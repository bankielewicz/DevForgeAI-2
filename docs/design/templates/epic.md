---
# == template header: read by the DevForgeAI gate; not copied into instances ==
template: epic
template_version: 1
accepts_versions: [1]
required_frontmatter: [id, slug, template, template_version, status, risk_tier, provenance, depends_on]
required_sections: ["## Goal", "## Scope", "## Stories", "## Constitution Sections"]
id_pattern: "^EPIC-[0-9]{3}$"
forbidden_text: ["TODO", "TBD", "{{", "}}", "<fill in>"]
# provenance vs depends_on: `provenance` is lineage - the PRD requirement anchors this epic descends
#   from. `depends_on` is what governs - the constitution sections it was sliced against. 11 section 3
#   lists both for this row; the split keeps one anchor in one list.
# risk_tier: LOW | MEDIUM | HIGH. A story inherits it and may only raise it
#   (templates/story.md, risk_tier).
# `## Stories` rows are the anchors each story's `provenance` cites, so the story anchor is the row's
#   heading text in the epic (templates/story.md, provenance).
# == instance frontmatter: fill every field ==
id: EPIC-000
slug: "{{slug}}"
template: epic
template_version: 1
status: draft               # draft | ready | superseded
risk_tier: LOW              # LOW | MEDIUM | HIGH ; stories inherit and may only raise it
provenance:
  - source: "docs/PM/{{slug}}/prd.md#requirements"
    hash: sha256:{{64 hex}}
depends_on:
  - source: "docs/architecture/constitution.md#principles"
    hash: sha256:{{64 hex}}
context:
  - source: "docs/architecture/constitution.md#principles"
    status: INTENDED        # INTENDED | OBSERVED
    hash: sha256:{{64 hex}}
    excerpt: |
      {{verbatim}}
---

# EPIC-000: {{title}}

## Goal

One sentence: the user-visible change this epic delivers. It names an outcome, not a set of tasks.

## Scope

What this epic covers and what it deliberately leaves to another epic, one line each, so plan does not slice the same requirement twice.

## Stories

One row per story this epic is sliced into. The ID column is the anchor each story's `provenance` cites back to.

| ID | Story | Requirement |
|---|---|---|
| STORY-000 | {{one sentence}} | REQ-000 |

## Constitution Sections

One row per `depends_on` entry: the section, and what it decides for this epic. A story sliced from this epic inherits these anchors in its own context bundle.

| Section | Decides |
|---|---|
| `constitution.md#principles` | {{one line}} |
