# Repository Guidelines

## Start Here

Read `docs/design/00-overview.md`, `10-sequencer-and-contracts.md`, and the governing skill specification before changing behavior. `docs/CHECKPOINT.md` records decisions and evidence; check the referenced source and raw evidence before repeating a support claim. This repository contains framework design, provider adapters, and executable staging components for the separate protected DevForge product.

## Project Structure & Module Organization

- `framework/skills/`: provider-neutral material; adapter references are derived copies.
- `providers/{claude,codex}/`: source adapters and agent profiles. Destinations come from `install-manifest.yaml`; local `.claude/`, `.agents/`, and `.codex/` are activation copies.
- `components/research-core/src/devforgeai/`: Python Research Core and checkpoint validator, staged for extraction under ADR-0001.
- `components/hook-runtime/reference/{claude,codex}-python/`: separate hook implementations, tests, and cookbooks; their protocols are provider-specific.
- `docs/design/examples/hooks/`: runnable sequencer, dispatcher, policy, and fixtures. Contributor worktrees are separate from these fixtures' candidate roots.
- `schemas/`, `tests/`, `docs/design/{templates,specs}/`: machine contracts, tests, and specifications. `docs/research/` holds evidence dossiers and manifests.

## Build, Test, and Development Commands

Run from the active worktree root. Research Core requires Linux and Python 3.11+. CI tool versions live in `.github/workflows/pr-verify.yml`.

```bash
# Reproduce the locked environment; requires Python 3.12.3 already installed.
UV_PYTHON=3.12.3 UV_PYTHON_DOWNLOADS=never uv sync --frozen --dev
uv run python -m pytest tests/research -q
uv run python docs/design/specs/verify.py
uv run python docs/design/examples/hooks/run_conformance.py
bash docs/design/examples/hooks/demo_sequencer.sh
uv run python components/hook-runtime/reference/claude-python/tests/run_tests.py
uv run python components/hook-runtime/reference/codex-python/tests/run_tests.py
uv run python -m devforgeai.checkpoint validate --plan docs/research/spec-driven-development-gap-closure
uv build --no-build-isolation
git diff --check
```

The demo exercises Python and Node in copy/worktree modes. With dependencies already available, the source-only Research command is `PYTHONPATH=components/research-core/src python3 -m pytest tests/research -q`. Use `python -m pytest` so repository test imports resolve.

## Coding Style & Naming Conventions

Python uses four spaces, type hints, `snake_case` functions/modules, `PascalCase` classes, `pathlib`, explicit validation, and deterministic output. Name tests `test_*.py` and schemas with lowercase hyphenated `*.schema.json`. No global formatter is configured; follow adjacent code.

## Worktrees & TDD Workflow

Never implement or commit on `main`. Use one topic branch in a dedicated worktree from `origin/main`; keep the canonical checkout clean. Contributor worktrees differ from sequencer candidate roots: use one candidate root per run, not per worker. The model dispatches; only the sequencer advances, rewinds, checkpoints, and promotes.

Story work follows red → green → refactor. Red changes only planned tests. Green/refactor change production files within `write_fence` and never modify tests. Defective tests return to red. Stories name `stack.yaml` keys, not literal commands.

Inside framework runs, producers use `writes: candidate` under a lease. Judges use `writes: none` and return bounded `findings` in their receipt; the sequencer persists them. Producers may run only granted keys through `devforgeai run <key>`; the sequencer independently runs transition oracles. The primary passes paths, status, and receipts, including bounded judge findings, without loading worker transcripts.

## Testing Guidelines

Add positive and hostile contract cases: malformed input, path escape, stale digest, timeout, and fail-closed behavior. Test public CLI and hook boundaries through subprocesses. Never weaken assertions. An unavailable runner is `could_not_run`, not a fabricated result; use doc 10's closed status vocabulary.

## Commit & Pull Request Guidelines

Use an imperative subject such as `Add hook runtime boundary`; separate structural moves from behavior. Pull requests name the governing Story/ADR, changed contracts, issue, and exact verification results. Identify `NOT_EVALUATED` and unobserved provider behavior.

The explicit PR skill accepts `/pr --base <40-lowercase-hex> --head <40-lowercase-hex> [--draft]`. It prepares a packet and ends at `complete_external`; publication remains human-owned. Repository push/PR work requires the user's authorization; the owner merges.

Hosted checks are advisory evidence. Keep action references pinned, permissions read-only, and secrets absent. An unavailable release candidate must fail its lane. Local tests, hosted tests, and live provider probes prove different things; none independently authorizes protected installation or checkpoint closure.

## Agent and Security Rules

Preserve other sessions' changes and obey write fences. Do not install hook POCs here or change implementation and authoritative outputs together merely to pass. After changing cited design sections or templates, recompute affected dependency hashes with the rule in `01-skill-anatomy.md` and run `verify.py`.

Frozen CP-00 candidate files and pins must remain consistent with their governing source commit. Do not re-pin them to make an unrelated change pass. PR additions use staged v2 run/taxonomy contracts alongside frozen v1 contracts. Drafts become authoritative only after human promotion to protected DevForge and consumption by pinned version and digest. Do not import legacy framework assumptions from `tmp/`.
