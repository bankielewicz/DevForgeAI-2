# Evidence, claims, corroboration, freshness, and custody

## Source lifecycle

```text
DISCOVERED_LEAD
  -> RETRIEVED_CANDIDATE
     -> ADMITTED_EVIDENCE
     -> ADMITTED_CONTEXT
     -> BIBLIOGRAPHY_ONLY
     -> REJECTED
```

Closed values:

```text
retrieval:
  NOT_ATTEMPTED | RETRIEVED | PARTIAL | UNAVAILABLE | ACCESS_DENIED | ERROR

source_admission:
  PENDING | ADMITTED_EVIDENCE | ADMITTED_CONTEXT | BIBLIOGRAPHY_ONLY | REJECTED

custody:
  TRACKED_CAS | LOCAL_ONLY_CAS | EXTRACT_ONLY | NONE

question_disposition:
  ANSWERED | PARTIALLY_ANSWERED | UNRESOLVED | OUT_OF_SCOPE | SUPERSEDED

dispute:
  NONE | OPEN | RESOLVED
```

These tokens are the canonical record values. `retrieval` is the source
record's retrieval status, `source_admission` is its separate admission status,
and `question_disposition` is the per-question disposition in a synthesis
record. No alias, case conversion, or lifecycle-status substitute is permitted.

Search snippets, catalog entries, stars, popularity, and worker summaries are
leads only. A source supports a claim only after the underlying material was
opened and admitted for a named role and scope. Unavailable and rejected
sources remain recorded with exact reasons.

Every discovery-derived Source records both its owning `query_ids[]` and the
exact `candidate_ids[]` selected for retrieval. Each `RETRIEVE` candidate must
resolve to exactly one Source attempt before close; the Source may record
`RETRIEVED`, `PARTIAL`, `UNAVAILABLE`, `ACCESS_DENIED`, or `ERROR`. Candidates
with any other disposition must resolve to zero Sources. A directly supplied
Source that did not originate in discovery records both arrays empty. This
linkage is accounting provenance, not evidence admission.

## Network authority

`DENY` permits only `LOCAL_FILE` and `SUPPLIED_BYTES` retrieval methods, with
`network_accessed: false`. `WEB` and `MCP` are network methods and require
`network_accessed: true` plus a URL locator. `OPEN` permits such access without
an origin restriction. `ALLOWLIST` permits it only when the URL's canonical
HTTP(S) origin is an exact member of the confirmed `network_allowlist`.

An allowlist entry is exactly `http://host[:port]` or
`https://host[:port]`: lowercase IDNA host, no credentials, path, query, or
fragment, and no explicit default port (`:80` for HTTP or `:443` for HTTPS).
Matching is exact after the same origin normalization; it does not perform a
suffix, wildcard, or substring match. Core rejects a contradictory method,
`network_accessed`, locator, or policy tuple before CAS or source-record writes.

A local repository source records origin URL when available, exact `HEAD`,
dirty-state observability, inspected paths, and file/blob digests. Static
inspection establishes only what is in those bytes. It does not establish
runtime behavior, safety, quality, scalability, or provider execution.

## Claim classes and evidence edges

The closed `claim_type` enum is exactly the six values in this table. No other
claim type and no `ASSUMPTION` claim type is permitted.

| Class | Meaning | Required evidence |
|---|---|---|
| `SOURCE_FACT` | Scoped statement of what a source documents | Open admitted source, version, anchors, limitations |
| `STATIC_OBSERVATION` | Direct observation of pinned local or retained bytes | Subject digest, method, paths/anchors |
| `IMPORTED_EMPIRICAL_OBSERVATION` | Result from a separately governed experiment | Immutable external evidence package and exact environment |
| `USER_OBSERVATION` | Attributed experiential report | Reporter and known date/environment; unknowns explicit |
| `INFERENCE` | Reasoning derived from existing claims | Supporting and contrary Claim IDs plus reasoning |
| `PROPOSAL` | Recommended option, not accepted policy | Verified supporting/contrary claims, alternatives, tradeoffs, owner |

The v1 schema admits all six classes, but the current executable Core closes and
seals only active `SOURCE_FACT` claims. Any active claim of another class fails
closing validation with `E_NOT_IMPLEMENTED_CLAIM_CLASS:<claim-id>`. A rejected,
superseded, or stale non-`SOURCE_FACT` record is retained as history but is not
published.

A decision is not a claim class. `decisions.jsonl` records only named human
Research-process decisions such as scope, budget, access, and permitted waiver.
Downstream product decisions remain in their owning workflow.

