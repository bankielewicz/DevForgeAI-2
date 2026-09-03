---
# == template header: read by the DevForgeAI gate; not copied into instances ==
template: adr
template_version: 1
accepts_versions: [1]
required_frontmatter: [id, template, template_version, status, date, supersedes, depends_on]
required_sections: ["## Context", "## Decision", "## Consequences", "## Alternatives"]
id_pattern: "^ADR-[0-9]{4}$"
forbidden_text: ["TODO", "TBD", "{{", "}}", "<fill in>"]
# Two producers write this template into the same directory: architect mints decisions and amend appends
#   them (11 ownership decisions). The template does not distinguish them; `depends_on` names the
#   constitution section the decision changes, which is the same in both cases.
# supersedes: an ADR id or null. A superseded ADR keeps `status: superseded` and is not deleted, so
#   /analyze and /review can still resolve a citation to it.
# status: proposed | accepted | superseded - the ADR lifecycle, narrower than the document set used by
#   the architecture documents.
# provenance: carried by `depends_on:` (11 section 3).
# == instance frontmatter: fill every field ==
id: ADR-0000
template: adr
template_version: 1
status: proposed            # proposed | accepted | superseded
date: 2026-01-01
supersedes: null            # an ADR id, or null
depends_on:
  - source: "docs/architecture/constitution.md#constraints"
    hash: sha256:{{64 hex}}
provenance:
  - source: "docs/reports/drift-{{slug}}.md#actions"
    hash: sha256:{{64 hex}}
---

# ADR-0000: {{title}}

## Context

What forced a decision: the constraint, the conflict, or the change that made the previous position untenable. Facts only.

## Decision

One paragraph in the present tense: what the project now does. This is the text a review cites.

## Consequences

What follows, one line each, both directions: what this makes possible and what it costs, including which documents or stories now need re-slicing.

## Alternatives

One row per alternative that was weighed and dropped, with the reason it was dropped. An alternative nobody weighed is not recorded here.

| Alternative | Dropped because |
|---|---|
| {{option}} | {{one line}} |
