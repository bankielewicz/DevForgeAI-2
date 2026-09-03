# Purpose and Enforcement

Status: draft, 2026-09-02. This document states what DevForgeAI is for and where it stops an agent. It is the positioning that the roster (02), the anatomy (01), and the Research Core were built without.

## 1. Purpose

DevForgeAI is a spec-driven development framework installed into any repository, greenfield or brownfield, that makes AI coding agents (Claude Code and Codex today) do only the work a validated artifact authorises, in the order the pipeline prescribes, with every output traceable to its source. The framework itself is Python, Markdown, YAML and JSON. The project it drives can be any language.

The one-sentence test for every feature: **does this make it harder for an agent to act without a validated reason?** If not, it is not a DevForgeAI feature.

## 2. The problem in concrete terms

"Bull in a china shop" is a set of observed failure modes, not a metaphor. Each one below has evidence in `docs/research/`.

| Failure | Evidence |
|---|---|
| Skips a phase and starts coding from the prompt | BMAD_Openclaw step-skip hole (Codex corpus, `sources/local-repository-corpus.md:101`) |
| Declares done because a file exists or a checkbox is ticked | OpenSpec and checkbox-rewrite completion (`:102,106`) |
| Validator fails but nothing blocks | Validator exiting 1 that does not gate (`:119`); parse errors exiting 0 (`:121`) |
| Gate is prose the model may ignore | Spec Kit's gates are template text; no shipped script checks them (comparison report F3) |
| Advisory hooks fail silently | `:108`; fail-open backends `:110` |
| Invents requirements or scope | Codex corpus on hallucinated requirements; 59.4% of audited SWE-bench Verified tasks flawed (`sources/assurance-and-agent-reliability.md:184-187`) |
| Multi-agent fan-out makes it worse, not better | +80.8% to -70% across 260 configurations (`:14-17`) |
| Writes artifacts it was never asked for | Spec Kit converge's `unrequested` gap class exists because this happens (F1) |

## 3. What the competition does about it

| Framework | Gate type | Can the agent bypass it? |
|---|---|---|
| GitHub Spec Kit v1.0.3 | Constitution and checklists as LLM-facing text | Yes. Only prerequisite scripts and a human approve/reject step are executable (F3) |
| Amazon Kiro (2026-08) | Human approval between requirements, design, tasks | Yes, by selecting Quick Spec (F6) |
| BMAD v6.11.0 | PASS/CONCERNS/FAIL readiness gate inside a skill | Yes. The gate is a model verdict; no lifecycle-event enforcement layer (Codex corpus `:166-170`) |
| OpenSpec v1.11.0 | `openspec validate` CLI, no phase gates | Only if wired into pre-commit; otherwise advisory (F5) |
| All of the above | Hooks | None ships a hook set for Claude Code or Codex that denies tool calls outside the workflow |

Nobody enforces at the tool-call level, and nobody enforces at the repository level as part of the framework. That is the gap.

## 4. The enforcement ladder

Four rungs. Each higher rung is harder to bypass and blinder to intent. DevForgeAI must occupy all four, because each has a hole the next one covers.

### Rung 1: Guidance

`CLAUDE.md`, `AGENTS.md`, skill bodies, subagent prompts. Model instructions. The agent can ignore them.

**DevForgeAI refuses nothing here.** Guidance carries orientation and the exact commands to run, never policy. (Codex corpus `provider-adapters.md`, "Guidance files versus canonical truth".)

### Rung 2: Deterministic validators inside the pipeline

The Gate sub-phase (01), template headers, provenance hashes, `check_story.py` as a library the sequencer imports, Research Core's 25 pre-seal checks. Scripts with exit codes, no model judgement. The gate is not a subagent: it is inlined in `devforgeai phase start`, so the model cannot open a phase without running it. Residual hole: the model still chooses when to call `phase start`, which is why the same library runs again at rung 3 and rung 4.

**Refusals at this rung:** a skill will not start Work on an artifact that fails its producer's template, has a stale or placeholder hash, or carries an unresolved ASSUMPTION. A Research run will not seal with an unmet check. Every refusal returns a handoff with `next` populated.

