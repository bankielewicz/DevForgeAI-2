#!/usr/bin/env python3
"""DevForgeAI hook dispatcher (rung 3). One script, both providers.

Reads one hook event as JSON on stdin, reads `.devforgeai/state.yaml`, the run
records under `.devforgeai/work/<run>/run.yaml` and the `stack.yaml` they point
at, runs an ordered check list, and answers with the provider's blocking
protocol. It never edits an artifact and never calls a model.

Usage (registered by settings.json / hooks.json, not run by hand):
    dispatch.py --provider claude|codex [--root <project root>]

Write model: a producer writes with Edit and Write inside the candidate root the
sequencer opened for the run, while it holds the phase lease. The lease is bound
at SubagentStart, the only identity-bearing pre-write event on both providers.
PreToolUse admits a write when the run is active, the lease is held, and the
target is under `candidate.root` and inside the fence for the current phase.
Everything else is denied. SubagentStop routes the worker's receipt into the
hook-only `devforgeai ingest-result`, which derives what actually changed from
the checkpoint diff and holds the receipt to it.

Blocking protocol: exit 2 with the reason on stderr. Both Claude Code and Codex
treat exit 2 as "block, and show stderr to the model" on every event that can
block. Exit 0 with no output means "no decision". Anything else is a dispatcher
fault and is reported on stderr with exit 1, which both providers treat as a
non-blocking error; the SessionStart self-test exists so that fault is seen.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

from policy import (
    GIT_READ_ONLY,
    HOOK_ONLY,
    PHASE_START_OPTIONS,
    PRIMARY_CALLABLE,
    RESULT_SCHEMA,
    RUN_MARKER,
    PatchTarget,
    PolicyError,
    allowed_agents,
    canonical_agent,
    findings_path,
    judge_write_denial,
    parse_apply_patch,
    phase_names,
    phase_run_keys,
    phase_spec,
    project_relative,
    validate_phase_write_path,
)

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.stderr.write("dispatch: PyYAML missing\n")
    sys.exit(1)

# Tools that can change the tree. NotebookEdit is included because Edit(path)
# permission rules do not cover it.
WRITE_TOOLS = {"Edit", "Write", "NotebookEdit", "MultiEdit", "apply_patch"}
# Read commands with no file-writing mode. Commands such as sed, find, sort,
# uniq and xargs are deliberately absent: each has a write/execute form that a
# command-head allowlist cannot distinguish safely.
READ_ONLY_CMDS = {
    "[", "cat", "cmp", "cut", "diff", "echo", "false", "grep", "head",
    "jq", "ls", "pwd", "rg", "sha256sum", "tail", "test", "tr", "true",
    "wc",
}
# The sequencer. It owns every candidate root and is the only writer of
# canonical `.devforgeai/**`; it enforces its own preconditions, including the
# hook-only env gate on session-start, lease-bind, ingest-result and phase next.
SEQUENCER = "devforgeai"
SEQUENCER_TIMEOUT = 660
# The Research Core CLI: a provider-external runner, not part of the sequencer
# grammar. It is the sole writer inside its own fence (`docs/research/**`,
# `.devforgeai/research-staging/`, `.devforgeai/research-cas/**`), it opens no
# framework run, and it needs none: its ten operations are admitted whether or
# not a story or document run is active. Everything else under this head is
# refused, and the single-argv rule above still rejects any redirect, pipeline
# or substitution wrapped around it.
RESEARCH_CLI = "devforgeai-research"
RESEARCH_OPS = {
    "normalize-request", "open-run", "append-record", "put-source",
    "transition-run", "validate-run", "seal-run", "render", "render-handoff",
    "resume-run",
}


class Block(Exception):
    """Raised by a check to deny the event. The message reaches the model."""


# ---------- inputs ----------

def discover_root(start: str | Path) -> Path:
    """The canonical project root, by the two-marker rule (D5)."""
    path = Path(start).resolve()
    if path.is_file():
        path = path.parent
    for candidate in (path, *path.parents):
        marker = candidate / RUN_MARKER
        if marker.exists():
            try:
                doc = yaml.safe_load(marker.read_text()) or {}
            except (OSError, yaml.YAMLError):
                doc = {}
            return Path(str(doc.get("canonical") or candidate)).resolve()
        if (candidate / ".devforgeai" / "state.yaml").exists():
            return candidate
    return path


def load_state(root: Path) -> dict:
    p = root / ".devforgeai" / "state.yaml"
    if not p.exists():
        return {}
    try:
        state = yaml.safe_load(p.read_text()) or {}
    except (OSError, yaml.YAMLError) as exc:
        raise Block(f"cannot read state.yaml; failing closed: {exc}") from exc
    if not isinstance(state, dict):
        raise Block("state.yaml is not a mapping; failing closed")
    return state


def load_run(root: Path, run: str) -> dict | None:
    path = root / ".devforgeai" / "work" / run / "run.yaml"
    if not path.exists():
        return None
    try:
        record = yaml.safe_load(path.read_text()) or {}
    except (OSError, yaml.YAMLError) as exc:
        raise Block(f"cannot read {run}/run.yaml; failing closed: {exc}") from exc
    if not isinstance(record, dict) or not record.get("run"):
        raise Block(f"{run}/run.yaml is not a run record; failing closed")
    return record


def active_records(root: Path, state: dict) -> list[dict]:
    """Every run the canonical index calls active, with its per-run record."""
    records = []
    for name, row in sorted((state.get("runs") or {}).items()):
        if (row or {}).get("status") != "active":
            continue
        record = load_run(root, name)
        if record:
            records.append(record)
    return records


def active(state: dict, root: Path, ev: dict | None = None) -> dict | None:
    """The run this event belongs to: the marker's, else the single active one."""
    records = active_records(root, state)
    if not records:
        return None
    if ev:
        cwd = str(ev.get("cwd") or "")
        for record in records:
            candidate = str((record.get("candidate") or {}).get("root") or "")
            if candidate and cwd and (Path(cwd).resolve() == Path(candidate).resolve()
                                      or Path(candidate).resolve() in Path(cwd).resolve().parents):
                return record
    if len(records) == 1:
        return records[0]
    return records[0] if not ev else None


