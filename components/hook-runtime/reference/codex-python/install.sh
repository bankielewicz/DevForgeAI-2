#!/usr/bin/env bash
# Install the Codex hookd POC into one project without changing trust, Git
# ignores, or unrelated hook definitions. Run from the project root, or pass
# --project-root. The embedded Python uses only the standard library.
set -euo pipefail

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 - "$SOURCE_DIR" "$@" <<'PY'
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import shlex
import stat
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path, PurePosixPath
from typing import Any


if sys.version_info < (3, 11):
    print("install: Python 3.11 or newer is required", file=sys.stderr)
    raise SystemExit(2)


EVENTS = ("SessionStart", "PreToolUse", "PostToolUse", "SubagentStop")
MAX_POLICY_BYTES = 1_048_576
POLICY_KEYS = frozenset(
    {
        "schema",
        "mode",
        "protected_paths",
        "deny_outside_project",
        "allowed_external_redirects",
        "denied_commands",
        "receipt_agents",
        "receipt_schema",
        "receipt_statuses",
        "max_receipt_bytes",
        "max_context_chars",
        "check_config",
    }
)
RECEIPT_STATUSES = frozenset({"pass", "fail", "needs_user", "could_not_run"})
SAFE_ID = re.compile(r"^[A-Z][A-Z0-9_]{1,63}$")
SAFE_AGENT = re.compile(r"^[A-Za-z0-9_.:-]{1,128}$")


class InstallError(RuntimeError):
    pass


def object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise InstallError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def reject_nonfinite(value: str) -> None:
    raise InstallError(f"non-finite JSON number is not accepted: {value}")


def validate_json_bounds(value: Any, *, max_depth: int = 32, max_nodes: int = 10_000) -> None:
    stack: list[tuple[Any, int]] = [(value, 0)]
    nodes = 0
    while stack:
        item, depth = stack.pop()
        nodes += 1
        if nodes > max_nodes or depth > max_depth:
            raise InstallError("policy JSON exceeds structural bounds")
        if isinstance(item, dict):
            stack.extend((nested, depth + 1) for nested in item.values())
        elif isinstance(item, list):
            stack.extend((nested, depth + 1) for nested in item)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="install.sh",
        description="Install or verify the DevForgeAI Codex hook dispatcher POC."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run", action="store_true", help="show changes without writing them"
    )
    mode.add_argument(
        "--check",
        action="store_true",
        help="exit 0 only when the managed installation is current",
    )
    parser.add_argument(
        "--enable-denies",
        action="store_true",
        help="set the installed policy mode to enforce; the default is observe",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="target project root (default: current directory)",
    )
    return parser.parse_args(argv)


def load_json(path: Path, label: str, *, max_bytes: int | None = None) -> Any:
    if path.is_symlink():
        raise InstallError(f"{label} must not be a symlink: {path}")
    try:
        if max_bytes is not None and path.stat().st_size > max_bytes:
            raise InstallError(f"{label} exceeds {max_bytes} bytes: {path}")
        text = path.read_text(encoding="utf-8")
        value = json.loads(
            text,
            object_pairs_hook=object_without_duplicates,
            parse_constant=reject_nonfinite,
        )
    except FileNotFoundError as exc:
        raise InstallError(f"{label} is missing: {path}") from exc
    except RecursionError as exc:
        raise InstallError(f"{label} exceeds the JSON nesting limit: {path}") from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise InstallError(f"{label} is unreadable or invalid JSON: {path}: {exc}") from exc
    return value


def string_array(
    policy: dict[str, Any], key: str, *, maximum: int, pattern: re.Pattern[str] | None = None
) -> list[str]:
    value = policy.get(key)
    if not isinstance(value, list) or len(value) > maximum:
        raise InstallError(f"policy.{key} must be an array of at most {maximum} strings")
    if any(not isinstance(item, str) or not item or len(item) > 512 for item in value):
        raise InstallError(f"policy.{key} contains an invalid string")
    if len(set(value)) != len(value):
        raise InstallError(f"policy.{key} contains a duplicate")
    if pattern is not None and any(pattern.fullmatch(item) is None for item in value):
        raise InstallError(f"policy.{key} contains a value with an invalid identifier shape")
    return value


