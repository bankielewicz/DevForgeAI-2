#!/bin/sh
# verify-release.sh <root>: independent verification of an installed (or built)
# release tree with coreutils only (INSTALLED-LAYOUT.md v2 rules 2-3). Never uses
# the generator or the validator. Prints one line per check and exits non-zero
# if any check FAILs. On a user-owned build tree OWNERSHIP FAILs by design.
set -u
root=${1:-}
if [ -z "$root" ] || [ ! -d "$root" ]; then
  echo "usage: verify-release.sh <root>" >&2
  exit 2
fi
status=0
cd "$root" || exit 2

# 1. digests: every listed entry verifies
if [ ! -f RELEASE.sha256 ]; then
  echo "DIGEST: FAIL (RELEASE.sha256 missing)"; status=1
elif grep -q '  RELEASE.sha256$' RELEASE.sha256; then
  echo "DIGEST: FAIL (RELEASE.sha256 lists itself)"; status=1
elif sha256sum --quiet --strict -c RELEASE.sha256 2>&1; then
  echo "DIGEST: OK"
else
  echo "DIGEST: FAIL"; status=1
fi

# 2. symlinks: none anywhere under the root
links=$(find . -type l | wc -l)
if [ "$links" -eq 0 ]; then echo "SYMLINKS: OK"; else echo "SYMLINKS: FAIL ($links)"; find . -type l; status=1; fi

# 3. coverage: every regular file except the manifest is listed, and only those
listed=$(grep -v '^#' RELEASE.sha256 2>/dev/null | sed 's/^[0-9a-f]*  //' | sed 's|^\./||' | sort)
present=$(find . -type f ! -name RELEASE.sha256 | sed 's|^\./||' | sort)
if [ "$listed" = "$present" ]; then
  echo "COVERAGE: OK"
else
  echo "COVERAGE: FAIL"; status=1
  printf '%s\n' "$listed" > /tmp/verify-release.listed.$$
  printf '%s\n' "$present" > /tmp/verify-release.present.$$
  echo "only in manifest:"; comm -23 /tmp/verify-release.listed.$$ /tmp/verify-release.present.$$
  echo "only on disk:";     comm -13 /tmp/verify-release.listed.$$ /tmp/verify-release.present.$$
  rm -f /tmp/verify-release.listed.$$ /tmp/verify-release.present.$$
fi

# 4. required entries (layout v2)
req=0
for name in bin/devforge bin/devforge-checkpoint.py RELEASE-IDENTITY.json \
            schemas/devforgeai/v1/research-gap-checkpoint.schema.json schemas/devforgeai/v1/release-identity.schema.json \
            schemas/devforgeai/v1/closure-attestation.schema.json contracts/MANIFEST.sha256; do
  grep -q "  $name\$" RELEASE.sha256 2>/dev/null || { echo "REQUIRED: FAIL (missing $name)"; req=1; }
done
[ "$req" -eq 0 ] && echo "REQUIRED: OK" || status=1

# 4b. exact modes (layout v2 rule 2): directories 0755, files 0644, the two bin/ entries 0755
loose=$( { find . -type d ! -perm 755 -printf '%m %p\n'; \
           find . -type f ! -path ./bin/devforge ! -path ./bin/devforge-checkpoint.py ! -perm 644 -printf '%m %p\n'; \
           find ./bin -maxdepth 1 -type f \( -name devforge -o -name devforge-checkpoint.py \) ! -perm 755 -printf '%m %p\n'; } | sed 's|^\([0-7]*\) \./|\1 |' )
if [ -z "$loose" ]; then
  echo "MODES: OK"
else
  echo "MODES: FAIL"; printf '%s\n' "$loose" | head -20; status=1
fi

# 5. ownership and modes: uid 0, no group/other write, on the root, every object under it, and every ancestor
bad=$(find . \( ! -uid 0 -o -perm /022 \) -printf '%u %m %p\n' | wc -l)
abs=$(cd "$root" && pwd -P)
anc=0
d=$abs
while [ "$d" != "/" ]; do
  d=$(dirname "$d")
  if [ "$(stat -c '%u' "$d")" != "0" ] || [ $(( 0$(stat -c '%a' "$d") & 022 )) -ne 0 ]; then
    echo "ancestor not protected: $(stat -c '%u %a %n' "$d")"; anc=1
  fi
done
if [ "$bad" -eq 0 ] && [ "$anc" -eq 0 ]; then
  echo "OWNERSHIP: OK"
else
  echo "OWNERSHIP: FAIL ($bad objects under the root, ancestors $anc)"
  find . \( ! -uid 0 -o -perm /022 \) -printf '%u %m %p\n' | head -20
  status=1
fi

exit $status
