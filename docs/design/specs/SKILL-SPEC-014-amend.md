---
template: skill-spec
template_version: 1
id: SKILL-SPEC-014
skill_name: amend
target: both
status: approved
author: "DevForgeAI plan skill (wave 2 spec authoring)"
date: 2026-09-02
depends_on:
  - source: docs/design/01-skill-anatomy.md#primary-window-contract
    hash: sha256:6556607035516c49ee43fe2bbeffe1a74e898889d84be00c9a05fdf751d209b6
    excerpt: "**The model dispatches, the sequencer decides.** For an anatomy-governed skill, the primary window (provider entry adapter + skill orchestration) does light, trivial work only."
  - source: docs/design/01-skill-anatomy.md#context-bundle-format
    hash: sha256:7b068feb30e7cc2f66292b512ac179cd217df225fb58517d2aaadd30b25236dc
    excerpt: "3. Split the file on LF (a file that ends with LF therefore yields a final empty line, which belongs to the last section); join the section lines with LF and append one LF."
  - source: docs/design/10-sequencer-and-contracts.md#4-per-skill-phase-registry
    hash: sha256:7c1d67f1154e49247e5dc178fcc1512bdbd53af378c360aeafe69bffed1136ab
    excerpt: "| amend | document | `docs/architecture/**`, `docs/reports/impact-<arg>.md`, `.devforgeai/provenance/adr/**` | 4 |"
  - source: docs/design/10-sequencer-and-contracts.md#5-worker-result
    hash: sha256:cd95bd6c0db2bda7a573665b73582c813c0c6cb01b7f3e9f7ed52a9d1afafe0c
    excerpt: "One schema, both providers, every skill. The worker's final message is exactly this object, with no Markdown fence and no surrounding prose."
  - source: docs/design/10-sequencer-and-contracts.md#3-status-vocabulary-and-gate-policy
    hash: sha256:1706823f7848f5cb6b23e68dfd783885fad3fdfa5d98fb6df0b90270a818fc20
    excerpt: "A document run carries the fixed map `{unresolvable_source: BLOCK}`, because it has no story to declare a wider one."
  - source: docs/design/10-sequencer-and-contracts.md#6-handoff-envelope
    hash: sha256:52cf474c332c7d8a02ad1b1abac51d852d5f54c30bf5126deb8a5b18cde77206
    excerpt: "| document run, promoted, no verdict or `verdict: pass` | `/status` |"
  - source: docs/design/11-artifact-registry.md#1-template-registry
    hash: sha256:fabb8d2f142dcde1a31bc53768f8a46d01cac3ea4a7f6b73db22479cc89b5553
    excerpt: "| `impact-report` | `.devforgeai/skills/amend/templates/impact-report.md` | 1 | `^IMP-[0-9]{3}$` | doc, template, template_version, status, depends_on | Change, Affected Stories, Re-slice Actions |"
  - source: docs/design/11-artifact-registry.md#2-artifact-path-patterns
    hash: sha256:858455b885ac6c1ddbe427a433ba715f7266d08b90e105135172877e29ea0ecc
    excerpt: "| `.devforgeai/provenance/adr/NNNN-<slug>.md` | `adr` | architect (`adr`), amend (`adr`) | sequencer |"
  - source: docs/design/02-skill-roster.md#amend
    hash: sha256:7d3fb6fd5626ff057c8ecc768d30ab052bdb90a9521ffab125245d279812caff
    excerpt: "- Impact-analyzer finds every story whose context bundle hashes the changed section."
  - source: docs/design/05-subagent-sets.md#sets-per-skill
    hash: sha256:f2957217c9af147e4a7ea03749cbe6efda266bd56d403f39aa25c9a655872609
    excerpt: "| amend | change-applier, adr-writer, impact-analyzer, resync-slicer |"
---

# Skill Specification: amend

A stranger with no conversation history must be able to build this skill from this document alone. Every question the generator would otherwise ask is answered below. The `depends_on` digests are computed under the hash rule in `01-skill-anatomy.md#context-bundle-format` and verified by `docs/design/specs/verify.py --only v3`; a source edit after this date makes V3 fail until the digest is recomputed.

## 0. Generator instructions

These instructions are addressed to the skill-generating agent (Anthropic's `skill-creator` skill, or DevForgeAI's `skill-generator`). They replace its interview.

### Cold-session prompt

Paste this into a fresh session from the repository root:

```
Use the skill-creator skill to build the skill specified in docs/design/specs/SKILL-SPEC-014-amend.md.
Follow its section 0 exactly. Output directory: ./out. Eval mode: quick.
```

### Rules for the generator

1. **Do not interview.** Sections 1-13 pre-answer every Capture Intent and Interview question (what it enables, when it triggers, output format, test cases, edge cases, input/output formats, example files, success criteria, dependencies). Treat this document as the conversation history you are told to harvest from.
2. **Test prompts are pre-approved.** Use section 10 verbatim as `evals/evals.json`. Do not ask whether they look right.
3. **Trigger queries are pre-approved.** Use section 4 verbatim as the trigger eval set. Do not ask for sign-off.
4. **No human review loop.** Do not wait for the user to review results. Proceed to the next stage on your own.
5. **Eval mode** is given in the prompt and is one of two values:
   - `skip`: write the skill only. Do not create `evals/`, do not run test prompts, do not optimize the description.
   - `quick`: write the skill and `evals/evals.json`. Build each eval's workspace from `fixtures/amend/` as section 10 describes, run each test prompt once with the skill (no baseline run), grade with the grader agent, write `grading.json`, and report pass/fail per expectation in your final message. Do not run the description-optimization loop. Run the eval executions and the grader as foreground Agent-tool subagents, never as background shell processes, and do not end your turn until every `grading.json` exists: a headless session terminates when the top-level turn ends and orphans anything still running.
   - Any other mode name is a spec defect. The deferred interactive mode is `12-post-mvp.md#pm-06`.
6. **Output location** is given in the prompt. Create `./out/amend/`. Do not write anywhere else except the `amend-workspace/` sibling that eval runs require.
7. **On ambiguity, stop before output.** If the spec is still `draft`, contains an unresolved authoring assumption, omits a section, contradicts itself, or leaves a decision this document does not make, do not guess and do not write candidate skill files. End with a list titled `SPEC GAPS` naming each section and question. The spec author fixes and approves the spec before re-running.
8. **Fidelity over creativity.** Use the description in section 3 verbatim. Use the worker contracts in section 7d verbatim as `agents/<role>.md` bodies, adding only the four-section framing `templates/agent-md.md` fixes (Job, Inputs, Rules, Receipt). Do not add steps, tools, or behaviours the spec does not mention.
9. **Finish with the acceptance checks** in section 14 and include their output in your final message.

## 1. Identity

| Field | Value |
|-------|-------|
| name | `amend` (kebab-case, 5 chars, equals the directory name, no `claude`/`anthropic` prefix) |
| title | Constitution-Set Amendment and Impact Analysis |
| purpose | Change one document in the architecture set, record the decision as an ADR, and name every story the change invalidates, so a stale context bundle is discovered before a story gate refuses it. |
| category | devforgeai-phase |
| version | 1.0.0 (skill-package version written to `metadata.version`; not the DevForgeAI or Research Core version) |
| license | MIT (frontmatter `license: MIT`) |

## 2. Problem and requirements

**Without this skill:** an architecture document is edited by hand. Three things follow, and all three are in the failure list in `07-purpose-and-enforcement.md` section 2. First, no decision record exists, so six weeks later nobody can say why the mandate changed or which ADR it supersedes. Second, every story whose `context[]` sliced the edited section still carries the old digest; the story gate re-resolves those entries (`10-sequencer-and-contracts.md` section 3.4) and refuses the run with `stale-hash`, one story at a time, at `/dev` time, with no list of what else is broken. Third, the edit is invisible to `/analyze`: no run opened, so `provenance/log.jsonl` has no line for it.

| ID | Kind | Requirement |
|----|------|-------------|
| R1 | explicit | Take a document name and a one-line change request, and apply the change to `docs/architecture/<doc>.md` without disturbing the rest of the file. |
| R2 | explicit | Record the change as an ADR against the `adr` template, numbered above every existing ADR, with `supersedes` filled when it replaces a live decision. |
| R3 | explicit | List every story whose `provenance[]` or `context[]` covers a section this run changed, with the verdict that story's next gate will reach. |
| R4 | explicit | Write `docs/reports/impact-<doc>.md` naming the re-slice command for each affected story, and hand off so `plan` re-slices them. |
| R5 | implicit | The amended document keeps the template `architect` owns: same frontmatter keys, same required sections, same `template_version`, so its consumers still validate it. |
| R6 | implicit | The primary window opens the run, dispatches, and prints the rendered handoff. It reads no architecture document and no story, and it writes nothing (`01-skill-anatomy.md#primary-window-contract`). |
| R7 | implicit | Every worker returns exactly one `devforgeai.worker-result/v1` receipt. A producer writes its files inside the candidate root and names them in `claimed_paths`; the sequencer derives what actually changed from the checkpoint diff and refuses anything unclaimed (`10-sequencer-and-contracts.md` section 5). |
| R8 | discovered | The impact chain is deterministic: `change_applier` records the changed `path#anchor` and the section digest before and after, and `impact_analyzer` compares recorded story digests against current bytes under the same hash rule. No model judgement decides whether a story is affected. |
| R9 | discovered | `amend` cannot write a story. `docs/plan/**` is outside its fence and `plan` owns the story template, so the re-slice is a handoff row, never an edit (`10-sequencer-and-contracts.md` section 4). |
| R10 | discovered | `amend`'s `adr` phase writes `.devforgeai/provenance/adr/NNNN-<slug>.md` directly. The prefix is sequencer-owned, so it reaches the fence through the producer exception in `10-sequencer-and-contracts.md` section 5.2; the sequencer checks the proposal against the `adr` template header before applying it. |

## 3. Description

