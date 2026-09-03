from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from devforgeai.research.core import ResearchStore, canonical_json

from tests.research import _fixtures as fx


class VerificationPacketContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temporary.name)
        (self.workspace / "inputs").mkdir()
        self.store = ResearchStore(
            self.workspace, allow_offline_test_harness=True
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _build_claim_at_p7(
        self,
        *,
        evidence_count: int = 1,
        evidence_length: int = 80,
        additional_claim_statuses: tuple[str, ...] = (),
    ) -> tuple[object, dict, dict]:
        request = fx.load_request()
        normalized, digest = self.store.normalize_request(request)
        ref = self.store.open_run(normalized, digest)
        fx.install_preflight_contract(
            self.store, self.workspace, normalized, digest, ref
        )
        self.store.transition(ref.slug, ref.run_id, "P1")
        self.store.transition(ref.slug, ref.run_id, "P2")
        question = fx.question()
        question["run_id"] = ref.run_id
        self.store.append_record(ref.slug, ref.run_id, "question", question)
        fx.install_context_contract(
            self.store, self.workspace, normalized, digest, ref
        )
        self.store.transition(ref.slug, ref.run_id, "P3")
        fx.install_plan_contract(
            self.store, self.workspace, normalized, digest, ref
        )
        self.store.transition(ref.slug, ref.run_id, "P4")
        query = fx.query()
        query["run_id"] = ref.run_id
        self.store.append_record(ref.slug, ref.run_id, "query", query)
        challenge = fx.challenge_query()
        challenge["run_id"] = ref.run_id
        challenge["results"][0].update(
            {
                "disposition": "REJECTED",
                "reason": "The bounded contrary candidate is outside this packet fixture.",
            }
        )
        self.store.append_record(ref.slug, ref.run_id, "query", challenge)
        self.store.transition(ref.slug, ref.run_id, "P5")

        source_path = self.workspace / "inputs" / "source-primary.txt"
        source_path.write_bytes(
            (fx.FIXTURES / "source-primary.txt").read_bytes()
        )
        metadata = fx.source_metadata(
            "SRC-000001",
            "source-primary.txt",
            publisher="Synthetic Standards Body",
        )
        metadata["run_id"] = ref.run_id
        metadata["custody"] = {"mode": "TRACKED_CAS"}
        source = self.store.put_source(
            ref.slug, ref.run_id, "SRC-000001", source_path, metadata
        )
        source_digest = source["custody"]["sha256"]
        evidence_ids: list[str] = []
        for number in range(1, evidence_count + 1):
            evidence_id = f"EVD-{number:06d}"
            evidence_ids.append(evidence_id)
            text = (f"Synthetic evidence {number:06d} " + "x" * evidence_length)[
                :12000
            ]
            evidence = fx.evidence(
                evidence_id, "SRC-000001", source_digest, text
            )
            evidence["run_id"] = ref.run_id
            self.store.append_record(ref.slug, ref.run_id, "evidence", evidence)

        self.store.transition(ref.slug, ref.run_id, "P6")
        claim = fx.claim(support=evidence_ids)
        claim["run_id"] = ref.run_id
        claim["evidence_refs"] = list(evidence_ids)
        self.store.append_record(ref.slug, ref.run_id, "claim", claim)
        for number, status in enumerate(additional_claim_statuses, 2):
            additional = copy.deepcopy(claim)
            additional["record_id"] = f"CLM-{number:06d}"
            additional["claim_id"] = f"CLM-{number:06d}"
            additional["text"] = f"Independent synthetic claim number {number}."
            additional["status"] = status
            if status == "REJECTED":
                additional["lifecycle_status"] = "REJECTED"
                additional["readiness_status"] = "NOT_READY"
            self.store.append_record(ref.slug, ref.run_id, "claim", additional)
        fx.install_reconciliation_contract(
            self.store,
            self.workspace,
            normalized,
            ref,
            query_ids=["QRY-000001", "QRY-000002"],
            source_count=1,
        )
        self.store.transition(ref.slug, ref.run_id, "P7")
        return ref, claim, source

    def _packet_path(self, ref: object, packet_ref: dict) -> Path:
        return (
            self.workspace
            / ".devforgeai"
            / "research-staging"
            / ref.slug
            / ref.run_id
            / packet_ref["path"]
        )

    def _verification(self, ref: object, claim: dict, **kwargs: object) -> dict:
        return fx.verification(
            claim,
            provider_conformance_path=ref.path / "provider-conformance.json",
            **kwargs,
        )

    def test_core_builds_single_claim_packet_and_accepts_offline_harness_pass(self) -> None:
        ref, claim, _ = self._build_claim_at_p7()
        packet_files = sorted((ref.path / "verification-packets").glob("*.json"))
        self.assertEqual([item.name for item in packet_files], ["VPK-000001.json"])
        receipt = self.store.build_verification_packet(
            ref.slug, ref.run_id, claim["claim_id"]
        )
        repeated = self.store.build_verification_packet(
            ref.slug, ref.run_id, claim["claim_id"]
        )
        self.assertEqual(receipt, repeated)
        self.assertEqual(
            [item.name for item in (ref.path / "verification-packets").glob("*.json")],
            ["VPK-000001.json"],
        )
        packet = receipt["packet"]
        packet_ref = receipt["packet_ref"]
        self.assertEqual(
            set(packet["claim"]),
            {"claim_id", "record_version", "claim_sha256", "text", "claim_type", "scope"},
        )
        self.assertEqual(packet["request_binding"]["request"], fx.load_request())
        self.assertEqual(len(canonical_json(packet)), packet_ref["byte_length"])
        self.assertLessEqual(packet_ref["byte_length"], 65536)
        self.assertEqual(
            self._packet_path(ref, packet_ref).read_bytes(),
            canonical_json(packet) + b"\n",
        )

        verification = self._verification(ref, claim, packet_ref=packet_ref)
        verification["run_id"] = ref.run_id
        attestation_bytes = (ref.path / "provider-conformance.json").read_bytes()
        self.assertEqual(
            verification["provider_conformance"]["attestation_sha256"],
            hashlib.sha256(attestation_bytes).hexdigest(),
        )
        self.store.append_record(
            ref.slug, ref.run_id, "verification", verification
        )
        records = json.loads(
            (
                self.workspace
                / ".devforgeai"
                / "research-staging"
                / ref.slug
                / ref.run_id
                / "verifications.jsonl"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(records["outcome"], "PASS")
        self.assertEqual(records["verifier"]["kind"], "OFFLINE_TEST_HARNESS")
        self.assertIn("does not establish Claude Code or Codex", records["limitations"][0])

    def test_p6_to_p7_builds_one_packet_for_each_candidate_and_skips_rejected(self) -> None:
        ref, _, _ = self._build_claim_at_p7(
            additional_claim_statuses=("CANDIDATE", "REJECTED")
        )
        packets = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in sorted((ref.path / "verification-packets").glob("*.json"))
        ]
        self.assertEqual(
            [packet["claim"]["claim_id"] for packet in packets],
            ["CLM-000001", "CLM-000002"],
        )

    def test_validation_rejects_duplicate_packets_for_one_candidate(self) -> None:
        ref, claim, _ = self._build_claim_at_p7()
        receipt = self.store.build_verification_packet(
            ref.slug, ref.run_id, claim["claim_id"]
        )
        duplicate = copy.deepcopy(receipt["packet"])
        duplicate["packet_id"] = "VPK-000002"
        (ref.path / "verification-packets" / "VPK-000002.json").write_bytes(
            canonical_json(duplicate) + b"\n"
        )

        report = self.store.validate_run(ref.slug, ref.run_id)

        self.assertFalse(report.valid)
        self.assertIn(
            "E_VERIFICATION_PACKET_CLAIM_DUPLICATE:CLM-000001",
            " ".join(report.errors),
        )

    def test_validation_rejects_missing_candidate_packet(self) -> None:
        ref, _, _ = self._build_claim_at_p7()
        (ref.path / "verification-packets" / "VPK-000001.json").unlink()

        report = self.store.validate_run(ref.slug, ref.run_id)

        self.assertFalse(report.valid)
        self.assertIn(
            "E_VERIFICATION_PACKET_CLAIM_MISSING:CLM-000001",
            " ".join(report.errors),
        )

    def test_validation_rejects_packet_for_non_candidate_claim(self) -> None:
        ref, claim, _ = self._build_claim_at_p7()
        changed = copy.deepcopy(claim)
        changed["status"] = "REJECTED"
        changed["lifecycle_status"] = "REJECTED"
        changed["readiness_status"] = "NOT_READY"
        (ref.path / "claims.jsonl").write_bytes(canonical_json(changed) + b"\n")

        report = self.store.validate_run(ref.slug, ref.run_id)

        self.assertFalse(report.valid)
        self.assertIn(
            "E_VERIFICATION_PACKET_CLAIM_NONCANDIDATE:CLM-000001",
            " ".join(report.errors),
        )

    def test_provider_agent_pass_fails_without_trusted_broker_and_conformance(self) -> None:
        ref, claim, _ = self._build_claim_at_p7()
        receipt = self.store.build_verification_packet(
            ref.slug, ref.run_id, claim["claim_id"]
        )
        verification = self._verification(
            ref, claim, packet_ref=receipt["packet_ref"]
        )
        verification["run_id"] = ref.run_id
        verification["verifier"].update(
            {
                "kind": "PROVIDER_AGENT",
                "provider": "CLAUDE_CODE",
                "model": "unproven-provider-model",
                "provider_version": "not-conformance-tested",
            }
        )
        with self.assertRaisesRegex(
            Exception, "E_PROVIDER_VERIFICATION_UNAVAILABLE"
        ):
            self.store.append_record(
                ref.slug, ref.run_id, "verification", verification
            )

    def test_packet_cap_is_16_evidence_records(self) -> None:
        with self.assertRaisesRegex(
            Exception, "E_VERIFICATION_PACKET_EVIDENCE_CAP"
        ):
            self._build_claim_at_p7(evidence_count=17)

    def test_packet_cap_is_65536_canonical_bytes_excluding_file_lf(self) -> None:
        with self.assertRaisesRegex(Exception, "E_VERIFICATION_PACKET_SIZE"):
            self._build_claim_at_p7(
                evidence_count=6, evidence_length=11900
            )

    def test_claim_change_invalidates_existing_packet_as_stale_revision(self) -> None:
        ref, claim, _ = self._build_claim_at_p7()
        self.store.build_verification_packet(
            ref.slug, ref.run_id, claim["claim_id"]
        )
        claims_path = (
            self.workspace
            / ".devforgeai"
            / "research-staging"
            / ref.slug
            / ref.run_id
            / "claims.jsonl"
        )
        changed = copy.deepcopy(claim)
        changed["text"] = "A changed claim revision cannot reuse the prior packet."
        claims_path.write_bytes(canonical_json(changed) + b"\n")
        report = self.store.validate_run(ref.slug, ref.run_id)
        self.assertFalse(report.valid)
        self.assertIn("E_VERIFICATION_PACKET_STALE", " ".join(report.errors))

    def test_packet_rejects_bias_fields_even_when_canonical_json(self) -> None:
        ref, claim, _ = self._build_claim_at_p7()
        receipt = self.store.build_verification_packet(
            ref.slug, ref.run_id, claim["claim_id"]
        )
        path = self._packet_path(ref, receipt["packet_ref"])
        packet = copy.deepcopy(receipt["packet"])
        packet["claim"]["author"] = claim["author"]
        path.write_bytes(canonical_json(packet) + b"\n")
        report = self.store.validate_run(ref.slug, ref.run_id)
        self.assertFalse(report.valid)
        self.assertIn("E_SCHEMA_VERIFICATION-PACKET", " ".join(report.errors))

    def test_verification_binds_exact_packet_hash_size_and_reference_sets(self) -> None:
        for mutation, expected in (
            ("digest", "E_VERIFICATION_PACKET_CUSTODY"),
            ("size", "E_VERIFICATION_PACKET_CUSTODY"),
            ("references", "E_VERIFICATION_REFERENCE_SETS"),
        ):
            with self.subTest(mutation=mutation):
                ref, claim, _ = self._build_claim_at_p7()
                receipt = self.store.build_verification_packet(
                    ref.slug, ref.run_id, claim["claim_id"]
                )
                verification = self._verification(
                    ref, claim, packet_ref=receipt["packet_ref"]
                )
                verification["run_id"] = ref.run_id
                if mutation == "digest":
                    verification["packet_ref"]["sha256"] = "f" * 64
                elif mutation == "size":
                    verification["packet_ref"]["byte_length"] += 1
                else:
                    verification["reference_sets"]["evidence_ids"] = [
                        "EVD-000001",
                        "EVD-999999"
                    ]
                with self.assertRaisesRegex(Exception, expected):
                    self.store.append_record(
                        ref.slug, ref.run_id, "verification", verification
                    )
                self.tearDown()
                self.setUp()

    def test_outcome_precedence_and_all_eight_checks_are_enforced(self) -> None:
        ref, claim, _ = self._build_claim_at_p7()
        receipt = self.store.build_verification_packet(
            ref.slug, ref.run_id, claim["claim_id"]
        )
        verification = self._verification(
            ref, claim, packet_ref=receipt["packet_ref"]
        )
        verification["run_id"] = ref.run_id
        verification["checks"]["entailment"]["status"] = "COULD_NOT_RUN"
        verification["checks"]["scope_match"]["status"] = "INFRA_FAILURE"
        verification["checks"]["contradictions_considered"]["status"] = "FAIL"
        verification["outcome"] = "PASS"
        with self.assertRaisesRegex(Exception, "E_VERIFICATION_OUTCOME:expected=FAIL"):
            self.store.append_record(
                ref.slug, ref.run_id, "verification", verification
            )

    def test_fresh_child_session_and_offline_custody_digests_are_enforced(self) -> None:
        for mutation, expected in (
            ("same-session", "E_VERIFICATION_INDEPENDENCE"),
            ("conformance", "E_OFFLINE_VERIFICATION_CONFORMANCE"),
            ("launch", "E_OFFLINE_VERIFICATION_LAUNCH_RECEIPT"),
            ("result", "E_OFFLINE_VERIFICATION_RESULT_CUSTODY"),
        ):
            with self.subTest(mutation=mutation):
                ref, claim, _ = self._build_claim_at_p7()
                receipt = self.store.build_verification_packet(
                    ref.slug, ref.run_id, claim["claim_id"]
                )
                verification = self._verification(
                    ref, claim, packet_ref=receipt["packet_ref"]
                )
                verification["run_id"] = ref.run_id
                if mutation == "same-session":
                    verification["session_binding"]["parent_session_id"] = (
                        verification["session_binding"]["child_session_id"]
                    )
                elif mutation == "conformance":
                    verification["provider_conformance"]["attestation_sha256"] = "f" * 64
                elif mutation == "launch":
                    verification["broker_launch_receipt_sha256"] = "f" * 64
                else:
                    verification["raw_result_sha256"] = "f" * 64
                with self.assertRaisesRegex(Exception, expected):
                    self.store.append_record(
                        ref.slug, ref.run_id, "verification", verification
                    )
                self.tearDown()
                self.setUp()


if __name__ == "__main__":
    unittest.main()
