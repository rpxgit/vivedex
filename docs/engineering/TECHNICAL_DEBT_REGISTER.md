# Vivédex Technical Debt Register

## 1. Executive Summary
This register catalogues verified engineering deficiencies, performance bottlenecks, architectural risks, and maintenance gaps in Vivédex.
Every entry contains empirical evidence, impact analysis, priority classification, and remediation estimates.
All findings adhere to the ASD-STE100 technical standard.

### Priority Classifications:
- **P0 (Critical):** Immediate operational or data security blocker. Prevents reliable execution.
- **P1 (High):** Architectural risk, concurrency blocker, or reliability defect. Must resolve before public pilot.
- **P2 (Medium):** Performance bottleneck, modularity deficiency, or maintainability risk.
- **P3 (Low):** Minor technical debt, code cleanliness, or cosmetic inconsistency.

---

## 2. Technical Debt Register

| Item ID | Category | Title | Priority | Estimated Effort |
|---|---|---|---|---|
| **DEBT-01** | Database | SQLite Default Journal Mode (Missing WAL Mode) | **P1** | 1 hour |
| **DEBT-02** | MLOps | Absence of Upstream Retry Logic with Exponential Backoff | **P1** | 3 hours |
| **DEBT-03** | Architecture | Synchronous Blocking HTTP Calls in UI Execution Thread | **P1** | 4 hours |
| **DEBT-04** | Performance | N+1 Sequential Database Connection Queries in Lineage Traversal | **P2** | 2 hours |
| **DEBT-05** | Performance | Unscaled Base64 Image Payload Transmission | **P2** | 2 hours |
| **DEBT-06** | MLOps | Hardcoded Prompt Strings and Lack of Semantic Versioning | **P2** | 2 hours |
| **DEBT-07** | MLOps | Discarded API Token Consumption and Cost Telemetry | **P2** | 2 hours |
| **DEBT-08** | Architecture | High Coupling and Mixed Responsibilities in CollectionService | **P2** | 6 hours |
| **DEBT-09** | Architecture | Inconsistent Data Contracts (Pydantic Schemas vs Dataclass Models) | **P2** | 4 hours |
| **DEBT-10** | CI/CD | Total Absence of Automated Continuous Integration (CI) Pipeline | **P2** | 3 hours |
| **DEBT-11** | Code Quality | Absence of Static Type Checking (mypy) and Automated Linting | **P2** | 3 hours |
| **DEBT-12** | Performance | Missing Cache Layer for Repeated GBIF Species Queries | **P3** | 2 hours |
| **DEBT-13** | Dependencies | Unused Declared Dependency (`httpx` in requirements.txt) | **P3** | 1 hour |
| **DEBT-14** | Deployment | Hardcoded Local Database Path Without Environment Variable Override | **P3** | 1 hour |

---

## 3. Detailed Technical Debt Analysis

### DEBT-01: SQLite Default Journal Mode (Missing WAL Mode)
- **Finding:** The SQLite connection does not enable Write-Ahead Logging (`WAL`).
- **Evidence:** `src/database.py` executes `PRAGMA foreign_keys = ON;` in `connect()` (line 92), but never configures `PRAGMA journal_mode = WAL;`.
- **Impact:** SQLite runs in default rollback journal mode. Any database write locks the entire database file, preventing concurrent reads from other Streamlit sessions. Under multi-user access, this raises `sqlite3.OperationalError: database is locked`.
- **Priority:** **P1**
- **Recommended Action:** Execute `conn.execute("PRAGMA journal_mode = WAL;")` during schema initialization.
- **Dependencies:** `src/database.py`.
- **Estimated Effort:** 1 hour.

---

### DEBT-02: Absence of Upstream Retry Logic with Exponential Backoff
- **Finding:** API adapter executes single-attempt HTTP calls without retries.
- **Evidence:** `src/meta_adapter.py` (lines 130-155) wraps `urllib.request.urlopen` in a single `try...except` block.
- **Impact:** Any transient network hiccup, HTTP 429 rate limit, or upstream 503 response immediately fails the user's observation analysis.
- **Priority:** **P1**
- **Recommended Action:** Wrap inference calls with a retry loop using exponential backoff and random jitter. Retry only transient status codes (429, 502, 503, 504) up to 3 times.
- **Dependencies:** None.
- **Estimated Effort:** 3 hours.

---

