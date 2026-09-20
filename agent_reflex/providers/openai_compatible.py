from __future__ import annotations

import os
from typing import Any


class OpenAICompatibleProvider:
    """Future HTTP adapter for OpenAI-compatible structured output endpoints.

    This is intentionally not wired to the network yet. The first release keeps
    provider contracts visible without adding credentials, deps, or failure risk.
    """

    name = "openai-compatible"

    def decide(self, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        missing = [env for env in ("AGENT_REFLEX_OPENAI_BASE_URL", "AGENT_REFLEX_OPENAI_API_KEY") if not os.environ.get(env)]
        if missing:
            raise RuntimeError(f"missing environment: {', '.join(missing)}")
        raise NotImplementedError("openai-compatible provider transport is not implemented yet")
