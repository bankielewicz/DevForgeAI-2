---
template: skill-spec
template_version: 1
id: SKILL-SPEC-008
skill_name: architect
target: both
status: approved
author: "DevForgeAI wave-2 specification author"
date: 2026-09-02
depends_on:
  - source: docs/design/01-skill-anatomy.md#primary-window-contract
    hash: sha256:a6bbaf9af2d69f7ede18d7c40f242c42edb26d79be964ffec3f386d6347014c2
    excerpt: "**The model dispatches, the sequencer decides.** For an anatomy-governed skill, the primary window (provider entry adapter + skill orchestration) does light, trivial work only."
  - source: docs/design/01-skill-anatomy.md#dedicated-templates
    hash: sha256:55bd4a18d63e645adffa187d34256dc7db7370095dcbf9e96a190028f7e65a5e
    excerpt: "Every anatomy-governed non-Research skill owns its templates under `.devforgeai/skills/<name>/templates/`. No shared or generic template exists."
  - source: docs/design/01-skill-anatomy.md#context-bundle-format
    hash: sha256:7b068feb30e7cc2f66292b512ac179cd217df225fb58517d2aaadd30b25236dc
    excerpt: "A literal placeholder hash (`sha256:fixture...`, `sha256:PENDING`) is reported as `unresolvable-source`."
  - source: docs/design/01-skill-anatomy.md#provenance-chain
    hash: sha256:a972a34352485d39e86add257fad2a007e6241521b18234d152cd35888dbad25
    excerpt: "`adr/NNNN-*.md` — architecture decisions, appended by architect and amend."
  - source: docs/design/10-sequencer-and-contracts.md#4-per-skill-phase-registry
    hash: sha256:511733ee35ca74fd5a5c0b59f225d7d975788e7d43d939f44c23b7aa8460cff0
    excerpt: "| architect | 1 | `option_compare` | `option_comparer` | none | 2 | — | report_only | — |"
  - source: docs/design/10-sequencer-and-contracts.md#5-2-validation-order
    hash: sha256:9f1bf77b7e84302ff6f3f20260228d57390cc97ab8e8d3f68f52c3ff2658aab8
    excerpt: "| 10 | `changed[]` is a subset of `claimed_paths` | refuse, reason `UNCLAIMED_CHANGE`; this **is** a phase attempt, because real bytes were written outside the claim |"
  - source: docs/design/10-sequencer-and-contracts.md#5-4-transition-oracles
    hash: sha256:ffa41b5d270dc260e28fa9f6bdbc855069a6e922d1148c74b25860dba63484dc
    excerpt: "the phase declared `writes: docs` and `changed[]` is non-empty, unless it is marked conditional, in which case an empty change set needs a non-empty `note`; every changed path exists in the root with the bytes the checkpoint will hold"
  - source: docs/design/10-sequencer-and-contracts.md#7-stack-yaml
    hash: sha256:f51716b6cfb1f4a48f4efbcff03947b3adab879dac1b6de7720564c85c87c43c
    excerpt: "Producers: `architect`'s `techstack` phase emits the INTENDED sections beside `techstack.md`; `onboard`'s `code_map` phase emits the OBSERVED sections."
  - source: docs/design/10-sequencer-and-contracts.md#6-handoff-envelope
    hash: sha256:747b6340fc5c2348aad33ca5488012808670b3503b311d7b7d0f1204625afd4c
    excerpt: "`next` is never empty and is never a description. One exact command."
  - source: docs/design/11-artifact-registry.md#1-template-registry
    hash: sha256:09607ea79839ab215871d87e8221166e14eeb6ca26f8372e4ead4173f1d92907
    excerpt: "| `techstack` | `.devforgeai/skills/architect/templates/techstack.md` | 1 | `^TS-[0-9]{3}$` | slug, template, template_version, status, mode, depends_on, stack_section | Languages, Data Access, Testing, Build And Lint |"
  - source: docs/design/11-artifact-registry.md#2-artifact-path-patterns
    hash: sha256:2d2e97afff50edf6b35bf674b1de217c684d5091361e5f1deae12de52b95fb51
    excerpt: "| `docs/architecture/design-<topic>.md` | `design` | architect | sequencer |"
  - source: docs/design/11-artifact-registry.md#3-depends-on-edges
    hash: sha256:f3c304ff840d2027432f743288bccec0ea5bc5d7b99b7f41c8d524b1c3591da2
    excerpt: "| `constitution` | `docs/PM/<slug>/prd.md` sections; admitted `observed-constraints`; current source citations |"
  - source: docs/design/11-artifact-registry.md#6-known-divergences
    hash: sha256:8a78656458735ce54ac73010da3b8fc87bbb7017a5a9268f85b210249736b82a
    excerpt: "Recorded here so that no specification silently inherits them."
  - source: docs/design/02-skill-roster.md#architect
    hash: sha256:adfc9d770858e05efabc8973988c39f98f8ed9a3ede5f181dfa1eb6c964f0c0d
    excerpt: "- `--yolo`: option-comparer subagent selects best practices per decision and records each as an ADR with `ASSUMPTION` tags."
  - source: docs/design/02-skill-roster.md#handoff-decision-tables
    hash: sha256:1dac784b4670cc7559f323011dfe304dfe8c0baf349063162f90d76d902c5d3c
    excerpt: "| architect | pass | `/plan {slug}` |"
  - source: docs/design/05-subagent-sets.md#sets-per-skill
    hash: sha256:9e12f3beb236a025c18d40e741c09ba675bd71d2d87f56e2b205c7556b944bf9
    excerpt: "| architect | option-comparer (yolo) or decision-interviewer, constitution-writer (including `#mandates`), sourcetree-writer, techstack-writer (emits the INTENDED `stack.yaml`), architecture-writer, design-writer, adr-writer, gap-analyzer (brownfield), prototyper (optional), critic |"
  - source: docs/design/03-brownfield.md#observed-vs-intended
    hash: sha256:76cdea3c2760b31cc074204be8c244bffb3d582a0ceba60482aa525ce03194a8
    excerpt: "Every constitution section carries a status:"
  - source: docs/design/07-purpose-and-enforcement.md#2-the-problem-in-concrete-terms
    hash: sha256:aa195bc0696dcc9da2f3511b7e03bac418430231f83e3f2ced3f71a4fa585917
    excerpt: "| Invents requirements or scope | Codex corpus on hallucinated requirements; 59.4% of audited SWE-bench Verified tasks flawed"
  - source: docs/design/12-post-mvp.md#pm-09
    hash: sha256:d78bedbec92e8830c353a747f7b163b882d9ccd7d523a9e51df3d9cc56222829
    excerpt: "A monorepo runs today by pinning one section per story; cross-package stories are out of scope."
---

# Skill Specification: architect

A stranger with no conversation history must be able to build this skill from this document alone. Every question the generator would otherwise ask is answered below.

## 0. Generator instructions

These instructions are addressed to the skill-generating agent (Anthropic's `skill-creator` skill, or DevForgeAI's `skill-generator`). They replace its interview.

### Cold-session prompt

Paste this into a fresh session from the repository root:

```
Use the skill-creator skill to build the skill specified in docs/design/specs/SKILL-SPEC-008-architect.md.
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
6. **Output location** is given in the prompt. Create `./out/architect/`. Do not write anywhere else except the `architect-workspace/` sibling that eval runs require.
7. **On ambiguity, stop before output.** If the spec is still `draft`, contains an unresolved authoring assumption, omits a section, contradicts itself, or leaves a decision this document does not make, do not guess and do not write candidate skill files. End with a list titled `SPEC GAPS` naming each section and question. The spec author fixes and approves the spec before re-running.
8. **Fidelity over creativity.** Use the description in section 3 verbatim. Use the worker contracts in section 7d verbatim as `agents/<role>.md` bodies, adding only the framing the grader agent in skill-creator uses (Role, Inputs, Process, Output). Do not add steps, tools, or behaviours the spec does not mention.
9. **Finish with the acceptance checks** in section 14 and include their output in your final message.

## 1. Identity

| Field | Value |
|-------|-------|
| name | `architect` (kebab-case, 9 characters, equals the directory name, no `claude`/`anthropic` prefix) |
| title | Intended Architecture Authoring |
| purpose | Turn one approved PRD into the INTENDED constitution set — constitution, sourcetree, techstack, architecture, per-topic design documents, ADRs and the machine-readable `stack.yaml` section — so that every later phase has one binding, hash-addressable source for what the project is allowed to be. |
| category | devforgeai-phase |
| version | 1.0.0 (skill-package version written to `metadata.version`; not the DevForgeAI or Research Core version) |

## 2. Problem and requirements

**Without this skill:** an agent asked to build from a PRD invents the architecture as it goes. `07-purpose-and-enforcement.md` section 2 records the two consequences with evidence. The "invents requirements or scope" row is the first: the choice of database, test runner or module layout is made inside a story, in one window, and is never written down, so the next story makes a different choice and neither is wrong against anything. The "gate is prose the model may ignore" row is the second: where a project does write an architecture document, nothing binds a later phase to it, because no digest pins the section a story claims to follow and no command list constrains what the agent may run. The visible symptom is a repository with an ORM in one module and hand-written SQL in another, a `docs/architecture/` directory that describes neither, and no record of who decided what or when.

| ID | Kind | Requirement |
|----|------|-------------|
| R1 | explicit | Take one project slug and produce the INTENDED constitution set at the registry's paths: `docs/architecture/constitution.md`, `sourcetree.md`, `techstack.md`, `architecture.md` and one `design-<topic>.md` per decided topic. Source: `11-artifact-registry.md` section 2. |
| R2 | explicit | Record every architecture decision as an ADR with its context, the options compared, and the consequences, so `amend`, `analyze`, `review` and `retro` can cite it. Source: `11-artifact-registry.md` section 3. |
| R3 | explicit | Emit the INTENDED `stack.yaml` section beside `techstack.md`, so the sequencer can broker build, test, lint and format commands by key and the hook layer can refuse anything else. Source: `10-sequencer-and-contracts.md` section 7. |
| R4 | explicit | `--yolo` chooses a defensible option per decision without a human round-trip and records each choice as an ADR. Source: `02-skill-roster.md#architect`. |
| R5 | implicit | Write mandates, and nothing else about skills, into `constitution.md#mandates`. `plan` is the sole owner of the skill-spec template; `architect` has no `mandate_specs` phase and no fence entry under `docs/plan/`. Source: `10-sequencer-and-contracts.md` section 4. |
| R6 | implicit | Every INTENDED section carries `depends_on` entries naming the PRD requirement anchors and, on brownfield, the admitted OBSERVED constraint sections it was written against, so `drift` and `amend` can detect staleness. Source: `11-artifact-registry.md` section 3. |
| R7 | implicit | Describe the target, not the present. OBSERVED material is advisory; INTENDED binds `dev`, `review` and `qa`. A brownfield gap becomes an evidenced migration epic, never a rewrite of the OBSERVED record. Source: `03-brownfield.md#observed-vs-intended`. |
| R8 | discovered | `.devforgeai/stack.yaml` is a producer exception to the sequencer-owned deny list, and only the `techstack` phase of this skill and the `code_map` phase of `onboard` may write it. It is written inside the candidate root and reaches canonical by promotion; every other `architect` phase is refused the path. Source: `examples/hooks/policy.py` `PRODUCER_EXCEPTIONS`. |
| R9 | discovered | `.devforgeai/provenance/adr/**` is the second producer exception, declared for `architect`/`adr` and `amend`/`adr`. The `adr` phase writes `NNNN-<slug>.md` files inside the candidate root; the sequencer validates each against the `adr` template header and the filename shape before checkpointing, never overwrites an existing ADR, and provides no rewind for the path. Both exception paths count as fence members, so `FENCE_OVERLAP` refuses a second run that holds either. Source: `examples/hooks/policy.py` `PRODUCER_EXCEPTIONS`, `AUTHOR-BRIEF.md` open item OI-6. |
| R10 | discovered | The registry gives `architect` nine phases and no `prototyper` and no `decision-interviewer`, though `02-skill-roster.md` and `05-subagent-sets.md` name both. Section 9 records which survive. Source: `10-sequencer-and-contracts.md` section 4. |

## 3. Description

