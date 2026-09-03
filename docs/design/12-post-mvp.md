# Post-MVP Roadmap

Status: roadmap, 2026-09-02. Every item here was removed from `00`-`09` or the templates because it cannot run in a Claude Code or Codex terminal on a Max plan. Nothing in this document is a precondition for running a skill. A skill specification that needs one of these names its entry ID under its section 11 as a deferred dependency; it must not gate on it.

| ID | Item | Rung served |
|---|---|---|
| PM-01 | Provider Conformance attestation as a run precondition | 2 |
| PM-02 | 200-trial provider conformance suites | 2 |
| PM-03 | Administrator-managed hook policy (`requirements.toml`) | 3 |
| PM-04 | Per-phase sandbox or container mounts | 3 |
| PM-05 | Token telemetry in `/status` | 1 |
| PM-06 | Full eval mode and the eval viewer | 2 |
| PM-07 | Any provider API use | — |
| PM-08 | Legacy DevForgeAI document migration | 2 |
| PM-09 | Monorepo `stack.yaml` | 2 |
| PM-10 | Rung 4 repository enforcement | 4 |
| PM-11 | Clean detached verification worktree for `qa` and `review` | 3 |
| PM-12 | Automated integration run for overlapping fences and copy-mode `STALE_BASE` | 3 |
| PM-13 | Pull-request and merge-queue promotion | 4 |

---

## PM-01

**Provider Conformance attestation as a run precondition**

| | |
|---|---|
| What | A signed, versioned statement that a named provider surface at an exact installed version, plus an exact adapter digest, passed a conformance suite; required before a skill that declares `isolation: required` may install or run. |
| Why deferred | A Max-plan terminal cannot produce or verify one. There is no evaluator identity, signature, issuer registry, or governance authority in this repository, and no way to authenticate a submitted attestation from inside a terminal session. |
| Unblock condition | An accepted attestation contract with a named issuer, a signing key, and a verifier that runs offline; plus a release process outside the terminal that can refuse installation. |
| Rung served | 2 (deterministic validators inside the pipeline). |
| Statements moved here | `02:165`; `04:107-108`, `04:128`, `04:138-146`; `06:17`, `06:59`, `06:87`, `06:93-94`, `06:138`; `templates/skill-spec.md:192`, `:259`, `:300`. |

Until PM-01 lands: required isolation is a declaration compiled into the target profile, and a generated adapter is a candidate that a human installs. No document may state that an attestation is checked.

## PM-02

**200-trial provider conformance suites**

| | |
|---|---|
| What | `provider-conformance-attestation/v1` const-binding the `devforgeai-research-provider-runtime` v1.0.0 suite, its manifest digest, and its ordered 20-fixture set: five fresh enabled and five fresh disabled trials per fixture, 200 passing trials, session IDs unique across the attestation. Offline Core acceptance is bound to a separate one-fixture suite and one `NOT_APPLICABLE` passing trial. |
| Why deferred | 200 fresh provider sessions are not obtainable from a Max-plan terminal within its rate and session limits, and there is no harness that can mint unique provider session IDs on demand. |
| Unblock condition | A trial harness with session-level control, plus a plan or quota that permits the trial count; the suite manifest and fixture set frozen and digested first. |
| Rung served | 2. |
| Statements moved here | `06:69`; `templates/skill-spec.md:259`. |

Quick-mode eval results remain generation feedback only. No document may present them as conformance.

## PM-03

**Administrator-managed hook policy (`requirements.toml`)**

