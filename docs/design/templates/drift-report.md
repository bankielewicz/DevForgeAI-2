---
# == template header: read by the DevForgeAI gate; not copied into instances ==
template: drift-report
template_version: 1
accepts_versions: [1]
required_frontmatter: [slug, template, template_version, status, depends_on]
required_sections: ["## Sourcetree Drift", "## Techstack Drift", "## Architecture Drift", "## Actions"]
id_pattern: "^DRIFT-[0-9]{3}$"
forbidden_text: ["TODO", "TBD", "{{", "}}", "<fill in>"]
# id_pattern applies to the rows inside the three drift sections; `## Actions` cites those ids.
# The three drift sections are the three INTENDED documents drift compares against the observed tree
#   (02-skill-roster.md, drift; 11 section 3).
# Two kinds of row, both required by 03-brownfield.md: an INTENDED section the tree has not reached, and
#   an OBSERVED citation the tree has invalidated. The Kind column keeps them apart so /amend and
#   /architect --update are not handed the same row twice.
# Extra instance keys: `run`, `session_id`, `evidence`. `run` is `drift-<slug>` (11 section 2). Phase
#   names are drift's registry phases in 10 section 4 - code_map, doc_diff, report.
# code-mapper is onboard's worker file, reused here; drift does not own it (11 divergence 3).
# provenance: carried by `depends_on:` - the sourcetree, techstack and architecture sections compared,
#   and the source paths the observed side was read from (11 section 3).
# == instance frontmatter: fill every field ==
slug: "{{slug}}"
template: drift-report
template_version: 1
status: ready               # draft | ready | superseded
run: "drift-{{slug}}"
session_id: "{{session_id}}"
evidence:
  - ".devforgeai/work/drift-{{slug}}/code_map-result.json"
  - ".devforgeai/work/drift-{{slug}}/doc_diff-result.json"
  - ".devforgeai/work/drift-{{slug}}/report-result.json"
depends_on:
  - source: "docs/architecture/sourcetree.md#layout"
    hash: sha256:{{64 hex}}
  - source: "docs/architecture/techstack.md#languages"
    hash: sha256:{{64 hex}}
  - source: "docs/architecture/architecture.md#components"
    hash: sha256:{{64 hex}}
  - source: "src/{{module}}/{{file}}#L1-L20"
    hash: sha256:{{64 hex}}
---

# Drift: {{slug}}

## Sourcetree Drift

One row per layout row that no longer matches the tree. Kind separates a target not yet reached from evidence the tree has invalidated.

| ID | Kind | Section | Observed | Owner |
|---|---|---|---|---|
| DRIFT-000 | {{not-reached or invalidated}} | `sourcetree.md#layout` | {{what the tree shows}} | architect |

## Techstack Drift

One row per language, data-access, testing or build rule that no longer matches the manifests and configuration. A value absent from a manifest is reported as unknown, not as drift.

| ID | Kind | Section | Observed | Owner |
|---|---|---|---|---|
| DRIFT-000 | {{not-reached or invalidated}} | `techstack.md#testing` | {{what the manifest shows}} | architect |

## Architecture Drift

One row per component, interface or data-flow statement the tree contradicts, with the path that contradicts it.

| ID | Kind | Section | Observed | Owner |
|---|---|---|---|---|
| DRIFT-000 | {{not-reached or invalidated}} | `architecture.md#components` | `src/{{module}}/{{file}}` | architect |

## Actions

One line per row, in the order to run them, each an exact command. A row whose resolution is to accept the tree and change the document goes to `/amend`; one whose resolution is to change the tree goes to `/architect --update` and then to plan.
