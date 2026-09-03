# Repository Guidelines

## Project Structure & Module Organization

`framework/skills/` holds provider-neutral contracts; `providers/{claude,codex}/` holds adapters. `install-manifest.yaml` maps install destinations. `components/research-core/src/devforgeai/` is the Python package; `components/hook-runtime/reference/claude-python/` is the Claude hook POC. Schemas, tests, and normative design live under `schemas/`, `tests/`, and `docs/`.

## Build, Test, and Development Commands

- `PYTHONPATH=components/research-core/src python3 -m pytest tests/research -q` — Research suite.
- `python3 docs/design/specs/verify.py` — design and provenance validation.
- `python3 docs/design/examples/hooks/run_conformance.py` — enforcement conformance.
- `bash docs/design/examples/hooks/demo_sequencer.sh` — copy/worktree-mode demo.
- `python3 components/hook-runtime/reference/claude-python/tests/run_tests.py` — hook POC tests.
- `uv build` — wheel build; `git diff --check` — whitespace check.

## Coding Style & Naming Conventions

Python uses four spaces, type hints, `snake_case` functions/modules, `PascalCase` classes, `pathlib`, explicit validation, and deterministic output. Name tests `test_*.py` and schemas with lowercase hyphenated `*.schema.json`. No global formatter is configured; follow adjacent code.

## Worktrees & TDD Workflow

Never implement or commit on `main`. Use one topic branch in a dedicated worktree from `origin/main`; keep the canonical checkout clean. Contributor worktrees differ from sequencer candidate roots: use one candidate root per run, not per worker. The model dispatches; only the sequencer advances, rewinds, checkpoints, and promotes.

Story work follows red → green → refactor. Red changes only planned tests. Green/refactor change production files within `write_fence` and never modify tests. Defective tests return to red. Stories name `stack.yaml` keys, not literal commands.

## Testing Guidelines

Add positive and hostile contract cases: malformed input, path escape, stale digest, timeout, and fail-closed behavior. Test public CLI and hook boundaries through subprocesses. Never weaken assertions. An unavailable runner is `could_not_run`, not a fabricated result; use doc 10's closed status vocabulary.

## Commit & Pull Request Guidelines

Use an imperative subject such as `Add hook runtime boundary`; separate structural moves from behavior. Pull requests name the governing Story/ADR, changed contracts, issue, and exact verification results. Identify `NOT_EVALUATED` and unobserved provider behavior.

## Agent and Security Rules

Preserve other sessions' changes and obey write fences. Do not install the hook POC here or change implementation and authoritative outputs together merely to pass. After changing design docs 00–11 or templates, run `verify.py` and update dependent hashes. Draft contracts remain non-authoritative until human-promoted to protected DevForge and consumed by pinned version and digest.
