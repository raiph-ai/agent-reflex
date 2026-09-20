import unittest

from agent_reflex.engine import decide


class EngineTests(unittest.TestCase):
    def test_risk_flags_production_publish(self):
        out = decide("risk", {"task": "publish this to the live production website"})
        self.assertEqual(out["risk_level"], "high")
        self.assertTrue(out["requires_human_approval"])
        self.assertIn("external_write", out["reason_codes"])
        self.assertIn("production_system", out["reason_codes"])

    def test_memory_saves_stable_preference(self):
        out = decide("memory", {"message": "Ralph prefers concise executive summaries"})
        self.assertEqual(out["decision"], "save")
        self.assertEqual(out["target"], "user_profile")

    def test_skill_recommends_github(self):
        out = decide("skill", {"task": "open a GitHub pull request for the repo"})
        self.assertIn("github-workflows", out["skills"])

    def test_validate_requires_missing_work(self):
        out = decide("validate", {"requirements": ["tests passed"], "output": "files written", "requires_verification": True})
        self.assertFalse(out["passes"])
        self.assertTrue(out["requires_followup_tool_call"])


if __name__ == "__main__":
    unittest.main()
