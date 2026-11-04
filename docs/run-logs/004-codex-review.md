# Run Log 004 — Focused Engineering Review

## 1. Run Metadata
- **Run number:** 004
- **Agent/Model:** Gemini in Antigravity (acting as reviewer)
- **Date and time:** 2026-11-04T23:20:00+05:30
- **Task:** RUN 004 — Focused Engineering Review
- **Branch:** main

## 2. Objective
Review the current Vivédex MVP codebase focusing strictly on correctness and security risks in the image-to-taxonomy workflow. Check all 12 checklist items: Meta API request alignment with verified API notes, image payload format, credential security, image type/size validation, in-memory EXIF stripping, separation of model proposal from GBIF match, GBIF score presentation, handling of higher-rank/fuzzy/missing matches, actionable error reporting, JSON export cleanliness, and expert disclaimer notices. Fix only critical/high-priority defects without architectural redesign or scope expansion.

## 3. Work Completed
1. Inspected `docs/MVP_SPEC.md`, `docs/API_NOTES.md`, `src/image_processor.py`, `src/schemas.py`, `src/meta_adapter.py`, `src/gbif_adapter.py`, `src/backend.py`, `app.py`, and `tests/`.
2. Evaluated all 12 review checklist items:
   - **Item 1 (Meta API request):** PASS. Uses verified endpoint `POST https://api.meta.ai/v1/chat/completions` and model `muse-spark-1.3`.
   - **Item 2 (Image payload format):** PASS. Uses Base64 data URL (`data:{mime};base64,...`) in `user` content array.
   - **Item 3 (Credential protection):** PASS. `MODEL_API_KEY` is checked in memory and never logged, printed, or rendered in exceptions or JSON exports.
   - **Item 4 (Image size and type validation):** PASS. Validates JPG, JPEG, PNG, WebP up to 8 MB; rejects corrupted files.
   - **Item 5 (EXIF removal):** PASS. Corrects EXIF orientation, strips all metadata, and keeps processing purely in memory.
   - **Item 6 (Model proposal vs GBIF match separation):** PASS. Stored in distinct fields (`ai_candidate` vs `taxonomic_resolution`).
   - **Item 7 (GBIF match score distinction):** PASS. Clearly labeled as `(name string match metric)` and never confused with image identification confidence.
   - **Item 8 (Higher-rank and fuzzy match labeling):** HIGH finding resolved. Added explicit notification banners in `app.py` for `HIGHERRANK` (or non-species ranks) and `FUZZY` matches so users are informed that a match is not a species-level confirmation.
   - **Item 9 (Missing match handling):** PASS. Unmatched queries set `match_type: NONE` without fabricating a taxon, preserving the model candidate.
   - **Item 10 (Actionable error messages):** PASS. Specific banners for `ImageValidationError`, `MetaAPIConfigurationError`, `MetaAPIRequestError`, and GBIF connectivity errors.
   - **Item 11 (Clean JSON export):** PASS. Exported observation record contains only taxonomic and provenance data with zero credentials or personal identifiers.
   - **Item 12 (Expert disclaimer):** PASS. Prominently displayed in UI (`⚠️ AI-generated candidate. Not expert-verified.`) and inside exported JSON records.
3. Updated `app.py` to add explicit distinction warnings for `HIGHERRANK` and `FUZZY` matches.
4. Ran all unit and UI integration tests (`pytest`). 19 of 19 tests passed.

## 4. Files Created
- `docs/run-logs/004-codex-review.md`

## 5. Files Updated
- `app.py` (added explicit higher-rank and fuzzy match UI callouts)

## 6. Files Deleted
None.

## 7. Tests and Commands Run
- `py -m pytest -v`

## 8. Test Results
- All 19 tests passed (19/19 PASS).

## 9. Review Findings by Severity
- **FINDING 1 (HIGH — Fixed):** Higher-rank and fuzzy matches previously displayed the returned rank, but did not show an explicit contextual warning banner clarifying that the match was at a higher rank or via fuzzy matching.
  *Fix:* Added informative alert callouts in `app.py` when `match_type == "HIGHERRANK"` (or non-species rank) and when `match_type == "FUZZY"`.
- **FINDING 2 (LOW — Not fixed):** In `src/meta_adapter.py`, `HTTPError` responses include `e.read().decode("utf-8")` in the exception message for debugging. Since Meta returns JSON error bodies without echo of secrets, this is low risk; retained to ensure actionable debugging without adding unnecessary filtering dependencies.

## 10. Scope Check
- Confirmed: The review stayed strictly within scope. Only one minimal high-priority correctness fix was applied to `app.py`. No architecture redesign, no new dependencies, and no new features were added.

## 11. Next Action
Proceed to RUN 005 — Final QA and verification (`docs/run-logs/005-gemini-final-qa.md`).
