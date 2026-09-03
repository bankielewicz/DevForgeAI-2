# Skill-Specification Author Brief

Status: normative for wave 2, 2026-09-02. Read this file first, then the six sources in
section 1, then write one `SKILL-SPEC-NNN-<skill>.md`. Nothing else is in scope for an
author. If a source disagrees with this brief, this brief is wrong; report it rather than
silently choosing.

## 1. What you read, in this order, and nothing else

| # | Source | Why |
|---|---|---|
| 1 | `docs/design/01-skill-anatomy.md` | the spine: primary-window contract, seven sub-phases, context bundle, state file, evidence home, handoff rules, hash rule |
| 2 | `docs/design/10-sequencer-and-contracts.md` | normative: CLI grammar, status vocabulary, per-skill phase registry, worker-result receipt, handoff envelope, `stack.yaml`, session evidence, the per-run `run.yaml`, the section 7 table shape |
| 3 | `docs/design/11-artifact-registry.md` | normative: every template, its header keys, its producer and consumers; every artifact path pattern; every `depends_on` edge |
| 4 | `docs/design/templates/skill-spec.md` | the template you fill; its header is what the gate checks |
| 5 | `docs/design/02-skill-roster.md`, `docs/design/05-subagent-sets.md`, and `examples/hooks/policy.py` | your skill's rows: command and flags, persona, ordered phases, workers, each phase's `writes` mode, handoff outcomes. `policy.py` is the running code and wins over any prose it contradicts; `10-sequencer-and-contracts.md` section 4 is the canonical phase and worker naming. Where two of them disagree, resolve it in your section 9 and name the file and line |
| 6 | `docs/design/specs/SKILL-SPEC-001-dev.md` | **form reference.** The dev specification is the fullest worked instance of the template; read it to see how a filled spec is shaped. |

Also read `docs/design/specs/ANTI-CEREMONY.md` before you write section 7 or any
`agents/<role>.md` body. It is short and it is a hard rule, not advice.

**The research author substitutes for source 1.** Instead of `01-skill-anatomy.md`, read
`src/devforgeai/skills/research/capability.md`, `src/devforgeai/skills/research/workflow.md`, and
`docs/reviews/2026-09-02-research-core-0.1.0-review.md` section 7. Research is exempt from
the seven sub-phases and from the `devforgeai.worker-result/v1` receipt; it keeps its own
typed status set and its own handoff contract. Sources 2, 3, 4, 5 and 6 still apply, and
`10-sequencer-and-contracts.md` still governs how the framework's sequencer treats a
`kind: external` skill.

Best-practice sources, for sections 3, 4, 5, 7, 8 and 13 only:

| Source | Pages / paths |
|---|---|
| `docs/provider/Anthropic/Skills/The-Complete-Guide-to-Building-Skill-for-Claude.pdf` | pages 8-16 (use cases, success criteria, file structure, frontmatter, description field, instruction style) and 25-31 (triggering failures, instruction failures, context budget, checklist, frontmatter reference) |
| `tmp/repos/skill-creators/agentskills/docs/specification.mdx` | frontmatter fields, progressive disclosure, file references |
| `tmp/repos/skill-creators/agentskills/docs/skill-creation/best-practices.mdx` | context budget, calibrating control, gotchas, templates, defaults over menus |
| `tmp/repos/skill-creators/agentskills/docs/skill-creation/optimizing-descriptions.mdx` | description structure, trigger-query design, near-misses |

Nothing else under `tmp/` is in scope. Do not read the legacy DevForgeAI repository.

## 2. The user's constraints, verbatim

These are the constraints the user set. They are not negotiable and they are not
paraphrasable.

- Terminal-only on a Max plan. Claude Code and Codex, in a terminal, and nothing else.
- No provider API. No HTTP call to a model provider from anywhere in the framework.
- Nothing aspirational. If the behaviour does not exist in `examples/hooks/`, in
  `src/devforgeai/skills/research/`, or as a contract in `10`/`11`, the spec says so plainly and
  does not describe it as though it runs.
- Full fidelity. The 500-line ceiling on `SKILL.md` is met by splitting content into more
  reference files, never by cutting content or watering it down.
- Zero ambiguity. A stranger with no conversation history builds the skill from the spec
  alone. Every question a generator would ask is answered.
- Anything deferred cites a `12-post-mvp.md` `PM-NN` entry under the spec's section 11 as
  a deferred dependency. It is never promised, and the spec never gates on it.

Two consequences that catch authors out:

1. "Deferred" is not a synonym for "coming soon". Section 11 names the `PM-NN` ID and says
   what the skill does today without it.
2. A behaviour that only half exists is written as the half that exists plus a sentence
   naming what is designed and unimplemented. `10-sequencer-and-contracts.md` section 3.2
   is the model for that voice.

## 3. The write model

