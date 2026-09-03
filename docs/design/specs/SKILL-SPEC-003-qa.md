---
template: skill-spec
template_version: 1
id: SKILL-SPEC-003
skill_name: qa
target: both
status: approved
author: "DevForgeAI plan skill"
date: 2026-09-02
depends_on:
  - source: docs/design/01-skill-anatomy.md#primary-window-contract
    hash: sha256:a6bbaf9af2d69f7ede18d7c40f242c42edb26d79be964ffec3f386d6347014c2
    excerpt: "For an anatomy-governed skill, the primary window (provider entry adapter + skill orchestration) does light, trivial work only. It dispatches workers and calls the sequencer. It never writes state, never advances a phase, and never decides that a phase passed."
  - source: docs/design/01-skill-anatomy.md#evidence-home
    hash: sha256:d4ad2626d2dc993f9879247429ce4a15a9dcee31c9b4b20da8178ffe8bac8dc9
    excerpt: "There is one home for a run's evidence. The sequencer writes every file below except the judge findings under `evidence/<agent>/`:"
  - source: docs/design/10-sequencer-and-contracts.md#4-per-skill-phase-registry
    hash: sha256:511733ee35ca74fd5a5c0b59f225d7d975788e7d43d939f44c23b7aa8460cff0
    excerpt: "| qa | 1 | `run_tests` | `test_runner` | none | 2 | `test` | green | — |"
  - source: docs/design/10-sequencer-and-contracts.md#3-2-defect-to-action-map-as-implemented
    hash: sha256:700e29f7b7eb3b6883d0895d79e3822bf06c32e633eb10b44155761fe4c5ef28
    excerpt: "| `test_runner_missing` | brokered command classified `INFRA_FAILURE` or `TIMEOUT`; worker `could_not_run` | record, block the run at the phase (`blocked_at`, resumable once the runner exists), hand off | **yes**, `run.yaml#gate_policy.test_runner_missing`, default `REQUIRE_HUMAN` | the policy value, verbatim |"
  - source: docs/design/10-sequencer-and-contracts.md#3-4-re-resolving-sources-and-the-one-downgrade
    hash: sha256:722dadc1737749e30d244f222aaa1d8b845bc93f4a573b16f662719e58b49bcd
    excerpt: "The story gate re-resolves every `provenance[]` and `context[]` entry as well as `commands`."
  - source: docs/design/10-sequencer-and-contracts.md#5-4-transition-oracles
    hash: sha256:ffa41b5d270dc260e28fa9f6bdbc855069a6e922d1148c74b25860dba63484dc
    excerpt: "`green` | every `test_paths` hash equals `red_hashes`; build when compiled; broker `test`; every `test_plan` name is `passed` | the tests that were red are green and were not edited to get there"
  - source: docs/design/10-sequencer-and-contracts.md#6-handoff-envelope
    hash: sha256:747b6340fc5c2348aad33ca5488012808670b3503b311d7b7d0f1204625afd4c
    excerpt: "| `qa`, promoted, `verdict: findings` or `fail` | `/dev <arg> --fix` |"
  - source: docs/design/10-sequencer-and-contracts.md#7-stack-yaml
    hash: sha256:f51716b6cfb1f4a48f4efbcff03947b3adab879dac1b6de7720564c85c87c43c
    excerpt: "`commands.<key>.junit_path` | string | `test` only | where the runner writes JUnit XML; the oracle reads per-test outcomes from this file, not from stdout"
  - source: docs/design/11-artifact-registry.md#1-template-registry
    hash: sha256:09607ea79839ab215871d87e8221166e14eeb6ca26f8372e4ead4173f1d92907
    excerpt: "`qa-report` | `.devforgeai/skills/qa/templates/qa-report.md` | 1 | `^CRIT-[0-9]{3}$` | story, template, template_version, status, verdict, depends_on | Criteria, Evidence, Regressions, Fix Guidance"
  - source: docs/design/11-artifact-registry.md#3-depends-on-edges
    hash: sha256:f3c304ff840d2027432f743288bccec0ea5bc5d7b99b7f41c8d524b1c3591da2
    excerpt: "`qa-report` | the story's acceptance criteria and `test_plan`; the `review-report`"
  - source: docs/design/02-skill-roster.md#handoff-decision-tables
    hash: sha256:1dac784b4670cc7559f323011dfe304dfe8c0baf349063162f90d76d902c5d3c
    excerpt: "| qa | pass (`verdict: pass`), more stories in sprint | `/dev {next_story}` |"
  - source: docs/design/05-subagent-sets.md#sets-per-skill
    hash: sha256:9e12f3beb236a025c18d40e741c09ba675bd71d2d87f56e2b205c7556b944bf9
    excerpt: "| qa | test-runner (names `commands.use` keys and reads the oracle output the sequencer recorded in `<phase>-result.json`; it runs nothing itself), criteria-checker, evidence-collector, qa-writer |"
---

# Skill Specification: qa

A stranger with no conversation history must be able to build this skill from this document alone. Every question the generator would otherwise ask is answered below. No unresolved authoring assumption remains; every open item this specification inherited is resolved in writing in section 9.

`qa` opens a story-anchored document run. Its argument is a story id, the same story gate that `dev` runs re-runs here, and the story's `commands`, `test_plan` and `gate_policy` map are copied into the enforcement block so the `run_tests` transition can broker the `test` key. Its fence is the report path, so its workers cannot touch code or tests.

The run gets its own candidate root, created by the sequencer at `devforgeai phase start` from canonical HEAD, exactly as every other run does. It does not attach to the story's `dev` root. The order per story is `dev` → `devforgeai promote <run>` → `review` → `qa`, and `STORY_IN_FLIGHT` enforces it: `devforgeai phase start qa <story>` is refused while any run naming that story — its `dev` run, and its `review` run too — is `active` or `ready_to_promote`. So by the time this run opens, the story's code and tests are in the canonical tree, and the fresh root holds them at the `base` checkpoint. Three of the four workers judge: they change nothing in the root and each writes its findings file into its own run-scoped scratch at `.devforgeai/work/<run>/evidence/<agent>/`, which is gitignored and never promoted. `qa_writer` is the run's one producer, writing the report inside the root under the run's fence; that report reaches the canonical checkout only when the user runs `devforgeai promote <run>`. The `test` key is granted to the `run_tests` phase, not to its worker: the sequencer runs every oracle at ingest, in this run's own root, and `test_runner` reads what it recorded. Running the suite against promoted code in a clean root is the MVP form of the clean verification worktree; the detached read-only variant that decision D8 moves into `12-post-mvp.md` stays deferred.

Two `writes` vocabularies meet here and mean different things. The registry phase's mode — `none` for the first three phases, `docs` for the report — says what a phase may change inside the candidate root. The worker header's `writes` — `candidate`, `evidence` or `none` — says where that agent's tools may write at all. A judging worker is `writes: none` against the root and `writes: evidence` in its header, because its findings file lives outside the root.

## 0. Generator instructions

These instructions are addressed to the skill-generating agent (Anthropic's `skill-creator` skill, or DevForgeAI's `skill-generator`). They replace its interview.

### Cold-session prompt

Paste this into a fresh session from the repository root:

```
Use the skill-creator skill to build the skill specified in docs/design/specs/SKILL-SPEC-003-qa.md.
Follow its section 0 exactly. Output directory: ./out. Eval mode: quick.
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
6. **Output location** is given in the prompt. Create `<output-dir>/qa/`. Do not write anywhere else except the `qa-workspace/` sibling that eval runs require.
7. **On ambiguity, stop before output.** If the spec is still `draft`, contains an unresolved authoring assumption, omits a section, contradicts itself, or leaves a decision this document does not make, do not guess and do not write candidate skill files. End with a list titled `SPEC GAPS` naming each section and question. The spec author fixes and approves the spec before re-running.
8. **Fidelity over creativity.** Use the description in section 3 verbatim. Use the worker contracts in section 7e verbatim as `agents/<role>.md` bodies, adding only the framing the grader agent in skill-creator uses (Role, Inputs, Process, Output). Use the phase guidance in section 7d verbatim as `references/<phase>.md`. Do not add steps, tools, or behaviours the spec does not mention.
9. **Finish with the acceptance checks** in section 14 and include their output in your final message.

## 1. Identity

| Field | Value |
|-------|-------|
| name | `qa` (kebab-case, 2 chars, equals the directory name, no `claude`/`anthropic` prefix) |
| title | Story Acceptance QA |
| purpose | Decide whether one implemented story meets every acceptance criterion, using the suite the sequencer brokers rather than a worker's claim, and record the verdict plus its evidence as a fenced report the next command can act on. |
| category | devforgeai-phase |
| version | 1.0.0 (skill-package version written to `metadata.version`; not the DevForgeAI or Research Core version) |

## 2. Problem and requirements

**Without this skill:** the agent that wrote the code decides whether it works, from the test output it remembers. Three failure modes in `07-purpose-and-enforcement.md` section 2 follow directly: a done declaration because a file exists or a box is ticked; a validator whose non-zero exit gates nothing; and a report that stands in for evidence. A criterion never encoded as a test is silently counted as met, the regression surface the story declared is never checked, and the next sprint inherits a story marked done on a claim nobody can re-derive.

| ID | Kind | Requirement |
|----|------|-------------|
| R1 | explicit | Take one story id and produce `docs/reports/qa-<story>.md` against the `qa-report` template, with one row per numbered acceptance criterion. Source: `11-artifact-registry.md` section 1 and section 2. |
| R2 | explicit | Decide each criterion from the brokered suite's recorded outcome, not from a worker's assertion. Source: `10-sequencer-and-contracts.md` section 1 consequence 3. |
| R3 | explicit | Run after `review`, and cite the review report, so a story that failed review is not passed on test results alone. Source: `11-artifact-registry.md` section 3, `qa-report` row. |
| R4 | implicit | Change no code and no test: three of the four workers change nothing in the candidate root and write only into their own evidence scratch, the run's fence is the report path only, and a change anywhere else in the candidate root fails the phase at ingest. Source: write-model decisions D1 and D4. |
| R5 | implicit | Re-gate the story on entry rather than trusting that `dev` gated it. Source: `01-skill-anatomy.md` gate section. |
| R6 | implicit | Check the story's `## Unchanged Behaviour` lines as the regression surface, and report any line no test covers. Source: `08-story-specification.md`, Unchanged Behaviour row. |
| R7 | discovered | A missing or timing-out test runner is `could_not_run` with a `reason_code`, routed by `gate_policy.test_runner_missing`, whose default is `REQUIRE_HUMAN`. It is never a failed criterion and it consumes no attempt. Source: `10-sequencer-and-contracts.md` section 3.2. |
| R8 | discovered | The `run_tests` transition uses the `green` oracle, which requires every `test_plan` row to be `passed`. A story whose suite is not fully green blocks at phase 1, so no `qa-report` is written on that path. Source: `10-sequencer-and-contracts.md` section 5.4 and section 9 of this specification. |
| R9 | discovered | `qa` brokers the `test` key because the run is story-anchored and copies the story's `commands`. A plain document run carries `commands: {}` and could not. The grant is the phase's, and the sequencer is what spends it at the transition; no `qa` worker runs a stack key. Source: `policy.py` `anchor: story` on `qa`, `devforgeai.py` `cmd_phase_start`, and write-model decision D8a. |
| R10 | discovered | The report is written in the candidate root and reaches the canonical checkout only when the user runs `devforgeai promote <run>` on a run the last passing transition marked `ready_to_promote`; that command fast-forwards under the sequencer's lock and is refused with `STALE_BASE` or `DIRTY_TARGET` rather than merging. Promotion is never automatic and is never part of Handoff. Source: write-model decisions D2 and D7 as amended. |
| R11 | discovered | `qa_writer` holds the run's lease while it writes; the three judging workers hold none and may read the checkpoint concurrently. Source: write-model decisions D3 and D6. |
| R12 | discovered | Each judging worker records its findings as a file under `.devforgeai/work/<run>/evidence/<agent>/` and names it in the receipt's `evidence_refs`; `issues[]` stays the bounded summary `qa_writer` and the handoff quote. That scratch is gitignored, is outside the candidate root and the fence, and is never promoted. Source: write-model decisions D1, D6 and D8a as amended. |
| R13 | discovered | The run opens its own candidate root from canonical HEAD and never attaches to the story's `dev` root; `STORY_IN_FLIGHT` refuses `devforgeai phase start qa <story>` while any run naming that story — `dev` or `review` — is `active` or `ready_to_promote`, so the suite runs against promoted code. A failing criterion routes to a new `/dev {story} --fix` run, never to an edit in this run's root. Source: write-model decision D12. |

