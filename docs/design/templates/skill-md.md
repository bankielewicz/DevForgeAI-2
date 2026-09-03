---
# == template header: read by the DevForgeAI gate; not copied into instances ==
template: skill-md
template_version: 1
accepts_versions: [1]
required_frontmatter: [name, description, compatibility, metadata]
required_sections: ["## Identity", "## Phases", "## Dispatch Loop", "## Handoff"]
id_pattern: "^[a-z][a-z0-9-]*$"
forbidden_text: ["TODO", "TBD", "{{", "}}", "<fill in>"]
# id_pattern applies to `name`, which equals the skill directory name.
# The compiled file stays under 500 lines and carries only identity, the phase list, the dispatch loop
#   and the handoff table; every other instruction lives in references/, subagents/, scripts/ or assets/
#   (06-skill-specification.md section 13).
# `description` is a YAML block scalar, max 1024 characters, no angle brackets
#   (06-skill-specification.md section 3).
# Frontmatter keys are a subset of the six the Agent Skills standard permits: name, description,
#   license, compatibility, allowed-tools, metadata. Anything DevForgeAI needs beyond those, including
#   provenance, lives under `metadata:` (Anthropic skills guide, Reference B; 13-skill-validator rule 1).
# `compatibility` (1-500 characters) is required here because every anatomy skill depends on the
#   devforgeai command, provider hooks and subagents: it does not run identically on Claude.ai or the API.
# `allowed-tools` carries the skill's Bash grammar verbatim so the restriction is structural, not prose.
# == instance frontmatter: fill every field ==
name: "{{skill-name}}"
description: >
  {{What it does.}} Use this skill whenever {{trigger contexts}}. It
  {{key capabilities}}. Do not use it for {{near-miss cases}}; use
  {{other skill}} instead.
compatibility: "{{Runs in the Claude Code terminal or the Codex terminal with DevForgeAI installed: the devforgeai command on PATH, its hook fragment in the provider settings, and git at the project root for worktree-mode candidate roots. Not Claude.ai or the API.}}"
allowed-tools: "Read Agent Bash(devforgeai status) Bash(devforgeai phase start *) Bash(devforgeai phase fail *) Bash(devforgeai validate) Bash(devforgeai promote *)"
metadata:
  version: "{{1.0.0}}"
  devforgeai-spec: "{{SKILL-SPEC-000}}"
  devforgeai-target: "{{claude | codex | both}}"
  devforgeai-anatomy: "true"
  provenance:
    - source: "docs/plan/{{slug}}/skill-specs/SKILL-SPEC-000.md#3-description"
      hash: sha256:{{64 hex}}
---

# {{skill-name}}

## Identity

Open with the two rules everything else rests on, before any persona text, so they are the first lines the model reads: this skill never writes a file and never advances a phase; the devforgeai sequencer does both, and a worker returns a receipt, not a result. Then one paragraph: the persona this skill runs as and the single job it owns. The artifact it produces and the artifact it gates on, each named by path.

## Phases

The phase list in run order, one line per phase naming the worker it dispatches. No guidance here; that lives in `references/<phase>.md`.

## Dispatch Loop

Open the run with `devforgeai phase start {{skill-name}} {{arg}}`, dispatch each phase's worker with file paths, a one-line instruction and the `devforgeai status` block, and branch on the returned status. The Bash grammar is `devforgeai status`, `phase start <skill> <arg>`, `phase fail --reason <text>`, `validate` and `promote <run>`; every other operation is hook-only, and `devforgeai run <key>` belongs to the lease-holding producer.

## Handoff

The outcome table, one row per status the skill can return, each with one exact command. Print the block the sequencer rendered rather than composing one.
