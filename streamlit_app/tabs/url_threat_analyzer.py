"""
Tab 2 – URL Threat Analyzer (primary interactive workflow)

Accept and validate a URL, optionally accept supplied HTML,
run inference, show predicted class, confidence and safe guidance.
"""

from __future__ import annotations

import streamlit as st
from datetime import datetime, timezone

from config.constants import (
    LABEL_DISPLAY,
    DISCLAIMER_BENIGN,
    DISCLAIMER_PHISHING,
    SUPPORTED_MODEL_NAMES,
    CURRENT_MODEL_VERSION,
)
from src.utils.validation import validate_url_input, sanitize_user_input
from src.models.predict import predict_url
from src.db.repositories import PredictionRepository


def render_url_threat_analyzer() -> None:
    st.header("URL Threat Analyzer")
    st.caption(
        "Submit a URL for phishing / benign classification. "
        "This is a defensive educational tool – predictions are not definitive."
    )

    # ------------------------------------------------------------------
    # Input form
    # ------------------------------------------------------------------
    with st.form("url_analysis_form", clear_on_submit=False):
        url_input = st.text_input(
            "URL to analyse",
            placeholder="https://example.com/login",
            help="Only http:// and https:// schemes are accepted.",
        )
        html_input = st.text_area(
            "Optional HTML content (paste if available)",
            height=120,
            help="Providing HTML improves feature coverage. Leave empty to analyse URL structure only.",
        )
        model_choice = st.selectbox(
            "Model",
            options=SUPPORTED_MODEL_NAMES,
            index=SUPPORTED_MODEL_NAMES.index("random_forest")
            if "random_forest" in SUPPORTED_MODEL_NAMES
            else 0,
        )
        submitted = st.form_submit_button("Analyse URL", type="primary")

    if not submitted:
        st.info("Enter a URL and click **Analyse URL** to begin.")
        return

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    is_valid, message, normalized_url = validate_url_input(url_input)
    if not is_valid:
        st.error(message)
        return

    st.success(f"URL accepted: `{normalized_url}`")
    html_clean = sanitize_user_input(html_input) if html_input else None

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------
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
            st.info("Train models offline first (see scripts/06_ml_experiments.py).")
            return
        except Exception as exc:
            st.error(f"Inference failed: {exc}")
            return

    # ------------------------------------------------------------------
    # Results
    # ------------------------------------------------------------------
    label = result["predicted_label"]
    display = result["predicted_display"]
    confidence = result.get("confidence")
    is_phish = label == "phish"

    # Colour-coded metric
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Prediction",
            display,
            delta="Suspicious" if is_phish else "Looks safe",
            delta_color="inverse" if is_phish else "normal",
        )
    with col2:
        conf_str = f"{confidence:.1%}" if confidence is not None else "N/A"
        st.metric("Confidence", conf_str)
    with col3:
        st.metric("Model", f"{result['model_name']} ({result['model_version']})")

    # Disclaimer
    st.warning(result["disclaimer"])

    # Evidence preview (full evidence lives in the next tab)
    if result.get("evidence"):
        with st.expander("Top signals used by the model", expanded=False):
            st.json(result["evidence"])

    # ------------------------------------------------------------------
    # Persist to history (best-effort)
    # ------------------------------------------------------------------
    try:
        pred_repo = PredictionRepository()
        pred_repo.insert_prediction(
            {
                "url": normalized_url,
                "original_url": url_input.strip(),
                "predicted_label": label,
                "predicted_class": result["predicted_class"],
                "confidence": confidence,
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

    # Store in session so the Evidence tab can reuse it
    st.session_state["last_prediction"] = result