from __future__ import annotations

from typing import Any

from agent_reflex.engine import decide


class MockProvider:
    """Dependency-free provider used for tests and demos."""

    name = "rules"

    def decide(self, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        return decide(kind, payload)
