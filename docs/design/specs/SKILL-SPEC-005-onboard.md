---
template: skill-spec
template_version: 1
id: SKILL-SPEC-005
skill_name: onboard
target: both
status: approved
author: "DevForgeAI plan skill, wave 2 spec author"
date: 2026-09-02
depends_on:
  - source: docs/design/01-skill-anatomy.md#primary-window-contract
    hash: sha256:de7d775e46bd44c52089a3998b114a5ebb5ce6875be3ebf3dca126f5a9bbaa32
    excerpt: "**The model dispatches, the sequencer decides.** For an anatomy-governed skill, the primary window (provider entry adapter + skill orchestration) does light, trivial work only."
  - source: docs/design/01-skill-anatomy.md#the-seven-sub-phases
    hash: sha256:b3c1a62145dc7fd7ef4fb351242f6b67bb0838da1c70cc359b679bfa4986e7d1
    excerpt: "Gate, Slice, Record, and Handoff are deterministic sequencer operations, not workers. Only Work, Write, and Review dispatch an LLM."
  - source: docs/design/10-sequencer-and-contracts.md#4-per-skill-phase-registry
    hash: sha256:37b51ea5748164510e7687527aeab55bc92af9524ee771b293989640cecf8cce
    excerpt: "| onboard | 1 | `code_map` | `code_mapper` | docs | 2 | — | document | — |"
  - source: docs/design/10-sequencer-and-contracts.md#5-4-transition-oracles
    hash: sha256:ffa41b5d270dc260e28fa9f6bdbc855069a6e922d1148c74b25860dba63484dc
    excerpt: "the phase declared `writes: docs` and `changed[]` is non-empty, unless it is marked conditional, in which case an empty change set needs a non-empty `note`; every changed path exists in the root with the bytes the checkpoint will hold"
  - source: docs/design/10-sequencer-and-contracts.md#3-2-defect-to-action-map-as-implemented
    hash: sha256:700e29f7b7eb3b6883d0895d79e3822bf06c32e633eb10b44155761fe4c5ef28
    excerpt: "A document run carries the fixed map `{unresolvable_source: BLOCK}`, because it has no story to declare a wider one."
  - source: docs/design/10-sequencer-and-contracts.md#7-stack-yaml
    hash: sha256:b08220564c5d2c4d1328cea9cbfd1cb793d5ee1fd9ec7c727505006e170e4241
    excerpt: "Producers: `architect`'s `techstack` phase emits the INTENDED sections beside `techstack.md`; `onboard`'s `code_map` phase emits the OBSERVED sections."
  - source: docs/design/11-artifact-registry.md#1-template-registry
    hash: sha256:25886acb1c2963b15938f0c577c3bfd28b9807dd2dd961c59ff2b43fa00b62e2
    excerpt: "| `observed-constraints` | `.devforgeai/skills/onboard/templates/observed-constraints.md` | 1 | `^OBS-[0-9]{3}$` | id, template, template_version, status, scope, evidence | Constraint, Evidence, Why It Is Not Derivable |"
  - source: docs/design/11-artifact-registry.md#2-artifact-path-patterns
    hash: sha256:2d2e97afff50edf6b35bf674b1de217c684d5091361e5f1deae12de52b95fb51
    excerpt: "| `docs/architecture/sourcetree.md#observed`, `techstack.md#observed`, `architecture.md#observed` | `observed-constraints` | onboard | sequencer |"
  - source: docs/design/03-brownfield.md#the-onboard-skill
    hash: sha256:712484fa78944f1d90b6c6ac92ae40d63793d1be6b15bf99a8eee4132f246db5
    excerpt: "Persona: **Archaeologist**. Its job is to describe what exists, never to prescribe."
  - source: docs/design/03-brownfield.md#observed-vs-intended
    hash: sha256:76cdea3c2760b31cc074204be8c244bffb3d582a0ceba60482aa525ce03194a8
    excerpt: "**OBSERVED** — optional sections written by onboard only for admitted facts that cannot be derived from current source, such as rationale, history, timing, or external constraints. Not binding."
  - source: docs/design/02-skill-roster.md#handoff-decision-tables
    hash: sha256:6edc7499ee163453f3be6390b0dda08b3fab885f1399ff944056040596ec3801
    excerpt: "| onboard | pass | `/architect {slug}` |"
  - source: docs/design/05-subagent-sets.md#sets-per-skill
    hash: sha256:9e12f3beb236a025c18d40e741c09ba675bd71d2d87f56e2b205c7556b944bf9
    excerpt: "| onboard | code-mapper, doc-ingester, convention-inferrer, observed-writer, critic |"
---

# Skill Specification: onboard

A stranger with no conversation history must be able to build this skill from this document alone. Every question the generator would otherwise ask is answered below. This document contains no unresolved authoring assumption; every decision the design documents left open is resolved in section 9 with the file and line that forced it.

## 0. Generator instructions

These instructions are addressed to the skill-generating agent (Anthropic's `skill-creator` skill, or DevForgeAI's `skill-generator`). They replace its interview.

### Cold-session prompt

Paste this into a fresh session from the repository root:

```
Use the skill-creator skill to build the skill specified in docs/design/specs/SKILL-SPEC-005-onboard.md.
Follow its section 0 exactly. Output directory: ./out. Eval mode: quick.
```

### Rules for the generator

1. **Do not interview.** Sections 1-13 pre-answer every Capture Intent and Interview question: what the skill enables, when it triggers, its output format, its test cases, its edge cases, its input and output formats, its example files, its success criteria, and its dependencies. Treat this document as the conversation history you are told to harvest from.
2. **Test prompts are pre-approved.** Use section 10 verbatim as `evals/evals.json`. Do not ask whether they look right.
3. **Trigger queries are pre-approved.** Use section 4 verbatim as the trigger eval set. Do not ask for sign-off.
4. **No human review loop.** Do not wait for the user to review results. Proceed to the next stage on your own.
5. **Eval mode** is given in the prompt and is one of two values:
   - `skip`: write the skill only. Do not create `evals/`, do not run test prompts, do not optimize the description.
   - `quick`: write the skill and `evals/evals.json`. For each eval copy `docs/design/examples/fixtures/onboard/` without `overlays/` to `./out/onboard-workspace/fixture-<eval-id>/`, copy `overlays/eval-<id>/` over it when one exists, run each test prompt once with the skill (no baseline run), grade with the grader agent, write `grading.json`, and report pass or fail per expectation in your final message. Do not run the description-optimization loop. Run the eval executions and the grader as foreground Agent-tool subagents, never as background shell processes, and do not end your turn until every `grading.json` exists: a headless session terminates when the top-level turn ends and orphans anything still running.
   - Any other mode name is a spec defect. The deferred interactive mode is `12-post-mvp.md#pm-06`.
6. **Output location** is given in the prompt. Create `./out/onboard/`. Do not write anywhere else except the `onboard-workspace/` sibling that eval runs require.
7. **On ambiguity, stop before output.** If this spec is still `draft`, contains an unresolved authoring assumption, omits a section, contradicts itself, or leaves a decision this document does not make, do not guess and do not write candidate skill files. End with a list titled `SPEC GAPS` naming each section and question. The spec author fixes and approves the spec before re-running.
8. **Fidelity over creativity.** Use the description in section 3 verbatim. Use each worker contract in section 7d verbatim as the body of `agents/<role>.md`, adding only the Role / Inputs / Process / Output framing the grader agent in skill-creator uses, where the Process text is that phase's reference file section from 7f. Do not add steps, tools, or behaviours this spec does not mention.
9. **Finish with the acceptance checks** in section 14 and include their output in your final message.

## 1. Identity

| Field | Value |
|-------|-------|
| name | `onboard` (kebab-case, 7 characters, equals the directory name, no provider prefix) |
| title | Brownfield Repository Onboarding |
| purpose | Record what a repository already is, as an applied OBSERVED `.devforgeai/stack.yaml` plus cited OBSERVED constraint sections, so every later phase reads evidence instead of guessing. |
| category | devforgeai-phase |
| version | 1.0.0 (skill-package version written to `metadata.version`; not the DevForgeAI or Research Core version) |

## 2. Problem and requirements

**Without this skill:** an agent asked to adopt an existing repository invents the parts it cannot see. It reads a `pyproject.toml`, decides the project "probably uses pytest", writes that guess into an architecture document, and every later phase treats the guess as fact because it is now written down. It copies README prose into a constitution, so a claim that was never true of the code becomes binding. It has no way to distinguish a fact that is readable from source today from a constraint that exists only in someone's head or in an operations policy, so both rot at the same rate and neither can be re-checked. When the test command it guessed is wrong, the failure surfaces three phases later, inside a story, as an infrastructure failure with no evidence trail.

| ID | Kind | Requirement |
|----|------|-------------|
| R1 | explicit | Write `.devforgeai/stack.yaml` from values that are literally present in the repository's manifests and configuration; report every required value that is absent rather than supplying one (`03-brownfield.md` sub-phase 1: "A command, language, or package-manager value not explicitly present is reported as unknown, never guessed"). |
| R2 | explicit | Write OBSERVED sections only for facts that cannot be derived from current source; source-derivable facts stay path-and-digest citations and are not copied (`03-brownfield.md#observed-vs-intended`). |
| R3 | explicit | Admit README, ADR, wiki and CONTRIBUTING material only through a sealed Research dossier, citing RUN plus Source, Evidence and Claim ids and the sealed manifest digest; a bare hash is not a provenance reference (`03-brownfield.md` "Ingested docs as research"). |
| R4 | implicit | Each of the four document-writing phases writes its own file inside the run's candidate root and returns one `devforgeai.worker-result/v1` receipt naming what it wrote; the critic phase changes nothing inside it, writing only its findings file into its own run-scoped evidence directory. The sequencer derives the real change set from the checkpoint diff, validates it against the claim, the fence and the template header, checkpoints, and promotes the root at Handoff. |
| R5 | implicit | The primary window stays in the canonical checkout, reads `.devforgeai/state.yaml` and nothing else, dispatches by path plus the `devforgeai status` block, and prints the handoff the sequencer rendered (`01-skill-anatomy.md#primary-window-contract`). |
| R6 | implicit | A contradiction between an ingested document and the code it describes is recorded as a conflict row, not averaged away (`03-brownfield.md`: "both observations remain recorded and the contradiction routes to the owning phase"). |
| R7 | discovered | Every `writes: docs` phase must produce at least one file or the `document` oracle fails the transition (`examples/hooks/devforgeai.py` `check_document`). Four of onboard's five phases declare `writes: docs`, so each owns exactly one fenced path and returns `needs_user` when it has nothing admissible to write. Resolved in section 9, row G-1. |
| R8 | discovered | `.devforgeai/stack.yaml` is sequencer-owned in the canonical checkout, and exactly one pair may write it: skill `onboard`, phase `code_map` (`examples/hooks/policy.py` `PRODUCER_EXCEPTIONS`). The write happens inside the candidate root, the sequencer validates the written bytes against `schemas/devforgeai/v1/stack.schema.json` at ingest before checkpointing, and the file reaches the canonical checkout only by promotion. `phase start` counts the path as a fence member, so a second run touching it is refused `FENCE_OVERLAP`. |
| R9 | discovered | `code_mapper` is dispatched by both `onboard` and `drift`; `onboard` owns the worker file and `drift` reuses it (`11-artifact-registry.md` section 6, divergence 1). |

