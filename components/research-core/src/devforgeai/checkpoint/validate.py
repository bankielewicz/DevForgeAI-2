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
                       the release pin: ``enforcement.trust_stage`` PROTECTED_RELEASE,
                       every release field non-null, executable absolute and outside
                       the repository, local digests equal when the files exist, both
                       provider proofs bound to the executable digest
  S07 open record      an open record carries no human closure decision
  S08 admission        ``ADMITTED`` only after CP-00 closed; admitted entries carry evidence
  S09 dependencies     a closed checkpoint's dependencies are closed
  S10 closure diff     a diff that closes a record touches closure paths only
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

Rules S06 and S10 need Git; when Git or the repository is unavailable the run
is ``COULD_NOT_RUN`` (exit 3), never a pass.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

import yaml
from jsonschema import Draft202012Validator

SCHEMA_NAME = "research-gap-checkpoint.schema.json"
PLACEHOLDERS = ("TODO", "TBD", "{{", "}}", "<fill in>", "lorem ipsum")
CLOSURE_ONLY_SUFFIXES = ("README.md", "MANIFEST.sha256")
LEDGER_HEADER = re.compile(r"^\|\s*ID\s*\|\s*Type\s*\|", re.I)
LEDGER_ROW = re.compile(r"^\|\s*(CP-\d{2})\s*\|")
HEX40 = re.compile(r"^[0-9a-f]{40}$")


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


def _find_schema(plan: Path, override: Path | None) -> Path:
    if override is not None:
        if not override.is_file():
            raise CouldNotRun(f"schema not found: {override}")
        return override
    for ancestor in (plan.resolve(), *plan.resolve().parents):
        candidate = ancestor / "schemas" / "devforgeai" / "v1" / SCHEMA_NAME
        if candidate.is_file():
            return candidate
    for ancestor in Path(__file__).resolve().parents:
        candidate = ancestor / "schemas" / "devforgeai" / "v1" / SCHEMA_NAME
        if candidate.is_file():
            return candidate
    raise CouldNotRun(f"{SCHEMA_NAME} not found above {plan} or above the validator")


def _git(root: Path, *argv: str) -> tuple[int, str]:
    try:
        completed = subprocess.run(["git", "-C", str(root), *argv],
                                   capture_output=True, text=True, timeout=60)
    except FileNotFoundError as exc:
        raise CouldNotRun("git is not installed") from exc
    except subprocess.TimeoutExpired as exc:
        raise CouldNotRun(f"git {argv[0]} timed out") from exc
    return completed.returncode, (completed.stdout + completed.stderr).strip()


def _git_root(plan: Path, override: Path | None) -> Path:
    if override is not None:
        root = override.resolve()
    else:
        code, out = _git(plan.resolve(), "rev-parse", "--show-toplevel")
        if code != 0:
            raise CouldNotRun(f"{plan} is not inside a Git repository: {out}")
        root = Path(out.splitlines()[0]).resolve()
    code, out = _git(root, "rev-parse", "--is-inside-work-tree")
    if code != 0 or out.splitlines()[-1] != "true":
        raise CouldNotRun(f"{root} is not a Git work tree: {out}")
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



def _blob_sha256(git_root: Path, commit: str, name: str) -> str | None:
    """SHA-256 of the exact bytes of ``name`` at ``commit``; None when absent."""
    try:
        completed = subprocess.run(["git", "-C", str(git_root), "show", f"{commit}:{name}"],
                                   capture_output=True, timeout=60)
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise CouldNotRun(f"git show {commit}:{name} failed: {exc}") from exc
    if completed.returncode != 0:
        return None
    return hashlib.sha256(completed.stdout).hexdigest()


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


def _check_enforcement(rec: dict[str, Any], plan: Path, git_root: Path,
                       closed: bool, reject: Any) -> None:
    """S13 (open record) and S06.9 (closure): the candidate and release pins."""
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
            _check_release_pin(rec, release, git_root, closed_rule, reject)


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


def _check_release_pin(rec: dict[str, Any], release: dict[str, Any], git_root: Path,
                       rule: str, reject: Any) -> None:
    executable = str(release["executable_path"])
    if not executable.startswith("/") or ".." in PurePosixPath(executable).parts:
        reject(rule, f"executable_path must be absolute without `..` (no PATH resolution): {executable}")
    else:
        try:
            inside = Path(executable).resolve().is_relative_to(git_root.resolve())
        except (OSError, ValueError):
            inside = False
        if inside:
            reject(rule, f"executable_path is inside the repository (project-local fallback): {executable}")
        exe = Path(executable)
        if exe.is_file() and _sha256(exe) != release["executable_sha256"]:
            reject(rule, f"executable digest mismatch at {executable}")
    for label in ("promotion_evidence_path", "permissions_evidence_path"):
        value = str(release[label])
        digest = release[label.replace("_path", "_sha256")]
        if value.startswith("/"):
            target = Path(value)
        elif why := _bad_relative(value):
            reject(rule, f"{label}: {why}: {value}")
            continue
        else:
            target = git_root / value
            if not target.is_file():
                reject(rule, f"{label} missing on disk: {value}")
                continue
        if target.is_file() and _sha256(target) != digest:
            reject(rule, f"{label} digest mismatch: {value}")
    if not rec.get("enforcement", {}).get("candidate", {}).get("source_commit"):
        reject(rule, "release pin without the retained candidate pin (candidate/release mapping)")
    proofs = rec.get("provider_proof", {})
    passing = {name: proof for name, proof in proofs.items() if proof.get("status") == "PASS"}
    bound = {proof.get("subject_sha256") for proof in passing.values()}
    if rec.get("checkpoint_type") != "RESEARCH_ONLY" and set(passing) != {"claude", "codex"}:
        reject(rule, "release pin needs both provider proofs PASS and bound to it")
    elif bound and bound != {release["executable_sha256"]}:
        reject(rule, "provider proofs are not both bound to the release executable digest")


