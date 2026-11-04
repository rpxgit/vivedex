# Technology Decision Record (TDR 001)

## Frontend Architecture Evaluation: Streamlit vs. Dedicated Frontend Migration

- **Date:** 2026-11-05
- **Status:** **APPROVED: Retain and Reconstruct Streamlit with Custom CSS Design System**
- **Decision Makers:** Lead Product Design Engineer & Frontend Architect

---

## 1. Context & Problem Statement
Vivédex requires a cohesive, visually distinctive user experience inspired by natural history museums, botanical field journals, Restor.eco, and classic Pokédex encyclopedias.
The existing MVP and platform prototype were implemented in **Streamlit 1.66.1** on Python 3.14.
We evaluated whether to migrate the frontend to a separate dedicated framework (React / TypeScript / Vite / Tailwind) or retain Streamlit and build an advanced design system layer using custom CSS tokens and component injection.

---

## 2. Options Considered

### Option A: Separate Dedicated Frontend (React / TypeScript + FastAPI / Flask Backend)
- **Architecture:** Node.js/Vite frontend communicating with a Python REST API.
- **Advantages:** Full DOM control, native component libraries (Radix, Tailwind), fine-grained client-side animations.
- **Disadvantages & Environmental Blockers:**
  1. **Host Environment Constraint:** Node.js, `npm`, and `pnpm` are **not installed** on the host environment (`CommandNotFoundException`). Installing Node.js violates the project's dependency lock.
  2. **Multi-Service Complexity:** Requires decoupling the single-process application into dual servers (Node frontend + Python API), adding build pipelines, CORS configuration, and process management.
  3. **Regression Risk:** Rewriting the frontend in a new framework risks breaking the verified 10-step image validation, EXIF metadata stripping, Meta Muse Spark integration, and GBIF reconciliation.
  4. **Time & Scope Cost:** Diverts focus from product polish and biodiversity storytelling into basic infrastructure plumbing.

### Option B: Retain Streamlit with a Dedicated Design System Layer (`src/ui/theme.py`)
- **Architecture:** Single-process Python 3.14 + Streamlit 1.66.1 leveraging Streamlit's multi-page navigation (`st.navigation`), injected Google Fonts (*Playfair Display*, *Cinzel*, *Plus Jakarta Sans*), CSS design tokens, custom specimen card HTML, and modular view controllers.
- **Advantages:**
  1. **Zero External Runtime Prerequisites:** Runs out-of-the-box on the verified Python 3.14 environment without Node.js.
  2. **Preserves Working Backend & DB:** All 42 automated tests, SQLite schema migrations, and security controls remain 100% operational.
  3. **Visual Flexibility:** Streamlit supports arbitrary CSS, custom typography, SVG icons, and HTML component cards via `st.markdown(..., unsafe_allow_html=True)`.
  4. **Rapid Iteration:** Allows immediate enhancement of all 8 main pages and the Admin Console without dual-process latency.
- **Disadvantages:**
  1. Client-side animations and deeply nested client-only state machines require careful structuring of `st.session_state`.
  2. Occasional page re-renders on widget interactions.

---

## 3. Decision
**We select Option B: Retain and reconstruct the Streamlit architecture.**
We will not migrate to React or Node.js merely for fashion.
Instead, we will build an editorial, natural-history-inspired design system directly within Python using:
1. `src/ui/theme.py`: Central repository of design tokens, editorial typography, specimen card builders, status pills, and custom CSS styling.
2. Modular page controllers across `src/ui/` that use these components to render a cohesive, museum-grade aesthetic.
3. Full preservation of the existing SQLite database, auth services, and Meta Muse Spark + GBIF identification adapters.

---

## 4. Consequences & Trade-offs
- **Positive:** Immediate visual elevation; zero build breaks; 100% test compatibility; zero new system dependencies; runs reliably on local Windows.
- **Negative:** Certain native micro-interactions (e.g. drag-and-drop reordering of cards) are constrained by Streamlit's server-driven execution model.
- **Mitigation:** We structure cards with clear button affordances, breadcrumb navigation, and tabbed inspection drawers to deliver an intuitive experience.
