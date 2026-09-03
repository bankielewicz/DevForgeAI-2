#!/usr/bin/env python3
"""Pure policy helpers shared by the hook dispatcher and phase sequencer.

This module performs no writes.  Keeping the skill/phase registry, path
parsing, and tech-stack checks in one place makes the fast hook check and the
authoritative transition check use the same rules.

The registry below is the single source of truth for:
  * which phases a skill has, in order;
  * which phases dispatch a worker, and which worker;
  * per-phase `max_attempts` (decision 11: no "2x/3x" notation);
  * what a phase may write (tests, code, docs, story fields, or evidence only);
  * which stack command keys a phase grants;
  * which earlier phase a phase may rewind to.
"""
from __future__ import annotations

import fnmatch
import os
import re
from dataclasses import dataclass
from pathlib import Path


IGNORED_DIRS = {
    ".agents", ".claude", ".codex", ".devforgeai", ".git", ".mypy_cache",
    ".pytest_cache", ".ruff_cache", ".venv", "__pycache__", "bin", "node_modules",
    "obj",
}

RESULT_SCHEMA = "devforgeai.worker-result/v1"

# Closed worker status vocabulary (decision 1). `could_not_run` carries a
# reason_code; nothing else does.
WORKER_STATUS = {"pass", "fail", "needs_user", "could_not_run"}
REASON_CODES = {"runner_missing", "timeout", "network", "hook_fault"}

# The receipt (D4). The worker writes inside the candidate root and returns this
# object; the sequencer derives what actually changed from the checkpoint diff.
RECEIPT_KEYS = {
    "schema", "run", "skill", "phase", "agent", "status", "reason_code",
    "candidate", "claimed_paths", "evidence_refs", "note", "issues", "next",
}
RECEIPT_REQUIRED = {
    "schema", "run", "skill", "phase", "agent", "status", "candidate", "claimed_paths",
}
MAX_CLAIMED_PATHS = 64
MAX_EVIDENCE_REFS = 16

# Refusal reasons the sequencer prints verbatim so a caller can match on them.
REFUSALS = {
    "STALE_BASE", "MERGE_CONFLICT", "DIRTY_TARGET", "FENCE_OVERLAP",
    "LEASE_HELD", "UNCLAIMED_CHANGE", "NO_CANDIDATE",
}

# The candidate root is a materialised project tree, and therefore has a
# `.devforgeai/` of its own. The marker below is what tells the two apart, and it
# is the one path inside a root that is neither checkpointed nor promoted.
RUN_MARKER = ".devforgeai/candidate"
WORK_PREFIX = ".devforgeai/work/"

# gate_policy is a defect-to-action map, never a returned status.
GATE_POLICIES = {"BLOCK", "REQUIRE_HUMAN", "WARN", "OFF"}

# Transition-oracle result classification (plan new contract 5).
CLASSIFICATIONS = {
    "PASS", "EXPECTED_TEST_FAILURE", "NO_TESTS", "COLLECTION_ERROR",
    "INFRA_FAILURE", "TIMEOUT", "TEST_FAILURE",
}

# Report verdict, closed. A report-producing phase records how its own report
# reads; the run's status is unaffected — reporting a defect is a passing run.
# The sequencer uses it to select the handoff row, nothing else.
REPORT_VERDICTS = {"pass", "findings", "fail"}

# The only (skill, phase) pairs whose `evidence` may carry `verdict`. Every
# other phase carrying the key is refused, so the field cannot drift into a
# second status vocabulary.
VERDICT_PHASES: set[tuple[str, str]] = {
    ("review", "report"), ("qa", "report"), ("skill-validator", "report"),
}

# The handoff `next` a non-`pass` verdict selects. `pass` keeps the default the
# skill's kind already produces.
VERDICT_NEXT: dict[str, str] = {
    "review": "/dev {arg} --fix",
    "qa": "/dev {arg} --fix",
    "skill-validator": "/skill-gen {arg} --fix",
}

# The frontmatter keys a field-restricted phase (`writes: fields`) may change.
STORY_FIELD_KEYS = ("blocked_by", "size", "sprint")

