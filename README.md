# Vivédex

**A biodiversity discovery, identification, collection, and contribution platform.**

Vivédex turns an organism photograph into a cautious, explainable candidate identification and a taxonomically resolved, provenance-backed species card, integrated with personal collection catalogs, gamified field milestones, and community moderation.

---

## Platform Evolution & Specifications

- **Current Platform Specification (v0.2.0):** [`docs/PLATFORM_SPEC.md`](docs/PLATFORM_SPEC.md)
- **Data Model Specification:** [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md)
- **Historical V0.1 MVP Specification:** [`docs/MVP_SPEC.md`](docs/MVP_SPEC.md)

---

## 1. Project Purpose & Philosophy

Modern biodiversity discovery requires a balance between rapid multimodal AI inference and rigorous taxonomic provenance:
- **AI identifications are candidate suggestions, not confirmed scientific facts.**
- **Taxonomic reconciliation must preserve authoritative sources.** Vivédex links proposed binomials to the Global Biodiversity Information Facility (GBIF) Backbone Taxonomy.
- **Privacy and provenance are first-class principles.** Images are processed in-memory with EXIF metadata stripped; data licensing metadata (e.g. GBIF CC BY 4.0) is preserved across all records and exports.
- **Engaging citizen science.** Inspired by Pokédex, Habitica, and ORCID, naturalists earn experience points, unlock achievement badges, and curate persistent field journals.

---

## 2. Key Platform Features

- **Multi-Page Discovery Portal:**
  1. **Home:** Contributor summary, metrics, level progress bar, recent observations, and milestone previews.
  2. **Explore Dex:** Query GBIF Backbone Taxonomy by scientific or vernacular name, inspect hierarchy, and save directly to collections.
  3. **Identify:** Multimodal AI vision analysis with Meta Muse Spark, in-memory EXIF stripping, candidate traits, lookalikes, uncertainty, and persistent observation recording.
  4. **My Collection:** Personal species catalog tracking first/latest encounters, cumulative encounter counts, and personal field notes.
  5. **Field Journal:** Persistent observation diary with editable notes, coarse location logging, and moderation status inspection.
  6. **Achievements:** Rule-based badge engine (First Encounter, Collector, Family Explorer, Field Naturalist, Contributor) with XP and player levels.
  7. **Researcher Profile:** Unique Contributor ID (`VDX-XXXXXX`), biography, and optional self-reported ORCID URL.
  8. **Knowledge Explorer:** Interactive SQLite-backed taxonomic knowledge graph with lineage trees, child nodes, and connected sightings.
  9. **Admin Console:** Role-protected console with platform metrics, user directory, observation moderation queue, and security audit logs.
- **Local-First SQLite Architecture:** Zero cloud database dependencies; stores nodes and relationships locally in `data/vivedex.sqlite3`.
- **Cryptographic Authentication:** PBKDF2-HMAC-SHA256 password hashing with per-user salts and automatic first-user administrator bootstrap.
- **Controlled Demo Dataset:** One-click loader for curated demonstration records explicitly stamped with `DEMO DATA` provenance.


---

## 3. Architecture

```
[User Image Input] (Upload JPG / PNG / WebP)
         │
         ▼
[Image Processor (`src/image_processor.py`)]
   ├── Size & MIME validation (<= 8 MB)
   └── In-memory EXIF metadata stripping & orientation normalization
         │
         ▼
[Meta Model API (`src/meta_adapter.py`)]
   ├── Model: `muse-spark-1.3`
   ├── Prompt: Strict structured JSON schema
   └── Output: Candidate identification, morphological traits, lookalikes, uncertainty
         │
         ▼
[GBIF Species Match API (`src/gbif_adapter.py`)]
   ├── Endpoint: `https://api.gbif.org/v1/species/match`
   └── Reconciliation: Taxon key, canonical name, status, match type, classification
         │
         ▼
[Streamlit Interface (`app.py`)]
   ├── Candidate Identification Card (Meta AI)
   ├── Taxonomic Reconciliation Card (GBIF)
   ├── Non-expert verification disclaimer
   └── JSON Export (`VivedexResult.to_json()`)
```

---

## 4. Installation & Setup

### Prerequisites
- Python 3.11 or higher (Python 3.14 compatible).

### Clone & Install
```bash
git clone https://github.com/rpxgit/vivedex.git
cd vivedex
pip install -r requirements.txt
```

### Configuration
Copy `.env.example` to `.env` or set the environment variable directly:
```bash
# Windows PowerShell
$env:MODEL_API_KEY = "your_meta_model_api_key_here"

# Linux / macOS
export MODEL_API_KEY="your_meta_model_api_key_here"
```
*Note:* If no key is set, Vivédex displays an environment warning banner and provides a **Demo Fixture Mode** toggle to test the full UI flow.

---

## 5. Running the Application

Launch the Streamlit app with one command:
```bash
streamlit run app.py
```
Or via the Python launcher on Windows:
```bash
py -m streamlit run app.py
```

Open your browser at `http://localhost:8501`.

---

## 6. Testing

Run the full automated test suite (backend and UI):
```bash
pytest -v
```
Or using Python's standard unittest runner:
```bash
py -m unittest discover -s tests -p "test_*.py" -v
```

---

## 7. Data Sources & Provenance

- **Taxonomic Backbone:** [Global Biodiversity Information Facility (GBIF)](https://www.gbif.org) Backbone Taxonomy. Data is accessed via the public GBIF Species API and licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Attribution: *GBIF Secretariat (2023). GBIF Backbone Taxonomy. Checklist dataset. https://doi.org/10.15468/39omei*.
- **AI Inference:** Meta Model API (`muse-spark-1.3`).
- **Data Policy:** For detailed information on external data handling, refer to `Vivédex Data Licensing and Provenance Policy.md`.

---

## 8. Limitations & Privacy Notes

- **Candidate Results:** Identifications generated by AI models are suggestions, not expert determinations. They should not be used as authoritative medical, agricultural, or ecological decisions.
- **Privacy:** Images uploaded to Vivédex are processed in memory for analysis; EXIF location tags and camera metadata are stripped before external transmission. Images are never written to permanent disk storage or shared.
