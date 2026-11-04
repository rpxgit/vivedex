"""SQLite database repository and connection manager for Vivédex.

This module provides thread-safe, context-managed SQLite access.
It supports schema versioning, safe migrations, and foreign key enforcement.
"""

from __future__ import annotations

import contextlib
import os
import sqlite3
from collections.abc import Generator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "vivedex.sqlite3"

SCHEMA_VERSION = 2

INITIAL_BADGES = [
    (
        "first_encounter",
        "First Encounter",
        "Recorded your first organism observation in Vivédex.",
        "First observation saved to the database.",
        "🌱",
        50,
    ),
    (
        "collector",
        "Collector",
        "Saved five distinct taxa to your personal collection.",
        "Five distinct taxa saved in collection.",
        "📚",
        100,
    ),
    (
        "family_explorer",
        "Family Explorer",
        "Recorded observations spanning three distinct taxonomic families.",
        "Three distinct families recorded across observations.",
        "🌳",
        150,
    ),
    (
        "field_naturalist",
        "Field Naturalist",
        "Added informative field notes to five or more observations.",
        "Five observations with non-empty field notes.",
        "📝",
        100,
    ),
    (
        "contributor",
        "Contributor",
        "Had an observation accepted for the platform catalog.",
        "First observation marked as ACCEPTED_FOR_CATALOG.",
        "🏅",
        200,
    ),
]

INITIAL_QUESTS = [
    (
        "daily_field_scan",
        "Daily Field Observation",
        "Record at least one field observation today.",
        "HABIT",
        1,
        25,
        "🔍",
        "OBSERVATION_COUNT",
    ),
    (
        "botanical_journaling",
        "Field Journaling Habit",
        "Attach informative field notes to your observation.",
        "HABIT",
        1,
        25,
        "📓",
        "FIELD_NOTES_COUNT",
    ),
    (
        "weekly_bio_blitz",
        "Weekly BioBlitz",
        "Record 5 organism encounters across your expeditions.",
        "RECURRING_GOAL",
        5,
        100,
        "⚡",
        "OBSERVATION_COUNT",
    ),
    (
        "taxonomic_breadth",
        "Taxonomic Diversity Goal",
        "Encounter species from 3 distinct taxonomic families.",
        "RECURRING_GOAL",
        3,
        120,
        "🌳",
        "FAMILY_COUNT",
    ),
    (
        "restor_explorer",
        "Field Site Explorer",
        "Link at least one observation to an established field site.",
        "MILESTONE",
        1,
        50,
        "📍",
        "SITE_VISIT",
    ),
    (
        "expedition_cadet",
        "Expedition Contributor",
        "Record 3 observations linked to an active expedition.",
        "MILESTONE",
        3,
        150,
        "🧭",
        "OBSERVATION_COUNT",
    ),
    (
        "master_taxonomist",
        "Master Taxonomist",
        "Add 10 distinct taxa to your personal collection.",
        "MILESTONE",
        10,
        250,
        "🏆",
        "COLLECTION_COUNT",
    ),
]


def utc_now_iso() -> str:
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