Every specification is written against this model. It is not restated in the spec as
prose; it is the reason the spec's section 7 looks the way it does.

1. **Write permission is per role.** Producers write; judges do not. Producer roles are
   the red, green, refactor and fix workers and every document writer — story, prd, adr,
   design, brainstorm, sourcetree, techstack, code_map, skill files, retro, drift,
   clarification, impact, validate reports. Judge roles are the gate resolver, critic,
   reviewer, smoke and QA verifier, analyze and status. Every worker header declares
   `writes: candidate`, `writes: evidence` or `writes: none`, and its `tools` follow from
   that: producers hold `Read`, `Grep`, `Glob`, `Edit`, `Write` (Codex: `apply_patch`) and
   `Bash(devforgeai run *)` for the keys the phase granted; judges hold `Read`, `Grep`,
   `Glob`, `Bash(devforgeai status)` and `Write` confined to
   `.devforgeai/work/<run>/evidence/<agent>/`, where their findings file lives and which
   the receipt names in `evidence_refs` — that directory is run-scoped, gitignored and
   never promoted, and `issues[]` stays the bounded summary. `writes: none` is left for a
   worker that produces nothing but the receipt. No class holds a git write, a package
   manager, a network tool, or a raw stack command.
2. **One candidate root per run.** The sequencer creates it at `phase start` and owns it
   until promotion or abandonment: a git worktree on branch `devforgeai/<run>` where the
   project is a git repository, a copy of the tree where it is not, at
   `.devforgeai/work/<run>/wt`. Every write a producer makes is under that root, and
   `devforgeai run <key>` executes with cwd = `candidate.root`. The primary session stays
   in the canonical checkout. The phases of one run build linearly on that root — base →
   red → green → refactor — and each transition leaves a checkpoint the next phase starts
   from. Rewinding to phase P resets the root to the checkpoint P started from — its
   predecessor's, or `base` for the first phase — and re-enters P.
3. **One receipt.** Every worker's final message is exactly one
   `devforgeai.worker-result/v1` object, schema at
   `schemas/devforgeai/v1/worker-result.schema.json`, fields and bounds in
   `10-sequencer-and-contracts.md` section 5.1. It names `claimed_paths` (at most 64) and
   `evidence_refs` (at most 16), never file bytes. No Markdown fence, no surrounding prose.
   A non-pass status carries an empty `claimed_paths`.
4. **The sequencer decides from the diff, not the claim.** At `ingest-result` it derives
   `changed[{path, blob_sha256, kind}]` from the checkpoint diff, refuses the result when
   `changed` is not a subset of `claimed_paths` or a path is outside the fence, runs the
   phase's transition oracle inside the candidate root, records the result and checkpoint,
   releases the run's lease, and advances, retries, rewinds or blocks. A worker's claim
   that its work is done is not why a phase advances.
5. **Exactly one producer holds the lease.** It is recorded in
   `.devforgeai/work/<run>/run.yaml`, granted at dispatch, released at `ingest-result`, and
   bound on Claude at the identity-bearing `SubagentStart`. Judges never hold it and may
   run concurrently against a checkpoint.
6. **Workers never receive a literal command.** A phase names a stack command key. The
   producer that holds the lease may call `devforgeai run <key>` for a granted key to get
   its own feedback; the sequencer resolves the same key from the hash-pinned `stack.yaml`
   section the run anchored at its gate and runs the oracle itself. A specification that
   writes a literal build or test command into a worker prompt, a story, or a reference
   file is wrong.
7. **The model dispatches, the sequencer decides.** The primary window parses arguments,
   calls the model-callable operations, dispatches workers by path plus the
   `devforgeai status` block, branches on a returned status, and prints the handoff the
   sequencer rendered. It reads no artifact, writes no file, and declares no phase
   complete.

Model-callable, closed: `devforgeai status`, `devforgeai phase start <skill> <arg>`,
`devforgeai phase fail --reason <text>`, `devforgeai validate`, and
`devforgeai promote <run>` — the last only after a run reached `ready_to_promote` and the
user asked for it. Hook-only: `devforgeai session-start`, `devforgeai ingest-result`,
`devforgeai phase next`, and `candidate open | checkpoint | promote | abandon`.
`devforgeai run <key>` is neither: it belongs to the lease-holding producer inside the
candidate root. There is no other operation. A specification that names one is rejected by
wave 4's grammar check.

## 4. The progressive-disclosure layout

Fixed. Written into `templates/skill-spec.md` sections 8 and 13, and repeated here because
it is the single most common place a spec drifts.

```
<skill>/SKILL.md            # at most 500 lines: identity, phase list, dispatch loop, handoff table
  references/<phase>.md     # one per phase: the guidance that phase's worker needs
  references/envelope.md    # the worker-result schema
  agents/<role>.md          # one per worker; body = the section 7 contract verbatim
  scripts/                  # deterministic, non-interactive, exit-coded
  assets/                   # output templates
```

