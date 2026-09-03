---
# == template header: read by the DevForgeAI gate; not copied into instances ==
template: analyze-report
template_version: 1
accepts_versions: [1]
required_frontmatter: [slug, template, template_version, status, depends_on]
required_sections: ["## Orphans", "## Gaps", "## Stale Hashes", "## Actions"]
id_pattern: "^FIND-[0-9]{3}$"
forbidden_text: ["TODO", "TBD", "{{", "}}", "<fill in>"]
# id_pattern applies to the finding rows inside the three finding sections, not to a document id.
# Rendered view: the sequencer writes this file at a passing transition of analyze's `report` phase;
#   the evidence it renders lives under .devforgeai/work/<run>/ (10 section 10). `run` is `analyze-<slug>`
#   because the run id for a document run is `<skill>-<arg>` (11 section 2).
# Extra instance keys beyond 11's list: `run`, `session_id` and `evidence` bind the report to the run
#   that produced it, so a reader can reach the accepted envelopes without searching.
# provenance: carried by `depends_on:` - every prd, epic, story and constitution anchor the walk resolved
#   (11 section 3).
# == instance frontmatter: fill every field ==
slug: "{{slug}}"
template: analyze-report
template_version: 1
status: ready               # draft | ready | superseded
run: "analyze-{{slug}}"
session_id: "{{session_id}}"
evidence:
  - ".devforgeai/work/analyze-{{slug}}/cross_reference-result.json"
  - ".devforgeai/work/analyze-{{slug}}/orphans-result.json"
  - ".devforgeai/work/analyze-{{slug}}/stale_hashes-result.json"
  - ".devforgeai/work/analyze-{{slug}}/report-result.json"
depends_on:
  - source: "docs/PM/{{slug}}/prd.md#requirements"
    hash: sha256:{{64 hex}}
  - source: "docs/plan/{{slug}}/epics/EPIC-000.md#stories"
    hash: sha256:{{64 hex}}
  - source: "docs/architecture/constitution.md#principles"
    hash: sha256:{{64 hex}}
---

# Analyze: {{slug}}

## Orphans

One row per story with no requirement behind it. The owner column names the skill that repairs it.

| ID | Story | Missing upstream | Owner |
|---|---|---|---|
| FIND-000 | STORY-000 | {{requirement it should cite}} | plan |

## Gaps

One row per requirement with no story. A gap is a planning defect, not a story defect.

| ID | Requirement | Owner |
|---|---|---|
| FIND-000 | REQ-000 | plan |

## Stale Hashes

One row per `context` or `depends_on` entry whose hash no longer matches its source, with the anchor that moved.

| ID | Artifact | Anchor | Owner |
|---|---|---|---|
| FIND-000 | STORY-000 | `constitution.md#principles` | amend |

## Actions

One line per finding, in the order they should be run, each an exact command. Findings with no action are not listed here.