## 3. Description

The exact frontmatter `description`. Written as a YAML block scalar so colons are safe; no angle brackets anywhere.

```yaml
description: >
  Verify one implemented DevForgeAI story against its acceptance criteria: the
  sequencer brokers the project's test key and this skill maps every numbered
  criterion to its recorded outcome, checks the story's unchanged-behaviour
  lines for regressions, and writes docs/reports/qa-STORY-NNN.md with a verdict
  and fix guidance. Use this skill whenever someone asks whether a story is
  done, asks to verify, accept, sign off or QA a story, asks which acceptance
  criteria still fail, or asks for test evidence after a review has passed. Do
  NOT use it to write code or tests (use dev), to judge a diff against the
  constitution (use review), to resolve an ambiguous criterion (use clarify),
  or to summarise a whole sprint (use retro).
```

Character count: 724 / 1024.

## 4. Trigger set

Realistic queries, varied in phrasing, explicitness, detail and complexity. The near-misses share vocabulary with `qa` and belong to an adjacent skill. The generator uses this list verbatim.

```json
[
  {"query": "/qa STORY-004", "should_trigger": true},
  {"query": "review passed on STORY-001, can you verify it actually meets the acceptance criteria now", "should_trigger": true},
  {"query": "is STORY-012 done? i want evidence per criterion, not a vibe", "should_trigger": true},
  {"query": "which acceptance criteria are still failing on STORY-007", "should_trigger": true},
  {"query": "sign off docs/plan/billing/stories/STORY-021.md if the tests back it up", "should_trigger": true},
  {"query": "STORY-015 is a change story, make sure the unchanged behaviour list still holds", "should_trigger": true},
  {"query": "collect the test evidence for STORY-003 so retro has something to read", "should_trigger": true},
  {"query": "can we accept STORY-009 into the sprint as complete, or does it go back to dev", "should_trigger": true},
  {"query": "run the acceptance check on STORY-002 and write the report", "should_trigger": true},
  {"query": "implement STORY-004, tests first", "should_trigger": false},
  {"query": "review the STORY-004 diff against the constitution before I raise the PR", "should_trigger": false},
  {"query": "the tests for STORY-004 are failing, fix the code", "should_trigger": false},
  {"query": "criterion 3 of STORY-011 is ambiguous, ask me what you need to know", "should_trigger": false},
  {"query": "our tests are flaky in CI, figure out why test_text.py fails randomly", "should_trigger": false},
  {"query": "sprint-001 is finished, what did we learn and what should change", "should_trigger": false},
  {"query": "add pytest to the project and set up a tests folder with a conftest", "should_trigger": false},
  {"query": "which PRD requirements have no story yet", "should_trigger": false},
  {"query": "write the acceptance criteria for the new rate limiter story", "should_trigger": false}
]
```

## 5. Use cases

### UC-1: Sign-off after review
- **User says:** "/qa STORY-001"
- **Steps:** 1. The adapter calls `devforgeai phase start qa STORY-001`; the document fence gate checks `docs/reports/qa-STORY-001.md`, and because `qa` is story-anchored the full story gate runs too, copying the story's `test_plan`, `commands` and `gate_policy` map into the enforcement block. Because the story's `dev` run was promoted before this call, `STORY_IN_FLIGHT` does not fire, and the run opens its own candidate root from canonical HEAD at the `base` checkpoint. 2. `test_runner` reports the criterion-to-test map the transition will assert and flags any planned test file or test name it cannot find at that checkpoint, writing nothing and running nothing. 3. At the transition the sequencer brokers the `test` key in the root, reads per-test outcomes from the section's `junit_path`, and requires every `test_plan` row to be `passed`. 4. `criteria_checker` maps each numbered criterion to its recorded outcome. 5. `evidence_collector` gathers the citations. 6. `qa_writer` writes `docs/reports/qa-STORY-001.md` inside the root; the sequencer confirms the changed set is that one fence path, the `document` oracle confirms the file reached disk, and the run is marked `ready_to_promote` with a first handoff block naming `devforgeai promote qa-STORY-001`. 7. The user confirms; that command copies the report into the canonical checkout and writes the second block.
- **Result:** one fenced report with a verdict, one row per criterion with the test that evidences it, four result and report pairs under `.devforgeai/work/qa-STORY-001/`, and two handoff blocks.

### UC-2: A criterion has no test
- **User says:** "which acceptance criteria are still failing on STORY-007"
- **Steps:** 1. The story gate refuses at `devforgeai phase start` when a `test_plan` row lacks a criterion, a file or a name, or names a file outside the fence, because that is the `criterion_without_test` class. 2. When the rows are well-formed but a named test is absent from the suite, the `green` oracle at the `run_tests` transition reports that row and the phase retries, then blocks. 3. The handoff carries the failing rows.
- **Result:** no report claiming a criterion is met by a test that does not exist, and a next step that routes the gap back to the skill that owns it.

### UC-3: The test runner is not installed
- **User says:** "/qa STORY-004"
- **Steps:** 1. The gate opens the run. 2. The brokered `test` command is classified `INFRA_FAILURE`, mapped to `could_not_run` with `reason_code: runner_missing`. 3. The sequencer routes it by `gate_policy.test_runner_missing`, whose default is `REQUIRE_HUMAN`, records it, closes the run and writes the handoff.
- **Result:** no criterion is marked failed because of a missing runner, no attempt is consumed, and the next step is the install followed by `/qa STORY-004`.

## 6. Inputs and outputs

### Inputs
| Input | Format | Example file | Required |
|-------|--------|--------------|----------|
| story id | positional argument matching `^STORY-(HOTFIX-)?[0-9]{3}$` | `STORY-001` | yes |
| story | markdown, `story` template v3, owned by `plan` | `docs/design/examples/fixtures/dev-tdd/STORY-001.md` | yes; resolved by the sequencer, never read by the primary window |
| the code and tests under test | project language, the paths the story's `write_fence` and `test_plan` name, read at the `refactor` checkpoint of the story's candidate root | `docs/design/examples/fixtures/dev-tdd/tinyapp/text.py` | yes |
| review report | markdown, `review-report` template, owned by `review` | `docs/reports/review-STORY-001.md` | no; cited when present |
| dev evidence | markdown and JSON under `.devforgeai/work/<story>/` | `.devforgeai/work/STORY-001/green-report.md` | no |
| `.devforgeai/stack.yaml` section | YAML, anchored by the story's `commands.source` and pinned by `commands.hash` | `docs/design/examples/hooks/fixtures/.devforgeai/stack.yaml` | yes; the `test` key is brokered from it |
| `.devforgeai/state.yaml` | YAML | `docs/design/examples/hooks/fixtures/.devforgeai/state.yaml` | yes |
| `--lenient` flag | boolean, forwarded to `devforgeai phase start` | | no; refused for any story under `docs/plan/` |

`qa` consumes `story` from `plan`, `dev-notes` from `dev`, `review-report` from `review`, and `techstack` and `stack` from `architect` or `onboard`, every one of which has a producer in `11-artifact-registry.md` section 5.

### Outputs
| Output | Format | Location | Template |
|--------|--------|----------|----------|
| qa report | markdown with frontmatter | `docs/reports/qa-<story>.md`, written in the candidate root and reaching the canonical checkout only when the user runs `devforgeai promote <run>` | `qa-report` (`.devforgeai/skills/qa/templates/qa-report.md`), seeded by `assets/qa-report.md` |
| phase result | JSON, the validated envelope plus the sequencer's added fields | `.devforgeai/work/qa-<story>/<phase>-result.json` | none; written by the sequencer |
| phase report | markdown | `.devforgeai/work/qa-<story>/<phase>-report.md` | none; rendered by the sequencer |
| rendered report view | markdown | `docs/reports/qa-qa-<story>-<phase>.md` | none; the sequencer's per-phase view, distinct from the fenced report above |
| handoff | JSON plus its printed rendering | `.devforgeai/work/qa-<story>/handoff.json` | `handoff`, rendered by the sequencer |

Evidence lives outside the candidate root, in the canonical checkout's gitignored `.devforgeai/work/<run>/`, and the sequencer is its only writer. A receipt's `evidence_refs` entry is therefore either a path under the candidate root or a path under `.devforgeai/work/<run>/`.

`qa` owns exactly one template, `qa-report`; `11-artifact-registry.md` section 1 records `dev` and `retro` as its consumers.

### Output template

The `qa-report` shape, which `assets/qa-report.md` seeds and `qa_writer` fills:

```
---
story: STORY-NNN
template: qa-report
template_version: 1
status: complete
verdict: pass | fail
depends_on:
  - source: docs/plan/<slug>/stories/STORY-NNN.md
    hash: sha256:<64 hex>
  - source: docs/reports/review-STORY-NNN.md
    hash: sha256:<64 hex>
---

## Criteria

| id | criterion | test | outcome | evidence |
|----|-----------|------|---------|----------|
| CRIT-001 | the criterion text, verbatim from the story | tests/test_text.py::test_slugify_basic | passed | the recorded oracle row that proves it |

## Evidence

- the brokered command key, its classification and its exit code, as the transition recorded them
- the phase report path each row was read from
- the review report path and verdict, when one exists

## Regressions

One line per `## Unchanged Behaviour` statement in the story, with the test that covers it or the word uncovered.

## Fix Guidance

