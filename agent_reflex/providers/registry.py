from __future__ import annotations

from typing import Any

from .cactus import CactusProvider
from .mock import MockProvider
from .openai_compatible import OpenAICompatibleProvider
from .policy import AUTO_PROVIDER, apply_rules_guardrail, configured_provider_name, provider_order
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
    key = configured_provider_name(name)
    try:
        provider_factory = PROVIDER_CLASSES[key]
    except KeyError as exc:
        raise ValueError(f"unknown provider: {name}") from exc
    return provider_factory()


def decide_with_provider(kind: str, payload: dict[str, Any], provider_name: str | None = None) -> dict[str, Any]:
    provider_key = configured_provider_name(provider_name)
    if provider_key == AUTO_PROVIDER:
        return decide_with_policy(kind, payload)

    provider = get_provider(provider_key)
    try:
        result = provider.decide(kind, payload)
        return apply_rules_guardrail(kind, result, payload)
    except Exception as exc:
        return _rules_fallback(kind, payload, f"{provider.name}: {exc}")


def decide_with_policy(kind: str, payload: dict[str, Any], policy: str | None = None) -> dict[str, Any]:
    errors: list[str] = []
    for name in provider_order(policy):
        provider = get_provider(name)
        try:
            result = provider.decide(kind, payload)
            result = apply_rules_guardrail(kind, result, payload)
            if errors:
                result["fallback"] = name == "rules"
                result["fallback_reason"] = "; ".join(errors)
                result["attempted_providers"] = provider_order(policy)
            return result
        except Exception as exc:
            errors.append(f"{provider.name}: {exc}")

    return _rules_fallback(kind, payload, "; ".join(errors) or "no policy provider returned a decision")


def _rules_fallback(kind: str, payload: dict[str, Any], reason: str) -> dict[str, Any]:
    fallback = MockProvider().decide(kind, payload)
    fallback["provider"] = "rules"
    fallback["fallback"] = True
    fallback["fallback_reason"] = reason
    return fallback
