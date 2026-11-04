"""Taxonomic Knowledge Explorer view for Vivédex.

Visualizes taxonomic lineage hierarchies, connected observations, collectors, and GBIF data provenance.
"""

from __future__ import annotations

import streamlit as st

from src.database import Database
from src.knowledge_graph import KnowledgeGraphService
from src.ui.common import inject_custom_styles, render_security_notice


def render_knowledge_page(db: Database, kg_service: KnowledgeGraphService) -> None:
    """Render the taxonomic knowledge graph and hierarchy exploration view."""
    inject_custom_styles()
    render_security_notice()

    st.markdown('<div class="main-header">🕸️ Knowledge Explorer</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Structured taxonomic hierarchies, connected observation nodes, and data provenance.</div>',
        unsafe_allow_html=True,
    )

    # Fetch available taxa from database
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
        st.info("No taxa currently recorded in the knowledge graph. Identify an organism or load sample demo data.")
        return

    # Select taxon to explore
    taxa_options = {
        f"{row['scientific_name']} ({row['rank'] or 'Unknown'}) [ID: {row['taxon_id']}]": row["taxon_id"]
        for row in taxa_list
    }

    selected_label = st.selectbox(
        "Select Taxon Node to Explore:",
        list(taxa_options.keys()),
        key="kg_taxon_selector",
    )

    selected_taxon_id = taxa_options[selected_label]
    target_taxon = kg_service.get_taxon_by_id(selected_taxon_id)

    if not target_taxon:
        st.error("Taxon record could not be loaded.")
        return

    # 1. Lineage Breadcrumb / Tree
    st.markdown("---")
    st.subheader("🌳 Taxonomic Lineage (Hierarchy)")

    lineage = kg_service.get_taxon_lineage(selected_taxon_id)
    if lineage:
        # Display as connected lineage chain
        lineage_str = "  ➔  ".join(
            f"**{t.scientific_name}** (`{t.rank or 'Taxon'}`)" for t in lineage
        )
        st.markdown(
            f"""
            <div style="background: #f0fdf4; border-left: 5px solid #2d6a4f; padding: 12px; border-radius: 4px; margin-bottom: 16px;">
                {lineage_str}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 2. Graph Neighborhood Details
    neighborhood = kg_service.get_taxon_neighborhood(selected_taxon_id)
    nodes = neighborhood["nodes"]
    edges = neighborhood["edges"]

    col_details, col_relations = st.columns([1, 1])

    with col_details:
        st.markdown("#### 🔬 Taxon Properties")
        st.write(f"**Scientific Name:** *{target_taxon.scientific_name}*")
        st.write(f"**Canonical Name:** *{target_taxon.canonical_name or 'N/A'}*")
        st.write(f"**Rank:** <span class='taxon-rank-pill'>{target_taxon.rank or 'Unknown'}</span>", unsafe_allow_html=True)
        st.write(f"**Status:** `{target_taxon.status or 'N/A'}`")
        st.write(f"**Kingdom:** {target_taxon.kingdom or 'N/A'}")
        st.write(f"**Family:** {target_taxon.family or 'N/A'}")
        st.write(f"**GBIF Taxon Key:** `{target_taxon.taxon_id}`")

        st.markdown("---")
        st.markdown("#### 📜 Source Provenance")
        st.caption(f"**Data Provider:** {target_taxon.data_provider}")
        st.caption(f"**Dataset:** GBIF Backbone Taxonomy")
        st.caption(f"**Licence:** {target_taxon.licence}")
        st.caption(f"**Citation:** {target_taxon.attribution}")

    with col_relations:
        st.markdown(f"#### 🔗 Connected Graph Nodes ({len(nodes)} Nodes, {len(edges)} Edges)")

        # Group edges by type
        parent_edges = [e for e in edges if e.relationship_type == "PARENT_OF" and e.target_id == f"Taxon:{selected_taxon_id}"]
        child_edges = [e for e in edges if e.relationship_type == "PARENT_OF" and e.source_id == f"Taxon:{selected_taxon_id}"]
        obs_edges = [e for e in edges if e.relationship_type == "OBSERVED_IN"]
        col_edges = [e for e in edges if e.relationship_type == "COLLECTED_BY"]

        if parent_edges:
            st.markdown(f"**Parent Taxon:** `{parent_edges[0].source_id}`")

        if child_edges:
            st.markdown(f"**Child Taxa ({len(child_edges)}):**")
            for ce in child_edges:
                st.markdown(f"- `{ce.target_id}`")

        if obs_edges:
            st.markdown(f"**Associated Observations ({len(obs_edges)}):**")
            for oe in obs_edges:
                st.markdown(f"- 📝 `{oe.source_id}`")
        else:
            st.caption("No linked observations recorded for this taxon.")

        if col_edges:
            st.markdown(f"**Recorded Collectors ({len(col_edges)}):**")
            for c_edge in col_edges:
                st.markdown(f"- 👤 `{c_edge.source_id}` (Encounters: {c_edge.properties.get('encounters', 1)})")
        else:
            st.caption("No collectors have saved this taxon yet.")

