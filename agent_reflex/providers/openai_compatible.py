from __future__ import annotations

import json
import urllib.request
from typing import Any

from agent_reflex.config import get_setting


class OpenAICompatibleProvider:
    """Small OpenAI-compatible adapter with safe fallback handled upstream."""

    name = "openai-compatible"
    url_env = "AGENT_REFLEX_OPENAI_BASE_URL"
    key_env = "AGENT_REFLEX_OPENAI_API_KEY"
    model_env = "AGENT_REFLEX_OPENAI_MODEL"

    def decide(self, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        base_url = get_setting(self.url_env)
        api_key = get_setting(self.key_env)
        model = get_setting(self.model_env, "needle-cq4") or "needle-cq4"
        missing = [name for name, value in ((self.url_env, base_url), (self.key_env, api_key)) if not value]
        if missing:
            raise RuntimeError(f"missing environment: {', '.join(missing)}")

        assert base_url is not None
        result = self._chat_json(base_url.rstrip("/"), api_key or "", model, kind, payload)
        result.setdefault("decision", kind)
        result.setdefault("confidence", 0.5)
        result.setdefault("thresholds", {})
        result["provider"] = self.name
        result["fallback"] = False
        return result

    def _chat_json(self, base_url: str, api_key: str, model: str, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        prompt = (
            "Return only compact JSON for an Agent Reflex decision. "
            f"Decision kind: {kind}. Input: {json.dumps(payload, sort_keys=True)}"
        )
        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You produce only valid JSON. No prose."},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 200,
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
        content = data["choices"][0]["message"].get("content", "")
        if not content:
            raise RuntimeError("provider returned empty content")
        parsed = json.loads(content)
        if not isinstance(parsed, dict):
            raise RuntimeError("provider returned non-object JSON")
        return parsed
