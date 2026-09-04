"""CP-00: positive and hostile subprocess tests for `python3 -m devforgeai.checkpoint validate`.

Every case runs the validator as a subprocess against a scratch plan inside a
scratch Git repository, so the Git rules (merged evidence, candidate pin,
closure-only diff) are deterministic and offline. The last test validates this
repository's own plan records.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "components" / "research-core" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
from devforgeai.checkpoint.validate import ReleaseFS, validate_plan  # noqa: E402
SCHEMA = ROOT / "schemas" / "devforgeai" / "v1" / "research-gap-checkpoint.schema.json"
REAL_PLAN = ROOT / "docs" / "research" / "spec-driven-development-gap-closure"
AUTH = "github:test-authority"
COMMIT = "0" * 40
SHA = "1" * 64
CANDIDATE_MANIFEST = "framework/contracts/MANIFEST.sha256"

README = """# Scratch plan

| Field | Value |
|---|---|
| Plan ID | `SCRATCH` |
| Amendment base | `{base}` |
| Decision authority | `{auth}` |

## 9. Checkpoint ledger

| ID | Type | Gap | Depends on | Closed | Current verification |
|---|---|---|---|---:|---|
| CP-00 | RESEARCH_AND_IMPLEMENTATION | custody | — | {cp00} | NOT_RUN |
| CP-01 | RESEARCH_AND_IMPLEMENTATION | providers | CP-00 | {cp01} | NOT_RUN |
| CP-13 | RESEARCH_ONLY | domain | CP-00 | {cp13} | NOT_RUN |
"""

RELEASE_FIELDS = ("version", "source_commit", "promotion_evidence_path", "promotion_evidence_sha256",
                  "executable_path", "executable_sha256", "schema_set_version", "schema_set_sha256",
                  "contract_policy_version", "contract_policy_sha256", "installation_owner",
                  "permissions_evidence_path", "permissions_evidence_sha256")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class FakeProtectedFS(ReleaseFS):
    """CS-1.7 seam: objects under the listed protected roots (and their ancestors)
    read as owned by uid 0 with no group/other write; bytes and symlinks are real.
    `executing_root` plays the release root the validator runs from (CS-6.1) and
    `attest_root` the fixed attestation directory (CS-9.2). In-process only."""

    def __init__(self, protected: list[Path] | None = None, executing_root: Path | None = None,
                 attest_root: Path | None = None) -> None:
        self.protected = [Path(p).resolve() for p in (protected or [])]
        self._executing_root = executing_root
        if attest_root is not None:
            self.attest_root = attest_root

    def _masked(self, path: Path) -> bool:
        resolved = Path(path).resolve()
        return any(resolved == root or resolved in root.parents or resolved.is_relative_to(root)
                   for root in self.protected)

    def lstat(self, path: Path) -> os.stat_result:
        st = os.lstat(path)
        if os.path.islink(path) or not self._masked(path):
            return st
        masked = (st.st_mode & ~0o022, st.st_ino, st.st_dev, st.st_nlink, 0, 0,
                  st.st_size, st.st_atime, st.st_mtime, st.st_ctime)
        return os.stat_result(masked)

    def executing_root(self, module_file: Path) -> Path | None:
        return self._executing_root


def run_inprocess(plan: Path, diff_range: str | None = None, scratch: "Scratch | None" = None,
                  fs: ReleaseFS | None = None):
    """The positive protected path: in-process, seam injected. Returns the report.
    A validator that refuses to run (any exception) is a failed assertion, so a
    red run records it as such rather than as an error."""
    if fs is None:
        assert scratch is not None
        fs = scratch.fake()
    try:
        return validate_plan(plan, diff_range=diff_range, release_fs=fs)
    except Exception as exc:      # noqa: BLE001
        raise AssertionError(f"validator refused to run: {type(exc).__name__}: {exc}") from exc


def admitted_input(**overrides: object) -> dict:
    entry = {
        "input_id": "IN-001", "state": "AVAILABLE_FOR_ADMISSION", "source_commit": COMMIT,
        "subject": "docs/x.md", "subject_sha256": SHA,
        "provider": "p", "provider_version": "1", "command": "c", "result": "r",
        "evidence_paths": [], "limitations": []}
    entry.update(overrides)
    return entry


def open_record(cp: str, ctype: str = "RESEARCH_AND_IMPLEMENTATION") -> dict:
    return {
        "checkpoint_id": cp,
        "checkpoint_type": ctype,
        "closed": False,
        "attempt_outcome": None,
        "owner_id": "agent:owner",
        "decision_authority_id": AUTH,
        "base_commit": COMMIT,
        "admitted_inputs": [],
        "closure_stages": {"researched": "NOT_RUN", "implemented": "NOT_RUN", "proven": "NOT_RUN"},
        "research": {"dossier_path": f"docs/research/{cp.lower()}", "manifest_sha256": None,
                     "verification_ids": []},
        "implementation": {"governing_decision_ids": [],
                           "changed_contracts": ["schemas/devforgeai/v1/*.schema.json"],
                           "changed_runtime_paths": ["src/**"], "test_evidence": []},
        "enforcement": {
            "trust_stage": "UNBOUND",
            "candidate": {"source_commit": None, "manifest_path": None, "manifest_sha256": None},
            "protected_release": {name: None for name in RELEASE_FIELDS},
        },
        "provider_proof": {"claude": {"status": "NOT_RUN", "evidence_path": None, "subject_sha256": None},
                           "codex": {"status": "NOT_RUN", "evidence_path": None, "subject_sha256": None}},
        "independent_review": {"reviewer_id": None, "verdict": None, "evidence_path": None},
        "human_closure": {"authority_id": None, "decision": None, "rationale": None, "decided_at": None},
        "evidence_merge_commits": [],
        "limitations": ["Not started."],
        "reopen_if": [],
    }


class Scratch:
    """A scratch Git repository holding a plan, a schema, a candidate and one dossier."""

    def __init__(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="dfai-cp00-")
        self._ext = tempfile.TemporaryDirectory(prefix="dfai-cp00-ext-")
        self.root = Path(self._tmp.name)
        # A release tree outside every agent-writable workspace, laid out as
        # components/devforge-release/INSTALLED-LAYOUT.md requires. It is
        # user-owned here: the subprocess path must reject it (CS-1.3) and
        # only the in-process seam of CS-1.7 may present it as root-owned.
        self.release_root = Path(self._ext.name) / "devforge" / "1.0.0-test"
        self.executable = self.release_root / "bin" / "devforge"
        # The fixed attestation directory (CS-9.2), played by the seam only.
        self.attest_root = Path(self._ext.name) / "var" / "lib" / "devforge" / "attest"
        self.identity: dict = {
            "identity_format": "devforge-release-identity/v1",
            "version": "1.0.0", "devforge_commit": COMMIT, "devforge_tag": "v1.0.0",
            "candidate_repository": "https://example.invalid/DevForgeAI",
            "candidate_checkpoint_id": "CP-00",
            "candidate_source_commit": COMMIT, "candidate_manifest_sha256": SHA,
            "schema_set_version": "v1", "contract_policy_version": "1",
            "launcher_toolchain": "rustc 0.0.0 (fixture)", "built_at": "2026-09-04T00:00:00Z",
        }
        self.write_release_tree()
        (self.root / "schemas" / "devforgeai" / "v1").mkdir(parents=True)
        shutil.copy2(SCHEMA, self.root / "schemas" / "devforgeai" / "v1" / SCHEMA.name)
        (self.root / "src").mkdir()
        (self.root / "src" / "validator.py").write_text("print('candidate')\n", encoding="utf-8")
        (self.root / "framework" / "contracts").mkdir(parents=True)
        self.plan = self.root / "docs" / "research" / "scratch-plan"
        self.checkpoints = self.plan / "checkpoints"
        self.checkpoints.mkdir(parents=True)
        self.git("init", "-q")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "user.name", "fixture")
        self.records: dict[str, dict] = {
            "CP-00": open_record("CP-00"),
            "CP-01": open_record("CP-01"),
            "CP-13": open_record("CP-13", "RESEARCH_ONLY"),
        }

    def cleanup(self) -> None:
        self._tmp.cleanup()
        self._ext.cleanup()

    def write_release_tree(self, manifest_entries: list[str] | None = None,
                           root: Path | None = None, identity: bool = True) -> None:
        """Write the installed layout (layout contract v2): bin/devforge, lib/,
        schemas/, contracts/MANIFEST.sha256 (the candidate manifest once pinned),
        RELEASE-IDENTITY.json, RELEASE.sha256."""
        root = root or self.release_root
        for sub in ("bin", "lib/devforgeai/checkpoint", "schemas/devforgeai/v1", "contracts"):
            (root / sub).mkdir(parents=True, exist_ok=True)
        (root / "bin" / "devforge").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        (root / "bin" / "devforge").chmod(0o755)
        (root / "bin" / "devforge-checkpoint.py").write_text("# launcher\n", encoding="utf-8")
        (root / "bin" / "devforge-checkpoint.py").chmod(0o755)
        (root / "lib" / "devforgeai" / "__init__.py").write_text("", encoding="utf-8")
        (root / "lib" / "devforgeai" / "checkpoint" / "validate.py").write_text("# installed copy\n", encoding="utf-8")
        shutil.copy2(SCHEMA, root / "schemas" / "devforgeai" / "v1" / SCHEMA.name)
        for name in ("release-identity.schema.json", "closure-attestation.schema.json"):
            source = SCHEMA.parent / name
            (root / "schemas" / "devforgeai" / "v1" / name).write_text(
                source.read_text(encoding="utf-8") if source.is_file() else "{}\n", encoding="utf-8")
        candidate = self.root / CANDIDATE_MANIFEST
        (root / "contracts" / "MANIFEST.sha256").write_bytes(
            candidate.read_bytes() if candidate.is_file() else f"{SHA}  schemas/devforgeai/v1/{SCHEMA.name}\n".encode())
        identity_file = root / "RELEASE-IDENTITY.json"
        if identity:
            identity_file.write_text(json.dumps(self.identity, indent=2) + "\n", encoding="utf-8")
        elif identity_file.exists():
            identity_file.unlink()
        files = [q for q in sorted(root.rglob("*")) if q.is_file() and q.name != "RELEASE.sha256"]
        lines = manifest_entries if manifest_entries is not None else [
            f"{sha256(q)}  {q.relative_to(root).as_posix()}" for q in files]
        (root / "RELEASE.sha256").write_text("# scratch release\n" + "\n".join(lines) + "\n", encoding="utf-8")
        if root == self.release_root:
            self.exe_sha = sha256(root / "bin" / "devforge")
            self.schema_sha = sha256(root / "schemas" / "devforgeai" / "v1" / SCHEMA.name)
            self.policy_sha = sha256(root / "contracts" / "MANIFEST.sha256")

    def fake(self, executing_root: Path | None = None, protected: list[Path] | None = None) -> FakeProtectedFS:
        """The seam for this scratch: release tree and attestation directory read as root-owned."""
        return FakeProtectedFS(
            protected=protected if protected is not None else [self.release_root.parent, self.attest_root],
            executing_root=executing_root or self.release_root,
            attest_root=self.attest_root)

    def repository_identity(self) -> tuple[str, list[str]]:
        roots = sorted(self.git("rev-list", "--max-parents=0", "HEAD").split())
        return hashlib.sha256("\n".join(roots).encode()).hexdigest(), roots

    def attest(self, cp: str, base: str, head: str, **overrides: object) -> Path:
        """Mint a closure attestation the way `devforge checkpoint attest` does (CS-9.1),
        into the fixed location under the seam's attest_root (CS-9.2)."""
        identity, roots = self.repository_identity()
        plan_rel = self.plan.relative_to(self.root).as_posix()
        record_rel = f"{plan_rel}/checkpoints/{cp}.yaml"
        blob = subprocess.run(["git", "-C", str(self.root), "cat-file", "blob", f"{head}:{record_rel}"],
                              capture_output=True, check=True).stdout
        document = {
            "attestation_format": "devforge-closure-attestation/v1",
            "repository_identity": identity, "repository_root_commits": roots,
            "plan_path": plan_rel, "plan_id": "SCRATCH", "checkpoint_id": cp, "record_path": record_rel,
            "base_commit": base, "head_commit": head,
            "record_sha256": hashlib.sha256(blob).hexdigest(),
            "release_root": str(self.release_root),
            "release_identity_sha256": (sha256(self.release_root / "RELEASE-IDENTITY.json")
                                        if (self.release_root / "RELEASE-IDENTITY.json").is_file() else "0" * 64),
            "authority_id": AUTH, "review_reference": "https://example.invalid/pull/1#review",
            "minted_at": "2026-09-04T00:00:00Z", "minted_by_uid": 0,
        }
        document.update(overrides)
        target = self.attest_root / identity[:32] / "SCRATCH" / f"{cp}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
        return target

    def git(self, *argv: str) -> str:
        completed = subprocess.run(["git", "-C", str(self.root), *argv],
                                   capture_output=True, text=True, check=True)
        return completed.stdout.strip()

    def commit(self, message: str = "scratch") -> str:
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", message)
        return self.git("rev-parse", "HEAD")

    def write_dossier(self, cp: str, verification_outcome: str = "PASS") -> str:
        dossier = self.root / self.records[cp]["research"]["dossier_path"]
        dossier.mkdir(parents=True, exist_ok=True)
        (dossier / "README.md").write_text(f"# dossier {cp}\n", encoding="utf-8")
        (dossier / "evidence").mkdir(exist_ok=True)
        (dossier / "evidence" / "probe.txt").write_text("exit 0\n", encoding="utf-8")
        (dossier / "evidence" / "promotion.txt").write_text("release 1.0.0 promoted\n", encoding="utf-8")
        (dossier / "evidence" / "permissions.txt").write_text("-r-xr-xr-x root root\n", encoding="utf-8")
        (dossier / "verification.jsonl").write_text(json.dumps({
            "verification_id": "V-01", "claim_ids": ["C-01"], "verifier": "agent:reviewer",
            "outcome": verification_outcome}) + "\n", encoding="utf-8")
        lines = []
        for path in sorted(dossier.rglob("*")):
            if path.is_file() and path.name != "MANIFEST.sha256":
                lines.append(f"{sha256(path)}  ./{path.relative_to(dossier).as_posix()}")
        manifest = dossier / "MANIFEST.sha256"
        manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return sha256(manifest)

    def write_candidate(self, cp: str, omit: str | None = None) -> str:
        """Pin the candidate bytes: write the manifest, commit, record the pin."""
        files = ["schemas/devforgeai/v1/research-gap-checkpoint.schema.json", "src/validator.py"]
        lines = [f"{sha256(self.root / f)}  {f}" for f in files if f != omit]
        manifest = self.root / CANDIDATE_MANIFEST
        manifest.write_text("# scratch candidate\n" + "\n".join(lines) + "\n", encoding="utf-8")
        commit = self.commit("candidate")
        self.records[cp]["enforcement"]["candidate"] = {
            "source_commit": commit, "manifest_path": CANDIDATE_MANIFEST,
            "manifest_sha256": sha256(manifest)}
        return commit

    def stage_candidate(self, cp: str, omit: str | None = None) -> str:
        commit = self.write_candidate(cp, omit)
        rec = self.records[cp]
        rec["enforcement"]["trust_stage"] = "STAGED_CANDIDATE"
        rec["closure_stages"]["implemented"] = "PASS"
        return commit

    def research_pass(self, cp: str, verification_outcome: str = "PASS") -> None:
        rec = self.records[cp]
        rec["research"]["manifest_sha256"] = self.write_dossier(cp, verification_outcome)
        rec["research"]["verification_ids"] = ["V-01"]
        rec["closure_stages"]["researched"] = "PASS"

    def close(self, cp: str, merged_commit: str, ctype: str | None = None) -> dict:
        """Fill every closure field of `cp` legally."""
        rec = self.records[cp]
        ctype = ctype or rec["checkpoint_type"]
        rec.update({
            "closed": True,
            "attempt_outcome": "COMPLETE",
            "evidence_merge_commits": [merged_commit],
            "limitations": ["Scratch fixture only; one provider version."],
            "reopen_if": ["The provider version changes."],
        })
        rec["research"]["manifest_sha256"] = self.write_dossier(cp)
        rec["research"]["verification_ids"] = ["V-01"]
        dossier = rec["research"]["dossier_path"]
        if not rec["enforcement"]["candidate"]["source_commit"]:
            self.write_candidate(cp)
        # The release identity binds the candidate of the checkpoint it was built
        # from (CS-6.4) and the installed policy is that candidate manifest itself.
        candidate = rec["enforcement"]["candidate"]
        if cp == self.identity["candidate_checkpoint_id"]:
            self.identity.update(candidate_source_commit=candidate["source_commit"],
                                 candidate_manifest_sha256=candidate["manifest_sha256"])
        self.write_release_tree()
        rec["enforcement"]["trust_stage"] = "PROTECTED_RELEASE"
        rec["enforcement"]["protected_release"] = {
            "version": "1.0.0", "source_commit": COMMIT,
            "promotion_evidence_path": f"{dossier}/evidence/promotion.txt",
            "promotion_evidence_sha256": sha256(self.root / dossier / "evidence" / "promotion.txt"),
            "executable_path": str(self.executable), "executable_sha256": self.exe_sha,
            "schema_set_version": "v1", "schema_set_sha256": self.schema_sha,
            "contract_policy_version": "1", "contract_policy_sha256": self.policy_sha,
            "installation_owner": "root",
            "permissions_evidence_path": f"{dossier}/evidence/permissions.txt",
            "permissions_evidence_sha256": sha256(self.root / dossier / "evidence" / "permissions.txt"),
        }
        if ctype == "RESEARCH_ONLY":
            rec["closure_stages"] = {"researched": "PASS", "implemented": "NOT_APPLICABLE",
                                     "proven": "NOT_APPLICABLE"}
            rec["human_closure"]["decision"] = "ACCEPT_RESEARCH_DISPOSITION"
        elif ctype == "EXPERIMENT":
            rec["closure_stages"] = {"researched": "PASS", "implemented": "NOT_APPLICABLE", "proven": "PASS"}
            rec["human_closure"]["decision"] = "ACCEPT_REMEDIATED"
        else:
            rec["closure_stages"] = {"researched": "PASS", "implemented": "PASS", "proven": "PASS"}
            rec["human_closure"]["decision"] = "ACCEPT_REMEDIATED"
        if ctype != "RESEARCH_ONLY":
            for provider in ("claude", "codex"):
                rec["provider_proof"][provider] = {
                    "status": "PASS",
                    "evidence_path": f"{dossier}/evidence/probe.txt",
                    "subject_sha256": self.exe_sha,
                }
        rec["independent_review"] = {"reviewer_id": "agent:reviewer", "verdict": "PASS",
                                     "evidence_path": f"{dossier}/README.md"}
        rec["human_closure"].update({"authority_id": AUTH, "rationale": "Scratch acceptance.",
                                     "decided_at": "2026-09-04T00:00:00Z"})
        return rec

    def materialize(self) -> None:
        closed = {cp: str(rec["closed"]).lower() for cp, rec in self.records.items()}
        (self.plan / "README.md").write_text(
            README.format(base=COMMIT, auth=AUTH, cp00=closed.get("CP-00", "false"),
                          cp01=closed.get("CP-01", "false"), cp13=closed.get("CP-13", "false")),
            encoding="utf-8")
        for stale in self.checkpoints.glob("*"):
            stale.unlink()
        for cp, rec in self.records.items():
            (self.checkpoints / f"{cp}.yaml").write_text(
                yaml.safe_dump(rec, sort_keys=False), encoding="utf-8")
        lines = [f"{sha256(path)}  {path.name}" for path in sorted(self.checkpoints.glob("CP-*.yaml"))]
        (self.checkpoints / "MANIFEST.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_validator(plan: Path, *extra: str, env_extra: dict[str, str] | None = None) -> tuple[int, str]:
    env = dict(os.environ, PYTHONPATH=str(SRC), PYTHONDONTWRITEBYTECODE="1", **(env_extra or {}))
    completed = subprocess.run(
        [sys.executable, "-m", "devforgeai.checkpoint", "validate", "--plan", str(plan), *extra],
        capture_output=True, text=True, env=env, cwd=str(ROOT))
    return completed.returncode, completed.stdout + completed.stderr


class GapCheckpointValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scratch = Scratch()
        self.addCleanup(self.scratch.cleanup)

    # ---- positive ----

    def test_open_plan_passes(self) -> None:
        self.scratch.materialize()
        self.scratch.commit()
        code, out = run_validator(self.scratch.plan)
        self.assertEqual(code, 0, out)
        self.assertIn("3 record(s), 0 problem(s)", out)

    def _work_then_close(self, *cps: str, attest: bool = True) -> tuple[str, str]:
        """Work commit (dossiers, candidate, open records), the closure commit, then
        the attestation the protected host mints once the head is frozen (CS-9.3)."""
        for cp in cps:
            self.scratch.write_dossier(cp)
        self.scratch.write_candidate("CP-00")
        self.scratch.materialize()
        base = self.scratch.commit("work")
        for cp in cps:
            self.scratch.close(cp, base)
        self.scratch.materialize()
        head = self.scratch.commit("closure")
        if attest:
            for cp in cps:
                self.scratch.attest(cp, base, head)
        return base, head

    def test_complete_closed_record_passes(self) -> None:
        # CS-1.7: the positive protected case runs in-process through the seam.
        base, head = self._work_then_close("CP-00")
        report = run_inprocess(self.scratch.plan, f"{base}..{head}", self.scratch)
        self.assertEqual([str(p) for p in report.problems], [])
        self.assertEqual(report.outcome, "PASS")

    def test_research_only_disposition_passes(self) -> None:
        base, head = self._work_then_close("CP-00", "CP-13")
        report = run_inprocess(self.scratch.plan, f"{base}..{head}", self.scratch)
        self.assertEqual([str(p) for p in report.problems], [])

    def test_no_seam_from_the_cli(self) -> None:
        # The same closed plan through the subprocess path: the staged validator
        # has no executing release and the release tree is user-owned, so no CLI
        # flag or environment selects the seam.
        base, head = self._work_then_close("CP-00")
        code, out = run_validator(self.scratch.plan, "--diff", f"{base}..{head}")
        self.assertEqual(code, 1, out)
        self.assertIn("S06.9", out)

    def test_closed_record_rejected_by_staged_validator(self) -> None:         # CS-6.1
        base, head = self._work_then_close("CP-00")
        code, out = run_validator(self.scratch.plan, "--diff", f"{base}..{head}")
        self.assertEqual(code, 1, out)
        self.assertIn("decidable only by the installed validator", out)

    def test_closure_range_comes_from_attestation(self) -> None:               # CS-9.5
        # No --diff: the attested base..head is the closure range.
        self._work_then_close("CP-00")
        report = run_inprocess(self.scratch.plan, None, self.scratch)
        self.assertEqual([str(p) for p in report.problems], [])
        self.assertEqual(report.outcome, "PASS")

    def test_attestation_holds_after_later_commit(self) -> None:               # CS-9.6
        self._work_then_close("CP-00")
        (self.scratch.root / "unrelated.md").write_text("later\n", encoding="utf-8")
        self.scratch.commit("later work")
        report = run_inprocess(self.scratch.plan, None, self.scratch)
        self.assertEqual([str(p) for p in report.problems], [])

    def test_open_record_with_staged_candidate_and_research_holds(self) -> None:
        # The CP-00 work-PR state the amendment allows: researched and
        # implemented PASS with their evidence, proven NOT_RUN, STAGED_CANDIDATE.
        self.scratch.research_pass("CP-00")
        self.scratch.stage_candidate("CP-00")
        self.scratch.materialize()
        self.scratch.commit("pin")
        code, out = run_validator(self.scratch.plan)
        self.assertEqual(code, 0, out)

    def test_closure_only_diff_passes(self) -> None:
        # The work PR created the dossier, the candidate pin and its manifest;
        # the closure diff touches records, ledger and adjacent manifest only.
        base, head = self._work_then_close("CP-00")
        report = run_inprocess(self.scratch.plan, f"{base}..{head}", self.scratch)
        self.assertEqual([str(p) for p in report.problems if p.rule == "S10"], [])
        self.assertEqual(report.outcome, "PASS")

    def test_json_output_names_outcome(self) -> None:
        self.scratch.materialize()
        self.scratch.commit()
        code, out = run_validator(self.scratch.plan, "--json")
        self.assertEqual(code, 0, out)
        self.assertIn('"outcome": "PASS"', out)

    # ---- hostile: each mutation is rejected with its rule id ----

    def _closed_scratch(self) -> tuple[str, dict]:
        self.scratch.write_dossier("CP-00")
        self.scratch.write_candidate("CP-00")
        evidence = self.scratch.commit("evidence")
        rec = self.scratch.close("CP-00", evidence)
        return evidence, rec

    def _commit_and_attest(self) -> tuple[str | None, str]:
        """Commit the scratch state; for every closed record mint the attestation
        the protected host would (base = the previous commit, head = HEAD)."""
        self.scratch.materialize()
        head = self.scratch.commit()
        base = None
        closed = [cp for cp, rec in self.scratch.records.items() if rec["closed"]]
        if closed:
            base = self.scratch.git("rev-parse", "HEAD~1")
            for cp in closed:
                self.scratch.attest(cp, base, head)
        return base, head

    def _expect(self, rule: str, *needles: str) -> str:
        """Subprocess path (staged validator). A closed plan is given the range that
        matches its attestation; the staged validator still rejects it (CS-6.1) and
        reports every other problem it can decide."""
        base, head = self._commit_and_attest()
        extra = ("--diff", f"{base}..{head}") if base else ()
        code, out = run_validator(self.scratch.plan, *extra)
        self.assertEqual(code, 1, out)
        self.assertIn(rule, out)
        for needle in needles:
            self.assertIn(needle, out)
        return out

    def _expect_inprocess(self, rule: str, *needles: str, diff: str | None = None,
                          fs: ReleaseFS | None = None, attest: bool = True) -> list[str]:
        """Protected path through the seam: the executing release is the fixture's."""
        if attest:
            self._commit_and_attest()
        else:
            self.scratch.materialize()
            self.scratch.commit()
        report = run_inprocess(self.scratch.plan, diff, self.scratch, fs)
        problems = [str(p) for p in report.problems]
        matching = [p for p in problems if rule in p]
        self.assertTrue(matching, f"no {rule} problem; got {problems}")
        for needle in needles:
            self.assertTrue(any(needle in p for p in matching), f"{needle!r} not in {matching}")
        return problems

    def test_missing_authority_rejected(self) -> None:
        _, rec = self._closed_scratch()
        rec["human_closure"]["authority_id"] = None
        self._expect("S06.5")

    def test_wrong_authority_rejected(self) -> None:
        _, rec = self._closed_scratch()
        rec["human_closure"]["authority_id"] = "agent:owner"
        self._expect("S06.5", "not the decision authority")

    def test_missing_manifest_rejected(self) -> None:
        _, rec = self._closed_scratch()
        (self.scratch.root / rec["research"]["dossier_path"] / "MANIFEST.sha256").unlink()
        self._expect("S06.2", "manifest missing")

    def test_manifest_digest_mismatch_rejected(self) -> None:
        _, rec = self._closed_scratch()
        rec["research"]["manifest_sha256"] = "2" * 64
        self._expect("S06.2", "does not equal")

    def test_manifest_listing_itself_rejected(self) -> None:
        _, rec = self._closed_scratch()
        manifest = self.scratch.root / rec["research"]["dossier_path"] / "MANIFEST.sha256"
        manifest.write_text(manifest.read_text() + f"{'3' * 64}  ./MANIFEST.sha256\n")
        rec["research"]["manifest_sha256"] = sha256(manifest)
        self._expect("S06.2", "lists itself")

    def test_unmanifested_dossier_file_rejected(self) -> None:
        _, rec = self._closed_scratch()
        dossier = self.scratch.root / rec["research"]["dossier_path"]
        (dossier / "evidence" / "late-note.txt").write_text("unlisted\n", encoding="utf-8")
        self._expect("S06.2", "not in manifest: evidence/late-note.txt")

    def test_closed_without_verification_ids_rejected(self) -> None:
        _, rec = self._closed_scratch()
        rec["research"]["verification_ids"] = []
        self._expect("S06.2", "verification_ids is empty")

    def test_closed_with_failed_verification_rejected(self) -> None:
        _, rec = self._closed_scratch()
        rec["research"]["manifest_sha256"] = self.scratch.write_dossier("CP-00", "COULD_NOT_RUN")
        self._expect("S06.2", "V-01 outcome is 'COULD_NOT_RUN'")

    def test_unmerged_evidence_rejected(self) -> None:
        self.scratch.commit("main")
        self.scratch.git("checkout", "-q", "-b", "side")
        side = self.scratch.commit("side work")
        self.scratch.git("checkout", "-q", "master") if "master" in self.scratch.git("branch") \
            else self.scratch.git("checkout", "-q", "main")
        rec = self.scratch.close("CP-00", side)
        self.assertEqual(rec["evidence_merge_commits"], [side])
        self._expect("S06.6", "not merged")

    def test_unknown_evidence_commit_rejected(self) -> None:
        _, rec = self._closed_scratch()
        rec["evidence_merge_commits"] = ["f" * 40]
        self._expect("S06.6", "does not exist")

    def test_self_review_rejected(self) -> None:
        _, rec = self._closed_scratch()
        rec["independent_review"]["reviewer_id"] = rec["owner_id"]
        self._expect("S06.4", "self-review")

    def test_review_not_pass_rejected(self) -> None:
        _, rec = self._closed_scratch()
        rec["independent_review"]["verdict"] = "COULD_NOT_RUN"
        self._expect("S06.4")

    def test_required_provider_not_run_rejected(self) -> None:
        _, rec = self._closed_scratch()
        rec["provider_proof"]["codex"] = {"status": "NOT_RUN", "evidence_path": None, "subject_sha256": None}
        self._expect("S06.3", "codex is NOT_RUN")

    def test_unbounded_limitation_rejected(self) -> None:
        _, rec = self._closed_scratch()
        rec["limitations"] = ["TBD"]
        self._expect("S06.7", "unbounded limitation")

    def test_empty_reopen_if_rejected(self) -> None:
        _, rec = self._closed_scratch()
        rec["reopen_if"] = []
        self._expect("S06.8", "empty reopen_if")

    def test_unknown_status_rejected(self) -> None:
        _, rec = self._closed_scratch()
        rec["closure_stages"]["proven"] = "DONE"
        self._expect("SCHEMA", "closure_stages/proven")

    def test_stage_illegal_for_type_rejected(self) -> None:
        _, rec = self._closed_scratch()
        rec["closure_stages"]["implemented"] = "NOT_APPLICABLE"
        self._expect("S05", "implemented = PASS")

    def test_research_disposition_illegal_for_implementation_type(self) -> None:
        _, rec = self._closed_scratch()
        rec["human_closure"]["decision"] = "ACCEPT_RESEARCH_DISPOSITION"
        self._expect("S06.5", "legal only for RESEARCH_ONLY")

    # -- corrective specification 001 (reviews/codex-security-2026-09-04) --

    def test_missing_executable_rejected(self) -> None:                       # CS-1.1
        _, rec = self._closed_scratch()
        rec["enforcement"]["protected_release"]["executable_path"] = str(self.scratch.release_root / "bin" / "absent")
        self._expect("S06.9", "executable missing")

    def test_missing_promotion_evidence_rejected(self) -> None:               # CS-1.1
        _, rec = self._closed_scratch()
        rec["enforcement"]["protected_release"]["promotion_evidence_path"] = str(self.scratch.release_root / "absent.txt")
        self._expect("S06.9", "promotion_evidence_path missing")

    def test_missing_release_manifest_rejected(self) -> None:                 # CS-1.2
        self._closed_scratch()
        (self.scratch.release_root / "RELEASE.sha256").unlink()
        self._expect("S06.9", "RELEASE.sha256 missing")

    def test_user_owned_executable_rejected(self) -> None:                    # CS-1.3
        self._closed_scratch()          # the fixture tree is owned by this user, not uid 0
        self._expect("S06.9", "not owned by uid 0")

    def test_group_writable_executable_rejected(self) -> None:                # CS-1.3
        self._closed_scratch()
        self.scratch.executable.chmod(0o775)
        self._expect("S06.9", "group or other writable")

    def test_symlinked_executable_rejected(self) -> None:                     # CS-1.3
        _, rec = self._closed_scratch()
        link = self.scratch.release_root / "bin" / "devforge-link"
        link.symlink_to(self.scratch.executable)
        rec["enforcement"]["protected_release"]["executable_path"] = str(link)
        self._expect("S06.9", "symbolic link")

    def test_writable_ancestor_rejected(self) -> None:                        # CS-1.3
        self._closed_scratch()          # the tree lives under a sticky world-writable temp dir
        self._expect("S06.9", "ancestor")

    def test_release_manifest_entry_tampered_rejected(self) -> None:          # CS-1.4
        self._closed_scratch()
        (self.scratch.release_root / "lib" / "devforgeai" / "checkpoint" / "validate.py").write_text(
            "# tampered\n", encoding="utf-8")
        self._expect("S06.9", "does not verify")

    def test_unlisted_release_file_rejected(self) -> None:                    # CS-1.4
        self._closed_scratch()
        (self.scratch.release_root / "lib" / "extra.py").write_text("print('unlisted')\n", encoding="utf-8")
        self._expect("S06.9", "not listed in RELEASE.sha256")

    def test_release_manifest_without_schema_rejected(self) -> None:          # CS-1.4
        self._closed_scratch()
        manifest = self.scratch.release_root / "RELEASE.sha256"
        manifest.write_text("".join(line for line in manifest.read_text().splitlines(keepends=True)
                                    if "schema.json" not in line), encoding="utf-8")
        self._expect("S06.9", "schema")

    def test_schema_set_digest_mismatch_rejected(self) -> None:               # CS-1.5
        _, rec = self._closed_scratch()
        rec["enforcement"]["protected_release"]["schema_set_sha256"] = "5" * 64
        self._expect("S06.9", "schema_set_sha256")

    def test_contract_policy_digest_mismatch_rejected(self) -> None:          # CS-1.5
        _, rec = self._closed_scratch()
        rec["enforcement"]["protected_release"]["contract_policy_sha256"] = "6" * 64
        self._expect("S06.9", "contract_policy_sha256")

    def test_schema_option_rejected(self) -> None:                            # CS-2.1
        self.scratch.materialize()
        self.scratch.commit()
        code, out = run_validator(self.scratch.plan, "--schema", str(SCHEMA))
        self.assertEqual(code, 2, out)

    def test_git_root_option_rejected(self) -> None:                          # CS-2.1, CS-2.3
        self.scratch.materialize()
        self.scratch.commit()
        code, out = run_validator(self.scratch.plan, "--git-root", str(self.scratch.root))
        self.assertEqual(code, 2, out)

    def test_schema_from_plan_tree_ignored(self) -> None:                     # CS-2.2
        # A permissive schema above the plan must not change a rejection.
        rec = self.scratch.records["CP-01"]
        rec["admitted_inputs"] = [admitted_input(subject_sha256="sha256:abc")]
        self.scratch.materialize()
        permissive = self.scratch.root / "schemas" / "devforgeai" / "v1" / SCHEMA.name
        permissive.write_text("{}\n", encoding="utf-8")
        self.scratch.commit()
        code, out = run_validator(self.scratch.plan)
        self.assertEqual(code, 1, out)
        self.assertIn("SCHEMA", out)

    # -- CS-6: the record's release is the executing release --

    def test_record_release_differs_from_executing_root_rejected(self) -> None:   # CS-6.2
        # Two protected releases with the same identity; the record names the one
        # that is not executing. Both verify; the record must still be rejected.
        self._closed_scratch()
        other = self.scratch.release_root.parent / "1.0.0-other"
        self.scratch.write_release_tree(root=other)
        rec = self.scratch.records["CP-00"]["enforcement"]["protected_release"]
        rec["executable_path"] = str(other / "bin" / "devforge")
        rec["executable_sha256"] = sha256(other / "bin" / "devforge")
        problems = self._expect_inprocess("S06.9", "executing")
        self.assertTrue(any("S06.9" in p and str(other) in p for p in problems), problems)

    def test_release_identity_missing_rejected(self) -> None:                     # CS-6.3
        self._closed_scratch()
        self.scratch.write_release_tree(identity=False)
        self._expect_inprocess("S06.9", "RELEASE-IDENTITY.json")

    def test_release_identity_candidate_mismatch_rejected(self) -> None:          # CS-6.4
        self._closed_scratch()
        self.scratch.identity["candidate_source_commit"] = "f" * 40
        self.scratch.write_release_tree()
        self._expect_inprocess("S06.9", "candidate_source_commit")

    def test_release_identity_version_mismatch_rejected(self) -> None:            # CS-6.4
        self._closed_scratch()
        self.scratch.identity["version"] = "9.9.9"
        self.scratch.write_release_tree()
        self._expect_inprocess("S06.9", "version")

    def test_release_identity_devforge_commit_mismatch_rejected(self) -> None:    # CS-6.4
        self._closed_scratch()
        self.scratch.identity["devforge_commit"] = "e" * 40
        self.scratch.write_release_tree()
        self._expect_inprocess("S06.9", "devforge_commit")

    def test_policy_not_candidate_manifest_rejected(self) -> None:                # CS-6.4
        # The installed policy is a self-consistent file that is not the pinned
        # candidate manifest: RELEASE.sha256 and the record both name its digest.
        _, rec = self._closed_scratch()
        root = self.scratch.release_root
        policy = root / "contracts" / "MANIFEST.sha256"
        policy.write_text("# not the candidate manifest\n", encoding="utf-8")
        lines = [f"{sha256(q)}  {q.relative_to(root).as_posix()}"
                 for q in sorted(root.rglob("*")) if q.is_file() and q.name != "RELEASE.sha256"]
        (root / "RELEASE.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
        rec["enforcement"]["protected_release"]["contract_policy_sha256"] = sha256(policy)
        self._expect_inprocess("S06.9", "contract_policy_sha256", "candidate")

    # -- CS-7: Git identity is not caller-controlled --

    def _alternate_repository(self) -> Path:
        alt = Path(tempfile.mkdtemp(prefix="dfai-alt-", dir=self.scratch._ext.name))
        subprocess.run(["git", "-C", str(alt), "init", "-q"], check=True)
        subprocess.run(["git", "-C", str(alt), "-c", "user.email=a@b", "-c", "user.name=a",
                        "commit", "-q", "--allow-empty", "-m", "alternate"], check=True)
        return alt

    def test_git_environment_ignored(self) -> None:                               # CS-7.1
        # Canonical: an open plan with a staged candidate holds. Each Git control
        # variable would redirect history to an alternate repository; the verdict
        # must not change.
        self.scratch.stage_candidate("CP-00")
        self.scratch.materialize()
        self.scratch.commit("pin")
        code, canonical = run_validator(self.scratch.plan)
        self.assertEqual(code, 0, canonical)
        alt = self._alternate_repository()
        cases = {
            "GIT_DIR": {"GIT_DIR": str(alt / ".git"), "GIT_WORK_TREE": str(self.scratch.root)},
            "GIT_OBJECT_DIRECTORY": {"GIT_OBJECT_DIRECTORY": str(alt / ".git" / "objects")},
            "GIT_ALTERNATE_OBJECT_DIRECTORIES": {"GIT_ALTERNATE_OBJECT_DIRECTORIES": str(alt / ".git" / "objects")},
            "GIT_CONFIG": {"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "core.hooksPath",
                           "GIT_CONFIG_VALUE_0": str(alt)},
            "GIT_CEILING_DIRECTORIES": {"GIT_CEILING_DIRECTORIES": str(self.scratch.root.parent)},
        }
        for name, env in cases.items():
            with self.subTest(variable=name):
                code, out = run_validator(self.scratch.plan, env_extra=env)
                self.assertEqual(code, 0, f"{name}: {out}")
                self.assertIn("0 problem(s)", out)

    def test_path_shadowed_git_ignored(self) -> None:                             # CS-7.1
        self.scratch.stage_candidate("CP-00")
        self.scratch.materialize()
        self.scratch.commit("pin")
        shadow = Path(tempfile.mkdtemp(prefix="dfai-shadow-", dir=self.scratch._ext.name))
        (shadow / "git").write_text("#!/bin/sh\necho shadow git ran >&2\nexit 99\n", encoding="utf-8")
        (shadow / "git").chmod(0o755)
        env = {"PATH": f"{shadow}:{os.environ.get('PATH', '')}"}
        code, out = run_validator(self.scratch.plan, env_extra=env)
        self.assertEqual(code, 0, out)
        self.assertNotIn("shadow git ran", out)

    # -- CS-9: closure range from a root-owned attestation (rule S14) --

    def test_closed_record_without_attestation_rejected(self) -> None:            # CS-9.4
        base, head = self._work_then_close("CP-00", attest=False)
        report = run_inprocess(self.scratch.plan, f"{base}..{head}", self.scratch)
        problems = [str(p) for p in report.problems]
        self.assertTrue(any("S14" in p and "attestation" in p for p in problems), problems)

    def test_attestation_user_owned_rejected(self) -> None:                       # CS-9.2
        base, head = self._work_then_close("CP-00")
        fs = self.scratch.fake(protected=[self.scratch.release_root.parent])   # attest_root stays user-owned
        report = run_inprocess(self.scratch.plan, f"{base}..{head}", self.scratch, fs)
        problems = [str(p) for p in report.problems]
        self.assertTrue(any("S14" in p and "not owned by uid 0" in p for p in problems), problems)

    def test_attestation_head_not_ancestor_rejected(self) -> None:                # CS-9.4
        base, head = self._work_then_close("CP-00")
        stray = self._alternate_repository()
        stray_head = subprocess.run(["git", "-C", str(stray), "rev-parse", "HEAD"],
                                    capture_output=True, text=True, check=True).stdout.strip()
        self.scratch.attest("CP-00", base, head, head_commit=stray_head)
        report = run_inprocess(self.scratch.plan, None, self.scratch)
        problems = [str(p) for p in report.problems]
        self.assertTrue(any("S14" in p and "head_commit" in p for p in problems), problems)

    def test_attestation_record_digest_mismatch_rejected(self) -> None:           # CS-9.4
        base, head = self._work_then_close("CP-00")
        # the record is edited after the attestation was minted (still legal on its face)
        self.scratch.records["CP-00"]["limitations"].append("Edited after attestation.")
        self.scratch.materialize()
        self.scratch.commit("record edited after attestation")
        report = run_inprocess(self.scratch.plan, None, self.scratch)
        problems = [str(p) for p in report.problems]
        self.assertTrue(any("S14" in p and "record_sha256" in p for p in problems), problems)

    def test_attestation_release_identity_mismatch_rejected(self) -> None:        # CS-9.4
        base, head = self._work_then_close("CP-00")
        self.scratch.attest("CP-00", base, head, release_identity_sha256="a" * 64)
        report = run_inprocess(self.scratch.plan, None, self.scratch)
        problems = [str(p) for p in report.problems]
        self.assertTrue(any("S14" in p and "release_identity_sha256" in p for p in problems), problems)

    def test_attestation_wrong_checkpoint_rejected(self) -> None:                 # CS-9.4
        base, head = self._work_then_close("CP-00")
        self.scratch.attest("CP-00", base, head, checkpoint_id="CP-01")
        report = run_inprocess(self.scratch.plan, None, self.scratch)
        problems = [str(p) for p in report.problems]
        self.assertTrue(any("S14" in p and "checkpoint_id" in p for p in problems), problems)

    def test_attestation_hostile_plan_id_rejected(self) -> None:                 # CS-9.7
        # An agent-authored Plan ID must never steer the attestation lookup.
        base, head = self._work_then_close("CP-00", attest=False)
        readme = self.scratch.plan / "README.md"
        readme.write_text(readme.read_text(encoding="utf-8").replace("`SCRATCH`", "`../x`"), encoding="utf-8")
        head = self.scratch.commit("hostile plan id")
        self.scratch.attest("CP-00", base, head)
        report = run_inprocess(self.scratch.plan, None, self.scratch)
        problems = [str(p) for p in report.problems]
        self.assertTrue(any("S14" in p and "plan id" in p for p in problems), problems)

    def test_diff_differs_from_attested_range_rejected(self) -> None:             # CS-9.5
        base, head = self._work_then_close("CP-00")
        for wrong in (f"{head}..{head}", f"{self.scratch.git('rev-parse', f'{base}~1')}..{head}"):
            with self.subTest(range=wrong):
                report = run_inprocess(self.scratch.plan, wrong, self.scratch)
                problems = [str(p) for p in report.problems]
                self.assertTrue(any("S14" in p and "attested" in p for p in problems), problems)

    def test_post_closure_repin_rejected(self) -> None:                           # CS-9.5, the reviewer's reproduction
        base, head = self._work_then_close("CP-00")
        # implementation work and a candidate re-pin after the attested head ...
        (self.scratch.root / "src" / "validator.py").write_text("print('changed after closure')\n", encoding="utf-8")
        implementation = self.scratch.write_candidate("CP-00")
        # ... then a record-only commit carrying the new pin, still closed
        self.scratch.materialize()
        repin = self.scratch.commit("re-pin")
        for diff in (None, f"{implementation}..{repin}"):
            with self.subTest(diff=diff):
                report = run_inprocess(self.scratch.plan, diff, self.scratch)
                self.assertEqual(report.outcome, "REJECTED", [str(p) for p in report.problems])

    # -- enforcement pins (amendment SDD-GAP-AMD-001) --

    def test_closed_under_staged_candidate_rejected(self) -> None:
        _, rec = self._closed_scratch()
        rec["enforcement"]["trust_stage"] = "STAGED_CANDIDATE"
        self._expect("S06.9", "closure requires PROTECTED_RELEASE")

    def test_closed_unbound_rejected(self) -> None:
        _, rec = self._closed_scratch()
        rec["enforcement"]["trust_stage"] = "UNBOUND"
        self._expect("S06.9", "UNBOUND")

    def test_closed_with_incomplete_release_pin_rejected(self) -> None:
        _, rec = self._closed_scratch()
        rec["enforcement"]["protected_release"]["executable_sha256"] = None
        self._expect("S06.9", "release pin incomplete: executable_sha256")

    def test_proofs_bound_to_different_pins_rejected(self) -> None:
        _, rec = self._closed_scratch()
        rec["provider_proof"]["codex"]["subject_sha256"] = SHA
        self._expect("S06.9", "not both bound")

    def test_relative_executable_rejected(self) -> None:
        _, rec = self._closed_scratch()
        rec["enforcement"]["protected_release"]["executable_path"] = "bin/devforge"
        self._expect("S06.9", "must be absolute")

    def test_project_local_executable_rejected(self) -> None:
        _, rec = self._closed_scratch()
        local = self.scratch.root / "devforge"
        shutil.copy2(self.scratch.executable, local)
        rec["enforcement"]["protected_release"]["executable_path"] = str(local)
        self._expect("S06.9", "inside the repository")

    def test_executable_digest_mismatch_rejected(self) -> None:
        _, rec = self._closed_scratch()
        self.scratch.executable.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        self._expect("S06.9", "executable digest mismatch")

    def test_promotion_evidence_digest_mismatch_rejected(self) -> None:
        _, rec = self._closed_scratch()
        rec["enforcement"]["protected_release"]["promotion_evidence_sha256"] = "4" * 64
        self._expect("S06.9", "promotion_evidence_path digest mismatch")

    def test_release_without_candidate_pin_rejected(self) -> None:
        _, rec = self._closed_scratch()
        rec["enforcement"]["candidate"] = {"source_commit": None, "manifest_path": None, "manifest_sha256": None}
        self._expect("S06.9", "without the retained candidate pin")

    def test_implemented_pass_unbound_rejected(self) -> None:
        self.scratch.records["CP-00"]["closure_stages"]["implemented"] = "PASS"
        self._expect("S13", "implemented: PASS with enforcement.trust_stage UNBOUND")

    def test_staged_candidate_without_pin_rejected(self) -> None:
        self.scratch.records["CP-00"]["enforcement"]["trust_stage"] = "STAGED_CANDIDATE"
        self._expect("S13", "candidate pin incomplete")

    def test_candidate_manifest_digest_mismatch_rejected(self) -> None:
        self.scratch.stage_candidate("CP-00")
        self.scratch.records["CP-00"]["enforcement"]["candidate"]["manifest_sha256"] = "2" * 64
        self._expect("S13", "does not equal the candidate manifest")

    def test_candidate_bytes_changed_since_pin_rejected(self) -> None:
        self.scratch.stage_candidate("CP-00")
        (self.scratch.root / "src" / "validator.py").write_text("print('drift')\n", encoding="utf-8")
        self._expect("S13", "changed since source_commit")

    def test_fenced_file_not_pinned_rejected(self) -> None:
        self.scratch.stage_candidate("CP-00", omit="src/validator.py")
        self._expect("S13", "not pinned by the candidate manifest: src/validator.py")

    def test_candidate_commit_not_ancestor_rejected(self) -> None:
        self.scratch.commit("main")
        self.scratch.git("checkout", "-q", "-b", "side")
        self.scratch.stage_candidate("CP-00")
        self.scratch.git("checkout", "-q", "master") if "master" in self.scratch.git("branch") \
            else self.scratch.git("checkout", "-q", "main")
        self._expect("S13", "not an ancestor of HEAD")

    def test_proven_pass_under_staged_candidate_rejected(self) -> None:
        self.scratch.stage_candidate("CP-00")
        self.scratch.records["CP-00"]["closure_stages"]["proven"] = "PASS"
        self._expect("S13", "proven: PASS with enforcement.trust_stage STAGED_CANDIDATE")

    def test_researched_pass_without_verification_rejected(self) -> None:
        self.scratch.research_pass("CP-00")
        self.scratch.records["CP-00"]["research"]["verification_ids"] = []
        self._expect("S13", "verification_ids is empty")

    def test_researched_pass_with_failed_verification_rejected(self) -> None:
        self.scratch.research_pass("CP-00", "COULD_NOT_RUN")
        self._expect("S13", "V-01 outcome is 'COULD_NOT_RUN'")

    def test_researched_pass_self_verified_rejected(self) -> None:
        self.scratch.research_pass("CP-00")
        self.scratch.records["CP-00"]["owner_id"] = "agent:reviewer"
        self._expect("S13", "verifier equals the record owner")

    # -- paths, digests, admission, ledger --

    def test_path_escape_rejected(self) -> None:
        rec = self.scratch.records["CP-01"]
        rec["implementation"]["changed_runtime_paths"] = ["../outside/file.py"]
        self._expect("S04", "escapes")

    def test_external_path_climbing_rejected(self) -> None:
        rec = self.scratch.records["CP-01"]
        rec["admitted_inputs"] = [admitted_input(subject="/tmp/../etc/evidence.jsonl")]
        self._expect("S04", "external evidence path contains `..`")

    def test_external_absolute_path_admitted(self) -> None:
        rec = self.scratch.records["CP-01"]
        rec["admitted_inputs"] = [admitted_input(subject="/srv/proof/raw-events.jsonl")]
        self.scratch.materialize()
        self.scratch.commit()
        code, out = run_validator(self.scratch.plan)
        self.assertEqual(code, 0, out)

    def test_malformed_digest_rejected(self) -> None:
        rec = self.scratch.records["CP-01"]
        rec["admitted_inputs"] = [admitted_input(subject_sha256="sha256:abc")]
        self._expect("SCHEMA", "subject_sha256")

    def test_unknown_record_field_rejected(self) -> None:
        self.scratch.records["CP-01"]["trust_stage"] = "PROTECTED"
        self._expect("SCHEMA", "trust_stage")

    def test_admitted_before_cp00_closed_rejected(self) -> None:
        rec = self.scratch.records["CP-01"]
        rec["admitted_inputs"] = [admitted_input(state="ADMITTED", evidence_paths=["docs/x.md"])]
        self._expect("S08", "before CP-00 is closed")

    def test_dependency_not_closed_rejected(self) -> None:
        evidence = self.scratch.commit("evidence")
        self.scratch.close("CP-01", evidence)          # CP-00 stays open
        self._expect("S09", "depends on CP-00")

    def test_ledger_disagreement_rejected(self) -> None:
        self.scratch.materialize()
        readme = self.scratch.plan / "README.md"
        readme.write_text(readme.read_text().replace("| — | false |", "| — | true |"))
        self.scratch.commit()
        code, out = run_validator(self.scratch.plan)
        self.assertEqual(code, 1, out)
        self.assertIn("S03", out)

    def test_plan_without_base_rejected(self) -> None:
        self.scratch.materialize()
        readme = self.scratch.plan / "README.md"
        readme.write_text(readme.read_text().replace("| Amendment base |", "| Something else |"))
        self.scratch.commit()
        code, out = run_validator(self.scratch.plan)
        self.assertEqual(code, 1, out)
        self.assertIn("S01", out)

    def test_authority_mismatch_rejected(self) -> None:
        self.scratch.records["CP-01"]["decision_authority_id"] = "github:someone-else"
        self._expect("S12", "differs from the plan")

    def test_open_record_with_decision_rejected(self) -> None:
        self.scratch.records["CP-01"]["human_closure"]["decision"] = "ACCEPT_REMEDIATED"
        self._expect("S07")

    def test_adjacent_manifest_tampered_rejected(self) -> None:
        self.scratch.materialize()
        record = self.scratch.checkpoints / "CP-01.yaml"
        record.write_text(record.read_text() + "# trailing edit\n")
        self.scratch.commit()
        code, out = run_validator(self.scratch.plan)
        self.assertEqual(code, 1, out)
        self.assertIn("S11", out)

    def test_implementation_change_in_closure_diff_rejected(self) -> None:
        self.scratch.write_dossier("CP-00")
        self.scratch.write_candidate("CP-00")
        self.scratch.materialize()
        base = self.scratch.commit("open")
        self.scratch.close("CP-00", base)
        self.scratch.materialize()
        (self.scratch.root / "src.py").write_text("print('changed')\n")
        head = self.scratch.commit("closure plus code")
        code, out = run_validator(self.scratch.plan, "--diff", f"{base}..{head}")
        self.assertEqual(code, 1, out)
        self.assertIn("S10", out)
        self.assertIn("src.py", out)

    # ---- could-not-run ----

    def test_missing_plan_is_could_not_run(self) -> None:
        code, out = run_validator(self.scratch.root / "nope")
        self.assertEqual(code, 3, out)
        self.assertIn("COULD_NOT_RUN", out)

    def test_plan_outside_git_is_could_not_run(self) -> None:
        self.scratch.materialize()
        shutil.rmtree(self.scratch.root / ".git")
        code, out = run_validator(self.scratch.plan)
        self.assertEqual(code, 3, out)

    # ---- this repository ----

    def test_repository_plan_records_hold(self) -> None:
        code, out = run_validator(REAL_PLAN)
        self.assertEqual(code, 0, out)
        self.assertIn("15 record(s), 0 problem(s)", out)


if __name__ == "__main__":
    unittest.main()
