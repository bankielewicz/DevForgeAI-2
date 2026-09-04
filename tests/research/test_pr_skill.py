"""Contracts for the PR packet, adapters, and exact-range entry gate."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "schemas" / "devforgeai" / "v1" / "pr-packet.schema.json"
RUN_SCHEMA = ROOT / "schemas" / "devforgeai" / "v2" / "run.schema.json"
TAXONOMY_SCHEMA = ROOT / "schemas" / "devforgeai" / "v2" / "error-taxonomy.schema.json"
TAXONOMY = ROOT / "framework" / "contracts" / "error-taxonomy-v2.yaml"


def valid_packet() -> dict:
    return {
        "schema": "devforgeai.pr-packet/v1",
        "run": "pr-111111111111-222222222222",
        "range": {
            "base": "1" * 40,
            "head": "2" * 40,
            "base_ref": "main",
            "head_ref": "feature/example",
        },
        "repository": "bankielewicz/DevForgeAI",
        "types": ["governance_amendment", "implementation"],
        "changed_paths": [
            {"status": "M", "path": "AGENTS.md"},
            {"status": "A", "path": "src/example.py"},
        ],
        "artifacts": {
            "title": {
                "path": ".devforgeai/work/pr-111111111111-222222222222/output/title.txt",
                "sha256": "sha256:" + "a" * 64,
            },
            "body": {
                "path": ".devforgeai/work/pr-111111111111-222222222222/output/body.md",
                "sha256": "sha256:" + "b" * 64,
            },
            "request": {
                "path": ".devforgeai/work/pr-111111111111-222222222222/output/pr-request.json",
                "sha256": "sha256:" + "c" * 64,
            },
        },
        "draft": False,
        "post_action_next": "/status",
        "created_at": "2026-09-04T12:00:00Z",
    }


class PrPacketSchemaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8")))

    def assert_valid(self, packet: dict) -> None:
        self.assertEqual(list(self.validator.iter_errors(packet)), [])

    def assert_invalid(self, packet: dict) -> None:
        self.assertNotEqual(list(self.validator.iter_errors(packet)), [])

    def test_complete_packet_is_valid(self) -> None:
        self.assert_valid(valid_packet())

    def test_commit_ids_are_full_lowercase_sha1(self) -> None:
        packet = valid_packet()
        packet["range"]["head"] = "2" * 39
        self.assert_invalid(packet)

    def test_packet_rejects_unknown_fields(self) -> None:
        packet = valid_packet()
        packet["publish_it"] = True
        self.assert_invalid(packet)

    def test_types_are_closed_and_unique(self) -> None:
        packet = valid_packet()
        packet["types"] = ["implementation", "implementation"]
        self.assert_invalid(packet)
        packet["types"] = ["made_up"]
        self.assert_invalid(packet)


class PrAdapterContractTests(unittest.TestCase):
    def test_provider_adapters_are_explicit_and_accept_only_the_exact_range_form(self) -> None:
        claude = (ROOT / "providers/claude/skills/pr/SKILL.md").read_text(encoding="utf-8")
        codex = (ROOT / "providers/codex/skills/pr/SKILL.md").read_text(encoding="utf-8")
        openai = (ROOT / "providers/codex/skills/pr/agents/openai.yaml").read_text(
            encoding="utf-8"
        )

        self.assertRegex(
            claude.split("---", 2)[1],
            r"(?m)^disable-model-invocation\s*:\s*true\s*$",
        )
        self.assertRegex(openai, r"(?m)^\s*allow_implicit_invocation\s*:\s*false\s*$")
        exact = "--base <40-lowercase-hex> --head <40-lowercase-hex> [--draft]"
        self.assertIn(exact, claude)
        self.assertIn(exact, codex)

    def test_worker_profiles_match_the_two_role_contract(self) -> None:
        drafter = (
            ROOT / "providers/claude/agents/pr-drafter.md"
        ).read_text(encoding="utf-8")
        critic = (
            ROOT / "providers/claude/agents/pr-critic.md"
        ).read_text(encoding="utf-8")

        self.assertRegex(drafter, r"(?m)^writes:\s*candidate\s*$")
        self.assertRegex(critic, r"(?m)^writes:\s*none\s*$")
        critic_frontmatter = critic.split("---", 2)[1]
        self.assertIsNone(re.search(r"(?m)^tools:.*(?:Write|Edit)", critic_frontmatter))


class PrRuntimeContractTests(unittest.TestCase):
    def test_range_run_uses_the_version_2_run_contract(self) -> None:
        fixture = yaml.safe_load(
            (
                ROOT
                / "docs/design/examples/hooks/fixtures/.devforgeai/work/STORY-001/run.yaml"
            ).read_text(encoding="utf-8")
        )
        base = "1" * 40
        head = "2" * 40
        fixture.update(
            {
                "run": "pr-111111111111-222222222222",
                "skill": "pr",
                "arg": f"{base}..{head}",
                "kind": "range",
                "phase": "draft",
                "write_fence": ["pr-artifacts/title.txt", "pr-artifacts/body.md"],
                "test_paths": [],
                "test_plan": [],
                "commands": {},
                "granted_keys": [],
                "attempts": {"draft": 0, "critique": 0},
                "max_attempts": {"draft": 2, "critique": 2},
                "range": {
                    "base": base,
                    "head": head,
                    "base_ref": "main",
                    "head_ref": "feature/example",
                },
                "repository": "bankielewicz/DevForgeAI",
                "changed_paths": [{"status": "M", "path": "AGENTS.md"}],
                "pr_types": ["implementation"],
                "draft": False,
                "post_action_next": "/status",
            }
        )
        fixture["lease"].update({"agent": "pr_drafter", "phase": "draft"})

        validator = Draft202012Validator(json.loads(RUN_SCHEMA.read_text(encoding="utf-8")))
        self.assertEqual(list(validator.iter_errors(fixture)), [])

    def test_version_2_taxonomy_validates_and_contains_pr_codes(self) -> None:
        taxonomy = yaml.safe_load(TAXONOMY.read_text(encoding="utf-8"))
        schema = json.loads(TAXONOMY_SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(list(Draft202012Validator(schema).iter_errors(taxonomy)), [])
        self.assertEqual(taxonomy["taxonomy_version"], 2)
        self.assertIn("PR_RANGE", taxonomy["sequencer_refusals"])
        self.assertIn("complete_external", taxonomy["run_states"])


if __name__ == "__main__":
    unittest.main()
