# Hook Dispatcher

Status: runnable draft, not installed or accepted, 2026-09-02. This is the rung 3 contract that `07-purpose-and-enforcement.md` section 7 item 2 asked for: one script, both providers, inputs `state.yaml` and `stack.yaml`, an ordered check list, a per-event blocking protocol, and an allow/deny conformance table. Working files are under `examples/hooks/`.

This document is the single normative statement of the actor boundary for both providers. No other design document restates it.

| File | Role |
|---|---|
| `examples/hooks/dispatch.py` | The decision dispatcher. On `SubagentStop`, it invokes the trusted sequencer to ingest the identity-bound result. Installed by `init` as `.devforgeai/hooks/dispatch.py`. |
| `examples/hooks/policy.py` | Pure path, phase, result, package and import-policy helpers shared by the dispatcher and sequencer. Install beside both entry points. |
| `examples/hooks/settings.claude.json` | Project `.claude/settings.json` fragment: hooks, permission rules, `disableAllHooks: false`. |
| `examples/hooks/hooks.codex.json` | Project `.codex/hooks.json`, same dispatcher with `--provider codex`. |
| `examples/hooks/config.codex.toml` | Strict project `.codex/config.toml` fragment: hooks on, workspace sandbox, no network/login shell, apps off. |
| `examples/hooks/agents/*.toml` | Project-scoped Codex worker profiles with stable names (`red_dev`, `green_dev`, and later phases). Producers write inside the candidate root; judges write nothing. |
| `examples/hooks/agents/claude/*.md` | Claude worker profiles with the same names, the same role split, and the same receipt contract. |
| `examples/hooks/fixtures/.devforgeai/state.yaml` | Canonical state: story statuses and the `runs` index. Written only by the sequencer. |
| `examples/hooks/fixtures/.devforgeai/work/<run>/run.yaml` | The per-run enforcement file the dispatcher reads on every event. Written only by the sequencer, gitignored in a real project. |
| `examples/hooks/fixtures/.devforgeai/stack.yaml` | A fixture instance of the `stack.yaml` contract in `10-sequencer-and-contracts.md`. |
| `examples/hooks/run_conformance.py` | The allow/deny, actor-bound result, and transition-backstop table. `python3 run_conformance.py` exits 0 when every row holds. |
| `examples/hooks/devforgeai.py` | The sequencer, receipt broker, candidate-root owner and stack-command broker. Only writer of canonical `.devforgeai/**`; creates, checkpoints, rewinds, promotes and abandons the candidate root; runs the per-phase `max_attempts` transition checks. |
| `examples/hooks/demo_sequencer.sh` | Walks STORY-001 through the gate (with `--lenient`, because the fixture story is stand-alone), red, a green that returns `status: fail` with `next: red`, red again, a clean green, and a refactor whose missing lint runner ends `REQUIRE_HUMAN`. It runs the story twice, once in copy mode and once in worktree mode against a `git init`ed scratch copy of the fixture, and both must end green. |

## 1. Principle

The model is never the sequencer. A deterministic command, `devforgeai`, owns everything under canonical `.devforgeai/`: the per-run enforcement file, captured receipts, sub-phase reports, the handoff envelope, checkpoints, and command evidence. It also owns the candidate root each run's producers write in. It is the only writer of the canonical tree. `policy.py` is pure. Hooks read the enforcement file on every event and deny anything the current phase does not authorise. On `SubagentStop`, the dispatcher invokes one hook-only sequencer operation; it does not implement a second state writer.

**The actor boundary, both providers.** A write is authorised by two facts a tool event cannot forge: a lease bound at an identity-bearing start event, and a path under the run's candidate root. Codex's documented `PreToolUse` schema does not identify whether a tool call came from the primary or a subagent; `agent_id` and `agent_type` are documented at `SubagentStart` and `SubagentStop`. Claude's equivalent identity on `SubagentStop` is asserted, not yet confirmed from a primary source. Both adapters therefore:

- bind the run's single write lease at `SubagentStart`, the only identity-bearing pre-write event either provider documents, and release it at `SubagentStop`;
- allow a write tool only while that lease is held, only under `candidate.root`, and only inside the phase's fence — on Claude by comparing the event's `agent_id` to the lease, on Codex by the path test alone, because its `PreToolUse` carries no identity and the root is the fence;
- deny every write in the primary window, every write outside a root, and every state-mutating `devforgeai` Bash call, on both providers;
- run judges with their write tools denied outright, so they hold no lease and several may read one checkpoint at once;
- take exactly one `devforgeai.worker-result/v1` receipt at `SubagentStop`, where the sequencer derives what actually changed from the checkpoint diff, checks it against the receipt's claim, runs the transition oracle in the root, checkpoints, and either advances or returns exit 2 so the same worker continues.

This avoids pretending that an unobservable tool-call actor can be authenticated: on the provider where identity is unavailable, the fence is a filesystem boundary rather than a claim. It keeps one write model instead of two.

Three sources feed one script:

```
story.md ──gate──> work/<run>/run.yaml   (fence, test paths, keys, phase, attempts, root, lease)
techstack.md ────> stack.yaml            (commands, package allowlist, forbidden imports, ignore_dirs)
event JSON ──────> dispatch.py ──> allow/no decision | deny/continue with reason
receipt JSON ─SubagentStop──> devforgeai ingest-result ──> diff/check/test/checkpoint/advance
```

## 2. The enforcement block

