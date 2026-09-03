#!/usr/bin/env bash
# Walks STORY-001 through the dev skill twice in scratch copies of the dev-tdd
# fixture: once in copy mode (no git repository) and once in worktree mode
# (git init, one commit, then run). Both must end green and promote.
#
# Every step goes through dispatch.py, the same route Claude Code and Codex use:
#   SessionStart      -> session evidence and the worktree self-test
#   phase start       -> gate, candidate root, phase red
#   SubagentStart     -> the phase lease is bound to one producer
#   PreToolUse Write  -> admitted inside the candidate root and the fence
#   Bash devforgeai run test -> the lease holder runs the suite in the root
#   SubagentStop      -> the receipt; the sequencer derives what changed
#
# Path: red -> green (rewind request, root back to base) -> red -> green ->
# refactor -> smoke -> review -> ready_to_promote -> `devforgeai promote`.
#
# Run: bash demo_sequencer.sh
set -u
export PYTHONDONTWRITEBYTECODE=1
HERE="$(cd "$(dirname "$0")" && pwd)"
FIX="$HERE/../fixtures/dev-tdd"
TOOLS="$(mktemp -d /tmp/dfai-demo-tools-XXXX)"

cat > "$TOOLS/agent.py" <<'PY'
"""One phase worker, driven through the dispatcher exactly as a provider does."""
import json, pathlib, subprocess, sys

HERE, ROOT = sys.argv[1], pathlib.Path(sys.argv[2])
PROVIDER = "claude"


def dispatch(event):
    p = subprocess.run(
        [sys.executable, f"{HERE}/dispatch.py", "--provider", PROVIDER, "--root", str(ROOT)],
        input=json.dumps(event), capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr).strip()


def event(name, **extra):
    base = {"hook_event_name": name, "session_id": "demo-session", "cwd": str(ROOT)}
    base.update(extra)
    return base


def run_root():
    record = pathlib.Path(sys.argv[3])
    import yaml
    return pathlib.Path(yaml.safe_load(record.read_text())["candidate"]["root"])


def main():
    record, agent, agent_id, phase = sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6]
    status, nxt, note = sys.argv[7], sys.argv[8], sys.argv[9]
    writes = [w for w in sys.argv[10:] if w]
    root = run_root()
    sub = {"agent_id": agent_id, "agent_type": agent}

    code, out = dispatch(event("SubagentStart", **sub))
    print(f"  SubagentStart -> exit {code}")
    if code:
        print("   " + out[:400])

    claimed = []
    for spec in writes:
        target, source = spec.split("=", 1)
        text = pathlib.Path(source).read_text()
        tool_input = {"file_path": str(root / target)}
        tool_input["content"] = text
        code, out = dispatch(event("PreToolUse", tool_name="Write",
                                   tool_input=tool_input, cwd=str(root), **sub))
        print(f"  PreToolUse Write {target} -> exit {code}")
        if code:
            print("   " + out[:400])
            continue
        (root / target).parent.mkdir(parents=True, exist_ok=True)
        (root / target).write_text(text)
        if not target.startswith(".devforgeai/"):
            claimed.append(target)   # evidence is not a project change

    if status == "pass" and claimed:
        code, out = dispatch(event("PreToolUse", tool_name="Bash",
                                   tool_input={"command": "devforgeai run test"},
                                   cwd=str(root), **sub))
        print(f"  Bash `devforgeai run test` -> exit {code}")

    receipt = {
        "schema": "devforgeai.worker-result/v1", "run": "STORY-001", "skill": "dev",
        "phase": phase, "agent": agent, "status": status,
        "candidate": {"id": "STORY-001", "input_checkpoint": checkpoint(record)},
        "claimed_paths": claimed if status == "pass" else [],
        "evidence_refs": [w.split("=", 1)[0] for w in writes
                          if w.startswith(".devforgeai/")],
        "note": note, "issues": [],
    }
    if nxt != "-":
        receipt["next"] = nxt
    message = "Done with this phase.\n\n```json\n" + json.dumps(receipt) + "\n```\n"
    code, out = dispatch(event("SubagentStop", stop_reason="end_turn",
                               last_assistant_message=message, **sub))
    print(f"  SubagentStop -> exit {code}")
    print("   " + "\n   ".join(out.splitlines()[:6]))
    return 0


def checkpoint(record):
    import yaml
    return yaml.safe_load(pathlib.Path(record).read_text())["candidate"]["checkpoint"]


sys.exit(main())
PY

cat > "$TOOLS/tests.py" <<'PY'
import tinyapp.text as text


def _slug(value):
    fn = getattr(text, "slugify", None)
    assert fn is not None, "slugify is not defined"
    return fn(value)


