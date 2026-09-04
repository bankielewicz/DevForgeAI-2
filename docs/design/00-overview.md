# DevForgeAI — Overview

DevForgeAI is a spec-driven development framework for AI coding agents (Claude Code and Codex CLI). It turns an idea into shipped, verified code through a fixed sequence of phases, each producing a reviewed artifact that the next phase consumes.

## Design principles

1. **Thin orchestration.** Provider entry adapters parse arguments, call the sequencer, load a skill, and print the handoff the sequencer rendered. Nothing else.
2. **The model dispatches, the sequencer decides.** Write permission is per role: producer workers write inside the run's candidate root and return a receipt that names paths, never file bodies; judge workers write nothing and return their findings as a bounded `findings` string in the receipt (at most 16 KiB), which the sequencer persists to the run's evidence directory. That findings body reaches the primary window as the subagent's result, as the provider model requires; the worker's transcript, reads, tool traffic and reasoning stay isolated. The primary window dispatches those workers and calls the model-callable sequencer operations; the deterministic `devforgeai` sequencer owns the candidate root, gates, checkpoints, runs the transition oracle, advances, promotes, and is the sole writer of canonical `.devforgeai/**`. See `01-skill-anatomy.md#primary-window-contract` and `10-sequencer-and-contracts.md`.
3. **The primary window does trivial work only.** Anatomy-governed phase skills delegate their bounded sub-phases. Research is the explicit exception: `framework/skills/research/` defines its P0-P9 workflow, contracts for four bounded worker roles that write nothing, typed records, and deterministic Research Core as the sole canonical writer. Those contracts do not make provider workers installed or executable.
4. **Provenance over recall.** A non-Research artifact claim traces to a constitution section, code file, or sealed Research dossier reference, or is tagged `ASSUMPTION`. Research uses only its closed claim types and never treats `ASSUMPTION` as a claim or evidence class.
5. **Context slicing.** Downstream phases never read entire constitution documents. They receive excerpts with anchors and hashes (see `01-skill-anatomy.md`).
6. **Gate on entry.** Every anatomy-governed skill validates its incoming artifact against that artifact's template and provenance chain before doing any work. Research instead applies the request, schema, custody, verification, and sealing gates under `framework/skills/research/`. A story whose context bundle hashes no longer match the constitution is rejected at the door, not discovered in dev.
7. **Dedicated templates.** Every anatomy-governed non-Research skill owns its templates under `.devforgeai/skills/<name>/templates/`. Templates are the contract between those phases; Research uses typed schemas and contracts.
8. **One pipeline, two entry doors.** Greenfield enters at `init → brainstorm`. Brownfield enters at `init → onboard`, then joins the same pipeline at a phase the user selects per request.
9. **Provider neutral semantics.** A neutral capability or skill specification is authoritative; Claude Code and Codex adapters are generated separately when their invocation controls or metadata differ (see `04-dual-target.md`).

The draft landscape comparison in `docs/research/sdd-landscape-comparison-2026-09-02.md` is non-normative evidence. Its recommendations change this design only when an applicable design document states the resulting contract explicitly.

## Phases

| # | Phase | Persona | Command | Primary artifact |
|---|-------|---------|---------|------------------|
| 0 | Init | Installer | `/init` | `.devforgeai/state.yaml`, doc skeleton |
| 0b | Onboard (brownfield) | Archaeologist | `/onboard` | optional non-derivable OBSERVED constraints; source-derived facts stay live |
| 1 | Brainstorm | Business Analyst | `/brainstorm <slug>` | `docs/brainstorm/<slug>.md` |
| 2 | Project Management | Project Manager | `/pm <slug>` | `docs/PM/<slug>/prd.md` |
| 3 | Architecture | Senior Architect | `/architect <slug>` | constitution, sourcetree, techstack, architecture, design-* |
| 4 | Plan | Scrum Master | `/plan <slug>` | epics, stories, sprints |
| 5 | Dev | Developer | `/dev <story>` | code, tests |
| 6 | Review | Reviewer | `/review <story>` | review report |
| 7 | QA | QA Engineer | `/qa <story>` | pass/fail, fix guidance |
| 8 | Close | Scrum Master / Architect | `/retro`, `/amend`, `/drift` | lessons, amendments, drift report |

Cross-cutting persistent Research accepts only `/research <slug> --request <request-file> --confirm-request <sha256>` on Claude and `$research <slug> --request <request-file> --confirm-request <sha256>` on Codex. Pull-request preparation accepts only explicit full commit pins through `/pr --base <40hex> --head <40hex> [--draft]`; it prepares a checked external packet and never calls GitHub. Other entries use their target-specific adapter form for `clarify`, `analyze`, `skill-gen`, `skill-validate`, and `status`.

## Phase diagram

