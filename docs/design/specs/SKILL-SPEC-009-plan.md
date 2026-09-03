---
template: skill-spec
template_version: 1
id: SKILL-SPEC-009
skill_name: plan
target: both
status: approved
author: "DevForgeAI wave-2 specification author"
date: 2026-09-02
depends_on:
  - source: docs/design/01-skill-anatomy.md#primary-window-contract
    hash: sha256:de7d775e46bd44c52089a3998b114a5ebb5ce6875be3ebf3dca126f5a9bbaa32
    excerpt: "**The model dispatches, the sequencer decides.** For an anatomy-governed skill, the primary window (provider entry adapter + skill orchestration) does light, trivial work only."
  - source: docs/design/01-skill-anatomy.md#dedicated-templates
    hash: sha256:55bd4a18d63e645adffa187d34256dc7db7370095dcbf9e96a190028f7e65a5e
    excerpt: "Every anatomy-governed non-Research skill owns its templates under `.devforgeai/skills/<name>/templates/`. No shared or generic template exists."
  - source: docs/design/01-skill-anatomy.md#context-bundle-format
    hash: sha256:7b068feb30e7cc2f66292b512ac179cd217df225fb58517d2aaadd30b25236dc
    excerpt: "A literal placeholder hash (`sha256:fixture...`, `sha256:PENDING`) is reported as `unresolvable-source`."
  - source: docs/design/10-sequencer-and-contracts.md#4-per-skill-phase-registry
    hash: sha256:37b51ea5748164510e7687527aeab55bc92af9524ee771b293989640cecf8cce
    excerpt: "| plan | 1 | `epics` | `epic_writer` | docs | 2 | — | document | — |"
  - source: docs/design/10-sequencer-and-contracts.md#3-4-re-resolving-sources-and-the-one-downgrade
    hash: sha256:722dadc1737749e30d244f222aaa1d8b845bc93f4a573b16f662719e58b49bcd
    excerpt: "The story gate re-resolves every `provenance[]` and `context[]` entry as well as `commands`."
  - source: docs/design/10-sequencer-and-contracts.md#5-2-validation-order
    hash: sha256:9f1bf77b7e84302ff6f3f20260228d57390cc97ab8e8d3f68f52c3ff2658aab8
    excerpt: "| 10 | `changed[]` is a subset of `claimed_paths` | refuse, reason `UNCLAIMED_CHANGE`; this **is** a phase attempt, because real bytes were written outside the claim |"
  - source: docs/design/10-sequencer-and-contracts.md#5-4-transition-oracles
    hash: sha256:ffa41b5d270dc260e28fa9f6bdbc855069a6e922d1148c74b25860dba63484dc
    excerpt: "the phase declared `writes: docs` and `changed[]` is non-empty, unless it is marked conditional, in which case an empty change set needs a non-empty `note`; every changed path exists in the root with the bytes the checkpoint will hold"
  - source: docs/design/10-sequencer-and-contracts.md#6-handoff-envelope
    hash: sha256:de637edceb588df104a40b57738eb263989f6603f90ece6f4d0e64fef07ffb6a
    excerpt: "`next` is never empty and is never a description. One exact command."
  - source: docs/design/11-artifact-registry.md#1-template-registry
    hash: sha256:25886acb1c2963b15938f0c577c3bfd28b9807dd2dd961c59ff2b43fa00b62e2
    excerpt: "| `story` | `.devforgeai/skills/plan/templates/story.md` | 3 |"
  - source: docs/design/11-artifact-registry.md#2-artifact-path-patterns
    hash: sha256:2d2e97afff50edf6b35bf674b1de217c684d5091361e5f1deae12de52b95fb51
    excerpt: "| `docs/plan/<slug>/stories/STORY-NNN.md` | `story` | plan | sequencer |"
  - source: docs/design/11-artifact-registry.md#3-depends-on-edges
    hash: sha256:f3c304ff840d2027432f743288bccec0ea5bc5d7b99b7f41c8d524b1c3591da2
    excerpt: "| `story` | `provenance`: its epic anchor and its PRD requirement anchor."
  - source: docs/design/02-skill-roster.md#plan
    hash: sha256:bd41bbb9a24165dcd2210b6e417ace22a03892b75848c2da88acf5665ed3e92e
    excerpt: "Gate: PRD passes prd template; every INTENDED constitution section it will slice has a current hash."
  - source: docs/design/02-skill-roster.md#handoff-decision-tables
    hash: sha256:6edc7499ee163453f3be6390b0dda08b3fab885f1399ff944056040596ec3801
    excerpt: "| plan | pass | `/analyze {slug}` to re-check traceability, then `/dev {first_story}` |"
  - source: docs/design/05-subagent-sets.md#sets-per-skill
    hash: sha256:9e12f3beb236a025c18d40e741c09ba675bd71d2d87f56e2b205c7556b944bf9
    excerpt: "| plan | epic-writer, story-writer, skill-spec-writer, dependency-mapper, estimator, sprint-writer, critic |"
  - source: docs/design/05-subagent-sets.md#contract-format
    hash: sha256:23d8c21c51ca70b053f4661b32249b86a330c816e02db1219be72d5a9bc07a4e
    excerpt: "`must_not` is compiled into the agent prompt verbatim."
  - source: docs/design/06-skill-specification.md#where-the-spec-sits-in-the-pipeline
    hash: sha256:3a3b21544bff9cfa31bc8529dbd0b0cf46952ea27169823452023b5433f5f62f
    excerpt: "- `architect` writes the mandate and nothing else. It does not author a spec and does not call skill-generator."
  - source: docs/design/03-brownfield.md#per-request-entry-with-scope
    hash: sha256:5a799568689fb5a1533e03a5ff3bd00cc7cb91a9c6cbde43e73d7b87a7a9411c
    excerpt: "Brownfield requests vary in size. The user picks the entry phase:"
  - source: docs/design/templates/story.md#acceptance-criteria
    hash: sha256:858884c170a1e7036346f1887791672316583bca6f1f4730ceb5961e35a3c166
    excerpt: "Numbered. Each criterion has exactly one `test_plan` row and becomes exactly one test."
  - source: docs/design/templates/story.md#verification
    hash: sha256:35e80f0b31a907d8743d3fe1cbbe2e1b0248629b37ffcbe84a953883f3f040d6
    excerpt: "What each dev sub-phase must show, named only by `commands.use` key."
  - source: docs/design/07-purpose-and-enforcement.md#2-the-problem-in-concrete-terms
    hash: sha256:aa195bc0696dcc9da2f3511b7e03bac418430231f83e3f2ced3f71a4fa585917
    excerpt: "| Skips a phase and starts coding from the prompt |"
  - source: docs/design/12-post-mvp.md#pm-09
    hash: sha256:d78bedbec92e8830c353a747f7b163b882d9ccd7d523a9e51df3d9cc56222829
    excerpt: "A monorepo runs today by pinning one section per story; cross-package stories are out of scope."
---

# Skill Specification: plan

A stranger with no conversation history must be able to build this skill from this document alone. Every question the generator would otherwise ask is answered below.

## 0. Generator instructions

These instructions are addressed to the skill-generating agent (Anthropic's `skill-creator` skill, or DevForgeAI's `skill-generator`). They replace its interview.

### Cold-session prompt

Paste this into a fresh session from the repository root:

```
Use the skill-creator skill to build the skill specified in docs/design/specs/SKILL-SPEC-009-plan.md.
Follow its section 0 exactly. Output directory: ./out. Eval mode: quick.
```

### Rules for the generator

1. **Do not interview.** Sections 1-13 pre-answer every Capture Intent and Interview question (what it enables, when it triggers, output format, test cases, edge cases, input/output formats, example files, success criteria, dependencies). Treat this document as the conversation history you are told to harvest from.
2. **Test prompts are pre-approved.** Use section 10 verbatim as `evals/evals.json`. Do not ask whether they look right.
3. **Trigger queries are pre-approved.** Use section 4 verbatim as the trigger eval set. Do not ask for sign-off.
4. **No human review loop.** Do not wait for the user to review results. Proceed to the next stage on your own.
5. **Eval mode** is given in the prompt and is one of two values:
   - `skip`: write the skill only. Do not create `evals/`, do not run test prompts, do not optimize the description.
   - `quick`: write the skill and `evals/evals.json`. Run each test prompt once with the skill (no baseline run), grade with the grader agent, write `grading.json`, and report pass/fail per expectation in your final message. Do not run the description-optimization loop. Run the eval executions and the grader as foreground Agent-tool subagents, never as background shell processes, and do not end your turn until every `grading.json` exists: a headless session terminates when the top-level turn ends and orphans anything still running.
   - Any other mode name is a spec defect. The deferred interactive mode is `12-post-mvp.md#pm-06`.
6. **Output location** is given in the prompt. Create `./out/plan/`. Do not write anywhere else except the `plan-workspace/` sibling that eval runs require.
7. **On ambiguity, stop before output.** If the spec is still `draft`, contains an unresolved authoring assumption, omits a section, contradicts itself, or leaves a decision this document does not make, do not guess and do not write candidate skill files. End with a list titled `SPEC GAPS` naming each section and question. The spec author fixes and approves the spec before re-running.
8. **Fidelity over creativity.** Use the description in section 3 verbatim. Use the worker contracts in section 7d verbatim as `agents/<role>.md` bodies, adding only the framing the grader agent in skill-creator uses (Role, Inputs, Process, Output). Do not add steps, tools, or behaviours the spec does not mention.
9. **Finish with the acceptance checks** in section 14 and include their output in your final message.

## 1. Identity

| Field | Value |
|-------|-------|
| name | `plan` (kebab-case, 4 characters, equals the directory name, no `claude`/`anthropic` prefix) |
| title | Epic, Story and Sprint Planning |
| purpose | Turn one PRD and the INTENDED architecture set into epics, self-contained stories carrying their own hash-addressed context bundle and criterion-to-test map, the skill specifications any of those stories require, and the sprints that order them. |
| category | devforgeai-phase |
| version | 1.0.0 (skill-package version written to `metadata.version`; not the DevForgeAI or Research Core version) |

## 2. Problem and requirements

**Without this skill:** work reaches an agent as a prompt rather than as an artifact, and `07-purpose-and-enforcement.md` section 2 names the result twice. "Skips a phase and starts coding from the prompt" is what happens when nothing between the PRD and the editor is machine-checkable: the agent reads a paragraph of intent and begins. "Declares done because a file exists or a checkbox is ticked" is what happens next, because there is no criterion-to-test map, so completion is whatever the agent says it is. Two further failures follow from the same absence. A story with no fence lets an agent touch any file it likes, so the "writes artifacts it was never asked for" row applies. A story with no pinned digests silently drifts from the architecture it was written against, so the "gate is prose the model may ignore" row applies to every downstream phase at once.

| ID | Kind | Requirement |
|----|------|-------------|
| R1 | explicit | Take one project slug and produce epics, stories and sprints at the registry's paths under `docs/plan/<slug>/`. Source: `11-artifact-registry.md` section 2. |
| R2 | explicit | Every story is self-contained: its own `context[]` bundle of excerpt-plus-anchor-plus-digest entries, its `write_fence`, its `commands` reference into `stack.yaml`, and one `test_plan` row per acceptance criterion. Source: `templates/story.md`. |
| R3 | explicit | `plan` is the sole author of the skill-spec template. For each `requires_skill` naming a skill the project lacks, and each `constitution.md#mandates` entry that needs a skill the project lacks, write `docs/plan/<slug>/skill-specs/SKILL-SPEC-NNN.md` and order a `skill-generator` story before the dependent story. Source: `06-skill-specification.md#where-the-spec-sits-in-the-pipeline`. |
| R4 | explicit | `--scope feature|change|hotfix` selects how much provenance the run has to work with, and the choice is recorded in every story's frontmatter. Source: `03-brownfield.md#per-request-entry-with-scope`. |
| R5 | implicit | A story's acceptance criteria are observable and each becomes exactly one test named in `test_plan`, because the `red` oracle asserts every `test_plan` name is present and failing and the `green` oracle asserts every one passes. Source: `10-sequencer-and-contracts.md` section 5.4. |
| R6 | implicit | Every `test_plan` row's `file` is inside that story's `write_fence`, and no fence entry is sequencer-owned, because the story gate refuses both. Source: `10-sequencer-and-contracts.md` section 3.2. |
| R7 | implicit | An undecided value is tagged in place rather than invented, and the tag is what makes `dev`'s gate refuse the story until `/clarify` settles it. Source: `templates/story.md#acceptance-criteria`. |
| R8 | discovered | The `skill_specs` phase declares `writes: docs` and is marked conditional in `examples/hooks/policy.py`: the `document` oracle accepts an empty change set from it when the receipt's note says why none was owed. Every other `writes: docs` phase must change a file. Section 9 records the decision. |
| R9 | discovered | No worker has a hashing command on its Bash surface, yet every story's `provenance[]`, `context[]` and `commands.hash` entries require one, so `story_writer` writes `sha256:PENDING` and the sequencer resolves it at ingest (step 13a of `10-sequencer-and-contracts.md` section 5.2) before the checkpoint. Section 9 records the resolution. |
| R10 | discovered | `--scope hotfix` skips epic decomposition, not the epic file: `epics`, `stories` and `sprints` declare `writes: docs`, so each still owes an artifact. `dependencies` and `estimates` declare `writes: fields` and may legitimately change nothing. Section 9 records what the hotfix path writes. |

