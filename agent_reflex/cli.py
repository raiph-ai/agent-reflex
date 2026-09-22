from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .providers import decide_with_provider
from .schema import KINDS, validate_result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agent-reflex", description="Typed decisions for autonomous agents")
    sub = parser.add_subparsers(dest="command")

    for kind in KINDS:
        p = sub.add_parser(kind)
        p.add_argument("--input", "-i", required=True, help="Path to JSON input, or '-' for stdin")
        p.add_argument("--provider", default=None, help="Decision provider: rules, auto, jev, cactus, openai-compatible")

    check = sub.add_parser("check", help="Validate a decision result JSON file")
    check.add_argument("path")

    args = parser.parse_args(argv)
    if args.command == "check":
        validate_result(_load_json(args.path))
        print(json.dumps({"ok": True}, indent=2))
        return 0
    if args.command not in KINDS:
        parser.print_help()
        return 2

    payload = _load_json(args.input)
    result = decide_with_provider(args.command, payload, args.provider)
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
