---
# == template header: read by the DevForgeAI gate; not copied into instances ==
template: clarification
template_version: 1
accepts_versions: [1]
required_frontmatter: [id, story, template, template_version, date, status]
required_sections: ["### Question", "### Answer", "### Authority"]
id_pattern: "^CLR-[0-9]{3}$"
forbidden_text: ["TODO", "TBD", "{{", "}}", "<fill in>"]
# render: an instance is one entry appended under the story's existing `## Clarifications` heading
#   (11 section 2, path docs/plan/<slug>/stories/STORY-NNN.md#clarifications); headings are `###` so they
#   nest under it, and the instance frontmatter is emitted as the marker comment on the entry's first
#   line, not as a second file frontmatter, so two entries in one story stay distinguishable. `## Clarifications` is the only append-only section of a story after `ready`
#   (08-story-specification.md, immutability).
# provenance: the story section that carried the assumption, with its hash at the time the question was
#   asked (11 section 3). Not in 11's required list, so it is carried as the extra `provenance:` key.
# `### Authority` exists because the sequencer records a decision with a named authority in the handoff
#   envelope (10 section 6, decisions[].authority); an answer with no authority cannot be recorded there.
# status: open | answered. An `open` entry leaves the story's ASSUMPTION tag in place.
# == instance frontmatter: fill every field ==
id: CLR-000
story: STORY-000
template: clarification
template_version: 1
date: 2026-01-01
status: answered            # open | answered
provenance:
  - source: "docs/plan/{{slug}}/stories/STORY-000.md#acceptance-criteria"
    hash: sha256:{{64 hex}}
---

<!-- id: CLR-000  story: STORY-000  date: 2026-01-01  status: answered -->

### Question

The ambiguity, quoted from the story text that carried it, with the `ASSUMPTION:` tag it was raised against.

### Answer

The decided value, written so the acceptance criterion can be read without the question. One answer per entry.

### Authority

Who decided, and on what basis: a person, a constitution section, or an ADR. This is the value the handoff envelope records as the decision's authority.
