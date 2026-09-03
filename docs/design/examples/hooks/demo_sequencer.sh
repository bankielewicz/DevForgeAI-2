#!/usr/bin/env bash
# Walks STORY-001 through the dev skill four times, in scratch copies of two
# sibling fixtures:
#
#   python  copy  |  python  worktree     ../fixtures/dev-tdd       (the control)
#   node    copy  |  node    worktree     ../fixtures/dev-tdd-node
#
# copy mode is a scratch tree with no git repository; worktree mode is the same
# tree after `git init` and one commit. All four must end green and promote.
#
# What the two ecosystems share is everything except one line of story
# frontmatter. Same skill, same phase registry, same fence, same lease, same
# oracles, same dispatcher, same receipts. The only difference is
# `commands.source`: `.devforgeai/stack.yaml#python` against
# `.devforgeai/stack.yaml#node`. The Python fixture is unchanged from before the
# Node one existed, so a Python regression here is a regression in the
# sequencer, not in the conversion.
#
# What this demo shows, exactly: two interpreted ecosystems run through the same
# stack-selected workflow. It does not prove compiled-stack support, arbitrary
# Node-version compatibility, or automatic stack detection. The `csharp` section
# of stack.yaml is never executed here, the Node runs are whatever `node` is on
# PATH and nothing else, and each story names its stack section by hand.
#
# Nothing is installed and nothing reaches the network. The Node section runs
# `node --test` and `node --check` from the standard library; `npm` is declared
# as the section's package manager and is never invoked. Each run asserts that
# afterwards: no `node_modules/`, no `package-lock.json`, no argv in the section
# that names a package manager or a fetcher, and a canonical tree whose only
# changed paths are the story's write-fence files plus the phase reports that
# promotion publishes under `docs/reports/` — the sequencer's own output, which
# the Python control produces identically.
#
# Every step goes through dispatch.py, the same route Claude Code and Codex use:
#   SessionStart      -> session evidence and the worktree self-test
#   phase start       -> gate, candidate root, phase red
#   SubagentStart     -> the phase lease is bound to one producer
#   PreToolUse Write  -> admitted inside the candidate root and the fence
#   Bash devforgeai run test -> the lease holder runs the suite in the root
#   SubagentStop      -> the receipt; the sequencer derives what changed
#
# Path per run: red -> green (rewind request, root back to base) -> red ->
# green -> refactor -> smoke -> review -> ready_to_promote -> `devforgeai
# promote`.
#
# Run: bash demo_sequencer.sh
set -u
export PYTHONDONTWRITEBYTECODE=1
# Nothing in this demo wants an inherited Node flag set: an injected
# --experimental-* or --require would change what the oracle observes.
export NODE_OPTIONS=
HERE="$(cd "$(dirname "$0")" && pwd)"
SCRATCH="${TMPDIR:-/tmp}"
TOOLS="$(mktemp -d "$SCRATCH/dfai-demo-tools-XXXX")"
mkdir -p "$TOOLS/python" "$TOOLS/node"

cat > "$TOOLS/agent.py" <<'PY'
"""One phase worker, driven through the dispatcher exactly as a provider does.

Language-neutral: it copies payload bytes to a path inside the candidate root
and returns a receipt. Which bytes and which path come from the caller.
"""
import json, os, pathlib, subprocess, sys

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
    # The dispatch context the provider hands the worker. Written out so the
    # demo can assert what the next phase is told, exactly as the worker sees it.
    if os.environ.get("DFAI_CTX_OUT"):
        pathlib.Path(os.environ["DFAI_CTX_OUT"]).write_text(out)

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
    # A judge returns its evidence in the receipt (D13): it writes no file, and
    # the sequencer persists these bytes at a path the worker cannot choose.
    if os.environ.get("DFAI_FINDINGS"):
        receipt["findings"] = pathlib.Path(os.environ["DFAI_FINDINGS"]).read_text()
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

# ---------------------------------------------------------------- payloads: python

