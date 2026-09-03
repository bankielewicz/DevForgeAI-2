# Write-model revision brief (candidate root), 2026-09-02

Status: applied 2026-09-03 (check-in 7). Kept as the decision register for the pivot; the normative text is 10 (sections 2, 3, 5, 12), 09 and 05. Superseded the "every worker is read-only, sequencer applies file bodies" text wherever it appears in 00–12, the templates, the schemas, the example sequencer and the 18 skill specs. Any later change goes into 10 first and is mirrored here only as a dated note.

## D1 Per-role write permission

Producers write; judges read. Producer roles: red, green, refactor and fix workers; every document writer (story, prd, adr, design, brainstorm, sourcetree, techstack, code_map, skill files, retro, drift, clarification, impact, validate reports and every other template-producing role). Judge roles: gate resolver, critic, reviewer, smoke/qa verifier, analyze, status. Judges have Read, Grep, Glob, `Bash(devforgeai status)`, and Write restricted to their own evidence directory `.devforgeai/work/<run>/evidence/<agent>/` (run-scoped scratch, gitignored, never promoted); a judge's findings file lives there and is named in `evidence_refs`, so `issues[]` stays a bounded summary and nothing large enters the primary context. This is Codex's 'read candidate checkpoint; write evidence only' row. Producers additionally have Edit, Write (Codex: `apply_patch`) and `Bash(devforgeai run *)` for the stack keys the phase grants. No worker ever has a git write, a package manager, a network tool, or a raw stack command. Worker headers declare `writes: candidate | evidence | none`.

## D2 The candidate root

Every anatomy-governed run gets one candidate root, created by the sequencer at `phase start` and owned by it until promotion or abandonment. Two materialisations, one contract; the sequencer picks by probing for a git repository at the project root and records `candidate.mode` in the run file.

