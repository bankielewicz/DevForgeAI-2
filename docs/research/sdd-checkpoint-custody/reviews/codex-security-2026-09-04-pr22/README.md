# Codex security review of PR 22 (exact head `257ba7d`), 2026-09-04

Verdict relayed by the decision authority: **FAIL / PROMOTION_HALT**. Do not merge PR 22 at `257ba7d`. Copied verbatim from the reviewer's scan directory (`/tmp/codex-security-scans/DevForgeAI/257ba7dbf972d6591a2848bb97cfd9cb1a31033e_20260904T164023Z/`, snapshot `codex-security-snapshot/v1:sha256:fa2e218fa6da5498e0eea5cc899a20bb1cdfca48fe70e14745ccaec64018a56b`).

| File | Content |
|---|---|
| `report.md` | the review: threat model, four high findings with remediation and tests, reviewed surfaces, open questions |
| `findings.json`, `coverage.json`, `scan-manifest.json` | the canonical machine artifacts the report projects |
| `reviewed-surfaces.md`, `threat-model.md` | the coverage table (three "needs follow-up" rows) and the threat model |
| `reproductions/*-output.txt` | the four hostile reproductions' recorded output (cross-root, git-environment, ld-preload, range-bypass) |
| `reproductions/*-validation-report.md` | the reviewer's validation write-up per reproduction |

This time the reviewer shipped outputs, not scripts; the hostile tests of `corrective-spec-002.md` are reconstructed from the descriptions and outputs and named there per finding.

Findings, in the reviewer's numbering: (1) inherited Git environment replaces repository history; (2) the record-selected release can differ from the executing validator (CS-1.8 confirmed); (3) `LD_PRELOAD` code runs before the shell wrapper can scrub anything; (4) a caller-selected `--diff` base hides post-closure implementation changes followed by a re-pin. Dispositions: V-03 FAIL (C-01 fails, C-02 to C-07 pass); layout contract v1 not confirmed; plan README CP-00 required outputs to be updated; D-CP00-11 stays in force.
