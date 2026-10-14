# Intelligent URL Threat Analyzer

### It looks legitimate. That doesn't make it trustworthy.

One character separates a real domain from a convincing imitation. A
familiar login form can hide an unfamiliar destination. A polished page
can still ask for the one thing it should never get: your credentials.

**Intelligent URL Threat Analyzer** examines a URL and optional HTML for
signals associated with **`benign`** and **`phish`** pages. It returns a
prediction with confidence and observable evidence---not a promise of
safety.

**The principle:** every prediction deserves scrutiny.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B.svg)](https://streamlit.io/)
[![MongoDB](https://img.shields.io/badge/MongoDB-PyMongo-47A248.svg)](https://www.mongodb.com/)
[![Dataset](https://img.shields.io/badge/Dataset-PhreshPhish-orange.svg)](https://huggingface.co/datasets/phreshphish/phreshphish)

**Dataset:**
[PhreshPhish](https://huggingface.co/datasets/phreshphish/phreshphish) ·
**Application:**
[GitHub](https://github.com/ArshiBansal/Intelligent_URL_Threat_Analyzer)

------------------------------------------------------------------------

## One URL. Multiple signals.

A URL can reveal suspicious structure. Supplied HTML can add context
through forms, password inputs, scripts, and outbound links. These
signals are evidence---not proof: legitimate sites can exhibit them too.

``` text
URL + optional HTML
        ↓
Validation and feature extraction
        ↓
Saved offline-trained model
        ↓
Prediction + confidence + evidence
        ↓
Optional MongoDB history
```

Training and evaluation happen offline. Streamlit loads saved artifacts;
it does not retrain models during a prediction.

## Investigate, don't just classify

The app has eight focused tabs:

  -----------------------------------------------------------------------
  Tab                                 What it reveals
  ----------------------------------- -----------------------------------
  **Dashboard**                       Dataset and prediction activity at
                                      a glance

  **URL Threat Analyzer**             Predicted class, confidence, and
                                      analysis result

  **Threat Evidence & Explanation**   Extracted signals behind the
                                      prediction

  **Dataset Explorer**                Searchable, filterable labeled
                                      records

  **Threat Analytics**                Class balance, languages, dates,
                                      and data quality

  **Prediction History**              Previous analyses, with
                                      confirmation before clearing

  **Model Performance**               Saved evaluation metrics and model
                                      comparisons

  **About, Dataset & Methodology**    Dataset attribution, methods, and
                                      limitations
  -----------------------------------------------------------------------

## Six models. No guesswork.

The project compares six classical machine-learning algorithms:

    \# Algorithm
  ---- --------------------------------
     1 Logistic Regression (balanced)
     2 Histogram Gradient Boosting
     3 Extra Trees
     4 Random Forest (regularized)
     5 Linear SVC with calibration
     6 XGBoost (regularized)

URL structure, lexical statistics, selected HTML features, and text
representations---including word- and character-level TF-IDF and
bag-of-words---can be evaluated in the feature pipeline.

Models are compared using precision, recall, F1-score, per-class
results, confusion matrices, and PR-AUC / ROC-AUC where appropriate.
**No model is declared the winner without measured results.** Accuracy
alone is not enough when missed phishing attempts matter.

## The dataset is part of the challenge

**PhreshPhish** is accessed through the Hugging Face `datasets` library,
using streaming rather than assuming the entire corpus can be loaded
into memory.

  ------------------------------------------------------------------------------------------------------------
  Detail                              Value
  ----------------------------------- ------------------------------------------------------------------------
  Dataset                             [PhreshPhish](https://huggingface.co/datasets/phreshphish/phreshphish)

  Labels                              `benign`, `phish`

  License                             [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

  Paper                               [arXiv:2507.10854](https://arxiv.org/abs/2507.10854)

  Fields used where available         `url`, `html`, `label`, `date`, `lang`, `lang_score`, `sha256`, `target`
  ------------------------------------------------------------------------------------------------------------

Large HTML documents make ingestion expensive. The pipeline uses sample
limits, HTML truncation, batch writes, data-quality checks, and upserts
keyed by `sha256` where available. Local experiments may use a subset;
reports should state the actual sample and split.

## Stack

-   **App:** Streamlit
-   **Database:** MongoDB + PyMongo
-   **Data:** Hugging Face `datasets`
-   **ML:** scikit-learn, XGBoost
-   **Text features:** TF-IDF, bag-of-words, lexical statistics
-   **HTML parsing:** BeautifulSoup, lxml
-   **Artifacts:** joblib
-   **Configuration:** python-dotenv

No deep-learning framework, notebook-based product interface, mandatory
Atlas account, or default live crawling of arbitrary websites is
required.

## Run locally

**Requirements:** Python 3.10+, Git, and a running local or self-hosted
MongoDB instance.

``` bash
git clone https://github.com/ArshiBansal/Intelligent_URL_Threat_Analyzer.git
cd Intelligent_URL_Threat_Analyzer

python -m venv venv
```

Activate the environment:

``` bat
:: Windows
venv\Scripts\activate
```

``` bash
# macOS / Linux
source venv/bin/activate
```

Install dependencies and configure the environment:

``` bash
pip install -r requirements.txt
```

Create `.env` using `.env.example` if present:

``` env
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=intelligent_url_threat_analyzer
# HF_TOKEN=your_hugging_face_token
```

Keep credentials out of source control.

### Prepare data and models

Run from the repository root; check each script's `--help` if options
differ in your checkout.

``` bash
python scripts/01_schema_audit.py --max-samples 2000
python scripts/02_ingest_to_mongodb.py --split train --max-samples 50000 --batch-size 100
python scripts/03_clean_and_explore.py
python scripts/04_feature_engineering.py --max-records 20000
python scripts/05_nlp_experiments.py --max-records 8000
python scripts/06_ml_experiments.py --max-records 15000 --save-artifacts
python scripts/07_evaluate_and_select.py --metric f1
python scripts/08_export_artifacts.py --promote
```

Then launch the app:

``` bash
streamlit run app.py
```

The app requires the saved model artifacts expected by its
configuration. Starting Streamlit does not train models or automatically
ingest the dataset.

Run tests if the test suite is present:

``` bash
pytest tests/ -v
```

## What a prediction cannot tell you

-   **Benign does not mean safe.** Never enter credentials based only on
    this result.
-   **Confidence is not certainty.** Treat it as model output, not a
    guaranteed real-world probability.
-   **Signals can overlap.** Legitimate sites can contain login forms,
    scripts, redirects, or unusual URL patterns.
-   **HTML may be absent or truncated.** The prediction then has less
    page-structure context.
-   **Threats change.** Dataset coverage and historical patterns cannot
    represent every current campaign.
-   **Evaluation matters.** Sampling, data leakage, class imbalance, and
    thresholds can distort reported performance.

## Responsible use

Use the system for defensive analysis and education. Do not use
predictions to harass people or attack systems. Never submit passwords,
session tokens, API keys, or other secrets. Secure database credentials
and preserve PhreshPhish attribution when sharing derived work.

**Attribution:**
[PhreshPhish](https://huggingface.co/datasets/phreshphish/phreshphish) ·
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) · [Research
paper](https://arxiv.org/abs/2507.10854)

------------------------------------------------------------------------

*The page can imitate trust. The evidence is where the story begins.*