# ---------------------------------------------------------------------------
# CLI grammar (plan new contract 1). Closed on both axes.
# ---------------------------------------------------------------------------
# Model-callable: appear in the provider Bash allowlist and need no hook env.
# `run <key>` is model-callable to the lease holder only: the producer working
# inside the candidate root runs the tests it was given keys for, and the
# sequencer executes the argv with cwd = candidate.root.
MODEL_CALLABLE = {
    "status": "devforgeai status",
    "phase start": "devforgeai phase start <skill> <arg> [--lenient]",
    "phase fail": "devforgeai phase fail --reason <text>",
    "validate": "devforgeai validate",
    "promote": "devforgeai promote <run>",
    "run": "devforgeai run <key>",
}
# The five forms a primary window may type (D7). `run <key>` is the sixth form
# and belongs to the lease holder inside the candidate root, never the primary.
PRIMARY_CALLABLE = ("status", "phase start", "phase fail", "validate", "promote")

# Hook-only: refused unless DEVFORGEAI_HOOK_EVENT names the matching event.
HOOK_ONLY = {
    "session-start": "SessionStart",
    "lease-bind": "SubagentStart",
    "ingest-result": "SubagentStop",
    "phase next": "SubagentStop",
}
# Sequencer-internal candidate operations, refused unless the caller is a hook or
# the sequencer itself: `phase start` calls `candidate open`, SubagentStart calls
# `candidate lease`, `ingest-result` calls `candidate checkpoint`, `promote`
# calls `candidate promote`, and `phase fail` calls `candidate abandon` when the
# policy says abandon.
CANDIDATE_OPS = ("open", "lease", "checkpoint", "promote", "abandon")

# Provider-facing worker names are canonical. Codex custom-agent names and
# Claude agent frontmatter `name:` values are identical, so `agent_type` from
# either provider needs no translation. The long framework role IDs used by
# earlier drafts remain accepted as aliases.
AGENT_ALIASES = {
    "dev-tdd-red-tester": "red_dev",
    "dev-tdd-green-implementer": "green_dev",
    "dev-tdd-refactorer": "refactor_dev",
    "dev-tdd-smoke-qa": "smoke_qa",
    "dev-tdd-critic": "dev_critic",
    "red-tester": "red_dev",
    "green-implementer": "green_dev",
    "refactorer": "refactor_dev",
    "smoke-qa": "smoke_qa",
    "critic": "dev_critic",
}


def _phase(name, agent=None, writes="none", attempts=2, run_keys=(), oracle="report_only",
           rewind_to=None, conditional=False, field_fence=(), fields=()):
    return {
        "name": name,
        "agent": agent,
        "writes": writes,
        "max_attempts": attempts,
        "run_keys": set(run_keys),
        "oracle": oracle,
        "rewind_to": rewind_to,
        # `writes: fields` only. `field_fence` is the narrower path set inside
        # the run fence this phase may update (`{arg}` substituted at gate
        # time); `fields` is the closed set of frontmatter keys its proposal may
        # change. Body bytes and every other key must be identical.
        "field_fence": list(field_fence),
        "fields": set(fields),
        # A `writes: docs` phase whose artifact is owed only under a condition
        # the run may not meet. The document oracle accepts an empty file set
        # from such a phase when the result says, in its note, why none was
        # owed; every other `writes: docs` phase must produce a file.
        "conditional": conditional,
    }


def _doc(name, agent, writes="docs", attempts=2, oracle="document", conditional=False):
    return _phase(name, agent=agent, writes=writes, attempts=attempts, oracle=oracle,
                  conditional=conditional)