- one line per failing or uncovered criterion, naming the criterion id and what has to change, for the dev run that follows
```

`verdict` is `pass` when every criterion row is `passed` and no regression line is uncovered, and `fail` otherwise. `depends_on` lists the story and the review report with the digests they resolved to, which is the `depends_on` edge `11-artifact-registry.md` section 3 records for `qa-report`.

### Return envelope (DevForgeAI-anatomy skills only)

One schema, both providers: `devforgeai.worker-result/v1`, normative in `schemas/devforgeai/v1/worker-result.schema.json`. A worker's final message is exactly this one JSON object — a receipt for work already done in the candidate root, not a proposal. The three judging workers do no work in the root at all and return an empty `claimed_paths`; `qa_writer` claims the one report path it wrote.

```yaml
schema: devforgeai.worker-result/v1
run: "qa-STORY-001"
skill: "qa"
phase: "run_tests | criteria | evidence | report"
agent: "test_runner | criteria_checker | evidence_collector | qa_writer"
status: pass | fail | needs_user | could_not_run
reason_code: runner_missing | timeout | network | hook_fault   # required only when status is could_not_run
candidate: {id: "qa-STORY-001", input_checkpoint: "refactor | run_tests | criteria | evidence"}
claimed_paths: ["docs/reports/qa-STORY-001.md"]   # report phase only; empty everywhere else
evidence_refs: [".devforgeai/work/qa-STORY-001/run_tests-report.md"]   # at most 16
note: "at most three lines"
issues: [{id, kind, text}]              # at most 10
next: ""                                # refused: no qa phase declares rewind_to
```

`gate_policy` (`BLOCK | REQUIRE_HUMAN | WARN | OFF`) is a defect-to-action map declared in the consumed story, never a status returned here. An unknown key is refused. The report's own frontmatter carries `verdict`, and the sequencer reads it from the file `evidence_refs` names: it selects the handoff row and therefore `next`, while the run's `status` and the handoff's `outcome` stay `pass`, because reporting a failing criterion is a passing run.

## 7. Procedure

The body of `SKILL.md` is section 7a plus the phase list and the handoff table. Section 7d becomes `references/<phase>.md`, one file per registry phase. Section 7e becomes `agents/<role>.md`, one file per worker.

### 7a. Steps

1. Parse the story id and `--lenient` from the invocation. Nothing else is parsed and nothing is read — why: whatever this window reads stays in it for all four phases, and a window that already holds the code is not an independent judge of whether the code works.
2. Run `devforgeai phase start qa <story-id>`, appending `--lenient` only when the user supplied it. Exit 0 opens the run, creates its own candidate root from canonical HEAD and names phase `run_tests`, printing the run id, the candidate root, the fence and the granted keys; exit 1 is a gate refusal with the defect list on stderr, and `STORY_IN_FLIGHT` is one of its reasons when any run naming the story — its `dev` run, or its `review` run — is still `active` or `ready_to_promote`; exit 2 is a usage error — why: `qa` is story-anchored, so this one call runs the document fence gate and the whole story gate, and it is what copies the story's `commands` into the enforcement block so the `test` key can be brokered in the root at the first transition; and this skill tests promoted code, so the root is created from canonical HEAD rather than attached to the story's `dev` root.
3. On a non-zero exit, print the sequencer's message and the matching row from the handoff table in section 7f, then stop. Do not repair the story and do not run the suite by hand — why: repair belongs to the skill that owns the template, and a hand-run suite is not evidence the sequencer recorded.
4. Dispatch the worker the sequencer named, in its own context window. Paste the `devforgeai status` block into the prompt — it names `run`, `candidate.root`, `phase`, `fence` and `granted_keys` — and add the story id and the paths of the earlier phases' reports under `.devforgeai/work/qa-<story>/` — why: paths and ids only; restating the criteria into the prompt replaces the gated artifact with a paraphrase, and the status block is the one place the root and the fence are stated, so a worker never guesses where the tree it judges lives.
5. Read the returned receipt and branch on `status` alone. A worker that completed its inspection returns `pass` whatever it found: failing criteria travel in `issues`, and the verdict is written into the report at phase 4, where the sequencer reads it from the report's frontmatter — why: `status` is a worker outcome, not a quality grade, and treating a failing criterion as a phase failure would retry the same inspection until the attempt budget blocked the run before the report was written.
6. Run `devforgeai status` and read `enforcement.phase`, or treat an empty enforcement block as a closed run. Dispatch that phase's worker and repeat from step 4 — why: the brokered suite runs inside the transition, so the phase recorded in the enforcement block already reflects the oracle's verdict, and reading the block works identically on both providers and after a session restart; the attempt counters and the lease live in the run file beside it.
7. Print the handoff block the sequencer rendered, verbatim. When the gate refused before the run opened, print the sequencer's stderr and the section 7f row instead — why: rule 8 of the handoff rendering rules forbids adding a fact the envelope does not hold.
8. When the user abandons the run, call `devforgeai phase fail --reason <text>` so it closes with a `BLOCK` handoff rather than staying active and refusing the next `devforgeai phase start` for every skill.
9. Run `devforgeai promote <run>` only after the printed handoff says the run is `ready_to_promote` and the user has confirmed the promotion in this session, then print the second handoff block that command renders — why: promotion is never automatic. The last passing transition marks the run `ready_to_promote` and writes a `REQUIRE_HUMAN` handoff whose only forward step is this command, so whether the report reaches the canonical checkout is the user's decision and not the sequencer's.

Bash grammar for this skill is exactly `devforgeai status`, `devforgeai phase start qa <story> [--lenient]`, `devforgeai phase fail --reason <text>`, `devforgeai validate` and `devforgeai promote <run>`. The `test` key is granted to the `run_tests` phase and spent by the sequencer inside that phase's transition oracle, in the candidate root; no `qa` worker carries a `devforgeai run` surface.

### 7b. Sub-phases and workers

Gate, Record and Handoff dispatch no LLM: they are `devforgeai` sequencer operations. Slice dispatches none either, for the reason recorded in section 9.

| # | Sub-phase | Performed by | Writes |
|---|-----------|--------------|--------|
| 0 | Gate | sequencer: `devforgeai phase start qa <story>`, which refuses on `STORY_IN_FLIGHT` while any run naming the story — `dev` or `review` — is `active` or `ready_to_promote`, and otherwise creates the run's own candidate root from canonical HEAD | sequencer |
| 1 | Slice | no worker; the story's `context[]` bundle is the slice, produced by `plan` and re-resolved at the gate | none |
| 2 | Work: `run_tests` | worker: `test_runner`; the suite itself is run by the sequencer at the transition, in the root | evidence |
| 3 | Work: `criteria` | worker: `criteria_checker` | evidence |
| 4 | Work: `evidence` | worker: `evidence_collector` | evidence |
| 5 | Write: `report` | worker: `qa_writer` | candidate |
| 6 | Record | sequencer: `devforgeai phase next` at every transition, which checkpoints the root | sequencer |
| 7 | Handoff | sequencer: `devforgeai phase next`, or `devforgeai phase fail`. A passing last transition marks the run `ready_to_promote` and renders the first block, a `REQUIRE_HUMAN` handoff naming `devforgeai promote <run>`; `devforgeai promote <run>`, run only after the user asks for it, renders the second | sequencer |

`qa` has no separate Review sub-phase: the whole skill is an acceptance check, and its own critic would be a critic of a criterion-to-test map the transition oracle has already verified against the JUnit results. The independence `01-skill-anatomy.md` requires holds between these workers and `dev`'s, which wrote the code they judge. Each worker runs as its own provider-native subagent, which is what gives the phase its own context window; runtime verification that it did is `12-post-mvp.md#pm-01`.

Promotion is not part of Handoff. The last passing transition sets `runs.<run>.status: ready_to_promote` and writes a `REQUIRE_HUMAN` handoff whose one forward command is `devforgeai promote <run>`; the root and its checkpoints stay on disk and no canonical byte moves. The compiled `SKILL.md` runs that command only after the user confirms in the session, and the sequencer then performs it under `.devforgeai/lock`: the report is fast-forwarded into the canonical checkout, and the second handoff block is written. Canonical movement since `base_ref` refuses the command with `STALE_BASE`, which the sequencer resolves in worktree mode by rebasing the root, re-running the last transition oracle and retrying the fast-forward, and reports as `needs_user` in copy mode; a dirty canonical report file refuses it with `DIRTY_TARGET` and nothing is copied. A run blocked before its last phase — for this skill, every red-suite run — never reaches `ready_to_promote` at all: it keeps `status: active` with its lease released, is not promotable, and `devforgeai phase fail --reason <text>` is what abandons it.

`05-subagent-sets.md` names these workers `test-runner`, `criteria-checker`, `evidence-collector` and `qa-writer`. Those hyphenated forms are display aliases; the canonical registry names below are what `agent_type` is compared against.

### 7c. Evidence and gate table

One row per registry phase, in phase order. `<run>` is `qa-<story>`, the `<skill>-<arg>` form a document run uses. The gate in row 1 runs once, at `devforgeai phase start`, and binds every later phase through the enforcement block it writes.

| phase | worker | deterministic gate check | gate_policy | evidence file | transition oracle |
|---|---|---|---|---|---|
| `run_tests` | `test_runner` | document fence gate: `docs/reports/qa-<story>.md` is declared, repository-relative, free of `..`, and not sequencer-owned; no run that is `active` or `ready_to_promote` names this story (`STORY_IN_FLIGHT`), which is what makes the story's `dev` work — and its `review` report — promoted before this run opens; story gate, because the skill is story-anchored: template v3, `status: ready`, no `ASSUMPTION:` before `## Clarifications`, `blocked_by` chain done, every `provenance[]` and `context[]` entry re-resolved to its recorded digest, `write_fence`, `test_plan` and `commands` present, every `test_plan` row carrying criterion, file and name with its file inside the fence, `commands.hash` equal to the current `stack.yaml` digest, the anchored section satisfying the `stack.yaml` contract and defining every key the story authorises; at ingest, `writes: none` against the root requires an empty `claimed_paths` and a candidate root unchanged since the `base` checkpoint the run opened at, while the worker's own write under `.devforgeai/work/qa-<story>/evidence/test_runner/` is admitted and is not part of `changed` | the story's map, copied into the enforcement block: `unresolved_assumption: BLOCK`, `stale_hash: BLOCK`, `unresolvable_source: BLOCK` (downgraded to a recorded warning only by `--lenient` on a story outside `docs/plan/`, or by `WARN`/`OFF` on a `scope: hotfix` story), `criterion_without_test: BLOCK`, `test_runner_missing: REQUIRE_HUMAN` | `.devforgeai/work/qa-<story>/run_tests-result.json`, `.devforgeai/work/qa-<story>/run_tests-report.md` | `green`: fence held, stack policy held, `build` first when the section is compiled, `test` run by the sequencer in the candidate root from the story's anchored section, classification neither `NO_TESTS` nor `COLLECTION_ERROR` nor `TEST_FAILURE`, and every `test_plan` row `passed` in the JUnit results at `junit_path`. `INFRA_FAILURE` or `TIMEOUT` is `could_not_run` routed by `gate_policy.test_runner_missing`, never a failed criterion |
| `criteria` | `criteria_checker` | `writes: none` against the root: `claimed_paths` is empty and nothing changed in the root; the worker holds no lease, so a write tool call inside the root is denied at `PreToolUse`, while its own scratch at `.devforgeai/work/qa-<story>/evidence/criteria_checker/` is admitted; the receipt's `agent` resolves to `criteria_checker` and matches the stop event's `agent_type` | `write_fence_violation: BLOCK` | `.devforgeai/work/qa-<story>/criteria-result.json`, `.devforgeai/work/qa-<story>/criteria-report.md` | `report_only`: no file outside the fence changed since the gate snapshot and the whole-tree package and import policy holds |
| `evidence` | `evidence_collector` | as `criteria`, with its own scratch at `.devforgeai/work/qa-<story>/evidence/evidence_collector/`; the phase grants no command key, so `devforgeai run` is refused for this worker on the key as well as on the lease | `write_fence_violation: BLOCK` | `.devforgeai/work/qa-<story>/evidence-result.json`, `.devforgeai/work/qa-<story>/evidence-report.md` | `report_only`: as `criteria` |
| `report` | `qa_writer` | `writes: docs`: the lease named in the run file is the dispatched agent's (`LEASE_HELD`), and `changed`, derived from the checkpoint diff, is a subset of `claimed_paths` (`UNCLAIMED_CHANGE`) and holds nothing but the run's fence path, `docs/reports/qa-<story>.md`; the whole-tree package and import policy scan over the root finds no violation | `write_fence_violation: BLOCK` | `.devforgeai/work/qa-<story>/report-result.json`, `.devforgeai/work/qa-<story>/report-report.md`, then `.devforgeai/work/qa-<story>/handoff.json` | `document`: the phase produced at least one file and every declared output with non-null content exists on disk. On pass this is the last phase: the run is marked `ready_to_promote`, enforcement is cleared, and the first handoff block names `devforgeai promote <run>`; the second block is written by that command once the user asks for it |

Attempt budgets are 2 for every phase. No phase declares `rewind_to`, so a `next` value in any receipt is refused; a failure retries the same phase and then closes the run `REQUIRE_HUMAN`. Only `run_tests` grants a command key, and only `test`; the grant belongs to the phase and the sequencer spends it in the transition oracle, so no worker of this skill carries a `devforgeai run` surface.

The four phases build linearly on this run's own candidate root from its `base` checkpoint, which is canonical HEAD at `devforgeai phase start`. Only `report` writes, and only it holds the lease: the sequencer grants the lease at dispatch, the hook layer binds it at `SubagentStart`, and `ingest-result` releases it. The three judging workers hold none and may read the checkpoint concurrently; their own writes land in a per-agent scratch outside the root.

Two honest limits bind every row. Every `devforgeai phase start` defect is a refusal whatever the story's declared value says, with the single downgrade in `10-sequencer-and-contracts.md` section 3.4; and `test_runner_missing` is the one class that changes behaviour at transition time, where `WARN` or `OFF` relabels the handoff outcome without continuing the run.

### 7d. Phase guidance

One subsection per registry phase. Each becomes `references/<phase>.md` verbatim, loaded when that phase's worker is dispatched. `references/envelope.md` carries the envelope shape from section 6 and is loaded on every dispatch.

#### references/run_tests.md

The `run_tests` phase does not run the tests. You judge; you change nothing in the candidate root, and the one file you write is your findings file at `.devforgeai/work/qa-<story>/evidence/test_runner/findings.md`, which you name in the receipt's `evidence_refs`. The sequencer runs the story's `test` key at the transition, in the candidate root, reads per-test outcomes from the section's `junit_path`, and requires every `test_plan` row to be `passed`. This phase's job is to state, before that happens, exactly what the transition will assert and to catch the mismatches a suite run would only report as a confusing failure.

