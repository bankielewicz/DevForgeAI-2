---
id: SKILL-SPEC-017
skill_name: status
target: both
status: approved
template: skill-spec
template_version: 1
author: "DevForgeAI spec author (wave 2)"
date: 2026-09-02
depends_on:
  - source: docs/design/10-sequencer-and-contracts.md#2-cli-grammar
    hash: sha256:87a07888354112467337a1b7a02b9111d2e2030e49ce8a25f22eb3f441ab87b7
    excerpt: |
      | `devforgeai status` | none | none | nothing | `0` | model |
  - source: docs/design/10-sequencer-and-contracts.md#9-enforcement-block
    hash: sha256:fb2caa96dcd1b9657eb01e5f2e2bdafaf00f92b9303292580d2c71e0af58bf03
    excerpt: "`.devforgeai/work/<run>/run.yaml`, `schemas/devforgeai/v1/run.schema.json`. Written by the sequencer at `devforgeai phase start` and updated at every transition. It outlives the candidate root: promotion and abandonment remove the root, branch, tags and copy-aside, and leave `run.yaml` with the final status so `devforgeai status`, inspection and `NO_CANDIDATE` still resolve."
  - source: docs/design/10-sequencer-and-contracts.md#6-handoff-envelope
    hash: sha256:3c4c95bbd73b5499e5569e650f84eea84cb68404c0909f5f1819c0f3a5c7b3d4
    excerpt: |
      | 7 | The run-end block and the `devforgeai status` block are the same rendering of the same file. |
  - source: docs/design/10-sequencer-and-contracts.md#4-per-skill-phase-registry
    hash: sha256:7c1d67f1154e49247e5dc178fcc1512bdbd53af378c360aeafe69bffed1136ab
    excerpt: |
      | status | none | — | none; the command is a thin wrapper over `devforgeai status` |
  - source: docs/design/01-skill-anatomy.md#state-file
    hash: sha256:b6afd02f6be66c6d1f475f84e66e384d4613a92706e71e849dc091610de8b25a
    excerpt: "`/status` renders this file. Only the `devforgeai` sequencer writes it, and only at `phase start` (registering the run), at promotion or abandonment, and at `phase fail`; Research state is written only by Research Core."
  - source: docs/design/01-skill-anatomy.md#handoff-template
    hash: sha256:69eaf61097311ab55d3f940d03a4d1694e58658a11da3f41cd12a51d216b762a
    excerpt: |
      The rendering of `handoff.json`. Printed by every slash command on completion and by `/status` on demand.
  - source: docs/design/02-skill-roster.md#status
    hash: sha256:8968e9247f9909e6289d81f659686f5a38eb79169c8a1ae9ce955537c5d01c1b
    excerpt: |
      - Zero LLM workers. `SKILL.md` is a thin wrapper over `devforgeai status`, which renders `.devforgeai/work/<run>/handoff.json` and the `next` recorded in `state.yaml`. It writes nothing.
  - source: docs/design/02-skill-roster.md#handoff-decision-tables
    hash: sha256:1dac784b4670cc7559f323011dfe304dfe8c0baf349063162f90d76d902c5d3c
    excerpt: |
      | status | any | the `next` recorded in `state.yaml`; status decides nothing itself |
  - source: docs/design/11-artifact-registry.md#4-upstream-and-downstream-per-skill
    hash: sha256:cfcaef76005176490e96b9e67c8fa4f0b7a6a2e13b6badf856468881fbe25200
    excerpt: |
      | status | — | `state.yaml`, `handoff.json` | nothing | — |
  - source: docs/design/05-subagent-sets.md#sets-per-skill
    hash: sha256:f2957217c9af147e4a7ea03749cbe6efda266bd56d403f39aa25c9a655872609
    excerpt: |
      | status | none; `SKILL.md` is a thin wrapper over `devforgeai status` |
  - source: docs/design/12-post-mvp.md#pm-05
    hash: sha256:67f35ed73777ffd7e03bb3e4b72cedf6057331e8f8033f6e2b7005f877edc591
    excerpt: |
      Until PM-05 lands, the primary-window contract is enforced structurally by `skill-validator`, not by measurement.
---

# Skill Specification: status

A stranger with no conversation history must be able to build this skill from this document alone. Every question the generator would otherwise ask is answered below.

`status` is the smallest skill in the roster and the only one that writes nothing at all. `10-sequencer-and-contracts.md` section 4 records its `kind` as `none`; `devforgeai phase start status` refuses with exit 1. Its whole body is one model-callable sequencer call and the rules for reading what that call printed.

## 0. Generator instructions

These instructions are addressed to the skill-generating agent (Anthropic's `skill-creator` skill, or DevForgeAI's `skill-generator`). They replace its interview.

### Cold-session prompt

Paste this into a fresh session from the repository root:

```
Use the skill-creator skill to build the skill specified in docs/design/specs/SKILL-SPEC-017-status.md.
Follow its section 0 exactly. Output directory: .devforgeai/skills. Eval mode: quick.
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
6. **Output location** is given in the prompt. Create `.devforgeai/skills/status/`. Do not write anywhere else except the `status-workspace/` sibling that eval runs require.
7. **On ambiguity, stop before output.** If the spec is still `draft`, contains an unresolved authoring assumption, omits a section, contradicts itself, or leaves a decision this document does not make, do not guess and do not write candidate skill files. End with a list titled `SPEC GAPS` naming each section and question. The spec author fixes and approves the spec before re-running.
8. **Fidelity over creativity.** Use the description in section 3 verbatim. This skill has no worker contracts and no scripts, so it produces no `agents/` directory and no `scripts/` directory. Do not add a bundled renderer, a state parser, or any second reader of `.devforgeai/`: section 9 records why.
9. **Finish with the acceptance checks** in section 14 and include their output in your final message.

## 1. Identity

| Field | Value |
|-------|-------|
| name | `status` (kebab-case, max 64 chars, equals the directory name, no `claude`/`anthropic` prefix) |
| title | DevForgeAI Status |
| purpose | Print where a DevForgeAI project currently stands — the active run, its phase, its fence and its attempt counters, plus the one command recorded as `next` — from a cold session with no memory of how it got there. |
| category | devforgeai-phase |
| version | 1.0.0 (skill-package version written to `metadata.version`; not the DevForgeAI or Research Core version) |

## 2. Problem and requirements

**Without this skill:** a user returning to a project after a break, or opening a fresh session mid-sprint, has to reconstruct state by reading `.devforgeai/state.yaml` by hand and knowing what an empty `enforcement` mapping means. That reading is easy to get wrong in the direction that costs the most: an `enforcement` block with `run: STORY-001` and `phase: red` looks like progress, but `10-sequencer-and-contracts.md` section 9 makes the block live only while `stories.<id>.status == in_dev` or `runs.<run>.status == active`, and a stale block left by a crashed session means every write and every non-read-only command is denied with no obvious cause. The user then fights the hook layer instead of the work.

The second failure is inventing the next command. `01-skill-anatomy.md`'s handoff rule 1 requires one exact, copy-pasteable command and forbids a description; rule 4 requires that it work from a fresh session. A model that composes that command from conversation memory violates both, because the memory is exactly what a cold session does not have. `state.yaml` holds the value the sequencer recorded, and reading it out is the entire job.

| ID | Kind | Requirement |
|----|------|-------------|
| R1 | explicit | Print the enforcement block and the recorded `next`, per `02-skill-roster.md#status` and the `devforgeai status` row in `10-sequencer-and-contracts.md` section 2. |
| R2 | explicit | Write nothing. `11-artifact-registry.md` section 4 records status's Produces column as `nothing`. |
| R3 | explicit | Decide nothing. `02-skill-roster.md`'s status row reads "the `next` recorded in `state.yaml`; status decides nothing itself". |
| R4 | implicit | Work while a run is active. `devforgeai status` is the one sequencer operation the hook dispatcher allows unconditionally, including from inside a phase worker; it is matched and returned before the active-run and subagent checks in `dispatch.py`. |
| R5 | implicit | Work in a repository with no `.devforgeai/` at all. The operation exits 0 there and prints an empty enforcement mapping. |
| R6 | implicit | Take no argument. `devforgeai status` accepts none, so the missing-positional-argument problem that `phase start` has does not reach this skill. |
| R7 | discovered | Read `state.yaml` through the sequencer, not directly. `01-skill-anatomy.md`'s primary-window contract keeps artifacts out of the primary window; the enforcement block is small, bounded, and already summarised by the operation, and a second parser would be a second source of truth for a file the sequencer owns. |
| R8 | discovered | Report the mid-run case honestly. `devforgeai status` prints `next: null` while a run is in progress, because `next` is only written at `phase next` and `phase fail`. Section 7's outcome table says what to print then instead of inventing a command. |