cat > "$TOOLS/python/tests.py" <<'PY'
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

cat > "$TOOLS/python/impl.py" <<'PY'
"""Text helpers for tinyapp."""
import re
import unicodedata


def slugify(title: str) -> str:
    value = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
PY

cat > "$TOOLS/python/refactored.py" <<'PY'
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

cat > "$TOOLS/python/evidence.md" <<'MD'
# smoke evidence for STORY-001

| criterion | checked against | result |
|---|---|---|
| 1 | tests/test_text.py::test_slugify_basic at checkpoint refactor | pass |
| 2 | tests/test_text.py::test_slugify_unicode at checkpoint refactor | pass |
| 3 | tests/test_text.py::test_slugify_empty at checkpoint refactor | pass |
MD

# ------------------------------------------------------------------ payloads: node
#
# The three test names are the story's test_plan verbatim:
#   test_slugify_basic  test_slugify_unicode  test_slugify_empty
# The helper asserts that `slugify` is a function before calling it, and the
# module is imported as a namespace rather than by named import, so a red run
# fails on an assertion instead of on an unresolved export. The oracle refuses a
# red phase whose tests error at import; that is what makes this shape load
# bearing rather than stylistic.

cat > "$TOOLS/node/tests.mjs" <<'JS'
import test from "node:test";
import assert from "node:assert/strict";
import * as text from "../tinyapp/text.mjs";

function slug(value) {
  assert.equal(typeof text.slugify, "function", "slugify is not defined");
  return text.slugify(value);
}

test("test_slugify_basic", () => {
  assert.equal(slug("Hello, World!"), "hello-world");
});

test("test_slugify_unicode", () => {
  assert.equal(slug("  Ünïcödé  Tïtle "), "unicode-title");
});

test("test_slugify_empty", () => {
  assert.equal(slug(""), "");
  assert.equal(slug("!!!"), "");
});
JS

cat > "$TOOLS/node/impl.mjs" <<'JS'
// Text helpers for tinyapp.

export function slugify(title) {
  const ascii = title
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^\x00-\x7f]/g, "");
  return ascii.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
}
JS

cat > "$TOOLS/node/refactored.mjs" <<'JS'
// Text helpers for tinyapp.

const SEPARATORS = /[^a-z0-9]+/g;
const COMBINING = /[\u0300-\u036f]/g;
const NON_ASCII = /[^\x00-\x7f]/g;
const EDGES = /^-+|-+$/g;

function toAscii(title) {
  return title.normalize("NFKD").replace(COMBINING, "").replace(NON_ASCII, "");
}

/** A url-safe slug: ascii, lowercase, single hyphens, no leading separator. */
export function slugify(title) {
  return toAscii(title).toLowerCase().replace(SEPARATORS, "-").replace(EDGES, "");
}
JS

cat > "$TOOLS/python/review.md" <<'MD'
# review findings for STORY-001

- criterion 1: tests/test_text.py::test_slugify_basic asserts the slug, not a constant.
- criterion 2: tests/test_text.py::test_slugify_unicode covers the accent rule.
- criterion 3: tests/test_text.py::test_slugify_empty covers both empty forms.
- tests unchanged since red: red_hashes match the refactor checkpoint.
- fence held: the change set is tinyapp/text.py and tests/test_text.py.
MD

cat > "$TOOLS/node/evidence.md" <<'MD'
# smoke evidence for STORY-001

| criterion | checked against | result |
|---|---|---|
| 1 | tests/text.test.mjs::test_slugify_basic at checkpoint refactor | pass |
| 2 | tests/text.test.mjs::test_slugify_unicode at checkpoint refactor | pass |
| 3 | tests/text.test.mjs::test_slugify_empty at checkpoint refactor | pass |
MD

cat > "$TOOLS/node/review.md" <<'MD'
# review findings for STORY-001

