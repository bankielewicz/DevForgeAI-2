from __future__ import annotations

import importlib.util
from pathlib import Path


source_root = Path(__file__).resolve().parents[2] / "source"
test_path = source_root / "tests" / "research" / "test_gap_checkpoints.py"
spec = importlib.util.spec_from_file_location("gap_tests", test_path)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

scratch = module.Scratch()
try:
    evidence = scratch.commit("evidence")
    scratch.close("CP-00", evidence)
    scratch.materialize()
    scratch.commit("closure with user-owned protected executable")
    stat = scratch.executable.stat()
    code, output = module.run_validator(scratch.plan)
    print(f"user_owned_executable uid={stat.st_uid} mode={stat.st_mode & 0o777:o} exit={code}")
    print(output, end="")
finally:
    scratch.cleanup()

scratch = module.Scratch()
try:
    evidence = scratch.commit("evidence")
    scratch.close("CP-00", evidence)
    scratch.executable.unlink()
    scratch.materialize()
    scratch.commit("closure with missing protected executable")
    code, output = module.run_validator(scratch.plan)
    print(f"missing_executable exit={code}")
    print(output, end="")
finally:
    scratch.cleanup()
