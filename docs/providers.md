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

## Phase II: provider policy

Agent Reflex should not force users to choose Jev **or** Cactus as an all-or-nothing decision. The recommended posture is a provider policy:

```bash
export AGENT_REFLEX_PROVIDER=auto
export AGENT_REFLEX_PROVIDER_POLICY=auto
export AGENT_REFLEX_PROVIDER_ORDER="cactus,jev,openai-compatible,rules"
```

In policy mode, Agent Reflex tries providers in order and falls back safely to `rules` when a provider is unavailable, unconfigured, times out, or returns invalid output.

Supported policy names:

- `auto` — local/provider-neutral default: `cactus, jev, openai-compatible, rules`
- `local-first` — prefer local/private decisions: `cactus, rules`
- `cloud-first` — prefer typed/cloud providers: `jev, openai-compatible, rules`
- `rules-only` — deterministic only

You can override the exact order with:

```bash
export AGENT_REFLEX_PROVIDER_ORDER="jev,cactus,rules"
```

`rules` is always appended as the terminal fallback.

## Deterministic guardrails

For risk decisions, Agent Reflex overlays deterministic `rules` guardrails even when a model provider succeeds. Provider models may improve classification quality, but rules preserve hard safety behavior for production writes, destructive actions, credentials, public sends, and other risky categories.

That means a provider can make the result smarter, but it should not make the system less safe.

## Current providers

### `rules`

Dependency-free deterministic backend. This is the default and the fallback path.

```bash
agent-reflex risk --provider rules --input examples/risk-production-write.json
```

Use this for tests, demos, safe installs, and CI.

### `auto`

Policy-driven provider selection.

```bash
agent-reflex risk --provider auto --input examples/risk-production-write.json
```

If Cactus/Jev/OpenAI-compatible providers are unavailable, the command still returns a usable `rules` decision with `fallback: true`.

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

Cactus can run as a local OpenAI-compatible HTTP server:

```bash
brew install cactus-compute/cactus/cactus
cactus serve Cactus-Compute/needle --port 8088 --no-cloud-handoff
```

Expected environment:

```bash
export AGENT_REFLEX_CACTUS_URL="http://127.0.0.1:8088/v1"
export AGENT_REFLEX_CACTUS_MODEL="needle-cq4"
```

`AGENT_REFLEX_CACTUS_API_KEY` is optional for a local server; Agent Reflex supplies a local placeholder when absent.

Current behavior: calls the OpenAI-compatible endpoint and falls back to `rules` if Cactus returns empty/non-JSON content or is unavailable. A future Cactus-specific tool-call adapter should parse Needle's native tool-call responses.

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
6. Provider policy should make the project more durable than any one model vendor.

## CLI pattern

```bash
agent-reflex route --provider rules --input task.json
agent-reflex risk --provider auto --input task.json
agent-reflex risk --provider jev --input task.json
agent-reflex validate --provider openai-compatible --input result.json
```

If a non-rules provider is unavailable, the command still returns a usable `rules` decision with `fallback: true`.
