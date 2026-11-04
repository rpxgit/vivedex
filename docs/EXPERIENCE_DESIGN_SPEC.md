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

### 3.1 Color Palette
```css
:root {
    /* Primary Natural Tones */
    --forest: #183B32;        /* Deep botanical primary */
    --deep-forest: #102A25;   /* Surface darks, headers */
    --moss: #718568;          /* Organic accents, secondary elements */
    --sage: #A9B99A;          /* Soft badges, subtle highlights */
    
    /* Backgrounds & Paper */
    --ivory: #F5F2E9;         /* Warm background surfaces */
    --paper: #FCFAF4;         /* Specimen card containers */
    --border: #E3DDD0;        /* Subtle botanical borders */
    
    /* Earth & Accent Tones */
    --earth: #A66B48;         /* Warm terracotta, warning states */
    --gold: #C6A66B;          /* Achievement markers, level crowns */
    --ink: #252C27;           /* High-contrast body text */
    --muted: #777E73;         /* Captions, taxonomic authorities */
    
    /* Functional Status */
    --status-pending: #E8F0FE;
    --status-accepted: #E6F4EA;
    --status-needs-evidence: #FEF7E0;
    --status-rejected: #FCE8E6;
}
```

### 3.2 Typography Tokens
- **Editorial Display Font:** *Cinzel* & *Playfair Display* (Google Fonts) for main page titles, specimen titles, and Latin binomial headers.
- **Scientific Binomial Style:** `font-style: italic; font-family: 'Playfair Display', serif; font-weight: 600;`
- **Body & Controls Font:** *Plus Jakarta Sans* / *Inter* for crisp, modern legibility across cards, tables, and forms.
- **Monospace Tokens:** `JetBrains Mono` / `ui-monospace` for Contributor IDs (`VDX-XXXXXX`), GBIF Taxon Keys, and Observation IDs.

---

## 4. Main Navigation Structure

| Page Order | Navigation Label | Icon | Route / URL Path | Target Experience |
|---|---|---|---|---|
| 1 | **Home** | 🧭 | `/home` | Naturalist expedition hub, diversity metrics, recent discoveries |
| 2 | **Explore** | 🔍 | `/explore` | Visual specimen card grid, 10 taxonomic categories, GBIF search |
| 3 | **Identify** | 🌿 | `/identify` | 10-step AI vision + GBIF reconciliation workflow |
| 4 | **My Dex** | 📚 | `/mydex` | Personal biological encyclopedia, encounters, completion metrics |
| 5 | **Field Journal** | 📓 | `/journal` | Chronological observation diary with editable field notes |
| 6 | **Knowledge** | 🕸️ | `/knowledge` | Graphical taxonomic lineage and neighborhood explorer |
| 7 | **Achievements** | 🏆 | `/achievements` | Naturalist ranks (Observer to Steward) and milestone badge families |
| 8 | **Profile** | 👤 | `/profile` | Contributor credentials, bio, and unverified ORCID citation |
| 9 | **Admin Console** | 🛡️ | `/admin` | *Restricted to Admins:* moderation queue, audit trail, metrics |

---

## 5. Page Specifications

### 5.1 Home (Expedition Dashboard)
- **Hero Section:** Rich botanical header: "Vivédex Expedition Hub" with subtitle and naturalist overview.
- **Ecological Diversity Metrics:** 4-column cards: Recorded Sightings, Collected Taxa, Documented Families, Naturalist Rank & XP.
- **Rank Progression:** Visual status card showing current rank (*Observer*, *Explorer*, *Naturalist*, *Field Researcher*, *Specialist*, *Biodiversity Steward*) and XP bar.
- **Recent Discoveries Stream:** Specimen preview cards displaying candidate name, observation date, and moderation status.
- **Expedition Quests & Milestones:** Next achievable badge with dynamic criteria progress bar.
- **Quick Action Call-to-Actions:** "🌱 Identify Organism Photograph" and "🔍 Browse Explore Dex".

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

### 5.4 Identify (10-Step Observation Workflow)
1. **Upload:** Clean file drag-and-drop supporting JPG, JPEG, PNG, WebP up to 8 MB.
2. **Preview:** In-memory image preview.
3. **Privacy Notice:** Transparent declaration that EXIF location/camera tags are stripped and original images are never stored.
4. **Analyse Action:** Progress state with natural history spinner.
5. **Visible Traits:** Itemized morphological evidence observed by Meta Muse Spark.
6. **Candidate Proposals:** Primary candidate binomial with uncertainty notes and lookalikes.
7. **GBIF Reconciliation:** Authoritative taxonomic match with CC BY 4.0 citation and match type warnings (`HIGHERRANK`, `FUZZY`).
8. **Save to My Dex:** Automatic or manual collection update.
9. **Record Field Notes:** Naturalist field notes input (habitat, behavior, coarse locality).
10. **Export Record:** Structured JSON export with complete provenance.

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

- **`.specimen-card`:** Botanical card container with `--paper` background, `--border` outline, gentle box shadow, and hover elevation.
- **`.latin-binomial`:** Italicized serif typography for valid scientific names.
- **`.rank-pill`:** Small rounded badge in `--sage` with dark green text.
- **`.status-pill`:** High-contrast rounded pill indicating moderation state.
- **`.provenance-tag`:** Monospace citation badge highlighting licensing (`CC BY 4.0`) and origin.
- **`.security-notice`:** Mandatory local prototype security disclaimer.

---

## 7. Responsive Behavior & Accessibility
- **Fluid Layouts:** Uses Streamlit `layout="wide"` with responsive column distribution (`st.columns([1, 1])` or `st.columns([2, 1])`).
- **Contrast Ratios:** Text color `--ink` (`#252C27`) against `--paper` (`#FCFAF4`) yields contrast ratio $> 11:1$ (exceeding WCAG AAA).
- **No Horizontal Scroll:** Images use `width="stretch"` to adapt fluidly to laptop and desktop screens without overflow.