## 3. Description

```yaml
description: >
  Break one project into epics, self-contained stories and sprints. Each story carries its own
  excerpt-and-digest context bundle, its write fence, its command keys, and one named test per
  acceptance criterion, so a developer agent can build it without opening the architecture
  documents. Use this skill after architect has written the constitution set, when someone asks
  to break work down, to write user stories or tickets, to plan a sprint, to order work by
  dependency, to size or estimate a backlog, or to turn a requirement into something a coding
  agent can pick up; use the scope flag for a smaller change or a hotfix. It also writes the
  skill specification for any capability the project still lacks. Do NOT use it to decide the
  architecture or tech stack (use architect), to resolve an open question inside a story
  (use clarify), to audit traceability across the plan (use analyze), or to write code (use dev).
```

Character count: 915 / 1024.

## 4. Trigger set

```json
[
  {"query": "/plan shop", "should_trigger": true},
  {"query": "the architecture set for billing is done, break it into stories", "should_trigger": true},
  {"query": "we need tickets for sprint one, ordered so nothing is blocked", "should_trigger": true},
  {"query": "/plan api --scope change, the change is: add a rate limiter to the public endpoints", "should_trigger": true},
  {"query": "turn REQ-004 and REQ-005 in docs/PM/shop/prd.md into something a coding agent can actually pick up", "should_trigger": true},
  {"query": "size the backlog for tinyapp and tell me what fits in two weeks", "should_trigger": true},
  {"query": "the constitution mandates tdd, so we need the dev-tdd skill specced before anyone codes", "should_trigger": true},
  {"query": "hotfix: the slug function crashes on unicode, i need a story for it right now", "should_trigger": true},
  {"query": "analyze found three requirements with no story. redo the plan for shop", "should_trigger": true},
  {"query": "what should the next sprint contain now that sprint-001 is finished", "should_trigger": true},
  {"query": "decide whether we use postgres or sqlite for this project", "should_trigger": false},
  {"query": "criterion 3 of STORY-004 is ambiguous, get it pinned down", "should_trigger": false},
  {"query": "implement STORY-001 with tests first", "should_trigger": false},
  {"query": "check that every PRD requirement has a story and every story has a requirement", "should_trigger": false},
  {"query": "generate the dev-tdd skill from its spec", "should_trigger": false},
  {"query": "the constitution changed, update every story that depended on the old section", "should_trigger": false},
  {"query": "write a retrospective for sprint-002", "should_trigger": false},
  {"query": "add a Gantt chart to our project wiki for the next quarter", "should_trigger": false},
  {"query": "review STORY-007's diff before I merge it", "should_trigger": false},
  {"query": "explain the difference between an epic and a story to my new hire", "should_trigger": false}
]
```

## 5. Use cases

### UC-1: Full plan from an approved architecture set
- **User says:** "/plan shop"
- **Steps:** 1. `devforgeai phase start plan shop` runs the document fence gate over `docs/plan/shop/**` and opens the run. 2. `epic_writer` writes one `EPIC-NNN.md` per PRD requirement cluster inside the candidate root, each listing the constitution sections it depends on. 3. `story_writer` writes one `STORY-NNN.md` per epic slice, each with a full context bundle, a fence, a `commands` reference and a `test_plan`. 4. `skill_spec_writer` writes a spec for each `requires_skill` naming a missing skill and each mandate needing one, or none and says why. 5. `dependency_mapper` sets `blocked_by` on the stories it ordered. 6. `estimator` sets `size` on each. 7. `sprint_writer` writes the sprint files and stamps each scheduled story's `sprint`. 8. `plan_critic` checks every criterion against its `test_plan` row and every story against its epic.
- **Result:** after promotion, `docs/plan/shop/epics/`, `stories/`, `sprints/` and, when needed, `skill-specs/` are populated, and the handoff's next steps are `/analyze shop` first and `/dev STORY-001` second.

### UC-2: A change against an existing project, no PRD
- **User says:** "/plan api --scope change, the change is: add a rate limiter to the public endpoints"
- **Steps:** 1. The gate opens the run. 2. `epic_writer` writes one `EPIC-000.md` whose `## Goal` quotes the intent verbatim, whose `## Scope` line records `Scope: change`, and whose `provenance` is an empty list because no PRD requirement anchor exists — the reduced-provenance record `/analyze` later flags. Every value the intent leaves open is tagged in place. 3. `story_writer` slices that epic, and every story carries `scope: change` and a `## Unchanged Behaviour` section, which the story template requires for this scope. 4. The remaining phases run unchanged.
- **Result:** a plan whose provenance gap is on the record rather than hidden, and stories that name what must keep working.

### UC-3: Hotfix
- **User says:** "hotfix: the slug function crashes on unicode, i need a story for it right now"
- **Steps:** 1. The gate opens the run. 2. `epic_writer` writes one `EPIC-000.md` recording the hotfix intent, because the `epics` phase declares `writes: docs` and owes an artifact whatever the scope. 3. `story_writer` writes exactly one `STORY-HOTFIX-NNN.md` with `scope: hotfix`, a `## Unchanged Behaviour` section, and `gate_policy.unresolvable_source` set to `WARN`, which is legal only at this scope. 4. `sprint_writer` writes `sprint-001.md` holding that single story. 5. `plan_critic` checks the criterion-to-test map as usual.
- **Result:** one story, one sprint, and a handoff naming `/analyze` for the slug first and `/dev STORY-HOTFIX-001` second.

## 6. Inputs and outputs

### Inputs
| Input | Format | Example file | Required |
|-------|--------|--------------|----------|
| project slug | positional argument, kebab-case | `shop` | yes |
| `--scope` flag | one of `feature`, `change`, `hotfix`; defaults to `feature` | not a file | no |
| PRD | markdown with frontmatter, `prd` template, owned by `pm` | `docs/design/examples/fixtures/plan/docs/PM/tinyapp/prd.md` | for `feature`; absent for `change` and `hotfix` |
| change or hotfix intent | prose supplied in the invocation | not a file | for `change` and `hotfix` |
| constitution set | markdown, `constitution`, `sourcetree`, `techstack`, `architecture` and `design` templates, owned by `architect` | `docs/design/examples/fixtures/plan/docs/architecture/constitution.md` | yes |
| stack section | YAML, `stack` template | `.devforgeai/stack.yaml` | yes; every story pins its digest and names one anchor |
| analyze, impact and retro reports | markdown, `analyze-report`, `impact-report`, `retro-report` templates | `docs/reports/analyze-<slug>.md` | no |
| `--reslice` flag | boolean, followed by one or more story ids; directs `story_writer` to rebuild those stories' context bundles | not a file | no |
| `--next-sprint` flag | boolean; directs `sprint_writer` to start after the last sprint marked done | not a file | no |
| `--retry` flag | boolean; a plain re-run, changing nothing the workers read | not a file | no |
| `.devforgeai/state.yaml` enforcement block | YAML, written by the sequencer at `devforgeai phase start` | `.devforgeai/state.yaml` | yes; the run's `write_fence` is read from it |

The positional slug is required on every invocation, flags included. `devforgeai phase start plan <arg>` substitutes `<arg>` into the fence `docs/plan/<arg>/**` (`10-sequencer-and-contracts.md` section 4), so the run cannot open without it. The four skills that route a stale story bundle here — `dev`, `review`, `qa` and `analyze` — and `amend`'s impact report all write the invocation as `/plan {slug} --reslice {story}` for that reason; the shorter `/plan --reslice {story}` in `02-skill-roster.md:89`, `:94` and `:105` and in `01-skill-anatomy.md:116` would fence the run to a directory named for a story id. Section 9 records the decision.

### Outputs
| Output | Format | Location | Template |
|--------|--------|----------|----------|
| epics | markdown | `docs/plan/<slug>/epics/EPIC-NNN.md` | `epic`, seeded by `assets/epic.md` |
| stories | markdown | `docs/plan/<slug>/stories/STORY-NNN.md` | `story` version 3, seeded by `assets/story.md` |
| skill specifications | markdown | `docs/plan/<slug>/skill-specs/SKILL-SPEC-NNN.md` | `skill-spec`, seeded by `assets/skill-spec.md` |
| sprints | markdown | `docs/plan/<slug>/sprints/sprint-NNN.md` | `sprint`, seeded by `assets/sprint.md` |
| phase results | JSON, written by the sequencer | `.devforgeai/work/plan-<slug>/<phase>-result.json` | none |
| phase reports | markdown, written by the sequencer | `.devforgeai/work/plan-<slug>/<phase>-report.md` and `docs/reports/plan-plan-<slug>-<phase>.md` | none |
| handoff | JSON plus its rendering | `.devforgeai/work/plan-<slug>/handoff.json` | `handoff` |

Template header keys, from `11-artifact-registry.md` section 1, are what the consuming skill's gate reads:

| Template | Version | `id_pattern` | `required_frontmatter` | `required_sections` |
|---|---|---|---|---|
| `epic` | 1 | `^EPIC-[0-9]{3}$` | id, slug, template, template_version, status, risk_tier, provenance, depends_on | Goal, Scope, Stories, Constitution Sections |
| `story` | 3, `accepts_versions: [3]` | `^STORY-(HOTFIX-)?[0-9]{3}$` | id, epic, sprint, scope, status, template, template_version, requires_skill, risk_tier, size, gate_policy, blocked_by, provenance, context, write_fence, commands, test_plan | Goal, Context, Interface, Acceptance Criteria, Unchanged Behaviour, Out of Scope, Verification, Clarifications |
| `skill-spec` | 1 | `^SKILL-SPEC-[0-9]{3}$` | id, skill_name, target, status, template_version, depends_on, author, date | the sixteen numbered sections listed in `templates/skill-spec.md` |
| `sprint` | 1 | `^sprint-[0-9]{3}$` | id, slug, template, template_version, status, stories | Goal, Stories, Order, Exit Criteria |

`forbidden_text` carries the same five entries on all four — the two words meaning "not written yet", the opening and closing double-brace placeholder markers, and the angle-bracketed fill-in marker, listed verbatim in `11-artifact-registry.md` section 1.

### Output template

The story is the artifact every downstream gate reads, so it is given in full, every field:

````
---
id: STORY-001
epic: EPIC-001
sprint: sprint-001
scope: feature
status: ready
template: story
template_version: 3
requires_skill: dev
risk_tier: LOW
size: S
gate_policy:
  unresolved_assumption: BLOCK
  stale_hash: BLOCK
  unresolvable_source: BLOCK
  write_fence_violation: BLOCK
  test_runner_missing: REQUIRE_HUMAN
  criterion_without_test: BLOCK
blocked_by: []
provenance:
  - source: docs/plan/shop/epics/EPIC-001.md#stories
    hash: sha256:0000000000000000000000000000000000000000000000000000000000000000
  - source: docs/PM/shop/prd.md#requirements
    hash: sha256:0000000000000000000000000000000000000000000000000000000000000000
context:
  - source: docs/architecture/techstack.md#data-access
    status: INTENDED
    hash: sha256:0000000000000000000000000000000000000000000000000000000000000000
    excerpt: |
      TS-002 Orders are read and written through the standard library sqlite3
      driver. No object-relational mapper is admitted.
  - source: shop/text.py#L1-L12
    status: OBSERVED
    hash: sha256:0000000000000000000000000000000000000000000000000000000000000000
    excerpt: |
      """Text helpers."""
write_fence:
  - shop/text.py
  - tests/test_text.py
commands:
  source: .devforgeai/stack.yaml#python
  hash: sha256:0000000000000000000000000000000000000000000000000000000000000000
  use: [test, lint]
test_plan:
  - criterion: 1
    file: tests/test_text.py
    name: test_slugify_lowercases_and_hyphenates
  - criterion: 2
    file: tests/test_text.py
    name: test_slugify_strips_punctuation
---

# STORY-001: Slugify helper

## Goal

Callers can turn an arbitrary display title into a URL-safe slug.

## Context

The write fence holds one existing module with no public function and one test file
that currently collects a single import test. The excerpts in the frontmatter bundle
are the whole context; no worker opens the source documents.

## Interface

`slugify(title: str) -> str`. Returns a lowercase, hyphen-separated string. Raises
nothing; an unmappable character is dropped.

