---
template: skill-spec
template_version: 1
id: SKILL-SPEC-015
skill_name: retro
target: both
status: approved
author: "DevForgeAI plan skill (wave 2 spec authoring)"
date: 2026-09-02
depends_on:
  - source: docs/design/01-skill-anatomy.md#primary-window-contract
    hash: sha256:a6bbaf9af2d69f7ede18d7c40f242c42edb26d79be964ffec3f386d6347014c2
    excerpt: "**The model dispatches, the sequencer decides.** For an anatomy-governed skill, the primary window (provider entry adapter + skill orchestration) does light, trivial work only."
  - source: docs/design/01-skill-anatomy.md#evidence-home
    hash: sha256:d4ad2626d2dc993f9879247429ce4a15a9dcee31c9b4b20da8178ffe8bac8dc9
    excerpt: "There is one home for a run's evidence. The sequencer writes every file below except the judge findings under `evidence/<agent>/`:"
  - source: docs/design/10-sequencer-and-contracts.md#4-per-skill-phase-registry
    hash: sha256:511733ee35ca74fd5a5c0b59f225d7d975788e7d43d939f44c23b7aa8460cff0
    excerpt: "| retro | document | `docs/reports/retro-<arg>.md` | 4 |"
  - source: docs/design/10-sequencer-and-contracts.md#5-worker-result
    hash: sha256:cee716ddb3ae9b6b4405037ede3bb7c6445e0e6c8ac28382344a655d31754dcd
    excerpt: "One schema, both providers, every skill. The worker's final message is exactly this object, with no Markdown fence and no surrounding prose."
  - source: docs/design/10-sequencer-and-contracts.md#3-status-vocabulary-and-gate-policy
    hash: sha256:36ffb340bd5d843cd945f7d17a590e335e491b11a60b08d4bf70e12a3a223620
    excerpt: "A document run carries the fixed map `{unresolvable_source: BLOCK}`, because it has no story to declare a wider one."
  - source: docs/design/10-sequencer-and-contracts.md#10-evidence-files
    hash: sha256:4eebadd862a3dfd90bc0afff8342a1b18a76b2a4fe1ec5bafa23cea390f48984
    excerpt: "| `docs/reports/<skill>-<run>-<phase>.md` | Markdown | sequencer at a passing transition | the human, `retro` `collect`, `review` |"
  - source: docs/design/10-sequencer-and-contracts.md#6-handoff-envelope
    hash: sha256:747b6340fc5c2348aad33ca5488012808670b3503b311d7b7d0f1204625afd4c
    excerpt: "| document run, promoted, no verdict or `verdict: pass` | `/status` |"
  - source: docs/design/11-artifact-registry.md#1-template-registry
    hash: sha256:09607ea79839ab215871d87e8221166e14eeb6ca26f8372e4ead4173f1d92907
    excerpt: "| `retro-report` | `.devforgeai/skills/retro/templates/retro-report.md` | 1 | `^LESS-[0-9]{3}$` | sprint, template, template_version, status, depends_on | Outcomes, Lessons, Proposed Amendments, Archive |"
  - source: docs/design/02-skill-roster.md#retro
    hash: sha256:f2a88c7bda36610205f8044bbc8314c9c65c0f72339ba2445ccb6eba3675e17e
    excerpt: "- Collects QA reports, review findings, and dev notes for the sprint."
  - source: docs/design/05-subagent-sets.md#sets-per-skill
    hash: sha256:9e12f3beb236a025c18d40e741c09ba675bd71d2d87f56e2b205c7556b944bf9
    excerpt: "| retro | report-collector, lesson-extractor, amendment-proposer, archiver |"
---

# Skill Specification: retro

A stranger with no conversation history must be able to build this skill from this document alone. Every question the generator would otherwise ask is answered below. The `depends_on` digests are computed under the hash rule in `01-skill-anatomy.md#context-bundle-format` and verified by `docs/design/specs/verify.py --only v3`; a source edit after this date makes V3 fail until the digest is recomputed.

## 0. Generator instructions

These instructions are addressed to the skill-generating agent (Anthropic's `skill-creator` skill, or DevForgeAI's `skill-generator`). They replace its interview.

### Cold-session prompt

Paste this into a fresh session from the repository root:

```
Use the skill-creator skill to build the skill specified in docs/design/specs/SKILL-SPEC-015-retro.md.
Follow its section 0 exactly. Output directory: ./out. Eval mode: quick.
```

### Rules for the generator

1. **Do not interview.** Sections 1-13 pre-answer every Capture Intent and Interview question (what it enables, when it triggers, output format, test cases, edge cases, input/output formats, example files, success criteria, dependencies). Treat this document as the conversation history you are told to harvest from.
2. **Test prompts are pre-approved.** Use section 10 verbatim as `evals/evals.json`. Do not ask whether they look right.
3. **Trigger queries are pre-approved.** Use section 4 verbatim as the trigger eval set. Do not ask for sign-off.
4. **No human review loop.** Do not wait for the user to review results. Proceed to the next stage on your own.
5. **Eval mode** is given in the prompt and is one of two values:
   - `skip`: write the skill only. Do not create `evals/`, do not run test prompts, do not optimize the description.
   - `quick`: write the skill and `evals/evals.json`. Build each eval's workspace from `fixtures/retro/` as section 10 describes, run each test prompt once with the skill (no baseline run), grade with the grader agent, write `grading.json`, and report pass/fail per expectation in your final message. Do not run the description-optimization loop. Run the eval executions and the grader as foreground Agent-tool subagents, never as background shell processes, and do not end your turn until every `grading.json` exists: a headless session terminates when the top-level turn ends and orphans anything still running.
   - Any other mode name is a spec defect. The deferred interactive mode is `12-post-mvp.md#pm-06`.
6. **Output location** is given in the prompt. Create `./out/retro/`. Do not write anywhere else except the `retro-workspace/` sibling that eval runs require.
7. **On ambiguity, stop before output.** If the spec is still `draft`, contains an unresolved authoring assumption, omits a section, contradicts itself, or leaves a decision this document does not make, do not guess and do not write candidate skill files. End with a list titled `SPEC GAPS` naming each section and question. The spec author fixes and approves the spec before re-running.
8. **Fidelity over creativity.** Use the description in section 3 verbatim. Use the worker contracts in section 7d verbatim as `agents/<role>.md` bodies, adding only the framing the grader agent in skill-creator uses (Role, Inputs, Process, Output). Do not add steps, tools, or behaviours the spec does not mention.
9. **Finish with the acceptance checks** in section 14 and include their output in your final message.

## 1. Identity

| Field | Value |
|-------|-------|
| name | `retro` (kebab-case, 5 chars, equals the directory name, no `claude`/`anthropic` prefix) |
| title | Sprint Retrospective and Amendment Proposal |
| purpose | Read one sprint's recorded evidence, extract the lessons it actually supports, and turn each lesson that needs a rule change into a ready-to-run amendment command, so the next sprint starts from evidence rather than memory. |
| category | devforgeai-phase |
| version | 1.0.0 (skill-package version written to `metadata.version`; not the DevForgeAI or Research Core version) |
| license | MIT (frontmatter `license: MIT`) |

## 2. Problem and requirements

**Without this skill:** a sprint ends and its evidence stays scattered. The qa verdicts are in `docs/reports/qa-STORY-NNN.md`, the review findings in `docs/reports/review-STORY-NNN.md`, the per-phase outcomes in `.devforgeai/work/<story>/<phase>-result.json`, and the rendered dev notes in `docs/reports/`. A human writes a retrospective from memory instead, so the recurring cause — the same criterion failing qa in three stories, or two rewinds from `green` to `red` in one story — is never named, and the rule that would prevent it is never written down. Two failure modes in `07-purpose-and-enforcement.md` section 2 apply directly: "declares done because a file exists or a checkbox is ticked", and "invents requirements or scope", which is what an unevidenced retrospective produces.

