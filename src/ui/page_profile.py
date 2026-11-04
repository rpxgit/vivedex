"""Researcher Passport view for Vivédex.

Inspired by ORCID, provides persistent contributor identity, verified affiliations,
research interests, privacy settings, and scholarly/field research outputs
with transparent provenance states.
"""

from __future__ import annotations

import streamlit as st

from src.achievements import AchievementService
from src.auth import AuthenticatedUser
from src.collection_service import CollectionService
from src.database import Database
from src.passport_service import PassportService
from src.ui.common import inject_custom_styles, render_breadcrumbs, render_security_notice
from src.ui.theme import escape_text, get_naturalist_rank, render_hero_banner, render_provenance_badge, safe_url


def render_profile_page(
    collection_service: CollectionService,
    achievement_service: AchievementService,
) -> None:
    """Render the full Researcher Passport view."""
    inject_custom_styles()
    render_security_notice()
    render_breadcrumbs([("Expedition Hub", "home"), ("Researcher Passport", None)])

    current_user: AuthenticatedUser | None = st.session_state.get("current_user")
    db: Database = st.session_state.get("db")
    passport_service = PassportService(db)

    render_hero_banner(
        title="Researcher Passport",
        subtitle="Persistent contributor identity, scientific affiliations, field documentation credentials, and research outputs inspired by ORCID.",
    )

    if current_user is None:
        st.info("👋 Please log in or register via the sidebar to access and manage your researcher passport.")
        return

    passport = passport_service.get_passport(current_user.id)
    if not passport:
        st.error("Researcher passport record could not be loaded from database.")
        return

    rank_title = get_naturalist_rank(achievement_service.get_user_gamification_stats(current_user.id).level)
    esc_display_name = escape_text(passport.display_name)
    esc_username = escape_text(passport.username)
    esc_vivedex_id = escape_text(passport.vivedex_id)
    esc_join_date = escape_text(passport.created_at[:10])
    esc_role = escape_text(current_user.role.upper())
    esc_bio = escape_text(passport.bio) if passport.bio else ""
    esc_rank_title = escape_text(rank_title)

    # Affiliations & interests pills
    affil_badges = "".join(
        f'<span class="rank-pill" style="margin-right: 6px; margin-bottom: 4px;">🏛️ {escape_text(a)}</span>'
        for a in passport.affiliations
    ) or '<span style="font-size: 0.82rem; color: #777;">No affiliations listed</span>'

    interest_badges = "".join(
        f'<span style="display: inline-block; background: #FAF5EB; color: #8C5432; border: 1px solid #EADBBE; font-size: 0.76rem; font-weight: 600; padding: 2px 8px; border-radius: 10px; margin-right: 6px; margin-bottom: 4px;">🌿 {escape_text(i)}</span>'
        for i in passport.research_interests
    ) or '<span style="font-size: 0.82rem; color: #777;">No research interests listed</span>'

    privacy_label = '<span class="status-pill-accepted">Public Passport</span>' if passport.is_public else '<span class="status-pill-pending">Private Passport</span>'

    # Grand Researcher Passport Card
    st.markdown(
        f"""
        <div class="specimen-card" style="border-left: 6px solid #183B32; margin-bottom: 1.5rem; background: #FCFAF4;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px;">
                <div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-size: 0.76rem; text-transform: uppercase; color: #4E5C53; font-weight: 700;">Verified Platform Contributor</span>
                        {privacy_label}
                    </div>
                    <h2 style="margin: 4px 0 2px 0; font-size: 2.1rem; color: #183B32;">{esc_display_name}</h2>
                    <div style="font-size: 0.92rem; color: #4E5C53;">
                        @{esc_username} &bull; Persistent Contributor ID: <code style="color: #183B32; font-weight: 700; background: #EFE9DC; padding: 2px 6px; border-radius: 4px;">{esc_vivedex_id}</code>
                    </div>
                    <div style="font-size: 0.82rem; color: #4E5C53; margin-top: 6px;">
                        Accredited since: <strong>{esc_join_date}</strong> &bull; Authorization: <span class="rank-pill">{esc_role}</span>
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="font-family: 'Cinzel', serif; font-size: 1.3rem; font-weight: 700; color: #183B32;">
                        {esc_rank_title}
                    </div>
                    <div style="font-size: 0.85rem; color: #8C5432; font-weight: 600;">{passport.total_xp} Total Field XP</div>
                </div>
            </div>

            <div style="margin-top: 14px; padding-top: 12px; border-top: 1px solid #E3DDD0;">
                <div style="font-size: 0.78rem; text-transform: uppercase; color: #4E5C53; font-weight: 700; margin-bottom: 4px;">Institutional Affiliations</div>
                <div>{affil_badges}</div>
            </div>

            <div style="margin-top: 10px;">
                <div style="font-size: 0.78rem; text-transform: uppercase; color: #4E5C53; font-weight: 700; margin-bottom: 4px;">Specialization & Research Interests</div>
                <div>{interest_badges}</div>
            </div>

            {f'<div style="margin-top: 14px; font-size: 0.92rem; color: #1E2621; line-height: 1.5; background: #FFFFFF; padding: 12px 14px; border-radius: 6px; border: 1px solid #E3DDD0;">{esc_bio}</div>' if esc_bio else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 4 Key Quantitative Metrics
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.markdown(
            f"""
            <div class="naturalist-metric">
                <div class="metric-val">{passport.total_observations}</div>
                <div class="metric-label">Field Observations</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_m2:
        st.markdown(
            f"""
            <div class="naturalist-metric">
                <div class="metric-val">{passport.species_collected}</div>
                <div class="metric-label">Cataloged Taxa</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_m3:
        st.markdown(
            f"""
            <div class="naturalist-metric">
                <div class="metric-val">{passport.families_documented}</div>
                <div class="metric-label">Families Documented</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_m4:
        st.markdown(
            f"""
            <div class="naturalist-metric">
                <div class="metric-val">{len(passport.outputs)}</div>
                <div class="metric-label">Research Outputs</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # Research Outputs Section (ORCID-inspired)
    # -------------------------------------------------------------------------
    st.markdown("### 📚 Research Outputs & Field Publications")
    st.markdown(
        """
        <div style="font-size: 0.88rem; color: #4E5C53; margin-bottom: 1rem;">
            Document datasets, checklists, observation catalogs, and field reports. Outputs carry explicit <strong>provenance states</strong>:
            <code>SELF_REPORTED</code>, <code>SOURCE_LINKED</code>, <code>PLATFORM_REVIEWED</code>, or <code>EXTERNALLY_VERIFIED</code>.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not passport.outputs:
        st.info("No research outputs recorded yet. Add your first publication, dataset, or field report below.")
    else:
        for out in passport.outputs:
            prov_pill = render_provenance_badge(out.provenance_state)
            safe_link = safe_url(out.doi_or_url)
            link_html = f'<a href="{safe_link}" target="_blank" style="color: #183B32; font-weight: 600; text-decoration: underline;">{escape_text(out.doi_or_url)}</a>' if safe_link else escape_text(out.doi_or_url)

            col_out_body, col_out_del = st.columns([5, 1])
            with col_out_body:
                st.markdown(
                    f"""
                    <div class="specimen-card" style="padding: 1rem 1.2rem; margin-bottom: 10px;">
                        <div style="display: flex; justify-content: space-between; align-items: baseline;">
                            <div style="font-weight: 700; color: #183B32; font-size: 1.05rem;">
                                📄 {escape_text(out.title)}
                            </div>
                            <div>{prov_pill}</div>
                        </div>
                        <div style="font-size: 0.82rem; color: #8C5432; font-weight: 600; margin: 3px 0;">
                            Type: {escape_text(out.output_type.replace('_', ' '))} &bull; Added: {escape_text(out.created_at[:10])}
                        </div>
                        {f'<div style="font-size: 0.84rem; color: #4E5C53; margin: 4px 0;">URI / DOI: {link_html}</div>' if out.doi_or_url else ''}
                        {f'<div style="font-size: 0.84rem; color: #1E2621; font-style: italic; margin-top: 4px;">"{escape_text(out.citation)}"</div>' if out.citation else ''}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with col_out_del:
                st.write("")
                if st.button("🗑️ Delete", key=f"del_out_{out.id}", width="stretch"):
                    passport_service.delete_research_output(current_user.id, out.id)
                    st.success("Output removed.")
                    st.rerun()

    # Form to add new research output
    with st.expander("➕ Add Research Output (Dataset, Field Report, Publication)"):
        with st.form("add_output_form"):
            o_title = st.text_input("Title of Research Output")
            o_type = st.selectbox(
                "Output Classification",
                ["DATASET", "FIELD_REPORT", "SPECIES_CHECKLIST", "PUBLICATION", "OBSERVATION_CATALOG"],
            )
            o_uri = st.text_input("DOI or Source URL (e.g. https://doi.org/... or https://gbif.org/...)")
            o_cite = st.text_area("Citation / Description (Author, Year, Venue, or Context)")
            sub_output = st.form_submit_button("Record Research Output", width="stretch")
            if sub_output:
                if not o_title.strip():
                    st.error("Output title is required.")
                else:
                    passport_service.add_research_output(
                        user_id=current_user.id,
                        title=o_title,
                        output_type=o_type,
                        doi_or_url=o_uri,
                        citation=o_cite,
                    )
                    st.success(f"Recorded '{o_title}' in your Researcher Passport!")
                    st.rerun()

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # Passport Profile & Attribution Settings
    # -------------------------------------------------------------------------
    col_edit_passport, col_orcid_box = st.columns([1.2, 1], gap="large")

    with col_edit_passport:
        st.markdown("### 📝 Edit Passport Credentials")
        with st.form("edit_passport_form"):
            disp_name_val = st.text_input("Public Display Name", value=passport.display_name)
            bio_val = st.text_area(
                "Biography & Field Background",
                value=passport.bio,
                placeholder="Share your natural history focus, local biomes, or taxonomic specialties...",
            )
            affils_str = st.text_input(
                "Institutional Affiliations (comma-separated)",
                value=", ".join(passport.affiliations),
                help="e.g. Royal Botanic Gardens Kew, University of Oxford, STRI",
            )
            interests_str = st.text_input(
                "Research Interests (comma-separated)",
                value=", ".join(passport.research_interests),
                help="e.g. Orchidaceae, Canopy Ecology, Lichenology, Restoration",
            )
            is_pub_val = st.checkbox("Make Passport Publicly Searchable", value=passport.is_public)
            orcid_val = st.text_input(
                "External ORCID Identifier URL",
                value=passport.external_orcid_url,
                placeholder="https://orcid.org/0000-0002-1825-0097",
                help="Persistent researcher identifier. Format: https://orcid.org/0000-000X-XXXX-XXXX",
            )

            save_passport_btn = st.form_submit_button("💾 Save Passport Details", width="stretch")
            if save_passport_btn:
                try:
                    # Validate ORCID URL format if provided (SEC-08)
                    if orcid_val.strip():
                        import re
                        if not re.match(r"^https://orcid\.org/\d{4}-\d{4}-\d{4}-\d{3}[\dX]$", orcid_val.strip()):
                            raise ValueError("ORCID URL must match format: https://orcid.org/0000-0000-0000-0000")

                    affil_list = [a.strip() for a in affils_str.split(",") if a.strip()]
                    interest_list = [i.strip() for i in interests_str.split(",") if i.strip()]

                    passport_service.update_passport_profile(
                        user_id=current_user.id,
                        display_name=disp_name_val.strip() or current_user.username,
                        bio=bio_val.strip(),
                        external_orcid_url=orcid_val.strip(),
                        affiliations=affil_list,
                        research_interests=interest_list,
                        is_public=is_pub_val,
                    )
                    st.success("Researcher Passport updated successfully!")
                    st.rerun()
                except ValueError as err:
                    st.error(str(err))

    with col_orcid_box:
        st.markdown("### 🔗 ORCID Persistent Attribution")
        st.markdown(
            """
            <div style="background: #FCFAF4; border: 1px solid #D8D1C2; border-radius: 8px; padding: 16px; font-size: 0.88rem; color: #4E5C53; line-height: 1.5;">
                <div style="font-weight: 700; color: #183B32; font-size: 0.95rem; margin-bottom: 6px;">Academic Citation & Data Attribution</div>
                Vivédex supports linking your verified ORCID researcher identifier to attribute observations, checklists, and taxonomic verifications.
                <div style="margin-top: 10px; font-size: 0.78rem; color: #8C5432; font-weight: 600; background: #FAF5EB; padding: 8px 10px; border-radius: 6px; border: 1px solid #EADBBE;">
                    ⚠️ Note: External ORCID links are currently self-reported. Official OAuth sign-in will be added in future platform releases.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if passport.external_orcid_url:
            clean_href = safe_url(passport.external_orcid_url)
            esc_display_url = escape_text(passport.external_orcid_url)
            if clean_href:
                st.write("")
                st.markdown(
                    f"""
                    <div style="background: #FFFFFF; border: 1px solid #C4D6BD; border-radius: 8px; padding: 12px 14px;">
                        <div style="font-size: 0.74rem; color: #183B32; font-weight: 700; text-transform: uppercase;">Linked Identifier (Self-Reported)</div>
                        <a href="{clean_href}" target="_blank" rel="noopener noreferrer" style="font-weight: 600; color: #183B32; text-decoration: underline; font-size: 0.95rem;">
                            🌐 {esc_display_url}
                        </a>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # Earned Milestone Badges
    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
    st.markdown(f"### 🎖️ Milestone Badges ({passport.badges_count})")
    badges = achievement_service.get_user_badges(current_user.id)
    if badges:
        cols = st.columns(3)
        for idx, b in enumerate(badges):
            with cols[idx % 3]:
                st.markdown(
                    f"""
                    <div class="specimen-card" style="padding: 12px; margin-bottom: 8px; display: flex; align-items: center; gap: 12px;">
                        <span style="font-size: 2rem;">{escape_text(b.icon)}</span>
                        <div>
                            <div style="font-size: 0.95rem; font-weight: 700; color: #183B32;">{escape_text(b.name)}</div>
                            <div style="font-size: 0.78rem; color: #4E5C53;">{escape_text(b.description)}</div>
                            <div style="font-size: 0.72rem; color: #8C5432; font-weight: 600; margin-top: 2px;">+{b.xp_reward} XP</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    else:
        st.caption("No milestone badges earned yet.")
