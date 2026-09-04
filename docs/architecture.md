# Architecture

[Home](../README.md) / Architecture · [Getting started](getting-started.md) · [Skills](skill-roster.md) · [Evidence](evidence.md)

DevForgeAI separates the workflow an AI follows from the deterministic decisions that accept its work. This page explains the design and reference implementation; it does not claim that all enforcement has been moved into a protected installation.

## From request to accepted changes

**Request → entry gate → bounded workers → independent checks → human handoff.**

The provider adapter routes the request. The sequencer creates the candidate root and sets the phase's authority. Producers edit; judges return findings. The sequencer checks actual changes, runs oracles, persists evidence, and renders the next action for the human.

Failures may block or rewind a run. Code and document candidates require explicit promotion; PR runs finish at `complete_external` without tree promotion. Research uses its own P0–P9 state machine. The exact rules live in [the sequencer contract](design/10-sequencer-and-contracts.md) and [Research workflow](../framework/skills/research/workflow.md).

## Worker context and write authority

| Participant | Owns | Does not own |
| :--- | :--- | :--- |
| Primary agent | Dispatch using the status block; relay receipts and the rendered handoff | Transition decisions, independent acceptance, rewriting worker output |
| Producer | Fenced candidate edits and an in-worker feedback loop using granted stack keys | Tests during green/refactor, canonical control records, promotion |
| Judge | Read inputs; return bounded findings in a receipt | Direct evidence-file writes or a producer's write lease |
| Sequencer | Derive the actual diff, run transition oracles, persist evidence, checkpoint and promote | Human acceptance or authority to publish a protected release |

For a TDD run, red owns the planned test changes; green and refactor own production changes, with the successful red test hashes frozen. A defective test returns to red rather than being weakened during implementation.

Worker transcripts and tool activity stay in their separate contexts. The primary still receives results, including judge findings up to 16 KiB per receipt. Isolation reduces primary-context load; it neither eliminates all context growth nor guarantees correctness. Hash checks, independent oracles, and review supply separate checks on worker claims.

Research is different: its Core is the sole canonical writer, and the four read-only research worker roles are contracts, not implemented provider launches. [Worker contracts →](design/05-subagent-sets.md)

## Candidate roots are not per-worker branches

A framework run shares **one candidate root** across its phases. The reference sequencer uses a Git worktree for a Git project or a scratch copy otherwise. Producers iterate there; later phases inspect that same candidate at the declared checkpoint. There is no primary-agent assembly of code snippets from separate worker folders.

Canonical control state and evidence can change while the run is active. Candidate source changes reach the canonical project through explicit promotion; rendered reports are sequencer-owned outputs. Promotion rechecks the base and change set rather than treating a worker's receipt as proof. Contributor worktrees used to change DevForgeAI itself are a separate layer.

## Hooks and stack commands

The hook reference components use a dispatcher and registered checks. A new check for an already configured event can be added as a module without adding another provider handler. A new event still requires provider configuration and adapter tests. Claude and Codex event/decision protocols are not interchangeable. [Cookbooks and component map →](../components/hook-runtime/README.md)

Stories name keys in `stack.yaml`, not arbitrary shell commands. A worker receives the intersection of its phase's allowed keys and the story's declared keys. The sequencer independently executes transition checks. Python and Node fixtures exercise this explicit selection; they do not implement automatic stack discovery.

## Trust boundary

**DevForgeAI stages candidates. DevForge owns protected enforcement.** The intended boundary covers the sequencer, dispatcher, checkpoint validator, and their authoritative schemas and policy. Human-reviewed promotion, pinned releases, and protected installation are distinct from passing tests in this repository. [Placement decision](design/adr/ADR-0001-research-placement.md) · [trust-boundary plan](research/spec-driven-development-gap-closure/README.md) · [promotion declaration](../framework/contracts/PROMOTION-CANDIDATE.md)

Today, the sequencer/dispatcher are runnable Python reference files and the Research Core/checkpoint validator are staging components. A project-local hook or worktree does not make those files tamper-proof, and the reference scripts are not an OS sandbox. Root ownership and installation claims require their own evidence. The [CP-00 record](research/spec-driven-development-gap-closure/checkpoints/CP-00.yaml) remains open; its current candidate is not promotion-eligible.

The Python implementation and Node demo do not prescribe the final DevForge implementation language or require every target application to use those languages. A Rust port is not evidence of current Rust support; language-neutral behavior must be demonstrated by the applicable conformance cases.

## Source map

| Path | Purpose |
| :--- | :--- |
| [`framework/skills/`](../framework/skills/) | Provider-neutral Research and PR capability/workflow sources |
| [`providers/`](../providers/) | Provider adapter and worker-profile sources |
| [`docs/design/specs/`](design/specs/) | The 19 skill specifications |
| [`docs/design/examples/hooks/`](design/examples/hooks/) | Runnable sequencer, dispatcher, policy, and fixtures |
| [`components/hook-runtime/`](../components/hook-runtime/) | Separate Claude and Codex hook reference implementations |
| [`components/research-core/`](../components/research-core/) | Python Research Core and checkpoint-validation staging package |
| [`schemas/`](../schemas/) and [`framework/contracts/`](../framework/contracts/) | Machine-readable contracts and promotion candidates |
| [`tests/research/`](../tests/research/) | Offline Core, custody, CLI, and packaging tests |

**You are here:** enforcement design. Next, use [evidence and limits](evidence.md) to distinguish implemented checks from live observations and protected-release acceptance.
