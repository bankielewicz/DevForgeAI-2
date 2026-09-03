---
template: skill-spec
template_version: 1
id: SKILL-SPEC-001
skill_name: dev
target: both
status: approved
author: "DevForgeAI plan skill"
date: 2026-09-02
depends_on:
  - source: docs/design/01-skill-anatomy.md#primary-window-contract
    hash: sha256:a6bbaf9af2d69f7ede18d7c40f242c42edb26d79be964ffec3f386d6347014c2
    excerpt: "For an anatomy-governed skill, the primary window (provider entry adapter + skill orchestration) does light, trivial work only. It dispatches workers and calls the sequencer. It never writes state, never advances a phase, and never decides that a phase passed."
  - source: docs/design/01-skill-anatomy.md#the-seven-sub-phases
    hash: sha256:b3c1a62145dc7fd7ef4fb351242f6b67bb0838da1c70cc359b679bfa4986e7d1
    excerpt: "Gate, Slice, Record, and Handoff are deterministic sequencer operations, not workers. Only Work, Write, and Review dispatch an LLM."
  - source: docs/design/10-sequencer-and-contracts.md#4-per-skill-phase-registry
    hash: sha256:511733ee35ca74fd5a5c0b59f225d7d975788e7d43d939f44c23b7aa8460cff0
    excerpt: "| dev | 1 | `red` | `red_dev` | tests | 2 | `test` | red | — |"
  - source: docs/design/10-sequencer-and-contracts.md#11-per-skill-evidence-and-gate-table
    hash: sha256:f5dc9ad016c382d9d033b25878267bd8e1ef240cb0ecaafeff33af16637e906e
    excerpt: "Every skill specification fills this table in its section 7, one row per phase, in phase order:"
  - source: docs/design/10-sequencer-and-contracts.md#3-4-re-resolving-sources-and-the-one-downgrade
    hash: sha256:722dadc1737749e30d244f222aaa1d8b845bc93f4a573b16f662719e58b49bcd
    excerpt: "The story gate re-resolves every `provenance[]` and `context[]` entry as well as `commands`."
  - source: docs/design/10-sequencer-and-contracts.md#5-4-transition-oracles
    hash: sha256:ffa41b5d270dc260e28fa9f6bdbc855069a6e922d1148c74b25860dba63484dc
    excerpt: "`red` | build first when the section is compiled; broker `test`; classification is not `NO_TESTS` or `COLLECTION_ERROR`; the command exits non-zero; every `test_plan` name is present and `failed`, never `error`; no test outside `test_plan`; records `red_hashes`"
  - source: docs/design/10-sequencer-and-contracts.md#6-handoff-envelope
    hash: sha256:747b6340fc5c2348aad33ca5488012808670b3503b311d7b7d0f1204625afd4c
    excerpt: "| story run, promoted | `/review <arg>` |"
  - source: docs/design/11-artifact-registry.md#2-artifact-path-patterns
    hash: sha256:2d2e97afff50edf6b35bf674b1de217c684d5091361e5f1deae12de52b95fb51
    excerpt: "`dev` has no document fence: its fence is the story's `write_fence`. `dev-notes` therefore exists only as evidence under `.devforgeai/work/<run>/` and as the rendered view above."
  - source: docs/design/02-skill-roster.md#handoff-decision-tables
    hash: sha256:1dac784b4670cc7559f323011dfe304dfe8c0baf349063162f90d76d902c5d3c
    excerpt: "| dev / dev-tdd | pass | `/review {story}` |"
  - source: docs/design/05-subagent-sets.md#worked-example-dev-tdd
    hash: sha256:66b4dd5370ee15bf1da2e4c790192943db299b150fd6fb56d9c58a92efefe32a
    excerpt: "smoke-qa failure sends the failing criterion back to green-implementer, not to red-tester. Tests are the contract; code moves to meet them."
  - source: docs/design/05-subagent-sets.md#sets-per-skill
    hash: sha256:9e12f3beb236a025c18d40e741c09ba675bd71d2d87f56e2b205c7556b944bf9
    excerpt: "| dev-tdd | red-tester, green-implementer, refactorer, smoke-qa, critic |"
  - source: docs/design/08-story-specification.md#what-a-story-must-carry-and-why
    hash: sha256:c8c466567a5e85ebcd61de29320f8c72f581f99a9b6e8d7dbd98e80f04861fcb
    excerpt: "Authoritative for the criterion-to-test mapping. Red writes exactly these tests; the critic detects a criterion with no test or a test with no criterion; the transition check asserts each named test is present with the expected outcome."
---

# Skill Specification: dev

A stranger with no conversation history must be able to build this skill from this document alone. Every question the generator would otherwise ask is answered below. No unresolved authoring assumption remains; every open item this specification inherited is resolved in writing in section 9.

`dev` is one skill with two worker-file variants. The registry knows one skill named `dev` with five phases; `dev-tdd` resolves to `dev` before the enforcement block is written, so the sequencer, the gate, the oracles and the handoff are identical for both. Section 7 gives both variants' worker contracts against the same five canonical worker names.

Every `dev` run works inside one candidate root. The sequencer creates it at `devforgeai phase start`, records its path and mode in the run file, and owns it until promotion or abandonment. The three producing workers — `red_dev`, `green_dev`, `refactor_dev` — write their files there with `Edit` and `Write` and run the phase's granted stack keys through `devforgeai run <key>`, which executes with the candidate root as its working directory. The two judging workers — `smoke_qa` and `dev_critic` — read the checkpoints and oracle output the sequencer recorded and change nothing in the root; each writes its findings file into its own run-scoped scratch under `.devforgeai/work/<run>/evidence/<agent>/`, which is gitignored and never promoted. Code reaches the canonical checkout only when the user runs `devforgeai promote <run>` on a run the last passing transition marked `ready_to_promote`; promotion is never automatic and is never part of Handoff.

Two `writes` vocabularies meet here and mean different things. The registry phase's mode — `tests`, `code`, `none`, `docs` — says what a phase may change inside the candidate root. The worker header's `writes` — `candidate`, `evidence` or `none` — says where that agent's tools may write at all. A judge is `writes: none` against the root and `writes: evidence` in its header, because its findings file lives outside the root.

## 0. Generator instructions

These instructions are addressed to the skill-generating agent (Anthropic's `skill-creator` skill, or DevForgeAI's `skill-generator`). They replace its interview.

### Cold-session prompt

Paste this into a fresh session from the repository root:

```
Use the skill-creator skill to build the skill specified in docs/design/specs/SKILL-SPEC-001-dev.md.
Follow its section 0 exactly. Output directory: ./out. Eval mode: quick.
Install the dev variant worker bodies from section 7e unless the invocation names the dev-tdd variant.
```

### Rules for the generator

1. **Do not interview.** Sections 1-13 pre-answer every Capture Intent and Interview question (what it enables, when it triggers, output format, test cases, edge cases, input/output formats, example files, success criteria, dependencies). Treat this document as the conversation history you are told to harvest from.
2. **Test prompts are pre-approved.** Use section 10 verbatim as `evals/evals.json`. Do not ask whether they look right.
3. **Trigger queries are pre-approved.** Use section 4 verbatim as the trigger eval set. Do not ask for sign-off.
4. **No human review loop.** Do not wait for the user to review results. Proceed to the next stage on your own.
5. **Eval mode** is given in the prompt and is one of two values:
   - `skip`: write the skill only. Do not create `evals/`, do not run test prompts, do not optimize the description.
   - `quick`: write the skill and `evals/evals.json`. Build each eval's workspace as section 10 specifies, run each test prompt once with the skill (no baseline run), grade with the grader agent, write `grading.json`, and report pass/fail per expectation in your final message. Do not run the description-optimization loop. Run the eval executions and the grader as foreground Agent-tool subagents, never as background shell processes, and do not end your turn until every `grading.json` exists: a headless session terminates when the top-level turn ends and orphans anything still running.
   - Any other mode name is a spec defect. The deferred interactive mode is `12-post-mvp.md#pm-06`.
6. **Output location** is given in the prompt. Create `<output-dir>/dev/`. Do not write anywhere else except the `dev-workspace/` sibling that eval runs require.
7. **On ambiguity, stop before output.** If the spec is still `draft`, contains an unresolved authoring assumption, omits a section, contradicts itself, or leaves a decision this document does not make, do not guess and do not write candidate skill files. End with a list titled `SPEC GAPS` naming each section and question. The spec author fixes and approves the spec before re-running.
8. **Fidelity over creativity.** Use the description in section 3 verbatim. Use the selected variant's worker contracts in section 7e verbatim as `agents/<role>.md` bodies, adding only the framing the grader agent in skill-creator uses (Role, Inputs, Process, Output). Use the phase guidance in section 7d verbatim as `references/<phase>.md`. Do not add steps, tools, or behaviours the spec does not mention.
9. **Finish with the acceptance checks** in section 14 and include their output in your final message.

## 1. Identity

| Field | Value |
|-------|-------|
| name | `dev` (kebab-case, 3 chars, equals the directory name, no `claude`/`anthropic` prefix) |
| title | Story Development |
| purpose | Turn one gated story into applied code and tests through five sequencer-checked phases, so the primary context window holds no artifact content and no phase advances on a worker's own say-so. |
| category | devforgeai-phase |
| version | 1.0.0 (skill-package version written to `metadata.version`; not the DevForgeAI or Research Core version) |

The `dev-tdd` variant is generated from this same specification when `docs/architecture/constitution.md#mandates` carries `tdd: required`. It installs different `agents/*.md` bodies at the same five canonical worker names and changes nothing the sequencer sees, so it has no separate identity row, no separate command, and no template of its own.

## 2. Problem and requirements

**Without this skill:** an agent handed a story reads the story, the constitution, the architecture documents and the existing source into one window, then writes tests and production code together in that same window. Four failure modes follow, each observed in `07-purpose-and-enforcement.md` section 2: it starts coding from the prompt rather than from the gated artifact (step-skip); it declares the story done because a file exists (checkbox completion); it edits a test until the test passes rather than the code; and the window fills with content it can no longer unload, so later phases reason over a stale mixture. There is no record of which acceptance criterion was never encoded as a test, because nothing outside the model ever checked.

| ID | Kind | Requirement |
|----|------|-------------|
| R1 | explicit | Take one story id as input and produce, inside that story's `write_fence`, the tests named by its `test_plan` and the production code that makes them pass. Source: `08-story-specification.md` "What a story must carry, and why". |
| R2 | explicit | Run `red`, `green`, `refactor`, `smoke` and `review` as five separate phases, each dispatching exactly one named worker in its own context window. Source: `10-sequencer-and-contracts.md` section 4 registry. |
| R3 | explicit | Refuse to start on a story that fails the story gate, and name in the handoff the skill that owns the failing artifact. Source: `01-skill-anatomy.md` gate outcomes table. |
| R4 | implicit | The primary window reads no artifact and writes no file: it parses the argument, calls the four model-callable operations, dispatches by path and id, and prints the handoff the sequencer rendered. Source: `01-skill-anatomy.md#primary-window-contract`. |
| R5 | implicit | No worker runs a raw build, test, lint or format command. A producer names a granted key through `devforgeai run <key>`, which the sequencer resolves from the hash-pinned `stack.yaml` section and executes in the candidate root; the same resolution runs again inside the transition oracle at ingest, and only that run decides the phase. Source: `10-sequencer-and-contracts.md` section 1 consequence 1, as revised by the write-model decisions D1 and D8a. |
| R6 | implicit | A test file frozen at `red` stays frozen: `green` and `refactor` may not edit a path in `test_paths`, and the oracle compares each test file's digest against `red_hashes`. Source: `10-sequencer-and-contracts.md` section 5.4 `green` row. |
| R7 | implicit | Every run ends with exactly one copy-pasteable next command, valid from a cold session. Source: `01-skill-anatomy.md#handoff-contract` rule 1 and rule 4. |
| R8 | discovered | A `green` or `refactor` worker that finds the criteria unbuildable rewinds to `red` rather than weakening a test: `status: fail` with `next: red`. The rewind costs an attempt at `red`, so the loop terminates in the attempt budget. Source: `10-sequencer-and-contracts.md` section 5.4 outcomes table. |
| R9 | discovered | `smoke` failure returns to `green`, not to `red`: tests are the contract and code moves to meet them. Source: `05-subagent-sets.md#worked-example-dev-tdd` loop rules. |
| R10 | discovered | The two variants differ only in the worker prompt bodies. Both run the same five phases against the same three test oracles, so a project that does not mandate TDD still gets a test-first sequence enforced by the `red` oracle. Source: `10-sequencer-and-contracts.md` section 4 variant note. |
| R11 | discovered | Every write of the run lands in the candidate root the sequencer opened, never in the canonical checkout, and reaches canonical only when the user runs `devforgeai promote <run>`, which the sequencer performs as a fast-forward under its lock. Promotion is never automatic: the last passing transition only marks the run `ready_to_promote` and writes a `REQUIRE_HUMAN` handoff naming that command. A promotion that cannot fast-forward is refused with `STALE_BASE` or `DIRTY_TARGET` rather than merged. Source: write-model decisions D2 and D7 as amended. |
| R12 | discovered | A judging worker records its findings as a file under `.devforgeai/work/<run>/evidence/<agent>/` and names it in the receipt's `evidence_refs`; `issues[]` stays the bounded summary the handoff and the reports quote. That scratch is gitignored, is outside the candidate root and the fence, and is never promoted. Source: write-model decisions D1, D6 and D8a as amended. |
| R13 | discovered | One producer holds the run's lease at a time. The sequencer grants it at dispatch, the hook layer binds it at `SubagentStart`, and `ingest-result` releases it; a write tool call from any other agent is denied. Judges hold no lease. Source: write-model decisions D3 and D6. |

## 3. Description

The exact frontmatter `description`. Written as a YAML block scalar so colons are safe; no angle brackets anywhere.

