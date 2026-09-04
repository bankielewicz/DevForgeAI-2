# devforge-release: staged release scaffold for the checkpoint validator (CP-00)

**Status: `STAGED_CANDIDATE`. Nothing here is protected, and nothing here installs anything.** This directory exists so that every byte a protected DevForge release of `devforge checkpoint validate` executes or imports is reviewed, pinned and reproducible from DevForgeAI, per CP-00 scope amendment `SDD-GAP-CP00-SCOPE-001` (dossier decision D-CP00-10) and corrective specification 001 (`docs/research/sdd-checkpoint-custody/corrective-spec-001.md`, CS-5).

## Boundaries (decision authority ruling, 2026-09-04)

- Everything under this directory remains a `STAGED_CANDIDATE`; it never becomes protected merely by passing DevForgeAI tests.
- Two distinct manifests. The DevForgeAI **candidate manifest** (`framework/contracts/MANIFEST.sha256`) pins the wrapper source, installer, package parent and validator modules, schema and policy, dependency lockfile and offline artifacts, installed-layout specification, manifest generator, and the positive and hostile tests. The DevForge **`RELEASE.sha256`** pins the final installed payload. A promotion record maps candidate manifest digest → DevForge commit/tag → release manifest digest.
- No unpinned glue. No network access during root installation. Third-party wheels carry recorded provenance and hashes (`wheels/PROVENANCE.md`, `requirements.lock`). The manifest generator cannot validate its own output; `verify-release.sh` (coreutils only) is the independent check. DevForgeAI never installs into `/usr/local`. Only the human promotes the reviewed bytes into DevForge. Claude and Codex have no write credentials or writable checkout for DevForge. The root installer consumes only the immutable DevForge release.

## Contents

| Path | Role | Pinned by |
|---|---|---|
| `INSTALLED-LAYOUT.md` | the installed-layout specification the validator's rules CS-1.2 to CS-1.5 implement | candidate manifest |
| `bin/devforge` | wrapper source: refuses a relative invocation, scrubs the environment, execs the distro interpreter with `-I -B -P` on the launcher | candidate manifest; installed copy in `RELEASE.sha256` |
| `bin/devforge-checkpoint.py` | launcher: puts `<root>/lib` first on `sys.path` and runs `devforgeai.checkpoint` | same |
| `requirements.lock` | every dependency with `--hash=sha256:…`, consumed with `--no-index --require-hashes` | candidate manifest |
| `wheels/*.whl`, `wheels/PROVENANCE.md` | the offline artifacts and, per wheel, the PyPI URL, PyPI-published digest, locally computed digest, download command and date | candidate manifest |
| `gen_release_manifest.py` | writes `RELEASE.sha256` for a built tree; refuses symlinks; never verifies | candidate manifest |
| `verify-release.sh` | independent verification of an installed tree with `sha256sum`, `stat`, `find` only | candidate manifest |
| `install.sh` | root installer for an immutable DevForge release directory: verifies, refuses an existing target, installs to a temporary sibling, sets ownership and modes, renames atomically; no `pip`, no network | candidate manifest |
| `tests/test_devforge_release.py` | positive and hostile tests for the generator, verifier, installer, wrapper and launcher, all unprivileged in scratch trees | candidate manifest |
| `../research-core/src/devforgeai/__init__.py`, `checkpoint/*.py` | the package parent and validator modules the release copies into `<root>/lib/devforgeai/` | candidate manifest |
| `../../schemas/devforgeai/v1/research-gap-checkpoint.schema.json`, `../../framework/contracts/MANIFEST.sha256` | the schema and policy the release copies into `<root>/schemas/…` and `<root>/contracts/` | candidate manifest |

## How DevForge builds a release from the reviewed candidate (human, in the DevForge repository)

```bash
# 1. exact candidate: every line OK, digest of the manifest equals the CP-00 record's candidate.manifest_sha256
sha256sum -c framework/contracts/MANIFEST.sha256
# 2. build tree (any scratch directory; nothing is installed)
B=/path/to/build/devforge-<version>
mkdir -p $B/bin $B/lib $B/schemas/devforgeai/v1 $B/contracts
cp components/devforge-release/bin/devforge components/devforge-release/bin/devforge-checkpoint.py $B/bin/
mkdir -p $B/lib/devforgeai/checkpoint
cp components/research-core/src/devforgeai/__init__.py $B/lib/devforgeai/
cp components/research-core/src/devforgeai/checkpoint/{__init__,__main__,validate}.py $B/lib/devforgeai/checkpoint/
cp schemas/devforgeai/v1/research-gap-checkpoint.schema.json $B/schemas/devforgeai/v1/
cp framework/contracts/MANIFEST.sha256 $B/contracts/MANIFEST.sha256
python3 -m pip install --no-index --find-links components/devforge-release/wheels --require-hashes \
  -r components/devforge-release/requirements.lock --target $B/lib --no-compile
find $B -name __pycache__ -type d -exec rm -r {} +
# 3. release manifest, then independent verification of the build tree
python3 components/devforge-release/gen_release_manifest.py $B
components/devforge-release/verify-release.sh $B     # ownership lines will FAIL on a user-owned build tree; digests, symlinks and coverage must be OK
```

The DevForge repository commits the build tree, tags it, and records the promotion: candidate manifest digest, DevForge commit and tag, `RELEASE.sha256` digest. That record is the `promotion_evidence_path` of the CP-00 closure.

## How the human installs the DevForge release (root, from the immutable release only)

```bash
sudo components/devforge-release/install.sh --release /path/to/immutable/devforge-<version> --root /usr/local/lib/devforge/<version>
/usr/local/lib/devforge/<version>/bin/devforge checkpoint validate --plan docs/research/spec-driven-development-gap-closure --diff <base>..<head>
components/devforge-release/verify-release.sh /usr/local/lib/devforge/<version>
```

`install.sh` is run from the DevForge release checkout the human controls, never from a DevForgeAI worktree, and it refuses a release directory that looks like a DevForgeAI checkout. The interpreter is the distro's `/usr/bin/python3`; its package name and version go into the permissions evidence (`INSTALLED-LAYOUT.md`).

## Tests

```bash
python3 -m pytest components/devforge-release/tests -q
```

Unprivileged: every test builds scratch trees under a temporary directory. The positive protected case (a root-owned tree accepted by the validator) cannot run here; it is DevForge's two-terminal probe.