- The authority for what the transition asserts is the story's `test_plan` rows and its `commands.use` keys, which the gate copied verbatim into the enforcement block after re-resolving `commands.hash`. Read them from the story; they are identical to the block by construction, and the story is what the gate validated.
- Check three things the oracle would otherwise report as a bare failure, reading the `refactor` checkpoint of the candidate root: every `test_plan` file exists there; every `test_plan` name appears in that file; and `commands.use` names the `test` key. Report each miss as an issue naming the row, because a planned test that is absent from the tree is a story-level defect that routes to `plan` or `dev`, not a test failure that routes to a code fix.
- Record the criterion-to-test map you checked in the findings file, one row per `test_plan` entry, so the later phases and the report read one map rather than three derivations of it; keep `issues` to the bounded summary of what is missing.
- Change nothing in the candidate root. The phase is `writes: none` against it, its `claimed_paths` is empty, and the worker holds no lease, so a write inside the root is denied before it reaches disk; your findings file is the one write you make, and it lands outside the root.
- Name no literal command anywhere. The story authorises keys; the sequencer resolves each key from the hash-pinned `stack.yaml` section and runs it in the root. A worker that writes a literal command into its findings file has invented a fact the run does not use, and this phase's grant is the sequencer's to spend, not yours.
- Return `pass` when the checks completed, whatever they found, so the transition can broker the suite and decide. Return `needs_user` when the story authorises no `test` key at all: the effective key set is the intersection of the phase's grant and the run's `commands.use`, so an empty intersection means the story cannot be verified as written, and that is a decision for the story's owner rather than a retry or a missing runner.

#### references/criteria.md

The `criteria` phase maps every numbered acceptance criterion to the outcome the transition recorded. You judge; you change nothing in the candidate root, and the one file you write is your findings file at `.devforgeai/work/qa-<story>/evidence/criteria_checker/findings.md`, which you name in the receipt's `evidence_refs`.

- The evidence is `.devforgeai/work/qa-<story>/run_tests-report.md`, the sequencer's rendering of the accepted `run_tests` result together with the oracle's problem rows and the brokered command's classification. Read it rather than re-deriving anything: the suite already ran, and a second opinion about what it printed is not evidence.
- One row per numbered criterion in the story's `## Acceptance Criteria`, in the findings file, in order, each carrying the criterion text verbatim, its `test_plan` test, the recorded outcome, and the report line that proves it; `issues` carries the failing and uncovered rows alone. Quoting the criterion verbatim matters because the report is read later by someone without the story open.
- A criterion whose `test_plan` row exists but whose test did not appear in the results is `uncovered`, not `failed`. The two route differently: uncovered is a gap the plan owns, failed is a defect the code owns.
- Read the story's `## Unchanged Behaviour` section and produce one regression row per statement, with the test that covers it or the word `uncovered`. For a `scope: feature` story that section may legitimately read `None.`; record that as a single row rather than as an omission.
- Do not judge a criterion by reading the implementation. If no test covers it, the honest answer is uncovered; a criterion decided by inspection is exactly the claim this skill exists to replace.
- Return `pass` when the mapping completed, whatever it shows, with an empty `claimed_paths`. Return `needs_user` when a criterion is written so that no outcome can be assigned to it, because that is a question for the story's owner and `needs_user` closes the run on the first ask rather than retrying.

#### references/evidence.md

The `evidence` phase collects the citations the report's Evidence section carries, so the verdict can be re-derived by someone who was not in the session. You judge; you change nothing in the candidate root, and the one file you write is your findings file at `.devforgeai/work/qa-<story>/evidence/evidence_collector/findings.md`, which you name in the receipt's `evidence_refs`.

- Collect four kinds of citation: the brokered command's key, classification and exit code as the `run_tests` transition recorded them; the phase report paths each criterion row was read from; the `dev` run's evidence under `.devforgeai/work/<story>/` when it exists; and `docs/reports/review-<story>.md` with its `verdict` when `review` has run.
- Resolve the review report's digest with the hash rule the gate uses, so the qa report's `depends_on` entry can be re-resolved later and a report written against a superseded review is detectable.
- Cite paths, not contents. An excerpt copied into the report is a second copy that will drift from the file it came from; a path plus a digest stays true.
- Where `review` has not run, say so as a citation of absence rather than omitting the row. A qa report that silently omits the review edge cannot be distinguished from one written before `review` existed.
- Add no judgement: this phase gathers, the `criteria` phase decided, and the `report` phase renders. The citations go in the findings file, one per line.
- Return `pass` when the collection completed. A missing optional citation is a recorded absence, not a failure.

#### references/report.md

The `report` phase renders the criterion map, the evidence and the regression rows into the one artifact `dev` and `retro` cite. You write that report inside the candidate root the status block names, at the run's fence path, using `Edit` and `Write`; you run no command; you finish with the receipt.

- Read `.devforgeai/work/qa-<story>/criteria-report.md` and `evidence-report.md`, and the findings file each judging worker left under `.devforgeai/work/qa-<story>/evidence/<agent>/`. The reports are the sequencer's rendering of the accepted receipts; the findings files hold the criterion rows and citations behind them. Both are evidence rather than a claim.
- Fill `assets/qa-report.md`. Every frontmatter key the `qa-report` template header requires is present: `story`, `template`, `template_version`, `status`, `verdict` and `depends_on`. Every required section is present: Criteria, Evidence, Regressions, Fix Guidance.
- Number criterion rows `CRIT-001` upward in the story's own criterion order, so a row id is stable enough to quote in a `dev` run and in a retro.
- Set `verdict: pass` only when every criterion row is `passed` and no regression row reads `uncovered`. Any other combination is `fail`, because a report that grades its own threshold is a report nobody can act on mechanically.
- Fill `depends_on` with the story path and the review report path, each with the digest the earlier phases resolved.
- Write one Fix Guidance line per failing or uncovered row, naming the criterion id and what has to change. That section is the input to the `dev` run the handoff routes to, so a line that names no criterion id is a line that cannot be acted on.
- Add no criterion and no verdict of your own. This phase renders; the `criteria` phase decided.
- Write exactly one file, at `docs/reports/qa-<story>.md` inside the candidate root, and claim that one path in the receipt. Any other changed path fails the phase at ingest, and a phase that writes no file fails the `document` oracle.
- The frontmatter `verdict` you set is what the sequencer reads to select the handoff row, through the `evidence_refs` entry naming this report. The run still passes: reporting a failing criterion is a passing run.

### 7e. Worker contracts

One block per worker. `must_not` is compiled into the agent prompt verbatim.

`writes` is the header D1 requires of every worker: `evidence` for the three judging workers, `candidate` for `qa_writer`, which is this skill's only producer. A judge's `tools` carry `Write`, admitted only under `.devforgeai/work/<run>/evidence/<agent>/`, plus `Bash(devforgeai status)` and nothing else that reaches a shell; a write anywhere else, the candidate root included, is denied at `PreToolUse`. The writer's carry `Edit` and `Write` — `apply_patch` on the Codex target — admitted under the candidate root. No worker carries a `devforgeai run` surface: the `test` key is granted to the `run_tests` phase and spent by the sequencer's oracle at ingest (D8a). Section 7g compiles these blocks into provider-native subagent files.

```yaml
name: test_runner
skill: qa
responsibility: State the criterion-to-test map the transition oracle will assert, and report every test_plan row whose file or test name is absent from the checkpoint under test.
inputs:
  - the devforgeai status block, which names run, candidate.root, phase and granted_keys
  - the story's test_plan rows and commands.use keys, which the gate copied into the enforcement block
  - the test files those rows name, at the base checkpoint of candidate.root, which is canonical HEAD after the story's dev run was promoted
outputs:
  - a findings file at .devforgeai/work/qa-<story>/evidence/test_runner/findings.md, one row per test_plan entry with its criterion, file, test name and whether both were found
  - a receipt whose issues carry one bounded row per missing file, missing test name or unauthorised test key, and whose evidence_refs name that findings file
must_not:
  - write a literal build, test, lint or format command into its findings file, its note or its issues
  - assert a test outcome; the sequencer runs the suite at the transition and records the outcomes
  - write anywhere but .devforgeai/work/qa-<story>/evidence/test_runner/, or run any build, test, lint or format command
tools: [Read, Grep, Glob, Write, Bash(devforgeai status)]
granted_keys: []
writes: evidence
returns: devforgeai.worker-result/v1
```

`test_runner` carries no `devforgeai run` surface, although its phase grants the `test` key. The key is the phase's and the sequencer spends it: a second run from this worker would produce a claim the oracle does not read, and D8a states that a judge needing a run key is a specification defect rather than a reason to widen the tool list. Section 9 records the correction.

```yaml
name: criteria_checker
skill: qa
responsibility: Map every numbered acceptance criterion and every unchanged-behaviour statement to the outcome the run_tests transition recorded.
inputs:
  - the devforgeai status block, which names run, candidate.root and phase
  - the story's Acceptance Criteria and Unchanged Behaviour sections and its test_plan rows
  - .devforgeai/work/qa-<story>/run_tests-report.md
outputs:
  - a findings file at .devforgeai/work/qa-<story>/evidence/criteria_checker/findings.md, one row per criterion with its verbatim text, its test, its outcome and the report line that proves it, plus one regression row per unchanged-behaviour statement
  - a receipt whose issues carry one bounded row per failed or uncovered criterion, and whose evidence_refs name that findings file
must_not:
  - decide a criterion by reading the implementation instead of a recorded outcome
  - report a criterion with no covering test as failed rather than uncovered
  - write anywhere but .devforgeai/work/qa-<story>/evidence/criteria_checker/, or run any build, test, lint or format command
tools: [Read, Grep, Glob, Write, Bash(devforgeai status)]
granted_keys: []
writes: evidence
returns: devforgeai.worker-result/v1
```

```yaml
name: evidence_collector
skill: qa
responsibility: Collect the brokered command outcome, the phase report paths, the dev run's evidence and the review report with its digest, so the verdict can be re-derived later.
inputs:
  - the devforgeai status block, which names run, candidate.root and phase
  - .devforgeai/work/qa-<story>/run_tests-report.md and criteria-report.md
  - .devforgeai/work/<story>/ phase reports from the dev run, when they exist
  - docs/reports/review-<story>.md at the base checkpoint of candidate.root, when a promoted review run wrote it
outputs:
  - a findings file at .devforgeai/work/qa-<story>/evidence/evidence_collector/findings.md, one citation per line, each a path plus the digest or recorded value that fixes it
  - a receipt whose evidence_refs name that findings file and the reports read
must_not:
  - copy file contents into the citations instead of citing a path and a digest
  - omit a missing optional citation instead of recording its absence
  - add a verdict or a criterion judgement
  - write anywhere but .devforgeai/work/qa-<story>/evidence/evidence_collector/, or run any build, test, lint or format command
tools: [Read, Grep, Glob, Write, Bash(devforgeai status)]
granted_keys: []
writes: evidence
returns: devforgeai.worker-result/v1
```

```yaml
name: qa_writer
skill: qa
responsibility: Write docs/reports/qa-<story>.md inside the candidate root, rendering the criterion map, the citations and the regression rows against the qa-report template and adding no judgement of its own.
inputs:
  - the devforgeai status block, which names run, candidate.root, phase and fence
  - .devforgeai/work/qa-<story>/criteria-report.md and evidence-report.md, and the findings file each judging worker left under .devforgeai/work/qa-<story>/evidence/
  - the story id and the paths and digests the evidence phase resolved
  - assets/qa-report.md
outputs:
  - the report file, written at the fence path under candidate.root
  - a receipt claiming that one path, with the report named in evidence_refs so the sequencer can read its verdict
must_not:
  - add a criterion row or a regression row no earlier phase produced
  - set verdict pass while a criterion row is not passed or a regression row reads uncovered
  - change any path other than docs/reports/qa-<story>.md
  - omit a required frontmatter key or a required section of the qa-report template
  - write outside the candidate root, or run any command other than devforgeai status
tools: [Read, Grep, Glob, Edit, Write, Bash(devforgeai status)]
granted_keys: []
writes: candidate
returns: devforgeai.worker-result/v1
```

### 7f. Handoff outcomes

The `handoff.outcomes` block this skill declares in `skill.yaml`, taken from `02-skill-roster.md`'s decision table and corrected to the closed status set. The **Rendered by** column says who produces the text the user sees: the sequencer writes `next` into `handoff.json` and the adapter prints that block verbatim, except on a gate refusal, where no handoff exists and the adapter prints the sequencer's stderr plus this table's repair route.

