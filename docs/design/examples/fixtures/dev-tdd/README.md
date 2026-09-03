# dev-tdd fixtures

A minimal project the dev skill can be walked over end to end. `demo_sequencer.sh`
and `run_conformance.py` in `../../examples/hooks/` copy this tree to a scratch
directory and run against the copy; nothing here is edited in place.

Contents: `tinyapp/` (the package under test, with an empty `text.py`), `tests/`
(an empty suite), `pyproject.toml`, and `STORY-001.md` — a story v3 instance
whose `write_fence` is `tinyapp/text.py` and `tests/test_text.py`, whose
`test_plan` names three criteria, and whose `commands` anchor
`.devforgeai/stack.yaml#python`. Its provenance and context hashes are fixture
placeholders, so the gate needs `--lenient` to open a run against it: that flag
downgrades `unresolvable-source` and nothing else.

`overlays/eval-<id>/` are alternative states of the same tree for evaluation
runs; copy the fixture without `overlays/`, then copy one overlay over it (see
`overlays/README.md`).

## What a run does to this tree

Nothing, until the run is promoted. `devforgeai phase start` creates a candidate
root at `.devforgeai/work/<run>/wt` — a git worktree when the scratch copy is a
repository, a plain tree copy when it is not — and every producer writes there.
The fixture files above are the candidate's `base` checkpoint; each phase that
passes adds a checkpoint on top of it. `devforgeai promote <run>` is what finally
moves those bytes into the tree, and a run that is blocked or abandoned moves
none of them.

Two consequences worth knowing when you read a scratch directory afterwards:

- `tinyapp/text.py` at the top of the scratch tree is the fixture's empty
  version until promotion. The implementation lives in
  `.devforgeai/work/STORY-001/wt/tinyapp/text.py` while the run is open.
- `.devforgeai/work/STORY-001/` holds the run's own state: `run.yaml` (phase,
  fence, granted keys, lease, candidate), `context.json` (the slice the gate
  resolved), `<phase>-result.json` and `<phase>-report.md`, `handoff.json`, and
  in copy mode the `cp/<phase>/` checkpoints. None of it is part of the project.

## Running it against a real repository

`git init` the scratch copy and commit before `phase start` to see worktree mode:
the copy must have at least one commit, `.devforgeai/work/` must be gitignored,
and `.devforgeai/stack.yaml` must be tracked. If any of those fails the run stops
with `could_not_run: hook_fault` rather than quietly falling back to copy mode —
copy mode is for a tree with no repository, not a substitute for a broken one.
`demo_sequencer.sh` does exactly this for its second pass.
