# Security Review: DevForgeAI PR 22

## Scope

Exact-head review of all 33 changed PR 22 paths plus directly supporting validator and plan contracts. D-CP00-11 prohibited DevForge writes, sudo, installation, probe authoring, and closure evidence.

- Scan mode: diff
- Target kind: git_diff
- Target ID: github.com/bankielewicz/DevForgeAI
- Revision range: 0384446503fc4fd4605e8af5013975d54c279c0a...257ba7dbf972d6591a2848bb97cfd9cb1a31033e
- Snapshot digest: codex-security-snapshot/v1:sha256:fa2e218fa6da5498e0eea5cc899a20bb1cdfca48fe70e14745ccaec64018a56b
- Inventory strategy: diff
- Included paths: .
- Excluded paths: none
- Runtime or test status: 244 research tests, 15 release tests, design verifier, 240 conformance rows, three manifests, checkpoint validator, and git diff check passed locally. Four targeted hostile reproductions also ran locally without sudo or installation.
- Artifacts reviewed: R/G/P commit boundaries, checkpoint validator and schema, release wrapper, launcher, installer, verifier, manifest generator, wheels and lockfile, CP-00 record, governing plan and dossier, all changed tests and manifests

Limitations and exclusions:
- Excluded protected DevForge repository and /usr/local installation: D-CP00-11 expressly prohibited DevForge changes, sudo, installs, probe script authoring, and closure evidence.

### Scan Summary

| Field | Value |
| --- | --- |
| Scan outcome | completed |
| Reportable findings | 4 |
| Severity mix | high: 4 |
| Confidence mix | high: 4 |
| Coverage | partial |
| Validation mode | focused dynamic reproductions plus exact source tracing |

Canonical artifacts: `scan-manifest.json`, `findings.json`, and `coverage.json`. This report is a deterministic projection of those files.

## Threat Model

Text: # Threat Model: PR 22 checkpoint validator promotion candidate The reviewed change stages a release scaffold and checkpoint-closure validator whose security purpose is to prevent Claude Code or Codex, running as the unprivileged repository user, from changing or gaming authoritative gates. The protected DevForge installation is expected to be root-owned outside every agent-writable workspace. ## Assets and objectives - Integrity and identity of the validator, launcher, schema, policy, dependencies, and complete installed release. - Truth of checkpoint PASS and closure verdicts. - Exact candidate-to-DevForge-release provenance. - Closure-only history and authoritative base/head provenance. ## Attacker capabilities - The workspace agent can edit checkpoint records, evidence, project-local code, and environment variables, and can invoke allowed commands as the ordinary user. - The agent can choose CLI arguments unless a protected host supplies them. - The agent cannot modify a correctly installed uid-0 release, obtain sudo non-interactively, or write the protected DevForge repository. - Multiple immutable DevForge releases may coexist. ## Trust boundaries - Agent-controlled shell arguments and process environment enter the protected wrapper. - The wrapper launches the distro interpreter and imports the release-local validator. - The executing validator verifies its own release root. - Each record independently names a protected executable and associated release root. - Git subprocesses turn repository history and a caller-provided diff range into closure decisions. - Human promotion maps staged candidate bytes to a protected release. ## Security objectives - The record executable must be exactly the executing release's own root/bin/devforge. - Release metadata and promotion evidence must bind the candidate manifest, DevForge commit/tag, release manifest, and executing root. - Caller environment must not redirect the interpreter, Git repository, object database, configuration, hooks, or output. - A protected host, not the workspace agent, must bind the reviewed closure base/head. - Staged candidate bytes must never be treated as protected. ## Assumptions and limitations - POSIX uid/mode enforcement only. - /usr/bin/python3 and its standard library remain outside RELEASE.sha256 and require separately reviewed distro evidence. - No real root-owned install or two-terminal positive probe was authorized by D-CP00-11. - The installer assumes an immutable DevForge source/release; this review did not run it as root. - Codex Security advisory intelligence was unavailable after its authentication request, so no TAC result was incorporated. Repository: DevForgeAI Version: 257ba7dbf972d6591a2848bb97cfd9cb1a31033e

## Findings

