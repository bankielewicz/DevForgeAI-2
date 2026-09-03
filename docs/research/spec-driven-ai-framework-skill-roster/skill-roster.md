# Recommended skill roster

This is a capability inventory, not a recommendation to expose every item as a
top-level command on day one. Public entrypoints should remain few and stable;
specialists can be invoked internally; hard controls belong in deterministic
services.

Evidence map: `CLM-006`, `CLM-009`, and `CLM-013` through `CLM-055` in
[the claim ledger](claim-ledger.md). Roster
membership and release tiers are proposals that require human acceptance.

## 1. User-facing phase skills

| ID | Provider-neutral skill | Primary owner/persona | Main output | Typical delegated perspectives | Release tier |
|---|---|---|---|---|---|
| WF-00 | `workflow-intake` | BA / delivery lead | Typed route: greenfield idea, feature, bug, refactor, spike, migration, compliance, or incident | Repository explorer, risk classifier | MVP |
| WF-00A | `brownfield-baseline` | Architect / maintainer | Observed current-system contract, build/test status, interfaces, constraints, uncertainty, and change map | Repository explorer, runtime/test investigator | Next |
| WF-00B | `bug-diagnosis` | Maintainer / QA | Reproduction, expected/actual behavior, causal evidence, regression requirement, and owning repair route; no implicit fix | Log/test investigator, repository explorer | Next |
| WF-01 | `brainstorm` | Business Analyst | Problem dossier, stakeholders, goals, assumptions, options, unresolved questions, decision recommendation | Researcher, domain SME, skeptic | MVP |
| WF-02 | `research` | Research lead | Claim ledger, source cache, contrary evidence, uncertainty, reusable provenance | Parallel source researchers, citation checker | MVP |
| WF-03 | `product-requirements` | Product Manager / Product Owner | MVP PRD, success measures, product risks, out-of-scope and deferred-ideas archive | BA, user advocate, market/domain researcher | MVP |
| WF-04 | `architecture` | Senior Architect | Architecture baseline, tech stack, source-tree contract, domain designs, install/distribution/upgrade/uninstall/migration design, proposed governance, and ADRs | Security, data, API, UX, deployment, spike agents | MVP |
| WF-05 | `backlog-planning` | Product/PM, with Architect review | Epics, capability map, dependency graph, ordering, Epic context manifests | Architect, estimator, risk reviewer | MVP |
| WF-06 | `story-specification` | BA/Product with delivery team perspectives | One implementable Story/Specification with stable IDs, examples, verification mapping, scoped context manifest | Developer, QA, Architect, security reviewer | MVP |
| WF-07 | `sprint-planning` | Human delivery team / Product Owner | Optional Sprint goal, selected READY Story revisions, capacity, dependencies, and delivery forecast | Dependency planner, estimator | MVP |
| WF-08 | `develop` | Developer | Code/config/docs plus test and execution evidence for one Story | Explorer, implementer, test specialist | MVP |
| WF-09 | `code-review` | Independent reviewer | Read-only correctness, maintainability, security, and conformance findings | Security reviewer, test-gap reviewer, docs/API reviewer | MVP |
| WF-10 | `qa-acceptance` | Independent QA lead | Requirements verification, user-need validation, evidence, and typed defect routing | Test executor, UX/accessibility reviewer, environment specialist | MVP |
| WF-11 | `release` | Release engineer | Reproducible build record, release checklist, artifact provenance, deployment approval packet | Supply-chain, security, documentation agents | Next |
| WF-12 | `operate` | SRE / operations | Deployment verification, telemetry/SLO evidence, operational runbook, incident feedback | Observability and incident agents | Later |
| WF-13 | `change-assessment` | BA/Product/Architect, selected by route | Impact report and route for feature change, bug, refactor, migration, or compliance update | Repository explorer, traceability auditor, RCA agent | Next |
| WF-14 | `retrospective` | Facilitator / delivery team | Evidence-based improvement proposals; no automatic policy mutation | Metrics analyst, failure-pattern reviewer | Later |

### Why Review and QA remain separate

`code-review` asks whether the implementation introduces defects, risks, or
maintenance problems. `qa-acceptance` asks whether the specified behavior was
verified and whether the result satisfies the intended user need. Passing one
does not imply passing the other.

### Why QA must not always route to Development

