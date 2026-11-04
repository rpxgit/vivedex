"""Organism identification workflow integrating Meta Muse Spark and GBIF Backbone Taxonomy.

Preserves in-memory processing, strict metadata stripping, candidate uncertainty,
and adds persistent field recording into user collections.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
import streamlit as st

from src.auth import AuthenticatedUser
from src.backend import VivedexBackend
from src.collection_service import CollectionService
from src.fixtures import get_demo_fixture_result
from src.gbif_adapter import GBIFRequestError
from src.image_processor import ImageValidationError
from src.meta_adapter import MetaAPIConfigurationError, MetaAPIRequestError
from src.schemas import VivedexResult
from src.ui.common import inject_custom_styles, render_security_notice


def render_identify_page(
    backend: VivedexBackend,
    collection_service: CollectionService,
) -> None:
    """Render the Identify page with image upload, live inference, and collection actions."""
    inject_custom_styles()
    render_security_notice()

    current_user: AuthenticatedUser | None = st.session_state.get("current_user")

    st.markdown('<div class="main-header">🌿 Identify Organism</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Cautious, explainable organism identification backed by authoritative GBIF taxonomy.</div>',
        unsafe_allow_html=True,
    )

    # Privacy Notice
    st.info(
        "🔒 **Privacy Notice:** Uploaded images are processed in-memory for identification and EXIF metadata is stripped. "
        "Images are not stored in any permanent database or file storage."
    )

    # API Key check banner
    has_api_key = bool(os.getenv("MODEL_API_KEY") or os.getenv("META_API_KEY"))
    if not has_api_key:
        st.warning(
            "⚠️ **Meta API Key Not Configured:** `MODEL_API_KEY` was not found in your environment. "
            "You can run the analysis using the **Demo Fixture Mode** below to test the complete UI workflow."
        )

    # Image Upload Control
    uploaded_file = st.file_uploader(
        "Upload an organism photograph (JPG, JPEG, PNG, WebP — max 8 MB):",
        type=["jpg", "jpeg", "png", "webp"],
        help="Select a clear photograph of an organism.",
        key="identify_file_uploader",
    )

    col_mode, _ = st.columns([1, 1])
    with col_mode:
        use_fixture = st.checkbox(
            "Use Demo Fixture Mode (for testing without live Meta API)",
            value=not has_api_key,
            key="identify_use_fixture",
        )

    if uploaded_file is not None:
        st.image(uploaded_file, caption="Uploaded Observation", width="stretch")

    # Action Button
    analyze_clicked = st.button(
        "🔍 Analyse Image",
        type="primary",
        disabled=(uploaded_file is None),
        key="identify_analyze_btn",
    )

    if analyze_clicked and uploaded_file is not None:
        raw_bytes = uploaded_file.getvalue()
        mime_type = uploaded_file.type or "image/jpeg"

        with st.spinner("Analyzing image features and querying GBIF Backbone Taxonomy..."):
            try:
                if use_fixture:
                    result: VivedexResult = get_demo_fixture_result()
                else:
                    result = backend.process_observation(raw_bytes, mime_type)

                # Cache in session state so navigation doesn't wipe it
                st.session_state["last_identification_result"] = result
                st.session_state["last_is_fixture"] = use_fixture
                st.session_state["obs_saved_flag"] = False

            except ImageValidationError as e:
                st.error(f"❌ **Image Validation Error:** {str(e)}")
                return
            except MetaAPIConfigurationError as e:
                st.error(f"⚙️ **Configuration Error:** {str(e)}")
                return
            except MetaAPIRequestError as e:
                st.error(f"🌐 **Vision Model Error:** {str(e)}")
                return
            except GBIFRequestError as e:
                st.error(f"🏛️ **GBIF Taxonomic Service Error:** {str(e)}")
                return
            except Exception as e:
                st.error(f"⚠️ **Unexpected Error:** {str(e)}")
                return

    # Check for active or cached result
    active_result: VivedexResult | None = st.session_state.get("last_identification_result")
    is_fixture = st.session_state.get("last_is_fixture", False)

    if active_result is not None:
        st.markdown("---")

        # 9. Visible Disclaimer
        st.warning(f"⚠️ **{active_result.disclaimer}**")

        if is_fixture:
            st.warning("⚠️ **DEMO FIXTURE — NOT A LIVE MODEL RESULT:** Generated from offline deterministic test fixtures.")

        # Candidate Info
        candidates = active_result.ai_candidate.candidates
        primary_candidate = candidates[0] if candidates else None

        # 6. Species Result Card
        st.header("🎯 Candidate Identification")
        if primary_candidate and primary_candidate.scientific_name:
            col_name, col_rank = st.columns([3, 1])
            with col_name:
                common_display = f" ({primary_candidate.common_name})" if primary_candidate.common_name else ""
                st.subheader(f"*{primary_candidate.scientific_name}*{common_display}")
            with col_rank:
                st.badge(primary_candidate.suggested_rank or "SPECIES")

            if primary_candidate.uncertainty_note:
                st.info(f"ℹ️ **Confidence & Uncertainty:** {primary_candidate.uncertainty_note}")

            # 7. Evidence Section
            st.subheader("🔍 Morphological Evidence")
            if primary_candidate.visual_evidence:
                for trait in primary_candidate.visual_evidence:
                    st.markdown(f"- {trait}")
            else:
                st.write("No distinct visual traits itemized.")

            # Lookalikes
            if primary_candidate.lookalikes:
                st.subheader("👥 Similar Taxa / Lookalikes")
                for item in primary_candidate.lookalikes:
                    st.markdown(f"- *{item}*")
        else:
            st.error("No candidate organism could be proposed from this photograph.")

        # 8. Separate Taxonomy Section for GBIF
        st.markdown("---")
        st.header("🏛️ GBIF Backbone Taxonomy Reconciliation")
        gbif_match = active_result.taxonomic_resolution

        if gbif_match and gbif_match.match_type != "NONE":
            # Match type warnings
            if gbif_match.match_type == "HIGHERRANK":
                st.warning(
                    f"⚠️ **HIGHER RANK MATCH:** The model proposal could not be matched to an exact species. "
                    f"Reconciled to a higher taxonomic rank ({gbif_match.rank}): *{gbif_match.matched_scientific_name}*."
                )
            elif gbif_match.match_type == "FUZZY":
                st.warning(
                    f"⚠️ **FUZZY NAME MATCH:** Name matched fuzzily with confidence score {gbif_match.gbif_match_score}/100. "
                    "This is an approximate match and may not be the exact species."
                )

            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Accepted Scientific Name:** *{gbif_match.matched_scientific_name or 'N/A'}*")
                st.write(f"**Canonical Name:** *{gbif_match.canonical_name or 'N/A'}*")
                st.write(f"**Taxonomic Rank:** `{gbif_match.rank or 'N/A'}`")
                st.write(f"**Taxonomic Status:** `{gbif_match.status or 'N/A'}`")
                st.write(f"**Match Type:** `{gbif_match.match_type}`")
                st.write(f"**Name Match Score:** `{gbif_match.gbif_match_score or 'N/A'}/100`")
                if gbif_match.usage_key:
                    st.write(f"**GBIF Usage Key:** `{gbif_match.usage_key}`")

            with col2:
                st.write("**Classification Hierarchy:**")
                if gbif_match.hierarchy:
                    for rank_level, name in gbif_match.hierarchy.items():
                        if name:
                            st.write(f"- **{rank_level.capitalize()}:** *{name}*")
                else:
                    st.write("Hierarchy details unavailable.")

            if gbif_match.source_url:
                st.markdown(f"[🔗 View in GBIF Backbone Taxonomy]({gbif_match.source_url})")

            # Mandatory CC BY 4.0 License Attribution
            st.caption(f"Taxonomic Data Source: {gbif_match.provider} — {gbif_match.dataset}")
            st.caption(f"Licence: {gbif_match.licence} | Citation: {gbif_match.attribution}")
            st.caption(f"Reconciled: {gbif_match.retrieved_at}")
        else:
            st.warning("⚠️ No matching taxon could be found in the GBIF Backbone Taxonomy for the proposed name.")

        # Actions: Record Observation & Save to Collection
        st.markdown("---")
        st.subheader("📝 Record Observation & Save to Collection")

        if current_user is not None:
            if st.session_state.get("obs_saved_flag"):
                st.success("✅ This observation has been recorded in your Field Journal and saved to your collection!")
            else:
                with st.form("record_obs_form"):
                    f_notes = st.text_area("Field Notes (morphology, habitat, behavior):", placeholder="Observed in garden hedge in afternoon sunlight...")
                    c_location = st.text_input("Coarse Location (City, Region, or Park):", placeholder="e.g. Richmond Park, London, UK")
                    submit_obs = st.form_submit_button("📓 Record Field Observation", type="primary")

                    if submit_obs:
                        cand_name = (
                            primary_candidate.scientific_name
                            if primary_candidate and primary_candidate.scientific_name
                            else "Unknown Organism"
                        )
                        # Upsert taxon in database if GBIF matched
                        matched_id = None
                        if gbif_match and gbif_match.usage_key:
                            matched_id = collection_service.upsert_taxon_from_gbif(gbif_match, cand_name)

                        obs_rec = collection_service.record_observation(
                            user_id=current_user.id,
                            candidate_scientific_name=cand_name,
                            model_result_json=active_result.ai_candidate.model_dump_json(),
                            gbif_result_json=gbif_match.model_dump_json() if gbif_match else None,
                            matched_taxon_id=matched_id,
                            field_notes=f_notes,
                            coarse_location=c_location,
                            provenance="DEMO DATA" if is_fixture else "LIVE_ANALYSIS",
                        )
                        st.session_state["obs_saved_flag"] = True
                        st.success(f"Observation recorded! ID: `{obs_rec.observation_id}` (Earned XP and evaluated badges)")
                        st.rerun()
        else:
            st.info("Log in or register via the sidebar to record this observation to your Field Journal and earn XP!")

        # 10. JSON Download Action
        st.markdown("---")
        json_output = active_result.to_json(indent=2)
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        st.download_button(
            label="💾 Download Complete JSON Observation",
            data=json_output,
            file_name=f"vivedex-observation-{timestamp_str}.json",
            mime="application/json",
            key="identify_download_json",
        )

