import unittest

import app


class TrailQuestLogicTests(unittest.TestCase):
    def test_normalize_request_limits_duration(self):
        result = app.normalize_request({"duration": 29, "interest": "plants", "environment": "garden"})
        self.assertEqual(result["duration"], 30)
        self.assertEqual(result["interest"], "plants")
        self.assertEqual(result["environment"], "garden")

    def test_invalid_inputs_fall_back_safely(self):
        result = app.normalize_request({"duration": 999, "interest": "unknown", "environment": "private_roof", "language": "Klingon"})
        self.assertEqual(result["duration"], 60)
        self.assertEqual(result["interest"], "surprise")
        self.assertEqual(result["environment"], "park")
        self.assertEqual(result["language"], "English")

    def test_fallback_quest_has_steps_and_safety_note(self):
        options = app.normalize_request({"duration": 15, "interest": "birds", "environment": "park"})
        quest = app.fallback_quest(options)
        self.assertEqual(quest["duration"], 15)
        self.assertGreaterEqual(len(quest["steps"]), 3)
        self.assertTrue(quest["safety_note"])
        self.assertIn("distance", quest["safety_note"])

    def test_model_output_is_normalized(self):
        options = app.normalize_request({"duration": 30, "interest": "plants", "environment": "garden"})
        candidate = {
            "title": "Pattern hunt", "intro": "Find textures.", "supplies": "Notebook",
            "steps": [
                {"title": "Look", "instruction": "Observe leaves.", "minutes": 4},
                {"title": "Compare", "instruction": "Compare shapes.", "minutes": 6},
            ],
            "takeaway": "Write one thing down.", "reflection": "What surprised you?"
        }
        result = app.normalize_model_quest(candidate, options)
        self.assertEqual(result["title"], "Pattern hunt")
        self.assertEqual(sum(step["minutes"] for step in result["steps"]), 30)
        self.assertIn("safety_note", result)

    def test_json_parser_handles_code_fences(self):
        result = app.parse_model_json('```json\n{"title":"Hello","steps":[]}\n```')
        self.assertEqual(result["title"], "Hello")


if __name__ == "__main__":
    unittest.main()