The current closable slice implements `SUPPORTS` through Claim
`support_evidence_ids` and `CONTRADICTS` through Claim `contradiction_ids` plus
Contradiction records. `QUALIFIES` and record-level `SUPERSEDES` are reserved
vocabulary only; Core rejects non-Decision record supersession and does not
publish those edges.

Every Claim contains an explicit closed scope:

```yaml
scope:
  include:
    - "condition, population, version, environment, or boundary where the text applies"
  exclude:
    - "named boundary where the text must not be generalized"
```

`include` contains at least one non-empty item. Both arrays contain unique
items. Scope is part of the exact immutable Claim record and its SHA-256
binding. Mutation is an integrity failure. The current Core has no same-run
Claim revision or supersession operation; a scope change requires a new run.
The P6 Claim status is `CANDIDATE`, `REJECTED`, `SUPERSEDED`, or `STALE`.
`PUBLISHABLE` is not a caller-authored Claim status. Core derives whether an
active `CANDIDATE` is publishable from a current, packet-bound Verification
`PASS` and all applicable risk, source, contradiction, and close gates. A P6
Claim never names a future `VER` ID.

Each claim records this confidence structure; no aggregate numeric confidence
score is permitted:

```yaml
confidence:
  source_fidelity: HIGH | MEDIUM | LOW | UNASSESSED
  scope_match: EXACT | PARTIAL | UNKNOWN
  freshness: CURRENT | AGING | STALE | UNKNOWN
  corroboration: NONE | SINGLE | MULTIPLE_INDEPENDENT
  empirical_support: NONE | STATIC | EXECUTED | REPLICATED
  contradiction: NONE_KNOWN | OPEN | RESOLVED
  rationale: "bounded explanation"
unknowns: []
```

## Risk-tier corroboration

| Risk | Publication threshold | Missing evidence route |
|---|---|---|
| `LOW` | One direct admitted evidence item per claim; authoritative primary source for normative facts; contrary lane per question; fresh verification | Claim remains unpublished |
| `MATERIAL` | LOW rules; volatile, comparative, safety, performance, scalability, and observational claims require two independent evidence items | Named human waiver with rationale, scope, and expiry where policy permits |
| `CRITICAL` | MATERIAL rules, retained or independently stable evidence, and mandatory named specialist review | No Research waiver may replace specialist review |

The current Core closes only LOW `SOURCE_FACT` runs. Publisher strings and
content digests are insufficient proof of independent ownership/data
generation, so every MATERIAL or CRITICAL positive Verification is rejected
with `E_NOT_IMPLEMENTED_MATERIAL_INDEPENDENCE`. It validates named Research
decision records but does not use a waiver to bypass a gate. CRITICAL closing
also fails with `E_NOT_IMPLEMENTED_CRITICAL_SPECIALIST_REVIEW`.

Two items are independent only when their originating ownership/data generation
differs, or one is an authoritative contract and the other is an independently
captured observation. Two agents summarizing one source, two pages derived from
one vendor statement, or repeated citations to one dataset remain `SINGLE`.

Every question requires a contrary/disconfirmation lane. A negative claim must
name the bounded corpus, versions, exact method, patterns, and exclusions, and
use `NONE_OBSERVED_WITHIN_SCOPE`. Open-web research never proves universal
absence.

## Verification evidence boundary

