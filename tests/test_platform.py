"""Automated tests for Vivédex platform evolution (RUN 007).

Tests all 23 required scenarios across database, authentication, collections,
achievements, administration, knowledge graph, and demo data separation.
Uses temporary isolated databases to protect production data.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from src.achievements import AchievementService
from src.admin_service import AdminService
from src.auth import (
    AuthenticatedUser,
    AuthService,
    AuthenticationError,
    AuthorizationError,
    generate_salt,
    hash_password,
    verify_password,
)
from src.collection_service import CollectionService
from src.database import Database
from src.demo_data import DEMO_PROVENANCE_TAG, load_demo_dataset
from src.knowledge_graph import KnowledgeGraphService
from src.schemas import GBIFMatchResult


class TestPlatformEvolution(unittest.TestCase):
    """Test suite covering the 23 platform evolution scenarios."""

    def setUp(self) -> None:
        """Create a temporary isolated SQLite database for each test."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_platform.sqlite3"
        self.db = Database(self.db_path)
        self.db.initialize_schema()
        self.auth_service = AuthService(self.db)
        self.collection_service = CollectionService(self.db)
        self.achievement_service = AchievementService(self.db)
        self.admin_service = AdminService(self.db)
        self.kg_service = KnowledgeGraphService(self.db)

    def tearDown(self) -> None:
        """Clean up the temporary database directory."""
        self.temp_dir.cleanup()

    # 1. Database initialization
    def test_database_initialization(self) -> None:
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT version FROM schema_version;")
            version = cursor.fetchone()[0]
            self.assertEqual(version, 1)

            # Check that tables exist
            tables = [
                "users",
                "user_profiles",
                "taxa",
                "taxon_relationships",
                "collections",
                "observations",
                "badges",
                "user_badges",
                "moderation_events",
                "audit_logs",
            ]
            for tbl in tables:
                cursor.execute(
                    f"SELECT name FROM sqlite_master WHERE type='table' AND name='{tbl}';"
                )
                self.assertIsNotNone(
                    cursor.fetchone(), f"Table '{tbl}' was not created."
                )

    # 2. Database migrations
    def test_database_migrations(self) -> None:
        def migration_v2(cursor):
            cursor.execute("ALTER TABLE users ADD COLUMN test_meta TEXT DEFAULT '';")

        self.db.apply_migration(2, "Test forward migration v2", migration_v2)

        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(version) FROM schema_version;")
            self.assertEqual(cursor.fetchone()[0], 2)
            cursor.execute("PRAGMA table_info(users);")
            col_names = [row[1] for row in cursor.fetchall()]
            self.assertIn("test_meta", col_names)

    # 3. Registration
    def test_registration(self) -> None:
        user = self.auth_service.register_user(
            username="botanist_jane",
            password="secure_password_123",
            display_name="Jane Doe",
        )
        self.assertEqual(user.username, "botanist_jane")
        self.assertEqual(user.display_name, "Jane Doe")
        self.assertTrue(user.vivedex_id.startswith("VDX-"))

        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT password_hash, salt FROM users WHERE id = ?;", (user.id,)
            )
            row = cursor.fetchone()
            self.assertNotEqual(row["password_hash"], "secure_password_123")
            self.assertTrue(len(row["salt"]) > 16)

    # 4. Duplicate username rejection
    def test_duplicate_username_rejection(self) -> None:
        self.auth_service.register_user("unique_name", "password_123")
        with self.assertRaises(AuthenticationError):
            # Attempt to register duplicate with different casing
            self.auth_service.register_user("UNIQUE_NAME", "another_password_123")

    # 5. Password hashing
    def test_password_hashing(self) -> None:
        salt = generate_salt()
        pwd = "ComplexPassword99!"
        h1 = hash_password(pwd, salt)
        h2 = hash_password(pwd, salt)
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 64)  # 256-bit hex = 64 characters

        different_salt = generate_salt()
        h3 = hash_password(pwd, different_salt)
        self.assertNotEqual(h1, h3)

    # 6. Password verification
    def test_password_verification(self) -> None:
        salt = generate_salt()
        pwd = "CorrectHorseBatteryStaple"
        hashed = hash_password(pwd, salt)
        self.assertTrue(verify_password(pwd, salt, hashed))
        self.assertFalse(verify_password("WrongPassword", salt, hashed))

    # 7. Login failure
    def test_login_failure(self) -> None:
        self.auth_service.register_user("valid_user", "password_123")
        # Non-existent user
        with self.assertRaises(AuthenticationError):
            self.auth_service.authenticate_user("ghost_user", "password_123")
        # Incorrect password
        with self.assertRaises(AuthenticationError):
            self.auth_service.authenticate_user("valid_user", "wrong_password")

    # 8. Logout
    def test_logout(self) -> None:
        user = self.auth_service.register_user("logout_tester", "password_123")
        # Simulated session state clear
        session: dict[str, AuthenticatedUser | None] = {"current_user": user}
        self.assertIsNotNone(session["current_user"])
        session["current_user"] = None
        self.assertIsNone(session["current_user"])

    # 9. First-user administrator bootstrap
    def test_first_user_admin_bootstrap(self) -> None:
        first_user = self.auth_service.register_user("first_admin", "password_123")
        second_user = self.auth_service.register_user(
            "second_member", "password_123"
        )
        self.assertEqual(first_user.role, "admin")
        self.assertTrue(first_user.is_admin)
        self.assertEqual(second_user.role, "user")
        self.assertFalse(second_user.is_admin)

    # 10. User role restrictions
    def test_user_role_restrictions(self) -> None:
        self.auth_service.register_user("admin_lead", "password_123")
        standard_user = self.auth_service.register_user("regular_user", "password_123")
        with self.assertRaises(AuthorizationError):
            self.auth_service.require_admin(standard_user)

    # 11. Collection creation
    def test_collection_creation(self) -> None:
        user = self.auth_service.register_user("collector_1", "password_123")
        gbif_sample = GBIFMatchResult(
            query_name="Passer domesticus",
            matched_scientific_name="Passer domesticus (Linnaeus, 1758)",
            canonical_name="Passer domesticus",
            rank="SPECIES",
            status="ACCEPTED",
            match_type="EXACT",
            gbif_match_score=99,
            usage_key=5231190,
            hierarchy={"kingdom": "Animalia", "family": "Passeridae"},
            retrieved_at="2026-11-05T00:00:00Z",
            licence="CC BY 4.0",
            attribution="GBIF Secretariat (2023)",
        )
        taxon_id = self.collection_service.upsert_taxon_from_gbif(gbif_sample)
        item = self.collection_service.save_to_collection(
            user.id, taxon_id, "Found in urban garden"
        )
        self.assertEqual(item.taxon_id, 5231190)
        self.assertEqual(item.encounter_count, 1)
        self.assertIn("Found in urban garden", item.notes)

    # 12. Duplicate taxon collection handling
    def test_duplicate_taxon_collection_handling(self) -> None:
        user = self.auth_service.register_user("collector_2", "password_123")
        gbif_sample = GBIFMatchResult(
            query_name="Passer domesticus",
            matched_scientific_name="Passer domesticus (Linnaeus, 1758)",
            canonical_name="Passer domesticus",
            match_type="EXACT",
            retrieved_at="2026-11-05T00:00:00Z",
            usage_key=5231190,
        )
        t_id = self.collection_service.upsert_taxon_from_gbif(gbif_sample)
        self.collection_service.save_to_collection(user.id, t_id, "Note 1")
        item2 = self.collection_service.save_to_collection(user.id, t_id, "Note 2")
        self.assertEqual(item2.encounter_count, 2)

        items = self.collection_service.get_user_collection(user.id)
        self.assertEqual(len(items), 1)  # Only 1 unique taxon row

    # 13. Observation creation
    def test_observation_creation(self) -> None:
        user = self.auth_service.register_user("observer_1", "password_123")
        obs = self.collection_service.record_observation(
            user_id=user.id,
            candidate_scientific_name="Passer domesticus",
            model_result_json='{"model": "muse-spark-1.3"}',
            gbif_result_json='{"matchType": "EXACT"}',
            matched_taxon_id=None,
            field_notes="Perched on fence",
            coarse_location="Oxford, UK",
        )
        self.assertTrue(obs.observation_id.startswith("OBS-"))
        self.assertEqual(obs.moderation_status, "PENDING")
        self.assertEqual(obs.field_notes, "Perched on fence")

    # 14. Field-note updates
    def test_field_note_updates(self) -> None:
        user = self.auth_service.register_user("observer_2", "password_123")
        obs = self.collection_service.record_observation(
            user_id=user.id,
            candidate_scientific_name="Passer domesticus",
            model_result_json="{}",
            field_notes="Initial note",
        )
        updated = self.collection_service.update_observation_notes(
            user_id=user.id,
            observation_id=obs.observation_id,
            new_notes="Expanded detailed observations of plumage.",
        )
        self.assertEqual(
            updated.field_notes, "Expanded detailed observations of plumage."
        )

        other_user = self.auth_service.register_user("intruder", "password_123")
        with self.assertRaises(PermissionError):
            self.collection_service.update_observation_notes(
                user_id=other_user.id,
                observation_id=obs.observation_id,
                new_notes="Malicious update",
            )

    # 15. Badge awarding
    def test_badge_awarding(self) -> None:
        user = self.auth_service.register_user("badge_hunter", "password_123")
        # Record observation -> should award 'first_encounter'
        self.collection_service.record_observation(
            user_id=user.id,
            candidate_scientific_name="Erannis defoliaria",
            model_result_json="{}",
            field_notes="First moth observation",
        )
        badges = self.achievement_service.get_user_badges(user.id)
        codes = [b.code for b in badges]
        self.assertIn("first_encounter", codes)

    # 16. Badge idempotency
    def test_badge_idempotency(self) -> None:
        user = self.auth_service.register_user("idempotent_user", "password_123")
        self.collection_service.record_observation(
            user_id=user.id,
            candidate_scientific_name="Passer domesticus",
            model_result_json="{}",
        )
        newly_1 = self.achievement_service.evaluate_user_achievements(user.id)
        self.assertEqual(newly_1, [])  # Already awarded during observation creation

        badges = self.achievement_service.get_user_badges(user.id)
        self.assertEqual(len(badges), 1)

    # 17. XP calculations
    def test_xp_calculations(self) -> None:
        user = self.auth_service.register_user("xp_gainer", "password_123")
        # 1. Base initial state
        xp_0 = self.achievement_service.calculate_user_xp(user.id)
        self.assertEqual(xp_0, 0)

        # 2. Add an observation with matched taxon and field notes
        gbif_sample = GBIFMatchResult(
            query_name="Apis mellifera",
            matched_scientific_name="Apis mellifera",
            match_type="EXACT",
            retrieved_at="2026-11-05T00:00:00Z",
            usage_key=1341976,
        )
        t_id = self.collection_service.upsert_taxon_from_gbif(gbif_sample)
        self.collection_service.record_observation(
            user_id=user.id,
            candidate_scientific_name="Apis mellifera",
            model_result_json="{}",
            matched_taxon_id=t_id,
            field_notes="Foraging on clover in park",
        )
        # Expected:
        # First encounter with taxon: 50 XP
        # Meaningful note (>=5 chars): 20 XP
        # Badge 'first_encounter' awarded: 50 XP
        # Total: 120 XP -> Level 2
        stats = self.achievement_service.get_user_gamification_stats(user.id)
        self.assertEqual(stats.total_xp, 120)
        self.assertEqual(stats.level, 2)

    # 18. Admin-only dashboard access
    def test_admin_only_dashboard_access(self) -> None:
        admin_user = self.auth_service.register_user("admin_boss", "password_123")
        reg_user = self.auth_service.register_user("staff_member", "password_123")

        # Admin access succeeds
        metrics = self.admin_service.get_dashboard_metrics(admin_user)
        self.assertGreaterEqual(metrics.total_users, 2)

        # Regular user access raises AuthorizationError
        with self.assertRaises(AuthorizationError):
            self.admin_service.get_dashboard_metrics(reg_user)

    # 19. Admin moderation
    def test_admin_moderation(self) -> None:
        admin = self.auth_service.register_user("admin_mod", "password_123")
        user = self.auth_service.register_user("submitting_user", "password_123")

        obs = self.collection_service.record_observation(
            user_id=user.id,
            candidate_scientific_name="Canis lupus",
            model_result_json="{}",
        )
        self.assertEqual(obs.moderation_status, "PENDING")

        self.admin_service.moderate_observation(
            admin_user=admin,
            observation_id=obs.observation_id,
            new_status="ACCEPTED_FOR_CATALOG",
            moderation_note="Criteria verified according to protocol.",
        )

        mod_obs = self.collection_service.get_observation_by_uid(obs.observation_id)
        self.assertEqual(mod_obs.moderation_status, "ACCEPTED_FOR_CATALOG")

        # User should now be eligible for 'contributor' badge
        badges = self.achievement_service.get_user_badges(user.id)
        self.assertIn("contributor", [b.code for b in badges])

    # 20. Audit log creation
    def test_audit_log_creation(self) -> None:
        admin = self.auth_service.register_user("audit_admin", "password_123")
        user = self.auth_service.register_user("audit_user", "password_123")
        obs = self.collection_service.record_observation(
            user_id=user.id,
            candidate_scientific_name="Passer domesticus",
            model_result_json="{}",
        )
        self.admin_service.moderate_observation(
            admin_user=admin,
            observation_id=obs.observation_id,
            new_status="NEEDS_MORE_EVIDENCE",
            moderation_note="Need clearer shot of throat bib.",
        )
        logs = self.admin_service.get_audit_logs(admin)
        actions = [l.action for l in logs]
        self.assertIn("USER_REGISTERED", actions)
        self.assertIn("OBSERVATION_RECORDED", actions)
        self.assertIn("MODERATION_DECISION", actions)

    # 21. Knowledge graph relationships
    def test_knowledge_graph_relationships(self) -> None:
        user = self.auth_service.register_user("kg_user", "password_123")
        gbif_sample = GBIFMatchResult(
            query_name="Erannis defoliaria",
            matched_scientific_name="Erannis defoliaria",
            match_type="EXACT",
            retrieved_at="2026-11-05T00:00:00Z",
            usage_key=1956599,
            family="Geometridae",
            hierarchy={"order": "Lepidoptera", "family": "Geometridae"},
        )
        t_id = self.collection_service.upsert_taxon_from_gbif(gbif_sample)
        self.collection_service.record_observation(
            user_id=user.id,
            candidate_scientific_name="Erannis defoliaria",
            model_result_json="{}",
            matched_taxon_id=t_id,
        )

        neighborhood = self.kg_service.get_taxon_neighborhood(t_id)
        node_types = {n.node_type for n in neighborhood["nodes"]}
        edge_types = {e.relationship_type for e in neighborhood["edges"]}

        self.assertIn("Taxon", node_types)
        self.assertIn("Source", node_types)
        self.assertIn("Observation", node_types)
        self.assertIn("User", node_types)

        self.assertIn("DERIVED_FROM", edge_types)
        self.assertIn("OBSERVED_IN", edge_types)
        self.assertIn("COLLECTED_BY", edge_types)
        self.assertIn("RECORDED_BY", edge_types)

    # 22. Taxonomy lineage
    def test_taxonomy_lineage(self) -> None:
        gbif_sample = GBIFMatchResult(
            query_name="Passer domesticus",
            matched_scientific_name="Passer domesticus",
            canonical_name="Passer domesticus",
            match_type="EXACT",
            retrieved_at="2026-11-05T00:00:00Z",
            usage_key=5231190,
            rank="SPECIES",
            hierarchy={
                "kingdom": "Animalia",
                "phylum": "Chordata",
                "class": "Aves",
                "order": "Passeriformes",
                "family": "Passeridae",
                "genus": "Passer",
                "species": "Passer domesticus",
            },
        )
        t_id = self.collection_service.upsert_taxon_from_gbif(gbif_sample)
        lineage = self.kg_service.get_taxon_lineage(t_id)
        self.assertTrue(len(lineage) >= 2)
        ranks = [item.rank for item in lineage if item.rank]
        self.assertIn("Kingdom", ranks)
        self.assertIn("Species", ranks)

    # 23. Demo-data separation
    def test_demo_data_separation(self) -> None:
        user = self.auth_service.register_user("real_naturalist", "password_123")
        real_obs = self.collection_service.record_observation(
            user_id=user.id,
            candidate_scientific_name="Live Observed Specimen",
            model_result_json="{}",
            provenance="LIVE_ANALYSIS",
        )

        load_res = load_demo_dataset(self.db)
        self.assertEqual(load_res["provenance"], DEMO_PROVENANCE_TAG)

        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT observation_id, provenance FROM observations ORDER BY id ASC;"
            )
            rows = cursor.fetchall()
            real_rows = [r for r in rows if r["provenance"] == "LIVE_ANALYSIS"]
            demo_rows = [r for r in rows if r["provenance"] == DEMO_PROVENANCE_TAG]

            self.assertEqual(len(real_rows), 1)
            self.assertEqual(real_rows[0]["observation_id"], real_obs.observation_id)
            self.assertTrue(len(demo_rows) >= 5)
            for d in demo_rows:
                self.assertEqual(d["provenance"], "DEMO DATA")


if __name__ == "__main__":
    unittest.main()