Status: designed, partly implemented (Research Core), and broken in one place: the sealed file set is not closed (review, section 3.1).

### Rung 3: Provider hooks

Verified capabilities, 2026-09-02:

| | Claude Code | Codex |
|---|---|---|
| Can deny a tool call before it runs | Yes. `PreToolUse` with `permissionDecision: deny` or exit code 2; matcher on tool name and argument filter (`Bash(git *)`) | Yes for supported local calls. `PreToolUse` can block or rewrite; hosted tool paths are documented exceptions |
| Fires inside subagents | Yes, for their tool calls; `SubagentStart` cannot block the spawn | Lifecycle hooks include subagents; coverage exceptions apply |
| Tool events identify the calling subagent | Provider adapter must fail closed when identity is absent | No in the documented Pre/PostToolUse fields; `agent_id` and `agent_type` are documented on SubagentStart/Stop |
| Can prevent the agent stopping early | Yes. `Stop` with `decision: block` | Stop event documented; blocking protocol per event |
| Can undo a completed action | No | No |
| Runs prompt or agent handlers | Yes, model judgement, experimental | Parsed but skipped; only command and MCP-tool handlers run |
| User can switch hooks off | Yes. `disableAllHooks: true` at any settings level | Non-managed hooks need review and trust bound to the definition hash; `--dangerously-bypass-hook-trust` exists |
| Failure mode | Errors, timeouts, invalid output are non-blocking | Unsupported output fields fail the hook while the call proceeds; MCP handler errors do not block |

Sources: Claude Code hooks reference and guide (code.claude.com/docs/en/hooks, hooks-guide); OpenAI Codex Hooks, Configuration Reference, and Subagents documentation read directly on 2026-09-02; prior Codex corpus note `sources/codex.md` CDX-05.

**Refusals at this rung:** the candidate root is the fence. Deny Write and Edit whose canonical path is outside the run's candidate root, and deny them inside the root when the path is outside the current phase's write fence. Deny every write from the primary window. Deny a raw stack command, a package manager, and a network tool to every actor; admit `devforgeai run <key>` only to the producer that holds the run's lease and only for a key the phase granted. Admit read-only git subcommands (`status`, `diff`, `log`, `show`, `ls-files`, `blame`) inside the root and deny every mutating one. Deny workflow writes when no run is active. Block Stop while the handoff envelope is missing. Claude binds the lease at `SubagentStart`, the only identity-bearing pre-write event, and compares `agent_id` at `PreToolUse`. Codex tool events do not expose a stable subagent actor, so its route fences by path alone — a write is admitted only under the candidate root and inside the fence — and it ingests the typed receipt at identity-bearing SubagentStop; see `09-hook-dispatcher.md`.

Hole: project hooks are user-disableable, infrastructure failures do not form a hard deny, and specialized/hosted paths can bypass tool hooks. None of the three is closed at this rung; the disable escape is covered by rung 4, and the deferred administrator-managed alternative is `12-post-mvp.md#pm-03`. An OS-level write boundary is `12-post-mvp.md#pm-04`. Hooks are adapters for rung 2, not an OS boundary of their own.

Status: runnable draft in `09-hook-dispatcher.md`; every local conformance row holds. It is not installed or accepted. Its `stack.yaml` contract is `10-sequencer-and-contracts.md`.

### Rung 4: Repository enforcement

Git pre-commit, GitHub rulesets with required status checks, CODEOWNERS on `docs/` and `.devforgeai/`. Provider-independent and the only rung the agent cannot switch off, because it runs where the agent has no settings file.

**Refusals at this rung:** a commit that touches code without a story in `dev_done` or later; a PR whose `state.yaml` chain does not validate; a merge without the clean-checkout chain check green; any edit to a sealed Research dossier.

