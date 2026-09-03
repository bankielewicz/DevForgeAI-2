---
template: skill-spec
template_version: 1
id: SKILL-SPEC-007
skill_name: pm
target: both
status: approved
author: "DevForgeAI plan skill, wave 2 spec author"
date: 2026-09-02
depends_on:
  - source: docs/design/01-skill-anatomy.md#primary-window-contract
    hash: sha256:a6bbaf9af2d69f7ede18d7c40f242c42edb26d79be964ffec3f386d6347014c2
    excerpt: "**The model dispatches, the sequencer decides.** For an anatomy-governed skill, the primary window (provider entry adapter + skill orchestration) does light, trivial work only."
  - source: docs/design/01-skill-anatomy.md#gate-validating-the-incoming-artifact
    hash: sha256:01d7f4e0e09db70d8d4869ab22646d7cea27959c936571db4850b11df4000dc8
    excerpt: "Review (sub-phase 4) checks what a skill *produces*. Gate (sub-phase 0) checks what a skill *consumes*."
  - source: docs/design/10-sequencer-and-contracts.md#4-per-skill-phase-registry
    hash: sha256:511733ee35ca74fd5a5c0b59f225d7d975788e7d43d939f44c23b7aa8460cff0
    excerpt: "| pm | 1 | `scope_split` | `scope_splitter` | docs | 2 | — | document | — |"
  - source: docs/design/10-sequencer-and-contracts.md#5-2-validation-order
    hash: sha256:9f1bf77b7e84302ff6f3f20260228d57390cc97ab8e8d3f68f52c3ff2658aab8
    excerpt: "| 10 | `changed[]` is a subset of `claimed_paths` | refuse, reason `UNCLAIMED_CHANGE`; this **is** a phase attempt, because real bytes were written outside the claim |"
  - source: docs/design/10-sequencer-and-contracts.md#5-4-transition-oracles
    hash: sha256:ffa41b5d270dc260e28fa9f6bdbc855069a6e922d1148c74b25860dba63484dc
    excerpt: "the phase declared `writes: docs` and `changed[]` is non-empty, unless it is marked conditional, in which case an empty change set needs a non-empty `note`; every changed path exists in the root with the bytes the checkpoint will hold"
  - source: docs/design/10-sequencer-and-contracts.md#6-handoff-envelope
    hash: sha256:747b6340fc5c2348aad33ca5488012808670b3503b311d7b7d0f1204625afd4c
    excerpt: "| document run, promoted, no verdict or `verdict: pass` | `/status` |"
  - source: docs/design/11-artifact-registry.md#1-template-registry
    hash: sha256:fabb8d2f142dcde1a31bc53768f8a46d01cac3ea4a7f6b73db22479cc89b5553
    excerpt: "| `prd` | `.devforgeai/skills/pm/templates/prd.md` | 1 | `^REQ-[0-9]{3}$` | slug, template, template_version, status, scope, provenance, depends_on | Goal, Users, Requirements, Non-Goals, Success Measures |"
  - source: docs/design/11-artifact-registry.md#3-depends-on-edges
    hash: sha256:f3c304ff840d2027432f743288bccec0ea5bc5d7b99b7f41c8d524b1c3591da2
    excerpt: "| `prd` | `docs/brainstorm/<slug>.md` sections; admitted `observed-constraints` |"
  - source: docs/design/02-skill-roster.md#pm
    hash: sha256:f240ecaaa3d6c628cfbca7a45ec47fdec70bcbb15d343068d7717e1520fbd0ef
    excerpt: "Scope-splitter subagent produces the MVP/archive partition with a one-line justification per idea."
  - source: docs/design/02-skill-roster.md#handoff-decision-tables
    hash: sha256:1dac784b4670cc7559f323011dfe304dfe8c0baf349063162f90d76d902c5d3c
    excerpt: "| pm | pass | `/architect {slug}` |"
  - source: docs/design/05-subagent-sets.md#sets-per-skill
    hash: sha256:9e12f3beb236a025c18d40e741c09ba675bd71d2d87f56e2b205c7556b944bf9
    excerpt: "| pm | scope-splitter, prd-writer, backlog-archiver, critic |"
---

# Skill Specification: pm

A stranger with no conversation history must be able to build this skill from this document alone. Every question the generator would otherwise ask is answered below. This document contains no unresolved authoring assumption; every decision the design documents left open is resolved in section 9 with the file and line that forced it.

## 0. Generator instructions

These instructions are addressed to the skill-generating agent (Anthropic's `skill-creator` skill, or DevForgeAI's `skill-generator`). They replace its interview.

### Cold-session prompt

Paste this into a fresh session from the repository root:

```
Use the skill-creator skill to build the skill specified in docs/design/specs/SKILL-SPEC-007-pm.md.
Follow its section 0 exactly. Output directory: ./out. Eval mode: quick.
```

### Rules for the generator

1. **Do not interview.** Sections 1-13 pre-answer every Capture Intent and Interview question: what the skill enables, when it triggers, its output format, its test cases, its edge cases, its input and output formats, its example files, its success criteria, and its dependencies. Treat this document as the conversation history you are told to harvest from.
2. **Test prompts are pre-approved.** Use section 10 verbatim as `evals/evals.json`. Do not ask whether they look right.
3. **Trigger queries are pre-approved.** Use section 4 verbatim as the trigger eval set. Do not ask for sign-off.
4. **No human review loop.** Do not wait for the user to review results. Proceed to the next stage on your own.
5. **Eval mode** is given in the prompt and is one of two values:
   - `skip`: write the skill only. Do not create `evals/`, do not run test prompts, do not optimize the description.
   - `quick`: write the skill and `evals/evals.json`. For each eval copy `docs/design/examples/fixtures/pm/` without `overlays/` to `./out/pm-workspace/fixture-<eval-id>/`, copy `overlays/eval-<id>/` over it when one exists, run each test prompt once with the skill (no baseline run), grade with the grader agent, write `grading.json`, and report pass or fail per expectation in your final message. Do not run the description-optimization loop. Run the eval executions and the grader as foreground Agent-tool subagents, never as background shell processes, and do not end your turn until every `grading.json` exists: a headless session terminates when the top-level turn ends and orphans anything still running.
   - Any other mode name is a spec defect. The deferred interactive mode is `12-post-mvp.md#pm-06`.
6. **Output location** is given in the prompt. Create `./out/pm/`. Do not write anywhere else except the `pm-workspace/` sibling that eval runs require.
7. **On ambiguity, stop before output.** If this spec is still `draft`, contains an unresolved authoring assumption, omits a section, contradicts itself, or leaves a decision this document does not make, do not guess and do not write candidate skill files. End with a list titled `SPEC GAPS` naming each section and question. The spec author fixes and approves the spec before re-running.
8. **Fidelity over creativity.** Use the description in section 3 verbatim. Use each worker contract in section 7d verbatim as the body of `agents/<role>.md`, adding only the Role / Inputs / Process / Output framing the grader agent in skill-creator uses, where the Process text is that phase's reference file section from 7f. Do not add steps, tools, or behaviours this spec does not mention.
9. **Finish with the acceptance checks** in section 14 and include their output in your final message.

## 1. Identity

| Field | Value |
|-------|-------|
| name | `pm` (kebab-case, 2 characters, equals the directory name, no provider prefix) |
| title | Scope Split and Requirements |
| purpose | Split captured ideas into a scoped, numbered PRD and an archived backlog with a reason per idea, so every later phase plans from requirements that trace back to an idea id. |
| category | devforgeai-phase |
| version | 1.0.0 (skill-package version written to `metadata.version`; not the DevForgeAI or Research Core version) |

## 2. Problem and requirements

**Without this skill:** the scope boundary is drawn in conversation and never written down. Requirements appear as prose paragraphs with no identifiers, so a story cannot cite one and `analyze` cannot tell a requirement with no story from a story with no requirement. Ideas that were consciously excluded vanish instead of being archived, so the same argument returns next month with no record of why it was settled. The PRD absorbs claims the brainstorm marked as unsupported, and an assumption becomes a requirement without anyone deciding to promote it. Success is stated as adjectives, so QA has nothing to measure and the project cannot tell when it is done.

| ID | Kind | Requirement |
|----|------|-------------|
| R1 | explicit | Produce `docs/PM/<slug>/prd.md` with the sections `Goal`, `Users`, `Requirements`, `Non-Goals` and `Success Measures` and the frontmatter keys the `prd` template header names (`11-artifact-registry.md` section 1). |
| R2 | explicit | Produce `docs/PM/<slug>/backlog-ideas.md` with `Archived Ideas` and `Promotion Log`, holding every excluded idea by its `IDEA-NNN` id with a one-line justification (`02-skill-roster.md#pm`). |
| R3 | explicit | Number every requirement `REQ-NNN` so epics, stories and `analyze` can cite it (`11-artifact-registry.md` section 1, `id_pattern`). |
| R4 | explicit | Support two scopes: an MVP PRD for a greenfield slug, and a feature PRD scoped to one slug on an existing product (`02-skill-roster.md#pm`). |
| R5 | implicit | Each of the three document-writing phases writes its fenced file inside the run's candidate root and returns one `devforgeai.worker-result/v1` receipt claiming it; the critic changes nothing inside it, writing only its findings file into its own run-scoped evidence directory. The sequencer derives the real change set from the checkpoint diff, validates it against the claim, the fence and the template header, checkpoints, and promotes the root at Handoff. |
| R6 | implicit | The primary window stays in the canonical checkout, reads `.devforgeai/state.yaml` and nothing else, dispatches by path plus the `devforgeai status` block, and prints the handoff the sequencer rendered (`01-skill-anatomy.md#primary-window-contract`). |
| R7 | implicit | `depends_on` records the brainstorm sections and any admitted OBSERVED constraints the PRD was sliced from, each with an anchor and a digest (`11-artifact-registry.md` section 3). |
| R8 | discovered | Three phases write; the fence holds two paths. `scope_split` and `backlog` both own `backlog-ideas.md`, so the second edits the file over the bytes the first phase's checkpoint left in the candidate root. Resolved in section 9, row G-1. |
| R9 | discovered | An `ASSUMPTION:` tag carried by an idea does not vanish when the idea becomes a requirement: it travels into the PRD, because plan's story gate refuses an unresolved assumption outside a Clarifications section (`10-sequencer-and-contracts.md` section 3.2). |

