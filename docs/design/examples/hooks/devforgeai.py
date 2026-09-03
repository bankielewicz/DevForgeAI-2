#!/usr/bin/env python3
"""DevForgeAI sequencer: the owner of every candidate root and of canonical state.

Closed CLI grammar (D7).

Model-callable (in the provider Bash allowlist, no hook env required):
    devforgeai status                        print the run block
    devforgeai phase start <skill> <arg> [--fix] [--lenient]
                                             gate, open the candidate root, enter phase 1
    devforgeai phase fail --reason TEXT      record a blocker and hand off
    devforgeai validate                      check fence/stack invariants without advancing
    devforgeai promote <run>                 promote a run the sequencer parked for a human
    devforgeai run <key>                     lease holder only: one stack command in the root

Hook-only (refused unless DEVFORGEAI_HOOK_EVENT names the matching event):
    devforgeai session-start                 SessionStart: session evidence and self-test
    devforgeai lease-bind --agent ...        SubagentStart: bind the phase lease
    devforgeai ingest-result --agent ...     SubagentStop: read the receipt, check, advance
    devforgeai phase next                    SubagentStop: run the oracle, advance or rewind

Sequencer-internal (hook or sequencer, never a model):
    devforgeai candidate open|checkpoint|promote|abandon <run> [<phase>]

Exit codes: 0 ok, 1 refused, 2 usage, 3 could_not_run.

Producers write with Edit and Write inside the candidate root the sequencer
opened for the run; judges read. A worker's final message is one
`devforgeai.worker-result/v1` receipt naming what it claims to have changed. At
`ingest-result` the sequencer derives the real change set from the checkpoint
diff, refuses anything unclaimed or outside the fence, runs the transition
oracle in the root, checkpoints, releases the lease, and advances. Canonical
files change only at promotion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

from policy import (
    ALWAYS_DENY,
    CANDIDATE_OPS,
    GATE_POLICIES,
    HOOK_ONLY,
    JUNIT_DIALECTS,
    MAX_CLAIMED_PATHS,
    MAX_EVIDENCE_REFS,
    REASON_CODES,
    RECEIPT_KEYS,
    MAX_FINDINGS_BYTES,
    FIX_REPORT_SOURCES,
    RECEIPT_REQUIRED,
    REPORT_VERDICTS,
    STORY_IN_FLIGHT_EXEMPT,
    RESULT_SCHEMA,
    RUN_MARKER,
    SKILL_VARIANTS,
    SKILLS,
    VERDICT_NEXT,
    VERDICT_PHASES,
    WORK_PREFIX,
    WORKER_STATUS,
    PolicyError,
    allowed_agents,
    canonical_agent,
    document_fence,
    effective_fence,
    fence_overlap,
    findings_path,
    handoff_kind,
    handoff_next,
    is_judge,
    matches,
    phase_fields,
    phase_names,
    phase_run_keys,
    phase_spec,
    project_relative,
    refused_tool,
    run_id,
    skill_key,
    skill_produces,
    skill_spec,
    stack_problems,
    story_anchored,
    techstack_text_problems,
    techstack_tree_problems,
    validate_phase_write_path,
)

OK, REFUSED, USAGE, COULD_NOT_RUN = 0, 1, 2, 3


def resolve_context(start: str | Path) -> tuple[Path, str | None]:
    """The two-marker root rule (D5).

    Walk up from `start` to the nearest `.devforgeai/`. When it holds a
    `run.yaml` marker, the walk started inside a candidate root: the canonical
    project is the path that marker records, and the run is the one it names.
    Otherwise the directory holding `state.yaml` is canonical and no run is
    implied by position. Nothing inside a candidate root ever reads
    `state.yaml`, which is why the marker carries the canonical path instead.
    """
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
            canonical = Path(str(doc.get("canonical") or candidate)).resolve()
            return canonical, (str(doc.get("run")) if doc.get("run") else None)
        if (candidate / ".devforgeai" / "state.yaml").exists():
            return candidate, None
    return path, None


ROOT, MARKER_RUN = resolve_context(os.environ.get("DEVFORGEAI_ROOT") or os.getcwd())
DF = ROOT / ".devforgeai"
STATE = DF / "state.yaml"
LOCK = DF / "lock"
IGNORE_DIRS = {
    ".devforgeai", ".git", ".claude", ".codex", ".agents", "__pycache__",
    ".pytest_cache", ".ruff_cache", ".venv", "node_modules",
}
# Excluded from a copy-mode candidate and from every tree manifest: the
# repository itself, and the caches a runner writes rather than a project keeps.
# Everything else a project might want left behind — `.venv`, `node_modules`,
# `dist` — is the project's own call, declared in `stack.yaml#ignore_dirs`, so a
# Python project that vendors its environment is not silently half-copied.
# `.devforgeai` is not here either: `.devforgeai/stack.yaml` and
# `.devforgeai/provenance/adr/**` are producer-exception artifacts a worker
# writes inside the root, so they are copied in and diffed. The run marker,
# `.devforgeai/work/` and the rest of the framework's bookkeeping are excluded by
# path in `sequencer_owned`.
CANDIDATE_SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".ruff_cache"}
GIT_IDENTITY = {
    "GIT_AUTHOR_NAME": "DevForgeAI sequencer",
    "GIT_AUTHOR_EMAIL": "sequencer@devforgeai.invalid",
    "GIT_COMMITTER_NAME": "DevForgeAI sequencer",
    "GIT_COMMITTER_EMAIL": "sequencer@devforgeai.invalid",
    "GIT_CONFIG_NOSYSTEM": "1",
}

MAX_RESULT_BYTES = 4 * 1024 * 1024
MAX_ISSUES = 10
HANDOFF_SCHEMA = "devforgeai.handoff/v1"


class Refuse(SystemExit):
    def __init__(self, msg: str, code: int = REFUSED):
        sys.stderr.write(f"devforgeai: {msg}\n")
        super().__init__(code)


def require_hook(op: str) -> None:
    """Hook-only operations refuse a model-typed invocation."""
    expected = HOOK_ONLY[op]
    if os.environ.get("DEVFORGEAI_HOOK_EVENT") != expected:
        raise Refuse(
            f"`devforgeai {op}` is hook-only; it runs only from the {expected} hook "
            "(DEVFORGEAI_HOOK_EVENT). Workers do not sequence.",
            REFUSED,
        )


def require_internal(op: str) -> None:
    """`candidate <op>` belongs to the sequencer and to the hooks that call it."""
    if op == "lease" and os.environ.get("DEVFORGEAI_HOOK_EVENT") not in (None, "", "SubagentStart") \
            and os.environ.get("DEVFORGEAI_INTERNAL") != "1":
        raise Refuse(
            "`devforgeai candidate lease` binds the write lease at SubagentStart, the only "
            "identity-bearing pre-write event; no other event may bind it.",
            REFUSED,
        )
    if os.environ.get("DEVFORGEAI_INTERNAL") == "1" or os.environ.get("DEVFORGEAI_HOOK_EVENT"):
        return
    raise Refuse(
        f"`devforgeai candidate {op}` is a sequencer-internal operation; `phase start`, "
        "`ingest-result`, run end and `phase fail` call it. The model-callable form is "
        "`devforgeai promote <run>`.",
        REFUSED,
    )


# ---------- canonical state and per-run state (D5) ----------

def load() -> dict:
    """Canonical `.devforgeai/state.yaml`: story statuses and the run index."""
    return yaml.safe_load(STATE.read_text()) if STATE.exists() else {}


def save(state: dict) -> None:
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(yaml.safe_dump(state, sort_keys=False))
    os.replace(tmp, STATE)


def work(run: str) -> Path:
    p = DF / "work" / run
    p.mkdir(parents=True, exist_ok=True)
    return p


def run_file(run: str) -> Path:
    return DF / "work" / run / "run.yaml"


def load_run(run: str) -> dict:
    path = run_file(run)
    if not path.exists():
        raise Refuse(f"run {run} has no run.yaml; it was never opened or was abandoned")
    doc = yaml.safe_load(path.read_text()) or {}
    if not isinstance(doc, dict) or not doc.get("run"):
        raise Refuse(f"run {run}: run.yaml is not a run record; failing closed")
    return doc


def save_run(e: dict) -> None:
    path = run_file(e["run"])
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(yaml.safe_dump(e, sort_keys=False))
    os.replace(tmp, path)


def live_runs(state: dict) -> list[str]:
    return sorted(
        name for name, row in (state.get("runs") or {}).items()
        if (row or {}).get("status") in ("active", "ready_to_promote")
    )


def active_run_id(state: dict, requested: str | None = None) -> str:
    """The run this invocation is about, by the D5 resolution rule."""
    name = requested or MARKER_RUN or os.environ.get("DEVFORGEAI_RUN") or ""
    if name:
        return name
    live = [n for n in live_runs(state) if (state["runs"][n] or {}).get("status") == "active"]
    if len(live) == 1:
        return live[0]
    if not live:
        raise Refuse("no run is active; run `devforgeai phase start <skill> <arg>`")
    raise Refuse(
        f"{len(live)} runs are active ({', '.join(live)}); name one with --run, or work "
        "inside its candidate root",
        REFUSED,
    )


def enf(state: dict | None = None, run: str | None = None) -> dict:
    """The per-run enforcement record for the run this invocation is about."""
    return load_run(active_run_id(state if state is not None else load(), run))


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def current_session() -> str:
    """Newest session evidence file wins; '' when no SessionStart hook has run."""
    sessions = DF / "sessions"
    newest, newest_at = "", ""
    if sessions.is_dir():
        for path in sessions.glob("*.json"):
            try:
                doc = json.loads(path.read_text())
            except (OSError, json.JSONDecodeError):
                continue
            at = str(doc.get("at") or "")
            if at >= newest_at:
                newest, newest_at = str(doc.get("session_id") or path.stem), at
    return newest


def append_session_event(session_id: str, kind: str, **fields) -> None:
    """The session file is written once and appended with lease events (10 s8)."""
    path = DF / "sessions" / f"{session_id}.json"
    if not path.exists():
        return
    try:
        doc = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return
    events = doc.get("events")
    if not isinstance(events, list):
        events = []
    events.append({"at": now(), "kind": kind, **fields})
    doc["events"] = events[-64:]
    write_json_atomic(path, doc)


def log(kind: str, session_id: str | None = None, **fields) -> None:
    (DF / "provenance").mkdir(parents=True, exist_ok=True)
    row = {
        "at": now(),
        "kind": kind,
        "session_id": session_id if session_id is not None else current_session(),
        **fields,
    }
    with (DF / "provenance" / "log.jsonl").open("a") as f:
        f.write(json.dumps(row) + "\n")


# ---------- the candidate root (D2) ----------

def sha(p: Path) -> str:
    return "sha256:" + hashlib.sha256(p.read_bytes()).hexdigest()


def in_fence(path: str, fence: list[str]) -> bool:
    return matches(path, fence)


def candidate_root(e: dict) -> Path:
    root = (e.get("candidate") or {}).get("root")
    if not root:
        raise Refuse(f"NO_CANDIDATE: run {e['run']} has no candidate root", REFUSED)
    path = Path(str(root))
    if not path.is_dir():
        raise Refuse(
            f"NO_CANDIDATE: the candidate root {path} for run {e['run']} does not exist; "
            "the run cannot be worked on until it is reopened",
            REFUSED,
        )
    return path


def run_sequencer_writes(run: str) -> set[str]:
    """Canonical paths this run's sequencer wrote; never a candidate change."""
    try:
        return set(sequencer_writes(run))
    except (OSError, ValueError):
        return set()


def sequencer_owned(rel: str) -> bool:
    """Framework bookkeeping: never a worker change, never a promotion input.

    `.devforgeai/stack.yaml` and `.devforgeai/provenance/adr/**` are deliberately
    absent: they are producer-exception artifacts a worker writes inside the
    root, so they are hashed, diffed and promoted like any other file. The run
    file, the work directory, the session evidence, the promotion lock, the
    provenance log and canonical state are the sequencer's own, and a copy-mode
    base digest that counted them would go stale the moment the run started.
    """
    if rel == RUN_MARKER or rel.startswith(WORK_PREFIX):
        return True
    if rel in (".devforgeai/state.yaml", ".devforgeai/lock"):
        return True
    if rel.startswith(".devforgeai/sessions/"):
        return True
    return (rel.startswith(".devforgeai/provenance/")
            and not rel.startswith(".devforgeai/provenance/adr/"))


def manifest_paths(root: Path, ignore_dirs) -> list[str]:
    """Every project-relative path a copy-mode manifest and copy cover."""
    skip = set(CANDIDATE_SKIP_DIRS)
    out: list[str] = []
    for directory, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in skip]
        rel_dir = Path(directory).relative_to(root).as_posix()
        dirs[:] = [
            d for d in dirs
            if not matches((f"{rel_dir}/{d}" if rel_dir != "." else d), list(ignore_dirs or []))
        ]
        for name in files:
            rel = (Path(directory) / name).relative_to(root).as_posix()
            if not sequencer_owned(rel):
                out.append(rel)
    return sorted(out)


def manifest(root: Path, ignore_dirs) -> dict[str, str]:
    result = {}
    for rel in manifest_paths(root, ignore_dirs):
        try:
            result[rel] = sha(root / rel)
        except OSError:
            continue
    return result


def manifest_digest(rows: dict[str, str]) -> str:
    return "sha256:" + hashlib.sha256(
        json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    proc = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True,
        env={**os.environ, **GIT_IDENTITY}, timeout=300,
    )
    if check and proc.returncode != 0:
        raise Refuse(
            f"git {' '.join(args)} failed in {cwd}: {(proc.stderr or proc.stdout).strip()[-600:]}",
            REFUSED,
        )
    return proc


def git_repo(path: Path) -> bool:
    if shutil.which("git") is None:
        return False
    return git(path, "rev-parse", "--git-dir", check=False).returncode == 0


def worktree_prerequisites(path: Path) -> list[str]:
    """The SessionStart self-test for worktree mode (D6).

    A git repository that fails any of these is a hook fault, never a silent
    fall back to copy mode: the run would lose its history and its rewind.
    """
    problems: list[str] = []
    if not git_repo(path):
        return ["not a git repository"]
    if git(path, "rev-parse", "--verify", "HEAD", check=False).returncode != 0:
        problems.append("the repository has no HEAD commit")
    if git(path, "check-ignore", "-q", ".devforgeai/work/probe", check=False).returncode != 0:
        problems.append(".devforgeai/work/ is not ignored by git")
    tracked = [".devforgeai/stack.yaml"]
    if (path / ".claude").is_dir():
        tracked.append(".claude/settings.json")
    for rel in tracked:
        if git(path, "ls-files", "--error-unmatch", rel, check=False).returncode != 0:
            problems.append(f"{rel} is not tracked")
    return problems


def candidate_open(e: dict, ignore_dirs) -> dict:
    """Materialise the run's candidate root and return its `candidate` block."""
    root = work(e["run"]) / "wt"
    shutil.rmtree(root, ignore_errors=True)
    branch = f"devforgeai/{e['run']}"
    if git_repo(ROOT) and git(ROOT, "rev-parse", "--verify", "HEAD", check=False).returncode == 0:
        problems = worktree_prerequisites(ROOT)
        if problems:
            sys.stderr.write(
                "devforgeai: could_not_run reason_code=prerequisite_missing: worktree "
                "mode is unavailable and copy mode is not a substitute in a git "
                "repository:\n  "
                + "\n  ".join(problems) + "\n"
            )
            raise SystemExit(COULD_NOT_RUN)
        git(ROOT, "worktree", "prune")
        git(ROOT, "branch", "-D", branch, check=False)
        base = git(ROOT, "rev-parse", "HEAD").stdout.strip()
        git(ROOT, "worktree", "add", "-b", branch, str(root), base)
        exclude_sequencer_paths(ROOT)
        mode, base_ref = "worktree", base
        dirty_at_open = sorted(canonical_dirty_set())
    else:
        dirty_at_open = []
        copy_tree(ROOT, root, ignore_dirs)
        mode, base_ref = "copy", manifest_digest(manifest(root, ignore_dirs))
    candidate = {"mode": mode, "root": str(root), "base_ref": base_ref,
                 "checkpoint": "base", "dirty_at_open": dirty_at_open}
    write_marker(root, e["run"])
    if mode == "copy":
        write_copy_checkpoint(e["run"], root, ignore_dirs, "base")
    return candidate


def write_copy_checkpoint(run: str, root: Path, ignore_dirs, phase: str) -> dict[str, str]:
    """Copy mode's checkpoint: a tree-hash manifest plus the bytes it names."""
    rows = manifest(root, ignore_dirs)
    write_json_atomic(work(run) / "cp" / f"{phase}.manifest.json", rows)
    aside = work(run) / "cp" / phase / "files"
    shutil.rmtree(aside, ignore_errors=True)
    for rel in rows:
        target = aside / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / rel, target)
    return rows


def write_marker(root: Path, run: str) -> None:
    """The candidate-root half of the two-marker rule."""
    marker = root / RUN_MARKER
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(yaml.safe_dump({"run": run, "canonical": str(ROOT)}, sort_keys=False))


