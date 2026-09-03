"""Hostile regression coverage for closed Research Core contract edges.

These tests intentionally cross record, phase, and provider-attestation
boundaries.  They complement the ordinary happy-path suites by proving that a
plausible, schema-shaped forgery cannot pass merely because each referenced ID
has the right prefix.
"""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from devforgeai import __version__ as PACKAGE_VERSION
from devforgeai.research import run_contracts as contracts
from devforgeai.research.core import (
    ResearchStore,
    SchemaValidationError,
    canonical_json,
)

from tests.research import _fixtures as fx
from tests.research import test_run_contracts as contract_fixtures
from tests.research import test_store as store_fixtures
from tests.research.test_schemas import validator as schema_validator


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: object) -> None:
    path.write_bytes(canonical_json(value) + b"\n")


class AdversarialResearchContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temporary.name)
        (self.workspace / "inputs").mkdir()
        self.store = ResearchStore(
            self.workspace, allow_offline_test_harness=True
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _copy_fixture(self, name: str) -> Path:
        target = self.workspace / "inputs" / name
        target.write_bytes((fx.FIXTURES / name).read_bytes())
        return target

    def _open_to_p4(self, *, two_questions: bool = False):
        request = fx.load_request()
        if two_questions:
            request["questions"].append(
                {
                    "question_id": "RQ-000002",
                    "text": "Does the independent fixture describe the same bounded behavior?",
                    "completion_criteria": [
                        "Answer from admitted evidence and run a contrary lane."
                    ],
                }
            )
            request["budget"]["limits"]["atomic_questions"] = 2

        normalized, digest = self.store.normalize_request(request)
        ref = self.store.open_run(normalized, digest)
        fx.install_preflight_contract(
            self.store, self.workspace, normalized, digest, ref
        )
        self.store.transition(ref.slug, ref.run_id, "P1")
        self.store.transition(ref.slug, ref.run_id, "P2")

        for confirmed in normalized["questions"]:
            question = fx.question()
            question.update(
                {
                    "record_id": confirmed["question_id"],
                    "question_id": confirmed["question_id"],
                    "run_id": ref.run_id,
                    "text": confirmed["text"],
                    "completion_criteria": list(
                        confirmed["completion_criteria"]
                    ),
                    "priority": normalized["risk_tier"],
                }
            )
            self.store.append_record(
                ref.slug, ref.run_id, "question", question
            )

        fx.install_context_contract(
            self.store, self.workspace, normalized, digest, ref
        )
        self.store.transition(ref.slug, ref.run_id, "P3")
        fx.install_plan_contract(
            self.store, self.workspace, normalized, digest, ref
        )
        if two_questions:
            plan_path = ref.path / "plan.json"
            plan = _read_json(plan_path)
            second_question_plan = copy.deepcopy(plan["question_plans"][0])
            second_question_plan["question_id"] = "RQ-000002"
            plan["question_plans"].append(second_question_plan)
            for lane in plan["lanes"]:
                lane["question_ids"] = ["RQ-000001", "RQ-000002"]
            _write_json(plan_path, plan)
        self.store.transition(ref.slug, ref.run_id, "P4")
        return normalized, ref

    def _append_query(
        self,
        ref,
        *,
        query_id: str,
        question_id: str,
        direct: bool,
        result_fixture: str | None = None,
    ) -> dict:
        query = fx.query() if direct else fx.challenge_query()
        lane_number = 1 if direct else 2
        query.update(
            {
                "record_id": query_id,
                "query_id": query_id,
                "run_id": ref.run_id,
                "question_ids": [question_id],
                "lane_id": f"LANE-{lane_number:06d}",
                "worker_envelope_id": f"ENV-{lane_number:06d}",
                "purpose": "DISCOVERY" if direct else "CHALLENGE",
                "query_text": f"bounded hostile query {query_id}",
            }
        )
        if result_fixture is None:
            query["results"] = []
        else:
            query["results"] = [
                {
                    "candidate_id": f"{query_id}-CAND-000001",
                    "locator": f"tests/research/fixtures/{result_fixture}",
                    "title": f"Synthetic candidate for {query_id}",
                    "discovery_only": True,
                    "disposition": "RETRIEVE",
                    "reason": "Selected for exact-byte hostile regression coverage.",
                }
            ]
        self.store.append_record(ref.slug, ref.run_id, "query", query)
        return query

    def _put_source(
        self,
        ref,
        *,
        source_id: str,
        question_id: str,
        query_id: str,
        fixture_name: str,
    ) -> dict:
        metadata = fx.source_metadata(
            source_id, fixture_name, publisher=f"Publisher for {source_id}"
        )
        metadata.update(
            {
                "run_id": ref.run_id,
                "question_ids": [question_id],
                "query_ids": [query_id],
                "candidate_ids": [f"{query_id}-CAND-000001"],
                "custody": {"mode": "TRACKED_CAS"},
            }
        )
        return self.store.put_source(
            ref.slug,
            ref.run_id,
            source_id,
            self._copy_fixture(fixture_name),
            metadata,
        )

    @staticmethod
    def _runtime_provider_attestation() -> dict:
        attestation = fx.provider_conformance(provider_kind="CODEX")
        attestation["capabilities"] = [
            {
                "capability_id": capability_id,
                "required": True,
                "status": "SUPPORTED",
                "reason": "The retained provider fixture passed this capability.",
                "evidence": [
                    {
                        "artifact_id": f"evidence-{capability_id.lower()}",
                        "path": "evidence/provider-runtime.json",
                        "sha256": "a" * 64,
                    }
                ],
            }
            for capability_id in sorted(
                contracts.PROVIDER_RUNTIME_REQUIRED_CAPABILITIES
            )
        ]
        attestation["trials"] = []
        for fixture_number, fixture_id in enumerate(
            fx.PROVIDER_RUNTIME_FIXTURE_IDS
        ):
            for repetition in range(1, 11):
                number = fixture_number * 10 + repetition
                attestation["trials"].append(
                    {
                        "trial_id": f"PCT-{number:06d}",
                        "fixture_id": fixture_id,
                        "session_id": f"fresh-provider-session-{number:06d}",
                        "baseline": "ENABLED" if repetition <= 5 else "DISABLED",
                        "fresh_session": True,
                        "outcome": "PASS",
                        "evidence_path": f"evidence/trial-{number:06d}.json",
                        "evidence_sha256": f"{number % 10}" * 64,
                        "performed_at_utc": fx.RECORDED_AT,
                    }
                )
        return attestation

    def test_default_store_rejects_offline_provider_attestation(self) -> None:
        default_store = ResearchStore(self.workspace)
        request = fx.load_request()
        normalized, digest = default_store.normalize_request(request)
        ref = default_store.open_run(normalized, digest)

        with self.assertRaisesRegex(
            Exception, "E_OFFLINE_TEST_HARNESS_DISABLED"
        ):
            fx.install_preflight_contract(
                default_store, self.workspace, normalized, digest, ref
            )

        self.assertFalse((ref.path / "provider-conformance.json").exists())
        self.assertFalse((ref.path / "preflight.json").exists())

    def test_provider_capabilities_and_trials_are_relationally_closed(self) -> None:
        valid = self._runtime_provider_attestation()
        schema_validator("provider-conformance").validate(valid)
        self.assertEqual(
            contracts.validate_provider_conformance_semantics(valid), []
        )
        self.assertEqual(len(valid["trials"]), 200)

        second_fixture = copy.deepcopy(valid["trials"])
        for number, trial in enumerate(second_fixture[:10], 201):
            trial["trial_id"] = f"PCT-{number:06d}"
            trial["fixture_id"] = "invented-provider-fixture"
            trial["session_id"] = f"fresh-provider-session-{number:06d}"
        extra_fixture = copy.deepcopy(valid)
        extra_fixture["trials"].extend(second_fixture[:10])
        self.assertIn(
            "E_PROVIDER_TRIAL_FIXTURE_COVERAGE",
            contracts.validate_provider_conformance_semantics(extra_fixture),
        )

        missing_fixture = copy.deepcopy(valid)
        del missing_fixture["trials"][:10]
        self.assertIn(
            "E_PROVIDER_TRIAL_FIXTURE_COVERAGE",
            contracts.validate_provider_conformance_semantics(missing_fixture),
        )

        wrong_suite = copy.deepcopy(valid)
        wrong_suite["fixture_suite"]["suite_version"] = "1.0.1"
        self.assertIn(
            "E_PROVIDER_FIXTURE_SUITE_BINDING",
            contracts.validate_provider_conformance_semantics(wrong_suite),
        )

        wrong_suite_digest = copy.deepcopy(valid)
        wrong_suite_digest["fixture_suite"]["manifest_sha256"] = "0" * 64
        suite_errors = contracts.validate_provider_conformance_semantics(
            wrong_suite_digest
        )
        self.assertIn("E_PROVIDER_FIXTURE_SUITE_BINDING", suite_errors)
        self.assertIn("E_PROVIDER_FIXTURE_SUITE_DIGEST", suite_errors)

        missing_capability = copy.deepcopy(valid)
        removed = missing_capability["capabilities"].pop()["capability_id"]
        self.assertIn(
            f"E_PROVIDER_REQUIRED_CAPABILITY_MISSING:{removed}",
            contracts.validate_provider_conformance_semantics(
                missing_capability
            ),
        )

        weak_capability = copy.deepcopy(valid)
        weak_capability["capabilities"][0].update(
            {"required": False, "status": "NOT_PROBED", "evidence": []}
        )
        weak_id = weak_capability["capabilities"][0]["capability_id"]
        weak_errors = contracts.validate_provider_conformance_semantics(
            weak_capability
        )
        self.assertIn(
            f"E_PROVIDER_REQUIRED_CAPABILITY_OPTIONAL:{weak_id}", weak_errors
        )
        self.assertIn(
            f"E_PROVIDER_REQUIRED_CAPABILITY_UNSUPPORTED:{weak_id}",
            weak_errors,
        )
        self.assertIn(
            f"E_PROVIDER_REQUIRED_CAPABILITY_EVIDENCE:{weak_id}", weak_errors
        )

        duplicate_capability = copy.deepcopy(valid)
        duplicate_capability["capabilities"].append(
            copy.deepcopy(duplicate_capability["capabilities"][0])
        )
        self.assertIn(
            "E_PROVIDER_CAPABILITY_DUPLICATE",
            contracts.validate_provider_conformance_semantics(
                duplicate_capability
            ),
        )

        duplicate_trials = copy.deepcopy(valid)
        duplicate_trials["trials"][1]["trial_id"] = duplicate_trials[
            "trials"
        ][0]["trial_id"]
        duplicate_trials["trials"][2]["session_id"] = duplicate_trials[
            "trials"
        ][0]["session_id"]
        duplicate_errors = contracts.validate_provider_conformance_semantics(
            duplicate_trials
        )
        self.assertIn("E_PROVIDER_TRIAL_ID_DUPLICATE", duplicate_errors)
        self.assertIn("E_PROVIDER_TRIAL_SESSION_DUPLICATE", duplicate_errors)

        wrong_composition = copy.deepcopy(valid)
        wrong_composition["trials"][5]["baseline"] = "ENABLED"
        self.assertIn(
            "E_PROVIDER_TRIAL_COMPOSITION",
            contracts.validate_provider_conformance_semantics(
                wrong_composition
            ),
        )

        failed_trial = copy.deepcopy(valid)
        failed_trial["trials"][0]["outcome"] = "FAIL"
        self.assertIn(
            "E_PROVIDER_SUPPORTED_TRIAL_NOT_PASS",
            contracts.validate_provider_conformance_semantics(failed_trial),
        )

        expired_trial = copy.deepcopy(valid)
        expired_trial["trials"][0]["performed_at_utc"] = valid[
            "expires_at_utc"
        ]
        self.assertIn(
            "E_PROVIDER_TRIAL_TIME:PCT-000001",
            contracts.validate_provider_conformance_semantics(expired_trial),
        )

        offline = fx.provider_conformance()
        self.assertEqual(
            contracts.validate_provider_conformance_semantics(offline), []
        )
        wrong_offline_fixture = copy.deepcopy(offline)
        wrong_offline_fixture["trials"][0]["fixture_id"] = "provider-runtime-fixture"
        self.assertIn(
            "E_PROVIDER_OFFLINE_TRIAL_COMPOSITION",
            contracts.validate_provider_conformance_semantics(
                wrong_offline_fixture
            ),
        )

    def test_request_rejects_impossible_lane_query_and_context_budgets(self) -> None:
        for field, value in (
            ("research_lanes", 1),
            ("discovery_queries", 1),
        ):
            with self.subTest(field=field):
                request = fx.load_request()
                request["budget"]["limits"][field] = value
                with self.assertRaisesRegex(
                    SchemaValidationError, "E_SCHEMA_REQUEST"
                ):
                    self.store.normalize_request(request)

        request = fx.load_request()
        request["budget"]["limits"]["context_bytes"] = 1
        with self.assertRaisesRegex(
            Exception, "E_BUDGET_CONTEXT_REQUEST_BYTES"
        ):
            self.store.normalize_request(request)
        self.assertFalse((self.workspace / ".devforgeai").exists())

    def test_claim_and_ready_handoff_lifecycle_combinations_are_schema_bound(
        self,
    ) -> None:
        claim = fx.claim(status="REJECTED")
        claim.update(
            {"lifecycle_status": "REJECTED", "readiness_status": "STALE"}
        )
        with self.assertRaisesRegex(SchemaValidationError, "E_SCHEMA_CLAIM"):
            self.store._validate_schema("claim", claim)

        handoff = fx.handoff("a" * 64)
        handoff.update(
            {"lifecycle_status": "REJECTED", "readiness_status": "STALE"}
        )
        with self.assertRaisesRegex(
            SchemaValidationError, "E_SCHEMA_HANDOFF"
        ):
            self.store._validate_schema("handoff", handoff)

        wrong_location = fx.handoff("a" * 64)
        wrong_location["location"]["subphase"] = "decision-needed"
        with self.assertRaisesRegex(
            SchemaValidationError, "E_SCHEMA_HANDOFF"
        ):
            self.store._validate_schema("handoff", wrong_location)

    def test_non_ready_handoff_outcomes_fail_closed_before_append(self) -> None:
        helper = store_fixtures.ResearchStoreContractTests(
            methodName="test_request_normalization_digest_is_deterministic"
        )
        helper.setUp()
        self.addCleanup(helper.tearDown)
        _, ref = helper.build_to_p8()
        handoff_path = ref.path / "handoff.json"
        handoff = _read_json(handoff_path)
        handoff_path.unlink()
        handoff["result"].update(
            {
                "outcome": "NEEDS_DECISION",
                "reason_code": "RESEARCH_GATES_OPEN",
            }
        )

        with self.assertRaisesRegex(
            Exception, "E_NOT_IMPLEMENTED_HANDOFF_OUTCOME"
        ):
            helper.store.append_record(
                ref.slug, ref.run_id, "handoff", handoff
            )
        self.assertFalse(handoff_path.exists())

    def test_dangling_decisions_and_nondecision_supersession_fail_on_append(
        self,
    ) -> None:
        _, ref = self._open_to_p4()

        dangling = fx.query()
        dangling.update(
            {"run_id": ref.run_id, "decision_refs": ["DEC-999999"]}
        )
        with self.assertRaisesRegex(Exception, "E_REFERENCE_DECISION"):
            self.store.append_record(ref.slug, ref.run_id, "query", dangling)

        superseding = fx.query()
        superseding.update(
            {"run_id": ref.run_id, "supersedes": ["QRY-999999"]}
        )
        with self.assertRaisesRegex(
            Exception, "E_NOT_IMPLEMENTED_RECORD_SUPERSESSION"
        ):
            self.store.append_record(
                ref.slug, ref.run_id, "query", superseding
            )

    def test_parent_must_be_prior_sealed_and_registered(self) -> None:
        cases = (
            ("RUN-000001", "E_PARENT_RUN_NOT_PRIOR"),
            ("RUN-000000", "E_PARENT_RUN_NOT_SEALED"),
        )
        for parent_run_id, expected in cases:
            with self.subTest(parent_run_id=parent_run_id):
                with tempfile.TemporaryDirectory() as root:
                    workspace = Path(root)
                    store = ResearchStore(
                        workspace, allow_offline_test_harness=True
                    )
                    request = fx.load_request()
                    request["parent_run_id"] = parent_run_id
                    normalized, digest = store.normalize_request(request)
                    with self.assertRaisesRegex(Exception, expected):
                        store.open_run(normalized, digest)
                    self.assertFalse(
                        (
                            workspace
                            / ".devforgeai/research-staging/offline-fixture/RUN-000001"
                        ).exists()
                    )

    def test_plan_rejects_context_input_that_was_not_selected(self) -> None:
        run = contract_fixtures._build_run(self.workspace)
        manifest_path = run / "context-manifest.json"
        manifest = _read_json(manifest_path)
        manifest["entries"][0]["selection"] = "EXCLUDED"
        _write_json(manifest_path, manifest)

        self.assertTrue(
            any(
                error.startswith("E_PLAN_INPUT_ARTIFACT_NOT_SELECTED:")
                for error in contracts.validate_plan_contract(
                    self.workspace, run
                )
            )
        )

    def test_cross_question_edges_and_source_locator_are_rejected(self) -> None:
        request, ref = self._open_to_p4(two_questions=True)
        self._append_query(
            ref,
            query_id="QRY-000001",
            question_id="RQ-000001",
            direct=True,
            result_fixture="source-primary.txt",
        )
        self._append_query(
            ref,
            query_id="QRY-000002",
            question_id="RQ-000001",
            direct=False,
        )
        self._append_query(
            ref,
            query_id="QRY-000003",
            question_id="RQ-000002",
            direct=True,
            result_fixture="source-corroborating.txt",
        )
        self._append_query(
            ref,
            query_id="QRY-000004",
            question_id="RQ-000002",
            direct=False,
        )
        self.store.transition(ref.slug, ref.run_id, "P5")

        wrong_locator = fx.source_metadata(
            "SRC-000099", "source-primary.txt", publisher="Wrong locator"
        )
        wrong_locator.update(
            {
                "run_id": ref.run_id,
                "locator": {
                    "kind": "LOCAL_FILE",
                    "value": "tests/research/fixtures/source-other.txt",
                },
                "custody": {"mode": "TRACKED_CAS"},
            }
        )
        with self.assertRaisesRegex(Exception, "E_SOURCE_CANDIDATE_LOCATOR"):
            self.store.put_source(
                ref.slug,
                ref.run_id,
                "SRC-000099",
                self._copy_fixture("source-primary.txt"),
                wrong_locator,
            )

        crossed_source = fx.source_metadata(
            "SRC-000098", "source-primary.txt", publisher="Crossed source"
        )
        crossed_source.update(
            {
                "run_id": ref.run_id,
                "question_ids": ["RQ-000002"],
                "custody": {"mode": "TRACKED_CAS"},
            }
        )
        with self.assertRaisesRegex(
            Exception, "E_SOURCE_QUERY_QUESTION_EDGE"
        ):
            self.store.put_source(
                ref.slug,
                ref.run_id,
                "SRC-000098",
                self._copy_fixture("source-primary.txt"),
                crossed_source,
            )

        source_one = self._put_source(
            ref,
            source_id="SRC-000001",
            question_id="RQ-000001",
            query_id="QRY-000001",
            fixture_name="source-primary.txt",
        )
        source_two = self._put_source(
            ref,
            source_id="SRC-000002",
            question_id="RQ-000002",
            query_id="QRY-000003",
            fixture_name="source-corroborating.txt",
        )

        crossed_evidence = fx.evidence(
            "EVD-000099",
            "SRC-000001",
            source_one["custody"]["sha256"],
            "This evidence is deliberately assigned to the wrong question.",
        )
        crossed_evidence.update(
            {"run_id": ref.run_id, "question_ids": ["RQ-000002"]}
        )
        with self.assertRaisesRegex(
            Exception, "E_EVIDENCE_SOURCE_QUESTION_EDGE"
        ):
            self.store.append_record(
                ref.slug, ref.run_id, "evidence", crossed_evidence
            )

        evidence_one = fx.evidence(
            "EVD-000001",
            "SRC-000001",
            source_one["custody"]["sha256"],
            "The first retained source supports the first bounded question.",
        )
        evidence_one["run_id"] = ref.run_id
        self.store.append_record(
            ref.slug, ref.run_id, "evidence", evidence_one
        )
        evidence_two = fx.evidence(
            "EVD-000002",
            "SRC-000002",
            source_two["custody"]["sha256"],
            "The second retained source supports the second bounded question.",
        )
        evidence_two.update(
            {"run_id": ref.run_id, "question_ids": ["RQ-000002"]}
        )
        self.store.append_record(
            ref.slug, ref.run_id, "evidence", evidence_two
        )
        self.store.transition(ref.slug, ref.run_id, "P6")

        crossed_claim = fx.claim(support=["EVD-000001"])
        crossed_claim.update(
            {"run_id": ref.run_id, "question_ids": ["RQ-000002"]}
        )
        with self.assertRaisesRegex(
            Exception, "E_CLAIM_EVIDENCE_QUESTION_EDGE"
        ):
            self.store.append_record(
                ref.slug, ref.run_id, "claim", crossed_claim
            )

        claim = fx.claim(support=["EVD-000001"])
        claim["run_id"] = ref.run_id
        self.store.append_record(ref.slug, ref.run_id, "claim", claim)

        crossed_contradiction = fx.contradiction()
        crossed_contradiction.update(
            {
                "run_id": ref.run_id,
                "source_refs": ["SRC-000002"],
                "evidence_refs": ["EVD-000002"],
                "evidence_ids": ["EVD-000002"],
            }
        )
        with self.assertRaisesRegex(
            Exception, "E_CONTRADICTION_EVIDENCE_QUESTION_EDGE"
        ):
            self.store.append_record(
                ref.slug,
                ref.run_id,
                "contradiction",
                crossed_contradiction,
            )

        fx.install_reconciliation_contract(
            self.store,
            self.workspace,
            request,
            ref,
            query_ids=[
                "QRY-000001",
                "QRY-000002",
                "QRY-000003",
                "QRY-000004",
            ],
            source_count=2,
        )
        reconciliation_path = ref.path / "reconciliation.json"
        reconciliation = _read_json(reconciliation_path)
        second_coverage = copy.deepcopy(
            reconciliation["question_coverage"][0]
        )
        second_coverage["question_id"] = "RQ-000002"
        reconciliation["question_coverage"].append(second_coverage)
        _write_json(reconciliation_path, reconciliation)
        self.store.transition(ref.slug, ref.run_id, "P7")

        packet = self.store.build_verification_packet(
            ref.slug, ref.run_id, claim["claim_id"]
        )
        verification = fx.verification(
            claim,
            packet_ref=packet["packet_ref"],
            provider_conformance_path=ref.path / "provider-conformance.json",
        )
        verification["run_id"] = ref.run_id
        self.store.append_record(
            ref.slug, ref.run_id, "verification", verification
        )
        self.store.transition(ref.slug, ref.run_id, "P8")

        crossed_synthesis = fx.synthesis()
        crossed_synthesis["run_id"] = ref.run_id
        crossed_synthesis["question_dispositions"].append(
            {
                "question_id": "RQ-000002",
                "disposition": "ANSWERED",
                "claim_ids": ["CLM-000001"],
                "reason": "Deliberately crosses the claim/question edge.",
            }
        )
        with self.assertRaisesRegex(
            Exception, "E_SYNTHESIS_CLAIM_QUESTION_EDGE"
        ):
            self.store.append_record(
                ref.slug, ref.run_id, "synthesis", crossed_synthesis
            )

    def test_shared_lanes_require_a_query_for_every_linked_question(self) -> None:
        request, ref = self._open_to_p4(two_questions=True)
        self._append_query(
            ref,
            query_id="QRY-000001",
            question_id="RQ-000001",
            direct=True,
        )
        self._append_query(
            ref,
            query_id="QRY-000002",
            question_id="RQ-000001",
            direct=False,
        )
        self.store.transition(ref.slug, ref.run_id, "P5")
        self.store.transition(ref.slug, ref.run_id, "P6")
        fx.install_reconciliation_contract(
            self.store,
            self.workspace,
            request,
            ref,
            query_ids=["QRY-000001", "QRY-000002"],
            source_count=0,
        )
        reconciliation_path = ref.path / "reconciliation.json"
        reconciliation = _read_json(reconciliation_path)
        second_coverage = copy.deepcopy(
            reconciliation["question_coverage"][0]
        )
        second_coverage["question_id"] = "RQ-000002"
        reconciliation["question_coverage"].append(second_coverage)
        _write_json(reconciliation_path, reconciliation)

        with self.assertRaisesRegex(
            Exception,
            "E_RECONCILIATION_DIRECT_TERMINAL:RQ-000002",
        ):
            self.store.transition(ref.slug, ref.run_id, "P7")

    def test_plan_requires_exactly_one_worker_envelope_per_lane(self) -> None:
        run = contract_fixtures._build_run(self.workspace)
        plan_path = run / "plan.json"
        plan = _read_json(plan_path)
        plan["lanes"][0]["worker_envelope_ids"].append("ENV-999999")

        with self.assertRaisesRegex(SchemaValidationError, "E_SCHEMA_PLAN"):
            self.store._validate_schema("plan", plan)

        _write_json(plan_path, plan)
        self.assertIn(
            "E_PLAN_LANE_ENVELOPE_CARDINALITY:LANE-000001",
            contracts.validate_plan_contract(self.workspace, run),
        )

    def test_reconciliation_attempts_equal_retries_plus_one(self) -> None:
        run = contract_fixtures._build_run(self.workspace)
        reconciliation_path = run / "reconciliation.json"
        reconciliation = _read_json(reconciliation_path)
        reconciliation["lane_results"][0]["attempts"] = 2
        _write_json(reconciliation_path, reconciliation)

        self.assertIn(
            "E_RECONCILIATION_ATTEMPT_RETRY_ACCOUNTING:LANE-000001",
            contracts.validate_reconciliation_contract(
                self.workspace, run
            ),
        )

    def test_generated_validation_binds_exact_package_core_version(self) -> None:
        helper = store_fixtures.ResearchStoreContractTests(
            methodName="test_request_normalization_digest_is_deterministic"
        )
        helper.setUp()
        self.addCleanup(helper.tearDown)
        _, ref = helper.build_to_p8()
        helper.store.transition(ref.slug, ref.run_id, "P9")

        validation = _read_json(ref.path / "validation.json")
        self.assertEqual(
            validation["environment"]["core_version"],
            f"devforgeai-research/{PACKAGE_VERSION}",
        )


if __name__ == "__main__":
    unittest.main()
