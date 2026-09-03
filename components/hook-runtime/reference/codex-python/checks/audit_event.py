"""Request a sanitized event record; this is not a durable change ledger."""

from __future__ import annotations

from .base import Check, CheckContext, Outcome


class AuditEvent(Check):
    name = "audit_event"
    order = 90
    events = frozenset({"PostToolUse"})
    critical = False

    def evaluate(self, event, context: CheckContext) -> Outcome:
        return Outcome.pass_(
            tool_name=event.safe_identifier("tool_name", 80),
            tool_use_id=event.safe_identifier("tool_use_id", 128),
        )
