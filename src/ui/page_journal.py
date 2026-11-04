"""Field Journal view: Structured chronological observation diary for Vivédex.

Presents observation timeline, diagnostic AI vision evidence, editable field notes,
coarse locality tracking, and transparent moderation status indicators.
"""

from __future__ import annotations

import json
import streamlit as st

from src.auth import AuthenticatedUser
from src.collection_service import CollectionService
from src.ui.common import inject_custom_styles, render_security_notice
from src.ui.theme import escape_text, render_hero_banner


def render_journal_page(collection_service: CollectionService) -> None:
    """Render the chronological naturalist Field Journal view."""
    inject_custom_styles()
    render_security_notice()

    current_user: AuthenticatedUser | None = st.session_state.get("current_user")

    # Banner
    render_hero_banner(
        title="📓 Naturalist Field Journal",
        subtitle="Chronological log of personal wildlife sightings, ecological habitat observations, and community verification status.",
    )

    if current_user is None:
        st.info("👋 Please log in or register via the sidebar to view your private Field Journal entries.")
        return

    # Filter Controls
    col_filter, col_sort = st.columns([3, 1])
    with col_filter:
        status_filter = st.selectbox(
            "Filter by Moderation State:",
            ["", "PENDING", "ACCEPTED_FOR_CATALOG", "NEEDS_MORE_EVIDENCE", "REJECTED"],
            key="journal_mod_filter",
        )

    observations = collection_service.get_user_observations(
        user_id=current_user.id,
        status_filter=status_filter,
    )

    st.markdown(f"**Total Journal Records:** {len(observations)}")

    if not observations:
        st.markdown(
            """
            <div style="background: #faf7f0; border: 1px dashed #ded6c5; border-radius: 8px; padding: 24px; text-align: center; color: #777E73; margin-top: 1rem;">
                <div style="font-size: 2rem; margin-bottom: 8px;">📓</div>
                <div style="font-family: 'Cinzel', serif; font-size: 1.15rem; font-weight: 700; color: #183B32;">No journal records match this filter.</div>
                <div style="font-size: 0.85rem; margin-top: 6px;">Use <strong>Identify</strong> to record your next wildlife observation.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # Chronological Timeline
    st.write("")
    for obs in observations:
        prov_prefix = f"[{obs.provenance}] " if obs.provenance == "DEMO DATA" else ""
        status_class = (
            "status-pill-accepted"
            if obs.moderation_status == "ACCEPTED_FOR_CATALOG"
            else (
                "status-pill-pending"
                if obs.moderation_status == "PENDING"
                else "status-pill-review"
            )
        )

        with st.expander(
            f"{prov_prefix}{obs.candidate_scientific_name} ({obs.observation_timestamp[:10]}) — {obs.moderation_status}"
        ):
            c_meta1, c_meta2 = st.columns([1, 1])
            with c_meta1:
                st.write(f"**Record ID:** `{obs.observation_id}`")
                esc_sci_name = escape_text(obs.candidate_scientific_name)
                st.write(f"**Candidate Taxon:** <span class='latin-binomial'>*{esc_sci_name}*</span>", unsafe_allow_html=True)
                st.write(f"**Taxon ID Key:** `{obs.matched_taxon_id or 'Unmatched'}`")
                st.write(f"**Taxonomic Resolution:** `{obs.taxonomic_resolution or 'None'}`")
            with c_meta2:
                st.write(f"**Observed Timestamp:** {obs.observation_timestamp}")
                esc_mod_status = escape_text(obs.moderation_status)
                st.write(f"**Moderation State:** <span class='{status_class}'>{esc_mod_status}</span>", unsafe_allow_html=True)
                st.write(f"**Data Provenance:** `{obs.provenance}`")
                if obs.coarse_location:
                    st.write(f"**Coarse Locality:** 📍 {obs.coarse_location}")

            # Vision Analysis Recap
            if obs.model_result_json:
                try:
                    m_data = json.loads(obs.model_result_json)
                    if m_data.get("observation_summary"):
                        esc_obs_summary = escape_text(m_data["observation_summary"])
                        st.markdown(
                            f"""
                            <div style="background:#fdfaf4; border-left:3px solid #718568; padding:8px 12px; margin:10px 0; font-size:0.85rem; color:#444;">
                                <strong>AI Vision Summary:</strong> {esc_obs_summary}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                except Exception:
                    pass

            # Editable Field Notes
            st.markdown("#### 📝 Naturalist Field Notes")
            edited_notes = st.text_area(
                "Update Habitat, Behavior, or Morphological Notes:",
                value=obs.field_notes,
                key=f"jnl_edit_{obs.observation_id}",
            )

            if st.button("💾 Save Updated Field Notes", key=f"jnl_save_{obs.observation_id}", type="primary"):
                collection_service.update_observation_notes(
                    user_id=current_user.id,
                    observation_id=obs.observation_id,
                    new_notes=edited_notes,
                )
                st.success("Field notes updated! XP and naturalist badges re-evaluated.")
                st.rerun()
