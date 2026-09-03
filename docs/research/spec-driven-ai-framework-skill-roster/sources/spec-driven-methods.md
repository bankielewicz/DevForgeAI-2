# Source notes: spec-driven methods and lifecycle frameworks

Accessed: 2026-09-01  
Corpus rule: DevForgeAI excluded. Official or project-primary sources preferred.

## SDD-01 — GitHub Spec Kit

- Source: [GitHub Spec Kit repository at `0053c3a3`](https://github.com/github/spec-kit/tree/0053c3a328aefbfebae096657c095eb0740a444d)
- Source: [Agentic SDD reference at `0053c3a3`](https://github.com/github/spec-kit/blob/0053c3a328aefbfebae096657c095eb0740a444d/docs/reference/agentic-sdd.md)
- Source class: official project documentation

Documented evidence:

- The core separates project constitution, behavioral specification, technical
  plan, tasks, implementation, and convergence.
- Current optional steps include clarification, requirement checklists, and a
  read-only cross-artifact analyzer before implementation.
- The analyzer routes a defect back to the phase that owns the source rather
  than repairing it downstream.
- The integration documentation explicitly distinguishes provider invocation;
  Codex skills use `$speckit-*` where slash-oriented hosts use `/speckit.*`.
- Current idea-assessment and bug extensions use different workflows rather
  than forcing every request through the feature path.

Design inference:

- DevForgeAI needs explicit clarification, cross-artifact analysis, convergence,
  and typed route skills in addition to authoring phases.
- Provider parity should preserve semantics, not invocation punctuation.

Limit:

- Spec Kit is an evolving implementation and is evidence of a useful pattern,
  not proof that its exact artifact model or command roster fits this framework.

## SDD-02 — Kiro Specs

- Source: [Kiro Specs](https://kiro.dev/docs/specs/)
- Source: [Kiro Feature Specs](https://kiro.dev/docs/specs/feature-specs/)
- Source: [Analyze Requirements](https://kiro.dev/docs/specs/analyze-requirements/)
- Source class: official vendor documentation

Documented evidence:

- Feature Specs separate requirements, design, and tasks; bugfix work has a
  separate analysis path.
- Requirements can be analyzed before design for ambiguity, contradiction,
  assumptions, missing edge cases, and conflicting constraints.
- Tasks form a dependency graph and independent work can execute in waves.
- Requirements-first, design-first, and quick/no-approval variants exist.

Design inference:

- Add workflow routing, a requirements analyzer, explicit dependency planning,
  and a carefully bounded autonomous-defaults mode.
- Parallel work should follow an explicit dependency graph, not optimistic
  agent fan-out.

## SDD-03 — OpenSpec

- Source: [OpenSpec quickstart](https://openspec.dev/docs/quickstart)
- Source: [Spec-driven schema](https://openspec.dev/docs/schemas/spec-driven)
- Source: [OpenSpec skills](https://openspec.dev/docs/skills)
- Source class: project-primary documentation

Documented evidence:

- Its change lifecycle distinguishes exploration, proposal, review, apply,
  verification, synchronization, and archive.
- Main specifications describe the built system while delta/change artifacts
  and archives preserve the evolution of behavior.
- Structural validation can reject behavior changes with no specification
  delta, and verification can report without silently editing the subject.

Design inference:

- DevForgeAI needs explicit change/supersession/archive semantics and a
  report-only spec-to-code verifier.
- Current truth and historical change records should not be conflated.

## SDD-04 — BMAD Method

- Source: [Workflow map at `4fc185c5`](https://github.com/bmad-code-org/BMAD-METHOD/blob/4fc185c598dd594f37391e73839aba4a30033c07/docs/reference/workflow-map.md)
- Source: [Create Epics and Stories skill at `4fc185c5`](https://github.com/bmad-code-org/BMAD-METHOD/blob/4fc185c598dd594f37391e73839aba4a30033c07/src/bmm-skills/plan/bmad-create-epics-and-stories/SKILL.md)
- Source class: project-primary documentation

Documented evidence:

- The project separates analysis, planning, solutioning, and implementation.
- Its Epic/Story workflow consumes both PRD and architecture information, while
  Sprint planning and just-in-time Story preparation remain distinct.

Design inference:

- Epic synthesis is best owned by a dedicated Product/Backlog skill after both
  product and architecture inputs exist.
- Sprint scheduling should remain separate from Story semantics.

Limit:

- This is one framework's ownership choice, not an industry standard. The
  recommendation is supported independently by the artifact-boundary analysis.

## SDD-05 — Spec Kitty

- Source: [Complete workflow tutorial](https://docs.spec-kitty.ai/guides/tutorials/your-first-mission.html)
- Source class: project-primary documentation

Documented evidence:

- The workflow separates specification, planning, tasks, analysis,
  implementation/review, acceptance, merge, post-mission review, and
  retrospective.
- Work packages can declare dependencies and execution lanes.

Design inference:

- “Tests pass,” “review accepted,” “requirements accepted,” and “safe to
  merge/release” require different gates.

## SDD-06 — Cucumber BDD and Example Mapping

- Source: [Cucumber BDD](https://cucumber.io/docs/bdd/)
- Source: [Example Mapping](https://cucumber.io/docs/bdd/example-mapping/)
- Source: [Gherkin reference](https://cucumber.io/docs/gherkin/reference/)
- Source class: official project documentation

Documented evidence:

- BDD separates discovery, formulation, and automation.
- Example Mapping explores a Story through rules, concrete examples, questions,
  and newly discovered/deferred Stories.
- Gherkin examples structure initial context, event, and observable outcome and
  can become executable specifications.

Design inference:

- Story authoring should include Product/BA, Development, and QA perspectives
  before coding.
- Provide Example Mapping and executable examples where useful, without forcing
  Gherkin on every project or criterion.

## SDD-07 — The Scrum Guide

- Source: [The 2020 Scrum Guide](https://scrumguides.org/scrum-guide.html)
- Source class: official framework definition

Documented evidence:

- The Product Owner orders the Product Backlog; the Developers create and adapt
  the Sprint Backlog.
- Product Backlog refinement makes items more precise and ready for selection.
- The Sprint Backlog combines a Sprint Goal, selected backlog items, and the
  plan for delivering the Increment.
- Work is not part of the Increment until it meets the Definition of Done.
- Scrum is intentionally incomplete and does not prescribe Epic or User Story
  artifact types.

Design inference:

- Product ordering, Story refinement, and Sprint selection are separate jobs.
- Make Sprint support an adapter, not a mandatory property of the core Story
  schema.

## SDD-08 — Architecture records and views

- Source: [AWS architectural decision record process](https://docs.aws.amazon.com/prescriptive-guidance/latest/architectural-decision-records/adr-process.html)
- Source: [C4 diagrams](https://c4model.com/diagrams)
- Source class: official vendor guidance and creator-maintained method

Documented evidence:

- AWS describes ADRs with context, decision, consequences, owner, lifecycle,
  review, and an immutable accepted record that a later ADR may supersede.
- C4 provides levels of architectural zoom and advises using only diagrams that
  add value; context and container diagrams are enough for many teams.

Design inference:

- Keep modular ADRs and focused architecture views instead of a monolithic
  `architecture.md` that every phase must load.
- A context compiler can select the relevant view and decision records for a
  specific Epic or Story.
