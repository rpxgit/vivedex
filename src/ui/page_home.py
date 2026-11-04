"""Home expedition hub for Vivédex.

Presents a naturalist expedition dashboard, biodiversity metrics, recent discoveries,
current expedition quests, and public onboarding landing page.
"""

from __future__ import annotations

import streamlit as st

from src.achievements import AchievementService
from src.auth import AuthenticatedUser
from src.collection_service import CollectionService
from src.database import Database
from src.ui.common import inject_custom_styles, render_security_notice
from src.ui.theme import get_naturalist_rank, render_hero_banner


def render_home_page(
    db: Database,
    collection_service: CollectionService,
    achievement_service: AchievementService,
) -> None:
    """Render the reconstructed naturalist expedition dashboard."""
    inject_custom_styles()
    render_security_notice()

    current_user: AuthenticatedUser | None = st.session_state.get("current_user")

    # Title for Streamlit component tree and accessibility
    st.title("🌿 Vivédex Expedition Hub")
    st.caption("Empowering field naturalists and researchers to discover, identify, reconcile, and catalog biodiversity backed by authoritative GBIF taxonomy.")

    # Grand Botanical Hero Banner
    render_hero_banner(
        title="🌿 Vivédex Expedition Hub",
        subtitle="Empowering field naturalists and researchers to discover, identify, reconcile, and catalog biodiversity backed by authoritative GBIF taxonomy.",
    )

    # 1. Logged-Out Public Landing Experience
    if current_user is None:
        st.markdown(
            """
            <div style="background: #ffffff; border: 1px solid #ded6c5; border-radius: 10px; padding: 2rem; margin-bottom: 2rem; box-shadow: 0 4px 14px rgba(0,0,0,0.03);">
                <div style="font-family: 'Cinzel', serif; font-size: 1.4rem; font-weight: 700; color: #183B32; margin-bottom: 0.5rem;">
                    Welcome, Explorer
                </div>
                <p style="font-size: 1.05rem; color: #444; line-height: 1.6; margin-bottom: 1.2rem;">
                    Vivédex is a citizen-science natural history platform. Identify wild flora and fauna with multimodal AI vision (Meta Muse Spark),
                    verify proposed names against the <strong>GBIF Backbone Taxonomy</strong> under open CC BY 4.0 licensing,
                    and build your personal biological encyclopedia.
                </p>
                <div style="display: flex; gap: 16px; flex-wrap: wrap;">
                    <div style="flex: 1; min-width: 200px; background: #fdfaf4; padding: 14px; border-radius: 8px; border: 1px solid #e8e0d0;">
                        <strong style="color: #183B32;">🔍 Discover & Explore</strong><br/>
                        <span style="font-size: 0.85rem; color: #666;">Browse birds, mammals, plants, fungi, and insects reconciled with global taxonomic backbones.</span>
                    </div>
                    <div style="flex: 1; min-width: 200px; background: #fdfaf4; padding: 14px; border-radius: 8px; border: 1px solid #e8e0d0;">
                        <strong style="color: #183B32;">🌿 Identify Organisms</strong><br/>
                        <span style="font-size: 0.85rem; color: #666;">Upload specimen photographs with in-memory EXIF stripping and explainable trait inspection.</span>
                    </div>
                    <div style="flex: 1; min-width: 200px; background: #fdfaf4; padding: 14px; border-radius: 8px; border: 1px solid #e8e0d0;">
                        <strong style="color: #183B32;">🏆 Naturalist Ranks</strong><br/>
                        <span style="font-size: 0.85rem; color: #666;">Progress from Observer to Biodiversity Steward by collecting species and documenting habitats.</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_act1, col_act2 = st.columns([1, 1])
        with col_act1:
            st.info("Log in or register via the sidebar to access your personal Dex, Field Journal, and achievements.")
        with col_act2:
            st.write("**Quick Expeditions:**")
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if st.button("🌱 Identify Organism", type="primary", width="stretch"):
                    st.session_state["nav_target"] = "Identify"
                    st.rerun()
            with col_b2:
                if st.button("🔍 Explore Dex", width="stretch"):
                    st.session_state["nav_target"] = "Explore"
                    st.rerun()
        return

    # 2. Logged-In Naturalist Expedition Dashboard
    profile = collection_service.get_user_profile(current_user.id)
    gamification = achievement_service.get_user_gamification_stats(current_user.id)
    badges = achievement_service.get_user_badges(current_user.id)
    recent_obs = collection_service.get_user_observations(current_user.id)[:4]
    all_quests = achievement_service.get_all_badge_progress(current_user.id)
    active_quests = [q for q in all_quests if not q.is_earned]

    rank_title = get_naturalist_rank(gamification.level)

    # Contributor Overview Card
    st.markdown(
        f"""
        <div class="specimen-card" style="border-left: 5px solid #183B32; margin-bottom: 1.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px;">
                <div>
                    <div style="font-size: 0.78rem; text-transform: uppercase; color: #777E73; font-weight: 700; letter-spacing: 0.05em;">Naturalist Station</div>
                    <h2 style="margin: 0; color: #183B32; font-size: 1.8rem;">{current_user.display_name}</h2>
                    <div style="font-size: 0.88rem; color: #A66B48; font-weight: 600; margin-top: 2px;">
                        Level {gamification.level} {rank_title} &bull; Contributor ID: <code style="color:#183B32;">{current_user.vivedex_id}</code>
                    </div>
                </div>
                <div style="text-align: right;">
                    <span class="dex-collected-tag" style="font-size: 0.82rem; padding: 4px 12px;">Rank: {rank_title}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 4-Column Naturalist Metric Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"""
            <div class="naturalist-metric">
                <div class="metric-val">{profile.observation_count if profile else 0}</div>
                <div class="metric-label">Field Sightings</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="naturalist-metric">
                <div class="metric-val">{profile.distinct_taxa_count if profile else 0}</div>
                <div class="metric-label">Taxa In Dex</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""
            <div class="naturalist-metric">
                <div class="metric-val">{profile.family_count if profile else 0}</div>
                <div class="metric-label">Families Documented</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f"""
            <div class="naturalist-metric">
                <div class="metric-val" style="color: #A66B48;">{gamification.total_xp}</div>
                <div class="metric-label">Experience Points (XP)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")
    # Level Progress Bar
    next_rank = get_naturalist_rank(gamification.level + 1)
    st.markdown(
        f"**Level {gamification.level} Progress toward {next_rank}:** {gamification.xp_in_level} / {gamification.xp_for_next_level} XP ({gamification.level_progress_percentage}%)"
    )
    st.progress(min(1.0, max(0.0, gamification.level_progress_percentage / 100.0)))

    st.markdown("---")

    # Two Main Columns: Recent Discoveries & Quests
    col_disc, col_quest = st.columns([11, 9])

    with col_disc:
        st.subheader("🌿 Recent Field Discoveries")
        if recent_obs:
            for obs in recent_obs:
                prov_tag = f"[{obs.provenance}] " if obs.provenance == "DEMO DATA" else ""
                status_class = (
                    "status-pill-accepted"
                    if obs.moderation_status == "ACCEPTED_FOR_CATALOG"
                    else "status-pill-pending"
                )

                st.markdown(
                    f"""
                    <div class="specimen-card" style="padding: 1rem; margin-bottom: 0.8rem;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                            <span style="font-size: 0.76rem; color: #777E73;">{obs.observation_timestamp[:10]} &bull; {obs.observation_id}</span>
                            <span class="{status_class}">{obs.moderation_status}</span>
                        </div>
                        <div style="font-size: 1.15rem; font-weight: 700; color: #183B32;">
                            {prov_tag}<span class="latin-binomial">*{obs.candidate_scientific_name}*</span>
                        </div>
                        <div style="font-size: 0.85rem; color: #555; margin-top: 4px;">
                            {obs.field_notes or 'No natural history field notes entered.'}
                        </div>
                        {f'<div style="font-size: 0.78rem; color: #A66B48; margin-top: 4px;">📍 {obs.coarse_location}</div>' if obs.coarse_location else ''}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                """
                <div style="background: #faf7f0; border: 1px dashed #ded6c5; border-radius: 8px; padding: 20px; text-align: center; color: #777E73;">
                    <div style="font-size: 1.6rem; margin-bottom: 6px;">📷</div>
                    <div style="font-weight: 700; color: #183B32;">Your field journal is waiting.</div>
                    <div style="font-size: 0.85rem; margin-top: 4px;">Take an organism photograph and analyze diagnostic traits to record your first discovery.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.write("")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            if st.button("🌱 Identify Organism Photograph", type="primary", width="stretch", key="home_cta_identify"):
                st.session_state["nav_target"] = "Identify"
                st.rerun()
        with col_c2:
            if st.button("🔍 Explore Full Dex Catalog", width="stretch", key="home_cta_explore"):
                st.session_state["nav_target"] = "Explore"
                st.rerun()

    with col_quest:
        st.subheader("🎯 Active Naturalist Quests")
        if active_quests:
            for q in active_quests[:3]:
                st.markdown(
                    f"""
                    <div class="quest-box">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 1.4rem;">{q.icon}</span>
                            <span style="font-size: 0.75rem; font-weight: 700; color: #A66B48;">REWARD: +{q.xp_reward} XP</span>
                        </div>
                        <div style="font-size: 0.95rem; font-weight: 700; color: #183B32; margin: 4px 0;">{q.name}</div>
                        <div style="font-size: 0.8rem; color: #555; margin-bottom: 6px;">{q.description}</div>
                        <div style="font-size: 0.76rem; font-weight: 700; color: #183B32;">Progress: {q.current_value} / {q.target_value}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.progress(min(1.0, q.current_value / max(1, q.target_value)))
        else:
            st.success("🎉 All initial naturalist milestone quests have been completed!")

        st.markdown("---")
        st.subheader(f"🎖️ Earned Milestones ({len(badges)})")
        if badges:
            for b in badges:
                st.markdown(
                    f"""
                    <div style="background: #ffffff; border: 1px solid #e3ddd0; border-radius: 6px; padding: 8px 12px; margin-bottom: 6px; display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 1.3rem;">{b.icon}</span>
                        <div>
                            <div style="font-size: 0.88rem; font-weight: 700; color: #183B32;">{b.name}</div>
                            <div style="font-size: 0.75rem; color: #777E73;">{b.description}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.caption("Record your first organism observation to unlock the First Encounter badge.")
