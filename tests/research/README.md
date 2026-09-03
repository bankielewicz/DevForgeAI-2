# Research Core black-box test contract

These tests are intentionally offline and use only synthetic sources. They target
`devforgeai.research.store` and assume this public API:

```python
normalize_request(mapping) -> (normalized_mapping, sha256_digest)
ResearchStore(project_root)
ResearchStore.open_run(normalized_request, confirmed_digest) -> RunRef
ResearchStore.append_record(slug, run_id, record_kind, mapping) -> sha256_digest
ResearchStore.put_source(slug, run_id, source_id, source_path, metadata) -> source_mapping
ResearchStore.transition(slug, run_id, to_phase, reason=None) -> event_or_phase
ResearchStore.validate_run(slug, run_id) -> ValidationReport
ResearchStore.seal_run(slug, run_id) -> sealed_run_directory
ResearchStore.seal_result(slug, run_id) -> research-seal-receipt/v1
ResearchStore.verify_run(slug, run_id) -> ValidationReport
ResearchStore.render(slug, run_id) -> deterministic_nonpublishing_render
ResearchStore.render_handoff(slug, run_id) -> deterministic_nonpublishing_handoff
ResearchStore.resume_run(slug, run_id) -> RunRef
```

`ResearchStore` is the sole canonical writer. Its root is a project root, and it
writes only within the confirmed Research fence: the slug dossier and tracked
CAS under `docs/research/`, plus staging, locks, and local-only CAS under
`.devforgeai/`. Methods fail before mutation when an input is invalid. `seal_run`
is idempotent for identical finalized bytes, while all post-seal mutations fail
closed. Workflow phases are `P0` through `P9`.
The canonical CLI operation for phase mutation is `transition-run`; successful
CLI `seal-run` emits the nonpersisted seven-field `research-seal-receipt/v1`.
Applicability authority is captured by the request/record contracts; Research
conclusions remain `PROPOSED` rather than silently becoming project policy.

`RunRef` exposes `.slug` and `.run_id`. Validation reports may contain additional
fields; tests rely on `.ok` (or an equivalent boolean result), schema fields, and
canonical paths defined by the v1 contracts.

## Implemented offline boundary

The current implementation is an offline deterministic Core, not provider
runtime acceptance. The black-box suite covers:

- exact request normalization, interactive digest confirmation, run allocation,
  exact question-semantic binding, fixed budget-profile ceilings and named
  override binding, write fences, P0-P9 state chaining, and legal repair
  transitions;
- exact provider-attestation/preflight, context-manifest, P3 plan, and P6
  reconciliation singleton gates, including provider-kind-specific fixture
  suite ID/version/manifest digest/required-ID binding, exact retention of
  request source, freshness, and stop-condition policy text;
- phase-fenced question, query, source, evidence, claim, contradiction,
  verification, synthesis, decision, and handoff records;
- network/source admission, bounded excerpts, tracked/local CAS, global
  nonblocking CAS serialization, no-replace installation, quarantine, and
  interrupted-quarantine recovery;
- exact plan lanes, worker envelopes, Query-to-lane/envelope/purpose bindings,
  per-lane and per-envelope Query attempt limits, reconciliation artifacts,
  exact-once Query-only lane acceptance, concurrency, and aggregate budget
  bindings;
- Core-built one-Claim verification packets, automatic P6-to-P7 packet
  construction, packet caps, exact candidate-to-packet cardinality,
  current-revision binding, a blocking P7-to-P8 current-`PASS` gate, and
  deterministic `OFFLINE_TEST_HARNESS` verification;
- supported LOW `SOURCE_FACT` closing checks, contrary
  coverage, source-class admission, synthesis authority, and exact
  handoff/source/budget accounting;
- P8-to-P9 run-local rendering, Core-owned 25-check pre-seal validation, exact
  whole-record validation reconstruction, bound handoff
  artifact/contradiction/validation summaries, `READY_TO_SEAL`
  state/handoff/validation semantics, manifest sealing, crash-retryable
  hash-chained registry publication, root views, readback, and the seven-field
  receipt; and
- wheel contents, the console entry point, all 21 v1 schemas, and the exact ten
  advertised public long operations.

## Explicit nonconformance boundary

The following are not implemented, and tests MUST NOT imply otherwise:

- accepted parent-work-order authority; `open-run` fails before mutation with
  `E_NOT_IMPLEMENTED_WORK_ORDER_AUTHORITY`;
- provider-asset installation or synchronization, trusted worker launch,
  provider-session freshness, external retrieval execution, or Claude/Codex
  runtime conformance;
- authentication of a Provider Conformance evaluator, signatures, an issuer
  registry, or governance authority. Core binds the submitted subject, version,
  adapter/evidence/trial data and requires
  `evaluator.independent_of_subject: true`, but structural validity alone is not
  independently trusted release evidence;
- acceptance of a `PROVIDER_AGENT` `PASS`; only the explicitly typed
  deterministic offline harness can produce a positive Core fixture;
- independent observation of provider model-token/byte, tool-call,
  elapsed-time, lane, concurrency, or retry use; Core validates the submitted
  reconciliation aggregates and binds them to handoff limits;
- semantic execution of free-text completion, freshness, or stop-condition
  prose; Core preserves and binds those strings and validates only their typed
  companion fields and explicit reconciliation assertions;
- closing an active claim class other than `SOURCE_FACT`, waiver-based bypass of
  missing corroboration, MATERIAL source-independence acceptance, or CRITICAL
  specialist review;
- automatic 30/90-day or version-change freshness calculation; Core validates
  explicit typed freshness records against request `as_of` only;
- a Core operation for non-success terminal state events, partial/failed run
  sealing, or binding a CAS quarantine receipt into such a terminal record; and
- complete derivation-cycle, qualification, and supersession semantics for the
  currently unclosable claim classes.

The wheel packages the Core and all 21 schemas. Provider skills and agent
profiles remain manual, uninstalled source templates; there is no
provider-asset installer or sync manifest.

Research Core 0.1.0 supports Linux only. Construction on another platform fails
with `E_PLATFORM_UNSUPPORTED` before any workspace mutation. The implementation
requires `fcntl`, `O_NOFOLLOW`, directory `fsync`, and Linux
`renameat2(RENAME_NOREPLACE)`; Python 3.11 availability alone is not sufficient.

The filesystem implementation rejects fixed symlink escapes and checks source
and CAS bytes before admission, but it is not a complete directory-descriptor,
race-proof transaction across every filesystem operation. A process crash
after immutable CAS installation but before the corresponding source-record
append can also leave an unreferenced CAS object. Such an object is not evidence
and requires a future deterministic garbage-collection policy; it MUST NOT be
deleted heuristically by a provider adapter.

Run the complete offline slice from the repository root with:

```bash
PYTHONPATH=python python3 -m unittest discover -s tests/research -v
```
