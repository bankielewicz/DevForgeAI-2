"""Offline distribution and command-surface acceptance checks."""

from __future__ import annotations

import contextlib
import io
import shutil
import tempfile
import tomllib
import unittest
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

import setuptools.build_meta as build_backend

from devforgeai.research.cli import _parser


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ROOT = ROOT / "schemas" / "research" / "v1"
CANONICAL_OPERATIONS = (
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
)


class ResearchPackagingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._temporary_directory = tempfile.TemporaryDirectory(
            prefix="devforgeai-packaging-test-"
        )
        temporary_root = Path(cls._temporary_directory.name)
        project = temporary_root / "project"
        project.mkdir()
        shutil.copy2(ROOT / "pyproject.toml", project / "pyproject.toml")
        shutil.copytree(ROOT / "src", project / "src")
        shutil.copytree(ROOT / "schemas", project / "schemas")

        distribution_directory = temporary_root / "dist"
        distribution_directory.mkdir()
        with contextlib.chdir(project):
            wheel_name = build_backend.build_wheel(str(distribution_directory))
        cls.wheel = distribution_directory / wheel_name
        with ZipFile(cls.wheel) as archive:
            cls.wheel_names = set(archive.namelist())
            entry_point_name = next(
                name
                for name in cls.wheel_names
                if name.endswith(".dist-info/entry_points.txt")
            )
            cls.entry_points = archive.read(entry_point_name).decode("utf-8")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temporary_directory.cleanup()

    def test_pyproject_declares_the_frozen_console_entry_point(self) -> None:
        configuration = tomllib.loads(
            (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )
        self.assertEqual(
            configuration["project"]["scripts"],
            {"devforgeai-research": "devforgeai.research.cli:main"},
        )
        self.assertEqual(
            self.entry_points,
            "[console_scripts]\n"
            "devforgeai-research = devforgeai.research.cli:main\n",
        )

    def test_wheel_contains_every_core_python_module(self) -> None:
        expected = {
            path.relative_to(ROOT / "src").as_posix()
            for path in (ROOT / "src" / "devforgeai").rglob("*.py")
            if "__pycache__" not in path.parts
        }
        actual = {
            name
            for name in self.wheel_names
            if name.startswith("devforgeai/") and name.endswith(".py")
        }
        self.assertEqual(actual, expected)

    def test_wheel_contains_every_versioned_research_schema(self) -> None:
        expected = {path.name for path in SCHEMA_ROOT.glob("*.schema.json")}
        actual = {
            PurePosixPath(name).name
            for name in self.wheel_names
            if "/share/devforgeai/schemas/research/v1/" in name
            and name.endswith(".schema.json")
        }
        self.assertEqual(actual, expected)

        configuration = tomllib.loads(
            (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )
        self.assertEqual(
            configuration["tool"]["setuptools"]["data-files"],
            {
                "share/devforgeai/schemas/research/v1": [
                    "schemas/research/v1/*.schema.json"
                ]
            },
        )

    def test_provider_source_templates_are_not_installed(self) -> None:
        forbidden_segments = (
            "/claude/",
            "/codex/agents/",
            "/agents/skills/",
        )
        self.assertFalse(
            any(
                segment in f"/{name}"
                for name in self.wheel_names
                for segment in forbidden_segments
            )
        )

    def test_help_advertises_exactly_the_ten_canonical_operations(self) -> None:
        help_text = _parser().format_help()
        advertised = "{" + ",".join(CANONICAL_OPERATIONS) + "}"
        self.assertEqual(help_text.count(advertised), 2)

    def test_undeclared_short_aliases_are_not_callable(self) -> None:
        for alias in ("normalize", "open", "append", "validate", "seal"):
            with self.subTest(alias=alias), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    _parser().parse_args([alias])


if __name__ == "__main__":
    unittest.main()
