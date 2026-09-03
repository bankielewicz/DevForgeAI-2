"""Strict Codex event accessors and deliberately bounded parsers."""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping


SUPPORTED_EVENTS = frozenset(
    {"SessionStart", "PreToolUse", "PostToolUse", "SubagentStop"}
)


class ProtocolError(ValueError):
    pass


@dataclass(frozen=True)
class HookEvent:
    raw: Mapping[str, Any]

    @classmethod
    def parse(cls, value: Any) -> "HookEvent":
        if not isinstance(value, dict):
            raise ProtocolError("hook input must be one JSON object")
        event_name = value.get("hook_event_name")
        if not isinstance(event_name, str) or not event_name:
            raise ProtocolError("hook_event_name must be a non-empty string")
        if event_name not in SUPPORTED_EVENTS:
            raise ProtocolError("hook_event_name is not supported by this dispatcher")
        if "cwd" in value and not isinstance(value["cwd"], str):
            raise ProtocolError("cwd must be a string")
        if event_name in {"PreToolUse", "PostToolUse"}:
            if not isinstance(value.get("tool_name"), str) or not value["tool_name"]:
                raise ProtocolError("tool_name must be a non-empty string")
            if value["tool_name"] in {"Bash", "apply_patch"}:
                if not isinstance(value.get("tool_input"), dict):
                    raise ProtocolError("Bash and apply_patch tool_input must be an object")
                if not isinstance(value["tool_input"].get("command"), str):
                    raise ProtocolError("tool_input.command must be a string")
        if event_name == "SubagentStop":
            for key in ("agent_id", "agent_type"):
                if not isinstance(value.get(key), str) or not value[key]:
                    raise ProtocolError(f"{key} must be a string")
            if value.get("last_assistant_message") is not None and not isinstance(
                value.get("last_assistant_message"), str
            ):
                raise ProtocolError("last_assistant_message must be a string or null")
            if not isinstance(value.get("stop_hook_active"), bool):
                raise ProtocolError("stop_hook_active must be boolean")
        return cls(value)

    @property
    def name(self) -> str:
        return str(self.raw["hook_event_name"])

    @property
    def tool_name(self) -> str:
        value = self.raw.get("tool_name", "")
        return value if isinstance(value, str) else ""

    @property
    def tool_input(self) -> Mapping[str, Any]:
        value = self.raw.get("tool_input", {})
        return value if isinstance(value, dict) else {}

    @property
    def command(self) -> str:
        value = self.tool_input.get("command", "")
        return value if isinstance(value, str) else ""

    @property
    def agent_id(self) -> str:
        value = self.raw.get("agent_id", "")
        return value if isinstance(value, str) else ""

    @property
    def agent_type(self) -> str:
        value = self.raw.get("agent_type", "")
        return value if isinstance(value, str) else ""

    @property
    def last_assistant_message(self) -> str:
        value = self.raw.get("last_assistant_message", "")
        return value if isinstance(value, str) else ""

    @property
    def stop_hook_active(self) -> bool:
        return self.raw.get("stop_hook_active") is True

    def safe_identifier(self, key: str, limit: int = 128) -> str:
        value = self.raw.get(key, "")
        if not isinstance(value, str):
            return ""
        return re.sub(r"[^A-Za-z0-9_.:-]", "_", value)[:limit]


_PATCH_TARGET = re.compile(r"^\*\*\* (Add|Update|Delete) File: (.+)$")
_PATCH_MOVE = re.compile(r"^\*\*\* Move to: (.+)$")


