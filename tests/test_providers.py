import unittest
from unittest.mock import patch

from agent_reflex.providers import decide_with_provider
from agent_reflex.providers.policy import provider_order


class ProviderTests(unittest.TestCase):
    def test_missing_jev_config_falls_back_to_rules(self):
        result = decide_with_provider("risk", {"task": "publish to production"}, "jev")
        self.assertTrue(result["fallback"])
        self.assertEqual(result["provider"], "rules")
        self.assertIn("jev:", result["fallback_reason"])

    def test_unknown_provider_errors(self):
        with self.assertRaises(ValueError):
            decide_with_provider("risk", {"task": "x"}, "does-not-exist")

    def test_auto_policy_falls_back_through_order(self):
        with patch.dict("os.environ", {"AGENT_REFLEX_PROVIDER_ORDER": "jev,rules"}, clear=False):
            result = decide_with_provider("risk", {"task": "publish to production"}, "auto")
        self.assertTrue(result["fallback"])
        self.assertEqual(result["provider"], "rules")
        self.assertIn("jev:", result["fallback_reason"])
        self.assertEqual(result["attempted_providers"], ["jev", "rules"])

    def test_provider_order_always_appends_rules(self):
        with patch.dict("os.environ", {"AGENT_REFLEX_PROVIDER_ORDER": "cactus,jev"}, clear=False):
            self.assertEqual(provider_order(), ["cactus", "jev", "rules"])

    def test_env_provider_default(self):
        with patch.dict("os.environ", {"AGENT_REFLEX_PROVIDER": "auto", "AGENT_REFLEX_PROVIDER_ORDER": "jev,rules"}, clear=False):
            result = decide_with_provider("route", {"task": "update IT Rockstar homepage"})
        self.assertEqual(result["provider"], "rules")
        self.assertTrue(result["fallback"])


if __name__ == "__main__":
    unittest.main()
