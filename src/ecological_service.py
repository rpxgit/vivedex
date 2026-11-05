"""Ecological hierarchy service for Vivédex.

Manages organisations, conservation projects, field sites, and scientific expeditions.
Calculates species richness and connects field observations to ecological locations.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from src.auth import AuthorizationError
from src.database import Database, utc_now_iso


def slugify(text: str) -> str:
    """Generate a clean, safe URL slug from human-readable text."""
    clean = re.sub(r"[^\w\s-]", "", text.strip().lower())
    return re.sub(r"[-\s]+", "-", clean)


@dataclass(frozen=True)
class Organisation:
    """Partner organisation or scientific institution."""

    id: int
    slug: str
    name: str
    description: str
    website_url: str
    logo_url: str
    country: str
    created_at: str


@dataclass(frozen=True)
class FieldSite:
    """Physical ecosystem site or field station."""

    id: int
    slug: str
    name: str
    description: str
    biome: str
    latitude: float | None
    longitude: float | None
    elevation_m: float | None
    country: str
    created_at: str
    observation_count: int = 0
    species_richness: int = 0


@dataclass(frozen=True)
class Project:
    """Biodiversity census or ecological research project."""

    id: int
    slug: str
    title: str
    summary: str
    organisation_id: int | None
    organisation_name: str | None
    lead_user_id: int | None
    target_habitat: str
    target_species_count: int
    status: str
    created_at: str
    observation_count: int = 0


@dataclass(frozen=True)
class Expedition:
    """Time-bounded scientific field expedition."""

    id: int
    slug: str
    title: str
    description: str
    site_id: int | None
    site_name: str | None
    project_id: int | None
    project_title: str | None
    lead_user_id: int | None
    start_date: str
    end_date: str | None
    status: str
    created_at: str
    observation_count: int = 0


class EcologicalService:
    """Service providing ecological hierarchy queries and management."""

    def __init__(self, db: Database) -> None:
        self.db = db

    # -------------------------------------------------------------------------
    # Organisations
    # -------------------------------------------------------------------------

    def list_organisations(self) -> list[Organisation]:
        """Return all registered partner organisations."""
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, slug, name, description, website_url, logo_url, country, created_at
                FROM organisations
                ORDER BY name ASC;
                """
            )
            rows = cursor.fetchall()
            return [Organisation(**dict(row)) for row in rows]

    def get_organisation(self, org_id_or_slug: int | str) -> Organisation | None:
        """Fetch single organisation by ID or slug."""
        with self.db.connect() as conn:
            cursor = conn.cursor()
            if isinstance(org_id_or_slug, int) or (isinstance(org_id_or_slug, str) and org_id_or_slug.isdigit()):
                cursor.execute(
                    """
                    SELECT id, slug, name, description, website_url, logo_url, country, created_at
                    FROM organisations WHERE id = ?;
                    """,
                    (int(org_id_or_slug),),
                )
            else:
                cursor.execute(
                    """
                    SELECT id, slug, name, description, website_url, logo_url, country, created_at
                    FROM organisations WHERE slug = ?;
                    """,
                    (str(org_id_or_slug),),
                )
            row = cursor.fetchone()
            return Organisation(**dict(row)) if row else None

    def create_organisation(
        self,
        name: str,
        slug: str | None = None,
        description: str = "",
        website_url: str = "",
        logo_url: str = "",
        country: str = "",
        admin_user: Any = None,
    ) -> Organisation:
        """Register a new partner organisation. Guarded by server-side administrator check."""
        if admin_user is not None and not getattr(admin_user, "is_admin", False):
            raise AuthorizationError("Only platform administrators can register partner organisations.")
        final_slug = slug or slugify(name)
        now = utc_now_iso()
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO organisations (slug, name, description, website_url, logo_url, country, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (final_slug, name, description, website_url, logo_url, country, now),
            )
            org_id = cursor.lastrowid
            return Organisation(
                id=org_id,
                slug=final_slug,
                name=name,
                description=description,
                website_url=website_url,
                logo_url=logo_url,
                country=country,
                created_at=now,
            )

    # -------------------------------------------------------------------------
    # Field Sites
    # -------------------------------------------------------------------------

    def list_field_sites(self) -> list[FieldSite]:
        """Return all field sites with observation counts and species richness."""
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    s.id, s.slug, s.name, s.description, s.biome,
                    s.latitude, s.longitude, s.elevation_m, s.country, s.created_at,
                    COUNT(DISTINCT o.id) as observation_count,
                    COUNT(DISTINCT o.matched_taxon_id) as species_richness
                FROM field_sites s
                LEFT JOIN observations o ON o.site_id = s.id
                GROUP BY s.id
                ORDER BY s.name ASC;
                """
            )
            rows = cursor.fetchall()
            return [FieldSite(**dict(row)) for row in rows]

    def get_field_site(self, site_id_or_slug: int | str) -> FieldSite | None:
        """Fetch single field site with calculated metrics."""
        with self.db.connect() as conn:
            cursor = conn.cursor()
            condition = "s.id = ?" if (isinstance(site_id_or_slug, int) or str(site_id_or_slug).isdigit()) else "s.slug = ?"
            param = int(site_id_or_slug) if (isinstance(site_id_or_slug, int) or str(site_id_or_slug).isdigit()) else str(site_id_or_slug)

            cursor.execute(
                f"""
                SELECT 
                    s.id, s.slug, s.name, s.description, s.biome,
                    s.latitude, s.longitude, s.elevation_m, s.country, s.created_at,
                    COUNT(DISTINCT o.id) as observation_count,
                    COUNT(DISTINCT o.matched_taxon_id) as species_richness
                FROM field_sites s
                LEFT JOIN observations o ON o.site_id = s.id
                WHERE {condition}
                GROUP BY s.id;
                """,
                (param,),
            )
            row = cursor.fetchone()
            return FieldSite(**dict(row)) if row else None

    def create_field_site(
        self,
        name: str,
        slug: str | None = None,
        description: str = "",
        biome: str = "",
        latitude: float | None = None,
        longitude: float | None = None,
        elevation_m: float | None = None,
        country: str = "",
    ) -> FieldSite:
        """Create a new field site."""
        final_slug = slug or slugify(name)
        now = utc_now_iso()
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO field_sites (slug, name, description, biome, latitude, longitude, elevation_m, country, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (final_slug, name, description, biome, latitude, longitude, elevation_m, country, now),
            )
            site_id = cursor.lastrowid
            return FieldSite(
                id=site_id,
                slug=final_slug,
                name=name,
                description=description,
                biome=biome,
                latitude=latitude,
                longitude=longitude,
                elevation_m=elevation_m,
                country=country,
                created_at=now,
                observation_count=0,
                species_richness=0,
            )

    # -------------------------------------------------------------------------
    # Projects
    # -------------------------------------------------------------------------

    def list_projects(self, org_id: int | None = None, status: str | None = None) -> list[Project]:
        """Return projects with optional filtering."""
        with self.db.connect() as conn:
            cursor = conn.cursor()
            query = """
                SELECT 
                    p.id, p.slug, p.title, p.summary, p.organisation_id,
                    org.name as organisation_name,
                    p.lead_user_id, p.target_habitat, p.target_species_count, p.status, p.created_at,
                    COUNT(DISTINCT o.id) as observation_count
                FROM projects p
                LEFT JOIN organisations org ON org.id = p.organisation_id
                LEFT JOIN observations o ON o.project_id = p.id
            """
            conditions = []
            params: list[Any] = []
            if org_id is not None:
                conditions.append("p.organisation_id = ?")
                params.append(org_id)
            if status is not None:
                conditions.append("p.status = ?")
                params.append(status)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " GROUP BY p.id ORDER BY p.created_at DESC;"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [Project(**dict(row)) for row in rows]

    def get_project(self, project_id_or_slug: int | str) -> Project | None:
        """Fetch project details."""
        with self.db.connect() as conn:
            cursor = conn.cursor()
            condition = "p.id = ?" if (isinstance(project_id_or_slug, int) or str(project_id_or_slug).isdigit()) else "p.slug = ?"
            param = int(project_id_or_slug) if (isinstance(project_id_or_slug, int) or str(project_id_or_slug).isdigit()) else str(project_id_or_slug)

            cursor.execute(
                f"""
                SELECT 
                    p.id, p.slug, p.title, p.summary, p.organisation_id,
                    org.name as organisation_name,
                    p.lead_user_id, p.target_habitat, p.target_species_count, p.status, p.created_at,
                    COUNT(DISTINCT o.id) as observation_count
                FROM projects p
                LEFT JOIN organisations org ON org.id = p.organisation_id
                LEFT JOIN observations o ON o.project_id = p.id
                WHERE {condition}
                GROUP BY p.id;
                """,
                (param,),
            )
            row = cursor.fetchone()
            return Project(**dict(row)) if row else None

    def create_project(
        self,
        title: str,
        slug: str | None = None,
        summary: str = "",
        organisation_id: int | None = None,
        lead_user_id: int | None = None,
        target_habitat: str = "",
        target_species_count: int = 0,
        status: str = "ACTIVE",
        user: Any = None,
    ) -> Project:
        """Create a new project. Validates institutional affiliation if linked to an organisation."""
        if organisation_id is not None and user is not None:
            is_admin = getattr(user, "is_admin", False)
            if not is_admin:
                # Check user profile affiliations
                with self.db.connect() as conn:
                    c = conn.cursor()
                    c.execute("SELECT affiliations FROM user_profiles WHERE user_id = ?;", (user.id,))
                    row = c.fetchone()
                    affils: list[str] = []
                    if row and row[0]:
                        try:
                            parsed_affils = json.loads(row[0])
                            if isinstance(parsed_affils, list):
                                affils = parsed_affils
                        except Exception:
                            affils = [a.strip() for a in str(row[0]).split(",") if a.strip()]
                    c.execute("SELECT name FROM organisations WHERE id = ?;", (organisation_id,))
                    org_row = c.fetchone()
                    org_name = org_row[0] if org_row else ""
                    if org_name and not any(a.lower() == org_name.lower() for a in affils):
                        raise AuthorizationError(
                            f"Project attribution to '{org_name}' requires verified institutional affiliation or platform administrator privileges."
                        )

        final_slug = slug or slugify(title)
        now = utc_now_iso()
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO projects (slug, title, summary, organisation_id, lead_user_id, target_habitat, target_species_count, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (final_slug, title, summary, organisation_id, lead_user_id, target_habitat, target_species_count, status, now),
            )
            proj_id = cursor.lastrowid
            org_name = None
            if organisation_id:
                cursor.execute("SELECT name FROM organisations WHERE id = ?;", (organisation_id,))
                org_row = cursor.fetchone()
                if org_row:
                    org_name = org_row[0]

            return Project(
                id=proj_id,
                slug=final_slug,
                title=title,
                summary=summary,
                organisation_id=organisation_id,
                organisation_name=org_name,
                lead_user_id=lead_user_id,
                target_habitat=target_habitat,
                target_species_count=target_species_count,
                status=status,
                created_at=now,
                observation_count=0,
            )

    # -------------------------------------------------------------------------
    # Expeditions
    # -------------------------------------------------------------------------

    def list_expeditions(
        self,
        site_id: int | None = None,
        project_id: int | None = None,
        status: str | None = None,
    ) -> list[Expedition]:
        """Return expeditions with metadata and observation count."""
        with self.db.connect() as conn:
            cursor = conn.cursor()
            query = """
                SELECT 
                    e.id, e.slug, e.title, e.description, e.site_id,
                    s.name as site_name,
                    e.project_id,
                    p.title as project_title,
                    e.lead_user_id, e.start_date, e.end_date, e.status, e.created_at,
                    COUNT(DISTINCT o.id) as observation_count
                FROM expeditions e
                LEFT JOIN field_sites s ON s.id = e.site_id
                LEFT JOIN projects p ON p.id = e.project_id
                LEFT JOIN observations o ON o.expedition_id = e.id
            """
            conditions = []
            params: list[Any] = []
            if site_id is not None:
                conditions.append("e.site_id = ?")
                params.append(site_id)
            if project_id is not None:
                conditions.append("e.project_id = ?")
                params.append(project_id)
            if status is not None:
                conditions.append("e.status = ?")
                params.append(status)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " GROUP BY e.id ORDER BY e.start_date DESC;"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [Expedition(**dict(row)) for row in rows]

    def get_expedition(self, expedition_id_or_slug: int | str) -> Expedition | None:
        """Fetch expedition details."""
        with self.db.connect() as conn:
            cursor = conn.cursor()
            condition = "e.id = ?" if (isinstance(expedition_id_or_slug, int) or str(expedition_id_or_slug).isdigit()) else "e.slug = ?"
            param = int(expedition_id_or_slug) if (isinstance(expedition_id_or_slug, int) or str(expedition_id_or_slug).isdigit()) else str(expedition_id_or_slug)

            cursor.execute(
                f"""
                SELECT 
                    e.id, e.slug, e.title, e.description, e.site_id,
                    s.name as site_name,
                    e.project_id,
                    p.title as project_title,
                    e.lead_user_id, e.start_date, e.end_date, e.status, e.created_at,
                    COUNT(DISTINCT o.id) as observation_count
                FROM expeditions e
                LEFT JOIN field_sites s ON s.id = e.site_id
                LEFT JOIN projects p ON p.id = e.project_id
                LEFT JOIN observations o ON o.expedition_id = e.id
                WHERE {condition}
                GROUP BY e.id;
                """,
                (param,),
            )
            row = cursor.fetchone()
            return Expedition(**dict(row)) if row else None

    def create_expedition(
        self,
        title: str,
        slug: str | None = None,
        description: str = "",
        site_id: int | None = None,
        project_id: int | None = None,
        lead_user_id: int | None = None,
        start_date: str = "",
        end_date: str | None = None,
        status: str = "PLANNED",
    ) -> Expedition:
        """Create a new field expedition."""
        final_slug = slug or slugify(title)
        now = utc_now_iso()
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO expeditions (slug, title, description, site_id, project_id, lead_user_id, start_date, end_date, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (final_slug, title, description, site_id, project_id, lead_user_id, start_date or now, end_date, status, now),
            )
            exp_id = cursor.lastrowid
            site_name = None
            if site_id:
                cursor.execute("SELECT name FROM field_sites WHERE id = ?;", (site_id,))
                s_row = cursor.fetchone()
                if s_row:
                    site_name = s_row[0]

            proj_title = None
            if project_id:
                cursor.execute("SELECT title FROM projects WHERE id = ?;", (project_id,))
                p_row = cursor.fetchone()
                if p_row:
                    proj_title = p_row[0]

            return Expedition(
                id=exp_id,
                slug=final_slug,
                title=title,
                description=description,
                site_id=site_id,
                site_name=site_name,
                project_id=project_id,
                project_title=proj_title,
                lead_user_id=lead_user_id,
                start_date=start_date or now,
                end_date=end_date,
                status=status,
                created_at=now,
                observation_count=0,
            )

    # -------------------------------------------------------------------------
    # Observation Linking
    # -------------------------------------------------------------------------

    def link_observation_ecological(
        self,
        observation_id: str,
        site_id: int | None = None,
        expedition_id: int | None = None,
        project_id: int | None = None,
        user_id: int | None = None,
        is_admin: bool = False,
    ) -> bool:
        """Link an observation to ecological entities. Requires ownership or admin."""
        with self.db.connect() as conn:
            cursor = conn.cursor()
            if not is_admin and user_id is not None:
                cursor.execute(
                    "SELECT owner_id FROM observations WHERE observation_id = ?;",
                    (observation_id,),
                )
                row = cursor.fetchone()
                if not row:
                    raise ValueError(f"Observation '{observation_id}' not found.")
                if row[0] != user_id:
                    raise PermissionError(
                        "You can only link your own observations to ecological sites and expeditions."
                    )

            cursor.execute(
                """
                UPDATE observations
                SET site_id = COALESCE(?, site_id),
                    expedition_id = COALESCE(?, expedition_id),
                    project_id = COALESCE(?, project_id)
                WHERE observation_id = ?;
                """,
                (site_id, expedition_id, project_id, observation_id),
            )
            return cursor.rowcount > 0

    def get_site_observations(self, site_id: int) -> list[dict[str, Any]]:
        """Return observations recorded at a specific site."""
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT o.observation_id, o.candidate_scientific_name, o.observation_timestamp,
                       o.taxonomic_resolution, o.moderation_status, o.coarse_location,
                       t.common_name, t.family
                FROM observations o
                LEFT JOIN taxa t ON t.taxon_id = o.matched_taxon_id
                WHERE o.site_id = ?
                ORDER BY o.observation_timestamp DESC;
                """,
                (site_id,),
            )
            return [dict(r) for r in cursor.fetchall()]

