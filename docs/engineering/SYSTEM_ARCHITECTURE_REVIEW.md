# Vivédex System Architecture Review

## 1. Executive Summary
This document provides a comprehensive systems engineering and architectural assessment of Vivédex.
It reviews the current architecture, module responsibilities, component dependencies, and data flows.
It establishes target design recommendations for future pilot and production deployments.
All findings adhere to the ASD-STE100 technical writing standard.

---

## 2. Current Architecture Baseline

### 2.1 High-Level Architecture
Vivédex is currently implemented as a single-process, local-first monolithic Python application.
The application stack contains:
- **Presentation Layer:** Streamlit 1.66.1 multi-page router with injected CSS design tokens and Google Fonts.
- **Application & Domain Services Layer:** Python domain services managing authentication, collections, observations, gamification, and knowledge traversal.
- **Inference & Reconciliation Pipeline:** Synchronous adapters communicating with the Meta Model API (`muse-spark-1.3`) and the GBIF Species Match API.
- **Data Persistence Layer:** Local SQLite database (`data/vivedex.sqlite3`) enforcing foreign keys and schema versioning.

### 2.2 Component Dependency Diagram (Current)
```
┌────────────────────────────────────────────────────────────────────────┐
│                        Streamlit UI (app.py)                           │
│   (Home • Explore • Identify • My Dex • Journal • Badges • Profile)    │
│                        Admin Console (Restricted)                      │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
     ┌───────────────────────────────┼──────────────────────────────┐
     ▼                               ▼                              ▼
┌───────────────┐           ┌───────────────┐              ┌────────────────┐
│ VivedexBackend│           │ AuthService   │              │AdminService    │
│ (src/backend) │           │ (src/auth)    │              │(src/admin_srv) │
└───────┬───────┘           └───────┬───────┘              └───────┬────────┘
        │                           │                              │
        ├───────────────┐           │                              │
        ▼               ▼           │                              │
┌───────────────┐ ┌───────────────┐ │                              │
│ImageProcessor │ │MetaAPIAdapter │ │                              │
│(in-memory)    │ │(muse-spark)   │ │                              │
└───────────────┘ └───────────────┘ │                              │
        │                           │                              │
        ▼                           │                              │
┌───────────────┐                   │                              │
│ GBIFAdapter   │                   │                              │
│ (api.gbif.org)│                   │                              │
└───────┬───────┘                   │                              │
        │                           ▼                              │
        │                  ┌───────────────────┐                   │
        └─────────────────►│ CollectionService │◄──────────────────┤
                           │ (src/collection)  │                   │
                           └─────────┬─────────┘                   │
                                     │                             │
                                     ▼                             ▼
                           ┌───────────────────┐          ┌─────────────────┐
                           │AchievementService │          │KnowledgeGraphSrv│
                           │(src/achievements) │          │(src/knowledge)  │
                           └─────────┬─────────┘          └────────┬────────┘
                                     │                             │
                                     └──────────────┬──────────────┘
                                                    │
                                                    ▼
                                          ┌───────────────────┐
                                          │   Database Repo   │
                                          │ (src/database.py) │
                                          └─────────┬─────────┘
                                                    │
                                                    ▼
                                          ┌───────────────────┐
                                          │  data/vivedex.db  │
                                          │     (SQLite3)     │
                                          └───────────────────┘
```

---

## 3. Architecture Findings and Technical Evaluation

### Finding ARCH-01: Blocking Synchronous I/O in Streamlit Execution Thread
- **Finding:** External HTTP calls to Meta Model API and GBIF run synchronously in the primary Streamlit script thread.
- **Evidence:** `src/meta_adapter.py` (lines 130-136) and `src/gbif_adapter.py` (lines 70-76) use `urllib.request.urlopen` with blocking timeouts up to 30 seconds.
- **Impact:** While an API call executes, the Streamlit session thread is locked. Slow network connections or upstream rate limits freeze the user interface.
- **Priority:** P1
- **Recommended Action:** Use asynchronous HTTP clients (`httpx.AsyncClient`) or execute long-running inference in background worker threads with Streamlit progress callbacks.
- **Dependencies:** None.
- **Estimated Effort:** 4 hours.

### Finding ARCH-02: High Coupling and Mixed Responsibilities in CollectionService
- **Finding:** `CollectionService` manages disparate domains including taxon upserts, observations, personal collections, researcher profiles, and badge evaluation.
- **Evidence:** `src/collection_service.py` contains 683 lines, 12 public methods, and directly instantiates `AchievementService(db)` internally (line 31).
- **Impact:** Any modification to collection logic risks breaking observation or achievement behavior. Testing requires mocking multiple domains.
- **Priority:** P2
- **Recommended Action:** Decompose `CollectionService` into single-responsibility domain services: `ObservationService`, `TaxonService`, `CollectionService`, and `ProfileService`. Pass domain events to trigger achievements.
- **Dependencies:** `src/models.py`, `src/database.py`.
- **Estimated Effort:** 6 hours.

