# Vivédex Cybersecurity Assessment and Vulnerability Audit

## 1. Executive Summary
This document records an independent cybersecurity audit of Vivédex.
The audit evaluated authentication mechanisms, authorization boundaries, database operations, image handling pipelines, model integrations, web presentation layers, and supply chain dependencies.
All findings adhere to the ASD-STE100 technical standard.

### Severity Summary:
- **CRITICAL:** 0
- **HIGH:** 2
- **MEDIUM:** 4
- **LOW:** 2
- **INFORMATIONAL:** 1

---

## 2. Confirmed Vulnerability Findings

### Finding SEC-01: Stored and Reflected Cross-Site Scripting (XSS) via Unsanitized HTML Interpolation
- **Finding ID:** SEC-01
- **Severity:** **HIGH**
- **Affected Component:** Presentation Layer (`src/ui/`)
- **Exact File and Function:**
  - `src/ui/page_profile.py`: `render_profile_page()` (lines 52, 67, 177)
  - `src/ui/page_journal.py`: `render_journal_page()` (lines 84, 102)
  - `src/ui/page_explore.py`: `render_explore_page()` (lines 125, 136)
- **Supporting Evidence:**
  The application interpolates user-controlled and model-derived strings directly into HTML f-strings passed to `st.markdown(..., unsafe_allow_html=True)` without HTML escaping:
  ```python
  # src/ui/page_profile.py (line 52 & 67)
  <h2 style="...">{profile.display_name}</h2>
  {f'<div ...>{profile.bio}</div>' if profile.bio else ''}

  # src/ui/page_profile.py (line 177)
  <a href="{profile.external_orcid_url}" target="_blank">...</a>

  # src/ui/page_journal.py (line 102)
  <strong>AI Vision Summary:</strong> {m_data['observation_summary']}
  ```
- **Exploit Scenario:**
  1. An attacker registers an account and navigates to the Profile page.
  2. The attacker updates their `bio` to `<img src=x onerror=alert(document.cookie)>` or their `external_orcid_url` to `javascript:alert(1)`.
  3. When an administrator inspects the user directory or moderation queue, the injected JavaScript executes within the administrator's session context.
- **Impact:** Session hijacking, unauthorized administrative actions performed on behalf of the victim, client-side data exfiltration, and UI defacement.
- **Recommended Remediation:**
  1. Wrap all dynamic text variables in `html.escape()` prior to string interpolation into HTML blocks.
  2. For external links, validate the protocol strictly (`https://`) and escape the `href` attribute.
  3. Prefer standard Streamlit components (`st.markdown`, `st.write`, `st.link_button`) without `unsafe_allow_html=True`.
- **Regression Test Requirement:**
  Create an automated test passing script tags (`<script>alert(1)</script>`, `<img src=x onerror=...>`) through profile updates and verifying that rendered HTML contains escaped entities (`&lt;script&gt;`).

---

### Finding SEC-02: Unprotected First-User Administrator Bootstrap Race Condition
- **Finding ID:** SEC-02
- **Severity:** **HIGH**
- **Affected Component:** Authentication Service (`src/auth.py`)
- **Exact File and Function:** `src/auth.py`: `AuthService.register_user()` (lines 118-121)
- **Supporting Evidence:**
  ```python
  # Check if this is the first user (bootstrap administrator)
  cursor.execute("SELECT COUNT(*) FROM users;")
  user_count = cursor.fetchone()[0]
  assigned_role = "admin" if user_count == 0 else "user"
  ```
- **Exploit Scenario:**
  1. An administrator deploys Vivédex to a public testbed, cloud instance, or staging server.
  2. Before the legitimate owner accesses the URL, an automated web crawler or malicious actor accesses the registration form.
  3. The attacker registers `username=attacker` and automatically receives full administrator privileges (`role='admin'`).
  4. Additionally, two concurrent registration requests hitting an empty database can both observe `user_count == 0` and both receive `admin`.
