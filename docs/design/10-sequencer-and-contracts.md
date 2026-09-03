# Sequencer and Contracts

Status: normative, 2026-09-02. This document closes the contracts every skill specification is written against: the sequencer's command grammar, the status vocabulary and its defect-to-action map, the per-skill phase registry, the worker receipt, the handoff envelope, `stack.yaml`, the session evidence file, the per-run enforcement file, and the candidate root every run's writes happen in. `09-hook-dispatcher.md` states the actor boundary; this document states what the deterministic side of that boundary accepts and produces.

The runnable implementation is `examples/hooks/devforgeai.py` with `examples/hooks/policy.py`. Where this document and that code differ, the code is the defect.

Section 12 is the candidate root: where a producer's writes land, how a phase transition is checkpointed, and what promotion checks before a byte reaches the canonical tree. Sections 2, 5 and 9 assume it.

| Schema | File |
|---|---|
| `devforgeai.worker-result/v1` | `schemas/devforgeai/v1/worker-result.schema.json` |
| `devforgeai.handoff/v1` | `schemas/devforgeai/v1/handoff.schema.json` |
| `stack.yaml` section | `schemas/devforgeai/v1/stack.schema.json` |
| `devforgeai.session/v1` | `schemas/devforgeai/v1/session.schema.json` |
| `.devforgeai/work/<run>/run.yaml` | `schemas/devforgeai/v1/run.schema.json` |

## 1. Principle

The model dispatches; the sequencer decides. A deterministic command owns everything under canonical `.devforgeai/`: the per-run enforcement file, captured receipts, phase reports, checkpoints, the handoff envelope, session evidence, and the provenance log. It also owns the candidate root each run's producers write in, from its creation at `phase start` to its promotion or abandonment. A worker returns exactly one `devforgeai.worker-result/v1` receipt; the sequencer validates it, derives what actually changed from the checkpoint diff, runs the transition oracle inside the root, and advances, retries, or rewinds.

Five consequences are load-bearing for every skill specification:

1. **No worker holds a literal command.** A phase names a command key. The sequencer resolves it from the hash-pinned `stack.yaml` section the run anchored at its gate; a producer that needs the suite runs `devforgeai run <key>`, which executes with cwd = `candidate.root`, and the sequencer re-runs the same key at the transition.
2. **No worker writes a canonical byte.** A producer writes real files with Edit and Write, inside the candidate root and inside the fence, under a lease bound to its own start event. Those bytes reach the canonical tree only through `devforgeai promote <run>`, which refuses on a moved base. A judge writes into one place and no other: its own findings directory under `.devforgeai/work/<run>/evidence/<agent>/`, which is run-scoped, gitignored and never promoted. Neither role can touch a tracked file that a promotion has not moved.
3. **The receipt is a claim, not a record.** A worker names the paths it believes it touched; the sequencer derives `changed[]` from the diff between the input checkpoint and the root as it stands, and refuses any change the receipt did not claim. Nothing a worker says about the tree is taken on trust.
4. **A report never substitutes for evidence.** Every transition diffs the root against its input checkpoint and re-runs the package and import policy over all matching files. A worker's claim that tests pass is not why a phase advances.
5. **The grammar is closed on two axes.** Five operations are model-callable from the primary window; `devforgeai run <key>` is callable by the lease-holding producer and by the sequencer inside a transition, and belongs to neither set alone; the remaining seven are hook-only and require the `DEVFORGEAI_HOOK_EVENT` marker. There is no operation that writes a report, and there is no operation that installs the framework: installation is the deterministic work of the installer skill, outside this grammar.

## 2. CLI grammar

Closed set. `Access` is `model` when the operation may appear in a provider Bash allowlist for the primary window, `worker (lease)` when only the producer currently holding the run's write lease may call it, and `hook (<event>)` when the sequencer refuses it unless `DEVFORGEAI_HOOK_EVENT` names that event. Exit codes are uniform: `0` ok, `1` refused, `2` usage, `3` could_not_run.

