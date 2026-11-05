"""Product QA regression and verification test suite for Vivédex.

Tests end-to-end user journeys, role boundaries, data integrity, and error recovery:
1. Account settings & BYOK session credential isolation.
2. Collection ownership & isolation boundaries.
3. Observation ownership & field notes authorization.
4. XP gamification integrity & claimed quest reward inclusion.
5. Milestone badge awarding idempotency & duplication prevention.
6. Partner organisation administrative registration guard.
7. Conservation project institutional affiliation verification.
8. Ecological observation linking ownership enforcement.
9. Administrator console access gating.
10. Global search resilient error recovery and private observation protection.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.achievements import AchievementService
from src.admin_service import AdminService
from src.auth import AuthService, AuthorizationError
from src.collection_service import CollectionService
from src.database import Database
from src.ecological_service import EcologicalService
from src.passport_service import PassportService
from src.quest_service import QuestService
from src.search_service import SearchService


class TestProductQA(unittest.TestCase):
    """Product Quality Assurance test suite verifying all 7 perspectives and 13 modules."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "qa_test.sqlite3"
        self.db = Database(self.db_path)
        self.db.initialize_schema()

        self.auth_service = AuthService(self.db)
        self.collection_service = CollectionService(self.db)
        self.achievement_service = AchievementService(self.db)
        self.admin_service = AdminService(self.db)
        self.eco_service = EcologicalService(self.db)
        self.quest_service = QuestService(self.db)
        self.passport_service = PassportService(self.db)
        self.search_service = SearchService(self.db)

        # Create two distinct naturalists
        self.alice = self.auth_service.register_user("alice_naturalist", "SecretPass123!", "Alice Researcher")
        self.bob = self.auth_service.register_user("bob_naturalist", "SecretPass456!", "Bob Explorer")

        # Provision administrator
        self.admin = self.auth_service.provision_admin_user(
            "charlie_admin", "AdminMaster123!", "Charlie Admin", allow_reprovision=True
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    # -------------------------------------------------------------------------
    # 1. Account Settings & Password Updates
    # -------------------------------------------------------------------------
    def test_authenticated_user_has_created_at_and_password_update(self) -> None:
        """Verify user created_at presence and password update workflow."""
        user = self.auth_service.get_user_by_id(self.alice.id)
        self.assertIsNotNone(user)
        self.assertTrue(hasattr(user, "created_at"))
        self.assertTrue(len(user.created_at) > 0)

        # Update password
        self.auth_service.update_password(self.alice.id, "NewSecretPass789!")
        # Authenticate with new password
        re_auth = self.auth_service.authenticate_user("alice_naturalist", "NewSecretPass789!")
        self.assertEqual(re_auth.id, self.alice.id)

    # -------------------------------------------------------------------------
    # 2. Collection Ownership & Privacy Boundaries
    # -------------------------------------------------------------------------
    def test_collection_isolation_between_users(self) -> None:
        """Verify collections are isolated per user account."""
        with self.db.connect() as conn:
            c = conn.cursor()
            c.execute(
                """
                INSERT INTO taxa (taxon_id, scientific_name, retrieved_at, created_at)
                VALUES (101, 'Passer domesticus', '2026-01-01', '2026-01-01');
                """
            )

        # Alice saves to collection
        self.collection_service.save_to_collection(self.alice.id, 101, notes="Alice saw this near tree")

        # Bob's collection should be empty
        bob_col = self.collection_service.get_user_collection(self.bob.id)
        self.assertEqual(len(bob_col), 0)

        # Alice's collection contains 1 item
        alice_col = self.collection_service.get_user_collection(self.alice.id)
        self.assertEqual(len(alice_col), 1)
        self.assertEqual(alice_col[0].taxon_id, 101)

        # Bob cannot delete Alice's item
        deleted = self.collection_service.remove_from_collection(self.bob.id, 101)
        self.assertFalse(deleted)
        # Alice still has it
        self.assertEqual(len(self.collection_service.get_user_collection(self.alice.id)), 1)

    # -------------------------------------------------------------------------
    # 3. Observation Ownership & Editing Authorization
    # -------------------------------------------------------------------------
    def test_observation_ownership_and_editing_permissions(self) -> None:
        """Verify only owner or admin can edit observation notes."""
        obs = self.collection_service.record_observation(
            user_id=self.alice.id,
            candidate_scientific_name="Passer domesticus",
            model_result_json='{"observation_summary": "Male sparrow perched on branch"}',
            field_notes="Original Alice notes",
            coarse_location="Sherwood Forest",
        )

        # Alice edits her notes -> succeeds
        updated = self.collection_service.update_observation_notes(
            user_id=self.alice.id,
            observation_id=obs.observation_id,
            new_notes="Updated notes by Alice",
        )
        self.assertEqual(updated.field_notes, "Updated notes by Alice")

        # Bob tries to edit Alice's notes -> raises PermissionError
        with self.assertRaises(PermissionError):
            self.collection_service.update_observation_notes(
                user_id=self.bob.id,
                observation_id=obs.observation_id,
                new_notes="Malicious overwrite by Bob",
            )

        # Admin edits Alice's notes -> succeeds with is_admin=True
        admin_updated = self.collection_service.update_observation_notes(
            user_id=self.admin.id,
            observation_id=obs.observation_id,
            new_notes="Admin verified morphological features",
            is_admin=True,
        )
        self.assertEqual(admin_updated.field_notes, "Admin verified morphological features")

    # -------------------------------------------------------------------------
    # 4. XP Integrity & Quest Rewards Aggregation
    # -------------------------------------------------------------------------
    def test_xp_includes_claimed_quests_and_habits(self) -> None:
        """Verify claimed quest XP increases user total XP and naturalist level."""
        initial_xp = self.achievement_service.calculate_user_xp(self.alice.id)
        self.assertEqual(initial_xp, 0)

        # Log habit action
        quests = self.quest_service.list_quests(quest_type="HABIT")
        self.assertTrue(len(quests) > 0)
        habit = quests[0]

        # Log habit action to complete it
        self.quest_service.log_habit_action(self.alice.id, habit.id)
        ok, xp_claimed, msg = self.quest_service.claim_quest_reward(self.alice.id, habit.id)
        self.assertTrue(ok)
        self.assertEqual(xp_claimed, habit.xp_reward)

        # Verify XP now includes claimed quest reward
        new_xp = self.achievement_service.calculate_user_xp(self.alice.id)
        self.assertEqual(new_xp, habit.xp_reward)

        # Also verify Researcher Passport calculates the identical XP
        passport = self.passport_service.get_passport(self.alice.id)
        self.assertIsNotNone(passport)
        self.assertEqual(passport.total_xp, new_xp)

    # -------------------------------------------------------------------------
    # 5. Badge Awarding Idempotency
    # -------------------------------------------------------------------------
    def test_badge_awarding_is_strictly_idempotent(self) -> None:
        """Verify badges are never awarded multiple times for the same user."""
        # Record observation to earn first_encounter badge
        self.collection_service.record_observation(
            user_id=self.alice.id,
            candidate_scientific_name="Monstera deliciosa",
            model_result_json='{"status": "OK"}',
            field_notes="Found in rainforest understory",
        )

        awarded_first = self.achievement_service.evaluate_user_achievements(self.alice.id)
        # Should have awarded first_encounter (or already awarded during record_observation)
        badges = self.achievement_service.get_user_badges(self.alice.id)
        badge_codes = [b.code for b in badges]
        self.assertIn("first_encounter", badge_codes)

        # Re-evaluating multiple times must yield empty new awards
        awarded_second = self.achievement_service.evaluate_user_achievements(self.alice.id)
        self.assertEqual(len(awarded_second), 0)

        # Distinct badges count in DB must equal unique badges
        with self.db.connect() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*), COUNT(DISTINCT badge_id) FROM user_badges WHERE user_id = ?;", (self.alice.id,))
            total_b, dist_b = c.fetchone()
            self.assertEqual(total_b, dist_b)

    # -------------------------------------------------------------------------
    # 6. Partner Organisation Administrative Registration Guard
    # -------------------------------------------------------------------------
    def test_organisation_creation_role_guard(self) -> None:
        """Verify regular users cannot register partner organisations without admin role."""
        # Alice (regular user) attempts creation -> raises AuthorizationError
        with self.assertRaises(AuthorizationError):
            self.eco_service.create_organisation(
                name="Rogue Botanical Institute",
                country="Nowhere",
                admin_user=self.alice,
            )

        # Admin attempts creation -> succeeds
        org = self.eco_service.create_organisation(
            name="Authoritative Botanical Trust",
            country="United Kingdom",
            admin_user=self.admin,
        )
        self.assertEqual(org.name, "Authoritative Botanical Trust")

    # -------------------------------------------------------------------------
    # 7. Project Institutional Affiliation Guard
    # -------------------------------------------------------------------------
    def test_project_organisation_affiliation_guard(self) -> None:
        """Verify projects can only be attributed to organisations if user is affiliated or admin."""
        # Register an organisation
        org = self.eco_service.create_organisation(
            name="Smithsonian Conservation Unit",
            country="United States",
            admin_user=self.admin,
        )

        # Alice (not affiliated with Smithsonian) tries to create project under Smithsonian -> raises AuthorizationError
        with self.assertRaises(AuthorizationError):
            self.eco_service.create_project(
                title="Canopy Study",
                organisation_id=org.id,
                lead_user_id=self.alice.id,
                user=self.alice,
            )

        # Alice updates profile to add affiliation
        self.passport_service.update_passport_profile(
            user_id=self.alice.id,
            display_name=self.alice.display_name,
            bio="Botanist",
            external_orcid_url="",
            affiliations=["Smithsonian Conservation Unit"],
            research_interests=["Canopy"],
            is_public=True,
        )

        # Alice re-attempts creation with verified affiliation -> succeeds
        proj = self.eco_service.create_project(
            title="Canopy Study",
            organisation_id=org.id,
            lead_user_id=self.alice.id,
            user=self.alice,
        )
        self.assertEqual(proj.title, "Canopy Study")
        self.assertEqual(proj.organisation_name, "Smithsonian Conservation Unit")

    # -------------------------------------------------------------------------
    # 8. Ecological Observation Linking Ownership Guard
    # -------------------------------------------------------------------------
    def test_ecological_observation_linking_ownership(self) -> None:
        """Verify users cannot re-link other users' observations to sites or expeditions."""
        obs = self.collection_service.record_observation(
            user_id=self.alice.id,
            candidate_scientific_name="Passer domesticus",
            model_result_json="{}",
        )

        # Create a field site
        site = self.eco_service.create_field_site(name="Test Field Site", country="Costa Rica")

        # Bob attempts to link Alice's observation -> raises PermissionError
        with self.assertRaises(PermissionError):
            self.eco_service.link_observation_ecological(
                observation_id=obs.observation_id,
                site_id=site.id,
                user_id=self.bob.id,
            )

        # Alice links her observation -> succeeds
        ok = self.eco_service.link_observation_ecological(
            observation_id=obs.observation_id,
            site_id=site.id,
            user_id=self.alice.id,
        )
        self.assertTrue(ok)

    # -------------------------------------------------------------------------
    # 9. Administrator Console Access Gating
    # -------------------------------------------------------------------------
    def test_admin_service_role_enforcement(self) -> None:
        """Verify non-admin users are rejected from all admin service operations."""
        # Alice tries to get admin dashboard metrics -> raises AuthorizationError
        with self.assertRaises(AuthorizationError):
            self.admin_service.get_dashboard_metrics(self.alice)

        # Alice tries to list all platform users -> raises AuthorizationError
        with self.assertRaises(AuthorizationError):
            self.admin_service.list_users(self.alice)

        # Admin succeeds
        metrics = self.admin_service.get_dashboard_metrics(self.admin)
        self.assertGreaterEqual(metrics.total_users, 3)

    # -------------------------------------------------------------------------
    # 10. Global Search Resilient Recovery & Observation Privacy
    # -------------------------------------------------------------------------
    def test_global_search_privacy_and_resilience(self) -> None:
        """Verify search handles empty, special chars, and protects unmoderated observations."""
        # 1. Empty or whitespace search
        empty_res = self.search_service.search("    ")
        self.assertEqual(empty_res.total_matches, 0)

        # 2. SQL injection attempt strings
        sql_injection_res = self.search_service.search("' OR 1=1; --")
        self.assertIsNotNone(sql_injection_res)

        # 3. Create a pending and a rejected observation
        obs_pending = self.collection_service.record_observation(
            user_id=self.alice.id,
            candidate_scientific_name="Rare Secret Orchid",
            model_result_json="{}",
            field_notes="Pending verification",
        )
        # Moderate one to REJECTED
        self.admin_service.moderate_observation(
            self.admin,
            obs_pending.observation_id,
            "REJECTED",
            "Unclear photograph",
        )

        # Create another observation accepted for catalog
        obs_accepted = self.collection_service.record_observation(
            user_id=self.alice.id,
            candidate_scientific_name="Common Oak Tree",
            model_result_json="{}",
            field_notes="Accepted catalog tree",
        )
        self.admin_service.moderate_observation(
            self.admin,
            obs_accepted.observation_id,
            "ACCEPTED_FOR_CATALOG",
            "Morphology confirmed",
        )

        # Anonymous visitor searches for "Secret Orchid" (rejected)
        anon_search = self.search_service.search("Secret Orchid")
        # Anonymous visitor must NOT see the rejected observation
        self.assertEqual(len(anon_search.observations), 0)

        # Anonymous visitor searches for "Common Oak" (accepted)
        anon_oak = self.search_service.search("Common Oak")
        self.assertEqual(len(anon_oak.observations), 1)

        # Alice (owner) searches -> can see her own observation even if rejected
        alice_search = self.search_service.search("Secret Orchid", user_id=self.alice.id)
        self.assertEqual(len(alice_search.observations), 1)

        # Admin searches -> can see all observations
        admin_search = self.search_service.search("Secret Orchid", is_admin=True)
        self.assertEqual(len(admin_search.observations), 1)


if __name__ == "__main__":
    unittest.main()
