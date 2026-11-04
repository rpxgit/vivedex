"""Home dashboard page for Vivédex.

Presents user statistics, collection progress, badges, and quick actions.
"""

from __future__ import annotations

import streamlit as st

from src.achievements import AchievementService
from src.auth import AuthenticatedUser
from src.collection_service import CollectionService
from src.database import Database
from src.ui.common import inject_custom_styles, render_security_notice


def render_home_page(
    db: Database,
    collection_service: CollectionService,
    achievement_service: AchievementService,
) -> None:
    """Render the main home dashboard view."""
    inject_custom_styles()
    render_security_notice()

    current_user: AuthenticatedUser | None = st.session_state.get("current_user")

    st.title("🌿 Vivédex")
    st.subheader("Biodiversity Discovery, Collection, and Taxonomic Reconciliation")

    if current_user is None:
        st.info("👋 **Welcome to Vivédex!** Please log in or register via the sidebar to view your collection, record observations, and track achievements.")
        # Provide guest summary
        col_cta1, col_cta2 = st.columns([1, 1])
        with col_cta1:
            st.markdown("### 🔍 Start Exploring")
            st.write("Use the **Identify** pipeline to analyze organism images with Meta Muse Spark and reconcile against the GBIF Backbone Taxonomy.")
            if st.button("Go to Identify Page", type="primary"):
                st.session_state["nav_target"] = "Identify"
                st.rerun()
        with col_cta2:
            st.markdown("### 📖 Browse the Dex")
            st.write("Search taxonomic records and explore biological classifications.")
            if st.button("Open Explore Dex"):
                st.session_state["nav_target"] = "Explore Dex"
                st.rerun()
        return

    # User is logged in: gather statistics
    profile = collection_service.get_user_profile(current_user.id)
    gamification = achievement_service.get_user_gamification_stats(current_user.id)
    badges = achievement_service.get_user_badges(current_user.id)
    recent_obs = collection_service.get_user_observations(current_user.id)[:5]

    # Contributor Header
    st.markdown(
        f"""
        <div class="card-box">
            <h3 style="margin:0; color: #1b4332;">Welcome back, {current_user.display_name}!</h3>
            <p style="margin:0; color: #555;">Vivédex Contributor ID: <code>{current_user.vivedex_id}</code> | Account Role: <strong>{current_user.role.upper()}</strong></p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 4-Column Metric Cards
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Recorded Observations", profile.observation_count if profile else 0)
    with m2:
        st.metric("Distinct Taxa Collected", profile.distinct_taxa_count if profile else 0)
    with m3:
        st.metric("Families Represented", profile.family_count if profile else 0)
    with m4:
        st.metric(f"Level {gamification.level}", f"{gamification.total_xp} XP")

    # Level Progress Bar
    st.markdown(f"**Progression to Level {gamification.level + 1}** ({gamification.xp_in_level} / {gamification.xp_for_next_level} XP)")
    st.progress(min(1.0, max(0.0, gamification.level_progress_percentage / 100.0)))

    # Two columns: Recent Observations & Earned Badges
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.subheader("📋 Recent Field Observations")
        if recent_obs:
            for obs in recent_obs:
                prov_label = f"[{obs.provenance}] " if obs.provenance == "DEMO DATA" else ""
                with st.expander(f"{prov_label}{obs.candidate_scientific_name} ({obs.observation_timestamp[:10]}) — {obs.moderation_status}"):
                    st.write(f"**Observation ID:** `{obs.observation_id}`")
                    if obs.coarse_location:
                        st.write(f"**Location:** {obs.coarse_location}")
                    if obs.field_notes:
                        st.write(f"**Field Notes:** {obs.field_notes}")
                    st.caption(f"Taxonomic Resolution: {obs.taxonomic_resolution or 'Unresolved'}")
        else:
            st.info("No observations recorded yet. Go to **Identify** to analyze an organism photograph!")

        st.markdown("---")
        if st.button("🌱 Identify an Organism Now", type="primary"):
            st.session_state["nav_target"] = "Identify"
            st.rerun()

    with col_right:
        st.subheader("🏅 Earned Achievements")
        if badges:
            for b in badges:
                st.markdown(
                    f"""
                    <div style="background: #fdfdfd; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px 12px; margin-bottom: 8px;">
                        <span style="font-size: 1.3rem;">{b.icon}</span> <strong>{b.name}</strong> (+{b.xp_reward} XP)<br/>
                        <span style="font-size: 0.85rem; color: #555;">{b.description}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No badges earned yet. Record your first observation to unlock the First Encounter badge!")

        st.markdown("---")
        all_progress = achievement_service.get_all_badge_progress(current_user.id)
        in_progress = [p for p in all_progress if not p.is_earned]
        if in_progress:
            st.markdown("#### Next Available Milestone")
            next_badge = in_progress[0]
            st.write(f"**{next_badge.icon} {next_badge.name}**")
            st.caption(next_badge.description)
            pct = next_badge.current_value / max(1, next_badge.target_value)
            st.progress(min(1.0, pct))
            st.caption(f"Progress: {next_badge.current_value} / {next_badge.target_value}")