# ---------- checks (ordered) ----------

def expected_agent(enf: dict) -> str:
    return next(iter(sorted(allowed_agents(enf))), "")


def check_worker(enf: dict, agent_type: str) -> None:
    allowed = allowed_agents(enf)
    actual = canonical_agent(agent_type or "")
    if not actual:
        raise Block("subagent action denied because the hook event has no agent_type")
    if actual not in allowed:
        raise Block(f"phase {enf.get('phase')} belongs to {sorted(allowed)}, not {agent_type}")


def check_agent(enf: dict, requested: str) -> None:
    allowed = allowed_agents(enf)
    if canonical_agent(requested or "") not in allowed:
        raise Block(
            f"phase {enf.get('phase')} may spawn only {sorted(allowed)}, not {requested}"
        )


def write_targets(tool: str, tool_input: dict) -> list[PatchTarget]:
    if tool == "apply_patch":
        command = tool_input.get("command")
        if command is None:
            command = tool_input.get("patch")
        return parse_apply_patch(command)
    raw = (
        tool_input.get("file_path")
        or tool_input.get("path")
        or tool_input.get("notebook_path")
    )
    body = ""
    for key in ("content", "new_string", "new_content", "new_source"):
        value = tool_input.get(key)
        if isinstance(value, str):
            body += value + "\n"
        elif key == "new_source" and isinstance(value, list) and all(isinstance(v, str) for v in value):
            body += "\n".join(value) + "\n"
    for edit in tool_input.get("edits") or []:
        if not isinstance(edit, dict):
            raise PolicyError("MultiEdit edits must be objects")
        for key in ("new_string", "new_content"):
            if isinstance(edit.get(key), str):
                body += edit[key] + "\n"
    return [PatchTarget(raw, body)]


