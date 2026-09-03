#!/usr/bin/env python3
"""hookd: one Claude Code hook entrypoint for every event.

settings.json registers this file once per event. It reads the event JSON on
stdin, runs the checks registered for that event in `order`, merges their
decisions and speaks the event's protocol back to Claude Code:

  deny     -> exit 2, reason on stderr (documented block on block-capable events;
              JSON cannot override it, and it also works on Stop/SubagentStop)
  ask      -> exit 0, JSON permissionDecision "ask" (PreToolUse only)
  context  -> exit 0, JSON hookSpecificOutput.additionalContext
  none     -> exit 0, no output: the normal permission flow applies

It never emits permissionDecision "allow": that would bypass the user's
permission prompt and widen authority. Passing through is silence.

Failure policy: a `critical` check that raises, or malformed stdin on a
block-capable event, becomes a deny. A non-critical failure is logged and
skipped. A wall-clock alarm fires well before the settings `timeout`, because a
timed-out PreToolUse hook fails open on the host side.

Stdlib only. Python 3.10+.
"""
from __future__ import annotations

import json
import os
import signal
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from checks import REGISTRY  # noqa: E402
from checks.base import Check, Decision, Event  # noqa: E402

BLOCK_CAPABLE = {"PreToolUse", "UserPromptSubmit", "Stop", "SubagentStop", "PostToolUse"}
ALARM_SECONDS = int(os.environ.get("HOOKD_ALARM_SECONDS", "6"))  # < settings timeout (10)
LOG_NAME = os.environ.get("HOOKD_LOG", ".claude/hooks/hookd.log.jsonl")


class Timeout(Exception):
    pass


def _alarm(signum, frame):  # pragma: no cover - signal path
    raise Timeout()


def project_dir() -> str:
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def load_policy(root: str) -> dict:
    path = Path(root) / ".claude" / "hooks" / "policy.json"
    if not path.exists():
        path = HERE / "policy.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def log(root: str, record: dict) -> None:
    try:
        path = Path(root) / LOG_NAME
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, sort_keys=True) + "\n")
    except OSError:
        pass  # logging must never change a decision


def merge(decisions: list[Decision]) -> Decision:
    """deny beats ask beats context beats none; contexts concatenate."""
    denies = [d for d in decisions if d.kind == "deny"]
    if denies:
        return denies[0]
    asks = [d for d in decisions if d.kind == "ask"]
    if asks:
        return asks[0]
    contexts = [d.context for d in decisions if d.kind == "context" and d.context]
    if contexts:
        return Decision(kind="context", context="\n".join(contexts))
    return Decision.none()


def emit(ev_name: str, decision: Decision) -> int:
    if decision.kind == "deny":
        sys.stderr.write(f"hookd[{decision.check}]: {decision.reason}\n")
        return 2
    if decision.kind == "ask" and ev_name == "PreToolUse":
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": f"hookd[{decision.check}]: {decision.reason}",
        }}))
        return 0
    if decision.kind == "context":
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": ev_name,
            "additionalContext": decision.context,
        }}))
        return 0
    return 0


def run(raw: dict, root: str, registry: list[type[Check]] | None = None) -> tuple[int, Decision]:
    policy = load_policy(root)
    ev = Event(raw, root)
    decisions: list[Decision] = []
    for cls in sorted(registry or REGISTRY, key=lambda c: c.order):
        check = cls(policy)
        if not check.applies(ev):
            continue
        started = time.monotonic()
        try:
            d = check.run(ev)
        except Timeout:
            raise
        except Exception as exc:  # noqa: BLE001 - the whole point is to classify failures
            if cls.critical and ev.name in BLOCK_CAPABLE:
                d = Decision.deny(f"check failed closed: {type(exc).__name__}: {exc}")
            else:
                log(root, {"event": ev.name, "check": cls.name, "error": repr(exc)})
                continue
        d.check = cls.name
        log(root, {
            "ts": time.time(), "event": ev.name, "check": cls.name, "tool": ev.tool_name,
            "file": ev.file_path, "agent_id": ev.agent_id, "agent_type": ev.agent_type,
            "session": ev.session_id, "decision": d.kind, "reason": d.reason,
            "ms": round((time.monotonic() - started) * 1000, 1),
        })
        decisions.append(d)
        if d.kind == "deny":
            break  # first deny wins; later checks need not run
    final = merge(decisions)
    return emit(ev.name, final), final


def main() -> int:
    root = project_dir()
    signal.signal(signal.SIGALRM, _alarm)
    signal.alarm(ALARM_SECONDS)
    try:
        text = sys.stdin.read()
        raw = json.loads(text) if text.strip() else {}
        if not isinstance(raw, dict) or "hook_event_name" not in raw:
            raise ValueError("stdin is not a hook event")
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"hookd: malformed event: {exc}\n")
        log(root, {"event": "?", "error": f"malformed stdin: {exc}"})
        return 2  # fail closed: we cannot know whether this was block-capable
    try:
        code, _ = run(raw, root)
        return code
    except Timeout:
        sys.stderr.write("hookd: check budget exceeded; denying rather than failing open\n")
        log(root, {"event": raw.get("hook_event_name"), "error": "alarm"})
        return 2 if raw.get("hook_event_name") in BLOCK_CAPABLE else 0
    finally:
        signal.alarm(0)


if __name__ == "__main__":
    sys.exit(main())
