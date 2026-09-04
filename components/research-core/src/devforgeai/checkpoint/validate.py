"""Semantic validation of research-gap checkpoint records (plan section 7).

Structural validity comes from ``schemas/devforgeai/v1/research-gap-checkpoint.schema.json``.
Everything a schema cannot say is a rule here, each with a stable id so a test
or a reviewer can name it:

  S01 plan header      the plan README names a decision authority and a base commit
                       (``Amendment base``, else ``Base commit``)
  S02 filename         ``checkpoints/<checkpoint_id>.yaml``
  S03 ledger           the README ledger and the records agree on ids and ``closed``
  S04 path escape      repository-relative paths stay inside the repository; an
                       admitted input's absolute path is external evidence and may
                       not contain ``..``
  S05 stages           closure stages legal for the checkpoint type when closed
  S06 closure          the nine ``closed: true`` conditions of section 7.1; S06.9 is
                       the release pin, fail-closed (corrective-spec-001 CS-1,
                       corrective-spec-002 CS-6): decidable only by the installed
                       validator, whose own verified release root R must be the
                       record's release: ``executable_path`` equals ``<R>/bin/devforge``;
                       every release resource exists; the executable, ``RELEASE.sha256``,
                       every file it lists and every ancestor up to ``/`` are regular
                       objects owned by uid 0 with no group/other write and no
                       symbolic link; the release manifest verifies in both
                       directions and lists the required entries; the record's digests
                       equal the installed bytes; ``RELEASE-IDENTITY.json`` binds the
                       record's version, DevForge commit, schema and policy versions
                       and the candidate pin (the installed policy is the promoted
                       candidate manifest); both provider proofs are bound to the
                       executable digest
  S07 open record      an open record carries no human closure decision
  S08 admission        ``ADMITTED`` only after CP-00 closed; admitted entries carry evidence
  S09 dependencies     a closed checkpoint's dependencies are closed
  S10 closure diff     the closure range of a closed record (from its attestation,
                       S14; a caller ``--diff`` is used only by the staged validator,
                       whose verdict on a closed record is already a rejection)
                       touches closure paths only
  S11 manifest         ``checkpoints/MANIFEST.sha256`` exists, excludes itself, covers
                       every record, and every entry verifies
  S12 authority        every record's ``decision_authority_id`` equals the plan's
  S13 open stages      an open record's ``PASS`` stages carry their evidence
                       (amendment SDD-GAP-AMD-001): ``researched`` needs the dossier
                       of S06.2 with passing independent verifications; a stage above
                       UNBOUND or ``implemented`` needs the complete candidate pin,
                       whose commit is merged and whose manifest verifies at that
                       commit and on disk and covers every fenced file outside the
                       records and the dossier; ``proven`` needs both provider proofs
                       and the release pin of S06.9
  S14 attestation      a closed record has a closure attestation minted by the
                       protected host (``devforge checkpoint attest``, uid 0) at the
                       fixed location ``/var/lib/devforge/attest/<repository
                       identity>/<plan id>/<checkpoint>.json`` on a protected path
                       chain; it validates against its schema and binds the
                       repository identity, plan, checkpoint, record path and digest
                       (at the attested head and on disk), base (proper ancestor of
                       head) and head (HEAD or an ancestor of HEAD), the executing
                       release root and its identity digest, the authority and uid 0;
                       a caller ``--diff`` must equal an attested range (CS-9)

Rules S06, S10, S13 and S14 need Git; when Git or the repository is unavailable
the run is ``COULD_NOT_RUN`` (exit 3), never a pass. Git runs as
``/usr/bin/git`` with an explicit minimal environment (CS-7.1); nothing from the
caller's environment reaches it.

Policy is never caller-selected (CS-2): the schemas are resolved from the
validator's own location (installed release root, else the checkout holding
the module), the Git root from the plan directory alone, and the CLI carries
no override. The filesystem view of protected paths, the executing release
root and the attestation directory form the ``ReleaseFS`` seam, injectable
in-process for tests only; the CLI always uses the real one.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat as statmod
import subprocess
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

import yaml
from jsonschema import Draft202012Validator

SCHEMA_NAME = "research-gap-checkpoint.schema.json"
IDENTITY_SCHEMA_NAME = "release-identity.schema.json"
ATTESTATION_SCHEMA_NAME = "closure-attestation.schema.json"
IDENTITY_NAME = "RELEASE-IDENTITY.json"
ATTEST_ROOT = Path("/var/lib/devforge/attest")
# Installed-layout contract v2: every entry RELEASE.sha256 must list.
REQUIRED_RELEASE_ENTRIES = (
    "bin/devforge", "bin/devforge-checkpoint.py", IDENTITY_NAME,
    f"schemas/devforgeai/v1/{SCHEMA_NAME}", f"schemas/devforgeai/v1/{IDENTITY_SCHEMA_NAME}",
    f"schemas/devforgeai/v1/{ATTESTATION_SCHEMA_NAME}", "contracts/MANIFEST.sha256",
)
PLACEHOLDERS = ("TODO", "TBD", "{{", "}}", "<fill in>", "lorem ipsum")
CLOSURE_ONLY_SUFFIXES = ("README.md", "MANIFEST.sha256")
LEDGER_HEADER = re.compile(r"^\|\s*ID\s*\|\s*Type\s*\|", re.I)
LEDGER_ROW = re.compile(r"^\|\s*(CP-\d{2})\s*\|")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
SAFE_COMPONENT = re.compile(r"[A-Za-z0-9_][A-Za-z0-9._-]*")      # CS-9.7
# CS-7.1: the only Git executable and the only environment it ever sees.
GIT = "/usr/bin/git"
GIT_ENV = {
    "PATH": "/usr/bin:/bin", "HOME": "/nonexistent", "LC_ALL": "C",
    "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_TERMINAL_PROMPT": "0",
}


class ReleaseFS:
    """Filesystem view of protected paths, the executing release root and the
    attestation directory. Tests inject a fake in-process; the CLI never
    exposes a way to select one."""

    attest_root: Path = ATTEST_ROOT

    def lstat(self, path: Path) -> os.stat_result:
        return os.lstat(path)

    def read_bytes(self, path: Path) -> bytes:
        return Path(path).read_bytes()

    def walk(self, root: Path) -> list[Path]:
        return sorted(Path(root).rglob("*"))

    def executing_root(self, module_file: Path) -> Path | None:
        """Installed mode: the module lies under a release root holding RELEASE.sha256."""
        return _release_root_of(module_file)


class CouldNotRun(Exception):
    """The validator could not reach a verdict; never reported as a pass."""


@dataclass(frozen=True)
class Problem:
    checkpoint: str
    rule: str
    message: str


@dataclass
class Report:
    plan: str
    records: int
    problems: list[Problem] = field(default_factory=list)

    @property
    def outcome(self) -> str:
        return "PASS" if not self.problems else "REJECTED"

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan": self.plan,
            "records": self.records,
            "outcome": self.outcome,
            "problems": [problem.__dict__ for problem in self.problems],
        }


# ---------- helpers ----------

def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _release_root_of(module_file: Path) -> Path | None:
    """Installed mode: the module lies under a release root holding RELEASE.sha256."""
    for ancestor in module_file.absolute().parents:
        if (ancestor / "RELEASE.sha256").is_file():
            return ancestor
    return None


def _schema_dir(release_root: Path | None) -> Path:
    """The schemas come from the validator's own location, never from the plan's
    tree (CS-2.2): the installed release root, else the checkout holding the module."""
    here = Path(__file__)
    if release_root is not None:
        return release_root / "schemas" / "devforgeai" / "v1"
    for ancestor in here.absolute().parents:
        candidate = ancestor / "schemas" / "devforgeai" / "v1"
        if (candidate / SCHEMA_NAME).is_file():
            return candidate
    raise CouldNotRun(f"{SCHEMA_NAME} not found above the validator module {here}")


def _git_bytes(root: Path, *argv: str) -> tuple[int, bytes, bytes]:
    """CS-7.1: absolute ``/usr/bin/git``, explicit environment, plumbing only."""
    try:
        completed = subprocess.run([GIT, "-C", str(root), *argv], capture_output=True,
                                   env=GIT_ENV, stdin=subprocess.DEVNULL, timeout=60)
    except FileNotFoundError as exc:
        raise CouldNotRun(f"git is not installed at {GIT}") from exc
    except subprocess.TimeoutExpired as exc:
        raise CouldNotRun(f"git {argv[0]} timed out") from exc
    return completed.returncode, completed.stdout, completed.stderr


def _git(root: Path, *argv: str) -> tuple[int, str]:
    code, out, err = _git_bytes(root, *argv)
    return code, (out.decode("utf-8", "replace") + err.decode("utf-8", "replace")).strip()


def _git_root(plan: Path) -> Path:
    """The repository root derives from the plan directory alone (CS-2.3)."""
    code, out = _git(plan.resolve(), "rev-parse", "--show-toplevel")
    if code != 0:
        raise CouldNotRun(f"{plan} is not inside a Git repository: {out}")
    root = Path(out.splitlines()[0]).resolve()
    code, out = _git(root, "rev-parse", "--is-inside-work-tree")
    if code != 0 or out.splitlines()[-1] != "true":
        raise CouldNotRun(f"{root} is not a Git work tree: {out}")
    if not plan.resolve().is_relative_to(root):
        raise CouldNotRun(f"plan {plan} is not inside its repository root {root}")
    return root


def _is_placeholder(text: str) -> bool:
    lowered = text.lower()
    return not text.strip() or any(token.lower() in lowered for token in PLACEHOLDERS)


def _bad_relative(path: str) -> str | None:
    """Return why a repository-relative path is unacceptable, or None."""
    if not path or path.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:[\\/]", path):
        return "absolute path where a repository-relative path is required"
    if "\\" in path:
        return "backslash in path"
    parts = PurePosixPath(path).parts
    if ".." in parts:
        return "path escapes the repository (`..`)"
    if any(part == "" for part in parts):
        return "empty path segment"
    return None


def _read_manifest(manifest: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        digest, _, name = line.partition("  ")
        name = name.strip()
        if name.startswith("./"):
            name = name[2:]
        entries[name] = digest.strip()
    return entries



def _blob(git_root: Path, commit: str, name: str) -> bytes | None:
    """The exact bytes of ``name`` at ``commit``; None when absent."""
    code, out, _ = _git_bytes(git_root, "cat-file", "blob", f"{commit}:{name}")
    return out if code == 0 else None


def _blob_sha256(git_root: Path, commit: str, name: str) -> str | None:
    """SHA-256 of the exact bytes of ``name`` at ``commit``; None when absent."""
    blob = _blob(git_root, commit, name)
    return hashlib.sha256(blob).hexdigest() if blob is not None else None


def _repository_identity(git_root: Path) -> tuple[str, list[str]]:
    """CS-9.1: SHA-256 over the sorted root-commit SHAs joined by LF."""
    code, out = _git(git_root, "rev-list", "--max-parents=0", "HEAD")
    if code != 0:
        raise CouldNotRun(f"git rev-list --max-parents=0 HEAD failed: {out}")
    roots = sorted(out.split())
    return hashlib.sha256("\n".join(roots).encode()).hexdigest(), roots


def _check_dossier(rec: dict[str, Any], git_root: Path, rule: str, reject: Any) -> None:
    """Closure condition 2 (S06.2) and the open-record form (S13): the dossier
    manifest resolves in both directions and the named verifications passed."""
    research = rec.get("research", {})
    dossier = research.get("dossier_path")
    if not dossier:
        reject(rule, "record names no research dossier")
        return
    manifest = git_root / str(dossier) / "MANIFEST.sha256"
    if not manifest.is_file():
        reject(rule, f"dossier manifest missing: {dossier}/MANIFEST.sha256")
        return
    if research.get("manifest_sha256") != _sha256(manifest):
        reject(rule, "research.manifest_sha256 does not equal the dossier manifest's digest")
    entries = _read_manifest(manifest)
    if "MANIFEST.sha256" in entries:
        reject(rule, "dossier manifest lists itself")
    for name, digest in entries.items():
        target = manifest.parent / name
        if not target.is_file():
            reject(rule, f"dossier manifest entry missing on disk: {name}")
        elif _sha256(target) != digest:
            reject(rule, f"dossier manifest entry does not verify: {name}")
    if not entries:
        reject(rule, "dossier manifest is empty")
    # Section 6: the manifest lists every retained dossier file except
    # itself, so a file the manifest does not name is a custody hole.
    for candidate in sorted(manifest.parent.rglob("*")):
        if not candidate.is_file() or candidate.name == "MANIFEST.sha256":
            continue
        if "__pycache__" in candidate.parts:
            continue
        rel = candidate.relative_to(manifest.parent).as_posix()
        if rel not in entries:
            reject(rule, f"dossier file not in manifest: {rel}")
    # Verification outcomes: every named verification exists, passed, and was
    # run by someone other than the record owner.
    ids = [str(v) for v in research.get("verification_ids", [])]
    if not ids:
        reject(rule, "research.verification_ids is empty; a researched stage needs an independent verification")
        return
    vfile = manifest.parent / "verification.jsonl"
    if not vfile.is_file():
        reject(rule, "dossier has no verification.jsonl")
        return
    found: dict[str, dict[str, Any]] = {}
    for line in vfile.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            reject(rule, "verification.jsonl has an unparseable line")
            continue
        if isinstance(row, dict) and row.get("verification_id"):
            found[str(row["verification_id"])] = row
    owner = rec.get("owner_id")
    for vid in ids:
        row = found.get(vid)
        if row is None:
            reject(rule, f"verification {vid} is not in verification.jsonl")
        elif row.get("outcome") != "PASS":
            reject(rule, f"verification {vid} outcome is {row.get('outcome')!r}, not PASS")
        elif not row.get("verifier"):
            reject(rule, f"verification {vid} names no verifier")
        elif row.get("verifier") == owner:
            reject(rule, f"verification {vid} verifier equals the record owner (not independent)")


def _glob_to_regex(pattern: str) -> re.Pattern[str]:
    """`**` matches across separators, `*` within one segment (fence globs)."""
    out = ""
    i = 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out += "(?:.*/)?"
            i += 3
        elif pattern.startswith("**", i):
            out += ".*"
            i += 2
        elif pattern[i] == "*":
            out += "[^/]*"
            i += 1
        else:
            out += re.escape(pattern[i])
            i += 1
    return re.compile("^" + out + "$")


def _check_enforcement(rec: dict[str, Any], ctx: Context, closed: bool, reject: Any) -> None:
    """S13 (open record) and S06.9 (closure): the candidate and release pins."""
    plan, git_root, fs = ctx.plan, ctx.git_root, ctx.fs
    enforcement = rec.get("enforcement", {})
    stage = enforcement.get("trust_stage", "UNBOUND")
    stages = rec.get("closure_stages", {})
    candidate = enforcement.get("candidate", {})
    release = enforcement.get("protected_release", {})
    open_rule = "S13"
    closed_rule = "S06.9" if closed else "S13"

    if not closed and stages.get("researched") == "PASS":
        _check_dossier(rec, git_root, open_rule, reject)
    if not closed and stages.get("proven") == "PASS":
        for provider in ("claude", "codex"):
            proof = rec.get("provider_proof", {}).get(provider, {})
            if proof.get("status") != "PASS":
                reject(open_rule, f"proven: PASS with provider proof {provider} {proof.get('status')}")
    if stages.get("implemented") == "PASS" and stage == "UNBOUND":
        reject(open_rule, "implemented: PASS with enforcement.trust_stage UNBOUND")
    if stage != "UNBOUND" or stages.get("implemented") == "PASS":
        missing = [k for k in ("source_commit", "manifest_path", "manifest_sha256") if not candidate.get(k)]
        if missing:
            reject(open_rule, f"candidate pin incomplete: {', '.join(missing)} null")
        else:
            _check_candidate_pin(rec, candidate, plan, git_root, open_rule, reject)

    if stages.get("proven") == "PASS" and stage != "PROTECTED_RELEASE":
        reject(closed_rule, f"proven: PASS with enforcement.trust_stage {stage}")
    if closed and stage != "PROTECTED_RELEASE":
        reject(closed_rule, f"closed record with enforcement.trust_stage {stage}; "
                            "closure requires PROTECTED_RELEASE")
    if stage == "PROTECTED_RELEASE" or stages.get("proven") == "PASS" or closed:
        missing = [k for k, v in release.items() if v in (None, "")]
        if missing:
            reject(closed_rule, f"release pin incomplete: {', '.join(missing)} null")
        else:
            _check_release_pin(rec, release, ctx, closed_rule, reject)


def _check_candidate_pin(rec: dict[str, Any], candidate: dict[str, Any], plan: Path,
                         git_root: Path, rule: str, reject: Any) -> None:
    commit = str(candidate["source_commit"])
    manifest_rel = str(candidate["manifest_path"])
    if why := _bad_relative(manifest_rel):
        reject(rule, f"candidate.manifest_path: {why}: {manifest_rel}")
        return
    code, _ = _git(git_root, "cat-file", "-e", f"{commit}^{{commit}}")
    if code != 0:
        reject(rule, f"candidate.source_commit {commit} does not exist in the repository")
        return
    code, _ = _git(git_root, "merge-base", "--is-ancestor", commit, "HEAD")
    if code != 0:
        reject(rule, f"candidate.source_commit {commit} is not an ancestor of HEAD")
    manifest = git_root / manifest_rel
    if not manifest.is_file():
        reject(rule, f"candidate manifest missing on disk: {manifest_rel}")
        return
    pinned = candidate.get("manifest_sha256")
    if _sha256(manifest) != pinned:
        reject(rule, "candidate.manifest_sha256 does not equal the candidate manifest's digest")
    at_commit = _blob_sha256(git_root, commit, manifest_rel)
    if at_commit is None:
        reject(rule, f"candidate manifest {manifest_rel} is absent at source_commit {commit[:12]}")
    elif at_commit != pinned:
        reject(rule, f"candidate manifest at source_commit {commit[:12]} differs from the pinned digest")
    entries = _read_manifest(manifest)
    if not entries:
        reject(rule, "candidate manifest is empty")
    if manifest_rel in entries:
        reject(rule, "candidate manifest lists itself")
    for name, digest in entries.items():
        blob = _blob_sha256(git_root, commit, name)
        if blob is None:
            reject(rule, f"candidate manifest entry absent at source_commit {commit[:12]}: {name}")
        elif blob != digest:
            reject(rule, f"candidate manifest entry does not verify at source_commit {commit[:12]}: {name}")
        target = git_root / name
        if not target.is_file():
            reject(rule, f"candidate manifest entry missing on disk: {name}")
        elif _sha256(target) != digest:
            reject(rule, f"candidate bytes changed since source_commit {commit[:12]}: {name}")
    # Coverage: every fenced file at source_commit, except the records, the
    # dossier and the manifest itself, must be pinned.
    plan_rel = plan.resolve().relative_to(git_root).as_posix()
    excluded_prefixes = [f"{plan_rel}/checkpoints/"]
    dossier = rec.get("research", {}).get("dossier_path")
    if dossier:
        excluded_prefixes.append(str(dossier).rstrip("/") + "/")
    fence = [*rec.get("implementation", {}).get("changed_contracts", []),
             *rec.get("implementation", {}).get("changed_runtime_paths", [])]
    patterns = [_glob_to_regex(str(f)) for f in fence]
    code, listing = _git(git_root, "ls-tree", "-r", "--name-only", commit)
    if code != 0:
        raise CouldNotRun(f"git ls-tree {commit} failed: {listing}")
    for path in listing.splitlines():
        path = path.strip()
        if not path or path == manifest_rel or "__pycache__" in path:
            continue
        if any(path.startswith(prefix) for prefix in excluded_prefixes):
            continue
        if any(pat.match(path) for pat in patterns) and path not in entries:
            reject(rule, f"fenced file not pinned by the candidate manifest: {path}")


def _protected_path_problems(path: Path, fs: ReleaseFS, want_dir: bool = False) -> list[str]:
    """CS-1.3: every component of ``path`` up to ``/`` exists, is not a symbolic
    link, is owned by uid 0 and grants no group/other write."""
    problems: list[str] = []
    chain = [*reversed(path.parents), path]
    for prefix in chain:
        label = "ancestor" if prefix != path else ("directory" if want_dir else "file")
        try:
            st = fs.lstat(prefix)
        except FileNotFoundError:
            problems.append(f"{label} missing: {prefix}")
            return problems
        except OSError as exc:
            problems.append(f"{label} cannot be inspected: {prefix}: {exc}")
            return problems
        if statmod.S_ISLNK(st.st_mode):
            problems.append(f"{label} is a symbolic link: {prefix}")
            return problems
        if prefix != path and not statmod.S_ISDIR(st.st_mode):
            problems.append(f"ancestor is not a directory: {prefix}")
            return problems
        if prefix == path and not (statmod.S_ISDIR(st.st_mode) if want_dir else statmod.S_ISREG(st.st_mode)):
            problems.append(f"{label} is not a regular {'directory' if want_dir else 'file'}: {prefix}")
            return problems
        if st.st_uid != 0:
            problems.append(f"{label} not owned by uid 0 (uid {st.st_uid}): {prefix}")
        if st.st_mode & 0o022:
            problems.append(f"{label} is group or other writable (mode {statmod.S_IMODE(st.st_mode):o}): {prefix}")
    return problems


def _release_root(executable: Path) -> Path:
    """CS-1.2: parent of ``bin/``, else the executable's directory."""
    return executable.parent.parent if executable.parent.name == "bin" else executable.parent


