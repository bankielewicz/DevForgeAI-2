from __future__ import annotations

import errno
import hashlib
import json
import os
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

from devforgeai.research import cas as cas_ops
from devforgeai.research import core as core_module
from devforgeai.research.store import ResearchStore

from tests.research import _fixtures as fx


class CASQuarantineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temporary.name)
        (self.workspace / "inputs").mkdir()
        self.store = ResearchStore(
            self.workspace, allow_offline_test_harness=True
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def prepare_p5(self, slug: str = "offline-fixture"):
        request = fx.load_request(slug=slug)
        normalized, digest = self.store.normalize_request(request)
        ref = self.store.open_run(normalized, digest)
        fx.install_preflight_contract(
            self.store, self.workspace, normalized, digest, ref
        )
        self.store.transition(slug, ref.run_id, "P1", reason="quarantine test")
        self.store.transition(slug, ref.run_id, "P2", reason="quarantine test")
        question = fx.question()
        question["run_id"] = ref.run_id
        self.store.append_record(slug, ref.run_id, "question", question)
        fx.install_context_contract(
            self.store, self.workspace, normalized, digest, ref
        )
        self.store.transition(slug, ref.run_id, "P3", reason="quarantine test")
        fx.install_plan_contract(
            self.store, self.workspace, normalized, digest, ref
        )
        self.store.transition(slug, ref.run_id, "P4", reason="quarantine test")
        query = fx.query()
        query["run_id"] = ref.run_id
        self.store.append_record(slug, ref.run_id, "query", query)
        self.store.transition(slug, ref.run_id, "P5", reason="quarantine test")
        return ref

    def source_path(self, name: str = "source-primary.txt") -> Path:
        destination = self.workspace / "inputs" / name
        destination.write_bytes((fx.FIXTURES / name).read_bytes())
        return destination

    def metadata(self, ref, source_id: str, cas_class: str) -> dict:
        result = fx.source_metadata(
            source_id, "source-primary.txt", publisher=f"Synthetic {source_id}"
        )
        result["run_id"] = ref.run_id
        result["query_ids"] = []
        result["candidate_ids"] = []
        result["custody"] = {"mode": cas_class}
        if cas_class == "LOCAL_ONLY_CAS":
            result["retention_policy"].update(
                {
                    "redistribution_basis": "NONE",
                    "redistribution_reference": None,
                    "data_classification": "INTERNAL",
                }
            )
            result["retention_policy"]["sensitive_scan"].update(
                {"status": "NOT_RUN", "findings_count": 0}
            )
        return result

    def root(self, cas_class: str) -> Path:
        return (
            self.store.tracked_cas_root
            if cas_class == "TRACKED_CAS"
            else self.store.local_cas_root
        )

    def object_path(self, cas_class: str) -> tuple[str, Path]:
        digest = hashlib.sha256(
            (fx.FIXTURES / "source-primary.txt").read_bytes()
        ).hexdigest()
        return digest, self.root(cas_class) / digest[:2] / digest

    def sources_bytes(self, ref) -> bytes:
        path = (
            self.workspace
            / ".devforgeai"
            / "research-staging"
            / ref.slug
            / ref.run_id
            / "sources.jsonl"
        )
        return path.read_bytes()

    def put(self, ref, source_id: str, cas_class: str) -> dict:
        return self.store.put_source(
            ref.slug,
            ref.run_id,
            source_id,
            self.source_path(),
            self.metadata(ref, source_id, cas_class),
        )

    def seed_corrupt_regular(self, cas_class: str) -> tuple[str, Path]:
        digest, target = self.object_path(cas_class)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"bytes that do not match the claimed digest\n")
        return digest, target

    def receipt_dir(self, cas_class: str, digest: str) -> Path:
        return self.root(cas_class).parent / "quarantine" / "sha256" / digest

    def test_correct_object_reuse_never_uses_rename_noreplace(self) -> None:
        for cas_class in ("TRACKED_CAS", "LOCAL_ONLY_CAS"):
            with self.subTest(cas_class=cas_class):
                workspace = Path(tempfile.mkdtemp(dir=self.workspace))
                (workspace / "inputs").mkdir()
                store = ResearchStore(workspace, allow_offline_test_harness=True)
                old_store, old_workspace = self.store, self.workspace
                self.store, self.workspace = store, workspace
                try:
                    ref = self.prepare_p5()
                    first = self.put(ref, "SRC-000001", cas_class)
                    with mock.patch.object(
                        cas_ops,
                        "rename_noreplace",
                        side_effect=AssertionError("reuse must not rename"),
                    ):
                        second = self.put(ref, "SRC-000002", cas_class)
                    self.assertEqual(first["custody"]["sha256"], second["custody"]["sha256"])
                finally:
                    self.store, self.workspace = old_store, old_workspace

    def test_corrupt_regular_is_quarantined_in_both_cas_classes(self) -> None:
        for cas_class in ("TRACKED_CAS", "LOCAL_ONLY_CAS"):
            with self.subTest(cas_class=cas_class):
                workspace = Path(tempfile.mkdtemp(dir=self.workspace))
                (workspace / "inputs").mkdir()
                store = ResearchStore(workspace, allow_offline_test_harness=True)
                old_store, old_workspace = self.store, self.workspace
                self.store, self.workspace = store, workspace
                try:
                    ref = self.prepare_p5()
                    digest, target = self.seed_corrupt_regular(cas_class)
                    corrupt = target.read_bytes()
                    with self.assertRaisesRegex(Exception, "E_CAS_INTEGRITY: QAR-000001"):
                        self.put(ref, "SRC-000001", cas_class)
                    self.assertFalse(target.exists())
                    qdir = self.receipt_dir(cas_class, digest)
                    self.assertEqual((qdir / "QAR-000001.object").read_bytes(), corrupt)
                    receipt_raw = (qdir / "QAR-000001.json").read_bytes()
                    receipt = json.loads(receipt_raw)
                    self.assertEqual(
                        set(receipt),
                        {
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
                        },
                    )
                    self.assertEqual(receipt["cas_class"], cas_class)
                    self.assertEqual(receipt["entry_type"], "REGULAR_FILE")
                    self.assertEqual(receipt["claimed_sha256"], digest)
                    self.assertEqual(receipt["actual_sha256"], hashlib.sha256(corrupt).hexdigest())
                    self.assertEqual(receipt["actual_byte_length"], len(corrupt))
                    self.assertFalse((qdir / "QAR-000001.pending").exists())
                    self.assertEqual(self.sources_bytes(ref), b"")
                finally:
                    self.store, self.workspace = old_store, old_workspace

    def test_symlink_and_fifo_are_moved_without_following(self) -> None:
        for entry_type in ("SYMLINK", "FIFO"):
            with self.subTest(entry_type=entry_type):
                workspace = Path(tempfile.mkdtemp(dir=self.workspace))
                (workspace / "inputs").mkdir()
                store = ResearchStore(workspace, allow_offline_test_harness=True)
                old_store, old_workspace = self.store, self.workspace
                self.store, self.workspace = store, workspace
                try:
                    ref = self.prepare_p5()
                    digest, target = self.object_path("LOCAL_ONLY_CAS")
                    target.parent.mkdir(parents=True, exist_ok=True)
                    protected = workspace / "protected.txt"
                    protected.write_bytes(b"must not be opened through a link")
                    if entry_type == "SYMLINK":
                        target.symlink_to(protected)
                    else:
                        os.mkfifo(target)
                    with self.assertRaisesRegex(Exception, "E_CAS_INTEGRITY"):
                        self.put(ref, "SRC-000001", "LOCAL_ONLY_CAS")
                    receipt = json.loads(
                        (self.receipt_dir("LOCAL_ONLY_CAS", digest) / "QAR-000001.json").read_text()
                    )
                    self.assertEqual(receipt["entry_type"], entry_type)
                    self.assertIsNone(receipt["actual_sha256"])
                    self.assertIsNone(receipt["actual_byte_length"])
                    self.assertEqual(protected.read_bytes(), b"must not be opened through a link")
                    self.assertEqual(self.sources_bytes(ref), b"")
                finally:
                    self.store, self.workspace = old_store, old_workspace

    def test_cas_lock_is_global_nonblocking_across_two_slugs(self) -> None:
        first = self.prepare_p5("first-dossier")
        second = self.prepare_p5("second-dossier")
        entered = threading.Event()
        release = threading.Event()
        original = cas_ops.rename_noreplace
        result: list[object] = []

        def delayed(source: Path, target: Path) -> None:
            if source.name.startswith(".incoming-"):
                entered.set()
                if not release.wait(5):
                    raise TimeoutError("test release was not signaled")
            original(source, target)

        def first_writer() -> None:
            try:
                result.append(self.put(first, "SRC-000001", "TRACKED_CAS"))
            except BaseException as exc:  # pragma: no cover - asserted below
                result.append(exc)

        with mock.patch.object(cas_ops, "rename_noreplace", side_effect=delayed):
            worker = threading.Thread(target=first_writer)
            worker.start()
            self.assertTrue(entered.wait(5))
            started = time.monotonic()
            with self.assertRaisesRegex(Exception, "E_CAS_WRITER_COLLISION"):
                self.put(second, "SRC-000001", "LOCAL_ONLY_CAS")
            self.assertLess(time.monotonic() - started, 2.0)
            release.set()
            worker.join(5)
        self.assertFalse(worker.is_alive())
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], dict)
        self.assertEqual(self.sources_bytes(second), b"")

    def test_quarantine_id_collision_never_overwrites(self) -> None:
        ref = self.prepare_p5()
        digest, target = self.seed_corrupt_regular("TRACKED_CAS")
        qdir = self.receipt_dir("TRACKED_CAS", digest)
        qdir.mkdir(parents=True)
        sentinel_object = qdir / "QAR-000001.object"
        sentinel_receipt = qdir / "QAR-000001.json"
        sentinel_object.write_bytes(b"prior quarantine")
        sentinel_receipt.write_bytes(b"prior receipt")
        with self.assertRaisesRegex(Exception, "E_CAS_INTEGRITY: QAR-000002"):
            self.put(ref, "SRC-000001", "TRACKED_CAS")
        self.assertEqual(sentinel_object.read_bytes(), b"prior quarantine")
        self.assertEqual(sentinel_receipt.read_bytes(), b"prior receipt")
        self.assertTrue((qdir / "QAR-000002.object").exists())
        self.assertTrue((qdir / "QAR-000002.json").exists())
        self.assertFalse(target.exists())

    def test_rename_unavailable_fails_closed_without_source_append(self) -> None:
        ref = self.prepare_p5()
        _, target = self.object_path("TRACKED_CAS")
        with mock.patch.object(
            cas_ops,
            "rename_noreplace",
            side_effect=OSError(errno.ENOSYS, "renameat2 unavailable"),
        ):
            with self.assertRaisesRegex(Exception, "E_CAS_INSTALL_FAILED"):
                self.put(ref, "SRC-000001", "TRACKED_CAS")
        self.assertFalse(target.exists())
        self.assertEqual(self.sources_bytes(ref), b"")

    def test_quarantine_rename_failure_preserves_original(self) -> None:
        ref = self.prepare_p5()
        digest, target = self.seed_corrupt_regular("LOCAL_ONLY_CAS")
        original = target.read_bytes()
        with mock.patch.object(
            cas_ops,
            "rename_noreplace",
            side_effect=OSError(errno.EIO, "injected rename failure"),
        ):
            with self.assertRaisesRegex(Exception, "E_CAS_QUARANTINE_FAILED"):
                self.put(ref, "SRC-000001", "LOCAL_ONLY_CAS")
        self.assertEqual(target.read_bytes(), original)
        qdir = self.receipt_dir("LOCAL_ONLY_CAS", digest)
        self.assertTrue((qdir / "QAR-000001.pending").exists())
        self.assertFalse((qdir / "QAR-000001.object").exists())
        self.assertEqual(self.sources_bytes(ref), b"")

    def test_interrupted_receipt_is_recovered_before_a_later_install(self) -> None:
        ref = self.prepare_p5()
        digest, target = self.seed_corrupt_regular("TRACKED_CAS")
        original_rename = cas_ops.rename_noreplace

        def fail_receipt_promotion(source: Path, destination: Path) -> None:
            if source.name.endswith(".pending"):
                raise OSError(errno.EIO, "injected receipt promotion failure")
            original_rename(source, destination)

        with mock.patch.object(
            cas_ops, "rename_noreplace", side_effect=fail_receipt_promotion
        ):
            with self.assertRaisesRegex(Exception, "E_CAS_QUARANTINE_FAILED"):
                self.put(ref, "SRC-000001", "TRACKED_CAS")
        qdir = self.receipt_dir("TRACKED_CAS", digest)
        self.assertFalse(target.exists())
        self.assertTrue((qdir / "QAR-000001.object").exists())
        self.assertTrue((qdir / "QAR-000001.pending").exists())
        self.assertFalse((qdir / "QAR-000001.json").exists())
        self.assertEqual(self.sources_bytes(ref), b"")

        with self.assertRaisesRegex(Exception, "E_CAS_INTEGRITY: recovered quarantine QAR-000001"):
            self.put(ref, "SRC-000001", "TRACKED_CAS")
        self.assertTrue((qdir / "QAR-000001.json").exists())
        self.assertFalse((qdir / "QAR-000001.pending").exists())
        self.assertEqual(self.sources_bytes(ref), b"")

        admitted = self.put(ref, "SRC-000001", "TRACKED_CAS")
        self.assertEqual(admitted["custody"]["sha256"], digest)
        self.assertTrue(target.is_file())

    def test_injected_quarantine_object_fsync_failure_leaves_recoverable_orphan(self) -> None:
        ref = self.prepare_p5()
        digest, target = self.seed_corrupt_regular("LOCAL_ONLY_CAS")
        original_fsync = cas_ops.fsync_regular_nofollow

        def fail_quarantine_object(path: Path) -> None:
            if "quarantine" in path.parts:
                raise OSError(errno.EIO, "injected object fsync failure")
            original_fsync(path)

        with mock.patch.object(
            cas_ops, "fsync_regular_nofollow", side_effect=fail_quarantine_object
        ):
            with self.assertRaisesRegex(Exception, "E_CAS_QUARANTINE_FAILED"):
                self.put(ref, "SRC-000001", "LOCAL_ONLY_CAS")
        qdir = self.receipt_dir("LOCAL_ONLY_CAS", digest)
        self.assertFalse(target.exists())
        self.assertTrue((qdir / "QAR-000001.object").exists())
        self.assertTrue((qdir / "QAR-000001.pending").exists())
        self.assertEqual(self.sources_bytes(ref), b"")

        with self.assertRaisesRegex(Exception, "recovered quarantine QAR-000001"):
            self.put(ref, "SRC-000001", "LOCAL_ONLY_CAS")
        self.assertTrue((qdir / "QAR-000001.json").exists())

    def test_injected_postmove_directory_fsync_failure_never_installs_incoming(self) -> None:
        ref = self.prepare_p5()
        digest, target = self.seed_corrupt_regular("TRACKED_CAS")
        original_fsync = core_module._fsync_dir

        def fail_source_shard(path: Path) -> None:
            if path == target.parent and not target.exists():
                raise OSError(errno.EIO, "injected postmove directory fsync failure")
            original_fsync(path)

        with mock.patch.object(core_module, "_fsync_dir", side_effect=fail_source_shard):
            with self.assertRaisesRegex(Exception, "E_CAS_QUARANTINE_FAILED"):
                self.put(ref, "SRC-000001", "TRACKED_CAS")
        qdir = self.receipt_dir("TRACKED_CAS", digest)
        self.assertFalse(target.exists())
        self.assertTrue((qdir / "QAR-000001.object").exists())
        self.assertTrue((qdir / "QAR-000001.pending").exists())
        self.assertEqual(list(self.root("TRACKED_CAS").glob(".incoming-*")), [])
        self.assertEqual(self.sources_bytes(ref), b"")

    def test_receipt_creation_failure_keeps_corrupt_original(self) -> None:
        ref = self.prepare_p5()
        _, target = self.seed_corrupt_regular("TRACKED_CAS")
        corrupt = target.read_bytes()
        with mock.patch.object(
            cas_ops,
            "write_exclusive",
            side_effect=OSError(errno.ENOSPC, "injected receipt failure"),
        ):
            with self.assertRaisesRegex(Exception, "E_CAS_QUARANTINE_FAILED"):
                self.put(ref, "SRC-000001", "TRACKED_CAS")
        self.assertEqual(target.read_bytes(), corrupt)
        self.assertEqual(self.sources_bytes(ref), b"")

    def test_symlinked_quarantine_root_and_digest_traversal_fail_closed(self) -> None:
        ref = self.prepare_p5()
        _, target = self.seed_corrupt_regular("LOCAL_ONLY_CAS")
        corrupt = target.read_bytes()
        escape = self.workspace / "escape"
        escape.mkdir()
        quarantine = self.root("LOCAL_ONLY_CAS").parent / "quarantine"
        quarantine.symlink_to(escape, target_is_directory=True)
        with self.assertRaisesRegex(Exception, "E_CAS_QUARANTINE_FAILED"):
            self.put(ref, "SRC-000001", "LOCAL_ONLY_CAS")
        self.assertEqual(target.read_bytes(), corrupt)
        self.assertEqual(list(escape.iterdir()), [])
        with self.assertRaisesRegex(Exception, "E_CAS_DIGEST"):
            self.store._quarantine_directory(
                self.root("LOCAL_ONLY_CAS"), "../outside"
            )
        self.assertEqual(self.sources_bytes(ref), b"")

    def test_quarantine_tree_is_excluded_from_tracked_dossier_accounting(self) -> None:
        ref = self.prepare_p5()
        quarantine = (
            self.store.tracked_cas_root.parent
            / "quarantine"
            / "sha256"
            / ("f" * 64)
        )
        quarantine.mkdir(parents=True)
        with (quarantine / "historical-noncanonical.object").open("wb") as stream:
            stream.truncate(101 * 1024 * 1024)
        admitted = self.put(ref, "SRC-000001", "TRACKED_CAS")
        self.assertEqual(admitted["custody"]["mode"], "TRACKED_CAS")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
