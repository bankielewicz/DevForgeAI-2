"""Base types for hookd checks.

A check is a small class that looks at one hook event and returns a Decision.
Checks never emit "allow": passing through means "no decision", so the host's
normal permission flow still runs. Only deny, ask and context are expressed.
"""
from __future__ import annotations

import fnmatch
import os
import re
from dataclasses import dataclass, field
from typing import Any, ClassVar, Iterable


class Event:
    """Typed accessors over the raw hook input JSON."""

    def __init__(self, raw: dict[str, Any], project_dir: str) -> None:
        self.raw = raw
        self.project_dir = os.path.realpath(project_dir)

    # ---- common fields -------------------------------------------------
    @property
    def name(self) -> str:
        return str(self.raw.get("hook_event_name", ""))

    @property
    def session_id(self) -> str:
        return str(self.raw.get("session_id", ""))

    @property
    def cwd(self) -> str:
        return str(self.raw.get("cwd", self.project_dir))

    @property
    def agent_id(self) -> str | None:
        v = self.raw.get("agent_id")
        return str(v) if v else None

    @property
    def agent_type(self) -> str | None:
        v = self.raw.get("agent_type")
        return str(v) if v else None

    # ---- tool events -----------------------------------------------------
    @property
    def tool_name(self) -> str:
        return str(self.raw.get("tool_name", ""))

    @property
    def tool_input(self) -> dict[str, Any]:
        v = self.raw.get("tool_input")
        return v if isinstance(v, dict) else {}

    @property
    def file_path(self) -> str | None:
        for key in ("file_path", "notebook_path", "path"):
            v = self.tool_input.get(key)
            if isinstance(v, str) and v:
                return v
        return None

    @property
    def command(self) -> str | None:
        v = self.tool_input.get("command")
        return v if isinstance(v, str) else None

    # ---- stop events ---------------------------------------------------
    @property
    def last_assistant_message(self) -> str:
        return str(self.raw.get("last_assistant_message", "") or "")

    # ---- path helpers --------------------------------------------------
    def rel_path(self, path: str) -> str | None:
        """Repo-relative POSIX path if `path` resolves under the project dir, else None.

        Resolves symlinks with realpath. A path outside the project returns None so
        a check can decide what to do with it (the protect-paths check denies).
        """
        abs_path = path if os.path.isabs(path) else os.path.join(self.cwd, path)
        # realpath of the nearest existing ancestor, so new files resolve too
        probe = abs_path
        while not os.path.exists(probe):
            parent = os.path.dirname(probe)
            if parent == probe:
                break
            probe = parent
        real = os.path.realpath(probe) + abs_path[len(probe):]
        try:
            rel = os.path.relpath(real, self.project_dir)
        except ValueError:
            return None
        if rel.startswith(".."):
            return None
        return rel.replace(os.sep, "/")


@dataclass
class Decision:
    """What a check concluded. `kind` is one of none | deny | ask | context."""

    kind: str = "none"
    reason: str = ""
    context: str = ""
    check: str = ""

    @staticmethod
    def none() -> "Decision":
        return Decision()

    @staticmethod
    def deny(reason: str) -> "Decision":
        return Decision(kind="deny", reason=reason)

    @staticmethod
    def ask(reason: str) -> "Decision":
        return Decision(kind="ask", reason=reason)

    @staticmethod
    def with_context(text: str) -> "Decision":
        return Decision(kind="context", context=text)


class Check:
    """Subclass this. Set the class attributes, implement run()."""

    name: ClassVar[str] = "unnamed"
    events: ClassVar[tuple[str, ...]] = ()
    tool_matcher: ClassVar[str | None] = None   # regex over tool_name, None = any
    order: ClassVar[int] = 100                  # lower runs first
    critical: ClassVar[bool] = False            # True: an exception becomes deny

    def __init__(self, policy: dict[str, Any]) -> None:
        self.policy = policy

    def applies(self, ev: Event) -> bool:
        if ev.name not in self.events:
            return False
        if self.tool_matcher and not re.search(self.tool_matcher, ev.tool_name):
            return False
        return True

    def run(self, ev: Event) -> Decision:  # pragma: no cover - abstract
        raise NotImplementedError


def glob_any(rel: str, patterns: Iterable[str]) -> str | None:
    """First fnmatch pattern that matches `rel`, or None. fnmatch, not gitignore."""
    for pat in patterns:
        if fnmatch.fnmatch(rel, pat):
            return pat
    return None


# Redirect targets in a Bash command are file writes. Cheap, conservative parse.
_REDIRECT = re.compile(r"(?<![<>])(?:>>|>|\d>>|\d>)\s*([^\s;&|]+)")


def redirect_targets(command: str) -> list[str]:
    return [t for t in _REDIRECT.findall(command) if t not in ("/dev/null", "&1", "&2")]
