---
# == template header: read by the DevForgeAI gate; not copied into instances ==
template: prd
template_version: 1
accepts_versions: [1]
required_frontmatter: [slug, template, template_version, status, scope, provenance, depends_on]
required_sections: ["## Goal", "## Users", "## Requirements", "## Non-Goals", "## Success Measures"]
id_pattern: "^REQ-[0-9]{3}$"
forbidden_text: ["TODO", "TBD", "{{", "}}", "<fill in>"]
# id_pattern applies to the REQ rows inside `## Requirements`: epics and stories cite a requirement
#   anchor, and /analyze walks requirement-to-story (11 section 3).
# provenance vs depends_on: `provenance` is lineage - the brainstorm sections each requirement was
#   sliced from. `depends_on` is what governs and is re-resolved by the consuming gate - the admitted
#   OBSERVED constraints. 11 section 3 lists both sources; the split keeps one anchor in one list.
# scope: derived from 03-brownfield.md - pm runs in MVP mode on greenfield and feature mode on
#   `--scope feature`.
# == instance frontmatter: fill every field ==
slug: "{{slug}}"
template: prd
template_version: 1
status: draft               # draft | ready | superseded
scope: mvp                  # mvp | feature ; recorded so /analyze can flag reduced-provenance work
provenance:
  - source: "docs/brainstorm/{{slug}}.md#ideas"
    hash: sha256:{{64 hex}}
  - source: "docs/brainstorm/{{slug}}.md#clusters"
    hash: sha256:{{64 hex}}
depends_on:
  - source: "docs/architecture/architecture.md#observed"
    hash: sha256:{{64 hex}}
context:
  - source: "docs/architecture/architecture.md#observed"
    status: OBSERVED        # INTENDED | OBSERVED
    hash: sha256:{{64 hex}}
    excerpt: |
      {{verbatim}}
---

# PRD: {{slug}}

## Goal

One sentence: what is true for the user when this slug ships.

## Users

One row per user the requirements serve, with the need that brings them here.

| User | Need |
|---|---|
| {{role}} | {{what they are trying to do}} |

## Requirements

One row per requirement. The ID is the anchor epics and stories cite; the origin column names the IDEA row it came from.

| ID | Requirement | Origin |
|---|---|---|
| REQ-000 | {{observable statement}} | IDEA-000 |

## Non-Goals

What this slug deliberately does not do, one line each, so architect and plan do not design for it.

## Success Measures

How anyone tells afterwards whether the goal was met, each measure countable and tied to a REQ row.
