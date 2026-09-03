# hook-runtime

Runtime code for DevForgeAI's provider hook layer: the process a provider's hook entry invokes, the ordered checks it runs, and the protocol it speaks back. This directory is a component, not provider payload; provider registration fragments (the thin `settings.json` or `hooks.json` block that invokes an installed command such as `devforge hook dispatch --provider claude`) will eventually live under `providers/`, while runtime code will not.

## What is here today

`reference/claude-python/` is a **Claude-only Python reference proof of concept** (`hookd.py`, an explicit check registry, `policy.json`, a settings fixture, an installer and a cookbook). Its status:

- 16/16 subprocess test cases pass locally (`python3 components/hook-runtime/reference/claude-python/tests/run_tests.py`).
- The scratch installer has been tested against a throwaway project; it has never been run against this repository.
- No live provider session has exercised it. Every protocol fact it relies on was read from the Claude Code hooks and permissions references on 2026-09-03, not observed.
- It implements Claude's hook input and output schema only. Claude and Codex have different hook schemas and outputs, so it must not be called provider-neutral or dual-provider.
- It is **not** the authoritative DevForge hook contract. The eventual implementation belongs in protected DevForge and is expected to be Rust; this reference exists to pin down behaviour (one dispatcher per event, explicit registry, fail-closed critical checks, exit-2 blocking, no `allow`) that the real runtime must reproduce.
- `settings.claude.json` inside the reference is a fixture, not an installable provider fragment. Installing it requires merging into an existing settings file, which `install-manifest.yaml` cannot yet express (a `mode: merge-json` style operation is a separate design task).

See `reference/claude-python/COOKBOOK.md` for the protocol table, failure policy, add-a-check recipe and best practices.