```yaml
description: >
  Amend one document in a DevForgeAI architecture set (constitution, sourcetree, techstack,
  architecture, or a design doc), record the decision, and report what it breaks. Use this
  skill whenever a rule, mandate, constraint, component, or convention already written into
  docs/architecture has to change: the user says update the constitution, we switched
  libraries so fix the docs, record an ADR for this, supersede that decision, or asks which
  stories a documentation change invalidates. It applies the change, writes an architecture
  decision record, finds every story whose context bundle slices the changed section, and
  writes an impact report naming the re-slice command per story. Do NOT use it to author a
  new architecture set (use /architect), to rewrite or re-slice stories (use /plan), to
  compare documents against code (use /drift), or to gather sprint lessons (use /retro).
```

Character count: 882 / 1024. No `<` or `>` appears in the description, so the command forms are written without angle brackets.

## 4. Trigger set

```json
[
  {"query": "/amend constitution \"tests are no longer optional, mandate tdd for every story\"", "should_trigger": true},
  {"query": "we dropped sqlalchemy for raw sqlite3 last sprint, update techstack.md properly and tell me what it breaks", "should_trigger": true},
  {"query": "record an ADR for removing the redis cache and patch docs/architecture/architecture.md to match", "should_trigger": true},
  {"query": "handlers moved from src/api to src/http. sourcetree.md still says the old layout, fix it", "should_trigger": true},
  {"query": "which stories still slice constitution.md#mandates? i want to change that section", "should_trigger": true},
  {"query": "ADR-0003 said we'd use JWTs, we're going with sessions now. supersede it", "should_trigger": true},
  {"query": "retro-sprint-002 says we should add a rate limit constraint to the architecture doc, please apply that", "should_trigger": true},
  {"query": "the drift report says techstack.md#data-access is wrong. do the change properly with a decision record", "should_trigger": true},
  {"query": "change the style section of the constitution to say ruff format instead of 4 space indent, and log why", "should_trigger": true},
  {"query": "write the constitution for this project from the prd", "should_trigger": false},
  {"query": "STORY-004 is refused with a stale hash, re-slice it", "should_trigger": false},
  {"query": "does the code still match architecture.md? i suspect it doesn't", "should_trigger": false},
  {"query": "sprint-002 is done, pull the lessons out of the qa reports", "should_trigger": false},
  {"query": "STORY-007 has an unresolved ASSUMPTION about the rate limit value", "should_trigger": false},
  {"query": "add an epic for the auth migration and split it into stories", "should_trigger": false},
  {"query": "review the diff on STORY-009 against the constitution before i merge", "should_trigger": false},
  {"query": "fix the typo in README.md, it says 'recieve'", "should_trigger": false},
  {"query": "generate the tdd skill the constitution mandate asks for", "should_trigger": false},
  {"query": "run the test suite and tell me if the techstack change broke anything", "should_trigger": false}
]
```

## 5. Use cases

### UC-1: Mandate change with impacted stories
- **User says:** "/amend constitution \"tests are no longer optional, mandate tdd for every story\""
- **Steps:** 1. The adapter parses `constitution` as the document and the quoted text as the change request, then calls `devforgeai phase start amend constitution`. 2. `change_applier` edits `docs/architecture/constitution.md` inside the candidate root, rewriting `## Mandates`, and records the changed anchor and its digest before and after. 3. `amend_adr_writer` writes `.devforgeai/provenance/adr/0002-mandate-tdd.md` inside the candidate root; the sequencer checks it against the `adr` template header at ingest; it reaches `.devforgeai/provenance/adr/` in the canonical checkout only when the user runs `devforgeai promote <run>` at the end. 4. `impact_analyzer` re-resolves every story's `context[]` and finds STORY-001 recorded the old `#mandates` digest. 5. `resync_slicer` writes `docs/reports/impact-constitution.md` with STORY-001 under Affected Stories and `/plan shop --reslice STORY-001` under Re-slice Actions.
- **Result:** the amended constitution, the ADR at its registry path, an impact report, four result files under `.devforgeai/work/amend-constitution/`, and a handoff whose next step is `/status` with `/plan shop --reslice STORY-001` printed as an open item.

### UC-2: Library swap in the techstack document
- **User says:** "we dropped sqlalchemy for raw sqlite3 last sprint, update techstack.md properly and tell me what it breaks"
- **Steps:** 1. The adapter resolves the document to `techstack` and calls `devforgeai phase start amend techstack`. 2. `change_applier` rewrites `## Data Access` and leaves the other required sections byte-identical. 3. `amend_adr_writer` fills `supersedes` with the ADR that chose the old library. 4. `impact_analyzer` lists the stories that sliced `techstack.md#data-access`. 5. `resync_slicer` writes `docs/reports/impact-techstack.md`, whose Re-slice Actions row for `.devforgeai/stack.yaml` names `/architect` because no amend worker may write that file.
- **Result:** `docs/architecture/techstack.md` matches the decision, and the report says in one row that the machine-readable stack section is still the old one and which command regenerates it.

### UC-3: The named document does not exist
- **User says:** "/amend design-auth \"record that we chose session cookies\""
- **Steps:** 1. `devforgeai phase start amend design-auth` opens the run: the document gate checks the fence, not the file. 2. `change_applier` finds no `docs/architecture/design-auth.md`, writes nothing, and returns `status: fail` with an empty `claimed_paths` and one issue row naming the missing path. 3. The transition oracle records `phase apply_change produced no document inside the fence`, the attempt counter reaches its limit of 2, and the run blocks.
- **Result:** no file changed anywhere, `REQUIRE_HUMAN` in `handoff.json`, and the run blocked at `apply_change` with its root kept. The next step is `devforgeai phase fail --reason <text>`, because the repair is another skill's run and the blocked run still holds the fence; the repair route then names `/architect` as the skill that creates a design document.

## 6. Inputs and outputs

### Inputs
| Input | Format | Example file | Required |
|-------|--------|--------------|----------|
| document name | first positional argument; the basename, without directory or extension, of a file under `docs/architecture/` (`constitution`, `sourcetree`, `techstack`, `architecture`, `design-auth`) | `docs/architecture/constitution.md` | yes |
| change request | second positional argument; one quoted line of user intent | | yes |
| target document | markdown under `architect`'s `constitution` / `sourcetree` / `techstack` / `architecture` / `design` template | `fixtures/amend/docs/architecture/constitution.md` | yes |
| stories | markdown, `plan`'s `story` template v3; read for frontmatter `provenance[]` and `context[]` only | `fixtures/amend/docs/plan/shop/stories/STORY-001.md` | no |
| existing ADRs | markdown, `architect`'s `adr` template | `fixtures/amend/.devforgeai/provenance/adr/0001-choose-sqlite.md` | no |
| `adr` template | markdown with the template header | `fixtures/amend/.devforgeai/skills/architect/templates/adr.md` | yes for the `adr` phase; the sequencer validates the proposal against it and refuses when it is absent |
| upstream report that motivated the change | markdown, `retro`'s `retro-report`, `drift`'s `drift-report` or `analyze`'s `analyze-report` | `docs/reports/drift-<slug>.md` | no; the change request is the argument, and the report is the citation behind it. Absent from the eval fixture in section 10, which exercises the change request alone |
| `.devforgeai/state.yaml` | yaml | `fixtures/amend/.devforgeai/state.yaml` | yes; `devforgeai phase start` refuses without it |

### Outputs
| Output | Format | Location | Template |
|--------|--------|----------|----------|
| amended document | markdown | `docs/architecture/<doc>.md` | `architect`'s `constitution`, `sourcetree`, `techstack`, `architecture` or `design`, unchanged |
| decision record | markdown | `.devforgeai/provenance/adr/NNNN-<slug>.md` | `adr`, read from `.devforgeai/skills/architect/templates/adr.md` |
| impact report | markdown | `docs/reports/impact-<doc>.md` | `impact-report` (`assets/impact-report.md`) |
| phase results | json | `.devforgeai/work/amend-<doc>/<phase>-result.json` | none; the sequencer writes it |
| phase reports | markdown | `.devforgeai/work/amend-<doc>/<phase>-report.md` | none; the sequencer renders it |
| rendered views | markdown | `docs/reports/amend-amend-<doc>-<phase>.md` | none; the sequencer writes it at each passing transition |
| handoff | json plus its printed block | `.devforgeai/work/amend-<doc>/handoff.json` | `handoff` |

`amend` consumes `constitution`, `sourcetree`, `techstack`, `architecture`, `design` and `adr` from `architect`, `story` from `plan`, and the three reports that route here — `retro-report` from `retro`, `drift-report` from `drift` and `analyze-report` from `analyze` — every one of which has a producer in `11-artifact-registry.md` section 5. A report is never the run argument: `retro`, `drift` and `analyze` each name `/amend {doc} "{change}"` in an Actions or open-items row, a human runs that command, and `change_applier` reads the named report as the citation for the change it applies. `amend` reads no report to decide what to change.

The amended document, the decision record and the impact report are the only three paths any amend worker writes, and all three are written inside the candidate root. Everything else in that table is written by the sequencer. The ADR path is sequencer-owned in the canonical checkout and reaches `amend`'s fence only through the producer exception for `.devforgeai/provenance/adr/**`, held by the `adr` phase alone (`10-sequencer-and-contracts.md` section 5.2): the worker writes it under the candidate root and it reaches canonical only at `devforgeai promote <run>`, never at Handoff and never by a worker write into `.devforgeai/`. `FENCE_OVERLAP` counts that exception path as a fence member, so two amend or architect runs cannot both be active.

### Output template

`docs/reports/impact-<doc>.md`, filled from `assets/impact-report.md`:

```
---
doc: constitution
template: impact-report
template_version: 1
status: complete
depends_on:
  - source: docs/architecture/constitution.md#mandates
    hash: sha256:<64 hex of the section after the change>
    excerpt: |
      tdd: required
---

# Impact: constitution

## Change
| Anchor | Digest before | Digest after | Requested |
|---|---|---|---|
| docs/architecture/constitution.md#mandates | sha256:<64 hex> | sha256:<64 hex> | tests are no longer optional, mandate tdd for every story |

Decision record: .devforgeai/provenance/adr/0002-mandate-tdd.md

## Affected Stories
| ID | Story | Entry | Recorded digest | Current digest | Gate verdict |
|---|---|---|---|---|---|
| IMP-001 | docs/plan/shop/stories/STORY-001.md | context: docs/architecture/constitution.md#mandates | sha256:<64 hex> | sha256:<64 hex> | stale-hash |

## Re-slice Actions
| ID | Action | Owner |
|---|---|---|
| IMP-001 | /plan shop --reslice STORY-001 | plan |
```

`id_pattern` for this template is `^IMP-[0-9]{3}$`, so every row in Affected Stories and Re-slice Actions carries an `IMP-NNN` id and the two tables share one numbering.

### Return envelope (DevForgeAI-anatomy skills only)

One schema, both providers: `devforgeai.worker-result/v1`, normative in `schemas/devforgeai/v1/worker-result.schema.json`. Three of the four phases are producers: they edit or create their files inside the candidate root with Edit and Write (Codex: `apply_patch`) and name them. `impact` is a judge: it holds no write tool at all, claims nothing, and returns its full row set in the receipt's `findings`, a string required on a judge pass or fail receipt, optional on its needs_user or could_not_run, and forbidden on a producer's, and bounded at 16,384 UTF-8 bytes. At the identity-bound `SubagentStop`, after the receipt validates, the sequencer writes that string verbatim to the fixed path `.devforgeai/work/<run>/evidence/impact_analyzer/findings.md` — run-scoped scratch, gitignored, outside the candidate root and never promoted — and records the path in `impact-result.json` for `resync_slicer` to read; the worker chooses neither the directory nor the name. The receipt is a claim plus a bounded findings body, never a file payload; the bounded `findings` does enter the primary context as part of the subagent's result, exactly as the provider model states, while the worker's transcript, reads and tool traffic stay isolated. At `devforgeai ingest-result` the sequencer derives `changed[{path, blob_sha256, kind}]` from the candidate root's checkpoint diff, refuses the result when `changed` is not a subset of `claimed_paths` (`UNCLAIMED_CHANGE`) or when any changed path is outside the fence, runs the transition oracle inside the root, writes `<phase>-result.json` with `changed` and the checkpoint ref, creates the next checkpoint and releases the lease.

```yaml
schema: devforgeai.worker-result/v1
run: "amend-constitution"
skill: "amend"
phase: "apply_change"
agent: "change_applier"
status: pass | fail | needs_user | could_not_run
reason_code: runner_missing | timeout | network | hook_fault | provider_tool_refused | prerequisite_missing | checkpoint_fault   # required only when status is could_not_run
candidate:
  id: "amend-constitution"
  input_checkpoint: "base"
claimed_paths:             # root-relative, at most 64; empty for a judge and for any non-pass status
  - docs/architecture/constitution.md
evidence_refs: []          # at most 16 paths, root-relative or under .devforgeai/work/<run>/
note: "Mandates section rewritten; three other sections byte-identical."
issues: [{id, kind, text}] # at most 10
next: ""                   # omitted: no amend phase declares rewind_to
```

Unknown keys are refused. `issues[]` is the bounded routing summary; the judge's full row set travels in `findings`, which the sequencer persists as `.devforgeai/work/<run>/evidence/impact_analyzer/findings.md` and `resync_slicer` reads by path when it renders the impact report.

`gate_policy` (`BLOCK | REQUIRE_HUMAN | WARN | OFF`) is a defect-to-action map declared in the consumed artifact, never a status returned here. A document run carries the fixed map `{unresolvable_source: BLOCK}`.

## 7. Procedure

### 7a. Steps

The body of `SKILL.md`. The primary window does exactly this and nothing else.

1. Parse the arguments: the first positional is the document basename, the rest of the line is the change request. Keep both as strings — why: the document name becomes the sequencer's `<arg>` and the change request is the one thing no file on disk holds yet.
2. Run `devforgeai phase start amend <doc>`. Exit 1 refuses the run and exit 2 rejects the arguments; print stderr verbatim and stop — why: the gate is the only thing that decides a run may open, and a refusal already names its defect.
3. Read the active phase from the `devforgeai phase start` output, or from `devforgeai status`. Load `references/<phase>.md` for that phase — why: each reference file holds the guidance one worker needs, so the primary window never carries four phases of detail at once.
4. Dispatch that phase's worker through the target's native worker mechanism, passing only: the run id, the skill name, the phase name, the file paths in `references/<phase>.md`, and — for `apply_change` only — the change request string. Do not paste the content of any file — why: the primary window persists for the whole run, and anything read into it stays there.
5. Wait for the worker to return. The `SubagentStop` hook has already handed its receipt to `devforgeai ingest-result`, which diffed the candidate root against the phase's input checkpoint, checked the derived change set against `claimed_paths` and the fence, ran the oracle inside the root, checkpointed it, and advanced, retried or blocked — why: a worker's own claim is not why a phase advances.
6. Run `devforgeai status`. If it names a new active phase, go to step 3. If it reports the run finished or blocked, print the handoff block it rendered and stop — why: the sequencer composes the handoff; the primary window prints it unchanged, and a blocked run's block already names the command that resumes it.
7. When that block reports the run `ready_to_promote` and the user asks for the promotion, call `devforgeai promote <run>` and print the second block the promotion rendered — why: promotion is never automatic, it is what moves the amended document, the ADR and the impact report from the candidate root into the canonical checkout under the lock, and a `REQUIRE_HUMAN` block is the only state in which the model may ask for it.
8. If the user abandons the run, call `devforgeai phase fail --reason <text>` — why: that is the only way a `BLOCK` handoff and a cleared enforcement block get written.

The skill never edits a document itself, never retries a worker by doing its work, and never announces that a phase passed.

Every phase of one run works inside the same candidate root — `.devforgeai/work/<run>/wt`, created by `devforgeai phase start` and named to each worker as `candidate.root` in the status block the primary window pastes into the dispatch prompt alongside `run`, `phase`, `fence` and `granted_keys`. The sequencer checkpoints the root at each transition, so `adr` builds on `apply_change`'s checkpoint and `resync` on `impact`'s, with no merge between them; exactly one producer holds the run's lease at a time, granted at dispatch and released at `devforgeai ingest-result`; the `impact` judge holds none, because its one write goes outside the root. Promotion is never automatic and is no part of Handoff: the last passing `devforgeai phase next` marks the run `ready_to_promote` and writes a `REQUIRE_HUMAN` handoff whose only forward step is `devforgeai promote <run>`, and `SKILL.md` runs that command only after the user confirms in the session. That command, not the transition, is what merges the candidate root into the canonical checkout under `.devforgeai/lock`, and it is what refuses with `STALE_BASE` when canonical HEAD has moved past the run's recorded `base_ref`, with `DIRTY_TARGET` when a canonical file among the run's changed paths is dirty, and with `MERGE_CONFLICT` when a rebase inside the root conflicted; a refused promotion leaves the run `ready_to_promote` with its candidate root intact for a retry. That one command is how the amended document, the ADR and the impact report all reach the working tree at once. A refused promotion leaves the run `ready_to_promote` and `devforgeai promote <run>` retries it.

### 7b. Sub-phases and workers

Gate, Record, Slice and Handoff dispatch no LLM: they are `devforgeai` sequencer operations. Slice runs inside `devforgeai phase start`, which resolves the incoming artifact's already-hashed context bundle and writes `.devforgeai/work/<run>/context.json`, whose path every worker of the run is handed (open item OI-1, section 9).

| # | Sub-phase | Registry phase | Performed by | Isolation |
|---|-----------|----------------|--------------|-----------|
| 0 | Gate | — | sequencer: `devforgeai phase start amend <doc>` | n/a |
| 1 | Slice | — | sequencer: `devforgeai phase start` writes `.devforgeai/work/<run>/context.json` | n/a |
| 2 | Work / Write | `apply_change` | worker: `change_applier` | required |
| 3 | Write | `adr` | worker: `amend_adr_writer` | required |
| 4 | Work | `impact` | worker: `impact_analyzer` | required |
| 5 | Write | `resync` | worker: `resync_slicer` | required |
| 6 | Record | — | sequencer: `devforgeai ingest-result`, then `devforgeai phase next` | n/a |
| 7 | Handoff | — | sequencer: `devforgeai phase next` marks the run `ready_to_promote` and writes the `REQUIRE_HUMAN` block whose only forward step is `devforgeai promote <run>`; `SKILL.md` runs that command only after the user confirms in the session, and the promotion writes the run's second handoff block | n/a |

`amend` has no Review sub-phase: the registry gives it four phases and none of them is a critic. The independent check on its output is the next story gate, which re-resolves the digests `impact_analyzer` predicted.

### 7c. Evidence and gate table

`<run>` is `amend-<doc>`. Attempt budget is 2 for every phase; there is no `rewind_to`, so no amend result may carry `next`.