def exclude_sequencer_paths(path: Path) -> None:
    """Keep the marker and the runner's caches out of every candidate commit."""
    common = git(path, "rev-parse", "--git-common-dir", check=False).stdout.strip()
    if not common:
        return
    info = (path / common if not Path(common).is_absolute() else Path(common)) / "info"
    info.mkdir(parents=True, exist_ok=True)
    exclude = info / "exclude"
    existing = exclude.read_text() if exclude.exists() else ""
    wanted = [RUN_MARKER, ".pytest_cache/", "__pycache__/", "*.pyc"]
    missing = [line for line in wanted if line not in existing.splitlines()]
    if missing:
        exclude.write_text(existing.rstrip("\n") + "\n" + "\n".join(missing) + "\n")


def copy_tree(source: Path, destination: Path, ignore_dirs) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for rel in manifest_paths(source, ignore_dirs):
        target = destination / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / rel, target)


def checkpoint_ref(e: dict, phase: str) -> str:
    return f"devforgeai/{e['run']}/{phase}"


def candidate_branch(e: dict) -> str:
    """The run branch. Derived, not stored: the run id is the whole name."""
    return f"devforgeai/{e['run']}"


def candidate_ignore(e: dict) -> list[str]:
    """`stack.yaml#ignore_dirs` for this run, re-resolved from canonical."""
    return stack_ignore_dirs(e)


def sequencer_writes_path(run: str) -> Path:
    return work(run) / "sequencer-writes.json"


def sequencer_writes(run: str) -> list[str]:
    path = sequencer_writes_path(run)
    return json.loads(path.read_text()) if path.exists() else []


def record_sequencer_write(run: str, relative: str) -> None:
    """Canonical paths the sequencer itself wrote during the run.

    The sequencer is not drift of its own run: copy mode's base comparison
    ignores them, because it wrote them after `phase start` pinned the base.
    """
    rows = sorted(set(sequencer_writes(run)) | {relative})
    write_json_atomic(sequencer_writes_path(run), rows)


def candidate_changes(e: dict) -> list[dict]:
    """`changed[]` since the run's input checkpoint, derived from the root itself.

    Worktree mode stages the tree and reads `git diff --cached --name-status`
    against the checkpoint tag; copy mode compares the current tree manifest
    against the manifest that checkpoint recorded. Neither asks the worker.
    """
    root, mode = candidate_root(e), (e["candidate"]).get("mode")
    since = (e["candidate"]).get("checkpoint") or "base"
    if mode == "worktree":
        git(root, "add", "-A")
        against = e["candidate"]["base_ref"] if since == "base" else checkpoint_ref(e, since)
        out = git(root, "diff", "--cached", "--name-status", "-z", against).stdout
        rows: list[dict] = []
        fields = [f for f in out.split("\0") if f]
        index = 0
        while index < len(fields):
            status = fields[index]
            if status[0] in ("R", "C"):
                source, target = fields[index + 1], fields[index + 2]
                index += 3
                rows.append({"path": source, "kind": "deleted", "blob_sha256": "ABSENT"})
                rows.append({"path": target, "kind": "added",
                             "blob_sha256": sha(root / target)})
                continue
            path = fields[index + 1]
            index += 2
            if sequencer_owned(path) or path in run_sequencer_writes(e["run"]):
                continue
            kind = {"A": "added", "D": "deleted"}.get(status[0], "modified")
            rows.append({
                "path": path, "kind": kind,
                "blob_sha256": "ABSENT" if kind == "deleted" else sha(root / path),
            })
        return sorted(rows, key=lambda row: row["path"])
    before = json.loads((work(e["run"]) / "cp" / f"{since}.manifest.json").read_text())
    after = manifest(root, candidate_ignore(e))
    rows = []
    for path in sorted(set(before) | set(after)):
        if before.get(path) == after.get(path):
            continue
        if path not in after:
            rows.append({"path": path, "kind": "deleted", "blob_sha256": "ABSENT"})
        else:
            rows.append({"path": path, "kind": "added" if path not in before else "modified",
                         "blob_sha256": after[path]})
    return rows


def candidate_checkpoint(e: dict, phase: str) -> str:
    """Freeze the root at the end of `phase` and return the new checkpoint name."""
    root, mode = candidate_root(e), e["candidate"]["mode"]
    if mode == "worktree":
        git(root, "add", "-A")
        git(root, "commit", "--allow-empty", "-q", "-m",
            f"devforgeai {e['run']} {phase}", check=False)
        git(root, "tag", "-f", checkpoint_ref(e, phase))
    else:
        write_copy_checkpoint(e["run"], root, candidate_ignore(e), phase)
    e["candidate"]["checkpoint"] = phase
    return phase


def candidate_rewind(e: dict, phase: str) -> None:
    """Put the root back to the checkpoint of `phase` (or to the base)."""
    root, mode = candidate_root(e), e["candidate"]["mode"]
    if mode == "worktree":
        target = e["candidate"]["base_ref"] if phase == "base" else checkpoint_ref(e, phase)
        git(root, "reset", "--hard", "-q", target)
        git(root, "clean", "-fdq")
        write_marker(root, e["run"])
    else:
        rows = json.loads((work(e["run"]) / "cp" / f"{phase}.manifest.json").read_text())
        aside = work(e["run"]) / "cp" / phase / "files"
        for rel in manifest_paths(root, candidate_ignore(e)):
            if rel not in rows:
                (root / rel).unlink()
        for rel in rows:
            source = aside / rel
            if source.exists():
                (root / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, root / rel)
    e["candidate"]["checkpoint"] = phase


def checkpoint_bytes(e: dict, phase: str, path: str) -> bytes | None:
    """One file exactly as the named checkpoint recorded it, or None."""
    if e["candidate"]["mode"] == "worktree":
        ref = e["candidate"]["base_ref"] if phase == "base" else checkpoint_ref(e, phase)
        proc = subprocess.run(
            ["git", "show", f"{ref}:{path}"], cwd=candidate_root(e),
            capture_output=True, env={**os.environ, **GIT_IDENTITY}, timeout=120,
        )
        return proc.stdout if proc.returncode == 0 else None
    source = work(e["run"]) / "cp" / phase / "files" / path
    return source.read_bytes() if source.is_file() else None


def promotion_rows(e: dict) -> list[dict]:
    """Everything the run changed since its base: the promotion's whole payload.

    Promotion is not the last phase's diff. It is the difference between the
    base the run pinned and the checkpoint it ended on.
    """
    root, mode = candidate_root(e), e["candidate"]["mode"]
    checkpoint = e["candidate"].get("checkpoint") or "base"
    if mode == "worktree":
        fields = [f for f in git(
            root, "diff", "--name-status", "-z", e["candidate"]["base_ref"], "HEAD"
        ).stdout.split("\0") if f]
        rows, index = [], 0
        while index < len(fields):
            status = fields[index]
            if status[0] in ("R", "C"):
                rows.append({"path": fields[index + 1], "kind": "deleted"})
                rows.append({"path": fields[index + 2], "kind": "added"})
                index += 3
                continue
            path = fields[index + 1]
            index += 2
            if not sequencer_owned(path) and path not in run_sequencer_writes(e["run"]):
                rows.append({"path": path,
                             "kind": {"A": "added", "D": "deleted"}.get(status[0], "modified")})
        return sorted(rows, key=lambda row: row["path"])
    before = json.loads((work(e["run"]) / "cp" / "base.manifest.json").read_text())
    after = json.loads((work(e["run"]) / "cp" / f"{checkpoint}.manifest.json").read_text()) \
        if checkpoint != "base" else dict(before)
    rows = []
    for path in sorted(set(before) | set(after)):
        if before.get(path) == after.get(path):
            continue
        rows.append({"path": path,
                     "kind": "deleted" if path not in after
                     else ("added" if path not in before else "modified")})
    return rows


def canonical_dirty_set() -> set[str]:
    """Every canonical working-tree path git reports as modified or untracked."""
    if not git_repo(ROOT):
        return set()
    out = git(ROOT, "status", "--porcelain", "-z", check=False).stdout
    return {row[3:] for row in out.split("\0") if len(row) > 3}


def canonical_dirty(paths) -> list[str]:
    """Canonical working-tree files that promotion would overwrite."""
    return sorted(canonical_dirty_set() & set(paths))


def stray_canonical_writes(e: dict, changed) -> list[str]:
    """Canonical paths that became dirty during the run and are not the run's own.

    A worker whose hook failed open, or a subprocess a hook cannot see, may have
    written outside the candidate root. Promotion refuses rather than carrying
    an unaudited canonical edit forward; the sequencer's own report files and
    the run's declared change set are excluded.
    """
    if e["candidate"].get("mode") != "worktree":
        return []
    before = set(e["candidate"].get("dirty_at_open") or [])
    own = set(changed) | set(sequencer_writes(e["run"]))
    now = canonical_dirty_set()
    # Canonical `.devforgeai/` is the sequencer's own (state, lock, sessions,
    # provenance log); hooks deny workers there, so it is not a stray signal.
    return sorted(p for p in now - before - own
                  if not p.startswith(".devforgeai/") and not p.endswith("/"))


