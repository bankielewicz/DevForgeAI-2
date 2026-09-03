# hookd: a hook cookbook for Claude Code

One dispatcher, registered once per event. Checks are Python classes in `checks/`, listed in an explicit registry. Adding a rule means adding a file and one registry line, never another `settings.json` entry.

Status: proof of concept, tested by `tests/run_tests.py` (16 subprocess cases) and not yet fired from a live session. Facts below are from the Claude Code hooks and permissions references as read on 2026-09-03; provider behaviour changes, so re-check the reference before relying on a fact in production.

## 1. Why one entry per event

- Hook entries merge across user, project and local settings and every matching hook runs, in no guaranteed order. Two `PreToolUse` entries cannot express "check A before check B". One dispatcher with an ordered registry can.
- The matcher in `settings.json` is a coarse filter over `tool_name`. Everything finer, such as path, agent and command shape, belongs in code where it can be tested.
- A single script means a single failure policy, a single log and a single alarm.

Layout after `install.sh`:

```text
.claude/
  settings.json          # hooks block: one hookd entry per event
  hooks/
    hookd.py             # dispatcher
    policy.json          # data the checks read
    checks/
      __init__.py        # REGISTRY, explicit
      base.py            # Event, Decision, Check
      protect_paths.py   # ... one class per file
    hookd.log.jsonl      # gitignored
    receipts/            # gitignored
```

## 2. The protocol hookd speaks, per event

| Event | Input fields used | Pass-through | Block | Other output |
|---|---|---|---|---|
| `PreToolUse` | `tool_name`, `tool_input.file_path|command`, `agent_id`, `agent_type`, `cwd` | exit 0, no output | exit 2, reason on stderr | JSON `permissionDecision: "ask"` |
| `PostToolUse` | same, plus `tool_response` | exit 0, no output | exit 2 (tool already ran; only tells the model) | `additionalContext` |
| `SessionStart` | `source` | exit 0 | none | `additionalContext` |
| `SubagentStop` | `agent_id`, `agent_type`, `last_assistant_message` | exit 0 | exit 2 keeps the subagent working; stderr is its instruction | `additionalContext` |
| `Stop` | `last_assistant_message`, `stop_hook_active` | exit 0 | exit 2 keeps the main agent working | `additionalContext` |

Rule one: hookd never emits `permissionDecision: "allow"`. Allow bypasses the user's permission prompt, so a hook that says allow widens authority. Passing through is silence, and the normal permission flow still applies.

Rule two: block with exit 2 and a stderr reason. It is documented for every block-capable event and JSON cannot override it. JSON is used only for `ask` and for context.

## 3. Failure policy

| Situation | hookd does | Why |
|---|---|---|
| A `critical = True` check raises on a block-capable event | deny, exit 2 | A gate that errors must not become an open door |
| A non-critical check raises | log, skip, continue | Advisory checks fail visibly, not silently |
| stdin is not a hook event | exit 2 | We cannot tell whether the event could block |
| A check hangs | `SIGALRM` at 6 s converts it to a deny | A timed-out `PreToolUse` hook fails open on the host side; the host `timeout` is 10 s, so hookd must always answer first |

Test 13, 14 and 15 in `tests/run_tests.py` prove each row.

## 4. Recipe: add a check

1. Copy `checks/_template.py` to `checks/<name>.py`; rename the class.
2. Set `events`, `tool_matcher`, `order`, `critical`.
3. Implement `run(ev) -> Decision`. Use `ev.rel_path()` for any path; it resolves symlinks and returns `None` outside the project.
4. Add the class to `REGISTRY` in `checks/__init__.py`.
5. Add a fixture case to `tests/run_tests.py` for the pass path and the deny path.
6. `python3 components/hook-runtime/reference/claude-python/tests/run_tests.py`, then `./install.sh` in the target project. Settings edits are picked up live by the file watcher; `/hooks` shows the entries.

Policy values live in `policy.json`, read once per event. A check that needs new data adds a key there, never an environment variable.

