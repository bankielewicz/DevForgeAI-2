# Artifact Registry

Status: normative, 2026-09-02. One place that answers, for every skill: which templates it owns, which artifacts it writes, which artifacts it reads, and which skills sit upstream and downstream of it. `10-sequencer-and-contracts.md` states how an artifact is written; this document states what is written, by whom, from what, and for whom.

Three rules govern every row:

1. **A template has exactly one owning skill.** The owner's writer fills it, the owner's critic reviews against it, and the consumer's gate validates against it. Skills do not borrow each other's templates.
2. **Every template has at least one producer and at least one consumer.** The two exceptions are `handoff`, which the sequencer renders for a human, and `validate-report`, which is terminal by design.
3. **Every producer-written artifact is written inside a candidate root, and reaches the canonical tree only by promotion.** The evidence files, `handoff.json` and `state.yaml` are the sequencer's own and are written canonically; `init` writes the skeleton before any run exists. For everything in the tables below, a producer worker writes the file under `candidate.root` and names its path in the receipt; the sequencer derives what changed from the checkpoint diff, refuses anything outside the run's fence or unclaimed, and promotes the run's bytes into the canonical checkout under its lock. "Producer" below always means the skill whose phase wrote the content.

## 1. Template registry

Every anatomy-governed non-Research skill owns its templates under `.devforgeai/skills/<name>/templates/`. Research uses the typed schemas and contracts under `framework/skills/research/` instead and owns no template in this registry.

Header keys are the machine-readable block the gate reads without a model. Every header carries `template`, `template_version`, `accepts_versions`, `required_frontmatter`, `required_sections`, `id_pattern` and `forbidden_text`; the table records the values that differ per template. `forbidden_text` is `["TODO", "TBD", "{{", "}}", "<fill in>"]` everywhere.

