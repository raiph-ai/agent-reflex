---
name: agent-reflex-risk-gate
description: "Use before risky agent actions: publishing, production writes, destructive changes, credentials, financial actions, or external messages."
version: 0.1.0
author: Red Circle Studio
---

# Agent Reflex Risk Gate

Before external, destructive, production, credential, or financial actions, run:

```bash
agent-reflex risk --input /path/to/task.json
```

If `requires_human_approval` is true, ask before acting. If `requires_verification` is true, read back or test the target after the action.
