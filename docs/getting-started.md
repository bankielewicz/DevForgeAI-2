# Getting started

[Home](../README.md) / Getting started · [Skills](skill-roster.md) · [Architecture](architecture.md) · [Evidence](evidence.md)

Start by evaluating the reference components in a development worktree. These instructions do **not** install hooks, activate provider skills, or install a protected DevForge release.

## Before you begin

| Requirement | Used for |
| :--- | :--- |
| Linux, Git, and Bash | Research Core's filesystem requirements and the scratch demo |
| Python 3.12.3 | Matching the repository's CI environment; package metadata permits Python 3.11+ |
| uv 0.11.26 | Creating the locked development environment |
| Node.js 24.18.0 | Matching the CI demo's second stack; its built-in test runner needs no npm dependencies |

The version pins come from [the workflow](../.github/workflows/pr-verify.yml). Research Core requires Linux-specific filesystem operations; Python availability alone does not make it portable to another OS. See the [test contract](../tests/research/README.md).

## Create a contributor worktree

From an existing clone of this repository, choose an unused branch name and worktree path. For example:

```bash
git fetch origin
git worktree add -b work/first-check worktrees/first-check origin/main
cd worktrees/first-check
git status --short
```

The new worktree should be clean before work begins. Do not reset or stash another session's changes. A contributor worktree is separate from the candidate roots created inside a framework run.

## Run the local checks

Run from the new worktree root, with Python 3.12.3 already available:

```bash
UV_PYTHON=3.12.3 UV_PYTHON_DOWNLOADS=never uv sync --frozen --dev
uv run python -m pytest tests/research -q
uv run python docs/design/specs/verify.py
uv run python docs/design/examples/hooks/run_conformance.py
git diff --check
```

`uv sync` creates the local environment and may download locked dependencies; it does not install provider hooks. Success means each command exits zero. Do not interpret an unavailable dependency, skipped check, or partial run as a pass.

These checks cover the offline Research Core and checkpoint validator, design provenance, and enforcement fixtures. They do not exercise live Claude Code or Codex sessions.

## Watch the sequencer work

With Node available, use the locked Python environment for the shell script's subprocesses:

```bash
uv run bash docs/design/examples/hooks/demo_sequencer.sh
```

The demo uses synthetic workers and temporary projects, not provider agents. It runs the Python and Node fixtures in both copy and Git-worktree modes, checks red → green → refactor → smoke → review, and promotes the scratch candidate. No hooks are installed in your checkout and no network retrieval is performed by the demo.

Completion requires exit zero and this final line:

```text
DEMO OK: python copy/worktree green, node copy/worktree green
```

Scratch paths are printed for inspection. The fixtures use `--lenient` for placeholder document hashes: this is a fixture accommodation, **not a recommended production invocation or proof of strict provenance gating**. Two configured stacks do not prove automatic stack discovery. [Demo assertions and limits →](design/examples/hooks/README.md)

## Go deeper without installing

| Task | Command from the worktree root |
| :--- | :--- |
| Claude hook subprocess tests | `uv run python components/hook-runtime/reference/claude-python/tests/run_tests.py` |
| Codex hook subprocess tests | `uv run python components/hook-runtime/reference/codex-python/tests/run_tests.py` |
| Check the gap-plan records | `uv run python -m devforgeai.checkpoint validate --plan docs/research/spec-driven-development-gap-closure` |
| Build the staging Python package | `uv build --no-build-isolation` |

A zero-exit checkpoint validation does not close a checkpoint or authorize a protected install. The wheel packages Research Core; it is not a complete framework installer.

## Using the framework in a project

There is no complete installation walkthrough here because that path has not been established by the retained evidence. The [install manifest](../install-manifest.yaml) describes destinations; it is not itself an installer. The roster's `init` entry is a specification, not an instruction to run this chat's `/init` command.

Provider hook cookbooks exist for controlled experiments: [Claude](../components/hook-runtime/reference/claude-python/COOKBOOK.md) and [Codex](../components/hook-runtime/reference/codex-python/COOKBOOK.md). Read their scope and safety conditions first. Installing a hook changes agent behavior; it is a separate, explicitly authorized task in a disposable proof project, not part of the quickstart.

**You are here:** local evaluation. Next, inspect the [skill roster](skill-roster.md) for workflow design or the [evidence page](evidence.md) before choosing a live proof.
