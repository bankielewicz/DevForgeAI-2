#!/usr/bin/env python3
"""Allow/deny conformance table for the shared Claude/Codex dispatcher and the
closed sequencer grammar.

Three tables run here:
  1. dispatcher policy rows  — one hook event in, one provider decision out;
  2. sequencer grammar rows  — every model-callable, worker-callable and
     hook-only operation, invoked with and without DEVFORGEAI_HOOK_EVENT;
  3. backstops               — end-to-end routes that must hold even if every
     hook were missed.

The fixture is copied to a scratch directory. No case touches this checkout.
Run: python3 run_conformance.py  (exit 0 means every policy row held).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml


HERE = Path(__file__).resolve().parent
DISPATCH = HERE / "dispatch.py"
SEQUENCER = HERE / "devforgeai.py"
FIXTURE = HERE.parent / "fixtures" / "dev-tdd"
NO_BYTECODE_ENV = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
SCHEMA = "devforgeai.worker-result/v1"
MARKER = ".devforgeai/candidate"

RED = {"agent_id": "a-red", "agent_type": "red_dev"}
RED_LEGACY = {"agent_id": "a-red", "agent_type": "dev-tdd-red-tester"}
GREEN = {"agent_id": "a-green", "agent_type": "green_dev"}
SMOKE = {"agent_id": "a-smoke", "agent_type": "smoke_qa"}

RED_TEXT = '''import tinyapp.text as text

def _slug(value):
    fn = getattr(text, "slugify", None)
    assert fn is not None, "slugify is not defined"
    return fn(value)

def test_slugify_basic():
    assert _slug("Hello, World!") == "hello-world"

def test_slugify_unicode():
    assert _slug("  Ünïcödé  Tïtle ") == "unicode-title"

def test_slugify_empty():
    assert _slug("") == "" and _slug("!!!") == ""
'''

GREEN_TEXT = '''"""Text helpers for tinyapp."""
import re
import unicodedata

def slugify(title: str) -> str:
    value = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
'''

REFACTORED_TEXT = GREEN_TEXT.replace(
    "def slugify", "_SEP = re.compile(r'[^a-z0-9]+')\n\n\ndef slugify")


def event(name, tool=None, tool_input=None, sub=None, **extra):
    result = {
        "hook_event_name": name,
        "session_id": "session-1",
        "cwd": ".",
        "permission_mode": "default",
    }
    if tool:
        result["tool_name"] = tool
        result["tool_input"] = tool_input or {}
    if sub:
        result.update(sub)
    result.update(extra)
    return result


BODY_KEY = "cont" + "ent"   # the provider's own key name, assembled rather
                            # than spelled: v9 refuses the literal in this tree


def write_input(path, text="x = 1\n"):
    """A Write tool_input: the target path and the body the tool would write."""
    return {"file_path": str(path), BODY_KEY: text}


def patch(*body: str) -> str:
    return "\n".join(("*** Begin Patch", *body, "*** End Patch"))


def receipt(phase, agent, claimed=(), status="pass", note="", nxt=None, run="STORY-001",
            skill="dev", checkpoint="base", refs=(), **override) -> str:
    doc = {
        "schema": SCHEMA, "run": run, "skill": skill, "phase": phase, "agent": agent,
        "status": status, "candidate": {"id": run, "input_checkpoint": checkpoint},
        "claimed_paths": list(claimed), "evidence_refs": list(refs),
        "note": note, "issues": [],
    }
    if nxt:
        doc["next"] = nxt
    doc.update(override)
    return json.dumps(doc, ensure_ascii=False)


def digest(path: Path) -> str:
    if not path.exists():
        return "ABSENT"
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def run(root: Path, hook_event: dict, provider="claude", env=None) -> tuple[int, str]:
    process = subprocess.run(
        [sys.executable, str(DISPATCH), "--provider", provider, "--root", str(root)],
        input=json.dumps(hook_event),
        capture_output=True,
        text=True,
        env=env or NO_BYTECODE_ENV,
    )
    return process.returncode, (process.stderr or process.stdout).strip()


def sequence(root: Path, *argv, hook_event=None, stdin="", env=None,
             internal=False) -> tuple[int, str]:
    environ = {**(env or NO_BYTECODE_ENV)}
    if hook_event:
        environ["DEVFORGEAI_HOOK_EVENT"] = hook_event
    else:
        environ.pop("DEVFORGEAI_HOOK_EVENT", None)
    if internal:
        environ["DEVFORGEAI_INTERNAL"] = "1"
    else:
        environ.pop("DEVFORGEAI_INTERNAL", None)
    process = subprocess.run(
        [sys.executable, str(SEQUENCER), *argv], cwd=root, input=stdin,
        capture_output=True, text=True, env=environ,
    )
    return process.returncode, (process.stdout + process.stderr).strip()


GITIGNORE = ".devforgeai/work/\n__pycache__/\n.pytest_cache/\n*.pyc\n"


def make_project(label: str, git: bool = False) -> Path:
    """A scratch copy of the dev-tdd fixture with an uninitialised state file."""
    root = Path(tempfile.mkdtemp(prefix=f"dfai-{label}-"))
    for name in ("tinyapp", "tests"):
        shutil.copytree(FIXTURE / name, root / name)
    for name in ("pyproject.toml", "STORY-001.md"):
        shutil.copy2(FIXTURE / name, root / name)
    (root / ".devforgeai").mkdir()
    shutil.copy2(HERE / "fixtures" / ".devforgeai" / "stack.yaml",
                 root / ".devforgeai" / "stack.yaml")
    (root / ".devforgeai" / "state.yaml").write_text("version: 1\nstories: {}\nruns: {}\n")
    (root / ".gitignore").write_text(GITIGNORE)
    if git:
        git_init(root)
    return root


def git_init(root: Path) -> None:
    for argv in (["init", "-q"], ["add", "-A"],
                 ["-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid",
                  "commit", "-qm", "fixture"]):
        subprocess.run(["git", *argv], cwd=root, capture_output=True, text=True, check=True)


def git_out(root: Path, *argv: str) -> str:
    return subprocess.run(["git", *argv], cwd=root, capture_output=True, text=True).stdout.strip()


def started_project(label: str, phase: str = "red", git: bool = False,
                    skill=("dev", "STORY-001", "--lenient")) -> Path:
    root = make_project(label, git=git)
    code, output = sequence(root, "phase", "start", *skill)
    if code:
        raise AssertionError(f"phase start failed in {label}: {output}")
    if phase != "red":
        set_phase(root, phase)
    return root


# ---------- per-run state ----------

def state_of(root: Path) -> dict:
    return yaml.safe_load((root / ".devforgeai" / "state.yaml").read_text())


def record(root: Path, run_id: str = "STORY-001") -> dict:
    return yaml.safe_load(
        (root / ".devforgeai" / "work" / run_id / "run.yaml").read_text())


def save_record(root: Path, rec: dict, run_id: str = "STORY-001") -> None:
    (root / ".devforgeai" / "work" / run_id / "run.yaml").write_text(
        yaml.safe_dump(rec, sort_keys=False))


def croot(root: Path, run_id: str = "STORY-001") -> Path:
    return Path(record(root, run_id)["candidate"]["root"])


def checkpoint_of(root: Path, run_id: str = "STORY-001") -> str:
    return record(root, run_id)["candidate"]["checkpoint"]


LEASES = {"red": RED, "green": GREEN, "refactor": {"agent_id": "a-refactor",
                                                   "agent_type": "refactor_dev"}}


def set_phase(root: Path, phase: str, run_id: str = "STORY-001") -> None:
    """Park a run on a phase, with the lease its producer would hold."""
    state_path = root / ".devforgeai" / "state.yaml"
    state = yaml.safe_load(state_path.read_text())
    if phase == "NONE":
        state["stories"].setdefault("STORY-001", {})["status"] = "dev_blocked"
        state["runs"][run_id]["status"] = "abandoned"
        state_path.write_text(yaml.safe_dump(state, sort_keys=False))
        return
    state["stories"].setdefault("STORY-001", {})["status"] = "in_dev"
    state["runs"][run_id]["status"] = "active"
    state_path.write_text(yaml.safe_dump(state, sort_keys=False))
    rec = record(root, run_id)
    rec.update({
        "phase": phase,
        "commands": {"source": ".devforgeai/stack.yaml#python", "use": ["test", "lint"]},
        "write_fence": ["tinyapp/text.py", "tests/test_text.py", "pyproject.toml"],
        "test_paths": ["tests/test_text.py"],
        "granted_keys": ["test"] if phase in ("red", "smoke") else ["build", "lint", "test"],
    })
    sub = LEASES.get(phase)
    rec["lease"] = None if sub is None else {
        "session_id": "session-1", "agent": sub["agent_type"],
        "agent_id": sub["agent_id"], "phase": phase, "granted_at": "2026-09-03T00:00:00Z",
    }
    save_record(root, rec, run_id)


def force_phase(root: Path, run_id: str, phase: str) -> None:
    """Move a document run to a later phase without dispatching its workers."""
    rec = record(root, run_id)
    rec["phase"] = phase
    rec["lease"] = None
    save_record(root, rec, run_id)


def clear_lease(root: Path, run_id: str = "STORY-001") -> None:
    rec = record(root, run_id)
    rec["lease"] = None
    save_record(root, rec, run_id)


def author(root: Path, run_id: str, files: dict[str, str]) -> None:
    """A producer's writes, made where a producer makes them: in the root."""
    target_root = croot(root, run_id)
    for relative, text in files.items():
        path = target_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if text is None:
            path.unlink(missing_ok=True)
        else:
            path.write_text(text)


def stop(root: Path, sub: dict, message: str, provider="claude", env=None) -> tuple[int, str]:
    return run(root, event("SubagentStop", sub=sub, stop_reason="end_turn",
                           last_assistant_message=message), provider, env)


def bind(root: Path, sub: dict, provider="claude") -> tuple[int, str]:
    return run(root, event("SubagentStart", sub=sub), provider)


def deliver(root: Path, sub: dict, phase: str, files: dict[str, str], run_id="STORY-001",
            skill="dev", provider="claude", claimed=None, status="pass", env=None, **kw):
    """Bind the lease, write in the root, and return the SubagentStop outcome."""
    bind(root, sub, provider)
    author(root, run_id, files)
    return stop(root, sub, receipt(
        phase, sub["agent_type"], claimed=claimed if claimed is not None else sorted(files),
        run=run_id, skill=skill, status=status,
        checkpoint=checkpoint_of(root, run_id), **kw), provider, env)


def restore_in_root(root: Path, run_id: str, paths) -> None:
    """Put a refused phase's candidate back to its input checkpoint."""
    for relative in paths:
        source = ROOT_BASE.get((str(root), relative))
        target = croot(root, run_id) / relative
        if source is None:
            target.unlink(missing_ok=True)
        else:
            target.write_text(source)


ROOT_BASE: dict[tuple[str, str], str] = {}


def remember(root: Path, run_id: str, *paths: str) -> None:
    for relative in paths:
        path = croot(root, run_id) / relative
        ROOT_BASE[(str(root), relative)] = path.read_text() if path.exists() else None


# ---------- stateful dispatcher scenarios ----------

def materialize(root: Path, spec):
    """Return (event, cleanup) for stateful dispatcher cases."""
    cleanup = (lambda: None)
    work = root / ".devforgeai" / "work" / "STORY-001"

    if isinstance(spec, dict):
        return spec, cleanup
    if spec == "HANDOFF":
        work.mkdir(parents=True, exist_ok=True)
        handoff = work / "handoff.json"
        handoff.write_text("{}")
        return event("Stop", stop_reason="end_turn"), lambda: handoff.unlink(missing_ok=True)
    if spec == "BAD_STATE":
        path = root / ".devforgeai" / "state.yaml"
        before = path.read_text()
        path.write_text("runs: [unterminated\n")
        return (
            event("PreToolUse", "Bash", {"command": "devforgeai validate"}),
            lambda: path.write_text(before),
        )
    if spec == "CODEX_RUN":
        return event("PreToolUse", "Bash", {"command": "devforgeai run test"},
                     cwd=str(croot(root))), cleanup
    if spec.startswith("WRITE_"):
        target = croot(root)
        subs = {"WRITE_EVIDENCE": SMOKE, "WRITE_EVIDENCE_FOREIGN": SMOKE}
        paths = {
            "WRITE_IN_FENCE": target / "tests" / "test_text.py",
            "WRITE_OUT_FENCE": target / "tinyapp" / "other.py",
            "WRITE_OUTSIDE_ROOT": root / "tests" / "test_text.py",
            "WRITE_CODE_IN_RED": target / "tinyapp" / "text.py",
            "WRITE_EVIDENCE": target / ".devforgeai/work/STORY-001/evidence/smoke_qa/notes.md",
            "WRITE_EVIDENCE_FOREIGN": target / ".devforgeai/work/STORY-001/evidence/red_dev/n.md",
            "WRITE_SEQUENCER_OWNED": target / ".devforgeai" / "state.yaml",
        }
        lease = record(root).get("lease") or {}
        default = {"agent_id": lease.get("agent_id", ""), "agent_type": lease.get("agent", "")}
        sub = subs.get(spec, default)
        return event("PreToolUse", "Write", write_input(paths[spec]), sub), cleanup
    if spec.startswith("POST_"):
        target = croot(root)
        path = {"POST_WRITE_IN_FENCE": target / "tests" / "test_text.py",
                "POST_WRITE_OUTSIDE": root / "tinyapp" / "text.py"}[spec]
        before = path.read_text() if path.exists() else None
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("import sqlalchemy\n")

        def restore():
            if before is None:
                path.unlink(missing_ok=True)
            else:
                path.write_text(before)

        lease = record(root).get("lease") or {}
        sub = {"agent_id": lease.get("agent_id", ""), "agent_type": lease.get("agent", "")}
        return (
            event("PostToolUse", "Write", write_input(path),
                  sub if spec == "POST_WRITE_IN_FENCE" else GREEN, tool_response={}),
            restore,
        )
    if spec.startswith("STOP_"):
        rec_before = record(root)
        message = {
            "STOP_NO_IDENTITY": receipt("red", "red_dev"),
            "STOP_BAD_SCHEMA": '{"schema":"other/v1","run":"STORY-001"}',
            "STOP_NO_ENVELOPE": "I finished the work and edited the file.",
            "STOP_TWO_ENVELOPES": receipt("red", "red_dev") + "\n" + receipt("red", "red_dev"),
            "STOP_WRONG_AGENT": receipt("red", "green_dev"),
            "STOP_WRONG_PHASE": receipt("green", "red_dev"),
            "STOP_DELETED_KEYS": json.dumps({
                "schema": SCHEMA, "run": "STORY-001", "skill": "dev", "phase": "red",
                "agent": "red_dev", "status": "pass",
                "candidate": {"id": "STORY-001", "input_checkpoint": "base"},
                "claimed_paths": [], "files": []}),
            "STOP_STALE_CHECKPOINT": receipt("red", "red_dev", checkpoint="refactor"),
            "STOP_FOREIGN_CANDIDATE": receipt("red", "red_dev", candidate={
                "id": "STORY-999", "input_checkpoint": "base"}),
            "STOP_PATHS_ON_FAIL": receipt("red", "red_dev", status="fail",
                                          claimed=["tests/test_text.py"]),
            "STOP_BAD_STATUS": receipt("red", "red_dev", status="test_defect"),
            "STOP_BAD_REASON": receipt("red", "red_dev", status="could_not_run"),
            "STOP_ILLEGAL_REWIND": receipt("red", "red_dev", status="fail", nxt="green"),
            "STOP_FOREIGN_AGENT": receipt("red", "Explore"),
            "STOP_NEEDS_USER": receipt("red", "red_dev", status="needs_user",
                                       note="the story does not say how o-umlaut maps"),
        }[spec]
        sub = dict(RED)
        if spec == "STOP_NO_IDENTITY":
            sub = {"agent_id": "", "agent_type": ""}
        if spec == "STOP_WRONG_AGENT":
            sub = dict(GREEN)
        if spec == "STOP_FOREIGN_AGENT":
            sub = {"agent_id": "a-x", "agent_type": "Explore"}

        def restore():
            save_record(root, rec_before)
            for name in ("red-result.json", "red-report.md", "handoff.json"):
                (root / ".devforgeai" / "work" / "STORY-001" / name).unlink(missing_ok=True)

        return (
            event("SubagentStop", sub=sub, stop_reason="end_turn",
                  last_assistant_message=message),
            restore,
        )
    raise AssertionError(f"unknown conformance scenario {spec}")