```yaml
description: >
  Turn an approved PRD into the binding architecture set for one project: a constitution with
  its mandates, a source tree, a tech stack with its machine-readable command section, a
  component architecture, one design document per decision, and an ADR for every choice made.
  Use this skill after pm has written a PRD, when someone asks how a project should be
  structured, which database or test runner to standardise on, where code should live, what
  the coding rules are, or asks to set the ground rules, tech stack or conventions before any
  code is written; use it with the yolo flag to have each decision chosen and recorded without
  a round trip. Do NOT use it to write epics, stories or skill specs (use plan), to change an
  architecture document that already exists (use amend), to describe what a codebase already
  does (use onboard), or to report where docs and code have diverged (use drift).
```

Character count: 893 / 1024.

## 4. Trigger set

```json
[
  {"query": "/architect shop", "should_trigger": true},
  {"query": "the PRD for the billing project is approved, set up the architecture", "should_trigger": true},
  {"query": "we need to decide postgres vs sqlite and where the modules live before anyone writes code", "should_trigger": true},
  {"query": "/architect tinyapp --yolo, just pick sensible defaults and write it all down", "should_trigger": true},
  {"query": "write the ground rules for this project: test runner, lint config, folder layout, and no ORM", "should_trigger": true},
  {"query": "pm finished docs/PM/shop/prd.md, what is the next phase", "should_trigger": true},
  {"query": "our team keeps arguing about layering. can you settle it and record the decision as an ADR", "should_trigger": true},
  {"query": "onboard wrote the OBSERVED sections for the legacy api, now define what it should become", "should_trigger": true},
  {"query": "i need a constitution.md with mandates for this repo, tdd required and conventional commits", "should_trigger": true},
  {"query": "set up stack.yaml so the hooks know which test command is allowed", "should_trigger": true},
  {"query": "split the PRD into epics and stories for sprint one", "should_trigger": false},
  {"query": "the constitution says Dapper but we want EF now, change it", "should_trigger": false},
  {"query": "map what this existing codebase actually does, nobody documented it", "should_trigger": false},
  {"query": "check whether the architecture doc still matches the code", "should_trigger": false},
  {"query": "implement STORY-004 following the architecture doc", "should_trigger": false},
  {"query": "review this PR against our coding standards", "should_trigger": false},
  {"query": "brainstorm some ideas for what this product could do", "should_trigger": false},
  {"query": "write me a blog post explaining hexagonal architecture", "should_trigger": false},
  {"query": "generate the tdd skill the constitution mandate asks for", "should_trigger": false},
  {"query": "our pytest suite is slow, profile it and suggest fixes", "should_trigger": false}
]
```

## 5. Use cases

### UC-1: Greenfield, decisions chosen without a round trip
- **User says:** "/architect shop --yolo"
- **Steps:** 1. `devforgeai phase start architect shop` runs the document fence gate and opens the run. 2. `option_comparer` reads `docs/PM/shop/prd.md`, lists one decision area per requirement cluster, compares at least two admissible options each, selects one, and writes the selections into its run-scoped evidence directory. 3. `constitution_writer` writes `docs/architecture/constitution.md` with Principles, Mandates, Constraints and Style inside the candidate root. 4. `sourcetree_writer`, `techstack_writer`, `architecture_writer` and `design_writer` write their documents in turn; `techstack_writer` writes `.devforgeai/stack.yaml` alongside `techstack.md`. 5. `adr_writer` writes one ADR per decision under `.devforgeai/provenance/adr/`. 6. `gap_analyzer` returns zero rows on greenfield. 7. `architect_critic` checks every section against the PRD anchors it claims.
- **Result:** after promotion, five architecture documents on disk, a `stack.yaml` section named by `techstack.md`'s `stack_section` key, one ADR per decision, and a handoff whose first next step is `/plan shop`.

### UC-2: Brownfield, an evidenced migration gap
- **User says:** "onboard wrote the OBSERVED sections for the legacy api, now define what it should become"
- **Steps:** 1. The gate opens the run over slug `api`. 2. `option_comparer` reads the PRD and the OBSERVED sections `onboard` admitted into `sourcetree.md`, `techstack.md` and `architecture.md`. 3. The writer phases write the INTENDED sections beside the OBSERVED ones inside the candidate root, each carrying `mode: INTENDED` and `depends_on` entries for the PRD anchors it used. 4. `gap_analyzer` compares the INTENDED sections against the OBSERVED constraints that actually exist and writes one section per evidenced difference into its run-scoped evidence directory, each citing the OBSERVED anchor and the INTENDED anchor. 5. `architect_critic` rejects any gap row with no OBSERVED citation.
- **Result:** both records coexist in the same three files, the gap rows are in `.devforgeai/work/architect-api/gap_analysis-result.json` and its evidence directory for `plan` to turn into a migration epic, and the handoff's first next step is `/plan api`.

### UC-3: Interactive, a decision the skill will not make
- **User says:** "/architect shop"
- **Steps:** 1. The gate opens the run. 2. `option_comparer` finds a decision area where the PRD admits two options and neither is defensible from the PRD alone, and returns `status: needs_user` with one `issues` row per such area and an empty `claimed_paths`. 3. The sequencer writes a `REQUIRE_HUMAN` handoff immediately, without consulting the attempt counter, and closes the run.
- **Result:** no architecture document is written, the open decisions are listed in the handoff with the PRD anchor each one turns on, and the next steps say to record the decision as a `REQ-NNN` row in `docs/PM/shop/prd.md` and then re-run.

## 6. Inputs and outputs

### Inputs
| Input | Format | Example file | Required |
|-------|--------|--------------|----------|
| project slug | positional argument, kebab-case | `shop` | yes |
| `--yolo` flag | boolean; selects the choose-and-record path in `option_comparer` | not a file | no |
| PRD | markdown with frontmatter, `prd` template, owned by `pm` at `.devforgeai/skills/pm/templates/prd.md` | `docs/design/examples/fixtures/architect/docs/PM/tinyapp/prd.md` | yes |
| OBSERVED constraint sections | markdown sections inside `sourcetree.md`, `techstack.md`, `architecture.md`, `observed-constraints` template, owned by `onboard` | `docs/design/examples/fixtures/architect/docs/architecture/techstack.md` | brownfield only |
| drift report | markdown, `drift-report` template, owned by `drift` | `docs/reports/drift-<slug>.md` | no |
| run file and context bundle | YAML and JSON, written by the sequencer at `devforgeai phase start` | `.devforgeai/work/<run>/run.yaml`, `.devforgeai/work/<run>/context.json` | yes; the run's fence, its granted keys and its candidate root come from the `devforgeai status` block the primary pastes into each dispatch |

### Outputs
| Output | Format | Location | Template |
|--------|--------|----------|----------|
| constitution | markdown | `docs/architecture/constitution.md` | `constitution`, seeded by `assets/constitution.md` |
| source tree | markdown | `docs/architecture/sourcetree.md` | `sourcetree`, seeded by `assets/sourcetree.md` |
| tech stack | markdown | `docs/architecture/techstack.md` | `techstack`, seeded by `assets/techstack.md` |
| architecture | markdown | `docs/architecture/architecture.md` | `architecture`, seeded by `assets/architecture.md` |
| design documents | markdown, one per topic | `docs/architecture/design-<topic>.md` | `design`, seeded by `assets/design.md` |
| stack section | YAML | `.devforgeai/stack.yaml` | `stack`, seeded by `assets/stack.yaml` |
| ADRs | markdown, one per decision | `.devforgeai/provenance/adr/NNNN-<slug>.md` | `adr`, seeded by `assets/adr.md`; written inside the candidate root under the producer exception and promoted with the run |
| phase results | JSON, written by the sequencer | `.devforgeai/work/architect-<slug>/<phase>-result.json` | none |
| phase reports | markdown, written by the sequencer | `.devforgeai/work/architect-<slug>/<phase>-report.md` and `docs/reports/architect-architect-<slug>-<phase>.md` | none |
| handoff | JSON plus its rendering | `.devforgeai/work/architect-<slug>/handoff.json` | `handoff` |

Template header keys, from `11-artifact-registry.md` section 1, are what the consuming skill's gate reads:

| Template | `id_pattern` | `required_frontmatter` | `required_sections` |
|---|---|---|---|
| `constitution` | `^SEC-[0-9]{3}$` | slug, template, template_version, status, provenance, depends_on | Principles, Mandates, Constraints, Style |
| `sourcetree` | `^PATH-[0-9]{3}$` | slug, template, template_version, status, mode, depends_on | Layout, Ownership, Naming |
| `techstack` | `^TS-[0-9]{3}$` | slug, template, template_version, status, mode, depends_on, stack_section | Languages, Data Access, Testing, Build And Lint |
| `architecture` | `^COMP-[0-9]{3}$` | slug, template, template_version, status, depends_on | Components, Interfaces, Data Flow, Failure Modes |
| `design` | `^DES-[0-9]{3}$` | slug, topic, template, template_version, status, depends_on | Decision, Options, Consequences, Interfaces |
| `adr` | `^ADR-[0-9]{4}$` | id, template, template_version, status, date, supersedes, depends_on | Context, Decision, Consequences, Alternatives |
| `stack` | anchor names match `^[a-z][a-z0-9-]*$` | version, compiled, package_manager, manifests, commands, test_glob, test_layout, runner_probe, packages, extractors, forbidden_imports | not a Markdown artifact; the section contract is `10-sequencer-and-contracts.md` section 7 |

`forbidden_text` carries the same five entries on every one of them — the two words meaning "not written yet", the opening and closing double-brace placeholder markers, and the angle-bracketed fill-in marker, listed verbatim in `11-artifact-registry.md` section 1. Every `template_version` is 1.

### Output template

`techstack.md`, the document that carries the machine-readable section name, is the shape all five follow:

````
---
slug: shop
template: techstack
template_version: 1
status: INTENDED
mode: INTENDED
stack_section: python
depends_on:
  - source: docs/PM/shop/prd.md#requirements
    hash: sha256:0000000000000000000000000000000000000000000000000000000000000000
    excerpt: |
      REQ-004 The service stores orders durably and survives a restart.
---

# Tech Stack: shop

## Languages

TS-001 Python 3.11 is the only implementation language. Rationale and alternatives are in
`docs/architecture/design-language.md`.

## Data Access

TS-002 Orders are read and written through the standard library sqlite3 driver. No
object-relational mapper is admitted; `.devforgeai/stack.yaml#python` refuses the packages
by name and refuses the imports by path.

## Testing

TS-003 Tests live under the path the source tree names and run through the `test` command
key of `.devforgeai/stack.yaml#python`.

## Build And Lint

TS-004 The section is not compiled, so no `build` key is defined. The `lint` key is defined
and the refactor transition requires it to exit zero.
````

The `stack.yaml` section `techstack.md` names, written by the same phase:

````
```yaml
python:
  version: 1
  compiled: false
  package_manager: pip
  manifests: [pyproject.toml, "requirements*.txt"]
  commands:
    test:
      argv: [python3, -m, pytest, -q, --junitxml=.devforgeai/work/junit.xml]
      junit_path: .devforgeai/work/junit.xml
      timeout_s: 600
    lint:
      argv: [python3, -m, ruff, check, .]
  test_glob: "tests/**/test_*.py"
  test_layout: "tests mirror the package tree"
  runner_probe: {argv: [python3, -m, pytest, --version], exit_ok: 0}
  packages:
    allow: [pytest, ruff, pyyaml]
    deny: ["(?i)sqlalchemy", "(?i)django"]
  extractors:
    - {paths: [pyproject.toml], regex: "^\\s*\"?([A-Za-z0-9_.-]+)"}
  forbidden_imports:
    - paths: ["shop/**"]
      patterns: ["^\\s*import\\s+sqlalchemy"]
      reason: "techstack.md#data-access admits only the standard library sqlite3 driver"
```
````

`commands.<key>.argv` is exec form, launched without a shell, so no redirect, pipeline, substitution or variable is interpreted. `build` is required when `compiled` is `true`.

### Return envelope (DevForgeAI-anatomy skills only)

One schema, both providers: `devforgeai.worker-result/v1`, normative in `schemas/devforgeai/v1/worker-result.schema.json`. A worker's final message is exactly this object, with no Markdown fence and no surrounding prose. A document writer has already written its files inside the candidate root when it returns; the receipt claims what it wrote. `option_comparer`, `gap_analyzer` and `architect_critic` write nothing and claim nothing.

