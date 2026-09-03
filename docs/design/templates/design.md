---
# == template header: read by the DevForgeAI gate; not copied into instances ==
template: design
template_version: 1
accepts_versions: [1]
required_frontmatter: [slug, topic, template, template_version, status, depends_on]
required_sections: ["## Decision", "## Options", "## Consequences", "## Interfaces"]
id_pattern: "^DES-[0-9]{3}$"
forbidden_text: ["TODO", "TBD", "{{", "}}", "<fill in>"]
# topic: the file is docs/architecture/design-<topic>.md (11 section 2), so the frontmatter carries the
#   topic that names the file and stories cite `design-<topic>.md#interfaces`.
# id_pattern applies to the option and interface rows.
# A design document is deeper than an ADR on one topic and is written by architect's design phase
#   (10 section 4). An ADR records that a decision changed; this records how the chosen one works.
# provenance: carried by `depends_on:` - the constitution sections this was sliced from (11 section 3).
# == instance frontmatter: fill every field ==
slug: "{{slug}}"
topic: "{{topic}}"          # kebab-case; the file is docs/architecture/design-{{topic}}.md
template: design
template_version: 1
status: draft               # draft | ready | superseded
depends_on:
  - source: "docs/architecture/constitution.md#principles"
    hash: sha256:{{64 hex}}
  - source: "docs/architecture/architecture.md#components"
    hash: sha256:{{64 hex}}
context:
  - source: "docs/architecture/architecture.md#components"
    status: INTENDED        # INTENDED | OBSERVED
    hash: sha256:{{64 hex}}
    excerpt: |
      {{verbatim}}
---

# Design: {{topic}}

## Decision

<!-- status: INTENDED -->

One paragraph: what was chosen for this topic, stated so a story can be written against it without reading the options.

## Options

<!-- status: INTENDED -->

One row per option that was actually considered, including the chosen one. An option nobody weighed is not an option.

| ID | Option | Chosen | Why |
|---|---|---|---|
| DES-000 | {{option}} | yes | {{one line}} |

## Consequences

<!-- status: INTENDED -->

What this decision makes easy and what it makes expensive, one line each, including the cost of reversing it.

## Interfaces

<!-- status: INTENDED -->

One row per name this design puts into the codebase that another story depends on: signature, shape, or error behaviour.

| ID | Name | Contract |
|---|---|---|
| DES-000 | {{symbol or endpoint}} | {{signature, shape, error behaviour}} |
