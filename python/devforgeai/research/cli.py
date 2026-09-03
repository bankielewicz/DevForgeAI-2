"""Command-line adapter for :mod:`devforgeai.research`."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from .core import ResearchError, ResearchStore, canonical_json


def _json_argument(value: str) -> Any:
    if value == "-":
        text = sys.stdin.read()
    else:
        candidate = Path(value)
        if candidate.is_file():
            text = candidate.read_text(encoding="utf-8")
        else:
            text = value
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ResearchError(f"invalid JSON input: {exc}") from exc


def _emit(value: Any, *, stream: Any = sys.stdout) -> None:
    stream.buffer.write(canonical_json(value) + b"\n")
    stream.flush()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="devforgeai-research")
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    commands = parser.add_subparsers(
        dest="command",
        required=True,
        metavar=(
            "{normalize-request,open-run,append-record,put-source,"
            "transition-run,validate-run,seal-run,render,render-handoff,"
            "resume-run}"
        ),
    )

    normalize = commands.add_parser("normalize-request")
    normalize.add_argument("request", help="JSON text, a JSON file, or '-' for stdin")

    open_command = commands.add_parser("open-run")
    open_command.add_argument("request", help="JSON text, a JSON file, or '-' for stdin")
    open_command.add_argument("--confirmed-digest", required=True)

    append = commands.add_parser("append-record")
    append.add_argument("slug")
    append.add_argument("run_id")
    append.add_argument("kind")
    append.add_argument("record", help="JSON text, a JSON file, or '-' for stdin")

    put_source = commands.add_parser("put-source")
    put_source.add_argument("slug")
    put_source.add_argument("run_id")
    put_source.add_argument("source_id")
    put_source.add_argument("path", type=Path)
    put_source.add_argument("metadata", help="JSON text, a JSON file, or '-' for stdin")

    transition = commands.add_parser("transition-run")
    transition.add_argument("slug")
    transition.add_argument("run_id")
    transition.add_argument("to_phase")
    transition.add_argument("--reason")

    for name in (
        "validate-run",
        "seal-run",
        "render",
        "render-handoff",
        "resume-run",
    ):
        command = commands.add_parser(name)
        command.add_argument("slug")
        command.add_argument("run_id")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        store = ResearchStore(args.workspace)
        if args.command == "normalize-request":
            normalized, digest = store.normalize_request(_json_argument(args.request))
            _emit({"digest": digest, "normalized": normalized})
        elif args.command == "open-run":
            ref = store.open_run(
                _json_argument(args.request), args.confirmed_digest
            )
            _emit(ref.to_dict())
        elif args.command == "append-record":
            digest = store.append_record(
                args.slug, args.run_id, args.kind, _json_argument(args.record)
            )
            _emit({"record_digest": digest})
        elif args.command == "put-source":
            result = store.put_source(
                args.slug,
                args.run_id,
                args.source_id,
                args.path,
                _json_argument(args.metadata),
            )
            _emit(result)
        elif args.command == "transition-run":
            ref = store.transition(
                args.slug, args.run_id, args.to_phase, reason=args.reason
            )
            _emit(ref.to_dict())
        elif args.command == "validate-run":
            report = store.validate_run(args.slug, args.run_id)
            _emit(report.to_dict())
            return 0 if report.valid else 1
        elif args.command == "seal-run":
            _emit(store.seal_result(args.slug, args.run_id))
        elif args.command == "render":
            _emit(store.render(args.slug, args.run_id))
        elif args.command == "render-handoff":
            _emit({"handoff": store.render_handoff(args.slug, args.run_id)})
        elif args.command == "resume-run":
            _emit(store.resume_run(args.slug, args.run_id).to_dict())
        else:  # argparse makes this unreachable
            raise ResearchError(f"unsupported command: {args.command}")
    except (ResearchError, OSError) as exc:
        _emit(
            {"error": type(exc).__name__, "message": str(exc)},
            stream=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
