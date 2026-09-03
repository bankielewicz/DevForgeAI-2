---
# == template header: read by the DevForgeAI gate; not copied into instances ==
template: architecture
template_version: 1
accepts_versions: [1]
required_frontmatter: [slug, template, template_version, status, depends_on]
required_sections: ["## Components", "## Interfaces", "## Data Flow", "## Failure Modes"]
id_pattern: "^COMP-[0-9]{3}$"
forbidden_text: ["TODO", "TBD", "{{", "}}", "<fill in>"]
# id_pattern applies to the component rows. Heading text stays plain: `architecture.md#observed` is a
#   normative anchor in 11 section 2, and story context bundles cite section anchors of this file
#   (03-brownfield.md, context slicing).
# `## Observed` is not a required section: it is the anchor onboard appends observed-constraints
#   sections to (11 divergence 6).
# provenance: carried by `depends_on:` - the constitution sections this was sliced from (11 section 3).
# == instance frontmatter: fill every field ==
slug: "{{slug}}"
template: architecture
template_version: 1
status: draft               # draft | ready | superseded
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

# Architecture: {{slug}}

## Components

<!-- status: INTENDED -->

One row per component. The ID is what interfaces, data flow and stories cite; the path column ties it to a sourcetree row.

| ID | Component | Path | Responsibility |
|---|---|---|---|
| COMP-000 | {{name}} | `src/{{package}}/` | {{one sentence, one job}} |

## Interfaces

<!-- status: INTENDED -->

One row per boundary between two components: what crosses it, in which direction, and what the caller may assume.

| ID | From | To | Contract |
|---|---|---|---|
| COMP-000 | {{component}} | {{component}} | {{signature, shape, or protocol}} |

## Data Flow

<!-- status: INTENDED -->

The path a unit of work takes through the components, named in order, with what each step may change.

## Failure Modes

<!-- status: INTENDED -->

One row per way this shape fails in production, with the component that owns detecting it. A mode with no owner is a gap, not a note.

| ID | Failure | Owner | Detected by |
|---|---|---|---|
| COMP-000 | {{what goes wrong}} | {{component}} | {{signal}} |

## Observed

<!-- status: OBSERVED -->

Appended by onboard, one `observed-constraints` section per admitted non-derivable architectural constraint. Absent when nothing was admitted.
