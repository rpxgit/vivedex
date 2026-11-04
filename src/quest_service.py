"""Quest and naturalist habit progression service for Vivédex.

Inspired by Habitica, provides constructive, non-punitive habits, recurring goals,
and milestone quests to motivate scientific fieldwork and biodiversity documentation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.database import Database, utc_now_iso


@dataclass(frozen=True)
class Quest:
    """Quest definition or field habit."""

    id: int
    code: str
    title: str
    description: str
    quest_type: str  # HABIT, RECURRING_GOAL, MILESTONE
    target_count: int
    xp_reward: int
    icon: str
    criteria_type: str
    created_at: str


@dataclass(frozen=True)
class UserQuestStatus:
    """User progress towards a quest."""

    quest_id: int
    code: str
    title: str
    description: str
    quest_type: str
    target_count: int
    xp_reward: int
    icon: str
    criteria_type: str
    current_progress: int
    is_completed: bool
    completed_at: str | None
    claimed_at: str | None
    last_logged_at: str | None


class QuestService:
    """Manages quests, field habit tracking, and reward claims."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def list_quests(self, quest_type: str | None = None) -> list[Quest]:
        """Return all available quests, optionally filtered by type."""
        with self.db.connect() as conn:
            cursor = conn.cursor()
            if quest_type:
                cursor.execute(
                    """
                    SELECT id, code, title, description, quest_type, target_count, xp_reward, icon, criteria_type, created_at
                    FROM quests WHERE quest_type = ?
                    ORDER BY id ASC;
                    """,
                    (quest_type,),
                )
            else:
                cursor.execute(
                    """
                    SELECT id, code, title, description, quest_type, target_count, xp_reward, icon, criteria_type, created_at
                    FROM quests
                    ORDER BY id ASC;
                    """
                )
            return [Quest(**dict(r)) for r in cursor.fetchall()]

    def get_user_quests(self, user_id: int) -> list[UserQuestStatus]:
        """Evaluate and return all quests with the current user's progress."""
        self.evaluate_user_quests(user_id)
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    q.id as quest_id, q.code, q.title, q.description, q.quest_type,
                    q.target_count, q.xp_reward, q.icon, q.criteria_type,
                    COALESCE(uq.current_progress, 0) as current_progress,
                    COALESCE(uq.is_completed, 0) as is_completed,
                    uq.completed_at,
                    uq.claimed_at,
                    uq.last_logged_at
                FROM quests q
                LEFT JOIN user_quests uq ON uq.quest_id = q.id AND uq.user_id = ?
                ORDER BY q.id ASC;
                """,
                (user_id,),
            )
            rows = cursor.fetchall()
            return [
                UserQuestStatus(
                    quest_id=r["quest_id"],
                    code=r["code"],
                    title=r["title"],
                    description=r["description"],
                    quest_type=r["quest_type"],
                    target_count=r["target_count"],
                    xp_reward=r["xp_reward"],
                    icon=r["icon"],
                    criteria_type=r["criteria_type"],
                    current_progress=r["current_progress"],
                    is_completed=bool(r["is_completed"]),
                    completed_at=r["completed_at"],
                    claimed_at=r["claimed_at"],
                    last_logged_at=r["last_logged_at"],
                )
                for r in rows
            ]

    def evaluate_user_quests(self, user_id: int) -> None:
        """Calculate progress for all quests based on user activity records."""
        with self.db.connect() as conn:
            cursor = conn.cursor()

            # 1. Total observations count
            cursor.execute("SELECT COUNT(*) FROM observations WHERE owner_id = ?;", (user_id,))
            obs_count = cursor.fetchone()[0]

            # 2. Observations with field notes
            cursor.execute(
                "SELECT COUNT(*) FROM observations WHERE owner_id = ? AND TRIM(field_notes) != '';",
                (user_id,),
            )
            notes_count = cursor.fetchone()[0]

            # 3. Personal collection count
            cursor.execute("SELECT COUNT(*) FROM collections WHERE user_id = ?;", (user_id,))
            collection_count = cursor.fetchone()[0]

            # 4. Distinct families observed
            cursor.execute(
                """
                SELECT COUNT(DISTINCT t.family)
                FROM observations o
                JOIN taxa t ON t.taxon_id = o.matched_taxon_id
                WHERE o.owner_id = ? AND t.family IS NOT NULL AND TRIM(t.family) != '';
                """,
                (user_id,),
            )
            family_count = cursor.fetchone()[0]

            # 5. Site visits (observations with site_id assigned)
            cursor.execute(
                "SELECT COUNT(*) FROM observations WHERE owner_id = ? AND site_id IS NOT NULL;",
                (user_id,),
            )
            site_count = cursor.fetchone()[0]

            # Fetch all quests
            cursor.execute("SELECT id, criteria_type, target_count FROM quests;")
            quests = cursor.fetchall()
            now = utc_now_iso()

            for q in quests:
                q_id = q["id"]
                crit = q["criteria_type"]
                target = q["target_count"]

                val = 0
                if crit == "OBSERVATION_COUNT":
                    val = obs_count
                elif crit == "FIELD_NOTES_COUNT":
                    val = notes_count
                elif crit == "COLLECTION_COUNT":
                    val = collection_count
                elif crit == "FAMILY_COUNT":
                    val = family_count
                elif crit == "SITE_VISIT":
                    val = site_count

                is_complete = 1 if val >= target else 0

                # Insert or update user_quest progress
                cursor.execute(
                    """
                    INSERT INTO user_quests (user_id, quest_id, current_progress, is_completed, completed_at, last_logged_at)
                    VALUES (?, ?, ?, ?, CASE WHEN ? = 1 THEN ? ELSE NULL END, ?)
                    ON CONFLICT(user_id, quest_id) DO UPDATE SET
                        current_progress = MAX(user_quests.current_progress, excluded.current_progress),
                        is_completed = CASE WHEN user_quests.is_completed = 1 OR MAX(user_quests.current_progress, excluded.current_progress) >= ? THEN 1 ELSE excluded.is_completed END,
                        completed_at = CASE 
                            WHEN user_quests.completed_at IS NOT NULL THEN user_quests.completed_at 
                            WHEN excluded.is_completed = 1 OR MAX(user_quests.current_progress, excluded.current_progress) >= ? THEN COALESCE(user_quests.completed_at, ?) 
                            ELSE NULL 
                        END,
                        last_logged_at = excluded.last_logged_at;
                    """,
                    (user_id, q_id, val, is_complete, is_complete, now, now, target, target, now),
                )

    def log_habit_action(self, user_id: int, quest_id: int) -> bool:
        """Manually log a positive habit action (e.g. daily field scan)."""
        now = utc_now_iso()
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT target_count FROM quests WHERE id = ?;", (quest_id,))
            q_row = cursor.fetchone()
            if not q_row:
                return False
            target = q_row[0]

            cursor.execute(
                """
                INSERT INTO user_quests (user_id, quest_id, current_progress, is_completed, completed_at, last_logged_at)
                VALUES (?, ?, 1, CASE WHEN 1 >= ? THEN 1 ELSE 0 END, CASE WHEN 1 >= ? THEN ? ELSE NULL END, ?)
                ON CONFLICT(user_id, quest_id) DO UPDATE SET
                    current_progress = current_progress + 1,
                    is_completed = CASE WHEN current_progress + 1 >= ? THEN 1 ELSE is_completed END,
                    completed_at = CASE WHEN completed_at IS NOT NULL THEN completed_at WHEN current_progress + 1 >= ? THEN ? ELSE NULL END,
                    last_logged_at = ?;
                """,
                (user_id, quest_id, target, target, now, now, target, target, now, now),
            )
            return True

    def claim_quest_reward(self, user_id: int, quest_id: int) -> tuple[bool, int, str]:
        """Claim the XP reward for a completed quest."""
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT uq.is_completed, uq.claimed_at, q.xp_reward, q.title
                FROM user_quests uq
                JOIN quests q ON q.id = uq.quest_id
                WHERE uq.user_id = ? AND uq.quest_id = ?;
                """,
                (user_id, quest_id),
            )
            row = cursor.fetchone()
            if not row:
                return False, 0, "Quest progress not found."
            if not row["is_completed"]:
                return False, 0, "Quest is not completed yet."
            if row["claimed_at"]:
                return False, 0, "Reward has already been claimed."

            xp = row["xp_reward"]
            title = row["title"]
            now = utc_now_iso()

            # Mark claimed
            cursor.execute(
                "UPDATE user_quests SET claimed_at = ? WHERE user_id = ? AND quest_id = ?;",
                (now, user_id, quest_id),
            )

            # Record in audit log
            cursor.execute(
                """
                INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details, timestamp)
                VALUES (?, 'QUEST_CLAIM', 'quest', ?, ?, ?);
                """,
                (user_id, str(quest_id), f"Claimed {xp} XP for quest '{title}'", now),
            )
            return True, xp, f"Successfully claimed {xp} XP for '{title}'!"
