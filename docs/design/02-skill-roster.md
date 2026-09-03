# Skill Roster

All skills except Research share the anatomy in `01-skill-anatomy.md`. Research is governed by the normative P0-P9 contract under `capabilities/research/`. This document lists what each skill adds. `05-subagent-sets.md` is authoritative for worker names; the "Extra workers" column below is a strict subset of it.

Every anatomy-governed non-Research skill owns its templates under `.devforgeai/skills/<name>/templates/`. The template a skill *produces* is the template the next skill *gates on*. Research uses the contracts and typed schemas under `capabilities/research/`.

| Skill | Gates incoming | Produces (templates) |
|-------|----------------|----------------------|
| init | — (no incoming artifact; its bundled `scripts/install.py` refuses a repository that already has `.devforgeai/state.yaml`) | `.devforgeai/state.yaml`, doc skeleton |
| onboard | — | optional OBSERVED constraint sections only for facts not derivable from source; source-derived facts remain live citations; OBSERVED `stack.yaml` |
| brainstorm | current source citations and any optional non-derivable OBSERVED constraints (brownfield only) | brainstorm.md |
| research | explicit, digest-confirmed `research-request/v1`; work-order authority is reserved but rejected by Core 0.1.0 | sealed JSON/JSONL dossier, derived synthesis and Handoff |
| pm | brainstorm.md | prd.md, backlog-ideas.md |
| architect | prd.md, current source citations, and any optional non-derivable OBSERVED constraints | constitution.md (including `#mandates`), sourcetree.md, techstack.md, architecture.md, design.md, adr.md, INTENDED `stack.yaml` |
| plan | prd.md, INTENDED set | epic.md, story.md, sprint.md, skill-spec.md |
| clarify | story.md | clarification section |
| analyze | all | analyze-report.md |
| skill-generator | skill-spec.md | skill.yaml, SKILL.md, agent.md, command.md |
| skill-validator | compiled skill | validate-report.md |
| dev | story.md (+ qa-report.md on --fix) | dev-notes.md |
| review | story.md, diff | review-report.md |
| qa | story.md, review-report.md | qa-report.md |
| amend | constitution doc | adr.md, impact-report.md |
| retro | sprint.md, qa/review reports | retro-report.md |
| drift | sourcetree.md, techstack.md, architecture.md | drift-report.md |
| status | — (read-only over `state.yaml`) | rendered handoff block only; writes nothing |

`plan` is the sole owner of the skill-spec template. `architect` writes mandates to `constitution.md#mandates`; `plan` turns each mandate that needs a skill into a `SKILL-SPEC-NNN.md`.

## Summary table

`Variant` names a generated alternative that replaces the base skill for a project when the constitution mandates it. `Extra workers` is a strict subset of `05-subagent-sets.md`.

**No skill calls another skill.** `devforgeai phase start` refuses while a run is active and no operation suspends a run, so a run cannot nest inside another (`10-sequencer-and-contracts.md` sections 2 and 6). The column below is therefore "Hands off to", not "Calls": every edge it names is a row in the handoff decision table whose first `next` step is that command, run by a human or a fresh session after the sequencer closed the run at `phase next`. A skill's own procedure never contains another skill's command.