def _parse_manifest_text(text: str) -> dict[str, str]:
    entries: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        digest, _, name = line.partition("  ")
        name = name.strip()
        if name.startswith("./"):
            name = name[2:]
        entries[name] = digest.strip()
    return entries


def verify_release_tree(root: Path, fs: ReleaseFS) -> tuple[list[str], dict[str, str]]:
    """CS-1.3 and CS-1.4 over an installed release root. Returns (problems, entries)."""
    problems: list[str] = []
    manifest = root / "RELEASE.sha256"
    for why in _protected_path_problems(root, fs, want_dir=True):
        problems.append(f"release root: {why}")
    try:
        fs.lstat(manifest)
    except FileNotFoundError:
        problems.append(f"RELEASE.sha256 missing at {root}")
        return problems, {}
    for why in _protected_path_problems(manifest, fs):
        problems.append(f"RELEASE.sha256: {why}")
    try:
        entries = _parse_manifest_text(fs.read_bytes(manifest).decode("utf-8"))
    except (OSError, UnicodeDecodeError) as exc:
        problems.append(f"RELEASE.sha256 unreadable: {exc}")
        return problems, {}
    if not entries:
        problems.append("RELEASE.sha256 is empty")
    if "RELEASE.sha256" in entries:
        problems.append("RELEASE.sha256 lists itself")
    for name, digest in entries.items():
        if name.startswith("/") or ".." in PurePosixPath(name).parts:
            problems.append(f"RELEASE.sha256 entry escapes the release root: {name}")
            continue
        target = root / name
        whys = _protected_path_problems(target, fs)
        for why in whys:
            problems.append(f"release entry {name}: {why}")
        if whys and any("missing" in w or "symbolic" in w or "not a regular" in w for w in whys):
            continue
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            problems.append(f"release entry {name}: malformed digest")
            continue
        if hashlib.sha256(fs.read_bytes(target)).hexdigest() != digest:
            problems.append(f"release entry does not verify: {name}")
    for path in fs.walk(root):
        rel = path.relative_to(root).as_posix()
        try:
            st = fs.lstat(path)
        except OSError:
            continue
        if statmod.S_ISLNK(st.st_mode):
            problems.append(f"symbolic link inside the release root: {rel}")
        elif statmod.S_ISREG(st.st_mode) and rel != "RELEASE.sha256" and rel not in entries:
            problems.append(f"release file not listed in RELEASE.sha256: {rel}")
    return problems, entries