| Outcome | Next steps | Rendered by |
|---------|------------|-------------|
| pass (all four phases), run `ready_to_promote`, report not yet promoted (`REQUIRE_HUMAN`) | `devforgeai promote {run}` | sequencer, at `devforgeai phase next` |
| `devforgeai promote {run}` succeeded, report `verdict: pass`, more stories in the sprint | `/dev {next_story}` | sequencer renders `/status` for a document run; section 9 records the difference |
| `devforgeai promote {run}` refused `STALE_BASE` after the rebase retry, or in copy mode (`needs_user`) | resolve the canonical divergence, then `devforgeai promote {run}` | sequencer |
| `devforgeai promote {run}` refused `MERGE_CONFLICT` or `DIRTY_TARGET` (the canonical report file is dirty) | commit or stash the named canonical file, then `devforgeai promote {run}` | sequencer |
| `devforgeai promote {run}` succeeded, report `verdict: pass`, sprint complete | `/retro {sprint}` | sequencer renders `/status` |
| `devforgeai promote {run}` succeeded, report `verdict: findings` or `verdict: fail` | `/dev {story} --fix`, then `/qa {story}` | sequencer, from the promoted block's verdict row (`10-sequencer-and-contracts.md` section 6); the failing rows and their fix guidance are in the fenced report, and the repair is a fresh `dev` run, never an edit inside this run's root |
| `run_tests` oracle failed to its attempt limit (`REQUIRE_HUMAN`); no report is written | `devforgeai phase fail --reason <text>`, then `/dev {story} --fix`, then `/qa {story}` | sequencer renders the `phase fail` step; `dev` is another skill on the same story, so the blocked qa run must be closed before it can open |
| `fail` at any other phase, attempts exhausted (`REQUIRE_HUMAN`) | repair the named defect, then `/qa {story}` — the run is blocked, not closed, and that command resumes it at `run.yaml#blocked_at` with attempts reset | sequencer |
| `needs_user` at any phase (`REQUIRE_HUMAN`, no retry), answerable without changing the story | `/qa {story}` — the same resume, once the human has acted | sequencer |
| `needs_user` at any phase whose answer changes the story | `devforgeai phase fail --reason <text>`, then `/clarify {story}`, then `/qa {story}` | sequencer renders the `phase fail` step, then `/clarify {story}` |
| `could_not_run`, `reason_code: runner_missing` or `timeout` (`test_runner_missing` default `REQUIRE_HUMAN`) | install or repair the test runner named in the report, then `/qa {story}` | sequencer |
| `could_not_run`, `reason_code: hook_fault` (no worker identity on the stop event) | install or repair the hook dispatcher, then `/qa {story}` | sequencer, through the same missing-runner route |
| `WARN` or `OFF` on `test_runner_missing` | `/qa {story} --fix` | sequencer |
| `devforgeai phase fail --reason` recorded a block (`BLOCK`) | `/qa {story} --fix` | sequencer |
| gate: unresolved ASSUMPTION in the story | `/clarify {story}`, then `/qa {story}` | adapter, from the refusal on stderr |
| gate: stale hash on a `provenance[]`, `context[]` or `commands` entry | `/plan {slug} --reslice {story}`, then `/qa {story}` | adapter |
| gate: unresolvable source | `/plan {slug} --reslice {story}`; for a stand-alone story outside `docs/plan/`, re-run with the lenient flag | adapter |
| gate: a `test_plan` row lacks a criterion, a file or a name, or names a file outside the fence | `/plan {slug} --reslice {story}`, then `/qa {story}` | adapter |
| gate: the report fence overlaps an active or `ready_to_promote` run (`FENCE_OVERLAP`) | finish or abandon the named run, then `/qa {story}` | adapter, from the refusal on stderr |
| gate: another run names this story and is still `active` or `ready_to_promote` — its `dev` run, or its `review` run (`STORY_IN_FLIGHT`) | promote the run the refusal names with `devforgeai promote {run}`, or close it with `devforgeai phase fail --reason <text>`, then `/qa {story}` | adapter, from the refusal on stderr |

The first row is the only one that leaves the run `ready_to_promote`, and `ready_to_promote` is the only status `devforgeai promote {run}` accepts. Every other `REQUIRE_HUMAN` row leaves the run `active` with its lease released and its candidate root on disk. A report written before the block is not lost and is not merged. A `REQUIRE_HUMAN` block — a `needs_user` result or an exhausted attempt budget — leaves the run `active` with its lease released, its candidate root and checkpoints on disk, and `run.yaml#blocked_at` naming the phase it stopped at. `devforgeai phase start` with the same skill and the same argument resumes that run at `blocked_at` with `attempts` reset to zero, rather than refusing it; any other skill on the same story needs `devforgeai phase fail --reason <text>` first, which abandons the root (`10-sequencer-and-contracts.md` sections 2, 3 and 5.4). So a blocked qa run is repaired by fixing the cause and re-running `/qa {story}`, which resumes it in place; a route through `dev` or `clarify` — another skill on the same story — needs the `phase fail` step first.

Also possible in every rendered row: `/status` reprints the same block from the same file. No row invokes another skill's run: `devforgeai phase start` refuses while a run is active, so every edge above is a command a human or a fresh session runs next. `{story}` is this run's argument, and `{slug}` in the `/plan {slug} --reslice {story}` rows is the project slug that `state.yaml` records and the story's own path under `docs/plan/<slug>/stories/` carries; `SKILL-SPEC-001-dev.md` section 7f states the same source, and `plan`'s run argument is that slug.

### 7g. Compiled subagent definitions

Each section 7e contract compiles to one provider-native subagent file per target. The Claude file is Markdown with YAML frontmatter at `.claude/agents/qa-<role>.md`; the Codex file is TOML at `.codex/agents/qa-<role>.toml`. The filename is skill-scoped so two skills' worker sets can install side by side; `name` stays the canonical registry name, because that is the value the provider reports as `agent_type` and the sequencer compares against the active phase's worker. Claude's own rule is that a filename need not match the `name` it declares.

| Worker | name | tools | model | writes | Claude file | Codex file |
|---|---|---|---|---|---|---|
| `test_runner` | `test_runner` | `Read, Grep, Glob, Write, Bash(devforgeai status)` | `inherit` | evidence | `.claude/agents/qa-test_runner.md` | `.codex/agents/qa-test_runner.toml` |
| `criteria_checker` | `criteria_checker` | `Read, Grep, Glob, Write, Bash(devforgeai status)` | `inherit` | evidence | `.claude/agents/qa-criteria_checker.md` | `.codex/agents/qa-criteria_checker.toml` |
| `evidence_collector` | `evidence_collector` | `Read, Grep, Glob, Write, Bash(devforgeai status)` | `inherit` | evidence | `.claude/agents/qa-evidence_collector.md` | `.codex/agents/qa-evidence_collector.toml` |
| `qa_writer` | `qa_writer` | `Read, Grep, Glob, Edit, Write, Bash(devforgeai status)` | `inherit` | candidate | `.claude/agents/qa-qa_writer.md` | `.codex/agents/qa-qa_writer.toml` |

`description` is one sentence naming when the primary dispatches the worker, because that is the field the provider matches a dispatch against:

| Worker | description |
|---|---|
| `test_runner` | Dispatch when `devforgeai status` names phase `run_tests` of a `qa` run; it states the criterion-to-test map the transition will assert and flags every planned test the tree does not hold, running nothing and writing only its findings file in the run's evidence scratch. |
| `criteria_checker` | Dispatch when `devforgeai status` names phase `criteria` of a `qa` run; it maps each acceptance criterion and each unchanged-behaviour statement to the outcome the transition recorded, writing only its findings file in the run's evidence scratch. |
| `evidence_collector` | Dispatch when `devforgeai status` names phase `evidence` of a `qa` run; it collects the paths and digests that let the verdict be re-derived later, writing only its findings file in the run's evidence scratch. |
| `qa_writer` | Dispatch when `devforgeai status` names phase `report` of a `qa` run; it writes the qa report in the candidate root from the criterion map and the citations, adding no judgement of its own. |

The body of each file is the four-part outline `templates/agent-md.md` fixes, filled from the worker's section 7e contract and its `references/<phase>.md`:

1. **Job** — the `responsibility` sentence, expanded to what a good result looks like and what it leaves to the next worker. `qa_writer`'s body opens with the work: "You write the qa report inside the candidate root the status block names, using Edit and Write; finish with the receipt." Each judging worker's opens with "You judge …; you change nothing in the candidate root, and the one file you write is your findings file under the run's evidence scratch; finish with the receipt."
2. **Inputs** — one line per `inputs:` entry, and nothing outside that list is opened. The first entry is always the `devforgeai status` block the primary pasted, which is where the run id, the candidate root, the phase, the fence and the granted keys come from.
3. **Rules** — the `must_not` lines verbatim, each with the mechanism that catches it: the fence check and the claimed-path check at ingest, the phase's `writes` mode against the root, the header's `writes` scope for the agent's own tools, the lease, the `green` oracle at `run_tests` and the `document` oracle at `report`.
4. **Receipt** — the `devforgeai.worker-result/v1` object from section 6, the statuses this worker may return, and the rule that the final message is exactly that object with no fence and no prose. `qa_writer`'s adds that the report's frontmatter `verdict` is what the sequencer reads through `evidence_refs`.

Provider differences, stated rather than assumed:

- Claude-only frontmatter keys — `hooks`, `memory`, `background`, `permissionMode`, `maxTurns`, `effort`, `disallowedTools`, `mcpServers`, `color` and the git-worktree isolation key — are omitted from every compiled file. The framework's own isolation is one subagent per phase and the candidate root the sequencer owns; forking a worktree from the default branch would take this run away from the checkpoint whose tests it exists to run.
- `skills:` preloads nothing for any of the four. The phase guidance a worker needs is `references/<phase>.md`, which its body links, and preloading the `qa` skill would put the primary's dispatch loop inside a worker.
- `model` is `inherit` for all four: no source in this specification's `depends_on` set assigns a per-worker model, and inheriting keeps a run's four phases on one model.
- The Codex file carries `name`, `description`, `sandbox_mode`, `approval_policy` and `developer_instructions`. Every one of the four runs in the writable-workspace mode, because each writes something; the difference between a judge and the writer is the path each may write, which the hook dispatcher enforces on both providers. `apply_patch` is the write tool in place of `Edit` and `Write`.
- Neither provider carries the lease, the fence or the granted keys in the agent file. They live in `.devforgeai/work/<run>/run.yaml` and are enforced by the hook dispatcher, so a stale agent file cannot hand a judge the `test` key its phase grants the sequencer, and a judge's `Write` is admitted by path — its own `.devforgeai/work/<run>/evidence/<agent>/` — not by the tool list alone.

## 8. Bundled resources

### Layout (fixed)

```
qa/SKILL.md                # at most 500 lines: identity, phase list, dispatch loop, handoff table
  references/run_tests.md  # section 7d, run_tests
  references/criteria.md   # section 7d, criteria
  references/evidence.md   # section 7d, evidence
  references/report.md     # section 7d, report
  references/envelope.md   # the worker-result schema from section 6
  agents/test_runner.md
  agents/criteria_checker.md
  agents/evidence_collector.md
  agents/qa_writer.md
  assets/qa-report.md      # the qa-report template
```

`SKILL.md` links to `references/`, `agents/` and `assets/`; an `agents/*.md` links to its own `references/<phase>.md` and to `references/envelope.md`; nothing links further. No `README.md` exists inside the skill directory.

### scripts/

None, and the directory is not created.

| File | Purpose | Invocation | Exit codes |
|------|---------|------------|------------|
| none | no actor in a `qa` run can invoke a script: the primary window's Bash grammar is the five model-callable `devforgeai` operations, and a worker's shell is `devforgeai status` alone | not applicable | not applicable |

The deterministic checks a script would otherwise perform already run: the story gate and the fence gate are inlined in `devforgeai phase start`, the suite is run by the sequencer and its JUnit results are parsed by the `green` oracle, receipt and changed-set validation runs in `devforgeai ingest-result`, and the `document` oracle confirms the report reached disk.

### references/

| File | Content | Load when |
|------|---------|-----------|
| `run_tests.md` | section 7d, run_tests: what the transition asserts, the three pre-checks, the criterion-to-test map, the no-literal-command rule | dispatching `test_runner` |
| `criteria.md` | section 7d, criteria: reading the recorded transition report, row shape, failed versus uncovered, the regression surface | dispatching `criteria_checker` |
| `evidence.md` | section 7d, evidence: the four citation kinds, digests over excerpts, recording an absence | dispatching `evidence_collector` |
| `report.md` | section 7d, report: template keys and sections, criterion numbering, the verdict rule, `depends_on`, fix guidance | dispatching `qa_writer` |
| `envelope.md` | the `devforgeai.worker-result/v1` shape, the closed status set, the `reason_code` rule, the bounds, and the rule that the final message is exactly this object with no fence and no prose | every dispatch |

