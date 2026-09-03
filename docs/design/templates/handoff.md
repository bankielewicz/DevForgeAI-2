---
# == template header: read by the DevForgeAI gate; not copied into instances ==
template: handoff
template_version: 1
accepts_versions: [1]
required_frontmatter: []
required_sections: ["## You Are Here", "## Artifacts", "## Open Issues", "## Next Steps", "## Also Possible"]
id_pattern: "^[a-z][a-z0-9-]*$"
forbidden_text: ["TODO", "TBD", "{{", "}}", "<fill in>"]
# required_frontmatter is empty because 11's row records this template as the rendering of
#   .devforgeai/work/<run>/handoff.json: the JSON envelope is the authority and the printed block carries
#   no frontmatter of its own. The instance block below names the envelope fields the renderer reads
#   (10 section 6), so a reader can tell which field each section comes from.
# id_pattern applies to `skill`, the skill whose run this handoff closes.
# No `depends_on` and no `provenance`: a handoff is evidence of one run (11 section 3). The lineage it
#   shows is `source_basis`, which is the set of provenance and context entries the gate re-resolved.
# The renderer adds nothing: a field absent from the envelope is absent from the block
#   (10 section 6, rendering rule 8). A section with no envelope field behind it is therefore omitted
#   from the printed block rather than filled with a placeholder.
# == instance frontmatter: fill every field ==
run: "{{run}}"
skill: "{{skill}}"
phase: "{{phase}}"
location: ".devforgeai/work/{{run}}/"
outcome: pass               # pass | BLOCK | REQUIRE_HUMAN | WARN | OFF
next: "/{{skill}} {{arg}}"  # exactly one copy-pasteable command; mirrored into state.yaml as `next`
session_id: "{{session_id}}"
session_guidance: continue  # continue | fresh_session
authority:
  write_fence:
    - "{{fence pattern}}"
---

# DevForgeAI Handoff

## You Are Here

One line from the Location and Result groups: the phase just completed, the phase now active, and the phases remaining, plus the project slug and mode.

## Artifacts

One line per `artifacts[]` entry: the path, its `sha256`, the `checkpoint` it was recorded at, and the phase that produced it.

## Open Issues

One line per `open_items[]` entry, blocking items first: the id, the text, and the owner. Printed before Next Steps.

## Next Steps

The `next` command, numbered `1.`, followed by any blocking commands the repair route named, in the order to run them. Every command works from a cold session because it resolves through state.yaml.

## Also Possible

Alternative commands that are valid but not the default, one per line with the reason to choose one. Absent when the envelope names no alternative.