- `SKILL.md` holds four things and nothing else: identity, the ordered phase list, the
  dispatch loop, and the handoff table. Guidance a phase needs lives in that phase's
  reference file. Nothing is duplicated across files.
- One `references/<phase>.md` per registry phase, named for the registry phase exactly,
  plus `references/envelope.md`. A phase whose guidance exceeds a comfortable reference
  file is split into more reference files, and `SKILL.md` names which to load when.
- One `agents/<role>.md` per worker in section 7, named for the canonical worker name.
  There is no agent file for Gate, Record or Handoff: they are sequencer operations.
- Link depth: `SKILL.md` links to `references/`, `agents/`, `scripts/` and `assets/`; an
  `agents/*.md` links to `references/*.md`; nothing links further.
- No `README.md` inside the skill directory.

Two skills have no phases and no workers (`init`, `status`) and one wraps an external
runner (`research`); `05-subagent-sets.md` records all three as having none. Do not invent
an `agents/` directory for a skill with no workers.

## 5. Best-practice rules that apply

From the Anthropic guide and the Agent Skills documentation. These are the rules a wave-4
check or a human reviewer will hold you to.

**Description (spec section 3, becomes the `description` frontmatter).**

- Structure: what it does + when to use it + key capabilities + what NOT to use it for.
- At most 1024 characters. Count them and record the count.
- No `<` or `>` anywhere in frontmatter, including inside the description. A command form
  that normally carries angle brackets is rewritten without them.
- Imperative phrasing aimed at the agent ("Use this skill when..."), not third person
  ("This skill does...").
- Focus on user intent, not internal mechanics; the agent matches what the user asked for.
- Be pushy about triggering: name contexts where the skill applies even when the user does
  not name the domain. Research is the exception — its description authorises persistence
  only from the exact explicit invocation with a confirmed request digest.
- Negative triggers are part of the description, not an afterthought: name the adjacent
  skill a near-miss should go to instead.
- Written as a YAML block scalar so colons are safe.

**Trigger set (spec section 4).**

- 8-10 positives and 8-10 near-misses, used verbatim by the generator.
- Vary phrasing (formal, casual, typos), explicitness (some name the domain, some do not),
  detail (terse and context-heavy, with real paths and backstory), and complexity
  (single-step and multi-step).
- The most useful positives are the ones where the skill helps but the connection is not
  obvious from the query alone.
- Near-misses share vocabulary with the skill and need something else. "Write a fibonacci
  function" tests nothing; "re-run the failing tests for STORY-004" against `qa` tests the
  boundary.

**Use cases (spec section 5).** Two or three, each with a verbatim user utterance,
numbered steps, and what exists afterwards.

**Instruction style (spec sections 7 and 13).**

- Imperative voice. Explain why a step matters instead of shouting it; an agent that
  understands the purpose makes better context-dependent decisions.
- No all-caps `ALWAYS` or `NEVER`. Where an instruction is genuinely non-negotiable, it is
  a gate, a fence or an oracle, and the spec names that mechanism instead.
- Provide defaults, not menus. Procedures over declarations: teach how to approach the
  class of problem, not what to produce for one instance.
- Add what the agent lacks; omit what it knows. Do not explain what a test is.
- Gotchas are the highest-value content. Only real ones. `None known` is a valid entry;
  an invented gotcha teaches a false constraint.
- References one level deep. Tell the agent *when* to load a file, not just that it exists.

**Scripts (spec section 8).** Deterministic, non-interactive, exit-coded (`0` ok, `1` fail,
`2` usage), stdout for data and stderr for diagnostics, `--help` documented. A script never
prompts.

## 6. Filling `templates/skill-spec.md`, section by section

The template's header lists sixteen required sections in order. Wave 4's V1 check asserts
all sixteen are present, in order, with `status: approved` and no placeholder text. The
placeholder scan is a substring test over the raw file for `{{`, `}}`, and three literal
words meaning "not written yet" — so do not use those words anywhere, not even inside a
constraint about them.

**Frontmatter.** `id` matches `^SKILL-SPEC-[0-9]{3}$`. `skill_name` is the registry skill
name from `11-artifact-registry.md` section 5 — `dev`, never `dev-tdd`. `target` is `both`
unless `02-skill-roster.md` says otherwise. `status: approved` on delivery. `author` and `date` are
filled. `depends_on` is the context bundle: see section 8 of this brief.

**0. Generator instructions.** Copy the template's rules 1-9 and adapt only the
cold-session prompt's paths and the output directory. Eval mode is `skip` or `quick`; a
third mode name is a spec defect and the deferred interactive mode is
`12-post-mvp.md#pm-06`.

