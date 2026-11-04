"""Explore Dex view: The visual centre of the Vivédex biodiversity catalog.

Provides visual specimen cards, 10 biological category filters, GBIF live search,
curated specimen galleries, and deep links to detailed species pages.
"""

from __future__ import annotations

import streamlit as st

from src.auth import AuthenticatedUser
from src.collection_service import CollectionService
from src.database import Database
from src.gbif_adapter import GBIFAdapter, GBIFRequestError
from src.knowledge_graph import KnowledgeGraphService
from src.schemas import GBIFMatchResult
from src.ui.common import inject_custom_styles, render_security_notice
from src.ui.page_species_detail import CURATED_SPECIMEN_ASSETS, render_species_detail_page
from src.ui.theme import escape_text, render_hero_banner

# 10 Biological Browsing Categories
TAXONOMIC_CATEGORIES = [
    ("ALL", "All Organisms", "🌐"),
    ("Aves", "Birds", "🦅"),
    ("Mammalia", "Mammals", "🦊"),
    ("Reptilia", "Reptiles", "🦎"),
    ("Amphibia", "Amphibians", "🐸"),
    ("Actinopterygii", "Fish", "🐟"),
    ("Insecta", "Insects", "🦋"),
    ("Arachnida", "Arachnids", "🕷️"),
    ("Plantae", "Plants", "🌿"),
    ("Fungi", "Fungi", "🍄"),
    ("Other", "Other Organisms", "🌊"),
]


@st.cache_data(ttl=1800, show_spinner=False)
def cached_gbif_match(name: str) -> dict | None:
    """Fetch and cache live GBIF species reconciliation results."""
    adapter = GBIFAdapter()
    try:
        res = adapter.match_species(name)
        return res.model_dump()
    except GBIFRequestError:
        return None
    except Exception:
        return None


