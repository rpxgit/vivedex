# Vivédex 3-Minute Demo Video Script

**Duration:** Exact target 2:45 – 3:00  
**Application:** Vivédex MVP (`app.py`)  
**Audience:** Hackathon judges & biodiversity developers  

---

## Part 1: Problem & Purpose (0:00 – 0:40)
- **Visual:** Open browser on `http://localhost:8501`. Show the clean Vivédex header and privacy notice.
- **Narrator (Speaking):**
  > "Hello! This is Vivédex. When observing wild organisms, nature lovers and researchers frequently face a dilemma: vision AI models can make wild guesses without provenance, while complex taxonomic databases are difficult to query quickly from field photos.
  >
  > Vivédex bridges this gap: it turns an organism photograph into a cautious, explainable candidate identification powered by Meta Muse Spark, and verifies that candidate against the authoritative GBIF Backbone Taxonomy."

---

## Part 2: Image Upload & In-Memory Privacy (0:40 – 1:05)
- **Visual:** Drag and drop an observation image (e.g. House Sparrow or test organism). Point out the privacy note.
- **Narrator (Speaking):**
  > "We start by uploading an observation photograph. Notice our privacy guarantee: Vivédex strips EXIF geolocation and camera metadata immediately in-memory, and never stores user images on disk."

---

## Part 3: Model Analysis & Candidate Evidence (1:05 – 1:45)
- **Visual:** Click **`Analyse Image`**. Show progress spinner, followed by the **Candidate Identification** card.
- **Narrator (Speaking):**
  > "Clicking 'Analyse Image' submits the cleaned image to Meta's `muse-spark-1.3` model.
  >
  > Notice what we do NOT do: we do not invent fake percentage probabilities. Instead, Meta Muse Spark reports concrete visible traits: the conical seed-eating bill, the black throat bib, and chestnut nape. It also lists possible lookalikes and uncertainty notes.
  >
  > Most importantly, look at the top banner: *AI-generated candidate. Not expert-verified.*"

---

## Part 4: GBIF Taxonomic Reconciliation (1:45 – 2:20)
- **Visual:** Scroll down to the **Taxonomic Reconciliation** card.
- **Narrator (Speaking):**
  > "Next, Vivédex queries the Global Biodiversity Information Facility (GBIF) Species Match API in real time.
  >
  > Here, our candidate scientific name is reconciled with the official GBIF Backbone Taxonomy. We see the accepted canonical name, the exact match status, the complete phylogenetic hierarchy from Animalia down to Passer, and a direct link to the official GBIF species page.
  >
  > We preserve the original AI candidate name separately from the authoritative GBIF record, respecting scientific provenance."

---

## Part 5: JSON Export & Provenance Record (2:20 – 3:00)
- **Visual:** Click **`Download JSON Report`** and expand the JSON viewer.
- **Narrator (Speaking):**
  > "Finally, the user can export a reproducible observation record in JSON. This record packages the model's visual evidence, the GBIF taxonomy keys, retrieval timestamps, and CC0 data licensing metadata into one structured file ready for downstream research.
  >
  > Vivédex combines the perception of Meta models with open scientific standards to deliver cautious, trustworthy biodiversity knowledge. Thank you!"