| | |
|---|---|
| What | `examples/hooks/requirements.codex.toml` deployed through the Codex administrator-managed requirements layer: pins hooks on, pins one open worker, permits only read-only and workspace sandboxes, sets `allow_managed_hooks_only = true`, and ignores user, project, and plugin hooks. |
| Why deferred | The managed requirements layer is written to a machine-level absolute path by an administrator. A Max-plan terminal user has no administrator role for that layer, so it cannot be installed or verified from a session. |
| Unblock condition | Administrative control of the host, or an equivalent org-managed policy channel; then reinstate the "project-trusted or administrator-managed, never both" installation rule. |
| Rung served | 3 (provider hooks). |
| Statements moved here | `09:13`, `09:91-92` (the managed-hooks cells), `09:123`; `07:75` (the "managed Codex hooks reduce the disable escape" clause). |

Until PM-03 lands: project hooks are trusted by definition hash through `/hooks` and remain user-disableable. That hole is covered by PM-10, not by a managed layer.

## PM-04

**Per-phase sandbox or container mounts**

| | |
|---|---|
| What | A phase launcher that starts each worker in a sandbox or container whose only writable mount is the phase's fence inside the candidate root, with everything else — the rest of the root, the canonical checkout, the home directory, the network — read-only or absent. |
| Why deferred | Building and mounting per-phase filesystems requires a container runtime and process supervision outside the agent session. A Max-plan terminal runs the agent inside the provider's own sandbox and cannot re-parent it. |
| Unblock condition | A supported host runtime (container or namespace) plus a launcher that the sequencer can invoke before dispatch; then the hook fence becomes a fast-feedback layer instead of the boundary. |
| Rung served | 3, upgrading it toward an OS boundary. |
| Statements moved here | `09:198` (the "run each phase in a sandbox/container" remedy), `09:201` (the "phase launcher that builds a restricted mount" remedy). |

**What the candidate root already covers, and what a sandbox would add.** The candidate root is a real isolation boundary for the outcome: a worker writes in a directory the sequencer owns, the canonical checkout is untouched for the whole run, promotion moves only the paths the run's receipts claimed and the checkpoint diff confirmed, and a run that is never promoted leaves no trace. Nothing a worker does — inside its fence, outside its fence, or outside the root entirely — reaches the canonical tree except through `devforgeai promote <run>`. On Codex, where `PreToolUse` carries no actor identity, the root is what makes the write check decidable at all: a path test on the filesystem rather than a claim in a tool input.

Three things the root does not give, and a sandbox would:

1. **Prevention rather than detection inside the root.** An out-of-fence write inside the root is caught at the next checkpoint diff, after the bytes exist. A mount would refuse the `write(2)`.
2. **Containment outside the root.** A hostile or buggy subprocess started by `devforgeai run <key>` can write anywhere the agent's own process can — the user's home directory, another project. That is out of scope of every check this framework performs; only an OS boundary bounds it.
3. **A hard boundary that survives a disabled hook.** Every check in `09` is a hook, and hooks are user-disableable and fail open on infrastructure faults. A mount is not.

Codex's native `workspace-write` sandbox in `config.codex.toml` is not deferred; it runs today, is pointed at the candidate root, and stays in `09`.

## PM-05

**Token telemetry in `/status`**

| | |
|---|---|
| What | `/status` reporting the primary window's token consumption per skill run, read from `provenance/log.jsonl`, so primary-window-contract regressions are visible as numbers. |
| Why deferred | Neither provider exposes per-window token accounting to a hook, a subagent, or a CLI in a terminal session. The sequencer can only record what a hook event carries, and no event carries usage. |
| Unblock condition | A provider event or CLI that reports per-turn usage to a hook; then the sequencer writes the figure into the `log.jsonl` row it already appends. |
| Rung served | 1 (guidance; it is an observability aid, not a refusal). |
| Statements moved here | `01:54` (final sentence). |

Until PM-05 lands, the primary-window contract is enforced structurally by `skill-validator`, not by measurement.

## PM-06

**Full eval mode and the eval viewer**