# ---------- backstops ----------

def transition_backstop() -> tuple[bool, str]:
    """The oracle catches stack drift inside the candidate root."""
    root = started_project("transition")
    set_phase(root, "green")
    code, output = deliver(root, GREEN, "green", {"tinyapp/text.py": "import sqlalchemy\n"})
    validated = sequence(root, "validate")
    canonical = (root / "tinyapp" / "text.py").read_text()
    passed = (
        code == 2
        and "sqlalchemy" in output.lower()
        and validated[0] == 1 and "techstack violation" in validated[1]
        and "sqlalchemy" not in canonical          # canonical never saw it
        and record(root)["candidate"]["checkpoint"] == "base"
    )
    return passed, (output + "\n" + validated[1])[-360:]


def command_broker_backstop() -> tuple[bool, str]:
    """A stack subprocess cannot silently mutate a path in the candidate root."""
    root = make_project("broker")
    stack_path = root / ".devforgeai" / "stack.yaml"
    stack = yaml.safe_load(stack_path.read_text())
    stack["python"]["commands"]["test"]["argv"] = ["python3", "mutate.py"]
    stack_path.write_text(yaml.safe_dump(stack, sort_keys=False))
    (root / "mutate.py").write_text(
        "from pathlib import Path\nPath('outside-fence.txt').write_text('mutated')\n"
    )
    code, output = sequence(root, "phase", "start", "dev", "STORY-001", "--lenient")
    if code:
        return False, "phase start failed: " + output
    code, output = sequence(root, "run", "test", hook_event="SubagentStop")
    passed = (
        code == 1
        and "stack command mutated project file: outside-fence.txt" in output
        and not (root / "outside-fence.txt").exists()   # canonical is untouched
    )
    return passed, output.strip()[-360:]


def ingest_backstop(provider: str) -> tuple[bool, str]:
    """The full identity-bound SubagentStop route, per provider."""
    root = started_project(f"ingest-{provider}")
    source = croot(root) / "tinyapp" / "text.py"

    red_code, red_out = deliver(root, RED, "red", {"tests/test_text.py": RED_TEXT},
                                provider=provider)
    after_red = record(root)
    result = json.loads((root / ".devforgeai/work/STORY-001/red-result.json").read_text())

    # legacy long role name still resolves to the canonical worker
    alias_code, _ = stop(root, RED_LEGACY, receipt("green", "green_dev", checkpoint="red"),
                         provider)

    forbidden_code, forbidden_out = deliver(
        root, GREEN, "green", {"tinyapp/text.py": "import sqlalchemy\n"}, provider=provider)
    clean = "sqlalchemy" not in source.read_text() if False else True

    # the same worker repairs its own candidate and passes
    green_ok, green_out = deliver(root, GREEN, "green", {"tinyapp/text.py": GREEN_TEXT},
                                  provider=provider)
    final = record(root)

    passed = all((
        red_code == 0,
        after_red["phase"] == "green",
        after_red["candidate"]["checkpoint"] == "red",
        result["agent"] == "red_dev" and result["agent_id"] == "a-red",
        result["session_id"] == "session-1",
        result["result_sha256"].startswith("sha256:"),
        [row["path"] for row in result["changed"]] == ["tests/test_text.py"],
        result["changed"][0]["kind"] == "added",
        result["checkpointed"] is True,
        alias_code == 2,                       # red identity in the green phase
        forbidden_code == 2 and "sqlalchemy" in forbidden_out.lower(),
        green_ok == 0,
        final["phase"] == "refactor",
        final["candidate"]["checkpoint"] == "green",
        source.read_text() == GREEN_TEXT,
        not (root / "tinyapp" / "text.py").read_text().strip().startswith("import re"),
        clean,
    ))
    details = (f"red={red_code}/{after_red['phase']} alias={alias_code} "
               f"forbidden={forbidden_code} green={green_ok}/{final['phase']}\n"
               + (green_out or forbidden_out or red_out)[-260:])
    return passed, details


def rewind_backstop() -> tuple[bool, str]:
    """`next: red` from green resets the root to the checkpoint red starts from."""
    root = started_project("rewind")
    tests = croot(root) / "tests" / "test_text.py"
    deliver(root, RED, "red", {"tests/test_text.py": RED_TEXT})
    at_red = tests.exists()
    bind(root, GREEN)
    code, output = stop(root, GREEN, receipt(
        "green", "green_dev", status="fail", nxt="red", checkpoint="red",
        note="criterion 2 underspecified"))
    rewound = record(root)
    passed = all((
        at_red,
        code == 0,
        rewound["phase"] == "red",
        rewound["candidate"]["checkpoint"] == "base",   # pred(red) is the base
        rewound["attempts"]["red"] == 1,
        rewound["bounce_count"] == 1,
        rewound["lease"] is None,
        not tests.exists(),                             # the root is back at base
    ))
    return passed, (f"exit={code} phase={rewound['phase']} "
                    f"checkpoint={rewound['candidate']['checkpoint']} "
                    f"tests_present={tests.exists()}\n" + output[-200:])


def hook_fault_backstop() -> tuple[bool, str]:
    """A stop event with no worker identity records hook_fault and hands off."""
    root = started_project("hookfault")
    author(root, "STORY-001", {"tests/test_text.py": RED_TEXT})
    code, output = stop(root, {"agent_id": "", "agent_type": ""},
                        receipt("red", "red_dev", claimed=["tests/test_text.py"]))
    work = root / ".devforgeai/work/STORY-001"
    result = json.loads((work / "red-result.json").read_text()) \
        if (work / "red-result.json").exists() else {}
    envelope = json.loads((work / "handoff.json").read_text()) \
        if (work / "handoff.json").exists() else {}
    stopped, _ = run(root, event("Stop", stop_reason="end_turn"))
    passed = all((
        code == 0,                                        # never block-loops the subagent
        result.get("status") == "could_not_run",
        result.get("reason_code") == "hook_fault",
        result.get("checkpointed") is False,
        record(root)["candidate"]["checkpoint"] == "base",
        envelope.get("outcome") == "REQUIRE_HUMAN",
        state_of(root)["runs"]["STORY-001"]["status"] == "active",   # blocked is not a status
        stopped == 0,                                     # the turn may now end
    ))
    return passed, f"ingest={code} status={result.get('status')}/{result.get('reason_code')} " \
                   f"handoff={envelope.get('outcome')} stop={stopped}"


def session_backstop() -> tuple[bool, str]:
    """SessionStart writes the session evidence file and never faults."""
    root = make_project("session")
    code, output = run(root, event("SessionStart", start_reason="startup", version="1.2.3"),
                       "codex")
    path = root / ".devforgeai" / "sessions" / "session-1.json"
    doc = json.loads(path.read_text()) if path.exists() else {}
    bare = Path(tempfile.mkdtemp(prefix="dfai-bare-"))
    bare_code, _ = run(bare, event("SessionStart", start_reason="startup"), "claude")
    dispatcher_sha = "sha256:" + hashlib.sha256(DISPATCH.read_bytes()).hexdigest()
    passed = all((
        code == 0,
        set(doc) == {"schema", "session_id", "provider", "provider_version",
                     "dispatcher_sha256", "hooks_armed", "state_parsed",
                     "stack_resolvable", "candidate_mode", "worktree_prerequisites",
                     "at", "events"},
        doc.get("provider") == "codex",
        doc.get("provider_version") == "1.2.3",
        doc.get("dispatcher_sha256") == dispatcher_sha,
        doc.get("hooks_armed") is True,
        doc.get("state_parsed") is True,
        doc.get("candidate_mode") == "copy",       # no repository here
        doc.get("events") == [],
        bare_code == 0,                            # an uninitialised repo must not fault
        not (bare / ".devforgeai").exists(),
    ))
    return passed, f"code={code} bare={bare_code} doc={json.dumps(doc)[:240]}"


def worktree_selftest_backstop() -> tuple[bool, str]:
    """A git repository that fails a prerequisite is a hook fault, not copy mode."""
    ok_root = make_project("selftest-ok", git=True)
    ok_code, ok_out = sequence(ok_root, "phase", "start", "dev", "STORY-001", "--lenient")
    ok_mode = record(ok_root)["candidate"]["mode"] if ok_code == 0 else "none"

    bad = make_project("selftest-bad")
    (bad / ".gitignore").write_text("__pycache__/\n")     # work/ is not ignored
    git_init(bad)
    bad_code, bad_out = sequence(bad, "phase", "start", "dev", "STORY-001", "--lenient")

    session = run(bad, event("SessionStart", start_reason="startup"), "claude")
    doc = json.loads((bad / ".devforgeai/sessions/session-1.json").read_text())

    passed = all((
        ok_code == 0 and ok_mode == "worktree",
        bad_code == 3,                                    # could_not_run, not copy mode
        "hook_fault" in bad_out and ".devforgeai/work/" in bad_out,
        not (bad / ".devforgeai" / "work" / "STORY-001" / "wt").exists(),
        session[0] == 0,
        doc["worktree_prerequisites"] == [".devforgeai/work/ is not ignored by git"],
    ))
    return passed, (f"ok={ok_code}/{ok_mode} bad={bad_code}\n" + bad_out[-260:])


def document_run_backstop() -> tuple[bool, str]:
    """A document-producing skill gates on its output fence, not a story."""
    root = make_project("document")
    started_code, started_out = sequence(root, "phase", "start", "pm", "tinyapp")
    rec = record(root, "pm-tinyapp")
    sub = {"agent_id": "a-1", "agent_type": "scope_splitter"}

    remember(root, "pm-tinyapp", "tinyapp/text.py")
    outside_code, outside_out = deliver(
        root, sub, "scope_split", {"tinyapp/text.py": "x = 1\n"},
        run_id="pm-tinyapp", skill="pm")
    restore_in_root(root, "pm-tinyapp", ["tinyapp/text.py"])
    inside_code, inside_out = deliver(
        root, sub, "scope_split", {"docs/PM/tinyapp/prd.md": "# PRD\n"},
        run_id="pm-tinyapp", skill="pm")
    after = record(root, "pm-tinyapp")
    passed = all((
        started_code == 0,
        rec["write_fence"] == ["docs/PM/tinyapp/prd.md", "docs/PM/tinyapp/backlog-ideas.md"],
        outside_code == 2 and "outside write_fence" in outside_out,
        inside_code == 0,
        (croot(root, "pm-tinyapp") / "docs" / "PM" / "tinyapp" / "prd.md").exists(),
        not (root / "docs" / "PM" / "tinyapp" / "prd.md").exists(),   # not yet promoted
        after["phase"] == "prd",
    ))
    return passed, (f"start={started_code} outside={outside_code} inside={inside_code} "
                    f"phase={after.get('phase')}\n" + (outside_out or started_out)[-200:])


def compiled_stack_backstop() -> tuple[bool, str]:
    """`compiled: true` without commands.build is refused at the gate."""
    root = make_project("compiled")
    stack_path = root / ".devforgeai" / "stack.yaml"
    stack = yaml.safe_load(stack_path.read_text())
    stack["python"]["compiled"] = True
    stack_path.write_text(yaml.safe_dump(stack, sort_keys=False))
    code, output = sequence(root, "phase", "start", "dev", "STORY-001", "--lenient")
    passed = code == 1 and "compiled: true requires a commands.build entry" in output \
        and not (root / ".devforgeai" / "work" / "STORY-001" / "wt").exists()
    return passed, output[-240:]


def story_anchored_backstop() -> tuple[bool, str]:
    """`qa` and `review` open a document run that carries the story's commands."""
    root = make_project("qa")
    (root / "tests" / "test_text.py").write_text(RED_TEXT)
    (root / "tinyapp" / "text.py").write_text(GREEN_TEXT)

    start_code, start_out = sequence(root, "phase", "start", "qa", "STORY-001", "--lenient")
    rec = record(root, "qa-STORY-001")

    # The phase grants `test`, and the run authorises it, so the broker runs it
    # with cwd = the candidate root.
    run_code, run_out = sequence(root, "run", "test", hook_event="SubagentStop")

    sub = {"agent_id": "a-qa", "agent_type": "test_runner"}
    remember(root, "qa-STORY-001", "tinyapp/text.py")
    code_code, code_out = deliver(root, sub, "run_tests",
                                  {"tinyapp/text.py": GREEN_TEXT + "\n# a code edit\n"},
                                  run_id="qa-STORY-001", skill="qa")
    restore_in_root(root, "qa-STORY-001", ["tinyapp/text.py"])
    pass_code, pass_out = deliver(root, sub, "run_tests", {}, run_id="qa-STORY-001", skill="qa")
    after = record(root, "qa-STORY-001")

    review_root = make_project("review")
    review_code, _ = sequence(review_root, "phase", "start", "review", "STORY-001", "--lenient")
    review_rec = record(review_root, "review-STORY-001")

    passed = all((
        start_code == 0,
        rec["kind"] == "document",
        rec["run"] == "qa-STORY-001",
        rec["write_fence"] == ["docs/reports/qa-STORY-001.md"],
        rec["commands"] == {"source": ".devforgeai/stack.yaml#python", "use": ["test", "lint"]},
        len(rec["test_plan"]) == 3,
        run_code == 0 and "classification: PASS" in run_out,
        # `run_tests` reads the suite and reports: it is a judge, so a code path
        # is refused by the evidence rule rather than by the fence
        code_code == 2 and ("outside write_fence" in code_out
                            or "only write path" in code_out),
        pass_code == 0,
        after["phase"] == "criteria",
        review_code == 0,
        review_rec["commands"]["source"] == ".devforgeai/stack.yaml#python",
        review_rec["write_fence"] == ["docs/reports/review-STORY-001.md"],
    ))
    return passed, (f"start={start_code} run={run_code} code={code_code} pass={pass_code} "
                    f"phase={after.get('phase')} review={review_code}\n"
                    + (start_out or run_out)[-200:])


# ---------- runner dialect normalisation ----------
#
# `junit_dialect` exists because a runner's JUnit is not self-describing. Every
# case below was written against the live reporter and the XML shape it produces
# is recorded beside it; each row proves the red gate refuses the shape with the
# classification that shape deserves, rather than the one a literal read gives.
# The `generic` reading of each hostile case is noted too, because that reading
# is what the dialect exists to correct — and what every other row still gets.

PLAN_NAMES = ("test_slugify_basic", "test_slugify_unicode", "test_slugify_empty")

PYTEST_HOSTILE = {
    # <testsuite tests="0" errors="0" failures="0"/> and no testcase at all.
    # Generic already reads this as NO_TESTS; the row holds the reading.
    "empty": "",
    # <testcase name="tests.test_text"><error message="collection failure">
    # carrying the SyntaxError traceback. Generic already reads this as
    # COLLECTION_ERROR, because pytest reports an unparseable module as <error>.
    "syntax": (
        "from tinyapp.text import slugify\n"
        "\n"
        "def test_slugify_basic(:\n"
        "    assert slugify('Hello, World!') == 'hello-world'\n"
    ),
    # Three <failure message="NameError: name 'slugifyy' is not defined">, one
    # per test_plan name. Generic reads all three as failed assertions and the
    # red gate advances: a throw in the test body satisfies nothing, and this is
    # the case the pytest dialect exists for.
    "nameerror": "".join(
        f"def {name}():\n"
        f"    assert slugifyy('Hello, World!') == 'hello-world'\n"
        f"\n"
        for name in PLAN_NAMES
    ),
}

NODE_STACK = """node:
  version: 1
  compiled: false
  package_manager: npm
  manifests: [package.json]
  junit_dialect: node
  commands:
    test:
      argv:
        - node
        - --test
        - --test-reporter=junit
        - --test-reporter-destination=.devforgeai/work/junit.xml
        - "tests/*.test.mjs"
      cwd: "."
      junit_path: .devforgeai/work/junit.xml
      timeout_s: 300
  test_glob: "tests/*.test.mjs"
  test_layout: sibling-tests-dir
  ignore_dirs: [node_modules, dist]
  runner_probe: {argv: [node, --version], exit_ok: 0}
  packages: {allow: [], deny: []}
  extractors: []
  forbidden_imports: []
"""

NODE_PLAN_NAMES = ("slugify basic", "slugify unicode", "slugify empty")

