---
name: pr
description: Package one exact committed Git range into a reviewed pull-request title, body, and human publication request without pushing or calling GitHub.
argument-hint: "--base <40-lowercase-hex> --head <40-lowercase-hex> [--draft]"
disable-model-invocation: true
allowed-tools: Bash, Agent
---

# Pull-request packet adapter

Read `references/capability.md` and `references/workflow.md`. Parse exactly
`--base <40-lowercase-hex> --head <40-lowercase-hex> [--draft]`; otherwise stop
with usage and create no run.

Call `devforgeai phase start pr <base>..<head> [--draft]`. Thereafter call only
`devforgeai status` and dispatch the agent named by the status block. Pass the
verbatim status block and no diff content. The hook-owned SubagentStop path
ingests the receipt and advances the run.

When status reports `complete_external`, print the sequencer-rendered handoff
verbatim and stop. Do not run git push, `gh`, a GitHub API call, or a merge.
