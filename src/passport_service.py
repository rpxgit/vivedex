"""Researcher Passport service for Vivédex.

Inspired by ORCID, provides persistent contributor identity, verified affiliations,
research interests, and scientific outputs with clear provenance states.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from src.achievements import AchievementService
from src.database import Database, utc_now_iso


@dataclass(frozen=True)
class ResearchOutput:
    """Scholarly or field research output."""

    id: int
    user_id: int
    title: str
    output_type: str  # DATASET, FIELD_REPORT, SPECIES_CHECKLIST, PUBLICATION, OBSERVATION_CATALOG
    doi_or_url: str
    citation: str
    provenance_state: str  # SELF_REPORTED, SOURCE_LINKED, PLATFORM_REVIEWED, EXTERNALLY_VERIFIED
    created_at: str


@dataclass(frozen=True)
class ResearcherPassport:
    """Complete contributor identity profile."""

    user_id: int
    username: str
    vivedex_id: str
    display_name: str
    bio: str
    external_orcid_url: str
    affiliations: list[str]
    research_interests: list[str]
    is_public: bool
    created_at: str
    updated_at: str
    # Aggregated metrics
    total_observations: int
    accepted_observations: int
    species_collected: int
    families_documented: int
    total_xp: int
    badges_count: int
    outputs: list[ResearchOutput]


class PassportService:
    """Manages researcher passports and research outputs."""

    def __init__(self, db: Database) -> None:
        self.db = db
        self.achievement_service = AchievementService(db)

    def get_passport(self, user_id: int) -> ResearcherPassport | None:
        """Fetch complete researcher passport for a user."""
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    u.id as user_id, u.username,
                    p.vivedex_id, p.display_name, p.bio, p.external_orcid_url,
                    p.affiliations, p.research_interests, p.is_public,
                    p.created_at, p.updated_at
                FROM users u
                JOIN user_profiles p ON p.user_id = u.id
                WHERE u.id = ?;
                """,
                (user_id,),
            )
            profile_row = cursor.fetchone()
            if not profile_row:
                return None

            # Parse JSON lists safely
            try:
                affils = json.loads(profile_row["affiliations"] or "[]")
                if not isinstance(affils, list):
                    affils = []
            except Exception:
                affils = [a.strip() for a in (profile_row["affiliations"] or "").split(",") if a.strip()]

            try:
                interests = json.loads(profile_row["research_interests"] or "[]")
                if not isinstance(interests, list):
                    interests = []
            except Exception:
                interests = [i.strip() for i in (profile_row["research_interests"] or "").split(",") if i.strip()]

            # Observation metrics
            cursor.execute("SELECT COUNT(*) FROM observations WHERE owner_id = ?;", (user_id,))
            total_obs = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM observations WHERE owner_id = ? AND moderation_status = 'ACCEPTED_FOR_CATALOG';",
                (user_id,),
            )
            accepted_obs = cursor.fetchone()[0]

            # Collection metrics
            cursor.execute("SELECT COUNT(*) FROM collections WHERE user_id = ?;", (user_id,))
            species_collected = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT COUNT(DISTINCT t.family)
                FROM observations o
                JOIN taxa t ON t.taxon_id = o.matched_taxon_id
                WHERE o.owner_id = ? AND t.family IS NOT NULL AND TRIM(t.family) != '';
                """,
                (user_id,),
            )
            families_count = cursor.fetchone()[0]

            # Badge & XP metrics
            cursor.execute(
                """
                SELECT COUNT(b.id)
                FROM user_badges ub
                JOIN badges b ON b.id = ub.badge_id
                WHERE ub.user_id = ?;
                """,
                (user_id,),
            )
            badges_count = cursor.fetchone()[0] or 0

            # Unified authoritative XP calculation
            total_xp = self.achievement_service.calculate_user_xp(user_id)

            # Research outputs
            cursor.execute(
                """
                SELECT id, user_id, title, output_type, doi_or_url, citation, provenance_state, created_at
                FROM research_outputs
                WHERE user_id = ?
                ORDER BY created_at DESC;
                """,
                (user_id,),
            )
            outputs = [ResearchOutput(**dict(r)) for r in cursor.fetchall()]

            return ResearcherPassport(
                user_id=profile_row["user_id"],
                username=profile_row["username"],
                vivedex_id=profile_row["vivedex_id"],
                display_name=profile_row["display_name"],
                bio=profile_row["bio"] or "",
                external_orcid_url=profile_row["external_orcid_url"] or "",
                affiliations=affils,
                research_interests=interests,
                is_public=bool(profile_row["is_public"]),
                created_at=profile_row["created_at"],
                updated_at=profile_row["updated_at"],
                total_observations=total_obs,
                accepted_observations=accepted_obs,
                species_collected=species_collected,
                families_documented=families_count,
                total_xp=total_xp,
                badges_count=badges_count,
                outputs=outputs,
            )

    def update_passport_profile(
        self,
        user_id: int,
        display_name: str,
        bio: str,
        external_orcid_url: str,
        affiliations: list[str],
        research_interests: list[str],
        is_public: bool,
    ) -> bool:
        """Update user profile passport details."""
        now = utc_now_iso()
        affils_json = json.dumps([a.strip() for a in affiliations if a.strip()])
        interests_json = json.dumps([i.strip() for i in research_interests if i.strip()])

        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE user_profiles
                SET display_name = ?,
                    bio = ?,
                    external_orcid_url = ?,
                    affiliations = ?,
                    research_interests = ?,
                    is_public = ?,
                    updated_at = ?
                WHERE user_id = ?;
                """,
                (
                    display_name,
                    bio,
                    external_orcid_url,
                    affils_json,
                    interests_json,
                    1 if is_public else 0,
                    now,
                    user_id,
                ),
            )
            return cursor.rowcount > 0

    def add_research_output(
        self,
        user_id: int,
        title: str,
        output_type: str,
        doi_or_url: str = "",
        citation: str = "",
        provenance_state: str = "SELF_REPORTED",
    ) -> ResearchOutput:
        """Add a research output record to the researcher passport."""
        # Auto-promote to SOURCE_LINKED if valid URL/DOI provided
        final_provenance = provenance_state
        if doi_or_url.strip() and final_provenance == "SELF_REPORTED":
            if doi_or_url.startswith("http") or doi_or_url.startswith("10."):
                final_provenance = "SOURCE_LINKED"

        now = utc_now_iso()
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO research_outputs (user_id, title, output_type, doi_or_url, citation, provenance_state, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (user_id, title.strip(), output_type, doi_or_url.strip(), citation.strip(), final_provenance, now),
            )
            out_id = cursor.lastrowid
            return ResearchOutput(
                id=out_id,
                user_id=user_id,
                title=title.strip(),
                output_type=output_type,
                doi_or_url=doi_or_url.strip(),
                citation=citation.strip(),
                provenance_state=final_provenance,
                created_at=now,
            )

    def delete_research_output(self, user_id: int, output_id: int) -> bool:
        """Remove a research output owned by the user."""
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM research_outputs WHERE id = ? AND user_id = ?;",
                (output_id, user_id),
            )
            return cursor.rowcount > 0

    def update_output_provenance(self, output_id: int, provenance_state: str) -> bool:
        """Moderator / reviewer action to update provenance status."""
        valid_states = {"SELF_REPORTED", "SOURCE_LINKED", "PLATFORM_REVIEWED", "EXTERNALLY_VERIFIED"}
        if provenance_state not in valid_states:
            raise ValueError(f"Invalid provenance state: {provenance_state}")

        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE research_outputs SET provenance_state = ? WHERE id = ?;",
                (provenance_state, output_id),
            )
            return cursor.rowcount > 0

