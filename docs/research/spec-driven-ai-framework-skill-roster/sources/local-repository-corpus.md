# Source notes: downloaded local repository corpus

Audited: 2026-09-01  
Status: `STATIC_REVIEW_ONLY` — no repository was installed, activated, built, or
tested during this audit.

Evidence map: `CLM-039` through `CLM-050` in
[the claim ledger](../claim-ledger.md).

## Why retain this corpus

The downloaded repositories are useful when treated as pinned implementation
examples, counterexamples, or bibliography leads. They are not a benchmark and
their README claims are not runtime evidence. This record preserves:

- exact local Git identities and dirty-state custody;
- the distinction between framework, implementation, adapter, catalog, and
  empty/unusable lead;
- observable state/gate/hook/context mechanisms;
- whether a claim is source-declared, statically observed, user-observed, or not
  evaluated; and
- follow-up tests needed before adopting a pattern.

No DevForgeAI implementation or `docs/design/` material was inspected. Local
repository contents were treated as untrusted data and read only.

## Evidence vocabulary

| Token | Meaning |
|---|---|
| `STATIC_HEAD` | Observed in bytes committed at the recorded Git HEAD |
| `DECLARED` | Claimed by repository prose; not independently demonstrated |
| `USER_OBSERVED` | Reported by the user from prior use; environment/version is recorded when known |
| `PRESENT_NOT_RUN` | Executable tests or validators were observed but not run; this is availability, not a behavioral verdict |
| `NONE_OBSERVED` | No executable test/evaluator was found in the scoped static audit; this is not proof one cannot exist elsewhere |
| `NOT_EVALUATED` | Runtime behavior, output quality, scalability, or safety was not tested; this is the empirical verdict |
| `EMPTY` | No auditable committed content was present |

For a dirty repository, every file used as evidence was checked against `HEAD`.
Evidence came from an unchanged path or from `git show HEAD:<path>`; modified
working-tree bytes were not attributed to the recorded commit. Dirty-entry counts
are custody warnings, not claims that every entry changes content.

## Documentation depth rule

Do not create 27 equal-depth dossiers before the corpus is tested. Promote an
entry only as its evidence and design relevance increase:

| Level | Keep for | Required record |
|---|---|---|
| Inventory | Every downloaded directory | Name, origin, exact revision, dirty/empty state, classification, executable-evidence availability, and runtime evaluation |
| Static pattern | Relevant primary implementations and useful counterexamples | Exact paths, observable mechanism, failure boundary, portability caveat, and follow-up test |
| Runtime candidate | Shortlisted patterns being considered for adoption | Quarantined install, pinned provider/environment, executable fixtures, repeated results, and cleanup evidence |
| Adopted dependency or design | Components or patterns accepted into DevForgeAI | Human decision, version/digest, license and trust review, compatibility contract, rollback, and ongoing revalidation owner |

Catalogs normally stop at Inventory unless a specific bundled implementation is
audited separately. An entry that cannot advance still has value as bibliography
or as a regression/anti-pattern fixture.

## Pinned inventory

