# Vivédex Experience Reconnaissance & Inspection Report

## 1. Executive Summary & Purpose
This document records the visible, architectural, and functional reconnaissance of the **Vivédex** biodiversity platform prototype.
Following the **Craft Anything** evidence-based inspection and reconstruction methodology, this report:
1. Gathers empirical evidence from the running application and codebase on branch `feat/platform-prototype`.
2. Strictly separates verified functional facts from visual assumptions.
3. Diagnoses usability, aesthetic, and structural gaps against product references (Restor.eco, Classic Pokédex, Habitica, ORCID).
4. Establishes the concrete reconstruction blueprint for RUN 007B.

---

## 2. Craft Anything Workflow Principles Applied
The Craft Anything workflow emphasizes evidence-based decomposition and verified reconstruction:
- **Inspect the Existing Product:** Directly audit runtime states, markup, data models, routes, and user interaction flows.
- **Record Evidence:** Itemize functional realities and failure points rather than idealized specifications.
- **Separate Verified Facts from Assumptions:** Distinguish what the code actually does from what documentation claims it does.
- **Define the Target Experience:** Articulate specific visual, interaction, and emotional expectations for the target audience (naturalists, academic researchers, citizen scientists, technology partners).
- **Reconstruct Experience:** Build a modular, theme-consistent design system and refined page controllers.
- **Validate Results:** Execute automated regressions and visual verification checks.
- **Record Outstanding Gaps:** Be explicit about architectural limitations and deferred features.

---

## 3. Empirical Inspection of the Existing Vivédex Baseline

### 3.1 Repository & Environment Facts
- **Repository:** `https://github.com/rpxgit/vivedex.git`
- **Current Branch:** `feat/platform-prototype` (Commit `0538346`)
- **Runtime:** Python 3.14.7 (Windows `py` launcher)
- **Local Application Server:** Streamlit 1.66.1 listening on `http://localhost:8501`
- **Node.js / npm Status:** **NOT INSTALLED** on host environment. Any React/TypeScript migration would fail without an external Node runtime installation.
- **Database:** Local SQLite database at `data/vivedex.sqlite3` with 10 tables, schema version 1, and foreign keys enforced.
- **Test Baseline:** 42/42 tests passing across `pytest` and `unittest`.

### 3.2 Existing Navigation & Routes
- Navigation is controlled in `app.py` via `st.navigation` using 8 standard views:
  1. `Home` (`view_home`)
  2. `Explore Dex` (`view_explore`)
  3. `Identify` (`view_identify`)
  4. `My Collection` (`view_collection`)
  5. `Field Journal` (`view_journal`)
  6. `Achievements` (`view_achievements`)
  7. `Researcher Profile` (`view_profile`)
  8. `Knowledge Explorer` (`view_knowledge`)
  9. `Admin Console` (`view_admin` — conditionally appended only when `current_user.is_admin` is True).

### 3.3 Functional Evidence (Verified Working)
- **Vision Inference:** `src/meta_adapter.py` formats prompt and handles `muse-spark-1.3` completions.
- **Taxonomic Reconciliation:** `src/gbif_adapter.py` matches scientific names against GBIF Species Match API, returning `GBIFMatchResult` with CC BY 4.0 attribution.
- **In-Memory Image Processing:** `src/image_processor.py` validates JPG/PNG/WebP under 8 MB, strips EXIF tags, and normalizes orientation in volatile memory.
- **Authentication & RBAC:** `src/auth.py` correctly hashes passwords using PBKDF2-HMAC-SHA256 (100,000 rounds, 16-byte random salt), provides constant-time comparison, and boots the first registered user as Administrator.
- **Gamification Engine:** `src/achievements.py` evaluates 5 distinct rules and calculates XP based on first encounters, completed field notes, and accepted submissions.
- **Knowledge Traversal:** `src/knowledge_graph.py` traverses SQLite-backed `taxa` and `taxon_relationships` tables up to Kingdom.
- **Moderation Engine:** `src/admin_service.py` allows admins to transition observations across `PENDING`, `ACCEPTED_FOR_CATALOG`, `NEEDS_MORE_EVIDENCE`, and `REJECTED`, logging all events to `audit_logs`.

---

## 4. Current Usability & Aesthetic Diagnosis

While functionally sound, the visual and experiential presentation suffers from key shortcomings:

