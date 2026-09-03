---
id: RSR-2026-09-02-sdd-landscape-comparison
title: Spec-driven development landscape versus the DevForgeAI design
date: 2026-09-02
author: Claude (Fable 5.1), deep-research workflow wf_3a9c3002-0d9 plus two Opus digest agents
status: draft
inputs:
  - web: 26 sources fetched, 128 claims extracted, 25 verified by 3-vote adversarial check, 15 findings kept, 3 refuted, 4 budget-dropped
  - codex: docs/research/spec-driven-ai-framework-skill-roster/ (RSR-2026-09-01, MANIFEST.sha256 verified OK)
  - claude: docs/design/00-06, templates/, examples/SKILL-SPEC-001-dev-tdd.md
---

# Spec-driven development landscape versus the DevForgeAI design

Citation forms: `F<n>` is a verified web finding (full list in section 8); `codex:<file>:<line>` is Codex's research corpus under `docs/research/spec-driven-ai-framework-skill-roster/`; `design:<file>:<line>` is `docs/design/`.

## 1. Executive summary

All three inputs agree on the shape of the field. Spec-driven development (SDD) for AI agents converges on a constitution-spec-plan-tasks pipeline, context-isolated subagents that return only a final result, progressive disclosure for skills, and Markdown artifacts with weak or convention-only provenance. They also agree that outcome evidence is thin and mostly vendor-authored.

Three tensions matter for DevForgeAI.

- **Observed architecture.** Both local corpora independently propose generating an observed baseline from existing code. The verified landscape moved the other way in August 2026: BMAD v6.11.0 deleted generated project docs and now stores only what cannot be derived from source (F9), and no core framework generates an observed-architecture artifact (F1, F4, F8). This is the sharpest external challenge to `03-brownfield.md`.
- **Stack agnosticism.** This is the user's stated priority and every input is weak on it. The web landscape is agnostic at the process level and stack-specific at the toolkit level (F2, F12). Codex's research addresses provider agnosticism only. The design claims language and package-manager detection but never specifies the mechanism, and its only worked example is pytest. This is the single biggest gap.
- **Gating philosophy.** The landscape splits into phase-approval gates that are human or LLM-instructional (Kiro, BMAD, Spec Kit; F3, F6, F10) and executable validators with no phase gates (OpenSpec; F5). DevForgeAI's template-header gate is executable like OpenSpec while its phase pipeline is fixed like Kiro. Codex's richer gate and state vocabulary has no counterpart in the design.

Coverage gap: zero verified web claims survived on OpenAI Codex-native skills, Tessl, Cursor rules beyond AGENTS.md handling, or academic SDD literature. The design's `04-dual-target.md` therefore rests on Codex's own documentation as read in `codex:sources/codex.md`.

## 2. Method and disclosure

- **Web run.** Five search angles, 26 sources, 128 claims extracted, 25 selected for verification, 22 confirmed, 3 refuted, 15 findings after merging. Almost every source is first-party vendor or project documentation, which is adequate for product-behavior claims and inadequate for effectiveness claims. No finding says any framework improves outcomes.
- **Refuted and excluded.** Spec Kit's nine-command enumeration (0-3). Kiro's "Sync Files" brownfield mechanism (0-3). traceSDD's hallucination-detection percentages (0-3).
- **Split votes rated medium.** Spec Kit brownfield/converge (F1), Spec Kit LLM-only gating (F3), AGENTS.md precedence (F13), traceSDD determinism (F15).
- **Codex corpus.** Independent input: it excluded DevForgeAI and `docs/design/` from its corpus (`codex:README.md:13-16`). It adds a 27-repository static audit pinned by commit (`codex:sources/local-repository-corpus.md:62-90`) that nothing here re-ran, and it read Codex's provider docs directly (`codex:sources/codex.md`), which the web run could not verify. Nothing in that corpus was installed or executed (`codex:sources/local-repository-corpus.md:4-5`), so its runtime verdicts are NOT_EVALUATED (CLM-045).
- **Claude corpus.** The design docs cite no external SDD framework at all; they borrow only from Anthropic's skill-creator, the Agent Skills spec, and the Claude Code and Codex layouts (`design:06-skill-specification.md:17,23-42`, `design:04-dual-target.md:95-128`).
- **Time sensitivity.** Spec Kit v1.0.3 shipped 2026-09-01, OpenSpec v1.11.0 on 2026-08-26 with validator features added weekly, BMAD v6.11.0 on 2026-08-10 with breaking changes to brownfield skills, Kiro docs updated 2026-08-27. agentskills.io and agents.md are unversioned and pinned only as "fetched 2026-09-02".

