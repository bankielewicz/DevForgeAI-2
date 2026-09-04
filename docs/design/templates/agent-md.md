---
# == template header: read by the DevForgeAI gate; not copied into instances ==
template: agent-md
template_version: 1
accepts_versions: [1]
required_frontmatter: [name, description, tools, writes]
required_sections: ["## Job", "## Inputs", "## Rules", "## Receipt"]
id_pattern: "^[a-z][a-z0-9_]*$"
forbidden_text: ["TODO", "TBD", "{{", "}}", "<fill in>"]
# id_pattern allows underscores because it matches the canonical worker names in 10 section 4
#   (`red_dev`, `green_dev`), which a Codex custom-agent name and a Claude agent frontmatter name share.
# Extra instance keys beyond 11's four: `skill`, `responsibility`, `inputs`, `outputs`, `must_not`,
#   `isolation` and `returns` are the worker contract in 05-subagent-sets.md. skill-validator rejects an
#   agent file with no `responsibility`, `must_not` or `writes`, or with `tools` that do not match the
#   role `writes` declares (06-skill-specification.md section 14), so they are carried here rather than
#   left to the prose body.
# writes: `candidate` for a producer, `none` for a judge (05-subagent-sets.md). There is no third
#   value. It fixes `tools`: a producer declares [Read, Grep, Glob, Edit, Write, Bash]; a judge
#   declares [Read, Grep, Glob, Bash] and no write tool of any kind. A judge returns its evidence
#   as the receipt's `findings`, and the sequencer persists it to
#   .devforgeai/work/<run>/evidence/<agent>/findings.md.
# tools names tools only: a Claude Code subagent's `tools:` frontmatter accepts tool names and MCP
#   server patterns, never a command pattern, so the hook dispatcher is the only command-level
#   bound. A judge's Bash runs `devforgeai status` and the dispatcher's read-only command set
#   (cat cmp cut diff echo grep head jq ls pwd rg sha256sum tail test tr wc, plus read-only git
#   subcommands inside the root, invoked as `git -C <candidate.root> <subcommand>`) and nothing
#   else; a producer's additionally runs
#   `devforgeai run KEY` for its granted keys. The Bash bound is restated in the body's ## Rules.
# provenance: the skill-spec section 7 worker contract this was generated from (11 section 3).
# == instance frontmatter: fill every field ==
name: "{{canonical_worker_name}}"
description: "{{one sentence: what this worker is dispatched to do}}"
tools: [Read, Grep, Glob, Edit, Write, Bash]   # producer set; judges drop the write tools
writes: candidate           # candidate (producer) | none (judge)
skill: "{{skill-name}}"
responsibility: "{{one sentence, one job}}"
inputs:
  - "{{path or named artifact}}"
outputs:                    # written under the candidate root; claimed in the receipt
  - "{{path written}}"
must_not:                   # compiled into the agent prompt verbatim
  - "{{forbidden action}}"
  - write outside the candidate root or outside this phase's write fence
  - run a raw stack command, a git write, a package manager, or a network tool
isolation: required         # required | preferred
returns: devforgeai.worker-result/v1
provenance:
  - source: "docs/plan/{{slug}}/skill-specs/SKILL-SPEC-000.md#7-procedure"
    hash: sha256:{{64 hex}}
---

# {{canonical_worker_name}}

The body is four sections, in this order, and nothing else: job, inputs, rules,
receipt. It leads with the job and never tells a producer what it does not do
before it has said what it does.

`run` and the candidate root are not compile-time values and are never written
into an instance as placeholders. The dispatch prompt carries the
`devforgeai status` block — `run`, `candidate.root`, `phase`, `fence`,
`granted_keys` — and the body refers to those values by name, so one compiled
file serves every run.

## Job

One paragraph, opening with the verb.

A producer opens: "You write {{what}} inside the candidate root the status block
names, using Edit and Write. Run `devforgeai run <key>` for a granted key
whenever you need the tests. Finish with the receipt." Then what a good result
looks like and what it deliberately leaves to the next worker.

A judge opens: "You judge {{what}}. You write nothing: you hold no write tool,
and your evidence goes in the receipt's `findings`, which the sequencer saves for
the next worker to read. Finish with the receipt." Then what the verdict rests
on, and what belongs in `findings` rather than in `issues`.

## Inputs

One line per `inputs:` entry: what the worker reads and what it may assume about
it. Nothing outside this list is opened. Paths are relative to the candidate
root unless the line says otherwise.

## Rules

The `must_not:` list verbatim, then the few positive rules the mechanisms do not
already carry. A rule the fence, the oracle or the gate enforces is not repeated
here: name the mechanism once instead. Steps the sequencer already performs are
not instructions to this worker.

## Receipt

The `devforgeai.worker-result/v1` object this worker ends with: which statuses it
can return, what belongs in `claimed_paths` (every path it wrote under the
candidate root, and nothing it did not — a judge's is always empty), what belongs
in `evidence_refs` (a report inside the root, or an oracle output; never a
findings path), what belongs in `findings` (a judge only: its detailed evidence,
at most 16384 UTF-8 bytes, required on its receipt and forbidden on a producer's,
refused rather than truncated when larger), and what belongs in `note` rather
than in prose. A non-pass status carries an empty `claimed_paths`, and `issues[]`
stays the bounded routing summary even when `findings` is long.
