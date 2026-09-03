#!/usr/bin/env python3
"""Black-box subprocess tests for the Codex hook dispatcher reference POC.

The suite deliberately imports none of the runtime implementation.  Each case
copies the reference payload into a disposable project's ``.codex/hooks``
directory and invokes the same ``hookd.py --expect-event`` process contract
that ``hooks.json`` uses.  Passing this suite is SIMULATED evidence only; it is
not evidence that a live Codex client discovered, trusted, or fired a hook.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping


HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent
RUNTIME_RELATIVE = Path(".codex/hooks")
LOG_RELATIVE = RUNTIME_RELATIVE / "hookd.log.jsonl"
RECEIPTS_RELATIVE = RUNTIME_RELATIVE / "receipts"
RECEIPT_SCHEMA = "devforgeai.worker-result/v1"
FORBIDDEN_LOG_KEYS = {
    "command",
    "last_assistant_message",
    "prompt",
    "tool_input",
    "tool_response",
    "transcript",
    "transcript_path",
}


@dataclass(frozen=True)
class Invocation:
    returncode: int
    stdout: str
    stderr: str

    def json_stdout(self) -> Mapping[str, Any]:
        if not self.stdout.strip():
            raise AssertionError(
                f"expected JSON stdout, got none (exit={self.returncode}, stderr={self.stderr!r})"
            )
        try:
            value = json.loads(self.stdout)
        except json.JSONDecodeError as exc:
            raise AssertionError(f"stdout is not one JSON value: {self.stdout!r}") from exc
        if not isinstance(value, dict):
            raise AssertionError(f"stdout JSON is not an object: {value!r}")
        return value


@dataclass(frozen=True)
class CaseResult:
    label: str
    passed: bool
    detail: str = ""


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _runtime_copy(project: Path) -> Path:
    runtime = project / RUNTIME_RELATIVE
    runtime.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        SOURCE,
        runtime,
        ignore=shutil.ignore_patterns("tests", "__pycache__", "*.pyc", "hookd.log.jsonl", "receipts"),
    )
    return runtime


@contextmanager
def project(mode: str = "enforce") -> Iterator[tuple[Path, Path]]:
    with tempfile.TemporaryDirectory(prefix="codex-hookd-test-") as temporary:
        root = Path(temporary).resolve()
        runtime = _runtime_copy(root)
        policy_path = runtime / "policy.json"
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        policy["mode"] = mode
        _write_json(policy_path, policy)

        (root / "src").mkdir()
        (root / "src/app.py").write_text("VALUE = 1\n", encoding="utf-8")
        (root / "AGENTS.md").write_text("# protected\n", encoding="utf-8")
        (root / "src/link-to-agents.md").symlink_to(root / "AGENTS.md")
        yield root, runtime


def event(name: str, **fields: Any) -> dict[str, Any]:
    value: dict[str, Any] = {
        "session_id": "session-test",
        "transcript_path": None,
        "cwd": "",
        "hook_event_name": name,
        "model": "test-model",
    }
    if name != "SessionStart":
        value["turn_id"] = "turn-test"
    value.update(fields)
    return value


def patch(path: str, *, operation: str = "Update", move_to: str | None = None) -> str:
    lines = ["*** Begin Patch", f"*** {operation} File: {path}"]
    if move_to is not None:
        lines.append(f"*** Move to: {move_to}")
    if operation != "Delete":
        lines.extend(("@@", "-VALUE = 1", "+VALUE = 2"))
    lines.append("*** End Patch")
    return "\n".join(lines)


def tool_event(name: str, tool_name: str, tool_input: Mapping[str, Any], **fields: Any) -> dict[str, Any]:
    return event(
        name,
        tool_name=tool_name,
        tool_use_id="tool-test",
        tool_input=dict(tool_input),
        **fields,
    )


def invoke(
    root: Path,
    expected_event: str,
    value: Mapping[str, Any] | None = None,
    *,
    raw: str | None = None,
    deadline_ms: int | None = None,
    extra_env: Mapping[str, str] | None = None,
) -> Invocation:
    command = [
        sys.executable,
        str(root / RUNTIME_RELATIVE / "hookd.py"),
        "--expect-event",
        expected_event,
    ]
    if deadline_ms is not None:
        command.extend(("--deadline-ms", str(deadline_ms)))
    payload = raw if raw is not None else json.dumps(value)
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment.update(extra_env or {})
    process = subprocess.run(
        command,
        cwd=root,
        input=payload,
        text=True,
        capture_output=True,
        env=environment,
        timeout=8,
        check=False,
    )
    return Invocation(process.returncode, process.stdout, process.stderr)


def _assert_silent_pass(result: Invocation) -> None:
    assert result.returncode == 0, result
    assert result.stdout == "", result
    assert result.stderr == "", result


def _assert_pre_tool_deny(result: Invocation, reason_fragment: str = "") -> Mapping[str, Any]:
    assert result.returncode == 0, result
    assert result.stderr == "", result
    output = result.json_stdout()
    specific = output.get("hookSpecificOutput")
    assert isinstance(specific, dict), output
    assert specific.get("hookEventName") == "PreToolUse", output
    assert specific.get("permissionDecision") == "deny", output
    reason = specific.get("permissionDecisionReason")
    assert isinstance(reason, str) and reason, output
    if reason_fragment:
        assert reason_fragment.lower() in reason.lower(), reason
    return output


def _assert_post_tool_block(result: Invocation, reason_fragment: str = "") -> Mapping[str, Any]:
    assert result.returncode == 0, result
    assert result.stderr == "", result
    output = result.json_stdout()
    assert output.get("decision") == "block", output
    reason = output.get("reason")
    assert isinstance(reason, str) and reason, output
    if reason_fragment:
        assert reason_fragment.lower() in reason.lower(), reason
    return output


def _assert_subagent_continue(result: Invocation, reason_fragment: str = "") -> Mapping[str, Any]:
    assert result.returncode == 0, result
    assert result.stderr == "", result
    output = result.json_stdout()
    assert output.get("decision") == "block", output
    reason = output.get("reason")
    assert isinstance(reason, str) and reason, output
    if reason_fragment:
        assert reason_fragment.lower() in reason.lower(), reason
    return output


def _assert_subagent_stop_loop(result: Invocation) -> Mapping[str, Any]:
    assert result.returncode == 0, result
    assert result.stderr == "", result
    output = result.json_stdout()
    assert output.get("continue") is False, output
    reason = output.get("stopReason")
    assert isinstance(reason, str) and reason, output
    return output


def _read_log(root: Path) -> tuple[dict[str, Any], ...]:
    path = root / LOG_RELATIVE
    assert path.is_file(), f"audit log was not written: {path}"
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AssertionError(f"audit line {number} is not JSON: {line!r}") from exc
        assert isinstance(row, dict), (number, row)
        rows.append(row)
    assert rows, "audit log is empty"
    return tuple(rows)


def _all_mapping_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        keys.update(str(key) for key in value)
        for nested in value.values():
            keys.update(_all_mapping_keys(nested))
    elif isinstance(value, list):
        for nested in value:
            keys.update(_all_mapping_keys(nested))
    return keys


def _receipt(agent: str = "red_dev") -> dict[str, Any]:
    return {
        "schema": RECEIPT_SCHEMA,
        "run": "RUN-001",
        "skill": "dev",
        "phase": "red",
        "agent": agent,
        "status": "pass",
        "candidate": {"id": "RUN-001", "input_checkpoint": "base"},
        "claimed_paths": ["tests/test_app.py"],
        "evidence_refs": ["evidence/red.json"],
        "note": "",
        "issues": [],
    }


def case_patch_pass_and_deny() -> None:
    with project() as (root, _):
        allowed = tool_event(
            "PreToolUse", "apply_patch", {"command": patch("src/app.py")}, cwd=str(root)
        )
        _assert_silent_pass(invoke(root, "PreToolUse", allowed))

        denied = tool_event(
            "PreToolUse", "apply_patch", {"command": patch("AGENTS.md")}, cwd=str(root)
        )
        _assert_pre_tool_deny(invoke(root, "PreToolUse", denied), "protected")


def case_patch_parser_and_escape() -> None:
    with project() as (root, _):
        malformed = tool_event(
            "PreToolUse",
            "apply_patch",
            {"command": "*** Update File: src/app.py\n@@\n-x\n+y"},
            cwd=str(root),
        )
        _assert_pre_tool_deny(invoke(root, "PreToolUse", malformed), "patch")

        escaping = tool_event(
            "PreToolUse", "apply_patch", {"command": patch("../outside.py", operation="Add")}, cwd=str(root)
        )
        _assert_pre_tool_deny(invoke(root, "PreToolUse", escaping), "path")

        symlink = tool_event(
            "PreToolUse",
            "apply_patch",
            {"command": patch("src/link-to-agents.md")},
            cwd=str(root),
        )
        _assert_pre_tool_deny(invoke(root, "PreToolUse", symlink), "protected")


def case_patch_move_checks_both_paths() -> None:
    with project() as (root, _):
        protected_destination = tool_event(
            "PreToolUse",
            "apply_patch",
            {"command": patch("src/app.py", move_to="AGENTS.md")},
            cwd=str(root),
        )
        _assert_pre_tool_deny(invoke(root, "PreToolUse", protected_destination), "protected")


def case_patch_add_delete_and_multi_file() -> None:
    with project() as (root, _):
        added = tool_event(
            "PreToolUse",
            "apply_patch",
            {
                "command": "\n".join(
                    (
                        "*** Begin Patch",
                        "*** Add File: src/new.py",
                        "+VALUE = 2",
                        "*** End Patch",
                    )
                )
            },
            cwd=str(root),
        )
        _assert_silent_pass(invoke(root, "PreToolUse", added))

        deleted = tool_event(
            "PreToolUse",
            "apply_patch",
            {
                "command": "\n".join(
                    (
                        "*** Begin Patch",
                        "*** Delete File: src/app.py",
                        "*** End Patch",
                    )
                )
            },
            cwd=str(root),
        )
        _assert_silent_pass(invoke(root, "PreToolUse", deleted))

        protected_second_target = tool_event(
            "PreToolUse",
            "apply_patch",
            {
                "command": "\n".join(
                    (
                        "*** Begin Patch",
                        "*** Add File: src/also-new.py",
                        "+VALUE = 3",
                        "*** Update File: AGENTS.md",
                        "@@",
                        "-# protected",
                        "+# changed",
                        "*** End Patch",
                    )
                )
            },
            cwd=str(root),
        )
        _assert_pre_tool_deny(
            invoke(root, "PreToolUse", protected_second_target), "protected"
        )


def case_bash_real_command_not_mentions() -> None:
    with project() as (root, _):
        actual = tool_event(
            "PreToolUse",
            "Bash",
            {"command": "git push --force origin main"},
            cwd=str(root),
        )
        _assert_pre_tool_deny(invoke(root, "PreToolUse", actual), "command")

        quoted = tool_event(
            "PreToolUse",
            "Bash",
            {"command": "printf '%s\\n' 'git push --force origin main'"},
            cwd=str(root),
        )
        _assert_silent_pass(invoke(root, "PreToolUse", quoted))

        heredoc = tool_event(
            "PreToolUse",
            "Bash",
            {"command": "python3 - <<'PY'\nprint('git push --force origin main')\nPY"},
            cwd=str(root),
        )
        _assert_silent_pass(invoke(root, "PreToolUse", heredoc))


def case_bash_chained_force_push_is_denied() -> None:
    with project() as (root, _):
        semicolon = tool_event(
            "PreToolUse",
            "Bash",
            {"command": "printf '%s\\n' ready; git push --force-with-lease origin main"},
            cwd=str(root),
        )
        _assert_pre_tool_deny(invoke(root, "PreToolUse", semicolon), "command")

        conditional = tool_event(
            "PreToolUse",
            "Bash",
            {"command": "printf '%s\\n' ready && env TRACE=0 git push -f origin main"},
            cwd=str(root),
        )
        _assert_pre_tool_deny(invoke(root, "PreToolUse", conditional), "command")


def case_bash_wrapped_force_pushes_fail_closed() -> None:
    with project() as (root, _):
        commands = (
            "env -u UNUSED git push --force",
            "sudo -u root git push --force",
            "! command git push --force",
            "if sudo git push --force; then printf ok; fi",
            "A[0]=x git push --force",
            "A[0]+=x git push --force",
            "coproc git push --force",
            "if false; then :; else git push --force; fi",
        )
        for command in commands:
            attempted = tool_event(
                "PreToolUse", "Bash", {"command": command}, cwd=str(root)
            )
            _assert_pre_tool_deny(invoke(root, "PreToolUse", attempted), "command")


def case_bash_quoted_and_commented_heredoc_tokens_do_not_hide_denial() -> None:
    with project() as (root, _):
        quoted_token = tool_event(
            "PreToolUse",
            "Bash",
            {"command": "printf '%s\\n' '<<EOF'\ngit push --force origin main"},
            cwd=str(root),
        )
        _assert_pre_tool_deny(invoke(root, "PreToolUse", quoted_token), "command")

        commented_token = tool_event(
            "PreToolUse",
            "Bash",
            {"command": "printf ready # <<EOF\ngit push --force origin main"},
            cwd=str(root),
        )
        _assert_pre_tool_deny(invoke(root, "PreToolUse", commented_token), "command")

        comment_after_separator = tool_event(
            "PreToolUse",
            "Bash",
            {"command": "true;# ignored \\\ngit push --force"},
            cwd=str(root),
        )
        _assert_pre_tool_deny(
            invoke(root, "PreToolUse", comment_after_separator), "command"
        )

        commented_quoted_heredoc = tool_event(
            "PreToolUse",
            "Bash",
            {"command": "true;# <<'EOF'\ngit push --force\nEOF"},
            cwd=str(root),
        )
        _assert_pre_tool_deny(
            invoke(root, "PreToolUse", commented_quoted_heredoc), "command"
        )

        harmless_comment = tool_event(
            "PreToolUse",
            "Bash",
            {"command": "true;# ignored \\\nprintf '%s\\n' safe"},
            cwd=str(root),
        )
        _assert_silent_pass(invoke(root, "PreToolUse", harmless_comment))

        quoted_control = tool_event(
            "PreToolUse",
            "Bash",
            {"command": "printf '%s\\n' 'true;# ignored \\\ngit push --force'"},
            cwd=str(root),
        )
        _assert_silent_pass(invoke(root, "PreToolUse", quoted_control))


def case_bash_nested_execution_forms_fail_closed_without_execution() -> None:
    with project() as (root, _):
        unquoted_marker = root / "src/unquoted-heredoc-executed"
        unquoted_heredoc = tool_event(
            "PreToolUse",
            "Bash",
            {
                "command": "\n".join(
                    (
                        "python3 - <<EOF",
                        "from pathlib import Path",
                        "Path('src/unquoted-heredoc-executed').touch()",
                        "EOF",
                    )
                )
            },
            cwd=str(root),
        )
        _assert_pre_tool_deny(
            invoke(root, "PreToolUse", unquoted_heredoc), "unquoted heredoc"
        )
        assert not unquoted_marker.exists()

        substitution_marker = root / "src/command-substitution-executed"
        command_substitution = tool_event(
            "PreToolUse",
            "Bash",
            {
                "command": (
                    "printf '%s\\n' \"$(touch src/command-substitution-executed)\""
                )
            },
            cwd=str(root),
        )
        _assert_pre_tool_deny(
            invoke(root, "PreToolUse", command_substitution), "substitution"
        )
        assert not substitution_marker.exists()

        subshell_marker = root / "src/subshell-executed"
        subshell = tool_event(
            "PreToolUse",
            "Bash",
            {"command": "(touch src/subshell-executed)"},
            cwd=str(root),
        )
        _assert_pre_tool_deny(invoke(root, "PreToolUse", subshell), "grouping")
        assert not subshell_marker.exists()


def case_bash_redirect_boundary() -> None:
    with project() as (root, _):
        allowed = tool_event(
            "PreToolUse", "Bash", {"command": "printf ok > /dev/null"}, cwd=str(root)
        )
        _assert_silent_pass(invoke(root, "PreToolUse", allowed))

        attached_dev_null = tool_event(
            "PreToolUse", "Bash", {"command": "printf ok >/dev/null"}, cwd=str(root)
        )
        _assert_silent_pass(invoke(root, "PreToolUse", attached_dev_null))

        fd_duplication = tool_event(
            "PreToolUse", "Bash", {"command": "printf ok 2>&1"}, cwd=str(root)
        )
        _assert_silent_pass(invoke(root, "PreToolUse", fd_duplication))

        for command in (
            "git &>/dev/null push --force",
            "git &> /dev/null push --force",
            "git &>>/dev/null push --force",
            "git 2<&0 push --force",
        ):
            interposed = tool_event(
                "PreToolUse", "Bash", {"command": command}, cwd=str(root)
            )
            _assert_pre_tool_deny(invoke(root, "PreToolUse", interposed), "command")

        legacy_both = tool_event(
            "PreToolUse", "Bash", {"command": "printf nope >&AGENTS.md"}, cwd=str(root)
        )
        _assert_pre_tool_deny(invoke(root, "PreToolUse", legacy_both), "protected")

        clobber = tool_event(
            "PreToolUse", "Bash", {"command": "printf nope >|AGENTS.md"}, cwd=str(root)
        )
        _assert_pre_tool_deny(invoke(root, "PreToolUse", clobber))

        for command in (
            "printf nope >$OUTPUT_PATH",
            "printf nope >*.txt",
        ):
            expanded = tool_event(
                "PreToolUse", "Bash", {"command": command}, cwd=str(root)
            )
            _assert_pre_tool_deny(
                invoke(root, "PreToolUse", expanded), "expanded or globbed"
            )

        outside = root.parent / "codex-hookd-outside.txt"
        denied = tool_event(
            "PreToolUse", "Bash", {"command": f"printf nope > {outside}"}, cwd=str(root)
        )
        _assert_pre_tool_deny(invoke(root, "PreToolUse", denied), "path")


def case_observe_suppresses_denial_and_records_it() -> None:
    with project("observe") as (root, _):
        would_deny = tool_event(
            "PreToolUse", "apply_patch", {"command": patch("AGENTS.md")}, cwd=str(root)
        )
        _assert_silent_pass(invoke(root, "PreToolUse", would_deny))
        rows = _read_log(root)
        rendered = "\n".join(json.dumps(row, sort_keys=True) for row in rows)
        assert "would_deny" in rendered, rendered
        assert "AGENTS.md" in rendered, rendered


def case_observe_mode_surfaces_critical_check_failure() -> None:
    with project("observe") as (root, runtime):
        (runtime / "checks/local_registry.py").write_text(
            "from .base import Check\n\n"
            "class CrashingCritical(Check):\n"
            "    name = 'crashing_critical'\n"
            "    order = 25\n"
            "    events = frozenset({'PreToolUse'})\n"
            "    tool_pattern = r'^apply_patch$'\n"
            "    critical = True\n\n"
            "    def evaluate(self, event, context):\n"
            "        raise RuntimeError('private critical failure detail')\n\n"
            "LOCAL_CHECKS = (CrashingCritical,)\n",
            encoding="utf-8",
        )
        attempted = tool_event(
            "PreToolUse", "apply_patch", {"command": patch("src/app.py")}, cwd=str(root)
        )
        output = _assert_pre_tool_deny(
            invoke(root, "PreToolUse", attempted), "critical check crashing_critical failed"
        )
        assert "private critical failure detail" not in json.dumps(output), output
        rows = _read_log(root)
        crash_rows = [row for row in rows if row.get("check") == "crashing_critical"]
        assert len(crash_rows) == 1, crash_rows
        assert crash_rows[0].get("reason_code") == "CHECK_FAILURE", crash_rows[0]


def case_session_start_context() -> None:
    with project("observe") as (root, _):
        started = event("SessionStart", cwd=str(root), source="startup")
        result = invoke(root, "SessionStart", started)
        assert result.returncode == 0, result
        assert result.stderr == "", result
        output = result.json_stdout()
        specific = output.get("hookSpecificOutput")
        assert isinstance(specific, dict), output
        assert specific.get("hookEventName") == "SessionStart", output
        context = specific.get("additionalContext")
        assert isinstance(context, str) and "mode=observe" in context, output
        assert "policy_sha256=" in context, output


def case_session_start_advisory_failure_remains_visible_with_context() -> None:
    with project() as (root, runtime):
        (runtime / "checks/local_registry.py").write_text(
            "from .base import Check\n\n"
            "class BrokenAdvisory(Check):\n"
            "    name = 'broken_advisory'\n"
            "    order = 25\n"
            "    events = frozenset({'SessionStart'})\n"
            "    critical = False\n\n"
            "    def evaluate(self, event, context):\n"
            "        raise RuntimeError('private advisory failure detail')\n\n"
            "LOCAL_CHECKS = (BrokenAdvisory,)\n",
            encoding="utf-8",
        )
        started = event("SessionStart", cwd=str(root), source="startup")
        result = invoke(root, "SessionStart", started)
        assert result.returncode == 0, result
        assert result.stderr == "", result
        output = result.json_stdout()
        specific = output.get("hookSpecificOutput")
        assert isinstance(specific, dict), output
        assert specific.get("hookEventName") == "SessionStart", output
        context = specific.get("additionalContext")
        assert isinstance(context, str), output
        assert "DevForgeAI hook warning:" in context, context
        assert "advisory check broken_advisory failed" in context, context
        assert "DevForgeAI Codex hookd POC is active" in context, context
        assert "private advisory failure detail" not in context, context


def case_post_tool_log_is_redacted() -> None:
    sentinel = "TOP-SECRET-hook-payload-5ae8d6"
    with project() as (root, _):
        completed = tool_event(
            "PostToolUse",
            "apply_patch",
            {"command": patch("src/app.py") + f"\n# {sentinel}"},
            cwd=str(root),
            tool_response={"output": sentinel, "status": "completed"},
        )
        _assert_silent_pass(invoke(root, "PostToolUse", completed))
        rows = _read_log(root)
        text = "\n".join(json.dumps(row, sort_keys=True) for row in rows)
        assert sentinel not in text, text
        keys = _all_mapping_keys(list(rows))
        assert not (keys & FORBIDDEN_LOG_KEYS), sorted(keys & FORBIDDEN_LOG_KEYS)
        assert any(row.get("event") == "PostToolUse" for row in rows), rows


def case_subagent_receipt_valid() -> None:
    with project() as (root, _):
        receipt = _receipt()
        stopped = event(
            "SubagentStop",
            cwd=str(root),
            agent_id="agent-red-1",
            agent_type="red_dev",
            agent_transcript_path=None,
            stop_hook_active=False,
            last_assistant_message=json.dumps(receipt, separators=(",", ":")),
        )
        result = invoke(root, "SubagentStop", stopped)
        assert result.returncode == 0, result
        assert result.stderr == "", result
        assert result.json_stdout() == {}, result.stdout

        receipt_files = tuple((root / RECEIPTS_RELATIVE).glob("*.json"))
        assert len(receipt_files) == 1, receipt_files
        assert json.loads(receipt_files[0].read_text(encoding="utf-8")) == receipt

        log_text = (root / LOG_RELATIVE).read_text(encoding="utf-8")
        assert "tests/test_app.py" not in log_text, log_text
        assert "evidence/red.json" not in log_text, log_text


def case_subagent_receipt_invalid_and_second_stop() -> None:
    with project() as (root, _):
        invalid = event(
            "SubagentStop",
            cwd=str(root),
            agent_id="agent-red-2",
            agent_type="red_dev",
            agent_transcript_path=None,
            stop_hook_active=False,
            last_assistant_message="finished successfully",
        )
        _assert_subagent_continue(invoke(root, "SubagentStop", invalid), "JSON")

        invalid["stop_hook_active"] = True
        _assert_subagent_stop_loop(invoke(root, "SubagentStop", invalid))


def case_subagent_receipt_duplicate_keys_are_rejected_recursively() -> None:
    with project() as (root, _):
        compact = json.dumps(_receipt(), separators=(",", ":"))
        top_level_duplicate = compact[:-1] + ',"status":"fail"}'
        top_level = event(
            "SubagentStop",
            cwd=str(root),
            agent_id="agent-red-duplicate-top",
            agent_type="red_dev",
            agent_transcript_path=None,
            stop_hook_active=False,
            last_assistant_message=top_level_duplicate,
        )
        _assert_subagent_continue(
            invoke(root, "SubagentStop", top_level), "valid JSON object"
        )

        original_candidate = '"candidate":{"id":"RUN-001","input_checkpoint":"base"}'
        duplicate_candidate = (
            '"candidate":{"id":"RUN-001","id":"RUN-002",'
            '"input_checkpoint":"base"}'
        )
        assert original_candidate in compact
        nested_duplicate = compact.replace(original_candidate, duplicate_candidate, 1)
        nested = event(
            "SubagentStop",
            cwd=str(root),
            agent_id="agent-red-duplicate-nested",
            agent_type="red_dev",
            agent_transcript_path=None,
            stop_hook_active=False,
            last_assistant_message=nested_duplicate,
        )
        _assert_subagent_continue(
            invoke(root, "SubagentStop", nested), "valid JSON object"
        )
        assert not (root / RECEIPTS_RELATIVE).exists()


def case_subagent_null_message_uses_receipt_stop_contract() -> None:
    with project() as (root, _):
        missing = event(
            "SubagentStop",
            cwd=str(root),
            agent_id="agent-red-null",
            agent_type="red_dev",
            agent_transcript_path=None,
            stop_hook_active=False,
            last_assistant_message=None,
        )
        first = _assert_subagent_continue(
            invoke(root, "SubagentStop", missing), "worker must return"
        )
        assert "bootstrap" not in str(first["reason"]).lower(), first

        missing["stop_hook_active"] = True
        second = _assert_subagent_stop_loop(invoke(root, "SubagentStop", missing))
        assert "worker must return" in str(second["stopReason"]).lower(), second
        assert "bootstrap" not in str(second["stopReason"]).lower(), second
        assert not (root / RECEIPTS_RELATIVE).exists()


def case_subagent_fenced_receipt_and_unlisted_agent() -> None:
    with project() as (root, _):
        fenced = event(
            "SubagentStop",
            cwd=str(root),
            agent_id="agent-red-fenced",
            agent_type="red_dev",
            agent_transcript_path=None,
            stop_hook_active=False,
            last_assistant_message=(
                "```json\n" + json.dumps(_receipt(), separators=(",", ":")) + "\n```"
            ),
        )
        _assert_subagent_continue(invoke(root, "SubagentStop", fenced), "Markdown fence")
        assert not (root / RECEIPTS_RELATIVE).exists()

        unlisted = event(
            "SubagentStop",
            cwd=str(root),
            agent_id="agent-reviewer",
            agent_type="reviewer",
            agent_transcript_path=None,
            stop_hook_active=False,
            last_assistant_message="ordinary reviewer prose, not a worker receipt",
        )
        result = invoke(root, "SubagentStop", unlisted)
        assert result.returncode == 0, result
        assert result.stderr == "", result
        assert result.json_stdout() == {}, result.stdout
        assert not (root / RECEIPTS_RELATIVE).exists()


def case_subagent_receipt_oversize() -> None:
    with project() as (root, runtime):
        policy = json.loads((runtime / "policy.json").read_text(encoding="utf-8"))
        limit = int(policy["max_receipt_bytes"])
        oversized_receipt = _receipt()
        oversized_receipt["note"] = "x" * (limit + 1)
        stopped = event(
            "SubagentStop",
            cwd=str(root),
            agent_id="agent-red-3",
            agent_type="red_dev",
            agent_transcript_path=None,
            stop_hook_active=False,
            last_assistant_message=json.dumps(oversized_receipt),
        )
        _assert_subagent_continue(invoke(root, "SubagentStop", stopped), "byte")


def case_corrupt_policy_fails_closed() -> None:
    with project() as (root, runtime):
        (runtime / "policy.json").write_text("{not-json\n", encoding="utf-8")
        attempted = tool_event(
            "PreToolUse", "apply_patch", {"command": patch("src/app.py")}, cwd=str(root)
        )
        _assert_pre_tool_deny(invoke(root, "PreToolUse", attempted), "policy")


def case_unknown_policy_key_fails_closed() -> None:
    with project() as (root, runtime):
        policy_path = runtime / "policy.json"
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        policy["project_override"] = True
        _write_json(policy_path, policy)
        attempted = tool_event(
            "PreToolUse", "apply_patch", {"command": patch("src/app.py")}, cwd=str(root)
        )
        _assert_pre_tool_deny(invoke(root, "PreToolUse", attempted), "policy")


def case_altered_receipt_schema_policy_fails_closed() -> None:
    with project() as (root, runtime):
        policy_path = runtime / "policy.json"
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        policy["receipt_schema"] = "project-specific.worker-result/v2"
        _write_json(policy_path, policy)
        attempted = tool_event(
            "PreToolUse", "apply_patch", {"command": patch("src/app.py")}, cwd=str(root)
        )
        _assert_pre_tool_deny(invoke(root, "PreToolUse", attempted), "policy")


def case_max_receipt_bytes_above_event_budget_fails_closed() -> None:
    with project() as (root, runtime):
        policy_path = runtime / "policy.json"
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        policy["max_receipt_bytes"] = 65_537
        _write_json(policy_path, policy)
        attempted = tool_event(
            "PreToolUse", "apply_patch", {"command": patch("src/app.py")}, cwd=str(root)
        )
        _assert_pre_tool_deny(invoke(root, "PreToolUse", attempted), "policy")

    with tempfile.TemporaryDirectory(prefix="codex-hookd-receipt-limit-") as temporary:
        root = Path(temporary).resolve()
        _init_git_project(root)
        runtime = root / ".codex/hooks"
        runtime.mkdir(parents=True)
        policy = json.loads((SOURCE / "policy.json").read_text(encoding="utf-8"))
        policy["max_receipt_bytes"] = 65_537
        _write_json(runtime / "policy.json", policy)
        before = _project_snapshot(root)

        result = _run_installer(root)
        assert result.returncode == 2, (result.stdout, result.stderr)
        assert "max_receipt_bytes" in result.stderr, result.stderr
        assert _project_snapshot(root) == before


def case_noncanonical_external_redirect_policy_fails_closed() -> None:
    for redirect in ("/tmp/../etc", "/tmp//sink", "/"):
        with project() as (root, runtime):
            policy_path = runtime / "policy.json"
            policy = json.loads(policy_path.read_text(encoding="utf-8"))
            policy["allowed_external_redirects"] = [redirect]
            _write_json(policy_path, policy)
            attempted = tool_event(
                "PreToolUse",
                "apply_patch",
                {"command": patch("src/app.py")},
                cwd=str(root),
            )
            _assert_pre_tool_deny(invoke(root, "PreToolUse", attempted), "policy")


def case_dead_protected_path_spellings_fail_closed() -> None:
    spellings = (
        "./AGENTS.md",
        "dir/./file",
        "foo/",
        "foo//bar",
        "/**",
        "dir\\file",
    )
    for spelling in spellings:
        with project() as (root, runtime):
            policy_path = runtime / "policy.json"
            policy = json.loads(policy_path.read_text(encoding="utf-8"))
            policy["protected_paths"] = [spelling]
            _write_json(policy_path, policy)
            attempted = tool_event(
                "PreToolUse",
                "apply_patch",
                {"command": patch("src/app.py")},
                cwd=str(root),
            )
            _assert_pre_tool_deny(invoke(root, "PreToolUse", attempted), "policy")

        with tempfile.TemporaryDirectory(prefix="codex-hookd-protected-path-") as temporary:
            root = Path(temporary).resolve()
            _init_git_project(root)
            runtime = root / ".codex/hooks"
            runtime.mkdir(parents=True)
            policy = json.loads((SOURCE / "policy.json").read_text(encoding="utf-8"))
            policy["protected_paths"] = [spelling]
            _write_json(runtime / "policy.json", policy)
            before = _project_snapshot(root)

            result = _run_installer(root)
            assert result.returncode == 2, (spelling, result.stdout, result.stderr)
            assert "protected_paths" in result.stderr, (spelling, result.stderr)
            assert _project_snapshot(root) == before


def case_empty_protected_paths_rejected_by_schema_and_engine() -> None:
    schema = json.loads((SOURCE / "policy.schema.json").read_text(encoding="utf-8"))
    protected_schema = schema["properties"]["protected_paths"]
    assert protected_schema.get("type") == "array", protected_schema
    assert protected_schema.get("minItems") == 1, protected_schema

    with project() as (root, runtime):
        policy_path = runtime / "policy.json"
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        policy["protected_paths"] = []
        _write_json(policy_path, policy)
        attempted = tool_event(
            "PreToolUse", "apply_patch", {"command": patch("src/app.py")}, cwd=str(root)
        )
        _assert_pre_tool_deny(invoke(root, "PreToolUse", attempted), "policy")


def case_broken_local_registry_fails_closed() -> None:
    with project() as (root, runtime):
        (runtime / "checks/local_registry.py").write_text(
            "raise RuntimeError('registry sentinel must not leak')\n", encoding="utf-8"
        )
        attempted = tool_event(
            "PreToolUse", "apply_patch", {"command": patch("src/app.py")}, cwd=str(root)
        )
        output = _assert_pre_tool_deny(invoke(root, "PreToolUse", attempted), "registry")
        assert "registry sentinel" not in json.dumps(output), output


def case_local_registry_extension_runs() -> None:
    with project() as (root, runtime):
        (runtime / "checks/local_registry.py").write_text(
            "from .base import Check, Outcome\n\n"
            "class LocalSentinel(Check):\n"
            "    name = 'local_sentinel'\n"
            "    order = 25\n"
            "    events = frozenset({'PreToolUse'})\n"
            "    tool_pattern = r'^apply_patch$'\n"
            "    critical = True\n\n"
            "    def evaluate(self, event, context):\n"
            "        return Outcome.violation('LOCAL_SENTINEL', 'local extension denied this fixture')\n\n"
            "LOCAL_CHECKS = (LocalSentinel,)\n",
            encoding="utf-8",
        )
        attempted = tool_event(
            "PreToolUse", "apply_patch", {"command": patch("src/app.py")}, cwd=str(root)
        )
        _assert_pre_tool_deny(invoke(root, "PreToolUse", attempted), "local extension")


def case_local_registry_extension_owns_validated_config() -> None:
    with project() as (root, runtime):
        (runtime / "checks/local_registry.py").write_text(
            "from .base import Check, Outcome\n\n"
            "class ConfiguredSentinel(Check):\n"
            "    name = 'configured_sentinel'\n"
            "    order = 25\n"
            "    events = frozenset({'PreToolUse'})\n"
            "    tool_pattern = r'^apply_patch$'\n"
            "    critical = True\n\n"
            "    def validate_config(self, config):\n"
            "        if set(config) != {'deny_path'} or not isinstance(config['deny_path'], str):\n"
            "            raise ValueError('deny_path must be the only string setting')\n"
            "        self.deny_path = config['deny_path']\n\n"
            "    def evaluate(self, event, context):\n"
            "        configured = context.config_for(self.name)\n"
            "        if self.deny_path in event.command and configured['deny_path'] == self.deny_path:\n"
            "            return Outcome.violation('LOCAL_CONFIG_DENY', 'configured local denial')\n"
            "        return Outcome.pass_()\n\n"
            "LOCAL_CHECKS = (ConfiguredSentinel,)\n",
            encoding="utf-8",
        )
        policy_path = runtime / "policy.json"
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        policy["check_config"] = {
            "configured_sentinel": {"deny_path": "src/app.py"}
        }
        _write_json(policy_path, policy)

        allowed = tool_event(
            "PreToolUse", "apply_patch", {"command": patch("src/other.py")}, cwd=str(root)
        )
        _assert_silent_pass(invoke(root, "PreToolUse", allowed))
        denied = tool_event(
            "PreToolUse", "apply_patch", {"command": patch("src/app.py")}, cwd=str(root)
        )
        _assert_pre_tool_deny(invoke(root, "PreToolUse", denied), "configured local denial")


def case_unregistered_check_config_name_fails_closed() -> None:
    with project() as (root, runtime):
        policy_path = runtime / "policy.json"
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        policy["check_config"] = {"unregistered_check": {"enabled": True}}
        _write_json(policy_path, policy)
        attempted = tool_event(
            "PreToolUse", "apply_patch", {"command": patch("src/app.py")}, cwd=str(root)
        )
        _assert_pre_tool_deny(invoke(root, "PreToolUse", attempted), "policy")


def case_generic_tool_input_is_opaque_but_guarded_tools_are_strict() -> None:
    with project() as (root, _):
        for event_name in ("PreToolUse", "PostToolUse"):
            for index, opaque_input in enumerate((None, "opaque scalar"), 1):
                generic = event(
                    event_name,
                    cwd=str(root),
                    tool_name="GenericTool",
                    tool_use_id=f"generic-{event_name}-{index}",
                    tool_input=opaque_input,
                )
                _assert_silent_pass(invoke(root, event_name, generic))

        pre_bash_null = event(
            "PreToolUse",
            cwd=str(root),
            tool_name="Bash",
            tool_use_id="bash-null",
            tool_input=None,
        )
        _assert_pre_tool_deny(invoke(root, "PreToolUse", pre_bash_null), "policy")

        pre_patch_missing_command = event(
            "PreToolUse",
            cwd=str(root),
            tool_name="apply_patch",
            tool_use_id="patch-missing-command",
            tool_input={"patch": "not the command field"},
        )
        _assert_pre_tool_deny(
            invoke(root, "PreToolUse", pre_patch_missing_command), "policy"
        )

        post_bash_scalar = event(
            "PostToolUse",
            cwd=str(root),
            tool_name="Bash",
            tool_use_id="bash-scalar",
            tool_input="opaque scalar",
        )
        _assert_post_tool_block(invoke(root, "PostToolUse", post_bash_scalar), "policy")

        post_patch_null_command = event(
            "PostToolUse",
            cwd=str(root),
            tool_name="apply_patch",
            tool_use_id="patch-null-command",
            tool_input={"command": None},
        )
        _assert_post_tool_block(
            invoke(root, "PostToolUse", post_patch_null_command), "policy"
        )


def case_malformed_and_oversized_stdin_fail_closed() -> None:
    with project() as (root, _):
        _assert_pre_tool_deny(invoke(root, "PreToolUse", raw="{bad json"), "input")
        oversized = json.dumps(
            {
                "hook_event_name": "PreToolUse",
                "session_id": "session-test",
                "cwd": str(root),
                "padding": "x" * (2 * 1024 * 1024),
            }
        )
        _assert_pre_tool_deny(invoke(root, "PreToolUse", raw=oversized), "exceeds")


def case_subagent_supervisor_input_faults_are_terminal() -> None:
    with project() as (root, _):
        oversized = json.dumps(
            {
                "hook_event_name": "SubagentStop",
                "session_id": "session-test",
                "turn_id": "turn-test",
                "cwd": str(root),
                "padding": "x" * 300_000,
            }
        )
        for raw in ("{bad json", oversized):
            output = _assert_subagent_stop_loop(
                invoke(root, "SubagentStop", raw=raw)
            )
            assert "decision" not in output, output
            assert "reason" not in output, output


def case_event_mismatch_fails_closed() -> None:
    with project() as (root, _):
        wrong = tool_event(
            "PostToolUse", "apply_patch", {"command": patch("src/app.py")}, cwd=str(root)
        )
        _assert_pre_tool_deny(invoke(root, "PreToolUse", wrong), "event")


def case_internal_deadline_fails_closed() -> None:
    with project() as (root, runtime):
        (runtime / "checks/local_registry.py").write_text(
            "import time\n"
            "from .base import Check, Outcome\n\n"
            "class SlowCheck(Check):\n"
            "    name = 'slow_check'\n"
            "    order = 25\n"
            "    events = frozenset({'PreToolUse'})\n"
            "    tool_pattern = r'^apply_patch$'\n"
            "    critical = True\n\n"
            "    def evaluate(self, event, context):\n"
            "        time.sleep(1.0)\n"
            "        return Outcome.pass_()\n\n"
            "LOCAL_CHECKS = (SlowCheck,)\n",
            encoding="utf-8",
        )
        attempted = tool_event(
            "PreToolUse", "apply_patch", {"command": patch("src/app.py")}, cwd=str(root)
        )
        _assert_pre_tool_deny(
            invoke(root, "PreToolUse", attempted, deadline_ms=25), "deadline"
        )


def _git(root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments], cwd=root, text=True, capture_output=True, check=False, timeout=8
    )


def _init_git_project(root: Path) -> None:
    initialized = _git(root, "init", "-q")
    assert initialized.returncode == 0, initialized.stderr
    (root / "README.md").write_text("fixture\n", encoding="utf-8")
    added = _git(root, "add", "README.md")
    assert added.returncode == 0, added.stderr
    committed = _git(
        root,
        "-c",
        "user.name=Hook Test",
        "-c",
        "user.email=hook@example.invalid",
        "commit",
        "-qm",
        "fixture",
    )
    assert committed.returncode == 0, committed.stderr


def _run_installer(root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(SOURCE / "install.sh"), "--project-root", str(root), *arguments],
        cwd=root,
        text=True,
        capture_output=True,
        timeout=15,
        check=False,
    )


def _project_snapshot(root: Path) -> dict[str, str]:
    """Capture every project path, type, mode, symlink target, and file digest."""

    values: dict[str, str] = {}
    for directory, directory_names, file_names in os.walk(root, followlinks=False):
        current = Path(directory)
        directory_names.sort()
        file_names.sort()
        for name in directory_names:
            path = current / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                values[relative] = "symlink:" + os.readlink(path)
            else:
                values[relative] = f"directory:{path.lstat().st_mode & 0o7777:04o}"
        for name in file_names:
            path = current / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                values[relative] = "symlink:" + os.readlink(path)
                continue
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            values[relative] = f"file:{path.lstat().st_mode & 0o7777:04o}:{digest}"
    return values


def _tree_hashes(root: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for path in sorted((root / ".codex").rglob("*")):
        if path.is_file() and not path.is_symlink():
            values[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return values


def _owned_handlers(document: Mapping[str, Any], event_name: str) -> int:
    count = 0
    groups = document.get("hooks", {}).get(event_name, [])
    for group in groups:
        if not isinstance(group, dict):
            continue
        for handler in group.get("hooks", []):
            if isinstance(handler, dict):
                command = str(handler.get("command", ""))
                if "hookd.py" in command and f"--expect-event {event_name}" in command:
                    count += 1
    return count


def _configure_installed_check(root: Path, config: Mapping[str, Any]) -> None:
    local_registry = root / ".codex/hooks/checks/local_registry.py"
    local_registry.write_text(
        "from .base import Check, Outcome\n\n"
        "class InstallerConfigured(Check):\n"
        "    name = 'installer_configured'\n"
        "    order = 25\n"
        "    events = frozenset({'SessionStart'})\n"
        "    critical = False\n\n"
        "    def validate_config(self, config):\n"
        "        if set(config) != {'enabled'} or type(config['enabled']) is not bool:\n"
        "            raise ValueError('enabled must be the only boolean setting')\n\n"
        "    def evaluate(self, event, context):\n"
        "        return Outcome.pass_()\n\n"
        "LOCAL_CHECKS = (InstallerConfigured,)\n",
        encoding="utf-8",
    )
    policy_path = root / ".codex/hooks/policy.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    policy["check_config"] = {"installer_configured": dict(config)}
    _write_json(policy_path, policy)


def case_installer_merge_mode_and_idempotence() -> None:
    with tempfile.TemporaryDirectory(prefix="codex-hookd-install-") as temporary:
        root = Path(temporary).resolve()
        _init_git_project(root)

        (root / ".codex").mkdir()
        existing = {
            "description": "unrelated fixture hook",
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "^Bash$",
                        "hooks": [{"type": "command", "command": "true", "timeout": 1}],
                    }
                ]
            },
        }
        _write_json(root / ".codex/hooks.json", existing)

        install = _run_installer(root)
        assert install.returncode == 0, (install.stdout, install.stderr)
        installed = json.loads((root / ".codex/hooks.json").read_text(encoding="utf-8"))
        assert installed["hooks"]["PreToolUse"][0] == existing["hooks"]["PreToolUse"][0]
        for name in ("SessionStart", "PreToolUse", "PostToolUse", "SubagentStop"):
            assert _owned_handlers(installed, name) == 1, (name, installed)
        policy_path = root / ".codex/hooks/policy.json"
        assert json.loads(policy_path.read_text(encoding="utf-8"))["mode"] == "observe"
        assert not (root / ".codex/config.toml").exists()
        assert not (root / ".gitignore").exists()

        local_registry = root / ".codex/hooks/checks/local_registry.py"
        custom_module = root / ".codex/hooks/checks/project_ticket.py"
        local_registry.write_text("# locally owned\nLOCAL_CHECKS = ()\n", encoding="utf-8")
        custom_module.write_text("# locally owned module\n", encoding="utf-8")
        before_local = local_registry.read_bytes()
        before_custom = custom_module.read_bytes()

        enforce = _run_installer(root, "--enable-denies")
        assert enforce.returncode == 0, (enforce.stdout, enforce.stderr)
        assert local_registry.read_bytes() == before_local
        assert custom_module.read_bytes() == before_custom
        assert json.loads(policy_path.read_text(encoding="utf-8"))["mode"] == "enforce"
        hashes = _tree_hashes(root)

        repeated = _run_installer(root, "--enable-denies")
        assert repeated.returncode == 0, (repeated.stdout, repeated.stderr)
        assert _tree_hashes(root) == hashes


def case_installer_dry_run_makes_no_writes() -> None:
    with tempfile.TemporaryDirectory(prefix="codex-hookd-dry-run-") as temporary:
        root = Path(temporary).resolve()
        _init_git_project(root)
        before = _project_snapshot(root)

        result = _run_installer(root, "--dry-run")
        assert result.returncode == 0, (result.stdout, result.stderr)
        assert result.stderr == "", result.stderr
        assert "would write .codex/hooks.json" in result.stdout, result.stdout
        assert "would leave policy mode=observe" in result.stdout, result.stdout
        assert _project_snapshot(root) == before


def case_installer_check_reports_drift_and_current() -> None:
    with tempfile.TemporaryDirectory(prefix="codex-hookd-check-") as temporary:
        root = Path(temporary).resolve()
        _init_git_project(root)
        before = _project_snapshot(root)

        absent = _run_installer(root, "--check")
        assert absent.returncode == 1, (absent.stdout, absent.stderr)
        assert "installation drift:" in absent.stdout, absent.stdout
        assert _project_snapshot(root) == before

        installed = _run_installer(root)
        assert installed.returncode == 0, (installed.stdout, installed.stderr)
        current = _run_installer(root, "--check")
        assert current.returncode == 0, (current.stdout, current.stderr)
        assert "installation is current; mode=observe" in current.stdout, current.stdout

        hookd_path = root / ".codex/hooks/hookd.py"
        hookd_path.write_bytes(hookd_path.read_bytes() + b"\n# drift fixture\n")
        drifted = _run_installer(root, "--check")
        assert drifted.returncode == 1, (drifted.stdout, drifted.stderr)
        assert ".codex/hooks/hookd.py" in drifted.stdout, drifted.stdout


def case_installer_rejects_inline_config_hooks() -> None:
    with tempfile.TemporaryDirectory(prefix="codex-hookd-inline-") as temporary:
        root = Path(temporary).resolve()
        _init_git_project(root)
        (root / ".codex").mkdir()
        (root / ".codex/config.toml").write_text(
            "model = 'test-model'\n\n[hooks]\nPreToolUse = []\n", encoding="utf-8"
        )
        before = _project_snapshot(root)

        result = _run_installer(root)
        assert result.returncode == 2, (result.stdout, result.stderr)
        assert "inline hooks are present" in result.stderr, result.stderr
        assert _project_snapshot(root) == before


def case_installer_rejects_duplicate_owned_handler() -> None:
    with tempfile.TemporaryDirectory(prefix="codex-hookd-duplicate-") as temporary:
        root = Path(temporary).resolve()
        _init_git_project(root)
        (root / ".codex").mkdir()
        hooks = json.loads((SOURCE / "hooks.codex.json").read_text(encoding="utf-8"))
        duplicate = json.loads(json.dumps(hooks["hooks"]["PreToolUse"][0]["hooks"][0]))
        hooks["hooks"]["PreToolUse"][0]["hooks"].append(duplicate)
        _write_json(root / ".codex/hooks.json", hooks)
        before = _project_snapshot(root)

        result = _run_installer(root)
        assert result.returncode == 2, (result.stdout, result.stderr)
        assert "multiple DevForgeAI dispatcher handlers" in result.stderr, result.stderr
        assert _project_snapshot(root) == before


def case_installer_distinguishes_mentions_from_quoted_managed_handler() -> None:
    with tempfile.TemporaryDirectory(prefix="codex-hookd-handler-identity-") as temporary:
        root = Path(temporary).resolve()
        _init_git_project(root)
        (root / ".codex").mkdir()
        unrelated_group = {
            "matcher": "^Bash$",
            "hooks": [
                {
                    "type": "command",
                    "command": (
                        "printf '%s\\n' 'python3 \"$(git rev-parse --show-toplevel)/"
                        ".codex/hooks/hookd.py\" --expect-event PreToolUse'"
                    ),
                    "timeout": 1,
                }
            ],
        }
        quoted_managed_group = {
            "hooks": [
                {
                    "type": "command",
                    "command": (
                        "python3 \"$(git rev-parse --show-toplevel)/.codex/hooks/hookd.py\" "
                        "'--expect-event' 'PreToolUse' '--deadline-ms' '6000'"
                    ),
                    "timeout": 10,
                }
            ]
        }
        existing = {
            "description": "handler identity fixture",
            "hooks": {"PreToolUse": [unrelated_group, quoted_managed_group]},
        }
        _write_json(root / ".codex/hooks.json", existing)

        result = _run_installer(root)
        assert result.returncode == 0, (result.stdout, result.stderr)
        installed = json.loads((root / ".codex/hooks.json").read_text(encoding="utf-8"))
        groups = installed["hooks"]["PreToolUse"]
        assert len(groups) == 2, groups
        assert groups[0] == unrelated_group, groups
        assert groups[1] == json.loads(
            (SOURCE / "hooks.codex.json").read_text(encoding="utf-8")
        )["hooks"]["PreToolUse"][0], groups


def case_installer_rejects_unanchored_denied_command_without_writes() -> None:
    with tempfile.TemporaryDirectory(prefix="codex-hookd-unanchored-") as temporary:
        root = Path(temporary).resolve()
        _init_git_project(root)
        runtime = root / ".codex/hooks"
        runtime.mkdir(parents=True)
        policy = json.loads((SOURCE / "policy.json").read_text(encoding="utf-8"))
        policy["denied_commands"][0]["pattern"] = policy["denied_commands"][0][
            "pattern"
        ].removeprefix("^")
        _write_json(runtime / "policy.json", policy)
        before = _project_snapshot(root)

        result = _run_installer(root)
        assert result.returncode == 2, (result.stdout, result.stderr)
        assert "pattern must be anchored with ^" in result.stderr, result.stderr
        assert _project_snapshot(root) == before


def case_installer_rejects_malformed_preserved_hooks_without_writes() -> None:
    fixtures = (
        (
            "group",
            {"hooks": {"PreToolUse": [{"matcher": "^Bash$"}]}},
            "needs handlers",
        ),
        (
            "handler",
            {
                "hooks": {
                    "PreToolUse": [
                        {"matcher": "^Bash$", "hooks": [{"type": "command"}]}
                    ]
                }
            },
            "needs a command",
        ),
    )
    for fixture_name, hooks, reason in fixtures:
        with tempfile.TemporaryDirectory(
            prefix=f"codex-hookd-malformed-{fixture_name}-"
        ) as temporary:
            root = Path(temporary).resolve()
            _init_git_project(root)
            (root / ".codex").mkdir()
            _write_json(root / ".codex/hooks.json", hooks)
            before = _project_snapshot(root)

            result = _run_installer(root)
            assert result.returncode == 2, (result.stdout, result.stderr)
            assert reason in result.stderr, result.stderr
            assert _project_snapshot(root) == before


def case_installer_check_validates_registered_local_config_without_writes() -> None:
    with tempfile.TemporaryDirectory(prefix="codex-hookd-local-config-") as temporary:
        root = Path(temporary).resolve()
        _init_git_project(root)
        installed = _run_installer(root)
        assert installed.returncode == 0, (installed.stdout, installed.stderr)

        _configure_installed_check(root, {"enabled": True})
        valid_before = _project_snapshot(root)
        valid = _run_installer(root, "--check")
        assert valid.returncode == 0, (valid.stdout, valid.stderr)
        assert "installation is current" in valid.stdout, valid.stdout
        assert _project_snapshot(root) == valid_before

        _configure_installed_check(root, {"enabled": "yes"})
        invalid_before = _project_snapshot(root)
        invalid = _run_installer(root, "--check")
        assert invalid.returncode == 2, (invalid.stdout, invalid.stderr)
        assert "candidate runtime rejected" in invalid.stderr, invalid.stderr
        assert _project_snapshot(root) == invalid_before


def case_installer_check_rejects_unregistered_config_without_writes() -> None:
    with tempfile.TemporaryDirectory(prefix="codex-hookd-ghost-config-") as temporary:
        root = Path(temporary).resolve()
        _init_git_project(root)
        installed = _run_installer(root)
        assert installed.returncode == 0, (installed.stdout, installed.stderr)

        policy_path = root / ".codex/hooks/policy.json"
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        policy["check_config"] = {"ghost_check": {"enabled": True}}
        _write_json(policy_path, policy)
        before = _project_snapshot(root)

        result = _run_installer(root, "--check")
        assert result.returncode == 2, (result.stdout, result.stderr)
        assert "candidate runtime rejected" in result.stderr, result.stderr
        assert _project_snapshot(root) == before


def case_installer_check_rejects_oversized_policy_without_writes() -> None:
    with tempfile.TemporaryDirectory(prefix="codex-hookd-large-policy-") as temporary:
        root = Path(temporary).resolve()
        _init_git_project(root)
        installed = _run_installer(root)
        assert installed.returncode == 0, (installed.stdout, installed.stderr)

        policy_path = root / ".codex/hooks/policy.json"
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        policy["check_config"] = {
            "session_selftest": {"padding": "x" * 1_048_576}
        }
        _write_json(policy_path, policy)
        assert policy_path.stat().st_size > 1_048_576
        before = _project_snapshot(root)

        result = _run_installer(root, "--check")
        assert result.returncode == 2, (result.stdout, result.stderr)
        assert "installed policy exceeds 1048576 bytes" in result.stderr, result.stderr
        assert _project_snapshot(root) == before


def case_installer_rejects_noncanonical_external_redirects_without_writes() -> None:
    for fixture_name, redirect in (
        ("parent", "/tmp/../etc"),
        ("slashes", "/tmp//sink"),
        ("root", "/"),
    ):
        with tempfile.TemporaryDirectory(
            prefix=f"codex-hookd-redirect-{fixture_name}-"
        ) as temporary:
            root = Path(temporary).resolve()
            _init_git_project(root)
            runtime = root / ".codex/hooks"
            runtime.mkdir(parents=True)
            policy = json.loads((SOURCE / "policy.json").read_text(encoding="utf-8"))
            policy["allowed_external_redirects"] = [redirect]
            _write_json(runtime / "policy.json", policy)
            before = _project_snapshot(root)

            result = _run_installer(root)
            assert result.returncode == 2, (result.stdout, result.stderr)
            assert "allowed_external_redirects" in result.stderr, result.stderr
            assert _project_snapshot(root) == before


def case_installer_and_handler_support_project_root_with_spaces() -> None:
    with tempfile.TemporaryDirectory(prefix="codex hookd spaced project ") as temporary:
        root = Path(temporary).resolve()
        assert " " in str(root), root
        _init_git_project(root)

        installed = _run_installer(root)
        assert installed.returncode == 0, (installed.stdout, installed.stderr)
        current = _run_installer(root, "--check")
        assert current.returncode == 0, (current.stdout, current.stderr)

        hooks = json.loads((root / ".codex/hooks.json").read_text(encoding="utf-8"))
        handler = hooks["hooks"]["SessionStart"][0]["hooks"][0]
        environment = dict(os.environ)
        environment.pop("PYTHONPATH", None)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        process = subprocess.run(
            ["bash", "-lc", handler["command"]],
            cwd=root,
            input=json.dumps(event("SessionStart", cwd=str(root), source="startup")),
            text=True,
            capture_output=True,
            env=environment,
            timeout=15,
            check=False,
        )
        result = Invocation(process.returncode, process.stdout, process.stderr)
        assert result.returncode == 0, result
        assert result.stderr == "", result
        output = result.json_stdout()
        specific = output.get("hookSpecificOutput")
        assert isinstance(specific, dict), output
        assert specific.get("hookEventName") == "SessionStart", output


CASES = (
    ("apply_patch pass and protected-path deny JSON", case_patch_pass_and_deny),
    ("apply_patch malformed, traversal and symlink paths", case_patch_parser_and_escape),
    ("apply_patch move validates destination", case_patch_move_checks_both_paths),
    ("apply_patch accepts add/delete and checks every file", case_patch_add_delete_and_multi_file),
    ("Bash real force-push differs from quoted and heredoc mentions", case_bash_real_command_not_mentions),
    ("Bash chained force-push commands are denied", case_bash_chained_force_push_is_denied),
    ("Bash wrapped force-push forms fail closed", case_bash_wrapped_force_pushes_fail_closed),
    ("Bash quoted/commented heredoc tokens cannot hide denials", case_bash_quoted_and_commented_heredoc_tokens_do_not_hide_denial),
    ("Bash nested execution forms fail closed without side effects", case_bash_nested_execution_forms_fail_closed_without_execution),
    ("Bash redirect forms enforce literal path boundaries", case_bash_redirect_boundary),
    ("observe mode suppresses and records would-deny", case_observe_suppresses_denial_and_records_it),
    ("observe mode surfaces critical check failure", case_observe_mode_surfaces_critical_check_failure),
    ("SessionStart returns bounded health context", case_session_start_context),
    ("SessionStart preserves selftest context with advisory failure", case_session_start_advisory_failure_remains_visible_with_context),
    ("PostToolUse audit is JSONL and redacted", case_post_tool_log_is_redacted),
    ("SubagentStop stores a valid exact receipt", case_subagent_receipt_valid),
    ("SubagentStop invalid receipt continues once only", case_subagent_receipt_invalid_and_second_stop),
    ("SubagentStop rejects top-level and nested duplicate receipt keys", case_subagent_receipt_duplicate_keys_are_rejected_recursively),
    ("SubagentStop null message uses receipt retry/stop wording", case_subagent_null_message_uses_receipt_stop_contract),
    ("SubagentStop rejects fenced receipts but skips unlisted agents", case_subagent_fenced_receipt_and_unlisted_agent),
    ("SubagentStop refuses an oversized receipt", case_subagent_receipt_oversize),
    ("corrupt policy fails closed", case_corrupt_policy_fails_closed),
    ("unknown policy key fails closed", case_unknown_policy_key_fails_closed),
    ("altered receipt-schema policy fails closed", case_altered_receipt_schema_policy_fails_closed),
    ("max receipt bytes above event budget fails closed", case_max_receipt_bytes_above_event_budget_fails_closed),
    ("noncanonical external redirect policy fails closed", case_noncanonical_external_redirect_policy_fails_closed),
    ("dead protected-path spellings fail closed", case_dead_protected_path_spellings_fail_closed),
    ("empty protected paths rejected by schema and engine", case_empty_protected_paths_rejected_by_schema_and_engine),
    ("broken local registry fails closed", case_broken_local_registry_fails_closed),
    ("local registry extension is loaded", case_local_registry_extension_runs),
    ("local registry extension owns validated check_config", case_local_registry_extension_owns_validated_config),
    ("unregistered check_config name fails closed", case_unregistered_check_config_name_fails_closed),
    ("generic tool_input is opaque while guarded tools stay strict", case_generic_tool_input_is_opaque_but_guarded_tools_are_strict),
    ("malformed and oversized stdin fail closed", case_malformed_and_oversized_stdin_fail_closed),
    ("SubagentStop supervisor input faults are terminal", case_subagent_supervisor_input_faults_are_terminal),
    ("expected-event mismatch fails closed", case_event_mismatch_fails_closed),
    ("internal deadline fails closed before host timeout", case_internal_deadline_fails_closed),
    ("installer merges, stages mode, preserves local checks and is idempotent", case_installer_merge_mode_and_idempotence),
    ("installer dry-run makes no project writes", case_installer_dry_run_makes_no_writes),
    ("installer check distinguishes drift from current", case_installer_check_reports_drift_and_current),
    ("installer rejects inline config hooks without writes", case_installer_rejects_inline_config_hooks),
    ("installer rejects duplicate owned handlers without writes", case_installer_rejects_duplicate_owned_handler),
    ("installer distinguishes hook mentions from quoted managed handler", case_installer_distinguishes_mentions_from_quoted_managed_handler),
    ("installer rejects unanchored command rules without writes", case_installer_rejects_unanchored_denied_command_without_writes),
    ("installer rejects malformed preserved hooks without writes", case_installer_rejects_malformed_preserved_hooks_without_writes),
    ("installer check validates registered local config without writes", case_installer_check_validates_registered_local_config_without_writes),
    ("installer check rejects unregistered config without writes", case_installer_check_rejects_unregistered_config_without_writes),
    ("installer check rejects oversized policy without writes", case_installer_check_rejects_oversized_policy_without_writes),
    ("installer rejects noncanonical external redirects without writes", case_installer_rejects_noncanonical_external_redirects_without_writes),
    ("installer and configured handler support a project root with spaces", case_installer_and_handler_support_project_root_with_spaces),
)


def main() -> int:
    results: list[CaseResult] = []
    for label, function in CASES:
        try:
            function()
        except Exception as exc:  # noqa: BLE001 - a failed case must not hide later cases
            results.append(CaseResult(label, False, f"{type(exc).__name__}: {exc}"))
        else:
            results.append(CaseResult(label, True))

    for result in results:
        marker = "PASS" if result.passed else "FAIL"
        suffix = f" -- {result.detail}" if result.detail else ""
        print(f"{marker}: {result.label}{suffix}")
    passed = sum(result.passed for result in results)
    print(f"{passed}/{len(results)} Codex hook subprocess cases passed")
    if passed == len(results):
        print("Evidence classification: SIMULATED; live Codex behavior remains NOT_OBSERVED_LIVE")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
