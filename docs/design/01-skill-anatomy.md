# Skill Anatomy

Every DevForgeAI skill except Research follows the spine in this document.
Research is governed instead by `framework/skills/research/`: its P0-P9 state
machine and typed JSON/JSONL records are normative, it defines contracts for
four worker roles that write nothing, and deterministic Research Core is its
sole canonical writer. The current provider templates do not execute those workers.

## Layers

```
provider entry adapter  ->  skill (primary window)  ->  LLM workers
(thin)                      (dispatch loop)            (isolated context windows)
                                  |                     producers write in the
                                  |                     candidate root; judges
                                  v                     write nothing
                          devforgeai sequencer
                          (deterministic; owns the candidate root;
                           sole writer of canonical .devforgeai/**)
```

### Provider entry adapter responsibilities (and nothing more)

1. Parse arguments and flags.
2. Call `devforgeai phase start <skill> <arg>`; the sequencer reads `.devforgeai/state.yaml`, runs the gate, and refuses if the prerequisite phase is incomplete.
3. Load the skill.
4. Print the handoff the sequencer rendered.

### Skill responsibilities

For a skill governed by this anatomy, run the seven sub-phases below in order. Gate, Slice, Record, and Handoff are sequencer operations; Work, Write, and Review dispatch LLM workers. The skill runs in the primary context window and is bound by the contract below.

## Primary window contract

**The model dispatches, the sequencer decides.** For an anatomy-governed skill, the primary window (provider entry adapter + skill orchestration) does light, trivial work only. It dispatches workers and calls the sequencer. It never writes state, never advances a phase, and never decides that a phase passed. The primary session stays in the canonical checkout; the writing happens in the candidate root, inside a worker.

| The primary window may | The primary window must never |
|------------------------|-------------------------------|
| Parse arguments and flags | Read an artifact, constitution document, or source file |
| Call the model-callable sequencer operations (below) | Read a template, sealed Research dossier record, or report |
| Dispatch a worker with file paths, a one-line instruction, and the `devforgeai status` block | Paste file content into a worker prompt |
| Receive a worker's receipt (bounded, see below) | Reason about the domain, fix a defect, or draft content |
| Branch on a returned status (`pass`, `fail`, `needs_user`, `could_not_run`) | Retry a worker by re-doing its work itself |
| Ask the user a question a worker flagged as `needs_user` | Write any file, in the candidate root, under `.devforgeai/`, or anywhere else |
| Print the handoff the sequencer rendered | Compose the handoff itself, or declare a phase complete |

Model-callable CLI, closed set. Anything else is hook-only and is denied in the Bash allowlist:

| Operation | Purpose |
|---|---|
| `devforgeai status` | print the run block: `run`, `candidate.root`, `phase`, `fence`, `granted_keys`, and `next` |
| `devforgeai phase start <skill> <arg>` | run the deterministic gate, open the candidate root, and open the phase |
| `devforgeai phase fail --reason <text>` | record a BLOCK handoff and stop |
| `devforgeai validate` | fence and invariant scan; writes nothing |
| `devforgeai promote <run>` | fast-forward a `ready_to_promote` run into the canonical checkout; called only after `REQUIRE_HUMAN` and only when the user asks |

`session-start`, `ingest-result`, `phase next`, and the four `candidate` operations (`open`, `checkpoint`, `promote`, `abandon`) are hook-only: they require the `DEVFORGEAI_HOOK_EVENT` environment marker and never appear in a model-facing allowlist. `devforgeai run <key>` is not model-callable from the primary window: it is available to the producer worker that holds the run's lease, for the keys the phase granted, and it executes with cwd = `candidate.root`. The grammar is normative in `10-sequencer-and-contracts.md`.

Write permission is per role, not blanket, and a worker header declares it as `writes: candidate | evidence | none` (`05-subagent-sets.md`). Producers (`candidate`) — red, green, refactor and fix workers, and every document writer — hold Edit and Write (Codex: `apply_patch`) and `Bash(devforgeai run *)` for the keys the phase granted, and every write they make is under `candidate.root`. Judges (`evidence`) — the gate resolver, critics, reviewers, smoke and QA verifiers, analyze and status — hold Read, Grep, Glob, `Bash(devforgeai status)`, and Write in exactly one place: `.devforgeai/work/<run>/evidence/<agent>/`, where the judge's findings file lives and which its receipt names in `evidence_refs`. That directory is run-scoped, gitignored, and never promoted, so a judge cannot change what the run ships. `writes: none` is left for a worker that produces nothing but the receipt. No worker of any class holds a git write, a package manager, a network tool, or a raw stack command.

