from __future__ import annotations

from dataclasses import dataclass
from typing import Any


HIGH_RISK_WORDS = {
    "delete", "remove", "publish", "deploy", "production", "payment", "charge",
    "email", "send", "external", "public", "database", "credential", "secret",
}
CRITICAL_WORDS = {"delete", "drop", "wipe", "force-push", "revoke", "terminate"}
MEMORY_WORDS = {"prefers", "preference", "always", "default", "likes", "dislikes"}
TEMP_WORDS = {"today", "tomorrow", "this week", "draft", "temporary", "todo", "progress"}


@dataclass(frozen=True)
class DecisionEngine:
    """Deterministic rules backend.

    ponytail: this keeps the public contract useful while model backends mature.
    """

    def route(self, payload: dict[str, Any]) -> dict[str, Any]:
        text = _text(payload)
        project = _project(text)
        intent = _intent(text)
        return {
            "decision": "route",
            "project": project,
            "intent": intent,
            "recommended_agent": _agent(intent, project),
            "priority": "high" if any(w in text for w in ["urgent", "asap", "broken", "down"]) else "normal",
            "confidence": 0.78 if intent != "general" else 0.55,
        }

    def risk(self, payload: dict[str, Any]) -> dict[str, Any]:
        text = _text(payload)
        reason_codes = []
        if any(w in text for w in ["publish", "send", "email", "external", "public"]):
            reason_codes.append("external_write")
        if any(w in text for w in ["production", "live", "deploy"]):
            reason_codes.append("production_system")
        if any(w in text for w in ["delete", "remove", "drop", "wipe"]):
            reason_codes.append("destructive_action")
        if any(w in text for w in ["payment", "charge", "invoice", "bank"]):
            reason_codes.append("financial_action")
        if any(w in text for w in ["secret", "credential", "token", "password"]):
            reason_codes.append("secret_or_credential")

        if any(w in text for w in CRITICAL_WORDS):
            level = "critical"
        elif reason_codes or any(w in text for w in HIGH_RISK_WORDS):
            level = "high"
        elif any(w in text for w in ["edit", "update", "write", "create"]):
            level = "medium"
        else:
            level = "low"

        return {
            "decision": "requires_approval" if level in {"high", "critical"} else "allowed",
            "risk_level": level,
            "requires_human_approval": level in {"high", "critical"},
            "requires_verification": level != "low",
            "reason_codes": reason_codes or ["no_high_risk_markers"],
            "confidence": 0.9 if reason_codes else 0.68,
        }

    def memory(self, payload: dict[str, Any]) -> dict[str, Any]:
        text = _text(payload)
        if any(w in text for w in TEMP_WORDS):
            return _memory("do_not_save", "session_history", "temporary_or_progress")
        if any(w in text for w in MEMORY_WORDS):
            return _memory("save", "user_profile", "stable_preference")
        if "workflow" in text or "procedure" in text or "steps" in text:
            return _memory("skillify", "skill", "reusable_procedure")
        return _memory("do_not_save", "none", "not_durable_enough")

    def skill(self, payload: dict[str, Any]) -> dict[str, Any]:
        text = _text(payload)
        skills: list[str] = []
        toolsets: list[str] = []
        if any(w in text for w in ["website", "wordpress", "bricks", "page"]):
            skills += ["wordpress-site-deployment", "bricks-browser-verify"]
            toolsets += ["browser", "web"]
        if any(w in text for w in ["github", "repo", "pull request", "pr"]):
            skills.append("github-workflows")
            toolsets += ["terminal", "file"]
        if any(w in text for w in ["email", "inbox"]):
            skills.append("email-inbox-triage")
        if any(w in text for w in ["draft", "rewrite", "blog", "copy"]):
            skills.append("stop-slop")
        if not skills:
            skills.append("none")
        return {
            "decision": "skill_recommendation",
            "skills": _dedupe(skills),
            "toolsets": _dedupe(toolsets),
            "confidence": 0.74 if skills != ["none"] else 0.45,
        }

    def validate(self, payload: dict[str, Any]) -> dict[str, Any]:
        required = [str(x).lower() for x in payload.get("requirements", [])]
        output = str(payload.get("output", "")).lower()
        missing = [r for r in required if r and r not in output]
        verified = any(w in output for w in ["verified", "tested", "passed", "200", "green"])
        passes = not missing and (verified or not payload.get("requires_verification"))
        return {
            "decision": "passes" if passes else "needs_more_work",
            "passes": passes,
            "missing_requirements": missing,
            "requires_followup_tool_call": bool(missing or (payload.get("requires_verification") and not verified)),
            "confidence": 0.72,
        }


def decide(kind: str, payload: dict[str, Any]) -> dict[str, Any]:
    engine = DecisionEngine()
    try:
        fn = getattr(engine, kind)
    except AttributeError as exc:
        raise ValueError(f"unknown decision kind: {kind}") from exc
    return fn(payload)


def _text(payload: dict[str, Any]) -> str:
    return " ".join(str(v) for v in payload.values() if isinstance(v, (str, int, float, bool))).lower()


def _project(text: str) -> str:
    for name in ["it rockstar", "red circle", "nsbe", "emery", "bioticman", "lov3", "hermes"]:
        if name in text:
            return name.replace(" ", "_")
    return "unknown"


def _intent(text: str) -> str:
    if any(w in text for w in ["publish", "post", "draft", "rewrite", "copy"]):
        return "content"
    if any(w in text for w in ["website", "page", "wordpress", "bricks"]):
        return "website_update"
    if any(w in text for w in ["github", "repo", "code", "bug", "test"]):
        return "software_delivery"
    if any(w in text for w in ["email", "inbox", "reply"]):
        return "communications"
    return "general"


def _agent(intent: str, project: str) -> str:
    if project == "emery":
        return "emery"
    if intent == "software_delivery":
        return "azze"
    return "raiph"


def _memory(action: str, target: str, reason: str) -> dict[str, Any]:
    return {"decision": action, "target": target, "reason_code": reason, "confidence": 0.75}


def _dedupe(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))
