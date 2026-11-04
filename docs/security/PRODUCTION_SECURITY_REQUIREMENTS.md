# Vivédex Production Security Requirements

## 1. Executive Summary
This document specifies the mandatory security architecture, technical requirements, and operational controls required to transition Vivédex from a local prototype to a hosted production platform.
It establishes compliance standards for academic partners, citizen-science networks, and institutional sponsors.
All specifications adhere to the ASD-STE100 technical standard.

---

## 2. Authentication & Identity Hardening

1. **Modern Password Hashing:**
   - Migrate from PBKDF2 to **Argon2id** (memory: 64 MB, time: 3 iterations, parallelism: 4 threads).
   - Reject passwords shorter than 12 characters or present in the HaveIBeenPwned common breached passwords corpus.
2. **Multi-Factor Authentication (MFA):**
   - Require Time-based One-Time Passwords (TOTP via RFC 6238) for all administrator accounts (`admin` role).
   - Provide optional TOTP authentication for standard naturalists.
3. **Session Management:**
   - Terminate in-memory session persistence.
   - Issue cryptographically signed HTTP-only, SameSite=Strict, Secure session cookies (JWT or server-side Redis session keys).
   - Enforce an absolute session timeout of 12 hours and an idle timeout of 60 minutes.
4. **Federated Identity & Scientific Verification:**
   - Implement OAuth 2.0 / OpenID Connect (OIDC) integration with the formal **ORCID API**.
   - Mark researcher profiles as *Verified Researcher* only after successful cryptographic ORCID token validation.

---

## 3. Web Application Security & Transport Controls

1. **Content Security Policy (CSP):**
   - Enforce strict HTTP response headers:
     ```http
     Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https://images.unsplash.com https://api.gbif.org; connect-src 'self' https://api.meta.ai https://api.gbif.org; frame-ancestors 'none';
     X-Content-Type-Options: nosniff
     X-Frame-Options: DENY
     Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
     Referrer-Policy: strict-origin-when-cross-origin
     ```
2. **Cross-Site Request Forgery (CSRF) Defense:**
   - Implement synchronized double-submit anti-CSRF tokens for all state-modifying actions (profile edits, observation recordings, moderation approvals).
3. **Input Sanitization & Output Encoding:**
   - Standardize on context-aware output encoding across all user interfaces.
   - Forbid raw HTML interpolation (`unsafe_allow_html=True`) in user-facing components unless strictly sanitized via an approved HTML sanitizer (e.g., `bleach`).

---

## 4. Database Security & Data Layer Transition

1. **Migration to Managed PostgreSQL:**
   - Replace local SQLite with Cloud Managed PostgreSQL (Google Cloud SQL or AWS RDS Aurora).
   - Use dedicated application database users with principle of least privilege (no `SUPERUSER` or `CREATE TABLE` permissions during normal runtime).
2. **Encryption at Rest and in Transit:**
   - Enforce SSL/TLS connections (`sslmode=verify-full`) between application services and the database.
   - Encrypt database tablespaces and automated snapshots with customer-managed encryption keys (CMEK) via Cloud KMS.
3. **Row-Level Security (RLS):**
   - Enable PostgreSQL Row-Level Security on `observations` and `collections` tables.
   - Ensure users can only read, update, or delete records matching their authenticated `tenant_id` / `user_id`.

---

## 5. Cloud Infrastructure & Secrets Governance

1. **Centralized Secrets Management:**
   - Forbid `.env` files in production container filesystems.
   - Inject `MODEL_API_KEY`, database passwords, and session secrets at runtime from Google Secret Manager or AWS Secrets Manager.
   - Enforce automated secret rotation every 90 days.
2. **Network Egress Filtering:**
   - Place application workloads inside a private VPC with no public IP addresses.
   - Restrict outbound internet egress exclusively to approved API endpoints:
     - Meta Model API: `api.meta.ai` (port 443)
     - GBIF API: `api.gbif.org` (port 443)
     - ORCID API: `pub.orcid.org` (port 443)
3. **Container Hardening:**
   - Execute containerized workloads as an unprivileged, non-root user (UID 10001).
   - Mount root filesystem as read-only (`read_only_root_filesystem: true`).
   - Use minimal distroless or Alpine/Debian-slim base images. Run automated vulnerability scans (Trivy / Snyk) in CI before deployment.

---

## 6. Biodiversity Data Governance & Endangered Species Protection

1. **Sensitive Species Locality Generalization:**
   - Integrate an authoritative sensitive species list (IUCN Red List vulnerable/endangered categories and national wildlife protection acts).
   - When an observation matches a sensitive taxon, automatically apply coordinate fuzzing:
     - Obscure coordinates to a minimum bounding grid of $10\text{ km} \times 10\text{ km}$ ($0.1^\circ$ resolution).
     - Restrict exact geographic points exclusively to verified taxonomic researchers and vetted conservation officials.
2. **Attribution and Provenance Preservation:**
   - Retain mandatory CC BY 4.0 attribution citations for all taxonomic data derived from the GBIF Backbone Taxonomy.
   - Maintain immutable provenance logs recording the exact model identifier, prompt version, and GBIF usage key for every scientific observation.
3. **GDPR / Privacy Compliance:**
   - Support user account deletion ("Right to be Forgotten") with cascading deletion of personal profiles while maintaining anonymized research observations.
   - Provide complete data export of all personal observations and collection items in standardized Darwin Core Archive (DwC-A) format.

---

## 7. Security Monitoring and Incident Response

1. **Centralized Audit Log Streaming:**
   - Stream all security audit events (`USER_LOGIN`, `USER_REGISTERED`, `OBSERVATION_MODERATED`, `PROFILE_UPDATED`) to Cloud Logging / CloudWatch.
   - Ensure audit logs are immutable and tamper-evident (WORM storage).
2. **Automated Security Alerting:**
   - Trigger immediate pager alerts for:
     - More than 10 failed login attempts within 5 minutes.
     - Any HTTP 403 authorization failure on administrative endpoints.
     - Sudden surges in Meta Model API errors (HTTP 429 or 5xx).
3. **Vulnerability Disclosure Policy:**
   - Publish a formal `SECURITY.md` in the repository.
   - Establish a dedicated vulnerability reporting inbox (`security@vivedex.org`) with a 48-hour response SLA.
