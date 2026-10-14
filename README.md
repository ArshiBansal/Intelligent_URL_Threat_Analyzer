# Intelligent URL Threat Analyzer

### The URL looks ordinary. The page looks polished. The model still gets a vote — and has to show its work.

Phishing succeeds when familiarity wins. A domain one letter off. A password field on a page that *feels* like your bank. A “verify now” banner that arrives at 11 p.m.

**Intelligent URL Threat Analyzer** is a defensive, Streamlit-only system that treats that familiarity as something to *measure*, not believe. It scores URLs (and optional HTML) as **benign** or **phish**, surfaces the **features** behind the score, and keeps every serious experiment **offline** — classical ML and NLP on the large-scale **PhreshPhish** dataset, persisted in **MongoDB**, never trained inside the browser tab.

No deep learning. No Jupyter-as-product. No silent promise that “benign” means safe.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B.svg)](https://streamlit.io/)
[![MongoDB](https://img.shields.io/badge/MongoDB-PyMongo-47A248.svg)](https://www.mongodb.com/)
[![PhreshPhish](https://img.shields.io/badge/Dataset-PhreshPhish-orange.svg)](https://huggingface.co/datasets/phreshphish/phreshphish)

**Code:** [github.com/ArshiBansal/Intelligent_URL_Threat_Analyzer](https://github.com/ArshiBansal/Intelligent_URL_Threat_Analyzer)

---

## The problem

Modern phishing is not always crude. It reuses real layout patterns, urgent language, and URLs that survive a glance. Two gaps show up again and again:

1. **String-only detectors** ignore page structure — forms, password inputs, scripts, outbound links.  
2. **Full webpage corpora** are huge and HTML-heavy; naive loading turns research into an out-of-memory story.

Accuracy alone also lies under class imbalance. A system that never raises a phishing flag looks “accurate” and still fails at the one job that matters.

This project exists to close that loop for **learning and defensive analysis**: rich features, honest metrics, an interface that explains *what was observed*, and a pipeline that survives real dataset size.

---

## Objectives

| Objective | How we pursue it |
|-----------|------------------|
| Know the data before modeling | Schema audit, label validation (`benign` / `phish`), quality reports |
| Ingest at scale without melting RAM | Hugging Face **streaming**, HTML truncation, batch upserts by `sha256` |
| Go beyond URL-only signals | Structural URL features + selected HTML features + classical text experiments |
| Compare methods, don’t anoint one early | ≥4 ML models · ≥4 NLP representations · offline only |
| Evaluate the failures that matter | Precision, recall, F1, per-class scores, confusion matrix, PR-AUC, ROC-AUC, thresholds |
| Make analysis usable day to day | Eight-tab Streamlit app: analyze, explain, explore, history, saved performance |
| Stay responsible | Disclaimers, env-based secrets, no default live crawl, defensive framing |

---

## What the system does

```
URL (± HTML)
    → validate (http/https, length, host)
    → extract URL + HTML features
    → load offline-trained model (joblib)
    → class · confidence · evidence
    → optional write to prediction history
```

Behind the scenes: PhreshPhish streams into MongoDB; scripts engineer features, train models, write evaluation JSON; the app **loads** artifacts — it does not fit models on click.

---

## Eight tabs — the product surface

| # | Tab | Role |
|---|-----|------|
| 1 | **Dashboard** | Health, counts, class mix, recent pulse |
| 2 | **URL Threat Analyzer** | Primary workflow — paste, score, disclaimer |
| 3 | **Threat Evidence & Explanation** | Non-zero signals vs interpretation |
| 4 | **Dataset Explorer** | Search, filter, paginate labeled records |
| 5 | **Threat Analytics** | Balance, language, temporal, quality charts |
| 6 | **Prediction History** | Prior analyses; clear only with confirmation |
| 7 | **Model Performance** | Metrics from offline runs only |
| 8 | **About, Dataset & Methodology** | Attribution, limits, stack, intent |

---

## Dataset: PhreshPhish

| | |
|--|--|
| **Name** | **PhreshPhish** (required; do not rename) |
| **Hub** | [phreshphish/phreshphish](https://huggingface.co/datasets/phreshphish/phreshphish) |
| **License** | [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/) |
| **Paper** | [arXiv:2507.10854](https://arxiv.org/abs/2507.10854) |
| **Labels** | `benign` · `phish` |
| **Access** | Hugging Face `datasets` library (streaming) — not a bulk CSV dump |

Fields in play: `url`, `html`, `label`, `date`, `lang`, `lang_score`, `sha256`, `target`.

---

## Stack

| Layer | Choice |
|-------|--------|
| UI | Streamlit |
| DB | MongoDB (local / self-hosted) + PyMongo |
| Data | Hugging Face `datasets` (streaming) |
| ML | scikit-learn, XGBoost |
| NLP | TF-IDF (word/char), bag-of-words, lexical stats |
| HTML | BeautifulSoup + lxml |
| Artifacts | joblib |
| Config | python-dotenv |

**Explicit non-goals:** deep learning frameworks, Jupyter as the delivery UI, mandatory MongoDB Atlas, default live fetching of arbitrary sites.

---

## Quick start

### Prerequisites

- Python 3.10+  
- MongoDB running locally (or any self-hosted URI)  
- Optional [HF token](https://huggingface.co/settings/tokens) for higher Hub limits  

### Install

```bash
git clone https://github.com/ArshiBansal/Intelligent_URL_Threat_Analyzer.git
cd Intelligent_URL_Threat_Analyzer

python -m venv venv
venv\Scripts\activate            # Windows
# source venv/bin/activate       # macOS / Linux

pip install -r requirements.txt
cp .env.example .env
```

`.env` (never commit secrets):

```env
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=intelligent_url_threat_analyzer
# HF_TOKEN=hf_...
```

```bash
python -c "from src.db.connection import ping; print('Mongo OK' if ping() else 'Mongo DOWN')"
```

### Data → train → app

Full PhreshPhish train is large; HTML can be multi‑MB per row. **Cap samples on laptops.**

```bash
python scripts/01_schema_audit.py --max-samples 2000
python scripts/02_ingest_to_mongodb.py --split train --max-samples 50000 --batch-size 100
python scripts/03_clean_and_explore.py
python scripts/04_feature_engineering.py --max-records 20000
python scripts/05_nlp_experiments.py --max-records 8000
python scripts/06_ml_experiments.py --max-records 15000 --save-artifacts
python scripts/07_evaluate_and_select.py --metric f1
python scripts/08_export_artifacts.py --promote

streamlit run app.py
```

Ingest is **idempotent** (upsert on `sha256`). Re-runs update; they do not multiply rows forever.

---

## Offline pipeline

| Script | Purpose |
|--------|---------|
| `01_schema_audit.py` | Labels, fields, sample quality (no write required) |
| `02_ingest_to_mongodb.py` | Stream HF → Mongo + indexes |
| `03_clean_and_explore.py` | Class balance, languages, missingness |
| `04_feature_engineering.py` | URL + HTML vectors |
| `05_nlp_experiments.py` | ≥4 text representations |
| `06_ml_experiments.py` | ≥4 models + joblib artifacts |
| `07_evaluate_and_select.py` | Choose and document the winner |
| `08_export_artifacts.py` | Manifest / promote `latest_*` |

Deeper reading: [architecture](docs/architecture.md) · [feature list](docs/feature_list.md) · [evaluation report](docs/evaluation_report.md)

---

## Layout

```
Intelligent_URL_Threat_Analyzer/
├── app.py
├── config/
├── src/data · features · models · db · utils
├── streamlit_app/tabs · components
├── scripts/01…08
├── artifacts/
├── data/reports/
├── tests/
└── docs/
```

```bash
pytest tests/ -v
```

---

## Limitations (the intrigue cuts both ways)

- A strong score is still a **probability**, not a verdict.  
- Laptop pipelines usually see a **subset** of PhreshPhish, not every published row.  
- Truncated HTML means some page signal is sacrificed for stability.  
- Real banks also have login forms and “secure” in the URL — features **fire on legit pages too**.  
- Without pasted HTML, the model leans harder on URL structure alone.

That tension is the point: detection is useful precisely because it is incomplete — and documented as such.

---

## Responsible use

Built for **anti-phishing research and education**.

- Do not use outputs to harass, dox, or attack people or systems.  
- Do not treat benign predictions as permission to trust a page with credentials.  
- Keep Mongo credentials in the environment, not the repository.  
- Preserve **PhreshPhish** naming and CC-BY-4.0 attribution when you publish results.

---

## Attribution

**Dataset:** PhreshPhish · [Hugging Face](https://huggingface.co/datasets/phreshphish/phreshphish) · [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/) · [paper](https://arxiv.org/abs/2507.10854)

**Application code:** license of your choice when you publish the repo.

---

*Trust is expensive. Evidence is cheaper. Start there.*