| Domain | Current Implementation Gap | Required Reconstructed Experience |
|---|---|---|
| **Aesthetic Personality** | Standard Streamlit dashboard look. White/grey flat cards, generic blue accents, default system fonts. Feels like an internal engineering dashboard. | Natural history museum aesthetic: deep forest greens, botanical ivory, warm parchment, gold accents, and editorial typography (Cinzel / Cormorant serif headers with crisp geometric sans body). |
| **Species Browsing (Explore)** | Text-dominated search with no imagery. Requires manual search input before any card appears. No category browsing. | Visual specimen card grid with curated photography, 10 ecological browsing categories (Birds, Mammals, Reptiles, Plants, Fungi, Insects, etc.), search filters, and instant collection indicators. |
| **Species Detail Experience** | No dedicated deep species view. Clicking an organism only showed basic taxonomy attributes inline. | Dedicated rich specimen page: prominent photography, italicized binomials, morphological evidence, collection status, GBIF Backbone links, and community sightings. |
| **Naming & Product Identity** | Pages called "My Collection" and "Explore Dex" lack Pokédex/Habitica inspiration. | Rebrand collection to **My Dex**, framing it as a personal biological encyclopedia with encounter counters and completion metrics. |
| **Gamification Immersion** | Numeric level integers ("Level 1", "Level 2"). Simple progress bar. | Immersive naturalist ranks: *Observer*, *Explorer*, *Naturalist*, *Field Researcher*, *Specialist*, *Biodiversity Steward*. Categorized badge families (First Encounters, Taxonomic Exploration, Field Documentation). |
| **Observation Workflow** | Identify page displays results in standard vertical text stack. Field note entry and collection saving appear as an afterthought. | Polished 10-step naturalist field workflow: clear preview, EXIF strip indicator, diagnostic trait badges, lookalike cards, clear uncertainty caveats, and a prominent "Add to Field Journal" action. |
| **Public vs Logged-In State** | Logged-out state simply displays a plain informational box. | Polished guest expedition landing page with biodiversity hero section, sample specimen showcase, and clear onboarding CTAs. |

---

## 5. Technology Architecture Evaluation Summary

- **Streamlit Capabilities:** Streamlit 1.66.1 supports full HTML/CSS injection (`unsafe_allow_html=True`), custom web fonts (Google Fonts: *Playfair Display*, *Cinzel*, *Plus Jakarta Sans*), CSS grid and flexbox styling, custom badges, and SVG specimen illustrations.
- **Host Limitations:** Windows environment lacks Node.js, npm, or pnpm. Creating a separate React frontend would require altering host prerequisites and introducing unvetted build steps.
- **Strategic Verdict:** Retain Streamlit as the application framework, but completely reconstruct the frontend layer with a dedicated, centralized Design System (`src/ui/theme.py`) providing high-fidelity CSS tokens, typography, specimen cards, and responsive components.

---

## 6. Reconstruction Roadmap (Phase Sequence)
1. **Phase B — Design System:** Centralize design tokens (`--forest`, `--deep-forest`, `--moss`, `--sage`, `--ivory`, `--paper`, `--earth`, `--gold`, `--ink`, `--muted`), editorial typography, specimen card layouts, and status badges in `src/ui/theme.py`.
2. **Phase C — Main Experience:**
   - Redesign `Home` as a naturalist expedition dashboard with onboarding and ecological metrics.
   - Reconstruct `Explore Dex` with 10 taxonomic category filters and visual species cards.
   - Build a dedicated `Species Detail` view with specimen photography and full classification.
   - Refine `Identify` into a 10-step naturalist observation workflow.
   - Upgrade `My Dex` into a personal biological encyclopedia.
3. **Phase D — User Experience:**
   - Enhance `Field Journal` with chronological observation timeline and inline note editing.
   - Upgrade `Achievements` with naturalist ranks and badge families.
   - Reconstruct `Researcher Profile` with Contributor ID, unverified ORCID citation, and field stats.
   - Upgrade `Knowledge Explorer` with lineage tree visuals and progressive node disclosure.
4. **Phase E — Administration:**
   - Refine `Admin Console` with data-quality indicators, observation moderation queue, and audit logs.
5. **Phase F — Verification:**
   - Run automated test suite (ensure 42+ tests pass).
   - Add new tests in `tests/test_ui_experience.py`.
   - Verify local application across multiple views.