# ---------------------------------------------------------------------------
# Skill registry: all 18 roster skills plus the dev-tdd variant of dev.
#   kind    story    -> `phase start <skill> <STORY-ID>`, story v3 gate
#           document -> `phase start <skill> <slug|doc-id>`, document fence gate
#           none     -> zero LLM workers (decision 14); phase start refuses
#           external -> wraps a separate runner (research)
#   fence   document-fence path patterns; `{arg}` is substituted at gate time.
#   anchor  "story" on a document skill whose `<arg>` is a story id: the story
#           gate also runs and the story's commands, test_plan and gate_policy
#           are copied into the run record, so the phase's run keys can
#           be brokered. The fence stays the document fence, so those runs read
#           code and tests and write only their report.
# ---------------------------------------------------------------------------
SKILLS: dict[str, dict] = {
    "init": {
        "kind": "none",
        "phases": [],
        "fence": [],
        "note": "zero LLM workers; SKILL.md is a thin wrapper over the installer",
    },
    "status": {
        "kind": "none",
        "phases": [],
        "fence": [],
        "note": "zero LLM workers; prints the run block",
    },
    "research": {
        "kind": "external",
        "runner": "devforgeai-research",
        "phases": [],
        "fence": ["docs/research/{arg}/**"],
        "note": "wraps the Research Core CLI; execution is out of scope here",
    },
    "onboard": {
        "kind": "document",
        "fence": ["docs/architecture/sourcetree.md", "docs/architecture/techstack.md",
                  "docs/architecture/architecture.md", ".devforgeai/stack.yaml"],
        "phases": [
            _doc("code_map", "code_mapper"),
            _doc("doc_ingest", "doc_ingester"),
            _doc("convention_infer", "convention_inferrer"),
            _doc("observed_write", "observed_writer"),
            _phase("critic", agent="onboard_critic"),
        ],
    },
    "brainstorm": {
        "kind": "document",
        "fence": ["docs/brainstorm/{arg}.md"],
        "phases": [
            _doc("capture", "idea_capturer"),
            _phase("research_request", agent="research_requester"),
            _doc("cluster", "idea_clusterer"),
            _doc("write", "brainstorm_writer"),
            _phase("critic", agent="brainstorm_critic"),
        ],
    },
    "pm": {
        "kind": "document",
        "fence": ["docs/PM/{arg}/prd.md", "docs/PM/{arg}/backlog-ideas.md"],
        "phases": [
            _doc("scope_split", "scope_splitter"),
            _doc("prd", "prd_writer"),
            _doc("backlog", "backlog_archiver"),
            _phase("critic", agent="pm_critic"),
        ],
    },
    # architect writes mandates into constitution.md#mandates and nothing else
    # about skills: `plan` is the sole owner of the skill-spec template
    # (decision 13), so no architect phase is fenced to docs/plan/**.
    "architect": {
        "kind": "document",
        "fence": ["docs/architecture/**", ".devforgeai/stack.yaml",
                  ".devforgeai/provenance/adr/**"],
        "phases": [
            _phase("option_compare", agent="option_comparer"),
            _doc("constitution", "constitution_writer"),
            _doc("sourcetree", "sourcetree_writer"),
            _doc("techstack", "techstack_writer"),
            _doc("architecture", "architecture_writer"),
            _doc("design", "design_writer"),
            _doc("adr", "adr_writer"),
            _phase("gap_analysis", agent="gap_analyzer"),
            _phase("critic", agent="architect_critic"),
        ],
    },
    "plan": {
        "kind": "document",
        "fence": ["docs/plan/{arg}/**"],
        "phases": [
            _doc("epics", "epic_writer"),
            _doc("stories", "story_writer"),
            # Conditional: a skill spec is owed only when a story's
            # `requires_skill` names a skill that does not exist yet. A plan
            # whose stories all use installed skills produces none, and the
            # worker says so in its note rather than inventing a document.
            _doc("skill_specs", "skill_spec_writer", conditional=True),
            # `dependencies` and `estimates` run after `stories` and set three
            # frontmatter keys on the stories that phase wrote. They are not
            # `writes: none` — that made `08-story-specification.md`'s producer
            # table undeliverable — and they are not `writes: docs` either: the
            # sequencer accepts a proposal only when the body is byte-identical
            # and the diff touches nothing but `blocked_by`, `size`, `sprint`.
            _phase("dependencies", agent="dependency_mapper", writes="fields",
                   field_fence=["docs/plan/{arg}/stories/*.md"], fields=STORY_FIELD_KEYS),
            _phase("estimates", agent="estimator", writes="fields",
                   field_fence=["docs/plan/{arg}/stories/*.md"], fields=STORY_FIELD_KEYS),
            _doc("sprints", "sprint_writer"),
            _phase("critic", agent="plan_critic"),
        ],
    },
    "clarify": {
        "kind": "document",
        "fence": ["docs/plan/*/stories/{arg}.md"],
        "phases": [
            _phase("find_ambiguity", agent="ambiguity_finder"),
            _doc("questions", "question_writer"),
            _doc("record_answers", "answer_recorder"),
        ],
    },
    "analyze": {
        "kind": "document",
        "fence": ["docs/reports/analyze-{arg}.md"],
        "phases": [
            _phase("cross_reference", agent="cross_referencer"),
            _phase("orphans", agent="orphan_finder"),
            _phase("stale_hashes", agent="stale_hash_finder"),
            _doc("report", "analyze_report_writer"),
        ],
    },
    "skill-generator": {
        "kind": "document",
        "fence": [".devforgeai/skills/{arg}/**"],
        "phases": [
            _phase("read_spec", agent="spec_reader"),
            _doc("skill_yaml", "skill_yaml_writer"),
            _doc("subagents", "subagent_writer"),
            _doc("templates", "template_writer"),
            _doc("compile_claude", "claude_compiler"),
            _doc("compile_codex", "codex_compiler"),
        ],
    },
    "skill-validator": {
        "kind": "document",
        "fence": ["docs/reports/validate-{arg}.md"],
        "phases": [
            _phase("anatomy", agent="anatomy_checker"),
            _phase("provider", agent="provider_checker"),
            _phase("spec_conformance", agent="spec_conformance_checker"),
            _doc("report", "validate_report_writer"),
        ],
    },
    "dev": {
        "kind": "story",
        "fence": None,  # the story's write_fence
        "phases": [
            _phase("red", agent="red_dev", writes="tests", attempts=2,
                   run_keys={"test"}, oracle="red"),
            _phase("green", agent="green_dev", writes="code", attempts=3,
                   run_keys={"test", "build"}, oracle="green", rewind_to="red"),
            _phase("refactor", agent="refactor_dev", writes="code", attempts=2,
                   run_keys={"test", "build", "lint"}, oracle="refactor", rewind_to="red"),
            _phase("smoke", agent="smoke_qa", writes="none", attempts=2,
                   run_keys={"test"}, oracle="report_only"),
            _phase("review", agent="dev_critic", writes="none", attempts=2,
                   oracle="report_only"),
        ],
    },
    "review": {
        "kind": "document",
        "anchor": "story",
        "fence": ["docs/reports/review-{arg}.md"],
        "phases": [
            _phase("compliance", agent="compliance_checker"),
            _phase("security", agent="security_checker"),
            _phase("style", agent="style_checker"),
            _doc("report", "review_writer"),
        ],
    },
    "qa": {
        "kind": "document",
        "anchor": "story",
        "fence": ["docs/reports/qa-{arg}.md"],
        "phases": [
            _phase("run_tests", agent="test_runner", run_keys={"test"}, oracle="green"),
            _phase("criteria", agent="criteria_checker"),
            _phase("evidence", agent="evidence_collector"),
            _doc("report", "qa_writer"),
        ],
    },
    "amend": {
        "kind": "document",
        "fence": ["docs/architecture/**", "docs/reports/impact-{arg}.md",
                  ".devforgeai/provenance/adr/**"],
        "phases": [
            _doc("apply_change", "change_applier"),
            _doc("adr", "amend_adr_writer"),
            _phase("impact", agent="impact_analyzer"),
            _doc("resync", "resync_slicer"),
        ],
    },
    "retro": {
        "kind": "document",
        "fence": ["docs/reports/retro-{arg}.md"],
        "phases": [
            _phase("collect", agent="report_collector"),
            _phase("lessons", agent="lesson_extractor"),
            _phase("amendments", agent="amendment_proposer"),
            _doc("archive", "archiver"),
        ],
    },
    "drift": {
        "kind": "document",
        "fence": ["docs/reports/drift-{arg}.md"],
        "phases": [
            _phase("code_map", agent="code_mapper"),
            _phase("doc_diff", agent="doc_differ"),
            _doc("report", "drift_writer"),
        ],
    },
}