- criterion 1: tests/text.test.mjs::test_slugify_basic asserts the slug, not a constant.
- criterion 2: tests/text.test.mjs::test_slugify_unicode covers the accent rule.
- criterion 3: tests/text.test.mjs::test_slugify_empty covers both empty forms.
- tests unchanged since red: red_hashes match the refactor checkpoint.
- fence held: the change set is tinyapp/text.mjs and tests/text.test.mjs.
MD

# ------------------------------------------------------------------- per-language

lang_setup() {  # lang_setup <python|node>
  case "$1" in
    python)
      LANG_FIX="$HERE/../fixtures/dev-tdd"
      LANG_MANIFEST=pyproject.toml
      LANG_TEST=tests/test_text.py
      LANG_IMPL=tinyapp/text.py
      LANG_PAY="$TOOLS/python"
      LANG_EXT=py
      LANG_MARKER=_SEPARATORS
      LANG_RUNNER=python3
      LANG_SECTION=python
      LANG_IGNORE='.devforgeai/work/\n__pycache__/\n.pytest_cache/\n*.pyc\n'
      ;;
    node)
      LANG_FIX="$HERE/../fixtures/dev-tdd-node"
      LANG_MANIFEST=package.json
      LANG_TEST=tests/text.test.mjs
      LANG_IMPL=tinyapp/text.mjs
      LANG_PAY="$TOOLS/node"
      LANG_EXT=mjs
      LANG_MARKER=SEPARATORS
      LANG_RUNNER=node
      LANG_SECTION=node
      LANG_IGNORE='.devforgeai/work/\nnode_modules/\ndist/\n'
      ;;
    *) echo "unknown language $1" >&2; return 2 ;;
  esac
}

build_project() {  # build_project <dir> <mode>
  local W="$1" MODE="$2"
  mkdir -p "$W/.devforgeai" "$W/.claude"
  cp -r "$LANG_FIX/tinyapp" "$LANG_FIX/tests" "$LANG_FIX/$LANG_MANIFEST" \
        "$LANG_FIX/STORY-001.md" "$W/"
  cp "$HERE/fixtures/.devforgeai/stack.yaml" "$W/.devforgeai/"
  cp "$HERE/settings.claude.json" "$W/.claude/settings.json"
  printf 'version: 1\nstories: {}\nruns: {}\n' > "$W/.devforgeai/state.yaml"
  printf "$LANG_IGNORE" > "$W/.gitignore"
  if [ "$MODE" = worktree ]; then
    git -C "$W" init -q
    git -C "$W" add -A
    git -C "$W" -c user.name=fixture -c user.email=fixture@example.invalid \
      commit -qm "fixture: tinyapp before STORY-001"
  fi
}

# ------------------------------------------------------------------- readers

work_of() { echo "$1/.devforgeai/work/STORY-001/run.yaml"; }

record_key() {  # record_key <project> <dotted key>
  python3 - "$(work_of "$1")" "$2" <<'PY'
import json, sys, yaml
record = yaml.safe_load(open(sys.argv[1]))
value = record
for part in sys.argv[2].split("."):
    value = (value or {}).get(part)
print(value if isinstance(value, str) else json.dumps(value, sort_keys=True))
PY
}

phase_of() { record_key "$1" phase; }
root_of()  { record_key "$1" candidate.root; }
mode_of()  { record_key "$1" candidate.mode; }
red_hashes_of() { record_key "$1" red_hashes; }

junit_states() {  # junit_states <candidate root>  ->  "<name>=<state>" per line
  # Deliberately the literal reading of the XML — a <failure> child is a
  # failure, an <error> child is an error — and not the sequencer's own
  # `junit_dialect` normalisation. The point is to check the runner's file
  # against the story's test_plan independently of the code under test. The
  # normalisation is checked separately, by the phase advancing at all.
  python3 - "$1/.devforgeai/work/junit.xml" <<'PY'
import pathlib, sys, xml.etree.ElementTree as ET
p = pathlib.Path(sys.argv[1])
if not p.exists():
    print("NO-JUNIT-FILE=missing")
    raise SystemExit(0)
for tc in ET.parse(p).getroot().iter("testcase"):
    if tc.find("failure") is not None:
        state = "failed"
    elif tc.find("error") is not None:
        state = "error"
    elif tc.find("skipped") is not None:
        state = "skipped"
    else:
        state = "passed"
    print(f"{tc.get('name')}={state}")
PY
}