def parse_apply_patch_paths(patch: str) -> tuple[str, ...]:
    """Extract every declared path or reject an incomplete patch envelope."""

    if not isinstance(patch, str) or not patch.strip():
        raise ProtocolError("apply_patch command is empty")
    lines = patch.splitlines()
    nonempty = [line for line in lines if line.strip()]
    if not nonempty or nonempty[0] != "*** Begin Patch" or nonempty[-1] != "*** End Patch":
        raise ProtocolError("apply_patch envelope is malformed")
    if sum(line == "*** Begin Patch" for line in lines) != 1:
        raise ProtocolError("apply_patch contains multiple begin markers")
    if sum(line == "*** End Patch" for line in lines) != 1:
        raise ProtocolError("apply_patch contains multiple end markers")

    paths: list[str] = []
    current_operation = ""
    for line in lines[1:-1]:
        target = _PATCH_TARGET.match(line)
        if target:
            current_operation = target.group(1)
            paths.append(target.group(2))
            continue
        move = _PATCH_MOVE.match(line)
        if move:
            if current_operation != "Update":
                raise ProtocolError("Move to must follow an Update File declaration")
            paths.append(move.group(1))
            continue
        if line == "*** End of File":
            continue
        if line.startswith("*** "):
            raise ProtocolError("unrecognized apply_patch control line")
    if not paths:
        raise ProtocolError("apply_patch declares no file paths")
    return tuple(paths)


def resolve_project_path(project_root: Path, raw_path: str) -> tuple[Path, str]:
    """Resolve a POSIX project-relative path and reject syntactic or symlink escape."""

    if not isinstance(raw_path, str) or not raw_path or "\x00" in raw_path:
        raise ProtocolError("path is empty or contains NUL")
    if "\\" in raw_path:
        raise ProtocolError("backslash paths are ambiguous and are not accepted")
    pure = PurePosixPath(raw_path)
    if pure.is_absolute() or any(part == ".." for part in pure.parts):
        raise ProtocolError("path must remain project-relative")
    if raw_path.endswith("/") or pure.name in {"", ".", ".."}:
        raise ProtocolError("path must name a file")

    root = project_root.resolve(strict=True)
    resolved = (root / Path(*pure.parts)).resolve(strict=False)
    try:
        relative = resolved.relative_to(root).as_posix()
    except ValueError as exc:
        raise ProtocolError("path resolves outside the project root") from exc
    if relative in {"", "."}:
        raise ProtocolError("path must not be the project root")
    return resolved, relative


def path_matches(relative: str, patterns: Iterable[str]) -> str | None:
    for pattern in patterns:
        if not isinstance(pattern, str) or not pattern:
            continue
        if pattern.endswith("/**"):
            base = pattern[:-3].rstrip("/")
            if relative == base or relative.startswith(base + "/"):
                return pattern
        elif relative == pattern:
            return pattern
    return None


_COMMENT_BOUNDARY_OPERATORS = frozenset(";|&<>()")


def _starts_shell_comment(text: str, index: int) -> bool:
    """Return whether an unquoted # begins a shell comment at this position."""

    return text[index] == "#" and (
        index == 0
        or text[index - 1].isspace()
        or text[index - 1] in _COMMENT_BOUNDARY_OPERATORS
    )


def _heredoc_delimiters(line: str) -> tuple[tuple[str, bool], ...]:
    """Read heredoc declarations only outside quotes and shell comments."""

    found: list[tuple[str, bool]] = []
    quote = ""
    escaped = False
    index = 0
    while index < len(line):
        char = line[index]
        if escaped:
            escaped = False
            index += 1
            continue
        if char == "\\" and quote != "'":
            escaped = True
            index += 1
            continue
        if quote:
            if char == quote:
                quote = ""
            index += 1
            continue
        if char in {"'", '"'}:
            quote = char
            index += 1
            continue
        if _starts_shell_comment(line, index):
            break
        if line.startswith("<<", index):
            cursor = index + 2
            if cursor < len(line) and line[cursor] == "-":
                cursor += 1
            while cursor < len(line) and line[cursor].isspace():
                cursor += 1
            delimiter_quote = line[cursor] if cursor < len(line) and line[cursor] in {"'", '"'} else ""
            if delimiter_quote:
                cursor += 1
            start = cursor
            while cursor < len(line) and (line[cursor].isalnum() or line[cursor] == "_"):
                cursor += 1
            delimiter = line[start:cursor]
            if not delimiter or not (delimiter[0].isalpha() or delimiter[0] == "_"):
                raise ProtocolError("unsupported or malformed heredoc declaration")
            if delimiter_quote:
                if cursor >= len(line) or line[cursor] != delimiter_quote:
                    raise ProtocolError("unterminated heredoc delimiter quote")
                cursor += 1
            else:
                # Unquoted heredoc bodies perform shell expansion. This small
                # guard cannot safely reason about their hidden substitutions.
                raise ProtocolError("unquoted heredocs are not accepted by command policy")
            found.append((delimiter, line.startswith("<<-", index)))
            index = cursor
            continue
        index += 1
    return tuple(found)


