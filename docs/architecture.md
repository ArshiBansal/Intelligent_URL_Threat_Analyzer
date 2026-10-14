# Architecture — Intelligent URL Threat Analyzer

> Phishing pages are good at looking legit. This system is good at not taking their word for it.

**Streamlit · PhreshPhish · Classical ML + NLP · MongoDB **  
Defensive / educational use — not a crystal ball, not a weapon.

---

## The idea in one breath

You paste a URL (and optionally some HTML). The app pulls structural clues from the link, peeks at page signals if you give it markup, runs a model that was trained offline on **PhreshPhish**, and returns:

- a **class** (benign vs phish)  
- a **confidence** when the model supports it  
- the **evidence** it actually used  
- a clear reminder that *benign ≠ safe* and *phish ≠ proven malice*

No deep learning. No Jupyter. No “trust me, bro” black box without a paper trail.

---

## Big picture

```
                    PhreshPhish (Hugging Face)
                              │
                     streaming ingest (scripts)
                              ▼
                    ┌─────────────────────┐
                    │   MongoDB           │
                    │  records · features │
                    │  history · metrics  │
                    └──────────┬──────────┘
                               │ PyMongo
                               ▼
                    ┌─────────────────────┐
                    │  Streamlit          │
                    │  analyze · explain  │
                    │  explore · history  │
                    └──────────┬──────────┘
                               │
                      loads joblib artifacts
                    (training never runs here)
```

**Offline lab** (scripts 01→08): audit → ingest → explore → features → NLP trials → ML trials → pick a winner → export artifacts.

**Online desk** (the app): validate → extract features → predict → show evidence → optionally remember the call.

---

## Why these choices

| Choice | Why it matters |
|--------|----------------|
| **Streamlit only** | One surface. No second frontend to babysit. |
| **MongoDB + PyMongo** | HTML-heavy docs, flexible schema, runs on your machine. |
| **HF `datasets` streaming** | No multi‑GB CSV sitting on disk “just in case.” |
| **Train offline, infer online** | The UI stays fast and boring in a good way. |
| **Classical ML only** | Interpretable-ish features, smaller footprint, spec-compliant. |
| **Secrets in `.env`** | Credentials never ride along in git history. |

---

## The moving parts

### Config — the single source of truth

`settings.py` reads the environment (Mongo URI, collection names, paths, optional HF token).  
`constants.py` freezes the things that must not drift: dataset name **PhreshPhish**, labels `benign` / `phish`, feature lists, the eight tab titles, disclaimers, model version.

### Data — get it in without melting the laptop

PhreshPhish pages can be *huge*. Ingest streams from Hugging Face, **truncates HTML** (default ~200k characters), validates labels, and **upserts by `sha256`**. Re-runs are safe: same hash → update, not a duplicate pile.

Explore helpers answer the boring-but-critical questions: class balance, languages, date range, missingness — all via aggregation, not “load everything into RAM.”

### Features — what the models actually see

- **URL** — length, dots, IP-in-host, HTTPS, shorteners, sketchy TLDs, login/bank/paypal-ish keywords.  
- **HTML** — forms, password fields, external links, scripts, iframes, title, “does this look like a login form?” (BeautifulSoup, tolerant of messy markup).  
- **Text** — TF-IDF (word + char), bag-of-words, lexical stats — four classical takes, no transformers required.

Same extractors in training and in the app → less train/serve drama.

### Models — four classical contenders

Logistic Regression · Random Forest · XGBoost · Gradient Boosting.

Train and compare offline. Save **joblib + JSON metadata**. The app only loads; it never fits. Evaluation covers precision, recall, F1, per-class scores, confusion matrix, balanced accuracy, PR-AUC, ROC-AUC, and threshold trade-offs.

### Database — five logical buckets

| Collection | Holds |
|------------|--------|
| Source records | Validated PhreshPhish rows |
| Derived features | Vectors keyed by `sha256` |
| Prediction history | What users asked and what the model said |
| Model metadata | Who was trained, when, with what shape |
| Evaluation summaries | Metrics you can show without re-running training |

Indexes on the fields you actually filter on (label, URL/hash, date, timestamps). Pagination everywhere the UI lists data.

### Streamlit — eight tabs, zero fluff

1. **Dashboard** — pulse check: counts, balance, Mongo status, recent calls  
2. **URL Threat Analyzer** — the main event: paste → analyze → confidence + disclaimer  
3. **Threat Evidence** — “here’s what we measured” vs “here’s how the model leaned”  
4. **Dataset Explorer** — search/filter/paginate without drowning the browser  
5. **Threat Analytics** — charts for balance, language, time, quality  
6. **Prediction History** — past runs; clear only if you type `DELETE`  
7. **Model Performance** — *saved* metrics only (no inventing scores at startup)  
8. **About** — PhreshPhish attribution, limits, stack, responsible-use note  

Sidebar keeps navigation obvious. Empty and error states are meant to be readable, not cryptic stack traces.

---

## Life of a prediction

1. User submits a URL (http/https only; length-capped).  
2. Optional HTML is sanitized and truncated.  
3. URL + HTML features are built with the same code used in training.  
4. The selected model artifact is loaded from disk.  
5. Class + confidence come back; top non-zero signals are attached as evidence.  
6. A plain-language disclaimer is always shown.  
7. If Mongo is up, the call is written to history.

If artifacts are missing, the app says so and points at the offline scripts — it does not pretend to train on the fly.

---

## Stack at a glance

Python · Streamlit · MongoDB/PyMongo · Hugging Face `datasets` · scikit-learn · XGBoost · BeautifulSoup · joblib · Plotly · python-dotenv

**Not in the room:** deep learning frameworks, notebooks as the product surface, default live crawling of arbitrary sites.

---

## Guardrails

- Benign predictions are **not** a safety certificate.  
- Phishing predictions can be wrong.  
- Don’t use outputs to harass people or poke systems you don’t own.  
- Keep Mongo credentials out of the repo.  
- Dataset name stays **PhreshPhish**; license is CC-BY-4.0 — attribute it.

---

## Layout you’ll actually navigate

```
app.py
config/          settings + constants
src/
  data/          ingest · validate · explore
  features/      url · html · text
  models/        train · evaluate · predict · compare
  db/            connection · repositories · indexes
  utils/         preprocessing · validation · helpers
streamlit_app/
  tabs/          the eight required surfaces
  components/    charts · cards · forms
scripts/         01…08 offline pipeline + shared feature loader
artifacts/       models · preprocessors · metadata · manifest
data/reports/    audit & experiment outputs
tests/
docs/            you are here
```

---

## Practical reality check

Full PhreshPhish train is large and HTML-heavy. On a normal laptop, prefer capped ingest (`--max-samples`) and truncated HTML. The ~tens of thousands of rows you can hold comfortably are enough to train, compare models, and demo the full UI. Upserts mean you can grow the collection later without starting from zero.

---

## Links worth keeping

- Dataset: [phreshphish/phreshphish](https://huggingface.co/datasets/phreshphish/phreshphish)  
- Paper: [arXiv:2507.10854](https://arxiv.org/abs/2507.10854)  
- Code: [Intelligent_URL_Threat_Analyzer](https://github.com/ArshiBansal/Intelligent_URL_Threat_Analyzer)

---

*Built to be inspected, not blindly trusted. That’s the point.*