### DEBT-03: Synchronous Blocking HTTP Calls in UI Execution Thread
- **Finding:** Remote API requests execute synchronously within the Streamlit session thread.
- **Evidence:** `src/meta_adapter.py` and `src/gbif_adapter.py` block execution for up to 30 seconds inside `VivedexBackend.process_observation()`.
- **Impact:** The browser websocket connection blocks. The UI freezes with no granular progress feedback until both network calls resolve.
- **Priority:** **P1**
- **Recommended Action:** Offload inference calls to background threads using Python `concurrent.futures.ThreadPoolExecutor`. Provide granular progress stages to Streamlit.
- **Dependencies:** `src/backend.py`, `src/ui/page_identify.py`.
- **Estimated Effort:** 4 hours.

---

### DEBT-04: N+1 Sequential Database Connection Queries in Lineage Traversal
- **Finding:** `KnowledgeGraphService.get_taxon_lineage` opens and closes a new database connection for each taxonomic level in a `while` loop.
- **Evidence:** `src/knowledge_graph.py` (lines 89-111) executes:
  ```python
  while current_id is not None and current_id not in visited:
      taxon = self.get_taxon_by_id(current_id)  # Opens and closes connection 1
      with self.db.connect() as conn:          # Opens and closes connection 2
          cursor.execute("SELECT parent_taxon_id FROM taxon_relationships ...")
  ```
- **Impact:** Resolving an 8-level taxonomic lineage opens and closes SQLite connections 16 consecutive times. This causes unnecessary filesystem lock cycling and degrades page render performance.
- **Priority:** **P2**
- **Recommended Action:** Rewrite lineage retrieval as a single SQL query using a recursive Common Table Expression (`WITH RECURSIVE lineage AS (...)`). Execute within a single connection.
- **Dependencies:** `src/knowledge_graph.py`.
- **Estimated Effort:** 2 hours.

---

### DEBT-05: Unscaled Base64 Image Payload Transmission
- **Finding:** Full-resolution uploaded images are encoded to Base64 without downscaling.
- **Evidence:** `src/image_processor.py` accepts images up to 8 MB. An 8 MB image produces an ~11 MB Base64 payload string transmitted to Meta Model API.
- **Impact:** Excessive memory consumption during string serialization, increased network upload time, and higher API bandwidth costs.
- **Priority:** **P2**
- **Recommended Action:** Downscale images in memory to a maximum bounding box of $1600 \times 1600$ pixels before Base64 encoding. This preserves diagnostic morphological features while reducing payload size by up to 75%.
- **Dependencies:** `src/image_processor.py`.
- **Estimated Effort:** 2 hours.

---

### DEBT-06: Hardcoded Prompt Strings and Lack of Semantic Versioning
- **Finding:** System instructions are stored as an immutable string constant without semantic versioning.
- **Evidence:** `MetaAPIAdapter.SYSTEM_PROMPT` is hardcoded at lines 42-63 of `src/meta_adapter.py`.
- **Impact:** Model prompts cannot be versioned, tested, or correlated with model hallucinations across runs.
- **Priority:** **P2**
- **Recommended Action:** Move prompts to external versioned files (e.g., `prompts/organism_v1.0.txt`). Record `prompt_version` in the observation database.
- **Dependencies:** `src/meta_adapter.py`, `src/schemas.py`.
- **Estimated Effort:** 2 hours.

---

### DEBT-07: Discarded API Token Consumption and Cost Telemetry
- **Finding:** The API response `usage` field containing token counts is discarded.
- **Evidence:** `src/meta_adapter.py` parses `raw_json["choices"][0]["message"]["content"]`, but ignores `raw_json.get("usage")`.
- **Impact:** Platform administrators cannot audit token usage, forecast inference costs, or track model operational expenses.
- **Priority:** **P2**
- **Recommended Action:** Capture `prompt_tokens`, `completion_tokens`, and `total_tokens`. Store in an operational telemetry table.
- **Dependencies:** `src/schemas.py`, `src/database.py`.
- **Estimated Effort:** 2 hours.

---