def _check_release_pin(rec: dict[str, Any], release: dict[str, Any], ctx: Context,
                       rule: str, reject: Any) -> None:
    """CS-1 and CS-6: fail-closed. Condition 9 is decidable only by the installed
    validator, whose executing release must be the record's release; every
    resource mandatory; protected-path rule; release manifest verified both ways;
    record digests bound to installed bytes; RELEASE-IDENTITY.json binds the
    record's version, DevForge commit and candidate pin."""
    fs, git_root = ctx.fs, ctx.git_root
    executable = str(release["executable_path"])
    if not executable.startswith("/") or ".." in PurePosixPath(executable).parts:
        reject(rule, f"executable_path must be absolute without `..` (no PATH resolution): {executable}")
        return
    exe = Path(executable)
    if exe.is_relative_to(git_root.resolve()) or exe.resolve().is_relative_to(git_root.resolve()):
        reject(rule, f"executable_path is inside the repository (project-local fallback): {executable}")
    # CS-6.1 / CS-6.2: the executing release decides, and it must be this one.
    if ctx.release_root is None:
        reject(rule, "condition 9 is decidable only by the installed validator: this validator runs "
                     "from a checkout, not from a verified release root")
    else:
        own = ctx.release_root / "bin" / "devforge"
        if executable != str(own):
            reject(rule, f"executable_path {executable} is not the executing release's executable {own} "
                         f"(executing root {ctx.release_root})")
    whys = _protected_path_problems(exe, fs)
    for why in whys:
        reject(rule, f"executable: {why}" if not why.startswith("file missing") else f"executable missing: {executable}")
    exe_present = not any("missing" in w or "symbolic" in w or "not a regular" in w for w in whys)
    root = _release_root(exe)
    problems, entries = verify_release_tree(root, fs)
    for why in problems:
        reject(rule, why)
    if entries:
        exe_rel = exe.relative_to(root).as_posix() if exe.is_relative_to(root) else None
        if exe_rel not in entries:
            reject(rule, f"RELEASE.sha256 does not list the executable {exe_rel}")
        for required in REQUIRED_RELEASE_ENTRIES:
            if required not in entries:
                reject(rule, f"RELEASE.sha256 does not list the required entry {required}")
        schema_rel = f"schemas/devforgeai/v1/{SCHEMA_NAME}"
        policy_rel = "contracts/MANIFEST.sha256"
        for label, rel, field_name in (("schema", schema_rel, "schema_set_sha256"),
                                       ("policy", policy_rel, "contract_policy_sha256")):
            if rel in entries and entries[rel] != release[field_name]:
                reject(rule, f"{field_name} does not equal the installed {label} digest")
    if exe_present:
        try:
            if hashlib.sha256(fs.read_bytes(exe)).hexdigest() != release["executable_sha256"]:
                reject(rule, f"executable digest mismatch at {executable}")
        except OSError as exc:
            reject(rule, f"executable unreadable: {exc}")
    # CS-6.3 / CS-6.4: the executing release's identity binds the record.
    candidate = rec.get("enforcement", {}).get("candidate", {})
    if ctx.release_root is not None:
        for why in ctx.identity_problems:
            reject(rule, why)
        identity = ctx.identity
        if identity is not None:
            bindings = [
                ("version", release.get("version"), "version"),
                ("source_commit", release.get("source_commit"), "devforge_commit"),
                ("schema_set_version", release.get("schema_set_version"), "schema_set_version"),
                ("contract_policy_version", release.get("contract_policy_version"), "contract_policy_version"),
                ("contract_policy_sha256", release.get("contract_policy_sha256"), "candidate_manifest_sha256"),
            ]
            if rec.get("checkpoint_id") == identity.get("candidate_checkpoint_id"):
                # The release was built from this record's candidate: its pin can never move.
                bindings += [
                    ("candidate.source_commit", candidate.get("source_commit"), "candidate_source_commit"),
                    ("candidate.manifest_sha256", candidate.get("manifest_sha256"), "candidate_manifest_sha256"),
                ]
            for record_field, record_value, identity_field in bindings:
                if record_value != identity.get(identity_field):
                    suffix = (": the installed policy must be the promoted candidate manifest"
                              if record_field == "contract_policy_sha256" else "")
                    reject(rule, f"{record_field} {record_value!r} does not equal {IDENTITY_NAME} "
                                 f"{identity_field} {identity.get(identity_field)!r}{suffix}")
    for label in ("promotion_evidence_path", "permissions_evidence_path"):
        value = str(release[label])
        digest = release[label.replace("_path", "_sha256")]
        if value.startswith("/"):
            if ".." in PurePosixPath(value).parts:
                reject(rule, f"{label} contains `..`: {value}")
                continue
            target = Path(value)
        elif why := _bad_relative(value):
            reject(rule, f"{label}: {why}: {value}")
            continue
        else:
            target = git_root / value
        if not target.is_file():
            reject(rule, f"{label} missing: {value}")
            continue
        if _sha256(target) != digest:
            reject(rule, f"{label} digest mismatch: {value}")
    if not candidate.get("source_commit"):
        reject(rule, "release pin without the retained candidate pin (candidate/release mapping)")
    proofs = rec.get("provider_proof", {})
    passing = {name: proof for name, proof in proofs.items() if proof.get("status") == "PASS"}
    bound = {proof.get("subject_sha256") for proof in passing.values()}
    if rec.get("checkpoint_type") != "RESEARCH_ONLY" and set(passing) != {"claude", "codex"}:
        reject(rule, "release pin needs both provider proofs PASS and bound to it")
    elif bound and bound != {release["executable_sha256"]}:
        reject(rule, "provider proofs are not both bound to the release executable digest")


