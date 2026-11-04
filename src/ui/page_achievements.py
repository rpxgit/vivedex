"""Achievements and Naturalist Progression view for Vivédex.

Presents authentic naturalist ranks (Observer to Biodiversity Steward),
badge families (First Encounters, Taxonomic Exploration, Field Documentation, Platform Contribution),
and transparent, non-punitive XP progression.
"""

from __future__ import annotations

import streamlit as st

from src.achievements import AchievementService
from src.auth import AuthenticatedUser
from src.ui.common import inject_custom_styles, render_security_notice
from src.ui.theme import escape_text, get_naturalist_rank, render_hero_banner

# Badge family mappings
BADGE_FAMILIES = {
    "first_encounter": ("🌱 First Encounters", "Initial organism sightings in the wild"),
    "collector": ("📚 Taxonomic Exploration", "Broadening personal biodiversity representation"),
    "family_explorer": ("🌳 Taxonomic Exploration", "Documenting deep phylogenetic variety"),
    "field_naturalist": ("📝 Field Documentation", "Enriching sightings with behavioral and ecological notes"),
    "contributor": ("🏅 Research Contributions", "Advancing catalog entries approved by moderation"),
}


def render_achievements_page(achievement_service: AchievementService) -> None:
    """Render the reconstructed naturalist progression and achievement view."""
    inject_custom_styles()
    render_security_notice()

    current_user: AuthenticatedUser | None = st.session_state.get("current_user")

    # Banner
    render_hero_banner(
        title="🏆 Naturalist Progression & Milestones",
        subtitle="Meaningful achievement progression honoring authentic field observations, deep taxonomic discovery, and scientific contributions.",
    )

    if current_user is None:
        st.info("👋 Please log in or register via the sidebar to view your naturalist rank, XP, and milestone badges.")
        return

    # Progression Stats
    stats = achievement_service.get_user_gamification_stats(current_user.id)
    rank_title = get_naturalist_rank(stats.level)
    next_rank = get_naturalist_rank(stats.level + 1)

    # Rank Showcase Card
    esc_rank_title = escape_text(rank_title)
    esc_next_rank = escape_text(next_rank)
    st.markdown(
        f"""
        <div class="specimen-card" style="border-left: 5px solid #C6A66B; margin-bottom: 1.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
                <div>
                    <div style="font-size: 0.78rem; text-transform: uppercase; color: #777E73; font-weight: 700; letter-spacing: 0.05em;">Current Rank</div>
                    <div style="font-family: 'Cinzel', serif; font-size: 1.8rem; font-weight: 700; color: #183B32;">
                        Level {int(stats.level)} &bull; {esc_rank_title}
                    </div>
                    <div style="font-size: 0.9rem; color: #555; margin-top: 4px;">
                        Cumulative Experience: <strong style="color: #A66B48;">{int(stats.total_xp)} XP</strong> &bull; Milestones Earned: <strong>{int(stats.badges_earned_count)} / {int(stats.total_badges_count)}</strong>
                    </div>
                </div>
                <div style="text-align: right;">
                    <span class="dex-collected-tag" style="font-size: 0.9rem; padding: 6px 16px;">Next Rank: {esc_next_rank}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Level Progress Bar
    st.markdown(
        f"**Progression to Level {stats.level + 1} ({next_rank}):** {stats.xp_in_level} / {stats.xp_for_next_level} XP ({stats.level_progress_percentage}%)"
    )
    st.progress(min(1.0, max(0.0, stats.level_progress_percentage / 100.0)))

    # Naturalist Ranks Hierarchy Guide
    with st.expander("📖 Inspect Naturalist Rank Hierarchy"):
        st.markdown(
            """
            - **Level 1 — Observer:** Beginning natural history documentation (0 - 99 XP).
            - **Level 2 — Explorer:** Broadening personal collection encounters (100 - 199 XP).
            - **Level 3 — Naturalist:** Adding rigorous morphological and habitat field notes (200 - 299 XP).
            - **Level 4 — Field Researcher:** Spanning multiple diverse phylogenetic families (300 - 399 XP).
            - **Level 5 — Specialist:** Advanced identification and catalog-verified observations (400 - 499 XP).
            - **Level 6+ — Biodiversity Steward:** Master contributor enriching the platform knowledge graph (500+ XP).
            """
        )

    # Badges Grid Grouped by Family
    st.markdown("---")
    st.subheader("🎖️ Milestone Badge Families")

    all_progress = achievement_service.get_all_badge_progress(current_user.id)

    cols = st.columns(2)
    for idx, p in enumerate(all_progress):
        fam_name, fam_desc = BADGE_FAMILIES.get(p.code, ("Platform Milestone", "General milestone"))
        earned_tag = (
            '<span class="status-pill-accepted">✅ EARNED</span>'
            if p.is_earned
            else '<span class="status-pill-pending">IN PROGRESS</span>'
        )

        with cols[idx % 2]:
            esc_icon = escape_text(p.icon)
            esc_fam_name = escape_text(fam_name)
            esc_name = escape_text(p.name)
            esc_desc = escape_text(p.description)
            st.markdown(
                f"""
                <div class="specimen-card" style="border: 2px solid {'#183B32' if p.is_earned else '#ded6c5'}; background: {'#f7fcf8' if p.is_earned else '#ffffff'};">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px;">
                        <span style="font-size: 2rem;">{esc_icon}</span>
                        <div>
                            {earned_tag}
                            <span class="dex-collected-tag" style="margin-left: 4px;">+{int(p.xp_reward)} XP</span>
                        </div>
                    </div>
                    <div style="font-size: 0.75rem; text-transform: uppercase; color: #718568; font-weight: 700; letter-spacing: 0.04em;">
                        {esc_fam_name}
                    </div>
                    <div style="font-family: 'Cinzel', serif; font-size: 1.15rem; font-weight: 700; color: #183B32; margin: 2px 0 6px 0;">
                        {esc_name}
                    </div>
                    <div style="font-size: 0.85rem; color: #555; margin-bottom: 8px;">
                        {esc_desc}
                    </div>
                    <div style="font-size: 0.78rem; font-weight: 700; color: #183B32;">
                        Criteria Progress: {int(p.current_value)} / {int(p.target_value)}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            pct = min(1.0, p.current_value / max(1, p.target_value))
            st.progress(pct)

    # XP Incentives Guide
    st.markdown("---")
    st.subheader("⚖️ Ethical Citizen-Science Experience Model")
    st.markdown(
        """
        Vivédex rejects punitive daily streaks and artificial gaming loops. Experience points are awarded solely for authentic scientific actions:
        - **First Encounter with a Species:** `+50 XP` awarded once per unique taxon in your personal collection.
        - **Detailed Natural History Note:** `+20 XP` for adding morphological, behavioral, or habitat notes (>= 5 chars).
        - **Moderation Acceptance:** `+100 XP` when an observation passes platform moderation into the curated catalog.
        - **Milestone Rewards:** Substantial bonus XP for unlocking platform badge families.
        """
    )