| Template | Path | Version | `id_pattern` | `required_frontmatter` | `required_sections` |
|---|---|---|---|---|---|
| `observed-constraints` | `.devforgeai/skills/onboard/templates/observed-constraints.md` | 1 | `^OBS-[0-9]{3}$` | id, template, template_version, status, scope, evidence | Constraint, Evidence, Why It Is Not Derivable |
| `brainstorm` | `.devforgeai/skills/brainstorm/templates/brainstorm.md` | 1 | `^IDEA-[0-9]{3}$` | slug, template, template_version, status, provenance | Problem, Ideas, Clusters, Open Questions |
| `prd` | `.devforgeai/skills/pm/templates/prd.md` | 1 | `^REQ-[0-9]{3}$` | slug, template, template_version, status, scope, provenance, depends_on | Goal, Users, Requirements, Non-Goals, Success Measures |
| `backlog-ideas` | `.devforgeai/skills/pm/templates/backlog-ideas.md` | 1 | `^IDEA-[0-9]{3}$` | slug, template, template_version, status | Archived Ideas, Promotion Log |
| `constitution` | `.devforgeai/skills/architect/templates/constitution.md` | 1 | `^SEC-[0-9]{3}$` | slug, template, template_version, status, provenance, depends_on | Principles, Mandates, Constraints, Style |
| `sourcetree` | `.devforgeai/skills/architect/templates/sourcetree.md` | 1 | `^PATH-[0-9]{3}$` | slug, template, template_version, status, mode, depends_on | Layout, Ownership, Naming |
| `techstack` | `.devforgeai/skills/architect/templates/techstack.md` | 1 | `^TS-[0-9]{3}$` | slug, template, template_version, status, mode, depends_on, stack_section | Languages, Data Access, Testing, Build And Lint |
| `architecture` | `.devforgeai/skills/architect/templates/architecture.md` | 1 | `^COMP-[0-9]{3}$` | slug, template, template_version, status, depends_on | Components, Interfaces, Data Flow, Failure Modes |
| `design` | `.devforgeai/skills/architect/templates/design.md` | 1 | `^DES-[0-9]{3}$` | slug, topic, template, template_version, status, depends_on | Decision, Options, Consequences, Interfaces |
| `stack` | `.devforgeai/skills/architect/templates/stack.yaml` | 1 | `^[a-z][a-z0-9-]*$` | version, compiled, package_manager, manifests, ignore_dirs, commands, test_glob, test_layout, runner_probe, packages, extractors, forbidden_imports | not a Markdown artifact; the section contract is `10-sequencer-and-contracts.md` section 7 |
| `adr` | `.devforgeai/skills/architect/templates/adr.md` | 1 | `^ADR-[0-9]{4}$` | id, template, template_version, status, date, supersedes, depends_on | Context, Decision, Consequences, Alternatives |
| `epic` | `.devforgeai/skills/plan/templates/epic.md` | 1 | `^EPIC-[0-9]{3}$` | id, slug, template, template_version, status, risk_tier, provenance, depends_on | Goal, Scope, Stories, Constitution Sections |
| `story` | `.devforgeai/skills/plan/templates/story.md` | 3 | `^STORY-(HOTFIX-)?[0-9]{3}$` | id, epic, sprint, scope, status, template, template_version, requires_skill, risk_tier, size, gate_policy, blocked_by, provenance, context, write_fence, commands, test_plan | Goal, Context, Interface, Acceptance Criteria, Unchanged Behaviour, Out of Scope, Verification, Clarifications |
| `sprint` | `.devforgeai/skills/plan/templates/sprint.md` | 1 | `^sprint-[0-9]{3}$` | id, slug, template, template_version, status, stories | Goal, Stories, Order, Exit Criteria |
| `skill-spec` | `.devforgeai/skills/plan/templates/skill-spec.md` | 1 | `^SKILL-SPEC-[0-9]{3}$` | id, skill_name, target, status, template_version, depends_on, author, date | the 16 numbered sections listed in `templates/skill-spec.md` |
| `clarification` | `.devforgeai/skills/clarify/templates/clarification.md` | 1 | `^CLR-[0-9]{3}$` | id, story, template, template_version, date, status | Question, Answer, Authority |
| `analyze-report` | `.devforgeai/skills/analyze/templates/analyze-report.md` | 1 | `^FIND-[0-9]{3}$` | slug, template, template_version, status, depends_on | Orphans, Gaps, Stale Hashes, Actions |
| `skill-yaml` | `.devforgeai/skills/skill-generator/templates/skill.yaml` | 1 | `^[a-z][a-z0-9-]*$` | name, version, target, handoff, workers | not a Markdown artifact; the neutral skill definition |
| `skill-md` | `.devforgeai/skills/skill-generator/templates/SKILL.md` | 1 | `^[a-z][a-z0-9-]*$` | name, description | Identity, Phases, Dispatch Loop, Handoff |
| `agent-md` | `.devforgeai/skills/skill-generator/templates/agent.md` | 1 | `^[a-z][a-z0-9_]*$` | name, description, tools, writes | Job, Inputs, Rules, Receipt |
| `command-md` | `.devforgeai/skills/skill-generator/templates/command.md` | 1 | `^[a-z][a-z-]*$` | name, description, argument-hint | Usage, Arguments, Handoff |
| `validate-report` | `.devforgeai/skills/skill-validator/templates/validate-report.md` | 1 | `^VAL-[0-9]{3}$` | skill, template, template_version, status, verdict, depends_on | Anatomy, Provider, Spec Conformance, Fixes |
| `dev-notes` | `.devforgeai/skills/dev/templates/dev-notes.md` | 1 | `^NOTE-[0-9]{3}$` | story, phase, template, template_version, status, run | Note, Issues, Files, Oracle |
| `review-report` | `.devforgeai/skills/review/templates/review-report.md` | 1 | `^FIND-[0-9]{3}$` | story, template, template_version, status, verdict, depends_on | Compliance, Security, Style, Findings |
| `qa-report` | `.devforgeai/skills/qa/templates/qa-report.md` | 1 | `^CRIT-[0-9]{3}$` | story, template, template_version, status, verdict, depends_on | Criteria, Evidence, Regressions, Fix Guidance |
| `impact-report` | `.devforgeai/skills/amend/templates/impact-report.md` | 1 | `^IMP-[0-9]{3}$` | doc, template, template_version, status, depends_on | Change, Affected Stories, Re-slice Actions |
| `retro-report` | `.devforgeai/skills/retro/templates/retro-report.md` | 1 | `^LESS-[0-9]{3}$` | sprint, template, template_version, status, depends_on | Outcomes, Lessons, Proposed Amendments, Archive |
| `drift-report` | `.devforgeai/skills/drift/templates/drift-report.md` | 1 | `^DRIFT-[0-9]{3}$` | slug, template, template_version, status, depends_on | Sourcetree Drift, Techstack Drift, Architecture Drift, Actions |
| `handoff` | `.devforgeai/skills/status/templates/handoff.md` | 1 | `^[a-z][a-z0-9-]*$` | none; the rendering of `handoff.json` | You Are Here, Artifacts, Open Issues, Next Steps, Also Possible |

Ownership decisions applied here:

- **`plan` is the sole owner of `skill-spec`.** `architect` writes mandates into `constitution.md#mandates` through its `constitution` phase and nothing else about skills. `architect` has no `mandate_specs` phase and no fence entry under `docs/plan/`, so no other skill can write the template (`10-sequencer-and-contracts.md` section 4).
- **`init` and `status` own no template.** Both have zero LLM workers. `init` writes `.devforgeai/state.yaml` and the documentation skeleton; `status` writes nothing and renders `handoff.json`. The `handoff` template is filed under `status` because that is the skill that prints it on demand; the sequencer is its only writer.
- **`dev-tdd` owns no template.** It is a variant of `dev` and shares `story` as its gated input and `dev-notes` as its output.
- **`adr` has two producers, and both have the same validated write path.** `architect` mints decisions; `amend` appends them. Both write the same template into the same directory, and `.devforgeai/provenance/adr/**` is in both document fences as a producer exception from the sequencer-owned deny list, restricted to exactly `architect`'s `adr` phase and `amend`'s `adr` phase. Every ADR the run writes is checked against the `adr` template header — required frontmatter keys, `id_pattern`, required sections, forbidden text — and against the `NNNN-<slug>.md` filename shape before the run is promoted, and an ADR that already exists is never overwritten: a reversal is a new record whose `supersedes` names the old one. There is no rewind for this path: a promoted ADR is a record, and abandoning the run removes only what never left the candidate root. The id shape is the template's `^ADR-[0-9]{4}$` with the filename `NNNN-<slug>.md`; the template owns that pattern and every other document repeats it.
- **`stack` has two producers, and a validated write path.** `architect`'s `techstack` phase emits the INTENDED sections; `onboard`'s `code_map` phase emits the OBSERVED sections. `.devforgeai/stack.yaml` is in both skills' document fences and is the one carve-out from the sequencer-owned deny list, restricted to exactly those two phases. The file the run writes is validated against `schemas/devforgeai/v1/stack.schema.json` and the section contract in `10-sequencer-and-contracts.md` section 7 — `build` is required when `compiled: true` — before the run is promoted.

