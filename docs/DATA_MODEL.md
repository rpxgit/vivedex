# Vivédex Data Model Specification

## 1. Overview
The Vivédex platform uses a local-first SQLite database architecture (`data/vivedex.sqlite3`).
All relationships enforce referential integrity with `PRAGMA foreign_keys = ON;`.
The database layer includes forward migration management via the `schema_version` table.

---

## 2. Entity Relational Architecture

### 2.1 Table: `schema_version`
Stores database migration history.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `version` | INTEGER | PRIMARY KEY | Integer schema version number |
| `applied_at` | TEXT | NOT NULL | ISO 8601 UTC timestamp of migration |
| `description` | TEXT | NOT NULL | Description of the applied schema migration |

---

### 2.2 Table: `users`
Stores core user account credentials and authentication metadata.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique internal user identifier |
| `username` | TEXT | UNIQUE NOT NULL COLLATE NOCASE | Unique lowercase login handle |
| `password_hash` | TEXT | NOT NULL | PBKDF2-HMAC-SHA256 hash (100,000 iterations) |
| `salt` | TEXT | NOT NULL | Cryptographically secure 16-byte random hex salt |
| `role` | TEXT | NOT NULL CHECK(role IN ('admin', 'user')) | System role. First user is 'admin'; later users are 'user' |
| `is_active` | INTEGER | NOT NULL DEFAULT 1 | 1 for active account, 0 for deactivated |
| `created_at` | TEXT | NOT NULL | Account creation ISO 8601 timestamp |

**Indexes:**
- `idx_users_username` ON `users (username)`

---

### 2.3 Table: `user_profiles`
Stores public researcher credentials, display attributes, and external links.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `user_id` | INTEGER | PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE | 1-to-1 link to user account |
| `vivedex_id` | TEXT | UNIQUE NOT NULL | Unique platform identifier (format: `VDX-XXXXXX`) |
| `display_name` | TEXT | NOT NULL | Naturalist public display name |
| `bio` | TEXT | DEFAULT '' | Natural history background and research interests |
| `external_orcid_url` | TEXT | DEFAULT '' | Optional self-reported external ORCID identifier (Unverified) |
| `created_at` | TEXT | NOT NULL | Profile creation timestamp |
| `updated_at` | TEXT | NOT NULL | Profile last modified timestamp |

**Indexes:**
- `idx_user_profiles_user_id` ON `user_profiles (user_id)`

---

### 2.4 Table: `taxa`
Authoritative biological taxonomy nodes reconciled from the GBIF Backbone Taxonomy.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Internal primary key |
| `taxon_id` | INTEGER | UNIQUE | GBIF usageKey identifier (or deterministic negative integer) |
| `scientific_name` | TEXT | NOT NULL | Binomial or scientific name with authorship |
| `canonical_name` | TEXT | NULL | Canonical binomial/trinomial without authorship |
| `common_name` | TEXT | NULL | Vernacular or common name |
| `rank` | TEXT | NULL | Taxonomic rank (SPECIES, GENUS, FAMILY, etc.) |
| `status` | TEXT | NULL | Taxonomic status (ACCEPTED, SYNONYM, DOUBTFUL) |
| `match_type` | TEXT | NULL | GBIF match type (EXACT, FUZZY, HIGHERRANK) |
| `kingdom` | TEXT | NULL | Kingdom name |
| `phylum` | TEXT | NULL | Phylum name |
| `class_name` | TEXT | NULL | Class name |
| `order_name` | TEXT | NULL | Order name |
| `family` | TEXT | NULL | Family name |
| `genus` | TEXT | NULL | Genus name |
| `species` | TEXT | NULL | Specific epithet |
| `authorship` | TEXT | NULL | Taxon authority citation |
| `source_id` | TEXT | NULL | Upstream source identifier |
| `data_provider` | TEXT | DEFAULT 'GBIF Backbone Taxonomy' | Taxonomic authority |
| `licence` | TEXT | DEFAULT 'CC BY 4.0' | Open metadata license |
| `attribution` | TEXT | NOT NULL | Mandatory attribution citation |
| `retrieved_at` | TEXT | NOT NULL | Timestamp when record was fetched |
| `created_at` | TEXT | NOT NULL | Creation timestamp |

**Indexes:**
- `idx_taxa_taxon_id` ON `taxa (taxon_id)`
- `idx_taxa_scientific_name` ON `taxa (scientific_name)`

---

### 2.5 Table: `taxon_relationships`
Taxonomic graph edges linking higher and lower taxa.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Internal primary key |
| `parent_taxon_id` | INTEGER | NOT NULL REFERENCES taxa(taxon_id) ON DELETE CASCADE | Parent taxon key |
| `child_taxon_id` | INTEGER | NOT NULL REFERENCES taxa(taxon_id) ON DELETE CASCADE | Child taxon key |
| `relationship_type` | TEXT | NOT NULL CHECK(relationship_type IN ('PARENT_OF', 'SYNONYM_OF')) | Graph relationship type |
| `source` | TEXT | DEFAULT 'GBIF' | Data source establishing relationship |
| `created_at` | TEXT | NOT NULL | Creation timestamp |

**Constraints:**
- `UNIQUE(parent_taxon_id, child_taxon_id, relationship_type)`

**Indexes:**
- `idx_taxon_rel_parent` ON `taxon_relationships (parent_taxon_id)`
- `idx_taxon_rel_child` ON `taxon_relationships (child_taxon_id)`

---