## 3. Description

```yaml
description: >
  Map an existing repository before DevForgeAI plans anything: propose the OBSERVED
  .devforgeai/stack.yaml from the manifests and configuration that are actually present,
  and record only the constraints that cannot be read from source - rationale, history,
  timing, external obligations - as cited OBSERVED sections of sourcetree.md, techstack.md
  and architecture.md. Use this skill whenever a repository already has code and DevForgeAI
  state says mode brownfield, whenever someone asks what a codebase does today, whenever
  build, test or lint commands must be recorded from evidence rather than guessed, or
  whenever README, ADR or wiki material has to enter the provenance chain. Do NOT use it to
  decide what the system should become (that is architect), to compare docs against code
  after adoption (that is drift), or to install DevForgeAI (that is init).
```

Character count: 854 / 1024.

## 4. Trigger set

```json
[
  {"query": "we just installed devforgeai in the ledger repo, map what is already here before we plan anything", "should_trigger": true},
  {"query": "/onboard", "should_trigger": true},
  {"query": "this is a six year old python service with no architecture docs. work out what the build and test commands actually are and record them", "should_trigger": true},
  {"query": "init said mode: brownfield and the next step is onboarding. go ahead", "should_trigger": true},
  {"query": "figure out our stack.yaml from pyproject.toml and setup.cfg, and dont guess anything that isnt in there", "should_trigger": true},
  {"query": "the README has a load of history and a release-approval rule in it. get those recorded with citations before architect runs", "should_trigger": true},
  {"query": "record what this repo actually does today, not what we wish it did", "should_trigger": true},
  {"query": "we're adopting devforgeai on an existing codebase. whats step 2? just do it", "should_trigger": true},
  {"query": "before /architect I want the observed state of this repository written down with evidence", "should_trigger": true},
  {"query": "write the architecture document for the new service we are about to build", "should_trigger": false},
  {"query": "the techstack doc says Dapper but the code uses EF Core, show me where they diverged", "should_trigger": false},
  {"query": "/init --target both", "should_trigger": false},
  {"query": "summarise the README for me in three bullets", "should_trigger": false},
  {"query": "add pytest to this project and set up a tests folder with a conftest", "should_trigger": false},
  {"query": "our constitution mandates tdd, generate the dev skill variant for it", "should_trigger": false},
  {"query": "brainstorm ideas for the ledger v2 rewrite", "should_trigger": false},
  {"query": "sprint-002 is finished, write the retro", "should_trigger": false},
  {"query": "re-slice STORY-014, the techstack section it quotes has moved", "should_trigger": false}
]
```

## 5. Use cases

### UC-1: Existing code, an admitted README, one non-derivable rule
- **User says:** "we just installed devforgeai here. the README has our release-approval rule in it, and there is a sealed research run for it already. onboard this repo"
- **Steps:** 1. The adapter reads `slug` from `.devforgeai/state.yaml` and calls `devforgeai phase start onboard ledger`. 2. `code_mapper` proposes `.devforgeai/stack.yaml` with one OBSERVED anchor built from `pyproject.toml`. 3. `doc_ingester` reads the sealed dossier under `docs/research/ledger/runs/RUN-000001/` and proposes the OBSERVED section of `docs/architecture/architecture.md` with one `OBS-001` entry citing RUN, Source, Evidence and Claim ids and the sealed manifest digest. 4. `convention_inferrer` and `observed_writer` propose their sections or return `needs_user` when nothing non-derivable remains. 5. `onboard_critic` reports any entry whose statement is readable at a cited path.
- **Result:** `.devforgeai/stack.yaml` is applied and schema-valid; `docs/architecture/architecture.md` carries one cited OBSERVED constraint; no README sentence is copied into any binding document; the handoff names the phase reached and the next command.

### UC-2: Existing code, no external documents
- **User says:** "/onboard"
- **Steps:** 1. `code_mapper` proposes the stack section. 2. `doc_ingester` globs for candidate documents, finds none, and returns `needs_user` with a note naming what it searched.
- **Result:** the stack section is applied, no OBSERVED section is written, the run is closed with a `REQUIRE_HUMAN` handoff, and the user proceeds to `/architect ledger` knowing that onboard admitted nothing.

### UC-3: The runner is not declared anywhere
- **User says:** "onboard this repo and record the commands"
- **Steps:** 1. `code_mapper` reads every manifest and configuration file, finds no test-runner declaration and no JUnit output path, and returns `needs_user` listing the missing keys and the files it searched.
- **Result:** no `.devforgeai/stack.yaml` is written, nothing is guessed, and the handoff carries the missing keys so a human states them once.

## 6. Inputs and outputs

### Inputs
| Input | Format | Example file | Required |
|-------|--------|--------------|----------|
| project slug | string, the `devforgeai phase start` argument, taken from `state.yaml` `slug` | `.devforgeai/state.yaml` | yes |
| run file and context bundle | YAML and JSON written by the sequencer at `devforgeai phase start`: `phase`, `fence`, `granted_keys`, `attempts`, `max_attempts`, `lease`, `gate_policy`, plus the sliced context | `.devforgeai/work/<run>/run.yaml`, `.devforgeai/work/<run>/context.json` | yes |
| repository manifests and configuration | ecosystem-native (`pyproject.toml`, `requirements*.txt`, `package.json`, `*.csproj`, `Directory.Packages.props`, `go.mod`, `Cargo.toml`, `pom.xml`, `build.gradle*`, `Gemfile`, `composer.json`, `setup.cfg`, `tox.ini`, `Makefile`) | `docs/design/examples/fixtures/onboard/pyproject.toml` | yes |
| repository source tree | any | `docs/design/examples/fixtures/onboard/ledger/accounts.py` | yes |
| sealed Research dossier | directory of typed records governed by `framework/skills/research/` | `docs/research/ledger/runs/RUN-000001/` | no; without one, no external document may be admitted |
| current OBSERVED files | markdown, `observed-constraints` template | `docs/architecture/architecture.md` | no; absent on a first run |

### Outputs
| Output | Format | Location | Template |
|--------|--------|----------|----------|
| OBSERVED stack section | YAML mapping of anchor name to section | `.devforgeai/stack.yaml` | `stack` (`.devforgeai/skills/architect/templates/stack.yaml`; owned by architect, produced by architect and onboard) |
| OBSERVED architecture constraints | markdown section | `docs/architecture/architecture.md#observed` | `observed-constraints` (`assets/observed-constraints.md`) |
| OBSERVED layout constraints | markdown section | `docs/architecture/sourcetree.md#observed` | `observed-constraints` |
| OBSERVED stack constraints | markdown section | `docs/architecture/techstack.md#observed` | `observed-constraints` |
| phase result and report | JSON and markdown, written by the sequencer | `.devforgeai/work/onboard-<slug>/<phase>-result.json`, `<phase>-report.md` | none |
| handoff | JSON, written by the sequencer; the printed block is its rendering | `.devforgeai/work/onboard-<slug>/handoff.json` | `handoff` |

`observed-constraints` header keys, from `11-artifact-registry.md` section 1: `template: observed-constraints`, `template_version: 1`, `accepts_versions: [1]`, `required_frontmatter: [id, template, template_version, status, scope, evidence]`, `required_sections: ["Constraint", "Evidence", "Why It Is Not Derivable"]`, `id_pattern: "^OBS-[0-9]{3}$"`, and the standard forbidden-text list recorded in that section.

### Output template

The OBSERVED section of one architecture document. `scope` is `architecture`, `sourcetree` or `techstack`, matching the file the section lives in.

```markdown
## OBSERVED
<!-- template: observed-constraints  template_version: 1  status: OBSERVED  scope: architecture -->

### Citations
| Fact | Source | Digest |
|------|--------|--------|
| package layout | ledger/__init__.py#L1-L4 | sha256:1f0c... |
| declared dependencies | pyproject.toml#L1-L9 | sha256:9ab3... |

### OBS-001

#### Constraint
Releases are approved by the operations team during a named maintenance window.

#### Evidence
RUN-000001; SRC-000001; EVD-000001; CLM-000001; sealed manifest sha256:4c7e...

#### Why It Is Not Derivable
No file in the repository encodes release approval or its timing; the obligation
is external to the code and cannot be recovered by reading it.
```

How the `observed-constraints` header keys map onto that rendering: the section comment carries `template`, `template_version`, `status` and `scope`; each entry's `### OBS-NNN` heading carries `id`; and the entry's `#### Evidence` subsection is `evidence`. `scripts/check_observed.py` matches the comment keys and the per-entry headings against the template header on that mapping.

The stack section `code_mapper` writes, one anchor per ecosystem present:

```yaml
observed-python:
  version: 1
  compiled: false
  package_manager: pip
  manifests: [pyproject.toml]
  commands:
    test:
      argv: [python3, -m, pytest, -q, --junitxml=.devforgeai/work/junit.xml]
      junit_path: .devforgeai/work/junit.xml
      timeout_s: 600
  test_glob: tests/**
  test_layout: tests-beside-package
  runner_probe: {argv: [python3, -m, pytest, --version], exit_ok: 0}
  packages: {allow: [click, pytest], deny: []}
  extractors:
    - {paths: [pyproject.toml], regex: '^\s*"([A-Za-z0-9._-]+)'}
  forbidden_imports: []
```

### Return envelope (DevForgeAI-anatomy skills only)

One schema, both providers: `devforgeai.worker-result/v1`, normative in `schemas/devforgeai/v1/worker-result.schema.json`. A worker's final message is exactly this object, with no Markdown fence and no surrounding prose. A document writer has already written its file inside the candidate root when it returns; the receipt claims what it wrote. The critic changes nothing inside the candidate root and claims nothing; it writes its findings file into `.devforgeai/work/<run>/evidence/onboard_critic/` and names it in `evidence_refs`.

```yaml
schema: devforgeai.worker-result/v1
run: "onboard-ledger"
skill: "onboard"
phase: "code_map"
agent: "code_mapper"
status: pass | fail | needs_user | could_not_run
reason_code: runner_missing | timeout | network | hook_fault   # required only when status is could_not_run
candidate: {id: "onboard-ledger", input_checkpoint: "base"}
claimed_paths: [".devforgeai/stack.yaml"]    # root-relative, at most 64; empty on any non-pass status
evidence_refs: [".devforgeai/stack.yaml"]    # at most 16
note: "one anchor written from pyproject.toml; no build key, the section is not compiled"
issues: [{id, kind, text}]                   # at most 10
```

At `devforgeai ingest-result` the sequencer derives `changed[{path, blob_sha256, kind}]` from the checkpoint diff, refuses when `changed` is not a subset of `claimed_paths` (`UNCLAIMED_CHANGE`) or a path is outside the fence, validates the written file against its template header, runs the transition oracle inside the root, writes `<phase>-result.json` with `changed` and the checkpoint ref, releases the lease and advances. `next` requires `status: fail` plus a registry `rewind_to`; no onboard phase declares one, so the key is never present. Unknown keys refuse the receipt.

