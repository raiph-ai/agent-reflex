---
name: agent-reflex-output-check
description: "Use after an agent task to check whether output satisfies the request and whether more tool work is needed."
version: 0.1.0
author: Red Circle Studio
---

# Agent Reflex Output Check

Run:

```bash
agent-reflex validate --input /path/to/result.json
```

If `requires_followup_tool_call` is true, continue work before finalizing.
