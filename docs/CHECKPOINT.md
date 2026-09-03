# DevForgeAI progress checkpoint

Updated at the end of every wave. Newest entry first. Each entry says what exists, what is verified, what is open, and the decision the owner is asked to make at that check-in.

## Check-in 7 — 2026-09-03, write-model revision wave complete, wave 4 complete

**Made**: the candidate-root write model is applied everywhere. Docs 00-12 and the 29 templates describe per-role writes (`candidate | evidence | none`), one sequencer-owned candidate root per run (git worktree when the project is a repository, copied root otherwise, same contract), linear red → green → refactor checkpoints, receipts instead of file bodies, a lease bound at SubagentStart, explicit promotion (`devforgeai promote <run>`, never automatic, every run ends in two handoff blocks), dev → promote → review → qa per story, rewind to the checkpoint a phase started from, and blocked-run resume via `run.yaml#blocked_at`. Doc 10 gained section 12 (the candidate root); the enforcement schema became `run.schema.json`. The example sequencer implements all of it, including `candidate open|lease|checkpoint|promote|abandon`, and the demo runs the dev story green in copy mode and in worktree mode. Decision register for the wave: `docs/design/specs/WRITE-MODEL-REVISION.md` (D1-D12). All 18 specs revised, persona definitions made compilable, `depends_on` excerpts refreshed verbatim and hashes recomputed. Stale example spec and the cards directory deleted.

**Verified**: `verify.py` V1, V2, V3, V4, V8, V9 ok on 18 specs; conformance 197/197 (124 dispatcher, 35 grammar, 38 backstops); demo green in both modes; five schemas validate.

**Departures from Codex's text, for the owner**: worktree mode is the default only when git is present (copy mode is the non-git fallback, identical contract); the primary session stays in the canonical checkout while workers write in the root; the sequencer never commits on the target branch, so promotion is a local fast-forward with no push or PR; the clean detached verification worktree, overlapping-fence integration, sandbox and merge-queue promotion are PM-04, PM-11, PM-12, PM-13.

**Prerequisites for worktree mode in this checkout**: `.git` is empty (no repository); `.devforgeai/work/` must be ignored (init now installs `.devforgeai/work/.gitignore`); settings, hooks and `stack.yaml` must be tracked.

**Remaining**: the live scratch-project proof (no hook has fired from a real Claude Code or Codex session yet); Research Core blockers cited by SKILL-SPEC-018; then skill building with skill-creator from the specs.

## Check-in 6b (background job 1ac4ccc2) — 2026-09-02 night, standing down to avoid concurrent edits

**What this job did against the same plan (`~/.claude/plans/radiant-crunching-wombat.md`)**, all verified before hand-over: wave 0 refresh of 00-12 and templates; 10 and 11 plus five schemas; sequencer generalised to 18 skills with hook-only grammar, story-anchored qa/review, gate hash re-resolution, `--lenient`; fix-up 2 decisions (Slice performed by the sequencer at `phase start` into `work/<run>/context.json`; no nested skill calls, handoff-only; plan dependencies/estimates as field-restricted story writes; `evidence.verdict` selects report handoff rows; init writes `.devforgeai/` only before `state.yaml` exists); 01 rule 6 reworded to the `--lenient` behaviour. Evidence: `run_conformance.py` 151/151; `verify.py --only v1,v2,v4,v8` ok; demo green.

**Collision**: the interactive session (check-ins 4-6) is executing the same waves and has pivoted the write model to the candidate-root contract (`memory/devforgeai-write-model-worktrees.md`). This job's docs 05/09/10, the worker-result schema, the dev agent files and the cards still say blanket read-only workers. Reconcile in the revision wave: keep the Slice, no-nesting, field-restricted-write, verdict and init decisions (they are mode-independent); replace `files[].content` with `candidate` + `changed[]` per the pivot.

**This job stops here.** No cross-review, hash recompute or example deletion will be run from it. A coordination message was sent to session `skill-spec-format-design`; remaining waves belong to the interactive session.

## Check-in 6 (interim) — 2026-09-02 night, write model pivot to a candidate root

**Landed since check-in 5**: sequencer fix agent completed all six items (Research CLI admitted through hooks, `status` renders handoff, `sha256:PENDING` resolved at ingest, architect ADR carve-out, conditional plan phase, fenced-heading hash rule); conformance 151/151; demo green; V1, V2, V4, V8 ok. Persona audit agent finished but its report was lost to a context reset; it will be re-run as a write-capable pass after the write-model revision.

**Decision converging (Codex, a second Claude session, advisor, this session)**: per-role write permission; code-phase workers write complete files inside a sequencer-owned candidate root; red, green, refactor build linearly there; envelopes carry `candidate {id, base_ref, result_ref}` and `changed[{path, blob_sha256}]`, never file bodies; promotion is base-check-or-refuse (`STALE_BASE`, `MERGE_CONFLICT`). Two modes under that one contract: **local candidate mode** (copied root under `.devforgeai/work/<run>/candidate/`, no git needed) is the MVP; **worktree mode** (one persistent worktree per story run, commit/tag per transition, fast-forward promotion, disjoint-fence parallel stories) is the first upgrade, which the owner intends to enable soon; sandbox (PM-04) stays post-MVP. `state.yaml` splits into canonical story status and per-run enforcement inside the candidate root in both modes. Retracted: the earlier "worktree isolation is an MVP invariant" line. Awaiting Codex's commentary on persistent story worktree vs per-agent temporary worktrees (worktree-mode detail only).

