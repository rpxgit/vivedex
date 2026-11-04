# RUN 007 — Vivédex Platform Evolution

## 1. Run Metadata
- **Date & Time:** 2026-11-05T01:02:00+05:30
- **Assigned Model:** Gemini in Antigravity IDE
- **Role:** Lead Software Engineer and Platform Architect
- **Coding Standard:** ASD-STE100
- **Git Branch:** `feat/platform-prototype`
- **Target Repository:** `https://github.com/rpxgit/vivedex.git`

---

## 2. Objective
Transform the existing Vivédex MVP into a coherent biodiversity discovery, collection, and contribution platform. Preserve the existing working Meta Muse Spark and GBIF identification pipeline. Extend the platform with user authentication, personal species collections, persistent field observations, researcher profiles, rule-based achievements, administrator moderation, a lightweight SQLite taxonomic knowledge graph, and a multi-page interface.

---

## 3. Architecture Decisions
1. **Retain Core Stack:** Preserved Python 3.14, Streamlit (1.66.1), SQLite (`sqlite3`), Pydantic (2.13.4), and Pillow (12.3.0).
2. **Zero External Heavy Infrastructure:** Rejected Neo4j, Microsoft GraphRAG, vector databases, Redis, Docker, Node.js, and React. Built a lightweight SQLite-backed graph model with typed nodes and relationship edges.
3. **Local-First Database:** Created `data/vivedex.sqlite3` with strict foreign key constraints (`PRAGMA foreign_keys = ON;`), schema versioning (`schema_version`), and parameterized queries. The database is ignored in `.gitignore` and never committed.
4. **Streamlit Multi-Page Navigation:** Implemented Streamlit 1.66.1 `st.navigation` with distinct URL paths and modular page renderers in `src/ui/`.
5. **Separation of Evidence and Verification:** Preserved strict boundaries between AI candidate proposals, GBIF taxonomic matching, and administrative moderation.

---

## 4. Features Implemented
1. **User Accounts & Authentication:**
   - Registration with unique usernames and display names.
   - First registered user is automatically bootstrapped as the platform administrator (`admin` role). Subsequent users receive the standard `user` role.
   - Salted password hashing with `hashlib.pbkdf2_hmac` (SHA-256, 100,000 iterations), `secrets.token_hex(16)` per-user salts, and constant-time `hmac.compare_digest` verification.
   - Displayed security notice: `LOCAL PROTOTYPE — AUTHENTICATION IS NOT PRODUCTION-HARDENED.`
2. **Personal Species Collection:**
   - Personal biodiversity catalog tracking unique collected taxa.
   - Records initial and latest encounter timestamps, plus cumulative encounter counts. Saving the same taxon increments encounters without duplicating species rows.
   - Search and filtering by common name, scientific name, family, and kingdom.
   - Direct removal action.
3. **Persistent Field Journal:**
   - Persistent observation logs with unique IDs (`OBS-YYYYMMDD-XXXX`).
   - Field notes editor allowing users to add and update natural history observations.
   - Coarse geographic locality tracking (never exact GPS).
   - Visual moderation status indicators (`PENDING`, `ACCEPTED_FOR_CATALOG`, `NEEDS_MORE_EVIDENCE`, `REJECTED`).
   - Stamped provenance tags (`LIVE_ANALYSIS` vs `DEMO DATA`).
4. **Researcher Profile:**
   - Unique Contributor ID (`VDX-XXXXXX`).
   - Naturalist biography and display name editing.
   - Self-reported external researcher identifier (ORCID URL) with explicit disclaimer: `External researcher identifier (Unverified — self-reported)`.
   - Aggregated biological metrics and earned badge showcase.
5. **Rule-Based Achievement Engine:**
   - 5 initial badges: `First Encounter`, `Collector`, `Family Explorer`, `Field Naturalist`, and `Contributor`.
   - XP incentives: `+50 XP` for first encounter with a taxon, `+20 XP` for detailed field notes (>= 5 characters), `+100 XP` for catalog-accepted submissions, plus badge bonus rewards.
   - Deterministic level progression: $\text{Level} = \max(1, 1 + \lfloor \frac{\text{XP}}{100} \rfloor)$.
   - Strict badge idempotency: no duplicate badge awards.