```yaml
schema: devforgeai.worker-result/v1
run: "architect-shop"
skill: "architect"
phase: "techstack"
agent: "techstack_writer"
status: pass | fail | needs_user | could_not_run
reason_code: runner_missing | timeout | network | hook_fault   # required only when status is could_not_run
candidate: {id: "architect-shop", input_checkpoint: "sourcetree"}
claimed_paths: ["docs/architecture/techstack.md", ".devforgeai/stack.yaml"]   # at most 64; empty on any non-pass status
evidence_refs: ["docs/architecture/techstack.md", ".devforgeai/stack.yaml"]   # at most 16
note: "techstack.md written and the python stack section added"
issues: [{id, kind, text}]                                                    # at most 10
```

At `devforgeai ingest-result` the sequencer derives `changed[{path, blob_sha256, kind}]` from the checkpoint diff, refuses when `changed` is not a subset of `claimed_paths` (`UNCLAIMED_CHANGE`) or a path is outside the fence, validates each written file against its template header, runs the transition oracle inside the root, writes `<phase>-result.json` with `changed` and the checkpoint ref, releases the lease and advances. `next` requires `status: fail` plus a registry `rewind_to`; no architect phase declares one, so the key is never present. Unknown keys refuse the receipt.

`gate_policy` (`BLOCK | REQUIRE_HUMAN | WARN | OFF`) is a defect-to-action map declared in the consumed artifact, never a status returned here. `architect` is a plain document run, so it carries the fixed map `{unresolvable_source: BLOCK}`.

## 7. Procedure

### 7a. Steps

The body of `SKILL.md`. Imperative voice; each step says why it matters.

1. Parse the positional slug and the optional `--yolo` flag. Read nothing else in this window — why: anything read here stays in the primary window for the whole run, and the primary-window contract forbids opening an artifact at all.
2. Call `devforgeai phase start architect <slug>`. On exit 1, print the defect list the gate wrote to stderr and stop — why: the gate opens the candidate root every later phase writes into, so a refusal leaves nothing half-written.
2a. Run `devforgeai status` and paste its block into every dispatch below. The block names `run`, `candidate.root`, `phase`, `fence` and `granted_keys` — why: a worker writes inside the candidate root and cannot resolve it from the canonical tree, and this block is the one thing a dispatch carries that is not a path or an id.
3. Dispatch `agents/option_comparer.md` with the status block, the PRD path, the three architecture document paths, and the `--yolo` flag token. Pass paths, the flag token and the block only — why: pasting a requirement into the prompt puts the PRD's text in two places and the worker reads the file itself.
4. Dispatch the five writer workers in registry order — `constitution_writer`, `sourcetree_writer`, `techstack_writer`, `architecture_writer`, `design_writer` — each with the status block, the slug, the paths it owns, and `.devforgeai/work/<run>/option_compare-result.json`. Load that phase's reference file before each dispatch — why: the template header keys and the section rules the phase is checked against live there, not in `SKILL.md`.
5. Dispatch `agents/adr_writer.md` with the status block, `.devforgeai/work/<run>/option_compare-result.json` and the constitution path — why: the ADR path is a producer exception, so this phase writes into `.devforgeai/provenance/adr/` inside the candidate root and nowhere else.
6. Dispatch `agents/gap_analyzer.md` with the three architecture document paths — why: it compares INTENDED sections against the OBSERVED sections in the same files, so it needs no separate input.
7. Dispatch `agents/architect_critic.md` with every prior result path and the five document paths.
8. Advance on a returned `pass`; stop and print on `needs_user` or `could_not_run` — why: `needs_user` closes the run immediately without consulting the attempt counter, so there is nothing left to dispatch.
9. Print the block the sequencer rendered into `.devforgeai/work/<run>/handoff.json`, verbatim. Compose nothing — why: the renderer adds nothing to the receipt, and `devforgeai status` must print the identical block from a cold session.
10. When the handoff reports the run `ready_to_promote` and the user asks for the promotion, call `devforgeai promote <run>` — why: promotion moves the candidate root's bytes into the canonical checkout under the lock, and a `REQUIRE_HUMAN` block is the only state in which the model may ask for it.

A transition failure is not the primary window's business: `devforgeai phase next` exits 1 with the oracle's problem rows, the sequencer rewinds the candidate root to the phase's input checkpoint, and the same worker returns a fresh receipt. The primary window dispatches once per phase.

Without `--yolo`, `option_comparer` returns `needs_user` for every decision area the PRD does not settle, and the run closes at phase 1. Only `--yolo` completes a run without a human round-trip; section 9 records where the human writes the answer.

### 7b. Sub-phases and workers

Gate, Record and Handoff dispatch no LLM: they are `devforgeai` sequencer operations. Slice is a sequencer step too, inside `phase start` (open item OI-1). Only Work, Write and Review name a worker.

| # | Sub-phase | Performed by | Writes | Isolation |
|---|-----------|--------------|--------|-----------|
| 0 | Gate | sequencer: `devforgeai phase start architect <slug>`, which also opens the candidate root | sequencer | n/a |
| 1 | Slice | sequencer: a step inside `phase start` that resolves the incoming artifact's hashed bundle into `.devforgeai/work/<run>/context.json`. No worker | sequencer | n/a |
| 2 | Work: `option_compare` | worker: `option_comparer` | evidence | required |
| 3 | Write: `constitution` | worker: `constitution_writer` | candidate | required |
| 4 | Write: `sourcetree` | worker: `sourcetree_writer` | candidate | required |
| 5 | Write: `techstack` | worker: `techstack_writer` | candidate | required |
| 6 | Write: `architecture` | worker: `architecture_writer` | candidate | required |
| 7 | Write: `design` | worker: `design_writer` | candidate | required |
| 8 | Write: `adr` | worker: `adr_writer` | candidate | required |
| 9 | Work: `gap_analysis` | worker: `gap_analyzer` | evidence | preferred |
| 10 | Review: `critic` | worker: `architect_critic` | evidence | required |
| 11 | Record | sequencer: `devforgeai phase next` | sequencer | n/a |
| 12 | Handoff | sequencer: `devforgeai phase next`, which on the last passing transition marks the run `ready_to_promote` and renders the first block, a `REQUIRE_HUMAN` handoff naming `devforgeai promote <run>`; that command, run only after the user confirms in the session, renders the second | sequencer | n/a |

`option_comparer` is the persona and `architect_critic` is the critic. They are different workers with different prompts and different agent files, because a persona reviewing its own output is the hallucination vector the anatomy exists to remove. Six workers are producers that write inside the candidate root; three are judges. A judge's `Write` is confined to its own run-scoped evidence directory, `.devforgeai/work/<run>/evidence/<agent>/`, which is gitignored, lies outside the candidate root, and is never promoted. Its findings file lives there and is named in `evidence_refs`; `issues[]` stays the bounded summary the handoff carries. Nothing a judge writes can reach the checkpoint diff, so its `claimed_paths` is empty on every status.

For an anatomy-governed skill, `SKILL.md` dispatches each worker through the selected target's provider-native worker mechanism, using the generated target profile, file paths and the `devforgeai status` block. It never pastes or paraphrases artifact content, objectives, or acceptance criteria into the prompt. Its Bash grammar is exactly `devforgeai status | phase start <skill> <arg> | phase fail --reason | validate | promote <run>`; every other sequencer operation is hook-only. The `Isolation` column is the DevForgeAI contract value compiled into the target profile, not Claude's `isolation` frontmatter field; the framework does not use Claude's worktree isolation or `EnterWorktree`, because both fork from HEAD and the run's phases build linearly on one candidate root. Runtime verification of isolation is `12-post-mvp.md#pm-01`.

### 7c. Evidence and gate table

One row per registry phase, in registry order. `<run>` is `architect-<slug>`; `<phase>` is the registry phase name.

| phase | worker | deterministic gate check | gate_policy | evidence file | transition oracle |
|---|---|---|---|---|---|
| `option_compare` | `option_comparer` | run-level gate at `devforgeai phase start`: `architect` is a known skill of kind `document`; no run is already active; each fence entry (`docs/architecture/**`, `.devforgeai/stack.yaml`, `.devforgeai/provenance/adr/**`) is repository-relative, contains no `..`, and is either not sequencer-owned or is a declared producer exception; and no active or `ready_to_promote` run's fence overlaps this one, which `FENCE_OVERLAP` enforces over the two exception paths as well. At ingest: `claimed_paths` is empty, because the registry declares the phase `writes: none` and the worker header `writes: evidence`, and any change inside the candidate root refuses the receipt as `UNCLAIMED_CHANGE`; the dispatcher allows this worker's writes only under `.devforgeai/work/<run>/evidence/option_comparer/` and denies every other path at `PreToolUse` | document run's fixed map `{unresolvable_source: BLOCK}`; every `devforgeai phase start` defect is a refusal whatever a declared value says, and only `test_runner_missing` changes behaviour at transition time, which this phase never reaches because it brokers no command | `.devforgeai/work/<run>/option_compare-result.json`, `option_compare-report.md` | `report_only`: no file outside the fence changed since the gate snapshot and the whole-tree package and import policy holds |
| `constitution` | `constitution_writer` | ingest validation: `changed` derived from the checkpoint diff is a subset of `claimed_paths`, every changed path canonicalises inside `candidate.root`, matches `docs/architecture/**`, is not sequencer-owned, and is allowed by the phase's `writes: docs` mode; then the whole-root package and import rescan before the checkpoint. `scripts/check_intended_set.py --template constitution` parses the written file against the `constitution` header keys | `{unresolvable_source: BLOCK}`; an `UNCLAIMED_CHANGE` refuses the receipt as a protocol error and does not consume an attempt | `.devforgeai/work/<run>/constitution-result.json`, `constitution-report.md` | `document`: the phase produced at least one file and every declared output with non-null content exists on disk |
| `sourcetree` | `sourcetree_writer` | as `constitution`, with `scripts/check_intended_set.py --template sourcetree` | `{unresolvable_source: BLOCK}` | `.devforgeai/work/<run>/sourcetree-result.json`, `sourcetree-report.md` | `document`: as `constitution` |
| `techstack` | `techstack_writer` | as `constitution`, plus the stack producer exception: `.devforgeai/stack.yaml` is admitted only from this `(skill, phase)` pair, and the written file is parsed, every anchor name is checked against `^[a-z][a-z0-9-]*$`, every section is validated against `schemas/devforgeai/v1/stack.schema.json`, and the section contract is re-run before the checkpoint — `build` present when `compiled: true`, `test` present with a `junit_path`, every extractor carrying a capture group. A file failing any of those refuses the receipt, and a deletion of the path is never accepted. `scripts/check_stack_section.py` is the same check as a standalone command | `{unresolvable_source: BLOCK}` | `.devforgeai/work/<run>/techstack-result.json`, `techstack-report.md` | `document`: as `constitution`, over both `docs/architecture/techstack.md` and `.devforgeai/stack.yaml` |
| `architecture` | `architecture_writer` | as `constitution`, with `scripts/check_intended_set.py --template architecture` | `{unresolvable_source: BLOCK}` | `.devforgeai/work/<run>/architecture-result.json`, `architecture-report.md` | `document`: as `constitution` |
| `design` | `design_writer` | as `constitution`, with `scripts/check_intended_set.py --template design`, which additionally checks that each written filename is `design-<topic>.md` where `<topic>` equals the file's own `topic` frontmatter value | `{unresolvable_source: BLOCK}` | `.devforgeai/work/<run>/design-result.json`, `design-report.md` | `document`: as `constitution` |
| `adr` | `adr_writer` | ingest validation as `constitution`, over paths matching `.devforgeai/provenance/adr/NNNN-<slug>.md`, which the producer exception admits from exactly this `(skill, phase)` pair. Each written file is checked against the `adr` template header — required frontmatter, `^ADR-[0-9]{4}$`, the four required sections, forbidden text — and against the filename shape, before the checkpoint. An ADR number already present in the directory refuses the receipt, because an ADR is never overwritten, and the path has no rewind | `{unresolvable_source: BLOCK}` | `.devforgeai/work/<run>/adr-result.json`, `adr-report.md` | `document`: the phase changed at least one file and every ADR it claimed exists in the candidate root |
| `gap_analysis` | `gap_analyzer` | at ingest: `claimed_paths` is empty, because the registry declares the phase `writes: none` and the worker header `writes: evidence`, and any change inside the candidate root refuses the receipt; the dispatcher confines this worker's writes to `.devforgeai/work/<run>/evidence/gap_analyzer/` | `{unresolvable_source: BLOCK}` | `.devforgeai/work/<run>/gap_analysis-result.json`, `gap_analysis-report.md` | `report_only`: as `option_compare` |
| `critic` | `architect_critic` | at ingest: `claimed_paths` is empty and any change inside the candidate root refuses the receipt; the dispatcher confines this worker's writes to `.devforgeai/work/<run>/evidence/architect_critic/`; the phase grants no command key, so `devforgeai run` refuses every key it might name | `{unresolvable_source: BLOCK}` | `.devforgeai/work/<run>/critic-result.json`, `critic-report.md`, then `handoff.json` | `report_only`: as `option_compare`. On pass this is the last phase: the run is marked `ready_to_promote`, enforcement is cleared, and the first handoff's `next` is `devforgeai promote <run>`; the second handoff, written by that command once the user asks for it, takes its `next` from the section 7e table |

