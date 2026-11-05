# Vivédex Experience Design Specification

## 1. Product Vision & Mission
Vivédex is an authoritative, visually captivating biodiversity discovery and personal cataloging platform.
It bridges multimodal artificial intelligence and formal taxonomy to empower naturalists, conservationists, students, and researchers to explore, identify, curate, and contribute biological knowledge.

### 1.1 Core Interaction Loop
$$\text{Discover} \longrightarrow \text{Identify} \longrightarrow \text{Verify} \longrightarrow \text{Collect} \longrightarrow \text{Learn} \longrightarrow \text{Contribute}$$

---

## 2. Design Principles

1. **Evidence-Based & Cautious:** AI inferences are never presented as verified scientific facts. Visual confidence, diagnostic traits, lookalikes, and authoritative GBIF taxonomic reconciliation are clearly distinguished.
2. **Natural History Museum Aesthetic:** Evokes the reverence of botanical atlases, specimen cabinets, and expedition field diaries. Uses rich organic tones, tactile card framing, and serif display typography.
3. **Restor.eco & Pokédex Fusion:** Blends ecological context and biome diversity with the satisfying encyclopedic completion mechanics of classic field guides.
4. **Persistent Attribution & Provenance:** Every taxon and observation links back to its authoritative data provider (GBIF Backbone Taxonomy, CC BY 4.0).
5. **Ethical Citizen Science:** Replaces aggressive streaks and gaming pressure with authentic naturalist progression, thoughtful field notes, and transparent community moderation.

---

## 3. Design System & Style Tokens

### 3.1 Authoritative Color Palette
```css
:root {
    /* Authoritative Natural Tones */
    --forest: #183B32;        /* Botanical primary; contrast >= 4.5:1 on light */
    --deep-forest: #102A25;   /* Surface darks, editorial headers */
    --moss: #718568;          /* Organic accents, secondary elements */
    --sage: #A9B99A;          /* Soft badges, subtle highlights */
    
    /* Backgrounds & Canvas */
    --ivory: #F5F2E9;         /* Base canvas background */
    --paper: #FCFAF4;         /* Specimen card containers & uploader canvas */
    --border: #D8D1C2;        /* Subtle card borders */
    --border-strong: #B8AE9C; /* Uploader dashed outline */
    
    /* Earth & Accent Tones */
    --earth: #A66B48;         /* Terracotta accents, milestone borders */
    --gold: #C6A66B;          /* Achievement markers, level crowns */
    --ink: #252C27;           /* High-contrast body text (>= 11:1 on ivory/paper) */
    --muted: #59645D;         /* High-contrast secondary captions (>= 4.5:1) */
    --white: #FFFFFF;         /* Crisp text inside dark hero surfaces */
    
    /* Moderation Status */
    --status-pending: #FEF7E0;
    --status-accepted: #E6F4EA;
    --status-review: #FCE8E6;
}
```

### 3.2 Contrast Compliance Matrix (WCAG 2.1 AA)

| Foreground Token | Background Surface | Contrast Ratio | Minimum AA Threshold | Status |
|---|---|---|---|---|
| `--ink` (`#252C27`) | `--paper` (`#FCFAF4`) | **13.5:1** | 4.5:1 (Normal text) | **PASS (AAA)** |
| `--ink` (`#252C27`) | `--ivory` (`#F5F2E9`) | **12.6:1** | 4.5:1 (Normal text) | **PASS (AAA)** |
| `--muted` (`#59645D`) | `--paper` (`#FCFAF4`) | **5.4:1** | 4.5:1 (Normal text) | **PASS (AA)** |
| `--forest` (`#183B32`) | `--paper` (`#FCFAF4`) | **9.8:1** | 4.5:1 (Normal text) | **PASS (AAA)** |
| `--white` (`#FFFFFF`) | `--deep-forest` (`#102A25`) | **13.8:1** | 3.0:1 (Large text) | **PASS (AAA)** |
| `--ivory` (`#F5F2E9`) | `--deep-forest` (`#102A25`) | **11.2:1** | 4.5:1 (Normal text) | **PASS (AAA)** |

### 3.3 Typography Tokens
- **Editorial Display Font:** *Cinzel* & *Playfair Display* (Google Fonts) for main page titles, specimen titles, and Latin binomial headers.
- **Scientific Binomial Style:** `font-style: italic; font-family: 'Playfair Display', serif; font-weight: 600;`
- **Body & Controls Font:** *Plus Jakarta Sans* / *Inter* for crisp, modern legibility across cards, tables, and forms.
- **Monospace Tokens:** `JetBrains Mono` / `ui-monospace` for Contributor IDs (`VDX-XXXXXX`), GBIF Taxon Keys, and Observation IDs.

