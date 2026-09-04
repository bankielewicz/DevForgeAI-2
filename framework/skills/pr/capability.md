# Pull-request packet capability

This contract defines a human-published pull-request packet for one immutable
Git range. It does not push a branch, call GitHub, merge a pull request, change
branch protection, or attest reviewer identity.

The accepted entry is an explicit base and head, each a full 40-character
lowercase commit ID. The gate requires the base to be an ancestor of the head,
the canonical checkout to be on a named non-default branch at the exact head,
and the configured remote default branch to resolve to the exact base. Those
checks bind the prose packet to the same refs the human later publishes.

The model performs two bounded phases:

1. `pr_drafter` reads the committed range and writes only
   `pr-artifacts/title.txt` and `pr-artifacts/body.md` inside the candidate
   root.
2. `pr_critic` writes nothing. It returns findings that identify unsupported
   claims, missing governing artifacts, missing verification, or range drift.

The sequencer validates both files, copies their exact bytes to
`.devforgeai/work/<run>/output/`, writes `pr-packet.json` and a GitHub API
`pr-request.json`, removes the candidate root without promotion, and marks the
run `complete_external`. The human owns `git push` and the authenticated GitHub
request. A provider session may print those commands but may not execute them.

The deterministic PR-type classifier may emit more than one of these values:
`architecture`, `analyzed_plan`, `validated_skill`, `passing_qa`,
`governance_amendment`, and `implementation`. The classifier uses changed
paths; it does not infer that a review, validation, or QA verdict passed merely
because a report file exists. The drafter states only verdicts present in
committed artifacts.