## 3. Description

The exact frontmatter `description`:

```yaml
description: >
  Print where this DevForgeAI project stands and the exact next command. Use this
  skill whenever someone asks what phase they are in, what is in progress, where
  they left off, what to run next, why a write was just denied, or opens a cold
  session in a repository that has a .devforgeai directory and needs to pick up
  where the last session stopped. It reports the active run, its phase, write
  fence, attempt counters and gate policy, plus the next command the sequencer
  recorded, and it writes nothing and decides nothing. Do NOT use it to install
  DevForgeAI (use init), to start or resume work on a story (use dev), or to read
  a QA or review report, which are files under docs/reports.
```

Character count: 685 / 1024.

## 4. Trigger set

```json
[
  {"query": "/status", "should_trigger": true},
  {"query": "where did we leave off", "should_trigger": true},
  {"query": "what phase am I in", "should_trigger": true},
  {"query": "I'm back after the weekend, what's the state of this project and what do I run next?", "should_trigger": true},
  {"query": "why did that edit just get blocked, is something in progress?", "should_trigger": true},
  {"query": "whats teh next command", "should_trigger": true},
  {"query": "new session here, no idea what happened last time — catch me up on this repo", "should_trigger": true},
  {"query": "is STORY-001 still open or did it finish", "should_trigger": true},
  {"query": "show me the write fence for whatever is running right now", "should_trigger": true},
  {"query": "the hook keeps denying my Write tool call and I don't know why", "should_trigger": true},
  {"query": "set devforgeai up in this repository", "should_trigger": false},
  {"query": "what did QA find on STORY-004", "should_trigger": false},
  {"query": "start the next story in the sprint", "should_trigger": false},
  {"query": "summarise the last three commits", "should_trigger": false},
  {"query": "git status", "should_trigger": false},
  {"query": "the run is stuck, close it and start over", "should_trigger": false},
  {"query": "which stories are left in sprint-001, plan the next one", "should_trigger": false},
  {"query": "check whether the docs still match the code", "should_trigger": false},
  {"query": "write a retro for sprint-001", "should_trigger": false},
  {"query": "run the test suite and tell me if it's green", "should_trigger": false}
]
```

The sharpest near-misses are "git status", which shares the whole word and needs a different tool entirely, and "the run is stuck, close it and start over", which shares status's subject but asks for a write: closing a run is `devforgeai phase fail --reason`, which status names in its outcome table and never calls.

## 5. Use cases

### UC-1: Cold session, run in progress
- **User says:** "new session, what's going on in this repo?"
- **Steps:**
  1. Run `devforgeai status`.
  2. The output carries a non-empty `enforcement` with `run: STORY-001`, `skill: dev`, `phase: red`, a three-path `write_fence`, `attempts` all zero, `max_attempts` per phase, and `next: null`.
  3. Compare `enforcement.session_id` with the printed `session` value. They differ, so the run was opened by a session that is gone.
  4. Print the output verbatim, then the row from section 7's outcome table for an orphaned active run.
- **Result:** the user sees that STORY-001 is at phase `red` with a fence of three paths, that this is why direct edits are denied, and that the one command that moves anything is `devforgeai phase fail --reason` followed by re-running `/dev STORY-001`.

### UC-2: Between runs
- **User says:** "what do I run next"
- **Steps:**
  1. Run `devforgeai status`.
  2. `enforcement` is `{}` and `next` is `/review STORY-001`.
  3. Print the output and then `next` as the single numbered forward command.
- **Result:** the user has one copy-pasteable command that came out of `state.yaml`, not out of the model's memory of the session that wrote it.

### UC-3: A blocked run waiting for an answer
- **User says:** "I answered the question, what now"
- **Steps:**
  1. Run `devforgeai status`.
  2. `runs` carries `clarify-STORY-007` with `status: active`; `enforcement` is non-empty, its `lease` is null and its `blocked_at` is `record_answers`.
  3. Print the output verbatim, then the sequencer's rendering of that run's `handoff.json`, whose `outcome` is `REQUIRE_HUMAN` and whose `next` is `/clarify STORY-007`.
  4. Print that command as the single numbered pending step, from the section 7 row for a run whose `blocked_at` is set.
- **Result:** the user learns the run was blocked, not closed; that its candidate root and every checkpoint survived; and that `/clarify STORY-007` resumes it at `record_answers` with attempts reset. Abandoning instead is `devforgeai phase fail --reason <text>`, which the same block records as the alternative.

### UC-4: A finished run waiting for promotion
- **User says:** "did that clarify run do anything? nothing changed"
- **Steps:**
  1. Run `devforgeai status`.
  2. `runs` carries `clarify-STORY-007` with `status: ready_to_promote`, `root: .devforgeai/work/clarify-STORY-007/wt` and the last phase's `checkpoint`; `enforcement` is `{}`, because the run holds no lease and no phase is active.
  3. Print the output verbatim, then the sequencer's rendering of that run's `handoff.json`, whose `outcome` is `REQUIRE_HUMAN` and whose `next` is `devforgeai promote clarify-STORY-007`.
  4. Print that command as the single numbered pending step, from the section 7 row for `status: ready_to_promote`.
- **Result:** the user learns the run finished its phases, that its work is sitting in the candidate root because promotion is never automatic, and that `devforgeai promote clarify-STORY-007` is the one command that moves it into the working tree. Status prints the command; it never runs it.

### UC-5: Uninstalled repository
- **User says:** "where are we with devforgeai here"
- **Steps:**
  1. Run `devforgeai status`. It exits 0 and prints `enforcement: {}`, `next: null` and `session: ''`.
  2. That triple is the uninstalled shape; the sequencer distinguishes it from an installed idle project only by whether `state.yaml` exists, and status does not open that file.
  3. Print the output and the `/init` row from section 7's outcome table, which names `/init` first and the installed-but-idle reading second.
- **Result:** the user is told the framework has recorded nothing here and that `/init` is the command that changes it.