| | worktree mode (default when the project is a git repository with at least one commit) | copy mode (fallback: no git repository, or fixtures) |
|---|---|---|
| create | `git worktree add -b devforgeai/<run> <root> <base_ref>`; `base_ref` = canonical HEAD at `phase start`, pinned in the run file | copy the project tree to `<root>` excluding `.git`, `.devforgeai/work`, and `stack.yaml#ignore_dirs`; `base_ref` = sha256 of the sorted tree-hash manifest |
| root path | `.devforgeai/work/<run>/wt` (gitignored) | same |
| checkpoint at each transition | commit on the run branch, tag `devforgeai/<run>/<phase>` | tree-hash manifest `<phase>.manifest.json` plus copy-aside of changed files under `.devforgeai/work/<run>/cp/<phase>/` |
| rewind to phase P (re-enter P, so reset to the checkpoint P started from: P's predecessor, `base` for red) | `git reset --hard devforgeai/<run>/<pred(P)>` inside the root, `base_ref` when P is the first phase | restore the copy-aside for pred(P) and delete files absent from its manifest |
| promote | refuse unless canonical HEAD == `base_ref` (`STALE_BASE`) and no dirty canonical file is among the candidate's changed paths, and no canonical path outside the change set became dirty since `candidate open` recorded `dirty_at_open` (`DIRTY_TARGET`, both forms); `git merge --ff-only devforgeai/<run>` run in the canonical checkout under the sequencer lock; the sequencer never commits on the target branch itself, so `state.yaml` edits are working-tree edits the owner commits with the story | refuse unless canonical tree manifest == `base_ref` (`STALE_BASE`); copy every changed path's exact bytes into the canonical tree under the lock, deleting paths the candidate deleted |
| abandon | `git worktree remove --force`, delete branch and tags | delete `<root>` and `cp/` |

The primary session stays in the canonical checkout. Workers receive `candidate.root` in their brief; every write they make must be under it; `devforgeai run <key>` executes with cwd = `candidate.root`. Claude's `isolation: worktree` and `EnterWorktree` are not used by the framework: they fork from HEAD and would split the linear history.

## D3 Linear history and the lease

For one run the phases build linearly on the same root: base → red → green → refactor → (review, qa read the refactor checkpoint). No merge exists between phases by construction. The run file records `lease: {session_id, agent, phase}`; exactly one producer holds the lease at a time, granted at dispatch and released at `ingest-result`. Judges never hold it and may run concurrently against a checkpoint.

Parallel stories: separate runs, separate roots, separate sessions (the Codex one-open-worker cap is per session). `phase start` refuses a story whose `write_fence` overlaps the fence of any run that is active or `ready_to_promote` (reason `FENCE_OVERLAP`). Promotion is serialised under `.devforgeai/lock`; the second promoter of two disjoint runs sees `STALE_BASE` and the sequencer, not the model, runs `git rebase <new HEAD>` inside the root, reruns the last transition oracle, then retries the fast-forward (worktree mode only; copy mode returns `needs_user`). Any rebase conflict: `git rebase --abort`, status `needs_user`, reason `MERGE_CONFLICT`. `FENCE_OVERLAP` counts producer-exception paths (`.devforgeai/stack.yaml`, `.devforgeai/provenance/adr/**`) as fence members, so two architect runs cannot both be active. Overlapping-fence integration, a clean detached verification worktree for qa/review, and the sandbox remain post-MVP (12).

## D4 The receipt (worker-result v1, breaking change, nothing shipped)

A worker's final message is exactly one JSON object:

```json
{"schema":"devforgeai.worker-result/v1","run":"<run>","skill":"<skill>","phase":"<phase>","agent":"<agent>",
 "status":"pass|fail|needs_user|could_not_run","reason_code":"runner_missing|timeout|network|hook_fault",
 "candidate":{"id":"<run>","input_checkpoint":"<phase-or-base>"},
 "claimed_paths":["<root-relative path>"],
 "evidence_refs":["<root-relative or .devforgeai/work/<run>/... path>"],
 "note":"","issues":[],"next":"<rewind_to>"}
```

Removed: `files[]`, `content`, `sha256_before`, `evidence` object. Added: `candidate`, `claimed_paths` (≤64), `evidence_refs` (≤16). Rules: non-pass carries empty `claimed_paths`; `next` requires `status: fail` and the registry `rewind_to`; `issues` ≤10; unknown keys refused. The sequencer, at `ingest-result`, derives `changed[{path, blob_sha256, kind: added|modified|deleted}]` from the checkpoint diff, refuses if `changed` is not a subset of `claimed_paths` or any path is outside the fence (or, for red, outside `test_paths`; for green/refactor, touches a test path whose hash changed since red), runs the transition oracle in the root, writes `<phase>-result.json` with `changed` and the checkpoint ref, creates the checkpoint, releases the lease, and advances. Handoff `artifacts[]` entries gain `checkpoint` and keep `sha256`.

## D5 State split

Canonical `.devforgeai/state.yaml` (tracked) holds story statuses, `runs: {<run>: {story, skill, mode, root, base_ref, checkpoint, status: active|ready_to_promote|promoted|abandoned}}` and nothing per-phase. Per-run enforcement (`phase`, `fence`, `test_paths`, `granted_keys`, `lease`, `bounce_count`) lives in `.devforgeai/work/<run>/run.yaml` (gitignored). Root resolution is a two-marker rule: walk up from cwd to the nearest `.devforgeai/`; if it contains `run.yaml`, cwd is inside a candidate root and the canonical root is the path recorded in `run.yaml#canonical`; otherwise cwd is canonical and the active run is `state.yaml#runs` filtered to `active`. Hook processes may pass `--run <id>` explicitly. Nothing inside a candidate root ever reads `state.yaml`: workers read `context.json`, the sequencer reads canonical state by the recorded path. The sequencer never commits on the target branch; canonical `state.yaml` edits are working-tree edits. Canonical state is written only at `phase start` (register run) and promotion/abandon, under the lock. The sequencer is the sole writer of canonical `.devforgeai/**`; producer-exception paths (`.devforgeai/stack.yaml`, `.devforgeai/provenance/adr/**`) are written by workers inside the candidate root and reach canonical only by promotion.

## D6 Hooks (09)

The lease is bound at SubagentStart, the only identity-bearing pre-write event on both providers: to `agent_id` on Claude, to the start event's identity on Codex. Check 6 becomes: a write tool is allowed for a judge only under `.devforgeai/work/<run>/evidence/<agent>/`; for a producer, when a run is active, the lease is held (Claude: PreToolUse `agent_id` equals the lease; Codex: path-under-root only, since PreToolUse carries no identity and the root is the fence), and the canonical path is under `candidate.root` and inside the fence for the current phase. Outside the root: deny. In the primary window: deny as today. Check 7 keeps the single-argv rule; `devforgeai run <key>` allowed to the lease holder. Git: read-only subcommands (`status`, `diff`, `log`, `show`, `ls-files`, `blame`) allowed inside the root; every mutating subcommand denied to workers and the primary. SubagentStop ingests the receipt as before. Worktree-mode prerequisites at SessionStart self-test: git present, HEAD exists, `.devforgeai/work/` ignored, `.claude/settings.json` (or `.codex/` config) and `stack.yaml` tracked; failure of any is `could_not_run: hook_fault` for `phase start`, not a silent fallback to copy mode.

## D7 Grammar additions (10 section 2)

Model-callable: unchanged four plus `devforgeai promote <run>`. Promotion is never automatic (10 §5.4, §12.4): the last passing transition marks the run `ready_to_promote` and writes a `REQUIRE_HUMAN` handoff whose only forward step is `devforgeai promote <run>`; the compiled SKILL.md runs that command only after the user confirms in the session. Every run therefore ends in two handoff blocks: ready, then promoted. Hook-only: `candidate open <run>` (called by `phase start`), `candidate checkpoint <run> <phase>`, `candidate promote <run>`, `candidate abandon <run>` (called by `phase fail --reason` when the policy says abandon). Exit codes unchanged. New refusal reasons: `STALE_BASE`, `MERGE_CONFLICT`, `DIRTY_TARGET`, `FENCE_OVERLAP`, `LEASE_HELD`, `UNCLAIMED_CHANGE`, `NO_CANDIDATE`. The fifth model-callable form propagates everywhere the four are enumerated: 09 static rules ("exactly the four forms" becomes five), dispatch check 8, conformance rows, `settings.claude.json`, `config.codex.toml`, `hooks.codex.json`.

## D7a Schema and file change set

`worker-result.schema.json`: D4 shape. `handoff.schema.json`: `artifacts[].checkpoint`. `stack.schema.json`: add `ignore_dirs` (array of root-relative dirs excluded from copy mode and tree hashing). `enforcement.schema.json`: becomes the schema of `.devforgeai/work/<run>/run.yaml` (rename the file to `run.schema.json`, update every reference). `session.schema.json`: add `lease` events. `state.yaml` example in 10: add `runs`.

## D8 Post-MVP moves (12)

Into 12: clean detached verification worktree for qa/review; automated integration run for overlapping fences / `STALE_BASE` in copy mode; sandbox (PM-04 stays); PR/merge-queue promotion (rung 4). Out of 12: nothing (worktree isolation was never a listed PM item; 04:122 line is rewritten, not moved).

## D8a Judges and evidence

Judges keep `Bash(devforgeai status)` and evidence-directory Write only (D1). The sequencer runs every oracle at `ingest-result`; smoke/qa verifiers read the oracle output the sequencer wrote under `.devforgeai/work/<run>/` and never run a stack key themselves. If a spec's judge needs a run key, that is a spec defect to fix, not a reason to widen D1.

## D9 Worker prompts

Lead with the job. Producers: "You write … inside the candidate root `{{candidate.root}}` using Edit/Write; run `devforgeai run <key>` whenever you need the tests; finish with the receipt." Never say "you do not write". Judges: "You judge …; you write nothing; finish with the receipt." Every `agents/<role>.md` body follows templates/agent-md.md: job, inputs, rules, receipt. `{{candidate.root}}` and `{{run}}` come from the `devforgeai status` block the primary pastes into the dispatch prompt; the block names `run`, `candidate.root`, `phase`, `fence`, `granted_keys`.

## D10 Mode-independent decisions already landed by the parallel fix-up job (keep, and remove residual contradictions)

1. Slice is a sequencer step inside `phase start`: it writes `.devforgeai/work/<run>/context.json`. There is no context-curator worker. Remove residual mentions of a curator worker or "one extra Slice agent file" from 03, 04, 06, the templates and every spec.
2. No nested skill calls. "Calls" became "Hands off to" in 02; the five call edges are handoff rows and `via: handoff` edges in 11. Specs must not describe one skill invoking another.
3. plan `dependencies` and `estimates` are field-restricted story writes (`blocked_by`, `size`, `sprint` only); phase order stories → dependencies → estimates → sprints.
4. Report-producing phases (review, qa, skill-validator) select their handoff row from a closed `evidence.verdict` (`pass|findings|fail`) carried in the receipt's `evidence_refs` target report; run status stays `pass`.
5. init writes `.devforgeai/` directly only while no `state.yaml` exists; the dispatcher denies it afterwards.
6. The story gate re-resolves every provenance and context hash (`stale-hash` never downgradable); `--lenient` downgrades only `unresolvable-source`, refused under `docs/plan/`.
7. qa and review runs are story-anchored and carry the story's commands, test_plan and gate_policy.
8. ADR ids stay `^ADR-[0-9]{4}$` with `NNNN-<slug>.md`.

## D11 Acceptance gate for this wave

`verify.py --only v9` must pass: no file under docs/design (except 12 and this brief), schemas/ or examples/hooks may contain `files[]`, `files[].content`, `"content":`, `sha256_before`, `read-only worker`, `context-curator`, `context curator`, `one extra Slice agent`, `--detach`, `applies the files`, `apply the files`, `full file text`; `isolation: worktree` may appear only in 04's fact table and 12. `demo_sequencer.sh` runs the dev story once in copy mode and once in worktree mode (it `git init`s a scratch copy of the fixture) and both end green; conformance grows rows for `promote`, `STALE_BASE`, `FENCE_OVERLAP`, `LEASE_HELD`, `UNCLAIMED_CHANGE`, `DIRTY_TARGET`, and the lease-bound write check on both providers.

## D12 Review and qa run after promotion (settles a conflict between 10 §2 `STORY_IN_FLIGHT` and specs 002/003)

`review` and `qa` do not attach to the `dev` run's unpromoted root. Order per story is dev → `devforgeai promote <run>` → review → qa, each a run with its own candidate root created from canonical HEAD, so review and qa judge the promoted code in a clean root (this is the MVP form of Codex's "clean verification worktree"; the detached read-only variant stays PM-11). `STORY_IN_FLIGHT` therefore holds as written: `phase start review|qa <story>` is refused while that story's dev run is `active` or `ready_to_promote`, and the dev handoff's forward step is `devforgeai promote <run>` followed by `/review {story}`. Review or qa findings that need code changes route to a new dev run (`/dev {story}` with the report as context), never to edits in the review root. One run per story at a time, one root per run.

