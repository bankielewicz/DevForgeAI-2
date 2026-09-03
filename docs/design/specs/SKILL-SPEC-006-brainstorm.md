---
template: skill-spec
template_version: 1
id: SKILL-SPEC-006
skill_name: brainstorm
target: both
status: approved
author: "DevForgeAI plan skill, wave 2 spec author"
date: 2026-09-02
depends_on:
  - source: docs/design/01-skill-anatomy.md#primary-window-contract
    hash: sha256:6556607035516c49ee43fe2bbeffe1a74e898889d84be00c9a05fdf751d209b6
    excerpt: "**The model dispatches, the sequencer decides.** For an anatomy-governed skill, the primary window (provider entry adapter + skill orchestration) does light, trivial work only."
  - source: docs/design/01-skill-anatomy.md#handoff-contract
    hash: sha256:dc50836dc15a928b0c4758ef3a671c6f78d5c7db7ea207c923b917d89faa9e96
    excerpt: "Every anatomy-governed skill run ends with a handoff. The sequencer writes `.devforgeai/work/<run>/handoff.json` at `phase next` and at `phase fail`; the block below is that file's rendering, and it is the only handoff the primary window prints."
  - source: docs/design/10-sequencer-and-contracts.md#4-per-skill-phase-registry
    hash: sha256:7c1d67f1154e49247e5dc178fcc1512bdbd53af378c360aeafe69bffed1136ab
    excerpt: "| brainstorm | 2 | `research_request` | `research_requester` | none | 2 | — | report_only | — |"
  - source: docs/design/10-sequencer-and-contracts.md#5-2-validation-order
    hash: sha256:9cf7115cdfa637023edc22cbdf5f64c106b1eba340598c8dc97b68361cb76b0f
    excerpt: "| 10 | `changed[]` is a subset of `claimed_paths` | refuse, reason `UNCLAIMED_CHANGE`; this **is** a phase attempt, because real bytes were written outside the claim |"
  - source: docs/design/10-sequencer-and-contracts.md#5-4-transition-oracles
    hash: sha256:076840ec9db03155bc9edcceb587e2aa1ca8bf3849e7a8b742f788d1a3b2315f
    excerpt: "the phase declared `writes: docs` and `changed[]` is non-empty, unless it is marked conditional, in which case an empty change set needs a non-empty `note`; every changed path exists in the root with the bytes the checkpoint will hold"
  - source: docs/design/11-artifact-registry.md#1-template-registry
    hash: sha256:fabb8d2f142dcde1a31bc53768f8a46d01cac3ea4a7f6b73db22479cc89b5553
    excerpt: "| `brainstorm` | `.devforgeai/skills/brainstorm/templates/brainstorm.md` | 1 | `^IDEA-[0-9]{3}$` | slug, template, template_version, status, provenance | Problem, Ideas, Clusters, Open Questions |"
  - source: docs/design/11-artifact-registry.md#4-upstream-and-downstream-per-skill
    hash: sha256:cfcaef76005176490e96b9e67c8fa4f0b7a6a2e13b6badf856468881fbe25200
    excerpt: "| brainstorm | init, onboard, pm | `observed-constraints`, `backlog-ideas`, sealed Research dossiers | `brainstorm` | pm |"
  - source: docs/design/02-skill-roster.md#brainstorm
    hash: sha256:528e8caae179b945781ade05601caaa2083cca8e66166058494207536ce0ff64
    excerpt: "Every idea gets an ID (`IDEA-NNN`) so PM can archive or promote by reference."
  - source: docs/design/02-skill-roster.md#handoff-decision-tables
    hash: sha256:1dac784b4670cc7559f323011dfe304dfe8c0baf349063162f90d76d902c5d3c
    excerpt: "| brainstorm | pass | `/pm {slug}` |"
  - source: docs/design/05-subagent-sets.md#sets-per-skill
    hash: sha256:f2957217c9af147e4a7ea03749cbe6efda266bd56d403f39aa25c9a655872609
    excerpt: "| brainstorm | idea-capturer, research-requester (prepares a complete request file, stops for the human's explicit digest-confirmed Research invocation, then consumes the sealed dossier), idea-clusterer, brainstorm-writer, critic |"
---

# Skill Specification: brainstorm

A stranger with no conversation history must be able to build this skill from this document alone. Every question the generator would otherwise ask is answered below. This document contains no unresolved authoring assumption; every decision the design documents left open is resolved in section 9 with the file and line that forced it.

## 0. Generator instructions

These instructions are addressed to the skill-generating agent (Anthropic's `skill-creator` skill, or DevForgeAI's `skill-generator`). They replace its interview.

### Cold-session prompt

Paste this into a fresh session from the repository root:

```
Use the skill-creator skill to build the skill specified in docs/design/specs/SKILL-SPEC-006-brainstorm.md.
Follow its section 0 exactly. Output directory: ./out. Eval mode: quick.
```

### Rules for the generator

1. **Do not interview.** Sections 1-13 pre-answer every Capture Intent and Interview question: what the skill enables, when it triggers, its output format, its test cases, its edge cases, its input and output formats, its example files, its success criteria, and its dependencies. Treat this document as the conversation history you are told to harvest from.
2. **Test prompts are pre-approved.** Use section 10 verbatim as `evals/evals.json`. Do not ask whether they look right.
3. **Trigger queries are pre-approved.** Use section 4 verbatim as the trigger eval set. Do not ask for sign-off.
4. **No human review loop.** Do not wait for the user to review results. Proceed to the next stage on your own.
5. **Eval mode** is given in the prompt and is one of two values:
   - `skip`: write the skill only. Do not create `evals/`, do not run test prompts, do not optimize the description.
   - `quick`: write the skill and `evals/evals.json`. For each eval copy `docs/design/examples/fixtures/brainstorm/` without `overlays/` to `./out/brainstorm-workspace/fixture-<eval-id>/`, copy `overlays/eval-<id>/` over it when one exists, run each test prompt once with the skill (no baseline run), grade with the grader agent, write `grading.json`, and report pass or fail per expectation in your final message. Do not run the description-optimization loop. Run the eval executions and the grader as foreground Agent-tool subagents, never as background shell processes, and do not end your turn until every `grading.json` exists: a headless session terminates when the top-level turn ends and orphans anything still running.
   - Any other mode name is a spec defect. The deferred interactive mode is `12-post-mvp.md#pm-06`.
6. **Output location** is given in the prompt. Create `./out/brainstorm/`. Do not write anywhere else except the `brainstorm-workspace/` sibling that eval runs require.
7. **On ambiguity, stop before output.** If this spec is still `draft`, contains an unresolved authoring assumption, omits a section, contradicts itself, or leaves a decision this document does not make, do not guess and do not write candidate skill files. End with a list titled `SPEC GAPS` naming each section and question. The spec author fixes and approves the spec before re-running.
8. **Fidelity over creativity.** Use the description in section 3 verbatim. Use each worker contract in section 7d verbatim as the body of `agents/<role>.md`, adding only the Role / Inputs / Process / Output framing the grader agent in skill-creator uses, where the Process text is that phase's reference file section from 7f. Do not add steps, tools, or behaviours this spec does not mention.
9. **Finish with the acceptance checks** in section 14 and include their output in your final message.

## 1. Identity

| Field | Value |
|-------|-------|
| name | `brainstorm` (kebab-case, 10 characters, equals the directory name, no provider prefix) |
| title | Idea Capture and Clustering |
| purpose | Turn an unstructured pile of ideas into one identified, clustered, question-bearing document that pm can gate on and archive from by reference. |
| category | devforgeai-phase |
| version | 1.0.0 (skill-package version written to `metadata.version`; not the DevForgeAI or Research Core version) |

## 2. Problem and requirements

**Without this skill:** ideas arrive as a chat transcript and leave as a summary. The summary silently merges two different ideas, drops the one nobody argued for, and invents a rationale nobody offered. Nothing has an identifier, so when pm later archives half of them there is no way to say which half, and when someone asks why an idea was dropped there is no row to point at. Claims that need outside evidence ("the competitor charges per seat", "that library is unmaintained") are written down as if they were established, and three phases later a requirement rests on a sentence no one can source. The document that results has no template, so the next skill's gate has nothing to check.

| ID | Kind | Requirement |
|----|------|-------------|
| R1 | explicit | Produce `docs/brainstorm/<slug>.md` with the sections `Problem`, `Ideas`, `Clusters` and `Open Questions` and the frontmatter keys the `brainstorm` template header names (`11-artifact-registry.md` section 1). |
| R2 | explicit | Give every idea its own `IDEA-NNN` id so pm can archive or promote by reference (`02-skill-roster.md#brainstorm`). |
| R3 | explicit | Prepare a complete Research request when an idea rests on a claim that needs sealed external evidence, and stop for the human's explicit digest-confirmed invocation; consume the sealed dossier on the next run (`05-subagent-sets.md#sets-per-skill`). |
| R4 | implicit | Each of the three document-writing phases edits `docs/brainstorm/<slug>.md` inside the run's candidate root and returns one `devforgeai.worker-result/v1` receipt claiming it; `research_request` and `critic` write nothing. The sequencer derives the real change set from the checkpoint diff, validates it against the claim, the fence and the `brainstorm` template header, checkpoints, and promotes the root at Handoff. |
| R5 | implicit | The primary window stays in the canonical checkout, reads `.devforgeai/state.yaml` and nothing else, dispatches by path plus the `devforgeai status` block, and prints the handoff the sequencer rendered (`01-skill-anatomy.md#primary-window-contract`). |
| R6 | implicit | A claim carried by an idea and not supported by a cited source is tagged `ASSUMPTION:` in the document, so plan's later gate can see it (`01-skill-anatomy.md`, persona rule). |
| R7 | discovered | The fence is exactly one path, `docs/brainstorm/<slug>.md`, and three phases declare `writes: docs`. Each therefore edits that same file in turn inside the candidate root, over the bytes the previous phase's checkpoint left. Resolved in section 9, row G-1. |
| R8 | discovered | The `research_request` phase and worker declare `writes: none`, so the worker changes nothing anywhere. It returns the complete request body in required `findings`; after receipt validation the sequencer persists it to `.devforgeai/work/<run>/evidence/research_requester/findings.md`. A `needs_user` note carries the invocation and persisted path. Resolved in section 9, row G-3. |
| R9 | discovered | Brownfield input is the OBSERVED constraint sections that exist plus current source citations; no OBSERVED architecture document is required (`02-skill-roster.md#brainstorm`). |

