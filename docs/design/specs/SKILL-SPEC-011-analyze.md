---
template: skill-spec
template_version: 1
id: SKILL-SPEC-011
skill_name: analyze
target: both
status: approved
author: "DevForgeAI wave-2 specification author"
date: 2026-09-02
depends_on:
  - source: docs/design/01-skill-anatomy.md#primary-window-contract
    hash: sha256:a6bbaf9af2d69f7ede18d7c40f242c42edb26d79be964ffec3f386d6347014c2
    excerpt: "**The model dispatches, the sequencer decides.** For an anatomy-governed skill, the primary window (provider entry adapter + skill orchestration) does light, trivial work only."
  - source: docs/design/01-skill-anatomy.md#provenance-chain
    hash: sha256:a972a34352485d39e86add257fad2a007e6241521b18234d152cd35888dbad25
    excerpt: "Every artifact's frontmatter lists the provenance entries it depends on (`depends_on:`) and the template version it was written under. Gate checks one artifact on entry; `/analyze` walks the whole chain."
  - source: docs/design/01-skill-anatomy.md#context-bundle-format
    hash: sha256:7b068feb30e7cc2f66292b512ac179cd217df225fb58517d2aaadd30b25236dc
    excerpt: "A literal placeholder hash (`sha256:fixture...`, `sha256:PENDING`) is reported as `unresolvable-source`."
  - source: docs/design/10-sequencer-and-contracts.md#4-per-skill-phase-registry
    hash: sha256:511733ee35ca74fd5a5c0b59f225d7d975788e7d43d939f44c23b7aa8460cff0
    excerpt: "| analyze | 1 | `cross_reference` | `cross_referencer` | none | 2 | — | report_only | — |"
  - source: docs/design/10-sequencer-and-contracts.md#3-4-re-resolving-sources-and-the-one-downgrade
    hash: sha256:722dadc1737749e30d244f222aaa1d8b845bc93f4a573b16f662719e58b49bcd
    excerpt: "The story gate re-resolves every `provenance[]` and `context[]` entry as well as `commands`."
  - source: docs/design/10-sequencer-and-contracts.md#5-2-validation-order
    hash: sha256:9f1bf77b7e84302ff6f3f20260228d57390cc97ab8e8d3f68f52c3ff2658aab8
    excerpt: "The path rules in step 11 are absolute and no receipt may waive them."
  - source: docs/design/10-sequencer-and-contracts.md#5-4-transition-oracles
    hash: sha256:ffa41b5d270dc260e28fa9f6bdbc855069a6e922d1148c74b25860dba63484dc
    excerpt: "| `report_only` | the shared invariants only; from a judge, `changed[]` is empty, and every `evidence_refs` entry that is a findings path exists under this run's own `evidence/<agent>/` | the fence held and the stack policy holds |"
  - source: docs/design/10-sequencer-and-contracts.md#6-handoff-envelope
    hash: sha256:747b6340fc5c2348aad33ca5488012808670b3503b311d7b7d0f1204625afd4c
    excerpt: "| Source basis | `source_basis[] {source, hash, status}` | no | the `provenance` and `context` entries the gate re-resolved |"
  - source: docs/design/10-sequencer-and-contracts.md#10-evidence-files
    hash: sha256:4eebadd862a3dfd90bc0afff8342a1b18a76b2a4fe1ec5bafa23cea390f48984
    excerpt: "| `.devforgeai/provenance/log.jsonl` | JSONL | every write operation | `analyze`, `retro`, `drift` |"
  - source: docs/design/11-artifact-registry.md#1-template-registry
    hash: sha256:09607ea79839ab215871d87e8221166e14eeb6ca26f8372e4ead4173f1d92907
    excerpt: "| `analyze-report` | `.devforgeai/skills/analyze/templates/analyze-report.md` | 1 | `^FIND-[0-9]{3}$` | slug, template, template_version, status, depends_on | Orphans, Gaps, Stale Hashes, Actions |"
  - source: docs/design/11-artifact-registry.md#3-depends-on-edges
    hash: sha256:f3c304ff840d2027432f743288bccec0ea5bc5d7b99b7f41c8d524b1c3591da2
    excerpt: "| `analyze-report` | every prd, epic, story and constitution anchor it walked |"
  - source: docs/design/11-artifact-registry.md#4-upstream-and-downstream-per-skill
    hash: sha256:cfcaef76005176490e96b9e67c8fa4f0b7a6a2e13b6badf856468881fbe25200
    excerpt: "\"Upstream\" is what the skill's gate consumes; \"downstream\" is the skill that gates on what it produced."
  - source: docs/design/02-skill-roster.md#analyze
    hash: sha256:2ce12ae1084231862186eba7f234a81decee638f44b47a84f007d4318d1331ce
    excerpt: "- Reports orphans (story with no PRD requirement), gaps (requirement with no story), stale hashes."
  - source: docs/design/02-skill-roster.md#handoff-decision-tables
    hash: sha256:1dac784b4670cc7559f323011dfe304dfe8c0baf349063162f90d76d902c5d3c
    excerpt: "| analyze | clean | `/dev {first_story}` |"
  - source: docs/design/05-subagent-sets.md#sets-per-skill
    hash: sha256:9e12f3beb236a025c18d40e741c09ba675bd71d2d87f56e2b205c7556b944bf9
    excerpt: "| analyze | cross-referencer, orphan-finder, stale-hash-finder, report-writer |"
  - source: docs/design/05-subagent-sets.md#contract-format
    hash: sha256:23d8c21c51ca70b053f4661b32249b86a330c816e02db1219be72d5a9bc07a4e
    excerpt: "`must_not` is compiled into the agent prompt verbatim."
  - source: docs/design/07-purpose-and-enforcement.md#2-the-problem-in-concrete-terms
    hash: sha256:aa195bc0696dcc9da2f3511b7e03bac418430231f83e3f2ced3f71a4fa585917
    excerpt: "| Writes artifacts it was never asked for |"
  - source: docs/design/12-post-mvp.md#pm-10
    hash: sha256:d10737be0438d174c382128493b7619bfd0016f8d1a57cdf11239955b0d64f34
    excerpt: "Rung 4 stays named in `07-purpose-and-enforcement.md` as external and unimplemented; its refusals are listed there, its implementation is this entry."
---

# Skill Specification: analyze

A stranger with no conversation history must be able to build this skill from this document alone. Every question the generator would otherwise ask is answered below.

## 0. Generator instructions

These instructions are addressed to the skill-generating agent (Anthropic's `skill-creator` skill, or DevForgeAI's `skill-generator`). They replace its interview.

### Cold-session prompt

Paste this into a fresh session from the repository root:

```
Use the skill-creator skill to build the skill specified in docs/design/specs/SKILL-SPEC-011-analyze.md.
Follow its section 0 exactly. Output directory: ./out. Eval mode: quick.
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
6. **Output location** is given in the prompt. Create `./out/analyze/`. Do not write anywhere else except the `analyze-workspace/` sibling that eval runs require.
7. **On ambiguity, stop before output.** If the spec is still `draft`, contains an unresolved authoring assumption, omits a section, contradicts itself, or leaves a decision this document does not make, do not guess and do not write candidate skill files. End with a list titled `SPEC GAPS` naming each section and question. The spec author fixes and approves the spec before re-running.
8. **Fidelity over creativity.** Use the description in section 3 verbatim. Use the worker contracts in section 7d verbatim as `agents/<role>.md` bodies, adding only the framing the grader agent in skill-creator uses (Role, Inputs, Process, Output). Do not add steps, tools, or behaviours the spec does not mention.
9. **Finish with the acceptance checks** in section 14 and include their output in your final message.

## 1. Identity

| Field | Value |
|-------|-------|
| name | `analyze` (kebab-case, 7 characters, equals the directory name, no `claude`/`anthropic` prefix) |
| title | Provenance Chain Audit |
| purpose | Walk the whole chain from PRD requirements through epics and stories to the constitution sections and sealed research references they cite, and report every story with no requirement, every requirement with no story, and every citation whose source, anchor or digest no longer holds. |
| category | devforgeai-phase |
| version | 1.0.0 (skill-package version written to `metadata.version`; not the DevForgeAI or Research Core version) |

## 2. Problem and requirements

**Without this skill:** each gate checks one artifact on entry and nothing checks the chain. `01-skill-anatomy.md#provenance-chain` states the division exactly: "Gate checks one artifact on entry; `/analyze` walks the whole chain." The failures that live in the gap are named in `07-purpose-and-enforcement.md` section 2. "Writes artifacts it was never asked for" appears as an orphan: a story nobody can trace to a requirement, which passes its own gate perfectly because a gate never looks upward. The mirror image is a requirement with no story, which no gate can see at all because no artifact references it. "Gate is prose the model may ignore" appears as the third class: a story whose context excerpt was copied from a constitution section that has since been amended, which keeps passing until the day a gate happens to re-resolve it, by which time work has been built on a rule that no longer exists.

| ID | Kind | Requirement |
|----|------|-------------|
| R1 | explicit | Take one project slug and walk PRD requirements to epics, epics to stories, and stories to the constitution, architecture and research references their `provenance[]` and `context[]` entries name. Source: `02-skill-roster.md#analyze`. |
| R2 | explicit | Report orphans (a story or epic with no upstream requirement), gaps (a requirement no story covers) and stale hashes, each as an addressable `FIND-NNN` row. Source: `11-artifact-registry.md` section 1. |
| R3 | explicit | Give each finding an action a human can run: a re-slice for a stale bundle, a re-plan for a gap, a deletion or a promotion for an orphan. Source: `02-skill-roster.md#handoff-decision-tables`. |
| R4 | implicit | Write one report and change nothing else. The fence `docs/reports/analyze-<slug>.md` is the whole authority of the run; an auditor that repaired what it found would remove the evidence it exists to produce. |
| R5 | implicit | A research reference is a sealed RUN plus its applicable Source, Evidence and Claim ids and the sealed manifest digest. A bare digest is not a provenance reference and is reported as one of the unresolvable rows. Source: `01-skill-anatomy.md#provenance-chain`. |
| R6 | discovered | No worker can compute a SHA-256, so the `stale_hashes` phase reports the digest rows the sequencer already resolved and the malformed or placeholder digests it can see by reading. Section 9 records exactly which of the three classes is deterministic today and which is not. |
| R7 | discovered | A heading inside a fenced code block truncates a section under the hash rule, because neither the rule nor `docs/design/specs/verify.py` tracks fences. An anchor can therefore resolve to fewer bytes than a reader expects. Section 9 records this as a distinct finding class. |
| R8 | discovered | `analyze` is a plain document skill, so its gate checks the fence and nothing else. The chain it audits is never gated on entry, which is why the audit exists. Source: `10-sequencer-and-contracts.md` section 4. |