**1. Identity.** `name` equals the skill directory name, kebab-case, at most 64
characters, no `claude` or `anthropic` prefix. `category` for every roster skill is
`devforgeai-phase`. `version` is the skill-package version written to `metadata.version`,
not a framework version.

**2. Problem and requirements.** State what goes wrong without the skill, for whom, in
which situation — grounded in the failure modes in `07-purpose-and-enforcement.md` section
2 where they apply. Then the requirement table: explicit (what the user asked for),
implicit (conventions, formats, safety), discovered (found in the design documents). Every
row is traceable to a source you can name.

**3. Description.** The exact frontmatter description, per section 5 above, plus the
character count.

**4. Trigger set.** The JSON array, verbatim-usable, per section 5 above.

**5. Use cases.** Two or three, per section 5 above.

**6. Inputs and outputs.** Inputs table (name, format, example file, required) and outputs
table (name, format, location, template). Every template name and every path pattern comes
from `11-artifact-registry.md` sections 1 and 2 — do not invent a path. Then the output
template block, showing the exact shape of the primary output. Then the return-envelope
block, unchanged from the template except for the skill and phase names.

**7. Procedure.** This is the section the generator turns into `SKILL.md` and
`agents/<role>.md`. It has four parts.

*7a. Steps.* The `SKILL.md` body: the dispatch loop, imperative, each step with its reason.

*7b. Sub-phases and workers.* The mapping from `01-skill-anatomy.md`'s seven sub-phases
onto your skill's registry phases. Gate, Slice, Record and Handoff are sequencer operations
and name no worker. `examples/hooks/policy.py` is the authority for which registry phase is
which sub-phase kind and for each phase's `writes` mode; a worker's own
`writes: candidate | evidence | none` follows from that mode — a phase that writes
files into the tree has a producer, a report-only phase has a judge, which writes
its findings under `.devforgeai/work/<run>/evidence/<agent>/` and nowhere else.

*7c. The evidence and gate table.* One row per registry phase, in phase order, exactly
this shape from `10-sequencer-and-contracts.md` section 11:

```
| phase | worker | deterministic gate check | gate_policy | evidence file | transition oracle |
```

Column rules, and how to fill them without writing fiction:

- **phase** — the registry name from `10-sequencer-and-contracts.md` section 4, character
  for character. `examples/hooks/policy.py` lists them in order.
- **worker** — the canonical worker name from the same table. Never the long alias.
- **deterministic gate check** — what a script verifies, with no model judgement. Three
  distinct things land in this column and you name whichever applies to that phase:
  1. the run-level gate at `devforgeai phase start`, which for a `kind: document` skill
     checks that no run is already active, that the skill is known, and that every fence
     entry is repository-relative, contains no `..`, and is not sequencer-owned; and for
     `kind: story` runs the whole story gate in section 3.2;
  2. the per-result validation at `ingest-result`, which derives `changed[]` from the
     candidate's checkpoint diff and refuses the result when a changed path is not in
     `claimed_paths`, falls outside the fence, or is not allowed by the phase's `writes`
     mode — for `red` a path outside `test_paths`, for `green` and `refactor` a test path
     whose hash changed since red;
  3. the whole-tree package and import policy rescan the oracle runs inside the candidate
     root before the checkpoint is taken.
  "The worker confirms" is not a gate check. If nothing deterministic checks something you
  wish were checked, say so in section 9 and cite the line that says it is unimplemented.
- **gate_policy** — the defect class this phase's failure maps to, and its action, from
  the map in section 3.2. Be honest about the two limits stated there: every
  `devforgeai phase start` defect is a refusal whatever the declared value says, and only
  `test_runner_missing` changes behaviour, at transition time. A document run carries the
  fixed map `{unresolvable_source: BLOCK}` and has no story to declare a wider one.
- **evidence file** — the exact path with `<run>` and `<phase>` substituted:
  `.devforgeai/work/<run>/<phase>-result.json` and `.devforgeai/work/<run>/<phase>-report.md`.
  For a document run `<run>` is `<skill>-<arg>`; for a story run it is the story id.
- **transition oracle** — the oracle name from section 5.4 and the one condition that makes
  it pass. For `writes: docs` phases that is `document`: the phase produced at least one
  file and every declared output with non-null content exists on disk. For `writes: none`
  phases that is `report_only`: no file outside the fence changed since the phase's input
  checkpoint and the whole-tree package and import policy holds. A judge's own findings
  file lives outside the tree the oracle compares, so writing it never trips
  `report_only`.