| phase | worker | deterministic gate check | gate_policy | evidence file | transition oracle |
|---|---|---|---|---|---|
| `apply_change` | `change_applier` | run gate: skill known, no run already active, no active or `ready_to_promote` run whose fence overlaps this one (`FENCE_OVERLAP`, which counts the `.devforgeai/provenance/adr/**` producer exception as a fence member), and every fence entry (`docs/architecture/**`, `docs/reports/impact-<doc>.md`, `.devforgeai/provenance/adr/**`) is repository-relative, free of `..`, and either not sequencer-owned or held by a producer exception this skill owns; `candidate open` creates the root and pins `base_ref`. At `ingest-result`: `changed` derived from the checkpoint diff is a subset of `claimed_paths` (`UNCLAIMED_CHANGE` otherwise), each changed path canonicalises inside the candidate root, is inside the fence, is allowed by `writes: docs`, and is at most 1 MiB; then the whole-tree package and import rescan | document run's fixed map `{unresolvable_source: BLOCK}`; a changed path outside the fence is `write_fence_violation`, which refuses the result with no `gate_policy` consulted | `.devforgeai/work/amend-<doc>/apply_change-result.json`, `apply_change-report.md` | `document`: at least one file applied inside the fence and every declared output with non-null content present on disk |
| `adr` | `amend_adr_writer` | the same ingest checks, plus the producer-exception contract for `.devforgeai/provenance/adr/**`: the path is `NNNN-<slug>.md` with a lowercase slug, its diff kind is `added` so an existing ADR is never overwritten, a `deleted` kind is refused, and the bytes satisfy the `adr` template header — required frontmatter keys, `id` matching `^ADR-[0-9]{4}$` and equal to the filename's number, accepted `template_version`, the four required sections present as headings, no forbidden template text. Template validation runs at ingest, before the checkpoint is taken, so an ADR that fails it never reaches a checkpoint and never reaches promotion; a missing template refuses the result rather than checkpointing it unvalidated | as above; a change at any other `.devforgeai/` path is refused as sequencer-owned, and one from any other phase or skill is refused the same way | `.devforgeai/work/amend-<doc>/adr-result.json`, `adr-report.md` | `document`: the ADR file exists on disk inside the fence |
| `impact` | `impact_analyzer` | `writes: none`, so the checkpoint diff of the root is empty: this worker holds no write tool at all, `PreToolUse` denies every write path without exception, and a non-empty root diff is `UNCLAIMED_CHANGE`. `issues` at most 10 rows, `evidence_refs` at most 16 paths, `note` at most 16384 bytes, `findings` required on a pass or fail receipt, optional on needs_user or could_not_run, and at most 16384 UTF-8 bytes, which the sequencer persists at `SubagentStop` to `.devforgeai/work/amend-<doc>/evidence/impact_analyzer/findings.md` | as above; an oversize envelope is a protocol refusal and does not consume an attempt | `.devforgeai/work/amend-<doc>/impact-result.json`, `impact-report.md`, `.devforgeai/work/amend-<doc>/evidence/impact_analyzer/findings.md` | `report_only`: no file outside the fence changed since the gate snapshot and the whole-tree package and import policy holds |
| `resync` | `resync_slicer` | the same ingest checks; the only path this phase may change is `docs/reports/impact-<doc>.md`, and a change under `docs/plan/**` is outside the fence and refused | as above | `.devforgeai/work/amend-<doc>/resync-result.json`, `resync-report.md` | `document`: `docs/reports/impact-<doc>.md` exists on disk in the root. On pass this is the last phase: the run becomes `ready_to_promote` and the handoff's `next` is `devforgeai promote <run>`; `/status` is the `next` of the second handoff, written when that promotion succeeds. A promotion refused with `STALE_BASE` or `DIRTY_TARGET` leaves the run `ready_to_promote` for `devforgeai promote <run>` |

Two limits from `10-sequencer-and-contracts.md` section 3.2 apply to every row and are not overstated here: every `devforgeai phase start` defect is a refusal whatever a declared policy value says, and at transition time only `test_runner_missing` changes behaviour. `amend` brokers no stack command key, so `test_runner_missing` reaches it only through a synthesised `could_not_run`.

### 7d. Worker contracts

Each block below is the body of `agents/<role>.md`, verbatim.

```yaml
name: change_applier
skill: amend
description: Dispatch this worker first in an amend run to apply the run's one-line change request to the named architecture document, before any decision record or impact list exists.
writes: candidate
tools: [Read, Grep, Glob, Edit, Write, Bash]
model: inherit
skills: []
responsibility: Edit the named architecture document inside the candidate root so it carries the run's one-line change request, and record which sections moved.
inputs:
  - .devforgeai/work/<run>/context.json, the bundle the gate sliced
  - docs/architecture/<doc>.md, where <doc> is the run argument
  - the change request string, forwarded once by the primary window as the dispatch line
  - .devforgeai/provenance/adr/*.md, read to avoid contradicting a live decision without superseding it
outputs:
  - docs/architecture/<doc>.md, edited under the candidate root with Edit and named in claimed_paths
  - issues[]: one row per section whose bytes differ, each with the path, the anchor and the section digest before and after, at most ten
  - note: the change request string, recorded verbatim so the ADR and the impact report can quote it
must_not:
  - change a section the request does not name
  - remove or rename a frontmatter key, a required section, or the template_version of the document it read
  - write or claim .devforgeai/stack.yaml, which architect and onboard own
  - write or claim any path outside docs/architecture/
isolation: required
returns: devforgeai.worker-result/v1
compiled_to:
  - .claude/agents/amend-change_applier.md
  - .codex/agents/amend-change_applier.toml
body: job, inputs, rules, receipt
```

```yaml
name: amend_adr_writer
skill: amend
description: Dispatch this worker after apply_change to write the architecture decision record for the change this run applied, so the decision has a durable home outside the document it changed.
writes: candidate
tools: [Read, Grep, Glob, Edit, Write, Bash]
model: inherit
skills: []
responsibility: Write the architecture decision record for this run's change as a new file under the candidate root's .devforgeai/provenance/adr/ directory, which the producer exception admits and promotion carries into the canonical checkout.
inputs:
  - .devforgeai/work/amend-<doc>/apply_change-result.json, for the changed anchors, digests and the request string
  - docs/architecture/<doc>.md, the changed sections only
  - .devforgeai/provenance/adr/*.md, for the highest existing number and the decision this one supersedes
  - the adr template, which belongs to architect and is read from .devforgeai/skills/architect/templates/adr.md
outputs:
  - .devforgeai/provenance/adr/NNNN-<slug>.md, created under the candidate root and named in claimed_paths, with frontmatter id, template, template_version, status, date, supersedes and depends_on, and sections Context, Decision, Consequences, Alternatives
must_not:
  - reuse an ADR number already present in .devforgeai/provenance/adr/, or write a path there that is not NNNN-<slug>.md
  - overwrite or delete an existing ADR; this phase creates one file
  - write or claim any other path under .devforgeai/: the producer exception is this directory, not the prefix
  - restate the amended document instead of recording the decision, its consequences and the alternatives considered
isolation: required
returns: devforgeai.worker-result/v1
compiled_to:
  - .claude/agents/amend-amend_adr_writer.md
  - .codex/agents/amend-amend_adr_writer.toml
body: job, inputs, rules, receipt
```

```yaml
name: impact_analyzer
skill: amend
description: Dispatch this worker after adr to judge which stories the change invalidated, when a reader needs the list of artifacts whose next gate will refuse them.
writes: none
tools: [Read, Grep, Glob, Bash]
model: inherit
skills: []
responsibility: List every story whose recorded provenance or context covers a section this run changed, with the verdict its next story gate will reach.
inputs:
  - .devforgeai/work/amend-<doc>/apply_change-result.json, for the changed path, anchors and digests
  - docs/plan/*/stories/STORY-*.md, frontmatter provenance[] and context[] only
  - docs/plan/*/epics/EPIC-*.md, frontmatter depends_on only
outputs:
  - findings: one row per artifact entry examined, each with the artifact, the entry kind, the source, the recorded digest, the current digest and the verdict, which is resolved, stale-hash or unresolvable-source; required on a pass or fail receipt and optional on needs_user or could_not_run, at most 16384 UTF-8 bytes, persisted by the sequencer to .devforgeai/work/<run>/evidence/impact_analyzer/findings.md
  - issues[]: at most 10 rows, the artifacts whose next gate refuses them, drawn from those rows
  - note: the counts of each verdict across every artifact examined
  - evidence_refs[]: the story and epic paths the rows were read from; never its own findings path, which does not exist until the sequencer has persisted it
must_not:
  - write any file anywhere; this worker holds no write tool and its rows travel in findings
  - report a story as affected without a recorded and a current digest for the same entry
  - open a story's body; the entries this phase compares are in frontmatter
isolation: required
returns: devforgeai.worker-result/v1
compiled_to:
  - .claude/agents/amend-impact_analyzer.md
  - .codex/agents/amend-impact_analyzer.toml
body: job, inputs, rules, receipt
```

```yaml
name: resync_slicer
skill: amend
description: Dispatch this worker last in an amend run to write the impact report: what changed, which artifacts the change invalidates, and the exact command that re-slices each.
writes: candidate
tools: [Read, Grep, Glob, Edit, Write, Bash]
model: inherit
skills: []
responsibility: Write the impact report inside the candidate root: what changed, which artifacts the change invalidates, and the exact command that re-slices each.
inputs:
  - .devforgeai/work/amend-<doc>/apply_change-result.json, adr-result.json and impact-result.json, and .devforgeai/work/amend-<doc>/evidence/impact_analyzer/findings.md, the persisted judge findings impact-result.json names
  - assets/impact-report.md, the impact-report skeleton
outputs:
  - docs/reports/impact-<doc>.md, written under the candidate root with Edit or Write and named in claimed_paths
  - evidence_refs[]: the three preceding result paths and the persisted impact findings the report was rendered from
must_not:
  - write or claim any path under docs/plan/, which plan owns and which is outside this run's fence
  - name an artifact that the persisted impact findings do not carry
  - return a findings key; findings is a judge field and a producer receipt carrying it is refused
  - write a re-slice action for a row whose verdict is resolved
  - write or claim any path other than docs/reports/impact-<doc>.md
isolation: required
returns: devforgeai.worker-result/v1
compiled_to:
  - .claude/agents/amend-resync_slicer.md
  - .codex/agents/amend-resync_slicer.toml
body: job, inputs, rules, receipt
```