## 3. Six-axis crosswalk

| Axis | Web (verified) | Codex research (2026-09-01) | Claude design (2026-09-02) |
|---|---|---|---|
| 1. Landscape | Spec Kit v1.0.3, OpenSpec v1.11.0, Kiro (docs 2026-08-27), BMAD v6.11.0, Agent Skills spec, AGENTS.md, Claude Code subagents (F1-F14). Nothing verified on Tessl, Codex-native skills, Cursor rules. | Same five plus Spec Kitty, Cucumber/Example Mapping, Scrum Guide, AWS ADR/C4, Codex docs, and a 27-repo audit (`codex:sources/spec-driven-methods.md:8-168`). | No external framework cited. Self-originated pipeline of 18 skills (`design:02-skill-roster.md`). |
| 2. Brownfield | Incremental reconciliation everywhere: converge diff (F1), delta specs (F4), Design-first and Bugfix specs with Unchanged Behavior (F8), one verified block in AGENTS.md (F9). No core reverse-specification. | D-001 open; recommends one lifecycle, greenfield first, typed routes (`codex:open-decisions.md:18`). `brownfield-baseline` is "Next" tier and would emit an observed current-system contract (`codex:skill-roster.md:16-17`). | Two doors: init to brainstorm, init to onboard (`design:00-overview.md:13`). Archaeologist persona, OBSERVED vs INTENDED per section, EPIC-000 migration, `--scope feature|change|hotfix` (`design:03-brownfield.md:20-64`). |
| 3. Stack agnosticism | Process-level only. Spec Kit needs Python 3.11+/uv, stack chosen at plan time (F2). Agent Skills pushes stack to optional `compatibility`, script languages "depend on the agent" (F12). AGENTS.md is plain Markdown (F13). | Not addressed. Provider agnosticism instead: shared capability contract plus generated wrappers, parity = same inputs/outputs/state/evidence (`codex:provider-adapters.md:3-7,65-99`). Keep tech versions out of the constitution (D-004). | Pipeline, envelope, handoff, subagent contracts are neutral (`design:01-skill-anatomy.md:40-49,216-229`). Detection of language and package manager is asserted (`design:02-skill-roster.md:108`, `design:03-brownfield.md:26`) but unspecified. Hash rule assumes Markdown headings (`design:01-skill-anatomy.md:169-174`). Only worked example is pytest (`design:examples/SKILL-SPEC-001-dev-tdd.md:276,301,437,498-505`). |
| 4. Provenance and gating | Mostly convention: documented rationale, EARS criteria (F7), archived change folders (F4). Only OpenSpec validates content executably (F5). Spec Kit gates are LLM text (F3). Kiro gates are human approvals, optional in Quick Spec (F6). BMAD PASS/CONCERNS/FAIL readiness gate finds artifacts by content (F10). | W3C PROV, SLSA v1.2, in-toto shapes; a digest is not an attestation (`codex:sources/assurance-and-agent-reliability.md:218-243`). Digest-pinned manifest, STALE on change (`codex:context-traceability-handoffs.md:8-21,47-100`). Gates declare BLOCK/REQUIRE_HUMAN/WARN/OFF plus timeout and malformed behavior (`codex:sources/local-repository-corpus.md:221-223`). COULD_NOT_RUN vs INFRA_FAILURE vs BLOCKED (`codex:workflow-and-artifacts.md:266-294`). | Context bundle with verbatim excerpt, anchor and sha256; template headers with required sections and forbidden text; gate never repairs, four outcomes (`design:01-skill-anatomy.md:71-111,150-181`). `state.yaml` with per-phase hashes (`design:01-skill-anatomy.md:183-213`). |
| 5. Agent structure | Context-isolated subagents returning only final results; fork drops input isolation (F14). BMAD dispatches context-free coders and reviewers from a `customize.toml` recipe, parent barred from restating goals (F11). Three-tier progressive disclosure (F12). | Four layers; subagents isolate context but do not prove truth; six-question delegation gate; handoff protocol with 11 field groups; nine validator lanes (`codex:README.md:20-48`, `codex:context-traceability-handoffs.md:186-289`, `codex:skill-roster.md:67-84`). | Three layers; seven sub-phases each a subagent; primary window contract and envelope; persona and critic distinct; handoff with seven rules; skill spec with skip/quick/full evals; `isolation: required` fails closed (`design:01-skill-anatomy.md:10-69,113-144,216-260`, `design:04-dual-target.md:88-91,128`, `design:06-skill-specification.md:44-68`). |
| 6. Evidence and failure modes | One preprint on citation discipline and determinism (F15); hallucination-detection result refuted. Practitioner criticism: "convention rather than enforcement" (F3). | Broad: multi-agent gains +80.8% to -70% across 260 configs; ~15x tokens; 59.4% of audited SWE-bench Verified tasks flawed; METR +19% slower; 157 malicious of 98,380 skills (`codex:sources/assurance-and-agent-reliability.md:14-17,44-49,184-187,283-286,322-327`). Corpus defects: completion equals file existence, validators exiting 1 that do not block, fail-open hooks (`codex:sources/local-repository-corpus.md:101-121`). | Acknowledged: full eval needs interactive session, background evals lost, holdout ignored, SPEC GAPS as intended failure (`design:06-skill-specification.md:89-94`). Escape hatches: `--force`, `--scope`, placeholder hashes warn outside a project (`design:02-skill-roster.md:156`, `design:03-brownfield.md:61`, `design:01-skill-anatomy.md:174`). |

