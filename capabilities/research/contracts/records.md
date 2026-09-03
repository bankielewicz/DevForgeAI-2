# Canonical Research records

JSON and JSONL records are canonical. Markdown files are deterministic derived
views and never semantic authority.

## Dossier layout

```text
docs/research/
├── _cas/
│   ├── sha256/<first-two-hex>/<64-hex-digest>
│   └── quarantine/sha256/<claimed-digest>/
│       ├── QAR-000001.object
│       ├── QAR-000001.pending
│       └── QAR-000001.json
└── <slug>/
    ├── registry.jsonl
    ├── runs/RUN-000001/
    │   ├── request.json
    │   ├── run.json
    │   ├── provider-conformance.json
    │   ├── preflight.json
    │   ├── context-manifest.json
    │   ├── plan.json
    │   ├── state.jsonl
    │   ├── questions.jsonl
    │   ├── queries.jsonl
    │   ├── sources.jsonl
    │   ├── evidence.jsonl
    │   ├── claims.jsonl
    │   ├── contradictions.jsonl
    │   ├── verification-packets/VPK-000001.json
    │   ├── verifications.jsonl
    │   ├── synthesis.jsonl
    │   ├── decisions.jsonl
    │   ├── reconciliation.json
    │   ├── validation.json
    │   ├── handoff.json
    │   ├── source-sheets/SRC-000001-v001.md
    │   ├── README.md
    │   ├── synthesis.md
    │   ├── handoff.md
    │   └── MANIFEST.sha256
    ├── README.md
    ├── synthesis.md
    └── handoff.md
```

The equivalent local-only custody tree is
`.devforgeai/research-cas/{sha256,quarantine/sha256}`. A `.pending` file is the
exact proposed QAR receipt staged before the corrupt-object move. It is absent
after an uninterrupted transaction, but is intentionally preserved on failure
and consumed by the fail-closed orphan-recovery path. `QAR` identities are
allocated independently within each CAS class and claimed-digest directory;
they are quarantine custody identities, not normal dossier record IDs.

Quarantine trees are outside each sealed run. They are not traversed for
tracked-dossier byte accounting, are not copied into a run, and are not listed
in `MANIFEST.sha256`. The QAR receipt is authoritative only for the quarantine
event it records; it cannot support a Claim or Evidence record and does not
make the quarantined bytes an admitted Source.

Root Markdown files are replaceable views of the latest applicable sealed run.
A run is immutable after sealing. A correction creates a new run and explicit
run lineage through the new Request's `parent_run_id` and the resulting registry
entry's `supersedes_run_ids`. This is distinct from record-level `SUPERSEDES`,
which the current closable slice does not implement outside Decision records.

`plan.json` is the one canonical typed P3 delegation plan. It contains the
question-to-lane map, direct and contrary lanes, full worker envelopes, selected
budget and current aggregate use, dependency barriers, retry limits, partial
result policy, stop conditions, and reconciliation rule. Provider adapters and
workers may propose plan content, but Research Core owns validation and the sole
canonical write.

The required closed singleton objects are `run.json` (`research-run/v1`),
`provider-conformance.json` (`provider-conformance-attestation/v1`),
`preflight.json` (`research-preflight/v1`), `context-manifest.json`
(`research-context-manifest/v1`), `plan.json` (`research-plan/v1`),
`reconciliation.json` (`research-reconciliation/v1`), `validation.json`
(`research-validation/v1`), and `handoff.json` (`research-handoff/v1`). The
preflight, context manifest, plan, reconciliation, and validation identities
are `RUN-NNNNNN/<kind>` singleton artifact identities, not new global record-ID
families. The provider-conformance file is the exact externally governed
attestation evaluated at P0. Its `provider_kind` mechanically separates
`CLAUDE_CODE`, `CODEX`, and `OFFLINE_TEST_HARNESS`; offline support never proves
either provider runtime. Its `fixture_suite` is a closed provider-kind-specific
suite ID, version, manifest digest, and ordered required fixture-ID set; a
supported provider attestation must cover that exact set with no missing or
invented fixture. The validation schema reserves `READY_TO_SEAL` and
`FAILED`; the current Core creates a Validation record only after every
implemented successful-path check passes, so its emitted gate is
`READY_TO_SEAL`. It cannot contain a manifest, registry, readback, or predictive
sealed-success claim. Core creates it only while entering P9.
Its `subject_files` array is the sorted exact path, SHA-256, and byte length of
every run-local regular file present after rendering except `validation.json`
and `MANIFEST.sha256`. Later validation recomputes that set; it does not trust
the recorded subjects. It also reconstructs the complete Core-owned Validation
record while preserving only its recorded validation timestamp; any different
ID, scope, subject, check, reason, evidence reference, error, warning,
environment value, or gate fails validation.

