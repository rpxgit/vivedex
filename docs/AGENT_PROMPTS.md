# Agent Prompts
# Vivedex Hackathon Build — Agent Prompt Pack

**Use:** Copy one prompt per agent run. Run the prompts in order. Do not run agents in parallel.

**Language standard:** ASD-STE100-style English. Use short sentences. Use the same name for the same item. Use active voice. Give one instruction per sentence. Define technical terms when needed. Avoid idioms, vague terms, and long compound sentences.

**Current target:** A small, working biodiversity identification prototype. The user uploads an organism image. Meta's model analyses the image. GBIF checks the proposed scientific name. Vivedex displays a candidate result with taxonomy and source details.

**Time limit:** Six hours for the build. One more hour for the three-minute demo and recording.

**Repository:** `https://github.com/rpxgit/vivedex`

**Setup before Run 001:** Copy this file into the repository as `docs/AGENT_PROMPTS.md`. Then paste one run prompt into the assigned agent. The agent must read `docs/AGENT_PROMPTS.md` before it starts. Do not start more than one run at a time.

## Fixed decisions

- Use Python.
- Use Streamlit unless the repository already contains a working user interface that is faster to keep.
- Use Meta Model API for image analysis. Verify the current official API endpoint, model identifier, image format, and authentication method before implementation. Do not guess these values.
- Use the GBIF Species API for taxonomic name matching. Use the documented endpoint. Keep the GBIF match score separate from any model assessment.
- Use Pydantic for response validation only if it is already installed or can be added with low effort.
- Use local session state. Do not add user accounts or a database.
- Do not store uploaded images after the request. Remove image metadata before transmission when feasible.
- Treat every AI identification as a candidate. Do not describe it as a confirmed identification.
- Keep the original scientific name proposed by the model. Keep the GBIF matched name in a separate field.
- Preserve source URLs, identifiers, retrieval times, and licence information when available.
- Do not assume that public data or media is free to reuse.

## Scope lock

### Must work

1. Upload one JPG, JPEG, PNG, or WebP image.
2. Send the image to the Meta model API.
3. Receive a proposed scientific name and visible-trait notes.
4. Match the proposed name against GBIF.
5. Display the model proposal and GBIF match as separate results.
6. Display the taxonomic rank, taxonomic status, GBIF match type, GBIF match score, and GBIF source link when GBIF returns them.
7. Display a clear warning that the result is not expert-verified.
8. Export one JSON report.
9. Show a useful error when an API key, network connection, model response, or taxonomy match is missing.

### Do not build

- User accounts or authentication.
- Social features or community observations.
- Maps or geolocation.
- Population estimates or distribution analysis.
- Conservation-status prediction.
- Knowledge graphs or vector databases.
- Model training or fine-tuning.
- Multiple image uploads or batch processing.
- A mobile application.
- A new deployment platform unless local execution is already stable.
- Extra APIs that are not required for the core workflow.

## Run log rule — mandatory for every run

At the end of every agent run, create one new Markdown file in `docs/run-logs/`.

Use this file-name pattern:

`NNN-agent-task.md`

Examples:

- `001-gemini-preflight.md`
- `002-gemini-backend.md`
- `003-gemini-ui.md`
- `004-codex-review.md`
- `005-gemini-final-qa.md`

Before you select the number, inspect `docs/run-logs/` and use the next unused number. Do not overwrite an earlier log. Do not edit an earlier log to record a new run.

Each log must contain these headings:

1. Run metadata: run number, agent/model, date and time, task, branch.
2. Objective.
3. Work completed.
4. Files created.
5. Files updated.
6. Files deleted, or `None`.
7. Tests and commands run.
8. Test results: `PASS`, `FAIL`, or `NOT RUN` for each test.
9. Known issues and blockers.
10. Scope check: confirm whether the run stayed inside the agreed scope.
11. Next action.

Do not include API keys, passwords, tokens, private user data, or image contents in the log.
Do not claim that a test passed unless you ran it and observed a successful result.
If the run cannot complete, create the log with the work completed and the reason for the stop.
Before you finish, verify that the Markdown log exists at the expected path.

## Universal instructions for every agent run

Follow these rules for every task:

- Read this prompt pack and the relevant project files before you edit code.
- Read `Vivédex Data Licensing and Provenance Policy.md` before you handle external data or media.
- Read `SECURITY.md` before you handle uploads, secrets, or API requests.
- Check `git status --short` before you edit files.
- Preserve existing user changes. Do not reset, clean, rebase, or force-push.
- Do not change the software licence or data policy.
- Do not print or copy secret values. Check only whether a required environment variable exists.
- Do not invent API routes, model names, request formats, response fields, or licence terms.
- Verify external API details from official documentation. Record the documentation URL in the run log.
- Do not add a new dependency unless it is required. Explain every new dependency in the run log.
- Do not modify files owned by another run unless the task requires it. State the reason in the log.
- Do not add features outside the scope lock.
- Do not commit or push unless the user asks you to do so.
- Use clear type names and small functions.
- Add useful error messages. Do not hide an API failure behind a fake result.
- Keep demo or fixture mode clearly labelled. Never present fixture output as a live Meta result.
- Run the smallest relevant tests. Report tests that you did not run.
- At the end, create and verify the required Markdown run log.

