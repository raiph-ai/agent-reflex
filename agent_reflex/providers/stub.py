from __future__ import annotations

from typing import Any

from agent_reflex.config import get_setting


class UnconfiguredProvider:
    """Placeholder for optional providers that are not configured yet."""

    def __init__(self, name: str, url_env: str, key_env: str):
        self.name = name
        self.url_env = url_env
        self.key_env = key_env

    def decide(self, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        missing = [env for env in (self.url_env, self.key_env) if not get_setting(env)]
        if missing:
            raise RuntimeError(f"missing environment: {', '.join(missing)}")
        raise NotImplementedError(f"{self.name} provider transport is not implemented yet")