- **Impact:** Complete platform compromise. The attacker can moderate observations, view all user records, inspect security audit logs, and deactivate other users.
- **Recommended Remediation:**
  1. In production, disable automatic registration-based administrator bootstrap.
  2. Require an initial administrator bootstrap token configured via an environment variable (`INITIAL_ADMIN_TOKEN`).
  3. Alternatively, provide a secure command-line provisioning script (`py -m src.cli bootstrap-admin`) to create the initial administrative account.
- **Regression Test Requirement:**
  Test concurrent registration attempts and verify that standard user registrations cannot receive `admin` role without administrative authorization.

---

### Finding SEC-03: Absence of Account Lockout and Rate Limiting on Login Endpoint
- **Finding ID:** SEC-03
- **Severity:** **MEDIUM**
- **Affected Component:** Authentication Service (`src/auth.py`, `src/ui/common.py`)
- **Exact File and Function:** `src/auth.py`: `AuthService.authenticate_user()` (lines 166-214)
- **Supporting Evidence:**
  The `authenticate_user()` method checks credentials against the SQLite database on each request without tracking failed login attempts, applying exponential backoff, or locking accounts.
- **Exploit Scenario:**
  An attacker conducts automated dictionary or credential-stuffing attacks against known naturalist handles (e.g., `naturalist_jane`, `admin`) using automated HTTP requests. The system processes thousands of attempts without throttling.
- **Impact:** Brute-force account takeover, unauthorized access to private naturalist field journals and personal collection records.
- **Recommended Remediation:**
  1. Track failed login attempts by username and client IP address in a `login_attempts` table.
  2. Lock accounts for 15 minutes after 5 consecutive failed attempts.
  3. Return a consistent error message: `"Invalid username or password or account temporarily locked."`
- **Regression Test Requirement:**
  Create an automated test submitting 6 invalid passwords and verifying that the 6th attempt is rejected with a locked account response.

---

### Finding SEC-04: Username Enumeration via Timing Side-Channel
- **Finding ID:** SEC-04
- **Severity:** **MEDIUM**
- **Affected Component:** Authentication Service (`src/auth.py`)
- **Exact File and Function:** `src/auth.py`: `AuthService.authenticate_user()` (lines 184-194)
- **Supporting Evidence:**
  ```python
  row = cursor.fetchone()
  if row is None:
      raise AuthenticationError("Invalid username or password.")

  user_id, uname, pwd_hash, salt, role, is_active, display_name, vivedex_id = row
  ...
  if not verify_password(password, salt, pwd_hash):
      raise AuthenticationError("Invalid username or password.")
  ```
  If the username does not exist, the function returns in $< 1 \text{ ms}$. If the username exists, it runs `verify_password()`, performing 100,000 PBKDF2 iterations which takes $\approx 50\text{–}100 \text{ ms}$.
- **Exploit Scenario:**
  An attacker measures response latency for different login attempts. Fast responses reveal invalid usernames; slow responses reveal valid usernames.
- **Impact:** Attacker accurately maps registered naturalist and administrator handles for targeted social engineering or focused password cracking.
- **Recommended Remediation:**
  Execute a dummy PBKDF2 hash computation against a hardcoded constant salt even when `row is None`, ensuring indistinguishable execution times across valid and invalid usernames.
- **Regression Test Requirement:**
  Verify that execution time for non-existent users is within $\pm 10\%$ of execution time for existing users with invalid passwords.

---

### Finding SEC-05: Gamification XP Inflation via Automated Taxon Scraping
- **Finding ID:** SEC-05
- **Severity:** **MEDIUM**
- **Affected Component:** Domain Layer (`src/collection_service.py`, `src/achievements.py`)
- **Exact File and Function:** `src/collection_service.py`: `save_to_collection()` (lines 220-275); `src/achievements.py`: `calculate_user_xp()` (lines 55-66)
- **Supporting Evidence:**
  `CollectionService.save_to_collection()` allows any logged-in user to add arbitrary taxa to their personal collection without verifying that an authentic photo observation took place.
  `calculate_user_xp()` awards $+50 \text{ XP}$ per distinct taxon in `collections`.
