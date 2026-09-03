# Story Specification

Status: draft, 2026-09-02. Defines the story file, template v3 at `templates/story.md`. The story is the specification a development skill works through: gate, red, green, refactor, light QA, handoff. It is the last artifact before code, so it carries everything the code phase needs and nothing the code phase may decide.

## Who produces it, who consumes it

| Role | Skill and subagent | Reference |
|---|---|---|
| Deconstructs the epic into stories | `plan`, story-writer | `02-skill-roster.md` plan section |
| Reviews each story against the template | `plan`, critic | `01-skill-anatomy.md` templates section |
| Orders and sizes | `plan`, dependency-mapper and estimator | fills `blocked_by`, `size`, `sprint` |
| Validates before any code | the sequencer's gate, inlined in `devforgeai phase start <skill> <story>` | `01-skill-anatomy.md#the-seven-sub-phases` |
| Resolves assumptions | `clarify` | appends to Clarifications only |
| Mirrors status | the sequencer, at `phase next` | `state.yaml` is authoritative |

No new skill is introduced. The predecessor to development is `plan`.

## What a story must carry, and why

| Field or section | Consumer | Reason |
|---|---|---|
| `provenance` (epic and PRD anchors with hashes) | gate, `/analyze` | Proves the story descends from an accepted epic; stale hash is a defect. Kept separate from `blocked_by` so provenance and ordering are never conflated. |
| `blocked_by` | dependency-mapper, gate | Story ordering is data, not prose. Gate refuses a story whose blockers are not `done`. |
| `context` (excerpt, anchor, hash, INTENDED or OBSERVED) | every dev worker | The worker never opens the source document. OBSERVED is advisory; INTENDED binds. |
| `scope` | gate, `/analyze` | `03-brownfield.md` records reduced provenance for change and hotfix. |
| `write_fence` | gate, refactorer, provider hooks | The only paths a producer may create or modify inside the run's candidate root, and the set `ingest-result` checks the checkpoint diff against. This is the data a `PreToolUse` deny reads (`07-purpose-and-enforcement.md`, rung 3). |
| `commands` (hashed reference into `stack.yaml`, plus which keys) | the sequencer's transition checks | Keeps the story stack-neutral. A literal command in a story makes the framework single-language. No worker ever receives a literal command: the story names keys, the lease-holding producer may call `devforgeai run <key>` for one of them, and the sequencer resolves the same key from the hash-pinned `stack.yaml` section (`10-sequencer-and-contracts.md`) and runs the oracle itself. |
| `test_plan` (criterion, file, test name) | red-tester, smoke-qa, critic, the transition oracle | Authoritative for the criterion-to-test mapping. Red writes exactly these tests; the critic detects a criterion with no test or a test with no criterion; the transition check asserts each named test is present with the expected outcome. There is no separate criteria map. |
| `gate_policy` | gate | A defect-to-action map: each defect class declares `BLOCK`, `REQUIRE_HUMAN`, `WARN` or `OFF`, following Codex's corpus rule that every gate states its policy and its behaviour on timeout and malformed input. It is never a status a worker returns. |
| `risk_tier`, `size` | estimator, review | Size L must be split; risk raises review depth. |
| `## Interface` | green-implementer | Criteria say what is observable; the implementer also needs the contract: signatures, shapes, error behaviour, names other stories depend on. |
| `## Acceptance Criteria` | red-tester, critic | Numbered, one test each, EARS form recommended. `ASSUMPTION:` outside Clarifications blocks. |
| `## Unchanged Behaviour` | smoke-qa | Kiro's regression surface. Required for change and hotfix scope. |
| `## Out of Scope` | green-implementer, critic | Stops behaviour creep. |
| `## Verification` | every dev sub-phase | What red, green, refactor and light QA must each show, expressed only through `commands.use` keys. This is the TDD loop written into the spec. |
| `## Clarifications` | `clarify` | Append-only. The only section that changes after `ready`. |

## What a story must not carry

- Dev evidence, test output, or review verdicts. Those go to `.devforgeai/work/<run>/` (`01-skill-anatomy.md#evidence-home`); `state.yaml` records the run and points at the rendered views under `docs/reports/`.
- Handoff outcomes or slash commands. Those are the dev skill's decision table in `02-skill-roster.md`, and naming `/dev` or `$dev` in a story would bind it to one provider.
- Literal build or test commands. See `commands`.
- Summaries of source documents. The context bundle is verbatim excerpts.

## Immutability

At `status: ready` the file is write-once, with two exceptions: `status` is mirrored from `state.yaml` by the sequencer at `phase next`, and `## Clarifications` is append-only. Any other change after `ready` is a stale-hash defect for every consumer that recorded the story's hash, which is the intended effect.

## Version

Template v3 only. The header declares `template_version: 3` and `accepts_versions: [3]`; the gate rejects any other version as a template defect, and `plan` rewrites the instance. No earlier version is accepted, migrated, or warned about, in the template or in any fixture. `01-skill-anatomy.md`'s header example is the same v3 header.

## Open points

1. `gate_policy` defaults should come from the constitution, with the story allowed only to tighten them. Not yet specified.
2. Whether `write_fence` may use globs, and whether test files outside the fence may be read. Recommended: globs allowed, reads unrestricted, writes fenced.

`stack.yaml` is no longer an open point: its contract, including `build` being required when `compiled: true`, is `10-sequencer-and-contracts.md`. `commands.source` resolves against it by anchor and hash.
