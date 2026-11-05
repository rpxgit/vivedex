# Vivédex

**A provenance-aware biodiversity discovery, identification, collection, and contribution platform.**

Vivédex transforms organism photographs into explainable candidate identifications and taxonomically reconciled species records. The platform connects individual sightings with personal specimen collections, Restor-inspired ecological context, Habitica-inspired field habits, and ORCID-inspired researcher passports.

---

## Technical Specifications and Documentation

- **Technical Whitepaper:** [`WHITEPAPER.md`](WHITEPAPER.md) — Architectural overview, design philosophy, and data governance.
- **Product Roadmap:** [`ROADMAP.md`](ROADMAP.md) — Implementation status across release phases.
- **Data Sources & Attribution:** [`DATA_SOURCES_AND_ATTRIBUTION.md`](DATA_SOURCES_AND_ATTRIBUTION.md) — Authoritative data licensing and GBIF Backbone Taxonomy notice.
- **Windows Installation Guide:** [`docs/INSTALLATION_WINDOWS.md`](docs/INSTALLATION_WINDOWS.md) — One-click launcher, PowerShell scripts, and administrator setup.
- **Product Experience Specification:** [`docs/PRODUCT_EXPERIENCE_SPEC.md`](docs/PRODUCT_EXPERIENCE_SPEC.md) — UI design system and component rules.
- **Feature Completion Matrix:** [`docs/FEATURE_COMPLETION_MATRIX.md`](docs/FEATURE_COMPLETION_MATRIX.md) — Status across all 13 application modules.
- **Security Audit & Hardening:** [`docs/security/SECURITY_AUDIT.md`](docs/security/SECURITY_AUDIT.md) and [`docs/security/REMEDIATION_BACKLOG.md`](docs/security/REMEDIATION_BACKLOG.md).

---

## 1. Project Purpose and Principles

Modern biodiversity monitoring requires balance between fast machine-learning inference and rigorous scientific provenance:
- **Identifications are hypotheses:** Artificial intelligence predictions are unconfirmed suggestions, not certified scientific facts.
- **Authoritative taxonomic reconciliation:** Proposed names are reconciled against the Global Biodiversity Information Facility (GBIF) Backbone Taxonomy under CC BY 4.0.
- **Observer privacy by design:** Images are processed in volatile memory. EXIF metadata, GPS micro-coordinates, and device tags are stripped before network transmission.
- **Persistent researcher attribution:** Observers receive unique Contributor IDs (`VDX-XXXXXX`) and record research outputs with auditable provenance states.
- **Ecological habit building:** Naturalists earn non-punitive experience points (XP), complete weekly BioBlitz quests, and monitor dynamic species richness at accredited field sites.

---

## 2. Platform Architecture and Modules

The platform is structured into four functional sections plus role-gated governance:

```
[Specimen Photo Upload] (JPG, PNG, WebP <= 8 MB)
          │
          ▼
[In-Memory Image Processor (`src/image_processor.py`)]
    └── Header validation, orientation normalization, EXIF stripped
          │
          ▼
[Meta Model API (`src/meta_adapter.py`)]
    └── Model: `muse-spark-1.3` (Candidate identification, diagnostic traits)
          │
          ▼
[GBIF Species Match API (`src/gbif_adapter.py`)]
    └── Authoritative taxonomic verification (TaxonKey, status, classification)
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
    └── Light botanical design system (WCAG AA contrast >= 4.5:1, 13 modular views)
```

### Module Directory
1. **Expedition Hub (`/home`):** Overview dashboard, platform statistics, and quick-start workflow.
2. **Global Search (`/search`):** Search across species, field sites, expeditions, and researchers.
3. **Explore Dex (`/explore`):** Query GBIF Backbone Taxonomy by scientific or common name.
4. **Identify Specimen (`/identify`):** 10-step multimodal AI vision pipeline with diagnostic traits and site linking.
5. **My Dex Collection (`/mydex`):** Personal species herbarium tracking first encounters and notes.
6. **Field Journal (`/journal`):** Persistent observation log with moderation status indicators.
7. **Field Sites & Expeditions (`/sites`):** Monitored ecosystems with dynamic species richness metrics.
8. **Partner Organisations (`/organisations`):** Accredited institutions supporting field research.
9. **Quests & Habits (`/quests`):** Daily field habits, BioBlitz goals, and XP progression.
10. **Milestone Badges (`/achievements`):** Rule-based milestone badge progression.
11. **Researcher Passport (`/passport`):** Contributor ID, institutional affiliations, and verified research outputs.
12. **Taxonomic Knowledge (`/knowledge`):** SQLite phylogenetic graph traversal.
13. **Account Settings (`/settings`):** Bring Your Own Key (BYOK) Meta Model API management and privacy controls.
14. **Admin Console (`/admin`):** Role-gated observation moderation queue and audit logs.