def candidate_promote(e: dict, state: dict) -> list[str]:
    """Move the run's work into the canonical checkout, or say why not.

    Returns an empty list on success and the refusal rows otherwise; each row
    opens with the refusal token so a caller can match on it.
    """
    root = candidate_root(e)
    rows = promotion_rows(e)
    changed = [row["path"] for row in rows]
    lock = acquire_lock()
    try:
        if e["candidate"]["mode"] == "worktree":
            head = git(ROOT, "rev-parse", "HEAD").stdout.strip()
            if head != e["candidate"]["base_ref"]:
                log("promote.stale", run=e["run"], base=e["candidate"]["base_ref"], head=head)
                sys.stderr.write(
                    f"devforgeai: STALE_BASE: canonical HEAD moved from "
                    f"{e['candidate']['base_ref'][:12]} to {head[:12]}; rebasing the "
                    "candidate before the fast-forward\n"
                )
                rebase = git(root, "rebase", head, check=False)
                if rebase.returncode != 0:
                    git(root, "rebase", "--abort", check=False)
                    return [f"MERGE_CONFLICT: the candidate does not rebase onto {head[:12]}; "
                            "a human resolves this one"]
                # The rebase rewrote the run's commits, so the checkpoint tag
                # must follow them: the tip is the checkpoint the run ended on.
                e["candidate"]["base_ref"] = head
                git(root, "tag", "-f", checkpoint_ref(e, e["candidate"]["checkpoint"]),
                    check=False)
                problems = run_oracle(e, {"status": "pass"})
                if problems:
                    return ["MERGE_CONFLICT: the rebased candidate no longer satisfies the "
                            + e["phase"] + " oracle:\n  " + "\n  ".join(problems)]
            dirty = canonical_dirty(changed)
            if dirty:
                return [f"DIRTY_TARGET: canonical has uncommitted changes to {dirty}"]
            stray = stray_canonical_writes(e, changed)
            if stray:
                return [f"DIRTY_TARGET: canonical paths changed outside the candidate root "
                        f"during the run: {stray}"]
            merge = git(ROOT, "merge", "--ff-only", candidate_branch(e), check=False)
            if merge.returncode != 0:
                return ["MERGE_CONFLICT: " + (merge.stderr or merge.stdout).strip()[-400:]]
        else:
            ignore_dirs = candidate_ignore(e)
            canonical_rows = manifest(ROOT, ignore_dirs)
            for rel in sequencer_writes(e["run"]):
                canonical_rows.pop(rel, None)
            if manifest_digest(canonical_rows) != e["candidate"]["base_ref"]:
                return ["STALE_BASE: the canonical tree changed since this run opened; "
                        "copy mode has no automated integration, so a human decides"]
            checkpoint = e["candidate"].get("checkpoint") or "base"
            aside = work(e["run"]) / "cp" / checkpoint / "files"
            for row in rows:
                target = ROOT / row["path"]
                if row["kind"] == "deleted":
                    target.unlink(missing_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(aside / row["path"], target)
    finally:
        release_lock(lock)
    state.setdefault("runs", {}).setdefault(e["run"], {})["status"] = "promoted"
    state["runs"][e["run"]]["checkpoint"] = e["candidate"]["checkpoint"]
    log("promote", run=e["run"], mode=e["candidate"]["mode"], paths=changed)
    return []


def candidate_remove(e: dict) -> None:
    """Delete the root, its branch and its tags (promotion step 6, and abandon)."""
    root = Path(str((e.get("candidate") or {}).get("root") or ""))
    if (e.get("candidate") or {}).get("mode") == "worktree":
        if root.is_dir():
            git(ROOT, "worktree", "remove", "--force", str(root), check=False)
        git(ROOT, "worktree", "prune", check=False)
        git(ROOT, "branch", "-D", candidate_branch(e), check=False)
        for phase in ("base", *phase_names(e["skill"])):
            git(ROOT, "tag", "-d", checkpoint_ref(e, phase), check=False)
    elif root.is_dir():
        shutil.rmtree(root, ignore_errors=True)
    shutil.rmtree(work(e["run"]) / "cp", ignore_errors=True)


def candidate_abandon(e: dict, state: dict) -> None:
    root = str((e.get("candidate") or {}).get("root") or "")
    if not root or not Path(root).is_dir():
        raise Refuse(
            f"NO_CANDIDATE: run {e['run']} has no candidate root: it was never opened, or it "
            "was already promoted or abandoned",
            REFUSED,
        )
    candidate_remove(e)
    save_run(e)
    state.setdefault("runs", {}).setdefault(e["run"], {})["status"] = "abandoned"
    log("abandon", run=e["run"])


def acquire_lock() -> Path:
    """Serialise promotion under `.devforgeai/lock` (D3)."""
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    for _ in range(300):
        try:
            handle = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            time.sleep(0.1)
            continue
        os.write(handle, str(os.getpid()).encode())
        os.close(handle)
        return LOCK
    sys.stderr.write(
        f"devforgeai: could_not_run reason_code=timeout: another promotion holds {LOCK}; "
        "retry when it finishes\n"
    )
    raise SystemExit(COULD_NOT_RUN)


def release_lock(path: Path) -> None:
    try:
        path.unlink()
    except OSError:
        pass


# ---------- stack ----------

def stack_section(e: dict) -> dict | None:
    """The resolved stack.yaml section, or None for a run with no commands."""
    src = (e.get("commands") or {}).get("source")
    if not src:
        return None
    path, _, anchor = src.partition("#")
    try:
        path = project_relative(ROOT, path)
        doc = yaml.safe_load((ROOT / path).read_text()) or {}
    except (OSError, PolicyError, yaml.YAMLError) as exc:
        raise Refuse(f"cannot load stack policy; failing closed: {exc}", REFUSED) from exc
    if not isinstance(doc, dict):
        raise Refuse("stack policy is not a mapping; failing closed", REFUSED)
    sec = doc.get(anchor) if anchor else doc
    if not isinstance(sec, dict):
        raise Refuse(f"stack.yaml has no section {anchor}", REFUSED)
    return sec


def command_entry(stack: dict, key: str) -> dict | None:
    entry = (stack.get("commands") or {}).get(key)
    return entry if isinstance(entry, dict) else None


def run_key(e: dict, key: str) -> dict:
    """Run one stack.yaml command. Returns a structured outcome record."""
    if key not in ((e.get("commands") or {}).get("use") or []):
        raise Refuse(f"run does not authorise command key '{key}'")
    stack = stack_section(e)
    if stack is None:
        return {"key": key, "classification": "INFRA_FAILURE", "exit": -1,
                "output": "run has no stack.yaml section", "junit": {}, "counts": {}}
    entry = command_entry(stack, key)
    if not entry:
        return {"key": key, "classification": "INFRA_FAILURE", "exit": -1,
                "output": f"stack.yaml defines no '{key}' command", "junit": {}, "counts": {}}
    argv = entry.get("argv")
    if not isinstance(argv, list) or not argv:
        return {"key": key, "classification": "INFRA_FAILURE", "exit": -1,
                "output": f"stack command '{key}' has no argv array", "junit": {}, "counts": {}}
    argv = [str(a) for a in argv]
    root = candidate_root(e)
    cwd = root / str(entry.get("cwd") or ".")
    timeout = int(entry.get("timeout_s") or 600)
    junit_path = entry.get("junit_path")
    if junit_path:
        target = root / str(junit_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            target.unlink()
    if shutil.which(argv[0]) is None:
        return {"key": key, "classification": "INFRA_FAILURE", "exit": -1,
                "output": f"{argv[0]} not found", "junit": {}, "counts": {}}
    try:
        p = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        partial = ((exc.stdout or "") + (exc.stderr or ""))
        partial = partial.decode(errors="replace") if isinstance(partial, bytes) else partial
        return {"key": key, "classification": "TIMEOUT", "exit": -1,
                "output": f"stack command '{key}' timed out after {timeout}s\n{partial[-3000:]}",
                "junit": {}, "counts": {}}
    out = (p.stdout + p.stderr)[-4000:]
    if re.search(r"No module named \S+", out) and p.returncode != 0:
        return {"key": key, "classification": "INFRA_FAILURE", "exit": p.returncode,
                "output": out, "junit": {}, "counts": {}}
    results, counts = read_junit(root, entry, stack)
    return {
        "key": key,
        "classification": classify(key, p.returncode, results, counts, junit_path),
        "exit": p.returncode,
        "output": out,
        "junit": results,
        "counts": counts,
    }


def read_junit(root: Path, entry: dict,
               stack: dict | None = None) -> tuple[dict[str, str], dict[str, int]]:
    junit_path = entry.get("junit_path")
    if not junit_path:
        return {}, {}
    p = root / str(junit_path)
    if not p.exists():
        return {}, {}
    try:
        xml_root = ET.parse(p).getroot()
    except ET.ParseError:
        return {}, {"parse_error": 1}
    section = stack or {}
    return normalize_junit(
        str(section.get("junit_dialect") or "generic"),
        xml_root,
        str(section.get("test_glob") or ""),
    )


# ---------- runner normalisation ----------
#
# The oracle speaks one vocabulary: a `<failure>` is a test that ran and failed
# an assertion, an `<error>` is a test that never ran. Real runners do not all
# speak it, and read literally their XML lets a red gate be satisfied by
# something that is not a failing assertion — which is the one thing the gate
# exists to require. Three cases, each observed against the live reporter:
#
#   * node's built-in runner reports an assertion failure, a ReferenceError
#     thrown inside a test body, and a module that would not parse, all as
#     `<failure type="testCodeFailure">`; only the assertion spells out
#     `cause: AssertionError [ERR_ASSERTION]` in the element body;
#   * an empty test file makes node emit one passing testcase named after the
#     file, so an empty red suite reads as a green one;
#   * pytest reports a `NameError` raised in a test body as a `<failure>`,
#     distinguishable from a real assertion only by its `message`.
#
# So a section names the runner that wrote its `junit_path`, and this boundary
# maps that runner's XML onto the generic vocabulary before `classify` sees it.
# It only ever moves an outcome towards `error` or drops a case that never ran;
# it never turns an error into a failure or a failure into a pass. `generic`
# reads the file exactly as the oracle always has.

NODE_TEST_FILE = re.compile(r"\.(?:js|mjs|cjs)$")
NODE_ASSERTION_MARKERS = ("ERR_ASSERTION", "AssertionError")
PYTEST_ASSERTION_PREFIXES = ("AssertionError", "assert ", "Failed:")


def normalize_junit(dialect: str, xml_root,
                    test_glob: str = "") -> tuple[dict[str, str], dict[str, int]]:
    """Read one runner's JUnit XML in the oracle's own vocabulary.

    Returns `(results, counts)`: a name -> `passed|failed|error|skipped` mapping
    and the suite totals `classify` reads. A dialect this does not know is read
    as `generic`; the gate refuses a section naming anything outside
    `JUNIT_DIALECTS`, so that fallback is a backstop, never a relaxation.
    """
    if dialect not in JUNIT_DIALECTS:
        dialect = "generic"
    results: dict[str, str] = {}
    for tc in xml_root.iter("testcase"):
        name = tc.get("name", "")
        state = junit_state(tc)
        if dialect == "node":
            if node_file_case(name, test_glob):
                # Node emits a testcase for the file itself only when the file
                # produced no subtests. Clean means no test ran at all, so the
                # case is dropped and `classify` reports NO_TESTS instead of
                # reading an empty file as a pass. Not clean means the module
                # threw before any test registered — a syntax error, a failed
                # import — which is a collection error for the whole run, not
                # one failing test.
                if state != "passed":
                    results[name] = "error"
                continue
            if state == "failed" and not element_carries(
                    tc.find("failure"), NODE_ASSERTION_MARKERS):
                state = "error"
        elif dialect == "pytest" and state == "failed":
            if not pytest_assertion(tc.find("failure")):
                state = "error"
        results[name] = state
    counts: dict[str, int] = {"tests": len(results)}
    for suite in xml_root.iter("testsuite"):
        for field in ("errors", "failures"):
            counts[field] = counts.get(field, 0) + int(suite.get(field) or 0)
    return results, counts


def junit_state(tc) -> str:
    """The literal reading of one testcase: the `generic` dialect, unchanged."""
    if tc.find("failure") is not None:
        return "failed"
    if tc.find("error") is not None:
        return "error"
    if tc.find("skipped") is not None:
        return "skipped"
    return "passed"


def node_file_case(name: str, test_glob: str) -> bool:
    """Whether node named this testcase after a test file rather than a test."""
    if NODE_TEST_FILE.search(name):
        return True
    return bool(test_glob) and matches(name, [test_glob])


def element_carries(element, markers) -> bool:
    """Whether an element's body text carries one of these markers.

    The body, not the attributes: node's `message` for a failed `assert.equal`
    is the value diff alone, and only the body spells out the assertion's own
    `cause: AssertionError [ERR_ASSERTION]`.
    """
    if element is None:
        return False
    body = "".join(element.itertext())
    return any(marker in body for marker in markers)


def pytest_assertion(element) -> bool:
    """Whether a pytest `<failure>` reports an assertion rather than a throw.

    pytest writes the exception's own name into `message`: an assertion reads
    `AssertionError: ...`, a bare assert with rewriting off reads `assert ...`,
    and `pytest.fail()` reads `Failed: ...`. Anything else — a `NameError`,
    `TypeError` or `ImportError` raised inside the test body — is a throw, and
    a throw is not the failing assertion a red gate requires. A `<failure>`
    carrying no message is read as a throw: the oracle fails closed.
    """
    if element is None:
        return False
    return (element.get("message") or "").lstrip().startswith(PYTEST_ASSERTION_PREFIXES)


def classify(key: str, code: int, results: dict, counts: dict, junit_path) -> str:
    """Map a runner outcome onto the closed classification set."""
    if key != "test":
        return "PASS" if code == 0 else "TEST_FAILURE"
    if counts.get("parse_error"):
        return "COLLECTION_ERROR"
    if junit_path and not results:
        return "NO_TESTS"
    if counts.get("errors"):
        return "COLLECTION_ERROR"
    if any(state == "error" for state in results.values()):
        return "COLLECTION_ERROR"
    if code == 0:
        return "PASS"
    return "TEST_FAILURE"


# ---------- the receipt (D4) ----------

def extract_envelope(raw: str) -> str:
    """Pull the single receipt object out of the worker's final message.

    Tolerant of a code fence and of surrounding prose; strict about there being
    exactly one object that declares the schema key.
    """
    if len(raw.encode()) > MAX_RESULT_BYTES:
        raise Refuse(f"worker result exceeds {MAX_RESULT_BYTES} bytes", REFUSED)
    text = raw.strip()
    text = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", text)
    text = re.sub(r"\s*```$", "", text).strip()
    candidates: list[str] = []
    depth, start, in_string, escape = 0, -1, False, False
    for index, char in enumerate(text):
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            if depth == 0:
                start = index
            depth += 1
        elif char == "}":
            if depth:
                depth -= 1
                if depth == 0 and start >= 0:
                    candidates.append(text[start:index + 1])
    envelopes = [c for c in candidates if '"schema"' in c and RESULT_SCHEMA in c]
    if len(envelopes) == 1:
        return envelopes[0]
    if not envelopes:
        raise Refuse(
            f"worker's final message contains no {RESULT_SCHEMA} object", REFUSED
        )
    raise Refuse(
        f"worker's final message contains {len(envelopes)} {RESULT_SCHEMA} objects; "
        "return exactly one",
        REFUSED,
    )


ARTIFACT_FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.S)
_MISSING = object()


def frontmatter_field(text: str, key: str):
    """One frontmatter value, or None when the text carries no such key."""
    match = ARTIFACT_FRONTMATTER.match(text or "")
    if not match:
        return None
    try:
        header = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None
    return header.get(key) if isinstance(header, dict) else None


def field_update_problems(e: dict, path: str, root: Path) -> list[str]:
    """Validate a `writes: fields` change against the phase's input checkpoint.

    A field-restricted phase does not author an artifact; it fills in keys the
    authoring phase left for it. So the file must already have existed at the
    checkpoint this phase started from, its body must be byte-identical, and its
    frontmatter may differ only in the keys the registry declares for it.
    """
    keys = phase_fields(e)
    target = root / path
    if not target.is_file():
        return [f"{path}: a field-restricted phase may not delete a file"]
    previous = checkpoint_bytes(e, e["candidate"]["checkpoint"], path)
    if previous is None:
        return [f"{path}: a field-restricted phase may only update a file that exists"]
    before = ARTIFACT_FRONTMATTER.match(previous.decode("utf-8", "replace"))
    after = ARTIFACT_FRONTMATTER.match(target.read_text())
    if not before:
        return [f"{path}: the file at the input checkpoint has no parseable YAML frontmatter"]
    if not after:
        return [f"{path}: the updated file has no parseable YAML frontmatter"]
    if after.group(2) != before.group(2):
        return [f"{path}: a field-restricted phase may not change the body"]
    try:
        old = yaml.safe_load(before.group(1))
        new = yaml.safe_load(after.group(1))
    except yaml.YAMLError as exc:
        return [f"{path}: frontmatter is not parseable YAML: {exc}"]
    if not isinstance(old, dict) or not isinstance(new, dict):
        return [f"{path}: frontmatter is not a mapping"]
    changed = sorted(
        key for key in set(old) | set(new)
        if old.get(key, _MISSING) != new.get(key, _MISSING)
    )
    illegal = [key for key in changed if key not in keys]
    if illegal:
        return [f"{path}: keys {illegal} changed; this phase may change only {sorted(keys)}"]
    return []


def parse_receipt(raw: str, e: dict, event_agent: str, agent_id: str) -> dict:
    """Validate the receipt a worker returns at SubagentStop (D4).

    The receipt says what the worker believes it did. It carries no file bodies
    and no digests: the sequencer derives the change set from the checkpoint
    diff and holds the receipt to it.
    """
    try:
        data = json.loads(extract_envelope(raw))
    except json.JSONDecodeError as exc:
        raise Refuse(f"worker receipt is not valid JSON: {exc}", REFUSED) from exc
    if not isinstance(data, dict):
        raise Refuse("worker receipt must be a JSON object", REFUSED)
    unknown = set(data) - RECEIPT_KEYS
    missing = RECEIPT_REQUIRED - set(data)
    if unknown or missing:
        raise Refuse(
            f"worker receipt keys invalid; missing={sorted(missing)}, unknown={sorted(unknown)}",
            REFUSED,
        )
    if data["schema"] != RESULT_SCHEMA:
        raise Refuse(f"worker receipt schema must be {RESULT_SCHEMA!r}", REFUSED)

    actual_agent = canonical_agent(event_agent)
    expected = allowed_agents(e)
    if not actual_agent or actual_agent not in expected:
        raise Refuse(f"phase {e['phase']} accepts {sorted(expected)}, not {event_agent!r}", REFUSED)
    if canonical_agent(str(data["agent"])) != actual_agent:
        raise Refuse("worker receipt agent does not match the SubagentStop agent_type", REFUSED)
    if data["run"] != e["run"] or data["phase"] != e["phase"]:
        raise Refuse(
            f"worker receipt targets {data['run']}/{data['phase']}, "
            f"active state is {e['run']}/{e['phase']}",
            REFUSED,
        )
    if skill_key(str(data["skill"])) != e["skill"]:
        raise Refuse(f"worker receipt skill {data['skill']!r} is not the active {e['skill']!r}",
                     REFUSED)

    candidate = data["candidate"]
    if not isinstance(candidate, dict) or set(candidate) != {"id", "input_checkpoint"}:
        raise Refuse("receipt candidate must be {id, input_checkpoint}", REFUSED)
    if str(candidate["id"]) != e["run"]:
        raise Refuse(
            f"receipt candidate.id {candidate['id']!r} is not this run's candidate {e['run']!r}",
            REFUSED,
        )
    expected_checkpoint = e["candidate"]["checkpoint"]
    if str(candidate["input_checkpoint"]) != expected_checkpoint:
        raise Refuse(
            f"receipt candidate.input_checkpoint {candidate['input_checkpoint']!r} is not the "
            f"checkpoint this phase started from ({expected_checkpoint!r})",
            REFUSED,
        )

    status = data["status"]
    if status not in WORKER_STATUS:
        raise Refuse(f"invalid worker status {status!r}; use {sorted(WORKER_STATUS)}", REFUSED)
    reason_code = data.get("reason_code")
    if status == "could_not_run":
        if reason_code not in REASON_CODES:
            raise Refuse(f"could_not_run needs reason_code in {sorted(REASON_CODES)}", REFUSED)
    elif reason_code is not None:
        raise Refuse("reason_code is only valid with status could_not_run", REFUSED)

    nxt = data.get("next")
    if nxt is not None:
        spec = phase_spec(e["skill"], e["phase"]) or {}
        order = phase_names(e["skill"])
        if status != "fail":
            raise Refuse("next is a rewind request and requires status fail", REFUSED)
        if spec.get("rewind_to") is None:
            raise Refuse(f"phase {e['phase']} may not rewind", REFUSED)
        if nxt != spec["rewind_to"]:
            raise Refuse(
                f"phase {e['phase']} may rewind only to {spec['rewind_to']!r}, not {nxt!r}",
                REFUSED,
            )
        if order.index(nxt) >= order.index(e["phase"]):
            raise Refuse("next must name an earlier phase in the same skill", REFUSED)

    claimed = data["claimed_paths"]
    if not isinstance(claimed, list) or len(claimed) > MAX_CLAIMED_PATHS \
            or not all(isinstance(item, str) and item.strip() for item in claimed):
        raise Refuse(
            f"claimed_paths must be a list of at most {MAX_CLAIMED_PATHS} root-relative paths",
            REFUSED,
        )
    if status != "pass" and claimed:
        raise Refuse("a non-pass receipt claims no paths", REFUSED)
    refs = data.get("evidence_refs", [])
    if not isinstance(refs, list) or len(refs) > MAX_EVIDENCE_REFS \
            or not all(isinstance(item, str) for item in refs):
        raise Refuse(f"evidence_refs must be a list of at most {MAX_EVIDENCE_REFS} paths", REFUSED)
    note = data.get("note", "")
    if not isinstance(note, str) or len(note.encode()) > 16_384:
        raise Refuse("worker receipt note must be a string of at most 16384 bytes", REFUSED)
    findings = validate_findings(e, data)
    issues = data.get("issues", [])
    if not isinstance(issues, list) or len(issues) > MAX_ISSUES:
        raise Refuse(f"issues must be a list of at most {MAX_ISSUES} entries", REFUSED)

    root = candidate_root(e)
    normalized: list[str] = []
    for item in claimed:
        try:
            path = project_relative(root, item)
        except PolicyError as exc:
            raise Refuse(f"claimed path {item!r}: {exc}", REFUSED) from exc
        if path in normalized:
            raise Refuse(f"duplicate claimed path {path}", REFUSED)
        normalized.append(path)

    return {
        "schema": RESULT_SCHEMA,
        "run": e["run"],
        "skill": e["skill"],
        "phase": e["phase"],
        "agent": actual_agent,
        "agent_id": agent_id,
        "status": status,
        "reason_code": reason_code,
        "candidate": {"id": e["run"], "input_checkpoint": expected_checkpoint},
        "claimed_paths": sorted(normalized),
        "evidence_refs": refs,
        "findings": findings,
        "note": note,
        "issues": issues,
        "next": nxt,
        "captured_at": now(),
    }


def validate_findings(e: dict, data: dict) -> str | None:
    """The `findings` rule (D13 item 2), refused by name in each direction.

    A judge phase returns its detailed evidence here because the provider
    refuses a subagent's report-file write before any hook runs. A producer
    returns none: its evidence is the change set the sequencer derives from the
    checkpoint. Nothing is truncated — an oversize body is a receipt defect.
    """
    judge = is_judge(e["skill"], e["phase"])
    present = "findings" in data
    # A judge that reached a verdict must show its work; a judge that could not
    # run, or that needs a human before it can judge, has no verdict to evidence
    # and may leave the field out. `note` still carries why.
    owed = judge and data.get("status") in ("pass", "fail")
    if owed and not present:
        raise Refuse(
            f"MISSING_FINDINGS: phase {e['phase']} is a judge phase and returned "
            f"{data.get('status')!r}; its receipt carries `findings`, the evidence body the "
            f"sequencer persists at {findings_path(e)}. Only `needs_user` and "
            "`could_not_run` may omit it",
            REFUSED,
        )
    if not judge and present:
        raise Refuse(
            f"UNEXPECTED_FINDINGS: phase {e['phase']} writes in the candidate root; its "
            "evidence is the change set, not a `findings` body. Only a judge phase carries "
            "`findings`",
            REFUSED,
        )
    if not present:
        return None
    findings = data["findings"]
    if not isinstance(findings, str) or not findings.strip():
        raise Refuse(
            f"EMPTY_FINDINGS: phase {e['phase']} must return a non-empty `findings` string",
            REFUSED,
        )
    size = len(findings.encode("utf-8"))
    if size > MAX_FINDINGS_BYTES:
        raise Refuse(
            f"OVERSIZE_FINDINGS: `findings` is {size} UTF-8 bytes, over the "
            f"{MAX_FINDINGS_BYTES}-byte limit; the sequencer truncates nothing. Shorten the "
            "body and return the receipt again",
            REFUSED,
        )
    return findings


def persist_findings(e: dict, result: dict) -> str | None:
    """Write a judge's returned `findings` verbatim to its fixed path (D13 item 3).

    Persistence of a returned result, not a merge into the tree: the path lives
    under the run's gitignored work directory in the canonical project, the
    worker cannot choose it, and nothing about the candidate root changes.
    """
    findings = result.get("findings")
    if not findings:
        return None
    relative = findings_path(e)
    target = ROOT / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(findings, encoding="utf-8")
    log("findings.persisted", session_id=e.get("session_id"), run=e["run"],
        phase=e["phase"], path=relative, bytes=len(findings.encode("utf-8")))
    return relative


def persisted_findings(e: dict) -> list[str]:
    """Every findings file this run has persisted, in phase order.

    Derived from the phase results the sequencer already wrote, so the run
    record carries no second copy that could drift from them.
    """
    rows: list[str] = []
    for phase in phase_names(e["skill"]):
        path = work(e["run"]) / f"{phase}-result.json"
        if not path.exists():
            continue
        try:
            reference = (json.loads(path.read_text()) or {}).get("findings_path")
        except (OSError, ValueError):
            continue
        if reference and reference not in rows:
            rows.append(str(reference))
    return rows


def lease_problems(e: dict, result: dict) -> list[str]:
    """A producer's receipt is accepted only from the worker holding the lease."""
    if (phase_spec(e["skill"], e["phase"]) or {}).get("writes", "none") == "none":
        return []
    lease = e.get("lease") or {}
    if not lease:
        return [f"LEASE_HELD: phase {e['phase']} has no lease; the worker was never bound at "
                "SubagentStart, so its writes were never admitted"]
    if lease.get("agent_id") and result.get("agent_id") \
            and lease["agent_id"] != result["agent_id"]:
        return [f"LEASE_HELD: the lease for phase {e['phase']} belongs to "
                f"{lease.get('agent')}/{lease.get('agent_id')}, not to "
                f"{result['agent']}/{result['agent_id']}"]
    return []


def change_problems(e: dict, changed: list[dict], claimed: list[str], root: Path) -> list[str]:
    """Hold the receipt to the change set the checkpoint diff derived."""
    problems: list[str] = []
    claimed_set = set(claimed)
    unclaimed = [row["path"] for row in changed if row["path"] not in claimed_set]
    if unclaimed:
        problems.append(
            "UNCLAIMED_CHANGE: the candidate changed paths the receipt does not claim: "
            + ", ".join(sorted(unclaimed))
        )
    for row in changed:
        try:
            validate_phase_write_path(root, e, row["path"])
        except PolicyError as exc:
            problems.append(str(exc))
    return problems


def artifact_problems(e: dict, changed: list[dict], root: Path) -> list[str]:
    """Contract checks for the artifacts a phase may write inside the root.

    A producer exception admits a sequencer-owned path to one phase's fence;
    the artifact's own contract decides whether the change may be checkpointed.
    """
    problems: list[str] = []
    stack = stack_section(e) or {}
    writes_mode = (phase_spec(e["skill"], e["phase"]) or {}).get("writes", "none")
    for row in changed:
        path, kind = row["path"], row["kind"]
        if kind != "deleted" and stack:
            try:
                text = (root / path).read_text(errors="replace")
            except OSError:
                text = ""
            problems += techstack_text_problems(path, text, stack)
        if path == STACK_PATH:
            if kind == "deleted":
                problems.append(f"{STACK_PATH} may be written, never deleted")
            else:
                rows = stack_proposal_problems((root / path).read_text())
                if rows:
                    problems.append(
                        "proposed stack.yaml does not satisfy stack.schema.json:\n  "
                        + "\n  ".join(rows))
        if path.startswith(ADR_PREFIX):
            if kind == "deleted":
                problems.append("an ADR may be written, never deleted")
            elif kind == "modified":
                problems.append(
                    f"{path} already existed at the input checkpoint; an ADR is append-only, "
                    "so record the reversal as a new ADR whose supersedes names this one"
                )
            else:
                rows = adr_proposal_problems(path, (root / path).read_text())
                if rows:
                    problems.append(
                        "proposed ADR does not satisfy the adr template header:\n  "
                        + "\n  ".join(rows))
        if writes_mode == "fields":
            problems += field_update_problems(e, path, root)
    return problems


def receipt_verdict(e: dict, result: dict, root: Path) -> tuple[str | None, list[str]]:
    """The report verdict a report-producing phase carries (D10 rule 4).

    The verdict lives in the report the receipt points at, not in the envelope:
    `review`, `qa` and `skill-validator` write one report and its frontmatter
    `verdict` selects the handoff row. The run's status is untouched, because
    reporting a defect is a passing run.
    """
    if (e["skill"], e["phase"]) not in VERDICT_PHASES or result["status"] != "pass":
        return None, []
    for ref in result.get("evidence_refs") or []:
        candidate = root / ref
        if not candidate.is_file() or candidate.suffix != ".md":
            continue
        declared = frontmatter_field(candidate.read_text(errors="replace"), "verdict")
        if declared is None:
            continue
        if str(declared) not in REPORT_VERDICTS:
            return None, [
                f"invalid verdict {declared!r} in {ref}; use {sorted(REPORT_VERDICTS)}"
            ]
        return str(declared), []
    return None, [
        f"phase {e['phase']} produces a report whose frontmatter states a verdict in "
        f"{sorted(REPORT_VERDICTS)}; name that report in evidence_refs"
    ]


def write_json_atomic(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, path)


def write_phase_report(e: dict, result: dict, problems: list[str] | None = None) -> Path:
    path = work(e["run"]) / f"{e['phase']}-report.md"
    lines = [
        f"# {e['skill']} / {e['phase']} — {result['status']}",
        "",
        f"- run: {e['run']}",
        f"- candidate: {(e.get('candidate') or {}).get('mode')} at "
        f"{(e.get('candidate') or {}).get('root')}",
        f"- input checkpoint: {(e.get('candidate') or {}).get('checkpoint')}",
        f"- agent: {result['agent']} ({result.get('agent_id') or 'no agent_id'})",
        f"- session: {result.get('session_id') or 'unknown'}",
        f"- at: {result.get('captured_at') or now()}",
    ]
    if result.get("reason_code"):
        lines.append(f"- reason_code: {result['reason_code']}")
    if result.get("next"):
        lines.append(f"- rewind requested to: {result['next']}")
    for substitution in result.get("digests_resolved") or []:
        lines.append(f"- digest resolved: {substitution}")
    lines += ["", "## Note", "", result.get("note") or "(none)", ""]
    if result.get("issues"):
        lines += ["## Issues", ""] + [f"- {issue}" for issue in result["issues"]] + [""]
    if result.get("changed"):
        lines += ["## Changed in the candidate", ""]
        lines += [f"- {row['kind']}: {row['path']}" for row in result["changed"]] + [""]
    if result.get("findings_path"):
        lines += ["## Findings", "",
                  f"- persisted verbatim at {result['findings_path']}", ""]
    if result.get("evidence_refs"):
        lines += ["## Evidence", ""] + [f"- {ref}" for ref in result["evidence_refs"]] + [""]
    if problems:
        lines += ["## Oracle problems", ""] + [f"- {p}" for p in problems] + [""]
    path.write_text("\n".join(lines))
    return path


# ---------- transition oracles ----------

def invariant_problems(e: dict) -> list[str]:
    """Checks no receipt and no PostToolUse event can waive.

    The fence is checked against the candidate's own change set, and the
    tech-stack policy against the candidate tree, because that tree is what a
    promotion would put into the canonical checkout.
    """
    root = candidate_root(e)
    problems = [
        f"file outside fence changed: {row['path']}"
        for row in candidate_changes(e)
        if not in_fence(row["path"], e["write_fence"])
    ]
    try:
        stack = stack_section(e)
        if stack:
            problems += [
                "techstack violation: " + problem
                for problem in techstack_tree_problems(root, stack)
            ]
    except (OSError, PolicyError, yaml.YAMLError) as exc:
        problems.append(f"techstack policy could not be evaluated: {exc}")
    return problems


def candidate_hashes(e: dict) -> dict[str, str]:
    """Every path's digest inside the candidate root, for the test freeze."""
    root = candidate_root(e)
    return {
        rel: sha(root / rel)
        for rel in manifest_paths(root, candidate_ignore(e))
    }


def compiled_build(e: dict) -> list[str]:
    stack = stack_section(e)
    if not stack or stack.get("compiled") is not True:
        return []
    if "build" not in ((e.get("commands") or {}).get("use") or []):
        return ["compiled stack section requires the run to authorise the build key"]
    outcome = run_key(e, "build")
    if outcome["classification"] in ("INFRA_FAILURE", "TIMEOUT"):
        return ["COULD_NOT_RUN: " + outcome["output"].strip().splitlines()[-1]]
    if outcome["exit"] != 0:
        return ["build failed:\n" + outcome["output"][-800:]]
    return []


def check_red(e: dict) -> list[str]:
    """Every test_plan test exists and fails on an assertion; nothing else moved."""
    problems = invariant_problems(e)
    problems += compiled_build(e)
    if any(p.startswith("COULD_NOT_RUN") for p in problems):
        return problems
    outcome = run_key(e, "test")
    e["last_oracle"] = {k: outcome[k] for k in ("key", "classification", "exit")}
    if outcome["classification"] in ("INFRA_FAILURE", "TIMEOUT"):
        return ["COULD_NOT_RUN: " + outcome["output"].strip().splitlines()[-1]]
    if outcome["classification"] == "NO_TESTS":
        return ["NO_TESTS: the test command collected nothing; red must produce failing tests"]
    if outcome["classification"] == "COLLECTION_ERROR":
        return ["COLLECTION_ERROR: tests must fail on an assertion, not on import or collection"]
    if outcome["exit"] == 0:
        problems.append("test command exited 0; red must be red")
    results = outcome["junit"]
    for row in e["test_plan"]:
        st = results.get(row["name"])
        if st is None:
            problems.append(
                f"criterion {row['criterion']}: test {row['name']} not found in {row['file']}"
            )
        elif st == "error":
            problems.append(
                f"criterion {row['criterion']}: {row['name']} errored (import/collection); "
                "it must fail on an assertion"
            )
        elif st != "failed":
            problems.append(f"criterion {row['criterion']}: {row['name']} is {st}, expected failed")
    extra = set(results) - {r["name"] for r in e["test_plan"]}
    if extra:
        problems.append(f"tests outside test_plan: {sorted(extra)}")
    if not problems:
        e["last_oracle"]["classification"] = "EXPECTED_TEST_FAILURE"
    hashes = candidate_hashes(e)
    e["red_hashes"] = {t: hashes.get(t) for t in e["test_paths"]}
    return problems


def check_green(e: dict, phase: str) -> list[str]:
    """Tests pass, tests unchanged since red, fence and stack policy hold."""
    problems = invariant_problems(e)
    hashes = candidate_hashes(e)
    for t, h in (e.get("red_hashes") or {}).items():
        if hashes.get(t) != h:
            problems.append(f"test file changed since red: {t}")
    problems += compiled_build(e)
    if any(p.startswith("COULD_NOT_RUN") for p in problems):
        return problems
    outcome = run_key(e, "test")
    e["last_oracle"] = {k: outcome[k] for k in ("key", "classification", "exit")}
    if outcome["classification"] in ("INFRA_FAILURE", "TIMEOUT"):
        return ["COULD_NOT_RUN: " + outcome["output"].strip().splitlines()[-1]]
    if outcome["classification"] == "COLLECTION_ERROR":
        problems.append("COLLECTION_ERROR: the suite did not collect cleanly")
    if outcome["classification"] == "NO_TESTS":
        problems.append("NO_TESTS: the test command collected nothing")
    if outcome["classification"] == "TEST_FAILURE":
        # A run with no test_plan rows (a story-anchored qa run) would otherwise
        # advance on a red suite, because there is no row to report as failing.
        problems.append(f"TEST_FAILURE: the test command exited {outcome['exit']}")
    for row in e.get("test_plan") or []:
        if outcome["junit"].get(row["name"]) != "passed":
            problems.append(
                f"criterion {row['criterion']}: {row['name']} is {outcome['junit'].get(row['name'])}"
            )
    if phase == "refactor" and "lint" in ((e.get("commands") or {}).get("use") or []):
        lint = run_key(e, "lint")
        if lint["classification"] in ("INFRA_FAILURE", "TIMEOUT"):
            problems.append("COULD_NOT_RUN: " + lint["output"].strip().splitlines()[-1])
        elif lint["exit"] != 0:
            problems.append("lint failed:\n" + lint["output"][-800:])
    return problems


def check_document(e: dict, result: dict) -> list[str]:
    """Document phases: fence held, and every declared output is in the root."""
    problems = invariant_problems(e)
    root = candidate_root(e)
    spec = phase_spec(e["skill"], e["phase"]) or {}
    if spec.get("writes") == "docs" and not result.get("changed"):
        if not spec.get("conditional"):
            problems.append(f"phase {e['phase']} produced no document inside {e['write_fence']}")
        elif not (result.get("note") or "").strip():
            # A conditional phase may owe nothing, but "nothing was owed" is a
            # finding the run records, not a silence the oracle infers.
            problems.append(
                f"phase {e['phase']} is conditional and produced no document; the receipt "
                "must say in its note why none was owed"
            )
    for row in result.get("changed") or []:
        if row["kind"] != "deleted" and not (root / row["path"]).exists():
            problems.append(f"declared output {row['path']} is not in the candidate root")
    return problems


def run_oracle(e: dict, result: dict) -> list[str]:
    kind = (phase_spec(e["skill"], e["phase"]) or {}).get("oracle", "report_only")
    if kind == "red":
        return check_red(e)
    if kind in ("green", "refactor"):
        return check_green(e, e["phase"])
    if kind == "document":
        return check_document(e, result)
    return invariant_problems(e)


# ---------- provenance re-resolution (01-skill-anatomy.md hash rule) ----------

PLACEHOLDER_HASH = re.compile(r"(?i)^sha256:(fixture|pending)")
CANONICAL_HASH = re.compile(r"^sha256:[0-9a-f]{64}$")
LINE_ANCHOR = re.compile(r"^L(\d+)-L(\d+)$")


def heading_slug(heading: str) -> str:
    """GitHub-style slug: lowercase, non-alphanumerics collapsed to hyphens."""
    return re.sub(r"[^a-z0-9]+", "-", heading.strip().lower()).strip("-")


CODE_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")


def fenced_lines(lines: list[str]) -> list[bool]:
    """True for every line inside a fenced code block, fence lines included.

    A fence opens on ``` or ~~~ (at most three leading spaces, an optional info
    string) and closes on a run of the same character, at least as long, with
    nothing after it. An unclosed fence runs to the end of the file.
    """
    inside = [False] * len(lines)
    marker: str | None = None
    for index, line in enumerate(lines):
        found = CODE_FENCE.match(line)
        if marker is None:
            if found:
                marker, inside[index] = found.group(1), True
            continue
        inside[index] = True
        if found and found.group(1)[0] == marker[0] \
                and len(found.group(1)) >= len(marker) and not found.group(2).strip():
            marker = None
    return inside


def section_bytes(path: Path, anchor: str | None) -> bytes | None:
    """The exact bytes `01-skill-anatomy.md` hashes for `path#anchor`.

    A heading anchor runs from its heading line to the next heading of the same
    or higher level; `#L10-L20` is that inclusive line range; no anchor is the
    whole file. A `#` line inside a fenced code block is sample text, not a
    heading: it neither opens nor ends a section. CRLF becomes LF, lines are
    joined with LF, and one trailing LF is appended. This is byte-for-byte the
    rule `docs/design/specs/verify.py` applies to every `depends_on`, so a gate
    digest and a V3 digest agree.
    """
    lines = path.read_text(encoding="utf-8").replace("\r\n", "\n").split("\n")
    if anchor is None:
        return ("\n".join(lines) + "\n").encode("utf-8")
    span = LINE_ANCHOR.fullmatch(anchor)
    if span:
        first, last = int(span.group(1)), int(span.group(2))
        if first < 1 or last < first or first > len(lines):
            return None
        return ("\n".join(lines[first - 1:last]) + "\n").encode("utf-8")
    fenced = fenced_lines(lines)
    start = level = None
    for index, line in enumerate(lines):
        heading = re.match(r"^(#{1,6})\s+(.*)", line)
        if heading and not fenced[index] and heading_slug(heading.group(2)) == anchor:
            start, level = index, len(heading.group(1))
            break
    if start is None:
        return None
    end = len(lines)
    for index in range(start + 1, len(lines)):
        heading = re.match(r"^(#{1,6})\s", lines[index])
        if heading and not fenced[index] and len(heading.group(1)) <= level:
            end = index
            break
    return ("\n".join(lines[start:end]) + "\n").encode("utf-8")


def resolve_reference(source: str, recorded: str) -> tuple[str, str]:
    """Re-resolve one `provenance[]` or `context[]` entry.

    Returns `("ok", detail)`, `("unresolvable-source", detail)` — the source or
    the anchor cannot be resolved, or the hash is a placeholder — or
    `("stale-hash", detail)` when the source resolves and the digest differs.
    """
    if not source:
        return "unresolvable-source", "entry has no source"
    path_part, sep, anchor = source.partition("#")
    if not recorded:
        return "unresolvable-source", f"{source}: no hash recorded"
    if PLACEHOLDER_HASH.match(recorded):
        return "unresolvable-source", f"{source}: placeholder hash {recorded}"
    if not CANONICAL_HASH.match(recorded):
        return "unresolvable-source", f"{source}: hash {recorded!r} is not sha256:<64 hex>"
    try:
        relative = project_relative(ROOT, path_part)
    except PolicyError as exc:
        return "unresolvable-source", f"{source}: {exc}"
    target = ROOT / relative
    if not target.is_file():
        return "unresolvable-source", f"{source}: source file does not exist"
    try:
        data = section_bytes(target, anchor if sep else None)
    except (OSError, UnicodeDecodeError) as exc:
        return "unresolvable-source", f"{source}: cannot read source ({exc})"
    if data is None:
        return "unresolvable-source", f"{source}: anchor #{anchor} does not resolve"
    actual = "sha256:" + hashlib.sha256(data).hexdigest()
    if actual != recorded:
        return "stale-hash", f"{source}: recorded {recorded[:19]}…, current {actual[:19]}…"
    return "ok", source


# ---------- sha256:PENDING resolution (10 section 5.2, step 13a) ----------

PENDING_HASH = re.compile(r"(?i)^sha256:pending$")
FRONTMATTER = re.compile(r"^---\n(.*?\n)---\n", re.S)
FM_TOP_KEY = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):")
FM_SOURCE = re.compile(r"^(\s*(?:-\s+)?)source:\s*(\S+)\s*$")
FM_HASH = re.compile(r"^(\s*(?:-\s+)?)hash:\s*(\S+)\s*$")