| Skill | Variant | Persona | Command | Inputs | Outputs | Extra workers | Hands off to |
|-------|---------|---------|---------|--------|---------|---------------|--------------|
| init | — | Installer | `/init [--target claude\|codex\|both]` | target repo | `.devforgeai/`, state, doc skeleton, hook files | none (thin wrapper over its bundled `scripts/install.py`) | `/onboard` when the repository already has code, `/brainstorm {slug}` when it does not |
| onboard | — | Archaeologist | `/onboard` | existing code, README, ADRs, wiki | optional non-derivable OBSERVED constraints; OBSERVED `stack.yaml`; source-derived facts remain live citations | code-mapper, doc-ingester | human invokes research when persistent ingestion is required |
| brainstorm | — | Business Analyst | `/brainstorm <slug>` | ideas, sealed Research dossier references | `docs/brainstorm/<slug>.md` | — | human invokes research when persistent evidence is required |
| research | — | Research Lead | `/research <slug> --request <request-file> --confirm-request <sha256>` (Claude), `$research <slug> --request <request-file> --confirm-request <sha256>` (Codex) | complete `research-request/v1` file plus its confirmed normalized SHA-256 | `docs/research/<slug>/runs/RUN-NNNNNN/` plus eligible shared CAS | contracts: discovery, evidence-extractor, contrary-evidence, verifier | — |
| pm | — | Project Manager | `/pm <slug>` | brainstorm doc | `prd.md`, `backlog-ideas.md` | scope-splitter | — |
| architect | — | Senior Architect | `/architect <slug> [--yolo]` | PRD, current source citations, optional non-derivable OBSERVED constraints (brownfield) | INTENDED constitution set including `#mandates`, INTENDED `stack.yaml`, ADRs, evidenced gap epic | option-comparer, gap-analyzer, techstack-writer, prototyper | `/brainstorm {slug} --from-prototype` when the prototype raised ideas |
| plan | — | Scrum Master | `/plan <slug> [--scope]` | PRD + constitution set | epics, stories, sprints, skill specs | dependency-mapper, estimator, skill-spec-writer | `/analyze {slug}` before dev, then `/dev {first_story}` |
| clarify | — | Analyst | `/clarify <story>` | story | resolved ambiguities appended | ambiguity-finder, question-writer | — |
| analyze | — | Auditor | `/analyze <slug>` | all docs | traceability report | cross-referencer | — |
| skill-generator | — | Toolsmith | `/skill-gen <skill> [--spec <path>]` | `SKILL-SPEC-NNN.md` | neutral skill + compiled files | template-writer | `/skill-validate {skill}` |
| skill-validator | — | Auditor | `/skill-validate <skill>` | skill + constitution | pass/fail + fixes | provider-checker, spec-conformance-checker | — |
| dev | dev-tdd (generated when `constitution.md#mandates` has `tdd: required`) | Developer | `/dev <story> [--fix]` | story context bundle | code, tests, story status | base: implementer, test-writer. Variant: red-tester, green-implementer, refactorer | `/clarify {story}` when the gate or a worker needs an answer; `/review {story}` on pass |
| review | — | Reviewer | `/review <story>` | diff + constitution slice | review report | security-checker, style-checker, compliance-checker | — |
| qa | — | QA Engineer | `/qa <story>` | acceptance criteria + code | pass/fail, fix guidance | test-runner, criteria-checker | — |
| amend | — | Architect | `/amend <doc> "<change>"` | constitution change | updated doc, ADR, impact list | impact-analyzer, resync-slicer | `/plan {slug} --reslice {story}` for each impacted story |
| retro | — | Scrum Master | `/retro <sprint>` | sprint results | lessons, archive | lesson-extractor, amendment-proposer | `/amend {doc} "{change}"` for each approved amendment |
| drift | — | Auditor | `/drift` | code + docs | drift report | code-mapper | — |
| status | — | — | `/status` | state | rendered handoff block | none (thin wrapper over `devforgeai status`) | — |

## Handoff decision tables

Every anatomy-governed skill ends in a Handoff. Research produces its typed Handoff only on the successful path defined by `capabilities/research/contracts/handoff.md`; current failures return errors and no canonical failed Handoff or receipt. The table below is the `handoff.outcomes` block each anatomy-governed skill declares and the executable-success or reserved-failure summary for Research. `{x}` placeholders are filled from the applicable canonical state.

