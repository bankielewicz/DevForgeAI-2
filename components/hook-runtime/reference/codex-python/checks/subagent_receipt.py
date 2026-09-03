"""Validate a bounded worker result envelope and store its exact bytes."""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

from .base import Check, CheckContext, Outcome


_REQUIRED = frozenset(
    {
        "schema",
        "run",
        "skill",
        "phase",
        "agent",
        "status",
        "candidate",
        "claimed_paths",
    }
)
_OPTIONAL = frozenset({"reason_code", "evidence_refs", "note", "issues", "next"})
_CANDIDATE_KEYS = frozenset({"id", "input_checkpoint"})


class DuplicateReceiptKey(ValueError):
    pass


def _object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise DuplicateReceiptKey(key)
        value[key] = item
    return value


def _reject_nonfinite(value: str) -> None:
    raise DuplicateReceiptKey(value)


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_list(value: Any) -> bool:
    return isinstance(value, list) and all(_nonempty_string(item) for item in value)


def _path_list(value: Any, maximum: int) -> bool:
    if not _string_list(value) or len(value) > maximum or len(value) != len(set(value)):
        return False
    for item in value:
        if (
            len(item) > 1024
            or item.startswith("/")
            or "\\" in item
            or any(ord(character) < 32 for character in item)
        ):
            return False
        if any(part == ".." for part in item.split("/")):
            return False
    return True


def _issues(value: Any) -> bool:
    if not isinstance(value, list) or len(value) > 10:
        return False
    for issue in value:
        if isinstance(issue, str):
            if not 1 <= len(issue) <= 300:
                return False
            continue
        if not isinstance(issue, dict) or not {"text"} <= set(issue) <= {"id", "kind", "text"}:
            return False
        if not isinstance(issue["text"], str) or not 1 <= len(issue["text"]) <= 300:
            return False
        if "id" in issue and (not isinstance(issue["id"], str) or not 1 <= len(issue["id"]) <= 120):
            return False
        if "kind" in issue and (
            not isinstance(issue["kind"], str)
            or not re.fullmatch(r"[a-z][a-z0-9_]*", issue["kind"])
        ):
            return False
    return True


