# Vivédex: Towards a Provenance-Aware, Interconnected Biodiversity Knowledge and Discovery Platform

**Authors:** Vivédex Technical Architecture Team  
**Date:** November 2026  
**Document Classification:** Technical Whitepaper (ASD-STE100)  
**Repository:** `rpxgit/vivedex`  
**Release Target:** v0.1.0 (Hackathon Release Candidate)  

---

## 1. Executive Summary

Global biodiversity loss presents an urgent challenge for conservation science, ecological restoration, and education. While citizen science applications have engaged millions of casual observers, existing platforms frequently present three systemic limitations:
1. They treat computer-vision inferences as authoritative conclusions rather than tentative hypotheses.
2. They detach species sightings from explicit taxonomic lineages, field station contexts, and open scientific licenses.
3. They fail to provide contributors with persistent, traceable academic attribution and transparent data provenance.

Vivédex is an open, modular biodiversity discovery and provenance platform. It combines multimodal artificial intelligence inference with authoritative taxonomic reconciliation, personal collection curation, ecological site monitoring, habit-building mechanics, and researcher attribution. 

This whitepaper describes the architectural principles, data models, security controls, and verification mechanisms implemented in the Vivédex reference prototype.

---

## 2. The Biodiversity Information Problem

Ecological research and conservation planning depend on high-quality biodiversity occurrence data. However, the modern biodiversity data lifecycle exhibits structural problems:

- **Uncalibrated AI Overconfidence:** Modern multimodal large language models and computer vision classifiers often predict species identities with excessive certainty. When an artificial intelligence model encounters rare taxa, hybrid species, or damaged specimens, it frequently generates plausible but inaccurate binomial names ("hallucinations").
- **Taxonomic Fragmentation:** Organism names shift over time due to phylogenetic revisions, synonymy, and regional taxonomic disputes. Unreconciled text names prevent automated integration across biodiversity databases.
- **Attribution Loss:** Observers contribute photographs and field notes without persistent author identifiers (such as ORCID or standard contributor identifiers). Consequently, data aggregation pipelines strip original observer credit.
- **Data Licensing Ambiguity:** Citizen observations often lack clear copyright and license metadata, preventing legal ingestion into global scientific repositories such as the Global Biodiversity Information Facility (GBIF).
- **Observer Attrition:** Traditional biological survey tools lack positive engagement loops. Observers submit single records but do not sustain continuous observation habits.

Vivédex addresses these problems through a unified design philosophy: **candidate-first inference, strict taxonomic reconciliation, persistent researcher identity, and continuous field engagement.**

---

## 3. Product Vision and Core Loop

Vivédex structures the naturalist journey into a closed 6-step loop:

$$\text{Discover} \longrightarrow \text{Identify} \longrightarrow \text{Verify} \longrightarrow \text{Collect} \longrightarrow \text{Learn} \longrightarrow \text{Contribute}$$

1. **Discover:** The user observes an organism in a natural habitat, urban park, or research station.
2. **Identify:** The platform analyzes a specimen photograph using a multimodal vision model, extracting diagnostic morphological traits, candidate taxa, lookalike species, and explicit confidence scores.
3. **Verify:** The candidate name is reconciled against the authoritative GBIF Backbone Taxonomy. The system flags ambiguous matches and displays taxonomic status (accepted, synonym, doubtful).
4. **Collect:** The verified observation is saved to the user's personal digital herbarium/catalog ("My Dex") and persistent field diary ("Field Journal").
5. **Learn:** The user explores the organism's phylogenetic lineage in the Taxonomic Knowledge Graph, reading diagnostic distinctions and ecological relationships.
6. **Contribute:** The user links the observation to an accredited field research site, contributing to dynamic species richness calculations and community biodiversity audits.

---

## 4. Specimen Identification Architecture

The specimen identification pipeline in Vivédex adheres to a 10-stage sequential process:

```
[Raw Specimen Image]
       │
       ▼ (Stage 1: MIME & Header Validation: JPEG, PNG, WebP <= 8MB)
[Security & Image Processor]
       │
       ▼ (Stage 2: In-Memory EXIF Metadata Stripping & Normalization)
[Sanitized Image Buffer]
       │
       ▼ (Stage 3: Multimodal Vision Inference — Meta Muse Spark / Llama 3.2 Vision)
[Structured JSON Inference: Binomial, Confidence, Traits, Lookalikes]
       │
       ▼ (Stage 4: Authoritative GBIF Species API Reconciliation)
[Reconciled Taxonomy: TaxonKey, Canonical Name, Rank, Hierarchy]
       │
       ▼ (Stage 5: Lineage Insertion into Taxonomic Knowledge Graph)
[Taxonomic Graph Nodes & Edges]
       │
       ▼ (Stage 6: Provenance & Attribution Token Generation)
[Observation Record: Status, License CC BY 4.0, Timestamp, Contributor ID]
       │
       ▼ (Stage 7: Ecological Site & Expedition Linking)
[Field Site Update: Dynamic Species Richness]
       │
       ▼ (Stage 8: Gamification & Habit Progression Engine)
[Experience Points (XP) Calculation & Badge Verification]
       │
       ▼ (Stage 9: Personal Herbarium Collection Update)
[First Encounter / Re-encounter Cataloging]
       │
       ▼ (Stage 10: JSON Serialization & Data Export)
[Auditable Research Export]
```

### 4.1 In-Memory Metadata Sanitization
To preserve naturalist privacy and protect vulnerable wildlife locations, raw image bytes are processed exclusively in volatile memory using Pillow. All Exchangeable Image File Format (EXIF) tags, Global Positioning System (GPS) coordinates, camera serial numbers, and capture timestamps are stripped before base64 encoding.

### 4.2 Candidate-First Model Inference
The vision adapter interfaces with the Meta Model API (`muse-spark-1.3`). The model prompt enforces a strict JSON schema containing:
- Proposed scientific binomial name.
- Primary common name.
- Confidence score (0.00 to 1.00).
- Key diagnostic morphological features.
- Lookalike taxa and distinguishing characteristics.
- Stated environmental context.

Identifications are treated as **unconfirmed candidates**. The system displays explicit visual warnings whenever confidence is below 0.70 or when model uncertainty is reported.

---

## 5. Taxonomic Reconciliation and Knowledge Infrastructure

To eliminate nomenclature errors, candidate binomials are submitted synchronously to the GBIF Species Match API (`https://api.gbif.org/v1/species/match`).

### 5.1 Reconciliation Outcomes
- **Exact Match:** The proposed name maps directly to an accepted taxon key in the GBIF Backbone Taxonomy.
- **Synonym Match:** The proposed name maps to an outdated synonym; Vivédex presents the valid canonical name while preserving the submitted name in audit records.
- **Higher-Rank Match:** When specific epithet determination is uncertain, the system falls back to Genus or Family rank.
- **No Match / Ambiguous:** The system alerts the user and permits manual taxonomic search via Explore Dex.

### 5.2 Local Taxonomic Knowledge Graph
Taxonomic hierarchies (Kingdom $\rightarrow$ Phylum $\rightarrow$ Class $\rightarrow$ Order $\rightarrow$ Family $\rightarrow$ Genus $\rightarrow$ Species) are persisted in an SQLite knowledge graph. The graph supports parent-child traversal, recursive lineage inspection, and bidirectional linking between physical observations and taxonomic nodes.

---

## 6. Ecological Context and Field Sites (Restor.eco Model)

Vivédex integrates individual specimen observations into physical ecological contexts:
- **Field Sites:** Monitored ecosystems characterized by coordinates, biome category, total area (hectares), elevation, and habitat description.
- **Dynamic Species Richness:** Unlike static registry platforms, Vivédex computes species richness dynamically from verified observations linked to the site.
- **Expeditions and Projects:** Time-bounded survey expeditions organized by affiliated partner institutions (botanical gardens, universities, conservation trusts).

---

## 7. Researcher Identity, Provenance, and Progression

### 7.1 Persistent Researcher Passport (ORCID Model)
Every registered user receives a unique Vivédex Contributor Identifier (`VDX-XXXXXX`). The Researcher Passport records:
- Contributor identity and institutional affiliations.
- Primary research interests and taxonomic specializations.
- Cumulative verified field observations.
- Research outputs (checklists, survey datasets, formal publications).
- Four-level provenance states: `SELF_REPORTED`, `SOURCE_LINKED`, `PLATFORM_REVIEWED`, and `EXTERNALLY_VERIFIED`.

### 7.2 Habitica-Inspired Field Progression
To incentivize regular scientific monitoring, Vivédex includes a non-punitive gamification engine:
- **Habits and Quests:** Daily observation habits (e.g., Daily Field Scan, Botanical Journaling) and weekly BioBlitz goals award experience points (XP).
- **XP Calculation:**
  $$\text{Total XP} = (\text{Species} \times 50) + (\text{Notes} \times 20) + (\text{Catalog Observations} \times 100) + \text{Badge XP} + \text{Quest XP}$$