The proposed universal instruction, `/dev story-xxx --fix`, is correct only for
an implementation defect. A QA finding must first be classified:

| Finding class | Owning repair workflow |
|---|---|
| Implementation differs from a clear accepted Story | `develop --fix` |
| Acceptance criterion is ambiguous, contradictory, or missing | `story-specification --amend` |
| Architecture constraint is wrong or incomplete | `architecture --amend` |
| Product requirement or MVP scope is wrong | `product-requirements --amend` |
| Test oracle is invalid | QA/test-spec correction followed by independent rerun |
| Required environment or evidence is unavailable | Verification `COULD_NOT_RUN`; phase outcome `BLOCKED` when progress requires that evidence; never fabricate pass/fail |

## 2. Framework-extension skills

| ID | Skill | Responsibility | Important boundary |
|---|---|---|---|
| EXT-01 | `capability-specification` | Specify a project-specific skill, agent, hook, MCP/tool, template, or deterministic validator before generating it | A skill specification is not interchangeable with an agent or hook specification |
| EXT-02 | `devforgeai-skill-generator` | Generate provider-neutral resources and Claude/Codex skill adapters from an accepted skill spec | Must not invent missing requirements; should not generate unrelated subagents implicitly |
| EXT-03 | `devforgeai-skill-validator` | Validate structure plus functional, behavioral, safety, project-policy, and provider conformance in a sandbox | Static frontmatter validation alone is insufficient; this does not authorize supply-chain release |
| EXT-04 | `agent-generator` | Generate least-authority Claude and Codex role/worker configurations from an accepted agent spec | Agents are execution profiles, not phase skills |
| EXT-05 | `provider-conformance` | Orchestrate and interpret a reproducible harness for generated skills, agents, commands, and hooks with pinned provider/model, CLI/runtime, capabilities, and environment | The harness, not model prose, executes checks; report `UNSUPPORTED_CAPABILITY` separately from failure |
| EXT-06 | `skill-supply-chain-audit` | Review origin, malicious behavior, version/digest, scripts, hidden references, permissions, install/update risk, prompt injection, and release approval | Functional quality does not establish installation safety; both this audit and EXT-03 must pass |
| EXT-07 | `capability-artifact-generator` | Dispatch an accepted hook, MCP/tool, template, or deterministic-validator spec to a type-specific deterministic scaffolder; route agent specs to EXT-04 | Must preserve artifact kind; generating a hook/tool/validator is not “generating a skill” |

`devforgeai-skill-validator` should have at least these independent test lanes:

1. format/schema and path safety;
2. should-trigger and should-not-trigger classification;
3. representative output assertions in fresh sessions;
4. with-skill versus without-skill baseline and version A/B evaluation;
5. provider-specific permission, hook, and packaging checks;
6. versioned representative, edge, and adversarial datasets;
7. multiple fresh trials with pass-rate and variance reporting;
8. human calibration for model graders; and
9. end-state and trace grading for tool choice, authority violations, routing,
   handoffs, guardrails, and final state.

Every result should pin provider/model, skill and dependency digests, harness,
CLI/runtime, CPU/RAM, enforcement mode, timeout, concurrency, and network policy.
Classify `INFRA_FAILURE` separately from a behavioral failure. Small score
differences from unmatched environments cannot be attributed confidently to the
model or skill until environments are matched or the confound is controlled.

Untrusted generated or imported capabilities should first run in quarantine with
secrets and network denied by default. The supply-chain skill interprets recorded
behavior; it must not execute untrusted code with ordinary user authority.

## 3. Internal reusable specialist skills

These should usually be invoked by a phase skill rather than occupying the
human's primary command menu.

