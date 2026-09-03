---
# == template header: read by the DevForgeAI gate; keep as is ==
template: skill-spec
template_version: 1
accepts_versions: [1]
required_frontmatter: [id, skill_name, target, status, template_version, depends_on, author, date]
required_sections:
  - "## 0. Generator instructions"
  - "## 1. Identity"
  - "## 2. Problem and requirements"
  - "## 3. Description"
  - "## 4. Trigger set"
  - "## 5. Use cases"
  - "## 6. Inputs and outputs"
  - "## 7. Procedure"
  - "## 8. Bundled resources"
  - "## 9. Gotchas and edge cases"
  - "## 10. Success criteria and test cases"
  - "## 11. Dependencies and compatibility"
  - "## 12. Targets"
  - "## 13. Constraints"
  - "## 14. Acceptance checks"
  - "## 15. Provenance"
id_pattern: "^SKILL-SPEC-[0-9]{3}$"
forbidden_text: ["TODO", "TBD", "{{", "}}", "<fill in>"]
# == instance frontmatter: fill every field ==
template: skill-spec
template_version: 1
id: SKILL-SPEC-000
skill_name: example-skill
target: both            # claude | codex | both
status: draft           # draft | approved | generated | validated
author: "{{author}}"
date: 2026-01-01
depends_on:             # context bundle: every upstream doc this spec was sliced from
  - source: docs/architecture/constitution.md#mandates
    hash: sha256:0000000000000000000000000000000000000000000000000000000000000000
    excerpt: "{{verbatim excerpt}}"
---

# Skill Specification: {{skill-name}}

A stranger with no conversation history must be able to build this skill from this document alone. Every question the generator would otherwise ask is answered below. A draft may record a genuinely unknown value as an authoring `ASSUMPTION:` instead of leaving a placeholder. An `approved`, `generated`, or `validated` spec must contain no unresolved authoring assumption; generation from a draft with one stops with `SPEC GAPS`. A literal `ASSUMPTION:` string used solely as fixture input or an expected test value is test data, not an authoring assumption.

## 0. Generator instructions

These instructions are addressed to the skill-generating agent (Anthropic's `skill-creator` skill, or DevForgeAI's `skill-generator`). They replace its interview.

### Cold-session prompt

Paste this into a fresh session from the repository root:

```
Use the skill-creator skill to build the skill specified in {{path/to/this/spec.md}}.
Follow its section 0 exactly. Output directory: {{absolute or repo-relative dir}}. Eval mode: quick.
```

### Rules for the generator

1. **Do not interview.** Sections 1-13 pre-answer every Capture Intent and Interview question (what it enables, when it triggers, output format, test cases, edge cases, input/output formats, example files, success criteria, dependencies). Treat this document as the conversation history you are told to harvest from.
2. **Test prompts are pre-approved.** Use section 10 verbatim as `evals/evals.json`. Do not ask whether they look right.
3. **Trigger queries are pre-approved.** Use section 4 verbatim as the trigger eval set. Do not ask for sign-off.
4. **No human review loop.** Do not wait for the user to review results. Proceed to the next stage on your own.
5. **Eval mode** is given in the prompt and is one of two values:
   - `skip`: write the skill only. Do not create `evals/`, do not run test prompts, do not optimize the description.
   - `quick`: write the skill and `evals/evals.json`. Run each test prompt once with the skill (no baseline run), grade with the grader agent, write `grading.json`, and report pass/fail per expectation in your final message. Do not run the description-optimization loop. Run the eval executions and the grader as foreground Agent-tool subagents, never as background shell processes, and do not end your turn until every `grading.json` exists: a headless session terminates when the top-level turn ends and orphans anything still running.
   - Any other mode name is a spec defect. The deferred interactive mode is `12-post-mvp.md#pm-06`.
6. **Output location** is given in the prompt. Create `{{output-dir}}/{{skill-name}}/`. Do not write anywhere else except the `{{skill-name}}-workspace/` sibling that eval runs require.
7. **On ambiguity, stop before output.** If the spec is still `draft`, contains an unresolved authoring assumption, omits a section, contradicts itself, or leaves a decision this document does not make, do not guess and do not write candidate skill files. End with a list titled `SPEC GAPS` naming each section and question. The spec author fixes and approves the spec before re-running.
8. **Fidelity over creativity.** Use the description in section 3 verbatim. Use the subagent contracts in section 7 verbatim as `agents/<role>.md` bodies, adding only the four-section framing `templates/agent-md.md` fixes (Job, Inputs, Rules, Receipt). Do not add steps, tools, or behaviours the spec does not mention.
9. **Finish with the acceptance checks** in section 14 and include their output in your final message.