## 6. Inputs and outputs

### Inputs
| Input | Format | Example file | Required |
|-------|--------|--------------|----------|
| `.devforgeai/state.yaml` | YAML, read by the sequencer, never by the skill; carries story statuses and the `runs` map | `docs/design/examples/hooks/fixtures/.devforgeai/state.yaml` | no; an absent file yields the empty shape |
| `.devforgeai/work/<run>/run.yaml` | YAML, read by the sequencer, never by the skill; carries the per-run enforcement block including `phase`, `fence`, `test_paths`, `granted_keys`, `lease`, `blocked_at` and `bounce_count` | written by `devforgeai phase start` | no; absent between runs |
| `.devforgeai/sessions/*.json` | JSON, read by the sequencer to name the current session | written by `devforgeai session-start` | no |
| `.devforgeai/work/<run>/handoff.json` | JSON | written by `devforgeai phase next`, by `devforgeai phase fail`, and again by `devforgeai promote <run>`, which is why a run has two envelopes over its life and the second is the one a promoted run shows | no; when one exists the sequencer renders it after the enforcement block, and when none does the enforcement block is the whole output |

`status` gates on no artifact and takes no argument.

### Outputs
| Output | Format | Location | Template |
|--------|--------|----------|----------|
| the status block | text on the session transcript | not a file | the enforcement mapping, then the sequencer's own rendering of `handoff.json` when one exists. `assets/handoff.md` records the fuller "You are here" shape from `01-skill-anatomy.md#handoff-template`, which no renderer fills |

`11-artifact-registry.md` section 4 records status's Produces column as `nothing`, and section 1 records that status owns no template: the `handoff` template is filed under `.devforgeai/skills/status/templates/handoff.md` because status is the skill that prints the block on demand, while the sequencer is its only writer.

### Output template: what `devforgeai status` prints today

Verbatim shape, from `docs/design/examples/hooks/devforgeai.py`'s status operation. It is one YAML mapping with exactly four top-level keys: `runs`, `enforcement`, `next` and `session`. `runs` is the canonical `state.yaml#runs` map, one entry per registered run. `enforcement` is the active run's per-run block, which lives in `.devforgeai/work/<run>/run.yaml` and not in `state.yaml` — the split the sequencer keeps so a candidate root never reads canonical state. A run blocked by `needs_user` or an exhausted attempt budget is still `active`, so it still has an `enforcement` block; what marks it is `blocked_at` naming the phase and `lease: null`.

```yaml
runs:
  STORY-001:
    story: STORY-001
    skill: dev
    mode: worktree
    root: .devforgeai/work/STORY-001/wt
    base_ref: 4f2a9c1d8e7b6a5f4e3d2c1b0a9f8e7d6c5b4a39
    checkpoint: devforgeai/STORY-001/red
    status: active
enforcement:
  run: STORY-001
  skill: dev
  arg: STORY-001
  kind: story
  phase: red
  candidate:
    id: STORY-001
    mode: worktree
    root: .devforgeai/work/STORY-001/wt
    base_ref: 4f2a9c1d8e7b6a5f4e3d2c1b0a9f8e7d6c5b4a39
    checkpoint: devforgeai/STORY-001/red
  lease:
    session_id: session-1
    agent: red_dev
    phase: red
  write_fence:
  - tinyapp/text.py
  - tests/test_text.py
  - pyproject.toml
  test_paths:
  - tests/test_text.py
  test_plan:
  - criterion: 1
    file: tests/test_text.py
    name: test_slugify_basic
  commands:
    source: .devforgeai/stack.yaml#python
    use:
    - test
    - lint
  granted_keys:
  - test
  - lint
  gate_policy:
    test_runner_missing: REQUIRE_HUMAN
  attempts:
    red: 0
    green: 0
    refactor: 0
    smoke: 0
    review: 0
  max_attempts:
    red: 2
    green: 3
    refactor: 2
    smoke: 2
    review: 2
  session_id: session-1
next: null
session: ''
```

Four of those keys are what makes the block worth printing mid-run, and step 2 forbids dropping any of them. `candidate.root` is the directory every write of this run lands in, so a user who cannot find an edited file learns where it went. `candidate.checkpoint` is the tag or manifest the current phase built on, so a rewind or a retry has a name. `candidate.base_ref` is what promotion compares canonical HEAD against, so a `STALE_BASE` refusal is legible before it happens. `lease` names the one session and agent that may write right now, which is why a second window's write is denied. The dispatch block a primary window pastes into a worker prompt is `run`, `candidate.root`, `phase`, `write_fence` and `granted_keys`, taken from exactly these fields.

The fixture above has no handoff envelope on disk, so the enforcement mapping is the whole output. When one exists, the sequencer appends its rendering — the same function `phase next` prints at a run end — after a blank line:

```
STORY-001  REQUIRE_HUMAN
  - refactor: COULD_NOT_RUN: runner_missing: ruff is not installed
Next: install the missing runner, then /dev STORY-001
```

A **blocked** run — one a `needs_user` result or an exhausted attempt budget stopped — is still `active`, so its enforcement block is still printed. Two fields say it is blocked rather than running: `lease` is null and `blocked_at` names the phase it stopped at. Only the differing keys are shown here; the rest of the block is as above:

```yaml
runs:
  clarify-STORY-007:
    story: STORY-007
    skill: clarify
    mode: worktree
    root: .devforgeai/work/clarify-STORY-007/wt
    base_ref: 4f2a9c1d8e7b6a5f4e3d2c1b0a9f8e7d6c5b4a39
    checkpoint: devforgeai/clarify-STORY-007/questions
    status: active
enforcement:
  run: clarify-STORY-007
  skill: clarify
  arg: STORY-007
  phase: record_answers
  blocked_at: record_answers
  lease: null
next: /clarify STORY-007
session: session-2
```

The pending step of a blocked run is the skill's own command with the same argument: `devforgeai phase start clarify STORY-007` resumes the run at `blocked_at` with `attempts` reset, in the candidate root it kept, instead of refusing (`10-sequencer-and-contracts.md` sections 2 and 3.1). Status prints that command from `next`; it does not run it. Abandoning instead is `devforgeai phase fail --reason <text>`, and any **other** skill on the same story needs that first.

A run that has finished its phases renders the same way, with `enforcement` empty because no phase is active and no lease is held, and with the run still listed:

```yaml
runs:
  clarify-STORY-007:
    story: STORY-007
    skill: clarify
    mode: worktree
    root: .devforgeai/work/clarify-STORY-007/wt
    base_ref: 4f2a9c1d8e7b6a5f4e3d2c1b0a9f8e7d6c5b4a39
    checkpoint: devforgeai/clarify-STORY-007/record_answers
    status: ready_to_promote
enforcement: {}
next: devforgeai promote clarify-STORY-007
session: session-2
```

The envelope rendering under it is `render_handoff` over the `REQUIRE_HUMAN` block `finish_run` wrote, with that function's own reason lines and nothing added:

```
clarify-STORY-007  REQUIRE_HUMAN
  - all clarify phases passed
  - the candidate root is at checkpoint devforgeai/clarify-STORY-007/record_answers
Next: devforgeai promote clarify-STORY-007
```