## Acceptance Criteria

1. WHEN the title contains capitals and spaces THE SYSTEM SHALL return the title
   lowercased with each run of spaces replaced by one hyphen.
2. WHEN the title contains punctuation THE SYSTEM SHALL return the title with the
   punctuation removed and no doubled hyphens.

## Unchanged Behaviour

None. Nothing in the write fence had behaviour before this story.

## Out of Scope

- Transliterating non-Latin scripts.
- Any change to the command-line entry point.

## Verification

- Red: `test` exits non-zero and every `test_plan` test is present and failing for its
  own criterion, not for an import or syntax error.
- Green: `test` exits zero with no test outside `test_plan` added or changed.
- Refactor: `test` and `lint` exit zero; no file outside `write_fence` changed.

## Clarifications

None.
````

`sprint: null` is written only where section 9 says so. `risk_tier` comes from the epic and may only be raised in the story. `size` is set by `estimator`, and an `L` story is split rather than written. `commands.use` names keys only; `build` is required in that list when the pinned section has `compiled: true`.

### Return envelope (DevForgeAI-anatomy skills only)

One schema, both providers: `devforgeai.worker-result/v1`, normative in `schemas/devforgeai/v1/worker-result.schema.json`. A worker's final message is exactly this object, with no Markdown fence and no surrounding prose. A document writer has already written its files inside the candidate root when it returns; the receipt claims what it wrote. `plan_critic` writes only into its own run-scoped evidence directory.

```yaml
schema: devforgeai.worker-result/v1
run: "plan-shop"
skill: "plan"
phase: "stories"
agent: "story_writer"
status: pass | fail | needs_user | could_not_run
reason_code: runner_missing | timeout | network | hook_fault   # required only when status is could_not_run
candidate: {id: "plan-shop", input_checkpoint: "epics"}
claimed_paths: ["docs/plan/shop/stories/STORY-001.md"]   # root-relative, at most 64; empty on any non-pass status
evidence_refs: ["docs/plan/shop/stories/STORY-001.md"]   # at most 16
note: "12 stories written across 3 epics"
issues: [{id, kind, text}]                               # at most 10
```

At `devforgeai ingest-result` the sequencer derives `changed[{path, blob_sha256, kind}]` from the checkpoint diff, refuses when `changed` is not a subset of `claimed_paths` (`UNCLAIMED_CHANGE`) or a path is outside the fence, validates each written file against its template header, runs the transition oracle inside the root, writes `<phase>-result.json` with `changed` and the checkpoint ref, releases the lease and advances. For a `writes: fields` phase it additionally refuses any change whose body bytes differ or whose frontmatter diff reaches beyond `blocked_by`, `size` and `sprint`. `next` requires `status: fail` plus a registry `rewind_to`; no plan phase declares one, so the key is never present. Unknown keys refuse the receipt.

`gate_policy` (`BLOCK | REQUIRE_HUMAN | WARN | OFF`) is a defect-to-action map declared in the consumed artifact, never a status returned here. `plan` is a plain document run, so its own enforcement block carries the fixed map `{unresolvable_source: BLOCK}`; the wider maps this skill writes are read by `dev`, `review` and `qa`, not by this run.

## 7. Procedure

### 7a. Steps

The body of `SKILL.md`. Imperative voice; each step says why it matters.

1. Parse the positional slug and the optional `--scope`, `--reslice`, `--next-sprint` and `--retry` flags, `--scope` defaulting to `feature`. When the scope is `change` or `hotfix`, keep the intent text the user supplied as an argument token; when `--reslice` is given, keep the story ids that follow it as ids and forward them to the `stories` dispatch. Read no file in this window — why: anything read here stays in the primary window for the whole run, and the primary-window contract forbids opening an artifact.
2. Call `devforgeai phase start plan <slug>`. On exit 1, print the defect list the gate wrote to stderr and stop — why: the gate opens the candidate root every later phase writes into, so a refusal leaves nothing half-written.
2a. Run `devforgeai status` and paste its block into every dispatch below. The block names `run`, `candidate.root`, `phase`, `fence` and `granted_keys` — why: a worker writes inside the candidate root and cannot resolve it from the canonical tree, and this block is the one thing a dispatch carries that is not a path or an id.
3. Dispatch `agents/epic_writer.md` with the status block, the slug, the PRD path, the constitution set paths, the scope token and, for `change` and `hotfix`, the intent text. The intent is the one piece of content that has no file, so it is passed as an argument; everything else is a path — why: pasting a requirement into the prompt would put the PRD's text in two places, and the worker reads the file itself.
4. Dispatch `agents/story_writer.md` with the slug, the scope token, `.devforgeai/work/<run>/epics-result.json`, the constitution set paths and `.devforgeai/stack.yaml`. Load `references/stories.md` before the dispatch — why: the bundle rules, the fence rules and the criterion-to-test rule are what the story is gated against later.
5. Dispatch `agents/skill_spec_writer.md` with the slug, `.devforgeai/work/<run>/stories-result.json` and `docs/architecture/constitution.md`.
6. Dispatch `agents/dependency_mapper.md`, then `agents/estimator.md`, each with the slug and `.devforgeai/work/<run>/stories-result.json`.
7. Dispatch `agents/sprint_writer.md` with the slug and the dependency and estimate result paths.
8. Dispatch `agents/plan_critic.md` with every prior result path and the produced artifact paths.
9. Advance on a returned `pass`; stop and print on `needs_user` or `could_not_run` — why: `needs_user` closes the run immediately without consulting the attempt counter, so there is nothing left to dispatch.
10. Print the block the sequencer rendered into `.devforgeai/work/<run>/handoff.json`, verbatim. Compose nothing — why: the renderer adds nothing to the receipt, and `devforgeai status` must print the identical block from a cold session.
11. When the handoff reports the run `ready_to_promote` and the user asks for the promotion, call `devforgeai promote <run>` — why: promotion moves the candidate root's bytes into the canonical checkout under the lock, and a `REQUIRE_HUMAN` block is the only state in which the model may ask for it.

A transition failure is not the primary window's business: `devforgeai phase next` exits 1 with the oracle's problem rows, the sequencer rewinds the candidate root to the phase's input checkpoint, and the same worker returns a fresh receipt. The primary window dispatches once per phase.

`dependency_mapper` and `estimator` are field-restricted writers: each opens the story files the previous phase wrote and sets `blocked_by` and `size` in place, leaving every body byte and every other frontmatter key identical. The phase order is `stories` then `dependencies` then `estimates` then `sprints`, so `story_writer` never fills those keys from a later phase's findings and `sprint_writer` sets only `sprint`.

### 7b. Sub-phases and workers

Gate, Record and Handoff dispatch no LLM: they are `devforgeai` sequencer operations, and Slice is a sequencer step inside `phase start` (open item OI-1). That matters more here than anywhere else: `story_writer` builds every story's own context bundle, which is a different job from the run-level bundle the sequencer slices into `context.json`.

| # | Sub-phase | Performed by | Writes | Isolation |
|---|-----------|--------------|--------|-----------|
| 0 | Gate | sequencer: `devforgeai phase start plan <slug>`, which also opens the candidate root | sequencer | n/a |
| 1 | Slice | sequencer: a step inside `phase start` that resolves the incoming artifact's hashed bundle into `.devforgeai/work/<run>/context.json`. No worker | sequencer | n/a |
| 2 | Write: `epics` | worker: `epic_writer` | candidate | required |
| 3 | Write: `stories` | worker: `story_writer` | candidate | required |
| 4 | Write: `skill_specs` | worker: `skill_spec_writer` | candidate, conditional | required |
| 5 | Write: `dependencies` | worker: `dependency_mapper` | candidate, fields | preferred |
| 6 | Write: `estimates` | worker: `estimator` | candidate, fields | preferred |
| 7 | Write: `sprints` | worker: `sprint_writer` | candidate | required |
| 8 | Review: `critic` | worker: `plan_critic` | evidence | required |
| 9 | Record | sequencer: `devforgeai phase next` | sequencer | n/a |
| 10 | Handoff | sequencer: `devforgeai phase next`, which on the last passing transition marks the run `ready_to_promote` and renders the first block, a `REQUIRE_HUMAN` handoff naming `devforgeai promote <run>`; that command, run only after the user confirms in the session, renders the second | sequencer | n/a |

`epic_writer` is the persona and `plan_critic` is the critic. They are different workers with different prompts and different agent files, because a persona reviewing its own output is the hallucination vector the anatomy exists to remove. Six workers are producers that write inside the candidate root; `plan_critic` is a judge whose `Write` the dispatcher confines to `.devforgeai/work/<run>/evidence/plan_critic/`, a gitignored, run-scoped directory outside the candidate root that is never promoted. Its findings file lives there and is named in `evidence_refs`; `issues[]` stays the bounded summary the handoff carries.

For an anatomy-governed skill, `SKILL.md` dispatches each worker through the selected target's provider-native worker mechanism, using the generated target profile, file paths and the `devforgeai status` block. It never pastes or paraphrases artifact content, objectives, or acceptance criteria into the prompt. Its Bash grammar is exactly `devforgeai status | phase start <skill> <arg> | phase fail --reason | validate | promote <run>`; every other sequencer operation is hook-only. The `Isolation` column is the DevForgeAI contract value compiled into the target profile, not Claude's `isolation` frontmatter field; the framework does not use Claude's worktree isolation or `EnterWorktree`, because both fork from HEAD and the run's phases build linearly on one candidate root. Runtime verification of isolation is `12-post-mvp.md#pm-01`.

### 7c. Evidence and gate table

One row per registry phase, in registry order. `<run>` is `plan-<slug>`; `<phase>` is the registry phase name.

| phase | worker | deterministic gate check | gate_policy | evidence file | transition oracle |
|---|---|---|---|---|---|
| `epics` | `epic_writer` | run-level gate at `devforgeai phase start`: `plan` is a known skill of kind `document`; no run is already active; the fence entry `docs/plan/<slug>/**` is repository-relative, contains no `..`, and is not sequencer-owned; and no active or `ready_to_promote` run's fence overlaps this one (`FENCE_OVERLAP`). Ingest validation: `changed` derived from the checkpoint diff is a subset of `claimed_paths` (`UNCLAIMED_CHANGE` otherwise), every changed path canonicalises inside `candidate.root`, matches the fence, and is allowed by the phase's `writes: docs` mode; then the whole-root package and import rescan before the checkpoint. `scripts/check_epic.py` parses each written file against the `epic` header keys | document run's fixed map `{unresolvable_source: BLOCK}`; every `devforgeai phase start` defect is a refusal whatever a declared value says, and only `test_runner_missing` changes behaviour at transition time, which no `plan` phase reaches because none brokers a command | `.devforgeai/work/<run>/epics-result.json`, `epics-report.md` | `document`: the phase produced at least one file and every declared output with non-null content exists on disk |
| `stories` | `story_writer` | as `epics`, plus `scripts/check_story.py` over each written story: `template_version` is 3, the id matches `^STORY-(HOTFIX-)?[0-9]{3}$`, all eighteen frontmatter keys and all eight sections are present, no placeholder text remains, every `test_plan` row carries `criterion`, `file` and `name`, every `test_plan` file is inside that story's `write_fence`, no fence entry is sequencer-owned, `commands.source` names an anchor that exists in `.devforgeai/stack.yaml`, and every criterion has exactly one `test_plan` row | `{unresolvable_source: BLOCK}` for this run. The map each story declares is read later, by `dev`, `review` and `qa` | `.devforgeai/work/<run>/stories-result.json`, `stories-report.md` | `document`: as `epics` |
| `skill_specs` | `skill_spec_writer` | as `epics`, plus `scripts/check_skill_spec.py`: the sixteen numbered sections are present and in order, the id matches `^SKILL-SPEC-[0-9]{3}$`, the eight frontmatter keys are present, `status` is `approved`, and no placeholder text remains | `{unresolvable_source: BLOCK}` | `.devforgeai/work/<run>/skill_specs-result.json`, `skill_specs-report.md` | `document`, conditional: the phase is marked `conditional` in `examples/hooks/policy.py`, so an empty change set passes when the receipt's note says why no specification was owed; otherwise every claimed specification must exist in the candidate root |
| `dependencies` | `dependency_mapper` | ingest validation as `epics`, restricted by the registry's `writes: fields` mode, which the worker header carries as `writes: candidate` narrowed to a field fence: every changed path matches the field fence `docs/plan/<slug>/stories/*.md`, the file already existed, its body bytes are identical to the input checkpoint's, and its frontmatter diff touches nothing but `blocked_by`, `size` and `sprint`. A change outside that restriction refuses the receipt | `{unresolvable_source: BLOCK}` | `.devforgeai/work/<run>/dependencies-result.json`, `dependencies-report.md` | `report_only`: no file outside the fence changed since the input checkpoint and the whole-root package and import policy holds. A field-restricted phase may legitimately change nothing, so an empty change set passes |
| `estimates` | `estimator` | ingest validation as `dependencies`, over the same field fence and the same three keys, on top of whatever the `dependencies` checkpoint left | `{unresolvable_source: BLOCK}` | `.devforgeai/work/<run>/estimates-result.json`, `estimates-report.md` | `report_only`: as `dependencies` |
| `sprints` | `sprint_writer` | as `epics`, plus `scripts/check_sprint.py`: the id matches `^sprint-[0-9]{3}$`, the six frontmatter keys and four sections are present, and every id in `stories` names a story file that exists under `docs/plan/<slug>/stories/`. This phase also sets each scheduled story's `sprint` key in place, under the same field restriction the two preceding phases carry, so those edits are re-checked by `scripts/check_story.py` | `{unresolvable_source: BLOCK}` | `.devforgeai/work/<run>/sprints-result.json`, `sprints-report.md` | `document`: as `epics` |
| `critic` | `plan_critic` | at ingest: `claimed_paths` is empty, because the registry declares the phase `writes: none` and the worker header `writes: evidence`, and any change inside the candidate root refuses the receipt as `UNCLAIMED_CHANGE`; the dispatcher confines this worker's writes to `.devforgeai/work/<run>/evidence/plan_critic/`; the phase grants no command key, so `devforgeai run` refuses every key it might name | `{unresolvable_source: BLOCK}` | `.devforgeai/work/<run>/critic-result.json`, `critic-report.md`, then `handoff.json` | `report_only`: as `dependencies`. On pass this is the last phase: the run is marked `ready_to_promote`, enforcement is cleared, and the first handoff's `next` is `devforgeai promote <run>`; the second handoff, written by that command once the user asks for it, takes its `next` from the section 7e table |

