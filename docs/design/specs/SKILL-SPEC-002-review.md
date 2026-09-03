---
template: skill-spec
template_version: 1
id: SKILL-SPEC-002
skill_name: review
target: both
status: approved
author: "DevForgeAI plan skill"
date: 2026-09-02
depends_on:
  - source: docs/design/01-skill-anatomy.md#primary-window-contract
    hash: sha256:6556607035516c49ee43fe2bbeffe1a74e898889d84be00c9a05fdf751d209b6
    excerpt: "For an anatomy-governed skill, the primary window (provider entry adapter + skill orchestration) does light, trivial work only. It dispatches workers and calls the sequencer. It never writes state, never advances a phase, and never decides that a phase passed."
  - source: docs/design/01-skill-anatomy.md#handoff-contract
    hash: sha256:dc50836dc15a928b0c4758ef3a671c6f78d5c7db7ea207c923b917d89faa9e96
    excerpt: "Every anatomy-governed skill run ends with a handoff. The sequencer writes `.devforgeai/work/<run>/handoff.json` at `phase next` and at `phase fail`; the block below is that file's rendering, and it is the only handoff the primary window prints."
  - source: docs/design/10-sequencer-and-contracts.md#4-per-skill-phase-registry
    hash: sha256:7c1d67f1154e49247e5dc178fcc1512bdbd53af378c360aeafe69bffed1136ab
    excerpt: "| review | 4 | `report` | `review_writer` | docs | 2 | — | document | — |"
  - source: docs/design/10-sequencer-and-contracts.md#3-4-re-resolving-sources-and-the-one-downgrade
    hash: sha256:722dadc1737749e30d244f222aaa1d8b845bc93f4a573b16f662719e58b49bcd
    excerpt: "The story gate re-resolves every `provenance[]` and `context[]` entry as well as `commands`."
  - source: docs/design/10-sequencer-and-contracts.md#5-2-validation-order
    hash: sha256:9cf7115cdfa637023edc22cbdf5f64c106b1eba340598c8dc97b68361cb76b0f
    excerpt: "when the phase is report-producing (`review`/`report`, `qa`/`report`, `skill-validator`/`report`), `evidence_refs` names exactly one report inside the fence, and that report's frontmatter carries a `verdict` in `pass`, `findings`, `fail`."
  - source: docs/design/10-sequencer-and-contracts.md#5-4-transition-oracles
    hash: sha256:076840ec9db03155bc9edcceb587e2aa1ca8bf3849e7a8b742f788d1a3b2315f
    excerpt: "the phase declared `writes: docs` and `changed[]` is non-empty, unless it is marked conditional, in which case an empty change set needs a non-empty `note`; every changed path exists in the root with the bytes the checkpoint will hold"
  - source: docs/design/10-sequencer-and-contracts.md#6-handoff-envelope
    hash: sha256:52cf474c332c7d8a02ad1b1abac51d852d5f54c30bf5126deb8a5b18cde77206
    excerpt: "| `review`, promoted, `verdict: findings` or `fail` | `/dev <arg> --fix` |"
  - source: docs/design/11-artifact-registry.md#1-template-registry
    hash: sha256:fabb8d2f142dcde1a31bc53768f8a46d01cac3ea4a7f6b73db22479cc89b5553
    excerpt: "`review-report` | `.devforgeai/skills/review/templates/review-report.md` | 1 | `^FIND-[0-9]{3}$` | story, template, template_version, status, verdict, depends_on | Compliance, Security, Style, Findings"
  - source: docs/design/11-artifact-registry.md#2-artifact-path-patterns
    hash: sha256:858455b885ac6c1ddbe427a433ba715f7266d08b90e105135172877e29ea0ecc
    excerpt: "For a document run the run id is `<skill>-<arg>`, so the rendered view of `review`'s `report` phase is `docs/reports/review-review-STORY-001-report.md`."
  - source: docs/design/02-skill-roster.md#handoff-decision-tables
    hash: sha256:1dac784b4670cc7559f323011dfe304dfe8c0baf349063162f90d76d902c5d3c
    excerpt: "| review | pass (`verdict: pass`) | `/qa {story}` |"
  - source: docs/design/05-subagent-sets.md#sets-per-skill
    hash: sha256:f2957217c9af147e4a7ea03749cbe6efda266bd56d403f39aa25c9a655872609
    excerpt: "review | compliance-checker, security-checker, style-checker, review-writer"
  - source: docs/design/08-story-specification.md#what-a-story-must-carry-and-why
    hash: sha256:c8c466567a5e85ebcd61de29320f8c72f581f99a9b6e8d7dbd98e80f04861fcb
    excerpt: "`risk_tier`, `size` | estimator, review | Size L must be split; risk raises review depth."
---

# Skill Specification: review

A stranger with no conversation history must be able to build this skill from this document alone. Every question the generator would otherwise ask is answered below. No unresolved authoring assumption remains; every open item this specification inherited is resolved in writing in section 9.

`review` opens a story-anchored document run. Its argument is a story id, the same story gate that `dev` runs re-runs here, and the story's `commands`, `test_plan` and `gate_policy` map are copied into the enforcement block. Its fence is the report path, so its workers cannot touch code.

The run gets its own candidate root, created by the sequencer at `devforgeai phase start` from canonical HEAD, exactly as every other run does. It does not attach to the story's `dev` root. The order per story is `dev` → `devforgeai promote <run>` → `review` → `qa`, and `STORY_IN_FLIGHT` enforces it: `devforgeai phase start review <story>` is refused while that story's `dev` run is `active` or `ready_to_promote`. So by the time this run opens, the story's code is in the canonical tree, and the fresh root holds it at the `base` checkpoint. The three inspection workers read that checkpoint and change nothing anywhere: each declares `writes: none`, carries no write tool, and returns its detailed evidence in the receipt's `findings` string, which the sequencer persists verbatim to `.devforgeai/work/<run>/evidence/<agent>/findings.md` — a run-scoped path the worker cannot choose, gitignored and never promoted — where `review_writer` reads it. `review_writer` is the run's one producer: it writes the report inside the root, under the run's fence, with `Edit` and `Write`, and the report reaches the canonical checkout only when the user runs `devforgeai promote <run>`. Judging promoted code in a clean root is the MVP form of the clean verification worktree; the detached read-only variant that decision D8 moves into `12-post-mvp.md` stays deferred.

Two `writes` vocabularies meet here and mean different things. The registry phase's mode — `none` for the three inspections, `docs` for the report — says what a phase may change inside the candidate root. The worker header's `writes` — `candidate` or `none` — says whether that agent is given a write tool at all. An inspection worker is `writes: none` in both vocabularies: it changes nothing inside the root, and it carries no `Write`, `Edit` or `apply_patch` anywhere. Its evidence reaches disk only through the `findings` string the sequencer persists for it.

## 0. Generator instructions

These instructions are addressed to the skill-generating agent (Anthropic's `skill-creator` skill, or DevForgeAI's `skill-generator`). They replace its interview.

### Cold-session prompt

Paste this into a fresh session from the repository root:

```
Use the skill-creator skill to build the skill specified in docs/design/specs/SKILL-SPEC-002-review.md.
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
6. **Output location** is given in the prompt. Create `<output-dir>/review/`. Do not write anywhere else except the `review-workspace/` sibling that eval runs require.
7. **On ambiguity, stop before output.** If the spec is still `draft`, contains an unresolved authoring assumption, omits a section, contradicts itself, or leaves a decision this document does not make, do not guess and do not write candidate skill files. End with a list titled `SPEC GAPS` naming each section and question. The spec author fixes and approves the spec before re-running.
8. **Fidelity over creativity.** Use the description in section 3 verbatim. Use the worker contracts in section 7e verbatim as `agents/<role>.md` bodies, adding only the four-section framing `templates/agent-md.md` fixes (Job, Inputs, Rules, Receipt). Use the phase guidance in section 7d verbatim as `references/<phase>.md`. Do not add steps, tools, or behaviours the spec does not mention.
9. **Finish with the acceptance checks** in section 14 and include their output in your final message.

## 1. Identity

| Field | Value |
|-------|-------|
| name | `review` (kebab-case, 6 chars, equals the directory name, no `claude`/`anthropic` prefix) |
| title | Story Review |
| purpose | Judge one implemented story against the constitution, security expectations and project style with three independent judging workers that change no code, and record the verdict as a fenced report a later skill can cite. |
| category | devforgeai-phase |
| version | 1.0.0 (skill-package version written to `metadata.version`; not the DevForgeAI or Research Core version) |

## 2. Problem and requirements

**Without this skill:** the same window that wrote the code judges it. The judgement is shaped by what the author already decided, so the constitution clause the change violated is exactly the clause nobody re-reads, and "looks fine" is recorded as a review. Three failure modes from `07-purpose-and-enforcement.md` section 2 apply directly: a done declaration because a file exists, a validator whose non-zero exit gates nothing, and a gate that is prose the model may ignore. There is no artifact afterwards that `qa` or `retro` can cite, so a finding is lost the moment the session ends.

| ID | Kind | Requirement |
|----|------|-------------|
| R1 | explicit | Take one story id and produce `docs/reports/review-<story>.md` against the `review-report` template. Source: `11-artifact-registry.md` section 1 and section 2. |
| R2 | explicit | Judge compliance, security and style in three separate phases, each dispatching one worker in its own context window. Source: `10-sequencer-and-contracts.md` section 4 registry. |
| R3 | explicit | Run before `qa`, so `qa` tests reviewed code. Source: `02-skill-roster.md` per-skill detail for review. |
| R4 | implicit | Change no code: the three inspection workers write nothing at all, the run's fence is the report path only, and a change anywhere else in the candidate root fails the phase at ingest. Source: write-model decisions D4 and D13. |
| R5 | implicit | Re-gate the story on entry rather than trusting that `dev` gated it: the constitution may have changed since. Source: `01-skill-anatomy.md` gate section. |
| R6 | implicit | Every finding carries an id matching `^FIND-[0-9]{3}$` and cites the file, the line range and the constitution or techstack anchor it violates, so `dev` can act on it without re-deriving it. Source: `11-artifact-registry.md` section 1 id pattern. |
| R7 | discovered | The report's `verdict` field, not the worker `status`, carries the judgement. A worker returns `pass` when it completed its inspection, whatever it found; the phase fails only when the worker could not do its job. Source: `10-sequencer-and-contracts.md` section 3.1, which defines status as a worker outcome and never as a quality grade. |
| R8 | discovered | No phase of `review` grants a stack command key, so this skill runs nothing and its verdicts rest on the evidence `dev` recorded plus the promoted code at this run's own `base` checkpoint. Source: `10-sequencer-and-contracts.md` section 4, review rows, run keys column, and write-model decision D8a. |
| R9 | discovered | The report is written in the candidate root and reaches the canonical checkout only when the user runs `devforgeai promote <run>` on a run the last passing transition marked `ready_to_promote`; that command fast-forwards under the sequencer's lock and is refused with `STALE_BASE` or `DIRTY_TARGET` rather than merging. Promotion is never automatic and is never part of Handoff. Source: write-model decisions D2 and D7 as amended. |
| R10 | discovered | `review_writer` holds the run's lease while it writes; the three inspection workers hold none and may read the checkpoint concurrently. Source: write-model decisions D3 and D6. |
| R11 | discovered | Each inspection worker writes nothing. It returns its detailed evidence in the receipt's `findings` string, at most 16,384 UTF-8 bytes, and the sequencer persists that string verbatim to `.devforgeai/work/<run>/evidence/<agent>/findings.md` at the identity-bound `SubagentStop`; `issues[]` stays the bounded routing summary `review_writer` and the handoff quote. The worker chooses neither the path nor the name, and the persisted file is gitignored, outside the candidate root and the fence, and never promoted; `review_writer` reads it by path. Source: write-model decision D13. |
| R12 | discovered | The run opens its own candidate root from canonical HEAD and never attaches to the story's `dev` root; `STORY_IN_FLIGHT` refuses `devforgeai phase start review <story>` while that story's `dev` run is `active` or `ready_to_promote`, so this skill judges promoted code. A finding that needs a code change routes to a new `/dev {story} --fix` run, never to an edit in this run's root. Source: write-model decision D12. |

## 3. Description

The exact frontmatter `description`. Written as a YAML block scalar so colons are safe; no angle brackets anywhere.

```yaml
description: >
  Review one implemented DevForgeAI story before it goes to QA: dispatch the
  compliance, security and style workers over the applied diff and the story's
  constitution excerpts, then write docs/reports/review-STORY-NNN.md with one
  numbered finding per defect. Use this skill whenever someone asks for a code
  review, a second pair of eyes, a security or style pass, or a check that a
  change follows the architecture or coding standards before a pull request,
  and whenever a dev run has just finished a story. Do NOT use it to write the
  code (use dev), to execute acceptance criteria and collect test evidence
  (use qa), to audit traceability across the whole plan (use analyze), or to
  compare documents against the current tree (use drift).