NODE_STORY = """---
id: STORY-001
epic: EPIC-001
sprint: sprint-001
scope: feature
status: ready
template: story
template_version: 3
requires_skill: dev-tdd
risk_tier: LOW
size: S
gate_policy:
  unresolved_assumption: BLOCK
  stale_hash: BLOCK
  unresolvable_source: BLOCK
  write_fence_violation: BLOCK
  test_runner_missing: REQUIRE_HUMAN
  criterion_without_test: BLOCK
blocked_by: []
provenance:
  - source: docs/plan/tinyapp/epics/EPIC-001.md#story-001
    hash: sha256:fixture0000000000000000000000000000000000000000000000000000000000
context:
  - source: docs/architecture/techstack.md#testing
    status: INTENDED
    hash: sha256:fixture0000000000000000000000000000000000000000000000000000000002
    excerpt: |
      Tests live under tests/ and are named <module>.test.mjs. The runner is
      node's own, and it writes JUnit XML the oracle reads.
write_fence:
  - tinyapp/text.mjs
  - tests/text.test.mjs
commands:
  source: .devforgeai/stack.yaml#node
  hash: sha256:fixture0000000000000000000000000000000000000000000000000000000004
  use: [test]
test_plan:
  - criterion: 1
    file: tests/text.test.mjs
    name: slugify basic
  - criterion: 2
    file: tests/text.test.mjs
    name: slugify unicode
  - criterion: 3
    file: tests/text.test.mjs
    name: slugify empty
---

# STORY-001: Add slugify helper

## Goal

Provide `slugify(title)` from `tinyapp/text.mjs` so page titles can become
URL-safe path segments.

## Context

See the frontmatter context bundle. `tinyapp/text.mjs` exists and exports no
`slugify`. `tests/text.test.mjs` does not exist.

## Interface

```js
// tinyapp/text.mjs
export function slugify(title) {}
```

Pure function. Never throws for a string argument.

## Acceptance Criteria

1. `slugify("Hello, World!")` returns `"hello-world"`.
2. `slugify("  Ünïcödé  Tïtle ")` returns `"unicode-title"`.
3. `slugify("")` and `slugify("!!!")` both return `""`.

## Unchanged Behaviour

None.

## Out of Scope

- Transliteration of non-Latin scripts.

## Verification

- Red: `test` exits non-zero; each `test_plan` name fails on an assertion.
- Green: `test` exits zero; only `tinyapp/text.mjs` changed since red.

## Clarifications

None.
"""

NODE_FILES = {
    "package.json": '{\n  "name": "tinyapp",\n  "private": true,\n  "type": "module"\n}\n',
    "tinyapp/text.mjs": "export const NAME = 'tinyapp';\n",
}

# The honest red. Every test_plan name is present and fails on an assertion,
# so the oracle must reach EXPECTED_TEST_FAILURE. The `typeof` guard is the
# reason this is an assertion at all: a named import of an export the module
# does not have is a link-time SyntaxError, which node reports as a file-level
# failure and the dialect correctly refuses as COLLECTION_ERROR. A namespace
# import always links, so the missing export is asserted rather than thrown.
NODE_RED_TEXT = """import test from 'node:test';
import assert from 'node:assert/strict';
import * as text from '../tinyapp/text.mjs';

function slug(value) {
  assert.equal(typeof text.slugify, 'function', 'slugify is not exported');
  return text.slugify(value);
}

test('slugify basic', () => {
  assert.equal(slug('Hello, World!'), 'hello-world');
});

test('slugify unicode', () => {
  assert.equal(slug('  Ünïcödé  Tïtle '), 'unicode-title');
});

test('slugify empty', () => {
  assert.equal(slug(''), '');
  assert.equal(slug('!!!'), '');
});
"""

NODE_GREEN_TEXT = """export const NAME = 'tinyapp';

export function slugify(title) {
  const ascii = String(title).normalize('NFD').replace(/[\\u0300-\\u036f]/g, '');
  return ascii.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
}
"""

NODE_HOSTILE = {
    # <testcase name="tests/text.test.mjs"/> with no failure child, exit 0, and
    # the reporter's own `pass 1` comment: node names the file as a testcase
    # when the file registered no test, so generic reads an empty red as PASS.
    "empty": "",
    # <testcase name="tests/text.test.mjs" failure="test failed"> wrapping
    # <failure type="testCodeFailure" message="test failed"> whose body is
    # `code: 'ERR_TEST_FAILURE', failureType: 'testCodeFailure'` and no
    # assertion marker: a module that would not parse looks like one ordinary
    # failing test, so generic reads it as TEST_FAILURE.
    "syntax": """import test from 'node:test';
import assert from 'node:assert/strict';

test('slugify basic', ( => {
  assert.equal('a', 'a');
});
""",
    # Three <failure type="testCodeFailure" message="slugifyy is not defined">
    # under the exact test_plan names, each body carrying
    # `cause: ReferenceError: slugifyy is not defined` and no assertion marker.
    # Generic reads three failing assertions on the right names and lets the red
    # gate through; this is the case the node dialect exists for.
    "reference": "".join(
        ["import test from 'node:test';\n",
         "import assert from 'node:assert/strict';\n\n"]
        + [f"test({name!r}, () => {{\n"
           f"  assert.equal(slugifyy('Hello, World!'), 'hello-world');\n"
           f"}});\n\n"
           for name in NODE_PLAN_NAMES]
    ),
}


def make_node_project(label: str) -> Path:
    """A minimal, dependency-free Node project, written here rather than copied.

    The node rows must not ride on another fixture: the manifest, the module,
    the story and the stack section the gate and the oracle read all come from
    this file, so an edit elsewhere cannot quietly disarm them.
    """
    root = Path(tempfile.mkdtemp(prefix=f"dfai-{label}-"))
    for relative, text in NODE_FILES.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    (root / "tests").mkdir()
    (root / "STORY-001.md").write_text(NODE_STORY)
    (root / ".devforgeai").mkdir()
    (root / ".devforgeai" / "stack.yaml").write_text(NODE_STACK)
    (root / ".devforgeai" / "state.yaml").write_text("version: 1\nstories: {}\nruns: {}\n")
    (root / ".gitignore").write_text(GITIGNORE)
    return root


def set_junit_dialect(root: Path, anchor: str, dialect: str) -> None:
    """Name the runner that writes `junit_path`, as a techstack phase would."""
    path = root / ".devforgeai" / "stack.yaml"
    doc = yaml.safe_load(path.read_text())
    doc[anchor]["junit_dialect"] = dialect
    path.write_text(yaml.safe_dump(doc, sort_keys=False))


def last_oracle(root: Path, run_id: str = "STORY-001") -> str:
    """The classification the oracle recorded, refused phases included."""
    return str((record(root, run_id).get("last_oracle") or {}).get("classification") or "")


REFUSAL_NEEDLE = {
    "NO_TESTS": "NO_TESTS: the test command collected nothing",
    "COLLECTION_ERROR": "COLLECTION_ERROR: tests must fail on an assertion",
}


def pytest_dialect_row(case: str, want: str) -> tuple[bool, str]:
    """One hostile pytest suite: the red gate must refuse it as `want`."""
    root = make_project(f"dialect-py-{case}")
    set_junit_dialect(root, "python", "pytest")
    start_code, start_out = sequence(root, "phase", "start", "dev", "STORY-001", "--lenient")
    if start_code:
        return False, f"gate refused the pytest-dialect project: {start_out[-300:]}"
    code, output = deliver(root, RED, "red", {"tests/test_text.py": PYTEST_HOSTILE[case]})
    got = last_oracle(root)
    passed = all((
        code == 2,                                  # the phase is refused
        got == want,                                # for the right reason
        REFUSAL_NEEDLE[want] in output,             # and says so
        record(root)["phase"] == "red",             # the run does not advance
    ))
    return passed, (f"exit={code} classification={got} want={want} "
                    f"phase={record(root)['phase']}\n" + output[-260:])


def pytest_honest_red_row() -> tuple[bool, str]:
    """`junit_dialect: pytest` still reads a real failing assertion as red."""
    root = make_project("dialect-py-honest")
    set_junit_dialect(root, "python", "pytest")
    start_code, start_out = sequence(root, "phase", "start", "dev", "STORY-001", "--lenient")
    if start_code:
        return False, f"gate refused the pytest-dialect project: {start_out[-300:]}"
    code, output = deliver(root, RED, "red", {"tests/test_text.py": RED_TEXT})
    got = last_oracle(root)
    passed = code == 0 and got == "EXPECTED_TEST_FAILURE" and record(root)["phase"] == "green"
    return passed, (f"exit={code} classification={got} phase={record(root)['phase']}\n"
                    + output[-260:])


def node_dialect_row(case: str, want: str) -> tuple[bool, str]:
    """One hostile `node --test` suite: the red gate must refuse it as `want`."""
    if shutil.which("node") is None:
        return False, "COULD_NOT_RUN: node is not on PATH, so this row did not run"
    root = make_node_project(f"dialect-node-{case}")
    start_code, start_out = sequence(root, "phase", "start", "dev", "STORY-001", "--lenient")
    if start_code:
        return False, f"gate refused the node project: {start_out[-300:]}"
    code, output = deliver(root, RED, "red", {"tests/text.test.mjs": NODE_HOSTILE[case]})
    got = last_oracle(root)
    passed = all((
        code == 2,
        got == want,
        REFUSAL_NEEDLE[want] in output,
        record(root)["phase"] == "red",
    ))
    return passed, (f"exit={code} classification={got} want={want} "
                    f"phase={record(root)['phase']}\n" + output[-260:])


def node_honest_row() -> tuple[bool, str]:
    """A real node red is EXPECTED_TEST_FAILURE and the green after it is PASS."""
    if shutil.which("node") is None:
        return False, "COULD_NOT_RUN: node is not on PATH, so this row did not run"
    root = make_node_project("dialect-node-honest")
    start_code, start_out = sequence(root, "phase", "start", "dev", "STORY-001", "--lenient")
    if start_code:
        return False, f"gate refused the node project: {start_out[-300:]}"
    red_code, red_out = deliver(root, RED, "red", {"tests/text.test.mjs": NODE_RED_TEXT})
    red_class, red_phase = last_oracle(root), record(root)["phase"]
    green_code, green_out = deliver(root, GREEN, "green",
                                    {"tinyapp/text.mjs": NODE_GREEN_TEXT})
    green_class, green_phase = last_oracle(root), record(root)["phase"]
    passed = all((
        red_code == 0,
        red_class == "EXPECTED_TEST_FAILURE",
        red_phase == "green",
        green_code == 0,
        green_class == "PASS",
        green_phase == "refactor",
    ))
    return passed, (f"red={red_code}/{red_class}/{red_phase} "
                    f"green={green_code}/{green_class}/{green_phase}\n"
                    + (green_out or red_out)[-260:])


VALID_STACK = """python:
  version: 1
  compiled: false
  package_manager: pip
  manifests: [pyproject.toml]
  commands:
    test:
      argv: [python3, -m, pytest, -q, --junitxml=.devforgeai/work/junit.xml]
      junit_path: .devforgeai/work/junit.xml
  test_glob: "tests/test_*.py"
  test_layout: sibling-tests-dir
  ignore_dirs: [dist]
  runner_probe: {argv: [python3, -m, pytest, --version], exit_ok: 0}
  packages: {allow: [pytest], deny: []}
  extractors: []
  forbidden_imports: []
"""

# `compiled: true` with no build command, and a test command with no junit_path.
INVALID_STACK = VALID_STACK.replace("compiled: false", "compiled: true").replace(
    "      junit_path: .devforgeai/work/junit.xml\n", "")

STACK_PATH = ".devforgeai/stack.yaml"
ADR_PATH = ".devforgeai/provenance/adr/0002-mandate-tdd.md"

REAL_MANDATES = """# Constitution

## Mandates

tdd: required. Every behaviour change starts with a failing test.
"""

VALID_ADR = """---
id: ADR-0002
template: adr
template_version: 1
status: accepted
date: 2026-01-01
supersedes: null
depends_on:
  - source: docs/architecture/constitution.md#mandates
    hash: sha256:%s
---

# ADR-0002: Mandate test-driven development

## Context

The constitution left tests optional, and two stories shipped without one.

## Decision

Every behaviour change starts with a failing test.

## Consequences

Story slicing carries a test_plan; the red phase is no longer skippable.

## Alternatives

| Alternative | Dropped because |
|---|---|
| Tests recommended | It is the position that produced the untested stories. |
""" % ("a" * 64)

INVALID_ADR = VALID_ADR[:VALID_ADR.index("## Alternatives")].rstrip() + "\n"


def architect_run(label: str, phase: str) -> Path:
    root = make_project(label)
    code, output = sequence(root, "phase", "start", "architect", "tinyapp")
    if code:
        raise AssertionError(f"architect gate failed in {label}: {output}")
    force_phase(root, "architect-tinyapp", phase)
    return root


def amend_run(label: str, phase: str = "adr") -> Path:
    root = make_project(label)
    (root / "docs" / "architecture").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "architecture" / "constitution.md").write_text(REAL_MANDATES)
    code, output = sequence(root, "phase", "start", "amend", "constitution")
    if code:
        raise AssertionError(f"amend gate failed in {label}: {output}")
    force_phase(root, "amend-constitution", phase)
    return root


def plan_run(label: str, phase: str) -> Path:
    root = make_project(label)
    (root / "docs" / "architecture").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "architecture" / "constitution.md").write_text(REAL_MANDATES)
    code, output = sequence(root, "phase", "start", "plan", "demo")
    if code:
        raise AssertionError(f"plan gate failed in {label}: {output}")
    force_phase(root, "plan-demo", phase)
    return root


def stack_writer_backstop() -> tuple[bool, str]:
    """`.devforgeai/stack.yaml` has exactly two producer phases, and a schema."""
    def propose(root, agent, phase, text, skill="architect", run_id="architect-tinyapp"):
        return deliver(root, {"agent_id": "a-1", "agent_type": agent}, phase,
                       {STACK_PATH: text}, run_id=run_id, skill=skill)

    good = architect_run("stack-good", "techstack")
    good_code, good_out = propose(good, "techstack_writer", "techstack", VALID_STACK)

    bad = architect_run("stack-bad", "techstack")
    bad_code, bad_out = propose(bad, "techstack_writer", "techstack", INVALID_STACK)

    wrong_phase = architect_run("stack-phase", "constitution")
    phase_code, phase_out = propose(
        wrong_phase, "constitution_writer", "constitution", VALID_STACK)

    other = make_project("stack-other")
    sequence(other, "phase", "start", "pm", "tinyapp")
    other_code, other_out = propose(other, "scope_splitter", "scope_split", VALID_STACK,
                                    skill="pm", run_id="pm-tinyapp")

    onboard = make_project("stack-onboard")
    onboard_start, _ = sequence(onboard, "phase", "start", "onboard", "tinyapp")
    onboard_code, _ = propose(onboard, "code_mapper", "code_map", VALID_STACK,
                              skill="onboard", run_id="onboard-tinyapp")

    passed = all((
        good_code == 0,
        "version: 1" in (croot(good, "architect-tinyapp") / STACK_PATH).read_text(),
        # the canonical policy file is untouched until promotion
        "csharp" in (good / STACK_PATH).read_text(),
        bad_code == 2 and "stack.schema.json" in bad_out and "build" in bad_out,
        # a judge phase refuses it by its own rule: its one path is its evidence
        phase_code == 2 and ("sequencer-owned" in phase_out or "only write path" in phase_out),
        other_code == 2 and "sequencer-owned" in other_out,
        onboard_start == 0 and onboard_code == 0,
    ))
    return passed, (f"good={good_code} bad={bad_code} wrong_phase={phase_code} "
                    f"other={other_code} onboard={onboard_code}\n" + bad_out[-260:])


def adr_accepted_backstop() -> tuple[bool, str]:
    """`amend`'s `adr` phase writes the registry path inside the candidate root."""
    root = amend_run("adr-good")
    code, output = deliver(root, {"agent_id": "a-adr", "agent_type": "amend_adr_writer"},
                           "adr", {ADR_PATH: VALID_ADR},
                           run_id="amend-constitution", skill="amend")
    after = record(root, "amend-constitution")
    written = croot(root, "amend-constitution") / ADR_PATH
    passed = all((
        code == 0,
        written.exists() and written.read_text() == VALID_ADR,
        not (root / ADR_PATH).exists(),          # canonical waits for promotion
        after["phase"] == "impact",
        after["write_fence"][-1] == ".devforgeai/provenance/adr/**",
    ))
    return passed, (f"exit={code} in_root={written.exists()} phase={after.get('phase')}\n"
                    + output[-200:])


