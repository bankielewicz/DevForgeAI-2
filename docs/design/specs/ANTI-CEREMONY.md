# Anti-Ceremony Rules

Status: normative for wave 2, 2026-09-02. Read this before writing a spec's section 7 or
any `agents/<role>.md` body. It is a hard rule, not advice.

## 1. Definition

**Ceremonial** — an instruction whose compliance no script and no hook can check.

An instruction is ceremonial when there is no exit code, no file on disk, no hash
comparison, and no oracle classification that distinguishes a run that followed it from a
run that ignored it. Whether the model complied can then only be asserted, by the model,
about itself.

Every ceremonial instruction costs the same as a real one: it occupies the primary
window's context, it competes for the agent's attention with the instructions that do
matter, and it teaches a reader that compliance is a matter of good intentions. Worse, it
is indistinguishable in tone from an enforced instruction, so a reader cannot tell which
half of the document is real.

The framework already has three places where an instruction becomes checkable: a
deterministic gate at `devforgeai phase start`, a fence plus a `PreToolUse` deny, and a
transition oracle at `devforgeai phase next`. Every instruction worth keeping belongs to
one of those three. An instruction that belongs to none of them is deleted.

A short test: **would this run look different if the model ignored the sentence?** If the
answer requires reading the model's self-report, the sentence is ceremonial.

## 2. The conversion table

Each row names a phrase authors reach for, the mechanism that already does the work, and
what the spec writes instead. The left column must not appear in a specification, a
`SKILL.md`, a reference file, or an agent body.

| Ceremonial instruction | Mechanism that replaces it | What the spec writes instead |
|---|---|---|
| "Verify the story is valid before proceeding." "Confirm prerequisites are met." | The deterministic gate inlined in `devforgeai phase start` (`01-skill-anatomy.md`, sub-phase 0; `10-sequencer-and-contracts.md` sections 3.2 and 3.3). It refuses and exits 1 with the defect list; no run opens. | Nothing in the procedure. The gate's checks are one row of section 7's evidence table, in the `deterministic gate check` column. |
| "Update the state file." "Record that this phase is complete." "Mark the story in progress." | The sequencer. It is the only writer of canonical `.devforgeai/**`, at `phase start`, at each transition, at promotion, and at `phase fail`. | Nothing. The spec states that the phase's worker returns a receipt and the sequencer records `<phase>-result.json` and updates `state.yaml`. |
| "Print the handoff." "Summarise what happened and what to do next." | `devforgeai phase next` writes `.devforgeai/work/<run>/handoff.json`; the printed block is that file's rendering, and rule 8 in `10-sequencer-and-contracts.md` section 6 says the renderer adds nothing. | The spec's handoff table (section 7e), which is the `handoff.outcomes` block the sequencer selects a row from. The procedure says only that the primary window prints the block the sequencer rendered. |
| "Stay in scope." "Only touch the files this story names." "Do not edit unrelated code." | The candidate root plus `write_fence` in `.devforgeai/work/<run>/run.yaml`: a `PreToolUse` deny for any write whose canonical path is outside the root or outside the fence, then a re-check at `ingest-result` against the checkpoint diff, which refuses any changed path that is unclaimed or out of fence. | The fence itself, listed in section 6 or taken from the story, plus a `must_not` line in the worker contract. No exhortation. |
| "Make sure the tests pass." "Confirm the build is green." | The transition oracle (`10-sequencer-and-contracts.md` section 5.4), which brokers the command itself from the hash-pinned `stack.yaml` section, runs it inside the candidate root, and reads per-test outcomes from the JUnit file. A producer may call `devforgeai run <key>` for its own feedback, but its claim that tests pass is not why a phase advances. | The oracle name and its one passing condition, in section 7's evidence table. The worker contract's `must_not` forbids raw stack commands, so the only way to a runner is the granted key. |
| Restating the story's goal, acceptance criteria, constitution text, or PRD requirements into a worker's prompt. | The context bundle. The worker reads paths; the primary window passes paths and ids, never content (`01-skill-anatomy.md`, primary-window contract). | A dispatch instruction of one line plus file paths. Section 7 says explicitly that the skill never pastes or paraphrases artifact content, objectives or acceptance criteria into a prompt. |
| `ALWAYS do X.` `NEVER do Y.` | Nothing enforces capitalisation. Where the rule is real it is a gate defect class, a fence, a `must_not` line, or an oracle condition. | The mechanism, named, with the reason. "Refactor may not edit tests; the `green` oracle compares every `test_paths` hash to `red_hashes` and fails the transition if one moved." |
| "Consider running the linter." "You may want to check the ADRs." | Nothing. An optional instruction has no failure mode and no gate. | Delete it, or make it a default. `best-practices.mdx` is explicit: provide defaults, not menus. If the linter must run, it is a `run_keys` entry and an oracle condition; if it must not, it is absent. |
| Self-attested checklists: `- [ ] Reviewed the constitution` `- [ ] Confirmed no regressions` | A checkbox the model ticks about itself is the failure mode `07-purpose-and-enforcement.md` section 2 names twice: "declares done because a file exists or a checkbox is ticked". | Either delete the item, or replace it with a numbered step whose result is a script exit code, a file the `document` oracle can see on disk, or an evidence row the critic phase's own oracle checks. |