Return summary budget. Every worker's final message is exactly one `devforgeai.worker-result/v1` receipt — the paths it claims, never the bytes:

```json
{"schema":"devforgeai.worker-result/v1","run":"<run>","skill":"<skill>","phase":"<phase>","agent":"<agent>",
 "status":"pass|fail|needs_user|could_not_run","reason_code":"runner_missing|timeout|network|hook_fault",
 "candidate":{"id":"<run>","input_checkpoint":"<phase-or-base>"},
 "claimed_paths":["<root-relative path>"],
 "evidence_refs":["<root-relative or .devforgeai/work/<run>/... path>"],
 "note":"","issues":[],"next":"<rewind_to>"}
```

The schema is normative in `schemas/devforgeai/v1/worker-result.schema.json`. Bounds: `claimed_paths` at most 64, `evidence_refs` at most 16, `issues` at most 10, `note` at most three lines. A non-pass status carries an empty `claimed_paths`; `next` is legal only with `status: fail` and names the registry's `rewind_to`. Rewinding to phase P resets the candidate root to the checkpoint P started from — its predecessor's, or `base` for the first phase — and re-enters P; it does not reset to P's own checkpoint, which is the state P is being rewound out of. An unknown key is refused.

At `ingest-result` the sequencer derives `changed[{path, blob_sha256, kind}]` from the candidate's checkpoint diff, refuses the result when `changed` is not a subset of `claimed_paths` or a path falls outside the run's fence, runs the transition oracle inside the candidate root, records the result and the checkpoint, releases the lease, and advances. A worker's claim is never why a phase advances; the diff is.

Status vocabulary, closed: `pass | fail | needs_user | could_not_run`, with `reason_code` in `runner_missing | timeout | network | hook_fault` whenever the status is `could_not_run`. `gate_policy` (`BLOCK | REQUIRE_HUMAN | WARN | OFF`) is a defect-to-action map declared per artifact, never a returned status. Research keeps its own typed set under `framework/skills/research/`.

The primary window forwards the changed paths and `issues` to the next worker by path and id. It does not open them.

Enforcement. For anatomy-governed skills, skill-validator rejects a compiled SKILL.md that contains a direct file read of anything except `state.yaml`, an inline prompt longer than a dispatch instruction, an LLM sub-phase without a named worker, or a Bash grammar wider than the model-callable operations above. Research is validated against `framework/skills/research/` instead.

Why this matters. The primary window persists across the whole skill run and across user conversation. Anything read into it stays there. A worker keeps its intermediate work outside the parent context and returns only its receipt, but still consumes provider tokens and its returned receipt consumes parent context.

## The seven sub-phases

Gate, Slice, Record, and Handoff are deterministic sequencer operations, not workers. Only Work, Write, and Review dispatch an LLM.

| # | Sub-phase | Performed by | Input | Output |
|---|-----------|--------------|-------|--------|
| 0 | Gate | sequencer, inlined in `devforgeai phase start` | incoming artifact(s) from the previous phase | pass, or a rejection with defects and a handoff pointing at the phase that must fix them |
| 1 | Slice | sequencer, at `phase start` | the incoming artifact's `context[]` bundle, already excerpted, anchored and hashed by the skill that wrote it | `.devforgeai/work/<run>/context.json`: every entry with its excerpt, anchor, digest and this run's re-resolution verdict. A run whose gate identifies no incoming artifact records the no-op |
| 2 | Work | workers: skill-owned (one per step) | context bundle, user conversation, sealed Research RUN/Source/Evidence/Claim/manifest references | structured findings (not the final file). May repeat (e.g. plan runs epics, stories, sprints). |
| 3 | Write | worker: skill-owned writer (`writes: candidate`) | findings + this skill's template | the artifact written into the candidate root; the receipt claims its path |
| 4 | Review | worker: skill-owned critic (`writes: evidence`) | draft artifact, template, context bundle, sealed Research dossier references | pass, or a list of defects, written to `work/<run>/evidence/<agent>/` and named in `evidence_refs` |
| 5 | Record | sequencer, at `phase next` | receipts from sub-phases 0-4 and the checkpoint diff | updated `state.yaml`, `provenance/log.jsonl` entry, artifact hashes, `.devforgeai/work/<run>/<phase>-result.json` |
| 6 | Handoff | sequencer, at `phase next` | state and the run's results | `.devforgeai/work/<run>/handoff.json` plus its rendered block |