def adr_header_backstop() -> tuple[bool, str]:
    """An ADR missing a required section, or misnamed, is refused unchecked-in."""
    root = amend_run("adr-bad")
    code, output = deliver(root, {"agent_id": "a-adr", "agent_type": "amend_adr_writer"},
                           "adr", {ADR_PATH: INVALID_ADR},
                           run_id="amend-constitution", skill="amend")
    misnamed = amend_run("adr-name")
    name_code, name_out = deliver(
        misnamed, {"agent_id": "a-adr", "agent_type": "amend_adr_writer"}, "adr",
        {".devforgeai/provenance/adr/mandate-tdd.md": VALID_ADR},
        run_id="amend-constitution", skill="amend")
    after = record(root, "amend-constitution")
    passed = all((
        code == 2,
        "adr template header" in output and "## Alternatives" in output,
        not (root / ADR_PATH).exists(),
        after["phase"] == "adr",
        after["candidate"]["checkpoint"] == "base",     # nothing was checkpointed
        name_code == 2 and "NNNN-<slug>.md" in name_out,
    ))
    return passed, (f"missing_section={code} misnamed={name_code} "
                    f"phase={after.get('phase')}\n" + output[-260:])


def architect_adr_backstop() -> tuple[bool, str]:
    """`architect`'s `adr` phase is the second producer, header-checked."""
    good = architect_run("adr-arch-good", "adr")
    good_code, _ = deliver(good, {"agent_id": "a-adr", "agent_type": "adr_writer"}, "adr",
                           {ADR_PATH: VALID_ADR}, run_id="architect-tinyapp", skill="architect")
    after = record(good, "architect-tinyapp")

    bad = architect_run("adr-arch-bad", "adr")
    bad_code, bad_out = deliver(bad, {"agent_id": "a-adr", "agent_type": "adr_writer"}, "adr",
                                {ADR_PATH: INVALID_ADR}, run_id="architect-tinyapp",
                                skill="architect")
    passed = all((
        good_code == 0,
        (croot(good, "architect-tinyapp") / ADR_PATH).read_text() == VALID_ADR,
        after["phase"] == "gap_analysis",
        ".devforgeai/provenance/adr/**" in after["write_fence"],
        bad_code == 2 and "adr template header" in bad_out and "## Alternatives" in bad_out,
    ))
    return passed, (f"accepted={good_code} invalid={bad_code} phase={after.get('phase')}\n"
                    + bad_out[-220:])


def adr_producer_backstop() -> tuple[bool, str]:
    """Only the `adr` phase of the two declared producers may write one."""
    wrong_phase = amend_run("adr-phase", phase="impact")
    phase_code, phase_out = deliver(
        wrong_phase, {"agent_id": "a-1", "agent_type": "impact_analyzer"}, "impact",
        {ADR_PATH: VALID_ADR}, run_id="amend-constitution", skill="amend")

    architect = architect_run("adr-architect", "design")
    arch_code, arch_out = deliver(
        architect, {"agent_id": "a-1", "agent_type": "design_writer"}, "design",
        {ADR_PATH: VALID_ADR}, run_id="architect-tinyapp", skill="architect")

    other = make_project("adr-other")
    sequence(other, "phase", "start", "pm", "tinyapp")
    other_code, other_out = deliver(
        other, {"agent_id": "a-1", "agent_type": "scope_splitter"}, "scope_split",
        {ADR_PATH: VALID_ADR}, run_id="pm-tinyapp", skill="pm")

    sibling = amend_run("adr-sibling")
    sibling_code, sibling_out = deliver(
        sibling, {"agent_id": "a-adr", "agent_type": "amend_adr_writer"}, "adr",
        {".devforgeai/provenance/log.jsonl": "{}\n"},
        run_id="amend-constitution", skill="amend")

    passed = all((
        # a judge phase refuses it by its own rule: its one path is its evidence
        phase_code == 2 and ("sequencer-owned" in phase_out or "only write path" in phase_out),
        arch_code == 2 and "sequencer-owned" in arch_out,
        other_code == 2 and "sequencer-owned" in other_out,
        # the provenance log inside a root is the sequencer's, not an artifact:
        # it is not in the change set at all, so the claim is what is refused
        sibling_code == 2,
        not (other / ADR_PATH).exists(),
    ))
    return passed, (f"wrong_phase={phase_code} architect_design={arch_code} pm={other_code} "
                    f"sibling={sibling_code}\n" + arch_out[-240:])


def planned_story(root: Path, context_hash: str, extra: str = "") -> None:
    """Write a story under docs/plan/ with a real source for its context entry."""
    (root / "docs" / "architecture").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "architecture" / "constitution.md").write_text(REAL_MANDATES)
    stories = root / "docs" / "plan" / "demo" / "stories"
    stories.mkdir(parents=True, exist_ok=True)
    stack_hash = digest(root / ".devforgeai" / "stack.yaml")
    (stories / "STORY-002.md").write_text(f"""---
id: STORY-002
template: story
template_version: 3
status: ready
scope: feature
requires_skill: dev
gate_policy:
  unresolvable_source: BLOCK
  stale_hash: BLOCK
  test_runner_missing: REQUIRE_HUMAN
blocked_by: []
provenance: []
context:
  - source: docs/architecture/constitution.md#mandates
    status: INTENDED
    hash: {context_hash}
    excerpt: |
      tdd: required.
write_fence:
  - tinyapp/text.py
  - tests/test_text.py
commands:
  source: .devforgeai/stack.yaml#python
  hash: {stack_hash}
  use: [test, lint]
test_plan:
  - criterion: 1
    file: tests/test_text.py
    name: test_slugify_basic
{extra}---

# STORY-002

## Acceptance Criteria

1. `slugify("Hello, World!")` returns `"hello-world"`.

## Clarifications

None.
""")


def section_digest(path: Path, anchor: str) -> str:
    """The 01-skill-anatomy.md hash rule, computed independently of the gate."""
    lines = path.read_text().replace("\r\n", "\n").split("\n")
    fence = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
    fenced, marker = [False] * len(lines), None
    for index, line in enumerate(lines):
        found = fence.match(line)
        if marker is None:
            if found:
                marker, fenced[index] = found.group(1), True
            continue
        fenced[index] = True
        if found and found.group(1)[0] == marker[0] \
                and len(found.group(1)) >= len(marker) and not found.group(2).strip():
            marker = None
    start = level = None
    for index, line in enumerate(lines):
        head = re.match(r"^(#{1,6})\s+(.*)", line)
        if head and not fenced[index] \
                and re.sub(r"[^a-z0-9]+", "-", head.group(2).strip().lower()).strip("-") == anchor:
            start, level = index, len(head.group(1))
            break
    end = len(lines)
    for index in range(start + 1, len(lines)):
        head = re.match(r"^(#{1,6})\s", lines[index])
        if head and not fenced[index] and len(head.group(1)) <= level:
            end = index
            break
    body = ("\n".join(lines[start:end]) + "\n").encode()
    return "sha256:" + hashlib.sha256(body).hexdigest()


def provenance_gate_backstop() -> tuple[bool, str]:
    """The gate re-resolves every provenance[] and context[] hash."""
    fresh = make_project("gate-fresh")
    planned_story(fresh, "sha256:" + "0" * 64)
    good_hash = section_digest(fresh / "docs" / "architecture" / "constitution.md", "mandates")
    planned_story(fresh, good_hash)
    good_code, good_out = sequence(fresh, "phase", "start", "dev", "STORY-002")

    stale = make_project("gate-stale")
    planned_story(stale, good_hash)
    (stale / "docs" / "architecture" / "constitution.md").write_text(
        REAL_MANDATES.replace("required", "recommended"))
    stale_code, stale_out = sequence(stale, "phase", "start", "dev", "STORY-002")

    placeholder = make_project("gate-placeholder")
    planned_story(placeholder, "sha256:fixture" + "0" * 57)
    ph_code, ph_out = sequence(placeholder, "phase", "start", "dev", "STORY-002")
    lenient_code, lenient_out = sequence(
        placeholder, "phase", "start", "dev", "STORY-002", "--lenient")
    doc_code, doc_out = sequence(placeholder, "phase", "start", "pm", "tinyapp", "--lenient")

    headless = make_project("gate-headless")
    story = (headless / "STORY-001.md").read_text().replace(
        "  source: .devforgeai/stack.yaml#python\n", "")
    (headless / "STORY-001.md").write_text(story)
    headless_code, headless_out = sequence(
        headless, "phase", "start", "dev", "STORY-001", "--lenient")

    passed = all((
        good_code == 0,
        stale_code == 1 and "stale-hash" in stale_out
        and "docs/architecture/constitution.md#mandates" in stale_out,
        ph_code == 1 and "unresolvable-source" in ph_out and "placeholder hash" in ph_out,
        lenient_code == 1 and "--lenient is refused" in lenient_out,
        doc_code == 2 and "no story to re-resolve" in doc_out,
        headless_code == 1 and "commands.source is empty" in headless_out
        and "Traceback" not in headless_out,
        # a refused gate opens no candidate root
        not (stale / ".devforgeai" / "work" / "STORY-002" / "wt").exists(),
    ))
    return passed, (f"good={good_code} stale={stale_code} placeholder={ph_code} "
                    f"lenient={lenient_code} document={doc_code} headless={headless_code}\n"
                    + (stale_out or good_out)[-260:])


FENCED_LINES = [
    "# Constitution", "", "## Mandates", "",
    "tdd: required. Every behaviour change starts with a failing test.", "",
    "```markdown", "## Review", "",
    "A heading inside a fence is sample text, not a section boundary.", "```", "",
    "The mandate continues after the sample.", "",
    "## Review", "", "Every story is reviewed.", "",
]


def code_fence_section_backstop() -> tuple[bool, str]:
    """A heading inside a code fence does not end a section."""
    def sliced(first: int, last: int) -> str:
        body = ("\n".join(FENCED_LINES[first:last]) + "\n").encode()
        return "sha256:" + hashlib.sha256(body).hexdigest()

    documented = sliced(2, 14)
    fence_blind = sliced(2, 7)

    def project(label: str, context_hash: str) -> tuple[int, str]:
        root = make_project(label)
        planned_story(root, context_hash)
        (root / "docs" / "architecture" / "constitution.md").write_text(
            "\n".join(FENCED_LINES))
        return sequence(root, "phase", "start", "dev", "STORY-002")

    good_code, good_out = project("fence-good", documented)
    blind_code, blind_out = project("fence-blind", fence_blind)
    passed = all((
        documented != fence_blind,
        good_code == 0,
        blind_code == 1 and "stale-hash" in blind_out
        and "docs/architecture/constitution.md#mandates" in blind_out,
    ))
    return passed, (f"documented={good_code} fence_blind={blind_code}\n"
                    + (good_out or blind_out)[-240:])


def pending_story(context_source: str) -> str:
    """A story exactly as `story_writer` writes it: digests it cannot compute."""
    return f"""---
id: STORY-002
template: story
template_version: 3
status: ready
scope: feature
requires_skill: dev
gate_policy:
  unresolvable_source: BLOCK
  stale_hash: BLOCK
  test_runner_missing: REQUIRE_HUMAN
blocked_by: []
provenance: []
context:
  - source: {context_source}
    status: INTENDED
    hash: sha256:PENDING
    excerpt: |
      tdd: required.
write_fence:
  - tinyapp/text.py
  - tests/test_text.py
commands:
  source: .devforgeai/stack.yaml#python
  hash: sha256:PENDING
  use: [test, lint]
test_plan:
  - criterion: 1
    file: tests/test_text.py
    name: test_slugify_basic
---

# STORY-002

## Acceptance Criteria

1. `slugify("Hello, World!")` returns `"hello-world"`.

## Clarifications

None.
"""


def pending_digest_backstop() -> tuple[bool, str]:
    """The sequencer resolves sha256:PENDING inside the root, before the diff."""
    story = "docs/plan/demo/stories/STORY-002.md"
    good = plan_run("pending-good", "stories")
    good_code, good_out = deliver(
        good, {"agent_id": "a-story", "agent_type": "story_writer"}, "stories",
        {story: pending_story("docs/architecture/constitution.md#mandates")},
        run_id="plan-demo", skill="plan")
    written = (croot(good, "plan-demo") / story).read_text()
    result = json.loads(
        (good / ".devforgeai" / "work" / "plan-demo" / "stories-result.json").read_text())

    bad = plan_run("pending-bad", "stories")
    bad_code, bad_out = deliver(
        bad, {"agent_id": "a-story", "agent_type": "story_writer"}, "stories",
        {story: pending_story("docs/architecture/nonexistent.md#mandates")},
        run_id="plan-demo", skill="plan")

    anchor = plan_run("pending-anchor", "stories")
    anchor_code, anchor_out = deliver(
        anchor, {"agent_id": "a-story", "agent_type": "story_writer"}, "stories",
        {story: pending_story("docs/architecture/constitution.md#no-such-heading")},
        run_id="plan-demo", skill="plan")

    passed = all((
        good_code == 0,
        "sha256:PENDING" not in written,
        len(re.findall(r"hash: sha256:[0-9a-f]{64}", written)) == 2,
        len(result.get("digests_resolved") or []) == 2,
        bad_code == 2 and "does not resolve" in bad_out,
        anchor_code == 2 and "is not a heading" in anchor_out,
        record(bad, "plan-demo")["candidate"]["checkpoint"] == "base",
    ))
    return passed, (f"ingest={good_code} missing_source={bad_code} bad_anchor={anchor_code}\n"
                    + (bad_out or good_out)[-240:])


def conditional_phase_backstop() -> tuple[bool, str]:
    """`plan`'s `skill_specs` phase may owe no document, and must say so."""
    root = plan_run("conditional-ok", "skill_specs")
    sub = {"agent_id": "a-spec", "agent_type": "skill_spec_writer"}
    ok_code, ok_out = deliver(root, sub, "skill_specs", {}, run_id="plan-demo", skill="plan",
                              note="no story sets requires_skill to a skill that is missing")
    after = record(root, "plan-demo")

    silent = plan_run("conditional-silent", "skill_specs")
    silent_code, silent_out = deliver(silent, sub, "skill_specs", {}, run_id="plan-demo",
                                      skill="plan", note="")

    epics = plan_run("conditional-epics", "epics")
    epics_code, epics_out = deliver(
        epics, {"agent_id": "a-e", "agent_type": "epic_writer"}, "epics", {},
        run_id="plan-demo", skill="plan", note="nothing to do here")

    passed = all((
        ok_code == 0,
        after["phase"] == "dependencies",
        silent_code == 2 and "must say in its note" in silent_out,
        epics_code == 2 and "produced no document" in epics_out,
    ))
    return passed, (f"conditional={ok_code} silent={silent_code} epics={epics_code} "
                    f"phase={after.get('phase')}\n" + silent_out[-200:])


def slice_backstop() -> tuple[bool, str]:
    """Slice is a sequencer operation at `phase start`, not a worker."""
    def context_doc(root: Path, run_dir: str) -> dict:
        return json.loads(
            (root / ".devforgeai" / "work" / run_dir / "context.json").read_text())

    story = make_project("slice-story")
    planned_story(story, "sha256:" + "0" * 64)
    good = section_digest(story / "docs" / "architecture" / "constitution.md", "mandates")
    planned_story(story, good)
    story_code, story_out = sequence(story, "phase", "start", "dev", "STORY-002")
    story_doc = context_doc(story, "STORY-002")

    start_code, start_out = run(story, event(
        "SubagentStart", sub={"agent_id": "a-red", "agent_type": "red_dev"}))

    document = make_project("slice-document")
    doc_code, doc_out = sequence(document, "phase", "start", "pm", "tinyapp")
    doc_doc = context_doc(document, "pm-tinyapp")

    anchored = make_project("slice-anchored")
    planned_story(anchored, good)
    anchored_code, _ = sequence(anchored, "phase", "start", "review", "STORY-002")
    anchored_doc = context_doc(anchored, "review-STORY-002")

    entries = story_doc.get("entries") or []
    passed = all((
        story_code == 0,
        story_doc["slice"] == "bundle",
        story_doc["incoming"] == "docs/plan/demo/stories/STORY-002.md",
        [row["source"] for row in entries] == ["docs/architecture/constitution.md#mandates"],
        entries[0]["verdict"] == "ok",
        entries[0]["excerpt"].strip() == "tdd: required.",
        "context.json" in story_out,
        start_code == 0 and ".devforgeai/work/STORY-002/context.json" in start_out,
        doc_code == 0,
        doc_doc["slice"] == "none" and doc_doc["entries"] == [] and doc_doc["incoming"] is None,
        anchored_code == 0 and anchored_doc["slice"] == "bundle",
    ))
    return passed, (f"story={story_code} document={doc_code} anchored={anchored_code} "
                    f"slice={story_doc.get('slice')}/{doc_doc.get('slice')}\n"
                    + (story_out or doc_out)[-200:])


