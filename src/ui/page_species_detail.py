"""Dedicated Species Detail view for Vivédex.

Presents prominent specimen photography, authoritative GBIF Backbone Taxonomy,
diagnostic evidence, personal collection status, and community sightings.
"""

from __future__ import annotations

import streamlit as st

from src.auth import AuthenticatedUser
from src.collection_service import CollectionService
from src.database import Database
from src.knowledge_graph import KnowledgeGraphService
from src.ui.common import inject_custom_styles, render_breadcrumbs, render_security_notice
from src.ui.theme import escape_text

# Curated specimen photography catalog (strictly documented source, author, CC licence)
CURATED_SPECIMEN_ASSETS = {
    5231190: {  # Passer domesticus
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/Passer_domesticus_male_15.jpg/800px-Passer_domesticus_male_15.jpg",
        "author": "Pierre-Selim",
        "licence": "CC BY-SA 3.0",
        "source": "Wikimedia Commons / Museum specimen archive",
        "description": "Adult male House Sparrow displaying characteristic black throat bib, chestnut nape trim, and conical seed-eating bill.",
        "visible_traits": [
            "Prominent black throat and upper breast bib (breeding plumage)",
            "Stout, conical bill adapted for granivory",
            "Rich chestnut and grey crown patterning",
            "Mantle streaked with warm sepia and black",
        ],
        "similar_taxa": ["Passer montanus (Tree Sparrow)", "Passer italiae (Italian Sparrow)"],
    },
    1956599: {  # Erannis defoliaria
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/22/Erannis_defoliaria_%28Mottled_Umber%29_%2822180862024%29.jpg/800px-Erannis_defoliaria_%28Mottled_Umber%29_%2822180862024%29.jpg",
        "author": "Peter Stronach",
        "licence": "CC BY 2.0",
        "source": "Wikimedia Commons / NHM Lepidoptera Specimen",
        "description": "Male Mottled Umber moth showing broad ochre wings with variable dark dusting and wavy postmedian lines.",
        "visible_traits": [
            "Broad ochre-yellow forewings with fine dark dusting",
            "Distinct variable postmedian and antemedian transverse bands",
            "Feathered antennae visible on males",
            "Cryptic resting posture on temperate deciduous bark",
        ],
        "similar_taxa": ["Colotois pennaria (Feathered Thorn)", "Agriopis aurantiaria (Scarce Umber)"],
    },
    5133088: {  # Danaus plexippus
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/73/Monarch_In_May.jpg/800px-Monarch_In_May.jpg",
        "author": "Kenneth Dwain Harrelson",
        "licence": "CC BY-SA 2.5",
        "source": "Wikimedia Commons",
        "description": "Iconic migratory nymphalid butterfly with tawny-orange wings outlined in bold black venation and white marginal dots.",
        "visible_traits": [
            "Brilliant tawny-orange dorsal wing surfaces",
            "Heavy black venation spanning all wing cells",
            "Double row of white spots along black wing margins",
            "Scent patch on hindwing vein in males",
        ],
        "similar_taxa": ["Limenitis archippus (Viceroy)", "Danaus gilippus (Queen)"],
    },
    1341976: {  # Apis mellifera
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/Apis_mellifera_Western_honey_bee.jpg/800px-Apis_mellifera_Western_honey_bee.jpg",
        "author": "Muhammad Mahdi Karim",
        "licence": "CC BY-SA 3.0",
        "source": "Wikimedia Commons",
        "description": "Eusocial pollinator showing golden-brown abdomen banding, pollen basket (corbicula) on hind tibia, and plumose body hairs.",
        "visible_traits": [
            "Golden-amber and dark brown alternating abdominal bands",
            "Pollen basket (corbicula) present on posterior tibiae",
            "Compound eyes with microscopic inter-ommatidial setae",
            "Forewing with characteristic submarginal venation cells",
        ],
        "similar_taxa": ["Bombus species (Bumblebees)", "Eristalis tenax (Drone Fly mimic)"],
    },
    5219173: {  # Canis lupus
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/68/Eurasian_wolf_2.jpg/800px-Eurasian_wolf_2.jpg",
        "author": "Mas3cf",
        "licence": "CC BY-SA 3.0",
        "source": "Wikimedia Commons",
        "description": "Apex apex carnivore displaying thick grizzly-grey pelage, broad muzzle, upright triangular ears, and large paw structure.",
        "visible_traits": [
            "Robust cranial structure with broad frontal rostrum",
            "Triangular erect pinnae with dense inner fur",
            "Long limbs with large splayed footpads adapted for snow pacing",
            "Bushy tail with black terminal gland marking",
        ],
        "similar_taxa": ["Canis latrans (Coyote)", "Canis aureus (Golden Jackal)"],
    },
}


