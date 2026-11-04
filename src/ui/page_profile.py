"""Researcher Profile view: Contributor identity, research background, and attribution.

Presents unique Contributor ID, unverified external ORCID identifier, biography,
and aggregated natural history metrics.
"""

from __future__ import annotations

import streamlit as st

from src.achievements import AchievementService
from src.auth import AuthenticatedUser
from src.collection_service import CollectionService
from src.ui.common import inject_custom_styles, render_security_notice
from src.ui.theme import escape_text, get_naturalist_rank, render_hero_banner, safe_url


def render_profile_page(
    collection_service: CollectionService,
    achievement_service: AchievementService,
) -> None:
    """Render the reconstructed naturalist researcher identity view."""
    inject_custom_styles()
    render_security_notice()

    current_user: AuthenticatedUser | None = st.session_state.get("current_user")

    # Banner
    render_hero_banner(
        title="👤 Naturalist & Researcher Profile",
        subtitle="Persistent contributor identity, scientific affiliations, field documentation summary, and verified attribution.",
    )

    if current_user is None:
        st.info("👋 Please log in or register via the sidebar to access and edit your researcher profile.")
        return

    profile = collection_service.get_user_profile(current_user.id)
    if not profile:
        st.error("Profile record could not be loaded from database.")
        return

    rank_title = get_naturalist_rank(profile.level)
    esc_display_name = escape_text(profile.display_name)
    esc_username = escape_text(profile.username)
    esc_vivedex_id = escape_text(profile.vivedex_id)
    esc_join_date = escape_text(profile.join_date[:10])
    esc_role = escape_text(profile.role.upper())
    esc_bio = escape_text(profile.bio) if profile.bio else ""
    esc_rank_title = escape_text(rank_title)
    bio_html = (
        f'<div style="margin-top: 14px; font-size: 0.95rem; color: #333; line-height: 1.5; background: #fdfaf4; padding: 12px; border-radius: 6px; border: 1px solid #efe8db;">{esc_bio}</div>'
        if esc_bio
        else ""
    )

    # Main Contributor Card
    st.markdown(
        f"""
        <div class="specimen-card" style="border-left: 5px solid #183B32; margin-bottom: 1.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap;">
                <div>
                    <div style="font-size: 0.78rem; text-transform: uppercase; color: #777E73; font-weight: 700;">Verified Platform Contributor</div>
                    <h2 style="margin: 0; font-size: 2rem; color: #183B32;">{esc_display_name}</h2>
                    <div style="font-size: 0.95rem; color: #666; margin-top: 2px;">
                        @{esc_username} &bull; Contributor ID: <code style="color: #183B32; font-weight: 700;">{esc_vivedex_id}</code>
                    </div>
                    <div style="font-size: 0.8rem; color: #777E73; margin-top: 6px;">
                        Member since: <strong>{esc_join_date}</strong> &bull; System Role: <span class="rank-pill">{esc_role}</span>
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="font-family: 'Cinzel', serif; font-size: 1.25rem; font-weight: 700; color: #183B32;">
                        Level {int(profile.level)} {esc_rank_title}
                    </div>
                    <div style="font-size: 0.85rem; color: #A66B48; font-weight: 600;">{int(profile.total_xp)} Total XP</div>
                </div>
            </div>
            {bio_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 4 Key Metrics
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"""
            <div class="naturalist-metric">
                <div class="metric-val">{profile.observation_count}</div>
                <div class="metric-label">Field Sightings</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="naturalist-metric">
                <div class="metric-val">{profile.distinct_taxa_count}</div>
                <div class="metric-label">Cataloged Taxa</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""
            <div class="naturalist-metric">
                <div class="metric-val">{profile.family_count}</div>
                <div class="metric-label">Families Documented</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f"""
            <div class="naturalist-metric">
                <div class="metric-val">{profile.badge_count}</div>
                <div class="metric-label">Earned Badges</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Profile Edit Form & External Identifier
    col_edit, col_orcid = st.columns([11, 9])

    with col_edit:
        st.subheader("📝 Edit Contributor Details")
        with st.form("edit_profile_form"):
            disp_name = st.text_input("Public Display Name:", value=profile.display_name)
            bio_input = st.text_area(
                "Biography & Field Interests:",
                value=profile.bio,
                placeholder="Share your natural history focus, local biomes, or taxonomic specialties...",
            )
            orcid_input = st.text_input(
                "External Researcher Identifier (ORCID URL):",
                value=profile.external_orcid_url,
                placeholder="https://orcid.org/0000-0002-1825-0097",
                help="Self-reported persistent researcher link. Note: ORCID OAuth is not implemented in this prototype.",
            )
            save_profile = st.form_submit_button("💾 Save Profile Changes", type="primary")

            if save_profile:
                try:
                    collection_service.update_user_bio(
                        user_id=current_user.id,
                        display_name=disp_name,
                        bio=bio_input,
                        external_orcid_url=orcid_input,
                    )
                    st.session_state["current_user"] = AuthenticatedUser(
                        id=current_user.id,
                        username=current_user.username,
                        role=current_user.role,
                        display_name=disp_name.strip() or current_user.username,
                        vivedex_id=current_user.vivedex_id,
                        is_active=current_user.is_active,
                    )
                    st.success("Profile credentials updated successfully!")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

    with col_orcid:
        st.subheader("🔗 External Attribution")
        st.markdown(
            """
            <div style="background: #faf7f0; border: 1px solid #e3ddd0; border-radius: 8px; padding: 14px; font-size: 0.85rem; color: #555;">
                <strong style="color: #183B32;">Academic & Professional Citation</strong><br/>
                Vivédex supports linking your personal ORCID researcher profile to attribute citizen-science observations to your formal record.
                <div style="margin-top: 8px; font-size: 0.78rem; color: #A66B48; font-weight: 600;">
                    ⚠️ Note: External ORCID links are currently self-reported by naturalists and not verified via ORCID OAuth.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if profile.external_orcid_url:
            clean_href = safe_url(profile.external_orcid_url)
            esc_display_url = escape_text(profile.external_orcid_url)
            if clean_href:
                st.write("")
                st.markdown(
                    f"""
                    <div style="background: #ffffff; border: 1px solid #c8d8be; border-radius: 6px; padding: 10px 14px;">
                        <div style="font-size: 0.75rem; color: #718568; font-weight: 700; text-transform: uppercase;">External Link (Self-Reported)</div>
                        <a href="{clean_href}" target="_blank" rel="noopener noreferrer" style="font-weight: 600; color: #183B32; text-decoration: none;">
                            🌐 {esc_display_url}
                        </a>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # Earned Badges Showcase
    st.markdown("---")
    st.subheader(f"🎖️ Milestone Badges ({profile.badge_count})")
    badges = achievement_service.get_user_badges(current_user.id)
    if badges:
        cols = st.columns(3)
        for idx, b in enumerate(badges):
            with cols[idx % 3]:
                esc_b_name = escape_text(b.name)
                esc_b_desc = escape_text(b.description)
                esc_b_icon = escape_text(b.icon)
                st.markdown(
                    f"""
                    <div class="specimen-card" style="padding: 12px; margin-bottom: 8px; display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 1.8rem;">{esc_b_icon}</span>
                        <div>
                            <div style="font-size: 0.95rem; font-weight: 700; color: #183B32;">{esc_b_name}</div>
                            <div style="font-size: 0.78rem; color: #777E73;">{esc_b_desc}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    else:
        st.caption("No milestone badges earned yet.")
