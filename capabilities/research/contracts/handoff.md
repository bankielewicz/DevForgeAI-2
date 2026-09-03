# Validation, sealing, and handoff contract

## Deterministic validation

After the semantic handoff and run-local views are finalized, the current Core
emits exactly 25 named checks. Each check has its own reason and retained
subject-file evidence. It reports `PASS` only for the implemented properties
below and uses `NOT_APPLICABLE` where stated:

- request schema, normalized digest, confirmation, authority, and write fence;
- the legal successful P0-P9 transition chain ending in the P9
  `READY_TO_SEAL` event;
- ID uniqueness and resolution of the reference sets Core currently implements:
  `source_refs`, `evidence_refs`, `decision_refs`, and the schema-specific
  Request, Question, Query, Source, Evidence, Claim, Contradiction,
  Verification, Synthesis, Decision, and Handoff links checked by Core;
- active Claims are the supported `SOURCE_FACT` class with exact scope and
  evidence edges; same-run derivation and supersession are rejected, so
  `CLAIM_DAG` is `NOT_APPLICABLE`;
- current fresh-verifier `PASS` for every published claim;
- LOW corroboration; MATERIAL and CRITICAL closure are unavailable;
- contrary lane and terminal disposition for every question;
- exact plan binding and terminal accounting for every Query, candidate, and
  worker lane;
- opened-source status plus retrieval, freshness, admission, and custody data for
  every admitted source;
- implemented Evidence and Contradiction edges; open material disputes prevent
  successful closure, so `DISPUTE_OWNERSHIP` is `NOT_APPLICABLE` on success;
- exclusion of stale records from current synthesis;
- CAS names, bytes, policy, 10 MiB object limit, and 100 MiB dossier limit;
- budget use within the confirmed request, including every actual counter's
  applicable confirmed ceiling;
- Markdown views byte-equal to a fresh deterministic render;
- the handoff identities, authorities, question dispositions, aggregate counts,
  contradiction details, selected artifact byte bindings, source basis,
  budget, decisions, exclusions, custody counts, and `READY_TO_SEAL` invariants.

`STALE_EXCLUSION` is `NOT_APPLICABLE` when no record is marked stale, and
`DECISION_AUTHORITY` is `NOT_APPLICABLE` when the run contains no Decision.
The remaining handoff prose fields listed below are schema-checked caller
statements; Core does not claim to derive or execute them.

This pre-seal validation cannot report a manifest digest, registry linkage, or
post-publication readback result. `seal-run` subsequently proves all of these
post-seal closure properties before it returns success:

- `MANIFEST.sha256` covers every finalized run-local file except itself,
  including the exact `handoff.json` and run-local `handoff.md` bytes;
- the dossier registry has exactly one valid entry for the run and that entry
  binds the manifest digest;
- the published root views are byte-equal to the deterministic views selected
  from the sealed run; and
- a fresh readback of the sealed run, manifest, registry binding, and root views
  passes.

Deterministic validation does not decide semantic truth, legal interpretation,
source completeness, or downstream applicability.

## Successful close order

P8 must already contain every caller-authored canonical record, including one
`handoff.json` whose location is P9/`ready-to-seal` and whose result is
`READY_TO_SEAL`. The close then uses these public operations in order:

1. `transition-run <slug> <run-id> P9` validates the closing inputs without a
   validation record.
2. Core appends and fsyncs the P9 state event with reason code
   `READY_TO_SEAL`.
3. Core generates the deterministic run-local Markdown views and source sheets;
   each write is atomic and fsynced.
4. Core repeats deterministic validation against those exact bytes.
5. Core writes and fsyncs the singleton `validation.json`, with pre-seal gate
   status `READY_TO_SEAL`, then validates its exact state and subject-file
   bindings.
6. `validate-run <slug> <run-id>` reports whether the P9 staging run is valid.
   It does not publish or mutate the run.
7. `seal-run <slug> <run-id>` validates staging, generates and fsyncs
   `MANIFEST.sha256` excluding itself, and atomically moves the run into the
   sealed dossier.
8. Core verifies the sealed manifest, generates and atomically publishes the
   three root current views from the sealed run, and reads every view back
   byte-for-byte.
9. Core atomically appends and reads back the hash-chained dossier registry
   entry, then independently validates the sealed run, manifest, registry
   binding, and root views.
10. Core re-reads the exact sealed `handoff.json`, constructs the noncanonical
    `research-seal-receipt/v1`, and returns that receipt as the unwrapped
    `seal-run` success payload. It does not render, mutate, or rewrite either
    sealed handoff artifact.

