#!/usr/bin/python3 -I
"""Launcher for `devforge checkpoint` (INSTALLED-LAYOUT.md rule 5).

Runs only through bin/devforge, which execs `/usr/bin/python3 -I -B -P` on this
file: no PYTHONPATH, no user site, no bytecode written, no script-directory path
entry. The release's own lib/ is the only addition to sys.path. The validator
module detects installed mode from RELEASE.sha256 above itself and verifies the
whole tree before reading any record.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).absolute().parent.parent
sys.path.insert(0, str(ROOT / "lib"))

from devforgeai.checkpoint.__main__ import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