Attempt budgets, materialised into the run file from the registry, are 2 for every phase. No `architect` phase declares `rewind_to`, so a `fail` receipt carrying `next` is refused; a `fail` without `next` becomes a transition problem row, the phase retries to its limit, and the run then blocks `REQUIRE_HUMAN` (open item OI-4).

Promotion is not part of the run's phases. The last passing `devforgeai phase next` marks the run `ready_to_promote` and writes a `REQUIRE_HUMAN` handoff whose one forward command is `devforgeai promote <run>`; the candidate root and its checkpoints stay on disk and no canonical byte moves. The compiled `SKILL.md` runs that command only after the user confirms in the session, and it is that command — never `phase next` — that merges the candidate root into the canonical checkout under `.devforgeai/lock`, refusing on `STALE_BASE` when canonical HEAD has moved past the run's pinned `base_ref`, on `DIRTY_TARGET` when a dirty canonical file is among the changed paths, and on `MERGE_CONFLICT` when the rebase cannot replay the run. A refusal moves no canonical byte and leaves the run `ready_to_promote` with its root intact, so the command can be run again once the named cause is settled. The second handoff block is written by a promotion that succeeded, and its `next` is the section 7e row for the run's outcome. Both producer-exception paths reach the canonical tree only through that command. Each refusal is a handoff row in section 7e.

`scripts/check_intended_set.py` and `scripts/check_stack_section.py` are designed as sequencer-side checks. The stack validation in the `techstack` row is implemented — `10-sequencer-and-contracts.md` section 7 states it as the condition of the carve-out. The template-header parsing in the other rows is not: `10-sequencer-and-contracts.md` section 3.3 shows the implemented document gate checking fence entries only. Section 9 records that gap and what the run does without it.

### 7d. Worker contracts

Each block becomes `agents/<role>.md` verbatim, wrapped in skill-creator's Role / Inputs / Process / Output framing, and compiles to one provider profile per target. `name` is the canonical registry worker name, which is what a hook receives as `agent_type`; the compiled filename carries the skill prefix so two skills' profiles cannot collide. `tools` are the Claude names and `tools_codex` the Codex ones, where `apply_patch` stands in for `Edit` and `Write`. `model: inherit` keeps the worker on the session's model, which is what the terminal-only constraint leaves available. No architect phase grants a stack command key, so no worker here carries `Bash(devforgeai run *)`. Claude-only frontmatter — `hooks`, `memory`, `background`, `permissionMode`, and Claude's own `isolation` — is omitted from every profile.

```yaml
name: option_comparer
description: Dispatch this worker at the option_compare phase to judge each architecture decision area the PRD raises and select an option, or say which the PRD cannot settle.
skill: architect
writes: evidence
model: inherit
tools: [Read, Grep, Glob, Bash(devforgeai status), Write]
tools_codex: [Read, Grep, Glob, Bash(devforgeai status), apply_patch]
skills: []
compiled_to: [.claude/agents/architect-option_comparer.md, .codex/agents/architect-option_comparer.toml]
responsibility: Produce one decision row per architecture decision area the PRD raises, each with at least two admissible options, the selected option, and the PRD anchor that justifies the selection.
inputs:
  - docs/PM/<slug>/prd.md
  - docs/architecture/sourcetree.md, techstack.md, architecture.md, for any OBSERVED section already present
  - the --yolo flag token
  - references/option_compare.md, for the decision areas and the selection rule
outputs:
  - .devforgeai/work/<run>/evidence/option_comparer/decisions.md, one section per decision area naming the area, the options compared, the selection, the PRD anchor and any OBSERVED anchor, written in its own run-scoped evidence directory and named in evidence_refs
  - note: the count of areas decided and the count left open
  - issues: one row per unsettled area when --yolo is absent, carried with status needs_user
must_not:
  - select an option the PRD and the OBSERVED sections give no basis for when --yolo is absent
  - read a source file the PRD or an OBSERVED section does not name
  - write anywhere but its own run-scoped evidence directory, or run any stack command key
isolation: required
returns: devforgeai.worker-result/v1
body:
  job: Judge each decision area the PRD raises, compare at least two admissible options, and select one or say the PRD cannot settle it.
  inputs: The list above, read under the candidate root; nothing outside it is opened.
  rules: references/option_compare.md, the selection rule under --yolo, and the must_not list.
  receipt: One devforgeai.worker-result/v1 object; claimed_paths is empty on every status, evidence_refs names the decisions file it wrote under its run-scoped evidence directory, and an unsettled area is one issues row with status needs_user.
```

```yaml
name: constitution_writer
description: Dispatch this worker at the constitution phase to write the constitution with its principles, mandates, constraints and style rules.
skill: architect
writes: candidate
model: inherit
tools: [Read, Grep, Glob, Bash(devforgeai status), Edit, Write]
tools_codex: [Read, Grep, Glob, Bash(devforgeai status), apply_patch]
skills: []
compiled_to: [.claude/agents/architect-constitution_writer.md, .codex/agents/architect-constitution_writer.toml]
responsibility: Write docs/architecture/constitution.md inside the candidate root with its Principles, Mandates, Constraints and Style sections, one SEC-NNN row per rule, and the mandates that later phases bind to.
inputs:
  - .devforgeai/work/<run>/option_compare-result.json
  - docs/PM/<slug>/prd.md
  - assets/constitution.md, the template skeleton
  - references/constitution.md, for the header keys, the SEC id rule and the mandate vocabulary
outputs:
  - docs/architecture/constitution.md, written inside the candidate root and claimed
  - the Mandates section, one row per mandate with its key, its value and the skill it names when it names one
must_not:
  - change any path outside docs/architecture/
  - write a skill specification or name a path under docs/plan/
  - record a rule that no decision row or PRD anchor supports
  - write outside the candidate root, or outside the run's fence inside it
isolation: required
returns: devforgeai.worker-result/v1
body:
  job: Write the constitution so every rule traces to a decision row or a PRD anchor, and the mandates say what the project must have.
  inputs: The list above, read under the candidate root.
  rules: references/constitution.md, the SEC id rule and the mandate vocabulary, and the must_not list.
  receipt: One devforgeai.worker-result/v1 object; claimed_paths is exactly docs/architecture/constitution.md.
```

```yaml
name: sourcetree_writer
description: Dispatch this worker at the sourcetree phase to write the INTENDED layout, ownership and naming sections.
skill: architect
writes: candidate
model: inherit
tools: [Read, Grep, Glob, Bash(devforgeai status), Edit, Write]
tools_codex: [Read, Grep, Glob, Bash(devforgeai status), apply_patch]
skills: []
compiled_to: [.claude/agents/architect-sourcetree_writer.md, .codex/agents/architect-sourcetree_writer.toml]
responsibility: Write docs/architecture/sourcetree.md inside the candidate root with the INTENDED Layout, Ownership and Naming sections, one PATH-NNN row per path rule.
inputs:
  - .devforgeai/work/<run>/option_compare-result.json
  - docs/architecture/constitution.md
  - assets/sourcetree.md
  - references/sourcetree.md, for the header keys and the mode field
outputs:
  - docs/architecture/sourcetree.md, written inside the candidate root and claimed
  - one PATH-NNN row per path rule, each with its path glob and the component it owns
must_not:
  - alter or delete an OBSERVED section already in the file
  - change any path outside docs/architecture/
  - name a path that no decision row or constitution section supports
  - write outside the candidate root, or outside the run's fence inside it
isolation: required
returns: devforgeai.worker-result/v1
body:
  job: Write the INTENDED source tree beside whatever OBSERVED section the file already carries.
  inputs: The list above, read under the candidate root.
  rules: references/sourcetree.md, the mode field, and the must_not list.
  receipt: One devforgeai.worker-result/v1 object; claimed_paths is exactly docs/architecture/sourcetree.md, and the checkpoint diff leaves any OBSERVED section byte-identical.
```

```yaml
name: techstack_writer
description: Dispatch this worker at the techstack phase to write techstack.md and the INTENDED stack.yaml section it names.
skill: architect
writes: candidate
model: inherit
tools: [Read, Grep, Glob, Bash(devforgeai status), Edit, Write]
tools_codex: [Read, Grep, Glob, Bash(devforgeai status), apply_patch]
skills: []
compiled_to: [.claude/agents/architect-techstack_writer.md, .codex/agents/architect-techstack_writer.toml]
responsibility: Write docs/architecture/techstack.md and the INTENDED .devforgeai/stack.yaml section it names in its stack_section key, inside the candidate root and against the section contract.
inputs:
  - .devforgeai/work/<run>/option_compare-result.json
  - docs/architecture/constitution.md
  - .devforgeai/stack.yaml, when the file already exists
  - assets/techstack.md and assets/stack.yaml
  - references/techstack.md, for the section contract and the anchor naming rule
outputs:
  - docs/architecture/techstack.md, written inside the candidate root and claimed
  - .devforgeai/stack.yaml inside the candidate root, edited in place so every section it did not derive stays byte-identical, claimed alongside it
  - the anchor name, the command keys defined, and whether the section is compiled, stated in the note
must_not:
  - remove a section from .devforgeai/stack.yaml, or delete the file
  - define a test key without a junit_path, or omit build when compiled is true
  - write a literal command anywhere in techstack.md; the document names keys and the section holds argv
  - change any other path under .devforgeai/
  - write outside the candidate root, or outside the run's fence inside it
isolation: required
returns: devforgeai.worker-result/v1
body:
  job: Write the tech stack document and the machine-readable section it names, so every later command is a key.
  inputs: The list above, read under the candidate root.
  rules: references/techstack.md, the full section contract, and the must_not list.
  receipt: One devforgeai.worker-result/v1 object; claimed_paths names both docs/architecture/techstack.md and .devforgeai/stack.yaml.
```

```yaml
name: architecture_writer
description: Dispatch this worker at the architecture phase to write the INTENDED components, interfaces, data flow and failure modes.
skill: architect
writes: candidate
model: inherit
tools: [Read, Grep, Glob, Bash(devforgeai status), Edit, Write]
tools_codex: [Read, Grep, Glob, Bash(devforgeai status), apply_patch]
skills: []
compiled_to: [.claude/agents/architect-architecture_writer.md, .codex/agents/architect-architecture_writer.toml]
responsibility: Write docs/architecture/architecture.md inside the candidate root with the INTENDED Components, Interfaces, Data Flow and Failure Modes sections, one COMP-NNN row per component.
inputs:
  - .devforgeai/work/<run>/option_compare-result.json
  - docs/architecture/constitution.md, sourcetree.md, techstack.md
  - assets/architecture.md
  - references/architecture.md, for the header keys and the component row shape
outputs:
  - docs/architecture/architecture.md, written inside the candidate root and claimed
  - one COMP-NNN row per component, each naming the sourcetree path it lives at
must_not:
  - alter or delete an OBSERVED section already in the file
  - name a component whose path no PATH-NNN row admits
  - change any path outside docs/architecture/
  - write outside the candidate root, or outside the run's fence inside it
isolation: required
returns: devforgeai.worker-result/v1
body:
  job: Write the component architecture so every component lives at a path the source tree already admits.
  inputs: The list above, read under the candidate root.
  rules: references/architecture.md, the component row shape, and the must_not list.
  receipt: One devforgeai.worker-result/v1 object; claimed_paths is exactly docs/architecture/architecture.md.
```