## 4. Framework version pins

| Framework | Web run pin | Codex pin | Note |
|---|---|---|---|
| GitHub Spec Kit | v1.0.3, released 2026-09-01 (F1, F2) | commit `0053c3a3` (`codex:sources/spec-driven-methods.md:8-9`) | Codex pinned a commit on 2026-09-01; the web run pinned the release of the same day. Possibly the same tree, not confirmed. Codex's local clone differs from its web pin (`codex:sources/local-repository-corpus.md:92-94`). |
| OpenSpec | v1.11.0, 2026-08-26 (F4, F5) | docs quickstart, unpinned (`codex:sources/spec-driven-methods.md:61-63`) | Validator features landed in v1.6, v1.8, v1.9, v1.11. Codex's OpenSpec observations predate the placeholder-Purpose detector. |
| Kiro | docs updated 2026-08-27 and 2026-08-04; IDE 1.0.0 on 2026-06-25 (F6-F8) | kiro.dev/docs/specs, unpinned (`codex:sources/spec-driven-methods.md:38-40`) | Quick Spec (no gates) postdates nothing in Codex's notes but is absent from them. |
| BMAD Method | v6.11.0, 2026-08-10 (F9-F11) | commit `4fc185c5` (`codex:sources/spec-driven-methods.md:83-84`) | v6.11.0 removed `bmad-document-project` and `bmad-check-implementation-readiness`. Whether `4fc185c5` predates those removals is unverified. Codex's BMAD verdicts (`codex:sources/local-repository-corpus.md:158-174`) should be re-checked against v6.11.0. |
| Agent Skills spec | unversioned, fetched 2026-09-02 (F12) | agentskills.io/specification (`codex:sources/claude-and-agent-skills.md`) | Consistent: two required fields, six portable fields, 500-line limit. |
| AGENTS.md | unversioned, v1.1 frontmatter proposal pending (F13) | Codex docs (`codex:sources/codex.md`) | Codex concatenates root to cwd with a 32 KiB cap. |