snapshot() {  # snapshot <dir>  ->  "<relpath>\t<sha256>" per line
  python3 - "$1" <<'PY'
import hashlib, os, pathlib, sys
root = pathlib.Path(sys.argv[1])
for directory, dirs, files in os.walk(root):
    # .git is the repository, .devforgeai is the sequencer's own state; the
    # question this snapshot answers is what happened to the *project*.
    dirs[:] = sorted(d for d in dirs if d not in (".git", ".devforgeai"))
    for name in sorted(files):
        p = pathlib.Path(directory) / name
        rel = p.relative_to(root).as_posix()
        try:
            digest = hashlib.sha256(p.read_bytes()).hexdigest()
        except OSError as exc:
            digest = f"UNREADABLE:{exc.errno}"
        print(f"{rel}\t{digest}")
PY
}

# ------------------------------------------------------------------- assertions

FAILS=0

ok()   { echo "  [ok]   $1"; }
bad()  { echo "  [FAIL] $1"; FAILS=$((FAILS + 1)); }
check() { if [ "$1" = 0 ]; then ok "$2"; else bad "$2"; fi; }

assert_junit() {  # assert_junit <label> <project> <expected state>
  local label="$1" W="$2" want="$3" got expect
  got="$(junit_states "$(root_of "$W")" | sort | tr '\n' ' ')"
  expect="test_slugify_basic=$want test_slugify_empty=$want test_slugify_unicode=$want "
  if [ "$got" = "$expect" ]; then
    ok "$label junit: $got"
  else
    bad "$label junit: got [$got] want [$expect]"
  fi
}

assert_equal() {  # assert_equal <label> <got> <want>
  if [ "$2" = "$3" ]; then ok "$1"; else bad "$1: got [$2] want [$3]"; fi
}

assert_absent() {  # assert_absent <project> <relpath>...
  local W="$1"; shift
  local rel
  for rel in "$@"; do
    if [ -e "$W/$rel" ]; then bad "$rel exists in the canonical tree"; else ok "no $rel"; fi
  done
}

assert_tree() {  # assert_tree <before snapshot file> <project> <allowed path>...
  local before="$1" W="$2"; shift 2
  snapshot "$W" > "$before.after"
  if python3 - "$before" "$before.after" "$@" <<'PY'
import sys


def load(path):
    rows = {}
    for line in open(path):
        line = line.rstrip("\n")
        if line:
            rel, digest = line.split("\t")
            rows[rel] = digest
    return rows


before, after = load(sys.argv[1]), load(sys.argv[2])
exact = {a for a in sys.argv[3:] if not a.endswith("/**")}
prefixes = tuple(a[:-2] for a in sys.argv[3:] if a.endswith("/**"))


def declared(path):
    return path in exact or path.startswith(prefixes)


delta = sorted(p for p in set(before) | set(after) if before.get(p) != after.get(p))
undeclared = [p for p in delta if not declared(p)]
print("changed or new in the canonical tree: " + (", ".join(delta) or "nothing"))
if undeclared:
    print("undeclared: " + ", ".join(undeclared))
    sys.exit(1)
PY
  then ok "tree delta is the write fence plus the published phase reports"
  else bad "undeclared output in the canonical tree"
  fi
}

