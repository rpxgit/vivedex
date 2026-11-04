"""My Collection page for managing personal organism catalogs.

Presents saved taxa, encounter counts, taxonomic groupings, notes, and remove actions.
"""

from __future__ import annotations

import streamlit as st

from src.auth import AuthenticatedUser
from src.collection_service import CollectionService
from src.ui.common import inject_custom_styles, render_security_notice


def render_collection_page(collection_service: CollectionService) -> None:
    """Render the My Collection personal catalog view."""
    inject_custom_styles()
    render_security_notice()

    current_user: AuthenticatedUser | None = st.session_state.get("current_user")

    st.markdown('<div class="main-header">📚 My Collection</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Your personal biodiversity catalogue and encounter history.</div>',
        unsafe_allow_html=True,
    )

    if current_user is None:
        st.info("Please log in or register via the sidebar to view and manage your personal collection.")
        return

    # Search & Filters
    col_s, col_f, col_k = st.columns([2, 1, 1])
    with col_s:
        search_query = st.text_input("Search Collection:", placeholder="Taxon or common name...", key="coll_search")
    with col_f:
        family_filter = st.text_input("Filter by Family:", placeholder="e.g. Passeridae", key="coll_fam")
    with col_k:
        kingdom_filter = st.selectbox("Kingdom:", ["", "Animalia", "Plantae", "Fungi", "Chromista", "Bacteria"], key="coll_kng")

    items = collection_service.get_user_collection(
        user_id=current_user.id,
        query=search_query,
        family=family_filter,
        kingdom=kingdom_filter,
    )

    st.markdown(f"**Total Collected Taxa:** {len(items)}")

    if not items:
        st.info("No taxa found in your collection matching the criteria. Use **Identify** or **Explore Dex** to add your first organism!")
        return

    # List items
    for item in items:
        with st.expander(f"{item.scientific_name} ({item.common_name or 'No common name'}) — Encounters: {item.encounter_count}"):
            c1, c2, c3 = st.columns([2, 2, 1])
            with c1:
                st.write(f"**Taxon ID:** `{item.taxon_id}`")
                st.write(f"**Rank:** `{item.rank or 'Unknown'}`")
                st.write(f"**Family:** {item.family or 'N/A'}")
                st.write(f"**Kingdom:** {item.kingdom or 'N/A'}")
            with c2:
                st.write(f"**First Encounter:** {item.first_encounter_at[:10]}")
                st.write(f"**Latest Encounter:** {item.last_encounter_at[:10]}")
                st.write(f"**Total Encounters:** {item.encounter_count}")
                if item.notes:
                    st.caption(f"Notes: {item.notes}")
            with c3:
                if st.button("🗑️ Remove", key=f"del_col_{item.taxon_id}"):
                    collection_service.remove_from_collection(current_user.id, item.taxon_id)
                    st.success("Removed from collection.")
                    st.rerun()