That is the whole of what `ready_to_promote` looks like from a cold session: the run block names the root and the checkpoint, and the envelope's one forward command is the pending step. Promotion is never automatic, so this state is where every run's phases end; `devforgeai promote <run>` is the command a human runs next, and `status` prints it without calling it.

With no active run, and in a repository with no `.devforgeai/` directory, the same operation exits 0 and prints:

```yaml
runs: {}
enforcement: {}
next: null
session: ''
```

Between runs in an installed project, `runs` is not empty: it carries every run the project has registered, including `promoted` and `abandoned` ones, and every run sitting at `ready_to_promote`. That last state is the normal end of a run's phases, not an error: promotion is never automatic, so the last passing transition marks the run `ready_to_promote` and leaves it there until a human runs the command, and a refused promotion leaves it there too. It is the state to look for after a run appears to have finished with nothing in the working tree: `devforgeai promote <run>` is the pending step that completes it, and section 7's outcome table has a row for it.

### Output template: `assets/handoff.md`

The block shape `01-skill-anatomy.md#handoff-template` defines, shipped so the target rendering has a home and a version. Its first line records what is and is not implemented: the sequencer's `render_handoff` is real — `devforgeai status` prints it after the enforcement block, and it is the same function `phase next` prints at a run end, which is `10-sequencer-and-contracts.md` section 6 rule 7 — but it prints the envelope's own fields under rule 8, not the progress bar and the sprint line below. Nothing fills this fuller shape today, and the skill must not hand-format it.

```
DevForgeAI — You are here
────────────────────────────────────────────────────────────────
Project      SLUG                         Mode   MODE
Progress     init > onboard > brainstorm > pm > architect > PHASE > dev > review > qa
Phase        PHASE (STATE)                Sprint SPRINT
Last action  COMMAND  — SUMMARY

Artifacts produced this run
  PATH

Open issues
  ID  KIND: TEXT

Next steps (run in a cold session)
  1. COMMAND

Also possible
  /status                reprint this block
────────────────────────────────────────────────────────────────
```

### Return envelope

Not applicable. `status` dispatches no worker, so no `devforgeai.worker-result/v1` object is produced or consumed. `05-subagent-sets.md#sets-per-skill` records status's worker set as none, and `10-sequencer-and-contracts.md` section 4 gives it `kind: none` with no phases.

## 7. Procedure

### Steps

The `SKILL.md` body. Four steps, one command.

1. Run `devforgeai status` — why: it is the only operation that reports state, it is allowed in every situation including from inside a phase worker, and it exits 0 whether or not a run is active or the framework is installed, so there is no branch before it.
2. Print its output verbatim — why: the enforcement block is the record `10-sequencer-and-contracts.md` section 9 defines, and paraphrasing it drops the fields (`write_fence`, `attempts`, `session_id`) that explain why a tool call was denied. `references/output.md` explains each field and who writes it.
3. Select one row from the outcome table below by reading three values out of that output: whether `enforcement` is empty, whether `next` is null, and whether `enforcement.session_id` equals the printed `session` — why: those three comparisons are the whole decision, and every one of them is a value the sequencer printed rather than a judgement about the project.
4. Print the selected row's next step as a single numbered command, and any alternatives under "Also possible" — why: `10-sequencer-and-contracts.md` section 6 rules 1 and 3 require exactly one forward path, numbered, with alternatives kept separate, so the default is unambiguous.

The skill runs no other command, opens no file, and dispatches nothing.

### Sub-phases and workers

`01-skill-anatomy.md`'s seven sub-phases govern anatomy skills that open a run. `status` opens none: `10-sequencer-and-contracts.md` section 4 gives it `kind: none` and states that `devforgeai phase start` refuses it. The mapping is degenerate and is recorded here so the generator does not invent phases.

| # | Sub-phase | Performed by | Isolation |
|---|-----------|--------------|-----------|
| 0 | Gate | none. `devforgeai phase start status <arg>` refuses with exit 1 and the message `skill status has no LLM workers and no phases; it is a thin wrapper over a deterministic operation`. | n/a |
| 1 | Slice | none | n/a |
| 2 | Work | none. The single operation is `devforgeai status`. | n/a |
| 3 | Write | none. This skill writes nothing anywhere. | n/a |
| 4 | Review | none | n/a |
| 5 | Record | none. There is nothing to record: the run this skill reports on is somebody else's. | n/a |
| 6 | Handoff | none. No `handoff.json` is written. The printed next step is the `next` value the sequencer already recorded, and where an envelope exists the sequencer renders it; the skill composes neither. | n/a |

### Sequencer operations

`status` has no registry phases, so the evidence and gate table in `10-sequencer-and-contracts.md` section 11 has no rows to fill. The operations it uses are these, and no other.

| Operation | Access | Called by | Precondition | Effect on `status` |
|---|---|---|---|---|
| `devforgeai status` | model | step 1, always, exactly once | none | prints `enforcement`, `next` and `session`, then the sequencer's own rendering of the run's `handoff.json` when one exists; writes nothing, not even the work directory; exits 0 |
| `devforgeai phase start status <arg>` | model | never | — | refuses with exit 1; recorded here so no generated `SKILL.md` calls it |
| `devforgeai phase fail --reason <text>` | model | never | a run is active | named in one outcome row as the user's escape from an orphaned run; status does not call it, because calling it would write `handoff.json` and clear the enforcement block, and R2 forbids status writing anything |
| `devforgeai promote <run>` | model | never | the run's `status` in `runs` is `ready_to_promote` and the user asked for it | named in one outcome row as the pending step of every run whose phases have all passed — promotion is never automatic — and of a run whose promotion was refused with `STALE_BASE`, `DIRTY_TARGET` or `MERGE_CONFLICT`, which are refusals of this operation and not of `devforgeai phase next`; status prints the command and never calls it, because it writes the canonical checkout |
| `devforgeai validate` | model | never | a run is active | a read-only invariant scan, but it is the `validate` skill surface, not the status surface; status reports state and runs no scan |

The dispatcher admits `devforgeai status` before any other test: `dispatch.py`'s sequencer check returns on an exact match of `devforgeai status` ahead of the active-run branch and ahead of the phase-worker branch. That is why R4 holds and why a phase worker may call it while every other operation is refused.

### Worker contracts

None. `status` has no worker, so the generated skill has no `agents/` directory and no `references/envelope.md`. It also has no producer and no judge: the skill runs one read-only operation in the primary window and prints what it printed. There is nothing here for `skill-generator` to compile into `.claude/agents/` or `.codex/agents/`, and a generated package that contains such a file is a defect `skill-validator` reports under its anatomy rule 2.

### Handoff outcomes

`status` writes no `handoff.json`. The rows below are the expansion of `02-skill-roster.md`'s single status row — "the `next` recorded in `state.yaml`; status decides nothing itself" — across the shapes the printed output actually takes. Each row's condition is a comparison over printed values, so no row requires a judgement.

