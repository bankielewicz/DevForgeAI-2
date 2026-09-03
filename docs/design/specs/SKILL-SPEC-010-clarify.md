---
template: skill-spec
template_version: 1
id: SKILL-SPEC-010
skill_name: clarify
target: both
status: approved
author: "DevForgeAI wave-2 specification author"
date: 2026-09-02
depends_on:
  - source: docs/design/01-skill-anatomy.md#primary-window-contract
    hash: sha256:a6bbaf9af2d69f7ede18d7c40f242c42edb26d79be964ffec3f386d6347014c2
    excerpt: "**The model dispatches, the sequencer decides.** For an anatomy-governed skill, the primary window (provider entry adapter + skill orchestration) does light, trivial work only."
  - source: docs/design/01-skill-anatomy.md#gate-validating-the-incoming-artifact
    hash: sha256:01d7f4e0e09db70d8d4869ab22646d7cea27959c936571db4850b11df4000dc8
    excerpt: "Review (sub-phase 4) checks what a skill *produces*. Gate (sub-phase 0) checks what a skill *consumes*."
  - source: docs/design/01-skill-anatomy.md#context-bundle-format
    hash: sha256:7b068feb30e7cc2f66292b512ac179cd217df225fb58517d2aaadd30b25236dc
    excerpt: "A literal placeholder hash (`sha256:fixture...`, `sha256:PENDING`) is reported as `unresolvable-source`."
  - source: docs/design/10-sequencer-and-contracts.md#4-per-skill-phase-registry
    hash: sha256:511733ee35ca74fd5a5c0b59f225d7d975788e7d43d939f44c23b7aa8460cff0
    excerpt: "| clarify | 1 | `find_ambiguity` | `ambiguity_finder` | none | 2 | — | report_only | — |"
  - source: docs/design/10-sequencer-and-contracts.md#3-2-defect-to-action-map-as-implemented
    hash: sha256:700e29f7b7eb3b6883d0895d79e3822bf06c32e633eb10b44155761fe4c5ef28
    excerpt: "A document run carries the fixed map `{unresolvable_source: BLOCK}`, because it has no story to declare a wider one."
  - source: docs/design/10-sequencer-and-contracts.md#5-2-validation-order
    hash: sha256:9f1bf77b7e84302ff6f3f20260228d57390cc97ab8e8d3f68f52c3ff2658aab8
    excerpt: "| 10 | `changed[]` is a subset of `claimed_paths` | refuse, reason `UNCLAIMED_CHANGE`; this **is** a phase attempt, because real bytes were written outside the claim |"
  - source: docs/design/10-sequencer-and-contracts.md#5-4-transition-oracles
    hash: sha256:ffa41b5d270dc260e28fa9f6bdbc855069a6e922d1148c74b25860dba63484dc
    excerpt: "the phase declared `writes: docs` and `changed[]` is non-empty, unless it is marked conditional, in which case an empty change set needs a non-empty `note`; every changed path exists in the root with the bytes the checkpoint will hold"
  - source: docs/design/10-sequencer-and-contracts.md#6-handoff-envelope
    hash: sha256:747b6340fc5c2348aad33ca5488012808670b3503b311d7b7d0f1204625afd4c
    excerpt: "`next` is never empty and is never a description. One exact command."
  - source: docs/design/11-artifact-registry.md#1-template-registry
    hash: sha256:fabb8d2f142dcde1a31bc53768f8a46d01cac3ea4a7f6b73db22479cc89b5553
    excerpt: "| `clarification` | `.devforgeai/skills/clarify/templates/clarification.md` | 1 | `^CLR-[0-9]{3}$` | id, story, template, template_version, date, status | Question, Answer, Authority |"
  - source: docs/design/11-artifact-registry.md#2-artifact-path-patterns
    hash: sha256:2d2e97afff50edf6b35bf674b1de217c684d5091361e5f1deae12de52b95fb51
    excerpt: "| `docs/plan/<slug>/stories/STORY-NNN.md#clarifications` | `clarification` | clarify | sequencer |"
  - source: docs/design/11-artifact-registry.md#6-known-divergences
    hash: sha256:8a78656458735ce54ac73010da3b8fc87bbb7017a5a9268f85b210249736b82a
    excerpt: "The template renders an OBSERVED section inside each of the three Markdown files, the way `clarification` renders a section inside a story."
  - source: docs/design/02-skill-roster.md#clarify
    hash: sha256:55d952cce82953a09287f353d9b85050896890886f4ad6548f4e38cf8ca1f8eb
    excerpt: "- Question-generator lists ambiguities in a story."
  - source: docs/design/02-skill-roster.md#handoff-decision-tables
    hash: sha256:1dac784b4670cc7559f323011dfe304dfe8c0baf349063162f90d76d902c5d3c
    excerpt: "| clarify | resolved | `/dev {story}` |"
  - source: docs/design/05-subagent-sets.md#sets-per-skill
    hash: sha256:9e12f3beb236a025c18d40e741c09ba675bd71d2d87f56e2b205c7556b944bf9
    excerpt: "| clarify | ambiguity-finder, question-writer, answer-recorder |"
  - source: docs/design/05-subagent-sets.md#contract-format
    hash: sha256:23d8c21c51ca70b053f4661b32249b86a330c816e02db1219be72d5a9bc07a4e
    excerpt: "`must_not` is compiled into the agent prompt verbatim."
  - source: docs/design/templates/story.md#acceptance-criteria
    hash: sha256:858884c170a1e7036346f1887791672316583bca6f1f4730ceb5961e35a3c166
    excerpt: "A story has an unresolved assumption when the text `ASSUMPTION:` appears anywhere in the body outside `## Clarifications`; dev's gate applies `gate_policy.unresolved_assumption` until `/clarify` moves the answer into Clarifications and removes the tag."
  - source: docs/design/templates/story.md#clarifications
    hash: sha256:2a503014f37681ba2f64eede5fc6a30f21a3aaffaec3abf9cae1368077cbe816
    excerpt: "None. (`/clarify` appends dated Q/A entries here; nothing else may edit this file after `ready`.)"
  - source: docs/design/12-post-mvp.md#pm-01
    hash: sha256:84de4052d2f508313af4d327a9b15b9f9abcd1d50ca563ce68d4bbfdea39785e
    excerpt: "Until PM-01 lands: required isolation is a declaration compiled into the target profile, and a generated adapter is a candidate that a human installs."
---

# Skill Specification: clarify

A stranger with no conversation history must be able to build this skill from this document alone. Every question the generator would otherwise ask is answered below.

## 0. Generator instructions

These instructions are addressed to the skill-generating agent (Anthropic's `skill-creator` skill, or DevForgeAI's `skill-generator`). They replace its interview.

### Cold-session prompt

Paste this into a fresh session from the repository root:

```
Use the skill-creator skill to build the skill specified in docs/design/specs/SKILL-SPEC-010-clarify.md.
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
6. **Output location** is given in the prompt. Create `./out/clarify/`. Do not write anywhere else except the `clarify-workspace/` sibling that eval runs require.
7. **On ambiguity, stop before output.** If the spec is still `draft`, contains an unresolved authoring assumption, omits a section, contradicts itself, or leaves a decision this document does not make, do not guess and do not write candidate skill files. End with a list titled `SPEC GAPS` naming each section and question. The spec author fixes and approves the spec before re-running.
8. **Fidelity over creativity.** Use the description in section 3 verbatim. Use the worker contracts in section 7d verbatim as `agents/<role>.md` bodies, adding only the framing the grader agent in skill-creator uses (Role, Inputs, Process, Output). Do not add steps, tools, or behaviours the spec does not mention.
9. **Finish with the acceptance checks** in section 14 and include their output in your final message.

## 1. Identity

| Field | Value |
|-------|-------|
| name | `clarify` (kebab-case, 7 characters, equals the directory name, no `claude`/`anthropic` prefix) |
| title | Story Clarification |
| purpose | Turn every undecided value a story still carries into a dated question-and-answer block inside that story's Clarifications section, and remove the tag that keeps dev's gate refusing the story. |
| category | devforgeai-phase |
| version | 1.0.0 (skill-package version written to `metadata.version`; not the DevForgeAI or Research Core version) |

## 2. Problem and requirements

**Without this skill:** a story reaches dev carrying an inline `ASSUMPTION:` tag on one of its acceptance criteria. Two things then happen, both recorded as observed failure modes in `07-purpose-and-enforcement.md` section 2. Either the agent invents the missing value and builds to it — the "invents requirements or scope" row — and the story passes its own tests because the test was written to the invented value; or the agent edits the story to remove the inconvenient tag and declares the story ready, which is the "declares done because a file exists or a checkbox is ticked" row applied to a document. In both cases the decision that was actually made is nowhere on disk, so `analyze` cannot flag it, `review` cannot check the code against it, and `retro` cannot learn from it. A human who later asks "why does empty input return an empty string rather than an error?" finds no record and no author.

| ID | Kind | Requirement |
|----|------|-------------|
| R1 | explicit | Take one story id, find every `ASSUMPTION:` span in that story's body outside `## Clarifications`, and report it with its line and its criterion number. Source: `templates/story.md#acceptance-criteria`. |
| R2 | explicit | Write one `CLR-NNN` block per ambiguity under the story's `## Clarifications` section, in the `clarification` template's shape (`11-artifact-registry.md` section 1). |
| R3 | explicit | Record the human's answer and the authority who gave it into the matching `CLR-NNN` block, and remove the `ASSUMPTION:` span the answer settles, so `gate_policy.unresolved_assumption` stops refusing the story at `devforgeai phase start dev`. |
| R4 | implicit | Edit nothing else in the story. The story is write-once when its status becomes `ready`, except `status` and `## Clarifications` (`templates/story.md` header comment). A clarification run that reworded a criterion would silently change the contract dev builds to. |
| R5 | implicit | Ask the human rather than decide. A worker that picks a value is the failure mode in section 2; the closed status set carries `needs_user` precisely so a worker can stop and get a human decision on the first ask (`10-sequencer-and-contracts.md` section 3.1). A `needs_user` envelope carries no files, so the phase that asks is never the phase that writes the question. |
| R6 | discovered | `needs_user` blocks the run rather than closing it (`10-sequencer-and-contracts.md` section 3.1): status stays `active`, the lease is released, the candidate root survives and `run.yaml#blocked_at` names the phase. The answer round-trip is therefore one run in two sessions: `/clarify <story> --continue` is `devforgeai phase start clarify <story>` on that blocked run, which resumes it at `blocked_at` with attempts reset, and the flag changes only what `question_writer` reads. Source: open item OI-5. |
| R7 | discovered | The `questions` and `record_answers` phases declare `writes: docs`, and the `document` oracle fails a `writes: docs` phase that changed no file (`examples/hooks/devforgeai.py` `check_document`). Neither is marked conditional, so every reachable passing path through both phases edits the story file inside the candidate root. Source: `10-sequencer-and-contracts.md` section 5.4. |
| R8 | discovered | The `clarification` template has no file of its own: it renders as a section inside the story, the way `observed-constraints` renders inside the three architecture documents. Source: `11-artifact-registry.md` section 6, divergence 3. |

