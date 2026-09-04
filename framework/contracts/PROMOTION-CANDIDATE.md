# Promotion candidate: DevForge contract v1 (draft)

Status: draft assembled 2026-09-03 in DevForgeAI. Not authoritative. Per `docs/design/adr/ADR-0001-research-placement.md`, contracts drafted here become authoritative only when a human reviews this exact set and promotes it into the protected DevForge repository; DevForgeAI then consumes the released version by digest. Nothing in DevForgeAI may treat these files as accepted expected outputs.

## What the reviewer promotes

| Kind | Path in this repository | Destination in DevForge |
|---|---|---|
| Error taxonomy (closed vocabulary, `taxonomy_version: 1`) | `framework/contracts/error-taxonomy.yaml` | `contracts/errors.yaml` |
| Schemas, JSON Schema Draft 2020-12 | `schemas/devforgeai/v1/*.schema.json` (6 files; the seventh, `research-gap-checkpoint.schema.json`, belongs to slice 2 below) | `contracts/schemas/` |
| CLI grammar: operations, arguments, preconditions, writes, exit codes, access | `docs/design/10-sequencer-and-contracts.md#2-cli-grammar` | `contracts/cli/` |
| Status vocabulary and gate policy | `docs/design/10-sequencer-and-contracts.md#3-status-vocabulary-and-gate-policy` | `contracts/cli/` |
| Conformance rows (dispatcher, grammar, backstops) | `docs/design/examples/hooks/run_conformance.py` | `conformance/` after extraction to data files |

The two document sections are pinned by section hash under the rule in `01-skill-anatomy.md` (heading to next heading of the same or higher level, CRLF to LF, joined with LF plus one trailing LF). The files are pinned by `MANIFEST.sha256` beside this document.

## Slice 2: research-gap checkpoint validator, `devforge` launcher and release scaffold (CP-00, staged 2026-09-04, corrected after the PR 20 and PR 22 reviews)

Promotion candidate under plan `SDD-GAP-CLOSURE-2026-09-03` amendment `SDD-GAP-AMD-001` (section 4.2, staged-to-protected trust boundary) and CP-00 scope amendment `SDD-GAP-CP00-SCOPE-001`. The candidate is non-authoritative until a human promotes this exact set into protected DevForge, builds the release there (the static launcher with the pinned toolchain, the Python delegate, the schemas, the policy), writes DevForge's own `RELEASE-IDENTITY.json` and installed-layout `RELEASE.sha256`, and installs it root-owned at an absolute path from the immutable release; the CP-00 record pins the set by `enforcement.candidate` (source commit, this manifest, its digest) and cannot close until `enforcement.protected_release` names the installed release, the installed validator's fail-closed rules accept it as its own executing release, and a root-minted closure attestation exists (`docs/research/sdd-checkpoint-custody/corrective-spec-001.md`, `corrective-spec-002.md`).

