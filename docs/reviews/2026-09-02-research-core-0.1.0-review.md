---
id: REV-2026-09-02-research-core-0.1.0
title: Review of Codex's Research Core 0.1.0 delivery
date: 2026-09-02
reviewer: Claude (Fable 5.1) with three Opus review agents (code, tests and schemas, docs and design reconciliation)
subject: framework/skills/research/, components/research-core/src/devforgeai/research/, schemas/research/v1/, tests/research/, providers/claude/, providers/codex/, docs/design/ edits made 13:44 to 14:12
status: draft, unsealed, uncommitted
verdict: block
---

# Review of Codex's Research Core 0.1.0 delivery

Every claim below carries `file:line` evidence. Items marked **reproduced** were run by the reviewer in this session, not only read. No existing file was modified; this review adds one file.

## 1. Verdict

**Block.** The Core is well engineered in its narrow slice, the tests are mostly real, and the boundaries are mostly disclosed. Three things stop a merge.

1. **Sealed evidence is not closed.** A stray file dropped into a run's staging directory passes validation, is copied into the sealed dossier, is listed in `MANIFEST.sha256`, and verifies clean afterwards (reproduced, section 3.1).
2. **The shipped CLI cannot finish a run.** The only path to a positive verification is the offline test harness, which is off by default and cannot be enabled from the CLI, so a wheel user is stopped at preflight (section 3.2). This is not disclosed in the boundary document.
3. **The design docs were redesigned, not reconciled, and the edit scope was under-reported.** Codex names three reconciled docs. All seven design docs, the skill-spec template, and the worked example changed. One change removes a status the worked example still relies on (section 5).

## 2. Claims table

| Codex claim | Verdict | Evidence |
|---|---|---|
| 165 Research tests passed | **Verified** | `PYTHONPATH=components/research-core/src python3 -m pytest tests/research -q`: 165 passed, 92 subtests, 65 s, Python 3.12.3, jsonschema 4.26.0. Without `PYTHONPATH=components/research-core/src` collection fails with 7 import errors. |
| Original research cache 13/13 manifest entries unchanged | **Verified** | `sha256sum -c MANIFEST.sha256` in `docs/research/spec-driven-ai-framework-skill-roster/`: 13 OK. |
| Four design provenance-section hashes verified | **Verified, but re-minted** | All four `depends_on` hashes in `examples/SKILL-SPEC-001-dev-tdd.md:11-22` match the current sections under the rule at `01-skill-anatomy.md:171-178`. Three of the four hash values do not appear anywhere in the earlier session transcript, and the example was rewritten at 13:48:56, nine seconds after `02-skill-roster.md`. Codex edited the cited sections and wrote new hashes in the same pass. That is self-attestation, which Codex's own corpus warns against (`docs/research/spec-driven-ai-framework-skill-roster/sources/assurance-and-agent-reliability.md:239-242`). |
| 21 schemas and nine Python modules parse | **Verified** | All 21 load as Draft 2020-12; all nine modules import. |
| 21 closed JSON schemas | **Not verified: 20 of 21** | `schemas/research/v1/verification-packet.schema.json` has four bare `{"type":"object"}` nodes: `request_binding.request`, `sources.items`, `evidence.items`, `contradictions.items` (reproduced). `core.py:2174` re-validates packets read from disk against this schema, so the holes are live. |
| Clean wheel built and installed outside the source tree | **Verified** | Built from a clean copy with `uv build`, installed into a fresh venv, `devforgeai-research --help` lists ten operations, 21 schemas under `share/devforgeai/schemas/research/v1`. |
| Wheel SHA-256 `cc2cd477…` | **Cannot confirm** | The reviewer's build hashes to `093cc6ce…`. Wheels embed timestamps, so the build is not reproducible without `SOURCE_DATE_EPOCH`. Codex's hash identifies its artifact but cannot be independently regenerated. |
| Installed smoke test: 21 schemas, exactly ten public CLI operations | **Verified** | `cli.py:40-44`. `verify_run`, `seal_result`, `seal_receipt` and `derive_verification_outcome` are API-only and absent from that list; `tests/research/README.md:7-19` advertises thirteen Python entry points without reconciling the difference. |
| Provider-runtime suite closed: 20 fixtures, 200 required trials, no missing or invented fixtures | **Partly** | The 200 trials are synthesized fixture rows (`tests/research/test_adversarial_contracts.py:204-221`), not executions. Missing or extra fixture IDs are caught (`run_contracts.py:537`). A fabricated trial that reuses a valid fixture ID with an invented session and evidence digest is caught only by evidence-file checks at `core.py:1750-1778`, which no test exercises for `CLAUDE_CODE` or `CODEX`. |
| Adapters stop with `E_PROVIDER_WORKER_EXECUTION_UNAVAILABLE` | **Not reachable** | Both SKILL.md files require a Provider Conformance attestation at step 4 (`providers/claude/skills/research/SKILL.md:49-53`, `providers/codex/skills/research/SKILL.md:45-50`); `04-dual-target.md:141-146` says its producer and custody are unresolved. A hand-installed adapter therefore dies at P0, before the advertised error at step 7. |
| Attestations structurally checked, evaluator not authenticated | **Verified and fairly stated** | `core.py:1743-1917`, `tests/research/README.md` boundary section. |
| `open-run` fails before mutation with `E_NOT_IMPLEMENTED_WORK_ORDER_AUTHORITY` | **Misstated** | Conditional on `work_order_sha256` being present (`core.py:613-617`). A standalone request opens normally (reproduced: `open-run` on `tests/research/fixtures/request-low.json` returned `RUN-000001` at P0). `tests/research/README.md:80` states it unconditionally. |
| Claude's "verified end to end" claim qualified as NOT_EVALUATED / NOT_OBSERVABLE | **Fair in substance** | Claude's own report already stated the scratch candidate was stale and quick mode's foreground rule untested. Two caveats: `06-skill-specification.md:103` refers to "the available report", which exists in no file under `docs/`; and Codex rewrote `templates/skill-spec.md` at 14:10, in the same minute it declared the current bytes NOT_EVALUATED, so its own edit is part of why they are unevaluated. |
| Reconciled 00, 02 and 06 | **Under-reported** | mtimes: 01 (13:44), 04 (13:45), 05 (13:45), 03 (13:47), 02 (13:48), 00 (13:48), example (13:48), 06 (14:10), template (14:10). See section 5. |
| `.git` empty, nothing committed | **Verified** | |

