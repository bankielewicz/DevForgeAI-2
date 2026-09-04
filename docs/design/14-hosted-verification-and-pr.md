# 14. Hosted verification and pull-request preparation

Status: implemented candidate, 2026-09-04. This document governs the advisory
GitHub workflow and the explicit `pr` skill. It does not grant either Claude or
Codex authority to push a branch, create a pull request, merge, publish a
release, write DevForge, use repository secrets, or install a protected binary.

## 1. Authority boundary

DevForgeAI prepares and verifies bytes. A human owns every GitHub mutation:
push the named branch, submit the saved request, choose draft status, merge, and
promote reviewed release bytes to the separate protected DevForge repository.
The workflow in `.github/workflows/pr-verify.yml` is advisory evidence. Branch
protection may later require its `required` job, but the workflow is not an
acceptance authority and cannot close CP-00 or claim that a staged DevForge
candidate is protected.

The future release lane belongs to a separately credentialed GitHub App in the
DevForge repository. No personal token, App key, deployment key, or release
secret is present in this repository or referenced by the advisory workflow.
Until that repository and App exist, release and installation remain human
operations outside DevForgeAI.

## 2. `pr` invocation and exact-range gate

The only invocation is:

```
/pr --base <40-lowercase-hex> --head <40-lowercase-hex> [--draft]
```

Claude maps it to `devforgeai phase start pr <base>..<head> [--draft]`.
Codex uses the same provider-neutral operation. Implicit invocation is disabled
on both providers. No abbreviated object name, branch name, `HEAD`, merge-base,
caller-selected alternate remote, or defaulted range is accepted.

Before opening a run, the sequencer proves all of the following:

1. both objects resolve to exactly the supplied commit IDs;
2. the checkout's current commit equals `head`;
3. `base` is an ancestor of `head` and the committed diff is non-empty;
4. the current branch is named, is not the remote default branch, and its tip is
   `head`;
5. `refs/remotes/origin/HEAD` resolves to `base`;
6. `origin` is a GitHub HTTPS or SSH repository URL.

Failure is a refusal before candidate creation. Rewriting a branch, advancing
the default branch, or changing either pin requires a new invocation; the run
does not silently rebase its evidence range.

## 3. Run and worker contract

The run ID is `pr-<base-first-12>-<head-first-12>`. The write fence contains
exactly `pr-artifacts/title.txt` and `pr-artifacts/body.md` inside the candidate
root. The two phases are:

| Phase | Worker | Role | Writes |
|---|---|---|---|
| `draft` | `pr_drafter` | inspect only the pinned committed range and prepare the title and body | the two fenced files |
| `critique` | `pr_critic` | judge range fidelity, unsupported claims, missing risk, and unverifiable test language | none |

The critic returns findings in its receipt. A failed critique rewinds to
`draft`; no third worker, hidden authoring phase, or primary-window rewrite is
permitted. The primary window reads only sequencer state and receipts, never
the changed source or generated body.

The per-run record validates against `schemas/devforgeai/v2/run.schema.json`,
and its PR refusals and `complete_external` state use
`framework/contracts/error-taxonomy-v2.yaml`. These additive version-2 staging
contracts leave the open CP-00 version-1 promotion candidate byte-identical.

The title is one non-empty trimmed line of at most 72 characters. The body has
exactly one of these headings, in this order: `## Summary`, `## Governing
artifacts`, `## Changes`, `## Verification`, `## Limits`, and `## Human
publication`. It contains both full commit IDs and no unresolved placeholder.

## 4. External completion

A passing critique does not promote the candidate root. The sequencer:

1. re-runs the exact-range gate;
2. copies the title and body byte-for-byte to
   `.devforgeai/work/<run>/output/`;
3. writes `pr-request.json`, containing the GitHub owner, repository, full head
   branch, default base branch, title, body, and draft boolean;
4. writes `pr-packet.json` conforming to
   `schemas/devforgeai/v1/pr-packet.schema.json`, with SHA-256 for both saved
   artifacts and the request;
5. removes the candidate root and records run state `complete_external`;
6. renders a `REQUIRE_HUMAN` handoff naming an explicit `git push` followed by
   the saved `gh api` request and then the continuation captured at run start.

The sequencer executes neither publication command. No generated PR file is
copied into the canonical Git tree. `complete_external` means the external
packet is complete, not that a GitHub pull request exists.

The type list in `pr-packet.json` is closed: `architecture`, `analyzed_plan`,
`validated_skill`, `passing_qa`, `governance_amendment`, and `implementation`.
Path inspection may identify architecture, plan, governance, and implementation
changes. `validated_skill` and `passing_qa` require a committed pass report;
their presence is never inferred from a filename alone.

## 5. Cadence

`pr` is required by project policy at these governed boundaries: accepted
architecture, analyzed plan, validated generated skill, passing QA, and an
accepted governance amendment. Brainstorm, Research, and PM may request a PR
when a human wants an independently reviewable checkpoint.

This candidate implements explicit `/pr` preparation. It does not yet rewrite
the preceding skill's handoff into `/pr`, because a safe automatic rewrite also
needs a deterministic rule for a remote default branch that advances between
the preceding run and PR preparation. Until that rule has a specification and
hostile tests, the human invokes `/pr` with the current exact pins. This is a
declared enforcement limitation, not an implicit model choice.

## 6. Advisory GitHub workflow

The workflow triggers only on `pull_request` and pushes to `main`. It has
repository permission `contents: read`, checks out the exact event head with
credentials disabled, references actions by full commit SHA, installs no hook
or protected release, and uses no secret. `pull_request_target` is forbidden.

| Job | Deterministic checks |
|---|---|
| `research` | locked Python environment; complete `tests/research` suite |
| `contracts` | design/provenance verifier, Claude hook POC tests, wheel build, whitespace check |
| `sequencer` | enforcement conformance and copy/worktree demo with pinned Python and Node |
| `release_candidate` | corrected PR 22 Rust launcher with locked Cargo graph, then staged release-layout tests; no install |
| `required` | runs even after a failed or cancelled dependency and succeeds only when all four lanes succeeded |

The environment is locked by committed `uv.lock`; Python is `3.12.3`, Node is
`24.18.0`, uv is `0.11.26`, and Rust is `1.94.0`. Wheel builds use the
lock-pinned setuptools `80.9.0` without an isolated build resolver. The release-candidate lane
requires the launcher's `Cargo.toml`, `Cargo.lock`, `BUILD-DIGEST.txt`, and the
release-layout Python tests. On the current base those files are absent because the corrected PR 22
has not merged, so that lane must fail. It must not skip, downgrade, or report
green until this branch is rebased onto the accepted PR 22 merge.

Hosted green means only that these commands passed on GitHub's runner at the
recorded commit. It does not replace live Claude/Codex probes, a root-owned
DevForge installation, human acceptance, or evidence custody required by the
gap-closure plan.

## 7. Acceptance checks

This feature is locally implemented only when all commands that exist at the
base pass:

```
PYTHONPATH=components/research-core/src python3 -m pytest tests/research -q
python3 docs/design/specs/verify.py
python3 docs/design/examples/hooks/run_conformance.py
bash docs/design/examples/hooks/demo_sequencer.sh
python3 components/hook-runtime/reference/claude-python/tests/run_tests.py
uv build
git diff --check
```

The hosted implementation is proven only after the corrected PR 22 merge is in
the branch and the `required` job reports success for that exact commit. A
local pass, skipped job, unavailable runner, or green run at another commit is
not that proof.
