# Vivédex MVP Specification

## 1. Executive Summary and Objective

Vivédex is a lightweight biodiversity identification and verification tool for the hackathon MVP. The user uploads an organism photograph. Meta Muse Spark analyses the image and proposes candidate identifications with visible evidence, lookalikes, and uncertainty notes. Vivédex checks the leading scientific name against the Global Biodiversity Information Facility (GBIF) taxonomic backbone API. Vivédex displays the model's candidate identification separately from the GBIF taxonomic match. The user can export a consolidated JSON report.

---

## 2. Fixed MVP Workflow

The MVP executes a deterministic five-step workflow:

1. **User Image Input:**
   - The user uploads one JPG, JPEG, PNG, or WebP image via Streamlit.
   - The image must not exceed 8 MB.
   - The application removes EXIF metadata when feasible.
   - The application does not save the image to permanent storage.

2. **Multimodal AI Identification:**
   - Model: `muse-spark-1.3` via Meta Model API (`POST https://api.meta.ai/v1/chat/completions`).
   - Authentication: HTTP header `Authorization: Bearer $MODEL_API_KEY`.
   - Payload: Structured user message containing the image formatted as a Base64 data URL (`data:image/...;base64,...`).
   - Instruction: Strict JSON output containing proposed candidate name(s), visible traits, lookalikes, and uncertainty notes. No invented numeric probabilities.

3. **Taxonomic Reconciliation with GBIF:**
   - Endpoint: GBIF Species Match API (`GET https://api.gbif.org/v1/species/match?name=...`).
   - Reconciliation verifies the candidate scientific name against the GBIF Taxonomic Backbone.
   - Extracts `scientificName`, `canonicalName`, `rank`, `status`, `matchType`, `confidence`, `usageKey`, and higher classification hierarchy.

4. **Provenance and Licence Attachment:**
   - Enforces `Vivédex Data Licensing and Provenance Policy.md`.
   - Labels AI output as a candidate result, not a confirmed identification.
   - Attaches model identifier, provider, and timestamp.
   - Attaches GBIF taxonomic backbone dataset reference, source URL, retrieval timestamp, and CC0 licence attribution.

5. **Presentation and Export:**
   - Displays uploaded image preview.
   - Displays AI candidate identification card.
   - Displays GBIF taxonomic match card separately.
   - Displays prominent disclaimer: Result is an aid, not expert verification.
   - Provides one-click JSON report download.

---

## 3. Data Contracts

### 3.1 Function: `identify_image(image_bytes: bytes, mime_type: str) -> dict`

The model returns valid JSON structured according to this contract:

```json
{
  "model": "muse-spark-1.3",
  "observation_summary": "Adult male house sparrow perched on a stone ledge.",
  "candidates": [
    {
      "common_name": "House Sparrow",
      "scientific_name": "Passer domesticus",
      "suggested_rank": "SPECIES",
      "visual_evidence": [
        "Robust seed-eating conical bill",
        "Black bib on throat and upper breast",
        "Grey crown with chestnut nape borders",
        "Streaked brown and black mantle"
      ],
      "lookalikes": [
        "Passer montanus (Eurasian Tree Sparrow)",
        "Passer italiae (Italian Sparrow)"
      ],
      "uncertainty_note": "Plumage clear; female lookalikes ruled out by black bib."
    }
  ],
  "limitations": "The result is a candidate, not expert confirmation."
}
```

### 3.2 Function: `resolve_taxon(scientific_name: str) -> dict`

GBIF species match returns structured taxonomy according to this contract:

```json
{
  "scientificName": "Passer domesticus (Linnaeus, 1758)",
  "canonicalName": "Passer domesticus",
  "rank": "SPECIES",
  "status": "ACCEPTED",
  "matchType": "EXACT",
  "confidence": 99,
  "usageKey": 5231190,
  "hierarchy": {
    "kingdom": "Animalia",
    "phylum": "Chordata",
    "class": "Aves",
    "order": "Passeriformes",
    "family": "Passeridae",
    "genus": "Passer"
  },
  "source_url": "https://www.gbif.org/species/5231190",
  "retrieved_at": "2026-11-04T17:20:01Z",
  "licence": "CC0 1.0 Universal"
}
```