## 3. Description

```yaml
description: >
  Turn a raw pile of ideas into docs/brainstorm/SLUG.md, the one document pm gates on:
  capture every idea under its own IDEA-NNN id, cluster them, and record the open questions
  that block a decision. Use this skill whenever someone dumps ideas, options or a wish list
  for a feature or product and wants them written down before requirements exist, whenever a
  slug needs a brainstorm document before /pm can run, whenever archived backlog ideas are
  being revisited, and whenever an idea rests on a claim that needs sealed external evidence,
  so the research request is prepared and handed to a human. Do NOT use it to write
  requirements or an MVP split (that is pm), to design a solution (that is architect), or to
  run research itself (that is research, which a human invokes with a confirmed request
  digest).
```

Character count: 805 / 1024.

## 4. Trigger set

```json
[
  {"query": "/brainstorm inbox", "should_trigger": true},
  {"query": "here's my notes file with about a dozen half-formed ideas for the ledger rewrite, get them written down properly", "should_trigger": true},
  {"query": "we had a whiteboard session about the inbox feature. can you turn notes/ideas.md into something pm can actually work from", "should_trigger": true},
  {"query": "init says greenfield and the next step is brainstorming the slug. off you go", "should_trigger": true},
  {"query": "before we write any requirements I want every option we discussed listed with an id, grouped, and the unknowns called out", "should_trigger": true},
  {"query": "pull the archived ideas back out of backlog-ideas.md for the inbox slug, we want to look at them again", "should_trigger": true},
  {"query": "one of these ideas assumes the vendor api supports webhooks. flag what we would need to check before pm picks it up", "should_trigger": true},
  {"query": "capture these: per-seat pricing, usage pricing, a free tier, and an enterprise plan. group them and tell me what we dont know", "should_trigger": true},
  {"query": "we keep re-arguing the same four options in standup. write them down once with ids so we can stop", "should_trigger": true},
  {"query": "write the prd for the inbox feature", "should_trigger": false},
  {"query": "pick the best of these four options and justify it in an ADR", "should_trigger": false},
  {"query": "/research pricing --request req.json --confirm-request sha256:abc", "should_trigger": false},
  {"query": "split EPIC-003 into stories for sprint-002", "should_trigger": false},
  {"query": "summarise this meeting transcript into bullet points for the team channel", "should_trigger": false},
  {"query": "which of these two libraries is faster? benchmark them", "should_trigger": false},
  {"query": "the brainstorm doc is done, archive the ideas we are not doing", "should_trigger": false},
  {"query": "map this existing repository and record its build commands", "should_trigger": false},
  {"query": "sprint-001 is over, collect the lessons", "should_trigger": false}
]
```

## 5. Use cases

### UC-1: A notes file becomes the gated document
- **User says:** "/brainstorm inbox, the ideas are in notes/ideas.md"
- **Steps:** 1. The adapter calls `devforgeai phase start brainstorm inbox`. 2. `idea_capturer` reads `notes/ideas.md` and proposes `docs/brainstorm/inbox.md` with one `IDEA-NNN` per idea, a `Problem` section, a single default cluster and the questions the notes leave open. 3. `research_requester` finds no claim that needs sealed evidence and returns `pass`. 4. `idea_clusterer` replaces the `Clusters` section with themed groups, each naming its idea ids. 5. `brainstorm_writer` proposes the final full text, completing `Problem` and `Open Questions` and tagging every unsupported claim. 6. `brainstorm_critic` reports ideas that lost their id, clusters naming absent ids, or untagged claims.
- **Result:** one template-conformant `docs/brainstorm/inbox.md`; the handoff points at `/pm inbox`.

### UC-2: An idea rests on outside evidence
- **User says:** "capture these pricing options; one of them assumes the competitor charges per seat"
- **Steps:** 1. `idea_capturer` writes the document with the pricing ideas into the candidate root. 2. `research_requester` returns the complete request body in required `findings` with `status: needs_user`; the sequencer persists it at the fixed evidence path, and the note carries that path and exact invocation.
- **Result:** the run blocks with a `REQUIRE_HUMAN` handoff naming the persisted request body, and the human copies it to the request path, runs `/research`, and then resumes `/brainstorm inbox`, where `research_requester` finds the sealed dossier and returns `pass` with its references.

### UC-3: Revisiting archived ideas
- **User says:** "pull the archived inbox ideas back out, we want another look"
- **Steps:** 1. `idea_capturer` reads `docs/PM/inbox/backlog-ideas.md` and the existing `docs/brainstorm/inbox.md`, carries every existing `IDEA-NNN` forward unchanged, and adds the revived ones under fresh ids. 2. The remaining phases run unchanged.
- **Result:** one document holding both the previous ids and the revived ones, so pm's promotion log still resolves every id it recorded.

## 6. Inputs and outputs

### Inputs
| Input | Format | Example file | Required |
|-------|--------|--------------|----------|
| slug | string, the `devforgeai phase start` argument | supplied on the command line | yes |
| run file and context bundle | YAML and JSON written by the sequencer at `devforgeai phase start`: `phase`, `fence`, `granted_keys`, `attempts`, `max_attempts`, `lease`, `gate_policy`, plus the sliced context | `.devforgeai/work/<run>/run.yaml`, `.devforgeai/work/<run>/context.json` | yes |
| idea source | markdown or plain text at a path the user names | `docs/design/examples/fixtures/brainstorm/notes/ideas.md` | yes, unless the brainstorm document already exists |
| existing brainstorm document | markdown, `brainstorm` template | `docs/brainstorm/<slug>.md` | no |
| archived ideas | markdown, `backlog-ideas` template | `docs/PM/<slug>/backlog-ideas.md` | no |
| OBSERVED constraint sections | markdown, `observed-constraints` template | `docs/architecture/architecture.md` | no; brownfield only |
| sealed Research dossier | directory of typed records governed by `framework/skills/research/` | `docs/research/<slug>/runs/RUN-NNNNNN/` | no |

### Outputs
| Output | Format | Location | Template |
|--------|--------|----------|----------|
| brainstorm document | markdown with frontmatter | `docs/brainstorm/<slug>.md` | `brainstorm` (`.devforgeai/skills/brainstorm/templates/brainstorm.md`, seeded by `assets/brainstorm.md`) |
| research request body | the receipt's `note`, recorded by the sequencer into the phase result; never a file the worker writes | `.devforgeai/work/brainstorm-<slug>/research_request-result.json` | none |
| phase result and report | JSON and markdown, written by the sequencer | `.devforgeai/work/brainstorm-<slug>/<phase>-result.json`, `<phase>-report.md` | none |
| handoff | JSON, written by the sequencer; the printed block is its rendering | `.devforgeai/work/brainstorm-<slug>/handoff.json` | `handoff` |

`brainstorm` header keys, from `11-artifact-registry.md` section 1: `template: brainstorm`, `template_version: 1`, `accepts_versions: [1]`, `required_frontmatter: [slug, template, template_version, status, provenance]`, `required_sections: ["## Problem", "## Ideas", "## Clusters", "## Open Questions"]`, `id_pattern: "^IDEA-[0-9]{3}$"`, and the standard forbidden-text list recorded in that section.

### Output template

```markdown
---
slug: inbox
template: brainstorm
template_version: 1
status: draft
provenance:
  - source: notes/ideas.md
    hash: sha256:8f1c...
  - source: docs/PM/inbox/backlog-ideas.md#archived-ideas
    hash: sha256:2b70...
---

# Brainstorm: inbox

## Problem
One paragraph naming the problem the ideas below are answers to, in the words of
the source, with its citation.

## Ideas

### IDEA-001 Per-seat pricing
Charge per named user per month.
Source: notes/ideas.md#L4-L6

### IDEA-002 Usage pricing
Charge per processed message.
ASSUMPTION: message volume is measurable at the ingest boundary.
Source: notes/ideas.md#L8-L9

## Clusters

### Pricing model
IDEA-001, IDEA-002

## Open Questions
| Question | Blocks | Route |
|----------|--------|-------|
| Does the competitor charge per seat? | IDEA-001 | sealed research evidence |
| Is message volume measurable at ingest? | IDEA-002 | the idea's author |
```

### Return envelope (DevForgeAI-anatomy skills only)

One schema, both providers: `devforgeai.worker-result/v1`, normative in `schemas/devforgeai/v1/worker-result.schema.json`. A worker's final message is exactly this object, with no Markdown fence and no surrounding prose. A document writer has already edited the file inside the candidate root when it returns; the receipt claims what it wrote. `research_requester` and `brainstorm_critic` change nothing anywhere and claim nothing; each returns `findings`, which the sequencer persists to its fixed `.devforgeai/work/<run>/evidence/<agent>/findings.md` path. `findings` is **required** on a judge receipt whose status is `pass` or `fail`, **optional** on a judge's `needs_user` or `could_not_run` — where the judge may have nothing to report — and **forbidden** on a producer receipt, on every status; the 16384-UTF-8-byte bound is the same wherever it is present, and an oversize string refuses the receipt.

