from datetime import datetime, timezone
from src.schemas import (
    ModelIdentificationResult,
    CandidateIdentification,
    GBIFMatchResult,
    VivedexResult,
)


def get_demo_fixture_result() -> VivedexResult:
    """
    Returns a deterministic demo fixture result clearly labeled as NOT A LIVE RESULT.
    Used for testing the UI and offline demonstration when MODEL_API_KEY is not configured.
    """
    model_res = ModelIdentificationResult(
        model="muse-spark-1.3 [DEMO FIXTURE]",
        observation_summary="[DEMO FIXTURE] Adult male House Sparrow (Passer domesticus) perched on a garden stone wall.",
        candidates=[
            CandidateIdentification(
                common_name="House Sparrow",
                scientific_name="Passer domesticus",
                suggested_rank="SPECIES",
                visual_evidence=[
                    "Prominent black bib on throat and upper chest",
                    "Stout, conical seed-eating bill",
                    "Warm chestnut nape markings bordering a grey crown",
                    "Streaked brown and black mantle"
                ],
                lookalikes=[
                    "Passer montanus (Eurasian Tree Sparrow)",
                    "Passer italiae (Italian Sparrow)"
                ],
                uncertainty_note="Diagnostic male plumage features visible clearly; female lookalikes ruled out by black bib."
            )
        ],
        limitations="DEMO FIXTURE — NOT A LIVE MODEL RESULT. AI-generated identifications are candidate suggestions, not confirmed scientific facts."
    )

    gbif_res = GBIFMatchResult(
        provider="Global Biodiversity Information Facility (GBIF)",
        dataset="GBIF Backbone Taxonomy",
        query_name="Passer domesticus",
        matched_scientific_name="Passer domesticus (Linnaeus, 1758)",
        canonical_name="Passer domesticus",
        rank="SPECIES",
        status="ACCEPTED",
        match_type="EXACT",
        gbif_match_score=99,
        usage_key=5231190,
        hierarchy={
            "kingdom": "Animalia",
            "phylum": "Chordata",
            "class": "Aves",
            "order": "Passeriformes",
            "family": "Passeridae",
            "genus": "Passer",
            "species": "Passer domesticus"
        },
        source_url="https://www.gbif.org/species/5231190",
        retrieved_at=datetime.now(timezone.utc).isoformat(),
        licence="CC0 1.0 Universal"
    )

    return VivedexResult(
        timestamp=datetime.now(timezone.utc).isoformat(),
        ai_candidate=model_res,
        taxonomic_resolution=gbif_res,
        disclaimer="DEMO FIXTURE — NOT A LIVE MODEL RESULT. AI-generated identifications are candidate suggestions, not confirmed scientific facts. Taxonomy verified against the GBIF Backbone Taxonomy."
    )

