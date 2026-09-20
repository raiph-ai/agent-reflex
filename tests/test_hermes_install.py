import tempfile
import unittest
from pathlib import Path

from agent_reflex.hermes.install import install_skill


class HermesInstallTests(unittest.TestCase):
    def test_installs_skill_to_empty_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path("agent_reflex/hermes/skills/agent-reflex")
            dest = Path(tmp) / "skills" / "agent-reflex"
            install_skill(source, dest, force=False)
            self.assertTrue((dest / "SKILL.md").exists())

    def test_existing_skill_requires_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path("agent_reflex/hermes/skills/agent-reflex")
            dest = Path(tmp) / "skills" / "agent-reflex"
            install_skill(source, dest, force=False)
            with self.assertRaises(FileExistsError):
                install_skill(source, dest, force=False)

    def test_force_creates_backup_and_replaces(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path("agent_reflex/hermes/skills/agent-reflex")
            dest = Path(tmp) / "skills" / "agent-reflex"
            install_skill(source, dest, force=False)
            (dest / "marker.txt").write_text("old", encoding="utf-8")
            install_skill(source, dest, force=True)
            self.assertTrue((dest / "SKILL.md").exists())
            self.assertTrue((dest.with_name("agent-reflex.bak") / "marker.txt").exists())


if __name__ == "__main__":
    unittest.main()
