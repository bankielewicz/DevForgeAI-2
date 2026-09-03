# Attended project-hook trust record

Codex CLI 0.152.1 was started interactively in each standalone repository without a trust-bypass flag. The project prompt's **Review hooks** path was selected. In `/hooks`, each project handler was opened and trusted individually with `t`.

The `/hooks` event table showed exactly four installed and active project handlers:

| Event | Installed | Active |
|---|---:|---:|
| SessionStart | 1 | 1 |
| PreToolUse | 1 | 1 |
| PostToolUse | 1 | 1 |
| SubagentStop | 1 | 1 |

All other displayed lifecycle events were 0 installed and 0 active. Each handler used the common dispatcher form:

`python3 "$(git rev-parse --show-toplevel)/.codex/hooks/hookd.py" --expect-event <Event> --deadline-ms 6000`

Every handler had a 10-second host timeout. SessionStart additionally had an `additionalContextLimit` of 1000. The source was the project `.codex/hooks.json`; no matcher was configured.

The `/hooks` UI did not display the definition hash. After trusting, the four exact handler hashes were read from Codex's persisted hook trust state and are preserved in `hashes/handler-trust.json`. Both project paths are persisted with `trust_level = "trusted"`.

SessionStart evidence:

- Observe trust/session: mode `observe`, policy `2461de8334c7d5ff164b8808915112ff94c7198ae5009410ce28774aee6019e0`.
- Enforce base session: mode `enforce`, policy `60a61df50bca5e45d10e561f8ad9c587a1e9efa1c1016ea435ca64b03f9562bb`.
- Extension session: mode `enforce`, policy `763935dbe6a3f52df1fd0b7025de3ec39974748efb7b19abc519d4f3e2bbd0f0`.

After the local extension, a fresh `/hooks` view again showed exactly the same four installed and active handlers. No new trust prompt appeared because `.codex/hooks.json` remained byte-identical; this does not imply separate trust of transitive Python modules.