```mermaid
flowchart TD
    subgraph INIT["init"]
        I1[detect repo] --> I2[pick target claude / codex / both] --> I3[write state + skeleton]
        I3 --> I4{existing code?}
    end

    subgraph ONB["onboard  (Archaeologist)"]
        O1[map directly observable source facts] --> O2[human runs explicit confirmed Research request for README / ADRs / wiki] --> O3[record only non-derivable OBSERVED constraints] --> O4[critic: every retained rule cites evidence] --> O5[handoff]
    end

    subgraph BS["brainstorm  (Business Analyst)"]
        B1[capture ideas] --> B2[explicit confirmed Research request; consume sealed dossier] --> B3[critic review] --> B4[handoff]
    end

    subgraph PM["pm  (Project Manager)"]
        P1[read brainstorm] --> P2[split MVP / feature vs archive] --> P3[write PRD] --> P4[critic] --> P5[handoff]
    end

    subgraph ARCH["architect  (Senior Architect)"]
        A1{yolo?} -->|yes| A2[auto-select best practices]
        A1 -->|no| A3[deep-dive discussion]
        A2 --> A4[mint INTENDED constitution set]
        A3 --> A4
        A4 -->|evidenced gap| A8[recorded OBSERVED constraints vs INTENDED gap → epic 0]
        A4 -->|no evidenced gap| A7
        A4 --> A5[optional prototype]
        A4 --> A6["mandates → constitution.md#mandates"]
        A5 --> A7[handoff]
        A6 --> A7
        A8 --> A7
    end

    subgraph PLAN["plan  (Scrum Master)"]
        L0[gate: PRD + constitution] --> L1[slice constitution] --> L2[epics] --> L3[stories / specs] --> L3b[skill specs for missing skills] --> L4[sprint assignment] --> L5[analyze traceability] --> L6[handoff]
    end

    subgraph SG["skill-generator / skill-validator"]
        S1[spec] --> S2[generate neutral skill] --> S3[compile claude + codex] --> S4[validate vs constitution]
    end

    subgraph DEV["dev  (Developer)"]
        D0[gate: story vs template + hashes] --> D1[clarify story] --> D2[load story slice] --> D3[implement / TDD] --> D4[self-check] --> D5[handoff]
    end

    subgraph REV["review"]
        R1[constitution compliance] --> R2[security / quality]
    end

    subgraph QA["qa  (QA Engineer)"]
        Q1[run acceptance criteria] --> Q2{pass?}
    end

    subgraph CLOSE["retro / drift / amend"]
        C1[retro lessons] --> C2[amend constitution] --> C3[impact re-slice]
        C4[drift check]
    end

    subgraph PR["pr  (Release Coordinator)"]
        PR0[gate exact committed base..head] --> PR1[pr-drafter writes title + body]
        PR1 --> PR2[pr-critic reads and judges]
        PR2 --> PR3[sequencer persists packet + request]
        PR3 --> PR4[REQUIRE_HUMAN: push and create PR]
    end

    I4 -->|greenfield| BS
    I4 -->|brownfield| ONB
    ONB --> ARCH
    BS --> PM --> ARCH --> PLAN --> DEV --> REV --> QA
    ENTRY{{"brownfield request<br/>--scope feature | change | hotfix"}}
    GATE[[every phase: gate incoming artifact<br/>vs template + provenance hashes]]
    ENTRY -->|feature| BS
    ENTRY -->|change| PLAN
    ENTRY -->|hotfix| PLAN
    A5 -.->|new ideas| BS
    L3b -.->|plan owns the skill spec| SG
    SG -.-> DEV
    Q2 -->|fail: /dev story --fix| DEV
    Q2 -->|pass| CLOSE
    ARCH -.->|accepted boundary| PR
    PLAN -.->|analyzed boundary| PR
    SG -.->|validated boundary| PR
    Q2 -.->|passing QA boundary| PR
    C2 -.->|accepted amendment boundary| PR
    C3 -.->|affected stories| PLAN
    C4 -.-> ARCH
```

## Repository layout produced by the framework

Everything under canonical `.devforgeai/` is written by the `devforgeai` sequencer and by nothing else. A producer worker writes only inside its run's candidate root, and those bytes reach the canonical tree by promotion.

```
.devforgeai/
  state.yaml              # story statuses, runs, next command
  stack.yaml              # hash-pinned build/test/lint/format contract; see 10
  hooks/                  # dispatch.py, policy.py, devforgeai.py; installed by init
  work/<run>/             # evidence home: <phase>-report.md, <phase>-result.json, handoff.json
  work/<run>/run.yaml     # per-run enforcement: phase, fence, granted keys, lease (gitignored)
  work/pr-*/output/       # accepted external title/body, pr-request.json and pr-packet.json; never promoted
  work/<run>/evidence/<agent>/  # findings.md, written by the sequencer from a judge's receipt (gitignored, never promoted)
  work/<run>/wt/          # the run's candidate root, where producers write (gitignored)
  sessions/<session_id>.json  # session evidence, written once by hook-only session-start
  provenance/
    adr/NNNN-*.md         # architecture decisions
    log.jsonl             # one line per skill run
  research-cas/sha256/... # local-only retained Research bytes; never tracked
  skills/<name>/
    skill.yaml            # neutral skill spec (compiled to .claude/ and .agents/)
    templates/*.md        # this skill's dedicated templates
docs/
  research/
    _cas/sha256/...       # tracked objects that passed Research custody gates
    <slug>/registry.jsonl
    <slug>/runs/RUN-NNNNNN/  # canonical JSON/JSONL, handoff.json, MANIFEST.sha256
  brainstorm/<slug>.md
  PM/<slug>/prd.md
  PM/<slug>/backlog-ideas.md
  architecture/
    constitution.md
    sourcetree.md
    techstack.md
    architecture.md
    design-<topic>.md
  plan/<slug>/
    epics/EPIC-NNN.md
    stories/STORY-NNN.md
    sprints/sprint-NNN.md
    skill-specs/SKILL-SPEC-NNN.md
  reports/
    analyze-*.md, review-*.md, qa-*.md, drift-*.md, retro-*.md
```

`docs/reports/*` is a rendered view of `.devforgeai/work/<run>/`, written by the sequencer at `phase next`. The evidence itself lives under `work/<run>/`; see `01-skill-anatomy.md#evidence-home`.
