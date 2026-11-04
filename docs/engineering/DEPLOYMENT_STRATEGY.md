# Vivédex Deployment Strategy and Containerization Assessment

## 1. Executive Summary
This document provides an engineering evaluation of the deployment architecture, developer workflow, and containerization strategy for Vivédex.
It establishes an explicit, evidence-based Docker decision.
It classifies the infrastructure requirements across five distinct platform lifecycle stages.
All recommendations adhere to the ASD-STE100 technical standard.

---

## 2. Explicit Docker Decision and Infrastructure Comparison

### 2.1 The Docker Decision
**Decision: DO NOT introduce Docker for the current local prototype or private Windows development workflow. Adopt Docker and Docker Compose starting at Stage 3 (Closed Pilot).**

### 2.2 Infrastructure Comparison Matrix

| Deployment Model | Windows Dev Friction | Environment Parity | Data Persistence Complexity | Operational Overhead | Recommendation |
|---|---|---|---|---|---|
| **Direct Execution (`py -m streamlit run app.py`)** | **Zero:** Native execution on Windows with virtual environments. | Low across diverse OS platforms. | **Zero:** Direct file access to `data/vivedex.sqlite3`. | Minimal | **Retain for Stage 1 & 2** |
| **Local Docker Engine** | **High on Windows:** Requires WSL2, Docker Desktop licensing, virtualization overhead. | High: Fixed Linux container environment. | Medium: Requires Docker volume mounts with Windows file permission mapping. | Moderate | **Defer to Stage 3** |
| **Docker Compose (App + Postgres)** | Medium: Orchestrates multi-container local stack. | Very High: Matches production containers. | Clean: Named volume mounts for PostgreSQL and media assets. | Moderate | **Target for Stage 3 & 4** |
| **Managed Cloud (Cloud Run / ECS + Cloud SQL)** | None for local developers. | Complete: Fully managed cloud containers and databases. | Fully Managed: Automated backups, multi-AZ replication. | Low runtime maintenance, higher cloud cost. | **Target for Stage 4 & 5** |

### 2.3 Rationale for Deferring Docker
1. **Developer Velocity on Windows:** The local workspace is Windows 11 with native Python 3.14. Running Streamlit natively takes 1.5 seconds. Forcing Docker Desktop on Windows requires virtualization, WSL2 setup, and port forwarding, creating friction with zero product benefit for local hacking.
2. **SQLite Locking in Docker Mounts:** Mounting a host Windows NTFS directory into a Linux container running SQLite frequently causes file-locking collisions (`database is locked`) due to 9P/virtiofs filesystem translation bugs.
3. **No Multi-Tier Dependencies in Prototype:** The application currently requires only Python and SQLite. There are no secondary services (Redis, Elasticsearch, Celery workers) that require multi-container orchestration at this stage.

---

## 3. Platform Lifecycle Stages and Infrastructure Classification

### Stage 1: Hackathon Demonstration
- **Target Audience:** Judges, reviewers, and project evaluators (1–5 concurrent users).
- **Execution Model:** Direct Python execution (`py -m streamlit run app.py --server.port 8501`).
- **Database:** Local SQLite database (`data/vivedex.sqlite3`) with pre-seeded demo records.
- **Secrets Management:** Local `.env` file containing `MODEL_API_KEY`.
- **Infrastructure Requirements:** Standard developer laptop or single virtual machine.
- **Monitoring & Logging:** Standard console logging and Streamlit UI error boundaries.

### Stage 2: Private Development
- **Target Audience:** Core project developers and contributors (1–3 developers).
- **Execution Model:** Direct Python execution with virtual environment (`venv`).
- **Database:** Local SQLite database with schema version tracking.
- **Secrets Management:** `.env` template (`.env.example`) with Git exclusion via `.gitignore`.
- **Quality Gates:** Manual or local automated test execution (`py -m pytest -v`).
- **Infrastructure Requirements:** Standard workstation with Python 3.10+.

### Stage 3: Closed Pilot
- **Target Audience:** Invited field naturalists and academic partners (50–200 registered users).
- **Execution Model:** Single containerized instance deployed to Google Cloud Run, AWS App Runner, or a dedicated Linux VM.
- **Container Architecture:** Standard Linux-based Docker image (`python:3.12-slim`) with non-root user execution.
- **Database:** Managed Cloud PostgreSQL (e.g., Google Cloud SQL or AWS RDS Aurora Serverless v2) or persistent container volume with SQLite in WAL mode.
- **Secrets Management:** Cloud Secret Manager or container environment variables injected at runtime.
- **Health Checks:** HTTP probe on `/` or custom `/healthz` endpoint returning HTTP 200.
- **Backups:** Daily automated database snapshots.

