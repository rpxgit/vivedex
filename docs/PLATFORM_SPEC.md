# Vivédex Platform Specification

## 1. Product Identity and Mission
Vivédex is a biodiversity discovery, identification, collection, and contribution platform.
It combines multimodal AI vision capabilities (Meta Muse Spark) with authoritative global taxonomy reconciliation (GBIF Backbone Taxonomy).
The platform empowers users to discover organisms, verify species proposals, curate personal biodiversity collections, track field observations, and earn achievements inspired by modern citizen-science workflows.

### 1.1 Core Interaction Loop
$$\text{Discover} \longrightarrow \text{Identify} \longrightarrow \text{Verify} \longrightarrow \text{Collect} \longrightarrow \text{Learn} \longrightarrow \text{Contribute}$$

---

## 2. Platform Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Streamlit Web Interface                         │
│   (Home • Explore • Identify • Collection • Journal • Badges • Admin)  │
└────────────────────────────────────────────────────────────────────────┘
                                    │
    ┌───────────────────────────────┼──────────────────────────────┐
    ▼                               ▼                              ▼
┌───────────────┐           ┌───────────────┐              ┌───────────────┐
│ Meta Adapter  │           │ GBIF Adapter  │              │ Domain Layer  │
│ (Muse Spark)  │           │ (Taxonomy API)│              │ (Auth, Dex,   │
└───────────────┘           └───────────────┘              │  Badges, Mod) │
        │                           │                      └───────────────┘
        ▼                           ▼                              │
┌───────────────────────────────────────────┐                      ▼
│          In-Memory Preprocessing          │             ┌────────────────┐
│         (EXIF strip, Max 8MB)             │             │ SQLite3 Storage│
└───────────────────────────────────────────┘             │(Nodes & Edges) │
                                                          └────────────────┘