assert_unchanged() {  # assert_unchanged <label> <before snapshot> <dir> [allowed path]...
  local label="$1" before="$2" dir="$3"; shift 3
  snapshot "$dir" > "$before.after"
  if python3 - "$before" "$before.after" "$@" <<'PY'
import sys


def load(path):
    rows = {}
    for line in open(path):
        line = line.rstrip("\n")
        if line:
            rel, digest = line.split("\t")
            rows[rel] = digest
    return rows


before, after = load(sys.argv[1]), load(sys.argv[2])
exact = {a for a in sys.argv[3:] if not a.endswith("/**")}
prefixes = tuple(a[:-2] for a in sys.argv[3:] if a.endswith("/**"))
delta = sorted(p for p in set(before) | set(after) if before.get(p) != after.get(p))
undeclared = [p for p in delta
              if p not in exact and not p.startswith(prefixes)]
if undeclared:
    print("undeclared: " + ", ".join(undeclared))
    sys.exit(1)
PY
  then ok "$label"
  else bad "$label"
  fi
}

assert_findings() {  # assert_findings <project> <agent> <payload file>
  local W="$1" agent="$2" payload="$3"
  local persisted="$W/.devforgeai/work/STORY-001/evidence/$agent/findings.md"
  if [ ! -f "$persisted" ]; then
    bad "$agent findings persisted at .devforgeai/work/STORY-001/evidence/$agent/findings.md"
    return
  fi
  if cmp -s "$persisted" "$payload"; then
    ok "$agent findings are byte-for-byte what the receipt returned"
  else
    bad "$agent findings differ from the receipt body"
  fi
  local recorded
  recorded="$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['findings_path'])" \
    "$W/.devforgeai/work/STORY-001/$4-result.json" 2>/dev/null || echo none)"
  assert_equal "$agent findings_path recorded in $4-result.json" \
    "$recorded" ".devforgeai/work/STORY-001/evidence/$agent/findings.md"
}

assert_contains() {  # assert_contains <file> <needle> <label>
  if [ -f "$1" ] && grep -qF -- "$2" "$1"; then ok "$3"; else bad "$3"; fi
}

assert_no_package_manager() {  # assert_no_package_manager <project> <section>
  if python3 - "$1/.devforgeai/stack.yaml" "$2" <<'PY'
import sys, yaml
BANNED = ("npm", "npx", "yarn", "pnpm", "corepack", "curl", "wget", "git",
          "pip", "pip3", "nuget", "dotnet")
section = yaml.safe_load(open(sys.argv[1]))[sys.argv[2]]
offenders = []
for key, entry in (section.get("commands") or {}).items():
    for token in entry.get("argv") or []:
        if str(token).split("/")[-1] in BANNED:
            offenders.append(f"commands.{key}: {token}")
for token in (section.get("runner_probe") or {}).get("argv") or []:
    if str(token).split("/")[-1] in BANNED:
        offenders.append(f"runner_probe: {token}")
if offenders:
    print("network-capable argv: " + ", ".join(offenders))
    sys.exit(1)
print("no argv in the section names a package manager or a fetcher")
PY
  then ok "no installer or fetcher is reachable from this section"
  else bad "the section names a package manager or fetcher in an argv"
  fi
}

assert_canonical_lint() {  # assert_canonical_lint <project> <section>
  # The refactor transition already ran lint inside the candidate root and
  # would have refused the phase on a non-zero exit. This runs the same
  # resolved argv against the promoted canonical tree, so "lint passed" is an
  # observation rather than an inference from the phase advancing.
  if python3 - "$1" "$2" <<'PY'
import pathlib, subprocess, sys, yaml
project, section = pathlib.Path(sys.argv[1]), sys.argv[2]
entry = yaml.safe_load((project / ".devforgeai" / "stack.yaml").read_text())
entry = entry[section]["commands"]["lint"]
argv = [str(a) for a in entry["argv"]]
p = subprocess.run(argv, cwd=project / (entry.get("cwd") or "."),
                   capture_output=True, text=True)
print(f"{' '.join(argv)} -> exit {p.returncode}")
if p.returncode:
    print((p.stdout + p.stderr)[-600:])
sys.exit(p.returncode)
PY
  then ok "lint passed against the promoted canonical tree"
  else bad "lint failed against the promoted canonical tree"
  fi
}