---

## 4. Main Navigation Structure

| Page Order | Navigation Label | Icon | Route / URL Path | Target Experience |
|---|---|---|---|---|
| 1 | **Home** | 🧭 | `/home` | Naturalist expedition hub, diversity metrics, recent discoveries |
| 2 | **Search** | 🔍 | `/search` | Global search across taxonomy, sites, expeditions, and observations |
| 3 | **Explore** | 📖 | `/explore` | Visual specimen card grid, 10 taxonomic categories, GBIF search |
| 4 | **Identify** | 🌿 | `/identify` | 6-step evidence-based specimen identification workflow |
| 5 | **My Dex** | 📚 | `/mydex` | Personal biological encyclopedia, encounters, completion metrics |
| 6 | **Field Journal** | 📓 | `/journal` | Chronological observation diary with editable field notes |
| 7 | **Field Sites** | 📍 | `/sites` | Expedition sites, protected areas, ecological monitoring projects |
| 8 | **Organisations** | 🏛️ | `/organisations` | Research institutions, museums, parks, universities |
| 9 | **Quests** | ⚡ | `/quests` | Field habits, daily observation tasks, recurring biodiversity monitoring |
| 10 | **Achievements** | 🏆 | `/achievements` | Naturalist ranks (Observer to Steward) and milestone badge families |
| 11 | **Passport** | 👤 | `/passport` | Contributor credentials, research passport, bio, and ORCID link |
| 12 | **Knowledge** | 🕸️ | `/knowledge` | Graphical taxonomic lineage and neighborhood explorer |
| 13 | **Admin Console** | 🛡️ | `/admin` | *Restricted to Admins:* moderation queue, audit trail, platform metrics |

---

## 5. Page Specifications

### 5.1 Home (Expedition Dashboard)
- **Hero Section:** Rich editorial header: "Field Ecology & Natural History Platform" with museum-grade botanical framing.
- **Ecological Diversity Metrics:** 4-column cards: Recorded Sightings, Collected Taxa, Documented Families, Naturalist Rank & XP.
- **Core Workflow Pillars:** Six interactive workflow cards (Discover → Identify → Verify → Collect → Learn → Contribute).
- **Featured Field Sites:** Preview cards of ecological reserves with biome tags, elevation, and location data.
- **Naturalist Sign-In / Registration:** Embedded login and signup tabs with instant session activation.

### 5.2 Explore Dex & Categories
- **10 Curated Biological Categories:**
  1. 🦅 Birds (*Aves*)
  2. 🦊 Mammals (*Mammalia*)
  3. 🦎 Reptiles (*Reptilia*)
  4. 🐸 Amphibians (*Amphibia*)
  5. 🐟 Fish (*Actinopterygii*)
  6. 🦋 Insects (*Insecta*)
  7. 🕷️ Arachnids (*Arachnida*)
  8. 🌿 Plants (*Plantae*)
  9. 🍄 Fungi (*Fungi*)
  10. 🌊 Other Organisms (*Protista / Marine*)
- **Specimen Cards:** Visual cards featuring:
  - Specimen image with thumbnail framing.
  - Common name in bold; scientific binomial in italics.
  - Rank pill (e.g. `SPECIES`) and Family tag.
  - Encounter status indicator (`IN DEX` vs `NOT ENCOUNTERED`).
  - "Inspect Specimen" button opening the deep detail view.
  - "Save to My Dex" action.

### 5.3 Deep Species Detail Experience
- Prominent specimen photograph with source attribution.
- Full taxonomic hierarchy breadcrumb (Kingdom > Phylum > Class > Order > Family > Genus > Species).
- Diagnostic visual traits and lookalikes.
- Authoritative GBIF Backbone Taxonomy record (Status, Usage Key, Match Type, Score, CC BY 4.0 citation).
- User collection status (First encounter, latest encounter, total encounter count).
- Linked community observations.
- Direct "Record Field Encounter" action.

