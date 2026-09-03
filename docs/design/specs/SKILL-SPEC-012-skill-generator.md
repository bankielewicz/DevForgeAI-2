---
# == instance frontmatter ==
template: skill-spec
template_version: 1
id: SKILL-SPEC-012
skill_name: skill-generator
target: both
status: approved
author: "DevForgeAI plan skill"
date: 2026-09-02
depends_on:
  - source: docs/design/04-dual-target.md#neutral-skill-spec
    hash: sha256:aca8c8d49d77a22b9905650f9d65f62d1458338e95ba1425024301d82d3047c5
    excerpt: "Lives in `.devforgeai/skills/<name>/skill.yaml`."
  - source: docs/design/04-dual-target.md#compiled-layouts
    hash: sha256:56e0e577fd32297a28ba3c1257ada03d487e3dfbb554e8912c45e11376180608
    excerpt: "portable `SKILL.md` frontmatter is exactly the six open-standard fields (`name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`), because the standard's validator rejects unknown keys."
  - source: docs/design/04-dual-target.md#validation
    hash: sha256:f9f32d90e5f6f84ca928790da8cba4e1e3bdeb0be7a12f94aeee8f29508585ed
    excerpt: "skill-validator runs after every compile and checks:"
  - source: docs/design/06-skill-specification.md#deferred-to-devforgeai-s-skill-generator
    hash: sha256:7c73717a4098a383d070bd0b2897276f3700ffc269045018efa5ab9800c0fdaa
    excerpt: "skill-creator does not write these. The same spec is the input when skill-generator adds them:"
  - source: docs/design/06-skill-specification.md#cold-session-protocol
    hash: sha256:ab73600267ef7b6721cf5c7599e7432f096b116b2b5aac12405ac933f9c17576
    excerpt: "If any section is ambiguous or any unresolved authoring assumption remains, the generator stops with a `SPEC GAPS` list instead of guessing. The author fixes the spec and re-runs."
  - source: docs/design/10-sequencer-and-contracts.md#4-per-skill-phase-registry
    hash: sha256:37b51ea5748164510e7687527aeab55bc92af9524ee771b293989640cecf8cce
    excerpt: "| skill-generator | document | `.devforgeai/skills/<arg>/**` | 6 |"
  - source: docs/design/10-sequencer-and-contracts.md#5-2-validation-order
    hash: sha256:9f1bf77b7e84302ff6f3f20260228d57390cc97ab8e8d3f68f52c3ff2658aab8
    excerpt: "It is `.devforgeai/state.yaml`, `.devforgeai/stack.yaml`, `.devforgeai/work/**`, `.devforgeai/provenance/**`, `.devforgeai/sessions/**`, `.devforgeai/hooks/**`, `.devforgeai/research-cas/**`, `.claude/**`, `.codex/**`, `.agents/**`, `.git/**`, `CLAUDE.md`, `AGENTS.md`."
  - source: docs/design/10-sequencer-and-contracts.md#9-enforcement-block
    hash: sha256:4aa0d2e9acd265d11271008b3e5e748bbf34c4b2b9e5c624ad8dc8d6d9cebb02
    excerpt: "`skill-generator`'s fence `.devforgeai/skills/<arg>/**` is checkpointed and rewound like any other path; **the \"no rewind promise for `skill-generator`\" caveat is withdrawn**"
  - source: docs/design/10-sequencer-and-contracts.md#11-per-skill-evidence-and-gate-table
    hash: sha256:f5dc9ad016c382d9d033b25878267bd8e1ef240cb0ecaafeff33af16637e906e
    excerpt: "Every skill specification fills this table in its section 7, one row per phase, in phase order:"
  - source: docs/design/11-artifact-registry.md#1-template-registry
    hash: sha256:25886acb1c2963b15938f0c577c3bfd28b9807dd2dd961c59ff2b43fa00b62e2
    excerpt: "| `skill-yaml` | `.devforgeai/skills/skill-generator/templates/skill.yaml` | 1 | `^[a-z][a-z0-9-]*$` | name, version, target, handoff, workers | not a Markdown artifact; the neutral skill definition |"
  - source: docs/design/11-artifact-registry.md#2-artifact-path-patterns
    hash: sha256:2d2e97afff50edf6b35bf674b1de217c684d5091361e5f1deae12de52b95fb51
    excerpt: "| `.devforgeai/skills/<name>/skill.yaml` | `skill-yaml` | skill-generator | sequencer |"
  - source: docs/design/10-sequencer-and-contracts.md#6-handoff-envelope
    hash: sha256:de637edceb588df104a40b57738eb263989f6603f90ece6f4d0e64fef07ffb6a
    excerpt: "| 1 | `next` is never empty and is never a description. One exact command. |"
  - source: docs/design/02-skill-roster.md#handoff-decision-tables
    hash: sha256:6edc7499ee163453f3be6390b0dda08b3fab885f1399ff944056040596ec3801
    excerpt: "| skill-generator | pass | `/skill-validate {skill}`, then the command that requested the generation. The generator's run is closed first; nothing is auto-run inside it |"
  - source: docs/design/05-subagent-sets.md#sets-per-skill
    hash: sha256:9e12f3beb236a025c18d40e741c09ba675bd71d2d87f56e2b205c7556b944bf9
    excerpt: "| skill-generator | spec-reader, skill-yaml-writer, subagent-writer, template-writer, claude-compiler, codex-compiler |"
  - source: docs/design/01-skill-anatomy.md#primary-window-contract
    hash: sha256:de7d775e46bd44c52089a3998b114a5ebb5ce6875be3ebf3dca126f5a9bbaa32
    excerpt: "Model-callable CLI, closed set. Anything else is hook-only and is denied in the Bash allowlist:"
---

# Skill Specification: skill-generator

A stranger with no conversation history must be able to build this skill from this document alone. Every question the generator would otherwise ask is answered below. This document contains no unresolved authoring assumption.

The `depends_on` digests are computed with the hash rule in `docs/design/01-skill-anatomy.md` (resolve the named heading through the next heading of the same or higher level, normalise CRLF to LF without trimming, join with LF, append one LF, and SHA-256 the UTF-8 bytes) and verified by `docs/design/specs/verify.py --only v3`; a source edit after this date makes V3 fail until the digest is recomputed.

## 0. Generator instructions

