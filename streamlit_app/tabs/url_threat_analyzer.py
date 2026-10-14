"""
Tab 2 – URL Threat Analyzer (primary interactive workflow)

Accept and validate a URL, optionally accept supplied HTML,
run inference, show predicted class, P(phish), risk band and guidance.
"""

from __future__ import annotations

from datetime import datetime, timezone

import streamlit as st

from config.constants import (
    DISCLAIMER_BENIGN,
    DISCLAIMER_PHISHING,
    SUPPORTED_MODEL_NAMES,
)
from src.utils.validation import validate_url_input, sanitize_user_input
from src.models.predict import predict_url
from src.db.repositories import PredictionRepository


def render_url_threat_analyzer() -> None:
    st.header("URL Threat Analyzer")
    st.caption(
        "Submit a URL for phishing / benign classification. "
        "This is a defensive educational tool — predictions are not definitive."
    )

    with st.form("url_analysis_form", clear_on_submit=False):
        url_input = st.text_input(
            "URL to analyse",
            placeholder="https://www.example.com/login",
            help="Prefer full URLs with https://. Only http and https are accepted.",
        )
        html_input = st.text_area(
            "Optional HTML content (paste if available)",
            height=120,
            help="Improves feature coverage. Leave empty for URL-structure-only analysis.",
        )
        model_choice = st.selectbox(
            "Model",
            options=SUPPORTED_MODEL_NAMES,
            index=(
                SUPPORTED_MODEL_NAMES.index("random_forest")
                if "random_forest" in SUPPORTED_MODEL_NAMES
                else 0
            ),
        )
        submitted = st.form_submit_button("Analyse URL", type="primary")

    if not submitted:
        st.info(
            "Enter a full URL (e.g. `https://www.google.com`) and click **Analyse URL**."
        )
        return

    is_valid, message, normalized_url = validate_url_input(url_input)
    if not is_valid:
        st.error(message)
        return

    st.success(f"URL accepted: `{normalized_url}`")
    html_clean = sanitize_user_input(html_input) if html_input else None

    with st.spinner("Running inference…"):
        try:
            result = predict_url(
                url=normalized_url,
                html=html_clean,
                model_name=model_choice,
                return_evidence=True,
            )
        except FileNotFoundError as exc:
            st.error(str(exc))
            st.info(
                "Train and export models offline first:\n\n"
                "`python scripts/06_ml_experiments.py --max-records 15000 --save-artifacts`\n\n"
                "`python scripts/07_evaluate_and_select.py`\n\n"
                "`python scripts/08_export_artifacts.py --promote`"
            )
            return
        except Exception as exc:
            st.error(f"Inference failed: {exc}")
            return

    label = result["predicted_label"]
    display = result["predicted_display"]
    confidence = result.get("confidence")
    p_phish = result.get("p_phish")
    risk = result.get("risk_band", display)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Prediction", display)
    with col2:
        st.metric("Risk band", risk)
    with col3:
        if p_phish is not None:
            st.metric("P(phish)", f"{p_phish:.1%}")
        else:
            conf_str = f"{confidence:.1%}" if confidence is not None else "N/A"
            st.metric("Confidence", conf_str)
    with col4:
        st.metric("Model", f"{result['model_name']}")

    # Guidance by band
    if risk == "Benign":
        st.success(
            "Model leans **benign**. This is **not** a guarantee the site is safe. "
            "Still verify the domain and avoid entering credentials if anything feels off."
        )
        st.caption(DISCLAIMER_BENIGN)
    elif risk == "Phishing":
        st.error(
            "Model leans **phishing**. Do not enter passwords or personal data. "
            "The model can be wrong — treat this as a warning, not a proof of malice."
        )
        st.caption(DISCLAIMER_PHISHING)
    else:
        st.warning(
            "Model is **uncertain** (middle probability band). "
            "Do not rely on this score alone. Check the domain carefully and "
            "prefer official apps/bookmarks for sensitive accounts."
        )
        st.caption(result.get("disclaimer", ""))

    st.caption(
        f"Decision threshold = {result['threshold']:.2f} · "
        f"version {result.get('model_version', '—')} · "
        f"feature dim {result.get('feature_dim', '—')}"
    )

    if result.get("evidence"):
        with st.expander("Top signals used by the model", expanded=False):
            st.json(result["evidence"])
            st.caption(
                "These are measured features, not proof of intent. "
                "Legitimate sites can share some of the same signals."
            )

    try:
        pred_repo = PredictionRepository()
        pred_repo.insert_prediction(
            {
                "url": normalized_url,
                "original_url": url_input.strip(),
                "predicted_label": label,
                "predicted_class": result["predicted_class"],
                "confidence": confidence,
                "p_phish": p_phish,
                "risk_band": risk,
                "threshold": result["threshold"],
                "model_name": result["model_name"],
                "model_version": result["model_version"],
                "evidence": result.get("evidence"),
                "timestamp": datetime.now(timezone.utc),
            }
        )
        st.caption("Prediction saved to history.")
    except Exception as exc:
        st.caption(f"Could not save to history: {exc}")

    st.session_state["last_prediction"] = result