*7d. Worker contracts.* One YAML block per worker, in the template's shape: `name`,
`writes`, `responsibility` (one sentence, one job), `inputs`, `outputs`, `must_not`,
`tools`, `isolation`, `returns`. `writes` is `candidate` for a producer, `evidence` for a
judge and `none` for a worker that produces nothing but the receipt, and `tools` follows it
exactly (section 3 of this brief). `must_not` is compiled into the agent prompt verbatim: a
producer's ends with "write outside the candidate root or outside this phase's write fence"
and "run a raw stack command, a git write, a package manager, or a network tool"; a judge's
ends with "write anywhere but this run's evidence directory"; a `writes: none` worker's ends
with "write any file". A producer is never told
that it does not write — its contract opens with what it writes and where
(`templates/agent-md.md`). These blocks become the `agents/<role>.md` bodies, whose four
sections are job, inputs, rules, receipt. Persona and critic are always different files
with different prompts.

*7e. Handoff outcomes.* The decision table your skill declares as `handoff.outcomes`. Take
the rows from `02-skill-roster.md`'s per-skill table and correct them against the closed
status set in `10-sequencer-and-contracts.md` section 3.1, and against the outcome rows
`examples/hooks/devforgeai.py` actually writes (see OI-11).

**8. Bundled resources.** The fixed layout from section 4 of this brief, then four tables:
`scripts/` (file, purpose, invocation, exit codes), `references/` (one row per phase plus
`envelope.md`, with a "load when" that names the dispatch it precedes), `assets/` (file,
output it seeds), `agents/` (one row per worker in section 7, no more and no fewer).

**9. Gotchas and edge cases.** Real ones. This is where the open items in section 10 that
touch your skill get resolved and recorded: each becomes a row saying what goes wrong and
what to do instead, or a stated decision with the file and line that forced it. An author
who leaves an applicable open item out of section 9 has not resolved it.

**10. Success criteria and test cases.** Countable criteria, then two or three evals in the
template's `evals/evals.json` shape, used verbatim. Expectations are checkable from the
transcript or the output files, never stylistic. Per-eval fixture changes ship as an
overlay directory, never as prose. Quick-mode results are generation feedback only; no
section may gate on them, and the deferred contract is `12-post-mvp.md#pm-02`.

**11. Dependencies and compatibility.** The template's table. `Tools` is `SKILL.md`:
`Read`, `Agent`, and a Bash grammar no wider than the model-callable operations; workers:
the producer or judge tool set its `writes` class fixes (section 3). `Project commands`
names `stack.yaml` keys only, never a literal command. **This is also where every deferred dependency goes**: one line per
`12-post-mvp.md` entry your skill would otherwise need, naming the `PM-NN` ID and what the
skill does today without it.

**12. Targets.** The template's target table, unchanged except for your skill's name and
invocation. Claude is `/<name>`; Codex is `$<name>`. A generated package is an uninstalled
candidate; generation success is not installation authority.

**13. Constraints.** The template's list, plus any constraint your skill's own rows add. The 500-line
ceiling, the one-level reference depth, no `README.md`, no angle brackets in frontmatter,
imperative voice, defaults not menus, non-interactive scripts.

**14. Acceptance checks.** The template's bash block, with your output directory
substituted, plus the wave-4 battery in section 9 of this brief.

**15. Provenance.** A mirror of frontmatter `depends_on` with the section each source fed.

## 7. Spec numbering and file path

Fixed by the plan. Do not renumber.

| Spec | Skill | Spec | Skill |
|---|---|---|---|
| `SKILL-SPEC-001` | dev (with the dev-tdd variant) | `SKILL-SPEC-010` | clarify |
| `SKILL-SPEC-002` | review | `SKILL-SPEC-011` | analyze |
| `SKILL-SPEC-003` | qa | `SKILL-SPEC-012` | skill-generator |
| `SKILL-SPEC-004` | init | `SKILL-SPEC-013` | skill-validator |
| `SKILL-SPEC-005` | onboard | `SKILL-SPEC-014` | amend |
| `SKILL-SPEC-006` | brainstorm | `SKILL-SPEC-015` | retro |
| `SKILL-SPEC-007` | pm | `SKILL-SPEC-016` | drift |
| `SKILL-SPEC-008` | architect | `SKILL-SPEC-017` | status |
| `SKILL-SPEC-009` | plan | `SKILL-SPEC-018` | research |

File path: `docs/design/specs/SKILL-SPEC-NNN-<skill>.md`. One file per author-task. Write
nothing else.

`status: approved` on delivery. A spec delivered as `draft` fails V1, and a `draft` spec
that a generator reads stops with a spec-gaps list instead of producing output.

## 8. `depends_on`, and why your hashes may read PENDING

Frontmatter `depends_on` is the context bundle the spec was sliced from. Each entry carries
`source` (a `path#anchor`), `hash`, and a verbatim `excerpt`. List every source and anchor
now, with the excerpt filled from the current bytes.

