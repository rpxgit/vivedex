"""Organism identification workflow integrating Meta Muse Spark and GBIF Backbone Taxonomy.

Features an evidence-based 10-step naturalist observation workflow with in-memory EXIF stripping,
diagnostic trait inspection, lookalike differentiation, and field journal logging.
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
from src.ui.theme import escape_text, render_hero_banner


def render_identify_page(
    backend: VivedexBackend,
    collection_service: CollectionService,
) -> None:
    """Render the 10-step naturalist organism identification workflow."""
    inject_custom_styles()
    render_security_notice()

    current_user: AuthenticatedUser | None = st.session_state.get("current_user")

    # Banner
    render_hero_banner(
        title="🌿 Identify Organism Photograph",
        subtitle="10-step observation pipeline: Multimodal vision trait analysis with Meta Muse Spark, reconciled with authoritative GBIF taxonomy.",
    )

    # Step 3: Privacy Notice
    st.markdown(
        """
        <div style="background: #fbf7ee; border: 1px solid #fae8c3; border-left: 4px solid #A66B48; border-radius: 6px; padding: 10px 14px; margin-bottom: 1.2rem; font-size: 0.85rem; color: #554422;">
            🔒 <strong>Naturalist Privacy Safeguard:</strong> Uploaded specimen photographs are processed strictly in volatile memory.
            EXIF metadata, device serials, and precise GPS coordinates are stripped before analysis. Images are never written to permanent storage.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # API Key check
    has_api_key = bool(os.getenv("MODEL_API_KEY") or os.getenv("META_API_KEY"))
    if not has_api_key:
        st.warning(
            "⚠️ **Meta API Key Not Configured:** `MODEL_API_KEY` was not found in your environment. "
            "You can execute the analysis using the **Demo Fixture Mode** below to test the complete workflow."
        )

    # Step 1: Upload an image
    col_upload, col_mode = st.columns([3, 1])
    with col_upload:
        uploaded_file = st.file_uploader(
            "Step 1: Upload Specimen Photograph (JPG, JPEG, PNG, WebP — max 8 MB):",
            type=["jpg", "jpeg", "png", "webp"],
            help="Select a clear photograph of a wild organism.",
            key="identify_uploader",
        )
    with col_mode:
        st.write("")
        st.write("")
        use_fixture = st.checkbox(
            "Demo Fixture Mode",
            value=not has_api_key,
            help="Run offline deterministic analysis without live API credentials.",
            key="identify_fixture_toggle",
        )

    # Step 2: Preview the image
    if uploaded_file is not None:
        st.markdown("#### Step 2: Specimen Preview & EXIF Inspection")
        st.image(uploaded_file, caption="Volatile Memory Specimen Preview", width="stretch")

    # Step 4: Analyse Action Button
    st.write("")
    analyze_clicked = st.button(
        "🔍 Step 4: Execute Naturalist Analysis",
        type="primary",
        disabled=(uploaded_file is None),
        key="identify_run_btn",
    )

    if analyze_clicked and uploaded_file is not None:
        raw_bytes = uploaded_file.getvalue()
        mime_type = uploaded_file.type or "image/jpeg"

        with st.spinner("Analyzing diagnostic traits with Meta Muse Spark and querying GBIF Backbone Taxonomy..."):
            try:
                if use_fixture:
                    result: VivedexResult = get_demo_fixture_result()
                else:
                    result = backend.process_observation(raw_bytes, mime_type)

                st.session_state["last_identification_result"] = result
                st.session_state["last_is_fixture"] = use_fixture
                st.session_state["obs_saved_flag"] = False

            except ImageValidationError as e:
                st.error(f"❌ **Validation Error:** {str(e)}")
                return
            except MetaAPIConfigurationError as e:
                st.error(f"⚙️ **Configuration Error:** {str(e)}")
                return
            except MetaAPIRequestError as e:
                st.error(f"🌐 **Vision Model Error:** {str(e)}")
                return
            except GBIFRequestError as e:
                st.error(f"🏛️ **GBIF Service Error:** {str(e)}")
                return
            except Exception as e:
                st.error(f"⚠️ **Unexpected Error:** {str(e)}")
                return

    # Results Rendering
    active_result: VivedexResult | None = st.session_state.get("last_identification_result")
    is_fixture = st.session_state.get("last_is_fixture", False)

    if active_result is not None:
        st.markdown("---")

        # Distinct Verification State Warnings
        esc_disclaimer = escape_text(active_result.disclaimer)
        st.markdown(
            f"""
            <div style="background: #fff8e6; border: 1px solid #ffe299; border-radius: 6px; padding: 10px 14px; margin-bottom: 12px; font-weight: 600; color: #8a6500;">
                ⚠️ {esc_disclaimer}
            </div>
            """,
            unsafe_allow_html=True,
        )

        if is_fixture:
            st.warning("⚠️ **DEMO FIXTURE — NOT A LIVE MODEL RESULT:** This observation was generated using offline demonstration fixtures.")

        candidates = active_result.ai_candidate.candidates
        primary_candidate = candidates[0] if candidates else None

        # Step 6: Candidate Identification
        st.markdown("### Step 6: Proposed Taxon Candidate (AI Vision)")
        if primary_candidate and primary_candidate.scientific_name:
            col_prop1, col_prop2 = st.columns([3, 1])
            with col_prop1:
                comm_name = escape_text(primary_candidate.common_name or "")
                sci_name = escape_text(primary_candidate.scientific_name)
                label_prefix = f"{comm_name} — " if comm_name else ""
                st.markdown(
                    f"""
                    <div style="font-family: 'Cinzel', serif; font-size: 1.5rem; font-weight: 700; color: #183B32;">
                        {label_prefix}<span class="latin-binomial">*{sci_name}*</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with col_prop2:
                esc_sugg_rank = escape_text(primary_candidate.suggested_rank or "SPECIES")
                st.markdown(f'<span class="rank-pill">{esc_sugg_rank}</span>', unsafe_allow_html=True)

            if primary_candidate.uncertainty_note:
                st.info(f"ℹ️ **Confidence & Diagnostic Uncertainty:** {primary_candidate.uncertainty_note}")

            # Step 5: Visible Evidence Traits
            st.markdown("#### Step 5: Morphological Evidence Traits")
            if primary_candidate.visual_evidence:
                for trait in primary_candidate.visual_evidence:
                    st.markdown(f"- {trait}")

            # Lookalikes
            if primary_candidate.lookalikes:
                st.markdown("#### 👥 Confusing Lookalikes / Related Taxa")
                for item in primary_candidate.lookalikes:
                    esc_item = escape_text(item)
                    st.markdown(f"- <span class='latin-binomial'>*{esc_item}*</span>", unsafe_allow_html=True)
        else:
            st.error("No candidate organism could be proposed from this photograph.")

        # Step 7: GBIF Backbone Taxonomic Reconciliation
        st.markdown("---")
        st.markdown("### Step 7: Authoritative GBIF Backbone Taxonomy Reconciliation")
        gbif_match = active_result.taxonomic_resolution

        if gbif_match and gbif_match.match_type != "NONE":
            # State warnings
            if gbif_match.match_type == "HIGHERRANK":
                st.warning(
                    f"⚠️ **HIGHER RANK MATCH:** Could not resolve to species. Reconciled to higher rank ({gbif_match.rank}): *{gbif_match.matched_scientific_name}*."
                )
            elif gbif_match.match_type == "FUZZY":
                st.warning(
                    f"⚠️ **FUZZY NAME MATCH:** Reconciled fuzzily with match score {gbif_match.gbif_match_score}/100. May not be exact species."
                )

            col_g1, col_g2 = st.columns(2)
            with col_g1:
                st.write(f"**Accepted Scientific Name:** *{gbif_match.matched_scientific_name or 'N/A'}*")
                st.write(f"**Canonical Name:** *{gbif_match.canonical_name or 'N/A'}*")
                st.write(f"**Taxonomic Rank:** `{gbif_match.rank or 'N/A'}`")
                st.write(f"**Status:** `{gbif_match.status or 'N/A'}`")
                st.write(f"**Match Type:** `{gbif_match.match_type}` (Score: {gbif_match.gbif_match_score or 'N/A'}/100)")
                if gbif_match.usage_key:
                    st.write(f"**GBIF Usage Key:** `{gbif_match.usage_key}`")
            with col_g2:
                st.write("**Classification Hierarchy:**")
                if gbif_match.hierarchy:
                    for r_level, val in gbif_match.hierarchy.items():
                        if val:
                            st.write(f"- **{r_level.capitalize()}:** *{val}*")

            st.caption(f"Authority: {gbif_match.provider} &bull; Dataset: {gbif_match.dataset} &bull; Licence: {gbif_match.licence}")
            st.caption(f"Citation: {gbif_match.attribution}")
        else:
            st.warning("⚠️ No matching taxon could be found in the GBIF Backbone Taxonomy for the proposed name.")

        # Steps 8 & 9: Save Observation & Add Field Notes
        st.markdown("---")
        st.markdown("### Steps 8 & 9: Save to My Dex & Add Field Notes")

        if current_user is not None:
            if st.session_state.get("obs_saved_flag"):
                st.success("✅ Observation has been saved to your Field Journal and added to My Dex!")
            else:
                with st.form("save_obs_workflow_form"):
                    notes_input = st.text_area(
                        "Step 9: Naturalist Field Notes (habitat, vegetation, behavior):",
                        placeholder="Recorded in damp deciduous woodland on oak trunk...",
                    )
                    location_input = st.text_input(
                        "Coarse Locality (City, Region, or Nature Reserve — never exact GPS):",
                        placeholder="e.g. Sherwood Forest, Nottinghamshire, UK",
                    )
                    submit_obs = st.form_submit_button("📓 Record Field Observation to Journal", type="primary")

                    if submit_obs:
                        cand_name = (
                            primary_candidate.scientific_name
                            if primary_candidate and primary_candidate.scientific_name
                            else "Unknown Organism"
                        )
                        matched_id = None
                        if gbif_match and gbif_match.usage_key:
                            matched_id = collection_service.upsert_taxon_from_gbif(gbif_match, cand_name)

                        obs_rec = collection_service.record_observation(
                            user_id=current_user.id,
                            candidate_scientific_name=cand_name,
                            model_result_json=active_result.ai_candidate.model_dump_json(),
                            gbif_result_json=gbif_match.model_dump_json() if gbif_match else None,
                            matched_taxon_id=matched_id,
                            field_notes=notes_input,
                            coarse_location=location_input,
                            provenance="DEMO DATA" if is_fixture else "LIVE_ANALYSIS",
                        )
                        st.session_state["obs_saved_flag"] = True
                        st.success(f"Observation recorded in Journal! ID: `{obs_rec.observation_id}` (+XP and badge evaluation completed)")
                        st.rerun()
        else:
            st.info("Log in or register via the sidebar to record this observation to your personal journal and earn naturalist XP.")

        # Step 10: Export JSON Record
        st.markdown("---")
        st.markdown("### Step 10: Export Scientific Observation")
        json_payload = active_result.to_json(indent=2)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        st.download_button(
            label="💾 Download Complete JSON Observation Record",
            data=json_payload,
            file_name=f"vivedex-observation-{stamp}.json",
            mime="application/json",
            key="identify_export_json_btn",
        )