6. **Administrator Console:**
   - Restricted to `admin` role with server-side enforcement.
   - Dashboard metrics: total users, total observations, distinct taxa, pending submissions, accepted submissions, and audit trail events.
   - User management directory with observation counts and account status.
   - Observation moderation queue with status update workflows, moderator notes, and audit trail logging.
   - Mandatory notice: `'ACCEPTED_FOR_CATALOG' indicates that the submission passed platform moderation. It DOES NOT mean that a taxonomic expert has confirmed the identification.`
7. **Taxonomic Knowledge Explorer:**
   - Lineage breadcrumb traversal (Kingdom $\to$ Phylum $\to$ Class $\to$ Order $\to$ Family $\to$ Genus $\to$ Species).
   - Graph neighborhood explorer displaying connected observations, collectors, and data provenance.
8. **Controlled Demonstration Data:**
   - One-click demo dataset loader with sample taxa, observations, and users.
   - All sample records are stamped with `DEMO DATA` provenance. Sample passwords are generated dynamically at runtime and never stored in source code.

---

## 5. Files Created
1. `src/database.py` — SQLite connection repository, schema initialization, and migration engine.
2. `src/auth.py` — Authentication, role-based access control, and password hashing service.
3. `src/models.py` — Domain dataclasses for platform entities.
4. `src/collection_service.py` — Taxa persistence, personal collection, observations, and profile service.
5. `src/achievements.py` — Rule-based badge engine and experience points progression service.
6. `src/admin_service.py` — Administrative metrics, user directory, moderation workflows, and audit logging.
7. `src/knowledge_graph.py` — Lightweight SQLite knowledge graph service.
8. `src/demo_data.py` — Controlled demo data loader with `DEMO DATA` provenance.
9. `src/ui/__init__.py` — Package export.
10. `src/ui/common.py` — Shared UI layout, CSS injection, and authentication sidebar controls.
11. `src/ui/page_home.py` — Home dashboard view.
12. `src/ui/page_explore.py` — Explore Dex taxonomy browser view.
13. `src/ui/page_identify.py` — Vision identification and field recording view.
14. `src/ui/page_collection.py` — My Collection personal catalog view.
15. `src/ui/page_journal.py` — Field Journal observation logs and notes editor view.
16. `src/ui/page_achievements.py` — Achievements and XP progress view.
17. `src/ui/page_profile.py` — Researcher profile credentials view.
18. `src/ui/page_knowledge.py` — Taxonomic knowledge graph view.
19. `src/ui/page_admin.py` — Administrator control panel and moderation queue view.
20. `tests/test_platform.py` — 23 automated tests covering platform evolution scenarios.
21. `docs/PLATFORM_SPEC.md` — Platform architecture and functional specification.
22. `docs/DATA_MODEL.md` — Relational schema, constraints, and index documentation.
23. `docs/run-logs/007-platform-evolution.md` — This run log.

---

## 6. Files Updated
1. `.gitignore` — Added `data/`, `*.sqlite3`, and `*.db` to prevent local database persistence in version control.
2. `src/__init__.py` — Exported new services (`Database`, `AuthService`, `CollectionService`, `AchievementService`, `AdminService`, `KnowledgeGraphService`).
3. `app.py` — Refactored to multi-page Streamlit application using `st.navigation`.
4. `README.md` — Updated with platform capabilities while referencing historical V0.1 MVP spec.

---

## 7. Files Deleted
None.

---

## 8. Database Schema
Created 10 tables in SQLite (`data/vivedex.sqlite3`):
1. `schema_version` (version, applied_at, description)
2. `users` (id, username, password_hash, salt, role, is_active, created_at)
3. `user_profiles` (user_id, vivedex_id, display_name, bio, external_orcid_url, created_at, updated_at)
4. `taxa` (id, taxon_id, scientific_name, canonical_name, common_name, rank, status, match_type, kingdom, phylum, class_name, order_name, family, genus, species, authorship, source_id, data_provider, licence, attribution, retrieved_at, created_at)
5. `taxon_relationships` (id, parent_taxon_id, child_taxon_id, relationship_type, source, created_at)
6. `collections` (id, user_id, taxon_id, first_encounter_at, last_encounter_at, encounter_count, notes, created_at)
7. `observations` (id, observation_id, owner_id, candidate_scientific_name, matched_taxon_id, observation_timestamp, field_notes, coarse_location, model_result_json, gbif_result_json, taxonomic_resolution, moderation_status, provenance, created_at)
8. `badges` (id, code, name, description, rule_description, icon, xp_reward, created_at)
9. `user_badges` (id, user_id, badge_id, awarded_at)
10. `moderation_events` (id, observation_id, moderator_id, previous_status, new_status, moderation_note, created_at)
11. `audit_logs` (id, user_id, action, entity_type, entity_id, details, timestamp)