If a crash leaves a P9 staging run without run-local views or
`validation.json`, `seal-run` may repeat steps 3 through 5. It does not replace
an existing invalid validation record.

Failure before publication returns an error and may leave unsealed staging; it
does not promise that the run can resume or complete. If failure occurs after
the atomic staging-to-final move, the immutable final run is retained. A later
identical `seal-run` validates those exact run and manifest bytes, writes and
reads back all required root views, and atomically appends the registry entry
only when absent. `COMPLETE` is not exposed in the registry until all root
views have passed byte readback; an interrupted registry append exposes either
the prior chain or the complete new entry. Conflicting registry state, changed
sealed bytes, or a failed final readback remains an integrity error. The current
Core does not append a `FAILED` terminal state event. No failure path returns a
seal receipt.

The `seal-run` success payload is exactly this structural shape, with no outer
wrapper or additional top-level fields:

```text
{
  "schema_version": "research-seal-receipt/v1",
  "run_id": "RUN-NNNNNN",
  "sealed_run_path": "docs/research/<slug>/runs/RUN-NNNNNN",
  "handoff": <research-handoff/v1 object>,
  "manifest_sha256": "<64 lowercase hexadecimal characters>",
  "registry": {
    "path": "docs/research/<slug>/registry.jsonl",
    "sequence": 1,
    "entry_sha256": "<64 lowercase hexadecimal characters>"
  },
  "readback": {"status": "PASS", "outcome": "COMPLETE"}
}
```

