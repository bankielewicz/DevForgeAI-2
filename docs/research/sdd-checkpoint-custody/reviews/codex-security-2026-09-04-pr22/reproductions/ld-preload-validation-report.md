# Validation: loader environment executes before wrapper scrub

Candidate: candidate-72d484d951dcef65

- [x] Attacker input identified: LD_PRELOAD at the unprivileged process boundary.
- [x] Sink identified: the dynamic loader starts /bin/sh before the wrapper executes.
- [x] Minimal native constructor built outside the source tree.
- [x] Relative and absolute wrapper invocations exercised.
- [x] Counterevidence assessed: root ownership protects bytes, not the caller's process environment.

Disposition: reportable. Confidence: high.

A minimal shared library constructor created a marker when the changed wrapper was invoked. It executed before the wrapper rejected a relative path and repeatedly through an absolute invocation. Because the shell starts before lines 20-21 can scrub anything, adding unset LD_PRELOAD inside this script is insufficient.

Artifact: validation_artifacts/ld-preload-output.txt

