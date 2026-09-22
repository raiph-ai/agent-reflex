# Hermes integration

Agent Reflex integrates with Hermes as a safe skill-first companion.

## Install

```bash
agent-reflex-hermes-install --dry-run
agent-reflex-hermes-install --target "$HERMES_HOME/skills"
```

Then restart Hermes or run `/reset` so the skill index reloads.

## Use inside Hermes

When the `agent-reflex` skill is loaded, Hermes can call the CLI before or after tool work:

```bash
agent-reflex risk --input task.json
agent-reflex route --input task.json
agent-reflex validate --input result.json
```

## Automatic preflight toggle

Agent Reflex also supports an advisory automatic mode for Hermes sessions that load the skill:

```bash
agent-reflex preflight --input task.json
```

Enable it in the local web UI or config file:

```text
AGENT_REFLEX_HERMES_AUTO_ENABLED=true
AGENT_REFLEX_HERMES_AUTO_KINDS=route,risk,skill
```

When enabled, the skill instructs Hermes to run a read-only preflight before risky actions or tool-heavy work. The result gives Hermes structured guidance for routing, risk, skill selection, approval, and verification. It does not execute actions by itself, and Hermes remains responsible for approvals and verification.

## No-break fallback

If installation fails, the CLI is absent, or a provider fails, Hermes should continue with the manual checklist included in the skill:

- require approval for external writes, production systems, destructive actions, credentials, public publishing, or financial actions;
- verify non-low-risk changes before claiming success;
- save only durable preferences/facts to memory;
- load the narrowest relevant skill/toolset;
- continue work if any stated requirement is missing or unverified.

Agent Reflex recommends. Hermes enforces.
