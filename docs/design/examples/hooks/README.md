# Runnable draft: sequencer, dispatcher and provider configuration

Everything here runs on Python 3 and the standard library plus PyYAML (and
`jsonschema` where a proposal is schema-checked). It is a draft of the write
model in `10-sequencer-and-contracts.md` sections 5 and 12 and
`09-hook-dispatcher.md`, not a product: it exists so the design can be executed
and refuted rather than only read.

| File | What it is |
|---|---|
| `devforgeai.py` | the sequencer: gates, candidate roots, checkpoints, receipts, oracles, promotion |
| `dispatch.py` | the hook dispatcher, one script for both providers: one event in, one decision out |
| `policy.py` | the shared registry and path policy both of the above read; it writes nothing |
| `run_conformance.py` | the allow/deny table: dispatcher rows, grammar rows, end-to-end backstops |
| `demo_sequencer.sh` | STORY-001 walked through the dev skill four times: the Python and Node fixtures, each in copy mode and in worktree mode |
| `settings.claude.json`, `hooks.codex.json`, `config.codex.toml` | the provider fragments an installed project carries |
| `requirements.codex.toml` | post-MVP: the administrator-managed Codex shape, read by nothing here |
| `agents/claude/*.md`, `agents/*.toml` | the five dev workers, in each provider's format |
| `fixtures/.devforgeai/` | a documented `state.yaml`, `stack.yaml` and `work/<run>/run.yaml` |

## Run it

```
bash demo_sequencer.sh        # four full runs; ends
                              # "DEMO OK: python copy/worktree green, node copy/worktree green"
python3 run_conformance.py    # ends "<n>/<n> rows hold"; exit 0 means every row held
```

Both write only to scratch directories under `$TMPDIR` (`/tmp` by default).

## The demo, and the one claim it supports

`demo_sequencer.sh` runs the same story through the dev skill four times: the
Python fixture (`../fixtures/dev-tdd/`, the control, unchanged) and the Node
fixture (`../fixtures/dev-tdd-node/`), each in copy mode and in worktree mode.
Each run goes gate → red → green (rewind) → red → green → refactor → smoke →
review → `ready_to_promote` → `devforgeai promote`, and each asserts, not just
prints:

- the story's three `test_plan` names appear in the JUnit file the section's
  `junit_path` points at, all `failed` at red and all `passed` at green and
  refactor — read straight out of the XML, keyed by `testcase@name`;
- `run.yaml#red_hashes` is unchanged from the successful red through green and
  through refactor, so the frozen-tests rule is observed rather than assumed;
- lint passed — both as the refactor transition advancing with the `lint` key
  authorised, and by re-running the section's resolved `lint` argv against the
  promoted canonical tree;
- the promoted refactored implementation is in the canonical tree, the handoff
  outcome is `pass` and the run status is `promoted`;
- **no undeclared output**: a file-by-file sha256 snapshot of the project taken
  before the gate and again after promotion, whose only delta is the story's two
  write-fence files plus the phase reports promotion publishes under
  `docs/reports/`. For the Node runs that also means no `node_modules/`, no
  `package-lock.json`, no `npm-shrinkwrap.json`, no `.npmrc` — checked
  explicitly — and no argv anywhere in the resolved section naming a package
  manager or a fetcher.

The two fixtures differ in one line of story frontmatter: `commands.source` is
`.devforgeai/stack.yaml#python` in one and `#node` in the other. The claim the
demo supports is exactly that: **two interpreted ecosystems run through the same
stack-selected workflow.** It does not prove compiled-stack support (the
`csharp` section is declared and never executed here), arbitrary Node-version
compatibility (the runs use whatever `node` is on `PATH`), or automatic stack
detection (each story names its section by hand and the gate pins the file by
hash). A missing runner is reported as `COULD_NOT_RUN`, naming it, with a
non-zero exit — never a silent skip.

## The model in one paragraph

A run gets one candidate root, created by the sequencer at `phase start` and
owned by it until promotion or abandonment: a git worktree on
`devforgeai/<run>` when the project is a repository, a tree copy otherwise.
Producers write there with Edit and Write while they hold the run's write lease,
which is bound at SubagentStart — the only identity-bearing pre-write event on
either provider — and released at `ingest-result`. Judges hold no lease and
write only under `.devforgeai/work/<run>/evidence/<agent>/`. A worker's final
message is one `devforgeai.worker-result/v1` receipt naming what it claims to
have changed; the sequencer derives the real change set from the checkpoint diff,
refuses anything unclaimed or outside the fence, runs the transition oracle with
cwd = the root, writes the checkpoint and advances. The canonical checkout the
user is looking at changes at exactly one moment: `devforgeai promote <run>`.

## Reading a scratch run

`.devforgeai/state.yaml` (canonical, tracked) holds story statuses and one row
per run. `.devforgeai/work/<run>/run.yaml` (gitignored) holds everything
per-phase: phase, fence, test paths, granted keys, attempts, lease, candidate.
A candidate root is recognised by `<root>/.devforgeai/candidate`, a two-line
marker naming the run and the canonical path; that marker, not "the nearest
`.devforgeai/`", is what tells a root from the project, because a root carries a
copy of the project's `.devforgeai/` too.

## Deliberate limits

The dispatcher trusts the provider's event fields, the sequencer trusts its own
filesystem, and neither sandboxes anything: the OS sandbox is post-MVP. Copy
mode has no rebase, so a canonical tree that moved during a run returns
`STALE_BASE` and asks for a human. `run_conformance.py` names the invariants
that are actually enforced; anything not in that table is aspiration, not
behaviour.

## Known gaps against `10-sequencer-and-contracts.md`

- Fix mode (`run.yaml#fix_report`, section 11): the draft applies the full required-fail red rule in every dev run and does not narrow it to the report's failed criteria.
- Conformance covers the dev skill end to end and single rows for the other registries; the qa and review skills are not run end to end by `demo_sequencer.sh`.