| ID | Kind | Requirement |
|----|------|-------------|
| R1 | explicit | Take a sprint id and collect every qa report, review report, dev note and phase result recorded for the stories that sprint lists. |
| R2 | explicit | Extract lessons, each one tied by path to the evidence row that supports it. |
| R3 | explicit | Propose amendments as exact `/amend` commands, one per lesson that needs a rule change, so a human can run them without rewriting anything. |
| R4 | explicit | Write `docs/reports/retro-<sprint>.md` against the `retro-report` template, whose sections are Outcomes, Lessons, Proposed Amendments and Archive. |
| R5 | implicit | A lesson without an evidence path is not written. The critic pattern in `01-skill-anatomy.md` exists because a persona reviewing its own output is the primary hallucination vector; here the substitute is the rule that every lesson row carries a file path an unrelated reader can open. |
| R6 | implicit | The primary window opens the run, dispatches, and prints the rendered handoff. It reads no report and writes nothing (`01-skill-anatomy.md#primary-window-contract`). |
| R7 | implicit | Every worker returns exactly one `devforgeai.worker-result/v1` receipt. The one producer writes its file inside the candidate root and names it in `claimed_paths`; the sequencer derives what actually changed from the checkpoint diff and refuses anything unclaimed (`10-sequencer-and-contracts.md` section 5). |
| R8 | discovered | Only the fourth phase writes inside the candidate root. `collect`, `lessons` and `amendments` declare `writes: evidence`, so their one write reaches `.devforgeai/work/<run>/evidence/<agent>/` and any change in the root's checkpoint diff refuses the result as `UNCLAIMED_CHANGE`; their findings file is named in `evidence_refs` and summarised in `issues` and `note`. |
| R9 | discovered | The run's fence is exactly `docs/reports/retro-<sprint>.md`. The sprint folder cannot be moved by any worker, so archiving is a recorded action, not a file operation; section 9 records the consequence. |
| R10 | discovered | `retro` invokes no other skill: `devforgeai phase start` refuses while a run is active, so the `/amend` edge is a handoff row and a report row. |

## 3. Description

```yaml
description: >
  Turn one finished DevForgeAI sprint into an evidence-backed retrospective. Use this skill
  whenever a sprint is done or a story run has closed and the user asks what went wrong,
  what to change, why qa keeps failing the same criterion, or says wrap up sprint-002, run
  the retro, post-mortem this sprint, or asks to archive a sprint. It collects the qa
  reports, review reports, dev notes and recorded phase results for the sprint's stories,
  extracts lessons that each cite the evidence file behind them, names each rule change
  as an exact amend command, and writes a retro report with an archive checklist. Do NOT
  use it to change a document or record a decision (use /amend), to plan the next sprint or
  re-slice stories (use /plan), to judge one story (use /qa or /review), or to compare
  documents against code (use /drift).
```

Character count: 825 / 1024. No `<` or `>` appears in the description, so the command forms are written without angle brackets.

## 4. Trigger set

```json
[
  {"query": "/retro sprint-002", "should_trigger": true},
  {"query": "sprint-001 is finished, what did we learn?", "should_trigger": true},
  {"query": "three stories failed qa on the same acceptance criterion this sprint, dig into why", "should_trigger": true},
  {"query": "run the post mortem for sprint-003 and tell me what rules we should change", "should_trigger": true},
  {"query": "all the stories in sprint-002 are done, wrap it up and archive it", "should_trigger": true},
  {"query": "before we plan the next sprint i want the lessons from the last one, with evidence not vibes", "should_trigger": true},
  {"query": "qa STORY-004 passed but it took four attempts, is that a pattern across sprint-001?", "should_trigger": true},
  {"query": "summarise how sprint-002 went from the review and qa reports in docs/reports", "should_trigger": true},
  {"query": "we keep rewinding from green to red. look at the last sprint and propose constitution changes", "should_trigger": true},
  {"query": "change the constitution so tdd is mandatory", "should_trigger": false},
  {"query": "plan sprint-003 from the remaining stories in the backlog", "should_trigger": false},
  {"query": "run the acceptance criteria for STORY-006 and tell me if it passes", "should_trigger": false},
  {"query": "review the diff on STORY-011 for security problems", "should_trigger": false},
  {"query": "does the code still match what architecture.md claims?", "should_trigger": false},
  {"query": "write the qa report for STORY-002, i tested it by hand", "should_trigger": false},
  {"query": "which requirements in the prd have no story?", "should_trigger": false},
  {"query": "STORY-009 is blocked on an unresolved assumption, ask me the questions", "should_trigger": false},
  {"query": "what does a retrospective usually cover? we've never run one", "should_trigger": false},
  {"query": "delete the old sprint folders, they're cluttering docs/plan", "should_trigger": false}
]
```

## 5. Use cases

### UC-1: Sprint with a repeated qa failure
- **User says:** "/retro sprint-002"
- **Steps:** 1. The adapter calls `devforgeai phase start retro sprint-002`. 2. `report_collector` resolves `docs/plan/*/sprints/sprint-002.md`, reads its `stories` frontmatter list, and returns one evidence row per story naming its qa report, review report, rendered dev notes and phase result files. 3. `lesson_extractor` finds the same acceptance criterion failing qa in STORY-004 and STORY-007 and returns one lesson row citing both report paths. 4. `amendment_proposer` turns that lesson into `/amend constitution "require an explicit error-path criterion in every story"`. 5. `archiver` writes `docs/reports/retro-sprint-002.md` inside the candidate root with Outcomes, Lessons, Proposed Amendments and Archive filled.
- **Result:** one retro report, four result files under `.devforgeai/work/retro-sprint-002/`, and a handoff whose next step is `/status` with the named amendment printed as an open item.

### UC-2: Clean sprint, nothing to amend
- **User says:** "sprint-001 is finished, what did we learn?"
- **Steps:** 1. The adapter resolves the sprint id from the user's words and calls `devforgeai phase start retro sprint-001`. 2. `report_collector` returns the evidence rows. 3. `lesson_extractor` returns lessons whose kind is `observation` only. 4. `amendment_proposer` returns no proposal rows. 5. `archiver` writes the report with an empty Proposed Amendments table and an Archive section naming the sprint file and the exact move a human performs.
- **Result:** a retro report that records the sprint as clean; the handoff's next step is `/status`, and `/plan <slug> --next-sprint` is printed under alternatives.

### UC-3: Sprint id resolves to two files that carry the same slug
- **User says:** "/retro sprint-002"
- **Steps:** 1. The run opens; the document gate checks the fence, not the sprint file. 2. `report_collector` finds `docs/plan/shop/sprints/sprint-002.md` and `docs/plan/billing/sprints/sprint-002.md`. 3. The tie-break is the sprint frontmatter `slug` against `state.yaml`'s `slug`; both files record `slug: shop`, so it does not resolve. 4. The worker writes nothing and returns `status: needs_user` with an empty `claimed_paths` and one issue row naming both paths.
- **Result:** the run closes on the first ask with `REQUIRE_HUMAN`, nothing is written, and the handoff names the two files whose frontmatter has to be corrected on disk before `/retro sprint-002` is run again.

## 6. Inputs and outputs

### Inputs
| Input | Format | Example file | Required |
|-------|--------|--------------|----------|
| sprint id | the single positional argument; matches `^sprint-[0-9]{3}$` | | yes |
| sprint file | markdown, `plan`'s `sprint` template v1; frontmatter `stories` is the story list and `slug` breaks a tie between files sharing an id | `fixtures/retro/docs/plan/shop/sprints/sprint-002.md` | yes |
| qa reports | markdown, `qa`'s `qa-report` template | `fixtures/retro/docs/reports/qa-STORY-004.md` | no |
| review reports | markdown, `review`'s `review-report` template | `fixtures/retro/docs/reports/review-STORY-004.md` | no |
| dev notes | markdown, `dev`'s `dev-notes` template, as the rendered view | `fixtures/retro/docs/reports/dev-STORY-004-green.md` | no |
| phase results | json, `devforgeai.worker-result/v1` plus the fields the sequencer adds | `fixtures/retro/.devforgeai/work/STORY-004/green-result.json` | no |
| provenance log | jsonl, one line per write operation, each with `at`, `kind` and `session_id` | `fixtures/retro/.devforgeai/provenance/log.jsonl` | no; without it the Outcomes table's attempt column is empty |
| ADRs | markdown, `architect`'s `adr` template | `fixtures/retro/.devforgeai/provenance/adr/0001-choose-sqlite.md` | no |
| `.devforgeai/state.yaml` | yaml | `fixtures/retro/.devforgeai/state.yaml` | yes; `devforgeai phase start` refuses without it |

A story run's evidence directory is named for the story, so `STORY-004`'s results are under `.devforgeai/work/STORY-004/`. `10-sequencer-and-contracts.md` section 10 names `retro`'s `collect` phase as a consumer of those files and of `docs/reports/<skill>-<run>-<phase>.md`.

### Outputs
| Output | Format | Location | Template |
|--------|--------|----------|----------|
| retro report | markdown | `docs/reports/retro-<sprint>.md` | `retro-report` (`assets/retro-report.md`) |
| phase results | json | `.devforgeai/work/retro-<sprint>/<phase>-result.json` | none; the sequencer writes it |
| phase reports | markdown | `.devforgeai/work/retro-<sprint>/<phase>-report.md` | none; the sequencer renders it |
| rendered views | markdown | `docs/reports/retro-retro-<sprint>-<phase>.md` | none; the sequencer writes it at each passing transition |
| handoff | json plus its printed block | `.devforgeai/work/retro-<sprint>/handoff.json` | `handoff` |

`docs/reports/retro-<sprint>.md` is the only path any retro worker writes, and it is written inside the candidate root.

### Output template

`docs/reports/retro-<sprint>.md`, filled from `assets/retro-report.md`:

```
---
sprint: sprint-002
template: retro-report
template_version: 1
status: complete
depends_on:
  - source: docs/plan/shop/sprints/sprint-002.md
    hash: sha256:<64 hex>
    excerpt: |
      stories: [STORY-004, STORY-007]
  - source: docs/reports/qa-STORY-004.md
    hash: sha256:<64 hex>
    excerpt: |
      verdict: fail
---

# Retro: sprint-002

## Outcomes
| Story | QA verdict | Review verdict | Phase attempts | Evidence |
|---|---|---|---|---|
| STORY-004 | fail then pass | pass | red 1, green 3 | docs/reports/qa-STORY-004.md; .devforgeai/provenance/log.jsonl |

## Lessons
| ID | Kind | Lesson | Evidence |
|---|---|---|---|
| LESS-001 | recurring-defect | Error-path behaviour is not encoded as a criterion, so qa fails it after dev is done | docs/reports/qa-STORY-004.md; docs/reports/qa-STORY-007.md |

## Proposed Amendments
| ID | Document | Command | Rationale |
|---|---|---|---|
| LESS-001 | constitution | /amend constitution "require an explicit error-path criterion in every story" | two qa failures in one sprint on the same missing criterion |

## Archive
| Item | Current path | Action | Owner |
|---|---|---|---|
| sprint file | docs/plan/shop/sprints/sprint-002.md | set status to archived when the next sprint opens | plan |
| story files | docs/plan/shop/stories/STORY-004.md, STORY-007.md | leave in place; retro performs no move | human |
```

`id_pattern` for this template is `^LESS-[0-9]{3}$`; the Lessons table mints the ids and the Proposed Amendments table reuses them, so a proposal always points back at its lesson.

### Return envelope (DevForgeAI-anatomy skills only)

One schema, both providers: `devforgeai.worker-result/v1`, normative in `schemas/devforgeai/v1/worker-result.schema.json`. Three of the four phases are judges: they write only their findings file under `.devforgeai/work/<run>/evidence/<agent>/` — run-scoped scratch, gitignored, outside the candidate root and never promoted — name it in `evidence_refs`, and claim nothing. `archive` is a producer: it writes the report inside the candidate root with Edit and Write (Codex: `apply_patch`) and names it. At `devforgeai ingest-result` the sequencer derives `changed[{path, blob_sha256, kind}]` from the candidate root's checkpoint diff, refuses the result when `changed` is not a subset of `claimed_paths` (`UNCLAIMED_CHANGE`) or when any changed path is outside the fence, runs the transition oracle inside the root, writes `<phase>-result.json` with `changed` and the checkpoint ref, creates the next checkpoint and releases the lease.

```yaml
schema: devforgeai.worker-result/v1
run: "retro-sprint-002"
skill: "retro"
phase: "collect"
agent: "report_collector"
status: pass | fail | needs_user | could_not_run
reason_code: runner_missing | timeout | network | hook_fault   # required only when status is could_not_run
candidate:
  id: "retro-sprint-002"
  input_checkpoint: "base"
claimed_paths: []          # empty for collect, lessons and amendments, and for any non-pass status
evidence_refs: []          # at most 16 paths, root-relative or under .devforgeai/work/<run>/
note: "Two stories, four reports, six phase results."
issues: [{id, kind, text}] # at most 10
next: ""                   # omitted: no retro phase declares rewind_to
```

Unknown keys are refused. `issues[]` is the bounded summary a reader sees in the handoff; a judge's full row set lives in its findings file, which the next phase and `archiver` read.

`gate_policy` (`BLOCK | REQUIRE_HUMAN | WARN | OFF`) is a defect-to-action map declared in the consumed artifact, never a status returned here. A document run carries the fixed map `{unresolvable_source: BLOCK}`.

## 7. Procedure

### 7a. Steps

The body of `SKILL.md`. The primary window does exactly this and nothing else.

1. Parse the single argument as the sprint id. When the user names a sprint in prose, resolve it to the `sprint-NNN` form before calling anything — why: the sequencer substitutes that string into the fence pattern, so a wrong form fences the wrong file.
2. Run `devforgeai phase start retro <sprint>`. Print stderr verbatim and stop on exit 1 or 2 — why: the gate is the only thing that decides a run may open.
3. Read the active phase from that output or from `devforgeai status`, and load `references/<phase>.md` — why: each reference file holds one phase's guidance, so the primary window never carries four phases of detail.
4. Dispatch that phase's worker through the target's native worker mechanism, passing only the run id, the skill name, the phase name and the file paths the reference file names. Do not paste report content into the prompt — why: the reports are the bulk of this skill's input and the primary window persists for the whole run.
5. Wait for the worker to return. The `SubagentStop` hook has already handed its envelope to `devforgeai ingest-result`, which validated it, applied any files, ran the oracle and advanced, retried or blocked.
6. Run `devforgeai status`. If a new phase is active, go to step 3. If the run is finished or blocked, print the handoff block the sequencer rendered and stop; a blocked run's block already names the command that resumes it.
7. When the block reports the run `ready_to_promote` and the user asks for the promotion, call `devforgeai promote <run>` and print the second block the promotion rendered — why: promotion is never automatic, it is what moves `docs/reports/retro-<sprint>.md` from the candidate root into the canonical checkout under the lock, and a `REQUIRE_HUMAN` block is the only state in which the model may ask for it.
8. If the user abandons the run, call `devforgeai phase fail --reason <text>` — why: that is the only way a `BLOCK` handoff and a cleared enforcement block get written.

### 7b. Sub-phases and workers

Gate, Record, Slice and Handoff dispatch no LLM: they are `devforgeai` sequencer operations. Slice runs inside `devforgeai phase start`, which resolves the incoming artifact's already-hashed context bundle and writes `.devforgeai/work/<run>/context.json`, whose path every worker of the run is handed (open item OI-1, section 9).

| # | Sub-phase | Registry phase | Performed by | Isolation |
|---|-----------|----------------|--------------|-----------|
| 0 | Gate | — | sequencer: `devforgeai phase start retro <sprint>` | n/a |
| 1 | Slice | — | sequencer: `devforgeai phase start` writes `.devforgeai/work/<run>/context.json` | n/a |
| 2 | Work | `collect` | worker: `report_collector` | required |
| 3 | Work | `lessons` | worker: `lesson_extractor` | required |
| 4 | Work | `amendments` | worker: `amendment_proposer` | required |
| 5 | Write | `archive` | worker: `archiver` | required |
| 6 | Record | — | sequencer: `devforgeai ingest-result`, then `devforgeai phase next` | n/a |
| 7 | Handoff | — | sequencer: `devforgeai phase next` marks the run `ready_to_promote` and writes the `REQUIRE_HUMAN` block whose only forward step is `devforgeai promote <run>`; `SKILL.md` runs that command only after the user confirms in the session, and the promotion writes the run's second handoff block | n/a |

`retro` has no Review sub-phase: the registry gives it four phases and none of them is a critic. `lesson_extractor` and `amendment_proposer` are deliberately separate workers so the worker that names a rule change is not the worker that decided the lesson was real.

Every phase of one run works inside the same candidate root — `.devforgeai/work/<run>/wt`, created by `devforgeai phase start` and named to each worker as `candidate.root` in the status block the primary window pastes into the dispatch prompt alongside `run`, `phase`, `fence` and `granted_keys`. The first three phases are judges and write nothing in the root; their findings files go to `.devforgeai/work/<run>/evidence/<agent>/`, which is outside it. `archive` writes one file in the root. The sequencer checkpoints the root at each transition, so the phases build linearly with no merge between them, and the one producer holds the run's lease from dispatch to `devforgeai ingest-result`. Promotion is never automatic and is no part of Handoff: the last passing `devforgeai phase next` marks the run `ready_to_promote` and writes a `REQUIRE_HUMAN` handoff whose only forward step is `devforgeai promote <run>`, and `SKILL.md` runs that command only after the user confirms in the session. That command, not the transition, is what merges the candidate root into the canonical checkout under `.devforgeai/lock`, and it is what refuses with `STALE_BASE` when canonical HEAD has moved past the run's recorded `base_ref`, with `DIRTY_TARGET` when the canonical report path is dirty, and with `MERGE_CONFLICT` when a rebase inside the root conflicted; a refused promotion leaves the run `ready_to_promote` with its candidate root intact for a retry.

### 7c. Evidence and gate table

`<run>` is `retro-<sprint>`. Attempt budget is 2 for every phase; there is no `rewind_to`, so no retro result may carry `next`.