def test_slugify_basic():
    assert _slug("Hello, World!") == "hello-world"


def test_slugify_unicode():
    assert _slug("  Ünïcödé  Tïtle ") == "unicode-title"


def test_slugify_empty():
    assert _slug("") == "" and _slug("!!!") == ""
PY

cat > "$TOOLS/impl.py" <<'PY'
"""Text helpers for tinyapp."""
import re
import unicodedata


def slugify(title: str) -> str:
    value = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
PY

cat > "$TOOLS/evidence.md" <<'MD'
# smoke evidence for STORY-001

| criterion | checked against | result |
|---|---|---|
| 1 | tests/test_text.py::test_slugify_basic at checkpoint refactor | pass |
| 2 | tests/test_text.py::test_slugify_unicode at checkpoint refactor | pass |
| 3 | tests/test_text.py::test_slugify_empty at checkpoint refactor | pass |
MD

cat > "$TOOLS/refactored.py" <<'PY'
"""Text helpers for tinyapp."""
import re
import unicodedata

_SEPARATORS = re.compile(r"[^a-z0-9]+")


def _ascii(title: str) -> str:
    return unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()


def slugify(title: str) -> str:
    """A url-safe slug: ascii, lowercase, single hyphens, no leading separator."""
    return _SEPARATORS.sub("-", _ascii(title).lower()).strip("-")
PY

build_project() {  # build_project <dir> <mode>
  local W="$1" MODE="$2"
  mkdir -p "$W/.devforgeai" "$W/.claude"
  cp -r "$FIX/tinyapp" "$FIX/tests" "$FIX/pyproject.toml" "$FIX/STORY-001.md" "$W/"
  cp "$HERE/fixtures/.devforgeai/stack.yaml" "$W/.devforgeai/"
  cp "$HERE/settings.claude.json" "$W/.claude/settings.json"
  printf 'version: 1\nstories: {}\nruns: {}\n' > "$W/.devforgeai/state.yaml"
  printf '.devforgeai/work/\n__pycache__/\n.pytest_cache/\n*.pyc\n' > "$W/.gitignore"
  if [ "$MODE" = worktree ]; then
    git -C "$W" init -q
    git -C "$W" add -A
    git -C "$W" -c user.name=fixture -c user.email=fixture@example.invalid \
      commit -qm "fixture: tinyapp before STORY-001"
  fi
}

work_of() { echo "$1/.devforgeai/work/STORY-001/run.yaml"; }

phase_of() {
  python3 -c "import yaml,sys;print(yaml.safe_load(open(sys.argv[1]))['phase'])" "$(work_of "$1")"
}

root_of() {
  python3 -c "import yaml,sys;print(yaml.safe_load(open(sys.argv[1]))['candidate']['root'])" \
    "$(work_of "$1")"
}

mode_of() {
  python3 -c "import yaml,sys;print(yaml.safe_load(open(sys.argv[1]))['candidate']['mode'])" \
    "$(work_of "$1")"
}