## 3. Description

```yaml
description: >
  Audit the whole provenance chain of one project at once: walk PRD requirements to epics, epics
  to stories, and stories to the constitution, architecture and sealed research references they
  cite, then write one report listing every story with no requirement behind it, every
  requirement no story covers, and every citation whose source, anchor or digest no longer holds.
  Use this skill before starting a sprint, after a plan run, after amending an architecture
  document, when someone asks whether the plan still matches the requirements, whether anything
  was missed, where a story came from, or why a gate is complaining about a stale hash. Every
  finding gets a numbered row and a command that fixes it. Do NOT use it to write or re-slice
  stories (use plan), to change an architecture document (use amend), to compare documents
  against code (use drift), or to check one story before coding (that is the dev gate).
```

Character count: 912 / 1024.

## 4. Trigger set

```json
[
  {"query": "/analyze shop", "should_trigger": true},
  {"query": "before we start sprint two, check nothing in the plan is orphaned", "should_trigger": true},
  {"query": "does every requirement in the billing PRD actually have a story", "should_trigger": true},
  {"query": "i amended constitution.md yesterday. which stories are now stale", "should_trigger": true},
  {"query": "where did STORY-014 come from? i cannot find a requirement for it", "should_trigger": true},
  {"query": "dev keeps refusing STORY-009 for a stale hash, work out what broke across the whole plan", "should_trigger": true},
  {"query": "audit the traceability for tinyapp end to end and give me a list of what to fix", "should_trigger": true},
  {"query": "plan finished. is the plan complete or did it miss something", "should_trigger": true},
  {"query": "we have 40 stories and 12 requirements and i do not trust the mapping", "should_trigger": true},
  {"query": "check the research citations in our stories still point at sealed runs", "should_trigger": true},
  {"query": "re-slice STORY-009 so its context bundle is current again", "should_trigger": false},
  {"query": "break EPIC-002 into stories for the next sprint", "should_trigger": false},
  {"query": "the constitution needs a new rule about logging, add it", "should_trigger": false},
  {"query": "does the architecture doc still describe what the code does", "should_trigger": false},
  {"query": "implement STORY-003", "should_trigger": false},
  {"query": "criterion 2 of STORY-011 is ambiguous, get an answer", "should_trigger": false},
  {"query": "review the diff on STORY-007 for security problems", "should_trigger": false},
  {"query": "run the test suite and tell me what fails", "should_trigger": false},
  {"query": "write a retrospective covering sprint-001", "should_trigger": false},
  {"query": "analyze this CSV of sales figures and find the trend", "should_trigger": false}
]
```

## 5. Use cases

### UC-1: Pre-sprint audit, clean chain
- **User says:** "/analyze shop"
- **Steps:** 1. `devforgeai phase start analyze shop` runs the document fence gate over `docs/reports/analyze-shop.md` and opens the run. 2. `cross_referencer` reads the PRD, every epic and every story and returns the requirement-to-epic-to-story edge list in its receipt. 3. `orphan_finder` returns the artifacts with no upstream edge. 4. `stale_hash_finder` returns one row per citation, marking each resolved, stale, unresolvable or unchecked. 5. `analyze_report_writer` writes `docs/reports/analyze-shop.md` inside the candidate root with the four required sections, each row numbered `FIND-NNN`, and an action for every row.
- **Result:** a report whose Orphans, Gaps and Stale Hashes sections are empty and whose Actions section says so, and a handoff whose first next step is `/dev STORY-001`.

### UC-2: After an amendment
- **User says:** "i amended constitution.md yesterday. which stories are now stale"
- **Steps:** 1. The gate opens the run over the slug in `state.yaml`. 2. `cross_referencer` builds the edge list as before. 3. `stale_hash_finder` reads each story's `context[]` entries, reads the `source_basis[]` rows the sequencer recorded in every `.devforgeai/work/*/handoff.json`, and reads `.devforgeai/provenance/log.jsonl`, then marks each citation of the amended anchor stale where a recorded row says so and unchecked where no run has re-resolved it since. 4. `analyze_report_writer` writes one `FIND-NNN` row per affected story with `/plan {slug} --reslice {story}` as its action.
- **Result:** `docs/reports/analyze-<slug>.md` names each affected story and the exact command per row, and the handoff lists the re-slices before the forward command.

### UC-3: An orphan and a gap in the same plan
- **User says:** "we have 40 stories and 12 requirements and i do not trust the mapping"
- **Steps:** 1. The gate opens the run. 2. `cross_referencer` returns the edge list. 3. `orphan_finder` returns one row for a story whose `provenance[]` names an epic anchor that no epic file contains, and one row for a requirement anchor no story cites. 4. `analyze_report_writer` writes the first under `## Orphans` and the second under `## Gaps`, each with its action.
- **Result:** a report distinguishing the two directions of the same break, so a human deletes or re-parents the orphan and re-plans for the gap rather than guessing which.

## 6. Inputs and outputs

### Inputs
| Input | Format | Example file | Required |
|-------|--------|--------------|----------|
| project slug | positional argument, kebab-case | `shop` | yes |
| PRD | markdown with frontmatter, `prd` template, owned by `pm` | `docs/design/examples/fixtures/analyze/docs/PM/tinyapp/prd.md` | yes |
| epics | markdown, `epic` template, owned by `plan` | `docs/plan/<slug>/epics/EPIC-NNN.md` | yes |
| stories | markdown, `story` version 3, owned by `plan` | `docs/plan/<slug>/stories/STORY-NNN.md` | yes |
| sprints | markdown, `sprint` template, owned by `plan` | `docs/plan/<slug>/sprints/sprint-NNN.md` | no |
| constitution set | markdown, owned by `architect` | `docs/architecture/constitution.md` | yes |
| recorded gate verdicts | JSON, `source_basis[]` rows inside each run's handoff | `.devforgeai/work/<run>/handoff.json` | no; absent on a project no gate has opened |
| provenance log | JSONL, one line per write operation | `.devforgeai/provenance/log.jsonl` | no |
| `.devforgeai/state.yaml` enforcement block | YAML, written by the sequencer at `devforgeai phase start` | `.devforgeai/state.yaml` | yes; the run's `write_fence` is read from it |

### Outputs
| Output | Format | Location | Template |
|--------|--------|----------|----------|
| analysis report | markdown | `docs/reports/analyze-<slug>.md` | `analyze-report`, seeded by `assets/analyze-report.md` |
| phase results | JSON, written by the sequencer | `.devforgeai/work/analyze-<slug>/<phase>-result.json` | none |
| phase reports | markdown, written by the sequencer | `.devforgeai/work/analyze-<slug>/<phase>-report.md` and `docs/reports/analyze-analyze-<slug>-<phase>.md` | none |
| handoff | JSON plus its rendering | `.devforgeai/work/analyze-<slug>/handoff.json` | `handoff` |

The `analyze-report` template header, from `11-artifact-registry.md` section 1: `template_version` 1, `id_pattern` `^FIND-[0-9]{3}$`, `required_frontmatter` slug, template, template_version, status, depends_on, `required_sections` Orphans, Gaps, Stale Hashes, Actions. `forbidden_text` carries the same five entries as every other template — the two words meaning "not written yet", the opening and closing double-brace placeholder markers, and the angle-bracketed fill-in marker.

`analyze` is the one skill whose `depends_on` is open-ended: it lists every prd, epic, story and constitution anchor it walked, so the report itself is re-checkable.

### Output template

````
---
slug: shop
template: analyze-report
template_version: 1
status: complete
depends_on:
  - source: docs/PM/shop/prd.md#requirements
    hash: sha256:0000000000000000000000000000000000000000000000000000000000000000
  - source: docs/plan/shop/epics/EPIC-001.md#stories
    hash: sha256:0000000000000000000000000000000000000000000000000000000000000000
---

# Analysis: shop

Walked 3 requirements, 3 epics, 12 stories, 41 citations.

## Orphans

| id | artifact | why | action |
|---|---|---|---|
| FIND-001 | docs/plan/shop/stories/STORY-014.md | `provenance[0]` names `EPIC-004.md#stories`, and no epic file with that id exists | `/plan shop` to re-parent it, or delete the story |

## Gaps

| id | requirement | why | action |
|---|---|---|---|
| FIND-002 | docs/PM/shop/prd.md#requirements REQ-005 | no story's `provenance[]` names this anchor | `/plan shop` |

## Stale Hashes

| id | citation | verdict | action |
|---|---|---|---|
| FIND-003 | STORY-009 `context[1]` docs/architecture/constitution.md#style | stale: `source_basis` in `.devforgeai/work/STORY-009/handoff.json` recorded `stale-hash` at the last gate | `/plan shop --reslice STORY-009` |
| FIND-004 | STORY-011 `commands.hash` | unresolvable: the recorded digest is a placeholder, not sixty-four hex characters | `/plan shop --reslice STORY-011` |
| FIND-005 | STORY-003 `context[0]` docs/architecture/architecture.md#components | unchecked: no recorded gate verdict since the last write to that file | `/analyze shop` after the next gate, or `/plan shop --reslice STORY-003` |

## Actions