## 3. Description

```yaml
description: >
  Resolve the open questions in one DevForgeAI story. Find every ASSUMPTION span the story
  still carries, write a dated CLR block for each under its Clarifications section, record
  the human's answer and the authority who gave it, and remove the tag so the dev gate stops
  refusing the story. Use this skill when a story is blocked on an undecided value, when a
  handoff or a gate names an unresolved assumption, when a plan run reports stories its
  critic flagged, when someone asks what an acceptance criterion actually means, or when a
  story is vague enough that two developers would build different things. It appends to
  Clarifications and changes nothing else in the story. Do NOT use it to rewrite a story or
  its acceptance criteria (use plan), to change an architecture decision (use amend), to
  audit traceability across a whole plan (use analyze), or to implement the story (use dev).
```

Character count: 886 / 1024.

## 4. Trigger set

```json
[
  {"query": "/clarify STORY-007", "should_trigger": true},
  {"query": "dev refused STORY-012 saying there is an unresolved assumption, sort it out", "should_trigger": true},
  {"query": "criterion 3 of docs/plan/billing/stories/STORY-004.md says the timeout value is undecided. can you get that pinned down", "should_trigger": true},
  {"query": "plan just finished and the handoff lists STORY-007 and STORY-011 as flagged. deal with the flags", "should_trigger": true},
  {"query": "whats criterion 2 on STORY-019 actually asking for? its ambiguous and i dont want to guess", "should_trigger": true},
  {"query": "we decided in standup that empty input returns an empty string. record that against STORY-001 please", "should_trigger": true},
  {"query": "i answered the questions at the bottom of STORY-007, pick it up from there", "should_trigger": true},
  {"query": "story-021 has three ASSUMPTION tags left in it, i need them resolved before the sprint starts", "should_trigger": true},
  {"query": "two devs read STORY-015 and built different things. make the story say which one is right", "should_trigger": true},
  {"query": "the rate limit in STORY-011 is not in techstack.md anywhere, what do we do", "should_trigger": true},
  {"query": "implement STORY-007, the criteria all look clear to me", "should_trigger": false},
  {"query": "split EPIC-003 into stories and write acceptance criteria for each", "should_trigger": false},
  {"query": "the constitution says we use Dapper but the story assumes an ORM, change the constitution", "should_trigger": false},
  {"query": "check whether every PRD requirement in the shop plan has a story", "should_trigger": false},
  {"query": "review the diff on STORY-004 before I open a PR", "should_trigger": false},
  {"query": "re-run the failing tests for STORY-004 and tell me which criterion broke", "should_trigger": false},
  {"query": "STORY-009 context hash is stale because techstack.md moved, fix the bundle", "should_trigger": false},
  {"query": "explain what an acceptance criterion is, my team keeps arguing about it", "should_trigger": false},
  {"query": "write a FAQ page for the docs site answering our top ten support questions", "should_trigger": false},
  {"query": "the qa report on STORY-013 says criterion 2 failed, go fix the code", "should_trigger": false}
]
```

## 5. Use cases

### UC-1: One undecided value, answered in the same sitting
- **User says:** "/clarify STORY-007"
- **Steps:** 1. `devforgeai phase start clarify STORY-007` runs the document gate and opens the run. 2. `ambiguity_finder` reads the story and writes one finding into its run-scoped evidence directory: criterion 3, line 84, span `ASSUMPTION: empty input behaviour is undecided`. 3. `question_writer` edits the story in the candidate root, appending a `### CLR-001` block under `## Clarifications` with `status: open` and an empty `#### Answer`, and returns `pass` claiming that path; the sequencer checkpoints it. 4. `answer_recorder` finds an `open` block with an empty answer and returns `needs_user` claiming nothing, so the sequencer writes a `REQUIRE_HUMAN` handoff naming that block and blocks the run at `record_answers`: status stays `active`, the lease is released, `run.yaml#blocked_at` is set, and the candidate root — which holds the `CLR-001` block — survives (section 9, OI-12). 5. The user writes the answer into `CLR-001`'s `#### Answer` body in the candidate root's copy of the story, the path the handoff names. 6. `/clarify STORY-007 --continue` is `devforgeai phase start clarify STORY-007` on that blocked run, which resumes it at `record_answers` in the same root with attempts reset; `question_writer` normalises the hand-written answer into the block's shape and sets `status: answered`; `answer_recorder` fills `#### Authority`, deletes the `ASSUMPTION:` span from criterion 3 and puts the decided value in its place.
- **Result:** after the second run, `docs/plan/<slug>/stories/STORY-007.md` carries a dated `CLR-001` block, criterion 3 states a value, no `ASSUMPTION:` text remains outside `## Clarifications`, and the handoff's first next step is `/dev STORY-007`. The first run left the question on disk for the human to answer.

### UC-2: The answer already exists upstream
- **User says:** "criterion 3 of STORY-004 says the timeout is undecided but techstack.md pins it at 30 seconds, use that"
- **Steps:** 1. The gate opens the run. 2. `ambiguity_finder` records the span and the `context[]` entry in the story's frontmatter whose anchor covers the same subject. 3. `question_writer` writes the `CLR-001` block with the question and, because the user named the authority in the invocation, `status: answered` and the source anchor in `#### Authority`. 4. `answer_recorder` removes the span and writes the value into criterion 3.
- **Result:** one run, no `needs_user`, the story is unblocked, and the authority line names the anchor rather than a person.

### UC-3: Nothing is actually ambiguous
- **User says:** "/clarify STORY-019"
- **Steps:** 1. The gate opens the run. 2. `ambiguity_finder` records zero findings. 3. `question_writer` edits the story with one `### CLR-NNN` block whose `#### Question` is the reason the run was opened and whose `#### Answer` is `None required.`, because the `document` oracle fails a `writes: docs` phase that changed no file. 4. `answer_recorder` fills `#### Authority` with the invoking user and changes nothing else.
- **Result:** the story is byte-identical outside `## Clarifications`, an auditable record says `/clarify` ran on that date and found nothing, and the handoff's first next step is `/dev STORY-019`.

## 6. Inputs and outputs

### Inputs
| Input | Format | Example file | Required |
|-------|--------|--------------|----------|
| story id | positional argument matching `^STORY-(HOTFIX-)?[0-9]{3}$` | `STORY-001` | yes |
| story | markdown with frontmatter, `story` template version 3, owned by `plan` at `.devforgeai/skills/plan/templates/story.md` | `docs/design/examples/fixtures/clarify/docs/plan/tinyapp/stories/STORY-001.md` | yes |
| `--continue` flag | boolean; selects the hand-answered reading path for `question_writer` | not a file | no |
| `.devforgeai/state.yaml` enforcement block | YAML, written by the sequencer at `devforgeai phase start` | `.devforgeai/state.yaml` | yes; the run's `write_fence` is read from it |

### Outputs
| Output | Format | Location | Template |
|--------|--------|----------|----------|
| clarification blocks | markdown section inside the story | `docs/plan/<slug>/stories/STORY-NNN.md#clarifications` | `clarification`, at `.devforgeai/skills/clarify/templates/clarification.md`, seeded by `assets/clarification.md` |
| phase results | JSON, written by the sequencer | `.devforgeai/work/clarify-STORY-NNN/<phase>-result.json` | none |
| phase reports | markdown, written by the sequencer | `.devforgeai/work/clarify-STORY-NNN/<phase>-report.md` and `docs/reports/clarify-clarify-STORY-NNN-<phase>.md` | none |
| handoff | JSON plus its rendering | `.devforgeai/work/clarify-STORY-NNN/handoff.json` | `handoff` |

The `clarification` template has no file of its own. It renders inside the story, exactly as `observed-constraints` renders inside the three architecture documents (`11-artifact-registry.md` section 6, divergence 3). The `required_frontmatter` keys of the template become the fenced YAML block at the top of each `CLR-NNN` entry, and its `required_sections` become the three fourth-level headings.

### Output template

The block `question_writer` appends and `answer_recorder` completes, inside `## Clarifications`:

````
### CLR-001

```yaml
id: CLR-001
story: STORY-007
template: clarification
template_version: 1
date: 2026-09-02
status: answered          # open | answered
```

#### Question

Criterion 3 does not say what the system returns when the input is an empty string.

#### Answer

An empty input returns an empty string. No error is raised.

#### Authority

bryan, 2026-09-02, in the session that opened run clarify-STORY-007.
````