## 1. Identity

| Field | Value |
|-------|-------|
| name | `{{skill-name}}` (kebab-case, max 64 chars, equals the directory name, no `claude`/`anthropic` prefix) |
| title | {{Human Title}} |
| purpose | One sentence: what this skill lets the agent do that it could not do reliably before. |
| category | document-creation \| workflow-automation \| mcp-enhancement \| devforgeai-phase |
| version | 1.0.0 (skill-package version written to `metadata.version`; not the DevForgeAI or Research Core version) |

## 2. Problem and requirements

**Without this skill:** describe what goes wrong, for whom, in which situations. If a baseline run exists, paste its verbatim failure here; it is the ground truth the skill must fix.

| ID | Kind | Requirement |
|----|------|-------------|
| R1 | explicit | What the user asked for. |
| R2 | implicit | Expected but unstated (conventions, formats, safety). |
| R3 | discovered | Found during analysis or baseline runs. |

## 3. Description

The exact frontmatter `description`. Structure: what it does + when to use it + key capabilities + what NOT to use it for. For non-Research skills, be pushy about triggering and list contexts where the user needs it without naming it. Research is the explicit exception: persistent execution must trigger only from the exact `/research` or `$research` request-file invocation plus human digest confirmation; an implicit match may provide nonpersistent advice only. Max 1024 characters. No `<` or `>`. Written as a YAML block scalar so colons are safe.

```yaml
description: >
  {{What it does.}} Use this skill whenever {{target-authorized trigger contexts;
  Research lists only the exact explicit invocation}}. It {{key capabilities}}. Do NOT use it for
  {{near-miss cases}}; use {{other skill}} instead.
```

Character count: {{n}} / 1024.

## 4. Trigger set

Realistic queries a user would type, with detail (paths, names, backstory, casual phrasing, the odd typo). Near-misses share vocabulary with the skill but need something else. For Research, every positive contains the exact explicit provider invocation and complete request-file/digest arguments; advisory prose is a near-miss for persistence. The generator uses this list verbatim; its optimizer does its own train/test split.

```json
[
  {"query": "{{positive 1}}", "should_trigger": true},
  {"query": "{{positive 2}}", "should_trigger": true},
  {"query": "{{... 8-10 positives total}}", "should_trigger": true},
  {"query": "{{near-miss 1}}", "should_trigger": false},
  {"query": "{{near-miss 2}}", "should_trigger": false},
  {"query": "{{... 8-10 near-misses total}}", "should_trigger": false}
]
```

## 5. Use cases

Two or three. Each is the shape the skill body's examples take.

### UC-1: {{name}}
- **User says:** "{{verbatim}}"
- **Steps:** 1. ... 2. ... 3. ...
- **Result:** {{what exists afterwards}}

### UC-2: {{name}}
- **User says:** ...
- **Steps:** ...
- **Result:** ...

## 6. Inputs and outputs

### Inputs
| Input | Format | Example file | Required |
|-------|--------|--------------|----------|
| {{name}} | {{markdown / json / path / prose}} | `{{path}}` | yes/no |

### Outputs
| Output | Format | Location | Template |
|--------|--------|----------|----------|
| {{name}} | {{format}} | `{{path pattern}}` | `assets/{{template}}` or inline below |

### Output template
```
{{exact shape of the primary output, with placeholders}}
```

### Return envelope (DevForgeAI-anatomy skills only)

One schema, both providers: `devforgeai.worker-result/v1`, normative in
`schemas/devforgeai/v1/worker-result.schema.json`. A producer has already written
its files inside the candidate root; the receipt names the paths it claims, never
the bytes. The sequencer derives what changed from the checkpoint diff, refuses a
change that is unclaimed or outside the fence, runs the oracle and advances.
Research specifications do not use this receipt; they reference the typed
statuses and records under `src/devforgeai/skills/research/`.