## D13 Judges return findings in the receipt; the sequencer persists them (2026-09-03, supersedes the `writes: evidence` amendment to D1, D6, D8a)

Observed on Claude Code 2.1.259 (eval 1 of the generated dev skill, then a direct probe): a subagent's Write of a report-like Markdown file is refused by the provider before any hook runs, with `Subagents should return findings as text, not write report files. Include this content in your final response instead.` `findings.json` and `notes.txt` in the same directory succeed. The heuristic is undocumented and must not be relied on in either direction.

1. Judges (critics, reviewers, smoke/qa verifiers, analyzers, gate resolvers) declare `writes: none` and receive no `Write`, `Edit` or `apply_patch` tool. The `writes` enum is `candidate | none` again; `evidence` is removed everywhere.
2. `devforgeai.worker-result/v1` gains `findings`: a string, required on a judge receipt, forbidden on a producer receipt, at most 16,384 UTF-8 bytes. `issues[]` stays the bounded routing summary (at most 10); `findings` carries the detailed evidence. The sequencer truncates neither; an oversize `findings` is refused like any other receipt defect.
3. At the identity-bound `SubagentStop`, after validating the receipt, the sequencer writes the decoded `findings` verbatim to the fixed path `.devforgeai/work/RUN/evidence/AGENT/findings.md` (RUN and AGENT are the run id and the agent name). The worker cannot choose the path or the name. This is persistence of a returned result, not merging of a snippet into the tree. The next phase's worker reads that file by path; the handoff and `PHASE-result.json` reference it.
4. Documentation correction: the bounded `findings` body necessarily enters the primary context as part of the subagent's result, exactly as the provider model states (a subagent returns its result to the parent; a hook can validate the final message but cannot suppress it). What stays isolated is the worker's transcript, its file reads, its tool traffic and its intermediate reasoning. Every sentence claiming "no file body enters the primary context" is replaced by that statement; the design still forbids producers from returning file bodies, and receipts still carry no code.
5. No workaround via `findings.json`, `notes.txt` or a Bash redirect. A judge that is refused a write has no write to make.
6. Taxonomy: new worker reason code `provider_tool_refused` (the provider refused a tool call before any DevForgeAI hook ran), rolling up to `INFRA_FAILURE`. `hook_fault` stays reserved for missing hook identity or a malformed receipt. Taxonomy version stays 1 with the code added (the draft is unreleased); the YAML, its schema, `worker-result.schema.json`, doc 10 section 3 and doc 13 carry it.
7. Handoff-row selection is implemented, not defaulted: a phase's refusal names its row from the skill's section 7f table (registry `handoff` rows in `policy.py`), so red's "a planned test already passes" routes to `/clarify STORY`, as spec 001 section 7f states. The eval-3 expectation stands; the sequencer was wrong.
8. Acceptance for this change: a fresh-session test proves a non-empty judge receipt is persisted at the fixed path, the candidate and canonical trees are unchanged by the judge, and the next phase's worker consumes the persisted file; then the three dev-skill evals rerun at 7/7, 4/4, 5/5. PR 7 is held until then.
9. A structured evidence-broker tool that keeps large findings out of the parent result is a later contract, listed in 12, and is not part of this one until implemented and proven live on both terminals.

