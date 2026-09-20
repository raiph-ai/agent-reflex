# Provider adapters

Agent Reflex is provider-agnostic. The durable contract is the decision envelope, not any one model API.

Every provider returns JSON with these fields:

```json
{
  "decision": "requires_approval",
  "confidence": 0.9,
  "provider": "rules",
  "thresholds": {},
  "fallback": false
}
```

## Current provider

### `rules`

Dependency-free deterministic backend. This is the default and the fallback path.

```bash
agent-reflex risk --provider rules --input examples/risk-production-write.json
```

Use this for tests, demos, and safe installs.

## Planned providers

### `jev` / `typesafe`

Intended for Jev / TypeSafe-style System One decision endpoints.

Expected environment:

```bash
export AGENT_REFLEX_JEV_URL="https://..."
export AGENT_REFLEX_JEV_API_KEY="..."
```

Current behavior: if these are missing or the provider fails, Agent Reflex falls back to `rules` and sets:

```json
{
  "fallback": true,
  "fallback_reason": "jev: missing environment: AGENT_REFLEX_JEV_URL, AGENT_REFLEX_JEV_API_KEY"
}
```

### `cactus`

Reserved for Cactus-compatible structured decision endpoints or local runtimes.

Expected environment:

```bash
export AGENT_REFLEX_CACTUS_URL="http://127.0.0.1:..."
export AGENT_REFLEX_CACTUS_API_KEY="optional-or-runtime-specific"
```

Current behavior: safe fallback to `rules`.

### `openai-compatible`

Reserved for OpenAI-compatible structured output APIs.

Expected environment:

```bash
export AGENT_REFLEX_OPENAI_BASE_URL="https://api.openai.com/v1"
export AGENT_REFLEX_OPENAI_API_KEY="..."
```

Current behavior: safe fallback to `rules`.

## Provider design rules

1. Provider failures must not break Hermes.
2. Missing credentials must not break local demos or CI.
3. Providers return the stable decision envelope.
4. Hermes remains the orchestrator and safety authority.
5. Real provider transports should be small: input JSON in, typed decision JSON out.

## CLI pattern

```bash
agent-reflex route --provider rules --input task.json
agent-reflex risk --provider jev --input task.json
agent-reflex validate --provider openai-compatible --input result.json
```

If a non-rules provider is unavailable, the command still returns a usable `rules` decision with `fallback: true`.
