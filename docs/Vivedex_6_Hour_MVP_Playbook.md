# Vivédex — 6-Hour MVP Build Playbook

**Hackathon:** Meta Global AI Developer Hackathon 2026  
**Project:** Vivédex  
**Repository:** https://github.com/rpxgit/vivedex  
**Owner / final integrator:** Radhey Patel  
**Build allowance:** 6 hours  
**Demo production allowance:** 1 hour  
**Submission deadline:** 4 November 2026, 9:00 PM ET = 5 November 2026, 02:00 UTC = 07:30 IST = 04:00 Bucharest time.

---

## 0. The one-sentence product

**Vivédex turns an organism photograph into a cautious, explainable candidate identification and a taxonomically resolved, provenance-backed species card.**

The MVP demonstrates one complete workflow:

1. A user uploads a photograph of an organism.
2. Meta Muse Spark analyses the image and returns one or more candidate identifications, visible evidence, lookalikes and uncertainty.
3. Vivédex checks the leading scientific-name candidate against GBIF's taxonomy API.
4. The application displays the model's candidate separately from GBIF's taxonomic match, with source links, match status and retrieval time.
5. The user can export a compact JSON report.

**Do not build a general biodiversity platform tonight. Build this vertical slice.**

## 1. Product rules that are already established in the repository

The existing repository contains a licence, a minimal README, `SECURITY.md`, and `Vivédex Data Licensing and Provenance Policy.md`. There is no existing application implementation to preserve.

The existing policy establishes these non-negotiable product principles:

- AI identifications are candidate results, not confirmed scientific facts.
- Preserve original source names and identifiers when normalizing taxonomy.
- Preserve source URL, provider, release/version where available, retrieval date, licence and attribution.
- A software licence does not automatically license biodiversity records, images, papers or model outputs.
- Do not redistribute data with missing or unclear rights.
- User contributions remain owned by their contributors; do not imply an open contribution licence without an affirmative consent flow.
- Protect sensitive species locations and contributor information.

**Do not delete or weaken either policy file or replace the project's Apache-2.0 code licence with a data licence.**

## 2. Hackathon positioning and verified requirements

The official event overview describes two tracks:

- **Indie Developer:** individual builders and students; creativity, technical ambition and whether it works.
- **Startup:** teams/founders building a real product; technical execution and production readiness.

It describes two themes:

- **Build for Your World:** bring Meta models into a domain you know and solve a real problem.
- **Push the Frontier:** use models to advance software, robotics, manufacturing, energy, materials and related areas.

**Recommended theme:** Build for Your World. Biodiversity knowledge discovery, verification and reuse is the authentic fit.

**Track decision:** Choose Indie Developer if this is your individual entry. Choose Startup only if you are submitting it as the startup/team product under the relevant event rules. The track is not the same thing as the project theme.

The submission form you showed requires: track, problem statement, optional X link for Most Viral, project description, public GitHub repository, 3-minute demo video, use of Meta products, why Meta models matter, and feedback on partner technologies.

Important distinction: the event overview names themes, not a complete list of selectable problem statements. In the portal, select the exact problem statement that most closely matches biodiversity knowledge discovery. Do not invent a problem-statement title or assume the theme itself is the required dropdown value.

The public event page confirms the deadline as **4 November 2026, 9:00 PM ET**. It states that selected participants must accept the official rules. The public waiver page is dynamically rendered, so this playbook is not a substitute for the detailed rules already made available in your participant portal. Review any accepted participant terms covering eligibility, IP, prize receipt, content permissions and submission requirements there.

## 3. Stack decision: Python, not Rust

Use **Python 3.11 + Streamlit** for the submission build.

| Concern | Choice | Reason |
|---|---|---|
| Language | Python 3.11 | Fast iteration and straightforward Meta API integration |
| UI | Streamlit | One-process interface; no separate frontend build |
| Meta client | OpenAI Python SDK pointed at Meta Model API | Meta documents OpenAI-compatible chat completions and image input |
| Model | `muse-spark-1.3` | Vision-capable model available through Meta Model API |
| Taxonomy | GBIF Species API | Independent taxonomic name resolution |
| Validation | Pydantic | Validate structured model output |
| HTTP | HTTPX | Simple timeout-aware GBIF requests |
| Persistence | Streamlit session state only | No database setup or migration during the hackathon |
| Export | JSON download | Reproducible result and provenance record |

Rust would add implementation and integration overhead without improving the visible six-hour workflow. Revisit Rust only if a future performance-critical parser or indexing engine justifies it.