# A phase that dispatches a worker and produces no artifact is a judge (D1): it
# reads a checkpoint and reports. Its one write path is its own evidence
# directory under the run's work tree, which is gitignored, never diffed and
# never promoted, so `writes: evidence` is the mode, not `writes: none`.
for _spec in SKILLS.values():
    for _phase_spec in _spec.get("phases", []):
        if _phase_spec["agent"] and _phase_spec["writes"] == "none":
            _phase_spec["writes"] = "evidence"

# dev-tdd is a variant of dev (decision 15), not a separate phase list.
SKILL_VARIANTS = {"dev-tdd": "dev"}


def evidence_prefix(enforcement: dict) -> str:
    """The one path a judge may write: its own directory in the run's work tree."""
    spec = phase_spec(enforcement.get("skill", ""), enforcement.get("phase", "")) or {}
    return f".devforgeai/work/{enforcement.get('run')}/evidence/{spec.get('agent')}/"


def skill_key(name: str) -> str:
    return SKILL_VARIANTS.get(name, name)


def skill_spec(name: str) -> dict | None:
    return SKILLS.get(skill_key(name))


def phase_names(name: str) -> list[str]:
    spec = skill_spec(name)
    return [p["name"] for p in (spec or {}).get("phases", [])]


def phase_spec(skill: str, phase: str) -> dict | None:
    for candidate in (skill_spec(skill) or {}).get("phases", []):
        if candidate["name"] == phase:
            return candidate
    return None