def pending_digest(root: Path, path: str, source: str, whole_file: bool) -> str:
    """The digest a `sha256:PENDING` entry stands for, or refuse the receipt."""
    if not source:
        raise Refuse(
            f"{path}: a sha256:PENDING hash has no preceding source to resolve", REFUSED
        )
    path_part, sep, anchor = source.partition("#")
    try:
        relative = project_relative(root, path_part)
    except PolicyError as exc:
        raise Refuse(f"{path}: sha256:PENDING source {source}: {exc}", REFUSED) from exc
    target = root / relative
    if not target.is_file():
        raise Refuse(
            f"{path}: sha256:PENDING source {source} does not resolve: no such file", REFUSED
        )
    if whole_file:
        return sha(target)
    try:
        data = section_bytes(target, anchor if sep else None)
    except (OSError, UnicodeDecodeError) as exc:
        raise Refuse(
            f"{path}: sha256:PENDING source {source} cannot be read ({exc})", REFUSED
        ) from exc
    if data is None:
        raise Refuse(
            f"{path}: sha256:PENDING source {source} does not resolve: anchor #{anchor} "
            "is not a heading in that file",
            REFUSED,
        )
    return "sha256:" + hashlib.sha256(data).hexdigest()


def resolve_pending_digests(e: dict, changed: list[dict], root: Path) -> list[str]:
    """Substitute every `sha256:PENDING` digest a written artifact carries.

    A worker cannot hash a file it is still writing, so `plan`'s `story_writer`
    writes `sha256:PENDING` for each `provenance[]`, `context[]` and
    `commands.hash` entry. The sequencer resolves them inside the candidate root
    before it derives the change set, under exactly the rule the gate
    re-resolves with: section bytes for a `provenance[]` or `context[]` entry,
    the whole file for `commands.hash`, which pins all of `stack.yaml`. Without
    this the dev gate refuses every plan-written story as a placeholder hash.

    The substitution is textual and byte-local: only a frontmatter `hash:` line
    whose value is exactly `sha256:PENDING` changes, resolved from the nearest
    preceding `source:` line. `sha256:FIXTURE` is a fixture marker, not a
    request, and is left alone. A source that does not resolve inside the root
    refuses the receipt, and the phase does not checkpoint.
    """
    substitutions: list[str] = []
    for row in changed:
        path = row["path"]
        if row["kind"] == "deleted" or not path.endswith(".md"):
            continue
        content = (root / path).read_text()
        match = FRONTMATTER.match(content)
        if not match:
            continue
        lines = match.group(1).split("\n")
        top, source = "", ""
        for index, line in enumerate(lines):
            key = FM_TOP_KEY.match(line)
            if key:
                top = key.group(1)
            found = FM_SOURCE.match(line)
            if found:
                source = found.group(2)
                continue
            found = FM_HASH.match(line)
            if not found or not PENDING_HASH.match(found.group(2)):
                continue
            digest = pending_digest(root, path, source, whole_file=(top == "commands"))
            lines[index] = f"{found.group(1)}hash: {digest}"
            substitutions.append(f"{path}: {source} -> {digest}")
        if substitutions:
            (root / path).write_text(
                "---\n" + "\n".join(lines) + "---\n" + content[match.end():])
    return substitutions