`gate_policy` (`BLOCK`, `REQUIRE_HUMAN`, `WARN`, `OFF`) is a defect-to-action map declared in the consumed artifact, never a status returned here. A document run carries the fixed map `{unresolvable_source: BLOCK}`.

## 7. Procedure

### 7a. Steps (the body of `SKILL.md`)

1. Parse the invocation. `/onboard` takes no positional argument, so read `slug` from `.devforgeai/state.yaml` and use it as the `devforgeai phase start` argument — why: the sequencer's grammar requires one, and the run id `onboard-<slug>` is the evidence directory every later command resolves. When `state.yaml` holds no `slug`, use the repository root directory name and say so in the dispatch note, because a run still needs a stable evidence home.
2. Call `devforgeai phase start onboard <slug>`. It runs the document gate, opens the run's candidate root, writes the run file and `context.json`, and prints the first phase, its worker and the status block — why: the phase order, the fence, the candidate root and the attempt budget are the sequencer's, and reading them from its output keeps this window free of design state.
3. Run `devforgeai status` and paste its block into the dispatch. The block names `run`, `candidate.root`, `phase`, `fence` and `granted_keys` — why: a worker writes inside the candidate root and cannot resolve it from the canonical tree, and this block is the one thing the dispatch carries that is not a path or an id.
4. Dispatch the worker the sequencer named, in a fresh context window, with that block, the run id, the phase name and the fence paths. Pass paths, ids and the status block only — why: anything else pasted here is duplicated into the worker's window and into this one, and the worker can read the path itself.
5. Read the worker's receipt. On `pass`, continue at step 4 with the next phase the sequencer names after its transition. On `fail`, dispatch the same phase's worker again with the sequencer's problem rows, until the sequencer stops naming that phase.
6. On `needs_user`, stop dispatching — why: the sequencer blocks the run at that phase on the first ask and writes a `REQUIRE_HUMAN` handoff; a second dispatch would open nothing and answer nobody. The run is not closed: it stays `active` with `run.yaml#blocked_at` naming the phase, and `/onboard` resumes it there once the human has acted.
7. On `could_not_run`, stop dispatching. The sequencer records the reason code and selects the repair route.
8. Print the handoff block the sequencer rendered, unchanged. When it reports the run `ready_to_promote` and the user asks for the promotion, call `devforgeai promote <run>` — why: promotion moves the candidate root's bytes into the canonical checkout under the lock, and a `REQUIRE_HUMAN` block is the only state in which the model may ask for it.

The primary window stays in the canonical checkout and never opens a manifest, a source file, an architecture document or a dossier record. Its Bash grammar is exactly `devforgeai status`, `devforgeai phase start <skill> <arg>`, `devforgeai phase fail --reason <text>`, `devforgeai validate` and `devforgeai promote <run>`.

### 7b. Sub-phases and workers

| # | Sub-phase | Performed by | Writes | Isolation |
|---|-----------|--------------|--------|-----------|
| 0 | Gate | sequencer: `devforgeai phase start onboard <slug>`, which also opens the candidate root | sequencer | n/a |
| 1 | Slice | sequencer: a step inside `phase start` that resolves the incoming artifact's hashed bundle into `.devforgeai/work/<run>/context.json`. No worker (section 9, row G-2) | sequencer | n/a |
| 2 | Work: `code_map` | worker: `code_mapper` | candidate | required |
| 3 | Work: `doc_ingest` | worker: `doc_ingester` | candidate | required |
| 4 | Work: `convention_infer` | worker: `convention_inferrer` | candidate | required |
| 5 | Write: `observed_write` | worker: `observed_writer` | candidate | required |
| 6 | Review: `critic` | worker: `onboard_critic` | evidence | required |
| 7 | Record | sequencer: `devforgeai phase next` | sequencer | n/a |
| 8 | Handoff | sequencer: `devforgeai phase next`, which on the last passing transition marks the run `ready_to_promote` and renders the first block, a `REQUIRE_HUMAN` handoff naming `devforgeai promote <run>`; that command, run only after the user confirms in the session, renders the second | sequencer | n/a |

Each worker becomes `agents/<role>.md`, named for the canonical registry worker name. The four document writers are producers: they write their file inside the candidate root and the receipt claims it. `onboard_critic` is a judge: it reads what the run wrote, repairs nothing, and writes only its findings file into its own run-scoped evidence directory. A judge's `Write` is confined to its own run-scoped evidence directory, `.devforgeai/work/<run>/evidence/<agent>/`, which is gitignored, lies outside the candidate root, and is never promoted. Its findings file lives there and is named in `evidence_refs`; `issues[]` stays the bounded summary the handoff carries. Nothing a judge writes can reach the checkpoint diff, so its `claimed_paths` is empty on every status. Persona and critic are different files with different prompts.

The `Isolation` column is the DevForgeAI worker-contract value compiled into the generated target profile, not Claude's `isolation` frontmatter field. The framework does not use Claude's worktree isolation or `EnterWorktree`: both fork from HEAD, and the run's phases build linearly on one candidate root instead.

### 7c. Evidence and gate table

`<run>` is `onboard-<slug>`. Attempt budget is 2 for every phase (`10-sequencer-and-contracts.md` section 4).

| phase | worker | deterministic gate check | gate_policy | evidence file | transition oracle |
|---|---|---|---|---|---|
| `code_map` | `code_mapper` | run gate: no run is already active, `onboard` is a known `kind: document` skill, every fence entry is repository-relative, free of `..`, and either not sequencer-owned or produced by this skill (`.devforgeai/stack.yaml` passes only through the producer exception), and no active or `ready_to_promote` run's fence overlaps this one (`FENCE_OVERLAP` counts `.devforgeai/stack.yaml`). Ingest validation: `changed` derived from the checkpoint diff is a subset of `claimed_paths` (`UNCLAIMED_CHANGE` otherwise), every changed path is under `candidate.root` and inside the fence, and the written `.devforgeai/stack.yaml` is parsed and validated section by section against `schemas/devforgeai/v1/stack.schema.json` plus the same contract checks the story gate applies, before the checkpoint is taken | document run map `{unresolvable_source: BLOCK}`; `test_runner_missing` is not consulted because this phase brokers no command key | `.devforgeai/work/<run>/code_map-result.json`, `code_map-report.md` | `document`: the phase changed at least one file inside the fence and `.devforgeai/stack.yaml` exists in the candidate root at the checkpoint |
| `doc_ingest` | `doc_ingester` | ingest validation: the single changed path is `docs/architecture/architecture.md`, under the candidate root, inside the fence, not sequencer-owned, and claimed; the file is validated against the `observed-constraints` template header before checkpointing; the whole root is rescanned against the stack policy and the checkpoint is refused on any violation | `{unresolvable_source: BLOCK}` | `.devforgeai/work/<run>/doc_ingest-result.json`, `doc_ingest-report.md` | `document`: at least one file changed and `docs/architecture/architecture.md` present in the root |
| `convention_infer` | `convention_inferrer` | ingest validation as above with the single path `docs/architecture/sourcetree.md`; `claimed_paths` carries at most 64 entries and holds no duplicate | `{unresolvable_source: BLOCK}` | `.devforgeai/work/<run>/convention_infer-result.json`, `convention_infer-report.md` | `document`: at least one file changed and `docs/architecture/sourcetree.md` present in the root |
| `observed_write` | `observed_writer` | ingest validation as above with the single path `docs/architecture/techstack.md`; the receipt carries at most 16 `evidence_refs` and at most 10 issue rows | `{unresolvable_source: BLOCK}` | `.devforgeai/work/<run>/observed_write-result.json`, `observed_write-report.md` | `document`: at least one file changed and `docs/architecture/techstack.md` present in the root |
| `critic` | `onboard_critic` | ingest validation: the registry declares the phase `writes: none` and the worker header `writes: evidence`, so `claimed_paths` is empty and any change inside the candidate root refuses the receipt as `UNCLAIMED_CHANGE`; the dispatcher allows this worker's writes only under `.devforgeai/work/<run>/evidence/onboard_critic/` and denies every other path at `PreToolUse`; the phase grants no command key, so a brokered run is refused for want of the hook marker | `{unresolvable_source: BLOCK}` | `.devforgeai/work/<run>/critic-result.json`, `critic-report.md`, then `handoff.json` | `report_only`: no file outside the fence changed since the input checkpoint and the whole-root package and import policy holds. On pass this is the last phase: the run is marked `ready_to_promote` and a `REQUIRE_HUMAN` handoff is written whose one forward command is `devforgeai promote <run>`; the `pass` handoff is the second block, written by that command once the user asks for it |

Promotion is not part of the run's phases. The last passing `devforgeai phase next` marks the run `ready_to_promote` and writes a `REQUIRE_HUMAN` handoff whose one forward command is `devforgeai promote <run>`; the candidate root and its checkpoints stay on disk and no canonical byte moves. The compiled `SKILL.md` runs that command only after the user confirms in the session, and it is that command — never `phase next` — that merges the candidate root into the canonical checkout under `.devforgeai/lock`, refusing on `STALE_BASE` when canonical HEAD has moved past the run's pinned `base_ref`, on `DIRTY_TARGET` when a dirty canonical file is among the changed paths, and on `MERGE_CONFLICT` when the sequencer's rebase cannot replay the run. A refusal moves no canonical byte and leaves the run `ready_to_promote` with its root intact, so the command can be run again once the named cause is settled. The second handoff block is written by a promotion that succeeded, and its `next` is the section 7e row for the run's outcome. Each refusal is a handoff row in section 7e; none of them is a model decision.

Two limits this table does not overstate. Every `devforgeai phase start` defect is a refusal whatever a declared policy value says, and only `test_runner_missing` changes behaviour, at transition time (`10-sequencer-and-contracts.md` section 3.2). The document gate checks the fence; template conformance of a consumed document artifact, and re-resolution of the citation digests onboard writes, are not checked at `devforgeai phase start` today. The story gate does re-resolve every `provenance` and `context` entry and `commands.hash`, so a story that quotes an OBSERVED section is checked when dev enters; `scripts/check_observed.py` is the same check for the document path, and today it runs as a human or continuous-integration step (section 9, row G-4).

### 7d. Worker contracts

Each block is the body of `agents/<role>.md` and compiles to one provider profile per target. `name` is the canonical registry worker name, which is what a hook receives as `agent_type`; the compiled filename carries the skill prefix so two skills' profiles cannot collide. `tools` are the Claude names; on Codex `apply_patch` stands in for `Edit` and `Write`, and the rest are the Codex equivalents of the same read surface. `model: inherit` keeps the worker on the session's model, which is what the terminal-only constraint leaves available. No onboard phase grants a stack command key, so no worker here carries `Bash(devforgeai run *)`. Claude-only frontmatter — `hooks`, `memory`, `background`, `permissionMode`, and Claude's own `isolation` — is omitted from every profile: the enforcement chain is the one dispatcher `init` installs, and the run's own candidate root is the isolation.

