# Vivédex Security Configuration and Operational Manual

## 1. Overview
This manual provides operational security guidance for Vivédex administrators and platform operators.
It details runtime configuration controls, credential management, administrative provisioning, and security limits.
All specifications follow the ASD-STE100 technical standard.

---

## 2. Environment Configuration Matrix

| Variable | Default Value | Production Value | Description |
|---|---|---|---|
| `VIVEDEX_DEMO_MODE` | `0` (Disabled) | `0` | Controls demonstration data generation and quick demo account switching. When set to `0`, demo dataset creation is strictly blocked. |
| `MODEL_API_KEY` | None | Set via Secret Manager | Multimodal vision API key for Meta Muse Spark model calls. Must never be committed to git. |
| `META_API_KEY` | None | Set via Secret Manager | Fallback environment variable for the vision model API key. |
| `VIVEDEX_DB_PATH` | `data/vivedex.sqlite3` | `/var/lib/vivedex/db.sqlite3` | Filesystem path for the primary database file. |

---

## 3. Administrator Provisioning Workflow

### 3.1 Policy
Public user registration via the web interface always assigns the standard `user` role.
Automatic administrator promotion on first registration is permanently removed (SEC-02).
Administrative accounts can only be provisioned by a server operator using the CLI interface.

### 3.2 Operator CLI Commands

#### Create Administrator Account
```powershell
# Standard invocation
python -m src.cli create-admin --username admin_lead --password StrongPassword123!

# Explicit custom database path and display name
python -m src.cli create-admin --username lead_naturalist --password StrongPassword123! --display-name "Lead Naturalist" --db-path data/vivedex.sqlite3

# Force additional administrator provisioning when one already exists
python -m src.cli create-admin --username backup_admin --password StrongPassword123! --force
```

#### Inspect Administrator Accounts
```powershell
python -m src.cli check-admin --db-path data/vivedex.sqlite3
```

---

## 4. Authentication and Rate Limiting Controls

### 4.1 Progressive Rate Limiting (SEC-03)
- **Threshold:** 5 consecutive failed login attempts on a single username.
- **Initial Cooldown:** 60 seconds lockout.
- **Progressive Cooldown:** Each subsequent failure adds 60 seconds up to a maximum cap of 900 seconds (15 minutes).
- **Reset:** Successful authentication immediately clears failed attempt records for that account.
- **Thread Safety:** Enforced via `threading.Lock` across application worker threads.

### 4.2 Timing Side-Channel Mitigation (SEC-04)
- When a requested username does not exist in the database, the authentication service executes a constant-time dummy PBKDF2 calculation against a pre-computed constant salt and hash.
- This equalizes execution duration between valid and invalid usernames, preventing timing enumeration attacks.

---

## 5. Session Lifecycle Management (SEC-07)

- **Idle Timeout:** 30 minutes (1,800 seconds).
- **Mechanism:** `check_session_timeout()` compares current time against `st.session_state["last_activity_timestamp"]`.
- **Expiration Behavior:** When idle threshold is exceeded, `current_user` and `active_user_id` are cleared from session state, forcing re-authentication.

---

## 6. Input Sanitization and XSS Prevention (SEC-01, SEC-08)

### 6.1 Text Sanitization
All user-supplied, model-generated, and external API strings rendered inside custom HTML must be escaped using:
```python
from src.ui.theme import escape_text

escaped_text = escape_text(user_input)
```

### 6.2 URL Protocol Filtering
Hyperlink references inside HTML cards must be verified using:
```python
from src.ui.theme import safe_url

clean_href = safe_url(user_provided_url)
```
Only `http` and `https` protocols are accepted. `javascript:`, `data:`, and `vbscript:` schemes return an empty string.

### 6.3 External ORCID Validation
ORCID links submitted in user profiles are validated using `src.auth.validate_orcid_url()`:
- Protocol must be `https://`.
- Host must be `orcid.org` or `www.orcid.org`.
- Path must strictly match the 16-digit format `/\d{4}-\d{4}-\d{4}-\d{3}[\dX]`.
- Query parameters and URL fragments are rejected.

