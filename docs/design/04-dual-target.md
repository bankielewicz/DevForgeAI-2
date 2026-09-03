# Dual Target: Claude Code and Codex

Skills are authored once in a provider-neutral spec and compiled by skill-generator to each target's layout.

## Neutral skill spec

Lives in `.devforgeai/skills/<name>/skill.yaml`.

```yaml
name: plan
version: 1
persona: scrum-master
command:
  name: plan
  args: [slug]
  flags: [--scope]
prerequisites:
  phases_done: [architect]
inputs:
  - docs/PM/<slug>/prd.md
  - constitution-set          # re-resolved by the gate at `phase start`
outputs:
  - docs/plan/<slug>/epics/
  - docs/plan/<slug>/stories/
  - docs/plan/<slug>/sprints/
gate:
  template: templates/prd.md            # incoming artifact must pass
  provenance: [constitution-set]         # hashes must be current
subagents:                                # owned by this skill; compiled as plan-<name>
  - name: epic-writer
    file: subagents/epic-writer.md
    writes: candidate                     # producer: writes under candidate.root
    inputs: [prd, context-bundle]
    outputs: [epics]
  - name: story-writer
    file: subagents/story-writer.md
    writes: candidate
    inputs: [epic, context-bundle]
    outputs: [stories]
  - name: skill-spec-writer
    file: subagents/skill-spec-writer.md
    writes: candidate
  - name: dependency-mapper
    file: subagents/dependency-mapper.md
    writes: candidate
  - name: estimator
    file: subagents/estimator.md
    writes: candidate
  - name: critic
    file: subagents/critic.md
    writes: evidence                      # judge: findings file under work/<run>/evidence/<agent>/ only
subphases:                                # `sequencer` sub-phases dispatch no LLM
  - id: gate
    sequencer: phase start
  - id: slice
    sequencer: phase start
  - id: epics
    subagent: epic-writer
    isolation: required
  - id: stories
    subagent: story-writer
    isolation: required
    repeat: per-epic
  - id: skill-specs
    subagent: skill-spec-writer
    isolation: preferred
  - id: sprints
    subagent: dependency-mapper
    isolation: preferred
  - id: review
    subagent: critic
    isolation: required
  - id: record
    sequencer: phase next
  - id: handoff
    sequencer: phase next
templates:                                # owned by this skill
  - templates/epic.md
  - templates/story.md
  - templates/sprint.md
  - templates/skill-spec.md               # plan is the sole owner of this template
handoff:
  outcomes:                               # selected by envelope status; see 02-skill-roster.md
    pass: ["/dev {first_story}"]
    assumptions: ["/clarify {story}", "/dev {first_story}"]
    skill_specs: ["/skill-gen {spec}", "/dev {first_story}"]
    analyze_gaps: ["/plan {slug} --retry"]
    gate_fail: ["/architect {slug} --retry"]
  also_possible: ["/analyze {slug}", "/status"]
```

`isolation` semantics:

- `required` — must run in a separate context window. If the target cannot isolate, the compiler emits a warning and the skill refuses to run in that target.
- `preferred` — separate window if available; sequential prompt otherwise.

## Compiled layouts

### Claude Code

```
.claude/
  skills/<name>/SKILL.md              # thin provider adapter; exposes /<name>
  skills/<name>/templates/
  agents/<skill>-<worker>.md          # one per skill-owned worker, e.g. dev-tdd-red-tester.md
  settings.json                       # hooks + permission fragment from 09; installed by init
```

Claude adapters request provider-native worker isolation through `agents/*.md`
tool and model declarations. A worker's `tools` list follows its role: a producer
declares `Read, Grep, Glob, Edit, Write` plus `Bash(devforgeai run *)`, a judge
declares `Read, Grep, Glob, Write` plus `Bash(devforgeai status)`, its Write
confined by the dispatcher to `.devforgeai/work/<run>/evidence/<agent>/`. Every worker returns
one `devforgeai.worker-result/v1` receipt naming the paths it claims inside the
candidate root. Isolation is a declaration compiled into the target profile;
verifying it at runtime is `12-post-mvp.md#pm-01`.

### Claude Code subagent facts the compile step relies on (docs read 2026-09-02)

