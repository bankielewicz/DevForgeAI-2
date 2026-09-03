---
# == template header: read by the DevForgeAI gate; not copied into instances ==
template: observed-constraints
template_version: 1
accepts_versions: [1]
required_frontmatter: [id, template, template_version, status, scope, evidence]
required_sections: ["### Constraint", "### Evidence", "### Why It Is Not Derivable"]
id_pattern: "^OBS-[0-9]{3}$"
forbidden_text: ["TODO", "TBD", "{{", "}}", "<fill in>"]
# render: an instance is one section appended under `## Observed` in docs/architecture/sourcetree.md,
#   techstack.md or architecture.md (11-artifact-registry.md section 2, divergence 6); headings are `###`
#   so they nest under the host's `## Observed`, and the instance frontmatter is emitted as the marker
#   comment on the section's first line (the form 03-brownfield.md shows), not as a second file frontmatter.
# provenance: carried by `evidence:`; each row is a source anchor plus hash, or a sealed Research
#   RUN/SRC/EVD/CLM reference plus manifest digest (03-brownfield.md). No separate `provenance:` key,
#   because a second list of the same anchors would be a second thing to keep current.
# status: derived from 03-brownfield.md; onboard writes OBSERVED only. INTENDED is architect's to write.
# scope: derived from onboard's document fence in 10-sequencer-and-contracts.md section 4 (exactly three files).
# == instance frontmatter: fill every field ==
id: OBS-000
template: observed-constraints
template_version: 1
status: OBSERVED            # OBSERVED only; architect writes INTENDED sections in its own templates
scope: architecture         # sourcetree | techstack | architecture ; the host file this section joins
evidence:                   # one row per citation; a bare hash is not a provenance reference
  - source: "src/{{module}}/{{file}}#L1-L20"
    hash: sha256:{{64 hex}}
  - source: "docs/research/{{slug}}/runs/RUN-000000/"
    ids: "SRC-000000; EVD-000000; CLM-000000"
    manifest: sha256:{{64 hex}}
---

<!-- status: OBSERVED  id: OBS-000  source: SRC-000000; EVD-000000; CLM-000000; sealed manifest digest -->

### Constraint

One sentence naming the constraint that governs this project and that current source does not encode.

### Evidence

One line per `evidence:` row: what that citation shows, in the citation's own words.

### Why It Is Not Derivable

Why a reader cannot get this from current source: rationale, history, timing, or an external obligation. A fact the gate could re-resolve from a path belongs in a citation, not here.
