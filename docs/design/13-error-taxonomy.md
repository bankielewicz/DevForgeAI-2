# 13. Error taxonomy

Status: draft, 2026-09-03. Not normative and not installed. The normative, machine-readable taxonomy is `framework/contracts/error-taxonomy.yaml` (installed to `.devforgeai/contracts/error-taxonomy.yaml`), validated by `schemas/devforgeai/v1/error-taxonomy.schema.json`. This page explains the shape and records the decisions behind it; when the two disagree, the YAML wins and this page is stale.

## Why one taxonomy

The framework reports outcomes from four places: a provider hook (deny, ask, context), the sequencer (refusal tokens and exit codes), a worker (status and reason code) and an oracle (test classification). Documents 09 and 10 already define each vocabulary, but nothing said how they roll up into what a human reads in a handoff, and the research's decision D-023 asked for a distinction the design had collapsed: a phase that *could not start* (missing runner), a phase whose *check was attempted and invalidated* (harness fault, timeout), and a phase that *can run but needs something external* (a decision, a lease, a moved base). One file now carries every code, its emitter, its wire protocol, its roll-up and its recovery route.

## Layers

| Layer | Codes | Wire form |
|---|---|---|
| Phase outcome | `COMPLETE`, `NEEDS_DECISION`, `BLOCKED`, `FAILED`, `COULD_NOT_RUN`, `INFRA_FAILURE` | the handoff's outcome line |
| Sequencer exit code | `0` done, `1` refused, `2` usage, `3` could not run | process exit |
| Hook decision | `none`, `deny`, `ask`, `context` (never `allow`) | exit 2 + stderr for deny; JSON otherwise |
| Hook failure class | critical check error, advisory check error, malformed input, budget exceeded, host fail-open | exit 2 + stderr, or a log line; host fail-open is invisible until promotion |
| Sequencer refusal | `STORY_IN_FLIGHT`, `FENCE_OVERLAP`, `LEASE_HELD`, `UNCLAIMED_CHANGE`, `STALE_BASE`, `MERGE_CONFLICT`, `DIRTY_TARGET`, `NO_CANDIDATE`, `REFUSED` | exit 1, token first on stderr, handoff `next` |
| Worker status and reason | `pass`, `fail`, `needs_user`, `could_not_run`; `runner_missing`, `timeout`, `network`, `hook_fault` | the receipt |
| Oracle classification | `PASS`, `EXPECTED_TEST_FAILURE`, `TEST_FAILURE`, `NO_TESTS`, `COLLECTION_ERROR`, `INFRA_FAILURE`, `TIMEOUT` | `<phase>-result.json#last_oracle` |
| Gate policy | `BLOCK`, `REQUIRE_HUMAN`, `WARN`, `OFF` | `run.yaml#gate_policy` |
| Run state | `active` (with optional `blocked_at`), `ready_to_promote`, `promoted`, `abandoned` | `state.yaml#runs` |

## The roll-up

The handoff renderer applies the YAML's `rollup` list, first match wins: promoted or ready to promote is `COMPLETE`; a `needs_user` receipt is `NEEDS_DECISION`; `could_not_run` with `runner_missing` is `COULD_NOT_RUN` and with any other reason is `INFRA_FAILURE`, as are the `INFRA_FAILURE` and `TIMEOUT` oracle classes; `UNCLAIMED_CHANGE` and the test-failure oracle classes are `FAILED`; every other refusal, hook deny, attempt limit or lease condition is `BLOCKED`. The wire formats do not change: a worker still says `could_not_run` with a reason code, and the roll-up is what turns that into two different human-facing outcomes.

## Decisions recorded

1. **Contracts live in an installed tree.** `docs/` never reaches a target project, so the runtime reads `framework/contracts/`. The manifest entry and the installer rules are in that directory's README; the manifest itself is not edited by this draft.
2. **No `allow` in the hook layer.** The schema forbids the key. A hook that says allow bypasses the user's permission prompt.
3. **Host fail-open is a named class with no emitter.** It is inferred at promotion, where `DIRTY_TARGET` now also refuses a canonical path that became dirty outside the run's change set. Whether SessionStart should record hook health so its absence is reportable is open item 3 in the YAML.
4. **Existing codes are kept verbatim.** The draft adds the phase-outcome layer and the hook-failure classes on top of 09 and 10; it renames nothing, so no spec or conformance row changes under it.

## Open items before version 2

Listed in the YAML's `open_items`: whether the receipt gains an explicit `infra_failure` status instead of the roll-up splitting `could_not_run`; whether the handoff's `outcome` line migrates from the gate-policy vocabulary to the phase-outcome set or carries both; whether hook health is recorded at SessionStart.
