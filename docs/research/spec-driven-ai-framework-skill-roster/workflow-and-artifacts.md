# Workflow and artifact ownership

Evidence map: `CLM-013` through `CLM-018`, `CLM-024`, `CLM-025`, `CLM-037`
through `CLM-039`, `CLM-041`, `CLM-043`, `CLM-044`, and `CLM-046` through
`CLM-050` in
[the claim ledger](claim-ledger.md). The diagrams below are framework proposals,
not claims that every cited method uses this exact lifecycle.

## End-to-end lifecycle

```mermaid
flowchart LR
    I{"Intake route"}
    I -->|greenfield idea| B["Brainstorm"]
    I -->|existing-system change, refactor, or migration| BB["Brownfield baseline"]
    I -->|bug or incident| BD["Bug diagnosis"]
    I -->|compliance or operational change| C["Change assessment"]
    I -->|research only| RSK["Reusable Research"]
    I -->|technical spike| TS["Technical spike"]
    TS -->|intake-originated problem framing| B
    B -. scoped evidence question .-> TS
    A -. scoped evidence question .-> TS
    TS -. findings return to owner .-> B
    TS -. findings return to owner .-> A
    BB --> C
    BD --> C
    B --> P["Product requirements"]
    P --> A["Architecture and design"]
    A --> E["Backlog and Epics"]
    E --> S["Story specification"]
    S -->|iteration-based delivery| SP["Optional Sprint planning"]
    S -->|continuous flow| D["Development"]
    SP --> D
    D --> CR["Independent code review"]
    CR -->|approved| Q["QA and acceptance"]
    CR -->|implementation finding| D
    Q -->|accepted| R["Release"]
    Q -->|implementation defect| D
    Q -->|Story defect| S
    Q -->|architecture defect| A
    Q -->|product defect| P
    R --> O["Operate and observe"]
    O --> RT["Optional retrospective"]
    O --> C["Change assessment"]
    RT --> C
    C -->|new problem or opportunity| B
    C -->|product change| P
    C -->|design change| A
    C -->|bounded feature or fix| S

    ANY[["Any public phase"]]
    ANY -. evidence question .-> RSK
    RSK --> RC
    RC[("Research cache")] -. returned evidence .-> ANY

    CORE[("Cross-cutting deterministic core for every public phase: state, schemas, traceability, provenance, gates")]
    H[["Validated handoff for every public phase transition"]]
    CORE -. governs .-> ANY
    ANY -. emits .-> H
```

This is a graph, not a one-way waterfall. A downstream discovery returns to the
phase that owns the defective source. The workflow must preserve the rejected or
superseded record and then rebuild affected derived artifacts.
`Any public phase` is a global annotation: it includes every lifecycle node,
including Research, brownfield/bug routes, Sprint, Release, and Retrospective.
Research is read-only by default; a technical spike is a distinct, explicitly
fenced workflow used from Brainstorm or Architecture.

## Planning subphases