def candidate_root(enf: dict) -> Path:
    root = (enf.get("candidate") or {}).get("root")
    if not root:
        raise Block(
            f"NO_CANDIDATE: run {enf.get('run')} has no candidate root; nothing may be written"
        )
    return Path(str(root)).resolve()


def inside_root(root: Path, raw: str, cwd: str) -> str | None:
    """The root-relative form of a write target, or None when it escapes."""
    if not isinstance(raw, str) or not raw.strip():
        raise Block("write tool did not provide a usable file path")
    path = Path(raw)
    if not path.is_absolute():
        base = Path(cwd).resolve() if cwd else root
        try:
            base.relative_to(root)
        except ValueError:
            base = root
        path = base / path
    try:
        return path.resolve(strict=False).relative_to(root).as_posix()
    except ValueError:
        return None


def check_write(enf: dict, tool: str, tool_input: dict, ev: dict, provider: str) -> None:
    """Check 6: a write belongs to the lease holder, in the root, in the fence."""
    root = candidate_root(enf)
    lease = enf.get("lease") or {}
    phase = enf.get("phase")
    try:
        targets = write_targets(tool, tool_input)
    except PolicyError as exc:
        raise Block(str(exc)) from exc
    mode = (phase_spec(enf.get("skill", ""), phase or "") or {}).get("writes", "none")
    if mode == "none":
        # D13 item 1: a judge phase has no write at all — not the candidate
        # root, not an evidence directory, not anywhere. Its write is denied on
        # exactly the terms a primary-window write is, and its evidence comes
        # back in the receipt's `findings` field instead.
        first = targets[0].path if targets else "that path"
        raise Block(judge_write_denial(enf, str(first)))
    if not lease:
        raise Block(
            f"NO_CANDIDATE: no lease is held for phase {phase}; a producer is bound at "
            "SubagentStart and writes only while it holds the lease"
        )
    elif provider == "claude":
        agent_id = ev.get("agent_id") or ""
        if not agent_id:
            raise Block(
                "writes in the primary window are denied while a run is active; the phase "
                f"worker writes inside {root}"
            )
        if agent_id != (lease.get("agent_id") or ""):
            raise Block(
                f"LEASE_HELD: the lease for phase {phase} belongs to {lease.get('agent')}/"
                f"{lease.get('agent_id')}, not to this caller"
            )
    for target in targets:
        relative = inside_root(root, target.path, str(ev.get("cwd") or ""))
        if relative is None:
            raise Block(
                f"{target.path} is outside the candidate root {root}; every write of this run "
                "lands in the root and reaches the project only by promotion"
            )
        try:
            validate_phase_write_path(root, enf, relative)
        except PolicyError as exc:
            raise Block(str(exc)) from exc


HOOK_ONLY_MESSAGE = (
    "`devforgeai {op}` is hook-only: it runs from the {event} hook, never from Bash. "
    "The producer writes inside the candidate root and returns one " + RESULT_SCHEMA
    + " receipt; the sequencer derives the change set, runs the oracle and advances."
)


