#!/usr/bin/python3
"""Write RELEASE.sha256 for a built release tree (INSTALLED-LAYOUT.md v2, rule 3).

    python3 gen_release_manifest.py <root>

Lists every regular file under <root> except RELEASE.sha256 itself, sha256sum
format, <root>-relative paths, sorted. Refuses a tree that contains a symbolic
link or a __pycache__ directory, lacks a required layout-v2 entry, or whose
bin/devforge is not a statically linked ELF executable (corrective-spec-002
CS-8.1, CS-10.2). This is a generator only: it never verifies an existing
manifest and its output is not evidence until verify-release.sh (coreutils)
and the validator's installed-mode self-check agree with it.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

REQUIRED = (
    "bin/devforge", "bin/devforge-checkpoint.py", "RELEASE-IDENTITY.json",
    "schemas/devforgeai/v1/research-gap-checkpoint.schema.json",
    "schemas/devforgeai/v1/release-identity.schema.json",
    "schemas/devforgeai/v1/closure-attestation.schema.json",
    "contracts/MANIFEST.sha256",
)


def static_elf_problem(path: Path) -> str | None:
    """Why ``path`` is not a static ELF64 executable, or None (CS-8.1)."""
    data = path.read_bytes()
    if data[:4] != b"\x7fELF":
        return "not an ELF file"
    if data[4] != 2 or data[5] != 1:
        return "not ELF64 little-endian"
    e_phoff = int.from_bytes(data[0x20:0x28], "little")
    e_phentsize = int.from_bytes(data[0x36:0x38], "little")
    e_phnum = int.from_bytes(data[0x38:0x3a], "little")
    for i in range(e_phnum):
        off = e_phoff + i * e_phentsize
        p_type = int.from_bytes(data[off:off + 4], "little")
        if p_type == 3:
            return "has a PT_INTERP program header (dynamically loaded)"
        if p_type == 2:
            p_offset = int.from_bytes(data[off + 8:off + 16], "little")
            p_filesz = int.from_bytes(data[off + 32:off + 40], "little")
            dyn = data[p_offset:p_offset + p_filesz]
            for j in range(0, len(dyn) - 15, 16):
                tag = int.from_bytes(dyn[j:j + 8], "little")
                if tag == 1:
                    return "has a DT_NEEDED entry (dynamically linked)"
                if tag == 0:
                    break
    return None


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
    if why := static_elf_problem(root / "bin" / "devforge"):
        raise SystemExit(f"bin/devforge is not a static launcher: {why}")
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