---

# RUN 001 — Repository and API preflight

**Model:** Gemini in Antigravity.

**Why:** Gemini handles repository reconnaissance and broad planning. Do not spend the limited Codex allowance on this task.

**Prompt:**

You are the technical lead for the Vivedex hackathon MVP.

Perform a short repository and API preflight. Do not build the application in this run.

1. Inspect the repository structure and the current Git status.
2. Read the README, the data licensing policy, and SECURITY.md.
3. Check whether the repository already contains an application or dependency file.
4. Recommend the smallest implementation that fits the current repository.
5. Verify the current Meta Model API documentation. Confirm the supported model identifier, base URL, authentication method, image input format, and required request structure. Use official Meta documentation only.
6. Check whether the required Meta API key variable exists. Do not print its value.
7. Check the documented GBIF species name-match endpoint. Confirm the request parameters and response fields that the MVP needs.
8. Perform a small GBIF connectivity check if network access is available. Use a common scientific name such as `Passer domesticus`.
9. Do not make a live Meta request unless an API key is already configured. Do not ask the user to paste a secret into chat.
10. Create `docs/MVP_SPEC.md`. Record the fixed MVP workflow, data contract, failure states, and excluded features.
11. Create `docs/API_NOTES.md`. Record official documentation URLs and verified API details. Mark every unverified detail as `UNVERIFIED`.
12. Do not create application code in this run.
13. Create the required run log. Use the next unused run number.

Time limit: 20 minutes.

Stop when the specification and preflight report are complete. Do not add new features. Report any blocker that prevents a live Meta API call.

---

# RUN 002 — Core backend

**Model:** Gemini in Antigravity.

**Why:** Use Gemini for the main implementation. Keep the work limited to the backend contract and service modules.

**Prompt:**

Implement the Vivedex backend for the MVP defined in `docs/MVP_SPEC.md`.

Before you edit code, read `docs/API_NOTES.md` and the universal instructions in this prompt pack.

Use Python. Keep the implementation small.

Implement only these parts:

1. Image validation for JPG, JPEG, PNG, and WebP.
2. Image size validation. Use a clear maximum size of 8 MB.
3. Image preprocessing. Remove EXIF metadata when feasible. Do not save the image to permanent storage.
4. A Meta API adapter. Use only the endpoint, model identifier, and request format verified in `docs/API_NOTES.md`.
5. A strict response schema for the model result.
6. A GBIF adapter. Use the documented name-match endpoint.
7. A result schema that stores the model proposal and GBIF match in separate fields.
8. JSON serialization for the final result.
9. Unit tests for validation, response parsing, GBIF matching, and error handling. Mock external API calls in unit tests.

The model output must contain:

- A proposed scientific name, if the model can provide one.
- Visible traits that support the proposal.
- Alternative candidate names, when available.
- A short explanation of uncertainty and possible confusion.
- A clear statement that the output is an AI-generated candidate.

Do not ask the model to invent a numeric probability. Do not treat the GBIF match score as image-identification confidence.

The GBIF result must preserve these fields when returned:

- Matched scientific name.
- Canonical name.
- Taxonomic rank.
- Taxonomic status.
- Match type.
- GBIF match score or confidence field.
- GBIF usage key.
- GBIF source URL.
- Retrieval time.

Keep the original model-proposed name. Do not overwrite it with the GBIF name.

If the Meta API key is missing, return a clear configuration error. Do not return a fake live result.

Do not build the Streamlit interface in this run. Do not add a database. Do not add deployment files.

Run the backend tests. Record the exact commands and results.

Create and verify the required Markdown run log before you finish.

---

# RUN 003 — User interface

**Model:** Gemini in Antigravity.

**Why:** Gemini handles the UI and the connection to the backend. The backend files are already defined.

**Prompt:**

Build the Vivedex Streamlit interface for the existing backend.

Read `docs/MVP_SPEC.md`, `docs/API_NOTES.md`, and the current backend code first.

Do not rewrite the backend unless a small interface fix is required. Record any required backend change in the run log.

The interface must contain these screens or sections:

1. A clear Vivedex title and one-sentence purpose.
2. One image upload control.
3. A short privacy note. State that the image is processed for analysis and is not stored by the MVP.
4. An `Analyse image` action.
5. A progress state while the APIs run.
6. A species result card.
7. A visible evidence section for the traits reported by the model.
8. A separate taxonomy section for the GBIF result.
9. A visible warning: `AI-generated candidate. Not expert-verified.`
10. A JSON download action.
11. Useful error messages for missing keys, network failures, invalid images, model errors, and missing GBIF matches.

Use a clean, readable layout. Do not spend time on decorative animation or custom visual effects.

Do not add maps, login, a database, a community feed, batch uploads, or a new API.

Do not show a numeric image-confidence score unless the model explicitly returns one and the UI labels it as a model-reported score. Do not confuse that score with the GBIF taxonomy match score.

Add a sample fixture only if it helps test the interface without API access. Label fixture results clearly as `DEMO FIXTURE — NOT A LIVE MODEL RESULT`.