```yaml
schema: devforgeai.worker-result/v1
run: "{{RUN-NNNNNN}}"
skill: "{{skill-name}}"
phase: "{{phase}}"
agent: "{{worker profile name}}"
status: pass | fail | needs_user | could_not_run
reason_code: runner_missing | timeout | network | hook_fault   # required only when status is could_not_run
candidate: {id: "{{RUN-NNNNNN}}", input_checkpoint: "{{phase-or-base}}"}
claimed_paths: ["{{root-relative path}}"]   # <= 64; empty for any non-pass status
evidence_refs: ["{{root-relative or work/<run>/ path}}"]   # <= 16
note: "{{<= 3 lines}}"
issues: [{id, kind, text}]              # <= 10
next: "{{rewind_to}}"                   # optional; legal only with status: fail
```

`gate_policy` (`BLOCK | REQUIRE_HUMAN | WARN | OFF`) is a defect-to-action map
declared in the consumed artifact, never a status returned here.

## 7. Procedure

The body of `SKILL.md`. Imperative voice. Explain why a step matters instead of shouting. Reference bundled files by relative path.

### Steps
1. {{step}} — why: {{reason}}
2. ...

### Sub-phases and workers (DevForgeAI-anatomy skills only)

Gate, Slice, Record and Handoff dispatch no LLM: they are `devforgeai` sequencer
operations. Only Work, Write and Review name a worker.

| # | Sub-phase | Performed by | Isolation |
|---|-----------|--------------|-----------|
| 0 | Gate | sequencer: `devforgeai phase start {{skill}} {{arg}}` | n/a |
| 1 | Slice | sequencer: `devforgeai phase start`, which writes `.devforgeai/work/<run>/context.json` | n/a |
| 2..n | Work | workers: {{skill-owned}} | required/preferred |
| n+1 | Write | worker: {{skill}}-writer | required |
| n+2 | Review | worker: {{skill}}-critic | required |
| n+3 | Record | sequencer: `devforgeai phase next` | n/a |
| n+4 | Handoff | sequencer: `devforgeai phase next` | n/a |

Each skill-owned worker becomes `agents/<role>.md` inside the skill. Contract per worker:

```yaml
name: {{role}}
writes: candidate | evidence | none   # producer | judge | receipt-only; it fixes the tools row below
responsibility: {{one sentence, one job}}
inputs: [{{paths or named artifacts}}]
outputs: [{{paths written under the candidate root and claimed in the receipt}}]
must_not:
  - {{forbidden action}}
  - write outside the candidate root or outside this phase's write fence   # producer
  - run a raw stack command, a git write, a package manager, or a network tool
tools: [Read, Grep, Glob, Edit, Write, Bash(devforgeai run *)]   # producer set
                               # judge set: [Read, Grep, Glob, Write, Bash(devforgeai status)], Write confined to
                               #   .devforgeai/work/<run>/evidence/<agent>/; a writes: none worker drops Write too
isolation: required | preferred
returns: devforgeai.worker-result/v1
```

A `writes: evidence` worker carries Write but never Edit or `devforgeai run`, and
its `must_not` says "write anywhere but this run's evidence directory"; its
findings file is what `evidence_refs` names, while `issues[]` stays the bounded
summary. A `writes: none` worker carries no write tool and its `must_not` says
"write any file". A `writes: candidate` worker is never told that it does not
write: its contract opens with what it writes and where.

For an anatomy-governed non-Research skill, SKILL.md dispatches each worker through the selected target's provider-native worker mechanism, using the generated target profile and file paths only. It never pastes or paraphrases artifact content, objectives, or acceptance criteria into the prompt. Its Bash grammar is exactly `devforgeai status | phase start <skill> <arg> | phase fail --reason | validate | promote <run>`; every other sequencer operation is hook-only, and `devforgeai run <key>` belongs to the lease-holding producer, not to the primary window. Isolation is a declaration compiled into the target profile; runtime verification of it is `12-post-mvp.md#pm-01`. Current Research adapters do not dispatch provider workers; they stop with `E_PROVIDER_WORKER_EXECUTION_UNAVAILABLE` before the first worker call.

### Handoff outcomes (DevForgeAI-anatomy skills only)
| Outcome | Next steps |
|---------|------------|
| pass | `{{command}}` |
| {{failure kind}} | `{{command}}` |

## 8. Bundled resources

### Layout (fixed)

```
<skill>/SKILL.md            # <=500 lines: identity, phase list, dispatch loop, handoff table
  references/<phase>.md     # one per phase: the guidance that phase's worker needs
  references/envelope.md    # worker-result schema
  agents/<role>.md          # one per worker; body = section 7 contract verbatim
  scripts/                  # deterministic, non-interactive, exit-coded
  assets/                   # output templates
```

