# Open design decisions

These are the decisions most likely to change the framework's architecture.
They should be closed deliberately before implementation rather than left for a
skill author to guess.

Decision evidence pool: `CLM-001` through `CLM-055` in
[the claim ledger](claim-ledger.md). Each accepted decision record must select the
exact supporting and contrary Claim IDs rather than inherit this pool wholesale.

All rows below have decision status `OPEN`; none of the recommended defaults is
accepted project policy. Closing a row requires a separate decision record with
the named human authority, selected option and rationale, supporting Claim IDs,
timestamp, revision, supersession links, and `stale_if` conditions.

| ID | Decision | Recommended default | Why it matters |
|---|---|---|---|
| D-001 | Greenfield only, or greenfield plus brownfield/bug/migration? | Define a common lifecycle but implement greenfield first; reserve typed routes for feature, bug, spike, refactor, migration, compliance, and incident | A one-size greenfield PRD flow handles existing systems and defects poorly |
| D-002 | Is a Sprint mandatory? | No. Make Sprint Planning an optional planning adapter; Stories remain scheduler-neutral | Scrum does not mandate Epic/Story types, and Kanban or continuous flow should not corrupt specification semantics |
| D-003 | Who may accept or amend the constitution? | Named human authority; Product and Architecture may propose; deterministic service records acceptance/supersession | A model must not silently mint its own governing authority |
| D-004 | What belongs in the constitution? | Only principles, precedence, governance, quality/security invariants, and amendment rules | Tech versions, file layouts, and detailed designs change at a different cadence |
| D-005 | Where do Epics come from? | Dedicated Backlog Planning after accepted PRD and sufficient architecture | It separates product value ownership from architecture feasibility and delivery slicing |
| D-006 | Where does Sprint membership live? | Sprint ledger or external tracker referencing Story ID and revision | Replanning should not rewrite the Story's behavioral contract |
| D-007 | Story and technical specification: one artifact or two? | One Story package with separate logical sections/files when size warrants; one canonical package ID | Product behavior and technical constraints need different owners but one traceable delivery boundary |
| D-008 | Who owns the acceptance oracle? | Story/QA co-design it; an independent oracle custodian approves changes; Development cannot silently weaken it | Tests generated or edited by the implementation author can make a false pass easy |
| D-009 | How much context may a phase load? | Declare per-phase/context-pack budgets and split work that cannot fit without truncating governing constraints | Long context can bury relevant facts; provider compaction is lossy |
| D-010 | When are subagents required? | Never globally; a Delegation Planner uses decomposability, state coupling, evidence, cost, and authority gates | Multi-agent performance is task-dependent and can degrade sequential work |
| D-011 | What is “YOLO mode”? | Reversible autonomous defaults with a complete assumption/decision log; never a permission or governance bypass | The label otherwise invites silent material choices and weakens auditability |
| D-012 | Shared `SKILL.md` or generated provider wrappers? | Shared capability contract/resources plus generated Claude and Codex wrappers | Both use Agent Skills, but provider extensions, invocation, agents, hooks, and packaging differ |
| D-013 | Exact public skill names? | Freeze a small provider-neutral kebab-case registry, with `/name` for Claude and `$name` for Codex | Renames break handoffs, routing metadata, plugins, and documentation; namespaces can collide |
| D-014 | Are implicit skill invocations allowed? | Allow for read-only/advisory skills; require explicit human invocation for phase transitions, deployment, acceptance changes, and materially consequential external writes/actions | Discovery convenience must not become autonomous authority |
| D-015 | What owns workflow state? | A deterministic CLI/service and artifact registry, not a transcript, hook chain, or Markdown checkbox alone | Resume, concurrency, idempotency, legal transitions, and failures need a single authority |
| D-016 | Hook failure policy? | Critical hook adapters fail closed through a tested wrapper and have the same gate in CLI/CI; advisory hooks fail visibly | Native provider error behavior is not uniformly blocking |
| D-017 | Research cache fidelity? | Store opened-source metadata, atomic claim ledger, contrary evidence, retrieval time, and digests/snapshots where lawful and useful | Links and vendor behavior drift; search snippets and narrative citations are insufficient provenance |
| D-018 | Provenance strength? | SHA-256-bound local attestations in MVP; add signatures/transparency only with a defined verifier and key/identity model | A hash without independent custody proves consistency, not authorship or trust |
| D-019 | Provider/version support policy? | Pin tested minimum versions and capability-probe install/upgrade; publish per-provider conformance results | Claude and Codex hook, skill, subagent, and packaging behavior evolves |
| D-020 | Skill installation trust? | Source allowlist, version/digest pin, static and behavior audit, least permissions, review updates, rollback | Skills and their references/scripts are executable supply-chain artifacts |
| D-021 | Does Skill Validator include security? | Keep functional Skill Validator and Skill Supply-Chain Security Auditor as distinct gates with a combined release verdict | Correct behavior and safe installation are independent properties |
| D-022 | How are external systems integrated? | MCP/tool adapters own authenticated data/actions; skills own method; untrusted content is schema-constrained and provenance-tagged | Tool output can be stale, malicious, or prompt-injecting and should not become instructions |
| D-023 | What makes a phase complete, blocked, or unable to run? | Completion requires an accepted artifact, schema/trace pass, required evidence, closed or owned open decisions, and a validated handoff. Use phase `COULD_NOT_RUN` only when the phase itself cannot validly start/execute because required host capability, tooling, or environment is unavailable; use `BLOCKED` when the phase can execute but cannot complete without an external decision, authority, dependency, conflict, or required input | A fluent narrative or self-reported completion is not an acceptance gate, and dimension-qualified failure states prevent ambiguous routing |
| D-024 | Can QA edit production code or specifications? | No by default. QA produces evidence and routes defects to the owning workflow | Independent acceptance is weakened when the reviewer silently repairs its subject |
| D-025 | How are generated context briefs treated? | Derived, reproducible, disposable, and stale when a pinned source changes | A brief should reduce context without becoming a second source of truth |
| D-026 | What is the canonical artifact layout and naming contract? | Use type-first directories under a project slug with stable IDs; separate canonical artifacts from derived context, evidence, handoffs, and archives; authority comes from the registry, not path | Paths such as `docs/PM/<slug>` become API surface once skills, links, installers, and migrations depend on them |
| D-027 | Who owns package installation lifecycle design? | Architecture specifies packaging, install, upgrade, uninstall, rollback, and migration contracts; Release executes and proves them against versioned packages | “How it installs” is architecture; “this exact package was safely promoted” is release evidence |
| D-028 | When may a downloaded framework, skill, hook, or catalog influence DevForgeAI? | A named human design authority may promote an entry through the corpus evidence levels. Admit pinned primary implementation mechanisms and counterexamples as static evidence; a code path proves only that a mechanism exists, not that the configured provider executes it. Keep catalogs as bibliography; require quarantined runtime and provider-conformance evidence before claiming behavior, safety, or quality; revalidate when a pin, provider capability, dependency, or trust fact changes | A large untested corpus is valuable for design discovery but can otherwise turn popularity, prose, or dormant code into false assurance |
| D-029 | How will framework scalability claims be evaluated? | Predeclare frozen fixtures and oracle custody, comparator/control, metric priority, randomized trial order, minimum fresh-trial count, pass/degradation/variance and abort thresholds, environment pins, and treatment of `COULD_NOT_RUN`/`INFRA_FAILURE`; then test increasing repository, backlog, dependency, context, concurrency, and dirty-state complexity with independently accepted outcomes | Small-project success does not establish reliable operation after fan-in, compaction, or concurrent change grows |

