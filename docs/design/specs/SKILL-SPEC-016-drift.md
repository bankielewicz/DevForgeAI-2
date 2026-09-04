---
template: skill-spec
template_version: 1
id: SKILL-SPEC-016
skill_name: drift
target: both
status: approved
author: "DevForgeAI plan skill (wave 2 spec authoring)"
date: 2026-09-02
depends_on:
  - source: docs/design/01-skill-anatomy.md#primary-window-contract
    hash: sha256:721c5d5e73f2678f565b23284f78cffe26b62919c6d652aa7756f13a9a0f064e
    excerpt: "**The model dispatches, the sequencer decides.** For an anatomy-governed skill, the primary window (provider entry adapter + skill orchestration) does light, trivial work only."
  - source: docs/design/01-skill-anatomy.md#context-bundle-format
    hash: sha256:7b068feb30e7cc2f66292b512ac179cd217df225fb58517d2aaadd30b25236dc
    excerpt: "3. Split the file on LF (a file that ends with LF therefore yields a final empty line, which belongs to the last section); join the section lines with LF and append one LF."
  - source: docs/design/03-brownfield.md#observed-vs-intended
    hash: sha256:76cdea3c2760b31cc074204be8c244bffb3d582a0ceba60482aa525ce03194a8
    excerpt: "Every constitution section carries a status:"
  - source: docs/design/03-brownfield.md#the-onboard-skill
    hash: sha256:712484fa78944f1d90b6c6ac92ae40d63793d1be6b15bf99a8eee4132f246db5
    excerpt: "Persona: **Archaeologist**. Its job is to describe what exists, never to prescribe."
  - source: docs/design/10-sequencer-and-contracts.md#4-per-skill-phase-registry
    hash: sha256:ac18004be37ef017e4d4abf8c6303e096d64dbbc0ae0c37e6288230473caaf66
    excerpt: "| drift | document | `docs/reports/drift-<arg>.md` | 3 |"
  - source: docs/design/10-sequencer-and-contracts.md#5-worker-result
    hash: sha256:a27553487d0bfd28fe9329ef145aa47fd00138ec923cf737e3e5e94f7ff212a4
    excerpt: "One schema, both providers, every skill. The worker's final message is exactly this object, with no Markdown fence and no surrounding prose."
  - source: docs/design/10-sequencer-and-contracts.md#3-status-vocabulary-and-gate-policy
    hash: sha256:5e1b603b96613581b8d9010526f504e445cbf524de972ea7a999ac0c127b6667
    excerpt: "A document run carries the fixed map `{unresolvable_source: BLOCK}`, because it has no story to declare a wider one."
  - source: docs/design/10-sequencer-and-contracts.md#6-handoff-envelope
    hash: sha256:fa55ff391a00f9b6c93ab76cd26b305bc16b2617aa714f90501b571e8f68f32f
    excerpt: "| document run, promoted, no verdict or `verdict: pass` | `/status` |"
  - source: docs/design/11-artifact-registry.md#1-template-registry
    hash: sha256:cb9cad97fcdd0d5b5da645e2d16f43c665f935174f52f9ba3c2858c004f3e894
    excerpt: "| `drift-report` | `.devforgeai/skills/drift/templates/drift-report.md` | 1 | `^DRIFT-[0-9]{3}$` | slug, template, template_version, status, depends_on | Sourcetree Drift, Techstack Drift, Architecture Drift, Actions |"
  - source: docs/design/11-artifact-registry.md#6-known-divergences
    hash: sha256:8a78656458735ce54ac73010da3b8fc87bbb7017a5a9268f85b210249736b82a
    excerpt: "Recorded here so that no specification silently inherits them."
  - source: docs/design/02-skill-roster.md#drift
    hash: sha256:2e692ec945705c37a620b9742b73ecfbcd8c2e16a385a3f50155666500788e2e
    excerpt: "- Re-runs onboard's code-mapper and diffs against sourcetree, techstack, architecture."
  - source: docs/design/05-subagent-sets.md#sets-per-skill
    hash: sha256:2bb8ba434c56127d48d09179d742bf0f2f284f18363e7c2e911b1f2211ba3a7e
    excerpt: "| drift | code-mapper, doc-differ, drift-writer |"
---

# Skill Specification: drift

A stranger with no conversation history must be able to build this skill from this document alone. Every question the generator would otherwise ask is answered below. The `depends_on` digests are computed under the hash rule in `01-skill-anatomy.md#context-bundle-format` and verified by `docs/design/specs/verify.py --only v3`; a source edit after this date makes V3 fail until the digest is recomputed.

## 0. Generator instructions

These instructions are addressed to the skill-generating agent (Anthropic's `skill-creator` skill, or DevForgeAI's `skill-generator`). They replace its interview.

### Cold-session prompt

Paste this into a fresh session from the repository root:

```
Use the skill-creator skill to build the skill specified in docs/design/specs/SKILL-SPEC-016-drift.md.
Follow its section 0 exactly. Output directory: ./out. Eval mode: quick.
```

### Rules for the generator

1. **Do not interview.** Sections 1-13 pre-answer every Capture Intent and Interview question (what it enables, when it triggers, output format, test cases, edge cases, input/output formats, example files, success criteria, dependencies). Treat this document as the conversation history you are told to harvest from.
2. **Test prompts are pre-approved.** Use section 10 verbatim as `evals/evals.json`. Do not ask whether they look right.
3. **Trigger queries are pre-approved.** Use section 4 verbatim as the trigger eval set. Do not ask for sign-off.
4. **No human review loop.** Do not wait for the user to review results. Proceed to the next stage on your own.
5. **Eval mode** is given in the prompt and is one of two values:
   - `skip`: write the skill only. Do not create `evals/`, do not run test prompts, do not optimize the description.
   - `quick`: write the skill and `evals/evals.json`. Build each eval's workspace from `fixtures/drift/` as section 10 describes, run each test prompt once with the skill (no baseline run), grade with the grader agent, write `grading.json`, and report pass/fail per expectation in your final message. Do not run the description-optimization loop. Run the eval executions and the grader as foreground Agent-tool subagents, never as background shell processes, and do not end your turn until every `grading.json` exists: a headless session terminates when the top-level turn ends and orphans anything still running.
   - Any other mode name is a spec defect. The deferred interactive mode is `12-post-mvp.md#pm-06`.
6. **Output location** is given in the prompt. Create `./out/drift/`. Do not write anywhere else except the `drift-workspace/` sibling that eval runs require.
7. **On ambiguity, stop before output.** If the spec is still `draft`, contains an unresolved authoring assumption, omits a section, contradicts itself, or leaves a decision this document does not make, do not guess and do not write candidate skill files. End with a list titled `SPEC GAPS` naming each section and question. The spec author fixes and approves the spec before re-running.
8. **Fidelity over creativity.** Use the description in section 3 verbatim. Use the worker contracts in section 7d verbatim as `agents/<role>.md` bodies, adding only the four-section framing `templates/agent-md.md` fixes (Job, Inputs, Rules, Receipt). This skill ships two agent files, not three: section 8 says which worker file it does not own. Do not add steps, tools, or behaviours the spec does not mention.
9. **Finish with the acceptance checks** in section 14 and include their output in your final message.

## 1. Identity

| Field | Value |
|-------|-------|
| name | `drift` (kebab-case, 5 chars, equals the directory name, no `claude`/`anthropic` prefix) |
| title | Documentation and Code Drift Report |
| purpose | Re-observe the repository and compare those facts against the sourcetree, techstack and architecture documents, so the places where the written architecture no longer describes the code are named with citations before a story is sliced from a document that is wrong. |
| category | devforgeai-phase |
| version | 1.0.0 (skill-package version written to `metadata.version`; not the DevForgeAI or Research Core version) |
| license | MIT (frontmatter `license: MIT`) |

## 2. Problem and requirements

**Without this skill:** the architecture set ages silently. Directories move, a dependency is swapped, a component is deleted, and `sourcetree.md`, `techstack.md` and `architecture.md` still describe the repository as it was. Every story sliced afterwards carries a context excerpt that is accurate as bytes and wrong as fact: its digest resolves, so the story gate passes it, and dev implements against a document that no longer matches the code. Two failure modes from `07-purpose-and-enforcement.md` section 2 apply: "declares done because a file exists", and "invents requirements or scope", which is what a stale architecture document invites.

| ID | Kind | Requirement |
|----|------|-------------|
| R1 | explicit | Re-observe the repository: paths, manifests and configuration facts, each with a source citation, and report anything not explicitly present as unknown rather than guessing it. |
| R2 | explicit | Compare those OBSERVED facts against the INTENDED sections of `sourcetree.md`, `techstack.md` and `architecture.md`, one row per disagreement. |
| R3 | explicit | Write `docs/reports/drift-<slug>.md` against the `drift-report` template, whose sections are Sourcetree Drift, Techstack Drift, Architecture Drift and Actions. |
| R4 | explicit | Give every drift row an action: the exact `/amend` or `/architect` command that resolves it, so no reader has to decide what to run. |
| R5 | implicit | `drift` describes and never prescribes. It changes no document it reads; its fence is one report file, written inside the candidate root. |
| R6 | implicit | OBSERVED is advisory and INTENDED binds (`03-brownfield.md#observed-vs-intended`), so a disagreement is reported as drift and never resolved in favour of the code. |
| R7 | implicit | The primary window opens the run, dispatches, and prints the rendered handoff. It reads no document and writes nothing (`01-skill-anatomy.md#primary-window-contract`). |
| R8 | discovered | `code_mapper` is dispatched by both `onboard` and `drift`. `onboard` owns the worker file; `drift` dispatches the same canonical name and ships no copy, because provider agent names are global and two profiles with one name would collide. |
| R9 | discovered | `drift`'s `code_map` phase declares `writes: none` in the registry, so its dispatch of the shared worker is a judge declaring `writes: none`: it holds no write tool, the observed map comes back in the receipt's `findings` for the sequencer to persist at `.devforgeai/work/<run>/evidence/code_mapper/findings.md`, and the receipt also carries the bounded `issues[]` and `note`. `onboard`'s `code_map` phase declares `writes: docs`, so its dispatch is a producer with `Edit` and `Write`. The shared contract must behave correctly under both, and section 9 records how. |
| R10 | discovered | `/drift` takes no positional argument in `02-skill-roster.md`, but `devforgeai phase start <skill> <arg>` requires one and the fence substitutes it. The adapter supplies the project slug from `state.yaml`; section 9 records what happens when there is none. |