```yaml
schema: devforgeai.worker-result/v1
run: "brainstorm-inbox"
skill: "brainstorm"
phase: "capture"
agent: "idea_capturer"
status: pass | fail | needs_user | could_not_run
reason_code: runner_missing | timeout | network | hook_fault | provider_tool_refused | prerequisite_missing | checkpoint_fault   # required only when status is could_not_run
candidate: {id: "brainstorm-inbox", input_checkpoint: "base"}
claimed_paths: ["docs/brainstorm/inbox.md"]   # root-relative, at most 64; empty on any non-pass status
evidence_refs: ["docs/brainstorm/inbox.md"]   # at most 16
note: "11 ideas captured from notes/ideas.md; 2 carry ASSUMPTION tags"
issues: [{id, kind, text}]                    # at most 10
```

At `devforgeai ingest-result` the sequencer derives `changed[{path, blob_sha256, kind}]` from the checkpoint diff, refuses when `changed` is not a subset of `claimed_paths` (`UNCLAIMED_CHANGE`) or a path is outside the fence, validates the written file against the `brainstorm` template header, runs the transition oracle inside the root, writes `<phase>-result.json` with `changed` and the checkpoint ref, releases the lease and advances. `next` requires `status: fail` plus a registry `rewind_to`; no brainstorm phase declares one, so the key is never present. Unknown keys refuse the receipt.

`gate_policy` (`BLOCK`, `REQUIRE_HUMAN`, `WARN`, `OFF`) is a defect-to-action map declared in the consumed artifact, never a status returned here. A document run carries the fixed map `{unresolvable_source: BLOCK}`.

## 7. Procedure

### 7a. Steps (the body of `SKILL.md`)

1. Parse the slug and, when the user named an idea source, its path — why: the slug is the `devforgeai phase start` argument and names the run `brainstorm-<slug>`, and the source path is the only content the first worker can read.
2. Call `devforgeai phase start brainstorm <slug>`. It runs the document gate, opens the run's candidate root, writes the run file and `context.json`, and prints the first phase, its worker and the status block.
3. Run `devforgeai status` and paste its block into the dispatch. The block names `run`, `candidate.root`, `phase`, `fence` and `granted_keys` — why: a worker writes inside the candidate root and cannot resolve it from the canonical tree, and this block is the one thing the dispatch carries that is not a path or an id.
4. Dispatch the worker the sequencer named, in a fresh context window, with that block, the run id, the phase name, the fence path and the idea source path. Pass paths, ids and the status block only — why: content pasted here is duplicated into two windows, and the worker can open the path itself.
5. Read the returned receipt. On `pass`, continue at step 4 with the next phase the sequencer names. On `fail`, dispatch the same phase's worker again with the sequencer's problem rows, until the sequencer stops naming that phase.
6. On `needs_user`, stop dispatching and print the handoff — why: the sequencer blocks the run at that phase on the first ask, and `research_request` uses this status to hand a prepared request to the human who must confirm its digest. The run is not closed: it stays `active` with `run.yaml#blocked_at` naming the phase, and `/brainstorm {slug}` resumes it there once the human has acted.
7. On `could_not_run`, stop dispatching. The sequencer records the reason code and selects the repair route.
8. Print the handoff block the sequencer rendered, unchanged. When it reports the run `ready_to_promote` and the user asks for the promotion, call `devforgeai promote <run>` — why: promotion moves the candidate root's bytes into the canonical checkout under the lock, and a `REQUIRE_HUMAN` block is the only state in which the model may ask for it.

The primary window stays in the canonical checkout and never opens the idea source, the brainstorm document, a backlog file or a dossier record. Its Bash grammar is exactly `devforgeai status`, `devforgeai phase start <skill> <arg>`, `devforgeai phase fail --reason <text>`, `devforgeai validate` and `devforgeai promote <run>`.

### 7b. Sub-phases and workers

| # | Sub-phase | Performed by | Writes | Isolation |
|---|-----------|--------------|--------|-----------|
| 0 | Gate | sequencer: `devforgeai phase start brainstorm <slug>`, which also opens the candidate root | sequencer | n/a |
| 1 | Slice | sequencer: a step inside `phase start` that resolves the incoming artifact's hashed bundle into `.devforgeai/work/<run>/context.json`. No worker (section 9, row G-2) | sequencer | n/a |
| 2 | Work: `capture` | worker: `idea_capturer` | candidate | required |
| 3 | Work: `research_request` | worker: `research_requester` | none | required |
| 4 | Work: `cluster` | worker: `idea_clusterer` | candidate | required |
| 5 | Write: `write` | worker: `brainstorm_writer` | candidate | required |
| 6 | Review: `critic` | worker: `brainstorm_critic` | none | required |
| 7 | Record | sequencer: `devforgeai phase next` | sequencer | n/a |
| 8 | Handoff | sequencer: `devforgeai phase next`, which on the last passing transition marks the run `ready_to_promote` and renders the first block, a `REQUIRE_HUMAN` handoff naming `devforgeai promote <run>`; that command, run only after the user confirms in the session, renders the second | sequencer | n/a |

`idea_capturer` is the persona and `brainstorm_critic` is the critic: different files, different prompts, and the critic changes nothing. A persona reviewing its own output is the hallucination vector this separation removes. `research_requester` is a judge too: it decides which claims need sealed evidence and returns the request body in `findings`. A judge carries no write tool. After receipt validation, the sequencer persists its `findings` to the fixed `.devforgeai/work/<run>/evidence/<agent>/findings.md` path, which is gitignored, lies outside the candidate root, and is never promoted; `issues[]` stays the bounded summary the handoff carries. A judge's `claimed_paths` is empty on every status. `tools` names tools only: a Claude Code subagent's `tools:` frontmatter accepts tool names and MCP server patterns, never a command pattern, so the hook dispatcher is the only command-level bound. A judge's `Bash` runs `devforgeai status` and the dispatcher's read-only command set (`cat cmp cut diff echo grep head jq ls pwd rg sha256sum tail test tr wc`, plus read-only git subcommands inside the root) and nothing else; a producer's additionally runs `devforgeai run KEY` for its granted keys.

The `Isolation` column is the DevForgeAI worker-contract value compiled into the generated target profile, not Claude's `isolation` frontmatter field. The framework does not use Claude's worktree isolation or `EnterWorktree`: both fork from HEAD, and the run's phases build linearly on one candidate root instead.

### 7c. Evidence and gate table

`<run>` is `brainstorm-<slug>`. Attempt budget is 2 for every phase (`10-sequencer-and-contracts.md` section 4).

| phase | worker | deterministic gate check | gate_policy | evidence file | transition oracle |
|---|---|---|---|---|---|
| `capture` | `idea_capturer` | run gate: no run is already active, `brainstorm` is a known `kind: document` skill, the fence entry `docs/brainstorm/<slug>.md` is repository-relative, free of `..` and not sequencer-owned, and no active or `ready_to_promote` run holds that path (`FENCE_OVERLAP`). Ingest validation: `changed` derived from the checkpoint diff is a subset of `claimed_paths` (`UNCLAIMED_CHANGE` otherwise), the single changed path is that fence entry under `candidate.root`, the written file is validated against the `brainstorm` template header before checkpointing, and the whole root is rescanned against the stack policy with the checkpoint refused on any violation | document run map `{unresolvable_source: BLOCK}`; `test_runner_missing` is not consulted because this phase brokers no command key | `.devforgeai/work/<run>/capture-result.json`, `capture-report.md` | `document`: at least one file produced inside the fence and `docs/brainstorm/<slug>.md` on disk |
| `research_request` | `research_requester` | ingest validation: the phase and worker declare `writes: none`, so `claimed_paths` is empty and any candidate-root change refuses the receipt as `UNCLAIMED_CHANGE`; the worker carries no write tool and returns the complete request body in required `findings`, which the sequencer persists at its fixed path; `note` is at most 16 KiB | `{unresolvable_source: BLOCK}` | `.devforgeai/work/<run>/evidence/research_requester/findings.md`, `research_request-result.json`, `research_request-report.md` | `report_only`: no file outside the fence changed since the gate snapshot and the whole-tree package and import policy holds |
| `cluster` | `idea_clusterer` | ingest validation as `capture`, over the bytes `capture`'s checkpoint left in the root. The phase's `input_checkpoint` is `capture`, so an edit built from anything else shows in the diff as a change the receipt did not claim | `{unresolvable_source: BLOCK}` | `.devforgeai/work/<run>/cluster-result.json`, `cluster-report.md` | `document`: at least one file produced and the fence path on disk |
| `write` | `brainstorm_writer` | ingest validation as `cluster`, over the bytes `cluster`'s checkpoint left; `claimed_paths` holds at most 64 entries and no duplicate, `evidence_refs` at most 16, `issues` at most 10 | `{unresolvable_source: BLOCK}` | `.devforgeai/work/<run>/write-result.json`, `write-report.md` | `document`: at least one file produced and the fence path on disk |
| `critic` | `brainstorm_critic` | ingest validation: the phase and worker declare `writes: none`, so `claimed_paths` is empty and any candidate-root change refuses the receipt; the worker carries no write tool and returns required `findings`, which the sequencer persists at its fixed path; the phase grants no command key, so a brokered run is refused for want of the hook marker | `{unresolvable_source: BLOCK}` | `.devforgeai/work/<run>/evidence/brainstorm_critic/findings.md`, `critic-result.json`, `critic-report.md`, then `handoff.json` | `report_only`: as `research_request`. On pass this is the last phase: the run is marked `ready_to_promote` and a `REQUIRE_HUMAN` handoff is written whose one forward command is `devforgeai promote <run>`; the `pass` handoff is the second block, written by that command once the user asks for it |

