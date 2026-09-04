"""Positive and hostile tests for the staged release scaffold (corrective-spec-001 CS-5).

Everything runs unprivileged in scratch trees. The positive protected case (a
root-owned tree the validator accepts) cannot run here; it is DevForge's probe.

    python3 -m pytest components/devforge-release/tests -q
"""

from __future__ import annotations

import hashlib
import json
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
LAUNCHER = COMPONENT / "launcher"
MUSL = "x86_64-unknown-linux-musl"
SCHEMAS = ROOT / "schemas" / "devforgeai" / "v1"
_LAUNCHER_BINARY: Path | None = None


def launcher_binary() -> Path:
    """Build (once) and return the static launcher (CS-8.1). A missing crate, a
    missing toolchain target or a failed build is a failed assertion."""
    global _LAUNCHER_BINARY
    if _LAUNCHER_BINARY is not None:
        return _LAUNCHER_BINARY
    assert (LAUNCHER / "Cargo.toml").is_file(), f"launcher crate missing at {LAUNCHER}"
    code, out = sh("cargo", "build", "--release", "--locked", "--target", MUSL, cwd=LAUNCHER,
                   env=dict(os.environ, CARGO_TERM_COLOR="never"))
    assert code == 0, f"launcher build failed:\n{out[-3000:]}"
    binary = LAUNCHER / "target" / MUSL / "release" / "devforge"
    assert binary.is_file(), f"built binary missing: {binary}"
    _LAUNCHER_BINARY = binary
    return binary


def elf_summary(path: Path) -> dict:
    """Program headers and DT_NEEDED entries of a 64-bit little-endian ELF."""
    data = path.read_bytes()
    assert data[:4] == b"\x7fELF", "not an ELF file"
    assert data[4] == 2 and data[5] == 1, "not ELF64 little-endian"
    e_phoff = int.from_bytes(data[0x20:0x28], "little")
    e_phentsize = int.from_bytes(data[0x36:0x38], "little")
    e_phnum = int.from_bytes(data[0x38:0x3a], "little")
    types, needed = [], []
    for i in range(e_phnum):
        off = e_phoff + i * e_phentsize
        p_type = int.from_bytes(data[off:off + 4], "little")
        types.append(p_type)
        if p_type == 2:                                            # PT_DYNAMIC
            p_offset = int.from_bytes(data[off + 8:off + 16], "little")
            p_filesz = int.from_bytes(data[off + 32:off + 40], "little")
            dyn = data[p_offset:p_offset + p_filesz]
            for j in range(0, len(dyn) - 15, 16):
                tag = int.from_bytes(dyn[j:j + 8], "little")
                if tag == 1:                                       # DT_NEEDED
                    needed.append(int.from_bytes(dyn[j + 8:j + 16], "little"))
                if tag == 0:
                    break
    return {"has_interp": 3 in types, "needed": needed}


HOOK_C = r"""
#include <fcntl.h>
#include <unistd.h>
__attribute__((constructor)) static void devforge_hook_init(void) {
    int fd = open(MARKER, O_WRONLY | O_CREAT | O_APPEND, 0644);
    if (fd >= 0) { (void)!write(fd, "constructor ran\n", 16); close(fd); }
}
unsigned int la_version(unsigned int v) { return v; }
"""


def build_hook(tmp: Path, marker: Path) -> Path:
    """A constructor shared object that appends to `marker` whenever it is loaded."""
    source = tmp / "hook.c"
    source.write_text(HOOK_C, encoding="utf-8")
    so = tmp / "hook.so"
    code, out = sh("cc", "-shared", "-fPIC", f"-DMARKER=\"{marker}\"", "-o", str(so), str(source))
    assert code == 0, out
    return so


ENV_DUMPER = """#!/usr/bin/python3 -I
import json, os, sys
print(json.dumps({"env": dict(os.environ), "argv": sys.argv[1:], "flags": {
    "isolated": sys.flags.isolated, "safe_path": sys.flags.safe_path,
    "dont_write_bytecode": sys.flags.dont_write_bytecode}, "cwd": os.getcwd(), "file": __file__}))
"""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sh(*argv: str, cwd: Path | None = None, env: dict | None = None) -> tuple[int, str]:
    completed = subprocess.run(list(argv), capture_output=True, text=True, cwd=cwd, env=env)
    return completed.returncode, completed.stdout + completed.stderr


