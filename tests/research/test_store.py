from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

from devforgeai.research import core as research_core
from devforgeai.research.store import ResearchStore, canonical_json, normalize_request

from tests.research import _fixtures as fx


RUN_ID = re.compile(r"^RUN-[0-9]{6}$")
SHIFTABLE_ID = re.compile(
    r"^(RSR|RQ|QRY|SRC|EVD|CLM|CTR|VER|SYN|DEC|HND)-([0-9]{6})$"
)
CANDIDATE_ID = re.compile(r"^QRY-([0-9]{6})-CAND-([0-9]{6})$")


def shift_record_ids(value: object, offset: int) -> object:
    """Move fixture-owned IDs into a disjoint dossier sequence range."""
    if offset == 0:
        return value
    if isinstance(value, dict):
        return {key: shift_record_ids(item, offset) for key, item in value.items()}
    if isinstance(value, list):
        return [shift_record_ids(item, offset) for item in value]
    if isinstance(value, str) and (match := CANDIDATE_ID.fullmatch(value)):
        return f"QRY-{int(match.group(1)) + offset:06d}-CAND-{match.group(2)}"
    if isinstance(value, str) and (match := SHIFTABLE_ID.fullmatch(value)):
        return f"{match.group(1)}-{int(match.group(2)) + offset:06d}"
    return value


def report_ok(report: object) -> bool:
    if isinstance(report, bool):
        return report
    if isinstance(report, dict):
        if "ok" in report:
            return bool(report["ok"])
        if "valid" in report:
            return bool(report["valid"])
    for name in ("ok", "valid"):
        if hasattr(report, name):
            return bool(getattr(report, name))
    return bool(report)


def report_text(report: object) -> str:
    if hasattr(report, "to_dict"):
        return json.dumps(report.to_dict(), sort_keys=True)
    return repr(report)


class ResearchStoreContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temporary.name)
        (self.workspace / "inputs").mkdir()
        self.store = ResearchStore(
            self.workspace, allow_offline_test_harness=True
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_non_linux_platform_fails_before_workspace_mutation(self) -> None:
        alternate = self.workspace / "unsupported"
        alternate.mkdir()
        with mock.patch.object(research_core.sys, "platform", "win32"):
            with self.assertRaisesRegex(Exception, "E_PLATFORM_UNSUPPORTED"):
                ResearchStore(alternate)
        self.assertEqual(list(alternate.iterdir()), [])

    def copy_source(self, fixture_name: str) -> Path:
        destination = self.workspace / "inputs" / fixture_name
        destination.write_bytes((fx.FIXTURES / fixture_name).read_bytes())
        return destination

    def open_request(self, *, material: bool = False, id_offset: int = 0):
        request = fx.load_request(high_risk=material)
        request = shift_record_ids(request, id_offset)
        normalized, digest = normalize_request(request)
        ref = self.store.open_run(normalized, digest)
        self.assertRegex(ref.run_id, RUN_ID)
        self.assertEqual(ref.slug, normalized["slug"])
        fx.install_preflight_contract(
            self.store, self.workspace, normalized, digest, ref
        )
        return normalized, digest, ref

    def test_unvalidated_parent_work_order_fails_before_mutation(self) -> None:
        request = fx.load_request()
        request["authority"]["work_order_sha256"] = "a" * 64
        normalized, digest = self.store.normalize_request(request)

        with self.assertRaisesRegex(
            Exception, "E_NOT_IMPLEMENTED_WORK_ORDER_AUTHORITY"
        ):
            self.store.open_run(normalized, digest)

        self.assertFalse((self.workspace / ".devforgeai").exists())
        self.assertFalse((self.workspace / "docs" / "research").exists())

    def advance(self, ref, through: int) -> None:
        request = json.loads((ref.path / "request.json").read_text(encoding="utf-8"))
        current = int(self.store.resume_run(ref.slug, ref.run_id).phase[1:])
        for number in range(current + 1, through + 1):
            if number == 3 and not (ref.path / "context-manifest.json").exists():
                fx.install_context_contract(
                    self.store,
                    self.workspace,
                    request,
                    ref.request_digest,
                    ref,
                )
            if number == 4 and not (ref.path / "plan.json").exists():
                fx.install_plan_contract(
                    self.store,
                    self.workspace,
                    request,
                    ref.request_digest,
                    ref,
                )
            self.store.transition(ref.slug, ref.run_id, f"P{number}", reason="offline fixture")

    def prepare_p5(
        self, request: dict | None = None, query_record: dict | None = None
    ):
        if request is None:
            normalized, _, ref = self.open_request()
        else:
            normalized, digest = self.store.normalize_request(request)
            ref = self.store.open_run(normalized, digest)
            fx.install_preflight_contract(
                self.store, self.workspace, normalized, digest, ref
            )
        self.advance(ref, 2)
        question = fx.question()
        question["run_id"] = ref.run_id
        self.store.append_record(ref.slug, ref.run_id, "question", question)
        self.advance(ref, 4)
        query = query_record if query_record is not None else fx.query()
        query["run_id"] = ref.run_id
        self.store.append_record(ref.slug, ref.run_id, "query", query)
        self.store.transition(ref.slug, ref.run_id, "P5")
        return normalized, ref

    @staticmethod
    def source_digest(result: dict) -> str:
        if "sha256" in result:
            return result["sha256"]
        return result["custody"]["sha256"]

    @staticmethod
    def source_object_path(result: dict) -> str:
        if "object_path" in result:
            return result["object_path"]
        if "cas_path" in result:
            return result["cas_path"]
        return result["custody"]["object_path"]

    def put_fixture_source(
        self,
        ref,
        source_id: str,
        fixture_name: str,
        publisher: str,
        *,
        mode: str = "TRACKED_CAS",
        query_ids: list[str] | None = None,
        candidate_ids: list[str] | None = None,
        freshness_status: str | None = None,
        id_offset: int = 0,
        content_fixture_name: str | None = None,
    ) -> dict:
        metadata = fx.source_metadata(source_id, fixture_name, publisher=publisher)
        if query_ids is not None:
            metadata["query_ids"] = query_ids
            if candidate_ids is None:
                candidate_ids = [f"{query_id}-CAND-000001" for query_id in query_ids]
        if candidate_ids is not None:
            metadata["candidate_ids"] = candidate_ids
        if freshness_status is not None:
            metadata["freshness"]["status"] = freshness_status
        metadata = shift_record_ids(metadata, id_offset)
        metadata["run_id"] = ref.run_id
        metadata["custody"] = {"mode": mode}
        if mode == "LOCAL_ONLY_CAS":
            metadata["retention_policy"].update(
                {
                    "redistribution_basis": "NONE",
                    "redistribution_reference": None,
                    "data_classification": "INTERNAL",
                }
            )
            metadata["retention_policy"]["sensitive_scan"]["status"] = "NOT_RUN"
        path = self.copy_source(content_fixture_name or fixture_name)
        return self.store.put_source(
            ref.slug, ref.run_id, metadata["source_id"], path, metadata
        )

    def append_evidence(self, ref, record: dict) -> str:
        record["run_id"] = ref.run_id
        return self.store.append_record(ref.slug, ref.run_id, "evidence", record)

    def build_to_p8(
        self,
        *,
        material: bool = False,
        corroborate: bool = False,
        contrary: bool = True,
        verify: bool = True,
        same_author_verifier: bool = False,
        failed_challenge: bool = False,
        duplicate_corroboration_bytes: bool = False,
        verification_omits_support: bool = False,
        claim_type: str = "SOURCE_FACT",
        stale_primary: bool = False,
        id_offset: int = 0,
        freshness_count_delta: int = 0,
        actual_budget_overrides: dict[str, int | str] | None = None,
        artifact_overrides: dict[str, object] | None = None,
        unfulfilled_retrieve_candidate: bool = False,
        stop_at_p7: bool = False,
    ):
        request, request_digest, ref = self.open_request(
            material=material, id_offset=id_offset
        )
        self.advance(ref, 2)

        question = shift_record_ids(fx.question(), id_offset)
        confirmed_question = request["questions"][0]
        question["text"] = confirmed_question["text"]
        question["completion_criteria"] = list(
            confirmed_question["completion_criteria"]
        )
        question["priority"] = request["risk_tier"]
        question["run_id"] = ref.run_id
        self.store.append_record(ref.slug, ref.run_id, "question", question)
        self.advance(ref, 4)

        base_query = fx.query()
        if corroborate:
            base_query["results"].append(
                {
                    "candidate_id": "QRY-000001-CAND-000002",
                    "locator": "tests/research/fixtures/source-corroborating.txt",
                    "title": "Synthetic Corroborating Source B",
                    "discovery_only": True,
                    "disposition": "RETRIEVE",
                    "reason": "Selected as the distinct corroborating retrieval candidate.",
                }
            )
        if unfulfilled_retrieve_candidate:
            base_query["results"].append(
                {
                    "candidate_id": "QRY-000001-CAND-000099",
                    "locator": "tests/research/fixtures/source-never-retrieved.txt",
                    "discovery_only": True,
                    "disposition": "RETRIEVE",
                    "reason": "Synthetic hostile candidate must be closed by a source attempt.",
                }
            )
        query = shift_record_ids(base_query, id_offset)
        query["run_id"] = ref.run_id
        self.store.append_record(ref.slug, ref.run_id, "query", query)
        if contrary:
            challenge = shift_record_ids(fx.challenge_query(), id_offset)
            challenge["run_id"] = ref.run_id
            if failed_challenge:
                challenge["status"] = "FAILED"
                challenge["failure"] = {
                    "kind": "NETWORK",
                    "message": "Synthetic challenge lane failure.",
                }
            self.store.append_record(ref.slug, ref.run_id, "query", challenge)
        self.store.transition(ref.slug, ref.run_id, "P5", reason="admit local fixtures")

        primary = self.put_fixture_source(
            ref,
            "SRC-000001",
            "source-primary.txt",
            "Synthetic Standards Body",
            freshness_status="STALE" if stale_primary else None,
            id_offset=id_offset,
        )
        base_support_ids = ["EVD-000001"]
        support_ids = [f"EVD-{1 + id_offset:06d}"]
        evidence_ids = list(support_ids)
        self.append_evidence(
            ref,
            shift_record_ids(
                fx.evidence(
                    "EVD-000001",
                    "SRC-000001",
                    self.source_digest(primary),
                    "The retained standard specifies one pulse for a valid start signal.",
                ),
                id_offset,
            ),
        )

        if corroborate:
            second = self.put_fixture_source(
                ref,
                "SRC-000002",
                "source-corroborating.txt",
                "Independent Synthetic Lab",
                candidate_ids=["QRY-000001-CAND-000002"],
                id_offset=id_offset,
                content_fixture_name=(
                    "source-primary.txt"
                    if duplicate_corroboration_bytes
                    else None
                ),
            )
            base_support_ids.append("EVD-000002")
            support_ids.append(f"EVD-{2 + id_offset:06d}")
            evidence_ids.append(f"EVD-{2 + id_offset:06d}")
            self.append_evidence(
                ref,
                shift_record_ids(
                    fx.evidence(
                        "EVD-000002",
                        "SRC-000002",
                        self.source_digest(second),
                        "An independently authored fixture also reports one pulse.",
                    ),
                    id_offset,
                ),
            )

        base_contradiction_ids: list[str] = []
        contradiction_ids: list[str] = []
        if contrary:
            third = self.put_fixture_source(
                ref,
                "SRC-000003",
                "source-contrary.txt",
                "Independent Errata Group",
                query_ids=["QRY-000002"],
                id_offset=id_offset,
            )
            evidence_ids.append(f"EVD-{3 + id_offset:06d}")
            self.append_evidence(
                ref,
                shift_record_ids(
                    fx.evidence(
                        "EVD-000003",
                        "SRC-000003",
                        self.source_digest(third),
                        "Rapidly repeated signals may produce two pulses.",
                        polarity="CONTRARY",
                    ),
                    id_offset,
                ),
            )
            base_contradiction_ids.append("CTR-000001")
            contradiction_ids.append(f"CTR-{1 + id_offset:06d}")

        self.store.transition(ref.slug, ref.run_id, "P6", reason="form atomic claims")
        base_claim = fx.claim(
            support=base_support_ids, contradictions=base_contradiction_ids
        )
        claim = shift_record_ids(base_claim, id_offset)
        claim["run_id"] = ref.run_id
        claim["claim_type"] = claim_type
        if material:
            claim["risk_characteristics"] = ["SAFETY"]
        if corroborate:
            claim["source_refs"] = [
                f"SRC-{1 + id_offset:06d}",
                f"SRC-{2 + id_offset:06d}",
            ] + (
                [f"SRC-{3 + id_offset:06d}"] if contrary else []
            )
            claim["evidence_refs"] = evidence_ids
        self.store.append_record(ref.slug, ref.run_id, "claim", claim)
        if contrary:
            contradiction = shift_record_ids(fx.contradiction(), id_offset)
            contradiction["run_id"] = ref.run_id
            self.store.append_record(ref.slug, ref.run_id, "contradiction", contradiction)

        reconciled_query_ids = [f"QRY-{1 + id_offset:06d}"]
        if contrary:
            reconciled_query_ids.append(f"QRY-{2 + id_offset:06d}")
        source_count = 1 + int(corroborate) + int(contrary)
        fx.install_reconciliation_contract(
            self.store,
            self.workspace,
            request,
            ref,
            query_ids=reconciled_query_ids,
            source_count=source_count,
            status="FAIL" if failed_challenge else "PASS",
        )
        self.store.transition(ref.slug, ref.run_id, "P7", reason="independent verification")
        if stop_at_p7:
            return request, ref
        if verify:
            packet_receipt = self.store.build_verification_packet(
                ref.slug, ref.run_id, claim["claim_id"]
            )
            verification_outcome = (
                "FAIL"
                if material and (not corroborate or duplicate_corroboration_bytes)
                else "PASS"
            )
            verification = fx.verification(
                claim,
                packet_ref=packet_receipt["packet_ref"],
                outcome=verification_outcome,
                nonpass_check="corroboration",
                provider_conformance_path=ref.path / "provider-conformance.json",
            )
            verification["record_id"] = f"VER-{1 + id_offset:06d}"
            verification["verification_id"] = f"VER-{1 + id_offset:06d}"
            if same_author_verifier:
                verification["verifier"]["actor_id"] = claim["author"]["actor_id"]
                verification["verifier"]["session_id"] = claim["author"]["session_id"]
            verification["run_id"] = ref.run_id
            if verification_omits_support:
                verification["evidence_refs"] = [f"EVD-{3 + id_offset:06d}"]
                verification["reference_sets"]["evidence_ids"] = [
                    f"EVD-{3 + id_offset:06d}"
                ]
            self.store.append_record(ref.slug, ref.run_id, "verification", verification)

        self.store.transition(ref.slug, ref.run_id, "P8", reason="evidence-bound synthesis")
        synthesis = shift_record_ids(fx.synthesis(), id_offset)
        synthesis["run_id"] = ref.run_id
        synthesis["source_refs"] = list(claim["source_refs"])
        synthesis["evidence_refs"] = evidence_ids
        self.store.append_record(
            ref.slug, ref.run_id, "synthesis", synthesis
        )
        synthesis_path = (
            self.workspace
            / ".devforgeai"
            / "research-staging"
            / ref.slug
            / ref.run_id
            / "synthesis.jsonl"
        )
        synthesis_bytes = synthesis_path.read_bytes()
        synthesis_digest = hashlib.sha256(synthesis_bytes).hexdigest()
        handoff = shift_record_ids(
            fx.handoff(
                synthesis_digest,
                run_id=ref.run_id,
                request_sha256=request_digest,
                slug=ref.slug,
            ),
            id_offset,
        )
        complete = (
            contrary
            and verify
            and not same_author_verifier
            and (
                not material
                or (corroborate and not duplicate_corroboration_bytes)
            )
        )
        handoff["location"]["project_id"] = request["project_id"]
        handoff["location"]["run_id"] = ref.run_id
        handoff["result"]["outcome"] = "READY_TO_SEAL" if complete else "NEEDS_DECISION"
        handoff["result"]["reason_code"] = (
            "RESEARCH_READY_TO_SEAL" if complete else "RESEARCH_GATES_OPEN"
        )
        handoff["questions"][0]["question_id"] = request["questions"][0]["question_id"]
        handoff["claims"]["by_dispute"] = {
            "NONE": int(not contrary),
            "OPEN": 0,
            "RESOLVED": int(contrary),
        }
        handoff["claims"]["by_verification"] = {
            "NOT_RUN": int(not verify),
            "PASS": int(
                verify
                and not same_author_verifier
                and (
                    not material
                    or (corroborate and not duplicate_corroboration_bytes)
                )
            ),
            "FAIL": int(
                verify
                and (
                    same_author_verifier
                    or (
                        material
                        and (not corroborate or duplicate_corroboration_bytes)
                    )
                )
            ),
            "COULD_NOT_RUN": 0,
            "INFRA_FAILURE": 0,
            "NOT_APPLICABLE": 0,
        }
        handoff["sources"]["total"] = source_count
        handoff["sources"]["by_admission"]["ADMITTED_EVIDENCE"] = source_count
        handoff["sources"]["by_retrieval"]["RETRIEVED"] = source_count
        handoff["sources"]["by_custody"]["TRACKED_CAS"] = source_count
        handoff["sources"]["by_freshness"]["CURRENT"] = (
            source_count + freshness_count_delta
        )
        handoff["contrary_evidence"] = {
            "open_count": 0,
            "resolved_count": int(contrary),
            "contradictions": (
                [
                    {
                        "contradiction_id": f"CTR-{1 + id_offset:06d}",
                        "status": "ACCEPTED_UNCERTAINTY",
                        "scope": "Rapid repetition may produce two pulses.",
                    }
                ]
                if contrary
                else []
            ),
            "uncovered_scope": [] if contrary else ["No contrary lane was completed."],
        }
        handoff["exclusions"] = list(request["scope"]["exclude"])
        handoff["budget"]["confirmed"] = {
            "profile": request["budget"]["profile"],
            "limits": dict(request["budget"]["limits"]),
            "overrides": list(request["budget"]["confirmed_overrides"]),
        }
        handoff["budget"]["actual"]["discovery_queries"] = 1 + int(contrary)
        handoff["budget"]["actual"]["admitted_sources"] = source_count
        handoff["budget"]["actual"]["concurrent_workers_peak"] = 2
        handoff["budget"]["actual"]["external_tool_calls"] = 1 + int(contrary)
        context = json.loads(
            (ref.path / "context-manifest.json").read_text(encoding="utf-8")
        )
        handoff["budget"]["actual"]["context_bytes"] = context[
            "context_budget"
        ]["used"]
        if actual_budget_overrides:
            handoff["budget"]["actual"].update(actual_budget_overrides)
        handoff["canonical_artifacts"][0]["byte_length"] = len(synthesis_bytes)
        if artifact_overrides:
            handoff["canonical_artifacts"][0].update(artifact_overrides)
        handoff["custody"]["by_mode"]["TRACKED_CAS"] = source_count
        handoff["source_basis"][0]["artifact_id"] = request["request_id"]
        handoff["source_basis"][0]["sha256"] = request_digest
        context_digest, _ = fx.exact_file_sha256(
            ref.path / "context-manifest.json"
        )
        handoff["source_basis"][1].update(
            {
                "artifact_id": f"{ref.run_id}/context-manifest",
                "sha256": context_digest,
            }
        )
        handoff["authorities"] = {
            "requester_id": request["authority"]["requester_id"],
            "phase_owner_id": request["authority"]["phase_owner_id"],
            "decision_authority_id": request["authority"]["decision_authority_id"],
            "confirming_authority_id": request["authority"]["confirming_authority_id"],
            "escalation_owner_id": request["escalation_owner_id"],
        }
        handoff["source_refs"] = list(claim["source_refs"])
        handoff["evidence_refs"] = evidence_ids
        self.store.append_record(ref.slug, ref.run_id, "handoff", handoff)
        return request, ref

    def test_request_normalization_digest_is_deterministic(self) -> None:
        request = fx.load_request()
        reordered = dict(reversed(list(request.items())))
        first, first_digest = normalize_request(request)
        second, second_digest = normalize_request(reordered)
        self.assertEqual(first, second)
        self.assertEqual(first_digest, second_digest)
        self.assertEqual(first_digest, fx.canonical_sha256(first))

    def test_request_question_count_cannot_exceed_confirmed_budget(self) -> None:
        request = fx.load_request()
        second = json.loads(json.dumps(request["questions"][0]))
        second["question_id"] = "RQ-000002"
        request["questions"].append(second)
        with self.assertRaisesRegex(Exception, "E_BUDGET_ATOMIC_QUESTIONS"):
            self.store.normalize_request(request)
        self.assertFalse((self.workspace / ".devforgeai").exists())

    def test_budget_profile_increases_require_an_exact_named_override(self) -> None:
        request = fx.load_request()
        request["budget"]["limits"]["discovery_queries"] = 31
        with self.assertRaisesRegex(Exception, "E_BUDGET_OVERRIDE_MISSING"):
            self.store.normalize_request(request)

        request["budget"]["confirmed_overrides"] = [
            {
                "field": "discovery_queries",
                "value": 31,
                "authority_id": "person:other",
            }
        ]
        with self.assertRaisesRegex(Exception, "E_BUDGET_OVERRIDE_BINDING"):
            self.store.normalize_request(request)

        request["budget"]["confirmed_overrides"][0]["authority_id"] = request[
            "authority"
        ]["decision_authority_id"]
        normalized, _ = self.store.normalize_request(request)
        self.assertEqual(
            normalized["budget"]["confirmed_overrides"],
            request["budget"]["confirmed_overrides"],
        )

    def test_budget_override_cannot_be_duplicate_or_unnecessary(self) -> None:
        request = fx.load_request()
        override = {
            "field": "discovery_queries",
            "value": request["budget"]["limits"]["discovery_queries"],
            "authority_id": request["authority"]["decision_authority_id"],
        }
        request["budget"]["confirmed_overrides"] = [override]
        with self.assertRaisesRegex(Exception, "E_BUDGET_OVERRIDE_NOT_NEEDED"):
            self.store.normalize_request(request)

        request["budget"]["limits"]["discovery_queries"] = 31
        request["budget"]["confirmed_overrides"] = [override, copy.deepcopy(override)]
        for item in request["budget"]["confirmed_overrides"]:
            item["value"] = 31
        with self.assertRaisesRegex(Exception, "E_BUDGET_OVERRIDE_DUPLICATE"):
            self.store.normalize_request(request)

    def test_request_source_policy_uses_closed_nonconflicting_classes(self) -> None:
        request = fx.load_request()
        request["source_policy"]["required_classes"] = ["BLOG_RUMOR"]
        with self.assertRaisesRegex(Exception, "E_SOURCE_POLICY_REQUIRED_CLASS"):
            self.store.normalize_request(request)

        request = fx.load_request()
        request["source_policy"]["prohibited_classes"] = ["BLOG_RUMOR"]
        with self.assertRaisesRegex(Exception, "E_SOURCE_POLICY_PROHIBITED_CLASS"):
            self.store.normalize_request(request)

        request = fx.load_request()
        request["source_policy"]["prohibited_classes"].append("PRIMARY")
        with self.assertRaisesRegex(Exception, "E_SOURCE_POLICY_CLASS_CONFLICT"):
            self.store.normalize_request(request)

    def test_request_and_question_ids_are_unique_within_the_dossier(self) -> None:
        request = fx.load_request()
        normalized, digest = self.store.normalize_request(request)
        self.store.open_run(normalized, digest)

        repeated_request = fx.load_request()
        repeated_request["questions"][0]["question_id"] = "RQ-000002"
        normalized, digest = self.store.normalize_request(repeated_request)
        with self.assertRaisesRegex(Exception, "E_REQUEST_ID_REUSE"):
            self.store.open_run(normalized, digest)

        repeated_question = fx.load_request()
        repeated_question["request_id"] = "RSR-000002"
        normalized, digest = self.store.normalize_request(repeated_question)
        with self.assertRaisesRegex(Exception, "E_REQUEST_QUESTION_ID_REUSE"):
            self.store.open_run(normalized, digest)

        duplicate_in_one = fx.load_request()
        duplicate_in_one["request_id"] = "RSR-000003"
        second_question = json.loads(json.dumps(duplicate_in_one["questions"][0]))
        second_question["text"] = "Different text must not legitimize a reused RQ ID."
        duplicate_in_one["questions"].append(second_question)
        with self.assertRaisesRegex(Exception, "E_REQUEST_QUESTION_ID_DUPLICATE"):
            self.store.normalize_request(duplicate_in_one)

    def test_digest_mismatch_fails_before_any_canonical_write(self) -> None:
        normalized, digest = normalize_request(fx.load_request())
        before = sorted(path.relative_to(self.workspace) for path in self.workspace.rglob("*") if path.is_file())
        bad = ("0" if digest[0] != "0" else "1") + digest[1:]
        with self.assertRaises(Exception):
            self.store.open_run(normalized, bad)
        after = sorted(path.relative_to(self.workspace) for path in self.workspace.rglob("*") if path.is_file())
        self.assertEqual(before, after)

    def test_open_run_rejects_missing_runtime_write_fence(self) -> None:
        request = fx.load_request()
        request["execution_policy"]["write_fence"].remove(".devforgeai/research-locks")
        normalized, digest = normalize_request(request)
        with self.assertRaises(Exception):
            self.store.open_run(normalized, digest)

    def test_open_run_rejects_staging_symlink_escape(self) -> None:
        with tempfile.TemporaryDirectory() as outside_name:
            outside = Path(outside_name)
            devforge = self.workspace / ".devforgeai"
            devforge.mkdir()
            (devforge / "research-staging").symlink_to(
                outside, target_is_directory=True
            )
            normalized, digest = self.store.normalize_request(fx.load_request())
            with self.assertRaisesRegex(Exception, "(?i)symlink|resolution|outside"):
                self.store.open_run(normalized, digest)
            self.assertEqual(list(outside.iterdir()), [])

    def test_illegal_transition_fails_closed(self) -> None:
        _, _, ref = self.open_request()
        with self.assertRaises(Exception):
            self.store.transition(ref.slug, ref.run_id, "P4")
        resumed = self.store.transition(ref.slug, ref.run_id, "P1")
        self.assertEqual(resumed.phase, "P1")

    def test_singleton_phase_gates_fail_before_state_mutation(self) -> None:
        request = fx.load_request()
        normalized, digest = self.store.normalize_request(request)
        ref = self.store.open_run(normalized, digest)

        with self.assertRaisesRegex(Exception, "E_SINGLETON_MISSING:preflight"):
            self.store.transition(ref.slug, ref.run_id, "P1")
        self.assertEqual(self.store.resume_run(ref.slug, ref.run_id).phase, "P0")

        fx.install_preflight_contract(
            self.store, self.workspace, normalized, digest, ref
        )
        self.store.transition(ref.slug, ref.run_id, "P1")
        self.store.transition(ref.slug, ref.run_id, "P2")
        with self.assertRaisesRegex(
            Exception, "E_SINGLETON_MISSING:context-manifest"
        ):
            self.store.transition(ref.slug, ref.run_id, "P3")
        self.assertEqual(self.store.resume_run(ref.slug, ref.run_id).phase, "P2")

        fx.install_context_contract(
            self.store, self.workspace, normalized, digest, ref
        )
        self.store.transition(ref.slug, ref.run_id, "P3")
        with self.assertRaisesRegex(Exception, "E_SINGLETON_MISSING:plan"):
            self.store.transition(ref.slug, ref.run_id, "P4")
        self.assertEqual(self.store.resume_run(ref.slug, ref.run_id).phase, "P3")

        fx.install_plan_contract(
            self.store, self.workspace, normalized, digest, ref
        )
        self.store.transition(ref.slug, ref.run_id, "P4")
        self.store.transition(ref.slug, ref.run_id, "P5")
        self.store.transition(ref.slug, ref.run_id, "P6")
        with self.assertRaisesRegex(Exception, "E_SINGLETON_MISSING:reconciliation"):
            self.store.transition(ref.slug, ref.run_id, "P7")
        self.assertEqual(self.store.resume_run(ref.slug, ref.run_id).phase, "P6")

    def test_append_record_enforces_phase_fences_before_context_checks(self) -> None:
        request, digest, ref = self.open_request()
        self.store.transition(ref.slug, ref.run_id, "P1")
        question = fx.question()
        question["run_id"] = ref.run_id
        with self.assertRaisesRegex(Exception, "E_RECORD_PHASE"):
            self.store.append_record(ref.slug, ref.run_id, "question", question)

        self.store.transition(ref.slug, ref.run_id, "P2")
        self.store.append_record(ref.slug, ref.run_id, "question", question)
        fx.install_context_contract(
            self.store, self.workspace, request, digest, ref
        )
        self.store.transition(ref.slug, ref.run_id, "P3")
        query = fx.query()
        query["run_id"] = ref.run_id
        with self.assertRaisesRegex(Exception, "E_RECORD_PHASE"):
            self.store.append_record(ref.slug, ref.run_id, "query", query)

        fx.install_plan_contract(
            self.store, self.workspace, request, digest, ref
        )
        self.store.transition(ref.slug, ref.run_id, "P4")
        wrong_phase_records = {
            "evidence": fx.evidence(
                "EVD-000001", "SRC-000001", "f" * 64, "Synthetic content."
            ),
            "claim": fx.claim(),
            "contradiction": fx.contradiction(),
            "verification": fx.verification(fx.claim()),
            "synthesis": fx.synthesis(),
            "handoff": fx.handoff("a" * 64, run_id=ref.run_id),
        }
        for kind, record in wrong_phase_records.items():
            record["run_id"] = ref.run_id
            with self.subTest(kind=kind):
                with self.assertRaisesRegex(Exception, "E_RECORD_PHASE"):
                    self.store.append_record(ref.slug, ref.run_id, kind, record)

    def test_query_is_bound_to_its_planned_lane_envelope_and_purpose(self) -> None:
        _, _, ref = self.open_request()
        self.advance(ref, 2)
        question = fx.question()
        question["run_id"] = ref.run_id
        self.store.append_record(ref.slug, ref.run_id, "question", question)
        self.advance(ref, 4)

        cases = (
            ("lane_id", "LANE-999999", "E_QUERY_PLAN_LANE"),
            ("worker_envelope_id", "ENV-000002", "E_QUERY_PLAN_ENVELOPE"),
            ("purpose", "CHALLENGE", "E_QUERY_LANE_PURPOSE"),
        )
        for field, value, error in cases:
            with self.subTest(field=field):
                query = fx.query()
                query["run_id"] = ref.run_id
                query[field] = value
                with self.assertRaisesRegex(Exception, error):
                    self.store.append_record(
                        ref.slug, ref.run_id, "query", query
                    )

        contrary = fx.challenge_query()
        contrary["run_id"] = ref.run_id
        contrary["purpose"] = "DISCOVERY"
        with self.assertRaisesRegex(Exception, "E_QUERY_LANE_PURPOSE"):
            self.store.append_record(ref.slug, ref.run_id, "query", contrary)

    def test_query_attempts_cannot_exceed_lane_or_envelope_budget(self) -> None:
        _, _, ref = self.open_request()
        self.advance(ref, 2)
        question = fx.question()
        question["run_id"] = ref.run_id
        self.store.append_record(ref.slug, ref.run_id, "question", question)
        self.advance(ref, 4)

        first = fx.query()
        first["run_id"] = ref.run_id
        self.store.append_record(ref.slug, ref.run_id, "query", first)

        plan_path = ref.path / "plan.json"
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        plan["worker_envelopes"][0]["budgets"]["queries"] = 1
        plan_path.write_bytes(canonical_json(plan) + b"\n")
        second = copy.deepcopy(first)
        second.update(
            {
                "record_id": "QRY-000003",
                "query_id": "QRY-000003",
                "results": [],
            }
        )
        with self.assertRaisesRegex(Exception, "E_QUERY_ENVELOPE_QUERY_LIMIT"):
            self.store.append_record(ref.slug, ref.run_id, "query", second)

        plan["worker_envelopes"][0]["budgets"]["queries"] = 2
        plan["lanes"][0]["query_limit"] = 1
        plan_path.write_bytes(canonical_json(plan) + b"\n")
        with self.assertRaisesRegex(Exception, "E_QUERY_LANE_QUERY_LIMIT"):
            self.store.append_record(ref.slug, ref.run_id, "query", second)

    def test_question_semantics_are_bound_to_the_confirmed_request(self) -> None:
        request, _, ref = self.open_request()
        self.advance(ref, 2)
        for field, replacement in (
            ("text", "A different question with the same identifier."),
            ("completion_criteria", ["A different completion contract."]),
            ("priority", "MATERIAL"),
        ):
            with self.subTest(field=field):
                record = copy.deepcopy(fx.question())
                record["run_id"] = ref.run_id
                record[field] = replacement
                with self.assertRaisesRegex(Exception, "E_QUESTION_REQUEST_BINDING"):
                    self.store.append_record(ref.slug, ref.run_id, "question", record)
        canonical = fx.question()
        canonical["run_id"] = ref.run_id
        canonical["text"] = request["questions"][0]["text"]
        canonical["completion_criteria"] = request["questions"][0][
            "completion_criteria"
        ]
        canonical["priority"] = request["risk_tier"]
        self.store.append_record(ref.slug, ref.run_id, "question", canonical)

    def test_repair_transitions_survive_state_chain_resume(self) -> None:
        for through, target in ((6, "P4"), (7, "P5")):
            with self.subTest(repair=f"P{through}->{target}"):
                if through == 6:
                    _, _, ref = self.open_request(id_offset=through * 100)
                    self.advance(ref, through)
                else:
                    _, ref = self.build_to_p8(
                        id_offset=through * 100, stop_at_p7=True
                    )
                repaired = self.store.transition(
                    ref.slug, ref.run_id, target, reason="bounded repair loop"
                )
                self.assertEqual(repaired.phase, target)
                resumed = ResearchStore(
                    self.workspace, allow_offline_test_harness=True
                ).resume_run(ref.slug, ref.run_id)
                self.assertEqual(resumed.phase, target)
                state_path = (
                    self.workspace
                    / ".devforgeai"
                    / "research-staging"
                    / ref.slug
                    / ref.run_id
                    / "state.jsonl"
                )
                events = [
                    json.loads(line) for line in state_path.read_text().splitlines()
                ]
                self.assertEqual(events[-1]["from_phase"], f"P{through}")
                self.assertEqual(events[-1]["to_phase"], target)
                self.assertEqual(
                    events[-1]["previous_event_sha256"],
                    fx.canonical_sha256(events[-2]),
                )

    def test_concurrent_duplicate_record_has_one_canonical_entry(self) -> None:
        _, _, ref = self.open_request()
        self.advance(ref, 2)
        record = fx.question()
        record["run_id"] = ref.run_id
        barrier = threading.Barrier(2)
        results: list[object] = []

        def append() -> None:
            barrier.wait()
            try:
                results.append(self.store.append_record(ref.slug, ref.run_id, "question", record))
            except Exception as exc:  # the losing writer may receive a collision
                results.append(exc)

        threads = [threading.Thread(target=append) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=5)
        self.assertFalse(any(thread.is_alive() for thread in threads))
        successes = [item for item in results if isinstance(item, str)]
        self.assertGreaterEqual(len(successes), 1)
        run_path = self.workspace / ".devforgeai" / "research-staging" / ref.slug / ref.run_id
        records = [json.loads(line) for line in (run_path / "questions.jsonl").read_text().splitlines()]
        matching = [record for record in records if record.get("record_id") == "RQ-000001"]
        self.assertEqual(len(matching), 1, "concurrent writers must not duplicate a canonical record ID")

    def test_writer_collision_fails_without_blocking(self) -> None:
        _, _, ref = self.open_request()
        lock_path = self.workspace / ".devforgeai" / "research-locks" / f"{ref.slug}.lock"
        holder = subprocess.Popen(
            [
                sys.executable,
                "-c",
                (
                    "import fcntl,sys; "
                    "stream=open(sys.argv[1], 'r+'); "
                    "fcntl.flock(stream.fileno(), fcntl.LOCK_EX); "
                    "print('LOCKED', flush=True); sys.stdin.read(1)"
                ),
                str(lock_path),
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            self.assertEqual(holder.stdout.readline().strip(), "LOCKED")
            started = time.monotonic()
            with self.assertRaisesRegex(Exception, "E_WRITER_COLLISION"):
                self.store.validate_run(ref.slug, ref.run_id)
            self.assertLess(time.monotonic() - started, 2.0)
        finally:
            holder.communicate("x", timeout=5)

    def test_source_cas_preserves_exact_bytes_and_local_only_fallback(self) -> None:
        _, _, ref = self.open_request()
        self.advance(ref, 5)
        result = self.put_fixture_source(
            ref,
            "SRC-000001",
            "source-primary.txt",
            "Private Synthetic Owner",
            mode="LOCAL_ONLY_CAS",
            query_ids=[],
        )
        object_path = self.source_object_path(result)
        self.assertRegex(
            object_path,
            r"^\.devforgeai/research-cas/sha256/[a-f0-9]{2}/[a-f0-9]{64}$",
        )
        actual = (self.workspace / object_path).read_bytes()
        expected = (fx.FIXTURES / "source-primary.txt").read_bytes()
        self.assertEqual(actual, expected)
        self.assertEqual(self.source_digest(result), hashlib.sha256(expected).hexdigest())

    def test_network_policy_denies_network_retrieval_before_cas_mutation(self) -> None:
        query = fx.query()
        query["results"][0]["locator"] = (
            "https://blocked.example/source-primary.txt"
        )
        _, ref = self.prepare_p5(query_record=query)
        metadata = fx.source_metadata(
            "SRC-000001", "source-primary.txt", publisher="Synthetic Owner"
        )
        metadata["run_id"] = ref.run_id
        metadata["locator"] = {
            "kind": "URL",
            "value": "https://blocked.example/source-primary.txt",
        }
        metadata["retrieval"].update(
            {"method": "WEB", "network_accessed": True}
        )
        metadata["custody"] = {"mode": "TRACKED_CAS"}
        with self.assertRaisesRegex(Exception, "E_NETWORK_DENY"):
            self.store.put_source(
                ref.slug,
                ref.run_id,
                "SRC-000001",
                self.copy_source("source-primary.txt"),
                metadata,
            )
        self.assertFalse(
            (self.workspace / "docs" / "research" / "_cas" / "sha256").exists()
        )

    def test_network_allowlist_uses_exact_canonical_origin(self) -> None:
        request = fx.load_request()
        request["execution_policy"].update(
            {
                "network_policy": "ALLOWLIST",
                "network_allowlist": ["https://allowed.example"],
            }
        )
        query = fx.query()
        query["results"][0]["locator"] = (
            "https://not-allowed.example/source-primary.txt"
        )
        query["results"].append(
            {
                "candidate_id": "QRY-000001-CAND-000002",
                "locator": "https://allowed.example/path/to/source",
                "title": "Allowed synthetic source",
                "discovery_only": True,
                "disposition": "RETRIEVE",
                "reason": "Exercise an exact canonical-origin allowlist match.",
            }
        )
        _, ref = self.prepare_p5(request, query_record=query)
        metadata = fx.source_metadata(
            "SRC-000001", "source-primary.txt", publisher="Synthetic Owner"
        )
        metadata["run_id"] = ref.run_id
        metadata["retrieval"].update(
            {"method": "WEB", "network_accessed": True}
        )
        metadata["custody"] = {"mode": "TRACKED_CAS"}
        metadata["locator"] = {
            "kind": "URL",
            "value": "https://not-allowed.example/source-primary.txt",
        }
        with self.assertRaisesRegex(Exception, "E_NETWORK_ALLOWLIST"):
            self.store.put_source(
                ref.slug,
                ref.run_id,
                "SRC-000001",
                self.copy_source("source-primary.txt"),
                metadata,
            )
        metadata["locator"]["value"] = "https://allowed.example/path/to/source"
        metadata["candidate_ids"] = ["QRY-000001-CAND-000002"]
        admitted = self.store.put_source(
            ref.slug,
            ref.run_id,
            "SRC-000001",
            self.copy_source("source-primary.txt"),
            metadata,
        )
        self.assertEqual(admitted["retrieval"]["network_accessed"], True)

    def test_prohibited_source_class_cannot_be_admitted(self) -> None:
        request = fx.load_request()
        request["source_policy"]["prohibited_classes"].append("SECONDARY")
        _, ref = self.prepare_p5(request)
        metadata = fx.source_metadata(
            "SRC-000001",
            "source-primary.txt",
            publisher="Synthetic Secondary Publisher",
            source_class="SECONDARY",
        )
        metadata["run_id"] = ref.run_id
        metadata["custody"] = {"mode": "TRACKED_CAS"}
        with self.assertRaisesRegex(Exception, "E_SOURCE_POLICY_PROHIBITED"):
            self.store.put_source(
                ref.slug,
                ref.run_id,
                "SRC-000001",
                self.copy_source("source-primary.txt"),
                metadata,
            )

    def test_unlicensed_excerpt_limit_is_cumulative_per_source(self) -> None:
        _, ref = self.prepare_p5()
        source = self.put_fixture_source(
            ref,
            "SRC-000001",
            "source-primary.txt",
            "Private Synthetic Owner",
            mode="LOCAL_ONLY_CAS",
        )
        allowed_text = " ".join(f"word{number}" for number in range(1, 26))
        allowed = fx.evidence(
            "EVD-000001",
            "SRC-000001",
            self.source_digest(source),
            allowed_text,
        )
        allowed["representation"] = "EXCERPT"
        self.append_evidence(ref, allowed)

        overflow = fx.evidence(
            "EVD-000002",
            "SRC-000001",
            self.source_digest(source),
            "overflow",
        )
        overflow["representation"] = "EXCERPT"
        with self.assertRaisesRegex(Exception, "E_EXCERPT_WORD_LIMIT"):
            self.append_evidence(ref, overflow)

        licensed_source = self.put_fixture_source(
            ref,
            "SRC-000002",
            "source-corroborating.txt",
            "Licensed Synthetic Owner",
            query_ids=[],
        )
        licensed_text = " ".join(f"licensed{number}" for number in range(1, 31))
        licensed = fx.evidence(
            "EVD-000003",
            "SRC-000002",
            self.source_digest(licensed_source),
            licensed_text,
        )
        licensed["representation"] = "EXCERPT"
        self.append_evidence(ref, licensed)

    def test_candidate_link_is_single_use_and_retrieve_only(self) -> None:
        _, ref = self.prepare_p5()
        self.put_fixture_source(
            ref,
            "SRC-000001",
            "source-primary.txt",
            "Synthetic Owner A",
        )
        with self.assertRaisesRegex(Exception, "E_SOURCE_CANDIDATE_REUSE"):
            self.put_fixture_source(
                ref,
                "SRC-000002",
                "source-primary.txt",
                "Synthetic Owner B",
            )

    def test_source_cannot_link_a_nonretrieve_candidate(self) -> None:
        query = fx.query()
        query["results"][0]["disposition"] = "BIBLIOGRAPHY_ONLY"
        query["results"][0]["reason"] = "Metadata is sufficient for bibliography."
        _, ref = self.prepare_p5(query_record=query)
        with self.assertRaisesRegex(Exception, "E_SOURCE_CANDIDATE_NOT_RETRIEVE"):
            self.put_fixture_source(
                ref,
                "SRC-000001",
                "source-primary.txt",
                "Synthetic Owner",
            )

    def test_metadata_only_sources_use_append_record_without_cas_objects(self) -> None:
        _, _, ref = self.open_request()
        self.advance(ref, 5)
        for number, mode in enumerate(("EXTRACT_ONLY", "NONE"), 1):
            source_id = f"SRC-{number:06d}"
            metadata = fx.source_metadata(
                source_id, "source-primary.txt", publisher="Synthetic Owner"
            )
            metadata["run_id"] = ref.run_id
            metadata["query_ids"] = []
            metadata["candidate_ids"] = []
            metadata["admission"] = "BIBLIOGRAPHY_ONLY"
            metadata["retention_policy"].update(
                {
                    "retention_permitted": False,
                    "redistribution_basis": "NONE",
                    "redistribution_reference": None,
                }
            )
            metadata["retention_policy"]["sensitive_scan"].update(
                {"status": "NOT_RUN", "findings_count": 0}
            )
            metadata["custody"] = {
                "mode": mode,
                "retention_reason": "Synthetic metadata-only source.",
            }
            self.store.append_record(
                ref.slug, ref.run_id, "source", metadata
            )
        source_file = (
            self.workspace
            / ".devforgeai"
            / "research-staging"
            / ref.slug
            / ref.run_id
            / "sources.jsonl"
        )
        sources = [json.loads(line) for line in source_file.read_text().splitlines()]
        self.assertEqual(
            [item["custody"]["mode"] for item in sources],
            ["EXTRACT_ONLY", "NONE"],
        )
        self.assertFalse((self.workspace / ".devforgeai" / "research-cas").exists())

    def test_put_source_rejects_retention_prohibited_bytes(self) -> None:
        _, _, ref = self.open_request()
        self.advance(ref, 5)
        metadata = fx.source_metadata(
            "SRC-000001", "source-primary.txt", publisher="Synthetic Owner"
        )
        metadata["run_id"] = ref.run_id
        metadata["custody"] = {"mode": "LOCAL_ONLY_CAS"}
        metadata["retention_policy"]["retention_permitted"] = False
        with self.assertRaises(Exception):
            self.store.put_source(
                ref.slug,
                ref.run_id,
                "SRC-000001",
                self.copy_source("source-primary.txt"),
                metadata,
            )

    def test_put_source_rejects_missing_source_and_out_of_fence_cas(self) -> None:
        _, _, ref = self.open_request()
        self.advance(ref, 5)
        metadata = fx.source_metadata(
            "SRC-000001", "source-primary.txt", publisher="Synthetic Owner"
        )
        metadata["run_id"] = ref.run_id
        metadata["query_ids"] = []
        metadata["candidate_ids"] = []
        metadata["custody"] = {"mode": "TRACKED_CAS"}
        with self.subTest("missing"):
            with self.assertRaises(Exception):
                self.store.put_source(
                    ref.slug,
                    ref.run_id,
                    "SRC-000001",
                    self.workspace / "inputs" / "missing-source.txt",
                    metadata,
                )
        escape = self.workspace / "escaped-cas"
        escape.mkdir()
        cas_link = self.workspace / ".devforgeai" / "research-cas"
        cas_link.symlink_to(escape, target_is_directory=True)
        metadata["custody"] = {"mode": "LOCAL_ONLY_CAS"}
        metadata["retention_policy"].update(
            {
                "redistribution_basis": "NONE",
                "redistribution_reference": None,
                "data_classification": "INTERNAL",
            }
        )
        metadata["retention_policy"]["sensitive_scan"]["status"] = "NOT_RUN"
        with self.subTest("resolved-cas-outside-fence"):
            with self.assertRaises(Exception):
                self.store.put_source(
                    ref.slug,
                    ref.run_id,
                    "SRC-000001",
                    self.copy_source("source-primary.txt"),
                    metadata,
                )

    def test_referential_integrity_rejects_missing_source(self) -> None:
        _, _, ref = self.open_request()
        self.advance(ref, 5)
        missing = fx.evidence("EVD-000001", "SRC-999999", "f" * 64, "Missing source.")
        missing["run_id"] = ref.run_id
        try:
            self.store.append_record(ref.slug, ref.run_id, "evidence", missing)
        except Exception:
            return
        report = self.store.validate_run(ref.slug, ref.run_id)
        self.assertFalse(report_ok(report), report_text(report))
        self.assertIn("source", report_text(report).lower())

    def test_evidence_requires_retrieved_and_evidence_admitted_source(self) -> None:
        _, _, ref = self.open_request()
        self.advance(ref, 2)
        question = fx.question()
        question["run_id"] = ref.run_id
        self.store.append_record(ref.slug, ref.run_id, "question", question)
        self.advance(ref, 4)
        query = fx.query()
        query["run_id"] = ref.run_id
        self.store.append_record(ref.slug, ref.run_id, "query", query)
        self.store.transition(ref.slug, ref.run_id, "P5")

        cases = (
            ("SRC-000001", "EVD-000001", "source-primary.txt", "RETRIEVED"),
            ("SRC-000002", "EVD-000002", "source-corroborating.txt", "PARTIAL"),
        )
        for source_id, evidence_id, fixture_name, retrieval in cases:
            metadata = fx.source_metadata(
                source_id, fixture_name, publisher=f"Synthetic {source_id}"
            )
            metadata["run_id"] = ref.run_id
            if source_id == "SRC-000002":
                metadata["query_ids"] = []
                metadata["candidate_ids"] = []
            metadata["admission"] = "ADMITTED_CONTEXT"
            metadata["retrieval"]["status"] = retrieval
            if retrieval == "PARTIAL":
                metadata["retrieval"]["limitation"] = "Only a bounded part was retrieved."
            metadata["custody"] = {"mode": "TRACKED_CAS"}
            source = self.store.put_source(
                ref.slug,
                ref.run_id,
                source_id,
                self.copy_source(fixture_name),
                metadata,
            )
            record = fx.evidence(
                evidence_id,
                source_id,
                self.source_digest(source),
                "This must not become supporting evidence.",
            )
            record["run_id"] = ref.run_id
            with self.subTest(retrieval=retrieval):
                with self.assertRaisesRegex(Exception, "E_G5_SOURCE_NOT_ADMITTED"):
                    self.store.append_record(
                        ref.slug, ref.run_id, "evidence", record
                    )

    def test_current_source_cannot_be_stale_at_request_as_of(self) -> None:
        request, _, ref = self.open_request()
        self.advance(ref, 2)
        question = fx.question()
        question["run_id"] = ref.run_id
        self.store.append_record(ref.slug, ref.run_id, "question", question)
        self.advance(ref, 4)
        query = fx.query()
        query["run_id"] = ref.run_id
        self.store.append_record(ref.slug, ref.run_id, "query", query)
        self.store.transition(ref.slug, ref.run_id, "P5")
        metadata = fx.source_metadata(
            "SRC-000001", "source-primary.txt", publisher="Synthetic Owner"
        )
        metadata["run_id"] = ref.run_id
        metadata["custody"] = {"mode": "TRACKED_CAS"}
        metadata["freshness"]["status"] = "CURRENT"
        metadata["freshness"]["stale_after"] = request["as_of"]
        try:
            self.store.put_source(
                ref.slug,
                ref.run_id,
                "SRC-000001",
                self.copy_source("source-primary.txt"),
                metadata,
            )
        except Exception as exc:
            self.assertRegex(str(exc).lower(), "fresh|stale")
            return
        report = self.store.validate_run(ref.slug, ref.run_id)
        self.assertFalse(report_ok(report), report_text(report))
        self.assertRegex(report_text(report).lower(), "fresh|stale")

    def test_material_claim_requires_independent_corroboration(self) -> None:
        with self.assertRaisesRegex(Exception, "E_G7_VERIFICATION"):
            self.build_to_p8(material=True, corroborate=False)

    def test_material_corroboration_rejects_duplicate_source_bytes(self) -> None:
        with self.assertRaisesRegex(Exception, "E_G7_VERIFICATION"):
            self.build_to_p8(
                material=True,
                corroborate=True,
                duplicate_corroboration_bytes=True,
            )

    def test_material_pass_is_unavailable_without_canonical_independence(self) -> None:
        with self.assertRaisesRegex(
            Exception,
            "E_NOT_IMPLEMENTED_MATERIAL_INDEPENDENCE",
        ):
            self.build_to_p8(material=True, corroborate=True)

    def test_contrary_lane_and_disposition_are_required(self) -> None:
        with self.assertRaisesRegex(
            Exception, "E_RECONCILIATION_CONTRARY_TERMINAL"
        ):
            self.build_to_p8(contrary=False)

    def test_failed_challenge_query_does_not_satisfy_contrary_lane(self) -> None:
        with self.assertRaisesRegex(Exception, "E_RECONCILIATION_NOT_PASS"):
            self.build_to_p8(failed_challenge=True)

    def test_no_publication_without_independent_verification(self) -> None:
        with self.assertRaisesRegex(Exception, "E_G7_VERIFICATION"):
            self.build_to_p8(verify=False)
        runs = list(
            (self.workspace / ".devforgeai" / "research-staging" / "offline-fixture").iterdir()
        )
        self.assertEqual(len(runs), 1)
        ref = self.store.resume_run("offline-fixture", runs[0].name)
        self.assertEqual(ref.phase, "P7")
        self.assertFalse(
            (self.workspace / "docs" / "research" / "offline-fixture" / "runs").exists()
        )

    def test_p7_to_p8_requires_the_current_verification_to_pass(self) -> None:
        _, ref = self.build_to_p8(stop_at_p7=True)
        claim = json.loads(
            (ref.path / "claims.jsonl").read_text(encoding="utf-8").splitlines()[0]
        )
        packet_ref = self.store.build_verification_packet(
            ref.slug, ref.run_id, claim["claim_id"]
        )["packet_ref"]
        failed = fx.verification(
            claim,
            packet_ref=packet_ref,
            outcome="FAIL",
            provider_conformance_path=ref.path / "provider-conformance.json",
        )
        failed["run_id"] = ref.run_id
        self.store.append_record(ref.slug, ref.run_id, "verification", failed)
        with self.assertRaisesRegex(Exception, "E_G7_VERIFICATION"):
            self.store.transition(ref.slug, ref.run_id, "P8")
        self.assertEqual(self.store.resume_run(ref.slug, ref.run_id).phase, "P7")

        passed = fx.verification(
            claim,
            packet_ref=packet_ref,
            outcome="PASS",
            provider_conformance_path=ref.path / "provider-conformance.json",
        )
        passed.update(
            {
                "record_id": "VER-000002",
                "verification_id": "VER-000002",
                "run_id": ref.run_id,
            }
        )
        self.store.append_record(ref.slug, ref.run_id, "verification", passed)
        transitioned = self.store.transition(ref.slug, ref.run_id, "P8")
        self.assertEqual(transitioned.phase, "P8")

    def test_synthesis_disposition_cannot_reference_unpublishable_claim(self) -> None:
        _, ref = self.build_to_p8()
        claim = json.loads(
            (ref.path / "claims.jsonl").read_text(encoding="utf-8").splitlines()[0]
        )
        existing_verification = json.loads(
            (ref.path / "verifications.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()[0]
        )
        failed = fx.verification(
            claim,
            packet_ref=existing_verification["packet_ref"],
            outcome="FAIL",
            provider_conformance_path=ref.path / "provider-conformance.json",
        )
        failed["run_id"] = ref.run_id
        (ref.path / "verifications.jsonl").write_bytes(
            canonical_json(failed) + b"\n"
        )

        report = self.store.validate_run(ref.slug, ref.run_id)
        self.assertFalse(report_ok(report), report_text(report))
        self.assertIn(
            "E_SYNTHESIS_DISPOSITION_UNPUBLISHABLE_CLAIM",
            report.errors,
        )

    def test_same_author_and_verifier_session_is_not_independent(self) -> None:
        with self.assertRaisesRegex(Exception, "E_VERIFICATION_INDEPENDENCE"):
            self.build_to_p8(same_author_verifier=True)

    def test_pass_verification_must_cover_claim_support(self) -> None:
        with self.assertRaisesRegex(Exception, "E_VERIFICATION_SUPPORT_COVERAGE"):
            self.build_to_p8(verification_omits_support=True)

    def test_stale_source_cannot_be_admitted_as_claim_support(self) -> None:
        with self.assertRaisesRegex(Exception, "(?i)stale"):
            self.build_to_p8(stale_primary=True)

    def test_unimplemented_claim_classes_fail_closed_at_close(self) -> None:
        _, ref = self.build_to_p8(claim_type="INFERENCE")
        report = self.store.validate_run(ref.slug, ref.run_id)
        self.assertFalse(report_ok(report), report_text(report))
        self.assertIn("E_NOT_IMPLEMENTED_CLAIM_CLASS", report_text(report))

    def test_handoff_is_a_singleton_canonical_record(self) -> None:
        _, ref = self.build_to_p8()
        duplicate = fx.handoff("a" * 64, run_id=ref.run_id, slug=ref.slug)
        duplicate["record_id"] = "HND-000002"
        duplicate["handoff_id"] = "HND-000002"
        with self.assertRaisesRegex(Exception, "E_HANDOFF_SINGLETON"):
            self.store.append_record(ref.slug, ref.run_id, "handoff", duplicate)

    def test_handoff_artifacts_are_existing_fenced_exact_bytes(self) -> None:
        hostile = (
            ({"sha256": "0" * 64}, "E_HANDOFF_ARTIFACT_SHA256"),
            ({"byte_length": 0}, "E_HANDOFF_ARTIFACT_BYTE_LENGTH"),
            ({"path": "missing.jsonl"}, "E_HANDOFF_ARTIFACT_MISSING_OR_ESCAPE"),
            ({"path": "../request.json"}, "E_SCHEMA_HANDOFF"),
            ({"version": "2"}, "E_HANDOFF_ARTIFACT_SEMANTICS"),
            ({"lifecycle_status": "ACCEPTED"}, "E_HANDOFF_ARTIFACT_SEMANTICS"),
            ({"readiness_status": "STALE"}, "E_HANDOFF_ARTIFACT_SEMANTICS"),
            ({"verification_status": "PASS"}, "E_HANDOFF_ARTIFACT_SEMANTICS"),
            ({"owner": "forged-owner"}, "E_HANDOFF_ARTIFACT_SEMANTICS"),
        )
        for index, (overrides, expected) in enumerate(hostile):
            with self.subTest(overrides=overrides):
                with self.assertRaisesRegex(Exception, expected):
                    self.build_to_p8(
                        id_offset=index * 100,
                        artifact_overrides=overrides,
                    )

    def test_handoff_contradiction_and_validation_details_are_bound(self) -> None:
        _, ref = self.build_to_p8()
        handoff_path = ref.path / "handoff.json"
        original = json.loads(handoff_path.read_text(encoding="utf-8"))

        def forged_contradiction(record: dict) -> None:
            record["contrary_evidence"]["contradictions"][0]["scope"] = (
                "A different contradiction scope."
            )

        def missing_validation_evidence(record: dict) -> None:
            record["validation"]["checks"][0]["evidence_ids"] = ["EVD-999999"]

        def nonpass_validation(record: dict) -> None:
            record["validation"]["checks"][0]["status"] = "FAIL"

        cases = (
            (forged_contradiction, "E_HANDOFF_CONTRADICTION_DETAILS"),
            (missing_validation_evidence, "E_HANDOFF_VALIDATION_EVIDENCE"),
            (nonpass_validation, "E_HANDOFF_VALIDATION_NOT_PASS"),
        )
        for mutate, expected in cases:
            with self.subTest(expected=expected):
                hostile = copy.deepcopy(original)
                mutate(hostile)
                handoff_path.write_bytes(canonical_json(hostile) + b"\n")
                report = self.store.validate_run(ref.slug, ref.run_id)
                self.assertFalse(report_ok(report), report_text(report))
                self.assertIn(expected, report_text(report))
        handoff_path.write_bytes(canonical_json(original) + b"\n")

    def test_all_handoff_budget_actuals_are_bounded_by_confirmed_limits(self) -> None:
        request = fx.load_request()
        limits = request["budget"]["limits"]
        cases = {
            "atomic_questions": limits["atomic_questions"] + 1,
            "research_lanes": limits["research_lanes"] + 1,
            "concurrent_workers_peak": limits["concurrent_workers"] + 1,
            "discovery_queries": limits["discovery_queries"] + 1,
            "admitted_sources": limits["admitted_sources"] + 1,
            "external_tool_calls": limits["external_tool_calls"] + 1,
            "aggregate_model_tokens": limits["aggregate_model_tokens"] + 1,
            "elapsed_minutes": limits["elapsed_minutes"] + 1,
            "retries": (
                limits["retry_per_failed_lane"] * limits["research_lanes"]
            )
            + 1,
        }
        for index, (field, value) in enumerate(cases.items()):
            with self.subTest(field=field):
                with self.assertRaisesRegex(
                    Exception, f"E_BUDGET_{field.upper()}"
                ):
                    self.build_to_p8(
                        id_offset=index * 100,
                        actual_budget_overrides={field: value},
                    )

    def test_every_retrieve_candidate_requires_exactly_one_source_attempt(self) -> None:
        with self.assertRaisesRegex(Exception, "E_QUERY_CANDIDATE_CLOSURE"):
            self.build_to_p8(unfulfilled_retrieve_candidate=True)

    def test_handoff_freshness_counts_match_explicit_source_statuses(self) -> None:
        _, ref = self.build_to_p8(freshness_count_delta=1)
        report = self.store.validate_run(ref.slug, ref.run_id)
        self.assertFalse(report_ok(report), report_text(report))
        self.assertIn("fresh", report_text(report).lower())

    def test_seal_is_idempotent_immutable_and_manifest_verifies(self) -> None:
        _, ref = self.build_to_p8()
        report = self.store.validate_run(ref.slug, ref.run_id)
        self.assertTrue(report_ok(report), report_text(report))
        self.store.transition(ref.slug, ref.run_id, "P9", reason="preseal gates passed")
        validation = json.loads(
            (ref.path / "validation.json").read_text(encoding="utf-8")
        )
        self.assertEqual(validation["gate_status"], "READY_TO_SEAL")
        checks = {item["check_id"]: item for item in validation["checks"]}
        self.assertEqual(
            checks["CLAIM_DAG"]["status"],
            "NOT_APPLICABLE",
        )
        self.assertEqual(
            checks["DISPUTE_OWNERSHIP"]["status"],
            "NOT_APPLICABLE",
        )
        self.assertTrue(
            all(item["evidence"] for item in checks.values() if item["applicable"])
        )
        self.assertGreater(len({item["reason"] for item in checks.values()}), 20)
        handoff_before_seal = json.loads(
            (ref.path / "handoff.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            handoff_before_seal["result"]["outcome"], "READY_TO_SEAL"
        )
        state_events = [
            json.loads(line)
            for line in (ref.path / "state.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        self.assertEqual(state_events[-1]["to_phase"], "P9")
        self.assertEqual(state_events[-1]["reason_code"], "READY_TO_SEAL")
        self.assertNotEqual(state_events[-1].get("outcome"), "COMPLETE")
        with self.assertRaises(Exception):
            self.store.append_record(ref.slug, ref.run_id, "question", fx.question())

        with mock.patch.object(
            research_core,
            "_utc_now",
            return_value="2030-01-02T03:04:05Z",
        ):
            final_path = self.store.seal_run(ref.slug, ref.run_id)
        self.assertEqual(final_path, self.store.seal_run(ref.slug, ref.run_id))
        self.assertTrue((final_path / "MANIFEST.sha256").is_file())
        self.assertTrue((final_path / "handoff.json").is_file())
        self.assertFalse((final_path / "handoffs.jsonl").exists())
        registry_path = (
            self.workspace / "docs" / "research" / ref.slug / "registry.jsonl"
        )
        self.assertTrue(registry_path.is_file())
        registry_entry = json.loads(registry_path.read_text(encoding="utf-8").splitlines()[-1])
        self.assertEqual(registry_entry["run_id"], ref.run_id)
        self.assertEqual(registry_entry["previous_entry_sha256"], None)
        self.assertEqual(registry_entry["outcome"], "COMPLETE")
        self.assertEqual(registry_entry["sealed_at_utc"], "2030-01-02T03:04:05Z")
        self.assertNotEqual(
            registry_entry["sealed_at_utc"],
            handoff_before_seal["rendered_at"],
        )
        receipt = self.store.seal_result(ref.slug, ref.run_id)
        self.assertEqual(
            set(receipt),
            {
                "schema_version",
                "run_id",
                "sealed_run_path",
                "handoff",
                "manifest_sha256",
                "registry",
                "readback",
            },
        )
        self.assertEqual(receipt["schema_version"], "research-seal-receipt/v1")
        self.assertEqual(
            receipt["readback"], {"outcome": "COMPLETE", "status": "PASS"}
        )
        self.assertEqual(
            receipt["handoff"]["result"]["outcome"], "READY_TO_SEAL"
        )
        self.assertNotIn("manifest_sha256", receipt["handoff"])
        self.assertTrue(report_ok(self.store.verify_run(ref.slug, ref.run_id)))
        with self.assertRaises(Exception):
            self.store.append_record(ref.slug, ref.run_id, "question", fx.question())

    def test_seal_retry_finishes_publication_after_final_move_interruption(self) -> None:
        _, ref = self.build_to_p8()
        self.store.transition(ref.slug, ref.run_id, "P9")
        final_path = self.store._final(ref.slug, ref.run_id)

        with mock.patch.object(
            self.store,
            "_finish_publication",
            side_effect=OSError("injected failure immediately after final move"),
        ):
            with self.assertRaisesRegex(OSError, "immediately after final move"):
                self.store.seal_run(ref.slug, ref.run_id)

        self.assertTrue(final_path.is_dir())
        self.assertFalse(ref.path.exists())
        self.assertFalse(self.store._registry(ref.slug).exists())

        self.assertEqual(self.store.seal_run(ref.slug, ref.run_id), final_path)
        entries = self.store._registry_entries(ref.slug)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["run_id"], ref.run_id)
        self.assertEqual(entries[0]["outcome"], "COMPLETE")
        self.assertTrue(report_ok(self.store.verify_run(ref.slug, ref.run_id)))

    def test_complete_is_not_appended_before_all_root_views_read_back(self) -> None:
        _, ref = self.build_to_p8()
        self.store.transition(ref.slug, ref.run_id, "P9")
        root = self.workspace / "docs" / "research" / ref.slug
        fail_target = root / "synthesis.md"
        real_atomic = research_core._atomic

        def fail_during_root_views(path: Path, content: bytes) -> None:
            if path == fail_target:
                raise OSError("injected root-view publication failure")
            real_atomic(path, content)

        with mock.patch(
            "devforgeai.research.core._atomic",
            side_effect=fail_during_root_views,
        ):
            with self.assertRaisesRegex(OSError, "root-view publication failure"):
                self.store.seal_run(ref.slug, ref.run_id)

        registry = self.store._registry(ref.slug)
        self.assertFalse(
            registry.exists(),
            "a COMPLETE registry entry became visible before all root views",
        )
        self.assertTrue((root / "README.md").is_file())
        self.assertFalse(fail_target.exists())

        final_path = self.store.seal_run(ref.slug, ref.run_id)
        self.assertTrue(final_path.is_dir())
        self.assertEqual(len(self.store._registry_entries(ref.slug)), 1)
        self.assertTrue(report_ok(self.store.verify_run(ref.slug, ref.run_id)))

    def test_seal_retry_after_registry_append_does_not_duplicate_completion(self) -> None:
        _, ref = self.build_to_p8()
        self.store.transition(ref.slug, ref.run_id, "P9")
        expected_views = self.store.render(ref.slug, ref.run_id)
        root = self.workspace / "docs" / "research" / ref.slug
        real_append_registry = self.store._append_registry
        checkpoint: dict[str, bool] = {}

        def append_then_interrupt(
            slug: str,
            run_id: str,
            path: Path,
            manifest_digest: str,
        ) -> None:
            checkpoint["views_ready"] = all(
                (root / name).read_bytes() == expected_views[name].encode("utf-8")
                for name in ("README.md", "synthesis.md", "handoff.md")
            )
            real_append_registry(slug, run_id, path, manifest_digest)
            raise OSError("injected failure after registry append")

        with mock.patch.object(
            self.store,
            "_append_registry",
            side_effect=append_then_interrupt,
        ):
            with self.assertRaisesRegex(OSError, "after registry append"):
                self.store.seal_run(ref.slug, ref.run_id)

        self.assertTrue(checkpoint.get("views_ready", False))
        entries = self.store._registry_entries(ref.slug)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["outcome"], "COMPLETE")

        final_path = self.store.seal_run(ref.slug, ref.run_id)
        self.assertTrue(final_path.is_dir())
        entries = self.store._registry_entries(ref.slug)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["run_id"], ref.run_id)
        self.assertTrue(report_ok(self.store.verify_run(ref.slug, ref.run_id)))

    def test_core_validation_record_semantic_tampering_blocks_publication(self) -> None:
        def forged_platform(validation: dict) -> None:
            validation["environment"]["platform"] = "forged-platform"

        def forged_reason(validation: dict) -> None:
            validation["checks"][0]["reason"] = "A forged reason that Core did not emit."

        def forged_applicability(validation: dict) -> None:
            validation["checks"][0]["applicable"] = False
            validation["checks"][0]["status"] = "NOT_APPLICABLE"

        def forged_evidence(validation: dict) -> None:
            validation["checks"][0]["evidence"].append(
                {
                    "artifact_id": "nonexistent-evidence",
                    "path": "nonexistent/evidence.json",
                    "sha256": "f" * 64,
                }
            )

        mutations = {
            "platform": forged_platform,
            "reason": forged_reason,
            "status-applicability": forged_applicability,
            "evidence-reference": forged_evidence,
        }
        for index, (label, mutate) in enumerate(mutations.items()):
            with self.subTest(mutation=label):
                _, ref = self.build_to_p8(id_offset=index * 100)
                self.store.transition(
                    ref.slug, ref.run_id, "P9", reason="preseal gates passed"
                )
                validation_path = ref.path / "validation.json"
                validation = json.loads(validation_path.read_text(encoding="utf-8"))
                stable_timestamp = validation["validated_at_utc"]
                mutate(validation)
                validation_path.write_bytes(canonical_json(validation) + b"\n")

                report = self.store.validate_run(ref.slug, ref.run_id)

                self.assertFalse(report_ok(report), report_text(report))
                self.assertIn("E_VALIDATION_RECORD_MISMATCH", report_text(report))
                self.assertEqual(validation["validated_at_utc"], stable_timestamp)
                with self.assertRaisesRegex(
                    Exception, "E_SEAL_VALIDATION.*E_VALIDATION_RECORD_MISMATCH"
                ):
                    self.store.seal_run(ref.slug, ref.run_id)
                published = (
                    self.workspace
                    / "docs"
                    / "research"
                    / ref.slug
                    / "runs"
                    / ref.run_id
                )
                self.assertFalse(published.exists())
                registry = (
                    self.workspace
                    / "docs"
                    / "research"
                    / ref.slug
                    / "registry.jsonl"
                )
                if registry.exists():
                    self.assertNotIn(ref.run_id, registry.read_text(encoding="utf-8"))

    def test_seal_rejects_preexisting_destination_collision(self) -> None:
        _, ref = self.build_to_p8()
        self.assertTrue(report_ok(self.store.validate_run(ref.slug, ref.run_id)))
        self.store.transition(ref.slug, ref.run_id, "P9")
        destination = (
            self.workspace / "docs" / "research" / ref.slug / "runs" / ref.run_id
        )
        destination.mkdir(parents=True)
        sentinel = destination / "unrelated.txt"
        sentinel.write_text("do not overwrite", encoding="utf-8")
        with self.assertRaises(Exception):
            self.store.seal_run(ref.slug, ref.run_id)
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "do not overwrite")

    def test_second_sealed_run_extends_registry_hash_chain(self) -> None:
        _, first = self.build_to_p8()
        self.assertTrue(report_ok(self.store.validate_run(first.slug, first.run_id)))
        self.store.transition(first.slug, first.run_id, "P9")
        self.store.seal_run(first.slug, first.run_id)

        _, second = self.build_to_p8(id_offset=100)
        self.assertTrue(report_ok(self.store.validate_run(second.slug, second.run_id)))
        self.store.transition(second.slug, second.run_id, "P9")
        self.store.seal_run(second.slug, second.run_id)

        registry = (
            self.workspace / "docs" / "research" / first.slug / "registry.jsonl"
        )
        entries = [json.loads(line) for line in registry.read_text().splitlines()]
        self.assertEqual([entry["sequence"] for entry in entries], [1, 2])
        self.assertIsNone(entries[0]["previous_entry_sha256"])
        self.assertEqual(
            entries[1]["previous_entry_sha256"], entries[0]["entry_sha256"]
        )
        for entry in entries:
            unhashed = dict(entry)
            recorded = unhashed.pop("entry_sha256")
            self.assertEqual(recorded, fx.canonical_sha256(unhashed))
        first_events = {
            json.loads(line)["event_id"]
            for line in (
                self.workspace
                / "docs"
                / "research"
                / first.slug
                / "runs"
                / first.run_id
                / "state.jsonl"
            ).read_text().splitlines()
        }
        second_events = {
            json.loads(line)["event_id"]
            for line in (
                self.workspace
                / "docs"
                / "research"
                / second.slug
                / "runs"
                / second.run_id
                / "state.jsonl"
            ).read_text().splitlines()
        }
        self.assertTrue(first_events.isdisjoint(second_events))
        root = self.workspace / "docs" / "research" / first.slug
        before = {
            name: (root / name).read_bytes()
            for name in ("README.md", "synthesis.md", "handoff.md")
        }
        self.assertEqual(
            self.store.seal_run(first.slug, first.run_id),
            root / "runs" / first.run_id,
        )
        after = {name: (root / name).read_bytes() for name in before}
        self.assertEqual(after, before)
        with self.assertRaisesRegex(Exception, "E_SEAL_RECEIPT_NOT_CURRENT"):
            self.store.seal_result(first.slug, first.run_id)
        self.assertTrue(report_ok(self.store.verify_run(first.slug, first.run_id)))
        self.assertTrue(report_ok(self.store.verify_run(second.slug, second.run_id)))

    def test_manifest_detects_post_seal_source_index_tamper(self) -> None:
        _, ref = self.build_to_p8()
        self.assertTrue(report_ok(self.store.validate_run(ref.slug, ref.run_id)))
        self.store.transition(ref.slug, ref.run_id, "P9")
        final_path = self.store.seal_run(ref.slug, ref.run_id)
        sources = final_path / "sources.jsonl"
        sources.write_bytes(sources.read_bytes() + b"\n")
        report = self.store.verify_run(ref.slug, ref.run_id)
        self.assertFalse(report_ok(report), report_text(report))
        self.assertIn("manifest", report_text(report).lower())

    def test_render_and_resume_are_mandatory_deterministic_and_nonpublishing(self) -> None:
        _, ref = self.build_to_p8()
        self.assertTrue(report_ok(self.store.validate_run(ref.slug, ref.run_id)))
        canonical = self.workspace / "docs" / "research" / ref.slug / "runs" / ref.run_id
        self.assertFalse(canonical.exists())
        first_handoff = self.store.render_handoff(ref.slug, ref.run_id)
        second_handoff = self.store.render_handoff(ref.slug, ref.run_id)
        self.assertEqual(first_handoff, second_handoff)
        first_render = self.store.render(ref.slug, ref.run_id)
        second_render = self.store.render(ref.slug, ref.run_id)
        self.assertEqual(first_render, second_render)
        self.assertFalse(canonical.exists())
        resumed = ResearchStore(
            self.workspace, allow_offline_test_harness=True
        ).resume_run(ref.slug, ref.run_id)
        self.assertEqual((resumed.slug, resumed.run_id), (ref.slug, ref.run_id))

    def test_cli_help_exposes_only_canonical_public_operations(self) -> None:
        result = subprocess.run(
            [sys.executable, "-B", "-m", "devforgeai.research", "--help"],
            check=True,
            capture_output=True,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            text=True,
        )
        for operation in (
            "normalize-request",
            "open-run",
            "append-record",
            "put-source",
            "transition-run",
            "validate-run",
            "seal-run",
            "render",
            "render-handoff",
            "resume-run",
        ):
            self.assertIn(operation, result.stdout)
        self.assertNotIn("verify-run", result.stdout)

    def test_cli_seal_run_rejects_offline_harness_run(self) -> None:
        _, ref = self.build_to_p8()
        self.store.transition(ref.slug, ref.run_id, "P9")
        result = subprocess.run(
            [
                sys.executable,
                "-B",
                "-m",
                "devforgeai.research",
                "--workspace",
                str(self.workspace),
                "seal-run",
                ref.slug,
                ref.run_id,
            ],
            check=False,
            capture_output=True,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            text=True,
        )
        self.assertEqual(result.returncode, 1)
        error = json.loads(result.stderr)
        self.assertEqual(error["error"], "IntegrityError")
        self.assertIn("E_OFFLINE_TEST_HARNESS_DISABLED", error["message"])
        self.assertFalse(
            (
                self.workspace
                / "docs"
                / "research"
                / ref.slug
                / "runs"
                / ref.run_id
            ).exists()
        )


if __name__ == "__main__":
    unittest.main()