Promotion is not part of the run's phases. The last passing `devforgeai phase next` marks the run `ready_to_promote` and writes a `REQUIRE_HUMAN` handoff whose one forward command is `devforgeai promote <run>`; the candidate root and its checkpoints stay on disk and no canonical byte moves. The compiled `SKILL.md` runs that command only after the user confirms in the session, and it is that command — never `phase next` — that merges the candidate root into the canonical checkout under `.devforgeai/lock`, refusing on `STALE_BASE` when canonical HEAD has moved past the run's pinned `base_ref`, on `DIRTY_TARGET` when a dirty canonical file is among the changed paths, and on `MERGE_CONFLICT` when the rebase cannot replay the run. A refusal moves no canonical byte and leaves the run `ready_to_promote` with its root intact, so the command can be run again once the named cause is settled. The second handoff block is written by a promotion that succeeded, and its `next` is the section 7e row for the run's outcome. Each refusal is a handoff row in section 7e.

Two limits this table does not overstate. Every `devforgeai phase start` defect is a refusal whatever a declared policy value says, and only `test_runner_missing` changes behaviour, at transition time (`10-sequencer-and-contracts.md` section 3.2). Pm opens a document run, and the document gate checks the fence: conformance of this document to the `brainstorm` template header, and re-resolution of its `provenance` digests, are not checked at `devforgeai phase start` today. The story gate does re-resolve every `provenance` and `context` entry and `commands.hash`, so a story that quotes this document is checked when dev enters; `scripts/check_brainstorm.py` is the same check for the document path, and today it runs as a human or continuous-integration step (section 9, row G-5).

### 7d. Worker contracts

Each block is the body of `agents/<role>.md` and compiles to one provider profile per target. `name` is the canonical registry worker name, which is what a hook receives as `agent_type`; the compiled filename carries the skill prefix so two skills' profiles cannot collide. `tools` are the Claude names; on Codex `apply_patch` stands in for `Edit` and `Write`. `model: inherit` keeps the worker on the session's model, which is what the terminal-only constraint leaves available. No brainstorm phase grants a stack command key, so no worker here is granted a `devforgeai run` key. Claude-only frontmatter — `hooks`, `memory`, `background`, `permissionMode`, and Claude's own `isolation` — is omitted from every profile.

```yaml
name: idea_capturer
description: Dispatch this worker at the capture phase to write the brainstorm document with one identified entry per idea in the named source.
skill: brainstorm
writes: candidate
model: inherit
tools: [Read, Grep, Glob, Bash, Edit, Write]
skills: []
compiled_to: [.claude/agents/brainstorm-idea_capturer.md, .codex/agents/brainstorm-idea_capturer.toml]
responsibility: Write `docs/brainstorm/<slug>.md` inside the candidate root with one identified entry per idea present in the named source, carrying every existing entry forward unchanged.
inputs:
  - the devforgeai status block pasted into the dispatch, which names run, candidate.root, phase, fence and granted_keys
  - .devforgeai/work/<run>/context.json, the bundle the sequencer sliced at phase start
  - the idea source path named in the dispatch, read under the candidate root
  - docs/brainstorm/<slug>.md inside the candidate root, when it exists, for the ids to carry forward
  - docs/PM/<slug>/backlog-ideas.md inside the candidate root, when it exists, for revived ids
  - assets/brainstorm.md (the template header and section order)
outputs:
  - docs/brainstorm/<slug>.md, written inside the candidate root and claimed
  - one IDEA entry per source idea, each with a Source line naming the path and line range it came from
  - an ASSUMPTION tag on its own line under every claim the source does not support
must_not:
  - merge two source ideas into one entry, or drop an idea the source states
  - reuse an IDEA id for a different idea, or renumber an existing one
  - state a rationale the source does not state
  - write outside the candidate root, or outside the run's fence inside it
tools_codex: [Read, Grep, Glob, Bash, apply_patch]
isolation: required
returns: devforgeai.worker-result/v1
body:
  job: Write the brainstorm document so every idea in the source has its own stable id and citation.
  inputs: The list above, read under the candidate root; nothing outside it is opened.
  rules: references/capture.md, the entry shape, and the must_not list.
  receipt: One devforgeai.worker-result/v1 object; on pass claimed_paths is exactly the fence path, on needs_user it is empty and the note names the globs searched.
```

```yaml
name: research_requester
description: Dispatch this worker at the research_request phase to judge which captured claims need sealed external evidence and hand the human one complete request.
skill: brainstorm
writes: none
model: inherit
tools: [Read, Grep, Glob, Bash]
skills: []
compiled_to: [.claude/agents/brainstorm-research_requester.md, .codex/agents/brainstorm-research_requester.toml]
responsibility: Report which captured claims need sealed external evidence and carry one complete research request body, or the sealed dossier references that already cover them.
inputs:
  - the devforgeai status block pasted into the dispatch
  - .devforgeai/work/<run>/context.json
  - .devforgeai/work/<run>/capture-result.json (by path)
  - docs/brainstorm/<slug>.md inside the candidate root
  - docs/research/<slug>/runs/ (sealed dossier directories, by path)
outputs:
  - findings: the complete request body; after receipt validation the sequencer persists it to .devforgeai/work/<run>/evidence/research_requester/findings.md
  - note: the exact invocation a human runs and the fixed persisted path, when a claim needs sealed evidence
  - issues: one row per claim already covered, naming its RUN, Source, Evidence and Claim ids and the sealed manifest digest
must_not:
  - invoke research, or treat an unconfirmed request as persistent evidence
  - cite a dossier by digest alone, without RUN, Source, Evidence and Claim ids
  - write any file, including a request file, or run any stack command key
tools_codex: [Read, Grep, Glob, Bash]
isolation: required
returns: devforgeai.worker-result/v1
body:
  job: Judge each captured claim as covered, needing sealed evidence, or answerable by a person.
  inputs: The list above, read under the candidate root.
  rules: references/research_request.md, the three claim states, and the must_not list.
  receipt: One devforgeai.worker-result/v1 object; claimed_paths is empty on every status, findings carries the request body, and a needs_user note carries the invocation and fixed persisted path in one ask.
```

```yaml
name: idea_clusterer
description: Dispatch this worker at the cluster phase to replace the document's Clusters section with themed groups naming the ids they contain.
skill: brainstorm
writes: candidate
model: inherit
tools: [Read, Grep, Glob, Bash, Edit, Write]
skills: []
compiled_to: [.claude/agents/brainstorm-idea_clusterer.md, .codex/agents/brainstorm-idea_clusterer.toml]
responsibility: Edit the document inside the candidate root so its `## Clusters` section holds themed groups, each naming the idea ids it contains and nothing else.
inputs:
  - the devforgeai status block pasted into the dispatch
  - .devforgeai/work/<run>/context.json
  - docs/brainstorm/<slug>.md inside the candidate root, as the capture checkpoint left it
  - .devforgeai/work/<run>/capture-result.json and research_request-result.json (by path)
outputs:
  - docs/brainstorm/<slug>.md, edited inside the candidate root and claimed
  - one cluster per theme, each listing its member ids, with every captured id in exactly one cluster
must_not:
  - add, remove, renumber or reword an idea entry
  - place an id in two clusters, or leave a captured id in none
  - name a cluster after a decision the document has not made
  - write outside the candidate root, or outside the run's fence inside it
tools_codex: [Read, Grep, Glob, Bash, apply_patch]
isolation: required
returns: devforgeai.worker-result/v1
body:
  job: Group the captured ideas by theme, changing nothing else in the document.
  inputs: The list above, read under the candidate root.
  rules: references/cluster.md, the exactly-one-cluster rule, and the must_not list.
  receipt: One devforgeai.worker-result/v1 object; claimed_paths is exactly the fence path, and the checkpoint diff touches only the Clusters section.
```

```yaml
name: brainstorm_writer
description: Dispatch this worker at the write phase to complete the document's frontmatter provenance, problem statement and open questions.
skill: brainstorm
writes: candidate
model: inherit
tools: [Read, Grep, Glob, Bash, Edit, Write]
skills: []
compiled_to: [.claude/agents/brainstorm-brainstorm_writer.md, .codex/agents/brainstorm-brainstorm_writer.toml]
responsibility: Complete the document inside the candidate root: frontmatter with resolved provenance, the problem statement, the captured ideas, the clusters and the open questions.
inputs:
  - the devforgeai status block pasted into the dispatch
  - .devforgeai/work/<run>/context.json
  - docs/brainstorm/<slug>.md inside the candidate root, as the cluster checkpoint left it
  - .devforgeai/work/<run>/capture-result.json, research_request-result.json and cluster-result.json (by path)
  - assets/brainstorm.md
outputs:
  - docs/brainstorm/<slug>.md, edited inside the candidate root and claimed
  - the Open Questions table, one row per question with the ids it blocks and its route
must_not:
  - introduce an idea, cluster or claim no prior phase recorded
  - leave a claim without either a source citation or an ASSUMPTION tag
  - record a provenance entry whose source path does not exist
  - write outside the candidate root, or outside the run's fence inside it
tools_codex: [Read, Grep, Glob, Bash, apply_patch]
isolation: required
returns: devforgeai.worker-result/v1
body:
  job: Finish the document so every claim carries a citation or a tag and the questions name what they block.
  inputs: The list above, read under the candidate root.
  rules: references/write.md, the four things completed here, and the must_not list.
  receipt: One devforgeai.worker-result/v1 object; claimed_paths is exactly the fence path.
```

```yaml
name: brainstorm_critic
description: Dispatch this worker at the critic phase to judge the finished document for missing ids, unresolvable citations, cluster gaps and untagged claims.
skill: brainstorm
writes: none
model: inherit
tools: [Read, Grep, Glob, Bash]
skills: []
compiled_to: [.claude/agents/brainstorm-brainstorm_critic.md, .codex/agents/brainstorm-brainstorm_critic.toml]
responsibility: Report every idea whose id or source citation is missing, every cluster naming an id the document does not contain, and every claim carrying neither a citation nor an ASSUMPTION tag.
inputs:
  - the devforgeai status block pasted into the dispatch
  - docs/brainstorm/<slug>.md inside the candidate root, as the write checkpoint left it
  - .devforgeai/work/<run>/capture-result.json, research_request-result.json, cluster-result.json and write-result.json (by path)
  - the source paths the document's provenance and idea entries cite
