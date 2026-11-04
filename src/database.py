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

SCHEMA_VERSION = 1

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