def worker_agents() -> set[str]:
    """Every agent name any phase of any skill dispatches."""
    names = set()
    for spec in SKILLS.values():
        for phase in spec.get("phases", []):
            if phase["agent"]:
                names.add(phase["agent"])
    return names


def canonical_agent(name: str) -> str:
    return AGENT_ALIASES.get(name, name)


def allowed_agents(enforcement: dict) -> set[str]:
    spec = phase_spec(enforcement.get("skill", ""), enforcement.get("phase", ""))
    return {spec["agent"]} if spec and spec["agent"] else set()


def phase_run_keys(enforcement: dict) -> set[str]:
    spec = phase_spec(enforcement.get("skill", ""), enforcement.get("phase", ""))
    return set(spec["run_keys"]) if spec else set()


def run_id(skill: str, arg: str) -> str:
    """Directory name under .devforgeai/work/."""
    spec = skill_spec(skill) or {}
    if spec.get("kind") == "story":
        return arg
    return f"{skill_key(skill)}-{arg}"


def document_fence(skill: str, arg: str) -> list[str]:
    spec = skill_spec(skill) or {}
    return [pattern.replace("{arg}", arg) for pattern in (spec.get("fence") or [])]


def story_anchored(skill: str) -> bool:
    """A document skill whose `<arg>` is a story id (`qa`, `review`)."""
    return (skill_spec(skill) or {}).get("anchor") == "story"


class PolicyError(ValueError):
    """The event or policy cannot be interpreted safely."""


@dataclass(frozen=True)
class PatchTarget:
    """One path touched by an apply_patch request and its proposed additions."""

    path: str
    added_text: str = ""


# Paths no worker result may ever carry, on any skill. `.devforgeai/skills/**`
# is deliberately absent: skill-generator's document fence writes there and the
# sequencer still applies it. Everything the sequencer itself owns is denied.
ALWAYS_DENY = [
    ".devforgeai/state.yaml", ".devforgeai/stack.yaml", ".devforgeai/work/**",
    ".devforgeai/provenance/**", ".devforgeai/sessions/**", ".devforgeai/hooks/**",
    ".devforgeai/research-cas/**",
    ".claude/**", ".codex/**", ".agents/**", ".git/**",
    "CLAUDE.md", "AGENTS.md",
]

# The carve-outs from ALWAYS_DENY, keyed by path pattern. Each entry names an
# artifact whose registry home is under `.devforgeai/` and whose declared
# producers (11-artifact-registry.md section 2) therefore have no other write
# path. Exactly those `(skill, phase)` pairs may propose a matching path, and
# only through a result the sequencer validates against the artifact's contract
# before applying it (10-sequencer-and-contracts.md section 5.2, step 13):
#   * `.devforgeai/stack.yaml`        -> `schemas/devforgeai/v1/stack.schema.json`
#   * `.devforgeai/provenance/adr/**` -> the `adr` template header
# Every other path under `.devforgeai/` stays denied to every skill and phase.
# Both declared producers of the `adr` template have the exception and the fence
# entry: `amend`'s `adr` phase records a decision reached while amending, and
# `architect`'s `adr` phase records one reached while designing.
PRODUCER_EXCEPTIONS: dict[str, set[tuple[str, str]]] = {
    ".devforgeai/stack.yaml": {("architect", "techstack"), ("onboard", "code_map")},
    ".devforgeai/provenance/adr/**": {("amend", "adr"), ("architect", "adr")},
}