```mermaid
flowchart TB
    subgraph BS["Brainstorm"]
        B1["Intake and problem framing"] --> B2["Stakeholder and need interview"]
        B2 --> B3["Research questions and evidence gathering"]
        B3 --> B4["Options, risks, and contrary views"]
        B4 --> B5["Synthesis and open decisions"]
        B5 --> B6{"Named human decision"}
        B6 -->|clarify| B2
        B6 -->|defer or stop| BH["Deferred / stopped handoff"]
    end

    subgraph PRD["Product requirements"]
        P1["Validate brainstorm inputs"] --> P2["Define users, outcomes, and success measures"]
        P2 --> P3["Select MVP scope and nonfunctional needs"]
        P3 --> P4["Archive deferred ideas without losing provenance"]
        P4 --> P5["PRD quality and traceability gate"]
        P5 --> P6{"Named human PRD decision"}
        P6 -->|return| P2
        P6 -->|defer or stop| PH["Deferred / stopped handoff"]
    end

    subgraph ARCH["Architecture and design"]
        A1["Compile relevant product and research context"] --> A2["Constraints and quality attributes"]
        A2 --> A3["Alternatives and tradeoffs"]
        A3 --> A4{"Evidence gap needs a spike?"}
        A4 -->|yes| A5["Time-boxed prototype or technical spike"]
        A5 --> A5D{"Discovery changes problem or scope?"}
        A5D -->|no| A3
        A4 -->|no| A6["ADRs and domain designs"]
        A6 --> A7["Tech stack, source tree, install/deploy/upgrade, and test strategy"]
        A7 --> A8["Constitution or governance proposal"]
        A8 --> A9{"Cross-artifact and named human decision"}
        A9 -->|return| A2
        A9 -->|blocked or stop| AH["Blocked / stopped handoff"]
    end

    subgraph BACKLOG["Backlog and Epic planning"]
        E1["Map capabilities and outcomes"] --> E2["Slice Epics by value"]
        E2 --> E3["Add dependencies, risks, and exclusions"]
        E3 --> E4["Attach digest-bound context manifests"]
        E4 --> E5{"Architecture feasibility and Product ordering decision"}
        E5 -->|return| E1
        E5 -->|defer, stop, or blocked| EH["Deferred / blocked handoff"]
    end

    subgraph STORY["Story specification"]
        S1["Select one accepted Epic slice"] --> S2["Example mapping: rules, examples, questions"]
        S2 --> S3["Acceptance, negative, edge, security, and quality criteria"]
        S3 --> S4["Map each criterion to a verification method"]
        S4 --> S5["Compile minimal project context"]
        S5 --> S6["Independent readiness analysis"]
        S6 --> S7{"Named human readiness decision"}
        S7 -->|return| S2
        S7 -->|defer, stop, or blocked| SH["Deferred / blocked handoff"]
    end

    subgraph SPRINT["Optional Sprint planning adapter"]
        T1["Agree Sprint Goal"] --> T2["Check capacity and dependencies"]
        T2 --> T3["Select READY Story revisions"]
        T3 --> T4["Create execution lanes and integration plan"]
        T4 --> T5["Delivery forecast"]
    end

    B6 -->|accept| P1
    P6 -->|accept| A1
    A5D -->|problem changed| B2
    A5D -->|scope changed| P2
    A9 -->|accept| E1
    A9 -->|product change| P2
    E5 -->|accept| S1
    E5 -->|architecture issue| A2
    E5 -->|product issue| P2
    S7 -->|upstream issue| E5
    S7 -->|READY| SCH{"Use iteration scheduling?"}
    SCH -->|yes| T1
    SCH -->|no, continuous flow| DR["Ready for Development"]
    T5 --> DR
```

### Prototype loop

A prototype is evidence, not a stealth first implementation. Its record should
state the question, hypothesis, time box, permitted file fence, evaluation
method, result, and disposition (`discard`, `retain-as-fixture`, or separately
authorize production hardening). If it changes the understood problem, route
back to Brainstorm or Product rather than laundering the discovery into an ADR.

An optional “YOLO” user experience should be named and implemented as
`autonomous-defaults`, not as a gate bypass. The agent may choose documented,
reversible defaults; it must surface material, irreversible, security, cost, or
external-impact decisions to the human and record every assumption.

## Delivery subphases and repair routing