```

Character count: 735 / 1024.

## 4. Trigger set

Realistic queries, varied in phrasing, explicitness, detail and complexity. The near-misses share vocabulary with `review` and belong to an adjacent skill. The generator uses this list verbatim.

```json
[
  {"query": "/review STORY-004", "should_trigger": true},
  {"query": "dev just finished STORY-001, can you look over it before I raise the PR", "should_trigger": true},
  {"query": "give the STORY-012 diff a second pair of eyes against our constitution please", "should_trigger": true},
  {"query": "security pass on the changes for STORY-007, it touches the session store", "should_trigger": true},
  {"query": "does the code for docs/plan/billing/stories/STORY-021.md follow our style rules? be honest", "should_trigger": true},
  {"query": "check STORY-015 for anything that breaks the architecture doc before qa gets it", "should_trigger": true},
  {"query": "i want the findings written down somewhere qa and retro can read later, story is STORY-003", "should_trigger": true},
  {"query": "code review STORY-009, risk tier is HIGH so go deep", "should_trigger": true},
  {"query": "the constitution says no ORM. did STORY-002 sneak one in?", "should_trigger": true},
  {"query": "run every acceptance criterion for STORY-004 and record the evidence", "should_trigger": false},
  {"query": "re-run the failing tests for STORY-004 and tell me which criteria are still red", "should_trigger": false},
  {"query": "implement STORY-004, tests first", "should_trigger": false},
  {"query": "fix the findings you just listed for STORY-004", "should_trigger": false},
  {"query": "our sourcetree doc is out of date with the actual repo layout, show me where", "should_trigger": false},
  {"query": "which PRD requirements have no story yet", "should_trigger": false},
  {"query": "review the sprint and tell me what we learned", "should_trigger": false},
  {"query": "check whether the generated skill matches its spec and the provider rules", "should_trigger": false},
  {"query": "amend the constitution to allow a query builder, and write the ADR", "should_trigger": false}
]
```

## 5. Use cases

### UC-1: Straight after dev
- **User says:** "/review STORY-001"
- **Steps:** 1. The adapter calls `devforgeai phase start review STORY-001`; the document fence gate checks `docs/reports/review-STORY-001.md`, and because `review` is story-anchored the full story gate runs too, re-resolving every `provenance[]`, `context[]` and `commands` reference and copying the story's `test_plan`, `commands` and `gate_policy` map into the enforcement block. Because the story's `dev` run was promoted before this call, `STORY_IN_FLIGHT` does not fire, and the run opens its own candidate root from canonical HEAD at the `base` checkpoint. 2. `compliance_checker` reads the code at that checkpoint and the story's constitution excerpts and returns findings in its receipt. 3. `security_checker` and `style_checker` follow, each in its own window. 4. `review_writer` writes `docs/reports/review-STORY-001.md` inside the root; the sequencer derives the changed set from the checkpoint diff, confirms it is the fence path alone, and the `document` oracle confirms the file is on disk. 5. The run is marked `ready_to_promote` and the first handoff block names `devforgeai promote review-STORY-001`. 6. The user confirms; that command copies the report into the canonical checkout and writes the second block, which names `/qa STORY-001`.
- **Result:** one fenced report with a `verdict`, numbered findings, four result and report pairs under `.devforgeai/work/review-STORY-001/`, and two handoff blocks.

### UC-2: A high-risk story
- **User says:** "code review STORY-015, risk tier is HIGH so go deep"
- **Steps:** 1. The story's `risk_tier` is already in the story the gate read; the adapter passes the story id only. 2. Each worker reads `risk_tier` from the story and reports at the depth that tier calls for, recording the tier in its note. 3. The report records the tier beside the verdict so `retro` can correlate depth with defects found.
- **Result:** the same artifact shape, with findings whose density reflects the declared tier rather than the reviewer's mood.

### UC-3: The story moved under the reviewer
- **User says:** "/review STORY-011"
- **Steps:** 1. The story gate re-resolves a `context[]` entry whose source has changed since `plan` sliced it and reports `stale-hash`. 2. The sequencer exits 1 with the defect list on stderr, opens no run and touches no candidate root. 3. The adapter prints the refusal and the repair route.
- **Result:** no report is written against a story whose constitution excerpt no longer matches its source, and the next step is `/plan {slug} --reslice STORY-011`.

## 6. Inputs and outputs

### Inputs
| Input | Format | Example file | Required |
|-------|--------|--------------|----------|
| story id | positional argument matching `^STORY-(HOTFIX-)?[0-9]{3}$` | `STORY-001` | yes |
| story | markdown, `story` template v3, owned by `plan` | `docs/design/examples/fixtures/dev-tdd/STORY-001.md` | yes; resolved by the sequencer, never read by the primary window |
| the code under review | project language, the paths the story's `write_fence` names, read at the `base` checkpoint of this run's own candidate root, which is canonical HEAD after the story's `dev` run was promoted | `docs/design/examples/fixtures/dev-tdd/tinyapp/text.py` | yes |
| dev evidence | markdown and JSON under `.devforgeai/work/<story>/` | `.devforgeai/work/STORY-001/green-report.md` | no; absent when `dev` has not run |
| `.devforgeai/state.yaml` | YAML | `docs/design/examples/hooks/fixtures/.devforgeai/state.yaml` | yes |
| `--lenient` flag | boolean, forwarded to `devforgeai phase start` | | no; refused for any story under `docs/plan/` |

`review` consumes `story` from `plan`, `dev-notes` from `dev`, and `constitution`, `techstack` and `adr` from `architect` or `amend`, every one of which has a producer in `11-artifact-registry.md` section 5. It reads the architecture set only through the story's `context[]` excerpts, which the gate re-resolved.

### Outputs
| Output | Format | Location | Template |
|--------|--------|----------|----------|
| review report | markdown with frontmatter | `docs/reports/review-<story>.md`, written in the candidate root and reaching the canonical checkout only when the user runs `devforgeai promote <run>` | `review-report` (`.devforgeai/skills/review/templates/review-report.md`), seeded by `assets/review-report.md` |
| phase result | JSON, the validated envelope plus the sequencer's added fields | `.devforgeai/work/review-<story>/<phase>-result.json` | none; written by the sequencer |
| phase report | markdown | `.devforgeai/work/review-<story>/<phase>-report.md` | none; rendered by the sequencer |
| rendered report view | markdown | `docs/reports/review-review-<story>-<phase>.md` | none; the sequencer's per-phase view, distinct from the fenced report above |
| handoff | JSON plus its printed rendering | `.devforgeai/work/review-<story>/handoff.json` | `handoff`, rendered by the sequencer |

Evidence lives outside the candidate root, in the canonical checkout's gitignored `.devforgeai/work/<run>/`, and the sequencer is its only writer. A receipt's `evidence_refs` entry is therefore either a path under the candidate root or a path under `.devforgeai/work/<run>/`.

`review` owns exactly one template, `review-report`; `11-artifact-registry.md` section 1 records `qa`, `dev` and `retro` as its consumers.

### Output template

The `review-report` shape, which `assets/review-report.md` seeds and `review_writer` fills:

```
---
story: STORY-NNN
template: review-report
template_version: 1
status: complete
verdict: pass | findings
depends_on:
  - source: docs/plan/<slug>/stories/STORY-NNN.md
    hash: sha256:<64 hex>
  - source: docs/architecture/constitution.md#<anchor>
    hash: sha256:<64 hex>
---

## Compliance

One line per constitution or techstack excerpt checked, with the applied paths it governs and whether the change honours it.

## Security

One line per class checked (input handling, secrets, authorisation, injection surface, error disclosure), with the applied paths inspected.

## Style

One line per style rule from the constitution excerpt, with the applied paths inspected.

## Findings