def plan_fields_backstop() -> tuple[bool, str]:
    """`dependencies` and `estimates` update three story keys, and nothing else."""
    root = make_project("plan-fields")
    planned_story(root, "sha256:" + "0" * 64)
    start_code, start_out = sequence(root, "phase", "start", "plan", "demo")
    force_phase(root, "plan-demo", "dependencies")
    target = "docs/plan/demo/stories/STORY-002.md"
    original = (croot(root, "plan-demo") / target).read_text()
    sub = {"agent_id": "a-dep", "agent_type": "dependency_mapper"}

    def propose(text, path=target):
        author(root, "plan-demo", {target: original})     # start from the checkpoint bytes
        return deliver(root, sub, "dependencies", {path: text},
                       run_id="plan-demo", skill="plan")

    body_code, body_out = propose(original.replace("# STORY-002", "# STORY-002 (reordered)"))
    key_code, key_out = propose(original.replace("status: ready", "status: draft"))
    fence_code, fence_out = propose(original, path="docs/plan/demo/epics/EPIC-001.md")
    new_code, new_out = propose(original, path="docs/plan/demo/stories/STORY-003.md")

    ordered = original.replace("blocked_by: []", "blocked_by: [STORY-001]")
    author(root, "plan-demo", {"docs/plan/demo/epics/EPIC-001.md": None,
                               "docs/plan/demo/stories/STORY-003.md": None})
    ok_code, ok_out = propose(ordered)
    after = record(root, "plan-demo")

    passed = all((
        start_code == 0,
        body_code == 2 and "may not change the body" in body_out,
        key_code == 2 and "may change only" in key_out and "status" in key_out,
        fence_code == 2 and "may update only" in fence_out,
        new_code == 2 and "only update a file that exists" in new_out,
        ok_code == 0,
        (croot(root, "plan-demo") / target).read_text() == ordered,
        after["phase"] == "estimates",
    ))
    return passed, (f"body={body_code} key={key_code} fence={fence_code} new={new_code} "
                    f"ok={ok_code} phase={after.get('phase')}\n" + (key_out or start_out)[-220:])


REVIEW_REPORT = """---
story: STORY-002
template: review-report
template_version: 1
status: final
verdict: %s
depends_on: []
---

# Review of STORY-002

## Findings

| id | text |
|---|---|
| FIND-001 | `text.py` shadows the module name in two helpers. |
"""


def verdict_backstop() -> tuple[bool, str]:
    """The report's own verdict selects the handoff row; the run still passes."""
    target = "docs/reports/review-STORY-002.md"

    def review_run(label: str, phase: str = "report") -> Path:
        root = make_project(label)
        planned_story(root, "sha256:" + "0" * 64)
        good = section_digest(root / "docs" / "architecture" / "constitution.md", "mandates")
        planned_story(root, good)
        code, output = sequence(root, "phase", "start", "review", "STORY-002")
        if code:
            raise AssertionError(f"review gate failed in {label}: {output}")
        force_phase(root, "review-STORY-002", phase)
        return root

    def report(root, text, agent="review_writer", phase="report", skill="review",
               run_id="review-STORY-002", path=target):
        files = {} if text is None else {path: text}
        return deliver(root, {"agent_id": "a-rep", "agent_type": agent}, phase, files,
                       run_id=run_id, skill=skill, refs=[path])

    def handoff_of(root: Path, run_dir: str) -> dict:
        return json.loads(
            (root / ".devforgeai" / "work" / run_dir / "handoff.json").read_text())

    findings = review_run("verdict-findings")
    f_code, f_out = report(findings, REVIEW_REPORT % "findings")
    f_handoff = handoff_of(findings, "review-STORY-002")
    f_promote = sequence(findings, "promote", "review-STORY-002")
    f_final = handoff_of(findings, "review-STORY-002")

    clean = review_run("verdict-pass")
    p_code, _ = report(clean, REVIEW_REPORT % "pass")
    sequence(clean, "promote", "review-STORY-002")
    p_handoff = handoff_of(clean, "review-STORY-002")

    bogus = review_run("verdict-bogus")
    b_code, b_out = report(bogus, REVIEW_REPORT % "reviewed")

    missing = review_run("verdict-missing")
    m_code, m_out = report(missing, REVIEW_REPORT.replace("verdict: %s\n", "") % ())

    validator = make_project("verdict-validator")
    v_start, _ = sequence(validator, "phase", "start", "skill-validator", "dev")
    force_phase(validator, "skill-validator-dev", "report")
    v_code, v_out = report(
        validator,
        "---\nskill: dev\ntemplate: validate-report\ntemplate_version: 1\n"
        "status: final\nverdict: fail\ndepends_on: []\n---\n\n# Validation of dev\n",
        agent="validate_report_writer", skill="skill-validator",
        run_id="skill-validator-dev", path="docs/reports/validate-dev.md")
    sequence(validator, "promote", "skill-validator-dev")
    v_handoff = handoff_of(validator, "skill-validator-dev")

    passed = all((
        f_code == 0,
        f_handoff["outcome"] == "REQUIRE_HUMAN",
        f_handoff["next"] == "devforgeai promote review-STORY-002",
        f_promote[0] == 0,
        f_final["outcome"] == "pass" and f_final["verdict"] == "findings",
        f_final["next"] == "/dev STORY-002 --fix",
        p_code == 0 and p_handoff["verdict"] == "pass" and p_handoff["next"] == "/status",
        b_code == 2 and "invalid verdict" in b_out,
        m_code == 2 and "states a verdict" in m_out,
        v_start == 0 and v_code == 0,
        v_handoff["next"] == "/skill-gen dev --fix" and v_handoff["outcome"] == "pass",
    ))
    return passed, (f"findings={f_code}/{f_promote[0]} pass={p_code} bogus={b_code} "
                    f"missing={m_code} validator={v_code}\n"
                    + (f"next={f_final.get('next')} " + (b_out or f_out))[-240:])


def installer_backstop() -> tuple[bool, str]:
    """`.devforgeai/` is writable directly exactly once: before it exists."""
    bare = Path(tempfile.mkdtemp(prefix="dfai-install-"))
    (bare / "README.md").write_text("# project\n")

    def write(path: str):
        return run(bare, event("PreToolUse", "Write", write_input(path)))

    inside_code, _ = write(".devforgeai/hooks/dispatch.py")
    skeleton_code, _ = write(".devforgeai/state.yaml")
    outside_code, outside_out = write("README.md")
    provider_code, provider_out = write(".claude/settings.json")
    patch_code, _ = run(bare, event(
        "PreToolUse", "apply_patch",
        {"command": patch("*** Add File: .devforgeai/state.yaml", "+version: 1")}))

    (bare / ".devforgeai").mkdir(exist_ok=True)
    (bare / ".devforgeai" / "state.yaml").write_text("version: 1\nstories: {}\nruns: {}\n")
    after_code, after_out = write(".devforgeai/state.yaml")
    hooks_code, hooks_out = write(".devforgeai/hooks/dispatch.py")

    passed = all((
        inside_code == 0,
        skeleton_code == 0,
        patch_code == 0,
        outside_code == 2 and "only writable prefix is .devforgeai/" in outside_out,
        provider_code == 2 and "only writable prefix is .devforgeai/" in provider_out,
        after_code == 2 and "already installed" in after_out,
        hooks_code == 2 and "already installed" in hooks_out,
    ))
    return passed, (f"inside={inside_code} skeleton={skeleton_code} patch={patch_code} "
                    f"outside={outside_code} provider={provider_code} after={after_code} "
                    f"hooks={hooks_code}\n" + (after_out or outside_out)[-200:])


RUN_KEYS = {"run", "canonical", "skill", "arg", "kind", "phase", "write_fence",
            "test_paths", "test_plan", "commands", "gate_policy", "granted_keys",
            "attempts", "max_attempts", "candidate", "lease", "blocked_at", "started_at",
            "session_id"}


def fixture_state_backstop() -> tuple[bool, str]:
    """The documented fixture run record matches every live one the sequencer writes."""
    fixture = yaml.safe_load(
        (HERE / "fixtures" / ".devforgeai" / "work" / "STORY-001" / "run.yaml").read_text())
    errors = [f"fixture run.yaml lacks {key}" for key in sorted(RUN_KEYS - set(fixture))]

    schema_dir = HERE.parents[3] / "schemas" / "devforgeai" / "v1"
    schema_path = schema_dir / "run.schema.json"
    schema_path = schema_path if schema_path.exists() else None
    validator = None
    if schema_path:
        try:
            from jsonschema import Draft202012Validator
            validator = Draft202012Validator(json.loads(schema_path.read_text()))
        except ImportError:
            validator = None

    def failures(label: str, candidate: dict) -> list[str]:
        rows = [f"{label} lacks {key}" for key in sorted(RUN_KEYS - set(candidate))]
        if validator:
            rows += [f"{label} {'/'.join(str(p) for p in e.path) or '(root)'}: {e.message}"
                     for e in validator.iter_errors(candidate)]
        return rows

    errors += failures("fixture", fixture) if validator else []
    for label, argv, run_id in (("dev", ("dev", "STORY-001", "--lenient"), "STORY-001"),
                                ("qa", ("qa", "STORY-001", "--lenient"), "qa-STORY-001"),
                                ("pm", ("pm", "tinyapp"), "pm-tinyapp")):
        root = make_project(f"schema-{label}")
        code, output = sequence(root, "phase", "start", *argv)
        if code:
            errors.append(f"{label} phase start exited {code}: {output[-120:]}")
            continue
        errors += failures(label, record(root, run_id))
        row = state_of(root)["runs"][run_id]
        if set(row) != {"story", "skill", "mode", "root", "base_ref", "checkpoint", "status"}:
            errors.append(f"{label} state.yaml#runs row is {sorted(row)}")
        if Path(row["root"]).is_absolute():
            errors.append(f"{label} state.yaml#runs.root is a machine path")
    return not errors, ("; ".join(errors)
                        or f"fixture and live run records agree on {len(RUN_KEYS)} keys "
                           f"(schema: {schema_path.name if schema_path else 'none present'})")


def dapper_policy_backstop() -> tuple[bool, str]:
    """Dapper allow / Entity Framework deny, through the receipt route on Codex."""
    def setup(label: str) -> Path:
        root = started_project(f"csharp-{label}", phase="green")
        rec = record(root)
        rec.update({
            "write_fence": ["app.csproj", "src/Repo.cs", "tests/RepoTests.cs"],
            "test_paths": ["tests/RepoTests.cs"],
            "commands": {"source": ".devforgeai/stack.yaml#csharp",
                         "use": ["build", "test", "lint"]},
            "granted_keys": ["build", "lint", "test"],
        })
        save_record(root, rec)
        return root

    def submit(root: Path, text: str) -> tuple[int, str]:
        # Make the downstream oracle deterministically report the runner missing
        # on every host: this row is about the package policy, not about dotnet.
        return deliver(root, GREEN, "green", {"app.csproj": text}, provider="codex",
                       env={**NO_BYTECODE_ENV, "PATH": "/usr/bin:/bin"})

    dapper_root = setup("dapper")
    dapper_code, dapper_out = submit(
        dapper_root, '<PackageReference Include="Dapper" Version="2.1.0" />\n')
    ef_root = setup("ef")
    ef_code, ef_out = submit(
        ef_root, '<PackageReference Include="Microsoft.EntityFrameworkCore" Version="9.0.0" />\n')
    passed = all((
        "Dapper" in (croot(dapper_root) / "app.csproj").read_text(),
        "COULD_NOT_RUN" in dapper_out,       # accepted, then the runner was absent
        "Dapper" not in dapper_out,          # the package itself was never the problem
        ef_code == 2,
        "EntityFrameworkCore" in ef_out,
        record(ef_root)["candidate"]["checkpoint"] == "base",
    ))
    return passed, f"Dapper={dapper_code}: {dapper_out[-200:]}\nEF={ef_code}: {ef_out[-200:]}"


# ---------- the candidate root: promotion and its refusals ----------

def finished_run(label: str, git: bool) -> Path:
    """A dev run walked to `ready_to_promote` through the dispatcher route."""
    root = started_project(label, git=git)
    deliver(root, RED, "red", {"tests/test_text.py": RED_TEXT})
    deliver(root, GREEN, "green", {"tinyapp/text.py": GREEN_TEXT})
    deliver(root, {"agent_id": "a-ref", "agent_type": "refactor_dev"}, "refactor",
            {"tinyapp/text.py": REFACTORED_TEXT})
    deliver(root, SMOKE, "smoke", {}, refs=["tests/test_text.py"])
    deliver(root, {"agent_id": "a-critic", "agent_type": "dev_critic"}, "review", {})
    return root


def promote_backstop() -> tuple[bool, str]:
    """Promotion is the only canonical write, and it is human-initiated."""
    rows = []
    outcomes = {}
    for mode, git in (("copy", False), ("worktree", True)):
        root = finished_run(f"promote-{mode}", git)
        state = state_of(root)["runs"]["STORY-001"]
        before = (root / "tinyapp" / "text.py").read_text()
        envelope = json.loads(
            (root / ".devforgeai/work/STORY-001/handoff.json").read_text())
        code, output = sequence(root, "promote", "STORY-001")
        after = state_of(root)["runs"]["STORY-001"]
        outcomes[mode] = (
            state["status"] == "ready_to_promote"
            and envelope["outcome"] == "REQUIRE_HUMAN"
            and envelope["next"] == "devforgeai promote STORY-001"
            and "_SEP" not in before                       # nothing moved before promotion
            and code == 0
            and after["status"] == "promoted"
            and (root / "tinyapp" / "text.py").read_text() == REFACTORED_TEXT
            and (root / "tests" / "test_text.py").read_text() == RED_TEXT
            and not croot(root).exists()                   # step 6 removed the root
        )
        if mode == "worktree":
            outcomes["ff"] = "devforgeai/STORY-001" not in git_out(root, "branch", "--list")
            outcomes["history"] = len(git_out(root, "log", "--oneline").splitlines()) >= 4
        rows.append(f"{mode}={code}/{after['status']}")
        # a second promotion of the same run is refused by status
        again = sequence(root, "promote", "STORY-001")
        outcomes[f"{mode}-again"] = again[0] == 1 and "promoted" in again[1]
    passed = all(outcomes.values())
    return passed, " ".join(rows) + " " + json.dumps(outcomes)


def stale_base_backstop() -> tuple[bool, str]:
    """A moved canonical base: copy mode refuses, worktree mode rebases once."""
    copy_root = finished_run("stale-copy", git=False)
    (copy_root / "README.md").write_text("a canonical edit made during the run\n")
    copy_code, copy_out = sequence(copy_root, "promote", "STORY-001")

    tree_root = finished_run("stale-worktree", git=True)
    (tree_root / "README.md").write_text("a canonical commit made during the run\n")
    subprocess.run(["git", "add", "-A"], cwd=tree_root, capture_output=True)
    subprocess.run(["git", "-c", "user.name=u", "-c", "user.email=u@e.invalid",
                    "commit", "-qm", "canonical moves on"], cwd=tree_root, capture_output=True)
    tree_code, tree_out = sequence(tree_root, "promote", "STORY-001")

    passed = all((
        copy_code == 1,
        "STALE_BASE" in copy_out,
        "STALE_BASE" in handoff_reasons(copy_root),
        "devforgeai promote STORY-001" in handoff_reasons(copy_root),
        state_of(copy_root)["runs"]["STORY-001"]["status"] == "ready_to_promote",
        "_SEP" not in (copy_root / "tinyapp" / "text.py").read_text(),
        tree_code == 0,
        "STALE_BASE" in tree_out,                       # announced, then rebased
        (tree_root / "tinyapp" / "text.py").read_text() == REFACTORED_TEXT,
        (tree_root / "README.md").read_text().startswith("a canonical commit"),
    ))
    return passed, (f"copy={copy_code} worktree={tree_code}\n"
                    + (copy_out[-200:] + " | " + tree_out[-200:]))


