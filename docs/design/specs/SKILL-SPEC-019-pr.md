---
template: skill-spec
template_version: 1
id: SKILL-SPEC-019
skill_name: pr
target: both
status: approved
author: Codex
date: 2026-09-04
depends_on:
  - source: docs/design/02-skill-roster.md#per-skill-detail
    hash: sha256:9fa52d566abd7ca28a7186afe36047b4c151820a7657b5bda864bf374056d9ad
    excerpt: "pr is explicit-only, prepares a checked external packet, and never publishes it."
  - source: docs/design/05-subagent-sets.md#sets-per-skill
    hash: sha256:2bb8ba434c56127d48d09179d742bf0f2f284f18363e7c2e911b1f2211ba3a7e
    excerpt: "pr uses pr_drafter as producer and pr_critic as judge."
  - source: docs/design/10-sequencer-and-contracts.md#4-per-skill-phase-registry
    hash: sha256:ac18004be37ef017e4d4abf8c6303e096d64dbbc0ae0c37e6288230473caaf66
    excerpt: "pr is a range-kind run with draft and critique phases."
  - source: docs/design/14-hosted-verification-and-pr.md#2-pr-invocation-and-exact-range-gate
    hash: sha256:b5472cb30a6dfec5c4c6862fdb6c551a5219cfe9a48dae69b0b6a96121a6fbea
    excerpt: "The gate binds the run to two full commit IDs and repository identity."
---

# Skill Specification: pr

This specification completely determines the `pr` skill. It prepares an
independently criticised pull-request packet for one exact committed Git range.
It does not publish that packet or grant a provider GitHub authority.

## 0. Generator instructions

Build `out/pr/` from this approved specification without interviewing. In quick
mode, write the three eval definitions from section 10 and run them in
foreground provider sessions. Stop without output if any required contract is
missing or contradictory. Use the description and worker contracts below
verbatim. Run every acceptance command in section 14 before reporting.

Cold-session prompt:

```
Use skill-creator to build docs/design/specs/SKILL-SPEC-019-pr.md into out/pr.
Do not ask questions. Eval mode: quick.
```

## 1. Identity

| Field | Value |
|---|---|
| name | `pr` |
| title | Pull Request Preparation |
| purpose | Prepare and independently criticise a GitHub pull-request request for one exact committed range without publishing it. |
| category | devforgeai-phase |
| version | 1.0.0 |

## 2. Problem and requirements

Without this skill, the primary agent can summarise an unpinned working tree,
omit failed checks, claim validation from filenames, or use its GitHub
credentials while preparing the request.

| ID | Kind | Requirement |
|---|---|---|
| R1 | explicit | Accept only `/pr --base` and `--head` with full lower-case 40-hex commit IDs, plus optional `--draft`. |
| R2 | explicit | Use a cold producer and separate cold judge so authoring and acceptance do not share reasoning context. |
| R3 | explicit | Save accepted title, body, GitHub request, and schema-valid packet under the run output directory. |
| R4 | explicit | Leave push, API submission, merge, release, and install to the human. |
| R5 | implicit | Refuse a stale head, non-default base, unrelated range, detached or default branch, non-GitHub origin, empty diff, malformed artifact, or candidate drift. |
| R6 | implicit | Never promote the candidate root or copy generated PR files into the canonical Git tree. |
| R7 | discovered | A passing report filename is not proof; validated-skill and passing-QA types require committed pass frontmatter. |
| R8 | discovered | Automatic insertion after another skill needs a remote-default advancement rule and is outside this version. |

## 3. Description

```yaml
description: >
  Prepare a human-published GitHub pull request for one exact committed range.
  Use only when the user explicitly invokes pr with full base and head commit
  IDs. Dispatch a cold drafter and a separate read-only critic, then persist a
  checked title, body, request, and digest-bound packet without pushing or
  calling GitHub. Do NOT use for code review, QA, merging, releasing, or
  installing; use review, qa, or the human-owned publication process instead.
```

Character count: 421 / 1024.

## 4. Trigger set

```json
[
  {"query":"/pr --base 1111111111111111111111111111111111111111 --head 2222222222222222222222222222222222222222","should_trigger":true},
  {"query":"/pr --base aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa --head bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb --draft","should_trigger":true},
  {"query":"$pr --base 0123456789abcdef0123456789abcdef01234567 --head 89abcdef0123456789abcdef0123456789abcdef","should_trigger":true},
  {"query":"open a PR for whatever I changed","should_trigger":false},
  {"query":"review STORY-001 before a pull request","should_trigger":false},
  {"query":"/pr --base main --head HEAD","should_trigger":false},
  {"query":"merge the current pull request","should_trigger":false},
  {"query":"release and install DevForge","should_trigger":false}
]
```

## 5. Use cases

### UC-1: Valid exact range

