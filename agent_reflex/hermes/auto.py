from __future__ import annotations

from typing import Any

from agent_reflex.config import get_bool_setting, get_setting
from agent_reflex.providers import decide_bundle_with_provider
from agent_reflex.schema import KINDS

DEFAULT_PREFLIGHT_KINDS = ("route", "risk", "skill")


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
    it gives Hermes structured routing/risk/skill guidance before normal work.
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

    return {
        "enabled": enabled,
        "skipped": False,
        "provider": provider or get_setting("AGENT_REFLEX_PROVIDER", "rules"),
        "bundled": True,
        "kinds": list(decisions),
        "decisions": decisions,
    }
