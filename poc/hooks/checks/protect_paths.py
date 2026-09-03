"""PreToolUse: deny edits to protected paths, including Bash redirect targets.

Matching is fnmatch over the repo-relative path, resolved through symlinks with
realpath. This is not gitignore semantics. Writes made by arbitrary
subprocesses (a script inside Bash) are invisible here, as they are to Claude's
own Edit deny rules.
"""
from __future__ import annotations

from checks.base import Check, Decision, Event, glob_any, redirect_targets

WRITE_TOOLS = r"^(Edit|Write|MultiEdit|NotebookEdit)$"


class ProtectPaths(Check):
    name = "protect_paths"
    events = ("PreToolUse",)
    tool_matcher = r"^(Edit|Write|MultiEdit|NotebookEdit|Bash)$"
    order = 20
    critical = True

    def run(self, ev: Event) -> Decision:
        patterns = self.policy.get("protected_paths", [])
        targets: list[str] = []
        if ev.tool_name == "Bash":
            if ev.command:
                targets = redirect_targets(ev.command)
        elif ev.file_path:
            targets = [ev.file_path]
        for target in targets:
            rel = ev.rel_path(target)
            if rel is None:
                if self.policy.get("deny_outside_project", True):
                    return Decision.deny(f"write outside the project: {target}")
                continue
            hit = glob_any(rel, patterns)
            if hit:
                return Decision.deny(f"{rel} is protected (rule {hit})")
        return Decision.none()
