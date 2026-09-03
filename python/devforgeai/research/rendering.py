"""Deterministic human-readable renderings for canonical Research records.

The renderer in this module is intentionally presentation-only.  It does not
add publication, registry, manifest, receipt, or readback facts to the
pre-seal handoff it is given.
"""

from __future__ import annotations

import html
import json
import re
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Final


_POST_SEAL_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "manifest_sha256",
        "published_at_utc",
        "published_path",
        "readback",
        "receipt",
        "registry",
        "registry_entry_sha256",
        "registry_head_sha256",
        "registry_sequence",
        "seal_receipt",
    }
)


def _plain(value: Any) -> str:
    """Return a stable textual representation without losing JSON types."""

    if isinstance(value, str):
        return value
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _cell(value: Any) -> str:
    """Escape a value for one GitHub-flavored Markdown table cell."""

    rendered = _plain(value).replace("\r\n", "\n").replace("\r", "\n")
    # Escape HTML before introducing the intentional <br> line separators.
    rendered = html.escape(rendered, quote=False)
    rendered = rendered.replace("\\", "\\\\")
    rendered = rendered.replace("|", "\\|")
    rendered = rendered.replace("`", "\\`")
    return rendered.replace("\n", "<br>")


def _table(headers: Sequence[str], rows: Iterable[Sequence[Any]]) -> str:
    """Render a deterministic table, explicitly representing an empty list."""

    materialized = [tuple(row) for row in rows]
    if not materialized:
        materialized = [("[]", *("" for _ in headers[1:]))]
    lines = [
        "| " + " | ".join(_cell(header) for header in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in materialized:
        if len(row) != len(headers):
            raise ValueError("Markdown table row width does not match its header")
        lines.append("| " + " | ".join(_cell(value) for value in row) + " |")
    return "\n".join(lines)


def _mapping_rows(value: Mapping[str, Any]) -> list[tuple[str, Any]]:
    """Return mapping rows in key order so insertion order cannot affect output."""

    return [(key, value[key]) for key in sorted(value)]


def _list_rows(values: Sequence[Any]) -> list[tuple[Any]]:
    return [(value,) for value in values]


def _section(title: str, body: str) -> str:
    return f"## {title}\n\n{body}"


def _exact_code_block(value: str) -> str:
    """Wrap exact text in a fence that cannot be closed by the text itself."""

    longest_tilde_run = max(
        (len(match.group(0)) for match in re.finditer(r"~+", value)), default=0
    )
    fence = "~" * max(3, longest_tilde_run + 1)
    final_newline = "" if value.endswith("\n") else "\n"
    return f"{fence}text\n{value}{final_newline}{fence}"


def render_handoff_markdown(handoff: Mapping[str, Any]) -> str:
    """Render a canonical ``research-handoff/v1`` object as stable Markdown.

    The caller remains responsible for schema validation.  Known post-seal
    closure fields are rejected because they are never part of canonical
    ``handoff.md``.  Lists retain their canonical order; mappings are sorted by
    key wherever their schema does not assign an order.
    """

    if not isinstance(handoff, Mapping):
        raise TypeError("handoff must be a mapping")

    forbidden = sorted(_POST_SEAL_FIELDS.intersection(handoff))
    if forbidden:
        raise ValueError(
            "post-seal fields are not renderable in canonical handoff Markdown: "
            + ", ".join(forbidden)
        )

    location = handoff["location"]
    result = handoff["result"]
    claims = handoff["claims"]
    sources = handoff["sources"]
    contrary = handoff["contrary_evidence"]
    budget = handoff["budget"]
    validation = handoff["validation"]
    custody = handoff["custody"]
    next_action = handoff["next_action"]
    repair_route = handoff["repair_route"]

    sections: list[str] = [
        "# Research handoff",
        f"> **{_cell(location['marker'])}**",
        _section(
            "Location and result",
            _table(
                ("Field", "Value"),
                [
                    ("Project", location["project_id"]),
                    ("Slug", location["slug"]),
                    ("Run", location["run_id"]),
                    ("Workflow", location["workflow"]),
                    ("Phase", location["phase"]),
                    ("Subphase", location["subphase"]),
                    ("Outcome", result["outcome"]),
                    ("Reason code", result["reason_code"]),
                    ("Explanation", result["explanation"]),
                ],
            ),
        ),
        _section(
            "Record identity and provenance",
            _table(
                ("Field", "Value"),
                [
                    ("Schema version", handoff["schema_version"]),
                    ("Record ID", handoff["record_id"]),
                    ("Record version", handoff["record_version"]),
                    ("Handoff ID", handoff["handoff_id"]),
                    ("Run ID", handoff["run_id"]),
                    ("Lifecycle status", handoff["lifecycle_status"]),
                    ("Readiness status", handoff["readiness_status"]),
                    ("Owner", handoff["owner"]),
                    ("Decision authority", handoff["decision_authority"]),
                    ("Created at UTC", handoff["created_at_utc"]),
                    ("Rendered at", handoff["rendered_at"]),
                    ("Source refs", handoff["source_refs"]),
                    ("Evidence refs", handoff["evidence_refs"]),
                    ("Decision refs", handoff["decision_refs"]),
                    ("Supersedes", handoff["supersedes"]),
                    ("Stale if", handoff["stale_if"]),
                ],
            ),
        ),
        _section(
            "Questions",
            _table(
                ("Question ID", "Disposition", "Reason"),
                [
                    (
                        question["question_id"],
                        question["disposition"],
                        question.get("reason", None),
                    )
                    for question in handoff["questions"]
                ],
            ),
        ),
        _section(
            "Claims",
            _table(
                ("Measure", "Value"),
                [
                    ("Total", claims["total"]),
                    *[
                        (f"Class: {key}", value)
                        for key, value in _mapping_rows(claims["by_class"])
                    ],
                    *[
                        (f"Readiness: {key}", value)
                        for key, value in _mapping_rows(claims["by_readiness"])
                    ],
                    *[
                        (f"Dispute: {key}", value)
                        for key, value in _mapping_rows(claims["by_dispute"])
                    ],
                    *[
                        (f"Verification: {key}", value)
                        for key, value in _mapping_rows(claims["by_verification"])
                    ],
                ],
            )
            + "\n\n### Material claims\n\n"
            + _table(
                ("Claim ID", "Limitations"),
                [
                    (claim["claim_id"], claim["limitations"])
                    for claim in claims["material_claims"]
                ],
            ),
        ),
        _section(
            "Sources",
            _table(
                ("Measure", "Value"),
                [
                    ("Total", sources["total"]),
                    *[
                        (f"Admission: {key}", value)
                        for key, value in _mapping_rows(sources["by_admission"])
                    ],
                    *[
                        (f"Retrieval: {key}", value)
                        for key, value in _mapping_rows(sources["by_retrieval"])
                    ],
                    *[
                        (f"Custody: {key}", value)
                        for key, value in _mapping_rows(sources["by_custody"])
                    ],
                    *[
                        (f"Freshness: {key}", value)
                        for key, value in _mapping_rows(sources["by_freshness"])
                    ],
                ],
            ),
        ),
        _section(
            "Contrary evidence",
            _table(
                ("Measure", "Value"),
                [
                    ("Open", contrary["open_count"]),
                    ("Resolved", contrary["resolved_count"]),
                ],
            )
            + "\n\n### Contradictions\n\n"
            + _table(
                ("Contradiction ID", "Status", "Scope"),
                [
                    (
                        contradiction["contradiction_id"],
                        contradiction["status"],
                        contradiction["scope"],
                    )
                    for contradiction in contrary["contradictions"]
                ],
            )
            + "\n\n### Uncovered scope\n\n"
            + _table(("Scope",), _list_rows(contrary["uncovered_scope"])),
        ),
        _section(
            "Exclusions",
            _table(("Excluded scope",), _list_rows(handoff["exclusions"])),
        ),
        _section(
            "Budget",
            _table(
                ("Confirmed field", "Value"),
                [
                    ("Profile", budget["confirmed"]["profile"]),
                    *[
                        (f"Limit: {key}", value)
                        for key, value in _mapping_rows(
                            budget["confirmed"]["limits"]
                        )
                    ],
                ],
            )
            + "\n\n### Authorized overrides\n\n"
            + _table(
                ("Field", "Value", "Authority"),
                [
                    (override["field"], override["value"], override["authority_id"])
                    for override in budget["confirmed"]["overrides"]
                ],
            )
            + "\n\n### Actual use\n\n"
            + _table(
                ("Actual field", "Value"),
                _mapping_rows(budget["actual"]),
            ),
        ),
        _section(
            "Canonical artifacts",
            _table(
                (
                    "Artifact ID",
                    "Version",
                    "Path",
                    "Lifecycle",
                    "Readiness",
                    "Verification",
                    "Owner",
                    "SHA-256",
                    "Bytes",
                ),
                [
                    (
                        artifact["artifact_id"],
                        artifact["version"],
                        artifact["path"],
                        artifact["lifecycle_status"],
                        artifact["readiness_status"],
                        artifact["verification_status"],
                        artifact["owner"],
                        artifact["sha256"],
                        artifact.get("byte_length", None),
                    )
                    for artifact in handoff["canonical_artifacts"]
                ],
            ),
        ),
        _section(
            "Source basis",
            _table(
                ("Artifact ID", "Version", "SHA-256"),
                [
                    (basis["artifact_id"], basis["version"], basis["sha256"])
                    for basis in handoff["source_basis"]
                ],
            ),
        ),
        _section(
            "Validation",
            "### Environment\n\n"
            + _table(("Field", "Value"), _mapping_rows(validation["environment"]))
            + "\n\n### Checks\n\n"
            + _table(
                ("Check", "Status", "Evidence IDs", "Reason"),
                [
                    (
                        check["check"],
                        check["status"],
                        check["evidence_ids"],
                        check.get("reason", None),
                    )
                    for check in validation["checks"]
                ],
            )
            + "\n\n### Checks not run\n\n"
            + _table(
                ("Check", "Reason", "Impact"),
                [
                    (
                        check["check"],
                        check["reason"],
                        check.get("impact", None),
                    )
                    for check in validation["checks_not_run"]
                ],
            ),
        ),
        _section(
            "Decisions",
            _table(("Decision ID",), _list_rows(handoff["decisions"])),
        ),
        _section(
            "Custody",
            _table(("Mode", "Count"), _mapping_rows(custody["by_mode"]))
            + "\n\n### Unavailable requirements\n\n"
            + _table(
                ("Requirement", "Reason", "Owner"),
                [
                    (
                        requirement["requirement"],
                        requirement["reason"],
                        requirement["owner"],
                    )
                    for requirement in custody["unavailable_requirements"]
                ],
            ),
        ),
        _section(
            "Conclusion",
            _table(
                ("Field", "Value"),
                [("Conclusion status", handoff["conclusion_status"])],
            ),
        ),
        _section(
            "Open items",
            _table(
                ("Item", "Owner"),
                [(item["item"], item["owner"]) for item in handoff["open_items"]],
            ),
        ),
        _section(
            "Next action",
            f"1. **Provider:** {_cell(next_action['provider'])}\n\n"
            + _exact_code_block(next_action["invocation"]),
        ),
        _section("Session guidance", _table(("Guidance",), [(handoff["session_guidance"],)])),
        _section(
            "Authority and fence",
            _table(("Authority", "Actor"), _mapping_rows(handoff["authorities"]))
            + "\n\n"
            + _table(("Fence",), [(handoff["authority_fence"],)]),
        ),
        _section(
            "Repair route",
            _table(
                ("Owner", "Invocation"),
                [(repair_route["owner"], repair_route["invocation"])],
            ),
        ),
    ]

    return "\n\n".join(sections) + "\n"


__all__ = ["render_handoff_markdown"]