## 5. Codex open decisions against the design

Codex left all 29 decisions open and said no default is accepted policy (`codex:open-decisions.md:11-14`). The design docs, written a day later without reading that corpus, settle several of them.

**Decided by the design, consistent with Codex's recommended default**

- D-002 sprint not mandatory: the design has sprints, but `--scope hotfix` enters with a single story and no sprint planning (`design:03-brownfield.md:54-58`).
- D-010 when subagents are required: every sub-phase, with `isolation: required|preferred` per step (`design:04-dual-target.md:88-91`).
- D-012, D-013 shared spec versus generated wrappers: neutral `skill.yaml` compiled per target (`design:04-dual-target.md:5-92`). Codex reached the same shape independently (`codex:provider-adapters.md:65-99`).
- D-015 what owns workflow state: `state.yaml` (`design:01-skill-anatomy.md:183-213`).
- D-018 provenance strength: sha256 local hashes, matching Codex's MVP recommendation (`codex:open-decisions.md:35`).
- D-019 provider version policy: pinned in `techstack.md` with a Provider Conformance attestation (`design:04-dual-target.md:124-128`). The attestation's producer and storage are undefined.

**Decided by the design, contrary to Codex's recommended default**

- D-001 greenfield first, brownfield later. The design treats brownfield as a first-class entry with its own skill and constitution status (`design:03-brownfield.md`). Codex recommends one lifecycle with typed routes and brownfield in the "Next" tier (`codex:open-decisions.md:18`, `codex:skill-roster.md:247`). The design's `--scope` flag covers three of Codex's seven route types (feature, change, hotfix); spike, refactor, migration, compliance and incident have no entry.
- D-011 YOLO mode: the design defines it as architect's option-comparer subagent selecting best practices per decision and recording each as an ADR (`design:02-skill-roster.md:133`, `design:05-subagent-sets.md:75`). Codex left it undefined. What YOLO may not decide unattended (for example licensing or data residency) is still unstated.

**Partially decided**

- D-023 phase complete/blocked/could-not-run: the design's envelope has `pass|fail|needs_user` and `UNSUPPORTED_CAPABILITY` (`design:01-skill-anatomy.md:40-49`, `design:04-dual-target.md:128`). Codex's COULD_NOT_RUN versus INFRA_FAILURE versus BLOCKED distinction is absent, so a test runner crash and a failing test currently collapse into the same status.
- D-016 hook failure policy: hooks are deferred and undefined (`design:06-skill-specification.md:102`). Codex's rule that every gate declares BLOCK/REQUIRE_HUMAN/WARN/OFF plus timeout behavior (`codex:sources/local-repository-corpus.md:221-223`) has no counterpart.
- D-008 acceptance oracle owner: the design's critic and smoke-qa subagents review, but no doc says who may amend acceptance criteria. D-024 (may QA edit code or specs) is likewise unaddressed.

**Still open in both**

D-003 constitution acceptance authority, D-005 where epics come from beyond the PRD, D-009 context budget per phase (the design reports tokens but sets no cap), D-017 research cache fidelity, D-020 skill installation trust, D-021 security in skill-validator, D-022 external systems, D-026 canonical layout (the design proposes one; Codex asks for acceptance), D-027 package installation lifecycle, D-028 when a downloaded framework may influence DevForgeAI, D-029 scalability evaluation.

## 6. Recommendations, keyed to the owning design doc

These are recommendations only. No design doc was edited in this task.

**03-brownfield.md**

1. Add a "derivability" admission rule to onboard's outputs, following BMAD v6.11.0 (F9): anything the agent can derive from source at run time is cited by path and not copied into OBSERVED sections. Keep OBSERVED for what source cannot tell you (why, history, timing, external constraints). This answers the strongest external objection while keeping the OBSERVED/INTENDED split.
2. Specify the code-mapper contract. It is the only place stack detection can live and today it is one line (`design:03-brownfield.md:26`). It should emit a machine-readable `stack.yaml` with build, test, lint and format commands, package manager, test-file glob and test-runner probe command per language present. Every downstream skill reads that file instead of assuming pytest.
3. Adopt Spec Kit converge's gap taxonomy missing/partial/contradicts/unrequested (F1) in place of the single CONFLICT tag. "Unrequested" catches code with no story, which is the common brownfield case.
4. For `--scope hotfix`, add an Unchanged Behavior section to the hotfix story, following Kiro's bugfix.md (F8). It gives smoke-qa an explicit regression surface.
5. Add spike, refactor and migration to `--scope`, or state why three routes are enough (Codex D-001).

