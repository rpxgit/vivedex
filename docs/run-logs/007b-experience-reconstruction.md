# RUN 007B — Vivédex Experience Reconstruction

## 1. Objective
Transform the Vivédex interface into an authoritative, visually captivating biodiversity discovery and personal cataloging platform.
Follow the Craft Anything evidence-based inspection and reconstruction methodology.
Incorporate product principles from:
- Restor.eco (ecological storytelling and biome context).
- Classic Pokédex (organism discovery, taxonomic classification, and collection).
- Habitica (meaningful naturalist progression without stressful gaming mechanics).
- ORCID (persistent contributor identity and attribution).
- Craft Anything (evidence-based decomposition and verified reconstruction).

Preserve the working multimodal vision pipeline (Meta Muse Spark 1.3) and GBIF taxonomic reconciliation.
Preserve the local-first SQLite database and authentication model.
Ensure the reconstructed experience runs cleanly on Windows with Python 3.14.

---

## 2. Reference Repositories Inspected
1. **Craft Anything (`https://github.com/storytold/craft-anything`):**
   - Methodology inspected: Evidence collection, structured specification, architecture decision record, iterative reconstruction, regression testing.
   - Core insight: Separate empirical facts from assumptions. Avoid unnecessary multi-tier migration when the existing host environment does not support it.
2. **Restor.eco:**
   - Visual inspiration: Forest tones, ecological storytelling, conservation context, clear scientific provenance.
3. **Classic Pokédex:**
   - Functional inspiration: Categorized biological exploration, numerical entry markers, encounter counters, and specimen detail cards.
4. **Habitica:**
   - Functional inspiration: Milestone-based naturalist ranks, non-aggressive progression, badges with educational flavor text.
5. **ORCID:**
   - Functional inspiration: Contributor identifiers (`VDX-XXXXXX`), verified vs self-reported credentials, transparent scientific attribution.

---

## 3. Design Evidence Collected
Empirical inspection of the baseline platform on branch `feat/platform-prototype` revealed:
1. **Runtime & Tooling:**
   - Host machine: Windows 11 with Python 3.14.7.
   - Node.js and npm: Not installed (`CommandNotFoundException`).
   - Web framework: Streamlit 1.66.1.
2. **Visual Gaps in Prior Baseline:**
   - Standard Streamlit widgets produced a generic dashboard appearance.
   - Cards lacked organic depth, botanical typography, and tactile specimen framing.
   - Explore and Collection views displayed dense data tables instead of visual natural history specimen cards.
   - Missing dedicated species detail view with lookalikes, trait highlights, and diagnostic imagery.
   - Missing persistent breadcrumb navigation across nested views.
3. **Verified Functional Strengths:**
   - Image analysis pipeline correctly stripped EXIF metadata in memory.
   - Meta Muse Spark 1.3 model proposals and GBIF Species Match results remained strictly isolated.
   - SQLite schema version 1 enforced foreign keys and audit logs.
   - Unit and integration tests (42 tests) passed without errors.

---

## 4. Design Decisions
1. **Editorial Botanical Color Palette:**
   - Primary: Deep botanical forest (`#183B32`, `#102A25`).
   - Secondary: Organic moss and sage (`#718568`, `#A9B99A`).
   - Background: Tactile ivory and warm paper (`#F5F2E9`, `#FCFAF4`, `#E3DDD0`).
   - Accents: Terracotta earth (`#A66B48`) and naturalist gold (`#C6A66B`).
2. **Atmospheric Natural History Typography:**
   - Display and page headings: *Playfair Display* and *Cinzel*.
   - Body and data metrics: *Plus Jakarta Sans*.
   - Scientific names: Formatted in italicized serif (`*Genus species*`).
3. **Visual Specimen Cards:**
   - Tactile paper containers with rounded borders and subtle drop shadows.
   - Embedded high-quality specimen photography with verified Creative Commons / Unsplash licenses.
   - Prominent biological rank badges (*Kingdom*, *Phylum*, *Class*, *Order*, *Family*, *Genus*, *Species*).
4. **Naturalist Progression Engine:**
   - 6 naturalist ranks: *Observer* (Lv 1), *Explorer* (Lv 2), *Naturalist* (Lv 3), *Field Researcher* (Lv 4), *Specialist* (Lv 5), *Biodiversity Steward* (Lv 6+).
   - Replaced aggressive streaks with authentic milestone badges.
5. **Separation of Evidence and Verification:**
   - Retained explicit amber warnings: `AI-generated candidate. Not expert-verified.`
   - Retained moderation disclaimers: `ACCEPTED_FOR_CATALOG indicates community moderation approval, not verified taxonomic identification.`

---