Status: external and unimplemented. Rung 4 runs where the agent has no settings file, which is also where a Max-plan terminal cannot reach: it needs a CI entry point, a pre-commit hook, branch-protection settings, and a clean-checkout chain validator distinct from the active-story `devforgeai validate`. Its implementation entry is `12-post-mvp.md#pm-10`. Rung 4 stays named here because the ladder is incomplete without it and because the holes at rungs 2 and 3 are only closed by it. GitHub rulesets and required checks were outside the deep-research scope.

## 5. What this changes in the current design

1. **The Gate sub-phase is no longer a subagent.** It is deterministic and inlined in `devforgeai phase start` (rung 2 run by rung 2), re-run as a `PreToolUse` hook check, and re-run by the rung-4 clean-checkout validator. No agent performs template or provenance checking; `check_story.py` is a library the sequencer imports.
2. **`stack.yaml` becomes an enforcement input, not only a convenience.** Rung 3 cannot allow-list build and test commands it does not know. Its contract is `10-sequencer-and-contracts.md`; `architect`'s techstack-writer emits the INTENDED copy, `onboard`'s code-mapper the OBSERVED copy, and `build` is required when `compiled: true`.
3. **The run file becomes the hook's source of truth.** A hook walks up from cwd to the nearest `.devforgeai/`: if it holds `run.yaml`, cwd is inside a candidate root and that file carries the phase, the fence, the granted keys and the lease; otherwise cwd is canonical and `state.yaml#runs` names the active run. Two markers, one decision. That is the primary-window contract applied to enforcement, and only the sequencer writes either file.
4. **Every gate declares its policy.** `gate_policy` is a defect-to-action map (`BLOCK | REQUIRE_HUMAN | WARN | OFF`) declared per artifact, covering behaviour on timeout and malformed input (Codex corpus CLM-043). It is never a returned status; worker status is the separate closed set in `01-skill-anatomy.md#primary-window-contract`.
5. **Codex parity is bounded.** Codex hooks skip prompt and agent handlers and exempt hosted tools, so any rung 3 refusal must be a command handler, and rung 4 must carry what Codex cannot.

## 6. Decisions, recorded

| Question | Decision |
|---|---|
| Is Research exempt from the anatomy? | Yes. It is specified against `framework/skills/research/`, keeps its own typed status set, and is not governed by the seven sub-phases. Which rungs apply to it is still open; see the review, section 5. |
| Is rung 4 in scope for the first release? | No. It is external and unimplemented; `12-post-mvp.md#pm-10`. Until it lands, every rung 3 refusal is disableable and the design says so rather than claiming otherwise. |
| Which rung 3 refusals are BLOCK versus REQUIRE_HUMAN by default? | The artifact's `gate_policy` map decides per defect class. The story template's defaults are in `templates/story.md`; a story may only tighten them. |
| Does `stack.yaml` come before the dev skills? | Yes. Its contract is written in `10-sequencer-and-contracts.md` before any skill specification is authored. No dev skill is language-specific. |

## 7. Next actions, in order

1. Targeted research: Codex hooks primary source (event list, blocking JSON, subagent coverage) and GitHub rulesets and required checks. Both are unverified from primary sources in this repository.
2. Review and accept or reject the runnable hook dispatcher contract in `09-hook-dispatcher.md`; do not treat local conformance as provider acceptance.
3. Fix the Research Core blockers (review, section 7).
4. Then generate dev, review and QA skills.

Rung 4 wiring is not on this list; it is `12-post-mvp.md#pm-10`.

## 8. Provenance

- `docs/research/sdd-landscape-comparison-2026-09-02.md` (F1, F3, F5, F6, F10, F14), unsealed draft.
- `docs/research/spec-driven-ai-framework-skill-roster/sources/codex.md` CDX-05; `provider-adapters.md` hook section; `sources/local-repository-corpus.md:101-121`; `sources/assurance-and-agent-reliability.md:14-17,184-187`.
- Claude Code hooks docs, fetched 2026-09-02 via the documentation agent; 33 event names, exit code 2 and per-event JSON blocking, `disableAllHooks`, subagent coverage.
- `docs/reviews/2026-09-02-research-core-0.1.0-review.md` sections 3.1 and 5.