- FIND-001 | compliance | tinyapp/text.py#L12-L18 | constitution.md#data-access | what the change does and which clause it breaks
- FIND-002 | security | severity and the same three columns
```

`verdict` is `pass` when Findings is empty and `findings` otherwise. `depends_on` lists the story and every constitution or techstack anchor the report cites, each with the digest the gate resolved, which is the `depends_on` edge `11-artifact-registry.md` section 3 records for `review-report`.

### Return envelope (DevForgeAI-anatomy skills only)

One schema, both providers: `devforgeai.worker-result/v1`, normative in `schemas/devforgeai/v1/worker-result.schema.json`. A worker's final message is exactly this one JSON object — a receipt for work already done in the candidate root, not a proposal. The three inspection workers do no work in the root at all and return an empty `claimed_paths`; `review_writer` claims the one report path it wrote.

```yaml
schema: devforgeai.worker-result/v1
run: "review-STORY-001"
skill: "review"
phase: "compliance | security | style | report"
agent: "compliance_checker | security_checker | style_checker | review_writer"
status: pass | fail | needs_user | could_not_run
reason_code: runner_missing | timeout | network | hook_fault | provider_tool_refused | prerequisite_missing | checkpoint_fault   # required only when status is could_not_run
candidate: {id: "review-STORY-001", input_checkpoint: "base | compliance | security | style"}
claimed_paths: ["docs/reports/review-STORY-001.md"]   # report phase only; empty everywhere else
evidence_refs: [".devforgeai/work/review-STORY-001/compliance-report.md"]   # at most 16
note: "at most three lines"
issues: [{id, kind, text}]              # at most 10
findings: "the inspection worker's detailed evidence"  # judges only, at most 16384 UTF-8 bytes: required on pass or fail, optional on needs_user or could_not_run
next: ""                                # refused: no review phase declares rewind_to
```

The `reason_code` set separates infrastructure failures that look alike from the primary window. `provider_tool_refused` is the provider declining a tool call before any DevForgeAI hook ran — the case that made this specification's inspection workers `writes: none`. `prerequisite_missing` is a worktree-mode prerequisite the `SessionStart` self-test found absent. `checkpoint_fault` is a checkpoint the sequencer could not create, read or reset. `hook_fault` stays reserved for a missing worker identity on the stop event or a malformed receipt. All of them roll up to `INFRA_FAILURE`.

A judging phase returns `findings` and writes nothing. `findings` is required when a judge returns `pass` or `fail`, because those are the statuses whose working `review_writer` reads, and optional when it returns `needs_user` or `could_not_run`; the same 16,384-byte bound applies either way. `review_writer` never carries it on any status. At the identity-bound `SubagentStop`, after the receipt validates, the sequencer writes the decoded string verbatim to `.devforgeai/work/<run>/evidence/<agent>/findings.md` — a fixed path the worker cannot choose or name — and `review_writer`, the handoff and `<phase>-result.json` reach it by that path. That is persistence of a returned result, not a merge into the tree. A `findings` string over 16,384 UTF-8 bytes is refused like any other receipt defect and is never truncated; a `findings` key on `review_writer`'s receipt is refused as an unknown key would be.

The `findings` body reaches the primary window as part of the subagent's result, exactly as any subagent result does: a hook can validate a final message but cannot suppress it. What stays isolated is the worker's transcript, its file reads, its tool traffic and its intermediate reasoning. The receipt still carries no report body and no code.

`gate_policy` (`BLOCK | REQUIRE_HUMAN | WARN | OFF`) is a defect-to-action map declared in the consumed story, never a status returned here. An unknown key is refused. The report's own frontmatter carries `verdict`, and the sequencer reads it from the file `evidence_refs` names: it selects the handoff row and therefore `next`, while the run's `status` and the handoff's `outcome` stay `pass`, because reporting a defect is a passing run.

## 7. Procedure

The body of `SKILL.md` is section 7a plus the phase list and the handoff table. Section 7d becomes `references/<phase>.md`, one file per registry phase. Section 7e becomes `agents/<role>.md`, one file per worker.

### 7a. Steps

1. Parse the story id and `--lenient` from the invocation. Nothing else is parsed and nothing is read — why: whatever this window reads stays in it for all four phases, and a reviewer's window that already holds the code cannot dispatch an independent opinion of it.
2. Run `devforgeai phase start review <story-id>`, appending `--lenient` only when the user supplied it. Exit 0 opens the run, creates its own candidate root from canonical HEAD and names phase `compliance`, printing the run id, the candidate root, the fence and the granted keys; exit 1 is a gate refusal with the defect list on stderr, and `STORY_IN_FLIGHT` is one of its reasons when the story's `dev` run is still `active` or `ready_to_promote`; exit 2 is a usage error — why: `review` is story-anchored, so this one call runs both the document fence gate and the whole story gate, and there is no way to open a phase without them; and this skill judges promoted code, so the root is created from canonical HEAD rather than attached to the story's `dev` root.
3. On a non-zero exit, print the sequencer's message and the matching row from the handoff table in section 7f, then stop. Do not repair the story — why: repair belongs to the skill that owns the template, and this skill owns only its report.
4. Dispatch the worker the sequencer named, in its own context window. Paste the `devforgeai status` block into the prompt — it names `run`, `candidate.root`, `phase`, `fence` and `granted_keys` — and add the story id and the paths of the earlier phases' reports under `.devforgeai/work/review-<story>/` — why: paths and ids only; restating the story's criteria into the prompt replaces the gated artifact with a paraphrase, and the status block is the one place the root and the fence are stated, so a worker never guesses where the code it judges lives.
5. Read the returned receipt and branch on `status` alone. A worker that inspected its subject returns `pass` whatever it found: findings travel in `issues`, and the verdict is written into the report at phase 4, where the sequencer reads it from the report's frontmatter — why: `status` is a worker outcome, not a quality grade, and treating a finding as a phase failure would retry the same inspection until the attempt budget blocked the run.
6. Run `devforgeai status` and read `enforcement.phase`, or treat an empty enforcement block as a closed run. Dispatch that phase's worker and repeat from step 4 — why: the sequencer's `SubagentStop` message names the same phase, but the enforcement block is the record it wrote, so reading it works identically on both providers and after a session restart, and the attempt counters, the limits and the lease that bound the loop live in the run file beside it.
7. Print the handoff block the sequencer rendered, verbatim. When the gate refused before the run opened, print the sequencer's stderr and the section 7f row instead — why: rule 8 of the handoff rendering rules forbids adding a fact the envelope does not hold.
8. When the user abandons the review mid-run, call `devforgeai phase fail --reason <text>` so the run closes with a `BLOCK` handoff rather than staying active and refusing the next `devforgeai phase start` for every skill.
9. Run `devforgeai promote <run>` only after the printed handoff says the run is `ready_to_promote` and the user has confirmed the promotion in this session, then print the second handoff block that command renders — why: promotion is never automatic. The last passing transition marks the run `ready_to_promote` and writes a `REQUIRE_HUMAN` handoff whose only forward step is this command, so whether the report reaches the canonical checkout is the user's decision and not the sequencer's.

Bash grammar for this skill is exactly `devforgeai status`, `devforgeai phase start review <story> [--lenient]`, `devforgeai phase fail --reason <text>`, `devforgeai validate` and `devforgeai promote <run>`. No `review` phase grants a stack key, so no worker of this skill ever calls `devforgeai run`.

### 7b. Sub-phases and workers

Gate, Record and Handoff dispatch no LLM: they are `devforgeai` sequencer operations. Slice dispatches none either, for the reason recorded in section 9.

| # | Sub-phase | Performed by | Writes |
|---|-----------|--------------|--------|
| 0 | Gate | sequencer: `devforgeai phase start review <story>`, which refuses on `STORY_IN_FLIGHT` while the story's `dev` run is `active` or `ready_to_promote`, and otherwise creates the run's own candidate root from canonical HEAD | sequencer |
| 1 | Slice | no worker; the story's `context[]` bundle is the slice, produced by `plan` and re-resolved at the gate | none |
| 2 | Work: `compliance` | worker: `compliance_checker` | evidence |
| 3 | Work: `security` | worker: `security_checker` | evidence |
| 4 | Work: `style` | worker: `style_checker` | evidence |
| 5 | Write: `report` | worker: `review_writer` | candidate |
| 6 | Record | sequencer: `devforgeai phase next` at every transition, which checkpoints the root | sequencer |
| 7 | Handoff | sequencer: `devforgeai phase next`, or `devforgeai phase fail`. A passing last transition marks the run `ready_to_promote` and renders the first block, a `REQUIRE_HUMAN` handoff naming `devforgeai promote <run>`; `devforgeai promote <run>`, run only after the user asks for it, renders the second | sequencer |

`review` has no separate Review sub-phase: the whole skill is the Review sub-phase of the pipeline, and its own critic would be a critic of a critic. The three inspection workers are independent of each other and of `review_writer`, which renders their findings and adds none of its own, so the persona-and-critic separation `01-skill-anatomy.md` requires holds between `dev`'s workers and these. Each worker runs as its own provider-native subagent, which is what gives the phase its own context window; runtime verification that it did is `12-post-mvp.md#pm-01`.

Promotion is not part of Handoff. The last passing transition sets `runs.<run>.status: ready_to_promote` and writes a `REQUIRE_HUMAN` handoff whose one forward command is `devforgeai promote <run>`; the root and its checkpoints stay on disk and no canonical byte moves. The compiled `SKILL.md` runs that command only after the user confirms in the session, and the sequencer then performs it under `.devforgeai/lock`: the report is fast-forwarded into the canonical checkout, and the second handoff block is written. Canonical movement since `base_ref` refuses the command with `STALE_BASE`, which the sequencer resolves in worktree mode by rebasing the root, re-running the last transition oracle and retrying the fast-forward, and reports as `needs_user` in copy mode; a dirty canonical report file refuses it with `DIRTY_TARGET` and nothing is copied. A run blocked before its last phase never reaches `ready_to_promote` at all: it keeps `status: active` with its lease released, is not promotable, and `devforgeai phase fail --reason <text>` is what abandons it.

`05-subagent-sets.md` names these workers `compliance-checker`, `security-checker`, `style-checker` and `review-writer`. Those hyphenated forms are display aliases; the canonical registry names below are what `agent_type` is compared against.

### 7c. Evidence and gate table

One row per registry phase, in phase order. `<run>` is `review-<story>`, the `<skill>-<arg>` form a document run uses. The gate in row 1 runs once, at `devforgeai phase start`, and binds every later phase through the enforcement block it writes.

| phase | worker | deterministic gate check | gate_policy | evidence file | transition oracle |
|---|---|---|---|---|---|
| `compliance` | `compliance_checker` | document fence gate: `docs/reports/review-<story>.md` is declared, repository-relative, free of `..`, and not sequencer-owned; no run that is `active` or `ready_to_promote` names this story (`STORY_IN_FLIGHT`), which is what makes the story's `dev` work promoted before this run opens; story gate, because the skill is story-anchored: template v3, `status: ready`, no `ASSUMPTION:` before `## Clarifications`, `blocked_by` chain done, every `provenance[]` and `context[]` entry re-resolved to its recorded digest, `write_fence`, `test_plan` and `commands` present, `commands.hash` equal to the current `stack.yaml` digest, the anchored section satisfying the `stack.yaml` contract; at ingest, `writes: none` requires an empty `claimed_paths` and a candidate root unchanged since the `base` checkpoint the run opened at, which the worker cannot violate because it carries no write tool; its receipt carries a `findings` string — required on `pass` or `fail`, optional on `needs_user` or `could_not_run` — which the sequencer persists to `.devforgeai/work/review-<story>/evidence/compliance_checker/findings.md` after the receipt validates | the story's map, copied into the enforcement block: `unresolved_assumption: BLOCK`, `stale_hash: BLOCK`, `unresolvable_source: BLOCK` (downgraded to a recorded warning only by `--lenient` on a story outside `docs/plan/`, or by `WARN`/`OFF` on a `scope: hotfix` story), `write_fence_violation: BLOCK` | `.devforgeai/work/review-<story>/compliance-result.json`, `.devforgeai/work/review-<story>/compliance-report.md` | `report_only`: no file outside the fence changed since the gate snapshot and the whole-tree package and import policy holds |
| `security` | `security_checker` | `writes: none`: the worker carries no write tool at all, `claimed_paths` is empty and nothing changed in the root; its `findings` string is persisted by the sequencer to `.devforgeai/work/review-<story>/evidence/security_checker/findings.md`; the receipt's `agent` resolves to `security_checker` and matches the stop event's `agent_type` | `write_fence_violation: BLOCK` | `.devforgeai/work/review-<story>/security-result.json`, `.devforgeai/work/review-<story>/security-report.md` | `report_only`: as `compliance` |
| `style` | `style_checker` | as `security`, with its `findings` persisted to `.devforgeai/work/review-<story>/evidence/style_checker/findings.md`; the phase grants no command key, so `devforgeai run` is refused for this worker on the key as well as on the lease | `write_fence_violation: BLOCK` | `.devforgeai/work/review-<story>/style-result.json`, `.devforgeai/work/review-<story>/style-report.md` | `report_only`: as `compliance` |
| `report` | `review_writer` | `writes: docs`: the lease named in the run file is the dispatched agent's (`LEASE_HELD`), and `changed`, derived from the checkpoint diff, is a subset of `claimed_paths` (`UNCLAIMED_CHANGE`) and holds nothing but the run's fence path, `docs/reports/review-<story>.md`; the whole-tree package and import policy scan over the root finds no violation | `write_fence_violation: BLOCK` | `.devforgeai/work/review-<story>/report-result.json`, `.devforgeai/work/review-<story>/report-report.md`, then `.devforgeai/work/review-<story>/handoff.json` | `document`: the phase produced at least one file and every declared output with non-null content exists on disk. On pass this is the last phase: the run is marked `ready_to_promote`, enforcement is cleared, and the first handoff block names `devforgeai promote <run>`; the second block is written by that command once the user asks for it |

Attempt budgets are 2 for every phase. No phase declares `rewind_to`, so a `next` value in any receipt is refused; a failure retries the same phase and then closes the run `REQUIRE_HUMAN`. No phase grants a stack command key, so `review` runs no build, test, lint or format command at any transition, and the three inspection workers carry no `devforgeai run` surface at all.

The four phases build linearly on this run's own candidate root from its `base` checkpoint, which is canonical HEAD at `devforgeai phase start`. Only `report` writes, and only it holds the lease: the sequencer grants the lease at dispatch, the hook layer binds it at `SubagentStart`, and `ingest-result` releases it. The three inspection workers hold none and may read the checkpoint concurrently; their own writes land in a per-agent scratch outside the root.

Two honest limits bind every row. Every `devforgeai phase start` defect is a refusal whatever the story's declared value says, with the single downgrade in `10-sequencer-and-contracts.md` section 3.4; and `test_runner_missing`, the only class that changes behaviour at transition time, never fires here because nothing is brokered.

### 7d. Phase guidance

One subsection per registry phase. Each becomes `references/<phase>.md` verbatim, loaded when that phase's worker is dispatched. `references/envelope.md` carries the envelope shape from section 6 and is loaded on every dispatch.

#### references/compliance.md

The `compliance` phase asks one question: does the change honour the excerpts the story carried. You judge and you write nothing: you have no `Write`, no `Edit` and no `apply_patch`, and the candidate root is byte-identical when you finish. Your detailed evidence goes in the receipt's `findings` string, capped at 16,384 UTF-8 bytes and refused rather than truncated if it exceeds that, and the sequencer persists it for you at `.devforgeai/work/review-<story>/evidence/compliance_checker/findings.md` once the receipt validates. Do not try to record it under another filename, as JSON, or through a shell redirect: a judge that is refused a write has no write to make.

