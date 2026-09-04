# Installed layout specification (release layout contract v2)

The staged validator's rules S06.9 and S14 (`corrective-spec-001.md` CS-1, `corrective-spec-002.md` CS-6, CS-9), DevForge's `RELEASE.sha256`, `gen_release_manifest.py`, `verify-release.sh` and `install.sh` all implement this layout, with the same required-entry list and the same modes. A record's `enforcement.protected_release` fields refer to it. Contract v1 (a shell wrapper, no identity file, a caller-supplied closure range) was not confirmed by the PR 22 review and is withdrawn.

## Tree

```
<root>/                                  release root; every byte below is in RELEASE.sha256
  RELEASE.sha256                         sha256sum format, paths relative to <root>, never lists itself
  RELEASE-IDENTITY.json                  release identity (schema release-identity.schema.json); never names RELEASE.sha256's digest
  bin/devforge                           the executable named by executable_path: a static Rust binary (mode 0755)
  bin/devforge-checkpoint.py             Python launcher the binary execs through /usr/bin/python3 -I -B -P (mode 0755)
  lib/devforgeai/__init__.py             package parent
  lib/devforgeai/checkpoint/__init__.py
  lib/devforgeai/checkpoint/__main__.py
  lib/devforgeai/checkpoint/validate.py
  lib/<dependency packages>              installed with pip --no-index --require-hashes --target lib --no-compile
  schemas/devforgeai/v1/research-gap-checkpoint.schema.json   schema_set_sha256 is this file's digest
  schemas/devforgeai/v1/release-identity.schema.json
  schemas/devforgeai/v1/closure-attestation.schema.json
  contracts/MANIFEST.sha256              the promoted candidate manifest; contract_policy_sha256 is this file's digest
```

Outside the release, owned by root, written only by `devforge checkpoint attest`:

```
/var/lib/devforge/attest/<repository identity[:32]>/<plan id>/<checkpoint id>.json   closure attestation (schema closure-attestation.schema.json)
```

## Rules

