from __future__ import annotations

import copy
import hashlib
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker, ValidationError

from tests.research import _fixtures as fx


SCHEMA_ROOT = Path(__file__).parents[2] / "schemas" / "research" / "v1"


def validator(name: str) -> Draft202012Validator:
    schema = json.loads((SCHEMA_ROOT / f"{name}.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


class ResearchSchemaTests(unittest.TestCase):
    def assert_valid(self, name: str, instance: dict) -> None:
        validator(name).validate(instance)

    def assert_invalid(self, name: str, instance: dict) -> None:
        with self.assertRaises(ValidationError):
            validator(name).validate(instance)

    def full_source(self) -> dict:
        path = fx.FIXTURES / "source-primary.txt"
        content = path.read_bytes()
        record = fx.source_metadata(
            "SRC-000001", "source-primary.txt", publisher="Synthetic Standards Body"
        )
        digest = hashlib.sha256(content).hexdigest()
        record["custody"] = {
            "mode": "TRACKED_CAS",
            "sha256": digest,
            "byte_length": len(content),
            "object_path": f"docs/research/_cas/sha256/{digest[:2]}/{digest}",
        }
        return record

    def test_all_schema_documents_are_valid_draft_2020_12(self) -> None:
        names = {path.stem.removesuffix(".schema") for path in SCHEMA_ROOT.glob("*.schema.json")}
        self.assertEqual(
            names,
            {
                "request",
                "question",
                "query",
                "source",
                "evidence",
                "claim",
                "contradiction",
                "verification-packet",
                "verification",
                "synthesis",
                "state-event",
                "run",
                "provider-conformance",
                "preflight",
                "context-manifest",
                "plan",
                "decision",
                "reconciliation",
                "validation",
                "handoff",
                "registry",
            },
        )
        for name in names:
            validator(name)

    def test_representative_records_validate(self) -> None:
        source = self.full_source()
        claim = fx.claim(contradictions=["CTR-000001"])
        self.assert_valid("request", fx.load_request())
        self.assert_valid("run", fx.run_header())
        attestation = fx.provider_conformance()
        self.assert_valid("provider-conformance", attestation)
        self.assert_valid("preflight", fx.preflight(attestation))
        self.assert_valid("context-manifest", fx.context_manifest())
        self.assert_valid("plan", fx.plan())
        self.assert_valid("decision", fx.decision())
        self.assert_valid("reconciliation", fx.reconciliation())
        self.assert_valid("validation", fx.validation())
        self.assert_valid("question", fx.question())
        self.assert_valid("query", fx.query())
        self.assert_valid("source", source)
        self.assert_valid(
            "evidence",
            fx.evidence(
                "EVD-000001",
                "SRC-000001",
                source["custody"]["sha256"],
                "The source states that one pulse follows a valid signal.",
            ),
        )
        self.assert_valid("claim", claim)
        self.assert_valid("contradiction", fx.contradiction())
        self.assert_valid("verification", fx.verification(claim))
        packet_claim = fx.claim()
        packet_request = fx.load_request()
        packet_source = self.full_source()
        packet_evidence = fx.evidence(
            "EVD-000001",
            "SRC-000001",
            packet_source["custody"]["sha256"],
            "The source states that one pulse follows a valid signal.",
        )
        self.assert_valid(
            "verification-packet",
            {
                "schema_version": "research-verification-packet/v1",
                "packet_id": "VPK-000001",
                "run_id": "RUN-000001",
                "request_binding": {
                    "request_id": packet_request["request_id"],
                    "request_sha256": fx.canonical_sha256(packet_request),
                    "request": packet_request,
                },
                "claim": {
                    "claim_id": packet_claim["claim_id"],
                    "record_version": packet_claim["record_version"],
                    "claim_sha256": fx.canonical_sha256(packet_claim),
                    "text": packet_claim["text"],
                    "claim_type": packet_claim["claim_type"],
                    "scope": packet_claim["scope"],
                },
                "sources": [packet_source],
                "evidence": [packet_evidence],
                "contradictions": [],
            },
        )
        self.assert_valid("synthesis", fx.synthesis())
        self.assert_valid(
            "state-event",
            {
                **fx.common_record("EVT-000001", lifecycle_status="ACCEPTED"),
                "schema_version": "research-state-event/v1",
                "event_id": "EVT-000001",
                "run_id": "RUN-000001",
                "sequence": 0,
                "previous_event_sha256": None,
                "event_type": "PHASE_TRANSITION",
                "from_phase": None,
                "to_phase": "P0",
                "actor_id": "core:research-store",
                "reason_code": "RUN_OPENED",
                "reason": "Run opened from a confirmed request digest.",
                "occurred_at": fx.RECORDED_AT,
            },
        )
        digest = "a" * 64
        handoff = fx.handoff(digest)
        handoff["location"]["phase"] = "P9"
        handoff["location"]["subphase"] = "ready-to-seal"
        self.assert_valid("handoff", handoff)
        self.assert_valid(
            "registry",
            {
                "schema_version": "research-registry-entry/v1",
                "sequence": 1,
                "run_id": "RUN-000001",
                "request_id": "RSR-000001",
                "slug": "offline-fixture",
                "canonical_path": "docs/research/offline-fixture/runs/RUN-000001",
                "lifecycle_status": "ACCEPTED",
                "readiness_status": "READY",
                "outcome": "COMPLETE",
                "manifest_sha256": digest,
                "previous_entry_sha256": None,
                "entry_sha256": "b" * 64,
                "sealed_at_utc": fx.RECORDED_AT,
                "supersedes_run_ids": [],
                "stale_if": [],
            },
        )

    def test_persistence_requires_explicit_authority(self) -> None:
        request = fx.load_request()
        request["authority"]["persistence_authorized"] = False
        self.assert_invalid("request", request)

    def test_request_context_budget_cannot_exceed_deep_profile_ceiling(self) -> None:
        request = fx.load_request()
        request["budget"]["limits"]["context_bytes"] = 262145
        self.assert_invalid("request", request)

    def test_run_confirmation_method_and_work_order_digest_are_consistent(self) -> None:
        record = fx.run_header()
        record["confirmation_binding"]["work_order_sha256"] = "a" * 64
        self.assert_invalid("run", record)

        record = fx.run_header()
        record["confirmation_binding"]["method"] = "WORK_ORDER"
        self.assert_invalid("run", record)

        record["confirmation_binding"]["work_order_sha256"] = "a" * 64
        self.assert_valid("run", record)

    def test_search_result_is_discovery_only(self) -> None:
        record = fx.query()
        record["results"][0]["discovery_only"] = False
        self.assert_invalid("query", record)

    def test_query_requires_plan_lane_and_worker_envelope_ids(self) -> None:
        record = fx.query()
        del record["lane_id"]
        self.assert_invalid("query", record)

        record = fx.query()
        del record["worker_envelope_id"]
        self.assert_invalid("query", record)

        record = fx.query()
        record["lane_id"] = "DIRECT"
        self.assert_invalid("query", record)

    def test_query_candidates_require_stable_query_local_ids(self) -> None:
        record = fx.query()
        del record["results"][0]["candidate_id"]
        self.assert_invalid("query", record)

        for invalid_id in (
            "CAND-000001",
            "QRY-000001",
            "QRY-000001-CAND-1",
            "SRC-000001-CAND-000001",
        ):
            with self.subTest(candidate_id=invalid_id):
                record = fx.query()
                record["results"][0]["candidate_id"] = invalid_id
                self.assert_invalid("query", record)

    def test_query_candidates_require_closed_terminal_dispositions_and_reasons(self) -> None:
        terminal_dispositions = (
            "RETRIEVE",
            "BIBLIOGRAPHY_ONLY",
            "REJECTED",
            "UNAVAILABLE",
            "ACCESS_DENIED",
            "ERROR",
        )
        for disposition in terminal_dispositions:
            with self.subTest(disposition=disposition):
                record = fx.query()
                record["results"][0]["disposition"] = disposition
                self.assert_valid("query", record)

        for invalid_disposition in ("PENDING", "ADMITTED_EVIDENCE", ""):
            with self.subTest(disposition=invalid_disposition):
                record = fx.query()
                record["results"][0]["disposition"] = invalid_disposition
                self.assert_invalid("query", record)

        record = fx.query()
        del record["results"][0]["reason"]
        self.assert_invalid("query", record)
        record = fx.query()
        record["results"][0]["reason"] = ""
        self.assert_invalid("query", record)

    def test_source_links_owning_query_and_retrieved_candidate_separately(self) -> None:
        query = fx.query()
        source = self.full_source()
        self.assertEqual(source["query_ids"], [query["query_id"]])
        self.assertEqual(source["candidate_ids"], [query["results"][0]["candidate_id"]])
        self.assert_valid("query", query)
        self.assert_valid("source", source)

        del source["candidate_ids"]
        self.assert_invalid("source", source)

    def test_provider_attestation_cannot_launder_unrun_provider_trials(self) -> None:
        offline = fx.provider_conformance()
        self.assertEqual(
            offline["attestation_subject"]["provider_kind"], "OFFLINE_TEST_HARNESS"
        )
        self.assert_valid("provider-conformance", offline)

        claude = fx.provider_conformance(
            provider_kind="CLAUDE_CODE", status="NOT_EVALUATED"
        )
        self.assert_valid("provider-conformance", claude)
        wrong_runtime_suite = copy.deepcopy(claude)
        wrong_runtime_suite["fixture_suite"]["suite_version"] = "1.0.1"
        self.assert_invalid("provider-conformance", wrong_runtime_suite)
        claude["status"] = "SUPPORTED"
        claude["capabilities"][0]["status"] = "SUPPORTED"
        self.assert_invalid("provider-conformance", claude)

        wrong_offline_suite = copy.deepcopy(offline)
        wrong_offline_suite["fixture_suite"]["manifest_sha256"] = "0" * 64
        self.assert_invalid("provider-conformance", wrong_offline_suite)

        disguised = fx.provider_conformance()
        disguised["attestation_subject"]["provider_kind"] = "CODEX"
        self.assert_invalid("provider-conformance", disguised)

    def test_provider_fixture_suite_manifest_digests_are_exact(self) -> None:
        for suite in (
            fx.PROVIDER_RUNTIME_FIXTURE_SUITE,
            fx.OFFLINE_FIXTURE_SUITE,
        ):
            with self.subTest(suite_id=suite["suite_id"]):
                manifest = {
                    key: value
                    for key, value in suite.items()
                    if key != "manifest_sha256"
                }
                self.assertEqual(
                    fx.canonical_sha256(manifest), suite["manifest_sha256"]
                )

    def test_preflight_pass_requires_supported_attestation_and_capabilities(self) -> None:
        record = fx.preflight()
        record["attestation"]["status"] = "NOT_EVALUATED"
        self.assert_invalid("preflight", record)

        record = fx.preflight()
        record["capability_checks"][0]["status"] = "NOT_PROBED"
        self.assert_invalid("preflight", record)

        record = fx.preflight()
        record["writer_lock"]["status"] = "COLLISION"
        self.assert_invalid("preflight", record)

    def test_context_manifest_selected_entries_must_resolve_and_be_reusable(self) -> None:
        record = fx.context_manifest()
        record["entries"][0]["resolution_status"] = "DIGEST_MISMATCH"
        self.assert_invalid("context-manifest", record)

        record = fx.context_manifest()
        record["entries"][0]["applicability"] = "STALE"
        self.assert_invalid("context-manifest", record)

        record = fx.context_manifest()
        record["unresolved_ambiguities"] = [
            {
                "ambiguity_id": "AMB-000001",
                "description": "A material input is ambiguous.",
                "owner": "person:owner",
                "material": True,
            }
        ]
        self.assert_invalid("context-manifest", record)

    def test_plan_requires_direct_and_contrary_lanes_and_full_worker_envelopes(self) -> None:
        record = fx.plan()
        record["question_plans"][0]["contrary_lane_ids"] = []
        self.assert_invalid("plan", record)

        record = fx.plan()
        del record["worker_envelopes"][0]["conflict_reconciliation_policy"]
        self.assert_invalid("plan", record)

        record = fx.plan()
        del record["worker_envelopes"][0]["run_id"]
        self.assert_invalid("plan", record)

        record = fx.plan()
        record["reconciliation_rule"]["majority_vote_permitted"] = True
        self.assert_invalid("plan", record)

    def test_research_decision_cannot_waive_critical_specialist_review(self) -> None:
        record = fx.decision()
        record["decision_type"] = "PERMITTED_WAIVER"
        record["risk_tier"] = "CRITICAL"
        record["effective_until_utc"] = fx.FRESH_UNTIL
        record["waiver"] = {
            "policy_rule": "specialist-review",
            "applies_to": ["CLM-000001"],
            "residual_risk": "Critical-domain applicability is not established.",
            "review_trigger": "Before downstream use.",
        }
        self.assert_invalid("decision", record)

    def test_reconciliation_pass_requires_terminal_coverage_and_no_majority_vote(self) -> None:
        record = fx.reconciliation()
        record["question_coverage"][0]["contrary_terminal"] = False
        self.assert_invalid("reconciliation", record)

        record = fx.reconciliation()
        record["majority_vote_used"] = True
        self.assert_invalid("reconciliation", record)

        for invalid_id in (
            "SRC-000001",
            "EVD-000001",
            "CLM-000001",
            "CTR-000001",
        ):
            with self.subTest(accepted_record_id=invalid_id):
                record = fx.reconciliation()
                record["lane_results"][0]["accepted_record_ids"] = [invalid_id]
                record["accepted_record_ids"] = [invalid_id, "QRY-000002"]
                self.assert_invalid("reconciliation", record)

    def test_ready_to_seal_validation_cannot_hide_applicable_failure(self) -> None:
        record = fx.validation()
        record["checks"][0]["status"] = "FAIL"
        self.assert_invalid("validation", record)

        record = fx.validation()
        record["errors"] = ["E_SYNTHETIC_FAILURE"]
        self.assert_invalid("validation", record)

    def test_tracked_cas_requires_digest_length_and_object_path(self) -> None:
        record = self.full_source()
        del record["custody"]["sha256"]
        self.assert_invalid("source", record)

    def test_tracked_cas_rejects_retention_without_permission(self) -> None:
        record = self.full_source()
        record["retention_policy"]["retention_permitted"] = False
        self.assert_invalid("source", record)

    def test_retention_policy_basis_and_scan_counts_are_closed(self) -> None:
        record = self.full_source()
        record["retention_policy"]["redistribution_basis"] = "NONE"
        self.assert_invalid("source", record)
        record = self.full_source()
        record["retention_policy"]["sensitive_scan"]["findings_count"] = 1
        self.assert_invalid("source", record)
        record = self.full_source()
        record["retention_policy"]["sensitive_scan"].update(
            {"status": "FAIL", "findings_count": 0}
        )
        self.assert_invalid("source", record)

    def test_local_only_cas_allows_nonredistributable_retained_bytes(self) -> None:
        record = self.full_source()
        digest = record["custody"]["sha256"]
        record["custody"]["mode"] = "LOCAL_ONLY_CAS"
        record["custody"]["object_path"] = (
            f".devforgeai/research-cas/sha256/{digest[:2]}/{digest}"
        )
        record["retention_policy"].update(
            {
                "redistribution_basis": "NONE",
                "redistribution_reference": None,
                "data_classification": "INTERNAL",
            }
        )
        record["retention_policy"]["sensitive_scan"]["status"] = "NOT_RUN"
        self.assert_valid("source", record)

    def test_retrieval_timestamps_and_failure_reasons_are_semantic(self) -> None:
        not_attempted = self.full_source()
        not_attempted["retrieval"]["status"] = "NOT_ATTEMPTED"
        del not_attempted["retrieval"]["retrieved_at"]
        not_attempted["admission"] = "PENDING"
        self.assert_valid("source", not_attempted)

        partial = self.full_source()
        partial["retrieval"]["status"] = "PARTIAL"
        self.assert_invalid("source", partial)
        partial["retrieval"]["limitation"] = "Only the synthetic header was retained."
        partial["admission"] = "ADMITTED_CONTEXT"
        self.assert_valid("source", partial)

        unavailable = self.full_source()
        unavailable["retrieval"]["status"] = "ACCESS_DENIED"
        del unavailable["retrieval"]["retrieved_at"]
        unavailable["admission"] = "BIBLIOGRAPHY_ONLY"
        self.assert_invalid("source", unavailable)
        unavailable["retrieval"]["limitation"] = "Fixture access was denied."
        self.assert_valid("source", unavailable)

    def test_evidence_admission_requires_complete_retrieval(self) -> None:
        record = self.full_source()
        record["retrieval"]["status"] = "PARTIAL"
        record["retrieval"]["limitation"] = "Only part of the source was retrieved."
        self.assert_invalid("source", record)

    def test_freshness_status_requires_an_explicit_assessment_basis(self) -> None:
        record = self.full_source()
        del record["freshness"]["assessment_basis"]
        self.assert_invalid("source", record)
        record = self.full_source()
        record["freshness"]["rationale"] = ""
        self.assert_invalid("source", record)

    def test_p6_claim_cannot_self_declare_publishability_or_future_verification(self) -> None:
        record = fx.claim(support=[])
        record["status"] = "PUBLISHABLE"
        self.assert_invalid("claim", record)
        record = fx.claim()
        record["verification_ids"] = ["VER-000001"]
        self.assert_invalid("claim", record)

    def test_claim_requires_explicit_scope(self) -> None:
        record = fx.claim()
        del record["scope"]
        self.assert_invalid("claim", record)

    def test_conclusion_cannot_be_promoted_by_research(self) -> None:
        record = fx.synthesis()
        record["conclusion_status"] = "ACCEPTED"
        self.assert_invalid("synthesis", record)

    def test_canonical_handoff_is_preseal_and_cannot_predict_complete(self) -> None:
        record = fx.handoff("a" * 64)
        self.assertEqual(record["result"]["outcome"], "READY_TO_SEAL")
        self.assert_valid("handoff", record)
        record["result"]["outcome"] = "COMPLETE"
        self.assert_invalid("handoff", record)

    def test_canonical_handoff_excludes_post_seal_receipt_hashes(self) -> None:
        record = fx.handoff("a" * 64)
        record["manifest_sha256"] = "b" * 64
        self.assert_invalid("handoff", record)
        record = fx.handoff("a" * 64)
        record["registry_entry_sha256"] = "b" * 64
        self.assert_invalid("handoff", record)
        for path in (
            "handoff.json",
            "handoff.md",
            "MANIFEST.sha256",
            "docs/research/offline-fixture/registry.jsonl",
            "receipts/research-seal-receipt.json",
        ):
            with self.subTest(path=path):
                record = fx.handoff("a" * 64)
                record["canonical_artifacts"][0]["path"] = path
                self.assert_invalid("handoff", record)

    def test_state_event_uses_closed_p0_through_p9_vocabulary(self) -> None:
        record = {
            **fx.common_record("EVT-000001", lifecycle_status="ACCEPTED"),
            "schema_version": "research-state-event/v1",
            "event_id": "EVT-000001",
            "run_id": "RUN-000001",
            "sequence": 0,
            "previous_event_sha256": None,
            "event_type": "PHASE_TRANSITION",
            "from_phase": None,
            "to_phase": "HANDOFF_READY",
            "actor_id": "core:research-store",
            "reason_code": "INVALID_LEGACY_PHASE",
            "reason": "Invalid legacy phase name.",
            "occurred_at": fx.RECORDED_AT,
        }
        self.assert_invalid("state-event", record)

    def test_state_terminal_outcome_is_nonpredictive_and_has_no_to_phase(self) -> None:
        record = {
            **fx.common_record("EVT-000001", lifecycle_status="ACCEPTED"),
            "schema_version": "research-state-event/v1",
            "event_id": "EVT-000001",
            "run_id": "RUN-000001",
            "sequence": 1,
            "previous_event_sha256": "a" * 64,
            "event_type": "TERMINAL_OUTCOME",
            "from_phase": "P0",
            "to_phase": None,
            "outcome": "COULD_NOT_RUN",
            "actor_id": "core:research-store",
            "reason_code": "PROVIDER_NOT_EVALUATED",
            "reason": "The required provider attestation is not evaluated.",
            "occurred_at": fx.RECORDED_AT,
        }
        self.assert_valid("state-event", record)

        record["outcome"] = "COMPLETE"
        self.assert_invalid("state-event", record)
        record["outcome"] = "COULD_NOT_RUN"
        record["to_phase"] = "P0"
        self.assert_invalid("state-event", record)

    def test_registry_chain_has_one_null_genesis_predecessor(self) -> None:
        digest = "a" * 64
        entry = {
            "schema_version": "research-registry-entry/v1",
            "sequence": 1,
            "run_id": "RUN-000001",
            "request_id": "RSR-000001",
            "slug": "offline-fixture",
            "canonical_path": "docs/research/offline-fixture/runs/RUN-000001",
            "lifecycle_status": "ACCEPTED",
            "readiness_status": "READY",
            "outcome": "COMPLETE",
            "manifest_sha256": digest,
            "previous_entry_sha256": None,
            "entry_sha256": "b" * 64,
            "sealed_at_utc": fx.RECORDED_AT,
            "supersedes_run_ids": [],
            "stale_if": [],
        }
        self.assert_valid("registry", entry)
        entry["sequence"] = 2
        self.assert_invalid("registry", entry)
        entry["previous_entry_sha256"] = "c" * 64
        self.assert_valid("registry", entry)
        entry["sequence"] = 1
        self.assert_invalid("registry", entry)

    def test_unknown_fields_fail_closed(self) -> None:
        record = copy.deepcopy(fx.question())
        record["quietly_accept"] = True
        self.assert_invalid("question", record)


if __name__ == "__main__":
    unittest.main()
