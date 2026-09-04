# devforge-release: staged release scaffold for the checkpoint validator (CP-00)

**Status: `STAGED_CANDIDATE`. Nothing here is protected, and nothing here installs anything.** This directory exists so that every byte a protected DevForge release of `devforge checkpoint validate` executes or imports is reviewed, pinned and reproducible from DevForgeAI, per CP-00 scope amendment `SDD-GAP-CP00-SCOPE-001` (dossier decision D-CP00-10), corrective specification 001 (`docs/research/sdd-checkpoint-custody/corrective-spec-001.md`, CS-5) and corrective specification 002 (`corrective-spec-002.md`, CS-6 to CS-10, after the PR 22 review).

## Boundaries (decision authority rulings, 2026-09-04)

- Everything under this directory remains a `STAGED_CANDIDATE`; it never becomes protected merely by passing DevForgeAI tests.
- Two distinct manifests. The DevForgeAI **candidate manifest** (`framework/contracts/MANIFEST.sha256`) pins the launcher source, toolchain pin, build script and build digest, installer, package parent and validator modules, schemas and policy, dependency lockfile and offline artifacts, installed-layout specification, manifest and identity generators, and the positive and hostile tests. The DevForge **`RELEASE.sha256`** pins the final installed payload, and DevForge's **`RELEASE-IDENTITY.json`** maps candidate checkpoint, source commit and manifest digest → DevForge commit and tag → release version. A promotion record repeats that mapping with the `RELEASE.sha256` digest.
- No unpinned glue. No network access during root installation. Third-party wheels carry recorded provenance and hashes (`wheels/PROVENANCE.md`, `requirements.lock`); the launcher has no third-party crates. The manifest generator cannot validate its own output; `verify-release.sh` (coreutils only) is the independent check. DevForgeAI never installs into `/usr/local`. Only the human promotes the reviewed bytes into DevForge. Claude and Codex have no write credentials or writable checkout for DevForge. The root installer consumes only the immutable DevForge release.
- `devforge` is the permanent Rust trust-boundary binary (D-CP00-13). Today `checkpoint validate` delegates to the Python validator inside the release; later the validator moves behind the same binary without changing hooks or invocation. `checkpoint attest` is already the binary's own.

## Contents

| Path | Role | Pinned by |
|---|---|---|
| `INSTALLED-LAYOUT.md` | the installed-layout specification (release layout contract v2) the validator's rules S06.9 and S14 implement | candidate manifest |
| `launcher/` | the `devforge` binary: `Cargo.toml`, `Cargo.lock` (one package, no dependencies), `rust-toolchain.toml` (channel and musl target), `.cargo/config.toml` (static, non-PIE, path-remapped), `src/main.rs`, `src/sha256.rs`, `build.sh`, `BUILD-DIGEST.txt` (compiler identity, flags, binary digest) | candidate manifest; built binary in `RELEASE.sha256` |
| `bin/devforge-checkpoint.py` | Python launcher: puts `<root>/lib` first on `sys.path` and runs `devforgeai.checkpoint`; only ever started by the binary with `-I -B -P` and a cleared environment | candidate manifest; installed copy in `RELEASE.sha256` |
| `requirements.lock` | every dependency with `--hash=sha256:…`, consumed with `--no-index --require-hashes` | candidate manifest |
| `wheels/*.whl`, `wheels/PROVENANCE.md` | the offline artifacts and, per wheel, the PyPI URL, PyPI-published digest, locally computed digest, download command and date | candidate manifest |
| `gen_release_identity.py` | writes `RELEASE-IDENTITY.json` from explicit arguments and the candidate manifest's digest; validates it against the schema | candidate manifest |
| `gen_release_manifest.py` | writes `RELEASE.sha256` for a built tree; refuses symlinks, a missing required entry or a non-static `bin/devforge`; never verifies | candidate manifest |
| `verify-release.sh` | independent verification of an installed tree with `sha256sum`, `stat`, `find` only: digests, symlinks, coverage, required entries, exact modes, ownership | candidate manifest |
| `install.sh` | root installer for an immutable DevForge release directory: requires the verifier beside it, verifies, refuses an existing target, installs to a temporary sibling, sets ownership and modes, renames atomically, re-verifies; no `pip`, no network | candidate manifest |
| `tests/test_devforge_release.py` | positive and hostile tests for the launcher (static ELF, exact environment, `LD_PRELOAD`/`LD_AUDIT` inert, root from `/proc/self/exe`, attest dry-run), generator, verifier and installer, all unprivileged in scratch trees | candidate manifest |
| `../research-core/src/devforgeai/__init__.py`, `checkpoint/*.py` | the package parent and validator modules the release copies into `<root>/lib/devforgeai/` | candidate manifest |
| `../../schemas/devforgeai/v1/research-gap-checkpoint.schema.json`, `release-identity.schema.json`, `closure-attestation.schema.json`, `../../framework/contracts/MANIFEST.sha256` | the schemas and policy the release copies into `<root>/schemas/…` and `<root>/contracts/` | candidate manifest |

