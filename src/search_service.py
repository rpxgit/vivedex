"""Global search and taxonomic discovery service for Vivédex.

Provides unified, fast querying across taxa, field sites, expeditions,
conservation projects, observations, and public researcher profiles.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.database import Database


@dataclass(frozen=True)
class SearchResultGroup:
    """Grouped search results categorized by entity type."""

    taxa: list[dict[str, Any]]
    field_sites: list[dict[str, Any]]
    projects: list[dict[str, Any]]
    expeditions: list[dict[str, Any]]
    observations: list[dict[str, Any]]
    researchers: list[dict[str, Any]]
    total_matches: int


class SearchService:
    """Unified search engine for Vivédex."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def search(self, query: str, limit_per_category: int = 10) -> SearchResultGroup:
        """Perform cross-entity search for the provided query string."""
        clean_q = query.strip()
        if not clean_q:
            return SearchResultGroup([], [], [], [], [], [], 0)

        pattern = f"%{clean_q}%"
        taxa: list[dict[str, Any]] = []
        sites: list[dict[str, Any]] = []
        projects: list[dict[str, Any]] = []
        expeditions: list[dict[str, Any]] = []
        observations: list[dict[str, Any]] = []
        researchers: list[dict[str, Any]] = []

        with self.db.connect() as conn:
            cursor = conn.cursor()

            # 1. Taxa search
            cursor.execute(
                """
                SELECT taxon_id, scientific_name, canonical_name, common_name, rank, family, kingdom
                FROM taxa
                WHERE scientific_name LIKE ? OR canonical_name LIKE ? OR common_name LIKE ? OR family LIKE ?
                LIMIT ?;
                """,
                (pattern, pattern, pattern, pattern, limit_per_category),
            )
            taxa = [dict(r) for r in cursor.fetchall()]

            # 2. Field sites search
            cursor.execute(
                """
                SELECT id, slug, name, description, biome, country, elevation_m
                FROM field_sites
                WHERE name LIKE ? OR biome LIKE ? OR country LIKE ? OR description LIKE ?
                LIMIT ?;
                """,
                (pattern, pattern, pattern, pattern, limit_per_category),
            )
            sites = [dict(r) for r in cursor.fetchall()]

            # 3. Projects search
            cursor.execute(
                """
                SELECT id, slug, title, summary, target_habitat, status
                FROM projects
                WHERE title LIKE ? OR summary LIKE ? OR target_habitat LIKE ?
                LIMIT ?;
                """,
                (pattern, pattern, pattern, limit_per_category),
            )
            projects = [dict(r) for r in cursor.fetchall()]

            # 4. Expeditions search
            cursor.execute(
                """
                SELECT id, slug, title, description, start_date, status
                FROM expeditions
                WHERE title LIKE ? OR description LIKE ?
                LIMIT ?;
                """,
                (pattern, pattern, limit_per_category),
            )
            expeditions = [dict(r) for r in cursor.fetchall()]

            # 5. Observations search
            cursor.execute(
                """
                SELECT o.observation_id, o.candidate_scientific_name, o.coarse_location,
                       o.taxonomic_resolution, o.moderation_status, o.observation_timestamp,
                       t.common_name
                FROM observations o
                LEFT JOIN taxa t ON t.taxon_id = o.matched_taxon_id
                WHERE o.candidate_scientific_name LIKE ? OR o.field_notes LIKE ? OR o.coarse_location LIKE ?
                LIMIT ?;
                """,
                (pattern, pattern, pattern, limit_per_category),
            )
            observations = [dict(r) for r in cursor.fetchall()]

            # 6. Public Researchers search
            cursor.execute(
                """
                SELECT u.id, u.username, p.vivedex_id, p.display_name, p.bio, p.external_orcid_url
                FROM users u
                JOIN user_profiles p ON p.user_id = u.id
                WHERE p.is_public = 1 AND (u.username LIKE ? OR p.display_name LIKE ? OR p.bio LIKE ?)
                LIMIT ?;
                """,
                (pattern, pattern, pattern, limit_per_category),
            )
            researchers = [dict(r) for r in cursor.fetchall()]

        total = len(taxa) + len(sites) + len(projects) + len(expeditions) + len(observations) + len(researchers)
        return SearchResultGroup(
            taxa=taxa,
            field_sites=sites,
            projects=projects,
            expeditions=expeditions,
            observations=observations,
            researchers=researchers,
            total_matches=total,
        )