The angle-bracketed `handoff` value is a typed object placeholder, not a string.
It is parsed from the sealed run's canonical `handoff.json`, validates as
`research-handoff/v1`, and is not augmented. The exact field semantics are
defined in
[Canonical Research records](records.md#noncanonical-seal-close-receipt). The
provider presents the embedded semantic handoff and the closure fields together.
The receipt is not a canonical Research record and none of its post-seal closure
fields may be copied into the canonical handoff.

## Required handoff fields

| Section | Required content |
|---|---|
| Location | Project, slug, run ID, workflow, phase/subphase, and `YOU ARE HERE` |
| Result | Closed outcome token, reason code, and plain-language meaning |
| Questions | Every RQ ID and terminal disposition |
| Claims | Counts by class, readiness, dispute, and verification; material Claim IDs and limitations |
| Sources | Counts by admission, retrieval, custody, and the explicit `source.freshness.status` value |
| Contrary evidence | Open/resolved contradictions and uncovered conflict scope |
| Exclusions | Declared exclusions and areas not searched |
| Budget | Confirmed profile/overrides and actual aggregate use |
| Canonical artifacts | In the current executable slice this is a caller-selected, non-exhaustive list. Each supplied entry identifies a canonical JSONL record by exact record ID. Version, owning ledger path, lifecycle, readiness, owner, and verification status are derived from that record; SHA-256 and optional byte length bind the exact complete ledger file. Non-Claim/non-Verification records use `NOT_APPLICABLE`; a Claim uses its current Verification outcome; a Verification uses its own outcome. Every path is run-relative POSIX, resolves to a nonsymlink regular file inside the run and confirmed write fence, and excludes `handoff.json`, run-local `handoff.md`, `MANIFEST.sha256`, and `registry.jsonl`; registry sequence/head/entry fields are also excluded. |
| Source basis | Input artifact IDs/revisions and context-manifest ID/digest |
| Validation | Checks, results, environment, evidence IDs, and checks not run |
| Decisions | Research-process decisions and named authorities |
| Custody | Tracked, local-only, extract-only, and unavailable evidence requirements |
| Conclusion status | `PROPOSED` unless separately accepted by the downstream owner |
| Open items | Ambiguities, risks, blocked items, and owners |
| Next action | Exactly one copy-pasteable provider-specific invocation with all required arguments |
| Session | Continue or start fresh, with reason |
| Authority/fence | What the next workflow may read/write and what needs approval |
| Repair route | Exact owning workflow and invocation if the next gate fails |

The exclusions in the Canonical artifacts row prevent self-reference. Core
validates every supplied entry but does not compute an exhaustive eligible set;
absence from this selected index is not proof that an artifact was absent from
the run. `handoff.json` and run-local `handoff.md` also must not contain
post-publication readback results. Manifest, registry, and readback facts appear
only in the adjacent seal receipt.

Core derives and compares the location identity, authorities, question
dispositions, Claim/Source/Contradiction/custody counts, material Claim IDs,
source basis, accepted Decision IDs, exclusions, and budget fields. It
schema-checks but does not semantically derive `limitations`, validation check
names, validation environment prose, `next_action`, session guidance,
authority-fence prose, or the repair invocation. Those fields are
caller-authored instructions for human review and are not evidence of provider
executability.

An embedded run returns to its recorded caller. A standalone run does not assume
Brainstorming; its continuation comes from the confirmed request and outcome.
Research never invokes the next workflow automatically.

Contradiction detail entries are an exact ID-to-status-and-description
projection of canonical Contradiction records; counts alone are insufficient.
Every evidence ID named by a handoff validation check resolves to canonical
Evidence. A `READY_TO_SEAL` handoff has only `PASS` validation checks and an
empty `checks_not_run` list. These handoff summaries do not replace the
Core-owned P9 `validation.json`.

## Acceptance boundary

The offline Core suite exercises the implemented request, singleton-gate,
record, verification-packet, CAS, rendering, publication, packaging, and
readback contracts. The detailed tested boundary is maintained in
[the black-box test contract](../../../tests/research/README.md).

Provider-runtime acceptance has not run, and the manual source templates are
not installed. Before any adapter can be labeled supported, an independently
governed acceptance suite must distinguish at least these cases:

- deterministic normalization and digest for repeated reads of the same complete
  request file, plus rejection of inline and short-form provider input before
  search or canonical write;
- no search or canonical write before confirmation;
- implicit/advisory request cannot persist;
- writer collision;
- snippet offered as evidence;
- static code presented as runtime proof;
- user observation generalized universally;
- missing MATERIAL corroboration and non-independent duplicate sources;
- contrary primary evidence and bounded negative claims;
- prompt injection in source content;
- requested executable or provider proof routed out of Research;
- capability unavailable before start versus dependency lost after useful work;
- worker retry exhaustion and budget exhaustion;
- attempted mutation of a Claim after verification;
- CAS digest collision and tracked-size thresholds;
- sealed-byte mutation and stale derived view;
- open CRITICAL dispute;
- cold-session reconstruction from canonical IDs;
- absent/stale Provider Conformance attestation;
- missing or unsupported hook without false `PASS`.

That provider acceptance is an unsatisfied release condition, not a result of
this repository. It requires every deterministic test to pass. For each
`trials[].fixture_id`, a supported Claude or Codex attestation bound to the exact
pinned provider version and adapter digest contains exactly five fresh
`ENABLED` trials and five fresh `DISABLED` trials, all `PASS`, with session IDs
unique across the attestation. The exact runtime fixture suite is
`devforgeai-research-provider-runtime` version `1.0.0`, manifest SHA-256
`ff76986b52a46adb438a721770251465883b1d5cad3ceb1ae842bd968bfdc2c4`.
Its ordered, closed `required_fixture_ids` value is:

```text
request-file-normalization-and-input-rejection
confirmation-before-search-or-write
implicit-request-no-persistence
writer-collision
snippet-evidence-rejection
static-code-runtime-proof-rejection
user-observation-universalization-rejection
material-corroboration-and-source-independence
contrary-primary-and-negative-claim-bounds
prompt-injection-source-content
out-of-scope-executable-or-provider-proof
capability-unavailable-versus-dependency-loss
retry-and-budget-exhaustion
verified-claim-mutation
cas-collision-and-size-thresholds
sealed-byte-mutation-and-stale-view
open-critical-dispute
cold-session-reconstruction
provider-attestation-absence-and-staleness
missing-or-unsupported-hook
```

Consequently, a supported runtime attestation contains exactly 200 trials. Its
`fixture_suite` object must equal the runtime constant in
[`provider-conformance.schema.json`](../../../schemas/research/v1/provider-conformance.schema.json).
The manifest digest is the Research canonical-JSON SHA-256 of the UTF-8 object
containing `schema_version`, `suite_id`, `suite_version`, and the ordered
`required_fixture_ids`, with `manifest_sha256` omitted and no trailing LF.

The offline harness is bound separately to
`devforgeai-research-offline-core` version `1.0.0`, manifest SHA-256
`a1d149d6fccb6721e9d4fb4532465f193fd3d98d28642ad3553e2bdd7ac9a65a`,
and the sole required fixture `offline-core-acceptance`. It has exactly one
`NOT_APPLICABLE` `PASS` trial. It cannot satisfy or be added to the provider
runtime suite. All evidence is retained, with zero prohibited
mutations, unsupported published claims, silently discarded contradictions,
invalid manifests, unresolved references, or implicit canonical writes. No
hallucination-reduction claim has been established by the offline suite.
