from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .engine import decide

KINDS = ("route", "risk", "memory", "skill", "validate")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agent-reflex", description="Typed decisions for autonomous agents")
    parser.add_argument("kind", choices=KINDS)
    parser.add_argument("--input", "-i", required=True, help="Path to JSON input, or '-' for stdin")
    args = parser.parse_args(argv)

    payload = _load_json(args.input)
    result = decide(args.kind, payload)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def _load_json(source: str) -> dict:
    raw = sys.stdin.read() if source == "-" else Path(source).read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise SystemExit("input JSON must be an object")
    return data


if __name__ == "__main__":
    raise SystemExit(main())
