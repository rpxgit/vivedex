"""Home expedition hub and public landing experience for Vivédex.

Presents a botanical editorial dashboard, live biodiversity metrics,
the core workflow (Discover → Identify → Verify → Collect → Learn → Contribute),
featured organisms, and active field habits.
"""

from __future__ import annotations

import streamlit as st

from src.achievements import AchievementService
from src.auth import AuthenticatedUser, AuthenticationError, AuthService
from src.collection_service import CollectionService
from src.database import Database
from src.ecological_service import EcologicalService
from src.quest_service import QuestService
from src.ui.common import inject_custom_styles, render_security_notice
from src.ui.theme import escape_text, get_naturalist_rank, render_hero_banner


def render_home_page(
    db: Database,
    collection_service: CollectionService,
    achievement_service: AchievementService,
) -> None:
    """Render the reconstructed naturalist expedition dashboard."""
    inject_custom_styles()
    render_security_notice()

    current_user: AuthenticatedUser | None = st.session_state.get("current_user")
    auth_service = st.session_state.get("auth_service", AuthService(db))
    eco_service = EcologicalService(db)
    quest_service = QuestService(db)

    # -------------------------------------------------------------------------
    # 1. Unauthenticated Visitor Landing Page
    # -------------------------------------------------------------------------
    if current_user is None:
        # Editorial Hero Banner (Single grand header, no duplicate titles)
        render_hero_banner(
            title="Vivédex Biodiversity Platform",
            subtitle="An evidence-based natural history discovery, identification, and specimen collection system backed by multimodal AI and the global GBIF Backbone Taxonomy.",
        )

        # Core Workflow Pillars
        st.markdown(
            """
            <div style="background: #FCFAF4; border: 1px solid #D8D1C2; border-radius: 10px; padding: 1.8rem 2rem; margin-bottom: 1.8rem; box-shadow: 0 2px 10px rgba(0,0,0,0.03);">
                <div style="font-family: 'Cinzel', serif; font-size: 1.25rem; font-weight: 700; color: #183B32; margin-bottom: 0.4rem;">
                    The Naturalist Workflow
                </div>
                <div style="font-size: 0.95rem; color: #4E5C53; margin-bottom: 1.4rem;">
                    Six deliberate steps connecting field observation to global scientific knowledge.
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 14px;">
                    <div style="background: #FFFFFF; border: 1px solid #E3DDD0; border-radius: 8px; padding: 12px 14px;">
                        <div style="font-size: 1.3rem; margin-bottom: 4px;">🔍</div>
                        <div style="font-weight: 700; color: #183B32; font-size: 0.9rem;">1. Discover</div>
                        <div style="font-size: 0.78rem; color: #4E5C53; margin-top: 4px;">Encounter living organisms across global habitats and field sites.</div>
                    </div>
                    <div style="background: #FFFFFF; border: 1px solid #E3DDD0; border-radius: 8px; padding: 12px 14px;">
                        <div style="font-size: 1.3rem; margin-bottom: 4px;">🧠</div>
                        <div style="font-weight: 700; color: #183B32; font-size: 0.9rem;">2. Identify</div>
                        <div style="font-size: 0.78rem; color: #4E5C53; margin-top: 4px;">Extract visual morphological markers with multimodal AI vision.</div>
                    </div>
                    <div style="background: #FFFFFF; border: 1px solid #E3DDD0; border-radius: 8px; padding: 12px 14px;">
                        <div style="font-size: 1.3rem; margin-bottom: 4px;">🌿</div>
                        <div style="font-weight: 700; color: #183B32; font-size: 0.9rem;">3. Verify</div>
                        <div style="font-size: 0.78rem; color: #4E5C53; margin-top: 4px;">Reconcile with GBIF Backbone Taxonomy with clear attribution.</div>
                    </div>
                    <div style="background: #FFFFFF; border: 1px solid #E3DDD0; border-radius: 8px; padding: 12px 14px;">
                        <div style="font-size: 1.3rem; margin-bottom: 4px;">📚</div>
                        <div style="font-weight: 700; color: #183B32; font-size: 0.9rem;">4. Collect</div>
                        <div style="font-size: 0.78rem; color: #4E5C53; margin-top: 4px;">Preserve in your personal Vivédex and annotated field journal.</div>
                    </div>
                    <div style="background: #FFFFFF; border: 1px solid #E3DDD0; border-radius: 8px; padding: 12px 14px;">
                        <div style="font-size: 1.3rem; margin-bottom: 4px;">🕸️</div>
                        <div style="font-weight: 700; color: #183B32; font-size: 0.9rem;">5. Learn</div>
                        <div style="font-size: 0.78rem; color: #4E5C53; margin-top: 4px;">Explore taxonomic hierarchies, synchronic families, and traits.</div>
                    </div>
                    <div style="background: #FFFFFF; border: 1px solid #E3DDD0; border-radius: 8px; padding: 12px 14px;">
                        <div style="font-size: 1.3rem; margin-bottom: 4px;">🏅</div>
                        <div style="font-weight: 700; color: #183B32; font-size: 0.9rem;">6. Contribute</div>
                        <div style="font-size: 0.78rem; color: #4E5C53; margin-top: 4px;">Earn research passport credentials and contribute verified datasets.</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Live Platform Metrics
        with db.connect() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM taxa;")
            total_taxa = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM observations;")
            total_obs = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM field_sites;")
            total_sites = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM expeditions WHERE status = 'IN_PROGRESS';")
            active_exp = c.fetchone()[0]

        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.markdown(
                f"""
                <div class="naturalist-metric">
                    <div class="metric-val">{total_taxa}</div>
                    <div class="metric-label">Taxa Cataloged</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_m2:
            st.markdown(
                f"""
                <div class="naturalist-metric">
                    <div class="metric-val">{total_obs}</div>
                    <div class="metric-label">Field Observations</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_m3:
            st.markdown(
                f"""
                <div class="naturalist-metric">
                    <div class="metric-val">{total_sites}</div>
                    <div class="metric-label">Monitored Field Sites</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_m4:
            st.markdown(
                f"""
                <div class="naturalist-metric">
                    <div class="metric-val">{active_exp}</div>
                    <div class="metric-label">Active Expeditions</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

        # Onboarding Access Box (Prominent Login / Register)
        col_onboard, col_preview = st.columns([1, 1], gap="large")

        with col_onboard:
            st.markdown("### Naturalist Sign-In & Registration")
            tab_landing_login, tab_landing_reg = st.tabs(["Sign In to Existing Account", "Create New Naturalist Account"])

            with tab_landing_login:
                with st.form("landing_login_form"):
                    user_inp = st.text_input("Username", key="landing_user_in")
                    pass_inp = st.text_input("Password", type="password", key="landing_pass_in")
                    submit_btn = st.form_submit_button("Sign In to Vivédex", width="stretch")
                    if submit_btn:
                        try:
                            user = auth_service.authenticate_user(user_inp, pass_inp)
                            st.session_state["current_user"] = user
                            st.session_state["active_user_id"] = user.id
                            st.success(f"Welcome back, {escape_text(user.display_name)}!")
                            st.rerun()
                        except AuthenticationError as e:
                            st.error(str(e))

            with tab_landing_reg:
                with st.form("landing_reg_form"):
                    reg_user = st.text_input("Choose Username", key="landing_reg_user")
                    reg_name = st.text_input("Full Naturalist Name", key="landing_reg_name")
                    reg_pass = st.text_input("Password (min 8 characters)", type="password", key="landing_reg_pass")
                    reg_btn = st.form_submit_button("Create Free Account", width="stretch")
                    if reg_btn:
                        try:
                            user = auth_service.register_user(
                                username=reg_user,
                                password=reg_pass,
                                display_name=reg_name,
                            )
                            st.session_state["current_user"] = user
                            st.session_state["active_user_id"] = user.id
                            st.success("Account created successfully! Welcome to Vivédex.")
                            st.rerun()
                        except AuthenticationError as e:
                            st.error(str(e))

        with col_preview:
            st.markdown("### Featured Field Sites & Expeditions")
            sites = eco_service.list_field_sites()[:2]
            for s in sites:
                st.markdown(
                    f"""
                    <div style="background: #FFFFFF; border: 1px solid #D8D1C2; border-radius: 8px; padding: 14px 16px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
                        <div style="display: flex; justify-content: space-between; align-items: baseline;">
                            <div style="font-weight: 700; color: #183B32; font-size: 1rem;">📍 {escape_text(s.name)}</div>
                            <span class="rank-pill">{escape_text(s.country)}</span>
                        </div>
                        <div style="font-size: 0.82rem; color: #8C5432; font-weight: 600; margin: 3px 0;">{escape_text(s.biome)} &bull; Elev. {s.elevation_m or 0}m</div>
                        <div style="font-size: 0.85rem; color: #4E5C53; line-height: 1.4;">{escape_text(s.description)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        return

    # -------------------------------------------------------------------------
    # 2. Authenticated Naturalist Expedition Hub
    # -------------------------------------------------------------------------
    gamification = achievement_service.get_user_gamification_stats(current_user.id)
    rank_title = get_naturalist_rank(gamification.level)

    # Hero Banner
    render_hero_banner(
        title=f"Expedition Hub &bull; {current_user.display_name}",
        subtitle=f"Naturalist Level {gamification.level} {rank_title} &bull; Total Contribution: {gamification.total_xp} XP &bull; All systems operational.",
    )

    # Quick Metrics Ribbon
    col_u1, col_u2, col_u3, col_u4 = st.columns(4)
    with col_u1:
        st.markdown(
            f"""
            <div class="naturalist-metric">
                <div class="metric-val">{gamification.total_observations}</div>
                <div class="metric-label">My Observations</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_u2:
        st.markdown(
            f"""
            <div class="naturalist-metric">
                <div class="metric-val">{gamification.species_collected}</div>
                <div class="metric-label">Taxa in My Dex</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_u3:
        st.markdown(
            f"""
            <div class="naturalist-metric">
                <div class="metric-val">{gamification.families_count}</div>
                <div class="metric-label">Families Documented</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_u4:
        st.markdown(
            f"""
            <div class="naturalist-metric">
                <div class="metric-val">{gamification.badges_unlocked_count}</div>
                <div class="metric-label">Badges Unlocked</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)

    # Quests & Habits Showcase (Habitica-inspired)
    st.markdown("### Active Field Habits & Expedition Quests")
    user_quests = quest_service.get_user_quests(current_user.id)

    col_q1, col_q2 = st.columns([1, 1], gap="medium")
    for i, q in enumerate(user_quests[:4]):
        target_col = col_q1 if i % 2 == 0 else col_q2
        with target_col:
            pct = min(100, int((q.current_progress / max(1, q.target_count)) * 100))
            type_class = (
                "quest-habit" if q.quest_type == "HABIT"
                else "quest-recurring" if q.quest_type == "RECURRING_GOAL"
                else "quest-milestone"
            )
            type_label = (
                "Field Habit" if q.quest_type == "HABIT"
                else "Weekly Goal" if q.quest_type == "RECURRING_GOAL"
                else "Milestone Quest"
            )

            st.markdown(
                f"""
                <div class="quest-box {type_class}">
                    <div style="display: flex; justify-content: space-between; align-items: baseline;">
                        <div style="font-weight: 700; color: #183B32; font-size: 0.98rem;">{q.icon} {escape_text(q.title)}</div>
                        <span style="font-size: 0.72rem; font-weight: 700; color: #8C5432; background: #FAF5EB; padding: 2px 7px; border-radius: 10px; border: 1px solid #EADBBE;">{type_label} &bull; +{q.xp_reward} XP</span>
                    </div>
                    <div style="font-size: 0.84rem; color: #4E5C53; margin: 4px 0 8px 0;">{escape_text(q.description)}</div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.76rem; color: #183B32; font-weight: 600; margin-bottom: 3px;">
                        <span>Progress: {q.current_progress} / {q.target_count}</span>
                        <span>{pct}%</span>
                    </div>
                    <div style="background: #E8E3D8; border-radius: 4px; height: 6px; overflow: hidden;">
                        <div style="background: #183B32; width: {pct}%; height: 100%;"></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if q.is_completed and not q.claimed_at:
                if st.button(f"Claim +{q.xp_reward} XP: {q.title}", key=f"claim_home_{q.quest_id}"):
                    ok, xp_val, msg = quest_service.claim_quest_reward(current_user.id, q.quest_id)
                    if ok:
                        st.success(msg)
                        st.rerun()

    # Recent Field Encounters
    st.markdown("### Recent Field Encounters")
    encounters = collection_service.list_user_observations(current_user.id, limit=3)
    if not encounters:
        st.info("No field encounters recorded yet. Start by identifying an organism with AI vision.")
    else:
        for obs in encounters:
            st.markdown(
                f"""
                <div class="specimen-card">
                    <div style="display: flex; justify-content: space-between; align-items: baseline;">
                        <span class="latin-binomial" style="font-size: 1.15rem;">{escape_text(obs.candidate_scientific_name)}</span>
                        <span class="status-pill-accepted">{escape_text(obs.moderation_status)}</span>
                    </div>
                    <div style="font-size: 0.85rem; color: #4E5C53; margin-top: 4px;">
                        Observed on {escape_text(obs.observation_timestamp[:10])} &bull; {escape_text(obs.coarse_location or "Field Location")}
                    </div>
                    <div style="font-size: 0.85rem; color: #1E2621; margin-top: 6px; font-style: italic;">
                        "{escape_text(obs.field_notes or "No notes entered.")}"
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
