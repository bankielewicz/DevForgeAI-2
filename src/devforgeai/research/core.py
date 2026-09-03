"""Deterministic filesystem authority for provider-neutral Research runs."""

from __future__ import annotations

import contextlib
import errno
import hashlib
import hmac
import json
import os
import re
import stat
import sys
import sysconfig
import tempfile
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Final
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator, FormatChecker

from devforgeai import __version__ as PACKAGE_VERSION

try:
    import fcntl
except ImportError:  # pragma: no cover - exercised only on unsupported hosts
    fcntl = None  # type: ignore[assignment]

from . import cas as cas_ops
from .rendering import render_handoff_markdown
from .run_contracts import (
    VALIDATION_CHECK_IDS,
    validate_context_manifest_contract,
    validate_plan_contract,
    validate_preflight_contract,
    validate_provider_conformance_semantics,
    validate_reconciliation_contract,
    validate_success_state_contract,
)


FORMAT_VERSION: Final[int] = 1
PHASES: Final[tuple[str, ...]] = tuple(f"P{i}" for i in range(10))
ZERO_HASH: Final[str] = "0" * 64
MAX_SAFE_INTEGER: Final[int] = 9_007_199_254_740_991
MAX_TRACKED_OBJECT: Final[int] = 10 * 1024 * 1024
MAX_TRACKED_DOSSIER: Final[int] = 100 * 1024 * 1024
MAX_UNLICENSED_EXCERPT_WORDS: Final[int] = 25
MAX_VERIFICATION_PACKET_BYTES: Final[int] = 65_536
MAX_VERIFICATION_PACKET_EVIDENCE: Final[int] = 16
PROFILE_LIMITS: Final[dict[str, dict[str, int]]] = {
    "quick": {
        "atomic_questions": 6,
        "research_lanes": 3,
        "concurrent_workers": 2,
        "discovery_queries": 30,
        "admitted_sources": 20,
        "external_tool_calls": 90,
        "aggregate_model_tokens": 120_000,
        "context_bytes": 65_536,
        "elapsed_minutes": 45,
        "retry_per_failed_lane": 1,
    },
    "standard": {
        "atomic_questions": 12,
        "research_lanes": 6,
        "concurrent_workers": 3,
        "discovery_queries": 60,
        "admitted_sources": 40,
        "external_tool_calls": 180,
        "aggregate_model_tokens": 250_000,
        "context_bytes": 131_072,
        "elapsed_minutes": 90,
        "retry_per_failed_lane": 1,
    },
    "deep": {
        "atomic_questions": 24,
        "research_lanes": 10,
        "concurrent_workers": 5,
        "discovery_queries": 150,
        "admitted_sources": 100,
        "external_tool_calls": 450,
        "aggregate_model_tokens": 750_000,
        "context_bytes": 262_144,
        "elapsed_minutes": 240,
        "retry_per_failed_lane": 2,
    },
}
ADMISSIBLE_SOURCE_CLASSES: Final[frozenset[str]] = frozenset(
    {"PRIMARY", "SECONDARY"}
)
SOURCE_POLICY_CLASSES: Final[frozenset[str]] = frozenset(
    {"PRIMARY", "SECONDARY", "SEARCH_SNIPPET"}
)
VERIFICATION_CHECKS: Final[tuple[str, ...]] = (
    "entailment",
    "scope_match",
    "citation_resolution",
    "source_admission",
    "custody_integrity",
    "freshness",
    "corroboration",
    "contradictions_considered",
)
SLUG_RE: Final[re.Pattern[str]] = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
RUN_RE: Final[re.Pattern[str]] = re.compile(r"^RUN-[0-9]{6}$")
HASH_RE: Final[re.Pattern[str]] = re.compile(r"^[a-f0-9]{64}$")
QAR_RE: Final[re.Pattern[str]] = re.compile(r"^QAR-[0-9]{6}$")
ALLOWLIST_ORIGIN_RE: Final[re.Pattern[str]] = re.compile(
    r"^https?://(?:[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?|\[[0-9a-f:]+\])(?::[0-9]{1,5})?$"
)
ID_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?:RSR|RUN|RQ|QRY|SRC|EVD|CLM|CTR|VPK|VER|SYN|DEC|HND|EVT)-[0-9]{6}$"
)

KIND_FILES: Final[dict[str, str]] = {
    "question": "questions.jsonl",
    "query": "queries.jsonl",
    "evidence": "evidence.jsonl",
    "claim": "claims.jsonl",
    "contradiction": "contradictions.jsonl",
    "verification": "verifications.jsonl",
    "synthesis": "synthesis.jsonl",
    "decision": "decisions.jsonl",
    "handoff": "handoff.json",
    "source": "sources.jsonl",
    "state-event": "state.jsonl",
}
SINGLETON_FILES: Final[dict[str, str]] = {
    "provider-conformance": "provider-conformance.json",
    "preflight": "preflight.json",
    "context-manifest": "context-manifest.json",
    "plan": "plan.json",
    "reconciliation": "reconciliation.json",
}
KIND_IDS: Final[dict[str, tuple[str, str]]] = {
    "question": ("question_id", "RQ"),
    "query": ("query_id", "QRY"),
    "evidence": ("evidence_id", "EVD"),
    "claim": ("claim_id", "CLM"),
    "contradiction": ("contradiction_id", "CTR"),
    "verification": ("verification_id", "VER"),
    "synthesis": ("synthesis_id", "SYN"),
    "decision": ("decision_id", "DEC"),
    "handoff": ("handoff_id", "HND"),
    "source": ("source_id", "SRC"),
    "state-event": ("event_id", "EVT"),
}
KIND_PHASES: Final[dict[str, set[str]]] = {
    "question": {"P2"},
    "query": {"P4"},
    "source": {"P5"},
    "evidence": {"P5"},
    "claim": {"P6"},
    "contradiction": {"P6"},
    "verification": {"P7"},
    "synthesis": {"P8"},
    "decision": {"P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8"},
    "handoff": {"P8"},
    "state-event": set(PHASES),
}
SINGLETON_PHASES: Final[dict[str, set[str]]] = {
    "provider-conformance": {"P0"},
    "preflight": {"P0"},
    "context-manifest": {"P2"},
    "plan": {"P3"},
    "reconciliation": {"P6"},
}


class ResearchError(ValueError):
    """Base class for stable, fail-closed Research Core errors."""


class DigestMismatchError(ResearchError):
    pass


class ConflictError(ResearchError):
    pass


class IntegrityError(ResearchError):
    pass


class TransitionError(ResearchError):
    pass


class SourceEligibilityError(ResearchError):
    pass


class SchemaValidationError(ResearchError):
    pass


@dataclass(frozen=True, slots=True)
class RunRef:
    slug: str
    run_id: str
    path: Path
    request_digest: str
    phase: str
    sealed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path.as_posix(),
            "phase": self.phase,
            "request_digest": self.request_digest,
            "run_id": self.run_id,
            "sealed": self.sealed,
            "slug": self.slug,
        }


@dataclass(frozen=True, slots=True)
class ValidationReport:
    valid: bool
    slug: str
    run_id: str
    phase: str | None
    sealed: bool
    path: Path | None
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    manifest_digest: str | None = None

    @property
    def ok(self) -> bool:
        return self.valid

    def __bool__(self) -> bool:
        return self.valid

    def to_dict(self) -> dict[str, Any]:
        return {
            "errors": list(self.errors),
            "manifest_digest": self.manifest_digest,
            "ok": self.valid,
            "path": None if self.path is None else self.path.as_posix(),
            "phase": self.phase,
            "run_id": self.run_id,
            "sealed": self.sealed,
            "slug": self.slug,
            "valid": self.valid,
            "warnings": list(self.warnings),
        }

    def render(self) -> str:
        return canonical_json(self.to_dict()).decode("utf-8") + "\n"


def _string(value: str) -> str:
    if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
        raise ResearchError("E_CANONICAL_JSON_SURROGATE: lone UTF-16 surrogate")
    return value


def _key_order(value: str) -> bytes:
    return value.encode("utf-16-be")


def _normalize(value: Any, location: str = "$") -> Any:
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int):
        if abs(value) > MAX_SAFE_INTEGER:
            raise ResearchError(f"E_CANONICAL_JSON_INTEGER: {location} exceeds I-JSON range")
        return value
    if isinstance(value, float):
        raise ResearchError(f"E_CANONICAL_JSON_FLOAT: {location} uses unsupported floating point")
    if isinstance(value, str):
        return _string(value)
    if isinstance(value, list):
        return [_normalize(item, f"{location}/{index}") for index, item in enumerate(value)]
    if isinstance(value, Mapping):
        output: dict[str, Any] = {}
        for key in sorted(value, key=lambda item: _key_order(item) if isinstance(item, str) else b""):
            if not isinstance(key, str):
                raise ResearchError(f"E_CANONICAL_JSON_KEY: {location} has a non-string key")
            checked = _string(key)
            if checked in output:
                raise ResearchError(f"E_CANONICAL_JSON_KEY: duplicate key {checked!r}")
            output[checked] = _normalize(value[key], f"{location}/{checked}")
        return output
    raise ResearchError(f"E_CANONICAL_JSON_TYPE: {location} has {type(value).__name__}")


def _encode(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False, allow_nan=False)
    if isinstance(value, list):
        return "[" + ",".join(_encode(item) for item in value) + "]"
    if isinstance(value, dict):
        keys = sorted(value, key=_key_order)
        return "{" + ",".join(_encode(key) + ":" + _encode(value[key]) for key in keys) + "}"
    raise AssertionError(type(value))


def canonical_json(value: Any) -> bytes:
    """RFC-8785-compatible bytes for the accepted I-JSON integer subset."""

    return _encode(_normalize(value)).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def derive_verification_outcome(checks: Mapping[str, Any]) -> str:
    """Derive the only permitted verification outcome from all eight checks."""

    if set(checks) != set(VERIFICATION_CHECKS):
        raise IntegrityError("E_VERIFICATION_CHECK_SET")
    statuses: list[str] = []
    for name in VERIFICATION_CHECKS:
        check = checks[name]
        if not isinstance(check, Mapping):
            raise IntegrityError(f"E_VERIFICATION_CHECK:{name}")
        status = check.get("status")
        if status not in {"PASS", "FAIL", "COULD_NOT_RUN", "INFRA_FAILURE"}:
            raise IntegrityError(f"E_VERIFICATION_CHECK_STATUS:{name}")
        statuses.append(status)
    for candidate in ("FAIL", "INFRA_FAILURE", "COULD_NOT_RUN"):
        if candidate in statuses:
            return candidate
    return "PASS"


def _offline_launch_receipt_projection(record: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "launched_at": record["launched_at"],
        "packet_ref": record["packet_ref"],
        "schema_version": "offline-verification-launch-receipt/v1",
        "session_binding": record["session_binding"],
        "verifier": record["verifier"],
    }


def _offline_result_projection(record: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "checks": record["checks"],
        "claim_binding": record["claim_binding"],
        "completed_at": record["completed_at"],
        "outcome": record["outcome"],
        "packet_ref": record["packet_ref"],
        "reference_sets": record["reference_sets"],
        "schema_version": "offline-verification-result/v1",
    }


def normalize_request(data: Any) -> tuple[dict[str, Any], str]:
    normalized = _normalize(data)
    if not isinstance(normalized, dict):
        raise ResearchError("E_REQUEST_TYPE: request must be a JSON object")
    slug = normalized.get("slug")
    if not isinstance(slug, str) or len(slug) > 96 or not SLUG_RE.fullmatch(slug):
        raise ResearchError("E_REQUEST_SLUG: slug must be lowercase kebab-case")
    return normalized, sha256_bytes(canonical_json(normalized))


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _parse_json(data: bytes, label: str) -> Any:
    try:
        return json.loads(
            data.decode("utf-8"),
            object_pairs_hook=lambda pairs: _unique_object(pairs, label),
            parse_constant=lambda token: (_ for _ in ()).throw(
                IntegrityError(f"E_JSON_NUMBER: {label}: {token}")
            ),
        )
    except ResearchError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise IntegrityError(f"E_JSON_PARSE: {label}: {exc}") from exc


def _unique_object(pairs: list[tuple[str, Any]], label: str) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in pairs:
        if key in output:
            raise IntegrityError(f"E_JSON_DUPLICATE_KEY: {label}: {key}")
        output[key] = value
    return output