1. **Release root and executing root** (CS-1.2, CS-6.1, CS-6.2): the release root is the parent of `bin/`. The validator that decides a closed record is the one installed under a verified root `R`; it accepts a record only when `executable_path` equals `<R>/bin/devforge` exactly. A validator running from a checkout rejects every closed record (condition 9 is not decidable there).
2. **Protected path** (CS-1.3): the executable, `RELEASE.sha256`, every listed file, the attestation file and every ancestor directory up to `/` are regular objects (no symbolic link anywhere in the chain), owned by uid 0, with no group or other write bit. Modes are exact: directories `0755`, files `0644`, `bin/devforge` and `bin/devforge-checkpoint.py` `0755` (`verify-release.sh` prints `MODES`). A virtualenv is forbidden: `venv` places symbolic links in `bin/`.
3. **Manifest** (CS-1.4, CS-10.2): `RELEASE.sha256` lists every regular file under `<root>` except itself, in `sha256sum` format with `<root>`-relative paths, and must list the seven required entries: `bin/devforge`, `bin/devforge-checkpoint.py`, `RELEASE-IDENTITY.json`, the three schemas, `contracts/MANIFEST.sha256`. The generator refuses a tree missing any of them, containing a symbolic link or `__pycache__`, or whose `bin/devforge` is not a static ELF. The validator rejects an unlisted file and a symbolic link anywhere under `<root>`.
4. **Release identity** (CS-6.3, CS-6.4): `RELEASE-IDENTITY.json` carries `version`, `devforge_commit`, `devforge_tag`, `candidate_repository`, `candidate_checkpoint_id`, `candidate_source_commit`, `candidate_manifest_sha256`, `schema_set_version`, `contract_policy_version`, `launcher_toolchain`, `built_at`. For every closed record `protected_release.version`, `source_commit`, `schema_set_version`, `contract_policy_version` equal the identity's, and `contract_policy_sha256` equals `candidate_manifest_sha256` (the installed policy *is* the promoted candidate manifest). For the record named by `candidate_checkpoint_id`, `enforcement.candidate` equals the identity's candidate commit and manifest digest. `executable_sha256` and `schema_set_sha256` equal the digests of the installed files.
5. **Launcher** (CS-8): `bin/devforge` is a statically linked ELF for `x86_64-unknown-linux-musl` (no `PT_INTERP`, no `DT_NEEDED`) built from `launcher/` with the pinned toolchain; its digest is pinned in `launcher/BUILD-DIGEST.txt`. It refuses a relative `argv[0]`, derives `<root>` from `/proc/self/exe`, clears the environment and execs `/usr/bin/python3 -I -B -P <root>/bin/devforge-checkpoint.py` with exactly `PATH=/usr/bin:/bin`, `LC_ALL=C.UTF-8`, `LANG=C.UTF-8`. `LD_PRELOAD` and `LD_AUDIT` never run code in its process. The Python validator behind it is a temporary delegate; it moves behind the same binary without changing hooks or invocation (D-CP00-13).
6. **Interpreter and standard library** are out of `RELEASE.sha256`'s scope. The distro package that provides `/usr/bin/python3` and the one that provides `/usr/bin/git` are pinned in the permissions evidence: `dpkg -s python3.12 git | grep -E '^(Package|Version)'` and `dpkg --verify python3.12 python3.12-minimal libpython3.12-stdlib git` (empty output means unmodified). Another distro records the equivalent.
7. **Self-verification** (CS-2.2): the installed validator detects installed mode from `RELEASE.sha256` above its own module and verifies the whole tree under rules 2–3 before reading any record; a failure is `COULD_NOT_RUN` (exit 3). A user-owned copy of the tree therefore cannot validate anything.
8. **Git** (CS-7.1): the validator and the launcher run `/usr/bin/git` with an explicit environment (`PATH=/usr/bin:/bin`, `HOME=/nonexistent`, `LC_ALL=C`, `GIT_CONFIG_GLOBAL=/dev/null`, `GIT_CONFIG_SYSTEM=/dev/null`, `GIT_CONFIG_NOSYSTEM=1`, `GIT_TERMINAL_PROMPT=0`), plumbing only. Workspace-resident Git state stays agent-writable and is defused by the attestation and the identity binding (CS-7.2).
9. **Closure attestation** (CS-9): after the closure PR head is frozen and independently reviewed, the human runs, as root, `<R>/bin/devforge checkpoint attest --repo <checkout> --plan <plan path> --checkpoint CP-NN --base <PR base sha> --head <PR head sha> --authority <decision authority id> --review <review reference>`. The binary resolves both commits through the sanitized Git, requires base to be a proper ancestor of head, digests the record blob at head and `<R>/RELEASE-IDENTITY.json`, and writes the document with `create_new` (never overwrites) under `0755` directories with mode `0644`. It prints the document's digest, which the human records in the PR review. The validator's S14 reads only this location; `--diff`, when given, must equal the attested range. Any later change to the head, the record, the candidate or the release invalidates the attestation: the human removes it and a new independent review mints a new one.
10. **Invocation**: always by absolute path. A bare name through an absolute `PATH` entry arrives with an absolute `argv[0]` and cannot be distinguished; that is exactly why hooks and probes must call the recorded absolute path, since a same-name shadow earlier in `PATH` would otherwise be run instead (CS-4.3).
11. **Evidence files** named by `promotion_evidence_path` and `permissions_evidence_path` live in the dossier (repository-relative) or at an absolute path; both are mandatory and digest-bound; neither is under `<root>`.

## Permissions evidence (captured as the unprivileged agent user, never as root)

```bash
V=<version>; R=/usr/local/lib/devforge/$V; A=/var/lib/devforge/attest
{ echo "# permissions evidence $(date -u +%FT%TZ) host=$(hostname) user=$(id -un)"
  stat -c '%u:%g %a %F %n' / /usr /usr/local /usr/local/lib /usr/local/lib/devforge $R $R/bin/devforge $R/RELEASE.sha256 $R/RELEASE-IDENTITY.json /var /var/lib /var/lib/devforge $A
  echo "objects under $R and $A not owned by uid 0 or group/other-writable (must be none):"
  find $R $A \( ! -uid 0 -o -perm /022 \) -printf '%u %m %p\n'
  echo "symbolic links under $R and $A (must be none):"; find $R $A -type l
  sudo -n true 2>&1; echo "sudo -n exit $?"
  dpkg -s python3.12 git | grep -E '^(Package|Version)'; dpkg --verify python3.12 python3.12-minimal libpython3.12-stdlib git; echo "dpkg --verify exit $?"
  sha256sum $R/bin/devforge $R/RELEASE-IDENTITY.json $R/schemas/devforgeai/v1/research-gap-checkpoint.schema.json $R/contracts/MANIFEST.sha256 $R/RELEASE.sha256
} > permissions.txt
```

The validator reads none of this as proof (CS-1.6); it inspects the filesystem itself. The evidence is for the human reviewer and the closure record.
