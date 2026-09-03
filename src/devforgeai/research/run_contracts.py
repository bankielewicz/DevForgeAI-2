"""Deterministic semantic checks for the singleton Research run contracts.

The JSON Schemas close each record's shape.  This module closes the relations
between records and the exact files they name.  It intentionally has no import
from :mod:`devforgeai.research.core`, so ``ResearchStore`` can call it without a
circular dependency.

Every public validator returns ordered, stable error strings.  Paths are
explicit, all referenced hashes are hashes of exact file bytes, and no provider
runtime is invoked or inferred by these checks.
"""

from __future__ import annotations

import hashlib
import json
import stat
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


PHASES = tuple(f"P{number}" for number in range(10))
LEGAL_TRANSITIONS: dict[str | None, frozenset[str]] = {
    None: frozenset({"P0"}),
    "P0": frozenset({"P1"}),
    "P1": frozenset({"P2"}),
    "P2": frozenset({"P3"}),
    "P3": frozenset({"P4"}),
    "P4": frozenset({"P5"}),
    "P5": frozenset({"P6"}),
    "P6": frozenset({"P4", "P5", "P7"}),
    "P7": frozenset({"P5", "P6", "P8"}),
    "P8": frozenset({"P9"}),
    "P9": frozenset(),
}

REQUIRED_PREFLIGHT_CAPABILITIES = frozenset(
    {
        "SOURCE_OPEN",
        "FRESH_ISOLATED_WORKERS",
        "READ_ONLY_WORKER_FENCE",
        "RESEARCH_CORE",
        "SELECTED_CAS",
        "DOSSIER_WRITER_LOCK",
    }
)

PREFLIGHT_ATTESTATION_CAPABILITY_MAP = {
    "SOURCE_OPEN": "SOURCE_OPEN",
    "FRESH_ISOLATED_WORKERS": "FRESH_ISOLATED_WORKER",
    "READ_ONLY_WORKER_FENCE": "READ_ONLY_WORKER_FENCE",
}

PREFLIGHT_LOCAL_CAPABILITIES = frozenset(
    {"RESEARCH_CORE", "SELECTED_CAS", "DOSSIER_WRITER_LOCK"}
)

PROVIDER_RUNTIME_REQUIRED_CAPABILITIES = frozenset(
    {
        "SKILL_INVOCATION",
        "SUBAGENT_DELEGATION",
        "FRESH_ISOLATED_WORKER",
        "READ_ONLY_WORKER_FENCE",
        "SOURCE_OPEN",
        "NETWORK_POLICY_ENFORCEMENT",
        "ADAPTER_OPERATION_MAPPING",
        "RESEARCH_CORE",
        "SCHEMA_VALIDATION",
        "CONTENT_ADDRESSED_STORAGE",
        "DOSSIER_WRITER_LOCK",
        "ATOMIC_PUBLICATION",
        "DETERMINISTIC_RENDER",
    }
)

OFFLINE_REQUIRED_CAPABILITIES = frozenset(
    {
        "FRESH_ISOLATED_WORKER",
        "READ_ONLY_WORKER_FENCE",
        "SOURCE_OPEN",
        "RESEARCH_CORE",
        "CONTENT_ADDRESSED_STORAGE",
        "DOSSIER_WRITER_LOCK",
    }
)

PROVIDER_RUNTIME_FIXTURE_IDS = (
    "request-file-normalization-and-input-rejection",
    "confirmation-before-search-or-write",
    "implicit-request-no-persistence",
    "writer-collision",
    "snippet-evidence-rejection",
    "static-code-runtime-proof-rejection",
    "user-observation-universalization-rejection",
    "material-corroboration-and-source-independence",
    "contrary-primary-and-negative-claim-bounds",
    "prompt-injection-source-content",
    "out-of-scope-executable-or-provider-proof",
    "capability-unavailable-versus-dependency-loss",
    "retry-and-budget-exhaustion",
    "verified-claim-mutation",
    "cas-collision-and-size-thresholds",
    "sealed-byte-mutation-and-stale-view",
    "open-critical-dispute",
    "cold-session-reconstruction",
    "provider-attestation-absence-and-staleness",
    "missing-or-unsupported-hook",
)

OFFLINE_FIXTURE_IDS = ("offline-core-acceptance",)

PROVIDER_RUNTIME_FIXTURE_SUITE = {
    "schema_version": "provider-conformance-fixture-suite/v1",
    "suite_id": "devforgeai-research-provider-runtime",
    "suite_version": "1.0.0",
    "manifest_sha256": (
        "ff76986b52a46adb438a721770251465883b1d5cad3ceb1ae842bd968bfdc2c4"
    ),
    "required_fixture_ids": list(PROVIDER_RUNTIME_FIXTURE_IDS),
}

OFFLINE_FIXTURE_SUITE = {
    "schema_version": "provider-conformance-fixture-suite/v1",
    "suite_id": "devforgeai-research-offline-core",
    "suite_version": "1.0.0",
    "manifest_sha256": (
        "a1d149d6fccb6721e9d4fb4532465f193fd3d98d28642ad3553e2bdd7ac9a65a"
    ),
    "required_fixture_ids": list(OFFLINE_FIXTURE_IDS),
}

VALIDATION_CHECK_IDS = frozenset(
    {
        "RUN_BINDING",
        "REQUEST_BINDING",
        "PREFLIGHT",
        "STATE_CHAIN",
        "CONTEXT_MANIFEST",
        "PLAN",
        "ID_UNIQUENESS",
        "REFERENTIAL_INTEGRITY",
        "CLAIM_DAG",
        "CLAIM_CLASS_CONTRACT",
        "VERIFICATION_FRESHNESS",
        "RISK_CORROBORATION",
        "CONTRARY_COVERAGE",
        "QUERY_CANDIDATE_ACCOUNTING",
        "WORKER_ACCOUNTING",
        "RECONCILIATION",
        "SOURCE_ADMISSION",
        "EVIDENCE_EDGES",
        "DISPUTE_OWNERSHIP",
        "STALE_EXCLUSION",
        "DECISION_AUTHORITY",
        "CAS_INTEGRITY",
        "BUDGET",
        "DETERMINISTIC_RENDER",
        "HANDOFF_SHAPE",
    }
)

USAGE_LIMIT_FIELDS = {
    "queries": "discovery_queries",
    "sources": "admitted_sources",
    "tool_calls": "external_tool_calls",
    "model_tokens_or_bytes": "aggregate_model_tokens",
    "elapsed_minutes": "elapsed_minutes",
}


class _Errors:
    """Insertion-ordered error set."""

    def __init__(self) -> None:
        self._values: list[str] = []
        self._seen: set[str] = set()

    def add(self, code: str, detail: str | None = None) -> None:
        value = code if detail is None else f"{code}:{detail}"
        if value not in self._seen:
            self._seen.add(value)
            self._values.append(value)

    def extend(self, values: Sequence[str]) -> None:
        for value in values:
            if value not in self._seen:
                self._seen.add(value)
                self._values.append(value)

    def list(self) -> list[str]:
        return list(self._values)


def _key_order(value: str) -> bytes:
    return value.encode("utf-16-be", "surrogatepass")


def _canonical_encode(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False, allow_nan=False)
    if isinstance(value, list):
        return "[" + ",".join(_canonical_encode(item) for item in value) + "]"
    if isinstance(value, dict):
        keys = sorted(value, key=_key_order)
        return "{" + ",".join(
            _canonical_encode(key) + ":" + _canonical_encode(value[key])
            for key in keys
        ) + "}"
    raise TypeError(f"unsupported canonical JSON type: {type(value).__name__}")