def check_sequencer(argv: list[str], enf: dict, in_subagent: bool, agent_type: str,
                    ev: dict, provider: str) -> None:
    """Check 7: only the five primary forms, plus `run <key>` for the lease holder."""
    if argv == [SEQUENCER, "status"]:
        return
    active_run = bool(enf.get("run"))

    op = " ".join(argv[1:3]) if len(argv) > 2 and argv[1] == "phase" else (
        argv[1] if len(argv) > 1 else ""
    )
    if op in HOOK_ONLY:
        raise Block(HOOK_ONLY_MESSAGE.format(op=op, event=HOOK_ONLY[op]))
    if op == "candidate":
        raise Block(
            "`devforgeai candidate` is sequencer-internal; `phase start`, `ingest-result`, "
            "run end and `phase fail` call it. The model-callable form is "
            "`devforgeai promote <run>`."
        )

    if op == "run":
        if not active_run:
            raise Block("no DevForgeAI run is active; there is no candidate root to run in")
        if len(argv) != 3:
            raise Block("`devforgeai run <key>` takes exactly one stack command key")
        lease = enf.get("lease") or {}
        # Codex carries no identity on PreToolUse, so the root is the identity
        # there, exactly as it is for a write: a call whose cwd resolves inside
        # candidate.root is the producer working in it.
        inside = False
        if provider == "codex":
            root = candidate_root(enf)
            cwd = Path(str(ev.get("cwd") or "")).resolve() if ev.get("cwd") else None
            inside = bool(cwd and (cwd == root or root in cwd.parents))
        if not in_subagent and not inside:
            raise Block(
                "`devforgeai run <key>` belongs to the producer holding the phase lease, "
                "inside the candidate root; the primary window runs no stack command"
            )
        if not lease:
            raise Block(f"no lease is held for phase {enf.get('phase')}; nothing may be run")
        if provider == "claude" and (ev.get("agent_id") or "") != (lease.get("agent_id") or ""):
            raise Block(
                f"LEASE_HELD: the lease for phase {enf.get('phase')} belongs to "
                f"{lease.get('agent')}/{lease.get('agent_id')}, not to this caller"
            )
        if argv[2] not in phase_run_keys(enf):
            raise Block(
                f"phase {enf.get('phase')} grants {sorted(phase_run_keys(enf))}, not {argv[2]!r}"
            )
        return

    if in_subagent:
        raise Block(
            "phase workers call only `devforgeai status` and `devforgeai run <key>`; they "
            f"never sequence. Return one {RESULT_SCHEMA} receipt instead."
        )
    if argv[1:3] == ["phase", "start"] and not active_run and len(argv) >= 5:
        # `phase start <skill> <arg>`, optionally with any subset of
        # `PHASE_START_OPTIONS` in any order, each at most once. No other option
        # is in the model-callable grammar.
        options = argv[5:]
        if not any(word.startswith("-") for word in argv[3:5]) \
                and all(word in PHASE_START_OPTIONS for word in options) \
                and len(set(options)) == len(options):
            return
    if argv == [SEQUENCER, "validate"] and active_run:
        return
    if len(argv) == 5 and argv[1:4] == ["phase", "fail", "--reason"] and active_run and argv[4]:
        return
    if len(argv) == 3 and argv[1] == "promote" and argv[2]:
        return
    raise Block(
        f"primary may call only the {len(PRIMARY_CALLABLE)} model-callable operations "
        "(`devforgeai phase start <skill> <arg> [--fix] [--lenient]`, "
        "`devforgeai phase fail --reason <text>`, `devforgeai validate`, "
        "`devforgeai promote <run>`, `devforgeai status`), as allowed by current state"
    )


def check_research(argv: list[str], in_subagent: bool) -> None:
    """The Research Core runner: exactly ten subcommands, never from a worker."""
    if in_subagent:
        raise Block(
            "phase workers call only `devforgeai status` and `devforgeai run <key>`; Research "
            "Core writes its own fence and is called from the primary window, outside any phase."
        )
    op = argv[1] if len(argv) > 1 else ""
    if op not in RESEARCH_OPS:
        raise Block(
            f"`{RESEARCH_CLI} {op or '(no subcommand)'}` is not a Research Core operation; "
            f"the admitted set is {sorted(RESEARCH_OPS)}"
        )


def check_git(enf: dict, argv: list[str], ev: dict) -> None:
    """Read-only git inside the candidate root; every mutating form is denied."""
    subcommand = argv[1] if len(argv) > 1 else ""
    if subcommand not in GIT_READ_ONLY:
        raise Block(
            f"git {subcommand or '(no subcommand)'} mutates history or the tree; the sequencer "
            "owns the candidate root's branch, its checkpoints and its promotion"
        )
    dangerous = ("--config-env", "--exec", "--ext-diff", "--output", "--textconv")
    if any(arg == "-c" or arg.startswith(dangerous) for arg in argv[2:]):
        raise Block("git option can execute a helper or write output and is denied")
    if enf.get("run"):
        root = candidate_root(enf)
        cwd = Path(str(ev.get("cwd") or root)).resolve()
        try:
            cwd.relative_to(root)
        except ValueError:
            if ev.get("agent_id") or ev.get("agent_type"):
                raise Block(
                    f"a phase worker reads git inside its candidate root ({root}), not in the "
                    "canonical checkout"
                ) from None


