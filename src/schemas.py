from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class CandidateIdentification(BaseModel):
    """A single candidate taxon identified from the image."""
    common_name: Optional[str] = Field(
        default=None,
        description="Common or vernacular name of the organism, or null if unknown."
    )
    scientific_name: Optional[str] = Field(
        default=None,
        description="Proposed binomial or taxonomic scientific name (e.g. 'Passer domesticus')."
    )
    suggested_rank: Optional[str] = Field(
        default="SPECIES",
        description="Taxonomic rank of the proposal (e.g. SPECIES, GENUS, FAMILY)."
    )
    visual_evidence: List[str] = Field(
        default_factory=list,
        description="Key morphological and visual traits observed in the image that support the candidate."
    )
    lookalikes: List[str] = Field(
        default_factory=list,
        description="Similar or easily confused taxa."
    )
    uncertainty_note: Optional[str] = Field(
        default=None,
        description="Explanation of uncertainty, blur, hidden features, or possible confusion."
    )


class ModelIdentificationResult(BaseModel):
    """Validated response from the multimodal vision model."""
    model: str = Field(
        default="muse-spark-1.3",
        description="Identifier of the model used."
    )
    observation_summary: str = Field(
        description="Brief natural language summary of the visible organism and context."
    )
    candidates: List[CandidateIdentification] = Field(
        default_factory=list,
        description="List of candidate identifications, sorted by plausibility."
    )
    limitations: str = Field(
        default="The result is an AI-generated candidate suggestion, not an authoritative or expert-confirmed identification.",
        description="Mandatory disclaimer emphasizing candidate nature of the output."
    )


class GBIFTaxonHierarchy(BaseModel):
    """Higher classification hierarchy returned by GBIF."""
    kingdom: Optional[str] = None
    phylum: Optional[str] = None
    order: Optional[str] = None
    family: Optional[str] = None
    genus: Optional[str] = None
    species: Optional[str] = None


class GBIFMatchResult(BaseModel):
    """Validated taxonomic reconciliation result from GBIF Backbone Taxonomy."""
    provider: str = Field(
        default="Global Biodiversity Information Facility (GBIF)",
        description="Taxonomic data provider."
    )
    dataset: str = Field(
        default="GBIF Backbone Taxonomy",
        description="Taxonomic dataset referenced."
    )
    query_name: str = Field(
        description="Scientific name queried against the GBIF backbone."
    )
    matched_scientific_name: Optional[str] = Field(
        default=None,
        description="Authoritative scientific name with authorship if available."
    )
    canonical_name: Optional[str] = Field(
        default=None,
        description="Canonical binomial/trinomial without authorship."
    )
    rank: Optional[str] = Field(
        default=None,
        description="Taxon rank resolved by GBIF (e.g. SPECIES, GENUS)."
    )
    status: Optional[str] = Field(
        default=None,
        description="Taxonomic status (e.g. ACCEPTED, SYNONYM, DOUBTFUL)."
    )
    match_type: str = Field(
        description="GBIF match type (EXACT, FUZZY, HIGHERRANK, NONE)."
    )
    gbif_match_score: Optional[int] = Field(
        default=None,
        description="GBIF confidence score (0-100) reflecting taxonomic name resolution, NOT image identification."
    )
    usage_key: Optional[int] = Field(
        default=None,
        description="Unique GBIF taxon identifier key."
    )
    hierarchy: Optional[Dict[str, Optional[str]]] = Field(
        default=None,
        description="Taxonomic classification hierarchy."
    )
    source_url: Optional[str] = Field(
        default=None,
        description="Direct link to GBIF species page."
    )
    retrieved_at: str = Field(
        description="ISO 8601 timestamp when GBIF was queried."
    )
    licence: str = Field(
        default="CC0 1.0 Universal",
        description="License covering GBIF Backbone Taxonomy metadata."
    )


class VivedexResult(BaseModel):
    """Consolidated result schema keeping AI proposal and GBIF match strictly separate."""
    project: str = Field(default="Vivédex")
    version: str = Field(default="0.1.0-mvp")
    timestamp: str = Field(description="ISO 8601 generation timestamp.")
    ai_candidate: ModelIdentificationResult
    taxonomic_resolution: Optional[GBIFMatchResult] = None
    disclaimer: str = Field(
        default="AI-generated identifications are candidate suggestions, not confirmed scientific facts. Taxonomy verified against the GBIF Backbone Taxonomy."
    )

    def to_json(self, indent: int = 2) -> str:
        """Serialize result to formatted JSON string."""
        return self.model_dump_json(indent=indent)

