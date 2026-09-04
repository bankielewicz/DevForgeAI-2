# Evidence and limits

[Home](../README.md) / Evidence · [Getting started](getting-started.md) · [Skills](skill-roster.md) · [Architecture](architecture.md)

This is a reading guide to the repository's evidence, not a release certification. The snapshot below describes the source available on **2026-09-04**. Historical results apply to their recorded commits, fixtures, and provider versions; they do not certify every later change.

## What exists, and what it establishes

| Surface | Evidence available | Boundary |
| :--- | :--- | :--- |
| Skill design | [19 specifications](design/specs/) and [design verifier](design/specs/verify.py) | Specification consistency is not installed-skill or live-provider acceptance |
| Research Core | [Offline black-box tests](../tests/research/README.md) and packaged Python source | No trusted provider worker launch, external retrieval execution, or accepted `PROVIDER_AGENT` PASS |
| Sequencer | [Conformance suite and demo](design/examples/hooks/README.md) | Synthetic Python/Node workers; no proof of arbitrary stack detection, compiled-stack support, or all skills end to end |
| Generated `dev` skill on Claude | [Frozen run-5 input inventory](research/spec-driven-development-gap-closure/README.md#21-re-freeze-evidence-and-admission-state) and [check-in history](CHECKPOINT.md) | One Python/worktree fixture; lenient provenance gate; raw proof-project files are external, not bundled in a fresh clone |
| Codex hook runtime | [Live report](research/codex-hook-runtime-live/20260903T142001Z-cli-0.152.1/report.md) and [verification JSON](research/codex-hook-runtime-live/20260903T142001Z-cli-0.152.1/verification.json) | Enumerated Codex CLI 0.152.1 hook probes, not a full DevForgeAI development run |
| PR preparation | [Neutral contract](../framework/skills/pr/capability.md), both adapter sources, and sequencer conformance | Locally implemented packet preparation; no live-provider acceptance claimed and no automatic publication |
| Hosted verification | [Workflow source](../.github/workflows/pr-verify.yml) and [scope contract](design/14-hosted-verification-and-pr.md) | Advisory checks; the required release-candidate files are absent in this snapshot, so that lane must fail |
| Checkpoint custody / CP-00 | [Record](research/spec-driven-development-gap-closure/checkpoints/CP-00.yaml), [dossier](research/sdd-checkpoint-custody/README.md), and staged validator | Open, staged, and not promotion-eligible; no protected-install or closure claim |

## Read live evidence with its qualifications

### Claude development run

The re-frozen plan records run 5 on branch `run5`, base `6bb06b89ce43ec88504122fdf2bf0cd65f19484a`, with the generated build-4 skill. The reported run completed the five phases, persisted both judges' findings, and promoted the candidate.

The same inventory records the limits: `/dev STORY-001 --lenient`, external mutable raw logs, and **Claude Code 2.1.259 as an operator-recorded version** while the session record itself says `unknown`. Its inputs are `AVAILABLE_FOR_ADMISSION`, not a closed CP-01. The re-freeze also records 2.1.260 as not yet re-probed. Do not convert those observations into a current-version compatibility guarantee.

### Codex hook proof

The retained Codex 0.152.1 bundle reports a passing attended observe/enforce gate, receipt continuation limits, and a locally registered extension firing without changing the provider hooks file.

Keep the qualifications attached: the first absolute-header patch was `NOT_EVALUATED` for the intended protected-path reason; the following relative-header probe passed. The optional corrupt-policy supervisor row was `NOT_OBSERVABLE`. PreToolUse rows lacked `tool_use_id`, limiting unique-call correlation. Full details and raw sanitized artifacts are linked from [the report](research/codex-hook-runtime-live/20260903T142001Z-cli-0.152.1/report.md).

## What a green result does not mean

- A local suite pass does not prove live provider behavior.
- A positive live fixture does not prove every hostile case or every skill.
- A well-formed checkpoint record does not authenticate its reviewer or close the checkpoint.
- A GitHub job named `required` does not establish branch protection or human acceptance.
- A digest-pinned staging candidate is not a protected DevForge installation.

The [gap-closure plan](research/spec-driven-development-gap-closure/README.md) tracks `RESEARCHED`, `IMPLEMENTED`, and `PROVEN` separately. Closure requires its specified evidence, independent review, and human decision; an unrun or unavailable check stays unrun or unavailable.

## Remaining work that affects adoption

| Gap | Where it is recorded |
| :--- | :--- |
| Complete installation/update path and provider-asset activation | [Post-MVP register](design/12-post-mvp.md) and [Research nonconformance boundary](../tests/research/README.md) |
| Full workflow conformance on both terminals | [CP-01](research/spec-driven-development-gap-closure/checkpoints/CP-01.yaml) |
| Stack discovery, rather than manually selected fixture sections | [CP-02](research/spec-driven-development-gap-closure/checkpoints/CP-02.yaml) |
| Broader cross-runner normalization | [CP-03](research/spec-driven-development-gap-closure/checkpoints/CP-03.yaml) |
| Concurrent ownership, promotion, crash recovery, and CI parity | [CP-09](research/spec-driven-development-gap-closure/checkpoints/CP-09.yaml) |
| `--fix` narrowing to failed criteria | [Reference sequencer limits](design/examples/hooks/README.md#deliberate-limits) |
| Protected enforcement and CP-00 acceptance | [CP-00](research/spec-driven-development-gap-closure/checkpoints/CP-00.yaml) and [promotion candidate](../framework/contracts/PROMOTION-CANDIDATE.md) |

These are recorded gaps, not promises of delivery dates. The checkpoint plan governs ordering; this navigation page does not authorize implementation, installation, or closure.

## Research and decision trail

Start with the [SDD landscape comparison](research/sdd-landscape-comparison-2026-09-02.md), then the [original research corpus](research/spec-driven-ai-framework-skill-roster/README.md). Use the [gap-closure plan](research/spec-driven-development-gap-closure/README.md) for evidence-admission requirements and the [checkpoint history](CHECKPOINT.md) to locate decisions. Where a checkpoint summarizes a live claim, follow it to the raw evidence and recorded digest before reusing that claim.

**You are here:** readiness review. Next, run the [local evaluation](getting-started.md) or select an open checkpoint with the human owner. Nothing on this page authorizes promotion or protected installation.