outputs:
  - findings: the full defect list; after receipt validation the sequencer persists it to .devforgeai/work/<run>/evidence/brainstorm_critic/findings.md
  - issues: one row per defect, naming the id and what is missing, bounded at ten
  - note: the counts of ideas, clusters, questions and citations examined
must_not:
  - repair, reword or renumber anything it reports
  - pass an idea whose source citation names a path that does not exist
  - write any file, or run any stack command key
tools_codex: [Read, Grep, Glob, Bash]
isolation: required
returns: devforgeai.worker-result/v1
body:
  job: Judge the finished document against identity, citation, cluster membership, claims and questions.
  inputs: The list above, read under the candidate root; nothing is opened outside it.
  rules: references/critic.md, the five properties, and the must_not list.
  receipt: One devforgeai.worker-result/v1 object; claimed_paths is empty on every status, findings carries the complete defect list for sequencer persistence, and each defect is also one bounded issues row.
```

### 7e. Handoff outcomes

The `handoff.outcomes` block this skill declares, corrected to the closed status set.

| Outcome | Next steps |
|---------|------------|
| pass, all five phases, run `ready_to_promote`, nothing promoted (`REQUIRE_HUMAN`) | 1. `devforgeai promote {run}` |
| `devforgeai promote {run}` succeeded after all five phases passed | 1. `/pm {slug}` |
| `needs_user` from `research_request` (a claim needs sealed evidence) | 1. `/research {slug} --request {request-file} --confirm-request {sha256}`, using the body the sequencer recorded into `research_request-result.json` from the receipt's note; 2. `/brainstorm {slug}` |
| `needs_user` from `capture` (no idea source path and no existing document) | 1. save the ideas to a file in the repository; 2. `/brainstorm {slug}` naming that path |
| `needs_user` from any other writing phase (the document cannot be completed without a human answer) | 1. answer the open questions in `docs/brainstorm/{slug}.md`; 2. `/brainstorm {slug}`, which resumes the blocked run at `blocked_at` with attempts reset |
| `fail` at the attempt limit, any phase, including a critic that reports defects twice | 1. fix what the handoff names, then `/brainstorm {slug}` — the run is blocked, not closed: it stays `active` with its root and checkpoints on disk and `run.yaml#blocked_at` naming the phase, and this same command resumes it there with attempts reset. `devforgeai phase fail --reason <text>` is what abandons it instead |
| `could_not_run` with any reason code | 1. the repair named by the reason code; 2. `/brainstorm {slug}` |
| `devforgeai promote {run}` refused `STALE_BASE` in worktree mode | 1. `devforgeai promote {run}` again; that command rebases the candidate root onto the new canonical HEAD, reruns the last transition oracle and retries the fast-forward itself before it reports, so this row is reached only when the retry also failed |
| `devforgeai promote {run}` refused `STALE_BASE` in copy mode, or `MERGE_CONFLICT` after an aborted rebase | 1. reconcile `docs/brainstorm/{slug}.md` by hand, then `devforgeai promote {run}` — the refusal moved no canonical byte, and the run stays `ready_to_promote` with its root intact |
| `devforgeai promote {run}` refused `DIRTY_TARGET` | 1. commit or discard the dirty canonical file the refusal names, then `devforgeai promote {run}` |
| `phase start` refused `FENCE_OVERLAP` | 1. finish or abandon the run the refusal names, then `/brainstorm {slug}` |

The current sequencer selects the printed `next` itself from the fixed table in `10-sequencer-and-contracts.md` section 6: `devforgeai promote <run>` for the first block of a completed run, `/status` for the block that promotion writes and for a blocked `REQUIRE_HUMAN` document run, and the repair route for a `COULD_NOT_RUN` row. The rows above are the declared intent that `skill.yaml` carries; where the two differ today, what is printed is the sequencer's (section 9, row G-6).

### 7f. Phase guidance (becomes `references/<phase>.md`)

One file per registry phase, named for the phase exactly. Each is loaded when its phase's worker is dispatched.

#### `references/capture.md`

This phase owes `docs/brainstorm/<slug>.md` inside the candidate root. It is the file every later phase in this run edits, so its shape is the shape the run keeps: frontmatter with `slug`, `template`, `template_version`, `status` and `provenance`, then `## Problem`, `## Ideas`, `## Clusters` and `## Open Questions`, in that order.

One idea, one entry, one id. `### IDEA-NNN Short name`, numbered from `IDEA-001` within the file, followed by the idea in the source's own terms and a `Source:` line naming the path and line range it came from. Two ideas that share a theme are two entries; merging them here destroys the id pm archives by, and the theme is what the `cluster` phase is for. An idea the source states weakly is still an idea: capture it and let the questions carry the doubt.

Carrying forward. When the document already exists in the candidate root, read it in this dispatch, keep every existing entry and its id verbatim, and continue numbering above the highest present id. Ids are how pm's promotion log resolves; renumbering silently rewrites history, and the checkpoint diff records the rewrite as a real change the receipt then has to claim.

Reviving archived ideas. When `docs/PM/<slug>/backlog-ideas.md` exists and the dispatch names it, an archived idea returns under a fresh id with a `Source:` line naming the backlog entry, so the promotion log can show that it came back rather than appearing twice.

The `## Clusters` section at this phase holds one group, `Uncategorised`, naming every captured id. That keeps the section present for the template and leaves the clustering to the phase that owns it.

`## Open Questions` at this phase holds the questions the source itself leaves open, as rows of question, blocked ids, and route. The route is either a person who can answer it or sealed research evidence; the next phase reads that column.

A claim inside an idea that the source does not support carries an `ASSUMPTION:` tag on its own line. Plan's gate later refuses a story with an `ASSUMPTION:` outside its Clarifications section, so tagging here is what lets the claim travel visibly instead of hardening into a fact.

Brownfield input. When OBSERVED constraint sections exist, an idea that contradicts one is captured with a `Source:` line naming the OBSERVED entry it conflicts with. No OBSERVED architecture document is required, and its absence is not a defect.

#### `references/research_request.md`

This phase judges and changes nothing anywhere. Return the complete research request body in required `findings`; after validation the sequencer persists it to `.devforgeai/work/<run>/evidence/research_requester/findings.md`. A candidate-root change refuses the receipt as `UNCLAIMED_CHANGE`.

Read the open-questions rows whose route is sealed research evidence, and the claims tagged `ASSUMPTION:` in the captured document. For each, decide which of three states it is in:

- **Already covered.** A sealed dossier under `docs/research/<slug>/runs/RUN-NNNNNN/` carries a claim answering it. Record the RUN with its Source, Evidence and Claim ids and the sealed manifest digest as one `issues` row. A digest alone is not a provenance reference and does not count as coverage.
- **Needs sealed evidence.** No dossier covers it. Put one complete request body — the questions, scope and requested acceptance — in `findings`, and return `status: needs_user` with empty `claimed_paths` and a note carrying the fixed persisted findings path and exact invocation: `/research <slug> --request <request-file> --confirm-request <sha256>` on Claude, or the `$research` form on Codex. The sequencer persists the validated body; the human copies it to the chosen request path and confirms its normalized digest. Persistence in Research Core requires that human confirmation; nothing here can supply it.
- **Answerable without research.** The route is a person, not evidence. Leave it in the questions table and return `pass`.

When every claim is covered or answerable, return `pass` with the coverage rows and no request. A `needs_user` closes the run, so raise it once, with every claim that needs evidence in the same request, rather than one claim at a time.

#### `references/cluster.md`

This phase owes the document with `## Clusters` replaced, edited where it sits in the candidate root. Read the current bytes in this dispatch: the `capture` phase's checkpoint is already in the root, and an edit built from anything else shows in the diff as a change nothing claimed.

A cluster is a theme, named after what its members have in common, listing member ids and nothing else. Every captured id appears in exactly one cluster: an id in two clusters makes the count ambiguous for pm's partition, and an id in none is an idea that silently leaves the document. When an idea genuinely stands alone, it is a cluster of one; naming it so is more honest than a bucket named for the leftovers.

Cluster names describe, they do not decide. `Pricing model` is a theme; `Chosen pricing model` is a decision this document has not made and pm has not been given yet.

Change nothing else. Idea entries, their ids, their source lines, the problem statement and the questions table pass through byte for byte; the critic phase compares them.

#### `references/write.md`

This phase owes the finished document, edited where it sits in the candidate root over the bytes the `cluster` checkpoint left.

Four things get completed here:

1. **Frontmatter provenance.** One entry per source the document actually cites: the idea source path, any backlog file, any OBSERVED section, and any sealed dossier reference recorded by `research_request`. Each carries the source and its digest computed with the hash rule in `01-skill-anatomy.md`. A provenance entry whose path does not exist is a defect the critic reports and pm's gate is meant to refuse.
2. **The problem statement.** One paragraph in the source's own terms, with its citation. The problem is what the ideas are answers to; inventing a grander one changes what pm will scope.
3. **The ideas and clusters.** Carried through unchanged from the prior phases.
4. **The open questions.** Every row from `capture`, plus one row per claim `research_request` recorded as needing evidence, with its route. A question that the sealed dossier now answers is closed by replacing its route with the dossier reference, not by deleting the row.

Every claim in the document ends with either a source citation or an `ASSUMPTION:` tag. That is the property the critic checks and the property pm depends on: an untagged, uncited claim is indistinguishable from a fact.

