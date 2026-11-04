"""Partner organisations and institutions directory for Vivédex.

Presents collaborating universities, botanical gardens, and conservation trusts.
"""

from __future__ import annotations

import streamlit as st

from src.auth import AuthenticatedUser
from src.database import Database
from src.ecological_service import EcologicalService
from src.ui.common import inject_custom_styles, render_breadcrumbs, render_security_notice
from src.ui.theme import escape_text, render_hero_banner, safe_url


def render_organisations_page(db: Database) -> None:
    """Render the Partner Organisations directory."""
    inject_custom_styles()
    render_security_notice()
    render_breadcrumbs([("Expedition Hub", "home"), ("Organisations", None)])

    current_user: AuthenticatedUser | None = st.session_state.get("current_user")
    eco_service = EcologicalService(db)

    render_hero_banner(
        title="Partner Organisations",
        subtitle="Botanical gardens, scientific research institutions, and conservation foundations advancing open biodiversity discovery.",
    )

    orgs = eco_service.list_organisations()
    st.markdown(f"**{len(orgs)} Accredited Institutions & Conservation Partners**")

    for org in orgs:
        # Check projects supported by this org
        projects = eco_service.list_projects(org_id=org.id)
        proj_badge = f"{len(projects)} Projects" if projects else "Affiliated Partner"
        safe_link = safe_url(org.website_url)

        st.markdown(
            f"""
            <div class="specimen-card">
                <div style="display: flex; justify-content: space-between; align-items: baseline;">
                    <div style="font-family: 'Cinzel', serif; font-size: 1.25rem; font-weight: 700; color: #183B32;">
                        🏛️ {escape_text(org.name)}
                    </div>
                    <span class="rank-pill">{escape_text(org.country)}</span>
                </div>
                <div style="font-size: 0.84rem; color: #8C5432; font-weight: 600; margin: 4px 0 8px 0;">
                    {escape_text(proj_badge)} &bull; {f'<a href="{safe_link}" target="_blank" style="color: #183B32; text-decoration: underline;">Official Website</a>' if safe_link else 'Independent Institute'}
                </div>
                <div style="font-size: 0.88rem; color: #4E5C53; line-height: 1.5;">
                    {escape_text(org.description)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if projects:
            with st.expander(f"View Active Projects ({len(projects)})"):
                for p in projects:
                    st.write(f"- **{p.title}** ({p.status}) &bull; Target: {p.target_habitat}")

    if current_user is not None and current_user.is_admin:
        with st.expander("➕ Register Partner Institution (Admin Only)"):
            with st.form("new_org_form"):
                no_name = st.text_input("Institution / Foundation Name")
                no_country = st.text_input("Headquarters Country")
                no_url = st.text_input("Official Website URL (https://...)")
                no_desc = st.text_area("Institutional Description & Focus Area")
                sub_org = st.form_submit_button("Register Organisation", width="stretch")
                if sub_org:
                    if not no_name.strip():
                        st.error("Organisation name is required.")
                    else:
                        new_o = eco_service.create_organisation(
                            name=no_name,
                            description=no_desc,
                            website_url=no_url,
                            country=no_country,
                        )
                        st.success(f"Organisation '{new_o.name}' registered!")
                        st.rerun()