- **Milestone Badges:** Rule-based achievement milestones (Collector, Family Explorer, Field Naturalist, Contributor) unlock automatically upon meeting validated criteria.

---

## 8. Security Architecture and Credential Isolation

Vivédex implements strict security controls verified through automated adversarial testing:

1. **Session-Isolated BYOK (Bring Your Own Key):** Users supply their own Meta Model API key via Account Settings. User keys are held in volatile Streamlit session state and are **never** persisted to SQLite, user profile rows, or disk logs.
2. **Password Hashing:** Passwords are hashed using PBKDF2-HMAC-SHA256 with 600,000 iterations and unique cryptographic salts.
3. **Role-Based Access Control (RBAC):** Administrative interfaces (`/admin`) and service actions (organization creation, project approval) enforce strict role verification at both UI and service layer boundaries.
4. **Input Sanitization and HTML Escaping:** Dynamic user content is escaped before rendering to prevent Cross-Site Scripting (XSS).
5. **Denial-of-Service Defense:** Image uploads enforce an 8 MB payload ceiling and a $4096 \times 4096$ pixel dimension limit.

---

## 9. Implementation Status: Implemented vs. Planned

| Capability / Module | Current Implementation Status (v0.1.0) | Planned Future Work |
|---|---|---|
| Image Upload & Sanitization | **Fully Implemented** (In-memory EXIF stripping) | RAW format decoding, multi-image upload |
| AI Vision Inference | **Fully Implemented** (Meta Muse Spark JSON schema) | Local on-device edge model execution |
| Taxonomic Reconciliation | **Fully Implemented** (GBIF API match & caching) | Multi-taxonomic authority cross-matching |
| Personal Collection ("My Dex") | **Fully Implemented** (Encounter counts, notes) | Offline mobile synchronization |
| Field Journal | **Fully Implemented** (Observation history, status) | Voice memo transcription, GPS tracklogs |
| Field Sites & Expeditions | **Fully Implemented** (Dynamic species richness) | Satellite vegetation indices (NDVI) |
| Partner Organisations | **Fully Implemented** (Accredited entity directory) | Automated institutional SSO integration |
| Quests & Milestone Badges | **Fully Implemented** (Rule-based XP & badges) | Community-created local BioBlitz quests |
| Researcher Passport | **Fully Implemented** (VDX-ID, provenance states) | Live ORCID OAuth2 API bidirectional sync |
| Taxonomic Knowledge Graph | **Fully Implemented** (SQLite graph traversal) | Neo4j / RDF triple-store export |
| Admin Console & Moderation | **Fully Implemented** (Role-gated review & audit) | Automated anomaly detection in submissions |
| BYOK Credential Settings | **Fully Implemented** (Session isolation & validation) | Key rotation reminders & usage quotas |
| Windows Launcher & Checks | **Fully Implemented** (Batch, PowerShell, venv) | Automated MSIX / standalone installer |

---

## 10. Limitations

1. **Local Prototype:** Current v0.1.0 is designed as a standalone local prototype. It does not provide high-availability distributed clustering.
2. **Third-Party API Dependency:** Specimen identification requires network access to the Meta Model API and GBIF Species API. In offline conditions, the platform falls back to reference fixtures.
3. **Taxonomic Ambiguities:** The GBIF Backbone Taxonomy is an aggregated consensus checklist; regional splits or controversial reclassifications may require manual review.
4. **Non-Medical Determination:** Identifications must never be relied upon for toxicological, edible foraging, or veterinary assessments.

---

## 11. Conclusion

Vivédex demonstrates that modern biodiversity discovery tools can combine accessible artificial intelligence with strict taxonomic rigor, observer privacy, and persistent academic attribution. By treating machine learning predictions as explainable hypotheses and embedding every observation within authoritative taxonomies and monitored field habitats, Vivédex establishes a credible foundation for community-driven ecological monitoring.

---

## References

1. GBIF Secretariat (2023). GBIF Backbone Taxonomy. Checklist dataset. DOI: https://doi.org/10.15468/39omei. (Accessed via GBIF API, licensed under CC BY 4.0).
2. Restor Foundation (2023). Restor: Open Data for Ecological Restoration. https://restor.eco.
3. ORCID Inc. (2024). Open Researcher and Contributor ID Specification. https://orcid.org.
4. Habitica (2024). Gamified Productivity Mechanics and Community Progression. https://habitica.com.