| Fact | Consequence for DevForgeAI |
|---|---|
| Subagents are discovered only in `.claude/agents/`, `~/.claude/agents/`, `--agents`, managed settings, and plugin `agents/` directories. A skill's own `agents/` directory is never scanned. | `<skill>/agents/<role>.md` is source. skill-generator copies each into `.claude/agents/<skill>-<role>.md` at compile time; `init` installs the dev set from `examples/hooks/agents/claude/`. Nothing runs until that copy exists. |
| A non-fork subagent receives its file body as system prompt, the task message, the CLAUDE.md hierarchy, a git-status snapshot, and the full content of any skill named in `skills:`. It does not receive conversation history. | The worker body carries the persona and the phase guidance itself. A body that says "read references/<phase>.md first" is ceremony; skill-generator compiles that reference into the agent body. |
| Frontmatter fields: `name`, `description`, `tools`, `disallowedTools`, `model`, `permissionMode`, `maxTurns`, `skills`, `mcpServers`, `hooks`, `memory`, `background`, `isolation`, `effort`, `color`. `name` is lowercase with hyphens; underscores are accepted in practice (verified today), no `:`. | Canonical worker names stay as the registry has them. `tools` is a comma list of real tool names. `maxTurns` is a deterministic cap and belongs on every worker. `permissionMode` is left to inherit. |
| The main agent cannot be forced to delegate through the Agent tool; it chooses by `description`. An `@agent-<name>` mention guarantees invocation. `Agent(<name>)` permission rules control which subagents may be spawned. | The dispatch loop names the worker explicitly, the settings fragment denies every `Agent(...)` except the current phase's worker, and the Stop hook blocks the turn until the handoff exists. Descriptions carry when-to-use language so delegation matches. |
| Per-subagent `hooks:` (PreToolUse, PostToolUse, Stop) in `.claude/agents/` frontmatter require workspace trust since v2.1.218. Project-level `SubagentStart`/`SubagentStop` hooks in settings match on agent name. | Hooks stay in the project settings fragment (one dispatcher); no per-agent frontmatter hooks in the MVP. |
| `skills:` preloads whole skills into the subagent, not files. | Not used: workers get their guidance in the body, and the primary window's SKILL.md is not loaded into workers. |
| `isolation: worktree` needs git; `memory:` persists per agent; `background: true` drops tools such as AskUserQuestion. | `memory:` and `background:` are post-MVP (`12-post-mvp.md`); workers run foreground and without memory. The framework does not use `isolation: worktree`, and does not use `EnterWorktree`: both fork from HEAD, which would split the linear phase history the run's candidate root depends on. The sequencer creates and owns that root itself (`10-sequencer-and-contracts.md`), and a worker writes inside the root it is given. |

### Codex

```
AGENTS.md                       # project-level guidance; one section per skill
.agents/skills/<name>/SKILL.md  # repo skills; Codex scans every .agents/skills/ up to repo root
.agents/skills/<name>/templates/
.codex/agents/<skill>-<role>.toml # provider-native worker profiles; `writes: candidate | evidence | none` per role
.codex/hooks.json                 # hook fragment from 09; installed by init
.codex/config.toml                # workspace sandbox fragment from 09; installed by init
```

A shared capability or skill specification owns provider-neutral semantics, but
its Claude Code and Codex adapters are separate generated artifacts whenever
frontmatter, invocation policy, or agent configuration differs. Claude Code
supports provider extensions such as invocation-control frontmatter. Codex has
built-in slash commands and deprecated user-local custom prompts invoked as
`/prompts:<name>`; reusable repository skills are invoked explicitly as
`$<name>` or selected implicitly only when their Codex policy permits it. Codex
skill policy belongs in target-side configuration such as `agents/openai.yaml`,
not in Claude-only frontmatter.

Frontmatter rule, one statement: portable `SKILL.md` frontmatter is exactly the
six open-standard fields (`name`, `description`, `license`, `compatibility`,
`metadata`, `allowed-tools`), because the standard's validator rejects unknown
keys. A provider-specific key such as `argument-hint` or
`disable-model-invocation` is documented as target-side and is compiled by
skill-generator into the Claude target's `SKILL.md` only when the Claude target
is selected; it never appears in the neutral spec, in `metadata`, or in a Codex
adapter. Pin each target version in `techstack.md`; generated files alone do not
establish runtime support.