def producers_for(path: str) -> set[tuple[str, str]]:
    """Every declared `(skill, phase)` producer of `path`, across all patterns."""
    owners: set[tuple[str, str]] = set()
    for pattern, pairs in PRODUCER_EXCEPTIONS.items():
        if matches(path, [pattern]):
            owners |= pairs
    return owners


def producer_exception(path: str, skill: str, phase: str) -> bool:
    """True when this exact skill and phase is a declared producer of `path`."""
    return (skill_key(skill), phase) in producers_for(path)


def skill_produces(path: str, skill: str) -> bool:
    """True when any phase of `skill` is a declared producer of `path`."""
    return any(owner == skill_key(skill) for owner, _ in producers_for(path))


# git subcommands with no writing mode. Everything else — `add`, `commit`,
# `merge`, `rebase`, `checkout`, `reset`, `clean`, `push`, `worktree`, `tag` —
# belongs to the sequencer, which owns the candidate root's history.
GIT_READ_ONLY = {"blame", "diff", "log", "ls-files", "rev-parse", "show", "status"}


def effective_fence(skill: str, fence) -> list[str]:
    """The fence plus every producer-exception path this skill may write.

    `FENCE_OVERLAP` counts `.devforgeai/stack.yaml` and
    `.devforgeai/provenance/adr/**` as fence members, so two runs that could
    both propose the same sequencer-owned artifact cannot be active at once.
    """
    patterns = list(fence or [])
    for pattern in PRODUCER_EXCEPTIONS:
        if skill_produces(pattern, skill) and pattern not in patterns:
            patterns.append(pattern)
    return patterns


def patterns_overlap(left: str, right: str) -> bool:
    """True when two fence patterns can name the same path."""
    if left == right:
        return True
    trimmed = (left.rstrip("*").rstrip("/"), right.rstrip("*").rstrip("/"))
    return (
        matches(left, [right]) or matches(right, [left])
        or matches(trimmed[0], [right]) or matches(trimmed[1], [left])
    )


def fence_overlap(left, right) -> list[str]:
    """Every pattern pair two fences share, sorted; empty when they are disjoint."""
    hits = {
        f"{a} ~ {b}"
        for a in left or [] for b in right or [] if patterns_overlap(str(a), str(b))
    }
    return sorted(hits)


def matches(path: str, patterns) -> bool:
    """Match repository-relative POSIX paths, including root files for **/*.x."""
    for raw in patterns or []:
        pattern = str(raw).replace("\\", "/")
        if (
            fnmatch.fnmatchcase(path, pattern)
            or path == pattern.rstrip("/")
            or (pattern.startswith("**/") and fnmatch.fnmatchcase(path, pattern[3:]))
        ):
            return True
        if pattern.endswith("/**") and path.startswith(pattern[:-3].rstrip("/") + "/"):
            return True
    return False


def project_relative(root: Path, raw: str) -> str:
    """Return a canonical project-relative path, rejecting root and escapes."""
    if not isinstance(raw, str) or not raw.strip() or "\x00" in raw:
        raise PolicyError("write tool did not provide a usable file path")
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = root / candidate
    resolved_root = root.resolve()
    resolved = candidate.resolve(strict=False)
    try:
        relative = resolved.relative_to(resolved_root).as_posix()
    except ValueError as exc:
        raise PolicyError(f"path {raw!r} is outside the project root") from exc
    if relative in ("", "."):
        raise PolicyError("the project root is not a writable file target")
    return relative


