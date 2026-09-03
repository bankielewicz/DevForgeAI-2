---
# == instance frontmatter ==
template: skill-spec
template_version: 1
id: SKILL-SPEC-013
skill_name: skill-validator
target: both
status: approved
author: "DevForgeAI plan skill"
date: 2026-09-02
depends_on:
  - source: docs/design/04-dual-target.md#validation
    hash: sha256:cc996fc4c545d08ef116b3a7657b36064247e278ca8301be0f0d9715a0d996f3
    excerpt: "1. For non-Research anatomy skills, anatomy compliance: all seven sub-phase kinds present; Gate, Slice, Record and Handoff bound to the sequencer operations that perform them; Work, Write and Review each bound to a named worker; persona and critic separated; Work may repeat."
  - source: docs/design/04-dual-target.md#compiled-layouts
    hash: sha256:faa1184ccf0d4d78a4c46900323d7f9570133b0c53cb886520cd1197e338e844
    excerpt: "A shared capability or skill specification owns provider-neutral semantics, but its Claude Code and Codex adapters are separate generated artifacts whenever frontmatter, invocation policy, or agent configuration differs."
  - source: docs/design/06-skill-specification.md#cold-session-protocol
    hash: sha256:ab73600267ef7b6721cf5c7599e7432f096b116b2b5aac12405ac933f9c17576
    excerpt: "Treat the generated output as a candidate. A non-Research adapter may install at `.claude/skills/<name>` and/or `.agents/skills/<name>` only after its section 12 release gates pass and a human accepts it."
  - source: docs/design/10-sequencer-and-contracts.md#4-per-skill-phase-registry
    hash: sha256:511733ee35ca74fd5a5c0b59f225d7d975788e7d43d939f44c23b7aa8460cff0
    excerpt: "| skill-validator | document | `docs/reports/validate-<arg>.md` | 4 |"
  - source: docs/design/10-sequencer-and-contracts.md#5-2-validation-order
    hash: sha256:9f1bf77b7e84302ff6f3f20260228d57390cc97ab8e8d3f68f52c3ff2658aab8
    excerpt: "`claimed_paths` is a list of at most 64 with no duplicate; a non-`pass` status carries none; `evidence_refs` at most 16; `note` and `issues` within bounds"
  - source: docs/design/10-sequencer-and-contracts.md#11-per-skill-evidence-and-gate-table
    hash: sha256:f5dc9ad016c382d9d033b25878267bd8e1ef240cb0ecaafeff33af16637e906e
    excerpt: "- **deterministic gate check** — what a script verifies before or after this phase, with no model judgement, against the candidate root rather than against the worker's account of it. \"The worker confirms\" is not a gate check."
  - source: docs/design/10-sequencer-and-contracts.md#6-handoff-envelope
    hash: sha256:747b6340fc5c2348aad33ca5488012808670b3503b311d7b7d0f1204625afd4c
    excerpt: "| 5 | A gate or critic failure names the owning skill and the command that re-runs it, from `repair_route`. |"
  - source: docs/design/11-artifact-registry.md#1-template-registry
    hash: sha256:09607ea79839ab215871d87e8221166e14eeb6ca26f8372e4ead4173f1d92907
    excerpt: "| `validate-report` | `.devforgeai/skills/skill-validator/templates/validate-report.md` | 1 | `^VAL-[0-9]{3}$` | skill, template, template_version, status, verdict, depends_on | Anatomy, Provider, Spec Conformance, Fixes |"
  - source: docs/design/11-artifact-registry.md#2-artifact-path-patterns
    hash: sha256:2d2e97afff50edf6b35bf674b1de217c684d5091361e5f1deae12de52b95fb51
    excerpt: "| `docs/reports/validate-<skill>.md` | `validate-report` | skill-validator | sequencer |"
  - source: docs/design/02-skill-roster.md#handoff-decision-tables
    hash: sha256:1dac784b4670cc7559f323011dfe304dfe8c0baf349063162f90d76d902c5d3c
    excerpt: "| skill-validator | pass (`verdict: pass`) | `/status`; then the command that requested the validation |"
  - source: docs/design/05-subagent-sets.md#sets-per-skill
    hash: sha256:9e12f3beb236a025c18d40e741c09ba675bd71d2d87f56e2b205c7556b944bf9
    excerpt: "| skill-validator | anatomy-checker, provider-checker, spec-conformance-checker, report-writer |"
  - source: docs/design/01-skill-anatomy.md#primary-window-contract
    hash: sha256:a6bbaf9af2d69f7ede18d7c40f242c42edb26d79be964ffec3f386d6347014c2
    excerpt: "For anatomy-governed skills, skill-validator rejects a compiled SKILL.md that contains a direct file read of anything except `state.yaml`, an inline prompt longer than a dispatch instruction, an LLM sub-phase without a named worker, or a Bash grammar wider than the model-callable operations above."
  - source: docs/design/01-skill-anatomy.md#the-seven-sub-phases
    hash: sha256:b3c1a62145dc7fd7ef4fb351242f6b67bb0838da1c70cc359b679bfa4986e7d1
    excerpt: "Gate, Slice, Record, and Handoff are deterministic sequencer operations, not workers. Only Work, Write, and Review dispatch an LLM."
---

# Skill Specification: skill-validator

A stranger with no conversation history must be able to build this skill from this document alone. Every question the generator would otherwise ask is answered below. This document contains no unresolved authoring assumption.

The `depends_on` digests are computed with the hash rule in `docs/design/01-skill-anatomy.md` (resolve the named heading through the next heading of the same or higher level, normalise CRLF to LF without trimming, join with LF, append one LF, and SHA-256 the UTF-8 bytes) and verified by `docs/design/specs/verify.py --only v3`; a source edit after this date makes V3 fail until the digest is recomputed.

## 0. Generator instructions