Three of the four workers are producers: their tools are `Read`, `Grep`, `Glob`, `Edit`, `Write` and `Bash`, with `Edit` and `Write` scoped to the candidate root by the `PreToolUse` check and compiled to `apply_patch` on the Codex target. `impact_analyzer` is a judge: it holds `Read`, `Grep`, `Glob` and `Bash` and no write tool of any kind, so it cannot touch the stories it reports on, and its row set comes back in the receipt's `findings` for the sequencer to persist. No `amend` phase grants a stack key, so no worker is granted a `devforgeai run` key, and no worker holds a git write, a package manager, a network tool or a raw stack command. `isolation` above is the framework's `required | preferred` declaration, not Claude's subagent `isolation` key, which the framework never sets because its one value forks a worktree from HEAD and would split the run's linear history. `hooks`, `memory`, `background` and `permissionMode` are Claude-only keys this skill leaves unset. `tools` names tools only: a Claude Code subagent's `tools:` frontmatter accepts tool names and MCP server patterns, never a command pattern, so the hook dispatcher is the only command-level bound. A judge's `Bash` runs `devforgeai status` and the dispatcher's read-only command set (`cat cmp cut diff echo grep head jq ls pwd rg sha256sum tail test tr wc`, plus read-only git subcommands inside the root) and nothing else; a producer's additionally runs `devforgeai run KEY` for its granted keys.

Each worker's envelope must carry `run`, `skill` and `phase` equal to the enforcement block. The primary window forwards those three ids in the dispatch line; a worker may also read them from `devforgeai status`, which is the one sequencer operation a phase worker may call.

### 7e. Handoff outcomes

`handoff.outcomes` as the skill declares it. The sequencer selects the row by envelope status and fills the placeholders from state, so the rows below are keyed on status, not on narrative outcome. `{doc}` is the run argument.

| Outcome | Selected when | Next steps |
|---------|---------------|------------|
| `ready_to_promote` | the last phase passed; the run's work is complete and unpromoted | 1. `devforgeai promote {run}` — the first of the run's two handoff blocks; `SKILL.md` runs the command only after the user confirms in the session, and the promotion writes the second block, whose row is one of the two below. |
| `pass` | all four phases passed and `impact-result.json` carries no unresolved row | 1. `/status`. The impact report's Re-slice Actions table is empty. |
| `pass` | all four phases passed with affected artifacts | 1. `/status`. Open items carry one `/plan {slug} --reslice STORY-NNN` per `issues[]` row, printed before the next step; `docs/reports/impact-{doc}.md` holds the full list when it exceeds the ten-row cap. |
| `REQUIRE_HUMAN` | any phase returned `needs_user`; the run blocks at that phase on the first ask with no retry — status stays `active`, the lease is released, `run.yaml#blocked_at` names the phase and the candidate root survives | 1. answer the question in `open_items`, then `/amend {doc} "<the resolved change>"`, which resumes the blocked run at `blocked_at` with attempts reset. Also possible: `devforgeai phase fail --reason <text>` to abandon the root, then `/status`. |
| `REQUIRE_HUMAN` | a phase returned `fail`, or its oracle reported problems, at the attempt limit of 2; the run blocks and keeps its root | 1. fix the cause `repair_route` names — the phase, its report file, and `/architect {slug}` when the missing input is a document architect owns — then `/amend {doc} "<the same change>"`, which resumes the blocked run at `blocked_at` with attempts reset. Repairing with another skill's run needs `devforgeai phase fail --reason <text>` first, because the blocked run still holds the fence. Also possible: `devforgeai phase fail --reason <text>`, then `/status`. |
| `REQUIRE_HUMAN` | `could_not_run`; also the synthesised result when a stop event carries no worker identity | 1. repair the dependency named by `reason_code`, then `/amend {doc} "<the same change>"`. |
| `BLOCK` | the primary window called `devforgeai phase fail --reason` | 1. `/amend {doc} --fix`, which the sequencer renders from its `BLOCK` default and which opens a fresh run from phase 1. |

`amend` invokes no other skill. Its edges to `plan`, `analyze`, `review` and `retro` are handoff rows: a finishing run's `next` names the command and a human or a fresh session runs it (open item OI-7, section 9).

## 8. Bundled resources

### Layout (fixed)

```
amend/SKILL.md              # <=500 lines: identity, phase list, dispatch loop, handoff table
  references/apply_change.md
  references/adr.md
  references/impact.md
  references/resync.md
  references/envelope.md
  agents/change_applier.md
  agents/amend_adr_writer.md
  agents/impact_analyzer.md
  agents/resync_slicer.md
  assets/impact-report.md
```

Link depth: `SKILL.md` links to `references/`, `agents/` and `assets/`; an `agents/*.md` links to `references/*.md`; nothing links further.

### scripts/

None. `amend` bundles no script: the one operation a script would have performed — putting the decision record at its registry path — is the sequencer's, through the producer exception for `.devforgeai/provenance/adr/**` and the template-header check in `10-sequencer-and-contracts.md` section 5.2, step 13. A script that moved or validated ADRs beside that check would be a second write path with a second opinion.

### references/
| File | Content | Load when |
|------|---------|-----------|
| `apply_change.md` | how to locate the named document, the anchor rule from `01-skill-anatomy.md#context-bundle-format`, the requirement to keep the producing template's frontmatter and required sections, how to compute the section digest before and after, and the `issues` row shape that carries one changed section each | before dispatching `change_applier` |
| `adr.md` | the `adr` template's header keys and where the template lives (`architect` owns it), the numbering rule over `.devforgeai/provenance/adr/`, the `NNNN-<slug>.md` filename shape the sequencer enforces, the append-only rule and when `supersedes` is filled, and the four required sections | before dispatching `amend_adr_writer` |
| `impact.md` | how to read `apply_change-result.json`, which story frontmatter entries to compare, the three verdicts from `10-sequencer-and-contracts.md` section 3.4, and how line-range anchors overlapping a changed range are treated | before dispatching `impact_analyzer` |
| `resync.md` | the `impact-report` template's three sections, the `IMP-NNN` id rule shared across its tables, and which command each verdict maps to | before dispatching `resync_slicer` |
| `envelope.md` | the `devforgeai.worker-result/v1` schema, its field bounds — `findings` included, at 16,384 UTF-8 bytes, required on a judge pass or fail receipt, optional on its needs_user or could_not_run, and forbidden on a producer's — the fixed path the sequencer persists `findings` to, and the rule that the final message is exactly one such object with no Markdown fence | every dispatch |

### assets/
| File | Used for |
|------|----------|
| `impact-report.md` | seeds `docs/reports/impact-<doc>.md`; carries the `impact-report` template header (`template_version: 1`, `id_pattern` `^IMP-[0-9]{3}$`, required sections Change, Affected Stories, Re-slice Actions) |

There is no `assets/adr.md`. The `adr` template belongs to `architect`, `amend_adr_writer` reads it from `.devforgeai/skills/architect/templates/adr.md`, and the sequencer validates against that same file; a copy here would be a second header able to drift out of agreement with the one that decides.

### agents/
| File | Worker (from section 7d) | writes | tools | compiled to |
|------|-------------------------|--------|-------|-------------|
| `change_applier.md` | `change_applier` | candidate | Read, Grep, Glob, Edit, Write, Bash | `.claude/agents/amend-change_applier.md`, `.codex/agents/amend-change_applier.toml` |
| `amend_adr_writer.md` | `amend_adr_writer` | candidate | Read, Grep, Glob, Edit, Write, Bash | `.claude/agents/amend-amend_adr_writer.md`, `.codex/agents/amend-amend_adr_writer.toml` |
| `impact_analyzer.md` | `impact_analyzer` | none | Read, Grep, Glob, Bash | `.claude/agents/amend-impact_analyzer.md`, `.codex/agents/amend-impact_analyzer.toml` |
| `resync_slicer.md` | `resync_slicer` | candidate | Read, Grep, Glob, Edit, Write, Bash | `.claude/agents/amend-resync_slicer.md`, `.codex/agents/amend-resync_slicer.toml` |

## 9. Gotchas and edge cases