1. `/plan shop` — covers FIND-001 and FIND-002.
2. `/plan shop --reslice STORY-009` — covers FIND-003.
3. `/plan shop --reslice STORY-011` — covers FIND-004.
4. `/amend architecture "re-anchor the components section STORY-003 cites"` — covers FIND-005 when the section itself is what moved.
````

Every row carries a `FIND-NNN` id, allocated in one sequence across all three sections so a human can name a finding without naming its section. The four `Stale Hashes` verdicts are the closed set: `resolved`, `stale`, `unresolvable`, `unchecked`. Section 9 records which of the four this skill can determine deterministically.

### Return envelope (DevForgeAI-anatomy skills only)

One schema, both providers: `devforgeai.worker-result/v1`, normative in `schemas/devforgeai/v1/worker-result.schema.json`. A producer writes its own file inside the candidate root with Edit and Write (Codex: `apply_patch`) and names what it wrote; a judge writes nothing and names nothing. The receipt is a claim, not a payload. At `devforgeai ingest-result` the sequencer derives `changed[{path, blob_sha256, kind}]` from the candidate root's checkpoint diff, refuses the result when `changed` is not a subset of `claimed_paths` (`UNCLAIMED_CHANGE`) or when any changed path is outside the fence, runs the transition oracle inside the root, writes `<phase>-result.json` with `changed` and the checkpoint ref, creates the next checkpoint and releases the lease.

```yaml
schema: devforgeai.worker-result/v1
run: "analyze-shop"
skill: "analyze"
phase: "stale_hashes"
agent: "stale_hash_finder"
status: pass | fail | needs_user | could_not_run
reason_code: runner_missing | timeout | network | hook_fault   # required only when status is could_not_run
candidate:
  id: "analyze-shop"
  input_checkpoint: "orphans"
claimed_paths: []          # root-relative, at most 64; empty for a judge and for any non-pass status
evidence_refs: []          # at most 16 paths, root-relative or under .devforgeai/work/<run>/
note: "41 citations examined, 3 not resolved"
issues: [{id, kind, text}] # at most 10
next: ""                   # requires status fail and a registry rewind_to; no analyze phase declares one
```

Unknown keys are refused. A judge writes its full findings file under `.devforgeai/work/<run>/evidence/<agent>/` — run-scoped scratch that is gitignored, lies outside the candidate root and is never promoted — and names it in `evidence_refs`; `issues[]` carries the bounded summary a reader sees in the handoff.

`gate_policy` (`BLOCK | REQUIRE_HUMAN | WARN | OFF`) is a defect-to-action map declared in the consumed artifact, never a status returned here. `analyze` is a plain document run, so it carries the fixed map `{unresolvable_source: BLOCK}`. The wider maps the stories it audits declare are data it reports, not policy it obeys.

## 7. Procedure

### 7a. Steps

The body of `SKILL.md`. Imperative voice; each step says why it matters.

1. Parse the positional slug. Read nothing else in this window — why: anything read here stays in the primary window for the whole run, and the primary-window contract forbids opening an artifact. An audit skill is the easiest place to violate that, because the temptation is to read the chain in the window that reports it.
2. Call `devforgeai phase start analyze <slug>`. On exit 1, print the defect list the gate wrote to stderr and stop — why: the gate takes the snapshot the run's fence restores from, so a refusal leaves nothing half-applied.
3. Dispatch `agents/cross_referencer.md` with the slug, the PRD path, the epics and stories directories and the constitution path — why: it builds the edge list every later phase reads, so it runs first and once.
4. Dispatch `agents/orphan_finder.md` with `.devforgeai/work/<run>/cross_reference-result.json`.
5. Dispatch `agents/stale_hash_finder.md` with `.devforgeai/work/<run>/cross_reference-result.json`, the `.devforgeai/work/` directory and `.devforgeai/provenance/log.jsonl`. Load `references/stale_hashes.md` before the dispatch — why: which verdict a worker may reach without computing a digest is the one rule this skill is easiest to get wrong.
6. Dispatch `agents/analyze_report_writer.md` with every prior result path.
7. Advance on a returned `pass`; stop and print on `needs_user` or `could_not_run` — why: `needs_user` blocks the run at that phase immediately without consulting the attempt counter, so there is nothing left to dispatch until the user has acted and re-runs `/analyze {slug}`.
8. Print the block the sequencer rendered into `.devforgeai/work/<run>/handoff.json`, verbatim. Compose nothing — why: the renderer adds nothing to the envelope, and `devforgeai status` must print the identical block from a cold session.
9. When that block reports the run `ready_to_promote` and the user asks for the promotion, call `devforgeai promote <run>`, then print the second block the promotion rendered — why: promotion is never automatic, it is what moves `docs/reports/analyze-<slug>.md` from the candidate root into the canonical checkout under the lock, and a `REQUIRE_HUMAN` block is the only state in which the model may ask for it.

A transition failure is not the primary window's business: `devforgeai phase next` exits 1 with the oracle's problem rows, the dispatcher turns that into a non-zero exit the worker sees, and the same worker returns a fresh envelope. The primary window dispatches once per phase.

Every phase of one run works inside the same candidate root — `.devforgeai/work/<run>/wt`, created by `devforgeai phase start` and named to each worker as `candidate.root` in the status block the primary window pastes into the dispatch prompt alongside `run`, `phase`, `fence` and `granted_keys`. Three of the four phases are judges: they write nothing in the root, and their findings files go to `.devforgeai/work/<run>/evidence/<agent>/`, which is outside it. Only `report` writes in the root, and it writes one file there. The sequencer checkpoints the root at each transition, so the phases build linearly with no merge between them; exactly one producer holds the run's lease at a time, granted at dispatch and released at `devforgeai ingest-result`, and judges hold no lease. Promotion is never automatic and is no part of Handoff: the last passing `devforgeai phase next` marks the run `ready_to_promote` and writes a `REQUIRE_HUMAN` handoff whose only forward step is `devforgeai promote <run>`, and `SKILL.md` runs that command only after the user confirms in the session. That command, not the transition, is what merges the candidate root into the canonical checkout under `.devforgeai/lock`, and it is what refuses with `STALE_BASE` when canonical HEAD has moved past the run's recorded `base_ref`, with `DIRTY_TARGET` when a canonical file among the run's changed paths is dirty, and with `MERGE_CONFLICT` when a rebase inside the root conflicted; a refused promotion leaves the run `ready_to_promote` with its candidate root intact for a retry.

### 7b. Sub-phases and workers

Gate, Record and Handoff dispatch no LLM: they are `devforgeai` sequencer operations, and so is Slice: `devforgeai phase start` resolves the incoming artifact's already-hashed context bundle and writes `.devforgeai/work/<run>/context.json`, whose path every worker of the run is handed. No worker performs it (open item OI-1).

| # | Sub-phase | Performed by | Isolation |
|---|-----------|--------------|-----------|
| 0 | Gate | sequencer: `devforgeai phase start analyze <slug>` | n/a |
| 1 | Slice | sequencer: `devforgeai phase start` writes `.devforgeai/work/<run>/context.json` | n/a |
| 2 | Work: `cross_reference` | worker: `cross_referencer` | required |
| 3 | Work: `orphans` | worker: `orphan_finder` | preferred |
| 4 | Work: `stale_hashes` | worker: `stale_hash_finder` | preferred |
| 5 | Write: `report` | worker: `analyze_report_writer` | required |
| 6 | Record | sequencer: `devforgeai phase next` | n/a |
| 7 | Handoff | sequencer: `devforgeai phase next` marks the run `ready_to_promote` and writes the `REQUIRE_HUMAN` block whose only forward step is `devforgeai promote <run>`; `SKILL.md` runs that command only after the user confirms in the session, and the promotion writes the run's second handoff block | n/a |

`analyze` has no Review sub-phase. The registry gives it four phases and no critic (`10-sequencer-and-contracts.md` section 4). That is defensible for this skill in a way it would not be for a writer: three of its four phases produce findings rather than content, and the independent check on the fourth is `scripts/check_analyze_report.py`, which compares each `FIND-NNN` row in the written report to the rows the three preceding results recorded and needs no model judgement.

For an anatomy-governed skill, `SKILL.md` dispatches each worker through the selected target's provider-native worker mechanism, using the generated target profile and file paths only. It never pastes or paraphrases artifact content, objectives, or acceptance criteria into the prompt. Its Bash grammar is exactly `devforgeai status | phase start <skill> <arg> | phase fail --reason | validate | promote <run>`; every other sequencer operation is hook-only. Isolation is a declaration compiled into the target profile; runtime verification of it is `12-post-mvp.md#pm-01`.

### 7c. Evidence and gate table

One row per registry phase, in registry order. `<run>` is `analyze-<slug>`; `<phase>` is the registry phase name.