| ID | Repository | Exact local identity | Working-tree custody | Classification | Executable evidence | Runtime evaluation |
|---|---|---|---|---|---|---|
| LRC-001 | BMAD-METHOD | `cbb69e64e744ef545f174386ca793144ecbd1cfc`; `https://github.com/bmad-code-org/BMAD-METHOD` | 8 dirty entries; cited paths HEAD-clean | Primary lifecycle/spec framework | `PRESENT_NOT_RUN` | Prior unpinned version `USER_OBSERVED`; current snapshot `NOT_EVALUATED` |
| LRC-002 | BMAD_Openclaw | `75229d8260af78a268c226ed8e3808f9762a032c`; `https://github.com/ErwanLorteau/BMAD_Openclaw` | Clean | Derivative OpenClaw adapter with bundled BMAD content | `PRESENT_NOT_RUN` | `NOT_EVALUATED` |
| LRC-003 | Claude-hooks | Empty non-Git directory | No files | Empty lead | `EMPTY` | `NOT_EVALUATED` |
| LRC-004 | ECC | `2d46e80e0925c7be0907f18c1812311ac212a6c5`; `https://github.com/affaan-m/ECC` | 65 dirty entries; cited paths HEAD-clean | Multi-provider engineering distribution | `PRESENT_NOT_RUN` | `NOT_EVALUATED` |
| LRC-005 | OpenSpec | `e50bd0983dc8dc48250e3181f36e28450542f2ab`; `https://github.com/Fission-AI/OpenSpec` | 3 dirty entries; cited paths HEAD-clean | Lightweight delta-spec framework | `PRESENT_NOT_RUN` | `NOT_EVALUATED` |
| LRC-006 | andrej-karpathy-skills | `2c606141936f1eeef17fa3043a72095b4765b9c2`; `https://github.com/multica-ai/andrej-karpathy-skills` | Clean | Single instructional skill | `NONE_OBSERVED` | `NOT_EVALUATED` |
| LRC-007 | awesome-claude-code | `be13803f439fdc606e5ea5803f7e3bf1f2bbb0fb`; `https://github.com/hesreallyhim/awesome-claude-code` | 2 dirty entries; cited paths HEAD-clean; local checkout reported one commit behind origin during audit | Curated catalog | `PRESENT_NOT_RUN` mechanical catalog checks | `NOT_EVALUATED` |
| LRC-008 | awesome-claude-code-toolkit | `ebdf1d596d2cde5c5cceb32177e8d1cf4829e7d9`; `https://github.com/rohitg00/awesome-claude-code-toolkit/` | Clean | Mega-catalog with bundled snippets | `NONE_OBSERVED` | `NOT_EVALUATED` |
| LRC-009 | awesome-claude-plugins | `e521f7ada8d89abea888e67b93b4dcfbb977041f`; `https://github.com/composio-community/awesome-claude-plugins` | Clean | Marketplace/aggregator with some primary plugin code | `NONE_OBSERVED` at corpus root | `NOT_EVALUATED` |
| LRC-010 | buildwithclaude | `87d0fbfb9d0e037958d275c93637095015817845`; `https://github.com/davepoon/buildwithclaude` | Clean | Catalog plus schema/structure validators | `PRESENT_NOT_RUN` | `NOT_EVALUATED` |
| LRC-011 | claude-code-hooks | `b0b5f3717eb63b9bb2422af5b1be9f69bebf6b2b`; `https://github.com/karanb192/claude-code-hooks` | 1 dirty entry excluded from evidence | Claude hook implementation collection | `PRESENT_NOT_RUN` | `NOT_EVALUATED` |
| LRC-012 | claude-code-hooks-mastery | `052ad1cbd5aeb1ec4a1def22012d1293c6225625`; `https://github.com/disler/claude-code-hooks-mastery` | 33 dirty entries; modified evidence read from committed HEAD | Educational hook/subagent corpus | `NONE_OBSERVED` automated | `NOT_EVALUATED` |
| LRC-013 | claude-code-spec-workflow | `f3de74d8055120658ac199bfca865a3e1de9fd99`; `https://github.com/Pimzino/claude-code-spec-workflow` | Clean | Claude-specific prompt/spec workflow | `PRESENT_NOT_RUN` | `NOT_EVALUATED` |
| LRC-014 | claude-hooks | `8fbfd14c2a2271fe58a95c416b3b31880458c7bc`; `https://github.com/lasso-security/claude-hooks` | 1 dirty entry; installer evidence read from committed HEAD | Post-tool prompt-injection warning hook | `PRESENT_NOT_RUN` manual reporter | `NOT_EVALUATED` |
| LRC-015 | claude-skills | `aa8d778811a557a2c28ccadda4cf3d0bd028a4cc`; `https://github.com/alirezarezvani/claude-skills` | 1,512 dirty entries; cited evidence HEAD-clean or read from HEAD | Large cross-provider skill/plugin library | `PRESENT_NOT_RUN` | `NOT_EVALUATED` |
| LRC-016 | claude-tools | `1e7c556c8def984e434da6c59e217fcc218f08b0`; `https://github.com/tarekziade/claude-tools` | 2 dirty hook scripts; cited implementation/tests HEAD-clean | Deterministic context-compaction helper | `PRESENT_NOT_RUN` | `NOT_EVALUATED` |
| LRC-017 | codex-cli-hooks | `854e02abee6e2d9745b74f8456a5368416b0fb96`; `https://github.com/shanraisshan/codex-cli-hooks` | 1 dirty entry; cited paths HEAD-clean | Versioned Codex hook demo | `PRESENT_NOT_RUN` | `NOT_EVALUATED` |
| LRC-018 | gentle-ai | `72e0cccb1ff10a7cf6ca0270961e903c4d7eb686`; `https://github.com/Gentleman-Programming/gentle-ai` | Clean | Transactional workflow/review framework | `PRESENT_NOT_RUN` | `NOT_EVALUATED` |
| LRC-019 | get-shit-done | `bdcaab2c752d9a33a1a1ca9acf3a3c81fb991815`; `https://github.com/gsd-build/get-shit-done` | 24 dirty entries; cited paths HEAD-clean | Planning/execution workflow framework | `PRESENT_NOT_RUN` | `NOT_EVALUATED` |
| LRC-020 | gsd-core | Unborn `master`; `https://github.com/open-gsd/gsd-core` | No committed files | Empty placeholder | `EMPTY` | `NOT_EVALUATED` |
| LRC-021 | looper | `0ade75122dbfa0dd85bd296b58ceb3d91615fbc1`; `https://github.com/nexu-io/looper/` | 7 dirty entries; cited paths HEAD-clean or read from HEAD | Autonomous workflow/state framework | `PRESENT_NOT_RUN` | `NOT_EVALUATED` |
| LRC-022 | moai-adk | `7ad9f8534dc48719854c67e2b9a06db97b594eaf`; `https://github.com/modu-ai/moai-adk` | Clean | Spec/TDD framework with mechanical gates | `PRESENT_NOT_RUN` | `NOT_EVALUATED` |
| LRC-023 | oh-my-codex | `a62d5bd77bef6d2bc7df467dcae68082b8616239`; `https://github.com/Yeachan-Heo/oh-my-codex` | 6 dirty entries; cited paths HEAD-clean | Codex state/team/plugin framework | `PRESENT_NOT_RUN` | `NOT_EVALUATED` |
| LRC-024 | skills | `84fdeffd12f2ee307994d1eb6feb48173b6e0502`; `https://github.com/mattpocock/skills` | 4 dirty entries; cited paths HEAD-clean or read from HEAD | Composable prompt-skill collection | `NONE_OBSERVED` representative | `NOT_EVALUATED` |
| LRC-025 | spec-kit | `684b3d8e05263a7c1948d3d0699ab1cb4f77c3d5`; `https://github.com/github/spec-kit` | 6 dirty shell scripts; cited paths HEAD-clean | Spec framework plus state/event engine | `PRESENT_NOT_RUN` | `NOT_EVALUATED` |
| LRC-026 | spec-kitty | `eff63532607d2f292efc16e3f8bfd0e61e0544aa`; `https://github.com/Priivacy-ai/spec-kitty` | Clean | Mission/work-package framework with FSM | `PRESENT_NOT_RUN` | `NOT_EVALUATED` |
| LRC-027 | spec_driven_develop | `14f8c0f2be4421d11b8eb7474cde3ee00fb52b14`; `https://github.com/zhu1090093659/spec_driven_develop` | Clean | Markdown/prompt spec workflow | `PRESENT_NOT_RUN` framework-package checks | `NOT_EVALUATED` |