| Situation | What goes wrong | What to do instead |
|-----------|-----------------|--------------------|
| OI-6: the ADR's canonical home is `.devforgeai/provenance/adr/NNNN-<slug>.md` | `.devforgeai/provenance/**` is sequencer-owned in `policy.ALWAYS_DENY`, so a fence entry naming it would once have been refused at the gate and any proposal refused at validation. An earlier draft staged the record under `docs/architecture/adr/` and had a human move it, which left the consumers that read the provenance directory (`analyze`, `review`, `retro`, `drift`) blind to it until someone remembered. | `.devforgeai/provenance/adr/**` is a producer exception, exactly as `.devforgeai/stack.yaml` is: it is in `amend`'s document fence, only the `adr` phase may write a path matching it, it writes that path inside the candidate root like every other producer, and the sequencer checks the bytes against the `adr` template header and the `NNNN-<slug>.md` filename shape at ingest, before the checkpoint is taken. The file reaches the canonical checkout with the rest of the run only when the user runs `devforgeai promote <run>`, never at Handoff; no worker writes into canonical `.devforgeai/`, which the sequencer alone owns. There is no staging path and no install step. Three consequences to design around: `FENCE_OVERLAP` counts the exception path as a fence member, so an `amend` run and an `architect` run cannot both be active; no amend phase declares `rewind_to`, so a written ADR is not rewound but is discarded whole with the candidate root if the run is abandoned; and `architect`'s `adr` phase holds the same exception, so its decisions reach canonical through its own promotion (`11-artifact-registry.md` section 6, divergence 6). |
| OI-1: which component performs Slice | A spec promising a slice worker would describe an agent file with no registry phase to run it. | Slice is a sequencer step inside `devforgeai phase start`: it resolves the incoming artifact's already-hashed context bundle and writes `.devforgeai/work/<run>/context.json`, whose path every worker of the run is handed. No framework worker performs it and this package ships no agent file for it. |
| OI-2 and section 3.4: which digests the gate re-resolves | An earlier draft said the gate checked only `commands.hash`, which would make the impact list advisory. | `10-sequencer-and-contracts.md` section 3.4 now re-resolves every `provenance[]` and `context[]` entry with the hash rule in `01-skill-anatomy.md#context-bundle-format`, and `stale-hash` is never downgradable. That is what makes this skill's impact list actionable: a story it lists is a story the next `/dev`, `/review` or `/qa` gate refuses. |
| OI-3: worker tools | A generator that gives every worker one list either leaves `change_applier` with no way to edit the document, or gives `impact_analyzer` a write tool over the stories it was asked to report on. | Tools are per role. The judge `impact_analyzer` holds `Read`, `Grep`, `Glob` and `Bash` and no write tool at all, its rows returned in the receipt's `findings`. The three producers hold `Edit` and `Write` inside the candidate root, scoped by the `PreToolUse` check. No amend phase grants a stack command key, so no worker is granted a `devforgeai run` key. |
| OI-4: a worker returns `fail` with no rewind target | Nothing in section 5.4 lists that row, so it looks like a silent pass. | `examples/hooks/devforgeai.py:1017-1018` inserts the reported failure as a transition problem, so the phase retries to its limit of 2 and then blocks `REQUIRE_HUMAN`. No amend phase declares `rewind_to`, so an amend result carrying `next` is refused at `ingest-result`. |
| OI-5: `--fix`, `--retry` and `--resync` look like resume flags | An earlier draft closed the run on `needs_user` and at an exhausted attempt budget, so no flag could resume anything. | Settled: `10-sequencer-and-contracts.md` sections 2 and 3.1 leave such a run `active` with its lease released, its candidate root kept and `run.yaml#blocked_at` naming the phase, and `devforgeai phase start amend <doc>` — same skill, same argument — resumes it there with attempts reset. Resuming is the command, not a flag: `/amend {doc} "<the same change>"` does it. With no blocked run to resume, the same call opens a fresh run from phase 1; every flag only changes what the workers read. |
| OI-7: `02-skill-roster.md` says amend calls plan | `devforgeai phase start` refuses while a run is active, so a nested run is impossible. | The plan edge is a handoff row and an impact-report action. The procedure never invokes another command. |
| OI-8: worker naming | `05-subagent-sets.md` writes `change-applier` and `adr-writer`; the registry writes `change_applier` and `amend_adr_writer`. | The registry name is canonical and is what `agent_type` is compared against. Use it in section 7, in the `agents/` filenames and in the evidence table; the hyphenated form is a display alias. |
| `/amend --resync <artifact>` appears in the gate outcomes in `01-skill-anatomy.md` | Every amend run executes all four phases, and `apply_change` is a `writes: docs` phase whose oracle needs a file, so a resync run with no document change cannot pass phase 1 unless it edits the document into a state whose bytes differ; even then `resync_slicer` may not touch `docs/plan/**`, so no story bundle is refreshed. | For a stale story bundle, run `/plan {slug} --reslice STORY-NNN`, which the impact report already names. This spec does not define a `--resync` behaviour beyond a fresh run. |
| The run id is `amend-<doc>` | Amending the same document twice reuses the run directory, so the second run overwrites `.devforgeai/work/amend-<doc>/*-result.json` and the earlier evidence is gone. | The durable record is the ADR under `.devforgeai/provenance/adr/` and `docs/reports/impact-<doc>.md`, plus one `provenance/log.jsonl` line per run. Read those, not the work directory, when reconstructing history. |
| The fence is `docs/architecture/**`, not the named document | A proposal that rewrites a second architecture document passes fence validation, because the fence admits the whole directory and no script compares a path to `<doc>`. | `change_applier`'s `must_not` forbids it and every applied path is recorded in `apply_change-result.json` and the rendered view, so `/analyze` sees it. There is no deterministic check today; this row exists so no reader assumes one. |
| Amending `techstack.md` leaves `.devforgeai/stack.yaml` behind | Only `architect`'s techstack phase and `onboard`'s code_map phase may write that file, so the machine-readable commands and package policy still describe the old stack, and every story pinning `commands.hash` still resolves against it. | `resync_slicer` writes a Re-slice Actions row naming `/architect <slug>` whenever the amended document is `techstack`. The row is data in the report, not an invocation. |
| The document gate checks the fence, not the document | `devforgeai phase start amend design-auth` opens a run for a document that does not exist. | `change_applier` returns `fail` with an empty `claimed_paths` and an issue row naming the missing path; two attempts later the run blocks with `REQUIRE_HUMAN`. Nothing reaches the canonical checkout, because a run that never promotes leaves the candidate root and its checkpoints behind and `candidate abandon` deletes them. |
| Where the impact rows live | The receipt has no bounded `evidence` object, and a repository with hundreds of stories has more affected rows than `issues[]` can carry | `impact_analyzer` returns the full row set in the receipt's `findings`, which the sequencer persists to `.devforgeai/work/<run>/evidence/impact_analyzer/findings.md` and records in `impact-result.json`; `issues[]` is the bounded routing summary the handoff prints, and `resync_slicer` reads the persisted file by path. `findings` is capped at 16,384 UTF-8 bytes and an oversize receipt is refused, so a repository whose affected set does not fit is a real limit of this skill and not a checked constraint: the rows that fit are returned worst-verdict first and `note` states the count returned against the count found. `WRITE-MODEL-REVISION.md` D13 item 5 forbids a side-channel file and item 9 defers the structured evidence broker to `12-post-mvp.md`. |
| The change request is not evidence | The enforcement block records `arg` only, so the quoted change text lives nowhere the sequencer writes. | `change_applier` copies it verbatim into the receipt's `note`, which the sequencer records in `apply_change-result.json`; the ADR's Decision section and the impact report's Change table are its durable record. |
| Which worker may write, and where | A generator that treated the four workers alike would let `impact_analyzer` repair the stories it was asked to report on, and the impact list would then describe a repository nobody amended | Roles follow the registry's `writes` column: `apply_change`, `adr` and `resync` declare `docs` and compile to producers holding `Edit` and `Write`; `impact` declares `none` in the registry and compiles to a judge declaring `writes: none`, which holds no write tool at all and returns its rows in the receipt's `findings`. Every write a producer makes lands inside the candidate root and is named in `claimed_paths`; the sequencer derives what actually changed from the checkpoint diff and refuses anything unclaimed as `UNCLAIMED_CHANGE`. |
| D13 (2026-09-03): the judge had an evidence-directory `Write` | Claude Code 2.1.259 refuses a subagent's `Write` of a report-like Markdown file before any hook runs, so `impact_analyzer` could not be relied on to write `rows.json`, and `resync_slicer` would render the impact report from a file that may not exist | `WRITE-MODEL-REVISION.md` D13 applied here: `impact_analyzer` declares `writes: none` (section 7c row, section 7d header, the section 8 `agents/` table, the section 12 Tools and target rows) and carries `Read`, `Grep`, `Glob`, `Bash` with no `Write`, `Edit` or `apply_patch`. Its rows travel in the receipt's `findings` string, required on a pass or fail and optional otherwise, at most 16,384 UTF-8 bytes, which the sequencer persists verbatim at `SubagentStop` to `.devforgeai/work/<run>/evidence/impact_analyzer/findings.md` and records in `impact-result.json`; `rows.json` is gone. `resync_slicer` reads that path, section 7c names it in the evidence-file column, and the judge never names its own findings path in `evidence_refs`, because that file does not exist when the receipt is validated. The bounded `findings` body does enter the primary context as part of the subagent's result (D13 item 4); what stays isolated is the worker's transcript, reads and tool traffic. Earlier revisions of `10-sequencer-and-contracts.md` and `09-hook-dispatcher.md` carried the superseded evidence-writing branch; D13 is now applied in those documents and here. |
| Where the amended document ends up | A reader expects `docs/architecture/<doc>.md` to change in the working tree the moment `apply_change` passes | Every write lands in the candidate root `.devforgeai/work/<run>/wt`, which is gitignored. The amended document, the ADR and the impact report reach the canonical checkout together only at `devforgeai promote <run>`, never at Handoff: the last passing `devforgeai phase next` marks the run `ready_to_promote` and writes a `REQUIRE_HUMAN` handoff whose only forward step is that command, and `SKILL.md` runs it only after the user confirms in the session. A promotion refused with `STALE_BASE` — canonical HEAD moved past `base_ref` — `DIRTY_TARGET` — a canonical file among the changed paths is dirty — or `MERGE_CONFLICT` refuses the promote command, not the transition, and leaves the run `ready_to_promote` with its candidate root intact; `devforgeai promote <run>` retries it once the user has resolved the reason. |
| A `REQUIRE_HUMAN` run treated as closed, with `/status` as its next step | `needs_user` and an exhausted attempt budget were described as closing the run, so the section 7e rows sent the user to `/status` and the OI-5 row said no flag could resume anything. A closed run has no candidate root, so the work the phases had already done appeared to be lost | Settled in `10-sequencer-and-contracts.md` (section 2's `phase start` row, section 3.1, section 5.4's `needs_user` row, section 6's `REQUIRE_HUMAN`, blocked-run row): such a run stays `active` with its lease released, keeps its candidate root and every checkpoint, and records `run.yaml#blocked_at`. `devforgeai phase start amend <arg>` — the same skill and argument — resumes it at `blocked_at` with `attempts` reset. The two section 7e `REQUIRE_HUMAN` rows, UC-3's result line, section 7a step 6 and OI-5 now name `/amend {doc} "<the same change>"` as the forward step, with `devforgeai phase fail --reason <text>` then `/status` as the abandon route; any other skill on the same story needs that `phase fail` first. |
| Promotion read as part of Handoff | "reach the canonical checkout together at Handoff, when the sequencer promotes the run" (and, in section 6, "reaches canonical by promotion at Handoff") made `devforgeai phase next` move canonical bytes on its own, with no point at which the user consents | Section 6's two ADR sentences, section 7b's candidate-root paragraph ("At Handoff the sequencer promotes the run … which is how the amended document, the ADR and the impact report all reach the working tree at once"), section 7b row 7 and the row above now carry the two-block model of `WRITE-MODEL-REVISION.md` D7 and `10-sequencer-and-contracts.md` sections 5.4, 6 and 12.4: `phase next` marks the run `ready_to_promote` and writes a `REQUIRE_HUMAN` block whose only forward step is `devforgeai promote <run>`; `SKILL.md` runs that command only after the user confirms; the promotion writes the second block. |
| UC-1 step 3 had the sequencer promote the ADR at ingest | "the sequencer checks it against the `adr` template header at ingest and promotes it with the run" put a canonical write inside a transition | The ingest check stands; the step now says the ADR reaches `.devforgeai/provenance/adr/` in the canonical checkout only when the user runs `devforgeai promote <run>` at the end of the run. |
| `STALE_BASE`, `DIRTY_TARGET` and `MERGE_CONFLICT` attributed to the transition | The refusals read as ways the last transition can fail, so a reader looks for them among the oracles | All three refuse `devforgeai promote <run>` (`10-sequencer-and-contracts.md` section 2's refusal table, section 12.4's ordered steps). The row above names the command that raises them, adds `MERGE_CONFLICT`, and states that the root and its checkpoints survive every refusal. |
| The section 7e table had no `ready_to_promote` row | The row below already told a reader to read every `pass` row as the post-promotion block, but the table itself never named the promote step, so a generator reading only the table would omit it | A `ready_to_promote` outcome row now heads the table with `devforgeai promote {run}` as its one forward step; the two `pass` rows keep `/status` and are the second block. |
| `promote <run>` was missing from the compiled grammar | Section 7f's Tools row already granted `devforgeai promote <run>`, but the section 7a procedure stopped at printing the block and the section 12 `allowed-tools` line omitted it, so the compiled skill could not run the only command its own handoff names | `WRITE-MODEL-REVISION.md` D7 propagates the fifth model-callable form everywhere the four are enumerated. A new step 7 in section 7a calls it after the user asks (the abandon step became 8), the `allowed-tools` line carries `Bash(devforgeai promote:*)`, section 12's paragraph above it says five model-callable operations rather than four, and the Tools row no longer describes the command as something reached only after a refused promotion. |
| Reading the section 7e `pass` rows as the block a finished run prints first | `10-sequencer-and-contracts.md#6-handoff-envelope` no longer carries a `document run, all phases passed` row: `/status` is now the `next` of a **promoted** document run, and a run whose phases all passed but which is not yet promoted takes `devforgeai promote <run>` instead. | Read every 7e `pass` row as the post-promotion block. The first block a finished run writes names `devforgeai promote <run>`, which the user runs; the `/status` row is what the second block carries. |
| Amending a document while an architect run is open | Both runs claim `.devforgeai/provenance/adr/**`, and the second to promote would write an ADR number the first already used | `devforgeai phase start` refuses the second with `FENCE_OVERLAP`: the producer-exception path counts as a fence member, so an `amend` run and an `architect` run cannot both be active. The ADR numbering therefore never races. |
| Template validation and the checkpoint | An ADR that fails the `adr` template header would be checkpointed and then have to be unwound | Template validation runs at ingest, before the checkpoint is taken. A failing ADR refuses the result, the phase burns an attempt, and no checkpoint records it. |

## 10. Success criteria and test cases

### Success criteria

- Triggers on the section 4 positives and on none of the near-misses.
- The transcript contains exactly one `devforgeai phase start amend <doc>` and no other `devforgeai` operation except `devforgeai status` and, when the user abandons, `devforgeai phase fail --reason`.
- Four worker dispatches at most, in registry order, one per phase.
- Every path in the run's checkpoint diff lies inside `docs/architecture/**`, `docs/reports/impact-<doc>.md` or `.devforgeai/provenance/adr/**`, appears in its phase's `claimed_paths`, and the last is changed only by the `adr` phase. The `impact` phase writes nothing at all, and the sequencer's persisted `findings.md` sits under `.devforgeai/work/<run>/evidence/impact_analyzer/`, which no checkpoint records and no promotion carries.
- Every story listed under Affected Stories carries a recorded digest and a current digest that differ; no story with matching digests is listed.
- `SKILL.md` is under 500 lines; `agents/` holds exactly the four files in section 8.

### Fixture

The generator creates `fixtures/amend/` with exactly these files before running any eval, and copies it to `amend-workspace/fixture-<eval-id>/` per eval:

| Path | Content |
|---|---|
| `.devforgeai/state.yaml` | `version: 1`, `target: [claude]`, `mode: greenfield`, `slug: shop`, `phase: plan`, `phases:` with a single `plan` entry whose `status` is `done`, `enforcement: {}`, `stories: {}`, `next: "/status"`. No active run, so `phase start` can open one. |
| `.devforgeai/hooks/devforgeai.py`, `policy.py`, `dispatch.py` | byte copies of `docs/design/examples/hooks/devforgeai.py`, `policy.py` and `dispatch.py`, so the `SubagentStop` route applies results |
| `.devforgeai/stack.yaml` | the `python` anchor from `docs/design/examples/hooks/fixtures/.devforgeai/stack.yaml` |
| `.devforgeai/skills/architect/templates/adr.md` | byte copy of `docs/design/templates/adr.md`: the `adr` template header the sequencer validates every ADR proposal against. Without it the `adr` phase fails closed, because an unvalidated ADR is refused rather than applied |
| `.devforgeai/provenance/adr/0001-choose-sqlite.md` | `adr` template v1, `id: ADR-0001`, `status: accepted`, `supersedes: none`, sections Context, Decision, Consequences, Alternatives |
| `docs/architecture/constitution.md` | `constitution` template v1; frontmatter `slug: shop`, `template: constitution`, `template_version: 1`, `status: approved`, `provenance: []`, `depends_on: []`; sections `## Principles`, `## Mandates`, `## Constraints`, `## Style`. `## Mandates` contains exactly one line of body: `tests: optional` |
| `docs/plan/shop/stories/STORY-001.md` | `story` template v3, `status: ready`, `write_fence: ["src/**"]`, `commands` pinning `.devforgeai/stack.yaml#python` with the file's true digest, `test_plan` with one row, and a `context[]` entry whose `source` is `docs/architecture/constitution.md#mandates` and whose `hash` is the true digest of that section in this fixture |
| `docs/plan/shop/stories/STORY-002.md` | the same shape, except its only `context[]` entry is `docs/architecture/techstack.md#testing` |
| `docs/architecture/techstack.md` | `techstack` template v1 with the four required sections, so STORY-002's entry resolves |

Overlay for eval 2: `fixtures/amend/overlays/eval-2/docs/plan/shop/stories/STORY-001.md` replaces the base file with one whose only `context[]` entry is `docs/architecture/sourcetree.md#layout`. Overlay for eval 3: `fixtures/amend/overlays/eval-3/` is empty except for a marker file `.keep`, because eval 3 exercises a document that is absent from the base fixture.

### evals/evals.json (used verbatim)

```json
{
  "skill_name": "amend",
  "evals": [
    {
      "id": 1,
      "prompt": "/amend constitution \"tests are no longer optional, mandate tdd for every story\"",
      "expected_output": "The constitution's Mandates section reads tdd: required, ADR-0002 is applied under .devforgeai/provenance/adr/, and the impact report names STORY-001 as stale and STORY-002 as unaffected.",
      "files": ["fixtures/amend"],
      "expectations": [
        "The transcript contains exactly one occurrence of 'devforgeai phase start amend constitution', and it precedes every worker dispatch",
        "docs/architecture/constitution.md contains the line 'tdd: required' under the heading '## Mandates' and still contains the headings '## Principles', '## Constraints' and '## Style'",
        "A file matching .devforgeai/provenance/adr/0002-*.md exists, its frontmatter id is ADR-0002, and it contains the headings '## Context', '## Decision', '## Consequences' and '## Alternatives'",
        "docs/reports/impact-constitution.md contains 'STORY-001' under the heading '## Affected Stories' and does not contain the string 'STORY-002'",
        "docs/reports/impact-constitution.md contains the exact command '/plan shop --reslice STORY-001' under the heading '## Re-slice Actions'",
        "No file under docs/plan/ differs from the fixture copy"
      ]
    },
    {
      "id": 2,
      "prompt": "/amend constitution \"tests are no longer optional, mandate tdd for every story\"",
      "expected_output": "The change and the ADR are applied, and the impact report records that no artifact is invalidated.",
      "files": ["fixtures/amend", "fixtures/amend/overlays/eval-2"],
      "expectations": [
        "docs/architecture/constitution.md contains the line 'tdd: required' under the heading '## Mandates'",
        "docs/reports/impact-constitution.md exists and its '## Affected Stories' section contains no line beginning with 'STORY-'",
        "docs/reports/impact-constitution.md contains no occurrence of the string '--reslice'",
        "The final printed handoff block lists '/status' as step 1 under 'Next steps'"
      ]
    },
    {
      "id": 3,
      "prompt": "/amend design-auth \"record that we chose session cookies over JWTs\"",
      "expected_output": "The run opens, the first phase cannot produce a document, and the run blocks without writing anything.",
      "files": ["fixtures/amend", "fixtures/amend/overlays/eval-3"],
      "expectations": [
        "No file named docs/architecture/design-auth.md exists after the run",
        "No file exists under .devforgeai/provenance/adr/ that was not in the fixture",
        "The transcript shows at most two dispatches of the change_applier worker and no dispatch of amend_adr_writer",
        "The final printed handoff block names '/status' as step 1 and reports the outcome REQUIRE_HUMAN"
      ]
    }
  ]
}
```

Quick-mode results are generation feedback only: one enabled run per eval and no baseline. They are not runtime conformance evidence, and no section of this spec gates on such evidence; the deferred contract is `12-post-mvp.md#pm-02`.

## 11. Dependencies and compatibility

| Kind | Value |
|------|-------|
| Tools | `SKILL.md`: `Read`, `Agent`, and a Bash grammar no wider than `devforgeai status`, `devforgeai phase start amend <doc>`, `devforgeai phase fail --reason <text>`, `devforgeai validate`, plus `devforgeai promote <run>`, which the last passing transition's `REQUIRE_HUMAN` block names as its only forward step and which `SKILL.md` calls only after the user asks for it. Judges: `Read`, `Grep`, `Glob` and `Bash`, with no `Write`, no `Edit` and no `apply_patch`; their rows are returned in the receipt's `findings` and persisted by the sequencer. Producers: the same read set plus `Edit` and `Write` (Codex `apply_patch`) inside the candidate root. No phase grants a stack key, so no worker is granted a `devforgeai run` key. |
| MCP servers | none |
| Runtime | None of amend's own: the package bundles no script. The sequencer and hook dispatcher it drives need Python 3.11+ |
| Project commands | none. No amend phase declares a run key, so this skill resolves no `.devforgeai/stack.yaml` anchor and brokers no command. Its evidence table's oracles are `document` and `report_only`, neither of which runs a command. |
| DevForgeAI/Core compatibility | DevForgeAI sequencer contract `10-sequencer-and-contracts.md` dated 2026-09-02; worker envelope `devforgeai.worker-result/v1`; `impact-report` template version 1; `adr` template version 1. Research Core: NOT_APPLICABLE. |
| Other skills | Consumes documents `architect` produces, stories `plan` produces, and the `retro-report`, `drift-report` and `analyze-report` whose Actions rows name this command. Hands off to `plan` (re-slice), `analyze`, `review` and `retro` through `impact-report` and `adr`, and to `architect` for `stack.yaml` regeneration. Must not conflict with `drift`, which reports the same documents against code but changes none of them. |

Deferred dependencies. Each names its `12-post-mvp.md` entry and what this skill does today without it.

- `12-post-mvp.md#pm-01`. Runtime verification that a dispatched worker ran in its own context window is deferred. Today `isolation: required` is a declaration compiled into the target profile, and `skill-validator` checks the declaration structurally.
- `12-post-mvp.md#pm-02`. There is no runtime conformance evidence for this skill. Quick-mode eval results are generation feedback and no section gates on them.
- `12-post-mvp.md#pm-06`. Only the `skip` and `quick` eval modes exist; a third mode name is a spec defect.
- `12-post-mvp.md#pm-10`. There is no clean-checkout chain validator, so nothing outside a session re-checks that an amended document and its dependent stories agree. `devforgeai validate` is a read-only invariant scan of the active run.

Frontmatter values derived from this table. `allowed-tools` is a space-separated string of pre-approved tool patterns, per the Agent Skills specification; the Bash entries below are the five model-callable operations, `devforgeai promote <run>` included, and nothing wider, because an unscoped `Bash` entry would exceed the grammar section 14's skill-validator check enforces.

```yaml
compatibility: "Claude Code and Codex terminals. Requires an installed DevForgeAI sequencer and hook dispatcher, and the adr template at .devforgeai/skills/architect/templates/adr.md, which the sequencer validates every ADR proposal against."
allowed-tools: "Read Agent Bash(devforgeai status) Bash(devforgeai phase start amend:*) Bash(devforgeai phase fail:*) Bash(devforgeai validate) Bash(devforgeai promote:*)"
```

## 12. Targets

The generator produces one provider-neutral semantic package and a separate adapter for each selected target when frontmatter, invocation policy, or agent configuration differs. Provider-neutral resources may be shared. Adapter directories are not required to be byte-identical or symlinked.

| Target | Install path | Invocation | Subagents | Notes |
|--------|--------------|------------|-----------|-------|
| claude | `.claude/skills/amend/` | `/amend <doc> "<change>"` | provider-native workers: producers `change_applier`, `amend_adr_writer` and `resync_slicer` (`writes: candidate`), judge `impact_analyzer` (`writes: none`) | Provider-specific frontmatter keys (`argument-hint`, `disable-model-invocation`) are compiled into this target's SKILL.md only. |
| codex | `.agents/skills/amend/` plus `.codex/agents/` profiles | `$amend <doc> "<change>"` | the same four names; Codex custom-agent `name` equals the Claude agent frontmatter `name`, so `agent_type` needs no translation | Portable six-field frontmatter only; policy goes in target-side configuration. |
| both | separate `.claude/skills/amend/` and `.agents/skills/amend/` adapters | as above | as above | Share only provider-neutral resources; validate each adapter independently. |

```yaml
metadata:
  version: "1.0.0"
  devforgeai-spec: "SKILL-SPEC-014"
  devforgeai-target: "both"
  devforgeai-anatomy: "true"
```

Not produced by skill-creator (deferred to DevForgeAI's skill-generator): provider-native `.claude/agents/*.md` and `.codex/agents/*.toml` worker profiles, provider-specific frontmatter keys for the Claude target, and concise `AGENTS.md` sections. Hook definitions are not per-skill: `init` installs the one dispatcher and its provider fragments from `09-hook-dispatcher.md`, and this spec ships none.

A generated package is an uninstalled candidate until those provider-native controls are present and independently validated. Generation or quick-mode success is not installation authority.

## 13. Constraints

- `SKILL.md` under 500 lines and roughly 5,000 tokens, holding only identity, the ordered phase list, the dispatch loop, and the handoff table. Every other instruction lives in `references/<phase>.md`, `agents/<role>.md` or `assets/`. Splitting a phase's guidance into more reference files is the correct response to the line budget; cutting content is not.
- References one level deep: `SKILL.md` links to `references/`, `agents/` and `assets/`; an `agents/*.md` may link to `references/*.md`. Nothing links further.
- Hooks, state writes and phase advancement are not in the skill. Do not write an instruction the sequencer or a hook already enforces.
- No `README.md` inside the skill directory.
- No angle brackets in frontmatter. Description at most 1024 characters, name at most 64.
- Imperative voice. Explain why a step matters instead of shouting it; where an instruction is non-negotiable it is a gate, a fence or an oracle, and the text names that mechanism.
- Provide defaults, not menus. Procedures over declarations.
- The amended document keeps `architect`'s template and its `template_version`; `amend` owns only the `impact-report` template.
- No amend worker writes a path under `docs/plan/`, or under `.devforgeai/` other than the `adr` phase's one `.devforgeai/provenance/adr/NNNN-<slug>.md` inside the candidate root.

## 14. Acceptance checks

Run these before reporting done and paste their output:

```bash
# frontmatter and naming (skill-creator's own validator)
python -m scripts.quick_validate ./out/amend        # run from the skill-creator directory
# open-standard validator, if installed
skills-ref validate ./out/amend
# size budget
wc -l ./out/amend/SKILL.md                          # must be < 500
# every worker in section 7d has a prompt file, and no extra
ls ./out/amend/agents/                              # change_applier.md amend_adr_writer.md impact_analyzer.md resync_slicer.md
# one reference file per phase, plus envelope.md
ls ./out/amend/references/                          # apply_change.md adr.md impact.md resync.md envelope.md
# no leftover placeholders
grep -rnE 'T[O]DO|T[B]D|[{][{]' ./out/amend || echo clean
# spec battery (from the repository root)
python3 docs/design/specs/verify.py --only v1,v2,v4
```

For non-Research anatomy skills, DevForgeAI skill-validator additionally checks: all sub-phase kinds present with Gate, Record and Handoff bound to sequencer operations; `must_not` and a `writes` declaration of `candidate`, `evidence` or `none` present in every agent file, with no tool wider than that declaration allows; the SKILL.md Bash grammar is no wider than the model-callable operations; handoff outcomes cover every status the skill can return, including `could_not_run`.

## 15. Provenance

| Source | Hash | Used for |
|--------|------|----------|
| `docs/design/01-skill-anatomy.md#primary-window-contract` | sha256:de7d775e46bd44c52089a3998b114a5ebb5ce6875be3ebf3dca126f5a9bbaa32 | sections 2, 7a |
| `docs/design/01-skill-anatomy.md#context-bundle-format` | sha256:7b068feb30e7cc2f66292b512ac179cd217df225fb58517d2aaadd30b25236dc | sections 7d, 8, 9 |
| `docs/design/10-sequencer-and-contracts.md#4-per-skill-phase-registry` | sha256:7d655abc79fb1789e37a57227eecc279faf035a0359ffa76e93b24b56796498e | sections 7b, 7c |
| `docs/design/10-sequencer-and-contracts.md#5-worker-result` | sha256:cee716ddb3ae9b6b4405037ede3bb7c6445e0e6c8ac28382344a655d31754dcd | sections 6, 7c, 7d |
| `docs/design/10-sequencer-and-contracts.md#3-status-vocabulary-and-gate-policy` | sha256:36ffb340bd5d843cd945f7d17a590e335e491b11a60b08d4bf70e12a3a223620 | sections 7c, 7e, 9 |
| `docs/design/10-sequencer-and-contracts.md#6-handoff-envelope` | sha256:de637edceb588df104a40b57738eb263989f6603f90ece6f4d0e64fef07ffb6a | section 7e |
| `docs/design/11-artifact-registry.md#1-template-registry` | sha256:25886acb1c2963b15938f0c577c3bfd28b9807dd2dd961c59ff2b43fa00b62e2 | sections 6, 8 |
| `docs/design/11-artifact-registry.md#2-artifact-path-patterns` | sha256:2d2e97afff50edf6b35bf674b1de217c684d5091361e5f1deae12de52b95fb51 | sections 6, 9 |
| `docs/design/02-skill-roster.md#amend` | sha256:7d3fb6fd5626ff057c8ecc768d30ab052bdb90a9521ffab125245d279812caff | sections 1, 2, 7e |
| `docs/design/05-subagent-sets.md#sets-per-skill` | sha256:9e12f3beb236a025c18d40e741c09ba675bd71d2d87f56e2b205c7556b944bf9 | sections 7d, 9 |

Mirror of `depends_on` in the frontmatter, with the section each source fed.
