# Vivédex Threat Model and Security Architecture

## 1. Executive Summary
This document defines the formal threat model for the Vivédex biodiversity platform.
It establishes assets, threat actors, attack surfaces, trust boundaries, and mitigation controls.
All analysis adheres to the ASD-STE100 technical standard.

---

## 2. Protected Assets and Criticality

| Asset ID | Asset Description | Confidentiality | Integrity | Availability | Asset Criticality |
|---|---|---|---|---|---|
| **AST-01** | **User Credentials:** Salted password hashes, user salts, login handles. | High | Critical | High | **Critical** |
| **AST-02** | **Administrator Privileges:** Moderation authority, user role assignment, audit logs. | High | Critical | High | **Critical** |
| **AST-03** | **API Credentials:** `MODEL_API_KEY` for upstream Meta Model API. | Critical | Critical | High | **Critical** |
| **AST-04** | **Taxonomic Integrity:** Canonical nomenclature, GBIF usage keys, parent/child relationships. | Public | Critical | High | **High** |
| **AST-05** | **Contributor Data:** Researcher profile bios, display names, self-reported ORCID IDs. | Public | High | High | **Medium** |
| **AST-06** | **Scientific Observations:** Field notes, observation timestamps, model proposals, status. | Medium | Critical | High | **High** |
| **AST-07** | **Gamification State:** Earned badges, calculated XP, player progression levels. | Public | High | High | **Medium** |
| **AST-08** | **Application Continuity:** Streamlit runtime, SQLite database file integrity. | Medium | Critical | Critical | **High** |
| **AST-09** | **Sensitive Species Coordinates (Future):** Precise locations of endangered/threatened taxa. | Critical | Critical | High | **Critical (Future)** |

---

## 3. Threat Actors and Profiles

### Actor 1: Malicious Unauthenticated External Attacker (Script Kiddie / Internet Crawler)
- **Motivation:** Opportunistic vandalism, resource hijacking, bot registration, credential stuffing.
- **Capabilities:** Automated HTTP scanners, dictionary password lists, malformed image files, prompt injection text.
- **Access Level:** Anonymous public HTTP/Websocket requests.

### Actor 2: Malicious Authenticated Standard User
- **Motivation:** Privilege escalation, game system manipulation, harassment, vandalism.
- **Capabilities:** Access to authenticated endpoints, profile editing, field notes modification, observation creation.
- **Access Level:** Standard `user` role account.

### Actor 3: Compromised or Malicious Upstream Provider (Meta Model API / GBIF)
- **Motivation:** Supply-chain compromise, service degradation, malformed payload transmission.
- **Capabilities:** Man-in-the-middle or upstream compromised responses containing malicious scripts or extreme data sizes.
- **Access Level:** Upstream network response.

### Actor 4: Rogue or Compromised Administrator
- **Motivation:** Abuse of power, unauthorized data modification, concealment of malicious activities.
- **Capabilities:** Access to moderation queue, audit log inspection, user management.
- **Access Level:** `admin` role.

---

## 4. Entry Points and Attack Surfaces

```
[ Internet / External Clients ]
          │
          ├── (1) Image Upload Endpoint (st.file_uploader)
          ├── (2) Taxonomic Search Box (st.text_input)
          ├── (3) User Registration & Login (st.form)
          ├── (4) Contributor Profile Editor (Display Name, Bio, ORCID Link)
          ├── (5) Field Notes & Locality Input (Observations)
          ├── (6) Moderation Queue Controls (Admin only)
          │
          ▼
[ Trust Boundary 1: Presentation & Streamlit Runtime ]
          │
          ├── (7) External Meta Model API Request (Bearer Token via HTTPS)
          ├── (8) External GBIF Backbone API Request (Open HTTPS)
          │
          ▼
[ Trust Boundary 2: Domain Services & Authorization Layer ]
          │
          ▼
[ Trust Boundary 3: Local SQLite Database (data/vivedex.sqlite3) ]
```

---

## 5. Trust Boundaries

1. **Trust Boundary 1: Client to Presentation Layer:**
   - Separates untrusted user inputs (form text, uploaded image bytes, query parameters) from the server runtime.
   - All client inputs must undergo strict validation before processing.
2. **Trust Boundary 2: Application to External Model & Taxonomy APIs:**
   - Separates the internal application state from external third-party web services.
   - External responses (Meta JSON, GBIF responses) must be treated as untrusted data.
3. **Trust Boundary 3: Domain Services to Database Storage:**
   - Separates business logic from physical SQLite persistence.
   - All queries must enforce parameter binding. Foreign keys must be active.

---

## 6. Threat Scenarios and Vulnerability Analysis

### Threat Scenario 1: Cross-Site Scripting (XSS) via Unsanitized Profile or Observation Text
- **Target Asset:** AST-02 (Administrator Privileges), AST-05 (Contributor Data).
- **Attack Vector:** An attacker registers an account and updates their public display name, biography, or observation notes with a script payload (e.g., `<img src=x onerror=...>` or `javascript:...` link).
- **Existing Control:** None. Several UI components interpolate raw strings directly into `st.markdown(..., unsafe_allow_html=True)`.
- **Impact:** When an administrator opens the moderation queue or user directory, the script executes, enabling session hijacking or unauthorized administrative decisions.

### Threat Scenario 2: First-Registrant Administrative Takeover
- **Target Asset:** AST-02 (Administrator Privileges).
- **Attack Vector:** On a fresh deployment where no users exist, an external attacker registers an account.
- **Existing Control:** `AuthService.register_user` assigns `admin` role when `SELECT COUNT(*) FROM users;` returns 0.
- **Impact:** Attacker gains full administrative access immediately without credentials or approval.

### Threat Scenario 3: Denial of Service via Decompression Bomb Image
- **Target Asset:** AST-08 (Application Continuity).
- **Attack Vector:** Attacker uploads an 8 MB PNG image that expands to 80+ megapixels when decompressed in memory.
- **Existing Control:** Image size limit (8 MB) and `Image.open().verify()`.
- **Missing Control:** No explicit pixel dimension bounds check ($W \times H$).
- **Impact:** High memory consumption, CPU saturation, or server crash.

### Threat Scenario 4: Automated Gamification XP and Milestone Inflation
- **Target Asset:** AST-07 (Gamification State).
- **Attack Vector:** A user scripts automated calls to `save_to_collection()` across hundreds of taxa or creates empty observations with 5-character notes.
- **Existing Control:** Idempotent badge assignment and server-side calculation.
- **Missing Control:** No validation that saved taxa represent genuine field encounters; observation notes award XP before moderation review.
- **Impact:** Fake achievement inflation and degraded platform credibility.

### Threat Scenario 5: Exploitation of Sensitive Species Coordinates (Future Risk)
- **Target Asset:** AST-09 (Sensitive Species Coordinates).
- **Attack Vector:** Poachers query the platform for exact GPS coordinates of endangered animals or rare orchids.
- **Existing Control:** The current MVP strictly excludes exact GPS coordinates and records only coarse text locality.
- **Missing Control (for future releases):** Geographic blurring or coordinate masking rules for IUCN Red List taxa.
- **Impact:** Real-world harm to threatened wildlife populations.