### Minimal dependencies

- `streamlit`
- `openai`
- `httpx`
- `pydantic`
- `pillow`
- `python-dotenv` (optional; environment variables are sufficient)
- `pytest` (only if time permits)

Do not add LangChain, LlamaIndex, a vector database, Docker, Kubernetes, Redis, Celery, a separate frontend framework or cloud infrastructure unless the working slice is already complete.

## 4. Scope lock

### P0 — Must exist for a valid demo

- [ ] Streamlit app starts locally with one documented command.
- [ ] User can upload one JPG/JPEG/PNG/WebP photograph.
- [ ] Image is resized/compressed and EXIF metadata is stripped before transmission.
- [ ] A real request is sent to Meta Model API using `muse-spark-1.3`.
- [ ] Meta returns structured candidate name(s), visible traits, lookalikes and uncertainty.
- [ ] The leading scientific name is checked against GBIF Species Match API.
- [ ] UI separates **AI candidate identification** from **GBIF taxonomy match**.
- [ ] UI shows taxonomy rank, match type/status and a link to the GBIF taxon page when a match exists.
- [ ] UI states clearly that the result is an aid, not expert confirmation.
- [ ] User can download a JSON report with model, timestamp, candidate, taxonomic response and source links.
- [ ] API errors and no-match results are handled without crashing the app.
- [ ] `.env` and credentials are excluded from Git.

### P1 — Only after every P0 item works

- [ ] Show up to three candidate species, with the top candidate resolved through GBIF.
- [ ] Add a small session-only observation history.
- [ ] Add CSV export in addition to JSON.
- [ ] Add a second example observation or a deliberate ambiguous-image example.
- [ ] Improve visual polish, icons and loading states.

### Explicitly out of scope — do not build tonight

- [ ] User accounts, authentication or contributor profiles.
- [ ] Public observations, social feed, likes, comments or community moderation.
- [ ] Precise GPS, maps, habitat mapping or species-range maps.
- [ ] Population trends, conservation status, IUCN assessments or threat predictions.
- [ ] Bulk ingestion of GBIF/iNaturalist/Catalogue of Life datasets.
- [ ] A custom-trained image classifier or local GPU inference.
- [ ] SAM segmentation, video processing, audio recognition or camera-trap pipelines.
- [ ] Multi-agent architecture, RAG, embeddings, vector search or knowledge graph.
- [ ] Mobile app, desktop app, browser extension or multi-tenant deployment.
- [ ] Rust rewrite, microservices, CI/CD overhaul or elaborate test infrastructure.
- [ ] Claims of confirmed species identification or calibrated AI probabilities.

**Scope rule:** A new feature is rejected unless it is required to complete or stabilize the P0 workflow.

## 5. Required data contract

Keep the frontend and backend interface stable so two coding agents can work without overwriting each other.

### `identify_image(image_bytes: bytes, mime_type: str) -> dict`

Return:

```json
{
  "model": "muse-spark-1.3",
  "observation_summary": "Short description of visible subject and context",
  "candidates": [
    {
      "common_name": "Example common name or null",
      "scientific_name": "Genus species",
      "suggested_rank": "SPECIES",
      "visual_evidence": ["Visible trait one", "Visible trait two"],
      "lookalikes": ["Similar taxon"],
      "uncertainty_note": "What prevents a confident identification"
    }
  ],
  "limitations": "The result is a candidate, not expert confirmation."
}
```

Do not return invented numerical probabilities. If the model cannot distinguish the organism confidently, it should return a broader taxonomic rank or explicitly say it cannot identify it.

### `resolve_taxon(scientific_name: str) -> dict`

Return only fields actually supplied by GBIF, such as:

- `scientificName`
- `canonicalName`
- `rank`
- `status`
- `matchType`
- `confidence` (a taxonomic matching score, **not** an image-identification probability)
- `usageKey`
- available higher taxonomy fields
- `retrieved_at`
- `source_url`

If GBIF returns only a genus/family-level match, say that. Do not label it a species-level confirmation. If there is no match, display “Taxonomic match not resolved” and retain the AI candidate separately.

## 6. Meta Model API integration

Meta's current documentation describes the Model API at `https://api.meta.ai/v1`, Bearer-token authentication via `MODEL_API_KEY`, and OpenAI SDK compatibility. The image-understanding guide documents both public image URLs and inline base64 data URLs for chat completions.