```yaml
name: code_mapper
description: Dispatch this worker at the code_map phase to write the OBSERVED .devforgeai/stack.yaml section from the values the repository's manifests and configuration actually state.
skill: onboard
writes: candidate
model: inherit
tools: [Read, Grep, Glob, Bash(devforgeai status), Edit, Write]
skills: []
compiled_to: [.claude/agents/onboard-code_mapper.md, .codex/agents/onboard-code_mapper.toml]
responsibility: Write the OBSERVED sections of `.devforgeai/stack.yaml` inside the candidate root from values stated in the repository's manifests and configuration, and report every required key no file states.
inputs:
  - the devforgeai status block pasted into the dispatch, which names run, candidate.root, phase, fence and granted_keys
  - .devforgeai/work/<run>/context.json, the bundle the sequencer sliced at phase start
  - the repository's manifest and configuration files under the candidate root, located by glob
  - .devforgeai/stack.yaml inside the candidate root, when it exists, for the anchors to carry forward
outputs:
  - .devforgeai/stack.yaml, written inside the candidate root and named in claimed_paths and evidence_refs
  - the cited repository facts, as the section's own keys plus an issues row per fact a caller asked for that no file states
must_not:
  - write a value for a stack key that no manifest or configuration file states
  - write inside the candidate root when dispatched by drift, whose phase grants only the run-scoped evidence directory
  - fill run, skill or phase from anything but the ids in the status block, since this profile serves more than one skill
  - drop or rewrite an anchor this phase did not derive
  - copy a manifest value into a Markdown file
  - write outside the candidate root, or outside the run's fence inside it
tools_codex: [Read, Grep, Glob, Bash(devforgeai status), apply_patch]
isolation: required
returns: devforgeai.worker-result/v1
body:
  job: Write the OBSERVED stack section from what the manifests state, and say which required keys nothing states.
  inputs: The list above, read under the candidate root; nothing outside it is opened.
  rules: references/code_map.md, the key-by-key sourcing table, and the must_not list.
  receipt: One devforgeai.worker-result/v1 object; claimed_paths and evidence_refs both name .devforgeai/stack.yaml on pass, and both are empty on needs_user.
```

```yaml
name: doc_ingester
description: Dispatch this worker at the doc_ingest phase to write the OBSERVED section of architecture.md from the claims a sealed Research dossier carries.
skill: onboard
writes: candidate
model: inherit
tools: [Read, Grep, Glob, Bash(devforgeai status), Edit, Write]
skills: []
compiled_to: [.claude/agents/onboard-doc_ingester.md, .codex/agents/onboard-doc_ingester.toml]
responsibility: Write the OBSERVED section of `docs/architecture/architecture.md` inside the candidate root from constraints carried by a sealed Research dossier, citing each one by RUN, Source, Evidence and Claim id and the sealed manifest digest.
inputs:
  - the devforgeai status block pasted into the dispatch
  - .devforgeai/work/<run>/context.json
  - docs/research/<slug>/runs/ (sealed dossier directories, by path)
  - docs/architecture/architecture.md inside the candidate root, for the entries to carry forward
  - assets/observed-constraints.md (the template header and section order)
  - the source paths a candidate claim describes, for the conflict rows
outputs:
  - docs/architecture/architecture.md, written inside the candidate root and claimed
  - one OBS entry per admitted claim, each carrying its RUN, Source, Evidence and Claim ids and the sealed manifest digest on its Evidence line
  - the conflict rows, written into the entry and into the note, one per admitted claim that contradicts the source path it describes
must_not:
  - admit a document that no sealed dossier covers
  - write an OBS entry whose statement is readable at a source path, rather than a citation to that path
  - reconcile a conflict between an admitted claim and the code it describes
  - change any path other than docs/architecture/architecture.md
  - write outside the candidate root, or outside the run's fence inside it
tools_codex: [Read, Grep, Glob, Bash(devforgeai status), apply_patch]
isolation: required
returns: devforgeai.worker-result/v1
body:
  job: Write the architecture document's OBSERVED section from sealed dossier claims, keeping every conflict on the record.
  inputs: The list above, read under the candidate root.
  rules: references/doc_ingest.md, the admission rule, and the must_not list.
  receipt: One devforgeai.worker-result/v1 object; on pass claimed_paths is exactly docs/architecture/architecture.md, on needs_user it is empty and the note carries the research invocation.
```

```yaml
name: convention_inferrer
description: Dispatch this worker at the convention_infer phase to write the OBSERVED section of sourcetree.md, separating layout facts a reader can obtain from constraints a reader cannot.
skill: onboard
writes: candidate
model: inherit
tools: [Read, Grep, Glob, Bash(devforgeai status), Edit, Write]
skills: []
compiled_to: [.claude/agents/onboard-convention_inferrer.md, .codex/agents/onboard-convention_inferrer.toml]
responsibility: Partition the observed layout, ownership and naming facts into source-derivable citations and non-derivable constraints, and write the OBSERVED section of `docs/architecture/sourcetree.md` inside the candidate root from that partition.
inputs:
  - the devforgeai status block pasted into the dispatch
  - .devforgeai/work/<run>/context.json
  - .devforgeai/work/<run>/code_map-result.json and doc_ingest-result.json (prior phase results, by path)
  - the repository tree under the candidate root, by glob
  - docs/architecture/sourcetree.md inside the candidate root, for the entries to carry forward
  - assets/observed-constraints.md
outputs:
  - docs/architecture/sourcetree.md, written inside the candidate root and claimed
  - the Citations table, one row per derivable fact with its path, anchor and digest
  - one OBS entry per non-derivable constraint, each stating what reading cannot recover
must_not:
  - promote a fact that is readable at a repository path into an OBS entry
  - state an ownership or naming rule no admitted source states
  - change any path other than docs/architecture/sourcetree.md
  - write outside the candidate root, or outside the run's fence inside it
tools_codex: [Read, Grep, Glob, Bash(devforgeai status), apply_patch]
isolation: required
returns: devforgeai.worker-result/v1
body:
  job: Write the sourcetree document's OBSERVED section, citing what a reader can obtain and recording only what a reader cannot.
  inputs: The list above, read under the candidate root.
  rules: references/convention_infer.md, the derivability partition, and the must_not list.
  receipt: One devforgeai.worker-result/v1 object; on pass claimed_paths is exactly docs/architecture/sourcetree.md, on needs_user it is empty and the note carries the derivable count.
```

```yaml
name: observed_writer
description: Dispatch this worker at the observed_write phase to write the OBSERVED section of techstack.md for the admitted stack constraints the stack section cannot express.
skill: onboard
writes: candidate
model: inherit
tools: [Read, Grep, Glob, Bash(devforgeai status), Edit, Write]
skills: []
compiled_to: [.claude/agents/onboard-observed_writer.md, .codex/agents/onboard-observed_writer.toml]
responsibility: Write the OBSERVED section of `docs/architecture/techstack.md` inside the candidate root for the admitted stack constraints that no manifest or configuration file encodes.
inputs:
  - the devforgeai status block pasted into the dispatch
  - .devforgeai/work/<run>/context.json
  - .devforgeai/work/<run>/code_map-result.json, doc_ingest-result.json and convention_infer-result.json (by path)
  - docs/architecture/techstack.md inside the candidate root, for the entries to carry forward
  - assets/observed-constraints.md
outputs:
  - docs/architecture/techstack.md, written inside the candidate root and claimed
  - one OBS entry per admitted constraint, each with its scope and its evidence reference
must_not:
  - restate a value already carried by the stack section this run wrote
  - mark an OBSERVED entry as binding on a later phase
  - change any path other than docs/architecture/techstack.md
  - write outside the candidate root, or outside the run's fence inside it
tools_codex: [Read, Grep, Glob, Bash(devforgeai status), apply_patch]
isolation: required
returns: devforgeai.worker-result/v1
body:
  job: Write the techstack document's OBSERVED section for constraints the stack section cannot hold.
  inputs: The list above, read under the candidate root.
  rules: references/observed_write.md, the earns-its-place test, and the must_not list.
  receipt: One devforgeai.worker-result/v1 object; on pass claimed_paths is exactly docs/architecture/techstack.md, on needs_user it is empty.
```

```yaml
name: onboard_critic
description: Dispatch this worker at the critic phase to judge the OBSERVED sections this run wrote and report every uncited, unresolvable or derivable entry.
skill: onboard
writes: evidence
model: inherit
tools: [Read, Grep, Glob, Bash(devforgeai status), Write]
skills: []
compiled_to: [.claude/agents/onboard-onboard_critic.md, .codex/agents/onboard-onboard_critic.toml]
responsibility: Report every OBSERVED entry whose Evidence names no resolvable path and no sealed Research reference, and every entry whose statement is readable at a path it cites.
inputs:
  - the devforgeai status block pasted into the dispatch
  - .devforgeai/work/<run>/code_map-result.json, doc_ingest-result.json, convention_infer-result.json, observed_write-result.json (by path)
  - the OBSERVED sections of docs/architecture/sourcetree.md, techstack.md and architecture.md as the observed_write checkpoint left them in the candidate root
  - the paths and dossier directories those sections cite
outputs:
  - .devforgeai/work/<run>/evidence/onboard_critic/findings.md, the full defect list, written in its own run-scoped evidence directory and named in evidence_refs
  - issues: one row per uncited entry, unresolvable citation, or entry duplicating a value readable at a cited path, bounded at ten
  - note: the count of entries examined and the count of citations resolved
must_not:
  - repair, rewrite or delete an entry it reports
  - accept an entry whose Evidence is a bare digest with no RUN, Source, Evidence and Claim ids
  - write anywhere but its own run-scoped evidence directory, or run any stack command key
tools_codex: [Read, Grep, Glob, Bash(devforgeai status), apply_patch]
isolation: required
returns: devforgeai.worker-result/v1
body:
  job: Judge the OBSERVED sections this run wrote against citation presence, citation resolvability and derivability.
  inputs: The list above, read under the candidate root; nothing is opened outside it.
  rules: references/critic.md, the three properties, and the must_not list.
  receipt: One devforgeai.worker-result/v1 object; claimed_paths is empty on every status, evidence_refs names the findings file it wrote under its run-scoped evidence directory, and each defect is also one issues row.
```

### 7e. Handoff outcomes

The `handoff.outcomes` block this skill declares, corrected to the closed status set. The rendered block is `.devforgeai/work/<run>/handoff.json`; the primary window prints it and adds nothing.