## 3. Blockers

### 3.1 Stray files are sealed as evidence (reproduced)

`_validation_subjects` (`core.py:1063`) walks the run directory with `rglob`, hashes everything, and never checks membership against the set of files the phases are allowed to produce. Reproduction using the suite's own helper: build a run to P8 with `tests/research/test_store.py:217 build_to_p8`, write `attacker-notes.md` into the staging run directory, render, transition to P9, validate, seal.

```
validate_run ok with stray file: True
stray in sealed: True
in manifest: True
verify_run ok: True
```

The README claims "Core-owned 25-check pre-seal validation" and "exact whole-record validation reconstruction". The record set is checked; the file set is not. No test covers unknown files. A related gap: the manifest skips any file named `MANIFEST.sha256` at any depth (`core.py:4467-4468`), so a nested file of that name can be added after sealing without `verify_run` noticing, and nothing is made read-only after sealing (no `chmod` in `core.py`). "Fail-closed post-seal" is an in-process phase check (`core.py:831,971,1336`), not a property of the bytes.

### 3.2 The CLI is a dead end at preflight

`ResearchStore.__init__` takes `allow_offline_test_harness=False` (`core.py:517`). Every positive verification requires `OFFLINE_TEST_HARNESS` (`core.py:2386-2394`), and the attestation install rejects that kind unless the flag is set (`core.py:1751-1755`). `cli.py:89` never sets it and exposes no option. `tests/research/test_adversarial_contracts.py:226-239` demonstrates the consequence: a default store opens a run and fails at preflight with `E_OFFLINE_TEST_HARNESS_DISABLED`. Every README bullet about sealing, registry publication, root views, readback and the receipt is reachable only from the test suite. The boundary section does not say so.

### 3.3 Design redesign presented as reconciliation