| Finding | Severity | Confidence | Detailed write-up |
| --- | --- | --- | --- |
| [Inherited Git environment can replace the repository history](#finding-1) | high | high | inline below |
| [Record-selected release can differ from the executing validator](#finding-2) | high | high | inline below |
| [Loader injection runs before the protected wrapper can scrub the environment](#finding-3) | high | high | inline below |
| [Caller-selected diff base can hide closure-related implementation changes](#finding-4) | high | high | inline below |

### Confidence Scale

| Label | Meaning |
| --- | --- |
| high | Direct evidence supports the finding with no material unresolved blocker. |
| medium | Evidence supports a plausible issue, but material runtime or reachability proof remains. |
| low | Evidence is incomplete and the item is retained only for explicit follow-up. |

<a id="finding-1"></a>

### [1] Inherited Git environment can replace the repository history

| Field | Value |
| --- | --- |
| Severity | high |
| Confidence | high |
| Confidence rationale | The changed code was traced end to end and a focused reproduction exercised the actual boundary without sudo or protected-file mutation. |
| Category | External control of system configuration |
| CWE | CWE-15 |
| Affected lines | components/devforge-release/bin/devforge:20-21, components/research-core/src/devforgeai/checkpoint/validate.py:152-160, components/research-core/src/devforgeai/checkpoint/__main__.py:38-42 |

#### Summary

`_git` uses a PATH-resolved Git subprocess with the caller's complete environment, allowing Git control variables to redirect HEAD, ancestry, tree, and diff operations while the reported work-tree root still appears legitimate.

#### Root Cause

The wrapper clears only Python variables, and `_git` inherits every remaining variable while invoking `git` through PATH. `GIT_DIR`, `GIT_WORK_TREE`, object-directory, config, hook, and diff controls are therefore caller-selected inputs to every security decision.

#### Validation

With two repositories holding different HEADs, setting `GIT_DIR` to the alternate repository and `GIT_WORK_TREE` to the legitimate plan path made `git -C` report the legitimate show-toplevel but return the alternate HEAD.

Validation method: Focused local reproduction against the exact PR head

- **Status:** confirmed
- **Disposition:** reportable

Limitations:
- No root-owned install or live provider probe was authorized; neither is needed to observe the missing control.

#### Dataflow

caller environment -\> wrapper preserves GIT_\* -\> `_git` inherits environment -\> Git reads attacker object database -\> S06/S10/S13 consume attacker history

- **Source:** workspace-controlled record, arguments, or process environment

- **Sink:** checkpoint closure verdict

- **Outcome:** attacker-selected evidence is accepted as authoritative

Transformations:
- protected wrapper or validator receives untrusted values
- changed control validates only local consistency
- verdict is emitted without the missing binding

#### Reachability

The ordinary workspace agent can create an alternate Git directory and set process environment variables when invoking validation unless a protected host strips them first.

- **Attacker:** Claude Code or Codex process running as the ordinary workspace user

- **Entry point:** absolute devforge checkpoint validate invocation

- **Outcome:** the protected gate can produce a misleading PASS

Preconditions:
- the agent can write its workspace and invoke the allowed validation command

Existing controls:
- root-owned release bytes
- release digest verification
- human independent review

#### Severity

**High** — The ordinary workspace agent can create an alternate Git directory and set process environment variables when invoking validation unless a protected host strips them first. The impact is loss of integrity in the machine gate that is intended to stop an agent from gaming checkpoint closure.

Severity would decrease only if a protected caller supplies and authenticates every relevant input and process environment so the workspace agent cannot reach this path.

#### Remediation

Invoke `/usr/bin/git` with an explicit minimal environment rather than a copy of `os.environ`; remove all Git-control variables and disable user/system configuration and hooks. Treat a protected host's repository identity as input rather than trusting discovery alone.

Tests:
- Set GIT_DIR/GIT_WORK_TREE to an alternate repository and require COULD_NOT_RUN or the canonical HEAD.
- Cover GIT_OBJECT_DIRECTORY, alternates, config count, hooks path, diff external, and work-tree variables.

Preventive controls:
- Central immutable subprocess environment policy for every enforcement child process.

<a id="finding-2"></a>

### [2] Record-selected release can differ from the executing validator

| Field | Value |
| --- | --- |
| Severity | high |
| Confidence | high |
| Confidence rationale | The changed code was traced end to end and a focused reproduction exercised the actual boundary without sudo or protected-file mutation. |
| Category | Release identity substitution |
| CWE | CWE-345 |
| Affected lines | components/research-core/src/devforgeai/checkpoint/validate.py:515-545, components/research-core/src/devforgeai/checkpoint/validate.py:845-850, components/devforge-release/INSTALLED-LAYOUT.md:23-30 |

#### Summary

The installed validator verifies its own release and the record-selected release separately, so a record can bind provider proof to another coexisting protected release and still pass.

#### Root Cause

`validate_plan` derives and verifies the executing release root but does not pass it to `_check_release_pin`; that function derives a second root solely from the record executable. It hashes promotion evidence but does not parse a candidate-manifest to DevForge commit/tag to release-manifest mapping or bind version/source fields to the executing tree.

#### Validation

A hostile fixture made release A the executing root and left the closed record naming separately protected release B. Both trees verified and `validate_plan` returned PASS with no problems.

Validation method: Focused local reproduction against the exact PR head

- **Status:** confirmed
- **Disposition:** reportable

Limitations:
- No root-owned install or live provider probe was authorized; neither is needed to observe the missing control.

#### Dataflow

record protected_release fields -\> derive root B -\> verify B; module location -\> derive root A -\> verify A; no equality or release-metadata comparison -\> PASS

- **Source:** workspace-controlled record, arguments, or process environment

- **Sink:** checkpoint closure verdict

- **Outcome:** attacker-selected evidence is accepted as authoritative

Transformations:
- protected wrapper or validator receives untrusted values
- changed control validates only local consistency
- verdict is emitted without the missing binding

#### Reachability

A workspace agent can select another installed, root-owned DevForge version in the record. The agent need not modify either release; coexistence of two releases is enough.

- **Attacker:** Claude Code or Codex process running as the ordinary workspace user

- **Entry point:** absolute devforge checkpoint validate invocation

- **Outcome:** the protected gate can produce a misleading PASS

Preconditions:
- the agent can write its workspace and invoke the allowed validation command

Existing controls:
- root-owned release bytes
- release digest verification
- human independent review

#### Severity

**High** — A workspace agent can select another installed, root-owned DevForge version in the record. The agent need not modify either release; coexistence of two releases is enough. The impact is loss of integrity in the machine gate that is intended to stop an agent from gaming checkpoint closure.

Severity would decrease only if a protected caller supplies and authenticates every relevant input and process environment so the workspace agent cannot reach this path.

#### Remediation

Carry the executing `release_root` into record enforcement and require an exact canonical match to `<release_root>/bin/devforge`. Add a digest-bound release metadata file under `RELEASE.sha256` that binds release version, DevForge source commit, candidate-manifest digest, and release-manifest digest; parse promotion evidence or replace it with that machine record.

Tests:
- Reject a complete valid record when its executable is under a different protected root.
- Reject wrong version, source commit, candidate manifest digest, or release manifest digest even when selected files hash correctly.

Preventive controls:
- One machine-readable release identity used by the wrapper, validator, record, and provider proofs.

<a id="finding-3"></a>

### [3] Loader injection runs before the protected wrapper can scrub the environment

| Field | Value |
| --- | --- |
| Severity | high |
| Confidence | high |
| Confidence rationale | The changed code was traced end to end and a focused reproduction exercised the actual boundary without sudo or protected-file mutation. |
| Category | External control of process environment |
| CWE | CWE-15 |
| Affected lines | components/devforge-release/bin/devforge:18-29 |

#### Summary

The protected entry point is a dynamically loaded shell script. Loader-control variables are acted on before the script executes, so root ownership and an absolute path do not stop same-user code injection into the validation process.

#### Root Cause

The first executable is `/bin/sh`, selected by the shebang. The dynamic loader processes `LD_PRELOAD` before shell code reaches the environment cleanup. Unsetting loader variables inside the script would therefore be too late.

#### Validation

A minimal constructor shared object supplied via `LD_PRELOAD` created a marker before a relative invocation was rejected and fired repeatedly through the absolute wrapper invocation. No repository or protected byte was changed.

Validation method: Focused local reproduction against the exact PR head

- **Status:** confirmed
- **Disposition:** reportable

Limitations:
- No root-owned install or live provider probe was authorized; neither is needed to observe the missing control.

#### Dataflow

caller LD_PRELOAD -\> dynamic loader starts /bin/sh -\> injected constructor executes -\> wrapper later scrubs only Python variables -\> attacker can alter exec or verdict

- **Source:** workspace-controlled record, arguments, or process environment

- **Sink:** checkpoint closure verdict

- **Outcome:** attacker-selected evidence is accepted as authoritative

Transformations:
- protected wrapper or validator receives untrusted values
- changed control validates only local consistency
- verdict is emitted without the missing binding

#### Reachability

A development agent that can write source and run compiler/tool commands as the ordinary user can supply a shared object when the absolute validator is called. A provider allowlist may reduce reachability but cannot be the independent DevForge boundary.

- **Attacker:** Claude Code or Codex process running as the ordinary workspace user

- **Entry point:** absolute devforge checkpoint validate invocation

- **Outcome:** the protected gate can produce a misleading PASS

Preconditions:
- the agent can write its workspace and invoke the allowed validation command

Existing controls:
- root-owned release bytes
- release digest verification
- human independent review

#### Severity

**High** — A development agent that can write source and run compiler/tool commands as the ordinary user can supply a shared object when the absolute validator is called. A provider allowlist may reduce reachability but cannot be the independent DevForge boundary. The impact is loss of integrity in the machine gate that is intended to stop an agent from gaming checkpoint closure.

Severity would decrease only if a protected caller supplies and authenticates every relevant input and process environment so the workspace agent cannot reach this path.

#### Remediation

Launch enforcement from a protected parent with an explicit environment, or replace the shell entrypoint with an appropriately reviewed static launcher that clears loader, Git, Python, locale, and shell controls before `execve` of the interpreter. Do not claim a shell script can self-sanitize pre-start loader state.

Tests:
- Invoke through hostile LD_PRELOAD and LD_AUDIT libraries and prove no constructor executes and output remains canonical.
- Repeat from both provider terminals through the actual protected host path.

Preventive controls:
- A single protected process launcher shared by hooks, CI, and terminal probes.

<a id="finding-4"></a>

### [4] Caller-selected diff base can hide closure-related implementation changes

| Field | Value |
| --- | --- |
| Severity | high |
| Confidence | high |
| Confidence rationale | The changed code was traced end to end and a focused reproduction exercised the actual boundary without sudo or protected-file mutation. |
| Category | Reliance on untrusted input in security decision |
| CWE | CWE-807 |
| Affected lines | components/research-core/src/devforgeai/checkpoint/__main__.py:31-33, components/research-core/src/devforgeai/checkpoint/validate.py:773-828 |

#### Summary

S10 only scans changes in the supplied range and only enforces closure-only paths when it observes a false-to-true record transition. A workspace caller can choose a later base after implementation changes and re-pin an already-closed record in the head commit.

#### Root Cause

The CLI exposes `--diff` directly to the caller. `_check_diff` verifies only that head is current and base is a proper ancestor, then returns immediately if no currently closed record changed from open to closed relative to that base.

#### Validation

After a legal closure, a focused fixture changed implementation and candidate-manifest bytes in one commit and re-pinned the still-closed record in the next. Using the implementation commit as base returned PASS with no S10 problem.

Validation method: Focused local reproduction against the exact PR head

- **Status:** confirmed
- **Disposition:** reportable

Limitations:
- No root-owned install or live provider probe was authorized; neither is needed to observe the missing control.

#### Dataflow

workspace implementation change -\> commit and candidate re-pin -\> record-only head commit -\> caller selects implementation commit as base -\> no false-to-true transition -\> S10 returns -\> PASS

- **Source:** workspace-controlled record, arguments, or process environment

- **Sink:** checkpoint closure verdict

- **Outcome:** attacker-selected evidence is accepted as authoritative

Transformations:
- protected wrapper or validator receives untrusted values
- changed control validates only local consistency
- verdict is emitted without the missing binding

#### Reachability

The plan explicitly admits this as CS-3.3 future DevForge work. That is honest counterevidence against a PROVEN claim, but the CP-00 record currently labels the staged implementation PASS and the candidate is proposed for promotion.

- **Attacker:** Claude Code or Codex process running as the ordinary workspace user

- **Entry point:** absolute devforge checkpoint validate invocation

- **Outcome:** the protected gate can produce a misleading PASS

Preconditions:
- the agent can write its workspace and invoke the allowed validation command

Existing controls:
- root-owned release bytes
- release digest verification
- human independent review

#### Severity

**High** — The plan explicitly admits this as CS-3.3 future DevForge work. That is honest counterevidence against a PROVEN claim, but the CP-00 record currently labels the staged implementation PASS and the candidate is proposed for promotion. The impact is loss of integrity in the machine gate that is intended to stop an agent from gaming checkpoint closure.

Severity would decrease only if a protected caller supplies and authenticates every relevant input and process environment so the workspace agent cannot reach this path.

#### Remediation

Do not authorize closure from an arbitrary terminal-supplied range. Bind base and head in a protected DevForge/CI host from reviewed PR metadata, and make the validator verify that binding. Revalidate any already-closed record mutation and its candidate-to-release mapping, not only first closure transitions.

Tests:
- Retain the reproduced implementation-commit to pin-commit range and require rejection.
- Test mutations to every already-closed record after its original closure.
- Reject a caller range that differs from the protected review range.

Preventive controls:
- Protected review-range attestation consumed by closure validation.

## Reviewed Surfaces

| Surface | Risk Area | Outcome | Notes |
| --- | --- | --- | --- |
| Validator release identity and promotion mapping | release substitution | Reported | Cross-root fixture returned PASS. Evidence: artifacts/05_findings/candidate-fa00cbdf00fd925e/validation_report.md, artifacts/05_findings/candidate-fa00cbdf00fd925e/attack_path_analysis_report.md |
| Git repository and history selection | caller-controlled Git configuration | Reported | Alternate object database selected through inherited environment. Evidence: artifacts/05_findings/candidate-47705383ae3f38a3/validation_report.md, artifacts/05_findings/candidate-47705383ae3f38a3/attack_path_analysis_report.md |
| Protected wrapper process boundary | loader injection | Reported | Constructor code ran before the shell script executed. Evidence: artifacts/05_findings/candidate-72d484d951dcef65/validation_report.md, artifacts/05_findings/candidate-72d484d951dcef65/attack_path_analysis_report.md |
| Closure-only Git range enforcement | security decision from untrusted range | Reported | Narrowed range passed with post-closure implementation changes. Evidence: artifacts/05_findings/candidate-6a9bcf718aaa5828/validation_report.md, artifacts/05_findings/candidate-6a9bcf718aaa5828/attack_path_analysis_report.md |
| Offline dependencies, wheel lock, and manifests | dependency and release payload integrity | No issue found | Vendored wheel hashes, offline install, manifests, and release tests passed; PyPI was not refreshed. Evidence: artifacts/03_coverage/reviewed_surfaces.md |
| Installer source custody and post-install verifier | root installer trust | Needs follow-up | Assumes immutable DevForge source and skips post-verification if the sibling verifier is missing or not executable. Evidence: artifacts/03_coverage/reviewed_surfaces.md |
| Installed layout v1 equivalence | contract drift | Needs follow-up | Narrative requires launcher and exact modes; generator, verifier, and validator enforce a narrower subset. Evidence: artifacts/03_coverage/reviewed_surfaces.md |
| CP-00 required outputs | governance completeness | Needs follow-up | The governing plan output list omits the release scaffold and its no-diff example becomes invalid after closure. Evidence: artifacts/03_coverage/reviewed_surfaces.md |

## Open Questions And Follow Up

- What protected DevForge host will authenticate the reviewed base/head and launch the validator with a minimal environment?
  - Follow-up prompt: Specify and hostile-test the protected range and process launcher before promoting PR 22's candidate.
- Will the release carry a machine-readable identity that binds candidate digest, DevForge commit/tag, release manifest, and exact executable root?
  - Follow-up prompt: Add CS-1.8 and release-metadata hostile cases, then regenerate the candidate pin.
- A real uid-0 installation and fresh Claude/Codex invocation remain NOT_EVALUATED under the stop order.
  - Follow-up prompt: Review deferred unit real-protected-install and close its stated proof gap. Paths: components/devforge-release/. Surfaces: installer, layout.
- The advisory tool requested authentication and returned no intelligence; source-backed local review continued without it.
  - Follow-up prompt: Review deferred unit tac-advisory and close its stated proof gap. Surfaces: payload.