Attempt budgets, materialised into the run file from the registry, are 2 for every phase. No `plan` phase declares `rewind_to`, so a `fail` receipt carrying `next` is refused; a `fail` without `next` becomes a transition problem row, the phase retries to its limit, and the run then blocks `REQUIRE_HUMAN` (open item OI-4).

Promotion is not part of the run's phases. The last passing `devforgeai phase next` marks the run `ready_to_promote` and writes a `REQUIRE_HUMAN` handoff whose one forward command is `devforgeai promote <run>`; the candidate root and its checkpoints stay on disk and no canonical byte moves. The compiled `SKILL.md` runs that command only after the user confirms in the session, and it is that command — never `phase next` — that merges the candidate root into the canonical checkout under `.devforgeai/lock`, refusing on `STALE_BASE` when canonical HEAD has moved past the run's pinned `base_ref`, on `DIRTY_TARGET` when a dirty canonical file is among the changed paths, and on `MERGE_CONFLICT` when the rebase cannot replay the run. A refusal moves no canonical byte and leaves the run `ready_to_promote` with its root intact, so the command can be run again once the named cause is settled. The second handoff block is written by a promotion that succeeded, and its `next` is the section 7e row for the run's outcome. Each refusal is a handoff row in section 7e.

The four `scripts/check_*.py` invocations are designed as sequencer-side checks and are not implemented in `examples/hooks/devforgeai.py` today: `10-sequencer-and-contracts.md` section 3.3 shows the implemented document gate checking fence entries only, and receipt validation stopping at the claim, the fence and the package policy. `check_story.py` is nonetheless the library the story gate imports when `dev` opens the story later, which is why `plan` owns it. Section 9 records the gap.

### 7d. Worker contracts

Each block becomes `agents/<role>.md` verbatim, wrapped in skill-creator's Role / Inputs / Process / Output framing, and compiles to one provider profile per target. `name` is the canonical registry worker name, which is what a hook receives as `agent_type`; the compiled filename carries the skill prefix so two skills' profiles cannot collide. `tools` are the Claude names and `tools_codex` the Codex ones, where `apply_patch` stands in for `Edit` and `Write`. `model: inherit` keeps the worker on the session's model, which is what the terminal-only constraint leaves available. No plan phase grants a stack command key, so no worker here carries `Bash(devforgeai run *)`. Claude-only frontmatter — `hooks`, `memory`, `background`, `permissionMode`, and Claude's own `isolation` — is omitted from every profile.

```yaml
name: epic_writer
description: Dispatch this worker at the epics phase to write one epic per requirement cluster.
skill: plan
writes: candidate
model: inherit
tools: [Read, Grep, Glob, Bash(devforgeai status), Edit, Write]
tools_codex: [Read, Grep, Glob, Bash(devforgeai status), apply_patch]
skills: []
compiled_to: [.claude/agents/plan-epic_writer.md, .codex/agents/plan-epic_writer.toml]
responsibility: Write one epic per requirement cluster inside the candidate root, each naming the constitution sections its stories will slice and the PRD requirement anchors it covers.
inputs:
  - docs/PM/<slug>/prd.md, when the scope is feature
  - the change or hotfix intent text, when the scope is not feature
  - docs/architecture/constitution.md, sourcetree.md, techstack.md, architecture.md and each design-<topic>.md
  - the scope token
  - assets/epic.md and references/epics.md, for the header keys and the scope rules
outputs:
  - one docs/plan/<slug>/epics/EPIC-NNN.md per epic, written inside the candidate root and each claimed
  - each epic's risk_tier and the requirement anchors it covers, in its own frontmatter and its Constitution Sections list
must_not:
  - change any path outside docs/plan/<slug>/
  - record a requirement the PRD or the supplied intent does not contain
  - leave a value undecided without tagging it in place, which is what makes the dev gate refuse the story that inherits it
  - write outside the candidate root, or outside the run's fence inside it
isolation: required
returns: devforgeai.worker-result/v1
body:
  job: Write one epic per requirement cluster, each naming the constitution sections its stories will slice.
  inputs: The list above, read under the candidate root; nothing outside it is opened.
  rules: references/epics.md, the three scope rules, and the must_not list.
  receipt: One devforgeai.worker-result/v1 object; claimed_paths lists every epic written, at most 64.
```

```yaml
name: story_writer
description: Dispatch this worker at the stories phase to write one self-contained story per epic slice.
skill: plan
writes: candidate
model: inherit
tools: [Read, Grep, Glob, Bash(devforgeai status), Edit, Write]
tools_codex: [Read, Grep, Glob, Bash(devforgeai status), apply_patch]
skills: []
compiled_to: [.claude/agents/plan-story_writer.md, .codex/agents/plan-story_writer.toml]
responsibility: Write one story per epic slice inside the candidate root, each self-contained: its own context bundle of excerpt, anchor and digest entries, its write fence, its stack reference and one test_plan row per acceptance criterion.
inputs:
  - .devforgeai/work/<run>/epics-result.json
  - docs/plan/<slug>/epics/
  - docs/architecture/constitution.md, sourcetree.md, techstack.md, architecture.md and each design-<topic>.md
  - the source files the epic's components name, for OBSERVED excerpts with line anchors
  - .devforgeai/stack.yaml, for the anchor name each story pins
  - the scope token
  - the story ids named after --reslice, when the invocation carried it; those stories' bundles are rebuilt from current sources and every other story is left byte-identical
  - assets/story.md and references/stories.md, for the bundle, fence, criterion and test_plan rules
outputs:
  - one docs/plan/<slug>/stories/STORY-NNN.md per story, written inside the candidate root and each claimed
  - each story's own context bundle, write fence, commands reference and one test_plan row per acceptance criterion
must_not:
  - summarise or paraphrase a context excerpt; an excerpt is verbatim bytes from the anchor it names
  - write a criterion with no test_plan row, or a test_plan row whose file is outside that story's write fence
  - name a write_fence entry that is sequencer-owned
  - write a literal build, test, lint or format command anywhere in a story; commands are a hashed reference and a list of keys
  - fill blocked_by or size, which the two field-restricted phases that follow set
  - change any path outside docs/plan/<slug>/
  - write outside the candidate root, or outside the run's fence inside it
isolation: required
returns: devforgeai.worker-result/v1
body:
  job: Write each story so a developer agent can build it without opening an architecture document.
  inputs: The list above, read under the candidate root.
  rules: references/stories.md and references/story-bundle.md, the criterion-to-test rule, and the must_not list.
  receipt: One devforgeai.worker-result/v1 object; claimed_paths lists every story written, at most 64, and the remainder above that ceiling is one issues row.
```

```yaml
name: skill_spec_writer
description: Dispatch this worker at the skill_specs phase to write one specification per capability the project still lacks, or none when none is owed.
skill: plan
writes: candidate
model: inherit
tools: [Read, Grep, Glob, Bash(devforgeai status), Edit, Write]
tools_codex: [Read, Grep, Glob, Bash(devforgeai status), apply_patch]
skills: []
compiled_to: [.claude/agents/plan-skill_spec_writer.md, .codex/agents/plan-skill_spec_writer.toml]
responsibility: Write one skill specification per capability the project lacks, inside the candidate root, filling all sixteen sections of the skill-spec template from the mandate or the requires_skill value that demands it.
inputs:
  - .devforgeai/work/<run>/stories-result.json
  - docs/architecture/constitution.md, for the mandates section
  - the installed skill directories under .devforgeai/skills/, to tell a missing skill from a present one
  - assets/skill-spec.md and references/skill_specs.md, for the sixteen sections and the approval rule
outputs:
  - one docs/plan/<slug>/skill-specs/SKILL-SPEC-NNN.md per owed specification, written inside the candidate root and each claimed
  - a note naming the mandate or story that demanded each, or saying why none was owed
must_not:
  - write a spec for a skill that already exists under .devforgeai/skills/
  - deliver a spec with status approved while it still records an unresolved authoring assumption
  - change any path outside docs/plan/<slug>/skill-specs/
  - write outside the candidate root, or outside the run's fence inside it
isolation: required
returns: devforgeai.worker-result/v1
body:
  job: Write a specification only where one is owed, and say in the note why none was when none was.
  inputs: The list above, read under the candidate root.
  rules: references/skill_specs.md, the sixteen sections and the approval rule, and the must_not list.
  receipt: One devforgeai.worker-result/v1 object; the phase is conditional, so an empty claimed_paths with a note naming the reason is a passing result.
```

```yaml
name: dependency_mapper
description: Dispatch this worker at the dependencies phase to set each story's blocked_by list in place.
skill: plan
writes: candidate
model: inherit
tools: [Read, Grep, Glob, Bash(devforgeai status), Edit, Write]
tools_codex: [Read, Grep, Glob, Bash(devforgeai status), apply_patch]
skills: []
compiled_to: [.claude/agents/plan-dependency_mapper.md, .codex/agents/plan-dependency_mapper.toml]
responsibility: Order the stories by dependency and set each story's `blocked_by` frontmatter key in place, leaving every body byte and every other key identical.
inputs:
  - .devforgeai/work/<run>/stories-result.json
  - docs/plan/<slug>/stories/
  - .devforgeai/work/<run>/skill_specs-result.json, so a story that needs a generated skill is ordered after the story that generates it
  - references/dependencies.md, for what counts as a dependency edge
outputs:
  - each edited docs/plan/<slug>/stories/STORY-NNN.md inside the candidate root, claimed, with only its blocked_by key changed
  - a note carrying one reason per edge, since the edge itself is the only thing the story records
must_not:
  - change any frontmatter key but blocked_by, or any body byte
  - change a path outside the field fence docs/plan/<slug>/stories/*.md
  - create a story file, or edit one this run did not write
  - record an edge no interface or fence overlap supports
  - produce a cycle; report one as an issues row instead
  - write outside the candidate root
isolation: preferred
returns: devforgeai.worker-result/v1
body:
  job: Set blocked_by on each story from the edges the interfaces and fences actually support.
  inputs: The list above, read under the candidate root.
  rules: references/dependencies.md, the field restriction to blocked_by, and the must_not list.
  receipt: One devforgeai.worker-result/v1 object; claimed_paths lists every story edited, and an empty list is a passing result when no story is blocked.
```

```yaml
name: estimator
description: Dispatch this worker at the estimates phase to set each story's size in place and flag every L for splitting.
skill: plan
writes: candidate
model: inherit
tools: [Read, Grep, Glob, Bash(devforgeai status), Edit, Write]
tools_codex: [Read, Grep, Glob, Bash(devforgeai status), apply_patch]
skills: []
compiled_to: [.claude/agents/plan-estimator.md, .codex/agents/plan-estimator.toml]
responsibility: Assign each story a size of XS, S, M or L from its fence breadth, criterion count and interface surface, set the `size` key in place, and flag every L for splitting.
inputs:
  - .devforgeai/work/<run>/stories-result.json
  - docs/plan/<slug>/stories/
  - references/estimates.md, for the size bands and what drives each
outputs:
  - each edited docs/plan/<slug>/stories/STORY-NNN.md inside the candidate root, claimed, with only its size key changed
  - a note carrying the two factors that set each size
  - issues: one row per story sized L, naming the split the story needs
must_not:
  - change any frontmatter key but size, or any body byte
  - change a path outside the field fence docs/plan/<slug>/stories/*.md
  - size a story it has not read
  - write outside the candidate root
isolation: preferred
returns: devforgeai.worker-result/v1
body:
  job: Set size on each story from its fence breadth, criterion count and interface surface.
  inputs: The list above, read under the candidate root.
  rules: references/estimates.md, the four size bands, and the must_not list.
  receipt: One devforgeai.worker-result/v1 object; claimed_paths lists every story edited, and each L is one issues row.
```

