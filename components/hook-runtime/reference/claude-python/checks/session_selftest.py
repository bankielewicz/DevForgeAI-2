"""SessionStart: prove the hook chain is alive and tell Claude what is fenced.

If this context never appears in a session, hooks are not firing: a missing
policy hook must be a visible health failure, not a silent loss of enforcement.
"""
from __future__ import annotations

from checks.base import Check, Decision, Event


class SessionSelfTest(Check):
    name = "session_selftest"
    events = ("SessionStart",)
    order = 10

    def run(self, ev: Event) -> Decision:
        protected = self.policy.get("protected_paths", [])
        denied = self.policy.get("denied_commands", [])
        lines = [
            "hookd is active for this session.",
            f"Protected paths ({len(protected)}): " + ", ".join(protected[:8]) + (" ..." if len(protected) > 8 else ""),
            f"Denied command patterns ({len(denied)}).",
            "A denied write or command is reported with the reason; do not retry it in another form.",
        ]
        return Decision.with_context("\n".join(lines))
