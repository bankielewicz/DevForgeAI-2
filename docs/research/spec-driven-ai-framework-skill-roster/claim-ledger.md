# Atomic claim ledger

Accessed/compiled: 2026-09-01  
`FACT` means directly documented by the cited source in the recorded scope.
`OBSERVED` means established by the recorded static/audit procedure against a
pinned scope, without claiming executed behavior. `SYNTHESIS` means a design
conclusion drawn from multiple facts. `PROPOSAL` requires human acceptance before
it becomes framework policy. `USER_OBSERVED` preserves a user's experiential
report without promoting it to a general fact.

| Claim ID | Class | Atomic claim | Evidence | Limitation or design use |
|---|---|---|---|---|
| CLM-001 | FACT | Claude Code custom commands have been merged into skills; compatibility command files still work | CLA-02 | Current provider behavior; version-pin before implementation |
| CLM-002 | FACT | Codex custom prompt-based slash commands are deprecated in favor of skills | CDX-03 | Built-in slash commands remain; this concerns user-authored prompt commands |
| CLM-003 | FACT | Claude and Codex both support the open Agent Skills core but add different extensions and packaging behavior | CLA-01, CLA-02, CDX-02 | Does not establish byte-for-byte portability |
| CLM-004 | FACT | Claude and Codex progressively disclose skill metadata, instructions, and supporting resources | CLA-01, CLA-02, CDX-02 | Provider extensions and exact loading behavior differ |
| CLM-005 | FACT | Claude and Codex hooks expose different running handler types and event/tool coverage | CLA-06, CDX-05 | Provider-version capability probes are required |
| CLM-006 | SYNTHESIS | Hooks should call deterministic gates but should not be the sole universal enforcement boundary | CLA-03, CLA-06, CDX-05 | Framework architecture proposal based on documented gaps |
| CLM-007 | FACT | Claude subagents have separate context, while Codex subagents run in separate agent threads and return summaries to the main thread | CLA-04, CDX-04 | Neither mechanism inherently isolates shared filesystem state |
| CLM-008 | FACT | The cited v3 evaluates 260 configurations across six benchmarks/five architectures/three model families and reports relative changes from +80.8% to -70.0% | REL-01 | Controlled benchmarks; its selector is not a validated universal routing formula |
| CLM-009 | SYNTHESIS | A Delegation Planner and centralized Result Reconciler are safer than unconditional fan-out | REL-01, REL-02, REL-04 | Must be evaluated on representative framework tasks |
| CLM-010 | FACT | Relevant facts can be used less reliably when buried in long contexts | REL-03 | Model- and task-dependent effect |
| CLM-011 | PROPOSAL | Downstream work should receive a digest-bound context manifest and disposable bounded brief rather than copied source documents | REL-03, REL-08, CLA-07, CDX-01 | Requires a selector, staleness rules, and evals |
| CLM-012 | FACT | Requirements practice supports stable identifiers, verification methods, and bidirectional links through design, code, and tests | REL-08 | Tailor rigor to project risk; do not blindly import aerospace ceremony |
| CLM-013 | PROPOSAL | Backlog Planning should author Epics after Product and sufficient Architecture inputs exist | SDD-01, SDD-02, SDD-04, SDD-07 | Ownership design, not a universal standard |
| CLM-014 | PROPOSAL | Story Specification should own behavior/examples and Sprint Planning should own mutable Sprint association | SDD-04, SDD-06, SDD-07 | Sprint Planning is optional outside Scrum-style delivery |
| CLM-015 | PROPOSAL | Handoff should be a shared validated protocol emitted by every phase, not a terminal semantics-owning phase | CLA-07, CDX-01, REL-08 | Needs an accepted schema and status vocabulary |
| CLM-016 | SYNTHESIS | A QA failure must route to the owner of the defective source, not universally to Development | SDD-01, SDD-03, REL-06, REL-07, REL-08 | Defect classification needs reproducible evidence |
| CLM-017 | FACT | Accepted ADRs can be retained and superseded rather than silently rewritten | SDD-08 | Governance must define which decisions merit ADRs |
| CLM-018 | SYNTHESIS | A generic Development/QA workflow should apply project TDD policy; generating a new TDD skill is justified only for a distinct recurring oracle/workflow | REL-04, REL-06, REL-07 | Must be validated for repository-scale tasks |
| CLM-019 | SYNTHESIS | Same-context self-correction or model confidence should not be the sole acceptance oracle; use applicable external evidence | REL-05, REL-06, REL-07 | Cited self-verification studies were not repository-level coding evaluations |
| CLM-020 | FACT | Skill activation and output quality are distinct evaluation targets | CLA-02, CDX-02, REL-06 | Provider-specific evaluators still require calibration |
| CLM-021 | FACT | Malicious and vulnerable skills exist in the studied public ecosystem | REL-11 | Corpus prevalence is not a risk rate for a curated private package |
| CLM-022 | PROPOSAL | Functional Skill Validator and Skill Supply-Chain Security Auditor should remain distinct gates | REL-11, CLA-07, CDX-07 | Combine verdicts only through explicit release policy |
| CLM-023 | FACT | The in-toto Statement binds a typed predicate to artifact subjects/digests, while the SLSA Provenance predicate describes build inputs, process, and builder claims | REL-09 | Authentication additionally requires an envelope/signature, identity, and trust policy |
| CLM-024 | PROPOSAL | Release and Operations skills are necessary to connect reviewed source to deployed artifact and runtime feedback | REL-09, REL-10, REL-14 | Deployment support can be a later implementation tier |
| CLM-025 | PROPOSAL | Deterministic services should own lifecycle state, schemas, IDs/digests, traceability, policy, oracle access, reproducible eval/build facts, evidence, and handoff form/binding | SDD-01, SDD-03, CLA-03, CDX-05, REL-08, REL-09 | Skills may select or interpret results but cannot replace mechanical truth |
| CLM-026 | FACT | Agent-evaluation results can shift materially with infrastructure; the cited Anthropic test moved six percentage points between resource configurations | REL-06 | Pin environment and trials; do not treat small unmatched-environment differences as model/skill effects |
| CLM-027 | FACT | Eligible model-invocable skills advertise discovery metadata at startup subject to provider controls and catalog budgets | CLA-02, CDX-02 | Exact host budgets may change |
| CLM-028 | FACT | Claude and Codex hooks differ in trust, failure, and blocking semantics | CLA-06, CDX-05 | A hook error is not universally fail-closed |
| CLM-029 | FACT | Subagents consume additional tokens and coordination cost | CDX-04, REL-02 | Measure benefit on representative tasks |
| CLM-030 | FACT | Provider compaction can summarize away detail | REL-03, CLA-07 | Durable artifacts must carry resume-critical facts |
| CLM-031 | FACT | Anthropic's pinned skill-creator uses fresh-session evaluation runs and with/without-skill comparisons | CLA-02 | Such comparisons are intended to reduce authoring-context bias; environmental and evaluator isolation still need verification |
| CLM-032 | SYNTHESIS | Bounded subagents should receive explicit, self-contained task and context packets | CLA-04, CDX-04, REL-03 | Packet completeness and least authority require evaluation |
| CLM-033 | FACT | Claude manual-only skills can remain absent from startup context until explicit invocation | CLA-02 | Claude-specific control, not part of the portable Agent Skills floor |
| CLM-034 | FACT | Codex may shorten skill descriptions or omit entries when the initial catalog budget is exhausted | CDX-02 | Exact catalog budget may change |
| CLM-035 | FACT | By default Codex non-managed hooks use review/hash-bound trust, with a documented one-invocation trust-bypass flag | CDX-05 | Bypass is a deliberate high-risk automation option, not the default |
| CLM-036 | FACT | W3C PROV models entities, activities, agents, derivations, versions, and provenance about provenance | REL-09 | It is a general provenance model, not a software-build compliance level |
| CLM-037 | PROPOSAL | Canonical artifacts should use stable IDs and a registry-backed type/slug layout that separates source authority from derived context, evidence, handoffs, and archives | REL-08, REL-09 | Exact directory names remain a human design decision |
| CLM-038 | PROPOSAL | Architecture should specify install/upgrade/uninstall/rollback/migration contracts, while Release proves an exact package was promoted under them | SDD-08, REL-09, REL-14 | Requires project-specific packaging and deployment decisions |
| CLM-039 | OBSERVED | The pinned local BMAD snapshot contains semantic readiness and review gates | LRC-001 | Presence does not establish fail-closed runtime enforcement or outcome quality |
| CLM-040 | OBSERVED | The scoped local BMAD snapshot contains no committed Claude/Codex lifecycle-event hook implementation; its named activation hooks are prompt-step insertion | LRC-001 | Applies only to the pinned local commit and recorded static search |
| CLM-041 | OBSERVED | The pinned local BMAD project-context contract sets a bounded kernel ceiling | LRC-001 | Static design evidence does not prove effectiveness at scale |
| CLM-042 | USER_OBSERVED | The user reports an earlier BMAD experience became less effective and more uncontrolled as project complexity grew | LRC-001 / USR-001 | Tested version, model/provider, configuration, scale, and fixtures are not pinned |
| CLM-043 | SYNTHESIS | Gate presence is insufficient; each gate needs an explicit enforcement mode and tested behavior for missing, malformed, timed-out, or failing handlers | LRC-001, LRC-004, LRC-011, LRC-012, LRC-014, LRC-017, LRC-019, LRC-023, LRC-025, LRC-026 | Must be capability-probed on every supported provider/version |
| CLM-044 | PROPOSAL | Framework scalability should be evaluated across repository/backlog/dependency growth and session age using repeated, pinned, independently accepted trials | LRC-001, REL-01, REL-06, REL-13 | Requires representative fixtures, frozen outcome/oracle policy, comparator, trial policy, and closure thresholds |
| CLM-045 | OBSERVED | No downloaded local repository was installed, activated, built, or tested during this audit | LRC-001 through LRC-027 | All runtime, quality, safety, and scalability verdicts remain `NOT_EVALUATED` unless separately user-observed |
| CLM-046 | SYNTHESIS | Catalog inclusion, stars, prompt prose, and structural validation are discovery/shape evidence rather than proof of behavior, safety, or outcome quality | LRC-006 through LRC-010, LRC-015, LRC-024 | Individual primary implementations still warrant separate static and runtime evaluation |
| CLM-047 | OBSERVED | The pinned local BMAD sprint tooling defines monotonic state transitions and atomic state writes | LRC-001 | The tooling was not executed in this audit |
| CLM-048 | OBSERVED | The pinned local BMAD project-context skill uses indexed on-demand loading with validation and staleness checks | LRC-001 | The tooling was not executed or evaluated under repository growth |
| CLM-049 | OBSERVED | The pinned local BMAD workflow prescribes a fresh reviewer context | LRC-001 | A prescribed fresh role does not prove environmental independence or review accuracy |
| CLM-050 | OBSERVED | The pinned local BMAD build workflow compiles scoped Epic context packs with a declared token target | LRC-001 | The target was not measured against representative large projects |
| CLM-051 | FACT | Claude dynamic workflows have runtime/interaction constraints, while agent teams are experimental and higher-cost | CLA-05 | Do not make either provider-specific capability a base-lifecycle prerequisite |
| CLM-052 | FACT | Codex loads hierarchical `AGENTS.md` guidance with precedence and a combined size limit | CDX-06 | Exact limits and discovery behavior should be version-probed |
| CLM-053 | FACT | The cited dependency study observed invented package names across evaluated models and warns that later package existence does not establish provenance | REL-12 | The evaluated models/settings were selected in early 2024; prevalence is not current-risk estimation |
| CLM-054 | FACT | In the cited randomized study, experienced developers expected acceleration but took an estimated 19 percent longer with the evaluated early-2025 AI tools | REL-13 | Small study with task/tool/time-measurement limits; it supports measuring outcomes rather than a universal productivity claim |
| CLM-055 | FACT | Claude forked skills run in the background by default; background execution has a narrower tool surface and edits outside session checkpoints | CLA-02 | Context separation is not transactional filesystem isolation |

## Claim use rules

- A downstream artifact should cite the Claim ID. This ledger is the canonical
  transitive Claim-to-Source binding. Also include the Source ID when republishing
  source-specific facts, quoting/paraphrasing close to the source, or detaching the
  downstream artifact from this cache. Pin a source revision when available;
  otherwise retain retrieval date, status, relevant section, and a lawful
  snapshot/digest when useful.
- A changed provider fact marks dependent accepted design records
  `readiness=STALE` and unresolved defaults as requiring revalidation until the
  official documentation and capability probe are refreshed.
- A `PROPOSAL` cannot be promoted to project policy merely because it appears in
  this cache; it requires the framework's named human authority.
- Contrary evidence should be attached to the same Claim ID rather than hidden
  in a separate narrative.