def validate_policy(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise InstallError("policy must be one JSON object")
    validate_json_bounds(value)
    keys = frozenset(value)
    if keys != POLICY_KEYS:
        missing = sorted(POLICY_KEYS - keys)
        unknown = sorted(keys - POLICY_KEYS)
        detail = []
        if missing:
            detail.append("missing=" + ",".join(missing))
        if unknown:
            detail.append("unknown=" + ",".join(unknown))
        raise InstallError("policy keys do not match v1: " + "; ".join(detail))
    if value["schema"] != "devforgeai.hookd-policy/v1":
        raise InstallError("policy.schema must be devforgeai.hookd-policy/v1")
    if value["mode"] not in {"observe", "enforce"}:
        raise InstallError("policy.mode must be observe or enforce")
    protected = string_array(value, "protected_paths", maximum=256)
    if not protected:
        raise InstallError("policy.protected_paths must not be empty")
    for path in protected:
        base = path[:-3] if path.endswith("/**") else path
        pure = PurePosixPath(base)
        if (
            pure.is_absolute()
            or not base
            or pure.as_posix() != base
            or any(part in {"", ".", ".."} for part in pure.parts)
        ):
            raise InstallError(f"policy.protected_paths is not project-relative: {path}")
        if (
            any(marker in base for marker in "*?[\\")
            or any(ord(character) < 32 for character in base)
        ):
            raise InstallError(
                f"policy.protected_paths supports exact paths and trailing /** only: {path}"
            )
    if type(value["deny_outside_project"]) is not bool:
        raise InstallError("policy.deny_outside_project must be boolean")
    redirects = string_array(value, "allowed_external_redirects", maximum=64)
    for path in redirects:
        pure = PurePosixPath(path)
        if (
            path == "/"
            or not pure.is_absolute()
            or pure.anchor != "/"
            or pure.as_posix() != path
            or any(part in {"", ".", ".."} for part in pure.parts[1:])
            or any(marker in path for marker in "$`~*?[]{}()\\")
            or any(ord(character) < 32 for character in path)
        ):
            raise InstallError(
                "policy.allowed_external_redirects entries must be canonical literal paths"
            )
    rules = value["denied_commands"]
    if not isinstance(rules, list) or len(rules) > 256:
        raise InstallError("policy.denied_commands must be an array of at most 256 rules")
    rule_ids: set[str] = set()
    for rule in rules:
        if not isinstance(rule, dict) or frozenset(rule) != {"id", "pattern"}:
            raise InstallError("each denied command requires exactly id and pattern")
        rule_id = rule["id"]
        expression = rule["pattern"]
        if not isinstance(rule_id, str) or SAFE_ID.fullmatch(rule_id) is None:
            raise InstallError("a denied command id has an invalid shape")
        if rule_id in rule_ids:
            raise InstallError(f"duplicate denied command id: {rule_id}")
        rule_ids.add(rule_id)
        if not isinstance(expression, str) or not expression or len(expression) > 1024:
            raise InstallError(f"denied command {rule_id} has an invalid pattern")
        if not expression.startswith("^"):
            raise InstallError(f"denied command {rule_id} pattern must be anchored with ^")
        try:
            re.compile(expression)
        except re.error as exc:
            raise InstallError(f"denied command {rule_id} has invalid regex: {exc}") from exc
    string_array(value, "receipt_agents", maximum=128, pattern=SAFE_AGENT)
    if value["receipt_schema"] != "devforgeai.worker-result/v1":
        raise InstallError("policy.receipt_schema must be devforgeai.worker-result/v1")
    statuses = string_array(value, "receipt_statuses", maximum=16)
    if not statuses or not set(statuses).issubset(RECEIPT_STATUSES):
        raise InstallError("policy.receipt_statuses contains an unsupported status")
    limit = value["max_receipt_bytes"]
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1024 <= limit <= 65536:
        raise InstallError("policy.max_receipt_bytes must be between 1024 and 65536")
    context_limit = value["max_context_chars"]
    if (
        isinstance(context_limit, bool)
        or not isinstance(context_limit, int)
        or not 128 <= context_limit <= 16384
    ):
        raise InstallError("policy.max_context_chars must be between 128 and 16384")
    check_config = value["check_config"]
    if not isinstance(check_config, dict):
        raise InstallError("policy.check_config must be an object")
    for name, config in check_config.items():
        if not isinstance(name, str) or re.fullmatch(r"[a-z][a-z0-9_]{1,63}", name) is None:
            raise InstallError("policy.check_config contains an invalid check name")
        if not isinstance(config, dict):
            raise InstallError(f"policy.check_config.{name} must be an object")
    return value


def validate_hook_template(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or not isinstance(value.get("hooks"), dict):
        raise InstallError("hooks.codex.json must contain one hooks object")
    hooks = value["hooks"]
    if set(hooks) != set(EVENTS):
        raise InstallError("hooks.codex.json must declare exactly the four POC events")
    for event in EVENTS:
        groups = hooks[event]
        if not isinstance(groups, list) or len(groups) != 1 or not isinstance(groups[0], dict):
            raise InstallError(f"{event} must contain exactly one matcherless group")
        group = groups[0]
        if "matcher" in group or frozenset(group) != {"hooks"}:
            raise InstallError(f"{event} group must contain only hooks and no matcher")
        handlers = group["hooks"]
        if not isinstance(handlers, list) or len(handlers) != 1:
            raise InstallError(f"{event} must contain exactly one dispatcher handler")
        handler = handlers[0]
        if not isinstance(handler, dict) or handler.get("type") != "command":
            raise InstallError(f"{event} dispatcher must be a command handler")
        command = handler.get("command")
        if (
            not isinstance(command, str)
            or ".codex/hooks/hookd.py" not in command
            or re.search(rf"--expect-event(?:=|\s+){re.escape(event)}(?:\s|$)", command) is None
        ):
            raise InstallError(f"{event} handler does not bind hookd to its expected event")
    return value


def has_inline_hooks(config: Path) -> bool:
    if not config.exists():
        return False
    if config.is_symlink():
        raise InstallError(f"Codex config must not be a symlink: {config}")
    try:
        payload = config.read_bytes()
    except OSError as exc:
        raise InstallError(f"cannot read Codex config: {config}: {exc}") from exc
    try:
        parsed = tomllib.loads(payload.decode("utf-8"))
    except (UnicodeError, tomllib.TOMLDecodeError) as exc:
        raise InstallError(f"Codex config is invalid TOML: {config}: {exc}") from exc
    return isinstance(parsed, dict) and "hooks" in parsed


def load_existing_hooks(path: Path) -> tuple[dict[str, Any], bool]:
    if not path.exists():
        return {}, False
    value = load_json(path, "installed hooks.json")
    if not isinstance(value, dict):
        raise InstallError("installed .codex/hooks.json must be one JSON object")
    if "description" in value and not isinstance(value["description"], str):
        raise InstallError("installed .codex/hooks.json description must be a string")
    hooks = value.get("hooks")
    if hooks is not None and not isinstance(hooks, dict):
        raise InstallError("installed .codex/hooks.json hooks must be an object")
    if isinstance(hooks, dict):
        for event, groups in hooks.items():
            if not isinstance(event, str) or not isinstance(groups, list):
                raise InstallError("installed .codex/hooks.json has an invalid event entry")
            for group in groups:
                if not isinstance(group, dict):
                    raise InstallError(f"installed hook group for {event} must be an object")
                if "matcher" in group and not isinstance(group["matcher"], str):
                    raise InstallError(f"installed hook matcher for {event} must be a string")
                handlers = group.get("hooks")
                if not isinstance(handlers, list) or not handlers:
                    raise InstallError(f"installed hook group for {event} needs handlers")
                for handler in handlers:
                    if not isinstance(handler, dict):
                        raise InstallError(f"installed hook handler for {event} must be an object")
                    if not isinstance(handler.get("type"), str) or not handler["type"]:
                        raise InstallError(f"installed hook handler for {event} needs a type")
                    if handler["type"] == "command" and (
                        not isinstance(handler.get("command"), str) or not handler["command"]
                    ):
                        raise InstallError(
                            f"installed command hook handler for {event} needs a command"
                        )
    return value, True


def owns_handler(handler: Any, event: str) -> bool:
    if not isinstance(handler, dict) or handler.get("type") != "command":
        return False
    command = handler.get("command")
    if not isinstance(command, str):
        return False
    root_expression = "$(git rev-parse --show-toplevel)"
    if command.count(root_expression) != 1:
        return False
    try:
        tokens = shlex.split(command.replace(root_expression, "__DEVFORGE_ROOT__"), posix=True)
    except ValueError:
        return False
    expanded: list[str] = []
    for token in tokens:
        if token.startswith("--expect-event="):
            expanded.extend(("--expect-event", token.split("=", 1)[1]))
        elif token.startswith("--deadline-ms="):
            expanded.extend(("--deadline-ms", token.split("=", 1)[1]))
        else:
            expanded.append(token)
    if len(expanded) not in {4, 6}:
        return False
    if expanded[:4] != [
        "python3",
        "__DEVFORGE_ROOT__/.codex/hooks/hookd.py",
        "--expect-event",
        event,
    ]:
        return False
    return len(expanded) == 4 or (
        expanded[4] == "--deadline-ms" and expanded[5].isdigit()
    )


def merge_hooks(
    installed: dict[str, Any], existed: bool, template: dict[str, Any]
) -> dict[str, Any]:
    # JSON round-trip makes a detached deep copy without accepting custom objects.
    merged = json.loads(json.dumps(installed))
    if not existed and "description" in template:
        merged["description"] = template["description"]
    target_hooks = merged.setdefault("hooks", {})
    for event in EVENTS:
        groups = target_hooks.setdefault(event, [])
        if not isinstance(groups, list):
            raise InstallError(f"installed hook event {event} must be an array")
        owned: list[tuple[int, int]] = []
        for index, group in enumerate(groups):
            if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
                continue
            count = sum(1 for handler in group["hooks"] if owns_handler(handler, event))
            if count:
                owned.append((index, count))
        owned_count = sum(count for _, count in owned)
        if owned_count > 1:
            raise InstallError(f"multiple DevForgeAI dispatcher handlers exist for {event}")
        desired = template["hooks"][event][0]
        if owned:
            index, _ = owned[0]
            existing_group = groups[index]
            if len(existing_group["hooks"]) != 1 or set(existing_group) - {"hooks", "matcher"}:
                raise InstallError(
                    f"DevForgeAI dispatcher for {event} shares a group with unrelated configuration"
                )
            groups[index] = desired
        else:
            groups.append(desired)
    return merged


def assert_safe_destination(root: Path, path: Path) -> None:
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise InstallError(f"destination escapes project root: {path}") from exc
    cursor = path
    while cursor != root:
        if cursor.is_symlink():
            raise InstallError(f"installation path must not be a symlink: {cursor}")
        cursor = cursor.parent


def atomic_write(path: Path, payload: bytes, default_mode: int = 0o644) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else default_mode
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary)
    try:
        os.fchmod(descriptor, mode)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def validate_candidate_runtime(
    source: Path,
    installed_runtime: Path,
    project_root: Path,
    desired_policy: dict[str, Any],
) -> None:
    """Validate shipped code plus preserved local extensions before target writes."""

    with tempfile.TemporaryDirectory(prefix="devforgeai-hookd-validate-") as temporary:
        staged = Path(temporary) / "hooks"
        staged_checks = staged / "checks"
        staged_checks.mkdir(parents=True)

        for source_path in sorted(source.glob("*.py")):
            if source_path.is_symlink() or not source_path.is_file():
                raise InstallError(f"managed source is not a regular file: {source_path}")
            shutil.copyfile(source_path, staged / source_path.name)
        shipped_check_names: set[str] = set()
        for source_path in sorted((source / "checks").glob("*.py")):
            if source_path.is_symlink() or not source_path.is_file():
                raise InstallError(f"managed source is not a regular file: {source_path}")
            shipped_check_names.add(source_path.name)
            if source_path.name != "local_registry.py":
                shutil.copyfile(source_path, staged_checks / source_path.name)

        installed_checks = installed_runtime / "checks"
        if installed_checks.is_dir():
            for local_path in sorted(installed_checks.glob("*.py")):
                if local_path.is_symlink() or not local_path.is_file():
                    raise InstallError(f"local check module is not a regular file: {local_path}")
                if local_path.name not in shipped_check_names or local_path.name == "local_registry.py":
                    shutil.copyfile(local_path, staged_checks / local_path.name)
        local_registry = staged_checks / "local_registry.py"
        if not local_registry.exists():
            shutil.copyfile(source / "checks" / "local_registry.py", local_registry)

        policy_payload = json_bytes(desired_policy)
        if len(policy_payload) > MAX_POLICY_BYTES:
            raise InstallError(f"desired policy exceeds {MAX_POLICY_BYTES} bytes")
        (staged / "policy.json").write_bytes(policy_payload)
        try:
            completed = subprocess.run(
                [
                    sys.executable,
                    str(staged / "engine.py"),
                    "--project-root",
                    str(project_root),
                    "--validate-installation",
                ],
                cwd=project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise InstallError("candidate runtime validation could not run") from exc
        try:
            result = json.loads(
                completed.stdout,
                object_pairs_hook=object_without_duplicates,
                parse_constant=reject_nonfinite,
            )
        except (json.JSONDecodeError, InstallError) as exc:
            raise InstallError("candidate runtime validation returned invalid output") from exc
        if (
            completed.returncode != 0
            or not isinstance(result, dict)
            or result.get("schema") != "devforgeai.hookd-outcome/v1"
            or result.get("kind") != "pass"
        ):
            raise InstallError("candidate runtime rejected policy, registry, or check_config")


def require_git_root(root: Path) -> None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise InstallError(f"cannot establish the Git/worktree root: {exc}") from exc
    if completed.returncode != 0:
        raise InstallError("project root must be a Git worktree root")
    try:
        discovered = Path(completed.stdout.strip()).resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise InstallError("git returned an invalid worktree root") from exc
    if discovered != root:
        raise InstallError(
            f"--project-root must name the exact Git/worktree root: expected {discovered}"
        )


def custody_digest(entries: list[tuple[str, bytes]]) -> str:
    digest = hashlib.sha256()
    for relative, payload in sorted(entries):
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(payload).digest())
        digest.update(b"\0")
    return digest.hexdigest()


def main() -> int:
    source = Path(sys.argv[1]).resolve(strict=True)
    args = parse_args(sys.argv[2:])
    try:
        root = args.project_root.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise InstallError(f"project root does not resolve: {args.project_root}: {exc}") from exc
    if not root.is_dir():
        raise InstallError(f"project root is not a directory: {root}")
    require_git_root(root)

    codex_dir = root / ".codex"
    runtime_dir = codex_dir / "hooks"
    checks_dir = runtime_dir / "checks"
    hooks_path = codex_dir / "hooks.json"
    config_path = codex_dir / "config.toml"
    policy_path = runtime_dir / "policy.json"
    local_registry_path = checks_dir / "local_registry.py"
    for destination in (
        codex_dir,
        runtime_dir,
        checks_dir,
        hooks_path,
        config_path,
        policy_path,
        local_registry_path,
    ):
        assert_safe_destination(root, destination)

    if has_inline_hooks(config_path):
        raise InstallError(
            "inline hooks are present in .codex/config.toml; keep one project representation "
            "and remove or migrate them before installing .codex/hooks.json"
        )

    template = validate_hook_template(load_json(source / "hooks.codex.json", "hook template"))
    source_policy = validate_policy(
        load_json(source / "policy.json", "source policy", max_bytes=MAX_POLICY_BYTES)
    )
    schema = load_json(source / "policy.schema.json", "policy schema")
    if not isinstance(schema, dict) or schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise InstallError("policy.schema.json must be a Draft 2020-12 JSON Schema")

    installed_hooks, hooks_existed = load_existing_hooks(hooks_path)
    merged_hooks = merge_hooks(installed_hooks, hooks_existed, template)

    installed_policy: dict[str, Any] | None = None
    if policy_path.exists():
        installed_policy = validate_policy(
            load_json(policy_path, "installed policy", max_bytes=MAX_POLICY_BYTES)
        )
        desired_policy = json.loads(json.dumps(installed_policy))
    else:
        desired_policy = json.loads(json.dumps(source_policy))
    if args.enable_denies:
        desired_policy["mode"] = "enforce"
    validate_policy(desired_policy)

    source_local_registry = source / "checks" / "local_registry.py"
    if not source_local_registry.is_file() or source_local_registry.is_symlink():
        raise InstallError("source checks/local_registry.py is missing or unsafe")
    validate_candidate_runtime(source, runtime_dir, root, desired_policy)
    managed_sources = sorted(source.glob("*.py")) + sorted((source / "checks").glob("*.py"))
    writes: list[tuple[Path, bytes]] = []
    drift: list[str] = []
    custody_source_entries: list[tuple[str, bytes]] = []
    custody_destinations: list[tuple[str, Path]] = []

    for source_path in managed_sources:
        if source_path.is_symlink() or not source_path.is_file():
            raise InstallError(f"managed source is not a regular file: {source_path}")
        if source_path == source_local_registry:
            continue
        relative = source_path.relative_to(source)
        destination = runtime_dir / relative
        assert_safe_destination(root, destination)
        payload = source_path.read_bytes()
        custody_source_entries.append((relative.as_posix(), payload))
        custody_destinations.append((relative.as_posix(), destination))
        if not destination.exists() or destination.read_bytes() != payload:
            writes.append((destination, payload))
            drift.append(destination.relative_to(root).as_posix())

    schema_destination = runtime_dir / "policy.schema.json"
    schema_payload = (source / "policy.schema.json").read_bytes()
    custody_source_entries.append(("policy.schema.json", schema_payload))
    custody_destinations.append(("policy.schema.json", schema_destination))
    if not schema_destination.exists() or schema_destination.read_bytes() != schema_payload:
        writes.append((schema_destination, schema_payload))
        drift.append(schema_destination.relative_to(root).as_posix())

    if not local_registry_path.exists():
        payload = source_local_registry.read_bytes()
        writes.append((local_registry_path, payload))
        drift.append(local_registry_path.relative_to(root).as_posix())

    desired_policy_payload = json_bytes(desired_policy)
    if installed_policy is None or desired_policy != installed_policy:
        writes.append((policy_path, desired_policy_payload))
        drift.append(policy_path.relative_to(root).as_posix())

    desired_hooks_payload = json_bytes(merged_hooks)
    if merged_hooks != installed_hooks:
        writes.append((hooks_path, desired_hooks_payload))
        drift.append(hooks_path.relative_to(root).as_posix())

    source_runtime_sha256 = custody_digest(custody_source_entries)

    if args.check:
        if drift:
            print("installation drift:")
            for item in dict.fromkeys(drift):
                print(f"  {item}")
            return 1
        print(f"ok: Codex hookd installation is current; mode={desired_policy['mode']}")
        destination_entries = [
            (relative, destination.read_bytes())
            for relative, destination in custody_destinations
        ]
        print(f"runtime source sha256={source_runtime_sha256}")
        print(f"runtime destination sha256={custody_digest(destination_entries)}")
        print(f"policy destination sha256={hashlib.sha256(policy_path.read_bytes()).hexdigest()}")
        print(f"hooks destination sha256={hashlib.sha256(hooks_path.read_bytes()).hexdigest()}")
        return 0

    if args.dry_run:
        if not drift:
            print(f"no changes; installed policy mode remains {desired_policy['mode']}")
            return 0
        for item in dict.fromkeys(drift):
            print(f"would write {item}")
        print(f"would leave policy mode={desired_policy['mode']}")
        print(f"runtime source sha256={source_runtime_sha256}")
        print(f"policy desired sha256={hashlib.sha256(desired_policy_payload).hexdigest()}")
        print(f"hooks desired sha256={hashlib.sha256(desired_hooks_payload).hexdigest()}")
        return 0

    # Runtime and policy land before hooks.json so a new event definition never
    # points at files that have not yet been installed. Each replacement is atomic.
    for destination, payload in writes:
        if destination == hooks_path:
            continue
        atomic_write(destination, payload)
    for destination, payload in writes:
        if destination == hooks_path:
            atomic_write(destination, payload)

    print(f"installed Codex hookd into {root}; policy mode={desired_policy['mode']}")
    destination_entries = [
        (relative, destination.read_bytes()) for relative, destination in custody_destinations
    ]
    print(f"runtime source sha256={source_runtime_sha256}")
    print(f"runtime destination sha256={custody_digest(destination_entries)}")
    print(f"policy destination sha256={hashlib.sha256(policy_path.read_bytes()).hexdigest()}")
    print(f"hooks destination sha256={hashlib.sha256(hooks_path.read_bytes()).hexdigest()}")
    if desired_policy["mode"] == "observe":
        print("denials are observation-only; inspect the audit log, then rerun with --enable-denies")
    print("open /hooks in a fresh Codex session to review and trust the exact definitions")
    return 0


try:
    raise SystemExit(main())
except InstallError as exc:
    print(f"install: {exc}", file=sys.stderr)
    raise SystemExit(2)
PY