### Stage 4: Public Beta
- **Target Audience:** Broader naturalist and student communities (1,000–10,000 users).
- **Execution Model:** Decoupled architecture:
  - Frontend: Streamlit or lightweight React SPA on Cloud CDN / Cloud Run.
  - Backend: FastAPI application running in auto-scaling container fleet.
- **Database:** Managed PostgreSQL with connection pooling (PgBouncer).
- **Caching:** Redis instance for GBIF taxonomy lookup caching and session store.
- **Asset Storage:** Cloud Object Storage (Google Cloud Storage / AWS S3) for uploaded specimen photography.
- **Observability:** Centralized logging (Cloud Logging / Datadog) and error tracking (Sentry).

### Stage 5: Production Platform
- **Target Audience:** Global citizen science network and conservation organizations (100,000+ users).
- **Execution Model:** Kubernetes (GKE / EKS) multi-region deployment with horizontal pod autoscaling (HPA).
- **Database:** Multi-AZ High Availability PostgreSQL cluster with read replicas.
- **Message Broker:** Cloud Pub/Sub or Apache Kafka for asynchronous observation moderation and batch evaluation.
- **Security & Compliance:** SOC2 / GDPR compliance, OAuth2 identity providers (ORCID, Google, Institutional SSO), WAF, DDoS protection.

---

## 4. Proposed Docker Architecture (For Stage 3 Implementation)

When Vivédex advances to Stage 3, the following container architecture must be deployed:

### 4.1 Container Specifications
- **Base Image:** `python:3.12-slim-bookworm` (stable, minimal CVE footprint, ~150 MB).
- **User Security:** Create and execute under unprivileged user `vivedex:vivedex` (UID 10001).
- **Working Directory:** `/app`.
- **Port:** Expose port `8501`.
- **Health Check:** `curl --fail http://localhost:8501/_stcore/health || exit 1`.

### 4.2 Docker Implementation Backlog
When ready to implement containerization, execute the following backlog items:
1. **Task DKR-01:** Create `.dockerignore` excluding `.git`, `__pycache__`, `.env`, `data/*.sqlite3`, and `tests/`.
2. **Task DKR-02:** Write multi-stage `Dockerfile` with dependency installation caching.
3. **Task DKR-03:** Write `docker-compose.yml` defining application service and optional local PostgreSQL service.
4. **Task DKR-04:** Add container health check script `scripts/healthcheck.py`.
5. **Task DKR-05:** Configure container environment variable injection for `MODEL_API_KEY` and database credentials.
6. **Task DKR-06:** Test container image build and execution on Linux runner.

---

## 5. Deployment Findings and Recommendations

### Finding DPLY-01: Absence of Formal Health Check Endpoint
- **Finding:** The application lacks a lightweight HTTP health check endpoint for container orchestrators.
- **Evidence:** `app.py` serves the full Streamlit UI on all routes. Streamlit 1.30+ provides `/_stcore/health`, but no custom database connectivity probe exists.
- **Impact:** Cloud load balancers cannot distinguish between a healthy instance and an instance with a locked or corrupted database.
- **Priority:** P2
- **Recommended Action:** Add a lightweight health probe verifying database readability before returning HTTP 200.
- **Dependencies:** `src/database.py`.
- **Estimated Effort:** 2 hours.

### Finding DPLY-02: Local File Storage for Persistent Database in Versioned Tree
- **Finding:** The SQLite database is stored directly inside the repository directory (`data/vivedex.sqlite3`).
- **Evidence:** `src/database.py` defaults to `Path(__file__).parent.parent / "data" / "vivedex.sqlite3"`.
- **Impact:** In containerized environments, container restarts destroy unmounted local databases. Storing database files in the working directory risks accidental Git tracking if `.gitignore` is misconfigured.
- **Priority:** P1
- **Recommended Action:** Support the `VIVEDEX_DB_PATH` environment variable. Default to an external data directory or volume mount path outside the source tree.
- **Dependencies:** `src/database.py`.
- **Estimated Effort:** 1 hour.
