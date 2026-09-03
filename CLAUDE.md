# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

DevForgeAI is a spec-driven development framework for AI coding agents (Claude Code and Codex). This repo is mostly *design* plus two runnable pieces; there is no product build yet. Read `docs/design/00-overview.md` first, then `10-sequencer-and-contracts.md`. `docs/CHECKPOINT.md` (newest entry first) is the running record of what exists, what is verified, and what the owner still has to decide.

## Commands

All commands run from the repository root. The Python package lives at `components/research-core/src`, so it must be on `PYTHONPATH`.

```bash
# Research Core tests (165 tests, ~75 s; includes a wheel build)
PYTHONPATH=components/research-core/src python3 -m pytest tests/research -q
# one test
PYTHONPATH=components/research-core/src python3 -m pytest tests/research/test_store.py -k seal -q
# unittest form documented in tests/research/README.md
PYTHONPATH=components/research-core/src python3 -m unittest discover -s tests/research -t .

# Design battery: spec headers, forbidden text, depends_on hashes, producer/consumer xref, CLI grammar
python3 docs/design/specs/verify.py                 # or --only v1,v2,v4,v8

# Sequencer + hook dispatcher draft (docs/design/examples/hooks/)
python3 docs/design/examples/hooks/run_conformance.py   # allow/deny table; exit 0 = every row holds
bash docs/design/examples/hooks/demo_sequencer.sh       # STORY-001 through dev in copy and worktree mode

# hookd reference proof of concept (components/hook-runtime/reference/claude-python/)
python3 components/hook-runtime/reference/claude-python/tests/run_tests.py
```

Dependencies: Python 3.11+, PyYAML, `jsonschema`, `pytest`. There is no linter configured (`ruff` is absent on the dev machine, which `demo_sequencer.sh` uses to demonstrate the `could_not_run` path).

## Git workflow

`origin/main` is protected by a GitHub ruleset: pushes require a pull request. Never commit on `main`. Create a branch in a worktree, commit there, push the branch, open a PR with `gh pr create`, and stop; the owner merges. Keep the main checkout clean.

`tmp/` (downloaded reference repos) and `.claude/`, `.agents/`, `.codex/` (local activation copies of `providers/`) are gitignored on purpose. Never read the legacy DevForgeAI repo contents under `tmp/` when designing; the framework is being rebuilt without it.

### Worktrees

Use `claude --worktree <topic>` or the `EnterWorktree` tool; both create `.claude/worktrees/<topic>/` on branch `worktree-<topic>`, branched from `origin/main` (`worktree.baseRef` is the default `fresh`). `.claude/` is already gitignored, so nothing extra is needed. Name the worktree after the PR topic, one topic per worktree, and open the PR from its branch. Facts that matter here:

- **A worktree is a fresh checkout.** `tmp/` and the local `.claude/`, `.agents/`, `.codex/` copies are absent. Every command in this file uses repo-relative paths, so they work unchanged; `PYTHONPATH=components/research-core/src` resolves inside the worktree. There is no `.worktreeinclude`; nothing untracked is needed to build or test.
- **Isolation is enforced by Claude Code.** Edits, commands and git redirects that target the main checkout are refused while in a worktree. Hook scripts referenced by `${CLAUDE_PROJECT_DIR}` still run from the main checkout; a hook that needs the worktree path must read `cwd` from its input.
- **Cleanup.** An unchanged worktree is removed on exit; one with commits or edits prompts. After the PR merges, `git worktree remove .claude/worktrees/<topic>` and delete the branch.
- **Do not confuse this with the design's worktree mode.** The sequencer creates its own candidate-root worktrees on `devforgeai/<run>` branches inside a *target* project (doc 10 section 12). That mechanism is not used for developing this repository, and `demo_sequencer.sh` exercises it only in a scratch directory.

## Layout and what installs where

Destinations come from `install-manifest.yaml`, never from folder names.

