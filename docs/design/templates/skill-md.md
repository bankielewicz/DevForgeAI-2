---
# == template header: read by the DevForgeAI gate; not copied into instances ==
template: skill-md
template_version: 1
accepts_versions: [1]
required_frontmatter: [name, description]
required_sections: ["## Identity", "## Phases", "## Dispatch Loop", "## Handoff"]
id_pattern: "^[a-z][a-z0-9-]*$"
forbidden_text: ["TODO", "TBD", "{{", "}}", "<fill in>"]
# id_pattern applies to `name`, which equals the skill directory name.
# The compiled file stays under 500 lines and carries only identity, the phase list, the dispatch loop
#   and the handoff table; every other instruction lives in references/, subagents/, scripts/ or assets/
#   (06-skill-specification.md section 13).
# `description` is a YAML block scalar, max 1024 characters, no angle brackets
#   (06-skill-specification.md section 3).
# provenance: the skill-spec sections this was generated from (11 section 3). Not in 11's required list,
#   so it is carried as the extra `provenance:` key.
# == instance frontmatter: fill every field ==
name: "{{skill-name}}"
description: >
  {{What it does.}} Use this skill whenever {{trigger contexts}}. It
  {{key capabilities}}. Do not use it for {{near-miss cases}}; use
  {{other skill}} instead.
provenance:
  - source: "docs/plan/{{slug}}/skill-specs/SKILL-SPEC-000.md#3-description"
    hash: sha256:{{64 hex}}
---

# {{skill-name}}

## Identity

One paragraph: the persona this skill runs as and the single job it owns. The artifact it produces and the artifact it gates on, each named by path.

## Phases

The phase list in run order, one line per phase naming the worker it dispatches. No guidance here; that lives in `references/<phase>.md`.

## Dispatch Loop

Open the run with `devforgeai phase start {{skill-name}} {{arg}}`, dispatch each phase's worker with file paths, a one-line instruction and the `devforgeai status` block, and branch on the returned status. The Bash grammar is `devforgeai status`, `phase start <skill> <arg>`, `phase fail --reason <text>`, `validate` and `promote <run>`; every other operation is hook-only, and `devforgeai run <key>` belongs to the lease-holding producer.

## Handoff

The outcome table, one row per status the skill can return, each with one exact command. Print the block the sequencer rendered rather than composing one.
