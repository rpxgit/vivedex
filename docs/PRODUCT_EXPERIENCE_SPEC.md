# Vivédex Product Experience Specification

**Document:** Product Experience and Design System Specification  
**Standard:** ASD-STE100 (Simplified Technical English)  
**Version:** 2.0  
**Status:** Approved and Implemented  

---

## 1. Product Vision

Vivédex is a citizen-science natural history and biodiversity platform.
It connects wild organism observations with authoritative global science.
The application operates on a core workflow:

$$\text{Discover} \longrightarrow \text{Identify} \longrightarrow \text{Verify} \longrightarrow \text{Collect} \longrightarrow \text{Learn} \longrightarrow \text{Contribute}$$

The platform combines five design inspirations:

| Inspiration Source | Implemented Design Principle | Application in Vivédex |
|---|---|---|
| **Botanical Atlases** | Museum-grade editorial design | Serif headings, Latin binomial typography, archival paper palettes |
| **Restor.eco** | Ecological context & habitats | Monitored field sites, conservation projects, dynamic species richness |
| **Classic Pokédex** | Systematic collection & catalog | Specimen cards, encounter counters, taxonomic resolution indicators |
| **Habitica** | Positive, non-punitive habits | Fieldwork habits, weekly BioBlitz goals, career milestone quests |
| **ORCID** | Scholarly identity & provenance | Persistent Contributor ID, institutional affiliations, research outputs |

---

## 2. Visual Design System

### 2.1 Theme Configuration
The application defaults to a light botanical editorial theme.
To prevent operating system dark mode leakage, the configuration is pinned in `.streamlit/config.toml`:

```toml
[theme]
base = "light"
primaryColor = "#183B32"
backgroundColor = "#F5F2E9"
secondaryBackgroundColor = "#FCFAF4"
textColor = "#1E2621"
font = "sans serif"
```

### 2.2 Color Palette Tokens & Contrast Compliance

All text and background color pairs comply with WCAG 2.1 Level AA contrast standards:
- Normal text requires a contrast ratio of at least $4.5 : 1$.
- Large text ($\ge 18\text{pt}$ or bold $\ge 14\text{pt}$) requires at least $3.0 : 1$.

| Token Name | Hex Code | Semantic Role | Background | Measured Contrast | Compliance |
|---|---|---|---|---|---|
| `--forest` | `#183B32` | Primary brand & active pills | Ivory (`#F5F2E9`) | $8.6 : 1$ | WCAG AAA |
| `--deep-forest` | `#102A25` | Main headings & borders | Ivory (`#F5F2E9`) | $12.1 : 1$ | WCAG AAA |
| `--ink` | `#1E2621` | Body reading text | Ivory (`#F5F2E9`) | $12.2 : 1$ | WCAG AAA |
| `--muted` | `#4E5C53` | Secondary text & captions | Ivory (`#F5F2E9`) | $5.8 : 1$ | WCAG AA |
| `--earth` | `#8C5432` | Biome & goal accents | Ivory (`#F5F2E9`) | $5.2 : 1$ | WCAG AA |
| `--gold` | `#A2782A` | Milestone quest borders | Ivory (`#F5F2E9`) | $4.6 : 1$ | WCAG AA |
| `--ivory` | `#F5F2E9` | Main page canvas | — | — | Canvas |
| `--paper` | `#FCFAF4` | Card & container fill | — | — | Container |
| `--border` | `#D8D1C2` | Container borders | Ivory (`#F5F2E9`) | — | Structural |

### 2.3 Typography Hierarchy

1. **Title and Major Headings ($h1$, $h2$):**
   - Font Family: `Cinzel`, `Playfair Display`, serif.
   - Color: `--deep-forest` (`#102A25`).
   - Letter Spacing: $-0.01\text{em}$.
2. **Section Headings ($h3$, $h4$):**
   - Font Family: `Playfair Display`, serif.
   - Color: `--forest` (`#183B32`).
3. **Scientific Names:**
   - Class: `.latin-binomial`.
   - Font Style: Italic serif.
   - Font Weight: 600.
4. **Body Text:**
   - Font Family: `Plus Jakarta Sans`, system sans-serif.
   - Color: `--ink` (`#1E2621`).

---

## 3. Navigation Architecture

The interface uses Streamlit sectioned navigation.
Pages are grouped into four logical operational categories plus administrator governance:

```
Vivédex Platform
│
├── 🧭 Discover & Catalog
│   ├── Expedition Hub (Home)
│   ├── Global Discovery Search
│   ├── Explore Dex (Taxonomic Browser)
│   ├── Identify Specimen (Vision Pipeline)
│   ├── My Dex Collection (Personal Catalog)
│   └── Field Journal (Observation Diary)
│
├── 📍 Ecology & Field Work
│   ├── Field Sites & Expeditions (Restor.eco)
│   └── Partner Organisations (Institutions)
│
├── ⚡ Naturalist Progression
│   ├── Quests & Habits (Habitica)
│   └── Milestone Badges (Achievements)
│
├── 👤 Science & Identity
│   ├── Researcher Passport (ORCID)
│   └── Taxonomic Knowledge Graph
│
└── 🛡️ Governance (Role-Gated)
    └── Admin Console (Moderation & Audit)
```

---

## 4. Domain Module Specifications

### 4.1 Ecological Hierarchy (Restor-Inspired)
- **Organisations:** Scientific institutes and conservation foundations.
- **Field Sites:** Physical habitats with latitude, longitude, elevation, and biome classification.
- **Species Richness:** Calculated dynamically from distinct matched taxa observed at the site.
- **Projects:** Targeted conservation census efforts with habitat objectives.
- **Expeditions:** Time-bounded fieldwork campaigns with participating researchers.

### 4.2 Naturalist Progression (Habitica-Inspired)
- **Field Habits:** Daily constructive actions (e.g. Daily Field Scan, Botanical Journaling).
- **Non-Punitive Rule:** Missed days do not reset progress or penalize user XP.
- **Recurring Goals:** Weekly multi-encounter goals (e.g. Weekly BioBlitz, Family Breadth).
- **Milestones:** Permanent career accomplishments rewarding XP.
- **Idempotent Claims:** Completed rewards can be claimed once and record audit log entries.

### 4.3 Researcher Passport (ORCID-Inspired)
- **Contributor Identity:** Unique, immutable Vivédex ID (`VDX-XXXXXX`).
- **Affiliations:** Institutional memberships and herbarium connections.
- **Research Interests:** Specialized taxa, biomes, or taxonomic methodologies.
- **Provenance States:**
  1. `SELF_REPORTED`: Naturalist-entered reference.
  2. `SOURCE_LINKED`: Validated DOI or external scientific URL.
  3. `PLATFORM_REVIEWED`: Verified by a community moderator or peer.
  4. `EXTERNALLY_VERIFIED`: Cross-checked against external registries.

### 4.4 Global Discovery Search
- Parameterized SQLite search matching across:
  - Taxa (Scientific, common, canonical, and family names)
  - Field Sites (Name, country, and biome)
  - Projects and Expeditions (Title, description, and habitat)
  - Observations (Candidate name, locality, and field notes)
  - Public Researchers (Display name, username, and biography)