Persistent Research is an explicit-only exception to any target's implicit
skill-selection policy. Its only current provider forms are
`/research <slug> --request <request-file> --confirm-request <sha256>` for
Claude and `$research <slug> --request <request-file> --confirm-request
<sha256>` for Codex. Implicit selection may not open a run or write durable
Research state.

A generated Research adapter is an uninstalled candidate until its required
provider-native agent profiles, invocation controls, and hooks are present and
independently validated. Installation is a human release action, not a
generation outcome; the deferred runtime-verification contract is
`12-post-mvp.md#pm-01`.

Worker status on both providers is the closed set `pass | fail | needs_user |
could_not_run`, with `reason_code` in `runner_missing | timeout | network |
hook_fault` whenever the status is `could_not_run`. `gate_policy` (`BLOCK |
REQUIRE_HUMAN | WARN | OFF`) is a defect-to-action map declared per artifact and
is never a returned status. A generated adapter for either target returns
exactly this set and never maps a failure to `pass`. Research keeps its separate
typed status vocabulary under `src/devforgeai/skills/research/`.

The actor boundary — what each provider's hooks can identify, which direct
writes are denied, and how a worker result is bound to a real agent identity —
is stated once in `09-hook-dispatcher.md`. This document does not restate it.

## Source layout in the DevForgeAI repository

Decided 2026-09-03. `src/` holds only what the installer deploys into a target project's operational folders, and each `src/` subfolder mirrors its destination one to one:

| Source | Installed to | Holds |
|---|---|---|
| `src/devforgeai/` | `.devforgeai/` | provider-neutral skill sources (`skills/<name>/`: capability, workflow, contracts, templates, later `skill.yaml`), hook dispatcher, sequencer |
| `src/claude/` | `.claude/` | Claude adapters: `skills/<name>/SKILL.md`, `agents/*.md` |
| `src/agents/` | `.agents/` | Codex skill adapters: `skills/<name>/SKILL.md`, `agents/openai.yaml` |
| `src/codex/` | `.codex/` | Codex agent profiles and hooks |
| `python/devforgeai/` | site-packages via the wheel | the Python package (Research Core, CLI); never copied into a target tree |

The neutral copy of a skill's supporting material lives once, under `src/devforgeai/skills/<name>/`. The installer copies it into each provider adapter's `references/` at install time, flattened to one level as the Agent Skills specification recommends, and `skill-validator` diffs every installed copy against the neutral source. No `references/` folder is hand-maintained under `src/claude/` or `src/agents/`. Adapter `SKILL.md` files cite the skill-relative `references/<file>` path, which is what exists at runtime; design documents and worker prompts cite the neutral `src/devforgeai/skills/<name>/` path.

## Shared assets

The state schema, the handoff envelope and its renderer, `stack.yaml`, and each skill's templates are provider-neutral and stored once under `.devforgeai/`. Compiled files reference them by path; they are not duplicated. The sequencer renders the handoff; no adapter renders its own.

## Validation

skill-validator runs after every compile and checks:

1. For non-Research anatomy skills, anatomy compliance: all seven sub-phase kinds present; Gate, Slice, Record and Handoff bound to the sequencer operations that perform them; Work, Write and Review each bound to a named worker; persona and critic separated; Work may repeat. Research is checked against `src/devforgeai/skills/research/` instead.
2. For non-Research anatomy skills, the primary window contract: compiled SKILL.md reads nothing but `state.yaml`, contains no inline content prompts, dispatches every LLM sub-phase, and exposes a Bash grammar no wider than `devforgeai status | phase start <skill> <arg> | phase fail --reason | validate | promote <run>`. Every worker profile declares `writes: candidate`, `writes: evidence` or `writes: none` and a tool list matching that role. Research uses its uninstalled provider-adapter source contract and deterministic Core contract instead; live provider execution remains unavailable.
3. Provider best practices for the target, including the six-field portable frontmatter rule and target-side placement of provider-specific keys.
4. Conformance to the originating spec document (for project-specific skills).
5. Handoff block present, `handoff.outcomes` covers every status the skill can return including `could_not_run`, no outcome has an empty next-steps list, and every command referenced exists in the target.