```yaml
name: sprint_writer
description: Dispatch this worker at the sprints phase to write the sprint files and set each scheduled story's sprint key.
skill: plan
writes: candidate
model: inherit
tools: [Read, Grep, Glob, Bash(devforgeai status), Edit, Write]
tools_codex: [Read, Grep, Glob, Bash(devforgeai status), apply_patch]
skills: []
compiled_to: [.claude/agents/plan-sprint_writer.md, .codex/agents/plan-sprint_writer.toml]
responsibility: Write the sprint files that order the stories inside the candidate root, and set the `sprint` key on each story they schedule.
inputs:
  - .devforgeai/work/<run>/dependencies-result.json
  - .devforgeai/work/<run>/estimates-result.json
  - docs/plan/<slug>/stories/
  - the --next-sprint token, when the invocation carried it; the first sprint this run writes then follows the last sprint whose status is done
  - assets/sprint.md and references/sprints.md, for the header keys and the exit-criteria rule
outputs:
  - one docs/plan/<slug>/sprints/sprint-NNN.md per sprint, written inside the candidate root and each claimed
  - each scheduled story edited in place with only its sprint key changed, claimed alongside the sprint files
must_not:
  - change any part of a story other than its sprint frontmatter value
  - place a story in a sprint earlier than a story it is blocked by
  - change any path outside docs/plan/<slug>/
  - write outside the candidate root, or outside the run's fence inside it
isolation: required
returns: devforgeai.worker-result/v1
body:
  job: Write the sprints in dependency order and stamp each scheduled story with the sprint it belongs to.
  inputs: The list above, read under the candidate root.
  rules: references/sprints.md, the exit-criteria rule, and the must_not list.
  receipt: One devforgeai.worker-result/v1 object; claimed_paths lists every sprint written and every story stamped.
```

```yaml
name: plan_critic
description: Dispatch this worker at the critic phase to judge every artifact this run wrote against its template header and the upstream anchor it cites.
skill: plan
writes: evidence
model: inherit
tools: [Read, Grep, Glob, Bash(devforgeai status), Write]
tools_codex: [Read, Grep, Glob, Bash(devforgeai status), apply_patch]
skills: []
compiled_to: [.claude/agents/plan-plan_critic.md, .codex/agents/plan-plan_critic.toml]
responsibility: Check every artifact this run wrote against its template header and against the upstream anchor it cites, and report defects without repairing them.
inputs:
  - every .devforgeai/work/<run>/<phase>-result.json from the six prior phases
  - docs/plan/<slug>/epics/, stories/, sprints/ and skill-specs/
  - docs/PM/<slug>/prd.md and docs/architecture/constitution.md
  - references/critic.md, for the defect classes and the evidence a finding must carry
outputs:
  - .devforgeai/work/<run>/evidence/plan_critic/findings.md, the full defect list and the per-requirement coverage table, written in its own run-scoped evidence directory and named in evidence_refs
  - issues: at most ten rows, each naming the file, the id and the defect class
  - note: the count of PRD requirement anchors covered by a story and uncovered
must_not:
  - repair a defect it found
  - pass a story without quoting the criterion and the test_plan row that pair
  - report a defect against an artifact no phase of this run wrote
  - write anywhere but its own run-scoped evidence directory, or run any stack command key
isolation: required
returns: devforgeai.worker-result/v1
body:
  job: Judge every artifact this run wrote against its template header and the upstream anchor it cites.
  inputs: The list above, read under the candidate root; nothing outside it is opened.
  rules: references/critic.md, the defect classes, and the must_not list.
  receipt: One devforgeai.worker-result/v1 object; claimed_paths is empty on every status, evidence_refs names the findings file it wrote under its run-scoped evidence directory, and each defect is also one issues row.
```

A producer's tools are the read set plus `Edit` and `Write`, which Codex serves as `apply_patch`; a judge's are the read set plus a `Write` the dispatcher confines to `.devforgeai/work/<run>/evidence/<agent>/`, a gitignored, run-scoped directory outside the candidate root that is never promoted. Both include `Bash(devforgeai status)` and nothing else on the Bash surface, because no `plan` phase grants a stack command key (open item OI-3).

### 7e. Handoff outcomes

The `handoff.outcomes` block the skill declares. The sequencer selects the row by receipt status and fills `{slug}`, `{story}`, `{first_story}` and `{spec}` from state.

| Outcome | Next steps |
|---------|------------|
| `devforgeai promote {run}` succeeded | 1. `/analyze {slug}` to re-check traceability, then 2. `/dev {first_story}` |
| promoted, stories carry an unresolved assumption tag | 1. `/clarify {story}` for each story listed in the open items, then 2. `/dev {first_story}` |
| pass, all phases, run `ready_to_promote`, nothing promoted (`REQUIRE_HUMAN`) | 1. `devforgeai promote {run}` |
| `devforgeai promote {run}` succeeded, skill specifications written | 1. `/skill-gen {skill}` for each spec listed in the open items, naming that spec's `skill_name`, then 2. `/dev {first_story}` |
| needs_user | 1. resolve the open items named in the handoff, then 2. `/plan {slug}`, which resumes the blocked run at `run.yaml#blocked_at` with attempts reset — the run stayed `active` with its root on disk |
| fail at any other phase, `max_attempts` reached | 1. fix what the handoff names, then `/plan {slug}` — the run is blocked, not closed: it stays `active` with its candidate root and every checkpoint on disk and `run.yaml#blocked_at` naming the phase, and this same command resumes it there with attempts reset. `devforgeai phase fail --reason <text>` is what abandons it instead |
| could_not_run, `reason_code: hook_fault` | 1. reinstall the dispatcher named in `.devforgeai/sessions/`, then 2. `/plan {slug}` |
| could_not_run, any other `reason_code` | 1. the repair route for that reason code, then 2. `/plan {slug}` |
| BLOCK, recorded by `devforgeai phase fail --reason` | 1. `/status` |
| `devforgeai promote {run}` refused `STALE_BASE` in worktree mode | 1. `devforgeai promote {run}` again; that command rebases the candidate root onto the new canonical HEAD, reruns the last transition oracle and retries the fast-forward itself before it reports, so this row is reached only when the retry also failed |
| `devforgeai promote {run}` refused `STALE_BASE` in copy mode, or `MERGE_CONFLICT` after an aborted rebase | 1. reconcile `docs/plan/{slug}/` by hand, then `devforgeai promote {run}` — the refusal moved no canonical byte, and the run stays `ready_to_promote` with its root intact |
| `devforgeai promote {run}` refused `DIRTY_TARGET` | 1. commit or discard the dirty canonical file the refusal names, then `devforgeai promote {run}` |
| `phase start` refused `FENCE_OVERLAP` | 1. finish or abandon the run the refusal names, then `/plan {slug}` |

A gate refusal is not a row in this table. `devforgeai phase start` exits 1 with the defect list and writes no handoff (`10-sequencer-and-contracts.md` section 3.2), so `02-skill-roster.md`'s `gate fail` row is corrected out of the decision table and recorded in section 9. `02`'s `analyze found gaps` row is a reason to run `/plan {slug}` again from a cold session, not an outcome this run can report, because `analyze` runs after this run closes.

## 8. Bundled resources

### Layout (fixed)

```
plan/SKILL.md               # at most 500 lines: identity, phase list, dispatch loop, handoff table
  references/epics.md
  references/stories.md
  references/story-bundle.md
  references/skill_specs.md
  references/dependencies.md
  references/estimates.md
  references/sprints.md
  references/critic.md
  references/envelope.md
  agents/epic_writer.md
  agents/story_writer.md
  agents/skill_spec_writer.md
  agents/dependency_mapper.md
  agents/estimator.md
  agents/sprint_writer.md
  agents/plan_critic.md
  scripts/check_epic.py
  scripts/check_story.py
  scripts/check_skill_spec.py
  scripts/check_sprint.py
  assets/epic.md
  assets/story.md
  assets/skill-spec.md
  assets/sprint.md
```

Link depth: `SKILL.md` links to `references/`, `agents/`, `scripts/` and `assets/`; an `agents/*.md` links to `references/*.md`; nothing links further. The `stories` phase carries more guidance than one comfortable reference file holds, so it is split into `stories.md` and `story-bundle.md`, and `SKILL.md` names both at that dispatch.

### scripts/

Every script is deterministic, non-interactive, prints data to stdout and diagnostics to stderr, and documents `--help`.

| File | Purpose | Invocation | Exit codes |
|------|---------|------------|------------|
| `check_epic.py` | Validate one epic against the `epic` header keys, id pattern, required sections and forbidden text, and check that every `depends_on` source and anchor resolves. Invoked by a human, and designed to be imported by the sequencer at `devforgeai ingest-result` for the `epics` phase; that import is not implemented today (section 9) | `python3 scripts/check_epic.py PATH [--json]` | 0 pass, 1 defects listed on stdout, 2 usage |
| `check_story.py` | The story gate library. Validate one story against the `story` version 3 header: frontmatter keys, section list, id pattern, forbidden text, an `ASSUMPTION:` span outside `## Clarifications`, one `test_plan` row per criterion with `criterion`, `file` and `name` present and the file inside `write_fence`, no sequencer-owned fence entry, `commands.source` resolving to an existing anchor, and every `provenance[]`, `context[]` and `commands.hash` entry re-resolved by the rule in `10-sequencer-and-contracts.md` section 3.4. `--lenient` downgrades an unresolvable source to a warning, and is refused for a story under `docs/plan/`. This is the library the sequencer imports when `dev`, `qa` or `review` opens the story, which is why `plan` ships it | `python3 scripts/check_story.py PATH [--json] [--strict\|--lenient]` | 0 pass, 1 defects, 2 usage or unparseable frontmatter |
| `check_skill_spec.py` | Validate one skill specification against the `skill-spec` header: the sixteen numbered sections present and in order, the id pattern, the eight frontmatter keys, `status` equal to `approved`, and no placeholder text. This is the library the sequencer imports when `skill-generator` gates the spec, which is why `plan` ships it | `python3 scripts/check_skill_spec.py PATH [--json]` | 0 pass, 1 defects, 2 usage |
| `check_sprint.py` | Validate one sprint against the `sprint` header keys, id pattern and sections, and check that every id in `stories` names an existing story file and that no story precedes one it is blocked by | `python3 scripts/check_sprint.py PATH [--stories-dir DIR] [--json]` | 0 pass, 1 defects, 2 usage |

### references/

| File | Content | Load when |
|------|---------|-----------|
| `epics.md` | The `epic` header keys, `EPIC-NNN` ids, what belongs in each of the four sections, the `risk_tier` bands, and the three scope rules: `feature` cites PRD requirement anchors; `change` quotes the supplied intent in `## Goal`, records `Scope: change` as the first line of `## Scope`, and carries an empty `provenance` list; `hotfix` does the same and produces exactly one epic. | dispatching `epic_writer` |
| `stories.md` | The `story` version 3 header keys and sections, the `STORY-NNN` and `STORY-HOTFIX-NNN` id rules, the criterion form (`WHEN condition THE SYSTEM SHALL observable result`), the one-criterion-one-test rule, the fence rules, the `commands` reference shape, the `gate_policy` map and the one value that may be loosened at `hotfix` scope, and where an undecided value is tagged. | dispatching `story_writer` |
| `story-bundle.md` | The context bundle rules: excerpt plus anchor plus digest, verbatim bytes only, `status: INTENDED` binds and `status: OBSERVED` is advisory, heading anchors versus `#L10-L20` line anchors, and the hash rule from `10-sequencer-and-contracts.md` section 3.4 with the reason a placeholder digest is an unresolvable source. | dispatching `story_writer` |
| `skill_specs.md` | When a spec is owed (a `requires_skill` naming a skill absent from `.devforgeai/skills/`, or a `constitution.md#mandates` entry naming one), the sixteen sections, the approval rule, and the ordering story that must run `skill-generator` before the dependent story. | dispatching `skill_spec_writer` |
| `dependencies.md` | What makes a dependency edge: an interface one story defines and another consumes, a shared fence path, or a story that needs a skill another story generates. Cycle reporting. The field restriction: this phase changes `blocked_by` and nothing else, on files the `stories` phase already wrote. | dispatching `dependency_mapper` |
| `estimates.md` | The four size bands and the factors that set them: fence breadth, criterion count, interface surface. Why an `L` is split rather than written. The field restriction: this phase changes `size` and nothing else. | dispatching `estimator` |
| `sprints.md` | The `sprint` header keys, `sprint-NNN` ids, the exit-criteria rule, and the one story frontmatter value this phase is allowed to change, `sprint`. | dispatching `sprint_writer` |
| `critic.md` | The defect classes — criterion with no test row, test row outside the fence, uncited context excerpt, story with no epic anchor, requirement with no story, sprint ordering that contradicts `blocked_by` — and the evidence each finding must carry. | dispatching `plan_critic` |
| `envelope.md` | The `devforgeai.worker-result/v1` receipt, its bounds (64 `claimed_paths`, 16 `evidence_refs`, 16 KiB note, 10 issues), the closed status set with `reason_code`, the rule that `claimed_paths` is empty on any non-pass status, and the rule that `next` needs a registry `rewind_to` no plan phase declares. | every dispatch |