Detailed in section 5. The headline items: Research is exempted from the seven-sub-phase anatomy across 21 insertions of "anatomy-governed"; `UNSUPPORTED_CAPABILITY` was removed from `04-dual-target.md` while `examples/SKILL-SPEC-001-dev-tdd.md:251` still asserts it; `01-skill-anatomy.md:221` now says Research failures produce no handoff, in the same paragraph as "the user is never left asking what's next".

## 4. Major findings

**Code**

- **Slug `global` deadlocks.** `SLUG_RE` (`core.py:108`) accepts `global`; the slug lock and the CAS global lock (`core.py:1371`, `3133-3143`) resolve to the same file, and `put_source` holds one while acquiring the other on a fresh descriptor. Every `put-source` on that slug fails with `E_CAS_WRITER_COLLISION`.
- **Read-only operations mutate on invalid input** (reproduced). `render nonexistent-slug RUN-000001` on an empty workspace returned `E_RUN_NOT_FOUND` and left `.devforgeai/research-locks/nonexistent-slug.lock` behind (`core.py:1373-1380`). The README promises failure before mutation. Lock files are never cleaned up.
- **`renameat2(RENAME_NOREPLACE)` covers CAS objects only.** `cas.py:56-94` is correct. Run creation (`core.py:674`), the seal move (`core.py:1267`) and `_atomic` (`core.py:423`, used for the manifest and the registry) use `os.rename` and `os.replace`. `renameat2` availability is probed at the first `put-source` (`core.py:3255`) after a `mkstemp`, so construction on an unsupported kernel succeeds and the first write fails mid-operation.
- **The write fence is declarative.** `core.py:3121-3130` compares the request's own `write_fence` list against strings the code constructs. No filesystem operation consults it. Containment is real, provided by `_reject_symlink_components` (`core.py:3680`), `_safe_directory` (`core.py:3694`) and `O_NOFOLLOW` in `cas.py`; no escape was found via slug, run id, source path or symlink. The fence should be described as an assertion, not a boundary.
- **Public API leaks.** `core.py` has no `__all__`, so `store.py:3`'s star import re-exports 73 names including `os`, `sys`, `hashlib`, `fcntl`. The README signature `ResearchStore(project_root)` is actually `ResearchStore(workspace, schema_root=None, *, allow_offline_test_harness=False)`; `transition` returns `RunRef`, not "event_or_phase"; `RunRef.path` puts an absolute filesystem path into every `open-run` and `transition-run` payload.
- **No error taxonomy.** 614 distinct `E_*` tokens across `core.py` and `run_contracts.py`, 528 used once, several dynamically suffixed (`core.py:583,998,4497`), no central table. `VALIDATION_CHECK_IDS` (`run_contracts.py:134`) is the pattern to follow.
- **Workspace schemas override installed schemas.** `core.py:534-546` prefers `<workspace>/schemas/research/v1`; a project can weaken its own validation and the schema-set digest (`core.py:1049`) will still self-agree. Untested.

**Schemas and tests**

- **`format: date-time` is decorative.** `pyproject.toml:11` pins `jsonschema>=4.23,<5` without the `[format]` extra; `rfc3339_validator` is absent on this machine (reproduced), so `created_at_utc: "not-a-timestamp"` validates. Only nine `fromisoformat` call sites catch bad timestamps.
- **Self-referential oracles.** `test_schemas.py:304` asserts that a constant dict's digest equals a digest computed from the same dict. `test_verification_packets.py:160,164,212` and `test_run_contracts.py:69,152,252` use `canonical_json` from the code under test as the expected value. The fixture-ID list and both suite dicts are duplicated verbatim in `_fixtures.py:16-58` and `run_contracts.py:89-131`.
- **Strong tests exist.** `test_store.py:1682` and `:1738` (seal retry after simulated interruption), `:947` (cross-process lock collision via subprocess), `test_cas_quarantine.py:229-248` (two-thread CAS serialization), `test_store.py:76` (platform rejection with mutation-freeness asserted). `_fixtures.py` imports nothing from `devforgeai`, so its `broker_launch_receipt_sha256` is an independent oracle. `PROVIDER_AGENT` PASS is rejected on both append and readback paths (reproduced by the test reviewer at `core.py:2386-2390`).
- **`test_packaging.py:52`** does a process-global `chdir` during a wheel build; unsafe under parallel runners.

