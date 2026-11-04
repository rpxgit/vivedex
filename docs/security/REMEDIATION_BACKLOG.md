# Vivédex Security Remediation Backlog

## 1. Executive Summary
This backlog provides an actionable, prioritized engineering remediation plan for all vulnerabilities and risks identified in the Vivédex Cybersecurity Assessment (RUN 009).
All tasks are categorized by priority and lifecycle phase.
All descriptions adhere to the ASD-STE100 technical standard.

---

## 2. Prioritized Remediation Task Matrix

| Task ID | Finding Ref | Priority | Title | Affected File(s) | Target Phase | Est. Effort |
|---|---|---|---|---|---|---|
| **REM-01** | SEC-01 | **P1 (High)** | Neutralize Stored & Reflected XSS via Strict HTML Escaping | `src/ui/page_*.py`, `src/ui/theme.py` | Immediate (Phase 1) | 3 hours |
| **REM-02** | SEC-02 | **P1 (High)** | Replace First-User Admin Bootstrap with Secure Provisioning | `src/auth.py`, `src/cli.py` | Immediate (Phase 1) | 3 hours |
| **REM-03** | SEC-06 | **P2 (Med)** | Enforce Maximum Image Dimensions to Prevent Decompression Bombs | `src/image_processor.py` | Next Sprint (Phase 2) | 2 hours |
| **REM-04** | SEC-03 | **P2 (Med)** | Implement Account Lockout and Brute-Force Throttling | `src/auth.py`, `src/database.py` | Next Sprint (Phase 2) | 4 hours |
| **REM-05** | SEC-04 | **P2 (Med)** | Eliminate Login Timing Side-Channel with Constant-Time Check | `src/auth.py` | Next Sprint (Phase 2) | 1 hour |
| **REM-06** | SEC-05 | **P2 (Med)** | Restrict Gamification XP Awards to Verified Observations | `src/collection_service.py`, `src/achievements.py` | Next Sprint (Phase 2) | 3 hours |
| **REM-07** | SEC-08 | **P3 (Low)** | Validate External Researcher URL Scheme (`https://orcid.org/`) | `src/collection_service.py` | Polish (Phase 3) | 1 hour |
| **REM-08** | SEC-07 | **P3 (Low)** | Add In-Memory Session Idle Timeout Invalidation | `app.py`, `src/ui/common.py` | Polish (Phase 3) | 2 hours |
| **REM-09** | SEC-09 | **P3 (Low)** | Formulate Endangered Species Locality Fuzzing Policy | `docs/data_governance/` | Hosted Beta (Phase 4)| 4 hours |

---

## 3. Detailed Remediation Action Plans

### REM-01: Neutralize Stored & Reflected XSS via Strict HTML Escaping
- **Objective:** Prevent arbitrary JavaScript execution when rendering user, model, or API strings into custom HTML cards.
- **Implementation Steps:**
  1. Import standard `html` module in `src/ui/common.py`, `src/ui/theme.py`, and all page controllers.
  2. Create a helper function `def safe_text(val: Any) -> str: return html.escape(str(val or ""))`.
  3. Wrap all dynamic variables (`profile.display_name`, `profile.bio`, `profile.external_orcid_url`, `obs.candidate_scientific_name`, `m_data['observation_summary']`, `search_query`) before inserting into f-strings.
  4. In `src/ui/page_profile.py`, validate that `external_orcid_url` starts with `https://` before rendering inside `<a href="...">`.
- **Target Verification:**
  Submit string `<script>alert(1)</script>` into bio. Confirm it renders as visible text without executing.

---

### REM-02: Replace First-User Admin Bootstrap with Secure Provisioning
- **Objective:** Eliminate unauthorized administrative takeover on newly deployed instances.
- **Implementation Steps:**
  1. In `src/auth.py`: Modify `register_user()`. Remove automatic `admin` role assignment when `user_count == 0`. Assign `role='user'` unconditionally to all standard registrations.
  2. Support an optional environment variable `INITIAL_ADMIN_TOKEN`. Allow registration with `role='admin'` only if the user provides the matching token.
  3. Provide a command-line administration script `py -m src.cli create-admin --username <name> --password <pwd>` that directly seeds an administrator account in the local database.