## 5. The five shipped checks

| Check | Event | Shows |
|---|---|---|
| `session_selftest` | SessionStart | A visible sign the chain is alive; a missing policy hook must be a health failure, not a silent loss of enforcement |
| `protect_paths` | PreToolUse | Path fence over Edit/Write/NotebookEdit and Bash redirect targets; realpath, fnmatch, outside-project deny |
| `bash_guard` | PreToolUse | Regex deny list and an `ask` list |
| `audit_log` | PostToolUse | The non-blocking shape; the log line is the product |
| `subagent_receipt` | SubagentStop | Exit-2 bounce until a named agent returns one JSON receipt; the body is stored, never logged |

## 6. Best practices, each tied to a documented fact

1. Hooks call gates; they are not the gate. Keep the authoritative decision in a deterministic tool the hook invokes, and repeat the same check where hooks cannot see (CI, a promotion step). Research claim CLM-006.
2. Hook errors are not fail-closed on the host. A non-2 exit, invalid JSON, a timeout or a missing script lets the call through. Wrap every critical check so its failure is an explicit exit 2. CLM-028, decision D-016.
3. Use the exec form (`command` plus `args`) and `${CLAUDE_PROJECT_DIR}`. No shell quoting, no dependency on the session's cwd.
4. Keep PreToolUse checks fast and side-effect free. They run on every matching call; anything slow belongs in PostToolUse or SubagentStop.
5. Never print `allow`. See rule one.
6. Bound and sanitise output. stderr on exit 2 reaches the transcript; never include secrets, file bodies or `last_assistant_message` text. hookd's log stores decisions and paths only.
7. Path checks: realpath first, then anchor. Claude's own deny rules check both the symlink and its target; match that. A bare relative pattern in a permission rule anchors at the session cwd, so write settings rules as `/path` (settings-anchored) and hook rules as repo-relative globs.
8. Know the blind spots. Neither Claude's Edit deny rules nor a PreToolUse hook sees a write made by an arbitrary subprocess inside Bash. The candidate root and the promotion diff exist for that reason.
9. Test both paths in a subprocess, not by importing. The exit code and stdout are the contract.
10. Version-pin and self-test. The SessionStart check is the cheapest possible probe that hooks fire in this session; extend it to compare the Claude Code version against the one the checks were verified on.
11. Commit `.claude/settings.json` and the checks; gitignore the log and receipts. `disableAllHooks: true` at any level switches everything off, and a `false` in project settings beats a `true` in user settings.
12. Only `Edit(path)` and `Read(path)` permission rules are consulted by the host; `Write(path)` rules are accepted and ignored. Express file fences as Edit rules, or in the hook.

## 7. Install and live smoke test

```bash
cd <project>
components/hook-runtime/reference/claude-python/install.sh          # copies to .claude/hooks, merges settings, gitignores runtime files
```

Then, in Claude Code inside that project:

1. `/hooks` lists SessionStart, PreToolUse, PostToolUse and SubagentStop entries pointing at `hookd.py`.
2. Start a new session; the first turn shows the hookd context line.
3. Ask Claude to add a line to `CLAUDE.md`. Expect the deny reason `CLAUDE.md is protected (rule CLAUDE.md)` and no edit.
4. Ask Claude to run `git push origin main`. Expect a permission prompt whose reason names `bash_guard`.
5. `claude --debug` prints hook stderr if a step above does not behave.
6. `tail .claude/hooks/hookd.log.jsonl` shows one line per decision with tool, path, agent and duration.

For the first install in a real project, ship `session_selftest` and `audit_log` first, confirm the log fills, then add `protect_paths` and `bash_guard` to the registry.

## 8. Where this sits in DevForgeAI

This is rung 3 of the enforcement ladder. The sequencer stays the authority: hookd's `subagent_receipt` is the shape of the SubagentStop ingest, `protect_paths` is the shape of the candidate-root fence, and the promotion diff catches what a hook cannot see.
