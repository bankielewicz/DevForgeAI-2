---
# == template header: read by the DevForgeAI gate; not copied into instances ==
template: command-md
template_version: 1
accepts_versions: [1]
required_frontmatter: [name, description, argument-hint]
required_sections: ["## Usage", "## Arguments", "## Handoff"]
id_pattern: "^[a-z][a-z-]*$"
forbidden_text: ["TODO", "TBD", "{{", "}}", "<fill in>"]
# id_pattern applies to `name`, the command stem. It has no digits, and it is the command string rather
#   than the skill name: 11 divergence 4 records that `/skill-gen` invokes `skill-generator`, so a
#   cross-reference check maps through the registry `command` field.
# This is the provider entry adapter and does four things only: parse arguments, call
#   `devforgeai phase start`, load the skill, print the rendered handoff (01-skill-anatomy.md).
# provenance: the skill-spec sections this was generated from (11 section 3).
# == instance frontmatter: fill every field ==
name: "{{command-stem}}"
description: "{{one sentence shown in the command list}}"
argument-hint: "{{arg}} [--flag]"
provenance:
  - source: "docs/plan/{{slug}}/skill-specs/SKILL-SPEC-000.md#12-targets"
    hash: sha256:{{64 hex}}
---

# /{{command-stem}}

## Usage

The invocation exactly as a user types it, and the one sentence saying when to reach for it rather than a neighbouring command.

## Arguments

One row per argument and flag: what it selects, whether it is required, and what happens when it is absent.

| Argument | Required | Effect |
|---|---|---|
| `{{arg}}` | yes | {{one line}} |

## Handoff

Call `devforgeai phase start {{skill-name}} {{arg}}`, load the skill, and print the block the sequencer rendered. The adapter decides nothing and writes nothing.
