# Research query log

Research date: 2026-09-01  
Method: web search followed by opening/fetching primary pages. Search snippets
were discovery aids only. DevForgeAI names, repositories, documentation, and
legacy material were excluded from web queries.

| Query lane | Representative search intent | Selection rule | Opened evidence groups |
|---|---|---|---|
| QRY-01 | Official spec-driven development lifecycle, constitution, spec, plan, tasks, implementation, convergence | Project-primary/official documentation; current workflow pages | SDD-01, SDD-02, SDD-03, SDD-05 |
| QRY-02 | Epic, Story, backlog, Sprint, and readiness ownership | Official Scrum definition plus primary framework implementations | SDD-04, SDD-06, SDD-07 |
| QRY-03 | Architecture views, ADR lifecycle, source-tree and design context | Creator/official architecture guidance | SDD-08 |
| QRY-04 | Current Claude Code skills, custom commands, slash invocation, subagents, workflows, hooks, memory, MCP, plugins | Official `code.claude.com` documentation only | CLA-01 through CLA-07 |
| QRY-05 | Current Codex skills, custom prompts, slash commands, subagents, custom agents, hooks, AGENTS.md, MCP, plugins | Official OpenAI documentation domains only | CDX-01 through CDX-07 |
| QRY-06 | Agent Skills structure, progressive disclosure, references, validation | Open Agent Skills specification and official provider docs | CLA-01, CLA-02, CDX-02 |
| QRY-07 | Multi-agent scaling, decomposability, context isolation, context loss, retrieval | Current primary paper versions and original vendor research reports | REL-01 through REL-04 |
| QRY-08 | Hallucination reduction, self-correction, independent verification, agent evals | Original research and official evaluation guidance | REL-05 through REL-07 |
| QRY-09 | Requirements engineering, verification versus validation, bidirectional traceability | ISO abstract/definitions and NASA engineering guidance | REL-08 |
| QRY-10 | Artifact and build provenance, attestations, source/build binding | W3C, SLSA, and in-toto specifications | REL-09 |
| QRY-11 | Secure development, human approval, prompt injection, skill and dependency supply chain | NIST/OpenAI guidance and peer-reviewed USENIX research | REL-10 through REL-12 |
| QRY-12 | Measured AI coding productivity and runtime feedback/observability | Original study/update and official OpenTelemetry documentation | REL-13, REL-14 |
| QRY-13 | User-downloaded spec frameworks, hook implementations, skill catalogs, state engines, and provider adapters | Pin each local HEAD/origin; inspect read-only; separate primary implementations from catalogs; preserve dirty-state custody; run nothing | LRC-001 through LRC-027 |

## Retrieval limitations

- Public documentation and research can change after the access date.
- Some standards expose only an official abstract or selected definitions
  without purchase; this cache does not claim access to unavailable normative
  text.
- Vendor evaluation results are recorded with workload and internal-evaluation
  limits; they are not treated as universal performance guarantees.
- This cache stores bounded paraphrases and metadata rather than reproducing
  complete copyrighted pages.
- No live provider capability probe was executed in this research pass. The
  design requires such probes before implementation or a support claim.
- No downloaded repository was installed, activated, built, or tested. Static
  implementation observations do not establish runtime quality, scalability, or
  safe installation. Two corpus entries had no auditable committed content, and
  dirty repositories are explicitly identified in the local source record.
