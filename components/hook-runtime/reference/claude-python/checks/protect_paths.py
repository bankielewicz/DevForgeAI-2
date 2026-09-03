"""PreToolUse: deny edits to protected paths, including Bash redirect targets.

Matching is fnmatch over the repo-relative path, resolved through symlinks with
realpath. This is not gitignore semantics. Writes made by arbitrary
subprocesses (a script inside Bash) are invisible here, as they are to Claude's
own Edit deny rules.

`deny_outside_project` refuses any write that does not resolve under the
project, except a target matching a pattern in `allowed_outside_project`:
absolute-path fnmatch globs, `~` expanded to the user's home. The default policy
lists Claude Code's per-project auto-memory directory so the fence does not also
switch off memory. Nothing here emits "allow": an allowed outside write passes
through to the host's own permission flow.
"""
from __future__ import annotations

import os

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
                if not self.policy.get("deny_outside_project", True):
                    continue
                if self._allowed_outside(ev.real_path(target)):
                    continue
                return Decision.deny(f"write outside the project: {target}")
            hit = glob_any(rel, patterns)
            if hit:
                return Decision.deny(f"{rel} is protected (rule {hit})")
        return Decision.none()

    def _allowed_outside(self, real: str) -> bool:
        patterns = [os.path.expanduser(p) for p in self.policy.get("allowed_outside_project", [])]
        return glob_any(real, patterns) is not None
