# Installed layout specification (release layout contract v1)

The staged validator's rules CS-1.2 to CS-1.5 (`corrective-spec-001.md`) and DevForge's `RELEASE.sha256` both implement this layout. A record's `enforcement.protected_release` fields refer to it.

## Tree

```
<root>/                                  release root; every byte below is in RELEASE.sha256
  RELEASE.sha256                         sha256sum format, paths relative to <root>, never lists itself
  bin/devforge                           the executable named by executable_path (mode 0755)
  bin/devforge-checkpoint.py             launcher (mode 0755)
  lib/devforgeai/__init__.py             package parent
  lib/devforgeai/checkpoint/__init__.py
  lib/devforgeai/checkpoint/__main__.py
  lib/devforgeai/checkpoint/validate.py
  lib/<dependency packages>              installed with pip --no-index --require-hashes --target lib --no-compile
  schemas/devforgeai/v1/research-gap-checkpoint.schema.json   schema_set_sha256 is this file's digest
  contracts/MANIFEST.sha256              the promoted candidate manifest; contract_policy_sha256 is this file's digest
```

## Rules

1. **Release root** (CS-1.2): the parent of the executable's directory when that directory is named `bin`, otherwise the executable's directory. `executable_path` is therefore `<root>/bin/devforge`.
2. **Protected path** (CS-1.3): the executable, `RELEASE.sha256`, every listed file and every ancestor directory up to `/` are regular objects (no symbolic link anywhere in the chain), owned by uid 0, with no group or other write bit. Directories `0755`, files `0644`, the two executables `0755`. A virtualenv is forbidden: `venv` places symbolic links in `bin/`.
3. **Manifest** (CS-1.4): `RELEASE.sha256` lists every regular file under `<root>` except itself, in `sha256sum` format with `<root>`-relative paths; it must list `bin/devforge`, `schemas/devforgeai/v1/research-gap-checkpoint.schema.json` and `contracts/MANIFEST.sha256`. The validator rejects an unlisted file and a symbolic link anywhere under `<root>`. Do not install `__pycache__` (the launcher runs with `-B`; the tree is not writable anyway).
4. **Record binding** (CS-1.5): `executable_sha256`, `schema_set_sha256` and `contract_policy_sha256` equal the digests of the installed files above; `schema_set_version` and `contract_policy_version` equal the release version string; `version` is the DevForge tag; `source_commit` is the DevForge commit that carries the built tree.
5. **Interpreter and standard library** are out of `RELEASE.sha256`'s scope. The wrapper execs `/usr/bin/python3 -I -B -P` (ignore `PYTHONPATH` and user site, write no bytecode, no script-directory path entry) and scrubs `PATH`, `PYTHONPATH`, `PYTHONHOME`, `PYTHONSTARTUP` and `PYTHONUSERBASE`. The distro package that provides the interpreter is pinned in the permissions evidence: `dpkg -s python3.12 | grep -E '^(Package|Version)'` and `dpkg --verify python3.12 python3.12-minimal libpython3.12-stdlib` (empty output means unmodified). Another distro records the equivalent.
6. **Self-verification**: the installed validator detects installed mode from `RELEASE.sha256` above its own module and verifies the whole tree under rules 2–3 before reading any record; a failure is `COULD_NOT_RUN` (exit 3). A user-owned copy of the tree therefore cannot validate anything.
7. **Invocation**: always by absolute path. `bin/devforge` refuses a relative invocation (`./bin/devforge`, a relative `PATH` entry) with exit 2. A bare name through an absolute `PATH` entry arrives as an absolute `$0` and cannot be distinguished; that is exactly why hooks and probes must call the recorded absolute path, since a same-name shadow earlier in `PATH` would otherwise be run instead (CS-4.3).
8. **Evidence files** named by `promotion_evidence_path` and `permissions_evidence_path` live in the dossier (repository-relative) or at an absolute path; both are mandatory and digest-bound; neither is under `<root>`.

## Permissions evidence (captured as the unprivileged agent user, never as root)

```bash
V=<version>; R=/usr/local/lib/devforge/$V
{ echo "# permissions evidence $(date -u +%FT%TZ) host=$(hostname) user=$(id -un)"
  stat -c '%u:%g %a %F %n' / /usr /usr/local /usr/local/lib /usr/local/lib/devforge $R $R/bin/devforge $R/RELEASE.sha256
  echo "objects under $R not owned by uid 0 or group/other-writable (must be none):"
  find $R \( ! -uid 0 -o -perm /022 \) -printf '%u %m %p\n'
  echo "symbolic links under $R (must be none):"; find $R -type l
  sudo -n true 2>&1; echo "sudo -n exit $?"
  dpkg -s python3.12 | grep -E '^(Package|Version)'; dpkg --verify python3.12 python3.12-minimal libpython3.12-stdlib; echo "dpkg --verify exit $?"
  sha256sum $R/bin/devforge $R/schemas/devforgeai/v1/research-gap-checkpoint.schema.json $R/contracts/MANIFEST.sha256 $R/RELEASE.sha256
} > permissions.txt
```

The validator reads none of this as proof (CS-1.6); it inspects the filesystem itself. The evidence is for the human reviewer and the closure record.
