"""Field sites, conservation projects, and scientific expeditions for Vivédex.

Inspired by Restor.eco, provides ecological context, monitored habitats,
species richness tracking, and expedition coordination.
"""

from __future__ import annotations

import streamlit as st

from src.auth import AuthenticatedUser
from src.database import Database
from src.ecological_service import EcologicalService
from src.ui.common import inject_custom_styles, render_breadcrumbs, render_security_notice
from src.ui.theme import escape_text, render_hero_banner


def render_sites_projects_page(db: Database) -> None:
    """Render the Field Sites, Projects, and Expeditions module."""
    inject_custom_styles()
    render_security_notice()
    render_breadcrumbs([("Expedition Hub", "home"), ("Field Sites & Projects", None)])

    current_user: AuthenticatedUser | None = st.session_state.get("current_user")
    eco_service = EcologicalService(db)

    render_hero_banner(
        title="Field Sites & Expeditions",
        subtitle="Explore monitored ecosystems, active conservation census projects, and time-bounded field expeditions inspired by Restor.eco.",
    )

    tab_sites, tab_projects, tab_expeditions = st.tabs([
        "📍 Monitored Field Sites",
        "🌱 Conservation Projects",
        "🧭 Field Expeditions",
    ])

    # -------------------------------------------------------------------------
    # TAB 1: FIELD SITES
    # -------------------------------------------------------------------------
    with tab_sites:
        sites = eco_service.list_field_sites()
        st.markdown(f"**{len(sites)} Monitored Ecological Sites Worldwide**")

        for site in sites:
            col_info, col_metrics = st.columns([2.5, 1.2])
            with col_info:
                st.markdown(
                    f"""
                    <div class="specimen-card">
                        <div style="display: flex; justify-content: space-between; align-items: baseline;">
                            <div style="font-family: 'Cinzel', serif; font-size: 1.2rem; font-weight: 700; color: #183B32;">
                                📍 {escape_text(site.name)}
                            </div>
                            <span class="rank-pill">{escape_text(site.country)}</span>
                        </div>
                        <div style="font-size: 0.84rem; color: #8C5432; font-weight: 600; margin: 4px 0 8px 0;">
                            {escape_text(site.biome)} &bull; Lat {site.latitude or 0:.3f}, Lon {site.longitude or 0:.3f} &bull; Elev. {site.elevation_m or 0}m
                        </div>
                        <div style="font-size: 0.88rem; color: #4E5C53; line-height: 1.5;">
                            {escape_text(site.description)}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with col_metrics:
                st.markdown(
                    f"""
                    <div style="display: flex; gap: 8px;">
                        <div class="naturalist-metric" style="flex: 1; padding: 0.8rem 0.5rem;">
                            <div class="metric-val" style="font-size: 1.4rem;">{site.observation_count}</div>
                            <div class="metric-label" style="font-size: 0.72rem;">Observations</div>
                        </div>
                        <div class="naturalist-metric" style="flex: 1; padding: 0.8rem 0.5rem;">
                            <div class="metric-val" style="font-size: 1.4rem;">{site.species_richness}</div>
                            <div class="metric-label" style="font-size: 0.72rem;">Richness</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Expand site observations
                with st.expander(f"View Site Encounters ({site.observation_count})"):
                    obs_list = eco_service.get_site_observations(site.id)
                    if not obs_list:
                        st.caption("No observations linked to this site yet.")
                    else:
                        for o in obs_list[:5]:
                            c_name = o.get("common_name") or o["candidate_scientific_name"]
                            st.write(f"- *{o['candidate_scientific_name']}* ({c_name}) &bull; `{o['taxonomic_resolution']}`")

        # Register New Field Site
        if current_user is not None:
            with st.expander("➕ Register a New Field Site"):
                with st.form("new_site_form"):
                    ns_name = st.text_input("Site Name (e.g. Monteverde Cloud Forest)")
                    ns_biome = st.text_input("Ecosystem / Biome (e.g. Tropical Cloud Forest)")
                    ns_country = st.text_input("Country (e.g. Costa Rica)")
                    ns_desc = st.text_area("Site Ecological Description")
                    col_g1, col_g2, col_g3 = st.columns(3)
                    with col_g1:
                        ns_lat = st.number_input("Latitude", value=0.0, format="%.5f")
                    with col_g2:
                        ns_lon = st.number_input("Longitude", value=0.0, format="%.5f")
                    with col_g3:
                        ns_elev = st.number_input("Elevation (meters)", value=0.0)

                    sub_site = st.form_submit_button("Register Site", width="stretch")
                    if sub_site:
                        if not ns_name.strip():
                            st.error("Site name is required.")
                        else:
                            new_s = eco_service.create_field_site(
                                name=ns_name,
                                description=ns_desc,
                                biome=ns_biome,
                                latitude=ns_lat,
                                longitude=ns_lon,
                                elevation_m=ns_elev,
                                country=ns_country,
                            )
                            st.success(f"Field site '{new_s.name}' registered successfully!")
                            st.rerun()

    # -------------------------------------------------------------------------
    # TAB 2: CONSERVATION PROJECTS
    # -------------------------------------------------------------------------
    with tab_projects:
        projects = eco_service.list_projects()
        st.markdown(f"**{len(projects)} Scientific & Census Projects Active**")

        for proj in projects:
            st.markdown(
                f"""
                <div class="specimen-card">
                    <div style="display: flex; justify-content: space-between; align-items: baseline;">
                        <div style="font-family: 'Cinzel', serif; font-size: 1.15rem; font-weight: 700; color: #183B32;">
                            🌱 {escape_text(proj.title)}
                        </div>
                        <span class="status-pill-accepted">{escape_text(proj.status)}</span>
                    </div>
                    <div style="font-size: 0.84rem; color: #8C5432; font-weight: 600; margin: 4px 0 6px 0;">
                        Partner: {escape_text(proj.organisation_name or "Independent Field Project")} &bull; Target: {escape_text(proj.target_habitat)}
                    </div>
                    <div style="font-size: 0.88rem; color: #4E5C53; line-height: 1.5;">
                        {escape_text(proj.summary)}
                    </div>
                    <div style="font-size: 0.8rem; color: #183B32; font-weight: 600; margin-top: 8px;">
                        Target Species: {proj.target_species_count} &bull; Observations Contributed: {proj.observation_count}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if current_user is not None:
            with st.expander("➕ Create New Project"):
                orgs = eco_service.list_organisations()
                org_options = {o.name: o.id for o in orgs}
                org_options["(Independent / None)"] = None

                with st.form("new_project_form"):
                    np_title = st.text_input("Project Title")
                    np_summary = st.text_area("Project Summary and Conservation Objectives")
                    np_habitat = st.text_input("Target Habitat / Strata (e.g. Canopy, Riparian Zone)")
                    np_species_target = st.number_input("Target Species Count", min_value=1, value=25)
                    np_org = st.selectbox("Partner Organisation", list(org_options.keys()))
                    sub_proj = st.form_submit_button("Create Project", width="stretch")
                    if sub_proj:
                        if not np_title.strip():
                            st.error("Project title is required.")
                        else:
                            try:
                                p = eco_service.create_project(
                                    title=np_title,
                                    summary=np_summary,
                                    organisation_id=org_options[np_org],
                                    lead_user_id=current_user.id,
                                    target_habitat=np_habitat,
                                    target_species_count=int(np_species_target),
                                    status="ACTIVE",
                                    user=current_user,
                                )
                                st.success(f"Project '{p.title}' initialized successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(str(e))

    # -------------------------------------------------------------------------
    # TAB 3: FIELD EXPEDITIONS
    # -------------------------------------------------------------------------
    with tab_expeditions:
        expeditions = eco_service.list_expeditions()
        st.markdown(f"**{len(expeditions)} Scientific Field Expeditions**")

        for exp in expeditions:
            st.markdown(
                f"""
                <div class="specimen-card">
                    <div style="display: flex; justify-content: space-between; align-items: baseline;">
                        <div style="font-family: 'Cinzel', serif; font-size: 1.15rem; font-weight: 700; color: #183B32;">
                            🧭 {escape_text(exp.title)}
                        </div>
                        <span class="status-pill-pending">{escape_text(exp.status)}</span>
                    </div>
                    <div style="font-size: 0.84rem; color: #8C5432; font-weight: 600; margin: 4px 0 6px 0;">
                        Site: {escape_text(exp.site_name or "Global")} &bull; Project: {escape_text(exp.project_title or "Unlinked")}
                    </div>
                    <div style="font-size: 0.88rem; color: #4E5C53; line-height: 1.5;">
                        {escape_text(exp.description)}
                    </div>
                    <div style="font-size: 0.8rem; color: #183B32; font-weight: 600; margin-top: 8px;">
                        Dates: {escape_text(exp.start_date[:10])} to {escape_text(exp.end_date[:10] if exp.end_date else 'Ongoing')} &bull; Observations: {exp.observation_count}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if current_user is not None:
            with st.expander("➕ Plan New Expedition"):
                sites_all = eco_service.list_field_sites()
                site_map = {s.name: s.id for s in sites_all}
                site_map["(Unassigned Site)"] = None

                projs_all = eco_service.list_projects()
                proj_map = {p.title: p.id for p in projs_all}
                proj_map["(Independent Expedition)"] = None

                with st.form("new_expedition_form"):
                    ne_title = st.text_input("Expedition Title")
                    ne_desc = st.text_area("Expedition Description and Transect Plan")
                    ne_site = st.selectbox("Field Site Destination", list(site_map.keys()))
                    ne_proj = st.selectbox("Associated Project", list(proj_map.keys()))
                    col_ed1, col_ed2 = st.columns(2)
                    with col_ed1:
                        ne_start = st.date_input("Start Date")
                    with col_ed2:
                        ne_end = st.date_input("End Date")

                    sub_exp = st.form_submit_button("Register Expedition", width="stretch")
                    if sub_exp:
                        if not ne_title.strip():
                            st.error("Expedition title is required.")
                        else:
                            exp = eco_service.create_expedition(
                                title=ne_title,
                                description=ne_desc,
                                site_id=site_map[ne_site],
                                project_id=proj_map[ne_proj],
                                lead_user_id=current_user.id,
                                start_date=str(ne_start),
                                end_date=str(ne_end),
                                status="PLANNED",
                            )
                            st.success(f"Expedition '{exp.title}' created successfully!")
                            st.rerun()

