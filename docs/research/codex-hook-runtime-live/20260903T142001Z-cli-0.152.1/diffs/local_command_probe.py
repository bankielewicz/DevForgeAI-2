"""Disposable project-local command check for the live extensibility probe."""

from __future__ import annotations

from typing import Any, Mapping

from .base import Check, CheckContext, Outcome


class LocalCommandProbe(Check):
    name = "local_command_probe"
    order = 50
    events = frozenset({"PreToolUse"})
    tool_pattern = r"^Bash$"
    critical = True

    def validate_config(self, config: Mapping[str, Any]) -> None:
        if set(config) != {"command"} or not isinstance(config.get("command"), str):
            raise ValueError("local_command_probe config requires only string command")
        if not config["command"]:
            raise ValueError("local_command_probe command must not be empty")

    def evaluate(self, event, context: CheckContext) -> Outcome:
        if event.command == context.config_for(self.name)["command"]:
            return Outcome.violation(
                "LOCAL_CHECK_TRIGGERED",
                "project-local extension denied the configured command",
                rule_id="LOCAL_COMMAND_PROBE",
            )
        return Outcome.pass_()
