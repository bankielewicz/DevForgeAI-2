# Pull-request packet workflow

## Entry gate

The adapter accepts exactly:

```text
--base <40-lowercase-hex> --head <40-lowercase-hex> [--draft]
```

It converts that form to `devforgeai phase start pr <base>..<head> [--draft]`.
The sequencer rejects malformed IDs, missing commits, a non-ancestor base, an
empty range, a head other than canonical `HEAD`, a detached or default head
branch, an unresolved remote default branch, a base other than that branch's
tip, or a non-GitHub `origin` URL. A refusal creates no run and no candidate.

## Dispatch loop

1. Print `devforgeai status` and dispatch only the worker named by its phase.
2. Give the worker the status block and paths, never pasted diff content.
3. Let `SubagentStop` deliver the worker receipt to the sequencer.
4. Repeat only when the sequencer names the next phase or retry.
5. On `complete_external`, print the sequencer-rendered handoff verbatim and
   stop. Do not push or publish.

## Drafter artifact contract

`title.txt` is UTF-8, one non-empty line, at most 72 characters, with no control
characters. `body.md` is UTF-8 and contains these headings exactly once and in
this order:

1. `## Summary`
2. `## Governing artifacts`
3. `## Changes`
4. `## Verification`
5. `## Limits`
6. `## Human publication`

The body names the full base and head commit IDs and contains no unfinished
placeholder. It may report a check only from committed evidence or from an
explicit result supplied by the status slice. Missing or unobserved checks stay
under `Limits`.

## External completion

The accepted output directory contains `title.txt`, `body.md`,
`pr-request.json`, and `pr-packet.json`. `pr-request.json` is the body for
GitHub's create-pull-request REST operation and contains only `title`, `head`,
`base`, `body`, and `draft`. The sequencer computes every digest in
`pr-packet.json` after all files are on disk.

The handoff names two human-owned actions in order: push the head branch, then
submit `pr-request.json` with an authenticated GitHub client. The adapter stops
before both actions. `post_action_next` preserves the workflow command that was
current when the PR run opened; it is not executed automatically.
