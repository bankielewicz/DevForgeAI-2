"""Checkpoint custody and closure validation for research-gap closure plans (CP-00).

Staged in DevForgeAI as a promotion candidate for the protected DevForge CLI
(`devforge checkpoint validate`). Invoke as::

    PYTHONPATH=components/research-core/src python3 -m devforgeai.checkpoint validate \\
        --plan docs/research/spec-driven-development-gap-closure

Exit codes: 0 every record holds; 1 at least one rule rejected; 2 usage;
3 could not run (missing plan, schema, or Git when a rule needs it).
"""

from devforgeai.checkpoint.validate import validate_plan, Problem

__all__ = ["validate_plan", "Problem"]