| phase | worker | deterministic gate check | gate_policy | evidence file | transition oracle |
|---|---|---|---|---|---|
| `collect` | `report_collector` | run gate: skill known, no run already active, no active or `ready_to_promote` run whose fence overlaps this one (`FENCE_OVERLAP`), and the fence entry `docs/reports/retro-<sprint>.md` is repository-relative, free of `..`, and not sequencer-owned; `candidate open` creates the root and pins `base_ref`. At `ingest-result`: `writes: evidence`, so the checkpoint diff of the root is empty: the `PreToolUse` check admits this worker's `Write` only under `.devforgeai/work/<run>/evidence/<agent>/`, which lies outside the root, and a non-empty root diff is `UNCLAIMED_CHANGE`. `issues` at most 10 rows, `evidence_refs` at most 16 paths, `note` at most 16384 bytes | document run's fixed map `{unresolvable_source: BLOCK}`; an oversize or malformed envelope is a protocol refusal that does not consume an attempt | `.devforgeai/work/retro-<sprint>/collect-result.json`, `collect-report.md` | `report_only`: no file outside the fence changed since the gate snapshot and the whole-tree package and import policy holds |
| `lessons` | `lesson_extractor` | as `collect`: `writes: evidence`, an empty root checkpoint diff, and the receipt bounds enforced before anything is recorded | as above | `.devforgeai/work/retro-<sprint>/lessons-result.json`, `lessons-report.md` | `report_only`: as `collect` |
| `amendments` | `amendment_proposer` | as `collect`; the phase grants no stack command key, so a `devforgeai run` call from this worker is refused for a missing hook marker | as above | `.devforgeai/work/retro-<sprint>/amendments-result.json`, `amendments-report.md` | `report_only`: as `collect` |
| `archive` | `archiver` | at `ingest-result`: `changed` derived from the checkpoint diff is exactly one path, `docs/reports/retro-<sprint>.md`, it is a subset of `claimed_paths` (`UNCLAIMED_CHANGE` otherwise), it canonicalises inside the candidate root, it equals the fence entry, it is allowed by `writes: docs`, and it is at most 1 MiB; then the whole-tree package and import rescan | as above; a change under `docs/plan/**` is `write_fence_violation`, which refuses the result with no `gate_policy` consulted | `.devforgeai/work/retro-<sprint>/archive-result.json`, `archive-report.md` | `document`: `docs/reports/retro-<sprint>.md` exists on disk in the root. On pass this is the last phase: the run becomes `ready_to_promote` and the handoff's `next` is `devforgeai promote <run>`; `/status` is the `next` of the second handoff, written when that promotion succeeds. A promotion refused with `STALE_BASE` or `DIRTY_TARGET` leaves the run `ready_to_promote` for `devforgeai promote <run>` |

Two limits from `10-sequencer-and-contracts.md` section 3.2 apply to every row: every `devforgeai phase start` defect is a refusal whatever a declared policy value says, and at transition time only `test_runner_missing` changes behaviour. `retro` brokers no stack command key, so that class reaches it only through a synthesised `could_not_run`.

### 7d. Worker contracts

Each block below is a compilable subagent definition and the body of `agents/<role>.md`. `name` is the canonical registry worker name, because the stop event's `agent_type` is compared against it. `description` is the sentence the primary window matches when it decides to dispatch. `writes` is `evidence` for a judge — its one write goes to `.devforgeai/work/<run>/evidence/<agent>/` and never into the candidate root — and `candidate` for a producer, following the registry's `writes` column: three phases declare `none` there and one declares `docs`, so three judges and one producer. `compiled_to` names the two provider-native files `skill-generator` emits from the block; each body follows `templates/agent-md.md` in four parts — job, inputs, rules, receipt — and the producer's job sentence leads with what it writes.

```yaml
name: report_collector
skill: retro
description: Dispatch this worker first in a retro run to resolve the sprint's story list and gather every recorded report and result path for it, before any lesson is drawn.
writes: evidence
tools: [Read, Grep, Glob, Write, Bash(devforgeai status)]
model: inherit
skills: []
responsibility: Resolve the sprint's story list and return one evidence row per story naming every recorded report and result file for it.
inputs:
  - docs/plan/*/sprints/<sprint>.md, frontmatter stories list and slug
  - .devforgeai/state.yaml, the slug key only, to break a tie between sprint files sharing an id
  - docs/reports/qa-STORY-NNN.md and docs/reports/review-STORY-NNN.md for each listed story
  - docs/reports/dev-STORY-NNN-<phase>.md and docs/reports/<skill>-<run>-<phase>.md rendered views
  - .devforgeai/work/STORY-NNN/<phase>-result.json for each listed story
  - .devforgeai/provenance/log.jsonl, filtered to the run ids of the listed stories, for the transition.pass, transition.fail and rewind lines that carry the attempt history
outputs:
  - .devforgeai/work/<run>/evidence/report_collector/stories.json, one row per story with its sprint path, qa report, review report, rendered dev notes, result files, recorded verdicts and attempt count
  - issues[]: at most 10 rows, one per story whose sprint entry has no report or result file at all
  - note: the story count, the report count and the result count the file carries
  - evidence_refs[]: the stories file above, then the sprint file and the report and result paths the rows name
must_not:
  - write or claim any path inside the candidate root; this phase's one write is its findings file under .devforgeai/work/<run>/evidence/report_collector/
  - resolve a sprint id to more than one file: when the glob matches several, keep the one whose frontmatter slug equals state.yaml's slug, and return needs_user naming every remaining path only when that still leaves more than one
  - infer a verdict a report does not state
  - summarise a report's prose; record its path, its recorded verdict and its counted rows
isolation: required
returns: devforgeai.worker-result/v1
compiled_to:
  - .claude/agents/retro-report_collector.md
  - .codex/agents/retro-report_collector.toml
body: job, inputs, rules, receipt
```

```yaml
name: lesson_extractor
skill: retro
description: Dispatch this worker after collect to turn the gathered evidence into lessons, each tied to the files that support it, when a reader wants to know what the sprint taught.
writes: evidence
tools: [Read, Grep, Glob, Write, Bash(devforgeai status)]
model: inherit
skills: []
responsibility: Turn the collected evidence into lessons, each tied to the files that support it.
inputs:
  - .devforgeai/work/retro-<sprint>/collect-result.json
  - the report and result paths that file names, read directly for the rows a lesson cites
outputs:
  - .devforgeai/work/<run>/evidence/lesson_extractor/lessons.json, every lesson with an id matching LESS-NNN, a kind of recurring-defect, process, estimate or observation, and the paths that support it
  - issues[]: at most 10 rows drawn from that file, the lessons a reader should see first
  - note: the count of lessons by kind, and which of them rest on a single story and are therefore not yet a pattern
  - evidence_refs[]: the lessons file above, then the report and result paths every lesson cites
must_not:
  - write or claim any path inside the candidate root; this phase's one write is its findings file under .devforgeai/work/<run>/evidence/lesson_extractor/
  - record a lesson with no supporting path
  - name a document change; that is the next phase's job and a separate worker
  - read a story's source code or diff; this phase works from recorded verdicts
isolation: required
returns: devforgeai.worker-result/v1
compiled_to:
  - .claude/agents/retro-lesson_extractor.md
  - .codex/agents/retro-lesson_extractor.toml
body: job, inputs, rules, receipt
```

```yaml
name: amendment_proposer
skill: retro
description: Dispatch this worker after lessons to turn each lesson that needs a rule change into one exact amend command against a named architecture document.
writes: evidence
tools: [Read, Grep, Glob, Write, Bash(devforgeai status)]
model: inherit
skills: []
responsibility: Turn each lesson that needs a rule change into one exact amend command against a named architecture document.
inputs:
  - .devforgeai/work/retro-<sprint>/lessons-result.json
  - docs/architecture/constitution.md, sourcetree.md, techstack.md, architecture.md, headings only, to name the document a change belongs to
  - .devforgeai/provenance/adr/*.md, to avoid proposing a change a live decision already made
outputs:
  - .devforgeai/work/<run>/evidence/amendment_proposer/proposals.json, every proposal with its lesson id, document basename, single-line amend command and rationale
  - issues[]: at most 10 rows drawn from that file, so the handoff prints them as open items
  - note: the count of proposals and the documents they name
  - evidence_refs[]: the proposals file above, then the lessons result and the architecture documents whose headings were read
must_not:
  - write or claim any path inside the candidate root; this phase's one write is its findings file under .devforgeai/work/<run>/evidence/amendment_proposer/
  - name a change to a document that does not exist under docs/architecture/
  - name more than one command per lesson
  - apply a change or write an ADR; amend owns both
isolation: required
returns: devforgeai.worker-result/v1
compiled_to:
  - .claude/agents/retro-amendment_proposer.md
  - .codex/agents/retro-amendment_proposer.toml
body: job, inputs, rules, receipt
```

