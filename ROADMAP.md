# Vivédex Development Roadmap

This document outlines the strategic engineering roadmap for Vivédex.

Writing standard: ASD-STE100.  
Status classification:
- **COMPLETE:** Implemented in codebase and verified by automated tests.
- **IN PROGRESS:** Partially implemented; components active in current release candidate.
- **PLANNED:** Architectural design established; implementation scheduled for future cycles.

---

## 1. Phase 1 — Hackathon Release Candidate (v0.1.0)
**Objective:** Deliver an end-to-end, locally runnable biodiversity discovery platform with verified security, botanical UI, and BYOK AI integration.

| Capability | Scope / Deliverable | Status | Evidence in Repository |
|---|---|---|---|
| Multimodal AI Inference | Meta Muse Spark (`muse-spark-1.3`) structured JSON extraction | **COMPLETE** | `src/meta_adapter.py`, `src/backend.py` |
| Taxonomic Reconciliation | GBIF Species Match API integration with caching | **COMPLETE** | `src/gbif_adapter.py` |
| In-Memory Image Sanitization | MIME validation and EXIF metadata stripping | **COMPLETE** | `src/image_processor.py` |
| Personal Collection ("My Dex") | First encounters, encounter counts, species notes | **COMPLETE** | `src/collection_service.py`, `src/ui/page_collection.py` |
| Field Journal | Observation log, status tracking, coarse location | **COMPLETE** | `src/ui/page_journal.py` |
| Ecological Context (Restor) | Field sites, monitored ecosystems, dynamic richness | **COMPLETE** | `src/ecological_service.py`, `src/ui/page_sites_projects.py` |
| Habit Progression (Habitica) | Daily habits, BioBlitz quests, XP reward engine | **COMPLETE** | `src/quest_service.py`, `src/achievements.py` |
| Researcher Identity (ORCID) | Contributor ID (`VDX-XXXXXX`), provenance states | **COMPLETE** | `src/passport_service.py`, `src/ui/page_profile.py` |
| Taxonomic Knowledge Graph | SQLite parent-child taxonomy graph traversal | **COMPLETE** | `src/knowledge_graph.py`, `src/ui/page_knowledge.py` |
| Security Hardening | PBKDF2 hashing, RBAC, input escaping, size limits | **COMPLETE** | `src/auth.py`, `tests/test_security.py` |
| BYOK Credential Settings | User-owned Meta API key with volatile session isolation | **COMPLETE** | `src/ui/page_settings.py`, `tests/test_api_credentials.py` |
| Windows Launcher & Checks | PowerShell initialization, pre-flight check, Batch launcher | **COMPLETE** | `Launch-Vivedex.bat`, `scripts/` |

---

## 2. Phase 2 — Personal Biodiversity Platform
**Objective:** Enhance field usability for naturalists and amateur botanists during field expeditions.

| Capability | Scope / Deliverable | Status | Repository Evidence / Notes |
|---|---|---|---|
| Offline Local Cache | Offline SQLite caching of GBIF taxonomic trees | **IN PROGRESS** | SQLite cache tables exist in `src/database.py` |
| Audio & Voice Notes | Voice memo capture and local transcription | **PLANNED** | Requires audio processing dependency |
| Multi-Specimen Batching | Batch upload of multiple field photos per sighting | **PLANNED** | Database schema supports multiple image keys |
| Custom User Tags & Filters | Custom field tags (phenology, flower color, habitat) | **IN PROGRESS** | Search service supports basic tag filtering |
| Export Formats | Darwin Core Archive (DwC-A) and CSV exports | **IN PROGRESS** | JSON export active (`VivedexResult.to_json()`) |

---

## 3. Phase 3 — Community Contribution Network
**Objective:** Connect independent naturalists into collaborative regional monitoring networks.

| Capability | Scope / Deliverable | Status | Repository Evidence / Notes |
|---|---|---|---|
| Community Peer Verification | Naturalists vote on proposed candidate identifications | **PLANNED** | Moderation statuses exist in `src/database.py` |
| Regional BioBlitz Challenges | Time-limited collaborative bio-surveys for field sites | **IN PROGRESS** | Project expeditions active in `src/ecological_service.py` |
| Moderation Review Queue | Multi-stage review by accredited taxonomic curators | **IN PROGRESS** | Admin console moderation tab active in `src/ui/page_admin.py` |
| Contributor Attribution Feed | Transparent activity feed showing recent verified finds | **IN PROGRESS** | Public expedition hub displays catalog finds |

---

## 4. Phase 4 — Knowledge Infrastructure & Interoperability
**Objective:** Integrate Vivédex with institutional biodiversity repositories and semantic graphs.

| Capability | Scope / Deliverable | Status | Repository Evidence / Notes |
|---|---|---|---|
| GBIF Occurrence Ingestion | Query and display historical GBIF occurrence density maps | **PLANNED** | Currently uses GBIF Species API exclusively |
| Semantic Knowledge Graph | Export local taxonomic graph to RDF / OWL ontologies | **PLANNED** | SQLite edge structure designed for graph extraction |
| iNaturalist & eBird Bridges | Import user observation histories via public APIs | **PLANNED** | Requires external API connectors |
| Multimodal Edge Models | Quantized on-device vision models (WebAssembly / ONNX) | **PLANNED** | Eliminates external API latency |

---

## 5. Phase 5 — Institutional & Sponsor Platform
**Objective:** Provide botanical gardens, universities, and conservation trusts with managed deployment and research analytics.

| Capability | Scope / Deliverable | Status | Repository Evidence / Notes |
|---|---|---|---|
| Single Sign-On (SSO) | Institutional SAML 2.0 and OpenID Connect (OIDC) | **PLANNED** | Replaces local PBKDF2 for enterprise users |
| Official ORCID API Integration | Live OAuth2 sync with formal ORCID public researcher registry | **PLANNED** | Passport data model ready for ORCID synchronization |
| Site Ecological Impact Metrics | Long-term biodiversity trend analysis and restoration tracking | **PLANNED** | Extends dynamic species richness service |
| Multi-Tenant Data Partitioning | Isolated workspaces for private conservation projects | **PLANNED** | Requires schema migration to tenant isolation |

