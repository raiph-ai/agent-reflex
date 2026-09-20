import unittest

from agent_reflex.engine import decide
from agent_reflex.schema import validate_result


class SchemaTests(unittest.TestCase):
    def test_decision_result_has_required_envelope(self):
        result = decide("risk", {"task": "edit a local draft"})
        validate_result(result)
        self.assertEqual(result["provider"], "rules")
        self.assertFalse(result["fallback"])


if __name__ == "__main__":
    unittest.main()