```yaml
name: archiver
skill: retro
description: Dispatch this worker last in a retro run to write the retro report and record the archival actions the run cannot perform itself.
writes: candidate
tools: [Read, Grep, Glob, Edit, Write, Bash(devforgeai status)]
model: inherit
skills: []
responsibility: Write the retro report inside the candidate root and record the archival actions the run cannot perform itself.
inputs:
  - .devforgeai/work/retro-<sprint>/collect-result.json, lessons-result.json and amendments-result.json, and the three findings files their evidence_refs name under .devforgeai/work/<run>/evidence/
  - assets/retro-report.md, the retro-report skeleton
outputs:
  - docs/reports/retro-<sprint>.md, written under the candidate root with Edit or Write and named in claimed_paths, with Outcomes, Lessons, Proposed Amendments and Archive filled and depends_on listing the sprint file and every report it cites
  - evidence_refs[]: the three preceding result paths and the three findings files the rows were rendered from
must_not:
  - write or claim any path under docs/plan/, which plan owns and which is outside this run's fence
  - add a lesson, an outcome row or a proposal that the three findings files do not carry
  - describe the sprint folder as moved; the Archive table records the action and its owner
  - write or claim any path other than docs/reports/retro-<sprint>.md
isolation: required
returns: devforgeai.worker-result/v1
compiled_to:
  - .claude/agents/retro-archiver.md
  - .codex/agents/retro-archiver.toml
body: job, inputs, rules, receipt
```

The three judges hold `Read`, `Grep`, `Glob`, `Write` and `Bash(devforgeai status)`, with `Write` admitted only under `.devforgeai/work/<run>/evidence/<agent>/`, so each can record a row set larger than the receipt without being able to touch the reports it reads. `archiver` is the one producer and holds `Edit` and `Write` inside the candidate root, scoped by the `PreToolUse` check and compiled to `apply_patch` on the Codex target. No `retro` phase grants a stack key, so no worker carries `Bash(devforgeai run *)`, and no worker holds a git write, a package manager, a network tool or a raw stack command. `isolation` above is the framework's `required | preferred` declaration, not Claude's subagent `isolation` key, which the framework never sets. `hooks`, `memory`, `background` and `permissionMode` are Claude-only keys this skill leaves unset.

Each worker's envelope must carry `run`, `skill` and `phase` equal to the enforcement block. The primary window forwards those three ids in the dispatch line; a worker may also read them from `devforgeai status`, which is the one sequencer operation a phase worker may call.

### 7e. Handoff outcomes

`handoff.outcomes` as the skill declares it. The sequencer selects the row by envelope status and fills the placeholders from state, so the rows are keyed on status, not on narrative outcome. `{sprint}` is the run argument and `{slug}` is `state.yaml`'s project slug.

| Outcome | Selected when | Next steps |
|---------|---------------|------------|
| `ready_to_promote` | the last phase passed; the run's work is complete and unpromoted | 1. `devforgeai promote {run}` — the first of the run's two handoff blocks; `SKILL.md` runs the command only after the user confirms in the session, and the promotion writes the second block, whose row is one of the two below. |
| `pass` | all four phases passed and `amendments-result.json` carries proposals | 1. `/status`. Open items carry one `/amend {doc} "{change}"` per `issues[]` row, printed before the next step; `docs/reports/retro-{sprint}.md` holds the full Proposed Amendments table when it exceeds the ten-row cap. Also possible: `/plan {slug} --next-sprint`. |
| `pass` | all four phases passed with no proposals | 1. `/status`. Also possible: `/plan {slug} --next-sprint`. The report's Proposed Amendments table is empty. |
| `REQUIRE_HUMAN` | any phase returned `needs_user`, such as a sprint id that two files claim under one slug; the run blocks at that phase on the first ask with no retry — status stays `active`, the lease is released, `run.yaml#blocked_at` names the phase and the candidate root survives | 1. `/retro {sprint}`, which resumes the blocked run at `blocked_at` with attempts reset. The answer is a change on disk — corrected sprint frontmatter, or the missing report the question named — not a reply in the session. |
| `REQUIRE_HUMAN` | a phase returned `fail`, or its oracle reported problems, at the attempt limit of 2; the run blocks and keeps its root | 1. fix the cause `repair_route` names — the phase and its report file — then `/retro {sprint}`, which resumes the blocked run at `blocked_at` with attempts reset. Also possible: `devforgeai phase fail --reason <text>` to abandon the root, then `/status`. |
| `REQUIRE_HUMAN` | `could_not_run`; also the synthesised result when a stop event carries no worker identity | 1. repair the dependency named by `reason_code`, then `/retro {sprint}`. |
| `BLOCK` | the primary window called `devforgeai phase fail --reason` | 1. `/retro {sprint} --fix`, which the sequencer renders from its `BLOCK` default and which opens a fresh run from phase 1. |

`retro` invokes no other skill. Its edges to `amend` and `plan` are handoff rows and report rows: the finishing run's `next` names the command and a human or a fresh session runs it (open item OI-7, section 9).

## 8. Bundled resources

### Layout (fixed)

```
retro/SKILL.md              # <=500 lines: identity, phase list, dispatch loop, handoff table
  references/collect.md
  references/lessons.md
  references/amendments.md
  references/archive.md
  references/envelope.md
  agents/report_collector.md
  agents/lesson_extractor.md
  agents/amendment_proposer.md
  agents/archiver.md
  scripts/sprint_evidence.py
  assets/retro-report.md
```

Link depth: `SKILL.md` links to `references/`, `agents/`, `scripts/` and `assets/`; an `agents/*.md` links to `references/*.md`; nothing links further.

### scripts/
| File | Purpose | Invocation | Exit codes |
|------|---------|------------|------------|
| `sprint_evidence.py` | Print, as JSON on stdout, every evidence path that exists for a sprint: the resolved sprint file, and per story its qa report, review report, rendered dev notes and `.devforgeai/work/<story>/*-result.json`. A human runs it before or after a run to check what the collector had to work with; nothing in a run may execute it, because no retro phase grants a stack key and the primary window's grammar is the model-callable operations only. | `python scripts/sprint_evidence.py --sprint sprint-002 --root .` | 0 printed, 1 no sprint file or more than one match, 2 usage |

The script prints JSON to stdout and every diagnostic to stderr, never prompts, and documents `--help`.

### references/
| File | Content | Load when |
|------|---------|-----------|
| `collect.md` | how a sprint id resolves to one file under `docs/plan/*/sprints/` and how the sprint frontmatter `slug` breaks a tie, which frontmatter key holds the story list, the five evidence families and their path shapes, why attempts and rewinds are counted from `provenance/log.jsonl` rather than from a result file, and what a row records when a family is missing | before dispatching `report_collector` |
| `lessons.md` | the four lesson kinds, the rule that a lesson without an evidence path is not written, how attempt counts and rewinds are read out of a result file, and how to tell a one-story incident from a pattern | before dispatching `lesson_extractor` |
| `amendments.md` | how a lesson maps to one architecture document, the exact single-line `/amend` form, and the rule that a live ADR already covering the change makes the proposal unnecessary | before dispatching `amendment_proposer` |
| `archive.md` | the `retro-report` template's four sections, the shared `LESS-NNN` numbering, how `depends_on` is filled from the collected paths, and what the Archive table may record given the fence | before dispatching `archiver` |
| `envelope.md` | the `devforgeai.worker-result/v1` schema, its field bounds, and the rule that the final message is exactly one such object with no Markdown fence | every dispatch |

### assets/
| File | Used for |
|------|----------|
| `retro-report.md` | seeds `docs/reports/retro-<sprint>.md`; carries the `retro-report` template header (`template_version: 1`, `id_pattern` `^LESS-[0-9]{3}$`, required sections Outcomes, Lessons, Proposed Amendments, Archive) |

### agents/
| File | Worker (from section 7d) | writes | tools | compiled to |
|------|-------------------------|--------|-------|-------------|
| `report_collector.md` | `report_collector` | evidence | Read, Grep, Glob, Write, Bash(devforgeai status) | `.claude/agents/retro-report_collector.md`, `.codex/agents/retro-report_collector.toml` |
| `lesson_extractor.md` | `lesson_extractor` | evidence | Read, Grep, Glob, Write, Bash(devforgeai status) | `.claude/agents/retro-lesson_extractor.md`, `.codex/agents/retro-lesson_extractor.toml` |
| `amendment_proposer.md` | `amendment_proposer` | evidence | Read, Grep, Glob, Write, Bash(devforgeai status) | `.claude/agents/retro-amendment_proposer.md`, `.codex/agents/retro-amendment_proposer.toml` |
| `archiver.md` | `archiver` | candidate | Read, Grep, Glob, Edit, Write, Bash(devforgeai status) | `.claude/agents/retro-archiver.md`, `.codex/agents/retro-archiver.toml` |

## 9. Gotchas and edge cases