# ---------- stack.yaml proposals ----------

STACK_PATH = ".devforgeai/stack.yaml"
STACK_ANCHOR = re.compile(r"^[a-z][a-z0-9-]*$")


def stack_schema() -> dict:
    """`schemas/devforgeai/v1/stack.schema.json`, found by walking upward."""
    relative = Path("schemas") / "devforgeai" / "v1" / "stack.schema.json"
    here = Path(__file__).resolve()
    for base in (here.parent, *here.parents, ROOT):
        candidate = base / relative
        if candidate.is_file():
            return json.loads(candidate.read_text())
    raise Refuse(
        f"cannot locate {relative.as_posix()}; a {STACK_PATH} proposal is refused "
        "rather than applied unvalidated",
        REFUSED,
    )


def stack_proposal_problems(text: str) -> list[str]:
    """Validate a proposed `.devforgeai/stack.yaml` before it is applied.

    Every section must satisfy `stack.schema.json` and the same contract checks
    the gate applies to the section a story anchors, so the file the sequencer
    later resolves commands from cannot be malformed.
    """
    try:
        from jsonschema import Draft202012Validator
    except ImportError:  # fail closed: an unvalidated stack policy is refused
        return ["jsonschema is not installed; a stack.yaml proposal cannot be validated"]
    try:
        doc = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        return [f"{STACK_PATH} is not parseable YAML: {exc}"]
    if not isinstance(doc, dict) or not doc:
        return [f"{STACK_PATH} must be a non-empty mapping of anchor name to section"]
    validator = Draft202012Validator(stack_schema())
    problems: list[str] = []
    for anchor in sorted(doc):
        if not STACK_ANCHOR.match(str(anchor)):
            problems.append(f"{STACK_PATH}: anchor {anchor!r} is not [a-z][a-z0-9-]*")
        section = doc[anchor]
        if not isinstance(section, dict):
            problems.append(f"{STACK_PATH}#{anchor} is not a mapping")
            continue
        for error in sorted(validator.iter_errors(section), key=lambda e: list(e.path)):
            location = "/".join(str(p) for p in error.path) or "(section)"
            problems.append(f"{STACK_PATH}#{anchor} {location}: {error.message}")
        problems += [
            f"{STACK_PATH}#{anchor}: {problem}"
            for problem in stack_problems(section, (section.get("commands") or {}).keys())
        ]
    return problems


# ---------- ADR proposals ----------