def check_bash(enf: dict, command: str, in_subagent: bool, agent_type: str,
               ev: dict, provider: str) -> None:
    if not isinstance(command, str) or not command.strip():
        raise Block("empty shell command is not allow-listed")
    # One argv invocation only. This rejects redirects, pipelines, background
    # jobs, process substitution, command substitution and multi-command text.
    if re.search(r"[\r\n;&|<>`$]", command):
        raise Block("shell operators, redirects, substitutions and variables are not allow-listed")
    try:
        argv = shlex.split(command)
    except ValueError as exc:
        raise Block(f"cannot parse command: {exc}") from exc
    if not argv:
        raise Block("empty shell command is not allow-listed")
    if argv[0] == SEQUENCER:
        check_sequencer(argv, enf, in_subagent, agent_type, ev, provider)
        return
    if argv[0] == RESEARCH_CLI:
        check_research(argv, in_subagent)
        return

    head = argv[0]
    if head == "git":
        check_git(enf, argv, ev)
        return
    if head not in READ_ONLY_CMDS:
        raise Block(
            f"{command!r} is neither a safe read nor a model-callable devforgeai operation; "
            "stack commands run only through `devforgeai run <key>`"
        )
    if head == "rg" and any(
        arg == "--pre" or arg.startswith("--pre=")
        or arg == "--hostname-bin" or arg.startswith("--hostname-bin=")
        for arg in argv[1:]
    ):
        raise Block("rg helper-execution options are denied")


def sequencer_path() -> Path:
    path = Path(__file__).with_name("devforgeai.py")
    if not path.is_file():
        raise Block(f"sequencer is missing at {path}; failing closed")
    return path


def call_sequencer(root: Path, event: str, argv: list[str], stdin: str = "") -> tuple[int, str]:
    env = {**os.environ, "DEVFORGEAI_ROOT": str(root), "DEVFORGEAI_HOOK_EVENT": event}
    try:
        process = subprocess.run(
            [sys.executable, str(sequencer_path()), *argv],
            input=stdin, capture_output=True, text=True, cwd=root, env=env,
            timeout=SEQUENCER_TIMEOUT,
        )
    except subprocess.TimeoutExpired as exc:
        raise Block(f"sequencer timed out on `{' '.join(argv)}`; state was not accepted") from exc
    return process.returncode, (process.stdout + process.stderr).strip()


def bind_lease(root: Path, enf: dict, ev: dict) -> str:
    """SubagentStart: the only identity-bearing pre-write event on both providers."""
    code, output = call_sequencer(
        root, "SubagentStart",
        ["candidate", "lease", str(enf.get("run") or ""),
         "--agent", str(ev.get("agent_type") or ""),
         "--agent-id", str(ev.get("agent_id") or ""),
         "--session-id", str(ev.get("session_id") or "")],
    )
    if code:
        raise Block(output[-4000:] or f"lease bind exited {code}")
    return output


def ingest_result(root: Path, ev: dict, enf: dict) -> str:
    """Route an identity-bound SubagentStop receipt through the trusted broker.

    Claude Code documents `agent_id` and `agent_type` on any hook firing inside
    a subagent, and `last_assistant_message` on Stop and SubagentStop; Codex
    documents the same three on SubagentStop. When identity is absent the
    sequencer records a `could_not_run / hook_fault` result and hands off to the
    human rather than blocking a subagent that cannot fix it.
    """
    agent = ev.get("agent_type") or ""
    agent_id = ev.get("agent_id") or ""
    message = ev.get("last_assistant_message")
    if not isinstance(message, str):
        message = ""
    code, output = call_sequencer(
        root, "SubagentStop",
        ["--run", str(enf.get("run") or ""), "ingest-result", "--agent", agent,
         "--agent-id", agent_id, "--session-id", str(ev.get("session_id") or "")],
        stdin=message,
    )
    if code:
        raise Block(output[-6000:] or f"receipt broker exited {code}")
    return output[-6000:]