The hash rule is `01-skill-anatomy.md`'s: resolve `path#anchor` where a heading anchor is
the GitHub-style slug of the heading (lowercase, non-alphanumerics collapsed to single
hyphens, trimmed) and the section runs to the next heading of the same or higher level; a
line anchor `#L10-L20` is that inclusive range; no anchor means the whole file. Normalise
CRLF to LF, join with LF, append one trailing LF, `sha256` the UTF-8 bytes, record as
`sha256:<64 hex>`. So `## 4. Per-skill phase registry` is the anchor
`#4-per-skill-phase-registry`.

Hashes are recomputed once, in wave 4, after every source is frozen. Until then a
`depends_on` entry may carry `hash: sha256:PENDING`. That is expected and is not a defect
in wave 2. What *is* a defect is a missing source, an anchor that does not resolve, or an
empty excerpt — those fail wave 4 and cannot be fixed by a recompute.

## 9. Acceptance checks you run before reporting done

```bash
python3 docs/design/specs/verify.py --only v1,v2,v4,v9
```

- **V1** asserts the sixteen sections in order, the id pattern, `status: approved`, and no
  placeholder text.
- **V2** asserts no forbidden text anywhere under `docs/design/**` except
  `12-post-mvp.md`. The forbidden list is in `verify.py`. Two that catch authors: any
  literal build-command allowlist entry, and the deleted status token that
  `10-sequencer-and-contracts.md` section 3.1 replaced with `could_not_run`. Refer to both
  by description, not by writing them.
- **V4** asserts every template your section 6 consumes has a producer in
  `11-artifact-registry.md` and every template it produces has a consumer, and that every
  backticked `/command` or `$command` in your body resolves to a registry skill or its
  command string. `/skill-gen` and `/skill-validate` resolve; `/skill-generator` does not.

- **V9** asserts no file still describes the superseded write model. Its token list is in
  `verify.py`: file-body and base-hash fields from the old envelope, the blanket
  no-worker-writes phrasing, and the deleted shared Slice worker. If a phrase of yours
  trips it, the phrase is stale, not the check.

V3 (hash recompute) and V8 (grammar parity) run in wave 4, not by you.

## 10. Cross-cutting open items

Thirteen contradictions cut across every skill. Each author resolves the ones that touch their skill.
You resolve each one in your spec's section 9, once, in writing, with the file and line
that forced the decision. Do not resolve them differently from another author: where a
resolution is already stated below, use it.