Each canonical `research-question/v1` record is a materialization of one
confirmed Request question, not an editable restatement. Its `question_id`,
`text`, and ordered `completion_criteria` equal the Request entry exactly, and
its `priority` equals the Request risk tier. A same-ID semantic rewrite is
rejected before append and during later validation.

`state.jsonl` is the append-only run state journal. The current Core appends one
`EVT` for each legal P0-P9 transition. A successful journal ends at P9 with
reason code `READY_TO_SEAL`, never `COMPLETE`. The state-event schema reserves a
terminal form with `to_phase: null` and outcome `NEEDS_DECISION`, `BLOCKED`,
`FAILED`, `COULD_NOT_RUN`, or `CANCELLED`, but the current Core exposes no
operation that writes that form. The dossier's root `registry.jsonl` is
separate: it contains sealed-run registry entries only and never substitutes
for the state journal.

`verifications.jsonl` is the canonical P7 ledger of independent `VER` records.
Each `VER` references one Core-built canonical packet at
`verification-packets/VPK-NNNNNN.json`. A packet is an immutable single-Claim
projection, not a JSONL record: its SHA-256 and byte length cover its RFC 8785
payload without the file's terminating LF. It is included in the run manifest.
Its schema, exact content, cap, and verification bindings are specified in
[delegation.md](delegation.md#fresh-verification-packet).
For an active Claim, append order defines the current Verification: the last
linked `VER` is current. P7 cannot advance to P8 unless that current outcome is
`PASS`.

`handoff.json` is a singleton canonical document: it contains exactly one typed
`research-handoff/v1` object, never an array and never JSONL. Run-local and root
`handoff.md` are deterministic renderings of that object; they are not
canonical handoff records.

Internal file references are POSIX and relative to the run unless a schema
explicitly defines a workspace-relative subject. In particular,
`preflight.attestation.path` is exactly `provider-conformance.json`;
verification-packet and reconciliation result-artifact paths are run-relative;
and handoff canonical-artifact paths resolve within the same run. Provider
attestation adapter/evidence/trial subjects and non-request context-manifest
entries are workspace-relative. The selected request context entry is the
run-relative `request.json`. Core rejects absolute paths, backslashes,
traversal, symlinks, nonregular files, and digest mismatches at these
boundaries.

Research Core finalizes `handoff.json` and the run-local `handoff.md` before it
constructs `MANIFEST.sha256`. Each contains the full semantic handoff required
by [the handoff contract](handoff.md), but neither may contain any of these
post-finalization facts:

- the SHA-256 of its own serialized bytes or of the other handoff rendering;
- the SHA-256 of `MANIFEST.sha256`;
- a registry sequence, registry entry digest, or registry-head digest; or
- a post-publication readback result.

Those facts cannot be embedded without circularity or prediction. The manifest
binds the finalized `handoff.json` and run-local `handoff.md` bytes. The appended
registry entry then binds the manifest digest. A post-seal receipt reports that
completed closure without changing either handoff artifact.

## IDs and canonical metadata

`RUN`, `EVT`, and `VPK` are allocated by Research Core under the dossier writer lock.
The confirmed request supplies its `RSR` and `RQ` IDs. The Research Lead
proposes `QRY`, `SRC`, `EVD`, `CLM`, `CTR`, `VER`, `SYN`, `DEC`, and `HND`
IDs in records submitted to Core. Core admits them only after checking their
six-digit form and dossier-wide non-reuse under the same lock. Gaps are
permitted; reuse is forbidden. `VPK` uses the same dossier-wide six-digit
non-reuse rule but is never caller-proposed because only Core can construct a
verification packet.

`research-request/v1` is the pre-open, digest-confirmed request envelope. It
necessarily has no `run_id`, because `open-run` allocates the run only after the
exact request digest is confirmed. On success, Research Core persists the
confirmed request bytes unchanged as `request.json` and associates the new run
identity through a deterministic persisted envelope/header. That run binding is
outside the confirmed request bytes and does not alter or recalculate the
confirmed request digest.

Discovery candidates use the query-local identifier
`QRY-NNNNNN-CAND-NNNNNN`. A candidate ID is unique within its owning query and
is not a dossier-scoped canonical record ID. A discovery-derived Source records
the owning `QRY-NNNNNN` in `query_ids[]` and the exact compound candidate in
`candidate_ids[]`. Core permits each candidate in at most one Source record.
At close, every `RETRIEVE` candidate has exactly one Source attempt and every
other candidate disposition has none. A Source received directly rather than
through discovery records both arrays empty.

Every Query also records its exact planned `lane_id` and
`worker_envelope_id`. Core binds the Query questions, purpose, and attempt count
to that lane and envelope. A discovery-derived Source inherits question
provenance through its Query/candidate edges; it does not copy lane or envelope
fields.

The common canonical metadata below applies to post-open record entries, not to
the pre-open `research-request/v1` exception. The record schema and its
deterministic append/manifest envelope jointly carry the metadata. A record
contains only fields declared by its schema; the envelope supplies record-byte
custody fields that cannot be embedded without self-reference:

```text
schema_version, record ID, record version, run ID
lifecycle_status, readiness_status
owner, decision_authority
created_at_utc, referenced-subject digest when applicable
source_refs[], evidence_refs[], decision_refs[]
supersedes[], stale_if[]
```

In Core 0.1.0, `supersedes[]` must be empty for non-Decision records. Decision
records may supersede earlier Decision records. Corrective run lineage uses the
Request and registry fields described above, not a record edge.

All timestamps are UTC RFC 3339. A subject digest means only the SHA-256 of
external or referenced subject bytes, such as source content, an evidence
payload, a verification packet, or another artifact revision. Its concrete
field name is schema-specific, for example `source_sha256`, `content_sha256`,
`packet_ref.sha256`, or `claim_binding.claim_sha256`. The packet digest covers
the canonical packet payload; the Claim digest covers the full exact current
Claim record. A record with no external byte subject omits that field; its
semantic value is `NOT_APPLICABLE`. It must never place the digest of its own
serialized bytes in a subject field.

The SHA-256 of a canonical record's finalized serialized bytes belongs only in
the deterministic append receipt, containing JSONL entry envelope, adjacent
manifest, or dossier registry as defined by the applicable schema. This removes
self-reference: serialize first, then hash and record custody outside those
bytes.

## Noncanonical seal close receipt

After publication and successful readback, `seal-run` returns one
`research-seal-receipt/v1` object. This object is the complete CLI success
response; it has no outer wrapper and exactly these seven top-level fields:

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
  "readback": {
    "status": "PASS",
    "outcome": "COMPLETE"
  }
}
```

The angle-bracketed `handoff` value is a typed object placeholder, not a string.
The top-level and nested fields have these exact meanings:

| Field | Contract |
|---|---|
| `schema_version` | Constant `research-seal-receipt/v1`. |
| `run_id` | The sealed run whose handoff is being returned. |
| `sealed_run_path` | Repository-relative POSIX path `docs/research/<slug>/runs/<run_id>`. |
| `handoff` | Object parsed from the exact sealed `handoff.json` bytes; it validates as `research-handoff/v1` and is not regenerated or augmented. |
| `manifest_sha256` | SHA-256 of the exact finalized `MANIFEST.sha256` bytes read from the sealed run. |
| `registry.path` | Repository-relative POSIX path `docs/research/<slug>/registry.jsonl`. |
| `registry.sequence` | Positive integer sequence of the unique registry entry for `run_id`. |
| `registry.entry_sha256` | That entry's `entry_sha256`, computed over its RFC 8785 canonical JSON excluding `entry_sha256`. |
| `readback.status` | Constant `PASS`; Core re-read and validated the sealed run, manifest, unique registry binding, and published root views. |
| `readback.outcome` | Constant `COMPLETE`; only this post-publication receipt and the registry establish successful completion. |

The receipt is a noncanonical, post-seal result. Core does not write it under
the dossier, include it in the manifest or registry, treat it as semantic
authority, or assign it a record ID, timestamp, or digest of its own. Core may
regenerate it only when a new readback proves every closure property represented
by `readback.status`; historical success is not inferred. Any seal or readback
failure returns no receipt. The provider presents the `handoff` member together
with the closure fields; a human-readable presentation may show the sealed
run-local `handoff.md` and the remaining receipt fields together. The embedded
handoff's semantic authority derives solely from the sealed `handoff.json`; its
presence in the noncanonical receipt creates no second authoritative copy.

## Closed statuses

```text
lifecycle:
  DRAFT | PROPOSED | ACCEPTED | REJECTED | SUPERSEDED | ARCHIVED

