# Skill Specification

A Skill Specification (`SKILL-SPEC-NNN.md`) is the single document from which a skill is generated. `plan` is the sole owner of the skill-spec template: every ordinary project-scoped spec is written by `plan`, consumed by a generator, and validated by `skill-validator`. `architect` writes mandates to `constitution.md#mandates` and nothing more. The author, slug, ID allocation, and collision rule for the cross-cutting Research spec remain unresolved. Its defining property is that a generator with no conversation history can build the selected target candidate from the spec alone.

Files:

| File | Role |
|------|------|
| `templates/skill-spec.md` | The template, with a machine-readable header for the gate. |
| `specs/SKILL-SPEC-001-dev.md` | The filled specification for the `dev` skill (TDD loop absorbed); the eighteen specs under `specs/` are the worked instances of this template. |
| `examples/fixtures/dev-tdd/` | A tiny project and story the example's test cases run against. |
| `templates/story.md` | Story template v3, `accepts_versions: [3]`, which the example's gate and fixtures conform to. |
| `examples/fixtures/dev-tdd/overlays/` | Per-eval fixture overlays (eval 2: unresolved assumption; eval 3: criterion 1 already green). |

## Why a spec instead of an interview

Anthropic's `skill-creator` is built as a conversation: it asks four Capture Intent questions, interviews for edge cases and dependencies, proposes test prompts for sign-off, waits for a human to review eval results, and asks for sign-off on trigger queries. That works in a warm session. It does not work when a skill has to be regenerated months later, by a different person, or by a pipeline. The spec pre-answers authoring questions and pre-approves its prompt sets. It does not waive deterministic validation or the human installation decision.

The spec also carries provenance. Every constitution excerpt and design decision that shaped the skill is listed with a digest. Research provenance identifies the sealed RUN, applicable Source/Evidence/Claim IDs, and manifest digest; a bare research hash is insufficient. This lets `amend` and `drift` detect when a generated skill is stale.

## Section to interview mapping

Each spec section exists because the generator would otherwise stop and ask. Line numbers refer to `skill-creator/SKILL.md`.

| Spec section | skill-creator stage | What it would ask |
|--------------|---------------------|-------------------|
| 0 Generator instructions | :26 "just vibe with me"; :49 harvest from conversation; :143 test prompt sign-off; :165 "one continuous sequence"; :251, :267, :314 human review loop; :370 trigger-set sign-off | Whether to run evals, whether the prompts look right, whether the user is done reviewing |
| 1 Identity | :66 name | Skill identifier |
| 2 Problem and requirements | :51 "What should this skill enable Claude to do?" | Purpose |
| 3 Description | :67 description, "pushy" | When to trigger, what it does |
| 4 Trigger set | :339-358 generate 20 queries | Sign-off on positives and near-misses |
| 5 Use cases | PDF p.8 use case definition | Concrete scenarios |
| 6 Inputs and outputs | :52 "What's the expected output format?"; :58 input/output formats, example files | Formats and examples |
| 7 Procedure | :69 "the rest of the skill" | Body content, steps |
| 8 Bundled resources | :304 bundle repeated scripts; agentskills `using-scripts.mdx` | Scripts, references, assets |
| 9 Gotchas | agentskills `best-practices.mdx:167-185` | Edge cases (:58) |
| 10 Success criteria and test cases | :53-54 "Should we set up test cases?"; :143-161 evals.json | Test prompts and assertions |
| 11 Dependencies | :58 dependencies; :68 compatibility | Tools, MCPs, runtime |
| 12 Targets | not covered by skill-creator | Where it installs, how it degrades |
| 13 Constraints | :86-98 progressive disclosure; :137-139 style | Size and voice |
| 14 Acceptance checks | `scripts/quick_validate.py`; `skills-ref validate` | Nothing asked; enforced |
| 15 Provenance | not covered by skill-creator | DevForgeAI chain |

## Cold-session protocol

1. The spec author fills the template. A draft may record an unknown as an authoring `ASSUMPTION:` with a value. Before status becomes `approved`, `generated`, or `validated`, every authoring assumption must be resolved. A literal `ASSUMPTION:` string used solely in fixture input or an expected test value is test data and is permitted.
2. A person or pipeline opens a fresh session at the repository root and pastes the prompt from section 0:
   ```
   Use the skill-creator skill to build the skill specified in <spec-path>.
   Follow its section 0 exactly. Output directory: <dir>. Eval mode: quick.
   ```
3. skill-creator reads the spec, treats it as harvested conversation history, and:
   - writes `<dir>/<name>/SKILL.md` with the section 3 description verbatim,
   - writes `agents/<role>.md` from the section 7 contracts,
   - writes `scripts/`, `references/`, `assets/` from section 8,
   - in `quick` mode writes `evals/evals.json` from section 10, runs each behavioral fixture once with the skill and without a baseline, grades, and reports,
   - runs the section 14 acceptance checks and includes the output.
4. If any section is ambiguous or any unresolved authoring assumption remains, the generator stops with a `SPEC GAPS` list instead of guessing. The author fixes the spec and re-runs.
5. Treat the generated output as a candidate. A non-Research adapter may install at `.claude/skills/<name>` and/or `.agents/skills/<name>` only after its section 12 release gates pass and a human accepts it. A generated Research adapter remains uninstalled because this repository has no accepted provider controls or worker broker. Share provider-neutral resources, but do not symlink provider adapters whose frontmatter or invocation policies differ.

