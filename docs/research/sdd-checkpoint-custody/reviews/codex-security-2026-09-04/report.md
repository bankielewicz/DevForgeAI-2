# Security Review: bankielewicz/DevForgeAI PR 20

## Scope

Exact-diff security review of PR 20's CP-00 promotion, protected-install, provider-probe, evidence, and closure instructions, with supporting review of the validator and its tests.

- Scan mode: diff
- Target kind: git_diff
- Target ID: devforgeai-pr20-9305715-b9998de
- Revision range: 9305715da59e179a89ea847caeb046fadde0c30a...b9998de92a821efa85f31497ee5b22f8fd97bf56
- Snapshot digest: codex-security-snapshot/v1:sha256:55f244705de1243a43ef6c6882165f642a8020659c71fd4ab9d597e42892e92b
- Inventory strategy: diff
- Included paths: CLAUDE.md, docs/CHECKPOINT.md
- Excluded paths: none
- Runtime or test status: Targeted tests pass 59/59 and the staged plan reports 15 records with 0 problems, but hostile subprocess proofs reproduce three fail-open behaviors.
- Artifacts reviewed: PR 20 base 9305715da59e179a89ea847caeb046fadde0c30a and head b9998de92a821efa85f31497ee5b22f8fd97bf56, components/research-core/src/devforgeai/checkpoint/__main__.py, components/research-core/src/devforgeai/checkpoint/validate.py, tests/research/test_gap_checkpoints.py, framework/contracts/MANIFEST.sha256, Four local subprocess proof scripts under artifacts/05_findings
- Scan context: The human owner asked whether Claude's proposed promotion, root install, and two-terminal proof sequence is safe and conforms to DevForgeAI's spec-driven trust boundary.

Limitations and exclusions:
- The separate DevForge repository and any future release artifact were not available for review.
- Claude Code and Codex live probes were intentionally not run because the candidate gate is unsafe before remediation.
- Codex Security TAC display status could not be verified after two accepted authentication retries; this did not affect local evidence.

### Scan Summary

| Field | Value |
| --- | --- |
| Scan outcome | completed |
| Reportable findings | 4 |
| Severity mix | high: 3, medium: 1 |
| Confidence mix | high: 4 |
| Coverage | partial |
| Validation mode | Exact-source inspection plus deterministic local subprocess proofs; no root installation or live provider session was performed. |

Canonical artifacts: `scan-manifest.json`, `findings.json`, and `coverage.json`. This report is a deterministic projection of those files.

## Threat Model

An AI worker can control workspace files, checkpoint data, process arguments, environment variables, and user-owned evidence, but must not be able to alter or select the protected validator, schema, policy, release manifest, or closure oracle. Human sudo and release authority are trusted. The protected boundary must fail closed when installed resources are missing, mutable, mismatched, caller-overridden, or incompletely invoked.

### Assets

- Root-owned DevForge executable and its complete release manifest
- Installed checkpoint schema and policy bytes
- CP-00 evidence and closure decision
- Human release, root-install, and acceptance authority

### Trust Boundaries

- Agent-writable DevForgeAI workspace to root-owned DevForge installation
- Caller-controlled CLI arguments and environment to protected validation policy
- User-writable probe output to independently reviewed closure evidence

### Attacker Capabilities

- Modify repository-local validator, schema, records, and evidence
- Choose or omit CLI options and influence environment variables
- Invoke the protected executable without sudo
- Interrupt a probe after a destructive step

### Security Objectives

- No agent-selected schema, repository root, or validation mode can weaken closure
- Every executed and imported release byte is reviewed, pinned, and root-owned
- Missing or mutable protected resources always reject
- Negative probes preserve protected and canonical bytes even when a control is broken

### Assumptions

- The human controls DevForge promotion, sudo, and final acceptance
- Agent sessions do not possess passwordless sudo or equivalent root capability

## Findings

