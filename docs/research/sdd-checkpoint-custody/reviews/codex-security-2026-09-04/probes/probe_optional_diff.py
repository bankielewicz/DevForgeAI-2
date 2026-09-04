from __future__ import annotations

import importlib.util
from pathlib import Path


scan_root = Path(__file__).resolve().parents[2]
source_root = scan_root / "source"
test_path = source_root / "tests" / "research" / "test_gap_checkpoints.py"
spec = importlib.util.spec_from_file_location("gap_tests", test_path)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

scratch = module.Scratch()
try:
    scratch.write_dossier("CP-00")
    scratch.write_candidate("CP-00")
    scratch.materialize()
    base = scratch.commit("open")
    scratch.close("CP-00", base)
    scratch.materialize()
    (scratch.root / "implementation.py").write_text("changed in closure PR\n", encoding="utf-8")
    head = scratch.commit("closure plus implementation")

    omitted_code, omitted_output = module.run_validator(scratch.plan)
    checked_code, checked_output = module.run_validator(
        scratch.plan, "--diff", f"{base}..{head}"
    )
    print(f"diff_omitted exit={omitted_code}")
    print(omitted_output, end="")
    print(f"diff_supplied exit={checked_code}")
    print(checked_output, end="")
finally:
    scratch.cleanup()