- **Target Verification:**
  Assert that registering the first user via web form assigns `role='user'`.

---

### REM-03: Enforce Maximum Image Dimensions to Prevent Decompression Bombs
- **Objective:** Mitigate memory exhaustion and DoS attacks using compressed image bombs.
- **Implementation Steps:**
  1. Define constants in `src/image_processor.py`:
     `MAX_IMAGE_WIDTH = 4096`, `MAX_IMAGE_HEIGHT = 4096`, `MAX_IMAGE_PIXELS = 16_777_216`.
  2. In `validate_image()`, open image using Pillow and check:
     ```python
     with Image.open(io.BytesIO(image_bytes)) as img:
         img.verify()
         if img.width > MAX_IMAGE_WIDTH or img.height > MAX_IMAGE_HEIGHT:
             raise ImageValidationError(f"Image dimensions ({img.width}x{img.height}) exceed maximum allowed {MAX_IMAGE_WIDTH}x{MAX_IMAGE_HEIGHT}.")
         if (img.width * img.height) > MAX_IMAGE_PIXELS:
             raise ImageValidationError("Image total pixel count exceeds memory threshold.")
     ```
- **Target Verification:**
  Submit synthetic image of dimensions $5000 \times 5000$. Verify immediate rejection with `ImageValidationError`.

---

### REM-04: Implement Account Lockout and Brute-Force Throttling
- **Objective:** Defend user accounts against automated password cracking.
- **Implementation Steps:**
  1. Add table `login_attempts (id INTEGER PRIMARY KEY, username TEXT, ip_address TEXT, attempted_at TEXT, success INTEGER)`.
  2. In `AuthService.authenticate_user()`, query failed attempts for `clean_username` within the last 15 minutes.
  3. If failed attempts $\ge 5$, raise `AuthenticationError("Account temporarily locked due to excessive failed attempts. Please try again in 15 minutes.")`.
  4. On successful login, clear failed attempt records for that username.
- **Target Verification:**
  Execute 5 failed login attempts in test; assert 6th attempt is locked.

---

### REM-05: Eliminate Login Timing Side-Channel with Constant-Time Check
- **Objective:** Prevent username enumeration through timing analysis.
- **Implementation Steps:**
  1. Generate a constant dummy salt and dummy password hash at module initialization in `src/auth.py`.
  2. When `cursor.fetchone()` returns `None`, execute `verify_password("dummy_password", DUMMY_SALT, DUMMY_HASH)`.
  3. Ensure both paths take uniform time ($\approx 80 \text{ ms}$) before raising `AuthenticationError("Invalid username or password.")`.
- **Target Verification:**
  Measure response duration for existing vs non-existent usernames. Confirm variance is $< 10\%$.

---

### REM-06: Restrict Gamification XP Awards to Verified Observations
- **Objective:** Restore integrity to player levels and milestone progression.
- **Implementation Steps:**
  1. In `src/achievements.py`, calculate first-encounter XP only from distinct taxa present in observations marked as `LIVE_ANALYSIS` or `ACCEPTED_FOR_CATALOG`.
  2. In `src/collection_service.py`, allow users to save taxa as "Target Wishlist" without incrementing field encounter XP.
  3. Award field notes XP (+20 XP) only when the observation passes community moderation.
- **Target Verification:**
  Save 10 taxa via `Explore Dex` without uploading photos. Verify user XP remains 0.

---

### REM-07: Validate External Researcher URL Scheme
- **Objective:** Prevent phishing links, open redirects, or javascript URLs in ORCID profile cards.
- **Implementation Steps:**
  1. In `src/collection_service.py:update_user_bio()`, validate `external_orcid_url` against regex:
     `^https://orcid\.org/[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{3}[0-9X]$`
  2. If the string is non-empty and does not match, raise `ValueError("Invalid ORCID URL. Must match format: https://orcid.org/XXXX-XXXX-XXXX-XXXX")`.
- **Target Verification:**
  Submit `javascript:alert(1)`. Verify that `ValueError` is raised and profile is not updated.
