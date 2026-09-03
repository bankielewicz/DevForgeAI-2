"""Project-owned extension registry. The installer preserves this file."""

from .local_command_probe import LocalCommandProbe


LOCAL_CHECKS = (LocalCommandProbe,)
