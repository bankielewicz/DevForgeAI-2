"""Deny explicitly listed commands only when they occur at command position."""

from __future__ import annotations

import re

from protocol import ProtocolError, normalized_command_position, shell_segments

from .base import Check, CheckContext, Outcome


class CommandGuard(Check):
    name = "command_guard"
    order = 30
    events = frozenset({"PreToolUse"})
    tool_pattern = r"^Bash$"
    critical = True

    def evaluate(self, event, context: CheckContext) -> Outcome:
        try:
            segments = shell_segments(event.command)
        except ProtocolError as exc:
            return Outcome.violation("COMMAND_UNPARSEABLE", str(exc))
        for segment in segments:
            normalized = normalized_command_position(segment)
            if not normalized:
                return Outcome.violation(
                    "COMMAND_UNPARSEABLE", "shell command could not be parsed safely"
                )
            for rule in context.policy["denied_commands"]:
                if re.search(rule["pattern"], normalized):
                    return Outcome.violation(
                        "COMMAND_DENIED",
                        f"command is denied by policy rule {rule['id']}",
                        rule_id=rule["id"],
                    )
        return Outcome.pass_(segments=len(segments))
