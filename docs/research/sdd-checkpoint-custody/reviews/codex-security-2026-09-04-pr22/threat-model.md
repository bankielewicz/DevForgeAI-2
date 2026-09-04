# Threat Model: PR 22 checkpoint validator promotion candidate

The reviewed change stages a release scaffold and checkpoint-closure validator whose security purpose is to prevent Claude Code or Codex, running as the unprivileged repository user, from changing or gaming authoritative gates. The protected DevForge installation is expected to be root-owned outside every agent-writable workspace.

## Assets and objectives

- Integrity and identity of the validator, launcher, schema, policy, dependencies, and complete installed release.
- Truth of checkpoint PASS and closure verdicts.
- Exact candidate-to-DevForge-release provenance.
- Closure-only history and authoritative base/head provenance.

## Attacker capabilities

- The workspace agent can edit checkpoint records, evidence, project-local code, and environment variables, and can invoke allowed commands as the ordinary user.
- The agent can choose CLI arguments unless a protected host supplies them.
- The agent cannot modify a correctly installed uid-0 release, obtain sudo non-interactively, or write the protected DevForge repository.
- Multiple immutable DevForge releases may coexist.

## Trust boundaries

- Agent-controlled shell arguments and process environment enter the protected wrapper.
- The wrapper launches the distro interpreter and imports the release-local validator.
- The executing validator verifies its own release root.
- Each record independently names a protected executable and associated release root.
- Git subprocesses turn repository history and a caller-provided diff range into closure decisions.
- Human promotion maps staged candidate bytes to a protected release.

## Security objectives

- The record executable must be exactly the executing release's own root/bin/devforge.
- Release metadata and promotion evidence must bind the candidate manifest, DevForge commit/tag, release manifest, and executing root.
- Caller environment must not redirect the interpreter, Git repository, object database, configuration, hooks, or output.
- A protected host, not the workspace agent, must bind the reviewed closure base/head.
- Staged candidate bytes must never be treated as protected.

## Assumptions and limitations

- POSIX uid/mode enforcement only.
- /usr/bin/python3 and its standard library remain outside RELEASE.sha256 and require separately reviewed distro evidence.
- No real root-owned install or two-terminal positive probe was authorized by D-CP00-11.
- The installer assumes an immutable DevForge source/release; this review did not run it as root.
- Codex Security advisory intelligence was unavailable after its authentication request, so no TAC result was incorporated.

Repository: DevForgeAI
Version: 257ba7dbf972d6591a2848bb97cfd9cb1a31033e