`devforgeai phase` writes this at every transition, to `.devforgeai/work/<run>/run.yaml`. Nothing in it is derived at hook time from a Markdown document; the gate did that once and recorded the result. The file is gitignored and per-run, so a transition dirties no tracked file and two runs never collide.

```yaml
run: STORY-001               # evidence home: .devforgeai/work/STORY-001/
skill: dev                   # canonical; the dev-tdd variant resolves before the write
arg: STORY-001               # the `phase start` argument
kind: story                  # story | document
phase: red                   # dev phases: red | green | refactor | smoke | review
canonical: /home/u/proj      # the checkout this run was opened from; the way back out of the root
candidate:
  mode: worktree             # worktree | copy
  root: /home/u/proj/.devforgeai/work/STORY-001/wt
  branch: devforgeai/STORY-001
  base_ref: 4f9c1e2a…        # canonical HEAD at phase start; promotion refuses if it moved
  checkpoint: base           # base, then the last phase whose transition passed
lease:                       # null when no producer holds it
  session_id: session-1
  agent: red_dev
  agent_id: agent-7f3c       # present on Claude; absent on Codex, where the root is the fence
  phase: red
  granted_at: "2026-09-02T09:01:00Z"
write_fence: [tinyapp/text.py, tests/test_text.py]     # story.write_fence, root-relative
test_paths: [tests/test_text.py]                        # every story.test_plan[].file
test_plan: [{criterion: 1, file: tests/test_text.py, name: test_slugify_basic}]
commands: {source: .devforgeai/stack.yaml#python, use: [test, lint]}   # story.commands, hash verified at gate
granted_keys: [test]         # this phase's run_keys ∩ commands.use
attempts: {red: 0, green: 0, refactor: 0, smoke: 0, review: 0}
max_attempts: {red: 2, green: 3, refactor: 2, smoke: 2, review: 2}   # one entry per phase; no `default` key
bounce_count: 0              # rewinds so far; distinct from attempts
gate_policy: {unresolved_assumption: BLOCK, stale_hash: BLOCK, test_runner_missing: REQUIRE_HUMAN}
started_at: "2026-09-02T09:00:00Z"
session_id: session-1        # the session evidence file this run was opened under
```

`examples/hooks/fixtures/.devforgeai/work/STORY-001/run.yaml` is the same file in full, and `schemas/devforgeai/v1/run.schema.json` is its normative shape. Canonical `state.yaml` holds the story statuses and the `runs` index only; `10-sequencer-and-contracts.md` section 12.3 states the split and the two-marker rule a hook uses to tell which side of it the event's cwd is on.

The file is live only while canonical `state.yaml#runs.<run>.status` is `active`. `ready_to_promote`, `promoted` and `abandoned` all mean no phase is running: every write is denied and every non-read-only command is denied, and the only operation left for that run is `devforgeai promote <run>` from the primary window.

## 3. Ordered checks

The dispatcher runs one ordered list per event, top to bottom; the first failure blocks. Every reason names the phase and the rule so the model's next move is obvious. The numbering below is `dispatch.py`'s own order, and "a run is active" means the run's enforcement file is live by the rule in section 2.

