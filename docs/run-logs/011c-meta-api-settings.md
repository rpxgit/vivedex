# RUN 011C — User API Settings and Meta Model Connection

**Assigned model:** Gemini in Antigravity IDE  
**Role:** Full-Stack Engineer and Application Security Engineer  
**Project:** Vivédex  
**Standard:** ASD-STE100  
**Mode:** BYOK Credential Management and Session Isolation  
**Branch:** `feat/byok-meta-settings`

---

## 1. Objective

Implement a Bring Your Own Key (BYOK) architecture for the Meta Model API.
Allow authenticated naturalists to connect, verify, and disconnect their personal Meta Model API keys in server-side session memory.
Preserve operator environment variable fallback (`MODEL_API_KEY`).
Prevent user API keys from being stored in persistent storage (SQLite, `.env`, local files, cookies, or browser storage).

---

## 2. Files Inspected

- `src/meta_adapter.py`: Inspected endpoint structure, authentication headers, and error handling.
- `src/backend.py`: Inspected pipeline orchestration and parameter routing.
- `src/ui/page_identify.py`: Inspected credential checks, status banners, and analysis execution.
- `src/ui/common.py`: Inspected sidebar controls, authentication handling, and logout cleanup.
- `src/auth.py`: Inspected user session structures and password verification.
- `src/database.py`: Inspected schema definitions to ensure zero credential columns.
- `app.py`: Inspected page routing and navigation structure.

---

## 3. Interface Changes

1. **Created Account Settings Page (`src/ui/page_settings.py`):**
   - Added `/settings` route with 4 structured tabs:
     - `🤖 AI Provider Settings`: Connect Meta Model API, view masked key, test connection, replace key, disconnect.
     - `👤 Account Information`: View username, display name, Contributor ID, and role.
     - `🔒 Security`: Password update form and session logout control.
     - `🛡️ Privacy Safeguards`: Data minimization declarations and memory-only storage disclosures.
2. **Added Step-by-Step Meta Connection Flow:**
   - Step 1: Instructional expander linking to `https://dev.meta.ai/` and `https://dev.meta.ai/docs/quickstart`.
   - Step 2: Password-style key input with show/hide control, automatic whitespace trimming, and empty submission rejection.
   - Step 3: "Test Connection" button executing a text-only ping to `https://api.meta.ai/v1/chat/completions`.
   - Step 4: Status badges for `NOT CONNECTED`, `CONNECTED`, `INVALID KEY`, `RATE LIMITED`, and `CONNECTION FAILED`.
3. **Updated Identify Page (`src/ui/page_identify.py`):**
   - Added dynamic connection status banner:
     - `🟢 My Meta API Key Connected`: Personal key in active session memory.
     - `🔵 Application-Provided Key Available`: Operator environment key fallback.
     - `⚠️ Connect Meta Model API`: Guidance notice with link to `/settings` and Demo Fixture Mode fallback.
4. **Updated Navigation (`app.py` & `src/ui/common.py`):**
   - Added `Account Settings` (`⚙️`) to navigation under `Science & Identity`.
   - Enhanced logout button in `src/ui/common.py` to immediately purge user API credentials from session state.

---

## 4. Backend Changes

1. **`src/meta_adapter.py`:**
   - Added `test_connection(api_key: str, timeout_seconds: float = 15.0) -> tuple[str, str, dict[str, Any]]`:
     - Sends text-only verification prompt (`Reply with exactly: VIVEDEX_API_CONNECTION_OK`) using model `muse-spark-1.3`.
     - Validates HTTP response without sending images.
     - Sanitizes errors and returns explicit status names (`CONNECTED`, `INVALID_KEY`, `RATE_LIMITED`, `CONNECTION_FAILED`).
   - Updated `identify_image(..., api_key: str | None = None)`:
     - Accepts explicit per-request `api_key` parameter.
     - Does not mutate instance attributes or set global environment variables.
   - Updated `_require_api_key(explicit_key: str | None = None)`:
     - Resolves priority: explicit key > instance key > `MODEL_API_KEY` > `META_API_KEY`.
2. **`src/backend.py`:**
   - Updated `process_observation(image_bytes, mime_type, api_key: str | None = None)`:
     - Passes user-provided `api_key` directly to `meta_adapter.identify_image`.
3. **`src/auth.py`:**
   - Added `update_password(user_id: int, new_password: str)` to support password changes in Account Settings.

---

## 5. Credential Handling

| Requirement | Implementation Detail | Status |
|---|---|---|
| In-Memory Session Storage | Key is stored exclusively in `st.session_state["user_meta_api_key"]`. | **COMPLIANT** |
| Zero SQLite Storage | No database tables contain columns for API keys. | **COMPLIANT** |
| Zero File / Disk Storage | Keys are never written to `.env`, logs, or temporary files. | **COMPLIANT** |
| Zero Cookie / Storage Leakage | Keys are not stored in cookies, query parameters, or local storage. | **COMPLIANT** |
| No Key in Exports | Observation JSON exports contain zero credential attributes. | **COMPLIANT** |
| Precedence Enforcement | User session key overrides operator environment key. | **COMPLIANT** |
| Disconnect & Logout Purge | Disconnecting or logging out explicitly deletes session keys. | **COMPLIANT** |
| Key Masking | Active keys are displayed masked as `••••••••••••••••••••...${key[-4:]}`. | **COMPLIANT** |
| Error Sanitization | Authorization headers and tokens are stripped from all exceptions. | **COMPLIANT** |

---

## 6. Security Decisions

