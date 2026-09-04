#!/bin/sh
# install.sh --release <dir> --root <target>
#
# Root installer for an immutable DevForge release directory (INSTALLED-LAYOUT.md).
# STAGED CANDIDATE source in DevForgeAI; the human runs the promoted copy from the
# DevForge release, never from a DevForgeAI worktree. It:
#   1. refuses a release that looks like a DevForgeAI checkout, a release without
#      RELEASE.sha256, or an existing target;
#   0. refuses to run without verify-release.sh beside it (CS-10.1);
#   2. verifies every entry, the absence of symbolic links, full coverage and the
#      required layout-v2 entries before copying anything (sha256sum, find; no
#      python, no pip, no network);
#   3. copies into a temporary sibling of the target, sets root:root and modes,
#      then renames atomically into place;
#   4. re-verifies the installed tree with verify-release.sh.
# Without root it still installs into the scratch target for testing, skips the
# ownership step and says so: the result is NOT a protected install.
set -eu

release=""; target=""
while [ $# -gt 0 ]; do
  case "$1" in
    --release) release=${2:-}; shift 2 ;;
    --root) target=${2:-}; shift 2 ;;
    *) echo "usage: install.sh --release <dir> --root <target>" >&2; exit 2 ;;
  esac
done
[ -n "$release" ] && [ -n "$target" ] || { echo "usage: install.sh --release <dir> --root <target>" >&2; exit 2; }
here=$(cd "$(dirname "$0")" && pwd -P)

# 0. the independent verifier must be beside this script (CS-10.1): no verifier, no install
[ -r "$here/verify-release.sh" ] || { echo "install: verify-release.sh missing or unreadable beside install.sh; refusing (nothing copied)" >&2; exit 1; }

# 1. refusals
[ -d "$release" ] || { echo "install: release directory not found: $release" >&2; exit 2; }
if [ -d "$release/.git" ] || [ -f "$release/install-manifest.yaml" ] || [ -d "$release/components" ]; then
  echo "install: '$release' looks like a repository checkout, not an immutable release; refusing" >&2; exit 2
fi
[ -f "$release/RELEASE.sha256" ] || { echo "install: RELEASE.sha256 missing in $release" >&2; exit 2; }
if [ -e "$target" ]; then
  echo "install: target exists: $target (a release is immutable; install a new version beside it)" >&2; exit 2
fi
case "$target" in /*) ;; *) echo "install: --root must be absolute" >&2; exit 2 ;; esac

# 2. verify the release before copying
( cd "$release" && sha256sum --quiet --strict -c RELEASE.sha256 ) || { echo "install: release digests do not verify; refusing" >&2; exit 1; }
if [ "$(find "$release" -type l | wc -l)" -ne 0 ]; then echo "install: release contains symbolic links; refusing" >&2; exit 1; fi
listed=$( (cd "$release" && grep -v '^#' RELEASE.sha256 | sed 's/^[0-9a-f]*  //' | sed 's|^\./||' | sort) )
present=$( (cd "$release" && find . -type f ! -name RELEASE.sha256 | sed 's|^\./||' | sort) )
[ "$listed" = "$present" ] || { echo "install: RELEASE.sha256 does not cover exactly the files present; refusing" >&2; exit 1; }
for name in bin/devforge bin/devforge-checkpoint.py RELEASE-IDENTITY.json \
            schemas/devforgeai/v1/research-gap-checkpoint.schema.json schemas/devforgeai/v1/release-identity.schema.json \
            schemas/devforgeai/v1/closure-attestation.schema.json contracts/MANIFEST.sha256; do
  [ -f "$release/$name" ] || { echo "install: required file missing in release: $name" >&2; exit 1; }
done

# 3. copy to a temporary sibling, set ownership and modes, rename atomically
parent=$(dirname "$target")
mkdir -p "$parent"
tmp="$parent/.$(basename "$target").install.$$"
rm -rf "$tmp"
cp -R "$release" "$tmp"
find "$tmp" -type d -exec chmod 0755 {} +
find "$tmp" -type f -exec chmod 0644 {} +
chmod 0755 "$tmp/bin/devforge" "$tmp/bin/devforge-checkpoint.py"
protected=1
if [ "$(id -u)" -eq 0 ]; then
  chown -R 0:0 "$tmp"
else
  protected=0
  echo "install: WARNING not running as root; ownership not set; '$target' is NOT a protected install" >&2
fi
mv "$tmp" "$target"

# 4. independent re-verification (the verifier's presence was required in step 0)
if sh "$here/verify-release.sh" "$target"; then
  echo "install: verified $target"
else
  if [ "$protected" -eq 1 ]; then echo "install: verification FAILED after install; do not use $target" >&2; exit 1; fi
  echo "install: verification reported failures (expected without root: OWNERSHIP)" >&2
fi
echo "install: done: $target (protected=$protected)"
exit 0
