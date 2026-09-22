---
name: agent-reflex
description: "Use when routing, risk-scoring, validating, or gating Hermes agent actions with safe fallbacks."
version: 0.2.0
author: Red Circle Studio
---

# Agent Reflex

Agent Reflex adds typed decision hooks to Hermes without replacing Hermes judgment or safety controls.

## Use when

- Routing an incoming request to a project, agent, skill, or toolset.
- Preflighting risky actions: publishing, production writes, destructive changes, credentials, external messages, or financial actions.
- Deciding whether context belongs in memory, a skill, session history, or nowhere.
- Validating whether final output satisfies the user request before replying.

## Automatic Hermes mode

If `AGENT_REFLEX_HERMES_AUTO_ENABLED=true`, run a read-only preflight at the start of the session/task before risky actions or tool-heavy work:

```bash
agent-reflex preflight --input task.json
```

Use the returned `route`, `risk`, and `skill` decisions as guidance for which skills/tools to load, whether approval is required, and what must be verified. This preflight is advisory and must never execute the user action by itself.

## Primary path

Write the current task context to a small JSON file, then run one of:

```bash
agent-reflex route --input task.json
agent-reflex risk --input task.json
agent-reflex memory --input task.json
agent-reflex skill --input task.json
agent-reflex validate --input result.json
```

Use the returned JSON as guidance. Hermes remains the orchestrator and final authority.

## Fallback path

If `agent-reflex` is missing, times out, errors, or returns invalid JSON, do **not** block or break Hermes. Continue with this manual fallback:

1. Risk: require approval for external writes, production systems, destructive actions, financial actions, credentials, or public publishing.
2. Verification: read back or test any non-low-risk change before claiming success.
3. Memory: save stable preferences/facts only; reusable procedures become skills; task progress stays in session history.
4. Routing: load the narrowest relevant skill/toolset; ask only if ambiguity changes the action.
5. Output: if a stated requirement is unverified or missing, continue work before finalizing.

## Guardrails

- Agent Reflex recommends; Hermes enforces.
- Never auto-execute risky actions solely because Agent Reflex allowed them.
- Low confidence means use Hermes judgment or ask Ralph.
- Installation must be non-destructive: this skill works even when the CLI is absent.