### assets/

| File | Used for |
|------|----------|
| `qa-report.md` | the `qa-report` template `qa` owns: the frontmatter keys, the Criteria, Evidence, Regressions and Fix Guidance sections, and the `CRIT-NNN` row shape |

### agents/

One file per worker in section 7e. No file for Gate, Record or Handoff.

| File | Worker (from section 7) | writes | Compiled to |
|------|-------------------------|--------|-------------|
| `test_runner.md` | `test_runner` | evidence | `.claude/agents/qa-test_runner.md`, `.codex/agents/qa-test_runner.toml` |
| `criteria_checker.md` | `criteria_checker` | evidence | `.claude/agents/qa-criteria_checker.md`, `.codex/agents/qa-criteria_checker.toml` |
| `evidence_collector.md` | `evidence_collector` | evidence | `.claude/agents/qa-evidence_collector.md`, `.codex/agents/qa-evidence_collector.toml` |
| `qa_writer.md` | `qa_writer` | candidate | `.claude/agents/qa-qa_writer.md`, `.codex/agents/qa-qa_writer.toml` |

## 9. Gotchas and edge cases

Each row is a real behaviour of the current implementation or a resolved contradiction between two design documents. Where a resolution is forced by a specific line, the line is named.

| Situation | What goes wrong | What to do instead |
|-----------|-----------------|--------------------|
| The seven sub-phases give Slice to a framework worker, but no registry phase dispatches one (OI-1) | A receipt from a worker the active phase does not name is refused at ingest, because the active phase's worker is `test_runner`, and the run stalls on a protocol error that consumes no attempt | Dispatch no Slice worker. Slice is a sequencer step inside `phase start`: it writes the resolved bundle to `.devforgeai/work/<run>/context.json` and hands every worker that path. The story's `context[]` bundle is what it resolves. This specification promises no slice phase and names no framework worker for it. |
| `01-skill-anatomy.md` describes provenance conformance as part of the gate while an earlier revision of `10-sequencer-and-contracts.md` limited the gate to `commands.hash` (OI-2) | A specification written against the older text understates the gate | The story gate re-resolves every `provenance[]` and `context[]` entry as well as `commands`, per `10-sequencer-and-contracts.md` section 3.4, and it runs for `qa` because the skill is story-anchored. A resolved source with a changed digest is `stale-hash` and is never downgradable. |
| A worker's tool list is read as authorising the suite (OI-3) | `test_runner` runs the project's tests itself and reports its own output as the acceptance evidence, which is the claim this skill exists to replace | Tools are per role (D1), and `test_runner` is a judge: `Read`, `Grep`, `Glob` and `Bash(devforgeai status)`, with no `devforgeai run` surface. **Decision (D8a):** the `test` key is granted to the `run_tests` phase and spent by the sequencer's oracle at ingest; an earlier revision of this specification gave the worker `Bash(devforgeai run *)`, which D8a names a specification defect, and it is removed here rather than met by widening D1. |
| A phase returns `status: fail` with no `next` (OI-4) | Section 5.4 lists no outcome row for it, so an author guesses the phase passes | The sequencer inserts the worker's failure as a transition problem row, the phase retries to its budget of 2, and the run then blocks `REQUIRE_HUMAN`. No `qa` phase declares `rewind_to`, so a `next` value is refused outright. |
| A user runs `/qa {story} --fix` expecting the flag to resume the blocked run (OI-5) | An author reads the flag as the resume mechanism and writes a repair route that depends on it | The run does resume, but the flag is not what resumes it. A blocked run stays `active` with `run.yaml#blocked_at` naming the phase, and `devforgeai phase start qa {story}` — same skill, same argument, flags or not — resumes it there with `attempts` reset. `--fix` on this skill is only the `BLOCK` and `WARN` handoffs' rendered next step; it changes nothing the workers read. Another skill on the same story, such as `/dev {story} --fix`, needs `devforgeai phase fail --reason <text>` first, which abandons the root. |
| The handoff says `/dev {next_story}` or `/retro {sprint}` and an author reads it as an invocation (OI-7) | The adapter tries to run the next skill in the same session and `devforgeai phase start` refuses because a run is active | A "calls" edge is a handoff row, not a call. The finishing run's `next` names the command; a human or a fresh session runs it. |
| `05-subagent-sets.md` names the workers `test-runner`, `criteria-checker`, `evidence-collector` and `qa-writer` (OI-8) | An agent file named `qa-writer` is refused at ingest, because `agent_type` is compared against the registry name and the alias map holds no entry for it | The registry names `test_runner`, `criteria_checker`, `evidence_collector` and `qa_writer` are canonical and are used in section 7, in the `agents/` filenames and in the evidence table. The hyphenated forms are display aliases. |
| `10-sequencer-and-contracts.md` section 4 says `qa`'s `run_tests` declares the `test` key and the `green` oracle but a document run carries `commands: {}`, so the broker refuses the key and the oracle reports an infrastructure failure | A specification written against that bullet promises no brokered test run and the skill becomes a report generator with nothing to report | `policy.py` marks `qa` with `anchor: story`, and `devforgeai.py` `cmd_phase_start` runs `document_gate` and then the whole `story_gate`, copying the story's `test_plan`, `commands` and `gate_policy` into the enforcement block while the fence stays the report path. The key is granted and brokered. The section 4 bullet describes the state before that anchor existed; `11-artifact-registry.md` section 6 divergence 5 and its closing paragraph already record the anchored behaviour, and that is what this specification describes. |
| The `green` oracle is described as requiring `test_paths` digests to equal `red_hashes` | A `qa` run has no `red_hashes`, so an author expects the oracle to fail or to be inapplicable | `red_hashes` is written by the `red` transition of a `dev` run and is absent from a fresh `qa` enforcement block, so the digest comparison iterates over nothing. What remains is the part `qa` needs: broker `test`, refuse `NO_TESTS`, `COLLECTION_ERROR` and `TEST_FAILURE`, and require every `test_plan` row `passed`. |
| The suite is not fully green | `02-skill-roster.md` says qa writes `docs/reports/qa-STORY-NNN.md` on failure and sets `next` to the dev fix command | The `run_tests` transition fails, the phase retries to its budget of 2, and the run blocks `REQUIRE_HUMAN` at phase 1, so the `report` phase never runs and **no qa report is written on that path**. The failing rows are in `.devforgeai/work/qa-<story>/run_tests-report.md` and in the handoff's reasons. A failing report is written only when the suite is green and a criterion is uncovered or a regression row is uncovered. Writing a report on a red suite would need a `report_only` oracle at `run_tests` or a fifth phase, and neither exists. |
| The run id looks like it should be the story id | Evidence from the `dev` run under `.devforgeai/work/<story>/` would be overwritten | `run_id` returns `<skill>-<arg>` for a document run, so this run's evidence home is `.devforgeai/work/qa-<story>/` and `dev`'s stays intact and readable as input. The sequencer's per-phase rendered view is therefore `docs/reports/qa-qa-<story>-<phase>.md`, a different file from the fenced report `docs/reports/qa-<story>.md` that the `report` phase writes. |
| A failing criterion is treated as a failed phase | Every story with a gap retries twice and blocks before the report is written | Worker `status` reports whether the inspection completed; the judgement is the report's `verdict`. `criteria_checker` returns `pass` with failing rows in `issues`. Note that this is distinct from the `run_tests` transition, where a red suite genuinely does block the run. |
| The story authorises no `test` key in `commands.use` | The oracle tries to broker a key the phase grants but the run does not authorise, and the refusal reads like a missing runner when the runner is present | The effective key set is the intersection of the phase's grant and the run's `commands.use`, so an empty intersection is a story defect, not an infrastructure fault. `test_runner` returns `needs_user`, which is recorded, written into a `REQUIRE_HUMAN` handoff and closes the run on the first ask with no retry. `could_not_run` with `reason_code: runner_missing` is reserved for the case the classification actually describes: a present key whose command is classified `INFRA_FAILURE` or `TIMEOUT`. |
| The skill declares `handoff.outcomes` and an author expects the sequencer to select a row from it | `01-skill-anatomy.md` says the sequencer selects the row by envelope status and fills placeholders from state, but `examples/hooks/devforgeai.py` selects from its own default table and never reads the skill's block | For a document run the sequencer renders `devforgeai promote <run>` on the first block of a completed run; on the block that promotion writes it renders `/status` when the report's `verdict` is `pass` and `/dev <story> --fix` when it is `findings` or `fail` (`10-sequencer-and-contracts.md` section 6); on a blocked `REQUIRE_HUMAN` it renders `/qa <story>`, which resumes the run; `/qa <story> --fix` on `BLOCK`, and the install-then-command route on a `COULD_NOT_RUN` row. Section 7f marks each row's renderer. Selection from the declared block, including the sprint-complete branch that would need the sprint's state, is designed and unimplemented; nothing here gates on it. |
| The handoff envelope declares `validation[]`, `artifacts[]`, `source_basis[]`, `repair_route[]` and `open_items[]` | An author promises a printed block listing every brokered command outcome | The written `handoff.json` carries `schema`, `run`, `skill`, `outcome`, `phase`, `location`, `reasons`, `next`, `attempts`, `authority.write_fence`, `session_id` and `at`. The other field groups are designed and unimplemented; the brokered command's classification is recorded in `enforcement.last_oracle` and rendered into the phase report instead. |
| `review` has not run | The `qa-report` `depends_on` edge expects a review report | The run still opens and completes: the review edge is a citation, not a gate. `evidence_collector` records the absence explicitly so a reader can tell an unreviewed story from one whose review edge was dropped. The ordering itself is a handoff convention, not a sequencer precondition. |
| The story's digests are placeholders because it is a stand-alone fixture story | Every `provenance[]` and `context[]` entry is `unresolvable-source` and the gate refuses | Pass `--lenient` to `devforgeai phase start`. It is accepted here because the skill is story-anchored, it downgrades `unresolvable-source` and nothing else, and it is refused with exit 1 for any story under `docs/plan/`. It is a flag on one of the four model-callable operations, not a fifth operation. |
| The gate refuses | An author expects a rendered handoff block | A `devforgeai phase start` defect writes no `handoff.json`: it exits 1 with the defect list on stderr and opens no run. The adapter prints that stderr plus the matching section 7f row. |
| The worker-result envelope carried a per-file base digest and full file bodies | A generated agent prompt emits the old file array, and every receipt is refused for an unknown key | The envelope is the section 6 receipt: `candidate`, `claimed_paths` and `evidence_refs`, with no per-file body and no per-file digest, because `qa_writer` has already written the report and the sequencer derives `changed` from the checkpoint diff. **Decision (D4):** this specification describes the receipt only. |
| An author expects the report to appear in the working tree as soon as `qa_writer` finishes | Nothing is in the canonical checkout until the user promotes | The report is written in the candidate root and reaches canonical only when the user runs `devforgeai promote <run>` on a run the last passing transition marked `ready_to_promote`; that command fast-forwards under the lock and is refused as `STALE_BASE` or `DIRTY_TARGET` rather than merging. A run that ends `REQUIRE_HUMAN` before its last phase — which for this skill includes every red-suite run — stays `active`, is not promotable, and keeps its root for inspection. **Decision (D2, D7 as amended):** the primary session stays in the canonical checkout, and promotion is never automatic. |
| `qa` needs a tree to test, and an earlier draft attached the run to the story's `dev` root at the `refactor` checkpoint | The suite runs against an unpromoted root, so a green acceptance run can be recorded for code that never reaches canonical, and the attachment contradicts `STORY_IN_FLIGHT`, which refuses `phase start qa <story>` for exactly that story | `qa` opens its own candidate root from canonical HEAD, like every other run, and the sequencer brokers the `test` key there. The order per story is `dev` → `devforgeai promote <run>` → `review` → `qa`, and `STORY_IN_FLIGHT` refuses this run while any run naming the story — `dev` or `review` — is `active` or `ready_to_promote`, so the `base` checkpoint the suite runs against already contains the promoted work. A failing criterion routes to a new `/dev {story} --fix` run, never to an edit inside this root. **Decision (D12):** testing promoted code in a clean root is the MVP form of the clean verification worktree; the detached read-only variant D8 moves into `12-post-mvp.md` stays deferred, and nothing here gates on it. |
| Two agents write into the root at once | The checkpoint diff cannot attribute a change, so `changed` matches no single receipt | The run file records the lease; the hook layer binds it at `SubagentStart` to the provider's agent identity, and a write from any other agent is denied at `PreToolUse` (`LEASE_HELD`). On Codex, where the pre-write event carries no identity, the root itself is the fence and the check is path-under-root. **Decision (D3, D6):** only `qa_writer` ever holds this skill's lease. |
| `AUTHOR-BRIEF.md` section 3 says every worker is read-only and section 6 requires every `must_not` block to end with "write any file, or run any build, test, lint or format command" | `qa_writer` compiled from that trailer is told not to do the job D1 gives it | `WRITE-MODEL-REVISION.md` is the decision register for this wave and supersedes the brief's write model wherever they differ. **Decision (D1, D9, as amended):** `qa_writer`'s trailer ends "write outside the candidate root, or run any command other than `devforgeai status`"; each judge's ends "write anywhere but `.devforgeai/work/<run>/evidence/<agent>/`, or run any build, test, lint or format command". Both lead with the job. |
| A judge is given no way to record its working | The criterion table has to fit in `issues`, which is bounded at ten rows, so a story with many criteria loses its evidence | Each judging worker writes one findings file under its own `.devforgeai/work/<run>/evidence/<agent>/` and names it in `evidence_refs`; `issues` stays the bounded summary, and `qa_writer` reads both. **Decision (D1, D6, D8a, as amended):** that scratch is run-scoped, gitignored, outside the candidate root and outside the fence, so it is never part of `changed` and is never promoted. |
| The compiled agent file is expected to carry the fence, the lease or the granted keys | An installed file drifts from the run file, and a judge appears to hold the phase's `test` key | The agent file carries `name`, `description`, `tools`, `model` and the body; the fence, the lease and the granted keys live in `.devforgeai/work/<run>/run.yaml` and are enforced by the hook dispatcher. **Decision (section 7g):** every Claude-only key — hooks, memory, background, `permissionMode`, `maxTurns`, `effort`, `disallowedTools`, `mcpServers`, colour and the git-worktree isolation key — is omitted, and `skills:` preloads nothing. |
| The eval workspaces are copies with no `.git` | An author writes worktree mode as the only materialisation and the run cannot open | The sequencer probes for a git repository at the project root and records `candidate.mode`: worktree mode when one exists with at least one commit, copy mode otherwise. The section 10 workspaces are copy mode, where a checkpoint is a tree-hash manifest plus a copy-aside and promotion copies the changed path's bytes under the lock. **Decision (D2):** one contract, two materialisations. |
| An earlier draft of section 7b said promotion is part of Handoff and that the sequencer promotes the report on a passing run | An author compiles a `SKILL.md` that never asks the user, and the report lands in the canonical checkout without a human decision | Promotion is never automatic. The last passing transition sets `runs.<run>.status: ready_to_promote` and writes a `REQUIRE_HUMAN` handoff whose only forward step is `devforgeai promote <run>`; the compiled `SKILL.md` runs that command only after the user confirms in the session, and that command writes the second handoff block, whose `next` is `/dev {next_story}`, `/retro {sprint}` or `/dev {story} --fix` by the report's `verdict`. Every run ends in two blocks. `STALE_BASE`, `DIRTY_TARGET` and `MERGE_CONFLICT` are refusals of `devforgeai promote <run>`, never of `devforgeai phase next`, and a run blocked before its last phase stays `active` and is not promotable at all. **Decision (D7, as amended; `10-sequencer-and-contracts.md` sections 5.4, 6 and 12.4):** the sequencer may not close a run onto the canonical tree on its own. |
| A criterion fails and the report is already written inside this run's root | An author has `qa_writer`, or a follow-up worker in the same run, fix the code in the qa root — a path outside the run's fence, denied at `PreToolUse`, and in a root that would be abandoned or promoted as a whole | A failing criterion never routes to an edit in the qa root. The repair is a new `dev` run, `/dev {story} --fix`, with the promoted qa report as its context; that run opens its own root and its own fence. One run per story at a time, one root per run. **Decision (D12):** `review` and `qa` run after promotion, each from canonical HEAD, and findings route forward to `dev` rather than backward into the judging root. |
| An earlier draft said a `REQUIRE_HUMAN` block closes the run, so "no flag resumes a closed one" | An author writes a repair route that opens a fresh run, and `devforgeai phase start` refuses it — the blocked run is still `active` — or writes `devforgeai phase fail --reason <text>` into every recovery row and throws away work the run had already checkpointed | A block is not a close. A `needs_user` result and an exhausted attempt budget both leave the run `active` with its lease released, its candidate root and checkpoints on disk, and `run.yaml#blocked_at` naming the phase. `devforgeai phase start` with the same skill and the same argument **resumes** that run at `blocked_at` with `attempts` reset to zero instead of refusing it, so `/qa {story}` is the whole recovery once the human has acted. Only another skill on the same story needs `devforgeai phase fail --reason <text>` first, and that call is what abandons the root. **Decision (`10-sequencer-and-contracts.md` sections 2, 3, 5.4 and 6):** blocked runs resume; they are not reopened. |
| The `verdict: findings` and `verdict: fail` rows were rendered as `/status` | An author promises a block that tells the user nothing about the defect the report just recorded, and the fenced report is never acted on | The sequencer selects the promoted block's row from the report's frontmatter `verdict`: `pass` keeps the document-run default `/status`, and `findings` or `fail` selects `/dev <story> --fix`. The run's `outcome` stays `pass` in all three cases, because reporting a defect is a passing run. **Decision (`10-sequencer-and-contracts.md` section 6, verdict rows; `02-skill-roster.md`):** the verdict picks the row, and the repair route is a fresh `dev` run. |

