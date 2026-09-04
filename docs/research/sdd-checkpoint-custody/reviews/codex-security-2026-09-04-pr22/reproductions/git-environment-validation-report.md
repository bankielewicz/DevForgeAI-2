# Validation: inherited Git environment redirects repository identity

Candidate: candidate-47705383ae3f38a3

- [x] Attacker input identified: inherited GIT_DIR and GIT_WORK_TREE.
- [x] Sink identified: subprocess.run of PATH-resolved git with the full inherited environment.
- [x] Focused realistic command executed.
- [x] Trusted-root counterevidence tested.
- [x] No protected-byte or sudo precondition required.

Disposition: reportable. Confidence: high.

Two scratch repositories had different HEAD commits. With GIT_DIR set to the alternate repository and GIT_WORK_TREE set to the legitimate plan tree, git -C legitimate rev-parse --show-toplevel still returned the legitimate root while rev-parse HEAD returned the alternate commit. The candidate's _git helper inherits this behavior. Removing --git-root therefore does not make Git identity non-caller-selectable.

Artifact: validation_artifacts/git-environment-output.txt