## 2. Artifact path patterns

| Pattern | Template | Producing skill | Writer |
|---|---|---|---|
| `.devforgeai/state.yaml` | none | init | sequencer |
| `.devforgeai/stack.yaml` | `stack` | architect (`techstack`), onboard (`code_map`) | sequencer |
| `docs/architecture/sourcetree.md#observed`, `techstack.md#observed`, `architecture.md#observed` | `observed-constraints` | onboard | sequencer |
| `docs/brainstorm/<slug>.md` | `brainstorm` | brainstorm | sequencer |
| `docs/PM/<slug>/prd.md` | `prd` | pm | sequencer |
| `docs/PM/<slug>/backlog-ideas.md` | `backlog-ideas` | pm | sequencer |
| `docs/architecture/constitution.md` | `constitution` | architect | sequencer |
| `docs/architecture/sourcetree.md` | `sourcetree` | architect, onboard | sequencer |
| `docs/architecture/techstack.md` | `techstack` | architect, onboard | sequencer |
| `docs/architecture/architecture.md` | `architecture` | architect, onboard | sequencer |
| `docs/architecture/design-<topic>.md` | `design` | architect | sequencer |
| `.devforgeai/provenance/adr/NNNN-<slug>.md` | `adr` | architect (`adr`), amend (`adr`) | sequencer |
| `docs/plan/<slug>/epics/EPIC-NNN.md` | `epic` | plan | sequencer |
| `docs/plan/<slug>/stories/STORY-NNN.md` | `story` | plan | sequencer |
| `docs/plan/<slug>/stories/STORY-NNN.md#clarifications` | `clarification` | clarify | sequencer |
| `docs/plan/<slug>/sprints/sprint-NNN.md` | `sprint` | plan | sequencer |
| `docs/plan/<slug>/skill-specs/SKILL-SPEC-NNN.md` | `skill-spec` | plan | sequencer |
| `docs/reports/analyze-<slug>.md` | `analyze-report` | analyze | sequencer |
| `docs/reports/review-<story>.md` | `review-report` | review | sequencer |
| `docs/reports/qa-<story>.md` | `qa-report` | qa | sequencer |
| `docs/reports/drift-<slug>.md` | `drift-report` | drift | sequencer |
| `docs/reports/retro-<sprint>.md` | `retro-report` | retro | sequencer |
| `docs/reports/impact-<doc>.md` | `impact-report` | amend | sequencer |
| `docs/reports/validate-<skill>.md` | `validate-report` | skill-validator | sequencer |
| `docs/reports/dev-<story>-<phase>.md` | `dev-notes` | dev | sequencer |
| `docs/reports/<skill>-<run>-<phase>.md` | none | every skill with a run | sequencer |
| `.devforgeai/skills/<name>/skill.yaml` | `skill-yaml` | skill-generator | sequencer |
| `.devforgeai/skills/<name>/SKILL.md` | `skill-md` | skill-generator | sequencer |
| `.devforgeai/skills/<name>/subagents/<role>.md` | `agent-md` | skill-generator | sequencer |
| `.devforgeai/skills/<name>/commands/<command>.md` | `command-md` | skill-generator | sequencer |
| `.devforgeai/work/<run>/handoff.json` | `handoff` | sequencer | sequencer |
| `.devforgeai/work/<run>/<phase>-result.json` | none | sequencer | sequencer |
| `.devforgeai/work/<run>/<phase>-report.md` | none | sequencer | sequencer |
| `.devforgeai/work/<run>/run.yaml` | none | sequencer | sequencer, hooks |
| `.devforgeai/work/<run>/wt/**` (candidate root), `<phase>.manifest.json`, `cp/<phase>/**` (copy-mode checkpoints) | none | sequencer creates; producers write inside the fence | sequencer |
| `.devforgeai/work/<run>/evidence/<agent>/**` | none | judge worker | sequencer, downstream producers |
| `.devforgeai/sessions/<session_id>.json` | none | sequencer | sequencer |
| `.devforgeai/provenance/log.jsonl` | none | sequencer | sequencer |
| `docs/research/<slug>/runs/RUN-NNNNNN/**` | Research typed schemas | research | Research Core |

Two naming facts that specifications must not restate incorrectly:

- The sequencer's rendered view is `docs/reports/<skill>-<run>-<phase>.md`. For a story run the run id is the story id, so `dev`'s notes land at `docs/reports/dev-STORY-001-green.md`. For a document run the run id is `<skill>-<arg>`, so the rendered view of `review`'s `report` phase is `docs/reports/review-review-STORY-001-report.md`. The report artifact a reader cites is the fenced one, `docs/reports/review-STORY-001.md`, which the `report` phase writes.
- `dev` has no document fence: its fence is the story's `write_fence`. `dev-notes` therefore exists only as evidence under `.devforgeai/work/<run>/` and as the rendered view above.

