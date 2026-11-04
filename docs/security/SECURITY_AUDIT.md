# Vivédex Cybersecurity Assessment and Vulnerability Audit

## 1. Executive Summary
This document records an independent cybersecurity audit and security remediation status of Vivédex.
The audit evaluated authentication mechanisms, authorization boundaries, database operations, image handling pipelines, model integrations, web presentation layers, and supply chain dependencies.
All findings adhere to the ASD-STE100 technical standard.

### Severity Summary:
- **CRITICAL:** 0
- **HIGH:** 2 (2 FIXED — TESTED)
- **MEDIUM:** 4 (4 FIXED — TESTED)
- **LOW:** 2 (2 FIXED — TESTED)
- **INFORMATIONAL:** 1 (1 DOCUMENTED — POLICY ESTABLISHED)

### Remediation Verification Status (RUN 010):

| Finding ID | Severity | Title | Status | Regression Test |
|---|---|---|---|---|
| **SEC-01** | HIGH | Stored/Reflected XSS in Custom HTML | **FIXED — TESTED** | `tests/test_security.py::test_html_escaping_utility`, `test_safe_url_filtering` |
| **SEC-02** | HIGH | First-User Admin Bootstrap Race Condition | **FIXED — TESTED** | `tests/test_security.py::test_public_registration_never_assigns_admin`, `test_provision_admin_user_service`, `test_cli_admin_provisioning_command` |
| **SEC-03** | MEDIUM | Login Endpoint Missing Rate Limiting | **FIXED — TESTED** | `tests/test_security.py::test_login_rate_limiting_lockout` |
| **SEC-04** | MEDIUM | Username Timing Side-Channel | **FIXED — TESTED** | `tests/test_security.py::test_dummy_password_verification_for_missing_user` |
| **SEC-05** | MEDIUM | Gamification XP Inflation via Taxon Scraping | **FIXED — TESTED** | `tests/test_security.py::test_xp_separation_no_xp_for_manual_collection_save` |
| **SEC-06** | MEDIUM | Decompression Bomb and Memory Exhaustion | **FIXED — TESTED** | `tests/test_security.py::test_image_processor_rejects_oversized_dimensions`, `test_image_processor_validates_standard_dimensions` |
| **SEC-07** | LOW | Missing Idle Session Expiration | **FIXED — TESTED** | `tests/test_security.py::test_session_timeout_expiration`, `test_session_timeout_active_session_retained` |
| **SEC-08** | LOW | Unvalidated Protocol/Scheme in External ORCID Links | **FIXED — TESTED** | `tests/test_security.py::test_orcid_validation_valid_formats`, `test_orcid_validation_invalid_formats` |
| **SEC-09** | INFORMATIONAL | Sensitive Species Locality Fuzzing Policy | **DOCUMENTED** | Policy in `docs/security/SECURITY_CONFIGURATION.md` |

---

## 2. Confirmed Vulnerability Findings & Remediation Verification

### Finding SEC-01: Stored and Reflected Cross-Site Scripting (XSS) via Unsanitized HTML Interpolation
- **Finding ID:** SEC-01
- **Severity:** **HIGH**
- **Status:** **FIXED — TESTED**
- **Affected Component:** Presentation Layer (`src/ui/`)
- **Remediation Implemented:**
  1. Centralized `escape_text(val)` and `safe_url(url)` in `src/ui/theme.py`.
  2. Applied `escape_text()` to all dynamic user-controlled, model-generated, and external API variables across all page controllers (`src/ui/page_*.py`).
  3. Sanitized external URLs with `safe_url()` to reject `javascript:`, `data:`, and `vbscript:` schemes.
  4. Added `rel="noopener noreferrer"` to external anchors.
- **Verification Evidence:**
  `tests/test_security.py::test_html_escaping_utility` and `tests/test_security.py::test_safe_url_filtering` pass with 100% assertion coverage.

---

### Finding SEC-02: Unprotected First-User Administrator Bootstrap Race Condition
- **Finding ID:** SEC-02
- **Severity:** **HIGH**
- **Status:** **FIXED — TESTED**
- **Affected Component:** Authentication Service (`src/auth.py`, `src/cli.py`, `src/demo_data.py`)
- **Remediation Implemented:**
  1. Removed automatic administrator role promotion from `register_user()`. All public registrations create accounts with `role='user'` unconditionally.
  2. Implemented operator-gated CLI tool `src/cli.py` (`python -m src.cli create-admin`) executing within an atomic transaction and logging an audit event.
  3. Added `provision_admin_user()` service method requiring explicit confirmation for multi-admin provisioning.
  4. Guarded demonstration dataset generation and quick-switch controls behind `is_demo_mode()` (`VIVEDEX_DEMO_MODE=1`).
- **Verification Evidence:**
  Verified in `tests/test_security.py::test_public_registration_never_assigns_admin`, `test_provision_admin_user_service`, and `test_cli_admin_provisioning_command`.

---

### Finding SEC-03: Absence of Account Lockout and Rate Limiting on Login Endpoint
- **Finding ID:** SEC-03
- **Severity:** **MEDIUM**
- **Status:** **FIXED — TESTED**
- **Affected Component:** Authentication Service (`src/auth.py`)
- **Remediation Implemented:**
  1. Integrated in-memory thread-safe `_failed_logins` tracker in `AuthService`.
  2. Enforced 5 failed attempts limit within a rolling 15-minute window.
  3. Implemented progressive cooldown starting at 60 seconds and scaling up to 900 seconds.
  4. Resets failed attempts immediately upon valid password verification.
- **Verification Evidence:**
  Verified in `tests/test_security.py::test_login_rate_limiting_lockout`.

---