def validate_phase_write_path(root: Path, enforcement: dict, raw: str) -> str:
    """Return a canonical target or fail the run fence and phase policy."""
    path = project_relative(root, raw)
    skill = enforcement.get("skill", "")
    phase = enforcement.get("phase", "")
    spec_mode = (phase_spec(skill, phase) or {}).get("writes", "none")
    if spec_mode == "evidence":
        prefix = evidence_prefix(enforcement)
        if not path.startswith(prefix):
            raise PolicyError(
                f"phase {phase} judges this checkpoint; its only write path is {prefix}, "
                f"not {path}"
            )
        return path
    if matches(path, ALWAYS_DENY) and not producer_exception(path, skill, phase):
        owners = sorted(producers_for(path))
        detail = f"; only {owners} may propose it" if owners else ""
        raise PolicyError(f"{path} is sequencer-owned; no phase may write it{detail}")
    fence = enforcement.get("write_fence") or []
    if not matches(path, fence):
        raise PolicyError(f"{path} is outside write_fence {fence}")
    tests = enforcement.get("test_paths") or []
    spec = phase_spec(enforcement.get("skill", ""), enforcement.get("phase", ""))
    mode = spec["writes"] if spec else "none"
    is_test = matches(path, tests)
    if mode in ("none", "evidence"):
        raise PolicyError(
            f"phase {enforcement.get('phase')} changes no project file; it reports"
        )
    if mode == "tests" and not is_test:
        raise PolicyError(f"phase red may write only test_plan files, not {path}")
    if mode == "code" and is_test:
        raise PolicyError(
            f"phase {enforcement.get('phase')} may not touch tests; return "
            'status fail with next "red" instead'
        )
    if mode == "fields" and not matches(path, phase_field_fence(enforcement)):
        raise PolicyError(
            f"phase {enforcement.get('phase')} may update only "
            f"{phase_field_fence(enforcement)}, not {path}"
        )
    return path


def phase_field_fence(enforcement: dict) -> list[str]:
    """The `writes: fields` path set, with `{arg}` substituted from the run.

    A field-restricted phase writes inside the run fence but not across all of
    it: it updates declared frontmatter keys of already-written artifacts, and
    this is the narrower pattern list that says which ones.
    """
    spec = phase_spec(enforcement.get("skill", ""), enforcement.get("phase", "")) or {}
    arg = str(enforcement.get("arg") or "")
    return [pattern.replace("{arg}", arg) for pattern in spec.get("field_fence") or []]


def phase_fields(enforcement: dict) -> set[str]:
    """The frontmatter keys a `writes: fields` phase may change."""
    spec = phase_spec(enforcement.get("skill", ""), enforcement.get("phase", "")) or {}
    return set(spec.get("fields") or ())


def parse_apply_patch(command: str) -> list[PatchTarget]:
    """Extract every source/destination path and added line from Codex patch text.

    The parser intentionally accepts only the documented apply_patch envelope.
    An unfamiliar header is denied instead of guessing which file it mutates.
    """
    if not isinstance(command, str):
        raise PolicyError("apply_patch tool_input.command must be a string")
    body = command.strip("\r\n")
    lines = body.splitlines()
    if len(lines) < 3 or lines[0] != "*** Begin Patch" or lines[-1] != "*** End Patch":
        raise PolicyError("apply_patch is missing the exact Begin Patch/End Patch envelope")

    order: list[str] = []
    additions: dict[str, list[str]] = {}
    current: str | None = None
    directive = re.compile(r"^\*\*\* (Add|Update|Delete) File: (.+)$")
    move = re.compile(r"^\*\*\* Move to: (.+)$")

    for line in lines[1:-1]:
        match = directive.match(line)
        if match:
            current = match.group(2).strip()
            if not current:
                raise PolicyError("apply_patch contains an empty file header")
            if current not in additions:
                order.append(current)
                additions[current] = []
            continue
        moved = move.match(line)
        if moved:
            if current is None:
                raise PolicyError("apply_patch Move to appears before a file header")
            source = current
            destination = moved.group(1).strip()
            if not destination:
                raise PolicyError("apply_patch contains an empty Move to header")
            if destination not in additions:
                order.append(destination)
                additions[destination] = []
            additions[destination].extend(additions[source])
            current = destination
            continue
        if line.startswith("*** ") and line != "*** End of File":
            raise PolicyError(f"unsupported apply_patch directive: {line}")
        if current is None:
            if line.strip():
                raise PolicyError("apply_patch content appears before a file header")
            continue
        if line.startswith("+") and not line.startswith("+++"):
            additions[current].append(line[1:])

    if not order:
        raise PolicyError("apply_patch contains no file directives")
    return [PatchTarget(path, "\n".join(additions[path])) for path in order]


def _regex(pattern: str, text: str):
    try:
        return list(re.finditer(pattern, text, re.MULTILINE))
    except re.error as exc:
        raise PolicyError(f"invalid stack policy regex {pattern!r}: {exc}") from exc


