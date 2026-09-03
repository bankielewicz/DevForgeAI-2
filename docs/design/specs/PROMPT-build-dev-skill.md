# Cold-session prompt: build the `dev` skill from SKILL-SPEC-001

Paste everything between the rules into a fresh Claude Code session started at the DevForgeAI repository root (`cd ~/Projects/DevForgeAI && claude`). The session needs the `skill-creator` plugin (`/skill-creator:skill-creator`) and nothing else.

---

Use `/skill-creator:skill-creator` to build the DevForgeAI `dev` skill from the specification at `docs/design/specs/SKILL-SPEC-001-dev.md`.

Read that specification in full before doing anything. Its section 0 replaces skill-creator's interview: do not ask me any Capture Intent or Interview question, do not ask me to approve test prompts or trigger queries, and do not wait for review between stages. Sections 1 to 14 pre-answer everything. If the spec is silent, contradictory or leaves a decision to you, stop before writing any skill file and end with a list titled `SPEC GAPS` naming each section and question.

Parameters:
- Output directory: `./out` (create `./out/dev/`; write nowhere else except the `dev-workspace/` sibling that eval runs need).
- Eval mode: `quick`, as section 0 rule 5 defines it. Run eval executions and the grader as foreground Agent-tool subagents and do not end your turn until every `grading.json` exists.
- Variant: `dev` (the plain variant). Use the `dev` worker contracts from section 7e; do not install the `dev-tdd` bodies.

Fidelity rules that override skill-creator's defaults:
1. `SKILL.md` frontmatter is exactly the six Agent Skills fields: `name`, `description`, `compatibility`, `allowed-tools`, `metadata`, and optionally `license`. Take `description` verbatim from section 3, `compatibility` and `allowed-tools` verbatim from section 11, and `metadata` verbatim from section 12. Put `provenance` under `metadata`, never at the top level. No angle brackets anywhere in the frontmatter.
2. The `SKILL.md` body has exactly four sections in this order: `## Identity`, `## Phases`, `## Dispatch Loop`, `## Handoff`, and stays under 500 lines. `## Identity` opens with these two sentences before any persona text: "This skill never writes a file and never advances a phase. The devforgeai sequencer does both; a worker returns a receipt, not a result." The dispatch loop is section 7a; the handoff table is section 7f.
3. In the dispatch loop, every dispatch names the exact subagent to invoke by its agent name: `red_dev`, `green_dev`, `refactor_dev`, `smoke_qa`, `dev_critic`. Never "a worker" or "the appropriate agent". The prompt handed to a worker contains only the story id, the `devforgeai status` block pasted verbatim, and one line naming the phase. Nothing is paraphrased from the story into the prompt.
4. `references/<phase>.md` is section 7d verbatim, one file per phase (`red`, `green`, `refactor`, `smoke`, `review`), plus `references/envelope.md` from section 6. `assets/dev-notes.md` is the dev-notes template. No `scripts/` directory. No `README.md` inside `out/dev/`.
5. `agents/<role>.md` is the section 7e contract for each of the five workers, framed with the four sections `templates/agent-md.md` fixes: `## Job`, `## Inputs`, `## Rules`, `## Receipt`. Each file's frontmatter carries `name`, `description`, `tools` and `writes` exactly as section 7g specifies. Producer bodies lead with the job they do; they never contain the phrase "you do not write". Do not write `{{candidate.root}}` or `{{run}}` literals into a body; say "the candidate root named in your dispatch brief" and "the run id named in your dispatch brief", because the SubagentStart hook injects those values.
6. Do not add steps, tools, hooks, commands or behaviours the spec does not name. The Bash grammar of the skill is exactly the five forms in section 7a. Hook definitions are not part of this skill; `init` installs them.

Context you should know but must not act on: this spec was exercised live on 2026-09-03 with a hand-written stand-in skill of the same shape (`~/Projects/dfai-proof/.claude/skills/dev/SKILL.md`) and the loop ran end to end: five workers, five checkpoints, promotion. You may read that file as a form reference for the four-section body. Do not copy its `metadata.version`; use section 12's.

When the skill and evals are written, run the acceptance checks in section 14 and paste their output verbatim. Then report, in this order: the `SPEC GAPS` list if any (and stop there), otherwise the tree of `out/dev/`, the line count of `SKILL.md`, the frontmatter keys, the pass/fail per expectation from every `grading.json`, and one line per deviation from the spec you had to make with the reason. Do not install the skill anywhere and do not commit.

---

## After the cold session reports

1. If it ended with `SPEC GAPS`, fix the spec, bump nothing, re-run this prompt.
2. Otherwise diff `out/dev/SKILL.md` against `~/Projects/dfai-proof/.claude/skills/dev/SKILL.md`; the generated skill must not be weaker than the stand-in on rules 2 and 3 above.
3. Second live proof: replace the stand-in in `~/Projects/dfai-proof/.claude/skills/dev/` with `out/dev/` (the `agents/` files go to `.claude/agents/`), reset the story, run `/dev STORY-001 --lenient` there, and collect.
4. Placement into `framework/skills/dev/` and `providers/claude/skills/dev/` is a manifest decision for the layout owner; do not move `out/` into the tree without it.
