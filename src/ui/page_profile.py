"""Researcher Profile page for Vivédex.

Presents contributor identity, Vivédex ID, unverified ORCID identifier, bio, and stats.
Prevents role elevation from the profile interface.
"""

from __future__ import annotations

import streamlit as st

from src.achievements import AchievementService
from src.auth import AuthenticatedUser
from src.collection_service import CollectionService
from src.ui.common import inject_custom_styles, render_security_notice


def render_profile_page(
    collection_service: CollectionService,
    achievement_service: AchievementService,
) -> None:
    """Render the researcher profile view."""
    inject_custom_styles()
    render_security_notice()

    current_user: AuthenticatedUser | None = st.session_state.get("current_user")

    st.markdown('<div class="main-header">👤 Researcher Profile</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Persistent contributor credentials, researcher links, and field statistics.</div>',
        unsafe_allow_html=True,
    )

    if current_user is None:
        st.info("Please log in or register via the sidebar to view and edit your profile.")
        return

    profile = collection_service.get_user_profile(current_user.id)
    if not profile:
        st.error("Profile not found.")
        return

    # Profile Card
    st.markdown(
        f"""
        <div class="card-box">
            <h2 style="margin: 0; color: #1b4332;">{profile.display_name}</h2>
            <p style="margin: 4px 0; color: #666;">@{profile.username} | Contributor ID: <code>{profile.vivedex_id}</code></p>
            <p style="margin: 4px 0;"><span class="status-pill">ROLE: {profile.role.upper()}</span> | Member since: {profile.join_date[:10]}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 4 Key Metrics
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Observations", profile.observation_count)
    with c2:
        st.metric("Collected Taxa", profile.distinct_taxa_count)
    with c3:
        st.metric("Families Documented", profile.family_count)
    with c4:
        st.metric(f"Level {profile.level}", f"{profile.total_xp} XP")

    st.markdown("---")
    st.subheader("📝 Edit Profile Details")

    with st.form("edit_profile_form"):
        new_disp_name = st.text_input("Display Name:", value=profile.display_name)
        new_bio = st.text_area("Biography & Research Interests:", value=profile.bio)

        st.markdown("**External Researcher Identifier**")
        st.caption("Optional ORCID identifier or profile URL. *Note: External identifiers are self-reported and not verified by Vivédex.*")
        new_orcid = st.text_input(
            "ORCID URL (e.g. https://orcid.org/0000-0002-1825-0097):",
            value=profile.external_orcid_url,
            placeholder="https://orcid.org/0000-XXXX-XXXX-XXXX",
        )

        save_profile_btn = st.form_submit_button("💾 Save Profile Changes", type="primary")

        if save_profile_btn:
            collection_service.update_user_bio(
                user_id=current_user.id,
                display_name=new_disp_name,
                bio=new_bio,
                external_orcid_url=new_orcid,
            )
            # Update session state display name if changed
            st.session_state["current_user"] = AuthenticatedUser(
                id=current_user.id,
                username=current_user.username,
                role=current_user.role,
                display_name=new_disp_name.strip() or current_user.username,
                vivedex_id=current_user.vivedex_id,
                is_active=current_user.is_active,
            )
            st.success("Profile updated successfully!")
            st.rerun()

    if profile.external_orcid_url:
        st.markdown("---")
        st.markdown(f"🔗 **External Researcher Link (Unverified):** [{profile.external_orcid_url}]({profile.external_orcid_url})")

    # Earned Badges
    st.markdown("---")
    st.subheader(f"🏅 Earned Badges ({profile.badge_count})")
    badges = achievement_service.get_user_badges(current_user.id)
    if badges:
        cols = st.columns(3)
        for idx, b in enumerate(badges):
            with cols[idx % 3]:
                st.markdown(
                    f"""
                    <div style="border: 1px solid #e2e8f0; border-radius: 6px; padding: 10px; margin-bottom: 8px;">
                        <span style="font-size: 1.5rem;">{b.icon}</span> <strong>{b.name}</strong><br/>
                        <span style="font-size: 0.8rem; color: #666;">{b.description}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    else:
        st.caption("No badges earned yet.")