Set `status: draft` in the frontmatter. The document becomes pm's input as it stands; nothing in this run marks it approved.

#### `references/critic.md`

This phase judges and changes nothing anywhere. Return the full defect list in required `findings`; after validation the sequencer persists it to `.devforgeai/work/<run>/evidence/brainstorm_critic/findings.md`.

Report each defect as one `issues` row, naming the id and what is missing:

1. **Identity.** Every idea entry has an id matching the template's pattern, no id appears twice, and no id a prior phase's report records is absent from the document.
2. **Citation.** Every idea has a `Source:` line whose path exists; every provenance entry names a path that exists. Digest re-computation belongs to `scripts/check_brainstorm.py`, which no worker's tool grammar admits; report a citation as unresolvable only when the path or anchor is absent.
3. **Cluster membership.** Every cluster member id exists in the document, and every captured id belongs to exactly one cluster.
4. **Claims.** Every claim carries a citation or an `ASSUMPTION:` tag.
5. **Questions.** Every open question names at least one idea id it blocks and a route.

Report and stop. Repair belongs to the phase that owns the section, and a critic that edits what it reviews removes the independent check this phase exists to provide. At the attempt limit the sequencer writes a `REQUIRE_HUMAN` handoff carrying the rows.

#### `references/envelope.md`

The `devforgeai.worker-result/v1` receipt, its field bounds, and one worked example per status. Loaded for every dispatch. Content: the field table from `10-sequencer-and-contracts.md` section 5.1; the caps (64 `claimed_paths`, 16 `evidence_refs`, 16 KiB note, 10 issues); the rule that the final message is exactly the object, with no Markdown fence and no surrounding prose; the rule that `claimed_paths` is empty on any status other than `pass`; the rule that `next` needs both `status: fail` and a registry `rewind_to`, which no brainstorm phase declares; the rule that an unknown key refuses the receipt; and the rule that `reason_code` is present exactly when the status is `could_not_run`.

## 8. Bundled resources

### Layout (fixed)

```
brainstorm/SKILL.md         # at most 500 lines: identity, phase list, dispatch loop, handoff table
  references/capture.md
  references/research_request.md
  references/cluster.md
  references/write.md
  references/critic.md
  references/envelope.md
  agents/idea_capturer.md
  agents/research_requester.md
  agents/idea_clusterer.md
  agents/brainstorm_writer.md
  agents/brainstorm_critic.md
  scripts/check_brainstorm.py
  assets/brainstorm.md
```

Link depth: `SKILL.md` links to `references/`, `agents/`, `scripts/` and `assets/`; an `agents/*.md` links to `references/*.md`; nothing links further. No `README.md` inside the skill directory.

### scripts/
| File | Purpose | Invocation | Exit codes |
|------|---------|------------|------------|
| `check_brainstorm.py` | Deterministic conformance check for a brainstorm document: frontmatter keys against the `brainstorm` template header, the four required sections in order, the `IDEA-NNN` id pattern, no duplicate id, every cluster member id present, every captured id in exactly one cluster, every `Source:` path resolvable, every `provenance` digest recomputed with the hash rule in `01-skill-anatomy.md`, the standard forbidden-text list, and every claim line carrying a citation or an `ASSUMPTION:` tag | `python scripts/check_brainstorm.py docs/brainstorm/inbox.md [--json] [--strict]` | 0 conformant, 1 defects listed on stdout, 2 usage |

The script prints JSON to stdout and diagnostics to stderr, documents `--help`, and never prompts. It is the library form of the template-conformance and provenance-conformance checks that `01-skill-anatomy.md` puts at pm's gate; the implemented document gate checks the fence only, so today the script runs as a human or continuous-integration check. No worker and no primary window runs it: their tool grammars do not admit it.

### references/
| File | Content | Load when |
|------|---------|-----------|
| `capture.md` | entry shape, id rules, carrying forward, reviving archived ideas, assumption tagging, brownfield input | dispatching `idea_capturer` |
| `research_request.md` | the three claim states, what a complete request body carries, where the sequencer persists it, and why confirming its digest stays the human's | dispatching `research_requester` |
| `cluster.md` | what a cluster is, the exactly-one-cluster rule, what passes through unchanged | dispatching `idea_clusterer` |
| `write.md` | the four things completed here, provenance resolution, the citation-or-tag rule | dispatching `brainstorm_writer` |
| `critic.md` | the five properties checked and why repair belongs elsewhere | dispatching `brainstorm_critic` |
| `envelope.md` | the `devforgeai.worker-result/v1` schema and bounds | every dispatch |

### assets/
| File | Used for |
|------|----------|
| `brainstorm.md` | the document skeleton every writing phase fills: the header block, the frontmatter keys, the four section headings in order, and one empty `IDEA-NNN` entry showing the entry shape |

### agents/
| File | Worker (from section 7d) |
|------|-------------------------|
| `idea_capturer.md` | `idea_capturer` |
| `research_requester.md` | `research_requester` |
| `idea_clusterer.md` | `idea_clusterer` |
| `brainstorm_writer.md` | `brainstorm_writer` |
| `brainstorm_critic.md` | `brainstorm_critic` |

## 9. Gotchas and edge cases

| Situation | What goes wrong | What to do instead |
|-----------|-----------------|--------------------|
| G-1: three `writes: docs` phases and a one-path fence | The `document` oracle fails a `writes: docs` phase that changed no file, so all three must edit the same path in turn; the phases build linearly on one candidate root, so each sees exactly what the previous checkpoint left | Each writing phase reads the current bytes in its own dispatch and edits the file in place: `capture` creates it, `cluster` replaces one section, `write` completes it. The reference files state exactly what each phase may change, the checkpoint diff shows what it did change, and the critic compares the parts that were meant to pass through |
| G-2: Slice has no phase | `01-skill-anatomy.md` and `05-subagent-sets.md` give Slice to a framework worker, but no registry phase dispatches one, and receipt validation binds the stop event's `agent_type` to the active phase's worker | Slice is a sequencer step inside `devforgeai phase start`: it resolves the incoming artifact's already-hashed bundle and writes `.devforgeai/work/<run>/context.json`, which every worker of the run is handed by path. This spec promises no slice phase and ships no slice agent file |
| G-3: where the research request lives | `05-subagent-sets.md` says `research_requester` prepares a request body, but the run fence holds only the brainstorm document | The judge changes nothing and returns the body in required `findings`; after validation the sequencer persists it to `.devforgeai/work/<run>/evidence/research_requester/findings.md`, a gitignored run-scoped path outside the candidate root that is never promoted. The note carries that path and the invocation. The human copies the file where Research wants it and confirms its digest; Research persistence requires that confirmation. |
| G-4: the user typed the ideas instead of naming a file | A dispatch carrying a dozen pasted ideas is an inline prompt longer than a dispatch instruction, which skill-validator rejects (`01-skill-anatomy.md`, Enforcement), and a worker in a fresh window cannot see the conversation | The dispatch names a path and nothing else. When no idea source path and no existing brainstorm document exist, `capture` returns `status: needs_user` with a note naming what it looked for, and the handoff asks for the ideas to be saved to a file and the command re-run. That keeps the ideas in a citable source, which is also what every `Source:` line depends on |
| G-5: template conformance at pm's gate | `01-skill-anatomy.md` describes the gate validating the incoming artifact against its template; `document_gate` in `examples/hooks/devforgeai.py` checks the fence only, so pm's run gate does not read this document | The story gate re-resolves every `provenance` and `context` entry and `commands.hash`, with a placeholder digest reported as `unresolvable-source` under `gate_policy`; the document gate does not. This document is therefore checked when a story quotes it, and `scripts/check_brainstorm.py` is the deterministic form a human or continuous-integration step runs meanwhile. `AUTHOR-BRIEF.md` section 12 supersedes its own OI-2 row on this point |
| G-6: the declared handoff table and the printed `next` | `01-skill-anatomy.md` says the sequencer selects a row from the skill's `handoff.outcomes`; `examples/hooks/devforgeai.py` selects `next` from the fixed table in `10-sequencer-and-contracts.md` section 6 | Section 7e is the declared intent carried in `skill.yaml`; a completed or `REQUIRE_HUMAN` document run currently prints `/status`. Read the handoff for what a given run printed |
| G-7: `--continue` after a `needs_user` | `02-skill-roster.md` offers `/brainstorm {slug} --continue`, and an earlier draft here said `needs_user` closes the run and abandons its candidate root | `needs_user` blocks the run rather than closing it: it stays `active` with its root and checkpoints on disk and `run.yaml#blocked_at` naming the phase, and plain `devforgeai phase start brainstorm {slug}` resumes it there with `attempts` reset. `--continue` is therefore unnecessary and is not implemented. Where a run really is closed — `devforgeai phase fail --reason <text>` abandoned it — the next `phase start` opens a new candidate root from the current canonical HEAD, over a document that already holds whatever an earlier run promoted; `capture` carries the ideas forward and `research_request` finds the now-sealed dossier |
| G-8: an idea that contradicts an OBSERVED constraint | An author may drop the idea or silently soften it | Capture it with a `Source:` line naming the OBSERVED entry it conflicts with. OBSERVED material is advisory until architect marks a section INTENDED, and pm decides what to do with the conflict |
| G-9: two ideas that are really one | Merging them at capture destroys the id pm archives by; keeping duplicates inflates the count | Capture both, then let `cluster` place them in one cluster. The clusters carry the relationship; the ids carry the identity |
| G-10: an idea arrives with no problem statement anywhere | The writer invents a problem, and pm scopes to the invention | `write` states the problem in the source's own terms with its citation. When the source states none, the problem paragraph carries an `ASSUMPTION:` tag and an open-questions row routed to the requester |
| G-11: the slug names no existing document and the user names no source | `capture` has nothing to read and would write an empty document, which the `document` oracle accepts and pm's gate cannot use | `capture` writes nothing and returns `status: needs_user` with empty `claimed_paths` and a note naming what it looked for. A document with no ideas is not a brainstorm; asking once is cheaper than three phases of nothing |
| G-12: the receipt no longer carries an `evidence` object | Earlier drafts gave each phase `evidence.ideas`, `evidence.assumptions`, `evidence.clusters`, `evidence.questions` and `evidence.checked`. The receipt schema in the write-model revision removes `evidence` and adds `claimed_paths`, `evidence_refs` and the bounded judge-only `findings` string | Every producer row already has a home in the document the phase wrote: ids and Source lines in `## Ideas`, tags on their own lines, membership in `## Clusters`, and routes in `## Open Questions`. Producer `evidence_refs` points at that file, `note` carries counts, and `issues` carries what could not be written. The two judges return their complete reports in `findings`; after validation, the sequencer persists each string to `.devforgeai/work/<run>/evidence/<agent>/findings.md`. Nothing a later phase reads is lost. |
| G-13: the primary window and the candidate root | A worker cannot resolve `candidate.root` from the canonical tree, and pasting artifact content into a dispatch is the restatement the anti-ceremony rules forbid | The one thing the dispatch carries beyond paths and ids is the `devforgeai status` block, which names `run`, `candidate.root`, `phase`, `fence` and `granted_keys`. It is generated, not composed, and it is the only sanctioned paste |
| G-14: an earlier draft said promotion is the last thing the run does and that `devforgeai phase next` merges the candidate root | An author compiles a `SKILL.md` that never asks the user, and the run's files land in the canonical checkout without a human decision | Promotion is never automatic. The last passing transition sets `runs.<run>.status: ready_to_promote` and writes a `REQUIRE_HUMAN` handoff whose only forward step is `devforgeai promote <run>`; the compiled `SKILL.md` runs that command only after the user confirms in the session, and that command writes the second handoff block, whose `next` is the section 7e row for the run's outcome. Every run ends in two blocks, not one, and `STALE_BASE`, `DIRTY_TARGET` and `MERGE_CONFLICT` are refusals of `devforgeai promote <run>` that leave the run `ready_to_promote` with its root intact, never refusals of `devforgeai phase next`. **Decision (D7, as amended; `10-sequencer-and-contracts.md` sections 5.4, 6 and 12.4):** the sequencer may not close a run onto the canonical tree on its own. |
| G-15: An earlier draft said a `REQUIRE_HUMAN` block closes the run, so "no flag resumes a closed one" | An author writes a repair route that opens a fresh run, and `devforgeai phase start` refuses it — the blocked run is still `active` — or writes `devforgeai phase fail --reason <text>` into every recovery row and throws away work the run had already checkpointed | A block is not a close. A `needs_user` result and an exhausted attempt budget both leave the run `active` with its lease released, its candidate root and checkpoints on disk, and `run.yaml#blocked_at` naming the phase. `devforgeai phase start` with the same skill and the same argument **resumes** that run at `blocked_at` with `attempts` reset to zero instead of refusing it, so `/brainstorm {slug}` is the whole recovery once the human has acted. Only another skill on the same story needs `devforgeai phase fail --reason <text>` first, and that call is what abandons the root. **Decision (`10-sequencer-and-contracts.md` sections 2, 3, 5.4 and 6):** blocked runs resume; they are not reopened. |
| G-16: an earlier draft gave `research_requester` and `brainstorm_critic` a `Write` fenced to their own run-scoped evidence directories | Claude Code 2.1.259 was observed refusing a subagent's write of a report-shaped Markdown file before any hook ran, with an undocumented heuristic that may not be relied on in either direction, so a judge that must write a findings file cannot finish its phase | Each judge declares `writes: none` and carries no `Write`, `Edit` or `apply_patch`. It returns its complete bounded report in the receipt's `findings` string — required on `pass` or `fail`, optional on `needs_user` or `could_not_run`, at most 16,384 UTF-8 bytes, refused rather than truncated — and the sequencer writes that string verbatim to `.devforgeai/work/<run>/evidence/<agent>/findings.md` at the identity-bound `SubagentStop` once the receipt validates. The worker chooses neither the path nor the name, does not name it in its own `evidence_refs`, and has no workaround through `findings.json`, `notes.txt` or a shell redirect. A tool call the provider refuses before any hook runs is `could_not_run` with `reason_code: provider_tool_refused`; `hook_fault` stays reserved for a missing worker identity or a malformed receipt, and a failed worktree prerequisite is `prerequisite_missing`. The bounded `findings` body does enter the primary window as part of the subagent's result, exactly as any subagent result does; what stays isolated is the worker's transcript, its file reads, its tool traffic and its intermediate reasoning. **Decision (D13):** judges write nothing; the sequencer persists what they return. |

