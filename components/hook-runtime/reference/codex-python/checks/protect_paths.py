"""Fast feedback for directly observable patch and shell-redirection paths."""

from __future__ import annotations

from pathlib import Path

from protocol import (
    ProtocolError,
    parse_apply_patch_paths,
    path_matches,
    redirect_targets,
    resolve_project_path,
)

from .base import Check, CheckContext, Outcome


class ProtectPaths(Check):
    name = "protect_paths"
    order = 20
    events = frozenset({"PreToolUse"})
    tool_pattern = r"^(?:apply_patch|Bash)$"
    critical = True

    def evaluate(self, event, context: CheckContext) -> Outcome:
        protected = context.policy["protected_paths"]
        if event.tool_name == "apply_patch":
            try:
                paths = parse_apply_patch_paths(event.command)
            except ProtocolError as exc:
                return Outcome.violation("PATCH_UNPARSEABLE", str(exc))
            source = "apply_patch"
        else:
            try:
                paths = redirect_targets(event.command)
            except ProtocolError as exc:
                return Outcome.violation("COMMAND_UNPARSEABLE", str(exc))
            source = "shell_redirect"

        checked: list[str] = []
        for raw_path in paths:
            if source == "shell_redirect" and Path(raw_path).is_absolute():
                if raw_path in context.policy["allowed_external_redirects"]:
                    continue
            try:
                _, relative = resolve_project_path(context.project_root, raw_path)
            except (ProtocolError, OSError) as exc:
                if context.policy["deny_outside_project"]:
                    return Outcome.violation("PATH_ESCAPE", str(exc), source=source)
                continue
            checked.append(relative)
            matched = path_matches(relative, protected)
            if matched:
                return Outcome.violation(
                    "PROTECTED_PATH",
                    f"{relative} is protected by policy rule {matched}",
                    source=source,
                    path=relative,
                )
        return Outcome.pass_(source=source, paths_checked=len(checked))
