from datetime import datetime, timezone
from typing import Optional

from src.image_processor import validate_image, preprocess_image, ImageValidationError
from src.meta_adapter import MetaAPIAdapter, MetaAPIConfigurationError, MetaAPIRequestError
from src.gbif_adapter import GBIFAdapter, GBIFRequestError
from src.schemas import VivedexResult, ModelIdentificationResult, GBIFMatchResult


class VivedexBackend:
    """
    Core backend orchestrating the Vivedex identification and taxonomic verification pipeline.
    """

    def __init__(self, meta_adapter: Optional[MetaAPIAdapter] = None, gbif_adapter: Optional[GBIFAdapter] = None):
        self.meta_adapter = meta_adapter or MetaAPIAdapter()
        self.gbif_adapter = gbif_adapter or GBIFAdapter()

    def process_observation(
        self,
        image_bytes: bytes,
        mime_type: str,
        api_key: Optional[str] = None,
    ) -> VivedexResult:
        """
        Execute the full MVP pipeline:
        1. Validate format & size.
        2. Preprocess and strip EXIF in-memory.
        3. Query Meta Model API for candidate identification (using explicit user key or env fallback).
        4. Reconcile candidate scientific name with GBIF Backbone Taxonomy.
        5. Return consolidated VivedexResult keeping model proposal and GBIF match separate.
        """
        # 1. Validation
        validate_image(image_bytes, mime_type)

        # 2. In-memory preprocessing and EXIF removal
        clean_bytes, clean_mime = preprocess_image(image_bytes)

        # 3. Meta Model API identification
        model_result = self.meta_adapter.identify_image(clean_bytes, clean_mime, api_key=api_key)

        # 4. Taxonomic verification with GBIF
        gbif_result = None
        if model_result.candidates:
            top_candidate = model_result.candidates[0]
            if top_candidate.scientific_name:
                try:
                    gbif_result = self.gbif_adapter.match_species(top_candidate.scientific_name)
                except GBIFRequestError:
                    # Graceful degradation if GBIF fails: preserve model identification
                    now = datetime.now(timezone.utc).isoformat()
                    gbif_result = GBIFMatchResult(
                        query_name=top_candidate.scientific_name,
                        match_type="SERVICE_UNAVAILABLE",
                        retrieved_at=now
                    )

        # 5. Consolidated result
        timestamp = datetime.now(timezone.utc).isoformat()
        return VivedexResult(
            timestamp=timestamp,
            ai_candidate=model_result,
            taxonomic_resolution=gbif_result
        )

