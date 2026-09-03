---
# == template header: read by the DevForgeAI gate; not copied into instances ==
template: skill-yaml
template_version: 1
accepts_versions: [1]
required_frontmatter: [name, version, target, handoff, workers]
required_sections: ["## Identity", "## Phases", "## Workers", "## Handoff Outcomes"]
id_pattern: "^[a-z][a-z0-9-]*$"
forbidden_text: ["TODO", "TBD", "{{", "}}", "<fill in>"]
# required_sections derived: 11's row records only that this is not a Markdown artifact, so the four
#   sections are the blocks the neutral definition has to carry - identity (name, version, target), the
#   phase list from 10-sequencer-and-contracts.md section 4, the worker set from 05-subagent-sets.md,
#   and the `handoff.outcomes` decision table each skill declares (01-skill-anatomy.md, handoff contract).
# render: the instance frontmatter is the whole of .devforgeai/skills/<name>/skill.yaml. The body is the
#   design-time explanation of each block, not part of the installed YAML.
# id_pattern applies to `name`, which equals the skill directory name.
# provenance: the skill-spec sections this definition was generated from (11 section 3). Not in 11's
#   required list, so it is carried as the extra `provenance:` key.
# == instance frontmatter: fill every field ==
name: "{{skill-name}}"
version: "1.0.0"
target: both                # claude | codex | both
phases:                     # in run order; names match the registry in 10 section 4 exactly
  - name: "{{phase}}"
    worker: "{{canonical_worker_name}}"
    writes: docs            # docs | tests | code | none
    max_attempts: 2
    oracle: document        # document | red | green | refactor | report_only
workers:
  - name: "{{canonical_worker_name}}"
    file: "subagents/{{role}}.md"
    isolation: required     # required | preferred
handoff:
  outcomes:
    - outcome: pass
      next: "/{{next-skill}} {{arg}}"
    - outcome: could_not_run
      next: "{{repair route for reason_code}}, then /{{skill}} {{arg}}"
provenance:
  - source: "docs/plan/{{slug}}/skill-specs/SKILL-SPEC-000.md#7-procedure"
    hash: sha256:{{64 hex}}
---

# Skill Definition: {{skill-name}}

## Identity

`name` equals the skill directory name and the slash or dollar command stem. `version` is the skill-package version, not the DevForgeAI version. `target` selects which adapters are compiled.

## Phases

One entry per phase, in run order, with names matching the per-skill registry exactly. `writes`, `max_attempts` and `oracle` are the values the sequencer materialises into `.devforgeai/work/<run>/run.yaml`; a phase that names no worker cannot exist.

## Workers

One entry per skill-owned worker, pointing at its `subagents/<role>.md` file. Gate, Record and Handoff are sequencer operations and have no entry here.

## Handoff Outcomes

The decision table the sequencer selects a row from by envelope status. Every status the skill can return needs a row, including `could_not_run`, and every `next` is one exact command.
