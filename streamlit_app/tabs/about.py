"""
Tab 8 – About, Dataset & Methodology

Project purpose, exact PhreshPhish attribution, data fields, workflow,
model limitations, responsible-use guidance and technology stack.
"""

from __future__ import annotations

import streamlit as st

from config.constants import (
    APP_TITLE,
    DATASET_DISPLAY_NAME,
    DATASET_HF_ID,
    DATASET_HF_URL,
    DATASET_LICENSE,
    DATASET_PAPER,
    RESPONSIBLE_USE_NOTE,
    CURRENT_MODEL_VERSION,
    SUPPORTED_MODEL_NAMES,
)


def render_about() -> None:
    st.header("About, Dataset & Methodology")

    st.subheader("Project Purpose")
    st.markdown(
        f"""
**{APP_TITLE}** is a defensive, educational decision-support tool that estimates
whether a URL (and optional webpage HTML) is more likely to be phishing or benign.

It combines:
- URL structural features
- Selected HTML / page signals
- Classical machine-learning models (no deep learning)
- The large-scale **{DATASET_DISPLAY_NAME}** dataset

The application is intentionally conservative: a benign prediction does **not**
guarantee safety, and a phishing prediction may be incorrect.
        """
    )

    st.subheader("Dataset – PhreshPhish")
    st.markdown(
        f"""
| Item | Value |
|------|-------|
| **Display name** | {DATASET_DISPLAY_NAME} (must not be renamed) |
| **Hugging Face ID** | `{DATASET_HF_ID}` |
| **URL** | [{DATASET_HF_URL}]({DATASET_HF_URL}) |
| **License** | {DATASET_LICENSE} |
| **Paper** | [arXiv]({DATASET_PAPER}) |

**Key fields used:** `url`, `label`, `html`, `date`, `lang`, `lang_score`, `sha256`, `target`.

The dataset is loaded exclusively via the Hugging Face `datasets` library
(streaming / chunked). No full CSV download is performed.
        """
    )

    st.subheader("Methodology Overview")
    st.markdown(
        """
1. **Ingestion** – Stream PhreshPhish → validate → upsert into MongoDB by `sha256`.
2. **Feature engineering** – Deterministic URL features + robust HTML features + classical text representations (TF-IDF word/char, Bag-of-Words, lexical stats).
3. **Model training** (offline only) – At least four classical algorithms:
   Logistic Regression, Random Forest, XGBoost, Gradient Boosting.
4. **Evaluation** – Precision, recall, F1, per-class metrics, confusion matrix,
   balanced accuracy, PR-AUC, ROC-AUC, threshold analysis.
5. **Inference** – Streamlit loads versioned joblib artifacts; never trains at runtime.
6. **Persistence** – Predictions, model metadata and evaluation summaries stored in MongoDB.
        """
    )

    st.markdown(f"**Currently supported models:** {', '.join(SUPPORTED_MODEL_NAMES)}")
    st.markdown(f"**Artifact version in use:** `{CURRENT_MODEL_VERSION}`")

    st.subheader("Limitations & Responsible Use")
    st.warning(RESPONSIBLE_USE_NOTE)
    st.markdown(
        """
- Predictions are probabilistic and can be wrong (false positives / false negatives).
- The system does **not** fetch live websites by default; it prioritises dataset-backed or user-supplied content.
- Do not use this tool to harass, target or perform unauthorised actions against any site or person.
- Always keep MongoDB credentials out of source control and use least-privilege access.
        """
    )

    st.subheader("Technology Stack")
    st.markdown(
        """
| Layer | Technology |
|-------|------------|
| Language | Python 3.10+ |
| Web UI | Streamlit |
| Database | MongoDB (local / self-hosted) via PyMongo |
| ML | scikit-learn, XGBoost |
| NLP | TF-IDF, CountVectorizer, lexical statistics |
| HTML parsing | BeautifulSoup + lxml |
| Visualisation | Plotly, Matplotlib |
| Dataset access | Hugging Face `datasets` (streaming) |
| Serialization | joblib |
        """
    )

    st.divider()
    st.caption(
        "Intelligent URL Threat Analyzer · Defensive cybersecurity / educational use only"
    )