If Review fails, loop Write <- Review up to the phase's entry in the `max_attempts` map in `.devforgeai/work/<run>/run.yaml`, then surface defects to the user in the handoff.

### Gate: validating the incoming artifact

Review (sub-phase 4) checks what a skill *produces*. Gate (sub-phase 0) checks what a skill *consumes*. Both are needed: the producing skill may have filled its template incorrectly, or the constitution may have changed since the artifact was written. A story is checked when dev enters, not only when plan exits.

The gate is deterministic and has no LLM judgment. It runs in three places over the same library (`check_story.py` and its siblings, imported by the sequencer): inlined in `devforgeai phase start`, re-run as a `PreToolUse` hook check, and re-run by the rung-4 clean-checkout validator (`12-post-mvp.md#pm-10`). Two checks:

1. **Template conformance.** The incoming artifact is checked against the template that produced it (frontmatter keys, required sections, ID formats, no placeholder text left behind). The template lives with the producing skill, so dev gates a story against `.devforgeai/skills/plan/templates/story.md`.
2. **Provenance conformance.** Every `context:` entry and every frontmatter `depends_on:` entry is re-resolved: the source must exist, the anchor must resolve, and the hash must match the current content. For a story this covers its constitution, sourcetree, techstack, architecture slices, its parent epic, and any sealed Research RUN/Source/Evidence/Claim/manifest references.

Outcomes:

| Result | Action |
|--------|--------|
| pass | continue to Slice |
| template defect | reject; handoff says `re-run /<producing-skill> <artifact>` with the defect list |
| stale hash | reject; handoff says `/plan <slug> --reslice` (re-slices from current sources) or `/plan <slug> --reslice <story>` |
| missing dependency | reject; handoff names the missing artifact and the command that produces it |

Each row's severity is the artifact's `gate_policy` entry for that defect class (`BLOCK | REQUIRE_HUMAN | WARN | OFF`). Gate never repairs the artifact. Repair belongs to the skill that owns the template.

## Dedicated templates

Every anatomy-governed non-Research skill owns its templates under `.devforgeai/skills/<name>/templates/`. No shared or generic template exists. A template is the contract between two phases:

- The producing skill's writer fills it.
- The producing skill's critic reviews against it.
- The consuming skill's gate validates against it.

Each template carries a machine-readable header so gate can check it without an LLM:

```yaml
# .devforgeai/skills/plan/templates/story.md  (header block)
template: story
template_version: 3
accepts_versions: [3]
required_frontmatter: [id, epic, sprint, scope, status, template, template_version, requires_skill, risk_tier, size, gate_policy, blocked_by, provenance, context, write_fence, commands, test_plan]
required_sections: ["## Goal", "## Context", "## Interface", "## Acceptance Criteria", "## Unchanged Behaviour", "## Out of Scope", "## Verification", "## Clarifications"]
id_pattern: "^STORY-(HOTFIX-)?[0-9]{3}$"
forbidden_text: ["TODO", "TBD", "{{", "}}", "<fill in>"]
```

Template version is written into the artifact's frontmatter. When a template changes, gate flags artifacts written under the old version so they can be migrated by the producing skill.

## Subagent ownership

Every anatomy-governed non-Research skill ships its own worker set under `.devforgeai/skills/<name>/subagents/`. A worker has one responsibility, one prompt, one input contract, one output contract. Skills do not borrow each other's workers. Every worker returns one `devforgeai.worker-result/v1` receipt on both providers; a producer has already written its files into the candidate root by then, and the sequencer checks the receipt against the checkpoint diff.

One kind exists. There is no framework worker and no shared `.devforgeai/subagents/` directory: Gate, Slice, Record and Handoff are all sequencer operations, and every remaining sub-phase belongs to the skill that runs it.