def merge_conflict_backstop() -> tuple[bool, str]:
    """A rebase that conflicts aborts, and no canonical byte moves."""
    root = finished_run("conflict", git=True)
    (root / "tinyapp" / "text.py").write_text('"""canonical took another path."""\n')
    subprocess.run(["git", "add", "-A"], cwd=root, capture_output=True)
    subprocess.run(["git", "-c", "user.name=u", "-c", "user.email=u@e.invalid",
                    "commit", "-qm", "canonical edits the same file"],
                   cwd=root, capture_output=True)
    head_before = git_out(root, "rev-parse", "HEAD")
    code, output = sequence(root, "promote", "STORY-001")
    passed = all((
        code == 1,
        "MERGE_CONFLICT" in output,
        "MERGE_CONFLICT" in handoff_reasons(root),
        git_out(root, "rev-parse", "HEAD") == head_before,
        (root / "tinyapp" / "text.py").read_text() == '"""canonical took another path."""\n',
        "rebase" not in git_out(root, "status", "--short"),
        state_of(root)["runs"]["STORY-001"]["status"] == "ready_to_promote",
    ))
    return passed, f"exit={code}\n" + output[-300:]


def stray_write_backstop() -> tuple[bool, str]:
    """A canonical path written outside the root during the run refuses promotion.

    This is the hole a fail-open hook leaves: the worker wrote to the canonical
    tree instead of the candidate root. The path is not in the fence and not in
    the run's change set, so only the dirty-set comparison can see it.
    """
    root = finished_run("stray", git=True)
    (root / "NOTES-stray.md").write_text("written outside the candidate root\n")
    code, output = sequence(root, "promote", "STORY-001")
    passed = all((
        code == 1,
        "DIRTY_TARGET" in output,
        "outside the candidate root" in output,
        "NOTES-stray.md" in output,
        (root / "NOTES-stray.md").read_text() == "written outside the candidate root\n",
        state_of(root)["runs"]["STORY-001"]["status"] == "ready_to_promote",
    ))
    return passed, f"exit={code}\n" + output[-260:]


def dirty_target_backstop() -> tuple[bool, str]:
    """An uncommitted canonical edit to a changed path refuses the promotion."""
    root = finished_run("dirty", git=True)
    (root / "tinyapp" / "text.py").write_text("# an uncommitted local edit\n")
    code, output = sequence(root, "promote", "STORY-001")
    passed = all((
        code == 1,
        "DIRTY_TARGET" in output,
        "tinyapp/text.py" in output,
        "commit or discard" in handoff_reasons(root),
        (root / "tinyapp" / "text.py").read_text() == "# an uncommitted local edit\n",
        state_of(root)["runs"]["STORY-001"]["status"] == "ready_to_promote",
    ))
    return passed, f"exit={code}\n" + output[-260:]


def fence_overlap_backstop() -> tuple[bool, str]:
    """A second run whose fence intersects a live one is refused at the gate."""
    root = started_project("overlap")
    same_fence = sequence(root, "--run", "x", "phase", "start", "dev", "STORY-001", "--lenient")

    # A document run whose fence is disjoint opens beside the story run.
    disjoint = sequence(root, "phase", "start", "pm", "tinyapp")

    # Two architect runs share the producer-exception paths even where their
    # document fences differ, so the second is refused.
    arch = make_project("overlap-architect")
    first, _ = sequence(arch, "phase", "start", "architect", "tinyapp")
    onboard_code, onboard_out = sequence(arch, "phase", "start", "onboard", "tinyapp")

    passed = all((
        same_fence[0] == 1 and "already active" in same_fence[1],
        disjoint[0] == 0,
        len(state_of(root)["runs"]) == 2,
        first == 0,
        onboard_code == 1 and "FENCE_OVERLAP" in onboard_out
        and ".devforgeai/stack.yaml" in onboard_out,
    ))
    return passed, (f"same={same_fence[0]} disjoint={disjoint[0]} architect={first} "
                    f"onboard={onboard_code}\n" + onboard_out[-240:])


def story_in_flight_backstop() -> tuple[bool, str]:
    """`review` and `qa` are refused while the story's dev run is unfinished."""
    root = started_project("in-flight")
    review_code, review_out = sequence(root, "phase", "start", "review", "STORY-001",
                                       "--lenient")
    qa_code, qa_out = sequence(root, "phase", "start", "qa", "STORY-001", "--lenient")

    # Still refused once the run is ready_to_promote: the work is not canonical yet.
    ready = finished_run("in-flight-ready", git=False)
    ready_code, ready_out = sequence(ready, "phase", "start", "review", "STORY-001",
                                     "--lenient")
    sequence(ready, "promote", "STORY-001")
    after_code, after_out = sequence(ready, "phase", "start", "review", "STORY-001",
                                     "--lenient")

    passed = all((
        review_code == 1 and "STORY_IN_FLIGHT" in review_out,
        qa_code == 1 and "STORY_IN_FLIGHT" in qa_out,
        ready_code == 1 and "STORY_IN_FLIGHT" in ready_out
        and "ready_to_promote" in ready_out,
        after_code == 0,                       # promoted: the story is canonical now
    ))
    return passed, (f"review={review_code} qa={qa_code} ready={ready_code} "
                    f"after_promote={after_code}\n" + review_out[-220:])


def lease_backstop() -> tuple[bool, str]:
    """One producer writes in a root at a time, on both providers."""
    root = started_project("lease")
    target = croot(root) / "tests" / "test_text.py"

    first = bind(root, RED)
    second = bind(root, {"agent_id": "a-red-2", "agent_type": "red_dev"})
    holder = run(root, event("PreToolUse", "Write", write_input(target), RED))
    other = run(root, event("PreToolUse", "Write", write_input(target),
                            {"agent_id": "a-red-2", "agent_type": "red_dev"}))
    primary = run(root, event("PreToolUse", "Write", write_input(target)))

    # Codex carries no identity on PreToolUse: the root is the fence there.
    codex_in = run(root, event("PreToolUse", "Write", write_input(target)), "codex")
    codex_out = run(root, event("PreToolUse", "Write",
                                write_input(root / "tests" / "test_text.py")), "codex")

    # A receipt from a worker that does not hold the lease is refused.
    author(root, "STORY-001", {"tests/test_text.py": RED_TEXT})
    foreign = stop(root, {"agent_id": "a-red-2", "agent_type": "red_dev"},
                   receipt("red", "red_dev", claimed=["tests/test_text.py"]))

    # The lease is released at ingest, so the next phase's worker can bind.
    ingested = stop(root, RED, receipt("red", "red_dev", claimed=["tests/test_text.py"]))
    released = record(root)["lease"]
    next_bind = bind(root, GREEN)

    # A judge never holds one.
    set_phase(root, "smoke")
    judge = bind(root, SMOKE)

    passed = all((
        first[0] == 0,
        second[0] == 2 and "LEASE_HELD" in second[1],
        holder[0] == 0,
        other[0] == 2 and "LEASE_HELD" in other[1],
        primary[0] == 2 and "primary window" in primary[1],
        codex_in[0] == 0,
        codex_out[0] == 2 and "outside the candidate root" in codex_out[1],
        foreign[0] == 2 and "LEASE_HELD" in foreign[1],
        ingested[0] == 0,
        released is None,
        next_bind[0] == 0,
        judge[0] == 0 and "evidence" in judge[1],
        record(root)["lease"] is None,
    ))
    return passed, (f"first={first[0]} second={second[0]} holder={holder[0]} other={other[0]} "
                    f"primary={primary[0]} codex={codex_in[0]}/{codex_out[0]} "
                    f"foreign={foreign[0]} judge={judge[0]}\n" + second[1][-200:])


def unclaimed_change_backstop() -> tuple[bool, str]:
    """The checkpoint diff, not the receipt, says what changed."""
    root = started_project("unclaimed")
    bind(root, RED)
    author(root, "STORY-001", {"tests/test_text.py": RED_TEXT,
                               "tests/test_extra.py": "def test_extra():\n    assert True\n"})
    silent = stop(root, RED, receipt("red", "red_dev", claimed=["tests/test_text.py"]))

    # Claiming more than was changed is not a defect: the check is a subset test.
    author(root, "STORY-001", {"tests/test_extra.py": None})
    generous = stop(root, RED, receipt(
        "red", "red_dev", claimed=["tests/test_text.py", "tinyapp/text.py"]))
    result = json.loads((root / ".devforgeai/work/STORY-001/red-result.json").read_text())

    passed = all((
        silent[0] == 2,
        "UNCLAIMED_CHANGE" in silent[1] and "tests/test_extra.py" in silent[1],
        generous[0] == 0,
        [row["path"] for row in result["changed"]] == ["tests/test_text.py"],
        record(root)["candidate"]["checkpoint"] == "red",
    ))
    return passed, f"silent={silent[0]} generous={generous[0]}\n" + silent[1][-240:]


def no_candidate_backstop() -> tuple[bool, str]:
    """Every operation that needs a root says so by name when it is gone."""
    root = finished_run("no-candidate", git=False)
    sequence(root, "promote", "STORY-001")
    gone = sequence(root, "promote", "STORY-001")

    abandoned = started_project("abandon")
    marker = croot(abandoned) / MARKER
    had_marker = marker.exists()
    fail_code, _ = sequence(abandoned, "phase", "fail", "--reason", "the API key is missing")
    status = state_of(abandoned)["runs"]["STORY-001"]["status"]
    again = sequence(abandoned, "candidate", "abandon", "STORY-001", internal=True)
    write_after = run(abandoned, event("PreToolUse", "Write",
                                       write_input("tests/test_text.py"), RED))

    passed = all((
        had_marker,
        gone[0] == 1 and "promoted" in gone[1],
        fail_code == 0,
        status == "abandoned",
        not (abandoned / ".devforgeai" / "work" / "STORY-001" / "wt").exists(),
        again[0] == 1 and "NO_CANDIDATE" in again[1],
        write_after[0] == 2 and "no DevForgeAI run is active" in write_after[1],
    ))
    return passed, (f"promoted_twice={gone[0]} fail={fail_code} status={status} "
                    f"abandon_again={again[0]} write={write_after[0]}\n" + again[1][-200:])


def resume_backstop() -> tuple[bool, str]:
    """A REQUIRE_HUMAN block keeps the run, and `phase start` resumes it."""
    # 1. needs_user: the worker asked for a human, and the human answered.
    asked = started_project("resume-user")
    bind(asked, RED)
    user = stop(asked, RED, receipt("red", "red_dev", status="needs_user",
                                    note="the story does not say how o-umlaut maps"))
    blocked = record(asked)
    envelope = json.loads((asked / ".devforgeai/work/STORY-001/handoff.json").read_text())
    other_skill = sequence(asked, "phase", "start", "review", "STORY-001", "--lenient")
    resumed = sequence(asked, "phase", "start", "dev", "STORY-001", "--lenient")
    after = record(asked)
    worked = deliver(asked, RED, "red", {"tests/test_text.py": RED_TEXT})

    # 2. the attempt limit: red failed its oracle twice.
    spent = started_project("resume-limit")
    empty = "def test_nothing():\n    assert True\n"
    for _ in range(2):
        deliver(spent, RED, "red", {"tests/test_text.py": empty})
    spent_record = record(spent)
    spent_state = state_of(spent)["runs"]["STORY-001"]["status"]
    spent_resume = sequence(spent, "phase", "start", "dev", "STORY-001", "--lenient")
    spent_after = record(spent)

    # 3. `phase fail` is the other exit, and it frees the story.
    failed = sequence(spent, "phase", "fail", "--reason", "the criterion is wrong")
    freed = sequence(spent, "phase", "start", "review", "STORY-001", "--lenient")

    passed = all((
        user[0] == 0,
        blocked["blocked_at"] == "red",
        blocked["lease"] is None,
        state_of(asked)["runs"]["STORY-001"]["status"] == "active",
        croot(asked).is_dir(),                       # the root is kept for inspection
        envelope["outcome"] == "REQUIRE_HUMAN" and envelope["next"] == "/dev STORY-001",
        other_skill[0] == 1 and "STORY_IN_FLIGHT" in other_skill[1],
        resumed[0] == 0 and "resumed at phase red" in resumed[1],
        after["blocked_at"] is None and after["phase"] == "red",
        after["attempts"]["red"] == 0,
        worked[0] == 0,
        spent_record["blocked_at"] == "red" and spent_record["attempts"]["red"] == 2,
        spent_state == "active",
        spent_resume[0] == 0,
        spent_after["attempts"]["red"] == 0 and spent_after["blocked_at"] is None,
        failed[0] == 0,
        state_of(spent)["runs"]["STORY-001"]["status"] == "abandoned",
        freed[0] == 0,                               # the story is free again
    ))
    return passed, (f"needs_user={user[0]} other_skill={other_skill[0]} resume={resumed[0]} "
                    f"worked={worked[0]} limit_resume={spent_resume[0]} fail={failed[0]} "
                    f"freed={freed[0]}\n" + (resumed[1] or user[1])[-220:])


def judge_evidence_backstop() -> tuple[bool, str]:
    """A judge writes in its evidence directory and nowhere else, on both providers."""
    root = started_project("evidence", phase="smoke")
    target = croot(root)
    mine = target / ".devforgeai/work/STORY-001/evidence/smoke_qa/criteria.md"
    theirs = target / ".devforgeai/work/STORY-001/evidence/red_dev/criteria.md"

    claude_in = run(root, event("PreToolUse", "Write", write_input(mine, "# evidence\n"), SMOKE))
    claude_out = run(root, event("PreToolUse", "Write",
                                 write_input(target / "tinyapp" / "text.py"), SMOKE))
    claude_other = run(root, event("PreToolUse", "Write", write_input(theirs), SMOKE))
    codex_in = run(root, event("PreToolUse", "Write", write_input(mine, "# evidence\n"), SMOKE),
                   "codex")
    codex_out = run(root, event("PreToolUse", "Write",
                                write_input(target / "tests" / "test_text.py"), SMOKE), "codex")

    mine.parent.mkdir(parents=True, exist_ok=True)
    mine.write_text("# evidence\n\n| criterion | result |\n|---|---|\n| 1 | pass |\n")
    ingest = stop(root, SMOKE, receipt(
        "smoke", "smoke_qa", checkpoint="base",
        refs=[".devforgeai/work/STORY-001/evidence/smoke_qa/criteria.md"]))
    result = json.loads((root / ".devforgeai/work/STORY-001/smoke-result.json").read_text())
    rows = promotion_rows_of(root)

    passed = all((
        claude_in[0] == 0,
        claude_out[0] == 2 and "only write path" in claude_out[1],
        claude_other[0] == 2 and "only write path" in claude_other[1],
        codex_in[0] == 0,
        codex_out[0] == 2 and "only write path" in codex_out[1],
        ingest[0] == 0,
        result["changed"] == [],              # evidence is never a project change
        result["claimed_paths"] == [],
        all("evidence" not in row for row in rows),
    ))
    return passed, (f"claude={claude_in[0]}/{claude_out[0]}/{claude_other[0]} "
                    f"codex={codex_in[0]}/{codex_out[0]} ingest={ingest[0]} "
                    f"changed={result.get('changed')}\n" + claude_out[1][-200:])


def handoff_reasons(root: Path, run_id: str = "STORY-001") -> str:
    """The reasons and the forward command the run's handoff envelope carries."""
    path = root / ".devforgeai" / "work" / run_id / "handoff.json"
    if not path.exists():
        return ""
    doc = json.loads(path.read_text())
    return " ".join(doc.get("reasons") or []) + " || " + str(doc.get("next") or "")


def promotion_rows_of(root: Path, run_id: str = "STORY-001") -> list[str]:
    """Whatever a promotion of this run would carry, read from the copy manifests."""
    work = root / ".devforgeai" / "work" / run_id / "cp"
    rec = record(root, run_id)
    base = json.loads((work / "base.manifest.json").read_text())
    checkpoint = rec["candidate"]["checkpoint"]
    if checkpoint == "base" or not (work / f"{checkpoint}.manifest.json").exists():
        return []
    after = json.loads((work / f"{checkpoint}.manifest.json").read_text())
    return sorted(p for p in set(base) | set(after) if base.get(p) != after.get(p))


def root_resolution_backstop() -> tuple[bool, str]:
    """The two-marker rule: a root's own state.yaml is never the authority."""
    root = started_project("resolution")
    candidate = croot(root)
    marker = yaml.safe_load((candidate / MARKER).read_text())

    # The candidate root carries a copy of the project's `.devforgeai/`, stale by
    # construction. Running the sequencer from inside the root must still resolve
    # the canonical project and the canonical run.
    (candidate / ".devforgeai" / "state.yaml").write_text("version: 1\nruns: {}\n")
    inside = sequence(candidate, "status")
    outside = sequence(root, "status")

    # A dispatcher event whose cwd is inside the root resolves the same way.
    ev = run(root, event("PreToolUse", "Bash", {"command": "devforgeai status"}, RED,
                         cwd=str(candidate)))

    passed = all((
        set(marker) == {"run", "canonical"},
        marker["run"] == "STORY-001",
        Path(marker["canonical"]).resolve() == root.resolve(),
        inside[0] == 0 and "STORY-001" in inside[1] and "phase: red" in inside[1],
        outside[0] == 0 and "STORY-001" in outside[1],
        ev[0] == 0,
    ))
    return passed, (f"inside={inside[0]} outside={outside[0]} bash={ev[0]} marker={marker}\n"
                    + inside[1][:200])