def strip_heredoc_bodies(command: str) -> str:
    """Keep command headers but discard bodies of lexically valid quoted heredocs."""

    output: list[str] = []
    pending: list[tuple[str, bool]] = []
    for line in command.splitlines():
        if pending:
            delimiter, strip_tabs = pending[0]
            candidate = line.lstrip("\t") if strip_tabs else line
            if candidate == delimiter:
                pending.pop(0)
            continue
        output.append(line)
        pending.extend(_heredoc_delimiters(line))
    if pending:
        raise ProtocolError("heredoc body is missing its delimiter")
    return "\n".join(output)


def _reject_nested_shell_syntax(text: str) -> None:
    """Reject constructs that can hide a second command from this bounded parser."""

    quote = ""
    escaped = False
    index = 0
    while index < len(text):
        char = text[index]
        if escaped:
            escaped = False
            index += 1
            continue
        if char == "\\" and quote != "'":
            if index + 1 < len(text) and text[index + 1] == "\n":
                raise ProtocolError("shell line continuations are not accepted")
            escaped = True
            index += 1
            continue
        if quote == "'":
            if char == "'":
                quote = ""
            index += 1
            continue
        if quote == '"':
            if char == '"':
                quote = ""
                index += 1
                continue
            if char == "`" or text.startswith("$(", index):
                raise ProtocolError("nested shell substitution is not accepted")
            index += 1
            continue
        if char in {"'", '"'}:
            quote = char
            index += 1
            continue
        if _starts_shell_comment(text, index):
            newline = text.find("\n", index)
            if newline < 0:
                return
            index = newline + 1
            continue
        if char == "`" or text.startswith("$(", index) or text.startswith("<(", index) or text.startswith(">(", index):
            raise ProtocolError("nested shell substitution is not accepted")
        if char in {"(", ")", "{", "}"}:
            raise ProtocolError("shell grouping or function syntax is not accepted")
        index += 1


def shell_segments(command: str) -> tuple[str, ...]:
    """Split top-level command positions; this is a guardrail, not a shell parser."""

    text = strip_heredoc_bodies(command)
    _reject_nested_shell_syntax(text)
    segments: list[str] = []
    current: list[str] = []
    quote = ""
    escaped = False
    index = 0
    while index < len(text):
        char = text[index]
        if escaped:
            current.append(char)
            escaped = False
            index += 1
            continue
        if char == "\\" and quote != "'":
            current.append(char)
            escaped = True
            index += 1
            continue
        if quote:
            current.append(char)
            if char == quote:
                quote = ""
            index += 1
            continue
        if char in {"'", '"'}:
            quote = char
            current.append(char)
            index += 1
            continue
        if _starts_shell_comment(text, index):
            newline = text.find("\n", index)
            index = len(text) if newline < 0 else newline
            continue
        if char in {";", "\n", "|", "&"}:
            if char == "&" and (
                (index > 0 and text[index - 1] in {">", "<"})
                or (index + 1 < len(text) and text[index + 1] == ">")
            ):
                current.append(char)
                index += 1
                continue
            candidate = "".join(current).strip()
            if candidate:
                segments.append(candidate)
            current = []
            if index + 1 < len(text) and text[index + 1] == char:
                index += 1
            index += 1
            continue
        current.append(char)
        index += 1
    candidate = "".join(current).strip()
    if candidate:
        segments.append(candidate)
    return tuple(segments)


_ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\+)?=.*$", re.DOTALL)
_CONTROL_PREFIXES = frozenset(
    {"!", "if", "elif", "else", "while", "until", "then", "do"}
)
_REJECTED_PREFIXES = frozenset({"coproc"})
_TRANSPARENT_WRAPPERS = frozenset(
    {"builtin", "command", "sudo", "doas", "exec", "nohup", "time"}
)
_SHELL_REDIRECT = re.compile(
    r"^(?:\d*(?:<<<|<<|<>|<&|>>|>\||>|<|>&)|&>>?)(.*)$"
)