`id` matches `^CLR-[0-9]{3}$` and is allocated in append order within the story, starting at `CLR-001`. `status: open` means the question is written and unanswered; `status: answered` means `#### Answer` and `#### Authority` are both non-empty and the matching `ASSUMPTION:` span has been removed from the body.

### Return envelope (DevForgeAI-anatomy skills only)

One schema, both providers: `devforgeai.worker-result/v1`, normative in `schemas/devforgeai/v1/worker-result.schema.json`. A worker's final message is exactly this object, with no Markdown fence and no surrounding prose. The two writing phases have already edited the story inside the candidate root when they return; the receipt claims it. `ambiguity_finder` writes only into its own run-scoped evidence directory.

```yaml
schema: devforgeai.worker-result/v1
run: "clarify-STORY-007"
skill: "clarify"
phase: "questions"
agent: "question_writer"
status: pass | fail | needs_user | could_not_run
reason_code: runner_missing | timeout | network | hook_fault   # required only when status is could_not_run
candidate: {id: "clarify-STORY-007", input_checkpoint: "find_ambiguity"}
claimed_paths: ["docs/plan/tinyapp/stories/STORY-007.md"]   # root-relative, at most 64; empty on any non-pass status
evidence_refs: ["docs/plan/tinyapp/stories/STORY-007.md"]   # at most 16
note: "1 ambiguity, 1 CLR block appended, awaiting an answer"
issues: [{id, kind, text}]                                  # at most 10
```

At `devforgeai ingest-result` the sequencer derives `changed[{path, blob_sha256, kind}]` from the checkpoint diff, refuses when `changed` is not a subset of `claimed_paths` (`UNCLAIMED_CHANGE`) or a path is outside the fence, validates the written story against the `story` version 3 template header, runs the transition oracle inside the root, writes `<phase>-result.json` with `changed` and the checkpoint ref, releases the lease and advances. `next` requires `status: fail` plus a registry `rewind_to`; no clarify phase declares one, so the key is never present. Unknown keys refuse the receipt.

`gate_policy` (`BLOCK | REQUIRE_HUMAN | WARN | OFF`) is a defect-to-action map declared in the consumed artifact, never a status returned here. A document run carries the fixed map `{unresolvable_source: BLOCK}`.

## 7. Procedure

### 7a. Steps

The body of `SKILL.md`. Imperative voice; each step says why it matters.

1. Parse the positional story id and the optional `--continue` flag. Read nothing else in this window — why: everything read here stays in the primary window for the whole run and cannot be unloaded, and the primary-window contract in `01-skill-anatomy.md` forbids opening an artifact.
2. Call `devforgeai phase start clarify <story-id>`. On exit 1, print the defect list the gate wrote to stderr and stop — why: the gate opens the candidate root the two writing phases edit in, so a refusal leaves nothing half-written. `clarify` is a plain `document` skill and not one of the two story-anchored ones (`10-sequencer-and-contracts.md` section 4), so this gate checks the fence and not the story: a story whose digests are placeholders can still be clarified, which is what makes this command the repair route for a dev gate that refused an unresolved assumption.
2a. Run `devforgeai status` and paste its block into every dispatch below. The block names `run`, `candidate.root`, `phase`, `fence` and `granted_keys` — why: a worker edits the story inside the candidate root and cannot resolve it from the canonical tree, and this block is the one thing a dispatch carries that is not a path or an id.
3. On exit 0, dispatch `agents/ambiguity_finder.md` with the status block, the story path the run's fence names, and the `--continue` flag value. Pass paths, flag tokens and the block only — why: pasting a criterion into a prompt puts the story's contract in two places, and the worker reads the file itself.
4. Dispatch `agents/question_writer.md` with the status block, the story path and `.devforgeai/work/<run>/find_ambiguity-result.json`. Load `references/questions.md` before the dispatch — why: the block shape and the append rules are what the phase's checkpoint is validated against.
5. Dispatch `agents/answer_recorder.md` with the status block, the story path and `.devforgeai/work/<run>/questions-result.json` — why: this is the phase that asks the human, because a `needs_user` receipt claims nothing and the `questions` phase owes its `document` oracle a change.
6. Advance on a returned `pass`; stop and print on `needs_user` or `could_not_run` — why: `needs_user` blocks the run at that phase without consulting the attempt counter, so there is nothing left to dispatch until the user has acted.
7. Print the block the sequencer rendered into `.devforgeai/work/<run>/handoff.json`, verbatim. Compose nothing — why: rule 8 of the handoff rendering rules says the renderer adds nothing, and `devforgeai status` must print the identical block from a cold session.
8. When the handoff reports the run `ready_to_promote` and the user asks for the promotion, call `devforgeai promote <run>` — why: promotion moves the edited story from the candidate root into the canonical checkout under the lock, and a `REQUIRE_HUMAN` block is the only state in which the model may ask for it.

A transition failure is not the primary window's business: `devforgeai phase next` exits 1 with the oracle's problem rows, the sequencer rewinds the candidate root to the phase's input checkpoint, and the same worker returns a fresh receipt. The primary window dispatches once per phase.

`--continue` is not a fresh run. It is `devforgeai phase start clarify <story>` on the run the `needs_user` result blocked: same skill, same argument, so `phase start` resumes it at `run.yaml#blocked_at` with `attempts` reset instead of refusing (`10-sequencer-and-contracts.md` sections 2 and 3.1). The candidate root, its checkpoints and the `CLR-NNN` blocks the `questions` phase wrote are the ones the resumed run continues from; the flag only tells `question_writer` to read existing blocks as hand-answered (open item OI-5).

### 7b. Sub-phases and workers

Gate, Record and Handoff dispatch no LLM: they are `devforgeai` sequencer operations, and Slice is a sequencer step inside `phase start` (open item OI-1). Only Work and Write name a worker.

| # | Sub-phase | Performed by | Writes | Isolation |
|---|-----------|--------------|--------|-----------|
| 0 | Gate | sequencer: `devforgeai phase start clarify <story-id>`, which also opens the candidate root | sequencer | n/a |
| 1 | Slice | sequencer: a step inside `phase start` that resolves the story's already-hashed bundle into `.devforgeai/work/<run>/context.json`. No worker | sequencer | n/a |
| 2 | Work: `find_ambiguity` | worker: `ambiguity_finder` | evidence | preferred |
| 3 | Write: `questions` | worker: `question_writer` | candidate | required |
| 4 | Write: `record_answers` | worker: `answer_recorder` | candidate | required |
| 5 | Record | sequencer: `devforgeai phase next` | sequencer | n/a |
| 6 | Handoff | sequencer: `devforgeai phase next` marks the run `ready_to_promote` and writes the `REQUIRE_HUMAN` block whose only forward step is `devforgeai promote <run>`; `SKILL.md` runs that command only after the user confirms in the session, and the promotion writes the run's second handoff block | sequencer | n/a |

`clarify` has no Review sub-phase. The registry gives it three phases and no critic (`10-sequencer-and-contracts.md` section 4); the independent check on its output is `check_clarify_edit.py`, which compares the checkpoint's bytes to the previous checkpoint's and needs no model judgement. `ambiguity_finder` is the one judge: its `Write` reaches only `.devforgeai/work/<run>/evidence/ambiguity_finder/`, a gitignored, run-scoped directory outside the candidate root that is never promoted, and its findings file is named in `evidence_refs`.

For an anatomy-governed skill, `SKILL.md` dispatches each worker through the selected target's provider-native worker mechanism, using the generated target profile, file paths and the `devforgeai status` block. It never pastes or paraphrases artifact content, objectives, or acceptance criteria into the prompt. Its Bash grammar is exactly `devforgeai status | phase start <skill> <arg> | phase fail --reason | validate | promote <run>`; every other sequencer operation is hook-only. The `Isolation` column is the DevForgeAI contract value compiled into the target profile, not Claude's `isolation` frontmatter field; the framework does not use Claude's worktree isolation or `EnterWorktree`, because both fork from HEAD and the run's phases build linearly on one candidate root. Runtime verification of isolation is `12-post-mvp.md#pm-01`.

### 7c. Evidence and gate table

One row per registry phase, in registry order. `<run>` is `clarify-STORY-NNN`.