| phase | worker | deterministic gate check | gate_policy | evidence file | transition oracle |
|---|---|---|---|---|---|
| `cross_reference` | `cross_referencer` | run-level gate at `devforgeai phase start`: `analyze` is a known skill of kind `document`; no run is already active; no active or `ready_to_promote` run's fence overlaps this one (`FENCE_OVERLAP`); the fence entry `docs/reports/analyze-<slug>.md` is repository-relative, contains no `..`, and is not sequencer-owned; `candidate open` creates the root and pins `base_ref`. At `ingest-result`: the checkpoint diff of the root is empty, because the phase's `writes` mode is `evidence` and the `PreToolUse` check admits this worker's `Write` only under `.devforgeai/work/<run>/evidence/<agent>/`, which lies outside the root; a non-empty root diff is `UNCLAIMED_CHANGE` and refuses the result | document run's fixed map `{unresolvable_source: BLOCK}`; every `devforgeai phase start` defect is a refusal whatever a declared value says, and only `test_runner_missing` changes behaviour at transition time, which no `analyze` phase reaches because none brokers a command | `.devforgeai/work/<run>/cross_reference-result.json`, `cross_reference-report.md` | `report_only`: no file outside the fence changed since the input checkpoint and the whole-tree package and import policy holds |
| `orphans` | `orphan_finder` | at `ingest-result`: an empty root checkpoint diff, as `cross_reference`; `issues[]` is at most ten rows and `evidence_refs` at most sixteen paths, which bounds the summary the receipt carries, not the findings file it points at | `{unresolvable_source: BLOCK}` | `.devforgeai/work/<run>/orphans-result.json`, `orphans-report.md` | `report_only`: as `cross_reference` |
| `stale_hashes` | `stale_hash_finder` | at `ingest-result`: an empty root checkpoint diff, as `cross_reference`. The digest comparison itself is not a check this phase performs: the sequencer's gate performs it, at `devforgeai phase start` for the story it opens, and records the verdict in that run's `source_basis[]`. This phase reads those recorded verdicts. `scripts/walk_chain.py` performs the comparison directly when a human runs it | `{unresolvable_source: BLOCK}` | `.devforgeai/work/<run>/stale_hashes-result.json`, `stale_hashes-report.md` | `report_only`: as `cross_reference` |
| `report` | `analyze_report_writer` | at `ingest-result`: `changed` derived from the checkpoint diff is exactly one path, `docs/reports/analyze-<slug>.md`, it is a subset of `claimed_paths`, it canonicalises inside the candidate root, it equals the fence entry, and it is allowed by the phase's `writes: docs` mode; then the whole-tree package and import rescan. `scripts/check_analyze_report.py` parses the written file against the `analyze-report` header keys and checks that every `FIND-NNN` row cites a row from one of the three preceding results | `{unresolvable_source: BLOCK}` | `.devforgeai/work/<run>/report-result.json`, `report-report.md`, then `handoff.json` | `document`: the phase produced at least one file and every declared output with non-null content exists on disk in the root. On pass this is the last phase, and promotion is not part of it: `devforgeai phase next` marks the run `ready_to_promote` and writes a `REQUIRE_HUMAN` handoff whose only forward step is `devforgeai promote <run>`. `SKILL.md` runs that command only after the user confirms in the session; the promotion moves the report into the canonical checkout, marks the run `promoted`, clears enforcement, and writes the second handoff block, whose `next` comes from the section 7e table |

Attempt budgets, materialised into the enforcement block from the registry, are 2 for every phase. No `analyze` phase declares `rewind_to`, so a `fail` result carrying `next` is refused at `ingest-result`; a `fail` without `next` becomes a transition problem row, the phase retries to its limit, and the run then blocks `REQUIRE_HUMAN` (open item OI-4).

`scripts/check_analyze_report.py` is designed as a sequencer-side check at `devforgeai ingest-result` and is not implemented in `examples/hooks/devforgeai.py` today; `scripts/walk_chain.py` has no sequencer path at all and is a human command. Section 9 records both and what the run does without them.

### 7d. Worker contracts

Each block is a compilable subagent definition. `name` is the canonical registry worker name, because the stop event's `agent_type` is compared against it. `description` is the sentence the primary window matches when it decides to dispatch. `writes` is `candidate` for a producer and `evidence` for a judge — a judge's one write goes to `.devforgeai/work/<run>/evidence/<agent>/` and never into the candidate root — and it follows the registry's `writes` column exactly: three `analyze` phases declare `none` there, one declares `docs`. `compiled_to` names the two provider-native files `skill-generator` emits from the block. The body of each file follows `templates/agent-md.md` in four parts — job, inputs, rules, receipt — and a producer's job sentence leads with what it writes.

```yaml
name: cross_referencer
skill: analyze
description: Dispatch this worker first in an analyze run to build the edge list of the whole provenance chain for one slug, before any phase classifies a break.
writes: evidence
tools: [Read, Grep, Glob, Write, Bash(devforgeai status)]
model: inherit
skills: []
responsibility: Build the edge list of the whole chain — requirement to epic, epic to story, story to every constitution, architecture, design and research reference it cites — one row per edge, each naming both endpoints by path and anchor.
inputs:
  - .devforgeai/work/<run>/context.json, the bundle the gate sliced
  - docs/PM/<slug>/prd.md
  - docs/plan/<slug>/epics/ and docs/plan/<slug>/stories/ and docs/plan/<slug>/sprints/
  - docs/architecture/constitution.md, sourcetree.md, techstack.md, architecture.md and each design-<topic>.md
  - references/cross_reference.md, for the edge kinds and the citation forms
outputs:
  - .devforgeai/work/<run>/evidence/cross_referencer/edges.json, the full edge and node list, one row per edge with both endpoints and the frontmatter key it came from
  - issues[]: one row per edge that does not resolve, kind `edge`, at most ten
  - note: the counts of nodes, edges and unresolved edges
  - evidence_refs[]: the findings file above, then the artifact paths whose frontmatter the rows were read from
must_not:
  - infer an edge from wording; an edge exists only where a provenance, context or depends_on entry names it
  - read a file no artifact in the chain references
  - write or claim any path inside the candidate root; this phase's one write is its findings file under .devforgeai/work/<run>/evidence/cross_referencer/
isolation: required
returns: devforgeai.worker-result/v1
compiled_to:
  - .claude/agents/analyze-cross_referencer.md
  - .codex/agents/analyze-cross_referencer.toml
body: job, inputs, rules, receipt
```

```yaml
name: orphan_finder
skill: analyze
description: Dispatch this worker after cross_reference to separate the two directions of a broken edge — an artifact with no upstream requirement, and a requirement with no story.
writes: evidence
tools: [Read, Grep, Glob, Write, Bash(devforgeai status)]
model: inherit
skills: []
responsibility: Report every artifact with no upstream edge and every requirement with no downstream edge, keeping the two directions distinct.
inputs:
  - .devforgeai/work/<run>/cross_reference-result.json
  - references/orphans.md, for the orphan and gap definitions and the action per class
outputs:
  - .devforgeai/work/<run>/evidence/orphan_finder/findings.json, every orphan and every gap, each with its path and the anchor that does not resolve
  - issues[]: one row per orphan, kind `orphan`, and one per gap, kind `gap`, at most ten in total
  - note: the count of each kind, so a summary shorter than the findings file says so
  - evidence_refs[]: the findings file above and .devforgeai/work/<run>/cross_reference-result.json
must_not:
  - report an orphan and a gap for the same break; a broken edge is one or the other, decided by which endpoint is missing
  - report an artifact the cross_reference findings file does not list as a node
  - write or claim any path inside the candidate root; this phase's one write is its findings file under .devforgeai/work/<run>/evidence/orphan_finder/
isolation: preferred
returns: devforgeai.worker-result/v1
compiled_to:
  - .claude/agents/analyze-orphan_finder.md
  - .codex/agents/analyze-orphan_finder.toml
body: job, inputs, rules, receipt
```

```yaml
name: stale_hash_finder
skill: analyze
description: Dispatch this worker after cross_reference to verdict every citation in the chain against the gate verdicts already recorded, when a user asks which stories a document change made stale.
writes: evidence
tools: [Read, Grep, Glob, Write, Bash(devforgeai status)]
model: inherit
skills: []
responsibility: Give every citation in the chain one of the four verdicts — resolved, stale, unresolvable, unchecked — from the gate verdicts already recorded and from what the citation itself shows.
inputs:
  - .devforgeai/work/<run>/cross_reference-result.json
  - .devforgeai/work/, for every run's handoff.json and its source_basis rows
  - .devforgeai/provenance/log.jsonl
  - the cited files themselves, to test whether each source exists and each anchor resolves
  - references/stale_hashes.md, for the four verdicts and which of them this worker may reach
outputs:
  - .devforgeai/work/<run>/evidence/stale_hash_finder/citations.json, one row per citation in the chain with its verdict and the basis for that verdict
  - issues[]: one row per citation that is not resolved, kind `citation`, carrying the verdict and its basis, at most ten
  - note: the count of citations in each of the four verdicts
  - evidence_refs[]: the findings file above, then the handoff.json and log.jsonl paths whose recorded verdicts the rows cite
must_not:
  - report a verdict of resolved or stale from its own reading; both require a digest comparison, and the basis is a recorded gate verdict or nothing
  - report a research citation as resolved when it names a digest without its RUN, Source, Evidence and Claim ids and the sealed manifest digest
  - write or claim any path inside the candidate root; this phase's one write is its findings file under .devforgeai/work/<run>/evidence/stale_hash_finder/
isolation: preferred
returns: devforgeai.worker-result/v1
compiled_to:
  - .claude/agents/analyze-stale_hash_finder.md
  - .codex/agents/analyze-stale_hash_finder.toml
body: job, inputs, rules, receipt
```

```yaml
name: analyze_report_writer
skill: analyze
description: Dispatch this worker last in an analyze run to write the one analysis report from the three preceding phase results, once every finding phase has returned.
writes: candidate
tools: [Read, Grep, Glob, Edit, Write, Bash(devforgeai status)]
model: inherit
skills: []
responsibility: Write the one report inside the candidate root, rendering every row from the three preceding phases as a numbered finding with an action, and listing the actions in the order a human should run them.
inputs:
  - .devforgeai/work/<run>/cross_reference-result.json, orphans-result.json and stale_hashes-result.json, and the findings files their evidence_refs name under .devforgeai/work/<run>/evidence/
  - assets/analyze-report.md, the template skeleton
  - references/report.md, for the header keys, the FIND numbering rule and the action vocabulary
outputs:
  - docs/reports/analyze-<slug>.md, written under the candidate root with Edit or Write and named in claimed_paths
  - evidence_refs[]: the three preceding result paths and the three findings files the rows were rendered from
must_not:
  - write a finding no row in a preceding phase's findings file supports
  - write or claim any path other than the run's single fence entry
  - give a finding an action that is not one exact command
isolation: required
returns: devforgeai.worker-result/v1
compiled_to:
  - .claude/agents/analyze-analyze_report_writer.md
  - .codex/agents/analyze-analyze_report_writer.toml
body: job, inputs, rules, receipt
```