def _without_shell_redirections(tokens: list[str]) -> list[str] | None:
    """Remove redirection operators/operands so they cannot hide argv position."""

    result: list[str] = []
    index = 0
    while index < len(tokens):
        match = _SHELL_REDIRECT.fullmatch(tokens[index])
        if match is None:
            result.append(tokens[index])
            index += 1
            continue
        if match.group(1):
            index += 1
            continue
        if index + 1 >= len(tokens):
            return None
        index += 2
    return result


def normalized_command_position(segment: str) -> str:
    """Return a normalized command and arguments for anchored rule matching."""

    try:
        tokens = shlex.split(segment, posix=True)
    except ValueError:
        return ""
    stripped = _without_shell_redirections(tokens)
    if stripped is None:
        return ""
    tokens = stripped
    # This is deliberately a small prefix grammar. Ambiguous wrapper options
    # fail closed instead of guessing their operand arity and skipping the real
    # command. Iterate because controls and wrappers can be interleaved.
    while tokens:
        if _ASSIGNMENT.match(tokens[0]):
            tokens.pop(0)
            continue
        if "=" in tokens[0]:
            # Bash accepts assignment forms beyond this POC's scalar grammar
            # (for example array subscripts). Do not mistake one for argv[0].
            return ""
        if tokens[0] in _REJECTED_PREFIXES:
            return ""
        if tokens[0] in _CONTROL_PREFIXES:
            tokens.pop(0)
            continue
        if tokens[0] == "env":
            tokens.pop(0)
            if tokens and tokens[0].startswith("-"):
                return ""
            continue
        if tokens[0] in _TRANSPARENT_WRAPPERS:
            tokens.pop(0)
            if tokens and tokens[0].startswith("-"):
                return ""
            continue
        break
    return " ".join(tokens)


_SEPARATE_WRITE_REDIRECT = re.compile(r"^(?:\d*(?:>|>>|>\|)|&>|&>>|>&|<>)$")
_LEGACY_BOTH_REDIRECT = re.compile(r"^>&(.+)$")
_BOTH_REDIRECT = re.compile(r"^&>>?(.+)$")
_WRITE_REDIRECT = re.compile(r"^\d*(?:>>?|>\||<>)(.+)$")
_FD_DUPLICATION = re.compile(r"^\d+>&(?:\d+|-)$")


def _literal_redirect_target(value: str) -> str:
    if not value:
        raise ProtocolError("redirection has no target")
    if any(character in value for character in "$`~*?[]{}()"):
        raise ProtocolError("expanded or globbed redirection targets are not accepted")
    if value.startswith("&"):
        raise ProtocolError("ambiguous file-descriptor redirection is not accepted")
    return value


def redirect_targets(command: str) -> tuple[str, ...]:
    """Extract simple shell redirection targets for early feedback only."""

    targets: list[str] = []
    for segment in shell_segments(command):
        try:
            tokens = shlex.split(segment, posix=True)
        except ValueError as exc:
            raise ProtocolError("shell quoting is malformed") from exc
        index = 0
        while index < len(tokens):
            token = tokens[index]
            if _SEPARATE_WRITE_REDIRECT.fullmatch(token):
                if index + 1 >= len(tokens):
                    raise ProtocolError("redirection has no target")
                target = tokens[index + 1]
                if token.endswith(">&") and target in {"-"} | {
                    str(number) for number in range(10)
                }:
                    index += 2
                    continue
                targets.append(_literal_redirect_target(target))
                index += 2
                continue
            if _FD_DUPLICATION.fullmatch(token):
                index += 1
                continue
            legacy = _LEGACY_BOTH_REDIRECT.match(token)
            if legacy:
                target = legacy.group(1)
                if target not in {"-"} and not target.isdigit():
                    targets.append(_literal_redirect_target(target))
                index += 1
                continue
            match = _BOTH_REDIRECT.match(token) or _WRITE_REDIRECT.match(token)
            if match:
                targets.append(_literal_redirect_target(match.group(1)))
            index += 1
    return tuple(targets)
