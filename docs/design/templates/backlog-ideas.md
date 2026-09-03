---
# == template header: read by the DevForgeAI gate; not copied into instances ==
template: backlog-ideas
template_version: 1
accepts_versions: [1]
required_frontmatter: [slug, template, template_version, status]
required_sections: ["## Archived Ideas", "## Promotion Log"]
id_pattern: "^IDEA-[0-9]{3}$"
forbidden_text: ["TODO", "TBD", "{{", "}}", "<fill in>"]
# id_pattern applies to the archived rows: pm's scope-splitter archives by IDEA reference and brainstorm
#   reads them back on the next pass (11 section 5, edges pm->pm and pm->brainstorm).
# provenance: not in 11's required list for this row, so it is optional here and carried as the extra
#   `provenance:` key - the brainstorm sections the archived ideas were split out of. Derived from
#   02-skill-roster.md (pm: non-MVP ideas go to backlog-ideas.md) so brainstorm can re-resolve them.
# == instance frontmatter: fill every field ==
slug: "{{slug}}"
template: backlog-ideas
template_version: 1
status: draft               # draft | ready | superseded
provenance:
  - source: "docs/brainstorm/{{slug}}.md#ideas"
    hash: sha256:{{64 hex}}
---

# Backlog Ideas: {{slug}}

## Archived Ideas

One row per idea the scope split kept out of the current PRD, with the one-line justification pm's scope-splitter produced.

| ID | Idea | Why archived |
|---|---|---|
| IDEA-000 | {{one sentence}} | {{one line}} |

## Promotion Log

One row per archived idea that later entered a PRD, so a reader can tell an idea that was dropped from one that was deferred and used.

| ID | Promoted on | Into |
|---|---|---|
| IDEA-000 | 2026-01-01 | REQ-000 |