## 3. Description

```yaml
description: >
  Report where a DevForgeAI project's architecture documents no longer describe its code.
  Use this skill whenever someone suspects the docs are stale or wants to check before
  trusting them: the user says the docs are out of date, does architecture.md still match,
  what changed since we wrote the sourcetree, we swapped a library months ago and never
  updated anything, or asks for a drift check before planning or onboarding a new person.
  It re-observes the repository paths, manifests and configuration, compares those facts
  against the sourcetree, techstack and architecture documents section by section, and
  writes a drift report whose every row carries the citation behind it and the exact command
  that fixes it. Do NOT use it to change a document or record a decision (use /amend), to
  write the architecture set (use /architect), to check one story's traceability (use
  /analyze), or to run tests (use /qa).
```

Character count: 908 / 1024. No `<` or `>` appears in the description, so the command forms are written without angle brackets.

## 4. Trigger set

```json
[
  {"query": "/drift", "should_trigger": true},
  {"query": "does architecture.md still match what's actually in src/?", "should_trigger": true},
  {"query": "we ripped out redis about three months ago, i bet the docs still mention it. check", "should_trigger": true},
  {"query": "before i plan the next epic, tell me whether the sourcetree doc is still accurate", "should_trigger": true},
  {"query": "new dev starts monday and i don't trust docs/architecture. what's stale?", "should_trigger": true},
  {"query": "handlers live in src/http now but i'm not sure the docs know that", "should_trigger": true},
  {"query": "compare the dependencies in pyproject.toml against techstack.md", "should_trigger": true},
  {"query": "run a drift check on the shop project and tell me what to amend", "should_trigger": true},
  {"query": "the qa report mentions a module that isn't in architecture.md at all, is anything else missing?", "should_trigger": true},
  {"query": "update techstack.md to say sqlite instead of postgres", "should_trigger": false},
  {"query": "write architecture.md for this project, we have none", "should_trigger": false},
  {"query": "which prd requirements have no story yet?", "should_trigger": false},
  {"query": "map this repository so we can start using devforgeai on it", "should_trigger": false},
  {"query": "run the test suite and tell me what fails", "should_trigger": false},
  {"query": "STORY-004's context hash is stale, re-slice it", "should_trigger": false},
  {"query": "review STORY-011's diff against the constitution", "should_trigger": false},
  {"query": "what did we learn in sprint-002?", "should_trigger": false},
  {"query": "generate a skill for the tdd mandate in the constitution", "should_trigger": false},
  {"query": "explain what architectural drift means, my manager keeps saying it", "should_trigger": false}
]
```

## 5. Use cases

### UC-1: Routine drift check before planning
- **User says:** "/drift"
- **Steps:** 1. The adapter reads the project slug from `state.yaml` and calls `devforgeai phase start drift shop`. 2. `code_mapper` walks the repository, records the paths and the manifest and configuration facts it can cite, and returns them in the receipt's `findings` — which the sequencer persists to `.devforgeai/work/<run>/evidence/code_mapper/findings.md` — with `unknown` for anything not explicitly present. 3. `doc_differ` reads `code_map-result.json` and the INTENDED sections of the three documents and returns one row per disagreement, each with the document anchor and the observed citation. 4. `drift_writer` writes `docs/reports/drift-shop.md` inside the candidate root with the three drift sections and an Actions table.
- **Result:** one drift report, three result files under `.devforgeai/work/drift-shop/`, and a handoff whose next step is `/status` with the drift rows printed as open items.

### UC-2: A dependency was swapped and never documented
- **User says:** "we ripped out redis about three months ago, i bet the docs still mention it. check"
- **Steps:** 1. The run opens for the project slug. 2. `code_mapper` records the current manifest package list with the manifest path and line for each. 3. `doc_differ` finds `techstack.md#data-access` naming a package that no manifest captures and emits a `doc-only` row. 4. `drift_writer` writes the row under Techstack Drift with the action `/amend techstack "remove the cache dependency the manifests no longer carry"`, and adds a second action naming `/architect` because `.devforgeai/stack.yaml` is regenerated by that skill, not this one.
- **Result:** a report that separates what changed in code from what must change in the documents, and names the owner of each fix.

### UC-3: No project slug recorded
- **User says:** "/drift"
- **Steps:** 1. The adapter reads `state.yaml` and finds no `slug`. 2. It does not call `devforgeai phase start`, because the fence pattern would substitute an empty argument. 3. It runs `devforgeai status` and stops, telling the user to re-run as `/drift <slug>`.
- **Result:** no run opened, nothing written, and a printed instruction naming the one argument the skill needs.

## 6. Inputs and outputs

### Inputs
| Input | Format | Example file | Required |
|-------|--------|--------------|----------|
| project slug | the single positional argument; defaults to `state.yaml`'s `slug` | | yes |
| repository tree | files and directories, minus the walk's ignored directories | `fixtures/drift/src/` | yes |
| manifests | whatever the ecosystem uses; read as text and cited by path and line | `fixtures/drift/pyproject.toml` | no |
| sourcetree document | markdown, `architect`'s `sourcetree` template v1 | `fixtures/drift/docs/architecture/sourcetree.md` | no |
| techstack document | markdown, `architect`'s `techstack` template v1 | `fixtures/drift/docs/architecture/techstack.md` | no |
| architecture document | markdown, `architect`'s `architecture` template v1 | `fixtures/drift/docs/architecture/architecture.md` | no |
| `.devforgeai/state.yaml` | yaml | `fixtures/drift/.devforgeai/state.yaml` | yes; `devforgeai phase start` refuses without it |

A missing document is a reportable fact, not a failure: `doc_differ` emits one row saying the document does not exist and names `/architect <slug>` as its action.

### Outputs
| Output | Format | Location | Template |
|--------|--------|----------|----------|
| drift report | markdown | `docs/reports/drift-<slug>.md` | `drift-report` (`assets/drift-report.md`) |
| phase results | json | `.devforgeai/work/drift-<slug>/<phase>-result.json` | none; the sequencer writes it |
| phase reports | markdown | `.devforgeai/work/drift-<slug>/<phase>-report.md` | none; the sequencer renders it |
| rendered views | markdown | `docs/reports/drift-drift-<slug>-<phase>.md` | none; the sequencer writes it at each passing transition |
| handoff | json plus its printed block | `.devforgeai/work/drift-<slug>/handoff.json` | `handoff` |

`docs/reports/drift-<slug>.md` is the only path any drift worker writes, and it is written inside the candidate root. In particular `drift` writes no document under `docs/architecture/` and no `.devforgeai/stack.yaml`: the write path for that file belongs to `architect`'s `techstack` phase and `onboard`'s `code_map` phase.

### Output template

`docs/reports/drift-<slug>.md`, filled from `assets/drift-report.md`:

```
---
slug: shop
template: drift-report
template_version: 1
status: complete
depends_on:
  - source: docs/architecture/sourcetree.md#layout
    hash: sha256:<64 hex>
    excerpt: |
      HTTP handlers live under src/api/.
  - source: docs/architecture/techstack.md#data-access
    hash: sha256:<64 hex>
    excerpt: |
      Caching uses redis.
---

# Drift: shop

## Sourcetree Drift
| ID | Document anchor | Says | Observed | Citation | Kind |
|---|---|---|---|---|---|
| DRIFT-001 | docs/architecture/sourcetree.md#layout | HTTP handlers live under src/api/ | src/api/ does not exist; src/http/ holds four modules | src/http/routes.py; src/http/middleware.py | doc-only |

## Techstack Drift
| ID | Document anchor | Says | Observed | Citation | Kind |
|---|---|---|---|---|---|
| DRIFT-002 | docs/architecture/techstack.md#data-access | Caching uses redis | no manifest captures a redis package | pyproject.toml L12-L18 | doc-only |

## Architecture Drift
| ID | Document anchor | Says | Observed | Citation | Kind |
|---|---|---|---|---|---|
| DRIFT-003 | docs/architecture/architecture.md#components | four components listed | src/billing/ exists and no component describes it | src/billing/__init__.py | code-only |

## Actions
| ID | Action | Owner |
|---|---|---|
| DRIFT-001 | /amend sourcetree "handlers moved from src/api to src/http" | amend |
| DRIFT-002 | /amend techstack "remove the cache dependency the manifests no longer carry" | amend |
| DRIFT-003 | /architect shop | architect |
```

`id_pattern` for this template is `^DRIFT-[0-9]{3}$`, and the ids run in one sequence across the three drift sections so an Actions row always points back at exactly one drift row. `Kind` is one of `doc-only` (the document states something the repository does not show), `code-only` (the repository shows something no document states), or `conflict` (both state something and the statements disagree).

### Return envelope (DevForgeAI-anatomy skills only)