def _fsync_dir(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _atomic(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise IntegrityError(f"E_PATH_SYMLINK: {path}")
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        _fsync_dir(path.parent)
    except BaseException:
        with contextlib.suppress(FileNotFoundError):
            temporary.unlink()
        raise


def _write_json(path: Path, value: Any) -> None:
    _atomic(path, canonical_json(value) + b"\n")


def _read_json(path: Path) -> Any:
    try:
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
            raise IntegrityError(f"E_FILE_TYPE: {path}")
        raw = path.read_bytes()
    except OSError as exc:
        raise IntegrityError(f"E_FILE_READ: {path}: {exc}") from exc
    value = _parse_json(raw, path.as_posix())
    if raw != canonical_json(value) + b"\n":
        raise IntegrityError(f"E_JSON_NONCANONICAL: {path}")
    return value


def _append_line(path: Path, value: Any) -> str:
    rendered = canonical_json(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(
        path,
        os.O_WRONLY
        | os.O_APPEND
        | os.O_CREAT
        | getattr(os, "O_NOFOLLOW", 0),
        0o644,
    )
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise IntegrityError(f"E_FILE_TYPE: {path}")
        data = memoryview(rendered + b"\n")
        while data:
            count = os.write(descriptor, data)
            if count <= 0:
                raise OSError("short JSONL append")
            data = data[count:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return sha256_bytes(rendered)


def _read_lines(path: Path) -> list[dict[str, Any]]:
    try:
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
            raise IntegrityError(f"E_FILE_TYPE: {path}")
        raw = path.read_bytes()
    except FileNotFoundError:
        raise IntegrityError(f"E_JSONL_MISSING: {path}") from None
    if raw and not raw.endswith(b"\n"):
        raise IntegrityError(f"E_JSONL_TRUNCATED: {path}")
    result: list[dict[str, Any]] = []
    for number, line in enumerate(raw.splitlines(keepends=True), 1):
        if line == b"\n":
            raise IntegrityError(f"E_JSONL_BLANK: {path}:{number}")
        value = _parse_json(line[:-1], f"{path}:{number}")
        if not isinstance(value, dict):
            raise IntegrityError(f"E_JSONL_TYPE: {path}:{number}")
        if line != canonical_json(value) + b"\n":
            raise IntegrityError(f"E_JSONL_NONCANONICAL: {path}:{number}")
        result.append(value)
    return result


def _file_hash(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    try:
        with path.open("rb") as stream:
            while block := stream.read(1024 * 1024):
                digest.update(block)
                size += len(block)
    except OSError as exc:
        raise IntegrityError(f"E_FILE_HASH: {path}: {exc}") from exc
    return digest.hexdigest(), size


class ResearchStore:
    def __init__(
        self,
        workspace: Path,
        schema_root: Path | None = None,
        *,
        allow_offline_test_harness: bool = False,
    ):
        if not sys.platform.startswith("linux") or fcntl is None:
            raise ResearchError(
                "E_PLATFORM_UNSUPPORTED: Research Core 0.1.0 requires Linux"
            )
        root = Path(workspace).expanduser()
        if not root.is_dir():
            raise ResearchError(f"E_WORKSPACE: not an existing directory: {root}")
        self.workspace = root.resolve()
        self.research_root = self.workspace / "docs" / "research"
        self.staging_root = self.workspace / ".devforgeai" / "research-staging"
        self.lock_root = self.workspace / ".devforgeai" / "research-locks"
        self.local_cas_root = self.workspace / ".devforgeai" / "research-cas" / "sha256"
        self.tracked_cas_root = self.research_root / "_cas" / "sha256"
        self._allow_offline_test_harness = allow_offline_test_harness
        candidates = [
            Path(schema_root).resolve() if schema_root is not None else None,
            self.workspace / "schemas" / "research" / "v1",
            Path(__file__).resolve().parents[3] / "schemas" / "research" / "v1",
            Path(sysconfig.get_path("data"))
            / "share"
            / "devforgeai"
            / "schemas"
            / "research"
            / "v1",
        ]
        self.schema_root = next(
            (candidate for candidate in candidates if candidate is not None and (candidate / "request.schema.json").is_file()),
            Path(schema_root).resolve() if schema_root is not None else candidates[1],
        )
        self._validators: dict[str, Draft202012Validator] = {}

    def normalize_request(self, data: Any) -> tuple[dict[str, Any], str]:
        normalized, digest = normalize_request(data)
        self._validate_schema("request", normalized)
        question_ids = [item["question_id"] for item in normalized["questions"]]
        if len(question_ids) != len(set(question_ids)):
            raise ConflictError("E_REQUEST_QUESTION_ID_DUPLICATE")
        if len(question_ids) > normalized["budget"]["limits"]["atomic_questions"]:
            raise ResearchError("E_BUDGET_ATOMIC_QUESTIONS")
        self._validate_budget_request(normalized)
        self._validate_network_request(normalized)
        request_file_bytes = len(canonical_json(normalized)) + 1
        if request_file_bytes > normalized["budget"]["limits"]["context_bytes"]:
            raise ResearchError("E_BUDGET_CONTEXT_REQUEST_BYTES")
        return normalized, digest

    @staticmethod
    def _validate_budget_request(request: dict[str, Any]) -> None:
        """Bind profile limits and every increase to the named decision authority."""

        budget = request["budget"]
        limits = budget["limits"]
        baseline = PROFILE_LIMITS[budget["profile"]]
        authority = request["authority"]["decision_authority_id"]
        overrides = budget["confirmed_overrides"]
        fields = [item["field"] for item in overrides]
        if len(fields) != len(set(fields)):
            raise ResearchError("E_BUDGET_OVERRIDE_DUPLICATE")
        by_field = {item["field"]: item for item in overrides}
        if not set(by_field).issubset(limits):
            raise ResearchError("E_BUDGET_OVERRIDE_FIELD")
        for field, value in limits.items():
            override = by_field.get(field)
            if value > PROFILE_LIMITS["deep"][field]:
                raise ResearchError(f"E_BUDGET_BEYOND_DEEP:{field}")
            if value > baseline[field]:
                if override is None:
                    raise ResearchError(f"E_BUDGET_OVERRIDE_MISSING:{field}")
                if (
                    override["value"] != value
                    or override["authority_id"] != authority
                ):
                    raise ResearchError(f"E_BUDGET_OVERRIDE_BINDING:{field}")
            elif override is not None:
                raise ResearchError(f"E_BUDGET_OVERRIDE_NOT_NEEDED:{field}")

        source_policy = request["source_policy"]
        required = set(source_policy["required_classes"])
        prohibited = set(source_policy["prohibited_classes"])
        if not required.issubset(ADMISSIBLE_SOURCE_CLASSES):
            raise ResearchError("E_SOURCE_POLICY_REQUIRED_CLASS")
        if not prohibited.issubset(SOURCE_POLICY_CLASSES):
            raise ResearchError("E_SOURCE_POLICY_PROHIBITED_CLASS")
        if required & prohibited:
            raise ResearchError("E_SOURCE_POLICY_CLASS_CONFLICT")

    def open_run(self, request: Any, confirmed_digest: str) -> RunRef:
        normalized, digest = self.normalize_request(request)
        if not isinstance(confirmed_digest, str) or not HASH_RE.fullmatch(confirmed_digest):
            raise DigestMismatchError("E_REQUEST_DIGEST_FORMAT: expected lowercase SHA-256")
        if not hmac.compare_digest(digest, confirmed_digest):
            raise DigestMismatchError(
                f"E_REQUEST_DIGEST_MISMATCH: confirmed {confirmed_digest}; normalized {digest}"
            )
        if normalized["authority"].get("work_order_sha256") is not None:
            raise ResearchError(
                "E_NOT_IMPLEMENTED_WORK_ORDER_AUTHORITY: this Core slice cannot "
                "receive and validate an accepted parent work-order artifact"
            )
        slug = normalized["slug"]
        self._assert_write_fence(
            normalized,
            [
                f".devforgeai/research-locks/{slug}.lock",
                f".devforgeai/research-staging/{slug}",
            ],
        )
        with self._lock(slug):
            self._ensure_request_ids_unused(slug, normalized)
            run_id = self._next_run_id(slug)
            self._validate_parent_run(slug, run_id, normalized)
            parent = self.staging_root / slug
            self._safe_directory(parent, create=True)
            target = parent / run_id
            temporary = Path(tempfile.mkdtemp(prefix=f".{run_id}.", dir=parent))
            try:
                _write_json(temporary / "request.json", normalized)
                method = (
                    "WORK_ORDER"
                    if normalized["authority"].get("work_order_sha256") is not None
                    else "INTERACTIVE"
                )
                _write_json(
                    temporary / "run.json",
                    {
                        "confirmation_binding": {
                            "confirmed_at": _utc_now(),
                            "confirming_authority": normalized["authority"][
                                "confirming_authority_id"
                            ],
                            "method": method,
                            "request_sha256": digest,
                            "work_order_sha256": normalized["authority"].get(
                                "work_order_sha256"
                            ),
                        },
                        "request_id": normalized["request_id"],
                        "run_id": run_id,
                        "schema_version": "research-run/v1",
                        "slug": slug,
                    },
                )
                for filename in sorted(set(KIND_FILES.values())):
                    if filename.endswith(".jsonl"):
                        _atomic(temporary / filename, b"")
                event = self._state_event(
                    run_id,
                    self._next_event_id(slug),
                    0,
                    None,
                    None,
                    "P0",
                    "Run opened from a confirmed request digest.",
                )
                _append_line(temporary / "state.jsonl", event)
                os.rename(temporary, target)
                _fsync_dir(parent)
            except BaseException:
                self._remove_tree(temporary)
                raise
            return RunRef(slug, run_id, target, digest, "P0", False)

    def append_record(self, slug: str, run_id: str, kind: str, record: Any) -> str:
        self._names(slug, run_id)
        if kind not in KIND_FILES and kind not in SINGLETON_FILES:
            raise ResearchError(
                "E_RECORD_KIND: expected one of "
                + ", ".join(sorted(set(KIND_FILES) | set(SINGLETON_FILES)))
            )
        if kind == "state-event":
            raise ResearchError(
                "E_STATE_EVENT_AUTHORITY: use transition-run; state events are core-owned"
            )
        normalized = _normalize(record)
        if not isinstance(normalized, dict):
            raise ResearchError("E_RECORD_TYPE: record must be an object")
        self._validate_schema(kind, normalized)
        if kind in SINGLETON_FILES:
            with self._lock(slug):
                path, sealed = self._locate(slug, run_id)
                phase = self._phase(path)
                if sealed or phase == "P9":
                    raise ConflictError("E_RUN_IMMUTABLE: sealed or terminal run")
                if phase not in SINGLETON_PHASES[kind]:
                    raise ConflictError(
                        f"E_RECORD_PHASE: {kind} requires "
                        f"{','.join(sorted(SINGLETON_PHASES[kind]))}; current {phase}"
                    )
                target = path / SINGLETON_FILES[kind]
                request, _ = self._request(path)
                self._assert_write_fence(
                    request,
                    [
                        target.relative_to(self.workspace).as_posix(),
                        f".devforgeai/research-locks/{slug}.lock",
                    ],
                )
                if target.exists() or target.is_symlink():
                    raise ConflictError(f"E_SINGLETON_EXISTS:{kind}")
                self._validate_singleton_context(path, kind, normalized)
                _write_json(target, normalized)
                return sha256_bytes(canonical_json(normalized))
        id_field, prefix = KIND_IDS[kind]
        record_id = normalized.get(id_field)
        if not isinstance(record_id, str) or not re.fullmatch(fr"{prefix}-[0-9]{{6}}", record_id):
            raise ResearchError(f"E_RECORD_ID: invalid {id_field}")
        if normalized.get("record_id") != record_id:
            raise ResearchError(f"E_RECORD_ID_MISMATCH: record_id must equal {id_field}")
        if normalized.get("run_id") != run_id:
            raise ResearchError("E_RECORD_RUN_MISMATCH")
        if kind == "source":
            custody = normalized["custody"]
            if custody["mode"] not in {"EXTRACT_ONLY", "NONE"}:
                raise ResearchError(
                    "E_SOURCE_AUTHORITY: use put-source for retained bytes"
                )
            if "object_path" in custody:
                raise ResearchError("E_SOURCE_METADATA_OBJECT_PATH")
            self._retention_policy(normalized["retention_policy"])
        with self._lock(slug):
            path, sealed = self._locate(slug, run_id)
            phase = self._phase(path)
            if sealed or phase == "P9":
                raise ConflictError("E_RUN_IMMUTABLE: sealed or terminal run")
            if phase not in KIND_PHASES[kind]:
                raise ConflictError(
                    f"E_RECORD_PHASE: {kind} requires {','.join(sorted(KIND_PHASES[kind]))}; current {phase}"
                )
            request, _ = self._request(path)
            self._assert_write_fence(
                request,
                [
                    (path / KIND_FILES[kind]).relative_to(self.workspace).as_posix(),
                    f".devforgeai/research-locks/{slug}.lock",
                ],
            )
            if kind == "handoff" and (path / KIND_FILES[kind]).exists():
                raise ConflictError("E_HANDOFF_SINGLETON")
            self._validate_record_context(path, kind, normalized)
            self._ensure_id_unused(slug, record_id)
            if kind == "handoff":
                target = path / KIND_FILES[kind]
                _write_json(target, normalized)
                return sha256_bytes(canonical_json(normalized))
            return _append_line(path / KIND_FILES[kind], normalized)

    def build_verification_packet(
        self, slug: str, run_id: str, claim_id: str
    ) -> dict[str, Any]:
        """Project and persist one canonical, bias-minimized P7 packet.

        This is a provider-neutral Core API, not an additional public CLI
        operation.  The returned byte length and digest cover the RFC 8785
        payload without the file's terminating LF.
        """

        self._names(slug, run_id)
        if not isinstance(claim_id, str) or not re.fullmatch(
            r"CLM-[0-9]{6}", claim_id
        ):
            raise ResearchError("E_CLAIM_ID: expected CLM-NNNNNN")
        with self._lock(slug):
            path, sealed = self._locate(slug, run_id)
            phase = self._phase(path)
            if sealed or phase == "P9":
                raise ConflictError("E_RUN_IMMUTABLE: sealed or terminal run")
            if phase != "P7":
                raise ConflictError(
                    f"E_VERIFICATION_PACKET_PHASE: packet requires P7; current {phase}"
                )
            return self._build_verification_packet_locked(path, slug, claim_id)

    def put_source(
        self,
        slug: str,
        run_id: str,
        source_id: str,
        path: Path,
        metadata: Any,
    ) -> dict[str, Any]:
        self._names(slug, run_id)
        if not re.fullmatch(r"SRC-[0-9]{6}", source_id):
            raise ResearchError("E_SOURCE_ID: expected SRC-NNNNNN")
        record = _normalize(metadata)
        if not isinstance(record, dict):
            raise ResearchError("E_SOURCE_METADATA: metadata must be an object")
        if record.get("source_id", source_id) != source_id:
            raise ResearchError("E_SOURCE_ID_MISMATCH: argument and metadata differ")
        record["source_id"] = source_id
        policy = self._retention_policy(record.get("retention_policy"))
        if not policy["retention_permitted"]:
            raise SourceEligibilityError(
                "E_RETENTION_PROHIBITED: use an EXTRACT_ONLY or NONE metadata-only record route"
            )
        requested = record.get("custody", {}).get("mode", "LOCAL_ONLY_CAS")
        if requested not in {"TRACKED_CAS", "LOCAL_ONLY_CAS"}:
            raise SourceEligibilityError("E_PUT_SOURCE_CUSTODY: bytes require tracked or local-only CAS")
        source = Path(path).expanduser()
        if not source.is_absolute():
            source = self.workspace / source
        try:
            source = source.resolve(strict=True)
            source.relative_to(self.workspace)
            source_stat = source.lstat()
        except (OSError, ValueError) as exc:
            raise ResearchError(f"E_SOURCE_FILE: {exc}") from exc
        if stat.S_ISLNK(source_stat.st_mode) or not stat.S_ISREG(source_stat.st_mode):
            raise ResearchError("E_SOURCE_FILE: expected a nonsymlink regular file")

        with self._lock(slug):
            run_path, sealed = self._locate(slug, run_id)
            phase = self._phase(run_path)
            if sealed or phase == "P9":
                raise ConflictError("E_RUN_IMMUTABLE: sealed or terminal run")
            if phase not in KIND_PHASES["source"]:
                raise ConflictError(f"E_RECORD_PHASE: source requires P5; current {phase}")
            provisional_digest, provisional_size = _file_hash(source)
            tracked, reasons = self._tracked_eligible(
                policy, provisional_size, provisional_digest, slug
            )
            selected = "TRACKED_CAS" if requested == "TRACKED_CAS" and tracked else "LOCAL_ONLY_CAS"
            root = self.tracked_cas_root if selected == "TRACKED_CAS" else self.local_cas_root
            relative = (root / provisional_digest[:2] / provisional_digest).relative_to(
                self.workspace
            ).as_posix()
            record["retention_policy"] = policy
            record["custody"] = {
                "byte_length": provisional_size,
                "mode": selected,
                "object_path": relative,
                "sha256": provisional_digest,
            }
            if selected != requested:
                record["custody"]["retention_reason"] = "tracked eligibility failed: " + ", ".join(reasons)
            self._validate_schema("source", record)
            self._validate_record_context(run_path, "source", record)
            self._ensure_id_unused(slug, source_id)
            request, _ = self._request(run_path)
            self._assert_write_fence(
                request,
                [
                    relative,
                    (root.parent / "quarantine").relative_to(self.workspace).as_posix(),
                    (run_path / "sources.jsonl").relative_to(self.workspace).as_posix(),
                    f".devforgeai/research-locks/{slug}.lock",
                    ".devforgeai/research-locks/global.lock",
                ],
            )
            digest, actual_size, object_path = self._put_cas(
                source,
                root,
                cas_class=selected,
                slug=slug,
                run_id=run_id,
                proposed_source_id=source_id,
            )
            if digest != provisional_digest or actual_size != provisional_size:
                raise ConflictError("E_SOURCE_CHANGED_BETWEEN_VALIDATION_AND_CUSTODY")
            _append_line(run_path / "sources.jsonl", record)
            return record

    def _transition_contract_errors(
        self, path: Path, *, current: str, to_phase: str
    ) -> list[str]:
        """Return exact singleton-gate failures for a legal phase edge."""

        checks: list[str] = []
        if (current, to_phase) == ("P0", "P1"):
            checks.extend(
                validate_preflight_contract(
                    self.workspace,
                    path,
                    expected_run_id=path.name,
                    as_of_utc=_utc_now(),
                )
            )
            preflight = self._singleton(path, "preflight", required=True)
            if preflight is not None and preflight["gate"]["status"] != "PASS":
                checks.append("E_PREFLIGHT_GATE_NOT_PASS")
        elif (current, to_phase) == ("P2", "P3"):
            checks.extend(
                validate_context_manifest_contract(
                    self.workspace, path, expected_run_id=path.name
                )
            )
            manifest = self._singleton(
                path, "context-manifest", required=True
            )
            if manifest is not None and manifest["gate_status"] != "PASS":
                checks.append("E_CONTEXT_GATE_NOT_PASS")
        elif (current, to_phase) == ("P3", "P4"):
            checks.extend(
                validate_plan_contract(
                    self.workspace, path, expected_run_id=path.name
                )
            )
            plan = self._singleton(path, "plan", required=True)
            if plan is not None and plan["plan_status"] != "READY":
                checks.append("E_PLAN_NOT_READY")
        elif (current, to_phase) == ("P4", "P5"):
            report = self._validate_path(
                path, closing=False, final=False, check_validation=False
            )
            checks.extend(report.errors)
        elif (current, to_phase) == ("P5", "P6"):
            report = self._validate_path(
                path, closing=False, final=False, check_validation=False
            )
            checks.extend(report.errors)
            records = self._all_records(path)
            checks.extend(self._query_candidate_closure_errors(records))
            for source in records["source"]:
                if source["admission"] == "PENDING":
                    checks.append(
                        f"E_SOURCE_ADMISSION_PENDING:{source['source_id']}"
                    )
        elif (current, to_phase) == ("P6", "P7"):
            checks.extend(
                validate_reconciliation_contract(
                    self.workspace, path, expected_run_id=path.name
                )
            )
            reconciliation = self._singleton(
                path, "reconciliation", required=True
            )
            if reconciliation is not None and reconciliation["status"] != "PASS":
                checks.append("E_RECONCILIATION_NOT_PASS")
        elif (current, to_phase) == ("P7", "P8"):
            report = self._validate_path(
                path, closing=False, final=False, check_validation=False
            )
            checks.extend(report.errors)
            records = self._all_records(path)
            for claim in records["claim"]:
                if claim["status"] != "CANDIDATE":
                    continue
                linked = [
                    verification
                    for verification in records["verification"]
                    if verification["claim_id"] == claim["claim_id"]
                ]
                if not linked or linked[-1]["outcome"] != "PASS":
                    checks.append(f"E_G7_VERIFICATION:{claim['claim_id']}")
        return list(dict.fromkeys(checks))

    def transition(self, slug: str, run_id: str, to_phase: str, reason: str | None = None) -> RunRef:
        self._names(slug, run_id)
        if to_phase not in PHASES:
            raise TransitionError("E_PHASE: expected P0 through P9")
        with self._lock(slug):
            path, sealed = self._locate(slug, run_id)
            if sealed:
                raise TransitionError("E_RUN_IMMUTABLE: sealed run")
            events = self._state(path, run_id)
            current = events[-1]["to_phase"]
            if current == to_phase:
                return self._ref(path, False)
            legal = {
                "P0": {"P1"},
                "P1": {"P2"},
                "P2": {"P3"},
                "P3": {"P4"},
                "P4": {"P5"},
                "P5": {"P6"},
                "P6": {"P4", "P5", "P7"},
                "P7": {"P5", "P6", "P8"},
                "P8": {"P9"},
                "P9": set(),
            }
            if to_phase not in legal[current]:
                raise TransitionError(
                    f"E_ILLEGAL_TRANSITION: {current}->{to_phase}; expected one of "
                    + ",".join(sorted(legal[current]))
                )
            contract_errors = self._transition_contract_errors(
                path, current=current, to_phase=to_phase
            )
            if contract_errors:
                raise IntegrityError(
                    f"E_{current}_{to_phase}_GATE: "
                    + "; ".join(contract_errors)
                )
            if to_phase == "P9":
                report = self._validate_path(
                    path, closing=True, final=False, check_validation=False
                )
                if not report.valid:
                    raise IntegrityError("E_P9_GATE: " + "; ".join(report.errors))
            request, _ = self._request(path)
            self._assert_write_fence(
                request,
                [
                    (path / "state.jsonl").relative_to(self.workspace).as_posix(),
                    f".devforgeai/research-locks/{slug}.lock",
                ],
            )
            if (current, to_phase) == ("P6", "P7"):
                candidate_claim_ids = sorted(
                    item["claim_id"]
                    for item in self._records(path, "claim")
                    if item["status"] == "CANDIDATE"
                )
                for claim_id in candidate_claim_ids:
                    self._build_verification_packet_locked(path, slug, claim_id)
            why = reason or f"Completed {current}; entered {to_phase}."
            previous = sha256_bytes(canonical_json(events[-1]))
            event = self._state_event(
                run_id,
                self._next_event_id(slug),
                len(events),
                previous,
                current,
                to_phase,
                why,
            )
            self._validate_schema("state-event", event)
            _append_line(path / "state.jsonl", event)
            if to_phase == "P9":
                self._finalize_preseal(path)
            return self._ref(path, False)

    def validate_run(self, slug: str, run_id: str) -> ValidationReport:
        self._names(slug, run_id)
        with self._lock(slug):
            try:
                path, final = self._locate(slug, run_id)
            except ResearchError as exc:
                return ValidationReport(False, slug, run_id, None, False, None, (str(exc),))
            return self._validate_path(path, closing=self._phase(path) in {"P8", "P9"}, final=final)

    def _schema_set_digest(self) -> str:
        """Digest the exact versioned schema-set names and bytes."""

        digest = hashlib.sha256()
        for schema in sorted(self.schema_root.glob("*.schema.json")):
            if schema.is_symlink() or not schema.is_file():
                raise IntegrityError(f"E_SCHEMA_SET_FILE:{schema}")
            raw = schema.read_bytes()
            digest.update(schema.name.encode("utf-8"))
            digest.update(b"\0")
            digest.update(str(len(raw)).encode("ascii"))
            digest.update(b"\0")
            digest.update(raw)
        return digest.hexdigest()

    def _validation_subjects(self, path: Path) -> list[dict[str, Any]]:
        subjects: list[dict[str, Any]] = []
        for candidate in sorted(
            path.rglob("*"), key=lambda item: item.relative_to(path).as_posix()
        ):
            relative = candidate.relative_to(path).as_posix()
            if relative in {"validation.json", "MANIFEST.sha256"}:
                continue
            candidate_stat = candidate.lstat()
            if stat.S_ISLNK(candidate_stat.st_mode):
                raise IntegrityError(f"E_VALIDATION_SUBJECT_SYMLINK:{relative}")
            if stat.S_ISDIR(candidate_stat.st_mode):
                continue
            if not stat.S_ISREG(candidate_stat.st_mode):
                raise IntegrityError(f"E_VALIDATION_SUBJECT_TYPE:{relative}")
            digest, byte_length = self._hash_regular_file(candidate, path)
            subjects.append(
                {
                    "byte_length": byte_length,
                    "path": relative,
                    "sha256": digest,
                }
            )
        return subjects

    def _validation_record(
        self, path: Path, *, validated_at_utc: str | None = None
    ) -> dict[str, Any]:
        subjects = self._validation_subjects(path)
        subject_by_path = {item["path"]: item for item in subjects}
        records = self._all_records(path)

        def evidence(*paths: str) -> list[dict[str, str]]:
            return [
                {
                    "artifact_id": f"{path.name}/{relative}",
                    "path": relative,
                    "sha256": subject_by_path[relative]["sha256"],
                }
                for relative in paths
                if relative in subject_by_path
            ]

        check_specs: dict[str, tuple[bool, str, tuple[str, ...]]] = {
            "RUN_BINDING": (True, "Run identity and phase path bind to run.json.", ("run.json", "state.jsonl")),
            "REQUEST_BINDING": (True, "Confirmed request bytes, digest, and authority bind to run.json.", ("request.json", "run.json")),
            "PREFLIGHT": (True, "Provider attestation and all six required P0 capabilities passed exact binding and freshness checks.", ("provider-conformance.json", "preflight.json")),
            "STATE_CHAIN": (True, "The hash-linked state journal is the legal P0-P9 READY_TO_SEAL path.", ("state.jsonl",)),
            "CONTEXT_MANIFEST": (True, "Selected context paths, bytes, request coverage, and budget match the accepted manifest.", ("context-manifest.json",)),
            "PLAN": (True, "The plan binds request policy, lanes, envelopes, barriers, authority, and budget.", ("plan.json",)),
            "ID_UNIQUENESS": (True, "Every dossier-scoped record and packet ID is unique.", tuple(KIND_FILES.values())),
            "REFERENTIAL_INTEGRITY": (True, "All supported canonical record references resolve to current records.", tuple(KIND_FILES.values())),
            "CLAIM_DAG": (False, "Not applicable: the closable SOURCE_FACT slice implements no claim-derivation or supersession edges.", ()),
            "CLAIM_CLASS_CONTRACT": (True, "Every active closable Claim is a supported SOURCE_FACT with exact scope and evidence edges.", ("claims.jsonl", "evidence.jsonl")),
            "VERIFICATION_FRESHNESS": (True, "Every exposed Claim has the latest exact-packet PASS permitted by the offline verifier boundary.", ("claims.jsonl", "verifications.jsonl")),
            "RISK_CORROBORATION": (True, "The supported LOW-risk corroboration rule passed; MATERIAL and CRITICAL closure are rejected.", ("request.json", "claims.jsonl", "evidence.jsonl", "sources.jsonl")),
            "CONTRARY_COVERAGE": (True, "Every planned contrary lane has an EXECUTED CHALLENGE Query and reconciled RETURNED result.", ("plan.json", "queries.jsonl", "reconciliation.json")),
            "QUERY_CANDIDATE_ACCOUNTING": (True, "Every Query is plan-bound and each discovery candidate has its required Source-attempt cardinality.", ("queries.jsonl", "sources.jsonl")),
            "WORKER_ACCOUNTING": (True, "Every planned lane and envelope is reconciled with exact Query-only acceptance and usage accounting.", ("plan.json", "queries.jsonl", "reconciliation.json")),
            "RECONCILIATION": (True, "Reconciliation binds the exact plan, returned lanes, artifacts, Query IDs, and aggregate budget.", ("plan.json", "reconciliation.json")),
            "SOURCE_ADMISSION": (True, "Every supporting Source is retrieved, admitted, policy-permitted, and non-stale at the request boundary.", ("request.json", "sources.jsonl")),
            "EVIDENCE_EDGES": (True, "Every Evidence record binds admitted Source bytes and every active Claim binds supporting Evidence.", ("sources.jsonl", "evidence.jsonl", "claims.jsonl")),
            "DISPUTE_OWNERSHIP": (False, "Not applicable: successful closure contains no open material dispute.", ()),
            "STALE_EXCLUSION": (
                any(
                    item.get("readiness_status") == "STALE"
                    for items in records.values()
                    for item in items
                )
                or any(
                    item["freshness"]["status"] == "STALE"
                    for item in records["source"]
                ),
                "Stale records are excluded from the publishable Claim and synthesis sets.",
                ("sources.jsonl", "claims.jsonl", "synthesis.jsonl"),
            ),
            "DECISION_AUTHORITY": (
                bool(records["decision"]),
                "Every present Research-process Decision binds the confirmed decision authority.",
                ("request.json", "decisions.jsonl"),
            ),
            "CAS_INTEGRITY": (True, "Every retained Source custody reference resolved to exact CAS bytes during pre-seal validation.", ("sources.jsonl",)),
            "BUDGET": (True, "Canonical counts and reconciled usage remain within the confirmed profile and named overrides.", ("request.json", "context-manifest.json", "plan.json", "reconciliation.json", "handoff.json")),
            "DETERMINISTIC_RENDER": (True, "Every run-local Markdown view is byte-equal to a fresh Core render.", ("README.md", "synthesis.md", "handoff.md")),
            "HANDOFF_SHAPE": (True, "The handoff's Core-derived identities, counts, bindings, and READY_TO_SEAL invariants match canonical records.", ("handoff.json", "synthesis.jsonl")),
        }
        if set(check_specs) != VALIDATION_CHECK_IDS:
            raise IntegrityError("E_VALIDATION_CHECK_IMPLEMENTATION")
        checks = []
        for check_id in sorted(VALIDATION_CHECK_IDS):
            applicable, reason, paths = check_specs[check_id]
            if not applicable and check_id == "STALE_EXCLUSION":
                reason = "Not applicable: no canonical record is marked stale."
            elif not applicable and check_id == "DECISION_AUTHORITY":
                reason = "Not applicable: this run contains no Research-process Decision."
            checks.append(
                {
                    "applicable": applicable,
                    "check_id": check_id,
                    "evidence": evidence(*paths) if applicable else [],
                    "reason": reason,
                    "status": "PASS" if applicable else "NOT_APPLICABLE",
                }
            )
        record = {
            "checks": checks,
            "environment": {
                "core_version": f"devforgeai-research/{PACKAGE_VERSION}",
                "platform": sysconfig.get_platform(),
                "schema_set_sha256": self._schema_set_digest(),
            },
            "errors": [],
            "gate_status": "READY_TO_SEAL",
            "run_id": path.name,
            "schema_version": "research-validation/v1",
            "scope": "PRE_SEAL",
            "subject_files": subjects,
            "validated_at_utc": validated_at_utc or _utc_now(),
            "validation_id": f"{path.name}/validation",
            "warnings": [],
        }
        self._validate_schema("validation", record)
        return record

    def _finalize_preseal(self, path: Path) -> None:
        """Render, validate, and persist the Core-owned P9 validation record."""

        if self._phase(path) != "P9":
            raise TransitionError("E_PRESEAL_PHASE")
        views = self._render_views(path)
        for relative, content in views.items():
            target = path / relative
            self._safe_directory(target.parent, create=True)
            _atomic(target, content.encode("utf-8"))
        report = self._validate_path(
            path, closing=True, final=False, check_validation=False
        )
        if not report.valid:
            raise IntegrityError("E_PRESEAL_VALIDATION: " + "; ".join(report.errors))
        validation_path = path / "validation.json"
        if validation_path.exists() or validation_path.is_symlink():
            raise ConflictError("E_VALIDATION_SINGLETON")
        _write_json(validation_path, self._validation_record(path))
        errors = validate_success_state_contract(
            self.workspace, path, expected_run_id=path.name
        )
        if errors:
            raise IntegrityError("E_PRESEAL_STATE: " + "; ".join(errors))

    def seal_run(self, slug: str, run_id: str) -> Path:
        self._names(slug, run_id)
        with self._lock(slug):
            final_path = self._final(slug, run_id)
            if final_path.exists():
                if self._staging(slug, run_id).exists() or not final_path.is_dir():
                    raise ConflictError("E_SEAL_DESTINATION_EXISTS")
                # Publication can be interrupted after the immutable run has
                # moved out of staging.  Validate those exact run bytes without
                # presuming that the registry/root-view transaction finished,
                # then resume that transaction under the same slug lock.
                report = self._validate_path(
                    final_path,
                    closing=True,
                    final=True,
                    check_publication=False,
                )
                if not report.valid:
                    raise IntegrityError("E_FINAL_INVALID: " + "; ".join(report.errors))
                self._finish_publication(slug, run_id, final_path)
                verified = self._validate_path(final_path, closing=True, final=True)
                if not verified.valid:
                    raise IntegrityError(
                        "E_PUBLICATION_INTEGRITY: " + "; ".join(verified.errors)
                    )
                return final_path
            staging = self._staging(slug, run_id)
            if not staging.is_dir():
                raise ResearchError(f"E_RUN_NOT_FOUND: {slug}/{run_id}")
            if self._phase(staging) != "P9":
                raise TransitionError("E_SEAL_PHASE: run must reach P9 before seal")
            request, _ = self._request(staging)
            self._assert_write_fence(
                request,
                [
                    staging.relative_to(self.workspace).as_posix(),
                    self._final(slug, run_id).relative_to(self.workspace).as_posix(),
                    self._registry(slug).relative_to(self.workspace).as_posix(),
                    f"docs/research/{slug}/README.md",
                    f"docs/research/{slug}/synthesis.md",
                    f"docs/research/{slug}/handoff.md",
                    f".devforgeai/research-locks/{slug}.lock",
                ],
            )
            if not (staging / "validation.json").exists():
                # Recover only a transition interrupted before its Core-owned
                # validation write. Existing invalid validation is never healed.
                self._finalize_preseal(staging)
            report = self._validate_path(staging, closing=True, final=False)
            if not report.valid:
                raise IntegrityError("E_SEAL_VALIDATION: " + "; ".join(report.errors))
            manifest = self._manifest_bytes(staging)
            _atomic(staging / "MANIFEST.sha256", manifest)
            self._safe_directory(final_path.parent, create=True)
            os.rename(staging, final_path)
            _fsync_dir(final_path.parent)
            self._finish_publication(slug, run_id, final_path)
            verified = self._validate_path(final_path, closing=True, final=True)
            if not verified.valid:
                raise IntegrityError("E_PUBLICATION_INTEGRITY: " + "; ".join(verified.errors))
            return final_path

    def verify_run(self, slug: str, run_id: str) -> ValidationReport:
        self._names(slug, run_id)
        with self._lock(slug):
            final = self._final(slug, run_id)
            if not final.is_dir():
                return ValidationReport(False, slug, run_id, None, False, None, ("E_FINAL_NOT_FOUND",))
            return self._validate_path(final, closing=True, final=True)

    def seal_receipt(self, slug: str, run_id: str) -> dict[str, Any]:
        """Regenerate the noncanonical post-publication receipt for a sealed run."""

        self._names(slug, run_id)
        with self._lock(slug):
            return self._seal_receipt_locked(slug, run_id)

    def seal_result(self, slug: str, run_id: str) -> dict[str, Any]:
        """Seal and return the nonpersisted post-publication receipt."""

        self.seal_run(slug, run_id)
        with self._lock(slug):
            return self._seal_receipt_locked(slug, run_id)

    def _seal_receipt_locked(self, slug: str, run_id: str) -> dict[str, Any]:
        final = self._final(slug, run_id)
        if not final.is_dir():
            raise ResearchError(f"E_FINAL_NOT_FOUND: {slug}/{run_id}")
        report = self._validate_path(final, closing=True, final=True)
        if not report.valid or report.manifest_digest is None:
            raise IntegrityError(
                "E_SEAL_RECEIPT_READBACK: " + "; ".join(report.errors)
            )
        entries = self._registry_entries(slug)
        matches = [entry for entry in entries if entry["run_id"] == run_id]
        if len(matches) != 1:
            raise IntegrityError("E_SEAL_RECEIPT_REGISTRY")
        entry = matches[0]
        if not entries or entries[-1]["run_id"] != run_id:
            raise IntegrityError("E_SEAL_RECEIPT_NOT_CURRENT")
        handoff = _read_json(final / KIND_FILES["handoff"])
        if not isinstance(handoff, dict):
            raise IntegrityError("E_HANDOFF_TYPE")
        return {
            "handoff": handoff,
            "manifest_sha256": report.manifest_digest,
            "readback": {"outcome": "COMPLETE", "status": "PASS"},
            "registry": {
                "entry_sha256": entry["entry_sha256"],
                "path": self._registry(slug).relative_to(self.workspace).as_posix(),
                "sequence": entry["sequence"],
            },
            "run_id": run_id,
            "schema_version": "research-seal-receipt/v1",
            "sealed_run_path": final.relative_to(self.workspace).as_posix(),
        }

    def resume_run(self, slug: str, run_id: str) -> RunRef:
        self._names(slug, run_id)
        with self._lock(slug):
            path = self._staging(slug, run_id)
            if not path.is_dir():
                if self._final(slug, run_id).exists():
                    raise ConflictError("E_RESUME_SEALED: sealed runs cannot be resumed")
                raise ResearchError("E_RUN_NOT_FOUND")
            report = self._validate_path(path, closing=self._phase(path) in {"P8", "P9"}, final=False)
            if not report.valid:
                raise IntegrityError("E_RESUME_INVALID: " + "; ".join(report.errors))
            return self._ref(path, False)

    def render(self, slug: str, run_id: str) -> dict[str, str]:
        self._names(slug, run_id)
        with self._lock(slug):
            path, _ = self._locate(slug, run_id)
            return self._render_views(path)

    def render_handoff(self, slug: str, run_id: str) -> str:
        return self.render(slug, run_id)["handoff.md"]

    def _validate_schema(self, name: str, value: dict[str, Any]) -> None:
        validator = self._validators.get(name)
        if validator is None:
            schema_path = self.schema_root / f"{name}.schema.json"
            try:
                schema = json.loads(schema_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise SchemaValidationError(f"E_SCHEMA_UNAVAILABLE_{name.upper()}: {exc}") from exc
            Draft202012Validator.check_schema(schema)
            validator = Draft202012Validator(schema, format_checker=FormatChecker())
            self._validators[name] = validator
        errors = sorted(validator.iter_errors(value), key=lambda item: (list(item.absolute_path), item.message))
        if errors:
            issue = errors[0]
            pointer = "/" + "/".join(str(part) for part in issue.absolute_path)
            raise SchemaValidationError(f"E_SCHEMA_{name.upper()}: {pointer}: {issue.message}")

    @contextlib.contextmanager
    def _lock(self, slug: str) -> Iterator[None]:
        if slug != "global" and not SLUG_RE.fullmatch(slug):
            raise ResearchError("E_SLUG")
        self._safe_directory(self.lock_root, create=True)
        lock_path = self.lock_root / f"{slug}.lock"
        self._reject_symlink_components(lock_path)
        descriptor = os.open(
            lock_path,
            os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0),
            0o600,
        )
        acquired = False
        try:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
            except OSError as exc:
                if exc.errno in {errno.EACCES, errno.EAGAIN}:
                    raise ConflictError(f"E_WRITER_COLLISION: {slug}") from exc
                raise
            yield
        finally:
            if acquired:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)

    def _names(self, slug: str, run_id: str) -> None:
        if not isinstance(slug, str) or not SLUG_RE.fullmatch(slug):
            raise ResearchError("E_SLUG: expected lowercase kebab-case")
        if not isinstance(run_id, str) or not RUN_RE.fullmatch(run_id):
            raise ResearchError("E_RUN_ID: expected RUN-NNNNNN")

    def _staging(self, slug: str, run_id: str) -> Path:
        return self.staging_root / slug / run_id

    def _final(self, slug: str, run_id: str) -> Path:
        return self.research_root / slug / "runs" / run_id

    def _registry(self, slug: str) -> Path:
        return self.research_root / slug / "registry.jsonl"

    def _locate(self, slug: str, run_id: str) -> tuple[Path, bool]:
        staging, final = self._staging(slug, run_id), self._final(slug, run_id)
        self._reject_symlink_components(staging)
        self._reject_symlink_components(final)
        if staging.exists() and final.exists():
            raise IntegrityError("E_RUN_DUPLICATE_LOCATION")
        if final.is_dir():
            return final, True
        if staging.is_dir():
            return staging, False
        raise ResearchError(f"E_RUN_NOT_FOUND: {slug}/{run_id}")

    def _validate_parent_run(
        self, slug: str, new_run_id: str, request: Mapping[str, Any]
    ) -> None:
        """Require an optional parent to be a prior sealed, registered run in this dossier."""

        parent_run_id = request.get("parent_run_id")
        if parent_run_id is None:
            return
        if (
            parent_run_id == new_run_id
            or int(parent_run_id.removeprefix("RUN-"))
            >= int(new_run_id.removeprefix("RUN-"))
        ):
            raise IntegrityError("E_PARENT_RUN_NOT_PRIOR")
        parent = self._final(slug, parent_run_id)
        self._reject_symlink_components(parent)
        try:
            mode = parent.lstat().st_mode
        except OSError as exc:
            raise IntegrityError("E_PARENT_RUN_NOT_SEALED") from exc
        if not stat.S_ISDIR(mode):
            raise IntegrityError("E_PARENT_RUN_NOT_SEALED")
        manifest_digest = self._verify_manifest(parent)
        self._verify_registry(slug, parent_run_id, manifest_digest)
        parent_request, _ = self._request(parent)
        if parent_request["slug"] != slug:
            raise IntegrityError("E_PARENT_RUN_SLUG")

    def _next_run_id(self, slug: str) -> str:
        numbers: set[int] = set()
        for parent in (self.staging_root / slug, self.research_root / slug / "runs"):
            self._reject_symlink_components(parent)
            if parent.is_dir():
                for path in parent.iterdir():
                    if RUN_RE.fullmatch(path.name):
                        numbers.add(int(path.name[4:]))
        registry = self._registry(slug)
        if registry.exists():
            for entry in self._registry_entries(slug):
                numbers.add(int(entry["run_id"][4:]))
        number = max(numbers, default=0) + 1
        if number > 999_999:
            raise ConflictError("E_RUN_ID_EXHAUSTED")
        return f"RUN-{number:06d}"

    def _ensure_request_ids_unused(
        self, slug: str, request: dict[str, Any]
    ) -> None:
        requested_questions = {item["question_id"] for item in request["questions"]}
        for parent in (self.staging_root / slug, self.research_root / slug / "runs"):
            self._reject_symlink_components(parent)
            if not parent.is_dir():
                continue
            for run in parent.iterdir():
                request_path = run / "request.json"
                if not run.is_dir() or not request_path.is_file():
                    continue
                existing = _read_json(request_path)
                if not isinstance(existing, dict):
                    raise IntegrityError("E_REQUEST_TYPE")
                if existing.get("request_id") == request["request_id"]:
                    raise ConflictError(
                        f"E_REQUEST_ID_REUSE: {request['request_id']}"
                    )
                existing_questions = {
                    item.get("question_id")
                    for item in existing.get("questions", [])
                    if isinstance(item, dict)
                }
                reused = sorted(requested_questions & existing_questions)
                if reused:
                    raise ConflictError(
                        "E_REQUEST_QUESTION_ID_REUSE: " + ",".join(reused)
                    )

    def _dossier_event_ids(self, slug: str) -> list[str]:
        identifiers: list[str] = []
        for parent in (self.staging_root / slug, self.research_root / slug / "runs"):
            self._reject_symlink_components(parent)
            if not parent.is_dir():
                continue
            for run in sorted(parent.iterdir(), key=lambda item: item.name):
                state_path = run / "state.jsonl"
                if not run.is_dir() or not state_path.is_file():
                    continue
                for event in _read_lines(state_path):
                    identifier = event.get("event_id")
                    if not isinstance(identifier, str) or not re.fullmatch(
                        r"EVT-[0-9]{6}", identifier
                    ):
                        raise IntegrityError("E_EVENT_ID")
                    identifiers.append(identifier)
        return identifiers

    def _next_event_id(self, slug: str) -> str:
        identifiers = self._dossier_event_ids(slug)
        if len(identifiers) != len(set(identifiers)):
            raise IntegrityError("E_EVENT_ID_REUSE")
        number = max((int(item[4:]) for item in identifiers), default=0) + 1
        if number > 999_999:
            raise ConflictError("E_EVENT_ID_EXHAUSTED")
        return f"EVT-{number:06d}"

    def _request(self, path: Path) -> tuple[dict[str, Any], str]:
        request = _read_json(path / "request.json")
        if not isinstance(request, dict):
            raise IntegrityError("E_REQUEST_TYPE")
        self._validate_schema("request", request)
        normalized, digest = normalize_request(request)
        if normalized != request:
            raise IntegrityError("E_REQUEST_NONCANONICAL")
        run = _read_json(path / "run.json")
        if not isinstance(run, dict):
            raise IntegrityError("E_RUN_TYPE")
        self._validate_schema("run", run)
        expected_method = (
            "WORK_ORDER" if request["authority"].get("work_order_sha256") is not None else "INTERACTIVE"
        )
        expected_static = {
            "request_id": request["request_id"],
            "run_id": path.name,
            "schema_version": "research-run/v1",
            "slug": request["slug"],
        }
        if {key: run.get(key) for key in expected_static} != expected_static:
            raise IntegrityError("E_RUN_REQUEST_BINDING")
        binding = run.get("confirmation_binding")
        if not isinstance(binding, dict) or set(binding) != {
            "confirmed_at", "confirming_authority", "method", "request_sha256", "work_order_sha256"
        }:
            raise IntegrityError("E_RUN_CONFIRMATION_BINDING")
        if (
            binding["request_sha256"] != digest
            or binding["confirming_authority"] != request["authority"]["confirming_authority_id"]
            or binding["method"] != expected_method
            or binding["work_order_sha256"] != request["authority"].get("work_order_sha256")
            or not isinstance(binding["confirmed_at"], str)
        ):
            raise IntegrityError("E_RUN_CONFIRMATION_BINDING")
        return request, digest

    def _state_event(
        self,
        run_id: str,
        event_id: str,
        sequence: int,
        previous: str | None,
        from_phase: str | None,
        to_phase: str,
        reason: str,
    ) -> dict[str, Any]:
        now = _utc_now()
        if from_phase is None and to_phase == "P0":
            reason_code = "RUN_OPENED"
        elif to_phase == "P9":
            reason_code = "READY_TO_SEAL"
        elif (from_phase, to_phase) in {
            ("P6", "P4"),
            ("P6", "P5"),
            ("P7", "P5"),
            ("P7", "P6"),
        }:
            reason_code = "REPAIR_ROUTE"
        else:
            reason_code = "PHASE_ADVANCE"
        return {
            "actor_id": "core:research-store",
            "created_at_utc": now,
            "decision_authority": "core:research-store",
            "decision_refs": [],
            "event_type": "PHASE_TRANSITION",
            "event_id": event_id,
            "evidence_refs": [],
            "from_phase": from_phase,
            "lifecycle_status": "ACCEPTED",
            "occurred_at": now,
            "owner": "core:research-store",
            "previous_event_sha256": previous,
            "reason": reason,
            "readiness_status": "READY",
            "record_id": event_id,
            "record_version": 1,
            "reason_code": reason_code,
            "run_id": run_id,
            "schema_version": "research-state-event/v1",
            "sequence": sequence,
            "source_refs": [],
            "stale_if": [],
            "supersedes": [],
            "to_phase": to_phase,
        }

    def _state(self, path: Path, run_id: str) -> list[dict[str, Any]]:
        events = _read_lines(path / "state.jsonl")
        if not events:
            raise IntegrityError("E_STATE_EMPTY")
        previous: str | None = None
        phase: str | None = None
        for index, event in enumerate(events):
            self._validate_schema("state-event", event)
            legal = {
                "P0": {"P1"}, "P1": {"P2"}, "P2": {"P3"}, "P3": {"P4"},
                "P4": {"P5"}, "P5": {"P6"}, "P6": {"P4", "P5", "P7"},
                "P7": {"P5", "P6", "P8"}, "P8": {"P9"}, "P9": set(),
            }
            transition_ok = event["to_phase"] == "P0" if index == 0 else event["to_phase"] in legal[phase or "P0"]
            if index == 0:
                expected_reason_code = "RUN_OPENED"
            elif event["to_phase"] == "P9":
                expected_reason_code = "READY_TO_SEAL"
            elif (event["from_phase"], event["to_phase"]) in {
                ("P6", "P4"),
                ("P6", "P5"),
                ("P7", "P5"),
                ("P7", "P6"),
            }:
                expected_reason_code = "REPAIR_ROUTE"
            else:
                expected_reason_code = "PHASE_ADVANCE"
            if (
                event["run_id"] != run_id
                or event["sequence"] != index
                or event["previous_event_sha256"] != previous
                or event["from_phase"] != phase
                or event["event_type"] != "PHASE_TRANSITION"
                or event["reason_code"] != expected_reason_code
                or not transition_ok
            ):
                raise IntegrityError(f"E_STATE_CHAIN: event {index}")
            previous = sha256_bytes(canonical_json(event))
            phase = event["to_phase"]
        return events

    def _phase(self, path: Path) -> str:
        return self._state(path, path.name)[-1]["to_phase"]

    def _ref(self, path: Path, sealed: bool) -> RunRef:
        request, digest = self._request(path)
        return RunRef(request["slug"], path.name, path, digest, self._phase(path), sealed)

    def _records(self, path: Path, kind: str) -> list[dict[str, Any]]:
        target = path / KIND_FILES[kind]
        if kind == "handoff":
            if not target.exists():
                return []
            value = _read_json(target)
            if not isinstance(value, dict):
                raise IntegrityError("E_HANDOFF_TYPE")
            return [value]
        return _read_lines(target)

    def _all_records(self, path: Path) -> dict[str, list[dict[str, Any]]]:
        return {kind: self._records(path, kind) for kind in KIND_FILES if kind != "state-event"}

    def _singleton(
        self, path: Path, kind: str, *, required: bool = False
    ) -> dict[str, Any] | None:
        if kind not in SINGLETON_FILES:
            raise ResearchError(f"E_SINGLETON_KIND:{kind}")
        target = path / SINGLETON_FILES[kind]
        if not target.exists() and not target.is_symlink():
            if required:
                raise IntegrityError(f"E_SINGLETON_MISSING:{kind}")
            return None
        value = _read_json(target)
        if not isinstance(value, dict):
            raise IntegrityError(f"E_SINGLETON_TYPE:{kind}")
        self._validate_schema(kind, value)
        return value

    def _workspace_artifact(
        self, relative_value: Any, *, code: str
    ) -> Path:
        if not isinstance(relative_value, str) or not relative_value:
            raise IntegrityError(code)
        pure = PurePosixPath(relative_value)
        if (
            "\\" in relative_value
            or pure.is_absolute()
            or pure.as_posix() != relative_value
            or any(part in {"", ".", ".."} for part in pure.parts)
        ):
            raise IntegrityError(f"{code}:{relative_value}")
        target = self.workspace.joinpath(*pure.parts)
        self._reject_symlink_components(target)
        try:
            resolved = target.resolve(strict=True)
            resolved.relative_to(self.workspace)
            mode = target.lstat().st_mode
        except (OSError, ValueError) as exc:
            raise IntegrityError(f"{code}:{relative_value}") from exc
        if resolved != target or not stat.S_ISREG(mode):
            raise IntegrityError(f"{code}:{relative_value}")
        return target

    def _run_artifact(
        self, run_path: Path, relative_value: Any, *, code: str
    ) -> Path:
        if not isinstance(relative_value, str) or not relative_value:
            raise IntegrityError(code)
        pure = PurePosixPath(relative_value)
        if (
            "\\" in relative_value
            or pure.is_absolute()
            or pure.as_posix() != relative_value
            or any(part in {"", ".", ".."} for part in pure.parts)
        ):
            raise IntegrityError(f"{code}:{relative_value}")
        target = run_path.joinpath(*pure.parts)
        self._reject_symlink_components(target)
        try:
            resolved = target.resolve(strict=True)
            resolved.relative_to(run_path)
            mode = target.lstat().st_mode
        except (OSError, ValueError) as exc:
            raise IntegrityError(f"{code}:{relative_value}") from exc
        if resolved != target or not stat.S_ISREG(mode):
            raise IntegrityError(f"{code}:{relative_value}")
        return target

    def _validate_singleton_context(
        self, path: Path, kind: str, record: dict[str, Any]
    ) -> None:
        request, request_digest = self._request(path)
        run_id = path.name
        authority = request["authority"]
        if kind == "provider-conformance":
            subject = record["attestation_subject"]
            if (
                subject["provider_kind"] == "OFFLINE_TEST_HARNESS"
                and not self._allow_offline_test_harness
            ):
                raise IntegrityError("E_OFFLINE_TEST_HARNESS_DISABLED")
            semantic_errors = validate_provider_conformance_semantics(record)
            if semantic_errors:
                raise IntegrityError(semantic_errors[0])
            adapter = self._workspace_artifact(
                subject["adapter_path"], code="E_PROVIDER_ADAPTER_PATH"
            )
            adapter_digest, _ = _file_hash(adapter)
            if adapter_digest != subject["adapter_sha256"]:
                raise IntegrityError("E_PROVIDER_ADAPTER_DIGEST")
            for capability in record["capabilities"]:
                for evidence in capability["evidence"]:
                    artifact = self._workspace_artifact(
                        evidence["path"], code="E_PROVIDER_EVIDENCE_PATH"
                    )
                    digest, _ = _file_hash(artifact)
                    if digest != evidence["sha256"]:
                        raise IntegrityError("E_PROVIDER_EVIDENCE_DIGEST")
            for trial in record["trials"]:
                artifact = self._workspace_artifact(
                    trial["evidence_path"], code="E_PROVIDER_TRIAL_PATH"
                )
                digest, _ = _file_hash(artifact)
                if digest != trial["evidence_sha256"]:
                    raise IntegrityError("E_PROVIDER_TRIAL_DIGEST")
            return

        expected_id = {
            "preflight": ("preflight_id", f"{run_id}/preflight"),
            "context-manifest": (
                "manifest_id",
                f"{run_id}/context-manifest",
            ),
            "plan": ("plan_id", f"{run_id}/plan"),
            "reconciliation": (
                "reconciliation_id",
                f"{run_id}/reconciliation",
            ),
        }[kind]
        if record.get("run_id") != run_id or record.get(expected_id[0]) != expected_id[1]:
            raise IntegrityError(f"E_{kind.upper().replace('-', '_')}_RUN_BINDING")

        if kind == "preflight":
            if (
                record["request_id"] != request["request_id"]
                or record["request_sha256"] != request_digest
            ):
                raise IntegrityError("E_PREFLIGHT_REQUEST_BINDING")
            attestation = self._singleton(
                path, "provider-conformance", required=True
            )
            assert attestation is not None
            attestation_path = path / SINGLETON_FILES["provider-conformance"]
            attestation_digest, _ = _file_hash(attestation_path)
            reference = record["attestation"]
            expected_path = "provider-conformance.json"
            if (
                record["provider_subject"] != attestation["attestation_subject"]
                or reference["attestation_id"] != attestation["attestation_id"]
                or reference["path"] != expected_path
                or reference["sha256"] != attestation_digest
                or reference["status"] != attestation["status"]
            ):
                raise IntegrityError("E_PREFLIGHT_ATTESTATION_BINDING")
            return

        if kind == "context-manifest":
            if (
                record["request_id"] != request["request_id"]
                or record["request_sha256"] != request_digest
                or record["declared_scope_exclusions"] != request["scope"]["exclude"]
            ):
                raise IntegrityError("E_CONTEXT_REQUEST_BINDING")
            budget = record["context_budget"]
            if budget["limit"] != request["budget"]["limits"]["context_bytes"]:
                raise IntegrityError("E_CONTEXT_BUDGET_BINDING")
            selected = 0
            request_entries = 0
            for entry in record["entries"]:
                if entry["resolution_status"] == "RESOLVED":
                    artifact = (
                        self._run_artifact(
                            path, entry["path"], code="E_CONTEXT_ENTRY_PATH"
                        )
                        if entry["artifact_kind"] == "REQUEST"
                        and entry["artifact_id"] == request["request_id"]
                        else self._workspace_artifact(
                            entry["path"], code="E_CONTEXT_ENTRY_PATH"
                        )
                    )
                    digest, byte_length = _file_hash(artifact)
                    if (
                        digest != entry["sha256"]
                        or byte_length != entry["serialized_bytes"]
                    ):
                        raise IntegrityError("E_CONTEXT_ENTRY_CUSTODY")
                if entry["selection"] == "SELECTED":
                    selected += entry["serialized_bytes"]
                if (
                    entry["artifact_kind"] == "REQUEST"
                    and entry["artifact_id"] == request["request_id"]
                    and entry["version"] == request["schema_version"]
                    and entry["selection"] == "SELECTED"
                    and entry["resolution_status"] == "RESOLVED"
                ):
                    request_entries += 1
            if request_entries != 1 or selected != budget["used"] or selected > budget["limit"]:
                raise IntegrityError("E_CONTEXT_BUDGET_ACCOUNTING")
            return

        if kind == "plan":
            context = self._singleton(path, "context-manifest", required=True)
            assert context is not None
            context_digest, _ = _file_hash(path / SINGLETON_FILES["context-manifest"])
            if (
                record["request_id"] != request["request_id"]
                or record["request_sha256"] != request_digest
                or record["context_manifest"]
                != {
                    "manifest_id": context["manifest_id"],
                    "sha256": context_digest,
                }
                or record["risk_tier"] != request["risk_tier"]
                or record["owner"] != authority["phase_owner_id"]
                or record["decision_authority"]
                != authority["decision_authority_id"]
                or record["budget"]["profile"] != request["budget"]["profile"]
                or record["budget"]["limits"] != request["budget"]["limits"]
            ):
                raise IntegrityError("E_PLAN_BINDING")
            return

        if kind == "reconciliation":
            plan = self._singleton(path, "plan", required=True)
            assert plan is not None
            plan_digest, _ = _file_hash(path / SINGLETON_FILES["plan"])
            if (
                record["plan"]
                != {"plan_id": plan["plan_id"], "sha256": plan_digest}
                or record["owner"] != authority["phase_owner_id"]
                or record["decision_authority"]
                != authority["decision_authority_id"]
            ):
                raise IntegrityError("E_RECONCILIATION_BINDING")
            for result in record["lane_results"]:
                for artifact_ref in result["result_artifacts"]:
                    pure = PurePosixPath(artifact_ref["path"])
                    if (
                        "\\" in artifact_ref["path"]
                        or pure.is_absolute()
                        or any(part in {"", ".", ".."} for part in pure.parts)
                    ):
                        raise IntegrityError("E_RECONCILIATION_RESULT_PATH")
                    artifact = path.joinpath(*pure.parts)
                    self._reject_symlink_components(artifact)
                    try:
                        resolved = artifact.resolve(strict=True)
                        resolved.relative_to(path)
                    except (OSError, ValueError) as exc:
                        raise IntegrityError("E_RECONCILIATION_RESULT_PATH") from exc
                    digest, _ = self._hash_regular_file(artifact, path)
                    if digest != artifact_ref["sha256"]:
                        raise IntegrityError("E_RECONCILIATION_RESULT_DIGEST")

    def _ensure_id_unused(self, slug: str, record_id: str) -> None:
        for parent in (self.staging_root / slug, self.research_root / slug / "runs"):
            self._reject_symlink_components(parent)
            if not parent.is_dir():
                continue
            for run in parent.iterdir():
                if not run.is_dir():
                    continue
                for kind, (field, _) in KIND_IDS.items():
                    if kind == "state-event":
                        continue
                    file = run / KIND_FILES[kind]
                    if file.exists() and any(item.get(field) == record_id for item in self._records(run, kind)):
                        raise ConflictError(f"E_ID_REUSE: {record_id}")

    def _dossier_packet_ids(self, slug: str) -> list[str]:
        identifiers: list[str] = []
        for parent in (self.staging_root / slug, self.research_root / slug / "runs"):
            self._reject_symlink_components(parent)
            if not parent.is_dir():
                continue
            for run in sorted(parent.iterdir(), key=lambda item: item.name):
                packet_root = run / "verification-packets"
                if not run.is_dir() or not packet_root.exists():
                    continue
                self._reject_symlink_components(packet_root)
                if not packet_root.is_dir():
                    raise IntegrityError(f"E_VERIFICATION_PACKET_DIRECTORY:{packet_root}")
                for packet_path in sorted(packet_root.iterdir(), key=lambda item: item.name):
                    match = re.fullmatch(r"(VPK-[0-9]{6})\.json", packet_path.name)
                    if match is None or not packet_path.is_file() or packet_path.is_symlink():
                        raise IntegrityError(
                            f"E_VERIFICATION_PACKET_FILE:{packet_path}"
                        )
                    identifiers.append(match.group(1))
        return identifiers

    def _next_packet_id(self, slug: str) -> str:
        identifiers = self._dossier_packet_ids(slug)
        if len(identifiers) != len(set(identifiers)):
            raise IntegrityError("E_VERIFICATION_PACKET_ID_REUSE")
        number = max((int(item[4:]) for item in identifiers), default=0) + 1
        if number > 999_999:
            raise ConflictError("E_VERIFICATION_PACKET_ID_EXHAUSTED")
        return f"VPK-{number:06d}"

    def _packet_dependencies(
        self, records: dict[str, list[dict[str, Any]]], claim_id: str
    ) -> tuple[
        dict[str, Any],
        list[dict[str, Any]],
        list[dict[str, Any]],
        list[dict[str, Any]],
    ]:
        matching_claims = [
            item for item in records["claim"] if item["claim_id"] == claim_id
        ]
        if len(matching_claims) != 1:
            raise IntegrityError(f"E_VERIFICATION_PACKET_CLAIM_CURRENT:{claim_id}")
        claim = matching_claims[0]
        if claim["status"] != "CANDIDATE":
            raise IntegrityError(f"E_VERIFICATION_PACKET_CLAIM_STATUS:{claim_id}")

        contradiction_index = {
            item["contradiction_id"]: item for item in records["contradiction"]
        }
        contradiction_ids = sorted(claim["contradiction_ids"])
        if any(identifier not in contradiction_index for identifier in contradiction_ids):
            raise IntegrityError(
                f"E_VERIFICATION_PACKET_CONTRADICTION_REFERENCE:{claim_id}"
            )
        contradictions = [contradiction_index[identifier] for identifier in contradiction_ids]

        expected_evidence_ids = set(claim["support_evidence_ids"])
        for contradiction in contradictions:
            if contradiction["claim_id"] != claim_id:
                raise IntegrityError(
                    f"E_VERIFICATION_PACKET_CONTRADICTION_CLAIM:{claim_id}"
                )
            expected_evidence_ids.update(contradiction["evidence_ids"])
        if set(claim["evidence_refs"]) != expected_evidence_ids:
            raise IntegrityError(
                f"E_VERIFICATION_PACKET_EVIDENCE_SET:{claim_id}"
            )
        if len(expected_evidence_ids) > MAX_VERIFICATION_PACKET_EVIDENCE:
            raise IntegrityError(
                "E_VERIFICATION_PACKET_EVIDENCE_CAP: "
                f"{len(expected_evidence_ids)}>{MAX_VERIFICATION_PACKET_EVIDENCE}"
            )
        evidence_index = {
            item["evidence_id"]: item for item in records["evidence"]
        }
        if any(identifier not in evidence_index for identifier in expected_evidence_ids):
            raise IntegrityError(
                f"E_VERIFICATION_PACKET_EVIDENCE_REFERENCE:{claim_id}"
            )
        evidence = [
            evidence_index[identifier] for identifier in sorted(expected_evidence_ids)
        ]

        expected_source_ids = {
            source_id
            for item in evidence
            for source_id in item["source_refs"]
        }
        if set(claim["source_refs"]) != expected_source_ids:
            raise IntegrityError(f"E_VERIFICATION_PACKET_SOURCE_SET:{claim_id}")
        source_index = {
            item["source_id"]: item for item in records.get("source", [])
        }
        if any(identifier not in source_index for identifier in expected_source_ids):
            raise IntegrityError(
                f"E_VERIFICATION_PACKET_SOURCE_REFERENCE:{claim_id}"
            )
        sources = [source_index[identifier] for identifier in sorted(expected_source_ids)]
        if len(sources) > MAX_VERIFICATION_PACKET_EVIDENCE:
            raise IntegrityError(
                "E_VERIFICATION_PACKET_SOURCE_CAP: "
                f"{len(sources)}>{MAX_VERIFICATION_PACKET_EVIDENCE}"
            )
        if len(contradictions) > MAX_VERIFICATION_PACKET_EVIDENCE:
            raise IntegrityError(
                "E_VERIFICATION_PACKET_CONTRADICTION_CAP: "
                f"{len(contradictions)}>{MAX_VERIFICATION_PACKET_EVIDENCE}"
            )
        return claim, sources, evidence, contradictions

    def _project_verification_packet(
        self, path: Path, packet_id: str, claim_id: str
    ) -> dict[str, Any]:
        request, request_digest = self._request(path)
        records = self._all_records(path)
        claim, sources, evidence, contradictions = self._packet_dependencies(
            records, claim_id
        )
        return {
            "claim": {
                "claim_id": claim["claim_id"],
                "claim_sha256": sha256_bytes(canonical_json(claim)),
                "claim_type": claim["claim_type"],
                "record_version": claim["record_version"],
                "scope": claim["scope"],
                "text": claim["text"],
            },
            "contradictions": contradictions,
            "evidence": evidence,
            "packet_id": packet_id,
            "request_binding": {
                "request": request,
                "request_id": request["request_id"],
                "request_sha256": request_digest,
            },
            "run_id": path.name,
            "schema_version": "research-verification-packet/v1",
            "sources": sources,
        }

    @staticmethod
    def _verification_packet_receipt(packet: dict[str, Any]) -> dict[str, Any]:
        payload = canonical_json(packet)
        packet_id = packet["packet_id"]
        return {
            "packet": packet,
            "packet_ref": {
                "byte_length": len(payload),
                "packet_id": packet_id,
                "path": f"verification-packets/{packet_id}.json",
                "sha256": sha256_bytes(payload),
            },
        }

    def _build_verification_packet_locked(
        self, path: Path, slug: str, claim_id: str
    ) -> dict[str, Any]:
        """Return or create the claim's sole current packet under the slug lock."""

        packets = self._verification_packets(path)
        matches = [
            packet
            for packet in packets.values()
            if packet["claim"]["claim_id"] == claim_id
        ]
        if len(matches) > 1:
            raise IntegrityError(f"E_VERIFICATION_PACKET_CLAIM_DUPLICATE:{claim_id}")
        if matches:
            return self._verification_packet_receipt(matches[0])

        packet_id = self._next_packet_id(slug)
        packet = self._project_verification_packet(path, packet_id, claim_id)
        self._validate_schema("verification-packet", packet)
        payload = canonical_json(packet)
        if len(payload) > MAX_VERIFICATION_PACKET_BYTES:
            raise IntegrityError(
                "E_VERIFICATION_PACKET_SIZE: "
                f"{len(payload)}>{MAX_VERIFICATION_PACKET_BYTES}"
            )
        relative = f"verification-packets/{packet_id}.json"
        target = path / relative
        request, _ = self._request(path)
        self._assert_write_fence(
            request,
            [
                target.relative_to(self.workspace).as_posix(),
                f".devforgeai/research-locks/{slug}.lock",
            ],
        )
        self._safe_directory(target.parent, create=True)
        if target.exists() or target.is_symlink():
            raise ConflictError(f"E_VERIFICATION_PACKET_EXISTS:{packet_id}")
        _atomic(target, payload + b"\n")
        readback = _read_json(target)
        if readback != packet:
            raise IntegrityError("E_VERIFICATION_PACKET_READBACK")
        return self._verification_packet_receipt(packet)

    def _verification_packets(
        self, path: Path, *, require_complete: bool = False
    ) -> dict[str, dict[str, Any]]:
        packet_root = path / "verification-packets"
        if not packet_root.exists():
            if require_complete:
                candidate_ids = sorted(
                    item["claim_id"]
                    for item in self._records(path, "claim")
                    if item["status"] == "CANDIDATE"
                )
                if candidate_ids:
                    raise IntegrityError(
                        "E_VERIFICATION_PACKET_CLAIM_MISSING:"
                        + ",".join(candidate_ids)
                    )
            return {}
        self._reject_symlink_components(packet_root)
        if not packet_root.is_dir() or packet_root.is_symlink():
            raise IntegrityError(f"E_VERIFICATION_PACKET_DIRECTORY:{packet_root}")
        claim_records = self._records(path, "claim")
        claims_by_id = {
            item["claim_id"]: item
            for item in claim_records
        }
        candidate_ids = {
            item["claim_id"]
            for item in claim_records
            if item["status"] == "CANDIDATE"
        }
        packets: dict[str, dict[str, Any]] = {}
        packet_claim_ids: set[str] = set()
        for packet_path in sorted(packet_root.iterdir(), key=lambda item: item.name):
            match = re.fullmatch(r"(VPK-[0-9]{6})\.json", packet_path.name)
            if match is None or not packet_path.is_file() or packet_path.is_symlink():
                raise IntegrityError(f"E_VERIFICATION_PACKET_FILE:{packet_path}")
            packet_id = match.group(1)
            packet = _read_json(packet_path)
            if not isinstance(packet, dict):
                raise IntegrityError(f"E_VERIFICATION_PACKET_TYPE:{packet_id}")
            self._validate_schema("verification-packet", packet)
            if packet["packet_id"] != packet_id or packet["run_id"] != path.name:
                raise IntegrityError(f"E_VERIFICATION_PACKET_IDENTITY:{packet_id}")
            claim_id = packet["claim"]["claim_id"]
            claim_record = claims_by_id.get(claim_id)
            if claim_record is not None and claim_record["status"] != "CANDIDATE":
                raise IntegrityError(
                    f"E_VERIFICATION_PACKET_CLAIM_NONCANDIDATE:{claim_id}"
                )
            if claim_id in packet_claim_ids:
                raise IntegrityError(
                    f"E_VERIFICATION_PACKET_CLAIM_DUPLICATE:{claim_id}"
                )
            expected = self._project_verification_packet(
                path, packet_id, claim_id
            )
            if packet != expected:
                raise IntegrityError(f"E_VERIFICATION_PACKET_STALE:{packet_id}")
            payload = canonical_json(packet)
            if len(payload) > MAX_VERIFICATION_PACKET_BYTES:
                raise IntegrityError(f"E_VERIFICATION_PACKET_SIZE:{packet_id}")
            if packet_id in packets:
                raise IntegrityError(f"E_VERIFICATION_PACKET_ID_REUSE:{packet_id}")
            packets[packet_id] = packet
            packet_claim_ids.add(claim_id)
        if require_complete:
            missing = sorted(candidate_ids - packet_claim_ids)
            if missing:
                raise IntegrityError(
                    "E_VERIFICATION_PACKET_CLAIM_MISSING:" + ",".join(missing)
                )
        return packets

    def _validate_verification_record(
        self,
        path: Path,
        request: dict[str, Any],
        record: dict[str, Any],
        claim: dict[str, Any],
    ) -> None:
        packets = self._verification_packets(path, require_complete=True)
        packet_ref = record["packet_ref"]
        packet_id = packet_ref["packet_id"]
        if packet_ref["path"] != f"verification-packets/{packet_id}.json":
            raise IntegrityError("E_VERIFICATION_PACKET_PATH")
        packet = packets.get(packet_id)
        if packet is None:
            raise IntegrityError("E_VERIFICATION_PACKET_MISSING")
        payload = canonical_json(packet)
        if (
            packet_ref["sha256"] != sha256_bytes(payload)
            or packet_ref["byte_length"] != len(payload)
            or len(payload) > MAX_VERIFICATION_PACKET_BYTES
        ):
            raise IntegrityError("E_VERIFICATION_PACKET_CUSTODY")

        claim_binding = record["claim_binding"]
        expected_claim_binding = {
            "claim_id": claim["claim_id"],
            "claim_sha256": sha256_bytes(canonical_json(claim)),
            "record_version": claim["record_version"],
        }
        if (
            record["claim_id"] != claim["claim_id"]
            or claim_binding != expected_claim_binding
            or packet["claim"]["claim_id"] != claim["claim_id"]
            or packet["claim"]["record_version"] != claim["record_version"]
            or packet["claim"]["claim_sha256"] != expected_claim_binding["claim_sha256"]
        ):
            raise IntegrityError("E_VERIFICATION_CLAIM_REVISION")

        source_ids = [item["source_id"] for item in packet["sources"]]
        evidence_ids = [item["evidence_id"] for item in packet["evidence"]]
        contradiction_ids = [
            item["contradiction_id"] for item in packet["contradictions"]
        ]
        expected_sets = {
            "contradiction_ids": contradiction_ids,
            "evidence_ids": evidence_ids,
            "source_ids": source_ids,
        }
        if not set(claim["support_evidence_ids"]).issubset(
            record["reference_sets"]["evidence_ids"]
        ):
            raise IntegrityError("E_VERIFICATION_SUPPORT_COVERAGE")
        if record["reference_sets"] != expected_sets:
            raise IntegrityError("E_VERIFICATION_REFERENCE_SETS")
        if record["source_refs"] != source_ids:
            raise IntegrityError("E_VERIFICATION_SOURCE_EDGE")
        if record["evidence_refs"] != evidence_ids:
            raise IntegrityError("E_VERIFICATION_EVIDENCE_EDGE")

        verifier = record["verifier"]
        sessions = record["session_binding"]
        if (
            sessions["context_mode"] != "PACKET_ONLY"
            or sessions["child_session_id"] != verifier["session_id"]
            or sessions["parent_session_id"] == sessions["child_session_id"]
            or verifier["actor_id"] == claim["author"]["actor_id"]
            or verifier["session_id"] == claim["author"]["session_id"]
        ):
            raise IntegrityError("E_VERIFICATION_INDEPENDENCE")
        try:
            launched = datetime.fromisoformat(
                record["launched_at"].replace("Z", "+00:00")
            )
            completed = datetime.fromisoformat(
                record["completed_at"].replace("Z", "+00:00")
            )
        except (TypeError, ValueError) as exc:
            raise IntegrityError("E_VERIFICATION_TIMING") from exc
        if completed < launched:
            raise IntegrityError("E_VERIFICATION_TIMING")

        derived_outcome = derive_verification_outcome(record["checks"])
        if record["outcome"] != derived_outcome:
            raise IntegrityError(
                f"E_VERIFICATION_OUTCOME:expected={derived_outcome}:actual={record['outcome']}"
            )

        evidence_by_id = {
            item["evidence_id"]: item for item in packet["evidence"]
        }
        source_by_id = {item["source_id"]: item for item in packet["sources"]}
        support_ids = sorted(claim["support_evidence_ids"])
        support_source_ids = sorted(
            {
                evidence_by_id[identifier]["source_id"]
                for identifier in support_ids
            }
        )
        expected_check_ids = {
            "entailment": [claim["claim_id"], *support_ids],
            "scope_match": [claim["claim_id"]],
            "citation_resolution": sorted(
                [*source_ids, *evidence_ids, *contradiction_ids]
            ),
            "source_admission": source_ids,
            "custody_integrity": source_ids,
            "freshness": source_ids,
            "corroboration": support_source_ids,
            "contradictions_considered": contradiction_ids,
        }
        for name in VERIFICATION_CHECKS:
            if record["checks"][name]["relevant_ids"] != expected_check_ids[name]:
                raise IntegrityError(f"E_VERIFICATION_CHECK_REFERENCES:{name}")

        sources_admitted = all(
            source["admission"] == "ADMITTED_EVIDENCE"
            and source["retrieval"]["status"] == "RETRIEVED"
            for source in packet["sources"]
        )
        if record["checks"]["source_admission"]["status"] == "PASS" and not sources_admitted:
            raise IntegrityError("E_VERIFICATION_FALSE_PASS:source_admission")

        custody_valid = True
        for source in packet["sources"]:
            custody = source["custody"]
            if custody["mode"] not in {"TRACKED_CAS", "LOCAL_ONLY_CAS"}:
                custody_valid = False
                continue
            root = (
                self.tracked_cas_root
                if custody["mode"] == "TRACKED_CAS"
                else self.local_cas_root
            )
            try:
                digest, byte_length = self._hash_cas_object(root, custody["sha256"])
            except ResearchError:
                custody_valid = False
                continue
            if digest != custody["sha256"] or byte_length != custody["byte_length"]:
                custody_valid = False
        if record["checks"]["custody_integrity"]["status"] == "PASS" and not custody_valid:
            raise IntegrityError("E_VERIFICATION_FALSE_PASS:custody_integrity")

        as_of = datetime.fromisoformat(request["as_of"].replace("Z", "+00:00"))
        freshness_valid = True
        for source in packet["sources"]:
            try:
                stale_after = datetime.fromisoformat(
                    source["freshness"]["stale_after"].replace("Z", "+00:00")
                )
            except (TypeError, ValueError):
                freshness_valid = False
                continue
            if (
                source["freshness"]["status"] not in {"CURRENT", "AGING"}
                or stale_after <= as_of
            ):
                freshness_valid = False
        if record["checks"]["freshness"]["status"] == "PASS" and not freshness_valid:
            raise IntegrityError("E_VERIFICATION_FALSE_PASS:freshness")

        corroboration_valid = bool(support_source_ids)
        if request["risk_tier"] in {"MATERIAL", "CRITICAL"}:
            support_sources = [source_by_id[identifier] for identifier in support_source_ids]
            corroboration_valid = (
                len({item["publisher"] for item in support_sources}) >= 2
                and len({item["custody"].get("sha256") for item in support_sources}) >= 2
            )
        if record["checks"]["corroboration"]["status"] == "PASS" and not corroboration_valid:
            raise IntegrityError("E_VERIFICATION_FALSE_PASS:corroboration")

        if record["outcome"] == "PASS":
            if record["lifecycle_status"] != "ACCEPTED" or record["readiness_status"] != "READY":
                raise IntegrityError("E_VERIFICATION_PASS_STATE")
            if request["risk_tier"] in {"MATERIAL", "CRITICAL"}:
                raise IntegrityError(
                    "E_NOT_IMPLEMENTED_MATERIAL_INDEPENDENCE: positive "
                    "verification requires canonical source-independence provenance"
                )
            if verifier["kind"] == "PROVIDER_AGENT":
                raise IntegrityError(
                    "E_PROVIDER_VERIFICATION_UNAVAILABLE: trusted broker and provider "
                    "conformance are not implemented"
                )
            if verifier["kind"] != "OFFLINE_TEST_HARNESS":
                raise IntegrityError("E_VERIFICATION_RUNTIME_UNAVAILABLE")

        if verifier["kind"] == "OFFLINE_TEST_HARNESS":
            if (
                verifier["provider"] != "OFFLINE_TEST_HARNESS"
                or verifier["model"] != "DETERMINISTIC_ORACLE"
            ):
                raise IntegrityError("E_OFFLINE_VERIFICATION_IDENTITY")
            attestation = self._singleton(
                path, "provider-conformance", required=True
            )
            preflight = self._singleton(path, "preflight", required=True)
            assert attestation is not None and preflight is not None
            self._validate_singleton_context(
                path, "provider-conformance", attestation
            )
            self._validate_singleton_context(path, "preflight", preflight)
            attestation_path = path / SINGLETON_FILES["provider-conformance"]
            attestation_digest, _ = _file_hash(attestation_path)
            subject = attestation["attestation_subject"]
            conformance_ref = record["provider_conformance"]
            if (
                conformance_ref["attestation_id"] != attestation["attestation_id"]
                or conformance_ref["attestation_sha256"] != attestation_digest
                or subject["provider_kind"] != "OFFLINE_TEST_HARNESS"
                or subject["installed_version"] != verifier["provider_version"]
                or subject["adapter_sha256"] != verifier["adapter_sha256"]
                or attestation["evaluation_profile"] != "OFFLINE_CORE_ACCEPTANCE"
                or attestation["status"] != "SUPPORTED"
            ):
                raise IntegrityError("E_OFFLINE_VERIFICATION_CONFORMANCE")
            try:
                issued = datetime.fromisoformat(
                    attestation["issued_at_utc"].replace("Z", "+00:00")
                )
                expires = datetime.fromisoformat(
                    attestation["expires_at_utc"].replace("Z", "+00:00")
                )
            except (TypeError, ValueError) as exc:
                raise IntegrityError("E_OFFLINE_VERIFICATION_CONFORMANCE") from exc
            if expires <= issued or launched < issued or completed >= expires:
                raise IntegrityError("E_OFFLINE_VERIFICATION_CONFORMANCE")
            expected_launch = sha256_bytes(
                canonical_json(_offline_launch_receipt_projection(record))
            )
            expected_result = sha256_bytes(
                canonical_json(_offline_result_projection(record))
            )
            if record["broker_launch_receipt_sha256"] != expected_launch:
                raise IntegrityError("E_OFFLINE_VERIFICATION_LAUNCH_RECEIPT")
            if record["raw_result_sha256"] != expected_result:
                raise IntegrityError("E_OFFLINE_VERIFICATION_RESULT_CUSTODY")

    def _validate_record_context(self, path: Path, kind: str, record: dict[str, Any]) -> None:
        request, _ = self._request(path)
        all_records = self._all_records(path)
        questions = {item["question_id"] for item in all_records["question"]}
        query_records = {
            item["query_id"]: item for item in all_records["query"]
        }
        queries = set(query_records)
        sources = {item["source_id"]: item for item in all_records.get("source", [])}
        evidence = {item["evidence_id"]: item for item in all_records["evidence"]}
        claims = {item["claim_id"]: item for item in all_records["claim"]}
        decisions = {
            item["decision_id"]: item for item in all_records["decision"]
        }
        limits = request["budget"]["limits"]
        if kind != "state-event" and (
            record.get("decision_authority")
            != request["authority"]["decision_authority_id"]
        ):
            raise IntegrityError("E_RECORD_DECISION_AUTHORITY")
        if not set(record.get("decision_refs", [])).issubset(decisions):
            raise IntegrityError("E_REFERENCE_DECISION")
        if kind == "decision" and record["decision_id"] in record.get(
            "decision_refs", []
        ):
            raise IntegrityError("E_DECISION_SELF_REFERENCE")
        if kind == "decision":
            expected_state = {
                "ACCEPTED": ("ACCEPTED", "READY"),
                "REJECTED": ("REJECTED", "READY"),
                "REVOKED": ("SUPERSEDED", "STALE"),
            }[record["status"]]
        elif kind == "claim":
            expected_state = {
                "CANDIDATE": ("PROPOSED", "READY"),
                "REJECTED": ("REJECTED", "NOT_READY"),
                "SUPERSEDED": ("SUPERSEDED", "STALE"),
                "STALE": ("PROPOSED", "STALE"),
            }[record["status"]]
        elif kind in {"verification", "handoff", "state-event"}:
            expected_state = ("ACCEPTED", "READY")
        else:
            expected_state = ("PROPOSED", "READY")
        if (
            record.get("lifecycle_status"),
            record.get("readiness_status"),
        ) != expected_state:
            raise IntegrityError(f"E_RECORD_STATE:{record['record_id']}")
        if kind == "decision":
            if record["decision_id"] in record.get("supersedes", []):
                raise IntegrityError("E_DECISION_SELF_SUPERSESSION")
        elif record.get("supersedes"):
            raise IntegrityError("E_NOT_IMPLEMENTED_RECORD_SUPERSESSION")
        if kind == "question" and not any(
            item["question_id"] == record["question_id"]
            for item in all_records["question"]
        ) and len(all_records["question"]) >= limits["atomic_questions"]:
            raise IntegrityError("E_BUDGET_ATOMIC_QUESTIONS")
        if kind == "query" and not any(
            item["query_id"] == record["query_id"] for item in all_records["query"]
        ) and len(all_records["query"]) >= limits["discovery_queries"]:
            raise IntegrityError("E_BUDGET_DISCOVERY_QUERIES")
        if kind == "source" and record["admission"] in {
            "ADMITTED_EVIDENCE",
            "ADMITTED_CONTEXT",
        }:
            existing_admitted = sum(
                item["source_id"] != record["source_id"]
                and item["admission"] in {"ADMITTED_EVIDENCE", "ADMITTED_CONTEXT"}
                for item in all_records.get("source", [])
            )
            if existing_admitted >= limits["admitted_sources"]:
                raise IntegrityError("E_BUDGET_ADMITTED_SOURCES")
        if not set(record.get("source_refs", [])).issubset(sources):
            raise IntegrityError("E_REFERENCE_SOURCE")
        if not set(record.get("evidence_refs", [])).issubset(evidence):
            raise IntegrityError("E_REFERENCE_EVIDENCE")
        request_question_index = {
            item["question_id"]: item for item in request["questions"]
        }
        request_questions = set(request_question_index)
        if kind == "question":
            confirmed_question = request_question_index.get(record["question_id"])
            if confirmed_question is None:
                raise IntegrityError("E_REFERENCE_QUESTION_REQUEST")
            if (
                record["text"] != confirmed_question["text"]
                or record["completion_criteria"]
                != confirmed_question["completion_criteria"]
                or record["priority"] != request["risk_tier"]
            ):
                raise IntegrityError("E_QUESTION_REQUEST_BINDING")
        if kind == "query" and not set(record["question_ids"]).issubset(questions):
            raise IntegrityError("E_REFERENCE_QUERY_QUESTION")
        if kind == "query":
            plan = self._singleton(path, "plan", required=True)
            assert plan is not None
            lanes = {
                item["lane_id"]: item for item in plan["lanes"]
            }
            envelopes = {
                item["envelope_id"]: item
                for item in plan["worker_envelopes"]
            }
            lane = lanes.get(record["lane_id"])
            if lane is None:
                raise IntegrityError("E_QUERY_PLAN_LANE")
            envelope = envelopes.get(record["worker_envelope_id"])
            if (
                envelope is None
                or record["worker_envelope_id"]
                not in lane["worker_envelope_ids"]
                or envelope["lane_id"] != record["lane_id"]
            ):
                raise IntegrityError("E_QUERY_PLAN_ENVELOPE")
            if not set(record["question_ids"]).issubset(lane["question_ids"]):
                raise IntegrityError("E_QUERY_LANE_QUESTION")
            allowed_purposes = (
                {"DISCOVERY", "CORROBORATION"}
                if lane["kind"] == "DIRECT"
                else {"CHALLENGE"}
            )
            if record["purpose"] not in allowed_purposes:
                raise IntegrityError("E_QUERY_LANE_PURPOSE")
            other_queries = [
                item
                for item in all_records["query"]
                if item["query_id"] != record["query_id"]
            ]
            if (
                sum(item["lane_id"] == record["lane_id"] for item in other_queries)
                >= lane["query_limit"]
            ):
                raise IntegrityError("E_QUERY_LANE_QUERY_LIMIT")
            if (
                sum(
                    item["worker_envelope_id"] == record["worker_envelope_id"]
                    for item in other_queries
                )
                >= envelope["budgets"]["queries"]
            ):
                raise IntegrityError("E_QUERY_ENVELOPE_QUERY_LIMIT")
            candidate_ids = [item["candidate_id"] for item in record.get("results", [])]
            expected_prefix = record["query_id"] + "-CAND-"
            if len(candidate_ids) != len(set(candidate_ids)) or any(
                not identifier.startswith(expected_prefix)
                for identifier in candidate_ids
            ):
                raise IntegrityError("E_QUERY_CANDIDATE_ID")
        if kind == "source":
            request_questions = {item["question_id"] for item in request["questions"]}
            if not set(record["question_ids"]).issubset(questions | request_questions):
                raise IntegrityError("E_REFERENCE_SOURCE_QUESTION")
            if (
                record["admission"] in {"ADMITTED_EVIDENCE", "ADMITTED_CONTEXT"}
                and record["source_class"]
                in request["source_policy"]["prohibited_classes"]
            ):
                raise IntegrityError("E_SOURCE_POLICY_PROHIBITED")
            source_queries = set(record["query_ids"])
            source_candidates = set(record["candidate_ids"])
            if not source_queries.issubset(queries):
                raise IntegrityError("E_REFERENCE_SOURCE_QUERY")
            if source_queries:
                owner_questions = {
                    question_id
                    for query_id in source_queries
                    for question_id in query_records[query_id]["question_ids"]
                }
                if not set(record["question_ids"]).issubset(owner_questions):
                    raise IntegrityError("E_SOURCE_QUERY_QUESTION_EDGE")
            candidate_owners = {
                candidate_id.split("-CAND-", 1)[0]
                for candidate_id in source_candidates
            }
            if candidate_owners != source_queries:
                raise IntegrityError("E_SOURCE_CANDIDATE_QUERY_EDGE")
            for candidate_id in source_candidates:
                owner = candidate_id.split("-CAND-", 1)[0]
                candidate = next(
                    (
                        item
                        for item in query_records[owner].get("results", [])
                        if item["candidate_id"] == candidate_id
                    ),
                    None,
                )
                if candidate is None:
                    raise IntegrityError("E_REFERENCE_SOURCE_CANDIDATE")
                if candidate["disposition"] != "RETRIEVE":
                    raise IntegrityError("E_SOURCE_CANDIDATE_NOT_RETRIEVE")
                if candidate["locator"] != record["locator"]["value"]:
                    raise IntegrityError("E_SOURCE_CANDIDATE_LOCATOR")
                if record["retrieval"]["status"] == "NOT_ATTEMPTED":
                    raise IntegrityError("E_SOURCE_CANDIDATE_NOT_ATTEMPTED")
            for existing in all_records.get("source", []):
                if (
                    existing["source_id"] != record["source_id"]
                    and source_candidates.intersection(existing["candidate_ids"])
                ):
                    raise IntegrityError("E_SOURCE_CANDIDATE_REUSE")
            self._validate_source_network(request, record)
            try:
                as_of = datetime.fromisoformat(request["as_of"].replace("Z", "+00:00"))
                stale_after = datetime.fromisoformat(
                    record["freshness"]["stale_after"].replace("Z", "+00:00")
                )
                checked_at = datetime.fromisoformat(
                    record["freshness"]["checked_at"].replace("Z", "+00:00")
                )
            except (TypeError, ValueError) as exc:
                raise IntegrityError("E_SOURCE_FRESHNESS_TIMESTAMP") from exc
            if checked_at > stale_after:
                raise IntegrityError("E_SOURCE_FRESHNESS_WINDOW")
            if (
                stale_after <= as_of
                and record["freshness"]["status"] in {"CURRENT", "AGING"}
            ):
                raise IntegrityError("E_SOURCE_FRESHNESS_STALE_AT_AS_OF")
        if kind == "evidence":
            source = sources.get(record["source_id"])
            if source is None or not set(record["question_ids"]).issubset(questions):
                raise IntegrityError("E_REFERENCE_EVIDENCE")
            if not set(record["question_ids"]).issubset(source["question_ids"]):
                raise IntegrityError("E_EVIDENCE_SOURCE_QUESTION_EDGE")
            if record["source_refs"] != [record["source_id"]]:
                raise IntegrityError("E_EVIDENCE_SOURCE_EDGE")
            if (
                source["retrieval"]["status"] != "RETRIEVED"
                or source.get("admission") != "ADMITTED_EVIDENCE"
            ):
                raise IntegrityError("E_G5_SOURCE_NOT_ADMITTED")
            if source["freshness"]["status"] == "STALE":
                raise IntegrityError("E_G5_SOURCE_STALE")
            if source["custody"].get("sha256") != record["source_sha256"]:
                raise IntegrityError("E_EVIDENCE_SOURCE_DIGEST")
            if sha256_bytes(record["content"].encode("utf-8")) != record["content_sha256"]:
                raise IntegrityError("E_EVIDENCE_CONTENT_DIGEST")
            self._validate_excerpt_limit(
                source,
                all_records["evidence"],
                record,
            )
        if kind == "claim":
            if not set(record["question_ids"]).issubset(questions):
                raise IntegrityError("E_REFERENCE_CLAIM_QUESTION")
            if not set(record["support_evidence_ids"]).issubset(evidence):
                raise IntegrityError("E_REFERENCE_CLAIM_EVIDENCE")
            if any(
                evidence[identifier]["polarity"] != "SUPPORTING"
                for identifier in record["support_evidence_ids"]
            ):
                raise IntegrityError("E_CLAIM_SUPPORT_POLARITY")
            if not set(record["support_evidence_ids"]).issubset(
                record["evidence_refs"]
            ):
                raise IntegrityError("E_CLAIM_SUPPORT_EDGE")
            supported_questions = {
                question_id
                for evidence_id in record["support_evidence_ids"]
                for question_id in evidence[evidence_id]["question_ids"]
            }
            if not set(record["question_ids"]).issubset(supported_questions):
                raise IntegrityError("E_CLAIM_EVIDENCE_QUESTION_EDGE")
        if kind == "contradiction":
            claim = claims.get(record["claim_id"])
            if claim is None or not set(record["evidence_ids"]).issubset(evidence):
                raise IntegrityError("E_REFERENCE_CONTRADICTION")
            if set(record["evidence_ids"]) != set(record["evidence_refs"]):
                raise IntegrityError("E_CONTRADICTION_EVIDENCE_EDGE")
            contradiction_sources = {
                source_id
                for evidence_id in record["evidence_ids"]
                for source_id in evidence[evidence_id]["source_refs"]
            }
            if set(record["source_refs"]) != contradiction_sources:
                raise IntegrityError("E_CONTRADICTION_SOURCE_EDGE")
            contradiction_questions = {
                question_id
                for evidence_id in record["evidence_ids"]
                for question_id in evidence[evidence_id]["question_ids"]
            }
            if not set(claim["question_ids"]).issubset(contradiction_questions):
                raise IntegrityError("E_CONTRADICTION_EVIDENCE_QUESTION_EDGE")
        if kind == "verification":
            claim = claims.get(record["claim_id"])
            if claim is None:
                raise IntegrityError("E_REFERENCE_VERIFICATION")
            self._validate_verification_record(path, request, record, claim)
        if kind == "synthesis":
            for disposition in record["question_dispositions"]:
                if disposition["question_id"] not in questions or not set(disposition["claim_ids"]).issubset(claims):
                    raise IntegrityError("E_REFERENCE_SYNTHESIS")
                if any(
                    disposition["question_id"]
                    not in claims[claim_id]["question_ids"]
                    for claim_id in disposition["claim_ids"]
                ):
                    raise IntegrityError("E_SYNTHESIS_CLAIM_QUESTION_EDGE")
            for assertion in record["assertions"]:
                if not set(assertion["claim_ids"]).issubset(claims):
                    raise IntegrityError("E_REFERENCE_SYNTHESIS_CLAIM")
            if record["conclusion_status"] != "PROPOSED":
                raise IntegrityError("E_SYNTHESIS_AUTHORITY")
        if kind == "decision":
            authority = request["authority"]["decision_authority_id"]
            if (
                record["authority_id"] != authority
                or record["decision_authority"] != authority
                or record["risk_tier"] != request["risk_tier"]
            ):
                raise IntegrityError("E_DECISION_AUTHORITY")
            if not set(record["decision_refs"]).issubset(decisions):
                raise IntegrityError("E_DECISION_REFERENCE")
            if not set(record["supersedes"]).issubset(decisions):
                raise IntegrityError("E_DECISION_SUPERSEDES")
            if (
                record["decision_type"] == "PERMITTED_WAIVER"
                and request["risk_tier"] == "CRITICAL"
            ):
                raise IntegrityError("E_CRITICAL_WAIVER_PROHIBITED")
        if kind == "handoff":
            if record["result"]["outcome"] != "READY_TO_SEAL":
                raise IntegrityError("E_NOT_IMPLEMENTED_HANDOFF_OUTCOME")
            if record["run_id"] != path.name or record["location"]["slug"] != request["slug"]:
                raise IntegrityError("E_HANDOFF_IDENTITY")
            if "manifest_sha256" in record:
                raise IntegrityError("E_HANDOFF_CIRCULAR_INTEGRITY")
            for artifact in record["canonical_artifacts"]:
                artifact_id = artifact["artifact_id"].lower()
                normalized_path = artifact["path"].replace("\\", "/").lower()
                basename = normalized_path.rsplit("/", 1)[-1]
                if (
                    basename
                    in {
                        "handoff.json",
                        "handoff.md",
                        "manifest.sha256",
                        "registry.jsonl",
                    }
                    or "seal-receipt" in artifact_id
                    or "seal_receipt" in artifact_id
                    or "seal-receipt" in normalized_path
                    or "seal_receipt" in normalized_path
                ):
                    raise IntegrityError("E_HANDOFF_CIRCULAR_ARTIFACT")
            self._validate_handoff_artifacts(path, request, record)
            budget_errors = self._budget_limit_errors(
                request["budget"]["limits"], record["budget"]["actual"]
            )
            if budget_errors:
                raise IntegrityError(budget_errors[0])

    @staticmethod
    def _url_origin(value: str) -> str:
        """Return the canonical HTTP(S) origin for a network locator."""

        try:
            parsed = urlsplit(value)
            port = parsed.port
        except (TypeError, ValueError) as exc:
            raise ResearchError("E_NETWORK_URL") from exc
        scheme = parsed.scheme.lower()
        hostname = parsed.hostname
        if (
            scheme not in {"http", "https"}
            or not hostname
            or parsed.username is not None
            or parsed.password is not None
        ):
            raise ResearchError("E_NETWORK_URL")
        try:
            host = hostname.encode("idna").decode("ascii").lower()
        except UnicodeError as exc:
            raise ResearchError("E_NETWORK_URL") from exc
        if ":" in host:
            host = f"[{host}]"
        if port == (443 if scheme == "https" else 80):
            port = None
        return f"{scheme}://{host}" + (f":{port}" if port is not None else "")

    def _validate_network_request(self, request: dict[str, Any]) -> None:
        policy = request["execution_policy"]
        mode = policy["network_policy"]
        allowlist = policy["network_allowlist"]
        if mode == "DENY" and allowlist:
            raise ResearchError("E_NETWORK_DENY_ALLOWLIST")
        if mode == "ALLOWLIST" and not allowlist:
            raise ResearchError("E_NETWORK_ALLOWLIST_EMPTY")
        for entry in allowlist:
            if not ALLOWLIST_ORIGIN_RE.fullmatch(entry):
                raise ResearchError("E_NETWORK_ALLOWLIST_ORIGIN")
            if self._url_origin(entry) != entry:
                raise ResearchError("E_NETWORK_ALLOWLIST_CANONICAL")

    def _validate_source_network(
        self, request: dict[str, Any], source: dict[str, Any]
    ) -> None:
        retrieval = source["retrieval"]
        method = retrieval["method"]
        network_accessed = retrieval["network_accessed"]
        network_method = method in {"WEB", "MCP"}
        if network_method != network_accessed:
            raise IntegrityError("E_NETWORK_RETRIEVAL_DECLARATION")
        if not network_accessed:
            return
        locator = source["locator"]
        if locator["kind"] != "URL":
            raise IntegrityError("E_NETWORK_LOCATOR")
        origin = self._url_origin(locator["value"])
        policy = request["execution_policy"]
        if policy["network_policy"] == "DENY":
            raise IntegrityError("E_NETWORK_DENY")
        if (
            policy["network_policy"] == "ALLOWLIST"
            and origin not in policy["network_allowlist"]
        ):
            raise IntegrityError(f"E_NETWORK_ALLOWLIST:{origin}")

    @staticmethod
    def _budget_limit_errors(
        limits: dict[str, int], actual: dict[str, Any]
    ) -> list[str]:
        mappings = (
            ("atomic_questions", "atomic_questions"),
            ("research_lanes", "research_lanes"),
            ("concurrent_workers_peak", "concurrent_workers"),
            ("discovery_queries", "discovery_queries"),
            ("admitted_sources", "admitted_sources"),
            ("external_tool_calls", "external_tool_calls"),
            ("aggregate_model_tokens", "aggregate_model_tokens"),
            ("context_bytes", "context_bytes"),
            ("elapsed_minutes", "elapsed_minutes"),
        )
        errors = [
            f"E_BUDGET_{actual_key.upper()}"
            for actual_key, limit_key in mappings
            if actual[actual_key] > limits[limit_key]
        ]
        if actual["retries"] > (
            limits["retry_per_failed_lane"] * actual["research_lanes"]
        ):
            errors.append("E_BUDGET_RETRIES")
        return errors

    def _validate_excerpt_limit(
        self,
        source: dict[str, Any],
        existing_evidence: list[dict[str, Any]],
        candidate: dict[str, Any],
    ) -> None:
        policy = source["retention_policy"]
        if policy["redistribution_basis"] != "NONE":
            return
        evidence = list(existing_evidence)
        if not any(
            item["evidence_id"] == candidate["evidence_id"] for item in evidence
        ):
            evidence.append(candidate)
        word_count = sum(
            len(re.findall(r"\S+", item["content"], flags=re.UNICODE))
            for item in evidence
            if item["source_id"] == source["source_id"]
            and item["representation"] == "EXCERPT"
        )
        if word_count > MAX_UNLICENSED_EXCERPT_WORDS:
            raise IntegrityError(
                f"E_EXCERPT_WORD_LIMIT:{source['source_id']}:{word_count}"
            )

    def _validate_handoff_artifacts(
        self,
        run_path: Path,
        request: dict[str, Any],
        handoff: dict[str, Any],
    ) -> None:
        try:
            run_root = run_path.resolve(strict=True)
            run_root.relative_to(self.workspace)
        except (OSError, ValueError) as exc:
            raise IntegrityError("E_HANDOFF_ARTIFACT_RUN_PATH") from exc
        records = self._all_records(run_path)
        verification_outcomes: dict[str, str] = {}
        for verification in records["verification"]:
            verification_outcomes[verification["claim_id"]] = verification[
                "outcome"
            ]
        record_index: dict[str, tuple[str, dict[str, Any]]] = {}
        for kind, items in records.items():
            if kind == "handoff":
                continue
            identifier_field, _ = KIND_IDS[kind]
            for item in items:
                record_index[item[identifier_field]] = (kind, item)

        seen: set[str] = set()
        for artifact in handoff["canonical_artifacts"]:
            declared = artifact["path"]
            relative = PurePosixPath(declared)
            if (
                "\\" in declared
                or relative.is_absolute()
                or relative.as_posix() != declared
                or any(part in {"", ".", ".."} for part in relative.parts)
            ):
                raise IntegrityError(f"E_HANDOFF_ARTIFACT_PATH:{declared}")
            if declared in seen:
                raise IntegrityError(f"E_HANDOFF_ARTIFACT_PATH_DUPLICATE:{declared}")
            seen.add(declared)
            candidate = run_path.joinpath(*relative.parts)
            self._reject_symlink_components(candidate)
            try:
                candidate_stat = candidate.lstat()
                resolved = candidate.resolve(strict=True)
                resolved.relative_to(run_root)
            except (OSError, ValueError) as exc:
                raise IntegrityError(
                    f"E_HANDOFF_ARTIFACT_MISSING_OR_ESCAPE:{declared}"
                ) from exc
            if resolved != candidate or not stat.S_ISREG(candidate_stat.st_mode):
                raise IntegrityError(f"E_HANDOFF_ARTIFACT_FILE_TYPE:{declared}")
            repository_path = candidate.relative_to(self.workspace).as_posix()
            self._assert_write_fence(request, [repository_path])
            digest, byte_length = self._hash_regular_file(candidate, run_root)
            if digest != artifact["sha256"]:
                raise IntegrityError(f"E_HANDOFF_ARTIFACT_SHA256:{declared}")
            if (
                "byte_length" in artifact
                and byte_length != artifact["byte_length"]
            ):
                raise IntegrityError(f"E_HANDOFF_ARTIFACT_BYTE_LENGTH:{declared}")
            indexed = record_index.get(artifact["artifact_id"])
            if indexed is None:
                raise IntegrityError(
                    f"E_HANDOFF_ARTIFACT_RECORD:{artifact['artifact_id']}"
                )
            kind, record = indexed
            if kind == "claim":
                verification_status = verification_outcomes.get(
                    record["claim_id"], "NOT_RUN"
                )
            elif kind == "verification":
                verification_status = record["outcome"]
            else:
                verification_status = "NOT_APPLICABLE"
            expected_semantics = {
                "version": str(record["record_version"]),
                "path": KIND_FILES[kind],
                "lifecycle_status": record["lifecycle_status"],
                "readiness_status": record["readiness_status"],
                "verification_status": verification_status,
                "owner": record["owner"],
            }
            if any(
                artifact[field] != value
                for field, value in expected_semantics.items()
            ):
                raise IntegrityError(
                    f"E_HANDOFF_ARTIFACT_SEMANTICS:{artifact['artifact_id']}"
                )

    def _hash_regular_file(self, path: Path, allowed_root: Path) -> tuple[str, int]:
        """Hash one nonsymlink regular file after resolving it within a root."""

        self._reject_symlink_components(path)
        try:
            before = path.lstat()
            resolved = path.resolve(strict=True)
            resolved.relative_to(allowed_root)
        except (OSError, ValueError) as exc:
            raise IntegrityError(f"E_FILE_HASH_FENCE:{path}") from exc
        if resolved != path or not stat.S_ISREG(before.st_mode):
            raise IntegrityError(f"E_FILE_HASH_TYPE:{path}")
        descriptor = -1
        try:
            descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
            opened = os.fstat(descriptor)
            if (
                opened.st_dev != before.st_dev
                or opened.st_ino != before.st_ino
                or not stat.S_ISREG(opened.st_mode)
            ):
                raise IntegrityError(f"E_FILE_HASH_RACE:{path}")
            digest = hashlib.sha256()
            size = 0
            while block := os.read(descriptor, 1024 * 1024):
                digest.update(block)
                size += len(block)
            after = os.fstat(descriptor)
            if (
                opened.st_size != after.st_size
                or opened.st_mtime_ns != after.st_mtime_ns
            ):
                raise IntegrityError(f"E_FILE_HASH_CHANGED:{path}")
            return digest.hexdigest(), size
        except ResearchError:
            raise
        except OSError as exc:
            raise IntegrityError(f"E_FILE_HASH:{path}:{exc}") from exc
        finally:
            if descriptor >= 0:
                with contextlib.suppress(OSError):
                    os.close(descriptor)

    def _retention_policy(self, value: Any) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise SourceEligibilityError("E_RETENTION_POLICY_REQUIRED")
        required = {
            "data_classification",
            "redistribution_basis",
            "redistribution_reference",
            "retention_permitted",
            "sensitive_scan",
        }
        if set(value) != required or not isinstance(value["retention_permitted"], bool):
            raise SourceEligibilityError("E_RETENTION_POLICY_SHAPE")
        if value["redistribution_basis"] not in {
            "SPDX_LICENSE", "PUBLIC_DOMAIN", "OWNER_PERMISSION", "USER_OWNED", "NONE"
        }:
            raise SourceEligibilityError("E_REDISTRIBUTION_BASIS")
        if value["data_classification"] not in {"PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"}:
            raise SourceEligibilityError("E_DATA_CLASSIFICATION")
        reference = value["redistribution_reference"]
        if reference is not None and (not isinstance(reference, str) or not reference):
            raise SourceEligibilityError("E_REDISTRIBUTION_REFERENCE")
        scan = value["sensitive_scan"]
        if not isinstance(scan, dict) or set(scan) != {"status", "scanner_id", "ruleset_sha256", "findings_count"}:
            raise SourceEligibilityError("E_SENSITIVE_SCAN_SHAPE")
        if scan["status"] not in {"PASS", "FAIL", "NOT_RUN", "COULD_NOT_RUN", "INFRA_FAILURE"}:
            raise SourceEligibilityError("E_SENSITIVE_SCAN_STATUS")
        if not isinstance(scan["scanner_id"], str) or not scan["scanner_id"]:
            raise SourceEligibilityError("E_SENSITIVE_SCAN_ID")
        if not isinstance(scan["ruleset_sha256"], str) or not HASH_RE.fullmatch(scan["ruleset_sha256"]):
            raise SourceEligibilityError("E_SENSITIVE_SCAN_RULESET")
        if not isinstance(scan["findings_count"], int) or isinstance(scan["findings_count"], bool) or scan["findings_count"] < 0:
            raise SourceEligibilityError("E_SENSITIVE_SCAN_FINDINGS")
        return value

    def _tracked_eligible(
        self,
        policy: dict[str, Any],
        size: int,
        digest: str,
        slug: str,
    ) -> tuple[bool, list[str]]:
        reasons: list[str] = []
        if policy["redistribution_basis"] == "NONE":
            reasons.append("redistribution_basis")
        if not policy["redistribution_reference"]:
            reasons.append("redistribution_reference")
        if policy["data_classification"] != "PUBLIC":
            reasons.append("data_classification")
        scan = policy["sensitive_scan"]
        if scan["status"] != "PASS" or scan["findings_count"] != 0:
            reasons.append("sensitive_scan")
        if size > MAX_TRACKED_OBJECT:
            reasons.append("object_size")
        tracked: dict[str, int] = {}
        for parent in (self.staging_root / slug, self.research_root / slug / "runs"):
            self._reject_symlink_components(parent)
            if not parent.is_dir():
                continue
            for run in parent.iterdir():
                source_file = run / "sources.jsonl"
                if not run.is_dir() or not source_file.exists():
                    continue
                for source in _read_lines(source_file):
                    custody = source["custody"]
                    if custody["mode"] == "TRACKED_CAS":
                        tracked[custody["sha256"]] = custody["byte_length"]
        total = sum(tracked.values()) + (0 if digest in tracked else size)
        if total > MAX_TRACKED_DOSSIER:
            reasons.append("dossier_size")
        return not reasons, reasons

    @staticmethod
    def _assert_write_fence(request: dict[str, Any], paths: list[str]) -> None:
        fences = request["execution_policy"]["write_fence"]
        for candidate in paths:
            normalized = candidate.strip("/")
            if not any(
                normalized == fence.rstrip("/")
                or normalized.startswith(fence.rstrip("/") + "/")
                for fence in fences
            ):
                raise ResearchError(f"E_WRITE_FENCE: {candidate}")

    @contextlib.contextmanager
    def _cas_global_lock(self) -> Iterator[None]:
        """Serialize both CAS classes without waiting on another writer."""

        cas_ops.nofollow_flag()
        try:
            with self._lock("global"):
                yield
        except ConflictError as exc:
            if str(exc) == "E_WRITER_COLLISION: global":
                raise ConflictError("E_CAS_WRITER_COLLISION") from exc
            raise

    def _put_cas(
        self,
        source: Path,
        root: Path,
        *,
        cas_class: str,
        slug: str,
        run_id: str,
        proposed_source_id: str,
    ) -> tuple[str, int, Path]:
        if cas_class not in {"TRACKED_CAS", "LOCAL_ONLY_CAS"}:
            raise IntegrityError("E_CAS_CLASS")
        expected_root = (
            self.tracked_cas_root
            if cas_class == "TRACKED_CAS"
            else self.local_cas_root
        )
        if root != expected_root:
            raise IntegrityError("E_CAS_CLASS_ROOT")
        self._reject_symlink_components(root)
        source_fd = -1
        temporary_fd = -1
        temporary: Path | None = None
        with self._cas_global_lock():
            root.mkdir(parents=True, exist_ok=True)
            self._resolved_cas_root(root)
            _fsync_dir(root)
            try:
                source_fd = os.open(source, os.O_RDONLY | cas_ops.nofollow_flag())
                temporary_fd, name = tempfile.mkstemp(prefix=".incoming-", dir=root)
                temporary = Path(name)
                digest = hashlib.sha256()
                size = 0
                before = os.fstat(source_fd)
                with os.fdopen(source_fd, "rb") as incoming, os.fdopen(
                    temporary_fd, "wb"
                ) as outgoing:
                    source_fd = temporary_fd = -1
                    while block := incoming.read(1024 * 1024):
                        digest.update(block)
                        size += len(block)
                        outgoing.write(block)
                    after = os.fstat(incoming.fileno())
                    outgoing.flush()
                    os.fsync(outgoing.fileno())
                if (
                    before.st_dev,
                    before.st_ino,
                    before.st_size,
                    before.st_mtime_ns,
                ) != (
                    after.st_dev,
                    after.st_ino,
                    after.st_size,
                    after.st_mtime_ns,
                ):
                    raise ConflictError("E_SOURCE_CHANGED_DURING_READ")
                hexdigest = digest.hexdigest()
                parent = root / hexdigest[:2]
                self._safe_directory(parent, create=True)
                try:
                    parent.resolve(strict=True).relative_to(self._resolved_cas_root(root))
                except (OSError, ValueError) as exc:
                    raise IntegrityError(f"E_CAS_PATH_ESCAPE: {parent}") from exc
                _fsync_dir(root)
                target = parent / hexdigest

                try:
                    recovered = self._recover_quarantine_orphans(
                        root, hexdigest, target
                    )
                except BaseException as exc:
                    if isinstance(exc, (KeyboardInterrupt, SystemExit)):
                        raise
                    raise IntegrityError(
                        f"E_CAS_QUARANTINE_FAILED: orphan recovery: {exc}"
                    ) from exc
                if recovered:
                    raise IntegrityError(
                        "E_CAS_INTEGRITY: recovered quarantine "
                        + ",".join(recovered)
                    )

                classification = self._classify_cas_entry(target)
                if classification is not None:
                    entry_type, actual, actual_size = classification
                    if (
                        entry_type == "REGULAR_FILE"
                        and actual == hexdigest
                        and actual_size == size
                    ):
                        return hexdigest, size, target
                    receipt = self._quarantine_corrupt_object(
                        root=root,
                        target=target,
                        cas_class=cas_class,
                        slug=slug,
                        run_id=run_id,
                        proposed_source_id=proposed_source_id,
                        claimed_sha256=hexdigest,
                        classification=classification,
                    )
                    raise IntegrityError(
                        "E_CAS_INTEGRITY: "
                        f"{receipt['quarantine_id']} receipt={receipt['receipt_path']} "
                        f"receipt_sha256={receipt['receipt_sha256']}"
                    )

                assert temporary is not None
                try:
                    cas_ops.rename_noreplace(temporary, target)
                except FileExistsError:
                    classification = self._classify_cas_entry(target)
                    if classification is None:
                        raise IntegrityError("E_CAS_INSTALL_RACE") from None
                    entry_type, actual, actual_size = classification
                    if (
                        entry_type == "REGULAR_FILE"
                        and actual == hexdigest
                        and actual_size == size
                    ):
                        return hexdigest, size, target
                    receipt = self._quarantine_corrupt_object(
                        root=root,
                        target=target,
                        cas_class=cas_class,
                        slug=slug,
                        run_id=run_id,
                        proposed_source_id=proposed_source_id,
                        claimed_sha256=hexdigest,
                        classification=classification,
                    )
                    raise IntegrityError(
                        "E_CAS_INTEGRITY: "
                        f"{receipt['quarantine_id']} receipt={receipt['receipt_path']} "
                        f"receipt_sha256={receipt['receipt_sha256']}"
                    ) from None
                except OSError as exc:
                    raise IntegrityError(f"E_CAS_INSTALL_FAILED: {exc}") from exc
                cas_ops.fsync_regular_nofollow(target)
                _fsync_dir(parent)
                check, check_size = self._hash_cas_object(root, hexdigest)
                if check != hexdigest or check_size != size:
                    raise IntegrityError("E_CAS_READBACK")
                return hexdigest, size, target
            finally:
                for descriptor in (source_fd, temporary_fd):
                    if descriptor >= 0:
                        with contextlib.suppress(OSError):
                            os.close(descriptor)
                if temporary is not None:
                    with contextlib.suppress(FileNotFoundError):
                        temporary.unlink()

    @staticmethod
    def _entry_type(mode: int) -> str:
        if stat.S_ISREG(mode):
            return "REGULAR_FILE"
        if stat.S_ISLNK(mode):
            return "SYMLINK"
        if stat.S_ISDIR(mode):
            return "DIRECTORY"
        if stat.S_ISFIFO(mode):
            return "FIFO"
        if stat.S_ISSOCK(mode):
            return "SOCKET"
        if stat.S_ISCHR(mode):
            return "CHAR_DEVICE"
        if stat.S_ISBLK(mode):
            return "BLOCK_DEVICE"
        return "OTHER"

    def _classify_cas_entry(
        self, path: Path
    ) -> tuple[str, str | None, int | None] | None:
        """Classify without following a link; hash only a stable regular file."""

        try:
            mode = path.lstat().st_mode
        except FileNotFoundError:
            return None
        except OSError as exc:
            raise IntegrityError(f"E_CAS_OBJECT_LSTAT: {path}: {exc}") from exc
        entry_type = self._entry_type(mode)
        if entry_type != "REGULAR_FILE":
            return entry_type, None, None
        try:
            actual, size = cas_ops.hash_regular_nofollow(path)
        except OSError as exc:
            raise IntegrityError(f"E_CAS_OBJECT_READ: {path}: {exc}") from exc
        return entry_type, actual, size

    def _quarantine_directory(self, root: Path, claimed_sha256: str) -> Path:
        if not HASH_RE.fullmatch(claimed_sha256):
            raise IntegrityError("E_CAS_DIGEST")
        quarantine = root.parent / "quarantine"
        sha_root = quarantine / "sha256"
        destination = sha_root / claimed_sha256
        for path in (quarantine, sha_root, destination):
            self._safe_directory(path, create=True)
            try:
                path.resolve(strict=True).relative_to(root.parent.resolve(strict=True))
            except (OSError, ValueError) as exc:
                raise IntegrityError(f"E_CAS_QUARANTINE_ESCAPE: {path}") from exc
            _fsync_dir(path)
            _fsync_dir(path.parent)
        return destination

    @staticmethod
    def _next_quarantine_id(directory: Path) -> str:
        occupied: set[int] = set()
        for entry in directory.iterdir():
            match = re.match(r"^(QAR-([0-9]{6}))(?:\..+)?$", entry.name)
            if match:
                occupied.add(int(match.group(2)))
        for number in range(1, 1_000_000):
            if number not in occupied:
                return f"QAR-{number:06d}"
        raise IntegrityError("E_CAS_QUARANTINE_ID_EXHAUSTED")

    def _quarantine_receipt(
        self,
        *,
        quarantine_id: str,
        cas_class: str,
        slug: str,
        run_id: str,
        proposed_source_id: str,
        original_path: Path,
        quarantine_path: Path,
        claimed_sha256: str,
        classification: tuple[str, str | None, int | None],
        detected_at: str,
    ) -> dict[str, Any]:
        entry_type, actual_sha256, actual_byte_length = classification
        return {
            "schema_version": "research-cas-quarantine-receipt/v1",
            "quarantine_id": quarantine_id,
            "cas_class": cas_class,
            "run_id": run_id,
            "slug": slug,
            "proposed_source_id": proposed_source_id,
            "original_path": original_path.relative_to(self.workspace).as_posix(),
            "quarantine_path": quarantine_path.relative_to(self.workspace).as_posix(),
            "entry_type": entry_type,
            "claimed_sha256": claimed_sha256,
            "actual_sha256": actual_sha256,
            "actual_byte_length": actual_byte_length,
            "detected_at": detected_at,
        }

    @staticmethod
    def _validate_quarantine_receipt(receipt: Any) -> None:
        expected_keys = {
            "schema_version",
            "quarantine_id",
            "cas_class",
            "run_id",
            "slug",
            "proposed_source_id",
            "original_path",
            "quarantine_path",
            "entry_type",
            "claimed_sha256",
            "actual_sha256",
            "actual_byte_length",
            "detected_at",
        }
        entry_types = {
            "REGULAR_FILE",
            "SYMLINK",
            "DIRECTORY",
            "FIFO",
            "SOCKET",
            "CHAR_DEVICE",
            "BLOCK_DEVICE",
            "OTHER",
        }
        if not isinstance(receipt, dict) or set(receipt) != expected_keys:
            raise IntegrityError("E_CAS_QUARANTINE_RECEIPT_SHAPE")
        if receipt["schema_version"] != "research-cas-quarantine-receipt/v1":
            raise IntegrityError("E_CAS_QUARANTINE_RECEIPT_VERSION")
        if not QAR_RE.fullmatch(receipt["quarantine_id"]):
            raise IntegrityError("E_CAS_QUARANTINE_RECEIPT_ID")
        if receipt["cas_class"] not in {"TRACKED_CAS", "LOCAL_ONLY_CAS"}:
            raise IntegrityError("E_CAS_QUARANTINE_RECEIPT_CLASS")
        if not RUN_RE.fullmatch(receipt["run_id"]):
            raise IntegrityError("E_CAS_QUARANTINE_RECEIPT_RUN")
        if not SLUG_RE.fullmatch(receipt["slug"]):
            raise IntegrityError("E_CAS_QUARANTINE_RECEIPT_SLUG")
        if not re.fullmatch(r"SRC-[0-9]{6}", receipt["proposed_source_id"]):
            raise IntegrityError("E_CAS_QUARANTINE_RECEIPT_SOURCE")
        if receipt["entry_type"] not in entry_types:
            raise IntegrityError("E_CAS_QUARANTINE_RECEIPT_ENTRY_TYPE")
        if not HASH_RE.fullmatch(receipt["claimed_sha256"]):
            raise IntegrityError("E_CAS_QUARANTINE_RECEIPT_CLAIMED_DIGEST")
        if receipt["entry_type"] == "REGULAR_FILE":
            if not isinstance(receipt["actual_sha256"], str) or not HASH_RE.fullmatch(
                receipt["actual_sha256"]
            ):
                raise IntegrityError("E_CAS_QUARANTINE_RECEIPT_ACTUAL_DIGEST")
            if (
                not isinstance(receipt["actual_byte_length"], int)
                or isinstance(receipt["actual_byte_length"], bool)
                or receipt["actual_byte_length"] < 0
            ):
                raise IntegrityError("E_CAS_QUARANTINE_RECEIPT_ACTUAL_LENGTH")
        elif (
            receipt["actual_sha256"] is not None
            or receipt["actual_byte_length"] is not None
        ):
            raise IntegrityError("E_CAS_QUARANTINE_RECEIPT_NONREGULAR_ACTUAL")
        for key in ("original_path", "quarantine_path", "detected_at"):
            if not isinstance(receipt[key], str) or not receipt[key]:
                raise IntegrityError(f"E_CAS_QUARANTINE_RECEIPT_{key.upper()}")

    def _quarantine_corrupt_object(
        self,
        *,
        root: Path,
        target: Path,
        cas_class: str,
        slug: str,
        run_id: str,
        proposed_source_id: str,
        claimed_sha256: str,
        classification: tuple[str, str | None, int | None],
    ) -> dict[str, str]:
        """Move a corrupt claimed object and durably finalize its QAR receipt."""

        try:
            destination = self._quarantine_directory(root, claimed_sha256)
            quarantine_id = self._next_quarantine_id(destination)
            quarantine_path = destination / f"{quarantine_id}.object"
            receipt_path = destination / f"{quarantine_id}.json"
            pending_path = destination / f"{quarantine_id}.pending"
            receipt = self._quarantine_receipt(
                quarantine_id=quarantine_id,
                cas_class=cas_class,
                slug=slug,
                run_id=run_id,
                proposed_source_id=proposed_source_id,
                original_path=target,
                quarantine_path=quarantine_path,
                claimed_sha256=claimed_sha256,
                classification=classification,
                detected_at=_utc_now(),
            )
            self._validate_quarantine_receipt(receipt)
            receipt_bytes = canonical_json(receipt) + b"\n"
            cas_ops.write_exclusive(pending_path, receipt_bytes)
            _fsync_dir(destination)
            if classification[0] == "REGULAR_FILE":
                cas_ops.fsync_regular_nofollow(target)
            cas_ops.rename_noreplace(target, quarantine_path)
            if classification[0] == "REGULAR_FILE":
                cas_ops.fsync_regular_nofollow(quarantine_path)
            _fsync_dir(target.parent)
            _fsync_dir(destination)
            moved = self._classify_cas_entry(quarantine_path)
            if moved != classification:
                raise IntegrityError("E_CAS_QUARANTINE_OBJECT_CHANGED")
            cas_ops.rename_noreplace(pending_path, receipt_path)
            _fsync_dir(destination)
            readback = cas_ops.read_regular_nofollow(receipt_path)
            if readback != receipt_bytes:
                raise IntegrityError("E_CAS_QUARANTINE_RECEIPT_READBACK")
            return {
                "quarantine_id": quarantine_id,
                "receipt_path": receipt_path.relative_to(self.workspace).as_posix(),
                "receipt_sha256": sha256_bytes(readback),
            }
        except BaseException as exc:
            if isinstance(exc, (KeyboardInterrupt, SystemExit)):
                raise
            raise IntegrityError(f"E_CAS_QUARANTINE_FAILED: {exc}") from exc

    def _recover_quarantine_orphans(
        self, root: Path, claimed_sha256: str, original_path: Path
    ) -> list[str]:
        """Finish durable receipt publication after an interrupted quarantine."""

        destination = root.parent / "quarantine" / "sha256" / claimed_sha256
        if not destination.exists() and not destination.is_symlink():
            return []
        self._safe_directory(destination, create=False)
        recovered: list[str] = []
        pending_paths = sorted(destination.glob("QAR-[0-9][0-9][0-9][0-9][0-9][0-9].pending"))
        for pending_path in pending_paths:
            quarantine_id = pending_path.name.removesuffix(".pending")
            if not QAR_RE.fullmatch(quarantine_id):
                raise IntegrityError(f"E_CAS_QUARANTINE_ID: {pending_path}")
            quarantine_path = destination / f"{quarantine_id}.object"
            receipt_path = destination / f"{quarantine_id}.json"
            raw = cas_ops.read_regular_nofollow(pending_path)
            pending = _parse_json(raw, pending_path.as_posix())
            if raw != canonical_json(pending) + b"\n" or not isinstance(pending, dict):
                raise IntegrityError(f"E_CAS_QUARANTINE_PENDING: {pending_path}")
            self._validate_quarantine_receipt(pending)
            if (
                pending.get("quarantine_id") != quarantine_id
                or pending.get("claimed_sha256") != claimed_sha256
                or pending.get("original_path")
                != original_path.relative_to(self.workspace).as_posix()
                or pending.get("quarantine_path")
                != quarantine_path.relative_to(self.workspace).as_posix()
            ):
                raise IntegrityError(f"E_CAS_QUARANTINE_PENDING_BINDING: {pending_path}")

            if receipt_path.exists() or receipt_path.is_symlink():
                receipt_raw = cas_ops.read_regular_nofollow(receipt_path)
                if receipt_raw != canonical_json(pending) + b"\n":
                    raise IntegrityError(f"E_CAS_QUARANTINE_RECEIPT_CONFLICT: {receipt_path}")
                classification = self._classify_cas_entry(quarantine_path)
                if classification is None or classification != (
                    pending["entry_type"],
                    pending["actual_sha256"],
                    pending["actual_byte_length"],
                ):
                    raise IntegrityError(
                        f"E_CAS_QUARANTINE_RECEIPT_OBJECT_MISMATCH: {receipt_path}"
                    )
            else:
                classification = self._classify_cas_entry(quarantine_path)
                if classification is None:
                    classification = self._classify_cas_entry(original_path)
                    if classification is None:
                        raise IntegrityError(
                            f"E_CAS_QUARANTINE_ORPHAN: {quarantine_id}"
                        )
                    if (
                        classification[0] == "REGULAR_FILE"
                        and classification[1] == claimed_sha256
                    ):
                        raise IntegrityError(
                            f"E_CAS_QUARANTINE_STALE_INTENT: {quarantine_id}"
                        )
                    if classification[0] == "REGULAR_FILE":
                        cas_ops.fsync_regular_nofollow(original_path)
                    cas_ops.rename_noreplace(original_path, quarantine_path)
                    _fsync_dir(original_path.parent)
                    _fsync_dir(destination)
                    classification = self._classify_cas_entry(quarantine_path)
                assert classification is not None
                if classification[0] == "REGULAR_FILE":
                    cas_ops.fsync_regular_nofollow(quarantine_path)
                _fsync_dir(destination)
                pending["entry_type"] = classification[0]
                pending["actual_sha256"] = classification[1]
                pending["actual_byte_length"] = classification[2]
                self._validate_quarantine_receipt(pending)
                receipt_raw = canonical_json(pending) + b"\n"
                cas_ops.write_exclusive(receipt_path, receipt_raw)
                _fsync_dir(destination)
            pending_stat = pending_path.lstat()
            if stat.S_ISLNK(pending_stat.st_mode) or not stat.S_ISREG(pending_stat.st_mode):
                raise IntegrityError(f"E_CAS_QUARANTINE_PENDING_TYPE: {pending_path}")
            pending_path.unlink()
            _fsync_dir(destination)
            recovered.append(quarantine_id)

        for quarantine_path in destination.glob(
            "QAR-[0-9][0-9][0-9][0-9][0-9][0-9].object"
        ):
            quarantine_id = quarantine_path.name.removesuffix(".object")
            receipt_path = destination / f"{quarantine_id}.json"
            pending_path = destination / f"{quarantine_id}.pending"
            if not receipt_path.exists() and not pending_path.exists():
                raise IntegrityError(f"E_CAS_QUARANTINE_ORPHAN: {quarantine_id}")
        return recovered

    def _resolved_cas_root(self, root: Path) -> Path:
        self._reject_symlink_components(root)
        try:
            resolved = root.resolve(strict=True)
            resolved.relative_to(self.workspace)
        except (OSError, ValueError) as exc:
            raise IntegrityError(f"E_CAS_ROOT_ESCAPE: {root}") from exc
        if resolved != root:
            raise IntegrityError(f"E_CAS_ROOT_RESOLUTION: {root}")
        return resolved

    def _hash_cas_object(self, root: Path, digest: str) -> tuple[str, int]:
        """Hash a CAS object through no-follow, directory-relative descriptors."""

        if not HASH_RE.fullmatch(digest):
            raise IntegrityError("E_CAS_DIGEST")
        root_resolved = self._resolved_cas_root(root)
        target = root / digest[:2] / digest
        try:
            target_stat = target.lstat()
        except OSError as exc:
            raise IntegrityError(f"E_CAS_OBJECT_LSTAT: {target}: {exc}") from exc
        if stat.S_ISLNK(target_stat.st_mode) or not stat.S_ISREG(target_stat.st_mode):
            raise IntegrityError(f"E_CAS_OBJECT_TYPE: {target}")
        try:
            target.resolve(strict=True).relative_to(root_resolved)
        except (OSError, ValueError) as exc:
            raise IntegrityError(f"E_CAS_PATH_ESCAPE: {target}") from exc

        directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        nofollow = getattr(os, "O_NOFOLLOW", 0)
        root_fd = shard_fd = object_fd = -1
        try:
            root_fd = os.open(root_resolved, directory_flags | nofollow)
            shard_fd = os.open(
                digest[:2], directory_flags | nofollow, dir_fd=root_fd
            )
            before = os.stat(digest, dir_fd=shard_fd, follow_symlinks=False)
            if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
                raise IntegrityError(f"E_CAS_OBJECT_TYPE: {target}")
            object_fd = os.open(digest, os.O_RDONLY | nofollow, dir_fd=shard_fd)
            opened = os.fstat(object_fd)
            if (
                opened.st_dev != before.st_dev
                or opened.st_ino != before.st_ino
                or not stat.S_ISREG(opened.st_mode)
            ):
                raise IntegrityError(f"E_CAS_OBJECT_RACE: {target}")
            result = hashlib.sha256()
            size = 0
            while block := os.read(object_fd, 1024 * 1024):
                result.update(block)
                size += len(block)
            return result.hexdigest(), size
        except ResearchError:
            raise
        except OSError as exc:
            raise IntegrityError(f"E_CAS_OBJECT_READ: {target}: {exc}") from exc
        finally:
            for descriptor in (object_fd, shard_fd, root_fd):
                if descriptor >= 0:
                    with contextlib.suppress(OSError):
                        os.close(descriptor)

    def _reject_symlink_components(self, path: Path) -> None:
        try:
            relative = path.relative_to(self.workspace)
        except ValueError as exc:
            raise IntegrityError(f"E_PATH_OUTSIDE_WORKSPACE: {path}") from exc
        current = self.workspace
        for component in relative.parts:
            current = current / component
            if not current.exists() and not current.is_symlink():
                continue
            mode = current.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise IntegrityError(f"E_PATH_SYMLINK: {current}")

    def _safe_directory(self, path: Path, *, create: bool) -> None:
        self._reject_symlink_components(path)
        if create:
            path.mkdir(parents=True, exist_ok=True)
        self._reject_symlink_components(path)
        try:
            resolved = path.resolve(strict=True)
            resolved.relative_to(self.workspace)
        except (OSError, ValueError) as exc:
            raise IntegrityError(f"E_PATH_OUTSIDE_WORKSPACE: {path}") from exc
        if resolved != path:
            raise IntegrityError(f"E_PATH_RESOLUTION: {path}")

    def _validate_path(
        self,
        path: Path,
        *,
        closing: bool,
        final: bool,
        check_validation: bool = True,
        check_publication: bool = True,
    ) -> ValidationReport:
        errors: list[str] = []
        warnings: list[str] = []
        slug, run_id = (path.parent.parent.name if final else path.parent.name), path.name
        phase: str | None = None
        request: dict[str, Any] | None = None
        records: dict[str, list[dict[str, Any]]] = {}
        records_valid = False
        try:
            request, _ = self._request(path)
            if request["slug"] != slug:
                raise IntegrityError("E_PATH_SLUG")
        except (ResearchError, OSError) as exc:
            errors.append(str(exc))
        try:
            phase = self._phase(path)
            event_ids = self._dossier_event_ids(slug)
            if len(event_ids) != len(set(event_ids)):
                raise IntegrityError("E_EVENT_ID_REUSE")
        except ResearchError as exc:
            errors.append(str(exc))
        try:
            phase_number = int(phase[1:]) if phase is not None else -1
            singleton_requirements = (
                (("provider-conformance", "preflight"), phase_number >= 1 or closing),
                (("context-manifest",), phase_number >= 3 or closing),
                (("plan",), phase_number >= 4 or closing),
                (("reconciliation",), phase_number >= 7 or closing),
            )
            for kinds, required in singleton_requirements:
                for kind in kinds:
                    value = self._singleton(path, kind, required=required)
                    if value is not None:
                        self._validate_singleton_context(path, kind, value)
            if phase_number >= 1 or closing:
                p1_events = [
                    event
                    for event in self._state(path, run_id)
                    if event.get("to_phase") == "P1"
                ]
                errors.extend(
                    validate_preflight_contract(
                        self.workspace,
                        path,
                        expected_run_id=run_id,
                        as_of_utc=(
                            p1_events[0]["occurred_at"]
                            if len(p1_events) == 1
                            else None
                        ),
                    )
                )
            if phase_number >= 3 or closing:
                errors.extend(
                    validate_context_manifest_contract(
                        self.workspace, path, expected_run_id=run_id
                    )
                )
            if phase_number >= 4 or closing:
                errors.extend(
                    validate_plan_contract(
                        self.workspace, path, expected_run_id=run_id
                    )
                )
            if phase_number >= 7 or closing:
                errors.extend(
                    validate_reconciliation_contract(
                        self.workspace, path, expected_run_id=run_id
                    )
                )
            validation_path = path / "validation.json"
            if validation_path.exists() or validation_path.is_symlink():
                validation = _read_json(validation_path)
                if not isinstance(validation, dict):
                    raise IntegrityError("E_VALIDATION_TYPE")
                self._validate_schema("validation", validation)
                expected_validation = self._validation_record(
                    path,
                    validated_at_utc=validation["validated_at_utc"],
                )
                if validation != expected_validation:
                    errors.append("E_VALIDATION_RECORD_MISMATCH")
                if validation["subject_files"] != expected_validation["subject_files"]:
                    errors.append("E_VALIDATION_SUBJECT_ACCOUNTING")
                if (
                    validation["environment"]["core_version"]
                    != expected_validation["environment"]["core_version"]
                    or validation["environment"]["schema_set_sha256"]
                    != expected_validation["environment"]["schema_set_sha256"]
                    or validation["environment"]["platform"]
                    != expected_validation["environment"]["platform"]
                ):
                    errors.append("E_VALIDATION_ENVIRONMENT_BINDING")
                errors.extend(
                    validate_success_state_contract(
                        self.workspace, path, expected_run_id=run_id
                    )
                )
            elif check_validation and (final or phase == "P9"):
                errors.append("E_SINGLETON_MISSING:validation")
        except (ResearchError, OSError) as exc:
            errors.append(str(exc))
        try:
            records = self._all_records(path)
            seen: set[str] = set()
            for kind, items in records.items():
                id_field, _ = KIND_IDS[kind]
                for item in items:
                    self._validate_schema(kind, item)
                    identifier = item[id_field]
                    if item.get("record_id") != identifier or item.get("run_id") != run_id:
                        raise IntegrityError(f"E_RECORD_IDENTITY: {identifier}")
                    if identifier in seen:
                        raise IntegrityError(f"E_ID_DUPLICATE: {identifier}")
                    seen.add(identifier)
                    self._validate_record_context(path, kind, item)
                    if kind == "source" and item["custody"]["mode"] in {
                        "TRACKED_CAS",
                        "LOCAL_ONLY_CAS",
                    }:
                        custody = item["custody"]
                        object_path = self.workspace / custody["object_path"]
                        expected_root = (
                            self.tracked_cas_root
                            if custody["mode"] == "TRACKED_CAS"
                            else self.local_cas_root
                        )
                        expected_path = expected_root / custody["sha256"][:2] / custody["sha256"]
                        if object_path != expected_path:
                            raise IntegrityError(
                                f"E_CAS_PATH_POLICY:{item['source_id']}"
                            )
                        digest, size = self._hash_cas_object(
                            expected_root, custody["sha256"]
                        )
                        if digest != custody["sha256"] or size != custody["byte_length"]:
                            raise IntegrityError(
                                f"E_CAS_SOURCE_MISMATCH:{item['source_id']}"
                            )
            source_ids = {item["source_id"] for item in records.get("source", [])}
            evidence_ids = {item["evidence_id"] for item in records["evidence"]}
            for items in records.values():
                for item in items:
                    if not set(item.get("source_refs", [])).issubset(source_ids):
                        raise IntegrityError(f"E_REFERENCE_SOURCE:{item['record_id']}")
                    if not set(item.get("evidence_refs", [])).issubset(evidence_ids):
                        raise IntegrityError(f"E_REFERENCE_EVIDENCE:{item['record_id']}")
            self._verification_packets(
                path, require_complete=phase_number >= 7 or closing
            )
            packet_ids = self._dossier_packet_ids(slug)
            if len(packet_ids) != len(set(packet_ids)):
                raise IntegrityError("E_VERIFICATION_PACKET_ID_REUSE")
            records_valid = True
        except (ResearchError, OSError) as exc:
            errors.append(str(exc))
        if request is not None and records_valid:
            limits = request["budget"]["limits"]
            if len(request["questions"]) > limits["atomic_questions"]:
                errors.append("E_BUDGET_ATOMIC_QUESTIONS")
            if len(records["question"]) > limits["atomic_questions"]:
                errors.append("E_BUDGET_ATOMIC_QUESTIONS")
            if len(records["query"]) > limits["discovery_queries"]:
                errors.append("E_BUDGET_DISCOVERY_QUERIES")
            admitted_sources = sum(
                item["admission"] in {"ADMITTED_EVIDENCE", "ADMITTED_CONTEXT"}
                for item in records.get("source", [])
            )
            if admitted_sources > limits["admitted_sources"]:
                errors.append("E_BUDGET_ADMITTED_SOURCES")
        if closing and request is not None and records_valid:
            errors.extend(self._closing_errors(path, request, records, run_id))
        manifest_digest: str | None = None
        if final:
            try:
                manifest_digest = self._verify_manifest(path)
                if check_publication:
                    self._verify_registry(slug, run_id, manifest_digest)
                    entries = self._registry_entries(slug)
                    if entries and entries[-1]["run_id"] == run_id:
                        expected = self._render_views(path)
                        for name in ("README.md", "synthesis.md", "handoff.md"):
                            if (self.research_root / slug / name).read_text(encoding="utf-8") != expected[name]:
                                raise IntegrityError(f"E_ROOT_VIEW: {name}")
            except (ResearchError, OSError) as exc:
                errors.append(str(exc))
        if request is not None and records_valid:
            try:
                expected_views = self._render_views(path)
                any_run_view = any((path / name).exists() for name in expected_views)
                if final or any_run_view:
                    for name, content in expected_views.items():
                        try:
                            if (path / name).read_text(encoding="utf-8") != content:
                                errors.append(f"E_RUN_VIEW:{name}")
                        except OSError as exc:
                            errors.append(f"E_RUN_VIEW:{name}:{exc}")
            except (ResearchError, OSError) as exc:
                errors.append(f"E_RENDER_VALIDATION:{exc}")
        return ValidationReport(
            not errors,
            slug,
            run_id,
            phase,
            final,
            path,
            tuple(sorted(set(errors))),
            tuple(sorted(set(warnings))),
            manifest_digest,
        )

    def _closing_errors(
        self,
        path: Path,
        request: dict[str, Any],
        records: dict[str, list[dict[str, Any]]],
        run_id: str,
    ) -> list[str]:
        errors: list[str] = []
        questions = {item["question_id"]: item for item in records["question"]}
        query_ids = {item["query_id"] for item in records["query"]}
        sources = {item["source_id"]: item for item in records.get("source", [])}
        claims = {item["claim_id"]: item for item in records["claim"]}
        evidence = {item["evidence_id"]: item for item in records["evidence"]}
        contradictions = {item["contradiction_id"]: item for item in records["contradiction"]}
        verifications = {item["verification_id"]: item for item in records["verification"]}
        request_question_ids = {item["question_id"] for item in request["questions"]}
        plan = self._singleton(path, "plan", required=True)
        assert plan is not None
        if request_question_ids != set(questions):
            errors.append("E_QUESTION_COVERAGE")
        for source in records.get("source", []):
            if not set(source["query_ids"]).issubset(query_ids):
                errors.append(f"E_REFERENCE_SOURCE_QUERY:{source['source_id']}")
            if source["admission"] == "PENDING":
                errors.append(f"E_SOURCE_ADMISSION_PENDING:{source['source_id']}")
            if (
                source["admission"] in {"ADMITTED_EVIDENCE", "ADMITTED_CONTEXT"}
                and source["source_class"]
                in request["source_policy"]["prohibited_classes"]
            ):
                errors.append(f"E_SOURCE_POLICY_PROHIBITED:{source['source_id']}")
        errors.extend(self._query_candidate_closure_errors(records))
        lane_by_id = {lane["lane_id"]: lane for lane in plan["lanes"]}
        for question_plan in plan["question_plans"]:
            question_id = question_plan["question_id"]
            for lane_kind, lane_ids, purposes in (
                (
                    "DIRECT",
                    question_plan["direct_lane_ids"],
                    {"DISCOVERY", "CORROBORATION"},
                ),
                ("CONTRARY", question_plan["contrary_lane_ids"], {"CHALLENGE"}),
            ):
                for lane_id in lane_ids:
                    lane = lane_by_id[lane_id]
                    if lane["kind"] != lane_kind or not any(
                        query["lane_id"] == lane_id
                        and question_id in query["question_ids"]
                        and query["purpose"] in purposes
                        and query["status"] == "EXECUTED"
                        for query in records["query"]
                    ):
                        errors.append(
                            f"E_{lane_kind}_LANE_QUESTION:{question_id}:{lane_id}"
                        )
        publishable: set[str] = set()
        for contradiction_id, contradiction in contradictions.items():
            claim = claims.get(contradiction["claim_id"])
            active = contradiction["lifecycle_status"] not in {
                "REJECTED",
                "SUPERSEDED",
                "ARCHIVED",
            }
            if active and (
                claim is None or contradiction_id not in claim["contradiction_ids"]
            ):
                errors.append(f"E_CONTRADICTION_BACKLINK:{contradiction_id}")
        for claim_id, claim in claims.items():
            if claim["status"] in {"REJECTED", "SUPERSEDED", "STALE"}:
                continue
            if (
                claim["lifecycle_status"] != "PROPOSED"
                or claim["readiness_status"] != "READY"
            ):
                errors.append(f"E_CLAIM_STATE:{claim_id}")
                continue
            if claim["supersedes"] or claim.get("superseded_claim_id") is not None:
                errors.append(f"E_NOT_IMPLEMENTED_CLAIM_SUPERSESSION:{claim_id}")
            if claim["claim_type"] != "SOURCE_FACT":
                errors.append(f"E_NOT_IMPLEMENTED_CLAIM_CLASS:{claim_id}")
            support_sources = {
                sources[evidence[evidence_id]["source_id"]]["source_class"]
                for evidence_id in claim["support_evidence_ids"]
                if evidence_id in evidence
                and evidence[evidence_id]["source_id"] in sources
            }
            required_source_classes = set(
                request["source_policy"]["required_classes"]
            )
            if not required_source_classes.issubset(support_sources):
                errors.append(f"E_SOURCE_POLICY_REQUIRED:{claim_id}")
            expected_evidence = set(claim["support_evidence_ids"])
            for contradiction_id in claim["contradiction_ids"]:
                contradiction = contradictions.get(contradiction_id)
                if contradiction is None:
                    errors.append(f"E_OPEN_CONTRADICTION:{claim_id}")
                    continue
                if contradiction["claim_id"] != claim_id:
                    errors.append(f"E_CONTRADICTION_CLAIM_EDGE:{contradiction_id}")
                expected_evidence.update(contradiction["evidence_ids"])
                if contradiction["status"] == "OPEN":
                    errors.append(f"E_OPEN_CONTRADICTION:{claim_id}")
            if set(claim["evidence_refs"]) != expected_evidence:
                errors.append(f"E_CLAIM_EVIDENCE_EDGE:{claim_id}")
            linked_verifications = [
                verification
                for verification in verifications.values()
                if verification["claim_id"] == claim_id
            ]
            valid_verification = bool(
                linked_verifications
                and linked_verifications[-1]["outcome"] == "PASS"
            )
            if not valid_verification:
                errors.append(f"E_G7_VERIFICATION:{claim_id}")
            else:
                publishable.add(claim_id)
            if request["risk_tier"] in {"MATERIAL", "CRITICAL"}:
                support_sources = [
                    sources.get(evidence[ev_id]["source_id"])
                    for ev_id in claim["support_evidence_ids"]
                    if ev_id in evidence
                ]
                support_sources = [item for item in support_sources if item is not None]
                publishers = {item["publisher"] for item in support_sources}
                source_digests = {
                    item["custody"].get("sha256") for item in support_sources
                }
                if len(publishers) < 2 or len(source_digests) < 2:
                    errors.append(f"E_G6_CORROBORATION:{claim_id}")
        if request["risk_tier"] == "MATERIAL":
            errors.append("E_NOT_IMPLEMENTED_MATERIAL_INDEPENDENCE")
        if request["risk_tier"] == "CRITICAL":
            errors.append("E_NOT_IMPLEMENTED_MATERIAL_INDEPENDENCE")
            errors.append("E_NOT_IMPLEMENTED_CRITICAL_SPECIALIST_REVIEW")
        if not records["synthesis"]:
            errors.append("E_SYNTHESIS_MISSING")
        for synthesis in records["synthesis"]:
            used = {
                claim_id
                for assertion in synthesis["assertions"]
                for claim_id in assertion["claim_ids"]
            }
            if not used.issubset(publishable):
                errors.append("E_SYNTHESIS_UNPUBLISHABLE_CLAIM")
            disposition_claims = {
                claim_id
                for disposition in synthesis["question_dispositions"]
                for claim_id in disposition["claim_ids"]
            }
            if not disposition_claims.issubset(publishable):
                errors.append("E_SYNTHESIS_DISPOSITION_UNPUBLISHABLE_CLAIM")
            for disposition in synthesis["question_dispositions"]:
                if any(
                    disposition["question_id"]
                    not in claims[claim_id]["question_ids"]
                    for claim_id in disposition["claim_ids"]
                    if claim_id in claims
                ):
                    errors.append("E_SYNTHESIS_CLAIM_QUESTION_EDGE")
            if synthesis["conclusion_status"] != "PROPOSED":
                errors.append("E_SYNTHESIS_AUTHORITY")
        if len(records["handoff"]) != 1:
            errors.append("E_HANDOFF_COUNT")
        elif records["handoff"][0]["run_id"] != run_id:
            errors.append("E_HANDOFF_RUN")
        else:
            if (
                records["handoff"][0]["lifecycle_status"] != "ACCEPTED"
                or records["handoff"][0]["readiness_status"] != "READY"
            ):
                errors.append("E_HANDOFF_STATE")
            errors.extend(
                self._handoff_errors(path, request, records, run_id, publishable)
            )
            if records["handoff"][0]["result"]["outcome"] != "READY_TO_SEAL":
                errors.append("E_HANDOFF_NOT_READY_TO_SEAL")
            if records["handoff"][0]["result"]["outcome"] == "READY_TO_SEAL" and errors:
                errors.append("E_HANDOFF_READY_TO_SEAL_INVALID")
        return errors

    @staticmethod
    def _query_candidate_closure_errors(
        records: dict[str, list[dict[str, Any]]],
    ) -> list[str]:
        """Bind every discovery candidate to its one authorized Source attempt."""

        errors: list[str] = []
        candidate_sources: dict[str, list[str]] = {}
        for source in records.get("source", []):
            for candidate_id in source["candidate_ids"]:
                candidate_sources.setdefault(candidate_id, []).append(
                    source["source_id"]
                )
        for query in records["query"]:
            for candidate in query.get("results", []):
                linked_sources = candidate_sources.get(candidate["candidate_id"], [])
                expected = 1 if candidate["disposition"] == "RETRIEVE" else 0
                if len(linked_sources) != expected:
                    errors.append(
                        f"E_QUERY_CANDIDATE_CLOSURE:{candidate['candidate_id']}:"
                        f"expected={expected}:actual={len(linked_sources)}"
                    )
        return errors

    def _handoff_errors(
        self,
        path: Path,
        request: dict[str, Any],
        records: dict[str, list[dict[str, Any]]],
        run_id: str,
        publishable: set[str],
    ) -> list[str]:
        """Cross-check caller-authored handoff summaries against canonical records."""

        errors: list[str] = []
        handoff = records["handoff"][0]

        expected_location = {
            "project_id": request["project_id"],
            "run_id": run_id,
            "slug": request["slug"],
        }
        location = handoff["location"]
        if any(location[key] != value for key, value in expected_location.items()):
            errors.append("E_HANDOFF_LOCATION_IDENTITY")
        if location["phase"] != "P9":
            errors.append("E_HANDOFF_LOCATION_PHASE")

        expected_authorities = {
            "confirming_authority_id": request["authority"]["confirming_authority_id"],
            "decision_authority_id": request["authority"]["decision_authority_id"],
            "escalation_owner_id": request["escalation_owner_id"],
            "phase_owner_id": request["authority"]["phase_owner_id"],
            "requester_id": request["authority"]["requester_id"],
        }
        if handoff["authorities"] != expected_authorities:
            errors.append("E_HANDOFF_AUTHORITIES")

        if len(records["synthesis"]) != 1:
            errors.append("E_SYNTHESIS_COUNT")
        if records["synthesis"]:
            synthesis = records["synthesis"][-1]
            synthesis_dispositions = {
                item["question_id"]: item["disposition"]
                for item in synthesis["question_dispositions"]
            }
            handoff_dispositions = {
                item["question_id"]: item["disposition"]
                for item in handoff["questions"]
            }
            requested = {item["question_id"] for item in request["questions"]}
            if (
                len(synthesis_dispositions) != len(synthesis["question_dispositions"])
                or len(handoff_dispositions) != len(handoff["questions"])
                or set(synthesis_dispositions) != requested
                or handoff_dispositions != synthesis_dispositions
            ):
                errors.append("E_HANDOFF_QUESTION_DISPOSITIONS")
            if synthesis["conclusion_status"] != "PROPOSED":
                errors.append("E_HANDOFF_CONCLUSION_STATUS")
            if (
                handoff["result"]["outcome"] == "READY_TO_SEAL"
                and synthesis["outcome"] != "READY"
            ):
                errors.append("E_HANDOFF_READY_TO_SEAL_SYNTHESIS")
        if handoff["conclusion_status"] != "PROPOSED":
            errors.append("E_HANDOFF_CONCLUSION_STATUS")

        def counts(values: list[str], vocabulary: tuple[str, ...]) -> dict[str, int]:
            result = {key: 0 for key in vocabulary}
            for value in values:
                result[value] += 1
            return result

        claim_items = records["claim"]
        contradiction_by_id = {
            item["contradiction_id"]: item for item in records["contradiction"]
        }
        verification_outcomes: dict[str, str] = {}
        for verification in records["verification"]:
            verification_outcomes[verification["claim_id"]] = verification["outcome"]
        dispute_values: list[str] = []
        for claim in claim_items:
            linked = [
                contradiction_by_id.get(identifier)
                for identifier in claim["contradiction_ids"]
            ]
            if any(item is None or item["status"] == "OPEN" for item in linked):
                dispute_values.append("OPEN")
            elif linked:
                dispute_values.append("RESOLVED")
            else:
                dispute_values.append("NONE")
        expected_claims = {
            "by_class": counts(
                [item["claim_type"] for item in claim_items],
                (
                    "SOURCE_FACT",
                    "STATIC_OBSERVATION",
                    "IMPORTED_EMPIRICAL_OBSERVATION",
                    "USER_OBSERVATION",
                    "INFERENCE",
                    "PROPOSAL",
                ),
            ),
            "by_dispute": counts(dispute_values, ("NONE", "OPEN", "RESOLVED")),
            "by_readiness": counts(
                [item["readiness_status"] for item in claim_items],
                ("NOT_READY", "READY", "STALE"),
            ),
            "by_verification": counts(
                [
                    verification_outcomes.get(item["claim_id"], "NOT_RUN")
                    for item in claim_items
                ],
                (
                    "NOT_RUN",
                    "PASS",
                    "FAIL",
                    "COULD_NOT_RUN",
                    "INFRA_FAILURE",
                    "NOT_APPLICABLE",
                ),
            ),
            "total": len(claim_items),
        }
        for field, expected in expected_claims.items():
            if handoff["claims"][field] != expected:
                errors.append(f"E_HANDOFF_CLAIM_{field.upper()}")
        expected_material = set(publishable)
        actual_material = [
            item["claim_id"] for item in handoff["claims"]["material_claims"]
        ]
        if len(actual_material) != len(set(actual_material)) or set(actual_material) != expected_material:
            errors.append("E_HANDOFF_MATERIAL_CLAIMS")

        source_items = records.get("source", [])
        expected_sources = {
            "by_admission": counts(
                [item["admission"] for item in source_items],
                (
                    "PENDING",
                    "ADMITTED_EVIDENCE",
                    "ADMITTED_CONTEXT",
                    "BIBLIOGRAPHY_ONLY",
                    "REJECTED",
                ),
            ),
            "by_custody": counts(
                [item["custody"]["mode"] for item in source_items],
                ("TRACKED_CAS", "LOCAL_ONLY_CAS", "EXTRACT_ONLY", "NONE"),
            ),
            "by_freshness": counts(
                [item["freshness"]["status"] for item in source_items],
                ("CURRENT", "AGING", "STALE", "UNKNOWN"),
            ),
            "by_retrieval": counts(
                [item["retrieval"]["status"] for item in source_items],
                (
                    "NOT_ATTEMPTED",
                    "RETRIEVED",
                    "PARTIAL",
                    "UNAVAILABLE",
                    "ACCESS_DENIED",
                    "ERROR",
                ),
            ),
            "total": len(source_items),
        }
        for field, expected in expected_sources.items():
            if handoff["sources"][field] != expected:
                errors.append(f"E_HANDOFF_SOURCE_{field.upper()}")

        open_contradictions = sum(
            item["status"] == "OPEN" for item in records["contradiction"]
        )
        resolved_contradictions = len(records["contradiction"]) - open_contradictions
        if handoff["contrary_evidence"]["open_count"] != open_contradictions:
            errors.append("E_HANDOFF_CONTRADICTION_OPEN_COUNT")
        if handoff["contrary_evidence"]["resolved_count"] != resolved_contradictions:
            errors.append("E_HANDOFF_CONTRADICTION_RESOLVED_COUNT")
        expected_contradiction_details = {
            item["contradiction_id"]: (item["status"], item["description"])
            for item in records["contradiction"]
        }
        actual_contradiction_details = {
            item["contradiction_id"]: (item["status"], item["scope"])
            for item in handoff["contrary_evidence"]["contradictions"]
        }
        if (
            len(actual_contradiction_details)
            != len(handoff["contrary_evidence"]["contradictions"])
            or actual_contradiction_details != expected_contradiction_details
        ):
            errors.append("E_HANDOFF_CONTRADICTION_DETAILS")

        canonical_evidence_ids = {
            item["evidence_id"] for item in records["evidence"]
        }
        handoff_checks = handoff["validation"]["checks"]
        check_names = [item["check"] for item in handoff_checks]
        if len(check_names) != len(set(check_names)):
            errors.append("E_HANDOFF_VALIDATION_CHECK_DUPLICATE")
        if any(
            not set(item["evidence_ids"]).issubset(canonical_evidence_ids)
            for item in handoff_checks
        ):
            errors.append("E_HANDOFF_VALIDATION_EVIDENCE")
        if handoff["result"]["outcome"] == "READY_TO_SEAL" and (
            any(item["status"] != "PASS" for item in handoff_checks)
            or handoff["validation"]["checks_not_run"]
        ):
            errors.append("E_HANDOFF_VALIDATION_NOT_PASS")

        custody_counts = expected_sources["by_custody"]
        if handoff["custody"]["by_mode"] != custody_counts:
            errors.append("E_HANDOFF_CUSTODY_COUNTS")
        if handoff["exclusions"] != request["scope"]["exclude"]:
            errors.append("E_HANDOFF_EXCLUSIONS")
        expected_budget = {
            "limits": request["budget"]["limits"],
            "overrides": request["budget"]["confirmed_overrides"],
            "profile": request["budget"]["profile"],
        }
        if handoff["budget"]["confirmed"] != expected_budget:
            errors.append("E_HANDOFF_BUDGET_CONFIRMED")
        actual_budget = handoff["budget"]["actual"]
        if actual_budget["atomic_questions"] != len(records["question"]):
            errors.append("E_HANDOFF_BUDGET_QUESTIONS")
        if actual_budget["discovery_queries"] != len(records["query"]):
            errors.append("E_HANDOFF_BUDGET_QUERIES")
        admitted_count = sum(
            item["admission"] in {"ADMITTED_EVIDENCE", "ADMITTED_CONTEXT"}
            for item in source_items
        )
        if actual_budget["admitted_sources"] != admitted_count:
            errors.append("E_HANDOFF_BUDGET_SOURCES")
        context = self._singleton(path, "context-manifest", required=True)
        plan = self._singleton(path, "plan", required=True)
        reconciliation = self._singleton(path, "reconciliation", required=True)
        assert context is not None and plan is not None and reconciliation is not None
        context_digest, _ = _file_hash(path / "context-manifest.json")
        expected_source_basis = {
            (
                request["request_id"],
                request["schema_version"],
                sha256_bytes(canonical_json(request)),
            ),
            (
                context["manifest_id"],
                context["schema_version"],
                context_digest,
            ),
        }
        expected_source_basis.update(
            (item["artifact_id"], item["version"], item["sha256"])
            for item in request["existing_refs"]
        )
        actual_source_basis = {
            (item["artifact_id"], item["version"], item["sha256"])
            for item in handoff["source_basis"]
        }
        if (
            len(actual_source_basis) != len(handoff["source_basis"])
            or actual_source_basis != expected_source_basis
        ):
            errors.append("E_HANDOFF_SOURCE_BASIS")
        expected_reconciled_actuals = {
            "aggregate_model_tokens": reconciliation["budget_use"][
                "model_tokens_or_bytes"
            ],
            "concurrent_workers_peak": reconciliation[
                "concurrent_workers_peak"
            ],
            "context_bytes": context["context_budget"]["used"],
            "elapsed_minutes": reconciliation["budget_use"]["elapsed_minutes"],
            "external_tool_calls": reconciliation["budget_use"]["tool_calls"],
            "research_lanes": len(plan["lanes"]),
            "retries": reconciliation["budget_use"]["retries"],
        }
        for field, expected in expected_reconciled_actuals.items():
            if actual_budget[field] != expected:
                errors.append(f"E_HANDOFF_BUDGET_{field.upper()}_ACCOUNTING")
        accepted_decisions = {
            item["decision_id"]
            for item in records["decision"]
            if item["status"] == "ACCEPTED"
        }
        if (
            set(handoff["decisions"]) != accepted_decisions
            or set(handoff["decision_refs"]) != accepted_decisions
        ):
            errors.append("E_HANDOFF_DECISION_ACCOUNTING")
        errors.extend(
            self._budget_limit_errors(
                request["budget"]["limits"], actual_budget
            )
        )
        return errors

    def _render_views(self, path: Path) -> dict[str, str]:
        request, digest = self._request(path)
        records = self._all_records(path)
        phase = self._phase(path)
        counts = "\n".join(
            f"- {kind}: {len(records[kind])}" for kind in sorted(records)
        )
        readme = (
            f"# Research run {path.name}\n\n"
            f"- Slug: `{request['slug']}`\n- Phase: `{phase}`\n"
            f"- Request: `{request['request_id']}`\n- Request SHA-256: `{digest}`\n\n"
            f"## Record counts\n\n{counts}\n"
        )
        synthesis = "# Research synthesis\n\nConclusion status remains `PROPOSED`.\n"
        for item in records["synthesis"]:
            synthesis += "\n    " + canonical_json(item).decode("utf-8") + "\n"
        handoff = (
            render_handoff_markdown(records["handoff"][-1])
            if records["handoff"]
            else "# Research handoff\n\nNo handoff record is present.\n"
        )
        output = {"README.md": readme, "handoff.md": handoff, "synthesis.md": synthesis}
        for source in records.get("source", []):
            output[f"source-sheets/{source['source_id']}-v001.md"] = (
                f"# Source {source['source_id']}\n\n    "
                + canonical_json(source).decode("utf-8")
                + "\n"
            )
        return output

    def _manifest_bytes(self, path: Path) -> bytes:
        lines: list[str] = []
        for item in sorted(path.rglob("*"), key=lambda p: p.relative_to(path).as_posix()):
            item_stat = item.lstat()
            if stat.S_ISLNK(item_stat.st_mode):
                raise IntegrityError(f"E_MANIFEST_SYMLINK: {item}")
            if stat.S_ISDIR(item_stat.st_mode):
                continue
            if not stat.S_ISREG(item_stat.st_mode):
                raise IntegrityError(f"E_MANIFEST_FILE_TYPE: {item}")
            if item.name == "MANIFEST.sha256":
                continue
            digest, _ = _file_hash(item)
            lines.append(f"{digest}  {item.relative_to(path).as_posix()}\n")
        return "".join(lines).encode("utf-8")

    def _verify_manifest(self, path: Path) -> str:
        manifest_path = path / "MANIFEST.sha256"
        try:
            raw = manifest_path.read_bytes()
        except OSError as exc:
            raise IntegrityError(f"E_MANIFEST_READ: {exc}") from exc
        if raw != self._manifest_bytes(path):
            raise IntegrityError("E_MANIFEST_MISMATCH")
        return sha256_bytes(raw)

    def _registry_entries(self, slug: str) -> list[dict[str, Any]]:
        path = self._registry(slug)
        if not path.exists():
            return []
        entries = _read_lines(path)
        previous: str | None = None
        for index, entry in enumerate(entries, 1):
            self._validate_schema("registry", entry)
            base = {key: entry[key] for key in entry if key != "entry_sha256"}
            if (
                entry["sequence"] != index
                or entry["previous_entry_sha256"] != previous
                or entry["entry_sha256"] != sha256_bytes(canonical_json(base))
            ):
                raise IntegrityError(f"E_REGISTRY_CHAIN:{index}")
            previous = entry["entry_sha256"]
        return entries

    def _append_registry(self, slug: str, run_id: str, path: Path, manifest_digest: str) -> None:
        entries = self._registry_entries(slug)
        matching = [entry for entry in entries if entry["run_id"] == run_id]
        if matching:
            if len(matching) != 1 or matching[0]["manifest_sha256"] != manifest_digest:
                raise IntegrityError("E_REGISTRY_RUN_CONFLICT")
            return
        request, _ = self._request(path)
        handoffs = self._records(path, "handoff")
        # Successful completion is established only after atomic publication,
        # registry linkage, and readback. The canonical handoff stops at
        # READY_TO_SEAL and cannot predict this post-publication fact.
        outcome = "COMPLETE"
        lifecycle = "ACCEPTED"
        base = {
            "canonical_path": path.relative_to(self.workspace).as_posix(),
            "lifecycle_status": lifecycle,
            "manifest_sha256": manifest_digest,
            "outcome": outcome,
            "previous_entry_sha256": entries[-1]["entry_sha256"] if entries else None,
            "readiness_status": "READY",
            "request_id": request["request_id"],
            "run_id": run_id,
            "schema_version": "research-registry-entry/v1",
            "sealed_at_utc": _utc_now(),
            "sequence": len(entries) + 1,
            "slug": slug,
            "stale_if": list(handoffs[-1].get("stale_if", [])),
            "supersedes_run_ids": (
                [request["parent_run_id"]]
                if request.get("parent_run_id") is not None
                else []
            ),
        }
        entry = dict(base)
        entry["entry_sha256"] = sha256_bytes(canonical_json(base))
        self._validate_schema("registry", entry)
        # Publish the logical append as one atomic old-or-new registry image.
        # A process interruption can therefore expose the prior valid chain or
        # the complete appended chain, never a truncated COMPLETE tail.
        registry_bytes = b"".join(
            canonical_json(existing) + b"\n" for existing in entries
        )
        registry_bytes += canonical_json(entry) + b"\n"
        _atomic(self._registry(slug), registry_bytes)
        readback = self._registry_entries(slug)
        if len(readback) != len(entries) + 1 or readback[-1] != entry:
            raise IntegrityError("E_REGISTRY_APPEND_READBACK")

    def _verify_registry(self, slug: str, run_id: str, manifest_digest: str) -> None:
        matches = [entry for entry in self._registry_entries(slug) if entry["run_id"] == run_id]
        if len(matches) != 1 or matches[0]["manifest_sha256"] != manifest_digest:
            raise IntegrityError("E_REGISTRY_LINK")

    def _finish_publication(self, slug: str, run_id: str, final: Path) -> None:
        manifest_digest = self._verify_manifest(final)
        request, _ = self._request(final)
        self._assert_write_fence(
            request,
            [
                self._registry(slug).relative_to(self.workspace).as_posix(),
                f"docs/research/{slug}/README.md",
                f"docs/research/{slug}/synthesis.md",
                f"docs/research/{slug}/handoff.md",
                f".devforgeai/research-locks/{slug}.lock",
            ],
        )
        entries = self._registry_entries(slug)
        matching = [entry for entry in entries if entry["run_id"] == run_id]
        if matching and (
            len(matching) != 1
            or matching[0]["manifest_sha256"] != manifest_digest
        ):
            raise IntegrityError("E_REGISTRY_RUN_CONFLICT")

        # Re-sealing an older immutable run must not replace the current root
        # views.  Its already-linked registry entry is sufficient.
        if matching and entries[-1]["run_id"] != run_id:
            return

        views = self._render_views(final)
        root = self.research_root / slug
        self._safe_directory(root, create=True)
        for name in ("README.md", "synthesis.md", "handoff.md"):
            _atomic(root / name, views[name].encode("utf-8"))

        # COMPLETE must not become observable in the registry until every
        # required root view exists and has been read back byte-for-byte.  A
        # crash before this point leaves no registry entry and is safely
        # repeatable; a crash after append finds the one matching entry and
        # completes the registry-inclusive readback in seal_run.
        for name in ("README.md", "synthesis.md", "handoff.md"):
            try:
                actual = (root / name).read_bytes()
            except OSError as exc:
                raise IntegrityError(f"E_ROOT_VIEW_READBACK:{name}:{exc}") from exc
            if actual != views[name].encode("utf-8"):
                raise IntegrityError(f"E_ROOT_VIEW_READBACK:{name}")

        if not matching:
            self._append_registry(slug, run_id, final, manifest_digest)

    @staticmethod
    def _remove_tree(path: Path) -> None:
        if not path.exists():
            return
        for item in sorted(path.rglob("*"), key=lambda p: len(p.parts), reverse=True):
            if item.is_dir() and not item.is_symlink():
                item.rmdir()
            else:
                item.unlink()
        path.rmdir()