| ID | Contradiction | Resolution the spec records |
|---|---|---|
| OI-1 | Earlier drafts of `01-skill-anatomy.md` and `05-subagent-sets.md` gave Slice to a shared framework worker, but no phase in `10-sequencer-and-contracts.md` section 4 dispatches one, and section 11 states every registry row has a worker | **DECIDED:** Slice is a sequencer operation, not a worker. At `phase start` the sequencer resolves the incoming artifact's already-hashed `context[]` bundle and writes it to `.devforgeai/work/<run>/context.json`; every worker of the run is handed that path. The shared framework worker is deleted from 01, 05, 10 and 11 and no agent entry for it exists. A run whose gate identifies no incoming artifact (every unanchored document run) records the no-op in the same file; `init`, `status` and `research` open no run and write nothing. |
| OI-2 | What the story gate re-resolves | DECIDED (section 12): every `provenance[]`, `context[]` and `commands.hash`; placeholders are `unresolvable-source` under `gate_policy`. An **unanchored** document gate checks the fence only. `review` and `qa` are the exception: `examples/hooks/policy.py` marks both `anchor: story`, so `phase start` runs the full story gate over `<arg>` and copies the story's `commands`, `test_plan`, `test_paths` and `gate_policy` into `.devforgeai/work/<run>/run.yaml`, while the write fence stays the report path. `10-sequencer-and-contracts.md:79` and :227 are behind the code on both points. |
| OI-3 | Worker tools: earlier drafts gave every worker the same read-only list, while `10-sequencer-and-contracts.md` described `Bash(devforgeai run *)` as declared surface only | **DECIDED:** tools follow the role. A producer (`writes: candidate`) holds `Read`, `Grep`, `Glob`, `Edit`, `Write` and `Bash(devforgeai run *)` for the keys its phase granted, and every write is under `candidate.root`. A judge (`writes: evidence`) holds `Read`, `Grep`, `Glob`, `Bash(devforgeai status)` and `Write` only under `.devforgeai/work/<run>/evidence/<agent>/`, where its findings file lives and is named in `evidence_refs`; `writes: none` is for workers that produce nothing but the receipt. Neither holds a git write, a package manager, a network tool, or a raw stack command, and `must_not` says so. |
| OI-4 | `10-sequencer-and-contracts.md` section 5.4 lists no outcome row for `status: fail` with no `next` | `examples/hooks/devforgeai.py:1017-1018` inserts `"<agent> reported fail"` as a transition problem row, so the phase retries to its `max_attempts` and then blocks `REQUIRE_HUMAN`. A critic that fails is a retry, then a human, never a silent pass. |
| OI-5 | `02-skill-roster.md` gives resume flags (`--continue`, `--retry`, `--fix`, `--reslice`) but `10-sequencer-and-contracts.md:61` closes the run on `needs_user` and :324 closes it when attempts are exhausted | **DECIDED (revised):** a `REQUIRE_HUMAN` block leaves the run `active` with `run.yaml#blocked_at` set; `devforgeai phase start` with the same skill and argument resumes at that phase with attempts reset (10 section 3), so `--continue` and `--retry` are that resume. `--fix` and `--reslice` open a fresh run from phase 1 and change only what the workers read. |
| OI-6 | `11-artifact-registry.md` puts `adr` at `.devforgeai/provenance/adr/NNNN-<slug>.md`, which `policy.ALWAYS_DENY` marks sequencer-owned and which is outside every document fence | **DECIDED:** `.devforgeai/provenance/adr/**` is a `PRODUCER_EXCEPTIONS` entry for `architect`/`adr` and `amend`/`adr`, and is in both skills' document fences, exactly as `.devforgeai/stack.yaml` is for `architect`/`techstack` and `onboard`/`code_map`. The sequencer validates the file against the `adr` template header — required frontmatter, `id_pattern`, required sections, forbidden text — and against the filename shape before the run is promoted; an existing ADR is never overwritten and there is no rewind for this path. The id shape is the template's own `^ADR-[0-9]{4}$` with the filename `NNNN-<slug>.md`, not a three-digit form: the template is the owner of that pattern and 01, 10, 11 and the code already agree on it. Installing an ADR by hand is no longer a step in any spec.
| OI-7 | `02-skill-roster.md` has plan call `/analyze`, skill-generator call `/skill-validate`, architect loop to brainstorm, and retro call `/amend`; `10-sequencer-and-contracts.md` refuses `devforgeai phase start` while a run is active | **DECIDED: no nesting, ever.** A skill that "calls" another ends its run with a handoff whose first `next` step is that command; the sequencer closes the run at `phase next` before the named command may start. `02-skill-roster.md`'s column is now "Hands off to", every such edge has a handoff row, `10-sequencer-and-contracts.md` section 6 carries it as rendering rule 9, and `11-artifact-registry.md` records the five edges as `via: handoff` control flow that no artifact depends on. A spec's procedure may not contain another skill's command.
| OI-8 | `05-subagent-sets.md` names eight skills' workers differently from the registry (`critic` versus `onboard_critic`, `report-writer` versus `analyze_report_writer`, and so on) | The registry name in `10-sequencer-and-contracts.md` section 4 is canonical and is what `agent_type` is compared against. `05`'s hyphenated form is a display alias. Use the canonical name in section 7, in `agents/<role>.md` filenames, and in the evidence table. |
| OI-9 | `.devforgeai/stack.yaml` write path | DECIDED: architect's techstack-writer (greenfield) and onboard's code-mapper (brownfield) carry `.devforgeai/stack.yaml` in their document fence; the sequencer validates the file against `schemas/devforgeai/v1/stack.schema.json` before the run is promoted. No other skill may write it. The fix-up agent is implementing this in policy.py and doc 10; specs describe it as the write path. |
| OI-10 | `/onboard`, `/drift` and `/status` take no positional argument, but `devforgeai phase start <skill> <arg>` requires one and the fence patterns substitute `{arg}` | The adapter supplies the project slug from `state.yaml` as `<arg>`. The spec states which value it passes and what happens when `state.yaml` holds no slug. |
| OI-11 | `02-skill-roster.md` gives each skill a per-outcome `next` command; `examples/hooks/devforgeai.py:1052` writes `/status` for every document run that passes, and `:1224` writes `/status` for every document-run block under `REQUIRE_HUMAN` | The per-skill table in `02-skill-roster.md` is the `handoff.outcomes` block the skill declares in `skill.yaml`, and it is the contract. The current sequencer does not read it: a document run's pass handoff names `/status`, a `COULD_NOT_RUN` block names the runner repair then `/<skill> <arg>`, a `REQUIRE_HUMAN` block names `/status`, and a `WARN` or `OFF` block names `/<skill> <arg> --fix`. The spec records both, with the line reference, and does not describe the declared row as what a run prints today. |
| OI-12 | `devforgeai phase start` accepts a `--lenient` flag in `examples/hooks/devforgeai.py`; `10-sequencer-and-contracts.md` section 2's `Args` column for that operation is `<skill> <arg>` and does not mention it | `--lenient` downgrades `unresolvable-source` to a recorded warning and nothing else. It is refused for any story under `docs/plan/` and for a skill with no story gate, so it is unreachable for every document skill. A document-skill spec does not mention it; the `dev` spec states its exact scope and that a planned story can never use it. |
| OI-13 | `10-sequencer-and-contracts.md` section 4 gives `architect` ten phases including `mandate_specs` with the worker `mandate_spec_writer` and a fence over `docs/plan/<arg>/skill-specs/*.md`; `11-artifact-registry.md:51` and its divergence 1 record the same conflict. `examples/hooks/policy.py` now has nine `architect` phases, no `mandate_spec_writer`, and a fence of `docs/architecture/**` plus `.devforgeai/stack.yaml` | `plan` is the sole producer of `skill-spec`, and `architect` no longer has a phase that writes one. Architect writes mandates into `constitution.md#mandates` through its `constitution` phase. Use the nine-phase registry; `10` section 4's architect rows and `11`'s divergence 1 are behind the code. |