### assets/

| File | Used for |
|------|----------|
| `epic.md` | `docs/plan/<slug>/epics/EPIC-NNN.md` skeleton: frontmatter keys and the four required section headings, empty. |
| `story.md` | `docs/plan/<slug>/stories/STORY-NNN.md` skeleton: all eighteen frontmatter keys and all eight section headings, empty, matching the section 6 output template's shape. |
| `skill-spec.md` | `docs/plan/<slug>/skill-specs/SKILL-SPEC-NNN.md` skeleton: the eight frontmatter keys and the sixteen numbered section headings, empty. |
| `sprint.md` | `docs/plan/<slug>/sprints/sprint-NNN.md` skeleton. |

### agents/

| File | Worker (from section 7d) |
|------|-------------------------|
| `epic_writer.md` | `epic_writer` |
| `story_writer.md` | `story_writer` |
| `skill_spec_writer.md` | `skill_spec_writer` |
| `dependency_mapper.md` | `dependency_mapper` |
| `estimator.md` | `estimator` |
| `sprint_writer.md` | `sprint_writer` |
| `plan_critic.md` | `plan_critic` |

## 9. Gotchas and edge cases

| Situation | What goes wrong | What to do instead |
|-----------|-----------------|--------------------|
| OI-1: Slice belongs to a framework worker, but no `plan` phase dispatches one | The generated skill grows an eighth agent file with no registry phase to run it | Slice is a sequencer step inside `devforgeai phase start`: it resolves the incoming artifact's already-hashed bundle and writes `.devforgeai/work/<run>/context.json`, which every worker of the run is handed by path. That is the run-level bundle. Each story's own bundle is a different artifact, built by `story_writer`, which is why `references/story-bundle.md` carries those rules — verbatim excerpts, anchors, no summarising — as that worker's own contract. |
| OI-2: provenance conformance at the gate | A `plan` spec that promised story-style re-resolution at its own gate would over-promise | `10-sequencer-and-contracts.md` section 3.4 carries full re-resolution, and section 4 makes `qa` and `review` the only story-anchored document skills. `plan`'s own gate is the fence gate alone, so nothing re-resolves the PRD or the constitution digests when this run opens. `02-skill-roster.md#plan` describes that check as `plan`'s gate; it is a requirement on the gate, not behaviour today, and `scripts/check_epic.py` is the designed replacement. |
| OI-3: worker tools | A generator either gives every worker the same tools or widens a judge's to include an unfenced write | Tools follow the role. A producer carries `Read`, `Grep`, `Glob`, `Bash(devforgeai status)` plus `Edit` and `Write`, which Codex serves as `apply_patch`; every write is denied outside `candidate.root` and outside the phase's fence, and a `writes: fields` phase is narrowed again to its field fence and its three keys. A judge carries the read set plus a `Write` the dispatcher confines to `.devforgeai/work/<run>/evidence/<agent>/`. `Bash(devforgeai run *)` is granted only where a phase declares run keys, and no `plan` phase does. |
| OI-4: no outcome row for `status: fail` with no `next` | A reader assumes a failing critic passes silently | `examples/hooks/devforgeai.py` inserts `"<agent> reported fail"` as a transition problem row, so the phase retries to `max_attempts: 2` and then blocks `REQUIRE_HUMAN`. The `fail at any other phase` row in section 7e is that path. |
| OI-5: `--retry`, `--reslice` and `--next-sprint` look like resume flags | A user expects `/plan {slug} --reslice {story}` to reopen a run and patch one story | No flag resumes anything. A blocked run resumes on its own account: it stays `active` with `run.yaml#blocked_at` naming the phase, and plain `devforgeai phase start plan {slug}` resumes it there with `attempts` reset, which is why `--retry` is unnecessary and is not implemented as a resume. Every other invocation — after `devforgeai phase fail --reason <text>` closed a run, or with no run open — starts fresh at `epics`, and the flags change only what the workers read: `--reslice` directs `story_writer` to rebuild the bundles of the named stories, `--next-sprint` directs `sprint_writer` to start after the last sprint marked done, and `--retry` is a plain re-run. `--scope` is the only flag whose value reaches the artifacts. The exact invocation is `/plan {slug} --reslice {story}`, with the slug positional and one or more story ids after the flag: the fence is `docs/plan/{arg}/**`, so a story id in the argument position would fence the run to a directory that does not exist. Every skill that routes here writes it that long form. |
| OI-6: the ADR path is a producer exception | Not reachable from `plan` | `.devforgeai/provenance/adr/**` is declared for `architect`/`adr` and `amend`/`adr` and is not in `plan`'s fence. `plan` has no `adr` phase and writes nothing under `.devforgeai/provenance/`. It reads ADRs only through `analyze` and `retro` reports it consumes. |
| OI-7: `02-skill-roster.md` used to say plan "then calls `/analyze` before handoff" | A generated `SKILL.md` tries `devforgeai phase start analyze` from inside a plan run and is refused, because a run is already active | No skill invokes another skill's run. The roster row now reads `/analyze {slug}` to re-check traceability, then `/dev {first_story}`, and `10-sequencer-and-contracts.md` section 6 states that such a row is a handoff whose first `next` step is that command, so section 7e's `pass` row orders `/analyze {slug}` first and `/dev {first_story}` second; a human or a fresh session runs each after this run is promoted or abandoned. Section 7a's dispatch loop names no other command. |
| OI-8: `05-subagent-sets.md` writes worker names hyphenated (`epic-writer`, `critic`) while the registry writes them with underscores | `agent_type` fails the phase-agent binding check and the receipt is refused | The registry name in `10-sequencer-and-contracts.md` section 4 is canonical: `epic_writer`, `story_writer`, `skill_spec_writer`, `dependency_mapper`, `estimator`, `sprint_writer`, `plan_critic`. Note `plan_critic`, not `critic`. It is the agent filename, the `agents/` table row, and the string compared to the stop event's `agent_type`. |
| OI-9: the `.devforgeai/stack.yaml` write path | A `story_writer` that tried to add a missing anchor would have its write denied at `PreToolUse` and its receipt refused at ingest | The path is a producer exception admitted only from `architect`/`techstack` and `onboard`/`code_map`. Every `plan` phase is refused it as sequencer-owned, and it is not in `plan`'s fence. `story_writer` reads the file to pin its digest and to name an anchor that already exists; when the anchor a story needs is absent, it returns `needs_user` naming `/architect {slug} --yolo` as the repair. |
| OI-10: skills whose command takes no positional argument | Not reachable from `plan` | `/plan` always carries a slug, which is the `devforgeai phase start` argument, the `{arg}` substituted into the fence `docs/plan/<slug>/**`, and the run id component in `plan-<slug>`. |
| OI-11 (new): no worker has a hashing command, yet every story requires three kinds of digest | A worker's Bash surface is `devforgeai status` alone, so `story_writer` cannot fill `provenance[].hash`, `context[].hash` or `commands.hash` and emits a placeholder. `10-sequencer-and-contracts.md` section 3.4 classes a placeholder as `unresolvable-source`, `--lenient` is refused for any story under `docs/plan/`, and `devforgeai phase start dev <story>` would therefore have refused every story this skill writes. This was the single defect that broke the plan-to-dev edge | The fix has landed at `devforgeai ingest-result` as step 13a of `10-sequencer-and-contracts.md` section 5.2: after the change set is validated and before the checkpoint is taken, the sequencer resolves every `sha256:PENDING` digest in a changed artifact's frontmatter under the same rule the gate re-resolves with, records each substitution in the result row's `digests_resolved`, and refuses the phase when a source or anchor does not resolve. Hashing stays out of every worker prompt, there is one hash implementation, and the promoted bytes carry real digests, so a story this skill writes opens a dev run with no flag. `story_writer` still emits `sha256:PENDING` and must not attempt a digest of its own. |
| OI-11 corollary: a heading inside a fenced code block truncates a section | The hash rule and `docs/design/specs/verify.py` both resolve a heading anchor by scanning for the next line beginning with hashes, with no fence tracking. A context entry pointing at a section that contains a fenced example with its own heading pins fewer bytes than a reader expects, and the excerpt a worker copies may sit outside the hashed range | `references/story-bundle.md` instructs `story_writer` to take its excerpt from the bytes the anchor actually resolves to, and `plan_critic`'s uncited-excerpt defect class catches an excerpt that is not inside the pinned range. Where a wanted region falls outside, the entry uses an `#L10-L20` line anchor instead of a heading anchor. |
| The `skill_specs` phase has nothing to write | A `writes: docs` phase whose change set is empty fails the `document` oracle, which would block every project whose stories all name skills that already exist | `examples/hooks/policy.py` marks the phase `conditional`, so the `document` oracle accepts an empty change set from it when the receipt's note says why no specification was owed. `skill_spec_writer` writes a spec only when one is owed, because writing a spec for an existing skill would be fiction, and it says so in the note. The dedicated failure row is gone from section 7e because the phase no longer fails on an empty result. |
| `--scope change` has no PRD to cite | The `epic` template requires a `provenance` key, and there is no requirement anchor to put in it | `epic_writer` writes `provenance: []` and quotes the user's intent verbatim in `## Goal`, with every value the intent leaves open tagged in place. The empty list is the reduced-provenance record `03-brownfield.md` describes, and `/analyze` reports it as a gap rather than a defect. `depends_on` still lists the constitution sections the epic slices, because those exist. A story minted at `change` or `hotfix` scope carries exactly one `provenance[]` entry, its epic anchor, and no PRD entry, because there is no requirement anchor to name; `references/stories.md` states that, and `check_story.py` checks presence of the key rather than a fixed entry count. |
| `--scope` has nowhere to go in the epic frontmatter | `03-brownfield.md` says the scope is recorded in state and in the artifact frontmatter, but the `epic` template has no `scope` key and `devforgeai phase start` accepts no flag but `--lenient`, so the value cannot reach `state.yaml` either | The story's `scope` frontmatter key is the machine-readable home, and it is present on every story. The epic records the same value as the first line of its `## Scope` section, in the form `Scope: change`, so a reader and `check_epic.py` can both find it. `/analyze` reads the story frontmatter. This spec does not claim the value reaches `state.yaml`. |
| `--scope hotfix` skips epics and sprints | `03-brownfield.md` says hotfix skips brainstorm, pm, architect and epics, but the `epics` and `sprints` phases both declare `writes: docs` and owe an artifact | Hotfix skips epic decomposition, not the epic file. `epic_writer` writes one `EPIC-000.md` recording the intent, and `sprint_writer` writes `sprint-001.md` holding the single story, so both phases satisfy their `document` oracle. The story's `sprint` value therefore names `sprint-001` rather than being null, which is where this spec parts company with the `sprint: null for scope: hotfix` comment in `templates/story.md`. That comment is the divergence; the oracle is the mechanism. |
| A `hotfix` story loosens a gate policy class | `gate_policy.unresolvable_source: WARN` is legal only at `hotfix` scope; declaring it at any other scope is itself a gate defect that refuses the run | `story_writer` writes `BLOCK` for every class at `feature` and `change` scope, and may write `WARN` for `unresolvable_source` only when `scope` is `hotfix`. `references/stories.md` states the rule and `check_story.py` checks it, because a story that loosened the wrong class would be refused at `dev`'s gate rather than at this one. |
| An `L` story reaches a sprint | `estimator` flags it, but nothing stops `sprint_writer` from scheduling it | `estimator` returns an issue row per `L` story naming the split it needs, and `plan_critic` reports a scheduled `L` as a defect. Nothing deterministic refuses it: the size band is a model judgement, so this is guidance backed by a critic row, not a gate. Recorded so the limit is visible rather than implied. |
| Two `plan` runs over the same slug | A second run's candidate root is cut from the canonical HEAD, so a story `/clarify` changed since the first run is in the root as the human left it | Each writer edits the file where it stands in the root, so a hand-edited story is carried forward rather than replaced. Where two runs genuinely overlap, `FENCE_OVERLAP` refuses the second at `phase start`, and where canonical HEAD moved under a run, promotion refuses `STALE_BASE` and the sequencer rebases and reruns the last oracle before retrying. |
| A plan larger than sixty-four files | The receipt caps `claimed_paths` at 64 entries, and a change the receipt did not claim refuses the whole result as `UNCLAIMED_CHANGE`. One phase is one receipt, with no batching operation in the grammar, so the `stories` phase cannot write more than 64 stories and the `sprints` phase cannot write more than 64 sprint files and stamped stories together | The cap is a real ceiling, not a guideline, and this spec does not describe a plan above it as writable. The fix is in the receipt contract: raise the `claimed_paths` cap, or add a batching operation that lets one phase checkpoint several receipts under one transition. Until then a project above the ceiling is split into two slugs, each with its own `docs/plan/<slug>/` fence and its own run, and `/analyze` walks each separately. `references/stories.md` states the ceiling so `story_writer` stops at it and reports the remainder as an `issues` row rather than writing files it cannot claim. The same cap applies to `architect`'s `design` and `adr` phases, where it is unlikely to bite. |
| The candidate root and the primary window | A worker cannot resolve `candidate.root` from the canonical tree, and pasting artifact content into a dispatch is the restatement the anti-ceremony rules forbid | Every anatomy run gets one candidate root, opened by `phase start` and owned by the sequencer until promotion or abandonment; the primary window stays in the canonical checkout. The one thing a dispatch carries beyond paths, ids and the scope and flag tokens is the `devforgeai status` block, which names `run`, `candidate.root`, `phase`, `fence` and `granted_keys`. It is generated, not composed, and it is the only sanctioned paste. Claude's own worktree isolation setting and `EnterWorktree` are not used: they fork from HEAD and would split the run's linear history |
| The receipt no longer carries an `evidence` object | Earlier drafts gave the phases `evidence.epics`, `evidence.stories`, `evidence.specs`, `evidence.order`, `evidence.sizes`, `evidence.sprints` and `evidence.coverage`, and made `dependencies` and `estimates` return their rows for `sprint_writer` to apply | The two ordering phases now write their keys into the stories themselves, under the `writes: fields` restriction, so `blocked_by` and `size` live where every consumer already reads them. Every other row has a home in the artifact its phase wrote. `evidence_refs` points at those files, `note` carries the counts and the per-edge reasons, and `plan_critic` writes its findings file into its own run-scoped evidence directory. |
| A monorepo with two package managers | A story can pin only one `stack.yaml` anchor, so a story spanning two ecosystems cannot express its commands | `story_writer` writes one anchor per story and splits work that spans two ecosystems into two stories. Cross-package stories are out of scope; the deferred contract is `12-post-mvp.md#pm-09`. |
| An earlier draft said promotion is the last thing the run does and that `devforgeai phase next` merges the candidate root | An author compiles a `SKILL.md` that never asks the user, and the run's files land in the canonical checkout without a human decision | Promotion is never automatic. The last passing transition sets `runs.<run>.status: ready_to_promote` and writes a `REQUIRE_HUMAN` handoff whose only forward step is `devforgeai promote <run>`; the compiled `SKILL.md` runs that command only after the user confirms in the session, and that command writes the second handoff block, whose `next` is the section 7e row for the run's outcome. Every run ends in two blocks, not one, and `STALE_BASE`, `DIRTY_TARGET` and `MERGE_CONFLICT` are refusals of `devforgeai promote <run>` that leave the run `ready_to_promote` with its root intact, never refusals of `devforgeai phase next`. **Decision (D7, as amended; `10-sequencer-and-contracts.md` sections 5.4, 6 and 12.4):** the sequencer may not close a run onto the canonical tree on its own. |
| An earlier draft said a `REQUIRE_HUMAN` block closes the run, so "no flag resumes a closed one" | An author writes a repair route that opens a fresh run, and `devforgeai phase start` refuses it — the blocked run is still `active` — or writes `devforgeai phase fail --reason <text>` into every recovery row and throws away work the run had already checkpointed | A block is not a close. A `needs_user` result and an exhausted attempt budget both leave the run `active` with its lease released, its candidate root and checkpoints on disk, and `run.yaml#blocked_at` naming the phase. `devforgeai phase start` with the same skill and the same argument **resumes** that run at `blocked_at` with `attempts` reset to zero instead of refusing it, so `/plan {slug}` is the whole recovery once the human has acted. Only another skill on the same story needs `devforgeai phase fail --reason <text>` first, and that call is what abandons the root. **Decision (`10-sequencer-and-contracts.md` sections 2, 3, 5.4 and 6):** blocked runs resume; they are not reopened. |
| An earlier section 7e row said an exhausted attempt budget closes the run and abandons its candidate root | An author promises that nothing survives a block, so a recovery route re-runs every phase from the start and the checkpoints the run had already earned are discarded | An attempt-limit block leaves the run `active` with its lease released and its root and every checkpoint on disk; `run.yaml#blocked_at` names the phase. Only `devforgeai phase fail --reason <text>` abandons the root, and only `devforgeai promote <run>` moves a byte into the canonical tree, so a blocked run has changed nothing canonical either way. **Decision (`10-sequencer-and-contracts.md` section 5.4):** blocked is `active`, not closed. |