| Folder | Role |
|---|---|
| `docs/design/00-12*.md` | Normative design. 10 is the sequencer/CLI/state contract, 11 the artifact registry (18 skills, 29 templates), 12 the post-MVP list. `adr/` holds decisions (ADR-0001: Research placement). |
| `docs/design/templates/` | The 29 artifact templates. Each has a machine-readable header (`required_frontmatter`, `required_sections`, `id_pattern`, `forbidden_text`) that the gate checks without an LLM. |
| `docs/design/specs/` | The 18 `SKILL-SPEC-NNN` files, `verify.py`, and the author kit (`AUTHOR-BRIEF.md`, `ANTI-CEREMONY.md`). |
| `docs/design/examples/hooks/` | Runnable draft of the write model: `devforgeai.py` (sequencer), `dispatch.py` (hook dispatcher, one script for both providers), `policy.py` (shared path/phase policy), fixtures, provider config fragments. |
| `components/hook-runtime/` | Runtime code for the provider hook layer, a component and not provider payload. Today only `reference/claude-python/`: `hookd`, one dispatcher per event with an explicit check registry, Claude-only (Claude and Codex hook schemas differ, so it is not dual-provider). Not the authoritative contract; the real runtime belongs in protected DevForge. Its CHECKPOINT entry lists defects it found in the older `examples/hooks/dispatch.py`. |
| `framework/skills/<name>/` | Provider-neutral skill material (today: the Research contracts). Installs to `.devforgeai/skills/`. Single source; adapters' `references/` are derived copies, never hand-edited. |
| `providers/claude/`, `providers/codex/` | Thin adapters: `SKILL.md`, agent profiles. Codex skills install to `.agents/`, its agents and hooks to `.codex/`. |
| `components/research-core/` | The Python Research Core and `devforgeai-research` CLI. Temporary staging for extraction into the protected DevForge repo (ADR-0001); never copied into a target project, shipped as a wheel. |
| `schemas/devforgeai/v1`, `schemas/research/v1` | JSON Schemas (Draft 2020-12). The wheel ships the research set under `share/devforgeai/`. |
| `docs/research/` | Evidence corpora with `MANIFEST.sha256`; the landscape comparison is non-normative input. |

## Architecture you need across files

**The model dispatches, the sequencer decides.** The deterministic `devforgeai` command (draft: `examples/hooks/devforgeai.py`) is the sole writer of `.devforgeai/**`. It opens a run, creates a candidate root (git worktree when the project is a repo, tree copy otherwise), gates the incoming artifact against its template header and provenance hashes, records the enforcement block, runs transition oracles (red: every `test_plan` test present and failing on an assertion; green: all pass, test files unchanged since red, nothing outside the fence changed), checkpoints, rewinds, and promotes. Promotion is explicit (`devforgeai promote <run>`), never automatic. Hooks (`dispatch.py`/`hookd`) read that state and deny anything the current phase does not authorise; they block with exit 2 plus a reason on stderr, the one protocol both providers honour.

**Write permission is per role.** Producer workers (red, green, refactor, writers) write complete files inside the candidate root under a lease bound at SubagentStart; judges (gate, critic, review, qa, smoke) write only evidence. A worker's final message is one `devforgeai.worker-result/v1` receipt naming changed paths and hashes, never file bodies; the sequencer derives the real diff from the checkpoint. The primary window never writes and never reads artifact content; it forwards paths and envelopes. `docs/design/specs/WRITE-MODEL-REVISION.md` records the decisions (D1-D12).

**Provenance is hashed, not recalled.** Every artifact carries `context:`/`depends_on:` entries as `path#anchor` plus `sha256:`. The hash rule is in `01-skill-anatomy.md` (heading anchor = GitHub slug; section runs to the next heading of same or higher level; CRLF to LF; join with LF plus one trailing LF). `verify.py --only v3` recomputes them; after editing any of 00-11 or a template, hashes that cite it must be recomputed. `sha256:PENDING` is a placeholder the sequencer resolves at ingest; `sha256:fixture...` is a fixture marker.

**Research is a deterministic capability, not a skill.** Per ADR-0001 it keeps its own P0-P9 state machine, custody rules and namespaced errors, and is exempt from the seven-sub-phase anatomy. `/research` and `$research` are thin adapters over the `devforgeai-research` CLI, which today cannot pass preflight from the shipped interface (review section 3.2). The Research Core review at `docs/reviews/2026-09-02-research-core-0.1.0-review.md` lists the blockers; treat its section 7 as the open fix list.

## TDD loop: red, green, refactor, QA