- The story's `context[]` entries are the standard, and they are verbatim slices with an anchor and a digest that the gate re-resolved on entry. Judge against the excerpt, not against a remembered rule and not against the whole constitution: an excerpt that binds is marked `status: INTENDED`, and one marked `OBSERVED` is advisory, describing what the code already does rather than what it must do.
- The subject is the story's `write_fence` paths at the `base` checkpoint of this run's own candidate root, which holds the story's code as its promoted `dev` run left it in the canonical tree. Read them there. Where `dev` ran, `.devforgeai/work/<story>/green-report.md` and `refactor-report.md` list what each phase changed, which is the fastest way to see the change rather than the whole file.
- Check the story's `## Interface`, `## Out of Scope` and `## Unchanged Behaviour` sections against the code at that `base` checkpoint: behaviour the story excluded but the code added is a compliance finding, not a style one, because the story is the authority the change was authorised by.
- Record every excerpt you checked in `findings`, including the ones the change honours. A review that lists only defects cannot be distinguished later from a review that stopped early, and `issues` is bounded at ten rows, so the full list belongs in `findings` and the defects belong in `issues`.
- One finding per defect, each carrying the path with a line range and the anchor of the excerpt it breaks. A finding with no anchor cannot be acted on by `dev` without re-deriving the whole judgement.
- Return `pass` when the inspection completed, whatever it found, with an empty `claimed_paths`. Return `fail` only when the inspection could not be completed — a fence path that does not exist at the checkpoint, or a `context[]` excerpt that is empty. Return `needs_user` when two excerpts contradict each other, because that is a decision for the constitution's owner and `needs_user` closes the run on the first ask rather than retrying.

#### references/security.md

The `security` phase inspects the change for the classes a story cannot be assumed to have considered. You judge and you write nothing: you have no `Write`, no `Edit` and no `apply_patch`, and the candidate root is byte-identical when you finish. Your detailed evidence goes in the receipt's `findings` string, capped at 16,384 UTF-8 bytes and refused rather than truncated if it exceeds that, and the sequencer persists it for you at `.devforgeai/work/review-<story>/evidence/security_checker/findings.md` once the receipt validates. Do not try to record it under another filename, as JSON, or through a shell redirect: a judge that is refused a write has no write to make.

- Cover five classes and say so explicitly for each in `findings`, even when the class is not present in the change: input handling and validation, secret and credential handling, authorisation and access decisions, injection surface (query construction, command construction, deserialisation, path construction), and error and log disclosure.
- Scope is the change plus what it calls. A pre-existing weakness the story did not touch is recorded in `findings` as context, not raised as a finding against this story, because a finding routes to `/dev {story} --fix` and that story has no authority to change code outside its fence.
- The techstack excerpt in the story's `context[]` often bans a whole class of construct for a reason quoted in the stack policy's `forbidden_imports`. A violation of that ban already fails a `dev` phase at ingest, so a finding here means the construct arrived by a route the policy does not match; say which route.
- Rate each finding with a severity the report carries, and justify it by what an attacker gains, not by how hard the fix is.
- Do not write the fix, and do not spell one out. This phase changes no code anywhere, and a suggested patch in a finding invites a `dev` run that implements it without a story authorising it.
- Return `pass` when the inspection completed, `fail` when it could not be, `needs_user` when a class cannot be judged without a fact the story and its excerpts do not carry.

#### references/style.md

The `style` phase checks the change against the project's own conventions, not against a general style opinion. You judge and you write nothing: you have no `Write`, no `Edit` and no `apply_patch`, and the candidate root is byte-identical when you finish. Your detailed evidence goes in the receipt's `findings` string, capped at 16,384 UTF-8 bytes and refused rather than truncated if it exceeds that, and the sequencer persists it for you at `.devforgeai/work/review-<story>/evidence/style_checker/findings.md` once the receipt validates. Do not try to record it under another filename, as JSON, or through a shell redirect: a judge that is refused a write has no write to make.

- The rules are the constitution's style slice and the sourcetree slice in the story's `context[]`: naming, layout, ownership of paths, and the test placement convention. A rule that is not in an excerpt is not a rule here; record it in `findings` as an observation instead of raising it as a finding.
- Check that every changed path is where the sourcetree excerpt says that kind of file belongs, and that test files match the naming convention the techstack excerpt states. A file in the right place with the wrong name is a finding, because the next story's fence will be drawn from the same convention.
- Where the project authorises a `lint` or `format` command in its stack section, that check is not this phase's job: no `review` phase grants a command key, this worker carries no `devforgeai run` surface, and the `refactor` transition of the `dev` run already required `lint` to exit zero. Report only what a linter cannot see, such as a name that is legal but contradicts the excerpt's convention.
- Keep findings separable from compliance ones. If the rule comes from the constitution's Style section it belongs here; if it comes from Principles, Mandates or Constraints it belongs to `compliance`. The report has one section for each, and `retro` counts them separately.
- Return `pass` when the inspection completed, `fail` when it could not be, `needs_user` when the excerpts state no convention for a decision the change had to make.

#### references/report.md

The `report` phase renders the three inspections into the one artifact a later skill cites. You write that report inside the candidate root the status block names, at the run's fence path, using `Edit` and `Write`; you run no command; you finish with the receipt.

- Read the three earlier reports under `.devforgeai/work/review-<story>/`, and the `findings.md` the sequencer persisted for each inspection worker under `.devforgeai/work/review-<story>/evidence/<agent>/`. The reports are the sequencer's rendering of the accepted receipts, including each worker's `issues` and the oracle's problem rows; the persisted findings hold the working behind them, written by the sequencer from the string the worker returned. Both are evidence rather than a claim.
- Fill `assets/review-report.md`. Every frontmatter key the `review-report` template header requires is present: `story`, `template`, `template_version`, `status`, `verdict` and `depends_on`. Every required section is present: Compliance, Security, Style, Findings.
- Number findings `FIND-001` upward across all three sections in the order they were raised, so a finding id is stable enough to quote in a `dev` run and in a retro.
- Set `verdict: pass` only when the Findings section is empty. Any finding at all, at any severity, is `verdict: findings`, because a report that grades its own severity threshold is a report nobody can act on mechanically.
- Fill `depends_on` with the story path and every constitution or techstack anchor the report cites, each with the digest the gate resolved. That is what lets `qa` and `retro` detect that a report was written against a document version that has since moved.
- Add no finding of your own. This phase renders; the three inspections judge. A defect that occurs to you here belongs in `issues` as a note for the human, not in the Findings table where it would carry the authority of an inspection that never happened.
- Write exactly one file, at `docs/reports/review-<story>.md` inside the candidate root, and claim that one path in the receipt. Any other changed path fails the phase at ingest, and a phase that writes no file fails the `document` oracle.
- The frontmatter `verdict` you set is what the sequencer reads to select the handoff row, through the `evidence_refs` entry naming this report. The run still passes: reporting a defect is a passing run.

### 7e. Worker contracts

One block per worker. `must_not` is compiled into the agent prompt verbatim.

`writes` is the header every worker declares, and its enum is `candidate | none`: `none` for the three inspection workers, `candidate` for `review_writer`, which is this skill's only producer. A judge's `tools` carry `Read`, `Grep`, `Glob` and `Bash` and nothing else: no `Write`, no `Edit`, no `apply_patch`, and nothing else that reaches a shell. A judge's evidence reaches disk through the receipt's required `findings` string, which the sequencer persists on its behalf. The writer's carry `Edit` and `Write` — `apply_patch` on the Codex target — admitted under the candidate root, and no `devforgeai run` surface, because no `review` phase grants a key. Section 7g compiles these blocks into provider-native subagent files. `tools` names tools only: a Claude Code subagent's `tools:` frontmatter accepts tool names and MCP server patterns, never a command pattern, so the hook dispatcher is the only command-level bound. A judge's `Bash` runs `devforgeai status` and the dispatcher's read-only command set (`cat cmp cut diff echo grep head jq ls pwd rg sha256sum tail test tr wc`, plus read-only git subcommands inside the root) and nothing else; a producer's additionally runs `devforgeai run KEY` for its granted keys.

```yaml
name: compliance_checker
skill: review
responsibility: Report every place the change departs from the INTENDED excerpts the story carried, with the path, the line range and the excerpt anchor.
inputs:
  - the devforgeai status block, which names run, candidate.root and phase
  - the story id, its context[] excerpts, and its Interface, Out of Scope and Unchanged Behaviour sections
  - the story's write_fence paths at the base checkpoint of candidate.root, which is canonical HEAD after the story's dev run was promoted
  - .devforgeai/work/<story>/green-report.md and refactor-report.md when a dev run recorded them
outputs:
  - a receipt whose findings string carries one row per excerpt checked, including those the change honours, which the sequencer persists under this run's evidence directory
  - a receipt whose issues carry one bounded row per departure, each naming the path with a line range and the excerpt anchor, and whose evidence_refs name the story and the checkpoint the departures were read from
must_not:
  - judge against a rule no context[] excerpt states
  - treat an OBSERVED excerpt as binding
  - raise a finding about a path outside the story's write_fence
  - write any file, or run any build, test, lint or format command
tools: [Read, Grep, Glob, Bash]
granted_keys: []
writes: none
returns: devforgeai.worker-result/v1
```

```yaml
name: security_checker
skill: review
responsibility: Inspect the change for input handling, secret handling, authorisation, injection surface and error disclosure, and report each defect with a severity and what an attacker gains.
inputs:
  - the devforgeai status block, which names run, candidate.root and phase
  - the story id, its context[] excerpts, and its Interface section
  - the story's write_fence paths at the base checkpoint of candidate.root, and the code they call
outputs:
  - a receipt whose findings string states what was inspected for each of the five classes even when nothing was found, which the sequencer persists under this run's evidence directory
  - a receipt whose issues carry one bounded row per defect, each with a class, a severity, the path with a line range and the exposure, and whose evidence_refs name the checkpoint the defects were read from
must_not:
  - write a patch text inside a finding
  - raise a pre-existing weakness the story did not touch as a finding; record it as context
  - assign a severity by how hard the fix looks rather than by what an attacker gains
  - write any file, or run any build, test, lint or format command
tools: [Read, Grep, Glob, Bash]
granted_keys: []
writes: none
returns: devforgeai.worker-result/v1
```

```yaml
name: style_checker
skill: review
responsibility: Check the change against the naming, layout and test-placement conventions the story's constitution and sourcetree excerpts state, and report each departure.
inputs:
  - the devforgeai status block, which names run, candidate.root and phase
  - the story id and its context[] excerpts for the constitution style slice, the sourcetree slice and the techstack testing slice
  - the story's write_fence paths at the base checkpoint of candidate.root
outputs:
  - a receipt whose findings string lists every convention checked, which the sequencer persists under this run's evidence directory
  - a receipt whose issues carry one bounded row per departure, each naming the path and the convention it contradicts, and whose evidence_refs name the excerpts the conventions were read from
must_not:
  - raise a preference no excerpt states as a finding; record it as an observation
  - duplicate a finding that belongs to the compliance phase's sections of the constitution
  - write any file, or run any build, test, lint or format command
tools: [Read, Grep, Glob, Bash]
granted_keys: []
writes: none
returns: devforgeai.worker-result/v1
```

```yaml
name: review_writer
skill: review
responsibility: Write docs/reports/review-<story>.md inside the candidate root, rendering the three inspections against the review-report template and adding no judgement of its own.
inputs:
  - the devforgeai status block, which names run, candidate.root, phase and fence
  - .devforgeai/work/review-<story>/compliance-report.md, security-report.md and style-report.md, and the findings.md the sequencer persisted for each inspection worker under .devforgeai/work/review-<story>/evidence/
  - the story id and the anchors and digests its context[] entries carry
  - assets/review-report.md
outputs:
  - the report file, written at the fence path under candidate.root
  - a receipt claiming that one path, with the report named in evidence_refs so the sequencer can read its verdict
must_not:
  - add a finding no inspection phase raised
  - set verdict pass while the Findings section holds a row
  - change any path other than docs/reports/review-<story>.md
  - omit a required frontmatter key or a required section of the review-report template
  - write outside the candidate root, or run any command other than devforgeai status
tools: [Read, Grep, Glob, Edit, Write, Bash]
granted_keys: []
writes: candidate
returns: devforgeai.worker-result/v1
```

### 7f. Handoff outcomes

The `handoff.outcomes` block this skill declares in `skill.yaml`, taken from `02-skill-roster.md`'s decision table and corrected to the closed status set. The **Rendered by** column says who produces the text the user sees: the sequencer writes `next` into `handoff.json` and the adapter prints that block verbatim, except on a gate refusal, where no handoff exists and the adapter prints the sequencer's stderr plus this table's repair route.

