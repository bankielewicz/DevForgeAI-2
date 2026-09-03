# hookd: a hook cookbook for Codex

This directory is a Codex-only Python reference proof of concept. It demonstrates one command dispatcher per lifecycle event, an explicit ordered registry of check classes, a versioned data policy, and event-specific Codex responses. It is not the DevForgeAI enforcement authority and it is not a provider-neutral runtime.

The Codex protocol statements in this cookbook were checked against the [official Codex Hooks documentation](https://learn.chatgpt.com/docs/hooks) on 2026-09-03. Local subprocess tests exercise synthetic hook input; they do not prove that an installed Codex client fired an event. Claude results do not establish Codex behavior.

Use these evidence labels literally:

| Label | Meaning |
|---|---|
| `DOCUMENTED` | The behavior appears in the current official Codex hook documentation. |
| `SIMULATED` | `tests/run_tests.py` invoked the installed entry point with fixture JSON and checked its process contract. |
| `OBSERVED_LIVE` | A named Codex version fired the hook in a fresh trusted session and the result was recorded. |
| `NOT_OBSERVED_LIVE` | No live Codex session has supplied that evidence. Documentation and fixtures do not upgrade this label. |
| `UNSUPPORTED` | The current Codex contract does not provide the required event field or decision. |

Unless a checked-in evidence record says otherwise, every Codex runtime statement in this component is `DOCUMENTED` or `SIMULATED`, and live behavior is `NOT_OBSERVED_LIVE`. The checked-in [Codex CLI 0.152.1 live record](../../../../docs/research/codex-hook-runtime-live/20260903T142001Z-cli-0.152.1/report.md) upgrades only the events and outcomes enumerated in that record; it does not establish untested hook paths or complete containment.

Current evidence on 2026-09-03:

| Surface | Result | Classification |
|---|---|---|
| Official event/input/output contract | Re-read from the linked Codex documentation | `DOCUMENTED` |
| `python3 components/hook-runtime/reference/codex-python/tests/run_tests.py` | 50 of 50 subprocess cases passed | `SIMULATED` |
| Codex discovery, trust, matcher firing, blocking, feedback, and bounded `SubagentStop` continuation | Declared acceptance gate passed in disposable repositories with Codex CLI 0.152.1; see the linked live record and its preserved qualifications | `OBSERVED_LIVE` for the enumerated probes only |

## 1. Why there is one dispatcher per event

Codex configuration has three levels: event, matcher group, and handler. There is no wildcard registration that subscribes one handler to all lifecycle events, so this POC registers four small event entries. Each entry invokes the same dispatcher with the expected event name:

```text
Codex event JSON on stdin
        |
        v
hookd.py --expect-event <Event>       provider input validation and output encoding
        |
        v
engine.py                             bounded child process
        |
        v
checks.REGISTRY                       explicit, ordered Python classes
        |
        v
policy.json                           data only; observe or enforce mode
        |
        v
exit status + stdout/stderr           the exact protocol for that event
```

The four POC events are:

- `SessionStart`
- `PreToolUse`
- `PostToolUse`
- `SubagentStop`

Each entry uses this installed command shape, with the event name changed to match its containing event key:

```text
python3 "$(git rev-parse --show-toplevel)/.codex/hooks/hookd.py" --expect-event SessionStart --deadline-ms 6000
```

The handler timeout is 10 seconds. The supervisor's 6-second child deadline is deliberately shorter. Tool-event matchers are omitted, so the registry—not the configuration file—selects tools.

The event declarations belong in `.codex/hooks.json`, not as repeated inline tables in `.codex/config.toml`. Codex merges hooks from all active layers and launches multiple matching command hooks for one event concurrently. Therefore:

- `hookd` provides deterministic ordering only among checks in its own registry;
- it cannot order, suppress, or replace hooks loaded from user, managed, plugin, or other project sources;
- adding a check for one of the four registered events changes Python code and tests, not `.codex/hooks.json` or `.codex/config.toml`;
- supporting a fifth lifecycle event requires one new event entry and a tested output adapter for that event.

Do not put the same project hooks in both `.codex/hooks.json` and inline `[hooks]` tables. Codex merges both representations and warns; it does not treat one as an override.

Matcherless registration trades configuration stability for runtime cost. This POC starts a supervisor and one bounded engine child for every registered event occurrence, including tool calls that no check ultimately selects. The fixture suite does not establish acceptable interactive latency. A live probe must record end-to-end hook latency and check-level `duration_ms`; until then performance is `NOT_EVALUATED`. A production runtime should avoid a two-process Python hot path, while retaining one ordered dispatch decision per event.

## 2. Source and installed layout

The reference source is:

```text
components/hook-runtime/reference/codex-python/
  hookd.py
  engine.py
  policy.json
  policy.schema.json
  hooks.codex.json
  install.sh
  COOKBOOK.md
  protocol.py
  checks/
    __init__.py
    base.py
    builtin_registry.py
    local_registry.py
    _template.py
    session_selftest.py
    protect_paths.py
    command_guard.py
    audit_event.py
    subagent_receipt.py
  tests/
    run_tests.py
```

After installation in a project, the relevant layout is:

```text
<project>/
  .codex/
    hooks.json                 one hookd handler for each of the four events
    hooks/
      hookd.py                 Codex dispatcher
      engine.py                isolated policy/check engine
      protocol.py              strict event and command/path parsing
      policy.json              local versioned policy; preserved on reinstall
      checks/
        __init__.py            combines the two explicit registries
        base.py                Outcome and Check contracts
        builtin_registry.py    shipped, explicit BUILTIN_CHECKS tuple
        local_registry.py      project-owned, explicit LOCAL_CHECKS tuple
        *.py                   one check class per module
      hookd.log.jsonl          runtime evidence; must be ignored
      receipts/                fixture receipt output; must be ignored
```

The installer copies executable code. The source component remains the reviewed reference; the installed copy is the code Codex invokes. Record hashes when comparing the two.

## 3. The check contract

Each check is a class with declarative routing metadata and one deterministic operation:

```python
class MyCheck(Check):
    name = "my_check"
    events = frozenset({"PreToolUse"})
    tool_pattern = r"^apply_patch$"
    order = 60
    critical = True

    def evaluate(self, event, context: CheckContext) -> Outcome:
        return Outcome.pass_()
```

The allowed decisions are deliberately smaller than Codex's complete output vocabulary:

| Outcome | Meaning inside hookd |
|---|---|
| `pass` | Make no decision. Normal Codex permissions still apply. |
| `violation` | A policy violation. In observe mode its audit outcome is rendered as `would_deny` and the provider decision is suppressed. In enforce mode the event adapter emits the documented blocking or feedback response. |
| `context` | Add bounded developer context. In this four-event POC, checks return it only for `SessionStart`. |
| `warning` | Surface a sanitized health warning. In this POC, it is rendered only for `SessionStart` or `SubagentStop`. |
| `stop` | End a repeated `SubagentStop` validation attempt instead of creating another continuation loop. It is invalid for every other event. |

There is no positive `allow` decision. A hook must not bypass Codex's normal permission prompt. Codex documents input rewriting for `PreToolUse`, but this POC does not implement it.

Registry arbitration is exact:

1. Load and validate `policy.json` before evaluating a check.
2. Validate the combined explicit registry; duplicate check names or duplicate orders are a configuration fault.
3. Sort the registry by `order`.
4. Skip a check unless its event and optional tool pattern apply.
5. Evaluate checks in order.
6. The first enforce-mode violation is final. Later checks do not run; the dispatcher itself records the final event result.
7. If there is no violation, prepend any sanitized warning to context concatenated in registry order, then apply the output bound. Warning-first ordering keeps the always-present SessionStart health context from hiding a later advisory failure even at the minimum context limit.
8. Silence is the normal pass-through result, except that a successful `SubagentStop` emits `{}` because that event requires JSON on stdout when exit status is zero.

Checks do not discover modules by scanning a directory. Executable policy is an auditable supply-chain input. Shipped classes appear in `BUILTIN_CHECKS`; project classes appear in the installer-preserved `LOCAL_CHECKS`; `checks/__init__.py` combines those tuples into `REGISTRY`.

## 4. Exact extension procedure

There are two extension routes. Do not put a project rule into the shipped registry merely to make the installer retain it.

### 4.1 Add a project-local check

After installing the POC in the target project:

1. Copy `.codex/hooks/checks/_template.py` to `.codex/hooks/checks/<check_name>.py`.
2. Give the class a unique lowercase-underscore `name` and a non-negative integer `order` that no built-in or local class uses.
3. Set `events` to a non-empty `frozenset` containing only the four registered events.
4. Set `tool_pattern` to `None` or a valid regular-expression string. Match Codex's canonical `tool_name`, not a display alias. File edits arrive as `apply_patch`; `Edit` and `Write` may match in configuration but are not the event's canonical name.
5. Put optional local data under `policy.json#check_config.<check_name>`. Override `validate_config()` to reject every unknown key and wrong type, and read the validated object with `context.config_for(self.name)`. A configuration name without a registered check fails closed. Do not add ad hoc top-level keys or environment-variable overrides.
6. Return an `Outcome`: normally `Outcome.pass_()` or `Outcome.violation(<code>, <safe message>)`. Use `Outcome.context_(...)` only on `SessionStart`, `Outcome.warning(...)` only on `SessionStart` or `SubagentStop`, and `Outcome.stop(...)` only for a repeated `SubagentStop`. Never print, exit, write provider JSON, or mutate source files from a check.
7. Import the class explicitly in `.codex/hooks/checks/local_registry.py` and append the class once to its `LOCAL_CHECKS` tuple.
8. Add a project subprocess test that invokes `.codex/hooks/hookd.py --expect-event <Event>` and covers one pass, one violation, and one malformed-input or boundary case. Importing the class directly does not test the provider process contract.
9. Run the test, then run the installer with `--check`. The installer preserves `local_registry.py` and project module names that do not collide with shipped module names.
10. Open a fresh session, review `/hooks`, and run a safe live fixture. Changing Python behind an unchanged command may not change the hook-definition hash, so `/hooks` trust is not code-integrity evidence; review and hash the installed module separately.

### 4.2 Add a shipped built-in check

1. Add the module under `components/hook-runtime/reference/codex-python/checks/`.
2. Import it and append its class once in `checks/builtin_registry.py`.
3. Add its complete subprocess cases to `tests/run_tests.py`.
4. Run from the repository root:

   ```bash
   python3 components/hook-runtime/reference/codex-python/tests/run_tests.py
   ```

5. Install into a disposable project/worktree, verify with `install.sh --check`, review the installed diff and hashes, then run the relevant live smoke step. Do not describe the check as `OBSERVED_LIVE` until that run has an evidence record.

Adding a check for `PermissionRequest`, `Stop`, `UserPromptSubmit`, or another unregistered event is a protocol change, not either procedure above. It requires:

1. an official-contract refresh;
2. an event parser and event-specific response tests;
3. one new handler in `hooks.codex.json`;
4. installer merge/idempotence coverage for that event;
5. a fresh `/hooks` trust review; and
6. a live probe before any support claim.

## 5. Event and decision matrix

All command hooks receive one JSON object on stdin. Codex supplies common fields including `session_id`, `transcript_path`, `cwd`, `hook_event_name`, and `model`; turn-scoped events also carry `turn_id`. This POC uses the event and safe identifiers, and uses `cwd` only as a reference-source fallback because an installed dispatcher derives its root from its own `.codex/hooks/` location. It never parses the transcript or model value. Codex types `tool_input` as a JSON value; only the canonical `Bash` and `apply_patch` adapters require its documented object-with-`command` shape.

| Event | Fields used by the POC | Exit 0 with no output | Enforce-mode violation | Other supported POC output | Limit |
|---|---|---|---|---|---|
| `SessionStart` | event name and safe common identifiers; `source` is ignored | session continues | no blocking form is claimed | health uses `hookSpecificOutput.additionalContext`; faults use a bounded `systemMessage` | Health context proves only that this invocation ran. |
| `PreToolUse` | common fields, `turn_id`, `tool_name`, `tool_use_id`, `tool_input` | normal permission flow continues | exit 0 with `hookSpecificOutput.hookEventName=PreToolUse`, `permissionDecision=deny`, and a safe reason | none | Hosted tools and specialized paths may not traverse this hook. |
| `PostToolUse` | tool name/use id and safe common identifiers; raw `tool_input` and `tool_response` are ignored by audit | original result continues | exit 0 with `decision=block` and a safe reason | audit logging | The tool already ran; no file or external side effect is undone. |
| `SubagentStop` | common fields, `turn_id`, `agent_id`, `agent_type`, `agent_transcript_path`, `stop_hook_active`, `last_assistant_message` | exit 0 with `{}` | first invalid receipt returns `decision=block`; a second invalid stop returns `continue=false` | none | The second form terminates the hook continuation; it does not turn the receipt into a success. |

Codex `PreToolUse` does not document `agent_id` or `agent_type`. This POC therefore does not claim role-authenticated tool calls. `SubagentStart` and `SubagentStop` identify an agent, but that identity cannot be inferred backward onto an individual tool event.

Codex treats `apply_patch` as the canonical file-edit tool. Its documented input, like `Bash`, is `tool_input.command`. A path check must inspect every add, update, delete, and move path in a patch. A Claude-style lookup of `tool_input.file_path` does not enforce a Codex patch.

`PostToolUse` is evidence and feedback, never rollback. Any completed write is independently checked by the candidate-root transition and promotion diff.

## 6. The shipped checks

| Check | Event | Observe mode | Enforce mode | Exact role |
|---|---|---|---|---|
| `session_selftest` | `SessionStart` | emits health context | same | Names the policy mode/hash and project root name, and states the enforcement boundary. |
| `protect_paths` | `PreToolUse` | records `would_deny` | denies | Extracts and canonicalizes every `apply_patch` path; rejects protected, escaping, symlinked, or ambiguous targets. |
| `command_guard` | `PreToolUse` | records `would_deny` | denies | Applies deny patterns only to normalized command positions and refuses shell forms this bounded parser cannot safely inspect. It is not a complete Bash parser or OS sandbox. |
| `audit_event` | `PostToolUse` | records sanitized metadata | same | Adds sanitized tool name and tool-use id to the dispatcher's event/check/result/duration/policy-hash record. |
| `subagent_receipt` | `SubagentStop` | validates and records without continuing | continues once on invalid required receipt | Requires selected agent types to return exactly one bounded JSON receipt. It never logs the receipt body. |

`observe` and `enforce` are policy modes, not inferred states:

- `observe`: deny-capable policy checks still execute and log `would_deny`, but the engine suppresses that policy violation before provider rendering, so hookd emits no policy-blocking response; a critical check crash is an integrity fault and remains visible or blocking in either mode;
- `enforce`: the same deterministic check result is rendered as the event's denial or continuation response.

Changing modes is an explicit local policy operation. It does not change a hook definition, does not prove the hook is trusted, and does not replace the live smoke test.

### 6.1 Policy contract

`policy.json` is one closed-schema JSON object. The engine rejects missing and unknown keys. `policy.schema.json` is its structural review/tooling representation; runtime and installer validation remain authoritative for cross-item semantics such as unique command IDs, canonical paths, registered `check_config` owners, and each check's nested configuration contract.

The policy file is capped at 1 MiB before parsing. The runtime and installer also apply aggregate nesting and node-count bounds, so an extension cannot use `check_config` to smuggle an unbounded JSON structure into the hook path.

This Codex sibling was installed and exercised in the disposable sessions recorded by the linked live proof, but it has not been released as a compatibility surface. Its v1 policy therefore includes `check_config` from the first releasable POC. If an out-of-tree copy of an earlier draft used the same v1 identifier without that key, it requires an explicit migration; silently treating the two shapes as compatible is forbidden.

| Key | Accepted value |
|---|---|
| `schema` | exactly `devforgeai.hookd-policy/v1` |
| `mode` | exactly `observe` or `enforce` |
| `protected_paths` | non-empty unique strings; each is an exact project-relative POSIX path or a prefix ending in `/**` |
| `deny_outside_project` | boolean |
| `allowed_external_redirects` | unique canonical, literal absolute path strings; the shipped policy contains only `/dev/null` |
| `denied_commands` | objects containing exactly an uppercase-underscore `id` and an anchored `pattern` |
| `receipt_agents` | unique agent-type strings |
| `receipt_schema` | exactly `devforgeai.worker-result/v1` |
| `receipt_statuses` | non-empty subset of `pass`, `fail`, `needs_user`, `could_not_run` |
| `max_receipt_bytes` | integer from 1,024 through 65,536; shipped value 65,536; the supervisor separately caps the complete outer event at 262,144 bytes |
| `max_context_chars` | integer from 128 through 16,384; shipped value 2,000 |
| `check_config` | object keyed by registered check name; each value is an object whose closed shape is validated by that check's `validate_config()` |

The shipped protected-path list covers `.codex/hooks.json`, `.codex/config.toml`, `.codex/hooks/**`, canonical DevForgeAI state/provenance, `.git`, `.git/**`, root `AGENTS.md`, and root `.env`. It does not imply that nested `AGENTS.md`, nested `.env`, or unrelated paths are protected. Add those exact paths or prefix rules deliberately and test them.

The shipped command rules are `GIT_FORCE_PUSH`, `GIT_RESET_HARD`, `GIT_CLEAN`, and `RECURSIVE_FORCE_ROOT_DELETE`. They are early-denial examples, not a complete command allowlist.

### 6.2 Receipt contract

A receipt-required worker's complete, non-null `last_assistant_message` is exactly one JSON object—no prose, duplicate JSON keys, or Markdown fence. Codex may supply `null`; for a receipt-required worker this is a missing receipt, not a malformed provider event. This is a valid shape:

```json
{
  "schema": "devforgeai.worker-result/v1",
  "run": "RUN-001",
  "skill": "dev",
  "phase": "red",
  "agent": "red_dev",
  "status": "pass",
  "candidate": {
    "id": "RUN-001",
    "input_checkpoint": "base"
  },
  "claimed_paths": ["tests/test_app.py"],
  "evidence_refs": ["evidence/red.json"],
  "note": "",
  "issues": []
}
```

Unknown top-level keys are rejected. The exact field rules are:

| Field | Required | Rule |
|---|---|---|
| `schema` | yes | Equals the policy's `receipt_schema`. |
| `run` | yes | Non-empty string, at most 200 characters. |
| `skill` | yes | Matches `[a-z][a-z0-9-]*`. |
| `phase` | yes | Matches `[a-z][a-z0-9_]*`. |
| `agent` | yes | Matches `[a-z][a-z0-9_-]*` and equals the event's `agent_type`. |
| `status` | yes | Appears in the policy's `receipt_statuses`. |
| `candidate` | yes | Contains exactly `id` and `input_checkpoint`; each is a non-empty string of at most 200 characters. |
| `claimed_paths` | yes | At most 64 unique non-empty strings; must be empty unless status is `pass`. |
| `evidence_refs` | no | At most 16 unique non-empty strings. |
| `reason_code` | no | Legal only with `could_not_run`; value is `runner_missing`, `timeout`, `network`, or `hook_fault`. |
| `note` | no | String of at most 16,384 characters. |
| `issues` | no | At most ten entries. Each is a 1–300 character string or an object containing required 1–300 character `text`, optional 1–120 character `id`, and optional `kind` matching `[a-z][a-z0-9_]*`. No other object keys. |
| `next` | no | Legal only with `fail`; matches `[a-z][a-z0-9_]*`. |

Every path-array entry is at most 1,024 characters, is relative, contains no backslash or control character, and has no `..` segment. The policy fixes the admitted schema, statuses, agent types, and total receipt byte limit.

A validated receipt is stored with its exact bytes under `receipts/` using an exclusive, non-following create and a filename derived from hashed event identity and payload. The audit log records only its filename and SHA-256. This POC does not prove that claimed paths or checkpoints match the filesystem; the sequencer derives and validates those facts independently.

## 7. Path and command rules

For every patch path, `protect_paths` must:

1. reject NULs and malformed headers;
2. resolve a relative target from the installed project/worktree root;
3. canonicalize the nearest existing ancestor so new files are covered;
4. reject a target outside the project/worktree root when `deny_outside_project` is true; the shipped policy sets it true;
5. resolve symlinks before comparing the target;
6. compare the root-relative POSIX path against exact policy entries or entries ending in `/**`; and
7. validate both source and destination for a move.

The check fails closed when it cannot enumerate all affected paths. A multi-file patch passes only if every path passes.

Path interception is not process confinement. A subprocess invoked by Bash can write paths that are absent from its command text. A worktree limits which checkout is at risk, while the sequencer's complete tree diff detects undeclared candidate changes. The OS sandbox controls filesystem locations outside that root. None substitutes for the others.

`command_guard` does not treat a regular-expression search over an entire command as a shell parser. It recognizes heredoc declarations only outside quotes and comments—including comments that begin immediately after a control operator—accepts only quoted delimiters, removes those literal bodies, separates top-level command positions, strips syntactically bounded redirections before matching, normalizes a bounded wrapper/assignment/control prefix grammar, and applies configured patterns to those positions. Wrapper options, unrecognized assignment forms, and shell line continuations fail closed because their interpretation is ambiguous; controls and wrappers are reduced iteratively so forms such as `! command ...` cannot hide the command. Unquoted heredocs, substitutions, process substitutions, grouping, and function syntax also fail closed. These rules close the observed false positive in which a quoted heredoc body merely mentioned a denied command, and the matching bypasses in which a commented `<<TOKEN`, a backslash inside an operator-adjacent comment, or a leading redirect hid a later real command. The check remains a guardrail rather than a complete Bash parser. An enforcement-grade DevForgeAI command surface uses an exact, single-command broker grammar and rejects compound commands, redirects, pipelines, substitutions, variables, heredocs, and unknown subcommands rather than trying to infer every Bash side effect.

The path check admits only literal redirect targets. It normalizes legacy `>&word`, permits descriptor duplication such as `2>&1`, and rejects targets containing variables, tilde expansion, globs, braces, or parentheses because their destination cannot be proven from the event text.

No denial claim is made for semantically indirect or path-equivalent execution such as aliases or functions, `sh -c`, `eval`, `xargs`, an absolute path to `git`, or Git global-option forms that do not match the configured anchored expression. Those gaps are why this check is early feedback and why production uses an exact command broker plus the post-run transition oracle.

The DevForgeAI contract reserves mutating Git for the sequencer. A model-driven command must not commit, reset, clean, checkout, rebase, merge, tag, remove a worktree, or promote a candidate. The shipped POC denies only the command patterns listed in section 6.1, so it does not claim complete enforcement of that contract. A Git worktree's `.git` is commonly a file that points into shared repository metadata; treating only `.git/` directories as protected is insufficient.

## 8. Failure policy

The dispatcher has an internal deadline shorter than the timeout in `hooks.codex.json`. A host timeout is a hook failure, not a reliable policy denial.

| Failure | POC result |
|---|---|
| malformed, empty, oversized, or non-object stdin | fail closed when the expected event can block; otherwise emit a visible health fault; unreadable `SubagentStop` input terminates rather than requesting an unbounded retry |
| `hook_event_name` differs from `--expect-event` | configuration fault; do not route the event under the supplied name |
| missing, symlinked, oversized, malformed, or wrong-version policy | critical fault |
| critical check raises | synthesize the event's violation response in either policy mode; observe mode cannot turn an integrity failure into healthy pass-through |
| advisory check raises | sanitize and record the fault; do not silently call it successful |
| registry import or validation fails | supervisor returns the expected event's fault response before the host timeout |
| internal deadline expires | terminate the engine and return the expected event's fault response |
| audit log cannot be written | the decision is unchanged; the absent audit artifact is an evidence failure for the later transition/promotion gate |

For `PostToolUse`, “fail closed” cannot mean undoing a completed operation. It means the event is recorded as a fault, feedback is returned where supported, and the transition/promotion gate refuses to trust the hook as evidence.

For `SubagentStop`, use `stop_hook_active` to prevent an infinite bounce. The first invalid required receipt may continue the subagent. If the continued agent stops again without a valid receipt, persist the rejection and hand control to the sequencer/human path rather than issuing another unbounded continuation.

## 9. Output and evidence hygiene

Hook output enters the model or UI. Keep it small and non-sensitive:

- never emit file bodies, patch text, raw commands, prompts, tool responses, transcripts, secrets, environment values, or receipt bodies;
- use stable reason codes plus one actionable sentence;
- cap additional context in hookd as well as with `additionalContextLimit`;
- use exit 0 with no output for pass-through, except the required `{}` on `SubagentStop`;
- write one sanitized JSON object per audit line;
- identify receipts by a sanitized or hashed `agent_id`, never by an unchecked path component;
- write receipt files atomically; and
- record policy SHA-256 in health and audit evidence and hash the installed runtime separately during the smoke test.

Codex may spill large model-visible hook output to disk. That is a safety valve, not permission to return large or secret content.

## 10. Staged installation

Do not install the reference component on `main`. Test it in a disposable project or a dedicated topic worktree.

From the target project root:

```bash
components/hook-runtime/reference/codex-python/install.sh --dry-run
components/hook-runtime/reference/codex-python/install.sh
components/hook-runtime/reference/codex-python/install.sh --check
```

The first install uses the source policy's `observe` mode. A reinstall preserves a valid installed policy and therefore does not silently downgrade an existing `enforce` installation. The installer:

1. requires a Git/worktree root and Python 3.11 or newer, so `.codex/config.toml` is parsed with the standard-library TOML parser rather than lexical heuristics;
2. parses existing `.codex/hooks.json` and refuses malformed JSON;
3. refuses symlinked runtime/configuration destinations;
4. preserves unrelated hook definitions;
5. merges exactly one owned handler for each of the four events;
6. detects duplicate owned handlers rather than choosing one;
7. preserves an existing valid `policy.json`;
8. replaces each managed file atomically, while making no claim that a multi-file upgrade is one transaction;
9. avoids changing `.codex/config.toml`, `.gitignore`, or hook trust;
10. prints the installed root, resulting policy mode, source/destination runtime custody digests, policy/hooks file SHA-256 values, and exact trust step; and
11. is idempotent on a second identical invocation.

If the same project layer contains inline Codex hooks, stop with a hook-source conflict instead of adding a second representation.

Inspect the proposed changes before opening Codex:

```bash
git diff -- .codex/hooks.json .codex/hooks/
python3 components/hook-runtime/reference/codex-python/tests/run_tests.py
components/hook-runtime/reference/codex-python/install.sh --check
```

The installer does not copy `tests/`. The reference suite tests a disposable installed copy of the source runtime; a project-local extension needs its own subprocess case as section 4.1 requires.

Before any target write, the installer assembles shipped runtime bytes plus preserved project check modules and the desired policy in a temporary directory, then runs `engine.py --validate-installation`. This binds every `check_config` owner to the explicit registry and runs each class's `validate_config()`. Consequently, installer execution also imports project-owned check code. Treat that code as trusted executable input: validators must be deterministic, bounded, side-effect free, and must not start subprocesses, threads, or network operations. The ten-second installer timeout terminates the validation engine, not an arbitrary descendant process tree.

## 11. Trust and audit-only live smoke

Start a fresh Codex session in the disposable project/worktree. Existing sessions do not prove how a fresh client discovers and trusts the new definition.

1. Run `/hooks`.
2. Confirm exactly four project handlers, their source, command, absence of a matcher, and timeout.
3. Review and trust the exact definitions. Do not use a trust bypass for the proof.
4. Start another fresh session if the client instructs you to do so.
5. Confirm `SessionStart` reports `mode=observe`, the policy hash, expected project root name, and guardrail boundary.
6. Perform one harmless patch in an unprotected fixture path.
7. Attempt one fixture patch that would touch a protected path.
8. Confirm the protected attempt was logged as `would_deny` under the observe-mode policy hash but was not represented as blocked.
9. Run one harmless shell command and one fixture command that would violate the command policy.
10. Complete an unlisted subagent and confirm receipt enforcement did not apply.
11. Inspect the audit log and verify it contains no command, patch, prompt, tool-response, transcript, or receipt body.

Record:

- Codex version;
- OS and shell;
- Git root and worktree path;
- hook definition hash;
- runtime and policy hashes;
- session id;
- event received;
- expected and actual result;
- exit code or rendered decision; and
- file/diff evidence demonstrating whether an operation occurred.

Passing the subprocess suite is `SIMULATED`. Completing these steps supplies `OBSERVED_LIVE` evidence only for observe-mode discovery, input shape, context, and logging—not for denial.

## 12. Enable denials and run the enforcement smoke

After the observe-only smoke matches its expectations:

```bash
components/hook-runtime/reference/codex-python/install.sh --enable-denies
```

Re-read the policy and verify that its mode is exactly `enforce`. If the hook definition changed, `/hooks` must show it for review; policy-mode changes are not assumed to retrigger Codex's definition-hash trust workflow.

In a fresh session:

1. Confirm the `SessionStart` health line says `mode=enforce`.
2. Ask Codex to patch a disposable protected fixture file.
3. Confirm `PreToolUse` denies it and the file digest is unchanged.
4. Attempt the command-policy fixture and confirm it does not execute.
5. Perform one allowed fixture patch and confirm `PostToolUse` logs it.
6. Start a receipt-required fixture agent whose first final message is prose. Confirm one `SubagentStop` continuation.
7. Have it return the exact valid JSON receipt. Confirm acceptance and atomic receipt storage.
8. Repeat with a deliberately invalid second stop and confirm the loop terminates through the documented human/sequencer path.
9. Reinspect the log for redaction and correlate each line with the recorded session/turn/tool identifiers.

Never probe destructive behavior against a real branch, remote, protected source file, secret, or external service. The test target is an expendable fixture whose before/after bytes are known.

## 13. Provider parity and deliberate differences

| Concern | Claude reference | Codex reference |
|---|---|---|
| Registration | one dispatcher handler per selected Claude event | one dispatcher handler per selected Codex event |
| Project hook file | `.claude/settings.json` | `.codex/hooks.json`; no duplicate inline project hooks |
| Handler command | Claude supports its documented command/argument form | Codex documents a command string; resolve an installed executable or Git-root path |
| Canonical file edit | Claude `Edit`/`Write` events expose paths | Codex reports `apply_patch`; patch text is in `tool_input.command` |
| Tool-call actor | Claude live evidence is Claude-only | Codex Pre/PostToolUse does not document subagent identity |
| Ask from PreToolUse | available in the Claude reference | `permissionDecision: "ask"` is unsupported; silence leaves normal permission behavior |
| PermissionRequest | separate Claude behavior | documented Codex event, but outside this four-event POC |
| Config-change event | Claude offers provider-specific coverage | no Codex event is claimed |
| Post-use block | cannot undo the completed tool | cannot undo the completed tool |
| Subagent receipt | provider-specific final-message fields and output | uses Codex `agent_id`, `agent_type`, `last_assistant_message`, and `stop_hook_active` |
| Native worktree isolation | provider feature, separate from this runtime | candidate-root/worktree enforcement remains sequencer-owned |

Parity means the same invariant receives an equivalent test and honest limitation. It does not mean copying field names or output JSON.

## 14. Limits and enforcement boundary

The following remain true even after a successful live smoke:

1. Project hooks are trust-gated and can be disabled. Managed hooks are required when an administrator must enforce their presence.
2. Hooks from other active layers still run, and Codex may launch matching command hooks concurrently.
3. Hosted tools do not use the local function-tool hook path, and specialized tool paths may opt out.
4. PreToolUse does not observe every filesystem side effect of a child process.
5. PostToolUse does not roll anything back.
6. A worktree isolates a checkout but shares Git objects and metadata with the repository.
7. Codex tool events do not provide enough identity to authenticate a red, green, or refactor worker at each write.
8. A hook's decision is not proof that tests, acceptance criteria, provenance, or architectural constraints hold.
9. A passing POC does not make Python hookd the production DevForgeAI authority.
10. The installer replaces managed files one at a time and preserves unknown modules; it neither provides a directory-wide atomic upgrade nor removes stale shipped filenames. A production distributor needs a signed/versioned managed-file manifest and an atomic release-pointer switch while keeping project extensions in a separate namespace.
11. `hookd.log.jsonl` and the aggregate receipt directory have no rotation or total-size quota in this POC. Do not operate it as a long-lived service; production needs explicit retention, quota, full-disk behavior, and evidence-export rules.

The production chain therefore remains:

```text
provider hook guardrail
    -> OS sandbox and candidate-root containment
    -> deterministic sequencer diff and transition oracle
    -> clean verification
    -> serialized promotion/CI revalidation
```

The hook may stop an observable action early. The sequencer decides whether a candidate may advance or be promoted.

## 15. Troubleshooting without overstating results

| Symptom | Check | Status wording until resolved |
|---|---|---|
| `/hooks` does not list the entry | project trust, hooks feature, JSON location, same-layer duplicate representation | `COULD_NOT_RUN: hook not discovered` |
| hook shown as untrusted/skipped | review the exact definition through `/hooks` | `COULD_NOT_RUN: hook not trusted` |
| no SessionStart health line | fresh-session source/matcher, command path, Python, stderr | `HOOK_FAULT`; do not claim enforcement |
| hook exits 1 or times out | internal deadline, import/policy failure, host timeout | `HOOK_FAULT`; generic failure is not a documented deny |
| protected patch passes in observe mode | expected; inspect `would_deny` evidence | `SIMULATED/OBSERVED_LIVE observe only` |
| protected patch passes in enforce mode | event path extraction, policy mode/hash, trust, tool coverage | `ENFORCEMENT_FAILURE`; promotion must stop |
| PostToolUse flags a write | inspect and restore through the candidate/sequencer workflow | never say the hook reverted it |
| Subagent repeats forever | `stop_hook_active` handling and receipt-attempt limit | `ENFORCEMENT_FAILURE`; stop the run |
| expected hosted-tool event is absent | current Codex tool coverage | `UNSUPPORTED`, not a passing test |

Use `NOT_EVALUATED` when a required test was not run, `COULD_NOT_RUN` when its prerequisites were unavailable, and `NOT_OBSERVED_LIVE` when only documentation or fixture execution exists. Do not collapse those states into “passed.”
