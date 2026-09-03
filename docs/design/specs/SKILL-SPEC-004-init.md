---
id: SKILL-SPEC-004
skill_name: init
target: both
status: approved
template: skill-spec
template_version: 1
author: "DevForgeAI spec author (wave 2)"
date: 2026-09-02
depends_on:
  - source: docs/design/10-sequencer-and-contracts.md#2-cli-grammar
    hash: sha256:231b93094676198b131720e581f044d8c66b4f0b8dcd3dcb35e4350100807090
    excerpt: |
      Skills whose kind is `none` have no phases and never open a run; their command is a thin wrapper over a deterministic operation. `status` wraps `devforgeai status`; the installer skill wraps the installer, which is not part of this grammar.
  - source: docs/design/10-sequencer-and-contracts.md#4-per-skill-phase-registry
    hash: sha256:511733ee35ca74fd5a5c0b59f225d7d975788e7d43d939f44c23b7aa8460cff0
    excerpt: |
      | init | none | — | none; the command is a thin wrapper over the deterministic installer, and `devforgeai phase start` refuses it |
  - source: docs/design/09-hook-dispatcher.md#5-provider-configuration-and-installation
    hash: sha256:57561a943867bc2ab6a76fb718050bd27e955019d02169cdc9062065eca438b9
    excerpt: |
      For Codex, install the example files as follows (merge existing files; do not overwrite unrelated settings):
  - source: docs/design/02-skill-roster.md#init
    hash: sha256:0917d5a622cc649b55fb714b637903ed5496d60836de49881a8ee199d0d74290
    excerpt: "- Zero LLM workers. `SKILL.md` is a thin wrapper over its bundled `scripts/install.py`; everything below is deterministic."
  - source: docs/design/02-skill-roster.md#handoff-decision-tables
    hash: sha256:1dac784b4670cc7559f323011dfe304dfe8c0baf349063162f90d76d902c5d3c
    excerpt: |
      | init | greenfield | `/brainstorm {slug}` |
      | init | brownfield | `/onboard` |
      | init | target unsupported | `/init --target {other}` |
  - source: docs/design/11-artifact-registry.md#4-upstream-and-downstream-per-skill
    hash: sha256:cfcaef76005176490e96b9e67c8fa4f0b7a6a2e13b6badf856468881fbe25200
    excerpt: |
      | init | — | the target repository | `state.yaml`, documentation skeleton, hook files | onboard, brainstorm |
  - source: docs/design/01-skill-anatomy.md#state-file
    hash: sha256:cec96cadc465f6269eaf0756ef40ff4299302e0754cd4cd887a2c44e50d4851d
    excerpt: "`/status` renders this file. Only the `devforgeai` sequencer writes it, and only at `phase start` (registering the run), at promotion or abandonment, and at `phase fail`; Research state is written only by Research Core."
  - source: docs/design/01-skill-anatomy.md#handoff-contract
    hash: sha256:dc50836dc15a928b0c4758ef3a671c6f78d5c7db7ea207c923b917d89faa9e96
    excerpt: |
      4. **Cold-session safe.** Every command works from a fresh session with no memory of this run, because it reads `state.yaml`.
  - source: docs/design/05-subagent-sets.md#sets-per-skill
    hash: sha256:9e12f3beb236a025c18d40e741c09ba675bd71d2d87f56e2b205c7556b944bf9
    excerpt: "| init | none; `SKILL.md` is a thin wrapper over its bundled `scripts/install.py` |"
  - source: docs/design/03-brownfield.md#entry-flow
    hash: sha256:4cc41530e239bbce842a2a0ce623ca484bf200e48bbc85c45ef60fc0f3948118
    excerpt: |
      /init  →  detects code  →  mode: brownfield  →  /onboard  →  /architect <slug>  →  /plan <slug>
  - source: docs/design/12-post-mvp.md#pm-01
    hash: sha256:84de4052d2f508313af4d327a9b15b9f9abcd1d50ca563ce68d4bbfdea39785e
    excerpt: |
      | Rung served | 2 (deterministic validators inside the pipeline). |
  - source: docs/design/12-post-mvp.md#pm-03
    hash: sha256:b6a4efe70a273ee76afe0340e88f24b53ebc57843476273749b94c98ca75f577
    excerpt: |
      Until PM-03 lands: project hooks are trusted by definition hash through `/hooks` and remain user-disableable. That hole is covered by PM-10, not by a managed layer.
---

# Skill Specification: init

A stranger with no conversation history must be able to build this skill from this document alone. Every question the generator would otherwise ask is answered below.

`init` is one of the two roster skills with no LLM workers and no phases. `10-sequencer-and-contracts.md` section 4 records its `kind` as `none`, and `devforgeai phase start init` refuses with exit 1. Everything `init` does is a deterministic script plus one model-callable sequencer read.

`init` is also the one exception to the write model every other skill follows. Every anatomy-governed run gets a candidate root that the sequencer creates at `phase start`, and that run's document writers write only inside it. `init` opens no run, so it has no candidate root: it writes `.devforgeai/` directly in the canonical checkout, and the dispatcher bounds that window at both ends. A write under `.devforgeai/` is permitted only while no `.devforgeai/state.yaml` exists, every other path is denied inside that window, and every `.devforgeai/` path is refused by name once the seed state file is on disk. Section 9 records the decision and the line that forced it.

## 0. Generator instructions

These instructions are addressed to the skill-generating agent (Anthropic's `skill-creator` skill, or DevForgeAI's `skill-generator`). They replace its interview.

### Cold-session prompt

Paste this into a fresh session from the repository root:

```
Use the skill-creator skill to build the skill specified in docs/design/specs/SKILL-SPEC-004-init.md.
Follow its section 0 exactly. Output directory: .devforgeai/skills. Eval mode: quick.
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
6. **Output location** is given in the prompt. Create `.devforgeai/skills/init/`. Do not write anywhere else except the `init-workspace/` sibling that eval runs require.
7. **On ambiguity, stop before output.** If the spec is still `draft`, contains an unresolved authoring assumption, omits a section, contradicts itself, or leaves a decision this document does not make, do not guess and do not write candidate skill files. End with a list titled `SPEC GAPS` naming each section and question. The spec author fixes and approves the spec before re-running.
8. **Fidelity over creativity.** Use the description in section 3 verbatim. This skill has no worker contracts, so it produces no `agents/` directory. Do not add steps, tools, or behaviours the spec does not mention.
9. **Finish with the acceptance checks** in section 14 and include their output in your final message.

### Payload the generator must copy

`init` ships the files it installs as its own `assets/` payload. Copy these bytes verbatim from `docs/design/examples/hooks/` at generation time:

| Source in this repository | Destination inside the generated skill |
|---|---|
| `docs/design/examples/hooks/dispatch.py` | `assets/hooks/dispatch.py` |
| `docs/design/examples/hooks/policy.py` | `assets/hooks/policy.py` |
| `docs/design/examples/hooks/devforgeai.py` | `assets/hooks/devforgeai.py` |
| `docs/design/examples/hooks/settings.claude.json` | `assets/claude/settings.json` |
| `docs/design/examples/hooks/agents/claude/*.md` | `assets/claude/agents/*.md` |
| `docs/design/examples/hooks/hooks.codex.json` | `assets/codex/hooks.json` |
| `docs/design/examples/hooks/config.codex.toml` | `assets/codex/config.toml` |
| `docs/design/examples/hooks/agents/*.toml` | `assets/codex/agents/*.toml` |

`assets/hooks/devforgeai` (the wrapper in section 6) and `assets/state.yaml` (the seed in section 6) are authored from this specification, not copied.

## 1. Identity

| Field | Value |
|-------|-------|
| name | `init` (kebab-case, max 64 chars, equals the directory name, no `claude`/`anthropic` prefix) |
| title | DevForgeAI Installer |
| purpose | Install the DevForgeAI enforcement chain into a repository — sequencer, hook dispatcher, shared policy library, the `devforgeai` wrapper, the state file, and the selected provider's settings fragment — and record which entry phase the project starts from. |
| category | devforgeai-phase |
| version | 1.0.0 (skill-package version written to `metadata.version`; not the DevForgeAI or Research Core version) |

## 2. Problem and requirements

**Without this skill:** a user who wants DevForgeAI in a repository has to hand-copy nine files out of `docs/design/examples/hooks/`, know that `dispatch.py`, `policy.py` and `devforgeai.py` must sit in the same directory because the dispatcher resolves the sequencer as `Path(__file__).with_name("devforgeai.py")`, know that the Claude and Codex hook entries reference `.devforgeai/hooks/dispatch.py` by absolute path, and know that every model-callable Bash rule is written against the bare token `devforgeai`, which resolves through `$PATH` and not through a path the settings file contains. Any one of those missed steps produces the failure mode `09-hook-dispatcher.md` section 9 names as the worst one: hooks that fail open. A missing dispatcher is the single fault a later hook cannot report, which is why `devforgeai session-start` records `hooks_armed` at all. The user then runs a whole story believing writes are fenced when nothing is checking them.

The second failure is choosing the wrong entry phase. `03-brownfield.md`'s entry flow branches at `/init`: an existing codebase must reach `/onboard` before `/architect`, and a fresh repository must reach `/brainstorm`. A user who guesses wrong writes an INTENDED constitution over a codebase nobody has mapped.

| ID | Kind | Requirement |
|----|------|-------------|
| R1 | explicit | Install `.devforgeai/` with `state.yaml`, `hooks/dispatch.py`, `hooks/policy.py`, `hooks/devforgeai.py`, `sessions/`, `work/` and `provenance/`, per `02-skill-roster.md#init` and `09-hook-dispatcher.md` section 5. |
| R2 | explicit | Install the project settings fragment for the chosen target: `.claude/settings.json` and `.claude/agents/` for `claude`; `.codex/config.toml`, `.codex/hooks.json` and `.codex/agents/` for `codex`; both for `both`. |
| R3 | explicit | Detect whether code exists and record `mode: greenfield` or `mode: brownfield` in `state.yaml`. |
| R4 | explicit | Hand off to `/brainstorm <slug>` for greenfield and `/onboard` for brownfield, per `02-skill-roster.md`'s init rows. |
| R5 | implicit | Make the bare token `devforgeai` resolve, because `dispatch.py` compares `argv[0]` to the literal string `devforgeai` and blocks anything else, and because the Claude allow rules are written as `Bash(devforgeai status)` and its three siblings. |
| R6 | implicit | Merge into an existing provider settings file rather than overwriting unrelated settings, per `09-hook-dispatcher.md` section 5. |
| R7 | implicit | Refuse a repository that already carries `.devforgeai/state.yaml`, per `02-skill-roster.md`'s gate column for init, and change nothing on that path. |
| R8 | discovered | The detection rule reads no file's contents and maps no filename to a language, package manager, or command; it counts surviving paths and nothing else. `03-brownfield.md` assigns that discovery to onboard's `code_mapper` and the `stack.yaml` contract, and `02-skill-roster.md#init` states it as a prohibition on init. |
| R9 | discovered | Write nothing under `.devforgeai/` after the install completes. `01-skill-anatomy.md#state-file` makes the sequencer the only writer of `state.yaml` from `phase start` onward; init writes the seed before any run exists and then stops. The dispatcher permits a `.devforgeai/` write only while no `state.yaml` exists and refuses every `.devforgeai/` path by name afterwards, so the rule is a deny decision rather than an instruction. |
| R10 | discovered | Produce no `handoff.json`. That file is written by `devforgeai phase next` and `devforgeai phase fail`, and init opens no run. Its cold-session guidance is the `next` key it seeds in `state.yaml`, which `devforgeai status` prints. |

## 3. Description

The exact frontmatter `description`:

```yaml
description: >
  Install DevForgeAI into this repository. Use this skill whenever someone wants
  to set DevForgeAI up, add the enforcement hooks, wire the sequencer into Claude
  Code or Codex, start a spec-driven workflow here, or asks what to run first in a
  repository that has no .devforgeai directory yet. It copies the sequencer, hook
  dispatcher and policy library into .devforgeai/hooks, makes the devforgeai
  command resolvable, writes the seed state file, installs the settings fragment
  for the chosen target, decides greenfield or brownfield from what is already in
  the tree, and prints the first command to run. Do NOT use it to re-install over
  an existing .devforgeai/state.yaml, to map an existing codebase (use onboard),
  or to print current progress (use status).
```

Character count: 756 / 1024.

## 4. Trigger set

```json
[
  {"query": "set up devforgeai in this repo", "should_trigger": true},
  {"query": "I just cloned an empty repo for a new CLI tool and I want the spec-driven workflow with the hooks and everything — where do I start?", "should_trigger": true},
  {"query": "install the hook dispatcher and the sequencer for codex please", "should_trigger": true},
  {"query": "add devforgeai to ~/work/billing-service, it's an existing django app, target both providers", "should_trigger": true},
  {"query": "how do i bootstrap this project so the write fence actually works", "should_trigger": true},
  {"query": "there's no .devforgeai directory here yet, can you fix that", "should_trigger": true},
  {"query": "wire up claude settings.json so the phase workers are fenced to their own candidate root", "should_trigger": true},
  {"query": "we're starting a greenfield service, get the framework in place and tell me the first command", "should_trigger": true},
  {"query": "initialise devforgeai wiht target claude and slug invoice-api", "should_trigger": true},
  {"query": "my teammate set this up on their machine, I need the same thing locally in /repos/atlas", "should_trigger": true},
  {"query": "map the existing code and write the OBSERVED sections", "should_trigger": false},
  {"query": "what phase am I in and what should I run next", "should_trigger": false},
  {"query": "regenerate the dev-tdd skill from its spec", "should_trigger": false},
  {"query": "the SubagentStop hook is exiting 2 on every worker, debug it", "should_trigger": false},
  {"query": "add pytest and ruff to the allowed packages in stack.yaml", "should_trigger": false},
  {"query": "create a new git repository and make the first commit", "should_trigger": false},
  {"query": "write the constitution and the techstack document for this project", "should_trigger": false},
  {"query": "npm init -y then install typescript and set up the tsconfig", "should_trigger": false},
  {"query": "reinstall the hooks, I think someone edited dispatch.py by hand", "should_trigger": false},
  {"query": "start the first story, STORY-001", "should_trigger": false}
]
```

The two near-misses that carry the most signal are "what phase am I in and what should I run next", which belongs to `status` and shares init's vocabulary about first commands, and "reinstall the hooks", which shares init's whole subject but hits R7: a repository with `.devforgeai/state.yaml` is refused, and the repair is a human deleting the tree, not a second install.

## 5. Use cases

### UC-1: Greenfield repository, both targets
- **User says:** "set up devforgeai here, I'm starting a new invoice service"
- **Steps:**
  1. Parse `--target` (default `both`) and `--slug` (default the sanitised repository directory name, here `invoice-service`).
  2. Run `python scripts/install.py --root . --target both --slug invoice-service`.
  3. The installer refuses if `.devforgeai/state.yaml` exists; here it does not.
  4. The installer copies the payload, writes the wrapper, links it onto `$PATH`, writes the seed `state.yaml` with `mode: greenfield` and `next: "/brainstorm invoice-service"`, and installs both provider fragments.
  5. Run `python scripts/check_install.py --root .` and print its report.
  6. Run `devforgeai status` and print its output.
- **Result:** `.devforgeai/` exists with the six installed paths, `.claude/` and `.codex/` carry the fragments, `devforgeai status` prints `enforcement: {}` and `next: /brainstorm invoice-service`, and the user's next command is on screen.

### UC-2: Existing codebase, Codex only
- **User says:** "add devforgeai to this repo, we already have the whole billing service in `src/`, I only use codex"
- **Steps:**
  1. Parse `--target codex`; slug defaults to the repository directory name.
  2. `scripts/detect_mode.py` walks the tree, finds files under `src/` that survive the ignore set, and prints `brownfield`.
  3. `scripts/install.py` writes `mode: brownfield` and `next: "/onboard"`, installs `.codex/config.toml`, `.codex/hooks.json` and `.codex/agents/`, and installs nothing under `.claude/`.
  4. `scripts/check_install.py` reports every installed path plus whether `devforgeai` resolves.
  5. `devforgeai status` prints the seeded `next`.
- **Result:** the project is installed for one target, and the handoff sends the user to `/onboard` rather than `/brainstorm`, because an unmapped codebase must not receive an INTENDED constitution first.

### UC-3: Already installed
- **User says:** "install devforgeai again, I want the latest hooks"
- **Steps:**
  1. `scripts/install.py` finds `.devforgeai/state.yaml`, writes the refusal to stderr, and exits 1 without touching a byte.
  2. The skill prints the refusal and the one repair route: remove `.devforgeai/`, `.claude/settings.json`, `.codex/config.toml` and `.codex/hooks.json` by hand, then re-run `/init`.
- **Result:** nothing changed. An in-place upgrade path does not exist, and inventing one would silently replace a dispatcher whose definition hash the user has already trusted through the provider hook-review command.

## 6. Inputs and outputs

### Inputs
| Input | Format | Example file | Required |
|-------|--------|--------------|----------|
| target | one of `claude`, `codex`, `both`; command flag | not a file | no; defaults to `both` |
| slug | lowercase kebab-case, command flag | not a file | no; defaults to the sanitised repository directory name |
| repository root | directory | `fixtures/init/empty/`, `fixtures/init/packaged/` | yes |
| payload | the files listed in section 0 | `assets/hooks/`, `assets/claude/`, `assets/codex/` | yes |

`init` gates on no incoming artifact. `11-artifact-registry.md` section 4 lists its upstream as `—` and its input as "the target repository".

### Outputs
| Output | Format | Location | Template |
|--------|--------|----------|----------|
| seed state file | YAML | `.devforgeai/state.yaml` | `assets/state.yaml` |
| sequencer | Python | `.devforgeai/hooks/devforgeai.py` | `assets/hooks/devforgeai.py` |
| hook dispatcher | Python | `.devforgeai/hooks/dispatch.py` | `assets/hooks/dispatch.py` |
| shared policy library | Python | `.devforgeai/hooks/policy.py` | `assets/hooks/policy.py` |
| command wrapper | POSIX shell, mode 0755 | `.devforgeai/hooks/devforgeai` | `assets/hooks/devforgeai` |
| evidence directories | empty directories | `.devforgeai/work/`, `.devforgeai/sessions/`, `.devforgeai/provenance/` | none |
| work-directory ignore rule | one-line gitignore | `.devforgeai/work/.gitignore`, holding `*` | none |
| Claude fragment | JSON | `.claude/settings.json` | `assets/claude/settings.json` |
| Claude worker profiles | Markdown | `.claude/agents/*.md` | `assets/claude/agents/*.md` |
| Codex config fragment | TOML | `.codex/config.toml` | `assets/codex/config.toml` |
| Codex hook fragment | JSON | `.codex/hooks.json` | `assets/codex/hooks.json` |
| Codex worker profiles | TOML | `.codex/agents/*.toml` | `assets/codex/agents/*.toml` |
| install report | JSON on stdout | not a file | none |

`11-artifact-registry.md` section 1 records that `init` owns no template: it produces no gated artifact and therefore has no template header for a downstream gate to check. `state.yaml` has no template in the registry either; its shape is fixed by `01-skill-anatomy.md#state-file` and its enforcement block by `schemas/devforgeai/v1/enforcement.schema.json`.

### Output template: the seed `state.yaml`

`SLUG`, `MODE`, `TARGETS`, `NEXT` and `TIMESTAMP` are substituted by the installer; nothing else varies.

```yaml
version: 1
target: TARGETS            # [claude], [codex], or [claude, codex]
mode: MODE                 # greenfield | brownfield
slug: SLUG
phase: init
phases:
  init: {status: done, at: TIMESTAMP}
stories: {}
runs: {}
enforcement: {}
next: NEXT                 # "/brainstorm SLUG" for greenfield, "/onboard" for brownfield
```

`enforcement: {}` is the value `10-sequencer-and-contracts.md` section 9 requires when no run is active. `stories` and `runs` are the two mappings the hook dispatcher reads to decide whether a run is live.

### Output template: `.devforgeai/hooks/devforgeai`

Mode 0755. Written by the installer, not copied.

```sh
#!/bin/sh
# DevForgeAI sequencer wrapper. The model-callable Bash grammar is written
# against the bare token `devforgeai`; this file is what that token resolves to.
exec python3 "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/devforgeai.py" "$@"
```

### Output template: the install report

`scripts/install.py` prints one JSON object to stdout. `check_install.py` prints the same shape with an added `problems` array.

```json
{
  "root": "/absolute/path/to/repository",
  "target": "both",
  "slug": "invoice-service",
  "mode": "greenfield",
  "docs_present": false,
  "git_repository": true,
  "installed": [".devforgeai/state.yaml", ".devforgeai/hooks/devforgeai.py"],
  "merged": [".claude/settings.json"],
  "wrapper": ".devforgeai/hooks/devforgeai",
  "path_link": "/home/user/.local/bin/devforgeai",
  "next": "/brainstorm invoice-service"
}
```

`path_link` is `null` when no directory in the preference list is both on `$PATH` and writable; section 9 records what the skill prints then.

### Return envelope

Not applicable. `init` dispatches no worker, so no `devforgeai.worker-result/v1` object is produced or consumed. `05-subagent-sets.md#sets-per-skill` records init's worker set as none, and `10-sequencer-and-contracts.md` section 4 gives it `kind: none` with no phases.

## 7. Procedure

### Steps

The `SKILL.md` body. Each step names the file that carries its detail; `SKILL.md` holds the loop and nothing else.

1. Parse `--target` (`claude`, `codex`, `both`; default `both`) and `--slug` (default the repository directory name, lowercased with every run of non-alphanumeric characters collapsed to a single hyphen and leading and trailing hyphens trimmed) — why: both values are written into `state.yaml`, and the slug is what the greenfield handoff hands to `/brainstorm`, so a wrong value costs a re-install that R7 forbids.
2. Reject a `--target` value outside the three names by printing `/init --target claude`, `/init --target codex` or `/init --target both` and stopping — why: `02-skill-roster.md`'s init decision table has a `target unsupported` row whose next step is `/init --target {other}`, and a fourth target has no fragment in `assets/`.
3. Run `python scripts/install.py --root . --target TARGET --slug SLUG` — why: the install is deterministic and file-by-file, and a script that exits 1 on a conflict is checkable in a way that a model copying files is not. Read `references/install.md` before changing any flag.
4. On exit 1, print the script's stderr and stop — why: exit 1 is either an existing `.devforgeai/state.yaml` (R7) or a settings conflict the user must resolve; both repairs are human, and re-running with different flags would overwrite something the user did not agree to.
5. Run `python scripts/check_install.py --root .` and print its report — why: the installer reports what it wrote, and the checker reports what is actually on disk and whether the bare token `devforgeai` resolves to the installed wrapper. `09-hook-dispatcher.md` section 9 records that a missing dispatcher is the one fault a later hook cannot report, so it is checked here rather than assumed.
6. When `check_install.py` reports `path_link: null`, print the exact `ln -s` line it emits and say that the model-callable Bash grammar does not work until the user runs it — why: `dispatch.py` compares the first argv element to the literal string `devforgeai`, so an absolute-path invocation is blocked by the same check that blocks an arbitrary command. `references/wrapper.md` holds the full explanation.
7. Run `devforgeai status` and print its output verbatim — why: this is the one model-callable sequencer operation init uses, it is the same rendering `/status` prints, and it shows the seeded `next` so the handoff is a fact read from `state.yaml` rather than a sentence the model composed.
8. Tell the user to trust the project and review the hook definitions with the provider hook-review command — why: `09-hook-dispatcher.md` section 5 makes trust a human action on both providers, and a changed definition gets a new hash and must be reviewed again. No script can perform it.

### Sub-phases and workers

`01-skill-anatomy.md`'s seven sub-phases govern anatomy skills that open a run. `init` opens none: `10-sequencer-and-contracts.md` section 4 gives it `kind: none` and states that `devforgeai phase start` refuses it. The mapping is therefore degenerate and is recorded here so the generator does not invent phases.

| # | Sub-phase | Performed by | Isolation |
|---|-----------|--------------|-----------|
| 0 | Gate | none. `devforgeai phase start init <arg>` refuses with exit 1 and the message `skill init has no LLM workers and no phases; it is a thin wrapper over a deterministic operation`. The install's own precondition is `scripts/install.py`'s refusal when `.devforgeai/state.yaml` exists. | n/a |
| 1 | Slice | none | n/a |
| 2 | Work | none. The deterministic work is `scripts/detect_mode.py` and `scripts/install.py`. | n/a |
| 3 | Write | none. The installer writes; no worker proposes. | n/a |
| 4 | Review | none. `scripts/check_install.py` verifies the tree. | n/a |
| 5 | Record | none. `devforgeai phase next` is hook-only and requires an active run. The record is the seed `state.yaml` the installer wrote. | n/a |
| 6 | Handoff | none. No `handoff.json` is written, because only `devforgeai phase next` and `devforgeai phase fail` write it and neither runs. The `next` key in `state.yaml` carries the cold-session command, and `devforgeai status` prints it. | n/a |

### Sequencer operations

`init` has no registry phases, so the evidence and gate table in `10-sequencer-and-contracts.md` section 11 has no rows to fill. The operations it uses are these, and no other.

| Operation | Access | Called by | Precondition | Effect on `init` |
|---|---|---|---|---|
| `devforgeai status` | model | step 7 of the procedure | none | prints `enforcement`, `next` and `session`; writes nothing |
| `devforgeai phase start init <arg>` | model | never | — | refuses with exit 1; recorded here so no generated `SKILL.md` calls it |
| `devforgeai phase fail --reason <text>` | model | never | a run is active | init opens no run, so the call would exit 1 |
| `devforgeai validate` | model | never | a run is active | same |
| `devforgeai promote <run>` | model | never | the run is `ready_to_promote` | init opens no run, so there is no candidate root to promote |
| `devforgeai session-start` | hook (SessionStart) | the dispatcher init installs, at the next session | hook marker present | writes `.devforgeai/sessions/<session_id>.json` with `hooks_armed`; the first evidence that the install worked |

The install itself is outside this grammar. `10-sequencer-and-contracts.md` section 2 states it plainly: "there is no operation that installs the framework: installation is the deterministic work of the installer skill, outside this grammar." `02-skill-roster.md#init` and `05-subagent-sets.md#sets-per-skill` now call the wrapper "a thin wrapper over its bundled `scripts/install.py`", which is that same deterministic operation; no `devforgeai init` exists in the sequencer's argparse, and section 9 records the resolution.

### Worker contracts

None. `init` has no worker, so the generated skill has no `agents/` directory and no `references/envelope.md`.

### Handoff outcomes

`init` writes no `handoff.json`. The rows below are the `next` value the installer seeds into `state.yaml` and the line the skill prints, and they are the corrected form of `02-skill-roster.md`'s three init rows.

| Outcome | Next steps |
|---------|------------|
| greenfield (no code found) | `/brainstorm <slug>` |
| brownfield (code found) | `/onboard` |
| target unsupported | `/init --target claude`, `/init --target codex` or `/init --target both` |
| already installed (`.devforgeai/state.yaml` exists) | remove the framework tree by hand, then `/init` |
| settings conflict (an existing provider key holds a different value) | resolve the listed keys by hand, then `/init` |
| `devforgeai` not on `$PATH` after install | run the `ln -s` line `check_install.py` printed, then `/status` |

The closed worker status set (`pass`, `fail`, `needs_user`, `could_not_run`) does not appear here because no worker returns one. `02-skill-roster.md`'s catch-all rows for `could_not_run` and unhandled errors apply to skills that open a run.

## 8. Bundled resources

### Layout

```
init/SKILL.md               # <=500 lines: identity, the eight-step loop, the outcome table
  references/install.md     # what each installed path is, in what order, and the merge rules
  references/targets.md     # per-target fragment map, and what each fragment turns on
  references/detection.md   # the greenfield/brownfield rule, verbatim, with the ignore set
  references/wrapper.md     # why the bare token must resolve, and the two ways it can
  scripts/detect_mode.py    # deterministic mode detection
  scripts/install.py        # the installer
  scripts/check_install.py  # post-install verification
  assets/hooks/             # dispatch.py, policy.py, devforgeai.py, devforgeai
  assets/claude/            # settings.json, agents/*.md
  assets/codex/             # config.toml, hooks.json, agents/*.toml
  assets/state.yaml         # the seed state file
  fixtures/init/empty/      # eval fixture: no code
  fixtures/init/packaged/   # eval fixture: a package and one source file
```

There is no `agents/` directory and no `references/envelope.md`: this skill dispatches no worker. There is no `README.md` inside the skill directory.

`SKILL.md` links to `references/`, `scripts/` and `assets/`; nothing links further, because no `agents/*.md` exists to hold a second hop.

### scripts/
| File | Purpose | Invocation | Exit codes |
|------|---------|------------|------------|
| `detect_mode.py` | Apply the section 9 detection rule to a directory and print `greenfield` or `brownfield` on the first line and a JSON object with `mode`, `docs_present`, `git_repository` and `sample_paths` on the second | `python scripts/detect_mode.py --root PATH` | 0 decided, 2 usage or unreadable root |
| `install.py` | Copy the payload, write the wrapper, link it onto `$PATH`, write the seed `state.yaml`, write `.devforgeai/work/.gitignore`, install the target fragments, print the install report | `python scripts/install.py --root PATH --target claude\|codex\|both --slug NAME` | 0 installed, 1 refused (state file exists, or a settings key conflicts), 2 usage |
| `check_install.py` | Verify every path the target requires exists, that the three hook files sit in one directory, that the wrapper is executable, that `devforgeai` on `$PATH` resolves to it, that `.devforgeai/work/` is ignored, and that both JSON fragments parse | `python scripts/check_install.py --root PATH` | 0 clean, 1 problems on stderr with the exact repair line, 2 usage |

Every script takes arguments, prompts for nothing, prints data on stdout and diagnostics on stderr, and documents `--help`. `install.py` writes each file through a temporary file in the destination directory and renames it into place, and it deletes what it created if a later step fails, so a refused install leaves no half-written tree.

### references/
| File | Content | Load when |
|------|---------|-----------|
| `install.md` | The ordered install list, the atomic-write and rollback rule, the JSON deep-merge rule for `.claude/settings.json` and `.codex/hooks.json`, the TOML limitation in section 9, the `.devforgeai/work/.gitignore` rule and why a run's candidate root depends on it, and the exact refusal messages | before running `install.py`, and whenever it exits 1 |
| `targets.md` | Which fragment goes to which path for each of the three targets, what each fragment turns on (the six Claude hook events, the seven Codex hook events, the deny and allow rules, the one-open-worker cap), and which worker profiles exist today | when the user names a target, or asks what the fragment changed |
| `detection.md` | The detection rule verbatim: the walk, the ignore set, the two facts reported, and why no language or command is inferred | when the reported mode surprises the user |
| `wrapper.md` | Why `dispatch.py` requires the bare token, the wrapper's contents, the `$PATH` preference list, and the exact `ln -s` repair | when `check_install.py` reports `path_link: null`, or a `devforgeai` call is blocked |

### assets/
| File | Used for |
|------|----------|
| `hooks/devforgeai.py` | the sequencer, installed at `.devforgeai/hooks/devforgeai.py` |
| `hooks/dispatch.py` | the hook decision dispatcher, installed beside it |
| `hooks/policy.py` | the shared path, phase, result and stack-policy library both entry points import |
| `hooks/devforgeai` | the wrapper the bare token resolves to |
| `claude/settings.json` | the project `.claude/settings.json` fragment: hooks, permission rules, `disableAllHooks: false` |
| `claude/agents/*.md` | Claude worker profiles for the dev family: `red_dev`, `green_dev` and `refactor_dev` declare `writes: candidate`, `smoke_qa` and `dev_critic` declare `writes: evidence` |
| `codex/config.toml` | the project `.codex/config.toml` fragment: hooks on, workspace sandbox, no network or login shell, apps off, one open worker |
| `codex/hooks.json` | the project `.codex/hooks.json` fragment: the same dispatcher with `--provider codex` |
| `codex/agents/*.toml` | Codex worker profiles with the same names and the same `writes` declarations as the Claude ones |
| `state.yaml` | the seed state file in section 6 |

### agents/
None. Section 7 declares no worker.

## 9. Gotchas and edge cases

| Situation | What goes wrong | What to do instead |
|-----------|-----------------|--------------------|
| An older draft of `02-skill-roster.md#init` and `05-subagent-sets.md#sets-per-skill` said `SKILL.md` is "a thin wrapper over `devforgeai init`" | There is no `init` operation. `10-sequencer-and-contracts.md` section 2 states that no operation installs the framework, and the sequencer's argparse exposes `phase`, `run`, `ingest-result`, `session-start`, `validate` and `status` and nothing else. A generated skill that calls `devforgeai init` fails with a usage error at exit 2. | Wrap `scripts/install.py`. Both sources now name `scripts/install.py` themselves, so the divergence is closed and the excerpts in this spec's `depends_on` quote the current wording; `10` remains the normative document. The only sequencer call init makes is `devforgeai status`. |
| The user asks for an in-place upgrade | Overwriting `dispatch.py` silently replaces a hook definition whose hash the user trusted through the provider hook-review command, and on Codex the changed definition must be reviewed again before it fires. A half-upgraded tree where `policy.py` and `dispatch.py` disagree fails open. | `install.py` refuses when `.devforgeai/state.yaml` exists (R7) and exits 1. The repair is a human removing the tree and re-running `/init`, then re-trusting with the provider hook-review command. |
| `.claude/settings.json` already exists with `disableAllHooks: true` | A deep merge that overwrites it silently disables the whole enforcement chain, and nothing later reports it. | `install.py` treats a scalar that is present with a different value as a conflict: it lists the key, writes nothing, and exits 1. Arrays such as `permissions.deny` are unioned in order, which is safe because on Claude a deny from any scope beats an allow from any scope. |
| `.codex/config.toml` already exists | Python's standard library reads TOML (`tomllib`) but cannot write it, so there is no faithful merge. Writing the fragment over the file destroys unrelated settings. | `install.py` writes `.codex/config.devforgeai.toml` beside the existing file, prints the exact block to merge, and exits 1. A fresh repository takes the normal path: the fragment is written directly as `.codex/config.toml`. |
| The bare token `devforgeai` does not resolve | Every model-callable operation is blocked. `dispatch.py` compares the first argv element to the literal string `devforgeai` and refuses anything else, so calling the wrapper by absolute path is blocked by the same rule that blocks an arbitrary command, and the Claude allow rules (`Bash(devforgeai status)` and its three siblings) never match either. | `install.py` links the wrapper into the first directory that is both listed in `$PATH` and writable, taking `~/.local/bin` then `~/bin` in that order. When neither qualifies it sets `path_link: null` and prints one `ln -s` line naming an absolute destination the user chooses. `check_install.py` re-checks and exits 1 until the token resolves. No packaging step, virtual environment, or shell-profile edit is part of this skill. |
| The repository is not a Git repository | Codex's `hooks.codex.json` locates the dispatcher with `$(git rev-parse --show-toplevel)`, which fails outside a work tree, so the Codex hooks never fire. A run also falls back to copy mode for its candidate root, which cannot rebase after a `STALE_BASE` and returns `needs_user` instead. | `install.py` records `git_repository: false` in the report and `check_install.py` raises it as a problem for the `codex` and `both` targets with the repair `git init`. The Claude fragment uses `${CLAUDE_PROJECT_DIR}` and is unaffected. |
| A run's candidate root would be committed to the project | Every anatomy run's candidate root lives at `.devforgeai/work/<run>/wt`. Tracked, it turns a worktree checkout into thousands of staged files and the `SessionStart` self-test reports the prerequisite as unmet. | `install.py` writes `.devforgeai/work/.gitignore` holding `*`, so the whole work tree is ignored without touching the project's own `.gitignore`. `check_install.py` re-checks that `git check-ignore` agrees, because the self-test that would otherwise report it runs only at the next session. |
| Only the five dev-family worker profiles exist | `assets/claude/agents/` and `assets/codex/agents/` carry `red_dev`, `green_dev`, `refactor_dev`, `smoke_qa` and `dev_critic`. Every other skill's workers have no installed profile, so those skills cannot dispatch until `skill-generator` produces the profiles and a human installs them. | Install what exists and say so. `templates/skill-spec.md` section 12 records that provider-native worker profiles are produced by `skill-generator`, and `12-post-mvp.md#pm-01` records that a generated adapter stays a candidate a human installs. `check_install.py` lists the five installed names rather than claiming a complete set. |
| A user expects init to detect the language or the test command | `02-skill-roster.md#init` forbids it and `03-brownfield.md` assigns it to onboard's `code_mapper`, which reports an absent value as unknown rather than guessing. A guessed command becomes a `stack.yaml` section that the transition oracle then runs. | Detect only the two facts in `references/detection.md`. Say that the stack section arrives from `/onboard` (brownfield) or `/architect <slug>` (greenfield). |
| Nothing prints a "You are here" block after the install | `01-skill-anatomy.md`'s handoff template is the rendering of `handoff.json`, which `devforgeai phase next` writes. init opens no run and writes no such file. | The `next` key in `state.yaml` is the cold-session command, and `devforgeai status` prints it. `SKILL-SPEC-017-status.md` section 9 records the same limitation from the other side. |
| The empty-directory case | A directory holding only `.gitignore`, `LICENSE` and `README.md` looks like a project to a naive file count and would be sent to `/onboard`, which has nothing to map. | The detection rule below excludes top-level dotfiles, top-level Markdown files and `LICENSE`, and excludes `docs/` entirely, so that directory is `greenfield` with `docs_present` reported separately. |
| Hooks can still be disabled after a clean install | `09-hook-dispatcher.md` section 5 records that project hooks are user-disableable on both providers, and section 9 records that a disabled hook layer is not a deny decision. | Install the fragments and say what they do and do not guarantee. The administrator-managed alternative is `12-post-mvp.md#pm-03` and the repository-level backstop is `12-post-mvp.md#pm-10`; neither is installed here. |

### The detection rule, verbatim

`scripts/detect_mode.py` walks the repository root and reports two facts.

1. Skip these directories wherever they occur: `.git`, `.devforgeai`, `.claude`, `.codex`, `.agents`, `node_modules`, `.venv`, `venv`, `__pycache__`, `dist`, `build`, `target`, `.mypy_cache`, `.pytest_cache`, `.ruff_cache`.
2. Skip the top-level `docs` directory entirely; its contents decide `docs_present`, not `mode`.
3. Skip, at the top level only, every file whose name begins with a dot, every file whose name ends in `.md`, and the file named `LICENSE`.
4. `mode` is `brownfield` when at least one file survives steps 1-3, and `greenfield` otherwise.
5. `docs_present` is true when at least one file exists under the top-level `docs` directory or at least one top-level `.md` file exists.
6. `git_repository` is true when `.git` exists at the root.

No rule reads a file's contents, and no rule maps an extension or a manifest name to a language, a package manager, or a command. `sample_paths` in the report holds at most five of the surviving paths so the user can see why the answer came out as it did. `docs_present` is reported and not written into `state.yaml`, because the sequencer owns every key in that file from `phase start` onward and an unknown key has no reader.

### Cross-cutting open items

| ID | Resolution recorded here |
|---|---|
| OI-1 | Not applicable in a mechanical sense — init dispatches no worker at all — but recorded so no generated file invents one: Slice is a step inside `devforgeai phase start`, which writes `.devforgeai/work/<run>/context.json`, and no worker performs it. init opens no run and writes no such file. |
| OI-5 | init has no resume flag. `--target` and `--slug` change what is installed, not where a previous install resumed. A second `/init` is refused by R7, not resumed. |
| OI-7 | init does not invoke `/brainstorm` or `/onboard`. The edge is the `next` key it seeds; a human or a fresh session runs that command. |
| write model | Every other skill's document writers write their template-conforming files inside the run's candidate root with Edit and Write, and that root reaches the canonical checkout only when the user runs `devforgeai promote <run>` on a run the last passing transition marked `ready_to_promote`; promotion is never automatic and is never part of Handoff (D7, as amended). `init` has no run and no candidate root: it writes `.devforgeai/` directly, and the dispatcher permits that only while no `state.yaml` exists and refuses every `.devforgeai/` path by name afterwards (`AUTHOR-BRIEF.md` section 10, item I-1). A generated `SKILL.md` that asks for a candidate root, or that writes under `.devforgeai/` a second time, is refused by the dispatcher rather than by a sentence here. |
| producer exceptions | `.devforgeai/stack.yaml` and `.devforgeai/provenance/adr/**` are the two paths a worker may write, and only from the four declared producer phases, inside the candidate root. `init` writes neither: `install.py` seeds `state.yaml` and the hook files, and the stack section arrives from `/onboard` or `/architect <slug>`. |
| OI-10 | init is the skill that fixes the missing positional argument for the rest of the roster. It writes `slug` into `state.yaml`, and `/onboard`, `/drift` and `/status` read it from there. When `--slug` is omitted the value is the sanitised repository directory name; when that sanitises to an empty string the installer exits 2 and asks for `--slug` explicitly. |

## 10. Success criteria and test cases

### Success criteria

- Triggers on the section 4 positives and not on the near-misses.
- On a directory with no `.devforgeai/`, `install.py` exits 0 and every path in section 6's output table for the selected target exists afterwards.
- On the same directory a second time, `install.py` exits 1 and the byte count of `.devforgeai/state.yaml` is unchanged.
- `detect_mode.py` prints `greenfield` for `fixtures/init/empty/` and `brownfield` for `fixtures/init/packaged/`.
- The seed `state.yaml` parses as YAML, carries `enforcement: {}`, and its `next` equals `/brainstorm <slug>` for greenfield and `/onboard` for brownfield.
- `.devforgeai/hooks/devforgeai` is mode 0755 and its first line is `#!/bin/sh`.
- `.devforgeai/work/.gitignore` exists and holds `*`, so a run's candidate root is ignored.
- `check_install.py` exits 0 on a clean install where the wrapper resolves, and exits 1 naming the missing path otherwise.
- `devforgeai status` exits 0 after the install and its output contains the seeded `next`.
- No file outside `.devforgeai/`, `.claude/`, `.codex/` and the chosen `$PATH` link directory is created or modified.

### evals/evals.json (used verbatim)

```json
{
  "skill_name": "init",
  "evals": [
    {
      "id": 1,
      "prompt": "Set up devforgeai in this repository for both providers. Use the slug demo-app.",
      "expected_output": "A greenfield install: .devforgeai/ with the seed state file and the three hook files plus the wrapper, .claude/ and .codex/ fragments, and a printed next step of /brainstorm demo-app.",
      "files": ["fixtures/init/empty"],
      "expectations": [
        "scripts/install.py was run with --target both and --slug demo-app and exited 0",
        ".devforgeai/state.yaml exists and parses as YAML with mode: greenfield, slug: demo-app and enforcement: {}",
        "the value of the next key in .devforgeai/state.yaml is exactly /brainstorm demo-app",
        ".devforgeai/hooks/ contains devforgeai.py, dispatch.py, policy.py and an executable devforgeai wrapper whose first line is #!/bin/sh",
        ".devforgeai/work/, .devforgeai/sessions/ and .devforgeai/provenance/ all exist",
        ".devforgeai/work/.gitignore exists and its content is a single line reading *",
        ".claude/settings.json parses as JSON and .codex/hooks.json parses as JSON",
        "the transcript shows devforgeai status being run and its output printed",
        "no worker or subagent was dispatched"
      ]
    },
    {
      "id": 2,
      "prompt": "Add devforgeai to this repo. I only use codex.",
      "expected_output": "A brownfield install for the codex target: mode brownfield, next /onboard, .codex/ fragments present and no .claude/ directory created.",
      "files": ["fixtures/init/packaged"],
      "expectations": [
        "scripts/detect_mode.py or install.py reported brownfield for this directory",
        ".devforgeai/state.yaml has mode: brownfield and its next key is exactly /onboard",
        ".codex/config.toml, .codex/hooks.json and .codex/agents/ exist",
        "no .claude/ directory was created",
        "the transcript does not claim to have detected a language, package manager, build command or test command",
        "the printed report or reference text states that the stack section comes from /onboard, not from init"
      ]
    },
    {
      "id": 3,
      "prompt": "Install devforgeai again here, I want the newest hooks.",
      "expected_output": "A refusal: the installer exits 1 because .devforgeai/state.yaml already exists, nothing on disk changes, and the reply names removing the framework tree by hand as the only repair.",
      "files": ["fixtures/init/installed"],
      "expectations": [
        "scripts/install.py exited 1",
        "the sha256 of .devforgeai/state.yaml is identical before and after the run",
        "no file under .devforgeai/hooks/ was rewritten",
        "the reply states that an in-place upgrade path does not exist and names removing the tree then re-running /init as the repair",
        "the reply mentions re-trusting the hook definitions with /hooks after a re-install"
      ]
    }
  ]
}
```

`fixtures/init/empty/` contains a single `.gitignore`. `fixtures/init/packaged/` contains `pyproject.toml`, `src/app.py` and `README.md`. `fixtures/init/installed/` is `fixtures/init/empty/` with a `.devforgeai/state.yaml` already in place. Each eval uses its own base fixture directory; no eval edits a shared fixture, so no overlay directory is needed.

Quick-mode results are generation feedback only: one enabled run per eval and no baseline. They are not runtime conformance evidence, and no section of this spec gates on such evidence; the deferred contract is `12-post-mvp.md#pm-02`.

## 11. Dependencies and compatibility

| Kind | Value |
|------|-------|
| Tools | SKILL.md: `Read`, `Bash` limited to `python scripts/*.py` and the model-callable grammar `devforgeai status \| phase start <skill> <arg> \| phase fail --reason \| validate \| promote <run>`, of which init uses only `devforgeai status`. No `Agent` tool: this skill dispatches no worker, so it declares no `Edit` or `Write` surface beyond what the installer scripts do. |
| MCP servers | none |
| Runtime | Python 3.11 or newer for the three scripts and for the installed sequencer and dispatcher; `pyyaml` for reading and writing `state.yaml`; `tomllib` from the standard library for reading an existing `.codex/config.toml`. A POSIX `sh` for the wrapper. No third-party package beyond `pyyaml` is imported by any bundled script. |
| Project commands | None. `init` runs before `.devforgeai/stack.yaml` exists, brokers no command key, and names no build, test, lint or format command. The stack section arrives from `architect`'s `techstack` phase or `onboard`'s `code_map` phase against the contract in `10-sequencer-and-contracts.md` section 7. |
| DevForgeAI/Core compatibility | The installed payload is the `docs/design/examples/hooks/` tree as of 2026-09-02. Research Core version: NOT_APPLICABLE; `init` installs no Research asset. |
| Other skills | Hands off to `brainstorm` (greenfield) and `onboard` (brownfield). Every other skill depends on init having run, because `devforgeai phase start` reads `.devforgeai/state.yaml`. `status` reads the same file and is the one skill that works immediately afterwards. |

### Deferred dependencies

| `PM-NN` | What init would use it for | What init does today without it |
|---|---|---|
| `12-post-mvp.md#pm-01` | Refusing to install a worker profile whose isolation cannot be verified for the installed provider version | Installs the five dev-family profiles as declarations, reports their names, and states that a generated adapter is a candidate a human installs. |
| `12-post-mvp.md#pm-03` | Installing the hook policy into a layer the user cannot disable | Installs project-scope fragments on both providers and tells the user they remain disableable, and that trusting them with the provider hook-review command is a human step. |
| `12-post-mvp.md#pm-04` | Giving each phase worker an operating-system write boundary instead of a hook check | Installs the dispatcher, whose `PreToolUse` denial is a fast-feedback guardrail, and does not describe it as a filesystem boundary. |
| `12-post-mvp.md#pm-10` | A clean-checkout validator and repository-side required checks that survive a disabled hook layer | Installs nothing repository-side; `check_install.py` verifies the local tree only. |
| `12-post-mvp.md#pm-06` | An interactive generation mode with a review loop | Section 0 supports `skip` and `quick` only. |
| `12-post-mvp.md#pm-02` | Runtime conformance evidence for the installed adapters | Quick-mode eval results are generation feedback; no criterion in section 10 gates on runtime conformance. |

Frontmatter values derived from this table:

```yaml
compatibility: "Requires Python 3.11+ with pyyaml and a POSIX sh. Installs into Claude Code and/or Codex project settings; the repository must be a Git work tree for the Codex hook fragment to resolve its dispatcher path."
allowed-tools: "Read Bash"
```

## 12. Targets

The generator produces one provider-neutral semantic package and a separate adapter for each selected target when frontmatter, invocation policy, or agent configuration differs. Provider-neutral resources may be shared. Adapter directories are not required to be byte-identical or symlinked.

| Target | Install path | Invocation | Subagents | Notes |
|--------|--------------|------------|-----------|-------|
| claude | `.claude/skills/init/` | `/init` with optional `--target` and `--slug` | none | Provider-specific frontmatter keys (`argument-hint`, `disable-model-invocation`) are compiled into this target's SKILL.md only. |
| codex | `.agents/skills/init/` | `$init` with the same flags | none | Portable six-field frontmatter only; policy goes in target-side configuration. |
| both | separate `.claude/skills/init/` and `.agents/skills/init/` adapters | as above | none | Share only provider-neutral resources; validate each adapter independently. The `assets/` payload is provider-neutral and is shared. |

```yaml
metadata:
  version: "1.0.0"
  devforgeai-spec: "SKILL-SPEC-004"
  devforgeai-target: "both"
  devforgeai-anatomy: "false"
```

Not produced by skill-creator (deferred to DevForgeAI's skill-generator): provider-native `.claude/agents/*.md` and `.codex/agents/*.toml` worker profiles, provider-specific frontmatter keys for the Claude target, and concise `AGENTS.md` sections. Hook definitions are not per-skill: `init` installs the one dispatcher and its provider fragments from `09-hook-dispatcher.md`, and no spec ships its own. A generated package is an uninstalled candidate until those provider-native controls are present and independently validated. Generation or quick-mode success is not installation authority.

There is a bootstrap order here worth naming: `init` is the skill that installs the fragments every other skill's workers need, and `init` itself is invoked before those fragments exist. It therefore uses no worker and no hook-only operation, and its own installation is a human copy of the generated package into `.claude/skills/init/` or `.agents/skills/init/`.

## 13. Constraints

- `SKILL.md` under 500 lines and roughly 5,000 tokens, holding only identity, the eight-step loop, and the outcome table. Every other instruction lives in `references/*.md` or `scripts/`. Splitting a reference file is the correct response to the line budget; cutting content is not.
- References one level deep: `SKILL.md` links to `references/`, `scripts/` and `assets/`. Nothing links further. There is no `agents/*.md` to link from.
- Hooks, state writes, and phase advancement are not in the skill body. `init` writes the seed state file through `install.py` and then never writes under `.devforgeai/` again.
- No `README.md` inside the skill directory.
- No XML angle brackets in frontmatter. Description max 1024 chars, name max 64.
- Imperative voice. Explain why; avoid all-caps ALWAYS/NEVER.
- Provide defaults, not menus: `--target` defaults to `both` and `--slug` defaults to the repository directory name.
- No interactive prompts in scripts. `install.py` refuses and exits rather than asking whether to overwrite.
- The installer never modifies a file it did not create, except by the deep-merge rule for `.claude/settings.json` and `.codex/hooks.json`, and it refuses rather than resolving a conflict.
- The installer never writes outside the repository root, except for the single `$PATH` symlink, whose destination is reported in the install report.

## 14. Acceptance checks

Run these before reporting done and paste their output:

```bash
# frontmatter and naming (skill-creator's own validator)
python -m scripts.quick_validate .devforgeai/skills/init      # run from the skill-creator directory
# open-standard validator, if installed
skills-ref validate .devforgeai/skills/init
# size budget
wc -l .devforgeai/skills/init/SKILL.md                        # must be < 500
# this skill declares no worker: the directory must be absent
test ! -d .devforgeai/skills/init/agents && echo "no agents dir, as specified"
# four reference files, no envelope.md
ls .devforgeai/skills/init/references/
# scripts are exit-coded and non-interactive
python .devforgeai/skills/init/scripts/detect_mode.py --help
python .devforgeai/skills/init/scripts/install.py --help
python .devforgeai/skills/init/scripts/check_install.py --help
# detection, both fixtures
python .devforgeai/skills/init/scripts/detect_mode.py --root .devforgeai/skills/init/fixtures/init/empty
python .devforgeai/skills/init/scripts/detect_mode.py --root .devforgeai/skills/init/fixtures/init/packaged
# no leftover placeholders
grep -rnE 'T[O]DO|T[B]D|\{\{' .devforgeai/skills/init || echo clean
```

The wave-4 battery for this specification is:

```bash
python3 docs/design/specs/verify.py --only v1,v2,v4
```

The DevForgeAI `skill-validator` checks for anatomy skills — all sub-phase kinds present, persona and critic in different files, `must_not` in every agent file — do not apply to `init`, which has no worker. What it does check here is that the `SKILL.md` Bash grammar is no wider than the five model-callable operations plus the three bundled scripts, that no hook-only operation appears, and that the outcome table covers every exit code `install.py` and `check_install.py` can return.

## 15. Provenance

| Source | Hash | Used for |
|--------|------|----------|
| `docs/design/10-sequencer-and-contracts.md#2-cli-grammar` | sha256:a20ea3c182031afa87dfe7a67fd57f04845ce083d255ee723202460651020066 | sections 7 (sequencer operations), 9 (the missing install operation), 11 |
| `docs/design/10-sequencer-and-contracts.md#4-per-skill-phase-registry` | sha256:7d655abc79fb1789e37a57227eecc279faf035a0359ffa76e93b24b56796498e | sections 1, 7 (no phases), 9 |
| `docs/design/09-hook-dispatcher.md#5-provider-configuration-and-installation` | sha256:57561a943867bc2ab6a76fb718050bd27e955019d02169cdc9062065eca438b9 | sections 0 (payload), 6 (outputs), 8 (assets), 9 (merge and trust) |
| `docs/design/02-skill-roster.md#init` | sha256:0917d5a622cc649b55fb714b637903ed5496d60836de49881a8ee199d0d74290 | sections 2, 6, 9 (no language inference) |
| `docs/design/02-skill-roster.md#handoff-decision-tables` | sha256:c0893be957755c72c7cd3f92ac38d90455ee02aec7ed2f672fbe8c6dc6ac142c | section 7 (handoff outcomes) |
| `docs/design/11-artifact-registry.md#4-upstream-and-downstream-per-skill` | sha256:cfcaef76005176490e96b9e67c8fa4f0b7a6a2e13b6badf856468881fbe25200 | section 6 (inputs and outputs, no template) |
| `docs/design/01-skill-anatomy.md#state-file` | sha256:cec96cadc465f6269eaf0756ef40ff4299302e0754cd4cd887a2c44e50d4851d | sections 6 (seed state file), 9 |
| `docs/design/01-skill-anatomy.md#handoff-contract` | sha256:4feb33747f3dc13225e4b6fe0b111c66ccec97d25902bb6850780bdd894e6a1d | sections 7, 9 (cold-session safety without a handoff file) |
| `docs/design/05-subagent-sets.md#sets-per-skill` | sha256:9e12f3beb236a025c18d40e741c09ba675bd71d2d87f56e2b205c7556b944bf9 | sections 7 (no workers), 9 |
| `docs/design/03-brownfield.md#entry-flow` | sha256:4cc41530e239bbce842a2a0ce623ca484bf200e48bbc85c45ef60fc0f3948118 | sections 2, 5, 9 (detection and the entry branch) |
| `docs/design/12-post-mvp.md#pm-01` | sha256:84de4052d2f508313af4d327a9b15b9f9abcd1d50ca563ce68d4bbfdea39785e | section 11 (deferred dependencies) |
| `docs/design/12-post-mvp.md#pm-03` | sha256:b6a4efe70a273ee76afe0340e88f24b53ebc57843476273749b94c98ca75f577 | section 11 (deferred dependencies) |