### Skill-specific items decided centrally

Four skill-level items were resolved once, in code and in 02, 10 and 11, rather than per spec. Use these answers verbatim.

| ID | Card | Resolution the spec records |
|---|---|---|
| PL-1 | plan | **DECIDED:** `dependencies` and `estimates` write. Both are `writes: fields`: the fence `docs/plan/<arg>/stories/*.md`, an existing file, a byte-identical body, and a frontmatter diff confined to `blocked_by`, `size` and `sprint`. The order stays `stories` → `dependencies` → `estimates` → `sprints`, so the two phases set those keys on the stories `stories` wrote; `story_writer` does not fill them from a later phase's evidence. A field-restricted phase may legitimately propose no file. |
| R-6, Q-7, SV-1 | review, qa, skill-validator | **DECIDED:** the report phase's receipt carries the verdict through `evidence_refs`, pointing at the report it wrote, as a closed value (`pass \| findings \| fail`) legal only from `review`/`report`, `qa`/`report` and `skill-validator`/`report`. It selects the handoff row and therefore `next`; the run's `status` and the handoff's `outcome` stay `pass`, because reporting a defect is a passing run. `findings` and `fail` emit `/dev <story> --fix` for review and qa and `/skill-gen <skill> --fix` for skill-validator; `pass` keeps `/status`. When the report's frontmatter carries a `verdict`, it must equal the receipt's. |
| I-1 | init | **DECIDED:** there is no `devforgeai init` and none is added. Installation is a provider-side action performed by `init`'s own `SKILL.md` through documented steps — copy the hook fragments, write the `state.yaml` skeleton, create `work/`, `sessions/` and `provenance/` — which are not sequencer operations. `init` is the only skill that writes `.devforgeai/` directly, and only while no `state.yaml` exists; the dispatcher permits a write under `.devforgeai/` in exactly that window, denies every other path in it, and refuses every `.devforgeai/` path by name once `state.yaml` exists. `.claude/**`, `.codex/**`, `CLAUDE.md` and `AGENTS.md` stay denied on both sides. |

## 11. What a finished spec looks like

- Sixteen sections, in order, `status: approved`, no placeholder text.
- Section 7's evidence table has one row per registry phase, in registry order, with the
  canonical worker name and a real deterministic check in every row.
- Section 7's worker contracts and section 8's `agents/` table list exactly the same set.
- Section 6's templates all exist in `11-artifact-registry.md`.
- Section 9 resolves every open item in section 10 that touches the skill.
- Section 11 names a `PM-NN` ID for every deferred dependency.
- `python3 docs/design/specs/verify.py --only v1,v2,v4,v9` exits 0.
- Nothing in it describes behaviour that does not exist.

## 12. Canonical skill format and decisions made after this brief was drafted

- Canonical format: https://agentskills.io (specification, skill-creation/best-practices, optimizing-descriptions, evaluating-skills, using-scripts; local mirror `tmp/repos/skill-creators/agentskills/docs/`). A skill is a folder with `SKILL.md` (frontmatter `name`, `description` required; `license`, `compatibility`, `metadata`, `allowed-tools` optional; nothing else) plus optional `scripts/`, `references/`, `assets/`. Body has no format restriction; keep it under 500 lines and 5000 tokens; validate with `skills-ref validate`.
- The per-skill facts an author needs — ordered phases, worker names and their `writes` class, fences, granted keys — come from `examples/hooks/policy.py`, with template names checked against `11-artifact-registry.md`'s machine-readable registry block. `policy.py` is running code and wins over prose it contradicts. Where two design documents disagree, the spec's section 9 names the file and line and says which side the author followed.
- `phase start review <story>` and `phase start qa <story>` load the story's `commands` so the qa oracle works; the write fence of both runs is the report path and nothing else, so their report writers are producers that may write exactly that file.
- The story gate re-resolves every `provenance[]`, `context[]` and `commands.hash`; placeholders are `unresolvable-source` under `gate_policy`.
- plan is the sole author of skill specs; architect writes `constitution.md#mandates` only.
- skill-generator's fence `.devforgeai/skills/<name>/**` has no rewind.