def worker_context(enf: dict) -> str:
    phase = enf.get("phase")
    agent = expected_agent(enf) or "<expected-agent>"
    root = (enf.get("candidate") or {}).get("root")
    writes = (phase_spec(enf.get("skill", ""), phase or "") or {}).get("writes", "none")
    prior = prior_findings(enf)
    job = (
        f"Read the checkpoint in {root} and judge it. You write nothing: no file, no "
        f"directory, no scratch note. Put your evidence in the receipt's `findings` field "
        f"(at most 16384 UTF-8 bytes, never truncated); the sequencer persists it verbatim "
        f"at {findings_path(enf)}."
        + (" Read the findings of the phases before you at: " + ", ".join(prior) + "."
           if prior else "")
        if writes == "none" else
        f"Write inside the candidate root {root}; every path you touch is relative to it and "
        f"must match {enf.get('write_fence')}. Run the tests with "
        f"`devforgeai run <key>` for {sorted(phase_run_keys(enf))}."
    )
    return (
        f"DevForgeAI {enf.get('skill')} phase {phase}. Your slice is "
        f".devforgeai/work/{enf.get('run')}/context.json in the canonical project, written by "
        "the sequencer at phase start; read it instead of re-opening the documents it "
        f"excerpts. {job} Finish with exactly one JSON object: "
        '{"schema":"' + RESULT_SCHEMA + '","run":"' + str(enf.get("run"))
        + '","skill":"' + str(enf.get("skill")) + '","phase":"' + str(phase)
        + '","agent":"' + agent + '","status":"pass|fail|needs_user|could_not_run",'
        '"candidate":{"id":"' + str(enf.get("run")) + '","input_checkpoint":"'
        + str((enf.get("candidate") or {}).get("checkpoint")) + '"},'
        '"claimed_paths":[],"evidence_refs":[],'
        + ('"findings":"<your evidence, at most 16384 UTF-8 bytes>",' if writes == "none" else "")
        + '"note":"","issues":[]}. '
        "No Markdown fence and no surrounding prose."
    )


def prior_findings(enf: dict) -> list[str]:
    """The findings files earlier phases of this run have already persisted.

    Named in the dispatch context so the next phase's worker can consume them
    by path (D13 item 3) without the sequencer copying any body forward. Read
    from the phase results the sequencer wrote, in phase order, so nothing here
    can disagree with what is on disk.
    """
    canonical = Path(str(enf.get("canonical") or "."))
    work = canonical / ".devforgeai" / "work" / str(enf.get("run") or "")
    rows: list[str] = []
    for phase in phase_names(str(enf.get("skill") or "")):
        if phase == enf.get("phase"):
            break
        result = work / f"{phase}-result.json"
        if not result.exists():
            continue
        try:
            reference = (json.loads(result.read_text()) or {}).get("findings_path")
        except (OSError, ValueError):
            continue
        if reference and reference not in rows:
            rows.append(str(reference))
    return rows


INSTALL_PREFIX = ".devforgeai/"