# ------------------------------------------------------------------- one full run

run_story() {  # run_story <language> <mode>
  local ECO="$1" MODE="$2"
  lang_setup "$ECO" || return 2
  FAILS=0
  local W; W="$(mktemp -d "$SCRATCH/dfai-demo-$ECO-$MODE-XXXX")"
  build_project "$W" "$MODE"
  local BEFORE="$TOOLS/$ECO-$MODE.snapshot"
  snapshot "$W" > "$BEFORE"
  local D="python3 $HERE/devforgeai.py"
  local A="python3 $TOOLS/agent.py $HERE $W $(work_of "$W")"

  echo; echo "############ $ECO / $MODE mode: $W"
  echo "runner: $LANG_RUNNER $("$LANG_RUNNER" --version 2>&1 | head -1)"
  echo "stack section: .devforgeai/stack.yaml#$LANG_SECTION"

  echo; echo "=== SessionStart: session evidence and the worktree self-test"
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
  printf '%s' '{"hook_event_name":"PreToolUse","session_id":"demo-session","cwd":"'"$W"'","agent_id":"a-red","agent_type":"red_dev","tool_name":"Write","tool_input":{"file_path":"'"$W/$LANG_TEST"'"}}' \
    | python3 "$HERE/dispatch.py" --provider claude --root "$W"; echo "[exit $?]"

  echo; echo "=== a worker tries to sequence: hook-only operations are refused"
  printf '%s' '{"hook_event_name":"PreToolUse","session_id":"demo-session","cwd":"'"$W"'","agent_id":"a-red","agent_type":"red_dev","tool_name":"Bash","tool_input":{"command":"devforgeai phase next"}}' \
    | python3 "$HERE/dispatch.py" --provider claude --root "$W"; echo "[exit $?]"

  echo; echo "=== the primary calls the Research Core runner: admitted, run or no run"
  printf '%s' '{"hook_event_name":"PreToolUse","session_id":"demo-session","cwd":"'"$W"'","tool_name":"Bash","tool_input":{"command":"devforgeai-research validate-run RUN-000001"}}' \
    | python3 "$HERE/dispatch.py" --provider claude --root "$W"; echo "[exit $?]"

  echo; echo "=== RED: red_dev writes the three failing tests in the candidate root"
  $A red_dev a-red red pass - "three criteria, each failing on its assertion" \
    "$LANG_TEST=$LANG_PAY/tests.$LANG_EXT"

  echo; echo "=== GREEN: green_dev finds criterion 2 underspecified and asks to rewind"
  $A green_dev a-green green fail red \
    "criterion 2 expects unicode-title but the story does not say how o-umlaut maps"
  echo "  candidate tests/ after the rewind: $(ls "$W/.devforgeai/work/STORY-001/wt/tests")"

  echo; echo "=== RED again: attempts.red is now 1 of 2"
  $A red_dev a-red red pass - "criterion 2 rewritten against the clarified rule" \
    "$LANG_TEST=$LANG_PAY/tests.$LANG_EXT"
  echo "--- assertions after red"
  assert_junit red "$W" failed
  local RED_HASHES; RED_HASHES="$(red_hashes_of "$W")"
  echo "  red_hashes: $RED_HASHES"

  echo; echo "=== GREEN: green_dev implements slugify; the oracle runs the suite"
  $A green_dev a-green green pass - "smallest change that satisfies the frozen tests" \
    "$LANG_IMPL=$LANG_PAY/impl.$LANG_EXT"
  echo "--- assertions after green"
  assert_junit green "$W" passed
  assert_equal "red_hashes unchanged through green" "$(red_hashes_of "$W")" "$RED_HASHES"

  echo; echo "=== REFACTOR: the oracle runs test then lint"
  $A refactor_dev a-refactor refactor pass - "extracted the separator pattern" \
    "$LANG_IMPL=$LANG_PAY/refactored.$LANG_EXT"
  echo "--- assertions after refactor"
  assert_junit refactor "$W" passed
  assert_equal "red_hashes unchanged through refactor" "$(red_hashes_of "$W")" "$RED_HASHES"
  # check_green runs the lint key when the run authorises it and refuses the
  # phase on a non-zero exit, so a refactor that advanced is a lint that passed.
  assert_equal "refactor advanced with lint authorised" \
    "$(phase_of "$W") $(record_key "$W" commands.use)" 'smoke ["test", "lint"]'

  echo; echo "=== a judge holds no write tool at all: a project file is denied"
  local CR; CR="$(root_of "$W")"
  printf '%s' '{"hook_event_name":"PreToolUse","session_id":"demo-session","cwd":"'"$CR"'","agent_id":"a-smoke","agent_type":"smoke_qa","tool_name":"Write","tool_input":{"file_path":"'"$CR/$LANG_IMPL"'"}}' \
    | python3 "$HERE/dispatch.py" --provider claude --root "$W"; echo "[exit $?]"

  echo; echo "=== ... and so is the run's own evidence directory: there is no scratch path"
  printf '%s' '{"hook_event_name":"PreToolUse","session_id":"demo-session","cwd":"'"$CR"'","agent_id":"a-smoke","agent_type":"smoke_qa","tool_name":"Write","tool_input":{"file_path":"'"$CR/.devforgeai/work/STORY-001/evidence/smoke_qa/notes.md"'"}}' \
    | python3 "$HERE/dispatch.py" --provider claude --root "$W"; echo "[exit $?]"

  # What the two judge phases must leave exactly as they found it.
  local JCAND="$TOOLS/$ECO-$MODE.judge-candidate" JCANON="$TOOLS/$ECO-$MODE.judge-canonical"
  snapshot "$CR" > "$JCAND"
  snapshot "$W" > "$JCANON"

  echo; echo "=== SMOKE: the judge returns findings in the receipt; the sequencer persists them"
  DFAI_FINDINGS="$LANG_PAY/evidence.md" DFAI_CTX_OUT="$TOOLS/$ECO-$MODE.smoke-ctx" \
    $A smoke_qa a-smoke smoke pass - "each criterion checked once against the checkpoint"
  echo "--- assertions after smoke"
  assert_findings "$W" smoke_qa "$LANG_PAY/evidence.md" smoke
  assert_contains "$TOOLS/$ECO-$MODE.smoke-ctx" \
    "the receipt's \`findings\` field" "smoke_qa is told to return findings, not write a file"

  echo; echo "=== REVIEW: the critic is handed smoke_qa's findings path and judges"
  DFAI_FINDINGS="$LANG_PAY/review.md" DFAI_CTX_OUT="$TOOLS/$ECO-$MODE.review-ctx" \
    $A dev_critic a-critic review pass - "criteria covered, tests frozen, fence held"
  echo "--- assertions after review"
  assert_findings "$W" dev_critic "$LANG_PAY/review.md" review
  assert_contains "$TOOLS/$ECO-$MODE.review-ctx" \
    ".devforgeai/work/STORY-001/evidence/smoke_qa/findings.md" \
    "dev_critic's dispatch context names smoke_qa's findings path"
  assert_unchanged "the judge phases changed nothing in the candidate root" "$JCAND" "$CR"
  # The only canonical delta the two judge phases produce is the sequencer's own
  # rendered phase report; no judge wrote it and no judge could have.
  assert_unchanged "the judge phases changed nothing in the canonical project tree" \
    "$JCANON" "$W" "docs/reports/**"
  assert_equal "the handoff names both findings files" \
    "$(python3 -c "import json,sys;print(len(json.load(open(sys.argv[1]))['findings_paths']))" \
       "$W/.devforgeai/work/STORY-001/handoff.json")" 2

  echo; echo "=== the user reads the reports, then promotes: the fifth model-callable form"
  (cd "$W" && $D promote STORY-001)

  echo; echo "=== final state"
  (cd "$W" && $D status)
  echo "provenance log:"; cut -c1-140 "$W/.devforgeai/provenance/log.jsonl"

  echo; echo "--- assertions after promote"
  local OUTCOME STATUS PROMOTED
  OUTCOME="$(python3 -c "import json;print(json.load(open('$W/.devforgeai/work/STORY-001/handoff.json'))['outcome'])" 2>/dev/null || echo none)"
  STATUS="$(python3 -c "import yaml;print(yaml.safe_load(open('$W/.devforgeai/state.yaml'))['runs']['STORY-001']['status'])" 2>/dev/null || echo none)"
  if grep -q "$LANG_MARKER" "$W/$LANG_IMPL" 2>/dev/null; then PROMOTED=yes; else PROMOTED=no; fi
  assert_equal "handoff outcome" "$OUTCOME" pass
  assert_equal "run status" "$STATUS" promoted
  assert_equal "refactored code is in the canonical tree" "$PROMOTED" yes
  # The write fence, and `docs/reports/**` — promotion publishes each phase
  # report there, which is the sequencer's own declared output rather than
  # anything a worker produced. Everything else in the canonical tree must be
  # byte-identical to what build_project laid down: no cache directory, no
  # lockfile, no installed dependency, no stray artifact of running the suite.
  assert_tree "$BEFORE" "$W" "$LANG_IMPL" "$LANG_TEST" "docs/reports/**"
  assert_no_package_manager "$W" "$LANG_SECTION"
  assert_canonical_lint "$W" "$LANG_SECTION"
  if [ "$ECO" = node ]; then
    assert_absent "$W" node_modules package-lock.json npm-shrinkwrap.json .npmrc
  fi

  local RESULT
  echo "$ECO/$MODE: outcome=$OUTCOME run_status=$STATUS canonical_has_refactored_code=$PROMOTED assertions_failed=$FAILS"
  if [ "$OUTCOME" = pass ] && [ "$STATUS" = promoted ] && [ "$PROMOTED" = yes ] \
     && [ "$FAILS" = 0 ]; then
    RESULT="green"
  else
    RESULT="RED"
  fi
  echo "$ECO/$MODE result: $RESULT (scratch $W)"
  [ "$RESULT" = green ]
}