| Skill | Used by | Output |
|---|---|---|
| `requirements-clarifier` | Brainstorm, Product, Architecture, Story | Questions, ambiguity IDs, assumptions, contradiction report |
| `delegation-planner` | Any phase considering subagents | Decomposability, coupling, authority, evidence, cost, and execution decision |
| `result-reconciler` | Any delegated phase | Evidence-bound synthesis proposal, rejected claims, unresolved contradictions, and coverage interpretation after schema checks |
| `context-compiler` | Every downstream phase | Applicability/exclusion rationale and bounded brief request; the resolver mints the digest-bound manifest |
| `traceability-impact-auditor` | Product through Operations | Interpretation of graph-computed orphan/gap/staleness and affected-artifact reports |
| `cross-artifact-analyzer` | Architecture, Backlog, Story, pre-Development | Read-only conflicts, omissions, stale references, and coverage gaps |
| `governance-decision` | Product and Architecture | Constitution proposal/amendment, decision authority, supersession record |
| `adr-lifecycle` | Architecture and Change Assessment | Proposed/accepted/rejected/superseded ADR with rationale and consequences |
| `technical-spike` | Brainstorm and Architecture | Time-boxed hypothesis, disposable prototype evidence, findings, disposition |
| `example-mapping` | Story Specification and QA | Business rules, concrete examples, questions, deferred discoveries |
| `eval-designer` | Story, Skill Validator, QA/independent evaluator | Proposed public/held-out cases, grader/rubric contract, and mutation strategy; no custody authority |
| `security-privacy-analysis` | Product through Release | Threats, security/privacy requirements, mitigations, verification links |
| `dependency-risk-review` | Architecture, Development, Release | Risk interpretation of tooling-verified publisher/source, version/digest/lock, license, vulnerability, and approval evidence |
| `environment-reproducibility` | Skill Validator, QA, Release | Interpretation of a recorder-produced execution contract, infrastructure drift, and `INFRA_FAILURE` evidence |
| `spec-code-convergence` | Review and QA | Report-only comparison of Story, plan/tasks, code, and evidence |
| `documentation-planning` | Product through Release | User, operator, API, migration, and support documentation obligations |
| `release-provenance-review` | Release | Review of tooling-produced source/build inputs, producer identity, artifact digests, and trust-policy verification |
| `incident-root-cause` | Operate and Change Assessment | Reproduction, causal evidence, regression requirement, routed change |

Domain design should be a family of focused Architect-invoked specialists
(`ux-design`, `data-design`, `api-design`, `deployment-design`, and similar),
not one permanently loaded mega-skill. Only generate the specialists actually
needed by the project.

These specialists own bounded judgment, not mechanical truth. Deterministic
services mint IDs and hashes, validate schemas, traverse the trace graph, enforce
oracle access, resolve dependencies, record environments, render handoffs, and
produce build attestations. A specialist may select, explain, or interpret those
results but must not recreate them as unverified prose.

Development may read and run public acceptance examples, but it must not receive
protected held-out cases. The Oracle Custodian owns hidden-case content and write
authority; QA or a separate evaluator runs those cases. A post-implementation
oracle change creates a new version, invalidates the earlier verdict, and
requires independent rerun.

Independent security/privacy verification is mandatory when a change crosses a
trust boundary, handles secrets or regulated/sensitive data, changes identity or
authorization, executes untrusted input, adds network/external-write authority,
changes dependencies/build/release controls, or requests a security exception.
A general code review cannot accept a security exception.

## 4. Personas are agents, not the workflow taxonomy

| Agent profile | Best use | Default authority |
|---|---|---|
| Business Analyst | Interviews, problem framing, requirements clarification | Read/write planning artifacts only |
| Researcher | Source discovery and evidence extraction | Read-only workspace; web/doc tools as needed |
| Product Manager / Product Owner | MVP scope, ordering, outcome measures | Planning artifacts; no code mutation |
| Architect | Tradeoffs, interfaces, constraints, ADRs | Architecture artifacts; prototype fence only when authorized |
| Developer | One accepted Story or bounded work package | Scoped workspace write |
| Reviewer | Independent diff/spec review | Read-only |
| QA | Execute acceptance oracles and capture evidence | Read-only product code; test/evidence writes as authorized |
| Oracle Custodian | Approve, version, and disclose protected evaluation assets | Held-out registry only; independent of Development |
| Security reviewer | Threat and vulnerability analysis | Read-only by default |
| Release engineer | Build/package/deploy workflow | Explicitly approval-gated external writes |

The phase skill supplies the procedure. The agent profile supplies an isolated
role, tools, model/cost choice, and authority. Avoid duplicating the same long
instructions in both.

## 5. Deterministic framework services — not skills

These are required if the framework intends to enforce a lifecycle rather than
merely suggest one:

| Service | Required property |
|---|---|
| Workflow state machine | Legal transitions, prerequisites, idempotency, resume and abort behavior |
| Artifact registry | Stable IDs, type, status, owner, canonical path, revision/digest, supersession |
| Schema validator | Machine-checkable required fields and closed status vocabulary |
| Policy/gate engine | Authority, approvals, file fences, quality gates, exception records |
| Traceability graph | Bidirectional relations and orphan, gap, and stale-edge detection |
| Context resolver | Exact source anchors/digests and stale-context invalidation |
| Oracle registry/access control | Public versus protected cases, version/write authority, disclosure audit, and verdict invalidation |
| Dependency resolver and inventory | Registry/publisher verification, lock/digest capture, license/vulnerability inputs, and SBOM-ready records |
| Provenance/evidence ledger | Commands, tools, inputs, outputs, timestamps, environments, and digests |
| Evaluation environment registry | Provider/model, skills, harness, tools, CPU/RAM, timeouts, concurrency, network, trials, and infrastructure-failure classification |
| Reproducible evaluation runner | Frozen dataset revisions, fresh trials, trace capture, grader calibration inputs, and typed outcomes |
| Untrusted-capability quarantine/runner | Deny secrets/network by default; record filesystem/process/network behavior; prevent install/activation until functional and supply-chain gates pass; require explicit release from quarantine |
| Build/provenance tooling | Reproducible build facts, artifact digests, authenticated producer envelope, and trust-policy verification |
| Provider adapter layer | Claude/Codex invocation, skills, agents, hooks, and version capability probes |
| Hook-health and conformance tests | Detect missing, mistyped, unsupported, timed-out, or fail-open controls |
| Handoff renderer/validator | Renders phase-supplied facts and verifies form/binding, exact next action, state, artifacts, evidence, decisions, and authority |

## 6. Direct ownership rulings

### Epic documents

Create them in `backlog-planning`, not wholly inside Product Management or
Architecture. The skill consumes:

- the accepted PRD and requirement IDs;
- relevant architecture/ADR constraints;
- UX, data, API, security, and operational obligations;
- unresolved research and risk;
- a context manifest generated from canonical sources.

Product/PM owns value, slicing, and ordering. Architecture performs a
feasibility and dependency review. The human approves the resulting backlog.

### Story/Specification documents

Create them in `story-specification`. A Story should describe one coherent
behavioral slice that a bounded Development run can complete and QA can verify.
It should contain stable IDs, business rules, concrete examples, negative and
edge cases, nonfunctional constraints, out-of-scope items, verification methods,
dependencies, and a pinned context manifest.

### Sprint association

When iteration scheduling is used, create association in `sprint-planning`. A
Sprint file or tracker record should reference Story IDs and revisions. Do not
make the Story file's identity depend on a Sprint because reprioritization should
not rewrite its behavior contract. Continuous-flow delivery may proceed from a
READY Story without a Sprint artifact.

### Constitution and architecture package

Keep the constitution small: non-negotiable principles, precedence, governance,
and amendment rules. Product may propose mission/value constraints; Architecture
may propose engineering, quality, security, and operability principles; a human
ratifies them through `governance-decision`.

Keep changing technical facts in separate `tech-stack`, `source-tree`,
architecture-view, domain-design, installation/distribution/upgrade/uninstall/
migration, and ADR artifacts. Accepted ADRs should be superseded by new records
rather than silently rewritten.

### TDD and other project policies

Do not generate a new TDD skill merely because Architecture selected TDD. Put
the test policy in the accepted project quality contract; make the generic
`develop`, `code-review`, and `qa-acceptance` skills honor it; and enforce the
observable parts with deterministic gates. Generate a project-specific skill
only when the project has a genuinely distinct, recurring test workflow or
domain oracle. Development cannot alter frozen acceptance tests. An authorized
oracle amendment creates a new oracle version and invalidates prior RED/GREEN
and acceptance evidence.

## 7. Suggested implementation order

1. Build the deterministic artifact/state/provenance core and provider
   capability probes.
2. Implement `brainstorm` plus `research`, the handoff contract, and validators.
3. Add Product, Architecture, Backlog, Story, and Sprint workflows with the
   context compiler and trace graph.
4. Add Development, independent Review, and QA with typed repair routing.
5. Add capability/skill generation and evaluation only after the base skill
   contract has representative evals.
6. Add Release, Operations, change/brownfield routes, and retrospectives.