- **Exploit Scenario:**
  A user writes an automated script querying the GBIF Backbone Taxonomy through `Explore Dex` and calling `save_to_collection()` on 1,000 species. The user instantly accrues $50,000 \text{ XP}$ and achieves the highest rank (`Biodiversity Steward`) without conducting a single field observation.
- **Impact:** Destroys gamification integrity, demoralizes authentic citizen scientists, and invalidates platform credibility.
- **Recommended Remediation:**
  1. Distinguish between *bookmarked taxa* (wishlist) and *verified encounters*.
  2. Award XP exclusively when a taxon is added via a verified observation analysis or when accepted by community moderation.
- **Regression Test Requirement:**
  Verify that saving an unobserved taxon via the manual explorer does not grant field encounter XP.

---

### Finding SEC-06: Decompression Bomb and Memory Exhaustion Risk
- **Finding ID:** SEC-06
- **Severity:** **MEDIUM**
- **Affected Component:** Image Processing (`src/image_processor.py`)
- **Exact File and Function:** `src/image_processor.py`: `validate_image()` (lines 20-48), `preprocess_image()` (lines 50-93)
- **Supporting Evidence:**
  The validation pipeline checks the file size limit (8 MB), but does not inspect or restrict total pixel dimensions ($W \times H$) before full image decompression.
- **Exploit Scenario:**
  An attacker crafts a compressed 6 MB PNG with repeating scanlines that decompresses into an image of $10,000 \times 10,000$ pixels (100 megapixels). Decompressing and converting to 24-bit RGB consumes $> 300 \text{ MB}$ of RAM per request.
- **Impact:** Memory exhaustion, thread starvation, and potential denial of service for concurrent users.
- **Recommended Remediation:**
  Inspect image dimensions immediately after `Image.open()` and reject any image exceeding $4096 \times 4096$ pixels or 25,000,000 total pixels.
- **Regression Test Requirement:**
  Create a test asserting that images with extreme dimensions are rejected with `ImageValidationError`.

---

## 3. Low and Informational Findings

### Finding SEC-07: Insecure In-Memory Session Storage and Lack of Session Expiration
- **Finding ID:** SEC-07
- **Severity:** **LOW**
- **Affected Component:** Session Management (`app.py`, `src/ui/common.py`)
- **Supporting Evidence:** Authentication state is stored purely in `st.session_state["current_user"]`. There is no expiration timestamp, idle timeout, or cryptographically signed session cookie.
- **Impact:** A session left open on a shared workstation remains permanently active until browser closure or server restart.
- **Recommended Remediation:** Implement session expiration timestamps in `st.session_state` and invalidate sessions after 60 minutes of inactivity.

---

### Finding SEC-08: Lack of Protocol and Format Validation on External ORCID URLs
- **Finding ID:** SEC-08
- **Severity:** **LOW**
- **Affected Component:** User Profile Service (`src/collection_service.py`: `update_user_bio`)
- **Supporting Evidence:** The method accepts arbitrary strings as `external_orcid_url` without verifying that the URL begins with `https://orcid.org/`.
- **Impact:** Potential open redirect, phishing links, or script injection if rendered unsafely.
- **Recommended Remediation:** Enforce regex validation: `^https://orcid\.org/\d{4}-\d{4}-\d{4}-\d{3}[\dX]$` or empty string.

---

### Finding SEC-09: Sensitive Species Locality Protection (Future Architectural Risk)
- **Finding ID:** SEC-09
- **Severity:** **INFORMATIONAL**
- **Affected Component:** Observation Data Model (`src/models.py`)
- **Supporting Evidence:** The prototype currently restricts location to coarse textual descriptions (`coarse_location`), deliberately excluding exact GPS coordinates.
- **Future Risk:** When geospatial mapping is integrated in future releases, publishing exact coordinates of endangered species (IUCN Red List, CITES) poses severe real-world poaching and habitat destruction risks.
- **Recommended Remediation:** Implement a sensitive taxon filtering policy. Automatically fuzz coordinates (to a 10 km grid) for threatened or endangered species prior to public display.

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