| Outcome | Next steps |
|---------|------------|
| `enforcement` is `{}` and `next` holds a command | 1. that `next` value, verbatim. Also possible: nothing; the sequencer chose it at the last transition. |
| `enforcement` names a run whose `blocked_at` is set and whose `lease` is null | 1. `/<enforcement.skill> <enforcement.arg>` — `devforgeai phase start` with the same skill and argument resumes a blocked run at `run.yaml#blocked_at` with `attempts` reset, in the candidate root it kept, rather than refusing (`10-sequencer-and-contracts.md` sections 2 and 3.1). The handoff's `open_items` say what the user must answer or fix first. Also possible: `devforgeai phase fail --reason <text>` to abandon the root, then `/status`; any **other** skill on the same story needs that first. |
| `enforcement` is `{}` and some entry in `runs` has `status: ready_to_promote` | 1. `devforgeai promote <run>` for that run id — this is the run's pending step, printed for every run whose phases have all passed, because the last passing transition marks the run `ready_to_promote` and writes a `REQUIRE_HUMAN` block whose only forward step is that command. A run in this state has produced its files inside its candidate root and has not yet put them in the working tree. Also possible: read `.devforgeai/work/<run>/handoff.json`, which carries a `STALE_BASE`, `DIRTY_TARGET` or `MERGE_CONFLICT` reason when a previous `devforgeai promote <run>` was refused. |
| `enforcement` is `{}`, `next` is null, `session` is empty | 1. `/init`. Also possible: if `.devforgeai/state.yaml` exists, the project is installed and idle and the forward command is the one for its recorded phase, which the last run's `docs/reports/` view names. |
| `enforcement` is non-empty and `enforcement.session_id` equals the printed `session` | 1. dispatch the worker named for `enforcement.phase`; that dispatch belongs to the skill named in `enforcement.skill`, which is already loaded in this session. Also possible: `devforgeai validate` to re-check the fence and stack invariants. |
| `enforcement` is non-empty and `enforcement.session_id` differs from the printed `session`, or `session` is empty | 1. `devforgeai phase fail --reason "run orphaned by a closed session"`, then the command for `enforcement.skill` and `enforcement.arg` again. Also possible: nothing; no flag resumes a run whose session is gone. |
| `enforcement.attempts` for the active phase equals its `max_attempts` entry | 1. the same row as above for the session comparison, and read `.devforgeai/work/<run>/<phase>-report.md` for the problem rows the oracle recorded. |

The closed worker status set (`pass`, `fail`, `needs_user`, `could_not_run`) does not appear here because no worker returns one. `02-skill-roster.md`'s catch-all `could_not_run` row applies to skills that open a run.

## 8. Bundled resources

### Layout

```
status/SKILL.md             # <=500 lines: identity, the four-step loop, the outcome table
  references/output.md      # every field devforgeai status prints, what it means, who writes it
  references/limits.md      # what the block does not show today, and the entry that would change it
  assets/handoff.md         # the target block shape from 01-skill-anatomy.md
```

There is no `agents/` directory, no `scripts/` directory, and no `references/envelope.md`. This skill dispatches no worker and runs no script; section 9 records why a bundled renderer is excluded. There is no `README.md` inside the skill directory.

### scripts/

None. A script here would have to open `.devforgeai/state.yaml` or `.devforgeai/work/<run>/handoff.json` and render them, which makes a second reader of files the sequencer owns and a second answer to "what is next". `10-sequencer-and-contracts.md` section 6 rule 7 requires one rendering, and it is now in the one correct place: `render_handoff` in the sequencer, called by `phase next` when it writes the envelope and by `devforgeai status` when it prints one. A bundled script would be the second reader that rule exists to prevent.

### references/
| File | Content | Load when |
|------|---------|-----------|
| `output.md` | Every key `devforgeai status` prints: the `runs` map from canonical `state.yaml` with its five per-run fields and its four statuses; the enforcement fields from `.devforgeai/work/<run>/run.yaml` with the operation that writes each, including `candidate` and `lease`; the `next` key with the two operations that write it; and the `session` value with its source in `.devforgeai/sessions/`. Also the two-marker root rule: a `.devforgeai/` containing `run.yaml` means the working directory is inside a candidate root, and the canonical root is the path that file records | when a printed field needs explaining, in particular `candidate.root`, `candidate.checkpoint`, `lease`, `granted_keys`, `attempts` against `max_attempts`, and `gate_policy` |
| `limits.md` | What the block does not carry: the `handoff.json` fields the sequencer does not write today, so the renderer never prints them (`artifacts`, `source_basis`, `validation`, `decisions`, `repair_route`; `open_items` prints when present), the "You are here" progress line, the contents of a candidate root — the block names the root and the checkpoint, and shows no diff of what is inside it — Research run state, and per-window measurement | when the user asks for something the block does not show |

### assets/
| File | Used for |
|------|----------|
| `handoff.md` | the fuller "You are here" block shape from `01-skill-anatomy.md#handoff-template`, filed at `.devforgeai/skills/status/templates/handoff.md` in `11-artifact-registry.md` section 1. The sequencer's `render_handoff` is implemented and is what `status` prints; this shape is the documented target beyond it, and is an input to no current code path. |

### agents/
None. Section 7 declares no worker.

## 9. Gotchas and edge cases

