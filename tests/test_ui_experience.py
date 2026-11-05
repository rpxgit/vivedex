"""Automated tests for Vivédex experience reconstruction (RUN 007B).

Verifies design tokens, naturalist rank calculation, curated specimen assets,
and multi-page navigation stability under AppTest.
"""

from __future__ import annotations

import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest

from src.ui.page_species_detail import CURATED_SPECIMEN_ASSETS
from src.ui.theme import COLOR_TOKENS, NATURALIST_RANKS, get_naturalist_rank


class TestUIExperience(unittest.TestCase):
    """Test suite covering the reconstructed UI design system and components."""

    def test_color_tokens_completeness(self) -> None:
        """Verify that all required botanical color tokens are defined."""
        required_keys = [
            "forest",
            "deep_forest",
            "moss",
            "sage",
            "ivory",
            "paper",
            "border",
            "earth",
            "gold",
            "ink",
            "muted",
        ]
        for key in required_keys:
            self.assertIn(key, COLOR_TOKENS)
            self.assertTrue(COLOR_TOKENS[key].startswith("#"))

    def test_naturalist_ranks(self) -> None:
        """Verify progression of naturalist rank titles across player levels."""
        self.assertEqual(get_naturalist_rank(1), "Observer")
        self.assertEqual(get_naturalist_rank(2), "Explorer")
        self.assertEqual(get_naturalist_rank(3), "Naturalist")
        self.assertEqual(get_naturalist_rank(4), "Field Researcher")
        self.assertEqual(get_naturalist_rank(5), "Specialist")
        self.assertEqual(get_naturalist_rank(6), "Biodiversity Steward")
        self.assertEqual(get_naturalist_rank(10), "Biodiversity Steward")

    def test_curated_specimen_assets_licensing(self) -> None:
        """Verify that all curated specimen assets have valid licences and authors."""
        for taxon_id, asset in CURATED_SPECIMEN_ASSETS.items():
            self.assertIsInstance(taxon_id, int)
            self.assertTrue(asset["image_url"].startswith("http"))
            self.assertTrue(len(asset["author"]) > 0)
            self.assertIn("CC", asset["licence"])
            self.assertTrue(len(asset["visible_traits"]) >= 2)
            self.assertTrue(len(asset["similar_taxa"]) >= 1)

    def test_apptest_navigation_loads(self) -> None:
        """Verify that the full multi-page application loads with the new theme."""
        root_dir = Path(__file__).resolve().parent.parent
        app_file = str(root_dir / "app.py")
        at = AppTest.from_file(app_file)
        at.run(timeout=10)
        self.assertFalse(at.exception)
        # Check that title contains Vivédex
        self.assertTrue(any("Vivédex" in t.value for t in at.title))


if __name__ == "__main__":
    unittest.main()