## 3. `depends_on` edges

An artifact's frontmatter `depends_on` lists the upstream sections it was sliced from, each with an anchor and a hash resolved by the rule in `01-skill-anatomy.md`. The gate re-resolves every entry when the consuming skill starts; a mismatch is a stale-hash defect.

| Consuming artifact | `depends_on` sources |
|---|---|
| `prd` | `docs/brainstorm/<slug>.md` sections; admitted `observed-constraints` |
| `constitution` | `docs/PM/<slug>/prd.md` sections; admitted `observed-constraints`; current source citations |
| `sourcetree`, `techstack`, `architecture`, `design` | `docs/architecture/constitution.md` sections |
| `stack` | `docs/architecture/techstack.md` sections (INTENDED); the observed tree (OBSERVED) |
| `adr` | the constitution section the decision changes |
| `epic` | `prd` requirement anchors; constitution sections |
| `story` | `provenance`: its epic anchor and its PRD requirement anchor. `context`: constitution, sourcetree, techstack, architecture and design slices, plus source ranges. `commands`: the `stack.yaml` anchor and file hash |
| `clarification` | the story section that carried the assumption |
| `skill-spec` | `docs/architecture/constitution.md#mandates`; the `requires_skill` story |
| `analyze-report` | every prd, epic, story and constitution anchor it walked |
| `skill-yaml`, `skill-md`, `agent-md`, `command-md` | the `skill-spec` sections they were generated from |
| `validate-report` | the compiled skill files; `constitution.md`; the originating `skill-spec` |
| `review-report` | the story; the constitution slice the story carried |
| `qa-report` | the story's acceptance criteria and `test_plan`; the `review-report` |
| `impact-report` | the amended constitution section; every story whose `context` hashed it |
| `retro-report` | the sprint; the qa and review reports for its stories |
| `drift-report` | `sourcetree`, `techstack`, `architecture` sections; the observed tree |

`dev-notes`, `handoff`, and every file under `.devforgeai/work/` carry no `depends_on`: they are evidence of one run, and that run's `.devforgeai/work/<run>/run.yaml` already pins what it was allowed to touch.

`.devforgeai/work/<run>/context.json` is the same kind of file: the Slice output the sequencer writes at `phase start` from the incoming artifact's already-hashed `context[]` bundle. It carries the entries and their re-resolution verdicts, not a new `depends_on` edge, and no worker writes it.

## 4. Upstream and downstream, per skill

"Upstream" is what the skill's gate consumes; "downstream" is the skill that gates on what it produced.

| Skill | Upstream skills | Consumes | Produces | Downstream skills |
|---|---|---|---|---|
| init | — | the target repository | `state.yaml`, documentation skeleton, hook files | onboard, brainstorm |
| onboard | init | existing source; README and ADRs through an explicit Research request | `observed-constraints`, OBSERVED `sourcetree`/`techstack`/`architecture`, OBSERVED `stack` | architect, brainstorm |
| brainstorm | init, onboard, pm | `observed-constraints`, `backlog-ideas`, sealed Research dossiers | `brainstorm` | pm |
| research | any skill, by explicit human request | a confirmed `research-request/v1` | sealed dossier under `docs/research/<slug>/` | every skill, by reference |
| pm | brainstorm | `brainstorm` | `prd`, `backlog-ideas` | architect, plan, analyze, brainstorm |
| architect | pm, onboard, drift | `prd`, `observed-constraints`, `drift-report` | `constitution`, `sourcetree`, `techstack`, `architecture`, `design`, `adr`, `stack` | plan, dev, review, qa, amend, drift, analyze, skill-validator |
| plan | pm, architect, analyze, amend, retro | `prd`, `constitution`, `sourcetree`, `techstack`, `architecture`, `design`, `analyze-report`, `impact-report`, `retro-report` | `epic`, `story`, `sprint`, `skill-spec` | dev, clarify, review, qa, analyze, skill-generator, skill-validator, retro |
| clarify | plan | `story` | `clarification` appended to the story | dev |
| analyze | pm, plan, architect | `prd`, `epic`, `story`, `constitution` | `analyze-report` | plan, amend |
| skill-generator | plan | `skill-spec` | `skill-yaml`, `skill-md`, `agent-md`, `command-md` | skill-validator |
| skill-validator | skill-generator, plan, architect | the compiled skill files, `skill-spec`, `constitution` | `validate-report` | — |
| dev (variant dev-tdd) | plan, clarify, architect, onboard, qa, review | `story`, `epic`, `constitution`, `sourcetree`, `techstack`, `architecture`, `design`, `stack`, `clarification`, `qa-report`, `review-report` | code and tests inside the story fence, `dev-notes` | review, qa, retro |
| review | plan, dev, architect | `story`, `dev-notes`, `constitution`, `techstack`, `adr` | `review-report` | qa, dev, retro |
| qa | plan, dev, review, architect | `story`, `dev-notes`, `review-report`, `techstack`, `stack` | `qa-report` | dev, retro |
| amend | architect, retro, drift, analyze | `constitution`, `sourcetree`, `techstack`, `architecture`, `adr`, `story`, `retro-report`, `drift-report`, `analyze-report` | amended architecture documents, `adr`, `impact-report` | plan, analyze, review, retro |
| retro | plan, dev, review, qa, amend | `sprint`, `dev-notes`, `review-report`, `qa-report`, `adr` | `retro-report` | amend, plan |
| drift | architect | `sourcetree`, `techstack`, `architecture`, the observed tree | `drift-report` | amend, architect |
| status | — | `state.yaml`, `handoff.json` | nothing | — |