| # | Event | Condition | Result |
|---|---|---|---|
| 0 | SessionStart | always | write the session evidence file through the sequencer and print the self-test: provider, state parsed, `stack.yaml` resolvable, active run, candidate root and fence. It also probes the worktree-mode prerequisites — `git` on `PATH`, a repository with at least one commit, `.devforgeai/work/` ignored, and `.claude/settings.json` (or the `.codex/` config) and `.devforgeai/stack.yaml` tracked, so a fresh worktree contains the hooks that govern it — and reports each. A missing dispatcher path is the one fault hooks cannot report, so this line is the evidence the chain is armed. Never blocks: a failed prerequisite is refused later, at `phase start`, as `could_not_run` with `reason_code: prerequisite_missing`, and is never a silent fallback to copy mode. |
| 1 | Any policy event | `state.yaml`, the run's `run.yaml`, or the referenced `stack.yaml` is malformed, non-mapping, or escapes the root it belongs to | block with a specific fail-closed reason. Unexpected script crashes remain the separate platform limitation in section 9. |
| 2 | SubagentStart | a run is active and the event carries an `agent_type` | the starting agent must be the active phase's worker, or block. An event with an `agent_id` and no `agent_type` is one of Claude Code's internal helper subagents (observed live 2026-09-03: the auto-mode classifier starts and stops one every 10 to 30 s while a worker runs); it is ignored, never checked, never leased. On a match, and only for a producer phase, take the run's write lease: record `{session_id, agent, agent_id, phase, granted_at}` in `run.yaml#lease` and append a `granted` row to the session evidence. A lease already held blocks with `LEASE_HELD`. This is the only identity-bearing pre-write event either provider documents, which is why the binding happens here. On a match, inject the run, the phase, `candidate.root`, the fence, `granted_keys` and the exact receipt schema as additional context. A judge phase takes no lease. The `PreToolUse` Agent check, not this one, is the preventive gate against the wrong worker starting at all. |
| 3 | ConfigChange | a run is active | block. Settings cannot change mid-run. Codex has no such event; rung 4 covers it. |
| 4 | PermissionRequest | a run is active | return an explicit deny decision. The agent cannot escape the workspace/network sandbox during an active run. |
| 5 | PreToolUse, tool `mcp__*` | a run is active | block. An arbitrary MCP tool may have local or remote side effects; add a typed capability to the run contract before allowing one. Outside a run this example does not govern MCP. |
| 6 | PreToolUse, write tool (`Edit`, `Write`, `MultiEdit`, `NotebookEdit`, `apply_patch`) | see the rule | one branch, and nothing else is allowed. **Producer branch:** allow only when a run is active, the run's lease is held, on Claude the event's `agent_id` equals the lease's, the target canonicalises under `candidate.root`, and the path relative to that root is inside `write_fence` and allowed by the active phase's `writes` mode. **A judge phase has no branch:** its worker is dispatched with no write tool at all, so any write tool call under a `writes: none` phase is a fault and is denied whatever its path, including a path under `.devforgeai/work/<run>/evidence/<agent>/`. That directory is written by the sequencer at ingest, from the receipt's `findings` (`10-sequencer-and-contracts.md` section 5.2 step 8b); it is not a hole in the fence, because nothing holds a tool that could reach it. Everything else blocks: a write with no run active, a write from the primary window, a write while no lease is held, any write at all from a judge phase, and any path outside the root or outside the fence. Symlinks resolve before every comparison, and fabricating `agent_type` in tool input creates no exception on either provider. |
| 7 | PreToolUse, `Bash` | command is not a single argv of an allow-listed read, or a subagent calls it with no run active | block. Multiple commands, redirects, pipelines, substitutions, variables and `rg` helper execution are all refused, and `sed`, `find`, `sort`, `uniq` and `xargs` are not deemed safe by command head. Git is admitted read-only and only inside the candidate root: `status`, `diff`, `log`, `show`, `ls-files`, `blame` and `rev-parse`, with cwd under `candidate.root` or, because a worker's cwd is the canonical checkout, with `-C <candidate.root>` as the first and only option naming exactly that path, so a producer can see its own work and a judge can read the tree it judges; `-C` in any other position or naming any other path is denied. Every mutating Git subcommand is denied, to workers and to the primary alike — the sequencer alone commits, tags, resets, rebases and merges, and it does so as the candidate operations of `10-sequencer-and-contracts.md` section 2, never through a model's Bash call. No worker ever receives a literal build, test, lint or format command: it names a key and the sequencer resolves it. |
| 8 | PreToolUse, `Bash` starting `devforgeai` | operation is outside the model-callable grammar, is hook-only, or is a subagent call outside `status` and the lease holder's `run <key>` | block. The model-callable set is `status`, `phase start <skill> <arg> [--fix] [--lenient]`, `phase fail --reason <text>`, `validate` and `promote <run>`; `--fix` and `--lenient` are the two options `phase start` accepts, as trailing tokens in either order and each at most once, and any other option is blocked here; `phase start` only with no run active, `validate` and `phase fail` only with one. A judge phase's worker may call `status` and nothing else; a producer phase's worker holding the lease may additionally call `run <key>` for a key its phase granted, inside the candidate root. Hook-only operations (`session-start`, `lease-bind`, `ingest-result`, `phase next`) are refused here and again by the sequencer, which requires `DEVFORGEAI_HOOK_EVENT`. Checks 7 and 8 are the **only** command-level bound on a subagent's `Bash`: a subagent's `tools:` frontmatter accepts tool names and MCP server patterns, never a command pattern (`04-dual-target.md`, read 2026-09-03), so a compiled worker profile lists the bare `Bash` and these two checks decide every command it may run — `devforgeai status` plus check 7's read-only command set for a judge, and additionally `devforgeai run KEY` for a producer's granted keys. |
| 9 | PreToolUse, `Bash` starting `devforgeai-research` | the subcommand is outside the ten Research Core operations, or the caller is a subagent | block. This head is a provider-external CLI, not part of the sequencer grammar: Research Core is the sole writer inside its own fence (`docs/research/**`, `.devforgeai/research-staging/`, `.devforgeai/research-cas/**`), opens no framework run, and needs none open, so the ten operations — `normalize-request`, `open-run`, `append-record`, `put-source`, `transition-run`, `validate-run`, `seal-run`, `render`, `render-handoff`, `resume-run` — are admitted to the primary window whether or not a run is active. A phase worker is still limited to `devforgeai status`, because Research Core writes files and a phase worker never does. Check 7's single-argv rule already refused any redirect, pipeline or substitution around it. Admitting the call is not the same as it being safe mid-run: the gate snapshot excludes only `.devforgeai/`, so a `seal-run` or `render` that writes under `docs/research/` during an active framework run reads as fence drift at the next transition. `10-sequencer-and-contracts.md` section 2 states the consequence; run Research Core between runs. |
| 10 | PreToolUse, `Agent` | no run is active, the caller is a subagent, the requested profile is not the current phase's worker, or the phase is a producer whose lease is already held | block before spawn. Both adapters reject a nested spawn; Codex additionally limits open workers to one, because its Agent tool event likewise does not identify the caller. |
| 11 | PostToolUse, write tool | a run is active and the write landed outside `candidate.root` or outside the fence | exit 2 with feedback. A write that escaped the pre-hook cannot be undone here, and it is never accepted as evidence: the transition derives its change set from the checkpoint diff, so an out-of-fence write inside the root surfaces there, and a write outside the root never reaches a promotion because promotion moves only the run's changed paths. |
| 12 | SubagentStop | a run is active and the event carries an `agent_type` | an event without `agent_type` is an internal helper stopping, not the worker: ignored, exit 0 (treating it as the worker's stop blocked the first live run and released the lease mid-phase). Otherwise hand `agent_type`, `agent_id`, `session_id` and the worker's final message to the hook-only `devforgeai ingest-result`, which derives the change set from the checkpoint diff, checks it against the receipt, runs the oracle, checkpoints, releases the lease and appends a `released` row to the session evidence. A non-zero broker exit becomes exit 2 with its output and the lease is **kept**, so the same worker continues in the same root; a zero exit becomes a system message. |
| 13 | Stop | a run is active, the recursion guard is false, attempts are below the phase limit, and no handoff envelope exists | block, and direct the primary to dispatch the current phase's worker. |

On Codex the `agent_id` comparison in the producer branch is skipped, because its `PreToolUse` carries no identity at all: the root and fence tests carry the whole decision, and they are filesystem facts a tool input cannot fabricate. One consequence must be said plainly rather than left to section 9: on Codex a primary-window `Edit` whose path happens to fall under `candidate.root` while a lease is held is admitted, because nothing in the event distinguishes it from the worker's. The control that makes that case not arise is the one-open-worker cap plus the primary being idle while its worker runs, and the containment if it does arise is that the edit is inside the root, so it appears in the next checkpoint diff as an unclaimed change rather than in the canonical tree. On Claude the `agent_id` comparison refuses it outright.

The result the broker receives is checked by the sequencer, not here. Its full order is `10-sequencer-and-contracts.md` section 5.2; four rows matter to a hook reader:

| Receipt check | Effect |
|---|---|
| a derived changed path resolves outside `candidate.root`, matches `ALWAYS_DENY`, or is outside `write_fence` | refuse the receipt. Symlinks resolve before comparison. `.devforgeai/**`, provider config, `CLAUDE.md` and `AGENTS.md` are protected; the two carve-outs are `.devforgeai/stack.yaml`, writable only from `architect`'s `techstack` phase or `onboard`'s `code_map` phase and only after it validates against `stack.schema.json`, and `.devforgeai/provenance/adr/**`, writable only from `amend`'s or `architect`'s `adr` phase and only after it satisfies the `adr` template header. Both are written inside the root and reach canonical only at promotion. |
| the derived change set is not a subset of the receipt's `claimed_paths` | refuse with `UNCLAIMED_CHANGE`, and count a phase attempt: real bytes were written outside the claim. |
| a tests-writing phase changed anything but `test_paths`; a code-writing phase changed a test; a judge phase changed anything | refuse. A phase that wants earlier work redone returns `status: fail` with `next: <rewind_to>` and an empty `claimed_paths`. |
| a changed file carries a forbidden package or import, or a recognised dependency outside `packages.allow` | refuse. Dapper is accepted and Entity Framework rejected in the C# fixture. |
| the whole candidate root, rescanned, violates the package or import policy | refuse; the root stays at the failed phase's state and is retried or rewound. |

## 4. Blocking protocol

Exit 2 with the reason on stderr is the common blocking protocol for PreToolUse, SubagentStop and Stop. Codex `PermissionRequest` instead returns its documented JSON `decision.behavior: "deny"` shape at exit 0. Successful Codex Stop calls emit `{}`; SubagentStart returns `additionalContext`; successful SubagentStop returns a JSON `systemMessage` summarizing the broker and transition. Known input/policy errors become exit 2. Exit 1 is reserved for an unexpected dispatcher fault and is not a hard boundary, which is why SessionStart, the transition oracle, and rung 4 remain necessary.

Provider differences the dispatcher absorbs with `--provider`:

| | Claude Code | Codex |
|---|---|---|
| PostToolUse exit 2 | shows stderr to the model, does not block | blocks with feedback |
| ConfigChange | exists, can block | no event |
| Hook trust | project settings apply after workspace trust | each definition trusted by hash via `/hooks` |
| Disable | `disableAllHooks`; project `false` beats user `true` | `hooks = false` in `config.toml` |
| Hosted tools | n/a | exempt from hooks |
| Tool-call actor | `agent_id`/`agent_type` on Pre/PostToolUse is asserted but unconfirmed; used only as a second test after the lease and path tests pass | documented Pre/PostToolUse fields do not include `agent_id`/`agent_type`; not consulted at all |
| Lease binding | `SubagentStart` `agent_id` is recorded and compared on every write | `SubagentStart` identity is recorded; writes are authorised by path under `candidate.root` alone |
| Worker boundary | producer writes in the candidate root under the lease, judge writes nothing and carries no write tool; exact receipt captured at SubagentStop | same roles, as a project custom agent; the receipt is captured where SubagentStop documents `agent_id`, `agent_type`, and `last_assistant_message` |
| Subagent write of a report file | **observed 2026-09-03 on Claude Code 2.1.259:** a subagent's `Write` of report-like Markdown, `findings.md` among them, is refused by the provider itself with `Subagents should return findings as text, not write report files. Include this content in your final response instead.` The refusal happens before any DevForgeAI hook runs, so no hook sees the call and no hook can permit it. `.json` and `.txt` in the same directory are not refused. The heuristic is undocumented; it is recorded here as a fact and is **not relied on in either direction** — the design gives a judge no write tool, which is what actually holds | not observed; no equivalent claim is made |
| Phase transition | trusted SubagentStop broker diffs, checks, checkpoints and transitions; Bash cannot mutate state while a run is active | same |
| Edit tool input | allowed under the lease, inside `candidate.root`, inside the fence; denied everywhere else, and always in the primary window | same, minus the identity comparison |
| Permission escalation | provider permission rules | `PermissionRequest` is denied while a run is active. |

An entry that a Max-plan terminal cannot influence is out of scope here: the administrator-managed hook policy is `12-post-mvp.md#pm-03`.

## 5. Provider configuration and installation

`examples/hooks/settings.claude.json` adds three things to the project `.claude/settings.json`:

1. **Static rules.** Allow exactly the five model-callable forms, never a wildcard: `Bash(devforgeai status)`, `Bash(devforgeai phase start *)`, `Bash(devforgeai phase fail --reason *)`, `Bash(devforgeai validate)`, `Bash(devforgeai promote *)`. `Bash(devforgeai run *)` is allowed as surface as well, so the permission layer can name the operation the lease-holding producer calls; the sequencer, not the allowlist, decides whether a given caller holds the lease. Hook-only operations are absent from the allowlist by construction, not merely denied by check 8. The provider-external Research Core runner is allowed the same way, one rule per operation and never a wildcard over the head: `Bash(devforgeai-research normalize-request *)` and its nine siblings, so that an eleventh subcommand is absent from the allowlist as well as denied by check 9. Deny rules for what no phase ever writes in the canonical checkout: framework directories, architecture and plan docs, `CLAUDE.md`, plus `curl`, `wget`, and every git subcommand that moves a tree — the read-only six of check 7 are the only ones admitted, and only inside a candidate root. Deny rules from any scope beat allow rules from any scope, and they apply in every permission mode.
2. **`Agent(...)` deny rules** for the built-in general-purpose, Explore and Plan agents, so dev cannot route around the phase worker set. Per-phase agent gating is check 10, because SubagentStart cannot block.
3. **Hooks** on SessionStart, PreToolUse, PostToolUse, SubagentStop, Stop and ConfigChange, all pointing at the one dispatcher in exec form (`command` plus `args`), 10-second timeout, `disableAllHooks: false` and `disableBypassPermissionsMode: "disable"`.

For Codex, install the example files as follows (merge existing files; do not overwrite unrelated settings):

```text
<repo>/.codex/config.toml             <- config.codex.toml
<repo>/.codex/hooks.json              <- hooks.codex.json
<repo>/.codex/agents/*.toml           <- agents/*.toml
<repo>/.devforgeai/hooks/dispatch.py  <- dispatch.py
<repo>/.devforgeai/hooks/policy.py    <- policy.py
<repo>/.devforgeai/hooks/devforgeai.py <- devforgeai.py
```

`hooks.codex.json` uses the official project-root form, `$(git rev-parse --show-toplevel)`, to locate the dispatcher. The dispatcher and sequencer also walk upward from the event `cwd` to find `.devforgeai/state.yaml`. The config enables hooks and multi-agent support, limits the session to one open worker, keeps the primary in `workspace-write`, disables network and login shells, excludes temporary directories as extra writable roots, and disables external apps by default. One open worker is a control, not a performance choice: it prevents an unidentifiable nested Agent call while a phase worker is active.

Codex has no permission vocabulary in `hooks.json`: its admitted shell surface is prose in `config.codex.toml` and enforcement is the `PreToolUse` hook itself, so `hooks.codex.json` names the surface in a comment rather than pretending to a rule the runtime would read. Claude's allowlist is therefore defence in depth on one provider and documentation on the other; check 7 and check 9 are what actually decide, on both.

Codex discovers project custom agents from `.codex/agents/`, and the profile's `name` is the identity exposed at SubagentStart/Stop. Judge profiles set `sandbox_mode = "read-only"`; producer profiles set `workspace-write` and receive `candidate.root` at SubagentStart. Both set `approval_policy = "never"` and the exact receipt instructions. Parent runtime overrides can supersede an agent's sandbox default, so the profile is defence in depth rather than the boundary: the `PreToolUse` hook still denies every Codex write that is not under the run's candidate root and inside its fence, regardless of claimed identity.

After installation, trust the project and review/trust the exact hook definitions with `/hooks`. A changed definition gets a new hash and must be reviewed again. Project hooks are suitable for repository policy but are user-disableable; that hole is covered by rung 4 (`12-post-mvp.md#pm-10`), and the administrator-managed alternative is `12-post-mvp.md#pm-03`.

## 6. Worker-result contract

One schema, both providers. The worker returns exactly one JSON object, with no Markdown fence or surrounding prose. It is a receipt: it says what the worker did in the candidate root, and carries no file body, no diff and no hash. The normative schema is `schemas/devforgeai/v1/worker-result.schema.json`:

```json
{
  "schema": "devforgeai.worker-result/v1",
  "run": "STORY-001",
  "skill": "dev",
  "phase": "green",
  "agent": "green_dev",
  "status": "pass",
  "candidate": {"id": "STORY-001", "input_checkpoint": "red"},
  "claimed_paths": ["tinyapp/text.py"],
  "evidence_refs": [".devforgeai/work/STORY-001/green-oracle.json"],
  "note": "minimal implementation",
  "issues": []
}
```

`status` is the closed set `pass | fail | needs_user | could_not_run`; a `could_not_run` result carries `reason_code` in `runner_missing | timeout | network | hook_fault | provider_tool_refused | prerequisite_missing | checkpoint_fault | provider_tool_refused` and claims nothing. `issues` holds at most 10 one-line rows. `claimed_paths` holds at most 64 root-relative paths and is empty on any status other than `pass`, and always empty from a judge; `evidence_refs` holds at most 16. `findings` is required on a judge receipt and forbidden on a producer's: it is the judge's detailed evidence, at most 16384 UTF-8 bytes, never truncated, and the sequencer persists it verbatim to `.devforgeai/work/<run>/evidence/<agent>/findings.md` at ingest. `next` is the optional rewind request: it requires `status: fail`, it is accepted only from a phase whose registry entry declares a `rewind_to` target, and it must name exactly that target. There is no `test_defect` status and no `test_defect` issue kind.

The broker rejects unknown keys, duplicates, a receipt over 64 KiB, and an `input_checkpoint` that is not the one the phase was dispatched against. It then stops reading the receipt and reads the tree: it diffs the candidate root against that checkpoint, derives `changed[{path, blob_sha256, kind}]`, refuses when that set is not a subset of `claimed_paths` (`UNCLAIMED_CHANGE`), canonicalizes symlinks and paths, applies the same phase/fence/stack rules the pre-write checks use, runs the transition oracle inside the root, takes the phase checkpoint, releases the lease, and persists the event `agent_id`, `session_id`, result digest, derived change set and checkpoint ref. Binary files are no longer a limitation: nothing about a file's bytes crosses this boundary.

The model-provided `agent` field is not identity, and `claimed_paths` is not evidence. The trusted binding is the SubagentStop event's `agent_type`, checked against the phase's worker and against the `agent_id` the lease was granted to; the trusted account of the work is the checkpoint diff. A green model cannot label itself red, cannot under-claim its way past the fence, and a primary/tool event cannot submit this operation through Bash.

## 7. Conformance

```
$ python3 docs/design/examples/hooks/run_conformance.py
240/240 rows hold (147 dispatcher, 35 grammar, 58 backstops)
```

The table covers: the documented identity-free tool event; fabricated identity rejection; actor-bound SubagentStart/Stop; valid red and green receipts; wrong agent, outside-fence and forbidden-ORM rejection; canonical aliases; primary-window and nested-agent controls; red-only tests and green-only code; every path in a multi-path change set; delete/move/traversal/framework targets; malformed state, run-file, stack and receipt input; pre-write and post-write package/import checks; explicit Dapper-allowed and Entity-Framework-denied cases; raw stack-command denial; phase keys; brokered-subprocess mutation detection outside `ignore_dirs`; the closed sequencer grammar and the hook-only marker; redirects, pipelines, variables, helper execution and Git mutation; the six read-only Git subcommands admitted inside a candidate root and denied outside it; MCP denial; escalation denial; handoff and recursion-stop behavior; ConfigChange; the `--fix` and `--lenient` flags as the two accepted `phase start` options, with any other option refused; each of the ten `devforgeai-research` operations admitted with and without a run active, an eleventh subcommand refused, a redirect around one refused, and the runner refused to a phase worker; the `devforgeai status` block rendering the active run's handoff envelope, rendering the most recent one when no run is active, and printing the run block alone when there is none; and behaviour with no run active.

The sequencer agent adds rows for the write model this document now describes, and they are the rows a reader should look for first: `devforgeai promote <run>` admitted as the fifth model-callable form and refused to a worker; the lease-bound write check on **both** providers — a write allowed under the lease inside `candidate.root`, the same write denied with no lease, denied from the primary window, denied from a judge phase, denied outside the root, and on Claude denied when the event's `agent_id` does not match the lease while Codex decides on the path alone; `LEASE_HELD` on a second producer dispatch; `UNCLAIMED_CHANGE` on a receipt whose derived change set exceeds its claim; `FENCE_OVERLAP` on a second `phase start` whose fence intersects an active run's, including through a producer-exception path; `STALE_BASE` on a promotion whose canonical base moved, with the worktree rebase-and-retry path and the copy-mode `needs_user` path; and `DIRTY_TARGET` on a promotion into a tree with uncommitted edits to one of the run's changed paths.

Twenty-four executable backstops follow the event table. They cover: the transition oracle rejecting ORM drift with every hook bypassed; a stack subprocess that mutates a path outside `ignore_dirs`; the full `SubagentStop` route on each provider, including rewind to a checkpoint and the oracle; an identity-free stop recorded as `hook_fault`; session evidence, including an uninstalled repository and the appended lease rows; a document run gating on its output fence; `compiled: true` with no build command refused at the gate; Dapper accepted and Entity Framework refused through the broker; `qa` and `review` opening a story-anchored run that brokers `test` and still cannot write code; `.devforgeai/stack.yaml` accepted from its two producer phases, refused from any other phase or skill, and refused when it fails `stack.schema.json`; the registry ADR accepted from `amend`'s and from `architect`'s `adr` phase, header-checked, and refused from every other phase, skill and sibling path; the gate re-resolving every `provenance` and `context` hash, with a stale hash refused, a placeholder refused, and `--lenient` refused on a planned story; a heading inside a fenced code block neither opening nor ending a section, against digests computed by explicit line slicing; the sequencer resolving `sha256:PENDING` so a story `plan` wrote opens a dev run with no flag, and refusing the phase when a source or an anchor does not resolve; a conditional document phase passing with no file and a note, and refused without one; and every enforcement file the sequencer writes validating against `run.schema.json`. All scratch trees are outside this checkout.

## 8. The sequencer

`examples/hooks/devforgeai.py` is the deterministic state, receipt, candidate and command broker. The grammar is closed and split in two. Model-callable operations may appear in a Bash allowlist; hook-only operations require the `DEVFORGEAI_HOOK_EVENT` environment marker and are denied to the model in every phase. `run <key>` sits between the two: the lease-holding producer calls it, and no one else. `report` does not exist: a worker's report is written by the sequencer from the ingested result.

Model-callable:

| Command | Precondition it enforces | Effect |
|---|---|---|
| `status` | | prints the run block — run, `candidate.root`, phase, fence, `granted_keys` — and `next`, then renders the run's handoff envelope with the same function `phase next` uses (`10-sequencer-and-contracts.md` section 6 rule 7). This is the block the primary pastes into a dispatch prompt. Writes nothing, and prints the run block alone when no envelope exists |
| `phase start <skill> <arg> [--fix] [--lenient]` | no run active, except the resume and `clarify` carve-outs in `10-sequencer-and-contracts.md` section 2; for a story gate (`dev`, and the story-anchored `qa` and `review`): story `template_version: 3` and `status: ready`, no `ASSUMPTION:` outside Clarifications, every `blocked_by` story `done`, every `test_plan.file` inside `write_fence`, no fence entry sequencer-owned, `commands.source` present with a current hash, and every `provenance[]` and `context[]` entry re-resolved by the `01-skill-anatomy.md` hash rule; for a document gate: a fence that is repository-relative and not sequencer-owned. `--lenient` downgrades `unresolvable-source` only, only where a story gate runs, and only for a story outside `docs/plan/`; `--fix` is legal for a story skill only and records the qa or review report as `run.yaml#fix_report` | runs the deterministic gate; refuses `FENCE_OVERLAP` against every active or `ready_to_promote` run; creates the candidate root and its `base` checkpoint through `candidate open`; opens the run under `.devforgeai/work/<run>/`; writes `run.yaml`, including `gate_warnings` for anything downgraded; registers the run in canonical `state.yaml#runs` and sets the first phase |
| `phase fail --reason <text>` | phase active | records a BLOCK handoff and, when the policy says abandon, calls `candidate abandon` so the root, its branch and its tags go and the canonical tree is exactly as it was at `phase start` |
| `validate` | a run is active | read-only fence and full tech-stack invariant scan over the candidate root against its last checkpoint. This is not the rung-4 clean-checkout validator (`12-post-mvp.md#pm-10`). |
| `promote <run>` | the run is `ready_to_promote`; canonical base unmoved (`STALE_BASE`); no dirty canonical file among its changed paths (`DIRTY_TARGET`) | takes `.devforgeai/lock`, calls `candidate promote` — fast-forward merge, or exact-byte copy — marks the run `promoted`, writes the promotion handoff, and removes the root. Used only after a completed run's `REQUIRE_HUMAN` handoff named it and the user asked |

Hook-only:

| Command | Precondition it enforces | Effect |
|---|---|---|
| `session-start` | hook-only marker; SessionStart event | creates `.devforgeai/sessions/<session_id>.json`: provider, provider version, dispatcher digest, hooks armed, state parsed, stack resolvable, worktree prerequisites. Later lease grants and releases append to it |
| `ingest-result --agent ...` | hook-only marker; active phase; identity-bearing SubagentStop; exact v1 receipt | derives the change set from the diff against the receipt's `input_checkpoint`, refuses `UNCLAIMED_CHANGE`, resolves every `sha256:PENDING` digest in a changed artifact in place (a worker has no hashing tool), writes `<phase>-report.md` and `<phase>-result.json`, runs `phase next`, releases the lease, and exits 1 if the phase remains active after a `pass`. The dispatcher turns any non-zero exit into the providers' exit 2, and the lease is kept so the same worker continues |
| `phase next` | an accepted result exists for the current phase | runs the transition check inside the root, takes the phase checkpoint through `candidate checkpoint`, advances or repeats the phase, records the run, renders `handoff.json` and the `docs/reports/` view |
| `run <key>` | the caller holds the run's lease, or the sequencer is inside a transition; the active phase grants the key and `commands.use` authorises it | resolves the literal command from the hash-pinned stack section, runs it without a shell with cwd = `candidate.root`, detects mutations outside `stack.yaml#ignore_dirs`, records the outcome. The lease-holding producer calls it to see its own tests; the sequencer calls it again at the transition. No worker ever receives the literal command, and the primary window holds no lease and is refused. |
| `candidate open\|checkpoint\|promote\|abandon` | hook-only marker; called by the sequencer itself, never by a provider event | the mechanical operations of the candidate root, one implementation for both modes: create it, checkpoint a phase, fast-forward or copy it into the canonical tree under the lock, remove it |

Transition checks are run by the sequencer itself, inside the candidate root, with the stack's own test command and the JUnit file it writes. Every transition first diffs the root against the phase's input checkpoint and runs the full package/import policy over the whole root. A report's claim and a prior hook result never substitute for current bytes:

Attempt limits come from `run.yaml`'s per-phase `max_attempts` map, never from a hard-coded number.

| From | Check | On failure |
|---|---|---|
| red | the derived change set is inside the fence and the full tech-stack policy holds; test command exits non-zero; every `test_plan` name is present and `failed`, not `error`; no test outside `test_plan`; records `red_hashes` | attempt +1, red again with the rows |
| green | fence and full tech-stack policy hold over the root; every `test_paths` hash equals `red_hashes`; every `test_plan` test `passed` | attempt +1, green again |
| refactor | as green, plus `lint` exits zero | attempt +1, refactor again |
| smoke, review | fence and full tech-stack policy hold; the judge changed nothing; result status `pass` | attempt +1 |
| document phases | fence and full tech-stack policy hold; a `writes: docs` phase changed at least one file in the root. A phase marked conditional in the registry — `plan`'s `skill_specs` is the one — may change none, but only with a `note` saying why none was owed | attempt +1 |
| any, result `fail` with `next: <rewind_to>` | the phase declares that rewind target | the root reset to the checkpoint that phase started from — its predecessor's, or `base` when it is the first — so the target's own output is discarded and it is re-entered; `bounce_count` +1, phase set to the target, that target's attempt +1, phase reports cleared |
| any, runner missing | test or lint executable absent, or the runner reports the module is missing | result recorded as `could_not_run` with `reason_code: runner_missing`; handoff by `gate_policy.test_runner_missing`; next step is the install, then `/dev` |
| any, attempts at that phase's `max_attempts` | | `dev_blocked`, `REQUIRE_HUMAN`, handoff written, lease released; the run stays `active` and its root survives for inspection until `phase fail --reason` abandons it |

The shell demo drives the sequencer directly and shows each transition path, once in copy mode and once in worktree mode against a `git init`ed scratch copy of the fixture, so the two materialisations are proved equivalent rather than asserted to be. The conformance backstop exercises the SubagentStop route, including acceptance of a Dapper change and rejection of the equivalent Entity Framework change. In the demo, the gate is opened with `--lenient` because the fixture story is stand-alone; a green worker that finds criterion 2 underspecified returns `status: fail` with `next: red`, which resets the root to `base` — red is the first phase, so the checkpoint it started from is the base — and costs an attempt at red; a receipt whose declared phase does not match the stop event's identity is refused; and a missing lint runner ends in `could_not_run` plus a `REQUIRE_HUMAN` handoff.

Not in the example: a clean detached worktree for the judge phases to verify in, and an automated integration run when two fences overlap. Both are post-MVP (`12-post-mvp.md#pm-11`, `#pm-12`). The promotion lock is `.devforgeai/lock` and is what serialises two sessions. The gate is inlined in `phase start` by design, not by omission.

## 9. What this does not close

- **A hook is not an OS write fence.** OpenAI documents tool hooks as a guardrail, not a complete enforcement boundary; hosted tools and specialized paths may bypass the default hook path. A literal “cannot write elsewhere” guarantee needs an OS boundary, which is `12-post-mvp.md#pm-04`. The story hook remains useful for precise reasons and fast feedback.
- **Subprocess writes.** No worker receives the literal test/build command. The sequencer launches its argv without a shell, with cwd = `candidate.root`, and detects byte changes outside `stack.yaml#ignore_dirs`. A hostile test that writes inside the root is caught at the next diff as `UNCLAIMED_CHANGE`; one that escapes the root is not prevented, only kept out of promotion, because promotion moves the run's changed paths and nothing else. Literal prevention requires the OS boundary above.
- **Hooks fail open on infrastructure faults.** Malformed state/stack/result inputs fail closed, but a timeout, process crash, missing hook script, untrusted project layer, or disabled project hook is not a deny. SessionStart makes some failures visible and records them in the session evidence file. A separate, provider-independent promotion validator is still required; it is `12-post-mvp.md#pm-10`.
- **Static Codex config cannot express a live story fence.** `sandbox_workspace_write.writable_roots` adds roots; it does not replace the workspace with per-story file paths. Dynamic enforcement therefore belongs in the dispatcher. Stronger isolation is `12-post-mvp.md#pm-04`.
- **Actor identity is only available at the start event.** The lease is bound at `SubagentStart`, the only identity-bearing pre-write event either provider documents. On Claude a write is then checked against that identity as well as against the root; on Codex `PreToolUse` carries no identity at all, so the root is the whole fence and a second unidentified writer inside the same session would be indistinguishable. The one-open-worker cap is what makes that case not arise, and it is a configuration a live parent override can supersede. The receipt broker is semantically enforceable only while SubagentStop hooks run.
- **`stack.yaml` extraction is only as good as its extractors.** The dispatcher reads `commands`, `manifests`, `packages.allow`, `packages.deny`, package `extractors`, and `forbidden_imports` from the section a story anchors to, against the contract in `10-sequencer-and-contracts.md`. The extractor must recognize every supported manifest syntax; a regex that does not recognize a dependency is not enforcement. Multi-package resolution is `12-post-mvp.md#pm-09`.
- **Tech-stack policy is more than QA.** Result ingestion rejects obvious drift; PostToolUse diagnoses escaped writes; every transition rescans actual files. QA still owns performance evidence such as Dapper query budgets, but it is not the first place an unauthorized ORM is discovered.
- **The sequencer is still illustrative.** `.devforgeai/lock` serialises promotion, but there is no signed state, no crash-recovery journal, and no durable transaction across checkpoint and transition: a crash between the two leaves a root whose last checkpoint is one phase behind, which is recoverable by rerunning the phase but is not a guarantee the code makes. Production needs those controls.
- **The receipt bounds the claim, not the work.** It caps `claimed_paths` at 64 and `evidence_refs` at 16. Those are review bounds: a phase that legitimately changes more than 64 paths cannot report them, and the fix is a narrower fence, not a larger cap. File size and file type are no longer bounded at all, because no byte of a changed file crosses this boundary. The one worker output that does cross it is a judge's `findings`, capped at 16384 UTF-8 bytes and refused rather than truncated when it is larger. A judge with more to say than that cap allows has no way to say it today; the structured evidence broker that would fix it is `12-post-mvp.md#pm-14`.
- **Rung 4 is not implemented here.** This `validate` command checks an active enforcement snapshot. The clean-checkout, durable-chain pre-commit/CI validator and the GitHub required check are `12-post-mvp.md#pm-10`.
- **Rewind durability differs by mode.** Worktree mode pins each checkpoint as a commit and a tag, so a rewind is exact for modes, deletions and renames. Copy mode's manifest and copy-aside are enough for the fixture trees it exists for, and are the weaker of the two: it is the fallback for a project with no repository, not the recommended deployment. A project that can be a git repository should be one.