| Op | Args | Preconditions it enforces | Writes | Exit codes | Access |
|---|---|---|---|---|---|
| `devforgeai status` | none | none | nothing | `0` | model |
| `devforgeai phase start` | `<skill> <arg> [--lenient]` | skill is known and its kind is `story` or `document`; no run is already active in this checkout, except a blocked run (`run.yaml#blocked_at` set, no lease) with the same skill and argument, which this call resumes; no `active` or `ready_to_promote` run names the same story, whatever the fences (`STORY_IN_FLIGHT`); the story's `write_fence` overlaps no active or `ready_to_promote` run's fence (`FENCE_OVERLAP`); the worktree-mode prerequisites in `09-hook-dispatcher.md` section 3 hold when the project is a git repository; for `kind: story` the whole story gate in section 3.2; for `kind: document` the fence gate in section 4, plus the same story gate when the skill is story-anchored (section 4); `--lenient` only where a story gate runs, and only for a story outside `docs/plan/` (section 3.4) | canonical `state.yaml#runs.<run>` (status `active`), `work/<run>/run.yaml`, `work/<run>/context.json`, the candidate root and its `base` checkpoint, `provenance/log.jsonl` | `0` opened; `1` refused (active run, `STORY_IN_FLIGHT`, `FENCE_OVERLAP`, gate defects, kind `none`, kind `external` with its runner present, `--lenient` on a planned story); `2` unknown skill, unparseable story frontmatter, or `--lenient` on a skill with no story gate; `3` kind `external` whose runner is absent from `PATH`, or a worktree prerequisite that failed (`hook_fault`) | model |
| `devforgeai phase fail` | `--reason <text>` | a run is active | `work/<run>/handoff.json`, canonical `state.yaml` (status `blocked`/`dev_blocked`, `next`), `provenance/log.jsonl`; abandons the candidate root when the policy says abandon | `0` recorded; `1` no active run | model |
| `devforgeai validate` | none | a run is active | nothing | `0` invariants hold; `1` no active run, or fence/stack invariants fail | model |
| `devforgeai promote` | `<run>` | the run's status is `ready_to_promote`; canonical base unmoved (`STALE_BASE`); no dirty canonical file among the run's changed paths (`DIRTY_TARGET`); the sequencer lock is free | canonical tree (the run's changed paths), canonical `state.yaml#runs.<run>` (status `promoted`), `work/<run>/handoff.json`, `provenance/log.jsonl` | `0` promoted; `1` `NO_CANDIDATE`, run not `ready_to_promote`, `STALE_BASE` after a failed rebase, `DIRTY_TARGET`, or `MERGE_CONFLICT`; `3` the lock could not be taken | model |
| `devforgeai session-start` | `--session-id <id> --provider {claude,codex} [--provider-version <v>]` | hook marker `SessionStart` | `sessions/<session_id>.json`, `provenance/log.jsonl` | `0` written, or the repository has no `.devforgeai/`; `1` marker absent | hook (SessionStart) |
| `devforgeai ingest-result` | `--agent <type> --agent-id <id> --session-id <id>`, receipt on stdin | hook marker `SubagentStop`; a run is active; the full validation order in section 5.2 | `work/<run>/<phase>-result.json` (including the derived `changed[]`), `work/<run>/<phase>-report.md`, the phase checkpoint, `work/<run>/run.yaml` (lease released), then everything `phase next` writes | `0` ingested and the run advanced, completed, or blocked; `1` marker absent, receipt refused, `UNCLAIMED_CHANGE`, oracle failed below the attempt limit, or the phase is still active after a `pass` | hook (SubagentStop) |
| `devforgeai phase next` | none | hook marker `SubagentStop`; a run is active; an accepted result exists for the current phase | canonical `state.yaml#runs.<run>`, `work/<run>/run.yaml`, `work/<run>/<phase>-report.md`, `work/<run>/handoff.json`, `docs/reports/<skill>-<run>-<phase>.md`, `provenance/log.jsonl` | `0` advanced, completed, or blocked; `1` no result, or oracle problems below the attempt limit | hook (SubagentStop) |
| `devforgeai run` | `<key>` | a run is active; the caller holds the run's write lease, or the marker names `SubagentStop` and the sequencer is inside a transition; the active phase grants the key and `commands.use` authorises it; the command mutated no path outside `stack.yaml#ignore_dirs` | `provenance/log.jsonl`; the runner's own `junit_path`; whatever the command itself writes inside the candidate root | `0` classified and the command exited 0; `1` key not granted, no lease, mutation outside `ignore_dirs`, or a non-zero exit; `3` `INFRA_FAILURE` or `TIMEOUT` | worker (lease), hook (SubagentStop) |
| `devforgeai candidate open` | `<run>` | hook marker; called by `phase start` | the candidate root, its `base` checkpoint, `work/<run>/run.yaml#candidate` | `0` created; `1` refused; `3` a worktree prerequisite failed | hook (sequencer-internal) |
| `devforgeai candidate lease` | `<run> --agent <t> --agent-id <id> --session-id <id>` | hook marker; called only from SubagentStart | `work/<run>/run.yaml#lease` bound to the start event's identity | `0` bound; `1` refused (`LEASE_HELD`, or the phase has no producer) | hook (sequencer-internal) |
| `devforgeai candidate checkpoint` | `<run> <phase>` | hook marker; called by `ingest-result` after the oracle passed | the phase checkpoint (commit and tag, or manifest and copy-aside), `work/<run>/run.yaml#candidate.checkpoint` | `0` written; `1` refused | hook (sequencer-internal) |
| `devforgeai candidate promote` | `<run>` | hook marker; called by `devforgeai promote` under the lock | the canonical tree, `provenance/log.jsonl` | `0` promoted; `1` `STALE_BASE`, `DIRTY_TARGET`, `MERGE_CONFLICT` | hook (sequencer-internal) |
| `devforgeai candidate abandon` | `<run>` | hook marker; called by `phase fail --reason` when the policy says abandon | deletes the candidate root, its branch and tags, or its copy-aside; canonical `state.yaml#runs.<run>` (status `abandoned`) | `0` abandoned; `1` `NO_CANDIDATE` | hook (sequencer-internal) |

The four `candidate` operations are hook-only in exactly the sense the others are — they refuse without `DEVFORGEAI_HOOK_EVENT` — but no provider event invokes them. The sequencer sets the marker itself and calls them from `phase start`, `ingest-result`, `promote` and `phase fail`. They exist as named operations so that root creation, checkpointing, promotion and abandonment are one implementation with one set of refusal reasons, not four inlined code paths.

Refusal reasons this grammar names, beyond the gate defect classes in section 3.2:

| Reason | Raised by | Meaning |
|---|---|---|
| `STORY_IN_FLIGHT` | `phase start` | a run that is `active` or `ready_to_promote` already names this story. `review` and `qa` are story-anchored but fenced to a report path, so a fence test alone would let one open against canonical HEAD while the story's `dev` work sat unpromoted in a candidate root — and it would then judge a tree that does not contain the work. The story id, not the fence, is what closes that |
| `FENCE_OVERLAP` | `phase start` | the requested run's `write_fence` intersects the fence of a run that is `active` or `ready_to_promote`. Producer-exception paths count as fence members, so two `architect` runs cannot both be open |
| `LEASE_HELD` | SubagentStart | a producer already holds this run's write lease. The second dispatch is refused rather than queued |
| `UNCLAIMED_CHANGE` | `ingest-result` | the change set derived from the checkpoint diff is not a subset of the receipt's `claimed_paths` |
| `STALE_BASE` | `promote` | the canonical tree no longer matches `candidate.base_ref`. In worktree mode the sequencer rebases the run branch, re-runs the last transition oracle and retries once; in copy mode it returns `needs_user` |
| `MERGE_CONFLICT` | `promote` | a rebase inside the root conflicted. `git rebase --abort` runs, the run is `needs_user`, and no canonical byte moved |
| `DIRTY_TARGET` | `promote` | a canonical file among the run's changed paths has uncommitted local edits. The user resolves it; the sequencer does not merge |
| `NO_CANDIDATE` | `promote`, `candidate abandon` | the named run has no candidate root: it was never opened, or it was already promoted or abandoned |

Notes that bind skill authors:

- `devforgeai run <key>` is the one operation a worker calls that is not `status`. It is admitted only to the producer holding the lease, only for a key in `run.yaml#granted_keys`, and it runs with cwd = `candidate.root`. The primary window is refused: it holds no lease. The Claude allowlist declares `Bash(devforgeai run *)` as surface so the permission layer can name the operation; the sequencer, not the allowlist, decides.
- A judge calls `devforgeai status` and nothing else. A producer calls `devforgeai status` and `devforgeai run <key>`. The primary window may call the five model-callable operations, and only as current state allows: `devforgeai phase start` only when no run is active, `devforgeai validate` and `devforgeai phase fail` only when one is, `devforgeai promote <run>` only for a run already marked `ready_to_promote` and only when the user has asked for it.
- `--lenient` is the only flag `phase start` accepts, and the dispatcher's Bash grammar accepts it only as a single trailing token. Any other flag is refused before the sequencer runs. `promote` takes one positional run id and no flag at all.
- No operation writes a narrative report on request. `<phase>-report.md` is rendered by the sequencer from the ingested result, and `docs/reports/<skill>-<run>-<phase>.md` is its rendered view, written at the transition.
- Skills whose kind is `none` have no phases and never open a run; their command is a thin wrapper over a deterministic operation. `status` wraps `devforgeai status`; the installer skill wraps the installer, which is not part of this grammar.
- The installer skill is the one skill that writes `.devforgeai/` itself, and it does so through documented provider-side steps in its own `SKILL.md` — copy the hook fragments, write the `state.yaml` skeleton, create `work/`, `sessions/` and `provenance/` — not through any operation in this table. There is nothing for a sequencer to enforce until `state.yaml` exists, so the window is exactly that: while no `.devforgeai/state.yaml` exists the hook dispatcher permits a write under `.devforgeai/` and denies every other path; the moment the file exists that window closes and every path under `.devforgeai/` is refused by name, to the installer skill and to everything else (`09-hook-dispatcher.md`; `examples/hooks/dispatch.py` `check_installer_write`). `.claude/**`, `.codex/**`, `CLAUDE.md` and `AGENTS.md` are denied on both sides of the boundary: the dispatcher is itself one of the files the installer writes, so the provider fragments land before it is armed to see them. Re-installing over an installed repository is therefore not a skill operation at all.

One command outside this grammar is nonetheless model-callable, and the hook layer admits it by name:

| Head | Operations | Access | Why it is not in the grammar above |
|---|---|---|---|
| `devforgeai-research` | `normalize-request`, `open-run`, `append-record`, `put-source`, `transition-run`, `validate-run`, `seal-run`, `render`, `render-handoff`, `resume-run` | model, primary window only | It is a **provider-external CLI**: the Research Core runner that `research`'s registry entry names (`kind: external`, section 4). It is the sole writer inside its own fence — `docs/research/**`, `.devforgeai/research-staging/`, `.devforgeai/research-cas/**` — which no framework phase may write and which the sequencer does not own. It opens no framework run and needs none open, so no `run.yaml` governs it and none of the preconditions above apply |

The dispatcher's Bash check admits exactly that head with exactly those ten subcommands, and the provider allowlists name the ten forms one by one. Any other subcommand is refused, so is any redirect, pipeline or substitution around it, and so is a call from a phase worker: no worker of any role may call it, because Research Core writes outside every candidate root and a worker writes only inside one. `devforgeai phase start research <arg>` remains refused — the framework does not sequence Research — and `12-post-mvp.md` owns any future brokering of this runner.

One consequence remains, and it is smaller than it was: Research Core runs in the canonical checkout, so a `seal-run` or `render` during an active framework run writes canonical bytes that the run's candidate root does not contain. The transition oracle diffs the root against its own checkpoint, so those writes are not drift and the phase does not repeat. They matter only at promotion, and only in worktree mode, where a canonical commit that lands after `phase start` moves the base: `promote` returns `STALE_BASE`, the sequencer rebases the run branch and retries once. Research writes under `docs/research/**`, which no framework fence contains, so a rebase conflict is possible only if the run's own fence overlaps that path — which `FENCE_OVERLAP` and the fence gate already prevent. Running Research Core between framework runs still avoids the rebase entirely.

## 3. Status vocabulary and gate policy

### 3.1 Two orthogonal sets

| Set | Values | Who produces it | Where it appears |
|---|---|---|---|
| Worker status | `pass`, `fail`, `needs_user`, `could_not_run` | the worker, in its envelope | `worker-result.status`, `<phase>-result.json` |
| Reason code | `runner_missing`, `timeout`, `network`, `hook_fault` | the worker, or the sequencer when it synthesises a result | required with `could_not_run`, rejected with every other status |
| Gate policy | `BLOCK`, `REQUIRE_HUMAN`, `WARN`, `OFF` | the artifact author, per defect class | `story.gate_policy`, `run.yaml#gate_policy`, `handoff.outcome` |
| Oracle classification | `PASS`, `EXPECTED_TEST_FAILURE`, `TEST_FAILURE`, `NO_TESTS`, `COLLECTION_ERROR`, `INFRA_FAILURE`, `TIMEOUT` | the sequencer, from a brokered command | `run.yaml#last_oracle`, `handoff.validation[]` |

`gate_policy` is a defect-to-action map. It is never a status a worker returns, and no worker reads it. There is no `test_defect` status and no `test_defect` issue kind: a rewind is `status: fail` with `next: <rewind_to>`, and it is legal only from a phase whose registry entry declares `rewind_to`.

`needs_user` never retries. It is recorded, written into a `REQUIRE_HUMAN` handoff, and the run is blocked at that phase: status stays `active`, the lease is released, the candidate root survives, and `run.yaml#blocked_at` names the phase; the attempt counter is not consulted. A worker that wants a human decision gets one on the first ask. The run resumes when the user has acted: `devforgeai phase start <skill> <arg>` with the same skill and argument on a blocked run **resumes** it at `blocked_at` with `attempts` reset to zero instead of refusing `STORY_IN_FLIGHT` (the same rule resumes an attempt-limit block). Any other skill on the same story needs `devforgeai phase fail --reason <text>` first, which abandons the root.

### 3.2 Defect-to-action map, as implemented

| Defect class | Detected by | Implemented action | Is `gate_policy` consulted? | Handoff outcome |
|---|---|---|---|---|
| `unresolved_assumption` | story gate: `ASSUMPTION:` before `## Clarifications` | refuse; no run opens | no | none written; exit 1 with the defect list |
| `stale_hash` | story gate: a `provenance[]` or `context[]` entry whose source and anchor resolve but whose digest no longer matches, or `commands.hash` differing from the current `stack.yaml` digest | refuse; no run opens | no | none written; exit 1 |
| `unresolvable_source` | story gate: a `provenance[]` or `context[]` source that does not exist, an anchor that does not resolve, or a placeholder or malformed hash (`sha256:fixture…`, `sha256:PENDING`, anything that is not `sha256:<64 hex>`), including on `commands.hash`; document gate: no fence declared | refuse; no run opens, unless the defect is downgraded by section 3.4, in which case the run opens and every downgraded row is recorded in `run.yaml#gate_warnings` | **yes**, `story.gate_policy.unresolvable_source`, and only on a `scope: hotfix` story | none written; exit 1 |
| `write_fence_violation` | result validation and every transition | refuse the envelope, or fail the transition | no | on the transition path, `REQUIRE_HUMAN` once attempts are exhausted |
| `criterion_without_test` | story gate: a `test_plan` row lacking `criterion`, `file` or `name`, or whose file is outside `write_fence`; red oracle: a `test_plan` name absent from the JUnit results | refuse at the gate; attempt +1 at the oracle | no | `REQUIRE_HUMAN` once attempts are exhausted |
| `test_runner_missing` | brokered command classified `INFRA_FAILURE` or `TIMEOUT`; worker `could_not_run` | record, block the run at the phase (`blocked_at`, resumable once the runner exists), hand off | **yes**, `run.yaml#gate_policy.test_runner_missing`, default `REQUIRE_HUMAN` | the policy value, verbatim |
| unknown defect class | story gate: any `gate_policy` value outside the four | refuse; no run opens | no | none written; exit 1 |

Three honest limits follow from that table and must not be overstated in a skill specification:

1. Every `devforgeai phase start` defect is a refusal, whatever the story's per-class value says, with the single exception in section 3.4. `WARN` and `OFF` are otherwise accepted as legal values and recorded in the enforcement block, but at the gate they do not downgrade a defect. At transition time only `test_runner_missing` changes behaviour.
2. `WARN` or `OFF` on `test_runner_missing` relabels the handoff outcome. It does not continue the run: the phase is blocked either way, and `phase start` with the same skill and argument resumes it once the runner is installed.
3. A downgraded defect is recorded, never hidden. `run.yaml#gate_warnings[]` holds one row per downgraded defect, the `phase.start` log line carries the same rows and the `lenient` flag, and the sequencer prints them on stderr as it opens the run.

A document run carries the fixed map `{unresolvable_source: BLOCK}`, because it has no story to declare a wider one. A story-anchored document run (`qa`, `review`; section 4) copies the story's map instead, exactly as a story run does.

### 3.3 Timeout and malformed input, per gate

Every gate states its behaviour on a timeout and on malformed input, and every one of them fails closed.

| Gate | Malformed input | Timeout |
|---|---|---|
| Hook dispatcher, any policy event | `state.yaml` or the referenced `stack.yaml` unreadable, non-mapping, or escaping the project root: block with the reason on stderr, exit 2 | sequencer subprocess exceeding 660 s: block; the transition is not accepted |
| `devforgeai phase start`, story | frontmatter that is not parseable YAML: exit 2; any gate defect: exit 1; `stack.yaml` unparseable or the anchor missing: refuse | not applicable; the gate runs no command |
| `devforgeai phase start`, document | a fence entry that is absolute, contains `..`, or matches a sequencer-owned path: refuse | not applicable |
| `devforgeai ingest-result` | not valid JSON, no receipt declaring the schema, more than one such object, unknown or missing keys, oversize (over 64 KiB total, over 64 `claimed_paths`, over 16 `evidence_refs`, note over 16 KiB, over 10 issues): refuse, exit 1, dispatcher exit 2, the same worker continues. The attempt counter is **not** incremented: a malformed receipt is a protocol error, not a phase attempt. A change set that exceeds no cap but is not a subset of `claimed_paths` is `UNCLAIMED_CHANGE`, which **is** a phase attempt: the bytes are real and the phase must redo them | inherited from the dispatcher's 660 s bound |
| Transition oracle | JUnit XML that does not parse: `COLLECTION_ERROR`; `junit_path` present but no test cases: `NO_TESTS` | brokered command over `timeout_s` (default 600): `TIMEOUT`, mapped to `could_not_run` / `timeout` and routed by `gate_policy.test_runner_missing` |
| `devforgeai run` | key not granted by the phase or by `commands.use`, the caller holds no lease, or the section defines no such command: refuse, exit 1 | `TIMEOUT` classification, exit 3 |
| `devforgeai validate` | stack policy that cannot be evaluated (bad regex, unreadable file): reported as a problem, exit 1 | not applicable |

A missing hook script, a disabled hook layer, a process crash, and a provider that skips a hook path are not deny decisions. That hole is named in `09-hook-dispatcher.md` section 9 and is closed only by rung 4 (`12-post-mvp.md#pm-10`).

### 3.4 Re-resolving sources, and the one downgrade

The story gate re-resolves every `provenance[]` and `context[]` entry as well as `commands`. For each entry it applies the hash rule in `01-skill-anatomy.md#context-bundle-format`: resolve `path#anchor` (a heading anchor runs from its heading to the next heading of the same or higher level; `#L10-L20` is that inclusive line range; no anchor is the whole file), normalise CRLF to LF, join with LF, append one trailing LF, and `sha256` the UTF-8 bytes. `docs/design/specs/verify.py` computes the same bytes for every `depends_on`, so a gate digest and a V3 digest agree by construction.

A `#` line inside a fenced code block is sample text, not a heading: it neither opens a section nor ends one. A fence opens on a line whose first non-space run is three or more backticks or tildes (at most three leading spaces, an optional info string) and closes on a run of the same character at least as long with nothing after it; an unclosed fence runs to the end of the file. Both resolvers implement this, so a document that quotes a heading — every design document here does — hashes to the bytes a reader would say the section contains.

`commands` is the one reference that pins a whole file rather than a section: `commands.source` names the anchor the run resolves its command keys from, and `commands.hash` is the digest of the entire `stack.yaml`, so any edit anywhere in the file is a stale hash. A `commands.source` that is empty or names a file that does not exist is refused whatever the policy map or the flag says: a run with no stack section can broker no command, so there is nothing to downgrade to. Only `commands.hash` participates in the downgrades below.

Each entry produces exactly one verdict:

| Verdict | When | Action |
|---|---|---|
| resolved | source exists, anchor resolves, digest matches | nothing |
| `stale-hash` | source and anchor resolve, digest differs | refuse; never downgradable |
| `unresolvable-source` | missing source, unresolvable anchor, unreadable file, or a placeholder or malformed hash | refuse, unless downgraded below |

Two downgrades exist, and both only for `unresolvable-source`:

1. **`gate_policy.unresolvable_source: WARN` or `OFF` on a `scope: hotfix` story.** `03-brownfield.md` gives hotfix scope reduced provenance. Declaring `WARN` or `OFF` for this class on any other scope is itself a gate defect and refuses the run.
2. **`devforgeai phase start <skill> <arg> --lenient`.** This is the implementation of rule 6 of the hash rule: a story that is not part of a planned project has no document set to resolve against, so its placeholder hashes are warnings rather than defects. The flag is refused (exit 1) for any story under `docs/plan/`, and refused as a usage error (exit 2) for a skill whose gate reads no story. It downgrades `unresolvable-source` and nothing else: a stale hash, an unresolved `ASSUMPTION:`, a fence violation and every other defect still refuse the run.

The stand-alone fixture story at `examples/fixtures/dev-tdd/STORY-001.md` is the case the flag exists for: it is copied to a scratch root, its context entries name architecture documents that scratch tree does not contain, and its hashes are literal `sha256:fixture…` placeholders. `examples/hooks/demo_sequencer.sh` therefore opens it with `--lenient`, and the five downgraded rows are printed and recorded. A story under `docs/plan/` cannot be opened that way at all.

## 4. Per-skill phase registry

The registry in `policy.py` is the single source of truth for which phases a skill has, in what order, which worker each dispatches, what it may write, how many attempts it gets, which stack keys it grants, which oracle runs at its transition, and which earlier phase it may rewind to. The table below is that registry.

Column meanings:

- **writes** — what the phase's worker may change inside the candidate root: `docs` (the run's fence, document mode), `tests` (only paths in `test_paths`), `code` (fence paths that are not in `test_paths`), `fields` (a narrower path set inside the run fence, and only the frontmatter keys the phase declares; see below), `none` (a judge: nothing in the root, and any derived change is a refusal). The column is also the role split: every mode but `none` is a producer, which holds the run's write lease while it is dispatched; `none` is a judge, which holds no lease and may run against a checkpoint while another judge does. `none` is not silence: a judge writes its findings under `.devforgeai/work/<run>/evidence/<agent>/` and names them in `evidence_refs`, and that directory is outside every candidate root, so those writes never enter a diff, a checkpoint or a promotion. A worker header declares the same split as a closed enum, `writes: candidate | evidence | none`: `candidate` for every producer mode in this column, `evidence` for a judge, `none` for a worker that writes nowhere at all. A `docs` phase marked **conditional** owes its document only under a condition the run may not meet, so the document oracle accepts an empty change set from it when the receipt's `note` says why none was owed; every other `docs` phase must change a file.
- **run keys** — the stack command keys this phase may broker. The effective set is the intersection with the run's `commands.use`, and it is what `run.yaml#granted_keys` holds while the phase is active.
- **oracle** — the transition check in section 5.4, run by the sequencer inside the candidate root.
- **rewind** — the only phase `next:` may name, on a `fail` result. The root is reset to the checkpoint that phase started from, and the phase is re-entered.
- **story-anchored** — a `document` skill whose `<arg>` is a story id, so the story gate runs as well and the story's commands and test rows enter `run.yaml`. `qa` and `review` are the two.