| Outcome | Next steps | Rendered by |
|---------|------------|-------------|
| pass (all four phases), run `ready_to_promote`, report not yet promoted (`REQUIRE_HUMAN`) | `devforgeai promote {run}` | sequencer, at `devforgeai phase next` |
| `devforgeai promote {run}` succeeded, report `verdict: pass` | `/qa {story}` | sequencer renders `/status` for a document run; section 9 records the difference |
| `devforgeai promote {run}` succeeded, report `verdict: findings` or `verdict: fail` | `/dev {story} --fix`, then `/review {story}` | sequencer, from the promoted block's verdict row (`10-sequencer-and-contracts.md` section 6); the findings are in the fenced report, and the repair is a fresh `dev` run, never an edit inside this run's root |
| `devforgeai promote {run}` refused `STALE_BASE` after the rebase retry, or in copy mode (`needs_user`) | resolve the canonical divergence, then `devforgeai promote {run}` | sequencer |
| `devforgeai promote {run}` refused `MERGE_CONFLICT` or `DIRTY_TARGET` (the canonical report file is dirty) | commit or stash the named canonical file, then `devforgeai promote {run}` | sequencer |
| `fail` at any phase, attempts exhausted (`REQUIRE_HUMAN`) | repair the named defect, then `/review {story}` — the run is blocked, not closed, and that command resumes it at `run.yaml#blocked_at` with attempts reset | sequencer |
| `needs_user` at any phase (`REQUIRE_HUMAN`, no retry) | answer the question the worker raised, then `/review {story}` — the same resume | sequencer |
| `REQUIRE_HUMAN` at any phase, and the story itself must change before the review can finish | `devforgeai phase fail --reason <text>`, then `/clarify {story}` | sequencer renders the `phase fail` step; another skill on the same story cannot open until this run is closed |
| `could_not_run`, `reason_code: provider_tool_refused` (the provider declined a worker's tool call before any DevForgeAI hook ran) | report the refused call to the spec author, then `/review {story}` — a worker asking for a tool its role does not carry is a specification defect, not a project fault | sequencer, through the missing-runner route |
| `could_not_run`, `reason_code: prerequisite_missing` (a worktree-mode prerequisite the `SessionStart` self-test names) | install or repair the named prerequisite, then `/review {story}` | sequencer, through the missing-runner route |
| `could_not_run`, `reason_code: checkpoint_fault` (the sequencer could not create, read or reset a checkpoint) | inspect the candidate root, then `devforgeai phase fail --reason <text>` and `/review {story}` | sequencer, through the missing-runner route |
| `could_not_run`, `reason_code: hook_fault` (no worker identity on the stop event, or a malformed receipt) | install or repair the hook dispatcher, then `/review {story}` | sequencer, through the missing-runner route |
| `could_not_run`, `reason_code: timeout` or `network` | remove the cause named in the report, then `/review {story}` | sequencer, through the missing-runner route |
| `devforgeai phase fail --reason` recorded a block (`BLOCK`) | `/review {story} --fix` | sequencer |
| gate: unresolved ASSUMPTION in the story | `/clarify {story}`, then `/review {story}` | adapter, from the refusal on stderr |
| gate: stale hash on a `provenance[]`, `context[]` or `commands` entry | `/plan {slug} --reslice {story}`, then `/review {story}` | adapter |
| gate: unresolvable source | `/plan {slug} --reslice {story}`; for a stand-alone story outside `docs/plan/`, re-run with the lenient flag | adapter |
| gate: the story is not `status: ready`, or a `blocked_by` story is not done | `/dev {story}` first, then `/review {story}` | adapter |
| gate: the report fence overlaps an active or `ready_to_promote` run (`FENCE_OVERLAP`) | finish or abandon the named run, then `/review {story}` | adapter, from the refusal on stderr |
| gate: the story's own `dev` run is still `active` or `ready_to_promote` (`STORY_IN_FLIGHT`) | promote that run with `devforgeai promote {dev_run}`, or close it with `devforgeai phase fail --reason <text>`, then `/review {story}` | adapter, from the refusal on stderr |

The first row is the only one that leaves the run `ready_to_promote`, and `ready_to_promote` is the only status `devforgeai promote {run}` accepts. Every other `REQUIRE_HUMAN` row leaves the run `active` with its lease released and its candidate root on disk. A report written before the block is not lost and is not merged. A `REQUIRE_HUMAN` block — a `needs_user` result or an exhausted attempt budget — leaves the run `active` with its lease released, its candidate root and checkpoints on disk, and `run.yaml#blocked_at` naming the phase it stopped at. `devforgeai phase start` with the same skill and the same argument resumes that run at `blocked_at` with `attempts` reset to zero, rather than refusing it; any other skill on the same story needs `devforgeai phase fail --reason <text>` first, which abandons the root (`10-sequencer-and-contracts.md` sections 2, 3 and 5.4). So a blocked review is repaired by fixing the cause and re-running `/review {story}`, which resumes it in place; only a route through another skill on the story, such as `/clarify {story}`, needs the `phase fail` step first.

Also possible in every rendered row: `/status` reprints the same block from the same file. No row invokes another skill's run: `devforgeai phase start` refuses while a run is active, so every edge above is a command a human or a fresh session runs next. `{story}` is this run's argument, and `{slug}` in the `/plan {slug} --reslice {story}` rows is the project slug that `state.yaml` records and the story's own path under `docs/plan/<slug>/stories/` carries; `SKILL-SPEC-001-dev.md` section 7f states the same source, and `plan`'s run argument is that slug.

### 7g. Compiled subagent definitions

Each section 7e contract compiles to one provider-native subagent file per target. The Claude file is Markdown with YAML frontmatter at `.claude/agents/review-<role>.md`; the Codex file is TOML at `.codex/agents/review-<role>.toml`. The filename is skill-scoped so two skills' worker sets can install side by side; `name` stays the canonical registry name, because that is the value the provider reports as `agent_type` and the sequencer compares against the active phase's worker. Claude's own rule is that a filename need not match the `name` it declares. The `tools` column below names tools only: a Claude Code subagent's `tools:` frontmatter accepts tool names and MCP server patterns, never a command pattern, so a compiled file writes `Bash` and never `Bash(devforgeai status)` or `Bash(devforgeai run *)`, and the hook dispatcher is the only command-level bound. A judge's `Bash` runs `devforgeai status` and the dispatcher's read-only command set (`cat cmp cut diff echo grep head jq ls pwd rg sha256sum tail test tr wc`, plus read-only git subcommands inside the root) and nothing else; a producer's additionally runs `devforgeai run KEY` for the keys its phase granted. Each compiled body restates its role's bound in its Rules section.

| Worker | name | tools | model | writes | Claude file | Codex file |
|---|---|---|---|---|---|---|
| `compliance_checker` | `compliance_checker` | `Read, Grep, Glob, Bash` | `inherit` | none | `.claude/agents/review-compliance_checker.md` | `.codex/agents/review-compliance_checker.toml` |
| `security_checker` | `security_checker` | `Read, Grep, Glob, Bash` | `inherit` | none | `.claude/agents/review-security_checker.md` | `.codex/agents/review-security_checker.toml` |
| `style_checker` | `style_checker` | `Read, Grep, Glob, Bash` | `inherit` | none | `.claude/agents/review-style_checker.md` | `.codex/agents/review-style_checker.toml` |
| `review_writer` | `review_writer` | `Read, Grep, Glob, Edit, Write, Bash` | `inherit` | candidate | `.claude/agents/review-review_writer.md` | `.codex/agents/review-review_writer.toml` |

`description` is one sentence naming when the primary dispatches the worker, because that is the field the provider matches a dispatch against:

| Worker | description |
|---|---|
| `compliance_checker` | Dispatch when `devforgeai status` names phase `compliance` of a `review` run; it reports where the story's change departs from the binding excerpts the story carried, and writes nothing, returning its working in the receipt's findings string. |
| `security_checker` | Dispatch when `devforgeai status` names phase `security` of a `review` run; it inspects the change for the five security classes and reports each defect with a severity, writing nothing and returning its working in the receipt's findings string. |
| `style_checker` | Dispatch when `devforgeai status` names phase `style` of a `review` run; it checks the change against the naming, layout and test-placement conventions the excerpts state, writing nothing and returning its working in the receipt's findings string. |
| `review_writer` | Dispatch when `devforgeai status` names phase `report` of a `review` run; it writes the review report in the candidate root from the three inspection reports, adding no finding of its own. |

The body of each file is the four-part outline `templates/agent-md.md` fixes, filled from the worker's section 7e contract and its `references/<phase>.md`:

1. **Job** — the `responsibility` sentence, expanded to what a good result looks like and what it leaves to the next worker. `review_writer`'s body opens with the work: "You write the review report inside the candidate root the status block names, using Edit and Write; finish with the receipt." Each inspection worker's opens with the template's own `writes: none` sentence: "You judge …. You write nothing. Finish with the receipt."
2. **Inputs** — one line per `inputs:` entry, and nothing outside that list is opened. The first entry is always the `devforgeai status` block the primary pasted, which is where the run id, the candidate root, the phase and the fence come from.
3. **Rules** — the `must_not` lines verbatim, each with the mechanism that catches it: the fence check and the claimed-path check at ingest, the phase's `writes` mode against the root, the header's `writes` scope for the agent's own tools, the lease, the `document` oracle.
4. **Receipt** — the `devforgeai.worker-result/v1` object from section 6, the statuses this worker may return, and the rule that the final message is exactly that object with no fence and no prose. `review_writer`'s adds that the report's frontmatter `verdict` is what the sequencer reads through `evidence_refs`, and that `findings` is forbidden on its receipt. Each inspection worker's adds that `findings` is required on `pass` and `fail` and optional on `needs_user` and `could_not_run`, is capped at 16,384 UTF-8 bytes either way, is where the detailed working goes, and is persisted by the sequencer to a fixed path the worker does not choose.

Provider differences, stated rather than assumed:

- Claude-only frontmatter keys — `hooks`, `memory`, `background`, `permissionMode`, `maxTurns`, `effort`, `disallowedTools`, `mcpServers`, `color` and the git-worktree isolation key — are omitted from every compiled file. The framework's own isolation is one subagent per phase and the candidate root the sequencer owns; forking a worktree from the default branch would take this run away from the checkpoint the story's `dev` run left, which is the thing it exists to judge.
- `skills:` preloads nothing for any of the four. The phase guidance a worker needs is `references/<phase>.md`, which its body links, and preloading the `review` skill would put the primary's dispatch loop inside a worker.
- `model` is `inherit` for all four: no source in this specification's `depends_on` set assigns a per-worker model, and inheriting keeps a run's four phases on one model.
- The Codex file carries `name`, `description`, `sandbox_mode`, `approval_policy` and `developer_instructions`. `sandbox_mode` is the writable-workspace mode for `review_writer` and the read-only mode for the three inspection workers, which is Codex's equivalent of the `tools` split; `apply_patch` is the write tool `review_writer` uses in place of `Edit` and `Write`, and the three judges carry no write tool on either target. The provider itself was observed refusing a report-shaped file write from a subagent on Claude, undocumented and relied on in neither direction, so the design does not depend on a hook catching it: a judge has no write tool to be caught with, and its evidence reaches disk only as the `findings` string the sequencer persists.
- Neither provider carries the lease or the fence in the agent file. They live in `.devforgeai/work/<run>/run.yaml` and are enforced by the hook dispatcher, so a stale agent file cannot widen what a worker may write. `review_writer`'s write is admitted by path — under the candidate root and inside the fence — not by the tool list alone; the three inspection workers carry no write tool on either target, so there is nothing to admit.

## 8. Bundled resources

### Layout (fixed)

```
review/SKILL.md              # at most 500 lines: identity, phase list, dispatch loop, handoff table
  references/compliance.md   # section 7d, compliance
  references/security.md     # section 7d, security
  references/style.md        # section 7d, style
  references/report.md       # section 7d, report
  references/envelope.md     # the worker-result schema from section 6
  agents/compliance_checker.md
  agents/security_checker.md
  agents/style_checker.md
  agents/review_writer.md
  assets/review-report.md    # the review-report template
```

`SKILL.md` links to `references/`, `agents/` and `assets/`; an `agents/*.md` links to its own `references/<phase>.md` and to `references/envelope.md`; nothing links further. No `README.md` exists inside the skill directory.

### scripts/

None, and the directory is not created.

| File | Purpose | Invocation | Exit codes |
|------|---------|------------|------------|
| none | no actor in a `review` run can invoke a script: the primary window's Bash grammar is the five model-callable `devforgeai` operations, and a worker's shell is `devforgeai status` alone | not applicable | not applicable |

The deterministic checks a script would otherwise perform already run: the story gate and the fence gate are inlined in `devforgeai phase start`, receipt and changed-set validation runs in `devforgeai ingest-result`, and the `document` oracle confirms the report reached disk.

### references/

| File | Content | Load when |
|------|---------|-----------|
| `compliance.md` | section 7d, compliance: excerpts as the standard, INTENDED versus OBSERVED, the applied set, finding shape | dispatching `compliance_checker` |
| `security.md` | section 7d, security: the five classes, scope limited to the change, severity by exposure, no patch text | dispatching `security_checker` |
| `style.md` | section 7d, style: conventions from excerpts only, path and naming checks, the boundary with compliance | dispatching `style_checker` |
| `report.md` | section 7d, report: reading the three phase reports, template keys and sections, finding numbering, the verdict rule, `depends_on` | dispatching `review_writer` |
| `envelope.md` | the `devforgeai.worker-result/v1` shape, the closed status set, the `reason_code` rule, the bounds, and the rule that the final message is exactly this object with no fence and no prose | every dispatch |

### assets/

| File | Used for |
|------|----------|
| `review-report.md` | the `review-report` template `review` owns: the frontmatter keys, the Compliance, Security, Style and Findings sections, and the `FIND-NNN` row shape |

### agents/

One file per worker in section 7e. No file for Gate, Record or Handoff.

| File | Worker (from section 7) | writes | Compiled to |
|------|-------------------------|--------|-------------|
| `compliance_checker.md` | `compliance_checker` | none | `.claude/agents/review-compliance_checker.md`, `.codex/agents/review-compliance_checker.toml` |
| `security_checker.md` | `security_checker` | none | `.claude/agents/review-security_checker.md`, `.codex/agents/review-security_checker.toml` |
| `style_checker.md` | `style_checker` | none | `.claude/agents/review-style_checker.md`, `.codex/agents/review-style_checker.toml` |
| `review_writer.md` | `review_writer` | candidate | `.claude/agents/review-review_writer.md`, `.codex/agents/review-review_writer.toml` |

## 9. Gotchas and edge cases

Each row is a real behaviour of the current implementation or a resolved contradiction between two design documents. Where a resolution is forced by a specific line, the line is named.

| Situation | What goes wrong | What to do instead |
|-----------|-----------------|--------------------|
| The seven sub-phases give Slice to a framework worker, but no registry phase dispatches one (OI-1) | A receipt from a worker the active phase does not name is refused at ingest, because the active phase's worker is `compliance_checker`, and the run stalls on a protocol error that consumes no attempt | Dispatch no Slice worker. Slice is a sequencer step inside `phase start`: it writes the resolved bundle to `.devforgeai/work/<run>/context.json` and hands every worker that path. The story's `context[]` bundle is what it resolves. This specification promises no slice phase and names no framework worker for it. |
| `01-skill-anatomy.md` describes provenance conformance as part of the gate while an earlier revision of `10-sequencer-and-contracts.md` limited the gate to `commands.hash` (OI-2) | A specification written against the older text understates the gate and lets an author claim a stale constitution excerpt is undetected here | The story gate re-resolves every `provenance[]` and `context[]` entry as well as `commands`, per `10-sequencer-and-contracts.md` section 3.4, and it runs for `review` because the skill is story-anchored. A resolved source with a changed digest is `stale-hash` and is never downgradable. |
| A worker's tool list is read as authorising a lint or test command (OI-3) | An author writes a style worker that runs the project's linter and reports its output as evidence | Tools are per role (D1), and no `review` phase grants a stack key, so no worker of this skill carries a `devforgeai run` surface at all. The three judges carry `Read`, `Grep`, `Glob` and `Bash`; `review_writer` adds `Edit` and `Write` for the report and nothing that reaches a runner. **Decision (D8a):** the sequencer runs every oracle at ingest, and a judge reads the output it wrote. |
| A phase returns `status: fail` with no `next` (OI-4) | Section 5.4 lists no outcome row for it, so an author guesses the phase passes | The sequencer inserts the worker's failure as a transition problem row, the phase retries to its budget of 2, and the run then blocks `REQUIRE_HUMAN`. No `review` phase declares `rewind_to`, so a `next` value is refused outright, and there is no checkpoint reset in this skill. |
| A user runs `/review {story} --fix` expecting the flag to resume the blocked run (OI-5) | An author reads the flag as the resume mechanism and writes a repair route that depends on it | The run does resume, but the flag is not what resumes it. A blocked run stays `active` with `run.yaml#blocked_at` naming the phase, and `devforgeai phase start review {story}` — same skill, same argument, flags or not — resumes it there with `attempts` reset. `--fix` on this skill is only the `BLOCK` handoff's rendered next step; it changes nothing the workers read. Another skill on the same story, such as `/dev {story} --fix`, needs `devforgeai phase fail --reason <text>` first, which abandons the root. |
| The handoff says `/qa {story}` and an author reads it as an invocation (OI-7) | The adapter tries to run `/qa` in the same session and `devforgeai phase start` refuses because a run is active | A "calls" edge is a handoff row, not a call. The finishing run's `next` names the command; a human or a fresh session runs it. |
| `05-subagent-sets.md` names the workers `compliance-checker`, `security-checker`, `style-checker` and `review-writer` (OI-8) | An agent file named `review-writer` is refused at ingest, because `agent_type` is compared against the registry name and the alias map holds no entry for it | The registry names `compliance_checker`, `security_checker`, `style_checker` and `review_writer` are canonical and are used in section 7, in the `agents/` filenames and in the evidence table. The hyphenated forms are display aliases. |
| `10-sequencer-and-contracts.md` section 4 lists `review` as `kind: document` with no note that its argument is a story | An author writes a document run that carries `commands: {}` and cannot re-gate the story | `policy.py` marks `review` with `anchor: story`, and `cmd_phase_start` runs `document_gate` and then the whole `story_gate`, copying the story's `test_plan`, `commands` and `gate_policy` into the enforcement block while the fence stays the report path. The section 4 `kind` table has not yet been annotated with that column; the behaviour is implemented and is what this specification describes. |
| The run id looks like it should be the story id | Evidence from the `dev` run under `.devforgeai/work/<story>/` would be overwritten by this run's results | `run_id` returns `<skill>-<arg>` for a document run, so this run's evidence home is `.devforgeai/work/review-<story>/` and `dev`'s stays intact. The sequencer's per-phase rendered view is therefore `docs/reports/review-review-<story>-<phase>.md`, which is a different file from the fenced report `docs/reports/review-<story>.md` that the `report` phase writes. |
| A finding is treated as a failed phase | Every inspection that finds something retries twice and the run blocks without ever writing a report | Worker `status` reports whether the inspection completed; the judgement is the report's `verdict` field. A worker returns `pass` with findings in `issues`. `fail` is for an inspection that could not be carried out. |
| The skill declares `handoff.outcomes` and an author expects the sequencer to select a row from it | `01-skill-anatomy.md` says the sequencer selects the row by envelope status and fills placeholders from state, but `examples/hooks/devforgeai.py` selects from its own default table and never reads the skill's block | For a document run the sequencer renders `devforgeai promote <run>` on the first block of a completed run; on the block that promotion writes it renders `/status` when the report's `verdict` is `pass` and `/dev <story> --fix` when it is `findings` or `fail` (`10-sequencer-and-contracts.md` section 6); on a blocked `REQUIRE_HUMAN` it renders `/review <story>`, which resumes the run; and `/review <story> --fix` on `BLOCK`. Section 7f marks each row's renderer. Selection from the declared block is designed and unimplemented; nothing here gates on it, and the adapter prints the rendered block verbatim wherever one exists. |
| The handoff envelope declares `repair_route[]`, `source_basis[]`, `artifacts[]`, `validation[]` and `open_items[]` | An author promises a printed block that names the owning skill of a failing template | The written `handoff.json` carries `schema`, `run`, `skill`, `outcome`, `phase`, `location`, `reasons`, `next`, `attempts`, `authority.write_fence`, `session_id` and `at`. The other field groups are designed and unimplemented, and rule 8 forbids the renderer from adding a fact the envelope does not hold. |
| `dev` has not run, or ran and blocked | There is no diff to review, and `.devforgeai/work/<story>/` may be empty or hold only a `red-report.md` | With no `dev` run open, this run still opens: the gate reads the story, not the dev evidence. Each worker reports the fence paths as they stand in canonical HEAD, which for an unimplemented story means findings that the change does not exist — a legitimate `verdict: findings` report whose repair route is `/dev {story} --fix`. A blocked `dev` run is different: it keeps `status: active`, so `STORY_IN_FLIGHT` refuses this run until the user closes it with `devforgeai phase fail --reason <text>`. |
| The story's digests are placeholders because it is a stand-alone fixture story | Every `provenance[]` and `context[]` entry is `unresolvable-source` and the gate refuses | Pass `--lenient` to `devforgeai phase start`. It is accepted here because the skill is story-anchored, it downgrades `unresolvable-source` and nothing else, and it is refused with exit 1 for any story under `docs/plan/`. It is a flag on one of the four model-callable operations, not a fifth operation. |
| The gate refuses | An author expects a rendered handoff block | A `devforgeai phase start` defect writes no `handoff.json`: it exits 1 with the defect list on stderr and opens no run. The adapter prints that stderr plus the matching section 7f row. |
| The worker-result envelope carried a per-file base digest and full file bodies | A generated agent prompt emits the old file array, and every receipt is refused for an unknown key | The envelope is the section 6 receipt: `candidate`, `claimed_paths` and `evidence_refs`, with no per-file body and no per-file digest, because `review_writer` has already written the report and the sequencer derives `changed` from the checkpoint diff. **Decision (D4):** this specification describes the receipt only. |
| An author expects the report to appear in the working tree as soon as `review_writer` finishes | Nothing is in the canonical checkout until the user promotes | The report is written in the candidate root and reaches canonical only when the user runs `devforgeai promote <run>` on a run the last passing transition marked `ready_to_promote`; that command fast-forwards under the lock and is refused as `STALE_BASE` or `DIRTY_TARGET` rather than merging. A run blocked before its last phase stays `active` and is not promotable; its root keeps the report for inspection. **Decision (D2, D7 as amended):** the primary session stays in the canonical checkout, and promotion is never automatic. |
| `review` needs a tree to judge, and an earlier draft attached the run to the story's `dev` root at the `refactor` checkpoint | The judges read an unpromoted root, so a clean review can be recorded against code that never reaches canonical, and the attachment contradicts `STORY_IN_FLIGHT`, which refuses `phase start review <story>` for exactly that story | `review` opens its own candidate root from canonical HEAD, like every other run. The order per story is `dev` → `devforgeai promote <run>` → `review` → `qa`, and `STORY_IN_FLIGHT` refuses this run while the story's `dev` run is `active` or `ready_to_promote`, so the `base` checkpoint the judges read already contains the promoted work. A finding needing a code change routes to a new `/dev {story} --fix` run, never to an edit inside this root. **Decision (D12):** judging promoted code in a clean root is the MVP form of the clean verification worktree; the detached read-only variant D8 moves into `12-post-mvp.md` stays deferred, and nothing here gates on it. |
| Two agents write into the root at once | The checkpoint diff cannot attribute a change, so `changed` matches no single receipt | The run file records the lease; the hook layer binds it at `SubagentStart` to the provider's agent identity, and a write from any other agent is denied at `PreToolUse` (`LEASE_HELD`). On Codex, where the pre-write event carries no identity, the root itself is the fence and the check is path-under-root. **Decision (D3, D6):** only `review_writer` ever holds this skill's lease. |
| `AUTHOR-BRIEF.md` section 3 says every worker is read-only and section 6 requires every `must_not` block to end with "write any file, or run any build, test, lint or format command" | `review_writer` compiled from that trailer is told not to do the job D1 gives it | `WRITE-MODEL-REVISION.md` is the decision register for this wave and supersedes the brief's write model wherever they differ. **Decision (D1, D9, as amended):** `review_writer`'s trailer ends "write outside the candidate root, or run any command other than `devforgeai status`". Each judge's trailer is the brief's own line, "write any file, or run any build, test, lint or format command", because D13 gives a judge no write at all (**D13 item 1**). Both lead with the job. |
| A judge is given no way to record its working | The per-excerpt and per-class tables have to fit in `issues`, which is bounded at ten rows, so a thorough inspection loses its evidence | The judge returns them in the receipt's `findings` string, at most 16,384 UTF-8 bytes, and the sequencer writes that string verbatim to `.devforgeai/work/<run>/evidence/<agent>/findings.md` at the identity-bound `SubagentStop` once the receipt validates. `issues` stays the bounded routing summary, and `review_writer` reads both. **Decision (D13 items 1-3):** each inspection worker declares `writes: none` and carries no write tool; the earlier evidence-directory write amendment is superseded and that third `writes` value is removed from the enum, because Claude Code 2.1.259 was observed refusing a subagent's write of a report-shaped Markdown file before any hook ran, with an undocumented heuristic that may not be relied on in either direction. The path is fixed and the worker chooses neither it nor the name. |
| A judge, denied a write, works around it | It writes `findings.json` or `notes.txt` in the same directory, which the observed provider heuristic happens to allow, or it redirects a Bash command into a file, and the design's guarantee that a judge changes nothing becomes an accident of one provider's undocumented filter | There is no workaround, because there is nothing to work around. The judge carries no `Write`, no `Edit` and no `apply_patch`, and its Bash surface is `devforgeai status` alone, which the single-argv rule forbids compounding with a redirect. **Decision (D13 item 5):** a judge that is refused a write has no write to make; its evidence goes in `findings`. |
| A worker's tool call is refused by the provider before any DevForgeAI hook runs | The refusal looks like a hook failure, and an author routes it to "repair the hook dispatcher", which repairs nothing | It is `could_not_run` with `reason_code: provider_tool_refused`, rolling up to `INFRA_FAILURE`, and its section 7f row says a worker asking for a tool its role does not carry is a specification defect. `hook_fault` stays reserved for a missing worker identity on the stop event or a malformed receipt. **Decision (D13 item 6):** the taxonomy version stays 1 with the code added, and every place this specification enumerated `reason_code` carries it. |
| An author reads the isolation guarantee as covering a judge's findings | The claim that no worker output body reaches the primary window is false on both providers — a subagent returns its result to the parent, and a hook can validate a final message but cannot suppress it — so the design rests on something the runtime does not do | The bounded `findings` body does enter the primary window, as part of the subagent's result, exactly as any subagent result does. What stays isolated is the worker's transcript, its file reads, its tool traffic and its intermediate reasoning. **Decision (D13 item 4):** the guarantee this specification makes is that the primary window opens no artifact file and that no receipt carries a report body or code; `review_writer` returns no `findings` at all. |
| The compiled agent file is expected to carry the fence or the lease | An installed file drifts from the run file and an author treats it as authority | The agent file carries `name`, `description`, `tools`, `model` and the body; the fence and the lease live in `.devforgeai/work/<run>/run.yaml` and are enforced by the hook dispatcher. **Decision (section 7g):** every Claude-only key — hooks, memory, background, `permissionMode`, `maxTurns`, `effort`, `disallowedTools`, `mcpServers`, colour and the git-worktree isolation key — is omitted, and `skills:` preloads nothing. |
| The `report` phase writes no file because nothing was found | The `document` oracle fails the transition with "phase report produced no document inside the fence" | A clean review still writes its report, with `verdict: pass` and an empty Findings section. The artifact is the evidence that the review happened, and `qa`'s `depends_on` edge expects it. |
| The eval workspaces are copies with no `.git` | An author writes worktree mode as the only materialisation and the run cannot open | The sequencer probes for a git repository at the project root and records `candidate.mode`: worktree mode when one exists with at least one commit, copy mode otherwise. The section 10 workspaces are copy mode, where a checkpoint is a tree-hash manifest plus a copy-aside and promotion copies the changed path's bytes under the lock. **Decision (D2):** one contract, two materialisations. |
| An earlier draft of section 7b said promotion is part of Handoff and that the sequencer promotes the report on a passing run | An author compiles a `SKILL.md` that never asks the user, and the report lands in the canonical checkout without a human decision | Promotion is never automatic. The last passing transition sets `runs.<run>.status: ready_to_promote` and writes a `REQUIRE_HUMAN` handoff whose only forward step is `devforgeai promote <run>`; the compiled `SKILL.md` runs that command only after the user confirms in the session, and that command writes the second handoff block, whose `next` is `/qa {story}` or `/dev {story} --fix` by the report's `verdict`. Every run ends in two blocks. `STALE_BASE`, `DIRTY_TARGET` and `MERGE_CONFLICT` are refusals of `devforgeai promote <run>`, never of `devforgeai phase next`, and a run blocked before its last phase stays `active` and is not promotable at all. **Decision (D7, as amended; `10-sequencer-and-contracts.md` sections 5.4, 6 and 12.4):** the sequencer may not close a run onto the canonical tree on its own. |
| A finding needs a code change and the report is already written inside this run's root | An author has `review_writer`, or a follow-up worker in the same run, edit the code in the review root — a path outside the run's fence, denied at `PreToolUse`, and in a root that would be abandoned or promoted as a whole | A finding never routes to an edit in the review root. The repair is a new `dev` run, `/dev {story} --fix`, with the promoted report as its context; that run opens its own root and its own fence. One run per story at a time, one root per run. **Decision (D12):** `review` and `qa` run after promotion, each from canonical HEAD, and findings route forward to `dev` rather than backward into the judging root. |
| An earlier draft said a `REQUIRE_HUMAN` block closes the run, so "no flag resumes a closed one" | An author writes a repair route that opens a fresh run, and `devforgeai phase start` refuses it — the blocked run is still `active` — or writes `devforgeai phase fail --reason <text>` into every recovery row and throws away work the run had already checkpointed | A block is not a close. A `needs_user` result and an exhausted attempt budget both leave the run `active` with its lease released, its candidate root and checkpoints on disk, and `run.yaml#blocked_at` naming the phase. `devforgeai phase start` with the same skill and the same argument **resumes** that run at `blocked_at` with `attempts` reset to zero instead of refusing it, so `/review {story}` is the whole recovery once the human has acted. Only another skill on the same story needs `devforgeai phase fail --reason <text>` first, and that call is what abandons the root. **Decision (`10-sequencer-and-contracts.md` sections 2, 3, 5.4 and 6):** blocked runs resume; they are not reopened. |
| The `verdict: findings` and `verdict: fail` rows were rendered as `/status` | An author promises a block that tells the user nothing about the defect the report just recorded, and the fenced report is never acted on | The sequencer selects the promoted block's row from the report's frontmatter `verdict`: `pass` keeps the document-run default `/status`, and `findings` or `fail` selects `/dev <story> --fix`. The run's `outcome` stays `pass` in all three cases, because reporting a defect is a passing run. **Decision (`10-sequencer-and-contracts.md` section 6, verdict rows; `02-skill-roster.md`):** the verdict picks the row, and the repair route is a fresh `dev` run. |

## 10. Success criteria and test cases

### Success criteria

- Triggers on the nine section 4 positives and on none of the nine near-misses.
- `SKILL.md` is under 500 lines and contains identity, the four-row phase list, the dispatch loop and the handoff table, and no phase guidance.
- `agents/` holds exactly four files, named for the four canonical workers; `references/` holds exactly five.
- Every `must_not` block ends with its role's closing line: the evidence-scratch line for the three judges, the candidate-root line for `review_writer`. No judge's `tools` value exceeds `Read`, `Grep`, `Glob` and `Bash`; `review_writer`'s adds `Edit` and no run surface.
- A judge's run leaves the candidate root and the canonical tree byte-identical and writes no file at all. On `pass` or `fail` its receipt carries a non-empty `findings` string, and the sequencer persists that string to `.devforgeai/work/<run>/evidence/<agent>/findings.md`, which `review_writer` reads by path.
- Every agent file declares `writes`, and its value matches the phase's row in section 7c.
- The `SKILL.md` Bash grammar is no wider than `devforgeai status`, `devforgeai phase start review <story> [--lenient]`, `devforgeai phase fail --reason <text>`, `devforgeai validate` and `devforgeai promote <run>`.
- In a run, the primary-window transcript contains no read of the story or of the code under review, and no file write.
- Every completed run leaves `docs/reports/review-<story>.md` conforming to the `review-report` template header, and the user's `devforgeai promote <run>` is what puts it in the canonical checkout.
- No file outside the run's fence differs in the candidate root between the `base` checkpoint the run opened at and the checkpoint the user promoted.

### Eval workspace, built once per eval

Each eval runs in its own workspace, built by copying files that already exist. No file is hand-edited; per-eval differences ship as the overlay directories already present in the fixture, or as the scratch tree the sequencer demo produces. The copied tree carries no `.git`, so the sequencer records `candidate.mode: copy` and materialises the candidate root by copy, manifest and copy-aside; the demo's own scratch tree initialises a git repository and exercises worktree mode.

1. Build the base tree.
   - Evals 1: run `bash docs/design/examples/hooks/demo_sequencer.sh` and copy the directory it prints as `scratch:` to `<output-dir>/review-workspace/fixture-1/`. That tree is the fixture story with `tests/test_text.py` and a complete `tinyapp/text.py`, written by a real `dev` run and promoted into its working tree, which is the canonical state `review` opens its own root from.
   - Evals 2 and 3: copy `docs/design/examples/fixtures/dev-tdd/` without `overlays/` to `<output-dir>/review-workspace/fixture-<id>/`, then copy `docs/design/examples/fixtures/dev-tdd/overlays/eval-<id>/` over it.
2. Write `.devforgeai/state.yaml` containing exactly the three lines `version: 1`, `stories: {}`, `runs: {}`. Do not copy the fixture `state.yaml`: it holds an active run and every `devforgeai phase start` would be refused. Writing the minimal file also clears any enforcement block the demo left behind when its own run had not closed. Leave `.devforgeai/work/STORY-001/` in place where the demo produced it: it is this run's read-only input evidence and it lives under a different run id.
3. Copy `docs/design/examples/hooks/fixtures/.devforgeai/stack.yaml` into the copy's `.devforgeai/` if it is not already there.
4. Copy `dispatch.py`, `devforgeai.py` and `policy.py` from `docs/design/examples/hooks/` into `.devforgeai/hooks/`. The dispatcher resolves the sequencer as its own sibling, so the three files stay together.
5. Merge `docs/design/examples/hooks/settings.claude.json` into `<copy>/.claude/settings.json` so `SessionStart`, `PreToolUse`, `PostToolUse`, `SubagentStop` and `Stop` route to the dispatcher. Without this no receipt is ingested and no checkpoint is taken.
6. Install the generated skill at `<copy>/.claude/skills/review/` and run the prompt from inside the copy.

### evals/evals.json (used verbatim)

```json
{
  "skill_name": "review",
  "evals": [
    {
      "id": 1,
      "prompt": "Review STORY-001 in this directory. The story is a stand-alone fixture story outside docs/plan/, so open the run in lenient mode. Promote the run when the handoff asks for it; this instruction is that confirmation.",
      "expected_output": "All four phases pass, docs/reports/review-STORY-001.md is written against the review-report template with a verdict and any findings, the first handoff names devforgeai promote review-STORY-001, and after that command runs the report is in the working tree.",
      "files": [],
      "expectations": [
        "The transcript shows `devforgeai phase start review STORY-001 --lenient` exiting 0 and naming phase compliance",
        "docs/reports/review-STORY-001.md exists and its frontmatter carries story, template, template_version, status, verdict and depends_on",
        "docs/reports/review-STORY-001.md contains the sections Compliance, Security, Style and Findings",
        ".devforgeai/work/review-STORY-001/ contains compliance-result.json, security-result.json, style-result.json and report-result.json",
        ".devforgeai/work/review-STORY-001/handoff.json names devforgeai promote review-STORY-001 before that command runs, and has outcome pass and next /status after it",
        "No file under tinyapp/ or tests/ was created or modified during the run, in the working tree or in the candidate root",
        "The primary-window transcript contains no Read of STORY-001.md or tinyapp/text.py; those reads happen inside dispatched workers"
      ]
    },
    {
      "id": 2,
      "prompt": "Run the review skill on STORY-001 in this directory. Open the run in lenient mode; the story is a stand-alone fixture story.",
      "expected_output": "The gate refuses because criterion 3 carries an unresolved ASSUMPTION tag. No run opens, no worker is dispatched, no report is written, and the printed next step is /clarify STORY-001.",
      "files": [],
      "expectations": [
        "`devforgeai phase start review STORY-001 --lenient` exits 1 and its stderr names the unresolved ASSUMPTION in the story body",
        "No .devforgeai/work/review-STORY-001/ directory exists, so no handoff.json and no snapshot were written",
        "docs/reports/review-STORY-001.md does not exist",
        "The final message names /clarify STORY-001 as the next step"
      ]
    },
    {
      "id": 3,
      "prompt": "Use the review skill on STORY-001 in this directory. Only part of the story is implemented. Open the run in lenient mode. Promote the run when the handoff asks for it; this instruction is that confirmation.",
      "expected_output": "All four phases pass and the report records verdict findings, with numbered findings naming the acceptance criteria the applied code does not satisfy.",
      "files": [],
      "expectations": [
        "docs/reports/review-STORY-001.md exists with verdict: findings in its frontmatter",
        "Its Findings section holds at least one row whose id matches FIND-0 followed by two digits and which names tinyapp/text.py",
        "The Compliance section names the story's Interface or Acceptance Criteria as the standard it checked against",
        ".devforgeai/work/review-STORY-001/handoff.json names devforgeai promote review-STORY-001 before that command runs, and after it has outcome pass and next /dev STORY-001 --fix, because the report verdict is findings",
        "tinyapp/text.py is byte-identical to the eval-3 overlay copy, so no code was changed by the review"
      ]
    }
  ]
}
```

Eval 1 depends on `pytest` being installed, because the demo it builds on runs the `dev` loop through the `test` key; the demo tolerates a missing `lint` runner and still leaves the applied tree the eval needs. Section 11 records both.

Quick-mode results are generation feedback only: one enabled run per eval and no baseline. They are not runtime conformance evidence, and no section of this specification gates on such evidence; the deferred contract is `12-post-mvp.md#pm-02`.

## 11. Dependencies and compatibility

| Kind | Value |
|------|-------|
| Tools | `SKILL.md`: `Read`, `Agent`, and a Bash grammar no wider than `devforgeai status \| phase start review <story> [--lenient] \| phase fail --reason \| validate \| promote <run>`. Judges (`compliance_checker`, `security_checker`, `style_checker`): `Read`, `Grep`, `Glob` and `Bash`, and no write tool of any kind on either target. Producer (`review_writer`): those plus `Edit` and `Write`, with writes admitted under the candidate root. No worker carries a `devforgeai run` surface, because no `review` phase grants a stack command key. |
| MCP servers | none |
| Runtime | Python 3.11+ and PyYAML 6+ for the sequencer and the hook dispatcher. Worktree mode additionally needs `git` with a repository at the project root, at least one commit, `.devforgeai/work/` ignored, and both the provider's settings file and `.devforgeai/stack.yaml` tracked; the `SessionStart` self-test checks all five and fails `phase start` with `could_not_run: prerequisite_missing` rather than falling back to copy mode. `review` itself runs no project command; the eval workspace additionally needs the `test` runner named by the fixture's `python` stack section, because it is built from a completed `dev` run. |
| Project commands | none. `review` grants no run key at any phase, so it resolves no `stack.yaml` command. The story's `commands` block is still re-resolved at the gate, because a story whose `commands.hash` no longer matches `stack.yaml` is a story whose review would cite a stale stack. Contract: `10-sequencer-and-contracts.md` section 7. |
| DevForgeAI/Core compatibility | Requires the sequencer grammar, the story-anchored document run, and the `devforgeai.worker-result/v1` schema of `10-sequencer-and-contracts.md`, 2026-09-02. `NOT_APPLICABLE` for Research Core: `review` is an anatomy-governed skill, not a Research adapter. |
| Other skills | Consumes `story` from `plan`, `dev-notes` from `dev`, and `constitution`, `techstack` and `adr` from `architect` or `amend`. Produces `review-report` for `qa`, `dev` and `retro`. Invokes none of them: every edge is a handoff row. |

Deferred dependencies. Each names the `12-post-mvp.md` entry and what this skill does today without it.

| Deferred entry | What it would give `review` | What `review` does today |
|---|---|---|
| `12-post-mvp.md#pm-01` | runtime verification that each worker actually ran in its own context window | one subagent per phase is a declaration compiled into the target profile; a generated adapter is an uninstalled candidate that a human installs. |
| `12-post-mvp.md#pm-02` | conformance evidence from repeated provider trials | quick-mode eval results are generation feedback only, and no section gates on them. |
| `12-post-mvp.md#pm-04` | an operating-system write boundary, with only the report path writable | the fence is enforced by the `PreToolUse` deny at the candidate root, by the changed-set check at ingest and by the whole-tree policy scan, which is a fast-feedback layer rather than a kernel boundary. |
| the clean detached verification worktree that decision D8 of the write-model revision moves into `12-post-mvp.md`; its `PM-NN` id is assigned when that file is revised in this wave | a read-only detached tree, so a review could not read anything outside the fence at all | the run opens its own candidate root from canonical HEAD, which under D12 already holds the promoted `dev` work, and judges the fence paths at its `base` checkpoint; that clean root is the MVP form, and nothing in this specification gates on the detached variant. |
| `12-post-mvp.md#pm-06` | eval modes beyond `skip` and `quick`, with the interactive viewer and the description-optimisation loop | eval mode is `skip` or `quick`; no third mode is named as available, and no section gates on an eval result. |
| `12-post-mvp.md#pm-10` | a clean-checkout chain validator that re-runs this review from a fresh clone as a required check | `devforgeai validate` is a read-only invariant scan over the active run, and the hook layer remains user-disableable. |

Frontmatter values derived from this table:

```yaml
compatibility: "Needs Python 3.11+ and PyYAML for the devforgeai sequencer and its hook dispatcher, installed with the DevForgeAI hook fragment for the selected target, plus git at the project root for worktree-mode candidate roots. It runs no project build, test or lint command of its own."
allowed-tools: "Read Agent Bash(devforgeai status) Bash(devforgeai phase start *) Bash(devforgeai phase fail *) Bash(devforgeai validate) Bash(devforgeai promote *)"
```

## 12. Targets

The generator produces one provider-neutral semantic package and a separate adapter for each selected target when frontmatter, invocation policy, or agent configuration differs. Provider-neutral resources may be shared. Adapter directories are not required to be byte-identical or symlinked.

| Target | Install path | Invocation | Subagents | Notes |
|--------|--------------|------------|-----------|-------|
| claude | `.claude/skills/review/` plus `.claude/agents/` worker profiles | `/review STORY-NNN [--lenient]` | one provider-native subagent per canonical worker name: three judges that carry no write tool and return their evidence in the receipt's `findings` string, one writer that writes the report in the candidate root | Provider-specific frontmatter keys (`argument-hint`, `disable-model-invocation`) are compiled into this target's `SKILL.md` only. |
| codex | `.agents/skills/review/` plus `.codex/agents/` profiles | `$review STORY-NNN [--lenient]` | the same four, compiled per section 7g; the writer uses `apply_patch` and the writable-workspace sandbox mode | Portable six-field frontmatter only; policy goes in target-side configuration. |
| both | separate `.claude/skills/review/` and `.agents/skills/review/` adapters | as above | as above | Share only provider-neutral resources; validate each adapter independently. |

```yaml
metadata:
  version: "1.0.0"
  devforgeai-spec: "SKILL-SPEC-002"
  devforgeai-target: "both"
  devforgeai-anatomy: "true"
```

Not produced by skill-creator (deferred to DevForgeAI's skill-generator): provider-native `.claude/agents/*.md` and `.codex/agents/*.toml` worker profiles, provider-specific frontmatter keys for the Claude target, and concise `AGENTS.md` sections. Hook definitions are not per-skill: `init` installs the one dispatcher and its provider fragments from `09-hook-dispatcher.md`, and this specification ships none.

A generated package is an uninstalled candidate until those provider-native controls are present and independently validated. Generation or quick-mode success is not installation authority.

## 13. Constraints

- `SKILL.md` under 500 lines and roughly 5,000 tokens, holding only identity, the four-row phase list, the dispatch loop and the handoff table. Every other instruction lives in `references/<phase>.md`, `agents/<role>.md` or `assets/`. Splitting a phase's guidance into more reference files is the correct response to the line budget; cutting content is not.
- References one level deep from whichever file is loaded: `SKILL.md` links to `references/`, `agents/` and `assets/`; an `agents/*.md` links to `references/*.md`. Nothing links further.
- Hooks, state writes and phase advancement are not in the skill. Do not write an instruction the sequencer or a hook already enforces: the gate is `devforgeai phase start`, the fence is result validation plus the `PreToolUse` deny, and "the report exists" is the `document` oracle.
- No `README.md` inside the skill directory.
- No angle brackets in frontmatter. Description 735 characters, name 6 characters.
- Imperative voice. Explain why a step matters rather than shouting it; where an instruction is non-negotiable it is a gate, a fence or an oracle, and the text names that mechanism.
- Provide defaults, not menus. Procedures over declarations.
- No script is shipped, so no script prompts.
- A finding cites a path, a line range and an excerpt anchor. A judgement with no citation is an opinion, and the report is consumed by skills that cannot ask a follow-up question.

## 14. Acceptance checks

Run these before reporting done and paste their output:

```bash
# frontmatter and naming (skill-creator's own validator)
python -m scripts.quick_validate <output-dir>/review    # run from the skill-creator directory
# open-standard validator, if installed
skills-ref validate <output-dir>/review
# size budget
wc -l <output-dir>/review/SKILL.md                        # must be < 500
# every worker in section 7 has a prompt file, and no extra
ls <output-dir>/review/agents/                            # compliance_checker.md security_checker.md style_checker.md review_writer.md
# every agent file declares its role's write mode
grep -l 'writes: none' <output-dir>/review/agents/*.md      # compliance_checker.md security_checker.md style_checker.md
grep -l 'writes: candidate' <output-dir>/review/agents/*.md  # review_writer.md
# no judge carries a write tool
grep -LE 'Write|Edit|apply_patch' <output-dir>/review/agents/compliance_checker.md <output-dir>/review/agents/security_checker.md <output-dir>/review/agents/style_checker.md
# one reference file per phase, plus envelope.md
ls <output-dir>/review/references/                        # compliance.md security.md style.md report.md envelope.md
# no leftover placeholders
grep -rnE 'T[O]DO|T[B]D|\{\{' <output-dir>/review || echo clean
# the spec battery
python3 docs/design/specs/verify.py --only v1,v2,v4
```

For non-Research anatomy skills, DevForgeAI skill-validator additionally checks: all sub-phase kinds present with Gate, Record and Handoff bound to sequencer operations; the inspection workers and the writer are different files; `responsibility`, `must_not` and `writes` present in every agent file, `writes` in `candidate | none`, no judge's `tools` exceed `Read`, `Grep`, `Glob` and `Bash`, and the writer's exceed those only by `Edit` and `Write`; the `SKILL.md` Bash grammar is no wider than the five model-callable operations; handoff outcomes cover every status the skill can return, including `could_not_run` with every `reason_code` the skill can return.

## 15. Provenance

| Source | Hash | Used for |
|--------|------|----------|
| docs/design/01-skill-anatomy.md#primary-window-contract | see frontmatter | sections 2 (R4), 7a, 13 |
| docs/design/01-skill-anatomy.md#handoff-contract | see frontmatter | sections 7a, 7f, 9 |
| docs/design/10-sequencer-and-contracts.md#4-per-skill-phase-registry | see frontmatter | sections 1, 2 (R2, R8), 7b, 7c |
| docs/design/10-sequencer-and-contracts.md#3-4-re-resolving-sources-and-the-one-downgrade | see frontmatter | sections 7c, 9, 10 |
| docs/design/10-sequencer-and-contracts.md#5-2-validation-order | see frontmatter | sections 6, 7c, 7d (the report verdict) |
| docs/design/10-sequencer-and-contracts.md#5-4-transition-oracles | see frontmatter | sections 7c, 7d, 9 |
| docs/design/10-sequencer-and-contracts.md#6-handoff-envelope | see frontmatter | sections 7f, 9 |
| docs/design/11-artifact-registry.md#1-template-registry | see frontmatter | sections 2 (R1, R6), 6 |
| docs/design/11-artifact-registry.md#2-artifact-path-patterns | see frontmatter | sections 6, 9 |
| docs/design/02-skill-roster.md#handoff-decision-tables | see frontmatter | section 7f |
| docs/design/05-subagent-sets.md#sets-per-skill | see frontmatter | sections 7b, 7e, 9 |
| docs/design/08-story-specification.md#what-a-story-must-carry-and-why | see frontmatter | sections 5 (UC-2), 7d |