## 10. Success criteria and test cases

### Success criteria

- Triggers on the nine section 4 positives and on none of the nine near-misses.
- `SKILL.md` is under 500 lines and contains identity, the four-row phase list, the dispatch loop and the handoff table, and no phase guidance.
- `agents/` holds exactly four files, named for the four canonical workers; `references/` holds exactly five.
- Every `must_not` block ends with its role's closing line: the evidence-scratch line for the three judges, the candidate-root line for `qa_writer`. No judge's `tools` value exceeds `Read`, `Grep`, `Glob`, `Write` and `Bash(devforgeai status)`; `qa_writer`'s adds `Edit`. No agent file carries a `devforgeai run` surface.
- A judge's run leaves the candidate root byte-identical and writes exactly one file, under `.devforgeai/work/<run>/evidence/<agent>/`.
- Every agent file declares `writes`, and its value matches the phase's row in section 7c.
- The `SKILL.md` Bash grammar is no wider than `devforgeai status`, `devforgeai phase start qa <story> [--lenient]`, `devforgeai phase fail --reason <text>`, `devforgeai validate` and `devforgeai promote <run>`.
- No literal build, test, lint or format command appears in `SKILL.md`, in any reference file, or in any agent file.
- In a run, the primary-window transcript contains no read of the story, a test file or a source file, and no file write.
- Every completed run leaves `docs/reports/qa-<story>.md` conforming to the `qa-report` template header, with one `CRIT-NNN` row per numbered acceptance criterion, and the user's `devforgeai promote <run>` is what puts it in the canonical checkout.
- No file outside the run's fence differs in the candidate root between the `base` checkpoint the run opened at and the checkpoint the user promoted.

### Eval workspace, built once per eval

Each eval runs in its own workspace, built by copying files that already exist. No file is hand-edited; per-eval differences ship as the overlay directories already present in the fixture, or as the scratch tree the sequencer demo produces. The copied tree carries no `.git`, so the sequencer records `candidate.mode: copy` and materialises the candidate root by copy, manifest and copy-aside; the demo's own scratch tree initialises a git repository and exercises worktree mode.

1. Build the base tree.
   - Eval 1: run `bash docs/design/examples/hooks/demo_sequencer.sh` and copy the directory it prints as `scratch:` to `<output-dir>/qa-workspace/fixture-1/`. That tree is the fixture story with `tests/test_text.py` holding the three planned tests and a complete `tinyapp/text.py`, written by a real `dev` run and promoted into its working tree, which is the canonical state `qa` opens its own root from.
   - Evals 2 and 3: copy `docs/design/examples/fixtures/dev-tdd/` without `overlays/` to `<output-dir>/qa-workspace/fixture-<id>/`, then copy `docs/design/examples/fixtures/dev-tdd/overlays/eval-<id>/` over it.
2. Write `.devforgeai/state.yaml` containing exactly the three lines `version: 1`, `stories: {}`, `runs: {}`. Do not copy the fixture `state.yaml`: it holds an active run and every `devforgeai phase start` would be refused. Writing the minimal file also clears any enforcement block the demo left behind when its own run had not closed. Leave `.devforgeai/work/STORY-001/` in place where the demo produced it: it is this run's read-only input evidence and it lives under a different run id.
3. Copy `docs/design/examples/hooks/fixtures/.devforgeai/stack.yaml` into the copy's `.devforgeai/` if it is not already there. Its `python` section is the one the fixture story's `commands.source` anchors, and its `test` key writes the JUnit file the oracle reads.
4. Copy `dispatch.py`, `devforgeai.py` and `policy.py` from `docs/design/examples/hooks/` into `.devforgeai/hooks/`. The dispatcher resolves the sequencer as its own sibling, so the three files stay together.
5. Merge `docs/design/examples/hooks/settings.claude.json` into `<copy>/.claude/settings.json` so `SessionStart`, `PreToolUse`, `PostToolUse`, `SubagentStop` and `Stop` route to the dispatcher. Without this no receipt is ingested, no checkpoint is taken and no oracle runs.
6. Install the generated skill at `<copy>/.claude/skills/qa/` and run the prompt from inside the copy.

### evals/evals.json (used verbatim)

```json
{
  "skill_name": "qa",
  "evals": [
    {
      "id": 1,
      "prompt": "Run acceptance QA on STORY-001 in this directory. The story is a stand-alone fixture story outside docs/plan/, so open the run in lenient mode. Promote the run when the handoff asks for it; this instruction is that confirmation.",
      "expected_output": "All four phases pass, docs/reports/qa-STORY-001.md is written with one CRIT row per acceptance criterion, every row passed and verdict pass, the first handoff names devforgeai promote qa-STORY-001, and after that command runs the report is in the working tree.",
      "files": [],
      "expectations": [
        "The transcript shows `devforgeai phase start qa STORY-001 --lenient` exiting 0 and naming phase run_tests",
        "docs/reports/qa-STORY-001.md exists and its frontmatter carries story, template, template_version, status, verdict and depends_on",
        "docs/reports/qa-STORY-001.md contains the sections Criteria, Evidence, Regressions and Fix Guidance, and three rows whose ids match CRIT-0 followed by two digits",
        "Each criterion row names one of test_slugify_basic, test_slugify_unicode or test_slugify_empty and records it as passed",
        ".devforgeai/work/qa-STORY-001/ contains run_tests-result.json, criteria-result.json, evidence-result.json and report-result.json",
        ".devforgeai/work/qa-STORY-001/handoff.json names devforgeai promote qa-STORY-001 before that command runs, and has outcome pass and next /status after it",
        "No file under tinyapp/ or tests/ was created or modified during the run, in the working tree or in the candidate root"
      ]
    },
    {
      "id": 2,
      "prompt": "Run the qa skill on STORY-001 in this directory. Open the run in lenient mode; the story is a stand-alone fixture story.",
      "expected_output": "The gate refuses because criterion 3 carries an unresolved ASSUMPTION tag. No run opens, no worker is dispatched, no report is written, and the printed next step is /clarify STORY-001.",
      "files": [],
      "expectations": [
        "`devforgeai phase start qa STORY-001 --lenient` exits 1 and its stderr names the unresolved ASSUMPTION in the story body",
        "No .devforgeai/work/qa-STORY-001/ directory exists, so no handoff.json and no snapshot were written",
        "docs/reports/qa-STORY-001.md does not exist",
        "The final message names /clarify STORY-001 as the next step"
      ]
    },
    {
      "id": 3,
      "prompt": "Use the qa skill on STORY-001 in this directory. Only criterion 1 has a test and an implementation. Open the run in lenient mode.",
      "expected_output": "The run_tests transition refuses because the tests named for criteria 2 and 3 are absent from the results; run_tests exhausts its two attempts and the run blocks REQUIRE_HUMAN with no qa report written.",
      "files": [],
      "expectations": [
        "`devforgeai phase start qa STORY-001 --lenient` exits 0 and opens phase run_tests",
        ".devforgeai/work/qa-STORY-001/run_tests-report.md contains oracle problem rows naming test_slugify_unicode and test_slugify_empty",
        ".devforgeai/work/qa-STORY-001/handoff.json has outcome REQUIRE_HUMAN and next /status",
        "docs/reports/qa-STORY-001.md does not exist, because the report phase never ran",
        "No criteria-result.json, evidence-result.json or report-result.json exists in .devforgeai/work/qa-STORY-001/"
      ]
    }
  ]
}
```