ADR_PREFIX = ".devforgeai/provenance/adr/"
ADR_FILENAME = re.compile(r"^([0-9]{4})-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
ADR_TEMPLATE = Path(".devforgeai") / "skills" / "architect" / "templates" / "adr.md"
DESIGN_ADR_TEMPLATE = Path("docs") / "design" / "templates" / "adr.md"


def adr_template_header() -> dict:
    """The `adr` template header, the same way `stack_schema()` finds its schema.

    In an installed project the template is `architect`'s, at
    `.devforgeai/skills/architect/templates/adr.md` (11-artifact-registry.md
    section 1). In this checkout the design-time template stands in for it. The
    header block above the instance frontmatter is the contract: the required
    frontmatter keys, the required sections, the id pattern, and the text no
    instance may carry.
    """
    here = Path(__file__).resolve()
    candidates = [ROOT / ADR_TEMPLATE]
    candidates += [base / DESIGN_ADR_TEMPLATE for base in (here.parent, *here.parents)]
    for candidate in candidates:
        if candidate.is_file():
            match = re.match(r"^---\n(.*?)\n---\n", candidate.read_text(), re.S)
            if not match:
                continue
            header = yaml.safe_load(match.group(1))
            if isinstance(header, dict) and header.get("template") == "adr":
                return header
    raise Refuse(
        f"cannot locate the adr template ({ADR_TEMPLATE.as_posix()}); an ADR "
        "proposal is refused rather than applied unvalidated",
        REFUSED,
    )


def adr_proposal_problems(path: str, text: str) -> list[str]:
    """Validate a proposed ADR against the `adr` template header before it lands.

    `.devforgeai/provenance/adr/**` is admitted to one phase's fence by a
    producer exception, so this is the only check standing between a worker's
    text and the directory `analyze`, `review`, `retro` and `drift` read.
    """
    header = adr_template_header()
    problems: list[str] = []

    name = path[len(ADR_PREFIX):]
    filename = ADR_FILENAME.match(name)
    if not filename:
        problems.append(
            f"{path} is not .devforgeai/provenance/adr/NNNN-<slug>.md with a lowercase slug"
        )

    match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not match:
        return problems + [f"{path} has no parseable YAML frontmatter"]
    try:
        fm = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        return problems + [f"{path} frontmatter is not parseable YAML: {exc}"]
    if not isinstance(fm, dict):
        return problems + [f"{path} frontmatter is not a mapping"]
    body = match.group(2)

    for key in header.get("required_frontmatter") or []:
        if key not in fm:
            problems.append(f"{path} frontmatter is missing required key {key!r}")

    identifier = str(fm.get("id", ""))
    pattern = str(header.get("id_pattern") or "")
    if pattern and not re.match(pattern, identifier):
        problems.append(f"{path} id {identifier!r} does not match {pattern}")
    elif filename and identifier != f"ADR-{filename.group(1)}":
        problems.append(
            f"{path} id {identifier!r} does not match its filename number {filename.group(1)}"
        )

    if fm.get("template") != header.get("template"):
        problems.append(f"{path} template must be {header.get('template')!r}")
    accepts = header.get("accepts_versions") or [header.get("template_version")]
    if fm.get("template_version") not in accepts:
        problems.append(f"{path} template_version must be one of {accepts}")

    lines = {line.rstrip() for line in body.splitlines()}
    for section in header.get("required_sections") or []:
        if section not in lines:
            problems.append(f"{path} is missing required section {section!r}")

    for forbidden in header.get("forbidden_text") or []:
        if str(forbidden) in text:
            problems.append(f"{path} carries forbidden template text {forbidden!r}")
    return problems


# ---------- gates ----------

def locate_story(story: str) -> Path:
    """`docs/plan/*/stories/<id>.md` when it exists, else `<id>.md` at the root."""
    planned = next(iter((ROOT / "docs" / "plan").glob(f"*/stories/{story}.md")), None)
    return planned or (ROOT / f"{story}.md")


def planned_story(path: Path) -> bool:
    """True when the story lives under `docs/plan/`, i.e. a real project story."""
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix().startswith("docs/plan/")
    except ValueError:
        return False


def reference_rows(fm: dict) -> list[tuple[str, str, str]]:
    """Every `provenance[]` and `context[]` entry, as (kind, source, hash)."""
    rows: list[tuple[str, str, str]] = []
    for kind in ("provenance", "context"):
        entries = fm.get(kind) or []
        if not isinstance(entries, list):
            rows.append((kind, "", ""))
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                rows.append((kind, "", ""))
                continue
            rows.append((kind, str(entry.get("source") or ""), str(entry.get("hash") or "")))
    return rows


def story_gate(state: dict, story: str, lenient: bool = False) -> tuple[dict, list[str], list[str]]:
    """Deterministic story v3 gate, inlined at `phase start` (decision 7).

    Returns the frontmatter, the defect list, and the downgraded-defect list.
    `lenient` downgrades `unresolvable-source` and nothing else, and is legal
    only for a stand-alone story outside `docs/plan/`.
    """
    sp = locate_story(story)
    if not sp.exists():
        raise Refuse(f"{story}.md not found")
    if lenient and planned_story(sp):
        raise Refuse(
            f"--lenient is refused: {sp.relative_to(ROOT).as_posix()} is a planned story. "
            "Every story under docs/plan/ re-resolves its sources at the gate.",
            REFUSED,
        )
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", sp.read_text(), re.S)
    if not m:
        raise Refuse("story does not have parseable YAML frontmatter", USAGE)
    fm, body = yaml.safe_load(m.group(1)) or {}, m.group(2)
    problems: list[str] = []
    warnings: list[str] = []

    # `unresolvable_source` is the one defect class a story may loosen, and only
    # when its scope is `hotfix` (03-brownfield.md's reduced provenance). The
    # `--lenient` flag is the implementation of rule 6 in
    # `01-skill-anatomy.md#context-bundle-format`: a stand-alone story has no
    # project document set to resolve against.
    declared = str((fm.get("gate_policy") or {}).get("unresolvable_source", "BLOCK"))
    scope = str(fm.get("scope") or "")
    if declared in ("WARN", "OFF") and scope != "hotfix":
        problems.append(
            f"gate_policy.unresolvable_source is {declared}; that is legal only for scope: hotfix, "
            f"not scope: {scope or '(unset)'}"
        )
    unresolvable_action = declared if (declared in GATE_POLICIES and scope == "hotfix") else "BLOCK"
    if lenient:
        unresolvable_action = "WARN"

    def record(verdict: str, detail: str) -> None:
        if verdict == "stale-hash":
            problems.append(f"stale-hash: {detail}")
        elif verdict == "unresolvable-source":
            row = f"unresolvable-source: {detail}"
            (warnings if unresolvable_action in ("WARN", "OFF") else problems).append(row)

    for kind, source, recorded in reference_rows(fm):
        if not source and not recorded:
            problems.append(f"{kind} entry is not a mapping with a source and a hash")
            continue
        record(*resolve_reference(source, recorded))

    if fm.get("template_version") != 3:
        problems.append(f"story template_version is {fm.get('template_version')}, accepts_versions: [3]")
    if fm.get("status") != "ready":
        problems.append(f"story status is {fm.get('status')}, not ready")
    if "ASSUMPTION:" in body.split("## Clarifications")[0]:
        problems.append("unresolved ASSUMPTION in story body")
    for blocker in fm.get("blocked_by") or []:
        if (state.get("stories", {}).get(str(blocker), {}) or {}).get("status") != "done":
            problems.append(f"blocked_by {blocker} is not done")
    for key in ("write_fence", "test_plan", "commands"):
        if not fm.get(key):
            problems.append(f"story lacks {key}")
    for policy in (fm.get("gate_policy") or {}).values():
        if policy not in GATE_POLICIES:
            problems.append(f"gate_policy value {policy!r} is not in {sorted(GATE_POLICIES)}")
    for row in fm.get("test_plan") or []:
        if not isinstance(row, dict) or not row.get("file") or not row.get("name") \
                or row.get("criterion") is None:
            problems.append("each test_plan row needs criterion, file and name")
        elif not matches(row["file"], fm.get("write_fence") or []):
            problems.append(f"test_plan file {row['file']} is not in write_fence")
    for path in fm.get("write_fence") or []:
        if matches(str(path), ALWAYS_DENY):
            problems.append(f"write_fence entry {path} is sequencer-owned")

    commands = fm.get("commands") or {}
    source = commands.get("source") or ""
    src, _, anchor = source.partition("#")
    stack = None
    if not src:
        # Never downgradable: a run with no stack section can broker nothing,
        # and the run record would carry an unusable commands mapping.
        problems.append("commands.source is empty")
    elif not (ROOT / src).exists():
        problems.append(f"commands.source {src} does not exist")
    else:
        # `commands` pins the whole stack.yaml by digest, not one anchored
        # section: the story names the anchor separately (10 section 7).
        expected_hash = str(commands.get("hash") or "")
        if not expected_hash:
            record("unresolvable-source", "commands.hash is empty")
        elif PLACEHOLDER_HASH.match(expected_hash) or not CANONICAL_HASH.match(expected_hash):
            record("unresolvable-source",
                   f"commands.hash {expected_hash or '(empty)'} is a placeholder")
        elif sha(ROOT / src) != expected_hash:
            record("stale-hash", f"{src}: commands.hash differs from the current file digest")
        try:
            stack_doc = yaml.safe_load((ROOT / src).read_text()) or {}
            stack = stack_doc.get(anchor) if anchor else stack_doc
            if not isinstance(stack, dict):
                problems.append(f"stack.yaml has no section {anchor!r}")
                stack = None
        except (OSError, yaml.YAMLError) as exc:
            problems.append(f"stack.yaml cannot be parsed: {exc}")
    if stack is not None:
        problems += stack_problems(stack, commands.get("use") or [])
        try:
            problems += [
                "existing techstack violation: " + problem
                for problem in techstack_tree_problems(ROOT, stack)
            ]
        except PolicyError as exc:
            problems.append(f"techstack policy cannot be evaluated: {exc}")
    return fm, problems, warnings


def document_gate(skill: str, arg: str) -> tuple[list[str], list[str]]:
    """Deterministic gate for a document-producing skill: the output fence."""
    fence = document_fence(skill, arg)
    problems: list[str] = []
    if not fence:
        problems.append(f"skill {skill} declares no document fence")
    for pattern in fence:
        if matches(pattern, ALWAYS_DENY) and not skill_produces(pattern, skill):
            problems.append(f"document fence entry {pattern} is sequencer-owned")
        if pattern.startswith("/") or ".." in pattern:
            problems.append(f"document fence entry {pattern} is not repository-relative")
    return fence, problems


# ---------- Slice: the context bundle, resolved at the gate ----------

def relative_or_raw(path: Path) -> str:
    """The project-relative form of `path`, or its raw text when it escapes."""
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def context_rows(fm: dict) -> list[dict]:
    """The incoming artifact's `context[]` bundle, re-resolved, entry by entry.

    The excerpt, anchor and digest are the author's; the verdict is this run's.
    Nothing is summarised and nothing is re-excerpted: an entry whose source
    moved is carried with `unresolvable-source` or `stale-hash` so the worker
    reads the row and its detail rather than a silently rewritten excerpt.
    """
    rows: list[dict] = []
    for entry in fm.get("context") or []:
        if not isinstance(entry, dict):
            rows.append({"source": "", "hash": "", "excerpt": "",
                         "verdict": "unresolvable-source",
                         "detail": "context entry is not a mapping"})
            continue
        source = str(entry.get("source") or "")
        recorded = str(entry.get("hash") or "")
        verdict, detail = resolve_reference(source, recorded)
        row = {
            "source": source,
            "hash": recorded,
            "excerpt": str(entry.get("excerpt") or ""),
            "verdict": verdict,
            "detail": detail,
        }
        if entry.get("status"):
            row["status"] = str(entry["status"])
        rows.append(row)
    return rows


def write_context(e: dict, fm: dict | None, source: str | None,
                  lenient: bool = False) -> Path:
    """Sub-phase 1, Slice, performed by the sequencer at `phase start`.

    No registry phase dispatches a curator. The incoming artifact of a story run
    (and of a story-anchored `qa` or `review` run) already carries a hashed
    `context[]` bundle, so the gate that just re-resolved every entry writes it
    to `.devforgeai/work/<run>/context.json` and each worker is given that path.
    A document run whose gate identifies no incoming artifact has no bundle to
    resolve; the file is still written, and records the no-op.
    """
    path = work(e["run"]) / "context.json"
    if fm is None:
        doc = {
            "run": e["run"], "skill": e["skill"], "arg": e["arg"], "phase": e["phase"],
            "slice": "none", "incoming": None, "incoming_sha256": None,
            "lenient": bool(lenient), "entries": [],
            "note": "the document gate identifies no incoming artifact, so this run has "
                    "no context bundle to resolve; each phase worker reads the paths its "
                    "own phase names",
            "resolved_at": now(),
        }
    else:
        rows = context_rows(fm)
        downgraded = [r for r in rows if r["verdict"] != "ok"]
        doc = {
            "run": e["run"], "skill": e["skill"], "arg": e["arg"], "phase": e["phase"],
            "slice": "bundle", "incoming": source,
            # The bytes the workers were given, so a resume can tell whether the
            # story moved under this run (a `/clarify` between the two).
            "incoming_sha256": sha(ROOT / source) if source and (ROOT / source).is_file()
            else None,
            # The gate that produced this slice: a resume repeats it rather than
            # refusing work the original `phase start` was allowed to open.
            "lenient": bool(lenient),
            "entries": rows,
            "note": f"{len(rows)} context entries re-resolved at the gate; "
                    f"{len(downgraded)} did not resolve to their recorded digest",
            "resolved_at": now(),
        }
    write_json_atomic(path, doc)
    return path


def context_path(run: str) -> str:
    """The path every worker of this run is given for its slice."""
    return f".devforgeai/work/{run}/context.json"


# ---------- commands ----------

def stack_ignore_dirs(e: dict) -> list[str]:
    """`stack.yaml#ignore_dirs`: directories a copy-mode candidate leaves behind."""
    try:
        stack = stack_section(e) or {}
    except SystemExit:
        return []
    dirs = stack.get("ignore_dirs") or []
    return [str(d) for d in dirs if isinstance(d, (str, int))]


def fence_conflicts(state: dict, run: str, skill: str, fence: list[str]) -> list[str]:
    """Every live run whose fence this one would overlap (D3)."""
    conflicts = []
    mine = effective_fence(skill, fence)
    for other in live_runs(state):
        if other == run:
            continue
        try:
            record = load_run(other)
        except SystemExit:
            continue
        theirs = effective_fence(record.get("skill", ""), record.get("write_fence") or [])
        shared = fence_overlap(mine, theirs)
        if shared:
            conflicts.append(f"{other} ({record.get('status', 'live')}): {', '.join(shared)}")
    return conflicts


def resolve_fix_report(kind: str, arg: str, wants_fix: bool) -> str | None:
    """`--fix` names the report that routed this run here (D14 item 2).

    A story run started with `--fix` was sent back by `qa` or `review`, and the
    worker needs the report by path. The sequencer resolves it at the gate — the
    newest of the two declared paths, by mtime, `review` winning an exact tie —
    and refuses the run if neither exists, because `--fix` with nothing to fix
    is a caller mistake, not a run. Every other kind records `null`.
    """
    if not wants_fix or kind != "story":
        return None
    rows = []
    for pattern in FIX_REPORT_SOURCES:
        relative = pattern.format(arg=arg)
        path = ROOT / relative
        if path.is_file():
            rows.append((path.stat().st_mtime, relative))
    if not rows:
        raise Refuse(
            "NO_FIX_REPORT: --fix names the qa or review report that sent this story back, "
            "and neither " + " nor ".join(p.format(arg=arg) for p in FIX_REPORT_SOURCES)
            + " exists. Run /qa or /review first, or start the run without --fix.",
            REFUSED,
        )
    return max(rows)[1]


def story_source_digest(arg: str) -> str | None:
    """The current digest of a story document, or None when it cannot be read."""
    try:
        return sha(locate_story(arg))
    except SystemExit:
        return None


def slice_doc(e: dict) -> dict:
    """This run's `context.json`, or an empty mapping when it cannot be read."""
    try:
        doc = json.loads((work(e["run"]) / "context.json").read_text())
    except (OSError, ValueError):
        return {}
    return doc if isinstance(doc, dict) else {}


def story_changed_since_slice(e: dict) -> bool:
    """Has the story moved since this run's `context.json` was written?

    The digest lives in the slice the gate wrote, not in the run record, so the
    comparison is against exactly the bytes the workers were given. An
    unreadable or digest-free slice re-gates: re-resolving is cheap and being
    wrong the other way would silently re-enter a phase on a stale story.
    """
    recorded = slice_doc(e).get("incoming_sha256")
    if not recorded:
        return True
    return story_source_digest(e["arg"]) != recorded


def regate_on_resume(state: dict, e: dict, args) -> list[str]:
    """Re-run the story gate and re-slice before re-entering `blocked_at`.

    `/clarify <story>` is the documented answer to a `needs_user` block, and it
    rewrites the story. Resuming without re-reading it would re-dispatch the
    phase against the bundle the old story produced. So: re-gate, and on a clean
    gate refresh the story-derived fields and rewrite `context.json`. A gate that
    now refuses leaves the run blocked exactly as it was, with its reasons.
    """
    # The original gate's leniency is part of what opened this run; a resume
    # repeats it, so answering a block does not need the flag typed again.
    lenient = bool(getattr(args, "lenient", False)) or bool(slice_doc(e).get("lenient"))
    fm, problems, warnings = story_gate(state, e["arg"], lenient)
    if problems:
        return problems
    commands = fm.get("commands") or {}
    e.update({
        "write_fence": fm["write_fence"],
        "test_paths": sorted({r["file"] for r in fm["test_plan"]}),
        "test_plan": fm["test_plan"],
        "commands": {"source": commands["source"], "use": commands["use"]},
        "gate_policy": fm.get("gate_policy", {}),
    })
    if warnings:
        e["gate_warnings"] = warnings
    write_context(e, fm, relative_or_raw(locate_story(e["arg"])), lenient=lenient)
    log("run.reslice", session_id=e.get("session_id"), run=e["run"], arg=e["arg"])
    return []


def resume_run(state: dict, e: dict, args) -> None:
    """Re-enter a blocked run at `blocked_at`, with the attempt budget reset.

    The human has answered the question or fixed the cause; the candidate root,
    its checkpoints and its history are exactly as the block left them, so
    resuming is re-dispatching the phase that stopped, not opening a new run.
    """
    phase = e["blocked_at"]
    resliced = False
    if e.get("kind") == "story" and story_changed_since_slice(e):
        problems = regate_on_resume(state, e, args)
        if problems:
            # The story moved and the gate now refuses it. The run keeps its
            # candidate root, its checkpoints and its block; the handoff carries
            # the gate's reasons and the row they select.
            rows = [f"gate failed on resume: {problem}" for problem in problems]
            block(state, e, rows, "REQUIRE_HUMAN")
            raise Refuse(
                f"{e['run']} stays blocked at {phase}; the story changed and the gate now "
                "refuses it:\n  " + "\n  ".join(problems),
                REFUSED,
            )
        resliced = True
    if getattr(args, "fix", False):
        # A resume that repeats `--fix` re-resolves the report; a resume without
        # it keeps whatever the run already recorded.
        e["fix_report"] = resolve_fix_report(e.get("kind", ""), e["arg"], True)
    if e.get("kind") == "story":
        state.setdefault("stories", {}).setdefault(e["arg"], {})["status"] = "in_dev"
    e["phase"] = phase
    e["attempts"] = {name: 0 for name in phase_names(e["skill"])}
    e["granted_keys"] = sorted(phase_run_keys(e))
    e["blocked_at"] = None
    e["lease"] = None
    save_run(e)
    save(state)
    log("run.resume", session_id=e.get("session_id"), run=e["run"], phase=phase)
    agent = (phase_spec(e["skill"], phase) or {}).get("agent") or "(no worker)"
    print(
        f"{e['run']} resumed at phase {phase}, candidate {e['candidate']['mode']} at "
        f"{e['candidate']['root']}, checkpoint {e['candidate']['checkpoint']}, attempts "
        f"reset. Dispatch {agent} with the slice at {context_path(e['run'])}."
        + (" The story changed since the last slice: the gate re-ran and "
           f"{context_path(e['run'])} was rewritten." if resliced else "")
        + (f" fix_report: {e['fix_report']}" if e.get("fix_report") else "")
    )


def cmd_phase_start(args) -> None:
    state = load()
    skill = skill_key(args.skill)
    spec = skill_spec(skill)
    if spec is None:
        known = sorted(set(SKILLS) | set(SKILL_VARIANTS))
        raise Refuse(f"unknown skill {args.skill!r}; known: {known}", USAGE)
    if spec["kind"] == "none":
        raise Refuse(
            f"skill {skill} has no LLM workers and no phases; it is a thin wrapper "
            "over a deterministic operation",
            REFUSED,
        )
    if spec["kind"] == "external":
        runner = spec.get("runner", "")
        if shutil.which(runner) is None:
            sys.stderr.write(
                f"devforgeai: could_not_run reason_code=runner_missing: {runner} is not on PATH\n"
            )
            raise SystemExit(COULD_NOT_RUN)
        raise Refuse(f"{skill} is executed by {runner}, not by this sequencer", REFUSED)

    run = run_id(skill, args.arg)
    if run in live_runs(state):
        existing = load_run(run)
        if existing.get("blocked_at") and existing.get("skill") == skill \
                and existing.get("arg") == args.arg:
            return resume_run(state, existing, args)
        raise Refuse(f"run {run} is already active")
    phases = phase_names(skill)
    e = {
        "run": run,
        "canonical": str(ROOT),
        "skill": skill,
        "arg": args.arg,
        "kind": spec["kind"],
        "phase": phases[0],
        "attempts": {p: 0 for p in phases},
        "max_attempts": {p: (phase_spec(skill, p) or {}).get("max_attempts", 2) for p in phases},
        "bounce_count": 0,
        "blocked_at": None,
        "lease": None,
        "started_at": now(),
        "session_id": current_session(),
    }

    anchored = story_anchored(skill)
    if args.lenient and not (spec["kind"] == "story" or anchored):
        raise Refuse(
            "--lenient downgrades unresolvable-source at a story gate; "
            f"skill {skill} opens a document run and has no story to re-resolve",
            USAGE,
        )
    warnings: list[str] = []
    bundle_fm: dict | None = None
    bundle_source: str | None = None

    if spec["kind"] == "story":
        fm, problems, warnings = story_gate(state, args.arg, args.lenient)
        bundle_fm, bundle_source = fm, relative_or_raw(locate_story(args.arg))
        if problems:
            # D13 item 7: a gate refusal names its section 7f row when the skill
            # declares one for this defect — the unresolved-ASSUMPTION row routes
            # to `/clarify`. A defect the skill declares no row for gets no
            # forward command from the sequencer: the adapter renders those from
            # the spec's own table, and inventing a plausible one here would be
            # worse than printing none.
            kind = handoff_kind(skill, problems, "BLOCK")
            declared = (skill_spec(skill) or {}).get("handoff") or {}
            route = handoff_next(skill, kind, arg=args.arg, run=run,
                                 agent="the phase worker", tool="the tool") \
                if kind in declared else None
            raise Refuse(
                "gate failed:\n  " + "\n  ".join(problems)
                + (f"\nNext: {route}" if route else ""), REFUSED)
        e.update({
            "write_fence": fm["write_fence"],
            "test_paths": sorted({r["file"] for r in fm["test_plan"]}),
            "test_plan": fm["test_plan"],
            "commands": {"source": fm["commands"]["source"], "use": fm["commands"]["use"]},
            "gate_policy": fm.get("gate_policy", {}),
        })
    else:
        fence, problems = document_gate(skill, args.arg)
        e.update({
            "write_fence": fence,
            "test_paths": [],
            "test_plan": [],
            "commands": {},
            "gate_policy": {"unresolvable_source": "BLOCK"},
        })
        if anchored:
            # `qa` and `review` are document runs anchored to a story: the same
            # story gate runs, and the story's commands, test rows and policy
            # map are copied in so the phase's run keys can be brokered. The
            # fence stays the report path, so those workers write no code.
            fm, story_problems, warnings = story_gate(state, args.arg, args.lenient)
            bundle_fm, bundle_source = fm, relative_or_raw(locate_story(args.arg))
            problems += story_problems
            story_commands = fm.get("commands") or {}
            e.update({
                "test_paths": sorted({r["file"] for r in fm.get("test_plan") or []}),
                "test_plan": fm.get("test_plan") or [],
                "commands": {"source": story_commands.get("source"),
                             "use": story_commands.get("use") or []}
                if story_commands.get("source") else {},
                "gate_policy": fm.get("gate_policy", {}),
            })
        if problems:
            raise Refuse("gate failed:\n  " + "\n  ".join(problems), REFUSED)

    # `clarify` writes the story document, never the code, so it is the one
    # skill that may open against a story another run already holds — which is
    # how a `needs_user` block gets answered. `review` and `qa` stay refused.
    story = args.arg if (spec["kind"] == "story" or anchored) else None
    if story and skill not in STORY_IN_FLIGHT_EXEMPT:
        for other in live_runs(state):
            if other != run and (state["runs"][other] or {}).get("story") == story:
                raise Refuse(
                    f"STORY_IN_FLIGHT: run {other} is "
                    f"{(state['runs'][other] or {}).get('status')} and already names story "
                    f"{story}; a story-anchored run would judge a canonical tree that does "
                    "not contain that work. Promote or abandon it first.",
                    REFUSED,
                )
    conflicts = fence_conflicts(state, run, skill, e["write_fence"])
    if conflicts:
        raise Refuse(
            "FENCE_OVERLAP: this run's write_fence overlaps a live run's:\n  "
            + "\n  ".join(conflicts)
            + "\nFinish or abandon that run first; overlapping-fence integration is post-MVP.",
            REFUSED,
        )

    e["granted_keys"] = sorted(phase_run_keys(e))
    e["fix_report"] = resolve_fix_report(spec["kind"], args.arg, bool(args.fix))
    if warnings:
        e["gate_warnings"] = warnings

    shutil.rmtree(work(run), ignore_errors=True)
    e["candidate"] = candidate_open(e, stack_ignore_dirs(e))
    write_context(e, bundle_fm, bundle_source, lenient=bool(args.lenient))
    save_run(e)
    if e["kind"] == "story":
        state.setdefault("stories", {}).setdefault(args.arg, {})["status"] = "in_dev"
    state.setdefault("runs", {})[run] = {
        "story": story,
        "skill": skill,
        "mode": e["candidate"]["mode"],
        # Relative: state.yaml is tracked and carries no machine path (10 s12.3).
        "root": os.path.relpath(e["candidate"]["root"], ROOT),
        "base_ref": e["candidate"]["base_ref"],
        "checkpoint": "base",
        "status": "active",
    }
    save(state)
    log("phase.start", session_id=e["session_id"], run=run, skill=skill,
        phase=e["phase"], mode=e["candidate"]["mode"], base_ref=e["candidate"]["base_ref"],
        lenient=bool(args.lenient), gate_warnings=warnings)
    agent = (phase_spec(skill, e["phase"]) or {}).get("agent") or "(no worker)"
    for warning in warnings:
        sys.stderr.write(f"devforgeai: gate warning (downgraded): {warning}\n")
    print(
        f"{run} active, skill {skill}, phase {e['phase']}, candidate {e['candidate']['mode']} "
        f"at {e['candidate']['root']}. Dispatch {agent} with the slice at "
        f"{context_path(run)}; it writes only {e['write_fence']} inside the candidate root."
        + (f" fix_report: {e['fix_report']}" if e.get("fix_report") else "")
    )


def handoff(state: dict, e: dict, outcome: str, next_cmd: str, reasons: list[str],
            verdict: str | None = None) -> None:
    doc = {
        "schema": HANDOFF_SCHEMA,
        "run": e["run"],
        "skill": e["skill"],
        "outcome": outcome,
        "phase": e["phase"],
        "location": f".devforgeai/work/{e['run']}/",
        "reasons": reasons,
        "next": next_cmd,
        "attempts": e["attempts"],
        "authority": {"write_fence": e["write_fence"]},
        # Every judge findings file this run has persisted, in phase order. The
        # next phase's worker reads them by path (D13 item 3).
        "findings_paths": persisted_findings(e),
        "session_id": e.get("session_id") or current_session(),
        "at": now(),
    }
    if verdict:
        # The report's own reading, from `evidence.verdict`. It selects the row
        # this handoff renders; it is not the run's status, which stays `pass`.
        doc["verdict"] = verdict
    write_json_atomic(work(e["run"]) / "handoff.json", doc)
    state["next"] = next_cmd
    print("\n" + render_handoff(doc))


def render_handoff(doc: dict) -> str:
    """The single rendering of a handoff envelope (10 section 6, rules 2, 7, 8).

    `phase next` prints it when a run ends and `devforgeai status` prints this
    same function over the same file, so the run-end block and the status block
    cannot drift. Nothing is derived: a field the envelope does not carry is
    not printed, and blocking items precede the forward command.
    """
    head = f"{doc.get('run', '')}  {doc.get('outcome', '')}".strip()
    if doc.get("verdict"):
        head += f"  (verdict: {doc['verdict']})"
    lines = [head]
    for reason in doc.get("reasons") or []:
        lines.append(f"  - {reason}")
    for ref in doc.get("findings_paths") or []:
        lines.append(f"  evidence: {ref}")
    for item in doc.get("open_items") or []:
        if isinstance(item, dict):
            lines.append(f"  open: {item.get('id', '')} {item.get('text', '')}".rstrip())
        else:
            lines.append(f"  open: {item}")
    if doc.get("next"):
        lines.append(f"Next: {doc['next']}")
    return "\n".join(lines)


def find_handoff(state: dict) -> dict | None:
    """The envelope `status` renders: the live run's, else the most recent.

    Read-only and deterministic. With exactly one live run only that run's file
    is considered; otherwise every `work/*/handoff.json` is ordered by the
    envelope's own `at` and then by path, and the last one wins. A missing or
    unreadable file yields nothing rather than an error, because `status`
    reports state and never fails on it.
    """
    live = live_runs(state)
    if len(live) == 1:
        candidates = [DF / "work" / live[0] / "handoff.json"]
    else:
        candidates = sorted((DF / "work").glob("*/handoff.json")) if (DF / "work").is_dir() else []
    rows: list[tuple[str, str, dict]] = []
    for path in candidates:
        try:
            envelope = json.loads(path.read_text())
        except (OSError, ValueError):
            continue
        if isinstance(envelope, dict) and envelope.get("schema") == HANDOFF_SCHEMA:
            rows.append((str(envelope.get("at") or ""), path.as_posix(), envelope))
    if not rows:
        return None
    rows.sort(key=lambda row: (row[0], row[1]))
    return rows[-1][2]


def close_run(state: dict, e: dict, status: str) -> None:
    row = state.setdefault("runs", {}).setdefault(e["run"], {})
    row["status"] = status
    row["checkpoint"] = (e.get("candidate") or {}).get("checkpoint")


def block(state: dict, e: dict, problems: list[str], policy: str) -> None:
    """Record a blocker. The run stays `active`, with its lease released.

    A blocked run is not abandoned (10 section 12.4): its root and every
    checkpoint survive for inspection, `blocked_at` records the phase it stopped
    in, and `devforgeai phase start <skill> <arg>` on the same run resumes there
    with the attempt budget reset. The other exit is `devforgeai phase fail`.
    """
    if e.get("kind") == "story":
        state.setdefault("stories", {}).setdefault(e["arg"], {})["status"] = "dev_blocked"
    state.setdefault("runs", {}).setdefault(e["run"], {})["checkpoint"] = \
        (e.get("candidate") or {}).get("checkpoint")
    # 10 section 6 and D13 item 7: the forward command is a named row of the
    # skill's section 7f table, not a default. The skill's own rows are tried
    # first, so `red`'s "a planned test already passes" routes to `/clarify`
    # rather than to the generic resume. It is never `/status`, which reports
    # and changes nothing.
    phase = e.get("phase") or ""
    at_limit = e.get("attempts", {}).get(phase, 0) >= e.get("max_attempts", {}).get(phase, 2)
    kind = handoff_kind(e["skill"], problems, policy, at_limit=at_limit)
    note = (last_result(e) or {}).get("note") or " ".join(str(p) for p in problems)
    nxt = handoff_next(
        e["skill"], kind, arg=e["arg"], run=e["run"],
        agent=(phase_spec(e["skill"], phase) or {}).get("agent") or "the phase worker",
        tool=refused_tool(note),
    )
    log("handoff.row", session_id=e.get("session_id"), run=e["run"], phase=phase,
        row=kind, policy=policy)
    e["blocked_at"] = e["phase"] if policy == "REQUIRE_HUMAN" else None
    e["lease"] = None
    save_run(e)
    handoff(state, e, policy, nxt, problems)
    save(state)
    log("blocked", session_id=e.get("session_id"), run=e["run"], policy=policy,
        blocked_at=e.get("blocked_at"), problems=problems)


def previous_checkpoint(e: dict, phase: str) -> str:
    """The checkpoint a phase starts from: the one its predecessor wrote."""
    order = phase_names(e["skill"])
    index = order.index(phase)
    return "base" if index == 0 else order[index - 1]


def rewind(state: dict, e: dict, target: str, reason: str) -> None:
    """Re-enter `target`, with the root back at the checkpoint that phase reads."""
    candidate_rewind(e, previous_checkpoint(e, target))
    e["attempts"][target] = e["attempts"].get(target, 0) + 1
    e["bounce_count"] = e.get("bounce_count", 0) + 1
    e["phase"] = target
    e["granted_keys"] = sorted(phase_run_keys(e))
    e["lease"] = None
    e.pop("red_hashes", None)
    for f in work(e["run"]).glob("*-report.md"):
        f.unlink()
    save_run(e)
    log("rewind", session_id=e.get("session_id"), run=e["run"], to=target,
        checkpoint=e["candidate"]["checkpoint"], reason=reason[-300:])
    if e["attempts"][target] >= e["max_attempts"].get(target, 2):
        return block(state, e, [f"{target} rewound too many times"], "REQUIRE_HUMAN")
    agent = (phase_spec(e["skill"], target) or {}).get("agent")
    print(
        f"rewound to {target} (attempt {e['attempts'][target]}); the candidate root is back "
        f"at checkpoint {e['candidate']['checkpoint']}. Dispatch {agent}."
    )


def cmd_phase_next(args) -> None:
    require_hook("phase next")
    state = load()
    e = enf(state, args.run)
    advance(state, e)


def finish_run(state: dict, e: dict, result: dict) -> None:
    """The last phase passed: park the run for a human to promote (10 s12.4).

    Promotion is never automatic. The run is marked `ready_to_promote` and the
    handoff's one forward command is `devforgeai promote <run>`; the user reads
    the rendered reports first and then promotes, or does not.
    """
    e["lease"] = None
    save_run(e)
    close_run(state, e, "ready_to_promote")
    verdict = result.get("verdict")
    reasons = [f"all {e['skill']} phases passed",
               f"the candidate root is at checkpoint {e['candidate']['checkpoint']}"]
    if verdict:
        reasons.append(f"{result['agent']} verdict: {verdict}")
    handoff(state, e, "REQUIRE_HUMAN", f"devforgeai promote {e['run']}", reasons,
            verdict=verdict or None)
    save(state)
    log("run.ready", run=e["run"], checkpoint=e["candidate"]["checkpoint"], verdict=verdict)


def advance(state: dict, e: dict, result: dict | None = None) -> None:
    phase = e["phase"]
    order = phase_names(e["skill"])
    result = result or last_result(e)
    if result is None:
        raise Refuse(f"phase {phase} has no worker receipt; nothing to check")

    if result.get("next"):
        return rewind(state, e, result["next"], result.get("note") or "rewind requested")

    if result["status"] == "could_not_run":
        policy = (e.get("gate_policy") or {}).get("test_runner_missing", "REQUIRE_HUMAN")
        reason = f"COULD_NOT_RUN: {result.get('reason_code')}: {result.get('note') or ''}".strip()
        write_phase_report(e, result, [reason])
        return block(state, e, [reason], policy)

    if result["status"] == "needs_user":
        # A worker asking for a human is never told to try again.
        reason = f"needs_user: {result.get('note') or 'the worker requires a human decision'}"
        write_phase_report(e, result, [reason])
        return block(state, e, [reason], "REQUIRE_HUMAN")

    problems = list(result.get("pre_oracle_problems") or [])
    problems += run_oracle(e, result)
    if result["status"] != "pass":
        problems.insert(0, f"{result['agent']} reported {result['status']}")
    write_phase_report(e, result, problems)

    if any(p.startswith("COULD_NOT_RUN") for p in problems):
        policy = (e.get("gate_policy") or {}).get("test_runner_missing", "REQUIRE_HUMAN")
        save_run(e)
        return block(state, e, problems, policy)

    if problems:
        e["attempts"][phase] = e["attempts"].get(phase, 0) + 1
        limit = e["max_attempts"].get(phase, 2)
        save_run(e)
        log("transition.fail", session_id=e.get("session_id"), run=e["run"],
            phase=phase, problems=problems)
        if e["attempts"][phase] >= limit:
            return block(state, e, problems, "REQUIRE_HUMAN")
        agent = (phase_spec(e["skill"], phase) or {}).get("agent")
        sys.stderr.write(
            f"devforgeai: phase {phase} check failed (attempt {e['attempts'][phase]} of {limit}):\n  "
            + "\n  ".join(problems)
            + f"\nDispatch {agent} again with these rows.\n"
        )
        raise SystemExit(REFUSED)

    candidate_checkpoint(e, phase)
    render_report_view(e)
    state.setdefault("runs", {}).setdefault(e["run"], {})["checkpoint"] = phase
    index = order.index(phase)
    nxt = order[index + 1] if index + 1 < len(order) else None
    log("transition.pass", session_id=e.get("session_id"), run=e["run"],
        checkpoint=phase, **{"from": phase, "to": nxt})
    if nxt is None:
        e["lease"] = None
        save_run(e)
        return finish_run(state, e, result)
    e["phase"] = nxt
    e["granted_keys"] = sorted(phase_run_keys(e))
    e["lease"] = None
    save_run(e)
    save(state)
    print(
        f"phase {phase} passed, checkpoint {phase} written -> {nxt}. "
        f"Dispatch {(phase_spec(e['skill'], nxt) or {}).get('agent')}."
    )


def render_report_view(e: dict) -> None:
    """`docs/reports/<skill>-<run>-<phase>.md` is a rendered view (10 section 2).

    It is the sequencer's own canonical write, not a run artifact: it names the
    run and the phase, so it cannot collide with a report a `review` or `qa` run
    writes inside its candidate root, and it is not part of any promotion.
    """
    source = work(e["run"]) / f"{e['phase']}-report.md"
    if not source.exists():
        return
    target = ROOT / "docs" / "reports" / f"{e['skill']}-{e['run']}-{e['phase']}.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source.read_text())
    record_sequencer_write(e["run"], target.relative_to(ROOT).as_posix())


def last_result(e: dict) -> dict | None:
    path = work(e["run"]) / f"{e['phase']}-result.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def cmd_phase_fail(args) -> None:
    """Record a blocker and abandon the candidate: the run is over."""
    state = load()
    e = enf(state, args.run)
    block(state, e, [args.reason], "BLOCK")
    candidate_abandon(e, state)
    save(state)


def bind_lease(e: dict, args) -> None:
    """SubagentStart: bind the phase lease to this worker (D3, D6; 10 s12.2).

    The only identity-bearing pre-write event on either provider, which is why
    the binding happens here and nowhere else. Reached as
    `devforgeai candidate lease <run>`, called by the dispatcher.
    """
    agent = canonical_agent(args.agent or "")
    allowed = allowed_agents(e)
    if agent not in allowed:
        raise Refuse(f"phase {e['phase']} belongs to {sorted(allowed)}, not {args.agent!r}",
                     REFUSED)
    if is_judge(e["skill"], e["phase"]):
        print(f"{e['run']} phase {e['phase']}: {agent} judges this checkpoint, holds no lease "
              f"and writes nothing; it returns its evidence in the receipt's `findings` field "
              f"and the sequencer persists it at {findings_path(e)}")
        return
    lease = e.get("lease") or {}
    if lease and lease.get("agent_id") and lease.get("agent_id") != args.agent_id:
        raise Refuse(
            f"LEASE_HELD: phase {e['phase']} is leased to {lease.get('agent')}/"
            f"{lease.get('agent_id')}; one producer writes in a candidate root at a time",
            REFUSED,
        )
    e["lease"] = {
        "session_id": args.session_id or current_session(),
        "agent": agent,
        "agent_id": args.agent_id,
        "phase": e["phase"],
        "granted_at": now(),
    }
    save_run(e)
    append_session_event(e["lease"]["session_id"], "lease.granted", run=e["run"],
                         phase=e["phase"], agent=agent, agent_id=args.agent_id)
    log("lease.bind", session_id=e["lease"]["session_id"], run=e["run"], phase=e["phase"],
        agent=agent, agent_id=args.agent_id)
    print(f"{e['run']} phase {e['phase']}: lease bound to {agent}/{args.agent_id}; "
          f"write inside {e['candidate']['root']}")


def cmd_ingest_result(args) -> None:
    """Hook-only broker: read the receipt, derive the changes, check, advance."""
    require_hook("ingest-result")
    raw = sys.stdin.read(MAX_RESULT_BYTES + 1)
    state = load()
    e = enf(state, args.run)
    phase = e["phase"]
    session_id = args.session_id or current_session()

    if not args.agent or not args.agent_id:
        # The event carried no worker identity. Do not checkpoint anything, do
        # not block-loop the subagent: record it and hand off to the human.
        result = {
            "schema": RESULT_SCHEMA, "run": e["run"], "skill": e["skill"], "phase": phase,
            "agent": args.agent or "unknown", "agent_id": args.agent_id or "",
            "status": "could_not_run", "reason_code": "hook_fault",
            "candidate": {"id": e["run"], "input_checkpoint": e["candidate"]["checkpoint"]},
            "claimed_paths": [], "evidence_refs": [], "findings": None,
            "findings_path": None,
            "note": "SubagentStop carried no agent_id/agent_type; the receipt cannot be bound "
                    "to the active phase and the candidate was not checkpointed.",
            "issues": [], "next": None, "changed": [],
            "captured_at": now(), "session_id": session_id, "checkpointed": False,
        }
        write_json_atomic(work(e["run"]) / f"{phase}-result.json", result)
        write_phase_report(e, result, ["hook_fault: no agent identity on the stop event"])
        log("hook_fault", session_id=session_id, run=e["run"], phase=phase)
        block(state, e, [f"COULD_NOT_RUN: hook_fault: {result['note']}"], "REQUIRE_HUMAN")
        return

    result = parse_receipt(raw, e, args.agent, args.agent_id)
    result["session_id"] = session_id
    # D13 item 3: the receipt is valid, so its `findings` body is persisted
    # verbatim at the fixed path before anything else is derived. The path is
    # recorded in `<phase>-result.json` and in the handoff `findings_paths` list.
    result["findings_path"] = persist_findings(e, result)
    root = candidate_root(e)
    problems = lease_problems(e, result)

    if result["status"] == "pass":
        # A worker cannot hash a file it is writing, so PENDING digests resolve
        # inside the root before the change set is derived from it.
        try:
            pending = candidate_changes(e)
        except (OSError, ValueError, SystemExit) as exc:
            # The checkpoint this phase started from is gone, or the diff against
            # it cannot be taken. Nothing about this run can be derived, so it is
            # an infra failure of the sequencer's own state, not a phase defect
            # and not a malformed receipt.
            return checkpoint_fault(state, e, result, exc)
        result["digests_resolved"] = resolve_pending_digests(e, pending, root)
        changed = candidate_changes(e)
        result["changed"] = changed
        problems += change_problems(e, changed, result["claimed_paths"], root)
        problems += artifact_problems(e, changed, root)
        verdict, verdict_problems = receipt_verdict(e, result, root)
        result["verdict"] = verdict
        problems += verdict_problems
    else:
        # Only a `pass` claims paths, so only a `pass` is held to a change set.
        # What the candidate holds is still recorded, unchecked, for the report.
        result["changed"] = []
        try:
            result["changed_unchecked"] = candidate_changes(e)
        except SystemExit:
            result["changed_unchecked"] = []

    result["result_sha256"] = "sha256:" + hashlib.sha256(
        json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    result["checkpointed"] = False
    result_path = work(e["run"]) / f"{phase}-result.json"
    write_json_atomic(result_path, result)
    log("receipt.ingested", session_id=session_id, run=e["run"], phase=phase,
        agent=result["agent"], agent_id=result["agent_id"], status=result["status"],
        claimed=len(result["claimed_paths"]), changed=len(result["changed"]))

    if problems:
        # The receipt is refused: the candidate keeps the worker's edits, the
        # phase does not checkpoint, and canonical is untouched.
        # The lease is not released: the broker exited non-zero, so the same
        # worker is being asked to continue in the same root (10 section 12.2).
        write_phase_report(e, result, problems)
        save_run(e)
        raise Refuse(
            f"receipt refused for {e['run']} phase {phase}:\n  " + "\n  ".join(problems),
            REFUSED,
        )

    (work(e["run"]) / "changes.json").write_text(
        json.dumps(result["changed"], indent=1))
    result["pre_oracle_problems"] = []
    advance(state, e, result)
    result["checkpointed"] = e["candidate"].get("checkpoint") == phase
    write_json_atomic(result_path, result)

    after = load_run(e["run"]) if run_file(e["run"]).exists() else {}
    if after.get("phase") == phase and result["status"] == "pass" \
            and (state.get("runs", {}).get(e["run"], {}) or {}).get("status") == "active":
        raise Refuse(
            f"phase {phase} remains active after validation; revise the candidate and return "
            f"a fresh {RESULT_SCHEMA} receipt",
            REFUSED,
        )


def checkpoint_fault(state: dict, e: dict, result: dict, exc: BaseException) -> None:
    """Ingest could not read the input checkpoint or diff against it.

    `hook_fault` is reserved for a missing hook identity and a malformed
    receipt; this is neither. The receipt was valid and the worker did its job —
    the sequencer's own checkpoint is what is missing — so the run is blocked
    for a human with the candidate root left exactly as it stands.
    """
    detail = str(exc).strip().splitlines()[-1] if str(exc).strip() else type(exc).__name__
    note = (f"the input checkpoint {(e.get('candidate') or {}).get('checkpoint')!r} could not "
            f"be read and the change set could not be derived: {detail[:400]}")
    result.update({
        "status": "could_not_run", "reason_code": "checkpoint_fault",
        "changed": [], "claimed_paths": [], "note": note, "checkpointed": False,
    })
    write_json_atomic(work(e["run"]) / f"{e['phase']}-result.json", result)
    write_phase_report(e, result, [f"COULD_NOT_RUN: checkpoint_fault: {note}"])
    log("checkpoint_fault", session_id=result.get("session_id"), run=e["run"],
        phase=e["phase"], detail=detail[:200])
    block(state, e, [f"COULD_NOT_RUN: checkpoint_fault: {note}"], "REQUIRE_HUMAN")


def cmd_run(args) -> None:
    """The lease holder's one stack key, with cwd = the candidate root.

    Also callable from the SubagentStop marker, where the sequencer itself runs
    a key inside a transition oracle.
    """
    state = load()
    e = enf(state, args.run)
    phase = e["phase"]
    if args.key not in phase_run_keys(e):
        raise Refuse(f"phase {phase} does not grant stack command key {args.key!r}", REFUSED)
    if os.environ.get("DEVFORGEAI_HOOK_EVENT") != "SubagentStop" and not (e.get("lease") or {}):
        raise Refuse(
            f"no lease is held for phase {phase}; `devforgeai run <key>` belongs to the "
            "producer working inside the candidate root",
            REFUSED,
        )
    root = candidate_root(e)

    problems = invariant_problems(e)
    if problems:
        raise Refuse(
            "refusing stack command; invariants already fail:\n  " + "\n  ".join(problems), REFUSED
        )

    ignore = candidate_ignore(e)
    before = manifest(root, ignore)
    outcome = run_key(e, args.key)
    after = manifest(root, ignore)
    changed = sorted(p for p in set(before) | set(after) if before.get(p) != after.get(p))
    # A runner writes its junit file and its caches, which no manifest sees. A
    # manifest-visible change means the command edited the tree (10 section 2).
    problems = [f"stack command mutated project file: {p}" for p in changed]
    problems += invariant_problems(e)
    log("command.run", session_id=e.get("session_id"), run=e["run"], phase=phase,
        key=args.key, classification=outcome["classification"], exit=outcome["exit"],
        mutation_count=len(changed))
    if problems:
        raise Refuse("stack command violated invariants:\n  " + "\n  ".join(problems), REFUSED)
    if outcome["classification"] in ("INFRA_FAILURE", "TIMEOUT"):
        sys.stderr.write(
            "devforgeai: COULD_NOT_RUN reason_code="
            + ("timeout" if outcome["classification"] == "TIMEOUT" else "runner_missing")
            + ": " + outcome["output"].strip().splitlines()[-1] + "\n"
        )
        raise SystemExit(COULD_NOT_RUN)
    if outcome["output"]:
        print(outcome["output"])
    print(f"classification: {outcome['classification']}")
    if outcome["exit"]:
        raise SystemExit(REFUSED)


def final_verdict(e: dict) -> str | None:
    """The verdict the run's last report stated, read back from its result."""
    path = work(e["run"]) / f"{phase_names(e['skill'])[-1]}-result.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text()).get("verdict")
    except (OSError, ValueError):
        return None


def cmd_promote(args) -> None:
    """Model-callable: promote the run the sequencer parked as ready_to_promote."""
    state = load()
    row = (state.get("runs") or {}).get(args.run)
    if not row:
        raise Refuse(f"NO_CANDIDATE: no run {args.run} is recorded in state.yaml", REFUSED)
    if row.get("status") != "ready_to_promote":
        raise Refuse(
            f"run {args.run} is {row.get('status')}; `devforgeai promote` finishes a run the "
            "sequencer parked as ready_to_promote",
            REFUSED,
        )
    e = load_run(args.run)
    problems = candidate_promote(e, state)
    if problems:
        # 10 section 6: a refused promotion says which canonical paths to settle,
        # and its forward command is the promotion itself, run again.
        joined = " ".join(problems)
        if "DIRTY_TARGET" in joined:
            nxt = f"commit or discard the named canonical edits, then devforgeai promote {e['run']}"
        else:
            nxt = f"resolve the named canonical paths, then devforgeai promote {e['run']}"
        handoff(state, e, "REQUIRE_HUMAN", nxt, problems)
        save(state)
        raise Refuse("promotion refused:\n  " + "\n  ".join(problems), REFUSED)
    if e.get("kind") == "story":
        state.setdefault("stories", {}).setdefault(e["arg"], {})["status"] = "dev_done"
    verdict = final_verdict(e)
    next_cmd = f"/review {e['arg']}" if e.get("kind") == "story" else "/status"
    reasons = [f"promoted {e['run']} into the canonical tree"]
    if verdict:
        reasons.append(f"report verdict: {verdict}")
    if verdict in ("findings", "fail") and e["skill"] in VERDICT_NEXT:
        next_cmd = VERDICT_NEXT[e["skill"]].format(arg=e["arg"])
    root = e["candidate"]["root"]
    candidate_remove(e)
    save_run(e)
    handoff(state, e, "pass", next_cmd, reasons, verdict=verdict or None)
    save(state)
    print(f"{e['run']} promoted from {root}; the candidate root is gone")


def cmd_candidate(args) -> None:
    """Sequencer-internal candidate lifecycle (D7)."""
    require_internal(args.op)
    state = load()
    e = load_run(args.run)
    if args.op == "open":
        e["candidate"] = candidate_open(e, stack_ignore_dirs(e))
        save_run(e)
        state.setdefault("runs", {}).setdefault(e["run"], {}).update({
            "mode": e["candidate"]["mode"], "root": e["candidate"]["root"],
            "base_ref": e["candidate"]["base_ref"], "checkpoint": "base", "status": "active",
        })
        save(state)
        print(f"{e['run']} candidate {e['candidate']['mode']} at {e['candidate']['root']}")
        return
    if args.op == "lease":
        bind_lease(e, args)
        return
    if args.op == "checkpoint":
        phase = args.phase or e["phase"]
        candidate_checkpoint(e, phase)
        save_run(e)
        state.setdefault("runs", {}).setdefault(e["run"], {})["checkpoint"] = phase
        save(state)
        print(f"{e['run']} checkpoint {phase}")
        return
    if args.op == "promote":
        problems = candidate_promote(e, state)
        save(state)
        if problems:
            raise Refuse("promotion refused:\n  " + "\n  ".join(problems), REFUSED)
        print(f"{e['run']} promoted")
        return
    candidate_abandon(e, state)
    save(state)
    print(f"{e['run']} abandoned")


def cmd_validate(args) -> None:
    """Read-only invariant check for pre-commit and CI backstops (rung 4)."""
    state = load()
    e = enf(state, args.run)
    problems = invariant_problems(e)
    stack = stack_section(e)
    if stack:
        problems += stack_problems(stack, (e.get("commands") or {}).get("use") or [])
    if problems:
        raise Refuse("validation failed:\n  " + "\n  ".join(problems), REFUSED)
    print(f"{e['run']} phase {e['phase']}: fence and techstack invariants hold")


def run_block(state: dict) -> dict:
    """The block a primary pastes into a dispatch prompt (D9)."""
    try:
        e = enf(state)
    except SystemExit:
        return {}
    return {
        "run": e["run"],
        "skill": e["skill"],
        "candidate": {
            "mode": (e.get("candidate") or {}).get("mode"),
            "root": (e.get("candidate") or {}).get("root"),
            "checkpoint": (e.get("candidate") or {}).get("checkpoint"),
        },
        "phase": e["phase"],
        "fence": e.get("write_fence") or [],
        "granted_keys": e.get("granted_keys") or [],
        "lease": e.get("lease"),
        "context": context_path(e["run"]),
        # Printed only when the run was started with `--fix`, so a status block
        # never names a report that does not exist (D14 item 2).
        **({"fix_report": e["fix_report"]} if e.get("fix_report") else {}),
    }


def cmd_status(args) -> None:
    """The run block, then the handoff envelope's own rendering.

    10 section 6 rule 7: the run-end block and the status block are the same
    rendering of the same file, so this prints `render_handoff` over
    `work/<run>/handoff.json` and never reformats the envelope by hand.
    """
    state = load()
    print(yaml.safe_dump({
        "run": run_block(state),
        "runs": state.get("runs", {}),
        "next": state.get("next"),
        "session": current_session(),
    }, sort_keys=False))
    envelope = find_handoff(state)
    if envelope:
        print(render_handoff(envelope))


def cmd_session_start(args) -> None:
    """Hook-only: session evidence plus the worktree-mode self-test (D6)."""
    require_hook("session-start")
    if not DF.exists():
        # SessionStart must never fault on an uninitialised repository.
        print("DevForgeAI is not installed in this repository; nothing to arm.")
        return
    state, state_parsed = {}, True
    try:
        state = load()
        if not isinstance(state, dict):
            state_parsed = False
            state = {}
    except (OSError, yaml.YAMLError):
        state_parsed = False
    stack_resolvable = True
    live = live_runs(state)
    e = {}
    if live:
        try:
            e = load_run(live[0])
        except SystemExit:
            e = {}
    if (e.get("commands") or {}).get("source"):
        try:
            stack_resolvable = stack_section(e) is not None
        except SystemExit:
            stack_resolvable = False
    dispatcher = Path(__file__).with_name("dispatch.py")
    repo = git_repo(ROOT)
    prerequisites = worktree_prerequisites(ROOT) if repo else []
    doc = {
        "schema": "devforgeai.session/v1",
        "session_id": args.session_id,
        "provider": args.provider,
        "provider_version": args.provider_version or "unknown",
        "dispatcher_sha256": sha(dispatcher) if dispatcher.is_file() else "ABSENT",
        "hooks_armed": dispatcher.is_file(),
        "state_parsed": state_parsed,
        "stack_resolvable": stack_resolvable,
        "candidate_mode": "worktree" if repo and not prerequisites else "copy",
        "worktree_prerequisites": prerequisites,
        "at": now(),
        "events": [],
    }
    (DF / "sessions").mkdir(parents=True, exist_ok=True)
    write_json_atomic(DF / "sessions" / f"{args.session_id}.json", doc)
    log("session.start", session_id=args.session_id, provider=args.provider,
        hooks_armed=doc["hooks_armed"], state_parsed=state_parsed,
        stack_resolvable=stack_resolvable, candidate_mode=doc["candidate_mode"],
        worktree_prerequisites=prerequisites)
    print(
        "DevForgeAI hooks armed. session "
        f"{args.session_id} provider {args.provider}/{doc['provider_version']}; "
        f"state_parsed={state_parsed}; stack_resolvable={stack_resolvable}; "
        f"candidate_mode={doc['candidate_mode']}"
        + (f"; worktree unavailable (could_not_run reason_code=prerequisite_missing): "
           f"{prerequisites}" if repo and prerequisites else "")
        + "; "
        + (f"live runs {live}" if live else "no live run: writes are denied outside a candidate")
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="devforgeai")
    ap.add_argument("--run", default=None, help="name the run when several are live")
    sub = ap.add_subparsers(dest="cmd", required=True)

    phase = sub.add_parser("phase", help="phase lifecycle")
    phase_ops = phase.add_subparsers(dest="op", required=True)
    start = phase_ops.add_parser("start", help="model-callable: gate and enter phase 1")
    start.add_argument("skill")
    start.add_argument("arg")
    start.add_argument(
        "--fix", action="store_true",
        help="this run was sent back by qa or review: record the newest of "
             "docs/reports/qa-<story>.md and docs/reports/review-<story>.md as "
             "run.yaml#fix_report and print it in the status block",
    )
    start.add_argument(
        "--lenient", action="store_true",
        help="downgrade unresolvable-source to a recorded warning; refused for a story "
             "under docs/plan/ and for a skill with no story gate",
    )
    start.set_defaults(fn=cmd_phase_start)
    nxt = phase_ops.add_parser("next", help="hook-only (SubagentStop): run the oracle")
    nxt.set_defaults(fn=cmd_phase_next)
    fail = phase_ops.add_parser("fail", help="model-callable: record a blocker")
    fail.add_argument("--reason", required=True)
    fail.set_defaults(fn=cmd_phase_fail)

    run = sub.add_parser("run", help="lease holder: one stack command key in the candidate root")
    run.add_argument("key")
    run.set_defaults(fn=cmd_run)

    ingest = sub.add_parser("ingest-result", help="hook-only (SubagentStop): read a receipt")
    ingest.add_argument("--agent", default="")
    ingest.add_argument("--agent-id", default="")
    ingest.add_argument("--session-id", default="")
    ingest.set_defaults(fn=cmd_ingest_result)

    session = sub.add_parser("session-start", help="hook-only (SessionStart): session evidence")
    session.add_argument("--session-id", required=True)
    session.add_argument("--provider", required=True, choices=["claude", "codex"])
    session.add_argument("--provider-version", default="")
    session.set_defaults(fn=cmd_session_start)

    candidate = sub.add_parser("candidate", help="sequencer-internal: candidate lifecycle")
    candidate.add_argument("op", choices=list(CANDIDATE_OPS))
    candidate.add_argument("run")
    candidate.add_argument("phase", nargs="?", default=None)
    candidate.add_argument("--agent", default="")
    candidate.add_argument("--agent-id", default="")
    candidate.add_argument("--session-id", default="")
    candidate.set_defaults(fn=cmd_candidate)

    promote = sub.add_parser("promote", help="model-callable: promote a ready_to_promote run")
    promote.add_argument("run", metavar="run")
    promote.set_defaults(fn=cmd_promote)

    sub.add_parser("validate", help="model-callable: fence/stack invariants").set_defaults(
        fn=cmd_validate
    )
    sub.add_parser("status", help="model-callable: print the run block").set_defaults(
        fn=cmd_status
    )
    return ap


def main() -> None:
    ap = build_parser()
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