| Skill | Outcome | Next steps (in order) |
|-------|---------|-----------------------|
| init | greenfield | `/brainstorm {slug}` |
| init | brownfield | `/onboard` |
| init | target unsupported | `/init --target {other}` |
| onboard | pass | `/architect {slug}` |
| onboard | CONFLICT rows | `/architect {slug}` (conflicts listed; architect resolves) |
| onboard | critic fail | `/onboard --retry` |
| brainstorm | pass | `/pm {slug}` |
| brainstorm | needs_user | answer questions in `{brainstorm}` then `/brainstorm {slug} --continue` |
| brainstorm | critic fail | `/brainstorm {slug} --retry` |
| research | post-seal receipt `COMPLETE` (canonical Handoff remains `READY_TO_SEAL`) | exactly one continuation from the confirmed request; never auto-invoke it |
| research | reserved `NEEDS_DECISION` (not emitted by Core 0.1.0) | no canonical Handoff or receipt; preserve staging and resolve the error reported by Core |
| research | reserved `BLOCKED` / `COULD_NOT_RUN` (not emitted by Core 0.1.0) | no canonical Handoff or receipt; preserve staging and restore the dependency named by the Core error |
| research | reserved `FAILED` / `CANCELLED` (not emitted by Core 0.1.0) | no canonical Handoff or receipt; preserve staging; Core exposes no operation that persists or seals these outcomes |
| pm | pass | `/architect {slug}` |
| pm | gate fail | `/brainstorm {slug} --retry` |
| pm | needs_user | resolve MVP split in `{prd}` then `/pm {slug} --continue` |
| architect | pass | `/plan {slug}` |
| architect | mandates need skills | `/plan {slug}`; plan writes the spec for each mandate and orders `/skill-gen` before the dependent story |
| architect | prototype raised ideas | `/brainstorm {slug} --from-prototype`, then `/architect {slug}` again |
| architect | gate fail | `/pm {slug} --retry` |
| plan | pass | `/analyze {slug}` to re-check traceability, then `/dev {first_story}` |
| plan | stories with ASSUMPTION | `/clarify {story}` for each, then `/dev {first_story}` |
| plan | skill specs written | `/skill-gen {skill}` for each, then `/dev {first_story}` |
| plan | analyze found gaps | fix listed rows; `/plan {slug} --retry` |
| plan | gate fail | `/architect {slug} --retry` |
| clarify | resolved | `/dev {story}` |
| clarify | needs_user | answer in `{story}#Clarifications` then `/clarify {story} --continue` |
| analyze | clean | `/dev {first_story}` |
| analyze | orphans / gaps / stale | `/plan {slug} --reslice {story}` or `/amend {doc} "{change}"` per row |
| skill-generator | pass | `/skill-validate {skill}`, then the command that requested the generation. The generator's run is closed first; nothing is auto-run inside it |
| skill-validator | pass (`verdict: pass`) | `/status`; then the command that requested the validation |
| skill-validator | findings (`verdict: findings`) | `/skill-gen {skill} --fix` |
| skill-validator | fail (`verdict: fail`) | `/skill-gen {skill} --fix` |
| dev / dev-tdd | pass | `/review {story}` |
| dev / dev-tdd | gate: stale hash | `/plan {slug} --reslice {story}` |
| dev / dev-tdd | gate: requires_skill missing | `/skill-gen {requires_skill}` |
| dev / dev-tdd | gate: ASSUMPTION unresolved | `/clarify {story}` |
| dev / dev-tdd | `could_not_run`, `reason_code: runner_missing` | install command from the gate envelope, then `/dev {story}` |
| dev / dev-tdd | smoke-qa fail after `max_attempts` | `/dev {story} --fix` (with notes) or `/clarify {story}` |
| review | pass (`verdict: pass`) | `/qa {story}` |
| review | findings (`verdict: findings`) | `/dev {story} --fix` |
| review | fail (`verdict: fail`) | `/dev {story} --fix` |
| qa | pass (`verdict: pass`), more stories in sprint | `/dev {next_story}` |
| qa | pass (`verdict: pass`), sprint complete | `/retro {sprint}` |
| qa | findings (`verdict: findings`) | `/dev {story} --fix` |
| qa | fail (`verdict: fail`) | `/dev {story} --fix` |
| amend | applied, no impact | `/status` |
| amend | stories impacted | `/plan {slug} --reslice {story}` for each; `/dev {story}` if in progress |
| retro | amendments proposed | `/amend {doc} "{change}"` for each approved; then `/plan {next_slug}` or `/brainstorm {slug}`. retro's own run is closed before the first `/amend` |
| retro | none | `/plan {slug} --next-sprint` |
| drift | clean | `/status` |
| drift | drift found | `/amend {doc} "{change}"` (architect has no `--update`; re-run `/architect {slug}` for a full redesign) |
| status | any | the `next` recorded in `state.yaml`; status decides nothing itself |
| any | `could_not_run` | the repair route for `reason_code`, then `/{skill} {args}` |
| any | unhandled error | `/status`; `/{skill} {args} --retry` |

`--continue` and `--retry` on a run the sequencer left blocked (`run.yaml#blocked_at` set) are the same `devforgeai phase start` call and resume that run at the blocked phase with attempts reset (`10-sequencer-and-contracts.md` section 3). When no run is blocked they open a fresh run. `--fix` and `--reslice` always open a fresh run and change only what the workers read.

## Per-skill detail

