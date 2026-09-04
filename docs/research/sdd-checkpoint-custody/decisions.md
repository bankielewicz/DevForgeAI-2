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
