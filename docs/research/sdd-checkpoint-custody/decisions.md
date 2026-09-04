# CP-00 decisions

Decision authority: `github:bankielewicz`. Decisions D-CP00-01 and the trust-boundary premise were taken by the decision authority in the 2026-09-04 session; the rest are implementation decisions by the CP-00 owner, open to the independent reviewer and to the authority at closure.

## D-CP00-01 — Validator invocation (decision authority, 2026-09-04)

The staged validator is `PYTHONPATH=components/research-core/src python3 -m devforgeai.checkpoint validate --plan docs/research/spec-driven-development-gap-closure`, a new subpackage `components/research-core/src/devforgeai/checkpoint/`. It preserves the frozen Research CLI (exactly ten operations: `tests/research/test_packaging.py`, `09-hook-dispatcher.md` check 9, `dispatch.py` `RESEARCH_OPS`, `framework/skills/research/workflow.md` as a frozen plan input), separates checkpoint governance from Research operations, ships in the staging wheel because the packaging test derives the module set from the source tree, and maps to the future protected command `devforge checkpoint validate`. Rejected alternatives: `devforgeai-research validate-checkpoints` (breaks four frozen contracts in one wave) and a standalone component script (not in the wheel).

## D-CP00-02 — Explicitly external evidence (revised after review)

Section 7.1 reads "repository-relative path or explicitly external evidence path". First decision: a required boolean `external` on `admitted_inputs[]`. The independent review (V-02) rejected it because the flag is not in the governing exact record shape and would need a plan amendment. Revised decision: no flag. An absolute path in `subject` or `evidence_paths` is external evidence by definition and rule S04 admits it if it contains no `..`; a relative path must stay inside the repository (no leading slash, no backslash, no empty segment, no `..`). Every other path field of the record is repository-relative. The plan's run-5 inputs (absolute paths under the proof project) pass; `/tmp/../etc/x` and `../outside` fail. The record shape is the plan's, unchanged.

## D-CP00-03 — Unbounded limitation and non-concrete reopen condition

A limitation or `reopen_if` entry is rejected on a closed record when it is empty or whitespace, contains a placeholder token (`TODO`, `TBD`, `{{`, `}}`, `<fill in>`, `lorem ipsum`), or exceeds 1,000 characters (schema `maxLength`). An empty `reopen_if` list on a closed record is rejected. The definition is deliberately narrow; it does not judge completeness.

## D-CP00-04 — Reviewer independence is declared, not authenticated

Rule S06.4 rejects `independent_review.reviewer_id == owner_id` and requires a `PASS` verdict with an evidence path. Identifiers are self-reported strings; the validator does not authenticate them, and the record has no separate dossier-author field, so a reviewer who authored the dossier but not the record is not detectable from the record. Recorded as a CP-00 limitation.

## D-CP00-05 — Worktree directory

Work happened in `.claude/worktrees/cp-00-checkpoint-custody` on the plan's branch `research/cp-00-checkpoint-custody`, because the Claude Code worktree tool enters only directories under `.claude/worktrees/`. The plan fixes the branch name; the directory is a local, untracked location.

## D-CP00-06 — Manifests

The checkpoint records carry their own adjacent manifest `checkpoints/MANIFEST.sha256`, listing every `CP-*.yaml` and excluding itself (rule S11). The plan directory's `MANIFEST.sha256` and `README.md` are owned by the plan author's amendment branch and are not touched by the CP-00 work PR (plan section 5: overlapping fences are `BLOCKED`); the closure PR or the amendment adds the `checkpoints/` entries to the plan manifest. This dossier's `MANIFEST.sha256` lists every retained dossier file except itself.

## D-CP00-07 — Dossier record format under manual execution

The JSONL records in this dossier follow plan section 6's manual-execution contract (stable ids, source refs, evidence refs, dispositions). They are not Research Core `research/v1` run records, which require a Research run id and verification packets; `request.json` alone is normalized through `devforgeai-research normalize-request` and its digest is recorded in `README.md`.

## D-CP00-08 — CP-00 stays open until the protected validator exists

Owner ruling (github:bankielewicz, 2026-09-04): CP-00 remains `closed: false` until the validator slice (not the whole sequencer) is promoted into DevForge, installed root-owned and pinned, and the two-terminal probes are repeated against that install. A `DEFERRED` proven stage was rejected: it would let an unprotected validator admit downstream evidence, and a later `reopen_if` cannot undo evidence already admitted under a weakened trust boundary. Amendment `SDD-GAP-AMD-001` (merged PR 18) then made the mechanism part of the plan: the record carries `enforcement.trust_stage` (`UNBOUND | STAGED_CANDIDATE | PROTECTED_RELEASE`), a candidate pin and a protected-release pin; closure condition 9 requires `PROTECTED_RELEASE` with every release field non-null and both provider proofs bound to it (rule S06.9); an open record's `PASS` stages carry their evidence (rule S13). The work PR leaves `proven: NOT_RUN`, `trust_stage: STAGED_CANDIDATE` and `closed: false`. `researched` stays `NOT_RUN` until an independent verification of this dossier records `PASS` in `verification.jsonl` (the first, V-02 by Codex, failed two claims). Sequence after this PR: promote the validator slice, install, probe, then the metadata-only closure PR.

