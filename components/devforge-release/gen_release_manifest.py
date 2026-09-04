#!/usr/bin/python3
"""Write RELEASE.sha256 for a built release tree (INSTALLED-LAYOUT.md rule 3).

    python3 gen_release_manifest.py <root>

Lists every regular file under <root> except RELEASE.sha256 itself, sha256sum
format, <root>-relative paths, sorted. Refuses a tree that contains a symbolic
link, a __pycache__ directory, or lacks the three required entries. This is a
generator only: it never verifies an existing manifest and its output is not
evidence until verify-release.sh (coreutils) and the validator's installed-mode
self-check agree with it.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

REQUIRED = ("bin/devforge", "schemas/devforgeai/v1/research-gap-checkpoint.schema.json",
            "contracts/MANIFEST.sha256")


def generate(root: Path) -> tuple[str, int]:
    root = Path(root)
    if not root.is_dir():
        raise SystemExit(f"not a directory: {root}")
    lines: list[str] = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        if path.is_symlink():
            raise SystemExit(f"symbolic link inside the release tree: {rel}")
        if path.is_dir() and path.name == "__pycache__":
            raise SystemExit(f"__pycache__ inside the release tree: {rel}")
        if path.is_file() and rel != "RELEASE.sha256":
            lines.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {rel}")
    listed = {line.split("  ", 1)[1] for line in lines}
    missing = [name for name in REQUIRED if name not in listed]
    if missing:
        raise SystemExit("required entries missing from the tree: " + ", ".join(missing))
    text = "\n".join(lines) + "\n"
    (root / "RELEASE.sha256").write_text(text, encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest(), len(lines)


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    digest, count = generate(Path(argv[0]))
    print(f"RELEASE.sha256 written: {count} entries, digest {digest}")
    print("not verified: run verify-release.sh on the tree")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