## 5. Architecture Decision
Documented in `docs/TECHNOLOGY_DECISION_RECORD.md` (TDR 001):
- **Decision:** Retain and reconstruct Streamlit 1.66.1 with a centralized CSS design layer (`src/ui/theme.py`).
- **Rationale:** Node.js and npm are absent from the host environment. Retaining Streamlit prevents severe environmental failures, eliminates multi-service deployment friction, and preserves all 42 existing automated tests.
- **Implementation:** Custom typography via Google Fonts `@import`, CSS custom properties, responsive HTML card components via `st.markdown(..., unsafe_allow_html=True)`, and modular page routing via `st.navigation`.

---

## 6. Features Implemented
1. **Theme & Design System (`src/ui/theme.py`):**
   - Full CSS design tokens injected globally on all pages.
   - Helper functions: `specimen_card_html`, `rank_badge_html`, `get_naturalist_rank`, and `status_pill_html`.
2. **Deep Species Detail View (`src/ui/page_species_detail.py`):**
   - Detailed species card with photography, taxonomy hierarchy, diagnostic traits, similar lookalikes, GBIF match status, personal collection status, and community field sightings.
3. **Restor.eco Inspired Home (`src/ui/page_home.py`):**
   - Naturalist expedition hub with global platform statistics, rank progress cards, recent field discoveries, active milestone quests, and guest onboarding.
4. **Explore Dex (`src/ui/page_explore.py`):**
   - 10 biological category filters (Birds, Mammals, Reptiles, Amphibians, Fish, Insects, Arachnids, Plants, Fungi, Other).
   - Specimen cards with category icons, scientific names, family tags, and direct inspection links.
5. **My Dex / Personal Collection (`src/ui/page_collection.py`):**
   - Biological encyclopedia view of the user's observed taxa.
   - Completion progress bar, encounter counters, and taxonomic grouping.
6. **Observation Identification Pipeline (`src/ui/page_identify.py`):**
   - 10-step guided observation workflow with in-memory EXIF metadata stripping notice.
   - Diagnostic trait inspection, candidate lookalikes, GBIF Backbone reconciliation, and instant journal recording.
7. **Field Journal (`src/ui/page_journal.py`):**
   - Chronological observation timeline with inline field notes editing and moderation status pills.
8. **Milestone Achievements (`src/ui/page_achievements.py`):**
   - Naturalist ranks (Level 1 to 6+) and 5 milestone badge families with progress bars.
9. **Researcher Profile (`src/ui/page_profile.py`):**
   - Contributor ID (`VDX-XXXXXX`), bio, display name editing, and unverified external ORCID citation.
10. **Progressive Taxonomy Knowledge Browser (`src/ui/page_knowledge.py`):**
    - Phylogenetic lineage chips, parent/child nodes, and GBIF CC BY 4.0 provenance.
11. **Administrator Console (`src/ui/page_admin.py`):**
    - Role-protected dashboard with metrics, user directory, moderation queue, and audit trail logs.
12. **Shared Layout & Navigation (`src/ui/common.py`):**
    - Persistent breadcrumb navigation (`render_breadcrumbs`), quick demo user switch, and auth drawer.

---

## 7. Files Created
1. `docs/DESIGN_RECONNAISSANCE.md` (Inspection and reconnaissance report).
2. `docs/EXPERIENCE_DESIGN_SPEC.md` (Design system specification and tokens).
3. `docs/TECHNOLOGY_DECISION_RECORD.md` (TDR 001: Frontend architecture evaluation).
4. `src/ui/theme.py` (Centralized design tokens, CSS injection, and card renderers).
5. `src/ui/page_species_detail.py` (Dedicated species inspection page).
6. `tests/test_ui_experience.py` (Automated tests for design tokens, ranks, assets, and navigation).
7. `docs/run-logs/007b-experience-reconstruction.md` (This document).

---

## 8. Files Updated
1. `app.py`: Integrated new modular page views and species detail routing.
2. `src/ui/common.py`: Added breadcrumbs and updated navigation controls.
3. `src/ui/page_home.py`: Reconstructed as naturalist expedition hub.
4. `src/ui/page_explore.py`: Added 10 biological category filters and specimen cards.
5. `src/ui/page_collection.py`: Reconstructed as visual My Dex encyclopedia.
6. `src/ui/page_identify.py`: Refined 10-step identification workflow with specimen card styling.
7. `src/ui/page_journal.py`: Refined observation timeline with status pills.
8. `src/ui/page_achievements.py`: Reconstructed naturalist rank crowns and milestone badges.
9. `src/ui/page_profile.py`: Reconstructed researcher credentials and ORCID card.
10. `src/ui/page_knowledge.py`: Reconstructed taxonomy knowledge explorer.
11. `src/ui/page_admin.py`: Reconstructed admin console and audit log tables.

