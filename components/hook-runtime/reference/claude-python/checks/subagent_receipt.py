"""SubagentStop: agents listed in policy `receipt_agents` must end with exactly
one JSON object carrying `schema` and `status`. Otherwise exit 2 keeps the
subagent working and the reason tells it what to return.

`last_assistant_message` is the documented field for the final text; the
receipt body is written to .claude/hooks/receipts/<agent_id>.json and never
logged.
"""
from __future__ import annotations

import json
from pathlib import Path

from checks.base import Check, Decision, Event


class SubagentReceipt(Check):
    name = "subagent_receipt"
    events = ("SubagentStop",)
    order = 50
    critical = True

    def run(self, ev: Event) -> Decision:
        required = set(self.policy.get("receipt_agents", []))
        if ev.agent_type not in required:
            return Decision.none()
        text = ev.last_assistant_message.strip()
        if text.startswith("```"):
            text = text.strip("`").split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        try:
            receipt = json.loads(text)
        except json.JSONDecodeError:
            return Decision.deny(
                "final message must be exactly one JSON receipt object with "
                "`schema` and `status`; no prose, no fence")
        if not isinstance(receipt, dict) or "schema" not in receipt or "status" not in receipt:
            return Decision.deny("receipt lacks `schema` or `status`")
        out = Path(ev.project_dir) / ".claude" / "hooks" / "receipts"
        out.mkdir(parents=True, exist_ok=True)
        (out / f"{ev.agent_id or 'unknown'}.json").write_text(json.dumps(receipt, indent=1))
        return Decision.none()