A judge's tools are `Read`, `Grep`, `Glob`, `Write` and `Bash(devforgeai status)`. Its `Write` is admitted only under `.devforgeai/work/<run>/evidence/<agent>/` — run-scoped scratch, gitignored, outside the candidate root and never promoted — so a judge can record a finding set larger than the receipt without being able to touch what it judges. A producer holds `Edit` and `Write` inside the candidate root — `apply_patch` on the Codex target — and `Bash(devforgeai run *)` for the stack keys its phase grants; `analyze` grants none, so no worker here carries it. No worker holds a git write, a package manager, a network tool or a raw stack command (open item OI-3). `isolation` in the blocks above is the framework's own `required | preferred` declaration that the worker run in its own window; it is not Claude's subagent `isolation` key, which the framework never sets because its one value forks a worktree from HEAD and would split the run's linear history. `hooks`, `memory`, `background` and `permissionMode` are Claude-only subagent frontmatter keys and this skill leaves all four unset, so the compiled Claude file carries `name`, `description`, `tools` and `model` and the Codex profile carries the portable equivalents.

### 7e. Handoff outcomes

The `handoff.outcomes` block the skill declares. The sequencer selects the row by envelope status and fills `{slug}`, `{story}`, `{doc}` and `{first_story}` from state; `{change}` is the one-line change request the reader supplies from the finding row.

| Outcome | Next steps |
|---------|------------|
| pass, last phase, run `ready_to_promote` and not yet promoted | 1. `devforgeai promote {run}` — the first of the run's two handoff blocks; `SKILL.md` runs the command only after the user confirms in the session, and the promotion writes the second block, which carries whichever `pass` row below matches |
| pass, promoted, no findings | 1. `/dev {first_story}` |
| pass, promoted, stale or unresolvable citation rows | 1. `/plan {slug} --reslice {story}` for each row listed in the open items, then 2. `/dev {first_story}` |
| pass, promoted, a cited section itself moved | 1. `/amend {doc} "{change}"` for each row listed in the open items, then 2. `/dev {first_story}` |
| pass, promoted, orphan or gap rows | 1. `/plan {slug}`, then 2. `/dev {first_story}` |
| needs_user | 1. resolve the open items named in the handoff, then 2. `/analyze {slug}`, which resumes the blocked run at `run.yaml#blocked_at` with attempts reset — the run stayed `active` and kept its candidate root. Also possible: `devforgeai phase fail --reason <text>` to abandon the root, then `/status` |
| fail at `max_attempts` | 1. fix the cause the `open_items` name, then `/analyze {slug}`, which resumes the blocked run at `blocked_at` with attempts reset. Also possible: `devforgeai phase fail --reason <text>` to abandon the root, then `/status` |
| could_not_run, `reason_code: hook_fault` | 1. reinstall the dispatcher named in `.devforgeai/sessions/`, then 2. `/analyze {slug}` |
| could_not_run, any other `reason_code` | 1. the repair route for that reason code, then 2. `/analyze {slug}` |
| BLOCK, recorded by `devforgeai phase fail --reason` | 1. `/status` |

A gate refusal is not a row in this table. `devforgeai phase start` exits 1 with the defect list and writes no handoff (`10-sequencer-and-contracts.md` section 3.2), so a gate row would be unreachable. `02-skill-roster.md` gives `analyze` two outcomes, clean and findings; the rows above split the findings outcome by which command fixes it, because rule 3 of the handoff rendering rules requires exactly one numbered forward path and a row that offered two commands could not satisfy it.

## 8. Bundled resources

### Layout (fixed)

```
analyze/SKILL.md            # at most 500 lines: identity, phase list, dispatch loop, handoff table
  references/cross_reference.md
  references/orphans.md
  references/stale_hashes.md
  references/report.md
  references/envelope.md
  agents/cross_referencer.md
  agents/orphan_finder.md
  agents/stale_hash_finder.md
  agents/analyze_report_writer.md
  scripts/walk_chain.py
  scripts/check_analyze_report.py
  assets/analyze-report.md
```

Link depth: `SKILL.md` links to `references/`, `agents/`, `scripts/` and `assets/`; an `agents/*.md` links to `references/*.md`; nothing links further.

### scripts/

Both scripts are deterministic, non-interactive, print data to stdout and diagnostics to stderr, and document `--help`.

| File | Purpose | Invocation | Exit codes |
|------|---------|------------|------------|
| `walk_chain.py` | Walk the chain for one slug and emit the authoritative row set as JSON: every edge, every orphan, every gap, and every citation with a digest verdict computed directly by the hash rule in `10-sequencer-and-contracts.md` section 3.4 — resolve `path#anchor`, normalise CRLF to LF, join with LF, append one trailing LF, SHA-256 the UTF-8 bytes. This is the only place in the skill where a digest is recomputed, and it is invoked by a human: no worker may run it, and no sequencer path imports it (section 9). Its output is what a human compares against the report when a verdict of `unchecked` is not good enough | `python3 scripts/walk_chain.py SLUG [--root PATH] [--json]` | 0 walked with no unresolved rows, 1 walked with at least one stale or unresolvable row, 2 usage or the slug has no plan directory |
| `check_analyze_report.py` | Validate a written report against the `analyze-report` header keys, id pattern, required sections and forbidden text, and check that every `FIND-NNN` row cites a row present in the three phase results. Invoked by a human, and designed to be imported by the sequencer at `devforgeai ingest-result` for the `report` phase; that import is not implemented today (section 9) | `python3 scripts/check_analyze_report.py PATH [--results DIR] [--json]` | 0 pass, 1 defects listed on stdout, 2 usage |

### references/

| File | Content | Load when |
|------|---------|-----------|
| `cross_reference.md` | The edge kinds and where each comes from: a story's `provenance[]` to its epic anchor and its PRD requirement anchor; a story's `context[]` to a constitution, sourcetree, techstack, architecture or design anchor, or to a source line range; an epic's `depends_on` to constitution sections; a sprint's `stories` list to story ids; a research citation, which is a sealed RUN plus its applicable Source, Evidence and Claim ids and the sealed manifest digest. The rule that an edge exists only where a frontmatter entry names it. | dispatching `cross_referencer` |
| `orphans.md` | The two directions: an orphan is an artifact whose upstream anchor does not resolve to an existing artifact; a gap is a requirement anchor no story cites. Why one break yields one row and not two, and the action per class. | dispatching `orphan_finder` |
| `stale_hashes.md` | The four verdicts and their bases. `resolved` and `stale` require a digest comparison and may be reported only from a recorded `source_basis[]` row or a `provenance/log.jsonl` line. `unresolvable` may be reported from reading alone, in three cases: the source file does not exist, the anchor does not resolve to a heading or line range, or the recorded digest is not sixty-four hexadecimal characters after the `sha256:` prefix. `unchecked` is the default for a citation with no recorded verdict. Also: a heading inside a fenced code block ends a section under the hash rule, so an anchor may resolve to fewer bytes than a reader expects, and the excerpt a story carries may sit outside them — reported as its own row rather than as a stale hash. | dispatching `stale_hash_finder` |
| `report.md` | The `analyze-report` header keys, the single `FIND-NNN` sequence across all three sections, what belongs under each of the four headings, and the action vocabulary: one exact command per row, drawn from the same set the handoff table uses. | dispatching `analyze_report_writer` |
| `envelope.md` | The `devforgeai.worker-result/v1` schema, its bounds, and the closed status set with `reason_code`. | every dispatch |

### assets/

| File | Used for |
|------|----------|
| `analyze-report.md` | `docs/reports/analyze-<slug>.md` skeleton: the five frontmatter keys, the four required section headings, and the column headers of each section's table, with no rows. |

### agents/

| File | Worker (from section 7d) | writes | tools | compiled to |
|------|-------------------------|--------|-------|-------------|
| `cross_referencer.md` | `cross_referencer` | evidence | Read, Grep, Glob, Write, Bash(devforgeai status) | `.claude/agents/analyze-cross_referencer.md`, `.codex/agents/analyze-cross_referencer.toml` |
| `orphan_finder.md` | `orphan_finder` | evidence | Read, Grep, Glob, Write, Bash(devforgeai status) | `.claude/agents/analyze-orphan_finder.md`, `.codex/agents/analyze-orphan_finder.toml` |
| `stale_hash_finder.md` | `stale_hash_finder` | evidence | Read, Grep, Glob, Write, Bash(devforgeai status) | `.claude/agents/analyze-stale_hash_finder.md`, `.codex/agents/analyze-stale_hash_finder.toml` |
| `analyze_report_writer.md` | `analyze_report_writer` | candidate | Read, Grep, Glob, Edit, Write, Bash(devforgeai status) | `.claude/agents/analyze-analyze_report_writer.md`, `.codex/agents/analyze-analyze_report_writer.toml` |

## 9. Gotchas and edge cases

