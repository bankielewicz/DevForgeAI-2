# Source notes: Codex customization, skills, agents, and hooks

Accessed: 2026-09-01  
Source class: official OpenAI documentation.

## CDX-01 — Codex best practices and customization map

- Source: [Codex best practices](https://learn.chatgpt.com/guides/best-practices)
- Source: [Customization](https://learn.chatgpt.com/docs/customization/overview)

Documented evidence:

- A strong task supplies goal, relevant context, constraints, and a concrete
  done condition.
- `AGENTS.md` is for durable repository guidance; skills package repeatable
  workflows; MCP supplies external systems; subagents separate bounded agent
  threads/context from the main chat while sharing workspace state and inherited
  runtime policy; tests and review improve reliability.
- OpenAI recommends keeping one chat to a coherent outcome and avoiding a
  project-long context containing every intermediate log and decision.

Design inference:

- DevForgeAI's phase artifacts and fresh-session handoffs fit the documented
  context model.
- `AGENTS.md` should route to canonical artifacts and commands rather than
  becoming a second constitution.

## CDX-02 — Skills

- Source: [Build skills](https://learn.chatgpt.com/docs/build-skills)
- Source: [Build skills for plugins](https://developers.openai.com/plugins/build/skills)

Documented evidence:

- Codex follows the Agent Skills format and progressively loads a skill's
  metadata, then `SKILL.md`, then selected references/scripts/assets.
- Codex CLI/IDE explicit invocation uses `$skill-name` or the `/skills` picker;
  ChatGPT surfaces use `@skill-name`. Implicit selection depends on the skill
  description.
- Repository skills can live in `.agents/skills` at the current working
  directory and each ancestor through the repository root; user,
  administrator, and system scopes also exist.
- A skill should be focused on one job, declare inputs and outputs, state facts
  it must not infer, and specify when to question, stop, or decline.
- Representative tests should cover direct/indirect activation, incomplete
  input, non-activation, and unsupported-action edge cases.
- The initial skill metadata list is bounded, so a very large roster can have
  descriptions shortened or omitted from initial discovery.

Design inference:

- Use a small public roster and focused internal skills.
- `devforgeai-skill-validator` must measure discovery/trigger behavior and
  output semantics in addition to structural validity.

## CDX-03 — Custom prompts and slash commands

- Source: [Custom prompts](https://learn.chatgpt.com/docs/custom-prompts)
- Source: [Slash commands in Codex CLI](https://learn.chatgpt.com/docs/developer-commands?surface=cli)

Documented evidence:

- Custom prompt files that appeared as `/prompts:name` are deprecated; OpenAI
  directs reusable instructions to skills.
- Codex CLI retains built-in slash commands for session/product control, including
  skill selection, planning, review, status, permissions, agents, and hooks.

Design inference:

- Do not promise a custom `/brainstorm` surface in Codex by building on the
  deprecated prompt mechanism. Use `$brainstorm` and render that exact form in
  Codex handoffs.
- Claude and Codex invocation syntax should differ while artifact semantics stay
  identical.

## CDX-04 — Subagents and custom agents

- Source: [Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)

Documented evidence:

- Codex can delegate independent work to separate agent threads and consolidate
  their results in the main thread.
- OpenAI recommends read-heavy exploration, tests, triage, and summarization as
  starting uses, with caution around parallel writers and shared state.
- Subagents consume more tokens. A useful prompt declares work division,
  waiting behavior, and expected summary/output.
- Project custom agents are configured separately from skills. Their TOML files
  define `name`, `description`, and `developer_instructions`, and may configure
  supported session keys such as model/reasoning, `sandbox_mode`, `mcp_servers`,
  and `skills.config`. Omitted values inherit from the parent, while live parent
  sandbox and approval overrides are reapplied at spawn.

Design inference:

- Agent profiles and phase skills are different artifacts and need separate
  generators/validators.
- Introduce a decomposability/cost gate and a single reconciler rather than an
  unconditional “use subagents” rule.

## CDX-05 — Hooks

- Source: [Codex hooks](https://learn.chatgpt.com/docs/hooks)

Documented evidence:

- Codex exposes lifecycle hooks for sessions, prompts, supported local tool
  calls, compaction, subagents, stopping, and session end.
- Matching command hooks can run concurrently. By default, non-managed hooks
  require review, trust is bound to the current definition hash, and project
  hooks require a trusted project `.codex` layer. The documented
  `--dangerously-bypass-hook-trust` flag bypasses persisted trust for one
  invocation.
- Supported running handler types are command and MCP tool. Prompt and agent
  handler definitions are currently parsed but skipped.
- `PreToolUse` can block or rewrite supported local calls; `PostToolUse` occurs
  after side effects and cannot undo them.
- Tool hook coverage has documented exceptions, including hosted tool paths.
- Oversized hook context can spill to disk and consume model context; secrets
  should not be returned in hook output.
- For `mcp_tool` handlers, errors or missing/unavailable tools do not block the
  operation. Command-hook blocking depends on the event-supported protocol;
  unsupported fields may fail the hook while allowing the tool call.

Design inference:

- Codex hooks are useful guardrails, not a complete enforcement boundary.
- Keep critical policy in the deterministic CLI/CI, add hook-health tests, and
  bound all hook output.

## CDX-06 — `AGENTS.md`

- Source: [Custom instructions with AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)

Documented evidence:

- Codex loads a chain of global and project guidance, with more specific files
  closer to the working directory taking precedence within the guidance chain.
- The combined guidance has a configured size limit; nested files and concise
  routing are preferred over a massive root document.

Design inference:

- `AGENTS.md` should contain universal commands, repository orientation, and
  source-precedence/routing rules. It should reference, not duplicate, the
  accepted PRD, architecture, and Story corpus.

## CDX-07 — Plugins and MCP

- Source: [Build plugins](https://learn.chatgpt.com/docs/build-plugins)
- Source: [Plugin architecture](https://developers.openai.com/plugins/concepts/plugins)
- Source: [Model Context Protocol](https://learn.chatgpt.com/docs/extend/mcp)

Documented evidence:

- Skills are the workflow-authoring unit; plugins are installable distribution
  units that may package skills, MCP capabilities, and supported lifecycle
  configuration.
- MCP servers own live information, authentication, authorization, structured
  tools, and controlled actions. Skills own reusable method and decision flow.

Design inference:

- Develop provider adapters locally as skills; distribute a stable grouped
  capability as a versioned plugin only after behavioral and supply-chain
  conformance tests.
- External data/actions should not be represented as static skill knowledge.
