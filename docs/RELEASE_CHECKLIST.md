# Vivédex Release & Submission Checklist

**Project:** Vivédex  
**Repository:** https://github.com/rpxgit/vivedex  
**Status:** Pre-submission Final Audit  

---

## 1. Product & Functional Checks
- [x] **Image Upload:** Uploads JPG, JPEG, PNG, and WebP images up to 8 MB.
- [x] **Meta Model API Integration:** Uses `muse-spark-1.3` with structured JSON schema (`model`, `observation_summary`, `candidates`, `visual_evidence`, `lookalikes`, `uncertainty_note`, `limitations`).
- [x] **GBIF Taxonomic Match:** Reconciles candidate scientific name with GBIF Backbone Taxonomy (`v1/species/match`).
- [x] **Separation of Results:** AI candidate identification and GBIF taxonomic match are stored and displayed in separate cards.
- [x] **Score Clarity:** GBIF match score is explicitly labeled as a name-string matching metric, never confused with model identification confidence.
- [x] **Uncertainty & Non-Expert Warnings:** Visible banner `⚠️ AI-generated candidate. Not expert-verified.` rendered in UI and embedded in all exports.
- [x] **JSON Export:** Download button generates clean, structured JSON reports with full provenance.
- [x] **Error States Handled:** Handled gracefully for missing keys, network timeouts, invalid images, model parsing errors, and GBIF missing matches.
- [x] **Demo Fixture Mode:** Clearly labeled as `DEMO FIXTURE — NOT A LIVE MODEL RESULT` when `MODEL_API_KEY` is not present.

---

## 2. Privacy, Licensing & Security Checks
- [x] **No Secrets in Repository:** Confirmed no API keys, tokens, or credentials exist in git tracking or source files.
- [x] **No Local `.env` Tracked:** `.env.example` contains only safe placeholder names; `.env` is absent from git.
- [x] **In-Memory Image Handling:** Uploaded images are never saved to disk; processed strictly in memory.
- [x] **EXIF Stripping:** Camera EXIF tags and geolocation coordinates are stripped before transmission.
- [x] **Data Licensing Compliance:** Aligned with `Vivédex Data Licensing and Provenance Policy.md`; CC0 GBIF backbone license and provider URLs preserved.
- [x] **Sensitive Species Protection:** No GPS coordinates or sensitive geographic locations collected or exposed.

---

## 3. Repository & Build Checks
- [x] **README Documentation:** Comprehensive README with purpose, features, architecture, installation, configuration, testing, and privacy notes.
- [x] **Single-Command Launch:** Verified `streamlit run app.py` (or `py -m streamlit run app.py`).
- [x] **Minimal Dependencies:** `requirements.txt` contains only required libraries (`streamlit`, `pydantic`, `pillow`, `httpx`, `pytest`).
- [x] **Automated Tests:** 19/19 tests passing across backend processing, schemas, error states, and UI AppTest simulations.
- [x] **Run Logs Complete:** All five mandatory run logs exist in `docs/run-logs/` (001 through 005).

---

## 4. Demo & Submission Readiness
- [x] **3-Minute Demo Script:** Script documented in `docs/DEMO_SCRIPT.md` covering problem, upload, privacy, Meta AI analysis, GBIF verification, and JSON export.
- [x] **Accuracy of Claims:** Live Meta Model API is documented accurately; Demo Fixture mode is prominently labeled.
- [x] **Public Git Readiness:** Clean repository structure ready for public inspection.