The local BMAD and spec-kit commits differ from the current branch revisions
pinned in [the web-source notes](spec-driven-methods.md). Findings below apply to
the local commits only.

## Framework implementation comparison

| Corpus | Evidence class | Pattern or mechanism | Boundary or counterexample | Evidence |
|---|---|---|---|---|
| LRC-001 BMAD | `STATIC_HEAD` + `DECLARED` | Broad lifecycle, explicit sprint states, bounded kernel/indexed context, scoped Epic packs, semantic reviewer/readiness gates | No committed Claude/Codex lifecycle-event hook implementation found; important gates remain model-mediated, and deterministic script failure can fall back to model judgment | `docs/reference/workflow-map.md:8-101`; `src/bmm-skills/plan/bmad-sprint-planning/references/readiness-gate.md:3-20`; `src/bmm-skills/plan/bmad-architecture/references/reviewer-gate.md:1-13`; `src/bmm-skills/plan/bmad-sprint-planning/scripts/sprint_plan.py:5-10,44-68,172-300,329-348,449-469`; `src/bmm-skills/plan/bmad-sprint-planning/SKILL.md:16-31`; `src/bmm-skills/plan/bmad-project-context/SKILL.md:19-53`; `src/bmm-skills/plan/bmad-project-context/references/kernel-contract.md:1-9`; `src/bmm-skills/ship/bmad-build/compile-epic-context.md:1-12,48-62`; `docs/reference/build-auto.md:8-24,44-53,71,91-103` |
| LRC-002 BMAD_Openclaw | `STATIC_HEAD` | Static dependency graph, persisted workflow state, fresh personas, constrained artifact writes | Arbitrary step loading can jump to the final step; completion then checks only the step number, so prompt-level “never skip” does not close the transition hole | `src/lib/workflow-registry.ts:327-352`; `src/tools/bmad-load-step.ts:46-96`; `src/tools/bmad-complete-workflow.ts:44-51`; `src/lib/orchestrator-rules.ts:6-33` |
| LRC-005 OpenSpec | `STATIC_HEAD` + `DECLARED` | Main specs plus change-local proposal/deltas/design/tasks; deterministic artifact graph; Git-native archive | Completion is largely file existence; validation/unfinished-task archive blocks can be overridden; semantic verification is an agent checklist | `docs/getting-started.md:12-98`; `src/core/artifact-graph/state.ts:6-36`; `src/core/archive.ts:1152-1341`; `skills/openspec-verify-change/SKILL.md:50-165` |
| LRC-025 spec-kit | `STATIC_HEAD` + `DECLARED` | Constitution/spec/plan/tasks workflow, stateful pause/fail/abort engine, JSONL events, provider-event generation | Engine execution does not itself establish semantic validation; missing hook handlers can succeed | `workflows/speckit/workflow.yml:1-77`; `src/specify_cli/workflows/engine.py:679-907,958-1246`; `src/specify_cli/events.py:655-712,1206-1421` |
| LRC-026 spec-kitty | `STATIC_HEAD` + `DECLARED` | Authoritative 27-transition FSM, guarded review/evidence/workspace transitions, atomic persistence, invocation hashes | Merge policies default to `warn` and permit `off`; some mission-gate documentation is proposed rather than shipped | `src/specify_cli/status/wp_state.py:129-207,297-387`; `src/specify_cli/status/store.py:431-520`; `src/specify_cli/invocation/record.py:135-177`; `src/specify_cli/invocation/executor.py:356-415`; `src/specify_cli/policy/config.py:19-118`; `docs/architecture/mission-gates.md:19-26` |
| LRC-027 spec_driven_develop | `STATIC_HEAD` + `DECLARED` | Clear intent-to-analysis-to-plan-to-progress workflow, parallel analyzers, task/issue/batch/PR mapping | Consumer gates are prompt-mediated; executable validation targets the framework package, and the approach is explicitly single-session | `plugins/spec-driven-develop/skills/spec-driven-develop/SKILL.md:53-99,166-227`; `scripts/validate.sh:3-50,385-401` |
| LRC-013 claude-code-spec-workflow | `STATIC_HEAD` + `DECLARED` | Requirements/design/tasks/implementation and separate bug workflow | Approval is marker/checklist based; completion rewrites a checkbox without independently proving tests or acceptance; task context can load all steering/spec files | `README.md:49-79`; `src/get-tasks.ts:116-220`; `src/task-generator.ts:149-275`; `src/dashboard/parser.ts:184-299` |
| LRC-018 gentle-ai | `STATIC_HEAD` + `DECLARED` | Mutation-free admission evaluator, revision/attempt budgets, strict hash-bound review receipts | SDD/review routes are optional and receipt evidence has force only when delivery policy consumes it | `internal/sddstatus/runtime_admission.go:49-152`; `internal/sddstatus/runtime_ledger.go:25-93`; `internal/reviewtransaction/receipt.go:15-137` |
| LRC-019 get-shit-done | `STATIC_HEAD` + `DECLARED` | Strong planning artifacts, fresh subagent contexts, wave execution, requirement-to-phase mapping, durable state/summaries | Some pivotal gates can continue after warning; verification is configurable; human gates can auto-approve; guard hooks are advisory and fail silently | `commands/gsd/execute-phase.md:18-58`; `get-shit-done/templates/state.md:47-121`; `get-shit-done/templates/requirements.md:53-68,99-108`; `sdk/src/research-gate.ts:1-93`; `sdk/src/phase-runner.ts:101-106,208-297`; `hooks/gsd-workflow-guard.js:3-12,76-93` |
| LRC-021 looper | `STATIC_HEAD` + `DECLARED` | Durable authoritative state, dependency authority, explicit human-veto window, idempotent dispatch, structured HITL, invariant/contract tests | Mechanical orchestration does not prove model task quality; optional auto-merge and same-channel checksum distribution raise trust risk | `docs/adr/0002-coordinator-authority-via-durable-labels.md:1-26`; `docs/adr/0004-dependency-gate-via-github-native-blocked-by.md:1-31`; `internal/coordinator/dispatch/dispatch.go:60-351`; `internal/worker/hitl.go:21-145` |
| LRC-022 moai-adk | `STATIC_HEAD` + `DECLARED` | Deterministic spec transitions, hard pre-tool path denial, exit-2 LSP gates, test/path evidence, drift detection, SHA-256 manifests | Broad/opinionated surface; some backends fail open and thresholds are configurable | `internal/spec/transitions.go:9-57,120-201`; `internal/hook/pre_tool.go:23-98`; `internal/lsp/hook/gate.go:38-253`; `internal/hook/evidence_writer.go:22-80`; `internal/spec/drift.go:18-112`; `internal/manifest/types.go:1-62`; `internal/manifest/hasher.go:11-42` |
| LRC-023 oh-my-codex | `STATIC_HEAD` + `DECLARED` | State/transition vocabulary, leases and atomic task claims, receipts/audit fields, input-size hardening, evidence budgets | The pinned provider-version note is stale and conflicts with both its HEAD hook output and the current official Codex hook contract; repeated Stop findings can eventually fail open; plugin/MCP/team runtime is a large trust surface | `docs/STATE_MODEL.md:12-175,224-255`; `src/team/state/tasks.ts:23-117`; `docs/codex-native-hooks.md:46-75,304-323`; `src/scripts/codex-native-hook.ts:751-800`; [current Codex hooks](https://learn.chatgpt.com/docs/hooks) |

## Provider, hook, and validation corpus

| Corpus | Evidence class | Merit | Important limit | Evidence |
|---|---|---|---|---|
| LRC-004 ECC | `STATIC_HEAD` + `DECLARED` | Concrete provider-adapter separation, hook-schema tests, deterministic configuration protection, small always-on context guidance | Large Claude hook graph versus a one-hook Codex bootstrap demonstrates that distribution parity is not behavior parity; dispatcher exceptions can fail open | `README.md:105-187,430-466`; `hooks/hooks.json:1-266`; `hooks/codex-hooks.json:1-18`; `scripts/hooks/config-protection.js:81-175` |
| LRC-011 claude-code-hooks | `STATIC_HEAD` | Explicit safety-level UX and tests that document malformed-input failure policy | Regex guards are not a sandbox; secret/Git guard exceptions emit `{}`, which makes no hook decision and leaves normal permission processing to continue | `SECURITY.md:11-19`; `hook-scripts/pre-tool-use/protect-secrets.js:183-217`; `hook-scripts/tests/pre-tool-use/git-safety.test.js:338-345` |
| LRC-012 hooks-mastery | `STATIC_HEAD` + `DECLARED` | Useful narrow subagent task contracts and broad event examples | The validator emits unsupported `result` fields and exits `1`; its JSON therefore does not decide the Stop event, and exit `1` does not block through the code alone. Exit `2`, or supported schema-valid decision JSON, is required | `README.md:294-302,571-669`; `.claude/hooks/validators/validate_new_file.py:209-227` (committed HEAD bytes); `.claude/agents/team/validator.md:1-29`; [current Claude hooks](https://code.claude.com/docs/en/hooks) |
| LRC-014 claude-hooks | `STATIC_HEAD` + `DECLARED` | Transparent deterministic pattern scanning after tool output | Post-tool timing cannot undo the action; missing dependencies/config, invalid regex/JSON, and runtime errors continue silently | `README.md:177-204`; `.claude/skills/prompt-injection-defender/hooks/defender-python/post-tool-defender.py:39-86,151-198,287-344` |
| LRC-017 codex-cli-hooks | `STATIC_HEAD` + `DECLARED` | Useful versioned syntax-drift and cwd test case | Active config and its own README disagree on handler schema; parse/fatal errors exit successfully; implementation is notification/context, not gating | `.codex/hooks.json:1-100`; `.codex/hooks/HOOKS-README.md:71-142`; `.codex/hooks/scripts/hooks.py:161-365` |
| LRC-010 buildwithclaude | `STATIC_HEAD` | Primary AJV structure/naming/duplicate validators and hook-event/schema checks | Several checks are advisory/nonblocking; structure does not establish behavioral correctness | `scripts/validate-skills.js:9-148`; `scripts/validate-hooks.js:23-220`; `.github/workflows/test-plugin.yml:15-19,46-106` |
| LRC-015 claude-skills | `STATIC_HEAD` + `DECLARED` | Layered CI pattern: structure, drift, smoke, dependency, security, and semantic review separated | Broad quality/readiness claims lack a representative behavioral suite; evaluator and dependency acquisition are insufficiently pinned | `.github/workflows/ci-quality-gate.yml:19-140`; `.github/workflows/skill-security-audit.yml:25-149,243-247`; `.github/workflows/skill-quality-review.yml:71-298` |
| LRC-016 claude-tools | `STATIC_HEAD` | Deterministic, fail-preserving context preprocessing with substantial committed tests | Transformation is lossy; its short SHA-1 fingerprint is neither semantic equivalence nor strong provenance | `ctools/trace_compactor.py:48-230`; `tests/test_trace_compactor.py:14-360`; `tests/test_cli.py:13-270` |

## Catalog and prompt-pattern evidence

- LRC-006, LRC-007, and LRC-008 are bibliography or inspiration only. A social
  post derivative, stars, age, or catalog inclusion is not safety or quality
  evidence.
- LRC-009 contains some inspectable primary plugin code, but marketplace entries
  do not pin every bundled source. Its `skill-bus` is useful for distinguishing
  dispatch from synthetic/model-mediated completion, not as proof that semantic
  work completed (`skill-bus/README.md:77-97,184-224`).
- LRC-024 is useful prompt-pattern evidence: thin user orchestration, model-
  invoked discipline skills, fresh phase contexts, separate review axes, and
  artifact-referencing handoffs (`README.md:184-212`;
  `skills/engineering/ask-matt/SKILL.md:13-90`;
  `skills/engineering/code-review/SKILL.md:1-87`). It has no representative
  behavioral evaluation suite.
- LRC-003 and LRC-020 contain no auditable implementation and should be excluded
  from design evidence.

## BMAD case note

### USR-001 — prior user experience

The user reports that an earlier BMAD experience worked reasonably at project
start but became less effective and more uncontrolled as the project grew, and
that effective gates/hooks were missing; in that experience, it appeared better
suited to smaller, less complicated projects. The tested BMAD version,
provider/model, configuration, project size, dependency density, and concrete
failure samples are not yet pinned. This is valuable experiential evidence and a
benchmark hypothesis, not a universal or current-version verdict.

### What the local snapshot establishes

- The broad literal statement “BMAD has no gates” does not fit LRC-001. The
  snapshot contains semantic readiness/review gates, deterministic sprint
  parsing/state rules, atomic
  state-writing machinery, verification instructions, and terminal states
  (`src/bmm-skills/plan/bmad-sprint-planning/references/readiness-gate.md:3-20`;
  `src/bmm-skills/plan/bmad-architecture/references/reviewer-gate.md:1-13`;
  `src/bmm-skills/plan/bmad-sprint-planning/scripts/sprint_plan.py:5-10,44-68,172-300,329-348,449-469`;
  `docs/reference/build-auto.md:8-24,44-53,91-103`).
- The narrower claim “this snapshot has no committed Claude/Codex lifecycle-
  event enforcement layer” is supported by the scoped static search. Its named
  activation hooks are prompt-step insertion, not provider `PreToolUse`,
  `PostToolUse`, session, permission, or stop hooks
  (`docs/how-to/customize-bmad.md:122-159,236-276`).
- Several gates remain model/instruction-mediated, and at least one deterministic
  script-failure path falls back to model judgment. That is materially different
  from fail-closed enforcement
  (`src/bmm-skills/plan/bmad-sprint-planning/SKILL.md:16-31`).
- The snapshot does have explicit scale mitigations: a roughly 150–200-
  instruction kernel ceiling, on-demand indexed knowledge, context validation/
  staleness tooling, fresh reviewers, and 800–1500-token Epic packs
  (`src/bmm-skills/plan/bmad-project-context/SKILL.md:19-53`;
  `src/bmm-skills/plan/bmad-project-context/references/kernel-contract.md:1-9`;
  `src/bmm-skills/ship/bmad-build/compile-epic-context.md:1-12,48-62`;
  `docs/reference/build-auto.md:71`).
- Static inspection cannot establish whether those mitigations remain effective
  as a real codebase, backlog, and dependency graph grow.

### Negative hook-search custody

At exact commit `cbb69e64e744ef545f174386ca793144ecbd1cfc`, these read-only
committed-tree checks both returned no matches:

```text
git -C tmp/repos/BMAD-METHOD grep -n -I -E 'PreToolUse|PostToolUse|SessionStart|PermissionRequest|hookSpecificOutput|hooks\.json|hooks\.toml' cbb69e64e744ef545f174386ca793144ecbd1cfc -- .
git -C tmp/repos/BMAD-METHOD ls-tree -r --name-only cbb69e64e744ef545f174386ca793144ecbd1cfc | rg '(^|/)\.(claude|codex)(/|$)|(^|/)hooks(/|$)|(^|/)hooks\.(json|toml|ya?ml)$'
```

This establishes only the recorded terms and conventional provider paths across
that committed tree. It cannot exclude an unusually named external adapter. The
dirty `.husky/pre-commit` path was not used: it is a repository-development Git
hook, not installed Claude/Codex lifecycle enforcement.

### Benchmark needed to evaluate the report

Hold provider/model, framework revision, permissions, hardware, timeouts, and
network constant. Vary:

- repository size and module count;
- accepted architecture/constitution size;
- Epic, Story, and sibling-spec fan-in;
- cross-component dependency density;
- session age, compaction, and fresh-session resume;
- concurrent work lanes and dirty working state; and
- hostile ambiguities, source conflicts, and out-of-scope mutation attempts.

Measure constraint misses, prohibited writes, gate-bypass rate, contradictory
edits, context tokens, elapsed/review time, rework, recovery after compaction,
reviewer disagreement, and independently accepted outcomes across repeated fresh
trials. Until that exists, use `USER_OBSERVED` and `NOT_EVALUATED`, not `PASS` or
`FAIL` for scalability.

## Cross-corpus design conclusions

1. A named “gate” must declare whether it is `BLOCK`, `REQUIRE_HUMAN`, `WARN`, or
   `OFF`, who may override it, and what happens on timeout, malformed output,
   missing handler, or infrastructure failure.
2. Keep separate: artifact exists; schema/structure passes; semantics are
   accepted; independent evidence passes; and an exact package is promoted.
3. Put transition legality, dependency readiness, IDs, hashes, atomic writes,
   leases, budgets, and receipts in deterministic services. Prompts may interpret
   or explain those facts, not replace them.
4. Use provider hooks as adapters into the same gate engine. Do not infer Claude
   and Codex parity from similar packaging or filenames.
5. A scalable context system needs stable IDs, dependency/applicability metadata,
   bounded packs, explicit exclusions, staleness invalidation, and fresh-session
   resume—not merely another summary document.
6. Preserve independent author, validator, acceptance, and promotion roles.
   Self-review, a checkbox rewrite, or a synthetic completion call is not
   acceptance.
7. Catalogs and structural validators are discovery/shape evidence only. Before
   install, pin source/revision/digest, quarantine executable content, inspect
   dependencies and permissions, and run behavioral/provider conformance tests.
8. The strongest patterns are selective rather than wholesale: OpenSpec deltas;
   BMAD/GSD planning and context packs; spec-kitty FSM; spec-kit provider events;
   gentle-ai admission/receipts; looper authority/HITL; and MoAI mechanical gates
   and provenance.
