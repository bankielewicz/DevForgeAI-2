---
# == template header: read by the DevForgeAI gate; not copied into instances ==
template: impact-report
template_version: 1
accepts_versions: [1]
required_frontmatter: [doc, template, template_version, status, depends_on]
required_sections: ["## Change", "## Affected Stories", "## Re-slice Actions"]
id_pattern: "^IMP-[0-9]{3}$"
forbidden_text: ["TODO", "TBD", "{{", "}}", "<fill in>"]
# id_pattern applies to the rows inside `## Affected Stories`.
# `doc` is amend's argument: the constitution document that changed, which also names the file
#   (docs/reports/impact-<doc>.md, 11 section 2).
# Extra instance keys: `run`, `session_id`, `evidence`. `run` is `amend-<doc>` (11 section 2). Phase names
#   are amend's registry phases in 10 section 4 - apply_change, adr, impact, resync.
# provenance: carried by `depends_on:` - the amended constitution section, and every story whose
#   `context` hashed it (11 section 3). The ADR amend wrote is listed there too, because it is the record
#   of why the section changed.
# == instance frontmatter: fill every field ==
doc: constitution
template: impact-report
template_version: 1
status: ready               # draft | ready | superseded
run: "amend-constitution"
session_id: "{{session_id}}"
evidence:
  - ".devforgeai/work/amend-constitution/apply_change-result.json"
  - ".devforgeai/work/amend-constitution/adr-result.json"
  - ".devforgeai/work/amend-constitution/impact-result.json"
  - ".devforgeai/work/amend-constitution/resync-result.json"
depends_on:
  - source: "docs/architecture/constitution.md#constraints"
    hash: sha256:{{64 hex}}
  - source: ".devforgeai/provenance/adr/0000-{{slug}}.md#decision"
    hash: sha256:{{64 hex}}
---

# Impact: constitution

## Change

What changed in the named section, before and after, in one line each, with the ADR that records why.

## Affected Stories

One row per story whose context bundle hashed the changed section. `Status at change` decides which re-slice action applies.

| ID | Story | Anchor | Status at change |
|---|---|---|---|
| IMP-000 | STORY-000 | `constitution.md#constraints` | ready |

## Re-slice Actions

One line per affected story, in the order to run them, each an exact command. A story already in dev is marked for re-review rather than silently re-sliced.