Make the application start with one documented command. Add or update the dependency file only when needed.

Run the application or the available UI tests. Report any part that you could not test.

Create and verify the required Markdown run log before you finish.

---

# RUN 004 — Focused engineering review

**Model:** Codex (GPT; limited Astra allowance).

**Why:** Use one Codex run for a narrow review of high-risk code. Do not use Codex for broad planning, UI design, or routine documentation.

**Prompt:**

Review the current Vivedex MVP. Focus only on correctness and security risks in the image-to-taxonomy workflow.

Read `docs/MVP_SPEC.md`, `docs/API_NOTES.md`, the backend modules, and the tests.

Do not redesign the architecture. Do not add features. Do not reformat unrelated files.

Check these items:

1. The Meta API request matches the official API notes.
2. The image payload uses the documented format.
3. API keys do not appear in logs, errors, source files, or the UI.
4. Uploaded image size and type are validated.
5. Image metadata is removed before external transmission when feasible.
6. The model proposal and GBIF match remain separate.
7. The GBIF match score is not shown as model confidence.
8. A higher-rank or fuzzy GBIF match is not described as an exact species match.
9. A missing match does not create a false species result.
10. API errors are visible and actionable.
11. JSON export does not include secrets or unnecessary personal data.
12. The result states that the identification is not expert-verified.

Fix only critical or high-priority defects. Limit code changes to the smallest necessary set. If there are no such defects, make no code changes.

Run the relevant tests. Report each finding as `CRITICAL`, `HIGH`, `MEDIUM`, or `LOW`. Explain any finding that you did not fix.

Do not spend time on style changes. Do not add dependencies unless a security defect requires one.

Create and verify the required Markdown run log before you finish. Keep the log concise.

---

# RUN 005 — Integration test and release preparation

**Model:** Gemini in Antigravity.

**Why:** Gemini handles the final integration, documentation, and demo preparation. Keep Codex available only if a new critical defect appears.

**Prompt:**

Prepare the current Vivedex MVP for the hackathon submission.

Read all existing run logs first. Review the current Git status. Do not discard existing changes.

Perform these tasks in order:

1. Run the backend unit tests.
2. Run the application locally.
3. Test the complete image upload, Meta analysis, GBIF match, result display, and JSON export workflow if the API key is configured.
4. Test the missing-key and no-match failure states.
5. Confirm that fixture output is clearly labelled and is never presented as a live Meta result.
6. Fix only defects that block the MVP workflow.
7. Update the README with the project purpose, features, architecture, installation, configuration, run command, testing, data sources, limitations, and privacy notes.
8. Update `.env.example` with variable names and safe placeholder values only. Do not include real secrets.
9. Add a short `docs/DEMO_SCRIPT.md` for a three-minute recording.
10. Add a `docs/RELEASE_CHECKLIST.md` with repository, demo, API, privacy, and submission checks.
11. Confirm that the data licensing policy still matches the implementation.
12. Confirm that the public repository contains no API keys or local environment files.
13. Do not add features.
14. Do not deploy unless the local workflow is stable and deployment takes less than 15 minutes.

The three-minute demo script must show:

- The problem and Vivedex purpose.
- An image upload.
- A real Meta model analysis, if API access is configured.
- The GBIF taxonomy match.
- The difference between the AI candidate and the taxonomy reference.
- The provenance details and uncertainty warning.
- The JSON export.

If live Meta access is not configured, do not claim that the demo uses a live Meta model. Record the blocker. Use a labelled fixture only to show the UI layout.

Run the relevant tests. Record exact commands and outcomes.

Create and verify the required Markdown run log before you finish.

---

# Final manual checklist

## Product

- [ ] The image upload works.
- [ ] The Meta API returns a real result.
- [ ] The output includes visible traits.
- [ ] GBIF returns a taxonomic match or a clear no-match result.
- [ ] The interface keeps the AI proposal separate from the GBIF match.
- [ ] The interface shows the uncertainty warning.
- [ ] The JSON export works.
- [ ] The error states work.

## Privacy and licensing

- [ ] No API key is in Git.
- [ ] No `.env` file is in Git.
- [ ] Uploaded images are not stored after analysis.
- [ ] Image metadata is removed when feasible.
- [ ] Every external data source has a source URL.
- [ ] No unlicensed image is bundled in the repository.
- [ ] No precise sensitive wildlife location is exposed.
- [ ] AI results are not presented as expert-confirmed facts.

## Repository

- [ ] README has setup instructions.
- [ ] `.env.example` has safe placeholders.
- [ ] Tests run successfully.
- [ ] The repository is public.
- [ ] The latest changes are pushed.
- [ ] All five run logs exist, including logs for any run that stopped early.

## Demo and submission

- [ ] The demo is no longer than three minutes.
- [ ] The recording shows the actual application.
- [ ] The recording does not show API keys or personal data.
- [ ] The GitHub URL opens in a private browser window.
- [ ] The video URL works in a private browser window.
- [ ] The submission describes only features that work.
- [ ] Meta usage is described accurately.
- [ ] Partner feedback is based on tools that were actually used.