Eval modes. Only two run in a terminal session:

| Mode | Writes evals/ | Runs prompts | Baseline | Description loop | Session |
|------|---------------|--------------|----------|------------------|---------|
| skip | no | no | no | no | any |
| quick | yes | once per prompt, with skill | none | no | any, including headless |

Quick-mode results are generation feedback: one enabled run per eval, no baseline, no viewer. They are not runtime conformance evidence for any skill, and no spec may gate on such evidence. The deferred contract is `12-post-mvp.md#pm-02`; the deferred interactive `full` mode is `12-post-mvp.md#pm-06`.

## Output shape

The generator produces provider-neutral workflow resources and a provider adapter for each selected target. A portable core directory may be reused only when both target validators accept identical bytes and no target-specific invocation control is required:

```
<name>/
  SKILL.md          # portable core only; a target adapter may require different frontmatter
  agents/           # one prompt file per subagent (skill-creator's own convention)
  scripts/
  references/
  assets/
  evals/evals.json  # quick and full modes only
```

For a non-Research anatomy skill, skill-creator emits one `agents/` file per skill-owned worker and no others, so the generated set matches `05-subagent-sets.md` exactly. It emits no agent file for Gate, Slice, Record or Handoff: those four are sequencer operations, and Slice is written by `devforgeai phase start` into `.devforgeai/work/<run>/context.json`. Research instead uses the worker contracts and Core contract under `capabilities/research/`; current Core does not launch provider workers.

Provider-neutral resources may be packaged for every target. Installation is a separate release action after provider-specific adapters and native agent profiles are compiled and validated; unsupported required isolation fails closed rather than degrading inline. Target-specific invocation fields remain in the provider adapter or its supported target-side policy file, not a shared frontmatter block.

## Known limitations

- skill-creator still asks if the spec has a gap. That is intended: a `SPEC GAPS` list is the correct failure.
- Claude and Codex adapters may target provider-native workers (`.claude/agents/*.md`, `.codex/agents/*.toml`). Isolation is a declaration compiled into the profile; runtime verification of it is `12-post-mvp.md#pm-01`.
- In a headless session the generator must run evals and grading as awaited Agent-tool calls. A first quick-mode run that launched evals as background processes lost them when the top-level turn ended; section 0 now forbids that.
- skill-creator's description optimizer performs its own train/test split. A spec-supplied holdout list is ignored, so the template does not have one.
- `metadata.version` is the generated skill-package version. A Research spec must separately name its exact compatible Research Core version; Core 0.1.0 is the current implementation version.
- The current design assigns every ordinary skill spec to `plan`, but it does not assign the authoring authority, project slug, next `SKILL-SPEC-NNN`, or collision rule for a cross-cutting Research skill spec. Do not create that spec until those decisions are made.
- The demonstrated cold-session generation protocol uses Anthropic's Agent-tool subagents. No Codex-native cold-generation execution and grading protocol has been accepted; Codex generation evidence is `NOT_EVALUATED`.

## Current generation evidence status

`docs/reviews/2026-09-02-research-core-0.1.0-review.md` does not establish a current end-to-end generation path:

| Evidence | Bytes exercised | Status |
|---|---|---|
| Runs 1-3 | earlier specification text; `skip` mode | Structural generation and validator observations only; no behavioral eval |
| Run 4 | earlier specification text; `quick` mode | Ended before grading; the later foreground/awaited rule was not exercised |
| Three direct evals | the run-4 generated `dev-tdd` candidate | Reported results are useful historical observations, but the scratch candidate and grading bytes are absent from this workspace and are `NOT_OBSERVABLE` |
| Current specification through generation and foreground quick grading | current bytes | `NOT_EVALUATED` |

Accordingly, the current-spec joined quick path must not be described as
complete or verified end to end.

## Deferred to DevForgeAI's skill-generator

skill-creator does not write these. The same spec is the input when skill-generator adds them:

- `.claude/agents/<skill>-<role>.md` (copies of `agents/*.md` with Claude-specific tool and model frontmatter)
- provider-specific adapter metadata and compatibility artifacts when a pinned provider actually requires them
- hooks
- `AGENTS.md` section for Codex
- the `skill.yaml` neutral spec described in `04-dual-target.md`

## Where the spec sits in the pipeline

```
architect ──> constitution.md#mandates ──┐
                                         ├──> plan ──> SKILL-SPEC-NNN.md ──> skill-generator / skill-creator ──> <name>/ ──> skill-validator
story.requires_skill ────────────────────┘                                                                                   │
                                                                                                                    pass ────┴──> validated candidate
```

- `plan` writes a spec when a story's `requires_skill` names a skill that does not exist, and when a `constitution.md#mandates` entry needs a skill the project lacks (for example `tdd: required` produces SKILL-SPEC-001).
- `architect` writes the mandate and nothing else. It does not author a spec and does not call skill-generator.
- `skill-generator` gates the spec against `templates/skill-spec.md` before generating.
- `skill-validator` checks the output against section 14 plus the anatomy rules.
- Installation occurs only after the applicable target release gates pass and a human accepts the candidate. The current Research candidate cannot pass that boundary because its provider controls are unavailable.