| | |
|---|---|
| What | skill-creator's `full` eval mode: enabled and disabled baseline runs per prompt, the interactive eval viewer, and the description-optimization loop. |
| Why deferred | `full` mode requires an interactive session with a viewer surface and a human review loop. The generation protocol is cold-session and headless by design, and a Max-plan terminal has no viewer. |
| Unblock condition | An interactive authoring station with the viewer available, and a decision that a human reviews each generated skill before it is written. |
| Rung served | 2. |
| Statements moved here | `06:66-68` (the eval-mode table's `full` row and its viewer column), `06:67`, `06:92`; `templates/skill-spec.md:60` (the viewer clause), `:64` (the `full` bullet). |

Supported modes are `skip` and `quick`. A spec must not name `full`.

## PM-07

**Any provider API use**

| | |
|---|---|
| What | Calling a provider's HTTP API directly from the framework: batch grading, programmatic subagent fan-out, model-side validation, or a hosted evaluation service. |
| Why deferred | Max-plan terminal use is the stated deployment. There is no API key in scope, no billing path, and no place to store a credential that the enforcement ladder would accept. |
| Unblock condition | An explicit decision to take an API dependency, with a key custody design and a rung-3 rule for the network calls it makes. |
| Rung served | — (it is a capability, not a refusal). |
| Statements moved here | none; recorded so no specification introduces one. |

Every worker in the MVP is dispatched by the host agent, and every deterministic step is a local process.

## PM-08

**Legacy DevForgeAI document migration**

| | |
|---|---|
| What | Reading documents produced by an earlier DevForgeAI version and rewriting them into the current templates, with provenance carried forward. |
| Why deferred | It is not a terminal capability limit but a scope limit; it is recorded here so `03` carries a pointer instead of a bare exclusion. No migration corpus exists in this repository, so a migrator cannot be specified or tested. |
| Unblock condition | A frozen set of legacy document shapes with real instances to migrate, and a decision that old provenance is trusted. |
| Rung served | 2. |
| Statements moved here | `03:8`. |

Until PM-08 lands, `onboard` treats a legacy DevForgeAI document exactly as it treats any other non-DevForgeAI document.

## PM-09

**Monorepo `stack.yaml`**

| | |
|---|---|
| What | One `stack.yaml` describing several packages with distinct package managers, manifests, and command sets, selected per story by path. |
| Why deferred | The `stack.yaml` contract in `10-sequencer-and-contracts.md` is single-stack: one `commands` block per anchor section, resolved by one hash. Multi-package resolution needs a selector and a per-package `cwd` policy that no MVP skill exercises. |
| Unblock condition | A monorepo fixture with two package managers, and a selector rule in `10` that the sequencer can resolve deterministically at `phase start`. |
| Rung served | 2. |
| Statements moved here | none; recorded so no specification assumes multi-package resolution. |

A monorepo runs today by pinning one section per story; cross-package stories are out of scope.

## PM-10

**Rung 4 repository enforcement**

| | |
|---|---|
| What | Git pre-commit hooks, GitHub rulesets with required status checks, CODEOWNERS on `docs/` and `.devforgeai/`, and a clean-checkout `devforgeai validate` that walks the whole chain from a fresh clone as a required check. |
| Why deferred | Rung 4 runs where the agent has no settings file: a CI runner and a repository's branch-protection settings. A Max-plan terminal has neither. `.git` in this repository is empty, so no pre-commit hook or required check can be installed or exercised. |
| Unblock condition | A real Git remote with administrative settings access, a CI entry point, and the clean-checkout chain validator implemented as a separate command from the active-story `devforgeai validate`. |
| Rung served | 4 (repository enforcement). |
| Statements moved here | `07:106` (the "replace the illustrative validate" next action); `09:208` (the rung-4 bullet's implementation claim). |

Rung 4 stays named in `07-purpose-and-enforcement.md` as external and unimplemented; its refusals are listed there, its implementation is this entry. The active-story `devforgeai validate` described in `10-sequencer-and-contracts.md` is a read-only invariant scan, not the rung-4 validator.

## PM-11

**Clean detached verification worktree for `qa` and `review`**

| | |
|---|---|
| What | A second, throwaway worktree checked out at the run's last checkpoint and detached from the run branch, dispatched to the judge phases — `smoke`, `review`, `qa`'s `run_tests` — so a verification runs against a tree no producer has ever had a handle on, with no build output, no editor artefact and no uncommitted remnant from an earlier phase. |
| Why deferred | It is a second materialisation to create, checkpoint-address, clean and remove per judge dispatch, and it doubles the disk and the setup cost of every run. Today's judges read the same root the producers wrote in, at a checkpoint the sequencer took, which is honest evidence: the tree is exactly what promotion would move. The extra guarantee — that no untracked file influenced the verdict — is real but small, and it is not worth a second root before the first one has been exercised. |
| Unblock condition | Worktree mode proven as the default deployment, and a measured case where an untracked file in the run root changed a judge's outcome. Then the sequencer creates the detached worktree at `candidate checkpoint` time and dispatches judges into it. Copy mode would need the equivalent from its manifest, or would keep judging in place. |
| Rung served | 3. |
| Statements moved here | `10:12.2` (the "clean detached verification worktree" clause of the linear-history section). |

Until PM-11 lands, a judge reads the run's own candidate root at the named checkpoint. A specification must not claim its verification ran against a clean tree.

## PM-12

**Automated integration run for overlapping fences and copy-mode `STALE_BASE`**

| | |
|---|---|
| What | A sequencer-driven integration pass that lets two runs with overlapping fences proceed — opening the second against the first's checkpoint, or replaying the second onto the promoted result and re-running its oracles — and that resolves a copy-mode `STALE_BASE` by recomputing the base manifest and replaying the change set instead of returning `needs_user`. |
| Why deferred | Both are merge policy, and a merge the model does not perform has to be a merge some deterministic thing does perform. Worktree mode already has one such thing for the disjoint case — `git rebase` plus a re-run of the last transition oracle — and it works because git decides the textual merge and the oracle decides whether the result is still correct. Neither exists for copy mode, which has no three-way merge at all, nor for the overlapping-fence case, where two runs may have changed the same lines for different reasons and no oracle can tell which intent survives. |
| Unblock condition | A copy-mode three-way merge with a defined conflict representation, plus a rule for what an overlapping-fence integration re-runs and what it refuses. Until then `FENCE_OVERLAP` at `phase start` and `needs_user` at promotion are the honest answers. |
| Rung served | 3. |
| Statements moved here | `10:12.2` (the "overlapping-fence integration" clause). |

Until PM-12 lands: `devforgeai phase start` refuses a story whose fence overlaps an active or `ready_to_promote` run, and a copy-mode `STALE_BASE` at promotion hands off to a human with the moved paths named.

## PM-13

**Pull-request and merge-queue promotion**

| | |
|---|---|
| What | `devforgeai promote <run>` pushing the run branch and opening a pull request, rather than fast-forwarding into the local canonical checkout; the merge then happens through a merge queue with the required status checks of PM-10, and the framework's promotion refusals become the queue's own. |
| Why deferred | It is rung 4 by definition: it needs a remote with administrative settings, a CI entry point, and branch protection. A Max-plan terminal has none of the three, and `.git` in this repository is empty. It is also a different trust model — the decision to merge moves from the user at the terminal to a policy on the server — and that is a choice to make deliberately, not a default to slide into. |
| Unblock condition | PM-10 landed, so a required check exists to gate the queue on; then promotion gains a mode flag and the local fast-forward becomes one of two paths. |
| Rung served | 4. |
| Statements moved here | none; recorded because the candidate root makes it newly cheap to build, and a specification must not assume it exists. |

Until PM-13 lands, promotion is local: a fast-forward in worktree mode or an exact-byte copy in copy mode, into the user's own checkout, which the user then commits. Pushes, approvals and required checks stay rung 4 and separate from candidate isolation, which is rungs 2 and 3.
