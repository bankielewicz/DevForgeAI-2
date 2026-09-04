"""`python3 -m devforgeai.checkpoint validate --plan <dir> [--git-root <dir>] [--diff <range>] [--json]`."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from devforgeai.checkpoint.validate import CouldNotRun, validate_plan

USAGE = 2
COULD_NOT_RUN = 3


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python3 -m devforgeai.checkpoint")
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser(
        "validate",
        help="validate every checkpoint record of a research-gap closure plan",
    )
    validate.add_argument("--plan", required=True, type=Path,
                          help="plan directory holding README.md and checkpoints/")
    validate.add_argument("--git-root", type=Path, default=None,
                          help="repository root for Git rules (default: the plan's repository)")
    validate.add_argument("--schema", type=Path, default=None,
                          help="override the checkpoint schema path (tests only)")
    validate.add_argument("--diff", default=None,
                          help="Git range <base>..<head>; a diff that closes a record may touch closure paths only")
    validate.add_argument("--json", action="store_true", help="machine-readable output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        report = validate_plan(args.plan, git_root=args.git_root, schema_path=args.schema,
                               diff_range=args.diff)
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
