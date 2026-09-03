#!/usr/bin/env python3
"""Codex hook supervisor and event-specific response renderer.

This file intentionally imports no project check modules. It can therefore turn
policy, registry, import, syntax, crash, and timeout failures into a documented
Codex event response instead of relying on an ambiguous generic process error.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


MAX_INPUT_BYTES = 262_144
MAX_ENGINE_OUTPUT_BYTES = 65_536
OUTCOME_SCHEMA = "devforgeai.hookd-outcome/v1"
SUPPORTED_EVENTS = ("SessionStart", "PreToolUse", "PostToolUse", "SubagentStop")


class SupervisorFault(RuntimeError):
    pass


def _object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SupervisorFault(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_nonfinite(value: str) -> None:
    raise SupervisorFault(f"non-finite JSON number is not accepted: {value}")


def _safe_text(value: str, limit: int = 1000) -> str:
    return " ".join(value.replace("\x00", "").split())[:limit]


def _read_event() -> tuple[dict[str, Any], bytes]:
    payload = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    if len(payload) > MAX_INPUT_BYTES:
        raise SupervisorFault("hook input exceeds 262144 bytes")
    try:
        value = json.loads(
            payload,
            object_pairs_hook=_object_without_duplicates,
            parse_constant=_reject_nonfinite,
        )
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise SupervisorFault("hook input is not one valid JSON object") from exc
    if not isinstance(value, dict):
        raise SupervisorFault("hook input must be one JSON object")
    return value, payload


def _project_root(runtime_dir: Path, raw_event: dict[str, Any]) -> Path:
    if runtime_dir.name == "hooks" and runtime_dir.parent.name == ".codex":
        return runtime_dir.parent.parent.resolve(strict=True)
    raw_cwd = raw_event.get("cwd")
    start = Path(raw_cwd) if isinstance(raw_cwd, str) and raw_cwd else Path.cwd()
    start = start.resolve(strict=True)
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    return start


def _failure(code: str, message: str) -> dict[str, str]:
    return {
        "schema": OUTCOME_SCHEMA,
        "kind": "violation",
        "reason_code": code,
        "message": message,
        "context": "",
    }


def _validate_engine_output(payload: bytes) -> dict[str, str]:
    if not payload or len(payload) > MAX_ENGINE_OUTPUT_BYTES:
        raise SupervisorFault("engine output size is invalid")
    try:
        value = json.loads(
            payload,
            object_pairs_hook=_object_without_duplicates,
            parse_constant=_reject_nonfinite,
        )
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise SupervisorFault("engine output is invalid JSON") from exc
    expected = {"schema", "kind", "reason_code", "message", "context"}
    if not isinstance(value, dict) or set(value) != expected:
        raise SupervisorFault("engine output has an invalid shape")
    if value["schema"] != OUTCOME_SCHEMA or value["kind"] not in {
        "pass",
        "violation",
        "context",
        "warning",
        "stop",
    }:
        raise SupervisorFault("engine outcome is invalid")
    if not all(isinstance(value[key], str) for key in expected):
        raise SupervisorFault("engine outcome fields must be strings")
    return value


def _emergency_log(runtime_dir: Path, event_name: str, code: str) -> None:
    path = runtime_dir / "hookd.log.jsonl"
    if path.is_symlink():
        return
    row = {
        "schema": "devforgeai.hookd-event/v1",
        "event": event_name,
        "check": "supervisor",
        "outcome": "violation",
        "reason_code": code,
    }
    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags, 0o600)
        try:
            os.write(
                descriptor,
                (json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode(),
            )
        finally:
            os.close(descriptor)
    except OSError:
        return


def _emit(value: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(value, sort_keys=True, separators=(",", ":")))


def render(event_name: str, result: dict[str, str], stop_hook_active: bool) -> None:
    kind = result["kind"]
    message = _safe_text(result["message"] or result["reason_code"] or "hook policy blocked")
    if kind == "pass":
        if event_name == "SubagentStop":
            _emit({})
        return
    if kind == "context":
        if event_name == "SessionStart":
            _emit(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "SessionStart",
                        "additionalContext": result["context"],
                    }
                }
            )
        elif event_name == "SubagentStop":
            _emit({"systemMessage": result["context"]})
        return
    if kind == "warning":
        if event_name == "SessionStart":
            _emit({"systemMessage": message})
        elif event_name == "SubagentStop":
            _emit({"systemMessage": message})
        return
    if kind == "stop" or (event_name == "SubagentStop" and stop_hook_active):
        _emit({"continue": False, "stopReason": message, "systemMessage": message})
        return
    if event_name == "PreToolUse":
        _emit(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": message,
                }
            }
        )
    elif event_name in {"PostToolUse", "SubagentStop"}:
        _emit({"decision": "block", "reason": message})
    elif event_name == "SessionStart":
        _emit({"systemMessage": "DevForgeAI hookd degraded: " + message})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expect-event", choices=SUPPORTED_EVENTS, required=True)
    parser.add_argument("--deadline-ms", type=int, default=6000, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not 10 <= args.deadline_ms <= 9000:
        parser.error("--deadline-ms must be between 10 and 9000")

    runtime_dir = Path(__file__).resolve().parent
    raw_event: dict[str, Any] = {}
    try:
        raw_event, payload = _read_event()
        actual_event = raw_event.get("hook_event_name")
        if actual_event != args.expect_event:
            raise SupervisorFault("hook_event_name does not match the registered event")
        root = _project_root(runtime_dir, raw_event)
        completed = subprocess.run(
            [
                sys.executable,
                str(runtime_dir / "engine.py"),
                "--project-root",
                str(root),
            ],
            input=payload,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=root,
            timeout=args.deadline_ms / 1000,
            check=False,
        )
        if completed.returncode != 0:
            raise SupervisorFault("policy engine exited unsuccessfully")
        result = _validate_engine_output(completed.stdout)
    except subprocess.TimeoutExpired:
        result = _failure("HOOK_TIMEOUT", "hook policy engine exceeded its internal deadline")
        _emergency_log(runtime_dir, args.expect_event, "HOOK_TIMEOUT")
    except BaseException as exc:
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        message = (
            str(exc)
            if isinstance(exc, SupervisorFault)
            else "hook supervisor could not validate policy"
        )
        result = _failure("HOOK_BOOTSTRAP_FAILURE", _safe_text(message))
        _emergency_log(runtime_dir, args.expect_event, "HOOK_BOOTSTRAP_FAILURE")

    terminal_subagent_fault = args.expect_event == "SubagentStop" and result[
        "reason_code"
    ] in {"HOOK_BOOTSTRAP_FAILURE", "HOOK_TIMEOUT", "CHECK_FAILURE"}
    render(
        args.expect_event,
        result,
        raw_event.get("stop_hook_active") is True or terminal_subagent_fault,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