## Recommended decisions to close first

Before specifying the first production skill, close at least:

1. D-001 scope and workflow routes;
2. D-003/D-004 governance and constitution authority;
3. D-012/D-013 provider adapters and public naming;
4. D-015 state authority and artifact registry;
5. D-008 acceptance-oracle custody;
6. D-016 hook failure policy;
7. D-019 supported provider versions;
8. D-023 the universal completion/handoff contract;
9. D-028 corpus-admission evidence levels; and
10. D-029 the scale and degradation benchmark.

## Questions likely to arise during design review

- Does `product-requirements` create only an MVP PRD, or also a durable Product
  Goal and ordered backlog?
- Must Architecture finish before any Epic exists, or may it produce a minimal
  baseline and iteratively deepen designs as Epics become ready?
- Which Story types are permitted: behavior, enabler, defect, spike,
  documentation, compliance, and operational work?
- What is the maximum Story size for one Development context and how is it
  measured?
- Which artifact changes invalidate downstream acceptance automatically?
- Which policies are universally deterministic versus project-configurable?
- May a generated skill call another generated skill, and what prevents cycles
  or privilege amplification?
- Where are held-out skill eval fixtures stored, and which role may view or
  change them?
- What evidence is required to say `PASS`, and which unavailable evidence must
  yield `COULD_NOT_RUN` or `BLOCKED`?
- How does the framework serialize two sessions attempting the same phase or
  artifact?
- Which external actions require preview/readback and explicit human approval?
- What is the rollback story for a provider adapter, hook set, or skill update?
- Which local-corpus patterns require a runtime counterexample or compatibility
  probe before they can enter the implementation backlog?