| Outcome | Next steps |
|---------|------------|
| pass, all five phases, run `ready_to_promote`, nothing promoted (`REQUIRE_HUMAN`) | 1. `devforgeai promote {run}` |
| `devforgeai promote {run}` succeeded after all five phases passed | 1. `/architect {slug}` |
| promoted, with conflict rows recorded by `doc_ingest` | 1. `/architect {slug}` — the conflict rows are `open_items`; architect owns the resolution |
| `needs_user` from `code_map` (a required stack key is stated nowhere) | 1. state the missing keys in the repository's own configuration, then `/onboard`, which resumes the blocked run at `code_map` with attempts reset |
| `needs_user` from `doc_ingest` (candidate documents exist, no sealed dossier covers them) | 1. `/research {slug} --request {request-file} --confirm-request {sha256}`, then `/onboard` |
| `needs_user` from `doc_ingest` (no candidate document exists) | 1. `/architect {slug}` — the applied stack section is this run's whole output |
| `needs_user` from `convention_infer` or `observed_write` (nothing non-derivable remains) | 1. `/architect {slug}` |
| `fail` at the attempt limit, any phase, including a critic that reports defects twice | 1. fix what the handoff names, then `/onboard` — the run is blocked, not closed: it stays `active` with its root and checkpoints on disk and `run.yaml#blocked_at` naming the phase, and this same command resumes it there with attempts reset. `devforgeai phase fail --reason <text>` is what abandons it instead |
| `could_not_run` with any reason code | 1. the repair named by the reason code, then `/onboard` |
| `devforgeai promote {run}` refused `STALE_BASE` in worktree mode | 1. `devforgeai promote {run}` again; that command rebases the candidate root onto the new canonical HEAD, reruns the last transition oracle and retries the fast-forward itself before it reports, so this row is reached only when the retry also failed |
| `devforgeai promote {run}` refused `STALE_BASE` in copy mode, or `MERGE_CONFLICT` after an aborted rebase | 1. reconcile the canonical tree by hand, then `devforgeai promote {run}` — the refusal moved no canonical byte, and the run stays `ready_to_promote` with its root intact |
| `devforgeai promote {run}` refused `DIRTY_TARGET` | 1. commit or discard the dirty canonical file the refusal names, then `devforgeai promote {run}` |
| `phase start` refused `FENCE_OVERLAP` | 1. finish or abandon the run the refusal names, then `/onboard` — two runs cannot both hold `.devforgeai/stack.yaml` |

The current sequencer selects the printed `next` itself from the fixed table in `10-sequencer-and-contracts.md` section 6: `devforgeai promote <run>` for the first block of a completed run, `/status` for the block that promotion writes and for a blocked `REQUIRE_HUMAN` document run, and the repair route for a `COULD_NOT_RUN` row. The rows above are the declared intent that `skill.yaml` carries; where the two differ today, what is printed is the sequencer's (section 9, row G-5).

### 7f. Phase guidance (becomes `references/<phase>.md`)

One file per registry phase, named for the phase exactly. Each is loaded when its phase's worker is dispatched.

#### `references/code_map.md`

This phase owes exactly one file, written inside the candidate root: `.devforgeai/stack.yaml`. The file is a mapping of anchor name to section; each anchor matches `[a-z][a-z0-9-]*`, and each section satisfies `schemas/devforgeai/v1/stack.schema.json`. A file that fails the schema is refused at ingest and never reaches a checkpoint, so build the section from stated values only. The canonical `.devforgeai/stack.yaml` is untouched until the run promotes; the file this phase edits is the copy under `candidate.root`.

Anchor naming. Name each OBSERVED anchor `observed-<ecosystem>`, for example `observed-python` or `observed-csharp`. Architect's INTENDED anchors use the bare ecosystem name, so the two producers never collide inside one file. Read the file in the candidate root first when it exists and edit in place, leaving every anchor this phase did not derive byte-identical: the sequencer compares the checkpoint diff to `claimed_paths`, so a rewrite that drops an anchor is a real deletion, not a formatting artefact.

Where each required key is read from:

| Key | Read from | When it is unknown |
|---|---|---|
| `version` | fixed at `1` | never |
| `compiled` | true when the ecosystem needs a build step before its tests run, evidenced by a build target in the manifest or configuration | when no manifest states a build step, `false` |
| `package_manager` | the manifest's own ecosystem, named by the file that exists | when no manifest exists at all |
| `manifests` | the manifest paths that exist, as globs | never; at least one manifest is required |
| `commands.test` | the test invocation stated in configuration: a runner section, a script entry, a task target, a continuous-integration workflow step | when no file states one |
| `commands.test.junit_path` | the JUnit output path the same configuration sets | when no file sets one |
| `commands.build` | the build invocation stated in configuration; mandatory when `compiled` is true | when `compiled` is true and no file states one |
| `commands.lint`, `commands.format` | the stated invocations; omit the key entirely when none is stated | omission is correct, not a defect |
| `test_glob`, `test_layout` | the configured test paths and the layout they describe | when no configuration states a test location |
| `runner_probe` | the cheapest form of the same runner, with `exit_ok: 0` | when `commands.test` is unknown |
| `packages.allow` | every package name the extractors capture from the manifests as they stand today | an empty list disables the check |
| `packages.deny`, `forbidden_imports` | an admitted constraint that states a ban, with the constraint's anchor as `reason` | an empty list, which is the correct value with no admitted ban |
| `extractors` | one entry per manifest syntax present, capture group 1 being the package name | never; an extractor with no capture group is a policy error |

Two traps. First, `packages.allow` is applied to the whole tree at application step 15, so an allowlist that omits a package a manifest already declares refuses the proposal and rolls back; derive it from what is declared today, or leave it empty. Second, inventing a `deny` pattern or a forbidden import refuses the existing tree for a rule nobody stated; leave both empty unless an admitted constraint states the ban and names its anchor.

When `commands.test`, its JUnit path, or a mandatory `build` is stated nowhere, write nothing, return `status: needs_user` with empty `claimed_paths`, one `issues` row per missing key naming the paths searched, and a note listing them. Guessing a runner is the failure this phase exists to prevent, and a `needs_user` result reaches a human on the first ask instead of consuming attempts.

Multi-package repositories: write one anchor for the ecosystem the repository root declares. Selecting a section per path is deferred (`12-post-mvp.md#pm-09`); record the additional ecosystems as `issues` rows so the omission is visible.

#### `references/doc_ingest.md`

This phase owes `docs/architecture/architecture.md` inside the candidate root, whose OBSERVED section carries constraints that came from documents, not from code. Edit the file where it sits under `candidate.root`; every other path in the root stays as the previous checkpoint left it.

Admission rule. A README, ADR, wiki page or CONTRIBUTING file enters the provenance chain only through a sealed Research dossier under `docs/research/<slug>/runs/RUN-NNNNNN/`. Cite RUN plus the applicable Source, Evidence and Claim ids and the sealed manifest digest on the entry's Evidence line; a bare digest is not a provenance reference. Dossier conformance is Research Core's, checked under `framework/skills/research/`; this phase cites ids and does not validate the dossier.

Candidate discovery. Glob for `README*`, `CONTRIBUTING*`, `ADR*`, `docs/**/*.md` and `*.wiki` outside `docs/architecture/` and `docs/research/`. Record every candidate and its admission state in the note, and each rejected candidate as one `issues` row.

Three outcomes, and the status each carries:

- Candidates exist and a sealed dossier covers at least one non-derivable claim: write the file with one `OBS-NNN` entry per admitted claim, `status: pass`, `claimed_paths` naming that one path.
- Candidates exist and no sealed dossier covers them: write nothing, `status: needs_user`, empty `claimed_paths`, and a note carrying the exact invocation a human runs, `/research <slug> --request <request-file> --confirm-request <sha256>` on Claude or the `$research` form on Codex. Onboard does not invoke Research and does not write a request file: this phase's fence admits one path, and Research persistence requires a human's confirmed digest.
- No candidate exists: write nothing, `status: needs_user`, empty `claimed_paths`, and a note naming the globs searched. There is nothing document-borne to admit, and writing an OBSERVED section anyway would either be empty, which the template's required sections refuse, or derived from source, which the derivability rule refuses.

Entry shape. Each `OBS-NNN` has `#### Constraint` (one statement, present tense), `#### Evidence` (the citation line), `#### Why It Is Not Derivable` (what a reader of the code cannot recover: a reason, a history, a timing, an obligation). Number entries from `OBS-001` within the file, continuing the highest existing number when the section already exists.

Conflicts. When an admitted claim contradicts the source path it describes, keep both: the entry records the claim and its citation, and an `issues` row records the claim id and the contradicting path with its line range. Averaging the two, or dropping one, destroys the only signal architect has that the document and the code disagree.

Citations block. Above the entries, the `### Citations` table lists the source paths this phase resolved while checking claims, each with its anchor and digest, and no copied value. That is the derivability rule in its written form: a fact a reader can obtain by opening a path is cited by path, never restated.

#### `references/convention_infer.md`

This phase owes `docs/architecture/sourcetree.md` inside the candidate root, whose OBSERVED section carries the layout, ownership and naming constraints that cannot be recovered by reading the tree.

Partition first. For every layout fact the earlier phases surfaced, ask whether a reader with the repository open can obtain it. A directory's existence, a package's name, a test file's location, an import graph and a naming pattern are all obtainable: they belong in `### Citations` as path, anchor and digest, which is where the derivable half lives on disk. A rule about who owns a directory, why a vendored tree exists, which generator produces a path, or which layout is frozen by an external agreement is not obtainable: it becomes an `OBS-NNN` entry whose `#### Why It Is Not Derivable` states what reading cannot recover.

Sources for the non-derivable half are the admitted dossier claims recorded by `doc_ingest` in `.devforgeai/work/<run>/doc_ingest-result.json`. A layout rule with no admitted source and no path is not written: it would be an invention with a citation-shaped hole.

When the partition admits no non-derivable constraint, write nothing, return `status: needs_user` with empty `claimed_paths` and a note carrying the derivable count, so a human sees that the layout was mapped and that nothing about it needed writing down.

#### `references/observed_write.md`

This phase owes `docs/architecture/techstack.md` inside the candidate root, whose OBSERVED section carries stack constraints that the stack section cannot express: a version freeze with a reason, a licence obligation, an operational timing rule, a dependency retained for a stated external reason.

Read the stack section this run wrote, at `.devforgeai/stack.yaml` in the candidate root, and cite manifests by path and digest in `### Citations`. Restating a value already carried by the stack section creates a second copy that drifts silently; the section is the value's home.

An entry earns its place only when a later phase would act differently for knowing it. Architect's gap analysis compares INTENDED sections with the OBSERVED constraints that exist, so an entry with no consequence is noise that a human must later read and discard.

When no admitted constraint remains after `doc_ingest` and `convention_infer` have taken theirs, write nothing, return `status: needs_user` with empty `claimed_paths` and a note saying so.

#### `references/critic.md`

This phase judges. The registry declares the phase `writes: none`, and the worker header declares `writes: evidence`: its `Write` reaches only `.devforgeai/work/<run>/evidence/onboard_critic/`, and a change the checkpoint diff reveals inside the candidate root refuses the receipt as `UNCLAIMED_CHANGE`. Write the full defect list to `findings.md` in that directory and name it in `evidence_refs`.

Check three properties over the OBSERVED sections in the candidate root and report each failure as one `issues` row:

1. **Citation presence.** Every `OBS-NNN` Evidence line names either a repository path with an anchor, or a RUN with its Source, Evidence and Claim ids and a sealed manifest digest. A bare digest, an unqualified document name, or an empty line is a defect.
2. **Citation resolvability.** Every cited path exists and contains the cited anchor or line range; every cited dossier directory exists. Digest re-computation belongs to `scripts/check_observed.py`, which no worker's tool grammar admits; report a citation as unresolvable only when the path or anchor is absent, and say which.
3. **Derivability.** An entry whose Constraint statement appears at a path the same entry cites is a derivable fact wearing a constraint's clothes; report it, naming the path and the line.

Report and stop. Repair belongs to the phase that proposed the entry, and a critic that edits what it reviews is the hallucination vector this design removes. When the run reaches this phase's attempt limit with defects outstanding, the sequencer writes a `REQUIRE_HUMAN` handoff carrying the rows.

#### `references/envelope.md`

The `devforgeai.worker-result/v1` receipt, its field bounds, and one worked example per status. Loaded for every dispatch. Content: the field table from `10-sequencer-and-contracts.md` section 5.1; the caps (64 `claimed_paths`, 16 `evidence_refs`, 16 KiB note, 10 issues); the rule that the final message is exactly the object, with no Markdown fence and no surrounding prose; the rule that `claimed_paths` is empty on any status other than `pass`; the rule that `next` needs both `status: fail` and a registry `rewind_to`, which no onboard phase declares; the rule that an unknown key refuses the receipt; and the rule that `reason_code` is present exactly when the status is `could_not_run`.

## 8. Bundled resources

### Layout (fixed)

```
onboard/SKILL.md            # at most 500 lines: identity, phase list, dispatch loop, handoff table
  references/code_map.md
  references/doc_ingest.md
  references/convention_infer.md
  references/observed_write.md
  references/critic.md
  references/envelope.md
  agents/code_mapper.md
  agents/doc_ingester.md
  agents/convention_inferrer.md
  agents/observed_writer.md
  agents/onboard_critic.md
  scripts/check_observed.py
  assets/observed-constraints.md
```

Link depth: `SKILL.md` links to `references/`, `agents/`, `scripts/` and `assets/`; an `agents/*.md` links to `references/*.md`; nothing links further. No `README.md` inside the skill directory.

### scripts/
| File | Purpose | Invocation | Exit codes |
|------|---------|------------|------------|
| `check_observed.py` | Deterministic conformance check for an OBSERVED section: frontmatter comment keys against the `observed-constraints` header, the three required per-entry sections, the `OBS-NNN` id pattern, the standard forbidden-text list, every Evidence citation resolved (path plus anchor exists, or dossier directory exists), every cited digest recomputed with the hash rule in `01-skill-anatomy.md`, and every Constraint statement compared against the bytes at the paths the entry cites so a derivable fact written as a constraint is reported | `python scripts/check_observed.py docs/architecture/architecture.md [--json] [--strict]` | 0 conformant, 1 defects listed on stdout, 2 usage |

The script prints JSON to stdout and diagnostics to stderr, documents `--help`, and never prompts. It is the library form of the template-conformance and provenance-conformance checks that `01-skill-anatomy.md` puts at the consuming gate; the implemented document gate checks the fence only, so today the script runs as a human or continuous-integration check. No worker and no primary window runs it: a worker's Bash grammar is `devforgeai status` alone, and the primary window's is the five model-callable operations.

### references/
| File | Content | Load when |
|------|---------|-----------|
| `code_map.md` | key-by-key sourcing rules for the stack section, anchor naming, the two allowlist traps, the unknown-key rule, and the two `writes` modes the shared profile serves: `candidate` under `onboard`, where the section is written into the candidate root, and `none` under `drift`, where the same reading produces `issues` rows and no file | dispatching `code_mapper` |
| `doc_ingest.md` | the admission rule, candidate discovery, the three outcomes, entry shape, conflict handling | dispatching `doc_ingester` |
| `convention_infer.md` | the derivable-versus-non-derivable partition and what each half becomes | dispatching `convention_inferrer` |
| `observed_write.md` | which stack constraints earn an entry and why restating an applied value is harmful | dispatching `observed_writer` |
| `critic.md` | the three properties checked, and why repair belongs elsewhere | dispatching `onboard_critic` |
| `envelope.md` | the `devforgeai.worker-result/v1` schema and bounds | every dispatch |

### assets/
| File | Used for |
|------|----------|
| `observed-constraints.md` | the OBSERVED section skeleton every writing phase fills: the header comment, the `### Citations` table header, and one `OBS-NNN` entry with its three sections and no content |

### agents/
| File | Worker (from section 7d) |
|------|-------------------------|
| `code_mapper.md` | `code_mapper` |
| `doc_ingester.md` | `doc_ingester` |
| `convention_inferrer.md` | `convention_inferrer` |
| `observed_writer.md` | `observed_writer` |
| `onboard_critic.md` | `onboard_critic` |

## 9. Gotchas and edge cases

| Situation | What goes wrong | What to do instead |
|-----------|-----------------|--------------------|
| G-1: four phases declare `writes: docs` and the fence holds four paths | The `document` oracle fails any `writes: docs` phase that changed no file (`examples/hooks/devforgeai.py` `check_document`), and two phases editing the same path in one run make the checkpoint diff ambiguous about which phase owes which change | Each writing phase owns exactly one fenced path: `code_map` owns `.devforgeai/stack.yaml`, `doc_ingest` owns `architecture.md`, `convention_infer` owns `sourcetree.md`, `observed_write` owns `techstack.md`. The mapping follows the scope of what each phase admits: document-borne rationale is architecture-scoped, layout classification is sourcetree-scoped, stack obligations are techstack-scoped. A phase with nothing admissible writes nothing and returns `needs_user` rather than inventing a section |
| G-2 (closed): an earlier draft of `01-skill-anatomy.md` and `05-subagent-sets.md` gave Slice to a framework worker; both now list Slice among the deterministic sequencer operations | No registry phase dispatches one, and receipt validation binds the stop event's `agent_type` to the active phase's worker, so a receipt from a slice worker would be refused | Slice is a sequencer step inside `devforgeai phase start`: it resolves the incoming artifact's already-hashed bundle and writes `.devforgeai/work/<run>/context.json`, which every worker of the run is handed by path. This spec promises no slice phase and ships no slice agent file |
| G-3: `.devforgeai/stack.yaml` is in `ALWAYS_DENY` | An earlier reading of `10-sequencer-and-contracts.md` section 7 made installing a generated section a human step | The producer exception in `examples/hooks/policy.py` admits exactly the pair skill `onboard`, phase `code_map`. `code_mapper` writes the file inside the candidate root, the sequencer validates the written bytes against `schemas/devforgeai/v1/stack.schema.json` at ingest before checkpointing, and the canonical file changes only when the run promotes. `phase start` counts the path as a fence member, so `FENCE_OVERLAP` stops a second run — an `architect` `techstack` run included — from holding it at the same time. `11-artifact-registry.md` section 6's closing paragraph records the earlier divergence as closed |
| G-13: the receipt no longer carries an `evidence` object | Earlier drafts of this spec gave `code_mapper` an `evidence.observed` row set that `drift`'s `doc_differ` consumed, and `evidence.unknown` for the keys nothing states. The receipt schema in the write-model revision removes `evidence` and adds `claimed_paths` and `evidence_refs`, which are paths, not rows | An observed fact's home is the file the phase wrote: the stack section's own keys, and the `### Citations` table in each OBSERVED section. `evidence_refs` points at those files, and `onboard_critic`, as a judge, writes its own findings under `.devforgeai/work/<run>/evidence/onboard_critic/` and names that file in `evidence_refs`; `issues[]` carries the bounded summary, at ten rows. The `drift` handshake still needs settling: `doc_differ` read `evidence.observed` from a sibling run's result file, and no receipt field now carries it. The proposed home is the judge evidence directory the brief's amendment adds — under `drift`, `code_mapper` is a judge and writes `.devforgeai/work/<run>/evidence/code_mapper/observed.md`, which `evidence_refs` names and `doc_differ` reads by path. The `drift` spec has not adopted that yet, so it is recorded here as a proposal, not as behaviour; `11-artifact-registry.md` section 6 divergence 1 is the other place it has to land |
| G-4: provenance and template conformance at the gate | `01-skill-anatomy.md` describes the gate re-resolving every citation; `document_gate` in `examples/hooks/devforgeai.py` checks the fence only, so nothing re-resolves a consumed document artifact at `devforgeai phase start` | The story gate re-resolves every `provenance` and `context` entry and `commands.hash`, and a placeholder digest is `unresolvable-source` under `gate_policy`; the document gate does not. Onboard's OBSERVED sections are therefore checked when a story quotes them, not when architect opens its document run, and `scripts/check_observed.py` is the deterministic form a human or continuous-integration step runs meanwhile. `AUTHOR-BRIEF.md` section 12 supersedes its own OI-2 row on this point |
| G-5: the declared handoff table and the printed `next` | `01-skill-anatomy.md` says the sequencer selects a row from the skill's `handoff.outcomes`; `examples/hooks/devforgeai.py` selects `next` from the fixed table in `10-sequencer-and-contracts.md` section 6 and does not read the declaration | Section 7e is the declared intent carried in `skill.yaml`; a completed or `REQUIRE_HUMAN` document run currently prints `/status`, and a `COULD_NOT_RUN` row prints its repair route. Read the handoff, not this table, for what a given run printed |
| G-6: `/onboard` takes no positional argument | `devforgeai phase start <skill> <arg>` requires one, and the run id `onboard-<arg>` names the evidence directory | The adapter reads `slug` from `.devforgeai/state.yaml` and passes it. With no `slug`, it passes the repository root directory name and records that substitution in the dispatch note, so a later reader can see why the evidence directory is named as it is |
| G-7: a resume flag after a block | `02-skill-roster.md` offers `/onboard --retry`, and an earlier draft here said `needs_user` and an exhausted attempt budget close the run and abandon its root | No flag resumes anything, and neither status closes the run: both leave it `active` with its root and checkpoints on disk and `run.yaml#blocked_at` naming the phase, and plain `devforgeai phase start onboard <arg>` resumes it there with `attempts` reset. `--retry` is therefore unnecessary and is not implemented. Where a run really is closed — `devforgeai phase fail --reason <text>` abandoned it — the next `phase start` opens a new candidate root from the current canonical HEAD, over a tree that already carries whatever an earlier run promoted; the phases are written to be re-runnable, each editing the file where it stands in the root and carrying existing entries forward |
| G-8: `code_mapper` is shared with `drift` | Two skills dispatching one worker crosses the no-borrowing rule, and provider agent names are global, so one profile serves both. Drift's `code_map` phase declares `writes: none` in the registry, so the same profile runs there as a judge whose `Write` reaches only `.devforgeai/work/<run>/evidence/code_mapper/`, and its run id and skill differ from onboard's | `onboard` owns `agents/code_mapper.md`; `drift` reuses it and owns no copy (`11-artifact-registry.md` section 6, divergence 1). The contract therefore writes into the candidate root only when the status block's phase grants it, and under `drift` writes its observed rows to `observed.md` in that evidence directory instead; it fills `run`, `skill` and `phase` from the status block rather than assuming onboard. The compiled profile is `onboard-code_mapper` on both providers, because onboard owns it. A change to the contract in section 7d is a change to both skills |
| G-9: OBSERVED and INTENDED anchors in one `stack.yaml` | `10-sequencer-and-contracts.md` section 7 names anchors `python` and `csharp` and says architect emits the INTENDED sections and onboard the OBSERVED ones, but never says how the two coexist in one file whose anchors match `[a-z][a-z0-9-]*` | Authored decision: onboard names each OBSERVED anchor `observed-<ecosystem>` and architect keeps the bare ecosystem name, so a story pins one anchor unambiguously and neither producer overwrites the other. Each producer edits the file in its own candidate root and leaves every anchor it did not derive byte-identical, and `FENCE_OVERLAP` keeps the two runs from being open at once |
| G-10: a legacy DevForgeAI document in the repository | An author may treat it as trusted provenance | It is treated exactly as any other non-DevForgeAI document: admissible only through a sealed dossier. Migration of legacy documents is deferred (`12-post-mvp.md#pm-08`) |
| G-11: a repository with two ecosystems | One anchor cannot describe both, and a story pins one anchor by hash | Write the root ecosystem's anchor and record the others as `issues` rows. Per-path section selection is deferred (`12-post-mvp.md#pm-09`) |
| G-12: an OBSERVED section already exists from an earlier run | A rewrite that omits existing entries deletes them, and the deletion reaches canonical at promotion because the checkpoint diff records exactly what the file now says | Edit the file in the candidate root rather than replacing it, carry every existing entry forward, and continue the `OBS-NNN` numbering from the highest present. `onboard_critic` reports a missing entry, and the run's own checkpoint diff is what a reviewer reads to see the deletion |
| G-14: the primary window and the candidate root | A worker cannot resolve `candidate.root` from the canonical tree, and pasting artifact content into a dispatch is the restatement the anti-ceremony rules forbid | The one thing the dispatch carries beyond paths and ids is the `devforgeai status` block, which names `run`, `candidate.root`, `phase`, `fence` and `granted_keys`. It is generated, not composed, and it is the only sanctioned paste |
| G-15: an earlier draft said promotion is the last thing the run does and that `devforgeai phase next` merges the candidate root | An author compiles a `SKILL.md` that never asks the user, and the run's files land in the canonical checkout without a human decision | Promotion is never automatic. The last passing transition sets `runs.<run>.status: ready_to_promote` and writes a `REQUIRE_HUMAN` handoff whose only forward step is `devforgeai promote <run>`; the compiled `SKILL.md` runs that command only after the user confirms in the session, and that command writes the second handoff block, whose `next` is the section 7e row for the run's outcome. Every run ends in two blocks, not one, and `STALE_BASE`, `DIRTY_TARGET` and `MERGE_CONFLICT` are refusals of `devforgeai promote <run>` that leave the run `ready_to_promote` with its root intact, never refusals of `devforgeai phase next`. **Decision (D7, as amended; `10-sequencer-and-contracts.md` sections 5.4, 6 and 12.4):** the sequencer may not close a run onto the canonical tree on its own. |
| G-16: An earlier draft said a `REQUIRE_HUMAN` block closes the run, so "no flag resumes a closed one" | An author writes a repair route that opens a fresh run, and `devforgeai phase start` refuses it — the blocked run is still `active` — or writes `devforgeai phase fail --reason <text>` into every recovery row and throws away work the run had already checkpointed | A block is not a close. A `needs_user` result and an exhausted attempt budget both leave the run `active` with its lease released, its candidate root and checkpoints on disk, and `run.yaml#blocked_at` naming the phase. `devforgeai phase start` with the same skill and the same argument **resumes** that run at `blocked_at` with `attempts` reset to zero instead of refusing it, so `/onboard` is the whole recovery once the human has acted. Only another skill on the same story needs `devforgeai phase fail --reason <text>` first, and that call is what abandons the root. **Decision (`10-sequencer-and-contracts.md` sections 2, 3, 5.4 and 6):** blocked runs resume; they are not reopened. |