---

## 9. Security Controls
1. **PBKDF2 Hashing:** SHA-256 with 100,000 iterations and per-user 16-byte random salt.
2. **Timing Attack Protection:** Used `hmac.compare_digest` for password verification.
3. **No Password Exposure:** Passwords are never stored in plaintext, never logged, and never included in UI or API payloads.
4. **Parameterized SQL:** All database statements use `?` parameter bindings to eliminate SQL injection.
5. **Server-Side Authorization:** Every administrative method validates `AuthService.require_admin(user)`. Non-admin calls raise `AuthorizationError`.
6. **No GPS Storage:** Observations only store coarse locality strings.
7. **No Permanent Image Storage:** Uploaded organism photographs remain exclusively in volatile memory and are discarded after analysis.
8. **Clear Security Notice:** Permanent warning banner displayed across UI: `LOCAL PROTOTYPE — AUTHENTICATION IS NOT PRODUCTION-HARDENED.`

---

## 10. Knowledge Graph Implementation
- Implemented in SQLite without graph databases.
- Node types: `Taxon`, `Observation`, `User`, `Source`, `Badge`.
- Relationship edges: `PARENT_OF`, `SYNONYM_OF`, `OBSERVED_IN`, `RECORDED_BY`, `COLLECTED_BY`, `DERIVED_FROM`, `AWARDED_TO`.
- Generates hierarchy edges from GBIF response fields.
- Neighborhood query retrieves taxon nodes, hierarchy lineage, linked sightings, and collectors.

---

## 11. Tests Executed
1. `py -m pytest -v`
2. `py -m unittest discover -s tests -p "test_*.py" -v`

---

## 12. Test Results
- **Pytest Results:** **42 passed** in 11.73 seconds (100% pass rate).
- **Unittest Discover Results:** **42 passed** in 9.755 seconds (100% pass rate).
- **Scenarios Verified:**
  - 16 core backend unit tests (image validation, metadata strip, schemas, Meta adapter, GBIF adapter, pipeline orchestrator).
  - 3 UI component tests (fixture generation, JSON export schema, Streamlit AppTest load).
  - 23 platform evolution tests:
    1. Database initialization
    2. Database migrations
    3. Registration
    4. Duplicate username rejection
    5. Password hashing
    6. Password verification
    7. Login failure
    8. Logout
    9. First-user administrator bootstrap
    10. User role restrictions
    11. Collection creation
    12. Duplicate taxon collection handling
    13. Observation creation
    14. Field-note updates
    15. Badge awarding
    16. Badge idempotency
    17. XP calculations
    18. Admin-only dashboard access
    19. Admin moderation
    20. Audit log creation
    21. Knowledge graph relationships
    22. Taxonomy lineage
    23. Demo-data separation

---

## 13. Known Issues
- Single-node SQLite concurrency is limited by file locking during high-frequency parallel write bursts.
- Streamlit in-memory session state resets if the user refreshes their browser tab, requiring re-login in local prototype mode.

---

## 14. Deferred Features
- Production OAuth 2.0 / OpenID Connect provider integration.
- Verified ORCID OAuth authorization exchange.
- GraphRAG vector indexing or external graph database hosting.
- Social feed and community comments.
- Remote cloud image hosting or CDN storage.

---

## 15. Scope-Creep Assessment
All implemented features strictly map to the RUN 007 requirements. No external databases, heavy frameworks, or unnecessary dependencies were introduced. The codebase uses only standard library packages and existing project dependencies.

---

## 16. Git Branch and Commit
- **Branch:** `feat/platform-prototype`
- **Commit:** `edfc05e32f6694eb5b29f35138d7b1ffd14d28ea`
- **Working Tree:** Cleaned and ready for review.
- **Main Branch Protection:** `main` was left intact; no merge was performed.

---

## 17. Recommended Next Run
Review the completed platform prototype on branch `feat/platform-prototype`. Conduct interactive user acceptance testing in the browser at `http://localhost:8501`. Following review approval, merge `feat/platform-prototype` into `main`.
