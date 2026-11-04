"""Rule-based achievement and experience points (XP) engine for Vivédex.

Evaluates user activity against defined criteria and awards persistent badges.
Ensures idempotency and calculates progressive player levels.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from src.database import Database, utc_now_iso
from src.models import BadgeRecord, UserBadgeRecord

XP_PER_FIRST_ENCOUNTER = 50
XP_PER_FIELD_NOTE = 20
XP_PER_ACCEPTED_OBSERVATION = 100
XP_PER_LEVEL = 100


@dataclass(frozen=True)
class AchievementProgress:
    """Represents user progress toward a specific badge."""

    code: str
    name: str
    description: str
    icon: str
    current_value: int
    target_value: int
    is_earned: bool
    xp_reward: int


@dataclass(frozen=True)
class UserGamificationStats:
    """Aggregated XP and level statistics for a user."""

    total_xp: int
    level: int
    xp_in_level: int
    xp_for_next_level: int
    level_progress_percentage: float
    badges_earned_count: int
    total_badges_count: int


class AchievementService:
    """Manages badge evaluation, XP computation, and player progression."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def calculate_user_xp(self, user_id: int) -> int:
        """Calculate total earned XP for a user from actions and earned badges."""
        with self.db.connect() as conn:
            cursor = conn.cursor()

            # 1. Distinct taxa collected (first encounter reward)
            cursor.execute(
                "SELECT COUNT(DISTINCT taxon_id) FROM collections WHERE user_id = ?;",
                (user_id,),
            )
            distinct_taxa = cursor.fetchone()[0] or 0
            encounter_xp = distinct_taxa * XP_PER_FIRST_ENCOUNTER

            # 2. Observations with meaningful field notes (>= 5 chars)
            cursor.execute(
                """
                SELECT COUNT(*) FROM observations
                WHERE owner_id = ? AND length(trim(field_notes)) >= 5;
                """,
                (user_id,),
            )
            notes_count = cursor.fetchone()[0] or 0
            notes_xp = notes_count * XP_PER_FIELD_NOTE

            # 3. Observations accepted by moderation for catalog
            cursor.execute(
                """
                SELECT COUNT(*) FROM observations
                WHERE owner_id = ? AND moderation_status = 'ACCEPTED_FOR_CATALOG';
                """,
                (user_id,),
            )
            accepted_count = cursor.fetchone()[0] or 0
            accepted_xp = accepted_count * XP_PER_ACCEPTED_OBSERVATION

            # 4. Bonus XP from awarded badges
            cursor.execute(
                """
                SELECT COALESCE(SUM(b.xp_reward), 0)
                FROM user_badges ub
                JOIN badges b ON ub.badge_id = b.id
                WHERE ub.user_id = ?;
                """,
                (user_id,),
            )
            badge_xp = cursor.fetchone()[0] or 0

            return encounter_xp + notes_xp + accepted_xp + badge_xp

    def get_user_gamification_stats(self, user_id: int) -> UserGamificationStats:
        """Calculate complete XP, level, progress, and badge counts for a user."""
        total_xp = self.calculate_user_xp(user_id)
        level = max(1, 1 + (total_xp // XP_PER_LEVEL))
        xp_in_level = total_xp % XP_PER_LEVEL
        progress_pct = (xp_in_level / XP_PER_LEVEL) * 100.0

        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM user_badges WHERE user_id = ?;", (user_id,)
            )
            earned_badges = cursor.fetchone()[0] or 0

            cursor.execute("SELECT COUNT(*) FROM badges;")
            total_badges = cursor.fetchone()[0] or 0

        return UserGamificationStats(
            total_xp=total_xp,
            level=level,
            xp_in_level=xp_in_level,
            xp_for_next_level=XP_PER_LEVEL,
            level_progress_percentage=round(progress_pct, 1),
            badges_earned_count=earned_badges,
            total_badges_count=total_badges,
        )

    def evaluate_user_achievements(self, user_id: int) -> list[str]:
        """Evaluate criteria and award eligible badges.

        Returns a list of badge codes newly awarded in this evaluation.
        Ensures strict idempotency: no badge is awarded twice.
        """
        newly_awarded: list[str] = []

        with self.db.connect() as conn:
            cursor = conn.cursor()

            # Load all badges
            cursor.execute("SELECT id, code, name, xp_reward FROM badges;")
            all_badges = {row["code"]: row for row in cursor.fetchall()}

            # Load already awarded badge IDs
            cursor.execute(
                "SELECT b.code FROM user_badges ub JOIN badges b ON ub.badge_id = b.id WHERE ub.user_id = ?;",
                (user_id,),
            )
            earned_codes = {row[0] for row in cursor.fetchall()}

            # Gather user metrics
            # 1. Observation count
            cursor.execute(
                "SELECT COUNT(*) FROM observations WHERE owner_id = ?;", (user_id,)
            )
            obs_count = cursor.fetchone()[0] or 0

            # 2. Distinct taxa count in collection
            cursor.execute(
                "SELECT COUNT(DISTINCT taxon_id) FROM collections WHERE user_id = ?;",
                (user_id,),
            )
            taxa_count = cursor.fetchone()[0] or 0

            # 3. Distinct families count
            cursor.execute(
                """
                SELECT COUNT(DISTINCT t.family)
                FROM observations o
                JOIN taxa t ON o.matched_taxon_id = t.taxon_id
                WHERE o.owner_id = ? AND t.family IS NOT NULL AND trim(t.family) != '';
                """,
                (user_id,),
            )
            family_count = cursor.fetchone()[0] or 0

            # 4. Field notes count
            cursor.execute(
                """
                SELECT COUNT(*) FROM observations
                WHERE owner_id = ? AND length(trim(field_notes)) >= 5;
                """,
                (user_id,),
            )
            notes_count = cursor.fetchone()[0] or 0

            # 5. Accepted observations count
            cursor.execute(
                """
                SELECT COUNT(*) FROM observations
                WHERE owner_id = ? AND moderation_status = 'ACCEPTED_FOR_CATALOG';
                """,
                (user_id,),
            )
            accepted_count = cursor.fetchone()[0] or 0

            now = utc_now_iso()

            # Rule evaluations
            evaluations = [
                ("first_encounter", obs_count >= 1),
                ("collector", taxa_count >= 5),
                ("family_explorer", family_count >= 3),
                ("field_naturalist", notes_count >= 5),
                ("contributor", accepted_count >= 1),
            ]

            for code, is_eligible in evaluations:
                if is_eligible and code not in earned_codes and code in all_badges:
                    badge_id = all_badges[code]["id"]
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO user_badges (user_id, badge_id, awarded_at)
                        VALUES (?, ?, ?);
                        """,
                        (user_id, badge_id, now),
                    )
                    if cursor.rowcount > 0:
                        newly_awarded.append(code)
                        # Record audit log
                        cursor.execute(
                            """
                            INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details, timestamp)
                            VALUES (?, 'BADGE_AWARDED', 'BADGE', ?, ?, ?);
                            """,
                            (
                                user_id,
                                code,
                                f"Awarded badge: {all_badges[code]['name']}",
                                now,
                            ),
                        )

        return newly_awarded

    def get_user_badges(self, user_id: int) -> list[UserBadgeRecord]:
        """Return all badges awarded to the specified user."""
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT ub.id, ub.user_id, ub.badge_id, b.code, b.name, b.description,
                       b.icon, b.xp_reward, ub.awarded_at
                FROM user_badges ub
                JOIN badges b ON ub.badge_id = b.id
                WHERE ub.user_id = ?
                ORDER BY ub.awarded_at ASC;
                """,
                (user_id,),
            )
            return [
                UserBadgeRecord(
                    id=row["id"],
                    user_id=row["user_id"],
                    badge_id=row["badge_id"],
                    code=row["code"],
                    name=row["name"],
                    description=row["description"],
                    icon=row["icon"],
                    xp_reward=row["xp_reward"],
                    awarded_at=row["awarded_at"],
                )
                for row in cursor.fetchall()
            ]

    def get_all_badge_progress(self, user_id: int) -> list[AchievementProgress]:
        """Return all badges and the user's progress toward each."""
        with self.db.connect() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT id, code, name, description, icon, xp_reward FROM badges ORDER BY id ASC;")
            all_badges = cursor.fetchall()

            cursor.execute(
                "SELECT b.code FROM user_badges ub JOIN badges b ON ub.badge_id = b.id WHERE ub.user_id = ?;",
                (user_id,),
            )
            earned_codes = {row[0] for row in cursor.fetchall()}

            # Metrics
            cursor.execute("SELECT COUNT(*) FROM observations WHERE owner_id = ?;", (user_id,))
            obs_count = cursor.fetchone()[0] or 0

            cursor.execute("SELECT COUNT(DISTINCT taxon_id) FROM collections WHERE user_id = ?;", (user_id,))
            taxa_count = cursor.fetchone()[0] or 0

            cursor.execute(
                """
                SELECT COUNT(DISTINCT t.family)
                FROM observations o
                JOIN taxa t ON o.matched_taxon_id = t.taxon_id
                WHERE o.owner_id = ? AND t.family IS NOT NULL AND trim(t.family) != '';
                """,
                (user_id,),
            )
            family_count = cursor.fetchone()[0] or 0

            cursor.execute(
                "SELECT COUNT(*) FROM observations WHERE owner_id = ? AND length(trim(field_notes)) >= 5;",
                (user_id,),
            )
            notes_count = cursor.fetchone()[0] or 0

            cursor.execute(
                "SELECT COUNT(*) FROM observations WHERE owner_id = ? AND moderation_status = 'ACCEPTED_FOR_CATALOG';",
                (user_id,),
            )
            accepted_count = cursor.fetchone()[0] or 0

            targets = {
                "first_encounter": (min(obs_count, 1), 1),
                "collector": (min(taxa_count, 5), 5),
                "family_explorer": (min(family_count, 3), 3),
                "field_naturalist": (min(notes_count, 5), 5),
                "contributor": (min(accepted_count, 1), 1),
            }

            results: list[AchievementProgress] = []
            for row in all_badges:
                code = row["code"]
                curr, target = targets.get(code, (0, 1))
                is_earned = code in earned_codes
                results.append(
                    AchievementProgress(
                        code=code,
                        name=row["name"],
                        description=row["description"],
                        icon=row["icon"],
                        current_value=target if is_earned else curr,
                        target_value=target,
                        is_earned=is_earned,
                        xp_reward=row["xp_reward"],
                    )
                )

            return results
