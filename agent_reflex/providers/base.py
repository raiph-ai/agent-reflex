from __future__ import annotations

from typing import Any, Protocol


class ReflexProvider(Protocol):
    name: str

    def decide(self, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Return a typed decision result."""
