import unittest

from agent_reflex.web import render_field, render_page


class WebUiTests(unittest.TestCase):
    def test_provider_fields_render_as_selects(self):
        html = render_field("AGENT_REFLEX_PROVIDER", "auto")
        self.assertIn('<select name="AGENT_REFLEX_PROVIDER">', html)
        self.assertIn('value="auto" selected', html)
        self.assertIn('Cactus — local reflex model', html)

    def test_policy_and_preflight_kinds_render_as_selects(self):
        html = render_page({
            "AGENT_REFLEX_PROVIDER": "auto",
            "AGENT_REFLEX_PROVIDER_POLICY": "local-first",
            "AGENT_REFLEX_PROVIDER_ORDER": "cactus,jev,openai-compatible,rules",
            "AGENT_REFLEX_HERMES_AUTO_KINDS": "route,risk,skill",
        })
        self.assertIn('<select name="AGENT_REFLEX_PROVIDER_POLICY">', html)
        self.assertIn('value="local-first" selected', html)
        self.assertIn('<select name="AGENT_REFLEX_HERMES_AUTO_KINDS">', html)
        self.assertIn('Recommended — route + risk + skill', html)

    def test_custom_select_value_is_preserved(self):
        html = render_field("AGENT_REFLEX_OPENAI_MODEL", "custom-model")
        self.assertIn('Current custom: custom-model', html)
        self.assertIn('value="custom-model" selected', html)


if __name__ == "__main__":
    unittest.main()
