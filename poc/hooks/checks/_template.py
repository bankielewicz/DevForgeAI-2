"""Copy me to checks/<name>.py, rename the class, add it to REGISTRY.

Rules a check follows:
  * return Decision.none() to pass through; never "allow"
  * be fast and side-effect free on PreToolUse; a slow check hits the alarm
  * read policy from self.policy, not from the environment
  * put anything you need in the log into `reason`, never tool_input bodies
"""
from __future__ import annotations

from checks.base import Check, Decision, Event


class MyCheck(Check):
    name = "my_check"                 # appears in log lines and deny reasons
    events = ("PreToolUse",)          # any documented hook event names
    tool_matcher = r"^(Edit|Write)$"  # regex over tool_name; None for non-tool events
    order = 60                        # lower runs first; first deny short-circuits
    critical = False                  # True: an exception becomes a deny

    def run(self, ev: Event) -> Decision:
        rel = ev.rel_path(ev.file_path or "")
        if rel and rel.endswith(".lock"):
            return Decision.deny("lock files are generated; edit the manifest instead")
        return Decision.none()
