#!/usr/bin/env bash
# Install hookd into a project: copies the dispatcher and checks to
# <project>/.claude/hooks/ and merges the hooks block into .claude/settings.json.
# Run from the project root. Re-runnable. Does not run hooks itself.
set -euo pipefail
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DST="$PWD/.claude/hooks"
mkdir -p "$DST"
cp "$SRC/hookd.py" "$DST/"
rm -rf "$DST/checks" && cp -r "$SRC/checks" "$DST/checks"
[ -f "$DST/policy.json" ] || cp "$SRC/policy.json" "$DST/policy.json"
python3 - "$SRC/settings.claude.json" "$PWD/.claude/settings.json" <<'PY'
import json, sys, pathlib
src = json.load(open(sys.argv[1]))["hooks"]
p = pathlib.Path(sys.argv[2]); p.parent.mkdir(exist_ok=True)
text = p.read_text() if p.exists() else ""
cur = json.loads(text) if text.strip() else {}
hooks = cur.setdefault("hooks", {})
for event, entries in src.items():
    existing = hooks.setdefault(event, [])
    if not any("hookd.py" in json.dumps(e) for e in existing):
        existing.extend(entries)
p.write_text(json.dumps(cur, indent=2) + "\n")
print(f"merged hookd entries into {p}")
PY
# Ignore runtime files unless the project already ignores .claude/ as a whole.
if ! git check-ignore -q .claude/hooks/hookd.log.jsonl 2>/dev/null; then
  grep -q "hookd.log.jsonl" .gitignore 2>/dev/null || printf '\n# hookd runtime files\n.claude/hooks/hookd.log.jsonl\n.claude/hooks/receipts/\n.claude/hooks/__pycache__/\n.claude/hooks/checks/__pycache__/\n' >> .gitignore
fi
echo "installed. Open /hooks in Claude Code to confirm the entries; SessionStart context appears on the next session."