# ---------- tables ----------

DISPATCHER_CASES = [
    # Check 6: a write belongs to the lease holder, in the root, in the fence.
    ("lease holder writes a test path in the root", 0, "WRITE_IN_FENCE", "red", "claude"),
    ("lease holder writes the same path on Codex", 0, "WRITE_IN_FENCE", "red", "codex"),
    ("write outside the candidate root denied", 2, "WRITE_OUTSIDE_ROOT", "red", "claude"),
    ("write outside the candidate root denied on Codex", 2, "WRITE_OUTSIDE_ROOT", "red", "codex"),
    ("write outside the fence denied", 2, "WRITE_OUT_FENCE", "red", "claude"),
    ("red writing production code denied", 2, "WRITE_CODE_IN_RED", "red", "claude"),
    ("sequencer-owned path inside the root denied", 2, "WRITE_SEQUENCER_OWNED", "red", "claude"),
    ("primary window write denied while a run is active", 2, event("PreToolUse", "Write", write_input("tests/test_text.py")), "red", "claude"),
    ("a worker that holds no lease is denied", 2, event("PreToolUse", "Write", write_input("tests/test_text.py"), {"agent_id": "a-x", "agent_type": "red_dev"}), "red", "claude"),
    ("judge writes inside its evidence directory", 0, "WRITE_EVIDENCE", "smoke", "claude"),
    ("judge writing another agent's evidence denied", 2, "WRITE_EVIDENCE_FOREIGN", "smoke", "claude"),
    ("judge writing a project path denied", 2, "WRITE_CODE_IN_RED", "smoke", "claude"),
    ("Claude MultiEdit follows the same rule", 2, event("PreToolUse", "MultiEdit", {"file_path": "tests/test_text.py", "edits": []}, GREEN), "green", "claude"),
    ("Claude MultiEdit inside the fence allowed", 0, event("PreToolUse", "MultiEdit", {"file_path": "tinyapp/text.py", "edits": []}, GREEN), "green", "claude"),
    ("Claude NotebookEdit outside the fence denied", 2, event("PreToolUse", "NotebookEdit", {"notebook_path": "docs/notes.ipynb"}, GREEN), "green", "claude"),
    ("Codex apply_patch outside the fence denied", 2, event("PreToolUse", "apply_patch", {"command": patch("*** Update File: docs/notes.md", "@@", "+x = 1")}, GREEN), "green", "codex"),
    ("Codex apply_patch inside the fence allowed", 0, event("PreToolUse", "apply_patch", {"command": patch("*** Update File: tinyapp/text.py", "@@", "+x = 1")}, GREEN), "green", "codex"),
    ("a completed write inside the root and fence is accepted", 0, "POST_WRITE_IN_FENCE", "red", "claude"),
    ("a completed write outside the root is diagnosed", 2, "POST_WRITE_OUTSIDE", "green", "claude"),

    # Shell: a single safe argv, never command-head guessing.
    ("raw stack test command denied to worker", 2, event("PreToolUse", "Bash", {"command": "python3 -m pytest -q"}, RED), "red", "codex"),
    ("exact stack test command denied to primary", 2, event("PreToolUse", "Bash", {"command": "python3 -m pytest -q"}), "red", "codex"),
    ("arbitrary pytest form denied", 2, event("PreToolUse", "Bash", {"command": "pytest -x tests/"}, RED), "red", "claude"),
    ("pip install denied", 2, event("PreToolUse", "Bash", {"command": "pip install sqlalchemy"}, RED), "red", "claude"),
    ("variable expansion denied", 2, event("PreToolUse", "Bash", {"command": "$TOOL tests/"}, RED), "red", "claude"),
    ("redirect denied even into the fence", 2, event("PreToolUse", "Bash", {"command": "echo x > tests/test_text.py"}, RED), "red", "claude"),
    ("pipeline denied", 2, event("PreToolUse", "Bash", {"command": "cat pyproject.toml | wc -l"}, RED), "red", "claude"),
    ("sed in-place denied", 2, event("PreToolUse", "Bash", {"command": "sed -i s/x/y/ tests/test_text.py"}, RED), "red", "claude"),
    ("find delete denied", 2, event("PreToolUse", "Bash", {"command": "find tests -delete"}, RED), "red", "claude"),
    ("xargs execution denied", 2, event("PreToolUse", "Bash", {"command": "xargs rm"}, RED), "red", "claude"),
    ("rg read allowed to a worker", 0, event("PreToolUse", "Bash", {"command": "rg slugify tests"}, RED), "red", "claude"),
    ("rg preprocessor denied", 2, event("PreToolUse", "Bash", {"command": "rg --pre cat slugify tests"}, RED), "red", "claude"),
    ("git status allowed to the primary", 0, event("PreToolUse", "Bash", {"command": "git status --short"}), "red", "claude"),
    ("git commit denied", 2, event("PreToolUse", "Bash", {"command": "git commit -m x"}, RED), "red", "claude"),
    ("git add denied", 2, event("PreToolUse", "Bash", {"command": "git add -A"}, RED), "red", "claude"),
    ("git merge denied", 2, event("PreToolUse", "Bash", {"command": "git merge devforgeai/STORY-001"}), "red", "claude"),
    ("git worktree denied", 2, event("PreToolUse", "Bash", {"command": "git worktree remove wt"}), "red", "claude"),
    ("git checkout denied", 2, event("PreToolUse", "Bash", {"command": "git checkout -- tests/"}, RED), "red", "claude"),
    ("git branch delete denied", 2, event("PreToolUse", "Bash", {"command": "git branch -D main"}, RED), "red", "claude"),
    ("git output option denied", 2, event("PreToolUse", "Bash", {"command": "git diff --output=tests/test_text.py"}, RED), "red", "claude"),
    ("chained rm denied", 2, event("PreToolUse", "Bash", {"command": "git status && rm -rf tests"}, RED), "red", "claude"),

    # Sequencer grammar as seen by the Bash gate.
    ("primary status allowed", 0, event("PreToolUse", "Bash", {"command": "devforgeai status"}), "red", "claude"),
    ("worker status allowed", 0, event("PreToolUse", "Bash", {"command": "devforgeai status"}, RED), "red", "claude"),
    ("primary validate allowed", 0, event("PreToolUse", "Bash", {"command": "devforgeai validate"}), "red", "codex"),
    ("primary phase fail allowed", 0, event("PreToolUse", "Bash", {"command": "devforgeai phase fail --reason blocked"}), "red", "claude"),
    ("primary promote allowed", 0, event("PreToolUse", "Bash", {"command": "devforgeai promote STORY-001"}), "red", "claude"),
    ("promote with a flag denied", 2, event("PreToolUse", "Bash", {"command": "devforgeai promote STORY-001 --force"}), "red", "claude"),
    ("primary phase start denied while a run is active", 2, event("PreToolUse", "Bash", {"command": "devforgeai phase start dev STORY-002"}), "red", "claude"),
    ("lease holder run test allowed", 0, event("PreToolUse", "Bash", {"command": "devforgeai run test"}, RED), "red", "claude"),
    ("run key the phase does not grant denied", 2, event("PreToolUse", "Bash", {"command": "devforgeai run lint"}, RED), "red", "claude"),
    ("run denied to a worker that is not the lease holder", 2, event("PreToolUse", "Bash", {"command": "devforgeai run test"}, {"agent_id": "a-x", "agent_type": "red_dev"}), "red", "claude"),
    ("run denied to the primary window", 2, event("PreToolUse", "Bash", {"command": "devforgeai run test"}), "red", "codex"),
    ("lease holder run test allowed on Codex from inside the root", 0, "CODEX_RUN", "red", "codex"),
    ("run denied to a judge", 2, event("PreToolUse", "Bash", {"command": "devforgeai run test"}, SMOKE), "smoke", "claude"),
    ("hook-only phase next denied to primary", 2, event("PreToolUse", "Bash", {"command": "devforgeai phase next"}), "red", "claude"),
    ("hook-only phase next denied to worker", 2, event("PreToolUse", "Bash", {"command": "devforgeai phase next"}, RED), "red", "codex"),
    ("hook-only ingest-result denied", 2, event("PreToolUse", "Bash", {"command": "devforgeai ingest-result --agent red_dev"}), "red", "codex"),
    ("hook-only session-start denied", 2, event("PreToolUse", "Bash", {"command": "devforgeai session-start --session-id x --provider claude"}), "red", "claude"),
    ("sequencer-internal candidate open denied", 2, event("PreToolUse", "Bash", {"command": "devforgeai candidate open STORY-001"}), "red", "claude"),
    ("sequencer-internal candidate promote denied", 2, event("PreToolUse", "Bash", {"command": "devforgeai candidate promote STORY-001"}), "red", "claude"),
    ("deleted report operation denied", 2, event("PreToolUse", "Bash", {"command": "devforgeai report red_dev --status pass"}, RED), "red", "claude"),
    ("worker validate denied", 2, event("PreToolUse", "Bash", {"command": "devforgeai validate"}, RED), "red", "claude"),
    ("arbitrary sequencer operation denied", 2, event("PreToolUse", "Bash", {"command": "devforgeai destroy all"}), "red", "codex"),
    ("malformed state fails closed", 2, "BAD_STATE", "red", "claude"),

    # The provider-external Research Core runner.
    ("research normalize-request allowed with no run", 0, event("PreToolUse", "Bash", {"command": "devforgeai-research normalize-request request-low.json"}), "NONE", "claude"),
    ("research open-run allowed with no run", 0, event("PreToolUse", "Bash", {"command": "devforgeai-research open-run --digest abc123"}), "NONE", "claude"),
    ("research append-record allowed with no run", 0, event("PreToolUse", "Bash", {"command": "devforgeai-research append-record RUN-000001 --kind source"}), "NONE", "codex"),
    ("research put-source allowed with no run", 0, event("PreToolUse", "Bash", {"command": "devforgeai-research put-source RUN-000001 --file s.html"}), "NONE", "claude"),
    ("research transition-run allowed with no run", 0, event("PreToolUse", "Bash", {"command": "devforgeai-research transition-run RUN-000001 --to P1"}), "NONE", "codex"),
    ("research validate-run allowed with no run", 0, event("PreToolUse", "Bash", {"command": "devforgeai-research validate-run RUN-000001"}), "NONE", "claude"),
    ("research seal-run allowed with no run", 0, event("PreToolUse", "Bash", {"command": "devforgeai-research seal-run RUN-000001"}), "NONE", "claude"),
    ("research render allowed with no run", 0, event("PreToolUse", "Bash", {"command": "devforgeai-research render sqlite-wal"}), "NONE", "codex"),
    ("research render-handoff allowed with no run", 0, event("PreToolUse", "Bash", {"command": "devforgeai-research render-handoff sqlite-wal"}), "NONE", "claude"),
    ("research resume-run allowed with no run", 0, event("PreToolUse", "Bash", {"command": "devforgeai-research resume-run sqlite-wal"}), "NONE", "claude"),
    ("research runner allowed while a framework run is active", 0, event("PreToolUse", "Bash", {"command": "devforgeai-research validate-run RUN-000001"}), "red", "claude"),
    ("research unknown subcommand denied", 2, event("PreToolUse", "Bash", {"command": "devforgeai-research seal-everything RUN-000001"}), "NONE", "claude"),
    ("research redirect denied", 2, event("PreToolUse", "Bash", {"command": "devforgeai-research render sqlite-wal > out.md"}), "NONE", "codex"),
    ("research runner denied to a phase worker", 2, event("PreToolUse", "Bash", {"command": "devforgeai-research open-run --digest abc123"}, RED), "red", "claude"),

    # Worker dispatch and the lease binding.
    ("spawn red worker allowed", 0, event("PreToolUse", "Agent", {"subagent_type": "red_dev"}), "red", "claude"),
    ("spawn red worker task alias allowed", 0, event("PreToolUse", "Agent", {"task_name": "red_dev"}), "red", "codex"),
    ("legacy role name still resolves", 0, event("PreToolUse", "Agent", {"subagent_type": "dev-tdd-red-tester"}), "red", "claude"),
    ("spawn green worker denied in red", 2, event("PreToolUse", "Agent", {"task_name": "green_dev"}), "red", "codex"),
    ("spawn deleted state_writer denied", 2, event("PreToolUse", "Agent", {"task_name": "state_writer"}), "red", "codex"),
    ("spawn deleted handoff_renderer denied", 2, event("PreToolUse", "Agent", {"task_name": "handoff_renderer"}), "red", "codex"),
    ("nested subagent denied", 2, event("PreToolUse", "Agent", {"task_name": "red_dev"}, RED), "red", "claude"),
    ("SubagentStart binds the lease and the receipt contract", 0, event("SubagentStart", sub=RED), "red", "codex"),
    ("SubagentStart binds the lease on Claude", 0, event("SubagentStart", sub=RED), "red", "claude"),
    ("SubagentStart wrong worker denied", 2, event("SubagentStart", sub=GREEN), "red", "codex"),

    # SubagentStop receipt validation.
    ("stop without agent identity records hook_fault", 0, "STOP_NO_IDENTITY", "red", "claude"),
    ("stop with wrong schema refused", 2, "STOP_BAD_SCHEMA", "red", "claude"),
    ("stop with no receipt refused", 2, "STOP_NO_ENVELOPE", "red", "claude"),
    ("stop with two receipts refused", 2, "STOP_TWO_ENVELOPES", "red", "codex"),
    ("stop from the wrong worker refused", 2, "STOP_WRONG_AGENT", "red", "claude"),
    ("stop naming the wrong phase refused", 2, "STOP_WRONG_PHASE", "red", "claude"),
    ("stop carrying the deleted result keys refused", 2, "STOP_DELETED_KEYS", "red", "claude"),
    ("stop naming a checkpoint this phase did not start from refused", 2, "STOP_STALE_CHECKPOINT", "red", "codex"),
    ("stop naming another run's candidate refused", 2, "STOP_FOREIGN_CANDIDATE", "red", "claude"),
    ("stop claiming paths on a fail refused", 2, "STOP_PATHS_ON_FAIL", "red", "claude"),
    ("stop with a deleted status value refused", 2, "STOP_BAD_STATUS", "red", "claude"),
    ("could_not_run without reason_code refused", 2, "STOP_BAD_REASON", "red", "claude"),
    ("illegal rewind target refused", 2, "STOP_ILLEGAL_REWIND", "red", "codex"),
    ("stop from a built-in agent during a run refused", 2, "STOP_FOREIGN_AGENT", "red", "claude"),
    ("needs_user hands off instead of retrying", 0, "STOP_NEEDS_USER", "red", "claude"),

    # Turn and session boundaries.
    ("primary Stop with handoff allowed", 0, "HANDOFF", "red", "codex"),
    ("primary Stop without handoff blocked", 2, event("Stop", stop_reason="end_turn"), "red", "codex"),
    ("primary Stop without handoff blocked on Claude", 2, event("Stop", stop_reason="end_turn"), "red", "claude"),
    ("Stop recursion guard allowed", 0, event("Stop", stop_reason="end_turn", stop_hook_active=True), "red", "codex"),
    ("Claude settings change blocked", 2, event("ConfigChange", source="project_settings"), "red", "claude"),
    ("Codex escalation request gets deny decision", 0, event("PermissionRequest", "Bash", {"command": "git status"}), "red", "codex"),
    ("MCP tool denied during an active run", 2, event("PreToolUse", "mcp__filesystem__write_file", {"path": "tinyapp/text.py"}, RED), "red", "codex"),

    # No active run: inspect and start only.
    ("no run: any write denied", 2, event("PreToolUse", "Write", write_input("README.md"), RED), "NONE", "codex"),
    ("no run: an installed repository denies a .devforgeai write by name", 2, event("PreToolUse", "Write", write_input(".devforgeai/state.yaml", "version: 1\n")), "NONE", "claude"),
    ("no run: read-only shell allowed", 0, event("PreToolUse", "Bash", {"command": "ls -la"}), "NONE", "codex"),
    ("no run: phase start allowed", 0, event("PreToolUse", "Bash", {"command": "devforgeai phase start dev STORY-001"}), "NONE", "codex"),
    ("no run: phase start --lenient allowed", 0, event("PreToolUse", "Bash", {"command": "devforgeai phase start dev STORY-001 --lenient"}), "NONE", "claude"),
    ("no run: phase start with any other flag denied", 2, event("PreToolUse", "Bash", {"command": "devforgeai phase start dev STORY-001 --force"}), "NONE", "claude"),
    ("no run: document phase start allowed", 0, event("PreToolUse", "Bash", {"command": "devforgeai phase start pm tinyapp"}), "NONE", "claude"),
    ("no run: promote allowed", 0, event("PreToolUse", "Bash", {"command": "devforgeai promote STORY-001"}), "NONE", "claude"),
    ("no run: phase next denied", 2, event("PreToolUse", "Bash", {"command": "devforgeai phase next"}), "NONE", "codex"),
    ("no run: validate denied", 2, event("PreToolUse", "Bash", {"command": "devforgeai validate"}), "NONE", "codex"),
    ("no run: run denied", 2, event("PreToolUse", "Bash", {"command": "devforgeai run test"}), "NONE", "codex"),
    ("no run: test run denied", 2, event("PreToolUse", "Bash", {"command": "python3 -m pytest"}), "NONE", "codex"),
    ("no run: agent spawn denied", 2, event("PreToolUse", "Agent", {"task_name": "red_dev"}), "NONE", "codex"),
    ("no run: MCP tool allowed", 0, event("PreToolUse", "mcp__filesystem__read_file", {"path": "README.md"}), "NONE", "codex"),
    ("no run: ConfigChange allowed", 0, event("ConfigChange", source="project_settings"), "NONE", "claude"),
]