| Situation | What goes wrong | What to do instead |
|-----------|-----------------|--------------------|
| The phase is called `archive` but the fence is one report file | `docs/plan/<slug>/sprints/` is outside the run's fence, so no worker may move, rename or delete a sprint folder; a proposal that tried would be refused as a fence violation, and the phase would then fail its `document` oracle. | The `archive` phase writes `docs/reports/retro-<sprint>.md`, and its Archive table records each archival action with the owner who performs it. The report is the archive record, not a file operation. |
| OI-1: which component performs Slice | A spec promising a slice worker would describe an agent file with no registry phase to run it. | Slice is a sequencer step inside `devforgeai phase start`: it writes `.devforgeai/work/<run>/context.json`, whose path every worker of the run is handed. No framework worker performs it and this package ships no agent file for it. |
| OI-2 and section 3.4: which digests a gate re-resolves | A retro report's `depends_on` entries look like they are checked when the report is read. | The story gate re-resolves `provenance[]` and `context[]` on a story run. Nothing re-resolves a report's `depends_on` today, so the digests `archiver` records are evidence for a human and for `/analyze`, not a gate the framework runs on this artifact. |
| OI-3: worker tools | A generator that gives every worker one list either leaves `archiver` with no way to write the report, or gives a judge a write tool over the reports it was asked to read. | Tools are per role. The three judges hold `Read`, `Grep`, `Glob`, `Write` and `Bash(devforgeai status)`, with `Write` admitted only under `.devforgeai/work/<run>/evidence/<agent>/`. `archiver` holds `Edit` and `Write` inside the candidate root, scoped by the `PreToolUse` check. No retro phase grants a stack command key, so no worker carries `Bash(devforgeai run *)`. |
| OI-4: a worker returns `fail` with no rewind target | Nothing in section 5.4 lists that row, so it looks like a silent pass. | `examples/hooks/devforgeai.py:1017-1018` inserts the reported failure as a transition problem, so the phase retries to its limit of 2 and then blocks `REQUIRE_HUMAN`. No retro phase declares `rewind_to`, so a retro result carrying `next` is refused at `ingest-result`. |
| OI-5: `--fix` and `--retry` look like resume flags | An earlier draft closed the run on `needs_user` and at an exhausted attempt budget, so no flag could resume anything. | Settled: `10-sequencer-and-contracts.md` sections 2 and 3.1 leave such a run `active` with its lease released, its candidate root kept and `run.yaml#blocked_at` naming the phase, and `devforgeai phase start retro <sprint>` — same skill, same argument — resumes it there with attempts reset. Resuming is the command, not a flag: `/retro {sprint}` does it. With no blocked run to resume, the same call opens a fresh run from phase 1; every flag only changes what the workers read. |
| OI-7: `02-skill-roster.md` says retro calls amend | `devforgeai phase start` refuses while a run is active, so a nested run is impossible. | The amend edge is a handoff row and a Proposed Amendments row. A human runs each command; the retro run never does. |
| OI-8: worker naming | `05-subagent-sets.md` writes `report-collector` and `lesson-extractor`; the registry writes `report_collector` and `lesson_extractor`. | The registry name is canonical and is what `agent_type` is compared against. Use it in section 7, in the `agents/` filenames and in the evidence table. |
| The document gate checks the fence, not the sprint | `devforgeai phase start retro sprint-999` opens a run for a sprint that does not exist. | `report_collector` returns `fail` with an issue naming the glob it searched; two attempts later the run blocks with `REQUIRE_HUMAN`. Nothing is written, because a non-`pass` status may carry no files. |
| The same sprint id exists under two project slugs | A collector that picked one silently would produce a retrospective for the wrong project. | The `sprint` template's `required_frontmatter` includes `slug` (`11-artifact-registry.md` section 1), so `report_collector` keeps the file whose `slug` equals `state.yaml`'s. `needs_user` is returned only when that leaves more than one, and it never retries: it is recorded, written into a `REQUIRE_HUMAN` handoff, and the run closes on the first ask. The repair is a frontmatter correction on disk. |
| The run id is `retro-<sprint>` | Re-running the retro for the same sprint reuses the run directory, so the second run overwrites `.devforgeai/work/retro-<sprint>/*-result.json`. | The durable record is `docs/reports/retro-<sprint>.md` plus one `provenance/log.jsonl` line per run. Read those when reconstructing history. |
| Where a judge's rows live | The receipt has no bounded `evidence` object, and a long sprint has more collected rows than `issues[]` can carry | Each judge writes its full row set to `.devforgeai/work/<run>/evidence/<agent>/` and names that file in `evidence_refs`; `issues[]` is the bounded summary the handoff prints, and `archiver` renders the report from the findings files. |
| The attempt count is not in a result file | `<phase>-result.json` holds the receipt plus `agent`, `agent_id`, `session_id`, `captured_at`, the derived `changed` list and the checkpoint ref, and the judge's own findings file sits beside it under `evidence/<agent>/`; `enforcement.attempts` is cleared when the run closes, so a collector reading only those files would have to invent the number. | Attempts and rewinds are counted from `provenance/log.jsonl`, whose `transition.pass`, `transition.fail` and `rewind` lines carry them. `10-sequencer-and-contracts.md` section 10 already names `retro` as a consumer of that file. |
| A story in the sprint never ran | There is no qa report, no review report and no result directory, so an extractor could read the absence as a passing story. | `report_collector` records the row with empty verdicts and adds an `issues[]` row; `lesson_extractor` may cite that absence as a `process` lesson, and `archiver` shows it in Outcomes with blank verdict cells. |
| A qa report exists for a story the sprint file does not list | The report belongs to another sprint or to an out-of-band run. | The sprint file's `stories` list is the only membership rule. A report outside it is not collected, and no lesson may cite it. |
| Which worker may write, and where | A generator that treated the four workers alike would let a judge edit the qa and review reports it was asked to read, and the retro would then describe a sprint nobody ran | Roles follow the registry's `writes` column: `collect`, `lessons` and `amendments` compile to judges declaring `writes: evidence`, whose one write reaches `.devforgeai/work/<run>/evidence/<agent>/` and nothing else; `archive` declares `docs` and compiles to a producer holding `Edit` and `Write`. Its one write lands inside the candidate root and is named in `claimed_paths`; the sequencer derives what actually changed from the checkpoint diff and refuses anything unclaimed as `UNCLAIMED_CHANGE`. |
| Where the retro report ends up | A reader expects `docs/reports/retro-<sprint>.md` in the working tree the moment `archive` passes | The write lands in the candidate root `.devforgeai/work/<run>/wt`, which is gitignored. The report reaches the canonical checkout only at `devforgeai promote <run>`, never at Handoff: the last passing `devforgeai phase next` marks the run `ready_to_promote` and writes a `REQUIRE_HUMAN` handoff whose only forward step is that command, and `SKILL.md` runs it only after the user confirms in the session. A promotion refused with `STALE_BASE`, `DIRTY_TARGET` or `MERGE_CONFLICT` — all three refuse the promote command, not the transition — leaves the run `ready_to_promote` with its candidate root intact, and `devforgeai promote <run>` retries it once the user has resolved the reason. |
| A `REQUIRE_HUMAN` run treated as closed, with `/status` as its next step | `needs_user` and an exhausted attempt budget were described as closing the run, so the section 7e rows sent the user to `/status` and the OI-5 row said no flag could resume anything. A closed run has no candidate root, so the work the phases had already done appeared to be lost | Settled in `10-sequencer-and-contracts.md` (section 2's `phase start` row, section 3.1, section 5.4's `needs_user` row, section 6's `REQUIRE_HUMAN`, blocked-run row): such a run stays `active` with its lease released, keeps its candidate root and every checkpoint, and records `run.yaml#blocked_at`. `devforgeai phase start retro <arg>` — the same skill and argument — resumes it at `blocked_at` with `attempts` reset. The two section 7e `REQUIRE_HUMAN` rows, section 7a step 6, OI-5 and the section 10 eval expectation that asserted `/status` as step 1 now name `/retro {sprint}` as the forward step, with `devforgeai phase fail --reason <text>` then `/status` as the abandon route; any other skill on the same story needs that `phase fail` first. |
| Promotion read as part of Handoff | "The report reaches the canonical checkout at Handoff, when the sequencer promotes the run" made `devforgeai phase next` move canonical bytes on its own, with no point at which the user consents | Section 7b's candidate-root paragraph ("At Handoff the sequencer promotes the run"), section 7b row 7 and the row above now carry the two-block model of `WRITE-MODEL-REVISION.md` D7 and `10-sequencer-and-contracts.md` sections 5.4, 6 and 12.4: `phase next` marks the run `ready_to_promote` and writes a `REQUIRE_HUMAN` block whose only forward step is `devforgeai promote <run>`; `SKILL.md` runs that command only after the user confirms; the promotion writes the second block. |
| `STALE_BASE`, `DIRTY_TARGET` and `MERGE_CONFLICT` attributed to the transition | The refusals read as ways the last transition can fail, and the "two sprints at once" row had the second run promote itself the moment its last phase passed | All three refuse `devforgeai promote <run>` (`10-sequencer-and-contracts.md` section 2's refusal table, section 12.4's ordered steps). The row above names the command that raises them and states the root survives; the two-sprints row now has both runs stop at `ready_to_promote` and wait for the user. |
| The section 7e table had no `ready_to_promote` row | The row below already told a reader to read every `pass` row as the post-promotion block, but the table itself never named the promote step, so a generator reading only the table would omit it | A `ready_to_promote` outcome row now heads the table with `devforgeai promote {run}` as its one forward step; the two `pass` rows keep `/status` and are the second block. |
| `promote <run>` was missing from the compiled grammar | Section 7f's Tools row already granted `devforgeai promote <run>`, but the section 7a procedure stopped at printing the block and the section 12 `allowed-tools` line omitted it, so the compiled skill could not run the only command its own handoff names | `WRITE-MODEL-REVISION.md` D7 propagates the fifth model-callable form everywhere the four are enumerated. A new step 7 in section 7a calls it after the user asks (the abandon step became 8), the `allowed-tools` line carries `Bash(devforgeai promote:*)`, section 12's paragraph above it says five model-callable operations rather than four, and the Tools row no longer describes the command as something reached only after a refused promotion. |
| Reading the section 7e `pass` rows as the block a finished run prints first | `10-sequencer-and-contracts.md#6-handoff-envelope` no longer carries a `document run, all phases passed` row: `/status` is now the `next` of a **promoted** document run, and a run whose phases all passed but which is not yet promoted takes `devforgeai promote <run>` instead. | Read every 7e `pass` row as the post-promotion block. The first block a finished run writes names `devforgeai promote <run>`, which the user runs; the `/status` row is what the second block carries. |
| Retrospecting two sprints at once | Both runs would claim their own report path, so the fences are disjoint and both open | `FENCE_OVERLAP` refuses only overlapping fences, so two retro runs on different sprints are legal. Both stop at `ready_to_promote` and wait for the user; the second `devforgeai promote <run>` may see `STALE_BASE`; in worktree mode the sequencer rebases the run branch onto the new HEAD, reruns the last transition oracle and retries the fast-forward, and any rebase conflict aborts to `needs_user` with `MERGE_CONFLICT`. Re-running `/retro <sprint>` for the same sprint while its run is active is refused as `FENCE_OVERLAP`. |

## 10. Success criteria and test cases

### Success criteria

- Triggers on the section 4 positives and on none of the near-misses.
- The transcript contains exactly one `devforgeai phase start retro <sprint>` and no other `devforgeai` operation except `devforgeai status` and, when the user abandons, `devforgeai phase fail --reason`.
- Four worker dispatches at most, in registry order, one per phase.
- The run's checkpoint diff holds exactly one path, `docs/reports/retro-<sprint>.md`, and it is the `archive` receipt's only `claimed_paths` entry; the three judge phases leave an empty diff and write only under `.devforgeai/work/<run>/evidence/<agent>/`, which no checkpoint records and no promotion carries.
- Every Lessons row carries at least one evidence path that exists in the fixture.
- Every Proposed Amendments row names a document that exists under `docs/architecture/` and a single-line `/amend` command.
- `SKILL.md` is under 500 lines; `agents/` holds exactly the four files in section 8.

### Fixture

The generator creates `fixtures/retro/` with exactly these files before running any eval, and copies it to `retro-workspace/fixture-<eval-id>/` per eval:

| Path | Content |
|---|---|
| `.devforgeai/state.yaml` | `version: 1`, `target: [claude]`, `mode: greenfield`, `slug: shop`, `phase: qa`, `active_sprint: sprint-002`, `enforcement:` an empty mapping, `next: "/status"`. No active run, so `phase start` can open one. |
| `.devforgeai/hooks/devforgeai.py`, `policy.py`, `dispatch.py` | byte copies of `docs/design/examples/hooks/devforgeai.py`, `policy.py` and `dispatch.py`, so the `SubagentStop` route applies results |
| `.devforgeai/provenance/adr/0001-choose-sqlite.md` | `adr` template v1, `id: ADR-0001`, `status: accepted`, sections Context, Decision, Consequences, Alternatives |
| `.devforgeai/work/STORY-004/green-result.json` | a recorded `devforgeai.worker-result/v1` for `skill: dev`, `phase: green`, `status: pass`, with `application: applied`, `agent: green_dev` and a `captured_at` timestamp |
| `.devforgeai/work/STORY-007/green-result.json` | the same shape |
| `.devforgeai/provenance/log.jsonl` | eight lines with `at`, `kind` and `session_id`: for STORY-004 a `phase.start`, two `transition.fail` lines for `green` and a `transition.pass`; for STORY-007 a `phase.start` and one `transition.pass` per phase |
| `docs/architecture/constitution.md` | `constitution` template v1 with sections `## Principles`, `## Mandates`, `## Constraints`, `## Style` |
| `docs/plan/shop/sprints/sprint-002.md` | `sprint` template v1, `id: sprint-002`, `slug: shop`, `status: closed`, frontmatter `stories: [STORY-004, STORY-007]`, sections Goal, Stories, Order, Exit Criteria |
| `docs/plan/shop/stories/STORY-004.md`, `STORY-007.md` | `story` template v3, `status: done`, each with one acceptance criterion about the success path and none about the error path |
| `docs/reports/qa-STORY-004.md` | `qa-report` template v1, `verdict: fail`, one Criteria row failing on unhandled error input, one Fix Guidance row |
| `docs/reports/qa-STORY-007.md` | `qa-report` template v1, `verdict: fail`, one Criteria row failing on the same class of unhandled error input |
| `docs/reports/review-STORY-004.md`, `review-STORY-007.md` | `review-report` template v1, `verdict: pass`, no findings |
| `docs/reports/dev-STORY-004-green.md` | the rendered `dev-notes` view for that phase |

Overlay for eval 2: `fixtures/retro/overlays/eval-2/docs/reports/qa-STORY-004.md` and `qa-STORY-007.md` replace the base files with `verdict: pass` versions whose Criteria rows all pass, so no recurring defect exists. Overlay for eval 3: `fixtures/retro/overlays/eval-3/docs/plan/billing/sprints/sprint-002.md` adds a second sprint file with the same id, `id: sprint-002`, and the same frontmatter `slug: shop` as the base file, so the slug tie-break cannot resolve it.

### evals/evals.json (used verbatim)

```json
{
  "skill_name": "retro",
  "evals": [
    {
      "id": 1,
      "prompt": "/retro sprint-002",
      "expected_output": "A retro report for sprint-002 that names the repeated qa failure as a lesson and names one amend command against the constitution.",
      "files": ["fixtures/retro"],
      "expectations": [
        "The transcript contains exactly one occurrence of 'devforgeai phase start retro sprint-002', and it precedes every worker dispatch",
        "docs/reports/retro-sprint-002.md exists and contains the headings '## Outcomes', '## Lessons', '## Proposed Amendments' and '## Archive'",
        "Under '## Lessons' there is a row whose id matches LESS-001 and whose evidence cell names both docs/reports/qa-STORY-004.md and docs/reports/qa-STORY-007.md",
        "Under '## Proposed Amendments' there is exactly one row and its command begins with '/amend constitution '",
        "Under '## Archive' the sprint file docs/plan/shop/sprints/sprint-002.md is named with an owner, and no file under docs/plan/ differs from the fixture copy",
        "No file outside docs/reports/ and .devforgeai/ differs from the fixture copy"
      ]
    },
    {
      "id": 2,
      "prompt": "sprint-002 is finished, what did we learn?",
      "expected_output": "A retro report whose Proposed Amendments table is empty because every criterion passed.",
      "files": ["fixtures/retro", "fixtures/retro/overlays/eval-2"],
      "expectations": [
        "docs/reports/retro-sprint-002.md exists and its '## Proposed Amendments' section contains no line beginning with '/amend'",
        "Under '## Lessons' every row's evidence cell names a file path that exists in the workspace",
        "The final printed handoff block lists '/status' as step 1 under 'Next steps'",
        "The transcript contains no occurrence of 'devforgeai phase next' or 'devforgeai ingest-result'"
      ]
    },
    {
      "id": 3,
      "prompt": "/retro sprint-002",
      "expected_output": "The run stops on the ambiguous sprint id and asks which project it belongs to.",
      "files": ["fixtures/retro", "fixtures/retro/overlays/eval-3"],
      "expectations": [
        "No file named docs/reports/retro-sprint-002.md exists after the run",
        "The transcript shows one dispatch of report_collector and no dispatch of lesson_extractor",
        "The report_collector envelope in the transcript has status 'needs_user' and its issues name both docs/plan/shop/sprints/sprint-002.md and docs/plan/billing/sprints/sprint-002.md, which carry the same frontmatter slug",
        "The final printed handoff block reports the outcome REQUIRE_HUMAN and names '/retro sprint-002' as step 1, the command that resumes the blocked run"
      ]
    }
  ]
}
```

Quick-mode results are generation feedback only: one enabled run per eval and no baseline. They are not runtime conformance evidence, and no section of this spec gates on such evidence; the deferred contract is `12-post-mvp.md#pm-02`.

## 11. Dependencies and compatibility

| Kind | Value |
|------|-------|
| Tools | `SKILL.md`: `Read`, `Agent`, and a Bash grammar no wider than `devforgeai status`, `devforgeai phase start retro <sprint>`, `devforgeai phase fail --reason <text>`, `devforgeai validate`, plus `devforgeai promote <run>`, which the last passing transition's `REQUIRE_HUMAN` block names as its only forward step and which `SKILL.md` calls only after the user asks for it. Judges: `Read`, `Grep`, `Glob`, `Bash(devforgeai status)` and `Write` scoped to `.devforgeai/work/<run>/evidence/<agent>/`. The one producer: the same read set plus `Edit` and `Write` (Codex `apply_patch`) inside the candidate root. No phase grants a stack key, so no worker carries `Bash(devforgeai run *)`. |
| MCP servers | none |
| Runtime | Python 3.11+ for `scripts/sprint_evidence.py`; standard library only, no third-party import |
| Project commands | none. No retro phase declares a run key, so this skill resolves no `.devforgeai/stack.yaml` anchor and brokers no command. Its oracles are `report_only` and `document`, neither of which runs a command. |
| DevForgeAI/Core compatibility | DevForgeAI sequencer contract `10-sequencer-and-contracts.md` dated 2026-09-02; worker envelope `devforgeai.worker-result/v1`; `retro-report` template version 1; consumes `sprint` v1, `qa-report` v1, `review-report` v1, `dev-notes` v1. Research Core: NOT_APPLICABLE. |
| Other skills | Consumes what `plan`, `dev`, `review` and `qa` produced. Hands off to `amend` (one command per proposal) and `plan` (next sprint). Must not conflict with `analyze`, which walks the traceability chain rather than one sprint's outcomes. |

Deferred dependencies. Each names its `12-post-mvp.md` entry and what this skill does today without it.

- `12-post-mvp.md#pm-01`. Runtime verification that a dispatched worker ran in its own context window is deferred. Today `isolation: required` is a declaration compiled into the target profile, and `skill-validator` checks the declaration structurally.
- `12-post-mvp.md#pm-02`. There is no runtime conformance evidence for this skill. Quick-mode eval results are generation feedback and no section gates on them.
- `12-post-mvp.md#pm-05`. Per-run token figures are not available to a hook, so the Outcomes table records verdicts, oracle classifications and the attempt counts read from `provenance/log.jsonl`, and no cost or usage column.
- `12-post-mvp.md#pm-06`. Only the `skip` and `quick` eval modes exist; a third mode name is a spec defect.
- `12-post-mvp.md#pm-10`. There is no clean-checkout chain validator, so nothing outside a session re-checks that a named amendment was ever applied. The retro report records the proposal; `/analyze` and the next `/amend` run are where it is picked up.

Frontmatter values derived from this table. `allowed-tools` is a space-separated string of pre-approved tool patterns, per the Agent Skills specification; the Bash entries below are the five model-callable operations, `devforgeai promote <run>` included, and nothing wider, because an unscoped `Bash` entry would exceed the grammar section 14's skill-validator check enforces.

```yaml
compatibility: "Claude Code and Codex terminals. Requires an installed DevForgeAI sequencer and hook dispatcher, plus a sprint whose stories have recorded qa or review reports."
allowed-tools: "Read Agent Bash(devforgeai status) Bash(devforgeai phase start retro:*) Bash(devforgeai phase fail:*) Bash(devforgeai validate) Bash(devforgeai promote:*)"
```

## 12. Targets

The generator produces one provider-neutral semantic package and a separate adapter for each selected target when frontmatter, invocation policy, or agent configuration differs. Provider-neutral resources may be shared. Adapter directories are not required to be byte-identical or symlinked.

| Target | Install path | Invocation | Subagents | Notes |
|--------|--------------|------------|-----------|-------|
| claude | `.claude/skills/retro/` | `/retro <sprint>` | provider-native workers: judges `report_collector`, `lesson_extractor` and `amendment_proposer` (`writes: evidence`), producer `archiver` (`writes: candidate`) | Provider-specific frontmatter keys (`argument-hint`, `disable-model-invocation`) are compiled into this target's SKILL.md only. |
| codex | `.agents/skills/retro/` plus `.codex/agents/` profiles | `$retro <sprint>` | the same four names; Codex custom-agent `name` equals the Claude agent frontmatter `name`, so `agent_type` needs no translation | Portable six-field frontmatter only; policy goes in target-side configuration. |
| both | separate `.claude/skills/retro/` and `.agents/skills/retro/` adapters | as above | as above | Share only provider-neutral resources; validate each adapter independently. |

```yaml
metadata:
  version: "1.0.0"
  devforgeai-spec: "SKILL-SPEC-015"
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
- A lesson without an evidence path is not written, and a proposal without a lesson id is not written.
- `retro` owns only the `retro-report` template. It changes no document it reads; its one write is its own report inside the candidate root.

## 14. Acceptance checks

Run these before reporting done and paste their output:

```bash
# frontmatter and naming (skill-creator's own validator)
python -m scripts.quick_validate ./out/retro        # run from the skill-creator directory
# open-standard validator, if installed
skills-ref validate ./out/retro
# size budget
wc -l ./out/retro/SKILL.md                          # must be < 500
# every worker in section 7d has a prompt file, and no extra
ls ./out/retro/agents/                              # report_collector.md lesson_extractor.md amendment_proposer.md archiver.md
# one reference file per phase, plus envelope.md
ls ./out/retro/references/                          # collect.md lessons.md amendments.md archive.md envelope.md
# no leftover placeholders
grep -rnE 'T[O]DO|T[B]D|[{][{]' ./out/retro || echo clean
# spec battery (from the repository root)
python3 docs/design/specs/verify.py --only v1,v2,v4
```

For non-Research anatomy skills, DevForgeAI skill-validator additionally checks: all sub-phase kinds present with Gate, Record and Handoff bound to sequencer operations; `must_not` and a `writes` declaration of `candidate`, `evidence` or `none` present in every agent file, with no tool wider than that declaration allows; the SKILL.md Bash grammar is no wider than the model-callable operations; handoff outcomes cover every status the skill can return, including `could_not_run`.

## 15. Provenance

| Source | Hash | Used for |
|--------|------|----------|
| `docs/design/01-skill-anatomy.md#primary-window-contract` | sha256:de7d775e46bd44c52089a3998b114a5ebb5ce6875be3ebf3dca126f5a9bbaa32 | sections 2, 7a |
| `docs/design/01-skill-anatomy.md#evidence-home` | sha256:d4ad2626d2dc993f9879247429ce4a15a9dcee31c9b4b20da8178ffe8bac8dc9 | sections 6, 7d |
| `docs/design/10-sequencer-and-contracts.md#4-per-skill-phase-registry` | sha256:7d655abc79fb1789e37a57227eecc279faf035a0359ffa76e93b24b56796498e | sections 7b, 7c |
| `docs/design/10-sequencer-and-contracts.md#5-worker-result` | sha256:cee716ddb3ae9b6b4405037ede3bb7c6445e0e6c8ac28382344a655d31754dcd | sections 6, 7c, 7d |
| `docs/design/10-sequencer-and-contracts.md#3-status-vocabulary-and-gate-policy` | sha256:36ffb340bd5d843cd945f7d17a590e335e491b11a60b08d4bf70e12a3a223620 | sections 7c, 7e, 9 |
| `docs/design/10-sequencer-and-contracts.md#10-evidence-files` | sha256:4eebadd862a3dfd90bc0afff8342a1b18a76b2a4fe1ec5bafa23cea390f48984 | sections 6, 9 |
| `docs/design/10-sequencer-and-contracts.md#6-handoff-envelope` | sha256:de637edceb588df104a40b57738eb263989f6603f90ece6f4d0e64fef07ffb6a | section 7e |
| `docs/design/11-artifact-registry.md#1-template-registry` | sha256:25886acb1c2963b15938f0c577c3bfd28b9807dd2dd961c59ff2b43fa00b62e2 | sections 6, 8 |
| `docs/design/02-skill-roster.md#retro` | sha256:f2a88c7bda36610205f8044bbc8314c9c65c0f72339ba2445ccb6eba3675e17e | sections 1, 2, 7e |
| `docs/design/05-subagent-sets.md#sets-per-skill` | sha256:9e12f3beb236a025c18d40e741c09ba675bd71d2d87f56e2b205c7556b944bf9 | sections 7d, 9 |

Mirror of `depends_on` in the frontmatter, with the section each source fed.