| Situation | What goes wrong | What to do instead |
|-----------|-----------------|--------------------|
| The skill is expected to render `handoff.json` itself | It must not, and it no longer has to. `10-sequencer-and-contracts.md` section 6 rule 7 — the run-end block and the status block are one rendering of one file — is implemented as `render_handoff` in `docs/design/examples/hooks/devforgeai.py`. `devforgeai phase next` calls it when it writes the envelope; `devforgeai status` calls it over the envelope on disk, after the enforcement mapping and without writing anything: the active run's `work/<run>/handoff.json`, or with no run active the most recent `work/*/handoff.json` ordered by the envelope's own `at` and then by path. A missing or unreadable envelope prints nothing and the enforcement block is the whole output. | Print what the operation prints, which now includes the handoff block, and never hand-format one: a second renderer in the skill is the second answer to "what is next" that rule 7 exists to prevent. What the block carries is bounded by rule 8 — the renderer adds nothing — so it shows the envelope's `run`, `outcome`, `reasons[]`, `open_items[]` when present, and the one `next`. `artifacts`, `source_basis`, `validation`, `decisions` and `repair_route` are still absent because the sequencer does not write them yet, not because the renderer drops them; `references/limits.md` carries that list. |
| The user expects the "You are here" ASCII block | `01-skill-anatomy.md#handoff-template` shows that block, and `render_handoff` prints the envelope's own fields instead: `<run>  <outcome>`, the reason lines, any open items, and `Next: <command>`. The progress bar, the sprint line and the mode line have no field in `devforgeai.handoff/v1` to come from. | Ship `assets/handoff.md` as the documented target shape, with its note recording that `render_handoff` is implemented and this fuller shape is not, print the real output, and do not compose the block by hand: a hand-formatted block is the model asserting state, which is the one thing this skill exists to avoid. |
| `next: null` while a run is active | A model that wants to be helpful invents a forward command. `next` is written only at `phase next` and `phase fail`, so mid-run it is legitimately null, and the correct forward move depends on whether the session that opened the run is still alive. | Use the session comparison in the outcome table. Both mid-run rows are deterministic reads of printed values. |
| A stale enforcement block | The block is live only while `stories.<id>.status == in_dev` or `runs.<run>.status == active`. `devforgeai status` prints the mapping without consulting that status, so a crashed session can leave a block that looks live and denies every write. | Print the block and use the session comparison row. The escape is `devforgeai phase fail --reason`, which the user runs; status names it and does not call it, because R2 forbids status writing anything and that operation writes `handoff.json` and clears enforcement. |
| Calling `/status` from inside a phase worker | Most sequencer operations are refused there. This one is not: `dispatch.py` matches an exact `devforgeai status` and returns before the subagent branch. A spec that told a worker it cannot ask for state would be wrong. | Say plainly that a phase worker may call `devforgeai status` and nothing else, which is the same sentence `10-sequencer-and-contracts.md` section 2 uses. |
| A Research run is in progress | Research state lives in `docs/research/<slug>/` and `.devforgeai/research-staging/`, is written only by Research Core, and never enters `state.yaml`. `devforgeai status` prints nothing about it. | Say so in `references/limits.md` and point at `resume-run`, the Research Core operation that validates and returns an existing unsealed staging run. `SKILL-SPEC-018-research.md` owns that surface. |
| The user asks how many tokens the last run consumed | Neither provider exposes per-window accounting to a hook or a CLI, so the sequencer records nothing to print. | `12-post-mvp.md#pm-05` is the entry; `references/limits.md` names it and says the figure is not recorded today. |
| Two projects share one `devforgeai` on `$PATH` | The wrapper resolves relative to its own directory, and the sequencer resolves the project from `DEVFORGEAI_ROOT` or the working directory, so a link installed by one project still reports the repository the shell is in. A user who assumes otherwise mistrusts a correct answer. | State the resolution rule in `references/output.md`. Nothing needs to change in the skill. |
| Running `/status` before `/init` | `devforgeai status` exits 0 and prints the empty shape, so nothing signals that the framework is absent. If the wrapper is not on `$PATH` at all, the shell reports command-not-found instead. | Both are covered: the empty-shape row names `/init` first, and a command-not-found result means the same thing, because `SKILL-SPEC-004-init.md` makes the wrapper the thing `init` installs. |
| The user cannot find a file a run just wrote | Every write of an anatomy-governed run lands in that run's candidate root, `.devforgeai/work/<run>/wt`, which is gitignored; nothing reaches the working tree until a human runs `devforgeai promote <run>`, which never happens at Handoff and never happens on its own. A user looking in the working tree mid-run sees nothing and concludes the run did nothing. | The block prints `candidate.root` and `candidate.checkpoint` for the active run, and `runs.<run>.status`. Step 2 prints both verbatim, and `references/output.md` says what they mean: the root is where the file is now, the checkpoint is which phase's state it is at, and neither `status: active` nor `status: ready_to_promote` means promotion has happened — only `status: promoted` does. |
| A run sits at `ready_to_promote` | The run finished its phases and the working tree is unchanged — which looks identical to a run that failed. It is in fact the normal end of every run's phases, because promotion is never automatic, and it is also where a refused promotion leaves a run. | The `runs` map carries the state and the outcome table has a row for it: the pending step is `devforgeai promote <run>`, and when a promotion was already tried and refused the reason (`STALE_BASE`, `DIRTY_TARGET`, `MERGE_CONFLICT` — all refusals of that command, not of `devforgeai phase next`) is in that run's `handoff.json`, which the sequencer's own renderer prints after the enforcement block. Status prints the command and does not call it. |
| A blocked run rendered as if it were running, or as if it were gone | `needs_user` and an exhausted attempt budget leave the run `active`, so its enforcement block is still printed — and the UC-1 reading treated a non-empty `enforcement` as a live phase awaiting a dispatch. A user could not tell a blocked run from a running one, and OI-5 said no flag resumed anything | `10-sequencer-and-contracts.md` sections 2 and 3.1: a blocked run keeps `status: active`, releases its lease and records `run.yaml#blocked_at`. Section 6 now names `blocked_at` in the `run.yaml` Inputs row, says which two fields mark a blocked run, and renders one verbatim; UC-3 walks it; section 7 gains an outcome row keyed on `blocked_at` set with `lease` null whose pending step is `/<skill> <arg>`, the command that resumes the run in place with `attempts` reset; OI-5 now separates resuming a blocked run from the orphaned-session row, which keeps `devforgeai phase fail --reason`. |
| `ready_to_promote` described as the mark of a refused promotion | Section 6 and the section 7 operation and outcome rows all reached `ready_to_promote` through `STALE_BASE` or `DIRTY_TARGET`, so a reader took it for an error state and a clean finished run for something status would never show | Promotion is never automatic (`WRITE-MODEL-REVISION.md` D7, `10-sequencer-and-contracts.md` sections 5.4, 6 and 12.4): every run's phases end at `ready_to_promote`, and a refused promotion is only one way to be there. Section 6's "between runs" paragraph, the `devforgeai promote <run>` operation row and the `ready_to_promote` outcome row now say so, and name `devforgeai promote <run>` as the run's pending step rather than as a retry. |
| `ready_to_promote` had no rendered example | The output section showed only an `active` run and an empty repository, so an author could not tell what status prints for a finished, unpromoted run — and `enforcement: {}` alone reads like "no run" | Section 6 now carries the `ready_to_promote` block verbatim: the `runs` entry with its root, checkpoint and status, an empty `enforcement` because no phase is active and no lease is held, `next: devforgeai promote <run>`, and the `REQUIRE_HUMAN` envelope rendering under it. UC-3 walks the same case; the former UC-3 is UC-4. The run key is `clarify-STORY-007`, the `run_id()` shape for a document skill, and the envelope's reason lines are the ones `finish_run` in `examples/hooks/devforgeai.py` actually writes, so nothing here is invented. Section 6's Inputs row for `handoff.json` now also names `devforgeai promote <run>` as a writer, which is why a run has two envelopes. |
| "nothing reaches the working tree until the sequencer promotes the run at Handoff" | The "cannot find a file" row put the canonical write inside the Handoff sub-phase, which is the one thing the two-block model rules out | Nothing reaches the working tree until a human runs `devforgeai promote <run>`. The row says that, and its guidance no longer implies `status: active` is the only pre-promotion state — `ready_to_promote` is one too, and only `status: promoted` means the bytes moved. |
| Looking for the enforcement block in `state.yaml` | `10-sequencer-and-contracts.md#9-enforcement-block` no longer defines `state.yaml#enforcement`: the block now lives per run at `.devforgeai/work/<run>/run.yaml`, is gitignored, and is deleted with the candidate root at promotion or abandonment; `snapshot` is no longer one of its fields. | Read the block only through `devforgeai status`, which prints the run's `run.yaml` fields; sections 6, 7 and 8 already name that path, and `references/output.md` lists the fields the current section 9 defines. |
| A second window's write is denied while the block looks idle to it | The lease is bound at `SubagentStart` and is held by one producer at a time; a window that is not the lease holder is denied every write even though a run is legitimately active. | The block prints `lease` with its `session_id`, `agent` and `phase`, so the denial is explained by a printed value rather than guessed at. `references/output.md` states that judges hold no lease and may run concurrently against a checkpoint. |

### Cross-cutting open items