## D14 Spec defects surfaced by the first skill-creator build of SKILL-SPEC-001 (2026-09-03)

The generator reported "SPEC GAPS: none" and then listed seven deviations. Each is a specification defect to fix in the spec, not a generator choice:

1. Section 10 eval workspaces must include the compiled `.claude/agents/dev-ROLE.md` files (section 7g shape); the Agent tool cannot dispatch a worker without them.
2. Section 7a step 4 and the three-part dispatch prompt rule conflict on `--fix` inputs: define exactly how the fix report path reaches the worker (the `devforgeai status` block prints `fix_report` when `run.yaml#fix_report` is set; the prompt still carries only story id, status block, phase line).
3. `assets/dev-notes.md` must be the registry template with its placeholders, and section 14's forbidden-text grep must exclude `assets/` (templates carry placeholders by design); state whose status vocabulary is authoritative.
4. Agent frontmatter: section 7g's four keys versus `templates/agent-md.md`'s `responsibility` and `must_not` requirement conflict; section 7g is corrected to the template's full key set.
5. `references/PHASE.md` may carry a one-line `# PHASE` heading above the verbatim section 7d text; say so.
6. `metadata.provenance.hash` is computed with the doc 01 section rule over section 3; say so instead of the placeholder sentence.
7. `evals/evals.json` lives in `out/dev/evals/` and is excluded from the installed skill; section 8's layout lists it as build-time only.

