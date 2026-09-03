"""PreToolUse on Bash: deny commands matching the policy's regex list, and ask
for the ones in `ask_commands`. Regexes are unanchored; keep them specific.
"""
from __future__ import annotations

import re

from checks.base import Check, Decision, Event


class BashGuard(Check):
    name = "bash_guard"
    events = ("PreToolUse",)
    tool_matcher = r"^Bash$"
    order = 30
    critical = True

    def run(self, ev: Event) -> Decision:
        cmd = ev.command or ""
        for pat in self.policy.get("denied_commands", []):
            if re.search(pat, cmd):
                return Decision.deny(f"command matches denied pattern {pat!r}")
        for pat in self.policy.get("ask_commands", []):
            if re.search(pat, cmd):
                return Decision.ask(f"command matches ask pattern {pat!r}")
        return Decision.none()
