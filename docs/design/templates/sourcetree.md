---
# == template header: read by the DevForgeAI gate; not copied into instances ==
template: sourcetree
template_version: 1
accepts_versions: [1]
required_frontmatter: [slug, template, template_version, status, mode, depends_on]
required_sections: ["## Layout", "## Ownership", "## Naming"]
id_pattern: "^PATH-[0-9]{3}$"
forbidden_text: ["TODO", "TBD", "{{", "}}", "<fill in>"]
# layout_rows: `## Layout` is a table of | ID | Path | Owner | Contents |. Each row carries exactly one
#   path or glob and exactly one owner, so plan's critic can check every story `write_fence` entry
#   against the Path column and name the owner when it does not match (08-story-specification.md,
#   write_fence row).
# id_pattern applies to those rows. Heading text stays plain: `sourcetree.md#observed` is a normative
#   anchor in 11 section 2.
# `## Observed` is not a required section: it is the anchor onboard appends observed-constraints
#   sections to, and it is absent on a greenfield project (11 divergence 6).
# mode: greenfield | brownfield, mirrored from state.yaml so a reader can tell an intended layout from
#   one that also has to describe existing code (01-skill-anatomy.md, state file).
# provenance: carried by `depends_on:` - the constitution sections this was sliced from (11 section 3).
# == instance frontmatter: fill every field ==
slug: "{{slug}}"
template: sourcetree
template_version: 1
status: draft               # draft | ready | superseded
mode: brownfield            # greenfield | brownfield ; mirrored from state.yaml
depends_on:
  - source: "docs/architecture/constitution.md#principles"
    hash: sha256:{{64 hex}}
  - source: "docs/architecture/constitution.md#constraints"
    hash: sha256:{{64 hex}}
context:
  - source: "docs/architecture/constitution.md#principles"
    status: INTENDED        # INTENDED | OBSERVED
    hash: sha256:{{64 hex}}
    excerpt: |
      {{verbatim}}
---

# Source Tree: {{slug}}

## Layout

<!-- status: INTENDED -->

One row per directory or glob a story may write to. Path and Owner are the two columns plan's critic reads; a fence entry with no matching row is a defect the critic names by owner.

| ID | Path | Owner | Contents |
|---|---|---|---|
| PATH-000 | `src/{{package}}/` | {{component or team}} | {{what lives here}} |
| PATH-001 | `tests/{{package}}/` | {{component or team}} | {{what lives here}} |

## Ownership

<!-- status: INTENDED -->

One line per owner named in Layout: what that owner decides, and who reviews a change to it.

## Naming

<!-- status: INTENDED -->

The naming rules a reviewer can apply without judgement: file, module, and test names, and where each derives from.

## Observed

<!-- status: OBSERVED -->

Appended by onboard, one `observed-constraints` section per admitted non-derivable layout constraint. Absent when nothing was admitted.