### 5.4 Identify (6-Step Evidence-Based Observation Workflow)
1. **1. Add a specimen photograph:** Clean file drag-and-drop box with paper canvas (`#FCFAF4`), subtle dashed border (`#B8AE9C`), and explicit 8 MB file size limit enforcement (`.streamlit/config.toml`).
2. **2. Review Photograph:** Rendered immediately upon file upload. Displays volatile in-memory preview with metadata safeguard notice.
3. **3. Analyse Specimen:** Prominent primary action button ("🔍 Analyse Specimen") with clear spinner status indicator.
4. **4. Candidate Identification:** Evidence-based candidate binomial in Playfair Display, suggested rank pill, confidence and diagnostic uncertainty note, observed morphological traits, and confusing lookalikes.
5. **5. Taxonomic Reconciliation (GBIF):** Authoritative GBIF Backbone Taxonomy match with canonical name, classification hierarchy, match score, CC BY 4.0 license, and warnings for higher-rank or fuzzy matches.
6. **6. Save Field Observation:** Field journal entry with optional locality, expedition link, and collection synchronization. Direct structured JSON export.

### 5.5 My Dex (Personal Encyclopedia)
- Grid of collected organisms arranged by taxonomic group or encounter date.
- Cumulative encounter counter (e.g. "Encounters: 3").
- Collection completion metrics (% of local reference families represented).
- Search and filter by Kingdom, Family, and common name.
- Direct link to inspect specimen details in the Knowledge Explorer.

### 5.6 Field Journal
- Chronological timeline cards.
- Provenance badge (`LIVE_ANALYSIS` vs `DEMO DATA`).
- Moderation status indicator (`PENDING`, `ACCEPTED_FOR_CATALOG`, `NEEDS_MORE_EVIDENCE`, `REJECTED`).
- Inline field notes editor.

### 5.7 Achievements (Naturalist Progression)
- Ranks:
  - Level 1: *Observer* (0 - 99 XP)
  - Level 2: *Explorer* (100 - 199 XP)
  - Level 3: *Naturalist* (200 - 299 XP)
  - Level 4: *Field Researcher* (300 - 399 XP)
  - Level 5: *Specialist* (400 - 499 XP)
  - Level 6+: *Biodiversity Steward* (500+ XP)
- Badge Families:
  - First Encounters (`first_encounter`)
  - Collection Milestone (`collector`)
  - Taxonomic Exploration (`family_explorer`)
  - Field Documentation (`field_naturalist`)
  - Platform Contribution (`contributor`)

---

## 6. Component Library & Visual Tokens

- **`.hero-banner`:** Deep botanical gradient surface (`#102A25` to `#183B32`) with guaranteed `#FFFFFF` heading and `#F5F2E9` subtitle contrast.
- **`[data-testid="stFileUploaderDropzone"]`:** Warm paper container (`#FCFAF4`) with subtle dashed outline (`#B8AE9C`) and forest green button.
- **`.specimen-card`:** Botanical card container with `--paper` background, `--border` outline, gentle box shadow, and hover elevation.
- **`.latin-binomial`:** Italicized serif typography for valid scientific names.
- **`.rank-pill`:** Small rounded badge in `--sage` with dark green text.
- **`.status-pill`:** High-contrast rounded pill indicating moderation state.
- **`.provenance-tag`:** Monospace citation badge highlighting licensing (`CC BY 4.0`) and origin.
- **`.privacy-badge`:** Subtle inline paper container with lock icon and metadata privacy notice.
- **`.security-badge`:** Mandatory local prototype security disclaimer.
---

## 7. Responsive Behavior & Accessibility
- **Fluid Layouts:** Uses Streamlit `layout="wide"` with responsive column distribution (`st.columns([1, 1])` or `st.columns([3, 1])`).
- **Contrast Ratios:** Text color `--ink` (`#252C27`) against `--paper` (`#FCFAF4`) yields contrast ratio $> 13:1$ (exceeding WCAG AAA).
- **Responsive Media:** Images use `width="stretch"` to adapt fluidly to laptop and desktop screens without horizontal overflow.

---

## 8. Account Settings & AI Provider Specification (BYOK)

### 8.1 Interface Workflow
The **Account Settings** page (`/settings`) implements a dedicated Bring Your Own Key (BYOK) experience:
1. **Instructional Onboarding:** Clear guidance with safe external links to the [Meta Model API Dashboard](https://dev.meta.ai/) and [Quickstart Documentation](https://dev.meta.ai/docs/quickstart).
2. **Password-Style Entry:** Masked input field with show/hide toggle, automated whitespace trimming, and empty submission rejection.
3. **Session-Only Memory Disclosure:** Explicit banner clarifying that keys reside exclusively in volatile server-side session memory and are never persisted to SQLite, user accounts, or disk.
4. **Live Verification:** Built-in "Test Connection" action sending a text-only ping (`Reply with exactly: VIVEDEX_API_CONNECTION_OK`) to verify endpoint responsiveness and display verified model (`muse-spark-1.3`).
5. **Key Management Controls:** Disconnect (clears session memory) and Replace API Key.


