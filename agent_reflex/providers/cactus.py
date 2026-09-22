from __future__ import annotations

from typing import Any

from agent_reflex.config import get_setting

from .openai_compatible import OpenAICompatibleProvider


class CactusProvider(OpenAICompatibleProvider):
    name = "cactus"
    url_env = "AGENT_REFLEX_CACTUS_URL"
    key_env = "AGENT_REFLEX_CACTUS_API_KEY"
    model_env = "AGENT_REFLEX_CACTUS_MODEL"

    def decide(self, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not get_setting(self.key_env):
            return self._decide_with_local_key(kind, payload)
        return super().decide(kind, payload)

    def _decide_with_local_key(self, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        import os

        previous = os.environ.get(self.key_env)
        os.environ[self.key_env] = "local-cactus"
        try:
            return super().decide(kind, payload)
        finally:
            if previous is None:
                os.environ.pop(self.key_env, None)
            else:
                os.environ[self.key_env] = previous
