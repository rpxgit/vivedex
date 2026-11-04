import urllib.request
import urllib.parse
import urllib.error
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from src.schemas import GBIFMatchResult


class GBIFRequestError(RuntimeError):
    """Raised when communication with GBIF API fails."""
    pass


class GBIFAdapter:
    """
    Adapter for the GBIF Species Name Match API.
    
    Documented endpoint: https://api.gbif.org/v1/species/match
    """

    MATCH_ENDPOINT = "https://api.gbif.org/v1/species/match"
    SPECIES_PAGE_BASE = "https://www.gbif.org/species"

    def __init__(self, timeout: int = 15):
        self.timeout = timeout

    def match_species(self, scientific_name: str) -> GBIFMatchResult:
        """
        Query GBIF Species Match API for a scientific name.
        
        Preserves:
        - Matched scientific name
        - Canonical name
        - Taxonomic rank
        - Taxonomic status
        - Match type
        - GBIF match score / confidence field
        - GBIF usage key
        - GBIF source URL
        - Retrieval time
        - Taxonomic hierarchy
        
        Args:
            scientific_name: The candidate scientific name proposed by the model.
            
        Returns:
            GBIFMatchResult with preserved fields and license metadata.
            
        Raises:
            GBIFRequestError: if network or HTTP request fails.
        """
        if not scientific_name or not scientific_name.strip():
            retrieved_at = datetime.now(timezone.utc).isoformat()
            return GBIFMatchResult(
                query_name=scientific_name or "",
                match_type="NONE",
                retrieved_at=retrieved_at
            )

        clean_name = scientific_name.strip()
        params = urllib.parse.urlencode({"name": clean_name})
        url = f"{self.MATCH_ENDPOINT}?{params}"

        headers = {
            "Accept": "application/json",
            "User-Agent": "Vivedex-MVP/0.1.0"
        }
        req = urllib.request.Request(url, headers=headers, method="GET")

        retrieved_at = datetime.now(timezone.utc).isoformat()

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                resp_bytes = resp.read()
                data = json.loads(resp_bytes.decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            raise GBIFRequestError(f"GBIF Species API returned HTTP {e.code}: {err_body}") from e
        except urllib.error.URLError as e:
            raise GBIFRequestError(f"Failed to connect to GBIF Species API: {str(e.reason)}") from e
        except Exception as e:
            raise GBIFRequestError(f"Error querying GBIF Species API: {str(e)}") from e

        match_type = data.get("matchType", "NONE")
        usage_key = data.get("usageKey")
        source_url = f"{self.SPECIES_PAGE_BASE}/{usage_key}" if usage_key else None

        # Build taxonomic classification hierarchy
        hierarchy = {}
        for rank_key in ("kingdom", "phylum", "class", "order", "family", "genus", "species"):
            if rank_key in data:
                hierarchy[rank_key] = data[rank_key]

        return GBIFMatchResult(
            provider="Global Biodiversity Information Facility (GBIF)",
            dataset="GBIF Backbone Taxonomy",
            query_name=clean_name,
            matched_scientific_name=data.get("scientificName"),
            canonical_name=data.get("canonicalName"),
            rank=data.get("rank"),
            status=data.get("status"),
            match_type=match_type,
            gbif_match_score=data.get("confidence"),
            usage_key=usage_key,
            hierarchy=hierarchy if hierarchy else None,
            source_url=source_url,
            retrieved_at=retrieved_at,
            licence="CC BY 4.0",
            attribution="GBIF Secretariat (2023). GBIF Backbone Taxonomy. Checklist dataset. https://doi.org/10.15468/39omei"
        )