`init` and `status` carry no template edge. `init` hands off through `state.yaml`, and `status` renders `handoff.json`; neither gates on a document, so neither appears in the edge list below.

## 5. Machine-readable registry

An edge's `via` is a template name, except for `via: handoff`. Those five edges are control flow, not provenance: they are the "calls" the roster used to describe, and each is a handoff row whose first `next` step names the other skill's command. Nothing gates on them and no artifact carries a `depends_on` for them; the second run starts after the first one closed (divergence 7).

```yaml
registry:
  skills:
  - name: init
    command: /init
    kind: none
    upstream: []
    downstream:
    - onboard
    - brainstorm
  - name: onboard
    command: /onboard
    kind: document
    upstream:
    - init
    downstream:
    - architect
    - brainstorm
  - name: brainstorm
    command: /brainstorm <slug>
    kind: document
    upstream:
    - init
    - onboard
    - pm
    downstream:
    - pm
  - name: research
    command: /research <slug> --request <request-file> --confirm-request <sha256>
    kind: external
    upstream: []
    downstream: []
  - name: pm
    command: /pm <slug>
    kind: document
    upstream:
    - brainstorm
    downstream:
    - architect
    - plan
    - analyze
    - brainstorm
  - name: architect
    command: /architect <slug>
    kind: document
    upstream:
    - pm
    - onboard
    - drift
    downstream:
    - plan
    - dev
    - review
    - qa
    - amend
    - drift
    - analyze
    - skill-validator
  - name: plan
    command: /plan <slug>
    kind: document
    upstream:
    - pm
    - architect
    - analyze
    - amend
    - retro
    downstream:
    - dev
    - clarify
    - review
    - qa
    - analyze
    - skill-generator
    - skill-validator
    - retro
  - name: clarify
    command: /clarify <story>
    kind: document
    upstream:
    - plan
    downstream:
    - dev
  - name: analyze
    command: /analyze <slug>
    kind: document
    upstream:
    - pm
    - plan
    - architect
    downstream:
    - plan
    - amend
  - name: skill-generator
    command: /skill-gen <skill> [--spec <path>]
    kind: document
    upstream:
    - plan
    downstream:
    - skill-validator
  - name: skill-validator
    command: /skill-validate <skill>
    kind: document
    upstream:
    - skill-generator
    - plan
    - architect
    downstream: []
  - name: dev
    command: /dev <story>
    kind: story
    variant: dev-tdd
    upstream:
    - plan
    - clarify
    - architect
    - onboard
    - qa
    - review
    downstream:
    - review
    - qa
    - retro
  - name: review
    command: /review <story>
    kind: document
    upstream:
    - plan
    - dev
    - architect
    downstream:
    - qa
    - dev
    - retro
  - name: qa
    command: /qa <story>
    kind: document
    upstream:
    - plan
    - dev
    - review
    - architect
    downstream:
    - dev
    - retro
  - name: amend
    command: /amend <doc> <change>
    kind: document
    upstream:
    - architect
    - retro
    - drift
    - analyze
    downstream:
    - plan
    - analyze
    - review
    - retro
  - name: retro
    command: /retro <sprint>
    kind: document
    upstream:
    - plan
    - dev
    - review
    - qa
    - amend
    downstream:
    - amend
    - plan
  - name: drift
    command: /drift
    kind: document
    upstream:
    - architect
    downstream:
    - amend
    - architect
  - name: status
    command: /status
    kind: none
    upstream: []
    downstream: []
  templates:
  - name: observed-constraints
    path: .devforgeai/skills/onboard/templates/observed-constraints.md
    produced_by:
    - onboard
    consumed_by:
    - architect
    - brainstorm
  - name: brainstorm
    path: .devforgeai/skills/brainstorm/templates/brainstorm.md
    produced_by:
    - brainstorm
    consumed_by:
    - pm
  - name: prd
    path: .devforgeai/skills/pm/templates/prd.md
    produced_by:
    - pm
    consumed_by:
    - architect
    - plan
    - analyze
  - name: backlog-ideas
    path: .devforgeai/skills/pm/templates/backlog-ideas.md
    produced_by:
    - pm
    consumed_by:
    - pm
    - brainstorm
  - name: constitution
    path: .devforgeai/skills/architect/templates/constitution.md
    produced_by:
    - architect
    - amend
    consumed_by:
    - plan
    - dev
    - review
    - qa
    - amend
    - analyze
    - skill-validator
  - name: sourcetree
    path: .devforgeai/skills/architect/templates/sourcetree.md
    produced_by:
    - architect
    - onboard
    - amend
    consumed_by:
    - plan
    - dev
    - drift
    - amend
  - name: techstack
    path: .devforgeai/skills/architect/templates/techstack.md
    produced_by:
    - architect
    - onboard
    - amend
    consumed_by:
    - plan
    - dev
    - review
    - qa
    - drift
    - amend
  - name: architecture
    path: .devforgeai/skills/architect/templates/architecture.md
    produced_by:
    - architect
    - onboard
    - amend
    consumed_by:
    - plan
    - dev
    - drift
    - amend
  - name: design
    path: .devforgeai/skills/architect/templates/design.md
    produced_by:
    - architect
    - amend
    consumed_by:
    - plan
    - dev
  - name: stack
    path: .devforgeai/skills/architect/templates/stack.yaml
    produced_by:
    - architect
    - onboard
    consumed_by:
    - dev
    - qa
  - name: adr
    path: .devforgeai/skills/architect/templates/adr.md
    produced_by:
    - architect
    - amend
    consumed_by:
    - amend
    - analyze
    - review
    - retro
  - name: epic
    path: .devforgeai/skills/plan/templates/epic.md
    produced_by:
    - plan
    consumed_by:
    - dev
    - analyze
  - name: story
    path: .devforgeai/skills/plan/templates/story.md
    produced_by:
    - plan
    consumed_by:
    - clarify
    - dev
    - review
    - qa
    - analyze
    - amend
  - name: sprint
    path: .devforgeai/skills/plan/templates/sprint.md
    produced_by:
    - plan
    consumed_by:
    - retro
    - analyze
  - name: skill-spec
    path: .devforgeai/skills/plan/templates/skill-spec.md
    produced_by:
    - plan
    consumed_by:
    - skill-generator
    - skill-validator
  - name: clarification
    path: .devforgeai/skills/clarify/templates/clarification.md
    produced_by:
    - clarify
    consumed_by:
    - dev
  - name: analyze-report
    path: .devforgeai/skills/analyze/templates/analyze-report.md
    produced_by:
    - analyze
    consumed_by:
    - plan
    - amend
  - name: skill-yaml
    path: .devforgeai/skills/skill-generator/templates/skill.yaml
    produced_by:
    - skill-generator
    consumed_by:
    - skill-validator
  - name: skill-md
    path: .devforgeai/skills/skill-generator/templates/SKILL.md
    produced_by:
    - skill-generator
    consumed_by:
    - skill-validator
  - name: agent-md
    path: .devforgeai/skills/skill-generator/templates/agent.md
    produced_by:
    - skill-generator
    consumed_by:
    - skill-validator
  - name: command-md
    path: .devforgeai/skills/skill-generator/templates/command.md
    produced_by:
    - skill-generator
    consumed_by:
    - skill-validator
  - name: validate-report
    path: .devforgeai/skills/skill-validator/templates/validate-report.md
    produced_by:
    - skill-validator
    consumed_by:
    - skill-generator
  - name: dev-notes
    path: .devforgeai/skills/dev/templates/dev-notes.md
    produced_by:
    - dev
    consumed_by:
    - review
    - qa
    - retro
  - name: review-report
    path: .devforgeai/skills/review/templates/review-report.md
    produced_by:
    - review
    consumed_by:
    - qa
    - dev
    - retro
  - name: qa-report
    path: .devforgeai/skills/qa/templates/qa-report.md
    produced_by:
    - qa
    consumed_by:
    - dev
    - retro
  - name: impact-report
    path: .devforgeai/skills/amend/templates/impact-report.md
    produced_by:
    - amend
    consumed_by:
    - plan
  - name: retro-report
    path: .devforgeai/skills/retro/templates/retro-report.md
    produced_by:
    - retro
    consumed_by:
    - amend
    - plan
  - name: drift-report
    path: .devforgeai/skills/drift/templates/drift-report.md
    produced_by:
    - drift
    consumed_by:
    - amend
    - architect
  - name: handoff
    path: .devforgeai/skills/status/templates/handoff.md
    produced_by:
    - sequencer
    consumed_by: []
  artifacts:
  - pattern: .devforgeai/state.yaml
    template: null
    writer: sequencer
  - pattern: .devforgeai/stack.yaml
    template: stack
    writer: sequencer
  - pattern: docs/architecture/sourcetree.md#observed
    template: observed-constraints
    writer: sequencer
  - pattern: docs/architecture/techstack.md#observed
    template: observed-constraints
    writer: sequencer
  - pattern: docs/architecture/architecture.md#observed
    template: observed-constraints
    writer: sequencer
  - pattern: docs/brainstorm/<slug>.md
    template: brainstorm
    writer: sequencer
  - pattern: docs/PM/<slug>/prd.md
    template: prd
    writer: sequencer
  - pattern: docs/PM/<slug>/backlog-ideas.md
    template: backlog-ideas
    writer: sequencer
  - pattern: docs/architecture/constitution.md
    template: constitution
    writer: sequencer
  - pattern: docs/architecture/sourcetree.md
    template: sourcetree
    writer: sequencer
  - pattern: docs/architecture/techstack.md
    template: techstack
    writer: sequencer
  - pattern: docs/architecture/architecture.md
    template: architecture
    writer: sequencer
  - pattern: docs/architecture/design-<topic>.md
    template: design
    writer: sequencer
  - pattern: .devforgeai/provenance/adr/NNNN-<slug>.md
    template: adr
    writer: sequencer
  - pattern: docs/plan/<slug>/epics/EPIC-NNN.md
    template: epic
    writer: sequencer
  - pattern: docs/plan/<slug>/stories/STORY-NNN.md
    template: story
    writer: sequencer
  - pattern: docs/plan/<slug>/stories/STORY-NNN.md#clarifications
    template: clarification
    writer: sequencer
  - pattern: docs/plan/<slug>/sprints/sprint-NNN.md
    template: sprint
    writer: sequencer
  - pattern: docs/plan/<slug>/skill-specs/SKILL-SPEC-NNN.md
    template: skill-spec
    writer: sequencer
  - pattern: docs/reports/analyze-<slug>.md
    template: analyze-report
    writer: sequencer
  - pattern: docs/reports/review-<story>.md
    template: review-report
    writer: sequencer
  - pattern: docs/reports/qa-<story>.md
    template: qa-report
    writer: sequencer
  - pattern: docs/reports/drift-<slug>.md
    template: drift-report
    writer: sequencer
  - pattern: docs/reports/retro-<sprint>.md
    template: retro-report
    writer: sequencer
  - pattern: docs/reports/impact-<doc>.md
    template: impact-report
    writer: sequencer
  - pattern: docs/reports/validate-<skill>.md
    template: validate-report
    writer: sequencer
  - pattern: docs/reports/dev-<story>-<phase>.md
    template: dev-notes
    writer: sequencer
  - pattern: docs/reports/<skill>-<run>-<phase>.md
    template: null
    writer: sequencer
  - pattern: .devforgeai/skills/<name>/skill.yaml
    template: skill-yaml
    writer: sequencer
  - pattern: .devforgeai/skills/<name>/SKILL.md
    template: skill-md
    writer: sequencer
  - pattern: .devforgeai/skills/<name>/subagents/<role>.md
    template: agent-md
    writer: sequencer
  - pattern: .devforgeai/skills/<name>/commands/<command>.md
    template: command-md
    writer: sequencer
  - pattern: .devforgeai/work/<run>/handoff.json
    template: handoff
    writer: sequencer
  - pattern: .devforgeai/work/<run>/<phase>-result.json
    template: null
    writer: sequencer
  - pattern: .devforgeai/work/<run>/<phase>-report.md
    template: null
    writer: sequencer
  - pattern: .devforgeai/work/<run>/context.json
    template: null
    writer: sequencer
  - pattern: .devforgeai/work/<run>/run.yaml
    template: null
    writer: sequencer
  - pattern: .devforgeai/work/<run>/wt/**
    template: null
    writer: producer
  - pattern: .devforgeai/work/<run>/<phase>.manifest.json
    template: null
    writer: sequencer
  - pattern: .devforgeai/work/<run>/evidence/<agent>/**
    template: null
    writer: judge
  - pattern: .devforgeai/sessions/<session_id>.json
    template: null
    writer: sequencer
  - pattern: .devforgeai/provenance/log.jsonl
    template: null
    writer: sequencer
  - pattern: docs/research/<slug>/runs/RUN-NNNNNN/
    template: null
    writer: research-core
  - pattern: .devforgeai/skills/<name>/{templates,references,scripts,assets,compiled}/**
    template: null
    writer: sequencer (skill-generator fence)
  edges:
  - from: onboard
    to: architect
    via: observed-constraints
  - from: onboard
    to: brainstorm
    via: observed-constraints
  - from: onboard
    to: dev
    via: stack
  - from: onboard
    to: qa
    via: stack
  - from: onboard
    to: plan
    via: sourcetree
  - from: onboard
    to: plan
    via: techstack
  - from: onboard
    to: plan
    via: architecture
  - from: brainstorm
    to: pm
    via: brainstorm
  - from: pm
    to: architect
    via: prd
  - from: pm
    to: plan
    via: prd
  - from: pm
    to: analyze
    via: prd
  - from: pm
    to: brainstorm
    via: backlog-ideas
  - from: pm
    to: pm
    via: backlog-ideas
  - from: architect
    to: plan
    via: constitution
  - from: architect
    to: dev
    via: constitution
  - from: architect
    to: review
    via: constitution
  - from: architect
    to: qa
    via: constitution
  - from: architect
    to: amend
    via: constitution
  - from: architect
    to: analyze
    via: constitution
  - from: architect
    to: skill-validator
    via: constitution
  - from: architect
    to: plan
    via: sourcetree
  - from: architect
    to: dev
    via: sourcetree
  - from: architect
    to: drift
    via: sourcetree
  - from: architect
    to: amend
    via: sourcetree
  - from: architect
    to: plan
    via: techstack
  - from: architect
    to: dev
    via: techstack
  - from: architect
    to: review
    via: techstack
  - from: architect
    to: qa
    via: techstack
  - from: architect
    to: drift
    via: techstack
  - from: architect
    to: amend
    via: techstack
  - from: architect
    to: plan
    via: architecture
  - from: architect
    to: dev
    via: architecture
  - from: architect
    to: drift
    via: architecture
  - from: architect
    to: amend
    via: architecture
  - from: architect
    to: plan
    via: design
  - from: architect
    to: dev
    via: design
  - from: architect
    to: dev
    via: stack
  - from: architect
    to: qa
    via: stack
  - from: architect
    to: amend
    via: adr
  - from: architect
    to: analyze
    via: adr
  - from: architect
    to: review
    via: adr
  - from: architect
    to: retro
    via: adr
  - from: plan
    to: dev
    via: epic
  - from: plan
    to: analyze
    via: epic
  - from: plan
    to: dev
    via: story
  - from: plan
    to: clarify
    via: story
  - from: plan
    to: review
    via: story
  - from: plan
    to: qa
    via: story
  - from: plan
    to: analyze
    via: story
  - from: plan
    to: amend
    via: story
  - from: plan
    to: retro
    via: sprint
  - from: plan
    to: analyze
    via: sprint
  - from: plan
    to: skill-generator
    via: skill-spec
  - from: plan
    to: skill-validator
    via: skill-spec
  - from: clarify
    to: dev
    via: clarification
  - from: analyze
    to: plan
    via: analyze-report
  - from: analyze
    to: amend
    via: analyze-report
  - from: skill-generator
    to: skill-validator
    via: skill-yaml
  - from: skill-generator
    to: skill-validator
    via: skill-md
  - from: skill-generator
    to: skill-validator
    via: agent-md
  - from: skill-generator
    to: skill-validator
    via: command-md
  - from: dev
    to: review
    via: dev-notes
  - from: dev
    to: qa
    via: dev-notes
  - from: dev
    to: retro
    via: dev-notes
  - from: review
    to: qa
    via: review-report
  - from: review
    to: dev
    via: review-report
  - from: review
    to: retro
    via: review-report
  - from: qa
    to: dev
    via: qa-report
  - from: qa
    to: retro
    via: qa-report
  - from: amend
    to: plan
    via: impact-report
  - from: amend
    to: analyze
    via: adr
  - from: amend
    to: review
    via: adr
  - from: amend
    to: retro
    via: adr
  - from: retro
    to: amend
    via: retro-report
  - from: retro
    to: plan
    via: retro-report
  - from: drift
    to: amend
    via: drift-report
  - from: drift
    to: architect
    via: drift-report
  - from: plan
    to: analyze
    via: handoff
  - from: skill-generator
    to: skill-validator
    via: handoff
  - from: retro
    to: amend
    via: handoff
  - from: architect
    to: brainstorm
    via: handoff
  - from: dev
    to: clarify
    via: handoff
```