## 10. Success criteria and test cases

### Success criteria

- Triggers on the section 4 positives and on none of the near-misses.
- Every `.devforgeai/stack.yaml` this skill writes validates against `schemas/devforgeai/v1/stack.schema.json`, and every command key in it is traceable to a manifest or configuration path the run's report names.
- No OBSERVED entry the run writes restates a value that appears at a path the same entry cites, measured by `scripts/check_observed.py` exiting 0.
- Every OBS entry's Evidence line names a repository path with an anchor, or a RUN with Source, Evidence and Claim ids and a sealed manifest digest.
- Every phase's `changed` set is a subset of its `claimed_paths` and lies inside the run's fence, and the `critic` phase changes nothing inside the candidate root.
- Every run ends with a handoff whose next step is exactly one command.

### Fixtures

Base fixture, `docs/design/examples/fixtures/onboard/`, a brownfield repository with one package and one README:

| Path | Content |
|---|---|
| `README.md` | Five short sections. `# ledger`; one paragraph of history ("in use by the finance team since 2019"); `## Layout`, stating that `ledger/` holds the package and `tests/` holds the tests; `## Release policy`, stating that the operations team approves every release during the Thursday maintenance window and that nothing in the code encodes this; `## Contact`, naming a team alias |
| `pyproject.toml` | `[project]` with `name = "ledger"`, `version = "0.3.1"`, `dependencies = ["click"]`; `[project.optional-dependencies]` with `dev = ["pytest"]`; `[tool.pytest.ini_options]` with `addopts = "-q --junitxml=.devforgeai/work/junit.xml"` and `testpaths = ["tests"]` |
| `ledger/__init__.py` | empty |
| `ledger/accounts.py` | twelve lines: a `balance(entries)` function summing signed amounts, with a module docstring |
| `tests/__init__.py` | empty |
| `tests/test_accounts.py` | one passing test of `balance` |
| `.devforgeai/state.yaml` | canonical state: `version: 1`, `target: [claude]`, `mode: brownfield`, `slug: ledger`, `phase: onboard`, an empty `stories` mapping, and a `runs` mapping with one key `onboard-ledger` whose value carries `story: null`, `skill: onboard`, `mode: copy`, `root: .`, `base_ref: fixture`, `checkpoint: base` and `status: active` |
| `.devforgeai/work/onboard-ledger/run.yaml` | the per-run enforcement file, standing in for what `devforgeai phase start` writes: `canonical: .`, `phase: code_map`, `fence` listing the three architecture documents and `.devforgeai/stack.yaml`, `test_paths: []`, `granted_keys: []`, `attempts` and `max_attempts` at 2 for the five phases, `gate_policy: {unresolvable_source: BLOCK}`, and a `lease` naming the eval session |

The sequencer is not installed in an eval copy, so the run file stands in for `devforgeai phase start` and the fixture root stands in for the candidate root: `candidate.mode` is `copy` and `candidate.root` is the fixture copy itself, so a worker's writes land where the eval can see them. Per-run enforcement lives in `run.yaml`, not in `state.yaml`, because nothing inside a candidate root reads canonical state. Expectations are checked against the receipt in the transcript and against files on disk. No eval gates on sequencer behaviour; quick-mode results are generation feedback only (`12-post-mvp.md#pm-02`).

Overlays, copied over the base fixture for the eval whose id they name:

| Overlay | Files |
|---|---|
| `overlays/eval-2/pyproject.toml` | the base file with `[project.optional-dependencies]` and `[tool.pytest.ini_options]` removed, so no file in the repository states a test runner or a JUnit path |
| `overlays/eval-3/.devforgeai/work/onboard-ledger/run.yaml` | the base run file with `phase` set to `doc_ingest` |
| `overlays/eval-3/docs/research/ledger/runs/RUN-000001/manifest.json` | one JSON object with `run: RUN-000001`, `sealed: true`, `manifest_sha256: sha256:4c7e1b0a9d2f3e5c6b8a0d1f2e3c4b5a6978859473625140f1e2d3c4b5a69788` |
| `overlays/eval-3/docs/research/ledger/runs/RUN-000001/sources.jsonl` | one line: `SRC-000001` naming `README.md` with its digest |
| `overlays/eval-3/docs/research/ledger/runs/RUN-000001/evidence.jsonl` | one line: `EVD-000001` quoting the release-policy sentence, citing `SRC-000001` |
| `overlays/eval-3/docs/research/ledger/runs/RUN-000001/claims.jsonl` | one line: `CLM-000001`, the claim that releases are approved during a named maintenance window, citing `EVD-000001` |

The dossier overlay carries the identifiers an OBS Evidence line cites. Its record shapes are governed by `framework/skills/research/`, and dossier conformance is Research Core's, not onboard's: the eval checks the citation, not the dossier.

### evals/evals.json (used verbatim)

```json
{
  "skill_name": "onboard",
  "evals": [
    {
      "id": 1,
      "prompt": "Onboard this repository. The DevForgeAI sequencer is not installed in this copy; the run file at .devforgeai/work/onboard-ledger/run.yaml is already open at phase code_map and this working copy is the candidate root. Dispatch that phase's worker and show me the receipt it returns, then continue with the phase that follows it.",
      "expected_output": "A code_mapper receipt claiming .devforgeai/stack.yaml, which now holds one anchor named observed-python whose commands.test argv and junit_path come from pyproject.toml; then a doc_ingester receipt with status needs_user naming the research invocation, because README.md is a candidate document and no sealed dossier covers it.",
      "files": [],
      "expectations": [
        "The code_mapper receipt's claimed_paths is exactly [.devforgeai/stack.yaml] and that file exists in the working copy afterwards",
        "The written stack section names a single anchor beginning with observed- and sets commands.test.junit_path to the value configured in pyproject.toml",
        "The written packages.allow contains click and pytest and nothing that pyproject.toml does not declare",
        "The written packages.deny and forbidden_imports are both empty lists",
        "The code_mapper receipt's evidence_refs names .devforgeai/stack.yaml and its note names pyproject.toml as the source of the test command",
        "The doc_ingester receipt has status needs_user, an empty claimed_paths, and a note containing a research invocation with both --request and --confirm-request",
        "No file under docs/architecture/ exists after the run, and no sentence from README.md appears in any file the run wrote"
      ]
    },
    {
      "id": 2,
      "prompt": "Onboard this repository. The sequencer is not installed; the run file at .devforgeai/work/onboard-ledger/run.yaml is already open at phase code_map and this working copy is the candidate root. Dispatch that phase's worker and show me the receipt it returns.",
      "expected_output": "A code_mapper receipt with status needs_user, empty claimed_paths, and an issues row naming commands.test and its junit path, because no manifest or configuration file in this copy states a test runner.",
      "files": [],
      "expectations": [
        "The code_mapper receipt has status needs_user and an empty claimed_paths list",
        "The receipt carries an issues row naming commands.test as a key no file states",
        "No stack.yaml is created anywhere in the working copy",
        "Neither the receipt nor the final message names a test runner that pyproject.toml does not declare"
      ]
    },
    {
      "id": 3,
      "prompt": "Continue onboarding this repository. The sequencer is not installed; the run file at .devforgeai/work/onboard-ledger/run.yaml is already open at phase doc_ingest and this working copy is the candidate root. Dispatch that phase's worker and show me the receipt it returns.",
      "expected_output": "A doc_ingester receipt claiming docs/architecture/architecture.md, which now carries an OBSERVED section with one OBS-001 entry for the release-approval window, cited to RUN-000001, SRC-000001, EVD-000001, CLM-000001 and the sealed manifest digest, plus a Citations table and no copied layout prose.",
      "files": [],
      "expectations": [
        "The doc_ingester receipt's claimed_paths is exactly [docs/architecture/architecture.md] and that file exists in the working copy afterwards",
        "The written file contains an entry with id OBS-001 and the three sections Constraint, Evidence, and Why It Is Not Derivable",
        "The OBS-001 Evidence line names RUN-000001, SRC-000001, EVD-000001, CLM-000001 and the manifest digest from the fixture",
        "The written file does not restate the README Layout sentence about ledger/ and tests/, and cites those paths in the Citations table instead",
        "The receipt's note records one admitted claim and names README.md as the admitted candidate"
      ]
    }
  ]
}
```