### DEBT-08: High Coupling and Mixed Responsibilities in CollectionService
- **Finding:** `CollectionService` manages disparate domains across taxa, observations, collections, profiles, and achievements.
- **Evidence:** `src/collection_service.py` spans 683 lines, exposes 12 distinct methods, and directly instantiates `AchievementService(db)` internally (line 31).
- **Impact:** Testing and maintaining collection logic requires understanding unrelated domains. Changes to one domain risk regressions in another.
- **Priority:** **P2**
- **Recommended Action:** Refactor `CollectionService` into single-responsibility services: `ObservationService`, `TaxonService`, `CollectionService`, and `ProfileService`. Dispatch events to trigger achievements.
- **Dependencies:** `src/models.py`, `src/database.py`.
- **Estimated Effort:** 6 hours.

---

### DEBT-09: Inconsistent Data Contracts Across Layers
- **Finding:** The application mixes Pydantic schemas and plain Python dataclasses across boundaries.
- **Evidence:** `src/schemas.py` uses Pydantic BaseModel. `src/models.py` uses `@dataclass`. `src/collection_service.py` uses multiple `getattr` fallback chains to read attributes.
- **Impact:** Reduces code clarity and risks silent runtime `AttributeError` defects when schemas change.
- **Priority:** **P2**
- **Recommended Action:** Standardize data boundaries. Use Pydantic models for external API input/output validation. Use domain entities for internal database operations.
- **Dependencies:** `src/schemas.py`, `src/models.py`.
- **Estimated Effort:** 4 hours.

---

### DEBT-10: Total Absence of Automated Continuous Integration (CI) Pipeline
- **Finding:** The repository contains no continuous integration configuration.
- **Evidence:** No `.github/workflows/` directory exists. All test runs are executed manually by developers.
- **Impact:** Breaking changes or broken tests can be committed and pushed to remote branches undetected.
- **Priority:** **P2**
- **Recommended Action:** Create `.github/workflows/ci.yml` running `pytest` across Python 3.10, 3.11, 3.12, and 3.14 on pull requests and pushes to `main` and `feat/*`.
- **Dependencies:** GitHub repository settings.
- **Estimated Effort:** 3 hours.

---

### DEBT-11: Absence of Static Type Checking (mypy) and Automated Linting
- **Finding:** No static type checker (mypy) or linter (ruff, flake8) is configured.
- **Evidence:** No `pyproject.toml`, `setup.cfg`, or linting configuration files exist in the repository root.
- **Impact:** Type errors, undefined variables, and inconsistent styling accumulate unnoticed.
- **Priority:** **P2**
- **Recommended Action:** Add `pyproject.toml` with configurations for `ruff` and `mypy`. Integrate into pre-commit and CI.
- **Dependencies:** None.
- **Estimated Effort:** 3 hours.

---

### DEBT-12: Missing Cache Layer for Repeated GBIF Species Queries
- **Finding:** Repeated searches for the same scientific name trigger redundant HTTP requests to GBIF.
- **Evidence:** `GBIFAdapter.match_species()` performs a live HTTP request on every invocation without an in-memory or database cache check.
- **Impact:** Unnecessary external network requests, increased latency, and potential upstream rate limiting.
- **Priority:** **P3**
- **Recommended Action:** Add `@functools.lru_cache(maxsize=1024)` or check the local `taxa` table before making an external GBIF request.
- **Dependencies:** `src/gbif_adapter.py`.
- **Estimated Effort:** 2 hours.

---

### DEBT-13: Unused Declared Dependency (`httpx` in requirements.txt)
- **Finding:** `httpx` is declared in `requirements.txt` but never imported in application code.
- **Evidence:** `requirements.txt` contains `httpx>=0.25.0`. Grep confirms zero occurrences of `import httpx` in `src/`.
- **Impact:** Wastes disk space and developer bandwidth during environment setup.
- **Priority:** **P3**
- **Recommended Action:** Either adopt `httpx` across API adapters to replace `urllib`, or remove it from `requirements.txt`.
- **Dependencies:** `requirements.txt`.
- **Estimated Effort:** 1 hour.

---

### DEBT-14: Hardcoded Local Database Path Without Environment Variable Override
- **Finding:** The SQLite database file path is relative to the codebase without environment variable configuration.
- **Evidence:** `src/database.py` defines `DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "vivedex.sqlite3"`.
- **Impact:** Deploying in containerized environments requires mounting the internal code directory or modifying source code.
- **Priority:** **P3**
- **Recommended Action:** Read `VIVEDEX_DB_PATH` from `os.getenv()`, falling back to `DEFAULT_DB_PATH`.
- **Dependencies:** `src/database.py`.
- **Estimated Effort:** 1 hour.