## 3. Description

```yaml
description: >
  Turn a brainstorm document into the two files the rest of DevForgeAI plans from:
  docs/PM/SLUG/prd.md with numbered REQ-NNN requirements, users, non-goals and success
  measures, and docs/PM/SLUG/backlog-ideas.md holding every idea the scope excludes with a
  one-line reason and a promotion log. Use this skill whenever ideas have been captured and
  someone asks what is in scope, what the MVP is, what we are actually building first, or
  wants requirements written before architecture starts; use it in feature mode on an
  existing product when one slug needs its own scoped PRD. Do NOT use it to collect or
  cluster ideas (that is brainstorm), to choose a technology or write mandates (that is
  architect), or to write epics, stories or sprints (that is plan).
```

Character count: 753 / 1024.

## 4. Trigger set

```json
[
  {"query": "/pm inbox", "should_trigger": true},
  {"query": "the brainstorm doc for inbox is done. what's actually in the first release and what are we parking?", "should_trigger": true},
  {"query": "write the requirements for the inbox slug from docs/brainstorm/inbox.md, numbered so stories can cite them", "should_trigger": true},
  {"query": "we need an MVP boundary before architect starts. draw it and say why for each idea we drop", "should_trigger": true},
  {"query": "this is an existing product and inbox is just one feature. scope a prd for that feature only", "should_trigger": true},
  {"query": "turn the clustered ideas into a prd with users, non-goals and something QA can measure", "should_trigger": true},
  {"query": "half these ideas are v2. archive them with a reason so we stop re-arguing", "should_trigger": true},
  {"query": "what does done look like for the inbox work? write it down properly before we plan", "should_trigger": true},
  {"query": "we promoted two ideas back off the backlog for inbox, redo the prd", "should_trigger": true},
  {"query": "capture these five ideas i just thought of for the inbox feature", "should_trigger": false},
  {"query": "break the prd into epics and stories for sprint-001", "should_trigger": false},
  {"query": "pick postgres or sqlite for this and write an ADR", "should_trigger": false},
  {"query": "check whether every requirement has a story yet", "should_trigger": false},
  {"query": "the qa report says criterion 2 failed, fix it", "should_trigger": false},
  {"query": "write a product update email for the customers about the inbox launch", "should_trigger": false},
  {"query": "estimate how long the inbox work will take", "should_trigger": false},
  {"query": "map this existing repository before we plan anything", "should_trigger": false},
  {"query": "the constitution changed, re-slice the stories that quoted it", "should_trigger": false}
]
```

## 5. Use cases

### UC-1: MVP split for a greenfield slug
- **User says:** "/pm inbox"
- **Steps:** 1. The adapter calls `devforgeai phase start pm inbox`. 2. `scope_splitter` reads `docs/brainstorm/inbox.md` and proposes `docs/PM/inbox/backlog-ideas.md` with every idea partitioned into promoted and archived, one line of justification each. 3. `prd_writer` proposes `docs/PM/inbox/prd.md` with one `REQ-NNN` per promoted idea, users, non-goals drawn from the archived half, and measurable success rows. 4. `backlog_archiver` rewrites the backlog file so its promotion log names the `REQ-NNN` each promoted idea became. 5. `pm_critic` reports requirements citing no idea, ideas in neither half, and success measures with nothing to measure.
- **Result:** two template-conformant files; every idea id resolves to a requirement or to an archive row; the handoff points at `/architect inbox`.

### UC-2: Feature scope on an existing product
- **User says:** "this is an existing product and inbox is one feature. scope a prd for that feature only"
- **Steps:** 1. The adapter passes the slug and the feature scope. 2. `scope_splitter` partitions against the feature boundary rather than a first release, and records the boundary it used. 3. The remaining phases run unchanged, with `scope: feature` in the PRD frontmatter and admitted OBSERVED constraints cited in `depends_on`.
- **Result:** a PRD whose scope key says `feature`, so `analyze` can later flag reduced-provenance work.

### UC-3: The boundary is not decidable from the document
- **User says:** "/pm inbox"
- **Steps:** 1. `scope_splitter` finds that the brainstorm's open questions leave two mutually exclusive ideas both unresolved, and that no answer exists in the document, the backlog or an admitted OBSERVED constraint. 2. It returns `status: needs_user` with the question and the ids it blocks.
- **Result:** no partition is invented, the run closes with a `REQUIRE_HUMAN` handoff, and the human answers in the brainstorm document before a fresh `/pm inbox`.

## 6. Inputs and outputs

### Inputs
| Input | Format | Example file | Required |
|-------|--------|--------------|----------|
| slug | string, the `devforgeai phase start` argument | supplied on the command line | yes |
| run file and context bundle | YAML and JSON written by the sequencer at `devforgeai phase start`: `phase`, `fence`, `granted_keys`, `attempts`, `max_attempts`, `lease`, `gate_policy`, plus the sliced context | `.devforgeai/work/<run>/run.yaml`, `.devforgeai/work/<run>/context.json` | yes |
| brainstorm document | markdown, `brainstorm` template | `docs/design/examples/fixtures/pm/docs/brainstorm/inbox.md` | yes |
| scope | `mvp` or `feature`, named in the dispatch | supplied on the command line | no; `mvp` is the default |
| existing backlog | markdown, `backlog-ideas` template | `docs/PM/<slug>/backlog-ideas.md` | no |
| existing PRD | markdown, `prd` template | `docs/PM/<slug>/prd.md` | no |
| OBSERVED constraint sections | markdown, `observed-constraints` template | `docs/architecture/architecture.md` | no; brownfield only |

### Outputs
| Output | Format | Location | Template |
|--------|--------|----------|----------|
| product requirements | markdown with frontmatter | `docs/PM/<slug>/prd.md` | `prd` (`.devforgeai/skills/pm/templates/prd.md`, seeded by `assets/prd.md`) |
| archived ideas and promotion log | markdown with frontmatter | `docs/PM/<slug>/backlog-ideas.md` | `backlog-ideas` (`.devforgeai/skills/pm/templates/backlog-ideas.md`, seeded by `assets/backlog-ideas.md`) |
| phase result and report | JSON and markdown, written by the sequencer | `.devforgeai/work/pm-<slug>/<phase>-result.json`, `<phase>-report.md` | none |
| handoff | JSON, written by the sequencer; the printed block is its rendering | `.devforgeai/work/pm-<slug>/handoff.json` | `handoff` |

Header keys, from `11-artifact-registry.md` section 1. `prd`: `template: prd`, `template_version: 1`, `accepts_versions: [1]`, `required_frontmatter: [slug, template, template_version, status, scope, provenance, depends_on]`, `required_sections: ["## Goal", "## Users", "## Requirements", "## Non-Goals", "## Success Measures"]`, `id_pattern: "^REQ-[0-9]{3}$"`. `backlog-ideas`: `template: backlog-ideas`, `template_version: 1`, `accepts_versions: [1]`, `required_frontmatter: [slug, template, template_version, status]`, `required_sections: ["## Archived Ideas", "## Promotion Log"]`, `id_pattern: "^IDEA-[0-9]{3}$"`. Both carry the standard forbidden-text list recorded in that section.

### Output template

`docs/PM/<slug>/prd.md`:

```markdown
---
slug: inbox
template: prd
template_version: 1
status: draft
scope: mvp
provenance:
  - source: docs/brainstorm/inbox.md#ideas
    hash: sha256:6d21...
depends_on:
  - source: docs/brainstorm/inbox.md#clusters
    hash: sha256:0ab4...
  - source: docs/architecture/architecture.md#observed
    hash: sha256:77c9...
---

# PRD: inbox

## Goal
One paragraph naming the outcome this scope delivers, in the terms the brainstorm
states the problem.

## Users
| User | What they need | Source |
|------|----------------|--------|
| team member | one place for shared mail | docs/brainstorm/inbox.md#idea-005 |

## Requirements

### REQ-001 Shared team inbox
Members of a team see the same message list.
Ideas: IDEA-005
Acceptance: a message delivered to the team address appears for every member.

### REQ-002 Usage-based pricing
Charge per processed message.
Ideas: IDEA-002
ASSUMPTION: message volume is measurable at the ingest boundary.
Acceptance: an invoice line equals the counted message total for the period.

## Non-Goals
| Not doing | Ideas | Why |
|-----------|-------|-----|
| enterprise plan | IDEA-004 | no named customer requires it in this scope |

## Success Measures
| Measure | How it is observed |
|---------|--------------------|
| every team member sees the same list | one delivered message is visible to all members of a two-member team |
```

`docs/PM/<slug>/backlog-ideas.md`:

```markdown
---
slug: inbox
template: backlog-ideas
template_version: 1
status: active
---

# Backlog: inbox

## Archived Ideas
| Idea | Title | Why it is out of this scope |
|------|-------|-----------------------------|
| IDEA-004 | enterprise plan | no named customer requires it in this scope |

## Promotion Log
| Idea | Outcome | Requirement | Date |
|------|---------|-------------|------|
| IDEA-005 | promoted | REQ-001 | 2026-09-02 |
| IDEA-004 | archived | none | 2026-09-02 |
```

### Return envelope (DevForgeAI-anatomy skills only)

One schema, both providers: `devforgeai.worker-result/v1`, normative in `schemas/devforgeai/v1/worker-result.schema.json`. A worker's final message is exactly this object, with no Markdown fence and no surrounding prose. A document writer has already written its file inside the candidate root when it returns; the receipt claims what it wrote. `pm_critic` changes nothing inside the candidate root and claims nothing; it writes its findings file into `.devforgeai/work/<run>/evidence/pm_critic/` and names it in `evidence_refs`.

```yaml
schema: devforgeai.worker-result/v1
run: "pm-inbox"
skill: "pm"
phase: "scope_split"
agent: "scope_splitter"
status: pass | fail | needs_user | could_not_run
reason_code: runner_missing | timeout | network | hook_fault   # required only when status is could_not_run
candidate: {id: "pm-inbox", input_checkpoint: "base"}
claimed_paths: ["docs/PM/inbox/backlog-ideas.md"]   # root-relative, at most 64; empty on any non-pass status
evidence_refs: ["docs/PM/inbox/backlog-ideas.md"]   # at most 16
note: "9 ideas partitioned: 5 promoted, 4 archived; boundary is the first release"
issues: [{id, kind, text}]                          # at most 10
```

At `devforgeai ingest-result` the sequencer derives `changed[{path, blob_sha256, kind}]` from the checkpoint diff, refuses when `changed` is not a subset of `claimed_paths` (`UNCLAIMED_CHANGE`) or a path is outside the fence, validates each written file against its template header, runs the transition oracle inside the root, writes `<phase>-result.json` with `changed` and the checkpoint ref, releases the lease and advances. `next` requires `status: fail` plus a registry `rewind_to`; no pm phase declares one, so the key is never present. Unknown keys refuse the receipt.

`gate_policy` (`BLOCK`, `REQUIRE_HUMAN`, `WARN`, `OFF`) is a defect-to-action map declared in the consumed artifact, never a status returned here. A document run carries the fixed map `{unresolvable_source: BLOCK}`.

## 7. Procedure

### 7a. Steps (the body of `SKILL.md`)

1. Parse the slug and the scope. The scope is `mvp` unless the user asked for a feature scope on an existing product — why: the slug is the `devforgeai phase start` argument and names the run `pm-<slug>`, and the scope changes which boundary the first phase partitions against.
2. Call `devforgeai phase start pm <slug>`. It runs the document gate, opens the run's candidate root, writes the run file and `context.json`, and prints the first phase, its worker and the status block.
3. Run `devforgeai status` and paste its block into the dispatch. The block names `run`, `candidate.root`, `phase`, `fence` and `granted_keys` — why: a worker writes inside the candidate root and cannot resolve it from the canonical tree, and this block is the one thing the dispatch carries that is not a path or an id.
4. Dispatch the worker the sequencer named, in a fresh context window, with that block, the run id, the phase name, the fence paths, the brainstorm document path and the scope word. Pass paths, ids, the scope word and the status block only — why: content pasted here is duplicated into two windows, and the worker can open the path itself.
5. Read the returned receipt. On `pass`, continue at step 4 with the next phase the sequencer names. On `fail`, dispatch the same phase's worker again with the sequencer's problem rows, until the sequencer stops naming that phase.
6. On `needs_user`, stop dispatching and print the handoff — why: the sequencer blocks the run at that phase on the first ask, and an undecidable scope boundary is a decision this skill is not entitled to make. The run is not closed: it stays `active` with `run.yaml#blocked_at` naming the phase, and `/pm {slug}` resumes it there once the human has acted.
7. On `could_not_run`, stop dispatching. The sequencer records the reason code and selects the repair route.
8. Print the handoff block the sequencer rendered, unchanged. When it reports the run `ready_to_promote` and the user asks for the promotion, call `devforgeai promote <run>` — why: promotion moves the candidate root's bytes into the canonical checkout under the lock, and a `REQUIRE_HUMAN` block is the only state in which the model may ask for it.

The primary window stays in the canonical checkout and never opens the brainstorm document, a PRD, a backlog file or an OBSERVED section. Its Bash grammar is exactly `devforgeai status`, `devforgeai phase start <skill> <arg>`, `devforgeai phase fail --reason <text>`, `devforgeai validate` and `devforgeai promote <run>`.

### 7b. Sub-phases and workers

| # | Sub-phase | Performed by | Writes | Isolation |
|---|-----------|--------------|--------|-----------|
| 0 | Gate | sequencer: `devforgeai phase start pm <slug>`, which also opens the candidate root | sequencer | n/a |
| 1 | Slice | sequencer: a step inside `phase start` that resolves the incoming artifact's hashed bundle into `.devforgeai/work/<run>/context.json`. No worker (section 9, row G-2) | sequencer | n/a |
| 2 | Work: `scope_split` | worker: `scope_splitter` | candidate | required |
| 3 | Write: `prd` | worker: `prd_writer` | candidate | required |
| 4 | Write: `backlog` | worker: `backlog_archiver` | candidate | required |
| 5 | Review: `critic` | worker: `pm_critic` | evidence | required |
| 6 | Record | sequencer: `devforgeai phase next` | sequencer | n/a |
| 7 | Handoff | sequencer: `devforgeai phase next`, which on the last passing transition marks the run `ready_to_promote` and renders the first block, a `REQUIRE_HUMAN` handoff naming `devforgeai promote <run>`; that command, run only after the user confirms in the session, renders the second | sequencer | n/a |

`scope_splitter` is the persona and `pm_critic` is the critic: different files, different prompts, and the critic writes only its findings file into its own run-scoped evidence directory. A persona reviewing its own partition would confirm every boundary it drew. A judge's `Write` is confined to its own run-scoped evidence directory, `.devforgeai/work/<run>/evidence/<agent>/`, which is gitignored, lies outside the candidate root, and is never promoted. Its findings file lives there and is named in `evidence_refs`; `issues[]` stays the bounded summary the handoff carries. Nothing a judge writes can reach the checkpoint diff, so its `claimed_paths` is empty on every status.

The `Isolation` column is the DevForgeAI worker-contract value compiled into the generated target profile, not Claude's `isolation` frontmatter field. The framework does not use Claude's worktree isolation or `EnterWorktree`: both fork from HEAD, and the run's phases build linearly on one candidate root instead.

### 7c. Evidence and gate table

`<run>` is `pm-<slug>`. Attempt budget is 2 for every phase (`10-sequencer-and-contracts.md` section 4).

| phase | worker | deterministic gate check | gate_policy | evidence file | transition oracle |
|---|---|---|---|---|---|
| `scope_split` | `scope_splitter` | run gate: no run is already active, `pm` is a known `kind: document` skill, both fence entries `docs/PM/<slug>/prd.md` and `docs/PM/<slug>/backlog-ideas.md` are repository-relative, free of `..` and not sequencer-owned, and no active or `ready_to_promote` run holds either path (`FENCE_OVERLAP`). Ingest validation: `changed` derived from the checkpoint diff is a subset of `claimed_paths` (`UNCLAIMED_CHANGE` otherwise), every changed path is one of those two under `candidate.root`, `claimed_paths` holds no duplicate, each written file is validated against its template header before checkpointing, and the whole root is rescanned against the stack policy with the checkpoint refused on any violation | document run map `{unresolvable_source: BLOCK}`; `test_runner_missing` is not consulted because this phase brokers no command key | `.devforgeai/work/<run>/scope_split-result.json`, `scope_split-report.md` | `document`: at least one file produced inside the fence and `docs/PM/<slug>/backlog-ideas.md` on disk |
| `prd` | `prd_writer` | ingest validation as above, with the single changed path `docs/PM/<slug>/prd.md`, written into the candidate root over whatever the `scope_split` checkpoint left there | `{unresolvable_source: BLOCK}` | `.devforgeai/work/<run>/prd-result.json`, `prd-report.md` | `document`: at least one file produced and `docs/PM/<slug>/prd.md` on disk |
| `backlog` | `backlog_archiver` | ingest validation as above, with the single changed path `docs/PM/<slug>/backlog-ideas.md`, edited over the bytes `scope_split`'s checkpoint left in the root. The phase's `input_checkpoint` is `prd`, so an edit built from anything else shows in the diff as a change nothing claimed | `{unresolvable_source: BLOCK}` | `.devforgeai/work/<run>/backlog-result.json`, `backlog-report.md` | `document`: at least one file produced and `docs/PM/<slug>/backlog-ideas.md` on disk |
| `critic` | `pm_critic` | ingest validation: the registry declares the phase `writes: none` and the worker header `writes: evidence`, so `claimed_paths` is empty and any change inside the candidate root refuses the receipt as `UNCLAIMED_CHANGE`; the dispatcher allows this worker's writes only under `.devforgeai/work/<run>/evidence/pm_critic/` and denies every other path at `PreToolUse`; the phase grants no command key, so a brokered run is refused for want of the hook marker | `{unresolvable_source: BLOCK}` | `.devforgeai/work/<run>/critic-result.json`, `critic-report.md`, then `handoff.json` | `report_only`: no file outside the fence changed since the gate snapshot and the whole-tree package and import policy holds. On pass this is the last phase: the run is marked `ready_to_promote` and a `REQUIRE_HUMAN` handoff is written whose one forward command is `devforgeai promote <run>`; the `pass` handoff is the second block, written by that command once the user asks for it |

