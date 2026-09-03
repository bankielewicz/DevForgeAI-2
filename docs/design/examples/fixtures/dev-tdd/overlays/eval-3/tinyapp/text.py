"""Text helpers for tinyapp.

Eval 3 overlay: a minimal slugify that already satisfies criterion 1 only.
It does not strip accents (criterion 2) and raises on empty input (criterion 3).
"""
import re


def slugify(title: str) -> str:
    if not title.strip():
        raise ValueError("title must not be empty")
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
