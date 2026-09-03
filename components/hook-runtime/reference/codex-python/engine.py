#!/usr/bin/env python3
"""Load policy and checks, then return one normalized semantic outcome."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
import re
import sys
import time
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping


OUTCOME_SCHEMA = "devforgeai.hookd-outcome/v1"
POLICY_SCHEMA = "devforgeai.hookd-policy/v1"
MAX_POLICY_BYTES = 1_048_576
_POLICY_KEYS = frozenset(
    {
        "schema",
        "mode",
        "protected_paths",
        "deny_outside_project",
        "allowed_external_redirects",
        "denied_commands",
        "receipt_agents",
        "receipt_schema",
        "receipt_statuses",
        "max_receipt_bytes",
        "max_context_chars",
        "check_config",
    }
)
_AUDIT_KEYS = frozenset(
    {
        "mode",
        "source",
        "path",
        "paths_checked",
        "rule_id",
        "segments",
        "tool_name",
        "tool_use_id",
        "receipt_required",
        "receipt_file",
        "receipt_sha256",
    }
)


class EngineFault(RuntimeError):
    pass


def _object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise EngineFault(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_nonfinite(value: str) -> None:
    raise EngineFault(f"non-finite JSON number is not accepted: {value}")


def _validate_json_bounds(value: Any, *, max_depth: int = 32, max_nodes: int = 10_000) -> None:
    stack: list[tuple[Any, int]] = [(value, 0)]
    nodes = 0
    while stack:
        item, depth = stack.pop()
        nodes += 1
        if nodes > max_nodes or depth > max_depth:
            raise EngineFault("policy JSON exceeds structural bounds")
        if isinstance(item, dict):
            stack.extend((nested, depth + 1) for nested in item.values())
        elif isinstance(item, list):
            stack.extend((nested, depth + 1) for nested in item)


def _read_json(path: Path) -> tuple[dict[str, Any], str]:
    if path.is_symlink() or not path.is_file():
        raise EngineFault("policy must be a regular, non-symlink file")
    size = path.stat().st_size
    if size <= 0 or size > MAX_POLICY_BYTES:
        raise EngineFault("policy size is outside the accepted range")
    payload = path.read_bytes()
    try:
        value = json.loads(
            payload,
            object_pairs_hook=_object_without_duplicates,
            parse_constant=_reject_nonfinite,
        )
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise EngineFault("policy is not valid JSON") from exc
    if not isinstance(value, dict):
        raise EngineFault("policy must be a JSON object")
    _validate_json_bounds(value)
    return value, hashlib.sha256(payload).hexdigest()


def _string_array(
    policy: Mapping[str, Any],
    key: str,
    *,
    nonempty: bool = False,
    maximum: int,
    max_chars: int = 512,
) -> list[str]:
    value = policy.get(key)
    if (
        not isinstance(value, list)
        or len(value) > maximum
        or not all(isinstance(item, str) and len(item) <= max_chars for item in value)
    ):
        raise EngineFault(f"{key} must be an array of strings")
    if nonempty and (not value or any(not item for item in value)):
        raise EngineFault(f"{key} must contain non-empty strings")
    if len(value) != len(set(value)):
        raise EngineFault(f"{key} must not contain duplicates")
    return value


def load_policy(runtime_dir: Path) -> tuple[dict[str, Any], str]:
    policy, digest = _read_json(runtime_dir / "policy.json")
    unknown = sorted(frozenset(policy) - _POLICY_KEYS)
    missing = sorted(_POLICY_KEYS - frozenset(policy))
    if unknown or missing:
        raise EngineFault(f"policy keys differ from schema; missing={missing}; unknown={unknown}")
    if policy["schema"] != POLICY_SCHEMA:
        raise EngineFault("unsupported policy schema")
    if policy["mode"] not in {"observe", "enforce"}:
        raise EngineFault("mode must be observe or enforce")
    if not isinstance(policy["deny_outside_project"], bool):
        raise EngineFault("deny_outside_project must be boolean")
    protected = _string_array(policy, "protected_paths", nonempty=True, maximum=256)
    for pattern in protected:
        base = pattern[:-3] if pattern.endswith("/**") else pattern
        pure = PurePosixPath(base)
        if (
            pure.is_absolute()
            or not base
            or pure.as_posix() != base
            or any(part in {"", ".", ".."} for part in pure.parts)
            or any(marker in base for marker in "*?[\\")
            or any(ord(character) < 32 for character in base)
        ):
            raise EngineFault("protected_paths accepts exact relative paths and trailing /** only")
    redirects = _string_array(policy, "allowed_external_redirects", maximum=64)
    for item in redirects:
        pure = PurePosixPath(item)
        if (
            item == "/"
            or not pure.is_absolute()
            or pure.anchor != "/"
            or pure.as_posix() != item
            or any(part in {"", ".", ".."} for part in pure.parts[1:])
            or any(marker in item for marker in "$`~*?[]{}()\\")
            or any(ord(character) < 32 for character in item)
        ):
            raise EngineFault("allowed_external_redirects entries must be canonical literal paths")
    agents = _string_array(policy, "receipt_agents", maximum=128, max_chars=128)
    if any(re.fullmatch(r"[A-Za-z0-9_.:-]+", item) is None for item in agents):
        raise EngineFault("receipt_agents contains an invalid identifier")
    statuses = _string_array(policy, "receipt_statuses", nonempty=True, maximum=16)
    if not set(statuses) <= {"pass", "fail", "needs_user", "could_not_run"}:
        raise EngineFault("receipt_statuses contains an unsupported status")
    if policy["receipt_schema"] != "devforgeai.worker-result/v1":
        raise EngineFault("receipt_schema must be devforgeai.worker-result/v1")
    if (
        not isinstance(policy["max_receipt_bytes"], int)
        or isinstance(policy["max_receipt_bytes"], bool)
        or not 1024 <= policy["max_receipt_bytes"] <= 65_536
    ):
        raise EngineFault("max_receipt_bytes must be an integer from 1024 through 65536")
    if (
        not isinstance(policy["max_context_chars"], int)
        or isinstance(policy["max_context_chars"], bool)
        or not 128 <= policy["max_context_chars"] <= 16_384
    ):
        raise EngineFault("max_context_chars must be an integer from 128 through 16384")
    check_config = policy["check_config"]
    if not isinstance(check_config, dict):
        raise EngineFault("check_config must be an object")
    for name, config in check_config.items():
        if not isinstance(name, str) or re.fullmatch(r"[a-z][a-z0-9_]{1,63}", name) is None:
            raise EngineFault("check_config contains an invalid check name")
        if not isinstance(config, dict):
            raise EngineFault(f"check_config.{name} must be an object")

    commands = policy["denied_commands"]
    if not isinstance(commands, list) or len(commands) > 256:
        raise EngineFault("denied_commands must be an array")
    identifiers: set[str] = set()
    for rule in commands:
        if not isinstance(rule, dict) or frozenset(rule) != {"id", "pattern"}:
            raise EngineFault("each denied command requires exactly id and pattern")
        identifier = rule["id"]
        pattern = rule["pattern"]
        if not isinstance(identifier, str) or not re.fullmatch(r"[A-Z][A-Z0-9_]{1,63}", identifier):
            raise EngineFault("denied command id is invalid")
        if identifier in identifiers:
            raise EngineFault("denied command ids must be unique")
        identifiers.add(identifier)
        if not isinstance(pattern, str) or len(pattern) > 1024 or not pattern.startswith("^"):
            raise EngineFault("denied command patterns must be anchored")
        try:
            re.compile(pattern)
        except re.error as exc:
            raise EngineFault("denied command pattern is invalid") from exc
    return policy, digest


def validate_registry(registry: Iterable[Any], supported_events: frozenset[str], check_base: type) -> list[type]:
    classes = list(registry)
    names: set[str] = set()
    orders: set[int] = set()
    for check_class in classes:
        if not isinstance(check_class, type) or not issubclass(check_class, check_base):
            raise EngineFault("registry entries must be Check subclasses")
        name = getattr(check_class, "name", None)
        order = getattr(check_class, "order", None)
        events = getattr(check_class, "events", None)
        pattern = getattr(check_class, "tool_pattern", None)
        critical = getattr(check_class, "critical", None)
        if not isinstance(name, str) or not re.fullmatch(r"[a-z][a-z0-9_]{1,63}", name):
            raise EngineFault("check name is invalid")
        if name in names:
            raise EngineFault(f"duplicate check name: {name}")
        names.add(name)
        if not isinstance(order, int) or isinstance(order, bool) or order < 0:
            raise EngineFault(f"check order is invalid: {name}")
        if order in orders:
            raise EngineFault(f"duplicate check order: {order}")
        orders.add(order)
        if not isinstance(events, frozenset) or not events or not events <= supported_events:
            raise EngineFault(f"check events are invalid: {name}")
        if pattern is not None:
            if not isinstance(pattern, str):
                raise EngineFault(f"tool pattern is invalid: {name}")
            try:
                re.compile(pattern)
            except re.error as exc:
                raise EngineFault(f"tool pattern is invalid: {name}") from exc
        if not isinstance(critical, bool):
            raise EngineFault(f"critical flag is invalid: {name}")
    return sorted(classes, key=lambda item: (item.order, item.name))


def _safe_text(value: str, limit: int = 1000) -> str:
    clean = " ".join(value.replace("\x00", "").split())
    return clean[:limit]


def _validate_outcome(value: Any, outcome_type: type, kind_type: type) -> Any:
    if not isinstance(value, outcome_type) or not isinstance(value.kind, kind_type):
        raise EngineFault("check returned an invalid Outcome")
    for field_name in ("reason_code", "message", "context"):
        if not isinstance(getattr(value, field_name), str):
            raise EngineFault("Outcome text fields must be strings")
    if not isinstance(value.audit, Mapping):
        raise EngineFault("Outcome audit field must be a mapping")
    if value.reason_code and re.fullmatch(r"[A-Z][A-Z0-9_]{1,79}", value.reason_code) is None:
        raise EngineFault("Outcome reason_code is invalid")
    if value.kind.value in {"violation", "warning", "stop"} and (
        not value.reason_code or not value.message
    ):
        raise EngineFault("non-pass Outcome requires a reason_code and message")
    return value


def _normalized(kind: str, code: str = "", message: str = "", context: str = "") -> dict[str, str]:
    return {
        "schema": OUTCOME_SCHEMA,
        "kind": kind,
        "reason_code": _safe_text(code, 80),
        "message": _safe_text(message),
        "context": context.replace("\x00", ""),
    }


def _safe_audit(value: Mapping[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, item in value.items():
        if key not in _AUDIT_KEYS:
            continue
        if isinstance(item, bool) or item is None:
            output[key] = item
        elif isinstance(item, int) and not isinstance(item, bool):
            output[key] = item
        elif isinstance(item, str):
            output[key] = _safe_text(item, 256)
    return output


def _append_log(
    runtime_dir: Path,
    event: Any,
    policy_sha: str,
    policy_mode: str,
    check_name: str,
    outcome: Any,
    ms: float,
) -> None:
    path = runtime_dir / "hookd.log.jsonl"
    if path.is_symlink():
        return
    agent_id = event.agent_id
    row: dict[str, Any] = {
        "schema": "devforgeai.hookd-event/v1",
        "event": event.name,
        "check": check_name,
        "outcome": (
            {"violation": "would_deny", "stop": "would_stop"}.get(
                outcome.kind.value, outcome.kind.value
            )
            if policy_mode == "observe" and outcome.reason_code != "CHECK_FAILURE"
            else outcome.kind.value
        ),
        "reason_code": _safe_text(outcome.reason_code, 80),
        "policy_mode": policy_mode,
        "policy_sha256": policy_sha,
        "session_id": event.safe_identifier("session_id"),
        "turn_id": event.safe_identifier("turn_id"),
        "agent_id_sha256": hashlib.sha256(agent_id.encode("utf-8")).hexdigest() if agent_id else "",
        "agent_type": event.safe_identifier("agent_type", 80),
        "tool_name": event.safe_identifier("tool_name", 80),
        "duration_ms": round(ms, 3),
        "audit": _safe_audit(outcome.audit),
    }
    payload = (json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags, 0o600)
        try:
            os.write(descriptor, payload)
        finally:
            os.close(descriptor)
    except OSError:
        # Logging is diagnostic. Transition/promotion evidence is authoritative.
        return


def prepare_runtime(project_root: Path, runtime_dir: Path) -> tuple[Any, ...]:
    from checks import REGISTRY
    from checks.base import Check, CheckContext
    from protocol import SUPPORTED_EVENTS

    policy, policy_sha = load_policy(runtime_dir)
    registry = validate_registry(REGISTRY, SUPPORTED_EVENTS, Check)
    context = CheckContext(project_root, runtime_dir, policy, policy_sha)
    registered_names = {check_class.name for check_class in registry}
    unknown_config = sorted(set(policy["check_config"]) - registered_names)
    if unknown_config:
        raise EngineFault(f"check_config names unregistered checks: {unknown_config}")
    checks: list[Any] = []
    for check_class in registry:
        captured_out = io.StringIO()
        captured_err = io.StringIO()
        with contextlib.redirect_stdout(captured_out), contextlib.redirect_stderr(captured_err):
            check = check_class()
            result = check.validate_config(context.config_for(check_class.name))
        if result is not None:
            raise EngineFault(f"validate_config must return None: {check_class.name}")
        if captured_out.getvalue() or captured_err.getvalue():
            raise EngineFault(f"check configuration wrote output: {check_class.name}")
        checks.append(check)
    return policy, policy_sha, context, checks


def execute(raw_event: Any, project_root: Path, runtime_dir: Path) -> dict[str, str]:
    from checks.base import Outcome, OutcomeKind
    from protocol import HookEvent

    event = HookEvent.parse(raw_event)
    policy, policy_sha, context, checks = prepare_runtime(project_root, runtime_dir)
    contexts: list[str] = []
    warnings: list[str] = []

    for check in checks:
        check_class = type(check)
        if event.name not in check_class.events:
            continue
        if check_class.tool_pattern is not None and not re.search(check_class.tool_pattern, event.tool_name):
            continue
        started = time.perf_counter()
        try:
            captured_out = io.StringIO()
            captured_err = io.StringIO()
            with contextlib.redirect_stdout(captured_out), contextlib.redirect_stderr(captured_err):
                outcome = check.evaluate(event, context)
            if captured_out.getvalue() or captured_err.getvalue():
                raise EngineFault("check wrote to stdout or stderr")
            outcome = _validate_outcome(outcome, Outcome, OutcomeKind)
            if outcome.kind is OutcomeKind.STOP and event.name != "SubagentStop":
                raise EngineFault("stop is legal only for SubagentStop")
            if outcome.kind is OutcomeKind.CONTEXT and event.name != "SessionStart":
                raise EngineFault("context is legal only for SessionStart in this POC")
            if outcome.kind is OutcomeKind.WARNING and event.name not in {
                "SessionStart",
                "SubagentStop",
            }:
                raise EngineFault("warning is legal only for SessionStart or SubagentStop")
        except BaseException as exc:  # every plugin fault must become an event-aware result
            if isinstance(exc, (KeyboardInterrupt, SystemExit)):
                raise
            if check_class.critical:
                outcome = Outcome.violation(
                    "CHECK_FAILURE", f"critical check {check_class.name} failed"
                )
            else:
                outcome = Outcome.warning(
                    "CHECK_FAILURE", f"advisory check {check_class.name} failed"
                )
        elapsed = (time.perf_counter() - started) * 1000
        _append_log(
            runtime_dir,
            event,
            policy_sha,
            policy["mode"],
            check_class.name,
            outcome,
            elapsed,
        )

        if outcome.kind is OutcomeKind.STOP:
            if policy["mode"] == "enforce":
                return _normalized("stop", outcome.reason_code, outcome.message)
            continue
        if outcome.kind is OutcomeKind.VIOLATION:
            # Observe mode suppresses policy findings, never engine-integrity
            # failures. A crashed critical check cannot be reported as healthy.
            if policy["mode"] == "enforce" or outcome.reason_code == "CHECK_FAILURE":
                return _normalized("violation", outcome.reason_code, outcome.message)
            continue
        if outcome.kind is OutcomeKind.CONTEXT and outcome.context:
            contexts.append(outcome.context)
        elif outcome.kind is OutcomeKind.WARNING and outcome.message:
            warnings.append(outcome.message)

    if contexts:
        parts: list[str] = []
        if warnings:
            parts.append(
                "DevForgeAI hook warning: "
                + "; ".join(_safe_text(item) for item in dict.fromkeys(warnings))
            )
        parts.extend(item.replace("\x00", "") for item in dict.fromkeys(contexts))
        combined = "\n".join(parts)[: policy["max_context_chars"]]
        return _normalized("context", context=combined)
    if warnings:
        return _normalized("warning", "HOOK_WARNING", "; ".join(dict.fromkeys(warnings)))
    return _normalized("pass")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--validate-installation", action="store_true")
    args = parser.parse_args()
    runtime_dir = Path(__file__).resolve().parent
    try:
        root = Path(args.project_root).resolve(strict=True)
        if not root.is_dir():
            raise EngineFault("project root must be a directory")
        if args.validate_installation:
            prepare_runtime(root, runtime_dir)
            result = _normalized("pass")
        else:
            raw_event = json.load(
                sys.stdin,
                object_pairs_hook=_object_without_duplicates,
                parse_constant=_reject_nonfinite,
            )
            result = execute(raw_event, root, runtime_dir)
    except BaseException as exc:
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        result = _normalized(
            "violation",
            "HOOK_BOOTSTRAP_FAILURE",
            "hook policy or registry engine failed",
        )
    sys.stdout.write(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