Promotion is not part of the run's phases. The last passing `devforgeai phase next` marks the run `ready_to_promote` and writes a `REQUIRE_HUMAN` handoff whose one forward command is `devforgeai promote <run>`; the candidate root and its checkpoints stay on disk and no canonical byte moves. The compiled `SKILL.md` runs that command only after the user confirms in the session, and it is that command — never `phase next` — that merges the candidate root into the canonical checkout under `.devforgeai/lock`, refusing on `STALE_BASE` when canonical HEAD has moved past the run's pinned `base_ref`, on `DIRTY_TARGET` when a dirty canonical file is among the changed paths, and on `MERGE_CONFLICT` when the rebase cannot replay the run. A refusal moves no canonical byte and leaves the run `ready_to_promote` with its root intact, so the command can be run again once the named cause is settled. The second handoff block is written by a promotion that succeeded, and its `next` is the section 7e row for the run's outcome. Each refusal is a handoff row in section 7e.

Two limits this table does not overstate. Every `devforgeai phase start` defect is a refusal whatever a declared policy value says, and only `test_runner_missing` changes behaviour, at transition time (`10-sequencer-and-contracts.md` section 3.2). The document gate checks the fence: conformance of the incoming brainstorm document to its template, and re-resolution of the `provenance` and `depends_on` digests this skill writes, are not checked at `devforgeai phase start` today. The story gate does re-resolve every `provenance` and `context` entry and `commands.hash`, so a story quoting a requirement is checked when dev enters; `scripts/check_prd.py` is the same check for the document path, and today it runs as a human or continuous-integration step (section 9, row G-3).

### 7d. Worker contracts

Each block is the body of `agents/<role>.md` and compiles to one provider profile per target. `name` is the canonical registry worker name, which is what a hook receives as `agent_type`; the compiled filename carries the skill prefix so two skills' profiles cannot collide. `tools` are the Claude names; on Codex `apply_patch` stands in for `Edit` and `Write`. `model: inherit` keeps the worker on the session's model, which is what the terminal-only constraint leaves available. No pm phase grants a stack command key, so no worker here carries `Bash(devforgeai run *)`. Claude-only frontmatter — `hooks`, `memory`, `background`, `permissionMode`, and Claude's own `isolation` — is omitted from every profile.

```yaml
name: scope_splitter
description: Dispatch this worker at the scope_split phase to write the backlog file recording which ideas the named scope promotes and which it archives.
skill: pm
writes: candidate
model: inherit
tools: [Read, Grep, Glob, Bash(devforgeai status), Edit, Write]
skills: []
compiled_to: [.claude/agents/pm-scope_splitter.md, .codex/agents/pm-scope_splitter.toml]
responsibility: Partition every idea in the brainstorm document into promoted and archived against the named scope boundary, with one line of justification per idea, and write the backlog file that records it inside the candidate root.
inputs:
  - the devforgeai status block pasted into the dispatch, which names run, candidate.root, phase, fence and granted_keys
  - .devforgeai/work/<run>/context.json, the bundle the sequencer sliced at phase start
  - docs/brainstorm/<slug>.md inside the candidate root
  - docs/PM/<slug>/backlog-ideas.md inside the candidate root, when it exists, for the rows to carry forward
  - the OBSERVED constraint sections that exist, when the project is brownfield
  - assets/backlog-ideas.md (the template header and section order)
  - the scope word named in the dispatch, mvp or feature
outputs:
  - docs/PM/<slug>/backlog-ideas.md, written inside the candidate root and claimed
  - the Archived Ideas table, one row per archived idea with its one-line reason
  - the boundary the partition was drawn against, stated in one line in the note
must_not:
  - leave an idea id in neither half, or place one in both
  - decide a boundary the brainstorm's open questions leave open, rather than returning needs_user
  - invent an idea the brainstorm document does not carry
  - write outside the candidate root, or outside the run's fence inside it
tools_codex: [Read, Grep, Glob, Bash(devforgeai status), apply_patch]
isolation: required
returns: devforgeai.worker-result/v1
body:
  job: Draw the scope boundary once, record which side each idea falls on, and say why in the boundary's own terms.
  inputs: The list above, read under the candidate root; nothing outside it is opened.
  rules: references/scope_split.md, the exactly-one-half rule, and the must_not list.
  receipt: One devforgeai.worker-result/v1 object; on pass claimed_paths is exactly the backlog path, on needs_user it is empty and the note names the unanswered question and the ids it blocks.
```

```yaml
name: prd_writer
description: Dispatch this worker at the prd phase to write the PRD from the partition the scope_split phase recorded.
skill: pm
writes: candidate
model: inherit
tools: [Read, Grep, Glob, Bash(devforgeai status), Edit, Write]
skills: []
compiled_to: [.claude/agents/pm-prd_writer.md, .codex/agents/pm-prd_writer.toml]
responsibility: Write `docs/PM/<slug>/prd.md` inside the candidate root with one identified requirement per promoted idea, the users it serves, the non-goals the archived half implies, and success measures stated as observations.
inputs:
  - the devforgeai status block pasted into the dispatch
  - .devforgeai/work/<run>/context.json
  - .devforgeai/work/<run>/scope_split-result.json (by path)
  - docs/brainstorm/<slug>.md inside the candidate root
  - docs/PM/<slug>/prd.md inside the candidate root, when it exists, for the ids to carry forward
  - the OBSERVED constraint sections cited by the partition
  - assets/prd.md
outputs:
  - docs/PM/<slug>/prd.md, written inside the candidate root and claimed
  - one REQ entry per promoted idea or coherent group, each with an Ideas line and an Acceptance line
  - the ASSUMPTION tag every promoted idea carried, on the requirement it became
must_not:
  - write a requirement that cites no promoted idea id
  - drop an ASSUMPTION tag an idea carried, or resolve it by asserting the claim
  - state a success measure that names no observation
  - write outside the candidate root, or outside the run's fence inside it
tools_codex: [Read, Grep, Glob, Bash(devforgeai status), apply_patch]
isolation: required
returns: devforgeai.worker-result/v1
body:
  job: Write requirements that trace back to idea ids and forward to something a test could observe.
  inputs: The list above, read under the candidate root.
  rules: references/prd.md, the requirement shape, and the must_not list.
  receipt: One devforgeai.worker-result/v1 object; on pass claimed_paths is exactly the PRD path.
```

```yaml
name: backlog_archiver
description: Dispatch this worker at the backlog phase to complete the promotion log against the PRD as it was actually written.
skill: pm
writes: candidate
model: inherit
tools: [Read, Grep, Glob, Bash(devforgeai status), Edit, Write]
skills: []
compiled_to: [.claude/agents/pm-backlog_archiver.md, .codex/agents/pm-backlog_archiver.toml]
responsibility: Edit the backlog file inside the candidate root so its promotion log is complete against the requirements the PRD actually carries, and every archived idea keeps its reason.
inputs:
  - the devforgeai status block pasted into the dispatch
  - .devforgeai/work/<run>/context.json
  - docs/PM/<slug>/backlog-ideas.md inside the candidate root, as the scope_split checkpoint left it
  - docs/PM/<slug>/prd.md inside the candidate root
  - .devforgeai/work/<run>/scope_split-result.json and prd-result.json (by path)
  - assets/backlog-ideas.md
outputs:
  - docs/PM/<slug>/backlog-ideas.md, edited inside the candidate root and claimed
  - the Promotion Log, one row per idea id with its outcome and the requirement id it became, or none
must_not:
  - record a promotion to a requirement id the PRD does not contain
  - delete or reword an archive row a previous run recorded
  - change an idea id or invent an idea
  - write outside the candidate root, or outside the run's fence inside it
tools_codex: [Read, Grep, Glob, Bash(devforgeai status), apply_patch]
isolation: required
returns: devforgeai.worker-result/v1
body:
  job: Reconcile the promotion log against the PRD as written, leaving the archive rows alone.
  inputs: The list above, read under the candidate root.
  rules: references/backlog.md, the per-idea log rule, and the must_not list.
  receipt: One devforgeai.worker-result/v1 object; claimed_paths is exactly the backlog path, and the checkpoint diff touches only the Promotion Log.
```