| phase | worker | deterministic gate check | gate_policy | evidence file | transition oracle |
|---|---|---|---|---|---|
| `find_ambiguity` | `ambiguity_finder` | run-level gate at `devforgeai phase start`: `clarify` is a known skill of kind `document`; no run is already active; the fence pattern `docs/plan/*/stories/<arg>.md` is repository-relative, contains no `..`, and is not sequencer-owned; and no active or `ready_to_promote` run holds that path (`FENCE_OVERLAP`). At ingest: `claimed_paths` is empty, because the registry declares the phase `writes: none` and the worker header `writes: evidence`, and any change inside the candidate root refuses the receipt as `UNCLAIMED_CHANGE`; the dispatcher allows this worker's writes only under `.devforgeai/work/<run>/evidence/ambiguity_finder/` and denies every other path at `PreToolUse` | document run's fixed map `{unresolvable_source: BLOCK}`; every `devforgeai phase start` defect is a refusal whatever a declared value says, and only `test_runner_missing` changes behaviour at transition time, which this phase never reaches because it brokers no command | `.devforgeai/work/<run>/find_ambiguity-result.json`, `.devforgeai/work/<run>/find_ambiguity-report.md` | `report_only`: no file outside the fence changed since the gate snapshot and the whole-tree package and import policy holds |
| `questions` | `question_writer` | ingest validation: `changed` derived from the checkpoint diff is a subset of `claimed_paths`, the single changed path canonicalises inside `candidate.root`, is not sequencer-owned, matches the fence pattern, and is allowed by the phase's `writes: docs` mode; then the whole-root package and import rescan before the checkpoint. `scripts/check_clarify_edit.py` compares the phase's checkpoint to its input checkpoint and exits 1 unless every differing line is one of the three sanctioned edit kinds in `references/questions.md`; that import into `devforgeai ingest-result` is designed and not implemented today, so what the sequencer actually enforces at this phase is the validation above and the script runs only when a human runs it (section 9, row 5) | `{unresolvable_source: BLOCK}`; an `UNCLAIMED_CHANGE` refuses the receipt as a protocol error and does not consume an attempt | `.devforgeai/work/<run>/questions-result.json`, `.devforgeai/work/<run>/questions-report.md` | `document`: the phase produced at least one file and every declared output with non-null content exists on disk |
| `record_answers` | `answer_recorder` | as `questions`, plus `scripts/check_clarify_edit.py --require-resolved`, which exits 1 when a `CLR-NNN` block reads `status: answered` while the `ASSUMPTION:` span its `#### Answer` settles is still present in the body outside `## Clarifications`; that invocation is designed sequencer-side and unimplemented today, so it too is a human-run check (section 9, row 5). A `needs_user` receipt carries an empty `claimed_paths`, so this phase either edits the story and claims it or changes nothing and closes the run | `{unresolvable_source: BLOCK}` | `.devforgeai/work/<run>/record_answers-result.json`, `.devforgeai/work/<run>/record_answers-report.md`, then `.devforgeai/work/<run>/handoff.json` | `document`: as `questions`. On pass this is the last phase: the run is marked done, enforcement is cleared, and the handoff's `next` is filled from the section 7e table. A `needs_user` result writes a `REQUIRE_HUMAN` handoff immediately, without consulting the attempt counter and without reaching this oracle |

Attempt budgets, materialised into the run file from the registry: `find_ambiguity: 2`, `questions: 2`, `record_answers: 2`. No `clarify` phase declares `rewind_to`, so a `fail` receipt carrying `next` is refused; a `fail` without `next` becomes a transition problem row, the phase retries to its limit, and the run then blocks `REQUIRE_HUMAN` (open item OI-4).

Promotion is never automatic. The last passing `devforgeai phase next` marks the run `ready_to_promote` and writes a `REQUIRE_HUMAN` handoff whose only forward step is `devforgeai promote <run>`; the run therefore ends in two handoff blocks, the ready one and the promoted one. `devforgeai promote <run>`, which `SKILL.md` calls only after the user confirms in the session, is what merges the candidate root into the canonical checkout under `.devforgeai/lock`, refusing on `STALE_BASE` when canonical HEAD has moved past the run's pinned `base_ref`, on `DIRTY_TARGET` when the story is dirty in the canonical checkout, and on `MERGE_CONFLICT` when the rebase cannot replay the run. All three are refusals of `devforgeai promote <run>`, never of `devforgeai phase next`, and each is a handoff row in section 7e.

Both `check_clarify_edit.py` invocations are designed as sequencer-side checks and are not implemented in `examples/hooks/devforgeai.py` today; section 9 records that gap and what the run does without them.

### 7d. Worker contracts

Each block becomes `agents/<role>.md` verbatim, wrapped in skill-creator's Role / Inputs / Process / Output framing, and compiles to one provider profile per target. `name` is the canonical registry worker name, which is what a hook receives as `agent_type`; the compiled filename carries the skill prefix so two skills' profiles cannot collide. `tools` are the Claude names and `tools_codex` the Codex ones, where `apply_patch` stands in for `Edit` and `Write`. `model: inherit` keeps the worker on the session's model, which is what the terminal-only constraint leaves available. No clarify phase grants a stack command key, so no worker here carries `Bash(devforgeai run *)`. Claude-only frontmatter — `hooks`, `memory`, `background`, `permissionMode`, and Claude's own `isolation` — is omitted from every profile.

```yaml
name: ambiguity_finder
description: Dispatch this worker at the find_ambiguity phase to judge one story and list every undecided value it still carries.
skill: clarify
writes: evidence
model: inherit
tools: [Read, Grep, Glob, Bash(devforgeai status), Write]
tools_codex: [Read, Grep, Glob, Bash(devforgeai status), apply_patch]
skills: []
compiled_to: [.claude/agents/clarify-ambiguity_finder.md, .codex/agents/clarify-ambiguity_finder.toml]
responsibility: List every undecided value in one story, one row per ambiguity, with its line, its criterion number and the exact span that marks it.
inputs:
  - the devforgeai status block pasted into the dispatch, which names run, candidate.root, phase, fence and granted_keys
  - .devforgeai/work/<run>/context.json, the bundle the sequencer sliced at phase start
  - the story path the run's fence names, read inside the candidate root
  - the --continue flag token, which selects whether existing CLR blocks are read as answered
outputs:
  - .devforgeai/work/<run>/evidence/ambiguity_finder/ambiguities.md, one section per finding with its criterion, line, span and kind, plus one row per CLR block already in the story with its id and status, written in its own run-scoped evidence directory and named in evidence_refs
  - issues: one row per finding, bounded at ten
  - note: the counts of ambiguities found and existing CLR blocks read
must_not:
  - decide the value an ambiguity leaves open
  - read a file the run's fence or the story's own frontmatter does not name
  - write anywhere but its own run-scoped evidence directory, or run any stack command key
isolation: preferred
returns: devforgeai.worker-result/v1
body:
  job: Judge one story for undecided values and name each with the exact span that marks it.
  inputs: The list above, read under the candidate root; nothing outside it is opened.
  rules: references/find_ambiguity.md, what counts as an ambiguity and what does not, and the must_not list.
  receipt: One devforgeai.worker-result/v1 object; claimed_paths is empty on every status, and evidence_refs names the ambiguities file it wrote under its run-scoped evidence directory.
```

```yaml
name: question_writer
description: Dispatch this worker at the questions phase to append one CLR block per ambiguity under the story's Clarifications section.
skill: clarify
writes: candidate
model: inherit
tools: [Read, Grep, Glob, Bash(devforgeai status), Edit, Write]
tools_codex: [Read, Grep, Glob, Bash(devforgeai status), apply_patch]
skills: []
compiled_to: [.claude/agents/clarify-question_writer.md, .codex/agents/clarify-question_writer.toml]
responsibility: Edit the story inside the candidate root so one CLR block per ambiguity is appended under its Clarifications section, in the clarification template's shape, marking each block answered where the invocation or the story already carries the answer and open where it does not.
inputs:
  - the devforgeai status block pasted into the dispatch
  - .devforgeai/work/<run>/context.json
  - the story path the run's fence names, read inside the candidate root
  - .devforgeai/work/<run>/find_ambiguity-result.json and the ambiguities file its evidence_refs names
  - references/questions.md, for the block shape and the three sanctioned edit kinds
  - assets/clarification.md, the block skeleton
outputs:
  - the story path, edited inside the candidate root and claimed
  - one CLR block per ambiguity, each with its id, its criterion and its status
must_not:
  - change any line outside the Clarifications section, other than the ASSUMPTION span an answered block settles
  - answer a question the invocation, an existing CLR block, or a story context entry does not already answer
  - return a status other than pass; a non-pass status claims nothing and the document oracle would then fail this phase
  - allocate a CLR id that is already used in that story
  - write outside the candidate root, or outside the run's fence inside it
isolation: required
returns: devforgeai.worker-result/v1
body:
  job: Append one CLR block per ambiguity so the question is on disk before anyone is asked to answer it.
  inputs: The list above, read under the candidate root.
  rules: references/questions.md, the three sanctioned edit kinds, and the must_not list.
  receipt: One devforgeai.worker-result/v1 object; claimed_paths is exactly the story path, and the status is always pass.
```

```yaml
name: answer_recorder
description: Dispatch this worker at the record_answers phase to complete each answered CLR block and remove the span it settles, or to ask when a block is still open.
skill: clarify
writes: candidate
model: inherit
tools: [Read, Grep, Glob, Bash(devforgeai status), Edit, Write]
tools_codex: [Read, Grep, Glob, Bash(devforgeai status), apply_patch]
skills: []
compiled_to: [.claude/agents/clarify-answer_recorder.md, .codex/agents/clarify-answer_recorder.toml]
responsibility: Complete each answered CLR block's Authority body and remove the ASSUMPTION span that block settles, inside the candidate root, or return needs_user claiming nothing when a block is still open and unanswered.
inputs:
  - the devforgeai status block pasted into the dispatch
  - .devforgeai/work/<run>/context.json
  - the story path the run's fence names, read inside the candidate root as the questions checkpoint left it
  - .devforgeai/work/<run>/questions-result.json
  - references/record_answers.md, for the removal rule and the authority forms
outputs:
  - the story path, edited inside the candidate root and claimed, on status pass
  - one Authority body per answered block, and the criterion text with each settled span replaced by the value its block records
must_not:
  - mark a block answered whose Answer body is empty
  - change any file alongside a needs_user status; a non-pass receipt claims nothing and any change refuses it as UNCLAIMED_CHANGE
  - remove an ASSUMPTION span no answered CLR block settles
  - change a criterion beyond replacing the span with the value its CLR block records
  - write outside the candidate root, or outside the run's fence inside it
isolation: required
returns: devforgeai.worker-result/v1
body:
  job: Settle each answered block and take its span out of the body, or ask once for the blocks still open.
  inputs: The list above, read under the candidate root.
  rules: references/record_answers.md, the removal rule and the three authority forms, and the must_not list.
  receipt: One devforgeai.worker-result/v1 object; on pass claimed_paths is exactly the story path, on needs_user it is empty and each open block is one issues row.
```