```

The system preserves the single-application Python architecture without external heavy frameworks (no Docker, Neo4j, Redis, or GraphRAG required).

---

## 3. Product Modules

### 3.1 Home Dashboard
Presents an overview of naturalist progression, including:
- Total recorded field observations.
- Distinct taxa cataloged in personal collection.
- Number of represented taxonomic families.
- Player level, current XP, and milestone progress.
- Quick link to the Identify pipeline.

### 3.2 Explore Dex
Provides direct exploration of the GBIF Backbone Taxonomy:
- Query by scientific name or vernacular common name.
- Filter by taxonomic rank (Species, Genus, Family, etc.).
- Inspect complete classification hierarchy and authority attribution.
- Direct **Save to My Collection** action with instant feedback.
- Strict warnings distinguishing exact matches from fuzzy or higher-rank matches.

### 3.3 Identify (Vision Pipeline)
Preserves the complete image-to-taxonomy reconciliation pipeline:
- Validates JPG, JPEG, PNG, and WebP up to 8 MB.
- In-memory EXIF metadata stripping.
- Inference via Meta Model API (`muse-spark-1.3`).
- Name matching via GBIF Species Match API.
- Separate display of AI visual traits and authoritative taxonomy.
- Explicit warnings: `AI-generated candidate. Not expert-verified.`
- Offline Demo Fixture Mode.
- Persistent **Record Field Observation** workflow saving to SQLite.
- Complete JSON observation download.

### 3.4 My Collection
Personal biological catalog:
- Displays unique collected taxa.
- Tracks initial encounter and latest encounter timestamps.
- Records cumulative encounter count (encounters increment without duplicating species).
- Search and filtering by common name, scientific name, family, and kingdom.
- Individual taxon removal.

### 3.5 Field Journal
Persistent observation log:
- Chronological list of user submissions.
- Field notes editor allowing progressive note enrichment.
- Coarse geographic locality tracking (city or region only).
- Visual status indicators (`PENDING`, `ACCEPTED_FOR_CATALOG`, `NEEDS_MORE_EVIDENCE`, `REJECTED`).
- Complete provenance labeling (`LIVE_ANALYSIS` vs `DEMO DATA`).

### 3.6 Achievements & XP
Gamified milestone engine:
- Experience points (XP) awarded for authentic contributions:
  - `+50 XP` for first encounter with a taxon.
  - `+20 XP` for detailed field notes (>= 5 characters).
  - `+100 XP` for observations accepted into the platform catalog.
- Deterministic level progression: $\text{Level} = \max(1, 1 + \lfloor \frac{\text{XP}}{100} \rfloor)$.
- Idempotent badge engine granting milestones once per user.

### 3.7 Researcher Profile
Persistent identity:
- Unique platform Contributor ID (`VDX-XXXXXX`).
- Naturalist biography and display name.
- Optional unverified external researcher identifier (e.g. ORCID URL).
- Aggregated biological metrics and earned badges.

### 3.8 Taxonomic Knowledge Explorer
Lightweight graph viewer:
- Traverses taxonomic lineages upwards (Species $\to$ Genus $\to$ Family $\to$ Kingdom).
- Lists connected child taxa, linked observations, and collectors.
- Exposes data source provenance and CC BY 4.0 metadata.

### 3.9 Administrator Console
Restricted to users with the `admin` role:
- Real-time platform metrics (users, observations, taxa, audit logs).
- User directory with account status.
- Observation moderation queue with status changes and reviewer notes.
- System audit log inspector.
- Curated demonstration data loader.

---

## 4. Authentication and Access Control

### 4.1 Cryptographic Password Storage
- Passwords are never stored in plaintext or logged.
- Salt generation: `secrets.token_hex(16)` per user.
- Key derivation: `hashlib.pbkdf2_hmac('sha256', password, salt, 100_000)`.
- Constant-time verification: `hmac.compare_digest`.

### 4.2 Administrator Bootstrap
- When the database has zero registered users, the first registration automatically receives the `admin` role.
- All subsequent registrations receive the `user` role.
- Registration forms do not expose role selection.

### 4.3 Server-Side Role Enforcement
- Every administrative action is guarded by `AuthService.require_admin(user)`.
- Non-admin attempts raise an `AuthorizationError` and are recorded in the audit log.

---

## 5. Knowledge Graph Model

The knowledge graph is modeled in SQLite using relational tables (`taxa`, `taxon_relationships`, `observations`, `collections`, `users`).

### 5.1 Node Types
- `Taxon`: Biological entity from GBIF.
- `Observation`: Field sighting record.
- `User`: Platform naturalist.
- `Source`: Data provider (GBIF Backbone Taxonomy).
- `Badge`: Platform milestone.

### 5.2 Relationship Edges
- `PARENT_OF`: Links higher taxonomic rank to lower rank (e.g., Family $\to$ Genus).
- `SYNONYM_OF`: Reconciles scientific synonyms where explicitly supported by GBIF.
- `OBSERVED_IN`: Connects an Observation to its resolved Taxon node.
- `RECORDED_BY`: Connects an Observation to the owning User.
- `COLLECTED_BY`: Connects a User to a Taxon node via the personal collection.
- `DERIVED_FROM`: Links Taxon nodes to their Source authority.
- `AWARDED_TO`: Links earned Badges to Users.

---

## 6. Privacy and Data Governance

1. **No Image Retention:** Uploaded images are held exclusively in volatile memory during vision analysis. Original image files are never written to permanent disk or database storage.
2. **Metadata Sanitization:** EXIF metadata (including camera serial numbers and GPS tags) is stripped before inference.
3. **No Exact GPS Coordinates:** Field journal records store optional coarse locations (e.g. city, region, or public reserve).
4. **Licensing Compliance:** GBIF Backbone Taxonomy metadata is published under CC BY 4.0. Mandatory attribution citations are permanently rendered across cards, exports, and knowledge nodes.
5. **Separation of Candidates and Facts:** AI vision model outputs are labeled as candidate suggestions. Administrative moderation (`ACCEPTED_FOR_CATALOG`) signifies platform guideline conformity, not verified scientific discovery.

---

## 7. Production Limitations and Prototype Boundaries

- **Single-Node SQLite:** Designed for local evaluation and small-group deployment. Concurrency is subject to SQLite file-level locking.
- **Local Prototype Authentication:** Session authentication operates in-memory within the Streamlit runtime. It is not hardened for multi-tenant internet deployment with OAuth or JWT.
- **API Rate Limiting:** Live Meta Model API and GBIF API calls depend on external network availability and upstream service quotas.

