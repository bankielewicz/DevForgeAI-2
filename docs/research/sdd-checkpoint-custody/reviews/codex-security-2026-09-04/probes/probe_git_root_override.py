from __future__ import annotations

import importlib.util
import subprocess
import tempfile
from pathlib import Path


scan_root = Path(__file__).resolve().parents[2]
source_root = scan_root / "source"
test_path = source_root / "tests" / "research" / "test_gap_checkpoints.py"
spec = importlib.util.spec_from_file_location("gap_tests", test_path)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

scratch = module.Scratch()
alternate_tmp = tempfile.TemporaryDirectory(prefix="dfai-cp00-alt-root-")
try:
    scratch.stage_candidate("CP-00")
    scratch.materialize()
    scratch.commit("open staged candidate")
    alternate = Path(alternate_tmp.name) / "clean"
    subprocess.run(
        ["git", "clone", "--quiet", str(scratch.root), str(alternate)],
        check=True,
    )

    (scratch.root / "src" / "validator.py").write_text(
        "print('agent-controlled drift')\n", encoding="utf-8"
    )
    normal_code, normal_output = module.run_validator(scratch.plan)
    override_code, override_output = module.run_validator(
        scratch.plan, "--git-root", str(alternate)
    )
    print(f"actual_root exit={normal_code}")
    print(normal_output, end="")
    print(f"caller_git_root exit={override_code}")
    print(override_output, end="")
finally:
    alternate_tmp.cleanup()
    scratch.cleanup()
