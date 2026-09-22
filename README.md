# Agent Reflex

Fast structured decision hooks for Hermes Agent — route, guard, and score agent actions before the big model thinks.

Agent Reflex is a small, model-agnostic decision layer for Hermes Agent and other agent frameworks. It turns messy agent context into boring, structured decisions: route, risk, memory, skill selection, and output validation.

It is designed for Jev/Cactus-style models that excel at fast typed decisions, but it works today with a deterministic rules backend so the interface can be tested without any model account. The marketable posture is provider-neutral: Agent Reflex should get better as more Jev-like competitors appear, not become locked to one of them.

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
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -e .
```

## Documentation site

Static documentation lives in `docs/` and is deployable with GitHub Pages. The Pages workflow publishes it from GitHub Actions whenever `docs/**` changes.

## Hermes integration

Install the bundled Hermes skill safely:

```bash
agent-reflex-hermes-install --dry-run
agent-reflex-hermes-install --target "$HERMES_HOME/skills"
```

If a skill already exists, the installer refuses to overwrite it unless you pass `--force`. With `--force`, it creates `agent-reflex.bak` first. The installer stages files in a temporary directory and only moves the completed skill into place, so a failed install should not leave Hermes half-modified.

After install, restart or `/reset` Hermes so the skill index reloads.

### Fallback behavior

The bundled `agent-reflex` Hermes skill is intentionally safe if the CLI is absent or broken. If `agent-reflex` fails, Hermes should continue with the skill's manual fallback checklist:

- require approval for external writes, production systems, destructive changes, credentials, public publishing, or financial actions;
- verify non-low-risk changes before claiming success;
- save only durable preferences/facts to memory;
- load the narrowest relevant skill/toolset;
- continue work if any stated requirement is missing or unverified.

This means Agent Reflex can improve Hermes decisions without becoming a single point of failure.

## CLI

```bash
agent-reflex risk --input examples/risk-production-write.json
agent-reflex memory --input examples/memory-preference.json
agent-reflex skill --input examples/skill-website-task.json
agent-reflex validate --input examples/output-validation.json
agent-reflex route --input examples/route-message.json
agent-reflex check result.json
agent-reflex-web --host 127.0.0.1 --port 8765
python examples/hermes_poc.py
```

Every decision command emits JSON with a stable envelope: `decision`, `confidence`, `provider`, `thresholds`, and `fallback`.

## Local web UI

Agent Reflex includes a local-only configuration UI:

```bash
agent-reflex-web --host 127.0.0.1 --port 8765
```

Open `http://127.0.0.1:8765` to edit provider policy, Cactus/Jev/OpenAI-compatible settings, and run a test decision. The UI writes `~/.agent-reflex/config.json`; environment variables still override config values. See [`docs/web-ui.md`](docs/web-ui.md).

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

## Backends and provider policy

Current:

- `rules` — deterministic, no dependencies, testable
- `auto` — policy-driven provider selection with safe fallback to `rules`

Provider adapters are documented in [`docs/providers.md`](docs/providers.md):

- `jev` / `typesafe` — TypeSafe/Jev structured decision endpoint
- `cactus` — Cactus-compatible structured decision endpoint or local runtime
- `openai-compatible` — OpenAI-compatible structured output endpoint
- `ollama` / local models — future local adapters

Recommended provider-neutral mode:

```bash
export AGENT_REFLEX_PROVIDER=auto
export AGENT_REFLEX_PROVIDER_POLICY=auto
export AGENT_REFLEX_PROVIDER_ORDER="cactus,jev,openai-compatible,rules"
agent-reflex risk --input examples/risk-production-write.json
```

Non-rules providers fail safe to `rules` when credentials or transports are missing. Risk decisions also receive deterministic rules guardrails so a model provider can improve the decision without weakening safety.

## Market posture

Agent Reflex should be positioned as a provider-neutral reflex layer, not a wrapper around one model vendor. See [`docs/market.md`](docs/market.md) for the open-source differentiation and commercial/control-plane path.

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
