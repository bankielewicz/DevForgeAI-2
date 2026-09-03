---
# == template header: read by the DevForgeAI gate; not copied into instances ==
template: review-report
template_version: 1
accepts_versions: [1]
required_frontmatter: [story, template, template_version, status, verdict, depends_on]
required_sections: ["## Compliance", "## Security", "## Style", "## Findings"]
id_pattern: "^FIND-[0-9]{3}$"
forbidden_text: ["TODO", "TBD", "{{", "}}", "<fill in>"]
# id_pattern applies to the rows inside `## Findings`; the three checking sections cite those ids.
# verdict vocabulary derived from 02-skill-roster.md's handoff table for review, which has exactly two
#   outcomes: pass and findings.
# The three checking sections are review's registry phases in 10 section 4 - `compliance`, `security`,
#   `style` - and `## Findings` is what the `report` phase writes.
# Extra instance keys: `run`, `session_id`, `evidence`. `run` is `review-<story>` because the run id for
#   a document run is `<skill>-<arg>` (11 section 2); the story id alone names dev's run, not this one.
# provenance: carried by `depends_on:` - the story and the constitution slice the story carried
#   (11 section 3).
# == instance frontmatter: fill every field ==
story: STORY-000
template: review-report
template_version: 1
status: ready               # draft | ready | superseded
verdict: pass               # pass | findings
run: "review-STORY-000"
session_id: "{{session_id}}"
evidence:
  - ".devforgeai/work/review-STORY-000/compliance-result.json"
  - ".devforgeai/work/review-STORY-000/security-result.json"
  - ".devforgeai/work/review-STORY-000/style-result.json"
  - ".devforgeai/work/review-STORY-000/report-result.json"
depends_on:
  - source: "docs/plan/{{slug}}/stories/STORY-000.md#acceptance-criteria"
    hash: sha256:{{64 hex}}
  - source: "docs/architecture/constitution.md#style"
    hash: sha256:{{64 hex}}
---

# Review: STORY-000

## Compliance

One line per constitution section the diff was checked against, naming the finding ids it produced. A section with nothing to say is listed as clear.

## Security

One line per security check applied to the diff, with the finding ids it produced. Checks that do not apply to this diff are named and skipped rather than omitted.

## Style

One line per style convention checked, with the finding ids it produced. A convention a linter already enforces is named by its rule, not re-argued.

## Findings

One row per finding. Severity decides whether the verdict is `findings`; the owner column names who fixes it.

| ID | Severity | File | Finding | Owner |
|---|---|---|---|---|
| FIND-000 | {{blocking or advisory}} | `src/{{module}}/{{file}}` | {{one line}} | dev |