| Finding | Severity | Confidence | Detailed write-up |
| --- | --- | --- | --- |
| [Protected-release validation accepts missing or user-owned enforcement bytes](#finding-1) | high | high | inline below |
| [Caller arguments can replace the protected validation schema](#finding-2) | high | high | inline below |
| [Omitting `--diff` bypasses the closure-only change fence](#finding-3) | high | high | inline below |
| [The proposed negative probe can corrupt the live control it tests](#finding-4) | medium | high | inline below |

### Confidence Scale

| Label | Meaning |
| --- | --- |
| high | Direct evidence supports the finding with no material unresolved blocker. |
| medium | Evidence supports a plausible issue, but material runtime or reachability proof remains. |
| low | Evidence is incomplete and the item is retained only for explicit follow-up. |

<a id="finding-1"></a>

### [1] Protected-release validation accepts missing or user-owned enforcement bytes

| Field | Value |
| --- | --- |
| Severity | high |
| Confidence | high |
| Confidence rationale | Direct source inspection and a deterministic subprocess PoC both show exit 0 for a uid-1000 mode-0644 executable and for a nonexistent executable. |
| Category | protection mechanism failure |
| CWE | CWE-693 |
| Affected lines | docs/CHECKPOINT.md:20-23, components/research-core/src/devforgeai/checkpoint/validate.py:377-415, tests/research/test_gap_checkpoints.py:100-110 |

#### Summary

PR 20 makes the staged validator the gate for a root-owned DevForge release, but `_check_release_pin` verifies a digest only when an executable or absolute evidence path happens to exist and never verifies owner, mode, parent-directory writability, symlinks, or the installed schema and policy bytes. An agent-writable executable can therefore satisfy the same closure record as a protected one, and a nonexistent executable is silently skipped.

#### Root Cause

The record's declaration `installation_owner: root` is trusted as metadata instead of being checked against the installed filesystem object, and resource existence is treated as optional.

**Missing executable skips validation** — `components/research-core/src/devforgeai/checkpoint/validate.py:389-391`

The `is_file()` guard converts absence into success and performs no ownership or permission validation when a file exists.

```python
exe = Path(executable)
if exe.is_file() and _sha256(exe) != release["executable_sha256"]:
    reject(rule, f"executable digest mismatch at {executable}")
```

**Positive fixture is user-owned** — `tests/research/test_gap_checkpoints.py:103-110`

The passing test labels a normal user-owned temporary file as protected, so it cannot distinguish the required root-owned state.

```python
self._ext = tempfile.TemporaryDirectory(prefix="dfai-cp00-ext-")
self.executable = Path(self._ext.name) / "devforge"
self.executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
self.exe_sha = sha256(self.executable)
```

#### Validation

Validation outcomes are recorded below.

Validation method: Constructed valid closed scratch records, then substituted a user-owned executable and a nonexistent absolute executable while retaining matching record metadata.

- **Status:** confirmed
- **Disposition:** reportable

**Missing executable skips validation** — `components/research-core/src/devforgeai/checkpoint/validate.py:389-391`

The `is_file()` guard converts absence into success and performs no ownership or permission validation when a file exists.

```python
exe = Path(executable)
if exe.is_file() and _sha256(exe) != release["executable_sha256"]:
    reject(rule, f"executable digest mismatch at {executable}")
```

**Positive fixture is user-owned** — `tests/research/test_gap_checkpoints.py:103-110`

The passing test labels a normal user-owned temporary file as protected, so it cannot distinguish the required root-owned state.

```python
self._ext = tempfile.TemporaryDirectory(prefix="dfai-cp00-ext-")
self.executable = Path(self._ext.name) / "devforge"
self.executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
self.exe_sha = sha256(self.executable)
```

Assertions:
- A uid-1000 mode-0644 executable produced 3 records, 0 problems and exit 0.
- A nonexistent executable path produced 3 records, 0 problems and exit 0.

Evidence:
- artifacts/05_findings/probe_validator_failopen.py

Limitations:
- No root-owned installation was needed to prove the fail-open branches.

#### Dataflow

Agent-controlled release record and path -\> `_check_release_pin` -\> `is_file()` false or digest-only true -\> no rejection -\> CP-00 closure validation passes.

- **Source:** Checkpoint YAML protected_release fields

- **Sink:** Zero-problem validator verdict

- **Outcome:** Unprotected or absent enforcement can be recorded as a protected release

**Missing executable skips validation** — `components/research-core/src/devforgeai/checkpoint/validate.py:389-391`

The `is_file()` guard converts absence into success and performs no ownership or permission validation when a file exists.

```python
exe = Path(executable)
if exe.is_file() and _sha256(exe) != release["executable_sha256"]:
    reject(rule, f"executable digest mismatch at {executable}")
```

#### Reachability

An AI worker preparing the closure PR controls record bytes and can point them at a user-owned or absent absolute path; the human may see a passing gate unless filesystem truth is independently checked.

- **Attacker:** Workspace-capable Claude Code or Codex worker

- **Entry point:** Checkpoint protected_release record

- **Sink:** CP-00 validator PASS

- **Outcome:** False proof of protected enforcement

Preconditions:
- The closure command runs the current staged validator

**Missing executable skips validation** — `components/research-core/src/devforgeai/checkpoint/validate.py:389-391`

The `is_file()` guard converts absence into success and performs no ownership or permission validation when a file exists.

```python
exe = Path(executable)
if exe.is_file() and _sha256(exe) != release["executable_sha256"]:
    reject(rule, f"executable digest mismatch at {executable}")
```

#### Severity

**High** — This is the root integrity gate for CP-00; a local agent that controls record fields can obtain a passing validation without the promised protected installation.

Severity would fall after the validator rejects absent resources and independently verifies root ownership, non-writability, symlink ancestry, and every installed release digest against a protected manifest.

#### Remediation

Make every protected resource mandatory and fail closed on `lstat` or hash errors. Verify uid 0, required modes, non-writable parent directories, no unexpected symlink traversal or ACL write grant, and actual executable, schema-set, policy, dependency, and release-manifest digests. Do not trust `installation_owner` as proof.

Tests:
- Reject missing executable, schema, manifest, promotion evidence, and permissions evidence.
- Reject uid-nonzero, group/other-writable file or ancestor, symlink substitution, ACL write grant, and digest mismatch.
- Run the positive integration test through the actual protected executable rather than `sys.executable` plus workspace `PYTHONPATH`.

Preventive controls:
- Use one protected release manifest covering every executed/imported byte and verify it before validation.

<a id="finding-2"></a>

### [2] Caller arguments can replace the protected validation schema

| Field | Value |
| --- | --- |
| Severity | high |
| Confidence | high |
| Confidence rationale | A deterministic subprocess test changed only the final `--schema` argument and changed the same hostile record from exit 1 to exit 0. |
| Category | external control of configuration |
| CWE | CWE-15 |
| Affected lines | docs/CHECKPOINT.md:19-23, components/research-core/src/devforgeai/checkpoint/__main__.py:23-39 |

#### Summary

The proposed wrapper injects the root-owned `--schema` before forwarding caller arguments. The existing argparse interface accepts duplicate `--schema` options and keeps the last value, so an agent can append a permissive project-local schema and remove enforcement constraints while still invoking the absolute protected executable.

#### Root Cause

A test seam is part of the production CLI and the wrapper does not terminate option parsing or reject duplicate protected options.

**Tests-only override is exposed in production parser** — `components/research-core/src/devforgeai/checkpoint/__main__.py:23-39`

Caller-controlled configuration flows unchanged into the validation authority; argparse's default duplicate-option behavior selects the last value.

```python
validate.add_argument("--git-root", type=Path, default=None,
                      help="repository root for Git rules (default: the plan's repository)")
validate.add_argument("--schema", type=Path, default=None,
                      help="override the checkpoint schema path (tests only)")
...
report = validate_plan(args.plan, git_root=args.git_root, schema_path=args.schema,
                       diff_range=args.diff)
```

#### Validation

Validation outcomes are recorded below.

Validation method: Ran the validator on one hostile record with the installed schema and again with a permissive final schema option.

- **Status:** confirmed
- **Disposition:** reportable

**Tests-only override is exposed in production parser** — `components/research-core/src/devforgeai/checkpoint/__main__.py:23-39`

Caller-controlled configuration flows unchanged into the validation authority; argparse's default duplicate-option behavior selects the last value.

```python
validate.add_argument("--git-root", type=Path, default=None,
                      help="repository root for Git rules (default: the plan's repository)")
validate.add_argument("--schema", type=Path, default=None,
                      help="override the checkpoint schema path (tests only)")
...
report = validate_plan(args.plan, git_root=args.git_root, schema_path=args.schema,
                       diff_range=args.diff)
```

Assertions:
- Protected schema rejected with exit 1.
- Caller override accepted with exit 0 and 3 records, 0 problems.

Evidence:
- artifacts/05_findings/probe_schema_override.py

#### Dataflow

Agent CLI arguments -\> duplicate `--schema` -\> argparse last-value selection -\> `validate_plan(schema_path=...)` -\> permissive validation verdict.

- **Source:** Caller arguments

- **Sink:** Schema selection

- **Outcome:** Hostile checkpoint passes

**Tests-only override is exposed in production parser** — `components/research-core/src/devforgeai/checkpoint/__main__.py:23-39`

Caller-controlled configuration flows unchanged into the validation authority; argparse's default duplicate-option behavior selects the last value.

```python
validate.add_argument("--git-root", type=Path, default=None,
                      help="repository root for Git rules (default: the plan's repository)")
validate.add_argument("--schema", type=Path, default=None,
                      help="override the checkpoint schema path (tests only)")
...
report = validate_plan(args.plan, git_root=args.git_root, schema_path=args.schema,
                       diff_range=args.diff)
```

#### Reachability

Any unprivileged caller allowed to invoke `/usr/local/bin/devforge` can append this option; root access is unnecessary.

- **Attacker:** Workspace agent

- **Entry point:** Protected CLI

- **Sink:** Checkpoint validation

- **Outcome:** Policy bypass

Preconditions:
- Wrapper forwards arbitrary trailing arguments

**Tests-only override is exposed in production parser** — `components/research-core/src/devforgeai/checkpoint/__main__.py:23-39`

Caller-controlled configuration flows unchanged into the validation authority; argparse's default duplicate-option behavior selects the last value.

```python
validate.add_argument("--git-root", type=Path, default=None,
                      help="repository root for Git rules (default: the plan's repository)")
validate.add_argument("--schema", type=Path, default=None,
                      help="override the checkpoint schema path (tests only)")
...
report = validate_plan(args.plan, git_root=args.git_root, schema_path=args.schema,
                       diff_range=args.diff)
```

#### Severity

**High** — A non-root workspace agent can directly choose the policy used by the root-owned validator and turn invalid closure records into PASS without modifying protected files.

Severity would fall after production invocation removes or rejects caller-supplied schema and repository-root overrides and binds policy selection inside protected code.

#### Remediation

Separate production and test entrypoints. Production code must select the installed schema and Git root internally and reject `--schema`, `--git-root`, and duplicate protected options. If a wrapper remains, place no security decision in shell argument order.

Tests:
- Assert production CLI rejects `--schema` and `--git-root` with exit 2.
- Append duplicate protected options and prove they cannot change the verdict.

Preventive controls:
- Keep test-only dependency injection callable from Python tests, not from the installed user-facing CLI.

<a id="finding-3"></a>

### [3] Omitting `--diff` bypasses the closure-only change fence

| Field | Value |
| --- | --- |
| Severity | high |
| Confidence | high |
| Confidence rationale | The same scratch closure plus implementation change passed with no range and was rejected by S10 when the range was supplied. |
| Category | improper workflow enforcement |
| CWE | CWE-841 |
| Affected lines | docs/CHECKPOINT.md:22-23, components/research-core/src/devforgeai/checkpoint/__main__.py:29-39 |

#### Summary

S10 only runs when the caller supplies a Git range. PR 20 documents a correct closure command containing `--diff`, but the installed enforcement interface still accepts a closure validation without it, allowing implementation changes and closure metadata to land together without detection.

#### Root Cause

Security-relevant transition context is optional caller input rather than a mandatory property of validating a closed-record change.

**Closure diff has a nullable default** — `components/research-core/src/devforgeai/checkpoint/__main__.py:29-39`

The nullable range makes the closure-only oracle caller-optional.

```python
validate.add_argument("--diff", default=None,
                      help="Git range <base>..<head>; a diff that closes a record may touch closure paths only")
...
report = validate_plan(args.plan, git_root=args.git_root, schema_path=args.schema,
                       diff_range=args.diff)
```

#### Validation

Validation outcomes are recorded below.

Validation method: Committed an implementation change alongside closure metadata in a scratch Git repository and ran both invocation forms.

- **Status:** confirmed
- **Disposition:** reportable

**Closure diff has a nullable default** — `components/research-core/src/devforgeai/checkpoint/__main__.py:29-39`

The nullable range makes the closure-only oracle caller-optional.

```python
validate.add_argument("--diff", default=None,
                      help="Git range <base>..<head>; a diff that closes a record may touch closure paths only")
...
report = validate_plan(args.plan, git_root=args.git_root, schema_path=args.schema,
                       diff_range=args.diff)
```

Assertions:
- Without `--diff`, validation returned exit 0.
- With the exact range, S10 rejected the implementation change with exit 1.

Evidence:
- artifacts/05_findings/probe_optional_diff.py

#### Dataflow

Agent prepares mixed closure/implementation PR -\> invokes validator without range -\> S10 has no diff -\> PASS.

- **Source:** Caller omission

- **Sink:** Closure-only fence

- **Outcome:** Mixed change is accepted

**Closure diff has a nullable default** — `components/research-core/src/devforgeai/checkpoint/__main__.py:29-39`

The nullable range makes the closure-only oracle caller-optional.

```python
validate.add_argument("--diff", default=None,
                      help="Git range <base>..<head>; a diff that closes a record may touch closure paths only")
...
report = validate_plan(args.plan, git_root=args.git_root, schema_path=args.schema,
                       diff_range=args.diff)
```

#### Reachability

The worker or human can invoke the documented executable while omitting one optional flag; no protected state is modified.

- **Attacker:** Workspace agent

- **Entry point:** Protected CLI

- **Sink:** Closure decision

- **Outcome:** Self-accepting implementation change

Preconditions:
- Closure gate does not independently supply or require the range

**Closure diff has a nullable default** — `components/research-core/src/devforgeai/checkpoint/__main__.py:29-39`

The nullable range makes the closure-only oracle caller-optional.

```python
validate.add_argument("--diff", default=None,
                      help="Git range <base>..<head>; a diff that closes a record may touch closure paths only")
...
report = validate_plan(args.plan, git_root=args.git_root, schema_path=args.schema,
                       diff_range=args.diff)
```

#### Severity

**High** — The omission defeats the two-PR closure rule that keeps an AI-authored implementation from manufacturing its own acceptance evidence, directly weakening the framework's decision boundary.

Severity would fall if closure mode is derived from the record transition and requires a trusted base/head range supplied by the protected host rather than the workspace caller.

#### Remediation

Make transition validation explicit and mandatory. A protected host should derive or receive an independently pinned base/head pair, refuse a closure transition without it, and reject ranges not matching the reviewed PR base and head.

Tests:
- A closed-record transition without a range must exit 2 or 3, never 0.
- A wrong or caller-substituted range must fail closed.
- A closure-only range passes and a range containing any implementation path rejects.

Preventive controls:
- Represent validation mode and immutable base/head as protected invocation context rather than optional user flags.

<a id="finding-4"></a>

### [4] The proposed negative probe can corrupt the live control it tests

| Field | Value |
| --- | --- |
| Severity | medium |
| Confidence | high |
| Confidence rationale | The destructive commands are prescribed verbatim in the changed checkpoint and their failure mode follows directly from shell redirection semantics. |
| Category | unsafe security test |
| CWE | CWE-693 |
| Affected lines | docs/CHECKPOINT.md:20-23 |

#### Summary

PR 20 tells provider sessions to append bytes to `/usr/local/bin/devforge` and edit canonical staged validator/schema files. If root ownership or permissions are wrong—the exact condition being tested—the first operation corrupts the protected executable. An interrupted restore can also leave the repository modified or overwrite another session's changes.

#### Root Cause

The proof assumes the security control works before testing whether it works, so its failure path is mutating rather than observational.

#### Validation

Validation outcomes are recorded below.

Validation method: Reviewed the prescribed shell and repository mutations against their stated negative-test purpose.

- **Status:** confirmed
- **Disposition:** reportable

Assertions:
- A successful append means the test has already changed the executable.
- Canonical checkout edits require a restore and can collide with concurrent work.

Evidence:
- docs/CHECKPOINT.md:20-23

#### Dataflow

Probe shell redirection -\> writable live executable -\> appended byte -\> validator corruption.

- **Source:** Provider-run probe

- **Sink:** /usr/local/bin/devforge

- **Outcome:** Enforcement integrity loss

#### Reachability

The path is reached precisely when installation permissions are wrong; interruption can occur after mutation and before restoration.

- **Attacker:** Unprivileged provider session executing the approved probe

- **Entry point:** Committed probe script

- **Sink:** Live control or canonical repository files

- **Outcome:** Corruption or dirty state

Preconditions:
- The protection under test is broken or the probe is interrupted

#### Severity

**Medium** — Exploitation is limited to a deliberately run proof session, but failure causes integrity loss in the enforcement binary or shared workspace and can invalidate all later evidence.

Severity would fall to informational when probes use non-writing open checks or disposable root-owned canaries and mutate only synthetic isolated fixture repositories.

#### Remediation

For protected files, attempt a write-capable open without writing and close immediately; any successful open fails the probe while preserving bytes. Prefer a root-owned versioned canary when ACL behavior must be tested. Perform all project-local hostile mutations in provider-specific disposable fixture worktrees with traps and before/after digests; never edit the canonical checkout.

Tests:
- Misconfigured writable canary is detected while its digest stays unchanged.
- Abrupt probe termination leaves protected and canonical trees byte-identical.
- Claude and Codex use distinct clean worktrees pinned to the same commit.

Preventive controls:
- Require negative probes to be idempotent and non-destructive on both expected-pass and expected-fail paths.

## Reviewed Surfaces

| Surface | Risk Area | Outcome | Notes |
| --- | --- | --- | --- |
| Protected-release filesystem validation | Enforcement integrity | Reported | Missing resources and user-owned bytes pass the current validator. |
| Protected CLI policy selection | Configuration integrity | Reported | Caller-controlled schema and repository-root options remain exposed. |
| Closure-only diff fence | Workflow integrity | Reported | The enforcement check is skipped when an optional range is omitted. |
| Two-terminal negative probes | Test safety | Reported | The documented test mutates the live control and canonical sources on its failure path. |
| Slice-2 promotion manifest | Release provenance | Needs follow-up | The six listed files do not cover the wrapper, parent package, interpreter, dependencies, or an installed-layout release manifest. |
| Root-owned installation supply chain | Software supply chain | Needs follow-up | Claude's proposed root network pip install and live-checkout copies are not committed release bytes and were reviewed only from the supplied transcript. |

## Open Questions And Follow Up

- Will DevForge ship a self-contained binary or an offline hash-locked Python wheelhouse and release manifest?
  - Follow-up prompt: Review the exact DevForge release PR and installer for complete-byte provenance, atomic installation, root ownership, environment scrubbing, and fail-closed verification.
- No DevForge release commit, signed/tagged artifact, offline dependency bundle, protected installer, or installed system exists yet.
  - Follow-up prompt: Review deferred unit devforge-release-review and close its stated proof gap. Surfaces: surface_promotion_manifest, surface_root_install.