## 11. Dependencies and compatibility

| Kind | Value |
|------|-------|
| Tools | `SKILL.md`: `Read`, `Agent`, and a Bash grammar no wider than the five model-callable operations `devforgeai status \| phase start <skill> <arg> \| phase fail --reason \| validate \| promote <run>`. Document writers (`code_mapper`, `doc_ingester`, `convention_inferrer`, `observed_writer`): `Read`, `Grep`, `Glob`, `Bash(devforgeai status)`, plus `Edit` and `Write`, which Codex serves as `apply_patch`; every write is denied outside `candidate.root` and outside the phase's fence. Judges (`onboard_critic`): `Read`, `Grep`, `Glob`, `Bash(devforgeai status)`, plus `Write` confined to `.devforgeai/work/<run>/evidence/<agent>/`. No onboard phase grants a stack command key, so no worker carries `Bash(devforgeai run *)` |
| MCP servers | none |
| Runtime | Python 3.11+ for `scripts/check_observed.py`, which imports `PyYAML` and the standard library only. Worktree mode additionally requires `git` with at least one commit on the project. The sequencer requires `jsonschema` to validate the written stack section at ingest; without it the phase is refused rather than checkpointed unvalidated |
| Project commands | none. Every onboard phase declares an empty run-key set, so no `stack.yaml` key is brokered during this skill's run. The section this skill proposes is what later skills resolve their `build`, `test`, `lint` and `format` keys from; the contract is `10-sequencer-and-contracts.md` section 7 |
| DevForgeAI/Core compatibility | `NOT_APPLICABLE`; `onboard` is an anatomy-governed skill, not a Research Core adapter. It cites sealed dossiers by id and never writes under `docs/research/` |
| Other skills | Upstream: `init`. Downstream: `architect` and `brainstorm` consume `observed-constraints`; `dev` and `qa` consume the applied `stack`; `plan` consumes the three architecture documents. `drift` reuses `agents/code_mapper.md`. Onboard invokes no other skill: a "calls" edge is a handoff row |

Deferred dependencies, named and not gated on:

| Entry | What onboard does today without it |
|---|---|
| `12-post-mvp.md#pm-01` | Isolation is a declaration compiled into the target profile; nothing verifies it at run time. Every worker contract still declares `isolation: required`, which is the DevForgeAI contract value and not Claude's `isolation` frontmatter field |
| `12-post-mvp.md#pm-04` | A worker's write boundary is the dispatcher's `PreToolUse` deny plus the candidate root, not an operating-system boundary |
| `12-post-mvp.md#pm-02` | Quick-mode eval results are generation feedback only. No section of this spec gates on them |
| `12-post-mvp.md#pm-06` | Eval mode is `skip` or `quick`; the interactive mode is not named as available |
| `12-post-mvp.md#pm-08` | A legacy DevForgeAI document is treated exactly as any other non-DevForgeAI document: admissible only through a sealed dossier |
| `12-post-mvp.md#pm-09` | One anchor per run, for the root ecosystem; additional ecosystems are recorded as unknown rather than resolved per path |
| `12-post-mvp.md#pm-10` | Nothing re-checks an applied OBSERVED section from a clean checkout. `scripts/check_observed.py` runs as a human or continuous-integration step |

Frontmatter values derived from this table:

```yaml
compatibility: "Runs in the Claude Code or Codex terminal inside a repository that has .devforgeai/state.yaml. Requires Python 3.11+ and PyYAML for the bundled check script."
allowed-tools: "Read Agent Bash(devforgeai status) Bash(devforgeai phase start *) Bash(devforgeai phase fail *) Bash(devforgeai validate) Bash(devforgeai promote *)"
```

## 12. Targets

The generator produces one provider-neutral semantic package and a separate adapter for each selected target when frontmatter, invocation policy, or agent configuration differs. Provider-neutral resources may be shared. Adapter directories are not required to be byte-identical or symlinked.

| Target | Install path | Invocation | Subagents | Notes |
|--------|--------------|------------|-----------|-------|
| claude | `.claude/skills/onboard/` | `/onboard`; the adapter supplies the slug from `state.yaml` as the sequencer argument | `.claude/agents/onboard-<role>.md`: four document writers with `Edit` and `Write` confined to the candidate root, one judge whose `Write` reaches only its run-scoped evidence directory | Provider-specific frontmatter keys are compiled into this target's `SKILL.md` only. `hooks`, `memory`, `background`, `permissionMode` and Claude's own `isolation` are omitted from every profile |
| codex | `.agents/skills/onboard/` plus `.codex/agents/` profiles | `$onboard`; same argument rule | `.codex/agents/onboard-<role>.toml`: the same five names, with `apply_patch` in place of `Edit` and `Write` | Portable six-field frontmatter only; policy goes in target-side configuration |
| both | separate `.claude/skills/onboard/` and `.agents/skills/onboard/` adapters | as above | as above | Share only provider-neutral resources; validate each adapter independently |

```yaml
metadata:
  version: "1.0.0"
  devforgeai-spec: "SKILL-SPEC-005"
  devforgeai-target: "both"
  devforgeai-anatomy: "true"
```

Not produced by skill-creator, and deferred to DevForgeAI's skill-generator: provider-native `.claude/agents/*.md` and `.codex/agents/*.toml` worker profiles, provider-specific frontmatter keys for the Claude target, and concise `AGENTS.md` sections. Hook definitions are not per-skill: `init` installs the one dispatcher and its provider fragments from `09-hook-dispatcher.md`, and this spec ships none. A generated package is an uninstalled candidate until those provider-native controls are present and independently validated; generation or quick-mode success is not installation authority.

## 13. Constraints

- `SKILL.md` under 500 lines and roughly 5,000 tokens, holding only identity, the ordered phase list, the dispatch loop, and the handoff table. Every other instruction lives in `references/<phase>.md`, `agents/<role>.md`, `scripts/` or `assets/`. Splitting a phase into more reference files is the correct response to the line budget; cutting content is not.
- References one level deep from whichever file is loaded: `SKILL.md` links to `references/`, `agents/`, `scripts/` and `assets/`; an `agents/*.md` may link to `references/*.md`. Nothing links further.
- Hooks, state writes and phase advancement are not in the skill. Do not write an instruction the sequencer or a hook already enforces.
- No `README.md` inside the skill directory.
- No angle brackets in frontmatter. Description at most 1024 characters, name at most 64.
- Imperative voice. Explain why a step matters rather than shouting it; no capitalised absolutes.
- Provide defaults, not menus. Procedures over declarations.
- Scripts are non-interactive, take arguments, print data to stdout and diagnostics to stderr, and exit 0, 1 or 2.
- From this skill's own subject matter: a value that no repository file states is reported as unknown; a fact readable at a path is cited by path and never copied; a document enters the provenance chain only through a sealed dossier.

## 14. Acceptance checks

Run these before reporting done and paste their output:

```bash
# frontmatter and naming (skill-creator's own validator)
python -m scripts.quick_validate ./out/onboard          # run from the skill-creator directory
# open-standard validator, if installed
skills-ref validate ./out/onboard
# size budget
wc -l ./out/onboard/SKILL.md                            # must be under 500
# every worker in section 7d has a prompt file, and no extra
ls ./out/onboard/agents/                                # code_mapper doc_ingester convention_inferrer observed_writer onboard_critic
# one reference file per registry phase, plus envelope.md
ls ./out/onboard/references/                            # code_map doc_ingest convention_infer observed_write critic envelope
# the bundled check script runs and reports usage cleanly
python ./out/onboard/scripts/check_observed.py --help
# no leftover placeholders
grep -rnE 'T[O]DO|T[B]D|\{\{' ./out/onboard || echo clean
# the spec battery
python3 docs/design/specs/verify.py --only v1,v2,v4
```

For non-Research anatomy skills, DevForgeAI skill-validator additionally checks: all sub-phase kinds present with Gate, Record and Handoff bound to sequencer operations; persona and critic are different files; `must_not` present in every agent file; every agent declaring `writes: candidate` or `writes: evidence`, with a `writes: evidence` agent carrying no `Edit` and a `Write` fenced to its run-scoped evidence directory, and a `writes: candidate` agent carrying no tool beyond the read set plus `Edit` and `Write`; the `SKILL.md` Bash grammar no wider than the five model-callable operations; and handoff outcomes covering every status the skill can return, including `could_not_run`.

## 15. Provenance

| Source | Hash | Used for |
|--------|------|----------|
| docs/design/01-skill-anatomy.md#primary-window-contract | see frontmatter | sections 2 (R5), 7a, 13 |
| docs/design/01-skill-anatomy.md#the-seven-sub-phases | see frontmatter | section 7b |
| docs/design/10-sequencer-and-contracts.md#4-per-skill-phase-registry | see frontmatter | sections 7b, 7c, 9 |
| docs/design/10-sequencer-and-contracts.md#5-4-transition-oracles | see frontmatter | sections 7c, 9 (G-1) |
| docs/design/10-sequencer-and-contracts.md#3-2-defect-to-action-map-as-implemented | see frontmatter | sections 6, 7c |
| docs/design/10-sequencer-and-contracts.md#7-stack-yaml | see frontmatter | sections 6, 7f, 11 |
| docs/design/11-artifact-registry.md#1-template-registry | see frontmatter | sections 6, 8 |
| docs/design/11-artifact-registry.md#2-artifact-path-patterns | see frontmatter | section 6 |
| docs/design/03-brownfield.md#the-onboard-skill | see frontmatter | sections 1, 2, 7f |
| docs/design/03-brownfield.md#observed-vs-intended | see frontmatter | sections 2 (R2), 6, 7f |
| docs/design/02-skill-roster.md#handoff-decision-tables | see frontmatter | section 7e |
| docs/design/05-subagent-sets.md#sets-per-skill | see frontmatter | sections 7d, 8 |