Link depth: `SKILL.md` links to `references/`, `agents/`, `scripts/`, `assets/`;
an `agents/*.md` links to `references/*.md`; nothing links further. Guidance a
phase needs lives in that phase's reference file, not in `SKILL.md`, and not
duplicated across files.

### scripts/
| File | Purpose | Invocation | Exit codes |
|------|---------|------------|------------|
| `{{name}}.py` | {{deterministic check the model should not eyeball}} | `python scripts/{{name}}.py --input X` | 0 ok, 1 fail, 2 usage |

Scripts must not prompt interactively, must print data to stdout and diagnostics to stderr, and must document `--help`.

### references/
One row per phase, plus `envelope.md`.

| File | Content | Load when |
|------|---------|-----------|
| `{{phase}}.md` | the guidance that phase's worker needs | dispatching the {{phase}} worker |
| `envelope.md` | the `devforgeai.worker-result/v1` receipt schema | every dispatch |

### assets/
| File | Used for |
|------|----------|
| `{{template}}` | {{output it seeds}} |

### agents/
One file per worker in section 7. No file for Gate, Slice, Record or Handoff.

| File | Worker (from section 7) | `writes` |
|------|-------------------------|----------|
| `{{role}}.md` | {{role}} | candidate \| evidence \| none |

## 9. Gotchas and edge cases

Highest-value content in most skills. Only real ones. `None known` is a valid entry; an invented gotcha teaches a false constraint.

| Situation | What goes wrong | What to do instead |
|-----------|-----------------|--------------------|
| {{case}} | {{failure}} | {{handling}} |

## 10. Success criteria and test cases

### Success criteria
- Triggers on the section 4 positives and not on the near-misses.
- {{objective, countable criteria}}

### evals/evals.json (used verbatim)
```json
{
  "skill_name": "{{skill-name}}",
  "evals": [
    {
      "id": 1,
      "prompt": "{{realistic task prompt}}",
      "expected_output": "{{what success looks like}}",
      "files": ["{{path relative to skill root, or omit}}"],
      "expectations": [
        "{{verifiable statement}}",
        "{{verifiable statement}}"
      ]
    }
  ]
}
```

Two or three evals. Expectations must be specific and checkable from the transcript or output files, not stylistic. Any per-eval change to a shared fixture ships as an overlay directory (`fixtures/<skill>/overlays/eval-<id>/`) that the generator copies over the base fixture; never describe fixture edits in prose, because the generator will write them differently each time and may write something vacuous.

Quick-mode results are generation feedback only: one enabled run per eval and no baseline. They are not runtime conformance evidence, and no section of this spec may gate on such evidence; the deferred contract is `12-post-mvp.md#pm-02`. Research's own release evidence contract lives under `src/devforgeai/skills/research/`, not in this template.

## 11. Dependencies and compatibility

| Kind | Value |
|------|-------|
| Tools | SKILL.md: `Read`, `Agent`, and a Bash grammar no wider than `devforgeai status \| phase start <skill> <arg> \| phase fail --reason \| validate \| promote <run>`. Workers: producers `Read`, `Grep`, `Glob`, `Edit`, `Write`, `Bash(devforgeai run *)`; judges `Read`, `Grep`, `Glob`, `Bash(devforgeai status)`. |
| MCP servers | {{none or names}} |
| Runtime | {{python 3.11+, node 20, ...}} plus every third-party library any bundled script imports |
| Project commands | `.devforgeai/stack.yaml#{{anchor}}` plus the `commands` keys this skill uses ({{build, test, lint, format}}). Name keys only, never a literal command; the sequencer resolves them from the hash-pinned section. `build` is required when that section has `compiled: true`. Contract: `10-sequencer-and-contracts.md`. |
| DevForgeAI/Core compatibility | {{exact compatible version or NOT_APPLICABLE; Research must name the Research Core version separately from the skill-package version}} |
| Other skills | {{skills this one calls or must not conflict with}} |

Frontmatter values derived from this table:

```yaml
compatibility: "{{<= 500 chars; omit if nothing special}}"
allowed-tools: "{{space-separated; omit if not needed}}"
```

## 12. Targets

The generator produces one provider-neutral semantic package and a separate adapter for each selected target when frontmatter, invocation policy, or agent configuration differs. Provider-neutral resources may be shared. Adapter directories are not required to be byte-identical or symlinked.