class SubagentReceipt(Check):
    name = "subagent_receipt"
    order = 40
    events = frozenset({"SubagentStop"})
    critical = True

    def _reject(self, event, code: str, message: str) -> Outcome:
        if event.stop_hook_active:
            return Outcome.stop(code, message)
        return Outcome.violation(code, message)

    def evaluate(self, event, context: CheckContext) -> Outcome:
        if event.agent_type not in context.policy["receipt_agents"]:
            return Outcome.pass_(receipt_required=False)

        raw = event.last_assistant_message
        encoded = raw.encode("utf-8")
        if len(encoded) > context.policy["max_receipt_bytes"]:
            return self._reject(
                event, "RECEIPT_TOO_LARGE", "worker receipt exceeds the policy byte limit"
            )
        if not raw.strip().startswith("{"):
            return self._reject(
                event,
                "RECEIPT_INVALID",
                "worker must return exactly one JSON object with no prose or Markdown fence",
            )
        try:
            receipt = json.loads(
                raw,
                object_pairs_hook=_object_without_duplicates,
                parse_constant=_reject_nonfinite,
            )
        except (json.JSONDecodeError, UnicodeError, DuplicateReceiptKey):
            return self._reject(
                event,
                "RECEIPT_INVALID",
                "worker must return exactly one valid JSON object",
            )
        if not isinstance(receipt, dict):
            return self._reject(event, "RECEIPT_INVALID", "worker receipt must be an object")

        keys = frozenset(receipt)
        missing = sorted(_REQUIRED - keys)
        unknown = sorted(keys - _REQUIRED - _OPTIONAL)
        if missing or unknown:
            detail = []
            if missing:
                detail.append("missing=" + ",".join(missing))
            if unknown:
                detail.append("unknown=" + ",".join(unknown))
            return self._reject(event, "RECEIPT_INVALID", "; ".join(detail))
        if receipt["schema"] != context.policy["receipt_schema"]:
            return self._reject(event, "RECEIPT_INVALID", "receipt schema is unsupported")
        for key in ("run", "skill", "phase", "agent"):
            if not _nonempty_string(receipt[key]):
                return self._reject(event, "RECEIPT_INVALID", f"{key} must be non-empty")
        if len(receipt["run"]) > 200:
            return self._reject(event, "RECEIPT_INVALID", "run exceeds 200 characters")
        if not re.fullmatch(r"[a-z][a-z0-9-]*", receipt["skill"]):
            return self._reject(event, "RECEIPT_INVALID", "skill has an invalid format")
        if not re.fullmatch(r"[a-z][a-z0-9_]*", receipt["phase"]):
            return self._reject(event, "RECEIPT_INVALID", "phase has an invalid format")
        if not re.fullmatch(r"[a-z][a-z0-9_-]*", receipt["agent"]):
            return self._reject(event, "RECEIPT_INVALID", "agent has an invalid format")
        if receipt["agent"] != event.agent_type:
            return self._reject(
                event, "RECEIPT_IDENTITY_MISMATCH", "receipt agent does not match agent_type"
            )
        if receipt["status"] not in context.policy["receipt_statuses"]:
            return self._reject(event, "RECEIPT_INVALID", "receipt status is unsupported")
        reason_code = receipt.get("reason_code")
        if receipt["status"] == "could_not_run":
            if reason_code not in {"runner_missing", "timeout", "network", "hook_fault"}:
                return self._reject(
                    event, "RECEIPT_INVALID", "could_not_run requires a supported reason_code"
                )
        elif "reason_code" in receipt:
            return self._reject(
                event, "RECEIPT_INVALID", "reason_code is legal only with could_not_run"
            )
        candidate = receipt["candidate"]
        if not isinstance(candidate, dict) or frozenset(candidate) != _CANDIDATE_KEYS:
            return self._reject(
                event, "RECEIPT_INVALID", "candidate requires exactly id and input_checkpoint"
            )
        if not all(_nonempty_string(candidate[key]) for key in _CANDIDATE_KEYS):
            return self._reject(
                event, "RECEIPT_INVALID", "candidate values must be non-empty strings"
            )
        if any(len(candidate[key]) > 200 for key in _CANDIDATE_KEYS):
            return self._reject(event, "RECEIPT_INVALID", "candidate value exceeds 200 characters")
        if not _path_list(receipt["claimed_paths"], 64):
            return self._reject(
                event, "RECEIPT_INVALID", "claimed_paths must be a string array"
            )
        if receipt["status"] != "pass" and receipt["claimed_paths"]:
            return self._reject(
                event, "RECEIPT_INVALID", "claimed_paths must be empty on a non-pass status"
            )
        if "evidence_refs" in receipt and not _path_list(receipt["evidence_refs"], 16):
            return self._reject(
                event, "RECEIPT_INVALID", "evidence_refs must be a valid path array"
            )
        if "issues" in receipt and not _issues(receipt["issues"]):
            return self._reject(event, "RECEIPT_INVALID", "issues has an invalid shape")
        for optional_string in ("note", "next"):
            if optional_string in receipt and not isinstance(receipt[optional_string], str):
                return self._reject(
                    event, "RECEIPT_INVALID", f"{optional_string} must be a string"
                )
        if "note" in receipt and len(receipt["note"]) > 16384:
            return self._reject(event, "RECEIPT_INVALID", "note exceeds 16384 characters")
        if "next" in receipt:
            if receipt["status"] != "fail":
                return self._reject(event, "RECEIPT_INVALID", "next is legal only with fail")
            if not re.fullmatch(r"[a-z][a-z0-9_]*", receipt["next"]):
                return self._reject(event, "RECEIPT_INVALID", "next has an invalid format")

        try:
            receipt_path = self._store_exact(event, context, encoded)
        except OSError:
            return self._reject(
                event, "RECEIPT_STORE_FAILED", "validated receipt could not be stored"
            )
        return Outcome.pass_(
            receipt_required=True,
            receipt_file=receipt_path.name,
            receipt_sha256=hashlib.sha256(encoded).hexdigest(),
        )

    @staticmethod
    def _store_exact(event, context: CheckContext, payload: bytes) -> Path:
        receipts = context.runtime_dir / "receipts"
        if receipts.is_symlink():
            raise OSError("receipt directory must not be a symlink")
        receipts.mkdir(mode=0o700, exist_ok=True)
        identity = "\x00".join(
            (
                event.safe_identifier("session_id"),
                event.safe_identifier("turn_id"),
                event.agent_id,
                hashlib.sha256(payload).hexdigest(),
            )
        ).encode("utf-8")
        basename = hashlib.sha256(identity).hexdigest()
        destination = receipts / (basename + ".json")
        temporary = receipts / (f".{basename}.{os.getpid()}.tmp")
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            descriptor = os.open(temporary, flags, 0o600)
        except FileExistsError:
            temporary.unlink(missing_ok=True)
            descriptor = os.open(temporary, flags, 0o600)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            try:
                os.link(temporary, destination)
            except FileExistsError:
                if destination.is_symlink() or destination.read_bytes() != payload:
                    raise OSError("receipt collision")
        finally:
            temporary.unlink(missing_ok=True)
        return destination
