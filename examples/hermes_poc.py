from __future__ import annotations

import json
import os
from agent_reflex.providers import decide_with_provider


TASK = "Publish the IT Rockstar homepage update to the live production website and verify it."


def main() -> int:
    payload = {"task": TASK}
    route = decide_with_provider("route", payload)
    risk = decide_with_provider("risk", payload)
    skill = decide_with_provider("skill", payload)
    previous_order = os.environ.get("AGENT_REFLEX_PROVIDER_ORDER")
    os.environ["AGENT_REFLEX_PROVIDER_ORDER"] = "jev,rules"
    try:
        auto_policy = decide_with_provider("risk", payload, "auto")
    finally:
        if previous_order is None:
            os.environ.pop("AGENT_REFLEX_PROVIDER_ORDER", None)
        else:
            os.environ["AGENT_REFLEX_PROVIDER_ORDER"] = previous_order

    approval = "yes" if risk["requires_human_approval"] else "no"
    verification = "yes" if risk["requires_verification"] else "no"
    hermes_decision = (
        "Do not proceed without approval. If approved, execute and verify the live target before final response."
        if risk["requires_human_approval"]
        else "Proceed, then verify before final response if required."
    )

    print("Agent Reflex Local POC")
    print("=" * 24)
    print(f"Task: {TASK}\n")
    print("Route")
    print(f"- project: {route['project']}")
    print(f"- intent: {route['intent']}")
    print(f"- recommended_agent: {route['recommended_agent']}")
    print(f"- provider: {route['provider']}\n")
    print("Risk")
    print(f"- level: {risk['risk_level']}")
    print(f"- approval_required: {approval}")
    print(f"- verification_required: {verification}")
    print(f"- reason_codes: {', '.join(risk['reason_codes'])}\n")
    print("Skill recommendation")
    print(f"- skills: {', '.join(skill['skills'])}")
    print(f"- toolsets: {', '.join(skill['toolsets']) or 'none'}\n")
    print("Provider policy check")
    print(f"- requested_provider: auto")
    print(f"- attempted_providers: {', '.join(auto_policy.get('attempted_providers', ['rules']))}")
    print(f"- actual_provider: {auto_policy['provider']}")
    print(f"- fallback: {json.dumps(auto_policy['fallback'])}")
    print(f"- fallback_reason: {auto_policy.get('fallback_reason', 'none')}\n")
    print("Hermes decision")
    print(f"- {hermes_decision}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
