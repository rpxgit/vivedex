"""Test suite for RUN 011 Experience Overhaul and new product modules.

Covers:
- Restor-inspired ecological hierarchy (Field sites, projects, expeditions, species richness)
- Habitica-inspired quests, habits, and non-punitive XP awards
- ORCID-inspired researcher passport, affiliations, and provenance states
- Global cross-entity discovery search
- Palette WCAG AA contrast ratio compliance
"""

from __future__ import annotations

import math
import tempfile
import unittest
from pathlib import Path

from src.auth import AuthService
from src.collection_service import CollectionService
from src.database import Database
from src.ecological_service import EcologicalService
from src.passport_service import PassportService
from src.quest_service import QuestService
from src.search_service import SearchService
from src.ui.theme import COLOR_TOKENS


def calculate_relative_luminance(hex_color: str) -> float:
    """Calculate relative luminance for WCAG contrast calculations."""
    hex_clean = hex_color.lstrip("#")
    r, g, b = [int(hex_clean[i : i + 2], 16) / 255.0 for i in (0, 2, 4)]
    r_lum = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
    g_lum = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
    b_lum = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
    return 0.2126 * r_lum + 0.7152 * g_lum + 0.0722 * b_lum


def calculate_contrast_ratio(hex1: str, hex2: str) -> float:
    """Calculate the WCAG contrast ratio between two hex colors."""
    lum1 = calculate_relative_luminance(hex1)
    lum2 = calculate_relative_luminance(hex2)
    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)
    return (lighter + 0.05) / (darker + 0.05)