- User says the first positive trigger.
- The adapter opens `pr` with the supplied range. The gate proves repository
  identity and range state. The drafter writes the two fixed files, the critic
  returns a passing receipt, and the sequencer persists the four outputs.
- Result: state is `complete_external`; the candidate is gone; the handoff asks
  the human to publish the saved request.

### UC-2: Default branch advanced

- User supplies the earlier default tip as base after `origin/HEAD` moved.
- The exact-range gate returns `PR_RANGE` before candidate creation.
- Result: no run or output exists; the user chooses current pins and invokes a
  new run.

### UC-3: Unsupported claim

- The draft labels a skill validated based only on a changed report filename.
- The critic returns `fail` with `next: draft`; the sequencer rewinds.
- Result: the producer removes or substantiates the claim before completion.

## 6. Inputs and outputs

### Inputs

| Input | Format | Example | Required |
|---|---|---|---|
| base | full lower-case Git commit ID | forty `1` characters | yes |
| head | full lower-case Git commit ID | forty `2` characters | yes |
| draft | boolean flag | `--draft` | no |
| repository state | local Git objects, named topic branch, `origin`, remote default ref | current checkout | yes |
| continuation | the canonical next action recorded before the run | `/status` | yes |

### Outputs

| Output | Format | Location | Contract |
|---|---|---|---|
| title | UTF-8 text | `.devforgeai/work/pr-*/output/title.txt` | one trimmed line, at most 72 characters |
| body | Markdown | `.devforgeai/work/pr-*/output/body.md` | Summary, Governing artifacts, Changes, Verification, Limits, Human publication; both pins; no unresolved placeholder |
| request | JSON | `.devforgeai/work/pr-*/output/pr-request.json` | GitHub request fields; human submits it |
| packet | JSON | `.devforgeai/work/pr-*/output/pr-packet.json` | `schemas/devforgeai/v1/pr-packet.schema.json` |

The candidate paths are exactly `pr-artifacts/title.txt` and
`pr-artifacts/body.md`. The sequencer, not a worker, creates the request and
packet and copies the accepted text into `output/`.

## 7. Procedure

1. Parse the explicit flags and call `devforgeai phase start pr BASE..HEAD`,
   appending `--draft` only when supplied.
2. Print the refusal unchanged if the exact-range gate fails. Do not infer new
   pins or retry with branch names.
3. Read `devforgeai status` and dispatch the named current worker with only the
   run ID, phase, and status block.
4. Continue dispatching while the sequencer keeps the run active. Never read or
   rewrite the title, body, range source, or worker findings in the primary
   window.
5. Print the sequencer-rendered handoff verbatim after `complete_external`.

| # | Sub-phase | Performed by | Isolation |
|---|---|---|---|
| 0 | Gate and Slice | sequencer at phase start | not applicable |
| 1 | draft | `pr_drafter` | required |
| 2 | critique | `pr_critic` | required |
| 3 | Record and Handoff | sequencer at phase next | not applicable |

`pr_drafter` contract:

```yaml
name: pr_drafter
writes: candidate
responsibility: Write a faithful title and structured body for only the pinned committed range.
inputs: [range context, committed diff, committed verification and governance artifacts]
outputs: [pr-artifacts/title.txt, pr-artifacts/body.md]
must_not:
  - read or describe changes outside the pinned range
  - claim validation, QA, or acceptance without committed evidence
  - push, call GitHub, merge, release, install, or read secrets
  - write outside the candidate root or the two fixed paths
tools: [Read, Grep, Glob, Edit, Write, Bash]
isolation: required
returns: devforgeai.worker-result/v1
```

`pr_critic` contract:

```yaml
name: pr_critic
writes: none
responsibility: Judge range fidelity, evidence claims, risks, publication language, and continuation without editing the draft.
inputs: [range context, committed diff, pr-artifacts/title.txt, pr-artifacts/body.md]
outputs: []
must_not:
  - write any file anywhere
  - repair or paraphrase the draft
  - push, call GitHub, merge, release, install, or read secrets
tools: [Read, Grep, Glob, Bash]
isolation: required
returns: devforgeai.worker-result/v1
```

Handoff outcomes:

| Outcome | Next |
|---|---|
| packet complete | human executes the rendered push and saved request, then the saved continuation |
| range refusal | correct the named repository or pin defect and invoke a new exact range |
| worker failure within attempts | sequencer retries or rewinds; primary dispatches the named worker |
| attempts exhausted or provider failure | inspect the preserved evidence and follow the sequencer repair route |

## 8. Bundled resources

```
pr/SKILL.md
  agents/pr_drafter.md
  agents/pr_critic.md
  references/capability.md
  references/workflow.md
  references/envelope.md
```

The neutral sources are `framework/skills/pr/capability.md` and `workflow.md`.
The install manifest derives each provider's `references/` copies. The skill has
no script, asset, template, GitHub client, credential, or hook of its own.

