"""`python3 -m devforgeai.checkpoint validate --plan <dir> [--diff <base>..<head>] [--json]`.

No policy option exists (corrective-spec-001 CS-2): the schemas and the Git
root are resolved by the validator, never by the caller. The closure range of
a closed record comes from its attestation (corrective-spec-002 CS-9); ``--diff``,
when given, must equal an attested range. Exit 0 holds, 1 rejected, 2 usage,
3 could not run.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from devforgeai.checkpoint.validate import CouldNotRun, validate_plan

USAGE = 2
COULD_NOT_RUN = 3


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python3 -m devforgeai.checkpoint", allow_abbrev=False)
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser(
        "validate",
        help="validate every checkpoint record of a research-gap closure plan",
        allow_abbrev=False,
    )
    validate.add_argument("--plan", required=True, type=Path,
                          help="plan directory holding README.md and checkpoints/")
    validate.add_argument("--diff", default=None,
                          help="Git range <base>..<head>; optional; when given it must equal the "
                               "attested closure range of a closed record")
    validate.add_argument("--json", action="store_true", help="machine-readable output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        report = validate_plan(args.plan, diff_range=args.diff)
    except CouldNotRun as exc:
        if args.json:
            print(json.dumps({"outcome": "COULD_NOT_RUN", "reason": str(exc)}))
        else:
            print(f"COULD_NOT_RUN: {exc}", file=sys.stderr)
        return COULD_NOT_RUN
    if args.json:
        print(json.dumps(report.to_dict(), indent=1, sort_keys=True))
    else:
        for problem in report.problems:
            print(f"{problem.checkpoint}: {problem.rule}: {problem.message}")
        print(f"{report.records} record(s), {len(report.problems)} problem(s); "
              f"outcome {report.outcome}")
    return 0 if not report.problems else 1


if __name__ == "__main__":
    sys.exit(main())
