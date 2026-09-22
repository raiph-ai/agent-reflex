import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_reflex.config import get_setting, load_config, save_config
from agent_reflex.providers import decide_with_provider


class ConfigTests(unittest.TestCase):
    def test_save_and_load_config_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            with patch.dict("os.environ", {"AGENT_REFLEX_CONFIG": str(path)}, clear=False):
                save_config({"AGENT_REFLEX_PROVIDER": "auto", "AGENT_REFLEX_PROVIDER_ORDER": "jev,rules"})
                loaded = load_config()
        self.assertEqual(loaded["AGENT_REFLEX_PROVIDER"], "auto")
        self.assertEqual(loaded["AGENT_REFLEX_PROVIDER_ORDER"], "jev,rules")

    def test_env_overrides_config_setting(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            with patch.dict("os.environ", {"AGENT_REFLEX_CONFIG": str(path)}, clear=False):
                save_config({"AGENT_REFLEX_PROVIDER": "rules"})
                with patch.dict("os.environ", {"AGENT_REFLEX_PROVIDER": "auto"}, clear=False):
                    self.assertEqual(get_setting("AGENT_REFLEX_PROVIDER"), "auto")

    def test_provider_reads_config_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            with patch.dict("os.environ", {"AGENT_REFLEX_CONFIG": str(path)}, clear=False):
                save_config({"AGENT_REFLEX_PROVIDER": "auto", "AGENT_REFLEX_PROVIDER_ORDER": "jev,rules"})
                result = decide_with_provider("risk", {"task": "publish to production"})
        self.assertEqual(result["provider"], "rules")
        self.assertTrue(result["fallback"])
        self.assertEqual(result["attempted_providers"], ["jev", "rules"])


if __name__ == "__main__":
    unittest.main()
