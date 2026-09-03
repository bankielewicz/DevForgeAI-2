"""Provider-neutral check outcomes used by the Codex hook dispatcher POC."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, ClassVar, Mapping


class OutcomeKind(str, Enum):
    PASS = "pass"
    VIOLATION = "violation"
    CONTEXT = "context"
    WARNING = "warning"
    STOP = "stop"


@dataclass(frozen=True)
class Outcome:
    """A semantic result. The parent process renders it for the Codex event."""

    kind: OutcomeKind
    reason_code: str = ""
    message: str = ""
    context: str = ""
    audit: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def pass_(cls, **audit: Any) -> "Outcome":
        return cls(OutcomeKind.PASS, audit=audit)

    @classmethod
    def violation(cls, code: str, message: str, **audit: Any) -> "Outcome":
        return cls(OutcomeKind.VIOLATION, code, message, audit=audit)

    @classmethod
    def context_(cls, text: str, **audit: Any) -> "Outcome":
        return cls(OutcomeKind.CONTEXT, context=text, audit=audit)

    @classmethod
    def warning(cls, code: str, message: str, **audit: Any) -> "Outcome":
        return cls(OutcomeKind.WARNING, code, message, audit=audit)

    @classmethod
    def stop(cls, code: str, message: str, **audit: Any) -> "Outcome":
        return cls(OutcomeKind.STOP, code, message, audit=audit)


@dataclass(frozen=True)
class CheckContext:
    project_root: Path
    runtime_dir: Path
    policy: Mapping[str, Any]
    policy_sha256: str

    def config_for(self, check_name: str) -> Mapping[str, Any]:
        """Return the already-validated object owned by one registered check."""

        value = self.policy["check_config"].get(check_name, {})
        if not isinstance(value, Mapping):  # engine validation should make this unreachable
            raise TypeError("check configuration must be an object")
        return value


class Check:
    """Base class for an explicitly registered hook check."""

    name: ClassVar[str]
    order: ClassVar[int]
    events: ClassVar[frozenset[str]]
    tool_pattern: ClassVar[str | None] = None
    critical: ClassVar[bool] = True

    def validate_config(self, config: Mapping[str, Any]) -> None:
        """Reject configuration unless a subclass defines and validates its keys."""

        if config:
            raise ValueError(f"{self.name} does not accept check_config values")

    def evaluate(self, event: Any, context: CheckContext) -> Outcome:
        raise NotImplementedError