**05-subagent-sets.md**

6. Make dev, dev-tdd, review and qa read commands from `stack.yaml` rather than from the skill spec. The dev-tdd example currently hard-codes `pytest` in the gate probe and `allowed-tools`.
7. Add a build or compile step before red-tester for compiled languages. No sub-phase compiles today, which is fatal for C#, Rust, Go and Java.
8. Resolve the test-layout conflict between `tests/<story-id>/*.test.*` (`design:05-subagent-sets.md:17`) and `tests/test_<module>.py` in the example. Delegate layout to `stack.yaml`.
9. Consider BMAD's rule that the parent may not restate goals or inject acceptance criteria into the dispatch (F11). The design's primary window contract already forbids content reads; extending it to forbid paraphrase closes the same hole.

**01-skill-anatomy.md**

10. Extend the envelope status set with `infra_failure` and `could_not_run`, distinct from `fail` (Codex D-023). Test-runner missing, network down and timeout are not story failures.
11. Extend the hash rule beyond Markdown headings: symbol or AST anchors for code slices, and section anchors for reStructuredText and AsciiDoc. Line anchors go stale on any edit.
12. Adopt Codex's rule "do not hash a document inside itself" (`codex:workflow-and-artifacts.md:277-278`) explicitly; the current rule hashes sections, which is compatible, but the doc never says the artifact's own frontmatter hash must be excluded.
13. Fix the header-key discrepancy: `version: 2` at `design:01-skill-anatomy.md:104-105` versus `template_version: 2` in `templates/story.md`.

**02-skill-roster.md and 04-dual-target.md**

14. Define a gate policy vocabulary (BLOCK, REQUIRE_HUMAN, WARN, OFF) and the behavior on timeout or malformed input for each gate (Codex CLM-043). OpenSpec's experience (F5) shows executable validators need explicit skip declarations, for example `skip_specs: true`, rather than silent passes.
15. State what review's diff is computed against (`design:02-skill-roster.md:20,42`).
16. Define who produces and where to store Provider Conformance attestations. Until then `isolation: required` on Codex is unverifiable.
17. Add a CI entry point. The pipeline has no commit, branch or PR workflow, and OpenSpec's `--archived` pre-commit lint (F5) is a concrete pattern.

**06-skill-specification.md**

18. Add a "stack" subsection to skill-spec section 11 so generated skills declare which commands they need from `stack.yaml` instead of naming runtimes.

**00-overview.md**

19. Add a monorepo and multi-language position. `techstack.md`, `mode` and `slug` are singular in state (`design:00-overview.md:130-135`, `design:01-skill-anatomy.md:189-192`).
20. Cite the frameworks this design departs from, with one line each. A reader today cannot tell whether OBSERVED/INTENDED was chosen with knowledge of BMAD's reversal.

## 7. Open questions carried forward

From the web run:

1. Does any core framework generate an observed-architecture artifact from existing code, and how does it separate observed from intended? None verified does.
2. Will Spec Kit's named constitutional gates or any executable spec-content validation ship in installed templates?
3. Does the traceSDD determinism effect replicate under peer review, in non-Python languages, with functional metrics?
4. How do Codex-native skills and Tessl handle format, disclosure, isolation and gating? Zero claims survived.

From the crosswalk:

5. Is the design's OBSERVED constitution worth its maintenance cost once a derivability rule strips out everything readable from source? BMAD concluded no for docs; the design's answer should be explicit.
6. What is the smallest `stack.yaml` schema that lets one dev-tdd skill drive pytest, dotnet test, cargo test, go test, and a Node runner without per-stack skill variants?
7. Which of Codex's seven route types does DevForgeAI need at launch?
8. Should Codex's BMAD verdicts (`codex:sources/local-repository-corpus.md:158-174`) be re-run against v6.11.0 before they inform D-016 and D-028?