## D-CP00-09 — Candidate pin in a second commit; pin interpretations

`enforcement.candidate.source_commit` names the commit that carries the candidate bytes, and a commit cannot contain its own hash. The work branch therefore ends in two commits: A carries the schema, validator package, tests, promotion-candidate declaration and manifest, dossier and records with CP-00 `UNBOUND` and `implemented: NOT_RUN`; B changes only `checkpoints/CP-00.yaml` and `checkpoints/MANIFEST.sha256`, setting `STAGED_CANDIDATE`, the pin to A and `implemented: PASS`. Rule S13 checks that A exists and is an ancestor of `HEAD`, that the manifest at A and on disk equals the pinned digest, that every entry verifies at A and on disk, and that every fenced file at A outside `checkpoints/` and the dossier is listed. Consequence: the work PR must merge with a merge commit; a squash discards A and the pin dangles. Further interpretations of the amendment, put to the plan author on PR 18 for confirmation: the plan base is `| Amendment base |` (rule S01); `evidence_merge_commits` stays DevForgeAI-only and ancestry-checked while the DevForge release commit lives in `protected_release.source_commit` bound by the promotion evidence digest; "both provider proofs bind that same pin" means both `subject_sha256` equal `protected_release.executable_sha256`; local digests of the executable and evidence files are compared only when the paths exist on the validating machine. The two promotion-candidate paths were added to the fence citing the merged amendment as the decision authority's scope amendment (plan section 5).

## D-CP00-10 — Scope amendment SDD-GAP-CP00-SCOPE-001: `components/devforge-release/**`

Decision authority ruling (github:bankielewicz, 2026-09-04), recorded verbatim, accepted by merging the amendment PR before any byte is written under the new path (plan section 5):

> Stage it in DevForgeAI, with two important boundaries. First merge a scope amendment adding `components/devforge-release/` to CP-00's fence. Do not implement the scaffold before that amendment is accepted. Everything there remains a `STAGED_CANDIDATE`; it never becomes protected merely by passing DevForgeAI tests.
>
> Use two distinct manifests. 1. DevForgeAI candidate manifest pins: wrapper source; installer; package parent and validator modules; schema and policy; dependency lockfile and offline artifacts; installed-layout specification; manifest generator; positive and hostile tests. 2. DevForge `RELEASE.sha256` pins the final installed payload. A promotion record maps: candidate digest → DevForge commit/tag → release digest.
>
> Additional requirements: no unpinned "glue"; no network access during root installation; third-party wheels must have recorded provenance and hashes; the manifest generator cannot validate its own output, independent verification is required; DevForgeAI must never install directly into `/usr/local`; only the human promotes the reviewed bytes into DevForge; Claude and Codex must have no write credentials or writable checkout for DevForge; the root installer consumes only the immutable DevForge release.
>
> The component is a non-authoritative staged promotion candidate. Its manifest must pin every authored or imported byte needed to build and install the validator. DevForge must independently review the exact candidate, create a separate installed-layout `RELEASE.sha256`, and publish the protected release. No network installation, unpinned glue, direct `/usr/local` installation from DevForgeAI, or AI write access to DevForge is permitted.