Every eval requires the `test` runner named by the fixture's `python` stack section, because the `run_tests` transition brokers that key; without it the run ends `REQUIRE_HUMAN` on a missing runner rather than reaching its intended outcome. Eval 1 additionally depends on the demo it is built from completing its `green` phase, which needs the same runner. Section 11 records both.

Quick-mode results are generation feedback only: one enabled run per eval and no baseline. They are not runtime conformance evidence, and no section of this specification gates on such evidence; the deferred contract is `12-post-mvp.md#pm-02`.

## 11. Dependencies and compatibility

| Kind | Value |
|------|-------|
| Tools | `SKILL.md`: `Read`, `Agent`, and a Bash grammar no wider than `devforgeai status \| phase start qa <story> [--lenient] \| phase fail --reason \| validate \| promote <run>`. Judges (`test_runner`, `criteria_checker`, `evidence_collector`): `Read`, `Grep`, `Glob`, `Bash(devforgeai status)` and `Write`, admitted only under `.devforgeai/work/<run>/evidence/<agent>/`. Producer (`qa_writer`): those plus `Edit`, with writes admitted under the candidate root. No worker carries a `devforgeai run` surface; the `test` key is the `run_tests` phase's and the sequencer spends it. |
| MCP servers | none |
| Runtime | Python 3.11+ and PyYAML 6+ for the sequencer and the hook dispatcher. Worktree mode additionally needs `git` with a repository at the project root, at least one commit, `.devforgeai/work/` ignored, and both the provider's settings file and `.devforgeai/stack.yaml` tracked; the `SessionStart` self-test checks all five and fails `phase start` with `could_not_run: hook_fault` rather than falling back to copy mode. The project under test supplies the runner behind its `test` key, which must write JUnit XML to the section's `junit_path`, because the oracle reads per-test outcomes from that file rather than from stdout. For the fixture's `python` section that runner is `pytest`. |
| Project commands | `.devforgeai/stack.yaml#<anchor>`, resolved from the story's `commands.source` and pinned by `commands.hash`. Keys granted: `test` at `run_tests`, and `build` when the anchored section has `compiled: true`, because the `green` oracle runs the build before the suite; none at `criteria`, `evidence` or `report`. The sequencer spends both in the transition oracle, inside the candidate root. Keys are named, never literal commands. Contract: `10-sequencer-and-contracts.md` section 7. |
| DevForgeAI/Core compatibility | Requires the sequencer grammar, the story-anchored document run, and the `devforgeai.worker-result/v1` schema of `10-sequencer-and-contracts.md`, 2026-09-02. `NOT_APPLICABLE` for Research Core: `qa` is an anatomy-governed skill, not a Research adapter. |
| Other skills | Consumes `story` from `plan`, `dev-notes` from `dev`, `review-report` from `review`, and `techstack` and `stack` from `architect` or `onboard`. Produces `qa-report` for `dev` and `retro`. Invokes none of them: every edge is a handoff row. |

Deferred dependencies. Each names the `12-post-mvp.md` entry and what this skill does today without it.

| Deferred entry | What it would give `qa` | What `qa` does today |
|---|---|---|
| `12-post-mvp.md#pm-01` | runtime verification that each worker actually ran in its own context window | one subagent per phase is a declaration compiled into the target profile; a generated adapter is an uninstalled candidate that a human installs. |
| `12-post-mvp.md#pm-02` | conformance evidence from repeated provider trials | quick-mode eval results are generation feedback only, and no section gates on them. |
| `12-post-mvp.md#pm-04` | an operating-system write boundary, with only the report path writable | the fence is enforced by the `PreToolUse` deny at the candidate root, by the changed-set check at ingest and by the whole-tree policy scan, which is a fast-feedback layer rather than a kernel boundary. |
| the clean detached verification worktree that decision D8 of the write-model revision moves into `12-post-mvp.md`; its `PM-NN` id is assigned when that file is revised in this wave | a read-only detached tree, so the suite could not be influenced by anything outside the fence at all | the run opens its own candidate root from canonical HEAD, which under D12 already holds the promoted `dev` work, and the sequencer runs the `test` key there at the `base` checkpoint; that clean root is the MVP form, and nothing in this specification gates on the detached variant. |
| `12-post-mvp.md#pm-06` | eval modes beyond `skip` and `quick`, with the interactive viewer and the description-optimisation loop | eval mode is `skip` or `quick`; no third mode is named as available, and no section gates on an eval result. |
| `12-post-mvp.md#pm-09` | one `stack.yaml` describing several packages, so a story spanning two of them could be verified in one run | the story pins one anchored section and one `test` key; a cross-package story is out of scope. |
| `12-post-mvp.md#pm-10` | a clean-checkout validator that re-runs this acceptance check from a fresh clone as a required check | `devforgeai validate` is a read-only invariant scan over the active run, and the hook layer remains user-disableable. |

Frontmatter values derived from this table:

```yaml
compatibility: "Needs Python 3.11+ and PyYAML for the devforgeai sequencer and its hook dispatcher, installed with the DevForgeAI hook fragment for the selected target. The project's test key must write JUnit XML to the junit_path its stack.yaml section declares, because the oracle reads per-test outcomes from that file."
allowed-tools: "Read Agent Bash(devforgeai status) Bash(devforgeai phase start *) Bash(devforgeai phase fail *) Bash(devforgeai validate) Bash(devforgeai promote *)"
```

## 12. Targets

The generator produces one provider-neutral semantic package and a separate adapter for each selected target when frontmatter, invocation policy, or agent configuration differs. Provider-neutral resources may be shared. Adapter directories are not required to be byte-identical or symlinked.

| Target | Install path | Invocation | Subagents | Notes |
|--------|--------------|------------|-----------|-------|
| claude | `.claude/skills/qa/` plus `.claude/agents/` worker profiles | `/qa STORY-NNN [--lenient]` | one provider-native subagent per canonical worker name: three judges that write only their findings file in the run's evidence scratch, one writer that writes the report in the candidate root | Provider-specific frontmatter keys (`argument-hint`, `disable-model-invocation`) are compiled into this target's `SKILL.md` only. |
| codex | `.agents/skills/qa/` plus `.codex/agents/` profiles | `$qa STORY-NNN [--lenient]` | the same four, compiled per section 7g; the writer uses `apply_patch` and the writable-workspace sandbox mode | Portable six-field frontmatter only; policy goes in target-side configuration. |
| both | separate `.claude/skills/qa/` and `.agents/skills/qa/` adapters | as above | as above | Share only provider-neutral resources; validate each adapter independently. |

```yaml
metadata:
  version: "1.0.0"
  devforgeai-spec: "SKILL-SPEC-003"
  devforgeai-target: "both"
  devforgeai-anatomy: "true"
```

Not produced by skill-creator (deferred to DevForgeAI's skill-generator): provider-native `.claude/agents/*.md` and `.codex/agents/*.toml` worker profiles, provider-specific frontmatter keys for the Claude target, and concise `AGENTS.md` sections. Hook definitions are not per-skill: `init` installs the one dispatcher and its provider fragments from `09-hook-dispatcher.md`, and this specification ships none.

A generated package is an uninstalled candidate until those provider-native controls are present and independently validated. Generation or quick-mode success is not installation authority.

## 13. Constraints

- `SKILL.md` under 500 lines and roughly 5,000 tokens, holding only identity, the four-row phase list, the dispatch loop and the handoff table. Every other instruction lives in `references/<phase>.md`, `agents/<role>.md` or `assets/`. Splitting a phase's guidance into more reference files is the correct response to the line budget; cutting content is not.
- References one level deep from whichever file is loaded: `SKILL.md` links to `references/`, `agents/` and `assets/`; an `agents/*.md` links to `references/*.md`. Nothing links further.
- Hooks, state writes and phase advancement are not in the skill. Do not write an instruction the sequencer or a hook already enforces: the gate is `devforgeai phase start`, the fence is result validation plus the `PreToolUse` deny, and "the tests pass" is the `green` oracle at the `run_tests` transition.
- No literal build, test, lint or format command appears anywhere in the skill. A phase names a stack key; the sequencer resolves it from the hash-pinned section and runs it in the candidate root.
- No `README.md` inside the skill directory.
- No angle brackets in frontmatter. Description 724 characters, name 2 characters.
- Imperative voice. Explain why a step matters rather than shouting it; where an instruction is non-negotiable it is a gate, a fence or an oracle, and the text names that mechanism.
- Provide defaults, not menus. Procedures over declarations.
- No script is shipped, so no script prompts.
- A criterion row cites the test and the recorded report line that decided it. A verdict with no citation is a claim, and the report is consumed by skills that cannot ask a follow-up question.

## 14. Acceptance checks

Run these before reporting done and paste their output:

```bash
# frontmatter and naming (skill-creator's own validator)
python -m scripts.quick_validate <output-dir>/qa        # run from the skill-creator directory
# open-standard validator, if installed
skills-ref validate <output-dir>/qa
# size budget
wc -l <output-dir>/qa/SKILL.md                            # must be < 500
# every worker in section 7 has a prompt file, and no extra
ls <output-dir>/qa/agents/                                # test_runner.md criteria_checker.md evidence_collector.md qa_writer.md
# every agent file declares its role's write mode, and no worker holds a run key
grep -l 'writes: evidence' <output-dir>/qa/agents/*.md    # test_runner.md criteria_checker.md evidence_collector.md
grep -L 'devforgeai run' <output-dir>/qa/agents/*.md      # all four
# one reference file per phase, plus envelope.md
ls <output-dir>/qa/references/                            # run_tests.md criteria.md evidence.md report.md envelope.md
# no leftover placeholders
grep -rnE 'T[O]DO|T[B]D|\{\{' <output-dir>/qa || echo clean
# the spec battery
python3 docs/design/specs/verify.py --only v1,v2,v4
```

For non-Research anatomy skills, DevForgeAI skill-validator additionally checks: all sub-phase kinds present with Gate, Record and Handoff bound to sequencer operations; the inspection workers and the writer are different files; `must_not` and `writes` present in every agent file, `writes` in `candidate | evidence | none`, no judge's `tools` exceed `Read`, `Grep`, `Glob`, `Write` and `Bash(devforgeai status)`, and the writer's exceed those only by `Edit`; the `SKILL.md` Bash grammar is no wider than the five model-callable operations; handoff outcomes cover every status the skill can return, including `could_not_run`.

## 15. Provenance

| Source | Hash | Used for |
|--------|------|----------|
| docs/design/01-skill-anatomy.md#primary-window-contract | see frontmatter | sections 2 (R4), 7a, 13 |
| docs/design/01-skill-anatomy.md#evidence-home | see frontmatter | sections 6, 7d, 9 |
| docs/design/10-sequencer-and-contracts.md#4-per-skill-phase-registry | see frontmatter | sections 1, 2 (R9), 7b, 7c |
| docs/design/10-sequencer-and-contracts.md#3-2-defect-to-action-map-as-implemented | see frontmatter | sections 2 (R7), 5 (UC-3), 7c, 7f |
| docs/design/10-sequencer-and-contracts.md#3-4-re-resolving-sources-and-the-one-downgrade | see frontmatter | sections 7c, 9, 10 |
| docs/design/10-sequencer-and-contracts.md#5-4-transition-oracles | see frontmatter | sections 2 (R2, R8), 7c, 7d, 9 |
| docs/design/10-sequencer-and-contracts.md#6-handoff-envelope | see frontmatter | sections 7f, 9 |
| docs/design/10-sequencer-and-contracts.md#7-stack-yaml | see frontmatter | sections 7d, 11 |
| docs/design/11-artifact-registry.md#1-template-registry | see frontmatter | sections 2 (R1), 6 |
| docs/design/11-artifact-registry.md#3-depends-on-edges | see frontmatter | sections 2 (R3), 6, 7d |
| docs/design/02-skill-roster.md#handoff-decision-tables | see frontmatter | sections 7f, 9 |
| docs/design/05-subagent-sets.md#sets-per-skill | see frontmatter | sections 7b, 7e, 9 |
