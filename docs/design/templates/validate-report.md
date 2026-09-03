---
# == template header: read by the DevForgeAI gate; not copied into instances ==
template: validate-report
template_version: 1
accepts_versions: [1]
required_frontmatter: [skill, template, template_version, status, verdict, depends_on]
required_sections: ["## Anatomy", "## Provider", "## Spec Conformance", "## Fixes"]
id_pattern: "^VAL-[0-9]{3}$"
forbidden_text: ["TODO", "TBD", "{{", "}}", "<fill in>"]
# id_pattern applies to the check rows inside the three finding sections.
# verdict vocabulary derived from 02-skill-roster.md's handoff table for skill-validator, which has
#   exactly two outcomes: pass and fail.
# The three finding sections are the three checking phases in 10 section 4 - `anatomy`, `provider`,
#   `spec_conformance` - and `## Fixes` is what the `report` phase writes.
# This template is terminal by design: it has no consumer (11 rule 2), so its sections are addressed to
#   a human and to the `/skill-gen {spec} --fix` run that follows.
# Extra instance keys: `run`, `session_id`, `evidence`. `run` is `validate-<skill>` (11 section 2).
# provenance: carried by `depends_on:` - the compiled skill files, the constitution, and the originating
#   skill-spec (11 section 3).
# == instance frontmatter: fill every field ==
skill: "{{skill-name}}"
template: validate-report
template_version: 1
status: ready               # draft | ready | superseded
verdict: pass               # pass | fail
run: "validate-{{skill-name}}"
session_id: "{{session_id}}"
evidence:
  - ".devforgeai/work/validate-{{skill-name}}/anatomy-result.json"
  - ".devforgeai/work/validate-{{skill-name}}/provider-result.json"
  - ".devforgeai/work/validate-{{skill-name}}/spec_conformance-result.json"
  - ".devforgeai/work/validate-{{skill-name}}/report-result.json"
depends_on:
  - source: ".devforgeai/skills/{{skill-name}}/SKILL.md"
    hash: sha256:{{64 hex}}
  - source: "docs/architecture/constitution.md#mandates"
    hash: sha256:{{64 hex}}
  - source: "docs/plan/{{slug}}/skill-specs/SKILL-SPEC-000.md#14-acceptance-checks"
    hash: sha256:{{64 hex}}
---

# Validate: {{skill-name}}

## Anatomy

One row per anatomy check: sub-phase kinds present, persona and critic in different files, `must_not` and `writes` in every worker, `tools` matching the role each `writes` declares, Bash grammar no wider than the model-callable operations.

| ID | Check | Result | Detail |
|---|---|---|---|
| VAL-000 | {{check}} | pass | {{one line}} |

## Provider

One row per target adapter check: frontmatter keys legal for that provider, invocation string correct, worker profiles present.

| ID | Target | Check | Result |
|---|---|---|---|
| VAL-000 | claude | {{check}} | pass |

## Spec Conformance

One row per section of the originating spec that the compiled skill was checked against, with what differed.

| ID | Spec section | Result | Detail |
|---|---|---|---|
| VAL-000 | `#7-procedure` | pass | {{one line}} |

## Fixes

One line per failing row, in the order to apply them, each an exact command. Empty when the verdict is pass.