---

## 3. Installation and Launch (Windows)

### Option A: One-Click Launcher (Recommended)
Double-click `Launch-Vivedex.bat` in the repository root.

The launcher executes the following tasks automatically:
1. Detects Python 3.10+ on the system.
2. Creates a local virtual environment (`.venv`) if absent.
3. Installs dependencies from `requirements.txt`.
4. Initializes database schema tables safely without data loss.
5. Starts the Streamlit server on `http://localhost:8501`.
6. Opens the application in the default web browser.

### Option B: PowerShell Commands
```powershell
# 1. Initialize environment and dependencies
powershell -ExecutionPolicy Bypass -File scripts\Initialize-Vivedex.ps1

# 2. Run diagnostic health checks
powershell -ExecutionPolicy Bypass -File scripts\Check-Vivedex.ps1

# 3. Launch application
powershell -ExecutionPolicy Bypass -File scripts\Start-Vivedex.ps1
```

For complete Windows setup instructions, see [`docs/INSTALLATION_WINDOWS.md`](docs/INSTALLATION_WINDOWS.md).

---

## 4. Bring Your Own Key (BYOK) Configuration

Vivédex uses a session-isolated Bring Your Own Key model:

1. **Connect via UI:**
   - Log into your account and open **Account Settings** (`/settings`).
   - Enter your Meta Model API key from [dev.meta.ai](https://dev.meta.ai/).
   - Click **Test & Connect Meta Model API**.
2. **Volatile Session Storage:**
   - User keys remain strictly in volatile server memory (`st.session_state`).
   - Keys are **never** persisted to SQLite, user profile rows, observation records, or export files.
3. **Environment Fallback:**
   - Operators can define `MODEL_API_KEY` in `.env` or system environment variables as a global fallback.
4. **Demo Fixture Mode:**
   - If no key is configured, Vivédex defaults to Demo Fixture Mode using reference specimen data.

---

## 5. Administrator Provisioning

Vivédex never creates an administrator account automatically. To provision an administrator account:

```powershell
# Using the virtual environment python:
.\.venv\Scripts\python.exe -m src.cli create-admin --username admin --password "StrongPassw0rd!" --display-name "Lead Naturalist"

# Check administrator presence:
.\.venv\Scripts\python.exe -m src.cli check-admin
```

---

## 6. Automated Verification and Tests

Vivédex includes an automated regression test suite containing 98 tests across 8 modules:

```powershell
# Run the complete test suite
py -3 -m pytest -v
```

Test coverage includes:
- Multimodal backend inference and fallback fixtures (`tests/test_backend.py`)
- API credentials, BYOK isolation, and masking (`tests/test_api_credentials.py`)
- Authentication, PBKDF2 hashing, and role checks (`tests/test_security.py`)
- Domain services, collections, quests, and passports (`tests/test_platform.py`)
- UI rendering and navigation routes (`tests/test_ui.py`, `tests/test_ui_experience.py`)
- Product QA defect remediation across 10 defect areas (`tests/test_product_qa.py`)

---

## 7. Data Licensing and Attribution

- **GBIF Backbone Taxonomy:** GBIF Secretariat (2023). GBIF Backbone Taxonomy. Checklist dataset. https://doi.org/10.15468/39omei. Licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
- **Meta Model API:** `muse-spark-1.3` inference endpoint used in accordance with Meta developer terms.
- **For full licensing details:** See [`DATA_SOURCES_AND_ATTRIBUTION.md`](DATA_SOURCES_AND_ATTRIBUTION.md).

---

## 8. Limitations and Security Notes

- **Tentative Determination:** Identifications are machine-learning suggestions and must not be used for medical, toxicological, or edible foraging decisions.
- **Local Prototype Scope:** Current v0.1.0 release is configured as a standalone workstation platform. Distributed clustering and cloud synchronization are planned for future phases.
