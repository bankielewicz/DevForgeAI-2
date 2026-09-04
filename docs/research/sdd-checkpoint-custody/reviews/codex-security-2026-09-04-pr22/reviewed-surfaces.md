# Reviewed surfaces

| Surface | Risk area | Outcome | Notes |
|---|---|---|---|
| Validator release pin | Release identity and provenance | Reported | Cross-root hostile fixture returned PASS; version/source/promotion mapping is not parsed. |
| Git helper | Repository and history identity | Reported | Inherited GIT_DIR/GIT_WORK_TREE redirected HEAD while show-toplevel appeared legitimate. |
| Protected wrapper | Process integrity | Reported | LD_PRELOAD code ran before the shell could scrub environment variables. |
| Closure diff | Closure-only enforcement | Reported | A narrowed base hid implementation work and S10 emitted no problem. |
| Release payload and wheels | Offline reproducibility | No issue found | Manifest checks, offline hash-locked install, and 15 release tests passed. External PyPI provenance was not refreshed. |
| Installer source custody and post-verifier | Root-install assumptions | Needs follow-up | The installer trusts an externally asserted immutable DevForge source; missing verify-release.sh skips post-verification. No sudo/root probe was authorized. |
| Layout v1 exactness | Required launcher and exact modes | Needs follow-up | The generator/verifier require fewer entries and looser modes than the narrative layout; provider proof may catch availability but the contract is not machine-equivalent. |
| Plan CP-00 required outputs | Governance completeness | Needs follow-up | Section 10 omits components/devforge-release and its staged invocation becomes incomplete after closure without --diff. |

