"""Shipped registry. Order remains explicit and reviewable."""

from .audit_event import AuditEvent
from .command_guard import CommandGuard
from .protect_paths import ProtectPaths
from .session_selftest import SessionSelfTest
from .subagent_receipt import SubagentReceipt


BUILTIN_CHECKS = (
    SessionSelfTest,
    ProtectPaths,
    CommandGuard,
    SubagentReceipt,
    AuditEvent,
)
