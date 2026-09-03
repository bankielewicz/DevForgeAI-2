"""Copy this file, rename the class, then register it in local_registry.py."""

from __future__ import annotations

from typing import Any, Mapping

from .base import Check, CheckContext, Outcome


class ExampleCheck(Check):
    name = "example_check"
    order = 500
    events = frozenset({"PreToolUse"})
    tool_pattern = r"^Bash$"
    critical = True

    def validate_config(self, config: Mapping[str, Any]) -> None:
        # Define a closed set and exact types for this check. Delete this method
        # when the check accepts no configuration.
        if set(config) - {"enabled"} or not isinstance(config.get("enabled", True), bool):
            raise ValueError("example_check config accepts only boolean enabled")

    def evaluate(self, event, context: CheckContext) -> Outcome:
        # Return a semantic result. Do not print, mutate provider permissions, or
        # read unstable transcript formats from a check.
        config = context.config_for(self.name)
        if config.get("enabled", True) is False:
            return Outcome.pass_()
        return Outcome.pass_()