## 9. Gotchas and edge cases

| Situation | Refusal or risk | Required behavior |
|---|---|---|
| abbreviated pin or branch token | range is ambiguous or movable | usage refusal before a run |
| checkout head differs | packet would describe different bytes | `PR_RANGE`; no candidate |
| base is not current remote default | stale or caller-selected comparison | `PR_RANGE`; new human-supplied pins |
| changed report says pass only by filename | unsupported quality claim | omit the type unless committed frontmatter proves pass |
| worker writes an extra file | candidate escape | `PR_DRAFT_PATHS`; retry |
| title or body malformed | publication packet is not deterministic | `PR_TITLE` or `PR_BODY`; retry |
| Git state changes during work | source basis moved | revalidate at completion and refuse |
| completion succeeds | human may mistake packet for publication | state says `complete_external`; handoff says publication remains human |

## 10. Success criteria and test cases

Success requires every positive trigger to select only on explicit invocation,
every invalid range to fail before candidate creation, exact candidate fencing,
independent critique, schema-valid output with matching digests, removed
candidate, unchanged canonical source tree, and no network or Git mutation.

```json
{
  "skill_name":"pr",
  "evals":[
    {"id":1,"prompt":"/pr with the fixture's exact base and head pins","expected_output":"complete external packet","expectations":["range gate passes","drafter and critic are distinct","four output artifacts exist and validate","candidate is absent","no push or API call occurs"]},
    {"id":2,"prompt":"/pr with an unrelated base and the fixture head","expected_output":"range refusal","expectations":["exit is nonzero","PR_RANGE is named","no run or candidate exists"]},
    {"id":3,"prompt":"/pr where the first draft contains an unsupported passing-QA claim","expected_output":"critic rewind then corrected packet","expectations":["critic does not write","draft rewinds","final packet omits or proves the claim"]}
  ]
}
```

## 11. Dependencies and compatibility

| Kind | Value |
|---|---|
| Primary tools | `Agent` and the closed `devforgeai` grammar only |
| Producer tools | `Read`, `Grep`, `Glob`, `Edit`, `Write`, `Bash` under hooks |
| Judge tools | `Read`, `Grep`, `Glob`, `Bash`; no write tool |
| Runtime | Python 3.11 or newer, Git with `origin/HEAD`, and the existing sequencer/hook runtime |
| Schemas | worker result, run, handoff, error taxonomy, and pr-packet v1 |
| Network | none during preparation; human publication is outside the skill |
| Other skills | no nested skill call; continuation is preserved, not invoked |

## 12. Targets

| Target | Install path | Invocation | Worker profiles |
|---|---|---|---|
| Claude | `.claude/skills/pr/` | `/pr --base FULL --head FULL [--draft]`; implicit disabled | `.claude/agents/pr-drafter.md`, `pr-critic.md` |
| Codex | `.agents/skills/pr/` | explicit `$pr` with the same flags; implicit disabled in `agents/openai.yaml` | `.codex/agents/pr-drafter.toml`, `pr-critic.toml` |

Both adapters share neutral semantics and differ only in provider metadata and
profile syntax. Neither contains credentials or a GitHub mutation tool.

## 13. Constraints

- The skill is explicit-only and uses full commit IDs.
- The primary window does not inspect source or author publication prose.
- One producer writes exactly two candidate files; one judge writes none.
- The sequencer is the only canonical state and output writer.
- Accepted output remains under `.devforgeai/work/`; no promotion occurs.
- Every external mutation remains a human step.
- Automatic governed-boundary routing is not claimed by this version.

## 14. Acceptance checks

```bash
PYTHONPATH=components/research-core/src python3 -m pytest tests/research/test_pr_skill.py -q
python3 docs/design/examples/hooks/run_conformance.py
python3 docs/design/specs/verify.py
python3 -m json.tool schemas/devforgeai/v1/pr-packet.schema.json >/dev/null
grep -l 'writes: candidate' providers/claude/agents/pr-drafter.md
grep -l 'writes: none' providers/claude/agents/pr-critic.md
grep -l 'allow_implicit_invocation: false' providers/codex/skills/pr/agents/openai.yaml
```

All commands must exit zero. Hosted or live provider proof is recorded
separately and must name the exact commit; generation success is not proof of
publication authority.

## 15. Provenance

| Source | Used for |
|---|---|
| `docs/design/02-skill-roster.md#per-skill-detail` | invocation, authority, cadence limitation |
| `docs/design/05-subagent-sets.md#sets-per-skill` | worker split |
| `docs/design/10-sequencer-and-contracts.md#4-per-skill-phase-registry` | phases, fence, state transition |
| `docs/design/14-hosted-verification-and-pr.md#2-pr-invocation-and-exact-range-gate` | exact range gate and external completion |
