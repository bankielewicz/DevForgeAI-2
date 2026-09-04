# CP-00 research questions

Budget profile `quick` (six atomic questions, three lanes). Five questions were bound in `request.json` before discovery. Source classes: repository files at base commit `6a446355605a06891cdeab1cc9d25f35309afba2`, digested in `sources.jsonl`, and the decision authority's recorded decisions. Freshness rule: a repository source is the byte content at the base commit; a later commit reopens the question.

Each question has a direct lane (what the plan and the repository require) and a contrary lane (how the resulting check could be gamed or could be wrong). Dispositions are those of plan section 6.

## RQ-000001 — Which closure conditions must be machine-checked?

- **Scope:** plan section 7.1's nine `closed: true` conditions (nine after amendment SDD-GAP-AMD-001), the stage rules per checkpoint type, the admission states of section 2.1, the two-PR rule of 7.2, and the hostile list in the CP-00 specification. **Excluded:** conditions that need a human judgement (quality of a rationale).
- **Completion criteria:** every condition maps to a validator rule id with one positive and one hostile subprocess test.
- **Direct lane:** read section 7.1, 7.2, 9 and 12 (S-01) and the CP-00 specification (S-01).
- **Contrary lane:** find a condition that a structurally valid record could satisfy while still being illegal (self-review with a different string, an evidence commit that exists but is unmerged, a manifest that lists itself, a ledger that disagrees with the record).
- **Disposition:** `ANSWERED`. Rules S01–S13 in `validate.py`; 59 subprocess tests (`probes/tests.txt`). Claims C-01 (narrowed after V-02: condition 7 is partly a reviewer judgement), C-04, C-05.

## RQ-000002 — Where must the validator execute?

- **Scope:** the DevForge trust boundary the decision authority stated on 2026-09-04 (enforcement executables live in the protected DevForge repository; DevForgeAI stages promotion candidates and consumes pinned releases), the frozen Research CLI, and the packaging contract. **Excluded:** the DevForge repository's own release process.
- **Completion criteria:** an invocation that changes no frozen contract, ships in the staging wheel, and maps to the future `devforge checkpoint validate`, accepted by the decision authority.
- **Direct lane:** `tests/research/test_packaging.py` (S-02) freezes console scripts to exactly `devforgeai-research`, data-files to the research schemas, and the help text to ten operations; `docs/design/09-hook-dispatcher.md` check 9 (S-03) and `dispatch.py` `RESEARCH_OPS` (S-08) admit exactly those ten; `framework/skills/research/workflow.md` (S-04) is a frozen plan input. CLAUDE.md (S-05) and ADR-0001 (S-06) already place authoritative enforcement in DevForge with DevForgeAI as staging.
- **Contrary lane:** the plan author's first recommendation, `devforgeai-research validate-checkpoints` (contradiction X-01), and the DevForge-first sequence (X-02).
- **Disposition:** `ANSWERED`. Decision D-CP00-01: `python3 -m devforgeai.checkpoint validate --plan <dir>` under `components/research-core/src/devforgeai/checkpoint/`, chosen by the decision authority (S-07). Claims C-02 (narrowed to the console-script assertion after V-02), C-07 (the eleventh operation), C-03.

## RQ-000003 — How is explicitly external evidence represented?

- **Scope:** `admitted_inputs[].subject` and `evidence_paths`, and every other path field of the record. **Excluded:** custody of the external bytes themselves (an admission-PR concern).
- **Completion criteria:** a decidable rule without changing the exact record shape; the plan's run-5 inputs pass; a climbing absolute path and an escaping relative path fail.
- **Direct lane:** section 7.1 says "repository-relative path or explicitly external evidence path" (S-01); the run-5 inputs of section 2.1 are absolute paths outside the repository.
- **Contrary lane:** an absolute path silently accepted as relative, or a relative path with `..` reaching outside the repository.
- **Disposition:** `ANSWERED`. Decision D-CP00-02 as revised after V-02 (absolute path = external, no marker; rule S04). Claim C-05.

## RQ-000004 — What does reviewer independence mean here?

- **Scope:** `independent_review.reviewer_id` against `owner_id`. **Excluded:** authenticating that a string names who it claims.
- **Completion criteria:** a rule that rejects self-review and a recorded limitation.
- **Direct lane:** section 7.1 condition 4 (S-01).
- **Contrary lane:** the same actor under two identifier strings; a reviewer that is the dossier author but not the record owner.
- **Disposition:** `PARTIALLY_ANSWERED`. Rule S06.4 rejects `reviewer_id == owner_id`; the record shape carries no separate dossier-author field, so a reviewer who authored the dossier but not the record is not detectable from the record alone. Decision D-CP00-04 records the limitation; a future schema revision may add `research.authors`. Claim C-04.

## RQ-000005 — What makes "unbounded limitation" and "concrete reopen_if" testable?

- **Scope:** the two hostile cases named by the CP-00 specification. **Excluded:** judging whether a limitation is complete.
- **Completion criteria:** a written definition and a hostile test matching it exactly.
- **Direct lane:** section 7.1 conditions 7 and 8; the CP-00 hostile list (S-01).
- **Contrary lane:** a limitation that is non-empty but says nothing ("see above"), which the definition does not catch.
- **Disposition:** `ANSWERED` for the definition, with the contrary lane recorded as a limitation. Decision D-CP00-03: an unbounded limitation is empty, whitespace, a placeholder token (`TODO`, `TBD`, `{{`, `}}`, `<fill in>`, `lorem ipsum`) or over 1,000 characters; a non-concrete `reopen_if` entry is the same set; an empty `reopen_if` list on a closed record is rejected.
