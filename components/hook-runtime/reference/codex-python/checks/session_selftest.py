"""Expose bounded startup context proving which dispatcher and policy loaded."""

from __future__ import annotations

from .base import Check, CheckContext, Outcome


class SessionSelfTest(Check):
    name = "session_selftest"
    order = 10
    events = frozenset({"SessionStart"})
    critical = False

    def evaluate(self, event, context: CheckContext) -> Outcome:
        mode = context.policy["mode"]
        root_name = context.project_root.name
        text = (
            "DevForgeAI Codex hookd POC is active; "
            f"mode={mode}; policy_sha256={context.policy_sha256}; "
            f"project={root_name}. Hooks are guardrails; transition and promotion "
            "validation remain authoritative."
        )
        return Outcome.context_(text, mode=mode)