def canonical_json_sha256(value: Mapping[str, Any]) -> str:
    """Return the Research canonical-JSON digest for an object."""

    return hashlib.sha256(_canonical_encode(dict(value)).encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    length = 0
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
            length += len(block)
    return digest.hexdigest(), length


def _relative_label(path: Path, workspace: Path) -> str:
    try:
        return path.relative_to(workspace).as_posix()
    except ValueError:
        return path.as_posix()


def _inside(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
    except ValueError:
        return False
    return True


def _normalize_roots(
    workspace: str | Path, run_path: str | Path, errors: _Errors
) -> tuple[Path, Path]:
    workspace_path = Path(workspace).expanduser().resolve()
    candidate = Path(run_path).expanduser()
    if not candidate.is_absolute():
        candidate = workspace_path / candidate
    resolved_run = candidate.resolve()
    if not workspace_path.is_dir():
        errors.add("E_CONTRACT_WORKSPACE")
    if not _inside(resolved_run, workspace_path):
        errors.add("E_CONTRACT_RUN_ESCAPE")
    if not resolved_run.is_dir():
        errors.add("E_CONTRACT_RUN_DIRECTORY")
    return workspace_path, resolved_run


def _has_symlink_component(path: Path, base: Path) -> bool:
    try:
        relative = path.relative_to(base)
    except ValueError:
        return True
    cursor = base
    for part in relative.parts:
        cursor = cursor / part
        try:
            if stat.S_ISLNK(cursor.lstat().st_mode):
                return True
        except FileNotFoundError:
            return False
    return False


def _workspace_ref(
    workspace: Path, value: Any, errors: _Errors, code: str
) -> Path | None:
    if not isinstance(value, str) or not value:
        errors.add(code)
        return None
    pure = PurePosixPath(value)
    if pure.is_absolute() or ".." in pure.parts or "\\" in value:
        errors.add(code, value)
        return None
    candidate = workspace.joinpath(*pure.parts)
    resolved = candidate.resolve()
    if not _inside(resolved, workspace) or _has_symlink_component(candidate, workspace):
        errors.add(code, value)
        return None
    return candidate


def _run_ref(run_path: Path, value: Any, errors: _Errors, code: str) -> Path | None:
    if not isinstance(value, str) or not value:
        errors.add(code)
        return None
    pure = PurePosixPath(value)
    if pure.is_absolute() or ".." in pure.parts or "\\" in value:
        errors.add(code, value)
        return None
    candidate = run_path.joinpath(*pure.parts)
    resolved = candidate.resolve()
    if not _inside(resolved, run_path) or _has_symlink_component(candidate, run_path):
        errors.add(code, value)
        return None
    return candidate


def _read_object(path: Path, workspace: Path, errors: _Errors) -> dict[str, Any] | None:
    label = _relative_label(path, workspace)
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError:
        errors.add("E_CONTRACT_FILE_MISSING", label)
        return None
    except OSError:
        errors.add("E_CONTRACT_FILE_READ", label)
        return None
    if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
        errors.add("E_CONTRACT_FILE_TYPE", label)
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        errors.add("E_CONTRACT_FILE_JSON", label)
        return None
    if not isinstance(value, dict):
        errors.add("E_CONTRACT_FILE_OBJECT", label)
        return None
    return value


def _read_jsonl(path: Path, workspace: Path, errors: _Errors) -> list[dict[str, Any]]:
    label = _relative_label(path, workspace)
    try:
        mode = path.lstat().st_mode
        raw_lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        errors.add("E_CONTRACT_FILE_MISSING", label)
        return []
    except (OSError, UnicodeError):
        errors.add("E_CONTRACT_FILE_READ", label)
        return []
    if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
        errors.add("E_CONTRACT_FILE_TYPE", label)
        return []
    records: list[dict[str, Any]] = []
    for number, line in enumerate(raw_lines, 1):
        if not line:
            errors.add("E_STATE_EMPTY_LINE", str(number))
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            errors.add("E_STATE_JSON", str(number))
            continue
        if not isinstance(value, dict):
            errors.add("E_STATE_OBJECT", str(number))
            continue
        records.append(value)
    return records


def _parse_utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.endswith("Z"):
        return None
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _check_exact_file(
    path: Path | None,
    expected_sha256: Any,
    errors: _Errors,
    code: str,
    *,
    expected_length: Any | None = None,
) -> None:
    if path is None:
        return
    label = path.as_posix()
    try:
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
            errors.add(f"{code}_FILE_TYPE", label)
            return
        actual_digest, actual_length = _sha256_file(path)
    except OSError:
        errors.add(f"{code}_FILE_MISSING", label)
        return
    if actual_digest != expected_sha256:
        errors.add(f"{code}_DIGEST", label)
    if expected_length is not None and actual_length != expected_length:
        errors.add(f"{code}_LENGTH", label)


def _request_digest(request: Mapping[str, Any]) -> str | None:
    try:
        return canonical_json_sha256(request)
    except (TypeError, ValueError):
        return None


def _deduplicated(values: Sequence[str]) -> bool:
    try:
        return len(values) == len(set(values))
    except TypeError:
        return False


def validate_provider_conformance_semantics(
    attestation: Mapping[str, Any],
) -> list[str]:
    """Close provider-trial and required-capability relations not expressible tersely in JSON Schema."""

    errors = _Errors()
    subject = attestation.get("attestation_subject", {})
    provider_kind = subject.get("provider_kind") if isinstance(subject, Mapping) else None
    expected_suite = (
        PROVIDER_RUNTIME_FIXTURE_SUITE
        if provider_kind in {"CLAUDE_CODE", "CODEX"}
        else OFFLINE_FIXTURE_SUITE
        if provider_kind == "OFFLINE_TEST_HARNESS"
        else None
    )
    fixture_suite = attestation.get("fixture_suite")
    if expected_suite is None or fixture_suite != expected_suite:
        errors.add("E_PROVIDER_FIXTURE_SUITE_BINDING")
    if isinstance(fixture_suite, Mapping):
        manifest = {
            key: value
            for key, value in fixture_suite.items()
            if key != "manifest_sha256"
        }
        try:
            manifest_digest = canonical_json_sha256(manifest)
        except (TypeError, ValueError):
            manifest_digest = None
        if manifest_digest != fixture_suite.get("manifest_sha256"):
            errors.add("E_PROVIDER_FIXTURE_SUITE_DIGEST")
    capabilities = [
        item
        for item in attestation.get("capabilities", [])
        if isinstance(item, Mapping)
    ]
    capability_ids = [item.get("capability_id") for item in capabilities]
    if len(capability_ids) != len(attestation.get("capabilities", [])):
        errors.add("E_PROVIDER_CAPABILITY_OBJECT")
    if any(not isinstance(value, str) or not value for value in capability_ids):
        errors.add("E_PROVIDER_CAPABILITY_ID")
    if not _deduplicated(capability_ids):
        errors.add("E_PROVIDER_CAPABILITY_DUPLICATE")
    capability_by_id = {
        item["capability_id"]: item
        for item in capabilities
        if isinstance(item.get("capability_id"), str)
    }

    if attestation.get("status") == "SUPPORTED":
        required_ids = (
            PROVIDER_RUNTIME_REQUIRED_CAPABILITIES
            if provider_kind in {"CLAUDE_CODE", "CODEX"}
            else OFFLINE_REQUIRED_CAPABILITIES
            if provider_kind == "OFFLINE_TEST_HARNESS"
            else frozenset()
        )
        for capability_id in sorted(required_ids):
            capability = capability_by_id.get(capability_id)
            if not isinstance(capability, Mapping):
                errors.add("E_PROVIDER_REQUIRED_CAPABILITY_MISSING", capability_id)
                continue
            if capability.get("required") is not True:
                errors.add("E_PROVIDER_REQUIRED_CAPABILITY_OPTIONAL", capability_id)
            if capability.get("status") != "SUPPORTED":
                errors.add("E_PROVIDER_REQUIRED_CAPABILITY_UNSUPPORTED", capability_id)
            evidence = capability.get("evidence")
            if not isinstance(evidence, list) or not evidence:
                errors.add("E_PROVIDER_REQUIRED_CAPABILITY_EVIDENCE", capability_id)

    trials = [
        item for item in attestation.get("trials", []) if isinstance(item, Mapping)
    ]
    if len(trials) != len(attestation.get("trials", [])):
        errors.add("E_PROVIDER_TRIAL_OBJECT")
    trial_ids = [item.get("trial_id") for item in trials]
    fixture_ids = [item.get("fixture_id") for item in trials]
    session_ids = [item.get("session_id") for item in trials]
    if not _deduplicated(trial_ids):
        errors.add("E_PROVIDER_TRIAL_ID_DUPLICATE")
    if any(not isinstance(value, str) or not value for value in fixture_ids):
        errors.add("E_PROVIDER_TRIAL_FIXTURE_ID")
    if not _deduplicated(session_ids):
        errors.add("E_PROVIDER_TRIAL_SESSION_DUPLICATE")

    issued = _parse_utc(attestation.get("issued_at_utc"))
    expires = _parse_utc(attestation.get("expires_at_utc"))
    if issued is None or expires is None or issued >= expires:
        errors.add("E_PROVIDER_ATTESTATION_TIME")
    for trial in trials:
        performed = _parse_utc(trial.get("performed_at_utc"))
        if (
            performed is None
            or issued is None
            or expires is None
            or not issued <= performed < expires
        ):
            errors.add("E_PROVIDER_TRIAL_TIME", str(trial.get("trial_id")))

    if attestation.get("status") == "SUPPORTED":
        if any(item.get("outcome") != "PASS" for item in trials):
            errors.add("E_PROVIDER_SUPPORTED_TRIAL_NOT_PASS")
        if provider_kind in {"CLAUDE_CODE", "CODEX"}:
            by_fixture: dict[str, list[Mapping[str, Any]]] = {}
            composition_valid = bool(trials)
            for trial in trials:
                fixture_id = trial.get("fixture_id")
                if not isinstance(fixture_id, str) or not fixture_id:
                    composition_valid = False
                    continue
                by_fixture.setdefault(fixture_id, []).append(trial)
            if set(by_fixture) != set(PROVIDER_RUNTIME_FIXTURE_IDS):
                errors.add("E_PROVIDER_TRIAL_FIXTURE_COVERAGE")
            for fixture_trials in by_fixture.values():
                enabled = sum(
                    item.get("baseline") == "ENABLED"
                    for item in fixture_trials
                )
                disabled = sum(
                    item.get("baseline") == "DISABLED"
                    for item in fixture_trials
                )
                if (
                    len(fixture_trials) != 10
                    or enabled != 5
                    or disabled != 5
                ):
                    composition_valid = False
            if not composition_valid:
                errors.add("E_PROVIDER_TRIAL_COMPOSITION")
        elif provider_kind == "OFFLINE_TEST_HARNESS":
            if len(trials) != 1 or any(
                item.get("baseline") != "NOT_APPLICABLE"
                or item.get("fixture_id") != OFFLINE_FIXTURE_IDS[0]
                for item in trials
            ):
                errors.add("E_PROVIDER_OFFLINE_TRIAL_COMPOSITION")
    return errors.list()


def validate_request_run_contract(
    workspace: str | Path,
    run_path: str | Path,
    *,
    expected_run_id: str | None = None,
) -> list[str]:
    """Validate the exact confirmed request and its run-header binding."""

    errors = _Errors()
    workspace_path, run = _normalize_roots(workspace, run_path, errors)
    request = _read_object(run / "request.json", workspace_path, errors)
    header = _read_object(run / "run.json", workspace_path, errors)
    if request is None or header is None:
        return errors.list()

    digest = _request_digest(request)
    run_id = expected_run_id or run.name
    if expected_run_id is not None and run.name != expected_run_id:
        errors.add("E_RUN_PATH_ID_BINDING")
    if header.get("run_id") != run_id:
        errors.add("E_RUN_ID_BINDING")
    if header.get("request_id") != request.get("request_id"):
        errors.add("E_RUN_REQUEST_ID_BINDING")
    if header.get("slug") != request.get("slug"):
        errors.add("E_RUN_SLUG_BINDING")

    binding = header.get("confirmation_binding")
    authority = request.get("authority")
    if not isinstance(binding, Mapping) or not isinstance(authority, Mapping):
        errors.add("E_RUN_CONFIRMATION_BINDING")
        return errors.list()
    if digest is None or binding.get("request_sha256") != digest:
        errors.add("E_RUN_REQUEST_DIGEST")
    if binding.get("confirming_authority") != authority.get("confirming_authority_id"):
        errors.add("E_RUN_CONFIRMING_AUTHORITY")
    work_order = authority.get("work_order_sha256")
    expected_method = "WORK_ORDER" if work_order is not None else "INTERACTIVE"
    if binding.get("method") != expected_method:
        errors.add("E_RUN_CONFIRMATION_METHOD")
    if binding.get("work_order_sha256") != work_order:
        errors.add("E_RUN_WORK_ORDER_BINDING")
    if _parse_utc(binding.get("confirmed_at")) is None:
        errors.add("E_RUN_CONFIRMATION_TIME")
    return errors.list()


def validate_preflight_contract(
    workspace: str | Path,
    run_path: str | Path,
    *,
    expected_run_id: str | None = None,
    as_of_utc: str | None = None,
) -> list[str]:
    """Validate the P0 request, run, attestation, and preflight singleton set.

    ``as_of_utc`` is an explicit deterministic freshness boundary.  When it is
    omitted, the recorded preflight time is used; no wall-clock lookup occurs.
    """

    errors = _Errors()
    workspace_path, run = _normalize_roots(workspace, run_path, errors)
    errors.extend(
        validate_request_run_contract(
            workspace_path, run, expected_run_id=expected_run_id
        )
    )
    request = _read_object(run / "request.json", workspace_path, errors)
    header = _read_object(run / "run.json", workspace_path, errors)
    preflight = _read_object(run / "preflight.json", workspace_path, errors)
    attestation = _read_object(
        run / "provider-conformance.json", workspace_path, errors
    )
    if None in (request, header, preflight, attestation):
        return errors.list()
    assert request is not None and header is not None
    assert preflight is not None and attestation is not None
    errors.extend(validate_provider_conformance_semantics(attestation))

    digest = _request_digest(request)
    run_id = expected_run_id or run.name
    if preflight.get("run_id") != run_id or preflight.get("preflight_id") != f"{run_id}/preflight":
        errors.add("E_PREFLIGHT_RUN_BINDING")
    if preflight.get("request_id") != request.get("request_id"):
        errors.add("E_PREFLIGHT_REQUEST_ID_BINDING")
    if digest is None or preflight.get("request_sha256") != digest:
        errors.add("E_PREFLIGHT_REQUEST_DIGEST")
    if preflight.get("request_sha256") != header.get("confirmation_binding", {}).get("request_sha256"):
        errors.add("E_PREFLIGHT_RUN_DIGEST_BINDING")

    subject = attestation.get("attestation_subject")
    if preflight.get("provider_subject") != subject:
        errors.add("E_PREFLIGHT_ATTESTATION_SUBJECT")
    reference = preflight.get("attestation")
    if not isinstance(reference, Mapping):
        errors.add("E_PREFLIGHT_ATTESTATION_REFERENCE")
    else:
        if reference.get("attestation_id") != attestation.get("attestation_id"):
            errors.add("E_PREFLIGHT_ATTESTATION_ID")
        if reference.get("status") != attestation.get("status"):
            errors.add("E_PREFLIGHT_ATTESTATION_STATUS")
        referenced_path = _run_ref(
            run,
            reference.get("path"),
            errors,
            "E_PREFLIGHT_ATTESTATION_PATH",
        )
        _check_exact_file(
            referenced_path,
            reference.get("sha256"),
            errors,
            "E_PREFLIGHT_ATTESTATION",
        )
        _check_exact_file(
            run / "provider-conformance.json",
            reference.get("sha256"),
            errors,
            "E_PREFLIGHT_RETAINED_ATTESTATION",
        )
        if referenced_path is not None and referenced_path.is_file():
            referenced = _read_object(referenced_path, workspace_path, errors)
            if referenced is not None and referenced != attestation:
                errors.add("E_PREFLIGHT_ATTESTATION_CONTENT")

    issued = _parse_utc(attestation.get("issued_at_utc"))
    expires = _parse_utc(attestation.get("expires_at_utc"))
    performed = _parse_utc(preflight.get("performed_at_utc"))
    freshness = _parse_utc(as_of_utc) if as_of_utc is not None else performed
    if None in (issued, expires, performed, freshness):
        errors.add("E_PREFLIGHT_ATTESTATION_TIME")
    else:
        assert issued is not None and expires is not None
        assert performed is not None and freshness is not None
        if not issued <= performed < expires:
            errors.add("E_PREFLIGHT_ATTESTATION_NOT_FRESH_AT_P0")
        if not issued <= freshness < expires:
            errors.add("E_PREFLIGHT_ATTESTATION_STALE")

    checks = preflight.get("capability_checks")
    if isinstance(checks, list):
        ids = [item.get("capability_id") for item in checks if isinstance(item, Mapping)]
        if not _deduplicated(ids):
            errors.add("E_PREFLIGHT_CAPABILITY_DUPLICATE")
        if not REQUIRED_PREFLIGHT_CAPABILITIES.issubset(set(ids)):
            errors.add("E_PREFLIGHT_CAPABILITY_MISSING")
        for item in checks:
            if (
                isinstance(item, Mapping)
                and item.get("capability_id") in REQUIRED_PREFLIGHT_CAPABILITIES
                and item.get("required") is not True
            ):
                errors.add(
                    "E_PREFLIGHT_CAPABILITY_NOT_REQUIRED",
                    str(item.get("capability_id")),
                )
        attestation_capabilities = attestation.get("capabilities")
        if not isinstance(attestation_capabilities, list):
            errors.add("E_PREFLIGHT_ATTESTATION_CAPABILITIES")
            attestation_capabilities = []
        attestation_ids = [
            item.get("capability_id")
            for item in attestation_capabilities
            if isinstance(item, Mapping)
        ]
        if not _deduplicated(attestation_ids):
            errors.add("E_PREFLIGHT_ATTESTATION_CAPABILITY_DUPLICATE")
        attestation_by_id = {
            item.get("capability_id"): item
            for item in attestation_capabilities
            if isinstance(item, Mapping)
        }
        for item in checks:
            if not isinstance(item, Mapping):
                continue
            capability_id = item.get("capability_id")
            expected_basis = (
                "ATTESTATION"
                if capability_id in PREFLIGHT_ATTESTATION_CAPABILITY_MAP
                else "DETERMINISTIC_LOCAL_CHECK"
                if capability_id in PREFLIGHT_LOCAL_CAPABILITIES
                else None
            )
            if expected_basis is not None and item.get("basis") != expected_basis:
                errors.add("E_PREFLIGHT_CAPABILITY_BASIS", str(capability_id))
            if capability_id not in PREFLIGHT_ATTESTATION_CAPABILITY_MAP:
                continue
            attestation_id = PREFLIGHT_ATTESTATION_CAPABILITY_MAP[capability_id]
            attested = attestation_by_id.get(attestation_id)
            if not isinstance(attested, Mapping):
                errors.add("E_PREFLIGHT_ATTESTED_CAPABILITY_MISSING", str(capability_id))
                continue
            if attested.get("required") is not True:
                errors.add("E_PREFLIGHT_ATTESTED_CAPABILITY_NOT_REQUIRED", str(capability_id))
            if item.get("status") != attested.get("status"):
                errors.add("E_PREFLIGHT_ATTESTED_CAPABILITY_STATUS", str(capability_id))
            expected_evidence = {
                evidence.get("artifact_id")
                for evidence in attested.get("evidence", [])
                if isinstance(evidence, Mapping)
            }
            actual_evidence = set(item.get("evidence_artifact_ids", []))
            if not expected_evidence or actual_evidence != expected_evidence:
                errors.add("E_PREFLIGHT_ATTESTED_CAPABILITY_EVIDENCE", str(capability_id))
        if preflight.get("gate", {}).get("status") == "PASS":
            for item in checks:
                if isinstance(item, Mapping) and item.get("required") is True and item.get("status") != "SUPPORTED":
                    errors.add("E_PREFLIGHT_REQUIRED_CAPABILITY", str(item.get("capability_id")))
    else:
        errors.add("E_PREFLIGHT_CAPABILITIES")
    if preflight.get("gate", {}).get("status") == "PASS":
        if attestation.get("status") != "SUPPORTED":
            errors.add("E_PREFLIGHT_UNSUPPORTED_ATTESTATION")
        if preflight.get("writer_lock", {}).get("status") != "AVAILABLE":
            errors.add("E_PREFLIGHT_WRITER_LOCK")
    return errors.list()


def validate_context_manifest_contract(
    workspace: str | Path,
    run_path: str | Path,
    *,
    expected_run_id: str | None = None,
) -> list[str]:
    """Validate selected context, request/existing-ref coverage, and byte budget."""

    errors = _Errors()
    workspace_path, run = _normalize_roots(workspace, run_path, errors)
    request = _read_object(run / "request.json", workspace_path, errors)
    header = _read_object(run / "run.json", workspace_path, errors)
    manifest = _read_object(run / "context-manifest.json", workspace_path, errors)
    if None in (request, header, manifest):
        return errors.list()
    assert request is not None and header is not None and manifest is not None
    digest = _request_digest(request)
    run_id = expected_run_id or run.name
    if manifest.get("run_id") != run_id or manifest.get("manifest_id") != f"{run_id}/context-manifest":
        errors.add("E_CONTEXT_RUN_BINDING")
    if manifest.get("request_id") != request.get("request_id"):
        errors.add("E_CONTEXT_REQUEST_ID_BINDING")
    if digest is None or manifest.get("request_sha256") != digest:
        errors.add("E_CONTEXT_REQUEST_DIGEST")
    if manifest.get("request_sha256") != header.get("confirmation_binding", {}).get("request_sha256"):
        errors.add("E_CONTEXT_RUN_DIGEST_BINDING")

    entries = manifest.get("entries")
    if not isinstance(entries, list):
        errors.add("E_CONTEXT_ENTRIES")
        return errors.list()
    entry_ids = [item.get("entry_id") for item in entries if isinstance(item, Mapping)]
    if len(entry_ids) != len(entries) or not _deduplicated(entry_ids):
        errors.add("E_CONTEXT_ENTRY_ID_DUPLICATE")

    selected_bytes = 0
    request_matches = 0
    index: dict[tuple[Any, Any], list[Mapping[str, Any]]] = {}
    for entry in entries:
        if not isinstance(entry, Mapping):
            errors.add("E_CONTEXT_ENTRY_OBJECT")
            continue
        key = (entry.get("artifact_kind"), entry.get("artifact_id"))
        index.setdefault(key, []).append(entry)
        if (
            entry.get("artifact_kind") == "REQUEST"
            and entry.get("artifact_id") == request.get("request_id")
        ):
            path = _run_ref(
                run, entry.get("path"), errors, "E_CONTEXT_ENTRY_PATH"
            )
        else:
            path = _workspace_ref(
                workspace_path,
                entry.get("path"),
                errors,
                "E_CONTEXT_ENTRY_PATH",
            )
        if entry.get("resolution_status") == "RESOLVED":
            _check_exact_file(
                path,
                entry.get("sha256"),
                errors,
                "E_CONTEXT_ENTRY",
                expected_length=entry.get("serialized_bytes"),
            )
        if entry.get("selection") == "SELECTED":
            value = entry.get("serialized_bytes")
            if isinstance(value, int) and not isinstance(value, bool):
                selected_bytes += value
            else:
                errors.add("E_CONTEXT_ENTRY_BYTES", str(entry.get("entry_id")))
        if (
            entry.get("artifact_kind") == "REQUEST"
            and entry.get("artifact_id") == request.get("request_id")
            and entry.get("version") == request.get("schema_version")
            and entry.get("selection") == "SELECTED"
            and entry.get("resolution_status") == "RESOLVED"
        ):
            request_matches += 1
    if request_matches != 1:
        errors.add("E_CONTEXT_REQUEST_ENTRY_COUNT")

    for existing in request.get("existing_refs", []):
        if not isinstance(existing, Mapping):
            errors.add("E_CONTEXT_EXISTING_REF_OBJECT")
            continue
        matches = index.get((existing.get("kind"), existing.get("artifact_id")), [])
        if len(matches) != 1:
            errors.add("E_CONTEXT_EXISTING_REF_COUNT", str(existing.get("artifact_id")))
            continue
        entry = matches[0]
        if entry.get("version") != existing.get("version"):
            errors.add("E_CONTEXT_EXISTING_REF_VERSION", str(existing.get("artifact_id")))
        if entry.get("sha256") != existing.get("sha256"):
            errors.add("E_CONTEXT_EXISTING_REF_DIGEST", str(existing.get("artifact_id")))

    budget = manifest.get("context_budget")
    request_context_limit = request.get("budget", {}).get("limits", {}).get(
        "context_bytes"
    )
    if not isinstance(budget, Mapping):
        errors.add("E_CONTEXT_BUDGET")
    else:
        if budget.get("limit") != request_context_limit:
            errors.add("E_CONTEXT_BUDGET_BINDING")
        if budget.get("used") != selected_bytes:
            errors.add("E_CONTEXT_BUDGET_ACCOUNTING")
        limit = budget.get("limit")
        if not isinstance(limit, int) or isinstance(limit, bool) or selected_bytes > limit:
            errors.add("E_CONTEXT_BUDGET_EXCEEDED")
        confirmed_limit = request.get("budget", {}).get("limits", {}).get("context_bytes")
        if limit != confirmed_limit:
            errors.add("E_CONTEXT_BUDGET_BINDING")
    return errors.list()


def _budget_overages(usage: Mapping[str, Any], limits: Mapping[str, Any]) -> list[str]:
    overages: list[str] = []
    for usage_field, limit_field in USAGE_LIMIT_FIELDS.items():
        used = usage.get(usage_field)
        limit = limits.get(limit_field)
        if not isinstance(used, int) or isinstance(used, bool) or not isinstance(limit, int) or used > limit:
            overages.append(usage_field)
    return overages


def _has_dependency_cycle(envelopes: Sequence[Mapping[str, Any]]) -> bool:
    graph = {
        str(item.get("task_id")): tuple(str(dep) for dep in item.get("dependencies", []))
        for item in envelopes
    }
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        if any(visit(dependency) for dependency in graph.get(node, ())):
            return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in graph)


def validate_plan_contract(
    workspace: str | Path,
    run_path: str | Path,
    *,
    expected_run_id: str | None = None,
) -> list[str]:
    """Validate the P3 request/context bindings and closed delegation graph."""

    errors = _Errors()
    workspace_path, run = _normalize_roots(workspace, run_path, errors)
    request = _read_object(run / "request.json", workspace_path, errors)
    header = _read_object(run / "run.json", workspace_path, errors)
    manifest = _read_object(run / "context-manifest.json", workspace_path, errors)
    plan = _read_object(run / "plan.json", workspace_path, errors)
    if None in (request, header, manifest, plan):
        return errors.list()
    assert request is not None and header is not None
    assert manifest is not None and plan is not None
    digest = _request_digest(request)
    run_id = expected_run_id or run.name
    if plan.get("run_id") != run_id or plan.get("plan_id") != f"{run_id}/plan":
        errors.add("E_PLAN_RUN_BINDING")
    if plan.get("request_id") != request.get("request_id"):
        errors.add("E_PLAN_REQUEST_ID_BINDING")
    if digest is None or plan.get("request_sha256") != digest:
        errors.add("E_PLAN_REQUEST_DIGEST")
    if plan.get("request_sha256") != header.get("confirmation_binding", {}).get("request_sha256"):
        errors.add("E_PLAN_RUN_DIGEST_BINDING")
    context_ref = plan.get("context_manifest")
    if not isinstance(context_ref, Mapping):
        errors.add("E_PLAN_CONTEXT_REFERENCE")
    else:
        if context_ref.get("manifest_id") != manifest.get("manifest_id"):
            errors.add("E_PLAN_CONTEXT_ID_BINDING")
        _check_exact_file(
            run / "context-manifest.json",
            context_ref.get("sha256"),
            errors,
            "E_PLAN_CONTEXT",
        )
    if plan.get("risk_tier") != request.get("risk_tier"):
        errors.add("E_PLAN_RISK_BINDING")
    authority = request.get("authority", {})
    if plan.get("decision_authority") != authority.get("decision_authority_id"):
        errors.add("E_PLAN_DECISION_AUTHORITY_BINDING")

    question_plans = plan.get("question_plans")
    lanes = plan.get("lanes")
    envelopes = plan.get("worker_envelopes")
    barriers = plan.get("barriers")
    if not all(isinstance(value, list) for value in (question_plans, lanes, envelopes, barriers)):
        errors.add("E_PLAN_COLLECTIONS")
        return errors.list()
    question_plans = [item for item in question_plans if isinstance(item, Mapping)]
    lanes = [item for item in lanes if isinstance(item, Mapping)]
    envelopes = [item for item in envelopes if isinstance(item, Mapping)]
    barriers = [item for item in barriers if isinstance(item, Mapping)]

    request_question_ids = [
        item.get("question_id")
        for item in request.get("questions", [])
        if isinstance(item, Mapping)
    ]
    planned_question_ids = [item.get("question_id") for item in question_plans]
    if len(planned_question_ids) != len(set(planned_question_ids)):
        errors.add("E_PLAN_QUESTION_DUPLICATE")
    if set(planned_question_ids) != set(request_question_ids):
        errors.add("E_PLAN_QUESTION_COVERAGE")

    source_policy = request.get("source_policy", {})
    required_source_classes = list(source_policy.get("required_classes", []))
    freshness_requirements = list(source_policy.get("freshness_requirements", []))
    request_stop_conditions = list(request.get("stop_conditions", []))
    for question_plan in question_plans:
        question_id = str(question_plan.get("question_id"))
        if question_plan.get("required_source_classes") != required_source_classes:
            errors.add("E_PLAN_SOURCE_POLICY", question_id)
        if question_plan.get("freshness_requirements") != freshness_requirements:
            errors.add("E_PLAN_FRESHNESS_REQUIREMENTS", question_id)
        if question_plan.get("stop_conditions") != request_stop_conditions:
            errors.add("E_PLAN_STOP_CONDITIONS", question_id)

    lane_ids = [item.get("lane_id") for item in lanes]
    envelope_ids = [item.get("envelope_id") for item in envelopes]
    task_ids = [item.get("task_id") for item in envelopes]
    barrier_ids = [item.get("barrier_id") for item in barriers]
    for values, code in (
        (lane_ids, "E_PLAN_LANE_DUPLICATE"),
        (envelope_ids, "E_PLAN_ENVELOPE_DUPLICATE"),
        (task_ids, "E_PLAN_TASK_DUPLICATE"),
        (barrier_ids, "E_PLAN_BARRIER_DUPLICATE"),
    ):
        if len(values) != len(set(values)):
            errors.add(code)
    lane_by_id = {item.get("lane_id"): item for item in lanes}
    envelope_by_id = {item.get("envelope_id"): item for item in envelopes}
    barrier_by_id = {item.get("barrier_id"): item for item in barriers}

    lane_question_links: set[tuple[Any, Any]] = set()
    referenced_lanes: list[Any] = []
    for question_plan in question_plans:
        question_id = question_plan.get("question_id")
        direct = question_plan.get("direct_lane_ids", [])
        contrary = question_plan.get("contrary_lane_ids", [])
        if set(direct) & set(contrary):
            errors.add("E_PLAN_LANE_POLARITY_OVERLAP", str(question_id))
        for kind, references in (("DIRECT", direct), ("CONTRARY", contrary)):
            if not references:
                errors.add("E_PLAN_LANE_POLARITY_MISSING", f"{question_id}/{kind}")
            for lane_id in references:
                referenced_lanes.append(lane_id)
                lane = lane_by_id.get(lane_id)
                if lane is None:
                    errors.add("E_PLAN_LANE_REFERENCE", str(lane_id))
                    continue
                if lane.get("kind") != kind:
                    errors.add("E_PLAN_LANE_KIND", str(lane_id))
                if question_id not in lane.get("question_ids", []):
                    errors.add("E_PLAN_LANE_QUESTION_BACKREF", str(lane_id))
                lane_question_links.add((lane_id, question_id))
    if set(referenced_lanes) != set(lane_ids):
        errors.add("E_PLAN_LANE_ORPHAN")
    for lane in lanes:
        if lane.get("required_source_classes") != required_source_classes:
            errors.add("E_PLAN_LANE_SOURCE_POLICY", str(lane.get("lane_id")))
        if lane.get("freshness_requirements") != freshness_requirements:
            errors.add(
                "E_PLAN_LANE_FRESHNESS_REQUIREMENTS",
                str(lane.get("lane_id")),
            )
        if lane.get("stop_conditions") != request_stop_conditions:
            errors.add(
                "E_PLAN_LANE_STOP_CONDITIONS",
                str(lane.get("lane_id")),
            )
        for question_id in lane.get("question_ids", []):
            if question_id not in request_question_ids:
                errors.add("E_PLAN_LANE_UNKNOWN_QUESTION", str(question_id))
            if (lane.get("lane_id"), question_id) not in lane_question_links:
                errors.add("E_PLAN_QUESTION_LANE_BACKREF", str(lane.get("lane_id")))

    referenced_envelopes: list[Any] = []
    referenced_barriers: list[Any] = []
    write_fences: list[str] = []
    selected_context_artifacts = {
        (
            item.get("artifact_id"),
            item.get("version"),
            item.get("path"),
            item.get("sha256"),
        )
        for item in manifest.get("entries", [])
        if isinstance(item, Mapping)
        and item.get("selection") == "SELECTED"
        and item.get("resolution_status") == "RESOLVED"
    }
    for lane in lanes:
        lane_id = lane.get("lane_id")
        lane_envelopes = lane.get("worker_envelope_ids", [])
        if len(lane_envelopes) != 1:
            errors.add("E_PLAN_LANE_ENVELOPE_CARDINALITY", str(lane_id))
        lane_barrier = lane.get("barrier_id")
        referenced_barriers.append(lane_barrier)
        barrier = barrier_by_id.get(lane_barrier)
        if barrier is None or lane_id not in barrier.get("lane_ids", []):
            errors.add("E_PLAN_BARRIER_BACKREF", str(lane_id))
        lane_query_budget = 0
        for envelope_id in lane_envelopes:
            referenced_envelopes.append(envelope_id)
            envelope = envelope_by_id.get(envelope_id)
            if envelope is None:
                errors.add("E_PLAN_ENVELOPE_REFERENCE", str(envelope_id))
                continue
            if envelope.get("lane_id") != lane_id:
                errors.add("E_PLAN_ENVELOPE_LANE_BINDING", str(envelope_id))
            if envelope.get("barrier_id") != lane_barrier:
                errors.add("E_PLAN_ENVELOPE_BARRIER_BINDING", str(envelope_id))
            envelope_context = envelope.get("context_manifest", {})
            if envelope_context != context_ref:
                errors.add("E_PLAN_ENVELOPE_CONTEXT_BINDING", str(envelope_id))
            envelope_input_keys: list[tuple[Any, Any, Any, Any]] = []
            for artifact in envelope.get("input_artifacts", []):
                if not isinstance(artifact, Mapping):
                    errors.add("E_PLAN_INPUT_ARTIFACT_OBJECT", str(envelope_id))
                    continue
                artifact_key = (
                    artifact.get("artifact_id"),
                    artifact.get("version"),
                    artifact.get("path"),
                    artifact.get("sha256"),
                )
                envelope_input_keys.append(artifact_key)
                if artifact_key not in selected_context_artifacts:
                    errors.add(
                        "E_PLAN_INPUT_ARTIFACT_NOT_SELECTED",
                        str(envelope_id),
                    )
                if artifact.get("artifact_id") == request.get("request_id"):
                    artifact_path = _run_ref(
                        run,
                        artifact.get("path"),
                        errors,
                        "E_PLAN_INPUT_ARTIFACT_PATH",
                    )
                else:
                    artifact_path = _workspace_ref(
                        workspace_path,
                        artifact.get("path"),
                        errors,
                        "E_PLAN_INPUT_ARTIFACT_PATH",
                    )
                _check_exact_file(
                    artifact_path,
                    artifact.get("sha256"),
                    errors,
                    "E_PLAN_INPUT_ARTIFACT",
                )
            if len(envelope_input_keys) != len(set(envelope_input_keys)):
                errors.add("E_PLAN_INPUT_ARTIFACT_DUPLICATE", str(envelope_id))
            for fence in envelope.get("write_fence", []):
                fence_path = _workspace_ref(
                    workspace_path, fence, errors, "E_PLAN_WRITE_FENCE_PATH"
                )
                if fence_path is not None and not _inside(fence_path.resolve(), run):
                    errors.add("E_PLAN_WRITE_FENCE_RUN", str(envelope_id))
                write_fences.append(fence)
            budgets = envelope.get("budgets", {})
            query_budget = budgets.get("queries")
            if isinstance(query_budget, int) and not isinstance(query_budget, bool):
                lane_query_budget += query_budget
            deadline = _parse_utc(budgets.get("deadline_utc"))
            created = _parse_utc(plan.get("created_at_utc"))
            if deadline is None or created is None or deadline < created:
                errors.add("E_PLAN_ENVELOPE_DEADLINE", str(envelope_id))
        if isinstance(lane.get("query_limit"), int) and lane_query_budget > lane.get("query_limit"):
            errors.add("E_PLAN_LANE_QUERY_BUDGET", str(lane_id))
    if len(write_fences) != len(set(write_fences)):
        errors.add("E_PLAN_WRITE_FENCE_COLLISION")
    if set(referenced_envelopes) != set(envelope_ids) or len(referenced_envelopes) != len(envelope_ids):
        errors.add("E_PLAN_ENVELOPE_ACCOUNTING")
    if set(referenced_barriers) != set(barrier_ids):
        errors.add("E_PLAN_BARRIER_ORPHAN")
    for barrier in barriers:
        expected = {lane.get("lane_id") for lane in lanes if lane.get("barrier_id") == barrier.get("barrier_id")}
        if set(barrier.get("lane_ids", [])) != expected:
            errors.add("E_PLAN_BARRIER_LANE_ACCOUNTING", str(barrier.get("barrier_id")))

    known_tasks = set(task_ids)
    for envelope in envelopes:
        if envelope.get("run_id") != run_id:
            errors.add("E_PLAN_ENVELOPE_RUN_BINDING", str(envelope.get("envelope_id")))
        for dependency in envelope.get("dependencies", []):
            if dependency not in known_tasks or dependency == envelope.get("task_id"):
                errors.add("E_PLAN_DEPENDENCY", str(envelope.get("task_id")))
    if _has_dependency_cycle(envelopes):
        errors.add("E_PLAN_DEPENDENCY_CYCLE")

    budget = plan.get("budget")
    request_budget = request.get("budget")
    if not isinstance(budget, Mapping) or not isinstance(request_budget, Mapping):
        errors.add("E_PLAN_BUDGET")
    else:
        if budget.get("profile") != request_budget.get("profile") or budget.get("limits") != request_budget.get("limits"):
            errors.add("E_PLAN_BUDGET_BINDING")
        limits = budget.get("limits", {})
        current_use = budget.get("current_use", {})
        if isinstance(limits, Mapping) and isinstance(current_use, Mapping):
            for field in _budget_overages(current_use, limits):
                errors.add("E_PLAN_BUDGET_EXCEEDED", field)
            if len(request_question_ids) > limits.get("atomic_questions", -1):
                errors.add("E_PLAN_ATOMIC_QUESTION_BUDGET")
            if len(lanes) > limits.get("research_lanes", -1):
                errors.add("E_PLAN_LANE_BUDGET")
            if sum(item.get("query_limit", 0) for item in lanes) > limits.get("discovery_queries", -1):
                errors.add("E_PLAN_DISCOVERY_QUERY_BUDGET")
            total_tool_calls = sum(item.get("budgets", {}).get("tool_calls", 0) for item in envelopes)
            total_model = sum(item.get("budgets", {}).get("model_tokens_or_bytes", 0) for item in envelopes)
            if total_tool_calls > limits.get("external_tool_calls", -1):
                errors.add("E_PLAN_TOOL_CALL_BUDGET")
            if total_model > limits.get("aggregate_model_tokens", -1):
                errors.add("E_PLAN_MODEL_BUDGET")
            retry_limit = limits.get("retry_per_failed_lane")
            if plan.get("retry_policy", {}).get("maximum_per_failed_lane", 0) > retry_limit:
                errors.add("E_PLAN_RETRY_BUDGET_BINDING")
            for envelope in envelopes:
                if envelope.get("budgets", {}).get("retries", 0) > retry_limit:
                    errors.add("E_PLAN_ENVELOPE_RETRY_BUDGET", str(envelope.get("envelope_id")))

    request_network = request.get("execution_policy", {})
    request_mode = request_network.get("network_policy")
    request_allowlist = set(request_network.get("network_allowlist", []))
    for envelope in envelopes:
        network = envelope.get("network_policy", {})
        mode = network.get("mode")
        allowlist = set(network.get("allowlist", []))
        if request_mode == "DENY" and mode != "DENY":
            errors.add("E_PLAN_NETWORK_AUTHORITY", str(envelope.get("envelope_id")))
        elif request_mode == "ALLOWLIST" and (mode == "OPEN" or not allowlist.issubset(request_allowlist)):
            errors.add("E_PLAN_NETWORK_AUTHORITY", str(envelope.get("envelope_id")))
    return errors.list()


def validate_reconciliation_contract(
    workspace: str | Path,
    run_path: str | Path,
    *,
    expected_run_id: str | None = None,
) -> list[str]:
    """Validate the P6 plan binding, lane accounting, artifacts, and budget."""

    errors = _Errors()
    workspace_path, run = _normalize_roots(workspace, run_path, errors)
    plan = _read_object(run / "plan.json", workspace_path, errors)
    reconciliation = _read_object(run / "reconciliation.json", workspace_path, errors)
    if plan is None or reconciliation is None:
        return errors.list()
    run_id = expected_run_id or run.name
    if reconciliation.get("run_id") != run_id or reconciliation.get("reconciliation_id") != f"{run_id}/reconciliation":
        errors.add("E_RECONCILIATION_RUN_BINDING")
    plan_ref = reconciliation.get("plan")
    if not isinstance(plan_ref, Mapping):
        errors.add("E_RECONCILIATION_PLAN_REFERENCE")
    else:
        if plan_ref.get("plan_id") != plan.get("plan_id"):
            errors.add("E_RECONCILIATION_PLAN_ID_BINDING")
        _check_exact_file(
            run / "plan.json",
            plan_ref.get("sha256"),
            errors,
            "E_RECONCILIATION_PLAN",
        )

    lanes = [item for item in plan.get("lanes", []) if isinstance(item, Mapping)]
    results = [item for item in reconciliation.get("lane_results", []) if isinstance(item, Mapping)]
    expected_lane_ids = [item.get("lane_id") for item in lanes]
    actual_lane_ids = [item.get("lane_id") for item in results]
    exact_lanes = (
        len(actual_lane_ids) == len(set(actual_lane_ids))
        and set(actual_lane_ids) == set(expected_lane_ids)
    )
    if not exact_lanes:
        errors.add("E_RECONCILIATION_LANE_ACCOUNTING")
    if reconciliation.get("all_expected_lanes_accounted") is not exact_lanes:
        errors.add("E_RECONCILIATION_LANE_ACCOUNTING_FLAG")

    lane_by_id = {item.get("lane_id"): item for item in lanes}
    envelope_by_id = {
        item.get("envelope_id"): item
        for item in plan.get("worker_envelopes", [])
        if isinstance(item, Mapping)
    }
    query_by_id = {
        item.get("record_id"): item
        for item in _read_jsonl(run / "queries.jsonl", workspace_path, errors)
        if isinstance(item, Mapping) and isinstance(item.get("record_id"), str)
    }
    aggregate = {
        "queries": 0,
        "sources": 0,
        "tool_calls": 0,
        "model_tokens_or_bytes": 0,
        "elapsed_minutes": 0,
        "retries": 0,
    }
    accepted_by_lanes: list[Any] = []
    for result in results:
        lane_id = result.get("lane_id")
        lane = lane_by_id.get(lane_id)
        if lane is None:
            continue
        result_envelopes = result.get("worker_envelope_ids", [])
        if set(result_envelopes) != set(lane.get("worker_envelope_ids", [])):
            errors.add("E_RECONCILIATION_ENVELOPE_ACCOUNTING", str(lane_id))
        attempts = result.get("attempts")
        maximum_attempts = 1 + plan.get("retry_policy", {}).get("maximum_per_failed_lane", 0)
        if not isinstance(attempts, int) or isinstance(attempts, bool) or attempts > maximum_attempts:
            errors.add("E_RECONCILIATION_RETRY_LIMIT", str(lane_id))
        allowed_schemas = {
            envelope_by_id[identifier].get("expected_result", {}).get("schema_id")
            for identifier in lane.get("worker_envelope_ids", [])
            if identifier in envelope_by_id
        }
        for artifact in result.get("result_artifacts", []):
            if not isinstance(artifact, Mapping):
                errors.add("E_RECONCILIATION_RESULT_OBJECT", str(lane_id))
                continue
            path = _run_ref(
                run,
                artifact.get("path"),
                errors,
                "E_RECONCILIATION_RESULT_PATH",
            )
            _check_exact_file(
                path,
                artifact.get("sha256"),
                errors,
                "E_RECONCILIATION_RESULT",
            )
            if artifact.get("schema_id") not in allowed_schemas:
                errors.add("E_RECONCILIATION_RESULT_SCHEMA", str(artifact.get("artifact_id")))
        lane_accepted = result.get("accepted_record_ids", [])
        accepted_by_lanes.extend(lane_accepted)
        for query_id in lane_accepted:
            query = query_by_id.get(query_id)
            if query is None:
                continue
            if query.get("lane_id") != lane_id:
                errors.add(
                    "E_RECONCILIATION_ACCEPTED_QUERY_LANE",
                    str(query_id),
                )
            if query.get("worker_envelope_id") not in result_envelopes:
                errors.add(
                    "E_RECONCILIATION_ACCEPTED_QUERY_ENVELOPE",
                    str(query_id),
                )
        usage = result.get("usage", {})
        if isinstance(usage, Mapping):
            for key in aggregate:
                value = usage.get(key)
                if isinstance(value, int) and not isinstance(value, bool):
                    aggregate[key] += value
                else:
                    errors.add("E_RECONCILIATION_USAGE", f"{lane_id}/{key}")
            query_limit = lane.get("query_limit")
            if isinstance(query_limit, int) and usage.get("queries", 0) > query_limit:
                errors.add("E_RECONCILIATION_LANE_QUERY_LIMIT", str(lane_id))
            expected_query_count = sum(
                query.get("lane_id") == lane_id for query in query_by_id.values()
            )
            if usage.get("queries") != expected_query_count:
                errors.add(
                    "E_RECONCILIATION_LANE_QUERY_ACCOUNTING",
                    str(lane_id),
                )
            if (
                isinstance(attempts, int)
                and not isinstance(attempts, bool)
                and usage.get("retries") != attempts - 1
            ):
                errors.add(
                    "E_RECONCILIATION_ATTEMPT_RETRY_ACCOUNTING",
                    str(lane_id),
                )
    if len(accepted_by_lanes) != len(set(accepted_by_lanes)):
        errors.add("E_RECONCILIATION_ACCEPTED_RECORD_DUPLICATE")
    if set(accepted_by_lanes) != set(reconciliation.get("accepted_record_ids", [])):
        errors.add("E_RECONCILIATION_ACCEPTED_RECORD_ACCOUNTING")
    if set(accepted_by_lanes) != set(query_by_id):
        errors.add("E_RECONCILIATION_QUERY_ACCOUNTING")
    if reconciliation.get("budget_use") != aggregate:
        errors.add("E_RECONCILIATION_BUDGET_ACCOUNTING")

    canonical_ids: set[str] = set()
    for filename in (
        "queries.jsonl",
        "sources.jsonl",
        "evidence.jsonl",
        "claims.jsonl",
        "contradictions.jsonl",
    ):
        candidate = run / filename
        if candidate.exists():
            for item in _read_jsonl(candidate, workspace_path, errors):
                identifier = item.get("record_id")
                if isinstance(identifier, str):
                    canonical_ids.add(identifier)
    unknown_accepted = sorted(
        set(reconciliation.get("accepted_record_ids", [])) - canonical_ids
    )
    for identifier in unknown_accepted:
        errors.add("E_RECONCILIATION_ACCEPTED_RECORD_MISSING", identifier)

    limits = plan.get("budget", {}).get("limits", {})
    budget_within = not _budget_overages(aggregate, limits) if isinstance(limits, Mapping) else False
    retry_limit = limits.get("retry_per_failed_lane") if isinstance(limits, Mapping) else None
    if not isinstance(retry_limit, int) or aggregate["retries"] > retry_limit * max(1, len(lanes)):
        budget_within = False
    concurrent_peak = reconciliation.get("concurrent_workers_peak")
    concurrent_limit = limits.get("concurrent_workers") if isinstance(limits, Mapping) else None
    if (
        not isinstance(concurrent_peak, int)
        or isinstance(concurrent_peak, bool)
        or not isinstance(concurrent_limit, int)
        or concurrent_peak > concurrent_limit
        or concurrent_peak > max(1, len(lanes))
    ):
        budget_within = False
        errors.add("E_RECONCILIATION_CONCURRENCY_EXCEEDED")
    if reconciliation.get("budget_within_limits") is not budget_within:
        errors.add("E_RECONCILIATION_BUDGET_FLAG")
    if not budget_within:
        errors.add("E_RECONCILIATION_BUDGET_EXCEEDED")

    question_plan_by_id = {
        item.get("question_id"): item
        for item in plan.get("question_plans", [])
        if isinstance(item, Mapping)
    }
    coverage = [
        item for item in reconciliation.get("question_coverage", []) if isinstance(item, Mapping)
    ]
    coverage_ids = [item.get("question_id") for item in coverage]
    if len(coverage_ids) != len(set(coverage_ids)) or set(coverage_ids) != set(question_plan_by_id):
        errors.add("E_RECONCILIATION_QUESTION_COVERAGE")
    returned_lanes = {
        item.get("lane_id")
        for item in results
        if item.get("terminal_status") == "RETURNED"
    }
    for item in coverage:
        expected = question_plan_by_id.get(item.get("question_id"))
        if expected is None:
            continue
        direct = expected.get("direct_lane_ids", [])
        contrary = expected.get("contrary_lane_ids", [])
        if item.get("direct_lane_ids") != direct or item.get("contrary_lane_ids") != contrary:
            errors.add("E_RECONCILIATION_QUESTION_LANES", str(item.get("question_id")))
        question_id = item.get("question_id")

        def executed_edge(lane_id: Any, purposes: set[str]) -> bool:
            return lane_id in returned_lanes and any(
                query.get("lane_id") == lane_id
                and question_id in query.get("question_ids", [])
                and query.get("purpose") in purposes
                and query.get("status") == "EXECUTED"
                for query in query_by_id.values()
            )

        direct_terminal = all(
            executed_edge(identifier, {"DISCOVERY", "CORROBORATION"})
            for identifier in direct
        )
        contrary_terminal = all(
            executed_edge(identifier, {"CHALLENGE"}) for identifier in contrary
        )
        if item.get("direct_terminal") is not direct_terminal:
            errors.add("E_RECONCILIATION_DIRECT_TERMINAL", str(item.get("question_id")))
        if item.get("contrary_terminal") is not contrary_terminal:
            errors.add("E_RECONCILIATION_CONTRARY_TERMINAL", str(item.get("question_id")))

    if reconciliation.get("majority_vote_used") is not False:
        errors.add("E_RECONCILIATION_MAJORITY_VOTE")
    if reconciliation.get("status") == "PASS":
        if not exact_lanes or not budget_within:
            errors.add("E_RECONCILIATION_PASS_GATE")
        for item in results:
            if item.get("terminal_status") != "RETURNED":
                errors.add(
                    "E_RECONCILIATION_PASS_LANE_NOT_RETURNED",
                    str(item.get("lane_id")),
                )
        for item in coverage:
            if not all(
                item.get(field) is True
                for field in ("direct_terminal", "contrary_terminal", "stop_conditions_met")
            ):
                errors.add("E_RECONCILIATION_PASS_COVERAGE", str(item.get("question_id")))
    return errors.list()


def validate_success_state_contract(
    workspace: str | Path,
    run_path: str | Path,
    *,
    expected_run_id: str | None = None,
) -> list[str]:
    """Validate a successful pre-seal journal and READY_TO_SEAL validation."""

    errors = _Errors()
    workspace_path, run = _normalize_roots(workspace, run_path, errors)
    events = _read_jsonl(run / "state.jsonl", workspace_path, errors)
    validation = _read_object(run / "validation.json", workspace_path, errors)
    run_id = expected_run_id or run.name
    if not events:
        errors.add("E_STATE_EMPTY")
    previous: str | None = None
    phase: str | None = None
    for index, event in enumerate(events):
        label = str(index)
        if event.get("run_id") != run_id:
            errors.add("E_STATE_RUN_BINDING", label)
        if event.get("sequence") != index:
            errors.add("E_STATE_SEQUENCE", label)
        if event.get("previous_event_sha256") != previous:
            errors.add("E_STATE_PREVIOUS_DIGEST", label)
        if event.get("event_type") != "PHASE_TRANSITION":
            errors.add("E_STATE_SUCCESS_TERMINAL_EVENT", label)
        if event.get("from_phase") != phase:
            errors.add("E_STATE_FROM_PHASE", label)
        to_phase = event.get("to_phase")
        if to_phase not in LEGAL_TRANSITIONS.get(phase, frozenset()):
            errors.add("E_STATE_TRANSITION", label)
        if "outcome" in event:
            errors.add("E_STATE_PRESEAL_OUTCOME", label)
        if event.get("outcome") == "COMPLETE" or event.get("reason_code") == "COMPLETE":
            errors.add("E_STATE_PRESEAL_COMPLETE", label)
        expected_reason = (
            "RUN_OPENED"
            if index == 0
            else "READY_TO_SEAL"
            if to_phase == "P9"
            else "REPAIR_ROUTE"
            if (phase, to_phase) in {("P6", "P4"), ("P6", "P5"), ("P7", "P5"), ("P7", "P6")}
            else "PHASE_ADVANCE"
        )
        if event.get("reason_code") != expected_reason:
            errors.add("E_STATE_REASON_CODE", label)
        try:
            previous = canonical_json_sha256(event)
        except (TypeError, ValueError):
            errors.add("E_STATE_CANONICAL", label)
            previous = None
        phase = to_phase if to_phase in PHASES else phase
    if not events or events[-1].get("to_phase") != "P9" or events[-1].get("reason_code") != "READY_TO_SEAL":
        errors.add("E_STATE_NOT_READY_TO_SEAL")

    if validation is None:
        return errors.list()
    if validation.get("run_id") != run_id or validation.get("validation_id") != f"{run_id}/validation":
        errors.add("E_VALIDATION_RUN_BINDING")
    if validation.get("scope") != "PRE_SEAL":
        errors.add("E_VALIDATION_SCOPE")
    if validation.get("gate_status") != "READY_TO_SEAL":
        errors.add("E_VALIDATION_NOT_READY_TO_SEAL")
    if validation.get("gate_status") == "COMPLETE" or any(
        value == "COMPLETE" for value in validation.get("errors", [])
    ):
        errors.add("E_VALIDATION_PRESEAL_COMPLETE")
    if validation.get("errors"):
        errors.add("E_VALIDATION_ERRORS")

    checks = validation.get("checks", [])
    check_ids = [item.get("check_id") for item in checks if isinstance(item, Mapping)]
    if len(check_ids) != len(checks) or len(check_ids) != len(set(check_ids)) or set(check_ids) != VALIDATION_CHECK_IDS:
        errors.add("E_VALIDATION_CHECK_ACCOUNTING")
    for check in checks:
        if not isinstance(check, Mapping):
            continue
        if check.get("applicable") is True and check.get("status") != "PASS":
            errors.add("E_VALIDATION_APPLICABLE_CHECK", str(check.get("check_id")))
        if check.get("applicable") is False and check.get("status") != "NOT_APPLICABLE":
            errors.add("E_VALIDATION_NOT_APPLICABLE_CHECK", str(check.get("check_id")))

    subjects = validation.get("subject_files", [])
    subject_paths = [item.get("path") for item in subjects if isinstance(item, Mapping)]
    if len(subject_paths) != len(subjects) or len(subject_paths) != len(set(subject_paths)):
        errors.add("E_VALIDATION_SUBJECT_DUPLICATE")
    for subject in subjects:
        if not isinstance(subject, Mapping):
            continue
        path = _run_ref(
            run,
            subject.get("path"),
            errors,
            "E_VALIDATION_SUBJECT_PATH",
        )
        _check_exact_file(
            path,
            subject.get("sha256"),
            errors,
            "E_VALIDATION_SUBJECT",
            expected_length=subject.get("byte_length"),
        )
    return errors.list()


def validate_run_contracts(
    workspace: str | Path,
    run_path: str | Path,
    *,
    expected_run_id: str | None = None,
    as_of_utc: str | None = None,
) -> list[str]:
    """Run every singleton semantic validator with stable error de-duplication."""

    errors = _Errors()
    for validator, kwargs in (
        (
            validate_preflight_contract,
            {"expected_run_id": expected_run_id, "as_of_utc": as_of_utc},
        ),
        (
            validate_context_manifest_contract,
            {"expected_run_id": expected_run_id},
        ),
        (validate_plan_contract, {"expected_run_id": expected_run_id}),
        (
            validate_reconciliation_contract,
            {"expected_run_id": expected_run_id},
        ),
        (
            validate_success_state_contract,
            {"expected_run_id": expected_run_id},
        ),
    ):
        errors.extend(validator(workspace, run_path, **kwargs))
    return errors.list()


__all__ = [
    "canonical_json_sha256",
    "validate_context_manifest_contract",
    "validate_plan_contract",
    "validate_preflight_contract",
    "validate_reconciliation_contract",
    "validate_request_run_contract",
    "validate_run_contracts",
    "validate_success_state_contract",
]
