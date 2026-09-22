from __future__ import annotations

import os
from typing import Any

from .mock import MockProvider

AUTO_PROVIDER = "auto"
DEFAULT_AUTO_ORDER = ("cactus", "jev", "openai-compatible", "rules")
RISK_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def configured_provider_name(explicit_provider: str | None = None) -> str:
    """Resolve the requested provider without making CLI users pass flags every time."""
    return (explicit_provider or os.environ.get("AGENT_REFLEX_PROVIDER") or "rules").lower()


def provider_order(policy: str | None = None) -> list[str]:
    """Return ordered providers for auto/policy mode.

    Environment override:
      AGENT_REFLEX_PROVIDER_ORDER="cactus,jev,openai-compatible,rules"
    """
    raw = os.environ.get("AGENT_REFLEX_PROVIDER_ORDER")
    if raw:
        order = [item.strip().lower() for item in raw.split(",") if item.strip()]
    else:
        policy_name = (policy or os.environ.get("AGENT_REFLEX_PROVIDER_POLICY") or "auto").lower()
        if policy_name == "local-first":
            order = ["cactus", "rules"]
        elif policy_name == "cloud-first":
            order = ["jev", "openai-compatible", "rules"]
        elif policy_name == "rules-only":
            order = ["rules"]
        else:
            order = [str(item) for item in DEFAULT_AUTO_ORDER]

    # Rules must always be the terminal fallback in policy mode.
    if "rules" not in order:
        order.append("rules")
    return order


def apply_rules_guardrail(kind: str, candidate: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    """Overlay deterministic guardrails without hiding the chosen provider.

    Provider models may be smarter, but deterministic rules keep production writes,
    destructive actions, credentials, and public sends fail-safe.
    """
    if kind != "risk" or candidate.get("provider") == "rules":
        return candidate

    rules = MockProvider().decide(kind, payload)
    candidate_level = str(candidate.get("risk_level", "low"))
    rules_level = str(rules.get("risk_level", "low"))
    if RISK_RANK.get(rules_level, 0) > RISK_RANK.get(candidate_level, 0):
        candidate["risk_level"] = rules_level

    for field in ("requires_human_approval", "requires_verification"):
        candidate[field] = bool(candidate.get(field)) or bool(rules.get(field))

    reason_codes = list(candidate.get("reason_codes", []))
    for code in rules.get("reason_codes", []):
        if code not in reason_codes:
            reason_codes.append(code)
    candidate["reason_codes"] = reason_codes
    candidate["guardrail_provider"] = "rules"
    return candidate