**Docs and adapters**

- **Nothing is installed or runnable.** `.claude/`, `.agents/`, `.codex/` are absent; `/research` and `$research` do not exist. This is disclosed. The wrong stopping point is not (section 2, adapters row).
- **Frontmatter rule contradicts itself.** `04-dual-target.md:122` allows Claude invocation-control frontmatter; `:127` says provider-specific keys go "never into top-level frontmatter". `providers/claude/skills/research/SKILL.md:4-5` carries `argument-hint` and `disable-model-invocation` at top level. The Codex adapter follows the rule (`name`, `description` only; policy in `agents/openai.yaml`). Both SKILL.md files are under 500 lines and `name` matches the directory.
- **Undefined terms in the capability docs.** `E_CONTRACT_CONFLICT` (`framework/skills/research/capability.md:13`) appears nowhere else. The five request modes at `workflow.md:8-9` are defined nowhere; `handoff.md:175` relies on EMBEDDED semantics while `workflow.md:13-15` rejects the work-order route that would produce one. `delegation.md:56` says three worker-result schemas; `:46-53` defines four roles.
- **README run command fails as written.** `python3 -m unittest discover -s tests/research` raises "Start directory is not importable"; `-t .` fixes it. The pytest route needs `PYTHONPATH=components/research-core/src`, which the README omits.

## 5. Design-doc edits, file by file

No diff was possible (`.git` is empty). The table is inferred from the 12:54 comparison report's line citations, mtimes, and content.

| File | mtime | What changed | Kind |
|---|---|---|---|
| `00-overview.md` | 13:48 | Principles 2, 5, 6 (`:8,11,12`) scoped to "anatomy-governed" skills; `:16` declares the comparison report non-normative; `:33` pins the confirmed-digest invocation; `:121,127` add CAS paths. | Redesign plus reconciliation |
| `01-skill-anatomy.md` | 13:44 | `:3-7` "Every DevForgeAI skill except Research"; "anatomy-governed" at `:25,29,54,94,116,217`; `:221` Research failures produce no handoff. | Redesign; `:221` self-contradiction |
| `02-skill-roster.md` | 13:48 | Exemption at `:3,5,51`; `:64-67` a second status vocabulary (COMPLETE, READY_TO_SEAL, NEEDS_DECISION, BLOCKED, COULD_NOT_RUN, FAILED, CANCELLED) for Research only; `:109` now disclaims language detection. | Mixed |
| `03-brownfield.md` | 13:47 | `:26` code-mapper reports unknowns; `:54` "current design does not specify detection". | Reconciliation, adopts comparison rec 2 as a disclaimer |
| `04-dual-target.md` | 13:45 | `:105-108,127-129` conformance; `:131-136` explicit-only Research; `:138-146` attestation producer unresolved; `:148-160` removes `UNSUPPORTED_CAPABILITY`, envelope is `pass|fail|needs_user` only. | Redesign; contradicts `examples:251` |
| `05-subagent-sets.md` | 13:45 | `:3` exemption; `:78` research row becomes "contracts, Core does not launch them". | Redesign |
| `06-skill-specification.md` | 14:10 | NOT_EVALUATED at eight places; `:101-113` evidence table; `:103` "the available report" has no referent. | Reconciliation |
| `templates/skill-spec.md` | 14:10 | `:151,192,259,269,300,330` add Research-specific attestation and `E_PROVIDER_WORKER_EXECUTION_UNAVAILABLE` text to a generic template. | Scope creep |
| `examples/SKILL-SPEC-001-dev-tdd.md` | 13:48 | `:504,508,518-519` conformance; four `depends_on` hashes re-minted; `:251` still says `UNSUPPORTED_CAPABILITY`. | Now contradicts 04 |

The Research exemption itself predates today's edits: `04-dual-target.md:138-139` already read "For non-Research anatomy skills" when this session began, and the design digest taken before 13:00 already saw `framework/skills/research/` cited as normative in 00, 01 and 02. Today's edits widened it. Whether the user approved exempting one skill from the anatomy the user asked for ("each skill will require its own set of subagents … per phase") is not recorded anywhere in `docs/`.

## 6. Codex's decision table, with the reviewer's view