```yaml
name: design_writer
description: Dispatch this worker at the design phase to write one design document per decision row.
skill: architect
writes: candidate
model: inherit
tools: [Read, Grep, Glob, Bash(devforgeai status), Edit, Write]
tools_codex: [Read, Grep, Glob, Bash(devforgeai status), apply_patch]
skills: []
compiled_to: [.claude/agents/architect-design_writer.md, .codex/agents/architect-design_writer.toml]
responsibility: Write one docs/architecture/design-<topic>.md per decision row inside the candidate root, each recording the Decision, the Options compared, the Consequences and the Interfaces it fixes.
inputs:
  - .devforgeai/work/<run>/option_compare-result.json
  - docs/architecture/constitution.md, techstack.md, architecture.md
  - assets/design.md
  - references/design.md, for the topic slug rule and the header keys
outputs:
  - one docs/architecture/design-<topic>.md per topic, written inside the candidate root and each claimed
  - each file's own topic frontmatter value, equal to its filename topic segment
must_not:
  - write a filename whose topic segment differs from the file's own topic frontmatter value
  - write a design document for a decision row option_comparer did not return
  - change any path outside docs/architecture/
  - write outside the candidate root, or outside the run's fence inside it
isolation: required
returns: devforgeai.worker-result/v1
body:
  job: Render each decision row as one design document whose filename and topic key agree.
  inputs: The list above, read under the candidate root.
  rules: references/design.md, the topic slug rule, and the must_not list.
  receipt: One devforgeai.worker-result/v1 object; claimed_paths lists every design document written, at most 64.
```

```yaml
name: adr_writer
description: Dispatch this worker at the adr phase to write one ADR per decision row into the run's provenance directory.
skill: architect
writes: candidate
model: inherit
tools: [Read, Grep, Glob, Bash(devforgeai status), Edit, Write]
tools_codex: [Read, Grep, Glob, Bash(devforgeai status), apply_patch]
skills: []
compiled_to: [.claude/agents/architect-adr_writer.md, .codex/agents/architect-adr_writer.toml]
responsibility: Write one ADR per decision row at .devforgeai/provenance/adr/NNNN-<slug>.md inside the candidate root, each with its Context, Decision, Consequences and Alternatives, numbered ADR-NNNN in the order the decisions were taken.
inputs:
  - the devforgeai status block pasted into the dispatch, which names run, candidate.root, phase, fence and granted_keys
  - .devforgeai/work/<run>/option_compare-result.json
  - docs/architecture/constitution.md inside the candidate root
  - .devforgeai/provenance/adr/ inside the candidate root, to read the highest number already allocated
  - assets/adr.md
  - references/adr.md, for the numbering rule and the producer exception this phase writes under
outputs:
  - one .devforgeai/provenance/adr/NNNN-<slug>.md per decision, written inside the candidate root and each claimed
  - each file's ADR-NNNN id, matching the number in its filename
must_not:
  - reuse an ADR number already present in the provenance directory, or rewrite an existing ADR
  - record a decision option_comparer did not return
  - change any path under .devforgeai/ other than .devforgeai/provenance/adr/
  - write outside the candidate root, or outside the run's fence inside it
isolation: required
returns: devforgeai.worker-result/v1
body:
  job: Write one ADR per decision, numbered above the highest already allocated, under the producer exception this phase holds.
  inputs: The list above, read under the candidate root.
  rules: references/adr.md, the numbering and filename rules, and the must_not list.
  receipt: One devforgeai.worker-result/v1 object; claimed_paths lists every ADR written, and the path has no rewind, so a refused receipt leaves the previous checkpoint intact.
```

```yaml
name: gap_analyzer
description: Dispatch this worker at the gap_analysis phase to judge each INTENDED section against the OBSERVED constraints that exist.
skill: architect
writes: evidence
model: inherit
tools: [Read, Grep, Glob, Bash(devforgeai status), Write]
tools_codex: [Read, Grep, Glob, Bash(devforgeai status), apply_patch]
skills: []
compiled_to: [.claude/agents/architect-gap_analyzer.md, .codex/agents/architect-gap_analyzer.toml]
responsibility: Compare each INTENDED section against the OBSERVED constraint sections that actually exist and return one evidenced gap row per difference, citing both anchors.
inputs:
  - docs/architecture/sourcetree.md, techstack.md, architecture.md
  - docs/reports/drift-<slug>.md, when it exists
  - references/gap_analysis.md, for what counts as an evidenced gap
outputs:
  - .devforgeai/work/<run>/evidence/gap_analyzer/gaps.md, one section per gap naming both anchors and the migration it implies, written in its own run-scoped evidence directory and named in evidence_refs
  - issues: one row per gap, each naming the intended anchor and the observed anchor, bounded at ten
  - note: the count of INTENDED sections compared and OBSERVED sections found
must_not:
  - report a gap against an OBSERVED section that does not exist in the file
  - write a migration epic or story; plan owns both templates
  - write anywhere but its own run-scoped evidence directory, or run any stack command key
isolation: preferred
returns: devforgeai.worker-result/v1
body:
  job: Judge each INTENDED section against the OBSERVED constraint in the same file and report the evidenced differences.
  inputs: The list above, read under the candidate root; nothing outside it is opened.
  rules: references/gap_analysis.md, what counts as an evidenced gap, and the must_not list.
  receipt: One devforgeai.worker-result/v1 object; claimed_paths is empty on every status, evidence_refs names the gaps file it wrote under its run-scoped evidence directory, and each gap is also one issues row citing both anchors.
```

```yaml
name: architect_critic
description: Dispatch this worker at the critic phase to judge every section this run wrote against its template header and the anchor it cites.
skill: architect
writes: evidence
model: inherit
tools: [Read, Grep, Glob, Bash(devforgeai status), Write]
tools_codex: [Read, Grep, Glob, Bash(devforgeai status), apply_patch]
skills: []
compiled_to: [.claude/agents/architect-architect_critic.md, .codex/agents/architect-architect_critic.toml]
responsibility: Check every written section against the template header it claims and against the PRD anchor or decision row it cites, and report defects without repairing them.
inputs:
  - every .devforgeai/work/<run>/<phase>-result.json from the eight prior phases
  - docs/architecture/constitution.md, sourcetree.md, techstack.md, architecture.md and every design-<topic>.md
  - docs/PM/<slug>/prd.md
  - references/critic.md, for the defect classes and the evidence a finding must carry
outputs:
  - .devforgeai/work/<run>/evidence/architect_critic/findings.md, the full defect list and the per-requirement coverage table, written in its own run-scoped evidence directory and named in evidence_refs
  - issues: at most ten rows, each naming the file, the section id and the defect class
  - note: the count of PRD requirement anchors covered and uncovered
must_not:
  - repair a defect it found
  - pass a section without quoting the anchor or decision row it cites
  - report a defect against a section no phase of this run wrote
  - write anywhere but its own run-scoped evidence directory, or run any stack command key
isolation: required
returns: devforgeai.worker-result/v1
body:
  job: Judge every section this run wrote against the template header it claims and the anchor it cites.
  inputs: The list above, read under the candidate root; nothing outside it is opened.
  rules: references/critic.md, the defect classes, and the must_not list.
  receipt: One devforgeai.worker-result/v1 object; claimed_paths is empty on every status, evidence_refs names the findings file it wrote under its run-scoped evidence directory, and each defect is also one issues row.
```

A producer's tools are the read set plus `Edit` and `Write`, which Codex serves as `apply_patch`; a judge's are the read set plus a `Write` the dispatcher confines to `.devforgeai/work/<run>/evidence/<agent>/`, and no `Edit`. Both include `Bash(devforgeai status)` and nothing else on the Bash surface, because no `architect` phase grants a stack command key (open item OI-3).

### 7e. Handoff outcomes

The `handoff.outcomes` block the skill declares. The sequencer selects the row by receipt status and fills `{slug}` from state.

| Outcome | Next steps |
|---------|------------|
| pass, run `ready_to_promote`, nothing promoted (`REQUIRE_HUMAN`) | 1. `devforgeai promote {run}` |
| `devforgeai promote {run}` succeeded | 1. `/plan {slug}` |
| promoted, `constitution.md#mandates` names a skill the project lacks | 1. `/plan {slug}`, which writes the spec for each mandate and orders `/skill-gen` before the dependent story |
| promoted, `gap_analysis` returned evidenced gap rows | 1. `/plan {slug}`, which turns the rows in `.devforgeai/work/{run}/gap_analysis-result.json` into a migration epic. Also possible: `/analyze {slug}` |
| needs_user at `option_compare` | 1. record each open decision as a `REQ-NNN` row in `docs/PM/{slug}/prd.md`, then 2. `/architect {slug} --yolo`, which resumes the blocked run at `option_compare` with attempts reset — the run stayed `active` with `run.yaml#blocked_at` naming that phase |
| fail at `adr`, `max_attempts` reached | 1. fix what the handoff names, then `/architect {slug}` — the run is blocked, not closed: it stays `active` with its lease released, its candidate root and every checkpoint on disk and `run.yaml#blocked_at` naming `adr`, and this same command resumes it there with attempts reset. Nothing the earlier phases wrote has reached the canonical tree either way, because only `devforgeai promote {run}` moves a byte; `devforgeai phase fail --reason <text>` is what abandons the root |
| fail at any other phase, `max_attempts` reached | 1. fix what the handoff names, then `/architect {slug}`, which resumes the blocked run at `blocked_at` with attempts reset |
| could_not_run, `reason_code: hook_fault` | 1. reinstall the dispatcher named in `.devforgeai/sessions/`, then 2. `/architect {slug}` |
| could_not_run, any other `reason_code` | 1. the repair route for that reason code, then 2. `/architect {slug}` |
| BLOCK, recorded by `devforgeai phase fail --reason` | 1. `/status` |
| `devforgeai promote {run}` refused `STALE_BASE` in worktree mode | 1. `devforgeai promote {run}` again; that command rebases the candidate root onto the new canonical HEAD, reruns the last transition oracle and retries the fast-forward itself before it reports, so this row is reached only when the retry also failed |
| `devforgeai promote {run}` refused `STALE_BASE` in copy mode, or `MERGE_CONFLICT` after an aborted rebase | 1. reconcile `docs/architecture/`, `.devforgeai/stack.yaml` and `.devforgeai/provenance/adr/` by hand, then `devforgeai promote {run}` — the refusal moved no canonical byte, and the run stays `ready_to_promote` with its root intact |
| `devforgeai promote {run}` refused `DIRTY_TARGET` | 1. commit or discard the dirty canonical file the refusal names, then `devforgeai promote {run}` |
| `phase start` refused `FENCE_OVERLAP` | 1. finish or abandon the run the refusal names, then `/architect {slug}` — a second architect run, or an onboard run holding `.devforgeai/stack.yaml`, cannot be open at the same time |

A gate refusal is not a row in this table. `devforgeai phase start` exits 1 with the defect list and writes no handoff (`10-sequencer-and-contracts.md` section 3.2), so `02-skill-roster.md`'s `gate fail` row is corrected out of the decision table and recorded in section 9. `02`'s `prototype raised ideas` row is removed for the reason section 9 records.

## 8. Bundled resources

### Layout (fixed)

```
architect/SKILL.md          # at most 500 lines: identity, phase list, dispatch loop, handoff table
  references/option_compare.md
  references/constitution.md
  references/sourcetree.md
  references/techstack.md
  references/architecture.md
  references/design.md
  references/adr.md
  references/gap_analysis.md
  references/critic.md
  references/envelope.md
  agents/option_comparer.md
  agents/constitution_writer.md
  agents/sourcetree_writer.md
  agents/techstack_writer.md
  agents/architecture_writer.md
  agents/design_writer.md
  agents/adr_writer.md
  agents/gap_analyzer.md
  agents/architect_critic.md
  scripts/check_prd.py
  scripts/check_intended_set.py
  scripts/check_stack_section.py
  assets/constitution.md
  assets/sourcetree.md
  assets/techstack.md
  assets/architecture.md
  assets/design.md
  assets/adr.md
  assets/stack.yaml
```

Link depth: `SKILL.md` links to `references/`, `agents/`, `scripts/` and `assets/`; an `agents/*.md` links to `references/*.md`; nothing links further.

### scripts/

Every script is deterministic, non-interactive, prints data to stdout and diagnostics to stderr, and documents `--help`.