```yaml
description: >
  Implement one DevForgeAI story: dispatch the red, green, refactor, smoke and
  review workers while the devforgeai sequencer gates the story, checkpoints
  each phase in the candidate root, runs the test oracle and renders the
  handoff. Use this skill
  whenever someone asks to implement, build, code, finish or fix a story,
  ticket or STORY-NNN file, asks for the next story in a sprint, says to write
  the failing tests first or to do red green refactor, or asks to redo work
  that qa or review sent back. Use it too when a story's frontmatter names
  requires_skill dev or dev-tdd, or the project constitution mandates
  test-driven development. Do NOT use it to write or split stories (use plan),
  to review a diff against the constitution (use review), to run acceptance
  criteria and regressions (use qa), or to resolve an ambiguous criterion (use
  clarify).
```

Character count: 848 / 1024.

## 4. Trigger set

Realistic queries, varied in phrasing, explicitness, detail and complexity. The near-misses share vocabulary with `dev` and belong to an adjacent skill. The generator uses this list verbatim.

```json
[
  {"query": "/dev STORY-012", "should_trigger": true},
  {"query": "implement docs/plan/shop/stories/STORY-004.md please, everything upstream is signed off", "should_trigger": true},
  {"query": "next story in sprint-002 is STORY-015, the rate limiter. get it coded the way our constitution wants", "should_trigger": true},
  {"query": "qa knocked back STORY-007 on criterion 2, can you go round again on just that one", "should_trigger": true},
  {"query": "can you tdd this one for me? docs/plan/api/stories/STORY-002.md, red green refactor, dont touch anything else", "should_trigger": true},
  {"query": "the story frontmatter says requires_skill: dev-tdd, go ahead", "should_trigger": true},
  {"query": "write the failing tests for STORY-009 first and then make them pass", "should_trigger": true},
  {"query": "pick up ticket STORY-021 from docs/plan/billing/stories and code it, we do tests first here", "should_trigger": true},
  {"query": "build the slugify helper described in STORY-001 in the tinyapp fixture", "should_trigger": true},
  {"query": "review the diff for STORY-004 against the constitution before I open a PR", "should_trigger": false},
  {"query": "run every acceptance criterion for STORY-004 and collect the evidence", "should_trigger": false},
  {"query": "re-run the failing tests for STORY-004 and tell me which criteria are still red", "should_trigger": false},
  {"query": "write me a story file for adding a slugify helper with three acceptance criteria", "should_trigger": false},
  {"query": "criterion 3 of STORY-011 is ambiguous, ask me the questions you need answered", "should_trigger": false},
  {"query": "split EPIC-003 into stories and put them in sprint-002", "should_trigger": false},
  {"query": "quick python script to rename all the .jpeg files in my photos folder to .jpg, no tests needed", "should_trigger": false},
  {"query": "explain what red green refactor means, my team keeps saying it", "should_trigger": false},
  {"query": "our tests are flaky in CI, figure out why test_text.py fails randomly", "should_trigger": false},
  {"query": "generate a tdd skill for this project from the constitution mandates", "should_trigger": false}
]
```

## 5. Use cases

### UC-1: The next story in the sprint
- **User says:** "/dev STORY-001"
- **Steps:** 1. The adapter calls `devforgeai phase start dev STORY-001`; the inlined story gate re-resolves every `provenance[]`, `context[]` and `commands` reference, checks template v3, `status: ready`, the `blocked_by` chain, the fence, the `test_plan` rows and the stack section, opens the candidate root at the pinned base, registers the run and opens phase `red`. 2. The adapter dispatches `red_dev` with the `devforgeai status` block, which names the run, the candidate root, the phase, the fence and the granted keys; `red_dev` writes the `test_plan` files inside that root and runs `devforgeai run test` while it works. 3. `SubagentStop` routes the receipt to `devforgeai ingest-result`; the sequencer derives the changed set from the checkpoint diff, checks it against `claimed_paths` and the fence, brokers `test`, confirms the suite is red for exactly the planned tests, records `red_hashes`, creates the `red` checkpoint, releases the lease and advances. 4. `green_dev` writes production code in the same root; the oracle re-runs `test` and requires every planned test `passed` with no test file touched. 5. `refactor_dev` changes structure; the oracle adds `lint`. 6. `smoke_qa` maps each criterion to the recorded result, writing nothing. 7. `dev_critic` reports coverage defects, writing nothing. 8. The sequencer marks the run `ready_to_promote` and renders a `REQUIRE_HUMAN` handoff whose one forward command is `devforgeai promote STORY-001`. 9. The user confirms the promotion in the session; the adapter runs that command, the sequencer fast-forwards the candidate into the canonical checkout under its lock, and the second handoff block names `/review STORY-001`.
- **Result:** `tests/test_text.py` and `tinyapp/text.py` in the canonical checkout after the user promoted the run, five result and report pairs under `.devforgeai/work/STORY-001/`, `stories.STORY-001.status` and the run's `promoted` status in `state.yaml`, and two handoff blocks: the first naming `devforgeai promote STORY-001`, the second, written by that command, naming `/review STORY-001`.

### UC-2: QA sent the story back
- **User says:** "/dev STORY-007 --fix"
- **Steps:** 1. `--fix` opens a fresh run from phase 1; it does not resume the closed one. 2. The adapter passes `docs/reports/qa-STORY-007.md` to each worker as an extra input path, so `red_dev` tightens only the tests for the criteria that report marks failed and `green_dev` changes only the code those tests reach. 3. The remaining phases run unchanged.
- **Result:** the previously failing criteria are green, the run's evidence is a second directory generation under the same run id, and the handoff names `/review STORY-007`.

### UC-3: The story is not ready
- **User says:** "implement STORY-011"
- **Steps:** 1. `devforgeai phase start dev STORY-011` runs the story gate and finds `ASSUMPTION:` in the body outside `## Clarifications`, or a `context[]` digest that no longer matches its source. 2. The sequencer exits 1 with the defect list on stderr and opens no run, so no candidate root is created and no worker is dispatched. 3. The adapter prints the defect list and the matching row from its handoff table.
- **Result:** no file changed anywhere, and the next step is `/clarify STORY-011` for an assumption or `/plan {slug} --reslice STORY-011` for a stale digest.

## 6. Inputs and outputs

### Inputs
| Input | Format | Example file | Required |
|-------|--------|--------------|----------|
| story id | positional argument matching `^STORY-(HOTFIX-)?[0-9]{3}$` | `STORY-001` | yes |
| story | markdown, `story` template v3, owned by `plan` | `docs/design/examples/fixtures/dev-tdd/STORY-001.md` | yes; resolved by the sequencer, never read by the primary window |
| `.devforgeai/state.yaml` | YAML | `docs/design/examples/hooks/fixtures/.devforgeai/state.yaml` | yes; the sequencer reads it, the adapter reads only what `devforgeai status` prints |
| `.devforgeai/stack.yaml` section | YAML, anchored by `commands.source` and pinned by `commands.hash` | `docs/design/examples/hooks/fixtures/.devforgeai/stack.yaml` | yes |
| `--fix` flag | boolean | | no |
| qa report | markdown, `qa-report` template, only with `--fix` | `docs/reports/qa-STORY-001.md` | with `--fix`, when one exists |
| review report | markdown, `review-report` template, only with `--fix` | `docs/reports/review-STORY-001.md` | with `--fix`, when one exists |
| clarifications | the story's `## Clarifications` section, appended by `clarify` | inside the story file | no |
| `--lenient` flag | boolean, forwarded to `devforgeai phase start` | | no; refused for any story under `docs/plan/` |

### Outputs
| Output | Format | Location | Template |
|--------|--------|----------|----------|
| tests | project language, one file per distinct `test_plan.file` | the story's `test_paths`, inside `write_fence`, written in the candidate root and reaching the canonical checkout by promotion | none; the `test_plan` rows are the contract |
| production code | project language | `write_fence` paths that are not `test_paths`, in the candidate root until promotion | none |
| phase result | JSON, the validated envelope plus the sequencer's added fields | `.devforgeai/work/<story>/<phase>-result.json` | none; written by the sequencer |
| phase report | markdown | `.devforgeai/work/<story>/<phase>-report.md` | `assets/dev-notes.md` (`dev-notes`, owned by `dev`) |
| rendered report view | markdown | `docs/reports/dev-<story>-<phase>.md` | `dev-notes` |
| handoff | JSON plus its printed rendering | `.devforgeai/work/<story>/handoff.json` | `handoff`, rendered by the sequencer |

Evidence lives outside the candidate root, in the canonical checkout's gitignored `.devforgeai/work/<run>/`, and the sequencer is its only writer. A receipt's `evidence_refs` entry is therefore either a path under the candidate root or a path under `.devforgeai/work/<run>/`.

`dev` owns exactly one template, `dev-notes`, at `.devforgeai/skills/dev/templates/dev-notes.md`; `11-artifact-registry.md` section 1 records `review`, `qa` and `retro` as its consumers. `dev` consumes `story`, `epic`, `constitution`, `sourcetree`, `techstack`, `architecture`, `design`, `stack`, `clarification`, `qa-report` and `review-report`, every one of which has a producer in that registry. For a story run the run id is the story id, so the rendered view path in `11-artifact-registry.md` section 2 (`docs/reports/dev-<story>-<phase>.md`) and the sequencer's general form (`docs/reports/<skill>-<run>-<phase>.md`) resolve to the same file.

### Output template

The `dev-notes` shape, which `assets/dev-notes.md` seeds and the sequencer's phase report fills:

```
---
story: STORY-NNN
phase: red | green | refactor | smoke | review
template: dev-notes
template_version: 1
status: pass | fail | needs_user | could_not_run
run: STORY-NNN
---

## Note

One to three lines from the worker envelope's `note`.

## Issues

- NOTE-001 kind text          (at most ten rows, one line each)

## Files

- path the phase changed inside the write fence, with its blob digest and kind, as the sequencer derived them from the checkpoint diff

## Oracle

- classification and the problem rows the transition oracle produced
```

### Return envelope (DevForgeAI-anatomy skills only)

One schema, both providers: `devforgeai.worker-result/v1`, normative in `schemas/devforgeai/v1/worker-result.schema.json`. A worker's final message is exactly this one JSON object — a receipt for work it has already done in the candidate root, not a proposal. The sequencer derives what actually changed from the checkpoint diff; the receipt only claims the paths the worker meant to touch.

```yaml
schema: devforgeai.worker-result/v1
run: "STORY-001"
skill: "dev"
phase: "red | green | refactor | smoke | review"
agent: "red_dev | green_dev | refactor_dev | smoke_qa | dev_critic"
status: pass | fail | needs_user | could_not_run
reason_code: runner_missing | timeout | network | hook_fault   # required only when status is could_not_run
candidate: {id: "STORY-001", input_checkpoint: "red | green | refactor | base"}
claimed_paths: ["tinyapp/text.py"]      # root-relative, at most 64; empty for any non-pass status
evidence_refs: [".devforgeai/work/STORY-001/red-report.md"]   # at most 16
note: "at most three lines"
issues: [{id, kind, text}]              # at most 10
next: "red"                             # optional; only with status fail, only from green or refactor
```

`gate_policy` (`BLOCK | REQUIRE_HUMAN | WARN | OFF`) is a defect-to-action map declared in the consumed story, never a status returned here. An unknown key is refused, as is a `next` value from a phase that declares no `rewind_to`. A judging phase returns the same object with an empty `claimed_paths`: its findings file lives under `.devforgeai/work/<run>/evidence/<agent>/`, outside the candidate root and outside the fence, so it is never part of `changed`, and the receipt reaches it through `evidence_refs`.

## 7. Procedure

The body of `SKILL.md` is section 7a plus the phase list and the handoff table. Section 7d becomes `references/<phase>.md`, one file per registry phase. Section 7e becomes `agents/<role>.md`, one file per worker.

### 7a. Steps