### Finding ARCH-03: Missing Formal Service Interfaces (Protocols)
- **Finding:** Adapters and services lack abstract interface definitions.
- **Evidence:** `VivedexBackend` accepts optional `MetaAPIAdapter` and `GBIFAdapter`, but references concrete classes instead of abstract protocols (`typing.Protocol`).
- **Impact:** Unit testing requires patching concrete network classes. Replacing Meta Muse Spark with another model provider requires altering adapter invocations.
- **Priority:** P2
- **Recommended Action:** Define `VisionModelProtocol` and `TaxonomyProviderProtocol` in `src/interfaces.py`. Implement adapters against these contracts.
- **Dependencies:** None.
- **Estimated Effort:** 3 hours.

### Finding ARCH-04: Inconsistent Data Contracts Across Layers
- **Finding:** The system mixes Pydantic models and plain Python dataclasses across module boundaries.
- **Evidence:** `src/schemas.py` defines Pydantic schemas (`CandidateIdentification`, `ModelIdentificationResult`, `GBIFMatchResult`). `src/models.py` defines standard dataclasses (`TaxonRecord`, `ObservationRecord`). In `src/collection_service.py` (lines 43-85), methods use complex `getattr` chains to handle both Pydantic models and raw dictionaries.
- **Impact:** Runtime attribute lookup errors can occur if schemas evolve. Maintenance overhead increases.
- **Priority:** P2
- **Recommended Action:** Standardize data boundaries. Use Pydantic models for external data validation and serialized data transfer. Use domain entities for internal database operations.
- **Dependencies:** `src/schemas.py`, `src/models.py`.
- **Estimated Effort:** 5 hours.

### Finding ARCH-05: Unused Declared Dependency
- **Finding:** `httpx` is declared in `requirements.txt` but never imported in application source code.
- **Evidence:** `requirements.txt` specifies `httpx>=0.25.0`. Searching the `src/` directory confirms zero occurrences of `import httpx`.
- **Impact:** Unnecessary installation footprint and false dependency perception.
- **Priority:** P3
- **Recommended Action:** Either adopt `httpx` across `meta_adapter.py` and `gbif_adapter.py` to replace `urllib`, or remove `httpx` from `requirements.txt`.
- **Dependencies:** `requirements.txt`.
- **Estimated Effort:** 1 hour.

---

## 4. Target Architecture Recommendation

### 4.1 Recommendation: Clean Modular Monolith
We recommend maintaining a **Modular Monolith** architecture for the closed pilot and private development stages.
Do not introduce microservices.
Microservices introduce network serialization latency, multi-container orchestration overhead, and operational complexity.
The modular monolith will scale effectively to 5,000+ active naturalists when supported by PostgreSQL and connection pooling.

### 4.2 Target Layered Architecture Diagram
```
┌────────────────────────────────────────────────────────────────────────┐
│                        User Interface Layer                            │
│           Streamlit 1.66+ (or Future React SPA / Mobile App)           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        Application API Layer                           │
│                 FastAPI REST Routers & OpenAPI Spec                    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
       ┌────────────────────────────┼────────────────────────────┐
       ▼                            ▼                            ▼
┌──────────────┐             ┌──────────────┐             ┌──────────────┐
│  Auth Engine │             │Observation Srv│            │Taxonomy Srv  │
│  (RBAC/JWT)  │             │& Moderation  │             │& Knowledge   │
└──────┬───────┘             └──────┬───────┘             └──────┬───────┘
       │                            │                            │
       └────────────────────────────┼────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     Domain Services & Interfaces                       │
│    VisionModelProtocol (Meta)  •  TaxonomyProviderProtocol (GBIF)      │
│                     Gamification & Event Dispatcher                    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
       ┌────────────────────────────┴────────────────────────────┐
       ▼                                                         ▼
┌──────────────┐                                          ┌──────────────┐
│  Cache Layer │                                          │ Repository   │
│ (Redis / LRU)│                                          │ Pattern (SQL)│
└──────────────┘                                          └──────┬───────┘
                                                                 │
                                                                 ▼
                                                          ┌──────────────┐
                                                          │  PostgreSQL  │
                                                          │(Managed Cloud│
                                                          └──────────────┘
```

### 4.3 Architecture Transition Roadmap
1. **Phase 1 (Immediate):**
   - Introduce `typing.Protocol` interfaces for adapters.
   - Separate `CollectionService` into focused domain modules.
   - Add in-memory caching (`functools.lru_cache` or `st.cache_data`) for GBIF queries.
2. **Phase 2 (Pilot Readiness):**
   - Wrap domain services in clean service layers independent of Streamlit `st.session_state`.
   - Prepare database repository for PostgreSQL driver (`psycopg3` or SQLAlchemy).
3. **Phase 3 (Scale):**
   - Extract FastAPI endpoints for native mobile or external client access.
   - Move long-running inference tasks to a lightweight asynchronous task queue (Celery or RQ).
