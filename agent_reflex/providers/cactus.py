from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

from agent_reflex.config import get_setting

from .mock import MockProvider
from .openai_compatible import OpenAICompatibleProvider

_KNOWN_TOOLSETS = {
    "browser",
    "web",
    "terminal",
    "file",
    "code_execution",
    "vision",
    "image_gen",
    "memory",
    "session_search",
    "skills",
    "cronjob",
    "delegation",
    "clarify",
    "todo",
}


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
        previous = os.environ.get(self.key_env)
        os.environ[self.key_env] = "local-cactus"
        try:
            return super().decide(kind, payload)
        finally:
            if previous is None:
                os.environ.pop(self.key_env, None)
            else:
                os.environ[self.key_env] = previous

    def _chat_json(self, base_url: str, api_key: str, model: str, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Use Cactus tool calls and normalize against deterministic rules.

        Needle/Cactus currently tends to return empty text for plain JSON prompts,
        but it can emit OpenAI-style tool calls. We treat the local model as a
        reflex signal, then fill/repair the final decision with the rules backend
        so Hermes receives a complete, safe contract instead of falling back.
        """
        rule_result = MockProvider().decide(kind, payload)
        tool_name = f"{kind}_decision"
        body = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are Agent Reflex. Call the provided tool with a compact "
                        "decision for the user's task. Prefer safe decisions for "
                        "production, external, destructive, credential, and financial actions."
                    ),
                },
                {"role": "user", "content": json.dumps(payload, sort_keys=True)},
            ],
            "max_tokens": 160,
            "tools": [{"type": "function", "function": _tool_definition(kind, tool_name)}],
            "tool_choice": {"type": "function", "function": {"name": tool_name}},
        }
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        req = urllib.request.Request(
            f"{base_url}/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))

        raw_args = _extract_tool_arguments(data)
        result = _merge_decision(kind, rule_result, raw_args)
        result["provider"] = self.name
        result["fallback"] = False
        result["cactus_raw"] = raw_args
        return result


def _tool_definition(kind: str, name: str) -> dict[str, Any]:
    properties: dict[str, Any] = {"decision": {"type": "string"}, "confidence": {"type": "number"}}
    if kind == "risk":
        properties.update(
            {
                "risk_level": {"type": "string"},
                "requires_human_approval": {"type": "boolean"},
                "requires_verification": {"type": "boolean"},
                "reason_codes": {"type": "array", "items": {"type": "string"}},
            }
        )
    elif kind == "route":
        properties.update(
            {
                "project": {"type": "string"},
                "intent": {"type": "string"},
                "recommended_agent": {"type": "string"},
                "priority": {"type": "string"},
            }
        )
    elif kind == "skill":
        properties.update(
            {
                "skills": {"type": "array", "items": {"type": "string"}},
                "toolsets": {"type": "array", "items": {"type": "string"}},
            }
        )
    elif kind == "memory":
        properties.update({"target": {"type": "string"}, "reason_code": {"type": "string"}})
    elif kind == "validate":
        properties.update(
            {
                "passes": {"type": "boolean"},
                "missing_requirements": {"type": "array", "items": {"type": "string"}},
                "requires_followup_tool_call": {"type": "boolean"},
            }
        )
    return {
        "name": name,
        "description": f"Return an Agent Reflex {kind} decision.",
        "parameters": {"type": "object", "properties": properties},
    }


def _extract_tool_arguments(response: dict[str, Any]) -> dict[str, Any]:
    message = response.get("choices", [{}])[0].get("message", {})
    for call in message.get("tool_calls") or []:
        function = call.get("function") or {}
        raw = function.get("arguments") or "{}"
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return {"raw_arguments": raw}
        return parsed if isinstance(parsed, dict) else {"raw_arguments": parsed}
    content = message.get("content") or ""
    if not content:
        return {}
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return {"raw_content": content}
    return parsed if isinstance(parsed, dict) else {"raw_content": parsed}


def _merge_decision(kind: str, defaults: dict[str, Any], raw: dict[str, Any]) -> dict[str, Any]:
    result = dict(defaults)
    if isinstance(raw.get("decision"), str):
        result["decision"] = raw["decision"]
    if isinstance(raw.get("confidence"), (int, float)) and 0 <= raw["confidence"] <= 1:
        result["confidence"] = raw["confidence"]

    if kind == "risk":
        level = str(raw.get("risk_level", "")).lower().strip()
        if level in {"low", "medium", "high", "critical"}:
            result["risk_level"] = level
        for field in ("requires_human_approval", "requires_verification"):
            if isinstance(raw.get(field), bool):
                result[field] = raw[field]
        reasons = _string_list(raw.get("reason_codes"))
        if reasons:
            result["reason_codes"] = reasons
    elif kind == "route":
        for field in ("project", "intent", "recommended_agent", "priority"):
            if isinstance(raw.get(field), str) and raw[field].strip():
                result[field] = raw[field].strip()
    elif kind == "skill":
        skills = _string_list(raw.get("skills"))
        if skills:
            result["skills"] = skills
        toolsets = [item for item in _string_list(raw.get("toolsets")) if item in _KNOWN_TOOLSETS]
        if toolsets:
            result["toolsets"] = toolsets
    elif kind == "memory":
        for field in ("target", "reason_code"):
            if isinstance(raw.get(field), str) and raw[field].strip():
                result[field] = raw[field].strip()
    elif kind == "validate":
        if isinstance(raw.get("passes"), bool):
            result["passes"] = raw["passes"]
            result["decision"] = "passes" if raw["passes"] else "needs_more_work"
        values = _string_list(raw.get("missing_requirements"))
        if values:
            result["missing_requirements"] = values
        if isinstance(raw.get("requires_followup_tool_call"), bool):
            result["requires_followup_tool_call"] = raw["requires_followup_tool_call"]

    result.setdefault("thresholds", {})
    return result


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [item.strip() for item in value.split(",") if item.strip()]
    return []
