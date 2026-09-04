"""Positive and hostile tests for the staged release scaffold (corrective-spec-001 CS-5).

Everything runs unprivileged in scratch trees. The positive protected case (a
root-owned tree the validator accepts) cannot run here; it is DevForge's probe.

    python3 -m pytest components/devforge-release/tests -q
"""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
COMPONENT = HERE.parent
ROOT = COMPONENT.parents[1]
SRC = ROOT / "components" / "research-core" / "src"
SCHEMA = ROOT / "schemas" / "devforgeai" / "v1" / "research-gap-checkpoint.schema.json"
POLICY = ROOT / "framework" / "contracts" / "MANIFEST.sha256"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sh(*argv: str, cwd: Path | None = None, env: dict | None = None) -> tuple[int, str]:
    completed = subprocess.run(list(argv), capture_output=True, text=True, cwd=cwd, env=env)
    return completed.returncode, completed.stdout + completed.stderr


def build_tree(dest: Path, with_deps: bool = False) -> Path:
    """Build the installed layout from the candidate bytes (README 'How DevForge builds')."""
    for sub in ("bin", "lib/devforgeai/checkpoint", "schemas/devforgeai/v1", "contracts"):
        (dest / sub).mkdir(parents=True, exist_ok=True)
    for name in ("devforge", "devforge-checkpoint.py"):
        shutil.copy2(COMPONENT / "bin" / name, dest / "bin" / name)
        (dest / "bin" / name).chmod(0o755)
    shutil.copy2(SRC / "devforgeai" / "__init__.py", dest / "lib" / "devforgeai" / "__init__.py")
    for name in ("__init__.py", "__main__.py", "validate.py"):
        shutil.copy2(SRC / "devforgeai" / "checkpoint" / name, dest / "lib" / "devforgeai" / "checkpoint" / name)
    shutil.copy2(SCHEMA, dest / "schemas" / "devforgeai" / "v1" / SCHEMA.name)
    shutil.copy2(POLICY, dest / "contracts" / "MANIFEST.sha256")
    if with_deps:
        code, out = sh(sys.executable, "-m", "pip", "install", "--no-index", "--find-links", str(COMPONENT / "wheels"),
                       "--require-hashes", "-r", str(COMPONENT / "requirements.lock"), "--target", str(dest / "lib"),
                       "--no-compile", "--quiet", "--disable-pip-version-check")
        assert code == 0, out
        for cache in dest.rglob("__pycache__"):
            shutil.rmtree(cache)
    return dest


def generate(root: Path) -> tuple[int, str]:
    return sh(sys.executable, str(COMPONENT / "gen_release_manifest.py"), str(root))


def verify(root: Path) -> tuple[int, str]:
    return sh("sh", str(COMPONENT / "verify-release.sh"), str(root))


class ReleaseScaffoldTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="dfai-release-")
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    # ---- lockfile and wheels (CS-5.3) ----

    def test_lockfile_hashes_match_wheels(self) -> None:
        lock = (COMPONENT / "requirements.lock").read_text(encoding="utf-8")
        hashes = set(re.findall(r"--hash=sha256:([0-9a-f]{64})", lock))
        wheels = {sha256(w): w.name for w in (COMPONENT / "wheels").glob("*.whl")}
        self.assertTrue(hashes)
        self.assertEqual(hashes, set(wheels), "every lock hash names a vendored wheel and vice versa")
        provenance = (COMPONENT / "wheels" / "PROVENANCE.md").read_text(encoding="utf-8")
        for digest, name in wheels.items():
            self.assertIn(name, provenance)
            self.assertEqual(provenance.count(digest), 2, f"{name}: pypi and local digests both recorded and equal")

    def test_offline_hash_locked_install_into_target(self) -> None:
        lib = self.tmp / "lib"
        lib.mkdir()
        code, out = sh(sys.executable, "-m", "pip", "install", "--no-index", "--find-links", str(COMPONENT / "wheels"),
                       "--require-hashes", "-r", str(COMPONENT / "requirements.lock"), "--target", str(lib),
                       "--no-compile", "--quiet", "--disable-pip-version-check")
        self.assertEqual(code, 0, out)
        self.assertTrue((lib / "yaml").is_dir() and (lib / "jsonschema").is_dir())

    # ---- generator and verifier (CS-5.4) ----

    def test_generator_lists_every_file_and_verifier_agrees(self) -> None:
        root = build_tree(self.tmp / "rel")
        code, out = generate(root)
        self.assertEqual(code, 0, out)
        listed = {line.split("  ", 1)[1] for line in (root / "RELEASE.sha256").read_text().splitlines()}
        present = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and p.name != "RELEASE.sha256"}
        self.assertEqual(listed, present)
        code, out = verify(root)
        self.assertIn("DIGEST: OK", out)
        self.assertIn("SYMLINKS: OK", out)
        self.assertIn("COVERAGE: OK", out)
        self.assertIn("REQUIRED: OK", out)
        self.assertIn("OWNERSHIP: FAIL", out)        # user-owned scratch tree, by design
        self.assertNotEqual(code, 0)

    def test_generator_refuses_symlink(self) -> None:
        root = build_tree(self.tmp / "rel")
        (root / "bin" / "alias").symlink_to(root / "bin" / "devforge")
        code, out = generate(root)
        self.assertNotEqual(code, 0)
        self.assertIn("symbolic link", out)

    def test_generator_and_verifier_disagree_on_tamper(self) -> None:
        root = build_tree(self.tmp / "rel")
        generate(root)
        (root / "lib" / "devforgeai" / "checkpoint" / "validate.py").write_text("# tampered\n", encoding="utf-8")
        code, out = verify(root)
        self.assertIn("DIGEST: FAIL", out)
        # the generator would happily rewrite the manifest over the tamper: it is not a verifier
        code, out = generate(root)
        self.assertEqual(code, 0, out)
        self.assertIn("not verified", out)

    def test_verifier_detects_unlisted_file(self) -> None:
        root = build_tree(self.tmp / "rel")
        generate(root)
        (root / "lib" / "extra.py").write_text("print('unlisted')\n", encoding="utf-8")
        code, out = verify(root)
        self.assertIn("COVERAGE: FAIL", out)
        self.assertIn("lib/extra.py", out)

    # ---- installer (CS-5.5) ----

    def _release(self) -> Path:
        root = build_tree(self.tmp / "release")
        generate(root)
        return root

    def test_installer_unprivileged_installs_and_reports(self) -> None:
        release = self._release()
        target = self.tmp / "installed" / "1.0.0-test"
        code, out = sh("sh", str(COMPONENT / "install.sh"), "--release", str(release), "--root", str(target))
        self.assertEqual(code, 0, out)
        self.assertIn("NOT a protected install", out)
        self.assertTrue((target / "bin" / "devforge").is_file())
        self.assertEqual(sha256(target / "RELEASE.sha256"), sha256(release / "RELEASE.sha256"))
        self.assertFalse(list((self.tmp / "installed").glob(".*install*")), "no temporary sibling left behind")

    def test_installer_refuses_tampered_release(self) -> None:
        release = self._release()
        (release / "bin" / "devforge").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        target = self.tmp / "installed" / "x"
        code, out = sh("sh", str(COMPONENT / "install.sh"), "--release", str(release), "--root", str(target))
        self.assertEqual(code, 1, out)
        self.assertIn("do not verify", out)
        self.assertFalse(target.exists())

    def test_installer_refuses_existing_target(self) -> None:
        release = self._release()
        target = self.tmp / "installed" / "x"
        target.mkdir(parents=True)
        code, out = sh("sh", str(COMPONENT / "install.sh"), "--release", str(release), "--root", str(target))
        self.assertEqual(code, 2, out)
        self.assertIn("target exists", out)

    def test_installer_refuses_checkout_as_release(self) -> None:
        fake = self.tmp / "checkout"
        (fake / "components").mkdir(parents=True)
        (fake / "RELEASE.sha256").write_text("", encoding="utf-8")
        code, out = sh("sh", str(COMPONENT / "install.sh"), "--release", str(fake), "--root", str(self.tmp / "t"))
        self.assertEqual(code, 2, out)
        self.assertIn("checkout", out)

    def test_installer_refuses_unlisted_file(self) -> None:
        release = self._release()
        (release / "lib" / "extra.py").write_text("x\n", encoding="utf-8")
        code, out = sh("sh", str(COMPONENT / "install.sh"), "--release", str(release), "--root", str(self.tmp / "t"))
        self.assertEqual(code, 1, out)
        self.assertIn("cover exactly", out)

    # ---- wrapper and launcher (CS-2, CS-5.2) ----

    def test_wrapper_refuses_relative_invocation(self) -> None:
        root = build_tree(self.tmp / "rel")
        code, out = sh("sh", "bin/devforge", "checkpoint", cwd=root)
        self.assertEqual(code, 2, out)
        self.assertIn("absolute path", out)
        # a relative PATH entry also yields a relative $0
        env = dict(os.environ, PATH=f"bin:{os.environ.get('PATH', '')}")
        code, out = sh("devforge", "checkpoint", cwd=root, env=env)
        self.assertEqual(code, 2, out)
        self.assertIn("absolute path", out)

    def test_wrapper_refuses_unknown_command(self) -> None:
        root = build_tree(self.tmp / "rel")
        code, out = sh(str(root / "bin" / "devforge"), "research", "validate")
        self.assertEqual(code, 2, out)
        self.assertIn("usage", out)

    def test_installed_mode_refuses_unprotected_tree(self) -> None:
        # A user-owned copy of the release must not validate anything (layout rule 6):
        # the launcher runs the real validator, which verifies its own tree first.
        root = build_tree(self.tmp / "rel", with_deps=True)
        generate(root)
        plan = self.tmp / "plan"
        (plan / "checkpoints").mkdir(parents=True)
        (plan / "README.md").write_text("| Decision authority | `github:x` |\n", encoding="utf-8")
        env = dict(os.environ, PYTHONPATH="/nonexistent")     # must be ignored by -I
        code, out = sh(str(root / "bin" / "devforge"), "checkpoint", "validate", "--plan", str(plan), env=env)
        self.assertEqual(code, 3, out)
        self.assertIn("installed release fails verification", out)
        self.assertIn("not owned by uid 0", out)

    def test_installed_mode_rejects_schema_option(self) -> None:
        root = build_tree(self.tmp / "rel", with_deps=True)
        generate(root)
        code, out = sh(str(root / "bin" / "devforge"), "checkpoint", "validate", "--plan", "x", "--schema", "y")
        self.assertEqual(code, 2, out)
        self.assertIn("unrecognized", out)


if __name__ == "__main__":
    unittest.main()