class TestExperienceOverhaul(unittest.TestCase):
    """Regression and functional test suite for the RUN 011 experience overhaul."""

    def setUp(self) -> None:
        """Create an isolated test database with schema v2."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_overhaul.sqlite3"
        self.db = Database(self.db_path)
        self.db.initialize_schema()

        self.auth_service = AuthService(self.db)
        self.collection_service = CollectionService(self.db)
        self.eco_service = EcologicalService(self.db)
        self.quest_service = QuestService(self.db)
        self.passport_service = PassportService(self.db)
        self.search_service = SearchService(self.db)

        # Create test user
        self.user = self.auth_service.register_user(
            username="naturalist_eva",
            password="secure_password_987",
            display_name="Eva Rostova",
        )

    def tearDown(self) -> None:
        """Clean up isolated test database."""
        self.temp_dir.cleanup()

    # -------------------------------------------------------------------------
    # 1. Palette Contrast Tests (WCAG AA Compliance)
    # -------------------------------------------------------------------------
    def test_theme_color_contrast_ratios(self) -> None:
        """Verify that all core reading text tokens meet WCAG AA contrast (>= 4.5:1)."""
        ivory = COLOR_TOKENS["ivory"]  # #F5F2E9

        contrast_ink = calculate_contrast_ratio(COLOR_TOKENS["ink"], ivory)
        self.assertGreaterEqual(
            contrast_ink, 4.5, f"Ink contrast ratio {contrast_ink:.2f} is below 4.5:1"
        )

        contrast_forest = calculate_contrast_ratio(COLOR_TOKENS["forest"], ivory)
        self.assertGreaterEqual(
            contrast_forest, 4.5, f"Forest contrast ratio {contrast_forest:.2f} is below 4.5:1"
        )

        contrast_deep_forest = calculate_contrast_ratio(COLOR_TOKENS["deep_forest"], ivory)
        self.assertGreaterEqual(
            contrast_deep_forest, 4.5, f"Deep forest contrast ratio {contrast_deep_forest:.2f} is below 4.5:1"
        )

        contrast_muted = calculate_contrast_ratio(COLOR_TOKENS["muted"], ivory)
        self.assertGreaterEqual(
            contrast_muted, 4.5, f"Muted text contrast ratio {contrast_muted:.2f} is below 4.5:1"
        )

        contrast_white_forest = calculate_contrast_ratio(COLOR_TOKENS["white"], COLOR_TOKENS["forest"])
        self.assertGreaterEqual(
            contrast_white_forest, 4.5, f"White on forest contrast ratio {contrast_white_forest:.2f} is below 4.5:1"
        )

        contrast_hero_title = calculate_contrast_ratio(COLOR_TOKENS["white"], COLOR_TOKENS["deep_forest"])
        self.assertGreaterEqual(
            contrast_hero_title, 4.5, f"Hero title on deep forest contrast {contrast_hero_title:.2f} is below 4.5:1"
        )

    def test_streamlit_upload_limit_config(self) -> None:
        """Verify that .streamlit/config.toml pins maxUploadSize to 8 MB."""
        root = Path(__file__).resolve().parent.parent
        cfg_file = root / ".streamlit" / "config.toml"
        self.assertTrue(cfg_file.exists())
        content = cfg_file.read_text(encoding="utf-8")
        self.assertIn("maxUploadSize = 8", content)

    # -------------------------------------------------------------------------
    # 2. Ecological Hierarchy & Species Richness
    # -------------------------------------------------------------------------
    def test_ecological_organisations(self) -> None:
        """Verify organisation querying and registration."""
        orgs = self.eco_service.list_organisations()
        self.assertGreaterEqual(len(orgs), 3)

        kew = self.eco_service.get_organisation("kew-gardens")
        self.assertIsNotNone(kew)
        self.assertEqual(kew.name, "Royal Botanic Gardens, Kew")

        new_org = self.eco_service.create_organisation(
            name="Max Planck Institute of Animal Behavior",
            country="Germany",
            website_url="https://www.ab.mpg.de",
        )
        self.assertEqual(new_org.slug, "max-planck-institute-of-animal-behavior")
        self.assertEqual(new_org.country, "Germany")

    def test_field_sites_and_species_richness(self) -> None:
        """Verify field site creation, observation linking, and dynamic richness calculation."""
        sites = self.eco_service.list_field_sites()
        self.assertGreaterEqual(len(sites), 3)

        site = self.eco_service.get_field_site("monteverde-cloud-forest")
        self.assertIsNotNone(site)
        self.assertEqual(site.observation_count, 0)
        self.assertEqual(site.species_richness, 0)

        # Seed test taxa to satisfy foreign key constraint
        now_ts = "2026-03-01T00:00:00Z"
        with self.db.connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO taxa (taxon_id, scientific_name, canonical_name, common_name, rank, family, kingdom, retrieved_at, created_at)
                VALUES (101, 'Monstera deliciosa', 'Monstera deliciosa', 'Swiss Cheese Plant', 'SPECIES', 'Araceae', 'Plantae', ?, ?),
                       (102, 'Epidendrum radicans', 'Epidendrum radicans', 'Ground-rooting Epidendrum', 'SPECIES', 'Orchidaceae', 'Plantae', ?, ?);
                """,
                (now_ts, now_ts, now_ts, now_ts),
            )

        # Record two observations with different taxa linked to this site
        obs1 = self.collection_service.record_observation(
            user_id=self.user.id,
            candidate_scientific_name="Monstera deliciosa",
            model_result_json='{"observation_summary": "Large fenestrated leaves"}',
            matched_taxon_id=101,
            field_notes="Found on cloud forest lower trunk.",
        )
        self.eco_service.link_observation_ecological(
            observation_id=obs1.observation_id,
            site_id=site.id,
        )

        obs2 = self.collection_service.record_observation(
            user_id=self.user.id,
            candidate_scientific_name="Epidendrum radicans",
            model_result_json='{"observation_summary": "Bright orange-red epiphyte orchid"}',
            matched_taxon_id=102,
            field_notes="Growing epiphytically at 1450m elevation.",
        )
        self.eco_service.link_observation_ecological(
            observation_id=obs2.observation_id,
            site_id=site.id,
        )

        updated_site = self.eco_service.get_field_site(site.id)
        self.assertEqual(updated_site.observation_count, 2)
        self.assertEqual(updated_site.species_richness, 2)

    def test_projects_and_expeditions(self) -> None:
        """Verify project and expedition creation and association."""
        projects = self.eco_service.list_projects()
        self.assertGreaterEqual(len(projects), 2)

        expeditions = self.eco_service.list_expeditions()
        self.assertGreaterEqual(len(expeditions), 2)

        new_proj = self.eco_service.create_project(
            title="Tropical Epiphyte Monitoring",
            summary="Monitoring epiphyte biomass across altitudinal gradient",
            lead_user_id=self.user.id,
            target_species_count=40,
        )
        self.assertEqual(new_proj.status, "ACTIVE")

        new_exp = self.eco_service.create_expedition(
            title="Monteverde Canopy Transect 2026",
            project_id=new_proj.id,
            lead_user_id=self.user.id,
            start_date="2026-06-01",
        )
        self.assertEqual(new_exp.project_id, new_proj.id)
        self.assertEqual(new_exp.status, "PLANNED")

    # -------------------------------------------------------------------------
    # 3. Quests, Habits, and Non-Punitive XP
    # -------------------------------------------------------------------------
    def test_quests_evaluation_and_rewards(self) -> None:
        """Verify that user activity correctly increments quest progress and rewards XP."""
        # 1. Initial quests list
        quests = self.quest_service.list_quests()
        self.assertGreaterEqual(len(quests), 7)

        # 2. Progress initially zero
        user_quests = self.quest_service.get_user_quests(self.user.id)
        habit = next(q for q in user_quests if q.code == "daily_field_scan")
        self.assertEqual(habit.current_progress, 0)
        self.assertFalse(habit.is_completed)

        # 3. Record an observation with notes
        obs = self.collection_service.record_observation(
            user_id=self.user.id,
            candidate_scientific_name="Passiflora incarnata",
            model_result_json='{"observation_summary": "Purple passionflower"}',
            field_notes="Detailed observation with prominent coronal filaments.",
        )

        # 4. Re-evaluate quests
        updated_quests = self.quest_service.get_user_quests(self.user.id)
        updated_habit = next(q for q in updated_quests if q.code == "daily_field_scan")
        self.assertGreaterEqual(updated_habit.current_progress, 1)
        self.assertTrue(updated_habit.is_completed)
        self.assertIsNone(updated_habit.claimed_at)

        # 5. Claim reward
        success, xp, msg = self.quest_service.claim_quest_reward(
            self.user.id, updated_habit.quest_id
        )
        self.assertTrue(success)
        self.assertEqual(xp, updated_habit.xp_reward)
        self.assertIn("Successfully claimed", msg)

        # 6. Prevent double claim
        retry_success, retry_xp, retry_msg = self.quest_service.claim_quest_reward(
            self.user.id, updated_habit.quest_id
        )
        self.assertFalse(retry_success)
        self.assertIn("already been claimed", retry_msg)

    def test_habit_manual_logging(self) -> None:
        """Verify non-punitive daily habit manual action logging."""
        user_quests = self.quest_service.get_user_quests(self.user.id)
        habit = next(q for q in user_quests if q.code == "daily_field_scan")

        ok = self.quest_service.log_habit_action(self.user.id, habit.quest_id)
        self.assertTrue(ok)

        recheck = self.quest_service.get_user_quests(self.user.id)
        rechecked_habit = next(q for q in recheck if q.code == "daily_field_scan")
        self.assertEqual(rechecked_habit.current_progress, 1)

    # -------------------------------------------------------------------------
    # 4. Researcher Passport and Outputs
    # -------------------------------------------------------------------------
    def test_researcher_passport_profile(self) -> None:
        """Verify researcher passport retrieval, updating, and output provenance."""
        passport = self.passport_service.get_passport(self.user.id)
        self.assertIsNotNone(passport)
        self.assertEqual(passport.username, "naturalist_eva")
        self.assertEqual(passport.display_name, "Eva Rostova")
        self.assertEqual(passport.affiliations, [])
        self.assertEqual(passport.research_interests, [])
        self.assertTrue(passport.is_public)

        # Update passport profile
        ok = self.passport_service.update_passport_profile(
            user_id=self.user.id,
            display_name="Dr. Eva Rostova",
            bio="Canopy ecologist researching Central American epiphytic flora.",
            external_orcid_url="https://orcid.org/0000-0002-1825-0097",
            affiliations=["Smithsonian Tropical Research Institute", "University of Costa Rica"],
            research_interests=["Orchidaceae", "Canopy Micro-climates", "Epiphyte Biomass"],
            is_public=True,
        )
        self.assertTrue(ok)

        updated_passport = self.passport_service.get_passport(self.user.id)
        self.assertEqual(updated_passport.display_name, "Dr. Eva Rostova")
        self.assertEqual(len(updated_passport.affiliations), 2)
        self.assertIn("Smithsonian Tropical Research Institute", updated_passport.affiliations)
        self.assertEqual(len(updated_passport.research_interests), 3)
        self.assertEqual(updated_passport.external_orcid_url, "https://orcid.org/0000-0002-1825-0097")

    def test_research_outputs_and_provenance(self) -> None:
        """Verify research output addition, auto-provenance promotion, and deletion."""
        output1 = self.passport_service.add_research_output(
            user_id=self.user.id,
            title="Monteverde Cloud Forest Vascular Epiphyte Checklist",
            output_type="SPECIES_CHECKLIST",
            doi_or_url="https://doi.org/10.15468/39omei",
            citation="Rostova, E. (2026). Checklist of Monteverde vascular epiphytes. Vivédex Occasional Papers.",
        )
        # Should auto-promote to SOURCE_LINKED because valid DOI/URL was provided
        self.assertEqual(output1.provenance_state, "SOURCE_LINKED")

        output2 = self.passport_service.add_research_output(
            user_id=self.user.id,
            title="Field Notes on Canopy Moss Micro-layers",
            output_type="FIELD_REPORT",
            doi_or_url="",
            citation="Unpublished expedition diary entries.",
        )
        self.assertEqual(output2.provenance_state, "SELF_REPORTED")

        # Update provenance state
        self.passport_service.update_output_provenance(output1.id, "PLATFORM_REVIEWED")

        passport = self.passport_service.get_passport(self.user.id)
        self.assertEqual(len(passport.outputs), 2)
        reviewed_out = next(o for o in passport.outputs if o.id == output1.id)
        self.assertEqual(reviewed_out.provenance_state, "PLATFORM_REVIEWED")

        # Delete output
        deleted = self.passport_service.delete_research_output(self.user.id, output2.id)
        self.assertTrue(deleted)

        rechecked_passport = self.passport_service.get_passport(self.user.id)
        self.assertEqual(len(rechecked_passport.outputs), 1)

    # -------------------------------------------------------------------------
    # 5. Global Search Service
    # -------------------------------------------------------------------------
    def test_global_search_service(self) -> None:
        """Verify cross-entity discovery search across taxa, sites, projects, and users."""
        # Setup searchable entities
        self.eco_service.create_field_site(
            name="Monteverde Cloud Forest Reserve",
            description="Endemic orchids and cloud forest canopy",
            biome="Cloud Forest",
            country="Costa Rica",
        )
        self.eco_service.create_project(
            title="Canopy Epiphyte Census",
            summary="Systematic transects of cloud forest trees",
            target_habitat="Canopy",
        )

        # Search for "Monteverde"
        results = self.search_service.search("Monteverde")
        self.assertGreaterEqual(results.total_matches, 1)
        self.assertTrue(any("Monteverde" in s["name"] for s in results.field_sites))

        # Search for "Eva"
        results_user = self.search_service.search("Eva")
        self.assertGreaterEqual(len(results_user.researchers), 1)
        self.assertEqual(results_user.researchers[0]["username"], "naturalist_eva")

        # Empty query
        empty_res = self.search_service.search("   ")
        self.assertEqual(empty_res.total_matches, 0)


if __name__ == "__main__":
    unittest.main()
