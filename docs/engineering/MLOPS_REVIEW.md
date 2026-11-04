# Vivédex MLOps and Model Architecture Review

## 1. Executive Summary
This document provides a comprehensive MLOps, AI safety, and knowledge retrieval assessment of the Vivédex biodiversity platform.
It audits the Meta Muse Spark 1.3 vision pipeline, prompt management, error resilience, privacy boundaries, and model evaluation protocols.
All recommendations adhere to the ASD-STE100 technical standard.

---

## 2. Meta Muse Spark Integration Analysis

### 2.1 Current Implementation Facts
- **Model Identifier:** `muse-spark-1.3` (hardcoded constant in `src/meta_adapter.py`).
- **Endpoint:** `POST https://api.meta.ai/v1/chat/completions`.
- **Authentication:** `Authorization: Bearer $MODEL_API_KEY`.
- **Payload Format:** Multimodal JSON message with Base64 data URL (`data:image/jpeg;base64,...`).
- **Sampling Temperature:** 0.2 (deterministic candidate generation).
- **Output Parsing:** Regular expression markdown code fence removal followed by Pydantic validation via `ModelIdentificationResult`.

### 2.2 MLOps Findings

#### Finding MLOPS-01: Zero Retry Logic and Resilience Against Transient Failures
- **Finding:** The adapter executes single-attempt HTTP requests without retry or exponential backoff.
- **Evidence:** `src/meta_adapter.py` (lines 130-155) wraps `urllib.request.urlopen` in a single `try...except` block. Any HTTP 429 (rate limit), HTTP 500/503 (upstream transient error), or socket timeout causes immediate failure.
- **Impact:** Temporary network instability or API throttling immediately terminates the user's observation analysis.
- **Priority:** P1
- **Recommended Action:** Implement exponential backoff with jitter using the `tenacity` library or standard HTTP retries. Retry only idempotent errors (HTTP 429, 502, 503, 504) up to 3 times.
- **Dependencies:** None (`tenacity` or custom backoff loop).
- **Estimated Effort:** 3 hours.

#### Finding MLOPS-02: Hardcoded Prompt Strings and Lack of Prompt Versioning
- **Finding:** System instructions are stored as an immutable string inside the adapter class without semantic versioning.
- **Evidence:** `MetaAPIAdapter.SYSTEM_PROMPT` is hardcoded at lines 42-63 of `src/meta_adapter.py`.
- **Impact:** System prompt changes cannot be tracked across different inference runs. Engineers cannot correlate changes in model behavior or hallucinations with specific prompt revisions.
- **Priority:** P1
- **Recommended Action:** Extract system prompts into version-controlled prompt templates (e.g., `prompts/organism_identification_v1.0.txt`). Attach `prompt_version` to every observation and telemetry record.
- **Dependencies:** `src/schemas.py`.
- **Estimated Effort:** 2 hours.

#### Finding MLOPS-03: Excessive Payload Inflation from Unscaled Image Encoding
- **Finding:** Images are converted to Base64 without pre-scaling dimensions.
- **Evidence:** `src/image_processor.py` accepts images up to 8 MB. An 8 MB JPEG image results in an ~11 MB Base64 string transmitted over HTTP.
- **Impact:** Inflated network transmission time, increased memory usage during JSON serialization, and higher token/bandwidth costs.
- **Priority:** P2
- **Recommended Action:** Resize images to a standard maximum bounding box (e.g., $1600 \times 1600$ pixels) during in-memory preprocessing before Base64 encoding. Retain fine visual traits while reducing payload size by up to 75%.
- **Dependencies:** `src/image_processor.py` (Pillow).
- **Estimated Effort:** 2 hours.

#### Finding MLOPS-04: Discarded API Usage and Cost Telemetry
- **Finding:** Token consumption metrics returned by the Meta Model API are discarded during response parsing.
- **Evidence:** `src/meta_adapter.py` (lines 157-169) parses `raw_json["choices"][0]["message"]["content"]`, but completely ignores `raw_json.get("usage")`.
- **Impact:** Platform administrators cannot measure token consumption, monitor inference costs, or detect quota exhaustion.
- **Priority:** P2
- **Recommended Action:** Extract `prompt_tokens`, `completion_tokens`, and `total_tokens` from API responses. Record usage statistics in an isolated operational telemetry log.
- **Dependencies:** `src/schemas.py`, `src/models.py`.
- **Estimated Effort:** 2 hours.

---

## 3. Knowledge Architecture and Retrieval Strategy

### 3.1 Review of Current Taxonomic Graph
The current taxonomic knowledge graph is stored in SQLite:
- `taxa` table stores node attributes (scientific name, rank, kingdom, phylum, class, order, family, genus, species, author, license, attribution).
- `taxon_relationships` table stores directed edges (`PARENT_OF`, `SYNONYM_OF`).
- `KnowledgeGraphService` provides upward lineage traversal and localized neighborhood queries.

### 3.2 Evaluation of Knowledge Retrieval Strategies

