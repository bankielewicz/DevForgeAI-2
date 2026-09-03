#!/usr/bin/env python3
"""Verification battery for the design refresh and skill specifications.

Checks (plan section "Verification"):
  V1 header      every SKILL-SPEC-*.md has the 16 required sections in order, an id
                 matching the template id_pattern, status approved, no placeholders
  V2 forbidden   no forbidden text in docs/design/** except 12-post-mvp.md
  V3 hashes      every depends_on hash resolves and matches (01 hash rule)
  V4 xref        every consumed template has a producer and vice versa, from
                 11-artifact-registry.md's registry block and each spec's section 6
  V8 grammar     10-sequencer-and-contracts.md CLI table equals devforgeai.py argparse

Usage: python3 docs/design/specs/verify.py [--only v1,v2,...,v9] [--specs-dir PATH]
Exit 0 when every selected check passes, 1 otherwise. Deterministic, no network.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
DESIGN = ROOT / "docs" / "design"
TEMPLATE = DESIGN / "templates" / "skill-spec.md"
REGISTRY = DESIGN / "11-artifact-registry.md"
CONTRACTS = DESIGN / "10-sequencer-and-contracts.md"
SEQUENCER = DESIGN / "examples" / "hooks" / "devforgeai.py"
POST_MVP = DESIGN / "12-post-mvp.md"

FORBIDDEN = [
    "Provider Conformance", "attestation", "requirements.toml", "UNSUPPORTED_CAPABILITY",
    "state-writer", "template-validator", "provenance-checker", "handoff-renderer",
    "criteria_map", "Bash(pytest", "template_version: 2", "token use", "eval viewer",
    "sandbox/container",
]
PLACEHOLDERS = ["{{", "}}", "TODO", "TBD", "<fill in>"]


def frontmatter(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        raise ValueError(f"{path}: no frontmatter")
    return yaml.safe_load(m.group(1)) or {}, m.group(2)


def template_header() -> dict:
    header, _ = frontmatter(TEMPLATE)
    return header


def slug(heading: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", heading.strip().lower()).strip("-")


def section_bytes(path: Path, anchor: str | None) -> bytes | None:
    lines = path.read_text(encoding="utf-8").replace("\r\n", "\n").split("\n")
    if anchor is None:
        return ("\n".join(lines) + "\n").encode("utf-8")
    if re.fullmatch(r"L\d+-L\d+", anchor):
        a, b = (int(x) for x in re.findall(r"\d+", anchor))
        return ("\n".join(lines[a - 1:b]) + "\n").encode("utf-8")
    # A `#` line inside a fenced code block is sample text, not a heading: it
    # neither opens nor ends a section. Fences open on ``` or ~~~ (up to three
    # leading spaces) and close on a run of the same character, at least as
    # long, with nothing after it.
    fence = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
    fenced = [False] * len(lines)
    marker = None
    for i, line in enumerate(lines):
        m = fence.match(line)
        if marker is None:
            if m:
                marker, fenced[i] = m.group(1), True
            continue
        fenced[i] = True
        if m and m.group(1)[0] == marker[0] and len(m.group(1)) >= len(marker) \
                and not m.group(2).strip():
            marker = None
    start = level = None
    for i, line in enumerate(lines):
        m = re.match(r"^(#{1,6})\s+(.*)", line)
        if m and not fenced[i] and slug(m.group(2)) == anchor:
            start, level = i, len(m.group(1))
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start + 1, len(lines)):
        m = re.match(r"^(#{1,6})\s", lines[j])
        if m and not fenced[j] and len(m.group(1)) <= level:
            end = j
            break
    return ("\n".join(lines[start:end]) + "\n").encode("utf-8")


def spec_files(specs_dir: Path) -> list[Path]:
    return sorted(specs_dir.glob("SKILL-SPEC-*.md"))


# V1 ---------------------------------------------------------------------------
def v1(specs: list[Path]) -> list[str]:
    errors: list[str] = []
    header = template_header()
    required = header["required_sections"]
    id_re = re.compile(header["id_pattern"])
    for spec in specs:
        try:
            fm, body = frontmatter(spec)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"V1 {spec.name}: {exc}")
            continue
        for key in header["required_frontmatter"]:
            if key not in fm:
                errors.append(f"V1 {spec.name}: missing frontmatter {key}")
        if not id_re.fullmatch(str(fm.get("id", ""))):
            errors.append(f"V1 {spec.name}: id {fm.get('id')!r} fails {header['id_pattern']}")
        if fm.get("status") != "approved":
            errors.append(f"V1 {spec.name}: status {fm.get('status')!r} != approved")
        positions = []
        for sec in required:
            m = re.search("^" + re.escape(sec) + r"\s*$", body, re.M)
            if not m:
                errors.append(f"V1 {spec.name}: missing section {sec!r}")
            else:
                positions.append(m.start())
        if positions != sorted(positions):
            errors.append(f"V1 {spec.name}: sections out of order")
        raw = spec.read_text(encoding="utf-8")
        for ph in PLACEHOLDERS:
            if ph in raw:
                errors.append(f"V1 {spec.name}: placeholder {ph!r} present")
    return errors


# V2 ---------------------------------------------------------------------------
def v2() -> list[str]:
    errors: list[str] = []
    for path in DESIGN.rglob("*.md"):
        if path == POST_MVP or "examples/hooks" in str(path):
            continue
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for word in FORBIDDEN:
                if word in line:
                    errors.append(f"V2 {path.relative_to(ROOT)}:{n}: {word!r}")
    return errors


# V9 ---------------------------------------------------------------------------
STALE = ["files[]", '"content":', "sha256_before", "read-only worker", "context-curator",
         "context curator", "one extra Slice agent", "--detach", "applies the files",
         "apply the files", "full file text", "read-only on both providers"]
BRIEF_NAME = "WRITE-MODEL-REVISION.md"


def v9() -> list[str]:
    """No file may still describe the pre-pivot write model (brief D11)."""
    errors: list[str] = []
    roots = [DESIGN, ROOT / "schemas" / "devforgeai"]
    for root in roots:
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix not in {".md", ".json", ".py", ".toml", ".sh", ".yaml"}:
                continue
            if path == POST_MVP or path.name == BRIEF_NAME or path.name == "verify.py":
                continue
            for n, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                for word in STALE:
                    if word in line:
                        errors.append(f"V9 {path.relative_to(ROOT)}:{n}: {word!r}")
                if "isolation: worktree" in line and path.name != "04-dual-target.md":
                    errors.append(f"V9 {path.relative_to(ROOT)}:{n}: 'isolation: worktree' outside 04")
    return errors


# V3 ---------------------------------------------------------------------------
def v3(specs: list[Path]) -> list[str]:
    errors: list[str] = []
    for spec in specs:
        fm, _ = frontmatter(spec)
        for dep in fm.get("depends_on", []) or []:
            source = str(dep.get("source", ""))
            recorded = str(dep.get("hash", "")).removeprefix("sha256:")
            path_part, _, anchor = source.partition("#")
            target = ROOT / path_part
            if not target.exists():
                errors.append(f"V3 {spec.name}: missing source {source}")
                continue
            data = section_bytes(target, anchor or None)
            if data is None:
                errors.append(f"V3 {spec.name}: anchor not found {source}")
                continue
            actual = hashlib.sha256(data).hexdigest()
            if actual != recorded:
                errors.append(f"V3 {spec.name}: stale {source} (have {recorded[:12]}, now {actual[:12]})")
    return errors


# V4 ---------------------------------------------------------------------------
def registry() -> dict:
    text = REGISTRY.read_text(encoding="utf-8")
    m = re.search(r"```yaml\n(registry:.*?)```", text, re.S)
    if not m:
        raise ValueError("11-artifact-registry.md has no ```yaml registry block")
    return yaml.safe_load(m.group(1))["registry"]


def v4(specs: list[Path]) -> list[str]:
    errors: list[str] = []
    try:
        reg = registry()
    except Exception as exc:  # noqa: BLE001
        return [f"V4 {exc}"]
    producers: dict[str, set[str]] = {}
    consumers: dict[str, set[str]] = {}
    for t in reg.get("templates", []):
        name = t["name"]
        for p in t.get("produced_by", []) or []:
            producers.setdefault(name, set()).add(p)
        for c in t.get("consumed_by", []) or []:
            consumers.setdefault(name, set()).add(c)
    for name in sorted(set(producers) | set(consumers)):
        if name not in producers:
            errors.append(f"V4 template {name}: consumed but no producer")
        if name not in consumers and name not in {"handoff", "validate-report"}:
            errors.append(f"V4 template {name}: produced but no consumer")
    skills = {s["name"] for s in reg.get("skills", [])} if reg.get("skills") else set()
    commands: set[str] = set()
    for s in reg.get("skills", []) or []:
        cmd = str(s.get("command", "")).strip()
        for token in re.findall(r"[/$]([a-z][a-z-]*)", cmd):
            commands.add(token)
    commands |= skills
    for spec in specs:
        fm, body = frontmatter(spec)
        skill = fm.get("skill_name")
        if skills and skill not in skills:
            errors.append(f"V4 {spec.name}: skill {skill!r} not in registry")
        for cmd in re.findall(r"`([/$][a-z][a-z-]*)", body):
            base = cmd[1:]
            if commands and base not in commands:
                errors.append(f"V4 {spec.name}: next-step command {cmd} names no skill")
    return errors


# V8 ---------------------------------------------------------------------------
def v8() -> list[str]:
    errors: list[str] = []
    text = CONTRACTS.read_text(encoding="utf-8")
    documented = set(re.findall(r"`devforgeai ([a-z][a-z-]*(?: [a-z][a-z-]*)?)", text))
    documented = {d.split(" ")[0] + (" " + d.split(" ")[1] if d.startswith("phase ") else "") for d in documented}
    try:
        out = subprocess.run([sys.executable, str(SEQUENCER), "--help"], capture_output=True, text=True, timeout=30).stdout
    except Exception as exc:  # noqa: BLE001
        return [f"V8 cannot run sequencer: {exc}"]
    m = re.search(r"\{([a-z\-,]+)\}", out)
    actual = set(m.group(1).split(",")) if m else set()
    phase_out = subprocess.run([sys.executable, str(SEQUENCER), "phase", "--help"], capture_output=True, text=True, timeout=30).stdout
    pm = re.search(r"\{([a-z\-,]+)\}", phase_out)
    if pm:
        actual |= {"phase " + p for p in pm.group(1).split(",")}
        actual.discard("phase")
    doc_top = {d for d in documented if not d.startswith("phase ")} | {d for d in documented if d.startswith("phase ")}
    missing = sorted(doc_top - actual)
    extra = sorted(actual - doc_top)
    if missing:
        errors.append(f"V8 documented but not in argparse: {missing}")
    if extra:
        errors.append(f"V8 in argparse but undocumented: {extra}")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="v1,v2,v3,v4,v8,v9")
    ap.add_argument("--specs-dir", default=str(DESIGN / "specs"))
    args = ap.parse_args()
    selected = {s.strip().lower() for s in args.only.split(",")}
    specs = spec_files(Path(args.specs_dir))
    results: dict[str, list[str]] = {}
    if "v1" in selected:
        results["v1"] = v1(specs)
    if "v2" in selected:
        results["v2"] = v2()
    if "v3" in selected:
        results["v3"] = v3(specs)
    if "v4" in selected:
        results["v4"] = v4(specs)
    if "v8" in selected:
        results["v8"] = v8()
    if "v9" in selected:
        results["v9"] = v9()
    failed = False
    for name, errs in results.items():
        print(f"{name.upper()}: {'ok' if not errs else f'{len(errs)} problem(s)'}")
        for e in errs:
            print("  " + e)
        failed |= bool(errs)
    print(f"specs checked: {len(specs)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