def build_tree(dest: Path, with_deps: bool = False) -> Path:
    """Build the installed layout from the candidate bytes (README 'How DevForge builds')."""
    for sub in ("bin", "lib/devforgeai/checkpoint", "schemas/devforgeai/v1", "contracts"):
        (dest / sub).mkdir(parents=True, exist_ok=True)
    launcher = LAUNCHER / "target" / MUSL / "release" / "devforge"
    if (LAUNCHER / "Cargo.toml").is_file():
        launcher = launcher_binary()
    shutil.copy2(launcher if launcher.is_file() else COMPONENT / "bin" / "devforge", dest / "bin" / "devforge")
    shutil.copy2(COMPONENT / "bin" / "devforge-checkpoint.py", dest / "bin" / "devforge-checkpoint.py")
    for name in ("devforge", "devforge-checkpoint.py"):
        (dest / "bin" / name).chmod(0o755)
    for name in ("release-identity.schema.json", "closure-attestation.schema.json"):
        if (SCHEMAS / name).is_file():
            shutil.copy2(SCHEMAS / name, dest / "schemas" / "devforgeai" / "v1" / name)
    if (COMPONENT / "gen_release_identity.py").is_file():
        code, out = sh(sys.executable, str(COMPONENT / "gen_release_identity.py"), "--root", str(dest),
                       "--version", "1.0.0-test", "--devforge-commit", "0" * 40, "--devforge-tag", "v1.0.0-test",
                       "--candidate-repository", "https://example.invalid/DevForgeAI", "--candidate-checkpoint", "CP-00",
                       "--candidate-source-commit", "1" * 40, "--candidate-manifest", str(POLICY),
                       "--launcher-toolchain", "rustc (fixture)", "--built-at", "2026-09-04T00:00:00Z")
        assert code == 0, out
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

    # ---- static Rust launcher (corrective-spec-002 CS-8) ----

    def _launcher_root(self, dumper: bool = True) -> Path:
        """A release-shaped tree whose bin/devforge is the built launcher and whose
        bin/devforge-checkpoint.py dumps its environment as JSON."""
        root = self.tmp / "rel"
        (root / "bin").mkdir(parents=True)
        shutil.copy2(launcher_binary(), root / "bin" / "devforge")
        (root / "bin" / "devforge").chmod(0o755)
        script = root / "bin" / "devforge-checkpoint.py"
        script.write_text(ENV_DUMPER if dumper else "print('launcher ran')\n", encoding="utf-8")
        script.chmod(0o755)
        return root

    def test_launcher_is_static(self) -> None:                                   # CS-8.1
        summary = elf_summary(launcher_binary())
        self.assertFalse(summary["has_interp"], "PT_INTERP present: dynamically loaded")
        self.assertEqual(summary["needed"], [], "DT_NEEDED entries present")

    def test_launcher_lock_has_no_dependencies(self) -> None:                    # CS-8.1, CS-8.6
        lock = LAUNCHER / "Cargo.lock"
        self.assertTrue(lock.is_file(), "Cargo.lock missing")
        packages = re.findall(r'^name = "([^"]+)"', lock.read_text(encoding="utf-8"), re.M)
        self.assertEqual(packages, ["devforge"], packages)
        toolchain = (LAUNCHER / "rust-toolchain.toml").read_text(encoding="utf-8")
        self.assertIn(MUSL, toolchain)
        self.assertRegex(toolchain, r'channel = "\d+\.\d+\.\d+"')

    def test_launcher_child_environment_is_exact(self) -> None:                  # CS-8.2
        root = self._launcher_root()
        hostile = dict(os.environ, LD_PRELOAD="/nonexistent/x.so", LD_AUDIT="/nonexistent/y.so",
                       GIT_DIR="/nonexistent/.git", GIT_WORK_TREE="/nonexistent", PYTHONPATH="/nonexistent",
                       PYTHONHOME="/nonexistent", PYTHONSTARTUP="/nonexistent/s.py", DEVFORGE_X="1")
        code, out = sh(str(root / "bin" / "devforge"), "checkpoint", "validate", "--plan", "x", "--json", env=hostile)
        self.assertEqual(code, 0, out)
        seen = json.loads(out)
        self.assertEqual(seen["env"], {"PATH": "/usr/bin:/bin", "LC_ALL": "C.UTF-8", "LANG": "C.UTF-8"})
        self.assertEqual(seen["argv"], ["validate", "--plan", "x", "--json"])
        self.assertEqual(seen["flags"], {"isolated": 1, "safe_path": True, "dont_write_bytecode": 1})

    def _loader_variable_is_inert(self, variable: str) -> None:
        marker = self.tmp / "marker.txt"
        hook = build_hook(self.tmp, marker)
        env = dict(os.environ, **{variable: str(hook)})
        # positive control: the constructor fires in an ordinary dynamic process
        sh("/bin/sh", "-c", "true", env=env)
        self.assertTrue(marker.is_file(), f"positive control: {variable} hook never fired under /bin/sh")
        marker.unlink()
        root = self._launcher_root(dumper=False)
        code, out = sh(str(root / "bin" / "devforge"), "checkpoint", "validate", "--plan", "x", env=env)
        self.assertEqual(code, 0, out)
        self.assertIn("launcher ran", out)
        self.assertFalse(marker.exists(), f"{variable} constructor ran inside the launcher process")

    def test_launcher_ignores_ld_preload(self) -> None:                          # CS-8.3
        self._loader_variable_is_inert("LD_PRELOAD")

    def test_launcher_ignores_ld_audit(self) -> None:                            # CS-8.3
        self._loader_variable_is_inert("LD_AUDIT")

    def test_launcher_root_from_running_executable(self) -> None:                # CS-8.4
        root = self._launcher_root()
        elsewhere = self.tmp / "elsewhere"
        elsewhere.mkdir()
        (elsewhere / "bin").mkdir()
        (elsewhere / "bin" / "devforge-checkpoint.py").write_text("print('wrong launcher')\n", encoding="utf-8")
        code, out = sh(str(root / "bin" / "devforge"), "checkpoint", "validate", "--plan", "x", cwd=elsewhere)
        self.assertEqual(code, 0, out)
        seen = json.loads(out)
        self.assertEqual(seen["file"], str(root / "bin" / "devforge-checkpoint.py"))

    def test_launcher_refuses_relative_invocation(self) -> None:                 # CS-8.4
        root = self._launcher_root()
        code, out = sh("bin/devforge", "checkpoint", "validate", "--plan", "x", cwd=root)
        self.assertEqual(code, 2, out)
        self.assertIn("absolute path", out)

    def test_launcher_refuses_unknown_command(self) -> None:                     # CS-8.5
        root = self._launcher_root()
        for argv in (("research", "validate"), ("checkpoint",), ("checkpoint", "promote"), ()):
            with self.subTest(argv=argv):
                code, out = sh(str(root / "bin" / "devforge"), *argv)
                self.assertEqual(code, 2, out)
                self.assertIn("usage", out)

    def test_build_digest_matches_binary(self) -> None:                          # CS-8.6
        digest_file = LAUNCHER / "BUILD-DIGEST.txt"
        self.assertTrue(digest_file.is_file(), "BUILD-DIGEST.txt missing")
        text = digest_file.read_text(encoding="utf-8")
        recorded = re.search(r"^sha256\s+([0-9a-f]{64})", text, re.M)
        self.assertIsNotNone(recorded, text)
        self.assertEqual(recorded.group(1), sha256(launcher_binary()), "rebuilt binary digest differs from the pinned one")
        self.assertIn("rustc", text)
        self.assertIn(MUSL, text)

    # ---- attestation minting (CS-9.3) ----

    def _attest_fixture(self) -> tuple[Path, Path, str, str]:
        repo = self.tmp / "repo"
        plan = repo / "docs" / "plan"
        (plan / "checkpoints").mkdir(parents=True)
        (plan / "README.md").write_text("| Plan ID | `SCRATCH` |\n| Decision authority | `github:x` |\n", encoding="utf-8")
        (plan / "checkpoints" / "CP-00.yaml").write_text("checkpoint_id: CP-00\nclosed: false\n", encoding="utf-8")
        def git(*argv: str) -> str:
            return subprocess.run(["git", "-C", str(repo), *argv], capture_output=True, text=True, check=True).stdout.strip()
        git("init", "-q"); git("config", "user.email", "f@x"); git("config", "user.name", "f")
        git("add", "-A"); git("commit", "-q", "-m", "work"); base = git("rev-parse", "HEAD")
        (plan / "checkpoints" / "CP-00.yaml").write_text("checkpoint_id: CP-00\nclosed: true\n", encoding="utf-8")
        git("add", "-A"); git("commit", "-q", "-m", "closure"); head = git("rev-parse", "HEAD")
        root = build_tree(self.tmp / "rel")
        generate(root)
        return repo, root, base, head

    def test_attest_dry_run_validates_against_schema(self) -> None:              # CS-9.1, CS-9.3
        import jsonschema
        repo, root, base, head = self._attest_fixture()
        code, out = sh(str(root / "bin" / "devforge"), "checkpoint", "attest", "--repo", str(repo),
                       "--plan", "docs/plan", "--checkpoint", "CP-00", "--base", base, "--head", head,
                       "--authority", "github:x", "--review", "https://example.invalid/pull/1#review", "--dry-run")
        self.assertEqual(code, 0, out)
        document = json.loads(out)
        schema = json.loads((SCHEMAS / "closure-attestation.schema.json").read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(schema).validate(document)
        self.assertEqual(document["base_commit"], base)
        self.assertEqual(document["head_commit"], head)
        blob = subprocess.run(["git", "-C", str(repo), "cat-file", "blob", f"{head}:docs/plan/checkpoints/CP-00.yaml"],
                              capture_output=True, check=True).stdout
        self.assertEqual(document["record_sha256"], hashlib.sha256(blob).hexdigest())
        self.assertEqual(document["release_root"], str(root))
        self.assertEqual(document["release_identity_sha256"], sha256(root / "RELEASE-IDENTITY.json"))
        self.assertEqual(document["plan_id"], "SCRATCH")
        roots = subprocess.run(["git", "-C", str(repo), "rev-list", "--max-parents=0", "HEAD"],
                               capture_output=True, text=True, check=True).stdout.split()
        self.assertEqual(document["repository_root_commits"], sorted(roots))
        self.assertEqual(document["repository_identity"], hashlib.sha256("\n".join(sorted(roots)).encode()).hexdigest())

    def test_attest_refuses_without_root(self) -> None:                          # CS-9.3
        if os.getuid() == 0:
            self.skipTest("running as root")
        repo, root, base, head = self._attest_fixture()
        code, out = sh(str(root / "bin" / "devforge"), "checkpoint", "attest", "--repo", str(repo),
                       "--plan", "docs/plan", "--checkpoint", "CP-00", "--base", base, "--head", head,
                       "--authority", "github:x", "--review", "r")
        self.assertEqual(code, 2, out)
        self.assertIn("uid 0", out)

    def test_attest_refuses_base_not_ancestor(self) -> None:                     # CS-9.3
        repo, root, base, head = self._attest_fixture()
        code, out = sh(str(root / "bin" / "devforge"), "checkpoint", "attest", "--repo", str(repo),
                       "--plan", "docs/plan", "--checkpoint", "CP-00", "--base", head, "--head", base,
                       "--authority", "github:x", "--review", "r", "--dry-run")
        self.assertEqual(code, 1, out)
        self.assertIn("ancestor", out)

    def test_attest_refuses_hostile_plan_id(self) -> None:                       # CS-9.7
        # A Plan ID that is an absolute path must not become a root-written location.
        repo, root, base, head = self._attest_fixture()
        readme = repo / "docs" / "plan" / "README.md"
        readme.write_text("| Plan ID | `/etc/cron.d` |\n| Decision authority | `github:x` |\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(repo), "commit", "-q", "-am", "hostile plan id"], check=True)
        head = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        code, out = sh(str(root / "bin" / "devforge"), "checkpoint", "attest", "--repo", str(repo),
                       "--plan", "docs/plan", "--checkpoint", "CP-00", "--base", base, "--head", head,
                       "--authority", "github:x", "--review", "r", "--dry-run")
        self.assertEqual(code, 1, out)
        self.assertIn("plan id", out)
        self.assertNotIn("/etc/cron.d/CP-00.json", out)

    # ---- scaffold follow-ups (CS-10) ----

    def test_installer_requires_verifier(self) -> None:                          # CS-10.1
        release = self._release()
        alone = self.tmp / "alone"
        alone.mkdir()
        shutil.copy2(COMPONENT / "install.sh", alone / "install.sh")
        target = self.tmp / "installed" / "x"
        code, out = sh("sh", str(alone / "install.sh"), "--release", str(release), "--root", str(target))
        self.assertEqual(code, 1, out)
        self.assertIn("verify-release.sh", out)
        self.assertFalse(target.exists(), "installed without the verifier")

    def test_generator_requires_identity_and_static_launcher(self) -> None:      # CS-10.2
        root = build_tree(self.tmp / "rel")
        (root / "RELEASE-IDENTITY.json").unlink(missing_ok=True)
        code, out = generate(root)
        self.assertNotEqual(code, 0, out)
        self.assertIn("RELEASE-IDENTITY.json", out)
        root2 = build_tree(self.tmp / "rel2")
        (root2 / "bin" / "devforge").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        code, out = generate(root2)
        self.assertNotEqual(code, 0, out)
        self.assertIn("static", out)

    def test_verifier_rejects_loose_modes(self) -> None:                         # CS-10.2
        root = build_tree(self.tmp / "rel")
        generate(root)
        code, out = verify(root)
        self.assertIn("MODES: OK", out)
        (root / "lib" / "devforgeai" / "__init__.py").chmod(0o664)
        code, out = verify(root)
        self.assertIn("MODES: FAIL", out)
        self.assertIn("lib/devforgeai/__init__.py", out)

    def test_release_identity_generator_output_validates(self) -> None:          # CS-10.3
        import jsonschema
        root = build_tree(self.tmp / "rel")
        identity = root / "RELEASE-IDENTITY.json"
        self.assertTrue(identity.is_file(), "RELEASE-IDENTITY.json not generated")
        document = json.loads(identity.read_text(encoding="utf-8"))
        schema = json.loads((SCHEMAS / "release-identity.schema.json").read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(schema).validate(document)
        self.assertEqual(document["candidate_manifest_sha256"], sha256(POLICY))
        self.assertNotIn("release_manifest_sha256", document)


if __name__ == "__main__":
    unittest.main()