```mermaid
flowchart TB
    subgraph DEV["Development"]
        D1["Verify Story revision, authority, workspace, and context freshness"] --> D2["Run public acceptance examples and capture initial RED evidence when policy requires"]
        D2 --> D3["Plan bounded implementation tasks"]
        D3 --> D4["Implement with controlled delegation"]
        D4 --> D5["Run focused tests, static checks, and integration checks"]
        D5 --> D6["Self-review diff and capture evidence"]
        D6 --> D7["Development handoff"]
    end

    subgraph REVIEW["Independent code review"]
        R1["Fresh read-only context and exact change set"] --> R2["Trace changed behavior to Story criteria"]
        R2 --> R3["Correctness, security, maintainability, and test-gap review"]
        R3 --> R4{"Reportable finding?"}
        R4 -->|yes| R5["Typed review report"]
        R4 -->|no| R6["Review acceptance record"]
    end

    subgraph QA["QA and acceptance"]
        Q1["Verify test environment and oracle custody"] --> Q2["Execute requirement verification"]
        Q2 --> Q3["Validate user-observable outcome"]
        Q3 --> Q4["Check negative, edge, regression, and nonfunctional cases"]
        Q4 --> Q5{"All accepted?"}
        Q5 -->|yes| Q7["Acceptance evidence and release handoff"]
    end

    subgraph REL["Release and operate"]
        L1["Reproducible build and artifact digests"] --> L2["Supply-chain, license, security, and provenance checks"]
        L2 --> L3{"Named human release decision"}
        L3 -->|approve| L4["Deploy with rollback plan"]
        L3 -->|defer or stop| LH["Release held / stopped"]
        L3 -->|return finding| LR["Classify and route to source owner"]
        L4 --> L5["Deployment verification and telemetry"]
        L5 --> L6["Operational feedback, incidents, and change intake"]
    end

    D7 --> R1
    R5 -->|implementation| D1
    R5 -->|source artifact defect| ROUTE
    R6 --> Q1
    Q5 -->|no| ROUTE{"Shared deterministic repair router: source owner?"}
    ROUTE -->|code| D1
    ROUTE -->|Story| SREF["Run Story amendment through named READY decision"]
    ROUTE -->|architecture| AREF["Run Architecture amendment through named acceptance"]
    ROUTE -->|product| PREF["Run Product amendment through named acceptance"]
    SREF --> IMP["Impact analysis; invalidate evidence; rebuild affected artifacts and context"]
    AREF --> IMP
    PREF --> IMP
    IMP --> REACC{"All affected artifacts reaccepted and Story READY?"}
    REACC -->|yes| D1
    REACC -->|no| RWAIT["Return to owning workflow; Development remains blocked"]
    ROUTE -->|oracle| OREF["Authorize new oracle version; invalidate prior verdict"]
    OREF --> Q1
    ROUTE -->|environment| BLOCK["BLOCKED or COULD_NOT_RUN"]
    BLOCK -->|environment restored| Q1
    Q7 --> L1
    LR --> ROUTE
```

## Artifact ownership matrix

| Artifact | Created by | Accepted by | Consumed by | Mutation rule |
|---|---|---|---|---|
| Idea/brainstorm dossier | Brainstorm | Human sponsor | Product, Research | Version; preserve deferred/rejected options |
| Research claim ledger and source cache | Research | Phase owner accepts applicability | Any phase | Append evidence; supersede stale claims; retain source history |
| PRD and deferred-idea archive | Product Requirements | Human Product Owner | Architecture, Backlog | Amend through Product; downstream phases cannot change scope silently |
| Constitution/governance record | Governance Decision with Product/Architecture proposals | Named human authority | Every phase and deterministic policy | Accepted versions are immutable; amend/supersede explicitly |
| Tech stack and source-tree contracts | Architecture | Human/architecture authority | Backlog, Story, Development, Review | Version and impact-analyze every accepted change |
| Domain designs | Architecture specialist | Architecture authority and affected stakeholder | Backlog through QA | Split by concern; do not force irrelevant domains into every context |
| ADR | ADR Lifecycle | Named decision group/human | Story, Development, Review | Accepted ADR remains; a new ADR supersedes it |
| Epic | Backlog Planning | Product Owner with feasibility review | Story Specification, roadmapping | Re-slice/reorder without rewriting source PRD/architecture |
| Story/Specification | Story Specification | Human Product/Delivery authority | Sprint, Development, Review, QA | Stable behavioral contract; amend with impact analysis |
| Sprint ledger | Sprint Planning | Human delivery team | Development coordination | Freely replan within governance; references Story ID and revision |
| Public acceptance examples | Story Specification with QA input | Product/QA authority | Development, Review, QA | Version with the Story; Development cannot change frozen accepted examples |
| Protected held-out eval pack | Independent Oracle Custodian through access-controlled registry | QA/Product authority | QA or independent evaluator only | Never disclosed to Development; authorized change creates a new version and invalidates prior verdicts |
| Implementation/evidence record | Development | Review and QA assess it | Review, QA, Release | Append attempts/results; bind exact code and Story revision |
| Review report | Independent Review | Reviewer | Development, QA, human | Immutable report; remediation creates a linked round |
| QA report | QA Acceptance | QA/Product authority | Repair router, Release | Immutable evidence; correction creates superseding report |
| Release attestation | Deterministic build/provenance tooling; interpreted by Release | Human release authority | Consumers, Operations | Bind source, build, artifacts, builder, authenticated producer, trust policy, and approvals by digest |
| Operational feedback/incident | Operate | Service owner | Change Assessment | Preserve timeline and evidence; route without rewriting history |
| Handoff | Emitting phase supplies facts; deterministic renderer materializes them | Emitting phase owns semantic accuracy; validator checks form/binding; named human owns any decision | Next phase/session | Derived transition record; never replaces source artifacts |