Minimal client configuration:

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://api.meta.ai/v1",
    api_key=os.environ["MODEL_API_KEY"],
)
MODEL = "muse-spark-1.3"
```

For local uploads, send the image as a base64 data URL in an `image_url` content part. Use a `user` message for image content. Keep the image prompt strict and ask for JSON. Validate the returned structure before rendering it; retry once or show an explicit parse error rather than fabricating a result.

### Model instruction

> You are assisting with preliminary biodiversity observation triage. Analyse only visible features in the supplied photograph. Return a maximum of three plausible taxonomic candidates, ordered from most to least plausible. For each candidate provide a common name if known, scientific name, suggested taxonomic rank, two or three visible diagnostic traits, likely lookalikes and a concise uncertainty note. Do not infer precise location, habitat, conservation status, distribution, rarity or population from the photograph. Do not invent a probability or imply expert verification. If the image is inadequate or the taxon cannot be distinguished, state that and return the narrowest defensible rank rather than guessing. Return valid JSON only.

### First technical gate — do this before building the UI

Within the first 20 minutes:

- [ ] Confirm `MODEL_API_KEY` exists locally.
- [ ] Run one text-only test call to prove credentials and model availability.
- [ ] Run one image test call with a self-taken or properly licensed photo.
- [ ] Confirm response content can be parsed.

If the Meta endpoint/key is not working after 20 minutes, stop debugging the environment indefinitely. Check the official quickstart and account access, then use a supported hosted Meta model from an event inference partner only if you already have working credentials. Never describe an untested integration as implemented.

## 7. GBIF taxonomy integration

Use the GBIF Species API name-match service for the candidate scientific name. Pass the name as a URL-encoded parameter and set a short timeout. Preserve the raw response fields needed to explain the match. GBIF's current API default has moved to the Catalogue of Life eXtended Release (COL XR); its technical documentation notes that the older GBIF Backbone remains available for backward compatibility but is no longer updated. Do not label a result as the old Backbone unless you explicitly requested that checklist.

The GBIF result is a taxonomic name match, not proof that the organism in the uploaded image is that species and not evidence that the species occurs at the user's location. Preserve the exact source/checklist metadata and licence that apply to the returned dataset; do not assume every GBIF-mediated record has the same licence.

Display:

- Candidate name from Muse Spark.
- GBIF accepted/canonical name when available.
- GBIF rank and status.
- GBIF match type and match score, labelled as a **taxonomy match score**.
- GBIF taxon-page link using the returned usage key.
- Retrieval timestamp and provider/source attribution.

Do not add occurrence counts, maps, range or conservation claims in this MVP. GBIF itself states that data accessed through its services is not guaranteed to be accurate; preserve the source trail and avoid overstating authority.

## 8. Privacy, security and licensing gates

- [ ] Never commit `.env`, API keys, access tokens or local secrets.
- [ ] Add `.env`, `.venv`, `__pycache__`, generated uploads and local database files to `.gitignore`.
- [ ] Strip EXIF metadata before sending user images to the model; EXIF can contain location and device details.
- [ ] Do not request or store precise GPS coordinates.
- [ ] Do not persist uploaded photographs in the MVP unless absolutely necessary; session-only handling is preferred.
- [ ] Use a self-taken demo photograph or a photograph whose media licence is verified and compatible.
- [ ] Do not scrape/re-host images from species pages or copy photographs from iNaturalist/GBIF without checking the individual media licence.
- [ ] Keep AI identifications visibly labelled as candidates.
- [ ] Retain source URLs, match status and retrieval timestamps.
- [ ] Do not claim GBIF has verified the image; it only resolves a taxonomic name.
- [ ] Avoid exposing sensitive locations of rare/threatened organisms.
- [ ] Preserve the existing data licensing/provenance policy and security policy.

## 9. Agent workflow — Gemini + Codex without file collisions

**You are the project lead and integration owner.** Use the agents for bounded implementation tasks, not open-ended product design.

Before agents edit:

1. Create a working branch, e.g. `hackathon-mvp`.
2. Give both agents the one-sentence product, P0 list, out-of-scope list and the data contract above.
3. Tell each agent exactly which files it may edit.
4. Do not let both agents edit the same file. Do not let either agent change the licence or policy files.

### Codex / GPT — backend owner

Permitted files: `vivedex/core.py`, `vivedex/gbif.py`, `vivedex/schemas.py`, `tests/`.

Task: implement image preprocessing, Muse Spark image call, JSON parsing/validation and GBIF name resolution. Strip image EXIF metadata before the Meta call. Apply HTTP timeouts and readable errors. Do not build UI, alter README, add a database or expand the feature set. Add minimal tests for malformed model output, GBIF no-match and GBIF timeout. Return exact function signatures and a short integration note.

### Gemini / Antigravity — frontend owner

Permitted files: `app.py`, `assets/` (only if needed).

Task: build a polished, compact Streamlit interface for the existing data contract. Include image upload, preview, one “Analyse observation” action, candidate card, GBIF taxonomy panel, provenance/uncertainty panel and JSON download. Import `identify_image` and `resolve_taxon` from the agreed backend module. Do not mock successful results in the real path, do not create a competing backend, do not edit README/dependencies/policy files, and do not add out-of-scope features. If the backend is not ready, use a clearly labelled temporary stub only for layout, then remove it before submission.

### You — integration owner

- Own `requirements.txt`, `.env.example`, `.gitignore`, README and the final app run.
- Review all agent diffs before accepting them.
- Resolve interface mismatches yourself; do not ask both agents to rewrite the same module.
- Run the app from a clean terminal and test the exact demo sequence.
- Commit a stable version before beginning video recording.

### Prompt header to paste into BOTH coding agents

> This is a six-hour hackathon MVP. Do not redesign the product. Do not add features beyond the written P0 list. Read README, SECURITY.md and the data licensing/provenance policy first. Preserve those files and the Apache-2.0 licence. Make only the edits in your assigned files. Do not invent data, model capabilities, test results, citations or licences. Do not silently change public function signatures. If blocked, report the blocker and the smallest viable fix. Prefer boring, working code over abstraction. Ask before modifying a file outside your assigned list.

## 10. Six-hour build schedule

| Elapsed | Time box | Deliverable | Stop condition |
|---|---|---|---|
| 00:00–00:20 | API gate | Meta text + image test calls work | Credentials and image call proven; otherwise switch to access troubleshooting/fallback |
| 00:20–01:25 | Core model path | Image preprocessing + candidate JSON | One real image produces validated output |
| 01:25–02:10 | Taxonomy | GBIF name match + source link | Candidate resolves or graceful no-match path works |
| 02:10–03:25 | UI | Upload → analyse → card | Complete end-to-end path visible |
| 03:25–04:10 | Provenance/privacy | Source panel, timestamp, EXIF stripping, safe errors | No unsupported claims or leaked metadata |
| 04:10–05:00 | Hardening | 2–3 manual test cases, timeout/invalid response handling | Happy path and one failure path work |
| 05:00–05:40 | Submission assets | README, requirements, `.env.example`, screenshots | Fresh-start instructions work |
| 05:40–06:00 | Freeze | Commit, smoke test, freeze features | No new features after this point |

If any stage slips, remove P1 items. Do not take time from the demo hour or final submission buffer to add features.

## 11. Test checklist

### Happy path

- [ ] Upload a clear photo of an organism.
- [ ] Meta API request succeeds.
- [ ] Model output validates against the schema.
- [ ] Candidate appears with visible traits and uncertainty.
- [ ] GBIF returns a meaningful taxonomic match.
- [ ] Correct rank/status/match type appears.
- [ ] Taxon link opens the expected GBIF page.
- [ ] JSON export downloads and contains the provenance fields.

### Failure path

- [ ] Unsupported file type is rejected clearly.
- [ ] Over-size image is rejected or resized safely.
- [ ] Missing API key produces a useful message, not a traceback.
- [ ] Meta API timeout or malformed JSON produces a recoverable error.
- [ ] GBIF timeout/no-match does not erase the AI candidate.
- [ ] A genus-level match is not labelled as a species confirmation.
- [ ] A visually ambiguous photo produces uncertainty, not false certainty.

### Release hygiene

- [ ] `git status` shows no `.env`, credentials, uploaded images or private data.
- [ ] Both policy files remain present and unchanged.
- [ ] Public GitHub repository opens in a logged-out/incognito browser.
- [ ] README includes setup, environment variables, run command, architecture, limitations and data attribution.
- [ ] Demo photo has clear reuse rights.

## 12. One-hour demo production plan

Record one continuous, dependable user journey. Use a clean browser window and a known-good photo. Keep a second known-good local copy in case of upload trouble.

| Video time | Shot | What to say/show |
|---|---|---|
| 00:00–00:20 | Problem | Biodiversity information is fragmented; an image alone is not verified knowledge. |
| 00:20–00:40 | Product | Introduce Vivédex as a provenance-first observation-to-knowledge workflow. |
| 00:40–01:05 | Upload | Upload your own/cleared organism photograph and start analysis. |
| 01:05–01:40 | Meta | Show Muse Spark's visual observations, candidate and uncertainty. Explain its role. |
| 01:40–02:15 | Taxonomy | Show GBIF resolution, accepted name/rank/match status and original source link. |
| 02:15–02:40 | Provenance | Show the model/source/timestamp and clear distinction between AI suggestion and taxonomic match. |
| 02:40–03:00 | Impact/close | Explain who benefits and what the next responsible extension would be. |

**One-hour recording budget:**

- 0–10 min: close unrelated apps, prepare photo, rehearse once.
- 10–25 min: record two takes; use the cleaner take.
- 25–40 min: trim dead air, add title and legible captions if practical.
- 40–50 min: upload the final 3-minute video and verify public/unlisted playback.
- 50–60 min: check repository/video URLs and submission form; submit and verify confirmation.

Do not add features during the video hour. Do not edit the demo so that a simulated or mocked result appears to be a live model call.

## 13. README minimum

- Project name and one-sentence description.
- Problem and intended user.
- What works in this prototype (exactly, not aspirationally).
- Architecture diagram or concise component list.
- Meta Model API integration and model identifier.
- GBIF taxonomy resolution and source link behavior.
- Setup instructions and `MODEL_API_KEY` configuration.
- Run command.
- Limitations: AI candidates are not expert-verified; GBIF name matching does not verify the image or location.
- Data rights/provenance and privacy notes.
- Demo video link and screenshots.

## 14. Submission form checklist

- [ ] Team name: use the actual registered team name.
- [ ] Team members: include every actual member; do not add coding agents as people.
- [ ] Track: Indie Developer if this is your individual project entry; Startup only if submitted under that team/company basis.
- [ ] Problem statement: choose the exact closest option shown in the portal; do not invent a label.
- [ ] Most Viral X post: leave blank unless entering that track and the qualifying public post exists.
- [ ] Project description: describe only the working photo → Muse Spark → GBIF → provenance card workflow.
- [ ] Public GitHub: `https://github.com/rpxgit/vivedex`.
- [ ] Demo: working public/unlisted URL to a three-minute video.
- [ ] Meta products: name Muse Spark / Meta Model API and state exactly how it analyses uploaded images.
- [ ] Why Meta models: explain the multimodal visual reasoning that turns the image into structured candidate observations; GBIF then independently resolves the name.
- [ ] Partner feedback: the event page lists Baseten, Modal and Fireworks as inference partners. Gemini/Antigravity and Codex are development tools, not those inference partners. Do not claim experience with a partner service you did not use. If the form permits, state plainly that no partner inference service was used; otherwise describe only a partner tool you actually tested.
- [ ] Submit before deadline and verify the portal confirmation.