def render_explore_page(
    db: Database,
    collection_service: CollectionService,
    kg_service: KnowledgeGraphService,
) -> None:
    """Render the reconstructed Explore Dex visual specimen catalog."""
    inject_custom_styles()
    render_security_notice()

    current_user: AuthenticatedUser | None = st.session_state.get("current_user")

    # If a specific taxon is selected for deep inspection, route to detail view
    selected_id = st.session_state.get("selected_taxon_id")
    if selected_id:
        render_species_detail_page(db, collection_service, kg_service, selected_id)
        return

    # Banner
    render_hero_banner(
        title="🔍 Explore Dex",
        subtitle="Browse authoritative biological specimens, filter across taxonomic kingdoms and classes, and inspect authoritative GBIF Backbone records.",
    )

    # Search & Category Filters
    col_search, col_rank = st.columns([3, 1])
    with col_search:
        search_query = st.text_input(
            "Search Organism Name:",
            placeholder="Search binomial (e.g. Passer domesticus, Quercus) or common name...",
            key="explore_dex_search",
        )
    with col_rank:
        rank_filter = st.selectbox(
            "Filter Rank:",
            ["ALL", "SPECIES", "GENUS", "FAMILY", "ORDER", "CLASS"],
            key="explore_dex_rank",
        )

    # 10 Browsing Categories as Horizontal Tabs/Pills
    category_labels = [f"{icon} {label}" for _, label, icon in TAXONOMIC_CATEGORIES]
    selected_cat_idx = st.radio(
        "Taxonomic Group Filter:",
        options=range(len(TAXONOMIC_CATEGORIES)),
        format_func=lambda i: category_labels[i],
        horizontal=True,
        key="explore_dex_cat_radio",
    )
    selected_cat_key = TAXONOMIC_CATEGORIES[selected_cat_idx][0]

    # Check for live search query
    if search_query.strip():
        st.markdown("---")
        st.subheader(f"Search Results for: *{search_query.strip()}*")

        with st.spinner(f"Reconciling '{search_query.strip()}' against GBIF Backbone Taxonomy..."):
            raw_match = cached_gbif_match(search_query.strip())

        if not raw_match:
            st.error(f"No response or network failure querying GBIF for '{search_query.strip()}'.")
        else:
            gbif_res = GBIFMatchResult(**raw_match)
            if gbif_res.match_type == "NONE":
                st.warning(f"❌ No matching taxon found in the GBIF Backbone Taxonomy for '{search_query.strip()}'.")
            else:
                # Upsert taxon so it can be viewed in detail
                taxon_id = collection_service.upsert_taxon_from_gbif(gbif_res)

                # Render result card
                is_exact = gbif_res.match_type == "EXACT"
                esc_rank = escape_text(gbif_res.rank or "TAXON")
                esc_name = escape_text(gbif_res.matched_scientific_name or gbif_res.query_name)
                fam_val = gbif_res.hierarchy.get("family", "Unassigned") if gbif_res.hierarchy else "N/A"
                esc_family = escape_text(fam_val)
                esc_match_type = escape_text(gbif_res.match_type)
                esc_score = escape_text(str(gbif_res.gbif_match_score) if gbif_res.gbif_match_score is not None else "N/A")

                st.markdown(
                    f"""
                    <div class="specimen-card" style="border-left: 5px solid {'#183B32' if is_exact else '#A66B48'};">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap;">
                            <div>
                                <span class="rank-pill">{esc_rank}</span>
                                <h3 style="margin: 4px 0 2px 0;">{esc_name}</h3>
                                <div style="font-size: 0.85rem; color: #555;">Family: {esc_family}</div>
                            </div>
                            <div style="text-align: right;">
                                <span class="status-pill-{ 'accepted' if is_exact else 'pending' }">
                                    {esc_match_type} MATCH ({esc_score}/100)
                                </span>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                col_b1, col_b2 = st.columns([1, 1])
                with col_b1:
                    if st.button("🔬 Inspect Deep Specimen Page", key=f"inspect_search_{taxon_id}", type="primary"):
                        st.session_state["selected_taxon_id"] = taxon_id
                        st.rerun()
                with col_b2:
                    if current_user is not None:
                        if st.button("📚 Save to My Dex", key=f"save_search_{taxon_id}"):
                            collection_service.save_to_collection(current_user.id, taxon_id)
                            st.success("Saved to your personal Dex!")
                            st.rerun()

    # Specimen Gallery from Database
    st.markdown("---")
    st.subheader("📚 Curated Specimen Catalog")

    # Fetch stored taxa from database
    with db.connect() as conn:
        cursor = conn.cursor()
        sql = """
            SELECT taxon_id, scientific_name, canonical_name, common_name,
                   rank, family, kingdom, class_name, data_provider
            FROM taxa
            WHERE taxon_id IS NOT NULL AND scientific_name IS NOT NULL
        """
        params = []
        if selected_cat_key != "ALL":
            if selected_cat_key in ["Aves", "Mammalia", "Reptilia", "Amphibia", "Actinopterygii", "Insecta", "Arachnida"]:
                sql += " AND class_name = ?"
                params.append(selected_cat_key)
            elif selected_cat_key in ["Plantae", "Fungi"]:
                sql += " AND kingdom = ?"
                params.append(selected_cat_key)

        if rank_filter != "ALL":
            sql += " AND rank = ?"
            params.append(rank_filter)

        sql += " ORDER BY scientific_name ASC;"
        cursor.execute(sql, params)
        db_taxa = cursor.fetchall()

    if not db_taxa:
        st.info("No specimens recorded in this category yet. Use search above or load the sample demo dataset to explore curated taxa.")
        return

    # Check user collection state
    user_collected_ids = set()
    if current_user is not None:
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT taxon_id FROM collections WHERE user_id = ?;", (current_user.id,))
            user_collected_ids = {r[0] for r in cursor.fetchall()}

    # Render Specimen Grid (2 Columns)
    cols = st.columns(2)
    for idx, t in enumerate(db_taxa):
        t_id = t["taxon_id"]
        in_user_dex = t_id in user_collected_ids
        asset = CURATED_SPECIMEN_ASSETS.get(t_id, {})
        img_thumb = asset.get("image_url")

        with cols[idx % 2]:
            esc_t_rank = escape_text(t['rank'] or 'SPECIES')
            esc_t_common = escape_text(t['common_name'] or t['scientific_name'])
            esc_t_sci = escape_text(t['scientific_name'])
            esc_t_family = escape_text(t['family'] or 'Biota')
            esc_t_kingdom = escape_text(t['kingdom'] or 'Biota')
            st.markdown(
                f"""
                <div class="specimen-card" style="min-height: 200px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span class="rank-pill">{esc_t_rank}</span>
                        <span class="{'dex-collected-tag' if in_user_dex else 'status-pill-pending'}" style="font-size: 0.72rem;">
                            {'✅ IN MY DEX' if in_user_dex else '⚪ NOT RECORDED'}
                        </span>
                    </div>
                    <div style="font-family: 'Cinzel', serif; font-size: 1.25rem; font-weight: 700; color: #183B32;">
                        {esc_t_common}
                    </div>
                    <div class="latin-binomial" style="font-size: 0.95rem; margin-bottom: 6px;">
                        *{esc_t_sci}*
                    </div>
                    <div style="font-size: 0.8rem; color: #777E73; margin-bottom: 12px;">
                        Family: <strong>{esc_t_family}</strong> &bull; Kingdom: {esc_t_kingdom}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            col_btn1, col_btn2 = st.columns([1, 1])
            with col_btn1:
                if st.button("🔬 Inspect Specimen", key=f"grid_insp_{t_id}_{idx}", width="stretch"):
                    st.session_state["selected_taxon_id"] = t_id
                    st.rerun()
            with col_btn2:
                if current_user is not None and not in_user_dex:
                    if st.button("📚 Add to Dex", key=f"grid_add_{t_id}_{idx}", width="stretch"):
                        collection_service.save_to_collection(current_user.id, t_id)
                        st.success("Added to Dex!")
                        st.rerun()
                elif in_user_dex:
                    st.caption("Already in Dex")