| File | Purpose | Invocation | Exit codes |
|------|---------|------------|------------|
| `check_prd.py` | Validate the incoming PRD against the `prd` template header owned by `pm` — frontmatter keys, the four required sections, `^REQ-[0-9]{3}$` ids, forbidden placeholder text — and re-resolve every `depends_on` entry with the hash rule in `10-sequencer-and-contracts.md` section 3.4. Invoked by a human, and designed to be imported by the sequencer's document gate at `devforgeai phase start architect` so a malformed PRD refuses the run; that gate import is not implemented today (section 9) | `python3 scripts/check_prd.py docs/PM/SLUG/prd.md [--template PATH] [--json]` | 0 pass, 1 defects listed on stdout, 2 usage |
| `check_intended_set.py` | Validate one written architecture document against the named template's header keys, id pattern, required sections and forbidden text, and check that every `depends_on` source and anchor resolves. Invoked by a human, and designed to be imported by the sequencer at `devforgeai ingest-result` for the five writer phases; that import is not implemented today (section 9) | `python3 scripts/check_intended_set.py PATH --template constitution\|sourcetree\|techstack\|architecture\|design [--json]` | 0 pass, 1 defects, 2 usage |
| `check_stack_section.py` | Validate one `stack.yaml` section against `schemas/devforgeai/v1/stack.schema.json` and the section contract: anchor name pattern, `build` present when `compiled` is true, `test` present with a `junit_path`, every extractor carrying capture group 1, every `forbidden_imports` row carrying a reason. This is the same check the sequencer runs before checkpointing a `techstack` phase, exposed as a command so a human can check a section before a run | `python3 scripts/check_stack_section.py .devforgeai/stack.yaml --anchor NAME [--json]` | 0 pass, 1 contract or schema violation, 2 usage |

### references/