## 15. Anti-scope-creep rules

1. No new feature after the P0 vertical slice is complete.
2. No framework changes after the first successful app launch.
3. No more than one retry for a transient model JSON parse failure.
4. No speculative maps, conservation scores, range claims or population statistics.
5. No storing public user observations without a consent and licensing flow.
6. No new dependency unless it directly unblocks a P0 item.
7. No code-style refactor during the final 90 minutes.
8. No claiming that an AI suggestion is a verified identification.
9. No claiming partner technology use that did not happen.
10. Freeze features at the six-hour mark. The next hour belongs to the demo and submission.

---

## Official and technical references

- Meta / Cerebral Valley event overview: https://events.cerebralvalley.ai/e/meta-ai-developer-hackathon
- Meta Model API overview: https://dev.meta.ai/docs/overview
- Meta image understanding: https://dev.meta.ai/docs/image-understanding
- Meta Muse Spark chat completions quickstart: https://dev.meta.ai/docs/cookbook/quickstart-chat-completions
- GBIF taxonomy interpretation and COL XR migration: https://techdocs.gbif.org/en/data-processing/taxonomy-interpretation
- GBIF terms and data licensing: https://www.gbif.org/terms
- GBIF Backbone Taxonomy dataset record and licence: https://www.gbif.org/dataset/d7dddbf4-2cf0-4f39-9b2a-bb099caae36c
- Existing Vivedex data licensing/provenance policy: https://github.com/rpxgit/vivedex/blob/main/Viv%C3%A9dex%20Data%20Licensing%20and%20Provenance%20Policy.md
- Existing Vivedex security policy: https://github.com/rpxgit/vivedex/blob/main/SECURITY.md