## 10. Success criteria and test cases

### Success criteria

- Triggers on the section 4 positives and on none of the near-misses.
- Every idea in the source appears exactly once in the document under its own id, and no id changes between phases; measured by `scripts/check_brainstorm.py` exiting 0.
- Every captured id belongs to exactly one cluster, and every cluster member id exists.
- Every claim carries either a source citation or an `ASSUMPTION:` tag.
- Every phase's `changed` set is a subset of its `claimed_paths` and holds no path but `docs/brainstorm/<slug>.md`, and the `research_request` and `critic` phases change nothing inside the candidate root.
- Every run ends with a handoff whose next step is exactly one command.

### Fixtures

Base fixture, `docs/design/examples/fixtures/brainstorm/`, a repository with an idea list and nothing else:

| Path | Content |
|---|---|
| `notes/ideas.md` | Twenty lines under `# inbox ideas`: nine dash-prefixed ideas in casual phrasing — per-seat pricing, usage pricing, a free tier, an enterprise plan, a shared team inbox, per-user rules, a mobile digest, a webhook integration, and an import from the old tool; one of them ("the competitor charges per seat, we should match it") states an external claim, and one ("usage pricing, assuming we can count messages at ingest") states an internal one; the last two lines are two open questions the author wrote as questions |
| `.devforgeai/state.yaml` | canonical state: `version: 1`, `target: [claude]`, `mode: greenfield`, `slug: inbox`, `phase: brainstorm`, an empty `stories` mapping, and a `runs` mapping with one key `brainstorm-inbox` whose value carries `skill: brainstorm`, `mode: copy`, `root: .`, `base_ref: fixture`, `checkpoint: base` and `status: active` |
| `.devforgeai/work/brainstorm-inbox/run.yaml` | the per-run enforcement file, standing in for what `devforgeai phase start` writes: `canonical: .`, `phase: capture`, `fence: [docs/brainstorm/inbox.md]`, `test_paths: []`, `granted_keys: []`, `attempts` and `max_attempts` at 2 for the five phases, `gate_policy: {unresolvable_source: BLOCK}`, and a `lease` naming the eval session |

The sequencer is not installed in an eval copy, so the run file stands in for `devforgeai phase start` and the fixture root stands in for the candidate root: `candidate.mode` is `copy` and `candidate.root` is the fixture copy itself, so a worker's writes land where the eval can see them. Per-run enforcement lives in `run.yaml`, not in `state.yaml`, because nothing inside a candidate root reads canonical state. Expectations are checked against the receipt in the transcript and against files on disk. No eval gates on sequencer behaviour; quick-mode results are generation feedback only (`12-post-mvp.md#pm-02`).

Overlays, copied over the base fixture for the eval whose id they name:

| Overlay | Files |
|---|---|
| `overlays/eval-2/.devforgeai/work/brainstorm-inbox/run.yaml` | the base run file with `phase` set to `research_request` |
| `overlays/eval-2/docs/brainstorm/inbox.md` | the document as `capture` leaves it: frontmatter with `slug: inbox`, `template: brainstorm`, `template_version: 1`, `status: draft` and one provenance entry for `notes/ideas.md`; `## Problem` with one paragraph; `## Ideas` with `IDEA-001` to `IDEA-009`, each carrying a `Source:` line into `notes/ideas.md`, `IDEA-001` carrying the competitor claim and `IDEA-002` carrying an `ASSUMPTION:` line about counting messages at ingest; `## Clusters` with the single group `Uncategorised` naming all nine ids; `## Open Questions` with the two author questions, the first routed to sealed research evidence |
| `overlays/eval-2/.devforgeai/work/brainstorm-inbox/capture-result.json` | the recorded `capture` result, with `claimed_paths` naming the document, a `changed` row for it, and a note recording nine ids of which `IDEA-002` carries a tag |
| `overlays/eval-3/.devforgeai/work/brainstorm-inbox/run.yaml` | the base run file with `phase` set to `cluster` |
| `overlays/eval-3/docs/brainstorm/inbox.md` | the same captured document as eval 2 |
| `overlays/eval-3/.devforgeai/work/brainstorm-inbox/capture-result.json` | as eval 2 |
| `overlays/eval-3/.devforgeai/work/brainstorm-inbox/research_request-result.json` | a `research_request` result with `status: pass`, empty `claimed_paths`, and a note recording that the competitor claim is routed to a human and no dossier covers it |

### evals/evals.json (used verbatim)

