---
# == template header: read by the DevForgeAI gate; not copied into instances ==
template: retro-report
template_version: 1
accepts_versions: [1]
required_frontmatter: [sprint, template, template_version, status, depends_on]
required_sections: ["## Outcomes", "## Lessons", "## Proposed Amendments", "## Archive"]
id_pattern: "^LESS-[0-9]{3}$"
forbidden_text: ["TODO", "TBD", "{{", "}}", "<fill in>"]
# id_pattern applies to the rows inside `## Lessons`; the amendment rows cite those ids.
# Extra instance keys: `run`, `session_id`, `evidence`. `run` is `retro-<sprint>` (11 section 2). Phase
#   names are retro's registry phases in 10 section 4 - collect, lessons, amendments, archive.
# provenance: carried by `depends_on:` - the sprint, and the qa and review reports for its stories
#   (11 section 3). Dev notes are read through the sprint's stories and are cited in `## Outcomes` rather
#   than re-listed as dependencies, because they carry no `depends_on` of their own.
# `## Proposed Amendments` is a proposal, not an application: a row becomes real only when the user
#   approves it and /amend runs (02-skill-roster.md, retro).
# == instance frontmatter: fill every field ==
sprint: sprint-000
template: retro-report
template_version: 1
status: ready               # draft | ready | superseded
run: "retro-sprint-000"
session_id: "{{session_id}}"
evidence:
  - ".devforgeai/work/retro-sprint-000/collect-result.json"
  - ".devforgeai/work/retro-sprint-000/lessons-result.json"
  - ".devforgeai/work/retro-sprint-000/amendments-result.json"
  - ".devforgeai/work/retro-sprint-000/archive-result.json"
depends_on:
  - source: "docs/plan/{{slug}}/sprints/sprint-000.md#stories"
    hash: sha256:{{64 hex}}
  - source: "docs/reports/qa-STORY-000.md#criteria"
    hash: sha256:{{64 hex}}
  - source: "docs/reports/review-STORY-000.md#findings"
    hash: sha256:{{64 hex}}
---

# Retro: sprint-000

## Outcomes

One row per story in the sprint, with its final state and the report the state came from. Facts only; the reading of them belongs in Lessons.

| Story | Final state | Attempts | Report |
|---|---|---|---|
| STORY-000 | done | 1 | `docs/reports/qa-STORY-000.md` |

## Lessons

One row per lesson, each tied to at least one Outcomes row. A lesson with no story behind it is an opinion and does not belong here.

| ID | Lesson | From |
|---|---|---|
| LESS-000 | {{one sentence}} | STORY-000 |

## Proposed Amendments

One row per lesson that implies a document change, with the exact `/amend` command the user runs if they approve it. Nothing here is applied by retro.

| ID | Document | Change | Command |
|---|---|---|---|
| LESS-000 | `constitution.md#style` | {{one line}} | `/amend constitution "{{change}}"` |

## Archive

Where the sprint's files were moved and what remains live, so a later reader can still resolve a citation into this sprint.