class Database:
    """Manages SQLite connections, migrations, and schema queries."""

    def __init__(self, db_path: Path | str | None = None) -> None:
        if db_path is None:
            self.db_path = DEFAULT_DB_PATH
        else:
            self.db_path = Path(db_path)

        # Ensure parent directory exists
        if self.db_path != Path(":memory:"):
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextlib.contextmanager
    def connect(self) -> Generator[sqlite3.Connection, None, None]:
        """Provide a context-managed SQLite connection with foreign keys enabled."""
        conn = sqlite3.connect(
            str(self.db_path),
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            timeout=30.0,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize_schema(self) -> None:
        """Create all required tables, indexes, and initial data if not present."""
        with self.connect() as conn:
            cursor = conn.cursor()

            # Schema version table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL,
                    description TEXT NOT NULL
                );
                """
            )

            # Check existing version
            cursor.execute("SELECT MAX(version) FROM schema_version;")
            row = cursor.fetchone()
            current_version = row[0] if row and row[0] is not None else 0

            if current_version < 1:
                self._apply_version_1(cursor)
                cursor.execute(
                    """
                    INSERT INTO schema_version (version, applied_at, description)
                    VALUES (?, ?, ?);
                    """,
                    (1, utc_now_iso(), "Initial core schema for Vivédex platform"),
                )
            else:
                # Ensure extended schema v2 tables exist on pre-existing v1 databases
                self._ensure_extended_schema(cursor)

    def _ensure_extended_schema(self, cursor: sqlite3.Cursor) -> None:
        """Ensure extended ecological, quest, and passport tables exist idempotently."""
        # 1. Update user_profiles with researcher passport fields
        cursor.execute("PRAGMA table_info(user_profiles);")
        profile_cols = [r["name"] for r in cursor.fetchall()]
        if "affiliations" not in profile_cols:
            cursor.execute("ALTER TABLE user_profiles ADD COLUMN affiliations TEXT DEFAULT '[]';")
        if "research_interests" not in profile_cols:
            cursor.execute("ALTER TABLE user_profiles ADD COLUMN research_interests TEXT DEFAULT '[]';")
        if "is_public" not in profile_cols:
            cursor.execute("ALTER TABLE user_profiles ADD COLUMN is_public INTEGER NOT NULL DEFAULT 1;")

        # 2. Organisations table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS organisations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                website_url TEXT DEFAULT '',
                logo_url TEXT DEFAULT '',
                country TEXT DEFAULT '',
                created_at TEXT NOT NULL
            );
            """
        )

        # 3. Field sites table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS field_sites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                biome TEXT DEFAULT '',
                latitude REAL,
                longitude REAL,
                elevation_m REAL,
                country TEXT DEFAULT '',
                created_at TEXT NOT NULL
            );
            """
        )

        # 4. Conservation and research projects
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                summary TEXT DEFAULT '',
                organisation_id INTEGER REFERENCES organisations(id) ON DELETE SET NULL,
                lead_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                target_habitat TEXT DEFAULT '',
                target_species_count INTEGER DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK(status IN ('PLANNING', 'ACTIVE', 'COMPLETED', 'ARCHIVED')),
                created_at TEXT NOT NULL
            );
            """
        )

        # 5. Field expeditions table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS expeditions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                site_id INTEGER REFERENCES field_sites(id) ON DELETE SET NULL,
                project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
                lead_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                start_date TEXT NOT NULL,
                end_date TEXT,
                status TEXT NOT NULL DEFAULT 'PLANNED' CHECK(status IN ('PLANNED', 'IN_PROGRESS', 'CONCLUDED', 'CANCELLED')),
                created_at TEXT NOT NULL
            );
            """
        )

        # 6. Update observations with ecological foreign keys
        cursor.execute("PRAGMA table_info(observations);")
        obs_cols = [r["name"] for r in cursor.fetchall()]
        if "site_id" not in obs_cols:
            cursor.execute("ALTER TABLE observations ADD COLUMN site_id INTEGER REFERENCES field_sites(id) ON DELETE SET NULL;")
        if "expedition_id" not in obs_cols:
            cursor.execute("ALTER TABLE observations ADD COLUMN expedition_id INTEGER REFERENCES expeditions(id) ON DELETE SET NULL;")
        if "project_id" not in obs_cols:
            cursor.execute("ALTER TABLE observations ADD COLUMN project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL;")

        # 7. Quests and field habits table (Habitica-inspired)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS quests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                quest_type TEXT NOT NULL CHECK(quest_type IN ('HABIT', 'RECURRING_GOAL', 'MILESTONE')),
                target_count INTEGER NOT NULL DEFAULT 1,
                xp_reward INTEGER NOT NULL DEFAULT 50,
                icon TEXT DEFAULT '🌿',
                criteria_type TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )

        # 8. User quests tracking table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_quests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                quest_id INTEGER NOT NULL REFERENCES quests(id) ON DELETE CASCADE,
                current_progress INTEGER NOT NULL DEFAULT 0,
                is_completed INTEGER NOT NULL DEFAULT 0,
                completed_at TEXT,
                claimed_at TEXT,
                last_logged_at TEXT,
                UNIQUE(user_id, quest_id)
            );
            """
        )

        # 9. Research outputs table (ORCID-inspired)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS research_outputs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                output_type TEXT NOT NULL CHECK(output_type IN ('DATASET', 'FIELD_REPORT', 'SPECIES_CHECKLIST', 'PUBLICATION', 'OBSERVATION_CATALOG')),
                doi_or_url TEXT DEFAULT '',
                citation TEXT DEFAULT '',
                provenance_state TEXT NOT NULL DEFAULT 'SELF_REPORTED' CHECK(provenance_state IN ('SELF_REPORTED', 'SOURCE_LINKED', 'PLATFORM_REVIEWED', 'EXTERNALLY_VERIFIED')),
                created_at TEXT NOT NULL
            );
            """
        )

        # 10. Indexes for extended schema
        indexes_ext = [
            ("idx_organisations_slug", "organisations", "slug"),
            ("idx_projects_slug", "projects", "slug"),
            ("idx_projects_org", "projects", "organisation_id"),
            ("idx_field_sites_slug", "field_sites", "slug"),
            ("idx_expeditions_site", "expeditions", "site_id"),
            ("idx_expeditions_proj", "expeditions", "project_id"),
            ("idx_quests_code", "quests", "code"),
            ("idx_user_quests_user", "user_quests", "user_id"),
            ("idx_research_outputs_user", "research_outputs", "user_id"),
            ("idx_obs_site_id", "observations", "site_id"),
            ("idx_obs_expedition_id", "observations", "expedition_id"),
            ("idx_obs_project_id", "observations", "project_id"),
        ]

        for index_name, table, column in indexes_ext:
            cursor.execute(
                f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} ({column});"
            )

        # Seed initial quests
        now = utc_now_iso()
        for code, title, desc, q_type, target, xp, icon, crit in INITIAL_QUESTS:
            cursor.execute(
                """
                INSERT OR IGNORE INTO quests (code, title, description, quest_type, target_count, xp_reward, icon, criteria_type, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (code, title, desc, q_type, target, xp, icon, crit, now),
            )

        # Seed initial organisations
        initial_orgs = [
            (
                "kew-gardens",
                "Royal Botanic Gardens, Kew",
                "World-leading botanic garden and scientific research institution devoted to plant and fungal conservation.",
                "https://www.kew.org",
                "",
                "United Kingdom",
            ),
            (
                "smithsonian-stri",
                "Smithsonian Tropical Research Institute",
                "Pioneering long-term tropical ecology research across rainforests and coastal marine habitats.",
                "https://stri.si.edu",
                "",
                "Panama",
            ),
            (
                "wcs-global",
                "Wildlife Conservation Society",
                "Conserving the world's largest wild places across priority ecological regions.",
                "https://www.wcs.org",
                "",
                "United States",
            ),
        ]
        for slug, name, desc, url, logo, country in initial_orgs:
            cursor.execute(
                """
                INSERT OR IGNORE INTO organisations (slug, name, description, website_url, logo_url, country, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (slug, name, desc, url, logo, country, now),
            )

        # Seed initial field sites
        initial_sites = [
            (
                "monteverde-cloud-forest",
                "Monteverde Cloud Forest Reserve",
                "Pristine high-elevation tropical cloud forest sanctuary renowned for epiphyte diversity, mosses, and endemic fauna.",
                "Tropical Montane Cloud Forest",
                10.301,
                -84.793,
                1440.0,
                "Costa Rica",
            ),
            (
                "danum-valley",
                "Danum Valley Conservation Area",
                "Ancient primary lowland dipterocarp rainforest harboring exceptional Southeast Asian biodiversity and canopy habitats.",
                "Tropical Lowland Rainforest",
                4.966,
                117.805,
                200.0,
                "Malaysia",
            ),
            (
                "daintree-rainforest",
                "Daintree Rainforest & Cape Tribulation",
                "One of the oldest surviving rainforest ecosystems on Earth, harboring primitive flowering plant lineages.",
                "Tropical Coastal Rainforest",
                -16.170,
                145.418,
                50.0,
                "Australia",
            ),
        ]
        for slug, name, desc, biome, lat, lon, elev, country in initial_sites:
            cursor.execute(
                """
                INSERT OR IGNORE INTO field_sites (slug, name, description, biome, latitude, longitude, elevation_m, country, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (slug, name, desc, biome, lat, lon, elev, country, now),
            )

        # Seed initial projects
        initial_projects = [
            (
                "epiphyte-canopy-census",
                "Canopy Epiphyte & Lichen Census",
                "Systematic canopy transect mapping documenting micro-climatic gradients and vascular epiphyte communities.",
                1,
                "Cloud Forest Canopy",
                50,
                "ACTIVE",
            ),
            (
                "dipterocarp-regeneration",
                "Dipterocarp Seedling & Soil Microbiome Study",
                "Multi-year forest regeneration monitoring across primary and selectively logged forest plots.",
                2,
                "Lowland Rainforest Floor",
                30,
                "ACTIVE",
            ),
        ]
        for slug, title, summary, org_id, habitat, target_count, status in initial_projects:
            cursor.execute(
                """
                INSERT OR IGNORE INTO projects (slug, title, summary, organisation_id, target_habitat, target_species_count, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (slug, title, summary, org_id, habitat, target_count, status, now),
            )

        # Seed initial expeditions
        initial_expeditions = [
            (
                "monteverde-epiphyte-2026",
                "Monteverde Cloud Forest Epiphyte Expedition",
                "Field team documenting canopy vascular flora and lichens along elevation transects.",
                1,
                1,
                "2026-03-01",
                "2026-03-20",
                "IN_PROGRESS",
            ),
            (
                "danum-riverine-transect-2026",
                "Danum Valley Riverine Ecological Survey",
                "Documenting riparian tree flora, ferns, and associated insect taxa along the Danum River.",
                2,
                2,
                "2026-05-10",
                "2026-05-25",
                "PLANNED",
            ),
        ]
        for slug, title, desc, site_id, proj_id, start_d, end_d, status in initial_expeditions:
            cursor.execute(
                """
                INSERT OR IGNORE INTO expeditions (slug, title, description, site_id, project_id, start_date, end_date, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (slug, title, desc, site_id, proj_id, start_d, end_d, status, now),
            )

    def _apply_version_1(self, cursor: sqlite3.Cursor) -> None:
        """Apply version 1 schema definitions."""
        # 1. Users table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin', 'user')) DEFAULT 'user',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            );
            """
        )

        # 2. User profiles table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                vivedex_id TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                bio TEXT DEFAULT '',
                external_orcid_url TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )

        # 3. Taxa table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS taxa (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                taxon_id INTEGER UNIQUE,
                scientific_name TEXT NOT NULL,
                canonical_name TEXT,
                common_name TEXT,
                rank TEXT,
                status TEXT,
                match_type TEXT,
                kingdom TEXT,
                phylum TEXT,
                class_name TEXT,
                order_name TEXT,
                family TEXT,
                genus TEXT,
                species TEXT,
                authorship TEXT,
                source_id TEXT,
                data_provider TEXT DEFAULT 'GBIF Backbone Taxonomy',
                licence TEXT DEFAULT 'CC BY 4.0',
                attribution TEXT DEFAULT 'GBIF Secretariat (2023). GBIF Backbone Taxonomy. Checklist dataset. https://doi.org/10.15468/39omei',
                retrieved_at TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )

        # 4. Taxon relationships table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS taxon_relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_taxon_id INTEGER NOT NULL REFERENCES taxa(taxon_id) ON DELETE CASCADE,
                child_taxon_id INTEGER NOT NULL REFERENCES taxa(taxon_id) ON DELETE CASCADE,
                relationship_type TEXT NOT NULL CHECK(relationship_type IN ('PARENT_OF', 'SYNONYM_OF')),
                source TEXT DEFAULT 'GBIF',
                created_at TEXT NOT NULL,
                UNIQUE(parent_taxon_id, child_taxon_id, relationship_type)
            );
            """
        )

        # 5. Collections table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS collections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                taxon_id INTEGER NOT NULL REFERENCES taxa(taxon_id) ON DELETE CASCADE,
                first_encounter_at TEXT NOT NULL,
                last_encounter_at TEXT NOT NULL,
                encounter_count INTEGER NOT NULL DEFAULT 1,
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                UNIQUE(user_id, taxon_id)
            );
            """
        )

        # 6. Observations table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                observation_id TEXT UNIQUE NOT NULL,
                owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                candidate_scientific_name TEXT NOT NULL,
                matched_taxon_id INTEGER REFERENCES taxa(taxon_id) ON DELETE SET NULL,
                observation_timestamp TEXT NOT NULL,
                field_notes TEXT DEFAULT '',
                coarse_location TEXT DEFAULT '',
                model_result_json TEXT NOT NULL,
                gbif_result_json TEXT,
                taxonomic_resolution TEXT,
                moderation_status TEXT NOT NULL DEFAULT 'PENDING' CHECK(moderation_status IN ('PENDING', 'ACCEPTED_FOR_CATALOG', 'NEEDS_MORE_EVIDENCE', 'REJECTED')),
                provenance TEXT NOT NULL DEFAULT 'LIVE_ANALYSIS',
                created_at TEXT NOT NULL
            );
            """
        )

        # 7. Badges table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS badges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                rule_description TEXT NOT NULL,
                icon TEXT DEFAULT '',
                xp_reward INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );
            """
        )

        # 8. User badges table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_badges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                badge_id INTEGER NOT NULL REFERENCES badges(id) ON DELETE CASCADE,
                awarded_at TEXT NOT NULL,
                UNIQUE(user_id, badge_id)
            );
            """
        )

        # 9. Moderation events table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS moderation_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                observation_id INTEGER NOT NULL REFERENCES observations(id) ON DELETE CASCADE,
                moderator_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                previous_status TEXT NOT NULL,
                new_status TEXT NOT NULL,
                moderation_note TEXT DEFAULT '',
                created_at TEXT NOT NULL
            );
            """
        )

        # 10. Audit logs table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                action TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id TEXT,
                details TEXT,
                timestamp TEXT NOT NULL
            );
            """
        )

        # Create indexes
        indexes = [
            ("idx_users_username", "users", "username"),
            ("idx_user_profiles_user_id", "user_profiles", "user_id"),
            ("idx_taxa_taxon_id", "taxa", "taxon_id"),
            ("idx_taxa_scientific_name", "taxa", "scientific_name"),
            ("idx_taxon_rel_parent", "taxon_relationships", "parent_taxon_id"),
            ("idx_taxon_rel_child", "taxon_relationships", "child_taxon_id"),
            ("idx_collections_user_id", "collections", "user_id"),
            ("idx_collections_taxon_id", "collections", "taxon_id"),
            ("idx_observations_owner_id", "observations", "owner_id"),
            ("idx_observations_status", "observations", "moderation_status"),
            ("idx_user_badges_user_id", "user_badges", "user_id"),
            ("idx_moderation_obs_id", "moderation_events", "observation_id"),
            ("idx_audit_logs_user_id", "audit_logs", "user_id"),
            ("idx_audit_logs_action", "audit_logs", "action"),
        ]

        for index_name, table, column in indexes:
            cursor.execute(
                f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} ({column});"
            )

        # Seed initial badges
        now = utc_now_iso()
        for code, name, desc, rule, icon, xp in INITIAL_BADGES:
            cursor.execute(
                """
                INSERT OR IGNORE INTO badges (code, name, description, rule_description, icon, xp_reward, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (code, name, desc, rule, icon, xp, now),
            )

        # Apply extended ecological, quest, and passport schema
        self._ensure_extended_schema(cursor)

    def apply_migration(self, version: int, description: str, migration_fn: Any) -> None:
        """Apply a forward migration function within a transaction."""
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(version) FROM schema_version;")
            row = cursor.fetchone()
            current_version = row[0] if row and row[0] is not None else 0

            if current_version < version:
                migration_fn(cursor)
                cursor.execute(
                    """
                    INSERT INTO schema_version (version, applied_at, description)
                    VALUES (?, ?, ?);
                    """,
                    (version, utc_now_iso(), description),
                )