```json
{
  "skill_name": "brainstorm",
  "evals": [
    {
      "id": 1,
      "prompt": "Brainstorm the inbox slug from notes/ideas.md. The DevForgeAI sequencer is not installed in this copy; the run file at .devforgeai/work/brainstorm-inbox/run.yaml is already open at phase capture and this working copy is the candidate root. Dispatch that phase's worker and show me the receipt it returns.",
      "expected_output": "An idea_capturer receipt claiming docs/brainstorm/inbox.md, which now holds nine IDEA entries, each with a Source line into notes/ideas.md, a single Uncategorised cluster naming all nine ids, an ASSUMPTION tag on the ingest-counting claim, and the two author questions in the Open Questions table.",
      "files": [],
      "expectations": [
        "The idea_capturer receipt's claimed_paths is exactly [docs/brainstorm/inbox.md] and that file exists in the working copy afterwards",
        "The written file contains nine entries with ids matching IDEA-001 through IDEA-009 and no duplicate id",
        "Every idea entry in the written file has a Source line naming notes/ideas.md with a line range",
        "The written file has the four sections Problem, Ideas, Clusters and Open Questions in that order",
        "The Clusters section names a single group containing all nine ids",
        "The claim about counting messages at ingest carries an ASSUMPTION tag",
        "The receipt's evidence_refs names docs/brainstorm/inbox.md and its note records nine ideas and names the idea carrying the tag"
      ]
    },
    {
      "id": 2,
      "prompt": "Continue the inbox brainstorm. The sequencer is not installed; the run file is open at phase research_request and this working copy is the candidate root. Dispatch that phase's worker and show me the receipt it returns.",
      "expected_output": "A research_requester receipt with status needs_user, empty claimed_paths, findings carrying one complete request body covering the competitor pricing claim, and a note carrying the research invocation with --request and --confirm-request plus the fixed persisted path.",
      "files": [],
      "expectations": [
        "The research_requester receipt has status needs_user and an empty claimed_paths list",
        "The receipt's note carries a request body naming the competitor pricing claim",
        "The receipt's note contains a research invocation with both --request and --confirm-request",
        "No file in the working copy is created or modified by this phase",
        "The receipt does not claim the competitor pricing question is already answered"
      ]
    },
    {
      "id": 3,
      "prompt": "Continue the inbox brainstorm. The sequencer is not installed; the run file is open at phase cluster and this working copy is the candidate root. Dispatch that phase's worker and show me the receipt it returns.",
      "expected_output": "An idea_clusterer receipt claiming docs/brainstorm/inbox.md, whose Clusters section is now themed groups covering all nine ids exactly once, with every idea entry, id and Source line unchanged.",
      "files": [],
      "expectations": [
        "The idea_clusterer receipt's claimed_paths is exactly [docs/brainstorm/inbox.md]",
        "Every one of the nine ids appears in exactly one cluster in the written file",
        "The written Clusters section names at least two groups and no group is named Uncategorised",
        "The idea entries, their ids and their Source lines are byte-identical to the fixture document",
        "No file in the working copy other than docs/brainstorm/inbox.md differs from the fixture",
        "The receipt's note lists each cluster with its member ids"
      ]
    }
  ]
}
```

## 11. Dependencies and compatibility

| Kind | Value |
|------|-------|
| Tools | `SKILL.md`: `Read`, `Agent`, and a Bash grammar no wider than the five model-callable operations `devforgeai status \| phase start <skill> <arg> \| phase fail --reason \| validate \| promote <run>`. Document writers (`idea_capturer`, `idea_clusterer`, `brainstorm_writer`): `Read`, `Grep`, `Glob`, `Bash`, plus `Edit` and `Write`, which Codex serves as `apply_patch`; every write is denied outside `candidate.root` and outside the phase's fence. Judges (`research_requester`, `brainstorm_critic`): `Read`, `Grep`, `Glob`, `Bash` and no write tool; they return required `findings` for sequencer persistence. No brainstorm phase grants a stack command key, so no worker is granted a `devforgeai run` key |
| MCP servers | none |
| Runtime | Python 3.11+ for `scripts/check_brainstorm.py`, which imports `PyYAML` and the standard library only. Worktree mode additionally requires `git` with at least one commit on the project; without it the run falls back to copy mode |
| Project commands | none. Every brainstorm phase declares an empty run-key set, so no `stack.yaml` key is brokered during this skill's run; a document run carries `commands: {}` (`10-sequencer-and-contracts.md` section 9) |
| DevForgeAI/Core compatibility | `NOT_APPLICABLE`; `brainstorm` is an anatomy-governed skill, not a Research Core adapter. It cites sealed dossiers by id and never writes under `docs/research/` |
| Other skills | Upstream: `init`, `onboard`, `pm`. Downstream: `pm` gates on the document this skill produces. Brainstorm invokes no other skill: the research edge and the pm edge are handoff rows a human or a fresh session runs |

Deferred dependencies, named and not gated on:

| Entry | What brainstorm does today without it |
|---|---|
| `12-post-mvp.md#pm-01` | Isolation is a declaration compiled into the target profile; nothing verifies it at run time. `isolation: required` is the DevForgeAI contract value, not Claude's `isolation` frontmatter field |
| `12-post-mvp.md#pm-04` | A worker's write boundary is the dispatcher's `PreToolUse` deny plus the candidate root, not an operating-system boundary |
| `12-post-mvp.md#pm-02` | Quick-mode eval results are generation feedback only. No section of this spec gates on them |
| `12-post-mvp.md#pm-06` | Eval mode is `skip` or `quick`; the interactive mode is not named as available |
| `12-post-mvp.md#pm-10` | Nothing re-checks an applied brainstorm document from a clean checkout. `scripts/check_brainstorm.py` runs as a human or continuous-integration step |

Frontmatter values derived from this table:

```yaml
compatibility: "Runs in the Claude Code or Codex terminal inside a repository that has .devforgeai/state.yaml. Requires Python 3.11+ and PyYAML for the bundled check script."
allowed-tools: "Read Agent Bash(devforgeai status) Bash(devforgeai phase start *) Bash(devforgeai phase fail *) Bash(devforgeai validate) Bash(devforgeai promote *)"
```

## 12. Targets

The generator produces one provider-neutral semantic package and a separate adapter for each selected target when frontmatter, invocation policy, or agent configuration differs. Provider-neutral resources may be shared. Adapter directories are not required to be byte-identical or symlinked.

| Target | Install path | Invocation | Subagents | Notes |
|--------|--------------|------------|-----------|-------|
| claude | `.claude/skills/brainstorm/` | `/brainstorm` with the slug as its argument | `.claude/agents/brainstorm-<role>.md`: three document writers with `Edit` and `Write` confined to the candidate root, and two judges with no write tool whose reports travel in `findings` | Provider-specific frontmatter keys are compiled into this target's `SKILL.md` only. `hooks`, `memory`, `background`, `permissionMode` and Claude's own `isolation` are omitted from every profile |
| codex | `.agents/skills/brainstorm/` plus `.codex/agents/` profiles | `$brainstorm` with the slug as its argument | `.codex/agents/brainstorm-<role>.toml`: the same five names, with `apply_patch` in place of `Edit` and `Write` | Portable six-field frontmatter only; policy goes in target-side configuration |
| both | separate `.claude/skills/brainstorm/` and `.agents/skills/brainstorm/` adapters | as above | as above | Share only provider-neutral resources; validate each adapter independently |

```yaml
metadata:
  version: "1.0.0"
  devforgeai-spec: "SKILL-SPEC-006"
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
- From this skill's own subject matter: one idea is one entry with one stable id; a cluster describes and does not decide; a claim carries a citation or an assumption tag; research persistence is the human's confirmed invocation, never this skill's.

## 14. Acceptance checks

Run these before reporting done and paste their output:

```bash
# frontmatter and naming (skill-creator's own validator)
python -m scripts.quick_validate ./out/brainstorm       # run from the skill-creator directory
# open-standard validator, if installed
skills-ref validate ./out/brainstorm
# size budget
wc -l ./out/brainstorm/SKILL.md                         # must be under 500
# every worker in section 7d has a prompt file, and no extra
ls ./out/brainstorm/agents/                             # idea_capturer research_requester idea_clusterer brainstorm_writer brainstorm_critic
# one reference file per registry phase, plus envelope.md
ls ./out/brainstorm/references/                         # capture research_request cluster write critic envelope
# the bundled check script runs and reports usage cleanly
python ./out/brainstorm/scripts/check_brainstorm.py --help
# no leftover placeholders
grep -rnE 'T[O]DO|T[B]D|\{\{' ./out/brainstorm || echo clean
# the spec battery
python3 docs/design/specs/verify.py --only v1,v2,v4
```

For non-Research anatomy skills, DevForgeAI skill-validator additionally checks: all sub-phase kinds present with Gate, Record and Handoff bound to sequencer operations; persona and critic are different files; `must_not` present in every agent file; every agent declaring `writes: candidate` or `writes: none`, with a judge carrying no write tool and returning required `findings`, and a producer carrying only the read set plus its required edit tools; the `SKILL.md` Bash grammar no wider than the five model-callable operations; and handoff outcomes covering every status the skill can return, including `could_not_run`.

## 15. Provenance

| Source | Hash | Used for |
|--------|------|----------|
| docs/design/01-skill-anatomy.md#primary-window-contract | see frontmatter | sections 2 (R5), 7a, 13 |
| docs/design/01-skill-anatomy.md#handoff-contract | see frontmatter | sections 7e, 9 (G-6) |
| docs/design/10-sequencer-and-contracts.md#4-per-skill-phase-registry | see frontmatter | sections 7b, 7c, 9 |
| docs/design/10-sequencer-and-contracts.md#5-2-validation-order | see frontmatter | sections 7c, 9 (G-1) |
| docs/design/10-sequencer-and-contracts.md#5-4-transition-oracles | see frontmatter | sections 7c, 9 (G-1) |
| docs/design/11-artifact-registry.md#1-template-registry | see frontmatter | sections 6, 8 |
| docs/design/11-artifact-registry.md#4-upstream-and-downstream-per-skill | see frontmatter | sections 6, 11 |
| docs/design/02-skill-roster.md#brainstorm | see frontmatter | sections 2 (R2, R9), 7f |
| docs/design/02-skill-roster.md#handoff-decision-tables | see frontmatter | section 7e |
| docs/design/05-subagent-sets.md#sets-per-skill | see frontmatter | sections 7d, 8, 9 (G-3) |