These instructions are addressed to the skill-generating agent (Anthropic's `skill-creator` skill, or a running DevForgeAI `skill-generator`). They replace its interview.

### Cold-session prompt

Paste this into a fresh session from the repository root:

```
Use the skill-creator skill to build the skill specified in docs/design/specs/SKILL-SPEC-013-skill-validator.md.
Follow its section 0 exactly. Output directory: ./out. Eval mode: quick.
```

### Rules for the generator

1. **Do not interview.** Sections 1-13 pre-answer every Capture Intent and Interview question. Treat this document as the conversation history you are told to harvest from.
2. **Test prompts are pre-approved.** Use section 10 verbatim as `evals/evals.json`. Do not ask whether they look right.
3. **Trigger queries are pre-approved.** Use section 4 verbatim as the trigger eval set. Do not ask for sign-off.
4. **No human review loop.** Do not wait for the user to review results. Proceed to the next stage on your own.
5. **Eval mode** is given in the prompt and is one of two values. `skip`: write the skill only; create no `evals/`, run no prompt, run no description optimisation. `quick`: write the skill and `evals/evals.json`, run each test prompt once with the skill and no baseline, grade with the grader agent, write `grading.json`, and report pass or fail per expectation in the final message. Run the eval executions and the grader as foreground Agent-tool subagents, never as background shell processes, and do not end the turn until every `grading.json` exists. Any other mode name is a spec defect; the deferred interactive mode is `12-post-mvp.md#pm-06`.
6. **Output location** is given in the prompt. Create `./out/skill-validator/`. Write nowhere else except the `skill-validator-workspace/` sibling that eval runs require.
7. **On ambiguity, stop before output.** If this spec is `draft`, contains an unresolved authoring assumption, omits a section, contradicts itself, or leaves a decision this document does not make, do not guess and do not write candidate skill files. End with a list titled `SPEC GAPS` naming each section and question.
8. **Fidelity over creativity.** Use the description in section 3 verbatim. Use the four worker contracts in section 7 verbatim as the bodies of `agents/<role>.md`, adding only the Role / Inputs / Process / Output framing the grader agent uses. Do not add steps, tools, or behaviours this document does not mention.
9. **Finish with the acceptance checks** in section 14 and include their output in the final message.

## 1. Identity

| Field | Value |
|-------|-------|
| name | `skill-validator` (kebab-case, 15 chars, equals the directory name, no provider prefix) |
| title | Skill Validator |
| purpose | Check one compiled skill against the DevForgeAI anatomy rules, the open-standard skill format, and its originating specification, and write a verdict with a repair list, so a candidate skill is never installed on the strength of a generation run alone. |
| category | devforgeai-phase |
| version | 1.0.0 (skill-package version written to `metadata.version`) |
| license | MIT (frontmatter `license: MIT`) |

## 2. Problem and requirements

**Without this skill:** a generated skill is accepted because generation exited without an error. Nobody checks that the compiled `SKILL.md` reads only `state.yaml`, that its Bash grammar stayed inside the model-callable operations, that every worker prompt declares a `writes` mode and carries `must_not` and no tool wider than that mode allows, that the portable frontmatter has exactly the six open-standard fields, or that the workers on disk are the workers the specification described. Defects surface later as refused envelopes, a run that cannot finish, or a worker with a write tool it should never have had, and the failure is attributed to the framework rather than to the compile step that introduced it.

| ID | Kind | Requirement |
|----|------|-------------|
| R1 | explicit | Take one skill name and check the compiled skill under `.devforgeai/skills/<name>/` against the five checks in `04-dual-target.md#validation`. |
| R2 | explicit | Also check the open-standard constraints: the six permitted frontmatter fields, `name` equal to the directory name, `SKILL.md` under 500 lines, references one level deep. |
| R3 | explicit | Write one report at `docs/reports/validate-<skill>.md` carrying a verdict and a repair list keyed to the skill that owns each defect. |
| R4 | implicit | Every check is enumerated and deterministic, so two runs over the same bytes produce the same finding list. A check no rule can express is not a check. |
| R5 | implicit | The validator repairs nothing and installs nothing. It reports. |
| R6 | discovered | The three checker phases declare `writes: none`, so their workers are judges holding `Read`, `Grep`, `Glob` and `Bash(devforgeai status)`; no phase of this skill grants a stack command key, so no worker executes the bundled script. The checkers apply the same enumerated rules by reading; the script is the reference implementation. |
| R7 | discovered | `skills-ref` is not on this repository's PATH. The bundled script is the fallback, and its absence is recorded in the report rather than reported as a pass. |
| R8 | discovered | The registry entries for `skill-generator` and for this skill have no Slice phase and no Review phase, so `04-dual-target.md#validation` item 1 cannot hold literally for them. Those two absences are reported as recorded divergences, not defects. |

## 3. Description

```yaml
description: >
  Checks one compiled DevForgeAI skill against the anatomy rules, the open skill-format
  constraints and its originating specification, then writes a verdict report with a repair
  list. Use this skill whenever skill-gen finishes, whenever a skill package is edited by
  hand, before a candidate skill is installed into a provider directory, or when the user
  says skill-validate, check the skill, validate the compiled skill, does this skill match
  its spec, do the worker prompts match their declared write modes, or is this SKILL.md within the line budget. It
  reports findings keyed to the skill that owns each defect and never repairs, regenerates
  or installs anything. Do NOT use it to compile a skill (use skill-generator), to write or
  amend a skill specification (use plan), or to review project source code (use review).
```

Character count: 797 / 1024, measured on the folded scalar with its trailing newline stripped. No angle brackets. Written as a YAML block scalar so colons are safe.

## 4. Trigger set

```json
[
  {"query": "/skill-validate report-writer", "should_trigger": true},
  {"query": "skill-gen just finished for dev-tdd, check the output before I install it", "should_trigger": true},
  {"query": "does .devforgeai/skills/qa still match SKILL-SPEC-003 after I edited the worker prompts", "should_trigger": true},
  {"query": "verify the compiled skill has the six frontmatter fields and nothing else on the codex side", "should_trigger": true},
  {"query": "is the SKILL.md for analyze under 500 lines and are the references only one level deep", "should_trigger": true},
  {"query": "one of our agent prompts might have a write tool in it, audit the whole skill folder", "should_trigger": true},
  {"query": "check that every worker in the plan skill has a must_not block and no tool wider than its job needs", "should_trigger": true},
  {"query": "before we ship, confirm the handoff outcomes cover could_not_run for the drift skill", "should_trigger": true},
  {"query": "run the validator over skill-generator and write the report to docs/reports", "should_trigger": true},
  {"query": "compile SKILL-SPEC-009 into a skill folder for both targets", "should_trigger": false},
  {"query": "write a skill spec for a changelog skill with three workers", "should_trigger": false},
  {"query": "review the diff on STORY-004 for security issues before I merge", "should_trigger": false},
  {"query": "the qa report says criterion 2 failed, fix the code", "should_trigger": false},
  {"query": "what are the six fields allowed in SKILL.md frontmatter", "should_trigger": false},
  {"query": "install the compiled adapters into .claude/skills and restart the session", "should_trigger": false},
  {"query": "our docs drifted from the code, produce a drift report", "should_trigger": false},
  {"query": "check the story template header on STORY-011 before dev starts", "should_trigger": false},
  {"query": "explain why persona and critic have to be different subagents", "should_trigger": false}
]
```

## 5. Use cases

### UC-1: Straight after generation
- **User says:** "/skill-validate report-writer"
- **Steps:** 1. `devforgeai phase start skill-validator report-writer` opens the document run and pins the fence `docs/reports/validate-report-writer.md`. 2. `anatomy_checker` applies the anatomy rule list to the compiled package and returns findings. 3. `provider_checker` applies the provider and open-standard rule list to each adapter. 4. `spec_conformance_checker` compares the package against the originating specification. 5. `validate_report_writer` writes the report inside the candidate root with a verdict and a `## Fixes` table. 6. The sequencer records the phase and renders the handoff.
- **Result:** `docs/reports/validate-report-writer.md` exists with `verdict: pass`; the handoff's first next step is `/status`.

### UC-2: The compiled skill has defects
- **User says:** "/skill-validate billing-audit"
- **Steps:** The three checkers return findings: one judge prompt declares a write tool its `writes: none` contract does not allow, the Codex adapter's `SKILL.md` carries a Claude-only frontmatter key, and one worker in the specification has no prompt file. `validate_report_writer` writes the report with `verdict: fail` and one `## Fixes` row per finding, each naming the owning skill.
- **Result:** the report lists the fixes; the handoff's first next step is `/skill-gen billing-audit --fix`.

### UC-3: There is nothing to validate
- **User says:** "/skill-validate dev"
- **Steps:** The gate opens the run because the fence is legal. `anatomy_checker` finds no `.devforgeai/skills/dev/` directory and returns `status: needs_user` with one `issues` row naming the missing candidate. The run's checkpoint diff stays empty and no report is written.
- **Result:** the handoff names `/skill-gen dev` as the repair, then `/skill-validate dev`.

## 6. Inputs and outputs

### Inputs
| Input | Format | Example file | Required |
|-------|--------|--------------|----------|
| skill name | one argument to `/skill-validate`; substituted into the fence `docs/reports/validate-<arg>.md` | `skill-generator` | yes |
| compiled skill package | directory produced by `skill-generator` | `.devforgeai/skills/skill-generator/` | yes |
| staged adapters | directory inside the package | `.devforgeai/skills/skill-generator/compiled/claude/`, `compiled/codex/` | yes when the specification selects that target |
| originating specification | markdown with frontmatter, `skill-spec` template version 1 | `docs/design/specs/SKILL-SPEC-012-skill-generator.md` | yes |
| `--spec <path>` flag | path; overrides specification resolution | `docs/design/specs/SKILL-SPEC-001-dev.md` | no |
| constitution slice | markdown | `docs/architecture/constitution.md` | no; absent outside a project with an architecture set |
| `.devforgeai/state.yaml` | yaml; read by the sequencer, not by the primary window beyond the enforcement block | | yes |

The specification is resolved by the same order `skill-generator` uses: the `--spec` path when given; otherwise the single file under `docs/plan/*/skill-specs/SKILL-SPEC-*.md` whose frontmatter `skill_name` equals the argument; otherwise the single file under `docs/design/specs/SKILL-SPEC-*.md` whose `skill_name` equals the argument. When the package records `metadata.devforgeai-spec`, that id must match the resolved specification's `id`; a mismatch is a `spec_conformance` finding, not a resolution failure. Zero matches or more than one match is `status: needs_user`.

`skill-validator` consumes the four templates `skill-generator` produces — `skill-yaml` at `.devforgeai/skills/<name>/skill.yaml`, `skill-md` at `.devforgeai/skills/<name>/SKILL.md`, `agent-md` at each `.devforgeai/skills/<name>/subagents/<role>.md` and `command-md` at each `.devforgeai/skills/<name>/commands/<command>.md` — plus `skill-spec` from `plan` and `constitution` from `architect`. Each has a producer in `11-artifact-registry.md` section 5. `validate-report` is recorded as terminal in `11-artifact-registry.md` — `consumed_by: []` — while this skill's `fail` verdict routes to `/skill-gen {skill} --fix`, whose `spec_reader` reads the report back (`SKILL-SPEC-012-skill-generator.md` section 6). The registry entry is behind that route; nothing here gates on the registry's empty consumer list, and section 11 records the same edge.

### Outputs
| Output | Format | Location | Template |
|--------|--------|----------|----------|
| validation report | markdown with frontmatter | `docs/reports/validate-<skill>.md` | `assets/validate-report.md` |

Nothing else is written. The fence is exactly `docs/reports/validate-<arg>.md`, so the `anatomy`, `provider` and `spec_conformance` phases are judges that write no file at all; their output is the `issues`, `note` and `evidence_refs` in their receipts, which the sequencer records under `.devforgeai/work/skill-validator-<arg>/`.

### Output template

The `validate-report` template of `11-artifact-registry.md#1-template-registry`: version 1, id pattern `^VAL-[0-9]{3}$`, required frontmatter `skill`, `template`, `template_version`, `status`, `verdict`, `depends_on`, required sections `Anatomy`, `Provider`, `Spec Conformance`, `Fixes`.

```
---
skill: report-writer
template: validate-report
template_version: 1
status: final
verdict: pass | findings | fail
depends_on:
  - source: docs/plan/shop/skill-specs/SKILL-SPEC-004.md
    hash: sha256:<64 hex>
  - source: .devforgeai/skills/report-writer/SKILL.md
    hash: sha256:<64 hex>
---

# Validation report: report-writer

## Anatomy
| ID | Rule | Result | Evidence |
|----|------|--------|----------|
| VAL-001 | Gate, Record and Handoff bound to sequencer operations | pass | SKILL.md lines 41-58 |
| VAL-002 | every LLM sub-phase names a worker | pass | skill.yaml subphases |

## Provider
| ID | Rule | Result | Evidence |
|----|------|--------|----------|
| VAL-010 | portable frontmatter is exactly the six open-standard fields | pass | compiled/codex/skills/report-writer/SKILL.md |

## Spec Conformance
| ID | Rule | Result | Evidence |
|----|------|--------|----------|
| VAL-020 | one worker prompt per section 7 contract, and no extra | pass | subagents/ holds 4 files |

## Fixes
| ID | Finding | Owner | Command |
|----|---------|-------|---------|
```

Every row in `## Fixes` names the skill that owns the defect and the exact command that repairs it, so the handoff's `repair_route` is a copy of this table. A `pass` verdict leaves the table header with no rows.

### Return envelope

One schema, both providers: `devforgeai.worker-result/v1`, normative in `schemas/devforgeai/v1/worker-result.schema.json`. The three checkers are judges: they write only their findings file under `.devforgeai/work/<run>/evidence/<agent>/` — run-scoped scratch, gitignored, outside the candidate root and never promoted — name it in `evidence_refs`, and claim nothing. `validate_report_writer` is a producer: it writes the report inside the candidate root with Edit and Write (Codex: `apply_patch`) and names it. At `devforgeai ingest-result` the sequencer derives `changed[{path, blob_sha256, kind}]` from the candidate root's checkpoint diff, refuses the result when `changed` is not a subset of `claimed_paths` (`UNCLAIMED_CHANGE`) or when any changed path is outside the fence, runs the transition oracle inside the root, writes `<phase>-result.json` with `changed` and the checkpoint ref, creates the next checkpoint and releases the lease.

```yaml
schema: devforgeai.worker-result/v1
run: "skill-validator-report-writer"
skill: "skill-validator"
phase: "anatomy"
agent: "anatomy_checker"
status: pass | fail | needs_user | could_not_run
reason_code: runner_missing | timeout | network | hook_fault   # required only when status is could_not_run
candidate:
  id: "skill-validator-report-writer"
  input_checkpoint: "base"
claimed_paths: []          # empty for the three checker phases and for any non-pass status
evidence_refs: []          # at most 16 paths, root-relative or under .devforgeai/work/<run>/
note: "3 lines at most"
issues: [{id, kind, text}] # 10 rows at most
next: ""                   # never used: this skill declares no rewind target
```

Unknown keys are refused. `issues[]` is the bounded summary a reader sees; a checker's full finding set lives in its findings file. The `report` phase's receipt names the written report in `evidence_refs`, and that report's frontmatter carries the closed `verdict` field (`pass | findings | fail`) the sequencer reads to select the handoff row. The run's `status` and the handoff's `outcome` stay `pass`, because reporting a defect is a passing run (decision R-6, Q-7, SV-1).

`gate_policy` (`BLOCK | REQUIRE_HUMAN | WARN | OFF`) is a defect-to-action map declared in the consumed artifact, never a status returned here. A document run carries the fixed map `{unresolvable_source: BLOCK}`.

A finding is not a phase failure. A checker that ran its full rule list returns `status: pass`, writes its full finding set to its evidence file, and carries the bounded summary in `issues` and the counts in `note`; the verdict is decided by `validate_report_writer` from the accumulated findings. A checker returns `status: fail` only when it could not complete its rule list, and `needs_user` when the package or the specification is absent or ambiguous.

## 7. Procedure

The body of `SKILL.md`. Imperative voice. Bundled files are referenced by relative path.

### Steps

1. Parse the skill name and the `--spec` flag — why: the primary window may parse arguments and nothing else; anything it reads stays in context for the whole run.
2. Call `devforgeai phase start skill-validator <name>`. The sequencer runs the document fence gate, opens the run, and writes the enforcement block. On a non-zero exit, print the sequencer's output and stop — why: the gate, not the model, decides whether a run may open.
3. Dispatch `subagents/anatomy_checker.md` with the skill name and the `--spec` path when given — why: passing paths and ids keeps the package's bytes out of the primary window, where they would persist for the whole run.
4. Dispatch `subagents/provider_checker.md` with the same arguments.
5. Dispatch `subagents/spec_conformance_checker.md` with the same arguments and the path of `.devforgeai/work/skill-validator-<name>/anatomy-result.json`, from which it reads the resolved specification path.
6. Dispatch `subagents/validate_report_writer.md` with the three preceding phases' result paths under `.devforgeai/work/skill-validator-<name>/`.
7. Print the handoff block the sequencer rendered — why: the handoff is a rendering of `handoff.json`, and a block composed in the primary window can state a fact the evidence does not hold.
8. When that block reports the run `ready_to_promote` and the user asks for the promotion, call `devforgeai promote <run>` and print the second block the promotion rendered — why: promotion is never automatic, it is what moves `docs/reports/validate-<name>.md` from the candidate root into the canonical checkout under the lock, and a `REQUIRE_HUMAN` block is the only state in which the model may ask for it.

Between steps the primary window does nothing: the `SubagentStop` hook routes each worker's receipt to the sequencer, which diffs the candidate root against the phase's input checkpoint, checks the derived change set against `claimed_paths` and the fence, runs the transition oracle inside the root, checkpoints it, and advances the phase. The primary window branches only on the status it sees in the receipt, and calls `devforgeai phase fail --reason <text>` when the user abandons the run.

### Sub-phases and workers

Gate, Record, Slice and Handoff dispatch no LLM: they are `devforgeai` sequencer operations. Slice runs inside `devforgeai phase start`, which writes `.devforgeai/work/<run>/context.json` and hands its path to every worker of the run. This skill's registry entry has four phases and therefore no Review phase: `spec_conformance` reviews the skill under validation, not this run's own draft, and `05-subagent-sets.md#sets-per-skill` lists no critic for this skill. See section 9.

| # | Sub-phase | Performed by | Isolation |
|---|-----------|--------------|-----------|
| 0 | Gate | sequencer: `devforgeai phase start skill-validator <name>` | n/a |
| 1 | Slice | sequencer: `devforgeai phase start` writes `.devforgeai/work/<run>/context.json` | n/a |
| 2 | Work: `anatomy` | worker: `anatomy_checker` | required |
| 3 | Work: `provider` | worker: `provider_checker` | required |
| 4 | Work: `spec_conformance` | worker: `spec_conformance_checker` | required |
| 5 | Write: `report` | worker: `validate_report_writer` | required |
| 6 | Record | sequencer: `devforgeai phase next` | n/a |
| 7 | Handoff | sequencer: `devforgeai phase next` marks the run `ready_to_promote` and writes the `REQUIRE_HUMAN` block whose only forward step is `devforgeai promote <run>`; `SKILL.md` runs that command only after the user confirms in the session, and the promotion writes the run's second handoff block | n/a |

Isolation is the framework's own `required | preferred` declaration compiled into the target profile, not Claude's subagent `isolation` key; runtime verification of it is `12-post-mvp.md#pm-01`.

Every phase of one run works inside the same candidate root — `.devforgeai/work/<run>/wt`, created by `devforgeai phase start` and named to each worker as `candidate.root` in the status block the primary window pastes into the dispatch prompt alongside `run`, `phase`, `fence` and `granted_keys`. The three checkers are judges and write nothing in the root; their findings files go to `.devforgeai/work/<run>/evidence/<agent>/`, which is outside it. `report` writes one file in the root. The sequencer checkpoints the root at each transition, so the phases build linearly with no merge between them, and the one producer holds the run's lease from dispatch to `devforgeai ingest-result`. Promotion is never automatic and is no part of Handoff: the last passing `devforgeai phase next` marks the run `ready_to_promote` and writes a `REQUIRE_HUMAN` handoff whose only forward step is `devforgeai promote <run>`, and `SKILL.md` runs that command only after the user confirms in the session. That command, not the transition, is what merges the candidate root into the canonical checkout under `.devforgeai/lock`, and it is what refuses with `STALE_BASE` when canonical HEAD has moved past the run's recorded `base_ref`, with `DIRTY_TARGET` when the canonical report path is dirty, and with `MERGE_CONFLICT` when a rebase inside the root conflicted; a refused promotion leaves the run `ready_to_promote` with its candidate root intact for a retry.

### Worker contracts

Each block is a compilable subagent definition. `name` is the canonical registry worker name, because the stop event's `agent_type` is compared against it. `description` is the sentence the primary window matches when it decides to dispatch. `writes` is `evidence` for a judge — its one write goes to `.devforgeai/work/<run>/evidence/<agent>/` and never into the candidate root — and `candidate` for a producer, following the registry's `writes` column: three phases declare `none` there and one declares `docs`, so three judges and one producer. `compiled_to` names the two provider-native files `skill-generator` emits from the block; each body follows `templates/agent-md.md` in four parts — job, inputs, rules, receipt — and the producer's job sentence leads with what it writes.

```yaml
name: anatomy_checker
skill: skill-validator
description: Dispatch this worker first in a skill-validate run to judge the compiled package against the DevForgeAI anatomy rule list, before any other checker runs.
writes: evidence
tools: [Read, Grep, Glob, Write, Bash(devforgeai status)]
model: inherit
skills: []
responsibility: Apply the anatomy rule list in references/anatomy.md to the compiled skill package and return one finding per violated rule; repair nothing.
inputs: [.devforgeai/work/<run>/context.json, .devforgeai/skills/<name>/ (package), resolved specification path, references/anatomy.md]
outputs:
  - .devforgeai/work/<run>/evidence/anatomy_checker/findings.json, one row per rule evaluated with its result, kind and the package path it was read from
  - issues[]: one row per violated rule, each with its rule number and finding kind, at most ten
  - note: the counts of defect, divergence and not_run findings and the rules evaluated
  - evidence_refs[]: the findings file above, then the package paths the rows were read from
must_not:
  - write or claim any path inside the candidate root; this phase's one write is its findings file under .devforgeai/work/<run>/evidence/anatomy_checker/
  - report a rule that references/anatomy.md does not enumerate
  - record a pass for a rule it did not evaluate
  - repair, regenerate or reorder any file
isolation: required
returns: devforgeai.worker-result/v1
compiled_to:
  - .claude/agents/skill-validator-anatomy_checker.md
  - .codex/agents/skill-validator-anatomy_checker.toml
body: job, inputs, rules, receipt
```

`anatomy_checker` rule list, enumerated in `references/anatomy.md` and mirrored by `scripts/validate_skill.py --section anatomy`:

1. `skill.yaml` binds Gate, Slice, Record and Handoff to `devforgeai phase start` and `devforgeai phase next`, and to no worker.
2. Every `subphases` entry that is not a sequencer operation names a worker that exists as a `subagents/<role>.md` file.
3. There is no `subagents/` file for Gate, Slice, Record or Handoff.
4. Persona and critic, where the specification declares both, are two different files with two different prompts.
5. Every `subagents/<role>.md` carries a `must_not` block with at least one line, declares `writes: candidate`, `writes: evidence` or `writes: none` consistent with its phase's registry `writes` mode, and lists no tool wider than that declaration allows: a `writes: none` file names `Read`, `Grep`, `Glob` and `Bash(devforgeai status)` and nothing else; a `writes: evidence` file adds `Write`, whose only admitted destination is `.devforgeai/work/<run>/evidence/<agent>/`; a `writes: candidate` file adds `Edit` and `Write` inside the candidate root, plus `Bash(devforgeai run *)` for the stack keys its phase grants. A git write, a package manager, a network tool, an unrestricted Bash tool, `Edit` on a `writes: evidence` file, or any write tool on a `writes: none` file is a defect. A file written in the older `[read]` shorthand of `05-subagent-sets.md:28` satisfies this rule only where its phase declares `writes: none`.
6. Every `subagents/<role>.md` declares `returns: devforgeai.worker-result/v1`.
7. The compiled `SKILL.md` reads no file other than `.devforgeai/state.yaml`.
8. The compiled `SKILL.md` contains no inline prompt longer than a dispatch instruction: no pasted artifact content, no restated objective or acceptance criterion.
9. The compiled `SKILL.md` Bash grammar is no wider than `devforgeai status`, `devforgeai phase start <skill> <arg>`, `devforgeai phase fail --reason <text>`, `devforgeai validate`, and `devforgeai promote <run>`.
10. `handoff.outcomes` has one row per status the skill can return, including `could_not_run`, and no row has an empty next-steps list.
11. Every command named in `handoff.outcomes` and in `also_possible` resolves to a skill or command string in the registry.
12. Every `subagents/<role>.md` body has the four parts job, inputs, rules and receipt, and a `writes: candidate` file's job sentence names what it writes rather than opening with a statement of what it does not do.
13. Findings 1 to 12 are reported for the phases the registry declares for that skill. Where the registry declares no Review phase, that absence is recorded as `divergence`, not `defect`, and the reason is the registry entry itself. An absent Slice phase is neither: Slice is a sequencer step inside `devforgeai phase start` for every skill, so no package has one and rule 1 covers it.

```yaml
name: provider_checker
skill: skill-validator
description: Dispatch this worker after anatomy to judge each staged adapter against the provider and open-standard rule list, including the six-field frontmatter rule and each profile's tool list against its declared write mode.
writes: evidence
tools: [Read, Grep, Glob, Write, Bash(devforgeai status)]
model: inherit
skills: []
responsibility: Apply the provider and open-standard rule list in references/provider.md to the portable package and to each staged adapter, and return one finding per violated rule; repair nothing.
inputs: [.devforgeai/work/<run>/context.json, .devforgeai/skills/<name>/ (package and its compiled/ subtree), references/provider.md]
outputs:
  - .devforgeai/work/<run>/evidence/provider_checker/findings.json, one row per rule evaluated per target, with its result, kind and the adapter path it was read from
  - issues[]: one row per violated rule, each with its rule number and finding kind, at most ten
  - note: the targets checked, the SKILL.md line count, the maximum reference depth, and whether the open-standard validator was available
  - evidence_refs[]: the findings file above, then the adapter paths the rows were read from
must_not:
  - write or claim any path inside the candidate root; this phase's one write is its findings file under .devforgeai/work/<run>/evidence/provider_checker/
  - report a rule that references/provider.md does not enumerate
  - treat an absent open-standard validator as a pass
  - repair, regenerate or reorder any file
isolation: required
returns: devforgeai.worker-result/v1
compiled_to:
  - .claude/agents/skill-validator-provider_checker.md
  - .codex/agents/skill-validator-provider_checker.toml
body: job, inputs, rules, receipt
```

`provider_checker` rule list, enumerated in `references/provider.md` and mirrored by `scripts/validate_skill.py --section provider`:

1. The portable `SKILL.md` frontmatter keys are a subset of `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`, and it carries `name` and `description`.
2. `name` equals the containing directory name, is 1 to 64 characters, is lowercase alphanumeric and hyphens only, does not start or end with a hyphen, and has no consecutive hyphens.
3. `description` is 1 to 1024 characters and contains no angle bracket.
4. `compatibility`, when present, is at most 500 characters.
5. `SKILL.md` is under 500 lines.
6. References are one level deep: `SKILL.md` links only into `references/`, the worker prompt directory, `scripts/` and `assets/`; a worker prompt links only into `references/*.md`; no file links further. The worker prompt directory is `agents/` in a portable package and `subagents/` in an installed `.devforgeai/skills/<name>/` package; both names satisfy this rule, and rules 2, 3 and 5 of the conformance list address whichever of the two the package on disk uses.
7. There is no `README.md` in the skill directory.
8. The Codex adapter's `SKILL.md` carries only the six permitted fields; no provider-specific key from the Claude target appears in it.
9. The Claude adapter's `SKILL.md` carries the six permitted fields plus only the provider-specific keys the specification's section 12 authorises.
10. Every staged worker profile's tool list matches the `writes` declaration of the contract it was compiled from. A profile compiled from `writes: none` carries `Read`, `Grep`, `Glob` and `Bash(devforgeai status)` and nothing wider — a read-only sandbox and an approval policy that requests no approval, on the Codex target. A profile compiled from `writes: evidence` adds `Write` and nothing else, and its Codex sandbox admits only the run's evidence directory. A profile compiled from `writes: candidate` adds `Edit` and `Write` — `apply_patch` and a workspace-write sandbox on the Codex target — and `Bash(devforgeai run *)` only where its phase grants a stack key. No profile carries a git write, a package manager, a network tool or a raw stack command, and no Claude profile carries `isolation`, `hooks`, `memory`, `background` or `permissionMode`.
11. Every bundled script takes arguments, prompts for nothing, prints data to stdout and diagnostics to stderr, and documents a help flag.
12. Each staged adapter's install map lists every file that adapter stages, and every destination lies under a provider directory.
13. When the open-standard validator is unavailable on this machine, that fact is recorded as a finding of kind `not_run` with the rule list above as the substitute, and never as a pass.

```yaml
name: spec_conformance_checker
skill: skill-validator
description: Dispatch this worker after provider to compare the compiled package against its originating specification section by section, when a reader needs to know whether the package still matches the spec it came from.
writes: evidence
tools: [Read, Grep, Glob, Write, Bash(devforgeai status)]
model: inherit
skills: []
responsibility: Compare the compiled skill package against its originating specification section by section and return one finding per divergence; repair nothing.
inputs: [.devforgeai/work/<run>/context.json, .devforgeai/skills/<name>/ (package), resolved specification path, references/spec_conformance.md]
outputs:
  - .devforgeai/work/<run>/evidence/spec_conformance_checker/findings.json, the full worker, reference, script, asset and template deltas with one row per divergence
  - issues[]: one row per divergence, each naming the rule number and the two sides, at most ten
  - note: the specification id and path, whether the description matched, and the worker, reference and template delta counts
  - evidence_refs[]: the findings file above, then the specification path and the package paths compared
must_not:
  - write or claim any path inside the candidate root; this phase's one write is its findings file under .devforgeai/work/<run>/evidence/spec_conformance_checker/
  - accept a package whose metadata names a different specification id without recording a finding
  - judge whether the specification itself is a good design
  - repair, regenerate or reorder any file
isolation: required
returns: devforgeai.worker-result/v1
compiled_to:
  - .claude/agents/skill-validator-spec_conformance_checker.md
  - .codex/agents/skill-validator-spec_conformance_checker.toml
body: job, inputs, rules, receipt
```

`spec_conformance_checker` rule list, enumerated in `references/spec_conformance.md` and mirrored by `scripts/spec_diff.py`:

1. The package's `metadata.devforgeai-spec` equals the resolved specification's `id`.
2. The portable `description` is byte-identical to the specification's section 3 description.
3. There is one `subagents/<role>.md` per worker contract in section 7, with matching names and matching `writes` declarations from the set `candidate`, `evidence`, `none`, and no extra file.
4. Each worker prompt carries its contract's `responsibility` and every `must_not` line, unparaphrased.
5. There is one `references/<phase>.md` per phase in section 7 plus `references/envelope.md`, and no extra file.
6. Every script in section 8 exists under `scripts/`, and no extra script exists.
7. Every asset in section 8 exists under `assets/`, and no extra asset exists.
8. Every template in section 8 exists under `templates/` and carries a machine-readable header with `template`, `template_version`, `accepts_versions`, `required_frontmatter`, `required_sections`, `id_pattern` and `forbidden_text`.
9. The `handoff.outcomes` rows match the specification's section 7 handoff table.
10. `metadata.devforgeai-target` matches the specification's frontmatter `target`, and a staged adapter exists for every selected target.

`spec_conformance_checker` evidence: `{spec_id, spec_path, description_match: true|false, worker_delta: [rows], reference_delta: [rows], template_delta: [rows], findings: [rows]}`.

```yaml
name: validate_report_writer
skill: skill-validator
description: Dispatch this worker last in a skill-validate run to write the one validation report from the three preceding phase results and set its verdict.
writes: candidate
tools: [Read, Grep, Glob, Edit, Write, Bash(devforgeai status)]
model: inherit
skills: []
responsibility: Write docs/reports/validate-<name>.md inside the candidate root from the three preceding phases' recorded results, set the verdict, and key every fix row to the skill that owns the defect.
inputs: [.devforgeai/work/skill-validator-<name>/anatomy-result.json, provider-result.json and spec_conformance-result.json, and the three findings files their evidence_refs name under .devforgeai/work/<run>/evidence/, assets/validate-report.md, references/report.md]
outputs:
  - docs/reports/validate-<name>.md, written under the candidate root with Edit or Write and named in claimed_paths
  - evidence_refs[]: the written report, whose frontmatter verdict selects the handoff row, then the three preceding result paths and the three findings files
must_not:
  - record a finding no preceding phase's findings file carries
  - set verdict pass while any finding of kind defect or divergence is present
  - name a repair command that is not a registry command
  - repair or regenerate any part of the validated skill
  - write or claim any path other than the run's single fence entry
isolation: required
returns: devforgeai.worker-result/v1
compiled_to:
  - .claude/agents/skill-validator-validate_report_writer.md
  - .codex/agents/skill-validator-validate_report_writer.toml
body: job, inputs, rules, receipt
```

A judge's tools are `Read`, `Grep`, `Glob`, `Write` and `Bash(devforgeai status)`, with `Write` admitted only under `.devforgeai/work/<run>/evidence/<agent>/`, so a checker can record a finding set larger than the receipt without being able to touch the package it judges. The one producer holds `Edit` and `Write` inside the candidate root — `apply_patch` on the Codex target. No phase of this skill grants a stack key, so no worker carries `Bash(devforgeai run *)`, and no worker holds a git write, a package manager, a network tool or a raw stack command. `isolation` above is the framework's `required | preferred` declaration, not Claude's subagent `isolation` key, which the framework never sets; `hooks`, `memory`, `background` and `permissionMode` are Claude-only keys this skill leaves unset.

Verdict rule, the closed set the handoff reads: `pass` when no finding of any kind was recorded; `findings` when every finding is of kind `divergence` or `not_run` and none is of kind `defect`; `fail` when any finding is of kind `defect`. A `not_run` finding is listed in its section and repeated in `## Fixes` with the owner `operator` and the command that installs the missing checker, so a reader never mistakes an unrun rule for a satisfied one.

### Evidence and gate table

Run id for a document run is `<skill>-<arg>`, so every evidence path below begins `.devforgeai/work/skill-validator-<name>/`. The gate policy for a document run is the fixed map `{unresolvable_source: BLOCK}`; `write_fence_violation` is refused at result validation on every phase and is not configurable. Attempt budget is 2 for every phase. No phase grants a stack command key, and no phase declares `rewind_to`.

| phase | worker | deterministic gate check | gate_policy | evidence file | transition oracle |
|---|---|---|---|---|---|
| `anatomy` | `anatomy_checker` | run-level gate at `devforgeai phase start`: the fence `docs/reports/validate-<name>.md` is declared, is relative, contains no parent traversal, and matches no sequencer-owned path; no active or `ready_to_promote` run's fence overlaps it (`FENCE_OVERLAP`); `candidate open` creates the root and pins `base_ref`. At `ingest-result`: the checkpoint diff of the root is empty, because the phase's `writes` mode is `evidence` and the `PreToolUse` check admits this judge's `Write` only under `.devforgeai/work/<run>/evidence/<agent>/`, which lies outside the root; a non-empty root diff is `UNCLAIMED_CHANGE`. The phase grants no command key | `unresolvable_source: BLOCK` (document run fixed map) | `.devforgeai/work/skill-validator-<name>/anatomy-result.json`, `anatomy-report.md` | `report_only`: no file outside the fence changed since the gate snapshot and the whole-tree package and import policy holds |
| `provider` | `provider_checker` | at `ingest-result`: an empty root checkpoint diff, as `anatomy`; `issues[]` is at most ten rows and `evidence_refs` at most sixteen paths, which bounds the summary the receipt carries, not the findings file it points at | `unresolvable_source: BLOCK` | `.devforgeai/work/skill-validator-<name>/provider-result.json`, `provider-report.md` | `report_only`: as above |
| `spec_conformance` | `spec_conformance_checker` | at `ingest-result`: an empty root checkpoint diff, as `anatomy` | `unresolvable_source: BLOCK` | `.devforgeai/work/skill-validator-<name>/spec_conformance-result.json`, `spec_conformance-report.md` | `report_only`: as above |
| `report` | `validate_report_writer` | at `ingest-result`: `changed` derived from the checkpoint diff is exactly one path, `docs/reports/validate-<name>.md`, it is a subset of `claimed_paths`, it canonicalises inside the candidate root, it equals the fence entry, it is not sequencer-owned, and it is allowed by `writes: docs`; the whole-tree package and import rescan holds. The written report's frontmatter `verdict` is one of the closed set `pass`, `findings`, `fail`, and it is what the handoff row is selected by | `unresolvable_source: BLOCK`; `write_fence_violation: BLOCK` | `.devforgeai/work/skill-validator-<name>/report-result.json`, `report-report.md`, then `handoff.json` | `document`: the phase declared `writes: docs`, produced at least one file, and the declared output exists on disk in the root. On pass this is the last phase, and promotion is not part of it: `devforgeai phase next` marks the run `ready_to_promote` and writes a `REQUIRE_HUMAN` handoff whose only forward step is `devforgeai promote <run>`. `SKILL.md` runs that command only after the user confirms in the session; the promotion moves the report into the canonical checkout under `.devforgeai/lock`, marks the run `promoted`, clears enforcement, and writes the second handoff block. `STALE_BASE`, `DIRTY_TARGET` and `MERGE_CONFLICT` refuse that command, never `devforgeai phase next`, and leave the run `ready_to_promote` with its candidate root intact for a retry |

### Handoff outcomes

This is the decision table the skill declares as `handoff.outcomes` in `.devforgeai/skills/skill-validator/skill.yaml`, and it is the contract. The current sequencer does not read it: for a document run it writes `devforgeai promote <run>` on the ready block that the last passing transition produces and `/status` on the promoted block, `/status` on a `REQUIRE_HUMAN` block, the runner repair followed by `/skill-validate <name>` on a `COULD_NOT_RUN` block, and `/skill-validate <name> --fix` on a `BLOCK`, `WARN` or `OFF` block, `BLOCK` being what `devforgeai phase fail --reason` records. Both are recorded; the rows below are not what a run prints today. See section 9.

| Outcome | Next steps |
|---------|------------|
| pass, last phase, run `ready_to_promote` and not yet promoted | `devforgeai promote {run}` — the first of the run's two handoff blocks; `SKILL.md` runs the command only after the user confirms in the session, and the promotion writes the second block, whose row is selected by the report's `verdict` |
| pass, promoted, verdict `pass` | `/status` |
| pass, promoted, verdict `findings` | 1. `/skill-gen {skill} --fix`; 2. `/skill-validate {skill}` |
| pass, promoted, verdict `fail` | 1. `/skill-gen {skill} --fix`; 2. `/skill-validate {skill}` |
| `needs_user`, no compiled package under `.devforgeai/skills/<name>/` | 1. `devforgeai phase fail --reason <text>`, because the repair is another skill's run and the blocked `skill-validator` run holds the story; 2. `/skill-gen {skill}`; 3. `/skill-validate {skill}` |
| `needs_user`, zero or several specifications match | 1. `/skill-validate {skill}` with an explicit `--spec` path, which resumes the blocked run at `run.yaml#blocked_at` with attempts reset — the run stayed `active` and kept its candidate root. Also possible: `devforgeai phase fail --reason <text>` to abandon the root, then `/status` |
| `fail` at the attempt limit on any phase | 1. `/skill-validate {skill}` after the `open_items` defects are fixed, which resumes the blocked run at `blocked_at` with attempts reset. Also possible: `devforgeai phase fail --reason <text>` to abandon the root, then `/status` |
| `could_not_run`, any `reason_code` | 1. the repair route the `reason_code` names; 2. `/skill-validate {skill}` |
| missing worker identity on the stop event (synthesised `could_not_run`, `hook_fault`) | 1. `/status`; 2. `/skill-validate {skill}` |
| `devforgeai phase fail --reason` recorded by the user | `/status` |

Also possible, on every row: `/status`. When the run was ordered by a plan-written story, `/dev {story}` is the forward command a reader continues with after a `pass` verdict; the roster's "return to caller" row is not a command, because no sequencer operation resumes a caller run. See section 9.

## 8. Bundled resources

### Layout (fixed)

```
skill-validator/SKILL.md    # <=500 lines: identity, phase list, dispatch loop, handoff table
  references/anatomy.md
  references/provider.md
  references/spec_conformance.md
  references/report.md
  references/envelope.md
  agents/anatomy_checker.md
  agents/provider_checker.md
  agents/spec_conformance_checker.md
  agents/validate_report_writer.md
  scripts/validate_skill.py
  scripts/spec_diff.py
  assets/validate-report.md
```

`SKILL.md` links to `references/`, `agents/`, `scripts/` and `assets/`; an `agents/*.md` links to `references/*.md`; nothing links further. Guidance a phase needs lives in that phase's reference file, not in `SKILL.md` and not duplicated across files.

The portable package names the worker prompt directory `agents/`, which is the fixed layout's name and the open-standard convention. The registry addresses the same files at `.devforgeai/skills/<name>/subagents/<role>.md` (`11-artifact-registry.md#2-artifact-path-patterns`), which is the path this skill's dispatch steps reference. Provider rule 6 accepts either name; the install map is the only place the two are related, exactly as it is for `assets/` and `templates/`.

### scripts/
| File | Purpose | Invocation | Exit codes |
|------|---------|------------|------------|
| `validate_skill.py` | Reference implementation of the `anatomy_checker` and `provider_checker` rule lists in section 7, over a compiled skill directory. Prints one JSON object with `verdict`, `findings` and `sections_run`. Delegates to the open-standard validator when it is on PATH and records `validator_available: false` with a `not_run` finding when it is not. | `python scripts/validate_skill.py <skill-dir> [--section anatomy\|provider\|all] [--json]` | 0 no defect finding, 1 at least one defect finding, 2 usage |
| `spec_diff.py` | Reference implementation of the `spec_conformance_checker` rule list: compares a compiled skill directory against its originating specification and prints the worker, reference, script, asset and template deltas as JSON. | `python scripts/spec_diff.py <skill-dir> --spec <spec-path> [--json]` | 0 no divergence, 1 divergences listed, 2 usage |

Both scripts are non-interactive, take arguments and never prompt, print data to stdout and diagnostics to stderr, and document a help flag. Neither is executed by a worker: no phase of this skill grants a stack command key, so no worker holds `Bash(devforgeai run *)`, and the brokered surface is hook-only in any case. The scripts are the reference implementation of the rules the workers apply by reading, they are run by a human in section 14, and they are a sibling of `check_story.py` that the sequencer's gate library imports. See section 9.

### references/
| File | Content | Load when |
|------|---------|-----------|
| `anatomy.md` | The twelve enumerated anatomy rules of section 7, each with the reason it exists and the evidence shape that proves it. | dispatching `anatomy_checker` |
| `provider.md` | The thirteen enumerated provider and open-standard rules of section 7, including the six permitted frontmatter fields and the per-target placement rule. | dispatching `provider_checker` |
| `spec_conformance.md` | The ten enumerated conformance rules of section 7 and the delta row format. | dispatching `spec_conformance_checker` |
| `report.md` | The verdict rule, the finding kinds (`defect`, `divergence`, `not_run`), and the owner-and-command convention for the fix table. | dispatching `validate_report_writer` |
| `envelope.md` | The `devforgeai.worker-result/v1` schema with a pass, a fail, a needs_user and a could_not_run example, and the rule that a finding is not a phase failure. | every dispatch |

### assets/
| File | Used for |
|------|----------|
| `validate-report.md` | seeds `docs/reports/validate-<skill>.md`; the `validate-report` template of `11-artifact-registry.md#1-template-registry`, carried with its machine-readable header |

The registry addresses this file at `.devforgeai/skills/skill-validator/templates/validate-report.md`. In the portable package it lives in `assets/`, because that is where the fixed layout puts output templates; the install map places it at the registry path.

### agents/
One file per worker in section 7. No file for Gate, Record or Handoff.

| File | Worker (from section 7) | writes | tools | compiled to |
|------|-------------------------|--------|-------|-------------|
| `anatomy_checker.md` | `anatomy_checker` | evidence | Read, Grep, Glob, Write, Bash(devforgeai status) | `.claude/agents/skill-validator-anatomy_checker.md`, `.codex/agents/skill-validator-anatomy_checker.toml` |
| `provider_checker.md` | `provider_checker` | evidence | Read, Grep, Glob, Write, Bash(devforgeai status) | `.claude/agents/skill-validator-provider_checker.md`, `.codex/agents/skill-validator-provider_checker.toml` |
| `spec_conformance_checker.md` | `spec_conformance_checker` | evidence | Read, Grep, Glob, Write, Bash(devforgeai status) | `.claude/agents/skill-validator-spec_conformance_checker.md`, `.codex/agents/skill-validator-spec_conformance_checker.toml` |
| `validate_report_writer.md` | `validate_report_writer` | candidate | Read, Grep, Glob, Edit, Write, Bash(devforgeai status) | `.claude/agents/skill-validator-validate_report_writer.md`, `.codex/agents/skill-validator-validate_report_writer.toml` |

## 9. Gotchas and edge cases

| Situation | What goes wrong | What to do instead |
|-----------|-----------------|--------------------|
| A checker returns `status: fail` because it found defects | The transition oracle counts an attempt and, at the limit, blocks the run, so a skill with defects never reaches the report phase and no report is written. | A finding is not a phase failure. A checker that completed its rule list returns `pass`, writes its full finding set to its evidence file, and carries the bounded summary in `issues` with the counts in `note`. `status: fail` means the rule list could not be completed. |
| The open-standard validator is absent | A run silently reports a provider pass that nothing checked. `skills-ref` is not on this repository's PATH. | Rule 13 of the provider list records a `not_run` finding; the report repeats it in `## Fixes` with the owner `operator`. The verdict may still be `pass`, but the unrun rule is visible. |
| Expecting a worker to execute `validate_skill.py` | No phase of this skill grants a stack command key, so no worker holds `Bash(devforgeai run *)` and the call is denied at `PreToolUse`. | The checker applies the enumerated rules by reading and returns findings in `issues` and counts in `note`. The script is the reference implementation, run by a human in section 14. |
| Expecting the `phase start` gate to check the compiled skill | The document gate validates the fence only; it opens no file in the package. | `anatomy_checker` performs the check and returns `needs_user` when there is no package. Template conformance at the gate is a requirement on the gate library, recorded in `10-sequencer-and-contracts.md#3-2-defect-to-action-map-as-implemented` note 3 as designed and unimplemented, not as behaviour this run relies on. |
| Applying `04-dual-target.md#validation` item 1 literally to `skill-generator` or to this skill | Two sub-phase kinds are reported missing on every run, and every generated framework skill fails validation for a reason its registry entry mandates. | The registry entry is the authority on which phases a skill has. A missing Review phase is recorded as `divergence` with the registry entry as the reason; an absent Slice phase is expected on every skill, because Slice is a sequencer step. Only the phases the registry declares are checked for binding. |
| Treating "return to caller" as a next step | The handoff's `next` must be exactly one copy-pasteable command, and no sequencer operation resumes a caller run. | The pass row names `/status`. When a plan-ordered story requested the generation, `/dev {story}` is listed under "Also possible". |
| Validating a skill whose staged adapter for one target is marked not selected | Rule 12 reports the empty install map as a missing adapter. | The install map's `"selected": false` is the authoritative record; rule 10 of the conformance list checks it against the specification's `target`, and no adapter is expected for an unselected provider. |
| Two specifications name the same `skill_name` | Resolution is ambiguous and the conformance check runs against the wrong document. | `spec_diff.py` and the checkers return `needs_user`; the handoff asks for an explicit `--spec` path. Where the package records `metadata.devforgeai-spec`, that id is the tie-breaker and a mismatch is reported as a defect. |
| A `pass` verdict read as installation authority | A candidate is copied into a provider directory on the strength of a report. | Installation is a human release action after the section 12 release gates; runtime verification of declared isolation is `12-post-mvp.md#pm-01`. This skill installs nothing and its report says so. |
| Expecting a Slice worker | A validated package is reported as missing a sub-phase whose worker no registry entry declares. | Slice is a sequencer step inside `devforgeai phase start`: it writes `.devforgeai/work/<run>/context.json`, whose path every worker of the run is handed. No framework worker performs it, this package ships no agent file for it, and rule 13 of the anatomy list says an absent Slice phase is neither a defect nor a divergence. |
| Labelling `spec_conformance` as the Review sub-phase | Nothing then reviews `validate_report_writer`'s own draft, while the sub-phase table claims Review is covered. | `spec_conformance` is a Work sub-phase: it reviews the skill under validation, not this run's output. This skill's registry entry has no Review phase and `05-subagent-sets.md#sets-per-skill` lists no critic for it. Applied to its own package, rule 13 of the anatomy list records the absent Review phase as `divergence`, with the registry entry as the reason. |
| Expecting the document gate to re-resolve the report's `depends_on` hashes | A report is assumed to have been checked against its upstream sources, because a story gate would have done so. A document run has no story to carry `provenance[]`, `context[]` or `commands.hash`, so it re-resolves nothing. | `validate_report_writer` computes the digests of the two files it names in `depends_on` — the resolved specification and the compiled `SKILL.md` — with the hash rule in `01-skill-anatomy.md`, and records what it observed. It does not re-resolve the specification's own `depends_on` entries, because a placeholder digest there would be `unresolvable-source` under hash rule 6 and is not this skill's defect to report. |
| Reading `tools: [read]` as a literal tool name | A compiled profile ends up with no usable tool, or with a write tool added to make it work — which rule 5 then reports as a defect. | `read` is the older shorthand for a judge's list: `Read`, `Grep`, `Glob`, `Bash(devforgeai status)`. It satisfies rule 5 only where the phase declares `writes: none`. A `writes: candidate` phase's profile carries `Edit` and `Write` as well, and rule 5 reports their absence as a defect, because a producer with no write tool cannot finish its phase. |
| A worker returns `status: fail` with no `next` | The phase is expected to stop or to be treated as a soft warning. | The sequencer inserts a transition problem row naming the worker, so the phase retries to its `max_attempts` of 2 and then blocks `REQUIRE_HUMAN`. A checker that could not complete its rule list is a retry, then a human, never a silent pass — and never a `pass` verdict. |
| Treating a repair flag as a resume | The user expects a flag to continue from the phase that failed, and the earlier findings are assumed still recorded. | Resuming is not a flag. `devforgeai phase start skill-validator <name>` resumes a **blocked** run — one a `needs_user` result or an exhausted attempt budget left `active` with `run.yaml#blocked_at` set — at that phase in the same candidate root with attempts reset (`10-sequencer-and-contracts.md` sections 2 and 3.1); `/skill-validate {skill}` is that command. With no blocked run to resume, the same call opens a fresh run from `anatomy` and re-derives every finding, so a report is never a merge of two runs. |
| Treating "skill-generator calls skill-validator" as an in-run invocation | `devforgeai phase start` refuses a second run while one is active, so a validator run opened from inside a generator run is refused. | No skill invokes another skill's run. The calls edge in `02-skill-roster.md` is a handoff row: the generator run's `next` names `/skill-validate {skill}`, and a human or a fresh session runs it after that run has completed. |
| Using the hyphenated worker names from `05-subagent-sets.md` | The stop event's `agent_type` is compared against the registry name, so `report-writer` does not resolve and the receipt is refused at `ingest-result`. | The registry name in `10-sequencer-and-contracts.md#4-per-skill-phase-registry` is canonical: `anatomy_checker`, `provider_checker`, `spec_conformance_checker`, `validate_report_writer`. The hyphenated form is a display alias. Canonical names are used in section 7, in the `subagents/<role>.md` filenames, and in the evidence table, and rule 3 of the conformance list compares against them. |
| Reading the section 7 handoff table as what a run prints | The declared rows and the rendered block differ, and a reader follows a next step the sequencer never wrote. | The declared table is the contract the skill carries in `skill.yaml`; the current sequencer writes `/status` for a document run that passes and for a `REQUIRE_HUMAN` block, the runner repair then the skill command for a `COULD_NOT_RUN` block, and the skill command with `--fix` for a `WARN` or `OFF` block. Both are recorded in section 7, and rule 10 of the anatomy list checks the declared block rather than the rendered one. |
| No compiled package produces a `fail` verdict in this repository | The `fail` path is described but never exercised, so a regression in the verdict rule goes unnoticed. | Recorded as a known limit: no committed candidate in this repository is non-conforming, and per the template's overlay rule such an input must ship as a fixture overlay directory rather than as prose. Section 10 exercises `pass` and `needs_user` only, and the `fail` path is covered by the enumerated verdict rule in `references/report.md`. |
| Which worker may write, and where | A checker given a write tool over the package could repair what it was asked to judge, and the report would then describe a package nobody validated | Roles follow the registry's `writes` column: the three checker phases compile to judges declaring `writes: evidence`, whose one write reaches `.devforgeai/work/<run>/evidence/<agent>/` and nothing else; `report` declares `docs` and compiles to a producer that writes inside the candidate root and names the one path in `claimed_paths`. The sequencer derives what actually changed from the checkpoint diff, so a checker that wrote anything is refused with `UNCLAIMED_CHANGE` rather than believed. |
| Where the report ends up | A reader expects `docs/reports/validate-<skill>.md` in the working tree the moment the `report` phase passes | Every write lands in the candidate root `.devforgeai/work/<run>/wt`, which is gitignored. The report reaches the canonical checkout only at `devforgeai promote <run>`, never at Handoff: the last passing `devforgeai phase next` marks the run `ready_to_promote` and writes a `REQUIRE_HUMAN` handoff whose only forward step is that command, and `SKILL.md` runs it only after the user confirms in the session. A promotion refused with `STALE_BASE`, `DIRTY_TARGET` or `MERGE_CONFLICT` — all three refuse the promote command, not the transition — leaves the run `ready_to_promote` with its candidate root intact, and `devforgeai promote <run>` retries it once the user has resolved the reason. |
| A `REQUIRE_HUMAN` run treated as closed, with `/status` as its next step | `needs_user` and an exhausted attempt budget were described as closing the run, so the section 7e rows sent the user to `/status` and the OI-5 row said no flag could resume anything. A closed run has no candidate root, so the work the phases had already done appeared to be lost | Settled in `10-sequencer-and-contracts.md` (section 2's `phase start` row, section 3.1, section 5.4's `needs_user` row, section 6's `REQUIRE_HUMAN`, blocked-run row): such a run stays `active` with its lease released, keeps its candidate root and every checkpoint, and records `run.yaml#blocked_at`. `devforgeai phase start skill-validator <arg>` — the same skill and argument — resumes it at `blocked_at` with `attempts` reset. The section 7e `needs_user` and attempt-limit rows and the "Treating a repair flag as a resume" row now name `/skill-validate {skill}` as the forward step, with `devforgeai phase fail --reason <text>` then `/status` as the abandon route; any other skill on the same story needs that `phase fail` first. |
| Promotion read as part of Handoff | "The report reaches the canonical checkout at Handoff, when the sequencer promotes the run" made `devforgeai phase next` move canonical bytes on its own, with no point at which the user consents | Section 7b's candidate-root paragraph ("At Handoff the sequencer promotes the run"), the `report` evidence row ("On pass this is the last phase: the sequencer promotes the run"), section 7b row 7 and the row above now carry the two-block model of `WRITE-MODEL-REVISION.md` D7 and `10-sequencer-and-contracts.md` sections 5.4, 6 and 12.4: `phase next` marks the run `ready_to_promote` and writes a `REQUIRE_HUMAN` block whose only forward step is `devforgeai promote <run>`; `SKILL.md` runs that command only after the user confirms; the promotion writes the second block. |
| `STALE_BASE`, `DIRTY_TARGET` and `MERGE_CONFLICT` attributed to the transition | The refusals read as ways the last transition can fail, so a reader looks for them among the oracles | All three are refusals of `devforgeai promote <run>` (`10-sequencer-and-contracts.md` section 2's refusal table, section 12.4's ordered steps). The row above names the command that raises them and states that the root and its checkpoints survive every refusal. |
| The section 7e outcome table had no `ready_to_promote` row, and the verdict rows read as the only block | This is a report-producing skill: its `verdict` selects a row of the **second** block, and with no ready row the promote step was invisible to a generator reading the table alone | A "pass, last phase, run `ready_to_promote` and not yet promoted" row now heads the table with `devforgeai promote {run}` as its one forward step, and the three verdict rows are labelled `promoted`, matching `10-sequencer-and-contracts.md` section 6's rule 10 (the verdict selects the row; the run's `outcome` stays `pass`). |
| `promote <run>` was missing from the compiled grammar | Section 7f's Tools row and section 5's rule 9 already carried `devforgeai promote <run>`, but the section 7a procedure stopped at printing the block and the section 12 `allowed-tools` line omitted it, so the compiled skill could not run the only command its own handoff names | A new step 8 in section 7a calls it after the user asks, and the `allowed-tools` line carries `Bash(devforgeai promote *)`. Section 5's rule 9 and section 9's "fixed count of operations" row are unchanged: they already said five. |
| Checking the SKILL.md Bash grammar against a fixed count of operations | `01-skill-anatomy.md#primary-window-contract` no longer names "four" model-callable operations: its closed set now also carries `devforgeai promote <run>`. A checker hard-coding four reports a false finding on every compiled package that names the promotion command. | Check the grammar against the closed set that section lists, not against a count. This specification's section 2 was corrected to say "the model-callable operations" for the same reason. |
| SV-1: where the verdict lives now that the receipt has no `evidence` object | A generator looks for a `verdict` key in the receipt, finds none, and either invents one or lets the run status carry the verdict — which would make a report of a defect a failed run | The verdict is a frontmatter field of the written report, and the `report` receipt names that report in `evidence_refs`; the sequencer reads it there to select the handoff row. The closed set is `pass`, `findings`, `fail`. The run's `status` and the handoff's `outcome` stay `pass` on all three, because reporting a defect is a passing run; `findings` and `fail` name `/skill-gen {skill} --fix`, `pass` names `/status`. When the report's frontmatter carries no verdict, or one outside the closed set, the `document` oracle passes and the sequencer falls back to the document-run default `/status`, which section 9's handoff row already records. |

## 10. Success criteria and test cases

### Success criteria
- Triggers on the section 4 positives and on none of the near-misses.
- All four phases pass and the run's evidence directory holds four `<phase>-result.json` files and four `<phase>-report.md` files.
- The run's checkpoint diff holds exactly one path across the whole run, `docs/reports/validate-<skill>.md`, and it is the `report` receipt's only `claimed_paths` entry; the three checker phases leave an empty diff and write only under `.devforgeai/work/<run>/evidence/<agent>/`, which no checkpoint records and no promotion carries.
- The report carries the four required sections and a `verdict` from the closed set `pass`, `findings`, `fail`, and every `## Fixes` row names an owner and a registry command.
- Every finding cites the rule number it came from, so two runs over the same bytes produce the same finding list.
- A run against a skill name with no compiled package writes no report and returns `needs_user`.

### evals/evals.json (used verbatim)
```json
{
  "skill_name": "skill-validator",
  "evals": [
    {
      "id": 1,
      "prompt": "Generate the skill-generator skill from docs/design/specs/SKILL-SPEC-012-skill-generator.md, then run skill-validate on skill-generator. Work from the repository root.",
      "expected_output": "All four validator phases pass. docs/reports/validate-skill-generator.md exists with verdict pass, the four required sections, and the two registry divergences recorded as divergence rather than defect.",
      "expectations": [
        "docs/reports/validate-skill-generator.md exists and its frontmatter carries skill, template, template_version, status, verdict and depends_on",
        "The report has the four sections Anatomy, Provider, Spec Conformance and Fixes",
        "The Anatomy section records the absent Review phase as divergence, not defect, and names the registry entry as the reason",
        "The generated .devforgeai/skills/skill-generator/skill.yaml declares a handoff.outcomes pass row naming the skill-validate command",
        "The Provider section records that the open-standard validator was not available and marks that rule not_run rather than pass",
        "The verdict is findings and the Fixes table contains only the not_run row",
        "Exactly one path appears in the run checkpoint diff, docs/reports/validate-skill-generator.md"
      ]
    },
    {
      "id": 2,
      "prompt": "Generate the skill-validator skill from docs/design/specs/SKILL-SPEC-013-skill-validator.md, then run skill-validate on skill-validator. Work from the repository root.",
      "expected_output": "All four validator phases pass. docs/reports/validate-skill-validator.md exists with verdict pass, and the Provider section confirms the six-field rule on the staged Codex adapter.",
      "expectations": [
        "docs/reports/validate-skill-validator.md exists with verdict pass",
        "The Provider section records that the staged Codex SKILL.md frontmatter keys are a subset of the six permitted fields and that the staged Claude SKILL.md carries only the provider-specific keys section 12 authorises",
        "The Spec Conformance section records four worker prompts matching the four section 7 contracts with no extra file, and five reference files including envelope.md",
        "The Anatomy section records that every worker prompt carries a must_not block and no tool wider than its declared writes mode allows",
        "The Anatomy section records the absent Review phase for skill-validator as divergence, not defect",
        "No file was created under .claude/, .codex/ or .agents/"
      ]
    },
    {
      "id": 3,
      "prompt": "Run skill-validate on dev. There is no compiled package for dev in this repository. Work from the repository root.",
      "expected_output": "The anatomy phase returns needs_user naming the missing candidate. No report is written and no later phase runs.",
      "expectations": [
        "docs/reports/validate-dev.md does not exist after the run",
        "The anatomy result reports status needs_user and its issues row names the missing compiled package under .devforgeai/skills/dev/",
        "The provider, spec_conformance and report phases did not run",
        "The final message contains a handoff block whose next steps line 1 is /status, which is what the sequencer writes for a REQUIRE_HUMAN document run"
      ]
    }
  ]
}
```

Eval workspace, identical for all three evals and required before any of them can open a run: copy `docs/design/examples/hooks/fixtures/`, which supplies an armed `.devforgeai/` with `state.yaml` and `stack.yaml`, then copy `docs/design/specs/` into it and install the dispatcher beside the sequencer. The repository root itself has no `.devforgeai/`, so `devforgeai phase start` cannot open a run there; an `/init`-ed copy is the equivalent alternative. No per-eval fixture overlay is required, because every input file is committed. Evals 1 and 2 chain generation before validation, which is the sequence the roster describes and which keeps every input a committed file rather than a hand-edited fixture. Quick-mode results are generation feedback only: one enabled run per eval and no baseline. They are not runtime conformance evidence, and no section of this specification gates on them; the deferred contract is `12-post-mvp.md#pm-02`.

## 11. Dependencies and compatibility

| Kind | Value |
|------|-------|
| Tools | SKILL.md: `Read` (limited to `.devforgeai/state.yaml`), `Agent`, and a Bash grammar no wider than `devforgeai status`, `devforgeai phase start <skill> <arg>`, `devforgeai phase fail --reason <text>`, `devforgeai validate`, plus `devforgeai promote <run>`, which the last passing transition's `REQUIRE_HUMAN` block names as its only forward step and which `SKILL.md` calls only after the user asks for it. Judges: `Read`, `Grep`, `Glob`, `Bash(devforgeai status)` and `Write` scoped to `.devforgeai/work/<run>/evidence/<agent>/`. The one producer: the same read set plus `Edit` and `Write` (Codex `apply_patch`) inside the candidate root. No phase of this skill grants a stack command key, so no worker carries the `Bash(devforgeai run *)` surface. |
| MCP servers | none |
| Runtime | Python 3.11+ and PyYAML 6+ for the two bundled scripts. The open-standard validator is used when it is on PATH and is not required; its absence is a recorded `not_run` finding. |
| Project commands | none. This is a document run: the enforcement block carries `commands: {}`, no phase declares a run key, and no oracle brokers a command. `.devforgeai/stack.yaml` is not consulted. Contract: `10-sequencer-and-contracts.md`. |
| DevForgeAI/Core compatibility | `NOT_APPLICABLE`. `skill-validator` is an anatomy-governed framework skill, not a Research Core adapter, and names no Research Core version. |
| Other skills | Upstream: `skill-generator` for the compiled package and its `skill-yaml`, `skill-md`, `agent-md` and `command-md` artifacts, `plan` for the specification, `architect` for the constitution slice. Downstream: `11-artifact-registry.md` records `validate-report` with no consumer, and the one real edge is the repair route: a `fail` verdict names `/skill-gen {skill} --fix`, which reads the report back. No run of this skill invokes that command. |
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
| claude | `.claude/skills/skill-validator/` plus `.claude/agents/` profiles | `/skill-validate` | provider-native workers: three judges and one producer | Provider-specific frontmatter keys (`argument-hint`, `disable-model-invocation`) are compiled into this target's SKILL.md only. |
| codex | `.agents/skills/skill-validator/` plus `.codex/agents/` profiles | `$skill-validate` | provider-native workers: three judges and one producer | Portable six-field frontmatter only; invocation policy goes in target-side configuration. |
| both | separate `.claude/skills/skill-validator/` and `.agents/skills/skill-validator/` adapters | as above | as above | Share only provider-neutral resources; validate each adapter independently. |

```yaml
license: MIT
metadata:
  version: "1.0.0"
  devforgeai-spec: "SKILL-SPEC-013"
  devforgeai-target: "both"
  devforgeai-anatomy: "true"
```

Not produced by `skill-creator` when this specification is built by it, and therefore added by a running `skill-generator` from the same specification: the provider-native `.claude/agents/*.md` and `.codex/agents/*.toml` worker profiles, provider-specific frontmatter keys for the Claude target, and the concise `AGENTS.md` section for Codex. Hook definitions are not per-skill: `/init` installs the one dispatcher and its provider fragments from `09-hook-dispatcher.md`, and this specification ships none.

A generated package, including this skill's own, is an uninstalled candidate until its provider-native controls are present and independently validated. A `pass` verdict from this skill is evidence for a human installation decision, not the decision itself.

## 13. Constraints

- `SKILL.md` under 500 lines and roughly 5,000 tokens, holding only identity, the phase list, the dispatch loop, and the handoff table. The enumerated rule lists live in `references/anatomy.md`, `references/provider.md` and `references/spec_conformance.md`. Splitting a rule list into more reference files is the correct response to the line budget; cutting rules is not.
- References one level deep from whichever file is loaded: `SKILL.md` links to `references/`, `agents/`, `scripts/`, `assets/`; an `agents/*.md` may link to `references/*.md`. Nothing links further.
- Hooks, state writes, and phase advancement are not in the skill. Do not write an instruction the sequencer or a hook already enforces.
- No `README.md` inside the skill directory.
- No angle brackets in frontmatter. Description at most 1024 characters; name at most 64 characters.
- Imperative voice. Explain why a rule exists rather than shouting a prohibition.
- Provide defaults, not menus. Procedures over declarations.
- Scripts take arguments, never prompt, and exit 0, 1 or 2.
- From the constitution slice for framework skills: every check is enumerated in a reference file before it is applied, so a finding always cites a rule number; the validator repairs nothing; a rule that could not be evaluated is reported as `not_run` and never as a pass.

## 14. Acceptance checks

Run these from the generated skill's parent directory before reporting done, and paste their output:

```bash
python -m scripts.quick_validate out/skill-validator     # run from the skill-creator directory
skills-ref validate out/skill-validator                  # open-standard validator, when installed
wc -l out/skill-validator/SKILL.md                       # must be under 500
ls out/skill-validator/agents/                           # four files, one per section 7 worker
ls out/skill-validator/references/                       # four rule files plus envelope.md
ls out/skill-validator/assets/                           # validate-report.md
python out/skill-validator/scripts/validate_skill.py out/skill-validator --json
python out/skill-validator/scripts/spec_diff.py out/skill-validator --spec docs/design/specs/SKILL-SPEC-013-skill-validator.md --json
grep -rnE 'T[O]DO|T[B]D|\{\{' out/skill-validator || echo clean
```

`skills-ref` is not on this repository's PATH. When it is absent, `validate_skill.py` plus the enumerated rule lists in `references/provider.md` are the enforced contract; record the absence as a `not_run` finding rather than reporting a pass the validator did not run.

For non-Research anatomy skills, this skill additionally checks, on every package it validates: Gate, Slice, Record and Handoff bound to sequencer operations; persona and critic in different files; `must_not` and a `writes` declaration of `candidate`, `evidence` or `none` present in every agent file, with no tool wider than that declaration allows; the SKILL.md Bash grammar no wider than the model-callable operations; handoff outcomes covering every status the validated skill can return, including `could_not_run`. Applied to its own package, the absent Review phase in its registry entry is reported as a recorded divergence, not a defect.

## 15. Provenance

| Source | Hash | Used for |
|--------|------|----------|
| docs/design/04-dual-target.md#validation | see frontmatter | sections 2, 7, 9 |
| docs/design/04-dual-target.md#compiled-layouts | see frontmatter | sections 6, 7, 12 |
| docs/design/06-skill-specification.md#cold-session-protocol | see frontmatter | sections 2, 9, 12 |
| docs/design/10-sequencer-and-contracts.md#4-per-skill-phase-registry | see frontmatter | sections 6, 7, 9 |
| docs/design/10-sequencer-and-contracts.md#5-2-validation-order | see frontmatter | sections 6, 7 |
| docs/design/10-sequencer-and-contracts.md#11-per-skill-evidence-and-gate-table | see frontmatter | section 7 |
| docs/design/10-sequencer-and-contracts.md#6-handoff-envelope | see frontmatter | sections 6, 7, 9 |
| docs/design/11-artifact-registry.md#1-template-registry | see frontmatter | sections 6, 8 |
| docs/design/11-artifact-registry.md#2-artifact-path-patterns | see frontmatter | section 6 |
| docs/design/02-skill-roster.md#handoff-decision-tables | see frontmatter | section 7 handoff outcomes |
| docs/design/05-subagent-sets.md#sets-per-skill | see frontmatter | sections 7, 8 |
| docs/design/01-skill-anatomy.md#primary-window-contract | see frontmatter | sections 7, 11, 13 |
| docs/design/01-skill-anatomy.md#the-seven-sub-phases | see frontmatter | sections 7, 9 |
