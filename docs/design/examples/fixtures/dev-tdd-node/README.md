# dev-tdd-node fixtures

The Node sibling of `../dev-tdd/`. Same story, same three acceptance criteria,
same phase path through the dev skill; a different ecosystem underneath.
`demo_sequencer.sh` in `../../examples/hooks/` copies this tree to a scratch
directory and runs against the copy; nothing here is edited in place.

## What it demonstrates, and what it does not

It demonstrates exactly this: **two interpreted ecosystems run through the same
stack-selected workflow.** The sequencer, the dispatcher, the phase registry,
the write fence, the lease, the receipts and the transition oracles are byte
for byte the same across the Python fixture and this one. The single difference
is one line of story frontmatter — `commands.source:
.devforgeai/stack.yaml#node` instead of `#python` — and the section that anchor
resolves to.

It does **not** prove:

- **compiled-stack support.** `compiled: true` and `commands.build` are in the
  contract and the `csharp` section of `stack.yaml` declares them, but no run
  here executes a build. The compiled path is specified, not exercised.
- **arbitrary Node-version compatibility.** The fixture requires Node 24 and
  the demo runs against the `node` on `PATH`. Its command uses
  `--test-isolation=none`, because Node 24's default process isolation reduces
  a failing file to one file-level JUnit case while the in-process form emits
  the three named cases the red oracle checks. No other major version is
  claimed; an absent runner reports `COULD_NOT_RUN` rather than skipping.
- **automatic stack detection.** No one sniffs the tree for a `package.json`.
  The story names its section by hand and the gate pins the whole file by hash.

## Contents

| Path | What it is |
|---|---|
| `package.json` | the manifest, `"type": "module"`, **no dependencies and no scripts** |
| `tinyapp/text.mjs` | the module under test, exporting nothing yet |
| `tests/` | an empty suite (`.gitkeep` only exists so git carries the directory) |
| `STORY-001.md` | a story v3 instance: the slugify story, three criteria, three tests |

`STORY-001.md`'s `write_fence` is `tinyapp/text.mjs` and `tests/text.test.mjs`;
its `test_plan` names `test_slugify_basic`, `test_slugify_unicode` and
`test_slugify_empty` in `tests/text.test.mjs`; its `commands` anchor is
`.devforgeai/stack.yaml#node` with `use: [test, lint]`. Its provenance and
context hashes are fixture placeholders, so the gate needs `--lenient` to open a
run against it: that flag downgrades `unresolvable-source` and nothing else.

`tinyapp/text.mjs` ships `export {};` rather than an empty file on purpose. A
red test imports the module namespace and asserts that `slugify` is a function,
so it fails on an assertion; a named import of a missing export would be a link
error, and the red oracle refuses a phase whose tests error rather than fail.

There is no `tests/text.test.mjs` here. Red writes it, inside the candidate
root, and the worker creates the parent directory as it writes — so a worktree
checkout that carries no `tests/` needs no placeholder.

## Nothing is installed, and nothing reaches the network

The `node` section of `.devforgeai/stack.yaml` names only what Node ships with:
`node --test --test-isolation=none --test-reporter=junit ...` for the suite and
`node --check` for the lint. `package_manager: npm` is declared so a reader knows which manifest syntax
the section's `extractors` speak; **no command key names `npm`, `npx`, `yarn`,
`pnpm`, `curl`, `wget` or `git`**, and the demo asserts that after every run,
together with the absence of `node_modules/`, `package-lock.json`,
`npm-shrinkwrap.json` and `.npmrc`, and a canonical tree whose only changed
paths are the two write-fence files and the sequencer's own published reports.

`packages.allow` and `packages.deny` are both empty, which is a statement rather
than a shrug: there is no dependency to allow or deny. `forbidden_imports`
carries one example rule — `require(` is refused under `tinyapp/**`, because the
project mandates ES modules — so the source-level ban is exercised and not just
declared.

`node --check` takes a **single** path and silently ignores extra arguments
(verified). The lint key therefore names `tinyapp/text.mjs` only; listing the
test file too would look like coverage the runner does not provide.

## What a run does to this tree

The same as the Python fixture: nothing, until the run is promoted. See
`../dev-tdd/README.md`, section "What a run does to this tree" — the candidate
root, the checkpoints, the promotion moment and the layout of
`.devforgeai/work/STORY-001/` are identical here, with `tinyapp/text.mjs` in
place of `tinyapp/text.py`.

`git init` the scratch copy and commit before `phase start` to see worktree
mode. `demo_sequencer.sh` runs this fixture in both modes.

## No overlays

`../dev-tdd/overlays/` has none here. The eval prompts are written against the
Python fixture; this tree exists to show the workflow is language-neutral, not
to double the eval matrix.
