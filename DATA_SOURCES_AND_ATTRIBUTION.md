# Vivédex — External Data Sources, Licenses, and Attribution

This document describes all external data sources, Application Programming Interfaces (APIs), third-party libraries, and intellectual property attributions used by Vivédex.

Writing standard: ASD-STE100 (Simplified Technical English).

---

## 1. Authoritative Taxonomic Data: GBIF Backbone Taxonomy

Vivédex queries the Global Biodiversity Information Facility (GBIF) Species Match API for taxonomic reconciliation, vernacular name resolution, and phylogenetic rank determination.

### Attribution Statement
> **GBIF Secretariat (2023). GBIF Backbone Taxonomy. Checklist dataset.**  
> **DOI:** https://doi.org/10.15468/39omei  
> **License:** Creative Commons Attribution 4.0 International (CC BY 4.0)  
> **Terms:** https://creativecommons.org/licenses/by/4.0/

### Scope of License
- **Applicability:** The CC BY 4.0 license applies specifically to the GBIF Backbone Taxonomy checklist data retrieved via `https://api.gbif.org/v1/species/match`.
- **Exclusion Notice:** This license does **not** apply to individual occurrence records, specimen photographs, dataset publishers, or third-party datasets hosted elsewhere on GBIF.org. Vivédex does not copy or redistribute GBIF bulk occurrence datasets.

---

## 2. Artificial Intelligence Vision Model: Meta Model API

Vivédex interfaces with the Meta Model API for multimodal image understanding and candidate species determination.

### Service Details
- **Provider:** Meta Platforms, Inc.
- **Model Identifier:** `muse-spark-1.3` (Multimodal Vision Inference)
- **API Documentation & Dashboard:** https://dev.meta.ai/
- **Integration Architecture:** Bring Your Own Key (BYOK). Each authenticated user connects their personal developer key.

### Data Privacy and Key Isolation
- **Ephemeral Session Storage:** User API keys are stored exclusively in volatile server session memory (`st.session_state`).
- **Zero Database Persistence:** User API keys are never written to SQLite database tables, audit logs, or disk caches.
- **No Training on User Data:** Requests sent to the model endpoint are processed for real-time inference only.
- **Terms of Service:** Users of Vivédex must comply with the Meta Terms of Service and developer policies when acquiring and using their personal API keys.

---

## 3. Product Design Inspirations (Conceptual References)

Vivédex acknowledges the following open platforms and products that provided conceptual inspiration for user experience patterns:

| Reference Platform | Conceptual Contribution | Intellectual Property Notice |
|---|---|---|
| **Restor.eco** | Ecological context, monitored field sites, dynamic species richness | Conceptual reference only. No code, trademarks, or proprietary map assets used. |
| **Classic Pokédex** | Taxon discovery, collection catalogs ("My Dex"), specimen cards | Conceptual reference only. All assets, icons, and branding are original Vivédex works. |
| **Habitica** | Daily field habits, milestone quests, non-punitive XP progression | Conceptual mechanics only. No assets or source code from Habitica used. |
| **ORCID** | Persistent researcher IDs (`VDX-XXXXXX`), provenance states | Conceptual identity pattern only. ORCID is a registered trademark of ORCID, Inc. |
| **Craft Anything** | Evidence-based inspection, multi-resolution verification | Architectural design pattern only. |

---

## 4. Open-Source Software Components

Vivédex is built with the following open-source libraries and frameworks:

| Component | License | Author / Copyright Holder | Usage in Vivédex |
|---|---|---|---|
| **Python** (3.10+) | PSF License | Python Software Foundation | Core programming language |
| **Streamlit** (>=1.30.0) | Apache 2.0 | Snowflake Inc. / Streamlit contributors | Application frontend and reactive UI engine |
| **Pydantic** (>=2.0.0) | MIT License | Samuel Colvin and contributors | Data validation and schema enforcement |
| **Pillow** (PIL) (>=10.0.0) | HPND License | Jeffrey A. Clark (Alex) and contributors | Image processing, sanitization, EXIF stripping |
| **HTTPX** (>=0.25.0) | BSD 3-Clause | Encode OSS Ltd. / Tom Christie | Asynchronous and synchronous HTTP API client |
| **Pytest** (>=8.0.0) | MIT License | Holger Krekel and pytest development team | Automated test suite and regression runner |
| **SQLite** (3.x) | Public Domain | D. Richard Hipp / SQLite Team | Embedded relational database and knowledge graph |
| **python-dotenv** (>=1.0.0) | BSD 3-Clause | Saurabh Kumar and contributors | Optional local environment variable configuration |

---

## 5. User-Contributed Content and Specimen Data Licensing

- **User Photographs:** Naturalists retain copyright over their submitted photographs. When submitting observations to the community catalog, users license their metadata under Creative Commons Attribution 4.0 International (CC BY 4.0) to support scientific research.
- **Location Privacy:** Coarse geographic coordinates are logged at the field site or regional level. Precise micro-coordinates of endangered taxa are protected from public exposure.