def render_species_detail_page(
    db: Database,
    collection_service: CollectionService,
    kg_service: KnowledgeGraphService,
    taxon_id: int,
) -> None:
    """Render the full specimen detail page for a given taxon ID."""
    inject_custom_styles()
    render_security_notice()

    current_user: AuthenticatedUser | None = st.session_state.get("current_user")
    taxon = kg_service.get_taxon_by_id(taxon_id)

    if not taxon:
        st.error(f"Taxon with identifier `{taxon_id}` was not found in the platform database.")
        if st.button("← Return to Explore Dex"):
            st.session_state["selected_taxon_id"] = None
            st.rerun()
        return

    # Breadcrumb Navigation
    render_breadcrumbs(
        [
            ("Expedition Hub", "home"),
            ("Explore Dex", "explore"),
            (taxon.scientific_name, None),
        ]
    )

    # Asset Data
    specimen_asset = CURATED_SPECIMEN_ASSETS.get(taxon_id, {})
    img_url = specimen_asset.get("image_url")
    author = specimen_asset.get("author", "GBIF Data Provider")
    licence_img = specimen_asset.get("licence", "CC BY 4.0")
    description = specimen_asset.get("description", "Taxonomic entry verified via the GBIF Backbone Taxonomy.")
    traits = specimen_asset.get("visible_traits", [])
    similar = specimen_asset.get("similar_taxa", [])

    # Main Header
    esc_common = escape_text(taxon.common_name)
    esc_sci = escape_text(taxon.scientific_name)
    esc_fam = escape_text(taxon.family or "Biota")
    esc_rank = escape_text(taxon.rank or "SPECIES")
    common_title = f"{esc_common} — " if esc_common else ""
    st.markdown(
        f"""
        <div style="margin-bottom: 1.5rem;">
            <div style="font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; color: #718568; font-weight: 700;">
                {esc_fam} &bull; <span class="rank-pill">{esc_rank}</span>
            </div>
            <h1 style="margin: 0.2rem 0; font-size: 2.4rem;">{common_title}<span class="latin-binomial">*{esc_sci}*</span></h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_specimen, col_meta = st.columns([11, 9])

    with col_specimen:
        # Specimen Image Frame
        if img_url:
            st.image(img_url, caption=f"Specimen: {taxon.scientific_name} (Photo: {author}, {licence_img})", width="stretch")
        else:
            st.markdown(
                f"""
                <div style="background: #f4efe4; border: 2px dashed #ded6c5; border-radius: 10px; height: 320px; display: flex; align-items: center; justify-content: center; text-align: center; color: #777E73; padding: 20px;">
                    <div>
                        <div style="font-size: 2.5rem; margin-bottom: 8px;">🌿</div>
                        <div style="font-family: 'Cinzel', serif; font-size: 1.1rem; font-weight: 700; color: #183B32;">{esc_sci}</div>
                        <div style="font-size: 0.8rem; margin-top: 4px;">Morphological photographic specimen on file in GBIF archive.</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Overview Description
        st.markdown("### 📖 Natural History Description")
        st.write(description)

        # Diagnostic Characteristics Section
        if traits:
            st.markdown("### 🔍 Diagnostic Characteristics (Identification Evidence)")
            for t in traits:
                st.markdown(f"- {t}")

        # Lookalikes Section
        if similar:
            st.markdown("### 👥 Similar Taxa & Lookalikes")
            for sim in similar:
                esc_sim = escape_text(sim)
                st.markdown(f"- <span class='latin-binomial'>*{esc_sim}*</span>", unsafe_allow_html=True)

    with col_meta:
        # Collection Status Card
        in_collection = False
        enc_count = 0
        first_enc = None

        if current_user is not None:
            with db.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT encounter_count, first_encounter_at FROM collections WHERE user_id = ? AND taxon_id = ?;",
                    (current_user.id, taxon_id),
                )
                col_row = cursor.fetchone()
                if col_row:
                    in_collection = True
                    enc_count = col_row["encounter_count"]
                    first_enc = col_row["first_encounter_at"]

        st.markdown(
            f"""
            <div class="specimen-card">
                <div style="font-size: 0.78rem; font-weight: 700; text-transform: uppercase; color: #777E73; margin-bottom: 4px;">Personal Collection Status</div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="font-size: 1.15rem; font-weight: 700; color: #183B32;">{'✅ IN MY DEX' if in_collection else '⚪ NOT YET RECORDED'}</span>
                    <span class="dex-collected-tag">Encounters: {enc_count}</span>
                </div>
                {f'<div style="font-size: 0.8rem; color: #666;">First recorded: {first_enc[:10]}</div>' if first_enc else '<div style="font-size: 0.8rem; color: #888;">Record an encounter to add this species to your Dex.</div>'}
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Save to Dex Action
        if current_user is not None:
            col_save1, col_save2 = st.columns([1, 1])
            with col_save1:
                enc_note = st.text_input("Encounter note:", placeholder="Habitat or behavior...", key=f"dtl_note_{taxon_id}")
            with col_save2:
                st.write("")
                st.write("")
                if st.button("📚 Record Encounter in My Dex", type="primary", key=f"dtl_save_{taxon_id}"):
                    collection_service.save_to_collection(current_user.id, taxon_id, enc_note)
                    st.success("Encounter recorded! XP and badges evaluated.")
                    st.rerun()
        else:
            st.info("Log in or register via the sidebar to record this organism in your personal Dex.")

        # Taxonomic Hierarchy
        st.markdown("### 🏛️ Taxonomic Classification (GBIF)")
        lineage = kg_service.get_taxon_lineage(taxon_id)
        if lineage:
            for node in lineage:
                is_target = node.taxon_id == taxon_id
                prefix = "➔ " if is_target else "&nbsp;&nbsp;&bull; "
                weight = "font-weight: 700; color: #183B32;" if is_target else "color: #555;"
                esc_n_rank = escape_text(node.rank or "Rank")
                esc_n_sci = escape_text(node.scientific_name)
                st.markdown(
                    f"{prefix}<span style='font-size:0.85rem;'>{esc_n_rank}:</span> <strong style='{weight}'>*{esc_n_sci}*</strong>",
                    unsafe_allow_html=True,
                )

        st.markdown("---")
        # Metadata & Attribution Box
        st.markdown("### 📜 Provenance & Licensing")
        esc_prov = escape_text(taxon.data_provider)
        esc_key = escape_text(str(taxon.taxon_id))
        esc_stat = escape_text(taxon.status or "ACCEPTED")
        esc_lic = escape_text(taxon.licence)
        esc_attr = escape_text(taxon.attribution)
        esc_ret = escape_text(taxon.retrieved_at[:10] if taxon.retrieved_at else "")
        st.markdown(
            f"""
            <div class="provenance-tag">
                <strong>Taxonomic Authority:</strong> {esc_prov}<br/>
                <strong>Dataset:</strong> GBIF Backbone Taxonomy<br/>
                <strong>Usage Key:</strong> {esc_key}<br/>
                <strong>Status:</strong> {esc_stat}<br/>
                <strong>Licence:</strong> {esc_lic} (<a href="https://creativecommons.org/licenses/by/4.0/" target="_blank" rel="noopener noreferrer">CC BY 4.0</a>)<br/>
                <strong>Citation:</strong> {esc_attr}<br/>
                <strong>Retrieved:</strong> {esc_ret}
            </div>
            """,
            unsafe_allow_html=True,
        )

        if taxon.source_id or taxon.taxon_id:
            gbif_key = taxon.taxon_id
            st.markdown(f"[🌐 Inspect on Official GBIF Species Portal](https://www.gbif.org/species/{gbif_key})")

    # Community Observations Section
    st.markdown("---")
    st.subheader("📋 Recorded Community Field Sightings")
    with db.connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT o.observation_id, o.observation_timestamp, o.coarse_location,
                   o.field_notes, o.moderation_status, o.provenance, u.username
            FROM observations o
            JOIN users u ON o.owner_id = u.id
            WHERE o.matched_taxon_id = ? AND o.moderation_status = 'ACCEPTED_FOR_CATALOG'
            ORDER BY o.observation_timestamp DESC
            LIMIT 5;
            """,
            (taxon_id,),
        )
        obs_rows = cursor.fetchall()

    if obs_rows:
        for row in obs_rows:
            tag = f"[{escape_text(row['provenance'])}] " if row["provenance"] == "DEMO DATA" else ""
            esc_u = escape_text(row['username'])
            esc_ts = escape_text(row['observation_timestamp'][:10] if row['observation_timestamp'] else "")
            esc_status = escape_text(row['moderation_status'])
            esc_fn = escape_text(row['field_notes'] or 'No natural history notes entered.')
            loc_div = f'<div style="font-size:0.75rem; color:#A66B48; margin-top:2px;">Location: {escape_text(row["coarse_location"])}</div>' if row['coarse_location'] else ''
            st.markdown(
                f"""
                <div style="background:#ffffff; border:1px solid #e3ddd0; border-radius:6px; padding:10px 14px; margin-bottom:8px;">
                    <div style="display:flex; justify-content:space-between; font-size:0.8rem; color:#777E73;">
                        <span>{tag}Observer: <strong>@{esc_u}</strong> &bull; {esc_ts}</span>
                        <span class="status-pill-{esc_status.lower() if 'status-pill-' + esc_status.lower() in ['status-pill-accepted', 'status-pill-pending'] else 'pending'}">{esc_status}</span>
                    </div>
                    <div style="font-size:0.9rem; margin-top:4px;">{esc_fn}</div>
                    {loc_div}
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("No field observations recorded for this species yet. Use **Identify** to record the first encounter!")

    st.markdown("---")
    if st.button("← Return to Full Species Explorer"):
        st.session_state["selected_taxon_id"] = None
        st.rerun()
