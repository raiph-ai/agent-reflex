import unittest

from agent_reflex.providers.cactus import _extract_tool_arguments, _merge_decision, _preflight_tool_definition


class CactusProviderTests(unittest.TestCase):
    def test_extracts_openai_tool_call_arguments(self):
        response = {
            "choices": [
                {
                    "message": {
                        "tool_calls": [
                            {
                                "function": {
                                    "name": "risk_decision",
                                    "arguments": '{"risk_level":"high","requires_human_approval":true}',
                                }
                            }
                        ]
                    }
                }
            ]
        }
        self.assertEqual(
            _extract_tool_arguments(response),
            {"risk_level": "high", "requires_human_approval": True},
        )

    def test_merge_decision_keeps_safe_defaults_when_cactus_args_are_partial(self):
        defaults = {
            "decision": "requires_approval",
            "risk_level": "high",
            "requires_human_approval": True,
            "requires_verification": True,
            "reason_codes": ["external_write", "production_system"],
            "confidence": 0.9,
            "provider": "rules",
            "thresholds": {},
            "fallback": False,
        }
        raw = {"risk_level": "external_write", "requires_human_approval": "production_system"}
        merged = _merge_decision("risk", defaults, raw)
        self.assertEqual(merged["risk_level"], "high")
        self.assertTrue(merged["requires_human_approval"])
        self.assertTrue(merged["requires_verification"])
        self.assertEqual(merged["reason_codes"], ["external_write", "production_system"])

    def test_merge_decision_accepts_valid_cactus_args(self):
        defaults = {
            "decision": "allowed",
            "risk_level": "low",
            "requires_human_approval": False,
            "requires_verification": False,
            "reason_codes": ["no_high_risk_markers"],
            "confidence": 0.68,
            "provider": "rules",
            "thresholds": {},
            "fallback": False,
        }
        raw = {
            "decision": "requires_approval",
            "risk_level": "medium",
            "requires_human_approval": False,
            "requires_verification": True,
            "reason_codes": ["writes_local_file"],
            "confidence": 0.7,
        }
        merged = _merge_decision("risk", defaults, raw)
        self.assertEqual(merged["decision"], "requires_approval")
        self.assertEqual(merged["risk_level"], "medium")
        self.assertTrue(merged["requires_verification"])
        self.assertEqual(merged["reason_codes"], ["writes_local_file"])
        self.assertEqual(merged["confidence"], 0.7)

    def test_merge_skill_filters_unknown_toolsets(self):
        defaults = {
            "decision": "skill_recommendation",
            "skills": ["wordpress-site-deployment"],
            "toolsets": ["browser", "web"],
            "confidence": 0.74,
            "provider": "rules",
            "thresholds": {},
            "fallback": False,
        }
        raw = {"toolsets": "production, browser, external"}
        merged = _merge_decision("skill", defaults, raw)
        self.assertEqual(merged["toolsets"], ["browser"])

    def test_preflight_tool_definition_bundles_kinds(self):
        tool = _preflight_tool_definition("preflight_decision", ["route", "risk", "skill"])
        props = tool["parameters"]["properties"]
        self.assertIn("route", props)
        self.assertIn("risk", props)
        self.assertIn("skill", props)
        self.assertIn("risk_level", props["risk"]["properties"])


if __name__ == "__main__":
    unittest.main()
