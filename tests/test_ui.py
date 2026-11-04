import os
import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest

from src.fixtures import get_demo_fixture_result
from src.schemas import VivedexResult


class TestUIComponents(unittest.TestCase):
    def test_fixture_generation(self):
        result = get_demo_fixture_result()
        self.assertIsInstance(result, VivedexResult)
        self.assertIn("DEMO FIXTURE", result.disclaimer)
        self.assertIn("Passer domesticus", result.ai_candidate.candidates[0].scientific_name)
        self.assertEqual(result.taxonomic_resolution.usage_key, 5231190)
        self.assertIn("Animalia", result.taxonomic_resolution.hierarchy["kingdom"])

    def test_json_export_structure(self):
        result = get_demo_fixture_result()
        json_str = result.to_json()
        self.assertIn("ai_candidate", json_str)
        self.assertIn("taxonomic_resolution", json_str)
        self.assertIn("DEMO FIXTURE — NOT A LIVE MODEL RESULT", json_str)

    def test_apptest_loads(self):
        root_dir = Path(__file__).resolve().parent.parent
        app_file = str(root_dir / "app.py")
        at = AppTest.from_file(app_file)
        at.run()
        self.assertFalse(at.exception)
        # Check that title was rendered
        self.assertTrue(any("Vivédex" in t.value for t in at.title))


if __name__ == "__main__":
    unittest.main()
