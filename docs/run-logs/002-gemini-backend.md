# Run Log 002 — Core Backend

## 1. Run Metadata
- **Run number:** 002
- **Agent/Model:** Gemini in Antigravity
- **Date and time:** 2026-11-04T23:01:00+05:30
- **Task:** RUN 002 — Core Backend Implementation
- **Branch:** main

## 2. Objective
Implement the Vivedex backend for the MVP defined in `docs/MVP_SPEC.md` using Python. Keep implementation small and modular. Provide image validation, in-memory EXIF stripping, Meta Model API adapter using verified endpoints and schemas, GBIF Species Match adapter, consolidated separate result schemas, JSON serialization, and comprehensive mocked unit tests. If Meta API key is missing, return a clear configuration error. Do not build UI or add databases.

## 3. Work Completed
1. Read `docs/API_NOTES.md`, `docs/MVP_SPEC.md`, and universal project instructions.
2. Implemented `src/image_processor.py`:
   - Validates image types: JPG, JPEG, PNG, WebP.
   - Enforces 8 MB size limit.
   - Verifies image integrity using Pillow.
   - Strips EXIF metadata and normalizes image orientation entirely in memory without writing to disk.
3. Implemented `src/schemas.py`:
   - Defined `CandidateIdentification` and `ModelIdentificationResult` with fields: `model`, `observation_summary`, `candidates` (`common_name`, `scientific_name`, `suggested_rank`, `visual_evidence`, `lookalikes`, `uncertainty_note`), and `limitations`.
   - Explicitly excluded invented numeric probabilities.
   - Defined `GBIFMatchResult` preserving `query_name`, `matched_scientific_name`, `canonical_name`, `rank`, `status`, `match_type`, `gbif_match_score` (confidence), `usage_key`, `hierarchy`, `source_url`, `retrieved_at`, and `licence`.
   - Defined `VivedexResult` consolidating AI candidate and GBIF taxonomic match while strictly keeping them in separate attributes. Added `to_json` serialization.
4. Implemented `src/meta_adapter.py`:
   - Integrated Meta Model API (`POST https://api.meta.ai/v1/chat/completions`) using model `muse-spark-1.3`.
   - Formatted images as Base64 data URLs in a multimodal `user` content array.
   - Added system instruction demanding structured JSON with candidate taxonomic attributes.
   - Enforced credential check: Raises `MetaAPIConfigurationError` when `MODEL_API_KEY` is missing without attempting a network call or returning a fake live result.
5. Implemented `src/gbif_adapter.py`:
   - Integrated GBIF Species Name Match API (`GET https://api.gbif.org/v1/species/match`).
   - Reconciles candidate scientific name, extracts usageKey, classification hierarchy, match type, and status, and attaches CC0 attribution and source link (`https://www.gbif.org/species/<usageKey>`).
6. Implemented `src/backend.py`:
   - `VivedexBackend.process_observation`: Coordinates validation, in-memory preprocessing, Meta API identification, GBIF resolution, and consolidated JSON serialization.
7. Implemented `src/__init__.py`:
   - Clean exports for the package.
8. Implemented `tests/test_backend.py`:
   - 16 comprehensive unit tests covering format validation, size boundary checks, corrupted file handling, EXIF stripping, schema parsing and JSON serialization, Meta API authentication checking and response parsing, GBIF response mapping, and mocked end-to-end pipeline execution.
9. Ran all unit tests and verified 100% pass rate.

## 4. Files Created
- `src/image_processor.py`
- `src/schemas.py`
- `src/meta_adapter.py`
- `src/gbif_adapter.py`
- `src/backend.py`
- `src/__init__.py`
- `tests/test_backend.py`
- `docs/run-logs/002-gemini-backend.md`

## 5. Files Updated
None.

## 6. Files Deleted
None.

## 7. Tests and Commands Run
1. `py -m unittest discover -s tests -p "test_*.py" -v`
2. `py -m pytest -v`

## 8. Test Results
- `test_corrupted_bytes`: PASS
- `test_empty_bytes`: PASS
- `test_preprocess_strips_metadata`: PASS
- `test_size_exceeded`: PASS
- `test_unsupported_mime`: PASS
- `test_valid_jpeg`: PASS
- `test_valid_png`: PASS
- `test_valid_webp`: PASS
- `test_model_result_schema`: PASS
- `test_gbif_schema_and_vivedex_consolidation`: PASS
- `test_missing_api_key_raises_configuration_error`: PASS
- `test_successful_meta_call`: PASS
- `test_meta_call_markdown_code_fence_cleaning`: PASS
- `test_gbif_empty_name`: PASS
- `test_gbif_match_success`: PASS
- `test_full_pipeline_mocked`: PASS

All 16 tests passed in 0.36s (unittest) and 4.07s (pytest).

## 9. Known Issues and Blockers
- None for the backend code. Live Meta Model API calls continue to require setting `MODEL_API_KEY` in the environment; the adapter raises an explicit `MetaAPIConfigurationError` if invoked without a key.

## 10. Scope Check
- Confirmed: The run stayed strictly inside the agreed scope. No Streamlit UI was built, no database was introduced, and no deployment files were created.

## 11. Next Action
Proceed to RUN 003 — UI implementation (`docs/run-logs/003-gemini-ui.md`).
