# RUN 008 — Systems Engineering and MLOps Assessment

## 1. Objective
Conduct a comprehensive systems engineering, architecture, database, MLOps, and deployment assessment of Vivédex.
Audit the complete platform without modifying application source code or altering existing user records.
Identify technical debt, architectural risks, performance bottlenecks, and reliability gaps.
Produce formal engineering reviews and a technical debt register conforming to the ASD-STE100 standard.

---

## 2. Repository State
- **Working Branch:** `feat/platform-prototype`
- **Base Branch:** `main`
- **Host OS:** Windows 11
- **Python Runtime:** Python 3.14.7 (`C:\Users\HP\AppData\Local\Python\pythoncore-3.14-64\python.exe`)
- **Web Framework:** Streamlit 1.66.1
- **Database:** Local SQLite database at `data/vivedex.sqlite3` (10 tables, schema version 1, foreign keys enabled)
- **Node.js / npm:** Not installed on host environment.
- **Git State:** 3 commits ahead of remote tracking branch. Working tree is clean.

---

## 3. Files Inspected
The reconnaissance audited the entire codebase:
1. **Application Entry Point:**
   - `app.py`
2. **Backend & Adapters:**
   - `src/backend.py`
   - `src/meta_adapter.py`
   - `src/gbif_adapter.py`
   - `src/image_processor.py`
   - `src/fixtures.py`
   - `src/__init__.py`
3. **Database & Data Layer:**
   - `src/database.py`
   - `src/models.py`
   - `src/schemas.py`
   - `src/demo_data.py`
   - `data/vivedex.sqlite3`
4. **Domain Services:**
   - `src/auth.py`
   - `src/collection_service.py`
   - `src/admin_service.py`
   - `src/achievements.py`
   - `src/knowledge_graph.py`
5. **Presentation & Theme Modules:**
   - `src/ui/theme.py`
   - `src/ui/common.py`
   - `src/ui/page_home.py`
   - `src/ui/page_explore.py`
   - `src/ui/page_identify.py`
   - `src/ui/page_collection.py`
   - `src/ui/page_journal.py`
   - `src/ui/page_knowledge.py`
   - `src/ui/page_achievements.py`
   - `src/ui/page_profile.py`
   - `src/ui/page_admin.py`
   - `src/ui/page_species_detail.py`
6. **Tests:**
   - `tests/test_backend.py`
   - `tests/test_platform.py`
   - `tests/test_ui.py`
   - `tests/test_ui_experience.py`
7. **Documentation & Run Logs:**
   - `README.md`
   - `docs/MVP_SPEC.md`
   - `docs/PLATFORM_SPEC.md`
   - `docs/API_NOTES.md`
   - `docs/DATA_MODEL.md`
   - `docs/DESIGN_RECONNAISSANCE.md`
   - `docs/EXPERIENCE_DESIGN_SPEC.md`
   - `docs/TECHNOLOGY_DECISION_RECORD.md`
   - `docs/run-logs/001-gemini-preflight.md` through `docs/run-logs/007b-experience-reconstruction.md`

---

## 4. Architecture Findings
1. **Synchronous Blocking I/O (P1):** API calls to Meta Model API and GBIF block the primary Streamlit thread for up to 30 seconds.
2. **High Coupling in CollectionService (P2):** `CollectionService` manages five distinct domains across 683 lines of code.
3. **Missing Abstract Interfaces (P2):** Adapters lack formal `typing.Protocol` interfaces, requiring concrete class monkeypatching in tests.
4. **Inconsistent Data Contracts (P2):** Pydantic schemas and plain dataclasses are mixed across boundaries, requiring fragile `getattr` chains.
5. **Unused Declared Dependency (P3):** `httpx` is listed in `requirements.txt` but never imported in source code.

---

## 5. MLOps Findings
1. **Absence of Retry Logic (P1):** Meta Model API requests fail immediately on transient network drops or HTTP 429 rate limits without backoff.
2. **Hardcoded Prompt Strings (P2):** System prompts are hardcoded constants in source code without semantic versioning.
3. **Discarded Cost Telemetry (P2):** Token usage (`prompt_tokens`, `completion_tokens`) returned in API responses is discarded during parsing.
4. **Reproducibility Gaps (P2):** Observation records store model output but do not preserve the input image SHA-256 digest or prompt version.

---

