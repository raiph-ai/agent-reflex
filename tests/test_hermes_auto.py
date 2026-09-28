import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_reflex.config import get_bool_setting, save_config
from agent_reflex.hermes.auto import automatic_enabled, configured_preflight_kinds, preflight, routing_plan


class HermesAutoTests(unittest.TestCase):
    def test_bool_setting_reads_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            with patch.dict("os.environ", {"AGENT_REFLEX_CONFIG": str(path)}, clear=False):
                save_config({"AGENT_REFLEX_HERMES_AUTO_ENABLED": "true"})
                self.assertTrue(get_bool_setting("AGENT_REFLEX_HERMES_AUTO_ENABLED"))
                self.assertTrue(automatic_enabled())

    def test_preflight_skips_when_disabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            with patch.dict("os.environ", {"AGENT_REFLEX_CONFIG": str(path)}, clear=False):
                save_config({"AGENT_REFLEX_HERMES_AUTO_ENABLED": "false"})
                result = preflight({"task": "publish to production"})
        self.assertTrue(result["skipped"])
        self.assertFalse(result["enabled"])

    def test_preflight_runs_configured_kinds_when_enabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            env = {"AGENT_REFLEX_CONFIG": str(path), "AGENT_REFLEX_PROVIDER_ORDER": "rules"}
            with patch.dict("os.environ", env, clear=False):
                save_config({
                    "AGENT_REFLEX_HERMES_AUTO_ENABLED": "true",
                    "AGENT_REFLEX_HERMES_AUTO_KINDS": "risk,skill",
                    "AGENT_REFLEX_PROVIDER": "auto",
                })
                self.assertEqual(configured_preflight_kinds(), ["risk", "skill"])
                result = preflight({"task": "publish the homepage to production"})
        self.assertFalse(result["skipped"])
        self.assertTrue(result["bundled"])
        self.assertEqual(result["kinds"], ["risk", "skill"])
        self.assertEqual(result["decisions"]["risk"]["provider"], "rules")
        self.assertIn("routing_plan", result)
        self.assertEqual(result["routing_plan"]["next_action"], "escalate_to_full_agent_for_approval_and_execution")
        self.assertIn("skills", result["decisions"]["skill"])

    def test_preflight_force_runs_when_disabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            with patch.dict("os.environ", {"AGENT_REFLEX_CONFIG": str(path), "AGENT_REFLEX_PROVIDER_ORDER": "rules"}, clear=False):
                save_config({"AGENT_REFLEX_HERMES_AUTO_ENABLED": "false"})
                result = preflight({"task": "route this website task"}, force=True)
        self.assertFalse(result["skipped"])
        self.assertFalse(result["enabled"])
        self.assertIn("routing_plan", result)
        self.assertIn("risk", result["decisions"])

    def test_routing_plan_continues_fast_path_for_high_confidence_low_risk(self):
        decisions = {
            "route": {"confidence": 0.92, "recommended_agent": "raiph"},
            "risk": {"confidence": 0.91, "requires_human_approval": False, "requires_verification": False},
            "skill": {"confidence": 0.95, "skills": ["none"], "toolsets": []},
        }
        plan = routing_plan(decisions)
        self.assertTrue(plan["default_first"])
        self.assertEqual(plan["next_action"], "continue_fast_path")

    def test_routing_plan_escalates_low_confidence(self):
        decisions = {
            "route": {"confidence": 0.55, "recommended_agent": "raiph"},
            "risk": {"confidence": 0.91, "risk_level": "medium", "requires_human_approval": False, "requires_verification": True},
            "skill": {"confidence": 0.95, "skills": ["none"], "toolsets": []},
        }
        plan = routing_plan(decisions)
        self.assertEqual(plan["next_action"], "escalate_to_full_agent_for_judgment")
        self.assertEqual(plan["low_confidence_decisions"], ["route"])


if __name__ == "__main__":
    unittest.main()
