# Promotion candidate: DevForge contract v1 (draft)

Status: draft assembled 2026-09-03 in DevForgeAI. Not authoritative. Per `docs/design/adr/ADR-0001-research-placement.md`, contracts drafted here become authoritative only when a human reviews this exact set and promotes it into the protected DevForge repository; DevForgeAI then consumes the released version by digest. Nothing in DevForgeAI may treat these files as accepted expected outputs.

## What the reviewer promotes

| Kind | Path in this repository | Destination in DevForge |
|---|---|---|
| Error taxonomy (closed vocabulary, `taxonomy_version: 1`) | `framework/contracts/error-taxonomy.yaml` | `contracts/errors.yaml` |
| Schemas, JSON Schema Draft 2020-12 | `schemas/devforgeai/v1/*.schema.json` (6 files) | `contracts/schemas/` |
| CLI grammar: operations, arguments, preconditions, writes, exit codes, access | `docs/design/10-sequencer-and-contracts.md#2-cli-grammar` | `contracts/cli/` |
| Status vocabulary and gate policy | `docs/design/10-sequencer-and-contracts.md#3-status-vocabulary-and-gate-policy` | `contracts/cli/` |
| Conformance rows (dispatcher, grammar, backstops) | `docs/design/examples/hooks/run_conformance.py` | `conformance/` after extraction to data files |

The two document sections are pinned by section hash under the rule in `01-skill-anatomy.md` (heading to next heading of the same or higher level, CRLF to LF, joined with LF plus one trailing LF). The files are pinned by `MANIFEST.sha256` beside this document.

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