---

## 7. Image Processing and Resource Limits (SEC-06)

Specimen photographs uploaded to the application must comply with the following constraints:
- **Maximum File Size:** 8 MB (8,388,608 bytes).
- **Maximum Width:** 4,096 pixels.
- **Maximum Height:** 4,096 pixels.
- **Maximum Total Pixels:** 16,777,216 pixels (`Image.MAX_IMAGE_PIXELS`).
- **Memory Safety:** Images are verified and preprocessed exclusively in memory. No temporary files are written to disk.
- **Metadata Stripping:** All EXIF metadata, GPS tags, and camera serials are stripped during preprocessing.

---

## 8. Gamification and XP Integrity (SEC-05)

- **First Encounter Bonus (+50 XP):** Awarded only once per unique taxon that is corroborated by an authentic recorded observation record in `observations`.
- **Manual Bookmarks:** Manually adding a taxon to `collections` via the catalog awards 0 XP.
- **Field Notes Bonus (+20 XP):** Awarded for observations with field notes containing at least 5 non-whitespace characters.
- **Catalog Moderation Acceptance (+100 XP):** Awarded when an administrator accepts the observation for the catalog.

---

## 9. Biodiversity Data Protection Policy (SEC-09)

- Current prototype stores coarse locality descriptions (`coarse_location`) and rejects precise GPS coordinates.
- For future GPS-enabled deployments, observations matching vulnerable, threatened, or endangered species (IUCN Red List Categories CR, EN, VU) must automatically apply coordinate fuzzing to a minimum 10 km grid before publication.


---

## 10. Bring Your Own Key (BYOK) Credential Security (SEC-BYOK)

Vivédex implements a zero-persistence Bring Your Own Key (BYOK) architecture for Meta Model API credentials:

### 10.1 Memory-Only Credential Lifecycle
- **Volatile Session Storage:** User-provided API keys reside exclusively in server-side Streamlit session state (`st.session_state["user_meta_api_key"]`).
- **Zero Database Persistence:** User keys are strictly prohibited from SQLite storage. No database tables (`users`, `user_profiles`, `observations`, `audit_logs`) contain columns or values for user API keys.
- **Zero Disk and File Persistence:** Keys are never written to `.env`, temporary files, local caches, cookies, or browser local storage.
- **Session Cleanup:** User keys and connection state are immediately purged on user disconnect or session logout.

### 10.2 Per-Request Isolation & Precedence
- **Direct Parameter Passing:** The backend routes credentials explicitly: `backend.process_observation(..., api_key=user_key)`.
- **No Global Client Mutation:** The singleton `MetaAPIAdapter` does not store the user's key on the instance or set process environment variables (`os.environ["MODEL_API_KEY"]` is never overwritten by user input).
- **Precedence Hierarchy:**
  1. `My Meta API Key` (User-supplied session key) takes highest priority for that user's observations.
  2. `Application-Provided Key` (Operator environment variable `MODEL_API_KEY`) serves as platform fallback when no user key is connected.
  3. `Demo Fixture Mode` serves as offline deterministic fallback when no credentials are present.
- **Zero Cross-User Leakage:** A user's session key is isolated to that user's active session and is never accessible to concurrent sessions.

### 10.3 Key Masking and Error Sanitization
- **Key Masking:** The UI displays only masked hints (e.g. `••••••••••••••••••••...cdef`) and never displays the full key string after entry.
- **Log and Exception Sanitization:** Error handling strips authorization headers and bearer tokens from exception strings and log messages.
- **Minimal Text-Only Test Verification:** Connection testing issues a minimal text prompt (`Reply with exactly: VIVEDEX_API_CONNECTION_OK`) to verify the endpoint without transmitting specimen photographs.