## 10. Success criteria and test cases

### Success criteria

- Triggers on the section 4 positives and on none of the near-misses.
- Every story the run applies passes `python3 scripts/check_story.py <path>` once the sequencer has resolved the `sha256:PENDING` digests OI-11 names.
- Every acceptance criterion in every story has exactly one `test_plan` row, and every `test_plan` row's `file` is inside that story's `write_fence`.
- Every story's `commands.source` names an anchor that exists in `.devforgeai/stack.yaml`, and `commands.use` names keys only, with no literal command anywhere in the file.
- Every sprint's `stories` list places each story after every story in its `blocked_by`.
- Every phase's `changed` set is a subset of its `claimed_paths` and lies inside `docs/plan/<slug>/`, and the `critic` phase changes nothing inside the candidate root.
- The `dependencies` and `estimates` phases change only `blocked_by` and `size` on existing story files, with every body byte identical.
- The primary window's transcript shows no read of the PRD, the constitution set or any produced artifact, and no Bash call outside `devforgeai status | phase start | phase fail --reason | validate | promote`.

### Fixture

`docs/design/examples/fixtures/plan/` is the base fixture. Its exact tree:

| Path | Contents |
|---|---|
| `.devforgeai/state.yaml` | canonical state: `version: 1`, `target: [claude]`, `mode: greenfield`, `slug: tinyapp`, `phase: plan`, `phases.pm.status: done` and `phases.architect.status: done` with their artifact paths and real digests, an empty `stories` mapping, and a `runs` mapping with one key `plan-tinyapp` whose value carries `skill: plan`, `mode: copy`, `root: .`, `base_ref: fixture`, `checkpoint: base` and `status: active` |
| `.devforgeai/work/plan-tinyapp/run.yaml` | the per-run enforcement file, standing in for what `devforgeai phase start` writes: `canonical: .`, `phase: epics`, `fence: [docs/plan/tinyapp/**]`, `granted_keys: []`, `attempts` and `max_attempts` at 2 for the seven phases, `gate_policy: {unresolvable_source: BLOCK}`, and a `lease` naming the eval session. The fixture copy is the candidate root, so `candidate.mode` is `copy` and `candidate.root` is the copy itself |
| `.devforgeai/stack.yaml` | one anchor, `python`, copied verbatim from `docs/design/examples/hooks/fixtures/.devforgeai/stack.yaml`, so `compiled` is false, `test` and `lint` keys exist, and `test` carries a `junit_path` |
| `.devforgeai/skills/dev/SKILL.md` | a one-line stub, present so `skill_spec_writer` can tell a skill that exists from one that does not |
| `docs/PM/tinyapp/prd.md` | a `prd` instance, `slug: tinyapp`, `status: approved`, three `REQ-NNN` rows under `## Requirements` — a slug helper, a punctuation rule, and a command-line entry point — with `## Goal`, `## Users`, `## Non-Goals` and `## Success Measures` each one paragraph |
| `docs/architecture/constitution.md` | a `constitution` instance with `## Principles`, `## Mandates`, `## Constraints` and `## Style`; `## Mandates` is a table with one row, `conventional-commits: required`, which names no skill |
| `docs/architecture/sourcetree.md` | a `sourcetree` instance, `mode: INTENDED`, with one `PATH-001` row placing the package at `tinyapp/` and tests at `tests/` |
| `docs/architecture/techstack.md` | a `techstack` instance, `mode: INTENDED`, `stack_section: python`, with `TS-001` naming Python and `TS-002` admitting only the standard library |
| `docs/architecture/architecture.md` | an `architecture` instance with one `COMP-001` row for the text module |
| `docs/architecture/design-language.md` | a `design` instance, `topic: language`, recording the language decision |
| `tinyapp/text.py` | a module with a docstring and no public function, so a story has an OBSERVED excerpt to pin |
| `tests/test_text.py` | one collected test asserting the module imports |

Overlays, copied over the base fixture after it is copied and before the prompt runs:

| Overlay | Change |
|---|---|
| `overlays/eval-2/docs/architecture/constitution.md` | the same constitution with a second `## Mandates` row, `tdd: required`, which names a skill the fixture's `.devforgeai/skills/` does not contain, so `skill_spec_writer` owes exactly one specification |
| `overlays/eval-3/.devforgeai/state.yaml` | the base canonical state file with `mode: brownfield` |
| `overlays/eval-3/tinyapp/text.py` | the module with a `slugify` function that crashes on a non-ASCII input, so the hotfix intent has a real defect to name |

Eval 1 has no overlay. Per-eval changes ship only as these overlay directories; no eval describes a fixture edit in prose.

### evals/evals.json (used verbatim)

```json
{
  "skill_name": "plan",
  "evals": [
    {
      "id": 1,
      "prompt": "Run plan on the tinyapp slug in this repository. The architecture set is finished; break it into epics, stories and sprints.",
      "expected_output": "Epics, stories and at least one sprint under docs/plan/tinyapp/, each story self-contained with a context bundle, a write fence, a stack reference and one test_plan row per criterion, and a handoff whose next steps name /analyze for the slug and then the first story.",
      "expectations": [
        "At least one file exists under docs/plan/tinyapp/epics/ and its frontmatter carries the keys id, slug, template, template_version, status, risk_tier, provenance and depends_on",
        "Every file under docs/plan/tinyapp/stories/ has template_version 3 and all eighteen required frontmatter keys",
        "In every story the number of test_plan rows equals the number of numbered acceptance criteria, and every test_plan file path also appears in that story's write_fence",
        "Every story's commands.source names the anchor python and commands.use lists only key names, with no executable name or command flag anywhere in the file",
        "At least one file exists under docs/plan/tinyapp/sprints/ and every story it lists appears after every story in that story's blocked_by",
        "No file was created or modified outside docs/plan/tinyapp/",
        "Every story that any sprint schedules carries a sprint frontmatter value, and every story blocked by another carries it in blocked_by",
        "The final message contains a handoff block whose next step 1 begins with /analyze and whose next step 2 begins with /dev STORY-"
      ]
    },
    {
      "id": 2,
      "prompt": "Run plan on tinyapp. The constitution now mandates tdd.",
      "expected_output": "As eval 1, plus exactly one skill specification under docs/plan/tinyapp/skill-specs/ for the skill the tdd mandate names, and a handoff that asks for it to be generated before the first story.",
      "expectations": [
        "Exactly one file exists under docs/plan/tinyapp/skill-specs/ and its id matches the SKILL-SPEC pattern",
        "That file contains all sixteen numbered section headings in order and its frontmatter status is approved",
        "At least one story's requires_skill value names the skill that specification describes",
        "The final message contains a handoff block whose next steps include a skill-gen command naming that specification's skill_name before the first dev command"
      ]
    },
    {
      "id": 3,
      "prompt": "Run plan on tinyapp with scope hotfix. The intent is: slugify crashes on a non-ASCII title and must return a usable slug instead.",
      "expected_output": "One epic recording the intent, exactly one hotfix story with an Unchanged Behaviour section, one sprint holding it, and a handoff whose first next step names that story.",
      "expectations": [
        "Exactly one file exists under docs/plan/tinyapp/stories/ and its id matches the hotfix story pattern",
        "That story's scope frontmatter value is hotfix and its Unchanged Behaviour section is not the word None",
        "Exactly one file exists under docs/plan/tinyapp/epics/ and its Scope section's first line records the hotfix scope",
        "Exactly one file exists under docs/plan/tinyapp/sprints/ and it lists that one story",
        "The final message contains a handoff block whose next step 1 names the hotfix story"
      ]
    }
  ]
}
```

