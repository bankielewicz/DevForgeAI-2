---
id: ADR-0001
template: adr
template_version: 1
status: accepted
date: 2026-09-03
supersedes: null
depends_on:
  - source: "docs/design/00-overview.md#design-principles"
    hash: sha256:c9de942a8186ed9e53e6ea67380108f5240f9bb549f303a8ac02a5781892a096
provenance:
  - source: "docs/reviews/2026-09-02-research-core-0.1.0-review.md#7-required-before-merge"
    hash: sha256:fee73f410ac930d59ceea1d28b31f9d436ec6b002e703d7cbb980de2d36d604e
---

# ADR-0001: Research is a deterministic DevForge capability, not an anatomy-governed skill

## Context

The Research Core review (item 10, section 7) found that Research had been exempted from the seven-sub-phase skill anatomy across the design documents without a recorded human decision. The same review found the Python Research Core blocked on structural defects, and the project owner has since decided that the Python package will be extracted into a separate, protected DevForge repository and eventually ported to Rust. Three placements were weighed on 2026-09-03: Research inside the DevForge core, Research as a separate executable and repository, and Research reworked as an ordinary anatomy-governed skill with model workers. The owner selected the first, with one refinement recorded below.

## Decision

Research is a deterministic capability of the protected DevForge product, shipped in the same executable and distribution as the workflow kernel but as a separate module (a `devforge-research` crate once the Rust port exists), never inside the workflow-engine module. It keeps its own P0-P9 state machine, typed JSON/JSONL records, evidence custody rules and sole-writer guarantee. It shares the protected executable, storage primitives, locking and the top-level error envelope with the workflow kernel; its error codes stay namespaced and are not flattened into workflow codes. `/research` on Claude and `$research` on Codex are thin DevForgeAI provider adapters over that capability. Research is therefore excused from `01-skill-anatomy.md` as a deterministic service, not as a skill, and the public interface converges on `devforge research ...`, with `devforgeai-research` retained as a temporary compatibility alias. DevForgeAI owns no authoritative expected outputs for Research; it consumes reviewed, released contracts and conformance fixtures from DevForge by version and digest.

## Consequences

- The anatomy exemption in `01`, `02`, `04`, `05` and `SKILL-SPEC-018` is now authorised; the wording should say "deterministic capability", not "skill exempt from the anatomy".
- The Python package under `components/research-core/` is staging for extraction into DevForge, not a permanent DevForgeAI component.
- Research contracts (`framework/skills/research/`) are drafts until promoted into the DevForge repository; after promotion DevForgeAI pins them by version and digest.
- One trust root, one release pin, one lock protocol: the concurrent-Research-moves-the-candidate-base problem noted in `10-sequencer-and-contracts.md` is solved inside one runtime rather than across two executables.
- A Rust port is deferred until the public error taxonomy, CLI contract and language-neutral conformance fixtures exist and are stable.
- `01-skill-anatomy.md` handoff rule 1 needs the explicit Research carve-out the review asked for in item 9.

## Alternatives

| Alternative | Dropped because |
|---|---|
| Separate Research executable and repository | Two artifacts, trust roots, release pins, lock protocols and upgrade paths; the current separate CLI already forces the design to explain how concurrent Research writes move a workflow candidate's base. |
| Research as an anatomy-governed skill with model workers | Pushes evidence custody and the P0-P9 semantics into a generic model-worker lifecycle, weakening the sole-writer and custody guarantees that are the point of Research. |
