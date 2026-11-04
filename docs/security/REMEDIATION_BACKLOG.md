# Vivédex Security Remediation Backlog

## 1. Executive Summary
This backlog records the prioritized engineering remediation plan and implementation status for all vulnerabilities identified in the Vivédex Cybersecurity Assessment (RUN 009).
All tasks were remediated, verified, and hardened during RUN 010.
All descriptions adhere to the ASD-STE100 technical standard.

---

## 2. Prioritized Remediation Task Matrix

| Task ID | Finding Ref | Priority | Title | Affected File(s) | Status | Verification |
|---|---|---|---|---|---|---|
| **REM-01** | SEC-01 | **P1 (High)** | Neutralize Stored & Reflected XSS via Strict HTML Escaping | `src/ui/page_*.py`, `src/ui/theme.py` | **COMPLETED** | `tests/test_security.py::test_html_escaping_utility` |
| **REM-02** | SEC-02 | **P1 (High)** | Replace First-User Admin Bootstrap with Secure Provisioning | `src/auth.py`, `src/cli.py`, `src/demo_data.py` | **COMPLETED** | `tests/test_security.py::test_public_registration_never_assigns_admin`, `test_cli_admin_provisioning_command` |
| **REM-03** | SEC-06 | **P2 (Med)** | Enforce Maximum Image Dimensions to Prevent Decompression Bombs | `src/image_processor.py` | **COMPLETED** | `tests/test_security.py::test_image_processor_rejects_oversized_dimensions` |
| **REM-04** | SEC-03 | **P2 (Med)** | Implement Account Lockout and Brute-Force Throttling | `src/auth.py` | **COMPLETED** | `tests/test_security.py::test_login_rate_limiting_lockout` |
| **REM-05** | SEC-04 | **P2 (Med)** | Eliminate Login Timing Side-Channel with Constant-Time Check | `src/auth.py` | **COMPLETED** | `tests/test_security.py::test_dummy_password_verification_for_missing_user` |
| **REM-06** | SEC-05 | **P2 (Med)** | Restrict Gamification XP Awards to Verified Observations | `src/collection_service.py`, `src/achievements.py` | **COMPLETED** | `tests/test_security.py::test_xp_separation_no_xp_for_manual_collection_save` |
| **REM-07** | SEC-08 | **P3 (Low)** | Validate External Researcher URL Scheme (`https://orcid.org/`) | `src/auth.py`, `src/collection_service.py` | **COMPLETED** | `tests/test_security.py::test_orcid_validation_valid_formats` |
| **REM-08** | SEC-07 | **P3 (Low)** | Add In-Memory Session Idle Timeout Invalidation | `src/ui/common.py` | **COMPLETED** | `tests/test_security.py::test_session_timeout_expiration` |
| **REM-09** | SEC-09 | **P3 (Low)** | Formulate Endangered Species Locality Fuzzing Policy | `docs/security/` | **COMPLETED** | Documented in `docs/security/SECURITY_CONFIGURATION.md` |

---

## 3. Detailed Remediation Action Plans & Completion Records

### REM-01: Neutralize Stored & Reflected XSS via Strict HTML Escaping
- **Status:** **COMPLETED** (RUN 010)
- **Implementation:** Added `escape_text()` and `safe_url()` in `src/ui/theme.py`. Applied escaping across all dynamic fields in `src/ui/page_profile.py`, `src/ui/page_journal.py`, `src/ui/page_home.py`, `src/ui/page_explore.py`, `src/ui/page_identify.py`, `src/ui/page_collection.py`, `src/ui/page_species_detail.py`, `src/ui/page_achievements.py`, `src/ui/page_admin.py`, and `src/ui/page_knowledge.py`.
- **Verification:** Verified in `tests/test_security.py::test_html_escaping_utility` and `tests/test_security.py::test_safe_url_filtering`.

---