readiness:
  NOT_READY | READY | STALE

gate_enforcement:
  BLOCK | REQUIRE_HUMAN | WARN | OFF

capability:
  NOT_PROBED | SUPPORTED | UNSUPPORTED_CAPABILITY

verification:
  NOT_RUN | PASS | FAIL | COULD_NOT_RUN | INFRA_FAILURE | NOT_APPLICABLE

phase_outcome:
  COMPLETE | NEEDS_DECISION | BLOCKED | FAILED | COULD_NOT_RUN | CANCELLED
```

In the current executable Core, `COMPLETE` appears only in the sealed-run
registry and the post-publication seal receipt. The successful canonical state,
validation, and handoff use `READY_TO_SEAL`. The other phase-outcome values are
schema vocabulary without a current Core operation that persists and seals
them.

Within the reserved phase-outcome vocabulary, `COULD_NOT_RUN` means a required
prerequisite or capability was unavailable before an applicable check could
execute. `INFRA_FAILURE` remains an implemented verification/check result when
a started check cannot reach a valid verdict because of its harness, timeout,
resource, or infrastructure. `NOT_RUN` is an implemented check result only for
an applicable check intentionally omitted under the confirmed schedule or
policy. Core 0.1.0 does not persist or seal the reserved phase outcome.

Phase `COULD_NOT_RUN` applies when Research cannot validly start. `BLOCKED`
applies when meaningful Research ran but cannot complete without an external
decision, authority, dependency, conflict resolution, or required input.

## Integrity and publication

- Research Core is the only canonical writer.
- An active run lives in framework staging; workers cannot write it.
- `MANIFEST.sha256` covers every finalized run-local file except itself.
- Publication uses exclusive creation and atomic replacement of derived root
  views only after readback verification.
- `registry.jsonl` appends one hash-chained entry per sealed run containing
  sequence, run ID, manifest digest, prior-entry digest, and entry digest.
- Registry entry digests use RFC 8785 canonical JSON excluding `entry_sha256`.
- Hashes demonstrate byte consistency, not authorship, identity, or protection
  from undetectable tail deletion without separately pinned custody.
- The Research workflow does not stage, commit, push, or publish Git changes.