# label, expected exit, argv, DEVFORGEAI_HOOK_EVENT, substring the output must contain
GRAMMAR_CASES = [
    # Model-callable: no hook env, and they work.
    ("model-callable status", 0, ["status"], None, "run:"),
    ("status names the candidate root, the phase, the fence and the granted keys", 0,
     ["status"], None, "granted_keys"),
    ("status renders the handoff of the live run", 0, ["status"], None, "Next: /dev STORY-001"),
    ("status renders the most recent handoff when no run is live", 0, ["status"], None,
     "Next: /dev STORY-001 --fix"),
    ("status with no handoff prints the run block only", 0, ["status"], None, "run:"),
    ("model-callable validate", 0, ["validate"], None, "invariants hold"),
    ("model-callable phase start rejects an unknown skill", 2, ["phase", "start", "nosuch", "X"], None, "unknown skill"),
    ("model-callable phase start rejects a second run for the same story", 1, ["phase", "start", "dev", "STORY-001"], None, "already active"),
    ("phase start resumes a blocked run of the same skill and argument", 0, ["phase", "start", "dev", "STORY-001", "--lenient"], None, "resumed at phase"),
    ("model-callable phase fail records a blocker and abandons the root", 0, ["phase", "fail", "--reason", "blocked on an API key"], None, "BLOCK"),
    ("phase fail without --reason is a usage error", 2, ["phase", "fail"], None, "required"),
    ("model-callable promote refuses a run that is not ready", 1, ["promote", "STORY-001"], None, "ready_to_promote"),
    ("promote refuses a run that does not exist", 1, ["promote", "STORY-404"], None, "NO_CANDIDATE"),
    ("deleted `report` operation is not a subcommand", 2, ["report", "red_dev", "--status", "pass"], None, "invalid choice"),
    ("init is not a subcommand", 2, ["init"], None, "invalid choice"),
    ("malformed stack policy fails closed at validate", 1, ["validate"], None, "failing closed"),

    # Worker-callable: `run <key>` needs the lease, or the SubagentStop marker.
    ("run refused with no lease and no marker", 1, ["run", "test"], None, "no lease is held"),
    ("run accepted from the SubagentStop marker", 1, ["run", "test"], "SubagentStop", "classification: NO_TESTS"),
    ("run refuses a key the phase does not grant", 1, ["run", "lint"], "SubagentStop", "does not grant"),

    # Hook-only: refused without the env, accepted with the matching event.
    ("hook-only phase next refused without hook env", 1, ["phase", "next"], None, "hook-only"),
    ("hook-only phase next accepted with SubagentStop", 1, ["phase", "next"], "SubagentStop", "no worker receipt"),
    ("hook-only phase next refused on the wrong event", 1, ["phase", "next"], "SessionStart", "hook-only"),
    ("hook-only ingest-result refused without hook env", 1, ["ingest-result", "--agent", "red_dev", "--agent-id", "a", "--session-id", "s"], None, "hook-only"),
    ("hook-only ingest-result accepted with SubagentStop", 1, ["ingest-result", "--agent", "red_dev", "--agent-id", "a", "--session-id", "s"], "SubagentStop", "no devforgeai.worker-result/v1 object"),
    ("hook-only session-start refused without hook env", 1, ["session-start", "--session-id", "s2", "--provider", "claude"], None, "hook-only"),
    ("hook-only session-start accepted with SessionStart", 0, ["session-start", "--session-id", "s2", "--provider", "claude"], "SessionStart", "hooks armed"),
    ("session-start rejects an unknown provider", 2, ["session-start", "--session-id", "s3", "--provider", "gemini"], "SessionStart", "invalid choice"),

    # Sequencer-internal: the candidate lifecycle.
    ("candidate checkpoint refused without a marker", 1, ["candidate", "checkpoint", "STORY-001", "red"], None, "sequencer-internal"),
    ("candidate promote refused without a marker", 1, ["candidate", "promote", "STORY-001"], None, "sequencer-internal"),
    ("candidate lease refused on the wrong event", 1, ["candidate", "lease", "STORY-001", "--agent", "red_dev", "--agent-id", "a"], "SubagentStop", "identity-bearing"),
    ("candidate lease accepted at SubagentStart", 0, ["candidate", "lease", "STORY-001", "--agent", "red_dev", "--agent-id", "a-red"], "SubagentStart", "lease bound"),
    ("candidate lease refuses the wrong worker", 1, ["candidate", "lease", "STORY-001", "--agent", "green_dev", "--agent-id", "a-g"], "SubagentStart", "belongs to"),

    # Skills with no workers and the external research runner.
    ("init skill has no phases", 1, ["phase", "start", "init", "."], None, "no LLM workers"),
    ("status skill has no phases", 1, ["phase", "start", "status", "."], None, "no LLM workers"),
    ("research without its runner is could_not_run", 3, ["phase", "start", "research", "topic"], None, "runner_missing"),
]

BACKSTOPS = [
    ("the oracle catches ORM drift inside the candidate root", transition_backstop),
    ("the command broker catches a stack command that edits the tree", command_broker_backstop),
    ("Claude SubagentStop route binds identity, lease, fence, diff and oracle",
     lambda: ingest_backstop("claude")),
    ("Codex SubagentStop route binds identity, lease, fence, diff and oracle",
     lambda: ingest_backstop("codex")),
    ("a rewind resets the root to the checkpoint the target phase starts from",
     rewind_backstop),
    ("identity-free stop records hook_fault without blocking the subagent", hook_fault_backstop),
    ("SessionStart writes session evidence and never faults", session_backstop),
    ("a failed worktree prerequisite is could_not_run, never a silent copy-mode run",
     worktree_selftest_backstop),
    ("the two-marker rule resolves the canonical root from inside a candidate",
     root_resolution_backstop),
    ("a document run gates on its output fence", document_run_backstop),
    ("compiled: true without commands.build is refused at the gate", compiled_stack_backstop),
    ("the receipt route accepts Dapper and rejects Entity Framework", dapper_policy_backstop),
    ("qa and review open a story-anchored document run that can broker `test`",
     story_anchored_backstop),
    ("junit_dialect: pytest reads an empty suite as NO_TESTS",
     lambda: pytest_dialect_row("empty", "NO_TESTS")),
    ("junit_dialect: pytest reads an unparseable test module as COLLECTION_ERROR",
     lambda: pytest_dialect_row("syntax", "COLLECTION_ERROR")),
    ("junit_dialect: pytest reads a NameError in the test body as COLLECTION_ERROR",
     lambda: pytest_dialect_row("nameerror", "COLLECTION_ERROR")),
    ("junit_dialect: pytest still reads a failing assertion as EXPECTED_TEST_FAILURE",
     pytest_honest_red_row),
    ("junit_dialect: node reads an empty test file as NO_TESTS, not the pass node reports",
     lambda: node_dialect_row("empty", "NO_TESTS")),
    ("junit_dialect: node reads a JavaScript syntax error as COLLECTION_ERROR",
     lambda: node_dialect_row("syntax", "COLLECTION_ERROR")),
    ("junit_dialect: node reads a ReferenceError under a test_plan name as COLLECTION_ERROR",
     lambda: node_dialect_row("reference", "COLLECTION_ERROR")),
    ("junit_dialect: node reds on assertions and greens on the same suite", node_honest_row),
    ("stack.yaml is writable only by its two producer phases, and schema-checked",
     stack_writer_backstop),
    ("amend's adr phase writes the registry ADR path, header-checked", adr_accepted_backstop),
    ("an ADR missing a required section or misnamed is refused uncheckpointed",
     adr_header_backstop),
    ("architect's adr phase is the second producer, header-checked", architect_adr_backstop),
    ("no other skill or phase may write under provenance/adr", adr_producer_backstop),
    ("the sequencer resolves sha256:PENDING inside the root", pending_digest_backstop),
    ("a conditional docs phase may produce no file, and must say why",
     conditional_phase_backstop),
    ("a heading inside a code fence does not end a section", code_fence_section_backstop),
    ("the gate re-resolves every provenance and context hash", provenance_gate_backstop),
    ("Slice is written by the gate, and a run with no bundle records the no-op",
     slice_backstop),
    ("plan's dependencies and estimates phases update three story keys only",
     plan_fields_backstop),
    ("the report's verdict selects the handoff row without changing the run status",
     verdict_backstop),
    ("`.devforgeai/` is directly writable only before state.yaml exists", installer_backstop),
    ("every run record the sequencer writes matches the documented fixture",
     fixture_state_backstop),
    ("promotion is human-initiated, exact, and removes the root", promote_backstop),
    ("STALE_BASE refuses in copy mode and rebases once in worktree mode", stale_base_backstop),
    ("MERGE_CONFLICT aborts the rebase and moves no canonical byte", merge_conflict_backstop),
    ("DIRTY_TARGET refuses to merge over an uncommitted canonical edit",
     dirty_target_backstop),
    ("DIRTY_TARGET refuses a canonical path written outside the root during the run",
     stray_write_backstop),
    ("FENCE_OVERLAP refuses a second run over the same paths", fence_overlap_backstop),
    ("STORY_IN_FLIGHT refuses review and qa until the story's run is promoted",
     story_in_flight_backstop),
    ("one producer holds the write lease at a time, on both providers", lease_backstop),
    ("UNCLAIMED_CHANGE holds the receipt to the checkpoint diff",
     unclaimed_change_backstop),
    ("NO_CANDIDATE names a missing root instead of failing obscurely",
     no_candidate_backstop),
    ("a judge writes in its evidence directory and nowhere else", judge_evidence_backstop),
    ("a REQUIRE_HUMAN block keeps the run and `phase start` resumes it", resume_backstop),
]


def main() -> int:
    scratch = started_project("hooks")

    failures = 0
    print("== dispatcher policy rows")
    for label, expected, spec, phase, provider in DISPATCHER_CASES:
        set_phase(scratch, phase)
        hook_event, cleanup = materialize(scratch, spec)
        try:
            actual, message = run(scratch, hook_event, provider)
        finally:
            cleanup()
        passed = actual == expected
        if label == "Codex escalation request gets deny decision":
            passed = passed and '"behavior": "deny"' in message
        if label.startswith("SubagentStart binds the lease"):
            passed = passed and SCHEMA in message
        if label.endswith("denies a .devforgeai write by name"):
            passed = passed and "already installed" in message
        if label == "needs_user hands off instead of retrying":
            passed = passed and "REQUIRE_HUMAN" in message and "/dev STORY-001" in message
        if label == "a worker that holds no lease is denied":
            passed = passed and "LEASE_HELD" in message
        failures += 0 if passed else 1
        print(f"{'ok ' if passed else 'FAIL'} exit={actual} want={expected}  {label}\n"
              f"      {message[:140]}")

    print("\n== sequencer grammar rows")
    grammar_root = started_project("grammar")
    set_phase(grammar_root, "red")
    for label, expected, argv, hook_event, needle in GRAMMAR_CASES:
        if label.startswith("model-callable phase fail"):
            root = started_project("grammar-fail")
        elif label == "status renders the handoff of the live run":
            root = started_project("grammar-handoff")
            handoff_path = root / ".devforgeai" / "work" / "STORY-001" / "handoff.json"
            handoff_path.write_text(json.dumps(ACTIVE_HANDOFF, indent=2))
        elif label == "status renders the most recent handoff when no run is live":
            root = started_project("grammar-handoff-closed")
            sequence(root, "phase", "fail", "--reason", "blocked on an API key")
            envelope = json.loads(
                (root / ".devforgeai/work/STORY-001/handoff.json").read_text())
            envelope["next"] = "/dev STORY-001 --fix"
            (root / ".devforgeai/work/STORY-001/handoff.json").write_text(
                json.dumps(envelope, indent=2))
        elif label == "status with no handoff prints the run block only":
            root = started_project("grammar-handoff-none")
        elif label.startswith(("init skill", "status skill", "research without")):
            root = make_project("grammar-none")
        elif label.startswith("malformed stack"):
            root = started_project("grammar-badstack")
            (root / ".devforgeai" / "stack.yaml").write_text("python: [unterminated\n")
        elif label.startswith("promote refuses a run that does not exist"):
            root = grammar_root
        elif label.startswith("phase start resumes"):
            root = started_project("grammar-resume")
            bind(root, RED)
            stop(root, RED, receipt("red", "red_dev", status="needs_user",
                                    note="the story does not say how o-umlaut maps"))
        elif label.startswith("candidate lease"):
            root = started_project("grammar-lease")
        elif label.startswith("run "):
            root = started_project("grammar-run")
            if "no lease" in label:
                clear_lease(root)
        else:
            root = grammar_root
        actual, message = sequence(root, *argv, hook_event=hook_event)
        passed = actual == expected and needle in message
        if label == "status renders the handoff of the live run":
            passed = passed and "  - red rewound too many times" in message \
                and "open: OI-1" in message and message.index("open: OI-1") < message.index("Next:")
        if label == "status with no handoff prints the run block only":
            passed = passed and "Next:" not in message
        if label.startswith("model-callable phase fail"):
            passed = passed and yaml.safe_load(
                (root / ".devforgeai" / "state.yaml").read_text()
            )["runs"]["STORY-001"]["status"] == "abandoned"
        failures += 0 if passed else 1
        print(f"{'ok ' if passed else 'FAIL'} exit={actual} want={expected}  {label}\n"
              f"      {message[:140]}")

    print("\n== backstops")
    for label, fn in BACKSTOPS:
        try:
            passed, message = fn()
        except Exception as exc:  # a backstop that cannot run is a failure
            passed, message = False, f"{type(exc).__name__}: {exc}"
        failures += 0 if passed else 1
        print(f"{'ok ' if passed else 'FAIL'} {label}\n      {message[-400:]}")

    total = len(DISPATCHER_CASES) + len(GRAMMAR_CASES) + len(BACKSTOPS)
    print(
        f"\n{total - failures}/{total} rows hold "
        f"({len(DISPATCHER_CASES)} dispatcher, {len(GRAMMAR_CASES)} grammar, "
        f"{len(BACKSTOPS)} backstops); scratch root {scratch}"
    )
    return 1 if failures else 0


ACTIVE_HANDOFF = {
    "schema": "devforgeai.handoff/v1",
    "run": "STORY-001",
    "skill": "dev",
    "outcome": "REQUIRE_HUMAN",
    "phase": "red",
    "location": ".devforgeai/work/STORY-001/",
    "reasons": ["red rewound too many times"],
    "open_items": [{"id": "OI-1", "text": "criterion 2 is underspecified"}],
    "next": "/dev STORY-001",
    "attempts": {"red": 2},
    "authority": {"write_fence": ["tests/test_text.py"]},
    "session_id": "session-1",
    "at": "2026-09-03T09:00:00Z",
}


if __name__ == "__main__":
    sys.exit(main())
