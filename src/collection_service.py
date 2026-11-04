"""Service managing taxa, user collections, field observations, and researcher profiles.

Ensures data integrity, handles duplicate encounters, and connects with the badge engine.
"""

from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from typing import Any

from src.achievements import AchievementService
from src.database import Database, utc_now_iso
from src.models import CollectionItem, ObservationRecord, TaxonRecord, UserProfileRecord
from src.schemas import GBIFMatchResult


def generate_observation_id() -> str:
    """Generate a clean, unique observation identifier."""
    token = secrets.token_hex(4).upper()
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"OBS-{date_str}-{token}"


class CollectionService:
    """Provides collection, observation, and taxon operations."""

    def __init__(self, db: Database) -> None:
        self.db = db
        self.achievement_service = AchievementService(db)

    def upsert_taxon_from_gbif(
        self,
        gbif_result: GBIFMatchResult,
        candidate_name: str | None = None,
    ) -> int:
        """Insert or update a taxon record from a GBIF match result.

        Returns the taxon_id used as reference.
        """
        now = utc_now_iso()
        # Support both GBIFMatchResult schema and raw response objects
        usage_key = getattr(gbif_result, "usage_key", None) or getattr(gbif_result, "usageKey", None)
        if usage_key is not None:
            taxon_id = usage_key
        else:
            name_seed = (
                getattr(gbif_result, "matched_scientific_name", None)
                or getattr(gbif_result, "scientificName", None)
                or candidate_name
                or "Unknown"
            )
            taxon_id = -(abs(hash(name_seed)) % 1_000_000_000)

        scientific_name = (
            getattr(gbif_result, "matched_scientific_name", None)
            or getattr(gbif_result, "scientificName", None)
            or candidate_name
            or "Unknown taxon"
        )
        canonical_name = getattr(gbif_result, "canonical_name", None) or getattr(gbif_result, "canonicalName", None)
        rank = getattr(gbif_result, "rank", None)
        status = getattr(gbif_result, "status", None)
        match_type = getattr(gbif_result, "match_type", None) or getattr(gbif_result, "matchType", None)

        hierarchy = getattr(gbif_result, "hierarchy", None)
        if isinstance(hierarchy, dict):
            kingdom = hierarchy.get("kingdom")
            phylum = hierarchy.get("phylum")
            class_name = hierarchy.get("class")
            order_name = hierarchy.get("order")
            family = hierarchy.get("family")
            genus = hierarchy.get("genus")
            species = hierarchy.get("species")
        else:
            kingdom = getattr(gbif_result, "kingdom", None)
            phylum = getattr(gbif_result, "phylum", None)
            class_name = getattr(gbif_result, "class_name", None) or getattr(gbif_result, "class", None)
            order_name = getattr(gbif_result, "order", None)
            family = getattr(gbif_result, "family", None)
            genus = getattr(gbif_result, "genus", None)
            species = getattr(gbif_result, "species", None)

        data_provider = getattr(gbif_result, "provider", "GBIF Backbone Taxonomy")
        licence = getattr(gbif_result, "licence", "CC BY 4.0")
        attribution = getattr(gbif_result, "attribution", None) or (
            "GBIF Secretariat (2023). GBIF Backbone Taxonomy. Checklist dataset. https://doi.org/10.15468/39omei"
        )

        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO taxa (
                    taxon_id, scientific_name, canonical_name, common_name, rank,
                    status, match_type, kingdom, phylum, class_name, order_name,
                    family, genus, species, data_provider, licence, attribution,
                    retrieved_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(taxon_id) DO UPDATE SET
                    scientific_name = excluded.scientific_name,
                    canonical_name = excluded.canonical_name,
                    rank = excluded.rank,
                    status = excluded.status,
                    match_type = excluded.match_type,
                    kingdom = excluded.kingdom,
                    phylum = excluded.phylum,
                    class_name = excluded.class_name,
                    order_name = excluded.order_name,
                    family = excluded.family,
                    genus = excluded.genus,
                    species = excluded.species,
                    retrieved_at = excluded.retrieved_at;
                """,
                (
                    taxon_id,
                    scientific_name,
                    canonical_name,
                    None,
                    rank,
                    status,
                    match_type,
                    kingdom,
                    phylum,
                    class_name,
                    order_name,
                    family,
                    genus,
                    species,
                    data_provider,
                    licence,
                    attribution,
                    now,
                    now,
                ),
            )

            # Store hierarchical taxon relationships if usage keys are available
            # Build hierarchy edges: kingdom -> phylum -> class -> order -> family -> genus -> species
            hierarchy_steps = [
                (
                    getattr(gbif_result, "kingdomKey", None),
                    kingdom or getattr(gbif_result, "kingdom", None),
                    "Kingdom",
                ),
                (
                    getattr(gbif_result, "phylumKey", None),
                    phylum or getattr(gbif_result, "phylum", None),
                    "Phylum",
                ),
                (
                    getattr(gbif_result, "classKey", None),
                    class_name or getattr(gbif_result, "class_name", None),
                    "Class",
                ),
                (
                    getattr(gbif_result, "orderKey", None),
                    order_name or getattr(gbif_result, "order", None),
                    "Order",
                ),
                (
                    getattr(gbif_result, "familyKey", None),
                    family or getattr(gbif_result, "family", None),
                    "Family",
                ),
                (
                    getattr(gbif_result, "genusKey", None),
                    genus or getattr(gbif_result, "genus", None),
                    "Genus",
                ),
                (
                    getattr(gbif_result, "speciesKey", None) or usage_key,
                    species or getattr(gbif_result, "species", None) or scientific_name,
                    "Species",
                ),
            ]

            valid_steps = []
            for k, name, r in hierarchy_steps:
                if name:
                    clean_name = str(name).strip()
                    if clean_name:
                        key = k if k is not None else (abs(hash(f"{r}:{clean_name}")) % 900_000_000) + 100_000_000
                        valid_steps.append((key, clean_name, r))

            for i in range(len(valid_steps)):
                key, name, r = valid_steps[i]
                # Ensure higher-level taxon exists in taxa table
                cursor.execute(
                    """
                    INSERT INTO taxa (taxon_id, scientific_name, rank, retrieved_at, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(taxon_id) DO UPDATE SET
                        scientific_name = excluded.scientific_name,
                        rank = excluded.rank;
                    """,
                    (key, name, r, now, now),
                )
                if i > 0:
                    parent_key = valid_steps[i - 1][0]
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO taxon_relationships (
                            parent_taxon_id, child_taxon_id, relationship_type, source, created_at
                        ) VALUES (?, ?, 'PARENT_OF', 'GBIF', ?);
                        """,
                        (parent_key, key, now),
                    )

            return taxon_id

    def save_to_collection(
        self,
        user_id: int,
        taxon_id: int,
        notes: str = "",
    ) -> CollectionItem:
        """Save a taxon to a user's collection or increment its encounter count.

        Idempotent: saving the same taxon again increments encounters without creating duplicates.
        """
        now = utc_now_iso()
        with self.db.connect() as conn:
            cursor = conn.cursor()

            # Check existing entry
            cursor.execute(
                """
                SELECT id, encounter_count, first_encounter_at, notes
                FROM collections
                WHERE user_id = ? AND taxon_id = ?;
                """,
                (user_id, taxon_id),
            )
            row = cursor.fetchone()

            if row:
                item_id, count, first_enc, existing_notes = row
                new_count = count + 1
                combined_notes = (
                    f"{existing_notes}\n{notes}".strip() if notes else existing_notes
                )
                cursor.execute(
                    """
                    UPDATE collections
                    SET encounter_count = ?, last_encounter_at = ?, notes = ?
                    WHERE id = ?;
                    """,
                    (new_count, now, combined_notes, item_id),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO collections (
                        user_id, taxon_id, first_encounter_at, last_encounter_at,
                        encounter_count, notes, created_at
                    ) VALUES (?, ?, ?, ?, 1, ?, ?);
                    """,
                    (user_id, taxon_id, now, now, notes.strip(), now),
                )
                item_id = cursor.lastrowid

            cursor.execute(
                """
                INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details, timestamp)
                VALUES (?, 'COLLECTION_UPDATED', 'TAXON', ?, ?, ?);
                """,
                (user_id, str(taxon_id), f"Encounter saved. Taxon: {taxon_id}", now),
            )

        # Trigger badge evaluation
        self.achievement_service.evaluate_user_achievements(user_id)

        return self.get_collection_item(user_id, taxon_id)

    def remove_from_collection(self, user_id: int, taxon_id: int) -> bool:
        """Remove a taxon from the user's collection."""
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM collections WHERE user_id = ? AND taxon_id = ?;",
                (user_id, taxon_id),
            )
            deleted = cursor.rowcount > 0
            if deleted:
                now = utc_now_iso()
                cursor.execute(
                    """
                    INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details, timestamp)
                    VALUES (?, 'COLLECTION_REMOVED', 'TAXON', ?, 'Removed from collection', ?);
                    """,
                    (user_id, str(taxon_id), now),
                )
            return deleted

    def get_collection_item(self, user_id: int, taxon_id: int) -> CollectionItem:
        """Fetch a specific collection item with taxon details."""
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT c.id, c.user_id, c.taxon_id, c.first_encounter_at, c.last_encounter_at,
                       c.encounter_count, c.notes, c.created_at,
                       t.scientific_name, t.common_name, t.rank, t.family, t.kingdom
                FROM collections c
                JOIN taxa t ON c.taxon_id = t.taxon_id
                WHERE c.user_id = ? AND c.taxon_id = ?;
                """,
                (user_id, taxon_id),
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError(
                    f"Collection item for user {user_id} and taxon {taxon_id} not found."
                )

            return CollectionItem(
                id=row["id"],
                user_id=row["user_id"],
                taxon_id=row["taxon_id"],
                first_encounter_at=row["first_encounter_at"],
                last_encounter_at=row["last_encounter_at"],
                encounter_count=row["encounter_count"],
                notes=row["notes"],
                scientific_name=row["scientific_name"],
                common_name=row["common_name"],
                rank=row["rank"],
                family=row["family"],
                kingdom=row["kingdom"],
                created_at=row["created_at"],
            )

    def get_user_collection(
        self,
        user_id: int,
        query: str = "",
        family: str = "",
        kingdom: str = "",
    ) -> list[CollectionItem]:
        """Fetch all taxa saved by the user with optional filtering."""
        with self.db.connect() as conn:
            cursor = conn.cursor()
            sql = """
                SELECT c.id, c.user_id, c.taxon_id, c.first_encounter_at, c.last_encounter_at,
                       c.encounter_count, c.notes, c.created_at,
                       t.scientific_name, t.common_name, t.rank, t.family, t.kingdom
                FROM collections c
                JOIN taxa t ON c.taxon_id = t.taxon_id
                WHERE c.user_id = ?
            """
            params: list[Any] = [user_id]

            if query.strip():
                sql += " AND (t.scientific_name LIKE ? OR t.common_name LIKE ?)"
                search_term = f"%{query.strip()}%"
                params.extend([search_term, search_term])

            if family.strip():
                sql += " AND t.family = ?"
                params.append(family.strip())

            if kingdom.strip():
                sql += " AND t.kingdom = ?"
                params.append(kingdom.strip())

            sql += " ORDER BY c.last_encounter_at DESC;"

            cursor.execute(sql, params)
            return [
                CollectionItem(
                    id=row["id"],
                    user_id=row["user_id"],
                    taxon_id=row["taxon_id"],
                    first_encounter_at=row["first_encounter_at"],
                    last_encounter_at=row["last_encounter_at"],
                    encounter_count=row["encounter_count"],
                    notes=row["notes"],
                    scientific_name=row["scientific_name"],
                    common_name=row["common_name"],
                    rank=row["rank"],
                    family=row["family"],
                    kingdom=row["kingdom"],
                    created_at=row["created_at"],
                )
                for row in cursor.fetchall()
            ]

    def record_observation(
        self,
        user_id: int,
        candidate_scientific_name: str,
        model_result_json: str,
        gbif_result_json: str | None = None,
        matched_taxon_id: int | None = None,
        field_notes: str = "",
        coarse_location: str = "",
        provenance: str = "LIVE_ANALYSIS",
    ) -> ObservationRecord:
        """Create a persistent observation record.

        Also updates the personal collection and evaluates achievements.
        """
        observation_id = generate_observation_id()
        now = utc_now_iso()

        # Extract resolution if GBIF is available
        taxonomic_resolution = None
        if gbif_result_json:
            try:
                g_data = json.loads(gbif_result_json)
                taxonomic_resolution = g_data.get("matchType") or g_data.get("rank")
            except Exception:
                pass

        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO observations (
                    observation_id, owner_id, candidate_scientific_name, matched_taxon_id,
                    observation_timestamp, field_notes, coarse_location, model_result_json,
                    gbif_result_json, taxonomic_resolution, moderation_status, provenance,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', ?, ?);
                """,
                (
                    observation_id,
                    user_id,
                    candidate_scientific_name,
                    matched_taxon_id,
                    now,
                    field_notes.strip(),
                    coarse_location.strip(),
                    model_result_json,
                    gbif_result_json,
                    taxonomic_resolution,
                    provenance,
                    now,
                ),
            )
            row_id = cursor.lastrowid

            cursor.execute(
                """
                INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details, timestamp)
                VALUES (?, 'OBSERVATION_RECORDED', 'OBSERVATION', ?, ?, ?);
                """,
                (
                    user_id,
                    observation_id,
                    f"Candidate: {candidate_scientific_name}",
                    now,
                ),
            )

        # If matched to a taxon, automatically record an encounter in the user's collection
        if matched_taxon_id is not None:
            self.save_to_collection(
                user_id=user_id,
                taxon_id=matched_taxon_id,
                notes=field_notes.strip(),
            )

        # Evaluate achievements
        self.achievement_service.evaluate_user_achievements(user_id)

        return self.get_observation_by_uid(observation_id)

    def update_observation_notes(
        self,
        user_id: int,
        observation_id: str,
        new_notes: str,
        is_admin: bool = False,
    ) -> ObservationRecord:
        """Update field notes for an existing observation. Requires ownership or admin."""
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, owner_id FROM observations WHERE observation_id = ?;",
                (observation_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Observation {observation_id} does not exist.")

            obs_id, owner_id = row
            if owner_id != user_id and not is_admin:
                raise PermissionError(
                    "You can only edit field notes on your own observations."
                )

            cursor.execute(
                "UPDATE observations SET field_notes = ? WHERE id = ?;",
                (new_notes.strip(), obs_id),
            )

            now = utc_now_iso()
            cursor.execute(
                """
                INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details, timestamp)
                VALUES (?, 'OBSERVATION_NOTES_UPDATED', 'OBSERVATION', ?, 'Updated field notes', ?);
                """,
                (user_id, observation_id, now),
            )

        # Re-evaluate achievements (e.g. Field Naturalist badge)
        self.achievement_service.evaluate_user_achievements(owner_id)

        return self.get_observation_by_uid(observation_id)

    def get_observation_by_uid(self, observation_id: str) -> ObservationRecord:
        """Fetch an observation record by unique observation ID."""
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, observation_id, owner_id, candidate_scientific_name,
                       matched_taxon_id, observation_timestamp, field_notes,
                       coarse_location, model_result_json, gbif_result_json,
                       taxonomic_resolution, moderation_status, provenance, created_at
                FROM observations
                WHERE observation_id = ?;
                """,
                (observation_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Observation {observation_id} not found.")

            return ObservationRecord(
                id=row["id"],
                observation_id=row["observation_id"],
                owner_id=row["owner_id"],
                candidate_scientific_name=row["candidate_scientific_name"],
                matched_taxon_id=row["matched_taxon_id"],
                observation_timestamp=row["observation_timestamp"],
                field_notes=row["field_notes"],
                coarse_location=row["coarse_location"],
                model_result_json=row["model_result_json"],
                gbif_result_json=row["gbif_result_json"],
                taxonomic_resolution=row["taxonomic_resolution"],
                moderation_status=row["moderation_status"],
                provenance=row["provenance"],
                created_at=row["created_at"],
            )

    def get_user_observations(
        self,
        user_id: int,
        status_filter: str = "",
    ) -> list[ObservationRecord]:
        """Fetch all observations owned by a specific user."""
        with self.db.connect() as conn:
            cursor = conn.cursor()
            sql = """
                SELECT id, observation_id, owner_id, candidate_scientific_name,
                       matched_taxon_id, observation_timestamp, field_notes,
                       coarse_location, model_result_json, gbif_result_json,
                       taxonomic_resolution, moderation_status, provenance, created_at
                FROM observations
                WHERE owner_id = ?
            """
            params: list[Any] = [user_id]
            if status_filter.strip():
                sql += " AND moderation_status = ?"
                params.append(status_filter.strip())

            sql += " ORDER BY observation_timestamp DESC;"

            cursor.execute(sql, params)
            return [
                ObservationRecord(
                    id=row["id"],
                    observation_id=row["observation_id"],
                    owner_id=row["owner_id"],
                    candidate_scientific_name=row["candidate_scientific_name"],
                    matched_taxon_id=row["matched_taxon_id"],
                    observation_timestamp=row["observation_timestamp"],
                    field_notes=row["field_notes"],
                    coarse_location=row["coarse_location"],
                    model_result_json=row["model_result_json"],
                    gbif_result_json=row["gbif_result_json"],
                    taxonomic_resolution=row["taxonomic_resolution"],
                    moderation_status=row["moderation_status"],
                    provenance=row["provenance"],
                    created_at=row["created_at"],
                )
                for row in cursor.fetchall()
            ]

    def get_user_profile(self, user_id: int) -> UserProfileRecord | None:
        """Fetch researcher profile and computed summary metrics."""
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT u.id, u.username, u.role, u.created_at as join_date,
                       p.vivedex_id, p.display_name, p.bio, p.external_orcid_url
                FROM users u
                LEFT JOIN user_profiles p ON u.id = p.user_id
                WHERE u.id = ?;
                """,
                (user_id,),
            )
            u_row = cursor.fetchone()
            if not u_row:
                return None

            cursor.execute(
                "SELECT COUNT(*) FROM observations WHERE owner_id = ?;", (user_id,)
            )
            obs_count = cursor.fetchone()[0] or 0

            cursor.execute(
                "SELECT COUNT(DISTINCT taxon_id) FROM collections WHERE user_id = ?;",
                (user_id,),
            )
            distinct_taxa = cursor.fetchone()[0] or 0

            cursor.execute(
                """
                SELECT COUNT(DISTINCT t.family)
                FROM observations o
                JOIN taxa t ON o.matched_taxon_id = t.taxon_id
                WHERE o.owner_id = ? AND t.family IS NOT NULL AND trim(t.family) != '';
                """,
                (user_id,),
            )
            families = cursor.fetchone()[0] or 0

        gamification = self.achievement_service.get_user_gamification_stats(user_id)

        return UserProfileRecord(
            user_id=u_row["id"],
            username=u_row["username"],
            role=u_row["role"],
            vivedex_id=u_row["vivedex_id"] or f"VDX-{user_id}",
            display_name=u_row["display_name"] or u_row["username"],
            bio=u_row["bio"] or "",
            external_orcid_url=u_row["external_orcid_url"] or "",
            join_date=u_row["join_date"],
            observation_count=obs_count,
            distinct_taxa_count=distinct_taxa,
            family_count=families,
            total_xp=gamification.total_xp,
            level=gamification.level,
            badge_count=gamification.badges_earned_count,
        )

    def update_user_bio(
        self,
        user_id: int,
        display_name: str,
        bio: str,
        external_orcid_url: str = "",
    ) -> None:
        """Update researcher profile fields. Note: role cannot be altered here."""
        now = utc_now_iso()
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE user_profiles
                SET display_name = ?, bio = ?, external_orcid_url = ?, updated_at = ?
                WHERE user_id = ?;
                """,
                (
                    display_name.strip(),
                    bio.strip(),
                    external_orcid_url.strip(),
                    now,
                    user_id,
                ),
            )
            cursor.execute(
                """
                INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details, timestamp)
                VALUES (?, 'PROFILE_UPDATED', 'USER', ?, 'Profile details modified', ?);
                """,
                (user_id, str(user_id), now),
            )