Quick-mode results are generation feedback only: one enabled run per eval and no baseline. They are not runtime conformance evidence, and no section of this spec gates on such evidence; the deferred contract is `12-post-mvp.md#pm-02`.

## 11. Dependencies and compatibility

| Kind | Value |
|------|-------|
| Tools | SKILL.md: `Read`, `Agent`, and a Bash grammar no wider than the five model-callable operations `devforgeai status \| phase start <skill> <arg> \| phase fail --reason \| validate \| promote <run>`. Document writers (`epic_writer`, `story_writer`, `skill_spec_writer`, `dependency_mapper`, `estimator`, `sprint_writer`): `Read`, `Grep`, `Glob`, `Bash(devforgeai status)` plus `Edit` and `Write`, which Codex serves as `apply_patch`, denied outside `candidate.root` and outside the phase's fence, and narrowed again to the field fence and the three keys for the two `writes: fields` phases. Judge (`plan_critic`): the same read set plus `Write` confined to `.devforgeai/work/<run>/evidence/<agent>/`. No `plan` phase grants a stack command key, so no worker carries `Bash(devforgeai run *)`. |
| MCP servers | none |
| Runtime | Python 3.11+ for the four bundled scripts; PyYAML 6+ for frontmatter and `stack.yaml` parsing. Worktree mode additionally requires `git` with at least one commit on the project; without it the run falls back to copy mode |
| Project commands | none brokered. No `plan` phase declares a `run_keys` entry, so this run brokers no command and its run file carries `granted_keys: []`. Every story this skill writes names the `test` key, and `lint` where the pinned section defines it, through `commands.use`; `build` is required in that list when the pinned section has `compiled: true`. Keys are named, never a literal command; the sequencer resolves them from the hash-pinned section. Contract: `10-sequencer-and-contracts.md` section 7. |
| DevForgeAI/Core compatibility | `NOT_APPLICABLE`. `plan` is an anatomy-governed skill, not a Research Core adapter, and names no Research Core version. |
| Other skills | Upstream: `pm` (`prd`), `architect` (`constitution`, `sourcetree`, `techstack`, `architecture`, `design`, `stack`), `analyze` (`analyze-report`), `amend` (`impact-report`), `retro` (`retro-report`). Downstream: `dev`, `clarify`, `review`, `qa`, `analyze`, `skill-generator`, `skill-validator`, `retro`. Calls none: every edge is a handoff row (open item OI-7). Sole owner of the `epic`, `story`, `sprint` and `skill-spec` templates; `architect` writes mandates and nothing else about skills. |

Deferred dependencies, each naming its `12-post-mvp.md` entry and what the skill does today without it:

| Deferred item | What `plan` does today |
|---|---|
| `12-post-mvp.md#pm-01` | `isolation: required` on five of the seven workers is the DevForgeAI contract value compiled into the target profile, not Claude's `isolation` frontmatter field. Nothing verifies at runtime that a worker ran in its own window, and the generated adapter is an uninstalled candidate a human accepts. |
| `12-post-mvp.md#pm-04` | A worker's write boundary is the dispatcher's `PreToolUse` deny plus the candidate root, not an operating-system boundary. |
| `12-post-mvp.md#pm-02` | Quick-mode eval results are generation feedback. No success criterion in section 10 is presented as conformance evidence. |
| `12-post-mvp.md#pm-06` | Only `skip` and `quick` eval modes exist. Section 0 rule 5 rejects any third mode name as a spec defect. |
| `12-post-mvp.md#pm-08` | A story is never sliced from a document produced by an earlier DevForgeAI version; such a document is treated as any other non-DevForgeAI source and is cited, not migrated. |
| `12-post-mvp.md#pm-09` | One story pins one `stack.yaml` anchor. Work spanning two package ecosystems is split into two stories rather than expressed in one. |
| `12-post-mvp.md#pm-10` | Nothing re-walks the plan from a clean checkout, so a story edited outside a run is caught only when a gate re-resolves it or `/analyze` is run. |

Frontmatter values derived from this table:

```yaml
compatibility: "Requires Python 3.11+ and PyYAML for the four bundled scripts. Runs inside a repository that already has a .devforgeai/ directory, a stack section, and the INTENDED architecture set for the slug; outside one, devforgeai phase start refuses and the skill does nothing."
allowed-tools: "Read Agent Bash(devforgeai status) Bash(devforgeai phase start *) Bash(devforgeai phase fail *) Bash(devforgeai validate) Bash(devforgeai promote *)"
```

## 12. Targets

The generator produces one provider-neutral semantic package and a separate adapter for each selected target when frontmatter, invocation policy, or agent configuration differs. Provider-neutral resources may be shared. Adapter directories are not required to be byte-identical or symlinked.

| Target | Install path | Invocation | Subagents | Notes |
|--------|--------------|------------|-----------|-------|
| claude | `.claude/skills/plan/` | `/plan` with a slug, and an optional scope flag taking `feature`, `change` or `hotfix` | `.claude/agents/plan-<role>.md`: six document writers with `Edit` and `Write` confined to the candidate root, one judge whose `Write` reaches only its run-scoped evidence directory | Provider-specific frontmatter keys (`argument-hint`, `disable-model-invocation`) are compiled into this target's SKILL.md only. `hooks`, `memory`, `background`, `permissionMode` and Claude's own `isolation` are omitted from every profile. |
| codex | `.agents/skills/plan/` plus `.codex/agents/` profiles | `$plan` with a slug, and the same optional scope flag | `.codex/agents/plan-<role>.toml`: the same seven names, with `apply_patch` in place of `Edit` and `Write` | Portable six-field frontmatter only; policy goes in target-side configuration. |
| both | separate `.claude/skills/plan/` and `.agents/skills/plan/` adapters | as above | as above | Share only provider-neutral resources; validate each adapter independently. |

```yaml
metadata:
  version: "1.0.0"
  devforgeai-spec: "SKILL-SPEC-009"
  devforgeai-target: "both"
  devforgeai-anatomy: "true"
```

Not produced by skill-creator (deferred to DevForgeAI's skill-generator): provider-native `.claude/agents/*.md` and `.codex/agents/*.toml` worker profiles, provider-specific frontmatter keys for the Claude target, and concise `AGENTS.md` sections. Hook definitions are not per-skill: `init` installs the one dispatcher and its provider fragments from `09-hook-dispatcher.md`, and this spec ships none.

A generated package is an uninstalled candidate until those provider-native controls are present and independently validated. Generation or quick-mode success is not installation authority.

## 13. Constraints

- `SKILL.md` under 500 lines and roughly 5,000 tokens, holding only identity, the ordered phase list, the dispatch loop, and the handoff table. Every other instruction lives in `references/<phase>.md`, `agents/<role>.md`, `scripts/` or `assets/`. The `stories` phase's guidance is split across `references/stories.md` and `references/story-bundle.md` for that reason.
- References one level deep from whichever file is loaded: `SKILL.md` links to `references/`, `agents/`, `scripts/`, `assets/`; an `agents/*.md` may link to `references/*.md`. Nothing links further.
- Hooks, state writes and phase advancement are not in the skill. `SKILL.md` contains no instruction the gate, the fence or a transition oracle already carries.
- No `README.md` inside the skill directory.
- No XML angle brackets in frontmatter. Description 915 characters; name 4 characters.
- Imperative voice; each step states why it matters. No capitalised absolutes: where a rule is real it is a gate defect class, the fence, a `must_not` line, or an oracle condition, and the text names that mechanism.
- Provide defaults, not menus. `--scope` defaults to `feature`, and `gate_policy` defaults to `BLOCK` on every class the story template lists.
- Scripts take arguments, never prompt, and exit `0`, `1` or `2`.
- Skill-specific: no literal build, test, lint or format command appears in a story, in a reference file, or in a worker prompt. A story names keys through `commands.use` and pins the section by digest.
- Skill-specific: every artifact is written inside the run's candidate root and reaches the canonical checkout only at promotion. The `dependencies` and `estimates` phases change three frontmatter keys and no body byte, which is what makes their diff checkable.
- Skill-specific: a context excerpt is verbatim bytes from the range its anchor resolves to. Summarising an excerpt is the hallucination surface the bundle exists to remove, and `plan_critic`'s uncited-excerpt defect class is what reports it.

## 14. Acceptance checks

Run these before reporting done and paste their output:

```bash
# frontmatter and naming (skill-creator's own validator)
python -m scripts.quick_validate ./out/plan          # run from the skill-creator directory
# open-standard validator, if installed
skills-ref validate ./out/plan
# size budget
wc -l ./out/plan/SKILL.md                            # must be < 500
# every worker in section 7d has a prompt file, and no extra
ls ./out/plan/agents/                                # seven files, canonical registry names
# one reference file per phase, plus the story split and envelope.md
ls ./out/plan/references/                            # eight phase files plus envelope.md
# scripts answer --help and reject bad usage with exit 2
python3 ./out/plan/scripts/check_epic.py --help
python3 ./out/plan/scripts/check_story.py --help
python3 ./out/plan/scripts/check_skill_spec.py --help
python3 ./out/plan/scripts/check_sprint.py --help
# the shipped story skeleton carries every required key and section
python3 ./out/plan/scripts/check_story.py ./out/plan/assets/story.md --lenient --json
# no leftover placeholders
grep -rnE 'T[O]DO|T[B]D|\{\{' ./out/plan || echo clean
```

The skeleton check exits 1 on the empty values it ships with; its purpose is that the failure list names only empty values and never a missing key or a missing section.

Then the wave-4 battery over this specification:

```bash
python3 docs/design/specs/verify.py --only v1,v2,v4
```

For non-Research anatomy skills, DevForgeAI skill-validator additionally checks: all sub-phase kinds present with Gate, Record and Handoff bound to sequencer operations; persona and critic are different files, which for this skill are `epic_writer.md` and `plan_critic.md`; `must_not` present in every agent file; every agent declaring `writes: candidate` or `writes: evidence`, with a `writes: evidence` agent carrying no `Edit` and a `Write` fenced to its run-scoped evidence directory; the SKILL.md Bash grammar is no wider than the five model-callable operations; handoff outcomes cover every status the skill can return, including `could_not_run`.

## 15. Provenance

| Source | Hash | Used for |
|--------|------|----------|
| docs/design/01-skill-anatomy.md#primary-window-contract | see frontmatter | sections 7a, 7b, 10 |
| docs/design/01-skill-anatomy.md#dedicated-templates | see frontmatter | sections 6, 8 |
| docs/design/01-skill-anatomy.md#context-bundle-format | see frontmatter | sections 6, 7d, 9 |
| docs/design/10-sequencer-and-contracts.md#4-per-skill-phase-registry | see frontmatter | sections 7b, 7c, 7d |
| docs/design/10-sequencer-and-contracts.md#3-4-re-resolving-sources-and-the-one-downgrade | see frontmatter | sections 8, 9 (OI-11) |
| docs/design/10-sequencer-and-contracts.md#5-2-validation-order | see frontmatter | sections 7c, 9 |
| docs/design/10-sequencer-and-contracts.md#5-4-transition-oracles | see frontmatter | sections 2 (R5, R8), 7c, 9 |
| docs/design/10-sequencer-and-contracts.md#6-handoff-envelope | see frontmatter | sections 7a, 7e |
| docs/design/11-artifact-registry.md#1-template-registry | see frontmatter | section 6 |
| docs/design/11-artifact-registry.md#2-artifact-path-patterns | see frontmatter | sections 2 (R1), 6 |
| docs/design/11-artifact-registry.md#3-depends-on-edges | see frontmatter | sections 2 (R2), 6 |
| docs/design/02-skill-roster.md#plan | see frontmatter | sections 1, 5, 9 |
| docs/design/02-skill-roster.md#handoff-decision-tables | see frontmatter | section 7e |
| docs/design/05-subagent-sets.md#sets-per-skill | see frontmatter | sections 7d, 9 |
| docs/design/05-subagent-sets.md#contract-format | see frontmatter | section 7d |
| docs/design/06-skill-specification.md#where-the-spec-sits-in-the-pipeline | see frontmatter | sections 2 (R3), 7d |
| docs/design/03-brownfield.md#per-request-entry-with-scope | see frontmatter | sections 2 (R4), 5, 9 |
| docs/design/templates/story.md#acceptance-criteria | see frontmatter | sections 2 (R5, R7), 6 |
| docs/design/templates/story.md#verification | see frontmatter | section 6 |
| docs/design/07-purpose-and-enforcement.md#2-the-problem-in-concrete-terms | see frontmatter | section 2 |
| docs/design/12-post-mvp.md#pm-09 | see frontmatter | sections 9, 11 |