def check_installer_write(root: Path, tool: str, tool_input: dict) -> bool:
    """The one direct write path into `.devforgeai/`, and where it closes.

    `init` is the only skill that writes `.devforgeai/` itself: it has no
    sequencer operation, because there is no state for a sequencer to enforce
    until it has written one. That window is exactly "no `state.yaml` exists".
    Inside it, a write under `.devforgeai/` is permitted and everything else is
    denied as usual. The moment `state.yaml` exists the window closes: every
    path under `.devforgeai/` is the sequencer's, and a second `init` is denied
    by name rather than by the generic no-run message.

    `.claude/**`, `.codex/**`, `CLAUDE.md` and `AGENTS.md` are denied on both
    sides of the boundary. The dispatcher is itself one of the files `init`
    installs, so the provider hook fragments land before it is armed to see them.
    """
    installed = (root / ".devforgeai" / "state.yaml").exists()
    try:
        targets = write_targets(tool, tool_input)
    except PolicyError as exc:
        raise Block(str(exc)) from exc
    paths = []
    for target in targets:
        try:
            paths.append(project_relative(root, target.path))
        except PolicyError as exc:
            raise Block(str(exc)) from exc
    under = [p for p in paths if p.startswith(INSTALL_PREFIX)]
    if installed:
        if under:
            raise Block(
                f"{under[0]} is written by the devforgeai sequencer, not by a skill. The "
                "installer skill writes .devforgeai/ directly only while no state.yaml "
                "exists; this repository is already installed."
            )
        return False  # not an installer write; the run rules decide
    if under and len(under) == len(paths):
        return True  # the installation window: .devforgeai/ only, nothing else
    raise Block(
        "DevForgeAI is not installed in this repository: until the installer skill has "
        "written .devforgeai/state.yaml, the only writable prefix is .devforgeai/"
    )


def check_stop(root: Path, enf: dict, ev: dict) -> None:
    if ev.get("stop_hook_active"):
        return  # already blocked once this turn; never loop
    attempts = (enf.get("attempts") or {}).get(enf.get("phase"), 0)
    limit = (enf.get("max_attempts") or {}).get(enf.get("phase"), 2)
    if attempts >= limit:
        return  # REQUIRE_HUMAN path: let the turn end so the user sees the handoff
    p = root / ".devforgeai" / "work" / enf["run"] / "handoff.json"
    if not p.exists():
        raise Block(
            f"run {enf['run']} is active at phase {enf.get('phase')} and no handoff envelope "
            "exists; dispatch the worker named by the active phase"
        )


# ---------- dispatch ----------

def session_start(root: Path, ev: dict, provider: str) -> str:
    """SessionStart writes the session evidence file through the sequencer."""
    argv = [
        "session-start",
        "--session-id", str(ev.get("session_id") or "unknown"),
        "--provider", provider,
        "--provider-version", str(ev.get("version") or ev.get("provider_version") or "unknown"),
    ]
    code, output = call_sequencer(root, "SessionStart", argv)
    if code:
        # SessionStart cannot block; surface the fault as context, not a denial.
        return f"DevForgeAI session-start failed (exit {code}): {output[-2000:]}"
    return output


def handle(ev: dict, provider: str, root: Path) -> int:
    event = ev.get("hook_event_name", "")
    tool = ev.get("tool_name", "")
    ti = ev.get("tool_input") or {}
    in_subagent = bool(ev.get("agent_id") or ev.get("agent_type"))
    agent_type = ev.get("agent_type") or ""

    if event == "SessionStart":
        print(session_start(root, ev, provider))
        return 0

    state = load_state(root)
    enf = active(state, root, ev)

    if event == "SubagentStart" and enf:
        if not agent_type:
            # Claude Code runs internal helper subagents (observed live 2026-09-03:
            # the auto-mode classifier fires SubagentStart/Stop with an agent_id and
            # no agent_type, every 10-30 s while a worker runs). They are not
            # workers: no lease, no check, no block. The raw-event log keeps them.
            return 0
        check_worker(enf, agent_type)
        bind_lease(root, enf, ev)
        ev["_hook_output"] = {
            "hookSpecificOutput": {
                "hookEventName": "SubagentStart",
                "additionalContext": worker_context(load_run(root, enf["run"]) or enf),
            }
        }
        return 0

    if event == "ConfigChange":
        if enf:
            raise Block("settings may not change while a DevForgeAI run is active")
        return 0

    if event == "PermissionRequest":
        if enf:
            raise Block("sandbox or network escalation is disabled while a run is active")
        return 0

    if event == "PreToolUse":
        if tool.startswith("mcp__"):
            if enf:
                raise Block("MCP tools are not in the run capability allowlist while a run is active")
            return 0
        if tool in WRITE_TOOLS:
            if not enf:
                if check_installer_write(root, tool, ti):
                    return 0  # the installation window, before any state exists
                raise Block("no DevForgeAI run is active; run `devforgeai phase start <skill> <arg>` first")
            check_write(enf, tool, ti, ev, provider)
            return 0
        if tool == "Bash":
            if not enf and in_subagent:
                raise Block("no DevForgeAI run is active; subagents have no phase to work in")
            check_bash(enf or {}, ti.get("command", ""), in_subagent, agent_type, ev, provider)
            return 0
        if tool == "Agent":
            if not enf:
                raise Block("no DevForgeAI run is active; run `devforgeai phase start <skill> <arg>` first")
            if in_subagent:
                raise Block("phase workers may not spawn nested agents")
            requested = ti.get("subagent_type") or ti.get("agent_type") or ti.get("task_name") or ""
            check_agent(enf, requested)
            return 0
        return 0

    if event == "PostToolUse" and tool in WRITE_TOOLS and enf:
        # A write that completed is accepted only if the pre-hook would have
        # admitted it; anything else changed a tree no checkpoint will accept.
        check_write(enf, tool, ti, ev, provider)
        return 0

    if event == "SubagentStop" and enf:
        if not agent_type:
            # An internal helper subagent stopping, not the worker (see
            # SubagentStart above). Ingesting it would record a hook fault and
            # release the worker's lease mid-phase; ignore it instead.
            return 0
        ev["_system_message"] = ingest_result(root, ev, enf)
        return 0

    if event == "Stop" and enf:
        check_stop(root, enf, ev)
        return 0

    return 0


