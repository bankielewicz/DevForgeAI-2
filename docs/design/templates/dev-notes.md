---
# == template header: read by the DevForgeAI gate; not copied into instances ==
template: dev-notes
template_version: 1
accepts_versions: [1]
required_frontmatter: [story, phase, template, template_version, status, run]
required_sections: ["## Note", "## Issues", "## Files", "## Oracle"]
id_pattern: "^NOTE-[0-9]{3}$"
forbidden_text: ["TODO", "TBD", "{{", "}}", "<fill in>"]
# id_pattern applies to the rows inside `## Issues`.
# No `depends_on` and no `provenance`: dev-notes is evidence of one run, and .devforgeai/work/<run>/run.yaml
#   already pins what it was allowed to touch (11 section 3). The bindings below take their place.
# `run` is the story id, because the run id for a story run is the story id (11 section 2). `phase` is
#   one of dev's registry phases - red, green, refactor, smoke, review (10 section 4).
# dev has no document fence, so this exists as evidence under .devforgeai/work/<run>/ and as the
#   rendered view docs/reports/dev-<story>-<phase>.md (11 section 2).
# `## Oracle` records the transition verdict the sequencer computed; the worker does not run commands
#   and does not decide the verdict (10 section 11).
# == instance frontmatter: fill every field ==
story: STORY-000
phase: green                # red | green | refactor | smoke | review
template: dev-notes
template_version: 1
status: ready               # draft | ready | superseded
run: STORY-000
session_id: "{{session_id}}"
evidence:
  - ".devforgeai/work/STORY-000/green-result.json"
  - ".devforgeai/work/STORY-000/green-report.md"
---

# Dev Notes: STORY-000 green

## Note

At most three lines: what this phase did, in the words the receipt's `note` carried. No restatement of the story.

## Issues

One row per issue the phase raised, at most ten, each one line. An issue names what a later phase has to deal with.

| ID | Kind | Text |
|---|---|---|
| NOTE-000 | {{critic, blocked, or assumption}} | {{one line}} |

## Files

One line per path the checkpoint diff recorded as changed, with its resulting hash. Every path is inside the story's `write_fence`.

## Oracle

The transition check the sequencer ran for this phase: which command keys it brokered, each classification, and the one condition that decided the verdict.
