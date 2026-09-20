import unittest

from agent_reflex.providers import decide_with_provider


class ProviderTests(unittest.TestCase):
    def test_missing_jev_config_falls_back_to_rules(self):
        result = decide_with_provider("risk", {"task": "publish to production"}, "jev")
        self.assertTrue(result["fallback"])
        self.assertEqual(result["provider"], "rules")
        self.assertIn("jev:", result["fallback_reason"])

    def test_unknown_provider_errors(self):
        with self.assertRaises(ValueError):
            decide_with_provider("risk", {"task": "x"}, "does-not-exist")


if __name__ == "__main__":
    unittest.main()