### Finding SEC-04: Username Enumeration via Timing Side-Channel
- **Finding ID:** SEC-04
- **Severity:** **MEDIUM**
- **Status:** **FIXED — TESTED**
- **Affected Component:** Authentication Service (`src/auth.py`)
- **Remediation Implemented:**
  1. Initialized constant `DUMMY_SALT` and pre-computed `DUMMY_HASH` at module load.
  2. When a requested username does not exist in the database, `authenticate_user()` performs a full PBKDF2 hash comparison using `hmac.compare_digest`.
  3. Execution times between existing and non-existent usernames are indistinguishable.
- **Verification Evidence:**
  Verified in `tests/test_security.py::test_dummy_password_verification_for_missing_user`.

---

### Finding SEC-05: Gamification XP Inflation via Automated Taxon Scraping
- **Finding ID:** SEC-05
- **Severity:** **MEDIUM**
- **Status:** **FIXED — TESTED**
- **Affected Component:** Domain Layer (`src/achievements.py`, `src/collection_service.py`)
- **Remediation Implemented:**
  1. Restructured `calculate_xp_breakdown()` in `src/achievements.py`: First encounter XP (+50 XP) is calculated exclusively from unique taxa recorded in authentic `observations`.
  2. Manually adding taxa to `collections` without recorded observations awards 0 XP.
- **Verification Evidence:**
  Verified in `tests/test_security.py::test_xp_separation_no_xp_for_manual_collection_save`.

---

### Finding SEC-06: Decompression Bomb and Memory Exhaustion Risk
- **Finding ID:** SEC-06
- **Severity:** **MEDIUM**
- **Status:** **FIXED — TESTED**
- **Affected Component:** Image Processing (`src/image_processor.py`)
- **Remediation Implemented:**
  1. Defined dimension limits: `MAX_IMAGE_WIDTH = 4096`, `MAX_IMAGE_HEIGHT = 4096`, `MAX_IMAGE_PIXELS = 16_777_216`.
  2. Set global Pillow threshold `Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS`.
  3. Validates dimensions in `validate_image()` before decompression; catches `DecompressionBombError` and raises `ImageValidationError`.
- **Verification Evidence:**
  Verified in `tests/test_security.py::test_image_processor_rejects_oversized_dimensions` and `test_image_processor_validates_standard_dimensions`.

---

## 3. Low and Informational Findings

### Finding SEC-07: Insecure In-Memory Session Storage and Lack of Session Expiration
- **Finding ID:** SEC-07
- **Severity:** **LOW**
- **Status:** **FIXED — TESTED**
- **Affected Component:** Session Management (`src/ui/common.py`)
- **Remediation Implemented:**
  1. Implemented `check_session_timeout()` with 30-minute idle threshold.
  2. Clears session authentication state and sets `session_expired_message` on timeout.
- **Verification Evidence:**
  Verified in `tests/test_security.py::test_session_timeout_expiration` and `test_session_timeout_active_session_retained`.

---

### Finding SEC-08: Lack of Protocol and Format Validation on External ORCID URLs
- **Finding ID:** SEC-08
- **Severity:** **LOW**
- **Status:** **FIXED — TESTED**
- **Affected Component:** User Profile Service (`src/auth.py`, `src/collection_service.py`)
- **Remediation Implemented:**
  1. Implemented `validate_orcid_url()` enforcing HTTPS, domain whitelist (`orcid.org`, `www.orcid.org`), no credentials/query/fragments, and strict 16-digit regex format.
  2. Normalized stored URLs to canonical `https://orcid.org/XXXX-XXXX-XXXX-XXXX`.
- **Verification Evidence:**
  Verified in `tests/test_security.py::test_orcid_validation_valid_formats` and `test_orcid_validation_invalid_formats`.

---

### Finding SEC-09: Sensitive Species Locality Protection (Future Architectural Risk)
- **Finding ID:** SEC-09
- **Severity:** **INFORMATIONAL**
- **Status:** **DOCUMENTED — POLICY ESTABLISHED**
- **Affected Component:** Data Governance (`docs/security/SECURITY_CONFIGURATION.md`, `docs/security/PRODUCTION_SECURITY_REQUIREMENTS.md`)
- **Remediation Implemented:**
  1. Documented sensitive species coordinate fuzzing policy requiring a minimum 10 km grid for IUCN Red List threatened/endangered taxa prior to public mapping.
  2. Current prototype restricts location to coarse textual descriptions (`coarse_location`).

---

## 4. Verified Security Strengths in Existing Architecture
1. **Zero SQL Injection Vulnerabilities:** All database queries across all modules use strict SQLite parameter binding (`?`). No string concatenation or unsafe f-strings exist in query construction.
2. **Referential Integrity & Cascading:** Foreign keys are explicitly enabled on every connection (`PRAGMA foreign_keys = ON;`), preventing orphan records.
3. **Robust Password Hashing:** PBKDF2-HMAC-SHA256 with 100,000 iterations, 16-byte random per-user salts, and constant-time verification (`hmac.compare_digest`).
4. **Clean EXIF Stripping:** Images are processed entirely in memory via Pillow. Orientation is corrected and metadata (including GPS tags) is completely stripped before external transmission.
5. **No Image Disk Spillage:** Raw images are never saved to local disk or temporary filesystem directories.
6. **Isolated JSON Export:** Downloadable JSON records contain only scientific taxonomic data and omit passwords, hashes, salts, and API tokens.
7. **Server-Side Authorization Enforcement:** `AdminService` enforces `_require_admin()` server-side on all moderation and administrative actions.
8. **Append-Only Security Audit Log:** All user registrations, logins, profile modifications, observations, and moderation decisions are logged with UTC timestamps.