def record_raw_event(root: Path, ev: dict) -> None:
    """Append the shape of every hook event (keys and identity, never bodies)
    to `.devforgeai/sessions/raw-events.jsonl`. This is the evidence that tells
    a stray or identity-less event apart from a dispatcher bug."""
    try:
        import time as _t
        row = {
            "at": _t.strftime("%Y-%m-%dT%H:%M:%SZ", _t.gmtime()),
            "event": ev.get("hook_event_name"),
            "keys": sorted(ev.keys()),
            "agent_id": ev.get("agent_id"),
            "agent_type": ev.get("agent_type"),
            "tool_name": ev.get("tool_name"),
            "stop_hook_active": ev.get("stop_hook_active"),
            "session_id": ev.get("session_id"),
            "message_len": len(ev.get("last_assistant_message") or "") if isinstance(ev.get("last_assistant_message"), str) else None,
        }
        base = Path(root) / ".devforgeai"
        if not base.is_dir():
            return  # not a DevForgeAI project: never create state on SessionStart
        path = base / "sessions" / "raw-events.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, sort_keys=True) + "\n")
    except Exception:
        pass


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", choices=["claude", "codex"], default="claude")
    ap.add_argument("--root")
    args = ap.parse_args()
    try:
        ev = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        sys.stderr.write(f"dispatch: bad event JSON: {e}\n")
        return 1
    start = args.root or os.environ.get("CLAUDE_PROJECT_DIR") or ev.get("cwd") or os.getcwd()
    root = discover_root(start)
    record_raw_event(root, ev)
    try:
        result = handle(ev, args.provider, root)
        if ev.get("_hook_output"):
            print(json.dumps(ev["_hook_output"]))
            return result
        # Codex documents JSON output for these two successful stop events.
        if args.provider == "codex" and ev.get("hook_event_name") in {"Stop", "SubagentStop"}:
            message = ev.get("_system_message")
            print(json.dumps({"systemMessage": message}) if message else "{}")
        elif ev.get("_system_message"):
            print(ev["_system_message"])
        return result
    except (Block, PolicyError) as b:
        if args.provider == "codex" and ev.get("hook_event_name") == "PermissionRequest":
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PermissionRequest",
                    "decision": {"behavior": "deny", "message": f"DevForgeAI: {b}"},
                }
            }))
            return 0
        sys.stderr.write(f"DevForgeAI: {b}\n")
        return 2
    except Exception as e:  # dispatcher fault: fail loud, not silent
        sys.stderr.write(f"dispatch fault: {type(e).__name__}: {e}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
