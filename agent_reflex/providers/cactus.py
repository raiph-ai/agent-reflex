from __future__ import annotations

import os
from typing import Any

from .openai_compatible import OpenAICompatibleProvider


class CactusProvider(OpenAICompatibleProvider):
    name = "cactus"
    url_env = "AGENT_REFLEX_CACTUS_URL"
    key_env = "AGENT_REFLEX_CACTUS_API_KEY"
    model_env = "AGENT_REFLEX_CACTUS_MODEL"

    def decide(self, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not os.environ.get(self.key_env):
            os.environ[self.key_env] = "local-cactus"
        return super().decide(kind, payload)