| Kind | Lives in | Examples | Rule |
|------|----------|----------|------|
| Skill-owned workers | `.devforgeai/skills/<name>/subagents/` | plan's epic-writer, dev-tdd's red-tester, qa's criteria-checker | One per Work / Write / Review step of that skill. Named `<skill>-<role>` when compiled so they never collide. |

A skill's Work sub-phase is therefore a sequence of its own workers, each invoked in a fresh context window with only the inputs its contract names. The primary window passes file paths and short summaries between them, never full content. See `05-subagent-sets.md` for the per-skill sets and the TDD worked example.

## Slice, and why it has no worker

Slice is sub-phase 1 and it dispatches nothing. The artifact a phase consumes already carries its own `context[]` bundle — an excerpt, an anchor and a digest per entry, written by the skill that produced it — and `devforgeai phase start` has just re-resolved every one of those digests to open the run. Extracting the sections again would be a second, unverified read of the same sources, so the sequencer writes what it resolved to `.devforgeai/work/<run>/context.json` and hands each worker that path.

| Case | What Slice writes |
|---|---|
| story run (`dev`) | the story's `context[]`, entry by entry, with each entry's verdict: resolved, `stale-hash` or `unresolvable-source` |
| story-anchored document run (`review`, `qa`) | the same, from the story the argument names |
| every other document run | `slice: none` and an empty entry list: the document gate identifies no incoming artifact, so there is no bundle to resolve and each worker reads the paths its own phase names |
| `init`, `status`, `research` | nothing: no run opens, so no evidence directory exists |

The excerpt is never rewritten and never summarised. An entry whose source moved is carried with its verdict, so the worker reads the row and the detail rather than a silently re-excerpted replacement.

Persona, writer, and critic are *patterns*, not shared agents. Each skill owns its own instance of each (e.g. `pm-persona`, `pm-writer`, `pm-critic`) with prompts specific to that phase's template and failure modes. Rules that apply to every instance:

| Pattern | Rule | Anti-hallucination duty |
|---------|------|-------------------------|
| persona | Domain thinking only; never writes the final file | Must tag unsupported claims `ASSUMPTION:` |
| writer | Renders findings into this skill's template | Cannot add content not present in findings |
| critic | Independent review of draft against template and sources | Rejects any untagged claim without a source |

Structural template conformance and anchor/hash re-resolution are not workers. Both are deterministic library checks the sequencer runs at the gate.

Persona and critic must be different workers with different prompts. A persona reviewing its own output is the primary hallucination vector this design eliminates.
The `ASSUMPTION` convention in this table applies only to non-Research
artifacts. Research has no `ASSUMPTION` claim type. In Core 0.1.0, a persistent
research need must enter through `/research <slug> --request <request-file>
--confirm-request <sha256>` on Claude or `$research <slug> --request
<request-file> --confirm-request <sha256>` on Codex, followed by confirmation of
that exact normalized digest. The reserved
parent-work-order route is rejected before mutation.

## Context bundle format

Used by every phase that consumes upstream documents, including stories.

```yaml
context:
  - source: docs/architecture/techstack.md#git-hosting
    hash: sha256:ab12cd...
    excerpt: |
      Repos are hosted on GitHub. Default branch is `main`.
      Conventional commits are required.
  - source: src/auth/session.py#L40-L72
    hash: sha256:9f0e...
    excerpt: |
      class SessionStore: ...
```

