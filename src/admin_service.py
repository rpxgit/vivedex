"""Administrator service for Vivédex.

Provides platform metrics, moderation workflows, user management, and audit inspection.
Strictly enforces server-side role checks on all operations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.achievements import AchievementService
from src.auth import AuthenticatedUser, AuthService, AuthorizationError
from src.database import Database, utc_now_iso
from src.models import AuditLogRecord, ObservationRecord

VALID_MODERATION_STATUSES = (
    "PENDING",
    "ACCEPTED_FOR_CATALOG",
    "NEEDS_MORE_EVIDENCE",
    "REJECTED",
)


@dataclass(frozen=True)
class AdminDashboardMetrics:
    """Aggregated platform statistics for administrator review."""

    total_users: int
    total_observations: int
    distinct_taxa_count: int
    pending_submissions: int
    accepted_submissions: int
    badge_distribution: dict[str, int]
    recent_activity_count: int


@dataclass(frozen=True)
class AdminUserSummary:
    """Summary record of a registered user for administration."""

    user_id: int
    username: str
    role: str
    display_name: str
    vivedex_id: str
    is_active: bool
    observation_count: int
    created_at: str


class AdminService:
    """Handles moderation, administrative queries, and platform audit trail."""

    def __init__(self, db: Database) -> None:
        self.db = db
        self.achievement_service = AchievementService(db)

    def _require_admin(self, user: AuthenticatedUser | None) -> None:
        """Enforce administrator role. Server-side guard."""
        AuthService.require_admin(user)

    def get_dashboard_metrics(self, admin_user: AuthenticatedUser) -> AdminDashboardMetrics:
        """Fetch high-level platform metrics for the administrator dashboard."""
        self._require_admin(admin_user)

        with self.db.connect() as conn:
            cursor = conn.cursor()

            # 1. Total users
            cursor.execute("SELECT COUNT(*) FROM users;")
            total_users = cursor.fetchone()[0] or 0

            # 2. Total observations
            cursor.execute("SELECT COUNT(*) FROM observations;")
            total_obs = cursor.fetchone()[0] or 0

            # 3. Distinct taxa
            cursor.execute("SELECT COUNT(DISTINCT taxon_id) FROM taxa WHERE taxon_id IS NOT NULL;")
            distinct_taxa = cursor.fetchone()[0] or 0

            # 4. Pending submissions
            cursor.execute("SELECT COUNT(*) FROM observations WHERE moderation_status = 'PENDING';")
            pending = cursor.fetchone()[0] or 0

            # 5. Accepted submissions
            cursor.execute("SELECT COUNT(*) FROM observations WHERE moderation_status = 'ACCEPTED_FOR_CATALOG';")
            accepted = cursor.fetchone()[0] or 0

            # 6. Badge distribution
            cursor.execute(
                """
                SELECT b.name, COUNT(ub.id) as count
                FROM badges b
                LEFT JOIN user_badges ub ON b.id = ub.badge_id
                GROUP BY b.id, b.name;
                """
            )
            badge_dist = {row["name"]: row["count"] for row in cursor.fetchall()}

            # 7. Recent activity count (audit logs)
            cursor.execute("SELECT COUNT(*) FROM audit_logs;")
            recent_activity = cursor.fetchone()[0] or 0

            return AdminDashboardMetrics(
                total_users=total_users,
                total_observations=total_obs,
                distinct_taxa_count=distinct_taxa,
                pending_submissions=pending,
                accepted_submissions=accepted,
                badge_distribution=badge_dist,
                recent_activity_count=recent_activity,
            )

    def list_users(self, admin_user: AuthenticatedUser) -> list[AdminUserSummary]:
        """List all registered users with summary metrics."""
        self._require_admin(admin_user)

        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT u.id, u.username, u.role, u.is_active, u.created_at,
                       p.display_name, p.vivedex_id,
                       (SELECT COUNT(*) FROM observations WHERE owner_id = u.id) as obs_count
                FROM users u
                LEFT JOIN user_profiles p ON u.id = p.user_id
                ORDER BY u.created_at ASC;
                """
            )
            return [
                AdminUserSummary(
                    user_id=row["id"],
                    username=row["username"],
                    role=row["role"],
                    display_name=row["display_name"] or row["username"],
                    vivedex_id=row["vivedex_id"] or f"VDX-{row['id']}",
                    is_active=bool(row["is_active"]),
                    observation_count=row["obs_count"],
                    created_at=row["created_at"],
                )
                for row in cursor.fetchall()
            ]

    def get_moderation_queue(
        self,
        admin_user: AuthenticatedUser,
        status_filter: str = "PENDING",
    ) -> list[ObservationRecord]:
        """Fetch observations awaiting or undergoing moderation."""
        self._require_admin(admin_user)

        with self.db.connect() as conn:
            cursor = conn.cursor()
            sql = """
                SELECT id, observation_id, owner_id, candidate_scientific_name,
                       matched_taxon_id, observation_timestamp, field_notes,
                       coarse_location, model_result_json, gbif_result_json,
                       taxonomic_resolution, moderation_status, provenance, created_at
                FROM observations
            """
            params: list[Any] = []
            if status_filter != "ALL":
                sql += " WHERE moderation_status = ?"
                params.append(status_filter)

            sql += " ORDER BY observation_timestamp ASC;"

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

    def moderate_observation(
        self,
        admin_user: AuthenticatedUser,
        observation_id: str,
        new_status: str,
        moderation_note: str = "",
    ) -> None:
        """Apply a moderation decision to an observation.

        Records an event in moderation_events and logs the action in audit_logs.
        Evaluates achievements for the observation owner if accepted.
        """
        self._require_admin(admin_user)

        if new_status not in VALID_MODERATION_STATUSES:
            raise ValueError(
                f"Invalid status '{new_status}'. Allowed: {VALID_MODERATION_STATUSES}"
            )

        now = utc_now_iso()
        owner_id: int | None = None

        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, owner_id, moderation_status FROM observations WHERE observation_id = ?;",
                (observation_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Observation {observation_id} not found.")

            obs_id, owner_id, previous_status = row

            # Update observation status
            cursor.execute(
                "UPDATE observations SET moderation_status = ? WHERE id = ?;",
                (new_status, obs_id),
            )

            # Insert moderation event
            cursor.execute(
                """
                INSERT INTO moderation_events (
                    observation_id, moderator_id, previous_status, new_status,
                    moderation_note, created_at
                ) VALUES (?, ?, ?, ?, ?, ?);
                """,
                (
                    obs_id,
                    admin_user.id,
                    previous_status,
                    new_status,
                    moderation_note.strip(),
                    now,
                ),
            )

            # Insert audit log
            cursor.execute(
                """
                INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details, timestamp)
                VALUES (?, 'MODERATION_DECISION', 'OBSERVATION', ?, ?, ?);
                """,
                (
                    admin_user.id,
                    observation_id,
                    f"Status changed from {previous_status} to {new_status}. Note: {moderation_note.strip()}",
                    now,
                ),
            )

        # Trigger badge evaluation if accepted
        if owner_id is not None and new_status == "ACCEPTED_FOR_CATALOG":
            self.achievement_service.evaluate_user_achievements(owner_id)

    def get_audit_logs(
        self,
        admin_user: AuthenticatedUser,
        limit: int = 100,
    ) -> list[AuditLogRecord]:
        """Fetch recent system audit logs."""
        self._require_admin(admin_user)

        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT a.id, a.user_id, u.username, a.action, a.entity_type, a.entity_id,
                       a.details, a.timestamp
                FROM audit_logs a
                LEFT JOIN users u ON a.user_id = u.id
                ORDER BY a.id DESC
                LIMIT ?;
                """,
                (limit,),
            )
            return [
                AuditLogRecord(
                    id=row["id"],
                    user_id=row["user_id"],
                    username=row["username"],
                    action=row["action"],
                    entity_type=row["entity_type"],
                    entity_id=row["entity_id"],
                    details=row["details"],
                    timestamp=row["timestamp"],
                )
                for row in cursor.fetchall()
            ]