| Target | Install path | Invocation | Subagents | Notes |
|--------|--------------|------------|-----------|-------|
| claude | `.claude/skills/{{name}}/` | `/{{name}}`; for Research exactly `/research <slug> --request <request-file> --confirm-request <sha256>` with no implicit persistence | provider-native workers, `writes: candidate \| evidence \| none` per role | Provider-specific frontmatter keys (`argument-hint`, `disable-model-invocation`) are compiled into this target's SKILL.md only. |
| codex | `.agents/skills/{{name}}/` plus `.codex/agents/` profiles | `${{name}}`; for Research exactly `$research <slug> --request <request-file> --confirm-request <sha256>` with no implicit persistence | provider-native workers, `writes: candidate \| evidence \| none` per role | Portable six-field frontmatter only; policy goes in target-side configuration. |
| both | separate `.claude/skills/{{name}}/` and `.agents/skills/{{name}}/` adapters | as above | as above | Share only provider-neutral resources; validate each adapter independently. |

```yaml
metadata:
  version: "1.0.0"
  devforgeai-core: "{{exact compatible Core version; Research only, omit otherwise}}"
  devforgeai-spec: "{{SKILL-SPEC-NNN}}"
  devforgeai-target: "{{claude|codex|both}}"
  devforgeai-anatomy: "{{true|false}}"
```

Not produced by skill-creator (deferred to DevForgeAI's skill-generator): provider-native `.claude/agents/*.md` and `.codex/agents/*.toml` worker profiles, provider-specific frontmatter keys for the Claude target, compatibility artifacts required by a pinned provider, and concise `AGENTS.md` sections. Hook definitions are not per-skill: `init` installs the one dispatcher and its provider fragments from `09-hook-dispatcher.md`, and no spec ships its own.

A generated package is an uninstalled candidate until those provider-native controls are present and independently validated. Generation or quick-mode success is not installation authority.

## 13. Constraints

- `SKILL.md` under 500 lines and roughly 5,000 tokens, holding only identity, the phase list, the dispatch loop, and the handoff table. Every other instruction lives in `references/<phase>.md`, `agents/<role>.md`, `scripts/`, or `assets/`, per the section 8 layout. Splitting a phase into more reference files is the correct response to the line budget; cutting content is not.
- References one level deep from whichever file is loaded: `SKILL.md` links to `references/`, `agents/`, `scripts/`, `assets/`; an `agents/*.md` may link to `references/*.md`. Nothing links further.
- Hooks, state writes, and phase advancement are not in the skill. Do not write an instruction the sequencer or a hook already enforces.
- No `README.md` inside the skill directory.
- No XML angle brackets in frontmatter. Description max 1024 chars, name max 64.
- Imperative voice. Explain why; avoid all-caps ALWAYS/NEVER.
- Provide defaults, not menus. Procedures over declarations.
- No interactive prompts in scripts.
- {{project-specific constraints from the constitution slice}}

## 14. Acceptance checks

Run these before reporting done and paste their output:

```bash
# frontmatter and naming (skill-creator's own validator)
python -m scripts.quick_validate {{output-dir}}/{{skill-name}}      # run from the skill-creator directory
# open-standard validator, if installed
skills-ref validate {{output-dir}}/{{skill-name}}
# size budget
wc -l {{output-dir}}/{{skill-name}}/SKILL.md                          # must be < 500
# every worker in section 7 has a prompt file, and no extra
ls {{output-dir}}/{{skill-name}}/agents/
# one reference file per phase, plus envelope.md
ls {{output-dir}}/{{skill-name}}/references/
# no leftover placeholders
grep -rnE 'T[O]DO|T[B]D|\{\{' {{output-dir}}/{{skill-name}} || echo clean
```

For non-Research anatomy skills, DevForgeAI skill-validator additionally checks: all sub-phase kinds present with Gate, Slice, Record and Handoff bound to sequencer operations; persona and critic are different files; `must_not` and `writes` present in every agent file and every agent's `tools` matching the role its `writes` declares; the SKILL.md Bash grammar is no wider than the model-callable operations; handoff outcomes cover every status the skill can return, including `could_not_run`. Research is validated against `src/devforgeai/skills/research/` and its typed schemas instead.

## 15. Provenance

| Source | Hash | Used for |
|--------|------|----------|
| {{doc#anchor}} | sha256:... | {{section}} |
| RUN-NNNNNN; SRC-NNNNNN; EVD-NNNNNN; CLM-NNNNNN; sealed manifest | sha256:... | {{section}} |

Mirror of `depends_on` in the frontmatter, with the section each source fed.
