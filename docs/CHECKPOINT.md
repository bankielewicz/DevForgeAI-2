# DevForgeAI progress checkpoint

Updated at the end of every wave. Newest entry first. Each entry says what exists, what is verified, what is open, and the decision the owner is asked to make at that check-in.

## Check-in 12 — 2026-09-03, live dev-loop proof prepared

**Made**: scratch project `~/Projects/dfai-proof` (separate git repo, not part of this repository): the Python dev-tdd fixture, `stack.yaml`, the prototype sequencer/dispatcher/policy installed at `.devforgeai/hooks/`, the prototype `settings.claude.json`, the five dev worker agents compiled into `.claude/agents/` (placeholders replaced), a hand-written `dev` skill to the corrected template (66 lines, six-field frontmatter), `PROOF.md` (what to run and watch) and `collect.sh` (evidence gatherer). A `devforgeai` wrapper on PATH (`~/.local/bin/devforgeai`) locates the project-local sequencer by walking up from cwd; it replaced a dangling symlink to the legacy `.venv`.

**Dry run on a throwaway copy, scripted events only**: SessionStart armed (candidate_mode=worktree); `phase start dev STORY-001 --lenient` opened a worktree root and phase red; SubagentStart bound the lease and injected the worker brief; PreToolUse allowed a write inside the root and denied one outside with the reason; `phase fail` abandoned cleanly. No model was in the loop.

**Awaiting the owner**: open Claude Code in `~/Projects/dfai-proof`, run `/dev STORY-001 --lenient`, confirm promotion, then say "collect" here.
**Live run 1, result (2026-09-03 17:52–17:57)**: the gate opened, the worktree root was created, `red_dev` was dispatched and its lease bound (agent_id recorded). 31 s later a `SubagentStop` with an `agent_id` and no `agent_type` arrived; the dispatcher treated it as the worker's stop with missing identity, recorded `hook_fault`, blocked the run and released the lease, so every later write, `devforgeai run test` and receipt from the real worker was refused. The same shape appeared in this repository's hookd log: dozens of `SubagentStop` events with distinct `agent_id`s and no `agent_type`, every 10–30 s while Opus agents ran. They are Claude Code's internal helper subagents (most likely the auto-mode classifier). **Fix**: the dispatcher ignores `SubagentStart`/`SubagentStop` without `agent_type`; a conformance row pins it (207/207 rows hold (124 dispatcher, 35 grammar, 48 backstops)); the sequencer records every hook event's shape in `.devforgeai/sessions/raw-events.jsonl`; the `hook_fault` handoff now points at that log instead of "install the missing runner". The proof project is reset for run 2.

