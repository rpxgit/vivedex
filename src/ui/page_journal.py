"""Field Journal page for recording, viewing, and annotating persistent organism observations.

Supports field note updates, moderation status inspection, and observation provenance.
"""

from __future__ import annotations

import json
import streamlit as st

from src.auth import AuthenticatedUser
from src.collection_service import CollectionService
from src.ui.common import inject_custom_styles, render_security_notice


def render_journal_page(collection_service: CollectionService) -> None:
    """Render the Field Journal observation logs and editor view."""
    inject_custom_styles()
    render_security_notice()

    current_user: AuthenticatedUser | None = st.session_state.get("current_user")

    st.markdown('<div class="main-header">📓 Field Journal</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Persistent natural history observations, habitat records, and verification status.</div>',
        unsafe_allow_html=True,
    )

    if current_user is None:
        st.info("Please log in or register via the sidebar to view and manage your Field Journal.")
        return

    # Filter status
    status_filter = st.selectbox(
        "Filter by Moderation Status:",
        ["", "PENDING", "ACCEPTED_FOR_CATALOG", "NEEDS_MORE_EVIDENCE", "REJECTED"],
        key="journal_status_filter",
    )

    observations = collection_service.get_user_observations(
        user_id=current_user.id,
        status_filter=status_filter,
    )

    st.markdown(f"**Total Journal Entries:** {len(observations)}")

    if not observations:
        st.info("No observations found in your journal. Use **Identify** to record your first field encounter!")
        return

    for obs in observations:
        prov_prefix = f"[{obs.provenance}] " if obs.provenance == "DEMO DATA" else ""
        header_text = f"{prov_prefix}{obs.candidate_scientific_name} — {obs.observation_timestamp[:16]} ({obs.moderation_status})"

        with st.expander(header_text):
            col_info1, col_info2 = st.columns(2)
            with col_info1:
                st.write(f"**Observation ID:** `{obs.observation_id}`")
                st.write(f"**Taxon ID:** `{obs.matched_taxon_id or 'Unmatched'}`")
                st.write(f"**Taxonomic Resolution:** `{obs.taxonomic_resolution or 'None'}`")
                st.write(f"**Provenance:** `{obs.provenance}`")
            with col_info2:
                st.write(f"**Recorded At:** {obs.observation_timestamp}")
                st.write(f"**Moderation Status:** <span class='status-pill'>{obs.moderation_status}</span>", unsafe_allow_html=True)
                if obs.coarse_location:
                    st.write(f"**Coarse Location:** {obs.coarse_location}")

            # AI Identification Summary
            if obs.model_result_json:
                try:
                    m_data = json.loads(obs.model_result_json)
                    st.markdown("#### Vision Model Analysis")
                    st.caption(f"Model: {m_data.get('model', 'muse-spark-1.3')}")
                    if m_data.get("observation_summary"):
                        st.write(m_data["observation_summary"])
                except Exception:
                    pass

            # Field notes editor
            st.markdown("#### Field Notes")
            new_notes = st.text_area(
                "Edit Notes:",
                value=obs.field_notes,
                key=f"edit_notes_{obs.observation_id}",
            )

            if st.button("💾 Save Updated Notes", key=f"save_btn_{obs.observation_id}"):
                collection_service.update_observation_notes(
                    user_id=current_user.id,
                    observation_id=obs.observation_id,
                    new_notes=new_notes,
                )
                st.success("Field notes updated successfully! (XP and achievements re-evaluated)")
                st.rerun()