| Strategy | Suitability for Vivédex | Operational Complexity | Recommendation |
|---|---|---|---|
| **Relational Hierarchy (Current)** | **High:** Exact phylogenetic trees require strict parental hierarchies. | Very Low (Standard SQL) | **Retain and Optimize:** Replace sequential N+1 loops with SQLite/Postgres recursive CTEs (`WITH RECURSIVE`). |
| **Full-Text Search (FTS5 / tsvector)** | **High:** Essential for matching common names, phonetic misspellings, and partial scientific names. | Low | **Adopt:** Implement SQLite FTS5 virtual table for rapid taxon lookup. |
| **Semantic Vector Retrieval** | **Low:** Vector embeddings fail on precise Linnaean nomenclature. Embeddings group organisms by visual or textual similarity, conflating distinct species lookalikes. | Medium | **Reject for Core Taxonomy:** Keep taxonomy deterministic. Reserve vector search solely for unstructured field note semantic exploration. |
| **GraphRAG (Microsoft GraphRAG / Neo4j)** | **Very Low:** GraphRAG is designed for synthesizing unstructured claims across hundreds of documents. Vivédex taxonomy is already structured by GBIF. | Very High | **Reject:** Introduces Neo4j clusters, vector stores, and entity extraction pipelines without measurable value. |

### 3.3 Evidence Threshold for GraphRAG or Dedicated Graph Databases
Vivédex must **NOT** adopt GraphRAG or dedicated graph databases (Neo4j) until the following empirical conditions are met:
1. The platform indexes more than 100,000 unstructured scientific ecological literature documents (PDFs, field journals, treatises).
2. Users require multi-hop natural language questions that cannot be resolved via taxonomic lineage (e.g., *"Find all migratory birds observed in Mediterranean scrub biomes that consume invasive beetles"*).
3. The query corpus exceeds 5,000,000 cross-entity relationship edges.
4. Scale exceeds SQLite relational capabilities and creates verified query bottlenecks.

---

## 4. Privacy-Preserving Model Observability

### 4.1 Telemetry Architecture
Operational model monitoring must remain strictly separated from user observation records.
Operational telemetry records performance, latency, and reliability metrics without logging private personal data.

### 4.2 Telemetry Record Schema
For each inference request, the platform will record:
- `request_id`: Unique UUIDv4.
- `timestamp`: UTC ISO 8601 string.
- `model_id`: Identifier of the model (`muse-spark-1.3`).
- `prompt_version`: Version string of the active prompt (`v1.0`).
- `image_sha256`: SHA-256 hash of the cleaned image bytes (for deduplication and verification).
- `preprocessing_latency_ms`: Duration of validation and EXIF stripping in milliseconds.
- `inference_latency_ms`: Duration of upstream HTTP request in milliseconds.
- `reconciliation_latency_ms`: Duration of GBIF API call in milliseconds.
- `prompt_tokens`: Input tokens counted by the provider.
- `completion_tokens`: Output tokens generated by the provider.
- `http_status`: HTTP response status code.
- `schema_valid`: Boolean flag indicating strict JSON schema validation success.
- `gbif_match_type`: Match outcome (`EXACT`, `FUZZY`, `HIGHERRANK`, `NONE`).
- `error_category`: Categorized error string (`None`, `TIMEOUT`, `AUTH_ERROR`, `RATE_LIMIT`, `PARSE_ERROR`).

### 4.3 Strict Privacy Constraints
The telemetry system **MUST NEVER LOG**:
- Raw API keys or authorization header values.
- Raw image binary bytes or Base64 image payloads.
- Personal location metadata (latitude, longitude, IP addresses).
- User passwords or account credentials.
- Free-form user field notes or personal identity fields.

---

## 5. Model Evaluation Framework

### 5.1 Objective
Establish an empirical, reproducible test harness to benchmark model performance, taxonomic resolution accuracy, and hallucination frequency.
Model confidence scores from GBIF must never be confused with model accuracy.

### 5.2 Curated Test Dataset Specification
Create a curated offline evaluation suite containing 200 standardized test cases:
1. **Taxonomic Diversity (80 images):** Balanced across 8 major classes (Aves, Insecta, Mammalia, Reptilia, Amphibia, Actinopterygii, Magnoliopsida, Agaricomycetes).
2. **Challenging Lookalikes (40 images):** Paired visually similar species (e.g., *Danaus plexippus* vs *Limenitis archippus*; *Apis mellifera* vs *Eristalis tenax*).
3. **Environmental Degradation (30 images):** Natural motion blur, extreme backlighting, heavy shadow, and partial leaf occlusion.
4. **Insufficient Evidence (20 images):** Unidentifiable parts (isolated bark, blurred wing tip, ambiguous caterpillar).
5. **Non-Organism Negative Controls (20 images):** Domestic furniture, vehicles, manufactured textiles, geological mineral specimens.
6. **Multi-Organism Scenes (10 images):** Pollinator perched on a flowering plant.

### 5.3 Quantitative Evaluation Metrics
The evaluation harness must compute the following metrics:
- **Top-1 Scientific Agreement:** $\frac{\text{Candidate scientific name matches ground truth}}{\text{Total valid organism images}}$.
- **GBIF Taxonomic Resolution Rate:** $\frac{\text{Proposed names successfully matched in GBIF Backbone}}{\text{Total proposed candidate names}}$.
- **Strict Schema Conformance:** $\frac{\text{Responses parsed without validation errors}}{\text{Total evaluation requests}}$.
- **Abstention Precision:** Model correctly identifies insufficient evidence or suggests higher taxonomic rank (`GENUS` or `FAMILY`) rather than hallucinating species.
- **Negative Control Rejection Rate:** Model correctly identifies non-organisms and refrains from proposing biological taxa.
- **Latency Distribution:** Record p50, p90, and p99 latency in seconds.