`kind` decides which gate runs and whether a run opens at all:

| Skill | Kind | Runner or fence | Phases |
|---|---|---|---|
| init | none | — | none; the command is a thin wrapper over the deterministic installer, and `devforgeai phase start` refuses it |
| status | none | — | none; the command is a thin wrapper over `devforgeai status` |
| research | external | runner `devforgeai-research`; fence `docs/research/<arg>/**` | none here; the Research Core CLI executes it under `src/devforgeai/skills/research/`, and `devforgeai phase start` refuses it (exit 3 when the runner is absent) |
| onboard | document | `docs/architecture/sourcetree.md`, `docs/architecture/techstack.md`, `docs/architecture/architecture.md`, `.devforgeai/stack.yaml` | 5, below |
| brainstorm | document | `docs/brainstorm/<arg>.md` | 5 |
| pm | document | `docs/PM/<arg>/prd.md`, `docs/PM/<arg>/backlog-ideas.md` | 4 |
| architect | document | `docs/architecture/**`, `.devforgeai/stack.yaml`, `.devforgeai/provenance/adr/**` | 9 |
| plan | document | `docs/plan/<arg>/**` | 7 |
| clarify | document | `docs/plan/*/stories/<arg>.md` | 3 |
| analyze | document | `docs/reports/analyze-<arg>.md` | 4 |
| skill-generator | document | `.devforgeai/skills/<arg>/**` | 6 |
| skill-validator | document | `docs/reports/validate-<arg>.md` | 4 |
| dev | story | the story's `write_fence` | 5 |
| review | document (story-anchored) | `docs/reports/review-<arg>.md`; `<arg>` is a story id | 4 |
| qa | document (story-anchored) | `docs/reports/qa-<arg>.md`; `<arg>` is a story id | 4 |
| amend | document | `docs/architecture/**`, `docs/reports/impact-<arg>.md`, `.devforgeai/provenance/adr/**` | 4 |
| retro | document | `docs/reports/retro-<arg>.md` | 4 |
| drift | document | `docs/reports/drift-<arg>.md` | 3 |

`dev-tdd` is a variant of `dev`, not a nineteenth entry: it resolves to `dev` before the enforcement block is written, so it shares the phase list, the gate, and the oracles. The story or the constitution decides which variant's worker files are installed; the sequencer sees `dev`.

### Phases, in order

| Skill | # | Phase | Worker | Writes | Max attempts | Run keys | Oracle | Rewind |
|---|---|---|---|---|---|---|---|---|
| onboard | 1 | `code_map` | `code_mapper` | docs | 2 | — | document | — |
| onboard | 2 | `doc_ingest` | `doc_ingester` | docs | 2 | — | document | — |
| onboard | 3 | `convention_infer` | `convention_inferrer` | docs | 2 | — | document | — |
| onboard | 4 | `observed_write` | `observed_writer` | docs | 2 | — | document | — |
| onboard | 5 | `critic` | `onboard_critic` | none | 2 | — | report_only | — |
| brainstorm | 1 | `capture` | `idea_capturer` | docs | 2 | — | document | — |
| brainstorm | 2 | `research_request` | `research_requester` | none | 2 | — | report_only | — |
| brainstorm | 3 | `cluster` | `idea_clusterer` | docs | 2 | — | document | — |
| brainstorm | 4 | `write` | `brainstorm_writer` | docs | 2 | — | document | — |
| brainstorm | 5 | `critic` | `brainstorm_critic` | none | 2 | — | report_only | — |
| pm | 1 | `scope_split` | `scope_splitter` | docs | 2 | — | document | — |
| pm | 2 | `prd` | `prd_writer` | docs | 2 | — | document | — |
| pm | 3 | `backlog` | `backlog_archiver` | docs | 2 | — | document | — |
| pm | 4 | `critic` | `pm_critic` | none | 2 | — | report_only | — |
| architect | 1 | `option_compare` | `option_comparer` | none | 2 | — | report_only | — |
| architect | 2 | `constitution` | `constitution_writer` | docs | 2 | — | document | — |
| architect | 3 | `sourcetree` | `sourcetree_writer` | docs | 2 | — | document | — |
| architect | 4 | `techstack` | `techstack_writer` | docs | 2 | — | document | — |
| architect | 5 | `architecture` | `architecture_writer` | docs | 2 | — | document | — |
| architect | 6 | `design` | `design_writer` | docs | 2 | — | document | — |
| architect | 7 | `adr` | `adr_writer` | docs | 2 | — | document | — |
| architect | 8 | `gap_analysis` | `gap_analyzer` | none | 2 | — | report_only | — |
| architect | 9 | `critic` | `architect_critic` | none | 2 | — | report_only | — |
| plan | 1 | `epics` | `epic_writer` | docs | 2 | — | document | — |
| plan | 2 | `stories` | `story_writer` | docs | 2 | — | document | — |
| plan | 3 | `skill_specs` | `skill_spec_writer` | docs (conditional) | 2 | — | document | — |
| plan | 4 | `dependencies` | `dependency_mapper` | fields (`blocked_by`, `size`, `sprint` in `docs/plan/<arg>/stories/*.md`) | 2 | — | report_only | — |
| plan | 5 | `estimates` | `estimator` | fields (`blocked_by`, `size`, `sprint` in `docs/plan/<arg>/stories/*.md`) | 2 | — | report_only | — |
| plan | 6 | `sprints` | `sprint_writer` | docs | 2 | — | document | — |
| plan | 7 | `critic` | `plan_critic` | none | 2 | — | report_only | — |
| clarify | 1 | `find_ambiguity` | `ambiguity_finder` | none | 2 | — | report_only | — |
| clarify | 2 | `questions` | `question_writer` | docs | 2 | — | document | — |
| clarify | 3 | `record_answers` | `answer_recorder` | docs | 2 | — | document | — |
| analyze | 1 | `cross_reference` | `cross_referencer` | none | 2 | — | report_only | — |
| analyze | 2 | `orphans` | `orphan_finder` | none | 2 | — | report_only | — |
| analyze | 3 | `stale_hashes` | `stale_hash_finder` | none | 2 | — | report_only | — |
| analyze | 4 | `report` | `analyze_report_writer` | docs | 2 | — | document | — |
| skill-generator | 1 | `read_spec` | `spec_reader` | none | 2 | — | report_only | — |
| skill-generator | 2 | `skill_yaml` | `skill_yaml_writer` | docs | 2 | — | document | — |
| skill-generator | 3 | `subagents` | `subagent_writer` | docs | 2 | — | document | — |
| skill-generator | 4 | `templates` | `template_writer` | docs | 2 | — | document | — |
| skill-generator | 5 | `compile_claude` | `claude_compiler` | docs | 2 | — | document | — |
| skill-generator | 6 | `compile_codex` | `codex_compiler` | docs | 2 | — | document | — |
| skill-validator | 1 | `anatomy` | `anatomy_checker` | none | 2 | — | report_only | — |
| skill-validator | 2 | `provider` | `provider_checker` | none | 2 | — | report_only | — |
| skill-validator | 3 | `spec_conformance` | `spec_conformance_checker` | none | 2 | — | report_only | — |
| skill-validator | 4 | `report` | `validate_report_writer` | docs | 2 | — | document | — |
| dev | 1 | `red` | `red_dev` | tests | 2 | `test` | red | — |
| dev | 2 | `green` | `green_dev` | code | 3 | `test`, `build` | green | `red` |
| dev | 3 | `refactor` | `refactor_dev` | code | 2 | `test`, `build`, `lint` | refactor | `red` |
| dev | 4 | `smoke` | `smoke_qa` | none | 2 | `test` | report_only | — |
| dev | 5 | `review` | `dev_critic` | none | 2 | — | report_only | — |
| review | 1 | `compliance` | `compliance_checker` | none | 2 | — | report_only | — |
| review | 2 | `security` | `security_checker` | none | 2 | — | report_only | — |
| review | 3 | `style` | `style_checker` | none | 2 | — | report_only | — |
| review | 4 | `report` | `review_writer` | docs | 2 | — | document | — |
| qa | 1 | `run_tests` | `test_runner` | none | 2 | `test` | green | — |
| qa | 2 | `criteria` | `criteria_checker` | none | 2 | — | report_only | — |
| qa | 3 | `evidence` | `evidence_collector` | none | 2 | — | report_only | — |
| qa | 4 | `report` | `qa_writer` | docs | 2 | — | document | — |
| amend | 1 | `apply_change` | `change_applier` | docs | 2 | — | document | — |
| amend | 2 | `adr` | `amend_adr_writer` | docs | 2 | — | document | — |
| amend | 3 | `impact` | `impact_analyzer` | none | 2 | — | report_only | — |
| amend | 4 | `resync` | `resync_slicer` | docs | 2 | — | document | — |
| retro | 1 | `collect` | `report_collector` | none | 2 | — | report_only | — |
| retro | 2 | `lessons` | `lesson_extractor` | none | 2 | — | report_only | — |
| retro | 3 | `amendments` | `amendment_proposer` | none | 2 | — | report_only | — |
| retro | 4 | `archive` | `archiver` | docs | 2 | — | document | — |
| drift | 1 | `code_map` | `code_mapper` | none | 2 | — | report_only | — |
| drift | 2 | `doc_diff` | `doc_differ` | none | 2 | — | report_only | — |
| drift | 3 | `report` | `drift_writer` | docs | 2 | — | document | — |

**Fix mode.** `/dev <story> --fix` opens an ordinary dev run whose story context bundle names the qa or review report that routed here; `phase start` records that path as `run.yaml#fix_report`. The only change is the red oracle's required-fail set: it is the `test_plan` rows whose criteria the report marks failed, plus any test added in this run, and every other `test_plan` test must pass in the red checkpoint. Green and refactor are unchanged. Without this narrowing, promoted code that already passes some planned tests could never leave red. The runnable draft in `examples/hooks/` does not yet read `fix_report` and applies the full-fail rule in every dev run; that gap is listed in its README.


Worker names are canonical. Provider identity is checked against them: a Codex custom-agent `name` and a Claude agent frontmatter `name` are the same string, so `agent_type` needs no translation. The long role identifiers used by earlier drafts remain accepted as aliases and resolve to the short name before any comparison:

| Alias | Canonical |
|---|---|
| `dev-tdd-red-tester`, `red-tester` | `red_dev` |
| `dev-tdd-green-implementer`, `green-implementer` | `green_dev` |
| `dev-tdd-refactorer`, `refactorer` | `refactor_dev` |
| `dev-tdd-smoke-qa`, `smoke-qa` | `smoke_qa` |
| `dev-tdd-critic`, `critic` | `dev_critic` |

Both providers register their `SubagentStart` and `SubagentStop` matchers as `.*`. Identity is not filtered by the matcher; it is checked in the sequencer. A narrow matcher list would silently skip the workers of every skill it forgot.

Sub-phase 1, **Slice**, is not in the table because it dispatches no worker. `phase start` has just re-resolved the incoming artifact's `context[]` bundle to open the run, so it writes what it resolved to `.devforgeai/work/<run>/context.json` and every worker of that run is handed the path. A story run and a story-anchored document run get the bundle, entry by entry, with each entry's verdict; every other document run gets `slice: none` and an empty entry list, because the document gate identifies no incoming artifact to resolve. No skill has a Slice worker, and there is no shared framework worker (`01-skill-anatomy.md#slice-and-why-it-has-no-worker`).