## Artifact metadata and state

Every canonical artifact should have, directly or through its registry entry:

```text
artifact_id, artifact_type, schema_version
artifact_version, lifecycle_status, readiness_status
enforcement_mode
owner, decision_authority
canonical_path, subject_sha256
source_artifact_ids_and_versions[]
requirement_ids[], decision_ids[], evidence_ids[]
created_at, updated_at
supersedes[], stale_if[]
```

Keep separate state dimensions rather than overloading one `status` field:

| Dimension | Suggested closed values |
|---|---|
| Lifecycle | `DRAFT`, `PROPOSED`, `ACCEPTED`, `REJECTED`, `SUPERSEDED`, `ARCHIVED` |
| Readiness | `NOT_READY`, `READY`, `STALE` |
| Gate enforcement | `BLOCK`, `REQUIRE_HUMAN`, `WARN`, `OFF` |
| Capability | `NOT_PROBED`, `SUPPORTED`, `UNSUPPORTED_CAPABILITY` |
| Verification | `NOT_RUN`, `PASS`, `FAIL`, `COULD_NOT_RUN`, `INFRA_FAILURE`, `NOT_APPLICABLE` |
| Phase outcome | `COMPLETE`, `NEEDS_DECISION`, `BLOCKED`, `FAILED`, `COULD_NOT_RUN` |

Do not hash a document inside itself. Put the digest in the artifact registry,
handoff, or an adjacent manifest calculated over finalized bytes.

Use `COULD_NOT_RUN` when a required prerequisite or capability was unavailable
before an applicable check could execute. Use `INFRA_FAILURE` when execution was
attempted but a harness, runner, resource, timeout, or infrastructure fault made
the behavioral verdict invalid. `UNSUPPORTED_CAPABILITY` is a capability-probe
fact; an applicable check that depends on it receives `COULD_NOT_RUN`. Reserve
`NOT_RUN` for an applicable check intentionally not attempted under the declared
schedule or policy, not for an unavailable prerequisite.

Use phase outcome `COULD_NOT_RUN` only when the phase itself could not validly
start or execute because a required host capability, tool, or environment was
unavailable. Use phase outcome `BLOCKED` when the phase could execute but cannot
complete without an unresolved external decision, authority, dependency, conflict,
or required input. A check-level `COULD_NOT_RUN` does not force a phase-level
`COULD_NOT_RUN` when other meaningful phase work and a truthful blocked handoff are
possible.

## Precedence and source repair

Later artifacts may refine but must not silently override accepted upstream
authority:

```text
human governance and explicit rulings
    > accepted product requirements
    > accepted architecture decisions and interfaces
    > accepted Epic
    > accepted Story and acceptance pack
    > Sprint schedule and task plan
    > implementation narrative
```

When two accepted sources conflict, stop and request a ruling. Do not let the
nearest skill choose whichever instruction is convenient. After the source is
amended, run impact analysis, mark derived context packs stale, and regenerate
only the affected artifacts.