The `dev` skill (and its `dev-tdd` variant, selected when `constitution.md#mandates` has `tdd: required`) is one linear run over a story: `base → red → green → refactor → smoke → review`, then `/review` and `/qa` as separate story-anchored runs. Normative text: `05-subagent-sets.md` worked example, `10-sequencer-and-contracts.md` sections 4, 5.4 and 12, and the story's own `## Verification` section. The sequencer, not the worker, decides whether a phase passed.

| Phase | Worker | Writes | Command keys | Oracle at the transition | Attempts | Rewind |
|---|---|---|---|---|---|---|
| red | `red_dev` | test files under the story's `test_paths` only, one test per `test_plan` row | `test` | every `test_plan` name present and `failed` on an assertion; a missing name is `criterion_without_test`; an import or collection error is `COLLECTION_ERROR`, not red | 2 | — |
| green | `green_dev` | production code inside `write_fence`; never a test file | `test`, `build` | all `test_plan` tests pass; test-file hashes unchanged since the red checkpoint; nothing outside the fence changed; no forbidden package or import | 3 | `red` |
| refactor | `refactor_dev` | production code only | `test`, `build`, `lint` | as green, plus `lint` exits zero | 2 | `red` |
| smoke | `smoke_qa` | nothing but its findings under `work/<run>/evidence/<agent>/` | `test` | report-only: one pass/fail row per acceptance criterion from the recorded oracle output | 2 | — |
| review (critic) | judge | evidence only | — | every criterion maps to a test, every test to code, no unresolved `ASSUMPTION`, diff respects the constitution slice | 2 | — |

Rules that hold across all of it:

- **Tests are the contract.** A green or refactor worker that finds a test wrong does not edit it; it returns `status: fail` with `next: red`, and the sequencer resets the candidate root to the checkpoint red started from. There is no `test_defect` status. Smoke failure routes back to green, never to red.
- **No literal commands.** A worker names a `stack.yaml` key and runs `devforgeai run <key>` for its own feedback inside the candidate root. The sequencer re-runs the same key at `ingest-result` and reads the JUnit output; that run, not the worker's claim, advances or rewinds the phase.
- **Runner missing is not failure.** A missing test or lint runner classifies as `INFRA_FAILURE` or `TIMEOUT`, the worker or sequencer returns `could_not_run` with a `reason_code`, and the run blocks at the phase under `gate_policy.test_runner_missing` (default `REQUIRE_HUMAN`) with a resumable `blocked_at`. Never fabricate a pass or fail.
- **Attempts are per phase** in `run.yaml#max_attempts`. Exhausting them ends the run `dev_blocked` with a `REQUIRE_HUMAN` handoff; the model never gets a retry loop it controls.
- **Fix mode** (`/dev <story> --fix`) narrows only the red oracle: the required-fail set is the `test_plan` rows the qa or review report marked failed plus any test added in this run; every other planned test must already pass at the red checkpoint. The runnable draft does not implement this narrowing yet.
- **Light QA versus `qa`.** `smoke` answers "does this story work" so dev can hand off. Full regression, Unchanged Behaviour checks (required for `change` and `hotfix` scope), cross-story checks and evidence capture belong to the `qa` skill, which runs the story's `test` key as a judge and routes defects to the owning phase rather than always to `/dev --fix`.

**Contracts drafted here are not authoritative.** Once accepted, a human promotes them to the protected DevForge repository and this repo consumes them pinned by version and digest, so the agent that drafts a contract cannot move its own goalposts. Do not present drafted expected outputs as accepted.

## Conventions the docs enforce

- Status vocabulary is closed and set in `10-sequencer-and-contracts.md` section 3 (`pass | fail | needs_user | could_not_run`, gate policy `BLOCK | REQUIRE_HUMAN | WARN | OFF`). Do not invent statuses.
- `verify.py` V2 fails on forbidden strings in `docs/design/**` (for example `Provider Conformance`, `attestation`, `UNSUPPORTED_CAPABILITY`, `template_version: 2`, `Bash(pytest`). Check the `FORBIDDEN` list before reintroducing retired vocabulary.
- Stories never carry literal build or test commands; they reference `stack.yaml` keys. Keep the framework stack-neutral; pytest in an example is illustration only.
- Templates are write-once at `status: ready` except `status` and the append-only Clarifications section.
- Nothing in `examples/hooks/` or `components/hook-runtime/` has fired from a live Claude Code or Codex session yet. Do not describe hooks as implemented; describe them as runnable drafts until the live proof in CHECKPOINT is done.
