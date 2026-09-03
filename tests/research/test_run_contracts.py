from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from devforgeai.research.run_contracts import (
    canonical_json_sha256,
    validate_context_manifest_contract,
    validate_plan_contract,
    validate_preflight_contract,
    validate_reconciliation_contract,
    validate_request_run_contract,
    validate_run_contracts,
    validate_success_state_contract,
)
from tests.research import _fixtures as fx


def _bytes(value: dict) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8") + b"\n"


def _write(path: Path, value: dict) -> tuple[str, int]:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = _bytes(value)
    path.write_bytes(content)
    return hashlib.sha256(content).hexdigest(), len(content)


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _state_event(number: int, from_phase: str | None, to_phase: str, previous: str | None) -> dict:
    reason_code = "RUN_OPENED" if number == 0 else "READY_TO_SEAL" if to_phase == "P9" else "PHASE_ADVANCE"
    return {
        **fx.common_record(
            f"EVT-{number + 1:06d}", lifecycle_status="ACCEPTED"
        ),
        "schema_version": "research-state-event/v1",
        "event_id": f"EVT-{number + 1:06d}",
        "sequence": number,
        "previous_event_sha256": previous,
        "event_type": "PHASE_TRANSITION",
        "from_phase": from_phase,
        "to_phase": to_phase,
        "actor_id": "core:research-store",
        "reason_code": reason_code,
        "reason": "Synthetic semantic-contract transition.",
        "occurred_at": fx.RECORDED_AT,
    }


def _build_run(workspace: Path) -> Path:
    run = workspace / ".devforgeai/research-staging/offline-fixture/RUN-000001"
    run.mkdir(parents=True)

    request = fx.load_request()
    request_digest = canonical_json_sha256(request)
    request_file_digest, request_length = _write(run / "request.json", request)
    _write(run / "run.json", fx.run_header(request_digest))

    attestation = fx.provider_conformance()
    attestation_digest, _ = _write(run / "provider-conformance.json", attestation)
    preflight = fx.preflight(attestation)
    preflight["request_sha256"] = request_digest
    preflight["provider_subject"] = copy.deepcopy(attestation["attestation_subject"])
    preflight["attestation"].update(
        {
            "path": "provider-conformance.json",
            "sha256": attestation_digest,
        }
    )
    _write(run / "preflight.json", preflight)

    context = fx.context_manifest()
    context["request_sha256"] = request_digest
    context["context_budget"]["limit"] = request["budget"]["limits"]["context_bytes"]
    context["context_budget"]["used"] = request_length
    context["entries"][0].update(
        {
            "path": "request.json",
            "sha256": request_file_digest,
            "serialized_bytes": request_length,
        }
    )
    context_digest, _ = _write(run / "context-manifest.json", context)

    plan = fx.plan()
    plan["request_sha256"] = request_digest
    plan["context_manifest"]["sha256"] = context_digest
    plan["decision_authority"] = request["authority"]["decision_authority_id"]
    for envelope in plan["worker_envelopes"]:
        envelope["context_manifest"]["sha256"] = context_digest
        envelope["input_artifacts"][0].update(
            {
                "path": "request.json",
                "sha256": request_file_digest,
            }
        )
        envelope["budgets"]["model_tokens_or_bytes"] = 400
    plan_digest, _ = _write(run / "plan.json", plan)

    reconciliation = fx.reconciliation()
    reconciliation["plan"]["sha256"] = plan_digest
    aggregate = {
        "queries": 0,
        "sources": 0,
        "tool_calls": 0,
        "model_tokens_or_bytes": 0,
        "elapsed_minutes": 0,
        "retries": 0,
    }
    for number, result in enumerate(reconciliation["lane_results"], 1):
        artifact = run / f"workers/lane-{number:06d}.json"
        artifact_digest, _ = _write(
            artifact,
            {"schema_version": "synthetic-research-lane-result/v1", "lane": number},
        )
        result["result_artifacts"][0].update(
            {
                "path": artifact.relative_to(run).as_posix(),
                "sha256": artifact_digest,
            }
        )
        result["usage"]["model_tokens_or_bytes"] = 100
        for field in aggregate:
            aggregate[field] += result["usage"][field]
    reconciliation["budget_use"] = aggregate
    _write(run / "reconciliation.json", reconciliation)
    (run / "queries.jsonl").write_bytes(
        _bytes(fx.query()) + _bytes(fx.challenge_query())
    )

    previous = None
    events = []
    from_phase = None
    for number in range(10):
        to_phase = f"P{number}"
        event = _state_event(number, from_phase, to_phase, previous)
        events.append(event)
        previous = canonical_json_sha256(event)
        from_phase = to_phase
    (run / "state.jsonl").write_bytes(b"".join(_bytes(event) for event in events))

    validation = fx.validation()
    validation["subject_files"] = [
        {
            "path": "request.json",
            "sha256": request_file_digest,
            "byte_length": request_length,
        }
    ]
    _write(run / "validation.json", validation)
    return run


class RunContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temporary.name)
        self.run = _build_run(self.workspace)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_complete_semantic_fixture_passes_every_contract(self) -> None:
        self.assertEqual(
            validate_run_contracts(
                self.workspace,
                self.run,
                expected_run_id="RUN-000001",
                as_of_utc=fx.RECORDED_AT,
            ),
            [],
        )

    def test_request_and_run_are_bound_to_exact_confirmed_bytes_and_authority(self) -> None:
        header = _read(self.run / "run.json")
        header["confirmation_binding"]["request_sha256"] = "0" * 64
        header["confirmation_binding"]["confirming_authority"] = "person:other"
        _write(self.run / "run.json", header)
        errors = validate_request_run_contract(self.workspace, self.run)
        self.assertIn("E_RUN_REQUEST_DIGEST", errors)
        self.assertIn("E_RUN_CONFIRMING_AUTHORITY", errors)

    def test_preflight_checks_exact_attestation_file_subject_and_freshness(self) -> None:
        preflight = _read(self.run / "preflight.json")
        preflight["attestation"]["sha256"] = "0" * 64
        preflight["provider_subject"]["installed_version"] = "other"
        _write(self.run / "preflight.json", preflight)
        errors = validate_preflight_contract(
            self.workspace,
            self.run,
            as_of_utc="2100-01-01T00:00:00Z",
        )
        self.assertIn("E_PREFLIGHT_ATTESTATION_SUBJECT", errors)
        self.assertTrue(any(value.startswith("E_PREFLIGHT_ATTESTATION_DIGEST:") for value in errors))
        self.assertIn("E_PREFLIGHT_ATTESTATION_STALE", errors)

    def test_preflight_cannot_make_a_fixed_capability_optional(self) -> None:
        preflight = _read(self.run / "preflight.json")
        preflight["capability_checks"][0]["required"] = False
        preflight["capability_checks"][0]["status"] = "NOT_PROBED"
        _write(self.run / "preflight.json", preflight)
        errors = validate_preflight_contract(self.workspace, self.run)
        self.assertIn(
            "E_PREFLIGHT_CAPABILITY_NOT_REQUIRED:SOURCE_OPEN",
            errors,
        )

    def test_preflight_attested_capabilities_are_exactly_bound(self) -> None:
        preflight = _read(self.run / "preflight.json")
        preflight["capability_checks"][0]["basis"] = "DETERMINISTIC_LOCAL_CHECK"
        preflight["capability_checks"][0]["evidence_artifact_ids"] = ["invented"]
        _write(self.run / "preflight.json", preflight)
        attestation = _read(self.run / "provider-conformance.json")
        attestation["capabilities"] = [
            item
            for item in attestation["capabilities"]
            if item["capability_id"] != "FRESH_ISOLATED_WORKER"
        ]
        _write(self.run / "provider-conformance.json", attestation)
        errors = validate_preflight_contract(self.workspace, self.run)
        self.assertIn("E_PREFLIGHT_CAPABILITY_BASIS:SOURCE_OPEN", errors)
        self.assertIn("E_PREFLIGHT_ATTESTED_CAPABILITY_EVIDENCE:SOURCE_OPEN", errors)
        self.assertIn(
            "E_PREFLIGHT_ATTESTED_CAPABILITY_MISSING:FRESH_ISOLATED_WORKERS",
            errors,
        )

    def test_context_accounts_for_existing_refs_exact_bytes_and_declared_budget(self) -> None:
        request = _read(self.run / "request.json")
        request["existing_refs"] = [
            {
                "kind": "SOURCE",
                "artifact_id": "SRC-000099",
                "version": "1",
                "sha256": "9" * 64,
            }
        ]
        request_digest = canonical_json_sha256(request)
        _write(self.run / "request.json", request)
        header = _read(self.run / "run.json")
        header["confirmation_binding"]["request_sha256"] = request_digest
        _write(self.run / "run.json", header)
        manifest = _read(self.run / "context-manifest.json")
        manifest["request_sha256"] = request_digest
        manifest["context_budget"]["used"] += 1
        _write(self.run / "context-manifest.json", manifest)
        errors = validate_context_manifest_contract(self.workspace, self.run)
        self.assertIn("E_CONTEXT_EXISTING_REF_COUNT:SRC-000099", errors)
        self.assertIn("E_CONTEXT_BUDGET_ACCOUNTING", errors)
        self.assertTrue(any(value.startswith("E_CONTEXT_ENTRY_DIGEST:") for value in errors))

    def test_plan_closes_lane_envelope_barrier_and_budget_relations(self) -> None:
        plan = _read(self.run / "plan.json")
        plan["question_plans"][0]["contrary_lane_ids"] = ["LANE-000001"]
        plan["worker_envelopes"][0]["barrier_id"] = "BAR-999999"
        plan["worker_envelopes"][0]["budgets"]["model_tokens_or_bytes"] = 2000
        _write(self.run / "plan.json", plan)
        errors = validate_plan_contract(self.workspace, self.run)
        self.assertIn("E_PLAN_LANE_POLARITY_OVERLAP:RQ-000001", errors)
        self.assertIn("E_PLAN_ENVELOPE_BARRIER_BINDING:ENV-000001", errors)
        self.assertIn("E_PLAN_MODEL_BUDGET", errors)

    def test_plan_envelopes_bind_the_exact_run(self) -> None:
        plan = _read(self.run / "plan.json")
        plan["worker_envelopes"][0]["run_id"] = "RUN-999999"
        _write(self.run / "plan.json", plan)
        self.assertIn(
            "E_PLAN_ENVELOPE_RUN_BINDING:ENV-000001",
            validate_plan_contract(self.workspace, self.run),
        )

    def test_plan_binds_request_source_freshness_and_stop_policies(self) -> None:
        plan = _read(self.run / "plan.json")
        plan["question_plans"][0]["required_source_classes"] = ["SECONDARY"]
        plan["question_plans"][0]["freshness_requirements"] = ["Different"]
        plan["question_plans"][0]["stop_conditions"] = ["Different"]
        plan["lanes"][0]["required_source_classes"] = ["SECONDARY"]
        plan["lanes"][0]["freshness_requirements"] = ["Different"]
        plan["lanes"][0]["stop_conditions"] = ["Different"]
        _write(self.run / "plan.json", plan)
        errors = validate_plan_contract(self.workspace, self.run)
        self.assertIn("E_PLAN_SOURCE_POLICY:RQ-000001", errors)
        self.assertIn("E_PLAN_FRESHNESS_REQUIREMENTS:RQ-000001", errors)
        self.assertIn("E_PLAN_STOP_CONDITIONS:RQ-000001", errors)
        self.assertIn("E_PLAN_LANE_SOURCE_POLICY:LANE-000001", errors)
        self.assertIn(
            "E_PLAN_LANE_FRESHNESS_REQUIREMENTS:LANE-000001",
            errors,
        )
        self.assertIn("E_PLAN_LANE_STOP_CONDITIONS:LANE-000001", errors)

    def test_reconciliation_requires_exact_plan_lanes_artifacts_and_budget(self) -> None:
        reconciliation = _read(self.run / "reconciliation.json")
        reconciliation["lane_results"] = reconciliation["lane_results"][:1]
        reconciliation["budget_use"]["queries"] = 999
        reconciliation["majority_vote_used"] = True
        _write(self.run / "reconciliation.json", reconciliation)
        errors = validate_reconciliation_contract(self.workspace, self.run)
        self.assertIn("E_RECONCILIATION_LANE_ACCOUNTING", errors)
        self.assertIn("E_RECONCILIATION_BUDGET_ACCOUNTING", errors)
        self.assertIn("E_RECONCILIATION_MAJORITY_VOTE", errors)

        artifact = self.run / "workers/lane-000001.json"
        artifact.write_bytes(artifact.read_bytes() + b"tampered")
        errors = validate_reconciliation_contract(self.workspace, self.run)
        self.assertTrue(any(value.startswith("E_RECONCILIATION_RESULT_DIGEST:") for value in errors))

    def test_reconciliation_pass_rejects_a_failed_lane(self) -> None:
        reconciliation = _read(self.run / "reconciliation.json")
        reconciliation["lane_results"][1]["terminal_status"] = "FAILED"
        _write(self.run / "reconciliation.json", reconciliation)
        errors = validate_reconciliation_contract(self.workspace, self.run)
        self.assertIn(
            "E_RECONCILIATION_CONTRARY_TERMINAL:RQ-000001",
            errors,
        )
        self.assertIn(
            "E_RECONCILIATION_PASS_LANE_NOT_RETURNED:LANE-000002",
            errors,
        )

    def test_reconciliation_binds_every_query_exactly_once_to_its_lane(self) -> None:
        reconciliation = _read(self.run / "reconciliation.json")
        reconciliation["lane_results"][0]["accepted_record_ids"] = [
            "QRY-000002"
        ]
        reconciliation["lane_results"][1]["accepted_record_ids"] = [
            "QRY-000001"
        ]
        _write(self.run / "reconciliation.json", reconciliation)
        errors = validate_reconciliation_contract(self.workspace, self.run)
        self.assertIn(
            "E_RECONCILIATION_ACCEPTED_QUERY_LANE:QRY-000001",
            errors,
        )
        self.assertIn(
            "E_RECONCILIATION_ACCEPTED_QUERY_LANE:QRY-000002",
            errors,
        )

        reconciliation = _read(self.run / "reconciliation.json")
        reconciliation["lane_results"][0]["accepted_record_ids"] = []
        reconciliation["accepted_record_ids"] = ["QRY-000002"]
        _write(self.run / "reconciliation.json", reconciliation)
        errors = validate_reconciliation_contract(self.workspace, self.run)
        self.assertIn("E_RECONCILIATION_QUERY_ACCOUNTING", errors)

    def test_reconciliation_lane_query_usage_is_derived(self) -> None:
        reconciliation = _read(self.run / "reconciliation.json")
        reconciliation["lane_results"][0]["usage"]["queries"] = 0
        reconciliation["lane_results"][1]["usage"]["queries"] = 2
        _write(self.run / "reconciliation.json", reconciliation)
        errors = validate_reconciliation_contract(self.workspace, self.run)
        self.assertIn(
            "E_RECONCILIATION_LANE_QUERY_ACCOUNTING:LANE-000001",
            errors,
        )
        self.assertIn(
            "E_RECONCILIATION_LANE_QUERY_ACCOUNTING:LANE-000002",
            errors,
        )

    def test_success_state_must_end_p9_ready_to_seal_and_never_complete(self) -> None:
        events = [json.loads(line) for line in (self.run / "state.jsonl").read_text().splitlines()]
        events[-1]["reason_code"] = "COMPLETE"
        (self.run / "state.jsonl").write_bytes(b"".join(_bytes(event) for event in events))
        errors = validate_success_state_contract(self.workspace, self.run)
        self.assertIn("E_STATE_PRESEAL_COMPLETE:9", errors)
        self.assertIn("E_STATE_NOT_READY_TO_SEAL", errors)

    def test_validation_subject_hash_is_exact(self) -> None:
        request_path = self.run / "request.json"
        request_path.write_bytes(request_path.read_bytes() + b" ")
        errors = validate_success_state_contract(self.workspace, self.run)
        self.assertTrue(any(value.startswith("E_VALIDATION_SUBJECT_DIGEST:") for value in errors))
        self.assertTrue(any(value.startswith("E_VALIDATION_SUBJECT_LENGTH:") for value in errors))


if __name__ == "__main__":
    unittest.main()