Two registry facts a skill author must design around rather than assume away:

- **Story-anchored document runs.** `qa` and `review` take a story id as their `<arg>`. The document fence gate runs, and so does the whole story gate: the story's `commands` (`source` and `use`), `test_plan`, `test_paths` and `gate_policy` are copied into `run.yaml`, exactly as a `dev` run copies them. That is what makes `qa`'s `run_tests` phase able to broker the `test` key and pass the `green` oracle. The fence is still only the report path, and every phase of both skills is a judge except the `report` phase that writes it, so those runs read the code and the tests at a checkpoint and change nothing but their report. The story file's `status` stays `ready` through its whole life — the sequencer mirrors progress into `state.yaml`, never back into the story — so a story that finished `dev` still gates cleanly for `qa` and `review`.
- `code_mapper` is dispatched by both `onboard` and `drift`. That is the one place the registry crosses the no-borrowing rule in `01-skill-anatomy.md`; the two specifications must state which one owns the worker file.

`architect` has no `mandate_specs` phase and no fence entry under `docs/plan/`. `plan` is the sole owner of the skill-spec template (`11-artifact-registry.md`); `architect` writes mandates into `docs/architecture/constitution.md#mandates` through its `constitution` phase and nothing else about skills.

Two sequencer-owned paths are writable, and only from the phases that produce them: `.devforgeai/stack.yaml` from `architect`'s `techstack` phase or `onboard`'s `code_map` phase, and `.devforgeai/provenance/adr/**` from `amend`'s `adr` phase or `architect`'s `adr` phase. They are in those skills' document fences for that reason; every other phase of those skills, and every phase of every other skill, is refused both as sequencer-owned. The producer writes them **inside the candidate root**, where they are ordinary fenced files; they reach canonical `.devforgeai/` only at promotion, which is why the sequencer remains the sole writer of the canonical tree. Section 5.2 lists the producer exceptions and what the sequencer validates at ingest, and section 7 states the `stack.yaml` contract in full.

One phase in the table is **conditional**: `plan`'s `skill_specs`. A skill spec is owed only when a story's `requires_skill` names a skill that does not exist yet, and a plan whose stories all use installed skills owes none. Without the flag the document oracle failed that phase for producing nothing, and the only way past it was to invent a specification. The flag does not weaken the oracle: an empty change set passes only when the receipt's `note` says why none was owed, so "nothing was owed" is a finding the run records rather than a silence the oracle infers.

Two phases are **field-restricted**: `plan`'s `dependencies` and `estimates`. `08-story-specification.md` makes the dependency-mapper and the estimator the producers of `blocked_by`, `size` and `sprint`, and the registry runs them after `stories`, which is the only order in which a story exists to carry those values. As `writes: none` they could deliver nothing at all; as `writes: docs` they could rewrite any story in the plan. So they write, and narrowly: every changed path must match `docs/plan/<arg>/stories/*.md`, the file must have existed at the input checkpoint, the body must be byte-identical to that checkpoint's, and the frontmatter diff must touch no key but those three. Anything else — a new file, a deletion, a changed criterion, a changed `status` — refuses the phase and rewinds the root to the input checkpoint. A field-restricted phase may legitimately change nothing at all, because a plan with no blockers and no resizing has nothing to set; its oracle is `report_only`, which asks only that the fence held.

Order matters and is fixed: `stories` writes the story, then `dependencies` sets `blocked_by`, then `estimates` sets `size` and `sprint`, then `sprints` reads all three. A specification must not describe `story_writer` as filling those keys from a later phase's evidence: the later phase writes them itself.

## 5. Worker result

### 5.1 Fields

One schema, both providers, every skill. The worker's final message is exactly this object, with no Markdown fence and no surrounding prose. It is a **receipt**: it says what the worker did, not what it wants done. A producer has already written its files inside the candidate root; a judge has written nothing. No file body, no diff and no hash crosses this boundary, so nothing a worker touched enters the primary window's context.

| Field | Type | Required | Rule |
|---|---|---|---|
| `schema` | string | yes | exactly `devforgeai.worker-result/v1` |
| `run` | string | yes | equals `run.yaml#run` |
| `skill` | string | yes | resolves through the variant map to `run.yaml#skill` |
| `phase` | string | yes | equals `run.yaml#phase` |
| `agent` | string | yes | resolves through the alias map to the same canonical name as the stop event's `agent_type` |
| `status` | enum | yes | `pass`, `fail`, `needs_user`, `could_not_run` |
| `reason_code` | enum | conditional | required with `could_not_run`; refused with any other status |
| `candidate` | object | yes | `{id, input_checkpoint}`, on every status. `id` equals the run id; `input_checkpoint` is the checkpoint the phase was dispatched against — `base`, or the name of the phase whose checkpoint it read — and must equal `run.yaml#candidate.checkpoint` as it stood at dispatch |
| `claimed_paths` | array | yes | at most 64 root-relative paths the worker believes it created, edited or deleted. Empty on any status other than `pass`, and empty from a judge. Not a request: the sequencer derives the truth from the diff and compares |
| `evidence_refs` | array | no | at most 16 paths to evidence the sequencer should read: a report inside the root, a findings file the judge wrote under `.devforgeai/work/<run>/evidence/<agent>/`, or an oracle output the sequencer itself wrote under `.devforgeai/work/<run>/`. A report-producing phase names its report here, and that report's frontmatter `verdict` selects the handoff row (section 6). Never a body, never a hash |
| `note` | string | no | at most 16384 bytes; three lines is the intended length |
| `issues` | array | no | at most 10 one-line rows |
| `next` | string | no | a rewind request; requires `status: fail`, requires the phase to declare `rewind_to`, and must equal that value. The sequencer resets the root to the checkpoint the named phase *started from* — its predecessor's, or `base` when it is the first phase — and re-enters it, because the named phase's own output is what is being redone |

The whole receipt is capped at 64 KiB. Unknown keys are refused; there is no forward-compatible ignore. No file list, no file body, no base hash and no `evidence` object appears anywhere in it: the previous envelope carried file bodies through the model's own message, which bounded a phase at 32 files and put every byte a worker wrote into the primary context. A receipt does neither, so `plan`'s `stories` phase can write a slice of any size and a `green` phase can touch a binary fixture the old envelope could not represent at all.

The two caps that remain are on the claim, not on the work: 64 `claimed_paths` and 16 `evidence_refs`. A phase that genuinely changes more than 64 paths is a phase whose fence is too wide to review, and the fix is to split the run by slug — `devforgeai phase start plan <slug>` per slice — not to raise the cap.

The model-supplied `agent` field is not identity. The trusted binding is the stop event's `agent_type`; the two must agree, so a green worker cannot label itself red and a primary-window Bash call cannot submit a result at all. `claimed_paths` is likewise not evidence: it is the claim the derived change set is checked against, and a worker that under-claims is refused with `UNCLAIMED_CHANGE` rather than quietly promoting an unclaimed edit.

### 5.2 Validation order

Steps 1 to 8 read the receipt alone. Step 9 is where the sequencer stops believing the worker and looks at the tree: it diffs the candidate root against the receipt's `input_checkpoint` and derives

```
changed[] = [{path, blob_sha256, kind: added | modified | deleted}, ...]
```

one row per path whose bytes differ between the checkpoint and the root as it stands, with `.git`, `.devforgeai/work`, the `.devforgeai/candidate` marker (12.3) and `stack.yaml#ignore_dirs` excluded. In worktree mode that diff is `git diff --name-status` against the checkpoint tag plus the untracked set; in copy mode it is the tree-hash manifest compared row by row. `changed[]` is the only account of what the phase did. Every later check runs against it, not against `claimed_paths`.

Steps 9 to 14 run **only on `status: pass`**. A producer that edited code and then returned `fail` with `next: red`, or `needs_user`, or `could_not_run`, claims nothing by rule and has changed something in fact; checking a non-empty diff against an empty claim would refuse every honest failure. So on a non-pass status the sequencer records the diff in the result row as `changed_unchecked[]`, runs no fence, policy or oracle check over it, takes no checkpoint, and routes by the status: a `next` rewinds the root to the checkpoint the named phase started from, and everything else leaves the root where it is for the retry or for a human to read. The bytes are unpromotable either way, because a run only promotes from a checkpoint.

A refusal below leaves the candidate root as it stands, so a failure loses nothing: the phase is retried or rewound to a checkpoint that exists. Nothing is "partially applied" because nothing is applied — the bytes were already written by the worker, inside a root no canonical reader sees.

