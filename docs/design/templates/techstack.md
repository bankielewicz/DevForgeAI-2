---
# == template header: read by the DevForgeAI gate; not copied into instances ==
template: techstack
template_version: 1
accepts_versions: [1]
required_frontmatter: [slug, template, template_version, status, mode, depends_on, stack_section]
required_sections: ["## Languages", "## Data Access", "## Testing", "## Build And Lint"]
id_pattern: "^TS-[0-9]{3}$"
forbidden_text: ["TODO", "TBD", "{{", "}}", "<fill in>"]
# stack_section: the anchor-and-hash pointer into .devforgeai/stack.yaml that this document is the prose
#   side of. A story pins the same file by hash and names one anchor (10-sequencer-and-contracts.md
#   section 7); this pointer is how /drift and /amend tell that the prose and the executable section
#   still describe the same thing.
# id_pattern applies to the rows inside each section. Heading text stays plain: `techstack.md#data-access`
#   and `techstack.md#testing` are cited in 05-subagent-sets.md and 10 sections 7.1 and 7.2.
# `## Observed` is not a required section: it is the anchor onboard appends observed-constraints
#   sections to (11 divergence 6).
# mode: greenfield | brownfield, mirrored from state.yaml.
# provenance: carried by `depends_on:` - the constitution sections this was sliced from (11 section 3).
# == instance frontmatter: fill every field ==
slug: "{{slug}}"
template: techstack
template_version: 1
status: draft               # draft | ready | superseded
mode: brownfield            # greenfield | brownfield ; mirrored from state.yaml
depends_on:
  - source: "docs/architecture/constitution.md#constraints"
    hash: sha256:{{64 hex}}
stack_section:              # the executable side of this document; installing it is a human step today
  source: ".devforgeai/stack.yaml#{{anchor}}"
  hash: sha256:{{64 hex}}
context:
  - source: "docs/architecture/constitution.md#constraints"
    status: INTENDED        # INTENDED | OBSERVED
    hash: sha256:{{64 hex}}
    excerpt: |
      {{verbatim}}
---

# Tech Stack: {{slug}}

## Languages

<!-- status: INTENDED -->

One row per language or runtime, with the version floor and the paths it governs. A value not present in a manifest is recorded as unknown rather than guessed.

| ID | Language | Version | Paths |
|---|---|---|---|
| TS-000 | {{language}} | {{version floor}} | `src/{{package}}/` |

## Data Access

<!-- status: INTENDED -->

How this project reaches storage, and what it may not use. Each row is quoted verbatim by the stack policy refusal that enforces it, so write it as the sentence you want a developer to read.

| ID | Rule | Reason |
|---|---|---|
| TS-000 | {{one sentence}} | {{why}} |

## Testing

<!-- status: INTENDED -->

The test framework, where tests live, and the layout convention. The runnable form of the same facts is the `stack_section` keys `test_glob`, `test_layout` and `commands.test`; this section says why.

| ID | Rule | Stack key |
|---|---|---|
| TS-000 | {{one sentence}} | `commands.test` |

## Build And Lint

<!-- status: INTENDED -->

Whether the project compiles, and what lint and format mean here. A compiled project has a `build` key in the stack section and the oracle runs it before every test.

| ID | Rule | Stack key |
|---|---|---|
| TS-000 | {{one sentence}} | `commands.lint` |

## Observed

<!-- status: OBSERVED -->

Appended by onboard, one `observed-constraints` section per admitted non-derivable stack constraint. Absent when nothing was admitted.