```yaml
name: pm_critic
description: Dispatch this worker at the critic phase to judge the PRD and backlog for traceability in both directions and for measurable success rows.
skill: pm
writes: evidence
model: inherit
tools: [Read, Grep, Glob, Bash(devforgeai status), Write]
skills: []
compiled_to: [.claude/agents/pm-pm_critic.md, .codex/agents/pm-pm_critic.toml]
responsibility: Report every requirement citing no idea id, every idea id in neither the PRD nor the archive, every promotion log row naming an absent requirement, and every success measure with no observation.
inputs:
  - the devforgeai status block pasted into the dispatch
  - docs/PM/<slug>/prd.md and docs/PM/<slug>/backlog-ideas.md inside the candidate root, as the backlog checkpoint left them
  - docs/brainstorm/<slug>.md inside the candidate root
  - .devforgeai/work/<run>/scope_split-result.json, prd-result.json and backlog-result.json (by path)
outputs:
  - .devforgeai/work/<run>/evidence/pm_critic/findings.md, the full defect list, written in its own run-scoped evidence directory and named in evidence_refs
  - issues: one row per defect, naming the id and what is missing, bounded at ten
  - note: the counts of ideas, requirements, archive rows and measures examined
must_not:
  - repair, reword or renumber anything it reports
  - pass a requirement whose cited idea id is absent from the brainstorm document
  - write anywhere but its own run-scoped evidence directory, or run any stack command key
tools_codex: [Read, Grep, Glob, Bash(devforgeai status), apply_patch]
isolation: required
returns: devforgeai.worker-result/v1
body:
  job: Judge the pair this run wrote against the six properties, and report rather than repair.
  inputs: The list above, read under the candidate root; nothing is opened outside it.
  rules: references/critic.md, the six properties, and the must_not list.
  receipt: One devforgeai.worker-result/v1 object; claimed_paths is empty on every status, evidence_refs names the findings file it wrote under its run-scoped evidence directory, and each defect is also one issues row.
```

### 7e. Handoff outcomes

The `handoff.outcomes` block this skill declares, corrected to the closed status set.

| Outcome | Next steps |
|---------|------------|
| pass, all four phases, run `ready_to_promote`, nothing promoted (`REQUIRE_HUMAN`) | 1. `devforgeai promote {run}` |
| `devforgeai promote {run}` succeeded after all four phases passed | 1. `/architect {slug}` |
| `needs_user` from `scope_split` (the boundary is not decidable from the document) | 1. answer the named open question in `docs/brainstorm/{slug}.md`; 2. `/pm {slug}`, which resumes the blocked run at `scope_split` with attempts reset |
| `needs_user` from `prd` or `backlog` (a promoted idea cannot be stated as a requirement without a human decision) | 1. record the decision in `docs/brainstorm/{slug}.md`; 2. `/pm {slug}` |
| `fail` at the attempt limit because the incoming brainstorm document is unusable | 1. `devforgeai phase fail --reason <text>`, because `brainstorm` is another skill and the blocked `pm` run must be closed first; 2. `/brainstorm {slug}`; 3. `/pm {slug}` |
| `fail` at the attempt limit, any other phase, including a critic that reports defects twice | 1. fix what the handoff names, then `/pm {slug}` — the run is blocked, not closed: it stays `active` with its root and checkpoints on disk and `run.yaml#blocked_at` naming the phase, and this same command resumes it there with attempts reset. `devforgeai phase fail --reason <text>` is what abandons it instead |
| `could_not_run` with any reason code | 1. the repair named by the reason code; 2. `/pm {slug}` |
| `devforgeai promote {run}` refused `STALE_BASE` in worktree mode | 1. `devforgeai promote {run}` again; that command rebases the candidate root onto the new canonical HEAD, reruns the last transition oracle and retries the fast-forward itself before it reports, so this row is reached only when the retry also failed |
| `devforgeai promote {run}` refused `STALE_BASE` in copy mode, or `MERGE_CONFLICT` after an aborted rebase | 1. reconcile the two files under `docs/PM/{slug}/` by hand, then `devforgeai promote {run}` — the refusal moved no canonical byte, and the run stays `ready_to_promote` with its root intact |
| `devforgeai promote {run}` refused `DIRTY_TARGET` | 1. commit or discard the dirty canonical file the refusal names, then `devforgeai promote {run}` |
| `phase start` refused `FENCE_OVERLAP` | 1. finish or abandon the run the refusal names, then `/pm {slug}` |

The current sequencer selects the printed `next` itself from the fixed table in `10-sequencer-and-contracts.md` section 6: `devforgeai promote <run>` for the first block of a completed run, `/status` for the block that promotion writes and for a blocked `REQUIRE_HUMAN` document run, and the repair route for a `COULD_NOT_RUN` row. The rows above are the declared intent that `skill.yaml` carries; where the two differ today, what is printed is the sequencer's (section 9, row G-4).

### 7f. Phase guidance (becomes `references/<phase>.md`)

One file per registry phase, named for the phase exactly. Each is loaded when its phase's worker is dispatched.

#### `references/scope_split.md`

This phase owes `docs/PM/<slug>/backlog-ideas.md` inside the candidate root, carrying the partition. The PRD is the next phase's; drawing the boundary and writing the requirements are separate jobs because a boundary drawn while writing requirements drifts to fit the prose.

The boundary. With scope `mvp`, the boundary is the first release: the smallest set of ideas that delivers the brainstorm's stated problem end to end. With scope `feature`, the boundary is the slug itself: ideas that belong to this feature are promoted, ideas that belong to the wider product are archived, and the boundary line names the feature. Record the boundary in one line in the receipt's note, because every justification below is relative to it and a reader who cannot see the boundary cannot check the partition.

Every idea id from the brainstorm document lands in exactly one half. An id in neither half is an idea that silently disappears; an id in both makes the promotion log ambiguous. Each row carries one line of justification in the terms of the boundary, not in the terms of taste: "no named customer requires it in this scope" is checkable against the document, "not important enough" is not.

Carrying forward. When the backlog file already exists in the candidate root, edit it in place, keep every existing archive row and promotion-log row byte-identical, and add to them. A row a previous run recorded is the record of a decision already taken; rewriting it erases the reason the argument was settled.

When the partition is not decidable. An idea whose inclusion turns on an open question the brainstorm document leaves unanswered, and which no OBSERVED constraint and no archived row settles, is not a judgement call: it is a decision the human owns. Write nothing, return `status: needs_user` with empty `claimed_paths`, and name the question and the ids it blocks in the note. Inventing the boundary here is the failure this phase exists to prevent, because everything downstream treats the PRD as settled.

Brownfield input. An admitted OBSERVED constraint can settle a partition question, for instance an external obligation that puts an idea out of reach in this scope. Cite it by path and anchor in the justification, so the reason survives the constraint being revised later.

#### `references/prd.md`

This phase owes `docs/PM/<slug>/prd.md` inside the candidate root.

Requirements. One `REQ-NNN` per promoted idea or per coherent group of promoted ideas, numbered from `REQ-001` within the file. Each names the idea ids it covers on an `Ideas:` line, so `analyze` can walk requirement to idea and back. A requirement citing no idea id is a requirement someone added here, which is exactly the drift this chain exists to prevent; if the scope genuinely needs it, it belongs in the brainstorm document first.

Each requirement states what must be true, once, in the present tense, plus an `Acceptance:` line naming what would show it is true. That line is what plan turns into acceptance criteria and what a story's test plan later encodes; a requirement with no acceptance line leaves plan to invent one.

Assumption tags travel. An idea that carried `ASSUMPTION:` in the brainstorm document carries it into the requirement it becomes. Resolving it by asserting the claim hides an unsupported statement inside a binding document; leaving it visible lets `/clarify` reach it once a story quotes it.

Goal, Users, Non-Goals, Success Measures:

- **Goal** is one paragraph in the terms the brainstorm states the problem, so the PRD and the brainstorm can be compared line by line.
- **Users** is a table of user, need and the idea or OBSERVED source the need comes from. A user nobody's idea mentions is an invention.
- **Non-Goals** is drawn from the archived half: each row names what is not being done, the idea ids it corresponds to, and the justification the partition recorded. This is what keeps the boundary visible after the backlog file drifts out of view.
- **Success Measures** are observations, not adjectives. Each row states the measure and how it is observed, in a form QA could later run. "Fast" is not a measure; "a delivered message is visible to every member of a two-member team" is.

Frontmatter. `slug`, `template`, `template_version`, `status: draft`, `scope` (`mvp` or `feature`), `provenance` and `depends_on`. `provenance` names the brainstorm sections this PRD was sliced from; `depends_on` names those sections plus any admitted OBSERVED constraint section, each with an anchor and a digest computed with the hash rule in `01-skill-anatomy.md`. A `depends_on` entry whose path does not exist is a defect the critic reports and the consuming gate is meant to refuse.

Re-runs. When the PRD already exists in the candidate root, edit it in place, keep every existing `REQ` id for the requirement it already names, and continue numbering above the highest present. Stories cite requirement ids; renumbering silently retargets them, and the checkpoint diff records the renumber as a real change.

#### `references/backlog.md`

This phase owes `docs/PM/<slug>/backlog-ideas.md` inside the candidate root, completed against the PRD as it was actually written. Read the current bytes in this dispatch: `scope_split`'s checkpoint is already in the root, and an edit built from anything else shows in the diff as a change nothing claimed.

The promotion log gets one row per idea id: the id, the outcome (`promoted` or `archived`), the requirement id it became or `none`, and the date. The log is what lets a later reader ask what happened to an idea and get an answer without re-reading the PRD.

Reconcile against the PRD, not against the plan. When `prd_writer` grouped two promoted ideas into one requirement, both rows name that requirement. When a promoted idea did not become any requirement, the row records it as promoted with no requirement and the critic reports the gap; silently moving it to the archive would hide a requirement the scope owes.

Archive rows keep the justification `scope_split` recorded. Rewriting one here would leave the recorded phase result and the document disagreeing about why an idea was dropped, and the checkpoint diff would show the rewrite.

#### `references/critic.md`

This phase judges. The registry declares the phase `writes: none`, and the worker header declares `writes: evidence`: write the full defect list to `findings.md` under `.devforgeai/work/<run>/evidence/pm_critic/`, name it in `evidence_refs`, and change nothing inside the candidate root.

Report each defect as one `issues` row, naming the id and what is missing:

1. **Traceability down.** Every requirement's `Ideas:` line names ids that exist in the brainstorm document.
2. **Traceability up.** Every idea id in the brainstorm document appears in the PRD's requirements or in the archive table, and in exactly one of them.
3. **Promotion log.** Every log row's requirement id exists in the PRD; every promoted idea has a log row; no archive row from a previous run has been reworded.
4. **Measurability.** Every success measure names an observation; every requirement has an acceptance line.
5. **Citations.** Every `provenance` and `depends_on` entry names a path that exists, and the anchor resolves. Digest re-computation belongs to `scripts/check_prd.py`, which no worker's tool grammar admits; report an entry as unresolvable only when the path or anchor is absent.
6. **Assumptions.** Every `ASSUMPTION:` tag an idea carried appears in the requirement that idea became.

Report and stop. Repair belongs to the phase that owns the file, and a critic that edits what it reviews removes the independent check this phase exists to provide. At the attempt limit the sequencer writes a `REQUIRE_HUMAN` handoff carrying the rows.

#### `references/envelope.md`

The `devforgeai.worker-result/v1` receipt, its field bounds, and one worked example per status. Loaded for every dispatch. Content: the field table from `10-sequencer-and-contracts.md` section 5.1; the caps (64 `claimed_paths`, 16 `evidence_refs`, 16 KiB note, 10 issues); the rule that the final message is exactly the object, with no Markdown fence and no surrounding prose; the rule that `claimed_paths` is empty on any status other than `pass`; the rule that `next` needs both `status: fail` and a registry `rewind_to`, which no pm phase declares; the rule that an unknown key refuses the receipt; and the rule that `reason_code` is present exactly when the status is `could_not_run`.

## 8. Bundled resources

### Layout (fixed)

```
pm/SKILL.md                 # at most 500 lines: identity, phase list, dispatch loop, handoff table
  references/scope_split.md
  references/prd.md
  references/backlog.md
  references/critic.md
  references/envelope.md
  agents/scope_splitter.md
  agents/prd_writer.md
  agents/backlog_archiver.md
  agents/pm_critic.md
  scripts/check_prd.py
  assets/prd.md
  assets/backlog-ideas.md
```

Link depth: `SKILL.md` links to `references/`, `agents/`, `scripts/` and `assets/`; an `agents/*.md` links to `references/*.md`; nothing links further. No `README.md` inside the skill directory.

### scripts/
| File | Purpose | Invocation | Exit codes |
|------|---------|------------|------------|
| `check_prd.py` | Deterministic conformance check for the pair this skill produces: frontmatter keys against the `prd` and `backlog-ideas` template headers, required sections in order, the `REQ-NNN` and `IDEA-NNN` id patterns, no duplicate id, every requirement's cited idea id present in the brainstorm document, every brainstorm idea id present in exactly one of the PRD and the archive, every promotion-log requirement id present in the PRD, every `provenance` and `depends_on` digest recomputed with the hash rule in `01-skill-anatomy.md`, and the standard forbidden-text list | `python scripts/check_prd.py docs/PM/inbox/prd.md --brainstorm docs/brainstorm/inbox.md [--json] [--strict]` | 0 conformant, 1 defects listed on stdout, 2 usage |

The script prints JSON to stdout and diagnostics to stderr, documents `--help`, and never prompts. It is the library form of the template-conformance and provenance-conformance checks that `01-skill-anatomy.md` puts at the gate, both for the brainstorm document pm consumes and for the PRD architect consumes; the implemented document gate checks the fence only, so today the script runs as a human or continuous-integration check. No worker and no primary window runs it: a worker's Bash grammar is `devforgeai status` alone, and the primary window's is the five model-callable operations.

### references/
| File | Content | Load when |
|------|---------|-----------|
| `scope_split.md` | how the boundary is drawn per scope, the exactly-one-half rule, carrying rows forward, when the partition is not decidable | dispatching `scope_splitter` |
| `prd.md` | requirement shape and numbering, assumption travel, the four other sections, frontmatter and re-runs | dispatching `prd_writer` |
| `backlog.md` | the promotion log's rows and how it reconciles against the PRD as written | dispatching `backlog_archiver` |
| `critic.md` | the six properties checked and why repair belongs elsewhere | dispatching `pm_critic` |
| `envelope.md` | the `devforgeai.worker-result/v1` schema and bounds | every dispatch |

### assets/
| File | Used for |
|------|----------|
| `prd.md` | the PRD skeleton: the header block, the frontmatter keys, the five section headings in order, and one empty `REQ-NNN` entry showing the entry shape |
| `backlog-ideas.md` | the backlog skeleton: the header block, the frontmatter keys, and the two tables with their column headers |

### agents/
| File | Worker (from section 7d) |
|------|-------------------------|
| `scope_splitter.md` | `scope_splitter` |
| `prd_writer.md` | `prd_writer` |
| `backlog_archiver.md` | `backlog_archiver` |
| `pm_critic.md` | `pm_critic` |

## 9. Gotchas and edge cases

| Situation | What goes wrong | What to do instead |
|-----------|-----------------|--------------------|
| G-1: two phases own `backlog-ideas.md` | The `document` oracle fails a `writes: docs` phase that changed no file, so both `scope_split` and `backlog` must write; the phases build linearly on one candidate root, so each sees exactly what the previous checkpoint left | `scope_split` creates the file with the partition; `backlog` reads the checkpointed bytes in its own dispatch and edits the same path so the promotion log matches the PRD. The reference files state exactly what each phase may change, the checkpoint diff shows what it did change, and the critic checks that archive rows passed through |
| G-2: Slice has no phase | `01-skill-anatomy.md` and `05-subagent-sets.md` give Slice to a framework worker, but no registry phase dispatches one, and receipt validation binds the stop event's `agent_type` to the active phase's worker | Slice is a sequencer step inside `devforgeai phase start`: it resolves the incoming artifact's already-hashed bundle and writes `.devforgeai/work/<run>/context.json`, which every worker of the run is handed by path. This spec promises no slice phase and ships no slice agent file |
| G-3: the incoming brainstorm document is not validated at the run gate | `01-skill-anatomy.md` makes template and provenance conformance of the consumed artifact part of the gate; `document_gate` in `examples/hooks/devforgeai.py` checks the fence only, while the story gate does re-resolve every `provenance` and `context` entry and `commands.hash` and reports a placeholder digest as `unresolvable-source`. `AUTHOR-BRIEF.md` section 12 supersedes its own OI-2 row on this point | Conformance and digest re-resolution are requirements on the gate, designed and unimplemented. `scripts/check_prd.py` checks both directions and runs as a human or continuous-integration step; `scope_splitter` returns `fail` with the missing ids as issue rows when the document it reads has no usable `IDEA-NNN` entries, which is what the attempt budget and the handoff row for an unusable input exist for |
| G-4: the declared handoff table and the printed `next` | `01-skill-anatomy.md` says the sequencer selects a row from the skill's `handoff.outcomes`; `examples/hooks/devforgeai.py` selects `next` from the fixed table in `10-sequencer-and-contracts.md` section 6 | Section 7e is the declared intent carried in `skill.yaml`; a completed or `REQUIRE_HUMAN` document run currently prints `/status`. Read the handoff for what a given run printed |
| G-5: `--continue` after a `needs_user` | `02-skill-roster.md` offers `/pm {slug} --continue`, and an earlier draft here said `needs_user` closes the run and abandons its candidate root | `needs_user` blocks the run rather than closing it: it stays `active` with its root and checkpoints on disk and `run.yaml#blocked_at` naming the phase, and plain `devforgeai phase start pm {slug}` resumes it there with `attempts` reset. `--continue` is therefore unnecessary and is not implemented. Where a run really is closed — `devforgeai phase fail --reason <text>` abandoned it — the next `phase start` opens a new candidate root from the current canonical HEAD, over a backlog that may already hold whatever an earlier run promoted; the partition phase carries those rows forward |
| G-6: an idea grouped with another into one requirement | The promotion log looks wrong if it expects one requirement per idea | Both idea rows name the same requirement id. The log is per idea, the requirements are per coherent statement, and the critic checks the mapping in both directions rather than assuming it is one to one |
| G-7: a promoted idea that became no requirement | Moving it quietly to the archive hides a scope decision nobody made | The log records it as promoted with no requirement, and the critic reports the gap. A human either accepts the archive or a fresh run writes the requirement |
| G-8: an `ASSUMPTION:` tag inherited from an idea | Resolving it while writing the requirement turns an unsupported claim into a binding statement | The tag travels into the requirement. Plan's story gate refuses an unresolved assumption outside a Clarifications section, so the tag is what routes it to `/clarify` at the point where it matters |
| G-9: brownfield feature scope | An MVP boundary applied to an existing product archives most of the product | The scope word is passed in the dispatch and written into the PRD frontmatter as `scope: feature`; the partition is drawn against the feature, and `analyze` can later flag reduced-provenance work by reading that key |
| G-10: a re-run after ideas were promoted off the backlog | Renumbering requirements retargets the stories that cite them | Existing `REQ` ids keep the requirement they already name, and new requirements continue above the highest present id. Existing archive and log rows are carried forward byte-identical, and the checkpoint diff is where a reviewer sees whether they were |
| G-12: the receipt no longer carries an `evidence` object | Earlier drafts gave the phases `evidence.promoted`, `evidence.archived`, `evidence.boundary`, `evidence.requirements`, `evidence.assumptions`, `evidence.log` and `evidence.checked`. The receipt schema in the write-model revision removes `evidence` and adds `claimed_paths` and `evidence_refs`, which are paths, not rows | Every one of those rows already has a home in the pair this run writes: the partition in the Archived Ideas table, the requirement-to-idea map on each `Ideas:` line, the outcomes in the Promotion Log, the tags on the requirements that inherited them. `evidence_refs` points at those files, `note` carries the boundary and the counts, and `issues` carries what could not be written, bounded at ten rows. `pm_critic`, as a judge, writes its own findings under `.devforgeai/work/<run>/evidence/pm_critic/` and names that file in `evidence_refs`. The critic reads the two documents, not a sibling phase's evidence object, so nothing downstream loses an input |
| G-13: the primary window and the candidate root | A worker cannot resolve `candidate.root` from the canonical tree, and pasting artifact content into a dispatch is the restatement the anti-ceremony rules forbid | The one thing the dispatch carries beyond paths, ids and the scope word is the `devforgeai status` block, which names `run`, `candidate.root`, `phase`, `fence` and `granted_keys`. It is generated, not composed, and it is the only sanctioned paste |
| G-11: the brainstorm document holds an idea with no source citation | The PRD inherits an unsourced statement and it becomes binding | `scope_splitter` records the idea in the partition and `pm_critic` reports the missing citation as an issue row; the repair belongs to `/brainstorm`, which owns that document's template. `pm`'s fence holds only the two `docs/PM/<slug>/` paths, so the brainstorm document cannot be edited from inside this run even in the candidate root |
| G-14: an earlier draft said promotion is the last thing the run does and that `devforgeai phase next` merges the candidate root | An author compiles a `SKILL.md` that never asks the user, and the run's files land in the canonical checkout without a human decision | Promotion is never automatic. The last passing transition sets `runs.<run>.status: ready_to_promote` and writes a `REQUIRE_HUMAN` handoff whose only forward step is `devforgeai promote <run>`; the compiled `SKILL.md` runs that command only after the user confirms in the session, and that command writes the second handoff block, whose `next` is the section 7e row for the run's outcome. Every run ends in two blocks, not one, and `STALE_BASE`, `DIRTY_TARGET` and `MERGE_CONFLICT` are refusals of `devforgeai promote <run>` that leave the run `ready_to_promote` with its root intact, never refusals of `devforgeai phase next`. **Decision (D7, as amended; `10-sequencer-and-contracts.md` sections 5.4, 6 and 12.4):** the sequencer may not close a run onto the canonical tree on its own. |
| G-15: An earlier draft said a `REQUIRE_HUMAN` block closes the run, so "no flag resumes a closed one" | An author writes a repair route that opens a fresh run, and `devforgeai phase start` refuses it — the blocked run is still `active` — or writes `devforgeai phase fail --reason <text>` into every recovery row and throws away work the run had already checkpointed | A block is not a close. A `needs_user` result and an exhausted attempt budget both leave the run `active` with its lease released, its candidate root and checkpoints on disk, and `run.yaml#blocked_at` naming the phase. `devforgeai phase start` with the same skill and the same argument **resumes** that run at `blocked_at` with `attempts` reset to zero instead of refusing it, so `/pm {slug}` is the whole recovery once the human has acted. Only another skill on the same story needs `devforgeai phase fail --reason <text>` first, and that call is what abandons the root. **Decision (`10-sequencer-and-contracts.md` sections 2, 3, 5.4 and 6):** blocked runs resume; they are not reopened. |