| # | Check | On failure |
|---|---|---|
| 1 | total size at most 64 KiB; exactly one object in the final message declaring the schema | refuse |
| 2 | the object parses as JSON and is a mapping | refuse |
| 3 | key set: every required key present, no unknown key | refuse |
| 4 | `schema` constant matches | refuse |
| 5 | phase-agent binding: canonical `agent_type` is the active phase's worker, the receipt's `agent` resolves to the same name, and — where the provider supplies one — the stop event's `agent_id` equals the `agent_id` the lease was granted to | refuse |
| 6 | `run` and `phase` equal `run.yaml`; `skill` resolves to the active skill; `candidate.id` equals the run and `candidate.input_checkpoint` equals the checkpoint the phase was dispatched against | refuse |
| 7 | `status` in the closed set; `reason_code` present exactly when `could_not_run` | refuse |
| 8 | `next` rules: `status: fail`, phase declares `rewind_to`, value equals it, and it names an earlier phase. `claimed_paths` is a list of at most 64 with no duplicate; a non-`pass` status carries none; `evidence_refs` at most 16; `note` and `issues` within bounds | refuse |
| 9 | derive `changed[]` from the checkpoint diff, as above | refuse when the checkpoint is missing or the diff cannot be taken (`could_not_run`, `hook_fault`) |
| 10 | `changed[]` is a subset of `claimed_paths` | refuse, reason `UNCLAIMED_CHANGE`; this **is** a phase attempt, because real bytes were written outside the claim |
| 11 | per changed path: canonicalised, inside the candidate root, not sequencer-owned, inside `write_fence`, allowed by the phase's `writes` mode — for `red` that means inside `test_paths`, for `green` and `refactor` inside the fence and outside `test_paths`, and for a judge (`writes: none`) that `changed[]` is empty, its findings having gone to `.devforgeai/work/<run>/evidence/<agent>/`, which no diff covers | refuse |
| 12 | per changed path with `kind` `added` or `modified`: the bytes now on disk pass the stack policy scan — no denied package pattern in a manifest, no captured package outside `packages.allow`, no forbidden import for that path | refuse |
| 13 | a changed path admitted by a producer exception passes that artifact's own contract, below. A delete is refused for both, and so is a missing validator: the change is refused rather than accepted unvalidated | refuse |
| 13b | on a `writes: fields` phase, every changed path is an update of the declared kind: it matches the phase's own pattern list with `<arg>` substituted, its `kind` is `modified`, both the checkpoint's version and the current version parse as frontmatter plus body, the body bytes are identical, and the frontmatter differs only in the keys the phase declares (`blocked_by`, `size`, `sprint` for `plan`'s `dependencies` and `estimates`) | refuse |
| 13c | when the phase is report-producing (`review`/`report`, `qa`/`report`, `skill-validator`/`report`), `evidence_refs` names exactly one report inside the fence, and that report's frontmatter carries a `verdict` in `pass`, `findings`, `fail`. Every other phase is refused for naming a report with a `verdict` at all | refuse |
| 14 | the whole candidate root, rescanned against the stack policy; a violation that only appears in combination is caught here | refuse |

Step 13 in full, one row per producer exception:

| Path pattern | Producers (skill / phase) | Validated against |
|---|---|---|
| `.devforgeai/stack.yaml` | `architect`/`techstack`, `onboard`/`code_map` | parses as a non-empty mapping; every anchor matches `^[a-z][a-z0-9-]*$`; every section validates against `schemas/devforgeai/v1/stack.schema.json`; every section passes the same contract checks the gate applies (`compiled: true` implies `commands.build`, `test` implies `junit_path`, every `argv` non-empty, every `timeout_s` positive). With `jsonschema` or the schema file absent, refused |
| `.devforgeai/provenance/adr/**` | `amend`/`adr`, `architect`/`adr` | the path is `.devforgeai/provenance/adr/NNNN-<slug>.md` with a lowercase slug; its `kind` is `added`, because an ADR is append-only and a reversal is a new record whose `supersedes` names the old one; the text parses as frontmatter plus body and satisfies the `adr` template header — every key in `required_frontmatter` present, `id` matching `id_pattern` and equal to the filename's number, `template` and `template_version` accepted, every entry of `required_sections` present as a heading line, and no `forbidden_text` anywhere in the file. With the template absent, refused |

One step runs after the checks pass and before the checkpoint, and it is the only step in which the sequencer changes bytes a worker wrote:

| # | Step | On failure |
|---|---|---|
| 13a | resolve every `sha256:PENDING` digest in a changed Markdown artifact's frontmatter, in place, inside the candidate root. A worker has no hashing tool — its Bash surface is `devforgeai status` and `devforgeai run <key>` — so `plan`'s `story_writer` writes `sha256:PENDING` for each `provenance[]`, `context[]` and `commands.hash` entry, and the sequencer, which reads the root anyway, substitutes the real digest under exactly the rule the gate re-resolves with: section bytes for a `provenance[]` or `context[]` entry, the whole file for `commands.hash`, which pins all of `stack.yaml`. The substitution is byte-local: only a frontmatter `hash:` line whose value is exactly `sha256:PENDING` changes, resolved from the nearest preceding `source:` line. `sha256:FIXTURE` is a fixture marker, not a request, and is left alone. The substitution happens before the checkpoint, so the checkpoint holds resolved digests. Every substitution is recorded in the result row's `digests_resolved` and in `<phase>-report.md` | refuse when a source or an anchor does not resolve. Resolution reads the candidate root, so a source the same phase wrote does resolve; one that does not exist anywhere refuses the phase |

Without this step every plan-written story was refused by the dev gate as a placeholder hash, and the only way to run one was `--lenient`, which is itself refused for a story under `docs/plan/`. The digest the sequencer computes is the digest the gate will recompute, so a story it wrote opens a dev run with no flag.

The transition then runs in its own order, and no step of it moves a canonical byte:

| # | Step |
|---|---|
| 15 | run the phase's transition oracle (section 5.4) inside the candidate root, with cwd = `candidate.root` |
| 16 | on pass, `devforgeai candidate checkpoint <run> <phase>`: commit and tag in worktree mode, manifest and copy-aside in copy mode; record it as `run.yaml#candidate.checkpoint` |
| 17 | write `<phase>-result.json` with the derived `changed[]` and the checkpoint ref, render `<phase>-report.md`, release the lease, and advance |
| 18 | on any failure in 13a-16, leave the root at the last checkpoint plus the failed phase's work, record the problem rows, and either retry the same phase or rewind to the checkpoint `next` names |

The path rules in step 11 are absolute and no receipt may waive them. `ALWAYS_DENY` covers what the sequencer owns, and it is enforced twice: live by the dispatcher on every write tool call inside the root, and again here against `changed[]`. It has one carve-out on the canonical side, and only for a judge: `.devforgeai/work/<run>/evidence/<agent>/` is writable by the judge whose canonical worker name is `<agent>`, in the run that is active, and by nothing else. That prefix is not in any candidate root, is gitignored, and is never promoted, so admitting it widens no promotion path. It is `.devforgeai/state.yaml`, `.devforgeai/stack.yaml`, `.devforgeai/work/**`, `.devforgeai/provenance/**`, `.devforgeai/sessions/**`, `.devforgeai/hooks/**`, `.devforgeai/research-cas/**`, `.claude/**`, `.codex/**`, `.agents/**`, `.git/**`, `CLAUDE.md`, `AGENTS.md`. `docs/architecture/**`, `docs/plan/**` and `docs/research/**` are **not** in that list: they are governed per skill by the document fence in section 4, because the skills that own them must be able to write them. `.devforgeai/skills/**` is likewise absent, because that is `skill-generator`'s fence.

The carve-outs from that list are the **producer exceptions**, and they are narrow by construction: an artifact whose registry home in `11-artifact-registry.md` section 2 is under `.devforgeai/` has no other write path, so exactly the `(skill, phase)` pairs that produce it may write it, and only through a receipt that passes step 13.

| Path pattern | Artifact | May write it | Everything else |
|---|---|---|---|
| `.devforgeai/stack.yaml` | `stack` | `architect`/`techstack`, `onboard`/`code_map` | refused as sequencer-owned |
| `.devforgeai/provenance/adr/**` | `adr` | `amend`/`adr`, `architect`/`adr` | refused as sequencer-owned |

Both are written **inside the candidate root**, at `<candidate.root>/.devforgeai/stack.yaml` and `<candidate.root>/.devforgeai/provenance/adr/`. Canonical `.devforgeai/` is untouched until promotion, so the sequencer's claim to be the sole writer of the canonical tree survives the exception intact: the producer writes a candidate copy, the sequencer validates it, and promotion moves it.

Every other phase of those skills, every phase of every other skill, and every story `write_fence` entry are refused both paths; so is every sibling under `.devforgeai/provenance/`, because the exception is the ADR directory and not the prefix. The exception is also what lets those document fences name the path without the fence gate rejecting the entry as sequencer-owned. Both declared producers of the `adr` template now hold the exception and the fence entry: `amend`'s `adr` phase records a decision reached while amending, `architect`'s records one reached while designing, and both are validated against the same template header. The divergence `11-artifact-registry.md` section 6 recorded — a declared producer with no write path — is closed by that second pair, and that document should be updated to say so.

Both exceptions are checkpointed and rewound like any other fenced path. The candidate root excludes only `.git`, `.devforgeai/work`, the `.devforgeai/candidate` marker and `stack.yaml#ignore_dirs`, so a `stack.yaml` or an ADR a phase wrote is in the diff, in the checkpoint, and restored by a rewind. The old caveat that these two paths were invisible to the snapshot and had no rewind promise came from the canonical tree walk skipping `.devforgeai/`, and section 12 replaces that walk.

### 5.3 Recording

The accepted result is written to `.devforgeai/work/<run>/<phase>-result.json`: the receipt, normalised, plus the fields the sequencer adds. The record, not the receipt, is what every later reader consults.

| Added field | Value |
|---|---|
| `agent` | the canonical name, not the alias the worker used |
| `agent_id` | the stop event's `agent_id`, verbatim |
| `session_id` | the stop event's `session_id`, or the newest session evidence file |
| `captured_at` | UTC timestamp of validation |
| `changed` | the derived change set: one `{path, blob_sha256, kind}` row per path whose bytes differ between `candidate.input_checkpoint` and the root. The sequencer's own account, never the worker's |
| `checkpoint` | the checkpoint this phase created, `<run>/<phase>`; absent when the phase did not pass |
| `result_sha256` | digest over the canonical serialisation of the validated record |
| `application` | `accepted` once `changed[]` passed every check and the checkpoint exists, `refused` for a rejected or synthesised failure |
| `digests_resolved` | every `sha256:PENDING` substitution step 13a made, as `<path>: <source> -> <digest>`; empty when the phase changed no such file |

`<phase>-report.md` is rendered from the same record: skill, phase, status, run, agent and agent id, session, timestamp, reason code, requested rewind, resolved digests, note, issues, the changed paths and their kinds, the checkpoint, and the oracle's problem rows. It is a rendering, not a second source of truth. At a passing transition the sequencer copies it to `docs/reports/<skill>-<run>-<phase>.md`, which is a canonical path outside the candidate root: the rendered view is the one thing a run writes canonically before promotion, and it is written by the sequencer, so it is never in a candidate diff and never reported as worker-caused change.

### 5.4 Transition oracles

`devforgeai phase next` runs the oracle the active phase declares, inside the candidate root with cwd = `candidate.root`. Every oracle starts from the same invariants: no path in `changed[]` is outside the fence, and the package and import policy holds over the whole root. Drift is now a property of the root against its own checkpoint, not of the project against a gate snapshot, so a canonical edit made in the primary window while a run is open is not drift; it is a moved base, and it is caught at promotion instead.

| Oracle | Additional checks | Passing condition |
|---|---|---|
| `red` | build first when the section is compiled; broker `test`; classification is not `NO_TESTS` or `COLLECTION_ERROR`; the command exits non-zero; every `test_plan` name is present and `failed`, never `error`; no test outside `test_plan`; records `red_hashes` | the suite is red for the intended assertions, and only for them; classification is recorded as `EXPECTED_TEST_FAILURE` |
| `green` | every `test_paths` hash equals `red_hashes`; build when compiled; broker `test`; every `test_plan` name is `passed` | the tests that were red are green and were not edited to get there |
| `refactor` | everything `green` checks, plus `lint` exits zero when the run authorises the key | behaviour unchanged, structure improved, style clean |
| `document` | the phase declared `writes: docs` and `changed[]` is non-empty, unless it is marked conditional, in which case an empty change set needs a non-empty `note`; every changed path exists in the root with the bytes the checkpoint will hold | the document the phase owes exists inside its fence, or the run records why none was owed |
| `report_only` | the shared invariants only; from a judge, `changed[]` is empty, and every `evidence_refs` entry that is a findings path exists under this run's own `evidence/<agent>/` | the fence held and the stack policy holds |

Outcomes:

| Situation | Effect |
|---|---|
| no problems, another phase follows | advance; log `transition.pass`; render the report view |
| no problems, last phase | set `runs.<run>.status: ready_to_promote`; write a `REQUIRE_HUMAN` handoff whose `next` is `devforgeai promote <run>`; keep the candidate root and its checkpoints. The run's work is complete and unpromoted, which is a decision for a human, not a status the sequencer may close on its own |
| problems, attempts below the limit | attempt +1; log `transition.fail`; exit 1 with the rows on stderr so the same worker sees them and continues |
| problems, attempts at the limit | `REQUIRE_HUMAN` handoff; the story's status becomes `dev_blocked` and the run stays `active` with its lease released, so the candidate root survives for inspection; `devforgeai phase fail --reason <text>` is what abandons it |
| any problem row beginning `COULD_NOT_RUN` | routed by `gate_policy.test_runner_missing`; the handoff's next step is the repair, then the skill's command |
| result carries `next` | the root is rewound to the checkpoint the named phase started from — its predecessor's, or `base` when it is the first — so the named phase's own output is discarded; phase reports deleted, `red_hashes` cleared, `bounce_count` +1, phase set to the rewind target, that target's attempt +1; at its limit, `REQUIRE_HUMAN` |
| result status `needs_user` | `REQUIRE_HUMAN` handoff immediately; no retry, no attempt increment; the run stays `active`, lease released, `run.yaml#blocked_at` set; `phase start` with the same skill and argument resumes it (section 3) |

### 5.5 The SubagentStop ingest route, per provider

Both providers register the same dispatcher on `SubagentStop` with matcher `.*`. The dispatcher reads the event, extracts three fields, and hands them to the hook-only broker; it implements no second write path.

| Event field | Claude Code | Codex | Used as |
|---|---|---|---|
| `agent_type` | present inside a subagent | documented on `SubagentStop` | `--agent`; the trusted identity |
| `agent_id` | present inside a subagent | documented on `SubagentStop` | `--agent-id`; recorded in the result row |
| `last_assistant_message` | documented on `Stop` and `SubagentStop` | documented on `SubagentStop` | the receipt, on stdin |
| `session_id` | present | present | `--session-id`; recorded in the result row and every log line |
| `hook_event_name` | present | present | selects the route |
| `stop_hook_active` | present on `Stop` | present on `Stop` | recursion guard, `Stop` only |

The route:

1. The dispatcher invokes the broker with `DEVFORGEAI_ROOT` and `DEVFORGEAI_HOOK_EVENT=SubagentStop`, a 660-second bound, and the worker's final message on stdin.
2. A non-zero broker exit becomes a dispatcher block: exit 2 with the broker's output on stderr, which both providers show to the model, so the same worker fixes its work in the root and returns a fresh receipt. The lease is not released on a block: the worker that still holds it is the one being asked to continue.
3. A zero exit becomes a system message. Codex receives it as JSON `systemMessage`; Claude receives it on stdout.
4. When the event carries no `agent_type` or no `agent_id`, no checkpoint is taken and the subagent is not put in a loop it cannot escape. The sequencer writes a synthesised result — `status: could_not_run`, `reason_code: hook_fault`, `application: refused`, no `result_sha256`, an explanatory note — renders its report, logs `hook_fault`, releases the lease, writes a `REQUIRE_HUMAN` handoff, and exits 0. Whatever the worker wrote stays in the candidate root, unpromotable and inspectable, because the last checkpoint is still the last accepted state.

The dispatcher records that Claude Code documents `agent_id` and `agent_type` on any hook firing inside a subagent and `last_assistant_message` on `Stop` and `SubagentStop`, and that Codex documents the same three on `SubagentStop`. `09-hook-dispatcher.md` is the authoritative statement of what is confirmed from a primary source; where it still marks Claude's identity as asserted rather than confirmed, that document governs. Either way the posture is the same: identity on `PreToolUse` and `PostToolUse` is unconfirmed on Claude and undocumented on Codex, so a write is authorised by the lease bound at `SubagentStart` and by the path being under `candidate.root`, never by a claim in the tool event. The absent-identity branch above exists precisely because the field cannot be assumed.

## 6. Handoff envelope

`.devforgeai/work/<run>/handoff.json`, `devforgeai.handoff/v1`. Written at a completed run, at a block, at `devforgeai phase fail`, and again at `devforgeai promote <run>`. The block printed by the primary window and by `devforgeai status` is this file's rendering; it may not contain a fact this file does not hold.

| Corpus field group | Concrete fields | Required | Source |
|---|---|---|---|
| Location | `run`, `skill`, `phase`, `location` | yes | `run.yaml`; `location` is `.devforgeai/work/<run>/` |
| Result | `outcome`, `reasons[]` | yes | `pass` on completion, else the `gate_policy` action; `reasons` is the defect or completion list, never empty |
| Canonical artifacts | `artifacts[] {path, sha256, phase, checkpoint, status}` | no | the `changed[]` rows of each phase result. Until the run is promoted these paths name bytes in the candidate root, which is why each row carries the `checkpoint` they live in as well as the hash |
| Source basis | `source_basis[] {source, hash, status}` | no | the `provenance` and `context` entries the gate re-resolved |
| Validation | `validation[] {key, classification, exit, not_run}` | no | every brokered command outcome; `not_run: true` names a check that could not run and why |
| Decisions | `decisions[] {text, authority}` | no | decisions accepted during the run, each with a named authority |
| Open items | `open_items[] {id, text, owner, kind}` | no | unresolved ambiguities, risks, questions, blocked rows |
| Next action | `next` | yes | exactly one copy-pasteable command; mirrored into `state.yaml` as `next` |
| Session guidance | `session_id`, `session_guidance` | `session_id` yes | which session opened the run; `continue` or `fresh_session` |
| Authority / fence | `authority.write_fence[]`, `authority.requires_approval[]` | `write_fence` yes | `run.yaml#write_fence` |
| Repair route | `repair_route[] {defect, owner, command}` | no | the skill that owns the failing template, and the command that re-runs it |
| Result | `verdict` | no | the frontmatter `verdict` of the report the last phase's receipt named in `evidence_refs`, on a report-producing skill only. It selects the row this envelope renders and therefore `next`; it never changes `outcome` |

`outcome` is `pass`, `BLOCK`, `REQUIRE_HUMAN`, `WARN` or `OFF`. `BLOCK` is what `devforgeai phase fail` records. `REQUIRE_HUMAN` is what an exhausted attempt budget, a `needs_user` result, a missing worker identity, the default `test_runner_missing` policy, and a completed-but-unpromoted run record. `pass` is now written at one moment only: a successful `devforgeai promote <run>`, when the work has actually reached the canonical tree. `WARN` and `OFF` appear only when a story loosened `test_runner_missing`; the run is still closed.

Rendering rules, enforced by the sequencer and checked by `skill-validator`:

| # | Rule |
|---|---|
| 1 | `next` is never empty and is never a description. One exact command. |
| 2 | Blocking items are printed before the forward command; `open_items` precede `next`. |
| 3 | Exactly one forward path is numbered `1.`; alternatives are printed under "Also possible". |
| 4 | Every printed command works from a cold session, because it resolves through `state.yaml`. |
| 5 | A gate or critic failure names the owning skill and the command that re-runs it, from `repair_route`. |
| 6 | One line shows the phase completed, the phase active, and the phases remaining. |
| 7 | The run-end block and the `devforgeai status` block are the same rendering of the same file. |
| 8 | The renderer adds nothing. A field absent from the envelope is absent from the block. |
| 9 | A row whose `next` names another skill's command is a handoff, never a call. No skill invokes another skill's run: `phase start` refuses while a run is active, and refuses a story that another unpromoted run already holds, and the promotion that clears the run has not happened by the time the block is printed, so the named command is run afterwards by a human or a fresh session. A specification's procedure may not describe a nested run, and the sequencer never starts one. |
| 10 | A report-producing skill selects its row with the report's frontmatter `verdict`, not with the run's status. `pass` keeps the skill's default row; `findings` and `fail` select the repair row. The run's `outcome` stays `pass` in all three cases, because reporting a defect is a passing run and the report is the artifact the phase owed. |

Rule 7 is a single function, `render_handoff`, in `examples/hooks/devforgeai.py`. `phase next` and `promote` call it when they write the envelope, and `devforgeai status` calls it over the envelope on disk, after the run block and without writing anything: for the active run that is `.devforgeai/work/<run>/handoff.json`, and with no run active it is the most recent `work/*/handoff.json`, ordered by the envelope's own `at` and then by path so the choice is deterministic. A missing or unreadable envelope prints nothing at all — the run block is then the whole output — because `status` reports state and never fails on it. Rule 8 is why the two blocks cannot drift: neither caller formats a field, so `status` prints the reasons, the open items and the one `next` the envelope holds, and nothing else.

The default next steps the sequencer selects:

| Situation | `next` |
|---|---|
| any run, all phases passed, not yet promoted | `devforgeai promote <run>` |
| story run, promoted | `/review <arg>` |
| document run, promoted, no verdict or `verdict: pass` | `/status` |
| `review`, promoted, `verdict: findings` or `fail` | `/dev <arg> --fix` |
| `qa`, promoted, `verdict: findings` or `fail` | `/dev <arg> --fix` |
| `skill-validator`, promoted, `verdict: findings` or `fail` | `/skill-gen <arg> --fix` |
| `STALE_BASE` in copy mode, or `MERGE_CONFLICT` | resolve the named canonical paths, then `devforgeai promote <run>` |
| `DIRTY_TARGET` | commit or discard the named canonical edits, then `devforgeai promote <run>` |
| any problem row beginning `COULD_NOT_RUN` | install the missing runner, then `/<skill> <arg>` |
| `REQUIRE_HUMAN`, blocked run (`needs_user` or attempt limit), the user has answered or fixed the cause | `/<skill> <arg>` (resumes at `blocked_at`, section 3) |
| `REQUIRE_HUMAN`, story run, the story itself needs changing | `devforgeai phase fail --reason <text>`, then `/clarify <arg>` |
| `REQUIRE_HUMAN`, document run, abandoning | `devforgeai phase fail --reason <text>`, then `/status` |
| `BLOCK`, `WARN` or `OFF` | `/<skill> <arg> --fix` |

Every run therefore ends in two blocks, not one. The first is written when the last phase passes: the work is done, it lives in the candidate root, and the one forward command is `devforgeai promote <run>`. The second is written when promotion succeeds, and its `next` is the row above that matches the skill and verdict. A run that is never promoted leaves the first block standing, which is exactly the state it is in.

The three verdict rows are the whole of what `02-skill-roster.md` calls a "findings" or "fail" outcome for `review`, `qa` and `skill-validator`. They exist because those skills' runs pass: the phase wrote the report it owed, the oracle held, and the defect lives inside the report. Before the report verdict was read the sequencer had no way to tell those rows apart from a clean run and named `/status` for all of them. `skill-validator`'s `<arg>` is the skill it validated, so its repair row names `/skill-gen <skill> --fix`; `02-skill-roster.md` writes the same row as `/skill-gen {spec}`, and the spec id is not a value the sequencer holds (`11-artifact-registry.md` section 6).

No handoff row is a call. `02-skill-roster.md` used to give `plan` a call to `/analyze`, `skill-generator` a call to `/skill-validate`, `retro` a call to `/amend`, `architect` a loop back to `/brainstorm` and `dev` a call to `/clarify`. None of those can nest: `phase start` refuses while a run is active, and there is no operation that suspends a run. Each is a handoff whose first `next` step is that command, run after the run was promoted or abandoned.

Research is the exception. Its typed handoff contract is `src/devforgeai/skills/research/contracts/handoff.md`; on the successful path Research Core writes it and the framework does not restate it. A Research failure returns a typed error, seals nothing, and the framework handoff is rendered from that error, taking `next` from the error's repair route. The rule that a user is never left asking "what's next?" therefore holds on every path.

## 7. `stack.yaml`

`.devforgeai/stack.yaml` is a mapping of anchor name to section. A story pins the whole file by hash and names one anchor: `commands.source: .devforgeai/stack.yaml#python` with `commands.hash: sha256:<64 hex>`. The gate verifies that hash, copies `source` and `use` into `run.yaml`, and never re-reads the story afterwards.

Producers: `architect`'s `techstack` phase emits the INTENDED sections beside `techstack.md`; `onboard`'s `code_map` phase emits the OBSERVED sections. Those two phases are the only ones that ever handle the file's contents, and they write it like any other fenced file, inside the candidate root. No consuming worker sees it: a phase names a command key, and the sequencer resolves and runs it.

The write path is closed, and narrowly. `.devforgeai/stack.yaml` stays in `ALWAYS_DENY` for every skill and every phase except the two that produce it: it is in `architect`'s and `onboard`'s document fence, and only `architect`'s `techstack` phase and `onboard`'s `code_map` phase may name it in a result. A candidate `stack.yaml` is accepted only after the sequencer parses it, checks every anchor name, validates every section against `schemas/devforgeai/v1/stack.schema.json`, and re-runs the section contract checks (section 5.2, step 13); one that fails any of those refuses the phase, and the root is rewound or retried rather than promoted. Deleting the file is never accepted.

Two consequences a specification must carry rather than assume away. First, a `stack.yaml` a run wrote is inside the candidate root until promotion, so every run in flight resolves its command keys from the hash-pinned section it anchored at its own gate, not from another run's in-progress rewrite. Second, once such a run is promoted it changes the digest any story pinned against that file, so the next `phase start` for that story is a stale-hash refusal until the story is re-sliced. That is the intended effect, not a defect.

| Key | Type | Required | Meaning |
|---|---|---|---|
| `version` | `1` | yes | section contract version |
| `compiled` | boolean | yes | `true` requires `commands.build`, and the oracle runs it before `test` at every transition |
| `package_manager` | string | yes | informational; names the manifest ecosystem |
| `manifests` | glob array | yes | the only files scanned for dependency policy |
| `commands` | mapping | yes | keys `build`, `test`, `lint`, `format`; `test` is mandatory |
| `commands.<key>.argv` | string array | yes | exec form; launched without a shell, so no redirect, pipeline, substitution or variable is interpreted |
| `commands.<key>.cwd` | string | no | repository-relative; defaults to the root |
| `commands.<key>.junit_path` | string | `test` only | where the runner writes JUnit XML; the oracle reads per-test outcomes from this file, not from stdout |
| `commands.<key>.timeout_s` | integer | no | defaults to 600; exceeding it is `TIMEOUT` |
| `ignore_dirs` | glob array | no | defaults to empty. Root-relative build and cache directories: excluded when copy mode materialises the candidate root, excluded from the tree-hash manifest that copy mode uses for `base_ref` and every checkpoint, and ignored by the mutation check on a brokered command, which would otherwise read a compiler's own output as an undeclared write. Nothing listed here is promoted or rewound |
| `test_glob` | glob | yes | where tests live |
| `test_layout` | string | yes | the project's test placement convention |
| `runner_probe` | `{argv[], exit_ok}` | yes | cheap liveness check; a probe that misses is `runner_missing`, never a phase failure |
| `packages.allow` | string array | yes | exact names, compared case-insensitively against every name an extractor captures; empty disables the check |
| `packages.deny` | regex array | yes | matched against manifest text; any match refuses |
| `extractors` | array of `{paths?, regex}` | yes | capture group 1 is the package name; an extractor without one is a policy error, not a silent pass |
| `forbidden_imports` | array of `{paths, patterns, reason}` | yes | source-level bans; `reason` is quoted verbatim in the refusal |

Classification of a brokered command, closed set: `PASS`, `EXPECTED_TEST_FAILURE`, `TEST_FAILURE`, `NO_TESTS`, `COLLECTION_ERROR`, `INFRA_FAILURE`, `TIMEOUT`. `INFRA_FAILURE` and `TIMEOUT` map to worker status `could_not_run` with `reason_code` `runner_missing` and `timeout`; they are never a phase failure and never consume an attempt.

### 7.1 Interpreted example: Python, not compiled

From `examples/hooks/fixtures/.devforgeai/stack.yaml`, anchor `python`:

- `compiled: false`, so no `build` key is required and none is defined. The section should declare `ignore_dirs: [__pycache__, .pytest_cache]`, so a test run's caches are not read as writes. A virtualenv is deliberately **not** listed: excluding it from a copy-mode root would leave the root with no `pytest` and turn every copy-mode run into `runner_missing`.
- `commands.test` is `python3 -m pytest -q --junitxml=.devforgeai/work/junit.xml` with `junit_path: .devforgeai/work/junit.xml` and `timeout_s: 600`. The oracle deletes that file before the run, so a stale report cannot be read as a fresh result.
- `manifests` are `pyproject.toml` and `requirements*.txt`; two extractors read package names out of each syntax.
- `packages.allow` is `pytest`, `ruff`, `pyyaml`; `packages.deny` refuses any case-insensitive match of `sqlalchemy` or `django` anywhere in a manifest.
- `forbidden_imports` refuses an `import sqlalchemy` or `import django` under `tinyapp/**`, quoting `techstack.md#data-access mandates raw sqlite3; no ORM`.

A `green` phase that adds SQLAlchemy to `pyproject.toml` inside the root is refused twice: by the deny pattern and by the allowlist. The bytes exist in the candidate root and reach the canonical tree never, because the phase does not pass and the run is not promoted.

### 7.2 Interpreted example: C#, compiled

Same file, anchor `csharp`:

- `compiled: true`, so `commands.build` (`dotnet build --nologo`) is mandatory at the gate and the oracle runs it before `test` on every transition. A run that does not authorise the `build` key fails the transition with an explicit message rather than skipping the build. The section should declare `ignore_dirs: [bin, obj]`: a compiled stack writes output on every build, and without that list every `devforgeai run build` would register as an undeclared mutation.
- `commands.test` is `dotnet test --nologo --logger "junit;LogFilePath=.devforgeai/work/junit.xml"` with `timeout_s: 1200`; the longer bound is the only difference the oracle sees.
- `manifests` are `**/*.csproj` and `Directory.Packages.props`; the extractor captures `Include="..."` from each `PackageReference`.
- `packages.allow` admits `Dapper`, `Microsoft.Data.SqlClient`, `xunit`, `xunit.runner.visualstudio`, `Microsoft.NET.Test.Sdk` and `JunitXml.TestLogger`. `packages.deny` refuses `Microsoft\.EntityFrameworkCore`.
- `forbidden_imports` refuses `using Microsoft.EntityFrameworkCore` under `src/**`, quoting `techstack.md#data-access mandates Dapper`.

A phase that adds a Dapper `PackageReference` is accepted; the equivalent Entity Framework change is refused at ingest by the per-path scan, and again by the whole-root rescan in step 14 if it arrives in combination with something the per-path scan admitted.

## 8. Session evidence

`.devforgeai/sessions/<session_id>.json`, `devforgeai.session/v1`, created once per provider session by the hook-only `devforgeai session-start` operation at `SessionStart`, and appended to whenever a run in this session grants or releases a write lease.

| Field | Meaning |
|---|---|
| `schema` | `devforgeai.session/v1` |
| `session_id` | the provider's session identifier, verbatim; `unknown` when the event carried none |
| `provider` | `claude` or `codex` |
| `provider_version` | from the event, or `unknown` |
| `dispatcher_sha256` | content hash of the installed dispatcher, or `ABSENT` |
| `hooks_armed` | whether the dispatcher was present beside the sequencer |
| `state_parsed` | whether `state.yaml` loaded as a mapping |
| `stack_resolvable` | whether the active run's anchor resolved to a section; `true` when no run is active |
| `at` | UTC creation timestamp; the newest `at` in the directory names the current session |
| `lease_events[]` | optional, appended: one `{kind: granted\|released, run, phase, agent, agent_id, root, at}` row per write-lease grant and release. `granted` is written at `SubagentStart`, `released` at `ingest-result`, whatever the receipt's status |

This is the evidence that the chain was armed, what it could resolve, and who was allowed to write while it ran. It is not a session model, holds no conversation state, and is never read to decide a transition — the live lease is `run.yaml#lease`, and `lease_events[]` is only its history, so a corrupt or missing session file loses an audit trail and never grants a write. Its one operational use is naming: `<phase>-result.json` rows, `handoff.json`, and every `provenance/log.jsonl` line carry the `session_id` that points at this file. A missing dispatcher is the one fault a later hook cannot report, which is why this file is written first and why `hooks_armed: false` is a legitimate recorded value rather than an error. In a repository with no `.devforgeai/` directory the operation prints that nothing is armed and exits 0; `SessionStart` never faults on an uninstalled repository.

## 9. Enforcement block

`.devforgeai/work/<run>/run.yaml`, `schemas/devforgeai/v1/run.schema.json`. Written by the sequencer at `devforgeai phase start` and updated at every transition. It outlives the candidate root: promotion and abandonment remove the root, branch, tags and copy-aside, and leave `run.yaml` with the final status so `devforgeai status`, inspection and `NO_CANDIDATE` still resolve. It is gitignored and per-run: it never enters a commit, a checkpoint or a promotion, and two runs never share one. Nothing in it is derived at hook time from a Markdown document: the gate resolved every value once and recorded the result, so a hook reads one file and decides.

The name "enforcement block" is kept for what this file holds, because that is what every skill specification calls it. What changed is where it lives: it used to be a mapping inside canonical `state.yaml`, which made two concurrent runs impossible and put per-phase churn into a tracked file. Section 12.3 states the split and the two-marker rule that resolves which file a process is looking at.

| Field | Type | Meaning |
|---|---|---|
| `run` | string | evidence directory name; the story id for a story run, `<skill>-<arg>` otherwise |
| `skill` | string | canonical skill; a variant is resolved before writing |
| `arg` | string | the `devforgeai phase start` argument |
| `kind` | `story` or `document` | which gate ran |
| `phase` | string | the active phase |
| `attempts` | mapping | one counter per phase, initialised to 0 |
| `max_attempts` | mapping | one limit per phase, materialised from the registry; there is no `default` key in the written block |
| `started_at` | timestamp | when the gate passed |
| `session_id` | string | the session the run opened under; empty when no `SessionStart` hook has run |
| `write_fence` | pattern array | the story's fence, or the skill's document fence with the argument substituted |
| `test_paths` | pattern array | every distinct `test_plan` file; empty for a document run that is not story-anchored |
| `test_plan` | row array | the criterion-to-test rows; empty for a document run that is not story-anchored |
| `commands` | mapping | `{source, use}` for a story run and for a story-anchored document run (`qa`, `review`); `{}` for every other document run |
| `gate_policy` | mapping | the defect-to-action map, copied from the story; `{unresolvable_source: BLOCK}` for a document run that is not story-anchored |
| `canonical` | path | absolute path to the canonical checkout this run was opened from; the way back out of the root |
| `candidate` | mapping | `{mode, root, base_ref, checkpoint, branch?}`; section 12 |
| `lease` | mapping or null | `{session_id, agent, agent_id?, phase, granted_at}`; the one producer allowed to write, or `null` |
| `granted_keys` | key array | the keys the active phase may broker: its registry `run_keys` intersected with `commands.use` |
| `gate_warnings` | string array | optional; one row per defect the gate downgraded instead of refusing (section 3.4). Absent when the gate refused everything it found |
| `bounce_count` | integer | optional; how many times this run has been rewound. Distinct from `attempts`, which counts dispatches per phase |
| `red_hashes` | mapping | optional; test-file hashes inside the root, recorded when a tests-writing phase passes, cleared on rewind |
| `last_oracle` | mapping | optional; the most recent brokered command's key, classification and exit, for the report renderer only |

The file is live only while canonical `state.yaml#runs.<run>.status` is `active`. `ready_to_promote`, `promoted` and `abandoned` all mean no phase is running: every write is denied, and the only operation left for that run is `devforgeai promote <run>`. A `run.yaml` whose run is not `active` is stale evidence, not authority.

Checkpoint and rewind. `devforgeai phase start` creates the candidate root and its `base` checkpoint; every passing transition adds one more. A rewind names the phase to redo, and resets the root to the checkpoint that phase *started from* — its predecessor's checkpoint, or `base` when it is the first phase — because the named phase's own output is exactly what is being discarded. `next: red` from `green` therefore resets to `base`, not to `red`: the tests red wrote are what green found wanting. In worktree mode that is `git reset --hard devforgeai/<run>/<pred(P)>`; in copy mode it restores that checkpoint's copy-aside and deletes every file absent from its manifest. The rewind is over the whole root, so it is exact for modes, deletions and files the old fence-copy scheme never held.

Every path in the root is covered, which closes three holes the previous snapshot scheme left open. `skill-generator`'s fence `.devforgeai/skills/<arg>/**` is checkpointed and rewound like any other path; **the "no rewind promise for `skill-generator`" caveat is withdrawn**, and a specification for that skill may now assume a failed phase leaves the previous generated files exactly as the last checkpoint had them. `.devforgeai/stack.yaml` and `.devforgeai/provenance/adr/**`, in `architect`'s, `onboard`'s and `amend`'s fences, are the same: written in the root, checkpointed, rewound. The only paths a candidate root does not carry are `.git`, `.devforgeai/work`, the `.devforgeai/candidate` marker and `stack.yaml#ignore_dirs`, and none of those is ever a fence entry.

## 10. Evidence files

| Path | Format | Producer | Consumer |
|---|---|---|---|
| `.devforgeai/state.yaml` | YAML | sequencer at `devforgeai phase start` (register the run), at promotion and at abandonment, under the lock | hook dispatcher, `devforgeai status`, every gate |
| `.devforgeai/work/<run>/run.yaml` | YAML | sequencer at `devforgeai phase start` and at every transition; gitignored | hook dispatcher on every event, every gate, `devforgeai status` |
| `.devforgeai/stack.yaml` | YAML | `architect` `techstack` (INTENDED) and `onboard` `code_map` (OBSERVED) write it in the candidate root; the sequencer validates it against `stack.schema.json` and promotion moves it | gate, transition oracle, stack policy scans |
| `.devforgeai/work/<run>/context.json` | JSON | `devforgeai phase start` (sub-phase 1, Slice) | every worker of the run, by path |
| `.devforgeai/work/<run>/wt/**` | working tree | the run's producers, under the lease; the sequencer creates and removes it | the run's judges, the transition oracles, promotion |
| `.devforgeai/work/<run>/cp/<phase>/**` | file copies | `devforgeai candidate checkpoint`, copy mode only | rewind restore |
| `.devforgeai/work/<run>/<phase>.manifest.json` | JSON | `devforgeai candidate checkpoint`, copy mode only | the checkpoint diff, rewind, promotion base check |
| `.devforgeai/work/<run>/evidence/<agent>/**` | any text | the judge phase named `<agent>`, directly; the only canonical path a worker writes | the sequencer at ingest, the report renderer, the human; named in `evidence_refs` |
| `.devforgeai/work/<run>/<phase>-result.json` | JSON | `devforgeai ingest-result` | `devforgeai phase next`, report rendering, `qa` and `retro` workers by path |
| `.devforgeai/work/<run>/<phase>-report.md` | Markdown | `devforgeai ingest-result` and `devforgeai phase next` | the human; rendered forward to `docs/reports/` |
| `.devforgeai/work/<run>/handoff.json` | JSON | `devforgeai phase next`, `devforgeai phase fail` and `devforgeai promote` | `devforgeai status`, the primary window's printed block, the `Stop` hook check |
| `.devforgeai/sessions/<session_id>.json` | JSON | `devforgeai session-start` | `devforgeai status`, result and log rows, session-fault diagnosis |
| `.devforgeai/provenance/log.jsonl` | JSONL | every write operation | `analyze`, `retro`, `drift` |
| `.devforgeai/provenance/adr/NNNN-*.md` | Markdown | `architect` `adr`, `amend` `adr` | `analyze`, `review`, `drift` |
| `docs/reports/<skill>-<run>-<phase>.md` | Markdown | sequencer at a passing transition | the human, `retro` `collect`, `review` |

The log line kinds are `session.start`, `phase.start`, `result.ingested`, `command.run`, `transition.pass`, `transition.fail`, `rewind`, `blocked`, `hook_fault`, `lease.granted`, `lease.released`, `candidate.checkpoint`, `candidate.rebase`, `candidate.promote`, and `candidate.abandon`. Every line carries `at`, `kind`, and `session_id`; every `candidate.*` and `lease.*` line also carries `run`.

`docs/reports/*` is a rendered view, not a second evidence home. A producer writes only inside its candidate root; a judge writes only under `.devforgeai/work/<run>/evidence/<agent>/`; neither writes anywhere else, and both return a receipt.

## 11. Per-skill evidence and gate table

Every skill specification fills this table in its section 7, one row per phase, in phase order:

```
| phase | worker | deterministic gate check | gate_policy | evidence file | transition oracle |
```

Column rules:

- **phase** — the registry name from section 4, exactly.
- **worker** — the canonical worker name, or `—` for a phase with no worker. A phase with no worker cannot exist in the current registry; every row has one.
- **deterministic gate check** — what a script verifies before or after this phase, with no model judgement, against the candidate root rather than against the worker's account of it. "The worker confirms" is not a gate check.
- **gate_policy** — the defect class this phase's failure maps to, and its action. At transition time only `test_runner_missing` changes behaviour; at the gate only `unresolvable_source` can be downgraded, and only as section 3.4 allows. Every other entry documents intent and refuses.
- **evidence file** — the exact path, with `<run>` and `<phase>` substituted.
- **transition oracle** — the oracle name from section 5.4 and the one condition that makes it pass.

`dev` is the worked example. Every other specification follows this shape.

| phase | worker | deterministic gate check | gate_policy | evidence file | transition oracle |
|---|---|---|---|---|---|
| `red` | `red_dev` | story is `template_version: 3` and `status: ready`; no `ASSUMPTION:` outside Clarifications; every `blocked_by` story is `done`; `write_fence`, `test_plan` and `commands` present; every `test_plan` row has criterion, file and name, and its file is inside the fence; no fence entry is sequencer-owned; `commands.source` exists and `commands.hash` is current; every `provenance[]` and `context[]` entry re-resolves to its recorded digest; the section satisfies the `stack.yaml` contract; the existing tree already passes the package and import policy | `unresolved_assumption: BLOCK`, `stale_hash: BLOCK`, `unresolvable_source: BLOCK`, `criterion_without_test: BLOCK` | `.devforgeai/work/<run>/red-result.json`, `red-report.md` | `red`: fence held, stack policy held, `test` exited non-zero, every `test_plan` test present and `failed` rather than `error`, no test outside `test_plan`; records `red_hashes` |
| `green` | `green_dev` | every derived changed path is inside `write_fence` and none is a `test_paths` entry; `changed[]` is a subset of `claimed_paths`; no changed file adds a denied or unlisted package or a forbidden import | `write_fence_violation: BLOCK`, `test_runner_missing: REQUIRE_HUMAN` | `.devforgeai/work/<run>/green-result.json`, `green-report.md` | `green`: fence held, stack policy held, every `test_paths` hash equals `red_hashes`, every `test_plan` test `passed`. `status: fail` with `next: red` rewinds instead |
| `refactor` | `refactor_dev` | as `green`, and the run authorises the `lint` key | `write_fence_violation: BLOCK`, `test_runner_missing: REQUIRE_HUMAN` | `.devforgeai/work/<run>/refactor-result.json`, `refactor-report.md` | `refactor`: everything `green` checks, plus `lint` exits zero. `status: fail` with `next: red` rewinds instead |
| `smoke` | `smoke_qa` | the phase is a judge: it holds no lease, `changed[]` is empty, and its only write path is `.devforgeai/work/<run>/evidence/smoke_qa/` | `test_runner_missing: REQUIRE_HUMAN` | `.devforgeai/work/<run>/smoke-result.json`, `smoke-report.md` | `report_only`: no file outside the fence changed and the stack policy holds |
| `review` | `dev_critic` | the phase is a judge: `changed[]` is empty, its only write path is `.devforgeai/work/<run>/evidence/dev_critic/`, and it is granted no command key | `criterion_without_test: BLOCK` | `.devforgeai/work/<run>/review-result.json`, `review-report.md`, then `handoff.json` | `report_only`: as `smoke`. On pass this is the last phase: the run becomes `ready_to_promote` and the handoff names `devforgeai promote <run>`; `/review <story>` is the `next` the promotion handoff carries |

Attempt budgets for that table are `red: 2`, `green: 3`, `refactor: 2`, `smoke: 2`, `review: 2`. A rewind from `green` or `refactor` names `red`, so it resets the candidate root to `base` — red is the first phase, and its tests are what the rewind exists to rewrite — and costs an attempt at `red`, so a story cannot loop indefinitely: the budget is exhausted and the run hands off to a human with its root intact for inspection.

## 12. The candidate root

Every anatomy-governed run gets one candidate root: a complete, runnable copy of the project that the sequencer creates at `phase start`, owns until promotion or abandonment, and then deletes. Producers write there with Edit and Write, run the suite there with `devforgeai run <key>`, and never touch a canonical byte. The canonical checkout stays where the primary session is, unchanged and usable, for the whole life of the run.

That is the whole of the write model. Everything else in this document — the receipt, the derived change set, the checkpoint diff, the lease, the promotion refusals — exists because writes happen in a root the sequencer owns rather than in the tree the user is looking at.

### 12.1 Two materialisations, one contract

The sequencer picks the mode at `phase start` by probing for a git repository at the canonical root, and records it as `run.yaml#candidate.mode`. Skills, worker prompts, dispatcher checks, oracles and the receipt are identical in both; only the six mechanical operations below differ.

| | worktree mode (default when the project is a git repository with at least one commit) | copy mode (fallback: no git repository, or a fixture tree) |
|---|---|---|
| create | `git worktree add -b devforgeai/<run> <root> <base_ref>`, then write the `.devforgeai/candidate` marker; `base_ref` is the canonical HEAD at `phase start`, pinned in `run.yaml` | copy the project tree to `<root>`, excluding `.git`, `.devforgeai/work` and `stack.yaml#ignore_dirs`, then write the marker; `base_ref` is the sha256 of the sorted tree-hash manifest |
| root path | `.devforgeai/work/<run>/wt`, gitignored | same |
| checkpoint at each transition | commit on the run branch, tag `devforgeai/<run>/<phase>` | write `<phase>.manifest.json` and copy every changed file aside under `.devforgeai/work/<run>/cp/<phase>/` |
| rewind to phase P | `git reset --hard devforgeai/<run>/<pred(P)>` inside the root, where `pred(P)` is the phase before P and `base_ref` when P is the first | restore the copy-aside for `pred(P)` and delete every file absent from its manifest |
| promote | refuse unless canonical HEAD equals `base_ref` (`STALE_BASE`) and no dirty canonical file is among the run's changed paths (`DIRTY_TARGET`); then `git merge --ff-only devforgeai/<run>` in the canonical checkout, under the sequencer lock | refuse unless the canonical tree manifest equals `base_ref` (`STALE_BASE`); then copy every changed path's exact bytes into the canonical tree under the lock, deleting the paths the candidate deleted |
| abandon | `git worktree remove --force`, then delete the branch and its tags | delete `<root>` and `cp/` |

Copy mode exists so the framework runs in a tree with no repository — a fixture, a scratch root, a directory a user has not initialised — and it pays for that with a full tree copy at `phase start` and no rebase on a moved base. Worktree mode is the default wherever git is present because a checkpoint is then a commit, a rewind is exact for modes and deletions, and a moved base is recoverable.

The framework does not use the Agent tool's own worktree isolation option, and does not fork a worktree per subagent. Both fork from HEAD, which would give each phase its own base and reintroduce the model-side merge this design exists to avoid. One root per run, sequential phases inside it.

Two rules bind every worker, in both modes:

- Every write a producer makes resolves inside `candidate.root`. A write outside it is denied by the dispatcher, on both providers, whether or not a run is active.
- `devforgeai run <key>` executes with cwd = `candidate.root`, so a test run sees the candidate's code and the candidate's tests, and its output lands in the candidate's `junit_path`.

The primary session stays in the canonical checkout. It never cds into a root, and it never needs to: `devforgeai status` prints the run, the root, the phase, the fence and the granted keys, and the primary pastes that block into the dispatch prompt.

### 12.2 Linear history and the lease

For one run the phases build linearly on one root: `base` → `red` → `green` → `refactor`, with `smoke` and `review` reading the `refactor` checkpoint. No merge exists between phases, by construction. Each phase is dispatched against the checkpoint the previous one created, and the receipt names that checkpoint so a stale dispatch is caught rather than silently rebased.

`run.yaml#lease` records `{session_id, agent, agent_id?, phase, granted_at}`. Exactly one producer holds it at a time:

| Moment | Effect |
|---|---|
| `SubagentStart` for a producer phase | grant the lease, or refuse with `LEASE_HELD` if one is already held. This is the only identity-bearing pre-write event on either provider, which is why the binding happens here and nowhere else |
| any write tool call inside the root | allowed only while the lease is held, and on Claude only when the event's `agent_id` equals the lease's. On Codex, where `PreToolUse` carries no identity, the root is the fence: a path under `candidate.root` and inside the phase fence is the whole test |
| `SubagentStart` for a judge phase | no lease is granted. A judge's write tools are denied outright, so several judges may read the same checkpoint at once |
| `ingest-result` | release the lease, whatever the receipt's status |
| dispatcher block (broker exit non-zero) | the lease is **not** released: the same worker is being asked to continue in the same root |

Parallel work is parallel runs, not parallel workers: separate stories, separate roots, separate sessions, because Codex's one-open-worker cap is per session. `phase start` refuses a story whose `write_fence` overlaps the fence of any run that is `active` or `ready_to_promote`, with reason `FENCE_OVERLAP`. The producer-exception paths count as fence members for that test, so two `architect` runs cannot both be open even though their document fences differ elsewhere.

Promotion is serialised under `.devforgeai/lock`. Two disjoint runs that finish together therefore promote one at a time, and the second sees `STALE_BASE` because the first moved canonical HEAD. What happens next is the sequencer's work, not the model's: in worktree mode it runs `git rebase <new HEAD>` inside the root, re-runs the last transition's oracle there, and retries the fast-forward once. A rebase conflict is `git rebase --abort`, status `needs_user`, reason `MERGE_CONFLICT`, and no canonical byte has moved. In copy mode there is no rebase, so `STALE_BASE` returns `needs_user` directly.

A clean detached worktree for `qa` and `review` to verify in, an automated integration run for overlapping fences and for `STALE_BASE` in copy mode, and the OS sandbox are all post-MVP (`12-post-mvp.md#pm-11`, `#pm-12`, `#pm-04`).

### 12.3 State split and root resolution

Canonical `.devforgeai/state.yaml` is tracked, and holds story statuses and one row per run — nothing per-phase, so a transition never dirties a tracked file:

```yaml
version: 1
target: [claude, codex]
mode: brownfield
slug: tinyapp
phase: dev
active_sprint: sprint-001
stories:
  STORY-001:
    status: in_dev              # ready | in_dev | dev_done | dev_blocked | review_failed | qa_failed | done
    sprint: sprint-001
    last_command: "/dev STORY-001"
    run: STORY-001
runs:
  STORY-001:
    story: STORY-001
    skill: dev
    mode: worktree              # worktree | copy
    root: .devforgeai/work/STORY-001/wt   # relative: state.yaml is tracked and carries no machine path
    base_ref: 4f9c1e2a8b7d6c5f4e3d2c1b0a9f8e7d6c5b4a39
    checkpoint: green
    status: active              # active | ready_to_promote | promoted | abandoned
next: "/dev STORY-001"
```

Per-run enforcement — `phase`, `write_fence`, `test_paths`, `granted_keys`, `lease`, `attempts`, `bounce_count` — lives in `.devforgeai/work/<run>/run.yaml`, which is gitignored (section 9). Canonical state is written at exactly three moments, always under the lock: `phase start` registers the run, promotion marks it `promoted`, abandonment marks it `abandoned`.

The sequencer never commits on the target branch. A promotion's edits to canonical `state.yaml` are working-tree edits, which the owner commits alongside the story's code; a framework that committed for the user would decide the granularity of their history.

**Root resolution is a two-marker rule.** A candidate root is a copy of the project, so it contains a `.devforgeai/` of its own — checked out or copied at `base_ref`, holding a stale `state.yaml` and `stack.yaml`. Walking up to the nearest `.devforgeai/` is therefore not enough on its own; what distinguishes the two is one file that only a candidate root has.

`candidate open` writes `<root>/.devforgeai/candidate`, two lines and nothing else:

```yaml
run: STORY-001
canonical: /home/u/proj
```

The rule is then: walk up from cwd to the nearest `.devforgeai/` directory, and look for that marker.

| What that directory contains | Where you are | Canonical root | Active run |
|---|---|---|---|
| a `candidate` marker | inside a candidate root | the marker's `canonical` | the marker's `run`; its enforcement file is `<canonical>/.devforgeai/work/<run>/run.yaml` |
| no `candidate` marker | the canonical checkout | the directory containing it | `state.yaml#runs` filtered to `status: active` |

The marker is the only thing a candidate root's `.devforgeai/` is consulted for. `run.yaml` itself lives on the canonical side, at `<canonical>/.devforgeai/work/<run>/run.yaml`, because a per-phase file inside the root would be committed by every worktree-mode checkpoint and promoted with the run. The marker is excluded from the checkpoint diff for the same reason, and it is the one path inside a root that is neither checkpointed nor promoted.

A hook process may pass `--run <id>` to skip the walk entirely, and does so wherever the event carries the run.

Nothing inside a candidate root ever reads that root's `state.yaml` or `stack.yaml` as authority. A worker reads `.devforgeai/work/<run>/context.json` and the paths its brief names; the sequencer resolves the run's stack section from the canonical side, through the marker, and every hook does the same. That is what stops a run from resolving against its own stale copy of the file it is about to change.

The sequencer remains the sole writer of canonical `.devforgeai/**`. The producer exceptions do not dent that: `.devforgeai/stack.yaml` and `.devforgeai/provenance/adr/**` are written by workers **inside the candidate root**, and reach canonical only when promotion copies them (section 5.2).

### 12.4 Promotion and abandonment

`devforgeai promote <run>` is the fifth model-callable operation, and the only one whose effect is on the canonical tree. It is not automatic: the last passing transition marks the run `ready_to_promote` and writes a `REQUIRE_HUMAN` handoff whose one forward command is this. The user reads what the run did — the reports are already rendered under `docs/reports/` — and then promotes, or does not.

Promotion, in order, under `.devforgeai/lock`:

| # | Step | Refusal |
|---|---|---|
| 1 | the run exists and its status is `ready_to_promote` | `NO_CANDIDATE`, or a refusal naming the actual status |
| 2 | the canonical base still matches `candidate.base_ref` | `STALE_BASE` — rebase and retry once in worktree mode, `needs_user` in copy mode |
| 3 | worktree mode only: no canonical file among the run's changed paths has uncommitted edits | `DIRTY_TARGET`; the user resolves it, the sequencer never merges over a local edit. Copy mode has no committed baseline to call a file dirty against, so step 2's manifest comparison is its whole base check and every difference is `STALE_BASE` |
| 4 | apply: `git merge --ff-only devforgeai/<run>` in the canonical checkout, or copy the changed paths' exact bytes and delete what the candidate deleted | `MERGE_CONFLICT` |
| 5 | mark `runs.<run>.status: promoted`, write the promotion handoff, log `candidate.promote` | — |
| 6 | remove the candidate root, its branch and its tags | — |

`devforgeai candidate abandon <run>` is the other exit. `devforgeai phase fail --reason <text>` calls it when the policy says abandon; the root, its branch and its tags go, `runs.<run>.status` becomes `abandoned`, and the canonical tree is exactly as it was at `phase start`. A blocked run is **not** abandoned: it keeps `status: active` with its lease released, so its root and every checkpoint survive for inspection, and the user chooses between `devforgeai phase fail --reason` and repairing the story and re-running.

Three properties follow, and every skill specification may rely on them:

1. **A failed run costs nothing.** No canonical byte moved, so there is nothing to revert and no half-applied phase to reason about.
2. **A promoted run is one reviewable change.** In worktree mode it is a branch of per-phase commits fast-forwarded onto the target; in copy mode it is one working-tree change set the user commits with the story.
3. **The primary window never sees a file body.** Bodies live in the root; the receipt carries paths; the reports carry prose. That is what keeps a long run inside a terminal session's context.
