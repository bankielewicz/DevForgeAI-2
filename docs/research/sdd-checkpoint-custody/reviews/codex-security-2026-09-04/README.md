# Codex security review of PR 20 (2026-09-04)

External evidence, copied verbatim from the Codex Security scan directory
`/tmp/codex-security-scans/DevForgeAI/b9998de92a821efa85f31497ee5b22f8fd97bf56_20260904T150425Z/`
(scan target `devforgeai-pr20-9305715-b9998de`, revision range `9305715…b9998de`, snapshot digest
`sha256:55f244705de1243a43ef6c6882165f642a8020659c71fd4ab9d597e42892e92b`). The scan's own `scan-manifest.json` lists the digests of `findings.json`
and `coverage.json`; this dossier's `MANIFEST.sha256` pins every file here.

| File | Content |
|---|---|
| `report.md` | the review: four reportable findings (three high, one medium), threat model, reviewed surfaces, follow-ups |
| `findings.json`, `coverage.json`, `scan-manifest.json` | the canonical machine-readable artifacts the report projects |
| `probes/probe_*.py` | the four deterministic subprocess proofs Codex ran (they load `tests/research/test_gap_checkpoints.py` through a `source` symlink two directories above themselves) |
| `reproduction.txt` | the same four proofs re-run by the CP-00 owner at `0246e76` (PR 20 merge); every fail-open result reproduced, plus an unhandled `ValueError` traceback for a `--git-root` naming another clone |

Findings, as they bear on CP-00: (1) the release pin is fail-open, a missing or user-owned executable passes and
no owner, mode, symlink or ancestor check exists; (2) the CLI's `--schema` and `--git-root` let the caller replace
the protected schema and repository root; (3) S10 runs only when `--diff` is supplied; (4) the probe design in
check-in 19 was destructive on its failure path. Consequence recorded in D-CP00-11: candidate `c784ab7` is not
promotion-eligible; a corrective work PR with a corrective spec and hostile red tests follows the accepted scope
amendment D-CP00-10.

To re-run the proofs from a checkout: `ln -s <checkout> <this dir>/../../source` is not needed; instead copy the
`probes/` directory to a scratch location `X/artifacts/05_findings/`, symlink `X/source` to the checkout, and run
each probe with `PYTHONPATH=components/research-core/src`.
