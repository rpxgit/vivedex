# Vivédex

**A biodiversity discovery, identification, collection, and contribution platform.**

Vivédex turns an organism photograph into a cautious, explainable candidate identification and a taxonomically resolved, provenance-backed species card, integrated with personal collection catalogs, Restor-inspired ecological context, Habitica-inspired field habits, and ORCID-inspired researcher passports.

---

## Platform Evolution & Specifications

- **Product Experience Specification (v2.0):** [`docs/PRODUCT_EXPERIENCE_SPEC.md`](docs/PRODUCT_EXPERIENCE_SPEC.md)
- **Feature Completion Matrix:** [`docs/FEATURE_COMPLETION_MATRIX.md`](docs/FEATURE_COMPLETION_MATRIX.md)
- **Security Audit & Hardening:** [`docs/security/SECURITY_AUDIT.md`](docs/security/SECURITY_AUDIT.md) & [`docs/security/REMEDIATION_BACKLOG.md`](docs/security/REMEDIATION_BACKLOG.md)
- **Platform Specification:** [`docs/PLATFORM_SPEC.md`](docs/PLATFORM_SPEC.md)
- **Experience Design Specification:** [`docs/EXPERIENCE_DESIGN_SPEC.md`](docs/EXPERIENCE_DESIGN_SPEC.md)

---

## 1. Project Purpose & Philosophy

Modern biodiversity discovery requires a balance between rapid multimodal AI inference and rigorous taxonomic provenance:
- **AI identifications are candidate suggestions, not confirmed scientific facts.**
- **Taxonomic reconciliation must preserve authoritative sources.** Vivédex links proposed binomials to the Global Biodiversity Information Facility (GBIF) Backbone Taxonomy under CC BY 4.0.
- **Privacy and provenance are first-class principles.** Images are processed in-memory with EXIF metadata stripped; data licensing metadata is preserved across all records and exports.
- **Engaging citizen science and ecological storytelling.** Inspired by botanical atlases, Restor.eco, Pokédex, Habitica, and ORCID, naturalists earn experience points, build field habits, explore monitored field sites, and curate persistent researcher passports.

---

## 2. Platform Navigation & Modules

The platform interface features a light botanical editorial design with verified WCAG AA contrast ($\ge 4.5:1$) and zero heading redundancy, structured into four main operational categories plus administrator governance:

### 🧭 Discover & Catalog
1. **Expedition Hub (Home):** Naturalist dashboard with live platform statistics, core 6-step naturalist workflow, featured habitats, and public onboarding controls.
2. **Global Discovery Search:** Fast, cross-entity query engine across taxa, field sites, conservation projects, expeditions, and naturalist profiles.
3. **Explore Dex:** Query the GBIF Backbone Taxonomy by scientific or vernacular name, inspect hierarchies, and save directly to personal collections.
4. **Identify Specimen:** 10-step multimodal AI vision pipeline with Meta Muse Spark, in-memory EXIF stripping, explainable diagnostic traits, and ecological site linking.
5. **My Dex Collection:** Personal species catalog tracking first/latest encounters, encounter counts, and personal field notes.
6. **Field Journal:** Persistent observation diary with editable notes, coarse location logging, and moderation status inspection.

### 📍 Ecology & Field Work (Restor.eco Inspired)
7. **Field Sites & Expeditions:** Monitored ecosystems with biomes, coordinates, elevation, dynamic species richness derived from actual sightings, and active scientific expeditions.
8. **Partner Organisations:** Accredited botanical gardens, universities, and conservation foundations supporting field research.

### ⚡ Naturalist Progression (Habitica Inspired)
9. **Quests & Habits:** Non-punitive daily field habits (e.g. Daily Field Scan, Botanical Journaling), weekly BioBlitz goals, and milestone quests with XP rewards.
10. **Milestone Badges:** Rule-based achievement engine (First Encounter, Collector, Family Explorer, Field Naturalist, Contributor) with level progression.

### 👤 Science & Identity (ORCID Inspired)
11. **Researcher Passport:** Persistent Contributor ID (`VDX-XXXXXX`), institutional affiliations, research interests, and research outputs (datasets, publications, checklists) with transparent provenance states (`SELF_REPORTED`, `SOURCE_LINKED`, `PLATFORM_REVIEWED`, `EXTERNALLY_VERIFIED`).
12. **Taxonomic Knowledge Graph:** Interactive SQLite-backed taxonomic knowledge graph with lineage trees, child nodes, and connected sightings.

### 🛡️ Governance (Role-Gated)
13. **Admin Console:** Role-protected console with platform metrics, user directory, observation moderation queue, and security audit logs.

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
[Domain Services Layer]
   ├── EcologicalService (`src/ecological_service.py`): Field sites & species richness
   ├── QuestService (`src/quest_service.py`): Habits & milestone XP tracking
   ├── PassportService (`src/passport_service.py`): Contributor passport & outputs
   ├── SearchService (`src/search_service.py`): Cross-entity discovery search
   ├── CollectionService (`src/collection_service.py`): Observations & collections
   └── AchievementService (`src/achievements.py`): Milestone badges & ranks
         │
         ▼
[Streamlit Interface (`app.py`)]
   ├── Light botanical theme (.streamlit/config.toml, WCAG AA compliant >= 4.5:1)
   ├── Sectioned navigation with 13 specialized pages
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
```powershell
# Windows PowerShell
$env:MODEL_API_KEY = "your_meta_model_api_key_here"

# Linux / macOS
export MODEL_API_KEY="your_meta_model_api_key_here"
```
*Note:* If no key is set, Vivédex displays an environment warning banner and provides a **Demo Fixture Mode** toggle to test the complete identification workflow offline.

---

## 5. Running the Application

Launch the Streamlit app with one command:
```powershell
streamlit run app.py
```
Or via the Python launcher on Windows:
```powershell
py -m streamlit run app.py
```

Open your browser at `http://localhost:8501` (or the port reported by Streamlit).

---

## 6. Testing

Run the full automated test suite (71 tests covering backend, platform, security, UI, and experience overhaul):
```powershell
py -m pytest -v
```
Or using Python's standard unittest runner:
```powershell
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
- **Privacy:** Images uploaded to Vivédex are processed strictly in volatile memory; EXIF location tags and camera metadata are stripped before external transmission. Images are never written to permanent disk storage or shared.
