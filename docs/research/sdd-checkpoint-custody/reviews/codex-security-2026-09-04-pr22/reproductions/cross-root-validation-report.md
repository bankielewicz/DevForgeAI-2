# Validation: executing and record release roots are not bound

Candidate: candidate-fa00cbdf00fd925e

- [x] Attacker input identified: protected_release fields in a workspace checkpoint record.
- [x] Root control identified: _check_release_pin derives a root solely from the record executable.
- [x] Executing release selection traced: _locate_schema independently finds and verifies the module's own root.
- [x] Focused hostile fixture executed against the actual validator.
- [x] Counterevidence assessed: both roots are individually immutable and digest-valid, but no equality or semantic promotion check joins them.

Disposition: reportable. Confidence: high.

The in-process CS-1.7 seam was used only to model uid-0 metadata, as the repository's own positive tests do. Release A was made the executing validator root, the closed CP-00 record continued to name release B, and both complete release trees verified. validate_plan returned PASS with zero problems. This proves CS-1.8 is absent. It also confirms that version, source_commit, and promotion evidence are only shape/hash fields rather than a parsed mapping to the executing release.

Artifact: validation_artifacts/cross-root-output.txt

