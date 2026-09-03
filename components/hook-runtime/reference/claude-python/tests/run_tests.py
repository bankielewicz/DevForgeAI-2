#!/usr/bin/env python3
"""Runs hookd as a subprocess against fixture events and checks exit code,
stdout JSON and stderr, so what is tested is what Claude Code sees.

    python3 components/hook-runtime/reference/claude-python/tests/run_tests.py

Covers: pass-through, path deny, redirect deny, outside-project deny, command
deny (including after `&&`), heredoc mention passing, interpreter-escape ask,
command ask, SessionStart context, SubagentStop receipt accept and
reject, a critical check that raises (fail closed), the alarm firing before the
settings timeout, and malformed stdin.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOOKD = HERE.parent / "hookd.py"


def event(name: str, **fields) -> dict:
    base = {"hook_event_name": name, "session_id": "s-test", "cwd": None}
    base.update(fields)
    return base


def run(ev: dict, root: Path, env_extra: dict | None = None) -> tuple[int, str, str]:
    ev = dict(ev)
    ev["cwd"] = ev.get("cwd") or str(root)
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(root), PYTHONDONTWRITEBYTECODE="1")
    env.update(env_extra or {})
    p = subprocess.run([sys.executable, str(HOOKD)], input=json.dumps(ev), text=True,
                       capture_output=True, env=env, timeout=30)
    return p.returncode, p.stdout, p.stderr


def main() -> int:
    root = Path(tempfile.mkdtemp(prefix="hookd-"))
    (root / ".claude" / "hooks").mkdir(parents=True)
    shutil.copy(HERE.parent / "policy.json", root / ".claude" / "hooks" / "policy.json")
    (root / "src").mkdir()
    (root / "src" / "app.py").write_text("print('hi')\n")
    (root / "CLAUDE.md").write_text("# rules\n")
    os.symlink(root / "CLAUDE.md", root / "link-to-rules.md")
    outside = Path(tempfile.mkdtemp(prefix="hookd-outside-"))

    results: list[tuple[str, bool, str]] = []

    def check(label: str, cond: bool, detail: str = "") -> None:
        results.append((label, cond, detail))

    # 1 pass-through: ordinary edit -> exit 0, no output
    code, out, err = run(event("PreToolUse", tool_name="Edit", tool_input={"file_path": str(root / "src/app.py")}), root)
    check("edit inside project passes through silently", code == 0 and out.strip() == "", f"{code} {out!r} {err!r}")

    # 2 protected path deny
    code, out, err = run(event("PreToolUse", tool_name="Write", tool_input={"file_path": "CLAUDE.md"}), root)
    check("write to CLAUDE.md denied with exit 2", code == 2 and "protected" in err, f"{code} {err!r}")

    # 3 symlink to protected file resolves and is denied
    code, out, err = run(event("PreToolUse", tool_name="Edit", tool_input={"file_path": "link-to-rules.md"}), root)
    check("symlink to protected file denied", code == 2, f"{code} {err!r}")

    # 4 bash redirect into protected path denied
    code, out, err = run(event("PreToolUse", tool_name="Bash", tool_input={"command": "echo x > .claude/settings.json"}), root)
    check("bash redirect into protected path denied", code == 2 and "protected" in err, f"{code} {err!r}")

    # 5 outside-project write denied
    code, out, err = run(event("PreToolUse", tool_name="Write", tool_input={"file_path": str(outside / "x.txt")}), root)
    check("write outside project denied", code == 2 and "outside" in err, f"{code} {err!r}")

    # 6 denied command
    code, out, err = run(event("PreToolUse", tool_name="Bash", tool_input={"command": "git push --force origin main"}), root)
    check("git push --force denied", code == 2 and "denied pattern" in err, f"{code} {err!r}")

    # 7 ask command -> JSON ask
    code, out, err = run(event("PreToolUse", tool_name="Bash", tool_input={"command": "git push origin main"}), root)
    ok = code == 0
    try:
        j = json.loads(out)
        ok = ok and j["hookSpecificOutput"]["permissionDecision"] == "ask"
    except Exception:  # noqa: BLE001
        ok = False
    check("git push asks via permissionDecision ask", ok, f"{code} {out!r}")

    # 8 harmless command passes
    code, out, err = run(event("PreToolUse", tool_name="Bash", tool_input={"command": "ls -la"}), root)
    check("ls passes through", code == 0 and out.strip() == "", f"{code} {out!r}")

    # 8a heredoc body mentioning a denied command passes (segment-anchored matching)
    heredoc = "cat > notes.md <<'EOF'\nnever run git push --force here\nEOF\n"
    code, out, err = run(event("PreToolUse", tool_name="Bash", tool_input={"command": heredoc}), root)
    check("heredoc mentioning a denied command passes", code == 0, f"{code} {err!r}")

    # 8b denied command in a later segment is still caught
    code, out, err = run(event("PreToolUse", tool_name="Bash", tool_input={"command": "cd src && git push --force origin main"}), root)
    check("denied command after && is caught", code == 2, f"{code} {err!r}")

    # 8c interpreter escape asks
    code, out, err = run(event("PreToolUse", tool_name="Bash", tool_input={"command": "bash -c 'git push --force'"}), root)
    check("bash -c asks", code == 0 and '"ask"' in out, f"{code} {out!r}")

    # 9 SessionStart context
    code, out, err = run(event("SessionStart", source="startup"), root)
    ok = code == 0 and "hookd is active" in json.loads(out)["hookSpecificOutput"]["additionalContext"]
    check("SessionStart injects context", ok, f"{code} {out!r}")

    # 10 SubagentStop: receipt accepted and written
    receipt = {"schema": "devforgeai.worker-result/v1", "status": "pass"}
    code, out, err = run(event("SubagentStop", agent_id="a1", agent_type="green_dev",
                               last_assistant_message=json.dumps(receipt)), root)
    written = (root / ".claude/hooks/receipts/a1.json").exists()
    check("SubagentStop valid receipt accepted and stored", code == 0 and written, f"{code} {err!r} written={written}")

    # 11 SubagentStop: prose instead of receipt -> exit 2 (subagent keeps working)
    code, out, err = run(event("SubagentStop", agent_id="a2", agent_type="green_dev",
                               last_assistant_message="I finished the implementation."), root)
    check("SubagentStop prose rejected with exit 2", code == 2 and "receipt" in err, f"{code} {err!r}")

    # 12 SubagentStop: agent not in receipt list is ignored
    code, out, err = run(event("SubagentStop", agent_id="a3", agent_type="Explore", last_assistant_message="done"), root)
    check("SubagentStop for unlisted agent passes", code == 0, f"{code} {err!r}")

    # 13 critical check raising -> deny (fail closed). Corrupt policy so protect_paths raises.
    (root / ".claude/hooks/policy.json").write_text(json.dumps({"protected_paths": 42}))
    code, out, err = run(event("PreToolUse", tool_name="Edit", tool_input={"file_path": "src/app.py"}), root)
    check("critical check exception fails closed", code == 2 and "failed closed" in err, f"{code} {err!r}")
    shutil.copy(HERE.parent / "policy.json", root / ".claude/hooks/policy.json")

    # 14 malformed stdin -> exit 2
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(root))
    p = subprocess.run([sys.executable, str(HOOKD)], input="not json", text=True, capture_output=True, env=env)
    check("malformed stdin fails closed", p.returncode == 2 and "malformed" in p.stderr, f"{p.returncode} {p.stderr!r}")

    # 15 alarm fires before the host timeout: a slow check via a test-only registry
    slow = HERE / "_slow_registry.py"
    slow.write_text(textwrap.dedent('''
        import sys, time, json, os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        import hookd
        from checks.base import Check, Decision
        class Slow(Check):
            name = "slow"; events = ("PreToolUse",); critical = True
            def run(self, ev):
                time.sleep(5); return Decision.none()
        raw = json.load(sys.stdin)
        import signal
        signal.signal(signal.SIGALRM, hookd._alarm); signal.alarm(1)
        try:
            code, _ = hookd.run(raw, os.environ["CLAUDE_PROJECT_DIR"], registry=[Slow])
        except hookd.Timeout:
            sys.stderr.write("alarm\\n"); code = 2
        sys.exit(code)
    '''))
    p = subprocess.run([sys.executable, str(slow)], input=json.dumps(event("PreToolUse", tool_name="Edit", tool_input={"file_path": "src/app.py"}, cwd=str(root))),
                       text=True, capture_output=True, env=env, timeout=20)
    slow.unlink()
    check("alarm converts a hung check into a deny", p.returncode == 2 and "alarm" in p.stderr, f"{p.returncode} {p.stderr!r}")

    # 16 log written, never containing tool_input bodies
    log = (root / ".claude/hooks/hookd.log.jsonl").read_text()
    check("decision log written without command bodies", "protect_paths" in log and "git push --force" not in log, "")

    failed = [r for r in results if not r[1]]
    for label, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {label}" + ("" if ok else f"\n      {detail}"))
    print(f"{len(results) - len(failed)}/{len(results)} hookd tests pass")
    shutil.rmtree(root, ignore_errors=True); shutil.rmtree(outside, ignore_errors=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