These instructions are addressed to the skill-generating agent (Anthropic's `skill-creator` skill, or a running DevForgeAI `skill-generator`). They replace its interview.

### Cold-session prompt

Paste this into a fresh session from the repository root:

```
Use the skill-creator skill to build the skill specified in docs/design/specs/SKILL-SPEC-012-skill-generator.md.
Follow its section 0 exactly. Output directory: ./out. Eval mode: quick.
```

### Rules for the generator

1. **Do not interview.** Sections 1-13 pre-answer every Capture Intent and Interview question. Treat this document as the conversation history you are told to harvest from.
2. **Test prompts are pre-approved.** Use section 10 verbatim as `evals/evals.json`. Do not ask whether they look right.
3. **Trigger queries are pre-approved.** Use section 4 verbatim as the trigger eval set. Do not ask for sign-off.
4. **No human review loop.** Do not wait for the user to review results. Proceed to the next stage on your own.
5. **Eval mode** is given in the prompt and is one of two values. `skip`: write the skill only; create no `evals/`, run no prompt, run no description optimisation. `quick`: write the skill and `evals/evals.json`, run each test prompt once with the skill and no baseline, grade with the grader agent, write `grading.json`, and report pass or fail per expectation in the final message. Run the eval executions and the grader as foreground Agent-tool subagents, never as background shell processes, and do not end the turn until every `grading.json` exists. Any other mode name is a spec defect; the deferred interactive mode is `12-post-mvp.md#pm-06`.
6. **Output location** is given in the prompt. Create `./out/skill-generator/`. Write nowhere else except the `skill-generator-workspace/` sibling that eval runs require.
7. **On ambiguity, stop before output.** If this spec is `draft`, contains an unresolved authoring assumption, omits a section, contradicts itself, or leaves a decision this document does not make, do not guess and do not write candidate skill files. End with a list titled `SPEC GAPS` naming each section and question.
8. **Fidelity over creativity.** Use the description in section 3 verbatim. Use the six worker contracts in section 7 verbatim as the bodies of `agents/<role>.md`, adding only the Role / Inputs / Process / Output framing the grader agent uses. Do not add steps, tools, or behaviours this document does not mention.
9. **Finish with the acceptance checks** in section 14 and include their output in the final message.

## 1. Identity

| Field | Value |
|-------|-------|
| name | `skill-generator` (kebab-case, 15 chars, equals the directory name, no provider prefix) |
| title | Skill Generator |
| purpose | Compile one approved skill specification into the neutral skill package and both staged provider adapter candidates, so a skill can be rebuilt from its specification alone with no conversation history. |
| category | devforgeai-phase |
| version | 1.0.0 (skill-package version written to `metadata.version`) |
| license | MIT (frontmatter `license: MIT`) |

## 2. Problem and requirements

**Without this skill:** a skill specification is turned into files by hand or by an interview-driven authoring agent. The result differs on every run: worker prompts drift from the specification's contracts, the Claude adapter and the Codex adapter diverge in ways nobody recorded, provider-specific frontmatter keys leak into the portable file and the open-standard validator rejects it, and no artifact records which specification a compiled skill came from. `amend` and `drift` then cannot tell a stale generated skill from a current one, because nothing links the two.

| ID | Kind | Requirement |
|----|------|-------------|
| R1 | explicit | Take one skill name, resolve its `SKILL-SPEC-NNN.md`, and refuse to generate anything from a specification that is not `approved`, is missing a required section, or whose worker contracts violate the anatomy rules. |
| R2 | explicit | Produce the neutral package under `.devforgeai/skills/<name>/`: `skill.yaml`, `SKILL.md`, `subagents/<role>.md`, `commands/<command>.md`, `templates/`, `references/`, `scripts/`, `assets/`. |
| R3 | explicit | Produce a staged Claude adapter and a staged Codex adapter, each with the frontmatter, worker profile format, and invocation policy its target requires. |
| R4 | implicit | The portable `SKILL.md` frontmatter is exactly the six open-standard fields, because the open-standard validator rejects unknown keys. Provider-specific keys exist only in the Claude adapter. |
| R5 | implicit | Every generated worker declares `writes: candidate`, `writes: evidence` or `writes: none`, consistent with its phase's registry `writes` mode, carries `must_not`, and returns one `devforgeai.worker-result/v1` receipt. |
| R6 | implicit | Every generated file records the specification it came from, so staleness is detectable. |
| R7 | discovered | The provider directories `.claude/**`, `.codex/**` and `.agents/**` are in `ALWAYS_DENY` (`10-sequencer-and-contracts.md#5-2-validation-order`). A compile phase therefore stages its adapter inside the fence; installation is not a generation outcome. |
| R8 | discovered | The fence `.devforgeai/skills/<arg>/**` is checkpointed and rewound like any other path in the candidate root, and `10-sequencer-and-contracts.md#9-enforcement-block` withdraws the earlier "no rewind promise for `skill-generator`" caveat. A failed phase therefore leaves the previous generated files exactly as the last checkpoint had them. Every phase still writes complete files rather than patching, so a re-run overwrites what it owns. |

## 3. Description

```yaml
description: >
  Compiles one approved DevForgeAI skill specification into a runnable skill package: the
  neutral skill.yaml, SKILL.md, worker prompts, templates, references and scripts,
  plus a staged Claude adapter and a staged Codex adapter. Use this skill whenever a story
  declares requires_skill naming a skill that does not exist, whenever plan reports that it
  wrote a skill spec, whenever a constitution mandate needs a skill the project lacks, or
  when the user says skill-gen, generate the skill, build the skill from the spec, compile
  this skill for Claude and Codex, or regenerate the skill after a validation report. It
  resolves the spec, refuses one that has gaps, and never installs what it compiles. Do NOT
  use it to write or amend a skill specification (use plan), to check a compiled skill (use
  skill-validator), or to install adapters into provider directories.
```

Character count: 869 / 1024, measured on the folded scalar with its trailing newline stripped. No angle brackets. Written as a YAML block scalar so colons are safe.

## 4. Trigger set

```json
[
  {"query": "/skill-gen dev-tdd", "should_trigger": true},
  {"query": "plan just wrote docs/plan/shop/skill-specs/SKILL-SPEC-004.md, build the skill from it", "should_trigger": true},
  {"query": "STORY-011 says requires_skill: report-writer and that skill doesnt exist yet, can you generate it", "should_trigger": true},
  {"query": "the constitution mandates tdd so we need the dev-tdd variant compiled for both claude and codex", "should_trigger": true},
  {"query": "compile the skill spec into .devforgeai/skills and stage the codex agent profiles too", "should_trigger": true},
  {"query": "skill-validate came back with three fixes, rerun skill-gen with --fix please", "should_trigger": true},
  {"query": "turn SKILL-SPEC-007 into an actual skill folder with the worker prompts and templates", "should_trigger": true},
  {"query": "we need the toolsmith step: spec in, skill out, dont install it anywhere", "should_trigger": true},
  {"query": "regenerate the analyze skill from its spec, the worker contracts changed", "should_trigger": true},
  {"query": "write a skill spec for a changelog skill with 3 workers and acceptance criteria", "should_trigger": false},
  {"query": "check whether .devforgeai/skills/qa matches its spec and the provider rules", "should_trigger": false},
  {"query": "install the compiled skills into .claude/skills and wire up the hooks", "should_trigger": false},
  {"query": "what does the skill-spec template header require in frontmatter again", "should_trigger": false},
  {"query": "implement STORY-004 with tests first, the constitution says tdd is required", "should_trigger": false},
  {"query": "explain how progressive disclosure works for SKILL.md and references", "should_trigger": false},
  {"query": "our .claude/agents/red_dev.md has the wrong tools line, fix it directly", "should_trigger": false},
  {"query": "split EPIC-002 into stories and order them into sprint-003", "should_trigger": false},
  {"query": "generate a report of which skills are stale compared to the architecture docs", "should_trigger": false}
]
```

## 5. Use cases

### UC-1: Plan ordered a skill before a dependent story
- **User says:** "/skill-gen report-writer"
- **Steps:** 1. `devforgeai phase start skill-generator report-writer` opens the document run and pins the fence `.devforgeai/skills/report-writer/**`. 2. `spec_reader` resolves the single spec whose `skill_name` is `report-writer`, checks it against the skill-spec template header and the anatomy preconditions, and returns the resolved path and an inventory in `evidence`. 3. `skill_yaml_writer`, `subagent_writer` and `template_writer` write the neutral package inside the candidate root. 4. `claude_compiler` and `codex_compiler` write the two staged adapters there. 5. The sequencer records each phase and renders the handoff.
- **Result:** `.devforgeai/skills/report-writer/` holds the neutral package and both staged adapters; the handoff's first next step is `/skill-validate report-writer`.

### UC-2: The specification has gaps
- **User says:** "/skill-gen billing-audit"
- **Steps:** The gate opens the run. `spec_reader` finds the specification is still `draft` and that two worker contracts declare write tools. It returns `status: needs_user` with one `issues` row per gap and an empty `claimed_paths`.
- **Result:** nothing is written under the fence; the handoff lists the gaps as `open_items` and names `/plan billing` as the repair route, then `/skill-gen billing-audit`.

### UC-3: Regeneration after a validation report
- **User says:** "/skill-gen report-writer --fix"
- **Steps:** The primary window passes the validate report path to `spec_reader` alongside the spec path. `spec_reader` returns the report's `## Fixes` rows as `issues` and names the report in `evidence_refs`. The four writing phases and the two compile phases rewrite every file they own, so no partial state survives.
- **Result:** the regenerated package addresses each fix row; the handoff's first next step is `/skill-validate report-writer`.

## 6. Inputs and outputs

### Inputs
| Input | Format | Example file | Required |
|-------|--------|--------------|----------|
| skill name | one argument to `/skill-gen`; substituted into the fence `.devforgeai/skills/<arg>/**` | `skill-validator` | yes |
| skill specification | markdown with frontmatter, `skill-spec` template version 1 | `docs/design/specs/SKILL-SPEC-013-skill-validator.md` | yes |
| `--spec <path>` flag | path; overrides specification resolution | `docs/design/specs/SKILL-SPEC-001-dev.md` | no |
| `--fix` flag | boolean; adds the validate report to `spec_reader`'s inputs | | no |
| validate report | markdown, `validate-report` template version 1, only with `--fix` | `docs/reports/validate-skill-validator.md` | with `--fix` |
| `.devforgeai/state.yaml` | yaml; read by the sequencer, not by the primary window beyond the enforcement block | | yes |

Specification resolution, in order, performed by `spec_reader` and by `scripts/resolve_spec.py`: the `--spec` path when given; otherwise the single file under `docs/plan/*/skill-specs/SKILL-SPEC-*.md` whose frontmatter `skill_name` equals the argument; otherwise the single file under `docs/design/specs/SKILL-SPEC-*.md` whose `skill_name` equals the argument. Zero matches or more than one match is `status: needs_user`, never a guess.

### Outputs

All paths are inside the run's fence `.devforgeai/skills/<name>/**`. `<name>` is the argument; `<role>` is a canonical worker name; `<phase>` is a registry phase name of the generated skill.

| Output | Format | Location | Template |
|--------|--------|----------|----------|
| neutral skill definition | yaml | `.devforgeai/skills/<name>/skill.yaml` | `assets/skill.yaml` |
| neutral skill body | markdown | `.devforgeai/skills/<name>/SKILL.md` | `assets/SKILL.md` |
| entry command | markdown | `.devforgeai/skills/<name>/commands/<command>.md` | `assets/command.md` |
| worker prompts | markdown | `.devforgeai/skills/<name>/subagents/<role>.md` | `assets/agent.md` |
| phase references | markdown | `.devforgeai/skills/<name>/references/<phase>.md`, `references/envelope.md` | inline below |
| generated skill's templates | markdown or yaml with a machine-readable header | `.devforgeai/skills/<name>/templates/` | the header shape in `11-artifact-registry.md#1-template-registry` |
| generated skill's scripts | python | `.devforgeai/skills/<name>/scripts/` | none |
| generated skill's assets | markdown | `.devforgeai/skills/<name>/assets/` | none |
| staged Claude adapter | markdown | `.devforgeai/skills/<name>/compiled/claude/skills/<name>/SKILL.md` and its `references/`, `scripts/`, `assets/`; `compiled/claude/agents/<role>.md` | inline below |
| staged Codex adapter | markdown and toml | `.devforgeai/skills/<name>/compiled/codex/skills/<name>/SKILL.md` and its `references/`, `scripts/`, `assets/`; `compiled/codex/agents/<role>.toml`; `compiled/codex/AGENTS.section.md` | inline below |
| install map, per target | json | `.devforgeai/skills/<name>/compiled/claude/install-map.json`, `compiled/codex/install-map.json` | inline below |

The staged tree mirrors the install destinations in `04-dual-target.md#compiled-layouts` so that installation is a copy and nothing is re-derived at install time. Installation into `.claude/`, `.agents/` and `.codex/` is not performed by this skill and is not performed by any sequencer operation; see section 11.

### Output template: install map
```
{
  "schema": "devforgeai.install-map/v1",
  "skill": "report-writer",
  "target": "claude",
  "selected": true,
  "spec": "docs/plan/shop/skill-specs/SKILL-SPEC-004.md",
  "files": [
    {"from": "compiled/claude/skills/report-writer/SKILL.md", "to": ".claude/skills/report-writer/SKILL.md"},
    {"from": "compiled/claude/agents/report_writer_critic.md", "to": ".claude/agents/report_writer_critic.md"}
  ]
}
```

When the specification's `target` does not select a provider, that compile phase writes exactly one file, its `install-map.json`, marked unselected with an empty copy list, so the `document` oracle still sees a produced file.

### Output template: staged Claude worker profiles

A judge, compiled from a `writes: none` contract:

```
---
name: report_writer_critic
description: Dispatch this worker at the review phase of a report-writer run to judge the written report against the story's acceptance criteria.
tools: Read, Grep, Glob, Bash(devforgeai status)
model: inherit
---

You judge the report this run wrote; you write nothing; finish with the receipt.
<the responsibility and must_not lines from the spec's section 7 contract>
<the envelope paragraph from references/envelope.md>
```

A producer, compiled from a `writes: candidate` contract:

```
---
name: report_writer
description: Dispatch this worker at the report phase of a report-writer run to write the report the story names.
tools: Read, Grep, Glob, Edit, Write, Bash(devforgeai status), Bash(devforgeai run *)
model: inherit
---

You write the report at the path this phase's fence names, inside the candidate root the dispatch block gives as candidate.root, using Edit and Write; run `devforgeai run <key>` whenever you need the tests; finish with the receipt.
<the responsibility and must_not lines from the spec's section 7 contract>
<the envelope paragraph from references/envelope.md>
```

`model` is `inherit` on both, so a worker never selects a model the session is not entitled to. `hooks`, `memory`, `isolation`, `background` and `permissionMode` are Claude-only keys; the compiler emits none of them, and Claude's `isolation` value in particular is never emitted because it forks a worktree from HEAD and would split the run's linear history.

### Output template: staged Codex worker profiles

```
name = "report_writer_critic"
description = "Review-phase critic for the report-writer skill."
sandbox_mode = "read-only"
approval_policy = "never"
developer_instructions = """
You judge the report this run wrote; you write nothing; finish with the receipt.
<the responsibility and must_not lines from the spec's section 7 contract>
<the envelope paragraph from references/envelope.md>
"""
```

```
name = "report_writer"
description = "Report-phase producer for the report-writer skill."
sandbox_mode = "workspace-write"
approval_policy = "never"
developer_instructions = """
You write the report at the path this phase's fence names, inside the candidate root, using apply_patch; run `devforgeai run <key>` whenever you need the tests; finish with the receipt.
<the responsibility and must_not lines from the spec's section 7 contract>
<the envelope paragraph from references/envelope.md>
"""
```

A Codex producer runs with cwd at the candidate root, which is the fence Codex can enforce: its pre-tool event carries no identity, so the root is what bounds the write.

### Output template: staged portable SKILL.md frontmatter
```
---
name: report-writer
description: <the spec's section 3 description, verbatim>
license: MIT
compatibility: <the spec's section 11 compatibility line, omitted when empty>
metadata:
  version: "1.0.0"
  devforgeai-spec: "SKILL-SPEC-004"
  devforgeai-target: "both"
  devforgeai-anatomy: "true"
allowed-tools: <the spec's section 11 allowed-tools line, omitted when empty>
---
```

The Claude adapter's `SKILL.md` carries the same six fields plus the provider-specific keys the spec's section 12 authorises (`argument-hint`, `disable-model-invocation`). The Codex adapter's `SKILL.md` carries the six fields and nothing else.

### Return envelope

One schema, both providers: `devforgeai.worker-result/v1`, normative in `schemas/devforgeai/v1/worker-result.schema.json`. A producer writes its files inside the candidate root with Edit and Write (Codex: `apply_patch`) and names them in `claimed_paths`; a judge writes only its findings file under `.devforgeai/work/<run>/evidence/<agent>/` — run-scoped scratch, gitignored, outside the candidate root and never promoted — and names it in `evidence_refs`, claiming nothing. The receipt is a claim, not a payload. At `devforgeai ingest-result` the sequencer derives `changed[{path, blob_sha256, kind}]` from the candidate root's checkpoint diff, refuses the result when `changed` is not a subset of `claimed_paths` (`UNCLAIMED_CHANGE`) or when any changed path is outside the fence, runs the transition oracle inside the root, writes `<phase>-result.json` with `changed` and the checkpoint ref, creates the next checkpoint and releases the lease.

```yaml
schema: devforgeai.worker-result/v1
run: "skill-generator-report-writer"
skill: "skill-generator"
phase: "skill_yaml"
agent: "skill_yaml_writer"
status: pass | fail | needs_user | could_not_run
reason_code: runner_missing | timeout | network | hook_fault   # required only when status is could_not_run
candidate:
  id: "skill-generator-report-writer"
  input_checkpoint: "read_spec"
claimed_paths: []          # root-relative, at most 64; empty for a judge and for any non-pass status
evidence_refs: []          # at most 16 paths, root-relative or under .devforgeai/work/<run>/
note: "3 lines at most"
issues: [{id, kind, text}] # 10 rows at most
next: ""                   # never used: this skill declares no rewind target
```

Unknown keys are refused. `issues[]` is the bounded summary; a judge's full row set lives in its findings file. A phase that owns more than 64 files splits its claim across the run's phases; section 9 records the bound.

`gate_policy` (`BLOCK | REQUIRE_HUMAN | WARN | OFF`) is a defect-to-action map declared in the consumed artifact, never a status returned here. A document run carries the fixed map `{unresolvable_source: BLOCK}`.

## 7. Procedure

The body of `SKILL.md`. Imperative voice. Bundled files are referenced by relative path.

### Steps

1. Parse the skill name and the `--spec` and `--fix` flags — why: the primary window may parse arguments and nothing else; anything it reads stays in context for the whole run.
2. Call `devforgeai phase start skill-generator <name>`. The sequencer runs the document fence gate, opens the run, and writes the enforcement block. On a non-zero exit, print the sequencer's output and stop — why: the gate, not the model, decides whether a run may open.
3. Dispatch `subagents/spec_reader.md` with the skill name, the `--spec` path when given, and the validate report path when `--fix` is given. Pass paths and ids only — why: pasting specification text into the prompt duplicates it in two windows and makes the worker's own read unverifiable.
4. Dispatch `subagents/skill_yaml_writer.md` with the path of the previous phase's result file, `.devforgeai/work/<run>/read_spec-result.json`, from which it reads the resolved specification path.
5. Dispatch `subagents/subagent_writer.md` with the same result path; the worker roster is in it.
6. Dispatch `subagents/template_writer.md` with the same result path; the template roster is in it.
7. Dispatch `subagents/claude_compiler.md` with the same path.
8. Dispatch `subagents/codex_compiler.md` with the same path.
9. Print the handoff block the sequencer rendered — why: the handoff is a rendering of `handoff.json`, and a block composed in the primary window can state a fact the evidence does not hold.
10. When that block reports the run `ready_to_promote` and the user asks for the promotion, call `devforgeai promote <run>` and print the second block the promotion rendered — why: promotion is never automatic, it is what moves `.devforgeai/skills/<name>/` from the candidate root into the canonical checkout under the lock, and a `REQUIRE_HUMAN` block is the only state in which the model may ask for it.

Between steps the primary window does nothing: the `SubagentStop` hook routes each worker's receipt to the sequencer, which diffs the candidate root against the phase's input checkpoint, checks the derived change set against `claimed_paths` and the fence, runs the transition oracle inside the root, checkpoints it, and advances the phase. The primary window branches only on the status it sees in the receipt, and calls `devforgeai phase fail --reason <text>` when the user abandons the run.

Every phase of one run works inside the same candidate root — `.devforgeai/work/<run>/wt`, created by `devforgeai phase start` and named to each worker as `candidate.root` in the status block the primary window pastes into the dispatch prompt alongside `run`, `phase`, `fence` and `granted_keys`. Five of the six phases are producers and write there with Edit and Write; `read_spec` is a judge, writes nothing in the root, and puts its findings file in `.devforgeai/work/<run>/evidence/spec_reader/`. The sequencer checkpoints the root at each transition, so the phases build linearly with no merge between them, and exactly one producer holds the run's lease at a time, granted at dispatch and released at `devforgeai ingest-result`. Promotion is never automatic and is no part of Handoff: the last passing `devforgeai phase next` marks the run `ready_to_promote` and writes a `REQUIRE_HUMAN` handoff whose only forward step is `devforgeai promote <run>`, and `SKILL.md` runs that command only after the user confirms in the session. That command, not the transition, is what merges the candidate root into the canonical checkout under `.devforgeai/lock`, and it is what refuses with `STALE_BASE` when canonical HEAD has moved past the run's recorded `base_ref`, with `DIRTY_TARGET` when a canonical file among the run's changed paths is dirty, and with `MERGE_CONFLICT` when a rebase inside the root conflicted; a refused promotion leaves the run `ready_to_promote` with its candidate root intact for a retry.

### Sub-phases and workers

Gate, Record, Slice and Handoff dispatch no LLM: they are `devforgeai` sequencer operations. Slice runs inside `devforgeai phase start`, which writes `.devforgeai/work/<run>/context.json` and hands its path to every worker of the run. This skill's registry entry has six phases and therefore no Review phase; see section 9.

| # | Sub-phase | Performed by | Isolation |
|---|-----------|--------------|-----------|
| 0 | Gate | sequencer: `devforgeai phase start skill-generator <name>` | n/a |
| 1 | Slice | sequencer: `devforgeai phase start` writes `.devforgeai/work/<run>/context.json` | n/a |
| 2 | Work: `read_spec` | worker: `spec_reader` | required |
| 3 | Write: `skill_yaml` | worker: `skill_yaml_writer` | required |
| 4 | Write: `subagents` | worker: `subagent_writer` | required |
| 5 | Write: `templates` | worker: `template_writer` | required |
| 6 | Write: `compile_claude` | worker: `claude_compiler` | required |
| 7 | Write: `compile_codex` | worker: `codex_compiler` | required |
| 8 | Record | sequencer: `devforgeai phase next` | n/a |
| 9 | Handoff | sequencer: `devforgeai phase next` marks the run `ready_to_promote` and writes the `REQUIRE_HUMAN` block whose only forward step is `devforgeai promote <run>`; `SKILL.md` runs that command only after the user confirms in the session, and the promotion writes the run's second handoff block | n/a |

Isolation is the framework's own `required | preferred` declaration compiled into the target profile, not Claude's subagent `isolation` key; runtime verification of it is `12-post-mvp.md#pm-01`.

### Worker contracts

Each block is a compilable subagent definition. `name` is the canonical registry worker name, because the stop event's `agent_type` is compared against it. `description` is the sentence the primary window matches when it decides to dispatch. `writes` is `candidate` for a producer and `evidence` for a judge, following the registry's `writes` column: `read_spec` declares `none` there and the other five declare `docs`, so one judge and five producers. `compiled_to` names the two provider-native files the run stages for its own package; the generated skill's own profiles are staged under its `compiled/` tree instead. Each body follows `templates/agent-md.md` in four parts — job, inputs, rules, receipt — and a producer's job sentence leads with what it writes.

```yaml
name: spec_reader
skill: skill-generator
description: Dispatch this worker first in a skill-gen run to resolve the one specification for the argument and judge it against the skill-spec header and the anatomy preconditions, before any phase writes a file.
writes: evidence
tools: [Read, Grep, Glob, Write, Bash(devforgeai status)]
model: inherit
skills: []
responsibility: Resolve the one skill specification for this run's argument, check it against the skill-spec template header and the anatomy preconditions in references/read_spec.md, and return the resolved path plus a bounded inventory; never repair it.
inputs: [.devforgeai/work/<run>/context.json, skill name (the run argument), --spec path (optional), docs/reports/validate-<name>.md (only with --fix)]
outputs:
  - .devforgeai/work/<run>/evidence/spec_reader/inventory.json, the resolved specification path with its full worker, template, script, command, fix and gap inventory
  - issues[]: one SPEC GAPS row per precondition the specification fails, at most ten
  - note: the resolved specification path, its id, its skill_name, its target, and the counts of phases, workers, templates and scripts
  - evidence_refs[]: the inventory file above, the resolved specification path, and the validate report path when --fix is given
must_not:
  - write or claim any path inside the candidate root; this phase's one write is its findings file under .devforgeai/work/<run>/evidence/spec_reader/
  - guess when zero or more than one specification matches the argument
  - accept a specification whose status is not approved
  - accept a worker contract with no responsibility, no must_not, no writes declaration outside candidate, evidence and none, or a tools list wider than its writes declaration allows
isolation: required
returns: devforgeai.worker-result/v1
compiled_to:
  - .claude/agents/skill-generator-spec_reader.md
  - .codex/agents/skill-generator-spec_reader.toml
body: job, inputs, rules, receipt
```

A non-empty gap list is returned with `status: needs_user` and one `issues` row per gap titled `SPEC GAPS`; the later phases read the resolved path and the full inventory from `.devforgeai/work/<run>/read_spec-result.json` and the findings file its `evidence_refs` names.

```yaml
name: skill_yaml_writer
skill: skill-generator
description: Dispatch this worker after read_spec to write the generated skill's neutral definition, body and entry command from the resolved specification.
writes: candidate
tools: [Read, Grep, Glob, Edit, Write, Bash(devforgeai status)]
model: inherit
skills: []
responsibility: Write the neutral skill definition, the neutral SKILL.md body, and the entry command file for the specified skill inside the candidate root, from the specification's sections 1, 3, 7, 11 and 12.
inputs: [.devforgeai/work/<run>/read_spec-result.json, resolved specification path, assets/skill.yaml, assets/SKILL.md, assets/command.md, references/skill_yaml.md]
outputs:
  - .devforgeai/skills/<name>/skill.yaml, SKILL.md and commands/<command>.md, written under the candidate root and named in claimed_paths
  - note: the SKILL.md line count, the subphase count, and the handoff outcome names
must_not:
  - add a subphase, worker, template or handoff outcome the specification does not name
  - place a provider-specific frontmatter key in the neutral SKILL.md
  - exceed 500 lines in the neutral SKILL.md
  - write or claim a path outside the fence .devforgeai/skills/<name>/**
isolation: required
returns: devforgeai.worker-result/v1
compiled_to:
  - .claude/agents/skill-generator-skill_yaml_writer.md
  - .codex/agents/skill-generator-skill_yaml_writer.toml
body: job, inputs, rules, receipt
```

```yaml
name: subagent_writer
skill: skill-generator
description: Dispatch this worker after skill_yaml to write one worker prompt per contract in the specification's section 7, plus one reference file per phase and the envelope reference.
writes: candidate
tools: [Read, Grep, Glob, Edit, Write, Bash(devforgeai status)]
model: inherit
skills: []
responsibility: Write one worker prompt per worker contract in the specification's section 7 inside the candidate root, plus one reference file per phase and the envelope reference.
inputs: [.devforgeai/work/<run>/read_spec-result.json, resolved specification path, assets/agent.md, references/subagents.md, references/envelope.md]
outputs:
  - .devforgeai/skills/<name>/subagents/<role>.md, references/<phase>.md and references/envelope.md, written under the candidate root and named in claimed_paths
  - note: the worker filenames, the reference filenames, and whether persona and critic are distinct files
must_not:
  - write a prompt for a sequencer operation; Gate, Slice, Record and Handoff have no worker
  - omit the must_not block, omit the writes declaration, or give a judge a write tool in any worker prompt
  - open a producer prompt with a sentence about what the worker does not do; the job comes first
  - paraphrase a responsibility or a must_not line instead of carrying it over verbatim
  - link a reference file to anything below one level
  - write or claim a path outside the fence .devforgeai/skills/<name>/**
isolation: required
returns: devforgeai.worker-result/v1
compiled_to:
  - .claude/agents/skill-generator-subagent_writer.md
  - .codex/agents/skill-generator-subagent_writer.toml
body: job, inputs, rules, receipt
```

```yaml
name: template_writer
skill: skill-generator
description: Dispatch this worker after subagents to write the templates the generated skill owns, each with its machine-readable header, plus its bundled scripts and output assets.
writes: candidate
tools: [Read, Grep, Glob, Edit, Write, Bash(devforgeai status)]
model: inherit
skills: []
responsibility: Write the templates the generated skill owns inside the candidate root, each with the machine-readable header the gate reads, plus its bundled scripts and output assets.
inputs: [.devforgeai/work/<run>/read_spec-result.json, resolved specification path, references/templates.md, 11-artifact-registry.md section 1 header shape]
outputs:
  - .devforgeai/skills/<name>/templates/, scripts/ and assets/, written under the candidate root and named in claimed_paths
  - note: the template names and versions, the script names and the asset names
must_not:
  - write a template the specification's section 8 does not list
  - write a template already owned by another skill
  - emit a template header missing template, template_version, accepts_versions, required_frontmatter, required_sections, id_pattern or forbidden_text
  - emit a script that prompts interactively or lacks a help flag
  - write or claim a path outside the fence .devforgeai/skills/<name>/**
isolation: required
returns: devforgeai.worker-result/v1
compiled_to:
  - .claude/agents/skill-generator-template_writer.md
  - .codex/agents/skill-generator-template_writer.toml
body: job, inputs, rules, receipt
```

```yaml
name: claude_compiler
skill: skill-generator
description: Dispatch this worker after templates to write the staged Claude adapter for the generated skill: its SKILL.md, its subagent profiles and its install map.
writes: candidate
tools: [Read, Grep, Glob, Edit, Write, Bash(devforgeai status)]
model: inherit
skills: []
responsibility: Write the staged Claude adapter inside the candidate root: its SKILL.md with the six portable fields plus the provider-specific keys the specification authorises, its subagent profiles, its copied references, scripts and assets, and its install map.
inputs: [.devforgeai/work/<run>/read_spec-result.json, resolved specification path, the neutral package paths the three preceding phases wrote, references/compile_claude.md]
outputs:
  - .devforgeai/skills/<name>/compiled/claude/**, written under the candidate root and named in claimed_paths
  - note: whether the target is selected, the SKILL.md line count, the profile names, the extra frontmatter keys and the install map entry count
must_not:
  - write or claim any path under .claude/, .codex/ or .agents/
  - give a profile compiled from a writes none contract a write tool, give one compiled from a writes evidence contract anything beyond Write, or omit Edit and Write from one compiled from a writes candidate contract
  - emit Claude's isolation, hooks, memory, background or permissionMode key in a profile
  - claim installation, or write an install map entry for a file it did not write
  - write or claim a path outside the fence .devforgeai/skills/<name>/**
isolation: required
returns: devforgeai.worker-result/v1
compiled_to:
  - .claude/agents/skill-generator-claude_compiler.md
  - .codex/agents/skill-generator-claude_compiler.toml
body: job, inputs, rules, receipt
```

```yaml
name: codex_compiler
skill: skill-generator
description: Dispatch this worker last in a skill-gen run to write the staged Codex adapter for the generated skill, its AGENTS.md section text and its install map.
writes: candidate
tools: [Read, Grep, Glob, Edit, Write, Bash(devforgeai status)]
model: inherit
skills: []
responsibility: Write the staged Codex adapter inside the candidate root: its SKILL.md with exactly the six portable fields, its worker profiles in the target's profile format, its copied references, scripts and assets, the AGENTS.md section text, and its install map.
inputs: [.devforgeai/work/<run>/read_spec-result.json, resolved specification path, the neutral package paths the three preceding phases wrote, references/compile_codex.md]
outputs:
  - .devforgeai/skills/<name>/compiled/codex/**, written under the candidate root and named in claimed_paths
  - note: whether the target is selected, the SKILL.md line count, the frontmatter field count, the profile names and the install map entry count
must_not:
  - write or claim any path under .claude/, .codex/ or .agents/
  - place a provider-specific key from the Claude target in this adapter's SKILL.md
  - give a profile compiled from a writes none or writes evidence contract a sandbox mode wider than the directory its declaration admits
  - append to the repository's AGENTS.md instead of writing the section text as a staged file
  - write or claim a path outside the fence .devforgeai/skills/<name>/**
isolation: required
returns: devforgeai.worker-result/v1
compiled_to:
  - .claude/agents/skill-generator-codex_compiler.md
  - .codex/agents/skill-generator-codex_compiler.toml
body: job, inputs, rules, receipt
```

A judge's tools are `Read`, `Grep`, `Glob`, `Write` and `Bash(devforgeai status)`, with `Write` admitted only under `.devforgeai/work/<run>/evidence/<agent>/`. A producer holds `Edit` and `Write` inside the candidate root — `apply_patch` on the Codex target — and `Bash(devforgeai run *)` for the stack keys its phase grants; `skill-generator` grants none, so no worker here carries it. No worker holds a git write, a package manager, a network tool or a raw stack command. `isolation` in the blocks above is the framework's `required | preferred` declaration, not Claude's subagent `isolation` key, which the framework never sets. `hooks`, `memory`, `background` and `permissionMode` are Claude-only keys this skill leaves unset.

### Evidence and gate table

Run id for a document run is `<skill>-<arg>`, so every evidence path below begins `.devforgeai/work/skill-generator-<name>/`. The gate policy for a document run is the fixed map `{unresolvable_source: BLOCK}`; `write_fence_violation` is refused at result validation on every phase and is not configurable. Attempt budget is 2 for every phase. No phase grants a stack command key, and no phase declares `rewind_to`.

| phase | worker | deterministic gate check | gate_policy | evidence file | transition oracle |
|---|---|---|---|---|---|
| `read_spec` | `spec_reader` | run-level gate at `devforgeai phase start`: the fence `.devforgeai/skills/<name>/**` is declared, is relative, contains no parent traversal, and matches no sequencer-owned path; no active or `ready_to_promote` run's fence overlaps it (`FENCE_OVERLAP`); `candidate open` creates the root and pins `base_ref`. At `ingest-result`: the checkpoint diff of the root is empty, because the phase's `writes` mode is `evidence` and the `PreToolUse` check admits this worker's `Write` only under `.devforgeai/work/<run>/evidence/spec_reader/`, which lies outside the root; a non-empty root diff is `UNCLAIMED_CHANGE`. The phase grants no command key | `unresolvable_source: BLOCK` (document run fixed map) | `.devforgeai/work/skill-generator-<name>/read_spec-result.json`, `read_spec-report.md` | `report_only`: no file outside the fence changed since the gate snapshot and the whole-tree package and import policy holds |
| `skill_yaml` | `skill_yaml_writer` | at `ingest-result`: `changed` derived from the checkpoint diff is a subset of `claimed_paths` (`UNCLAIMED_CHANGE` otherwise); every changed path canonicalises inside the candidate root, is inside the fence, is not sequencer-owned, and is allowed by `writes: docs`; the whole-tree package and import rescan holds | `unresolvable_source: BLOCK`; `write_fence_violation: BLOCK` | `.devforgeai/work/skill-generator-<name>/skill_yaml-result.json`, `skill_yaml-report.md` | `document`: the phase declared `writes: docs`, produced at least one file, and every declared output with non-null content exists on disk |
| `subagents` | `subagent_writer` | as `skill_yaml` | `unresolvable_source: BLOCK`; `write_fence_violation: BLOCK` | `.devforgeai/work/skill-generator-<name>/subagents-result.json`, `subagents-report.md` | `document`: as above |
| `templates` | `template_writer` | as `skill_yaml` | `unresolvable_source: BLOCK`; `write_fence_violation: BLOCK` | `.devforgeai/work/skill-generator-<name>/templates-result.json`, `templates-report.md` | `document`: as above |
| `compile_claude` | `claude_compiler` | as `skill_yaml`, and no changed path is under `.claude/`, `.codex/` or `.agents/`; the `PreToolUse` check denies the write itself, and a path that reaches the diff anyway refuses the result as sequencer-owned | `unresolvable_source: BLOCK`; `write_fence_violation: BLOCK` | `.devforgeai/work/skill-generator-<name>/compile_claude-result.json`, `compile_claude-report.md` | `document`: as above |
| `compile_codex` | `codex_compiler` | as `compile_claude` | `unresolvable_source: BLOCK`; `write_fence_violation: BLOCK` | `.devforgeai/work/skill-generator-<name>/compile_codex-result.json`, `compile_codex-report.md`, then `handoff.json` | `document`: as above. On pass this is the last phase, and promotion is not part of it: `devforgeai phase next` marks the run `ready_to_promote` and writes a `REQUIRE_HUMAN` handoff whose only forward step is `devforgeai promote <run>`. `SKILL.md` runs that command only after the user confirms in the session; the promotion moves the package into the canonical checkout under `.devforgeai/lock`, marks the run `promoted`, clears enforcement, and writes the run's second handoff block. `STALE_BASE`, `DIRTY_TARGET` and `MERGE_CONFLICT` refuse `devforgeai promote <run>`, never `devforgeai phase next`, and leave the run `ready_to_promote` with its candidate root intact for a retry |

### Handoff outcomes

This is the decision table the skill declares as `handoff.outcomes` in `.devforgeai/skills/skill-generator/skill.yaml`, and it is the contract. The current sequencer does not read it: for a document run it writes `devforgeai promote <run>` on the ready block that the last passing transition produces and `/status` on the promoted block, `/status` on a `REQUIRE_HUMAN` block, the runner repair followed by `/skill-gen <name>` on a `COULD_NOT_RUN` block, and `/skill-gen <name> --fix` on a `BLOCK`, `WARN` or `OFF` block, `BLOCK` being what `devforgeai phase fail --reason` records. Both are recorded; the rows below are not what a run prints today. See section 9.

| Outcome | Next steps |
|---------|------------|
| pass, every phase passed, run `ready_to_promote` and not yet promoted | `devforgeai promote {run}` — the first of the run's two handoff blocks; `SKILL.md` runs the command only after the user confirms in the session, and the promotion writes the second block |
| pass, promoted | `/skill-validate {skill}` |
| `needs_user` from `read_spec`, gaps listed | 1. `/plan {slug} --retry` with the `SPEC GAPS` rows; 2. `/skill-gen {skill}`, which resumes the blocked run at `run.yaml#blocked_at` with attempts reset — the run stayed `active` and kept its candidate root |
| `needs_user` from `read_spec`, zero or several specifications match | 1. `/skill-gen {skill}` with an explicit `--spec` path, which resumes the blocked run at `blocked_at`. Also possible: `devforgeai phase fail --reason <text>` to abandon the root, then `/status` |
| `fail` at the attempt limit on any phase | 1. `/skill-gen {skill}` after the `open_items` defects are fixed, which resumes the blocked run at `blocked_at` with attempts reset. Also possible: `devforgeai phase fail --reason <text>` to abandon the root, then `/status` |
| `could_not_run`, any `reason_code` | 1. the repair route the `reason_code` names; 2. `/skill-gen {skill}` |
| missing worker identity on the stop event (synthesised `could_not_run`, `hook_fault`) | 1. `/status`; 2. `/skill-gen {skill}` |
| `devforgeai phase fail --reason` recorded by the user | `/status` |

Also possible, on every row: `/status`.

## 8. Bundled resources

### Layout (fixed)

```
skill-generator/SKILL.md    # <=500 lines: identity, phase list, dispatch loop, handoff table
  references/read_spec.md
  references/skill_yaml.md
  references/subagents.md
  references/templates.md
  references/compile_claude.md
  references/compile_codex.md
  references/envelope.md
  agents/spec_reader.md
  agents/skill_yaml_writer.md
  agents/subagent_writer.md
  agents/template_writer.md
  agents/claude_compiler.md
  agents/codex_compiler.md
  scripts/check_spec.py
  scripts/resolve_spec.py
  assets/skill.yaml
  assets/SKILL.md
  assets/agent.md
  assets/command.md
```

`SKILL.md` links to `references/`, `agents/`, `scripts/` and `assets/`; an `agents/*.md` links to `references/*.md`; nothing links further. Guidance a phase needs lives in that phase's reference file, not in `SKILL.md` and not duplicated across files.

The portable package names the worker prompt directory `agents/`, which is the fixed layout's name and the open-standard convention. The registry addresses the same files at `.devforgeai/skills/<name>/subagents/<role>.md` (`11-artifact-registry.md#2-artifact-path-patterns`), which is the path this skill's outputs in section 6 use and the path its own dispatch steps reference. The install map is the only place the two names are related, exactly as it is for `assets/` and `templates/`.

### scripts/
| File | Purpose | Invocation | Exit codes |
|------|---------|------------|------------|
| `check_spec.py` | Deterministic check of one skill specification against the `skill-spec` template header (frontmatter key set, id pattern, the 16 required sections in order, forbidden placeholder strings from the template header, `status: approved`, no unresolved authoring assumption) plus the anatomy preconditions in `references/read_spec.md`: every section 7 worker contract has `responsibility`, `must_not`, `tools` no wider than read, and a canonical worker name; every phase named has a reference file row in section 8; the section 3 description is at most 1024 characters and has no angle bracket; section 12 names only supported targets; section 0 names only the eval modes `skip` and `quick`; section 7 names no worker for Gate, Record or Handoff; the return envelope named is `devforgeai.worker-result/v1`. Prints one JSON object with `ok`, `gaps` and `inventory`. | `python scripts/check_spec.py <spec-path> [--json]` | 0 ok, 1 gaps listed on stdout, 2 usage |
| `resolve_spec.py` | Resolve one skill name to exactly one specification path using the order in section 6, and print the match as JSON with the search roots it used. | `python scripts/resolve_spec.py <skill-name> [--spec <path>]` | 0 exactly one match, 1 zero or several matches, 2 usage |

Both scripts are non-interactive, take arguments and never prompt, print data to stdout and diagnostics to stderr, and document a help flag. Neither is executed by a worker: no `skill-generator` phase grants a stack command key, so no worker holds `Bash(devforgeai run *)`, and the brokered surface is hook-only in any case. The scripts are the reference implementation of the rules the workers apply by reading, they are run by a human in section 14, and they are the sibling of `check_story.py` that the sequencer's gate library imports when the provenance half of the gate described in `01-skill-anatomy.md` is implemented. See section 9.

### references/
| File | Content | Load when |
|------|---------|-----------|
| `read_spec.md` | The specification resolution order; the skill-spec header rules; the enumerated anatomy preconditions a specification must satisfy before generation, including the two supported eval modes, the rule that a contract's tools match its `writes` declaration, the canonical worker names, and the ban on a worker for Gate, Slice, Record or Handoff; the `SPEC GAPS` row format, in which every row cites the rule it came from. | dispatching `spec_reader` |
| `skill_yaml.md` | The neutral `skill.yaml` field set and the neutral `SKILL.md` body shape: identity, phase list, dispatch loop, handoff table, and nothing else. | dispatching `skill_yaml_writer` |
| `subagents.md` | The worker prompt shape and its four body parts (job, inputs, rules, receipt); why `must_not` is carried verbatim; why Gate, Slice, Record and Handoff get no file; why persona and critic must be different files; how a `writes` declaration of `candidate`, `evidence` or `none` selects the profile's tool list and the directory its Write reaches, and why a producer prompt opens with the job rather than with a prohibition. | dispatching `subagent_writer` |
| `templates.md` | The machine-readable template header keys and how a template version is written into the artifacts it produces. | dispatching `template_writer` |
| `compile_claude.md` | The Claude adapter layout, the six portable fields, the provider-specific keys allowed in this target only, the subagent frontmatter field set (`name`, `description`, `tools`, `model`), and the Claude-only keys the compiler never emits. | dispatching `claude_compiler` |
| `compile_codex.md` | The Codex adapter layout, the six-field rule, the worker profile field set with its sandbox mode per `writes` declaration, and the AGENTS.md section shape. | dispatching `codex_compiler` |
| `envelope.md` | The `devforgeai.worker-result/v1` schema with a pass, a fail, a needs_user and a could_not_run example. | every dispatch |

### assets/
| File | Used for |
|------|----------|
| `skill.yaml` | seeds `.devforgeai/skills/<name>/skill.yaml`; the `skill-yaml` template of `11-artifact-registry.md#1-template-registry` |
| `SKILL.md` | seeds `.devforgeai/skills/<name>/SKILL.md`; the `skill-md` template |
| `agent.md` | seeds each `.devforgeai/skills/<name>/subagents/<role>.md`; the `agent-md` template |
| `command.md` | seeds `.devforgeai/skills/<name>/commands/<command>.md`; the `command-md` template |

The registry addresses these four files at `.devforgeai/skills/skill-generator/templates/`. In the portable package they live in `assets/`, because that is where the fixed layout puts output templates; the install map places them at the registry path. See section 9.

### agents/
One file per worker in section 7. No file for Gate, Record or Handoff.

| File | Worker (from section 7) | writes | tools | compiled to |
|------|-------------------------|--------|-------|-------------|
| `spec_reader.md` | `spec_reader` | evidence | Read, Grep, Glob, Write, Bash(devforgeai status) | `.claude/agents/skill-generator-spec_reader.md`, `.codex/agents/skill-generator-spec_reader.toml` |
| `skill_yaml_writer.md` | `skill_yaml_writer` | candidate | Read, Grep, Glob, Edit, Write, Bash(devforgeai status) | `.claude/agents/skill-generator-skill_yaml_writer.md`, `.codex/agents/skill-generator-skill_yaml_writer.toml` |
| `subagent_writer.md` | `subagent_writer` | candidate | Read, Grep, Glob, Edit, Write, Bash(devforgeai status) | `.claude/agents/skill-generator-subagent_writer.md`, `.codex/agents/skill-generator-subagent_writer.toml` |
| `template_writer.md` | `template_writer` | candidate | Read, Grep, Glob, Edit, Write, Bash(devforgeai status) | `.claude/agents/skill-generator-template_writer.md`, `.codex/agents/skill-generator-template_writer.toml` |
| `claude_compiler.md` | `claude_compiler` | candidate | Read, Grep, Glob, Edit, Write, Bash(devforgeai status) | `.claude/agents/skill-generator-claude_compiler.md`, `.codex/agents/skill-generator-claude_compiler.toml` |
| `codex_compiler.md` | `codex_compiler` | candidate | Read, Grep, Glob, Edit, Write, Bash(devforgeai status) | `.claude/agents/skill-generator-codex_compiler.md`, `.codex/agents/skill-generator-codex_compiler.toml` |

## 9. Gotchas and edge cases

| Situation | What goes wrong | What to do instead |
|-----------|-----------------|--------------------|
| A compile phase writes under `.claude/`, `.codex/` or `.agents/` | The `PreToolUse` check denies the write, because those trees are sequencer-owned and lie outside the candidate root; a path that reaches the checkpoint diff anyway refuses the result and the phase burns an attempt. | Stage under `compiled/claude/` and `compiled/codex/` inside the fence and record the destination in `install-map.json`. Installation is a separate human step; no sequencer operation performs it. |
| Treating the fence as including the target directories | Every proposal is refused and the run cannot finish. | The fence is exactly `.devforgeai/skills/<arg>/**` (`10-sequencer-and-contracts.md#4-per-skill-phase-registry`). The earlier reading that it also covers the provider trees is recorded here as rejected. |
| Expecting a failed phase to leave earlier files as they were | No phase declares `rewind_to`, so a `fail` never rewinds to an earlier phase: the failed phase retries against the same checkpoint, which holds the previous phases' files exactly as they were. | Every phase rewrites every file it owns, so a re-run overwrites rather than patches. A partially generated package is a legitimate on-disk state after a failure, and `/skill-validate {skill}` reports it. |
| Passing the specification path as the run argument | The fence becomes `.devforgeai/skills/docs/plan/.../SKILL-SPEC-004.md/**` and the gate refuses it. | The run argument is the skill name; the specification path is resolved by `spec_reader`, optionally overridden by `--spec`. The roster's `/skill-gen <spec>` names the specification by the skill it specifies. |
| The skill name and the command differ | A cross-reference check that compares a slash command to a skill name reports a false orphan. | The skill is `skill-generator` and its command is `/skill-gen`; the registry records both, and `11-artifact-registry.md` records this as divergence 4. The command file is `commands/skill-gen.md`. |
| Expecting a worker to run `check_spec.py` | No `skill-generator` phase grants a stack command key, so no worker holds `Bash(devforgeai run *)` and the call is denied at `PreToolUse`. | `spec_reader` applies the enumerated rules by reading and returns findings in its evidence file, with the bounded summary in `issues` and `note`. The script is the reference implementation, run by a human in section 14. |
| Expecting the `phase start` gate to check the specification | The document gate validates the fence only; it does not open the specification. | `read_spec` performs the specification check and returns `needs_user` with `SPEC GAPS`. Template and provenance conformance at the gate is a requirement on the gate library, recorded in `10-sequencer-and-contracts.md#3-2-defect-to-action-map-as-implemented` note 3 as designed and unimplemented, not as behaviour this run relies on. |
| The specification's `target` selects one provider | The unselected compile phase produces no file and the `document` oracle fails the transition. | That phase writes exactly one file, its `install-map.json`, marked unselected with an empty copy list, and claims that one path. |
| The registry gives this skill no Slice phase and no Review phase | A validator applying `04-dual-target.md#validation` item 1 literally reports two missing sub-phase kinds. | `read_spec` carries the Slice duty, and Review is externalised: this skill's handoff names `/skill-validate {skill}` as the first next step, which is the roster's "always runs skill-validator on its output". `skill-validator` records both as recorded divergences, not defects. |
| The four asset files carry the same names as files in the generated package | An author edits `assets/SKILL.md` believing it is the skill's own `SKILL.md`. | `assets/SKILL.md` is the `skill-md` template that seeds a generated skill; the package's own body is the root `SKILL.md`. The install map is the only place the two are related. |
| A generated project-specific skill is expected to be runnable | `devforgeai phase start` exits 2 for an unknown skill, and the phase registry in `policy.py` is the single source of truth for which skills exist. A newly generated skill such as `report-writer` has no entry there, so its command cannot open a run. | Generating the package is not registry admission. The package is a candidate; running it needs both a human install of the adapters and a registry entry naming its phases, workers, writes modes, attempts and oracle. This specification produces the first and states that the second is a separate change to the sequencer's registry. |
| Two specifications name the same `skill_name` | Resolution is ambiguous and a silent pick generates the wrong skill. | `resolve_spec.py` and `spec_reader` return `needs_user`; the handoff asks for an explicit `--spec` path. |
| A generated adapter is treated as installed | A run assumes provider-native workers exist that no one copied into place. | A generated adapter is an uninstalled candidate (`06-skill-specification.md#cold-session-protocol` step 5). Runtime verification of declared isolation is `12-post-mvp.md#pm-01`. |
| Expecting a Slice worker | A generated package grows a seventh agent file with no registry phase to run it. | Slice is a sequencer step inside `devforgeai phase start`: it writes `.devforgeai/work/<run>/context.json`, whose path every worker of the run is handed. No framework worker performs it and this package ships no agent file for it. |
| Expecting the document gate to re-resolve `depends_on` or `provenance` hashes | A specification is assumed to have been checked against its upstream sources, because a story gate would have done so. A document run has no story to carry `provenance[]`, `context[]` or `commands.hash`, so it re-resolves nothing. | `spec_reader` records the specification's `depends_on` entries in `evidence` and does not re-resolve them. Re-resolving would refuse every specification whose digests are still placeholders, which `01-skill-anatomy.md` hash rule 6 classes as `unresolvable-source` and a defect inside a project. Staleness of a generated skill against its specification is detected downstream: by `skill-validator`'s conformance rule 1 against `metadata.devforgeai-spec`, and by `/drift`. |
| Deciding a compiled profile's tool list | A compiler that gives every profile the same list either lets a judge repair what it found, or leaves a producer with no way to write. | The contract's `writes` declaration selects the list. `writes: none` compiles to `Read`, `Grep`, `Glob`, `Bash(devforgeai status)`. `writes: evidence` adds `Write`, admitted only under `.devforgeai/work/<run>/evidence/<agent>/`. `writes: candidate` adds `Edit` and `Write` inside the candidate root — `apply_patch` and `sandbox_mode = "workspace-write"` on the Codex target — plus `Bash(devforgeai run *)` for the stack keys the phase grants. Nothing wider is emitted: no git write, no package manager, no network tool, no raw stack command. |
| A worker returns `status: fail` with no `next` | The phase is expected to stop or to be treated as a soft warning. | The sequencer inserts a transition problem row naming the worker, so the phase retries to its `max_attempts` of 2 and then blocks `REQUIRE_HUMAN`. A failing phase is a retry, then a human, never a silent pass. |
| Treating `--fix` as a resume | The user expects `--fix` to continue from the phase that failed, and the earlier phases' files are assumed intact. | Resuming is not a flag. `devforgeai phase start skill-generator <name>` resumes a **blocked** run — one a `needs_user` result or an exhausted attempt budget left `active` with `run.yaml#blocked_at` set — at that phase in the same candidate root with attempts reset (`10-sequencer-and-contracts.md` sections 2 and 3.1); `/skill-gen {skill}` is that command, with or without `--fix`. With no blocked run to resume, the same call opens a fresh run with a fresh candidate root from `read_spec`, and `--fix` changes only what the workers read: the validate report is added to `spec_reader`'s inputs. It never merges two runs' files. |
| Treating "skill-generator calls skill-validator" as an in-run invocation | `devforgeai phase start` refuses a second run while one is active, so the call is refused and the run cannot finish. | No skill invokes another skill's run. The calls edge in `02-skill-roster.md` is a handoff row: this run's `next` names `/skill-validate {skill}`, and a human or a fresh session runs it. The procedure in section 7 contains no such call. |
| Using the hyphenated worker names from `05-subagent-sets.md` | The stop event's `agent_type` is compared against the registry name, so `skill-yaml-writer` does not resolve and the receipt is refused at `ingest-result`. | The registry name in `10-sequencer-and-contracts.md#4-per-skill-phase-registry` is canonical: `spec_reader`, `skill_yaml_writer`, `subagent_writer`, `template_writer`, `claude_compiler`, `codex_compiler`. The hyphenated form is a display alias. Canonical names are used in section 7, in the `subagents/<role>.md` filenames, in each compiled profile's `name` field, and in the evidence table. The compiled provider file is named `<skill>-<role>` so two skills' profiles never collide in one `.claude/agents/` directory, while `name` stays the canonical worker name the stop event carries. |
| Reading the section 7 handoff table as what a run prints | The declared rows and the rendered block differ, and a reader follows a next step the sequencer never wrote. | The declared table is the contract the skill carries in `skill.yaml`; the current sequencer writes `/status` for a document run that passes and for a `REQUIRE_HUMAN` block, the runner repair then the skill command for a `COULD_NOT_RUN` block, and the skill command with `--fix` for a `WARN` or `OFF` block. Both are recorded in section 7. |
| Which worker may write, and where | A compiler that treats every worker alike either lets `spec_reader` repair the specification it was asked to judge, or leaves the five writing phases with no way to produce a file | Roles follow the registry's `writes` column: `read_spec` compiles to a judge declaring `writes: evidence`, whose one write reaches `.devforgeai/work/<run>/evidence/spec_reader/` and nothing else, and the other five compile to producers that write inside the candidate root with Edit and Write and name what they wrote in `claimed_paths`. The sequencer derives what actually changed from the checkpoint diff, so the split is enforced by the diff and not by the worker's word. |
| Where the generated package ends up | A reader expects `.devforgeai/skills/<name>/` to appear in the working tree the moment a phase passes | Every write lands in the candidate root `.devforgeai/work/<run>/wt`, which is gitignored. The package reaches the canonical checkout only at `devforgeai promote <run>`, never at Handoff: the last passing `devforgeai phase next` marks the run `ready_to_promote` and writes a `REQUIRE_HUMAN` handoff whose only forward step is that command, and `SKILL.md` runs it only after the user confirms in the session. A promotion refused with `STALE_BASE`, `DIRTY_TARGET` or `MERGE_CONFLICT` — all three refuse the promote command, not the transition — leaves the run `ready_to_promote` with its candidate root intact, and `devforgeai promote <run>` retries it once the user has resolved the reason. |
| A `REQUIRE_HUMAN` run treated as closed, with `/status` as its next step | `needs_user` and an exhausted attempt budget were described as closing the run, so the section 7e rows sent the user to `/status` and the OI-5 row said no flag could resume anything. A closed run has no candidate root, so the work the phases had already done appeared to be lost | Settled in `10-sequencer-and-contracts.md` (section 2's `phase start` row, section 3.1, section 5.4's `needs_user` row, section 6's `REQUIRE_HUMAN`, blocked-run row): such a run stays `active` with its lease released, keeps its candidate root and every checkpoint, and records `run.yaml#blocked_at`. `devforgeai phase start skill-generator <arg>` — the same skill and argument — resumes it at `blocked_at` with `attempts` reset. The three section 7e `needs_user` and attempt-limit rows and the "Treating `--fix` as a resume" row now name `/skill-gen {skill}` as the forward step, with `devforgeai phase fail --reason <text>` then `/status` as the abandon route; any other skill on the same story needs that `phase fail` first. |
| The `compile_codex` evidence row promoted the run itself | "On pass this is the last phase: the sequencer promotes the run into the canonical checkout" made the last transition move canonical bytes with no point at which the user consents | Section 7b's candidate-root paragraph ("At Handoff the sequencer promotes the run"), the section 7c row and the section 9 row above now carry the two-block model of `WRITE-MODEL-REVISION.md` D7 and `10-sequencer-and-contracts.md` sections 5.4, 6 and 12.4: `devforgeai phase next` marks the run `ready_to_promote` and writes a `REQUIRE_HUMAN` block whose only forward step is `devforgeai promote <run>`; `SKILL.md` runs that command only after the user confirms; the promotion writes the second block. |
| `STALE_BASE`, `DIRTY_TARGET` and `MERGE_CONFLICT` attributed to the transition | The refusals read as ways the last transition can fail, and the "two skill-gen runs at once" row had the second run promote itself the moment its last phase passed | All three refuse `devforgeai promote <run>` (`10-sequencer-and-contracts.md` section 2's refusal table, section 12.4's ordered steps). The section 7c row, the row above and the "two skill-gen runs" row now name the command that raises them, and both concurrent runs stop at `ready_to_promote` and wait for the user. |
| The section 7e outcome table had no `ready_to_promote` row | Every run ends in two handoff blocks and the table listed only the second, so a generator reading the table alone would never emit the promote step | A "pass, every phase passed, run `ready_to_promote` and not yet promoted" row now heads the table with `devforgeai promote {run}` as its one forward step, and the row naming `/skill-validate {skill}` is labelled `promoted` so it is clear it renders the second block. |
| `promote <run>` was missing from the compiled grammar | Section 7f's Tools row already granted `devforgeai promote <run>`, but the section 7a procedure stopped at printing the block, the section 12 `allowed-tools` line omitted it, and section 13's `skill-validator` rule said "four model-callable operations" — so the compiled skill could not run the only command its own handoff names | `WRITE-MODEL-REVISION.md` D7 propagates the fifth form everywhere the four are enumerated. A new step 10 in section 7a calls it after the user asks, the `allowed-tools` line carries `Bash(devforgeai promote *)`, and section 13 now says five. |
| A phase owns more than 64 files | `claimed_paths` is bounded at 64 entries, and a package with a large `templates/` or `references/` tree can exceed it in one phase | The bound is per receipt, and this skill's six phases already split ownership by kind. A generated skill large enough to exceed 64 files in one phase is a specification whose section 8 lists more files than one phase can own; `spec_reader` reports it as a `SPEC GAPS` row rather than the run failing at ingest. |
| Reading this specification's earlier "no rewind for `skill-generator`" caveat | `10-sequencer-and-contracts.md#9-enforcement-block` no longer supports it: the fence `.devforgeai/skills/<arg>/**` is now checkpointed and rewound with the rest of the candidate root, and the caveat is explicitly withdrawn there. | R8 and the rewind row above are restated from the current section 9: a failed phase leaves the previous generated files as the last checkpoint had them. |
| Two skill-gen runs for different skills at once | Their fences are disjoint, so both open, and the second to finish finds canonical HEAD moved | `FENCE_OVERLAP` refuses only overlapping fences, so both runs are legal. Both stop at `ready_to_promote` and wait for the user; the second `devforgeai promote <run>` sees `STALE_BASE`; in worktree mode the sequencer rebases the run branch onto the new HEAD, reruns the last transition oracle and retries the fast-forward, and any rebase conflict aborts to `needs_user` with `MERGE_CONFLICT`. In copy mode `STALE_BASE` returns `needs_user` directly. |

## 10. Success criteria and test cases

### Success criteria
- Triggers on the section 4 positives and on none of the near-misses.
- For an approved specification, all six phases pass and the run's evidence directory holds six `<phase>-result.json` files and six `<phase>-report.md` files.
- Every path in the run's checkpoint diff lies inside `.devforgeai/skills/<name>/**` and appears in the writing phase's `claimed_paths`; the sequencer refuses the result otherwise.
- The generated `.devforgeai/skills/<name>/SKILL.md` is under 500 lines; the staged Codex `SKILL.md` frontmatter has exactly six keys; the staged Claude `SKILL.md` frontmatter has those six plus only keys the specification's section 12 authorises.
- The number of files under `subagents/` equals the number of worker contracts in the specification's section 7, with no file for Gate, Record or Handoff.
- The number of files under `references/` equals the number of phases plus one for `envelope.md`.
- For a specification with gaps, the run's checkpoint diff is empty and the handoff's `open_items` lists one row per gap.

### evals/evals.json (used verbatim)
```json
{
  "skill_name": "skill-generator",
  "evals": [
    {
      "id": 1,
      "prompt": "Run skill-gen for dev using a copy of docs/design/specs/SKILL-SPEC-001-dev.md whose section 7 worker table has been emptied. Work from the repository root.",
      "expected_output": "The read_spec phase returns needs_user with a SPEC GAPS list. No file is created under .devforgeai/skills/dev-tdd/. The handoff names the plan repair route and then the skill-gen command.",
      "expectations": [
        "No file exists under .devforgeai/skills/dev-tdd/ after the run",
        "The read_spec result reports status needs_user and its issues rows are titled SPEC GAPS",
        "The gaps name at least these three, each citing the rule it came from: a worker contract whose tools exceed read, a worker prompt file named for a sequencer operation, and an eval mode outside skip and quick",
        "The handoff block's open items list one row per gap",
        "The final message contains a handoff block whose next steps line 1 is /status, which is what the sequencer writes for a REQUIRE_HUMAN document run"
      ]
    },
    {
      "id": 2,
      "prompt": "Run skill-gen for skill-validator using the spec at docs/design/specs/SKILL-SPEC-013-skill-validator.md. Work from the repository root.",
      "expected_output": "All six phases pass. The neutral package and both staged adapters exist under .devforgeai/skills/skill-validator/. The handoff's first next step is the skill-validate command for skill-validator.",
      "expectations": [
        ".devforgeai/skills/skill-validator/skill.yaml, SKILL.md and commands/skill-validate.md all exist",
        ".devforgeai/skills/skill-validator/subagents/ holds exactly four files named anatomy_checker.md, provider_checker.md, spec_conformance_checker.md and validate_report_writer.md",
        ".devforgeai/skills/skill-validator/references/ holds exactly five files: one per phase plus envelope.md",
        "The staged file compiled/codex/skills/skill-validator/SKILL.md has exactly six frontmatter keys and the staged file compiled/claude/skills/skill-validator/SKILL.md additionally carries argument-hint",
        "compiled/claude/install-map.json and compiled/codex/install-map.json both list every staged file with a destination under a provider directory",
        "No file was created under .claude/, .codex/ or .agents/",
        "The generated .devforgeai/skills/skill-validator/skill.yaml declares a handoff.outcomes pass row naming the skill-validate command for skill-validator",
        "The final message contains a handoff block whose next steps line 1 is /status, which is what the sequencer writes for a document run that passed"
      ]
    },
    {
      "id": 3,
      "prompt": "Run skill-gen for skill-generator using the spec at docs/design/specs/SKILL-SPEC-012-skill-generator.md. Work from the repository root.",
      "expected_output": "All six phases pass and the skill generates itself: six worker prompts, seven reference files, four asset templates, two bundled scripts.",
      "expectations": [
        ".devforgeai/skills/skill-generator/subagents/ holds exactly six files named spec_reader.md, skill_yaml_writer.md, subagent_writer.md, template_writer.md, claude_compiler.md and codex_compiler.md",
        ".devforgeai/skills/skill-generator/references/ holds exactly seven files including envelope.md",
        ".devforgeai/skills/skill-generator/assets/ holds exactly four files named skill.yaml, SKILL.md, agent.md and command.md",
        ".devforgeai/skills/skill-generator/scripts/ holds check_spec.py and resolve_spec.py, and each prints usage text for a help flag",
        ".devforgeai/skills/skill-generator/SKILL.md is under 500 lines",
        "Every subagents file contains a must_not block and declares writes candidate, evidence or none with a tool list matching that declaration"
      ]
    }
  ]
}
```

Eval workspace, identical for all three evals and required before any of them can open a run: copy `docs/design/examples/hooks/fixtures/`, which supplies an armed `.devforgeai/` with `state.yaml` and `stack.yaml`, then copy `docs/design/specs/` and `docs/design/examples/` into it and install the dispatcher beside the sequencer. The repository root itself has no `.devforgeai/`, so `devforgeai phase start` cannot open a run there; an `/init`-ed copy is the equivalent alternative. No per-eval fixture overlay is required, because every input file is committed. Eval 1's input is the stale worked example, which is scheduled for deletion and is replaced by `docs/design/specs/SKILL-SPEC-001-dev.md`; when that deletion lands, eval 1's input path becomes the last committed copy of the example under `docs/design/examples/`, and the eval is retired if no copy remains. Quick-mode results are generation feedback only: one enabled run per eval and no baseline. They are not runtime conformance evidence, and no section of this specification gates on them; the deferred contract is `12-post-mvp.md#pm-02`.

## 11. Dependencies and compatibility

| Kind | Value |
|------|-------|
| Tools | SKILL.md: `Read` (limited to `.devforgeai/state.yaml`), `Agent`, and a Bash grammar no wider than `devforgeai status`, `devforgeai phase start <skill> <arg>`, `devforgeai phase fail --reason <text>`, `devforgeai validate`, plus `devforgeai promote <run>` after a `REQUIRE_HUMAN` block leaves a run `ready_to_promote` and the user asks for it. Judges: `Read`, `Grep`, `Glob`, `Bash(devforgeai status)` and `Write` scoped to `.devforgeai/work/<run>/evidence/<agent>/`. Producers: the same read set plus `Edit` and `Write` (Codex `apply_patch`) inside the candidate root. No phase of this skill grants a stack command key, so no worker carries the `Bash(devforgeai run *)` surface. |
| MCP servers | none |
| Runtime | Python 3.11+ and PyYAML 6+ for the two bundled scripts. No third-party library beyond PyYAML is imported. |
| Project commands | none. This is a document run: the enforcement block carries `commands: {}`, no phase declares a run key, and no oracle brokers a command. `.devforgeai/stack.yaml` is not consulted. Contract: `10-sequencer-and-contracts.md`. |
| DevForgeAI/Core compatibility | `NOT_APPLICABLE`. `skill-generator` is an anatomy-governed framework skill, not a Research Core adapter, and names no Research Core version. |
| Other skills | Upstream: `plan`, the sole author of the `skill-spec` template. Downstream: `skill-validator`, named as the first next step on the pass row. Calls no skill itself; the primary window may open a `skill-validator` run only after this run has completed, because `devforgeai phase start` refuses a second run while one is active. |
| Deferred dependencies | `12-post-mvp.md#pm-01` for runtime verification of declared worker isolation and for any installation authority beyond a human copy. `12-post-mvp.md#pm-06` for eval modes beyond `skip` and `quick`. `12-post-mvp.md#pm-02` for conformance evidence from repeated provider trials; quick-mode eval results are generation feedback only. None of the three is a precondition for running this skill, and no section gates on any of them. |

Frontmatter values derived from this table:

```yaml
compatibility: "Requires Python 3.11+ and PyYAML for the bundled scripts. Runs inside the Claude Code terminal or the Codex terminal with the DevForgeAI hook dispatcher installed."
allowed-tools: "Read Agent Bash(devforgeai status) Bash(devforgeai phase start *) Bash(devforgeai phase fail *) Bash(devforgeai validate) Bash(devforgeai promote *)"
```

## 12. Targets

The generator produces one provider-neutral semantic package and a separate adapter for each selected target when frontmatter, invocation policy, or agent configuration differs. Provider-neutral resources may be shared. Adapter directories are not required to be byte-identical or symlinked.

| Target | Install path | Invocation | Subagents | Notes |
|--------|--------------|------------|-----------|-------|
| claude | `.claude/skills/skill-generator/` plus `.claude/agents/` profiles | `/skill-gen` | provider-native workers: one judge and five producers | Provider-specific frontmatter keys (`argument-hint`, `disable-model-invocation`) are compiled into this target's SKILL.md only. |
| codex | `.agents/skills/skill-generator/` plus `.codex/agents/` profiles | `$skill-gen` | provider-native workers: one judge and five producers | Portable six-field frontmatter only; invocation policy goes in target-side configuration. |
| both | separate `.claude/skills/skill-generator/` and `.agents/skills/skill-generator/` adapters | as above | as above | Share only provider-neutral resources; validate each adapter independently. |

```yaml
license: MIT
metadata:
  version: "1.0.0"
  devforgeai-spec: "SKILL-SPEC-012"
  devforgeai-target: "both"
  devforgeai-anatomy: "true"
```

Not produced by `skill-creator` when this specification is built by it, and therefore added by a running `skill-generator` from the same specification: the provider-native `.claude/agents/*.md` and `.codex/agents/*.toml` worker profiles, provider-specific frontmatter keys for the Claude target, and the concise `AGENTS.md` section for Codex. Hook definitions are not per-skill: `/init` installs the one dispatcher and its provider fragments from `09-hook-dispatcher.md`, and this specification ships none.

A generated package, including this skill's own, is an uninstalled candidate until its provider-native controls are present and independently validated. Generation success and quick-mode eval success are not installation authority.

## 13. Constraints

- `SKILL.md` under 500 lines and roughly 5,000 tokens, holding only identity, the phase list, the dispatch loop, and the handoff table. Every other instruction lives in `references/<phase>.md`, `agents/<role>.md`, `scripts/` or `assets/`. Splitting a phase into more reference files is the correct response to the line budget; cutting content is not.
- References one level deep from whichever file is loaded: `SKILL.md` links to `references/`, `agents/`, `scripts/`, `assets/`; an `agents/*.md` may link to `references/*.md`. Nothing links further.
- Hooks, state writes, and phase advancement are not in the skill. Do not write an instruction the sequencer or a hook already enforces.
- No `README.md` inside the skill directory.
- No angle brackets in frontmatter. Description at most 1024 characters; name at most 64 characters.
- Imperative voice. Explain why a step matters rather than shouting a prohibition.
- Provide defaults, not menus. Procedures over declarations.
- Scripts take arguments, never prompt, and exit 0, 1 or 2.
- From the constitution slice for framework skills: every worker declares `writes: candidate`, `writes: evidence` or `writes: none` and holds no tool wider than that declaration allows; every generated worker prompt carries `must_not` verbatim from its contract; persona and critic are separate files; the neutral package records the specification id in `metadata.devforgeai-spec` so staleness is detectable.

## 14. Acceptance checks

Run these from the generated skill's parent directory before reporting done, and paste their output:

```bash
python -m scripts.quick_validate out/skill-generator     # run from the skill-creator directory
skills-ref validate out/skill-generator                  # open-standard validator, when installed
wc -l out/skill-generator/SKILL.md                       # must be under 500
ls out/skill-generator/agents/                           # six files, one per section 7 worker
ls out/skill-generator/references/                       # six phase files plus envelope.md
ls out/skill-generator/assets/                           # skill.yaml SKILL.md agent.md command.md
python out/skill-generator/scripts/check_spec.py docs/design/specs/SKILL-SPEC-012-skill-generator.md --json
python out/skill-generator/scripts/resolve_spec.py skill-validator
grep -rnE 'T[O]DO|T[B]D|\{\{' out/skill-generator || echo clean
```

`skills-ref` is not on this repository's PATH. When it is absent, `check_spec.py` plus the frontmatter rules enumerated in `references/compile_claude.md` and `references/compile_codex.md` are the enforced contract, and `skill-validator` re-checks the same rules; record the absence in the validation report rather than reporting a pass the validator did not run.

For non-Research anatomy skills, `skill-validator` additionally checks: Gate, Record and Handoff bound to sequencer operations; persona and critic in different files; `must_not` present in every agent file and no agent's `tools` exceeding read; the SKILL.md Bash grammar no wider than the five model-callable operations, `devforgeai promote <run>` included; handoff outcomes covering every status this skill can return, including `could_not_run`. The two recorded divergences in section 9 (no Slice phase, no Review phase in the registry entry) are reported as recorded divergences, not defects.

## 15. Provenance

| Source | Hash | Used for |
|--------|------|----------|
| docs/design/04-dual-target.md#neutral-skill-spec | see frontmatter | sections 6, 7, 8 |
| docs/design/04-dual-target.md#compiled-layouts | see frontmatter | sections 2, 6, 12 |
| docs/design/04-dual-target.md#validation | see frontmatter | sections 9, 14 |
| docs/design/06-skill-specification.md#deferred-to-devforgeai-s-skill-generator | see frontmatter | sections 2, 12 |
| docs/design/06-skill-specification.md#cold-session-protocol | see frontmatter | sections 0, 9, 12 |
| docs/design/10-sequencer-and-contracts.md#4-per-skill-phase-registry | see frontmatter | sections 6, 7, 9 |
| docs/design/10-sequencer-and-contracts.md#5-2-validation-order | see frontmatter | sections 2, 6, 7, 9 |
| docs/design/10-sequencer-and-contracts.md#9-enforcement-block | see frontmatter | sections 2, 9 |
| docs/design/10-sequencer-and-contracts.md#11-per-skill-evidence-and-gate-table | see frontmatter | section 7 |
| docs/design/10-sequencer-and-contracts.md#6-handoff-envelope | see frontmatter | sections 7, 9 |
| docs/design/11-artifact-registry.md#1-template-registry | see frontmatter | sections 7, 8 |
| docs/design/11-artifact-registry.md#2-artifact-path-patterns | see frontmatter | section 6 |
| docs/design/02-skill-roster.md#handoff-decision-tables | see frontmatter | section 7 handoff outcomes |
| docs/design/05-subagent-sets.md#sets-per-skill | see frontmatter | sections 7, 8 |
| docs/design/01-skill-anatomy.md#primary-window-contract | see frontmatter | sections 7, 11, 13 |