One schema, both providers: `devforgeai.worker-result/v1`, normative in `schemas/devforgeai/v1/worker-result.schema.json`. Two of the three phases are judges: they hold no write tool at all, claim nothing, and return their full row sets in the receipt's `findings`, a string required on a judge pass or fail receipt, optional on its needs_user or could_not_run, and forbidden on a producer's, and bounded at 16,384 UTF-8 bytes. At the identity-bound `SubagentStop`, after the receipt validates, the sequencer writes that string verbatim to the fixed path `.devforgeai/work/<run>/evidence/<agent>/findings.md` — run-scoped scratch, gitignored, outside the candidate root and never promoted — and records the path in `<phase>-result.json` for the next phase to read; the worker chooses neither the directory nor the name. The bounded `findings` body does enter the primary context as part of the subagent's result, exactly as the provider model states, while the worker's transcript, reads and tool traffic stay isolated. `report` is a producer: it writes the drift report inside the candidate root with Edit and Write (Codex: `apply_patch`) and names it. At `devforgeai ingest-result` the sequencer derives `changed[{path, blob_sha256, kind}]` from the candidate root's checkpoint diff, refuses the result when `changed` is not a subset of `claimed_paths` (`UNCLAIMED_CHANGE`) or when any changed path is outside the fence, runs the transition oracle inside the root, writes `<phase>-result.json` with `changed` and the checkpoint ref, creates the next checkpoint and releases the lease.

```yaml
schema: devforgeai.worker-result/v1
run: "drift-shop"
skill: "drift"
phase: "code_map"
agent: "code_mapper"
status: pass | fail | needs_user | could_not_run
reason_code: runner_missing | timeout | network | hook_fault | provider_tool_refused | prerequisite_missing | checkpoint_fault   # required only when status is could_not_run
candidate:
  id: "drift-shop"
  input_checkpoint: "base"
claimed_paths: []          # empty for code_map and doc_diff, and for any non-pass status
evidence_refs: []          # at most 16 paths, root-relative or under .devforgeai/work/<run>/
note: "142 paths, one manifest, two configuration files; three facts recorded as unknown."
issues: [{id, kind, text}] # at most 10
next: ""                   # omitted: no drift phase declares rewind_to
```

Unknown keys are refused. `issues[]` is the bounded routing summary a reader sees in the handoff; a judge's full row set travels in `findings`, which the sequencer persists as `.devforgeai/work/<run>/evidence/<agent>/findings.md` and the next phase and `drift_writer` read by path.

`gate_policy` (`BLOCK | REQUIRE_HUMAN | WARN | OFF`) is a defect-to-action map declared in the consumed artifact, never a status returned here. A document run carries the fixed map `{unresolvable_source: BLOCK}`.

## 7. Procedure

### 7a. Steps

The body of `SKILL.md`. The primary window does exactly this and nothing else.

1. Determine the argument: use the positional one when given, otherwise the `slug` recorded in `state.yaml`. If neither exists, run `devforgeai status`, print it, and stop with the instruction to re-run naming a slug — why: `devforgeai phase start` substitutes the argument into the fence pattern, so an empty one fences nothing.
2. Run `devforgeai phase start drift <slug>`. Print stderr verbatim and stop on exit 1 or 2 — why: the gate is the only thing that decides a run may open.
3. Read the active phase from that output or from `devforgeai status`, and load `references/<phase>.md` — why: each reference file holds one phase's guidance, so the primary window never carries three phases of detail.
4. Dispatch that phase's worker through the target's native worker mechanism, passing only the run id, the skill name, the phase name and the file paths the reference file names. Do not paste document or source content into the prompt — why: the observed map is the largest thing this skill handles and the primary window persists for the whole run.
5. Wait for the worker to return. The `SubagentStop` hook has already handed its envelope to `devforgeai ingest-result`, which validated it, applied any files, ran the oracle and advanced, retried or blocked.
6. Run `devforgeai status`. If a new phase is active, go to step 3. If the run is finished or blocked, print the handoff block the sequencer rendered and stop; a blocked run's block already names the command that resumes it.
7. When the block reports the run `ready_to_promote` and the user asks for the promotion, call `devforgeai promote <run>` and print the second block the promotion rendered — why: promotion is never automatic, it is what moves `docs/reports/drift-<slug>.md` from the candidate root into the canonical checkout under the lock, and a `REQUIRE_HUMAN` block is the only state in which the model may ask for it.
8. If the user abandons the run, call `devforgeai phase fail --reason <text>` — why: that is the only way a `BLOCK` handoff and a cleared enforcement block get written.

### 7b. Sub-phases and workers

Gate, Record, Slice and Handoff dispatch no LLM: they are `devforgeai` sequencer operations. Slice runs inside `devforgeai phase start`, which resolves the incoming artifact's already-hashed context bundle and writes `.devforgeai/work/<run>/context.json`, whose path every worker of the run is handed (open item OI-1, section 9).

| # | Sub-phase | Registry phase | Performed by | Isolation |
|---|-----------|----------------|--------------|-----------|
| 0 | Gate | — | sequencer: `devforgeai phase start drift <slug>` | n/a |
| 1 | Slice | — | sequencer: `devforgeai phase start` writes `.devforgeai/work/<run>/context.json` | n/a |
| 2 | Work | `code_map` | worker: `code_mapper` (owned by `onboard`, dispatched here) | required |
| 3 | Work | `doc_diff` | worker: `doc_differ` | required |
| 4 | Write | `report` | worker: `drift_writer` | required |
| 5 | Record | — | sequencer: `devforgeai ingest-result`, then `devforgeai phase next` | n/a |
| 6 | Handoff | — | sequencer: `devforgeai phase next` marks the run `ready_to_promote` and writes the `REQUIRE_HUMAN` block whose only forward step is `devforgeai promote <run>`; `SKILL.md` runs that command only after the user confirms in the session, and the promotion writes the run's second handoff block | n/a |

`drift` has no Review sub-phase: the registry gives it three phases and none of them is a critic. `code_mapper` and `doc_differ` are separate workers so the worker that observes the repository is not the worker that judges a document against it.

Every phase of one run works inside the same candidate root — `.devforgeai/work/<run>/wt`, created by `devforgeai phase start` and named to each worker as `candidate.root` in the status block the primary window pastes into the dispatch prompt alongside `run`, `phase`, `fence` and `granted_keys`. `code_map` and `doc_diff` are judges: they hold no write tool and write nothing anywhere, and the sequencer persists each one's returned `findings` to `.devforgeai/work/<run>/evidence/<agent>/findings.md`, which is outside the root. `report` writes one file in the root. The sequencer checkpoints the root at each transition, so the phases build linearly with no merge between them, and the one producer holds the run's lease from dispatch to `devforgeai ingest-result`. Promotion is never automatic and is no part of Handoff: the last passing `devforgeai phase next` marks the run `ready_to_promote` and writes a `REQUIRE_HUMAN` handoff whose only forward step is `devforgeai promote <run>`, and `SKILL.md` runs that command only after the user confirms in the session. That command, not the transition, is what merges the candidate root into the canonical checkout under `.devforgeai/lock`, and it is what refuses with `STALE_BASE` when canonical HEAD has moved past the run's recorded `base_ref`, with `DIRTY_TARGET` when the canonical report path is dirty, and with `MERGE_CONFLICT` when a rebase inside the root conflicted; a refused promotion leaves the run `ready_to_promote` with its candidate root intact for a retry.

### 7c. Evidence and gate table

`<run>` is `drift-<slug>`. Attempt budget is 2 for every phase; there is no `rewind_to`, so no drift result may carry `next`.

| phase | worker | deterministic gate check | gate_policy | evidence file | transition oracle |
|---|---|---|---|---|---|
| `code_map` | `code_mapper` | run gate: skill known, no run already active, no active or `ready_to_promote` run whose fence overlaps this one (`FENCE_OVERLAP`), and the fence entry `docs/reports/drift-<slug>.md` is repository-relative, free of `..`, and not sequencer-owned; `candidate open` creates the root and pins `base_ref`. At `ingest-result`: `writes: none`, so the checkpoint diff of the root is empty: this worker holds no write tool at all, `PreToolUse` denies every write path without exception, and a non-empty root diff is `UNCLAIMED_CHANGE`. The phase-agent binding check requires the stop event's canonical `agent_type` to be `code_mapper`, so a differently named profile is refused rather than accepted. `issues` at most 10 rows, `evidence_refs` at most 16 paths, `note` at most 16384 bytes, `findings` required on a pass or fail receipt, optional on needs_user or could_not_run, and at most 16384 UTF-8 bytes, which the sequencer persists at `SubagentStop` to `.devforgeai/work/drift-<slug>/evidence/code_mapper/findings.md` | document run's fixed map `{unresolvable_source: BLOCK}`; an oversize or malformed envelope is a protocol refusal that does not consume an attempt | `.devforgeai/work/drift-<slug>/code_map-result.json`, `code_map-report.md`, `.devforgeai/work/drift-<slug>/evidence/code_mapper/findings.md` | `report_only`: no file outside the fence changed since the gate snapshot and the whole-tree package and import policy holds |
| `doc_diff` | `doc_differ` | as `code_map`: `writes: none`, an empty root checkpoint diff, and the receipt bounds — `findings` included — enforced before anything is recorded; the phase grants no stack command key, so a `devforgeai run` call from this worker is refused for a missing hook marker | as above | `.devforgeai/work/drift-<slug>/doc_diff-result.json`, `doc_diff-report.md`, `.devforgeai/work/drift-<slug>/evidence/doc_differ/findings.md` | `report_only`: as `code_map` |
| `report` | `drift_writer` | at `ingest-result`: `changed` derived from the checkpoint diff is exactly one path, `docs/reports/drift-<slug>.md`, it is a subset of `claimed_paths` (`UNCLAIMED_CHANGE` otherwise), it canonicalises inside the candidate root, it equals the fence entry, it is allowed by `writes: docs`, and it is at most 1 MiB; then the whole-tree package and import rescan | as above; a change under `docs/architecture/**` or at `.devforgeai/stack.yaml` is `write_fence_violation`, which refuses the result with no `gate_policy` consulted | `.devforgeai/work/drift-<slug>/report-result.json`, `report-report.md` | `document`: `docs/reports/drift-<slug>.md` exists on disk in the root. On pass this is the last phase: the run becomes `ready_to_promote` and the handoff's `next` is `devforgeai promote <run>`; `/status` is the `next` of the second handoff, written when that promotion succeeds. A promotion refused with `STALE_BASE` or `DIRTY_TARGET` leaves the run `ready_to_promote` for `devforgeai promote <run>` |

