# Local web interface

Agent Reflex includes a small local-only web UI for configuring provider policy without hand-editing environment variables.

It is intentionally lightweight: Python standard library only, no database, no auth server, and binds to `127.0.0.1` by default.

## Start

```bash
agent-reflex-web --host 127.0.0.1 --port 8765
```

Open:

```text
http://127.0.0.1:8765
```

Health check:

```bash
curl http://127.0.0.1:8765/health
```

## What it configures

The UI writes a local JSON config file:

```text
~/.agent-reflex/config.json
```

Supported values include:

```text
AGENT_REFLEX_PROVIDER
AGENT_REFLEX_PROVIDER_POLICY
AGENT_REFLEX_PROVIDER_ORDER
AGENT_REFLEX_JEV_URL
AGENT_REFLEX_JEV_API_KEY
AGENT_REFLEX_CACTUS_URL
AGENT_REFLEX_CACTUS_MODEL
AGENT_REFLEX_CACTUS_API_KEY
AGENT_REFLEX_OPENAI_BASE_URL
AGENT_REFLEX_OPENAI_MODEL
AGENT_REFLEX_OPENAI_API_KEY
```

Environment variables still win over the config file. This lets CI, shells, and deployment environments override the local UI safely.

## Recommended local values

```text
AGENT_REFLEX_PROVIDER=auto
AGENT_REFLEX_PROVIDER_POLICY=auto
AGENT_REFLEX_PROVIDER_ORDER=cactus,jev,openai-compatible,rules
AGENT_REFLEX_CACTUS_URL=http://127.0.0.1:8088/v1
AGENT_REFLEX_CACTUS_MODEL=needle-cq4
```

## Secret handling

The UI stores values in the local config file with `0600` file permissions when the OS allows it. This is convenient for a local MVP, but production/enterprise deployments should use a proper secret manager.

The UI does not display existing secret values back into the browser form. Leave a secret field blank to keep the existing saved value.

## Test decisions

The UI can run a sample decision from the browser. This is useful for confirming:

- provider order;
- fallback behavior;
- Cactus/Jev availability;
- deterministic rules output.

Example CLI equivalent:

```bash
agent-reflex risk --provider auto --input examples/risk-production-write.json
```

## Product note

The local web UI is an MVP configuration surface. The commercial product should evolve this into a hosted/team control plane with policy management, approval workflows, provider benchmarking, audit trails, and observability.
