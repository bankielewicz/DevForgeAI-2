"""Explicit check registry. Adding a check is: add a module, add one line here.

Discovery is deliberately not automatic: hook scripts are executable
supply-chain artifacts, and an explicit list is the auditable form.
"""
from checks.session_selftest import SessionSelfTest
from checks.protect_paths import ProtectPaths
from checks.bash_guard import BashGuard
from checks.audit_log import AuditLog
from checks.subagent_receipt import SubagentReceipt

REGISTRY = [
    SessionSelfTest,
    ProtectPaths,
    BashGuard,
    AuditLog,
    SubagentReceipt,
]