1. Parse the story id, `--fix` and `--lenient` from the invocation. Nothing else is parsed and nothing is read — why: the primary window persists for the whole run, so every byte read here is carried through all five phases and cannot be unloaded.
2. Run `devforgeai phase start dev <story-id>`, appending `--lenient` only when the user supplied it. Exit 0 opens the run, creates the candidate root and prints the run id, the candidate root, the active phase, the fence and the granted keys; exit 1 is a gate refusal with the defect list on stderr; exit 2 is a usage error; exit 3 is a missing runner — why: the gate is inlined in this one operation, so there is no way to open a phase without it, and the root exists before any worker can be dispatched into it.
3. On a non-zero exit, print the sequencer's message and the matching row from the handoff table in section 7f, then stop. Do not retry and do not repair the story — why: the gate refuses on the producing skill's artifact, and repair belongs to the skill that owns the template.
4. Dispatch the worker the sequencer named, in its own context window. Paste the `devforgeai status` block into the prompt — it names `run`, `candidate.root`, `phase`, `fence` and `granted_keys` — and add the story id and the path of any extra input this run carries (`docs/reports/qa-<story>.md` and `docs/reports/review-<story>.md` under `--fix`, and the previous phase's report path from phase 2 onward). Pass paths and ids only — why: restating a goal or a criterion into a worker prompt replaces the gated artifact with a paraphrase, and the status block is the one place the root and the granted keys are stated, so a worker never guesses where it may write.
5. Read the worker's returned receipt and branch on `status` alone. `pass` and `fail` continue to step 6; `needs_user` and `could_not_run` continue to step 7 — why: by the time this branch runs the sequencer has already diffed the checkpoint, run the oracle, written the checkpoint and released the lease, so the status is a report of a decision already made, not the decision.
6. Run `devforgeai status` and read `enforcement.phase`, or treat an empty enforcement block as a closed run. That value is the next phase on an advance, the same phase on a retry, and `red` after a rewind. Dispatch the worker for that phase and repeat from step 4 — why: the sequencer's `SubagentStop` message names the same phase, but the enforcement block is the record it wrote, so reading it works identically on both providers and after a session restart, and the attempt counters, the limits and the lease that bound the loop live in the run file beside it.
7. Print the handoff block the sequencer rendered, verbatim. When the run closed without a handoff because the gate refused before it opened, print the sequencer's stderr and the section 7f row instead — why: rule 8 of the handoff rendering rules forbids the renderer from adding a fact the envelope does not hold, and the same rule binds the adapter that prints it.
8. When the user abandons the story mid-run, call `devforgeai phase fail --reason <text>` so the run is closed with a `BLOCK` handoff rather than left active — why: a run left active refuses the next `devforgeai phase start` for every skill, and its candidate root stays on disk holding the lease.
9. Run `devforgeai promote <run>` only after the printed handoff says the run is `ready_to_promote` and the user has confirmed the promotion in this session, then print the second handoff block that command renders — why: promotion is never automatic. The last passing transition marks the run `ready_to_promote` and writes a `REQUIRE_HUMAN` handoff whose only forward step is this command, so whether the candidate's bytes reach the canonical checkout is the user's decision and not the sequencer's.

Bash grammar for this skill is exactly `devforgeai status`, `devforgeai phase start dev <story> [--lenient]`, `devforgeai phase fail --reason <text>`, `devforgeai validate` and `devforgeai promote <run>`. `devforgeai session-start`, `devforgeai ingest-result`, `devforgeai phase next`, `devforgeai run <key>` and the `devforgeai candidate` operations are hook-only and refuse a call that carries no `DEVFORGEAI_HOOK_EVENT` marker. A worker's `devforgeai run <key>` call is the one exception the hook layer admits: it is allowed to the lease holder, for a key the phase granted, with the candidate root as its working directory.

### 7b. Sub-phases and workers

Gate, Record and Handoff dispatch no LLM: they are `devforgeai` sequencer operations. Slice dispatches none either, for the reason recorded in section 9.

| # | Sub-phase | Performed by | Writes |
|---|-----------|--------------|--------|
| 0 | Gate | sequencer: `devforgeai phase start dev <story>`, which also opens the candidate root and registers the run | sequencer |
| 1 | Slice | no worker; the story's `context[]` bundle is the slice, produced by `plan` and re-resolved at the gate | none |
| 2 | Work: `red` | worker: `red_dev` | candidate |
| 3 | Work: `green` | worker: `green_dev` | candidate |
| 4 | Work: `refactor` | worker: `refactor_dev` | candidate |
| 5 | Work: `smoke` | worker: `smoke_qa` | evidence |
| 6 | Review | worker: `dev_critic` | evidence |
| 7 | Record | sequencer: `devforgeai phase next` at every transition, which checkpoints the root | sequencer |
| 8 | Handoff | sequencer: `devforgeai phase next`, or `devforgeai phase fail`. A passing last transition marks the run `ready_to_promote` and renders the first block, a `REQUIRE_HUMAN` handoff naming `devforgeai promote <run>`; `devforgeai promote <run>`, run only after the user asks for it, renders the second | sequencer |

`dev` has no Write sub-phase distinct from Work: its output is code and tests inside the story fence, written by the Work workers in the candidate root, so there is no writer rendering findings into a document template. Each worker runs as its own provider-native subagent, which is what gives the phase its own context window; runtime verification that it did is `12-post-mvp.md#pm-01`.

Promotion is not part of Handoff. The last passing transition sets `runs.<run>.status: ready_to_promote` and writes a `REQUIRE_HUMAN` handoff whose one forward command is `devforgeai promote <run>`; the candidate root and every checkpoint stay on disk and no canonical byte moves. The compiled `SKILL.md` runs that command only after the user confirms in the session, and the sequencer then performs it under `.devforgeai/lock`:

- The promotion succeeds: `git merge --ff-only devforgeai/<run>` in the canonical checkout, in worktree mode; in copy mode, the changed paths' exact bytes are copied into the canonical tree and the candidate's deletions are applied. The run's status becomes `promoted`, and the second handoff block names `/review <story>`.
- Canonical `HEAD` has moved since `base_ref`: `devforgeai promote <run>` is refused with `STALE_BASE`. In worktree mode the sequencer rebases the root onto the new `HEAD`, re-runs the last transition oracle and retries the fast-forward; a rebase conflict aborts to `needs_user` with `MERGE_CONFLICT`. In copy mode `STALE_BASE` is `needs_user`. The run stays `ready_to_promote`, so the command can be run again once the divergence is settled.
- A canonical file is dirty and is among the candidate's changed paths: `devforgeai promote <run>` is refused with `DIRTY_TARGET`, and nothing is copied.
- The run ended `REQUIRE_HUMAN` on an exhausted attempt budget or a `needs_user` result: it never reached the last passing transition, so it keeps `status: active` with its lease released and is not promotable at all. The root stays on disk for inspection, and `devforgeai phase fail --reason <text>` is what abandons it.

Variant role names map onto the canonical worker names as follows. The canonical name is what `agent_type` is compared against at result validation, so it is the name used in the evidence table, in the contracts and in the `agents/` filenames.

| Registry phase | Canonical worker | `dev` role (`05-subagent-sets.md`) | `dev-tdd` role (`05-subagent-sets.md`) |
|---|---|---|---|
| `red` | `red_dev` | test-writer | red-tester |
| `green` | `green_dev` | implementer | green-implementer |
| `refactor` | `refactor_dev` | implementer, structure-only pass | refactorer |
| `smoke` | `smoke_qa` | smoke-qa | smoke-qa |
| `review` | `dev_critic` | critic | critic |

### 7c. Evidence and gate table

One row per registry phase, in phase order. The story gate in row 1 runs once, at `devforgeai phase start`, and its checks bind every later phase through the enforcement block it writes.

| phase | worker | deterministic gate check | gate_policy | evidence file | transition oracle |
|---|---|---|---|---|---|
| `red` | `red_dev` | story is `template_version: 3` and `status: ready`; no `ASSUMPTION:` before `## Clarifications`; every `blocked_by` story is `done`; every `provenance[]` and `context[]` entry re-resolves to its recorded digest; `write_fence`, `test_plan` and `commands` present; every `test_plan` row has criterion, file and name and its file is inside the fence; no fence entry is sequencer-owned; `commands.source` exists and `commands.hash` equals the current `stack.yaml` digest; the anchored section satisfies the `stack.yaml` contract; the existing tree already passes the package and import policy; the story's `write_fence` overlaps no active or `ready_to_promote` run's fence (`FENCE_OVERLAP`); at ingest the sequencer derives `changed` from the `base` checkpoint diff and requires it to be a subset of `claimed_paths` (`UNCLAIMED_CHANGE`) and every entry to be a `test_paths` entry (`writes: tests`) | `unresolved_assumption: BLOCK`, `stale_hash: BLOCK`, `unresolvable_source: BLOCK` (downgraded to a recorded warning only by `--lenient` on a story outside `docs/plan/`, or by `WARN`/`OFF` on a `scope: hotfix` story), `criterion_without_test: BLOCK` | `.devforgeai/work/<story>/red-result.json`, `.devforgeai/work/<story>/red-report.md` | `red`: fence held, stack policy held, `test` exited non-zero, classification is neither `NO_TESTS` nor `COLLECTION_ERROR`, every `test_plan` test present and `failed` rather than `error`, no test outside `test_plan`; records `red_hashes`, classifies `EXPECTED_TEST_FAILURE` and creates the `red` checkpoint. On a `--fix` run the oracle is narrowed rather than relaxed: the sequencer reads the failed-criteria list from the `qa` or `review` report the story's `context[]` bundle names, and requires the `test_plan` tests for exactly those criteria — plus any test the run newly added — to be `failed`, and every other `test_plan` test to be `passed`. A fix run whose narrowed set is empty is a defect, because there is nothing to fix |
| `green` | `green_dev` | the lease named in the run file is the dispatched agent's, so a write from any other agent is denied before it reaches disk (`LEASE_HELD`); `changed`, derived from the `red` checkpoint diff, is a subset of `claimed_paths`, lies inside `write_fence`, and contains no `test_paths` entry (`writes: code`); the whole-tree package and import policy scan over the root finds no denied package, no package outside `packages.allow` and no forbidden import for a changed path | `write_fence_violation: BLOCK`, `test_runner_missing: REQUIRE_HUMAN` | `.devforgeai/work/<story>/green-result.json`, `.devforgeai/work/<story>/green-report.md` | `green`: fence held, stack policy held, every `test_paths` digest equals `red_hashes`, `build` first when the section is compiled, every `test_plan` test `passed` and the classification is not `TEST_FAILURE`. `status: fail` with `next: red` resets the root to the `red` checkpoint instead |
| `refactor` | `refactor_dev` | as `green`, and the run's `commands.use` authorises the `lint` key the phase grants and the oracle brokers | `write_fence_violation: BLOCK`, `test_runner_missing: REQUIRE_HUMAN` | `.devforgeai/work/<story>/refactor-result.json`, `.devforgeai/work/<story>/refactor-report.md` | `refactor`: everything `green` checks, plus `lint` exits zero when the run authorises the key. `status: fail` with `next: red` resets to the `red` checkpoint instead |
| `smoke` | `smoke_qa` | `writes: none` against the root: `claimed_paths` is empty and the `refactor` checkpoint diff shows nothing changed since it; the worker holds no lease, so a write tool call inside the root is denied at `PreToolUse`, while a write under `.devforgeai/work/<story>/evidence/smoke_qa/` is admitted and is not part of `changed` | `test_runner_missing: REQUIRE_HUMAN`, which cannot fire here because the phase's `report_only` oracle spends no key | `.devforgeai/work/<story>/smoke-result.json`, `.devforgeai/work/<story>/smoke-report.md` | `report_only`: nothing changed in the root since the `refactor` checkpoint and the whole-tree package and import policy holds |
| `review` | `dev_critic` | as `smoke`, with its own scratch at `.devforgeai/work/<story>/evidence/dev_critic/`; the phase grants no command key, so `devforgeai run` is refused for this worker on the key as well as on the lease | `criterion_without_test: BLOCK` | `.devforgeai/work/<story>/review-result.json`, `.devforgeai/work/<story>/review-report.md`, then `.devforgeai/work/<story>/handoff.json` | `report_only`: as `smoke`. On pass this is the last phase: the run is marked `ready_to_promote`, enforcement is cleared, and the first handoff block names `devforgeai promote <run>`; the second block, written by that command after the user asks for it, names `/review <story>` |

Attempt budgets are `red: 2`, `green: 3`, `refactor: 2`, `smoke: 2`, `review: 2`, materialised into `enforcement.max_attempts` at the gate. A rewind from `green` or `refactor` costs an attempt at `red`, so the loop terminates: the budget is exhausted and the run hands off to a human with `REQUIRE_HUMAN`.

The five phases build linearly on one root: `base` → `red` → `green` → `refactor`, with `smoke` and `review` reading the `refactor` checkpoint and changing nothing. No merge exists between phases by construction. The lease is granted to a producer at dispatch, bound at `SubagentStart` to the agent identity the provider supplies, and released at `ingest-result`; `smoke` and `review` hold none and may read a checkpoint while nothing else is writing, because their own writes land in a per-agent scratch outside the root. Granted keys are `test` at `red`, `test` and `build` at `green`, `test`, `build` and `lint` at `refactor`, `test` at `smoke` and none at `review`. The `smoke` grant is inert: its oracle is `report_only`, which spends no key, and `smoke_qa` carries no `devforgeai run` surface, so nothing in the phase can spend it. The two judging phases read the oracle output the sequencer wrote rather than running anything.

Two honest limits bind every row. Every `devforgeai phase start` defect is a refusal whatever the story's declared value says, with the single downgrade in `10-sequencer-and-contracts.md` section 3.4; only `test_runner_missing` changes behaviour, and only at transition time, where `WARN` or `OFF` relabels the handoff outcome without continuing the run.

### 7d. Phase guidance

One subsection per registry phase. Each becomes `references/<phase>.md` verbatim, loaded when that phase's worker is dispatched. `references/envelope.md` carries the envelope shape from section 6 and is loaded on every dispatch. Where a paragraph is marked for one variant, the generator keeps only the paragraph for the variant it installs.

#### references/red.md

The `red` phase turns the story's `test_plan` into failing tests and nothing else. You write those files inside the candidate root the status block names, using `Edit` and `Write`, and you run `devforgeai run test` whenever you need to see the suite; the transition oracle runs it again at ingest, and that run is what advances the phase.

- The `test_plan` rows are the contract, not a suggestion. Write exactly one test per row, at the row's `file`, with the row's `name`. A row without a test is `criterion_without_test` at the oracle; a test that no row names is "tests outside test_plan" and fails the transition just as hard, because an unplanned test can pass and mask an unimplemented criterion.
- Each test fails on its own assertion. A test that fails because the module does not import yet is classified `error`, not `failed`, and the oracle rejects it — an import error proves nothing about the criterion. Where the target name does not exist yet, resolve it at call time (a lookup that asserts the name is present, then calls it) so the failure is an assertion about behaviour.
- Read the story's `## Acceptance Criteria`, `## Interface`, `## Unchanged Behaviour` and `## Out of Scope` sections, and the `context[]` excerpts for the testing conventions. The excerpts are verbatim slices with anchors and digests; treat them as the source, because opening the document they came from reintroduces the drift the digest exists to detect.
- Write only inside `test_paths`, and list every path you touched in the receipt's `claimed_paths`. The `writes: tests` mode is checked at ingest against the diff the sequencer takes, so a production file changed here fails the phase whether or not the receipt admits it, and a changed path the receipt does not claim is `UNCLAIMED_CHANGE`.
- Do not read the production file you expect `green` to change beyond the signature the story's `## Interface` section states. A test written against the implementation rather than the criterion is the failure this phase exists to prevent.
- Under `--fix`, the qa report and review report paths are inputs, whichever of the two exists: `qa` routes here on `verdict: fail` and `review` routes here on `verdict: findings`, so a `--fix` run after a review with no qa run yet has only the review report. Tighten or add tests only for the criteria the qa report marks failed and the findings the review report raises, and leave every other planned test byte-identical, because the oracle compares digests, not intentions.
- The `--fix` oracle is the plain `red` oracle narrowed to that same list, and the sequencer reads the list from the report itself rather than from anything you say: the tests for the criteria the report marks failed, plus any test this run newly added, must be `failed`; every other `test_plan` test must be `passed`. That is the opposite of a plain run, where every planned test must fail, and it is what makes a fix run possible against promoted code that already satisfies most of the story. Weakening an already-green test to make it fail is therefore a transition failure, not a way to pass.
- `dev-tdd` variant: no production code exists yet for the criterion under test, and none is written here. The red report is the specification `green` builds to.
- `dev` variant: production code may already exist for part of the story. A planned test that passes on the first run is still a transition failure, because `red` must be red; report that criterion in `issues` with kind `already-green` and return `status: fail` so a human decides whether the criterion is redundant. Do not weaken the test to make it fail.
- Return `needs_user` when a criterion cannot be expressed as a failing assertion without inventing a value the story does not state. `needs_user` never retries: it is recorded, written into a `REQUIRE_HUMAN` handoff, and the run blocks at this phase on the first ask. It is not closed — it stays `active` with `run.yaml#blocked_at` naming `red` — so once the human has answered, `/dev {story}` resumes it here with attempts reset.

#### references/green.md

The `green` phase makes the frozen tests pass with the smallest change to production code. You write that code inside the candidate root, using `Edit` and `Write`, and you run `devforgeai run test` and `devforgeai run build` while you work; the transition oracle runs them again at ingest, and that run is what advances the phase.

- The tests are frozen. Every path in `test_paths` has a digest recorded in `red_hashes`, and the oracle compares it before running anything. Editing a test file here fails the transition with "test file changed since red", and the `writes: code` check at ingest rejects a `test_paths` entry in the changed set on its own.
- Change only what a failing test demands. Behaviour the story's `## Out of Scope` section excludes is not made better by being small; it is out of scope, and the critic reports it in the `review` phase.
- The `context[]` excerpts carry the constitution, techstack and sourcetree slices that bind this change. The stack policy is enforced independently: a manifest edit that adds a package matched by `packages.deny` or absent from `packages.allow`, or a source file carrying an import forbidden for its path, fails the phase at ingest when the sequencer scans the root. The refusal quotes the `forbidden_imports` reason verbatim, which names the architecture section that mandated it.
- Read the test files in the root and `.devforgeai/work/<story>/red-report.md` for the failure each test asserts. The report is the sequencer's rendering of the accepted `red` result and includes the oracle's problem rows, so it is evidence, not a claim.
- When the tests cannot be satisfied as written because a criterion is ambiguous or self-contradictory, return `status: fail` with `next: red` and a note naming the criterion. The sequencer then resets the candidate root to the `red` checkpoint, deletes the phase reports, clears `red_hashes` and charges an attempt to `red`. It is the only legal `next` value from this phase.
- The attempt budget here is 3. Each transition failure returns the oracle's problem rows to this same worker so the next attempt starts from evidence rather than from a guess.
- `dev-tdd` variant: write the smallest change that turns the failing assertions green, and stop. Structure comes in the next phase, where the tests are already green and can prove behaviour is unchanged.
- `dev` variant: the same limit applies for the same reason. The oracle compares test digests and test outcomes; a larger change is not detected as wrong, but it is not demanded by a test and the critic reports it as behaviour no criterion asked for.

#### references/refactor.md

The `refactor` phase improves structure while the tests stay green and behaviour stays identical. You work in the candidate root as `green` did, with `lint` added to the keys you may run.

- Same fence, same frozen tests, same stack policy as `green`. The one addition is `lint`: when the run's `commands.use` authorises the key, the oracle brokers it after `test` and requires exit zero, and you can run it yourself as `devforgeai run lint` before you finish.
- Behaviour is unchanged by definition here. The oracle cannot prove that on its own — it proves the same tests still pass — so the honest boundary is: change names, extraction, ordering and duplication; do not change a branch condition, a returned value, or an error type. A change that needs a new test is a new story.
- Change nothing when nothing is warranted. An empty `claimed_paths` with `status: pass` is a valid result: the oracle still re-runs the invariants, the suite and `lint`, so the phase remains a real check rather than a formality.
- Reading the diff means reading the files in the root and `.devforgeai/work/<story>/green-report.md`, which lists the paths `green` changed. A path outside the fence fails the phase at ingest, and the sequencer's reset to the `green` checkpoint is what undoes it.
- `status: fail` with `next: red` is available here too, for the case where refactoring exposes that a test encodes the wrong contract. It costs an attempt at `red`.
- When `lint` is not installed, the brokered command is classified `INFRA_FAILURE`, mapped to `could_not_run` with `reason_code: runner_missing`, and routed by `gate_policy.test_runner_missing`, whose default is `REQUIRE_HUMAN`. That closes the run with an install instruction in the handoff; it is not a phase failure and it consumes no attempt.

#### references/smoke.md

The `smoke` phase answers one question: does this story work, criterion by criterion. You judge; you change nothing in the candidate root, and the one file you write is your findings file at `.devforgeai/work/<story>/evidence/smoke_qa/findings.md`, which you name in the receipt's `evidence_refs`.

- The evidence already exists. Read `.devforgeai/work/<story>/green-report.md` and `.devforgeai/work/<story>/refactor-report.md`: the sequencer renders each from the accepted result and includes the oracle's classification and problem rows. The sequencer runs every oracle at ingest, so a second run from this worker would add nothing; the phase grants no key and this worker holds no lease, so neither a stack command nor a write reaches disk.
- The subject is the `refactor` checkpoint of the candidate root. Read the files there; they are the story as `refactor` left it, and the scratch you write into is outside that root, so nothing you write can reach the fence or the promotion.
- Put the criterion-by-criterion table in the findings file and keep `issues` to the bounded summary: one row per failing or uncovered criterion. The file is where a reader goes for the working; `issues` is what the handoff and the phase report quote.
- Map each numbered acceptance criterion to its `test_plan` row and that row's recorded outcome. Report a criterion the tests do not reach as uncovered rather than judging it by reading code; an uncovered criterion is the defect `criterion_without_test` exists to name.
- The story's `## Unchanged Behaviour` section is the regression surface for `scope: change` and `scope: hotfix` stories. Check each line against the recorded suite results and report any line no test covers.
- A failing criterion is a `fail` with the criterion in `issues`. The registry declares no `rewind_to` for this phase, so `next` is refused here: the failure retries this phase to its budget of 2 and then blocks `REQUIRE_HUMAN`. The design intent recorded in `05-subagent-sets.md` is that a failing criterion returns to `green`; section 9 records that the registry does not implement that edge.
- This phase is deliberately narrow. Full regression, cross-story checks and evidence capture belong to the `qa` skill, which runs after `review`.

#### references/review.md

The `review` phase is the independent critic. You judge and you repair nothing; you change nothing in the candidate root, and the one file you write is your findings file at `.devforgeai/work/<story>/evidence/dev_critic/findings.md`, which you name in the receipt's `evidence_refs`.

- Read all four earlier reports under `.devforgeai/work/<story>/`, the files at the `refactor` checkpoint of the candidate root, and the story. Confirm four things: every acceptance criterion maps to a `test_plan` row and that row's test exists; every production change is reached by at least one of those tests; no `ASSUMPTION:` survives outside `## Clarifications`; and the diff respects the `context[]` constitution and style excerpts.
- Quote evidence for each verdict: the test name, the changed path, and the report line. A verdict with no quoted evidence is the failure mode a second opinion exists to eliminate, and it is why this worker is a different file with a different prompt from every worker whose output it reviews.
- Report defects; do not fix them. This phase changes nothing in the root, grants no command key and runs nothing. The criterion-to-test-to-code map you walked belongs in the findings file; `issues` carries one bounded row per defect.
- A `fail` here is not a silent pass. The sequencer inserts the failure as a transition problem row, so the phase retries to its budget of 2 and then closes the run `REQUIRE_HUMAN` with the defect list in the handoff.
- On `pass` this is the last phase: the sequencer marks the run `ready_to_promote`, clears enforcement and writes a `handoff.json` whose one forward command is `devforgeai promote <run>`. Nothing reaches the canonical checkout until the user asks for that command; the second handoff block, written by it, names `/review <story>`. The `review` skill then re-checks the same story against the constitution with fresh workers, which is why this phase's job is coverage and traceability rather than a full compliance review.

### 7e. Worker contracts

One block per worker per variant. `must_not` is compiled into the agent prompt verbatim. The `dev` variant is the default; `dev-tdd` is installed when `constitution.md#mandates` carries `tdd: required`. Exactly one body per canonical name is installed, so `agents/` always holds five files.

`writes` is the header D1 requires of every worker: `candidate` for the three producers, `evidence` for the two judges. A producer's `tools` carry `Edit` and `Write` — `apply_patch` on the Codex target — plus `Bash(devforgeai run *)` as the surface through which the hook layer admits the keys `granted_keys` lists. A judge's carry `Write`, admitted only under `.devforgeai/work/<run>/evidence/<agent>/`, plus `Bash(devforgeai status)` and nothing else that reaches a shell; a write anywhere else, the candidate root included, is denied at `PreToolUse`. Section 7g compiles these blocks into provider-native subagent files.

#### `red_dev`

Variant `dev`:

```yaml
name: red_dev
skill: dev
responsibility: Write exactly the test files the story's test_plan names, inside the candidate root, each failing on its own assertion for its own criterion.
inputs:
  - the devforgeai status block, which names run, candidate.root, phase, fence and granted_keys
  - the story id and the enforcement block's test_paths and test_plan rows
  - the story's Acceptance Criteria, Interface, Unchanged Behaviour and Out of Scope sections
  - the story's context[] excerpts for testing conventions
  - docs/reports/qa-<story>.md, only when the run was opened with --fix
outputs:
  - one file per distinct test_plan file, written under candidate.root at the row's path
  - a receipt whose claimed_paths lists every path written and whose issues carry one row per criterion that could not be expressed
must_not:
  - write a path that is not a test_paths entry
  - weaken, merge or skip a criterion to make a test easier
  - write a test that no test_plan row names
  - return pass for a planned test that already passes; report it as an issue and fail
  - write outside candidate.root, or run a command other than devforgeai run for a granted key
tools: [Read, Grep, Glob, Edit, Write, Bash(devforgeai run *), Bash(devforgeai status)]
granted_keys: [test]
writes: candidate
returns: devforgeai.worker-result/v1
```

Variant `dev-tdd`:

```yaml
name: red_dev
skill: dev
responsibility: Turn each acceptance criterion into the single failing test its test_plan row names, written inside the candidate root before any production code for it exists.
inputs:
  - the devforgeai status block, which names run, candidate.root, phase, fence and granted_keys
  - the story id and the enforcement block's test_paths and test_plan rows
  - the story's Acceptance Criteria, Interface, Unchanged Behaviour and Out of Scope sections
  - the story's context[] excerpts for testing conventions
  - docs/reports/qa-<story>.md, only when the run was opened with --fix
outputs:
  - one file per distinct test_plan file, written under candidate.root at the row's path
  - a receipt whose claimed_paths lists every path written and whose issues carry one row per criterion that could not be expressed
must_not:
  - write or change production code
  - write a path that is not a test_paths entry
  - weaken, merge or skip a criterion to make a test easier
  - leave a planned test that passes before green runs
  - write outside candidate.root, or run a command other than devforgeai run for a granted key
tools: [Read, Grep, Glob, Edit, Write, Bash(devforgeai run *), Bash(devforgeai status)]
granted_keys: [test]
writes: candidate
returns: devforgeai.worker-result/v1
```

#### `green_dev`

Variant `dev`:

```yaml
name: green_dev
skill: dev
responsibility: Write the production code that makes every frozen test_plan test pass, inside the candidate root, and nothing the story does not ask for.
inputs:
  - the devforgeai status block, which names run, candidate.root, phase, fence and granted_keys
  - the test files at the red checkpoint of candidate.root
  - .devforgeai/work/<story>/red-report.md
  - the story's Interface, Acceptance Criteria and Out of Scope sections
  - the story's context[] excerpts for the constitution, techstack and sourcetree slices
outputs:
  - production files written inside write_fence, under candidate.root
  - a receipt whose claimed_paths lists every path written and whose issues name any criterion the tests cannot reach
must_not:
  - change a path that is in test_paths
  - add behaviour the story's Out of Scope section excludes
  - add a package outside packages.allow or matched by packages.deny, or an import forbidden for that path
  - request a rewind to any phase other than red
  - write outside candidate.root, or run a command other than devforgeai run for a granted key
tools: [Read, Grep, Glob, Edit, Write, Bash(devforgeai run *), Bash(devforgeai status)]
granted_keys: [test, build]
writes: candidate
returns: devforgeai.worker-result/v1
```

Variant `dev-tdd`:

```yaml
name: green_dev
skill: dev
responsibility: Make the frozen red tests pass with the smallest production change that satisfies their assertions, written inside the candidate root.
inputs:
  - the devforgeai status block, which names run, candidate.root, phase, fence and granted_keys
  - the test files at the red checkpoint of candidate.root
  - .devforgeai/work/<story>/red-report.md
  - the story's Interface, Acceptance Criteria and Out of Scope sections
  - the story's context[] excerpts for the constitution, techstack and sourcetree slices
outputs:
  - production files written inside write_fence, under candidate.root
  - a receipt whose claimed_paths lists every path written and whose issues name any criterion the tests cannot reach
must_not:
  - change a path that is in test_paths
  - add behaviour no failing test demands
  - add a package outside packages.allow or matched by packages.deny, or an import forbidden for that path
  - request a rewind to any phase other than red
  - write outside candidate.root, or run a command other than devforgeai run for a granted key
tools: [Read, Grep, Glob, Edit, Write, Bash(devforgeai run *), Bash(devforgeai status)]
granted_keys: [test, build]
writes: candidate
returns: devforgeai.worker-result/v1
```

#### `refactor_dev`

Variant `dev`:

```yaml
name: refactor_dev
skill: dev
responsibility: Make structure-only improvements to the files green wrote, inside the candidate root, with the frozen tests still passing and lint clean.
inputs:
  - the devforgeai status block, which names run, candidate.root, phase, fence and granted_keys
  - .devforgeai/work/<story>/green-report.md and the paths it lists
  - the production files at the green checkpoint of candidate.root
  - the story's context[] excerpt for the constitution style slice
outputs:
  - production files changed inside write_fence, under candidate.root, or nothing when no change is warranted
  - a receipt whose claimed_paths lists every path changed, empty when nothing was
must_not:
  - change a branch condition, a returned value or an error type
  - change a path that is in test_paths, or any path outside write_fence
  - add a package outside packages.allow or matched by packages.deny, or an import forbidden for that path
  - write outside candidate.root, or run a command other than devforgeai run for a granted key
tools: [Read, Grep, Glob, Edit, Write, Bash(devforgeai run *), Bash(devforgeai status)]
granted_keys: [test, build, lint]
writes: candidate
returns: devforgeai.worker-result/v1
```

Variant `dev-tdd`:

```yaml
name: refactor_dev
skill: dev
responsibility: Improve the structure of the code green wrote, inside the candidate root, while the frozen tests stay green and behaviour stays identical.
inputs:
  - the devforgeai status block, which names run, candidate.root, phase, fence and granted_keys
  - .devforgeai/work/<story>/green-report.md and the paths it lists
  - the production files at the green checkpoint of candidate.root
  - the story's context[] excerpt for the constitution style slice
outputs:
  - production files changed inside write_fence, under candidate.root, or nothing when no change is warranted
  - a receipt whose claimed_paths lists every path changed, empty when nothing was
must_not:
  - change observable behaviour
  - change a path that is in test_paths, or any path outside write_fence
  - add a package outside packages.allow or matched by packages.deny, or an import forbidden for that path
  - write outside candidate.root, or run a command other than devforgeai run for a granted key
tools: [Read, Grep, Glob, Edit, Write, Bash(devforgeai run *), Bash(devforgeai status)]
granted_keys: [test, build, lint]
writes: candidate
returns: devforgeai.worker-result/v1
```

#### `smoke_qa`

The same contract serves both variants; the phase reads recorded evidence and changes nothing in the candidate root, so nothing about it is variant-specific.

```yaml
name: smoke_qa
skill: dev
responsibility: Decide pass or fail for each numbered acceptance criterion from the test outcomes the sequencer already recorded.
inputs:
  - the devforgeai status block, which names run, candidate.root and phase
  - the story's Acceptance Criteria and Unchanged Behaviour sections and its test_plan rows
  - .devforgeai/work/<story>/green-report.md and .devforgeai/work/<story>/refactor-report.md
  - the files at the refactor checkpoint of candidate.root
outputs:
  - a findings file at .devforgeai/work/<story>/evidence/smoke_qa/findings.md, one row per criterion with its test, verdict and the report line that proves it
  - a receipt whose issues carry one bounded row per failing or uncovered criterion and whose evidence_refs name that findings file and the reports the verdicts were read from
must_not:
  - judge a criterion no test_plan row covers; report it as uncovered instead
  - restate a test outcome the recorded reports do not contain
  - write anywhere but .devforgeai/work/<story>/evidence/smoke_qa/, or run any build, test, lint or format command
tools: [Read, Grep, Glob, Write, Bash(devforgeai status)]
granted_keys: []
writes: evidence
returns: devforgeai.worker-result/v1
```

#### `dev_critic`

The same contract serves both variants. It is a different file with a different prompt from every worker whose output it reviews, which is the point of the phase.

```yaml
name: dev_critic
skill: dev
responsibility: Report, with quoted evidence, every criterion without a test, every change no test reaches, every surviving ASSUMPTION tag, and every departure from the story's constitution excerpts.
inputs:
  - the devforgeai status block, which names run, candidate.root and phase
  - the four earlier reports under .devforgeai/work/<story>/
  - the files at the refactor checkpoint of candidate.root, inside write_fence
  - the story, including its Clarifications section and its context[] excerpts
outputs:
  - a findings file at .devforgeai/work/<story>/evidence/dev_critic/findings.md, carrying the criterion-to-test-to-code map it walked
  - a receipt whose issues carry one bounded row per defect, each quoting the test name, changed path or report line that evidences it, and whose evidence_refs name that findings file and the reports it walked
must_not:
  - repair any defect it finds
  - pass a criterion without quoting the test name and the changed path
  - re-derive a test outcome the recorded reports do not contain
  - write anywhere but .devforgeai/work/<story>/evidence/dev_critic/, or run any build, test, lint or format command
tools: [Read, Grep, Glob, Write, Bash(devforgeai status)]
granted_keys: []
writes: evidence
returns: devforgeai.worker-result/v1
```

### 7f. Handoff outcomes

The `handoff.outcomes` block this skill declares in `skill.yaml`, taken from `02-skill-roster.md`'s decision table and corrected to the closed status set. The **Rendered by** column says who produces the text the user sees: the sequencer writes `next` into `handoff.json` and the adapter prints that block verbatim, except on a gate refusal, where no handoff exists at all and the adapter prints the sequencer's stderr plus this table's repair route.

| Outcome | Next steps | Rendered by |
|---------|------------|-------------|
| pass (all five phases), run `ready_to_promote`, nothing promoted (`REQUIRE_HUMAN`) | `devforgeai promote {run}` | sequencer, at `devforgeai phase next` |
| `devforgeai promote {run}` succeeded, run `promoted` | `/review {story}` | sequencer, at `devforgeai promote` |
| `devforgeai promote {run}` refused `STALE_BASE` after the rebase retry, or in copy mode (`needs_user`) | resolve the canonical divergence, then `devforgeai promote {run}` | sequencer |
| `devforgeai promote {run}` refused `MERGE_CONFLICT` (the rebase was aborted) or `DIRTY_TARGET` (a canonical file the candidate changed is dirty) | commit or stash the named canonical files, then `devforgeai promote {run}` | sequencer |
| `fail` at any phase, attempts exhausted (`REQUIRE_HUMAN`), and the cause is fixable without changing the story | `/dev {story}` — the run is blocked, not closed, and this resumes it at `run.yaml#blocked_at` with attempts reset | sequencer |
| `fail` at any phase, attempts exhausted (`REQUIRE_HUMAN`), and the story itself needs changing | `devforgeai phase fail --reason <text>`, then `/clarify {story}`, then `/dev {story} --fix` | sequencer renders the `phase fail` step, then `/clarify {story}` |
| `needs_user` at any phase (`REQUIRE_HUMAN`, no retry), answerable without changing the story | `/dev {story}` — resumes at `blocked_at` with attempts reset once the human has acted | sequencer |
| `needs_user` at any phase whose answer changes the story | `devforgeai phase fail --reason <text>`, then `/clarify {story}`, then `/dev {story} --fix` | sequencer renders the `phase fail` step, then `/clarify {story}` |
| rewind to `red` exhausted its attempts (`REQUIRE_HUMAN`) | `devforgeai phase fail --reason <text>`, then `/clarify {story}`, then `/dev {story} --fix` | sequencer renders the `phase fail` step, then `/clarify {story}` |
| `could_not_run`, `reason_code: runner_missing` or `timeout` | install the missing runner, then `/dev {story}` | sequencer |
| `could_not_run`, `reason_code: hook_fault` (no worker identity on the stop event) | install or repair the hook dispatcher, then `/dev {story}` | sequencer, through the same missing-runner route |
| `WARN` or `OFF` on `test_runner_missing` | `/dev {story} --fix` | sequencer |
| `devforgeai phase fail --reason` recorded a block (`BLOCK`) | `/dev {story} --fix` | sequencer |
| gate: unresolved ASSUMPTION | `/clarify {story}` | adapter, from the refusal on stderr |
| gate: stale hash on a `provenance[]`, `context[]` or `commands` entry | `/plan {slug} --reslice {story}`, then `/dev {story}` | adapter |
| gate: unresolvable source (missing file, unresolved anchor, placeholder digest) | `/plan {slug} --reslice {story}`; for a stand-alone story outside `docs/plan/`, re-run with the lenient flag | adapter |
| gate: `blocked_by` story not done | `/dev {blocking_story}` first | adapter |
| gate: `requires_skill` names a skill that does not exist | `/skill-gen {requires_skill}`, then `/dev {story}` | adapter; the check itself is designed and unimplemented (section 9) |
| gate: the story's `write_fence` overlaps an active or `ready_to_promote` run (`FENCE_OVERLAP`) | finish or abandon the named run, then `/dev {story}` | adapter, from the refusal on stderr |

The first row is the only one that leaves the run `ready_to_promote`, and `ready_to_promote` is the only status `devforgeai promote {run}` accepts. Every other `REQUIRE_HUMAN` row — an exhausted attempt budget, a `needs_user` result — leaves the run `active` with its lease released and its candidate root on disk. The work is not lost and it is not merged. A `REQUIRE_HUMAN` block — a `needs_user` result or an exhausted attempt budget — leaves the run `active` with its lease released, its candidate root and checkpoints on disk, and `run.yaml#blocked_at` naming the phase it stopped at. `devforgeai phase start` with the same skill and the same argument resumes that run at `blocked_at` with `attempts` reset to zero, rather than refusing it; any other skill on the same story needs `devforgeai phase fail --reason <text>` first, which abandons the root (`10-sequencer-and-contracts.md` sections 2, 3 and 5.4). So the recovery has two shapes: fix the cause and re-run `/dev {story}`, which resumes the blocked run in place; or, when the story itself is what must change, run `devforgeai phase fail --reason <text>` first, because `/clarify {story}` is another skill on the same story.

Also possible in every rendered row: `/status` reprints the same block from the same file. No row invokes another skill's run: `devforgeai phase start` refuses while a run is active, so every edge above is a command a human or a fresh session runs next.

`{story}` is this run's argument. `{slug}` in the `/plan {slug} --reslice {story}` rows is the project slug: `state.yaml` records it (open item OI-10), and the story's own path under `docs/plan/<slug>/stories/` carries it for a story the gate resolved. `plan`'s run argument is the slug that builds its fence, so the shorter form the roster prints would open no run (`SKILL-SPEC-009-plan.md` section 6). `review` and `qa` carry the same rows and the same source for the value.

### 7g. Compiled subagent definitions

Each section 7e contract compiles to one provider-native subagent file per target. The Claude file is Markdown with YAML frontmatter at `.claude/agents/dev-<role>.md`; the Codex file is TOML at `.codex/agents/dev-<role>.toml`. The filename is skill-scoped so two skills' worker sets can install side by side; `name` stays the canonical registry name, because that is the value the provider reports as `agent_type` and the sequencer compares against the active phase's worker. Claude's own rule is that a filename need not match the `name` it declares.

| Worker | name | tools | model | writes | Claude file | Codex file |
|---|---|---|---|---|---|---|
| `red_dev` | `red_dev` | `Read, Grep, Glob, Edit, Write, Bash(devforgeai run *), Bash(devforgeai status)` | `inherit` | candidate | `.claude/agents/dev-red_dev.md` | `.codex/agents/dev-red_dev.toml` |
| `green_dev` | `green_dev` | as `red_dev` | `inherit` | candidate | `.claude/agents/dev-green_dev.md` | `.codex/agents/dev-green_dev.toml` |
| `refactor_dev` | `refactor_dev` | as `red_dev` | `inherit` | candidate | `.claude/agents/dev-refactor_dev.md` | `.codex/agents/dev-refactor_dev.toml` |
| `smoke_qa` | `smoke_qa` | `Read, Grep, Glob, Write, Bash(devforgeai status)` | `inherit` | evidence | `.claude/agents/dev-smoke_qa.md` | `.codex/agents/dev-smoke_qa.toml` |
| `dev_critic` | `dev_critic` | `Read, Grep, Glob, Write, Bash(devforgeai status)` | `inherit` | evidence | `.claude/agents/dev-dev_critic.md` | `.codex/agents/dev-dev_critic.toml` |

`description` is one sentence naming when the primary dispatches the worker, because that is the field the provider matches a dispatch against:

| Worker | description |
|---|---|
| `red_dev` | Dispatch when `devforgeai status` names phase `red` of a `dev` run; it writes the story's planned test files in the candidate root and leaves the suite failing on their assertions. |
| `green_dev` | Dispatch when `devforgeai status` names phase `green` of a `dev` run; it writes the production code that turns the frozen planned tests green, in the candidate root. |
| `refactor_dev` | Dispatch when `devforgeai status` names phase `refactor` of a `dev` run; it improves the structure of that code in the candidate root while the tests stay green. |
| `smoke_qa` | Dispatch when `devforgeai status` names phase `smoke` of a `dev` run; it decides each acceptance criterion from the recorded oracle output and writes only its findings file in the run's evidence scratch. |
| `dev_critic` | Dispatch when `devforgeai status` names phase `review` of a `dev` run; it reports coverage and traceability defects with quoted evidence and writes only its findings file in the run's evidence scratch. |

The body of each file is the four-part outline `templates/agent-md.md` fixes, filled from the worker's section 7e contract and its `references/<phase>.md`:

1. **Job** — the `responsibility` sentence, expanded to what a good result looks like and what it leaves to the next worker. A producer's body opens with the work: "You write … inside the candidate root the status block names, using Edit and Write; run `devforgeai run <key>` whenever you need the tests; finish with the receipt." A judge's opens with "You judge …; you change nothing in the candidate root, and the one file you write is your findings file under the run's evidence scratch; finish with the receipt."
2. **Inputs** — one line per `inputs:` entry, and nothing outside that list is opened. The first entry is always the `devforgeai status` block the primary pasted, which is where the run id, the candidate root, the phase, the fence and the granted keys come from.
3. **Rules** — the `must_not` lines verbatim, each with the mechanism that catches it: the fence check and the claimed-path check at ingest, the phase's `writes` mode against the root, the header's `writes` scope for the agent's own tools, the lease, the oracle condition.
4. **Receipt** — the `devforgeai.worker-result/v1` object from section 6, the statuses this worker may return, and the rule that the final message is exactly that object with no fence and no prose.

Provider differences, stated rather than assumed:

- Claude-only frontmatter keys — `hooks`, `memory`, `background`, `permissionMode`, `maxTurns`, `effort`, `disallowedTools`, `mcpServers`, `color` and the git-worktree isolation key — are omitted from every compiled file. The framework's own isolation is one subagent per phase and the candidate root the sequencer owns; forking a worktree from the default branch would split the linear history these five phases build.
- `skills:` preloads nothing for any of the five. The phase guidance a worker needs is `references/<phase>.md`, which its body links, and preloading the `dev` skill would put the primary's dispatch loop inside a worker.
- `model` is `inherit` for all five: no source in this specification's `depends_on` set assigns a per-worker model, and inheriting keeps a run's five phases on one model rather than making capability depend on a default this specification does not control.
- The Codex file carries `name`, `description`, `sandbox_mode`, `approval_policy` and `developer_instructions`. `sandbox_mode` is the writable-workspace mode for the three producers and the read-only mode for the two judges, which is Codex's equivalent of the `tools` split; `apply_patch` is the write tool the producers use in place of `Edit` and `Write`.
- Neither provider carries the lease, the fence or the granted keys in the agent file. They live in `.devforgeai/work/<run>/run.yaml` and are enforced by the hook dispatcher, so a stale agent file cannot widen what a worker may write. A judge's `Write` is admitted by path — its own `.devforgeai/work/<run>/evidence/<agent>/` — not by the tool list alone.
- On Codex every worker that writes anything, the two judges included, runs in the writable-workspace mode; which directory each may write is the hook dispatcher's restriction, and that is where it is enforced on both providers.

## 8. Bundled resources

### Layout (fixed)

```
dev/SKILL.md               # at most 500 lines: identity, phase list, dispatch loop, handoff table
  references/red.md        # section 7d, red
  references/green.md      # section 7d, green
  references/refactor.md   # section 7d, refactor
  references/smoke.md      # section 7d, smoke
  references/review.md     # section 7d, review
  references/envelope.md   # the worker-result schema from section 6
  agents/red_dev.md        # section 7e contract for the installed variant
  agents/green_dev.md
  agents/refactor_dev.md
  agents/smoke_qa.md
  agents/dev_critic.md
  assets/dev-notes.md      # the dev-notes template
```

`SKILL.md` links to `references/`, `agents/` and `assets/`; an `agents/*.md` links to its own `references/<phase>.md` and to `references/envelope.md`; nothing links further. No `README.md` exists inside the skill directory.

### scripts/

None, and the directory is not created.

| File | Purpose | Invocation | Exit codes |
|------|---------|------------|------------|
| none | no actor in a `dev` run can invoke a script: the primary window's Bash grammar is the five model-callable `devforgeai` operations, and a worker's shell is `devforgeai status` plus, for a producer, `devforgeai run <key>` on a granted key | not applicable | not applicable |

The deterministic checks a script would otherwise perform are already deterministic and already run: the story gate is inlined in `devforgeai phase start`, receipt and changed-set validation runs in `devforgeai ingest-result`, and the suite is brokered by the transition oracle. Shipping a second copy as a script would be a check nothing calls.

### references/

| File | Content | Load when |
|------|---------|-----------|
| `red.md` | section 7d, red: the `test_plan` contract, assertion-not-import failure, the `writes: tests` boundary, the variant paragraphs | dispatching `red_dev` |
| `green.md` | section 7d, green: frozen tests, smallest change, stack policy, the rewind rule, the attempt budget | dispatching `green_dev` |
| `refactor.md` | section 7d, refactor: the structure-only boundary, the `lint` key, the no-change case, the missing-runner route | dispatching `refactor_dev` |
| `smoke.md` | section 7d, smoke: reading recorded evidence, criterion mapping, uncovered criteria, the regression surface | dispatching `smoke_qa` |
| `review.md` | section 7d, review: the four checks, quoted evidence, report-do-not-repair, what a `fail` costs | dispatching `dev_critic` |
| `envelope.md` | the `devforgeai.worker-result/v1` shape, the closed status set, the `reason_code` rule, the bounds, and the rule that the final message is exactly this object with no fence and no prose | every dispatch |

### assets/

| File | Used for |
|------|----------|
| `dev-notes.md` | the `dev-notes` template `dev` owns: the frontmatter keys and the Note, Issues, Files and Oracle sections the phase report is rendered into |

### agents/

One file per worker in section 7e. No file for Gate, Record or Handoff.

| File | Worker (from section 7) | writes | Compiled to |
|------|-------------------------|--------|-------------|
| `red_dev.md` | `red_dev` | candidate | `.claude/agents/dev-red_dev.md`, `.codex/agents/dev-red_dev.toml` |
| `green_dev.md` | `green_dev` | candidate | `.claude/agents/dev-green_dev.md`, `.codex/agents/dev-green_dev.toml` |
| `refactor_dev.md` | `refactor_dev` | candidate | `.claude/agents/dev-refactor_dev.md`, `.codex/agents/dev-refactor_dev.toml` |
| `smoke_qa.md` | `smoke_qa` | evidence | `.claude/agents/dev-smoke_qa.md`, `.codex/agents/dev-smoke_qa.toml` |
| `dev_critic.md` | `dev_critic` | evidence | `.claude/agents/dev-dev_critic.md`, `.codex/agents/dev-dev_critic.toml` |

## 9. Gotchas and edge cases

Each row is a real behaviour of the current implementation or a resolved contradiction between two design documents. Where a resolution is forced by a specific line, the line is named.

| Situation | What goes wrong | What to do instead |
|-----------|-----------------|--------------------|
| OI-1 (closed): an earlier draft of the seven sub-phases gave Slice to a framework worker, though no registry phase dispatches one; `01-skill-anatomy.md#the-seven-sub-phases` now lists Slice among the deterministic sequencer operations | A receipt from a worker the active phase does not name is refused at ingest, because the active phase's worker is `red_dev`, and the run stalls on a protocol error that consumes no attempt | Dispatch no Slice worker. Slice is a sequencer step inside `phase start`: it writes the resolved bundle to `.devforgeai/work/<run>/context.json` and hands every worker that path. The story's `context[]` bundle is what it resolves: `plan` produced it and the gate re-resolved every entry. This specification promises no slice phase and names no framework worker for it. |
| `01-skill-anatomy.md` describes provenance conformance as part of the gate while `10-sequencer-and-contracts.md` section 3.2 limit 3 once said the gate re-resolves `commands.hash` and nothing else (OI-2) | A specification written against the older text understates the gate and lets an author claim a stale `context[]` digest is undetected | The gate re-resolves every `provenance[]` and `context[]` entry as well as `commands`, per `10-sequencer-and-contracts.md` section 3.4 and the story gate's reference-row loop in `examples/hooks/devforgeai.py`. A resolved source with a changed digest is `stale-hash` and is never downgradable; a missing source, unresolved anchor or placeholder digest is `unresolvable-source` and is downgradable only by the two routes in section 3.4. |
| A worker's tool list is read as authorising the raw test command (OI-3) | An author writes a worker that runs the project's runner itself, and its claim that tests pass becomes the reason a phase advances | Tools are per role (D1). A producer carries `Read`, `Grep`, `Glob`, `Edit`, `Write` and `Bash(devforgeai run *)`, and the hook layer admits a `devforgeai run` call only from the lease holder, only for a key the phase granted, with the candidate root as its working directory. A judge carries `Read`, `Grep`, `Glob` and `Bash(devforgeai status)`. No worker ever holds a git write, a package manager, a network tool or a raw stack command, and the phase advances on the oracle the sequencer runs at ingest, never on a worker's own run of the suite. |
| A phase returns `status: fail` with no `next` (OI-4) | Section 5.4 lists no outcome row for it, so an author guesses that the phase passes or that the run ends | The sequencer inserts the worker's failure as a transition problem row, so the phase retries to its `max_attempts` and then blocks `REQUIRE_HUMAN`. A critic that fails is a retry, then a human, never a silent pass. |
| The user runs `/dev {story} --fix` expecting to resume the blocked run (OI-5) | An author reads the flag as the thing that resumes, and writes a `--retry` flag beside it | The run resumes, but no flag is what resumes it. `needs_user` and an exhausted attempt budget both block the run rather than closing it, and `devforgeai phase start dev {story}` — same skill, same argument, flags or not — resumes it at `run.yaml#blocked_at` with attempts reset. `--fix` is an adapter-level flag that changes only what the workers read: the qa report and review report paths are passed as extra inputs, and the `red` oracle is narrowed to the criteria those reports mark failed. `--retry` adds nothing the resume rule does not already give. Only another skill on the same story needs `devforgeai phase fail --reason <text>` first. |
| A handoff row names another skill's command and an author reads it as an invocation (OI-7) | The adapter tries to run `/review` inside the same session and `devforgeai phase start` refuses because a run is active | A "calls" edge is a handoff row, not a call. The finishing run's `next` names the command; a human or a fresh session runs it. |
| `05-subagent-sets.md` names dev's workers `implementer`, `test-writer`, `smoke-qa` and `critic`, and dev-tdd's `red-tester`, `green-implementer`, `refactorer`, `smoke-qa` and `critic`, while the registry binds five phases to `red_dev`, `green_dev`, `refactor_dev`, `smoke_qa` and `dev_critic` (OI-8) | An agent file named `implementer` is refused at ingest, because `agent_type` is compared against the registry's canonical name and the alias map holds no entry for it | The registry name is canonical and is used in section 7, in the `agents/` filenames and in the evidence table. `05`'s hyphenated forms are display aliases, mapped in section 7b. The `dev` variant supplies a `refactor_dev` body even though `05` lists four roles for plain dev, because the registry runs five phases for both variants and a phase with no installed worker cannot advance. |
| Both variants are described as if only `dev-tdd` is test-first | A project that has not mandated TDD is promised a loop it will not get, or is surprised when `green` cannot start before a failing test exists | The `red` oracle requires a red suite with exactly the planned tests failing before `green` opens, for both variants. The variants differ only in the worker prompt bodies in section 7e; the sequencer sees `dev` either way, per `10-sequencer-and-contracts.md` section 4. There is one skill directory, one command and one template set. |
| A criterion fails at `smoke` | `05-subagent-sets.md` says the failing criterion returns to `green-implementer`, but the registry declares no `rewind_to` for the `smoke` phase, so `next: green` is refused at ingest | The `fail` retries `smoke` to its budget of 2 and then blocks `REQUIRE_HUMAN` at `smoke`, with the run still `active` and `run.yaml#blocked_at` naming it. Returning to `green` from `smoke` is designed and unimplemented; `/dev {story}` resumes at `smoke` itself, and the route through `/clarify {story}` needs `devforgeai phase fail --reason <text>` first, after which `/dev {story} --fix` opens a fresh run at `red`. |
| A planned test already passes when `red` runs | The `red` oracle requires every `test_plan` name to be `failed`; a `passed` row fails the transition, and `red_dev` may not touch production code to make it fail | On a plain run, report the criterion in `issues` with kind `already-green` and return `fail`. The phase retries once and then blocks `REQUIRE_HUMAN`, so a human decides whether the criterion is redundant or the story needs re-slicing. Deleting the test is not available: a `test_plan` name absent from the results is `criterion_without_test`. On a `--fix` run the same situation is expected rather than a defect: the oracle requires only the tests for the criteria the report marks failed to be `failed`, and requires every other planned test to be `passed`. |
| The story's digests are placeholders because it is a stand-alone fixture story | Every `provenance[]` and `context[]` entry is `unresolvable-source`, and the gate refuses before any worker runs | Pass `--lenient` to `devforgeai phase start`. It downgrades `unresolvable-source` and nothing else, records every downgraded row in `enforcement.gate_warnings`, prints them on stderr and logs them with the `phase.start` line. It is refused with exit 1 for any story under `docs/plan/` and with exit 2 for a skill whose gate reads no story. It is a flag on one of the four model-callable operations, not a fifth operation. |
| The gate refuses | An author expects a rendered handoff block to print | A `devforgeai phase start` defect writes no `handoff.json`: it exits 1 with the defect list on stderr and opens no run. The gate-outcome routing in `01-skill-anatomy.md` is a requirement on the adapter's printed guidance, not a rendered artifact. The adapter prints the sequencer's stderr plus the matching section 7f row. |
| The story names `requires_skill: dev-tdd` and the skill is not installed | `02-skill-roster.md` promises a `gate: requires_skill missing` route to `/skill-gen` | The story gate does not check `requires_skill` today; the row is retained in section 7f because the handoff table must cover it, and the check is designed and unimplemented. Nothing in this specification gates on it. The row names `/skill-gen {requires_skill}`, not a specification path: `skill-generator`'s one positional argument is the skill name that builds its fence `.devforgeai/skills/<arg>/**`, and a specification path reaches that skill through its `--spec` flag (`SKILL-SPEC-012-skill-generator.md` section 6). |
| `ruff` (or the project's `lint` runner) is absent | The `refactor` oracle brokers `lint`, gets `INFRA_FAILURE`, and an author reads it as a failed refactor | It is `could_not_run` with `reason_code: runner_missing`, routed by `gate_policy.test_runner_missing`. It consumes no attempt and is never a phase failure. The handoff's next step is the install, then `/dev {story}`. |
| The `dev-notes` template declares frontmatter (`story`, `phase`, `template`, `template_version`, `status`, `run`) that the rendered phase report does not carry | An author claims the rendered report is gated against the template header | `examples/hooks/devforgeai.py` renders `<phase>-report.md` as a heading plus bullet rows with no frontmatter. `assets/dev-notes.md` ships as the template `dev` owns and as the shape the renderer fills; conformance of the rendered file to that header is designed and unimplemented, and no phase of this skill gates on it. |
| The worker-result envelope carried a per-file base digest and full file bodies | A generated agent prompt emits the old file array, and every receipt is refused for an unknown key | The envelope is the section 6 receipt: `candidate`, `claimed_paths` and `evidence_refs`, with no per-file body and no per-file digest, because the worker has already written the files and the sequencer derives `changed` — path, blob digest and kind — from the checkpoint diff. `references/envelope.md` carries that shape and nothing older. **Decision (D4):** this specification describes the receipt only. |
| A rewind is requested after several phases have reported | The reports an author expected to read are gone | A rewind is a checkpoint reset the sequencer performs: it resets the candidate root to the `red` checkpoint, deletes every `*-report.md` in the run directory, clears `red_hashes` and charges an attempt to `red`. The canonical checkout is untouched, because nothing has been promoted. **Open:** D2's rewind row names the checkpoint of the phase rewound to, which for `next: red` is the checkpoint `red` itself created; whether a rewind that must also discard `red`'s own tests resets to `base` instead is not stated in D2 and is not decided here. |
| The stop event carries no `agent_type` or `agent_id` | Nothing identifies the worker, so nothing can be applied | The sequencer writes a synthesised result with `status: could_not_run`, `reason_code: hook_fault` and `application: refused`, renders its report, logs `hook_fault`, writes a `REQUIRE_HUMAN` handoff, clears enforcement and exits 0. The subagent is not left in a loop it cannot escape. |
| The skill declares `handoff.outcomes` and an author expects the sequencer to select a row from it | `01-skill-anatomy.md` says the sequencer selects the row by envelope status and fills the placeholders from state, but `examples/hooks/devforgeai.py` selects from its own default table in `10-sequencer-and-contracts.md` section 6 and never reads the skill's block | Section 7f marks which rows the sequencer renders and which the adapter prints from a gate refusal. Selection from the declared block is designed and unimplemented; nothing in this specification gates on it, and the adapter still prints the rendered block verbatim wherever one exists. |
| The handoff envelope declares `repair_route[]`, `source_basis[]`, `artifacts[]`, `validation[]`, `open_items[]` and `session_guidance` | An author promises a block that names the owning skill for a failing template, sourced from `repair_route` | The written `handoff.json` carries `schema`, `run`, `skill`, `outcome`, `phase`, `location`, `reasons`, `next`, `attempts`, `authority.write_fence`, `session_id` and `at`. The other field groups are designed and unimplemented; rule 8 forbids the renderer from adding a fact the envelope does not hold, so the printed block carries only the fields above. |
| A worker returns two JSON objects, or one wrapped in prose plus a second copy | The envelope is refused and the author counts it as a phase attempt | More than one object declaring the schema is a protocol error: the result is refused, the dispatcher exits 2, the same worker sees the reason and continues, and the attempt counter is not incremented. |
| A worker changed a file it did not list in `claimed_paths` | An author expects the extra file to be applied anyway, or to be silently dropped | Neither. The sequencer derives `changed` from the checkpoint diff and refuses the receipt when `changed` is not a subset of `claimed_paths` (`UNCLAIMED_CHANGE`), or when any changed path is outside the fence. Nothing is dropped, because nothing was proposed: the bytes are already in the candidate root, and the phase fails with them still there for the retry to read. **Decision (D4):** `claimed_paths` is a claim the diff checks, not the mechanism that applies anything. |
| Two stories are worked at once | Both runs write the same file in different roots and the second promotion overwrites the first | `phase start` refuses a story whose `write_fence` overlaps the fence of any run that is active or `ready_to_promote`, with `FENCE_OVERLAP`. Two runs with disjoint fences are legal; promotion is serialised under `.devforgeai/lock`, and the second promoter sees `STALE_BASE`, which the sequencer resolves by rebasing the root, re-running the last transition oracle and retrying the fast-forward. **Decision (D3):** parallel stories are separate runs, separate roots and separate sessions; this specification describes no shared root. |
| A second worker is dispatched while a producer is still running | Two agents write into one root and the checkpoint diff cannot attribute either change | The run file records the lease, the hook layer binds it at `SubagentStart` to the provider's agent identity, and a write from any other agent is denied at `PreToolUse` (`LEASE_HELD`). On Codex, where the pre-write event carries no identity, the root itself is the fence and the check is path-under-root. **Decision (D3, D6):** exactly one producer holds the lease at a time; `smoke_qa` and `dev_critic` hold none. |
| The user expects the code to be in the working tree while the run is going | Nothing appears in the canonical checkout until the user promotes | Every write of the run lands in the candidate root under `.devforgeai/work/<run>/wt`, which is gitignored, and reaches the canonical checkout only when the user runs `devforgeai promote {run}` on a run the last passing transition marked `ready_to_promote`. Promotion is never automatic and never part of Handoff. A run that ends `REQUIRE_HUMAN` on an exhausted budget or a `needs_user` result stays `active` and is not promotable; its root stays on disk for inspection, `run.yaml#blocked_at` names the phase, and `/dev {story}` resumes it there with attempts reset. **Decision (D2, D7 as amended):** the primary session stays in the canonical checkout; the model never moves itself into the root. |
| `AUTHOR-BRIEF.md` section 3 says every worker is read-only and section 6 requires every `must_not` block to end with "write any file, or run any build, test, lint or format command" | A producer compiled from that trailer is told not to do the job D1 gives it, and the contradiction is resolved differently by each author | `WRITE-MODEL-REVISION.md` is the decision register for this wave and supersedes the brief's write model wherever they differ. **Decision (D1, D9, as amended):** a producer's trailer ends "write outside the candidate root, or run a command other than `devforgeai run` for a granted key"; a judge's ends "write anywhere but `.devforgeai/work/<run>/evidence/<agent>/`, or run any build, test, lint or format command". Both prompts lead with the job rather than with what the worker may not do. |
| A judge is given no way to record its working | The criterion-by-criterion table has to fit in `issues`, which is bounded at ten rows, so a long story loses its evidence | Each judge writes one findings file under its own `.devforgeai/work/<run>/evidence/<agent>/` and names it in `evidence_refs`; `issues` stays the bounded summary the handoff and the phase report quote. **Decision (D1, D6, D8a, as amended):** that scratch is run-scoped, gitignored, outside the candidate root and outside the fence, so it is never part of `changed` and is never promoted. A judge's `Write` is admitted for that directory alone. |
| The compiled agent file is expected to carry the fence, the lease or the granted keys | An installed file drifts from the run file and an author treats it as authority | The agent file carries `name`, `description`, `tools`, `model` and the body; the fence, the lease and the granted keys live in `.devforgeai/work/<run>/run.yaml` and are enforced by the hook dispatcher. **Decision (section 7g):** every Claude-only key — hooks, memory, background, `permissionMode`, `maxTurns`, `effort`, `disallowedTools`, `mcpServers`, colour and the git-worktree isolation key — is omitted, and `skills:` preloads nothing, so the two targets compile from one contract. |
| The registry grants the `test` key to the `smoke` phase, but `smoke_qa` is a judge with no run surface | An author either widens the judge's tools to spend the grant, or writes that the phase grants nothing and contradicts the registry row this specification quotes | Both statements are true of different things: `examples/hooks/policy.py` gives `smoke` `run_keys={"test"}` with `oracle="report_only"`, and a `report_only` oracle spends no key. **Decision (D8a):** the grant stays as the registry declares it and is inert — the oracle does not spend it and the worker cannot, so no test run happens at `smoke` and `test_runner_missing` cannot fire there. A judge needing a key would be a specification defect, not a reason to widen D1. |
| The project is not a git repository, or is a fixture copy | An author writes the worktree mechanism as the only one and the run cannot open | The sequencer probes for a git repository at the project root and records `candidate.mode`: worktree mode when one exists with at least one commit, copy mode otherwise. Copy mode checkpoints by tree-hash manifest with a copy-aside of changed files, rewinds by restoring that copy-aside, and promotes by copying the changed paths' bytes under the lock; `STALE_BASE` in copy mode is `needs_user` rather than a rebase. **Decision (D2):** one contract, two materialisations, and the eval workspaces in section 10 are copy mode. |
| An earlier draft of section 7b said promotion is part of Handoff and that the sequencer promotes a passing run on its own | An author compiles a `SKILL.md` that never asks the user, and the candidate's bytes land in the canonical checkout without a human decision | Promotion is never automatic. The last passing transition sets `runs.<run>.status: ready_to_promote` and writes a `REQUIRE_HUMAN` handoff whose only forward step is `devforgeai promote <run>`; the compiled `SKILL.md` runs that command only after the user confirms in the session, and that command writes the second handoff block, whose `next` is `/review {story}`. Every run therefore ends in two blocks, not one, and `STALE_BASE`, `DIRTY_TARGET` and `MERGE_CONFLICT` are refusals of `devforgeai promote <run>`, never of `devforgeai phase next`. **Decision (D7, as amended; `10-sequencer-and-contracts.md` sections 5.4, 6 and 12.4):** the sequencer may not close a run onto the canonical tree on its own. |
| An earlier draft said every `REQUIRE_HUMAN` row leaves the run `ready_to_promote` | An author writes a repair route that offers `devforgeai promote {run}` for a blocked run, and the command refuses because the status is `active` | Only the last passing transition sets `ready_to_promote`, and that is the only status `devforgeai promote <run>` accepts. An exhausted attempt budget or a `needs_user` result leaves the run `active` with its lease released and its root on disk for inspection; `devforgeai phase fail --reason <text>` is what abandons it. **Decision (D7, as amended; `10-sequencer-and-contracts.md` sections 5.4 and 12.4):** blocked is not promotable. |
| An earlier draft said a `REQUIRE_HUMAN` block closes the run, so "no flag resumes a closed one" | An author writes a repair route that opens a fresh run, and `devforgeai phase start` refuses it — the blocked run is still `active` — or writes `devforgeai phase fail --reason <text>` into every recovery row and throws away work the run had already checkpointed | A block is not a close. A `needs_user` result and an exhausted attempt budget both leave the run `active` with its lease released, its candidate root and checkpoints on disk, and `run.yaml#blocked_at` naming the phase. `devforgeai phase start` with the same skill and the same argument **resumes** that run at `blocked_at` with `attempts` reset to zero instead of refusing it, so `/dev {story}` is the whole recovery once the human has acted. Only another skill on the same story needs `devforgeai phase fail --reason <text>` first, and that call is what abandons the root. **Decision (`10-sequencer-and-contracts.md` sections 2, 3, 5.4 and 6):** blocked runs resume; they are not reopened. |
| A `--fix` run's `red` phase runs against promoted code that already satisfies most of the story | The plain `red` oracle requires every `test_plan` name to be `failed`, so a fix run can never go red for only the criteria that actually failed, and `red_dev` may not touch production code to force the rest to fail | The `--fix` oracle is the plain `red` oracle narrowed, not relaxed. The sequencer reads the failed-criteria list from the `qa` or `review` report the story's `context[]` bundle names, then requires the `test_plan` tests for exactly those criteria — plus any test the run newly added — to be `failed`, and requires every other `test_plan` test to be `passed`. A fix run whose narrowed set is empty is a defect: there is nothing to fix. Weakening an already-green test to make it fail still fails the transition. **Decision (section 7c `red` row and `references/red.md`):** the list comes from the report, never from the worker's claim. |

## 10. Success criteria and test cases

### Success criteria

- Triggers on the nine section 4 positives and on none of the ten near-misses.
- `SKILL.md` is under 500 lines and contains identity, the five-row phase list, the dispatch loop and the handoff table, and no phase guidance.
- `agents/` holds exactly five files, named for the five canonical workers; `references/` holds exactly six.
- Every `must_not` block ends with its role's closing line: the evidence-scratch line for `smoke_qa` and `dev_critic`, the candidate-root and granted-key line for the three producers. No judge's `tools` value exceeds `Read`, `Grep`, `Glob`, `Write` and `Bash(devforgeai status)`; no producer's exceeds those plus `Edit` and `Bash(devforgeai run *)`.
- A judge's run leaves the candidate root byte-identical and writes exactly one file, under `.devforgeai/work/<run>/evidence/<agent>/`.
- Every agent file declares `writes`, and its value matches the phase's row in section 7c.
- The `SKILL.md` Bash grammar is no wider than `devforgeai status`, `devforgeai phase start dev <story> [--lenient]`, `devforgeai phase fail --reason <text>`, `devforgeai validate` and `devforgeai promote <run>`.
- In a run, the primary-window transcript contains no read of the story, a test file or a source file, and no file write.
- Every file a run changes is inside the candidate root until the user runs `devforgeai promote <run>`; a run that ends `REQUIRE_HUMAN` and is never promoted leaves the canonical checkout byte-identical.
- Every eval run ends with a printed next step that is exactly one command.

### Eval workspace, built once per eval

Each eval runs in its own workspace, built by copying files that already exist. No file is hand-edited; per-eval differences ship as the overlay directories already present in the fixture. The copied tree carries no `.git`, so the sequencer records `candidate.mode: copy` and materialises the candidate root by copy, manifest and copy-aside. That is the mode these evals exercise; worktree mode is exercised by the sequencer demo, which initialises a git repository in its own scratch copy.

1. Copy `docs/design/examples/fixtures/dev-tdd/` without `overlays/` to `<output-dir>/dev-workspace/fixture-<eval-id>/`.
2. Copy `docs/design/examples/fixtures/dev-tdd/overlays/eval-<id>/` over it when that directory exists.
3. Create `.devforgeai/` in the copy. Copy `docs/design/examples/hooks/fixtures/.devforgeai/stack.yaml` into it, and write `state.yaml` containing exactly the three lines `version: 1`, `stories: {}`, `runs: {}`. Do not copy the fixture `state.yaml`: it holds an active run and every `devforgeai phase start` would be refused.
4. Copy `dispatch.py`, `devforgeai.py` and `policy.py` from `docs/design/examples/hooks/` into `.devforgeai/hooks/`. The dispatcher resolves the sequencer as its own sibling, so the three files stay together.
5. Merge `docs/design/examples/hooks/settings.claude.json` into `<copy>/.claude/settings.json` so `SessionStart`, `PreToolUse`, `PostToolUse`, `SubagentStop` and `Stop` route to the dispatcher. Without this no receipt is ingested, no checkpoint is taken and no oracle runs.
6. Install the generated skill at `<copy>/.claude/skills/dev/` and run the prompt from inside the copy.

### evals/evals.json (used verbatim)

```json
{
  "skill_name": "dev",
  "evals": [
    {
      "id": 1,
      "prompt": "Implement STORY-001 in this directory with the dev skill. The story is a stand-alone fixture story outside docs/plan/, so open the run in lenient mode. Promote the run when the handoff asks for it; this instruction is that confirmation.",
      "expected_output": "All five phases pass: tests/test_text.py holds the three planned tests, tinyapp/text.py implements slugify, the run is marked ready_to_promote with a first handoff naming devforgeai promote STORY-001, and after that command runs the second handoff block names /review STORY-001.",
      "files": [],
      "expectations": [
        "The transcript shows `devforgeai phase start dev STORY-001 --lenient` exiting 0 and naming phase red",
        "tests/test_text.py exists after the run and defines test_slugify_basic, test_slugify_unicode and test_slugify_empty",
        "tinyapp/text.py defines slugify, and the only project files changed are the two the story's write_fence names, tinyapp/text.py and tests/test_text.py",
        "The transcript shows the first handoff block naming devforgeai promote STORY-001, then that command being run, and only then do both files reach the working tree: .devforgeai/state.yaml records the run with status promoted",
        ".devforgeai/work/STORY-001/ contains red-result.json, green-result.json, refactor-result.json, smoke-result.json and review-result.json",
        ".devforgeai/work/STORY-001/red-report.md records the red transition and .devforgeai/work/STORY-001/handoff.json, rewritten by devforgeai promote, has outcome pass with next /review STORY-001",
        "The primary-window transcript contains no Read of STORY-001.md, tests/test_text.py or tinyapp/text.py; those reads happen inside dispatched workers"
      ]
    },
    {
      "id": 2,
      "prompt": "Run the dev skill on STORY-001 in this directory. Open the run in lenient mode; the story is a stand-alone fixture story.",
      "expected_output": "The gate refuses because criterion 3 carries an unresolved ASSUMPTION tag. No run opens, no worker is dispatched, no file changes, and the printed next step is /clarify STORY-001.",
      "files": [],
      "expectations": [
        "`devforgeai phase start dev STORY-001 --lenient` exits 1 and its stderr names the unresolved ASSUMPTION in the story body",
        "No .devforgeai/work/STORY-001/ directory exists, so no handoff.json and no snapshot were written",
        "tests/test_text.py does not exist and tinyapp/text.py is byte-identical to the fixture copy",
        "The final message names /clarify STORY-001 as the next step"
      ]
    },
    {
      "id": 3,
      "prompt": "Use the dev skill on STORY-001 in this directory. Criterion 1 already has a passing test and a partial implementation. Open the run in lenient mode.",
      "expected_output": "The red oracle refuses because test_slugify_basic passes rather than failing; red exhausts its two attempts and the run blocks REQUIRE_HUMAN with /clarify STORY-001 as the next step.",
      "files": [],
      "expectations": [
        "`devforgeai phase start dev STORY-001 --lenient` exits 0 and opens phase red",
        ".devforgeai/work/STORY-001/red-report.md contains an oracle problem row naming test_slugify_basic as passed where failed was expected",
        ".devforgeai/work/STORY-001/handoff.json has outcome REQUIRE_HUMAN and next /clarify STORY-001",
        "tinyapp/text.py is byte-identical to the eval-3 overlay copy, because the run blocked and nothing was promoted",
        "No green-result.json, refactor-result.json, smoke-result.json or review-result.json exists in .devforgeai/work/STORY-001/"
      ]
    }
  ]
}
```

Eval 1 requires the `lint` runner named by the fixture's `python` stack section to be installed, because the `refactor` oracle brokers the `lint` key; without it the run ends `REQUIRE_HUMAN` on a missing runner rather than passing. Section 11 records it as a runtime dependency.

Quick-mode results are generation feedback only: one enabled run per eval and no baseline. They are not runtime conformance evidence, and no section of this specification gates on such evidence; the deferred contract is `12-post-mvp.md#pm-02`.

## 11. Dependencies and compatibility

| Kind | Value |
|------|-------|
| Tools | `SKILL.md`: `Read`, `Agent`, and a Bash grammar no wider than `devforgeai status \| phase start dev <story> [--lenient] \| phase fail --reason \| validate \| promote <run>`. Producers (`red_dev`, `green_dev`, `refactor_dev`): `Read`, `Grep`, `Glob`, `Edit`, `Write`, `Bash(devforgeai run *)` and `Bash(devforgeai status)`, with writes admitted under the candidate root. Judges (`smoke_qa`, `dev_critic`): `Read`, `Grep`, `Glob`, `Bash(devforgeai status)` and `Write`, admitted only under `.devforgeai/work/<run>/evidence/<agent>/`. |
| MCP servers | none |
| Runtime | Python 3.11+ and PyYAML 6+ for the sequencer and the hook dispatcher. Worktree mode additionally needs `git` with a repository at the project root, at least one commit, `.devforgeai/work/` ignored, and both the provider's settings file and `.devforgeai/stack.yaml` tracked; the `SessionStart` self-test checks all five and fails `phase start` with `could_not_run: hook_fault` rather than falling back to copy mode. The project under development supplies its own runtime; the fixture's `python` stack section additionally needs `pytest` for the `test` key and `ruff` for the `lint` key. |
| Project commands | `.devforgeai/stack.yaml#<anchor>`, resolved from the story's `commands.source` and pinned by `commands.hash`. Keys granted by the registry: `test` at `red`, `test` and `build` at `green`, `test`, `build` and `lint` at `refactor`, `test` at `smoke`, none at `review`. A producer may run a granted key through `devforgeai run <key>`; the sequencer runs the same keys again in the transition oracle. The `smoke` grant is spent by nothing: that phase's oracle is `report_only` and its worker carries no run surface. Keys are named, never literal commands. Contract: `10-sequencer-and-contracts.md` section 7. |
| DevForgeAI/Core compatibility | Requires the sequencer grammar and the `devforgeai.worker-result/v1` schema of `10-sequencer-and-contracts.md`, 2026-09-02. `NOT_APPLICABLE` for Research Core: `dev` is an anatomy-governed skill, not a Research adapter. |
| Other skills | Consumes `story` from `plan`, `clarification` from `clarify`, `qa-report` from `qa`, `review-report` from `review`, and the architecture set plus `stack` from `architect` or `onboard`. Produces `dev-notes` for `review`, `qa` and `retro`. Invokes none of them: every edge is a handoff row. |

Deferred dependencies. Each names the `12-post-mvp.md` entry and what this skill does today without it.

| Deferred entry | What it would give `dev` | What `dev` does today |
|---|---|---|
| `12-post-mvp.md#pm-01` | runtime verification that each worker actually ran in its own context window | one subagent per phase is a declaration compiled into the target profile; a generated adapter is an uninstalled candidate that a human installs. |
| `12-post-mvp.md#pm-02` | conformance evidence from repeated provider trials | quick-mode eval results are generation feedback only, and no section gates on them. |
| `12-post-mvp.md#pm-04` | an operating-system write boundary per phase, with only the fence mounted writable | the fence is enforced by the `PreToolUse` deny at the candidate root, by the changed-set check at ingest and by the whole-tree policy scan, which is a fast-feedback layer rather than a kernel boundary. |
| `12-post-mvp.md#pm-06` | eval modes beyond `skip` and `quick`, with the interactive viewer and the description-optimisation loop | eval mode is `skip` or `quick`; no third mode is named as available, and no section gates on an eval result. |
| `12-post-mvp.md#pm-09` | one `stack.yaml` describing several packages, selected per story by path | a story pins one anchored section; cross-package stories are out of scope. |
| `12-post-mvp.md#pm-10` | a clean-checkout chain validator as a required repository check | `devforgeai validate` is a read-only invariant scan over the active run, and the hook layer remains user-disableable. |

Frontmatter values derived from this table:

```yaml
compatibility: "Needs Python 3.11+ and PyYAML for the devforgeai sequencer and its hook dispatcher, installed with the DevForgeAI hook fragment for the selected target, plus git at the project root for worktree-mode candidate roots. The project supplies its own build, test and lint runners through the stack.yaml section the story pins."
allowed-tools: "Read Agent Bash(devforgeai status) Bash(devforgeai phase start *) Bash(devforgeai phase fail *) Bash(devforgeai validate) Bash(devforgeai promote *)"
```

## 12. Targets

The generator produces one provider-neutral semantic package and a separate adapter for each selected target when frontmatter, invocation policy, or agent configuration differs. Provider-neutral resources may be shared. Adapter directories are not required to be byte-identical or symlinked.

| Target | Install path | Invocation | Subagents | Notes |
|--------|--------------|------------|-----------|-------|
| claude | `.claude/skills/dev/` plus `.claude/agents/` worker profiles | `/dev STORY-NNN [--fix] [--lenient]` | one provider-native subagent per canonical worker name: three producers that write in the candidate root, two judges that write only their findings file in the run's evidence scratch | Provider-specific frontmatter keys (`argument-hint`, `disable-model-invocation`) are compiled into this target's `SKILL.md` only. |
| codex | `.agents/skills/dev/` plus `.codex/agents/` profiles | `$dev STORY-NNN [--fix] [--lenient]` | the same five, compiled per section 7g; producers use `apply_patch` and the writable-workspace sandbox mode | Portable six-field frontmatter only; policy goes in target-side configuration. |
| both | separate `.claude/skills/dev/` and `.agents/skills/dev/` adapters | as above | as above | Share only provider-neutral resources; validate each adapter independently. |

The `dev-tdd` variant has no invocation of its own. It is installed by swapping the five `agents/*.md` bodies for the `dev-tdd` contracts in section 7e; the command, the skill directory, the gate, the oracles and the handoff table are unchanged.

```yaml
metadata:
  version: "1.0.0"
  devforgeai-spec: "SKILL-SPEC-001"
  devforgeai-target: "both"
  devforgeai-anatomy: "true"
```

Not produced by skill-creator (deferred to DevForgeAI's skill-generator): provider-native `.claude/agents/*.md` and `.codex/agents/*.toml` worker profiles, provider-specific frontmatter keys for the Claude target, and concise `AGENTS.md` sections. Hook definitions are not per-skill: `init` installs the one dispatcher and its provider fragments from `09-hook-dispatcher.md`, and this specification ships none.

A generated package is an uninstalled candidate until those provider-native controls are present and independently validated. Generation or quick-mode success is not installation authority.

## 13. Constraints

- `SKILL.md` under 500 lines and roughly 5,000 tokens, holding only identity, the five-row phase list, the dispatch loop and the handoff table. Every other instruction lives in `references/<phase>.md`, `agents/<role>.md` or `assets/`. Splitting a phase's guidance into more reference files is the correct response to the line budget; cutting content is not.
- References one level deep from whichever file is loaded: `SKILL.md` links to `references/`, `agents/` and `assets/`; an `agents/*.md` links to `references/*.md`. Nothing links further.
- Hooks, state writes and phase advancement are not in the skill. Do not write an instruction the sequencer or a hook already enforces: the gate is `devforgeai phase start`, the fence is result validation plus the `PreToolUse` deny, and "the tests pass" is the transition oracle.
- No `README.md` inside the skill directory.
- No angle brackets in frontmatter. Description 830 characters, name 3 characters.
- Imperative voice. Explain why a step matters rather than shouting it; where an instruction is non-negotiable it is a gate, a fence or an oracle, and the text names that mechanism.
- Provide defaults, not menus. Procedures over declarations.
- No script is shipped, so no script prompts.
- From the story's constitution excerpt: production code is written only in response to a failing test, tests live where `techstack.md#testing` says they live, and no test imports from outside the package under test.

## 14. Acceptance checks

Run these before reporting done and paste their output:

```bash
# frontmatter and naming (skill-creator's own validator)
python -m scripts.quick_validate <output-dir>/dev      # run from the skill-creator directory
# open-standard validator, if installed
skills-ref validate <output-dir>/dev
# size budget
wc -l <output-dir>/dev/SKILL.md                          # must be < 500
# every worker in section 7 has a prompt file, and no extra
ls <output-dir>/dev/agents/                              # red_dev.md green_dev.md refactor_dev.md smoke_qa.md dev_critic.md
# every agent file declares its role's write mode
grep -l 'writes: candidate' <output-dir>/dev/agents/*.md # red_dev.md green_dev.md refactor_dev.md
grep -l 'writes: evidence' <output-dir>/dev/agents/*.md  # smoke_qa.md dev_critic.md
# one reference file per phase, plus envelope.md
ls <output-dir>/dev/references/                          # red.md green.md refactor.md smoke.md review.md envelope.md
# no leftover placeholders
grep -rnE 'T[O]DO|T[B]D|\{\{' <output-dir>/dev || echo clean
# the spec battery
python3 docs/design/specs/verify.py --only v1,v2,v4
```

For non-Research anatomy skills, DevForgeAI skill-validator additionally checks: all sub-phase kinds present with Gate, Record and Handoff bound to sequencer operations; persona and critic are different files; `must_not` and `writes` present in every agent file, `writes` in `candidate | evidence | none`, no judge's `tools` exceed `Read`, `Grep`, `Glob`, `Write` and `Bash(devforgeai status)`, and no producer's exceed those plus `Edit` and `Bash(devforgeai run *)`; the `SKILL.md` Bash grammar is no wider than the five model-callable operations; handoff outcomes cover every status the skill can return, including `could_not_run`.

## 15. Provenance

| Source | Hash | Used for |
|--------|------|----------|
| docs/design/01-skill-anatomy.md#primary-window-contract | see frontmatter | sections 2 (R4), 7a, 13 |
| docs/design/01-skill-anatomy.md#the-seven-sub-phases | see frontmatter | sections 7b, 9 (Slice) |
| docs/design/10-sequencer-and-contracts.md#4-per-skill-phase-registry | see frontmatter | sections 1, 2 (R2, R10), 7b, 7c |
| docs/design/10-sequencer-and-contracts.md#11-per-skill-evidence-and-gate-table | see frontmatter | section 7c |
| docs/design/10-sequencer-and-contracts.md#3-4-re-resolving-sources-and-the-one-downgrade | see frontmatter | sections 7c, 9, 10 |
| docs/design/10-sequencer-and-contracts.md#5-4-transition-oracles | see frontmatter | sections 2 (R6, R8), 7c, 7d |
| docs/design/10-sequencer-and-contracts.md#6-handoff-envelope | see frontmatter | sections 7f, 9 |
| docs/design/11-artifact-registry.md#2-artifact-path-patterns | see frontmatter | section 6 |
| docs/design/02-skill-roster.md#handoff-decision-tables | see frontmatter | section 7f |
| docs/design/05-subagent-sets.md#worked-example-dev-tdd | see frontmatter | sections 2 (R9), 7d, 7e, 9 |
| docs/design/05-subagent-sets.md#sets-per-skill | see frontmatter | sections 7b, 7e, 9 |
| docs/design/08-story-specification.md#what-a-story-must-carry-and-why | see frontmatter | sections 2 (R1), 6, 7d |
