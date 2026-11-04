"""Knowledge Explorer view: SQLite-backed taxonomic graph browser.

Presents progressive lineage breadcrumbs, parent and child taxa nodes,
connected observations, and source provenance without external graph databases.
"""

from __future__ import annotations

import streamlit as st

from src.database import Database
from src.knowledge_graph import KnowledgeGraphService
from src.ui.common import inject_custom_styles, render_security_notice
from src.ui.theme import escape_text, render_hero_banner


def render_knowledge_page(db: Database, kg_service: KnowledgeGraphService) -> None:
    """Render the reconstructed graphical taxonomy knowledge browser."""
    inject_custom_styles()
    render_security_notice()

    # Banner
    render_hero_banner(
        title="🕸️ Taxonomic Knowledge Explorer",
        subtitle="Graph-based exploration of phylogenetic lineages, parent-child taxon trees, specimen sightings, and authoritative GBIF source provenance.",
    )

    # Fetch stored taxa from database
    with db.connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT taxon_id, scientific_name, rank, common_name
            FROM taxa
            WHERE taxon_id IS NOT NULL AND scientific_name IS NOT NULL
            ORDER BY scientific_name ASC;
            """
        )
        taxa_list = cursor.fetchall()

    if not taxa_list:
        st.info("No taxa currently recorded in the knowledge graph. Identify an organism or load sample demo data to explore graph nodes.")
        return

    # Taxon Node Selector
    taxa_options = {
        f"{row['scientific_name']} ({row['rank'] or 'Unknown'}) [Key: {row['taxon_id']}]": row["taxon_id"]
        for row in taxa_list
    }

    selected_label = st.selectbox(
        "Select Active Taxon Node to Inspect:",
        list(taxa_options.keys()),
        key="kg_active_node_select",
    )

    selected_taxon_id = taxa_options[selected_label]
    target_taxon = kg_service.get_taxon_by_id(selected_taxon_id)

    if not target_taxon:
        st.error("Selected taxon record could not be retrieved from database.")
        return

    # Lineage Tree Breadcrumb
    st.markdown("---")
    st.subheader("🌳 Phylogenetic Lineage Tree (Progressive Traversal)")

    lineage = kg_service.get_taxon_lineage(selected_taxon_id)
    if lineage:
        lineage_chips = []
        for t in lineage:
            is_active = t.taxon_id == selected_taxon_id
            bg_col = "#183B32" if is_active else "#f0fdf4"
            text_col = "#FCFAF4" if is_active else "#183B32"
            border_col = "#183B32" if is_active else "#c8d8be"
            esc_t_rank = escape_text(t.rank or "Taxon")
            esc_t_sci = escape_text(t.scientific_name)
            lineage_chips.append(
                f'<span style="background:{bg_col}; color:{text_col}; border:1px solid {border_col}; padding:5px 12px; border-radius:20px; font-size:0.85rem; font-weight:600;">'
                f"{esc_t_rank}: *{esc_t_sci}*</span>"
            )

        st.markdown(
            f'<div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap; margin-bottom:1.5rem;">'
            + " ➔ ".join(lineage_chips)
            + "</div>",
            unsafe_allow_html=True,
        )

    # Neighborhood Graph Breakdown
    neighborhood = kg_service.get_taxon_neighborhood(selected_taxon_id)
    nodes = neighborhood["nodes"]
    edges = neighborhood["edges"]

    col_node_info, col_edges = st.columns([1, 1])

    with col_node_info:
        esc_sci_name = escape_text(target_taxon.scientific_name)
        esc_rank = escape_text(target_taxon.rank or "UNKNOWN")
        esc_status = escape_text(target_taxon.status or "ACCEPTED")
        esc_kingdom = escape_text(target_taxon.kingdom or "N/A")
        esc_phylum = escape_text(target_taxon.phylum or "N/A")
        esc_class = escape_text(target_taxon.class_name or "N/A")
        esc_order = escape_text(target_taxon.order_name or "N/A")
        esc_family = escape_text(target_taxon.family or "N/A")
        esc_genus = escape_text(target_taxon.genus or "N/A")
        esc_taxon_id = escape_text(str(target_taxon.taxon_id))

        st.markdown(
            f"""
            <div class="specimen-card" style="border-left: 5px solid #183B32;">
                <div style="font-size: 0.78rem; font-weight: 700; text-transform: uppercase; color: #777E73;">Active Graph Node</div>
                <h3 style="margin: 4px 0 2px 0;">{esc_sci_name}</h3>
                <div class="latin-binomial" style="font-size: 0.95rem; margin-bottom: 8px;">
                    Rank: <span class="rank-pill">{esc_rank}</span> &bull; Status: {esc_status}
                </div>
                <div style="font-size: 0.85rem; color: #555; line-height: 1.6;">
                    Kingdom: <strong>{esc_kingdom}</strong><br/>
                    Phylum: <strong>{esc_phylum}</strong><br/>
                    Class: <strong>{esc_class}</strong><br/>
                    Order: <strong>{esc_order}</strong><br/>
                    Family: <strong>{esc_family}</strong><br/>
                    Genus: <strong>{esc_genus}</strong><br/>
                    GBIF Taxon Key: <code>{esc_taxon_id}</code>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("#### 📜 Data Provenance & Open Licensing")
        esc_provider = escape_text(target_taxon.data_provider)
        esc_licence = escape_text(target_taxon.licence)
        esc_attr = escape_text(target_taxon.attribution)
        esc_retrieved = escape_text(target_taxon.retrieved_at[:10] if target_taxon.retrieved_at else "")
        st.markdown(
            f"""
            <div class="provenance-tag">
                Authority: {esc_provider}<br/>
                Dataset: GBIF Backbone Taxonomy<br/>
                Licence: {esc_licence} (CC BY 4.0)<br/>
                Attribution: {esc_attr}<br/>
                Retrieved: {esc_retrieved}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_edges:
        st.markdown(f"#### 🔗 Connected Graph Neighborhood ({len(nodes)} Nodes, {len(edges)} Edges)")

        parent_edges = [e for e in edges if e.relationship_type == "PARENT_OF" and e.target_id == f"Taxon:{selected_taxon_id}"]
        child_edges = [e for e in edges if e.relationship_type == "PARENT_OF" and e.source_id == f"Taxon:{selected_taxon_id}"]
        obs_edges = [e for e in edges if e.relationship_type == "OBSERVED_IN"]
        col_edges = [e for e in edges if e.relationship_type == "COLLECTED_BY"]

        if parent_edges:
            st.markdown(f"**Parent Taxon Node (`PARENT_OF`):** `{parent_edges[0].source_id}`")

        if child_edges:
            st.markdown(f"**Child Taxon Nodes (`PARENT_OF` — {len(child_edges)}):**")
            for ce in child_edges:
                st.markdown(f"- 🌿 `{ce.target_id}`")

        if obs_edges:
            st.markdown(f"**Observation Nodes (`OBSERVED_IN` — {len(obs_edges)}):**")
            for oe in obs_edges:
                st.markdown(f"- 📝 `{oe.source_id}`")
        else:
            st.caption("No field observation nodes currently linked to this taxon.")

        if col_edges:
            st.markdown(f"**Collector Nodes (`COLLECTED_BY` — {len(col_edges)}):**")
            for ce in col_edges:
                st.markdown(f"- 👤 `{ce.source_id}` (Encounter Count: {ce.properties.get('encounters', 1)})")
        else:
            st.caption("No naturalists have added this taxon to My Dex yet.")

    st.markdown("---")
    col_nav1, _ = st.columns([1, 1])
    with col_nav1:
        if st.button("🔬 View Deep Specimen Page for this Taxon", type="primary"):
            st.session_state["selected_taxon_id"] = selected_taxon_id
            st.session_state["nav_target"] = "Explore"
            st.rerun()
