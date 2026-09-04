# Corrective specification 001 — fail-closed release pin, no caller overrides, mandatory closure range, non-destructive probes

| Field | Value |
|---|---|
| Checkpoint | `CP-00` of `SDD-GAP-CLOSURE-2026-09-03` (amended by `SDD-GAP-AMD-001`, scope amendment `SDD-GAP-CP00-SCOPE-001`) |
| Trigger | Codex security review of PR 20, `reviews/codex-security-2026-09-04/` (findings 1–4) and the owner's reproduction (`reproduction.txt`), decision D-CP00-11 |
| Supersedes | check-in 19 steps 2 and 3; the "digests compared only when the paths exist" limitation of the first CP-00 record |
| Method | red first: every statement below has a hostile test that fails on the candidate `c784ab7` (`probes/red-corrective-001.txt`), then the fix, then the same tests green |
| Platform | POSIX only. Ownership and mode rules are stated in POSIX terms; another operating system needs its own accepted realization (plan section 4.2). |

Each statement is numbered `CS-<finding>.<n>` and names its test in `tests/research/test_gap_checkpoints.py` (or `components/devforge-release/tests/`).

## CS-1 Release pin is fail-closed (finding 1, rule S06.9)

A record whose `enforcement.trust_stage` is `PROTECTED_RELEASE`, or whose `closure_stages.proven` is `PASS`, or which is `closed: true`, is accepted only when every statement holds. Any failure is a rejection (exit 1), never a skip.

- **CS-1.1 Every release resource is mandatory.** `executable_path`, `promotion_evidence_path` and `permissions_evidence_path` must exist as regular files. Absence rejects. Test: `test_missing_executable_rejected`, `test_missing_promotion_evidence_rejected`.
- **CS-1.2 Release root rule.** The release root is the parent of the executable's directory when that directory is named `bin`, otherwise the executable's directory. `<root>/RELEASE.sha256` must exist. Test: `test_missing_release_manifest_rejected`.
- **CS-1.3 Protected path rule.** For the executable, `RELEASE.sha256`, every file `RELEASE.sha256` lists, and every ancestor directory of each of them up to `/`: `lstat` succeeds; the object is not a symbolic link; its owner uid is 0; its mode grants no group or other write (`mode & 0o022 == 0`). Tests: `test_user_owned_executable_rejected`, `test_group_writable_executable_rejected`, `test_symlinked_executable_rejected`, `test_writable_ancestor_rejected`.
- **CS-1.4 Release manifest verification.** `RELEASE.sha256` has the `sha256sum` line format with paths relative to the release root; it does not list itself; every entry exists, verifies and satisfies CS-1.3; every regular file under the release root except `RELEASE.sha256` is listed (reverse walk). It must list `bin/devforge` (the executable, by its path relative to the root), `schemas/devforgeai/v1/research-gap-checkpoint.schema.json` and `contracts/MANIFEST.sha256`. Tests: `test_release_manifest_entry_tampered_rejected`, `test_unlisted_release_file_rejected`, `test_release_manifest_without_schema_rejected`.
- **CS-1.5 Record digests bind to installed bytes.** `executable_sha256` equals the digest of the executable; `schema_set_sha256` equals the digest of the installed schema; `contract_policy_sha256` equals the digest of the installed `contracts/MANIFEST.sha256`; `promotion_evidence_sha256` and `permissions_evidence_sha256` equal the digests of their files. Tests: `test_executable_digest_mismatch_rejected`, `test_schema_set_digest_mismatch_rejected`, `test_contract_policy_digest_mismatch_rejected`, `test_promotion_evidence_digest_mismatch_rejected`.
- **CS-1.6 `installation_owner` is a declaration, not evidence.** The validator never reads it as proof; CS-1.3 decides. No test beyond CS-1.3.
- **CS-1.7 Positive case through a seam.** The validator's filesystem view of protected paths is an injectable interface (`validate_plan(..., release_fs=...)`) used only in-process by tests; the CLI exposes no flag, environment variable or file that selects it. The true positive integration test is DevForge's two-terminal probe against a real root-owned install and cannot run in this repository (limitation on the record). Tests: `test_complete_closed_record_passes`, `test_research_only_disposition_passes`, `test_closure_only_diff_passes` run in-process with a fake that reports uid 0 and masked write bits for the fixture's release tree; `test_no_seam_from_the_cli` proves the subprocess path rejects the same user-owned fixture.

## CS-2 No caller-selected policy (finding 2)

- **CS-2.1** The CLI accepts exactly `validate --plan <dir> [--diff <base>..<head>] [--json]`. `--schema`, `--git-root`, any abbreviation and any unknown option exit 2 before validation. Tests: `test_schema_option_rejected`, `test_git_root_option_rejected`.
- **CS-2.2 Schema resolution never consults the plan's tree.** Installed mode: the validator module lies under a release root (a `RELEASE.sha256` above the module); the schema is `<root>/schemas/devforgeai/v1/research-gap-checkpoint.schema.json`, and the release manifest is verified under CS-1.3/CS-1.4 before any record is read (failure exits 3). Staged mode: the module lies in a checkout; the schema is resolved above the module's own location only. The former walk over the plan's ancestors is removed. Test: `test_schema_from_plan_tree_ignored` (a permissive schema placed above the plan does not change a rejection).
- **CS-2.3 Git root derives from the plan only.** `git -C <plan> rev-parse --show-toplevel`; a plan not inside a work tree exits 3; a plan whose resolved path is not under that root exits 3 (closes the `ValueError` traceback). Test: `test_plan_outside_git_is_could_not_run` (kept), `test_git_root_option_rejected`.

