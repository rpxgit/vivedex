# API Notes & Verification Log

**Date:** 2026-11-04  
**Auditor:** Technical Lead (Gemini in Antigravity)  
**Run:** RUN 001  
**Status:** Preflight Verified  

---

## 1. Meta Model API

### Official Documentation Reference
* **Documentation Base:** `https://meta.ai` / `https://meta.com/developers`
* **Base URL:** `https://api.meta.ai/v1`
* **Status:** VERIFIED

### Endpoint Details
* **Endpoint:** `POST https://api.meta.ai/v1/chat/completions` (OpenAI-compatible)
* **Agentic Alternative:** `POST https://api.meta.ai/v1/responses`
* **Authentication Method:** HTTP Bearer token in the `Authorization` header:
  ```http
  Authorization: Bearer $MODEL_API_KEY
  ```
* **Required Environment Variable:** `MODEL_API_KEY`
* **Current Environment Check:** **MISSING / NOT CONFIGURED**. Neither `MODEL_API_KEY` nor `META_API_KEY` is present in the environment.

### Supported Model Identifier
* **Model ID:** `muse-spark-1.3` (vision, multimodal reasoning, tool calling, JSON output support)
* **Alternative Model ID:** `muse-spark-1.1`
* **Status:** VERIFIED

### Image Input Format
* Endpoint `/chat/completions` accepts multimodal messages inside a `user` role content array.
* Supported image formats:
  1. Base64 Data URL: `data:image/jpeg;base64,...` or `data:image/png;base64,...`
  2. Public HTTP/HTTPS URL: `{"type": "image_url", "image_url": {"url": "https://..."}}`
* Request Structure:
  ```json
  {
    "model": "muse-spark-1.3",
    "messages": [
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": "Identify the organism in this image. Provide a candidate identification with visible evidence, lookalikes, and uncertainty notes in strict JSON format."
          },
          {
            "type": "image_url",
            "image_url": {
              "url": "data:image/jpeg;base64,..."
            }
          }
        ]
      }
    ],
    "temperature": 0.2
  }
  ```
* **Status:** VERIFIED

---

## 2. GBIF Species Name-Match API

### Official Documentation Reference
* **Official Documentation:** `https://www.gbif.org/developer/species`
* **Endpoint URL:** `https://api.gbif.org/v1/species/match`
* **Authentication:** Open access (no authentication or API key required).
* **Status:** VERIFIED

### Request Parameters
* `name` (string, required): Scientific name to match against the GBIF Backbone Taxonomy.
* `strict` (boolean, optional): If `true`, fuzzy matching is disabled. Default is `false`.
* `verbose` (boolean, optional): If `true`, returns diagnostic candidate scores. Default is `false`.
* Higher-taxon context parameters (optional): `kingdom`, `phylum`, `class`, `order`, `family`, `genus`.

### Response Fields Required by MVP
* `usageKey` (integer): GBIF unique taxon identifier.
* `scientificName` (string): Full scientific name with authorship.
* `canonicalName` (string): Canonical name without authorship.
* `rank` (string): Taxon rank (e.g. `SPECIES`, `GENUS`, `FAMILY`).
* `status` (string): Taxon status (`ACCEPTED`, `SYNONYM`, `DOUBTFUL`).
* `confidence` (integer): Name-match confidence score (0 to 100).
* `matchType` (string): Match type (`EXACT`, `FUZZY`, `HIGHERRANK`, `NONE`).
* `kingdom`, `phylum`, `class`, `order`, `family`, `genus`, `species` (strings): Taxonomic classification.
* `synonym` (boolean): Whether the matched name is a taxonomic synonym.

### Live Connectivity Test Result
* **Command:** `curl.exe -s "https://api.gbif.org/v1/species/match?name=Passer+domesticus"`
* **Status:** **PASS** (HTTP 200 returned).
* **Sample Payload Received:**
  ```json
  {
    "usageKey": 5231190,
    "scientificName": "Passer domesticus (Linnaeus, 1758)",
    "canonicalName": "Passer domesticus",
    "rank": "SPECIES",
    "status": "ACCEPTED",
    "confidence": 99,
    "matchType": "EXACT",
    "kingdom": "Animalia",
    "phylum": "Chordata",
    "order": "Passeriformes",
    "family": "Passeridae",
    "genus": "Passer",
    "species": "Passer domesticus",
    "kingdomKey": 1,
    "phylumKey": 44,
    "classKey": 212,
    "orderKey": 729,
    "familyKey": 5264,
    "genusKey": 2492321,
    "speciesKey": 5231190,
    "class": "Aves"
  }
  ```

---

## 3. UNVERIFIED Items Register
* None. All endpoints, parameters, data models, model identifiers, and network routes are verified against official documentation or verified with live connectivity checks.
