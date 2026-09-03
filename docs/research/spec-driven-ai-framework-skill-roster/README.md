# Spec-driven AI framework skill roster research

Research ID: `RSR-2026-09-01-spec-driven-ai-framework-skill-roster`  
Researched: 2026-09-01  
Status: independent design research, not an implementation specification

## Scope and independence

This cache studies public spec-driven frameworks, AI-assisted software delivery,
Claude Code extensibility, Codex extensibility, agent skills, context management,
traceability, verification, and release provenance.

DevForgeAI itself was deliberately excluded from the research corpus. The
concurrently authored files under `docs/design/` were also not read or used.
This preserves the cache as an independent design input rather than a review of
the legacy framework or of another author's proposal.

## Executive answer

The sound architecture is not "one giant skill per persona." It is four layers:

1. **Thin provider entrypoints** select a workflow and pass arguments.
2. **Focused phase skills** own one user-recognizable outcome and orchestrate
   bounded specialist agents.
3. **Deterministic framework services** own state transitions, schemas,
   authority, provenance, traceability, and hard gates.
4. **Durable artifacts and handoffs** let a human approve transitions and let a
   fresh session resume without trusting conversational memory.

The main ownership decisions are:

- A dedicated **Backlog Planning** skill should create Epics after the PRD and
  architecture baseline are ready. Product/PM owns value and ordering; the
  Architect supplies constraints and reviews feasibility.
- A separate **Story Specification** skill should refine one Epic slice into an
  implementable, testable Story. It should use BA/Product, Developer, QA, and
  Architect perspectives and mint stable requirement and acceptance IDs.
- A separate **Sprint Planning** skill should associate READY Stories with
  `Sprint-001`, `Sprint-002`, and so on. Sprint membership is mutable scheduling
  state and should not be embedded in the Story's behavior contract.
- **Handoff is a cross-cutting protocol**, emitted by every phase and checked by
  a deterministic validator. It is not merely the last prose section of a
  skill.
- **Research is a reusable cross-cutting skill** whose claim ledger and source
  cache become inputs to later phases.
- **Subagents isolate context; they do not prove truth.** Delegation needs a
  decomposability gate, self-contained task packets, least authority, and
  independent evidence or executable oracles.
- **Hooks are enforcement adapters, not workflow engines.** They should call
  deterministic validators and remain defense in depth because provider event
  coverage and failure semantics differ.

A supplemental read-only audit covers 27 user-downloaded repository directories:
25 pinned Git histories and two empty/unborn leads. No package was installed or
tested. It is implementation-pattern evidence, not a quality leaderboard. The
user's prior BMAD experience is retained as `USER_OBSERVED`; the current local
snapshot contains semantic readiness/review gates, deterministic sprint-state
tooling, and context-scaling mitigations, but no committed Claude/Codex
lifecycle-event enforcement layer was found and runtime scalability remains
`NOT_EVALUATED`.

Several essential workflows were missing from the proposed lifecycle: intake
routing, clarification, context compilation, traceability/impact analysis,
cross-artifact readiness analysis, independent code review, release and build
provenance, deployment verification, operations/observability, change control,
brownfield/bug routing, retrospective learning, and skill supply-chain review.

## Cache contents

- [Skill roster](skill-roster.md) — recommended public workflows, internal
  specialists, deterministic services, and rollout tiers.
- [Workflow and artifact ownership](workflow-and-artifacts.md) — Mermaid maps,
  subphases, artifact boundaries, and typed failure loops.
- [Provider adapters](provider-adapters.md) — Claude/Codex command, skill,
  subagent, hook, and packaging guidance.
- [Context, traceability, and handoffs](context-traceability-handoffs.md) — the
  context compiler, evidence graph, research cache, and handoff contract.
- [Open decisions](open-decisions.md) — choices that should be resolved before
  implementation.
- [Atomic claim ledger](claim-ledger.md) — documented fact, scoped observation,
  synthesis, user observation, and proposal IDs with evidence and limitations.
- [Research query log](query-log.md) — search lanes, selection rules, and
  retrieval limitations.
- [Sources: spec-driven methods](sources/spec-driven-methods.md)
- [Sources: Claude and Agent Skills](sources/claude-and-agent-skills.md)
- [Sources: Codex](sources/codex.md)
- [Sources: assurance and AI-agent reliability](sources/assurance-and-agent-reliability.md)
- [Sources: downloaded local repository corpus](sources/local-repository-corpus.md)
- `MANIFEST.sha256` — digest inventory generated after the cache is complete.

## Working definitions

| Primitive | Owns | Must not be trusted to own |
|---|---|---|
| Phase skill | Reasoned workflow, interview, synthesis, artifact drafting | Hard authorization or proof that its own output is correct |
| Specialist agent | Bounded investigation or perspective in an isolated context | Canonical state, implicit parent context, or final acceptance |
| Thin command/entrypoint | Argument capture and selection of a phase skill | Duplicated phase logic |
| Hook | Guaranteed event trigger where the host supports it | The entire ordered workflow or universal enforcement coverage |
| Deterministic service | State, schemas, IDs, hashes, policy, trace graph, gates | Product judgment or ambiguous stakeholder decisions |
| MCP/tool adapter | Live data and controlled external actions | Workflow semantics or unverified truth |
| Handoff | Human-readable transition record bound to exact artifacts | Replacement for the canonical artifacts or their validators |

## Research method

Sources were opened or fetched from official vendor documentation, primary
project documentation, original standards bodies, or original research. Search
snippets were not treated as evidence. The source notes distinguish documented
facts from design inference and record an access date. The user's phase sketch
defined the design question; no legacy/public DevForgeAI implementation or
design artifact was used as evidentiary research material.

The later downloaded-repository supplement used exact local Git heads and
read-only static inspection. Dirty working-tree custody is explicit; referenced
bytes were checked against `HEAD`. Repository tests, installers, hooks, and skills
were not executed, and README outcome claims were not promoted to empirical facts.
