# Brownfield Support

DevForgeAI supports two entry states for existing codebases:

1. **Existing code, no docs.** Onboard maps current source citations in a run-local receipt. It does not generate a mandatory OBSERVED architecture document from facts that can be derived from source at use time.
2. **Existing code plus non-DevForgeAI docs** (README, ADRs, wiki, CONTRIBUTING). Onboard stops and asks the human to run `/research <slug> --request <request-file> --confirm-request <sha256>` on Claude or `$research <slug> --request <request-file> --confirm-request <sha256>` on Codex before those documents are persistently ingested as research sources. Core 0.1.0 rejects parent work orders before mutation.

Legacy DevForgeAI document migration is out of scope for this version; see `12-post-mvp.md#pm-08`. Onboard treats a legacy DevForgeAI document exactly as it treats any other non-DevForgeAI document.

## Entry flow

```
/init  →  detects code  →  mode: brownfield  →  /onboard  →  /architect <slug>  →  /plan <slug>
```

Then per request, the user selects the entry phase with `--scope`.

## The onboard skill

Persona: **Archaeologist**. Its job is to describe what exists, never to prescribe.

### Sub-phases

Worker names are authoritative in `05-subagent-sets.md`.

| # | Sub-phase | Performed by | Output |
|---|-----------|--------------|--------|
| 1 | Map | worker: code-mapper | repository paths and directly observed manifest or configuration facts, each with a source citation; plus the OBSERVED `.devforgeai/stack.yaml` written against the contract in `10-sequencer-and-contracts.md`. A command, language, or package-manager value not explicitly present is reported as unknown, never guessed. |
| 2 | Ingest | worker: doc-ingester, after the human completes an explicit digest-confirmed Research run | README, ADRs, wiki, CONTRIBUTING referenced through a sealed `docs/research/<slug>/runs/RUN-NNNNNN/` dossier and its custody records |
| 3 | Classify | worker: convention-inferrer | partition into source-derivable facts, which remain citations, and non-derivable constraints such as rationale, history, timing, and external obligations |
| 4 | Write | worker: observed-writer | optional OBSERVED sections containing only admitted non-derivable constraints; do not create an empty or source-derived OBSERVED architecture document |
| 5 | Review | worker: critic | every rule must cite a file path or a sealed Research RUN plus applicable Source/Evidence/Claim IDs and manifest digest; uncited rules are removed |
| 6 | Record + Handoff | sequencer, at `phase next` | state updated; `handoff.json` written; next: `/architect <slug>` |

The Map result is a bounded `devforgeai.worker-result/v1` receipt, not a
generated OBSERVED architecture artifact. A downstream skill's writer resolves
and rehashes current source paths when it builds a context bundle, and the gate
re-resolves every one of those digests at `phase start`. Only the optional
non-derivable constraints in step 4 and the promoted `stack.yaml` persist.

### OBSERVED vs INTENDED

Every constitution section carries a status:

```markdown
## Deployment window
<!-- status: OBSERVED  source: RUN-000001; SRC-000001; EVD-000001; CLM-000001; sealed manifest digest -->
The operations policy requires release approval during a named maintenance
window. Source code does not encode that external timing constraint.
```

- **OBSERVED** — optional sections written by onboard only for admitted facts that cannot be derived from current source, such as rationale, history, timing, or external constraints. Not binding. Source-derivable facts remain path-and-digest citations and are not copied into these sections.
- **INTENDED** — written by architect. Describes the target. Binding for dev, review, and QA.

Architect's gap-analyzer compares INTENDED sections with the OBSERVED constraint sections that exist and produces `EPIC-000 Migration` only for an evidenced gap. The user may defer, split, or delete any of these stories in plan. Until a section is marked INTENDED, review and QA treat it as advisory. Missing optional OBSERVED material is not itself a gap.

`/drift` re-runs the code-mapper against cited source paths, reports invalidated OBSERVED evidence where present, and reports where INTENDED sections have not been reached. Language, package-manager, build, test, lint, and format commands are not detected by heuristic: code-mapper writes the OBSERVED `.devforgeai/stack.yaml` inside the candidate root from facts present in manifests and configuration, reports anything absent as unknown, and the sequencer validates it against its schema before the run is promoted. The contract, including `build` being required when `compiled: true`, is in `10-sequencer-and-contracts.md`. Multi-package resolution is `12-post-mvp.md#pm-09`.

## Per-request entry with `--scope`

Brownfield requests vary in size. The user picks the entry phase:

| Scope | Entry | What is skipped | Provenance cost |
|-------|-------|-----------------|-----------------|
| `feature` | `/brainstorm <slug> --scope feature` | nothing | none |
| `change` | `/plan <slug> --scope change` | brainstorm, pm, architect | user writes the epic intent inline; plan records it as the PRD stand-in |
| `hotfix` | `/plan <slug> --scope hotfix "<intent>"` | brainstorm, pm, architect, epics | plan mints one `STORY-HOTFIX-NNN` with `ASSUMPTION` tags and hands off to `/dev <story>`; review and QA still run |

Rules:

- `--scope` is recorded in state and in the artifact frontmatter so `/analyze` can flag reduced-provenance work.
- `hotfix` requires an INTENDED constitution to exist. Without one, the framework downgrades to `change`.
- `feature` on brownfield runs pm in feature-PRD mode, not MVP mode.

## Context slicing for brownfield stories

Stories in brownfield projects reference code as well as docs. `plan`'s story-writer puts code excerpts with line anchors and hashes into the story's `context[]` bundle, and the gate re-resolves them when dev opens the run:

```yaml
context:
  - source: docs/architecture/architecture.md#request-pipeline
    status: INTENDED
    hash: sha256:...
    excerpt: "All HTTP handlers go through middleware/auth.py before routing."
  - source: src/middleware/auth.py#L1-L38
    status: OBSERVED
    hash: sha256:...
    excerpt: |
      def authenticate(request): ...
```

Dev sees both the rule and the current code it must change. It never opens the full file unless the story says so.

## Ingested docs as research

README, ADRs, and wiki pages are admitted through the Research custody policy so they enter the provenance chain. Onboard cites Source, Evidence, and Claim IDs plus the sealed run manifest; a bare hash is not enough. If a README claim conflicts with code, both observations remain recorded and the contradiction routes to the owning phase rather than being silently averaged.