| ID | Resolution recorded here |
|---|---|
| OI-1 | Not applicable in a mechanical sense — status dispatches no worker — but recorded so no generated file invents one: Slice is a sequencer step inside `devforgeai phase start`, which writes `.devforgeai/work/<run>/context.json`, and status opens no run and so reaches no phase at all. |
| OI-4 | Status does not observe a worker's `fail`. It reports the attempt counters the sequencer wrote, and the outcome table's last row sends the reader to `<phase>-report.md` for the problem rows, which is where `examples/hooks/devforgeai.py` records the `"<agent> reported fail"` row. |
| OI-5 | Resuming is a command, not a flag, and status offers neither — it prints them. A run blocked by `needs_user` or an exhausted attempt budget stays `active` with `blocked_at` set, and `/<skill> <arg>` resumes it in place; status names that as the pending step. Its orphaned-run row is the different case, where the owning session is gone: there the row names `devforgeai phase fail --reason` followed by the skill's command. |
| OI-7 | Status invokes no other skill. Every command it prints is a command a human or a fresh session runs. |
| OI-10 | `/status` takes no positional argument and needs none: `devforgeai status` takes none either. The problem is confined to `devforgeai phase start`, which status never calls. Where the printed `next` carries an argument, it is the argument the sequencer recorded. |

## 10. Success criteria and test cases

### Success criteria

- Triggers on the section 4 positives and not on the near-misses.
- Exactly one command is run per invocation, and it is `devforgeai status`.
- No file is created or modified anywhere in the repository during an invocation, inside a candidate root or outside one. The skill declares no worker, so no compiled subagent file exists for it to dispatch.
- On the fixture state, the printed output contains `run: STORY-001`, `phase: red`, the three `write_fence` entries, the `runs` entry for the run with its `root`, `base_ref`, `checkpoint` and `status`, and the `candidate` and `lease` mappings.
- On a repository with no `.devforgeai/`, the reply names `/init` as the single forward command, whether the operation printed `enforcement: {}` or the shell reported that `devforgeai` could not be found.
- Where `next` holds a command, the reply's numbered forward command is that string character for character.
- The reply never contains a command that is absent from both the printed output and section 7's outcome table.

### evals/evals.json (used verbatim)

```json
{
  "skill_name": "status",
  "evals": [
    {
      "id": 1,
      "prompt": "New session here. What's the state of this project and what should I run?",
      "expected_output": "The enforcement block for STORY-001 at phase red, printed verbatim, plus the orphaned-run row: close the run with devforgeai phase fail --reason, then run /dev STORY-001 again.",
      "files": ["fixtures/status/active-run"],
      "expectations": [
        "exactly one shell command was run and it was devforgeai status",
        "the reply contains run: STORY-001 and phase: red",
        "the reply lists all three write_fence paths",
        "the reply notes that next is null and does not invent a forward command from memory",
        "the reply names devforgeai phase fail --reason as the way to close the orphaned run",
        "no file in the fixture was created or modified"
      ]
    },
    {
      "id": 2,
      "prompt": "What do I run next?",
      "expected_output": "An empty enforcement block and the recorded next value printed as the single numbered forward command.",
      "files": ["fixtures/status/idle"],
      "expectations": [
        "exactly one shell command was run and it was devforgeai status",
        "the reply contains enforcement: {}",
        "the numbered forward command equals the next value in the fixture state file character for character",
        "the reply presents exactly one numbered forward command",
        "no file in the fixture was created or modified"
      ]
    },
    {
      "id": 3,
      "prompt": "Where are we with devforgeai in this repo?",
      "expected_output": "The empty shape, and /init named as the single forward command because nothing is installed here.",
      "files": ["fixtures/status/uninstalled"],
      "expectations": [
        "the reply reports either the empty shape enforcement: {} with next: null, or that the devforgeai command could not be found",
        "the numbered forward command is /init",
        "the reply does not claim that a run is in progress",
        "no .devforgeai directory was created"
      ]
    }
  ]
}
```

Each eval uses its own base fixture directory; no eval edits a shared fixture, so no overlay directory is needed. The sequencer resolves the project from `DEVFORGEAI_ROOT` or the working directory, so a fixture that carries the sequencer beside its state file answers for itself.

| Fixture | Contents |
|---|---|
| `fixtures/status/active-run/` | `.devforgeai/state.yaml` copied from `docs/design/examples/hooks/fixtures/`, with `stories.STORY-001.status: in_dev` and the enforcement block for phase `red`; the `.devforgeai/stack.yaml` its `commands.source` anchors; and `.devforgeai/hooks/` carrying `devforgeai.py`, `policy.py` and the executable `devforgeai` wrapper, copied from `docs/design/examples/hooks/`, so `devforgeai status` resolves inside the eval workspace |
| `fixtures/status/idle/` | the same `.devforgeai/hooks/` payload, plus a `.devforgeai/state.yaml` whose `enforcement` is `{}` and whose `next` is `/review STORY-001` |
| `fixtures/status/uninstalled/` | a directory holding a single `.gitignore` and no `.devforgeai/` at all. Whether `devforgeai` resolves there depends on the harness: with the wrapper on the path the operation prints the empty shape and exits 0, and without it the shell reports command-not-found. Both readings route to `/init`, which is why eval 3's first expectation accepts either. |

Quick-mode results are generation feedback only: one enabled run per eval and no baseline. They are not runtime conformance evidence, and no section of this spec gates on such evidence; the deferred contract is `12-post-mvp.md#pm-02`.

## 11. Dependencies and compatibility

| Kind | Value |
|------|-------|
| Tools | SKILL.md: `Bash` limited to the single model-callable operation `devforgeai status`. No `Read`: this skill opens no file. No `Agent`: it dispatches no worker. The wider model-callable grammar `devforgeai status \| phase start <skill> <arg> \| phase fail --reason \| validate \| promote <run>` is the ceiling; status uses one of the five and names two more in its outcome table without calling them. It has no producer and no judge: nothing here writes, in a candidate root or anywhere else. |
| MCP servers | none |
| Runtime | The installed sequencer at `.devforgeai/hooks/devforgeai.py` and the `devforgeai` wrapper on `$PATH`, both installed by `init`. Python 3.11 or newer with `pyyaml`, which the sequencer requires. This skill bundles no script and imports nothing. |
| Project commands | None. `status` brokers no command key and names no build, test, lint or format command. It prints the `commands.source` and `commands.use` values the enforcement block already holds, which are a `stack.yaml` anchor and a list of key names, never a literal command. |
| DevForgeAI/Core compatibility | The sequencer in `docs/design/examples/hooks/` as of 2026-09-02, whose status operation prints the four-key mapping in section 6. Research Core version: NOT_APPLICABLE; status reports no Research state. |
| Other skills | Depends on `init` having installed the sequencer and the wrapper. Every other skill's handoff names `/status` as a reprint, so status is downstream of all of them and upstream of none. `11-artifact-registry.md` section 4 records both its Upstream and Downstream columns as `—`. |

### Deferred dependencies

| `PM-NN` | What status would use it for | What status does today without it |
|---|---|---|
| `12-post-mvp.md#pm-05` | Reporting the primary window's consumption per skill run from `provenance/log.jsonl`, so a primary-window regression is visible as a number | Prints no such figure and says in `references/limits.md` that none is recorded, because no provider event carries it. |
| `12-post-mvp.md#pm-10` | Reporting whether a clean checkout still validates, rather than only the active run's snapshot | Prints the active run's `candidate.checkpoint` and nothing about a fresh clone. |
| `12-post-mvp.md#pm-06` | An interactive generation mode with a review loop | Section 0 supports `skip` and `quick` only. |
| `12-post-mvp.md#pm-02` | Runtime conformance evidence for the generated adapters | Quick-mode eval results are generation feedback; no criterion in section 10 gates on runtime conformance. |

Frontmatter values derived from this table:

```yaml
compatibility: "Requires a repository where init has installed the DevForgeAI sequencer and the devforgeai wrapper is resolvable on PATH. Python 3.11+ with pyyaml, which the sequencer needs."
allowed-tools: "Bash"
```

## 12. Targets

The generator produces one provider-neutral semantic package and a separate adapter for each selected target when frontmatter, invocation policy, or agent configuration differs. Provider-neutral resources may be shared. Adapter directories are not required to be byte-identical or symlinked.

| Target | Install path | Invocation | Subagents | Notes |
|--------|--------------|------------|-----------|-------|
| claude | `.claude/skills/status/` | `/status`, no arguments | none | Provider-specific frontmatter keys (`argument-hint`, `disable-model-invocation`) are compiled into this target's SKILL.md only; `argument-hint` is empty because the command takes no argument. |
| codex | `.agents/skills/status/` | `$status`, no arguments | none | Portable six-field frontmatter only; policy goes in target-side configuration. |
| both | separate `.claude/skills/status/` and `.agents/skills/status/` adapters | as above | none | Share only provider-neutral resources; validate each adapter independently. Both reference files and `assets/handoff.md` are provider-neutral and are shared. |

```yaml
metadata:
  version: "1.0.0"
  devforgeai-spec: "SKILL-SPEC-017"
  devforgeai-target: "both"
  devforgeai-anatomy: "false"
```

Not produced by skill-creator (deferred to DevForgeAI's skill-generator): provider-specific frontmatter keys for the Claude target and concise `AGENTS.md` sections. There are no worker profiles to produce. Hook definitions are not per-skill: `init` installs the one dispatcher and its provider fragments from `09-hook-dispatcher.md`, and no spec ships its own. A generated package is an uninstalled candidate until those provider-native controls are present and independently validated. Generation or quick-mode success is not installation authority.

## 13. Constraints

- `SKILL.md` under 500 lines and roughly 5,000 tokens, holding only identity, the four-step loop, and the outcome table. Everything else lives in `references/output.md` and `references/limits.md`. This skill is expected to land well under the ceiling; the ceiling is not a target.
- References one level deep: `SKILL.md` links to `references/` and `assets/`. Nothing links further. There is no `agents/*.md` to link from.
- Hooks, state writes, and phase advancement are not in the skill. This skill writes nothing at all, which is the strongest form of that constraint.
- No `README.md` inside the skill directory.
- No XML angle brackets in frontmatter. Description max 1024 chars, name max 64.
- Imperative voice. Explain why; avoid all-caps ALWAYS/NEVER.
- Provide defaults, not menus: one command, one selected outcome row, one numbered forward command.
- No bundled script and no second parser of `.devforgeai/`. Section 8 and section 9 record the reason.
- Every command the skill prints comes from the printed output or from section 7's outcome table. A command assembled from conversation memory breaks handoff rule 4, which is the rule this skill exists to keep.

## 14. Acceptance checks

Run these before reporting done and paste their output:

```bash
# frontmatter and naming (skill-creator's own validator)
python -m scripts.quick_validate .devforgeai/skills/status      # run from the skill-creator directory
# open-standard validator, if installed
skills-ref validate .devforgeai/skills/status
# size budget
wc -l .devforgeai/skills/status/SKILL.md                        # must be < 500
# this skill declares no worker and no script: both directories must be absent
test ! -d .devforgeai/skills/status/agents && echo "no agents dir, as specified"
test ! -d .devforgeai/skills/status/scripts && echo "no scripts dir, as specified"
# two reference files, no envelope.md
ls .devforgeai/skills/status/references/
# one asset
ls .devforgeai/skills/status/assets/
# the only sequencer operation the body may name
grep -c 'devforgeai status' .devforgeai/skills/status/SKILL.md
grep -n 'devforgeai phase start\|devforgeai ingest-result\|devforgeai phase next\|devforgeai run\|devforgeai session-start' .devforgeai/skills/status/SKILL.md || echo "no other operation named"
# no leftover placeholders
grep -rnE 'T[O]DO|T[B]D|\{\{' .devforgeai/skills/status || echo clean
```

The wave-4 battery for this specification is:

```bash
python3 docs/design/specs/verify.py --only v1,v2,v4
```

The DevForgeAI `skill-validator` checks for anatomy skills — all sub-phase kinds present, persona and critic in different files, `must_not` and a `writes` declaration in every agent file — do not apply to `status`, which has no worker and therefore no agent file at all. What it does check here is that the `SKILL.md` Bash grammar is exactly `devforgeai status`, that no hook-only operation appears, that no `agents/` directory and no compiled profile exists for this skill, and that the outcome table covers every shape the printed output can take, including the empty one and the `ready_to_promote` one.

## 15. Provenance

| Source | Hash | Used for |
|--------|------|----------|
| `docs/design/10-sequencer-and-contracts.md#2-cli-grammar` | sha256:a20ea3c182031afa87dfe7a67fd57f04845ce083d255ee723202460651020066 | sections 7 (sequencer operations), 11, 13 |
| `docs/design/10-sequencer-and-contracts.md#9-enforcement-block` | sha256:4aa0d2e9acd265d11271008b3e5e748bbf34c4b2b9e5c624ad8dc8d6d9cebb02 | sections 2, 6 (output template), 8 (`references/output.md`) |
| `docs/design/10-sequencer-and-contracts.md#6-handoff-envelope` | sha256:de637edceb588df104a40b57738eb263989f6603f90ece6f4d0e64fef07ffb6a | sections 7 (step 4), 9 (the rendering gap) |
| `docs/design/10-sequencer-and-contracts.md#4-per-skill-phase-registry` | sha256:7d655abc79fb1789e37a57227eecc279faf035a0359ffa76e93b24b56796498e | sections 1, 7 (no phases) |
| `docs/design/01-skill-anatomy.md#state-file` | sha256:cec96cadc465f6269eaf0756ef40ff4299302e0754cd4cd887a2c44e50d4851d | sections 2, 6 (inputs) |
| `docs/design/01-skill-anatomy.md#handoff-template` | sha256:69eaf61097311ab55d3f940d03a4d1694e58658a11da3f41cd12a51d216b762a | sections 6 (assets template), 8, 9 |
| `docs/design/02-skill-roster.md#status` | sha256:8968e9247f9909e6289d81f659686f5a38eb79169c8a1ae9ce955537c5d01c1b | sections 2, 9 (the handoff.json claim) |
| `docs/design/02-skill-roster.md#handoff-decision-tables` | sha256:c0893be957755c72c7cd3f92ac38d90455ee02aec7ed2f672fbe8c6dc6ac142c | section 7 (handoff outcomes) |
| `docs/design/11-artifact-registry.md#4-upstream-and-downstream-per-skill` | sha256:cfcaef76005176490e96b9e67c8fa4f0b7a6a2e13b6badf856468881fbe25200 | sections 6 (outputs), 11 |
| `docs/design/05-subagent-sets.md#sets-per-skill` | sha256:9e12f3beb236a025c18d40e741c09ba675bd71d2d87f56e2b205c7556b944bf9 | sections 7 (no workers), 8 |
| `docs/design/12-post-mvp.md#pm-05` | sha256:67f35ed73777ffd7e03bb3e4b72cedf6057331e8f8033f6e2b7005f877edc591 | sections 9, 11 (deferred dependencies) |
