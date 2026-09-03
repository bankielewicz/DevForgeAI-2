---
# == template header: read by the DevForgeAI gate; not copied into instances ==
template: constitution
template_version: 1
accepts_versions: [1]
required_frontmatter: [slug, template, template_version, status, provenance, depends_on]
required_sections: ["## Principles", "## Mandates", "## Constraints", "## Style"]
id_pattern: "^SEC-[0-9]{3}$"
forbidden_text: ["TODO", "TBD", "{{", "}}", "<fill in>"]
# id_pattern applies to the rows inside each section, not to a heading. Heading text is the anchor:
#   `constitution.md#mandates` is cited by 02-skill-roster.md and 11 section 3, so a heading may not
#   carry an id or the GitHub slug changes and every citation breaks.
# section status: each section carries `<!-- status: INTENDED -->` per 03-brownfield.md. Architect writes
#   INTENDED here; OBSERVED constraints live in the three architecture files onboard is fenced to.
# mandates: rows are `key: value` in a fixed column because the sequencer selects the dev variant from
#   `tdd: required` and plan mints one skill-spec per mandate (02-skill-roster.md, architect and plan).
# provenance vs depends_on: `provenance` is lineage - the PRD sections this was sliced from.
#   `depends_on` is what the consuming gate re-resolves - the admitted OBSERVED constraints and the
#   current source citations behind them (11 section 3).
# == instance frontmatter: fill every field ==
slug: "{{slug}}"
template: constitution
template_version: 1
status: draft               # draft | ready | superseded
provenance:
  - source: "docs/PM/{{slug}}/prd.md#requirements"
    hash: sha256:{{64 hex}}
  - source: "docs/PM/{{slug}}/prd.md#non-goals"
    hash: sha256:{{64 hex}}
depends_on:
  - source: "docs/architecture/architecture.md#observed"
    hash: sha256:{{64 hex}}
  - source: "src/{{module}}/{{file}}#L1-L20"
    hash: sha256:{{64 hex}}
context:
  - source: "docs/PM/{{slug}}/prd.md#requirements"
    status: INTENDED        # INTENDED | OBSERVED
    hash: sha256:{{64 hex}}
    excerpt: |
      {{verbatim}}
---

# Constitution: {{slug}}

## Principles

<!-- status: INTENDED -->

One row per principle: the standing decision a reviewer cites when rejecting work. Each row states the principle, not its history.

| ID | Principle | Applies to |
|---|---|---|
| SEC-000 | {{one sentence}} | {{skill, or a path glob}} |

## Mandates

<!-- status: INTENDED -->

One row per mandate. The `key: value` cell is read without a model: the sequencer selects a dev variant from it, and plan writes one skill spec per mandate the project lacks a skill for.

| ID | Mandate | Applies to |
|---|---|---|
| SEC-000 | `tdd: required` | dev |

## Constraints

<!-- status: INTENDED -->

One row per binding limit that is not a preference: a licence, a platform floor, a data rule, a budget. Each names what breaks if it is violated.

| ID | Constraint | Consequence if violated |
|---|---|---|
| SEC-000 | {{one sentence}} | {{what breaks}} |

## Style

<!-- status: INTENDED -->

One row per convention review enforces on a diff. Anything a linter already decides belongs in techstack, not here.

| ID | Convention | Enforced by |
|---|---|---|
| SEC-000 | {{one sentence}} | {{review check, or a lint rule name}} |