### init
- Zero LLM workers. `SKILL.md` is a thin wrapper over its bundled `scripts/install.py`; everything below is deterministic.
- Detects whether the target is a Git repository and whether code or documentation files are present. Language, package-manager, and command discovery belong to onboard's code-mapper and the `stack.yaml` contract in `10-sequencer-and-contracts.md`; nothing is inferred from filenames alone.
- Writes `.devforgeai/state.yaml` with `mode: greenfield` or `mode: brownfield`, and creates `.devforgeai/hooks/`, `work/`, `sessions/`, and `provenance/`.
- **`init` is the only skill that writes `.devforgeai/` directly, and only while no `state.yaml` exists.** There is no sequencer operation that installs the framework: the grammar in `10-sequencer-and-contracts.md` section 2 is closed and contains none, so the steps above are documented provider-side actions in `init`'s own `SKILL.md`, not sequencer calls. The hook dispatcher enforces the window: with no `.devforgeai/state.yaml` on disk it permits a write under `.devforgeai/` and denies every other path; once the file exists every path under `.devforgeai/` is refused by name, so a second install is not a skill operation at all. `.claude/**`, `.codex/**`, `CLAUDE.md` and `AGENTS.md` are denied on both sides of that boundary — the dispatcher is itself one of the files `init` writes, so the provider fragments land before it is armed.
- Compiles base skills for the selected target(s) and installs the hook files listed in `09-hook-dispatcher.md`.
- Handoff: `/brainstorm <slug>` (greenfield) or `/onboard` (brownfield).

### onboard
See `03-brownfield.md`.

### brainstorm
- Sub-phases in the current executable slice: capture → have the human explicitly invoke and digest-confirm a Research request when persistence is required → consume its sealed dossier → cluster ideas → critic → handoff. Automatic parent work orders remain a future contract and are rejected by Core 0.1.0.
- Every idea gets an ID (`IDEA-NNN`) so PM can archive or promote by reference.
- Brownfield: consumes any admitted non-derivable OBSERVED constraints and otherwise uses current source citations; it does not require an OBSERVED architecture document.

### research
- Any phase may propose a Research request. In Core 0.1.0, persistence still requires an explicit human invocation and exact request-digest confirmation; parent work orders are rejected before mutation. Implicit selection is advisory-only and writes nothing.
- The normative P0–P9 workflow, schemas, evidence custody, and handoff gates live under `capabilities/research/`. JSON/JSONL is canonical; Markdown is derived.
- Research defines contracts for read-only discovery, evidence-extraction, contrary-evidence, and fresh-verification workers. Core 0.1.0 does not launch provider workers or validate the illustrative worker-result objects. Research Core remains the sole canonical writer.
- The canonical Handoff stops at `READY_TO_SEAL`. `COMPLETE` appears only after sealing, registry publication, root-view readback, and receipt construction. Research conclusions remain `PROPOSED` until the requesting phase owner accepts applicability.

### pm
- Greenfield: writes an MVP PRD. Non-MVP ideas go to `backlog-ideas.md`.
- Brownfield (`--scope feature`): writes a feature PRD scoped to one slug.
- Scope-splitter subagent produces the MVP/archive partition with a one-line justification per idea.

### architect
- `--yolo`: option-comparer subagent selects best practices per decision and records each as an ADR with `ASSUMPTION` tags.
- Interactive: deep-dive conversation per decision area (tech stack, source layout, install, data, GUI).
- Mints the INTENDED constitution set. Brownfield: gap-analyzer compares INTENDED sections only with admitted OBSERVED constraints that actually exist; absence of an OBSERVED architecture document does not create `EPIC-000 Migration`.
- Mandates (e.g. "TDD required") are written to `constitution.md#mandates`, and that is where architect's authority over skills ends. Architect does not write a skill spec and does not call skill-generator; `plan` owns the skill-spec template and turns each mandate into a spec plus an ordering story.
- techstack-writer emits the INTENDED `stack.yaml` alongside `techstack.md`, against the contract in `10-sequencer-and-contracts.md`.
- Prototype path hands off to `/brainstorm {slug} --from-prototype` with new `IDEA-NNN` entries, then back to `/architect {slug}`. It is a handoff, not a nested run.

### plan
Gate: PRD passes prd template; every INTENDED constitution section it will slice has a current hash.