| Codex says the owner must decide | Reviewer's view |
|---|---|
| Research skill-spec authority, path, ID allocation, collision rule, version | Half decided already. `templates/skill-spec.md:23` fixes the ID pattern `^SKILL-SPEC-[0-9]{3}$`, `:5` requires `author`, and `02-skill-roster.md:137,146` fix the path for project-scoped specs under `docs/plan/<slug>/skill-specs/`. Genuinely open: where a framework-level spec with no plan slug lives, and the collision rule. Not a blocker for fixing sections 3.1 and 3.2. |
| Stack-neutral development: deterministic multi-language and monorepo command discovery | Agreed, and it is the comparison report's recommendation 2 and 6. It blocks dev, review and QA skill generation, not the Research Core. |
| Attestation trust and custody; worker broker and result schemas | Agreed for provider execution. It does not block closing the file set (3.1) or exposing the harness flag (3.2), both of which are Core-local. |
| Then a fresh current-spec quick run and Provider Conformance | Agreed, after the above. |

## 7. Required before merge

1. Close the run-directory file set: validate against an explicit allowlist per phase, reject unknown paths before seal, cover with a test that plants a stray file. Record directories and modes in the manifest, or state that they are out of scope. Skip only the top-level `MANIFEST.sha256`.
2. Either expose `allow_offline_test_harness` on the CLI or state in `tests/research/README.md` and `capability.md` that no run can pass preflight from the shipped interface.
3. Add `additionalProperties: false` to the four open nodes in `verification-packet.schema.json` and extend `test_unknown_fields_fail_closed` to all 21 schemas.
4. Add `jsonschema[format]` or `rfc3339-validator` to dependencies, and a test that a bad `date-time` is rejected.
5. Reject `global` as a slug or namespace the lock files.
6. Make lock acquisition not create directories or files for unknown runs.
7. Fix `tests/research/README.md:80` to state the work-order condition, the real constructor signature, the `RunRef` shape, and the `-t .` and `PYTHONPATH=components/research-core/src` run instructions.
8. Add `__all__` to `core.py`.
9. Restore consistency between `04-dual-target.md:148-160` and `examples/SKILL-SPEC-001-dev-tdd.md:251` on `UNSUPPORTED_CAPABILITY`, and fix `01-skill-anatomy.md:221` so Research either produces a handoff on failure or is explicitly excused from handoff rule 1.
10. Record the Research anatomy exemption as a decision with the user's approval, or revert it.

## 8. Follow-ups outside this review

- Refresh the line citations in `docs/research/sdd-landscape-comparison-2026-09-02.md`. The docs reviewer checked 24 and found 11 drifted. Wrong now: `01:104-105` (fixed by Codex), `01:174` (now 179), `02:108` (now 109 and the claim inverted), `03:54-58` (now 64), `03:61` (now 56, 62-64), `04:128` (token deleted), `05:75` (now 80), `06:102` (now 121), `00:130-135` (now 136). Two of the report's claims are now false: language detection is now explicitly disclaimed rather than asserted, and the envelope no longer carries `UNSUPPORTED_CAPABILITY` in 04.
- Move `templates/skill-spec.md`'s Research-specific attestation text into `framework/skills/research/` and leave the template generic.
- Reproducible wheel builds via `SOURCE_DATE_EPOCH` if wheel hashes are to be quoted as evidence.

## 9. Reproduction commands

```bash
# tests
PYTHONPATH=components/research-core/src python3 -m pytest tests/research -q
PYTHONPATH=components/research-core/src python3 -m unittest discover -s tests/research -t .

# provenance hashes (rule from 01-skill-anatomy.md:171-178)
# section = heading line to next heading of same or higher level, CRLF->LF, join LF, one trailing LF, sha256

# CLI dead-end and lock-file mutation
devforgeai-research --workspace /tmp/w normalize-request tests/research/fixtures/request-low.json
devforgeai-research --workspace /tmp/w open-run --confirmed-digest <digest> tests/research/fixtures/request-low.json
devforgeai-research --workspace /tmp/w2 render nonexistent-slug RUN-000001; find /tmp/w2

# stray-file seal: see section 3.1; uses tests/research/test_store.py build_to_p8
```