8. (added after live run 3) A custom subagent's `tools:` frontmatter accepts tool names and MCP server patterns only (Claude Code subagents reference, 2026-09-03); `Bash(devforgeai status)` or `Bash(devforgeai run *)` written there does not restrict commands. Every agent file and section 7g lists `Bash` and states that the hook dispatcher bounds it per role: a judge may run `devforgeai status` and the dispatcher's read-only command set (`cat cmp cut diff echo grep head jq ls pwd rg sha256sum tail test tr wc`, plus read-only git subcommands inside the root); a producer additionally runs `devforgeai run KEY` for its granted keys. `allowed-tools` in SKILL.md frontmatter does accept permission patterns and keeps the five-form grammar.
9. (added after live run 3) The read-only command set above is part of the judge contract and is named in section 7e/7g and in doc 05, not left implicit in the dispatcher.

Also from the eval transcripts, two SKILL.md defects: every dispatch and every sequencer call is the bare command with no `; echo` or redirect (the dispatcher's single-argv rule denies compounds), and on any block or refusal the skill prints the handoff and stops; it never inspects hook files, sequencer sources or logs, never messages other sessions and never writes memory.

## D15 `--fix` in the grammar; clarify exempt from STORY_IN_FLIGHT; resume re-gates (2026-09-03)

`devforgeai phase start` now reads `<skill> <arg> [--fix] [--lenient]`, and those two options are the whole of what it accepts: `--fix` is legal for a story skill only, records the newer of `docs/reports/qa-<story>.md` and `docs/reports/review-<story>.md` as `run.yaml#fix_report`, is refused `NO_FIX_REPORT` when neither exists, and is printed as `fix_report` in the `devforgeai status` block that the primary pastes into the dispatch prompt (extending the D9 field list); the red oracle's narrowing under fix mode is unchanged, and the runnable draft's failure to read `fix_report` stays noted where 10 section 4 "Fix mode" states it. `clarify` is exempt from `STORY_IN_FLIGHT`, narrowing D12's "one run per story at a time" for that skill alone: a dev run that is blocked (`run.yaml#blocked_at` set, no lease) may have `/clarify <story>` opened against the same story, because clarify's fence is the story document under `docs/plan/` and not the code the blocked run holds, while `review` and `qa` stay refused and `clarify` itself stays refused against a story whose run is running, holds a lease, or is `ready_to_promote`. Because clarify can rewrite the story under a blocked run, resuming `phase start dev <story>` on a blocked run whose story file no longer hashes to `run.yaml#story_sha256` re-runs the whole story gate and re-slices `context.json` before re-entering `blocked_at`; if that gate refuses, nothing is reset and the run stays blocked with the gate's reasons. The `/clarify <arg>` handoff rows in 10 section 6 therefore no longer prepend `devforgeai phase fail`.
