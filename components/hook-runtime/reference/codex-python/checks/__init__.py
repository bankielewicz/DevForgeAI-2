"""Single explicit dispatcher registry; no filesystem or entry-point discovery."""

from .builtin_registry import BUILTIN_CHECKS
from .local_registry import LOCAL_CHECKS


REGISTRY = BUILTIN_CHECKS + LOCAL_CHECKS