| Situation | What goes wrong | What to do instead |
|-----------|-----------------|--------------------|
| OI-1: which component performs Slice | The generated skill grows a fifth agent file with no registry phase to run it | Slice is a sequencer step inside `devforgeai phase start`: it resolves the incoming artifact's already-hashed context bundle and writes `.devforgeai/work/<run>/context.json`, which every worker of the run is handed. No framework worker performs it and this package ships no agent file for it. |
| OI-2: provenance conformance at the gate | An `analyze` spec that described the gate as re-resolving the chain would make the skill redundant | `10-sequencer-and-contracts.md` section 3.4 carries full re-resolution, but only for the one story a story gate opens, and section 4 makes `qa` and `review` the only story-anchored document skills. `analyze`'s own gate is the fence gate alone. Nothing in the framework checks the chain as a whole at any gate, which is why this skill exists and why `01-skill-anatomy.md#provenance-chain` divides the two jobs the way it does. |
| OI-3: worker tools | A generator either gives every worker the same tool list — which would let `stale_hash_finder` shell out and compute digests, hiding the honest gap below — or gives the report writer no way to write | Tools are per role. The three judges hold `Read`, `Grep`, `Glob`, `Write` and `Bash(devforgeai status)`, with `Write` admitted only under `.devforgeai/work/<run>/evidence/<agent>/`. `analyze_report_writer` is a producer and holds `Edit` and `Write` (Codex `apply_patch`) scoped to the candidate root by the `PreToolUse` check. No `analyze` phase grants a stack key, so no worker carries `Bash(devforgeai run *)`, and no worker holds a git write, a package manager or a network tool. `walk_chain.py` is therefore a human command, not a worker tool. |
| OI-4: no outcome row for `status: fail` with no `next` | A reader assumes a failing phase passes silently | `examples/hooks/devforgeai.py` inserts `"<agent> reported fail"` as a transition problem row, so the phase retries to `max_attempts: 2` and then blocks `REQUIRE_HUMAN`. The `fail at max_attempts` row in section 7e is that path. |
| OI-5: `--reslice` appears in this skill's actions | A reader takes it for a flag `analyze` accepts | It is a flag of `plan`, printed in this skill's report and handoff as the command a human runs next, and always written `/plan {slug} --reslice {story}` because `plan`'s run argument is the slug that builds its fence (`SKILL-SPEC-009-plan.md` section 6). `analyze` itself takes one positional slug and no flag. No flag resumes a closed run anywhere in the framework. |
| `02-skill-roster.md:89` and `01-skill-anatomy.md:116` route a moved section to `/amend --resync {artifact}` | `SKILL-SPEC-014-amend.md` section 9 records that `amend` defines no `--resync` behaviour and that its two arguments are a document basename and a quoted change | A moved-section row names `/amend {doc} "{change}"`, the invocation `amend` actually accepts, and a stale story bundle names `/plan {slug} --reslice {story}`. This skill prints no command another skill's specification refuses. |
| OI-6: the ADR producer exception for `.devforgeai/provenance/adr/**` | Not reachable from `analyze` | The exception is held by `architect`/`adr` and `amend`/`adr` only. `analyze` writes exactly one file, its report, inside the candidate root; it reads `.devforgeai/provenance/adr/` as part of the chain and writes nothing there. |
| OI-7: `02-skill-roster.md` shows plan calling `/analyze` | A generated `SKILL.md` for either skill tries to open the other's run and is refused, because a run is already active | No skill invokes another skill's run. `/analyze {slug}` is an "Also possible" row in `plan`'s handoff table, and this skill's own next steps are handoff rows in the same way. Section 7a's dispatch loop names no other command. |
| OI-8: `05-subagent-sets.md` calls the fourth worker `report-writer` while the registry calls it `analyze_report_writer` | `agent_type` fails the phase-agent binding check at `ingest-result` and the receipt is refused; worse, `report-writer` collides with the same display name in `skill-validator` | The registry name in `10-sequencer-and-contracts.md` section 4 is canonical: `cross_referencer`, `orphan_finder`, `stale_hash_finder`, `analyze_report_writer`. It is the agent filename, the `agents/` table row, and the string compared to the stop event's `agent_type`. |
| OI-9: the `.devforgeai/stack.yaml` write path | Not reachable from `analyze` | The path is admitted only from `architect`/`techstack` and `onboard`/`code_map`. Every `analyze` phase is refused it as sequencer-owned. `stale_hash_finder` is a judge: it reads the file to test whether a story's `commands.source` anchor still exists, and its one write tool reaches only `.devforgeai/work/<run>/evidence/stale_hash_finder/`. |
| OI-10: skills whose command takes no positional argument | Not reachable from `analyze` | `/analyze` always carries a slug, which is the `devforgeai phase start` argument, the `{arg}` substituted into the fence `docs/reports/analyze-<slug>.md`, and the run id component in `analyze-<slug>`. |
| OI-11 (new): no worker can compute a SHA-256, and this is the skill whose third phase is named for digests | `stale_hash_finder` is a judge with no shell beyond `devforgeai status`, and its one write tool reaches only the run's evidence directory, so it cannot recompute a digest and compare it. A spec that promised a `stale` verdict from the worker's own reading would be describing behaviour that cannot happen | The four verdicts are split by what is determinable. `unresolvable` is fully deterministic from reading: the source file does not exist, the anchor does not resolve, or the recorded digest is not sixty-four hexadecimal characters — and that class already catches every artifact `plan` wrote with a placeholder digest, which is the same defect `plan`'s own spec records. `resolved` and `stale` are reported only from a recorded gate verdict in a run's `source_basis[]` or a `provenance/log.jsonl` line, because the gate is where the comparison actually happens. `unchecked` is the honest default. `walk_chain.py` gives a human the real comparison on demand. The framework fix is the same one `plan` names: resolve placeholder digests at `devforgeai ingest-result`, so the chain carries real digests and the recorded verdicts become dense. This spec does not gate on that fix and does not describe it as running. |
| A heading inside a fenced code block truncates a section | Both the hash rule and `docs/design/specs/verify.py` find a section's end by scanning for the next line beginning with hashes, with no fence tracking. A citation naming a section that contains a fenced example with its own heading pins fewer bytes than the citing excerpt shows, so the excerpt is outside the hashed range and every later comparison is against the wrong bytes | `stale_hash_finder` reports this as its own row: the anchor resolves, the digest may even match, and the excerpt still does not appear in the pinned bytes. The action is to re-cite with an `#L10-L20` line anchor. `references/stale_hashes.md` states the case, and `walk_chain.py` reports it as a distinct row kind rather than folding it into `stale`. |
| A citation names a research digest with no ids | A bare digest looks like a valid provenance reference and would be reported as `resolved` | `01-skill-anatomy.md#provenance-chain` requires a sealed RUN plus the applicable Source, Evidence and Claim ids and the sealed manifest digest. `stale_hash_finder`'s `must_not` forbids reporting such a citation as resolved, and it becomes an `unresolvable` row whose action is to re-cite from the sealed dossier. |
| A project no gate has ever opened | `.devforgeai/work/` holds no handoff, so there are no recorded verdicts at all and every citation is `unchecked` | The report says so in its Stale Hashes section rather than reporting a clean chain, and the Actions section's first row is to run `walk_chain.py`. A report whose every citation row is `unchecked` is a true statement about a project nothing has yet gated, not a pass. |
| The same break appears as both an orphan and a gap | Double-counting inflates the finding list and makes the action ambiguous | `orphan_finder`'s `must_not` forbids it: a broken edge is classed by which endpoint is missing. A story naming an epic that does not exist is an orphan; a requirement no story names is a gap. |
| Where a judge's findings live | The receipt has no bounded `evidence` object, and a plan with hundreds of citations has more rows than `issues[]` can carry | Each judge writes its full row set to `.devforgeai/work/<run>/evidence/<agent>/` and names that file in `evidence_refs`; `issues[]` is the bounded summary the handoff prints, and `analyze_report_writer` renders from the findings files. |
| The two scripts' runners | Both scripts are honest deterministic checks, and only one of them has even a designed sequencer path | `check_analyze_report.py` is designed to be imported at `devforgeai ingest-result` and is not implemented; `10-sequencer-and-contracts.md` section 5.2 shows result validation stopping at path, hash and package policy. `walk_chain.py` has no sequencer path at all: no `analyze` phase grants a stack key, so no worker can invoke it, and it is a human command. A judge's evidence write is a file write, not a shell, so it does not open one either. Both run today only when a human runs them, no success criterion in section 10 gates on the unimplemented import, and the evidence table says which is which. |
| Which worker may write, and where | A generator that gave every worker the same permissions would let a judge repair what it found, destroying the evidence the skill exists to produce; one that gave the report writer none would leave the run with no output | Roles are split by the registry's `writes` column. The three finding phases compile to judges declaring `writes: evidence`, whose one write reaches `.devforgeai/work/<run>/evidence/<agent>/` and nothing else. `analyze_report_writer` compiles to a producer that writes `docs/reports/analyze-<slug>.md` inside the candidate root with Edit or Write and names it in `claimed_paths`. The sequencer derives what actually changed from the checkpoint diff and refuses anything unclaimed as `UNCLAIMED_CHANGE`, so the split is enforced by the diff rather than by the worker's word. |
| Where the report ends up | A reader expects the report to appear in the working tree the moment the phase passes | Every write lands in the candidate root `.devforgeai/work/<run>/wt`, which is gitignored. The report reaches the canonical checkout only at `devforgeai promote <run>`, never at Handoff: the last passing `devforgeai phase next` marks the run `ready_to_promote` and writes a `REQUIRE_HUMAN` handoff whose only forward step is that command, and `SKILL.md` runs it only after the user confirms in the session. Promotion, under `.devforgeai/lock`, refuses with `STALE_BASE` if canonical HEAD moved past the run's `base_ref`, with `DIRTY_TARGET` if the canonical report path is dirty, and with `MERGE_CONFLICT` if a rebase inside the root conflicted; all three refuse `devforgeai promote <run>`, not `devforgeai phase next`. A refused promotion leaves the run `ready_to_promote` with its candidate root intact and `devforgeai promote <run>` retries it once the user has resolved the reason. |
| A `REQUIRE_HUMAN` run treated as closed, with `/status` as its next step | `needs_user` and an exhausted attempt budget were described as closing the run, so the section 7e rows sent the user to `/status` and the OI-5 row said no flag could resume anything. A closed run has no candidate root, so the work the phases had already done appeared to be lost | Settled in `10-sequencer-and-contracts.md` (section 2's `phase start` row, section 3.1, section 5.4's `needs_user` row, section 6's `REQUIRE_HUMAN`, blocked-run row): such a run stays `active` with its lease released, keeps its candidate root and every checkpoint, and records `run.yaml#blocked_at`. `devforgeai phase start analyze <arg>` — the same skill and argument — resumes it at `blocked_at` with `attempts` reset. The section 7e `needs_user` and `fail at max_attempts` rows and section 7a step 7 now name `/analyze {slug}` as the forward step, with `devforgeai phase fail --reason <text>` then `/status` as the abandon route; any other skill on the same story needs that `phase fail` first. |
| Promotion read as part of Handoff | "The report reaches the canonical checkout at Handoff, when the sequencer promotes the run" made `devforgeai phase next` move canonical bytes on its own, with no point at which the user consents | Section 7b's candidate-root paragraph ("At Handoff the sequencer promotes the run"), the `report` evidence row ("On pass this is the last phase: the sequencer promotes the run"), section 7b row 7 and the row above now carry the two-block model of `WRITE-MODEL-REVISION.md` D7 and `10-sequencer-and-contracts.md` sections 5.4, 6 and 12.4: `phase next` marks the run `ready_to_promote` and writes a `REQUIRE_HUMAN` block whose only forward step is `devforgeai promote <run>`; `SKILL.md` runs that command only after the user confirms; the promotion writes the second block. |
| `STALE_BASE`, `DIRTY_TARGET` and `MERGE_CONFLICT` attributed to the transition | The refusals read as ways the last transition can fail, so a generator looks for them in the oracle table rather than on the promote path | All three are refusals of `devforgeai promote <run>` (`10-sequencer-and-contracts.md` section 2's refusal table, section 12.4's ordered steps). The row above names the command that raises them and states that the root and its checkpoints survive every refusal. |
| The section 7e outcome table had no `ready_to_promote` row | Every run ends in two handoff blocks and the table listed only the second, so a generator reading the table alone would never emit the promote step | A "pass, last phase, run `ready_to_promote` and not yet promoted" row now heads the table with `devforgeai promote {run}` as its one forward step, and the four `pass` rows that name `/dev {first_story}` and friends are labelled `promoted` so it is clear they render the second block. |
| `promote <run>` was missing from the primary window's grammar | `SKILL.md` could not run the only forward command its own handoff names, so no `analyze` run could ever be promoted | `WRITE-MODEL-REVISION.md` D7 propagates the fifth model-callable form everywhere the four are enumerated. Section 7b's grammar sentence, section 7f's Tools row, section 10's transcript criterion, the section 12 `allowed-tools` line and a new step 9 in the section 7a procedure now all carry `devforgeai promote <run>`, section 13's `skill-validator` rule says five operations rather than four, and step 9 fires only after the user asks. |
| Two audits of one project at once | Both runs claim the same fence entry and the second would overwrite the first's report at promotion | `devforgeai phase start` refuses the second with `FENCE_OVERLAP`, because the fence of an active or `ready_to_promote` run is reserved. The user finishes or abandons the first run; there is no merge between candidate roots. |

## 10. Success criteria and test cases

### Success criteria

- Triggers on the section 4 positives and on none of the near-misses.
- The report exists at `docs/reports/analyze-<slug>.md` and nothing else in the repository changed.
- Every `FIND-NNN` id is unique across all three finding sections and the sequence has no gaps.
- Every finding row's action is one exact command, and every command in the Actions section appears in at least one finding row.
- The only path in the run's checkpoint diff is `docs/reports/analyze-<slug>.md`, and it is the only entry in the `report` receipt's `claimed_paths`. Each judge's writes are confined to `.devforgeai/work/<run>/evidence/<agent>/`, which no checkpoint records and no promotion carries.
- Every citation row carries one of exactly four verdicts, and no row carries `resolved` or `stale` without naming the recorded gate verdict it came from.
- A story whose `provenance[]` names an epic that does not exist appears under Orphans, and a requirement anchor no story cites appears under Gaps, and neither appears twice.
- The primary window's transcript shows no read of the PRD, an epic, a story or the report, and no Bash call outside `devforgeai status | phase start | phase fail --reason | validate | promote <run>`, the last of which appears only after the user asked for the promotion.

### Fixture

`docs/design/examples/fixtures/analyze/` is the base fixture. Its exact tree:

| Path | Contents |
|---|---|
| `.devforgeai/state.yaml` | `version: 1`, `target: [claude]`, `mode: greenfield`, `slug: tinyapp`, `phase: plan`, `phases.plan.status: done`, `stories.STORY-001.status: ready` and `stories.STORY-002.status: ready`, and an empty `enforcement: {}` mapping |
| `.devforgeai/stack.yaml` | one anchor, `python`, copied verbatim from `docs/design/examples/hooks/fixtures/.devforgeai/stack.yaml` |
| `.devforgeai/provenance/log.jsonl` | three lines: a `session.start`, a `phase.start` for run `plan-tinyapp` and a `transition.pass` for its `stories` phase, each carrying `at`, `kind` and `session_id` |
| `docs/PM/tinyapp/prd.md` | a `prd` instance, `slug: tinyapp`, `status: approved`, with three rows under `## Requirements`: `REQ-001` a slug helper, `REQ-002` a punctuation rule, `REQ-003` a command-line entry point |
| `docs/architecture/constitution.md` | a `constitution` instance with the four required sections, one `SEC-001` row under `## Style` |
| `docs/plan/tinyapp/epics/EPIC-001.md` | an `epic` instance whose `provenance` names `docs/PM/tinyapp/prd.md#requirements` with a real digest of the fixture's own bytes, and whose `## Stories` section lists `STORY-001` and `STORY-002` |
| `docs/plan/tinyapp/stories/STORY-001.md` | a version 3 story covering `REQ-001`, `provenance` naming `EPIC-001.md#stories` and `prd.md#requirements`, one `context[]` entry naming `constitution.md#style` with a real digest, two criteria and two `test_plan` rows |
| `docs/plan/tinyapp/stories/STORY-002.md` | a version 3 story covering `REQ-002`, built the same way |
| `docs/plan/tinyapp/sprints/sprint-001.md` | a `sprint` instance listing both stories in order |
| `tinyapp/text.py` and `tests/test_text.py` | a module and a test file, present so the stories' fences name real paths |

`REQ-003` is deliberately uncovered in the base fixture, so a gap exists on every eval and eval 1 can assert it.

Overlays, copied over the base fixture after it is copied and before the prompt runs:

| Overlay | Change |
|---|---|
| `overlays/eval-2/docs/plan/tinyapp/stories/STORY-003.md` | a third version 3 story whose `provenance[0]` names `docs/plan/tinyapp/epics/EPIC-004.md#stories`, an epic the fixture does not contain, so exactly one orphan exists |
| `overlays/eval-3/docs/architecture/constitution.md` | the same constitution with the text of its `## Style` section rewritten, so `STORY-001`'s recorded `context[0]` digest no longer matches the current bytes |
| `overlays/eval-3/.devforgeai/work/STORY-001/handoff.json` | a `devforgeai.handoff/v1` object for a prior `dev` run whose `source_basis[]` holds one row: the `constitution.md#style` source, the digest `STORY-001` recorded, and the status `stale-hash`, so a recorded gate verdict exists for the worker to read |

Eval 1 has no overlay. Per-eval changes ship only as these overlay directories; no eval describes a fixture edit in prose.

### evals/evals.json (used verbatim)

```json
{
  "skill_name": "analyze",
  "evals": [
    {
      "id": 1,
      "prompt": "Run analyze on the tinyapp slug in this repository and tell me whether the plan covers the PRD.",
      "expected_output": "One report at docs/reports/analyze-tinyapp.md whose Gaps section names the uncovered requirement, whose Orphans section is empty, and whose Actions section gives one command per finding.",
      "expectations": [
        "docs/reports/analyze-tinyapp.md exists and its frontmatter carries the keys slug, template, template_version, status and depends_on",
        "The report contains the four headings Orphans, Gaps, Stale Hashes and Actions",
        "The Gaps section contains exactly one row and that row names the third requirement of docs/PM/tinyapp/prd.md",
        "The Orphans section contains no finding rows",
        "Every finding id in the report matches the FIND pattern and the ids form one unbroken sequence",
        "No file outside docs/reports/analyze-tinyapp.md was created or modified",
        "The final message contains a handoff block whose next steps include a plan command for the uncovered requirement"
      ]
    },
    {
      "id": 2,
      "prompt": "Run analyze on tinyapp. Someone added a story last week and I do not know where it came from.",
      "expected_output": "The report's Orphans section names the story whose parent epic does not exist, kept separate from the Gaps section's uncovered requirement.",
      "expectations": [
        "The Orphans section contains exactly one row and that row names docs/plan/tinyapp/stories/STORY-003.md",
        "That row states that the epic anchor its provenance names does not resolve to an existing file",
        "The Gaps section still contains the uncovered requirement row and does not also list STORY-003",
        "The final message contains a handoff block whose next step 1 is a plan command"
      ]
    },
    {
      "id": 3,
      "prompt": "Run analyze on tinyapp. The constitution was amended and I want to know which stories are affected.",
      "expected_output": "The report's Stale Hashes section marks the story citing the amended section as stale, citing the recorded gate verdict, and gives a re-slice command as its action.",
      "expectations": [
        "The Stale Hashes section contains a row naming STORY-001 and the constitution style anchor",
        "That row's verdict is stale and its basis names the recorded source_basis entry rather than a digest the worker computed",
        "That row's action is a plan reslice command naming STORY-001",
        "The final message contains a handoff block that lists the reslice command before the forward command"
      ]
    }
  ]
}
```

Quick-mode results are generation feedback only: one enabled run per eval and no baseline. They are not runtime conformance evidence, and no section of this spec gates on such evidence; the deferred contract is `12-post-mvp.md#pm-02`.

## 11. Dependencies and compatibility

| Kind | Value |
|------|-------|
| Tools | SKILL.md: `Read`, `Agent`, and a Bash grammar no wider than the five model-callable operations `devforgeai status \| phase start <skill> <arg> \| phase fail --reason \| validate \| promote <run>`, the last of which `SKILL.md` calls only after the user asks for the promotion the run's `REQUIRE_HUMAN` block names. Judges: `Read`, `Grep`, `Glob`, `Bash(devforgeai status)` and `Write` scoped to `.devforgeai/work/<run>/evidence/<agent>/`. Producers: `Read`, `Grep`, `Glob`, `Bash(devforgeai status)`, `Edit` and `Write` (Codex `apply_patch`) inside the candidate root, plus `Bash(devforgeai run *)` for the stack keys the phase grants, of which `analyze` grants none. |
| MCP servers | none |
| Runtime | Python 3.11+ for both bundled scripts; PyYAML 6+ for frontmatter parsing. `walk_chain.py` uses only the standard library beyond that, because it reimplements the hash rule directly rather than importing another skill's checker. |
| Project commands | none. No `analyze` phase declares a `run_keys` entry, so the run brokers no `stack.yaml` command and the enforcement block carries `commands: {}` for this document run. `stale_hash_finder` reads `.devforgeai/stack.yaml` to test whether a story's `commands.source` anchor still exists; it names no key and runs nothing. |
| DevForgeAI/Core compatibility | `NOT_APPLICABLE`. `analyze` is an anatomy-governed skill, not a Research Core adapter, and names no Research Core version. It reads sealed Research dossier references by RUN, Source, Evidence and Claim id and never opens a dossier record. |
| Other skills | Upstream: `pm` (`prd`), `plan` (`epic`, `story`, `sprint`), `architect` (`constitution`). Downstream: `plan` and `amend`, both of which consume `analyze-report`. Calls none: every edge is a handoff row (open item OI-7). Must not overlap with `drift`, which compares documents against code rather than documents against each other, or with a gate, which checks one artifact rather than the chain. |

Deferred dependencies, each naming its `12-post-mvp.md` entry and what the skill does today without it:

| Deferred item | What `analyze` does today |
|---|---|
| `12-post-mvp.md#pm-01` | `isolation: required` on two of the four workers is a declaration compiled into the target profile. Nothing verifies at runtime that a worker ran in its own window, and the generated adapter is an uninstalled candidate a human accepts. |
| `12-post-mvp.md#pm-02` | Quick-mode eval results are generation feedback. No success criterion in section 10 is presented as conformance evidence. |
| `12-post-mvp.md#pm-06` | Only `skip` and `quick` eval modes exist. Section 0 rule 5 rejects any third mode name as a spec defect. |
| `12-post-mvp.md#pm-10` | The clean-checkout chain validator that would run this audit as a required check from a fresh clone does not exist. `analyze` runs when a human runs it, its report is evidence rather than a refusal, and nothing blocks a commit on its findings. |

Frontmatter values derived from this table:

```yaml
compatibility: "Requires Python 3.11+ and PyYAML for the two bundled scripts. Runs inside a repository that already has a .devforgeai/ directory and a plan directory for the slug; outside one, devforgeai phase start refuses and the skill does nothing."
allowed-tools: "Read Agent Bash(devforgeai status) Bash(devforgeai phase start *) Bash(devforgeai phase fail *) Bash(devforgeai validate) Bash(devforgeai promote *)"
```

## 12. Targets

The generator produces one provider-neutral semantic package and a separate adapter for each selected target when frontmatter, invocation policy, or agent configuration differs. Provider-neutral resources may be shared. Adapter directories are not required to be byte-identical or symlinked.

| Target | Install path | Invocation | Subagents | Notes |
|--------|--------------|------------|-----------|-------|
| claude | `.claude/skills/analyze/` | `/analyze` with a slug | provider-native workers: three judges and one producer | Provider-specific frontmatter keys (`argument-hint`, `disable-model-invocation`) are compiled into this target's SKILL.md only. |
| codex | `.agents/skills/analyze/` plus `.codex/agents/` profiles | `$analyze` with a slug | provider-native workers: three judges and one producer | Portable six-field frontmatter only; policy goes in target-side configuration. |
| both | separate `.claude/skills/analyze/` and `.agents/skills/analyze/` adapters | as above | as above | Share only provider-neutral resources; validate each adapter independently. |

```yaml
metadata:
  version: "1.0.0"
  devforgeai-spec: "SKILL-SPEC-011"
  devforgeai-target: "both"
  devforgeai-anatomy: "true"
```

Not produced by skill-creator (deferred to DevForgeAI's skill-generator): provider-native `.claude/agents/*.md` and `.codex/agents/*.toml` worker profiles, provider-specific frontmatter keys for the Claude target, and concise `AGENTS.md` sections. Hook definitions are not per-skill: `init` installs the one dispatcher and its provider fragments from `09-hook-dispatcher.md`, and this spec ships none.

A generated package is an uninstalled candidate until those provider-native controls are present and independently validated. Generation or quick-mode success is not installation authority.

## 13. Constraints

- `SKILL.md` under 500 lines and roughly 5,000 tokens, holding only identity, the ordered phase list, the dispatch loop, and the handoff table. Every other instruction lives in `references/<phase>.md`, `agents/<role>.md`, `scripts/` or `assets/`.
- References one level deep from whichever file is loaded: `SKILL.md` links to `references/`, `agents/`, `scripts/`, `assets/`; an `agents/*.md` may link to `references/*.md`. Nothing links further.
- Hooks, state writes and phase advancement are not in the skill. `SKILL.md` contains no instruction the gate, the fence or a transition oracle already carries.
- No `README.md` inside the skill directory.
- No XML angle brackets in frontmatter. Description 912 characters; name 7 characters.
- Imperative voice; each step states why it matters. No capitalised absolutes: where a rule is real it is a gate defect class, the fence, a `must_not` line, or an oracle condition, and the text names that mechanism.
- Provide defaults, not menus. A citation with no recorded verdict is `unchecked` by default rather than by a choice the worker offers.
- Scripts take arguments, never prompt, and exit `0`, `1` or `2`.
- Skill-specific: the skill reports and never repairs. Its fence is one report path, and the one producer's `must_not` forbids writing or claiming anything else, because an auditor that fixed what it found would destroy the evidence it exists to produce.
- Skill-specific: a verdict of `resolved` or `stale` names the recorded gate verdict it came from. A verdict with no named basis is a defect `check_analyze_report.py` reports, not a finding.

## 14. Acceptance checks

Run these before reporting done and paste their output:

```bash
# frontmatter and naming (skill-creator's own validator)
python -m scripts.quick_validate ./out/analyze       # run from the skill-creator directory
# open-standard validator, if installed
skills-ref validate ./out/analyze
# size budget
wc -l ./out/analyze/SKILL.md                         # must be < 500
# every worker in section 7d has a prompt file, and no extra
ls ./out/analyze/agents/                             # four files, canonical registry names
# one reference file per phase, plus envelope.md
ls ./out/analyze/references/                         # four phase files plus envelope.md
# scripts answer --help and reject bad usage with exit 2
python3 ./out/analyze/scripts/walk_chain.py --help
python3 ./out/analyze/scripts/check_analyze_report.py --help
# the shipped skeleton carries every required key and section
python3 ./out/analyze/scripts/check_analyze_report.py ./out/analyze/assets/analyze-report.md
# no leftover placeholders
grep -rnE 'T[O]DO|T[B]D|\{\{' ./out/analyze || echo clean
```

The skeleton check exits 1 on the empty values it ships with; its purpose is that the failure list names only empty values and never a missing key or a missing section.

Then the wave-4 battery over this specification:

```bash
python3 docs/design/specs/verify.py --only v1,v2,v4
```

For non-Research anatomy skills, DevForgeAI skill-validator additionally checks: all sub-phase kinds present with Gate, Record and Handoff bound to sequencer operations; `must_not` present in every agent file, every agent's `writes` is `candidate`, `evidence` or `none`, and no judge's `tools` exceed read plus the run-scoped evidence write; the SKILL.md Bash grammar is no wider than the five model-callable operations, `devforgeai promote <run>` included; handoff outcomes cover every status the skill can return, including `could_not_run`. `analyze` has no critic phase, so skill-validator's persona-versus-critic check does not apply to it; section 7b names `check_analyze_report.py` as the independent check in its place.

## 15. Provenance

| Source | Hash | Used for |
|--------|------|----------|
| docs/design/01-skill-anatomy.md#primary-window-contract | see frontmatter | sections 7a, 7b, 10 |
| docs/design/01-skill-anatomy.md#provenance-chain | see frontmatter | sections 1, 2, 7d, 9 |
| docs/design/01-skill-anatomy.md#context-bundle-format | see frontmatter | sections 6, 9 |
| docs/design/10-sequencer-and-contracts.md#4-per-skill-phase-registry | see frontmatter | sections 7b, 7c, 7d |
| docs/design/10-sequencer-and-contracts.md#3-4-re-resolving-sources-and-the-one-downgrade | see frontmatter | sections 8, 9 |
| docs/design/10-sequencer-and-contracts.md#5-2-validation-order | see frontmatter | sections 7c, 9 |
| docs/design/10-sequencer-and-contracts.md#5-4-transition-oracles | see frontmatter | section 7c |
| docs/design/10-sequencer-and-contracts.md#6-handoff-envelope | see frontmatter | sections 6, 7d, 7e, 9 |
| docs/design/10-sequencer-and-contracts.md#10-evidence-files | see frontmatter | sections 6, 7d |
| docs/design/11-artifact-registry.md#1-template-registry | see frontmatter | sections 2 (R2), 6 |
| docs/design/11-artifact-registry.md#3-depends-on-edges | see frontmatter | sections 6, 7d |
| docs/design/11-artifact-registry.md#4-upstream-and-downstream-per-skill | see frontmatter | section 11 |
| docs/design/02-skill-roster.md#analyze | see frontmatter | sections 1, 2 (R1), 5 |
| docs/design/02-skill-roster.md#handoff-decision-tables | see frontmatter | section 7e |
| docs/design/05-subagent-sets.md#sets-per-skill | see frontmatter | sections 7d, 9 |
| docs/design/05-subagent-sets.md#contract-format | see frontmatter | section 7d |
| docs/design/07-purpose-and-enforcement.md#2-the-problem-in-concrete-terms | see frontmatter | section 2 |
| docs/design/12-post-mvp.md#pm-10 | see frontmatter | section 11 |