### REM-02: Replace First-User Admin Bootstrap with Secure Provisioning
- **Status:** **COMPLETED** (RUN 010)
- **Implementation:** In `src/auth.py`, removed automatic `admin` role assignment upon registration. Standard registration always assigns `role='user'`. Created `src/cli.py` (`python -m src.cli create-admin`) with subcommands `create-admin` and `check-admin`. Added `is_demo_mode()` check guarding demo data loading.
- **Verification:** Verified in `tests/test_security.py::test_public_registration_never_assigns_admin`, `test_provision_admin_user_service`, and `test_cli_admin_provisioning_command`.

---

### REM-03: Enforce Maximum Image Dimensions to Prevent Decompression Bombs
- **Status:** **COMPLETED** (RUN 010)
- **Implementation:** Added constants in `src/image_processor.py`: `MAX_IMAGE_WIDTH = 4096`, `MAX_IMAGE_HEIGHT = 4096`, `MAX_IMAGE_PIXELS = 16_777_216`. Set `Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS`. Added explicit dimension checks in `validate_image()`.
- **Verification:** Verified in `tests/test_security.py::test_image_processor_rejects_oversized_dimensions` and `test_image_processor_validates_standard_dimensions`.

---

### REM-04: Implement Account Lockout and Brute-Force Throttling
- **Status:** **COMPLETED** (RUN 010)
- **Implementation:** Integrated thread-safe progressive rate limiter in `AuthService`. Allows 5 attempts before enforcing a 60-second cooldown, scaling up to 900 seconds. Clears upon successful authentication.
- **Verification:** Verified in `tests/test_security.py::test_login_rate_limiting_lockout`.

---

### REM-05: Eliminate Login Timing Side-Channel with Constant-Time Check
- **Status:** **COMPLETED** (RUN 010)
- **Implementation:** Added module-level `DUMMY_SALT` and `DUMMY_HASH`. Non-existent usernames trigger full PBKDF2 hash comparison using `hmac.compare_digest`.
- **Verification:** Verified in `tests/test_security.py::test_dummy_password_verification_for_missing_user`.

---

### REM-06: Restrict Gamification XP Awards to Verified Observations
- **Status:** **COMPLETED** (RUN 010)
- **Implementation:** Updated `calculate_xp_breakdown()` in `src/achievements.py`: First encounter XP (+50 XP) is calculated exclusively from unique taxa with recorded observations (`observations.matched_taxon_id IS NOT NULL`). Manual collection entries award 0 XP.
- **Verification:** Verified in `tests/test_security.py::test_xp_separation_no_xp_for_manual_collection_save`.

---

### REM-07: Validate External Researcher URL Scheme (`https://orcid.org/`)
- **Status:** **COMPLETED** (RUN 010)
- **Implementation:** Created `validate_orcid_url()` in `src/auth.py`. Validates HTTPS, domain whitelist (`orcid.org`, `www.orcid.org`), no credentials, query parameters, or fragments, and 16-digit regex format `/\d{4}-\d{4}-\d{4}-\d{3}[\dX]`. Enforced in `CollectionService.update_user_bio`.
- **Verification:** Verified in `tests/test_security.py::test_orcid_validation_valid_formats` and `test_orcid_validation_invalid_formats`.

---

### REM-08: Add In-Memory Session Idle Timeout Invalidation
- **Status:** **COMPLETED** (RUN 010)
- **Implementation:** Added `check_session_timeout()` in `src/ui/common.py` with a 30-minute idle threshold. Automatically clears `current_user` and `active_user_id` upon expiration.
- **Verification:** Verified in `tests/test_security.py::test_session_timeout_expiration` and `test_session_timeout_active_session_retained`.

---

### REM-09: Formulate Endangered Species Locality Fuzzing Policy
- **Status:** **COMPLETED** (RUN 010)
- **Implementation:** Established policy requiring coordinate generalization to a minimum 10 km grid for IUCN Red List threatened/endangered taxa prior to public mapping. Documented in `docs/security/SECURITY_CONFIGURATION.md` and `docs/security/PRODUCTION_SECURITY_REQUIREMENTS.md`.
