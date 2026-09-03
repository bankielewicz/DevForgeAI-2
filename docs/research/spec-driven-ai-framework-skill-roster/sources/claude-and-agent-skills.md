# Source notes: Claude Code and Agent Skills

Accessed: 2026-09-01  
Source class: official Anthropic/Claude documentation and repositories, plus the open Agent Skills specification.

## CLA-01 — Agent Skills specification

- Source: [Agent Skills specification](https://agentskills.io/specification)

Documented evidence:

- A skill directory requires `SKILL.md` with `name` and `description`; optional
  `scripts/`, `references/`, and `assets/` support the workflow.
- Progressive disclosure loads metadata first, full instructions when activated,
  and other resources only as needed.
- The specification recommends focused references, shallow reference paths, a
  `SKILL.md` under 500 lines, and structural validation.

Design inference:

- Use this as the portable floor, not the full provider behavior contract.
- Keep detailed project/domain material outside the entry file and load it by
  explicit routing.

## CLA-02 — Claude skills and commands

- Source: [Extend Claude with skills](https://code.claude.com/docs/en/skills)
- Source: [Anthropic skill-creator at `53048666`](https://github.com/anthropics/skills/blob/53048666b05b4799081517d00e09e0a2dd688678/skills/skill-creator/SKILL.md)

Documented evidence:

- Skills can be selected automatically from their description or invoked as
  `/skill-name`.
- Custom commands have been merged into skills. Existing `.claude/commands/`
  files remain compatible, while new work should use skills.
- Claude extensions include invocation controls, argument substitution,
  supporting files, dynamic context injection, tool restrictions, isolated
  `context: fork` execution, and agent selection.
- A forked skill runs in the background by default. Background execution has a
  narrower tool surface and edits made by background tasks are outside session
  checkpoints.
- Claude's skills documentation recommends testing direct and automatic
  invocation and refining descriptions/instructions when triggering or output
  is wrong. Anthropic's pinned `skill-creator` package separately implements a
  fresh-session evaluation flow with with/without baselines, assertions with
  evidence, token/time benchmarks, blind version A/B, and trigger-description
  tests.

Design inference:

- A Claude phase skill can itself be the thin `/phase` entrypoint; a second
  wrapper command adds duplication without value.
- Skill Validator needs behavioral and trigger evals, not only frontmatter lint.
- Claude-specific frontmatter belongs in a generated adapter.

## CLA-03 — Choosing between guidance, skills, agents, MCP, and hooks

- Source: [Extend Claude Code](https://code.claude.com/docs/en/features-overview)

Documented evidence:

- `CLAUDE.md` is always-on guidance, path-scoped rules can load selectively,
  skills are on-demand workflows/knowledge, subagents isolate work, MCP supplies
  external capabilities/data, and hooks fire on lifecycle events.
- Anthropic explicitly distinguishes deterministic hook triggers from model-
  interpreted skill behavior and recommends hooks for mechanical guardrails.

Design inference:

- Do not treat a prompt prohibition as enforcement.
- Store canonical project truth in versioned artifacts and use hooks/CI for
  mechanically testable invariants.

## CLA-04 — Subagents and context isolation

- Source: [Create custom subagents](https://code.claude.com/docs/en/subagents)

Documented evidence:

- Subagents have separate context, instructions, tool/MCP restrictions, optional
  preloaded skills, and results summarized back to the caller.
- A fresh worker does not automatically receive the parent conversation,
  previously invoked skills, or every file the parent read.
- Short, accurate agent descriptions reduce startup context; least-authority
  tool and permission choices can specialize workers.

Design inference:

- Every delegation must contain exact inputs, governing context, output schema,
  evidence obligations, and stop rules.
- Context isolation reduces pollution but does not validate the result.

## CLA-05 — Dynamic workflows and teams

- Source: [Dynamic workflows](https://code.claude.com/docs/en/workflows)
- Source: [Agent teams](https://code.claude.com/docs/en/agent-teams)

Documented evidence:

- Dynamic workflows put fan-out, pipelines, aggregation, and intermediate state
  in a rerunnable program, but have runtime and interaction constraints.
- Agent teams enable more peer coordination but remain an experimental,
  higher-cost capability with lifecycle limitations.

Design inference:

- Use an ordinary skill plus a few bounded subagents for most phases. A
  provider-specific workflow adapter may help large research/audit jobs.
- Do not place a required mid-run human approval inside a no-interaction
  workflow or depend on experimental teams for the base lifecycle.

## CLA-06 — Hooks

- Source: [Hooks guide](https://code.claude.com/docs/en/hooks-guide)
- Source: [Hooks reference](https://code.claude.com/docs/en/hooks)

Documented evidence:

- Claude exposes many session, prompt, tool, subagent, task, compaction, file,
  worktree, and shutdown events.
- Handler types include command, HTTP, MCP, prompt, and agent. Anthropic
  recommends command hooks for deterministic production checks; agent hooks are
  experimental.
- All matching hooks run and should not be assumed to have a safe order.
- Command hook exit code `2` is the blocking signal available through the exit
  code alone for block-capable events. Supported event-specific decision JSON can
  also decide an event on a normal exit. Other failures, malformed output,
  timeouts, or missing executables may be nonblocking depending on the event.

Design inference:

- Put ordered checks in one tested dispatcher and prove failure behavior.
- A missing policy hook must be a detectable health failure, not a silent loss
  of enforcement.

## CLA-07 — Memory, context, MCP, plugins, and best practices

- Source: [Memory](https://code.claude.com/docs/en/memory)
- Source: [Context window](https://code.claude.com/docs/en/context-window)
- Source: [MCP](https://code.claude.com/docs/en/mcp)
- Source: [Plugins](https://code.claude.com/docs/en/plugins)
- Source: [Claude Code best practices](https://code.claude.com/docs/en/best-practices)

Documented evidence:

- `CLAUDE.md` and auto memory provide model context rather than deterministic
  enforcement. Context compaction can summarize or bound dynamically loaded
  material.
- MCP supplies external tools and data, while skills explain how to use them.
- Plugins bundle reusable provider capabilities and run trusted code with the
  user's authority.
- Best practices emphasize explicit verification criteria, separating
  exploration/planning from implementation, self-contained specifications,
  fresh sessions, and fresh reviewers.

Design inference:

- Every phase must resume from durable artifacts rather than transcript memory.
- Canonical custody must live in durable, versioned artifacts rather than auto
  memory or transcript state.
- Treat MCP/plugin content as a capability and supply-chain boundary.
- Cold/fresh independent review is appropriate for high-value acceptance, but
  must receive a complete, pinned review packet.
