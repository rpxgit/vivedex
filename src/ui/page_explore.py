"""Explore Dex page for querying and browsing taxonomic records via the GBIF API.

Provides search by scientific or vernacular name, rank filtering, species cards,
hierarchy exploration, and personal collection integration.
"""

from __future__ import annotations

import streamlit as st

from src.auth import AuthenticatedUser
from src.collection_service import CollectionService
from src.gbif_adapter import GBIFAdapter, GBIFRequestError
from src.schemas import GBIFMatchResult
from src.ui.common import inject_custom_styles, render_security_notice


@st.cache_data(ttl=1800, show_spinner=False)
def cached_gbif_lookup(name: str) -> dict | None:
    """Fetch GBIF species match with local caching to conserve network requests."""
    adapter = GBIFAdapter()
    try:
        res = adapter.match_species(name)
        return res.model_dump()
    except GBIFRequestError:
        return None
    except Exception:
        return None


def render_explore_page(collection_service: CollectionService) -> None:
    """Render the Explore Dex search and taxonomy browser view."""
    inject_custom_styles()
    render_security_notice()

    current_user: AuthenticatedUser | None = st.session_state.get("current_user")

    st.markdown('<div class="main-header">🔍 Explore Dex</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Search authoritative biodiversity records via the GBIF Backbone Taxonomy.</div>',
        unsafe_allow_html=True,
    )

    col_q, col_rank = st.columns([3, 1])
    with col_q:
        search_query = st.text_input(
            "Search Organism Name (Scientific or Vernacular):",
            placeholder="e.g. Passer domesticus, Erannis defoliaria, Monarch butterfly, Quercus robur",
            key="explore_search_input",
        )
    with col_rank:
        rank_filter = st.selectbox(
            "Filter Rank:",
            ["ALL", "SPECIES", "GENUS", "FAMILY", "ORDER", "CLASS"],
            key="explore_rank_filter",
        )

    search_button = st.button("Search Taxonomy", type="primary")

    if search_query.strip() and (search_button or search_query != st.session_state.get("_prev_query")):
        st.session_state["_prev_query"] = search_query.strip()
        with st.spinner(f"Reconciling '{search_query.strip()}' against GBIF Backbone Taxonomy..."):
            data = cached_gbif_lookup(search_query.strip())

        if not data:
            st.error(f"Network error or no response received from GBIF for '{search_query.strip()}'.")
            return

        gbif_res = GBIFMatchResult(**data)

        # Apply rank filter if specified
        if rank_filter != "ALL" and gbif_res.rank and gbif_res.rank.upper() != rank_filter:
            st.warning(f"Result returned with rank '{gbif_res.rank}', which does not match filter '{rank_filter}'.")

        # Species Detail Card
        st.markdown("---")
        st.subheader("Taxonomic Record")

        # Check match quality
        is_exact = gbif_res.match_type == "EXACT"
        if gbif_res.match_type == "HIGHERRANK":
            st.warning("⚠️ **Higher-Rank Match:** GBIF could not find a species-level match; resolved to a higher taxonomic rank.")
        elif gbif_res.match_type == "FUZZY":
            st.warning(f"⚠️ **Fuzzy Name Match:** Reconciled via approximate matching (confidence score: {gbif_res.gbif_match_score}/100). Not an exact species match.")
        elif gbif_res.match_type == "NONE":
            st.error(f"❌ No matching taxon found in the GBIF Backbone Taxonomy for '{search_query.strip()}'.")
            return

        col_meta1, col_meta2 = st.columns([2, 1])
        with col_meta1:
            st.markdown(f"### {gbif_res.matched_scientific_name or gbif_res.query_name}")
            if gbif_res.canonical_name:
                st.caption(f"Canonical Binomial: *{gbif_res.canonical_name}*")
            st.markdown(
                f"""
                - **Taxonomic Rank:** <span class="taxon-rank-pill">{gbif_res.rank or 'Unknown'}</span>
                - **Taxonomic Status:** <span class="status-pill">{gbif_res.status or 'Unknown'}</span>
                - **Match Type:** `{gbif_res.match_type}` (Score: {gbif_res.gbif_match_score or 'N/A'}/100)
                - **GBIF Taxon Key:** `{gbif_res.usage_key or 'None'}`
                """,
                unsafe_allow_html=True,
            )

        with col_meta2:
            st.markdown("#### Classification")
            hierarchy = gbif_res.hierarchy or {}
            for rank_level in ["kingdom", "phylum", "class", "order", "family", "genus", "species"]:
                val = hierarchy.get(rank_level)
                if val:
                    st.text(f"{rank_level.capitalize()}: {val}")

        # Provenance and Licence
        st.markdown(
            f"""
            <div class="provenance-tag">
                Provider: {gbif_res.provider} | Dataset: {gbif_res.dataset}<br/>
                Licence: {gbif_res.licence} | Attribution: {gbif_res.attribution}<br/>
                Retrieved: {gbif_res.retrieved_at}
            </div>
            """,
            unsafe_allow_html=True,
        )

        if gbif_res.source_url:
            st.markdown(f"[🌐 View Official GBIF Taxon Page]({gbif_res.source_url})")

        # Action: Save to My Collection
        st.markdown("---")
        if current_user is not None:
            col_act1, col_act2 = st.columns([1, 2])
            with col_act1:
                col_notes = st.text_input("Encounter Notes (optional):", key="explore_enc_notes")
                if st.button("📚 Save to My Collection", type="primary", key="explore_save_btn"):
                    taxon_id = collection_service.upsert_taxon_from_gbif(gbif_res)
                    item = collection_service.save_to_collection(
                        user_id=current_user.id,
                        taxon_id=taxon_id,
                        notes=col_notes,
                    )
                    st.success(f"Saved to your collection! (Total encounters: {item.encounter_count})")
        else:
            st.info("Log in or register via the sidebar to save this taxon to your personal collection!")