Fresh verification consumes the canonical one-Claim packet defined in
[delegation.md](delegation.md#fresh-verification-packet). Source and Evidence
records in that packet are exact canonical records, not summaries. The verifier
must return all eight named checks; Core independently resolves the packet and
immutable Claim record, checks the exact ID sets, validates retained-object custody,
and rejects a structurally false `PASS` for source admission, freshness,
custody, or risk-tier corroboration.

Entailment and scope match remain verifier judgments. In the current executable
slice, only the deterministic `OFFLINE_TEST_HARNESS` path may produce an
accepted positive result, and that result is evidence about Core behavior only.
Claude Code and Codex `PROVIDER_AGENT` positives remain unavailable until a
trusted broker and current provider-conformance attestation can be validated.

## Provider freshness policy not implemented by Core

The following values are requirements for a future provider request builder,
not defaults computed or proven by the current Core:

- Provider/runtime and similarly volatile claims: reopen every run; stale after
  30 days or a version change, whichever occurs first.
- Mutable web documentation: reopen after 90 days or whenever the request's
  `as_of` date requires a newer view.
- Pinned standards, source revisions, and Git commits: no age-only expiry;
  refresh on consuming-version change or discovered supersession.
- User observations remain permanently scoped to their recorded date and
  environment; freshness does not generalize them.
- A request may set a shorter period; the stricter rule wins.

The current Core requires explicit `checked_at`, `stale_after`, status, basis,
and rationale values, checks their timestamp relations and request `as_of`
boundary, and rejects `STALE` claim support. It does not derive 30/90-day or
version-change deadlines from free text or source type. Provider adapters remain
unsupported and must not claim that calculation occurred.

## CAS custody

Every retained object is addressed by SHA-256. The source record says whether
the bytes are a raw response, decoded document, tool-rendered text, screenshot,
or local file blob. Tool-rendered extraction is never labeled raw capture.

Every `put-source` request carries this complete `retention_policy` object:

```yaml
retention_policy:
  retention_permitted: true | false
  redistribution_basis: SPDX_LICENSE | PUBLIC_DOMAIN | OWNER_PERMISSION | USER_OWNED | NONE
  redistribution_reference: "non-empty license, permission, or ownership reference" | null
  data_classification: PUBLIC | INTERNAL | CONFIDENTIAL | RESTRICTED
  sensitive_scan:
    status: PASS | FAIL | NOT_RUN | COULD_NOT_RUN | INFRA_FAILURE
    scanner_id: "non-empty scanner identity"
    ruleset_sha256: "64 lowercase hexadecimal characters"
    findings_count: 0
```

The object is invalid and `put-source` fails before mutation if any field is
absent, any value is outside its closed enum, `scanner_id` is empty,
`ruleset_sha256` is not 64 lowercase hexadecimal characters, or
`findings_count` is negative. An affirmative `redistribution_basis` requires a
non-empty `redistribution_reference`; `NONE` requires
`redistribution_reference: null`. Any other basis/reference combination is
invalid.

`sensitive_scan` has these exact invariants:

- `PASS` requires `findings_count: 0`.
- `FAIL` requires `findings_count` of at least 1.
- `NOT_RUN`, `COULD_NOT_RUN`, and `INFRA_FAILURE` require
  `findings_count: 0`, because no valid findings set was produced.
- `scanner_id` identifies the scanner selected for the policy even when it did
  not run. `ruleset_sha256` identifies the exact selected ruleset in every
  status.
- Only `PASS` is eligible for tracked custody. No other status is interpreted
  as a clean scan.
- A status/count combination that violates these rules invalidates the policy;
  it does not trigger local-only fallback.

Tracked CAS path:

```text
docs/research/_cas/sha256/<first-two-hex>/<64-hex-digest>
```

An object resolves to `TRACKED_CAS` if and only if every condition below is
true:

1. `retention_permitted` is `true`.
2. `redistribution_basis` is `SPDX_LICENSE`, `PUBLIC_DOMAIN`,
   `OWNER_PERMISSION`, or `USER_OWNED`; `NONE` is not affirmative.
3. `redistribution_reference` identifies the applicable basis.
4. `data_classification` is `PUBLIC`.
5. `sensitive_scan.status` is `PASS` and `findings_count` is `0`.
6. The object is no larger than 10 MiB, exactly 10,485,760 bytes.
7. Adding its digest keeps the dossier's sum of unique tracked-object byte
   lengths at or below 100 MiB, exactly 104,857,600 bytes. A digest already
   counted by that dossier contributes zero additional bytes.

No subset of those conditions is sufficient. A policy assertion records
custody authorization; it is not a legal opinion or provider-conformance claim.
Research Core computes the object digest and byte length from the opened source
descriptor and computes aggregate usage from canonical tracked-CAS references;
caller-supplied digest, size, or aggregate values are not eligibility evidence.

Research Core serializes tracked and local-only CAS mutations with the one
nonblocking lock `.devforgeai/research-locks/global.lock`. Contention returns
`E_CAS_WRITER_COLLISION`; it never waits. Under that lock, Core opens source
and regular CAS objects with `O_NOFOLLOW`, classifies nonregular directory
entries with `lstat`, hashes regular entries from their opened descriptors,
and verifies stable file identity. A matching object is reused. A new object
is installed only with Linux `renameat2(RENAME_NOREPLACE)`, followed by file
and directory `fsync` and independent digest readback. Core fails closed when
`O_NOFOLLOW` or `renameat2(RENAME_NOREPLACE)` is unavailable. It never uses an
overwrite, copy/unlink, or ordinary-rename fallback.

An existing claimed path with the wrong bytes or a nonregular entry is a CAS
integrity incident. While retaining the same global lock, Core reopens or
reclassifies the entry without following it and atomically moves the entry,
without replacement, into the matching CAS class:

```text
docs/research/_cas/quarantine/sha256/<claimed-sha256>/<QAR-id>.object
.devforgeai/research-cas/quarantine/sha256/<claimed-sha256>/<QAR-id>.object
```

`QAR-id` is the lowest unused `QAR-NNNNNN` within that CAS class and claimed
digest directory. Any occupied `QAR` stem is skipped; no object, pending
receipt, or finalized receipt is overwritten. The finalized canonical receipt
is `<QAR-id>.json`. It is RFC-8785 canonical JSON with one trailing newline and
exactly these fields:

| Field | Contract |
|---|---|
| `schema_version` | Constant `research-cas-quarantine-receipt/v1`. |
| `quarantine_id` | The allocated `QAR-NNNNNN`. |
| `cas_class` | `TRACKED_CAS` or `LOCAL_ONLY_CAS`. |
| `run_id`, `slug`, `proposed_source_id` | The attempted admission that detected the corrupt entry. |
| `original_path` | Repository-relative claimed CAS object path. |
| `quarantine_path` | Repository-relative path of `<QAR-id>.object`. |
| `entry_type` | `REGULAR_FILE`, `SYMLINK`, `DIRECTORY`, `FIFO`, `SOCKET`, `CHAR_DEVICE`, `BLOCK_DEVICE`, or `OTHER`. |
| `claimed_sha256` | The 64-lowercase-hex digest asserted by the original object name. |
| `actual_sha256`, `actual_byte_length` | Descriptor-derived values for `REGULAR_FILE`; JSON `null` for every nonregular entry, which Core never opens as content. |
| `detected_at` | UTC RFC 3339 time at which this quarantine transaction began. |

Before moving the corrupt entry, Core exclusively writes and flushes the exact
proposed receipt bytes as `<QAR-id>.pending`. After the no-replace move, it
flushes the moved regular object when applicable and both affected directories,
reclassifies and rehashes the moved entry, promotes the unchanged pending bytes
to `<QAR-id>.json` with `renameat2(RENAME_NOREPLACE)`, flushes the receipt
directory, and performs no-follow receipt readback. A later invocation recovers
an interrupted object/pending pair before considering an incoming install and
returns an integrity failure for that recovery invocation. Only a subsequent
invocation may install the now-absent valid object.

A successfully finalized quarantine returns `E_CAS_INTEGRITY` with the QAR ID,
receipt path, and receipt-byte SHA-256. Any rename, object flush, directory
flush, receipt creation, promotion, or readback failure returns
`E_CAS_QUARANTINE_FAILED`. Core preserves whichever original, quarantined,
pending, or finalized bytes remain; it neither rolls them back nor installs the
incoming object. Both errors occur before `sources.jsonl` append. QAR objects
and receipts are never Sources or Evidence and are excluded from normal CAS
quota accounting and sealed-run manifests. Binding a QAR receipt into a
canonical `FAILED` handoff or terminal state-evidence record is outside the
current executable Core and remains not implemented.

When source bytes were submitted for tracked retention,
`retention_permitted` is `true`, and any tracked-only condition 2 through 7
fails, Research Core resolves custody to `LOCAL_ONLY_CAS` and records every
failed tracked condition in the custody retention reason. A request for
`LOCAL_ONLY_CAS` also requires `retention_permitted: true` and resolves directly
to local-only custody. These are the only byte-retaining fallback paths. Neither
is reported as tracked custody.

Local-only CAS path:

```text
.devforgeai/research-cas/sha256/<first-two-hex>/<64-hex-digest>
```

If the resolved local-only path is outside the confirmed Research write fence,
cannot be exclusively created, or fails digest readback, `put-source` rejects
the operation before a canonical source record is admitted. It does not fall
back to an arbitrary path or metadata-only success.

When `retention_permitted` is `false`, `put-source` rejects both
`TRACKED_CAS` and `LOCAL_ONLY_CAS` before writing source bytes. A separately
permitted bounded extraction may be recorded as `EXTRACT_ONLY`; otherwise the
source is `NONE` and retains metadata only. `EXTRACT_ONLY` and `NONE` never
carry an object path. Without an affirmative redistribution basis, retained
bytes default to `LOCAL_ONLY_CAS`, not `TRACKED_CAS`.

For this deterministic retention policy, a word is one maximal sequence of
non-Unicode-whitespace characters. When `redistribution_basis` is `NONE`, all
`EXCERPT` evidence content for one Source in one run is cumulative and limited
to 25 such words; splitting a quotation across evidence records does not reset
the counter. Paraphrase is preferred. A larger retained excerpt requires a
non-`NONE` redistribution basis and its recorded reference. This is a
conservative retention gate, not a legal conclusion.
