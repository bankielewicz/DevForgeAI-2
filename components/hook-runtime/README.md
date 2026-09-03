# hook-runtime

Runtime code for DevForgeAI's provider hook layer: the process a provider's hook entry invokes, the ordered checks it runs, and the protocol it speaks back. This directory is a component, not provider payload; provider registration fragments (the thin `settings.json` or `hooks.json` block that invokes an installed command such as `devforge hook dispatch --provider claude`) will eventually live under `providers/`, while runtime code will not.

## What is here today

There are two provider-specific Python reference proofs of concept:

- `reference/claude-python/` contains the Claude event adapter, explicit check registry, policy, settings fixture, installer, tests and cookbook.
- `reference/codex-python/` contains the Codex event adapter, a supervisor-isolated policy engine, explicit built-in and project registries, policy schema, `.codex/hooks.json` fixture, non-destructive installer, tests and cookbook.

The Codex reference's first attended observe/enforce run is preserved under `docs/research/codex-hook-runtime-live/20260903T142001Z-cli-0.152.1/`. Its declared acceptance gate passed for the enumerated Codex CLI 0.152.1 probes; the report's qualifications and containment boundary remain part of that result.

They reuse an architectural pattern, not a wire protocol. Claude and Codex expose different event fields, decision JSON, identity surfaces, configuration files and trust behavior. Neither reference may be described as provider-neutral or as evidence for the other provider.

The Codex reference registers one handler for each of four lifecycle events and routes every handler to the same dispatcher. Its ordered registry is the extension seam: adding a check for an already registered event does not add a hook entry. A genuinely new event still needs one configuration entry and a tested event adapter because Codex has no all-events registration.

These are **not** the authoritative DevForgeAI hook or sequencer contracts. They are executable protocol cookbooks. Hooks remain early guardrails; candidate-root diffs, transition oracles, explicit promotion and CI are the material enforcement chain. Each cookbook states its own `DOCUMENTED`, `SIMULATED`, `OBSERVED_LIVE` or `NOT_OBSERVED_LIVE` evidence status and must be read before making a provider-support claim.

See `reference/claude-python/COOKBOOK.md` and `reference/codex-python/COOKBOOK.md` for their protocol matrices, extension procedures, failure policies, test commands and live-probe recipes.