1. **Explicit Parameter Routing over Singleton Mutation:**
   - *Decision:* Pass `api_key` as a function argument through `backend.process_observation` and `meta_adapter.identify_image`.
   - *Rationale:* Mutating `os.environ["MODEL_API_KEY"]` or `self.meta_adapter.api_key` would cause race conditions and credential leakage between concurrent users on the local server.
2. **Text-Only Connection Testing:**
   - *Decision:* The `test_connection` method uses a 16-token prompt and zero image bytes.
   - *Rationale:* Minimizes network overhead, prevents accidental consumption of model image quotas, and verifies authentication rapidly.
3. **Transparent Disclosure Notice:**
   - *Decision:* Rendered an explicit banner stating keys are not saved permanently:
     `Your API key stays in server memory for this session. Vivédex does not save it to your account or database.`
   - *Rationale:* Prevents false expectations of persistent storage and encourages good security hygiene.

---

## 7. Files Created

- `src/ui/page_settings.py`: Complete user Account Settings and BYOK Meta API connection interface.
- `tests/test_api_credentials.py`: Comprehensive test suite containing 16 unit and security tests.
- `docs/run-logs/011c-meta-api-settings.md`: Mandatory ASD-STE100 technical run log.

---

## 8. Files Modified

- `src/meta_adapter.py`: Added `test_connection` and explicit `api_key` parameter routing.
- `src/backend.py`: Updated `process_observation` to forward `api_key`.
- `src/auth.py`: Added `update_password` method with PBKDF2 hashing.
- `src/ui/page_identify.py`: Integrated BYOK credential check, status pills, and dynamic action buttons.
- `src/ui/common.py`: Added credential purging on user logout.
- `app.py`: Registered `Account Settings` page in routing and navigation sections.
- `README.md`: Documented BYOK architecture and configuration options.
- `docs/PLATFORM_SPEC.md`: Added Section 8 detailing BYOK specifications.
- `docs/EXPERIENCE_DESIGN_SPEC.md`: Added Section 8 detailing Account Settings interface.
- `docs/security/SECURITY_CONFIGURATION.md`: Added Section 10 on BYOK credential security.

---

## 9. Files Deleted

None.

---

## 10. Tests Executed

Executed automated test suite using `pytest`:

```powershell
py -m pytest tests/test_api_credentials.py -v
py -m pytest
```

---

## 11. Test Results

### BYOK Security Test Suite (`tests/test_api_credentials.py`):
1. `test_key_input_validation`: **PASS** (Rejects empty and whitespace-only keys).
2. `test_successful_connection_test`: **PASS** (Verifies 200 OK and text-only payload).
3. `test_invalid_key_handling`: **PASS** (Verifies 401 handling and sanitization).
4. `test_key_masking`: **PASS** (Verifies partial masking).
5. `test_disconnect_behaviour`: **PASS** (Verifies session state purging).
6. `test_replacement_behaviour`: **PASS** (Verifies key replacement).
7. `test_session_isolation`: **PASS** (Verifies adapter immutability).
8. `test_per_request_credential_selection`: **PASS** (Verifies explicit parameter passing).
9. `test_environment_key_fallback`: **PASS** (Verifies operator key fallback).
10. `test_user_key_precedence`: **PASS** (Verifies user key takes priority).
11. `test_logout_clearing`: **PASS** (Verifies logout credential purging).
12. `test_no_key_in_database_records`: **PASS** (Asserts zero keys in SQLite tables).
13. `test_no_key_in_observation_exports`: **PASS** (Asserts zero keys in JSON exports).
14. `test_no_key_in_logs`: **PASS** (Asserts zero keys in log records).
15. `test_no_key_in_exception_messages`: **PASS** (Asserts sanitized exception strings).
16. `test_no_cross_user_credential_leakage`: **PASS** (Verifies concurrent session isolation).

### Full Test Suite Summary:
- Total test files: 7
- Total tests: 88
- Result: **88 passed in 26.97s (100% PASS)**

---

## 12. Live API Test Status

A live connection test was executed using the configured operator environment key:
- Endpoint: `https://api.meta.ai/v1/chat/completions`
- Model: `muse-spark-1.3`
- Result Code: **HTTP 200 OK**
- Status: **`CONNECTED`**
- Verified Output: `Meta Muse Spark is connected. Live identification is available.`

---

## 13. Known Limitations

- **Session Volatility:** Because keys are intentionally held only in server session memory, restarting the Streamlit application or clearing the browser session requires re-entering the key.
- **Upstream Rate Limits:** Personal keys are subject to individual Meta developer account tier limits.
- **No Client Encryption Key:** For the local prototype, keys in session memory are unencrypted strings in server RAM. Production multi-tenant architectures will require an encrypted vault.

---

## 14. Git Branch and Commit

- Working Branch: `feat/byok-meta-settings`
- Base Commit: `ea2e60e` ("fix(ui): correct hero banner contrast, reconstruct uploader, and align 6-step workflow")
- Status: Clean working directory ready for commit; unmerged to `main`.

---

## 15. Scope Assessment

All requirements for RUN 011C have been fulfilled:
- Dedicated Account Settings page implemented with 4 structured tabs.
- Full BYOK workflow implemented with external links, masked inputs, and connection testing.
- Live model `muse-spark-1.3` verified over HTTP.
- Strict credential isolation maintained: zero database, file, or export persistence.
- Precedence hierarchy implemented and verified: User Key > Operator Key > Demo Fixture.
- Comprehensive 16-scenario test suite passes with 100% success.
- Documentation and run log complete.

---

## 16. Next Recommended Action

1. Commit changes to `feat/byok-meta-settings`.
2. Review multi-user authentication hardening for future multi-tenant deployment.
3. Prepare user guide walkthrough for the BYOK connection flow.