Two limits from `10-sequencer-and-contracts.md` section 3.2 apply to every row: every `devforgeai phase start` defect is a refusal whatever a declared policy value says, and at transition time only `test_runner_missing` changes behaviour. `drift` brokers no stack command key, so that class reaches it only through a synthesised `could_not_run`.

### 7d. Worker contracts

Each block below is a compilable subagent definition and the body of `agents/<role>.md`, except `code_mapper`: that file is `onboard`'s, and the block below states the requirements `drift` places on the shared contract rather than a second copy of it. `name` is the canonical registry worker name, because the stop event's `agent_type` is compared against it. `description` is the sentence the primary window matches when it decides to dispatch. `writes` is `none` for a judge — it carries no `Write`, no `Edit` and no `apply_patch`, and the sequencer persists its returned `findings` to `.devforgeai/work/<run>/evidence/<agent>/findings.md`, never into the candidate root — and `candidate` for a producer, following the registry's `writes` column: `drift` declares `none` on its first two phases and `docs` on the third, so two judges and one producer. `compiled_to` names the two provider-native files `skill-generator` emits from the block; each body follows `templates/agent-md.md` in four parts — job, inputs, rules, receipt — and the producer's job sentence leads with what it writes.

```yaml
name: code_mapper
skill: onboard          # owned by onboard; dispatched unchanged by drift's code_map phase
description: Dispatch this worker first in a drift run to record what the repository actually contains — paths, manifests, configuration — each fact with the file it was read from.
writes: none            # under drift's code_map phase; onboard's code_map phase declares candidate
tools: [Read, Grep, Glob, Bash]          # under drift this worker holds no write tool at all; onboard's dispatch adds Edit and Write inside the candidate root
model: inherit
skills: []
responsibility: Record the repository's paths and its directly observed manifest and configuration facts, each with a source citation, and report anything not explicitly present as unknown.
inputs:
  - .devforgeai/work/<run>/context.json, the bundle the gate sliced
  - the repository tree, minus the directories the sequencer's walk ignores
  - manifests and configuration files, read as text
outputs:
  - under drift's code_map phase: findings, the observed map with its paths, manifests, packages and commands and its unknown rows, every row carrying the path it was read from and, for a manifest fact, a line range; required on a pass or fail receipt and optional on needs_user or could_not_run, at most 16384 UTF-8 bytes, persisted by the sequencer to .devforgeai/work/<run>/evidence/code_mapper/findings.md; issues[] carrying at most ten rows for the facts recorded as unknown; note carrying the observed counts, and the count returned against the count found whenever the map did not fit; and evidence_refs[] naming the manifests behind the rows but never its own findings path, which does not exist until the sequencer has persisted it
  - under onboard's code_map phase, whose writes mode is candidate: the same receipt fields plus the .devforgeai/stack.yaml file onboard's specification has it write inside the candidate root and name in claimed_paths, which drift neither requires nor forbids
must_not:
  - guess a language, package manager, build, test, lint or format value that no file states; record it under unknown
  - write any file anywhere under drift's dispatch; that profile holds no write tool and its map travels in findings
  - paraphrase a manifest line instead of citing its path and line range
isolation: required
returns: devforgeai.worker-result/v1
compiled_to:
  - .claude/agents/drift-code_mapper.md and .claude/agents/onboard-code_mapper.md
  - .codex/agents/drift-code_mapper.toml and .codex/agents/onboard-code_mapper.toml
body: job, inputs, rules, receipt
```

The two compiled files carry the same `name: code_mapper`, because that is the string the stop event's `agent_type` carries and the phase-agent binding check compares. They differ in their tool list and their `writes` line — `none` with no write tool at all for drift, its map returned in the receipt's `findings`; `candidate` with `Edit` and `Write` in the candidate root for onboard — because their phases declare different write modes, and they are named for their skill so both can sit in one `.claude/agents/` directory. Which of the two a dispatch resolves to is the primary window's choice: `drift`'s `SKILL.md` names `drift-code_mapper` and `onboard`'s names `onboard-code_mapper`. Section 9 records the name collision this creates and why it is resolved at the filename rather than at `name`.

```yaml
name: doc_differ
skill: drift
description: Dispatch this worker after code_map to judge the INTENDED sections of the architecture documents against what the repository was observed to contain, and return one row per disagreement.
writes: none
tools: [Read, Grep, Glob, Bash]
model: inherit
skills: []
responsibility: Compare the observed facts against the INTENDED sections of the sourcetree, techstack and architecture documents and return one row per disagreement.
inputs:
  - .devforgeai/work/drift-<slug>/code_map-result.json and .devforgeai/work/drift-<slug>/evidence/code_mapper/findings.md, the persisted observed map that result file names
  - docs/architecture/sourcetree.md, techstack.md, architecture.md, section by section
outputs:
  - findings: every disagreement with an id matching DRIFT-NNN, the document, the anchor, what the document says, what was observed, the repository citation, and a kind of doc-only, code-only or conflict; required on a pass or fail receipt and optional on needs_user or could_not_run, at most 16384 UTF-8 bytes, persisted by the sequencer to .devforgeai/work/<run>/evidence/doc_differ/findings.md
  - issues[]: at most 10 rows drawn from those rows, so the handoff prints them as open items
  - note: the count of rows by kind across every section compared, and the count returned against the count found whenever the rows did not fit
  - evidence_refs[]: the code_map result and the document anchors the rows cite; never its own findings path, which does not exist until the sequencer has persisted it
must_not:
  - write any file anywhere; this worker holds no write tool and its rows travel in findings
  - report an OBSERVED section as drift; OBSERVED is advisory and INTENDED binds
  - resolve a disagreement in favour of either side, or draft document text
  - emit a row without a document anchor and a repository citation
isolation: required
returns: devforgeai.worker-result/v1
compiled_to:
  - .claude/agents/drift-doc_differ.md
  - .codex/agents/drift-doc_differ.toml
body: job, inputs, rules, receipt
```

```yaml
name: drift_writer
skill: drift
description: Dispatch this worker last in a drift run to write the drift report, with every row carrying its citation and an action naming the command and the owning skill.
writes: candidate
tools: [Read, Grep, Glob, Edit, Write, Bash]
model: inherit
skills: []
responsibility: Write the drift report inside the candidate root, with every row carrying its citation and every row an action naming the command and the owning skill.
inputs:
  - .devforgeai/work/drift-<slug>/code_map-result.json and doc_diff-result.json, and the two persisted judge findings those result files name: evidence/code_mapper/findings.md and evidence/doc_differ/findings.md
  - assets/drift-report.md, the drift-report skeleton
outputs:
  - docs/reports/drift-<slug>.md, written under the candidate root with Edit or Write and named in claimed_paths, with Sourcetree Drift, Techstack Drift, Architecture Drift and Actions filled and depends_on listing each document anchor it cites
  - evidence_refs[]: the two preceding result paths and the two persisted judge findings the rows were rendered from
must_not:
  - write or claim any path under docs/architecture/ or .devforgeai/, both outside this run's fence
  - add a drift row the two persisted judge findings do not carry
  - return a findings key; findings is a judge field and a producer receipt carrying it is refused
  - write an action for a document that does not exist without naming architect as its owner
  - write or claim any path other than docs/reports/drift-<slug>.md
isolation: required
returns: devforgeai.worker-result/v1
compiled_to:
  - .claude/agents/drift-drift_writer.md
  - .codex/agents/drift-drift_writer.toml
body: job, inputs, rules, receipt
```

The two judges hold `Read`, `Grep`, `Glob` and `Bash` and no write tool of any kind, so neither can touch the documents or the code it judges, and each row set comes back in the receipt's `findings` for the sequencer to persist. `drift_writer` is the one producer and holds `Edit` and `Write` inside the candidate root, scoped by the `PreToolUse` check and compiled to `apply_patch` on the Codex target. No `drift` phase grants a stack key, so no worker is granted a `devforgeai run` key, and no worker holds a git write, a package manager, a network tool or a raw stack command. `isolation` above is the framework's `required | preferred` declaration, not Claude's subagent `isolation` key, which the framework never sets. `hooks`, `memory`, `background` and `permissionMode` are Claude-only keys this skill leaves unset. `tools` names tools only: a Claude Code subagent's `tools:` frontmatter accepts tool names and MCP server patterns, never a command pattern, so the hook dispatcher is the only command-level bound. A judge's `Bash` runs `devforgeai status` and the dispatcher's read-only command set (`cat cmp cut diff echo grep head jq ls pwd rg sha256sum tail test tr wc`, plus read-only git subcommands inside the root) and nothing else; a producer's additionally runs `devforgeai run KEY` for its granted keys.

Each worker's envelope must carry `run`, `skill` and `phase` equal to the enforcement block. The primary window forwards those three ids in the dispatch line; a worker may also read them from `devforgeai status`, which is the one sequencer operation a phase worker may call. `code_mapper` needs those ids to fill `skill: drift` and `phase: code_map` when this skill dispatches it, and `skill: onboard` when `onboard` does.

### 7e. Handoff outcomes

`handoff.outcomes` as the skill declares it. The sequencer selects the row by envelope status and fills the placeholders from state, so the rows are keyed on status, not on narrative outcome. `{slug}` is the run argument.

