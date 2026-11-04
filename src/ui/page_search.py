"""Global search and taxonomic discovery interface for Vivédex.

Unified cross-entity querying across taxa, field sites, expeditions,
conservation projects, observations, and public researcher profiles.
"""

from __future__ import annotations

import streamlit as st

from src.database import Database
from src.search_service import SearchService
from src.ui.common import inject_custom_styles, render_breadcrumbs, render_security_notice
from src.ui.theme import escape_text, render_hero_banner


def render_search_page(db: Database) -> None:
    """Render the global cross-entity discovery search page."""
    inject_custom_styles()
    render_security_notice()
    render_breadcrumbs([("Expedition Hub", "home"), ("Global Discovery Search", None)])

    search_service = SearchService(db)

    render_hero_banner(
        title="Global Discovery Search",
        subtitle="Search across taxonomic backbones, field sites, conservation projects, expeditions, and naturalist profiles.",
    )

    query = st.text_input(
        "Search Vivédex",
        placeholder="Enter organism name, field site, country, project, or researcher...",
        key="global_search_query_input",
    )

    if not query.strip():
        st.markdown(
            """
            <div style="background: #FFFFFF; border: 1px solid #D8D1C2; border-radius: 8px; padding: 2rem; text-align: center; color: #4E5C53;">
                <div style="font-size: 2rem; margin-bottom: 8px;">🔍</div>
                <div style="font-weight: 700; color: #183B32; font-size: 1.1rem;">Discover Living Earth</div>
                <p style="font-size: 0.9rem; max-width: 500px; margin: 8px auto 0 auto;">
                    Try searching for <em>"Monstera"</em>, <em>"Monteverde"</em>, <em>"Danum"</em>, <em>"Canopy"</em>, or <em>"Orchidaceae"</em>.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    results = search_service.search(query.strip())
    st.markdown(f"**Found {results.total_matches} matches for '{escape_text(query)}'**")

    tab_all, tab_taxa, tab_sites, tab_proj, tab_obs, tab_res = st.tabs([
        f"All ({results.total_matches})",
        f"Taxa ({len(results.taxa)})",
        f"Field Sites ({len(results.field_sites)})",
        f"Projects & Expeditions ({len(results.projects) + len(results.expeditions)})",
        f"Observations ({len(results.observations)})",
        f"Researchers ({len(results.researchers)})",
    ])

    with tab_all:
        if results.total_matches == 0:
            st.info("No matching records found. Try a broader search term.")
        else:
            if results.taxa:
                st.markdown("#### Taxa")
                for t in results.taxa[:3]:
                    st.markdown(
                        f"""
                        <div class="specimen-card" style="padding: 0.9rem 1.2rem;">
                            <div class="latin-binomial" style="font-size: 1.05rem;">{escape_text(t['scientific_name'])}</div>
                            <div style="font-size: 0.82rem; color: #4E5C53;">{escape_text(t.get('common_name') or 'No common name')} &bull; Family: {escape_text(t.get('family') or 'N/A')} &bull; Rank: {escape_text(t.get('rank') or 'N/A')}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            if results.field_sites:
                st.markdown("#### Field Sites")
                for s in results.field_sites[:3]:
                    st.markdown(
                        f"""
                        <div class="specimen-card" style="padding: 0.9rem 1.2rem;">
                            <div style="font-weight: 700; color: #183B32;">📍 {escape_text(s['name'])} ({escape_text(s['country'])})</div>
                            <div style="font-size: 0.82rem; color: #4E5C53;">{escape_text(s['biome'])} &bull; Elev. {s['elevation_m'] or 0}m</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            if results.projects:
                st.markdown("#### Projects")
                for p in results.projects[:3]:
                    st.markdown(
                        f"""
                        <div class="specimen-card" style="padding: 0.9rem 1.2rem;">
                            <div style="font-weight: 700; color: #183B32;">🌱 {escape_text(p['title'])}</div>
                            <div style="font-size: 0.82rem; color: #4E5C53;">Target: {escape_text(p['target_habitat'])} &bull; Status: {escape_text(p['status'])}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    with tab_taxa:
        if not results.taxa:
            st.caption("No taxa found matching this query.")
        else:
            for t in results.taxa:
                st.markdown(
                    f"""
                    <div class="specimen-card">
                        <div class="latin-binomial" style="font-size: 1.15rem;">{escape_text(t['scientific_name'])}</div>
                        <div style="font-size: 0.88rem; color: #183B32; font-weight: 600; margin-top: 2px;">{escape_text(t.get('common_name') or 'Unspecified Common Name')}</div>
                        <div style="font-size: 0.82rem; color: #4E5C53; margin-top: 4px;">Rank: {escape_text(t.get('rank'))} &bull; Kingdom: {escape_text(t.get('kingdom'))} &bull; Family: {escape_text(t.get('family'))}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    with tab_sites:
        if not results.field_sites:
            st.caption("No field sites found matching this query.")
        else:
            for s in results.field_sites:
                st.markdown(
                    f"""
                    <div class="specimen-card">
                        <div style="font-weight: 700; color: #183B32; font-size: 1.1rem;">📍 {escape_text(s['name'])}</div>
                        <div style="font-size: 0.84rem; color: #8C5432; font-weight: 600;">{escape_text(s['biome'])} &bull; {escape_text(s['country'])} &bull; Elev. {s['elevation_m'] or 0}m</div>
                        <div style="font-size: 0.85rem; color: #4E5C53; margin-top: 4px;">{escape_text(s['description'])}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    with tab_proj:
        if not results.projects and not results.expeditions:
            st.caption("No projects or expeditions found matching this query.")
        else:
            for p in results.projects:
                st.markdown(
                    f"""
                    <div class="specimen-card">
                        <div style="font-weight: 700; color: #183B32; font-size: 1.1rem;">🌱 {escape_text(p['title'])}</div>
                        <div style="font-size: 0.84rem; color: #8C5432; font-weight: 600;">Status: {escape_text(p['status'])} &bull; Target: {escape_text(p['target_habitat'])}</div>
                        <div style="font-size: 0.85rem; color: #4E5C53; margin-top: 4px;">{escape_text(p['summary'])}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            for e in results.expeditions:
                st.markdown(
                    f"""
                    <div class="specimen-card">
                        <div style="font-weight: 700; color: #183B32; font-size: 1.1rem;">🧭 {escape_text(e['title'])}</div>
                        <div style="font-size: 0.84rem; color: #8C5432; font-weight: 600;">Status: {escape_text(e['status'])} &bull; Date: {escape_text(e['start_date'][:10])}</div>
                        <div style="font-size: 0.85rem; color: #4E5C53; margin-top: 4px;">{escape_text(e['description'])}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    with tab_obs:
        if not results.observations:
            st.caption("No observations found matching this query.")
        else:
            for o in results.observations:
                st.markdown(
                    f"""
                    <div class="specimen-card">
                        <div style="display: flex; justify-content: space-between; align-items: baseline;">
                            <span class="latin-binomial" style="font-size: 1.05rem;">{escape_text(o['candidate_scientific_name'])}</span>
                            <span class="status-pill-accepted">{escape_text(o['moderation_status'])}</span>
                        </div>
                        <div style="font-size: 0.82rem; color: #4E5C53; margin-top: 4px;">{escape_text(o['common_name'] or '')} &bull; {escape_text(o['coarse_location'])} &bull; {escape_text(o['observation_timestamp'][:10])}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    with tab_res:
        if not results.researchers:
            st.caption("No public researchers found matching this query.")
        else:
            for r in results.researchers:
                st.markdown(
                    f"""
                    <div class="specimen-card">
                        <div style="font-weight: 700; color: #183B32; font-size: 1.1rem;">👤 {escape_text(r['display_name'])} (@{escape_text(r['username'])})</div>
                        <div style="font-size: 0.8rem; color: #8C5432; font-family: monospace;">Vivédex ID: {escape_text(r['vivedex_id'])}</div>
                        <div style="font-size: 0.85rem; color: #4E5C53; margin-top: 4px;">{escape_text(r['bio'] or 'No bio provided.')}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
