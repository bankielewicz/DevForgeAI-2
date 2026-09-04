#!/bin/sh
# build.sh [--record]
#
# Builds the static `devforge` launcher with the pinned toolchain
# (rust-toolchain.toml, Cargo.lock, .cargo/config.toml) and checks that the
# result is statically linked. Without --record it compares the binary's
# SHA-256 with BUILD-DIGEST.txt and fails on a mismatch (DevForge's rebuild
# check, CS-8.6); with --record it rewrites BUILD-DIGEST.txt (DevForgeAI, when
# the source or the toolchain pin changes). Offline: `--locked --offline`
# needs no registry because the crate has no dependencies.
set -eu
here=$(cd "$(dirname "$0")" && pwd -P)
cd "$here"
target=x86_64-unknown-linux-musl
record=0
[ "${1:-}" = "--record" ] && record=1

cargo build --release --locked --offline --target "$target"
bin="$here/target/$target/release/devforge"
[ -f "$bin" ] || { echo "build: binary missing: $bin" >&2; exit 1; }

# static: no program interpreter, no dynamic section needed
if ldd "$bin" 2>&1 | grep -qiE 'statically linked|not a dynamic executable'; then
  echo "build: static: OK"
else
  echo "build: binary is dynamically linked; refusing" >&2; ldd "$bin" >&2 || true; exit 1
fi

digest=$(sha256sum "$bin" | cut -d' ' -f1)
if [ "$record" -eq 1 ]; then
  {
    echo "# BUILD-DIGEST.txt: the pinned launcher build (corrective-spec-002 CS-8.6)."
    echo "# DevForge rebuilds with the pinned toolchain and must reproduce this digest,"
    echo "# or record the deviation and its cause in the promotion record."
    echo "target $target"
    echo "command cargo build --release --locked --offline --target $target"
    echo "rustflags -C target-feature=+crt-static -C relocation-model=static --remap-path-prefix /home=/remapped --remap-path-prefix /tmp=/remapped"
    rustc -Vv | sed 's/^/rustc /'
    cargo -V | sed 's/^/cargo /'
    echo "sha256 $digest"
  } > BUILD-DIGEST.txt
  echo "build: recorded BUILD-DIGEST.txt ($digest)"
else
  expected=$(grep '^sha256 ' BUILD-DIGEST.txt | cut -d' ' -f2)
  if [ "$digest" = "$expected" ]; then
    echo "build: digest matches BUILD-DIGEST.txt ($digest)"
  else
    echo "build: digest $digest differs from pinned $expected" >&2; exit 1
  fi
fi
echo "build: $bin"