| File | Content | Load when |
|------|---------|-----------|
| `option_compare.md` | The decision areas a PRD raises (language and runtime, source layout, data access, testing, build and lint, install and packaging, interface surface), what makes an option admissible, the selection rule under `--yolo` (prefer the option the PRD's own requirements and any OBSERVED section already imply; break a remaining tie toward the smaller dependency surface), and the `needs_user` rule without it. | dispatching `option_comparer` |
| `constitution.md` | The `constitution` header keys, the `SEC-NNN` id rule, what belongs in Principles versus Constraints versus Style, and the mandate vocabulary — a mandate is a key, a value and, where it names one, the skill the project must have. | dispatching `constitution_writer` |
| `sourcetree.md` | The `sourcetree` header keys, `PATH-NNN` ids, the `mode` field, and why an OBSERVED section in the same file is left byte-identical. | dispatching `sourcetree_writer` |
| `techstack.md` | The `techstack` header keys including `stack_section`, `TS-NNN` ids, and the full `stack.yaml` section contract from `10-sequencer-and-contracts.md` section 7: every key, its type, `compiled` implying `build`, `junit_path` on `test`, extractor capture groups, and the package and import policy fields. | dispatching `techstack_writer` |
| `architecture.md` | The `architecture` header keys, `COMP-NNN` ids, and the rule that every component names a path an existing `PATH-NNN` row admits. | dispatching `architecture_writer` |
| `design.md` | The `design` header keys, `DES-NNN` ids, the topic slug rule that ties the filename to the `topic` frontmatter value, and what the four sections hold. | dispatching `design_writer` |
| `adr.md` | The `adr` header keys, `ADR-NNNN` numbering from the highest already in the provenance directory, the `NNNN-<slug>.md` filename shape, and the producer exception that lets this phase write under `.devforgeai/provenance/adr/` inside the candidate root. | dispatching `adr_writer` |
| `gap_analysis.md` | What an evidenced gap is: an INTENDED section and an OBSERVED section in the same file that state incompatible things, each cited by anchor. Absence of an OBSERVED section is not a gap. | dispatching `gap_analyzer` |
| `critic.md` | The defect classes — uncited rule, id pattern violation, missing required section, component with no admitting path, PRD requirement with no covering section — and the evidence each finding must carry. | dispatching `architect_critic` |
| `envelope.md` | The `devforgeai.worker-result/v1` receipt, its bounds (64 `claimed_paths`, 16 `evidence_refs`, 16 KiB note, 10 issues), the closed status set with `reason_code`, the rule that `claimed_paths` is empty on any non-pass status, and the rule that `next` needs a registry `rewind_to` no architect phase declares. | every dispatch |

### assets/

| File | Used for |
|------|----------|
| `constitution.md` | `docs/architecture/constitution.md` skeleton: frontmatter keys and the four required section headings, empty. |
| `sourcetree.md` | `docs/architecture/sourcetree.md` skeleton. |
| `techstack.md` | `docs/architecture/techstack.md` skeleton, including the `stack_section` frontmatter key. |
| `architecture.md` | `docs/architecture/architecture.md` skeleton. |
| `design.md` | `docs/architecture/design-<topic>.md` skeleton. |
| `adr.md` | ADR skeleton: frontmatter keys and the four required section headings. |
| `stack.yaml` | One commented `stack.yaml` section with every required key present and no value filled, so a written section starts from the contract rather than from memory. |

### agents/

| File | Worker (from section 7d) |
|------|-------------------------|
| `option_comparer.md` | `option_comparer` |
| `constitution_writer.md` | `constitution_writer` |
| `sourcetree_writer.md` | `sourcetree_writer` |
| `techstack_writer.md` | `techstack_writer` |
| `architecture_writer.md` | `architecture_writer` |
| `design_writer.md` | `design_writer` |
| `adr_writer.md` | `adr_writer` |
| `gap_analyzer.md` | `gap_analyzer` |
| `architect_critic.md` | `architect_critic` |

## 9. Gotchas and edge cases

| Situation | What goes wrong | What to do instead |
|-----------|-----------------|--------------------|
| OI-1: `01-skill-anatomy.md` and `05-subagent-sets.md` give Slice to a framework worker, but no `architect` phase dispatches one | The generated skill grows a tenth agent file with no registry phase to run it, and `agent_type` never matches at ingest | Slice is a sequencer step inside `devforgeai phase start`: it resolves the incoming artifact's already-hashed bundle and writes `.devforgeai/work/<run>/context.json`, which every worker of the run is handed by path. This spec promises no slice phase and ships no slice agent file. |
| OI-2: provenance conformance at the gate | An `architect` spec that promised story-style re-resolution would over-promise | `10-sequencer-and-contracts.md` section 3.4 now carries full re-resolution, and section 4 makes `qa` and `review` the only story-anchored document skills. `architect`'s gate is the fence gate alone, so nothing re-resolves the PRD's `depends_on` entries when the run opens. `check_prd.py` is the designed replacement and is not wired in; the run relies on `architect_critic` reporting an uncited section instead, which is a model judgement and not a gate. |
| OI-3: worker tools | A generator either gives every worker the same tools or widens a judge's to include a write | Tools follow the role. A producer carries `Read`, `Grep`, `Glob`, `Bash(devforgeai status)` plus `Edit` and `Write`, which Codex serves as `apply_patch`; every write is denied outside `candidate.root` and outside the phase's fence, and the lease bound at `SubagentStart` is what the dispatcher checks. A judge carries the read set plus a `Write` the dispatcher confines to `.devforgeai/work/<run>/evidence/<agent>/`, which is gitignored, outside the candidate root, and never promoted. `Bash(devforgeai run *)` is granted only where a phase declares run keys, and no `architect` phase does. |
| OI-4: no outcome row for `status: fail` with no `next` | A reader assumes a failing critic passes silently | `examples/hooks/devforgeai.py` inserts `"<agent> reported fail"` as a transition problem row, so the phase retries to `max_attempts: 2` and then blocks `REQUIRE_HUMAN`. The `fail at any other phase` row in section 7e is that path. |
| OI-5: `--yolo` and `--retry` look like resume flags | A user expects the flag to be what picks up where the run stopped, and an author writes a repair route that depends on it | The run does pick up where it stopped, and no flag is what does it. A `needs_user` result blocks the run rather than closing it: it stays `active` with `run.yaml#blocked_at` naming `option_compare`, and plain `devforgeai phase start architect {slug}` resumes it there with `attempts` reset. `--yolo` changes only what the worker reads, and it is the only flag this skill defines; `02-skill-roster.md`'s `--retry` and `--update` are unnecessary under the resume rule, are not implemented, and this spec does not name them as commands. Where a run really is closed by `devforgeai phase fail --reason <text>`, the next invocation opens a fresh run from `option_compare`. |
| OI-6: the ADR path is under `.devforgeai/` | An earlier draft of this spec had `adr_writer` carry each ADR's text in the receipt because no path admitted it, which left the phase unable to satisfy its `document` oracle | `examples/hooks/policy.py` now carries `.devforgeai/provenance/adr/**` in `PRODUCER_EXCEPTIONS` for `(architect, adr)` and `(amend, adr)`, and `architect`'s fence lists it. `adr_writer` writes `NNNN-<slug>.md` files inside the candidate root; the sequencer validates each against the `adr` template header — required frontmatter, `^ADR-[0-9]{4}$`, the four required sections, forbidden text — and against the filename shape before checkpointing, refuses a number already allocated, and provides no rewind for the path. The files reach the canonical tree only at promotion. Installing an ADR by hand is no longer a step in this spec. |
| OI-7: `02-skill-roster.md` shows architect looping back to brainstorm | A generated `SKILL.md` tries `devforgeai phase start brainstorm` from inside an architect run and is refused, because a run is already active | No skill invokes another skill's run. Every cross-skill edge is a handoff row the sequencer fills; a human or a fresh session runs it. Section 7a's dispatch loop names no other command. |
| OI-8: `05-subagent-sets.md` writes worker names hyphenated (`option-comparer`, `critic`) while the registry writes them with underscores | `agent_type` fails the phase-agent binding check and the receipt is refused | The registry name in `10-sequencer-and-contracts.md` section 4 is canonical: `option_comparer`, `constitution_writer`, `sourcetree_writer`, `techstack_writer`, `architecture_writer`, `design_writer`, `adr_writer`, `gap_analyzer`, `architect_critic`. Note `architect_critic`, not `critic`. It is the agent filename, the `agents/` table row, and the string compared to the stop event's `agent_type`. |
| OI-9: the `.devforgeai/stack.yaml` write path | An author could either refuse to write the path at all or let any phase write it | The path is a producer exception to the sequencer-owned deny list, restricted to `architect`/`techstack` and `onboard`/`code_map`. `techstack_writer` edits it in place inside the candidate root; at ingest the sequencer parses the written file, checks every anchor name, validates every section against `schemas/devforgeai/v1/stack.schema.json`, re-runs the section contract, and checkpoints, or refuses the receipt. Every other `architect` phase is refused the path as sequencer-owned. `FENCE_OVERLAP` counts the path, so an `onboard` run and an `architect` run cannot both hold it. |
| OI-10: skills whose command takes no positional argument | Not reachable from `architect` | `/architect` always carries a slug, which is both the `devforgeai phase start` argument and the run id component in `architect-<slug>`. The fence `docs/architecture/**` does not substitute the argument, so two projects in one repository share one architecture set by design. |
| OI-11 (new): no worker can compute a SHA-256, yet every INTENDED document's `depends_on` entries require one | A worker's Bash surface is `devforgeai status` alone, with no hashing command, so each writer emits `sha256:PENDING` for its PRD anchors. `10-sequencer-and-contracts.md` section 3.4 classes that as `unresolvable-source`, so every story `plan` later slices from these documents inherits an unresolvable digest and `devforgeai phase start dev` refuses it | `architect`'s own gate does not re-resolve `depends_on`, so the placeholder does not stop this run. The defect lands downstream. The fix belongs at `devforgeai ingest-result`: after the change set is validated and before the checkpoint is taken, resolve every `sha256:PENDING` in a written artifact's frontmatter with the section 3.4 rule, using the same section-resolution library the gate uses, and refuse the receipt when a source or anchor does not resolve. This spec does not gate on that fix and does not describe it as running. |
| `02-skill-roster.md` and `05-subagent-sets.md` name a `prototyper` worker and a prototype loop back to brainstorm | A generator writes a tenth agent file and a handoff row for a phase that does not exist | The registry gives `architect` nine phases and no `prototyper`. This spec ships no prototyper agent file and removes `02`'s `prototype raised ideas` handoff row. A project that wants a prototype runs `/brainstorm {slug}` as a separate command after the architect run closes. |
| `05-subagent-sets.md` offers `decision-interviewer` as the alternative to `option-comparer` | An interactive run would need a worker the registry does not have | Phase 1 always dispatches `option_comparer`. Without `--yolo` it returns `needs_user` rather than interviewing, because a worker cannot hold a conversation and the closed status set gives it one way to ask. The human records the answer as a `REQ-NNN` row in `docs/PM/<slug>/prd.md` — the only upstream artifact `architect` reads that a human may edit between runs — and re-runs with `--yolo`. Only `--yolo` completes a run without a human round-trip today. |
| A second `architect` run over a repository that already has the five documents | A writer that rewrote a file wholesale would drop any OBSERVED section `onboard` wrote, and the deletion would reach canonical at promotion | Each writer edits the file where it stands in the candidate root, over the bytes the previous checkpoint left, and each writer's `must_not` forbids altering or deleting an OBSERVED section in the same file. `architect_critic` reports a removed OBSERVED anchor as a defect and the checkpoint diff is what a reviewer reads. Nothing deterministic checks the OBSERVED preservation today; that is the same gap as the unimplemented `check_intended_set.py` import. |
| Rewriting a `stack.yaml` section a story already pinned | The story's `commands.hash` digests the whole file, so any edit anywhere invalidates every story pinned to it, and promotion is the moment the invalidation lands | That is the intended effect. The next `devforgeai phase start` for such a story is a stale-hash refusal, which is never downgradable, and the repair is `/plan {slug} --reslice {story}`. The handoff row for a passing run says `/plan {slug}`, which re-slices as it re-plans. |
| A monorepo with two package managers | One `stack.yaml` section carries one `commands` block, so a project with two ecosystems cannot express both in the section a story pins | `techstack_writer` writes one section per anchor and each story pins exactly one. Cross-package stories are out of scope; the deferred contract is `12-post-mvp.md#pm-09`. |
| The candidate root and the primary window | A worker cannot resolve `candidate.root` from the canonical tree, and pasting artifact content into a dispatch is the restatement the anti-ceremony rules forbid | Every anatomy run gets one candidate root, opened by `phase start` and owned by the sequencer until promotion or abandonment; the primary window stays in the canonical checkout. The one thing a dispatch carries beyond paths, ids and the `--yolo` token is the `devforgeai status` block, which names `run`, `candidate.root`, `phase`, `fence` and `granted_keys`. It is generated, not composed, and it is the only sanctioned paste. Claude's own worktree isolation setting and `EnterWorktree` are not used: they fork from HEAD and would split the run's linear history |
| The receipt no longer carries an `evidence` object | Earlier drafts gave the phases `evidence.decisions`, `evidence.mandates`, `evidence.paths`, `evidence.stack_section`, `evidence.components`, `evidence.topics`, `evidence.adrs`, `evidence.gaps` and `evidence.coverage`. The receipt schema in the write-model revision removes `evidence` and adds `claimed_paths` and `evidence_refs`, which are paths, not rows | Every writer's rows have a home in the file it wrote: mandates in `## Mandates`, path rules as `PATH-NNN`, components as `COMP-NNN`, topics in each design document's own frontmatter, ADRs as files. `evidence_refs` points at those files, `note` carries the counts and the decision selections, and `issues` carries a judge's findings, bounded at ten rows. The one thing that changes shape is `adr_writer`: its output is now files rather than text in a field, which is what the producer exception exists for |
| The `design` phase has nothing to write | A project with no decisions would fail the `document` oracle at phase 6 | `option_comparer` returns at least the language-and-runtime and the testing decision rows on any PRD, because both are required for a `stack.yaml` section to exist at all, so `design_writer` always has at least two topics. A run whose `option_compare` evidence is empty fails at phase 2 instead, where `constitution_writer` has no decision row to render. |
| An earlier draft said promotion is the last thing the run does and that `devforgeai phase next` merges the candidate root | An author compiles a `SKILL.md` that never asks the user, and the run's files land in the canonical checkout without a human decision | Promotion is never automatic. The last passing transition sets `runs.<run>.status: ready_to_promote` and writes a `REQUIRE_HUMAN` handoff whose only forward step is `devforgeai promote <run>`; the compiled `SKILL.md` runs that command only after the user confirms in the session, and that command writes the second handoff block, whose `next` is the section 7e row for the run's outcome. Every run ends in two blocks, not one, and `STALE_BASE`, `DIRTY_TARGET` and `MERGE_CONFLICT` are refusals of `devforgeai promote <run>` that leave the run `ready_to_promote` with its root intact, never refusals of `devforgeai phase next`. **Decision (D7, as amended; `10-sequencer-and-contracts.md` sections 5.4, 6 and 12.4):** the sequencer may not close a run onto the canonical tree on its own. |
| An earlier draft said a `REQUIRE_HUMAN` block closes the run, so "no flag resumes a closed one" | An author writes a repair route that opens a fresh run, and `devforgeai phase start` refuses it — the blocked run is still `active` — or writes `devforgeai phase fail --reason <text>` into every recovery row and throws away work the run had already checkpointed | A block is not a close. A `needs_user` result and an exhausted attempt budget both leave the run `active` with its lease released, its candidate root and checkpoints on disk, and `run.yaml#blocked_at` naming the phase. `devforgeai phase start` with the same skill and the same argument **resumes** that run at `blocked_at` with `attempts` reset to zero instead of refusing it, so `/architect {slug}` is the whole recovery once the human has acted. Only another skill on the same story needs `devforgeai phase fail --reason <text>` first, and that call is what abandons the root. **Decision (`10-sequencer-and-contracts.md` sections 2, 3, 5.4 and 6):** blocked runs resume; they are not reopened. |
| An earlier section 7e row said an exhausted attempt budget closes the run and abandons its candidate root | An author promises that nothing survives a block, so a recovery route re-runs every phase from the start and the checkpoints the run had already earned are discarded | An attempt-limit block leaves the run `active` with its lease released and its root and every checkpoint on disk; `run.yaml#blocked_at` names the phase. Only `devforgeai phase fail --reason <text>` abandons the root, and only `devforgeai promote <run>` moves a byte into the canonical tree, so a blocked run has changed nothing canonical either way. **Decision (`10-sequencer-and-contracts.md` section 5.4):** blocked is `active`, not closed. |

## 10. Success criteria and test cases

### Success criteria

- Triggers on the section 4 positives and on none of the near-misses.
- A `--yolo` run over the fixture leaves exactly `docs/architecture/constitution.md`, `sourcetree.md`, `techstack.md`, `architecture.md`, at least two `design-<topic>.md` files, `.devforgeai/stack.yaml`, and one ADR per decision row in its candidate root, and `devforgeai promote <run>` — run after the user confirms — is what puts exactly those files in the canonical tree. `--yolo` selects options without a human round-trip; it does not promote without one.
- `python3 scripts/check_stack_section.py .devforgeai/stack.yaml --anchor <the anchor techstack.md names>` exits 0 after the run.
- `python3 scripts/check_intended_set.py <path> --template <name>` exits 0 for each of the four named documents and each design document.
- Every decision `option_comparer` recorded has exactly one `design-<topic>.md` and one ADR file.
- `.devforgeai/provenance/adr/` holds one `NNNN-<slug>.md` per decision after promotion, each conforming to the `adr` template header, and no previously existing ADR was rewritten.
- The primary window's transcript shows no read of the PRD or of any architecture document, and no Bash call outside `devforgeai status | phase start | phase fail --reason | validate | promote`.
- Every phase's `changed` set is a subset of its `claimed_paths` and lies inside the run's fence, and no judge phase changes a file inside the candidate root.

### Fixture

`docs/design/examples/fixtures/architect/` is the base fixture. Its exact tree:

| Path | Contents |
|---|---|
| `.devforgeai/state.yaml` | canonical state: `version: 1`, `target: [claude]`, `mode: greenfield`, `slug: tinyapp`, `phase: architect`, `phases.pm.status: done` with the PRD path and its digest, `phases.architect.status: in_progress`, an empty `stories` mapping, and a `runs` mapping with one key `architect-tinyapp` whose value carries `skill: architect`, `mode: copy`, `root: .`, `base_ref: fixture`, `checkpoint: base` and `status: active` |
| `.devforgeai/work/architect-tinyapp/run.yaml` | the per-run enforcement file, standing in for what `devforgeai phase start` writes: `canonical: .`, `phase: option_compare`, `fence: [docs/architecture/**, .devforgeai/stack.yaml, .devforgeai/provenance/adr/**]`, `granted_keys: []`, `attempts` and `max_attempts` at 2 for the nine phases, `gate_policy: {unresolvable_source: BLOCK}`, and a `lease` naming the eval session. The fixture copy is the candidate root, so `candidate.mode` is `copy` and `candidate.root` is the copy itself |
| `docs/PM/tinyapp/prd.md` | a `prd` instance, `slug: tinyapp`, `status: approved`, five `REQ-NNN` rows under `## Requirements` covering a text-slug helper, durable storage of the result, a command-line entry point, a test requirement and a no-dependency requirement; `## Goal`, `## Users`, `## Non-Goals` and `## Success Measures` each one paragraph; `provenance` and `depends_on` naming `docs/brainstorm/tinyapp.md` with real digests of the fixture's own bytes |
| `docs/brainstorm/tinyapp.md` | a `brainstorm` instance with three `IDEA-NNN` rows, present so the PRD's digests resolve |
| `tinyapp/__init__.py` | an empty package marker, so a source tree exists to describe |
| `pyproject.toml` | a minimal project table naming no dependencies, so `packages.allow` has something to scan |

Overlays, copied over the base fixture after it is copied and before the prompt runs:

| Overlay | Change |
|---|---|
| `overlays/eval-2/docs/architecture/techstack.md` | a `techstack` instance holding only an OBSERVED section — `mode: OBSERVED`, one `TS-001` row recording that the deployment window is externally imposed — and no INTENDED section, so `gap_analyzer` has an OBSERVED anchor to compare against |
| `overlays/eval-2/.devforgeai/state.yaml` | the base canonical state file with `mode: brownfield` |
| `overlays/eval-3/docs/PM/tinyapp/prd.md` | the base PRD with `REQ-002` rewritten so it admits either a file-backed store or an in-process store and gives no basis for choosing, so `option_comparer` has an unsettled decision area |

Eval 1 has no overlay. Per-eval changes ship only as these overlay directories; no eval describes a fixture edit in prose.

### evals/evals.json (used verbatim)

```json
{
  "skill_name": "architect",
  "evals": [
    {
      "id": 1,
      "prompt": "Run architect on the tinyapp slug in this repository with the yolo flag. Pick sensible defaults for every decision and write the whole intended set.",
      "expected_output": "constitution.md, sourcetree.md, techstack.md, architecture.md and at least two design documents under docs/architecture/, a stack section in .devforgeai/stack.yaml, one ADR file per decision under .devforgeai/provenance/adr/, and a handoff whose first next step is /plan tinyapp.",
      "expectations": [
        "docs/architecture/constitution.md exists and contains the four headings Principles, Mandates, Constraints and Style",
        "docs/architecture/techstack.md has a stack_section frontmatter value and .devforgeai/stack.yaml contains a section with exactly that anchor name",
        "The stack section defines a test command with a junit_path and defines no build command while compiled is false",
        "At least two files matching docs/architecture/design-*.md exist and each one's topic frontmatter value equals its filename topic segment",
        "At least one file matching .devforgeai/provenance/adr/NNNN-*.md exists and its frontmatter id matches the ADR-NNNN pattern",
        "The final message contains a handoff block whose next step 1 is /plan tinyapp"
      ]
    },
    {
      "id": 2,
      "prompt": "Run architect on tinyapp with the yolo flag. Onboard already recorded what exists; define what it should become.",
      "expected_output": "The intended sections are added beside the observed section already in techstack.md without altering it, and the gap analysis phase returns at least one gap row citing both anchors.",
      "expectations": [
        "The OBSERVED section that was in docs/architecture/techstack.md before the run is present afterwards with its text unchanged",
        "docs/architecture/techstack.md also contains an INTENDED section with its own TS-NNN rows",
        "The gap_analysis phase result contains at least one gap row naming both an intended anchor and an observed anchor",
        "The final message contains a handoff block whose next step 1 is /plan tinyapp"
      ]
    },
    {
      "id": 3,
      "prompt": "Run architect on tinyapp.",
      "expected_output": "The option comparison phase cannot settle the storage decision from the PRD, so the run stops with a request for a human decision and writes no architecture document.",
      "expectations": [
        "No file was created or modified under docs/architecture/",
        "No file was created or modified at .devforgeai/stack.yaml, and none under .devforgeai/provenance/adr/",
        "The option_compare phase result has status needs_user, an empty claimed_paths, and one issues row naming the storage decision as an open item",
        "The final message contains a handoff block whose next steps name docs/PM/tinyapp/prd.md as where to record the decision"
      ]
    }
  ]
}
```

Quick-mode results are generation feedback only: one enabled run per eval and no baseline. They are not runtime conformance evidence, and no section of this spec gates on such evidence; the deferred contract is `12-post-mvp.md#pm-02`.

## 11. Dependencies and compatibility

| Kind | Value |
|------|-------|
| Tools | SKILL.md: `Read`, `Agent`, and a Bash grammar no wider than the five model-callable operations `devforgeai status \| phase start <skill> <arg> \| phase fail --reason \| validate \| promote <run>`. Document writers (`constitution_writer`, `sourcetree_writer`, `techstack_writer`, `architecture_writer`, `design_writer`, `adr_writer`): `Read`, `Grep`, `Glob`, `Bash(devforgeai status)` plus `Edit` and `Write`, which Codex serves as `apply_patch`, denied outside `candidate.root` and outside the phase's fence. Judges (`option_comparer`, `gap_analyzer`, `architect_critic`): the same read set plus `Write` confined to `.devforgeai/work/<run>/evidence/<agent>/`. No `architect` phase grants a stack command key, so no worker carries `Bash(devforgeai run *)`. |
| MCP servers | none |
| Runtime | Python 3.11+ for the three bundled scripts; PyYAML 6+ for frontmatter and `stack.yaml` parsing; `jsonschema` 4+ for `check_stack_section.py`, which validates against `schemas/devforgeai/v1/stack.schema.json` |
| Project commands | none brokered. No `architect` phase declares a `run_keys` entry, so the run brokers no command and the run file carries `granted_keys: []`. The `techstack` phase writes the `build`, `test`, `lint` and `format` keys other skills later name; it names keys and `argv` inside the section it writes and writes no literal command into `techstack.md`. |
| DevForgeAI/Core compatibility | `NOT_APPLICABLE`. `architect` is an anatomy-governed skill, not a Research Core adapter, and names no Research Core version. |
| Other skills | Upstream: `pm` (`prd`), `onboard` (`observed-constraints`, and the OBSERVED `stack` sections), `drift` (`drift-report`). Downstream: `plan`, `dev`, `review`, `qa`, `amend`, `drift`, `analyze`, `skill-validator`. Calls none: every edge is a handoff row (open item OI-7). Must not overlap with `plan` (which owns `epic`, `story`, `sprint` and `skill-spec`), `amend` (which owns changes to an existing architecture document) or `onboard` (which owns the OBSERVED record). |

Deferred dependencies, each naming its `12-post-mvp.md` entry and what the skill does today without it:

| Deferred item | What `architect` does today |
|---|---|
| `12-post-mvp.md#pm-01` | `isolation: required` on eight of the nine workers is the DevForgeAI contract value compiled into the target profile, not Claude's `isolation` frontmatter field. Nothing verifies at runtime that a worker ran in its own window, and the generated adapter is an uninstalled candidate a human accepts. |
| `12-post-mvp.md#pm-04` | A worker's write boundary is the dispatcher's `PreToolUse` deny plus the candidate root, not an operating-system boundary. |
| `12-post-mvp.md#pm-02` | Quick-mode eval results are generation feedback. No success criterion in section 10 is presented as conformance evidence. |
| `12-post-mvp.md#pm-06` | Only `skip` and `quick` eval modes exist. Section 0 rule 5 rejects any third mode name as a spec defect. |
| `12-post-mvp.md#pm-09` | One `stack.yaml` section carries one `commands` block. `techstack_writer` writes one section per anchor and a story pins exactly one; cross-package stories are out of scope. |
| `12-post-mvp.md#pm-10` | Nothing re-runs the architecture checks from a clean checkout, so a document edited outside a run is caught only when `drift` or a later gate re-resolves it. |

Frontmatter values derived from this table:

```yaml
compatibility: "Requires Python 3.11+, PyYAML and jsonschema for the three bundled scripts. Runs inside a repository that already has a .devforgeai/ directory and an approved PRD for the slug; outside one, devforgeai phase start refuses and the skill does nothing."
allowed-tools: "Read Agent Bash(devforgeai status) Bash(devforgeai phase start *) Bash(devforgeai phase fail *) Bash(devforgeai validate) Bash(devforgeai promote *)"
```

## 12. Targets

The generator produces one provider-neutral semantic package and a separate adapter for each selected target when frontmatter, invocation policy, or agent configuration differs. Provider-neutral resources may be shared. Adapter directories are not required to be byte-identical or symlinked.

| Target | Install path | Invocation | Subagents | Notes |
|--------|--------------|------------|-----------|-------|
| claude | `.claude/skills/architect/` | `/architect` with a slug, and `--yolo` for the choose-and-record path | `.claude/agents/architect-<role>.md`: six document writers with `Edit` and `Write` confined to the candidate root, three judges whose `Write` reaches only their run-scoped evidence directories | Provider-specific frontmatter keys (`argument-hint`, `disable-model-invocation`) are compiled into this target's SKILL.md only. `hooks`, `memory`, `background`, `permissionMode` and Claude's own `isolation` are omitted from every profile. |
| codex | `.agents/skills/architect/` plus `.codex/agents/` profiles | `$architect` with a slug, and `--yolo` for the choose-and-record path | `.codex/agents/architect-<role>.toml`: the same nine names, with `apply_patch` in place of `Edit` and `Write` | Portable six-field frontmatter only; policy goes in target-side configuration. |
| both | separate `.claude/skills/architect/` and `.agents/skills/architect/` adapters | as above | as above | Share only provider-neutral resources; validate each adapter independently. |

```yaml
metadata:
  version: "1.0.0"
  devforgeai-spec: "SKILL-SPEC-008"
  devforgeai-target: "both"
  devforgeai-anatomy: "true"
```

Not produced by skill-creator (deferred to DevForgeAI's skill-generator): provider-native `.claude/agents/*.md` and `.codex/agents/*.toml` worker profiles, provider-specific frontmatter keys for the Claude target, and concise `AGENTS.md` sections. Hook definitions are not per-skill: `init` installs the one dispatcher and its provider fragments from `09-hook-dispatcher.md`, and this spec ships none.

A generated package is an uninstalled candidate until those provider-native controls are present and independently validated. Generation or quick-mode success is not installation authority.

## 13. Constraints

- `SKILL.md` under 500 lines and roughly 5,000 tokens, holding only identity, the ordered phase list, the dispatch loop, and the handoff table. Every other instruction lives in `references/<phase>.md`, `agents/<role>.md`, `scripts/` or `assets/`. Nine phases and nine workers make this the largest skill in the roster; splitting a phase into more reference files is the correct response to the line budget.
- References one level deep from whichever file is loaded: `SKILL.md` links to `references/`, `agents/`, `scripts/`, `assets/`; an `agents/*.md` may link to `references/*.md`. Nothing links further.
- Hooks, state writes and phase advancement are not in the skill. `SKILL.md` contains no instruction the gate, the fence or a transition oracle already carries.
- No `README.md` inside the skill directory.
- No XML angle brackets in frontmatter. Description 893 characters; name 9 characters.
- Imperative voice; each step states why it matters. No capitalised absolutes: where a rule is real it is a gate defect class, the fence, a `must_not` line, or an oracle condition, and the text names that mechanism.
- Provide defaults, not menus. `--yolo` selects an option rather than listing the alternatives back to the user; the alternatives are recorded in the design document and the ADR.
- Scripts take arguments, never prompt, and exit `0`, `1` or `2`.
- Skill-specific: no literal build, test, lint or format command appears in `techstack.md`, in a reference file, or in a worker prompt. Commands exist only as `argv` inside a `stack.yaml` section, and every consumer names a key.
- Skill-specific: `.devforgeai/stack.yaml` and every ADR are written inside the candidate root and reach the canonical checkout only at promotion. The stack file is edited in place so every section the run did not derive stays byte-identical; the checkpoint diff is what the sequencer compares to `claimed_paths`.

## 14. Acceptance checks

Run these before reporting done and paste their output:

```bash
# frontmatter and naming (skill-creator's own validator)
python -m scripts.quick_validate ./out/architect     # run from the skill-creator directory
# open-standard validator, if installed
skills-ref validate ./out/architect
# size budget
wc -l ./out/architect/SKILL.md                       # must be < 500
# every worker in section 7d has a prompt file, and no extra
ls ./out/architect/agents/                           # nine files, canonical registry names
# one reference file per phase, plus envelope.md
ls ./out/architect/references/                       # nine phase files plus envelope.md
# scripts answer --help and reject bad usage with exit 2
python3 ./out/architect/scripts/check_prd.py --help
python3 ./out/architect/scripts/check_intended_set.py --help
python3 ./out/architect/scripts/check_stack_section.py --help
# the shipped stack skeleton satisfies the section contract
python3 ./out/architect/scripts/check_stack_section.py ./out/architect/assets/stack.yaml --anchor example
# no leftover placeholders
grep -rnE 'T[O]DO|T[B]D|\{\{' ./out/architect || echo clean
```

Then the wave-4 battery over this specification:

```bash
python3 docs/design/specs/verify.py --only v1,v2,v4
```

For non-Research anatomy skills, DevForgeAI skill-validator additionally checks: all sub-phase kinds present with Gate, Record and Handoff bound to sequencer operations; persona and critic are different files, which for this skill are `option_comparer.md` and `architect_critic.md`; `must_not` present in every agent file; every agent declaring `writes: candidate` or `writes: evidence`, with a `writes: evidence` agent carrying no `Edit` and a `Write` fenced to its run-scoped evidence directory; the SKILL.md Bash grammar is no wider than the five model-callable operations; handoff outcomes cover every status the skill can return, including `could_not_run`.

## 15. Provenance

| Source | Hash | Used for |
|--------|------|----------|
| docs/design/01-skill-anatomy.md#primary-window-contract | see frontmatter | sections 7a, 7b, 10 |
| docs/design/01-skill-anatomy.md#dedicated-templates | see frontmatter | sections 6, 8 |
| docs/design/01-skill-anatomy.md#context-bundle-format | see frontmatter | section 9, OI-11 |
| docs/design/01-skill-anatomy.md#provenance-chain | see frontmatter | sections 6, 9 (OI-6) |
| docs/design/10-sequencer-and-contracts.md#4-per-skill-phase-registry | see frontmatter | sections 7b, 7c, 7d |
| docs/design/10-sequencer-and-contracts.md#5-2-validation-order | see frontmatter | sections 7c, 9 |
| docs/design/10-sequencer-and-contracts.md#5-4-transition-oracles | see frontmatter | sections 7c, 9 |
| docs/design/10-sequencer-and-contracts.md#7-stack-yaml | see frontmatter | sections 2 (R3), 6, 7d, 13 |
| docs/design/10-sequencer-and-contracts.md#6-handoff-envelope | see frontmatter | sections 7a, 7e |
| docs/design/11-artifact-registry.md#1-template-registry | see frontmatter | section 6 |
| docs/design/11-artifact-registry.md#2-artifact-path-patterns | see frontmatter | section 6 |
| docs/design/11-artifact-registry.md#3-depends-on-edges | see frontmatter | sections 2 (R6), 6 |
| docs/design/11-artifact-registry.md#6-known-divergences | see frontmatter | section 9 |
| docs/design/02-skill-roster.md#architect | see frontmatter | sections 1, 2, 5 |
| docs/design/02-skill-roster.md#handoff-decision-tables | see frontmatter | section 7e |
| docs/design/05-subagent-sets.md#sets-per-skill | see frontmatter | sections 7d, 9 |
| docs/design/03-brownfield.md#observed-vs-intended | see frontmatter | sections 2 (R7), 5, 9 |
| docs/design/07-purpose-and-enforcement.md#2-the-problem-in-concrete-terms | see frontmatter | section 2 |
| docs/design/12-post-mvp.md#pm-09 | see frontmatter | sections 9, 11 |
