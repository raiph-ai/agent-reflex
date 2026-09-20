# Agent Reflex

Typed decisions for autonomous agents.

Agent Reflex is a small, model-agnostic decision layer for Hermes Agent and other agent frameworks. It turns messy agent context into boring, structured decisions: route, risk, memory, skill selection, and output validation.

It is designed for Jev/Cactus-style models that excel at fast typed decisions, but it works today with a deterministic rules backend so the interface can be tested without any model account.

## Why

Most agents use the main reasoning model for everything. That is expensive and inconsistent for simple decisions like:

- Does this action need human approval?
- Which skill should load?
- Should this fact go into memory?
- Did the agent actually satisfy the user's request?
- Should this go to a specialist agent?

Agent Reflex gives those decisions a contract.

## Install locally

```bash
python3 -m pip install -e .
```

## CLI

```bash
agent-reflex risk --input examples/risk-production-write.json
agent-reflex memory --input examples/memory-preference.json
agent-reflex skill --input examples/skill-website-task.json
agent-reflex validate --input examples/output-validation.json
agent-reflex route --input examples/route-message.json
```

Every command emits JSON.

## Example

```bash
agent-reflex risk --input examples/risk-production-write.json
```

```json
{
  "decision": "requires_approval",
  "risk_level": "high",
  "requires_human_approval": true,
  "requires_verification": true,
  "reason_codes": ["external_write", "production_system"],
  "confidence": 0.9
}
```

## Hermes integration idea

The initial integration is a skill pack in `skills/`. A Hermes skill can call Agent Reflex before risky actions or after completion:

```text
Before publishing or production writes, run `agent-reflex risk` with task context. If high/critical, ask for approval. After the action, run `agent-reflex validate`.
```

Future integration can become a Hermes toolset/plugin:

```python
agent_reflex_decide(schema="risk", input={...})
```

## Backends

Current:

- `rules` — deterministic, no dependencies, testable

Planned:

- `jev` — TypeSafe/Jev structured decision endpoint
- `cactus` — Cactus-compatible structured decision endpoint
- `openai` / `anthropic` structured output
- `ollama` / local models

## MVP schemas

- `route` — classify and route a message/task
- `risk` — decide risk and approval requirements
- `memory` — decide whether to save, skillify, archive, or ignore
- `skill` — recommend agent skills/toolsets
- `validate` — verify output satisfies requested criteria

## Project posture

Ponytail mode: boring code first. No server, database, UI, dependency stack, or model lock-in until the contract proves useful.

## License

MIT
