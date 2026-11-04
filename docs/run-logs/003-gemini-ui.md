# Run Log 003 — User Interface

## 1. Run Metadata
- **Run number:** 003
- **Agent/Model:** Gemini in Antigravity
- **Date and time:** 2026-11-04T23:08:30+05:30
- **Task:** RUN 003 — User Interface Implementation
- **Branch:** main

## 2. Objective
Build the Vivédex Streamlit user interface connecting directly to the existing backend without rewriting backend modules. Implement the 11 required UI sections (title & purpose, image upload control, in-memory privacy notice, analyse action, progress state, species result card, visible traits evidence section, separate GBIF taxonomy section, prominent AI-candidate disclaimer, JSON download action, and comprehensive error feedback). Add a demo fixture for offline testing clearly labelled as `DEMO FIXTURE — NOT A LIVE MODEL RESULT`. Ensure single-command execution.

## 3. Work Completed
1. Inspected existing backend code (`src/backend.py`, `src/image_processor.py`, `src/schemas.py`, `src/meta_adapter.py`, `src/gbif_adapter.py`). No backend rewrites were required.
2. Installed `streamlit` (v1.66.1) to support UI execution.
3. Created `src/fixtures.py`:
   - Deterministic sample observation (`Passer domesticus`) with visible traits, lookalikes, uncertainty note, and exact GBIF match.
   - Distinctly labeled with `DEMO FIXTURE — NOT A LIVE MODEL RESULT`.
4. Created `app.py`:
   - Title: `🌿 Vivédex` and subheader purpose statement.
   - Privacy Notice: Informs users that images are processed in-memory, EXIF is stripped, and no images are stored permanently.
   - Environment check: Displays a banner if `MODEL_API_KEY` is not found, automatically offering Demo Fixture Mode.
   - File Uploader: Supports JPG, JPEG, PNG, WebP up to 8 MB.
   - Execution Button: `🔍 Analyse Image` triggering progress spinner and backend execution.
   - Results Presentation:
     - Prominent warning: `⚠️ AI-generated candidate. Not expert-verified.`
     - Candidate Identification Card: Model ID, observation summary, common name, scientific name, suggested rank.
     - Morphological Evidence: Bulleted visible evidence traits and lookalikes list.
     - Separate GBIF Taxonomy Card: Matched scientific name, canonical name, rank, status, match type, and GBIF match score (clearly annotated as a name-string matching metric, not an image probability).
     - GBIF metadata: Usage key, clickable link to GBIF species page, hierarchical taxonomy breadcrumb, and CC0 licence attribution.
   - JSON Export: One-click download button exporting `vivedex-observation-<timestamp>.json` with full provenance.
   - Error Handling: Specific, user-friendly alerts for `ImageValidationError`, `MetaAPIConfigurationError`, `MetaAPIRequestError`, and GBIF connectivity issues.
5. Created `requirements.txt`:
   - Minimal dependency file (`streamlit`, `pydantic`, `pillow`, `httpx`, `pytest`).
6. Created `tests/test_ui.py`:
   - Tests fixture generation, JSON serialization, and automated Streamlit app loading via `streamlit.testing.v1.AppTest`.
7. Executed all unit and UI integration tests (`pytest` and `unittest`).

## 4. Files Created
- `app.py`
- `src/fixtures.py`
- `requirements.txt`
- `tests/test_ui.py`
- `docs/run-logs/003-gemini-ui.md`

## 5. Files Updated
None (no backend files rewritten).

## 6. Files Deleted
None.

## 7. Tests and Commands Run
1. `py -m unittest discover -s tests -p "test_*.py" -v`
2. `py -m pytest -v`
3. `py -c "from streamlit.testing.v1 import AppTest; ..."` (Simulated Streamlit rendering test)

## 8. Test Results
- `test_corrupted_bytes`: PASS
- `test_empty_bytes`: PASS
- `test_preprocess_strips_metadata`: PASS
- `test_size_exceeded`: PASS
- `test_unsupported_mime`: PASS
- `test_valid_jpeg`: PASS
- `test_valid_png`: PASS
- `test_valid_webp`: PASS
- `test_gbif_schema_and_vivedex_consolidation`: PASS
- `test_model_result_schema`: PASS
- `test_meta_call_markdown_code_fence_cleaning`: PASS
- `test_missing_api_key_raises_configuration_error`: PASS
- `test_successful_meta_call`: PASS
- `test_gbif_empty_name`: PASS
- `test_gbif_match_success`: PASS
- `test_full_pipeline_mocked`: PASS
- `test_fixture_generation`: PASS
- `test_json_export_structure`: PASS
- `test_apptest_loads`: PASS

All 19 tests passed in 1.18s (unittest) and 3.30s (pytest).

## 9. Known Issues and Blockers
- **Live Meta Model API:** Remains blocked until the user sets `MODEL_API_KEY`. In the meantime, the UI provides the integrated Demo Fixture mode to demonstrate the complete user workflow.
- **Untested in headless CI:** Interactive browser clicking was simulated programmatically via `streamlit.testing.v1.AppTest`. Full browser rendering requires running `py -m streamlit run app.py` locally.

## 10. Scope Check
- Confirmed: The run stayed strictly inside the agreed scope. No maps, accounts, databases, or social features were added.

## 11. Next Action
Proceed to RUN 004 — Codex review (`docs/run-logs/004-codex-review.md`).
