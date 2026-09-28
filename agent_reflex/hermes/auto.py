from __future__ import annotations

from typing import Any

from agent_reflex.config import get_bool_setting, get_setting
from agent_reflex.providers import decide_bundle_with_provider
from agent_reflex.schema import KINDS

DEFAULT_PREFLIGHT_KINDS = ("route", "risk", "skill")
LOW_CONFIDENCE_THRESHOLD = 0.7


def automatic_enabled() -> bool:
    """Return whether Hermes automatic preflight mode is enabled."""
    return get_bool_setting("AGENT_REFLEX_HERMES_AUTO_ENABLED", False)


def configured_preflight_kinds() -> list[str]:
    raw = get_setting("AGENT_REFLEX_HERMES_AUTO_KINDS", ",".join(DEFAULT_PREFLIGHT_KINDS)) or ""
    kinds: list[str] = []
    for item in raw.split(","):
        kind = item.strip().lower()
        if kind in KINDS and kind not in kinds:
            kinds.append(kind)
    return kinds or list(DEFAULT_PREFLIGHT_KINDS)


def preflight(payload: dict[str, Any], provider: str | None = None, *, force: bool = False) -> dict[str, Any]:
    """Run the configured Hermes preflight decisions.

    This is intentionally a read-only helper. It never executes user actions;
    it gives Hermes structured routing/risk/skill guidance before normal reasoning or tool use.
    """
    enabled = automatic_enabled()
    if not enabled and not force:
        return {
            "enabled": False,
            "skipped": True,
            "reason": "AGENT_REFLEX_HERMES_AUTO_ENABLED is false",
            "decisions": {},
        }

    kinds = configured_preflight_kinds()
    decisions = decide_bundle_with_provider(payload, provider, kinds)

    plan = routing_plan(decisions)
    return {
        "enabled": enabled,
        "skipped": False,
        "provider": provider or get_setting("AGENT_REFLEX_PROVIDER", "auto"),
        "bundled": True,
        "kinds": list(decisions),
        "routing_plan": plan,
        "decisions": decisions,
    }


def routing_plan(decisions: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Summarize preflight decisions into a simple agent routing instruction."""
    route = decisions.get("route", {})
    risk = decisions.get("risk", {})
    skill = decisions.get("skill", {})

    low_confidence = [
        kind for kind, decision in decisions.items()
        if float(decision.get("confidence", 0) or 0) < LOW_CONFIDENCE_THRESHOLD
    ]
    requires_approval = bool(risk.get("requires_human_approval"))
    requires_verification = bool(risk.get("requires_verification"))
    recommended_agent = route.get("recommended_agent") or "current_agent"
    skills = skill.get("skills") or []
    toolsets = skill.get("toolsets") or []
    low_risk_fast_path = (
        not requires_approval
        and not requires_verification
        and str(risk.get("risk_level", "low")) == "low"
        and (not skills or skills == ["none"])
    )
    if low_risk_fast_path:
        low_confidence = []

    if requires_approval:
        next_action = "escalate_to_full_agent_for_approval_and_execution"
    elif low_confidence:
        next_action = "escalate_to_full_agent_for_judgment"
    elif skills and skills != ["none"]:
        next_action = "load_recommended_skills_then_continue"
    else:
        next_action = "continue_fast_path"

    return {
        "default_first": True,
        "next_action": next_action,
        "recommended_agent": recommended_agent,
        "requires_human_approval": requires_approval,
        "requires_verification": requires_verification,
        "low_confidence_decisions": low_confidence,
        "skills": skills,
        "toolsets": toolsets,
    }
