from __future__ import annotations

import copy
import re
import unittest

from devforgeai.research.rendering import render_handoff_markdown

from tests.research import _fixtures as fx


class ResearchHandoffRenderingTests(unittest.TestCase):
    def fixture(self) -> dict:
        return fx.handoff("a" * 64, outcome="READY_TO_SEAL")

    def test_render_is_deterministic_and_covers_every_semantic_section(self) -> None:
        handoff = self.fixture()

        first = render_handoff_markdown(handoff)
        second = render_handoff_markdown(copy.deepcopy(handoff))

        self.assertEqual(first, second)
        self.assertTrue(first.startswith("# Research handoff\n\n> **YOU ARE HERE**"))
        for heading in (
            "Location and result",
            "Record identity and provenance",
            "Questions",
            "Claims",
            "Sources",
            "Contrary evidence",
            "Exclusions",
            "Budget",
            "Canonical artifacts",
            "Source basis",
            "Validation",
            "Decisions",
            "Custody",
            "Conclusion",
            "Open items",
            "Next action",
            "Session guidance",
            "Authority and fence",
            "Repair route",
        ):
            self.assertIn(f"## {heading}\n", first)

        for value in (
            "READY_TO_SEAL",
            "RQ-000001",
            "CLM-000001",
            "SRC-000001",
            "EVD-000001",
            "CTR-000001",
            "SYN-000001",
            "person:requester",
            "Read this run; create a new run to refresh it.",
            "no short refresh invocation is executable",
        ):
            self.assertIn(value, first)

        self.assertEqual(re.findall(r"(?m)^1\. ", first), ["1. "])
        self.assertIn("**Provider:** neutral", first)
        self.assertIn("~~~text\nreturn-to-caller\n~~~", first)

    def test_table_values_escape_pipes_backslashes_newlines_and_html(self) -> None:
        handoff = self.fixture()
        handoff["location"]["project_id"] = "project:a|b\nc\\d<unsafe>"
        handoff["exclusions"] = ["one|two\nthree\\four<script>"]

        rendered = render_handoff_markdown(handoff)

        self.assertIn("project:a\\|b<br>c\\\\d&lt;unsafe&gt;", rendered)
        self.assertIn("one\\|two<br>three\\\\four&lt;script&gt;", rendered)
        self.assertNotIn("project:a|b\nc", rendered)
        self.assertNotIn("<script>", rendered)

    def test_exact_multiline_invocation_uses_a_noncolliding_fence(self) -> None:
        handoff = self.fixture()
        invocation = "codex run --arg 'a|b'\\path\n~~~\n--literal `value`"
        handoff["next_action"] = {"provider": "codex", "invocation": invocation}

        rendered = render_handoff_markdown(handoff)

        self.assertIn(invocation, rendered)
        self.assertIn("~~~~text\n" + invocation + "\n~~~~", rendered)
        self.assertEqual(re.findall(r"(?m)^1\. ", rendered), ["1. "])
        self.assertIn("**Provider:** codex", rendered)

    def test_input_is_not_mutated(self) -> None:
        handoff = self.fixture()
        before = copy.deepcopy(handoff)

        render_handoff_markdown(handoff)

        self.assertEqual(handoff, before)

    def test_post_seal_fields_fail_closed(self) -> None:
        for field in ("readback", "registry_head_sha256", "manifest_sha256"):
            with self.subTest(field=field):
                handoff = self.fixture()
                handoff[field] = "must-not-render"
                with self.assertRaisesRegex(ValueError, "post-seal fields"):
                    render_handoff_markdown(handoff)

    def test_non_mapping_input_is_rejected(self) -> None:
        with self.assertRaisesRegex(TypeError, "handoff must be a mapping"):
            render_handoff_markdown([])  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
