# CP-00 dossier: checkpoint custody and closure

| Field | Value |
|---|---|
| Checkpoint | `CP-00` of `SDD-GAP-CLOSURE-2026-09-03` |
| Record | `docs/research/spec-driven-development-gap-closure/checkpoints/CP-00.yaml` |
| Owner | `agent:claude-fable-5.1/session-01Q1TK69vPB4KT763iv2dwQM` |
| Decision authority | `github:bankielewicz` |
| Base commit | `6a446355605a06891cdeab1cc9d25f35309afba2` (PR 17 merge) |
| Budget profile | `quick` |
| Request digest | `bb074040aae271daffec1f0bdea0dd7a19199b85194a0f3f78aacb27ce13cf78` (from `devforgeai-research normalize-request request.json`) |
| Status after corrective 002 | candidates `c784ab7` and `89be834` superseded (not promotion-eligible, D-CP00-11, D-CP00-13); corrective-spec-002 implemented red-first (D-CP00-14): executing-release identity, sanitized Git, static Rust `devforge` launcher, root-minted closure attestation (rule S14); `researched: NOT_RUN` (V-03 FAIL on C-01, revised), `implemented: PASS` under the new candidate pin, `proven: NOT_RUN`, `trust_stage: STAGED_CANDIDATE`, `closed: false` |

## What CP-00 delivers

1. `schemas/devforgeai/v1/research-gap-checkpoint.schema.json`: the exact structural shape of plan section 7.1 as amended by SDD-GAP-AMD-001 (`enforcement` block with candidate and protected-release pins); external evidence is an absolute path, no marker (D-CP00-02).
2. `components/research-core/src/devforgeai/checkpoint/`: the semantic validator, invoked as
   `PYTHONPATH=components/research-core/src python3 -m devforgeai.checkpoint validate --plan docs/research/spec-driven-development-gap-closure`. Rules S01–S14 are listed in its module docstring; S06.9 and S13 are fail-closed per corrective-spec-001, S06.9 binds the executing release and S14 the closure attestation per corrective-spec-002. Exit 0 holds, 1 rejected, 2 usage, 3 could not run.
3. One record per ledger entry under the plan's `checkpoints/`, all `closed: false`, with the plan's seven `admitted_inputs` rows carried as `AVAILABLE_FOR_ADMISSION`, and an adjacent `checkpoints/MANIFEST.sha256` that excludes itself.
4. `tests/research/test_gap_checkpoints.py`: positive and hostile subprocess tests in a scratch Git repository (`probes/tests.txt`).
5. `framework/contracts/PROMOTION-CANDIDATE.md` slice 2 and `framework/contracts/MANIFEST.sha256`: the promotion candidate the CP-00 record pins (amendment SDD-GAP-AMD-001), covering the validator and the scaffold.
6. `components/devforge-release/`: the staged release scaffold (scope amendment SDD-GAP-CP00-SCOPE-001): the `devforge` Rust launcher (source, toolchain pin, lock, build script, build digest), the Python launcher, installer, lockfile and vendored wheels with provenance, identity and manifest generators, coreutils verifier, installed-layout specification v2, tests; plus `schemas/devforgeai/v1/release-identity.schema.json` and `closure-attestation.schema.json`.
7. This dossier and its manifest.

## Files

| File | Content |
|---|---|
| `request.json` | the bound request: questions, scope, budget, fence, authority |
| `questions.md` | five questions with lanes and dispositions |
| `query-log.jsonl` | every repository inspection performed for discovery |
| `sources.jsonl` | admitted sources with SHA-256 at the base commit |
| `evidence.jsonl` | quoted excerpts bound to sources |
| `claims.jsonl` | seven claims, all `NOT_ACCEPTED_PENDING_INDEPENDENT_VERIFICATION` (C-01, C-02 revised and C-07 split out after V-02) |
| `contradictions.jsonl` | three resolved contradictions (two with the plan author's recommendations, one raised by the independent review), one open |
| `verification.jsonl` | V-01 `COULD_NOT_RUN` (opened with the work PR); V-02 `FAIL` (Codex, head a9ae070, pre-amendment shape); the corrected head awaits V-03 |
| `decisions.md` | D-CP00-01 to D-CP00-14 (10: scope amendment `components/devforge-release/**`; 11: stop order; 12: corrective design 001; 13: halt at `257ba7d` and the Rust/attestation rulings; 14: corrective design 002) |
| `probes/environment.txt` | interpreter and provider versions, HEAD, status |
| `probes/claude-validate.txt` | the validator run from the Claude Code terminal, output and exit code |
| `probes/codex-validate.txt` | `NOT_RUN`: the same command for the Codex terminal, to be run by the independent reviewer |
| `probes/red-corrective-001.txt` | the corrective tests against candidate `c784ab7` before the fix: 18 failed on assertion, 59 passed |
| `probes/red-corrective-002.txt` | the corrective-002 tests against candidate `89be834` before the fix: 38 failed on assertion (32 tests, 6 subtests), 91 passed |
| `probes/tests.txt` | the test-suite run on the corrected validator, output and exit code |
| `corrective-spec-001.md` | one testable statement per finding of the Codex review of PR 20 (CS-1 to CS-5), the red-first method and the test names |
| `corrective-spec-002.md` | one testable statement per finding of the Codex review of PR 22 (CS-6 to CS-10): executing-release identity, sanitized Git, static launcher, attested closure range, scaffold follow-ups |
| `reviews/codex-security-2026-09-04-pr22/` | the Codex exact-head review of PR 22 at `257ba7d` (FAIL / PROMOTION_HALT): report, findings, coverage, scan manifest, threat model, the four reproductions' outputs and validation reports |
| `reviews/codex-security-2026-09-04/` | the Codex security review of PR 20: report, findings, scan manifest, coverage, its four proof scripts, the owner's reproduction at `0246e76` (`reproduction.txt`) and the same scripts against the corrected validator (`reproduction-after-fix.txt`) |
| `MANIFEST.sha256` | every file above except itself |

No record class is `NOT_APPLICABLE`.

## Limitations

- The validator is a staged promotion candidate; the authoritative executable is the future protected DevForge `devforge checkpoint validate`. CP-00's `proven` stage requires that pinned, root-owned install verified from both terminals, which this PR cannot supply.
- Identities are self-reported strings (D-CP00-04).
- The Codex-terminal probe is `NOT_RUN` in this PR; the independent reviewer runs it.
- The schema is resolved from the checkout, not from wheel data-files, because the Research Core packaging contract freezes the shipped schema set.
- The worktree directory differs from the plan's table (D-CP00-05); the branch name matches.