Effect on the record: `changed_runtime_paths` gains `components/devforge-release/**`. The candidate manifest (`framework/contracts/MANIFEST.sha256`) will pin the eight kinds of bytes the ruling lists once the corrective PR creates them; rule S13's coverage check then requires every file under the new path to be listed. The plan README's CP-00 section (the plan author's file) may align its required-outputs list in a later plan amendment; this decision does not edit it.

## D-CP00-11 — Stop order: candidate `c784ab7` is not promotion-eligible

The Codex security review of PR 20 (`reviews/codex-security-2026-09-04/`, snapshot `sha256:55f244705de1243a43ef6c6882165f642a8020659c71fd4ab9d597e42892e92b`) reported four findings, all reproduced by the CP-00 owner at `0246e76` (`reviews/codex-security-2026-09-04/reproduction.txt`):

1. `_check_release_pin` verifies a digest only when the executable or evidence file happens to exist and never checks owner, mode, symlinks or ancestor writability; a uid-1000 mode-0644 executable and a nonexistent executable both pass. The check-in 19 guidance had recorded "digests compared only when the paths exist" as a limitation; it is a fail-open closure gate.
2. The CLI's `--schema` (a test seam) and `--git-root` are caller-controlled; argparse keeps the last `--schema`, so a wrapper that injects the protected schema before `"$@"` is defeated by appending another. The wrapper proposed in check-in 19 had exactly that shape.
3. S10 (closure-only diff) runs only when `--diff` is supplied; omitting it accepts a closure commit that also changes implementation.
4. The probe design in check-in 19 (`echo x >> /usr/local/bin/devforge`, edits of the canonical checkout) mutates the control under test on its failure path.

Additional, found in reproduction: `--git-root` naming a different clone raises an unhandled `ValueError` (traceback, exit 1) instead of a clean refusal.

Decision (relayed from the reviewer, adopted by the decision authority): stop CP-00 promotion and installation; no DevForge change, no `sudo`, no dependency installation, no closure evidence preparation. The record sets `implemented: NOT_RUN` while keeping the pin to `c784ab7` so the reviewed defective bytes stay identified; the candidate is recorded as not promotion-eligible. A corrective work PR on `research/cp-00-checkpoint-custody-fix1` (second work branch; deviation from plan section 5, which names one branch per checkpoint) will carry a corrective specification in this dossier with one testable statement per finding, hostile red tests written first, the fix, a regenerated candidate manifest, and a new pin; it needs independent exact-head review before any promotion. Check-in 19's steps 2 and 3 are withdrawn; a later check-in records the replacement procedure.

## D-CP00-12 — Corrective design 001: release layout contract, seams, mandatory range

Implements corrective-spec-001 after the red run (`probes/red-corrective-001.txt`, 18 hostile tests failing on assertion against candidate `c784ab7`). Decisions the specification left to the implementation:

1. **Release layout contract v1** (`components/devforge-release/INSTALLED-LAYOUT.md`). The record carries digests for the schema set and the policy but no paths, so the validator locates them through the layout: release root = parent of `bin/`, `RELEASE.sha256` at the root listing every installed byte, `schemas/devforgeai/v1/research-gap-checkpoint.schema.json` and `contracts/MANIFEST.sha256` at fixed relative paths. The interpreter and standard library are outside `RELEASE.sha256`'s scope and are pinned by distro package in the permissions evidence; no virtualenv, because `venv` places symbolic links in `bin/` (checked on this machine). The wrapper execs `/usr/bin/python3 -I -B -P` with a scrubbed environment.
2. **Fail-closed everywhere** (CS-1): absence, a symbolic link, a non-root owner or a group/other write bit on the executable, the release manifest, any listed file or any ancestor up to `/` rejects; digests of the executable, schema and policy bind to installed bytes; both evidence files are mandatory. The former limitation "digests compared only when the paths exist" is withdrawn.
3. **Seam, in-process only** (CS-1.7): `validate_plan(..., release_fs=)` is the single injection point; the CLI has no flag, environment variable or file that reaches it; `test_no_seam_from_the_cli` proves the subprocess path rejects the same user-owned fixture the in-process positive tests accept. The true positive integration test is DevForge's probe against a root-owned install (limitation on the record).
4. **Installed mode** (CS-2.2): the module detects a `RELEASE.sha256` above itself, verifies its whole tree before reading a record and refuses (`COULD_NOT_RUN`) otherwise, so a user-owned copy of the release validates nothing (`test_installed_mode_refuses_unprotected_tree`). Staged mode resolves the schema above the module only; the walk over the plan's ancestors is gone. `--schema` and `--git-root` are removed; `allow_abbrev=False`.
5. **Mandatory range** (CS-3): a closed record without `--diff` raises `RangeRequired` (CLI exit 2); the head must equal `HEAD`, the base must be a proper ancestor (S10). Consequence recorded as a limitation: every validation of a plan with a closed record needs the range, CI included; a host-supplied trusted base/head is DevForge work.
6. **Scaffold** (CS-5): `components/devforge-release/` with wrapper, launcher, installer, lockfile, seven vendored wheels with PyPI-published and locally computed digests recorded side by side, generator, coreutils verifier, layout specification and fifteen unprivileged tests. The candidate manifest now pins every file there plus the package parent (`gen_contracts.py` globs the component). The generator never verifies; `verify-release.sh` and the installed validator's self-check are the independent checks.
7. **Probe design only** (CS-4): no probe script in this PR; the evidence PR writes it after independent exact-head review.
8. **Second work branch**: `research/cp-00-checkpoint-custody-fix1`, three commits (red, green, pin), merge commit required as before.
