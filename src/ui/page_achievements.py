"""Achievements and XP progression view for Vivédex.

Displays earned badges, criteria progress bars, player level, and experience points.
"""

from __future__ import annotations

import streamlit as st

from src.achievements import AchievementService
from src.auth import AuthenticatedUser
from src.ui.common import inject_custom_styles, render_security_notice


def render_achievements_page(achievement_service: AchievementService) -> None:
    """Render the achievements and level progression view."""
    inject_custom_styles()
    render_security_notice()

    current_user: AuthenticatedUser | None = st.session_state.get("current_user")

    st.markdown('<div class="main-header">🏆 Achievements & Badges</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Rule-based naturalist accomplishments and scientific milestones.</div>',
        unsafe_allow_html=True,
    )

    if current_user is None:
        st.info("Please log in or register via the sidebar to view your achievements and level progress.")
        return

    # Progression Stats
    stats = achievement_service.get_user_gamification_stats(current_user.id)

    st.markdown(
        f"""
        <div class="card-box">
            <h3 style="color: #1b4332; margin: 0;">Rank: Level {stats.level} Field Observer</h3>
            <p style="margin: 4px 0; color: #555;">Total Experience: <strong>{stats.total_xp} XP</strong> | Badges Earned: <strong>{stats.badges_earned_count} / {stats.total_badges_count}</strong></p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Level progress bar
    st.markdown(f"**Level {stats.level} Progress:** {stats.xp_in_level} / {stats.xp_for_next_level} XP ({stats.level_progress_percentage}%)")
    st.progress(min(1.0, max(0.0, stats.level_progress_percentage / 100.0)))

    # Badges Grid
    st.markdown("---")
    st.subheader("🎖️ Platform Milestone Badges")

    all_progress = achievement_service.get_all_badge_progress(current_user.id)

    cols = st.columns(2)
    for idx, p in enumerate(all_progress):
        with cols[idx % 2]:
            status_color = "#2d6a4f" if p.is_earned else "#6c757d"
            earned_badge_text = "✅ EARNED" if p.is_earned else "IN PROGRESS"
            st.markdown(
                f"""
                <div style="border: 2px solid {'#2d6a4f' if p.is_earned else '#dee2e6'}; border-radius: 8px; padding: 14px; margin-bottom: 12px; background: {'#f0fff4' if p.is_earned else '#ffffff'};">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 1.8rem;">{p.icon}</span>
                        <span style="font-size: 0.75rem; font-weight: 700; color: {status_color};">{earned_badge_text} (+{p.xp_reward} XP)</span>
                    </div>
                    <h4 style="margin: 6px 0; color: #1b4332;">{p.name}</h4>
                    <p style="font-size: 0.85rem; color: #555; margin-bottom: 8px;">{p.description}</p>
                    <div style="font-size: 0.8rem; font-weight: 600; color: #444;">Progress: {p.current_value} / {p.target_value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            pct = min(1.0, p.current_value / max(1, p.target_value))
            st.progress(pct)

    # XP Rules Guide
    st.markdown("---")
    st.subheader("📖 Experience Points (XP) Guide")
    st.markdown(
        """
        Vivédex awards experience points for authentic contributions to your personal knowledge and the platform:

        - **First Encounter with a Taxon:** `+50 XP` awarded once for each unique species/taxon added to your collection.
        - **Detailed Field Note:** `+20 XP` for adding morphological, behavioral, or habitat notes (>= 5 chars) to an observation.
        - **Accepted Contribution:** `+100 XP` when an observation is reviewed and accepted for the platform catalog.
        - **Milestone Badges:** Bonus XP awarded upon achieving each badge criteria.

        *Note: Vivédex does not reward duplicate submissions or use streak pressure.*
        """
    )

