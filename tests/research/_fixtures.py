"""Synthetic record factories shared by Research Core contract tests."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any


FIXTURES = Path(__file__).parent / "fixtures"
RECORDED_AT = "2026-09-01T00:00:00Z"
FRESH_UNTIL = "2099-01-01T00:00:00Z"

PROVIDER_RUNTIME_FIXTURE_IDS = [
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
]

PROVIDER_RUNTIME_FIXTURE_SUITE = {
    "schema_version": "provider-conformance-fixture-suite/v1",
    "suite_id": "devforgeai-research-provider-runtime",
    "suite_version": "1.0.0",
    "manifest_sha256": (
        "ff76986b52a46adb438a721770251465883b1d5cad3ceb1ae842bd968bfdc2c4"
    ),
    "required_fixture_ids": PROVIDER_RUNTIME_FIXTURE_IDS,
}

OFFLINE_FIXTURE_SUITE = {
    "schema_version": "provider-conformance-fixture-suite/v1",
    "suite_id": "devforgeai-research-offline-core",
    "suite_version": "1.0.0",
    "manifest_sha256": (
        "a1d149d6fccb6721e9d4fb4532465f193fd3d98d28642ad3553e2bdd7ac9a65a"
    ),
    "required_fixture_ids": ["offline-core-acceptance"],
}


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def common_record(
    record_id: str,
    *,
    run_id: str = "RUN-000001",
    source_refs: list[str] | None = None,
    evidence_refs: list[str] | None = None,
    decision_refs: list[str] | None = None,
    lifecycle_status: str = "PROPOSED",
    readiness_status: str = "READY",
) -> dict[str, Any]:
    return {
        "record_id": record_id,
        "record_version": 1,
        "run_id": run_id,
        "lifecycle_status": lifecycle_status,
        "readiness_status": readiness_status,
        "owner": "agent:research-lead",
        "decision_authority": "person:owner",
        "created_at_utc": RECORDED_AT,
        "source_refs": list(source_refs or []),
        "evidence_refs": list(evidence_refs or []),
        "decision_refs": list(decision_refs or []),
        "supersedes": [],
        "stale_if": [],
    }


def load_request(*, high_risk: bool = False, slug: str | None = None) -> dict[str, Any]:
    name = "request-high.json" if high_risk else "request-low.json"
    result = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    if slug is not None:
        result["slug"] = slug
    return result


def run_header(request_sha256: str = "b" * 64) -> dict[str, Any]:
    return {
        "schema_version": "research-run/v1",
        "run_id": "RUN-000001",
        "request_id": "RSR-000001",
        "slug": "offline-fixture",
        "confirmation_binding": {
            "request_sha256": request_sha256,
            "confirming_authority": "person:requester",
            "method": "INTERACTIVE",
            "confirmed_at": RECORDED_AT,
            "work_order_sha256": None,
        },
    }


def provider_conformance(
    *,
    provider_kind: str = "OFFLINE_TEST_HARNESS",
    status: str = "SUPPORTED",
) -> dict[str, Any]:
    offline = provider_kind == "OFFLINE_TEST_HARNESS"
    capability_status = "SUPPORTED" if status == "SUPPORTED" else "NOT_PROBED"
    return {
        "schema_version": "provider-conformance-attestation/v1",
        "attestation_id": "PCA-000001",
        "attestation_subject": {
            "provider_kind": provider_kind,
            "provider_id": "devforgeai-offline-contract-harness" if offline else provider_kind.lower(),
            "installed_version": "fixture-v1",
            "adapter_path": "tests/research/offline-harness" if offline else "src/provider/research-adapter",
            "adapter_sha256": "1" * 64,
        },
        "evaluation_profile": "OFFLINE_CORE_ACCEPTANCE" if offline else "PROVIDER_RUNTIME",
        "fixture_suite": copy.deepcopy(
            OFFLINE_FIXTURE_SUITE if offline else PROVIDER_RUNTIME_FIXTURE_SUITE
        ),
        "evaluator": {
            "actor_id": "test:research-schema-suite",
            "independent_of_subject": True,
            "harness_id": "offline-schema-validator",
            "harness_version": "1",
            "harness_sha256": "2" * 64,
        },
        "capabilities": [
            {
                "capability_id": capability_id,
                "required": True,
                "status": capability_status,
                "reason": (
                    "The synthetic Core contract is exercised without a provider runtime."
                    if offline
                    else "No provider runtime trial has been performed."
                ),
                "evidence": (
                    [
                        {
                            "artifact_id": "offline-schema-suite",
                            "path": "tests/research/test_schemas.py",
                            "sha256": "3" * 64,
                        }
                    ]
                    if offline
                    else []
                ),
            }
            for capability_id in (
                "SOURCE_OPEN",
                "FRESH_ISOLATED_WORKER",
                "READ_ONLY_WORKER_FENCE",
                "RESEARCH_CORE",
                "CONTENT_ADDRESSED_STORAGE",
                "DOSSIER_WRITER_LOCK",
            )
        ],
        "trial_policy": (
            "OFFLINE_SYNTHETIC_ACCEPTANCE"
            if offline
            else "FIVE_FRESH_WITH_DISABLED_BASELINE"
        ),
        "trials": (
            [
                {
                    "trial_id": "PCT-000001",
                    "fixture_id": "offline-core-acceptance",
                    "session_id": "offline-test-process-001",
                    "baseline": "NOT_APPLICABLE",
                    "fresh_session": True,
                    "outcome": "PASS",
                    "evidence_path": "tests/research/test_schemas.py",
                    "evidence_sha256": "3" * 64,
                    "performed_at_utc": RECORDED_AT,
                }
            ]
            if offline
            else []
        ),
        "status": status,
        "issued_at_utc": RECORDED_AT,
        "expires_at_utc": FRESH_UNTIL,
        "limitations": [
            "OFFLINE_TEST_HARNESS evidence does not establish Claude Code or Codex conformance."
        ],
    }


def preflight(attestation: dict[str, Any] | None = None) -> dict[str, Any]:
    attestation = copy.deepcopy(attestation or provider_conformance())
    return {
        "schema_version": "research-preflight/v1",
        "preflight_id": "RUN-000001/preflight",
        "run_id": "RUN-000001",
        "request_id": "RSR-000001",
        "request_sha256": "b" * 64,
        "provider_subject": copy.deepcopy(attestation["attestation_subject"]),
        "attestation": {
            "attestation_id": attestation["attestation_id"],
            "path": "tests/research/fixtures/offline-provider-conformance.json",
            "sha256": canonical_sha256(attestation),
            "status": attestation["status"],
        },
        "capability_checks": [
            {
                "capability_id": capability_id,
                "required": True,
                "status": "SUPPORTED",
                "basis": (
                    "ATTESTATION"
                    if capability_id in {"SOURCE_OPEN", "FRESH_ISOLATED_WORKERS", "READ_ONLY_WORKER_FENCE"}
                    else "DETERMINISTIC_LOCAL_CHECK"
                ),
                "reason": "Available in the bounded synthetic offline acceptance harness.",
                "evidence_artifact_ids": (
                    ["offline-schema-suite"]
                    if capability_id
                    in {
                        "SOURCE_OPEN",
                        "FRESH_ISOLATED_WORKERS",
                        "READ_ONLY_WORKER_FENCE",
                    }
                    else [f"local:{capability_id.lower()}"]
                ),
            }
            for capability_id in (
                "SOURCE_OPEN",
                "FRESH_ISOLATED_WORKERS",
                "READ_ONLY_WORKER_FENCE",
                "RESEARCH_CORE",
                "SELECTED_CAS",
                "DOSSIER_WRITER_LOCK",
            )
        ],
        "writer_lock": {
            "path": ".devforgeai/research-locks/offline-fixture.lock",
            "status": "AVAILABLE",
            "checked_at_utc": RECORDED_AT,
        },
        "gate": {
            "status": "PASS",
            "reason_code": "P0_CAPABILITIES_SUPPORTED",
            "explanation": "All required synthetic offline capabilities are supported.",
        },
        "performed_at_utc": RECORDED_AT,
    }


def context_manifest() -> dict[str, Any]:
    return {
        "schema_version": "research-context-manifest/v1",
        "manifest_id": "RUN-000001/context-manifest",
        "run_id": "RUN-000001",
        "request_id": "RSR-000001",
        "request_sha256": "b" * 64,
        "lifecycle_status": "ACCEPTED",
        "readiness_status": "READY",
        "owner": "agent:research-lead",
        "decision_authority": "person:owner",
        "created_at_utc": RECORDED_AT,
        "context_budget": {"meter_mode": "BYTE_PROXY", "limit": 65536, "used": 1024},
        "entries": [
            {
                "entry_id": "CTX-ENTRY-000001",
                "artifact_kind": "REQUEST",
                "artifact_id": "RSR-000001",
                "version": "research-request/v1",
                "path": ".devforgeai/research-staging/offline-fixture/RUN-000001/request.json",
                "sha256": "b" * 64,
                "anchors": ["ENTIRE_ARTIFACT"],
                "applicability": "REUSABLE",
                "selection": "SELECTED",
                "resolution_status": "RESOLVED",
                "serialized_bytes": 1024,
                "rationale": "The exact confirmed request is required by every lane.",
            }
        ],
        "declared_scope_exclusions": ["Real providers and real products"],
        "unresolved_ambiguities": [],
        "gate_status": "PASS",
    }


def _worker_envelope(number: int, lane_id: str, objective: str) -> dict[str, Any]:
    return {
        "envelope_id": f"ENV-{number:06d}",
        "trace_id": f"TRACE-{number:06d}",
        "run_id": "RUN-000001",
        "task_id": f"TASK-{number:06d}",
        "lane_id": lane_id,
        "objective": objective,
        "delegation_reason": "The lane is disjoint, read-only, and schema bounded.",
        "scope": {"include": ["Synthetic fixture evidence"], "exclude": ["External sources"]},
        "input_artifacts": [
            {
                "artifact_id": "RSR-000001",
                "version": "research-request/v1",
                "path": ".devforgeai/research-staging/offline-fixture/RUN-000001/request.json",
                "sha256": "b" * 64,
            }
        ],
        "context_manifest": {"manifest_id": "RUN-000001/context-manifest", "sha256": "c" * 64},
        "unresolved_ambiguities": [],
        "runtime": {
            "provider": "offline-test-harness",
            "provider_version": "fixture-v1",
            "model": "not-applicable",
            "agent": "synthetic-worker",
            "agent_version": "1",
            "skill": "research",
            "skill_version": "1",
            "harness": "python-unittest",
            "harness_version": "1",
        },
        "allowed_tools": ["fixture-read"],
        "network_policy": {"mode": "DENY", "allowlist": []},
        "secret_access": {"mode": "NONE", "secret_ids": []},
        "trust_class": "TRUSTED_LOCAL",
        "write_fence": [],
        "expected_result": {
            "schema_id": "synthetic-research-lane-result/v1",
            "schema_sha256": "d" * 64,
            "evidence_requirements": ["Return exact fixture path and SHA-256."],
        },
        "success_conditions": ["Every returned candidate has a terminal disposition."],
        "stop_conditions": ["The bounded synthetic fixture set is exhausted."],
        "escalation_conditions": ["A required fixture cannot be read."],
        "budgets": {
            "queries": 2,
            "tool_calls": 2,
            "retries": 1,
            "model_tokens_or_bytes": 4096,
            "deadline_utc": FRESH_UNTIL,
        },
        "partial_result_policy": "REJECT",
        "dependencies": [],
        "barrier_id": "BAR-000001",
        "conflict_reconciliation_policy": "PRESERVE_AND_ROUTE",
    }


def plan() -> dict[str, Any]:
    limits = copy.deepcopy(load_request()["budget"]["limits"])
    usage = {
        "queries": 0,
        "sources": 0,
        "tool_calls": 0,
        "model_tokens_or_bytes": 0,
        "elapsed_minutes": 0,
        "retries": 0,
    }
    return {
        "schema_version": "research-plan/v1",
        "plan_id": "RUN-000001/plan",
        "run_id": "RUN-000001",
        "request_id": "RSR-000001",
        "request_sha256": "b" * 64,
        "context_manifest": {"manifest_id": "RUN-000001/context-manifest", "sha256": "c" * 64},
        "risk_tier": "LOW",
        "owner": "agent:research-lead",
        "decision_authority": "person:owner",
        "question_plans": [
            {
                "question_id": "RQ-000001",
                "direct_lane_ids": ["LANE-000001"],
                "contrary_lane_ids": ["LANE-000002"],
                "required_source_classes": ["PRIMARY"],
                "admission_criteria": ["Open the underlying synthetic fixture."],
                "freshness_requirements": ["Use the exact retained fixture bytes."],
                "stop_conditions": [
                    "Stop after the synthetic fixture is sealed.",
                ],
            }
        ],
        "lanes": [
            {
                "lane_id": "LANE-000001",
                "question_ids": ["RQ-000001"],
                "kind": "DIRECT",
                "objective": "Find direct evidence for the bounded question.",
                "query_limit": 2,
                "required_source_classes": ["PRIMARY"],
                "admission_criteria": ["Underlying fixture opened."],
                "freshness_requirements": [
                    "Use the exact retained fixture bytes.",
                ],
                "stop_conditions": [
                    "Stop after the synthetic fixture is sealed.",
                ],
                "worker_envelope_ids": ["ENV-000001"],
                "barrier_id": "BAR-000001",
            },
            {
                "lane_id": "LANE-000002",
                "question_ids": ["RQ-000001"],
                "kind": "CONTRARY",
                "objective": "Seek a bounded counterexample.",
                "query_limit": 2,
                "required_source_classes": ["PRIMARY"],
                "admission_criteria": ["Underlying fixture opened."],
                "freshness_requirements": [
                    "Use the exact retained fixture bytes.",
                ],
                "stop_conditions": [
                    "Stop after the synthetic fixture is sealed.",
                ],
                "worker_envelope_ids": ["ENV-000002"],
                "barrier_id": "BAR-000001",
            },
        ],
        "worker_envelopes": [
            _worker_envelope(1, "LANE-000001", "Find direct evidence."),
            _worker_envelope(2, "LANE-000002", "Find contrary evidence."),
        ],
        "barriers": [
            {
                "barrier_id": "BAR-000001",
                "lane_ids": ["LANE-000001", "LANE-000002"],
                "release_when": "ALL_LANES_TERMINAL",
                "on_incomplete": "BLOCK",
            }
        ],
        "budget": {
            "profile": "quick",
            "limits": limits,
            "current_use": usage,
            "meter_mode": "BYTE_PROXY",
        },
        "retry_policy": {"maximum_per_failed_lane": 1, "retryable_results": ["FAILED", "TIMED_OUT", "INVALID"]},
        "partial_result_policy": "REJECT",
        "reconciliation_rule": {
            "method": "CENTRAL_SCHEMA_AND_EVIDENCE_RECONCILIATION",
            "stable_sort_keys": ["lane_id", "artifact_id"],
            "duplicate_key": "record_id+record_version",
            "conflict_rule": "PRESERVE_AND_ROUTE",
            "missing_lane_rule": "RECORD_AND_FAIL_GATE",
            "majority_vote_permitted": False,
        },
        "plan_status": "READY",
        "created_at_utc": RECORDED_AT,
    }


def decision() -> dict[str, Any]:
    return {
        **common_record("DEC-000001", lifecycle_status="ACCEPTED"),
        "schema_version": "research-decision/v1",
        "decision_id": "DEC-000001",
        "decision_type": "SCOPE",
        "status": "ACCEPTED",
        "risk_tier": "LOW",
        "subject_refs": ["RQ-000001"],
        "decision_text": "Keep the research scope limited to synthetic fixture behavior.",
        "rationale": "The offline acceptance run must not imply a real provider result.",
        "scope": ["RQ-000001"],
        "constraints": ["Do not generalize beyond retained fixtures."],
        "authority_id": "person:owner",
        "authority_basis": "Named decision authority in the confirmed request.",
        "decided_at_utc": RECORDED_AT,
        "effective_until_utc": None,
        "downstream_acceptance": False,
    }


def reconciliation() -> dict[str, Any]:
    usage = {
        "queries": 1,
        "sources": 1,
        "tool_calls": 1,
        "model_tokens_or_bytes": 1024,
        "elapsed_minutes": 1,
        "retries": 0,
    }
    lane_results = []
    for number in (1, 2):
        lane_results.append(
            {
                "lane_id": f"LANE-{number:06d}",
                "terminal_status": "RETURNED",
                "attempts": 1,
                "worker_envelope_ids": [f"ENV-{number:06d}"],
                "result_artifacts": [
                    {
                        "artifact_id": f"lane-result-{number:06d}",
                        "schema_id": "synthetic-research-lane-result/v1",
                        "path": f"workers/lane-{number:06d}.json",
                        "sha256": str(number + 3) * 64,
                    }
                ],
                "accepted_record_ids": [f"QRY-{number:06d}"],
                "usage": copy.deepcopy(usage),
                "reason": "The schema-valid bounded lane result was reconciled.",
                "limitations": ["Synthetic fixture result only."],
                "completed_at_utc": RECORDED_AT,
            }
        )
    return {
        "schema_version": "research-reconciliation/v1",
        "reconciliation_id": "RUN-000001/reconciliation",
        "run_id": "RUN-000001",
        "plan": {"plan_id": "RUN-000001/plan", "sha256": "e" * 64},
        "owner": "agent:research-lead",
        "decision_authority": "person:owner",
        "lane_results": lane_results,
        "question_coverage": [
            {
                "question_id": "RQ-000001",
                "direct_lane_ids": ["LANE-000001"],
                "contrary_lane_ids": ["LANE-000002"],
                "direct_terminal": True,
                "contrary_terminal": True,
                "stop_conditions_met": True,
            }
        ],
        "conflicts": [],
        "invalid_outputs": [],
        "accepted_record_ids": ["QRY-000001", "QRY-000002"],
        "budget_use": {
            "queries": 2,
            "sources": 2,
            "tool_calls": 2,
            "model_tokens_or_bytes": 2048,
            "elapsed_minutes": 2,
            "retries": 0,
        },
        "concurrent_workers_peak": 2,
        "all_expected_lanes_accounted": True,
        "budget_within_limits": True,
        "majority_vote_used": False,
        "status": "PASS",
        "completed_at_utc": RECORDED_AT,
    }


VALIDATION_CHECK_IDS = (
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
)


def validation() -> dict[str, Any]:
    return {
        "schema_version": "research-validation/v1",
        "validation_id": "RUN-000001/validation",
        "run_id": "RUN-000001",
        "scope": "PRE_SEAL",
        "subject_files": [
            {
                "path": "request.json",
                "sha256": "b" * 64,
                "byte_length": 1024,
            }
        ],
        "checks": [
            {
                "check_id": check_id,
                "applicable": True,
                "status": "PASS",
                "reason": "The deterministic synthetic contract check passed.",
                "evidence": [],
            }
            for check_id in VALIDATION_CHECK_IDS
        ],
        "errors": [],
        "warnings": [],
        "environment": {
            "core_version": "offline-fixture-v1",
            "schema_set_sha256": "f" * 64,
            "platform": "synthetic-offline",
        },
        "gate_status": "READY_TO_SEAL",
        "validated_at_utc": RECORDED_AT,
    }


def question() -> dict[str, Any]:
    return {
        **common_record("RQ-000001"),
        "schema_version": "research-question/v1",
        "question_id": "RQ-000001",
        "text": "Does a valid start signal cause exactly one green pulse?",
        "completion_criteria": [
            "Answer from admitted evidence and run a contrary lane."
        ],
        "priority": "LOW",
    }


def query() -> dict[str, Any]:
    return {
        **common_record("QRY-000001"),
        "schema_version": "research-query/v1",
        "query_id": "QRY-000001",
        "question_ids": ["RQ-000001"],
        "lane_id": "LANE-000001",
        "worker_envelope_id": "ENV-000001",
        "purpose": "DISCOVERY",
        "query_text": "synthetic widget single green pulse",
        "tool": "offline-fixture",
        "status": "EXECUTED",
        "executed_at": RECORDED_AT,
        "results": [
            {
                "candidate_id": "QRY-000001-CAND-000001",
                "locator": "tests/research/fixtures/source-primary.txt",
                "title": "Synthetic Standard A",
                "discovery_only": True,
                "disposition": "RETRIEVE",
                "reason": "Selected for exact-byte retrieval as the primary synthetic source.",
            }
        ],
    }


def challenge_query() -> dict[str, Any]:
    return {
        **common_record("QRY-000002"),
        "schema_version": "research-query/v1",
        "query_id": "QRY-000002",
        "question_ids": ["RQ-000001"],
        "lane_id": "LANE-000002",
        "worker_envelope_id": "ENV-000002",
        "purpose": "CHALLENGE",
        "query_text": "synthetic widget counterexample repeated signal",
        "tool": "offline-fixture",
        "status": "EXECUTED",
        "executed_at": RECORDED_AT,
        "results": [
            {
                "candidate_id": "QRY-000002-CAND-000001",
                "locator": "tests/research/fixtures/source-contrary.txt",
                "title": "Synthetic Erratum C",
                "discovery_only": True,
                "disposition": "RETRIEVE",
                "reason": "Selected for exact-byte retrieval in the contrary-evidence lane.",
            }
        ],
    }


def source_metadata(
    source_id: str,
    fixture_name: str,
    *,
    publisher: str,
    source_class: str = "PRIMARY",
) -> dict[str, Any]:
    return {
        **common_record(source_id),
        "schema_version": "research-source/v1",
        "source_id": source_id,
        "question_ids": ["RQ-000001"],
        "query_ids": ["QRY-000001"],
        "candidate_ids": ["QRY-000001-CAND-000001"],
        "title": fixture_name.replace("-", " ").removesuffix(".txt").title(),
        "publisher": publisher,
        "locator": {
            "kind": "LOCAL_FILE",
            "value": f"tests/research/fixtures/{fixture_name}",
        },
        "source_type": "DOCUMENTATION",
        "source_class": source_class,
        "retrieval": {
            "method": "LOCAL_FILE",
            "status": "RETRIEVED",
            "retrieved_at": RECORDED_AT,
            "network_accessed": False,
        },
        "admission": "ADMITTED_EVIDENCE",
        "retention_policy": {
            "retention_permitted": True,
            "redistribution_basis": "USER_OWNED",
            "redistribution_reference": "synthetic fixture authored for this test suite",
            "data_classification": "PUBLIC",
            "sensitive_scan": {
                "status": "PASS",
                "scanner_id": "fixture-sensitive-scan",
                "ruleset_sha256": "1" * 64,
                "findings_count": 0,
            },
        },
        "relevant_sections": ["entire synthetic fixture"],
        "limitations": ["Synthetic evidence; never a claim about a real system."],
        "freshness": {
            "status": "CURRENT",
            "checked_at": RECORDED_AT,
            "stale_after": FRESH_UNTIL,
            "assessment_basis": "Pinned synthetic fixture with a future stale-after boundary.",
            "rationale": "The retained fixture bytes are current for this offline run.",
        },
    }


def evidence(
    evidence_id: str,
    source_id: str,
    source_sha256: str,
    text: str,
    *,
    polarity: str = "SUPPORTING",
) -> dict[str, Any]:
    return {
        **common_record(
            evidence_id,
            source_refs=[source_id],
        ),
        "schema_version": "research-evidence/v1",
        "evidence_id": evidence_id,
        "question_ids": ["RQ-000001"],
        "source_id": source_id,
        "source_sha256": source_sha256,
        "locator": "line 2",
        "representation": "PARAPHRASE",
        "polarity": polarity,
        "content": text,
        "content_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "extracted_at": RECORDED_AT,
        "limitations": ["Synthetic offline fixture."],
    }


def claim(
    *,
    support: list[str] | None = None,
    contradictions: list[str] | None = None,
    status: str = "CANDIDATE",
) -> dict[str, Any]:
    support_ids = support if support is not None else ["EVD-000001"]
    contradiction_ids = contradictions or []
    source_refs = ["SRC-000001"]
    evidence_refs = list(support_ids)
    if contradiction_ids:
        source_refs.append("SRC-000003")
        evidence_refs.append("EVD-000003")
    result = {
        **common_record(
            "CLM-000001",
            source_refs=source_refs,
            evidence_refs=evidence_refs,
        ),
        "schema_version": "research-claim/v1",
        "claim_id": "CLM-000001",
        "question_ids": ["RQ-000001"],
        "claim_type": "SOURCE_FACT",
        "text": "A valid start signal causes one green pulse under the stated fixture conditions.",
        "scope": {
            "include": ["One non-repeated valid start signal in the synthetic fixture."],
            "exclude": ["Rapidly repeated signals and all real products or providers."],
        },
        "support_evidence_ids": support_ids,
        "contradiction_ids": contradiction_ids,
        "confidence": {
            "source_fidelity": "HIGH",
            "scope_match": "EXACT",
            "freshness": "CURRENT",
            "corroboration": "MULTIPLE_INDEPENDENT" if len(support_ids) > 1 else "SINGLE",
            "empirical_support": "STATIC",
            "contradiction": "RESOLVED" if contradiction_ids else "NONE_KNOWN",
            "rationale": "Bounded synthetic source records support this scoped claim.",
        },
        "author": {
            "actor_id": "agent:research-author",
            "session_id": "session:author-001",
        },
        "status": status,
        "unknowns": ["Rapidly repeated signals may differ."],
    }
    return result


def contradiction() -> dict[str, Any]:
    return {
        **common_record(
            "CTR-000001",
            source_refs=["SRC-000003"],
            evidence_refs=["EVD-000003"],
        ),
        "schema_version": "research-contradiction/v1",
        "contradiction_id": "CTR-000001",
        "claim_id": "CLM-000001",
        "evidence_ids": ["EVD-000003"],
        "description": "Rapid repetition may produce two pulses.",
        "severity": "MEDIUM",
        "status": "ACCEPTED_UNCERTAINTY",
        "resolution": "Limit the conclusion to non-repeated valid signals.",
        "resolution_authority_id": "person:owner",
        "resolved_at": RECORDED_AT,
    }


def verification(
    claim_record: dict[str, Any],
    *,
    packet_ref: dict[str, Any] | None = None,
    outcome: str = "PASS",
    nonpass_check: str = "entailment",
    provider_conformance_path: Path | None = None,
) -> dict[str, Any]:
    conformance = provider_conformance()
    conformance_sha256 = canonical_sha256(conformance)
    if provider_conformance_path is not None:
        conformance_bytes = provider_conformance_path.read_bytes()
        conformance = json.loads(conformance_bytes.decode("utf-8"))
        conformance_sha256 = hashlib.sha256(conformance_bytes).hexdigest()
    subject = conformance["attestation_subject"]
    packet = copy.deepcopy(
        packet_ref
        or {
            "packet_id": "VPK-000001",
            "path": "verification-packets/VPK-000001.json",
            "sha256": "4" * 64,
            "byte_length": 1024,
        }
    )
    source_ids = sorted(claim_record["source_refs"])
    evidence_ids = sorted(claim_record["evidence_refs"])
    contradiction_ids = sorted(claim_record["contradiction_ids"])
    support_ids = sorted(claim_record["support_evidence_ids"])
    support_source_ids = source_ids[: len(support_ids)]
    checks = {
        "entailment": {
            "status": "PASS",
            "reason": "The deterministic offline oracle accepts the synthetic entailment fixture.",
            "relevant_ids": [claim_record["claim_id"], *support_ids],
        },
        "scope_match": {
            "status": "PASS",
            "reason": "The claim states explicit included and excluded synthetic scope.",
            "relevant_ids": [claim_record["claim_id"]],
        },
        "citation_resolution": {
            "status": "PASS",
            "reason": "Every packet reference resolves to an exact canonical fixture record.",
            "relevant_ids": sorted([*source_ids, *evidence_ids, *contradiction_ids]),
        },
        "source_admission": {
            "status": "PASS",
            "reason": "The synthetic sources are retrieved and admitted for evidence.",
            "relevant_ids": source_ids,
        },
        "custody_integrity": {
            "status": "PASS",
            "reason": "The synthetic retained objects pass digest readback.",
            "relevant_ids": source_ids,
        },
        "freshness": {
            "status": "PASS",
            "reason": "The synthetic sources are current at the confirmed as-of boundary.",
            "relevant_ids": source_ids,
        },
        "corroboration": {
            "status": "PASS",
            "reason": "The confirmed LOW-risk fixture requires one admitted supporting source.",
            "relevant_ids": support_source_ids,
        },
        "contradictions_considered": {
            "status": "PASS",
            "reason": "Every contradiction linked by the claim is present in the packet.",
            "relevant_ids": contradiction_ids,
        },
    }
    if outcome != "PASS":
        checks[nonpass_check]["status"] = outcome
    result = {
        **common_record(
            "VER-000001",
            source_refs=source_ids,
            evidence_refs=evidence_ids,
            lifecycle_status="ACCEPTED",
        ),
        "schema_version": "research-verification/v1",
        "verification_id": "VER-000001",
        "claim_id": claim_record["claim_id"],
        "packet_ref": packet,
        "claim_binding": {
            "claim_id": claim_record["claim_id"],
            "record_version": claim_record["record_version"],
            "claim_sha256": canonical_sha256(claim_record),
        },
        "reference_sets": {
            "source_ids": source_ids,
            "evidence_ids": evidence_ids,
            "contradiction_ids": contradiction_ids,
        },
        "verifier": {
            "actor_id": "agent:blind-verifier",
            "session_id": "session:independent-001",
            "kind": "OFFLINE_TEST_HARNESS",
            "provider": "OFFLINE_TEST_HARNESS",
            "model": "DETERMINISTIC_ORACLE",
            "provider_version": subject["installed_version"],
            "adapter_sha256": subject["adapter_sha256"],
            "profile_sha256": "6" * 64,
        },
        "provider_conformance": {
            "attestation_id": conformance["attestation_id"],
            "attestation_sha256": conformance_sha256,
        },
        "session_binding": {
            "parent_session_id": "session:research-lead-001",
            "child_session_id": "session:independent-001",
            "context_mode": "PACKET_ONLY",
        },
        "launched_at": RECORDED_AT,
        "completed_at": RECORDED_AT,
        "raw_result_sha256": "0" * 64,
        "broker_launch_receipt_sha256": "0" * 64,
        "checks": checks,
        "outcome": outcome,
        "limitations": [
            "OFFLINE_TEST_HARNESS proves Core contract behavior only; it does not establish Claude Code or Codex conformance."
        ],
    }
    result["broker_launch_receipt_sha256"] = canonical_sha256(
        {
            "launched_at": result["launched_at"],
            "packet_ref": result["packet_ref"],
            "schema_version": "offline-verification-launch-receipt/v1",
            "session_binding": result["session_binding"],
            "verifier": result["verifier"],
        }
    )
    result["raw_result_sha256"] = canonical_sha256(
        {
            "checks": result["checks"],
            "claim_binding": result["claim_binding"],
            "completed_at": result["completed_at"],
            "outcome": result["outcome"],
            "packet_ref": result["packet_ref"],
            "reference_sets": result["reference_sets"],
            "schema_version": "offline-verification-result/v1",
        }
    )
    return result


def synthesis(*, include_claim: bool = True) -> dict[str, Any]:
    claim_ids = ["CLM-000001"] if include_claim else []
    assertions = (
        [
            {
                "text": "The synthetic sources support one pulse under bounded conditions.",
                "claim_ids": ["CLM-000001"],
            }
        ]
        if include_claim
        else []
    )
    return {
        **common_record(
            "SYN-000001",
            source_refs=["SRC-000001"],
            evidence_refs=["EVD-000001"],
        ),
        "schema_version": "research-synthesis/v1",
        "synthesis_id": "SYN-000001",
        "question_dispositions": [
            {
                "question_id": "RQ-000001",
                "disposition": "ANSWERED" if include_claim else "UNRESOLVED",
                "claim_ids": claim_ids,
                "reason": "Synthetic evidence was checked." if include_claim else "No admitted evidence.",
            }
        ],
        "assertions": assertions,
        "limitations": ["No real provider or external source was used."],
        "conclusion_status": "PROPOSED",
        "outcome": "READY" if include_claim else "NEEDS_DECISION",
        "synthesis_method": "Claim-ID-bound deterministic fixture assembly.",
    }


def handoff(
    synthesis_sha256: str,
    *,
    run_id: str = "RUN-000001",
    request_id: str = "RSR-000001",
    request_sha256: str = "b" * 64,
    project_id: str = "project:offline-fixture",
    slug: str = "offline-fixture",
    outcome: str = "READY_TO_SEAL",
    context_sha256: str = "c" * 64,
) -> dict[str, Any]:
    return {
        **common_record(
            "HND-000001",
            run_id=run_id,
            source_refs=["SRC-000001"],
            evidence_refs=["EVD-000001"],
            lifecycle_status="ACCEPTED",
        ),
        "schema_version": "research-handoff/v1",
        "handoff_id": "HND-000001",
        "run_id": run_id,
        "location": {
            "project_id": project_id,
            "slug": slug,
            "run_id": run_id,
            "workflow": "research",
            "phase": "P9",
            "subphase": "ready-to-seal",
            "marker": "YOU ARE HERE",
        },
        "result": {
            "outcome": outcome,
            "reason_code": f"RESEARCH_{outcome}",
            "explanation": "Synthetic research is ready to return to its recorded caller.",
        },
        "questions": [
            {
                "question_id": "RQ-000001",
                "disposition": "ANSWERED",
                "reason": "The bounded synthetic question is supported by admitted evidence.",
            }
        ],
        "claims": {
            "total": 1,
            "by_class": {
                "SOURCE_FACT": 1,
                "STATIC_OBSERVATION": 0,
                "IMPORTED_EMPIRICAL_OBSERVATION": 0,
                "USER_OBSERVATION": 0,
                "INFERENCE": 0,
                "PROPOSAL": 0,
            },
            "by_readiness": {"NOT_READY": 0, "READY": 1, "STALE": 0},
            "by_dispute": {"NONE": 0, "OPEN": 0, "RESOLVED": 1},
            "by_verification": {
                "NOT_RUN": 0,
                "PASS": 1,
                "FAIL": 0,
                "COULD_NOT_RUN": 0,
                "INFRA_FAILURE": 0,
                "NOT_APPLICABLE": 0,
            },
            "material_claims": [
                {
                    "claim_id": "CLM-000001",
                    "limitations": ["The conclusion is bounded to the synthetic fixture."],
                }
            ],
        },
        "sources": {
            "total": 2,
            "by_admission": {
                "PENDING": 0,
                "ADMITTED_EVIDENCE": 2,
                "ADMITTED_CONTEXT": 0,
                "BIBLIOGRAPHY_ONLY": 0,
                "REJECTED": 0,
            },
            "by_retrieval": {
                "NOT_ATTEMPTED": 0,
                "RETRIEVED": 2,
                "PARTIAL": 0,
                "UNAVAILABLE": 0,
                "ACCESS_DENIED": 0,
                "ERROR": 0,
            },
            "by_custody": {
                "TRACKED_CAS": 2,
                "LOCAL_ONLY_CAS": 0,
                "EXTRACT_ONLY": 0,
                "NONE": 0,
            },
            "by_freshness": {"CURRENT": 2, "AGING": 0, "STALE": 0, "UNKNOWN": 0},
        },
        "contrary_evidence": {
            "open_count": 0,
            "resolved_count": 1,
            "contradictions": [
                {
                    "contradiction_id": "CTR-000001",
                    "status": "ACCEPTED_UNCERTAINTY",
                    "scope": "Rapidly repeated signals remain outside the bounded conclusion.",
                }
            ],
            "uncovered_scope": [],
        },
        "exclusions": ["Real products and providers"],
        "budget": {
            "confirmed": {
                "profile": "quick",
                "limits": {
                    "atomic_questions": 1,
                    "research_lanes": 2,
                    "concurrent_workers": 2,
                    "discovery_queries": 4,
                    "admitted_sources": 4,
                    "external_tool_calls": 8,
                    "aggregate_model_tokens": 1000,
                    "context_bytes": 65536,
                    "elapsed_minutes": 5,
                    "retry_per_failed_lane": 1,
                },
                "overrides": [],
            },
            "actual": {
                "atomic_questions": 1,
                "research_lanes": 2,
                "concurrent_workers_peak": 0,
                "discovery_queries": 2,
                "admitted_sources": 2,
                "external_tool_calls": 0,
                "aggregate_model_tokens": 0,
                "context_bytes": 1024,
                "elapsed_minutes": 0,
                "retries": 0,
                "meter_mode": "BYTE_PROXY",
            },
        },
        "canonical_artifacts": [
            {
                "artifact_id": "SYN-000001",
                "version": "1",
                "path": "synthesis.jsonl",
                "lifecycle_status": "PROPOSED",
                "readiness_status": "READY",
                "verification_status": "NOT_APPLICABLE",
                "sha256": synthesis_sha256,
                "owner": "agent:research-lead",
            }
        ],
        "source_basis": [
            {
                "artifact_id": request_id,
                "version": "research-request/v1",
                "sha256": request_sha256,
            },
            {
                "artifact_id": f"{run_id}/context-manifest",
                "version": "research-context-manifest/v1",
                "sha256": context_sha256,
            },
        ],
        "validation": {
            "environment": {
                "runner": "python-unittest",
                "platform": "synthetic-offline",
                "provider_runtime": "NOT_APPLICABLE",
            },
            "checks": [
                {
                    "check": "synthetic-record-contract",
                    "status": "PASS",
                    "evidence_ids": ["EVD-000001"],
                }
            ],
            "checks_not_run": [],
        },
        "decisions": [],
        "custody": {
            "by_mode": {
                "TRACKED_CAS": 2,
                "LOCAL_ONLY_CAS": 0,
                "EXTRACT_ONLY": 0,
                "NONE": 0,
            },
            "unavailable_requirements": [],
        },
        "conclusion_status": "PROPOSED",
        "open_items": [],
        "next_action": {"provider": "neutral", "invocation": "return-to-caller"},
        "session_guidance": "Resume from sealed artifacts in a fresh session.",
        "authorities": {
            "requester_id": "person:requester",
            "phase_owner_id": "person:owner",
            "decision_authority_id": "person:owner",
            "confirming_authority_id": "person:requester",
            "escalation_owner_id": "person:owner",
        },
        "authority_fence": "Read this run; create a new run to refresh it.",
        "repair_route": {
            "owner": "research",
            "invocation": "Create and confirm a complete research-request/v1 file; no short refresh invocation is executable.",
        },
        "rendered_at": RECORDED_AT,
    }


def with_new_request_identity(request: dict[str, Any], number: int, slug: str) -> dict[str, Any]:
    result = copy.deepcopy(request)
    result["request_id"] = f"RSR-{number:06d}"
    result["slug"] = slug
    return result


def exact_file_sha256(path: Path) -> tuple[str, int]:
    content = path.read_bytes()
    return hashlib.sha256(content).hexdigest(), len(content)


def install_preflight_contract(
    store: Any,
    workspace: Path,
    request: dict[str, Any],
    request_digest: str,
    ref: Any,
) -> None:
    """Install a self-contained, explicitly offline P0 acceptance fixture."""

    adapter = workspace / "inputs" / "offline-provider-adapter.txt"
    adapter.parent.mkdir(parents=True, exist_ok=True)
    adapter.write_bytes(b"DevForgeAI deterministic offline Research harness v1\n")
    adapter_digest, _ = exact_file_sha256(adapter)
    adapter_relative = adapter.relative_to(workspace).as_posix()
    attestation = provider_conformance()
    attestation["attestation_subject"].update(
        {
            "adapter_path": adapter_relative,
            "adapter_sha256": adapter_digest,
        }
    )
    for capability in attestation["capabilities"]:
        for evidence_ref in capability["evidence"]:
            evidence_ref.update(
                {"path": adapter_relative, "sha256": adapter_digest}
            )
    for trial in attestation["trials"]:
        trial.update(
            {"evidence_path": adapter_relative, "evidence_sha256": adapter_digest}
        )
    store.append_record(ref.slug, ref.run_id, "provider-conformance", attestation)
    retained = ref.path / "provider-conformance.json"
    retained_digest, _ = exact_file_sha256(retained)
    gate = preflight(attestation)
    gate.update(
        {
            "preflight_id": f"{ref.run_id}/preflight",
            "run_id": ref.run_id,
            "request_id": request["request_id"],
            "request_sha256": request_digest,
        }
    )
    gate["provider_subject"] = copy.deepcopy(attestation["attestation_subject"])
    gate["attestation"].update(
        {
            "path": "provider-conformance.json",
            "sha256": retained_digest,
        }
    )
    gate["writer_lock"]["path"] = (
        f".devforgeai/research-locks/{ref.slug}.lock"
    )
    store.append_record(ref.slug, ref.run_id, "preflight", gate)


def install_context_contract(
    store: Any,
    workspace: Path,
    request: dict[str, Any],
    request_digest: str,
    ref: Any,
) -> dict[str, Any]:
    request_path = ref.path / "request.json"
    request_file_digest, request_size = exact_file_sha256(request_path)
    manifest = context_manifest()
    manifest.update(
        {
            "manifest_id": f"{ref.run_id}/context-manifest",
            "run_id": ref.run_id,
            "request_id": request["request_id"],
            "request_sha256": request_digest,
            "owner": request["authority"]["phase_owner_id"],
            "decision_authority": request["authority"]["decision_authority_id"],
            "declared_scope_exclusions": list(request["scope"]["exclude"]),
        }
    )
    manifest["context_budget"].update(
        {
            "limit": request["budget"]["limits"]["context_bytes"],
            "used": request_size,
        }
    )
    manifest["entries"][0].update(
        {
            "artifact_id": request["request_id"],
            "path": "request.json",
            "sha256": request_file_digest,
            "serialized_bytes": request_size,
        }
    )
    store.append_record(ref.slug, ref.run_id, "context-manifest", manifest)
    return manifest


def install_plan_contract(
    store: Any,
    workspace: Path,
    request: dict[str, Any],
    request_digest: str,
    ref: Any,
) -> dict[str, Any]:
    context_path = ref.path / "context-manifest.json"
    context_digest, _ = exact_file_sha256(context_path)
    request_path = ref.path / "request.json"
    request_file_digest, _ = exact_file_sha256(request_path)
    record = plan()
    question_id = request["questions"][0]["question_id"]
    record.update(
        {
            "plan_id": f"{ref.run_id}/plan",
            "run_id": ref.run_id,
            "request_id": request["request_id"],
            "request_sha256": request_digest,
            "risk_tier": request["risk_tier"],
            "owner": request["authority"]["phase_owner_id"],
            "decision_authority": request["authority"]["decision_authority_id"],
        }
    )
    record["context_manifest"] = {
        "manifest_id": f"{ref.run_id}/context-manifest",
        "sha256": context_digest,
    }
    record["question_plans"][0]["question_id"] = question_id
    record["question_plans"][0]["required_source_classes"] = list(
        request["source_policy"]["required_classes"]
    )
    record["question_plans"][0]["freshness_requirements"] = list(
        request["source_policy"]["freshness_requirements"]
    )
    record["question_plans"][0]["stop_conditions"] = list(
        request["stop_conditions"]
    )
    for lane in record["lanes"]:
        lane["question_ids"] = [question_id]
        lane["required_source_classes"] = list(
            request["source_policy"]["required_classes"]
        )
        lane["freshness_requirements"] = list(
            request["source_policy"]["freshness_requirements"]
        )
        lane["stop_conditions"] = list(request["stop_conditions"])
    for envelope in record["worker_envelopes"]:
        envelope["run_id"] = ref.run_id
        envelope["context_manifest"] = copy.deepcopy(record["context_manifest"])
        envelope["input_artifacts"][0].update(
            {
                "artifact_id": request["request_id"],
                "path": "request.json",
                "sha256": request_file_digest,
            }
        )
        envelope["network_policy"] = {
            "mode": request["execution_policy"]["network_policy"],
            "allowlist": list(request["execution_policy"]["network_allowlist"]),
        }
        envelope["budgets"]["model_tokens_or_bytes"] = 400
    record["budget"].update(
        {
            "profile": request["budget"]["profile"],
            "limits": copy.deepcopy(request["budget"]["limits"]),
        }
    )
    record["retry_policy"]["maximum_per_failed_lane"] = request["budget"][
        "limits"
    ]["retry_per_failed_lane"]
    store.append_record(ref.slug, ref.run_id, "plan", record)
    return record


def install_reconciliation_contract(
    store: Any,
    workspace: Path,
    request: dict[str, Any],
    ref: Any,
    *,
    query_ids: list[str],
    source_count: int,
    status: str = "PASS",
) -> dict[str, Any]:
    plan_path = ref.path / "plan.json"
    plan_digest, _ = exact_file_sha256(plan_path)
    record = reconciliation()
    record.update(
        {
            "reconciliation_id": f"{ref.run_id}/reconciliation",
            "run_id": ref.run_id,
            "owner": request["authority"]["phase_owner_id"],
            "decision_authority": request["authority"]["decision_authority_id"],
            "status": status,
        }
    )
    record["plan"] = {
        "plan_id": f"{ref.run_id}/plan",
        "sha256": plan_digest,
    }
    record["question_coverage"][0]["question_id"] = request["questions"][0][
        "question_id"
    ]
    query_records = {
        item["query_id"]: item
        for item in (
            json.loads(line)
            for line in (ref.path / "queries.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line
        )
    }
    query_ids_by_lane: dict[str, list[str]] = {}
    for query_id in query_ids:
        query_ids_by_lane.setdefault(
            query_records[query_id]["lane_id"], []
        ).append(query_id)
    accepted: list[str] = []
    aggregate = {
        "queries": 0,
        "sources": 0,
        "tool_calls": 0,
        "model_tokens_or_bytes": 0,
        "elapsed_minutes": 0,
        "retries": 0,
    }
    for number, lane_result in enumerate(record["lane_results"], 1):
        lane_result["accepted_record_ids"] = sorted(
            query_ids_by_lane.get(lane_result["lane_id"], [])
        )
        accepted.extend(lane_result["accepted_record_ids"])
        lane_result["usage"] = {
            "queries": len(lane_result["accepted_record_ids"]),
            "sources": source_count if number == 1 else 0,
            "tool_calls": len(lane_result["accepted_record_ids"]),
            "model_tokens_or_bytes": 0,
            "elapsed_minutes": 0,
            "retries": 0,
        }
        if status != "PASS" and number == 2:
            lane_result["terminal_status"] = "FAILED"
        artifact = ref.path / f"workers/lane-{number:06d}.json"
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_bytes(
            json.dumps(
                {
                    "lane_id": lane_result["lane_id"],
                    "schema_version": "synthetic-research-lane-result/v1",
                    "status": lane_result["terminal_status"],
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            + b"\n"
        )
        artifact_digest, _ = exact_file_sha256(artifact)
        lane_result["result_artifacts"][0].update(
            {
                "path": artifact.relative_to(ref.path).as_posix(),
                "sha256": artifact_digest,
            }
        )
        for field in aggregate:
            aggregate[field] += lane_result["usage"][field]
    record["accepted_record_ids"] = accepted
    record["budget_use"] = aggregate
    record["concurrent_workers_peak"] = min(
        len(record["lane_results"]),
        request["budget"]["limits"]["concurrent_workers"],
    )
    if status != "PASS":
        record["budget_within_limits"] = True
    store.append_record(ref.slug, ref.run_id, "reconciliation", record)
    return record
