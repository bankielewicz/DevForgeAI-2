---
# == template header: read by the DevForgeAI gate; not copied into instances ==
template: brainstorm
template_version: 1
accepts_versions: [1]
required_frontmatter: [slug, template, template_version, status, provenance]
required_sections: ["## Problem", "## Ideas", "## Clusters", "## Open Questions"]
id_pattern: "^IDEA-[0-9]{3}$"
forbidden_text: ["TODO", "TBD", "{{", "}}", "<fill in>"]
# id_pattern applies to the IDEA rows inside `## Ideas`, not to a document id: pm archives and promotes
#   ideas by reference (02-skill-roster.md, brainstorm section), so the id lives on the row.
# provenance: lineage this brainstorm was built from - admitted OBSERVED constraints, the archived ideas
#   pm returned, and any sealed Research dossier the human ran (02-skill-roster.md, 11 section 4).
# context: excerpts, because idea-clusterer and brainstorm-writer never open the source documents
#   (01-skill-anatomy.md, context bundle).
# status: the closed document set used across these templates: draft | ready | superseded.
# == instance frontmatter: fill every field ==
slug: "{{slug}}"
template: brainstorm
template_version: 1
status: draft               # draft | ready | superseded
provenance:                 # re-resolved by pm's gate
  - source: "docs/PM/{{slug}}/backlog-ideas.md#archived-ideas"
    hash: sha256:{{64 hex}}
  - source: "docs/architecture/architecture.md#observed"
    hash: sha256:{{64 hex}}
  - source: "docs/research/{{slug}}/runs/RUN-000000/"
    ids: "SRC-000000; EVD-000000; CLM-000000"
    manifest: sha256:{{64 hex}}
context:                    # excerpt + anchor + hash; never summarised
  - source: "docs/architecture/architecture.md#observed"
    status: OBSERVED        # INTENDED | OBSERVED ; OBSERVED is advisory, INTENDED binds
    hash: sha256:{{64 hex}}
    excerpt: |
      {{verbatim}}
---

# Brainstorm: {{slug}}

## Problem

The problem this slug exists to solve, in the user's terms. One paragraph.

## Ideas

One row per idea. The ID is how pm promotes it into a requirement or archives it.

| ID | Idea | Origin |
|---|---|---|
| IDEA-000 | {{one sentence}} | {{conversation, or a `provenance:` source}} |

## Clusters

Named groups of IDEA rows that solve the same part of the problem, one line per cluster naming its ids.

## Open Questions

Questions that change which ideas survive, each addressed to a named owner. Write `ASSUMPTION: {{text}}` inline where a value was assumed to keep going.