| Kind | Path in this repository | Destination in DevForge |
|---|---|---|
| Record schema, release identity schema, closure attestation schema (JSON Schema Draft 2020-12) | `schemas/devforgeai/v1/research-gap-checkpoint.schema.json`, `release-identity.schema.json`, `closure-attestation.schema.json` | `<root>/schemas/devforgeai/v1/` |
| Policy (this manifest, as promoted) | `framework/contracts/MANIFEST.sha256` | `<root>/contracts/MANIFEST.sha256` |
| Package parent and validator modules (rules S01–S14) | `components/research-core/src/devforgeai/__init__.py`, `checkpoint/__init__.py`, `checkpoint/validate.py` | `<root>/lib/devforgeai/` |
| CLI integration (argparse, exit codes 0/1/2/3, no policy option) | `components/research-core/src/devforgeai/checkpoint/__main__.py` | `<root>/lib/devforgeai/checkpoint/` |
| `devforge` launcher source, toolchain pin, lock, build script and build digest | `components/devforge-release/launcher/**` (`Cargo.toml`, `Cargo.lock`, `rust-toolchain.toml`, `.cargo/config.toml`, `src/main.rs`, `src/sha256.rs`, `build.sh`, `BUILD-DIGEST.txt`) | `<root>/bin/devforge` (built by DevForge, digest reproduced) |
| Python launcher | `components/devforge-release/bin/devforge-checkpoint.py` | `<root>/bin/` |
| Installed-layout specification (contract v2) | `components/devforge-release/INSTALLED-LAYOUT.md` | release documentation |
| Dependency lockfile and offline artifacts with provenance | `components/devforge-release/requirements.lock`, `wheels/*.whl`, `wheels/PROVENANCE.md` | `<root>/lib/` (installed with `--no-index --require-hashes`) |
| Identity and manifest generators (never verifiers) | `components/devforge-release/gen_release_identity.py`, `gen_release_manifest.py` | DevForge build step |
| Independent verifier (coreutils only) | `components/devforge-release/verify-release.sh` | human verification after install |
| Root installer (immutable release in, no network, no pip, verifier required) | `components/devforge-release/install.sh` | human installation step |
| Positive and hostile tests | `tests/research/test_gap_checkpoints.py`, `components/devforge-release/tests/test_devforge_release.py` | DevForge test suite |
| Declarations | `framework/contracts/PROMOTION-CANDIDATE.md`, `components/devforge-release/README.md` | promotion record |

Staged invocation, from the repository root (the staged module resolves its schemas from this checkout, never from the plan's tree, and rejects every closed record because condition 9 is decidable only by the installed validator):

```bash
PYTHONPATH=components/research-core/src python3 -m devforgeai.checkpoint validate --plan docs/research/spec-driven-development-gap-closure
PYTHONPATH=components/research-core/src python3 -m pytest tests/research/test_gap_checkpoints.py -q
python3 -m pytest components/devforge-release/tests -q
```

Promotion maps the operation to `devforge checkpoint validate` (and `devforge checkpoint attest` for the human) without adding an eleventh Research operation or a second staging console script. Every file in the table is pinned by `MANIFEST.sha256` beside this document, which the validator checks against the CP-00 record's candidate pin (rule S13): every entry must verify at the pinned source commit and on disk, and every fenced file outside the records and the dossier must be listed. The installed release is pinned separately by DevForge's `RELEASE.sha256`, verified by the installed validator itself before it reads any record and by `verify-release.sh` independently; `RELEASE-IDENTITY.json` binds the release back to this candidate's checkpoint, commit and manifest digest.

## How to verify before promoting

```bash
sha256sum -c framework/contracts/MANIFEST.sha256
python3 docs/design/specs/verify.py --only v3,v8     # section hashes; CLI table equals the sequencer's argparse
python3 -c "import json,jsonschema,yaml;jsonschema.validate(yaml.safe_load(open('framework/contracts/error-taxonomy.yaml')),json.load(open('schemas/devforgeai/v1/error-taxonomy.schema.json')));print('taxonomy ok')"
python3 docs/design/examples/hooks/run_conformance.py
```

A mismatch in any line means the candidate changed after this document was written; regenerate `MANIFEST.sha256` and re-read the diff before promoting.

## Change made while assembling this candidate

`error-taxonomy.yaml#exit_codes` keys are now quoted (`"0"` to `"3"`). Unquoted, every YAML loader reads them as integers, and the schema requires string property names, so the file failed its own validation command above. No code or meaning changed. This is the kind of defect a promotion review exists to catch before a second implementation reads the file.

## Known gaps carried into the review

- The conformance rows still live as Python in `run_conformance.py`. Extraction to language-neutral fixture files (event in, expected exit and stderr pattern out) is the next task; until then the rows are reviewable but not consumable by a non-Python implementation.
- `error-taxonomy.yaml#open_items` lists three divergences between document 10 and the roll-up (worker `could_not_run` versus `INFRA_FAILURE`; handoff `outcome` vocabulary; no emitter for `host_fail_open`). Promotion of version 1 accepts them as open; version 2 closes them.
- No DevForge repository exists yet, so `vendor/devforge/v1/` in DevForgeAI is empty. When it is created, the first release is this set with these digests, and DevForgeAI's CI verifies against it.
