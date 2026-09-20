from __future__ import annotations

from typing import Any

from .cactus import CactusProvider
from .mock import MockProvider
from .openai_compatible import OpenAICompatibleProvider
from .stub import UnconfiguredProvider

PROVIDER_CLASSES = {
    "rules": MockProvider,
    "mock": MockProvider,
    "jev": lambda: UnconfiguredProvider("jev", "AGENT_REFLEX_JEV_URL", "AGENT_REFLEX_JEV_API_KEY"),
    "typesafe": lambda: UnconfiguredProvider("typesafe", "AGENT_REFLEX_JEV_URL", "AGENT_REFLEX_JEV_API_KEY"),
    "cactus": CactusProvider,
    "openai-compatible": OpenAICompatibleProvider,
}


def get_provider(name: str | None):
    key = (name or "rules").lower()
    try:
        provider_factory = PROVIDER_CLASSES[key]
    except KeyError as exc:
        raise ValueError(f"unknown provider: {name}") from exc
    return provider_factory()


def decide_with_provider(kind: str, payload: dict[str, Any], provider_name: str | None = None) -> dict[str, Any]:
    provider = get_provider(provider_name)
    try:
        return provider.decide(kind, payload)
    except Exception as exc:
        # ponytail: provider failures must not break agent flow; fall back to rules.
        fallback = MockProvider().decide(kind, payload)
        fallback["provider"] = "rules"
        fallback["fallback"] = True
        fallback["fallback_reason"] = f"{provider.name}: {exc}"
        return fallback