# ---------- plan README ----------

@dataclass
class PlanHeader:
    decision_authority: str | None
    base_commit: str | None
    ledger: dict[str, dict[str, str]]   # id -> {"closed": "true"/"false", "depends": "…"}


def _parse_readme(readme: Path) -> PlanHeader:
    authority = base = None
    ledger: dict[str, dict[str, str]] = {}
    in_ledger = False
    columns: list[str] = []
    for line in readme.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("| Decision authority |"):
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
    return PlanHeader(authority, base, ledger)


# ---------- rules ----------

def _check_record(cp: str, rec: dict[str, Any], header: PlanHeader, plan: Path,
                  git_root: Path, records: dict[str, dict[str, Any]],
                  problems: list[Problem]) -> None:
    def reject(rule: str, message: str) -> None:
        problems.append(Problem(cp, rule, message))

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
        _check_enforcement(rec, plan, git_root, False, reject)
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
    _check_enforcement(rec, plan, git_root, True, reject)

    # S09 dependencies
    if row is not None and row["depends"] not in ("", "—", "-"):
        for dep in re.findall(r"CP-\d{2}", row["depends"]):
            dep_rec = records.get(dep)
            if dep_rec is None or not dep_rec.get("closed"):
                reject("S09", f"depends on {dep}, which is not closed")


def _check_diff(plan: Path, git_root: Path, checkpoints: Path, records: dict[str, dict[str, Any]],
                diff_range: str, problems: list[Problem]) -> None:
    """S10: a diff that flips any record to closed may touch closure paths only."""
    if ".." not in diff_range:
        raise CouldNotRun(f"--diff needs <base>..<head>, got {diff_range!r}")
    base, _, head = diff_range.partition("..")
    code, out = _git(git_root, "diff", "--name-only", diff_range)
    if code != 0:
        raise CouldNotRun(f"git diff {diff_range} failed: {out}")
    changed = [line.strip() for line in out.splitlines() if line.strip()]
    plan_rel = plan.resolve().relative_to(git_root).as_posix()
    closing: list[str] = []
    for cp, rec in records.items():
        if not rec.get("closed"):
            continue
        rel = f"{plan_rel}/checkpoints/{cp}.yaml"
        code, before = _git(git_root, "show", f"{base}:{rel}")
        if code != 0:
            closing.append(cp)      # record created closed inside the diff
            continue
        try:
            before_closed = bool(yaml.safe_load(before).get("closed"))
        except Exception:      # noqa: BLE001 - an unreadable base record is a closing diff
            before_closed = False
        if not before_closed:
            closing.append(cp)
    if not closing:
        return
    allowed_prefix = f"{plan_rel}/"
    for path in changed:
        inside = path.startswith(allowed_prefix)
        closure_file = inside and (
            path.startswith(f"{plan_rel}/checkpoints/") and path.endswith((".yaml", "MANIFEST.sha256"))
            or path.endswith(CLOSURE_ONLY_SUFFIXES) and path.count("/") == plan_rel.count("/") + 1
        )
        if not closure_file:
            problems.append(Problem(
                ",".join(closing), "S10",
                f"closure-only diff {diff_range} also changes {path}"))


# ---------- entry ----------

def validate_plan(plan: Path, git_root: Path | None = None, schema_path: Path | None = None,
                  diff_range: str | None = None) -> Report:
    plan = Path(plan)
    readme = plan / "README.md"
    checkpoints = plan / "checkpoints"
    if not readme.is_file():
        raise CouldNotRun(f"plan README not found: {readme}")
    if not checkpoints.is_dir():
        raise CouldNotRun(f"checkpoints directory not found: {checkpoints}")
    schema = json.loads(_find_schema(plan, schema_path).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    root = _git_root(plan, git_root)
    header = _parse_readme(readme)
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
        _check_record(cp, rec, header, plan, root, records, problems)

    if diff_range:
        _check_diff(plan, root, checkpoints, records, diff_range, problems)

    problems.sort(key=lambda p: (p.checkpoint, p.rule, p.message))
    return Report(plan=str(plan), records=len(records), problems=problems)