## How DevForge builds a release from the reviewed candidate (human, in the DevForge repository)

```bash
# 1. exact candidate: every line OK, digest of the manifest equals the CP-00 record's candidate.manifest_sha256
sha256sum -c framework/contracts/MANIFEST.sha256
# 2. launcher: pinned toolchain (rust-toolchain.toml), locked, offline; must reproduce BUILD-DIGEST.txt
sh components/devforge-release/launcher/build.sh
# 3. build tree (any scratch directory; nothing is installed)
B=/path/to/build/devforge-<version>
mkdir -p $B/bin $B/lib/devforgeai/checkpoint $B/schemas/devforgeai/v1 $B/contracts
cp components/devforge-release/launcher/target/x86_64-unknown-linux-musl/release/devforge $B/bin/devforge
cp components/devforge-release/bin/devforge-checkpoint.py $B/bin/
cp components/research-core/src/devforgeai/__init__.py $B/lib/devforgeai/
cp components/research-core/src/devforgeai/checkpoint/{__init__,__main__,validate}.py $B/lib/devforgeai/checkpoint/
cp schemas/devforgeai/v1/{research-gap-checkpoint,release-identity,closure-attestation}.schema.json $B/schemas/devforgeai/v1/
cp framework/contracts/MANIFEST.sha256 $B/contracts/MANIFEST.sha256
python3 -m pip install --no-index --find-links components/devforge-release/wheels --require-hashes \
  -r components/devforge-release/requirements.lock --target $B/lib --no-compile
find $B -name __pycache__ -type d -exec rm -r {} +
# 4. identity, then the release manifest, then independent verification of the build tree
python3 components/devforge-release/gen_release_identity.py --root $B --version <version> \
  --devforge-commit <DevForge commit> --devforge-tag <tag> --candidate-repository https://github.com/bankielewicz/DevForgeAI \
  --candidate-checkpoint CP-00 --candidate-source-commit <CP-00 candidate.source_commit> \
  --candidate-manifest framework/contracts/MANIFEST.sha256 --launcher-toolchain "$(rustc -V)"
python3 components/devforge-release/gen_release_manifest.py $B
components/devforge-release/verify-release.sh $B     # OWNERSHIP FAILs on a user-owned build tree; every other line must be OK
```

The DevForge repository commits the build tree, tags it, and records the promotion: candidate manifest digest, DevForge commit and tag, `RELEASE-IDENTITY.json` and `RELEASE.sha256` digests, and whether `build.sh` reproduced `BUILD-DIGEST.txt`. That record is the `promotion_evidence_path` of the CP-00 closure.

## How the human installs the DevForge release (root, from the immutable release only)

```bash
sudo components/devforge-release/install.sh --release /path/to/immutable/devforge-<version> --root /usr/local/lib/devforge/<version>
components/devforge-release/verify-release.sh /usr/local/lib/devforge/<version>
/usr/local/lib/devforge/<version>/bin/devforge checkpoint validate --plan docs/research/spec-driven-development-gap-closure
```

`install.sh` is run from the DevForge release checkout the human controls, never from a DevForgeAI worktree, and it refuses a release directory that looks like a DevForgeAI checkout. The interpreter is the distro's `/usr/bin/python3` and Git is `/usr/bin/git`; their package names and versions go into the permissions evidence (`INSTALLED-LAYOUT.md`).

## How a checkpoint closes (attestation, CS-9)

After the closure PR's head is frozen and independently reviewed, the human mints the attestation as root; the validator takes the closure range from it and refuses a closed record without one:

```bash
sudo /usr/local/lib/devforge/<version>/bin/devforge checkpoint attest --repo /path/to/DevForgeAI \
  --plan docs/research/spec-driven-development-gap-closure --checkpoint CP-00 \
  --base <PR base sha> --head <PR head sha> --authority github:bankielewicz --review <PR review URL>
# prints the attestation path under /var/lib/devforge/attest/ and its sha256; record the digest in the PR review
```

`--dry-run` prints the document without writing (no root needed). `--repo` must be the checkout root (the minter names it in `safe.directory` because it runs as uid 0 over the agent user's checkout). An existing attestation is never overwritten; a new review removes it explicitly first. A plan id or checkpoint id that is not a safe path component is refused (CS-9.7).

## Tests

```bash
python3 -m pytest components/devforge-release/tests -q
```

Unprivileged: every test builds scratch trees under a temporary directory; the launcher is built once per session with the pinned toolchain (`cargo build --release --locked --target x86_64-unknown-linux-musl`). The positive protected case (a root-owned tree accepted by the validator) and a real root-minted attestation cannot run here; they are DevForge's two-terminal probe.