---

## 9. Files Deleted
No files were deleted. All prior modules and run logs were preserved.

---

## 10. Assets and Licensing
All curated specimen photographs are sourced from Unsplash under the Unsplash Open License:
- *Passer domesticus*: Photo by David Clode (Unsplash).
- *Danaus plexippus*: Photo by Suzanne D. Williams (Unsplash).
- *Taraxacum officinale*: Photo by Yoksel Zok (Unsplash).
- *Amanita muscaria*: Photo by Florian van Duyn (Unsplash).
- *Sciurus carolinensis*: Photo by Vincent van Zalinge (Unsplash).
- *Bombus terrestris*: Photo by Krzysztof Niewolny (Unsplash).
- *Anolis carolinensis*: Photo by Timothy Dykes (Unsplash).
- *Salmo trutta*: Photo by Clark Young (Unsplash).

GBIF taxonomic backbone data is licensed under Creative Commons Attribution 4.0 International (CC BY 4.0).
No proprietary assets, copyrighted logos, or trademarks from Pokémon, Nintendo, Habitica, or ORCID were used.

---

## 11. Tests Executed
Executed the full automated test suite with Python 3.14 on Windows:
1. `py -m pytest -v`:
   - `tests/test_backend.py`: 16 passed.
   - `tests/test_platform.py`: 23 passed.
   - `tests/test_ui.py`: 3 passed.
   - `tests/test_ui_experience.py`: 4 passed.
   - Result: **46 passed in 12.20 seconds**.
2. `py -m unittest discover -s tests -p "test_*.py" -v`:
   - All 46 test cases passed cleanly (**OK** in 12.54 seconds).

---

## 12. Screenshots Captured / Visual Checks
1. **Home / Expedition Hub:** Loaded on `http://localhost:8501`. Verified header, statistics tiles, and recent discoveries.
2. **Explore Dex:** Verified category filters and specimen card grids.
3. **Species Detail:** Verified breadcrumbs, trait lists, lookalikes, and GBIF match indicators.
4. **Identify:** Verified EXIF stripping notice, upload widget, and candidate display.
5. **My Dex:** Verified completion metrics and encounter counts.
6. **Field Journal:** Verified observation cards and field note editing.
7. **Achievements:** Verified rank crowns and milestone progression bars.
8. **Researcher Profile:** Verified Contributor ID card and ORCID citation.
9. **Admin Console:** Verified role-gated access and moderation queues.

---

## 13. Visual Issues
1. **Streamlit Button Hover:** Native Streamlit button hover states occasionally override custom CSS border colors. Addressed by applying explicit `!important` declarations in `src/ui/theme.py`.
2. **Font Loading Delay:** On offline environments, Google Fonts fallback to system serif and sans-serif fonts. Modern system font fallbacks (*Georgia*, *Cambria*, *Segoe UI*) were configured to maintain visual balance.

---

## 14. Known Limitations
1. **Single-Process Streamlit:** Complex client-side animations and drag-and-drop interactions are limited by Streamlit's server-driven rerun model.
2. **Offline Image Cache:** Curated specimen images load over HTTPS from Unsplash CDN. If the machine is completely disconnected from the Internet, fallback SVG badges are rendered.
3. **Self-Reported ORCID:** External researcher ORCID URLs are self-reported and unverified by OAuth in this prototype.

---

## 15. Remaining Work
1. Add offline asset caching for specimen photographs in `static/images/`.
2. Connect OAuth 2.0 flow for formal ORCID researcher verification.
3. Enable multi-photo uploads per observation.
4. Add spatial mapping integration (e.g., Folium/Leaflet) for coarse locality visualization.

---

## 16. Git Branch and Commits
- **Working Branch:** `feat/platform-prototype`
- **Base Branch:** `main`
- **Key Commits:**
  - `6ac9aa1`: docs: record exact commit hash in RUN 007 log
  - `0538346`: feat: add quick demo account switch in sidebar for rapid testing
  - `66e69bf`: refactor: restructure UI layout with modular page components and botanical theme
  - Current commit adds `docs/run-logs/007b-experience-reconstruction.md`.
- **Merge Status:** Preserved on `feat/platform-prototype`. NOT merged into `main`.

---

## 17. Scope Assessment
The reconstruction successfully achieved all objectives of RUN 007B:
- Delivered an authoritative natural history museum and botanical atlas aesthetic.
- Reconstructed all 8 main platform views and the Admin Console.
- Established a dedicated Species Detail view with diagnostic traits and lookalikes.
- Retained the working backend, Meta Muse Spark vision adapter, and GBIF taxonomy reconciliation.
- Added comprehensive automated regression tests.
- Reached 100% test pass rate across all 46 test cases.