A producer's tools are the read set plus `Edit` and `Write`, which Codex serves as `apply_patch`; the judge's are the read set plus a `Write` the dispatcher confines to `.devforgeai/work/<run>/evidence/<agent>/`, a gitignored, run-scoped directory outside the candidate root that is never promoted. Both include `Bash(devforgeai status)` and nothing else on the Bash surface, because no `clarify` phase grants a stack command key (open item OI-3).

### 7e. Handoff outcomes

The `handoff.outcomes` block the skill declares. The sequencer selects the row by receipt status and fills `{story}` and `{slug}` from state.

| Outcome | Next steps |
|---------|------------|
| pass, last phase, run `ready_to_promote` and not yet promoted | 1. `devforgeai promote {run}` — the first of the run's two blocks; `SKILL.md` runs the command only after the user confirms in the session, and promotion then writes the second block, which carries whichever `pass` row below matches |
| pass, promoted, no `ASSUMPTION:` span left outside Clarifications | 1. `/dev {story}` |
| pass, promoted, `analyze` has not run since the story changed | 1. `/dev {story}`. Also possible: `/analyze {slug}` |
| needs_user, raised by `record_answers` because a block is open and unanswered | 1. answer the open `CLR-NNN` blocks under `## Clarifications` in the candidate root's copy of `{story}`, the path the handoff names — the run is blocked, not closed, so the blocks the `questions` phase wrote are in the root and reach the canonical story only when the resumed run is promoted — then 2. `/clarify {story} --continue`, which resumes the blocked run at `record_answers`. Also possible: `devforgeai phase fail --reason <text>` to abandon the root, then `/status` |
| fail at `max_attempts` | 1. fix the cause the `open_items` name, then `/clarify {story} --continue`, which resumes the blocked run at `blocked_at` with attempts reset. Also possible: `devforgeai phase fail --reason <text>` to abandon the root, then `/status` |
| could_not_run, `reason_code: hook_fault` | 1. reinstall the dispatcher named in `.devforgeai/sessions/`, then 2. `/clarify {story}` |
| could_not_run, any other `reason_code` | 1. the repair route for that reason code, then 2. `/clarify {story}` |
| BLOCK, recorded by `devforgeai phase fail --reason` | 1. `/status` |
| `devforgeai promote {run}` refused `STALE_BASE` in worktree mode | 1. reconcile the canonical paths the refusal names, then `devforgeai promote {run}` — the sequencer already rebased the candidate root onto the new canonical HEAD, reran the last transition oracle and retried the fast-forward once, so this row is written only when that retry also failed |
| `devforgeai promote {run}` refused `STALE_BASE` in copy mode, or `MERGE_CONFLICT` after an aborted rebase | 1. reconcile the canonical paths the refusal names, then `devforgeai promote {run}` — no canonical byte moved and the run keeps its candidate root and every checkpoint |
| `devforgeai promote {run}` refused `DIRTY_TARGET` | 1. commit or discard the canonical story the refusal names, then `devforgeai promote {run}` |
| `phase start` refused `FENCE_OVERLAP` | 1. finish or abandon the run the refusal names, then `/clarify {story}` |

A gate refusal is not a row in this table. `devforgeai phase start` exits 1 with the defect list and writes no handoff (`10-sequencer-and-contracts.md` section 3.2), so `02-skill-roster.md`'s gate rows are corrected out of the decision table and recorded in section 9. When the story argument names no file at all, the primary window calls `devforgeai phase fail --reason` and the `BLOCK` row applies.

## 8. Bundled resources

### Layout (fixed)

```
clarify/SKILL.md            # at most 500 lines: identity, phase list, dispatch loop, handoff table
  references/find_ambiguity.md
  references/questions.md
  references/record_answers.md
  references/envelope.md
  agents/ambiguity_finder.md
  agents/question_writer.md
  agents/answer_recorder.md
  scripts/find_assumptions.py
  scripts/check_clarify_edit.py
  assets/clarification.md
```

Link depth: `SKILL.md` links to `references/`, `agents/`, `scripts/` and `assets/`; an `agents/*.md` links to `references/*.md`; nothing links further.

### scripts/

Both scripts are deterministic, non-interactive, print data to stdout and diagnostics to stderr, and document `--help`.

| File | Purpose | Invocation | Exit codes |
|------|---------|------------|------------|
| `find_assumptions.py` | Parse a story and emit every `ASSUMPTION:` span outside `## Clarifications` as JSON — line, criterion number, span text — plus every `CLR-NNN` block already present with its id and `status`. Invoked by a human before or after a run, and designed to be imported by the sequencer's document gate at `devforgeai phase start clarify` so a story with nothing to clarify is refused rather than run; that gate import is not implemented today (section 9, row 5) | `python3 scripts/find_assumptions.py STORY.md [--json]` | 0 ok, 1 the story does not parse as a version 3 story, 2 usage |
| `check_clarify_edit.py` | Compare a written story to the bytes its phase started from and exit non-zero unless every differing line belongs to one of the three sanctioned edit kinds in `references/questions.md`. With `--require-resolved`, additionally exit non-zero when a block reads `status: answered` while the span its answer settles is still in the body. Invoked by a human, and designed to be imported by the sequencer at `devforgeai ingest-result` for the `questions` and `record_answers` phases, comparing the phase's checkpoint to its input checkpoint; that import is not implemented today (section 9, row 5) | `python3 scripts/check_clarify_edit.py --before STORY.md --after WRITTEN.md [--require-resolved] [--json]` | 0 every differing line is sanctioned, 1 an unsanctioned edit (offending line numbers on stdout), 2 usage |

### references/