## 6. Known divergences

Recorded here so that no specification silently inherits them.

| # | Divergence | Registry position |
|---|---|---|
| 1 | `code_mapper` is dispatched by both `onboard` and `drift` | `onboard` owns the worker file; `drift` reuses it. This is the single exception to the no-borrowing rule in `01-skill-anatomy.md`. |
| 2 | `02-skill-roster.md` gives the commands `/skill-gen` and `/skill-validate` for the skills named `skill-generator` and `skill-validator` | The registry records both the skill name and the command string. A cross-reference check that compares a slash command to a skill name must map through the `command` field. |
| 3 | `observed-constraints` has no file of its own: `onboard`'s document fence is `sourcetree.md`, `techstack.md`, `architecture.md` and `.devforgeai/stack.yaml` | The template renders an OBSERVED section inside each of the three Markdown files, the way `clarification` renders a section inside a story. |
| 4 | `sourcetree`, `techstack` and `architecture` have two producers: `architect` (INTENDED) and `onboard` (OBSERVED) | Both write the same template. `01-skill-anatomy.md` distinguishes them by the `status` field on each context entry, and OBSERVED is advisory while INTENDED binds. |
| 5 | `qa` and `review` produce a report but take a story id, so their runs are story-anchored | The document fence is the report path; the story's `commands` and `test_plan` enter `.devforgeai/work/<run>/run.yaml` so `qa`'s `run_tests` phase can broker `test` (`10-sequencer-and-contracts.md` section 4). Neither skill may write code: the fence admits only its own report. |
| 6 | `skill-validator`'s `<arg>` is the skill it validated, but `02-skill-roster.md` writes its repair row as `/skill-gen {spec}`, a spec id | The sequencer holds the skill name, not the spec id, so the row it emits on `verdict: findings` or `verdict: fail` is `/skill-gen <skill> --fix` (`10-sequencer-and-contracts.md` section 6). A specification records both and does not claim the spec id is filled in. |
| 7 | A "calls" edge between two skills is a handoff row, never a nested run | `phase start` refuses while a run is active and no operation suspends a run, so `plan` → `analyze`, `skill-generator` → `skill-validator`, `retro` → `amend`, `architect` → `brainstorm` and `dev` → `clarify` are edges `via: handoff` in the block above: control flow, not a `depends_on` document edge, and the second command runs after the first run closed. |

Four divergences recorded in earlier drafts are closed: `architect`'s `mandate_specs` phase and its `docs/plan/` fence are gone, so `plan` is the only producer of `skill-spec`; `qa`'s `run_tests` phase can broker `test`, because a story-anchored run carries the story's `commands`; both `.devforgeai/stack.yaml` and `.devforgeai/provenance/adr/**` have write paths — `stack.yaml` from `architect`'s `techstack` phase and `onboard`'s `code_map` phase, validated against its schema, and the ADR directory from `architect`'s and `amend`'s `adr` phases, validated against the `adr` template header — before either is applied; and `architect`'s `adr` phase now holds the same producer exception `amend`'s does, so a decision reached while designing no longer needs an `amend` run to reach the registry.
