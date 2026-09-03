"""Static provider-adapter reachability checks.

These checks validate source shape only. They do not claim that an installed
provider discovered, invoked, or executed either adapter.
"""

from __future__ import annotations

import re
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class ResearchAdapterContractTests(unittest.TestCase):
    def test_claude_adapter_is_manual_only_until_work_orders_are_validated(self) -> None:
        skill = (
            ROOT / "src" / "claude" / "skills" / "research" / "SKILL.md"
        ).read_text(encoding="utf-8")
        frontmatter = skill.split("---", 2)[1]
        normalized_text = " ".join(skill.split())

        self.assertIsNotNone(
            re.search(r"(?m)^disable-model-invocation\s*:\s*true\s*$", frontmatter)
        )
        self.assertIn("E_NOT_IMPLEMENTED_WORK_ORDER_AUTHORITY", normalized_text)

    def test_codex_adapter_is_manual_only_until_work_orders_are_validated(self) -> None:
        skill = (
            ROOT / "src" / "agents" / "skills" / "research" / "SKILL.md"
        ).read_text(encoding="utf-8")
        policy = (
            ROOT
            / "src"
            / "agents"
            / "skills"
            / "research"
            / "agents"
            / "openai.yaml"
        ).read_text(encoding="utf-8")
        normalized_text = " ".join(skill.split())

        self.assertRegex(
            policy,
            r"(?m)^\s*allow_implicit_invocation\s*:\s*false\s*$",
        )
        self.assertIn("E_NOT_IMPLEMENTED_WORK_ORDER_AUTHORITY", normalized_text)

    def test_codex_dispatch_names_match_profile_identifiers(self) -> None:
        skill = (
            ROOT / "src" / "agents" / "skills" / "research" / "SKILL.md"
        ).read_text(encoding="utf-8")
        profiles = ROOT / "src" / "codex" / "agents"

        for path in sorted(profiles.glob("research-*.toml")):
            profile = tomllib.loads(path.read_text(encoding="utf-8"))
            expected_name = path.stem
            self.assertEqual(profile["name"], expected_name)
            self.assertIn(f"`{expected_name}`", skill)


if __name__ == "__main__":
    unittest.main()
