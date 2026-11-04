import os
import streamlit as st
from PIL import Image

from src.backend import VivedexBackend
from src.image_processor import ImageValidationError
from src.meta_adapter import MetaAPIConfigurationError, MetaAPIRequestError
from src.gbif_adapter import GBIFRequestError
from src.fixtures import get_demo_fixture_result

st.set_page_config(
    page_title="Vivédex — Biodiversity Identification & Taxonomic Reconciliation",
    page_icon="🌿",
    layout="centered"
)

# 1. Title and Purpose
st.title("🌿 Vivédex")
st.subheader("Cautious, explainable organism identification backed by authoritative GBIF taxonomy.")

# 3. Privacy Note
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

# 2. Image Upload Control
uploaded_file = st.file_uploader(
    "Upload an organism photograph (JPG, JPEG, PNG, WebP — max 8 MB):",
    type=["jpg", "jpeg", "png", "webp"],
    help="Select a clear photograph of an organism."
)

col_mode, _ = st.columns([1, 1])
with col_mode:
    use_fixture = st.checkbox(
        "Use Demo Fixture Mode (for testing without live Meta API)",
        value=not has_api_key
    )

if uploaded_file is not None:
    st.image(uploaded_file, caption="Uploaded Observation", width="stretch")

# 4. Action Button
analyze_clicked = st.button("🔍 Analyse Image", type="primary", disabled=(uploaded_file is None))

if analyze_clicked and uploaded_file is not None:
    image_bytes = uploaded_file.getvalue()
    mime_type = uploaded_file.type or "image/jpeg"

    if use_fixture:
        with st.spinner("Processing image via Demo Fixture..."):
            result = get_demo_fixture_result()
            st.session_state["result"] = result
            st.session_state["is_fixture"] = True
    else:
        # Live run
        with st.spinner("Analyzing image with Meta Muse Spark and verifying against GBIF..."):
            backend = VivedexBackend()
            try:
                result = backend.process_observation(image_bytes, mime_type)
                st.session_state["result"] = result
                st.session_state["is_fixture"] = False
            except ImageValidationError as e:
                st.error(f"❌ **Invalid Image:** {str(e)}")
            except MetaAPIConfigurationError as e:
                st.error(f"⚙️ **Configuration Error:** {str(e)}")
            except MetaAPIRequestError as e:
                st.error(f"🤖 **Model API Error:** {str(e)}")
            except Exception as e:
                st.error(f"⚠️ **Unexpected Error:** {str(e)}")

# Display Results
if "result" in st.session_state:
    res = st.session_state["result"]
    is_fixture = st.session_state.get("is_fixture", False)

    st.markdown("---")

    # Fixture notification banner
    if is_fixture:
        st.warning("⚠️ **DEMO FIXTURE — NOT A LIVE MODEL RESULT**")

    # 9. Visible Warning
    st.warning("⚠️ **AI-generated candidate. Not expert-verified.**")

    # 6. Species Result Card
    st.subheader("📋 Candidate Identification (Meta Model API)")
    ai = res.ai_candidate
    st.markdown(f"**Model:** `{ai.model}`")
    st.markdown(f"**Observation Summary:** {ai.observation_summary}")

    if ai.candidates:
        top = ai.candidates[0]
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Common Name:** {top.common_name or 'Not specified'}")
            st.markdown(f"**Scientific Name:** *{top.scientific_name or 'Not identified'}*")
        with c2:
            st.markdown(f"**Suggested Rank:** `{top.suggested_rank or 'SPECIES'}`")

        # 7. Visible Evidence Section
        st.markdown("#### 🔍 Visible Morphological Evidence")
        if top.visual_evidence:
            for trait in top.visual_evidence:
                st.markdown(f"- {trait}")
        else:
            st.markdown("*No specific visible traits reported.*")

        if top.lookalikes:
            st.markdown("#### 👥 Lookalikes & Similar Taxa")
            for lookalike in top.lookalikes:
                st.markdown(f"- {lookalike}")

        if top.uncertainty_note:
            st.markdown(f"**Uncertainty Note:** {top.uncertainty_note}")
    else:
        st.markdown("*No candidate species could be identified.*")

    st.markdown(f"*{ai.limitations}*")

    st.markdown("---")

    # 8. Separate Taxonomy Section for GBIF Result
    st.subheader("🏛️ Taxonomic Reconciliation (GBIF Backbone Taxonomy)")
    gbif = res.taxonomic_resolution

    if gbif is not None:
        if gbif.match_type == "SERVICE_UNAVAILABLE":
            st.error("⚠️ GBIF taxonomic service was temporarily unavailable. AI candidate retained above.")
        elif gbif.match_type == "NONE":
            st.warning("⚠️ **Taxonomic match not resolved:** The proposed name could not be matched in the GBIF Backbone Taxonomy.")
            st.markdown(f"Queried Name: *{gbif.query_name}*")
            st.markdown("[Search GBIF manually](https://www.gbif.org)")
        else:
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                st.markdown(f"**Matched Scientific Name:** *{gbif.matched_scientific_name}*")
                st.markdown(f"**Canonical Name:** *{gbif.canonical_name}*")
                st.markdown(f"**Taxonomic Rank:** `{gbif.rank}`")
            with col_g2:
                st.markdown(f"**Taxonomic Status:** `{gbif.status}`")
                st.markdown(f"**GBIF Match Type:** `{gbif.match_type}`")
                # Do not confuse GBIF match score with identification confidence
                st.markdown(f"**GBIF Match Score:** `{gbif.gbif_match_score}/100` *(name string match metric)*")

            # Explicit distinction for non-exact or higher-rank matches
            if gbif.match_type == "HIGHERRANK" or (gbif.rank and gbif.rank.upper() not in ("SPECIES", "SUBSPECIES", "VARIETY")):
                st.info(f"ℹ️ **Taxonomic Note:** Matched at higher rank (`{gbif.rank}`), not a species-level confirmation.")
            elif gbif.match_type == "FUZZY":
                st.info("ℹ️ **Taxonomic Note:** Matched via fuzzy name resolution. Check spelling or author citation.")

            if gbif.usage_key:
                st.markdown(f"**GBIF Usage Key:** `{gbif.usage_key}`")
            if gbif.source_url:
                st.markdown(f"🔗 [View on GBIF Species Page]({gbif.source_url})")

            if gbif.hierarchy:
                st.markdown("#### 🌳 Classification Hierarchy")
                hierarchy_str = " → ".join(
                    [f"**{k.capitalize()}**: {v}" for k, v in gbif.hierarchy.items() if v]
                )
                st.markdown(hierarchy_str)

            st.caption(
                f"Source: {gbif.provider} ({gbif.dataset}) | Licence: {gbif.licence} | Retrieved: {gbif.retrieved_at}"
            )
    else:
        st.info("No taxonomic verification performed.")

    st.markdown("---")

    # 10. JSON Download Action
    st.subheader("💾 Export Observation Record")
    json_export = res.to_json(indent=2)
    st.download_button(
        label="📥 Download JSON Report",
        data=json_export,
        file_name=f"vivedex-observation-{res.timestamp.replace(':', '-')}.json",
        mime="application/json",
        type="secondary"
    )

    with st.expander("View Raw JSON Output"):
        st.json(json_export)