## 10. Success criteria and test cases

### Success criteria

- Triggers on the section 4 positives and on none of the near-misses.
- Every idea id in the brainstorm document appears in exactly one of the PRD's requirements and the archive table; measured by `scripts/check_prd.py` exiting 0.
- Every requirement carries an `Ideas:` line naming ids that exist, and an acceptance line.
- Every promotion-log row names a requirement that exists in the PRD, or `none`.
- Every success measure names an observation.
- Every phase's `changed` set is a subset of its `claimed_paths` and holds no path outside the two fence entries, and the `critic` phase changes nothing inside the candidate root.
- Every run ends with a handoff whose next step is exactly one command.

### Fixtures

Base fixture, `docs/design/examples/fixtures/pm/`, a repository holding one finished brainstorm document:

| Path | Content |
|---|---|
| `docs/brainstorm/inbox.md` | A conformant `brainstorm` document: frontmatter with `slug: inbox`, `template: brainstorm`, `template_version: 1`, `status: draft`, and one provenance entry for `notes/ideas.md`; `## Problem` with one paragraph; `## Ideas` with nine entries `IDEA-001` to `IDEA-009` (per-seat pricing, usage pricing, free tier, enterprise plan, shared team inbox, per-user rules, mobile digest, webhook integration, import from the old tool), each with a `Source:` line, `IDEA-002` carrying an `ASSUMPTION:` line about counting messages at ingest; `## Clusters` with three groups, `Pricing model` holding `IDEA-001`, `IDEA-002` and `IDEA-003`, `Inbox behaviour` holding `IDEA-005`, `IDEA-006` and `IDEA-007`, `Integration` holding `IDEA-008` and `IDEA-009`, and `IDEA-004` in a cluster of its own; `## Open Questions` with two rows, both routed to a named person and neither blocking the first release |
| `notes/ideas.md` | the nine-idea source the brainstorm document cites, so `provenance` resolves |
| `.devforgeai/state.yaml` | canonical state: `version: 1`, `target: [claude]`, `mode: greenfield`, `slug: inbox`, `phase: pm`, an empty `stories` mapping, and a `runs` mapping with one key `pm-inbox` whose value carries `skill: pm`, `mode: copy`, `root: .`, `base_ref: fixture`, `checkpoint: base` and `status: active` |
| `.devforgeai/work/pm-inbox/run.yaml` | the per-run enforcement file, standing in for what `devforgeai phase start` writes: `canonical: .`, `phase: scope_split`, `fence: [docs/PM/inbox/prd.md, docs/PM/inbox/backlog-ideas.md]`, `test_paths: []`, `granted_keys: []`, `attempts` and `max_attempts` at 2 for the four phases, `gate_policy: {unresolvable_source: BLOCK}`, and a `lease` naming the eval session |

The sequencer is not installed in an eval copy, so the run file stands in for `devforgeai phase start` and the fixture root stands in for the candidate root: `candidate.mode` is `copy` and `candidate.root` is the fixture copy itself, so a worker's writes land where the eval can see them. Per-run enforcement lives in `run.yaml`, not in `state.yaml`, because nothing inside a candidate root reads canonical state. Expectations are checked against the receipt in the transcript and against files on disk. No eval gates on sequencer behaviour; quick-mode results are generation feedback only (`12-post-mvp.md#pm-02`).

Overlays, copied over the base fixture for the eval whose id they name:

| Overlay | Files |
|---|---|
| `overlays/eval-2/.devforgeai/work/pm-inbox/run.yaml` | the base run file with `phase` set to `prd` |
| `overlays/eval-2/docs/PM/inbox/backlog-ideas.md` | the backlog as `scope_split` leaves it: frontmatter with `slug: inbox`, `template: backlog-ideas`, `template_version: 1`, `status: active`; `## Archived Ideas` with rows for `IDEA-001`, `IDEA-003`, `IDEA-004` and `IDEA-007`, each with a one-line reason; `## Promotion Log` with nine rows recording the outcome per idea and no requirement ids yet |
| `overlays/eval-2/.devforgeai/work/pm-inbox/scope_split-result.json` | the recorded `scope_split` result: `claimed_paths` naming the backlog file, a `changed` row for it, and a note recording `IDEA-002`, `IDEA-005`, `IDEA-006`, `IDEA-008` and `IDEA-009` as promoted, the other four as archived, and the first release as the boundary |
| `overlays/eval-3/docs/brainstorm/inbox.md` | the base document with its `## Open Questions` replaced by one row: "which pricing model is in scope for the first release?", blocking `IDEA-001`, `IDEA-002` and `IDEA-003`, routed to a named person and unanswered anywhere in the fixture |

### evals/evals.json (used verbatim)