*Note:* `confidence` from GBIF is a string-matching score against taxonomic names. It is not an image identification probability.

### 3.3 Final Consolidated JSON Export Contract

```json
{
  "project": "Vivédex",
  "version": "0.1.0-mvp",
  "timestamp": "2026-11-04T17:20:01Z",
  "ai_candidate": {
    "model": "muse-spark-1.3",
    "observation_summary": "Adult male house sparrow perched on a stone ledge.",
    "candidates": [
      {
        "common_name": "House Sparrow",
        "scientific_name": "Passer domesticus",
        "suggested_rank": "SPECIES",
        "visual_evidence": [
          "Robust seed-eating conical bill",
          "Black bib on throat and upper breast"
        ],
        "lookalikes": [
          "Passer montanus"
        ],
        "uncertainty_note": "Plumage clear; female lookalikes ruled out by black bib."
      }
    ],
    "limitations": "The result is a candidate, not expert confirmation."
  },
  "taxonomic_resolution": {
    "provider": "Global Biodiversity Information Facility (GBIF)",
    "dataset": "GBIF Backbone Taxonomy",
    "query_name": "Passer domesticus",
    "matched_scientific_name": "Passer domesticus (Linnaeus, 1758)",
    "canonical_name": "Passer domesticus",
    "rank": "SPECIES",
    "status": "ACCEPTED",
    "match_type": "EXACT",
    "gbif_match_score": 99,
    "usage_key": 5231190,
    "source_url": "https://www.gbif.org/species/5231190",
    "retrieved_at": "2026-11-04T17:20:01Z",
    "licence": "CC0 1.0 Universal"
  },
  "disclaimer": "AI-generated identifications are candidate suggestions, not confirmed scientific facts. Taxonomy verified against the GBIF Backbone Taxonomy."
}
```

---

## 4. Failure States and Error Handling

1. **Missing or Unconfigured Meta API Key:**
   - The system checks for `MODEL_API_KEY`.
   - If missing, the app displays a clear notification banner without crashing.
   - A fixture/demo mode allows testing without external Meta API calls.

2. **Network or Service Failure Calling Meta API:**
   - Error code: `META_API_UNAVAILABLE`.
   - System presents an explicit error message to the user with a retry button.

3. **Invalid Model Output:**
   - If the model returns malformed JSON or fails the schema check, the system triggers one retry.
   - If retry fails, the system returns `INVALID_MODEL_OUTPUT`.

4. **GBIF Name Match Fails (`matchType: NONE`):**
   - The AI candidate name is preserved and displayed.
   - The GBIF card displays "Taxonomic match not resolved in GBIF Backbone".
   - System provides a manual link to `https://www.gbif.org`.

5. **GBIF Returns Fuzzy or Higher Rank Match:**
   - System clearly marks `matchType: FUZZY` or `rank: GENUS/FAMILY`.
   - The interface prevents misrepresenting a higher-rank match as a species-level confirmation.

6. **Network Failure Calling GBIF:**
   - Error code: `GBIF_SERVICE_UNAVAILABLE`.
   - System displays the AI candidate identification and notifies the user that taxonomic verification was unavailable.

---

## 5. Excluded Features (Scope Lock)

The following items are out of scope:
- User accounts, authentication, or contributor profiles.
- Public observations, social feeds, comments, or community moderation.
- Precise GPS, maps, habitat mapping, or species range maps.
- Population estimates, conservation status, IUCN assessments, or threat predictions.
- Bulk ingestion of GBIF, iNaturalist, or Catalogue of Life datasets.
- Custom-trained classifiers, local model fine-tuning, or local weight inference.
- Audio recognition, SAM segmentation, video processing, or camera-trap pipelines.
- Vector databases, knowledge graphs, or RAG frameworks.
- Multi-image uploads or batch processing.
- Mobile applications or new deployment architectures.
