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
    evidence = scratch.commit("evidence")
    record = scratch.close("CP-00", evidence)
    record["enforcement"]["protected_release"]["schema_set_sha256"] = "not-a-digest"
    scratch.materialize()
    scratch.commit("structurally invalid closure")
    evil_schema = scratch.root / "evil-schema.json"
    evil_schema.write_text("{}\n", encoding="utf-8")

    protected_code, protected_output = module.run_validator(
        scratch.plan, "--schema", str(module.SCHEMA)
    )
    override_code, override_output = module.run_validator(
        scratch.plan,
        "--schema",
        str(module.SCHEMA),
        "--schema",
        str(evil_schema),
    )
    print(f"protected_schema exit={protected_code}")
    print(protected_output, end="")
    print(f"caller_override exit={override_code}")
    print(override_output, end="")
finally:
    scratch.cleanup()