**Worktree-mode prerequisites, not design blockers**: this checkout is not a git repository (`.git` is empty); `.gitignore` ignores only the three research dirs under `.devforgeai/`, so `.devforgeai/work/**` must be ignored; settings, hooks and `stack.yaml` must be tracked.

**Remaining**: revision wave over 05, 09, 10, 12, two schemas, specs 001/013/014, six dev agent files, sequencer (`snapshot` → candidate root, `restore_fence` → discard, root resolution, `candidate open|promote`, lock); persona pass; hash recompute; stale example deletion; full battery; live proof.

## Check-in 5 — 2026-09-02 late, wave 3 (cross-review) complete

**Made**: forward and backward cross-review of all 18 specs; 12 producer/consumer mismatches and 33 worker-tool contracts fixed; doc 11 registry corrected (amend produces the constitution set, validate-report consumed by skill-generator, drift no longer a constitution consumer, skill-generator subdir patterns); stale command forms in 01 and 02 corrected (`/plan {slug} --reslice {story}`, `/skill-gen {skill}`, no `--update`/`--resync`); conformance 146/146; V1, V2, V4 ok on 18 specs.

**Open decision, blocking wave 4**: the write model for code-phase workers. Two outside reviews (another Claude session; Codex pending) and this session agree that red, green and refactor must write and run tests inside their own loop, and that "every worker read-only" was an over-correction. Proposed contract: write permission per role; Claude code workers write in-tree inside the fence under a per-agent PreToolUse hook; Codex code workers write in a scratch copy the sequencer applies; document writers stay propose-and-apply; `devforgeai run <key>` callable by a worker whenever the phase grants the key. Docs 05, 09, 10, the dev/review/qa specs and the dev agent files change once the owner confirms.

**Running**: persona-subagent audit of all 18 specs against the Claude Code subagent docs; sequencer fixes (Research CLI admission, status renders handoff, PENDING digests resolved at ingest, architect ADR carve-out, conditional plan phase, fenced-heading hash rule).

**Remaining**: write-model revision; persona edits; hash recompute; delete the stale example; full battery; live proof.

## Check-in 4 — 2026-09-02 evening, wave 3 in progress

**Made**

| Layer | State | Evidence |
|---|---|---|
| Design docs 00-12 | Refreshed to one status vocabulary, one writer of `.devforgeai/` (sequencer), one evidence home, read-only workers on both providers, Research exempt, plan sole spec author, story v3, post-MVP roadmap in 12 | `python3 docs/design/specs/verify.py --only v2` ok |
| Contracts | 10 (grammar, statuses, phase tables for 18 skills, worker-result, handoff, stack.yaml, session, enforcement), 11 (registry: 18 skills, 29 templates, 78 edges), 5 schemas | V4, V8 ok; schemas pass check_schema |
| Templates | 29 under `docs/design/templates/`, headers checked | template check 29/29 |
| Sequencer prototype | `examples/hooks/`: 18-skill phase registry, gate re-resolves hashes, stack.yaml and ADR producer exceptions, review/qa story-anchored, session evidence | conformance 125/125, demo green |
| Skill specs | 18 of 18 written, 13,193 lines, `status: approved`, hashes `sha256:PENDING` | V1, V2, V4 ok |
| Author kit | AUTHOR-BRIEF, ANTI-CEREMONY, verify.py | |

**Running now**: sequencer fix (Research CLI admitted through hooks, `status` renders handoff, PENDING digests resolved at ingest, architect ADR carve-out, conditional plan phase, fenced-heading hash rule); forward and backward cross-review of the 18 specs.

**Remaining (wave 4)**

1. Recompute every `depends_on` hash (V3) after the cross-review lands; nothing may edit 00-11 or templates after that without a re-hash.
2. Delete `docs/design/examples/SKILL-SPEC-001-dev-tdd.md` (absorbed into SKILL-SPEC-001-dev).
3. Full battery: verify.py V1-V4, V8; conformance; `PYTHONPATH=python python3 -m pytest tests/research -q`.
4. Update this file and memory.

**Open decisions for the owner**

- Live proof: nothing in `examples/hooks/` has fired from a real Claude Code or Codex session. The one-hour scratch-project test is the next milestone after wave 4.
- Research Core blockers (docs/reviews/…review.md section 7) are prerequisites cited by SKILL-SPEC-018; unfixed.
- `.git` is empty. Nothing is version-controlled. Initialising it is the owner's call.

**Known limits recorded in specs**: one envelope carries at most 32 files (a plan with more stories splits by slug); worker `evidence` over 64 KiB fails; smoke to green rewind has no `rewind_to` yet.

## Check-in 3 — wave 2 (spec authoring), complete

Six Opus authors wrote 18 specs directly from docs 10 and 11 (assignment cards dropped as an unnecessary intermediate). Each author recorded its choices in section 9. Defects they surfaced were routed into the sequencer fix agent rather than left as prose.

## Check-in 2 — wave 1 (contracts and code), complete

10, 11, schemas; sequencer generalised from dev-only to all 18 skills; unified read-only-worker write model; 116 then 122 then 125 conformance rows. A wave-1a agent died to an API timeout before writing and was relaunched. Two agents believed killed by a session restart were still alive and completed their work; later agents were told to stand down when they saw concurrent writes.

## Check-in 1 — wave 0 (design refresh), complete

Decision register rows 1-17 applied to 00-09 and both templates; 12-post-mvp.md created. Forbidden-text grep clean.

## Check-in 0 — plan approved

Plan at `~/.claude/plans/radiant-crunching-wombat.md`. Owner decisions: full roster; read-only workers plus sequencer on both providers; Research exempt; plan owns skill specs; story v3 only; build required when compiled; post-MVP roadmap instead of an appendix.