| File | Content | Load when |
|------|---------|-----------|
| `find_ambiguity.md` | What counts as an ambiguity: an `ASSUMPTION:` span; a criterion whose observable result names no value, unit or boundary; a criterion two readers can satisfy with different behaviour. What does not: a criterion that is merely terse, and anything inside `## Clarifications`. The shape of the `ambiguities.md` findings file this worker writes into its run-scoped evidence directory. | dispatching `ambiguity_finder` |
| `questions.md` | The `CLR-NNN` block shape from section 6, id allocation, `status` values, and the three sanctioned edit kinds `check_clarify_edit.py` accepts: replacing the template's `None.` line on the first append; appending or completing a `### CLR-NNN` block inside `## Clarifications`; replacing one `ASSUMPTION:` span in the body with the value an answered block records. The `--continue` reading rule: normalise a hand-written answer into the block's shape rather than re-asking. | dispatching `question_writer` |
| `record_answers.md` | The removal rule (a span is removed only when a block whose `#### Answer` settles it reads `status: answered`), the three authority forms (a named person with a date; a source anchor from the story's own `context[]`; the invoking user for a `None required.` block), and why the criterion's wording otherwise stays byte-identical. | dispatching `answer_recorder` |
| `envelope.md` | The `devforgeai.worker-result/v1` receipt, its bounds (64 `claimed_paths`, 16 `evidence_refs`, 16 KiB note, 10 issues), the closed status set with `reason_code`, the rule that `claimed_paths` is empty on any non-pass status, and the rule that `next` needs a registry `rewind_to` no clarify phase declares. | every dispatch |

### assets/

| File | Used for |
|------|----------|
| `clarification.md` | The `CLR-NNN` block skeleton from section 6: the third-level heading, the fenced YAML block with the six template keys, and the three empty fourth-level headings. No guidance text; that lives in `references/questions.md`. |

### agents/

| File | Worker (from section 7d) |
|------|-------------------------|
| `ambiguity_finder.md` | `ambiguity_finder` |
| `question_writer.md` | `question_writer` |
| `answer_recorder.md` | `answer_recorder` |

## 9. Gotchas and edge cases

| Situation | What goes wrong | What to do instead |
|-----------|-----------------|--------------------|
| OI-1: `01-skill-anatomy.md` and `05-subagent-sets.md` give Slice to a framework worker, but no `clarify` phase dispatches one | A generated skill grows a fourth agent file with no registry phase to run it, and `agent_type` never matches at ingest | Slice is a sequencer step inside `devforgeai phase start`: it resolves the story's already-hashed bundle and writes `.devforgeai/work/<run>/context.json`, which every worker of the run is handed by path. This spec promises no slice phase and ships no slice agent file. |
| OI-2: `01-skill-anatomy.md` makes provenance conformance part of the gate, while an earlier draft of `10-sequencer-and-contracts.md` said the gate re-resolved `commands.hash` and nothing else | A spec that describes only `commands.hash` under-promises; one that applies story re-resolution to `clarify` over-promises, because `clarify` is not story-anchored | `AUTHOR-BRIEF.md` section 12 supersedes OI-2 and `10-sequencer-and-contracts.md` section 3.4 now carries it: a story gate re-resolves every `provenance[]` and `context[]` entry as well as `commands`, with `stale-hash` never downgradable and `unresolvable-source` downgradable only on a `scope: hotfix` story or under `--lenient` outside `docs/plan/`. That gate does not run for `clarify`: section 4 makes `qa` and `review` the only story-anchored document skills, so `clarify`'s gate checks the fence alone. |
| OI-3: `05-subagent-sets.md:28` gives workers `tools: [read]` | A generator either gives every worker the same tools or widens the judge's to include an unfenced write | Tools follow the role. A producer carries `Read`, `Grep`, `Glob`, `Bash(devforgeai status)` plus `Edit` and `Write`, which Codex serves as `apply_patch`; every write is denied outside `candidate.root` and outside the run's fence. The judge carries the read set plus a `Write` the dispatcher confines to `.devforgeai/work/<run>/evidence/<agent>/`. `Bash(devforgeai run *)` is granted only where a phase declares run keys, and no `clarify` phase does. |
| OI-4: `10-sequencer-and-contracts.md` section 5.4 has no outcome row for `status: fail` with no `next` | A reader assumes a failing phase passes silently | `examples/hooks/devforgeai.py:1017-1018` inserts `"<agent> reported fail"` as a transition problem row, so the phase retries to `max_attempts: 2` and then blocks `REQUIRE_HUMAN`. The section 7e table's `fail at max_attempts` row is that path. |
| OI-5: `02-skill-roster.md` gives `--continue`, and an earlier draft of `10-sequencer-and-contracts.md` closed the run on `needs_user` | A user expects `--continue` to resume and, under the closed-run reading, phase 1 would run again over a root that no longer existed | Settled: `10-sequencer-and-contracts.md` section 3.1 blocks the run instead of closing it, and section 2's `phase start` row resumes a blocked run when the skill and argument match. `--continue` is that resume — same run, same candidate root, resumed at `run.yaml#blocked_at` with `attempts` reset — and the flag changes only what `question_writer` reads. Section 7a says so. |
| OI-6: `adr` at a producer-exception path | Not reachable from `clarify` | `.devforgeai/provenance/adr/**` is declared for `architect`/`adr` and `amend`/`adr` and is not in `clarify`'s fence. `clarify` has no `adr` phase and writes nothing under `.devforgeai/provenance/`. Recorded so the open item is closed for this skill rather than silently inherited. |
| OI-7: `02-skill-roster.md` shows skills calling one another | A generated `SKILL.md` tries `devforgeai phase start dev` from inside a clarify run and is refused, because a run is already active | No skill invokes another skill's run. The `/dev {story}` edge is a handoff row filled by the sequencer; a human or a fresh session runs it. Section 7a's dispatch loop names no other command. |
| OI-8: `05-subagent-sets.md` writes worker names hyphenated (`ambiguity-finder`) while the registry writes them with underscores | `agent_type` fails the phase-agent binding check at validation step 5 and the envelope is refused | The registry name in `10-sequencer-and-contracts.md` section 4 is canonical: `ambiguity_finder`, `question_writer`, `answer_recorder`. It is the agent filename, the `agents/` table row, and the string compared to the stop event's `agent_type`. `05`'s hyphenated form is a display alias. |
| OI-9: `.devforgeai/stack.yaml` write path | Not reachable from `clarify` | The path is a producer exception restricted to `architect`'s `techstack` phase and `onboard`'s `code_map` phase. Every `clarify` phase is refused it as sequencer-owned, and it is not in `clarify`'s fence. `clarify` changes only the story file and never reads the stack. |
| OI-10: `/onboard`, `/drift` and `/status` take no positional argument | Not reachable from `clarify` | `/clarify` always carries a story id, which is both the `devforgeai phase start` argument and the `{arg}` substituted into the fence pattern `docs/plan/*/stories/<arg>.md`. |
| OI-11 (new): no worker has a hashing command, yet `provenance[]`, `context[]` and `commands.hash` are required story frontmatter and the gate refuses a placeholder digest | A worker's Bash surface is `devforgeai status` alone, so `story_writer` cannot fill a digest and writes `sha256:PENDING`. `10-sequencer-and-contracts.md` section 3.4 makes that `unresolvable-source`, `--lenient` is refused for any story under `docs/plan/`, and `devforgeai phase start dev` therefore refuses every story `plan` wrote | `clarify` is unaffected at its own gate, which checks the fence only, so `/clarify` still opens on such a story. The defect lands on `dev`, and the fix belongs at `devforgeai ingest-result`: after the change set is validated and before the checkpoint is taken, resolve every `sha256:PENDING` in a written artifact's frontmatter with the section 3.4 rule, using the same section-resolution library the gate uses, and refuse the receipt when a source or anchor does not resolve. This spec does not gate on that fix and does not describe it as running; it is recorded here so the `clarify` handoff's `/dev {story}` next step is understood to depend on it. |
| OI-12: a `needs_user` result never promotes, so where does the user answer? | Under the earlier reading, `needs_user` closed the run and nothing was promoted, so the `CLR-NNN` block existed only in a candidate root that a fresh `--continue` run would not have — the answer round-trip had no home | Settled in `10-sequencer-and-contracts.md` (section 2's `phase start` row, section 3.1, section 5.4's `needs_user` row, section 6's `REQUIRE_HUMAN`, blocked-run row): a `REQUIRE_HUMAN` block from `needs_user` or an exhausted attempt budget leaves the run `active` with its lease released, its candidate root and checkpoints kept, and `run.yaml#blocked_at` naming the phase. `devforgeai phase start clarify <story>` — the same skill and argument — resumes that run at `blocked_at` with `attempts` reset, which is exactly what `/clarify {story} --continue` is. The user answers in the candidate root's copy of the story, the path the handoff names, and the block reaches the canonical story when the resumed run finishes and the user runs `devforgeai promote <run>`. Abandoning instead is `devforgeai phase fail --reason <text>`, then `/status`. Section 6 UC-1, section 7a's `--continue` paragraph, the section 7e `needs_user` and `fail at max_attempts` rows, OI-5 and the "phase that writes the question is not the phase that asks" row all state this. |
| Promotion described as part of the Handoff sub-phase | A reader takes `devforgeai phase next` to promote the candidate root by itself, and a generated `SKILL.md` never asks the user before canonical bytes move | Section 7b row 6 and section 7c now carry the two-block model of `WRITE-MODEL-REVISION.md` D7 and `10-sequencer-and-contracts.md` sections 5.4, 6 and 12.4: `phase next` marks the run `ready_to_promote` and writes a `REQUIRE_HUMAN` block whose only forward step is `devforgeai promote <run>`; `SKILL.md` runs that command only after the user confirms; the promotion writes the second block. |
| `STALE_BASE`, `DIRTY_TARGET` and `MERGE_CONFLICT` attributed to the transition | The three rows read as ways `devforgeai phase next` can fail, so a spec reader looks for them in the oracle table | All three are refusals of `devforgeai promote <run>` (`10-sequencer-and-contracts.md` section 2's refusal table and section 12.4's ordered steps). Section 7c and the three section 7e rows now name the command that raises them. |
| A promotion refusal row with no forward command, and one that claimed the root was abandoned | Handoff rendering rule 1 forbids an empty `next`, and section 12.4 keeps the root on every refusal — only `devforgeai phase fail --reason` abandons one | The worktree `STALE_BASE` row now names `devforgeai promote {run}` after the sequencer's one internal rebase-and-retry has already failed (section 2, exit 1 on "`STALE_BASE` after a failed rebase"), and the copy-mode/`MERGE_CONFLICT` row now says no canonical byte moved and the root and its checkpoints survive. |
| The section 7e outcome table had no `ready_to_promote` row | Every run ends in two handoff blocks and the table listed only the second, so the promote step was invisible to a generator reading the table alone | A "pass, last phase, run `ready_to_promote` and not yet promoted" row now heads the table with `devforgeai promote {run}` as its one forward step, and the two `pass` rows that name `/dev {story}` are labelled `promoted` so it is clear they render the second block. |
| Section 10's transcript criterion listed only four operations | The criterion "no Bash call outside `devforgeai status \| phase start \| phase fail --reason \| validate`" would fail a compiled skill that ran the promote step section 7a step 8 requires | `WRITE-MODEL-REVISION.md` D7 propagates the fifth model-callable form everywhere the four are enumerated. The criterion now reads `... \| validate \| promote <run>` and adds that the last form appears only after the user asked for the promotion; section 7b's grammar sentence and the section 12 `allowed-tools` line already carried it. |
| The `document` oracle fails a `writes: docs` phase that changed no file | A story with nothing to clarify would block at `questions` after two attempts | `question_writer` always edits the story: with one block per ambiguity, or with a single block whose `#### Answer` is `None required.` when `ambiguity_finder` returned zero rows. UC-3 is that path, and it leaves an auditable record that `/clarify` ran. The `skill_specs` conditional exception in `plan` does not apply here: `clarify`'s phases are not marked conditional. |
| The first append has to remove the template's `None.` line | A naive append leaves `None.` above a block that contradicts it, and a diff checker that only allows appends rejects the removal | Replacing the `None.` line is the first of the three sanctioned edit kinds `check_clarify_edit.py` accepts. `references/questions.md` states it, and `assets/clarification.md` starts at the third-level heading so the skeleton cannot reintroduce the line. |
| `--continue` runs `question_writer` when nothing is left to ask | The phase writes a spurious `None required.` block on every continuation | On `--continue`, `question_writer` normalises the hand-written answers already in the story into the block shape — date, `#### Authority` placeholder, `status: answered` — which is a real edit and satisfies the `document` oracle. It writes a `None required.` block only when `ambiguity_finder` returned zero rows and the story carries no `open` block. |
| The phase that writes the question is not the phase that asks | The receipt makes `claimed_paths` empty on any status other than `pass`, and a change the receipt did not claim refuses it as `UNCLAIMED_CHANGE`. A `question_writer` that returned `needs_user` after editing the story would have its receipt refused as a protocol error, so the block would never reach a checkpoint, the human would have nothing to answer, and `--continue` would find no block to normalise | `question_writer` always returns `pass` with the blocks written, which is also what its `document` oracle requires. `answer_recorder` is the phase that returns `needs_user`, claiming nothing, when a block is still `open` with an empty `#### Answer`. The run is then blocked at `record_answers`, not closed: the `REQUIRE_HUMAN` handoff points at a question in the candidate root the run keeps, and `/clarify {story} --continue` resumes that same run once the user has answered there (OI-12). |
| The story's immutability comment and its Acceptance Criteria paragraph disagree | `templates/story.md:11-13` says only `status` and `## Clarifications` may change; `templates/story.md#acceptance-criteria` requires `/clarify` to remove the tag from the body | The Acceptance Criteria paragraph governs, because the dev gate's `unresolved_assumption` class is defined by the tag's presence in the body. `answer_recorder` makes exactly two body-affecting changes — the block append and the span replacement — and `check_clarify_edit.py` is what makes that checkable rather than promised. |
| Two stories in different plan slugs share a story id | The fence stays a pattern rather than a resolved path: `matches()` in `examples/hooks/policy.py` is an `fnmatch` over `docs/plan/*/stories/STORY-NNN.md`, so both files are inside the fence, both live in the candidate root, and an edit to the wrong slug is checkpointed and promoted without complaint | Each worker edits the path it actually read and claims that exact path, so the checkpoint diff and the phase report both name it. Nothing in the current gate rejects a duplicate id across slugs, so a project that reuses story ids must renumber before running `/clarify`. Recorded rather than papered over: this is a real gap, not a checked constraint. |
| The candidate root and the primary window | A worker cannot resolve `candidate.root` from the canonical tree, and pasting a criterion into a dispatch is the restatement the anti-ceremony rules forbid | Every anatomy run gets one candidate root, opened by `phase start` and owned by the sequencer until promotion or abandonment; the primary window stays in the canonical checkout. The one thing a dispatch carries beyond the story path, the run id and the `--continue` token is the `devforgeai status` block, which names `run`, `candidate.root`, `phase`, `fence` and `granted_keys`. It is generated, not composed, and it is the only sanctioned paste. Claude's own worktree isolation setting and `EnterWorktree` are not used: they fork from HEAD and would split the run's linear history |
| The receipt no longer carries an `evidence` object | Earlier drafts gave the phases `evidence.ambiguities`, `evidence.existing_clarifications`, `evidence.blocks` and `evidence.resolved`. The receipt schema in the write-model revision removes `evidence` and adds `claimed_paths` and `evidence_refs`, which are paths, not rows | The two writing phases' rows have a home in the story itself: each `CLR-NNN` block carries its id, criterion and status, and a settled span is visibly gone from the body. `ambiguity_finder` is a judge and writes its findings file into `.devforgeai/work/<run>/evidence/ambiguity_finder/`, which `evidence_refs` names and `question_writer` reads by path. `issues[]` stays the bounded summary, at ten rows |
| Section 9, row 5 (scripts have no implemented runner) | Both scripts are honest deterministic checks with no sequencer that imports them yet, so an author could describe them as enforced | `10-sequencer-and-contracts.md` section 3.3 shows the implemented document gate checking fence entries only, and section 5.2 shows result validation stopping at path, hash and package policy. Both scripts run today only when a human runs them. The evidence table names them as designed sequencer-side checks and section 7c says they are unimplemented; no criterion in section 10 gates on them. |

## 10. Success criteria and test cases

### Success criteria

- Triggers on the section 4 positives and on none of the near-misses.
- Every `ASSUMPTION:` span in the fixture story that a `CLR-NNN` block answers is absent from the story body afterwards, and every span with no answered block is still present.
- Every `CLR-NNN` block the run writes carries all six template keys, all three fourth-level headings, and an id matching `^CLR-[0-9]{3}$`.
- `python3 scripts/check_clarify_edit.py --before <original> --after <result>` exits 0 for every run the skill completes.
- Outside `## Clarifications` and the replaced spans, the story is byte-identical before and after.
- The primary window's transcript shows no read of the story, and no Bash call outside `devforgeai status | phase start | phase fail --reason | validate | promote <run>`, the last of which appears only after the user asked for the promotion.

### Fixture

`docs/design/examples/fixtures/clarify/` is the base fixture. Its exact tree:

| Path | Contents |
|---|---|
| `.devforgeai/state.yaml` | canonical state: `version: 1`, `target: [claude]`, `mode: greenfield`, `slug: tinyapp`, `phase: plan`, `phases.plan.status: done`, `stories.STORY-001.status: ready`, `stories.STORY-001.sprint: sprint-001`, `next: "/clarify STORY-001"`, and a `runs` mapping with one key `clarify-STORY-001` whose value carries `story: STORY-001`, `skill: clarify`, `mode: copy`, `root: .`, `base_ref: fixture`, `checkpoint: base` and `status: active` |
| `.devforgeai/work/clarify-STORY-001/run.yaml` | the per-run enforcement file, standing in for what `devforgeai phase start` writes: `canonical: .`, `phase: find_ambiguity`, `fence: [docs/plan/*/stories/STORY-001.md]`, `granted_keys: []`, `attempts` and `max_attempts` at 2 for the three phases, `gate_policy: {unresolvable_source: BLOCK}`, and a `lease` naming the eval session. The fixture copy is the candidate root, so `candidate.mode` is `copy` and `candidate.root` is the copy itself |
| `.devforgeai/stack.yaml` | one anchor, `python`, copied verbatim from `docs/design/examples/hooks/fixtures/.devforgeai/stack.yaml` |
| `docs/plan/tinyapp/epics/EPIC-001.md` | an `epic` instance, `id: EPIC-001`, `slug: tinyapp`, `status: ready`, `risk_tier: LOW`, `provenance: []`, `depends_on: []`, with the four required sections filled in one line each |
| `docs/plan/tinyapp/stories/STORY-001.md` | a version 3 `story` instance for a `slugify` helper: three numbered acceptance criteria, three `test_plan` rows, `write_fence` of `tinyapp/text.py` and `tests/test_text.py`, `commands.source` of the `python` anchor, and `## Clarifications` holding exactly the template's `None.` line. Criterion 3 reads `WHEN the input is an empty string THE SYSTEM SHALL return ASSUMPTION: empty input behaviour is undecided`. Every `provenance[]`, `context[]` and `commands.hash` digest is a real digest of the fixture's own bytes, so the gate opens the run |
| `tinyapp/text.py` | an empty module with a docstring |
| `tests/test_text.py` | one collected test asserting the module imports |

Overlays, copied over the base fixture after it is copied and before the prompt runs:

| Overlay | Change |
|---|---|
| `overlays/eval-2/docs/plan/tinyapp/stories/STORY-001.md` | the same story with criterion 3 rewritten to a decided value, no `ASSUMPTION:` span anywhere, and `## Clarifications` still holding the template's `None.` line |
| `overlays/eval-3/docs/plan/tinyapp/stories/STORY-001.md` | the same story as the base fixture, plus a `### CLR-001` block under `## Clarifications` with `status: open`, an empty `#### Answer`, and the hand-written line `An empty input returns an empty string.` typed under `#### Answer` by the user |

Eval 1 has no overlay. Per-eval changes ship only as these overlay directories; no eval describes a fixture edit in prose.

### evals/evals.json (used verbatim)

```json
{
  "skill_name": "clarify",
  "evals": [
    {
      "id": 1,
      "prompt": "Run clarify on STORY-001 in this repository. Criterion 3 has an open assumption about empty input. Our decision is that an empty input returns an empty string and raises no error; I am bryan and I am deciding it now.",
      "expected_output": "STORY-001.md gains a CLR-001 block under ## Clarifications with status answered, the ASSUMPTION span is gone from criterion 3 and replaced by the decided value, and the handoff's first next step is /dev STORY-001.",
      "expectations": [
        "docs/plan/tinyapp/stories/STORY-001.md contains a heading CLR-001 under the Clarifications section with the keys id, story, template, template_version, date and status",
        "That block's status is answered and its Answer body names an empty string as the return value",
        "The text ASSUMPTION: does not appear anywhere in docs/plan/tinyapp/stories/STORY-001.md outside the Clarifications section",
        "Criterion 3 of the story states the empty-input behaviour as a value rather than as an open question",
        "Outside the Clarifications section and criterion 3, every line of the story is identical to the fixture copy",
        "The final message contains a handoff block whose next step 1 is /dev STORY-001"
      ]
    },
    {
      "id": 2,
      "prompt": "Run clarify on STORY-001 in this repository.",
      "expected_output": "The story has no open assumption, so one CLR block recording that nothing needed clarifying is appended, the rest of the story is untouched, and the handoff's first next step is /dev STORY-001.",
      "expectations": [
        "docs/plan/tinyapp/stories/STORY-001.md contains exactly one CLR block under the Clarifications section",
        "That block's Answer body is the text None required.",
        "No acceptance criterion in the story differs from the fixture copy",
        "The final message contains a handoff block whose next step 1 is /dev STORY-001"
      ]
    },
    {
      "id": 3,
      "prompt": "I already typed my answer under the open question at the bottom of STORY-001. Pick it up from there.",
      "expected_output": "The existing CLR-001 block becomes status answered with an Authority body, the ASSUMPTION span disappears from criterion 3, and no second CLR block is created.",
      "expectations": [
        "docs/plan/tinyapp/stories/STORY-001.md contains exactly one CLR block, still numbered CLR-001",
        "That block's status is answered and its Authority body is non-empty",
        "The text ASSUMPTION: does not appear anywhere in the story outside the Clarifications section",
        "The final message contains a handoff block whose next step 1 is /dev STORY-001"
      ]
    }
  ]
}
```

Quick-mode results are generation feedback only: one enabled run per eval and no baseline. They are not runtime conformance evidence, and no section of this spec gates on such evidence; the deferred contract is `12-post-mvp.md#pm-02`.

## 11. Dependencies and compatibility

| Kind | Value |
|------|-------|
| Tools | SKILL.md: `Read`, `Agent`, and a Bash grammar no wider than the five model-callable operations `devforgeai status \| phase start <skill> <arg> \| phase fail --reason \| validate \| promote <run>`. Document writers (`question_writer`, `answer_recorder`): `Read`, `Grep`, `Glob`, `Bash(devforgeai status)` plus `Edit` and `Write`, which Codex serves as `apply_patch`, denied outside `candidate.root` and outside the run's fence. Judge (`ambiguity_finder`): the same read set plus `Write` confined to `.devforgeai/work/<run>/evidence/<agent>/`. No `clarify` phase grants a stack command key, so no worker carries `Bash(devforgeai run *)`. |
| MCP servers | none |
| Runtime | Python 3.11+ for both bundled scripts; PyYAML 6+, which `find_assumptions.py` and `check_clarify_edit.py` import to parse story frontmatter and the fenced block inside each `CLR-NNN` entry. Worktree mode additionally requires `git` with at least one commit on the project; without it the run falls back to copy mode |
| Project commands | none. `clarify` declares no `run_keys` in any phase, so the run brokers no `stack.yaml` command and the run file carries `granted_keys: []` for this document run. The story's own `commands.source` anchor is re-resolved by the gate and is not otherwise used. |
| DevForgeAI/Core compatibility | `NOT_APPLICABLE`. `clarify` is an anatomy-governed skill, not a Research Core adapter, and names no Research Core version. |
| Other skills | Consumes `story`, owned by `plan`. Produces `clarification`, consumed by `dev`. Calls none: the `/dev` and `/analyze` edges are handoff rows (open item OI-7). Must not overlap with `plan` (which owns story wording), `amend` (which owns constitution changes) or `analyze` (which owns cross-artifact traceability). |

Deferred dependencies, each naming its `12-post-mvp.md` entry and what the skill does today without it:

| Deferred item | What `clarify` does today |
|---|---|
| `12-post-mvp.md#pm-01` | `isolation: required` on `question_writer` and `answer_recorder` is the DevForgeAI contract value compiled into the target profile, not Claude's `isolation` frontmatter field. Nothing verifies at runtime that a worker ran in its own window, and the generated adapter is an uninstalled candidate a human accepts. |
| `12-post-mvp.md#pm-04` | A worker's write boundary is the dispatcher's `PreToolUse` deny plus the candidate root, not an operating-system boundary. |
| `12-post-mvp.md#pm-02` | Quick-mode eval results are generation feedback. No success criterion in section 10 is presented as conformance evidence. |
| `12-post-mvp.md#pm-06` | Only `skip` and `quick` eval modes exist. Section 0 rule 5 rejects any third mode name as a spec defect. |
| `12-post-mvp.md#pm-10` | Nothing re-runs `clarify`'s checks from a clean checkout, so a story edited outside a run is caught only the next time a gate re-resolves it. |

Frontmatter values derived from this table:

```yaml
compatibility: "Requires Python 3.11+ and PyYAML for the two bundled scripts. Runs inside a repository that already has a .devforgeai/ directory and a version 3 story; outside one, devforgeai phase start refuses and the skill does nothing."
allowed-tools: "Read Agent Bash(devforgeai status) Bash(devforgeai phase start *) Bash(devforgeai phase fail *) Bash(devforgeai validate) Bash(devforgeai promote *)"
```

## 12. Targets

The generator produces one provider-neutral semantic package and a separate adapter for each selected target when frontmatter, invocation policy, or agent configuration differs. Provider-neutral resources may be shared. Adapter directories are not required to be byte-identical or symlinked.

| Target | Install path | Invocation | Subagents | Notes |
|--------|--------------|------------|-----------|-------|
| claude | `.claude/skills/clarify/` | `/clarify` with a story id, and `--continue` on the answer round-trip | `.claude/agents/clarify-<role>.md`: two document writers with `Edit` and `Write` confined to the candidate root, one judge whose `Write` reaches only its run-scoped evidence directory | Provider-specific frontmatter keys (`argument-hint`, `disable-model-invocation`) are compiled into this target's SKILL.md only. `hooks`, `memory`, `background`, `permissionMode` and Claude's own `isolation` are omitted from every profile. |
| codex | `.agents/skills/clarify/` plus `.codex/agents/` profiles | `$clarify` with a story id, and `--continue` on the answer round-trip | `.codex/agents/clarify-<role>.toml`: the same three names, with `apply_patch` in place of `Edit` and `Write` | Portable six-field frontmatter only; policy goes in target-side configuration. |
| both | separate `.claude/skills/clarify/` and `.agents/skills/clarify/` adapters | as above | as above | Share only provider-neutral resources; validate each adapter independently. |

```yaml
metadata:
  version: "1.0.0"
  devforgeai-spec: "SKILL-SPEC-010"
  devforgeai-target: "both"
  devforgeai-anatomy: "true"
```

Not produced by skill-creator (deferred to DevForgeAI's skill-generator): provider-native `.claude/agents/*.md` and `.codex/agents/*.toml` worker profiles, provider-specific frontmatter keys for the Claude target, and concise `AGENTS.md` sections. Hook definitions are not per-skill: `init` installs the one dispatcher and its provider fragments from `09-hook-dispatcher.md`, and this spec ships none.

A generated package is an uninstalled candidate until those provider-native controls are present and independently validated. Generation or quick-mode success is not installation authority.

## 13. Constraints

- `SKILL.md` under 500 lines and roughly 5,000 tokens, holding only identity, the ordered phase list, the dispatch loop, and the handoff table. Every other instruction lives in `references/<phase>.md`, `agents/<role>.md`, `scripts/` or `assets/`.
- References one level deep from whichever file is loaded: `SKILL.md` links to `references/`, `agents/`, `scripts/`, `assets/`; an `agents/*.md` may link to `references/*.md`. Nothing links further.
- Hooks, state writes and phase advancement are not in the skill. `SKILL.md` contains no instruction the gate, the fence or a transition oracle already carries.
- No `README.md` inside the skill directory.
- No XML angle brackets in frontmatter. Description 886 characters; name 7 characters.
- Imperative voice; each step states why it matters. No capitalised absolutes: where a rule is real it is a gate defect class, the fence, a `must_not` line, or an oracle condition, and the text names that mechanism.
- Provide defaults, not menus. `question_writer` writes the `None required.` block by default rather than offering the choice to skip.
- Scripts take arguments, never prompt, and exit `0`, `1` or `2`.
- Skill-specific: the story is the only file this skill changes, it is edited inside the run's candidate root, and it reaches the canonical checkout only at promotion. Each phase edits over the bytes the previous checkpoint left, and the checkpoint diff is what the sequencer compares to `claimed_paths`.

## 14. Acceptance checks

Run these before reporting done and paste their output:

```bash
# frontmatter and naming (skill-creator's own validator)
python -m scripts.quick_validate ./out/clarify      # run from the skill-creator directory
# open-standard validator, if installed
skills-ref validate ./out/clarify
# size budget
wc -l ./out/clarify/SKILL.md                        # must be < 500
# every worker in section 7d has a prompt file, and no extra
ls ./out/clarify/agents/                            # ambiguity_finder.md question_writer.md answer_recorder.md
# one reference file per phase, plus envelope.md
ls ./out/clarify/references/                        # find_ambiguity.md questions.md record_answers.md envelope.md
# scripts answer --help and reject bad usage with exit 2
python3 ./out/clarify/scripts/find_assumptions.py --help
python3 ./out/clarify/scripts/check_clarify_edit.py --help
# no leftover placeholders
grep -rnE 'T[O]DO|T[B]D|\{\{' ./out/clarify || echo clean
```

Then the wave-4 battery over this specification:

```bash
python3 docs/design/specs/verify.py --only v1,v2,v4
```

For non-Research anatomy skills, DevForgeAI skill-validator additionally checks: all sub-phase kinds present with Gate, Record and Handoff bound to sequencer operations; `must_not` present in every agent file; every agent declaring `writes: candidate` or `writes: evidence`, with a `writes: evidence` agent carrying no `Edit` and a `Write` fenced to its run-scoped evidence directory; the SKILL.md Bash grammar is no wider than the five model-callable operations; handoff outcomes cover every status the skill can return, including `could_not_run`. `clarify` has no critic phase, so skill-validator's persona-versus-critic check does not apply to it; section 7b names `check_clarify_edit.py` as the independent check in its place.

## 15. Provenance

| Source | Hash | Used for |
|--------|------|----------|
| docs/design/01-skill-anatomy.md#primary-window-contract | see frontmatter | sections 2, 7a, 7b |
| docs/design/01-skill-anatomy.md#gate-validating-the-incoming-artifact | see frontmatter | sections 7b, 7c |
| docs/design/01-skill-anatomy.md#context-bundle-format | see frontmatter | section 9, OI-11 |
| docs/design/10-sequencer-and-contracts.md#4-per-skill-phase-registry | see frontmatter | sections 7b, 7c, 7d |
| docs/design/10-sequencer-and-contracts.md#3-2-defect-to-action-map-as-implemented | see frontmatter | sections 7c, 7e |
| docs/design/10-sequencer-and-contracts.md#5-2-validation-order | see frontmatter | sections 7c, 13 |
| docs/design/10-sequencer-and-contracts.md#5-4-transition-oracles | see frontmatter | sections 7c, 9 |
| docs/design/10-sequencer-and-contracts.md#6-handoff-envelope | see frontmatter | sections 7a, 7e |
| docs/design/11-artifact-registry.md#1-template-registry | see frontmatter | sections 6, 8 |
| docs/design/11-artifact-registry.md#2-artifact-path-patterns | see frontmatter | section 6 |
| docs/design/11-artifact-registry.md#6-known-divergences | see frontmatter | sections 2 (R8), 6 |
| docs/design/02-skill-roster.md#clarify | see frontmatter | sections 1, 2, 5 |
| docs/design/02-skill-roster.md#handoff-decision-tables | see frontmatter | section 7e |
| docs/design/05-subagent-sets.md#sets-per-skill | see frontmatter | sections 7b, 7d |
| docs/design/05-subagent-sets.md#contract-format | see frontmatter | section 7d |
| docs/design/templates/story.md#acceptance-criteria | see frontmatter | sections 2 (R1, R3), 9 |
| docs/design/templates/story.md#clarifications | see frontmatter | sections 6, 9 |
| docs/design/12-post-mvp.md#pm-01 | see frontmatter | section 11 |