Hash rule (deterministic, used by the sequencer's gate and Slice, `/amend`, `/drift`):

1. Resolve `path#anchor`. A heading anchor is the GitHub-style slug of a heading (lowercase, non-alphanumerics collapsed to single hyphens, trimmed); the section runs from that heading line up to, not including, the next heading of the same or higher level. A line anchor `#L10-L20` is that inclusive line range. No anchor means the whole file.
2. Normalise CRLF to LF. Do not strip trailing whitespace or re-indent.
2a. A heading line inside a fenced code block (``` or ~~~) is not a heading: it neither starts nor ends a section.
3. Split the file on LF (a file that ends with LF therefore yields a final empty line, which belongs to the last section); join the section lines with LF and append one LF. A section that ends the file thus hashes with two trailing LFs; every other section with one. This is what `run_conformance.section_digest`, `devforgeai.section_bytes` and `specs/verify.py` implement.
4. `sha256` over the UTF-8 bytes; record as `sha256:<64 hex>`.
5. Binary sources (PDF, images) are hashed over their exact retained bytes; page numbers or equivalent anchors are recorded separately.
6. A literal placeholder hash (`sha256:fixture...`, `sha256:PENDING`) is reported as `unresolvable-source`. The gate routes it through the artifact's `gate_policy.unresolvable_source` (`BLOCK` by default; `WARN` or `OFF` is legal only for `scope: hotfix`). `devforgeai phase start --lenient` downgrades only this class, is refused for any story under `docs/plan/`, and records every downgrade in `enforcement.gate_warnings[]`. A hash that resolves and differs is `stale-hash` and is never downgradable. Normative detail: `10-sequencer-and-contracts.md` section 3.4.

Rules:

- **Excerpt** so the consumer never opens the full document.
- **Anchor** so a human or `/amend` can find the origin.
- **Hash** so `/amend` and `/drift` can detect when the excerpt is stale.
- Slice copies the entry; it never summarizes and never re-excerpts. Summaries are hallucination surfaces.

## State file

`.devforgeai/state.yaml`

```yaml
version: 1
target: [claude, codex]
mode: greenfield | brownfield
slug: <project-or-feature-slug>
phase: plan
phases:
  init:      {status: done, at: 2026-09-01T10:00Z}
  onboard:   {status: skipped}
  brainstorm:{status: done, artifact: docs/brainstorm/<slug>.md, hash: sha256:...}
  pm:        {status: done, artifact: docs/PM/<slug>/prd.md, hash: sha256:...}
  architect: {status: done, artifacts: [docs/architecture/constitution.md, ...]}
  plan:      {status: in_progress}
active_sprint: sprint-001
stories:
  STORY-001:
    status: qa_failed          # ready | in_dev | dev_done | dev_blocked | review_failed | qa_failed | done
    sprint: sprint-001
    last_command: "/qa STORY-001"
    run: RUN-000012                # evidence home: .devforgeai/work/RUN-000012/
    reports:                       # rendered views, written by the sequencer at `phase next`
      qa: docs/reports/qa-STORY-001.md
      review: docs/reports/review-STORY-001.md
      dev: docs/reports/dev-STORY-001.md
runs:                              # one row per candidate root the sequencer opened
  RUN-000012:
    story: STORY-001
    skill: dev
    mode: worktree                 # worktree | copy
    root: .devforgeai/work/RUN-000012/wt
    base_ref: 4c1f9ab              # canonical HEAD pinned at `phase start`
    checkpoint: devforgeai/RUN-000012/green
    status: active                 # active | ready_to_promote | promoted | abandoned
next: "/dev STORY-001 --fix"
```

`/status` renders this file. Only the `devforgeai` sequencer writes it, and only at `phase start` (registering the run), at promotion or abandonment, and at `phase fail`; Research state is written only by Research Core. Canonical `state.yaml` carries no per-phase enforcement: `phase`, `fence`, `test_paths`, `granted_keys`, `lease` and `bounce_count` live in `.devforgeai/work/<run>/run.yaml`, which is gitignored and never promoted. Nothing inside a candidate root reads `state.yaml`; a worker reads `context.json` and the status block it was handed.

### Evidence home

There is one home for a run's evidence. The sequencer writes every file below except the judge findings under `evidence/<agent>/`:

| Path | Contents |
|---|---|
| `.devforgeai/work/<run>/run.yaml` | the run's enforcement: `phase`, `fence`, `test_paths`, `granted_keys`, `lease`, `bounce_count`, and the canonical root path. Gitignored |
| `.devforgeai/work/<run>/wt/` | the candidate root itself: a git worktree on branch `devforgeai/<run>`, or a copy of the project tree where the project is not a git repository. Producers write here; the sequencer creates, checkpoints, promotes and removes it. Gitignored |
| `.devforgeai/work/<run>/evidence/<agent>/` | the one place a judge writes: its findings file, named in the receipt's `evidence_refs`. Run-scoped, gitignored, never promoted |
| `.devforgeai/work/<run>/context.json` | the Slice output: the incoming artifact's context bundle as the gate resolved it, written once at `phase start` |
| `.devforgeai/work/<run>/<phase>-report.md` | the phase's narrative report, rendered from the worker receipt and the checkpoint diff |
| `.devforgeai/work/<run>/<phase>-result.json` | the accepted `devforgeai.worker-result/v1` plus `session_id`, the `changed[]` set the sequencer derived from the checkpoint diff, the checkpoint ref, and the transition verdict |
| `.devforgeai/work/<run>/handoff.json` | the handoff envelope for this run |
| `.devforgeai/provenance/log.jsonl` | one line per skill run |
| `.devforgeai/sessions/<session_id>.json` | the session evidence file, written once by the hook-only `session-start` operation |

`docs/reports/*` is a rendered view of the same evidence, written by the sequencer at `phase next`. No worker writes into either place: a producer writes only under the candidate root, and a judge only under `work/<run>/evidence/<agent>/`.

## Handoff contract

Every anatomy-governed skill run ends with a handoff. The sequencer writes `.devforgeai/work/<run>/handoff.json` at `phase next` and at `phase fail`; the block below is that file's rendering, and it is the only handoff the primary window prints. The envelope's field groups and schema are normative in `10-sequencer-and-contracts.md`.

Research follows its own typed handoff contract in `framework/skills/research/contracts/handoff.md` on the successful path. A Research failure returns a typed error and leaves staging evidence unsealed: it creates no canonical Research Handoff or receipt, and the sequencer renders the framework handoff from that typed error, taking its next steps from the error's repair route. Rule 1 therefore holds on every path. The user is never left asking "what's next?".

Rules enforced by the sequencer's renderer and checked by skill-validator:

1. **Next steps is never empty.** At least one exact, copy-pasteable command. Never "consider running..." or a description.
2. **Next steps are ordered.** Blocking items first (clarifications, fixes), then the forward command.
3. **One forward path.** If several commands are valid, list one as `1.` and the alternatives under "Also possible", so the default is unambiguous.
4. **Cold-session safe.** Every command works from a fresh session with no memory of this run, because it reads `state.yaml`.
5. **Failure handoffs name the owner.** A gate or critic failure says which skill owns the template and which command re-runs it.
6. **Where you are, where you came from.** The block shows the phase just completed, the phase now active, and the phases remaining, as a single line.
7. **Same block everywhere.** `/status` prints the same block from `state.yaml`; the run-end Handoff and the cold-session Handoff must not differ.

Each skill declares its handoff decision table in `skill.yaml` (`handoff.outcomes`); the sequencer selects the row by receipt status and fills the placeholders from state. The per-skill tables are in `02-skill-roster.md`.

## Handoff template

The rendering of `handoff.json`. Printed by every slash command on completion and by `/status` on demand.

```
DevForgeAI — You are here
────────────────────────────────────────────────────────────────
Project      <slug>                      Mode   brownfield
Progress     init > onboard > brainstorm > pm > architect > [plan] > dev > review > qa
Phase        plan (in progress)          Sprint sprint-001
Last action  /plan <slug>  — 12 stories written, 2 flagged by critic

Artifacts produced this run
  docs/plan/<slug>/epics/EPIC-001.md
  docs/plan/<slug>/stories/STORY-001.md … STORY-012.md

Open issues
  STORY-007  critic: acceptance criteria reference undefined API endpoint
  STORY-011  ASSUMPTION: rate limit value not in techstack.md

Next steps (run in a cold session)
  1. /clarify STORY-007
  2. /clarify STORY-011
  3. /dev STORY-001

Also possible
  /analyze <slug>        re-check traceability before starting dev
  /status                reprint this block
────────────────────────────────────────────────────────────────
```

## Provenance chain

`.devforgeai/provenance/` holds:

- `adr/NNNN-*.md` — architecture decisions, appended by architect and amend.
- `log.jsonl` — one line per non-Research skill run: `session_id`, run, skill, inputs, outputs, hashes, workers dispatched.

Research provenance lives in the sealed
`docs/research/<slug>/runs/RUN-NNNNNN/` dossier. A consuming artifact cites the
RUN plus applicable Source, Evidence, and Claim IDs and the sealed manifest
digest; a bare research hash is not a provenance reference.

Every artifact's frontmatter lists the provenance entries it depends on (`depends_on:`) and the template version it was written under. Gate checks one artifact on entry; `/analyze` walks the whole chain.
