from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

CONFIG_ENV = "AGENT_REFLEX_CONFIG"
DEFAULT_CONFIG_PATH = Path.home() / ".agent-reflex" / "config.json"

DEFAULT_CONFIG: dict[str, Any] = {
    "AGENT_REFLEX_PROVIDER": "rules",
    "AGENT_REFLEX_PROVIDER_POLICY": "auto",
    "AGENT_REFLEX_PROVIDER_ORDER": "cactus,jev,openai-compatible,rules",
    "AGENT_REFLEX_CACTUS_URL": "http://127.0.0.1:8088/v1",
    "AGENT_REFLEX_CACTUS_MODEL": "needle-cq4",
    "AGENT_REFLEX_OPENAI_BASE_URL": "http://127.0.0.1:8088/v1",
    "AGENT_REFLEX_OPENAI_MODEL": "needle-cq4",
}

SECRET_KEYS = {
    "AGENT_REFLEX_JEV_API_KEY",
    "AGENT_REFLEX_CACTUS_API_KEY",
    "AGENT_REFLEX_OPENAI_API_KEY",
}

CONFIG_KEYS = tuple(DEFAULT_CONFIG) + (
    "AGENT_REFLEX_JEV_URL",
    "AGENT_REFLEX_JEV_API_KEY",
    "AGENT_REFLEX_CACTUS_API_KEY",
    "AGENT_REFLEX_OPENAI_API_KEY",
)


def config_path() -> Path:
    return Path(os.environ.get(CONFIG_ENV, DEFAULT_CONFIG_PATH)).expanduser()


def load_config() -> dict[str, Any]:
    path = config_path()
    if not path.exists():
        return dict(DEFAULT_CONFIG)
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Agent Reflex config must be a JSON object: {path}")
    merged = dict(DEFAULT_CONFIG)
    merged.update({str(key): value for key, value in data.items() if value not in (None, "")})
    return merged


def save_config(values: dict[str, Any]) -> Path:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    clean = {key: str(value) for key, value in values.items() if key in CONFIG_KEYS and value not in (None, "")}
    with path.open("w", encoding="utf-8") as handle:
        json.dump(clean, handle, indent=2, sort_keys=True)
        handle.write("\n")
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return path


def get_setting(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name)
    if value not in (None, ""):
        return value
    config = load_config()
    configured = config.get(name)
    if configured in (None, ""):
        return default
    return str(configured)


def masked_value(name: str, value: Any) -> str:
    if name in SECRET_KEYS and value:
        return "••••••••"
    return "" if value is None else str(value)
