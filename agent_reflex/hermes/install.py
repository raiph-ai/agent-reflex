from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
from importlib import resources
from pathlib import Path

SKILL_NAME = "agent-reflex"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Install the Agent Reflex Hermes skill safely")
    parser.add_argument("--target", help="Hermes skills directory. Defaults to profile-aware HERMES_HOME/skills or ~/.hermes/skills")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing Agent Reflex skill after backing it up")
    args = parser.parse_args(argv)

    target = Path(args.target).expanduser() if args.target else default_skill_dir()
    source = resources.files("agent_reflex.hermes.skills").joinpath(SKILL_NAME)
    dest = target / SKILL_NAME

    print(f"target={target}")
    if args.dry_run:
        print(f"would install {SKILL_NAME} to {dest}")
        return 0

    try:
        install_skill(source, dest, force=args.force)
    except Exception as exc:  # ponytail: installer must fail closed, never half-install.
        print(f"Agent Reflex Hermes install failed safely: {exc}", file=sys.stderr)
        print("Hermes was not modified. Use the fallback checklist in README.md.", file=sys.stderr)
        return 1

    print(f"installed {SKILL_NAME} to {dest}")
    print("Restart or /reset Hermes so the new skill index is loaded.")
    return 0


def default_skill_dir() -> Path:
    hermes_home = os.environ.get("HERMES_HOME")
    return Path(hermes_home).expanduser() / "skills" if hermes_home else Path.home() / ".hermes" / "skills"


def install_skill(source, dest: Path, *, force: bool) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    backup = None
    if dest.exists():
        if not force:
            raise FileExistsError(f"{dest} already exists; rerun with --force to back it up and replace it")
        backup = dest.with_name(f"{dest.name}.bak")
        if backup.exists():
            shutil.rmtree(backup)
        shutil.copytree(dest, backup)

    with tempfile.TemporaryDirectory(prefix="agent-reflex-skill-") as tmp:
        staged = Path(tmp) / SKILL_NAME
        shutil.copytree(source, staged)
        if dest.exists():
            shutil.rmtree(dest)
        shutil.move(str(staged), dest)

    if not (dest / "SKILL.md").exists():
        if backup and backup.exists():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.move(str(backup), dest)
        raise RuntimeError("installed skill is missing SKILL.md")


if __name__ == "__main__":
    raise SystemExit(main())
