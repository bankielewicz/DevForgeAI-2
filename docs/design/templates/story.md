---
# == template header: read by the DevForgeAI gate; not copied into instances ==
template: story
template_version: 3
accepts_versions: [3]      # v3 only; the gate rejects any other version as a template defect
required_frontmatter: [id, epic, sprint, scope, status, template, template_version, requires_skill, risk_tier, size, gate_policy, blocked_by, provenance, context, write_fence, commands, test_plan]
required_sections: ["## Goal", "## Context", "## Interface", "## Acceptance Criteria", "## Unchanged Behaviour", "## Out of Scope", "## Verification", "## Clarifications"]
id_pattern: "^STORY-(HOTFIX-)?[0-9]{3}$"
forbidden_text: ["TODO", "TBD", "{{", "}}", "<fill in>"]
# Immutability: every field and section is write-once when status becomes `ready`,
# except `status` (mirrored from state.yaml by the sequencer at `phase next`) and
# `## Clarifications` (append-only, by /clarify). Dev evidence never goes here;
# it goes to .devforgeai/work/<run>/.
# == instance frontmatter: fill every field ==
id: STORY-000
epic: EPIC-000
sprint: sprint-000          # null for scope: hotfix
scope: feature              # feature | change | hotfix ; copied from the plan invocation
status: ready               # ready | in_dev | dev_done | dev_blocked | review_failed | qa_failed | done
template: story
template_version: 3
requires_skill: dev         # skill that implements this story; must exist for the active target
risk_tier: LOW              # LOW | MEDIUM | HIGH ; from the epic, may only be raised here
size: S                     # XS | S | M | L ; set by estimator; L must be split
gate_policy:                # defect-to-action map: BLOCK | REQUIRE_HUMAN | WARN | OFF.
                            # Read by the gate; never a status a worker returns.
  unresolved_assumption: BLOCK
  stale_hash: BLOCK
  unresolvable_source: BLOCK        # WARN is legal only when scope is hotfix
  write_fence_violation: BLOCK
  test_runner_missing: REQUIRE_HUMAN
  criterion_without_test: BLOCK
blocked_by: []              # story IDs that must be `done` first; ordered by dependency-mapper
provenance:                 # where this story came from; re-hashed by gate
  - source: docs/plan/{{slug}}/epics/EPIC-000.md#{{story-anchor}}
    hash: sha256:{{64 hex}}
  - source: docs/PM/{{slug}}/prd.md#{{requirement-anchor}}
    hash: sha256:{{64 hex}}
context:                    # excerpt + anchor + hash, written by plan's story writer; never summarised
  - source: docs/architecture/constitution.md#{{anchor}}
    status: INTENDED        # INTENDED | OBSERVED ; OBSERVED is advisory, INTENDED binds
    hash: sha256:{{64 hex}}
    excerpt: |
      {{verbatim}}
write_fence:                # the only paths a producer may create or modify inside the candidate root
  - "{{package}}/{{module}}"
  - tests/{{test file}}
commands:                   # never literal commands; a hashed reference into stack.yaml
  source: .devforgeai/stack.yaml#{{language-or-package-anchor}}
  hash: sha256:{{64 hex}}
  use: [test, lint]         # keys granted to this run; the lease holder may call `devforgeai run <key>` for one, and the oracle runs them; `build` is required when that section has compiled: true
test_plan:                  # authoritative criterion-to-test map, one row per acceptance criterion;
                            # red-tester writes exactly these tests and the transition oracle asserts them
  - criterion: 1
    file: tests/{{test file}}
    name: "{{test name}}"
---

# STORY-000: {{title}}

## Goal

One sentence: the behaviour that exists when this story is done.

## Context

Point to the frontmatter bundle. State what already exists in the write fence and what is empty. No prose beyond that; the excerpts are the context. Every worker reads the bundle; none opens the source document.

## Interface

The contract green-implementer builds to: signatures, types or shapes, error behaviour, and any name that another story depends on. Write it in the project's language. If nothing is public, write `Internal only.`

## Acceptance Criteria

1. {{observable, testable statement}}
2. {{...}}

Numbered. Each criterion has exactly one `test_plan` row and becomes exactly one test. The recommended form is `WHEN {{condition}} THE SYSTEM SHALL {{observable result}}`; any form is accepted if a test can fail it. Write `ASSUMPTION: {{text}}` inline where a value is undecided. A story has an unresolved assumption when the text `ASSUMPTION:` appears anywhere in the body outside `## Clarifications`; dev's gate applies `gate_policy.unresolved_assumption` until `/clarify` moves the answer into Clarifications and removes the tag.

## Unchanged Behaviour

Behaviour that must still hold after this story, each line testable. Required when `scope` is `change` or `hotfix`; smoke-qa runs these as regression checks. For `feature` write `None.` only if nothing in the write fence had behaviour before.

## Out of Scope

- {{explicit exclusions so green-implementer does not add behaviour}}

## Verification

What each dev sub-phase must show, named only by `commands.use` key. No worker names a literal command: the lease-holding producer may call `devforgeai run <key>` for its own feedback, and the sequencer resolves the same key from `stack.yaml` and runs it in the transition check, which is what decides the phase:

- Red: `test` exits non-zero and every `test_plan` test is present and failing for its own criterion, not for an import or syntax error.
- Green: `test` exits zero with no test outside `test_plan` added or changed.
- Refactor: `test` and `lint` exit zero; no file outside `write_fence` changed.
- QA (light): `test` exits zero; Unchanged Behaviour checks pass; the critic finds no vacuous test.

## Clarifications

None. (`/clarify` appends dated Q/A entries here; nothing else may edit this file after `ready`.)
