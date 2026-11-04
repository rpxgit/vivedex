"""Quests and field habits interface for Vivédex.

Inspired by Habitica, provides constructive, non-punitive habits, recurring goals,
and milestone quests to motivate scientific fieldwork and biodiversity documentation.
"""

from __future__ import annotations

import streamlit as st

from src.auth import AuthenticatedUser
from src.database import Database
from src.quest_service import QuestService
from src.ui.common import inject_custom_styles, render_breadcrumbs, render_security_notice
from src.ui.theme import escape_text, render_hero_banner


def render_quests_page(db: Database) -> None:
    """Render the Quests, Habits, and Recurring Goals module."""
    inject_custom_styles()
    render_security_notice()
    render_breadcrumbs([("Expedition Hub", "home"), ("Quests & Habits", None)])

    current_user: AuthenticatedUser | None = st.session_state.get("current_user")
    quest_service = QuestService(db)

    render_hero_banner(
        title="Field Habits & Quests",
        subtitle="Meaningful, non-punitive progression inspired by Habitica. Build lasting fieldwork habits, achieve weekly goals, and complete naturalist milestones.",
    )

    if current_user is None:
        st.info("Log in or register via the sidebar to track your field habits, complete quests, and claim XP rewards.")
        all_quests = quest_service.list_quests()
        st.markdown(f"### Available Fieldwork Quests ({len(all_quests)})")
        for q in all_quests:
            st.markdown(
                f"""
                <div class="quest-box">
                    <div style="font-weight: 700; color: #183B32; font-size: 1rem;">{q.icon} {escape_text(q.title)} (+{q.xp_reward} XP)</div>
                    <div style="font-size: 0.85rem; color: #4E5C53; margin-top: 4px;">{escape_text(q.description)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        return

    # User quests with live progress
    user_quests = quest_service.get_user_quests(current_user.id)

    tab_habits, tab_recurring, tab_milestones = st.tabs([
        "🌱 Daily Field Habits",
        "⚡ Weekly Recurring Goals",
        "🏆 Milestone Quests",
    ])

    with tab_habits:
        habits = [q for q in user_quests if q.quest_type == "HABIT"]
        st.markdown(
            """
            <div style="font-size: 0.9rem; color: #4E5C53; margin-bottom: 1rem;">
                Field habits encourage consistent documentation. These habits are <strong>non-punitive</strong>: missing a day never resets your experience.
            </div>
            """,
            unsafe_allow_html=True,
        )

        for h in habits:
            pct = min(100, int((h.current_progress / max(1, h.target_count)) * 100))
            col_h_info, col_h_act = st.columns([3, 1.2])

            with col_h_info:
                st.markdown(
                    f"""
                    <div class="quest-box quest-habit">
                        <div style="display: flex; justify-content: space-between; align-items: baseline;">
                            <div style="font-weight: 700; color: #183B32; font-size: 1.05rem;">
                                {h.icon} {escape_text(h.title)}
                            </div>
                            <span style="font-size: 0.74rem; font-weight: 700; color: #183B32; background: #E6F4EA; padding: 2px 8px; border-radius: 10px; border: 1px solid #CEEAD6;">
                                +{h.xp_reward} XP
                            </span>
                        </div>
                        <div style="font-size: 0.85rem; color: #4E5C53; margin: 4px 0 8px 0;">
                            {escape_text(h.description)}
                        </div>
                        <div style="display: flex; justify-content: space-between; font-size: 0.78rem; color: #183B32; font-weight: 600; margin-bottom: 3px;">
                            <span>Logged Actions: {h.current_progress}</span>
                            <span>{pct}%</span>
                        </div>
                        <div style="background: #E8E3D8; border-radius: 4px; height: 6px; overflow: hidden;">
                            <div style="background: #183B32; width: {pct}%; height: 100%;"></div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with col_h_act:
                st.write("")
                if st.button(f"➕ Log Daily Action", key=f"habit_btn_{h.quest_id}", width="stretch"):
                    ok = quest_service.log_habit_action(current_user.id, h.quest_id)
                    if ok:
                        st.success(f"Logged habit: {h.title}!")
                        st.rerun()

                if h.is_completed and not h.claimed_at:
                    if st.button(f"🏅 Claim +{h.xp_reward} XP", key=f"claim_h_{h.quest_id}", width="stretch"):
                        ok, xp_val, msg = quest_service.claim_quest_reward(current_user.id, h.quest_id)
                        if ok:
                            st.success(msg)
                            st.rerun()
                elif h.claimed_at:
                    st.caption("✅ Reward Claimed")

    with tab_recurring:
        recurring = [q for q in user_quests if q.quest_type == "RECURRING_GOAL"]
        st.markdown(
            """
            <div style="font-size: 0.9rem; color: #4E5C53; margin-bottom: 1rem;">
                Recurring goals reward broad sampling, BioBlitzes, and multi-family exploration across ongoing expeditions.
            </div>
            """,
            unsafe_allow_html=True,
        )

        for r in recurring:
            pct = min(100, int((r.current_progress / max(1, r.target_count)) * 100))
            col_r_info, col_r_act = st.columns([3, 1.2])

            with col_r_info:
                st.markdown(
                    f"""
                    <div class="quest-box quest-recurring">
                        <div style="display: flex; justify-content: space-between; align-items: baseline;">
                            <div style="font-weight: 700; color: #183B32; font-size: 1.05rem;">
                                {r.icon} {escape_text(r.title)}
                            </div>
                            <span style="font-size: 0.74rem; font-weight: 700; color: #8C5432; background: #FAF5EB; padding: 2px 8px; border-radius: 10px; border: 1px solid #EADBBE;">
                                +{r.xp_reward} XP
                            </span>
                        </div>
                        <div style="font-size: 0.85rem; color: #4E5C53; margin: 4px 0 8px 0;">
                            {escape_text(r.description)}
                        </div>
                        <div style="display: flex; justify-content: space-between; font-size: 0.78rem; color: #183B32; font-weight: 600; margin-bottom: 3px;">
                            <span>Progress: {r.current_progress} / {r.target_count}</span>
                            <span>{pct}%</span>
                        </div>
                        <div style="background: #E8E3D8; border-radius: 4px; height: 6px; overflow: hidden;">
                            <div style="background: #8C5432; width: {pct}%; height: 100%;"></div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with col_r_act:
                st.write("")
                if r.is_completed and not r.claimed_at:
                    if st.button(f"🏅 Claim +{r.xp_reward} XP", key=f"claim_r_{r.quest_id}", width="stretch"):
                        ok, xp_val, msg = quest_service.claim_quest_reward(current_user.id, r.quest_id)
                        if ok:
                            st.success(msg)
                            st.rerun()
                elif r.claimed_at:
                    st.caption("✅ Reward Claimed")
                else:
                    st.caption(f"{r.target_count - r.current_progress} remaining")

    with tab_milestones:
        milestones = [q for q in user_quests if q.quest_type == "MILESTONE"]
        st.markdown(
            """
            <div style="font-size: 0.9rem; color: #4E5C53; margin-bottom: 1rem;">
                Permanent career milestones marking significant field achievements, catalog growth, and institutional collaboration.
            </div>
            """,
            unsafe_allow_html=True,
        )

        for m in milestones:
            pct = min(100, int((m.current_progress / max(1, m.target_count)) * 100))
            col_m_info, col_m_act = st.columns([3, 1.2])

            with col_m_info:
                st.markdown(
                    f"""
                    <div class="quest-box quest-milestone">
                        <div style="display: flex; justify-content: space-between; align-items: baseline;">
                            <div style="font-weight: 700; color: #183B32; font-size: 1.05rem;">
                                {m.icon} {escape_text(m.title)}
                            </div>
                            <span style="font-size: 0.74rem; font-weight: 700; color: #A2782A; background: #FDF9EE; padding: 2px 8px; border-radius: 10px; border: 1px solid #F2DC9E;">
                                +{m.xp_reward} XP
                            </span>
                        </div>
                        <div style="font-size: 0.85rem; color: #4E5C53; margin: 4px 0 8px 0;">
                            {escape_text(m.description)}
                        </div>
                        <div style="display: flex; justify-content: space-between; font-size: 0.78rem; color: #183B32; font-weight: 600; margin-bottom: 3px;">
                            <span>Progress: {m.current_progress} / {m.target_count}</span>
                            <span>{pct}%</span>
                        </div>
                        <div style="background: #E8E3D8; border-radius: 4px; height: 6px; overflow: hidden;">
                            <div style="background: #A2782A; width: {pct}%; height: 100%;"></div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with col_m_act:
                st.write("")
                if m.is_completed and not m.claimed_at:
                    if st.button(f"🏅 Claim +{m.xp_reward} XP", key=f"claim_m_{m.quest_id}", width="stretch"):
                        ok, xp_val, msg = quest_service.claim_quest_reward(current_user.id, m.quest_id)
                        if ok:
                            st.success(msg)
                            st.rerun()
                elif m.claimed_at:
                    st.caption("✅ Milestone Completed")
                else:
                    st.caption(f"{m.target_count - m.current_progress} remaining")