Four work sub-phases, one skill:
1. **Epics.** From PRD sections + constitution slice. Each epic lists the constitution sections it depends on.
2. **Stories.** Each story carries its own context bundle (see `01-skill-anatomy.md`), acceptance criteria, and dependencies. A story may declare `requires_skill: <name>`.
3. **Skill specs.** Plan is the sole owner of the skill-spec template. For each `requires_skill` naming a skill that does not exist, and for each `constitution.md#mandates` entry that needs a skill the project lacks, plan authors `docs/plan/<slug>/skill-specs/SKILL-SPEC-NNN.md` (persona, inputs, outputs, sub-phases, templates it needs) and adds a story to run skill-generator before the dependent story.
4. **Dependencies.** The dependency-mapper sets `blocked_by` on the stories phase 2 wrote. It is a field-restricted phase: the body of every story is untouched and no other frontmatter key may change (`10-sequencer-and-contracts.md` section 4).
5. **Estimates.** The estimator sets `size` and `sprint` under the same restriction.
6. **Sprints.** Sprint files are written from the ordered, sized stories.

Then hands off: the pass row's first `next` step is `/analyze {slug}`, and the second is `/dev {first_story}`. plan does not run `/analyze` itself — `phase start` refuses while plan's own run is active, and the analyze findings reach a later plan run through `docs/reports/analyze-<slug>.md`.

`--scope change`: user supplies the epic intent inline; plan records it as the PRD stand-in with `ASSUMPTION` tags.
`--scope hotfix`: plan mints one `STORY-HOTFIX-NNN` and hands off to `/dev <story>`; dev's contract is unchanged.

### clarify
- Question-generator lists ambiguities in a story.
- User answers; answers are appended under `## Clarifications` with date.
- Dev refuses to start a story with unresolved `ASSUMPTION` tags unless `--force`.

### analyze
- Walks PRD → epics → stories → constitution → sealed Research RUN/Source/Evidence/Claim/manifest references.
- Reports orphans (story with no PRD requirement), gaps (requirement with no story), stale hashes.

### skill-generator
- Input: a `SKILL-SPEC-NNN.md` authored by plan from `templates/skill-spec.md`. Chain is plan → generator → validator. See `06-skill-specification.md` and the worked instances under `specs/`.
- Generates the skill, its workers, templates, and target adapter candidates. A generated adapter is a candidate; installation is a separate human action (`12-post-mvp.md#pm-01`).
- Hands off to `/skill-validate {skill}` as the first `next` step. It does not run the validator inside its own run: the generator's run closes at `phase next` first.
- Invoked by a plan-ordered story or by the user. Architect does not call it. Dev does not call it; dev's gate fails if `requires_skill` is unmet and the handoff points at the missing `/skill-gen` story.

### skill-validator
- Checks against the DevForgeAI constitution for skills (anatomy compliance, subagent isolation, handoff present).
- Checks against provider best practices (Claude Code, Codex).
- Checks against the originating spec document.

### dev
- Gate: story passes story template; every context bundle hash matches its source; `requires_skill` satisfied; no unresolved `ASSUMPTION` unless `--force`.
- Loads only the story's context bundle. Never opens full constitution docs.
- `--fix`: reads the QA report and the story, targets only failed criteria.
- If `constitution.md#mandates` requires TDD, the generated `dev-tdd` variant runs instead. Its worker set (red-tester, green-implementer, refactorer, smoke-qa, critic) is specified in `05-subagent-sets.md`. The variant shares dev's command, gate, story template, and handoff table; only the Work workers and the per-phase `max_attempts` map differ.

### review
- Distinct from QA. Checks constitution compliance, security, style, and diff quality.
- Runs before QA so QA tests reviewed code.

### qa
- Executes each acceptance criterion; records evidence.
- On failure, writes `docs/reports/qa-STORY-NNN.md` and sets `next: "/dev STORY-NNN --fix"`.

### amend
- Applies a change to one constitution document, writes an ADR.
- Impact-analyzer finds every story whose context bundle hashes the changed section.
- resync-slicer refreshes those bundles; the sequencer marks stories `needs_review` if already in dev.

### retro
- Collects QA reports, review findings, and dev notes for the sprint.
- Proposes constitution amendments; the user approves; the handoff's first `next` steps are one `/amend {doc} "{change}"` per approved amendment, each run after retro's own run closed.
- Archives the sprint folder.

### drift
- Re-runs onboard's code-mapper and diffs against sourcetree, techstack, architecture.
- Reports where docs no longer match code. Handoff suggests `/amend {doc} "{change}"` or a full `/architect {slug}` re-run.

### status
- Zero LLM workers. `SKILL.md` is a thin wrapper over `devforgeai status`, which renders `.devforgeai/work/<run>/handoff.json` and the `next` recorded in `state.yaml`. It writes nothing.