## 8. Web findings index

| Ref | Confidence | Vote | Claim (abridged) | Primary source |
|---|---|---|---|---|
| F1 | medium | 2-1 | Spec Kit v1.0.3: three modes; only brownfield mechanism is `/speckit.converge` (missing/partial/contradicts/unrequested); no core reverse-spec command; community extension v1.0.0 only. | github.com/github/spec-kit, fetched 2026-09-02 |
| F2 | high | 3-0 | Spec Kit: process-level agnosticism; stack chosen at plan; Python 3.11+, uv; 30+ agents via integrations; template precedence overrides > presets > extensions > core. | github.com/github/spec-kit README |
| F3 | medium | 2-1 | Spec Kit gating and traceability are LLM-instructional; only executable checks are prerequisite scripts, a human gate step, and bundle validation. | spec-driven.md; Scott Logic 2025-11-26 |
| F4 | high | 3-0 | OpenSpec v1.11.0 is brownfield-first: per-change folders, ADDED/MODIFIED/REMOVED deltas, dated archive with artifacts intact. | Fission-AI/OpenSpec docs/existing-projects.md |
| F5 | high | 3-0 | OpenSpec rejects phase gates; `openspec validate` checks structure, MODIFIED requirements, zero-delta changes, `--archived` pre-commit lint, placeholder Purpose. | OpenSpec docs/cli.md, CHANGELOG |
| F6 | high | 3-0 | Kiro Feature Specs: requirements, design, tasks with human approval gates; Quick Spec (IDE 1.0.0, 2026-06-25) has none. | kiro.dev/docs/specs, updated 2026-08-27 |
| F7 | high | 3-0 | Kiro uses EARS acceptance criteria for testability and per-requirement traceability. | kiro.dev/docs/specs/feature-specs |
| F8 | high | 3-0 | Kiro added Design-first specs and Bugfix specs with Current/Expected/Unchanged Behavior on 2026-02-18. | kiro.dev/blog/specs-bugfix-and-design-first |
| F9 | high | 3-0 | BMAD v6.11.0 (2026-08-10) replaced generated project docs with one verified AGENTS.md block; anything derivable from source is read live, never stored. | BMAD-METHOD releases v6.11.0 |
| F10 | high | 3-0 | BMAD v6.11.0 readiness gate PASS/CONCERNS/FAIL inside sprint-planning; finds artifacts by content not filename. | BMAD v6.11.0 release notes, PR #2659 |
| F11 | high | 3-0 | BMAD dispatches context-free coding and review subagents from a `customize.toml` recipe; parent may not restate goals or inject criteria. | BMAD v6.11.0, bmad-build customize.toml |
| F12 | high | 3-0 | Agent Skills spec: SKILL.md with two required fields; three-tier progressive disclosure; `compatibility` optional; script languages depend on the agent; `allowed-tools` experimental. | agentskills.io/specification, fetched 2026-09-02 |
| F13 | medium | 3-0, 2-1 | AGENTS.md: Markdown only, no schema or linter; closest file wins; Codex concatenates root to cwd with 32 KiB cap; v1.1 frontmatter proposal pending. | agents.md FAQ; Codex agents-md guide |
| F14 | high | 3-0 | Claude Code subagents run in their own context window; only the final result returns; fork inherits history but its tool calls stay out of the parent. | code.claude.com/docs/en/sub-agents |
| F15 | medium | 2-1 | One preprint (arXiv:2606.30689, 2026-06-28): mandatory per-line citations reduce lexical determinism versus uncited; cited traceSDD still more deterministic than Spec Kit. Hallucination-detection result refuted. | arxiv.org/abs/2606.30689 |

Refuted, excluded: Spec Kit nine-command enumeration; Kiro "Sync Files"; traceSDD hallucination-detection percentages.
