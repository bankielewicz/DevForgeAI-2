---
# == template header: read by the DevForgeAI gate; not copied into instances ==
template: sprint
template_version: 1
accepts_versions: [1]
required_frontmatter: [id, slug, template, template_version, status, stories]
required_sections: ["## Goal", "## Stories", "## Order", "## Exit Criteria"]
id_pattern: "^sprint-[0-9]{3}$"
forbidden_text: ["TODO", "TBD", "{{", "}}", "<fill in>"]
# `stories` is a list of story ids, not a list of anchors: the story file is the authority for its own
#   ordering (`blocked_by`) and the sprint records membership only. retro reads this list to collect the
#   dev, review and qa reports for the sprint (11 section 3).
# provenance: not in 11's required list for this row, so it is carried as the extra `provenance:` key -
#   the epics the member stories descend from. Derived from retro's need to name what the sprint was
#   meant to deliver (02-skill-roster.md, retro).
# `## Order` restates the dependency-mapper result as a readable sequence; `blocked_by` in each story
#   stays authoritative, so a disagreement is a plan defect rather than two competing orders.
# == instance frontmatter: fill every field ==
id: sprint-000
slug: "{{slug}}"
template: sprint
template_version: 1
status: draft               # draft | ready | superseded
stories:
  - STORY-000
  - STORY-001
provenance:
  - source: "docs/plan/{{slug}}/epics/EPIC-000.md#stories"
    hash: sha256:{{64 hex}}
---

# sprint-000: {{title}}

## Goal

One sentence: what a user can do at the end of this sprint that they could not at the start.

## Stories

One row per id in `stories:`, with its size and the epic it came from, so retro can read outcomes without opening each story.

| ID | Story | Size | Epic |
|---|---|---|---|
| STORY-000 | {{one sentence}} | S | EPIC-000 |

## Order

The sequence the dependency-mapper produced, one line per story, naming the story it waits on. Each story's `blocked_by` remains authoritative.

## Exit Criteria

What must be true to close this sprint, each line checkable from a qa or review report rather than from an opinion.
