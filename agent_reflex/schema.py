from __future__ import annotations

from typing import Any

KINDS = ("route", "risk", "memory", "skill", "validate")
REQUIRED_RESULT_FIELDS = ("decision", "confidence", "provider", "thresholds", "fallback")


def validate_payload(payload: dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")


def validate_result(result: dict[str, Any]) -> None:
    missing = [field for field in REQUIRED_RESULT_FIELDS if field not in result]
    if missing:
        raise ValueError(f"decision result missing fields: {', '.join(missing)}")
    confidence = result["confidence"]
    if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        raise ValueError("confidence must be a number from 0 to 1")
