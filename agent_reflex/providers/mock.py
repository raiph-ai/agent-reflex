from __future__ import annotations

from typing import Any

from agent_reflex.engine import decide


class MockProvider:
    """Dependency-free provider used for tests and demos."""

    name = "rules"

    def decide(self, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        return decide(kind, payload)

    def decide_bundle(self, payload: dict[str, Any], kinds: list[str]) -> dict[str, dict[str, Any]]:
        return {kind: self.decide(kind, payload) for kind in kinds}