def stack_extractors(stack: dict) -> list[dict]:
    """Section-level `extractors[]` with the legacy packages.extractors fallback."""
    extractors = stack.get("extractors")
    if extractors:
        return list(extractors)
    packages = stack.get("packages") or {}
    if packages.get("extractors"):
        return list(packages["extractors"])
    if packages.get("dependency_regex"):
        return [{"paths": stack.get("manifests") or [], "regex": packages["dependency_regex"]}]
    return []


def techstack_text_problems(path: str, text: str, stack: dict) -> list[str]:
    """Return dependency/import violations for one path and supplied text."""
    problems: list[str] = []
    manifests = stack.get("manifests") or []
    packages = stack.get("packages") or {}

    if matches(path, manifests):
        for pattern in packages.get("deny") or []:
            if _regex(str(pattern), text):
                problems.append(f"{path} references forbidden package pattern {pattern!r}")

        allowed = {str(name).casefold() for name in packages.get("allow") or []}
        for extractor in stack_extractors(stack):
            if not matches(path, extractor.get("paths") or manifests):
                continue
            pattern = extractor.get("regex")
            if not isinstance(pattern, str) or not pattern:
                raise PolicyError(f"package extractor for {path} has no regex")
            for match in _regex(pattern, text):
                if not match.groups():
                    raise PolicyError(f"package extractor for {path} needs capture group 1")
                name = match.group(1)
                if allowed and name.casefold() not in allowed:
                    problems.append(
                        f"{path} references package {name!r} outside the techstack allowlist"
                    )

    for rule in stack.get("forbidden_imports") or []:
        if not matches(path, rule.get("paths") or ["**"]):
            continue
        for pattern in rule.get("patterns") or []:
            if _regex(str(pattern), text):
                reason = str(rule.get("reason") or "no reason recorded")
                problems.append(f"{path} matches forbidden import {pattern!r} ({reason})")
    return problems


def techstack_file_problems(root: Path, stack: dict, paths) -> list[str]:
    """Scan existing files from an explicit path collection."""
    problems: list[str] = []
    for path in sorted(set(paths)):
        file_path = root / path
        if not file_path.exists():
            continue  # a permitted delete has no resulting content to scan
        if not file_path.is_file():
            problems.append(f"{path} is not a regular file")
            continue
        try:
            text = file_path.read_text(errors="replace")
        except OSError as exc:
            problems.append(f"cannot scan {path}: {exc}")
            continue
        problems.extend(techstack_text_problems(path, text, stack))
    return problems


def techstack_tree_problems(root: Path, stack: dict) -> list[str]:
    """Authoritative full-tree scan used at gate and every transition."""
    patterns = list(stack.get("manifests") or [])
    for rule in stack.get("forbidden_imports") or []:
        patterns.extend(rule.get("paths") or ["**"])
    paths: list[str] = []
    for directory, dirs, files in os.walk(root):
        dirs[:] = [name for name in dirs if name not in IGNORED_DIRS]
        for name in files:
            path = (Path(directory) / name).relative_to(root).as_posix()
            if matches(path, patterns):
                paths.append(path)
    return techstack_file_problems(root, stack, paths)


def stack_problems(stack: dict, use_keys) -> list[str]:
    """Contract checks on one resolved stack.yaml section."""
    problems: list[str] = []
    commands = stack.get("commands")
    if not isinstance(commands, dict):
        problems.append("stack section has no commands mapping")
        commands = {}
    if stack.get("compiled") is True and not commands.get("build"):
        problems.append("compiled: true requires a commands.build entry")
    for key in sorted(set(use_keys or ())):
        entry = commands.get(key)
        if not isinstance(entry, dict):
            problems.append(f"stack.yaml defines no command key {key!r} as a mapping")
            continue
        argv = entry.get("argv")
        if not isinstance(argv, list) or not argv or not all(isinstance(a, str) for a in argv):
            problems.append(f"stack command {key!r} needs a non-empty argv array of strings")
        if key == "test" and not entry.get("junit_path"):
            problems.append("stack command 'test' needs junit_path so the oracle can read results")
        timeout = entry.get("timeout_s", 600)
        if not isinstance(timeout, int) or timeout <= 0:
            problems.append(f"stack command {key!r} timeout_s must be a positive integer")
    return problems
