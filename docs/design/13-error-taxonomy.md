# 13. Error taxonomy

Status: draft, 2026-09-04. Not normative and not installed. The frozen version-1 promotion candidate remains `framework/contracts/error-taxonomy.yaml`, validated by `schemas/devforgeai/v1/error-taxonomy.schema.json`. Range-kind PR runs use the staged version-2 vocabulary in `framework/contracts/error-taxonomy-v2.yaml`, validated by `schemas/devforgeai/v2/error-taxonomy.schema.json`. Both are installed by digest; this page explains their relationship and is stale if it disagrees with either machine-readable file.

## Why one taxonomy

The framework reports outcomes from four places: a provider hook (deny, ask, context), the sequencer (refusal tokens and exit codes), a worker (status and reason code) and an oracle (test classification). Documents 09 and 10 already define each vocabulary, but nothing said how they roll up into what a human reads in a handoff, and the research's decision D-023 asked for a distinction the design had collapsed: a phase that *could not start* (missing runner), a phase whose *check was attempted and invalidated* (harness fault, timeout), and a phase that *can run but needs something external* (a decision, a lease, a moved base). One file now carries every code, its emitter, its wire protocol, its roll-up and its recovery route.

## Layers

| Layer | Codes | Wire form |
|---|---|---|
| Phase outcome | `COMPLETE`, `NEEDS_DECISION`, `BLOCKED`, `FAILED`, `COULD_NOT_RUN`, `INFRA_FAILURE` | the handoff's outcome line |
| Sequencer exit code | `0` done, `1` refused, `2` usage, `3` could not run | process exit |
| Hook decision | `none`, `deny`, `ask`, `context` (never `allow`) | exit 2 + stderr for deny; JSON otherwise |
| Hook failure class | critical check error, advisory check error, malformed input, budget exceeded, host fail-open | exit 2 + stderr, or a log line; host fail-open is invisible until promotion |
| Sequencer refusal | `STORY_IN_FLIGHT`, `FENCE_OVERLAP`, `LEASE_HELD`, `UNCLAIMED_CHANGE`, `STALE_BASE`, `MERGE_CONFLICT`, `DIRTY_TARGET`, `NO_CANDIDATE`, `PR_RANGE`, `PR_DRAFT_PATHS`, `PR_TITLE`, `PR_BODY`, `PR_ENCODING`, `PR_PACKET`, `REFUSED` | exit 1, token first on stderr, handoff `next` |
| Worker status and reason | `pass`, `fail`, `needs_user`, `could_not_run`; `runner_missing`, `timeout`, `network`, `hook_fault`, `provider_tool_refused`, `prerequisite_missing`, `checkpoint_fault` | the receipt |
| Oracle classification | `PASS`, `EXPECTED_TEST_FAILURE`, `TEST_FAILURE`, `NO_TESTS`, `COLLECTION_ERROR`, `INFRA_FAILURE`, `TIMEOUT` | `<phase>-result.json#last_oracle` |
| Gate policy | `BLOCK`, `REQUIRE_HUMAN`, `WARN`, `OFF` | `run.yaml#gate_policy` |
| Run state | `active` (with optional `blocked_at`), `ready_to_promote`, `promoted`, `complete_external`, `abandoned` | `state.yaml#runs` |

## The roll-up

The handoff renderer applies the YAML's `rollup` list, first match wins: promoted, ready to promote, or complete external is `COMPLETE`; a `needs_user` receipt is `NEEDS_DECISION`; `could_not_run` with `runner_missing` is `COULD_NOT_RUN` and with any other reason, `provider_tool_refused` included, is `INFRA_FAILURE`, as are the `INFRA_FAILURE` and `TIMEOUT` oracle classes; `UNCLAIMED_CHANGE` and the test-failure oracle classes are `FAILED`; every other refusal, hook deny, attempt limit or lease condition is `BLOCKED`. The wire formats do not change: a worker still says `could_not_run` with a reason code, and the roll-up is what turns that into two different human-facing outcomes.

## Decisions recorded

1. **Contracts live in an installed tree.** `docs/` never reaches a target project, so the runtime reads `framework/contracts/`. The manifest entry and the installer rules are in that directory's README. The PR additions are version 2 so the CP-00 version-1 candidate manifest and its source-commit pin remain byte-identical.
2. **No `allow` in the hook layer.** The schema forbids the key. A hook that says allow bypasses the user's permission prompt.
3. **Host fail-open is a named class with no emitter.** It is inferred at promotion, where `DIRTY_TARGET` now also refuses a canonical path that became dirty outside the run's change set. Whether SessionStart should record hook health so its absence is reportable is open item 3 in the YAML.
4. **Existing codes are kept verbatim.** The draft adds the phase-outcome layer and the hook-failure classes on top of 09 and 10; it renames nothing, so no spec or conformance row changes under it.
5. **`provider_tool_refused` separates the provider from the framework.** It names a tool call the provider refused before any DevForgeAI hook ran — no hook saw it, no fence or lease was consulted, and nothing in the framework could have permitted it. It rolls up to `INFRA_FAILURE` like the other attempted-but-invalidated causes. `hook_fault` is reserved for the two framework faults it already named and no others: a hook event that lacked identity, and a malformed receipt. The PR refusal codes and `complete_external` are the first version-2 additions; they do not re-pin the open CP-00 candidate.

## Open items carried into version 2

Listed in the YAML's `open_items`: whether the receipt gains an explicit `infra_failure` status instead of the roll-up splitting `could_not_run`; whether the handoff's `outcome` line migrates from the gate-policy vocabulary to the phase-outcome set or carries both; whether hook health is recorded at SessionStart.
