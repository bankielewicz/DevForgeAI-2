"""PreToolUse on Bash: deny commands matching the policy's regex list, ask for
the ones in `ask_commands`.

Matching is per command segment, not over the whole text. The command is
split into segments at `;`, `&&`, `||`, `|` and newlines after heredoc
bodies are removed, and every pattern is anchored at the start of a segment
(leading env assignments and `sudo`/`time`/`nice`/`env` prefixes skipped). So
a heredoc or an `echo` that merely mentions a denied command does not trip the
guard, while `cd x && <denied command>` still does. Interpreter escapes such
as `bash -c "..."` and `eval` cannot be seen through; list them in
`ask_commands`.
"""
from __future__ import annotations

import re

from checks.base import Check, Decision, Event

_HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1[^\n]*\n(?:.*?\n)*?\s*\2\s*(?=\n|$)", re.S)
_SPLIT = re.compile(r"\s*(?:\|\||&&|;|\||\n)\s*")
_PREFIX = re.compile(
    r"^(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*"
    r"(?:(?:sudo|time|nice|env|command|exec)\s+(?:-\S+\s+)*)*"
)


def segments(command: str) -> list[str]:
    body = _HEREDOC.sub("", command)
    out = []
    for seg in _SPLIT.split(body):
        seg = seg.strip()
        if not seg:
            continue
        seg = seg.lstrip("({ ").strip()
        out.append(_PREFIX.sub("", seg))
    return out


class BashGuard(Check):
    name = "bash_guard"
    events = ("PreToolUse",)
    tool_matcher = r"^Bash$"
    order = 30
    critical = True

    def run(self, ev: Event) -> Decision:
        segs = segments(ev.command or "")
        for pat in self.policy.get("denied_commands", []):
            rx = re.compile(r"^(?:" + pat + r")")
            for seg in segs:
                if rx.search(seg):
                    # the reason names the pattern, never the command text:
                    # reasons are logged and shown in the transcript
                    return Decision.deny(f"a command segment matches denied pattern {pat!r}")
        for pat in self.policy.get("ask_commands", []):
            rx = re.compile(r"^(?:" + pat + r")")
            for seg in segs:
                if rx.search(seg):
                    return Decision.ask(f"a command segment matches ask pattern {pat!r}")
        return Decision.none()