## 6. Database Findings
1. **Missing WAL Journal Mode (P1):** SQLite operates in default rollback journal mode. Concurrent writes lock the database file, blocking concurrent readers in multi-session environments.
2. **N+1 Connection Cycling (P2):** `KnowledgeGraphService.get_taxon_lineage` opens and closes SQLite connections 16 consecutive times during an 8-level taxonomic traversal.
3. **Hardcoded File Path (P3):** The SQLite database path is relative to the source tree without `VIVEDEX_DB_PATH` environment variable support.
4. **PostgreSQL Migration Path:** For Stage 3 (Closed Pilot) and beyond, PostgreSQL is required to support concurrent multi-user writes, connection pooling, and managed backups.

---

## 7. Performance Findings
1. **Unscaled Base64 Image Payload (P2):** Images up to 8 MB are encoded directly to Base64 (~11 MB string), causing network upload latency and high memory consumption. Pre-scaling to $1600 \times 1600$ pixels will reduce payload size by up to 75%.
2. **Missing GBIF Query Caching (P3):** Repeated searches for identical scientific names make redundant external network calls instead of consulting an LRU cache or local `taxa` table.

---

## 8. Deployment Findings
1. **Absence of Formal Health Check Endpoint (P2):** No probe endpoint exists to verify database read/write health for cloud load balancers.
2. **Lack of Automated CI Pipeline (P2):** No GitHub Actions workflows exist. All automated tests are currently executed manually.
3. **Lack of Static Analysis (P2):** No linter (`ruff`) or static type checker (`mypy`) is configured in the repository.

---

## 9. Docker Recommendation
- **Decision:** **DO NOT introduce Docker for the current local prototype or private Windows development workflow.**
- **Rationale:** Native execution on Windows with Python 3.14 provides maximum developer velocity (1.5-second startup). Docker Desktop on Windows adds virtualization overhead, licensing constraints, and known SQLite file-locking bugs over WSL2/virtiofs mount points.
- **Adoption Roadmap:** Defer Docker containerization to **Stage 3 (Closed Pilot)** when deploying to Linux-based cloud infrastructure (Google Cloud Run / AWS ECS).

---

## 10. Documents Created
The following engineering review documents were authored in `docs/engineering/`:
1. `docs/engineering/SYSTEM_ARCHITECTURE_REVIEW.md` (System architecture, component coupling, target modular monolith design).
2. `docs/engineering/MLOPS_REVIEW.md` (Meta Muse Spark integration, knowledge architecture comparison, observability schema, evaluation framework).
3. `docs/engineering/DEPLOYMENT_STRATEGY.md` (Docker decision, lifecycle infrastructure classification from hackathon to production, container implementation backlog).
4. `docs/engineering/TECHNICAL_DEBT_REGISTER.md` (Comprehensive register of 14 technical debt items classified P1–P3 with evidence and remediation effort).
5. `docs/run-logs/008-systems-mlops-audit.md` (This document).

---

## 11. Tests Executed
Executed the full automated test suite using Python 3.14 to verify baseline stability during the read-only audit:
- `py -m pytest -v`:
  - `tests/test_backend.py`: 16 passed.
  - `tests/test_platform.py`: 23 passed.
  - `tests/test_ui.py`: 3 passed.
  - `tests/test_ui_experience.py`: 4 passed.
  - Total: **46 passed in 21.65s**.
- Zero source code files were modified.

---

## 12. Unverified Items
1. Upstream Meta Model API token quotas and rate limits under sustained concurrent load (> 10 requests/minute).
2. SQLite write concurrency performance when 20+ active Streamlit sessions perform concurrent image analyses.

---

## 13. Recommended Next Steps (Priority Order)
1. **Enable SQLite WAL Mode (P1):** Add `PRAGMA journal_mode = WAL;` to eliminate database locking under concurrent access.
2. **Add Upstream Retry with Exponential Backoff (P1):** Protect `MetaAPIAdapter` against transient network drops and rate limits.
3. **Implement Image Downscaling (P2):** Add $1600 \times 1600$ pixel maximum dimension bounding box in `ImageProcessor` to cut Base64 payload sizes.
4. **Optimize Lineage Traversal (P2):** Replace iterative N+1 query loop in `KnowledgeGraphService` with a single recursive CTE.
5. **Establish GitHub Actions CI Workflow (P2):** Automate test execution on all pull requests and branches.