```json
{
  "skill_name": "pm",
  "evals": [
    {
      "id": 1,
      "prompt": "Run pm for the inbox slug with the default mvp scope. The DevForgeAI sequencer is not installed in this copy; the run file at .devforgeai/work/pm-inbox/run.yaml is already open at phase scope_split and this working copy is the candidate root. Dispatch that phase's worker and show me the receipt it returns.",
      "expected_output": "A scope_splitter receipt claiming docs/PM/inbox/backlog-ideas.md, which now partitions all nine idea ids into promoted and archived with one line of justification each, and a note naming the first release as the boundary.",
      "files": [],
      "expectations": [
        "The scope_splitter receipt's claimed_paths is exactly [docs/PM/inbox/backlog-ideas.md] and that file exists in the working copy afterwards",
        "Every one of IDEA-001 through IDEA-009 appears exactly once across the written Archived Ideas table and Promotion Log",
        "Every archived idea row in the written file carries a one-line reason",
        "The receipt's note states the boundary the partition was drawn against",
        "The written file has the two sections Archived Ideas and Promotion Log and the frontmatter keys slug, template, template_version and status",
        "No prd.md exists in the working copy after this phase"
      ]
    },
    {
      "id": 2,
      "prompt": "Continue pm for the inbox slug. The sequencer is not installed; the run file is open at phase prd and this working copy is the candidate root. Dispatch that phase's worker and show me the receipt it returns.",
      "expected_output": "A prd_writer receipt claiming docs/PM/inbox/prd.md, whose requirements cover exactly the five promoted ideas, each citing its idea ids and carrying an acceptance line, with the ASSUMPTION from IDEA-002 preserved, non-goals drawn from the four archived ideas, and success measures stated as observations.",
      "files": [],
      "expectations": [
        "The prd_writer receipt's claimed_paths is exactly [docs/PM/inbox/prd.md] and that file exists in the working copy afterwards",
        "Every requirement in the written file has an id matching REQ-NNN and an Ideas line naming only ids the scope_split result recorded as promoted",
        "The five promoted idea ids are each cited by at least one requirement",
        "The requirement covering IDEA-002 carries the ASSUMPTION line about counting messages at ingest",
        "The Non-Goals section names the four archived idea ids",
        "Every row of Success Measures names how the measure is observed",
        "The frontmatter carries scope: mvp and depends_on entries naming docs/brainstorm/inbox.md"
      ]
    },
    {
      "id": 3,
      "prompt": "Run pm for the inbox slug with the default mvp scope. The sequencer is not installed; the run file is open at phase scope_split and this working copy is the candidate root. Dispatch that phase's worker and show me the receipt it returns.",
      "expected_output": "A scope_splitter receipt with status needs_user, empty claimed_paths, naming the unanswered pricing question and the three idea ids it blocks, because the brainstorm document leaves the boundary undecidable.",
      "files": [],
      "expectations": [
        "The scope_splitter receipt has status needs_user and an empty claimed_paths list",
        "The receipt names the open question about which pricing model is in scope",
        "The receipt names IDEA-001, IDEA-002 and IDEA-003 as the ids the question blocks",
        "No file under docs/PM/ is created in the working copy",
        "The receipt does not assert a pricing model as chosen"
      ]
    }
  ]
}
```

## 11. Dependencies and compatibility

| Kind | Value |
|------|-------|
| Tools | `SKILL.md`: `Read`, `Agent`, and a Bash grammar no wider than the five model-callable operations `devforgeai status \| phase start <skill> <arg> \| phase fail --reason \| validate \| promote <run>`. Document writers (`scope_splitter`, `prd_writer`, `backlog_archiver`): `Read`, `Grep`, `Glob`, `Bash(devforgeai status)`, plus `Edit` and `Write`, which Codex serves as `apply_patch`; every write is denied outside `candidate.root` and outside the phase's fence. Judges (`pm_critic`): `Read`, `Grep`, `Glob`, `Bash(devforgeai status)`, plus `Write` confined to `.devforgeai/work/<run>/evidence/<agent>/`. No pm phase grants a stack command key, so no worker carries `Bash(devforgeai run *)` |
| MCP servers | none |
| Runtime | Python 3.11+ for `scripts/check_prd.py`, which imports `PyYAML` and the standard library only. Worktree mode additionally requires `git` with at least one commit on the project; without it the run falls back to copy mode |
| Project commands | none. Every pm phase declares an empty run-key set, so no `stack.yaml` key is brokered during this skill's run; a document run carries `commands: {}` (`10-sequencer-and-contracts.md` section 9) |
| DevForgeAI/Core compatibility | `NOT_APPLICABLE`; `pm` is an anatomy-governed skill, not a Research Core adapter. It cites sealed dossiers by id where a brainstorm idea carries one and never writes under `docs/research/` |
| Other skills | Upstream: `brainstorm`. Downstream: `architect`, `plan` and `analyze` consume `prd`; `brainstorm` and `pm` itself consume `backlog-ideas`. Pm invokes no other skill: the architect edge is a handoff row a human or a fresh session runs |

Deferred dependencies, named and not gated on:

| Entry | What pm does today without it |
|---|---|
| `12-post-mvp.md#pm-01` | Isolation is a declaration compiled into the target profile; nothing verifies it at run time. `isolation: required` is the DevForgeAI contract value, not Claude's `isolation` frontmatter field |
| `12-post-mvp.md#pm-04` | A worker's write boundary is the dispatcher's `PreToolUse` deny plus the candidate root, not an operating-system boundary |
| `12-post-mvp.md#pm-02` | Quick-mode eval results are generation feedback only. No section of this spec gates on them |
| `12-post-mvp.md#pm-06` | Eval mode is `skip` or `quick`; the interactive mode is not named as available |
| `12-post-mvp.md#pm-10` | Nothing re-checks an applied PRD from a clean checkout. `scripts/check_prd.py` runs as a human or continuous-integration step |

Frontmatter values derived from this table:

```yaml
compatibility: "Runs in the Claude Code or Codex terminal inside a repository that has .devforgeai/state.yaml and a brainstorm document for the slug. Requires Python 3.11+ and PyYAML for the bundled check script."
allowed-tools: "Read Agent Bash(devforgeai status) Bash(devforgeai phase start *) Bash(devforgeai phase fail *) Bash(devforgeai validate) Bash(devforgeai promote *)"
```

## 12. Targets

The generator produces one provider-neutral semantic package and a separate adapter for each selected target when frontmatter, invocation policy, or agent configuration differs. Provider-neutral resources may be shared. Adapter directories are not required to be byte-identical or symlinked.

| Target | Install path | Invocation | Subagents | Notes |
|--------|--------------|------------|-----------|-------|
| claude | `.claude/skills/pm/` | `/pm` with the slug as its argument, and the scope word when it is a feature scope | `.claude/agents/pm-<role>.md`: three document writers with `Edit` and `Write` confined to the candidate root, one judge whose `Write` reaches only its run-scoped evidence directory | Provider-specific frontmatter keys are compiled into this target's `SKILL.md` only. `hooks`, `memory`, `background`, `permissionMode` and Claude's own `isolation` are omitted from every profile |
| codex | `.agents/skills/pm/` plus `.codex/agents/` profiles | `$pm` with the same arguments | `.codex/agents/pm-<role>.toml`: the same four names, with `apply_patch` in place of `Edit` and `Write` | Portable six-field frontmatter only; policy goes in target-side configuration |
| both | separate `.claude/skills/pm/` and `.agents/skills/pm/` adapters | as above | as above | Share only provider-neutral resources; validate each adapter independently |

```yaml
metadata:
  version: "1.0.0"
  devforgeai-spec: "SKILL-SPEC-007"
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
- Provide defaults, not menus: the default scope is `mvp`, and the feature scope is named explicitly.
- Scripts are non-interactive, take arguments, print data to stdout and diagnostics to stderr, and exit 0, 1 or 2.
- From this skill's own subject matter: every idea id lands in exactly one half; every requirement cites the ideas it came from; a boundary the document leaves open is a human decision; an assumption tag travels rather than dissolving.

## 14. Acceptance checks

Run these before reporting done and paste their output:

```bash
# frontmatter and naming (skill-creator's own validator)
python -m scripts.quick_validate ./out/pm               # run from the skill-creator directory
# open-standard validator, if installed
skills-ref validate ./out/pm
# size budget
wc -l ./out/pm/SKILL.md                                 # must be under 500
# every worker in section 7d has a prompt file, and no extra
ls ./out/pm/agents/                                     # scope_splitter prd_writer backlog_archiver pm_critic
# one reference file per registry phase, plus envelope.md
ls ./out/pm/references/                                 # scope_split prd backlog critic envelope
# the bundled check script runs and reports usage cleanly
python ./out/pm/scripts/check_prd.py --help
# no leftover placeholders
grep -rnE 'T[O]DO|T[B]D|\{\{' ./out/pm || echo clean
# the spec battery
python3 docs/design/specs/verify.py --only v1,v2,v4
```

For non-Research anatomy skills, DevForgeAI skill-validator additionally checks: all sub-phase kinds present with Gate, Record and Handoff bound to sequencer operations; persona and critic are different files; `must_not` present in every agent file; every agent declaring `writes: candidate` or `writes: evidence`, with a `writes: evidence` agent carrying no `Edit` and a `Write` fenced to its run-scoped evidence directory, and a `writes: candidate` agent carrying no tool beyond the read set plus `Edit` and `Write`; the `SKILL.md` Bash grammar no wider than the five model-callable operations; and handoff outcomes covering every status the skill can return, including `could_not_run`.

## 15. Provenance

| Source | Hash | Used for |
|--------|------|----------|
| docs/design/01-skill-anatomy.md#primary-window-contract | see frontmatter | sections 2 (R6), 7a, 13 |
| docs/design/01-skill-anatomy.md#gate-validating-the-incoming-artifact | see frontmatter | sections 7c, 9 (G-3) |
| docs/design/10-sequencer-and-contracts.md#4-per-skill-phase-registry | see frontmatter | sections 7b, 7c |
| docs/design/10-sequencer-and-contracts.md#5-2-validation-order | see frontmatter | sections 7c, 9 (G-1) |
| docs/design/10-sequencer-and-contracts.md#5-4-transition-oracles | see frontmatter | sections 7c, 9 (G-1) |
| docs/design/10-sequencer-and-contracts.md#6-handoff-envelope | see frontmatter | sections 7e, 9 (G-4) |
| docs/design/11-artifact-registry.md#1-template-registry | see frontmatter | sections 6, 8 |
| docs/design/11-artifact-registry.md#3-depends-on-edges | see frontmatter | sections 2 (R7), 6, 7f |
| docs/design/02-skill-roster.md#pm | see frontmatter | sections 2 (R2, R4), 7f |
| docs/design/02-skill-roster.md#handoff-decision-tables | see frontmatter | section 7e |
| docs/design/05-subagent-sets.md#sets-per-skill | see frontmatter | sections 7d, 8 |
