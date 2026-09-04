# Validation: caller-selected range omits closure-related implementation work

Candidate: candidate-6a9bcf718aaa5828

- [x] Attacker input identified: --diff base..head.
- [x] Root control identified: S10 computes only false-to-true closure transitions in that range.
- [x] Focused actual-validator fixture executed.
- [x] Candidate pin and checkpoint manifest were updated consistently.
- [x] Declared CS-3.3 limitation assessed.

Disposition: reportable. Confidence: high.

The fixture first legally closed CP-00. A later commit changed src/validator.py and rewrote the candidate manifest; the next commit re-pinned the still-closed record. Passing the implementation commit as base and the pin commit as head caused validation to return PASS with no S10 row. This is the exact protected-host dependency admitted by CS-3.3, not a closed control.

Artifact: validation_artifacts/range-bypass-output.txt