def _read_release_identity(root: Path, fs: ReleaseFS, schema_dir: Path) -> tuple[dict[str, Any] | None, list[str]]:
    """CS-6.3: parse and validate <root>/RELEASE-IDENTITY.json of the executing release."""
    path = root / IDENTITY_NAME
    problems = [f"{IDENTITY_NAME}: {why}" for why in _protected_path_problems(path, fs)]
    if problems:
        return None, [f"{IDENTITY_NAME} missing from the executing release {root}"
                      if "missing" in problems[0] else problems[0]]
    try:
        document = json.loads(fs.read_bytes(path).decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, [f"{IDENTITY_NAME} unreadable: {exc}"]
    schema_path = schema_dir / IDENTITY_SCHEMA_NAME
    if not schema_path.is_file():
        return None, [f"{IDENTITY_SCHEMA_NAME} missing beside the validator's schemas"]
    validator = Draft202012Validator(json.loads(schema_path.read_text(encoding="utf-8")))
    errors = [f"{IDENTITY_NAME} invalid: {'/'.join(str(p) for p in e.path) or '<root>'}: {e.message[:160]}"
              for e in sorted(validator.iter_errors(document), key=lambda e: list(e.path))]
    if errors or not isinstance(document, dict):
        return None, errors or [f"{IDENTITY_NAME} is not an object"]
    return document, []


def _check_attestation(cp: str, rec: dict[str, Any], ctx: Context, reject: Any) -> None:
    """S14 (CS-9.4): the closure attestation of a closed record, at the fixed
    location on a protected path chain, binds this repository, plan, record,
    range and the executing release. On success the attested range is kept for S10."""
    rule = "S14"
    if ctx.release_root is None:
        reject(rule, "closure attestation is checked only by the installed validator")
        return
    if ctx.attestation_validator is None:
        reject(rule, f"{ATTESTATION_SCHEMA_NAME} missing beside the validator's schemas")
        return
    fs, git_root = ctx.fs, ctx.git_root
    identity, roots = _repository_identity(git_root)
    plan_id = ctx.header.plan_id
    if not plan_id:
        reject(rule, "plan README names no `Plan ID`; the attestation location needs it")
        return
    # CS-9.7: neither the plan id (agent-authored README) nor the checkpoint id
    # may steer the lookup under the fixed attestation root.
    for label, value in (("plan id", plan_id), ("checkpoint id", cp)):
        if not SAFE_COMPONENT.fullmatch(value):
            reject(rule, f"{label} {value!r} is unsafe as a path component under the attestation root")
            return
    path = fs.attest_root / identity[:32] / plan_id / f"{cp}.json"
    whys = _protected_path_problems(path, fs)
    if whys:
        for why in whys:
            reject(rule, f"closure attestation missing at {path}" if why.startswith("file missing")
                   else f"closure attestation {path}: {why}")
        return
    try:
        document = json.loads(fs.read_bytes(path).decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        reject(rule, f"closure attestation unreadable: {exc}")
        return
    errors = sorted(ctx.attestation_validator.iter_errors(document), key=lambda e: list(e.path))
    if errors:
        for error in errors:
            reject(rule, f"closure attestation invalid: {'/'.join(str(p) for p in error.path) or '<root>'}: "
                         f"{error.message[:160]}")
        return
    plan_rel = ctx.plan.resolve().relative_to(git_root).as_posix()
    record_rel = f"{plan_rel}/checkpoints/{cp}.yaml"
    expected = {
        "repository_identity": identity, "repository_root_commits": roots, "plan_path": plan_rel,
        "plan_id": plan_id, "checkpoint_id": cp, "record_path": record_rel,
        "release_root": str(ctx.release_root), "authority_id": ctx.header.decision_authority,
        "minted_by_uid": 0,
    }
    ok = True
    for name, want in expected.items():
        if document.get(name) != want:
            reject(rule, f"closure attestation {name} {document.get(name)!r} does not equal {want!r}")
            ok = False
    identity_file = ctx.release_root / IDENTITY_NAME
    try:
        identity_digest = hashlib.sha256(fs.read_bytes(identity_file)).hexdigest()
    except OSError:
        identity_digest = None
    if document.get("release_identity_sha256") != identity_digest:
        reject(rule, f"closure attestation release_identity_sha256 does not equal the digest of {identity_file}")
        ok = False
    head, base = str(document.get("head_commit")), str(document.get("base_commit"))
    code, _ = _git(git_root, "cat-file", "-e", f"{head}^{{commit}}")
    if code != 0:
        reject(rule, f"closure attestation head_commit {head} does not exist in the repository")
        return
    code, _ = _git(git_root, "merge-base", "--is-ancestor", head, "HEAD")
    if code != 0:
        reject(rule, f"closure attestation head_commit {head[:12]} is neither HEAD nor an ancestor of HEAD")
        ok = False
    code, _ = _git(git_root, "cat-file", "-e", f"{base}^{{commit}}")
    if code != 0:
        reject(rule, f"closure attestation base_commit {base} does not exist in the repository")
        return
    code, _ = _git(git_root, "merge-base", "--is-ancestor", base, head)
    if code != 0 or base == head:
        reject(rule, f"closure attestation base_commit {base[:12]} is not a proper ancestor of head_commit {head[:12]}")
        ok = False
    at_head = _blob_sha256(git_root, head, record_rel)
    on_disk = _sha256(ctx.plan / "checkpoints" / f"{cp}.yaml")
    if at_head != document.get("record_sha256"):
        reject(rule, f"closure attestation record_sha256 does not equal the record blob at head_commit {head[:12]}")
        ok = False
    if on_disk != document.get("record_sha256"):
        reject(rule, "closure attestation record_sha256 does not equal the record on disk: "
                     "the record changed after the attestation was minted")
        ok = False
    if ok:
        ctx.attested[cp] = (base, head)


# ---------- plan README ----------

@dataclass
class PlanHeader:
    decision_authority: str | None
    base_commit: str | None
    ledger: dict[str, dict[str, str]]   # id -> {"closed": "true"/"false", "depends": "…"}
    plan_id: str | None = None


@dataclass
class Context:
    """What one validation run knows beyond the record: the seam, the plan and
    its repository, the executing release (installed mode) and its identity, the
    attestation schema, and the attested closure ranges S14 collects for S10."""
    fs: ReleaseFS
    plan: Path
    git_root: Path
    header: PlanHeader
    release_root: Path | None
    identity: dict[str, Any] | None
    identity_problems: list[str]
    attestation_validator: Draft202012Validator | None
    attested: dict[str, tuple[str, str]] = field(default_factory=dict)


def _parse_readme(readme: Path) -> PlanHeader:
    authority = base = plan_id = None
    ledger: dict[str, dict[str, str]] = {}
    in_ledger = False
    columns: list[str] = []
    for line in readme.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("| Plan ID |"):
            plan_id = stripped.split("|")[2].strip().strip("`")
        elif stripped.startswith("| Decision authority |"):
            authority = stripped.split("|")[2].strip().strip("`")
        elif stripped.startswith("| Amendment base |") or (
                stripped.startswith("| Base commit |") and base is None):
            cell = stripped.split("|")[2].strip()
            match = re.search(r"[0-9a-f]{40}", cell)
            base = match.group(0) if match else base
        if LEDGER_HEADER.match(stripped):
            in_ledger = True
            columns = [cell.strip().lower() for cell in stripped.strip("|").split("|")]
            continue
        if in_ledger:
            if not stripped.startswith("|"):
                in_ledger = False
                continue
            match = LEDGER_ROW.match(stripped)
            if not match:
                continue
            cells = [cell.strip() for cell in stripped.strip("|").split("|")]
            row = dict(zip(columns, cells))
            ledger[match.group(1)] = {
                "closed": row.get("closed", "").strip().lower(),
                "depends": row.get("depends on", "").strip(),
            }
    return PlanHeader(authority, base, ledger, plan_id)


# ---------- rules ----------

def _check_record(cp: str, rec: dict[str, Any], ctx: Context, records: dict[str, dict[str, Any]],
                  problems: list[Problem]) -> None:
    def reject(rule: str, message: str) -> None:
        problems.append(Problem(cp, rule, message))

    header, plan, git_root = ctx.header, ctx.plan, ctx.git_root
    closed = bool(rec.get("closed"))
    ctype = rec.get("checkpoint_type")

    # S12 authority
    if header.decision_authority and rec.get("decision_authority_id") != header.decision_authority:
        reject("S12", f"decision_authority_id {rec.get('decision_authority_id')!r} differs from the "
                      f"plan's {header.decision_authority!r}")

    # S03 ledger agreement
    row = header.ledger.get(cp)
    if row is None:
        reject("S03", "no ledger row in the plan README")
    else:
        ledger_closed = row["closed"] == "true"
        if ledger_closed != closed:
            reject("S03", f"ledger says closed={row['closed']} but the record says {str(closed).lower()}")

    # S04 paths
    for label, value in (
        ("research.dossier_path", rec.get("research", {}).get("dossier_path")),
        ("provider_proof.claude.evidence_path", rec.get("provider_proof", {}).get("claude", {}).get("evidence_path")),
        ("provider_proof.codex.evidence_path", rec.get("provider_proof", {}).get("codex", {}).get("evidence_path")),
        ("independent_review.evidence_path", rec.get("independent_review", {}).get("evidence_path")),
    ):
        if value is not None and (why := _bad_relative(str(value))):
            reject("S04", f"{label}: {why}: {value}")
    for label in ("changed_contracts", "changed_runtime_paths"):
        for value in rec.get("implementation", {}).get(label, []):
            if why := _bad_relative(str(value)):
                reject("S04", f"implementation.{label}: {why}: {value}")
    for entry in rec.get("admitted_inputs", []):
        subject = str(entry.get("subject", ""))
        for value in [subject, *map(str, entry.get("evidence_paths", []))]:
            if value.startswith("/"):
                # Section 7.1: an absolute path is explicitly external evidence.
                # It is admitted as such; it may not climb.
                if ".." in PurePosixPath(value).parts:
                    reject("S04", f"{entry.get('input_id')}: external evidence path contains `..`: {value}")
            elif why := _bad_relative(value):
                reject("S04", f"{entry.get('input_id')}: {why}: {value}")

    # S08 admission
    cp00 = records.get("CP-00")
    cp00_closed = bool(cp00 and cp00.get("closed")) if cp != "CP-00" else closed
    for entry in rec.get("admitted_inputs", []):
        if entry.get("state") == "ADMITTED":
            if not cp00_closed:
                reject("S08", f"{entry.get('input_id')} is ADMITTED before CP-00 is closed")
            if not entry.get("evidence_paths"):
                reject("S08", f"{entry.get('input_id')} is ADMITTED without evidence_paths")

    # S07 open record
    if not closed:
        if rec.get("human_closure", {}).get("decision") is not None:
            reject("S07", "an open record carries a human closure decision")
        # S13 pins of an open record
        _check_enforcement(rec, ctx, False, reject)
        return

    # ---- closed: S05, S06, S09 ----
    stages = rec.get("closure_stages", {})
    expected = {
        "RESEARCH_ONLY": {"researched": "PASS", "implemented": "NOT_APPLICABLE", "proven": "NOT_APPLICABLE"},
        "RESEARCH_AND_IMPLEMENTATION": {"researched": "PASS", "implemented": "PASS", "proven": "PASS"},
        "EXPERIMENT": {"researched": "PASS", "implemented": "NOT_APPLICABLE", "proven": "PASS"},
    }.get(ctype, {})
    for stage, want in expected.items():
        if stages.get(stage) != want:
            reject("S05", f"{ctype} requires closure_stages.{stage} = {want}, found {stages.get(stage)}")

    if rec.get("attempt_outcome") != "COMPLETE":
        reject("S06.1", f"closed record has attempt_outcome {rec.get('attempt_outcome')!r}, not COMPLETE")

    _check_dossier(rec, git_root, "S06.2", reject)

    if ctype != "RESEARCH_ONLY":
        for provider in ("claude", "codex"):
            proof = rec.get("provider_proof", {}).get(provider, {})
            if proof.get("status") != "PASS":
                reject("S06.3", f"required provider proof {provider} is {proof.get('status')}, not PASS")
            elif not proof.get("evidence_path") or not proof.get("subject_sha256"):
                reject("S06.3", f"provider proof {provider} PASS without evidence_path and subject_sha256")

    review = rec.get("independent_review", {})
    if review.get("verdict") != "PASS":
        reject("S06.4", f"independent_review.verdict is {review.get('verdict')}, not PASS")
    reviewer = review.get("reviewer_id")
    if not reviewer:
        reject("S06.4", "independent_review.reviewer_id is missing")
    elif reviewer == rec.get("owner_id"):
        reject("S06.4", "self-review: reviewer_id equals owner_id")
    if not review.get("evidence_path"):
        reject("S06.4", "independent_review.evidence_path is missing")

    closure = rec.get("human_closure", {})
    decision = closure.get("decision")
    if closure.get("authority_id") != rec.get("decision_authority_id"):
        reject("S06.5", f"human_closure.authority_id {closure.get('authority_id')!r} is not the "
                        f"decision authority {rec.get('decision_authority_id')!r}")
    if decision not in ("ACCEPT_REMEDIATED", "ACCEPT_RESEARCH_DISPOSITION"):
        reject("S06.5", f"human_closure.decision is {decision!r}")
    elif decision == "ACCEPT_RESEARCH_DISPOSITION" and ctype != "RESEARCH_ONLY":
        reject("S06.5", "ACCEPT_RESEARCH_DISPOSITION is legal only for RESEARCH_ONLY")
    if not closure.get("decided_at") or not closure.get("rationale"):
        reject("S06.5", "human_closure needs decided_at and rationale")

    commits = rec.get("evidence_merge_commits", [])
    if not commits:
        reject("S06.6", "closed record names no evidence_merge_commits")
    for commit in commits:
        code, _ = _git(git_root, "cat-file", "-e", f"{commit}^{{commit}}")
        if code != 0:
            reject("S06.6", f"evidence commit {commit} does not exist in the repository")
            continue
        code, _ = _git(git_root, "merge-base", "--is-ancestor", commit, "HEAD")
        if code != 0:
            reject("S06.6", f"evidence commit {commit} is not merged (not an ancestor of HEAD)")

    limitations = rec.get("limitations", [])
    for limitation in limitations:
        if _is_placeholder(str(limitation)):
            reject("S06.7", f"unbounded limitation (empty or placeholder): {limitation!r}")

    reopen = rec.get("reopen_if", [])
    if not reopen:
        reject("S06.8", "closed record has an empty reopen_if")
    for condition in reopen:
        if _is_placeholder(str(condition)):
            reject("S06.8", f"reopen_if condition is not concrete: {condition!r}")

    # S06.9 release pin (closure condition 9) and the retained candidate pin
    _check_enforcement(rec, ctx, True, reject)

    # S14 closure attestation (corrective-spec-002 CS-9)
    _check_attestation(cp, rec, ctx, reject)

    # S09 dependencies
    if row is not None and row["depends"] not in ("", "—", "-"):
        for dep in re.findall(r"CP-\d{2}", row["depends"]):
            dep_rec = records.get(dep)
            if dep_rec is None or not dep_rec.get("closed"):
                reject("S09", f"depends on {dep}, which is not closed")


def _closure_only_problems(plan: Path, git_root: Path, records: dict[str, dict[str, Any]],
                           base: str, head: str, only: str | None = None) -> list[Problem]:
    """S10 over ``base..head``: if the range flips a closed record (or creates it
    closed) it may touch closure paths only. ``only`` restricts the records
    considered to one checkpoint (an attested range belongs to its record)."""
    code, out = _git(git_root, "diff-tree", "-r", "--name-only", base, head)
    if code != 0:
        raise CouldNotRun(f"git diff-tree {base[:12]} {head[:12]} failed: {out}")
    changed = [line.strip() for line in out.splitlines() if line.strip() and not HEX40.match(line.strip())]
    plan_rel = plan.resolve().relative_to(git_root).as_posix()
    closing: list[str] = []
    for cp, rec in records.items():
        if not rec.get("closed") or (only is not None and cp != only):
            continue
        rel = f"{plan_rel}/checkpoints/{cp}.yaml"
        before = _blob(git_root, base, rel)
        if before is None:
            closing.append(cp)      # record created closed inside the range
            continue
        try:
            before_closed = bool(yaml.safe_load(before.decode("utf-8")).get("closed"))
        except Exception:      # noqa: BLE001 - an unreadable base record is a closing range
            before_closed = False
        if not before_closed:
            closing.append(cp)
    if not closing:
        return []
    problems: list[Problem] = []
    allowed_prefix = f"{plan_rel}/"
    for path in changed:
        inside = path.startswith(allowed_prefix)
        closure_file = inside and (
            path.startswith(f"{plan_rel}/checkpoints/") and path.endswith((".yaml", "MANIFEST.sha256"))
            or path.endswith(CLOSURE_ONLY_SUFFIXES) and path.count("/") == plan_rel.count("/") + 1
        )
        if not closure_file:
            problems.append(Problem(",".join(closing), "S10",
                                    f"closure-only diff {base[:12]}..{head[:12]} also changes {path}"))
    return problems


def _resolve_range(git_root: Path, diff_range: str) -> tuple[str, str]:
    if ".." not in diff_range:
        raise CouldNotRun(f"--diff needs <base>..<head>, got {diff_range!r}")
    base, _, head = diff_range.partition("..")
    code, base_sha = _git(git_root, "rev-parse", "--verify", f"{base}^{{commit}}")
    if code != 0:
        raise CouldNotRun(f"range base {base!r} does not resolve: {base_sha}")
    code, head_sha = _git(git_root, "rev-parse", "--verify", f"{head}^{{commit}}")
    if code != 0:
        raise CouldNotRun(f"range head {head!r} does not resolve: {head_sha}")
    return base_sha, head_sha


def _check_diff(ctx: Context, records: dict[str, dict[str, Any]], diff_range: str | None,
                problems: list[Problem]) -> None:
    """S10 and the CS-9.5 range rule. Installed mode: every attested range is
    checked and a caller range must equal one of them. Staged mode (no
    attestation can be checked, and every closed record is already rejected): a
    caller range, if any, is checked as before, for the reviewer's information."""
    plan, git_root = ctx.plan, ctx.git_root
    caller: tuple[str, str] | None = None
    if diff_range:
        caller = _resolve_range(git_root, diff_range)
    for cp, (base, head) in ctx.attested.items():
        problems.extend(_closure_only_problems(plan, git_root, records, base, head, only=cp))
    if caller is None:
        return
    if ctx.release_root is not None:
        if caller not in ctx.attested.values():
            attested = ", ".join(f"{b[:12]}..{h[:12]}" for b, h in ctx.attested.values()) or "none"
            problems.append(Problem("PLAN", "S14", f"--diff {caller[0][:12]}..{caller[1][:12]} differs from every "
                                                   f"attested closure range ({attested})"))
        return
    base, head = caller
    code, _ = _git(git_root, "merge-base", "--is-ancestor", base, head)
    if code != 0 or base == head:
        problems.append(Problem("PLAN", "S10", f"range base {base[:12]} is not a proper ancestor of head"))
        return
    problems.extend(_closure_only_problems(plan, git_root, records, base, head))


# ---------- entry ----------

def validate_plan(plan: Path, diff_range: str | None = None,
                  release_fs: ReleaseFS | None = None) -> Report:
    """Validate every record of ``plan``. ``release_fs`` is the in-process test seam
    of CS-1.7 (filesystem view, executing root, attestation directory); the CLI
    never sets it."""
    fs = release_fs or ReleaseFS()
    plan = Path(plan)
    readme = plan / "README.md"
    checkpoints = plan / "checkpoints"
    if not readme.is_file():
        raise CouldNotRun(f"plan README not found: {readme}")
    if not checkpoints.is_dir():
        raise CouldNotRun(f"checkpoints directory not found: {checkpoints}")
    release_root = fs.executing_root(Path(__file__))
    identity: dict[str, Any] | None = None
    identity_problems: list[str] = []
    schema_dir = _schema_dir(release_root)
    if release_root is not None:
        # Installed mode: the release verifies itself before any record is read.
        tree_problems, _ = verify_release_tree(release_root, fs)
        if tree_problems:
            raise CouldNotRun("installed release fails verification: " + "; ".join(tree_problems[:5]))
        identity, identity_problems = _read_release_identity(release_root, fs, schema_dir)
    schema_path = schema_dir / SCHEMA_NAME
    if not schema_path.is_file():
        raise CouldNotRun(f"schema not found: {schema_path}")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    attestation_validator = None
    attestation_schema = schema_dir / ATTESTATION_SCHEMA_NAME
    if attestation_schema.is_file():
        try:
            attestation_validator = Draft202012Validator(json.loads(attestation_schema.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, Exception):      # noqa: BLE001 - an unusable schema means no attestation passes
            attestation_validator = None
    root = _git_root(plan)
    header = _parse_readme(readme)
    ctx = Context(fs=fs, plan=plan, git_root=root, header=header, release_root=release_root,
                  identity=identity, identity_problems=identity_problems,
                  attestation_validator=attestation_validator)
    problems: list[Problem] = []

    # S01 plan header
    if not header.decision_authority:
        problems.append(Problem("PLAN", "S01", "README names no `Decision authority`"))
    if not header.base_commit:
        problems.append(Problem("PLAN", "S01", "README names no 40-hex `Amendment base` or `Base commit`"))
    if not header.ledger:
        problems.append(Problem("PLAN", "S01", "README has no checkpoint ledger table"))

    # load + structural
    records: dict[str, dict[str, Any]] = {}
    files = sorted(checkpoints.glob("CP-*.yaml"))
    for path in files:
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            problems.append(Problem(path.stem, "SCHEMA", f"unparseable YAML: {exc}"))
            continue
        if not isinstance(data, dict):
            problems.append(Problem(path.stem, "SCHEMA", "record is not a mapping"))
            continue
        errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
        for error in errors:
            where = "/".join(str(part) for part in error.path) or "<root>"
            problems.append(Problem(path.stem, "SCHEMA", f"{where}: {error.message[:200]}"))
        cp = str(data.get("checkpoint_id", path.stem))
        if path.stem != cp:
            problems.append(Problem(path.stem, "S02", f"file name {path.name} does not match checkpoint_id {cp}"))
        if errors:
            continue
        records[cp] = data

    # S03: every ledger row has a record
    for cp in header.ledger:
        if cp not in records and not any(p.checkpoint == cp for p in problems):
            problems.append(Problem(cp, "S03", "ledger row has no record under checkpoints/"))

    # S11 adjacent manifest
    manifest = checkpoints / "MANIFEST.sha256"
    if not manifest.is_file():
        problems.append(Problem("PLAN", "S11", "checkpoints/MANIFEST.sha256 is missing"))
    else:
        entries = _read_manifest(manifest)
        if "MANIFEST.sha256" in entries:
            problems.append(Problem("PLAN", "S11", "checkpoints/MANIFEST.sha256 lists itself"))
        for path in files:
            digest = entries.get(path.name)
            if digest is None:
                problems.append(Problem(path.stem, "S11", f"{path.name} is not in checkpoints/MANIFEST.sha256"))
            elif digest != _sha256(path):
                problems.append(Problem(path.stem, "S11", f"{path.name} does not match its manifest digest"))
        for name in entries:
            if not (checkpoints / name).is_file():
                problems.append(Problem("PLAN", "S11", f"manifest entry missing on disk: {name}"))

    for cp, rec in records.items():
        _check_record(cp, rec, ctx, records, problems)

    _check_diff(ctx, records, diff_range, problems)

    problems.sort(key=lambda p: (p.checkpoint, p.rule, p.message))
    return Report(plan=str(plan), records=len(records), problems=problems)
