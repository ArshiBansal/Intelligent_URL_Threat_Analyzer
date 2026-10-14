# Intelligent URL Threat Analyzer

> Phishing pages are built to look trustworthy. This project is built to question that trust — carefully, measurably, and without pretending to be perfect.

**AI-assisted phishing URL and webpage detection**  
Streamlit-only app · **PhreshPhish** dataset · Classical ML + NLP · MongoDB (PyMongo)  
No deep learning · No Jupyter · No “benign means safe” myths

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![MongoDB](https://img.shields.io/badge/DB-MongoDB%20%2B%20PyMongo-47A248.svg)](https://www.mongodb.com/)
[![Dataset](https://img.shields.io/badge/Dataset-PhreshPhish-orange.svg)](https://huggingface.co/datasets/phreshphish/phreshphish)

**Repository:** [github.com/ArshiBansal/Intelligent_URL_Threat_Analyzer](https://github.com/ArshiBansal/Intelligent_URL_Threat_Analyzer)

---

## The problem it solves

Phishing sites imitate banks, email providers, and payment services. They reuse familiar layouts, urgent language, and URLs that *almost* look right. Two common gaps make detection hard in practice:

1. **URL-only checks** miss page context (forms, password fields, scripts, link structure).  
2. **Full webpage datasets** are large, messy, and expensive to process if you load everything into memory.

Teams and learners also need more than a single accuracy number: **false positives**, **false negatives**, class imbalance, and an interface that shows *evidence* — not a black-box “trust us” label.

**Intelligent URL Threat Analyzer** addresses that gap as a **defensive, educational decision-support system**: it combines URL structure, selected HTML signals, and classical supervised models trained on **PhreshPhish**, then explains what was measured and how uncertain the answer still is.

It does **not** claim perfect detection. It does **not** replace browsers, email filters, or human judgment.

---

## Objectives

| Goal | How this project approaches it |
|------|--------------------------------|
| Understand the data before modeling | Schema audit, label checks (`benign` / `phish`), missingness, streaming ingest |
| Handle large HTML safely | Chunked/streaming HF load, HTML truncation, paginated Mongo queries |
| Richer signals than URL-only | URL features + selected HTML features + classical text experiments |
| Compare methods fairly | ≥4 ML algorithms and ≥4 text representations offline |
| Evaluate beyond accuracy | Precision, recall, F1, per-class metrics, confusion matrix, PR-AUC, ROC-AUC, thresholds |
| Make results usable | Eight-tab Streamlit app: analyze, explain, explore, history, saved model metrics |
| Stay responsible | Disclaimers, no default live crawling, credentials in env vars, defensive framing only |

---

## What you get

- **URL Threat Analyzer** — submit a URL (optional HTML), get class + confidence + disclaimer  
- **Threat Evidence** — which URL/HTML signals were non-zero (observations ≠ proof of malice)  
- **Dataset Explorer & Analytics** — browse PhreshPhish-backed records without loading the full collection  
- **Prediction History** — prior runs stored in MongoDB  
- **Model Performance** — metrics from offline evaluation only (never invented at app startup)  
- **About** — methodology, PhreshPhish attribution, limitations  

**Offline pipeline:** ingest → features → NLP trials → train ≥4 models → evaluate → export artifacts the app can load.

---

## System at a glance

```
PhreshPhish (Hugging Face, streaming)
        → validate & upsert (sha256) → MongoDB
                                          ↓
                         Streamlit (8 tabs) ← joblib artifacts
                                          ↑
              offline scripts: features · train · evaluate · export
```

Training **never** runs inside Streamlit. The UI only loads versioned model files.

---

## Dataset — PhreshPhish

| | |
|--|--|
| **Display name** | PhreshPhish (**do not rename**) |
| **Hugging Face** | [phreshphish/phreshphish](https://huggingface.co/datasets/phreshphish/phreshphish) |
| **License** | [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/) |
| **Paper** | [PhreshPhish (arXiv:2507.10854)](https://arxiv.org/abs/2507.10854) |
| **Labels used** | `benign`, `phish` |
| **Access method** | `datasets` library only (streaming) — not a bulk CSV download |

Key fields: `url`, `label`, `html`, `date`, `lang`, `lang_score`, `sha256`, `target`.

---

## Tech stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.10+ |
| UI | Streamlit |
| Database | MongoDB (local / self-hosted) + PyMongo |
| Data access | Hugging Face `datasets` (streaming) |
| ML | scikit-learn, XGBoost |
| NLP | TF-IDF, CountVectorizer, lexical statistics |
| HTML parsing | BeautifulSoup + lxml |
| Serialization | joblib |
| Visualization | Plotly / Streamlit charts |
| Config | python-dotenv |

**Out of scope by design:** deep learning frameworks, Jupyter as the product interface, MongoDB Atlas requirement, default live fetching of arbitrary websites.

---

## The eight required tabs

1. **Dashboard** — dataset totals, class mix, Mongo status, recent activity  
2. **URL Threat Analyzer** — primary interactive analysis  
3. **Threat Evidence & Explanation** — features vs interpretation  
4. **Dataset Explorer** — filter, paginate, inspect records  
5. **Threat Analytics** — interactive charts and quality snapshot  
6. **Prediction History** — search history; clear only with explicit confirmation  
7. **Model Performance** — saved evaluation results and confusion matrix  
8. **About, Dataset & Methodology** — purpose, attribution, limits, stack  

---

## Quick start

### Prerequisites

- Python 3.10+  
- Local MongoDB running and reachable  
- Optional: [Hugging Face token](https://huggingface.co/settings/tokens) in `.env` for higher rate limits  

### Setup

```bash
git clone https://github.com/ArshiBansal/Intelligent_URL_Threat_Analyzer.git
cd Intelligent_URL_Threat_Analyzer

python -m venv venv
# Windows:
venv\Scripts\activate
# macOS / Linux:
# source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

Minimal `.env`:

```env
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=intelligent_url_threat_analyzer
# HF_TOKEN=hf_xxx   # optional
```

Never commit a real `.env`.

### Ingest (use a cap on laptops)

Full train is large; HTML fields can be multi‑megabyte. Prefer:

```bash
python scripts/01_schema_audit.py --max-samples 2000
python scripts/02_ingest_to_mongodb.py --split train --max-samples 50000 --batch-size 100
python scripts/03_clean_and_explore.py
```

Upserts by `sha256` → safe to re-run.

### Train offline, then open the app

```bash
python scripts/04_feature_engineering.py --max-records 20000
python scripts/05_nlp_experiments.py --max-records 8000
python scripts/06_ml_experiments.py --max-records 15000 --save-artifacts
python scripts/07_evaluate_and_select.py --metric f1
python scripts/08_export_artifacts.py --promote

streamlit run app.py
```

---

## Offline pipeline (phases)

| # | Script | Deliverable |
|---|--------|-------------|
| 1 | `01_schema_audit.py` | Schema / label audit report |
| 2 | `02_ingest_to_mongodb.py` | Streamed ingest + indexes |
| 3 | `03_clean_and_explore.py` | Data-quality report |
| 4 | `04_feature_engineering.py` | URL + HTML features in Mongo / sample export |
| 5 | `05_nlp_experiments.py` | ≥4 text approaches compared |
| 6 | `06_ml_experiments.py` | ≥4 ML models trained + artifacts |
| 7 | `07_evaluate_and_select.py` | Selection report + optional Mongo register |
| 8 | `08_export_artifacts.py` | Manifest / `latest_*` promotion |

Details: [docs/architecture.md](docs/architecture.md) · [docs/feature_list.md](docs/feature_list.md) · [docs/evaluation_report.md](docs/evaluation_report.md)

---

## Project structure

```
Intelligent_URL_Threat_Analyzer/
├── app.py
├── config/                 # env-driven settings + constants
├── src/
│   ├── data/               # ingest, validate, explore
│   ├── features/           # URL, HTML, text
│   ├── models/             # train, evaluate, predict, compare
│   ├── db/                 # connection, repositories, indexes
│   └── utils/
├── streamlit_app/
│   ├── tabs/               # eight tabs
│   └── components/
├── scripts/                # 01–08 + ml_feature_utils
├── artifacts/              # models, preprocessors, metadata
├── data/reports/
├── tests/
└── docs/
```

---

## Tests

```bash
pytest tests/ -v
```

Mongo-dependent tests skip automatically if the database is unavailable.

---

## Limitations

- Typical laptop workflows use a **sample** of PhreshPhish, not the entire train split.  
- HTML is **truncated** on ingest/parse for memory safety.  
- Models optimize statistical risk on labeled data — they are not a full security product.  
- Legitimate login pages share features with phishing pages (password fields, “verify” language).  
- Without optional HTML, the model leans more on URL structure alone.

---

## Responsible use

- Positioned for **anti-phishing research and education**, not harassment or unauthorized testing.  
- Do not treat a benign prediction as proof of safety.  
- Do not use predictions to target individuals or websites.  
- Keep database credentials out of source control; use least-privilege access.  
- Honor PhreshPhish **CC-BY-4.0** attribution when you share results or derivatives.

---

## License & citation

**Application code** — add a repository license of your choice when you publish (e.g. MIT).

**Dataset** — PhreshPhish; CC-BY-4.0; cite the authors’ paper when appropriate:

- Dataset: https://huggingface.co/datasets/phreshphish/phreshphish  
- Paper: https://arxiv.org/abs/2507.10854  

---

## Further reading

| Doc | Contents |
|-----|----------|
| [docs/architecture.md](docs/architecture.md) | Design, data flow, components |
| [docs/feature_list.md](docs/feature_list.md) | Every URL / HTML / text signal |
| [docs/evaluation_report.md](docs/evaluation_report.md) | Metrics, templates, how to fill results |

---

*Inspect the evidence. Question the score. That is the product.*
