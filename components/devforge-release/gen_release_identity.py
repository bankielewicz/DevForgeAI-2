#!/usr/bin/python3
"""Write RELEASE-IDENTITY.json for a built release tree (installed-layout contract v2,
corrective-spec-002 CS-6.3 and CS-10.3).

    python3 gen_release_identity.py --root <build tree> --version <v> --devforge-commit <sha> \\
        --devforge-tag <tag> --candidate-repository <url> --candidate-checkpoint CP-00 --candidate-source-commit <sha> \\
        --candidate-manifest <path to the promoted MANIFEST.sha256> --launcher-toolchain <rustc identity> \\
        [--schema-set-version v1] [--contract-policy-version 1] [--built-at <ISO UTC>]

Pinned glue DevForge runs during the build, after copying the candidate
manifest to <root>/contracts/MANIFEST.sha256 and before gen_release_manifest.py.
The candidate manifest digest is computed from the file named, never typed.
The document never contains the digest of RELEASE.sha256 (that file lists
this one). Validates its own output against the release-identity schema found
in <root>/schemas/devforgeai/v1/ when present.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="gen_release_identity.py", allow_abbrev=False)
    parser.add_argument("--root", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--devforge-commit", required=True)
    parser.add_argument("--devforge-tag", required=True)
    parser.add_argument("--candidate-repository", required=True)
    parser.add_argument("--candidate-checkpoint", required=True, help="checkpoint id the candidate belongs to, e.g. CP-00")
    parser.add_argument("--candidate-source-commit", required=True)
    parser.add_argument("--candidate-manifest", required=True)
    parser.add_argument("--launcher-toolchain", required=True)
    parser.add_argument("--schema-set-version", default="v1")
    parser.add_argument("--contract-policy-version", default="1")
    parser.add_argument("--built-at", default=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    args = parser.parse_args(argv)

    root = Path(args.root)
    if not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 2
    manifest = Path(args.candidate_manifest)
    if not manifest.is_file():
        print(f"candidate manifest not found: {manifest}", file=sys.stderr)
        return 2
    document = {
        "identity_format": "devforge-release-identity/v1",
        "version": args.version,
        "devforge_commit": args.devforge_commit,
        "devforge_tag": args.devforge_tag,
        "candidate_repository": args.candidate_repository,
        "candidate_checkpoint_id": args.candidate_checkpoint,
        "candidate_source_commit": args.candidate_source_commit,
        "candidate_manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
        "schema_set_version": args.schema_set_version,
        "contract_policy_version": args.contract_policy_version,
        "launcher_toolchain": args.launcher_toolchain,
        "built_at": args.built_at,
    }
    schema_path = root / "schemas" / "devforgeai" / "v1" / "release-identity.schema.json"
    if schema_path.is_file():
        try:
            import jsonschema
        except ImportError:
            jsonschema = None
        if jsonschema is not None:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            errors = list(jsonschema.Draft202012Validator(schema).iter_errors(document))
            if errors:
                for error in errors:
                    print(f"identity invalid: {'/'.join(str(p) for p in error.path) or '<root>'}: {error.message}",
                          file=sys.stderr)
                return 1
    text = json.dumps(document, indent=2) + "\n"
    (root / "RELEASE-IDENTITY.json").write_text(text, encoding="utf-8")
    print(f"RELEASE-IDENTITY.json written: sha256 {hashlib.sha256(text.encode('utf-8')).hexdigest()}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