# ------------------------------------------------------------------- the four runs

runner_missing() {  # runner_missing <language> <argv0>
  echo
  echo "############ $1 runs: COULD_NOT_RUN"
  echo "$1/copy result: COULD_NOT_RUN (runner_missing: $2 is not on PATH)"
  echo "$1/worktree result: COULD_NOT_RUN (runner_missing: $2 is not on PATH)"
  echo "Install $2 and re-run; this demo never installs a runtime for you."
}

PY_COPY=RED
PY_WT=RED
NODE_COPY=RED
NODE_WT=RED

if command -v python3 >/dev/null 2>&1; then
  run_story python copy     && PY_COPY=green
  run_story python worktree && PY_WT=green
else
  runner_missing python "python3"
  PY_COPY=COULD_NOT_RUN; PY_WT=COULD_NOT_RUN
fi

if command -v node >/dev/null 2>&1; then
  run_story node copy     && NODE_COPY=green
  run_story node worktree && NODE_WT=green
else
  runner_missing node "node"
  NODE_COPY=COULD_NOT_RUN; NODE_WT=COULD_NOT_RUN
fi

echo
if [ "$PY_COPY" = green ] && [ "$PY_WT" = green ] \
   && [ "$NODE_COPY" = green ] && [ "$NODE_WT" = green ]; then
  echo "DEMO OK: python copy/worktree green, node copy/worktree green"
  exit 0
fi
echo "DEMO FAILED: python copy=$PY_COPY worktree=$PY_WT, node copy=$NODE_COPY worktree=$NODE_WT"
exit 1
