"""PostToolUse: record which files were changed by which actor. Never blocks.

The dispatcher already logs every decision; this check exists to show the
non-blocking, context-free shape and to give the sequencer an actor-bound
change trail it can compare with a receipt later.
"""
from __future__ import annotations

from checks.base import Check, Decision, Event


class AuditLog(Check):
    name = "audit_log"
    events = ("PostToolUse",)
    tool_matcher = r"^(Edit|Write|MultiEdit|NotebookEdit)$"
    order = 40

    def run(self, ev: Event) -> Decision:
        # The dispatcher's log line carries tool, file, agent and session.
        # Returning none keeps PostToolUse silent in the transcript.
        return Decision.none()
