"""My Dex view: Personal biodiversity encyclopedia and organism collection catalog.

Tracks cumulative encounters, initial and latest observations, personal field notes,
and completion metrics across biological kingdoms and families.
"""

from __future__ import annotations

import streamlit as st

from src.auth import AuthenticatedUser
from src.collection_service import CollectionService
from src.database import Database
from src.knowledge_graph import KnowledgeGraphService
from src.ui.common import inject_custom_styles, render_security_notice
from src.ui.page_species_detail import CURATED_SPECIMEN_ASSETS
from src.ui.theme import render_hero_banner


def render_collection_page(
    db: Database,
    collection_service: CollectionService,
    kg_service: KnowledgeGraphService,
) -> None:
    """Render the personal My Dex biological encyclopedia view."""
    inject_custom_styles()
    render_security_notice()

    current_user: AuthenticatedUser | None = st.session_state.get("current_user")

    # Banner
    render_hero_banner(
        title="📚 My Dex — Personal Biodiversity Encyclopedia",
        subtitle="Your curated personal catalog of encountered wild species, biological classifications, and observation history.",
    )

    if current_user is None:
        st.info("👋 Please log in or register via the sidebar to access and manage your personal Dex collection.")
        return

    # Check for direct specimen inspection
    if st.session_state.get("selected_taxon_id"):
        from src.ui.page_species_detail import render_species_detail_page
        render_species_detail_page(db, collection_service, kg_service, st.session_state["selected_taxon_id"])
        return

    # Search & Filter Controls
    col_s, col_f, col_k = st.columns([2, 1, 1])
    with col_s:
        search_query = st.text_input("Search My Dex:", placeholder="Scientific or common name...", key="mydex_search")
    with col_f:
        family_filter = st.text_input("Filter Family:", placeholder="e.g. Passeridae", key="mydex_fam")
    with col_k:
        kingdom_filter = st.selectbox("Kingdom:", ["", "Animalia", "Plantae", "Fungi", "Chromista"], key="mydex_kng")

    # Fetch collection items
    items = collection_service.get_user_collection(
        user_id=current_user.id,
        query=search_query,
        family=family_filter,
        kingdom=kingdom_filter,
    )

    # Collection Completion Overview Bar
    with db.connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(DISTINCT taxon_id) FROM taxa WHERE taxon_id IS NOT NULL;")
        total_platform_taxa = cursor.fetchone()[0] or 1

    completion_pct = min(100.0, round((len(items) / max(1, total_platform_taxa)) * 100.0, 1))

    st.markdown(
        f"""
        <div class="specimen-card" style="margin-bottom: 1.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="font-size: 0.9rem; font-weight: 700; color: #183B32;">Encyclopedia Catalog Progress</span>
                <span class="dex-collected-tag" style="font-size: 0.82rem;">{len(items)} Collected / {total_platform_taxa} Known Taxa ({completion_pct}%)</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(completion_pct / 100.0)

    if not items:
        st.markdown(
            """
            <div style="background: #faf7f0; border: 1px dashed #ded6c5; border-radius: 8px; padding: 24px; text-align: center; color: #777E73; margin-top: 1.5rem;">
                <div style="font-size: 2rem; margin-bottom: 8px;">📖</div>
                <div style="font-family: 'Cinzel', serif; font-size: 1.15rem; font-weight: 700; color: #183B32;">Your personal Dex has no entries matching this filter.</div>
                <div style="font-size: 0.85rem; margin-top: 6px;">Use <strong>Identify</strong> to record a photograph or browse <strong>Explore Dex</strong> to add wild organisms.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.write("")
    st.markdown(f"### 📋 Cataloged Specimens ({len(items)})")

    # Render Card Grid (2 Columns)
    cols = st.columns(2)
    for idx, item in enumerate(items):
        t_id = item.taxon_id
        asset = CURATED_SPECIMEN_ASSETS.get(t_id, {})
        img_thumb = asset.get("image_url")

        with cols[idx % 2]:
            st.markdown(
                f"""
                <div class="specimen-card" style="border-left: 4px solid #C6A66B;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span class="rank-pill">{item.rank or 'SPECIES'}</span>
                        <span class="dex-collected-tag">Encounters: {item.encounter_count}</span>
                    </div>
                    <div style="font-family: 'Cinzel', serif; font-size: 1.25rem; font-weight: 700; color: #183B32;">
                        {item.common_name or item.scientific_name}
                    </div>
                    <div class="latin-binomial" style="font-size: 0.95rem; margin-bottom: 6px;">
                        *{item.scientific_name}*
                    </div>
                    <div style="font-size: 0.8rem; color: #777E73;">
                        Family: <strong>{item.family or 'Biota'}</strong> &bull; Kingdom: {item.kingdom or 'Biota'}
                    </div>
                    <div style="font-size: 0.78rem; color: #A66B48; margin-top: 4px;">
                        First Recorded: {item.first_encounter_at[:10]} &bull; Latest: {item.last_encounter_at[:10]}
                    </div>
                    {f'<div style="font-size: 0.8rem; color: #555; background: #fdfaf4; padding: 6px; border-radius: 4px; margin-top: 8px; border: 1px solid #efe8db;">Notes: {item.notes}</div>' if item.notes else ''}
                </div>
                """,
                unsafe_allow_html=True,
            )

            c_btn1, c_btn2 = st.columns([1, 1])
            with c_btn1:
                if st.button("🔬 Inspect Specimen", key=f"mydex_insp_{t_id}_{idx}", width="stretch"):
                    st.session_state["selected_taxon_id"] = t_id
                    st.rerun()
            with c_btn2:
                if st.button("🗑️ Remove", key=f"mydex_rm_{t_id}_{idx}", width="stretch"):
                    collection_service.remove_from_collection(current_user.id, t_id)
                    st.success("Removed from Dex.")
                    st.rerun()