## 3. Where the best-practice sources appear to disagree, and how they do not

Two sources authors are told to read recommend patterns that look ceremonial. They are not,
provided the distinction below is kept.

**Checklists.** `best-practices.mdx` recommends a progress checklist for multi-step
workflows, and every item in its example is a script invocation
(`run scripts/validate_fields.py`). A checklist whose every item is a command with an exit
code, or a file whose existence an oracle checks, is a procedure written as a list; keep
it. A checklist whose items are states of mind ("reviewed", "considered", "confirmed") is
the self-attested-checklist row above; delete it.

**Validation loops.** The same source recommends "do the work, run a validator, fix,
repeat". In DevForgeAI the validator is not the model's own script call: it is the
transition oracle, and the loop is the `max_attempts` map. A spec writes the oracle and the
attempt budget, not the loop's prose. Where a phase genuinely needs an in-worker check the
sequencer cannot perform, that check is a `scripts/` file with an exit code, named in
section 8, and its output is a file the receipt names in `evidence_refs`.

**`CRITICAL:` blocks.** The Anthropic guide, page 26, recommends putting critical
validations at the top and prefixing them. Its own advanced technique on the same page is
the correct one here: "for critical validations, consider bundling a script that performs
the checks programmatically rather than relying on language instructions. Code is
deterministic; language interpretation isn't." In this framework the script already exists
as the gate and the oracle. Do not add a `CRITICAL:` block that restates them; a reader who
follows the block and a reader who ignores it produce the same run.

**"Model laziness" encouragement** (guide, page 26: "Take your time", "Quality is more
important than speed"). The guide itself notes this belongs in a user prompt rather than in
`SKILL.md`. It is ceremonial by the definition in section 1. Do not write it.

## 4. Review checklist

Run this over your own spec's section 7 and over every `agents/<role>.md` body before you
report done. Each item is a search you perform, and each failure names its fix.

1. **Search for the ceremonial phrasings.** `verify`, `ensure`, `make sure`, `confirm
   that`, `be sure to`, `remember to`, `do not forget`, `consider`, `you may want to`,
   `as needed`, `where appropriate`. For each hit ask the section 1 test. Convert with the
   section 2 table, or delete.
2. **Search for capitalised absolutes.** `ALWAYS`, `NEVER`, `MUST NOT` in shouting form,
   `CRITICAL:`, `IMPORTANT:`. For each, name the gate defect class, fence, `must_not` line
   or oracle condition that carries the rule, and rewrite as that mechanism plus its
   reason. If no mechanism carries it, the rule is not enforced and the sentence says so
   or goes.
3. **Search for literal commands.** Any build, test, lint or format command written out —
   an executable name, a runner flag, a test path. A worker never receives one. Replace
   with a `stack.yaml` command key and the sequencer's brokered run.
4. **Search for state writes.** `write`, `update`, `append`, `record`, `save` with an
   object under canonical `.devforgeai/`. Only the sequencer writes there. A producer writes
   its artifacts inside the candidate root and claims their paths in the receipt; the run
   file, the evidence files, `state.yaml` and promotion are the sequencer's.
5. **Search for content restatement.** Any place a worker's `inputs` or a dispatch step
   quotes, summarises or paraphrases a goal, an acceptance criterion, a requirement, or a
   constitution rule. Replace with the path and the id.
6. **Check every evidence-table `deterministic gate check` cell.** It must name something a
   script does: a parse, a pattern match, a hash comparison, a path check, a policy scan, an
   exit code. A cell containing "the worker checks", "the critic verifies", or "the agent
   confirms" is a defect. If nothing deterministic checks it, write what is checked and
   record the gap in section 9.
7. **Check every `must_not` line.** Each must be a forbidden action a validation step or an
   oracle can catch — writing outside the candidate root or the fence, touching a test file
   from a code phase, adding a package outside the allowlist. A `writes: evidence` worker's list
   says "write anywhere but this run's evidence directory", a `writes: none` worker's says "write
   any file", and a `writes: candidate` worker's never says it does not write. "Do not hallucinate" and "do not exceed
   scope" are not actions; replace them with the fence, the `writes` mode, or the critic
   phase's own oracle row.
8. **Check every checklist you kept.** Every item resolves to a command with an exit code, a
   file an oracle sees on disk, or an `evidence_refs` target the receipt names. If an item resolves to none
   of those, delete the item.
9. **Ask the counterfactual, per paragraph.** Would this run look different if the model
   ignored this paragraph? If the only difference is what the model would say about itself,
   delete the paragraph. The content that survives is the content the skill is for.