## CS-3 Closure range is mandatory (finding 3, rule S10)

- **CS-3.1** When any record of the plan is `closed: true` and no `--diff` is given, the CLI exits 2 with `usage: closure validation requires --diff <base>..<head>`; the library raises `RangeRequired`. Test: `test_closed_record_without_diff_rejected`.
- **CS-3.2** The range's head must resolve to `HEAD` of the plan's repository, and its base must be a proper ancestor of that head; otherwise S10 rejects (exit 1). Tests: `test_diff_head_not_head_rejected`, `test_diff_base_not_ancestor_rejected`.
- **CS-3.3** Consequence, recorded as a limitation: once any record of a plan is closed, every validation of that plan, including CI, must supply the range; a trusted base/head pair supplied by the protected host rather than the caller remains DevForge work.

## CS-4 Probes are non-destructive (finding 4; design only, no script in this PR)

- **CS-4.1** Write-denial is proven with `os.open(path, os.O_WRONLY)` expecting `EACCES`/`EPERM`; a successful open is closed immediately without writing and fails the probe. No probe ever appends to, truncates or renames a protected file.
- **CS-4.2** Project-local hostile mutations (a permissive schema, a stubbed validator, a tampered record) happen only in a disposable per-provider fixture worktree created from the same commit, under a shell `trap` that removes it; the canonical checkout is never edited. Before and after digests of the protected tree and `git status --short` of the canonical checkout are retained.
- **CS-4.3** The PATH-shadow proof places a shadow executable in a temporary directory and calls the protected executable by absolute path; the bare-name call is run only to show the shadow would be hit.
- **CS-4.4** The probe script and its prompt are written in the evidence PR after this corrective PR passes independent exact-head review (D-CP00-11).

## CS-5 Staged release scaffold (`components/devforge-release/`, scope amendment 001)

- **CS-5.1** The candidate manifest `framework/contracts/MANIFEST.sha256` pins every file under `components/devforge-release/` plus the validator package, its parent package file `components/research-core/src/devforgeai/__init__.py`, the schema, the tests and the declaration. Rule S13's coverage check enforces the fence part; `gen_contracts.py` globs the component. Test: `test_repository_plan_records_hold` after the pin.
- **CS-5.2** `INSTALLED-LAYOUT.md` is the installed-layout specification the validator's CS-1.2/CS-1.4 rules implement: `<root>/bin/devforge`, `<root>/bin/devforge-checkpoint.py` (launcher), `<root>/lib/` (the `devforgeai` package and the dependency packages installed with `pip install --no-index --require-hashes --target`), `<root>/schemas/devforgeai/v1/`, `<root>/contracts/MANIFEST.sha256`, `<root>/RELEASE.sha256`; no virtualenv (a venv puts symlinks in `bin/`, forbidden by CS-1.3); the interpreter is the distro's `/usr/bin/python3` invoked with `-I -B -P`, pinned by distro package name and version in the permissions evidence, and is out of `RELEASE.sha256`'s scope, which covers every byte under the release root.
- **CS-5.3** Dependencies: `requirements.lock` with `--hash` for every wheel; the wheels themselves under `wheels/`; `wheels/PROVENANCE.md` records for each wheel the PyPI URL, the digest PyPI publishes, the locally computed digest, the download command and date. Test: `test_lockfile_hashes_match_wheels` (component tests).
- **CS-5.4** `gen_release_manifest.py` writes `RELEASE.sha256` for an installed tree and is never the verifier; `verify-release.sh` verifies with coreutils only (`sha256sum -c`, `stat`, `find -type l`) and is the independent check a human runs after installation. Test: `test_generator_and_verifier_disagree_on_tamper`.
- **CS-5.5** `install.sh` consumes only an immutable DevForge release archive plus its `RELEASE.sha256`: verifies every entry before copying, refuses an existing target, installs into a temporary sibling, sets `root:root` and modes, renames atomically; it never calls `pip` with an index, never touches the network, and refuses to run from inside a DevForgeAI checkout. It is candidate source; only the human runs it, from the DevForge release. Tests: `test_installer_refuses_tampered_release`, `test_installer_refuses_existing_target` (run unprivileged into a scratch target; ownership steps are skipped when not root and reported).
- **CS-5.6** Everything under the component is `STAGED_CANDIDATE` bytes. Passing these tests makes nothing protected; DevForge reviews the exact candidate, builds the release, writes its own `RELEASE.sha256`, and the promotion record maps candidate manifest digest → DevForge commit/tag → release manifest digest.

## Red run

`probes/red-corrective-001.txt` records the test run on candidate `c784ab7` with the CS-1 to CS-3 tests added and nothing fixed: every new test fails on its assertion (exit code or message), every pre-existing test passes.
