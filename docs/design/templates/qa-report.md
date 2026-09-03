---
# == template header: read by the DevForgeAI gate; not copied into instances ==
template: qa-report
template_version: 1
accepts_versions: [1]
required_frontmatter: [story, template, template_version, status, verdict, depends_on]
required_sections: ["## Criteria", "## Evidence", "## Regressions", "## Fix Guidance"]
id_pattern: "^CRIT-[0-9]{3}$"
forbidden_text: ["TODO", "TBD", "{{", "}}", "<fill in>"]
# id_pattern applies to the criterion rows inside `## Criteria`; one row per acceptance criterion of the
#   story, which is also one row of its `test_plan` (08-story-specification.md, test_plan).
# verdict vocabulary derived from 02-skill-roster.md's handoff table for qa, which has exactly two
#   outcomes: pass and fail.
# `## Regressions` is the Unchanged Behaviour surface: smoke-qa covers one story, and the full
#   regression belongs here (05-subagent-sets.md, loop rules).
# Extra instance keys: `run`, `session_id`, `evidence`. `run` is `qa-<story>` (11 section 2). Phase names
#   are qa's registry phases in 10 section 4 - run_tests, criteria, evidence, report.
# Known limit recorded rather than papered over: qa's `run_tests` phase declares the `test` key, but a
#   document run carries `commands: {}`, so the broker refuses the key today (10 section 4, 11
#   divergence 2). A row whose result came from dev's recorded run says so in its Source column.
# provenance: carried by `depends_on:` - the story's acceptance criteria and test_plan, and the
#   review-report (11 section 3).
# == instance frontmatter: fill every field ==
story: STORY-000
template: qa-report
template_version: 1
status: ready               # draft | ready | superseded
verdict: pass               # pass | fail
run: "qa-STORY-000"
session_id: "{{session_id}}"
evidence:
  - ".devforgeai/work/qa-STORY-000/run_tests-result.json"
  - ".devforgeai/work/qa-STORY-000/criteria-result.json"
  - ".devforgeai/work/qa-STORY-000/evidence-result.json"
  - ".devforgeai/work/qa-STORY-000/report-result.json"
depends_on:
  - source: "docs/plan/{{slug}}/stories/STORY-000.md#acceptance-criteria"
    hash: sha256:{{64 hex}}
  - source: "docs/reports/review-STORY-000.md#findings"
    hash: sha256:{{64 hex}}
---

# QA: STORY-000

## Criteria

One row per acceptance criterion, in the story's numbering, with the `test_plan` test that decides it.

| ID | Criterion | Test | Result |
|---|---|---|---|
| CRIT-000 | {{criterion 1, quoted}} | `tests/{{test file}}::{{test name}}` | pass |

## Evidence

One line per criterion row: where its result came from, naming the result file and the classification the sequencer recorded, or the dev run it was read from.

## Regressions

One row per Unchanged Behaviour line in the story, with its result. Empty only when the story's scope is `feature` and it declared none.

| ID | Behaviour | Result |
|---|---|---|
| CRIT-000 | {{one testable line}} | pass |

## Fix Guidance

One line per failing criterion, naming the criterion and what a fix has to change. Empty when the verdict is pass.
