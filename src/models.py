"""Domain data models and records for the Vivédex platform.

These models encapsulate database rows with explicit types.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TaxonRecord:
    """Represents a taxon entity in the database."""

    id: int
    taxon_id: int | None
    scientific_name: str
    canonical_name: str | None
    common_name: str | None
    rank: str | None
    status: str | None
    match_type: str | None
    kingdom: str | None
    phylum: str | None
    class_name: str | None
    order_name: str | None
    family: str | None
    genus: str | None
    species: str | None
    authorship: str | None
    source_id: str | None
    data_provider: str
    licence: str
    attribution: str
    retrieved_at: str
    created_at: str


@dataclass(frozen=True)
class CollectionItem:
    """Represents a saved taxon in a user's personal collection."""

    id: int
    user_id: int
    taxon_id: int
    first_encounter_at: str
    last_encounter_at: str
    encounter_count: int
    notes: str
    scientific_name: str
    common_name: str | None
    rank: str | None
    family: str | None
    kingdom: str | None
    created_at: str


@dataclass(frozen=True)
class ObservationRecord:
    """Represents a persistent organism observation."""

    id: int
    observation_id: str
    owner_id: int
    candidate_scientific_name: str
    matched_taxon_id: int | None
    observation_timestamp: str
    field_notes: str
    coarse_location: str
    model_result_json: str
    gbif_result_json: str | None
    taxonomic_resolution: str | None
    moderation_status: str
    provenance: str
    created_at: str
    site_id: int | None = None
    expedition_id: int | None = None
    project_id: int | None = None


@dataclass(frozen=True)
class BadgeRecord:
    """Represents an achievement badge definition."""

    id: int
    code: str
    name: str
    description: str
    rule_description: str
    icon: str
    xp_reward: int
    created_at: str


@dataclass(frozen=True)
class UserBadgeRecord:
    """Represents an awarded badge to a user."""

    id: int
    user_id: int
    badge_id: int
    code: str
    name: str
    description: str
    icon: str
    xp_reward: int
    awarded_at: str


@dataclass(frozen=True)
class ModerationEventRecord:
    """Represents an audit entry for observation moderation."""

    id: int
    observation_id: int
    moderator_id: int | None
    moderator_username: str | None
    previous_status: str
    new_status: str
    moderation_note: str
    created_at: str


@dataclass(frozen=True)
class AuditLogRecord:
    """Represents a system audit log record."""

    id: int
    user_id: int | None
    username: str | None
    action: str
    entity_type: str
    entity_id: str | None
    details: str | None
    timestamp: str


@dataclass(frozen=True)
class UserProfileRecord:
    """Represents user profile and statistics."""

    user_id: int
    username: str
    role: str
    vivedex_id: str
    display_name: str
    bio: str
    external_orcid_url: str
    join_date: str
    observation_count: int
    distinct_taxa_count: int
    family_count: int
    total_xp: int
    level: int
    badge_count: int