| Outcome | Selected when | Next steps |
|---------|---------------|------------|
| `ready_to_promote` | the last phase passed; the run's work is complete and unpromoted | 1. `devforgeai promote {run}` — the first of the run's two handoff blocks; `SKILL.md` runs the command only after the user confirms in the session, and the promotion writes the second block, whose row is one of the two below. |
| `pass` | all three phases passed and `doc_diff-result.json` carries no row | 1. `/status`. The report's three drift sections are empty and its Actions table is empty. |
| `pass` | all three phases passed with drift rows | 1. `/status`. Open items carry one `/amend {doc} "{change}"` per `issues[]` row, printed before the next step; `docs/reports/drift-{slug}.md` holds the full Actions table when it exceeds the ten-row cap. Also possible: `/architect {slug}` for the rows whose owner is architect. |
| `REQUIRE_HUMAN` | any phase returned `needs_user`; the run blocks at that phase on the first ask with no retry — status stays `active`, the lease is released, `run.yaml#blocked_at` names the phase and the candidate root survives | 1. `/drift {slug}`, which resumes the blocked run at `blocked_at` with attempts reset. The answer is a change on disk — a slug argument, or a document the question named — not a reply in the session. Also possible: `devforgeai phase fail --reason <text>` to abandon the root, then `/status`. |
| `REQUIRE_HUMAN` | a phase returned `fail`, or its oracle reported problems, at the attempt limit of 2; the run blocks and keeps its root | 1. fix the cause `repair_route` names — the phase and its report file — then `/drift {slug}`, which resumes the blocked run at `blocked_at` with attempts reset. When the failing input is a missing architecture document the route names `/architect {slug}`, and running it needs `devforgeai phase fail --reason <text>` first, because the blocked run still holds the fence. Also possible: `devforgeai phase fail --reason <text>`, then `/status`. |
| `REQUIRE_HUMAN` | `could_not_run`; also the synthesised result the sequencer writes when a `SubagentStop` event arrives carrying no `agent_type` or `agent_id` | 1. repair the dependency named by `reason_code`, then `/drift {slug}`. |
| `BLOCK` | the primary window called `devforgeai phase fail --reason`, which is the route when a dispatch cannot start at all — an absent `code_mapper` profile is the expected case, because no subagent starts and therefore no stop event fires | 1. install `onboard`, whose package carries the `code_mapper` profile, then `/drift {slug}`. The sequencer's own `BLOCK` default renders `/drift {slug} --fix`, which opens a fresh run from phase 1. |

`drift` invokes no other skill. Its edges to `amend` and `architect` are handoff rows and Actions rows: the finishing run's `next` names the command and a human or a fresh session runs it (open item OI-7, section 9).

## 8. Bundled resources

### Layout (fixed)

```
drift/SKILL.md              # <=500 lines: identity, phase list, dispatch loop, handoff table
  references/code_map.md
  references/doc_diff.md
  references/report.md
  references/envelope.md
  agents/doc_differ.md
  agents/drift_writer.md
  scripts/observed_map.py
  assets/drift-report.md
```

There is no `agents/code_mapper.md` in this package. The file lives at `.devforgeai/skills/onboard/subagents/code_mapper.md` and is installed by `onboard`; provider agent names are global, so a second profile with the same name would collide with it. `drift` dispatches the canonical name and ships `references/code_map.md`, which states what the shared worker must return under a `writes: none` phase.

Link depth: `SKILL.md` links to `references/`, `agents/`, `scripts/` and `assets/`; an `agents/*.md` links to `references/*.md`; nothing links further.

### scripts/
| File | Purpose | Invocation | Exit codes |
|------|---------|------------|------------|
| `observed_map.py` | Print, as JSON on stdout, the repository paths and manifest file list a drift run would see, applying the same ignored-directory set the sequencer's tree walk applies. A human runs it to check what the mapper had available, or to diff two points in time; nothing in a run may execute it, because the worker Bash grammar is `devforgeai run *` as declared surface only and the primary window's grammar is the four model-callable operations. | `python scripts/observed_map.py --root . --manifest-glob 'pyproject.toml' --manifest-glob '**/*.csproj'` | 0 printed, 1 root unreadable, 2 usage |

The script prints JSON to stdout and every diagnostic to stderr, never prompts, and documents `--help`.

### references/
| File | Content | Load when |
|------|---------|-----------|
| `code_map.md` | which directories the walk ignores, what a citation must carry (path, and a line range for a manifest fact), the rule that an absent value is recorded as unknown rather than inferred, the shape of the observed map this phase returns in the receipt's `findings`, which the sequencer persists as `.devforgeai/work/<run>/evidence/code_mapper/findings.md`, the counts its receipt carries in `note`, and the rule that under `drift` it holds no write tool and writes nothing anywhere | before dispatching `code_mapper` |
| `doc_diff.md` | how to read `code_map-result.json`, which sections of the three documents are compared, the OBSERVED and INTENDED distinction from `03-brownfield.md`, the three drift kinds, and the rule that a missing document is one row rather than a failure | before dispatching `doc_differ` |
| `report.md` | the `drift-report` template's four sections, the single `DRIFT-NNN` sequence shared across them, how `depends_on` is filled from the cited document anchors, and how each drift kind maps to an action command and an owning skill | before dispatching `drift_writer` |
| `envelope.md` | the `devforgeai.worker-result/v1` schema, its field bounds — `findings` included, at 16,384 UTF-8 bytes, carried on a judge receipt and forbidden on a producer's — the fixed path the sequencer persists `findings` to, and the rule that the final message is exactly one such object with no Markdown fence | every dispatch |

### assets/
| File | Used for |
|------|----------|
| `drift-report.md` | seeds `docs/reports/drift-<slug>.md`; carries the `drift-report` template header (`template_version: 1`, `id_pattern` `^DRIFT-[0-9]{3}$`, required sections Sourcetree Drift, Techstack Drift, Architecture Drift, Actions) |

### agents/
| File | Worker (from section 7d) | writes | tools | compiled to |
|------|-------------------------|--------|-------|-------------|
| not shipped by `drift`; `onboard` owns the `code_mapper` contract, and `drift` compiles its own dispatch of it | `code_mapper` | none | Read, Grep, Glob, Bash | `.claude/agents/drift-code_mapper.md`, `.codex/agents/drift-code_mapper.toml` |
| `doc_differ.md` | `doc_differ` | none | Read, Grep, Glob, Bash | `.claude/agents/drift-doc_differ.md`, `.codex/agents/drift-doc_differ.toml` |
| `drift_writer.md` | `drift_writer` | candidate | Read, Grep, Glob, Edit, Write, Bash | `.claude/agents/drift-drift_writer.md`, `.codex/agents/drift-drift_writer.toml` |

## 9. Gotchas and edge cases