### 2.6 Table: `collections`
Personal biodiversity catalogs tracking user encounters with distinct taxa.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Internal primary key |
| `user_id` | INTEGER | NOT NULL REFERENCES users(id) ON DELETE CASCADE | Owning naturalist ID |
| `taxon_id` | INTEGER | NOT NULL REFERENCES taxa(taxon_id) ON DELETE CASCADE | Saved taxon reference |
| `first_encounter_at` | TEXT | NOT NULL | Timestamp of initial encounter |
| `last_encounter_at` | TEXT | NOT NULL | Timestamp of most recent encounter |
| `encounter_count` | INTEGER | NOT NULL DEFAULT 1 | Total number of recorded encounters |
| `notes` | TEXT | DEFAULT '' | Personal naturalist notes |
| `created_at` | TEXT | NOT NULL | Creation timestamp |

**Constraints:**
- `UNIQUE(user_id, taxon_id)`: A taxon is collected once per user; repeat encounters increment `encounter_count`.

**Indexes:**
- `idx_collections_user_id` ON `collections (user_id)`
- `idx_collections_taxon_id` ON `collections (taxon_id)`

---

### 2.7 Table: `observations`
Persistent organism field records from vision analysis or manual input.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Internal primary key |
| `observation_id` | TEXT | UNIQUE NOT NULL | Human-readable record ID (`OBS-YYYYMMDD-XXXX`) |
| `owner_id` | INTEGER | NOT NULL REFERENCES users(id) ON DELETE CASCADE | User who recorded observation |
| `candidate_scientific_name` | TEXT | NOT NULL | Proposed binomial name from vision model |
| `matched_taxon_id` | INTEGER | REFERENCES taxa(taxon_id) ON DELETE SET NULL | Linked GBIF taxon key |
| `observation_timestamp` | TEXT | NOT NULL | Timestamp of occurrence |
| `field_notes` | TEXT | DEFAULT '' | Naturalist field observations |
| `coarse_location` | TEXT | DEFAULT '' | Coarse region or city (never exact GPS) |
| `model_result_json` | TEXT | NOT NULL | Serialized raw vision model candidate payload |
| `gbif_result_json` | TEXT | NULL | Serialized raw GBIF reconciliation response |
| `taxonomic_resolution` | TEXT | NULL | Resolution match quality (EXACT, FUZZY, etc.) |
| `moderation_status` | TEXT | NOT NULL DEFAULT 'PENDING' CHECK(moderation_status IN ('PENDING', 'ACCEPTED_FOR_CATALOG', 'NEEDS_MORE_EVIDENCE', 'REJECTED')) | Submission workflow status |
| `provenance` | TEXT | NOT NULL DEFAULT 'LIVE_ANALYSIS' | Data origin ('LIVE_ANALYSIS' or 'DEMO DATA') |
| `created_at` | TEXT | NOT NULL | Creation timestamp |

**Indexes:**
- `idx_observations_owner_id` ON `observations (owner_id)`
- `idx_observations_status` ON `observations (moderation_status)`

---

### 2.8 Table: `badges`
Master catalog of available achievement badges and XP incentives.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Internal primary key |
| `code` | TEXT | UNIQUE NOT NULL | Semantic badge key (`first_encounter`, etc.) |
| `name` | TEXT | NOT NULL | Public badge title |
| `description` | TEXT | NOT NULL | Narrative explanation of achievement |
| `rule_description` | TEXT | NOT NULL | Technical evaluation rule |
| `icon` | TEXT | DEFAULT '' | Visual icon marker |
| `xp_reward` | INTEGER | NOT NULL DEFAULT 0 | Experience point reward granted |
| `created_at` | TEXT | NOT NULL | Timestamp |

---

### 2.9 Table: `user_badges`
Awarded badges per user ensuring idempotency.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Internal primary key |
| `user_id` | INTEGER | NOT NULL REFERENCES users(id) ON DELETE CASCADE | Recipient user ID |
| `badge_id` | INTEGER | NOT NULL REFERENCES badges(id) ON DELETE CASCADE | Awarded badge definition |
| `awarded_at` | TEXT | NOT NULL | Award timestamp |

**Constraints:**
- `UNIQUE(user_id, badge_id)`: Prevents duplicate award issuance.

**Indexes:**
- `idx_user_badges_user_id` ON `user_badges (user_id)`

---

### 2.10 Table: `moderation_events`
Audit log of administrative moderation actions on observations.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Internal primary key |
| `observation_id` | INTEGER | NOT NULL REFERENCES observations(id) ON DELETE CASCADE | Reviewed observation ID |
| `moderator_id` | INTEGER | REFERENCES users(id) ON DELETE SET NULL | Reviewing administrator user ID |
| `previous_status` | TEXT | NOT NULL | Status before moderation action |
| `new_status` | TEXT | NOT NULL | Status assigned by moderator |
| `moderation_note` | TEXT | DEFAULT '' | Mandatory or optional justification |
| `created_at` | TEXT | NOT NULL | Decision timestamp |

**Indexes:**
- `idx_moderation_obs_id` ON `moderation_events (observation_id)`

---

### 2.11 Table: `audit_logs`
Comprehensive platform security and compliance event audit trail.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Internal primary key |
| `user_id` | INTEGER | REFERENCES users(id) ON DELETE SET NULL | Acting user ID (or NULL for system) |
| `action` | TEXT | NOT NULL | Action type code (e.g. `USER_REGISTERED`) |
| `entity_type` | TEXT | NOT NULL | Target entity type (`USER`, `OBSERVATION`, etc.) |
| `entity_id` | TEXT | NULL | Identifier of affected entity |
| `details` | TEXT | NULL | Contextual information |
| `timestamp` | TEXT | NOT NULL | ISO 8601 UTC timestamp |

**Indexes:**
- `idx_audit_logs_user_id` ON `audit_logs (user_id)`
- `idx_audit_logs_action` ON `audit_logs (action)`