run_story() {  # run_story <mode>
  local MODE="$1"
  local W; W="$(mktemp -d "/tmp/dfai-demo-$MODE-XXXX")"
  build_project "$W" "$MODE"
  local D="python3 $HERE/devforgeai.py"
  local A="python3 $TOOLS/agent.py $HERE $W $(work_of "$W")"

  echo; echo "############ $MODE mode: $W"
  echo "=== SessionStart: session evidence and the worktree self-test"
  printf '%s' '{"hook_event_name":"SessionStart","session_id":"demo-session","cwd":"'"$W"'","version":"demo-1.0","start_reason":"startup"}' \
    | python3 "$HERE/dispatch.py" --provider claude --root "$W"

  echo; echo "=== gate: story v3 checks, candidate root, phase red"
  # The fixture story is stand-alone: it lives at the scratch root rather than
  # under docs/plan/, and its provenance and context entries carry placeholder
  # hashes with no documents to resolve against. --lenient downgrades exactly
  # that defect class (unresolvable-source) to a recorded gate warning; a stale
  # hash and every other defect still refuses the run.
  (cd "$W" && $D phase start dev STORY-001 --lenient)
  echo "candidate mode: $(mode_of "$W")"

  echo; echo "=== a worker tries to write outside the candidate root: denied"
  printf '%s' '{"hook_event_name":"PreToolUse","session_id":"demo-session","cwd":"'"$W"'","agent_id":"a-red","agent_type":"red_dev","tool_name":"Write","tool_input":{"file_path":"'"$W"'/tests/test_text.py"}}' \
    | python3 "$HERE/dispatch.py" --provider claude --root "$W"; echo "[exit $?]"

  echo; echo "=== a worker tries to sequence: hook-only operations are refused"
  printf '%s' '{"hook_event_name":"PreToolUse","session_id":"demo-session","cwd":"'"$W"'","agent_id":"a-red","agent_type":"red_dev","tool_name":"Bash","tool_input":{"command":"devforgeai phase next"}}' \
    | python3 "$HERE/dispatch.py" --provider claude --root "$W"; echo "[exit $?]"

  echo; echo "=== the primary calls the Research Core runner: admitted, run or no run"
  printf '%s' '{"hook_event_name":"PreToolUse","session_id":"demo-session","cwd":"'"$W"'","tool_name":"Bash","tool_input":{"command":"devforgeai-research validate-run RUN-000001"}}' \
    | python3 "$HERE/dispatch.py" --provider claude --root "$W"; echo "[exit $?]"

  echo; echo "=== RED: red_dev writes the three failing tests in the candidate root"
  $A red_dev a-red red pass - "three criteria, each failing on its assertion" \
    "tests/test_text.py=$TOOLS/tests.py"

  echo; echo "=== GREEN: green_dev finds criterion 2 underspecified and asks to rewind"
  $A green_dev a-green green fail red \
    "criterion 2 expects unicode-title but the story does not say how o-umlaut maps"
  echo "  candidate tests/ after the rewind: $(ls "$W/.devforgeai/work/STORY-001/wt/tests")"

  echo; echo "=== RED again: attempts.red is now 1 of 2"
  $A red_dev a-red red pass - "criterion 2 rewritten against the clarified rule" \
    "tests/test_text.py=$TOOLS/tests.py"

  echo; echo "=== GREEN: green_dev implements slugify; the oracle runs the suite"
  $A green_dev a-green green pass - "smallest change that satisfies the frozen tests" \
    "tinyapp/text.py=$TOOLS/impl.py"

  echo; echo "=== REFACTOR: the oracle runs test then lint"
  $A refactor_dev a-refactor refactor pass - "extracted the separator pattern" \
    "tinyapp/text.py=$TOOLS/refactored.py"

  echo; echo "=== a judge writing a project file is denied: its path is its evidence directory"
  CR="$(root_of "$W")"
  printf '%s' '{"hook_event_name":"PreToolUse","session_id":"demo-session","cwd":"'"$CR"'","agent_id":"a-smoke","agent_type":"smoke_qa","tool_name":"Write","tool_input":{"file_path":"'"$CR"'/tinyapp/text.py"}}' \
    | python3 "$HERE/dispatch.py" --provider claude --root "$W"; echo "[exit $?]"

  echo; echo "=== SMOKE: a judge reads the refactor checkpoint and writes only evidence"
  $A smoke_qa a-smoke smoke pass - "each criterion checked once against the checkpoint" \
    ".devforgeai/work/STORY-001/evidence/smoke_qa/criteria.md=$TOOLS/evidence.md"


  echo; echo "=== REVIEW: the critic judges and the run is parked for a human"
  $A dev_critic a-critic review pass - "criteria covered, tests frozen, fence held"

  echo; echo "=== the user reads the reports, then promotes: the fifth model-callable form"
  (cd "$W" && $D promote STORY-001)

  echo; echo "=== final state"
  (cd "$W" && $D status)
  echo "provenance log:"; cut -c1-140 "$W/.devforgeai/provenance/log.jsonl"

  local OUTCOME STATUS PROMOTED
  OUTCOME="$(python3 -c "import json;print(json.load(open('$W/.devforgeai/work/STORY-001/handoff.json'))['outcome'])" 2>/dev/null || echo none)"
  STATUS="$(python3 -c "import yaml;print(yaml.safe_load(open('$W/.devforgeai/state.yaml'))['runs']['STORY-001']['status'])" 2>/dev/null || echo none)"
  if grep -q "_SEPARATORS" "$W/tinyapp/text.py" 2>/dev/null; then PROMOTED=yes; else PROMOTED=no; fi
  echo "$MODE mode: outcome=$OUTCOME run_status=$STATUS canonical_has_refactored_code=$PROMOTED"
  if [ "$OUTCOME" = pass ] && [ "$STATUS" = promoted ] && [ "$PROMOTED" = yes ]; then
    RESULT="green"
  else
    RESULT="RED"
  fi
  echo "$MODE mode result: $RESULT (scratch $W)"
  [ "$RESULT" = green ]
}

COPY_OK=0
WORKTREE_OK=0
run_story copy && COPY_OK=1
run_story worktree && WORKTREE_OK=1

echo
if [ "$COPY_OK" = 1 ] && [ "$WORKTREE_OK" = 1 ]; then
  echo "DEMO OK: copy mode green, worktree mode green"
  exit 0
fi
echo "DEMO FAILED: copy=$COPY_OK worktree=$WORKTREE_OK (1 is green)"
exit 1
