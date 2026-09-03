# Source notes: assurance, provenance, and AI-agent reliability

Accessed: 2026-09-01  
Corpus rule: primary research, original standards, or official guidance preferred.

## REL-01 — Multi-agent performance is task-dependent

- Source: [Towards a Science of Scaling Agent Systems, v3](https://arxiv.org/abs/2512.08296)
- Source: [Google Research explainer](https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/)
- Source class: current research preprint and an official earlier-snapshot explainer

Documented evidence:

- The current v3, revised 2026-04-08, evaluates 260 configurations across six
  benchmarks, five canonical architectures, and three model families. Relative
  performance ranged from a gain of 80.8% on decomposable financial reasoning
  to a loss of 70.0% on sequential planning.
- Its architecture selector chose the best architecture for 87% of held-out
  configurations, but the reported cross-validated explanatory power was modest:
  R² 0.373 overall and 0.413 with its task-grounded capability metric.
- Architectures without centralized verification propagated errors more; task
  and tool characteristics affected the suitable architecture.
- The Google explainer describes an earlier 180-configuration snapshot. Its
  exact error-amplification figures should not be presented as the current v3
  result.

Design inference:

- Add a Delegation Planner and centralized Result Reconciler.
- Never encode “always use subagents.” Measure decomposability, shared-state
  coupling, tool use, evidence, and cost first.
- Treat the paper's selector as evidence that routing matters, not as a validated
  universal routing formula for this framework.

## REL-02 — Anthropic multi-agent research system

- Source: [How Anthropic built its multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)
- Source class: official vendor engineering report

Documented evidence:

- Anthropic reports that an Opus 4 lead with Sonnet 4 workers outperformed a
  single-agent Opus 4 baseline by 90.2% on its internal breadth-first research
  evaluation. The system used about 15 times the tokens of ordinary chat
  interactions; that token multiple is not a comparison to the single-agent
  research baseline.
- Its effective delegations state objective, output format, tool/source
  guidance, and boundaries. It warns that coding work is often less
  parallelizable than breadth-first research.

Design inference:

- Use parallel workers for evidence lanes with clear boundaries and preserve
  their original artifacts. Do not repeatedly compress evidence through layers
  of summaries.

Limit:

- The performance result is a vendor internal evaluation for a specific
  research workload, not a general coding guarantee.

## REL-03 — Context engineering and retrieval

- Source: [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- Source: [Lost in the Middle](https://arxiv.org/abs/2307.03172)
- Source: [Retrieval-Augmented Generation](https://arxiv.org/abs/2005.11401)
- Source class: official engineering guidance and original research

Documented evidence:

- Anthropic recommends high-signal context, just-in-time retrieval, structured
  notes, compaction, and context-isolated subagents, while warning that
  compaction can lose subtle facts.
- Lost in the Middle showed reduced use of relevant information when it was
  buried in long contexts in the studied models/settings.
- RAG showed factuality/specificity benefits from explicit retrieval in its
  evaluated knowledge-intensive tasks.

Design inference:

- Use a digest-bound Context Compiler and task packs instead of loading entire
  constitutions/architecture corpora or trusting memory.
- Retrieval improves access, not truth; preserve provenance and validate the
  retrieved content.

## REL-04 — Prefer measured workflow complexity

- Source: [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)
- Source: [SWE-agent](https://arxiv.org/abs/2405.15793)
- Source: [Agentless](https://arxiv.org/abs/2407.01489)
- Source class: official vendor guidance and original research

Documented evidence:

- Anthropic distinguishes prompt chaining, routing, parallelization,
  orchestrator-workers, and evaluator-optimizer patterns and advises adding
  complexity only when evaluation justifies it.
- SWE-agent demonstrated that the agent-computer interface materially affects
  coding results.
- Agentless demonstrated that a simpler localization, repair, and validation
  pipeline could outperform more elaborate contemporary agents on its evaluated
  SWE-bench Lite setting.

Design inference:

- Each skill should declare its orchestration pattern and why it is needed.
- Stable lifecycle transformations should prefer deterministic workflows with
  bounded agent judgment.

## REL-05 — Self-review is not external verification

- Source: [Chain-of-Verification Reduces Hallucination](https://aclanthology.org/2024.findings-acl.212/)
- Source: [Large Language Models Cannot Self-Correct Reasoning Yet](https://arxiv.org/abs/2310.01798)
- Source: [SelfCheckGPT](https://arxiv.org/abs/2303.08896)
- Source class: original peer-reviewed/preprint research

Documented evidence:

- Chain-of-Verification improved the evaluated factual tasks by drafting,
  independently answering verification questions, and revising.
- The self-correction study found that intrinsic correction without external
  feedback often failed or degraded the studied reasoning tasks.
- SelfCheckGPT uses sampling disagreement as a useful signal, not ground truth.
- These studies were not repository-level coding-agent evaluations. They support
  an independent-verification pattern but do not prove improved code acceptance.

Design inference:

- A fresh Evidence Verifier should check atomic claims against sources, tests,
  or system state. Model confidence or a same-context “double-check” must not be
  the sole acceptance gate.

## REL-06 — Evaluation-driven skills and workflows

- Source: [OpenAI evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices)
- Source: [OpenAI agent evals](https://developers.openai.com/api/docs/guides/agent-evals)
- Source: [Anthropic: Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
- Source: [Anthropic: Quantifying infrastructure noise in agentic coding evals](https://www.anthropic.com/engineering/infrastructure-noise)
- Source class: official vendor guidance

Documented evidence:

- OpenAI recommends production-like typical, edge, and adversarial cases,
  continuous evaluation, logging, and human-calibrated graders.
- Agent traces can evaluate routing, tool use, handoffs, guardrails, and final
  outcomes rather than grading only final prose.
- Anthropic recommends multiple trials, full traces, end-state grading, mixed
  code/model/human graders, calibrated rubrics, and living suites.
- Anthropic measured a six-percentage-point Terminal-Bench 2.0 swing between
  resource configurations and recommends skepticism for differences below three
  points until configurations match.

Design inference:

- Separate Product QA from workflow/skill evaluation.
- Keep the core eval format provider-neutral, with provider adapters for traces
  and graders.
- Create an independent Eval Designer/Oracle Custodian and protect held-out
  cases from the generator/implementation workflow.
- Pin provider/model, skill, harness, CPU/RAM, enforcement mode, timeout,
  concurrency, and network policy; run repeated fresh trials and distinguish
  infrastructure failure from behavioral failure.

Temporal note:

- OpenAI's page says its legacy Evals platform becomes read-only for existing
  users on 2026-10-31 and is scheduled to shut down on 2026-11-30. The framework
  should not bind its canonical schema to a vendor platform lifecycle.

## REL-07 — Executable specifications and oracle quality

- Source: [Test-Driven Development for Code Generation](https://arxiv.org/abs/2402.13521)
- Source: [Cucumber Gherkin reference](https://cucumber.io/docs/gherkin/reference/)
- Source: [Introducing SWE-bench Verified](https://openai.com/index/introducing-swe-bench-verified/)
- Source: [Why SWE-bench Verified no longer measures frontier coding capabilities](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/)
- Source class: original research and official project/vendor reports

Documented evidence:

- The TDD study found that including tests improved generation on the evaluated
  function-level benchmarks; that result does not establish repository-scale
  TDD effectiveness by itself.
- Cucumber examples can express user-observable executable specifications.
- Professional review improved SWE-bench task quality. OpenAI later audited 138
  tasks—27.6% of the 500-task set—that o3 did not consistently solve over 64
  independent runs, and reported material test-design and/or problem-description
  issues in 59.4% of those 138 audited tasks.

Design inference:

- Require an initial RED proof when the accepted project policy calls for TDD,
  while keeping the acceptance oracle independent of the implementation agent.
- Assess oracle quality with negative, mutation, and held-out cases. Record and
  mitigate benchmark/oracle leakage, but do not claim those checks establish the
  absence of model-training contamination. A green oracle can itself be wrong.

## REL-08 — Requirements and bidirectional traceability

- Source: [ISO/IEC/IEEE 29148:2018](https://www.iso.org/obp/ui?_escaped_fragment_=iso%3Astd%3Aiso-iec-ieee%3A29148%3Aed-2%3Av1%3Aen)
- Source: [NASA Systems Engineering Handbook appendix](https://www.nasa.gov/reference/system-engineering-handbook-appendix/)
- Source: [NASA bidirectional traceability guidance](https://swehb.nasa.gov/spaces/SWEHBVD/pages/102695427/SWE-052%2B-%2BBidirectional%2BTraceability)
- Source class: international standard and government engineering guidance

Documented evidence:

- The standard defines requirements lifecycle, derivation, upward/downward
  traceability, verification, and validation.
- NASA describes verification matrices and bidirectional links among needs,
  requirements, design, code, and tests.

Design inference:

- Every requirement needs a stable ID, rationale/source, owner, status,
  verification method, and linked result.
- Change impact and stale-derived-artifact detection are core services, not
  optional reports.

## REL-09 — Provenance and attestations

- Source: [W3C PROV Overview](https://www.w3.org/TR/prov-overview/)
- Source: [SLSA v1.2 Provenance](https://slsa.dev/spec/v1.2/provenance)
- Source: [in-toto Attestation Framework v1.2.0](https://github.com/in-toto/attestation/blob/v1.2.0/spec/v1/README.md)
- Source class: standards/project specifications

Documented evidence:

- W3C PROV models entities, activities, agents, derivations, versions, and
  provenance about provenance.
- The in-toto Statement binds a typed predicate to artifact subjects and
  digests, while its Envelope supplies authentication/serialization. The SLSA
  Provenance predicate describes build inputs, process, and builder claims.

Design inference:

- Use attestation-shaped records for generated specs, skills, tests, evidence,
  and releases: subject digest, sources, producer/tool/provider versions,
  transformation, verification, approval, and supersession.
- Borrowing this shape does not make the framework SLSA compliant; do not make
  that claim without satisfying and verifying the standard's requirements.
- A digest-bearing record is not automatically an authenticated attestation.
  Trust also requires an authenticated envelope/signature, verified producer
  identity, and an explicit consumer trust policy.

## REL-10 — Secure development and human authority

- Source: [NIST SP 800-218 / SSDF v1.1](https://csrc.nist.gov/projects/ssdf)
- Source: [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)
- Source: [NIST AI RMF Playbook](https://airc.nist.gov/airmf-resources/playbook/)
- Source: [NIST Human-AI Interaction appendix](https://airc.nist.gov/airmf-resources/airmf/appendices/app-c-ai-risk-management-and-human-ai-interaction/)
- Source: [OpenAI safety in building agents](https://developers.openai.com/api/docs/guides/agent-builder-safety)
- Source class: government and official vendor guidance

Documented evidence:

- SSDF v1.1 groups practices as Prepare the Organization; Protect the Software;
  Produce Well-Secured Software; and Respond to Vulnerabilities. It includes
  security requirements, risks, decisions, and provenance. The NIST project page
  also lists finalized SP 800-218A.
- AI RMF materials emphasize explicit roles, escalation, override, error, and
  go/no-go responsibilities. Human presence alone does not establish safety.
  NIST currently states that AI RMF 1.0 is being revised and that the Playbook
  will be updated after that revision.
- OpenAI recommends keeping untrusted data out of privileged instructions,
  schema-constraining node communication, tool approvals, guardrails, and trace
  evaluation. This source currently sits under OpenAI's legacy Agent Builder
  documentation; it is relevant official guidance, not provider-neutral
  empirical evidence.

Design inference:

- Security/privacy requirements must start in Product and Architecture, not
  appear only as a final scan.
- Human gates need named authority, evidence, alternatives, rationale, and
  scope; untrusted research/MCP content must never become privileged policy.

## REL-11 — Skills are supply-chain artifacts

- Source: [USENIX Security 2026: Detecting and Understanding Malicious Agent Skills in the Wild](https://www.usenix.org/conference/usenixsecurity26/presentation/liu-yi)
- Source class: peer-reviewed security research

Documented evidence:

- The study examined 98,380 skills and reports 157 confirmed malicious skills,
  632 vulnerabilities, and 13 attack techniques, including credential
  theft and adversarial instructions embedded in documentation. It combined
  static detection with dynamic verification.

Design inference:

- Add a Skill Supply-Chain Security Auditor separate from functional Skill
  Validator. Inspect source/version/digest, scripts, references, network and
  secret access, permissions, hidden behavior, install/update behavior, and
  documentation-to-behavior consistency; include sandboxed dynamic behavioral
  analysis plus quarantine and explicit release approval.

## REL-12 — Dependency provenance

- Source: [USENIX Security 2025: We Have a Package for You!](https://www.usenix.org/conference/usenixsecurity25/presentation/spracklen)
- Source class: peer-reviewed security research

Documented evidence:

- The study evaluated 16 models against two prompt datasets, producing 576,000
  Python and JavaScript samples, and found invented package names. The evaluated
  models/settings were selected in early 2024, so its rates are not estimates
  for current models. Merely observing that a package name now exists is not
  enough because an attacker could register an invented name.

Design inference:

- Add a dependency gate that verifies publisher/history, lock/digest,
  vulnerability and license posture, and explicit approval for new production
  dependencies.

## REL-13 — Measure actual delivery outcomes

- Source: [METR randomized developer productivity study](https://arxiv.org/abs/2507.09089)
- Source: [METR 2026 update](https://metr.org/blog/2026-02-24-uplift-update/)
- Source class: original research and author update

Documented evidence:

- The early-2025 randomized study covered 16 developers and 246 tasks; subjects
  averaged about five years of experience with their repositories and primarily
  used Cursor Pro with Claude 3.5/3.7 Sonnet. They took an estimated 19% longer
  with the evaluated AI tools, with a reported 95% confidence interval of +2%
  to +39%, despite expecting acceleration.
- METR calls the later study an unreliable signal and only weak evidence of
  improvement because of selection and time-measurement problems.

Design inference:

- Evaluate DevForgeAI on representative tasks using elapsed time, accepted
  quality, rework, defects, and human review cost—not perceived speed or a single
  generic benchmark.

## REL-14 — Operations closes the specification loop

- Source: [OpenTelemetry observability primer](https://opentelemetry.io/docs/concepts/observability-primer/)
- Source class: official project documentation

Documented evidence:

- Traces, metrics, and logs describe runtime behavior; service-level indicators
  and objectives connect measurements to reliability expectations.

Design inference:

- Architecture and Story phases should define observability obligations; Release
  should verify instrumentation; Operations should feed measured behavior and
  incidents into Change Assessment.