**Live run 2, result (2026-09-03 18:13–18:43, session ce63b288): the dev loop ran end to end with a real Claude Code session.** Gate opened a worktree root; five workers dispatched in order (red_dev, green_dev, refactor_dev, smoke_qa, dev_critic), each bound its lease at SubagentStart and returned a receipt the SubagentStop hook ingested; the sequencer ran the oracle at every transition (red: TEST_FAILURE from the worker's own `devforgeai run test`, then EXPECTED_TEST_FAILURE at ingest; green and refactor: PASS on `test`, refactor also PASS on `lint`); five checkpoints committed on the run branch; `ready_to_promote` handoff; the owner confirmed and `devforgeai promote` fast-forwarded the canonical tree, removed the root, and rendered `Next: /review STORY-001`. Canonical tree now has `tinyapp/text.py` and `tests/test_text.py` with the three named tests passing. 178 raw hook events: 105 typed PreToolUse, 22 identity-less helper SubagentStops (all ignored by the fixed dispatcher), no hook fault, no deny during the run. Duration about 30 minutes, of which green took 8. This is the first evidence that the design works in a plain terminal on a Max plan; it proves the Claude side of the dev loop, one story, Python stack, worktree mode. Not yet proven: `--fix`, rewind under a real worker, Codex, any other skill.


## Check-in 11 — 2026-09-03, language-neutral fixture conversion (Node) and JUnit normalization

**Made**
- `docs/design/examples/fixtures/dev-tdd-node/`: dependency-free `package.json` (`"type": "module"`), `tinyapp/text.mjs`, empty `tests/`, and a story anchored to `.devforgeai/stack.yaml#node` with the same three criteria and test names as the Python control (`test_slugify_basic`, `test_slugify_unicode`, `test_slugify_empty`). Python fixture tree unchanged (README mention only).
- `stack.yaml` gains a `node` section (direct `node --test --test-reporter=junit --test-reporter-destination=...` argv, `node --check` lint, no npm ever) and a new optional per-section key `junit_dialect: generic | pytest | node` (schema, template, doc 10 §3 and §7).
- Sequencer: a deterministic runner-normalization boundary (`normalize_junit`) behind `junit_dialect`, monotone toward refusal: a failure without an assertion marker becomes `error`, a file-named testcase is a collection error, an empty file is `NO_TESTS`. Generic dialect is byte-for-byte the old behaviour. Live probing showed the old reader let a thrown ReferenceError (node) or NameError (pytest) satisfy the red gate; eight new conformance rows pin the six hostile cases plus honest node red and green.
- Demo runs four complete stories (python and node, copy and worktree), each asserting exact test names and outcomes in the JUnit file, frozen red hashes through green and refactor, lint, promoted refactored code, a sha256 tree diff (fence files, `.devforgeai/**`, `docs/reports/**` only), and for node the absence of `node_modules`, lockfiles and any package-manager or fetcher token in the resolved argv. A missing `node` reports `COULD_NOT_RUN` and fails the demo; never a silent skip.

**Verified**: `DEMO OK: python copy/worktree green, node copy/worktree green`; conformance 206/206 (124 dispatcher, 35 grammar, 47 backstops); verify.py V1–V4, V8, V9 ok, hashes recomputed; six schemas validate.

**What this proves and does not**: two interpreted ecosystems run through the same stack-selected workflow with the same oracle. It does not prove compiled-stack support (Rust needs a non-JUnit result parser; C# needs a network restore), arbitrary Node-version compatibility, or automatic stack detection.

**Known limits recorded**: `node --check` accepts one path, so lint covers `tinyapp/text.mjs` only; the node dialect treats a leaf test literally named like a file as file-level (fails closed either way); `runner_probe` is declared but not yet invoked by the sequencer; no `commands.format` for node; network isolation is structural, not enforced.

**Addendum (skills-guide conformance, 2026-09-03)**: spec 001's skill design was checked against Anthropic's "Complete Guide to Building Skills for Claude". Structure, naming, description, progressive disclosure, specificity, error handling, examples and testing conform. Fixed: `templates/skill-md.md` now requires `compatibility` and `metadata`, carries `allowed-tools` as the skill's Bash grammar, and puts `provenance` under `metadata` (the top-level key would have failed skill-validator's six-field rule); the Identity section opens with the two critical rules; spec 001 and doc 11's registry row updated. `agents/` is documented as a DevForgeAI extension of the standard layout.

## Check-in 10 — 2026-09-03, defect pass and error-taxonomy draft

**Made**
- Reference hook component: `bash_guard` now matches per command segment with heredoc bodies removed and patterns anchored at command position; interpreter escapes (`bash -c`, `eval`) moved to the ask list; deny reasons name the pattern, never the command text. Tests 19/19 (three new: heredoc mention passes, denied command after `&&` caught, `bash -c` asks). Installer no longer appends gitignore lines when `.claude/` is already ignored. Reinstalled locally.
- Prototype settings (`docs/design/examples/hooks/settings.claude.json`): `Write(...)` rules removed (the host consults `Edit(path)`/`Read(path)` only); every path rule anchored with `/` at the settings source instead of the session cwd.
- Sequencer: `candidate open` records the canonical dirty set (`run.yaml#candidate.dirty_at_open`, worktree mode); `promote` refuses `DIRTY_TARGET` when a canonical path outside the run's change set became dirty during the run, closing the hole a fail-open hook or an unseen subprocess leaves. Sequencer-owned `.devforgeai/` paths are excluded. New conformance row; doc 10 §2 row, §12.4 step 3, brief D2 and `run.schema.json` updated.
- Doc 12 PM-04: the Codex `workspace-write` sandbox bounds the session workspace, not the candidate root (per-agent TOML sets `sandbox_mode` only); the root fence on Codex is the hook's path check unless the Codex session runs from the worktree. Memory corrected.
- Withdrawn: the `hookSpecificOutput.decision.behavior` item from check-in 8; it is the PermissionRequest output shape, used only on that event.
- Error taxonomy draft, per the owner's placement decision: normative `framework/contracts/error-taxonomy.yaml` (`taxonomy_version: 1`), `framework/contracts/README.md` with install guidance for the future installer (destination `.devforgeai/contracts`, verbatim copy, digest pin, install before hooks), `schemas/devforgeai/v1/error-taxonomy.schema.json` (forbids `allow`), narrative `docs/design/13-error-taxonomy.md`. Every existing code kept verbatim; new layers are the phase-outcome roll-up (COMPLETE, NEEDS_DECISION, BLOCKED, FAILED, COULD_NOT_RUN, INFRA_FAILURE, per research D-023) and the hook failure classes. Three open items recorded for version 2. `install-manifest.yaml` untouched.

**Verified**: hookd tests 19/19; demo green in copy and worktree modes; verify.py V1–V4, V8, V9 ok with hashes recomputed; taxonomy validates against its schema; conformance 198/198 rows hold (124 dispatcher, 35 grammar, 39 backstops).

**Not done**: the manifest entry for `framework/contracts` (manifest owner); the receipt-bounce live probe; language-neutral fixture conversion (next).

## Check-in 9 — 2026-09-03, first live hook proof

**Made**: hookd installed into this repository from `components/hook-runtime/reference/claude-python/install.sh` (staged: self-test, audit and receipt first; protect_paths and bash_guard enabled after the audit line was observed). `.claude/settings.json` now carries one hookd entry per event; `.claude/hooks/` holds the dispatcher, checks and policy; log and receipts are gitignored.

**Observed live in session b6bbdd44 (first DevForgeAI hooks ever to fire from a real Claude Code session)**: PreToolUse Edit on `CLAUDE.md` denied with reason `CLAUDE.md is protected (rule CLAUDE.md)`, file unchanged; PreToolUse Bash on a forced-push dry run denied by bash_guard before execution; PostToolUse Write logged with the session id; SubagentStop fired for an Explore subagent with `agent_id` and `agent_type` populated and the receipt check passing through. Deny latency 0.1 to 0.2 ms. Hook config changes were picked up without a restart.

**Observed limit**: bash_guard scans the whole Bash command text, so a heredoc whose body merely mentions a denied command is denied too (a false positive hit while writing this entry). Fix for the cookbook: match patterns against command positions (first token of each pipeline segment), not the full text.

**Not yet observed**: SessionStart context (needs a new session); the receipt bounce on a listed agent (no listed agent exists in this repo yet); Codex.

**Consequence**: the hook layer moves from "documented" to "observed" for Claude Code on the four events the sequencer design uses. The candidate-root sequencer itself is still unproven live.

## Check-in 8 — 2026-09-03, hook cookbook proof of concept

**Made**: `components/hook-runtime/reference/claude-python/` (relocated from `poc/hooks/` on 2026-09-03 after layout commit 0cf4656) — one dispatcher (`hookd.py`) registered once per event, an explicit check registry, five checks (SessionStart self-test, protected-path fence with symlink and redirect handling, Bash deny/ask guard, PostToolUse audit, SubagentStop receipt bounce), `policy.json`, a check template, `install.sh` (idempotent merge into `.claude/settings.json`, gitignores runtime files), `settings.claude.json` snippet and `COOKBOOK.md` (protocol per event, failure policy, add-a-check recipe, twelve best practices tied to doc facts and claim IDs, live smoke test).

**Verified**: `python3 components/hook-runtime/reference/claude-python/tests/run_tests.py` 16/16 (pass-through, path deny, symlink deny, redirect deny, outside-project deny, command deny, `ask`, SessionStart context, receipt accept/reject/ignore, critical exception fails closed, malformed stdin fails closed, alarm beats host timeout, log without bodies); install tested on an empty-settings scratch project. Doc facts re-read 2026-09-03: `permissionDecision` is `allow|deny|ask` and `allow` bypasses the permission prompt; `last_assistant_message` on SubagentStop; `agent_id`/`agent_type` on PreToolUse inside subagents; exit 2 keeps a subagent working; only `Edit(path)`/`Read(path)` permission rules are consulted; bare relative rule paths anchor at the session cwd.

**Defects found in the older prototype** (`docs/design/examples/hooks/`): `settings.claude.json` carried `Write(...)` rules the host ignores and bare relative deny paths (fixed 2026-09-03: Edit rules only, `/path` anchoring). The `hookSpecificOutput.decision.behavior` form in `dispatch.py` was re-checked: it is the PermissionRequest output shape, used only on that event, not a PreToolUse defect; withdrawn.

**Not done**: nothing has fired from a live session. Installing hookd into this repository is the live proof and awaits the owner's go; this repo's `.claude/settings.json` is currently zero bytes, so install replaces it with valid JSON.

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
3. Full battery: verify.py V1-V4, V8; conformance; `PYTHONPATH=components/research-core/src python3 -m pytest tests/research -q`.
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