| Situation | What goes wrong | What to do instead |
|-----------|-----------------|--------------------|
| `code_mapper` is dispatched by both `onboard` and `drift` | This is the single exception to the no-borrowing rule in `01-skill-anatomy.md`, recorded in `11-artifact-registry.md#6-known-divergences`. Shipping a second `agents/code_mapper.md` would install two provider profiles under one global name. | `onboard` owns the file. `drift` ships none, dispatches the canonical name, and states its requirements on the shared contract in section 7d and `references/code_map.md`. The acceptance check in section 14 expects two agent files, not three. Where that profile is not installed, the dispatch never starts a subagent, so no `SubagentStop` event fires and the sequencer observes nothing: the run stays open with the failure in the primary window, and the exit is `devforgeai phase fail --reason`, whose `BLOCK` handoff names installing `onboard` before `/drift <slug>`. |
| The shared worker faces two different `writes` modes | Under `onboard` the `code_map` phase writes documents inside the candidate root; under `drift` it writes nothing at all and returns its map in the receipt's `findings`, and any change in the root's checkpoint diff is refused as `UNCLAIMED_CHANGE`. One profile serving both would either give the drift dispatch a write tool over the repository it must not have, or leave the onboard dispatch unable to finish its phase. | Two profiles, one name. `drift-code_mapper` declares `writes: none` and carries no `Write`, `Edit` or `apply_patch`, the sequencer persisting its returned `findings` to `.devforgeai/work/<run>/evidence/code_mapper/findings.md`; `onboard-code_mapper` declares `writes: candidate` and carries `Edit` and `Write` inside the candidate root. Both carry `name: code_mapper`, which is the string the stop event's `agent_type` binds against, and each skill's `SKILL.md` dispatches its own file. The worker fills `skill` and `phase` from the ids the primary window forwards, or reads them from `devforgeai status`. |
| Where a judge's rows live | The receipt has no bounded `evidence` object, and a large repository has more observed facts and more drift rows than `issues[]` can carry | Each judge returns its full row set in the receipt's `findings`, which the sequencer persists to `.devforgeai/work/<run>/evidence/<agent>/findings.md` and records in `<phase>-result.json`; `issues[]` is the bounded routing summary the handoff prints, and `drift_writer` reads the two persisted files by path. |
| `findings` is capped at 16,384 UTF-8 bytes and `code_mapper` enumerates a whole repository | This is the sharpest case of the cap in the roster: the observed map carries one row per path plus every manifest, package and command fact with its citation, and a large repository exceeds 16 KiB before the drift rows are even drawn. An oversize `findings` is refused like any other receipt defect, so `code_map` would fail on a bound rather than on what it observed, and `doc_differ` would compare against a truncated map without knowing it | Not reconciled, and recorded rather than papered over. `WRITE-MODEL-REVISION.md` D13 item 5 forbids a `findings.json` or `notes.txt` side channel and item 9 defers the structured evidence broker that would carry a map this size to `12-post-mvp.md`. What this spec promises today is the bounded form: `code_mapper` returns the manifest, package and command facts and the `unknown` rows first, then path rows until the budget is spent, and its `note` states the count returned against the count found whenever the two differ; `doc_differ` reads that `note` and records any section it could not compare as `unknown` rather than as drift. A repository whose observed map does not fit is a real limit of this skill, not a checked constraint, and the broker contract is the fix. Under `onboard`'s dispatch the same worker is a producer and writes `.devforgeai/stack.yaml` inside the candidate root, so the cap does not apply there. |
| OI-10: `/drift` takes no positional argument | `devforgeai phase start <skill> <arg>` requires one and the fence pattern substitutes it, so an empty argument fences nothing. | The adapter passes `state.yaml`'s `slug`. With no slug and no explicit argument it opens no run at all: it prints `devforgeai status` and the instruction to re-run as `/drift <slug>`. `devforgeai phase fail` is not available, because that operation requires an active run. |
| OI-1: which component performs Slice | A spec promising a slice worker would describe an agent file with no registry phase to run it. | Slice is a sequencer step inside `devforgeai phase start`: it writes `.devforgeai/work/<run>/context.json`, whose path every worker of the run is handed. No framework worker performs it and this package ships no agent file for it. |
| OI-2 and section 3.4: which digests a gate re-resolves | A drift report's `depends_on` entries look like they are checked when the report is read. | The story gate re-resolves `provenance[]` and `context[]` on a story run. Nothing re-resolves a report's `depends_on` today, so the digests `drift_writer` records are evidence for a human and for `/analyze`. A digest that resolves is not a promise that the sentence it covers is still true; that gap is exactly what this skill reports. |
| OI-3: worker tools | A generator that gives every worker one list either leaves `drift_writer` with no way to write the report, or gives `code_mapper` a write tool over the repository it was asked to observe. | Tools are per role. `code_mapper` and `doc_differ` are judges under `drift` and hold `Read`, `Grep`, `Glob` and `Bash` and no write tool at all, their rows returned in the receipt's `findings`. `drift_writer` holds `Edit` and `Write` inside the candidate root, scoped by the `PreToolUse` check. No drift phase grants a stack command key, so no worker is granted a `devforgeai run` key. |
| OI-4: a worker returns `fail` with no rewind target | Nothing in section 5.4 lists that row, so it looks like a silent pass. | `examples/hooks/devforgeai.py:1017-1018` inserts the reported failure as a transition problem, so the phase retries to its limit of 2 and then blocks `REQUIRE_HUMAN`. No drift phase declares `rewind_to`, so a drift result carrying `next` is refused at `ingest-result`. |
| OI-5: `--fix` and `--retry` look like resume flags | An earlier draft closed the run on `needs_user` and at an exhausted attempt budget, so no flag could resume anything. | Settled: `10-sequencer-and-contracts.md` sections 2 and 3.1 leave such a run `active` with its lease released, its candidate root kept and `run.yaml#blocked_at` naming the phase, and `devforgeai phase start drift <slug>` — same skill, same argument — resumes it there with attempts reset. Resuming is the command, not a flag: `/drift {slug}` does it. With no blocked run to resume, the same call opens a fresh run from phase 1; every flag only changes what the workers read. |
| OI-7: `02-skill-roster.md` says drift suggests `/amend` or `/architect --update` | A suggestion is not an invocation, and `devforgeai phase start` refuses while a run is active. | Both edges are Actions rows in the report and open items in the handoff. The drift run never invokes them. The architect edge is written `/architect {slug}` with no flag: `SKILL-SPEC-008-architect.md` section 9 records that `--yolo` is the only flag that skill defines and that the roster's `--update` is not implemented, so an Actions row naming it would name a command architect refuses. |
| OI-8: worker naming | `05-subagent-sets.md` writes `code-mapper` and `doc-differ`; the registry writes `code_mapper` and `doc_differ`. | The registry name is canonical and is what `agent_type` is compared against by the phase-agent binding check at `ingest-result`. Use it in section 7, in the `agents/` filenames and in the evidence table. |
| Drift found in `techstack.md` also invalidates `.devforgeai/stack.yaml` | Only `architect`'s `techstack` phase and `onboard`'s `code_map` phase may write that file, so a drift run cannot refresh the commands or the package policy that every story pins by hash. | `drift_writer` adds an Actions row naming `/architect <slug>` whenever a techstack drift row concerns a command, a manifest or a package. The row is data in the report, not an invocation. |
| The tree walk skips ignored directories | The sequencer's walk skips `.devforgeai/`, `.git/`, the provider directories and the usual build and cache directories, so files inside them are never hashed or compared. A mapper that walked them would report drift the framework cannot see. | `code_mapper` applies the same ignored-directory set, and `references/code_map.md` names it. A document claim about an ignored directory is reported as `unknown`, not as agreement. |
| The document gate checks the fence, not the documents | `devforgeai phase start drift shop` opens a run in a repository with no `docs/architecture/` at all. | `doc_differ` emits one row per missing document, kind `code-only`, action `/architect <slug>`. The run passes: an empty architecture set is a legitimate finding, not a failure. |
| OBSERVED sections in the three documents | Treating an OBSERVED section as a rule would turn `onboard`'s advisory notes into drift rows against the code they were copied from. | OBSERVED is advisory and INTENDED binds (`03-brownfield.md#observed-vs-intended`). `doc_differ` compares INTENDED sections only and records the count of OBSERVED sections it skipped in `note`. |
| The run id is `drift-<slug>` | Re-running drift for the same slug reuses the run directory, so the second run overwrites `.devforgeai/work/drift-<slug>/*-result.json`. | The durable record is `docs/reports/drift-<slug>.md` plus one `provenance/log.jsonl` line per run. Compare two reports, not two work directories. |
| Which worker may write, and where | A generator that treated the three workers alike would let `doc_differ` rewrite the architecture document it was asked to judge, and the drift report would then describe a repository nobody observed | Roles follow the registry's `writes` column: `code_map` and `doc_diff` compile to judges declaring `writes: none`, with no write tool and reports returned in `findings`; `report` declares `docs` and compiles to a producer holding `Edit` and `Write`. Its one write lands inside the candidate root and is named in `claimed_paths`; the sequencer derives what actually changed from the checkpoint diff and refuses anything unclaimed as `UNCLAIMED_CHANGE`. |
| D13 (2026-09-03): both judges had an evidence-directory `Write`, and the shared `code_mapper` contract was split on it | Claude Code 2.1.259 refuses a subagent's `Write` of a report-like Markdown file before any hook runs, so under `drift` the shared worker could not be relied on to write `observed.json` and `doc_differ` could not be relied on to write `rows.json`; `doc_differ` and `drift_writer` would each read a file that may not exist, and the two-profile story rested on a `Write` the provider may refuse | `WRITE-MODEL-REVISION.md` D13 applied here: under `drift` both `code_mapper` and `doc_differ` declare `writes: none` (R9, the section 7c rows, the section 7d headers and the shared-contract note, the section 8 `agents/` table, the section 12 Tools and target rows, section 14's anatomy check) and carry `Read`, `Grep`, `Glob`, `Bash` with no `Write`, `Edit` or `apply_patch`. Each returns its rows in the receipt's `findings` string, at most 16,384 UTF-8 bytes, which the sequencer persists verbatim at `SubagentStop` to `.devforgeai/work/<run>/evidence/<agent>/findings.md`; `observed.json` and `rows.json` are gone. `doc_differ` and `drift_writer` read the persisted paths (section 7d inputs), section 7c names them in the evidence-file column, and no judge names its own findings path in `evidence_refs`, because that file does not exist when the receipt is validated. The two profiles still differ, but now over the whole write surface rather than over a `Write` destination: `drift-code_mapper` has none, `onboard-code_mapper` has `Edit` and `Write` in the candidate root. The bounded `findings` body does enter the primary context as part of the subagent's result (D13 item 4); what stays isolated is the worker's transcript, reads and tool traffic. Earlier revisions of `10-sequencer-and-contracts.md` and `09-hook-dispatcher.md` carried the superseded evidence-writing branch; D13 is now applied in those documents and here. |
| Where the drift report ends up | A reader expects `docs/reports/drift-<slug>.md` in the working tree the moment `report` passes | The write lands in the candidate root `.devforgeai/work/<run>/wt`, which is gitignored. The report reaches the canonical checkout only at `devforgeai promote <run>`, never at Handoff: the last passing `devforgeai phase next` marks the run `ready_to_promote` and writes a `REQUIRE_HUMAN` handoff whose only forward step is that command, and `SKILL.md` runs it only after the user confirms in the session. A promotion refused with `STALE_BASE`, `DIRTY_TARGET` or `MERGE_CONFLICT` — all three refuse the promote command, not the transition — leaves the run `ready_to_promote` with its candidate root intact, and `devforgeai promote <run>` retries it once the user has resolved the reason. |
| A `REQUIRE_HUMAN` run treated as closed, with `/status` as its next step | `needs_user` and an exhausted attempt budget were described as closing the run, so the section 7e rows sent the user to `/status` and the OI-5 row said no flag could resume anything. A closed run has no candidate root, so the work the phases had already done appeared to be lost | Settled in `10-sequencer-and-contracts.md` (section 2's `phase start` row, section 3.1, section 5.4's `needs_user` row, section 6's `REQUIRE_HUMAN`, blocked-run row): such a run stays `active` with its lease released, keeps its candidate root and every checkpoint, and records `run.yaml#blocked_at`. `devforgeai phase start drift <arg>` — the same skill and argument — resumes it at `blocked_at` with `attempts` reset. The two section 7e `REQUIRE_HUMAN` rows, section 7a step 6 and OI-5 now name `/drift {slug}` as the forward step, with `devforgeai phase fail --reason <text>` then `/status` as the abandon route; any other skill on the same story needs that `phase fail` first. |
| Promotion read as part of Handoff | "The report reaches the canonical checkout at Handoff, when the sequencer promotes the run" made `devforgeai phase next` move canonical bytes on its own, with no point at which the user consents | Section 7b's candidate-root paragraph ("At Handoff the sequencer promotes the run"), section 7b row 6 and the row above now carry the two-block model of `WRITE-MODEL-REVISION.md` D7 and `10-sequencer-and-contracts.md` sections 5.4, 6 and 12.4: `phase next` marks the run `ready_to_promote` and writes a `REQUIRE_HUMAN` block whose only forward step is `devforgeai promote <run>`; `SKILL.md` runs that command only after the user confirms; the promotion writes the second block. |
| `STALE_BASE`, `DIRTY_TARGET` and `MERGE_CONFLICT` attributed to the transition | The refusals read as ways the last transition can fail, so a reader looks for them among the oracles | All three refuse `devforgeai promote <run>` (`10-sequencer-and-contracts.md` section 2's refusal table, section 12.4's ordered steps). The row above names the command that raises them, adds `MERGE_CONFLICT`, and states that the root and its checkpoints survive every refusal. |
| The section 7e table had no `ready_to_promote` row | The row below already told a reader to read every `pass` row as the post-promotion block, but the table itself never named the promote step, so a generator reading only the table would omit it | A `ready_to_promote` outcome row now heads the table with `devforgeai promote {run}` as its one forward step; the two `pass` rows keep `/status` and are the second block. |
| `promote <run>` was missing from the compiled grammar | Section 7f's Tools row already granted `devforgeai promote <run>`, but the section 7a procedure stopped at printing the block and the section 12 `allowed-tools` line omitted it, so the compiled skill could not run the only command its own handoff names | `WRITE-MODEL-REVISION.md` D7 propagates the fifth model-callable form everywhere the four are enumerated. A new step 7 in section 7a calls it after the user asks (the abandon step became 8), the `allowed-tools` line carries `Bash(devforgeai promote:*)`, section 12's paragraph above it says five model-callable operations rather than four, and the Tools row no longer describes the command as something reached only after a refused promotion. |
| Reading the section 7e `pass` rows as the block a finished run prints first | `10-sequencer-and-contracts.md#6-handoff-envelope` no longer carries a `document run, all phases passed` row: `/status` is now the `next` of a **promoted** document run, and a run whose phases all passed but which is not yet promoted takes `devforgeai promote <run>` instead. | Read every 7e `pass` row as the post-promotion block. The first block a finished run writes names `devforgeai promote <run>`, which the user runs; the `/status` row is what the second block carries. |
| Two `code_mapper` profiles with one `name` | Both `drift-code_mapper` and `onboard-code_mapper` declare `name: code_mapper`, and the provider warns that names should be unique within a scope | The collision is deliberate and it is resolved at the filename, not at `name`. `agent_type` on the stop event carries `name`, and the phase-agent binding check compares it against the registry's canonical worker for the active phase — which is `code_mapper` under both skills — so changing `name` would break the binding in both. The two files differ only in their tool list and `writes` line, and each skill's `SKILL.md` dispatches its own filename, so the read order between them never decides which one runs. |

## 10. Success criteria and test cases

### Success criteria

- Triggers on the section 4 positives and on none of the near-misses.
- The transcript contains exactly one `devforgeai phase start drift <slug>` and no other `devforgeai` operation except `devforgeai status` and, when the user abandons, `devforgeai phase fail --reason`.
- Three worker dispatches at most, in registry order, one per phase.
- The run's checkpoint diff holds exactly one path, `docs/reports/drift-<slug>.md`, and it is the `report` receipt's only `claimed_paths` entry; the two judge phases write nothing, and the sequencer's persisted findings sit under `.devforgeai/work/<run>/evidence/<agent>/`, which no checkpoint records and no promotion carries.
- Every drift row carries a document anchor and a repository citation; every drift row has exactly one Actions row with the same id.
- No row is emitted for an OBSERVED section.
- `SKILL.md` is under 500 lines; `agents/` holds exactly the two files in section 8.

### Fixture

The generator creates `fixtures/drift/` with exactly these files before running any eval, and copies it to `drift-workspace/fixture-<eval-id>/` per eval:

| Path | Content |
|---|---|
| `.devforgeai/state.yaml` | `version: 1`, `target: [claude]`, `mode: brownfield`, `slug: shop`, `phase: plan`, `enforcement:` an empty mapping, `next: "/status"`. No active run, so `phase start` can open one. |
| `.devforgeai/hooks/devforgeai.py`, `policy.py`, `dispatch.py` | byte copies of `docs/design/examples/hooks/devforgeai.py`, `policy.py` and `dispatch.py`, so the `SubagentStop` route applies results |
| `pyproject.toml` | a project table plus dependencies `pytest` and `pyyaml`; it names no cache library |
| `src/http/routes.py`, `src/http/middleware.py` | two small modules, enough that `src/http/` exists and `src/api/` does not |
| `src/billing/__init__.py` | one module, so a component exists that no document describes |
| `tests/test_routes.py` | one test, so the tree has a test directory |
| `docs/architecture/sourcetree.md` | `sourcetree` template v1, `mode: INTENDED`, sections `## Layout`, `## Ownership`, `## Naming`; `## Layout` states that HTTP handlers live under `src/api/` |
| `docs/architecture/techstack.md` | `techstack` template v1, `mode: INTENDED`, sections `## Languages`, `## Data Access`, `## Testing`, `## Build And Lint`; `## Data Access` states that caching uses redis |
| `docs/architecture/architecture.md` | `architecture` template v1, sections `## Components`, `## Interfaces`, `## Data Flow`, `## Failure Modes`; `## Components` lists the http and test components and does not mention billing. The file also carries one OBSERVED section, `## Deployment window`, whose status comment marks it OBSERVED |

Overlay for eval 2: `fixtures/drift/overlays/eval-2/docs/architecture/sourcetree.md`, `techstack.md` and `architecture.md` replace the base files with versions that describe `src/http/`, name no cache library, and list a billing component, so nothing drifts. Overlay for eval 3: `fixtures/drift/overlays/eval-3/.devforgeai/state.yaml` replaces the base state file with one that has no `slug` key.

### evals/evals.json (used verbatim)

```json
{
  "skill_name": "drift",
  "evals": [
    {
      "id": 1,
      "prompt": "/drift",
      "expected_output": "A drift report for the shop project naming the moved handler directory, the cache library no manifest carries, and the undocumented billing component.",
      "files": ["fixtures/drift"],
      "expectations": [
        "The transcript contains exactly one occurrence of 'devforgeai phase start drift shop', and it precedes every worker dispatch",
        "docs/reports/drift-shop.md exists and contains the headings '## Sourcetree Drift', '## Techstack Drift', '## Architecture Drift' and '## Actions'",
        "Under '## Sourcetree Drift' a row names docs/architecture/sourcetree.md#layout and cites a path under src/http/",
        "Under '## Techstack Drift' a row names docs/architecture/techstack.md#data-access and cites pyproject.toml",
        "Under '## Architecture Drift' a row names src/billing and its kind cell reads 'code-only'",
        "Every id under '## Actions' also appears in one of the three drift sections, and every action line begins with '/amend ' or '/architect '",
        "No row in the report names the heading 'Deployment window'",
        "No file under docs/architecture/ differs from the fixture copy, and no file named .devforgeai/stack.yaml was created"
      ]
    },
    {
      "id": 2,
      "prompt": "does architecture.md still match what's actually in src/?",
      "expected_output": "A drift report with three empty drift sections and an empty Actions table.",
      "files": ["fixtures/drift", "fixtures/drift/overlays/eval-2"],
      "expectations": [
        "docs/reports/drift-shop.md exists and contains no line beginning with 'DRIFT-'",
        "The report's '## Actions' section contains no line beginning with '/amend' or '/architect'",
        "The final printed handoff block lists '/status' as step 1 under 'Next steps'",
        "The transcript contains no occurrence of 'devforgeai phase next' or 'devforgeai ingest-result'"
      ]
    },
    {
      "id": 3,
      "prompt": "/drift",
      "expected_output": "No run opens, because state.yaml records no project slug.",
      "files": ["fixtures/drift", "fixtures/drift/overlays/eval-3"],
      "expectations": [
        "The transcript contains no occurrence of 'devforgeai phase start'",
        "The transcript contains exactly one occurrence of 'devforgeai status'",
        "No file named docs/reports/drift-shop.md exists after the run",
        "The final message tells the user to re-run the command with a project slug as its argument"
      ]
    }
  ]
}
```

Quick-mode results are generation feedback only: one enabled run per eval and no baseline. They are not runtime conformance evidence, and no section of this spec gates on such evidence; the deferred contract is `12-post-mvp.md#pm-02`.

## 11. Dependencies and compatibility

| Kind | Value |
|------|-------|
| Tools | `SKILL.md`: `Read`, `Agent`, and a Bash grammar no wider than `devforgeai status`, `devforgeai phase start drift <slug>`, `devforgeai phase fail --reason <text>`, `devforgeai validate`, plus `devforgeai promote <run>`, which the last passing transition's `REQUIRE_HUMAN` block names as its only forward step and which `SKILL.md` calls only after the user asks for it. Judges: `Read`, `Grep`, `Glob` and `Bash` with no write tool; their reports travel in `findings`. The one producer: the same read set plus `Edit` and `Write` (Codex `apply_patch`) inside the candidate root. No phase grants a stack key, so no worker is granted a `devforgeai run` key. |
| MCP servers | none |
| Runtime | Python 3.11+ for `scripts/observed_map.py`; standard library only, no third-party import |
| Project commands | none. No drift phase declares a run key, so this skill resolves no `.devforgeai/stack.yaml` anchor and brokers no command. It reads manifests as text and never executes a package manager. |
| DevForgeAI/Core compatibility | DevForgeAI sequencer contract `10-sequencer-and-contracts.md` dated 2026-09-02; worker envelope `devforgeai.worker-result/v1`; `drift-report` template version 1; consumes `sourcetree` v1, `techstack` v1, `architecture` v1. Research Core: NOT_APPLICABLE. |
| Other skills | Requires `onboard` to be installed, because `onboard` owns the `code_mapper` worker profile this skill's first phase dispatches. Hands off to `amend` (one command per document row) and `architect` (`/architect {slug}`, which regenerates `.devforgeai/stack.yaml` through its `techstack` phase; that skill defines no `--update` flag). Must not conflict with `analyze`, which walks document-to-document traceability rather than documents against code. |

Deferred dependencies. Each names its `12-post-mvp.md` entry and what this skill does today without it.

- `12-post-mvp.md#pm-01`. Runtime verification that a dispatched worker ran in its own context window is deferred. Today `isolation: required` is a declaration compiled into the target profile, and `skill-validator` checks the declaration structurally.
- `12-post-mvp.md#pm-02`. There is no runtime conformance evidence for this skill. Quick-mode eval results are generation feedback and no section gates on them.
- `12-post-mvp.md#pm-06`. Only the `skip` and `quick` eval modes exist; a third mode name is a spec defect.
- `12-post-mvp.md#pm-08`. Documents produced by an earlier DevForgeAI version are read exactly as any other non-DevForgeAI document; there is no migration path, so a legacy architecture document drifts against code like any other prose.
- `12-post-mvp.md#pm-09`. A repository with several packages and package managers has no supported single stack description, so techstack rows for a second package are reported against whichever manifests the run's globs matched, and the report says which manifests it read.
- `12-post-mvp.md#pm-10`. There is no clean-checkout chain validator, so nothing outside a session re-runs this comparison. A drift report is a point-in-time observation, dated by its run's log line.

Frontmatter values derived from this table. `allowed-tools` is a space-separated string of pre-approved tool patterns, per the Agent Skills specification; the Bash entries below are the five model-callable operations, `devforgeai promote <run>` included, and nothing wider, because an unscoped `Bash` entry would exceed the grammar section 14's skill-validator check enforces.

```yaml
compatibility: "Claude Code and Codex terminals. Requires an installed DevForgeAI sequencer and hook dispatcher, plus onboard's code_mapper worker profile."
allowed-tools: "Read Agent Bash(devforgeai status) Bash(devforgeai phase start drift:*) Bash(devforgeai phase fail:*) Bash(devforgeai validate) Bash(devforgeai promote:*)"
```

## 12. Targets

The generator produces one provider-neutral semantic package and a separate adapter for each selected target when frontmatter, invocation policy, or agent configuration differs. Provider-neutral resources may be shared. Adapter directories are not required to be byte-identical or symlinked.

| Target | Install path | Invocation | Subagents | Notes |
|--------|--------------|------------|-----------|-------|
| claude | `.claude/skills/drift/` | `/drift` with an optional slug argument | provider-native workers: judges `drift-code_mapper` and `drift-doc_differ` (`writes: none`, no write tool, bounded `findings` in the receipt), producer `drift-drift_writer` (`writes: candidate`); all three carry the canonical `name` the stop event binds against | Provider-specific frontmatter keys (`argument-hint`, `disable-model-invocation`) are compiled into this target's SKILL.md only. |
| codex | `.agents/skills/drift/` plus `.codex/agents/` profiles | `$drift` with an optional slug argument | the same names; Codex custom-agent `name` equals the Claude agent frontmatter `name`, so `agent_type` needs no translation | Portable six-field frontmatter only; policy goes in target-side configuration. |
| both | separate `.claude/skills/drift/` and `.agents/skills/drift/` adapters | as above | as above | Share only provider-neutral resources; validate each adapter independently. |

```yaml
metadata:
  version: "1.0.0"
  devforgeai-spec: "SKILL-SPEC-016"
  devforgeai-target: "both"
  devforgeai-anatomy: "true"
```

Not produced by skill-creator (deferred to DevForgeAI's skill-generator): provider-native `.claude/agents/*.md` and `.codex/agents/*.toml` worker profiles, provider-specific frontmatter keys for the Claude target, and concise `AGENTS.md` sections. Hook definitions are not per-skill: `init` installs the one dispatcher and its provider fragments from `09-hook-dispatcher.md`, and this spec ships none.

A generated package is an uninstalled candidate until those provider-native controls are present and independently validated. Generation or quick-mode success is not installation authority.

## 13. Constraints

- `SKILL.md` under 500 lines and roughly 5,000 tokens, holding only identity, the ordered phase list, the dispatch loop, and the handoff table. Every other instruction lives in `references/<phase>.md`, `agents/<role>.md`, `scripts/` or `assets/`. Splitting a phase's guidance into more reference files is the correct response to the line budget; cutting content is not.
- References one level deep: `SKILL.md` links to `references/`, `agents/`, `scripts/` and `assets/`; an `agents/*.md` may link to `references/*.md`. Nothing links further.
- Hooks, state writes and phase advancement are not in the skill. Do not write an instruction the sequencer or a hook already enforces.
- No `README.md` inside the skill directory.
- No angle brackets in frontmatter. Description at most 1024 characters, name at most 64.
- Imperative voice. Explain why a step matters instead of shouting it; where an instruction is non-negotiable it is a gate, a fence or an oracle, and the text names that mechanism.
- Provide defaults, not menus. Procedures over declarations.
- No interactive prompts in scripts.
- `drift` describes and does not prescribe: it writes no architecture document, no `.devforgeai/stack.yaml` and no story, and its only write is its own report inside the candidate root.
- This package ships no `code_mapper` agent file; `onboard` owns it.

## 14. Acceptance checks

Run these before reporting done and paste their output:

```bash
# frontmatter and naming (skill-creator's own validator)
python -m scripts.quick_validate ./out/drift        # run from the skill-creator directory
# open-standard validator, if installed
skills-ref validate ./out/drift
# size budget
wc -l ./out/drift/SKILL.md                          # must be < 500
# the two worker files this skill owns, and no code_mapper.md
ls ./out/drift/agents/                              # doc_differ.md drift_writer.md
# one reference file per phase, plus envelope.md
ls ./out/drift/references/                          # code_map.md doc_diff.md report.md envelope.md
# no leftover placeholders
grep -rnE 'T[O]DO|T[B]D|[{][{]' ./out/drift || echo clean
# spec battery (from the repository root)
python3 docs/design/specs/verify.py --only v1,v2,v4
```

For non-Research anatomy skills, DevForgeAI skill-validator additionally checks: all sub-phase kinds present with Gate, Record and Handoff bound to sequencer operations; `must_not` and a `writes` declaration of `candidate` or `none` present in every agent file, with no tool wider than that declaration allows and no write tool at all on a `writes: none` file; the SKILL.md Bash grammar is no wider than the model-callable operations; handoff outcomes cover every status the skill can return, including `could_not_run`. For this skill it also checks that the `code_map` phase's dispatch resolves to `drift-code_mapper`, whose `writes` is `none`, and not to `onboard-code_mapper`, whose `writes` is `candidate`.

## 15. Provenance

| Source | Hash | Used for |
|--------|------|----------|
| `docs/design/01-skill-anatomy.md#primary-window-contract` | sha256:de7d775e46bd44c52089a3998b114a5ebb5ce6875be3ebf3dca126f5a9bbaa32 | sections 2, 7a |
| `docs/design/01-skill-anatomy.md#context-bundle-format` | sha256:7b068feb30e7cc2f66292b512ac179cd217df225fb58517d2aaadd30b25236dc | sections 6, 9 |
| `docs/design/03-brownfield.md#observed-vs-intended` | sha256:76cdea3c2760b31cc074204be8c244bffb3d582a0ceba60482aa525ce03194a8 | sections 2, 7d, 9 |
| `docs/design/03-brownfield.md#the-onboard-skill` | sha256:712484fa78944f1d90b6c6ac92ae40d63793d1be6b15bf99a8eee4132f246db5 | sections 7d, 9 |
| `docs/design/10-sequencer-and-contracts.md#4-per-skill-phase-registry` | sha256:7d655abc79fb1789e37a57227eecc279faf035a0359ffa76e93b24b56796498e | sections 7b, 7c |
| `docs/design/10-sequencer-and-contracts.md#5-worker-result` | sha256:cee716ddb3ae9b6b4405037ede3bb7c6445e0e6c8ac28382344a655d31754dcd | sections 6, 7c, 7d |
| `docs/design/10-sequencer-and-contracts.md#3-status-vocabulary-and-gate-policy` | sha256:36ffb340bd5d843cd945f7d17a590e335e491b11a60b08d4bf70e12a3a223620 | sections 7c, 7e, 9 |
| `docs/design/10-sequencer-and-contracts.md#6-handoff-envelope` | sha256:de637edceb588df104a40b57738eb263989f6603f90ece6f4d0e64fef07ffb6a | section 7e |
| `docs/design/11-artifact-registry.md#1-template-registry` | sha256:25886acb1c2963b15938f0c577c3bfd28b9807dd2dd961c59ff2b43fa00b62e2 | sections 6, 8 |
| `docs/design/11-artifact-registry.md#6-known-divergences` | sha256:8a78656458735ce54ac73010da3b8fc87bbb7017a5a9268f85b210249736b82a | sections 2, 9 |
| `docs/design/02-skill-roster.md#drift` | sha256:2e692ec945705c37a620b9742b73ecfbcd8c2e16a385a3f50155666500788e2e | sections 1, 2, 7e |
| `docs/design/05-subagent-sets.md#sets-per-skill` | sha256:9e12f3beb236a025c18d40e741c09ba675bd71d2d87f56e2b205c7556b944bf9 | sections 7d, 9 |

Mirror of `depends_on` in the frontmatter, with the section each source fed.
