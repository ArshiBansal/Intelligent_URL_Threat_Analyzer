"""
Inference helpers used by the Streamlit application.

Loads saved artifacts (never trains) and returns
predicted class + confidence + feature evidence + risk band.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np

from config.settings import settings
from config.constants import (
    LABEL_INVERSE_MAP,
    LABEL_DISPLAY,
    DEFAULT_THRESHOLD,
    CURRENT_MODEL_VERSION,
    DISCLAIMER_BENIGN,
    DISCLAIMER_PHISHING,
    URL_FEATURE_NAMES,
    HTML_FEATURE_NAMES,
)
from src.features.url_features import extract_url_features
from src.features.html_features import extract_html_features

logger = logging.getLogger(__name__)

# Must match training order in scripts/ml_feature_utils.py
DEFAULT_FEATURE_NAMES: List[str] = list(URL_FEATURE_NAMES) + list(HTML_FEATURE_NAMES)

# Risk bands on P(phish) — tune after you inspect evaluation metrics
RISK_LOW = 0.35
RISK_HIGH = 0.65


def _find_latest_artifact(directory: Path, pattern: str) -> Optional[Path]:
    files = sorted(
        directory.glob(pattern),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return files[0] if files else None


def load_model_artifacts(
    model_name: str = "random_forest",
    version: Optional[str] = None,
) -> Tuple[Any, Dict[str, Any], Optional[Any]]:
    """
    Load newest model for `model_name`, with fallbacks:
    1) versioned files
    2) any model_name_*.joblib
    3) latest_model.joblib (from script 08 --promote)
    """
    settings.ensure_directories()
    version = version or CURRENT_MODEL_VERSION

    model_path = _find_latest_artifact(
        settings.MODELS_DIR, f"{model_name}_{version}_*.joblib"
    )
    if model_path is None:
        model_path = _find_latest_artifact(
            settings.MODELS_DIR, f"{model_name}_*.joblib"
        )
    if model_path is None:
        # promoted stable name
        candidate = settings.MODELS_DIR / "latest_model.joblib"
        if candidate.exists():
            model_path = candidate

    if model_path is None:
        raise FileNotFoundError(
            f"No saved model found for '{model_name}'. "
            "Run offline training first:\n"
            "  python scripts/06_ml_experiments.py --max-records 15000 --save-artifacts\n"
            "  python scripts/07_evaluate_and_select.py\n"
            "  python scripts/08_export_artifacts.py --promote"
        )

    meta_path = model_path.with_suffix(".json")
    if not meta_path.exists():
        meta_path = settings.METADATA_DIR / model_path.name.replace(".joblib", ".json")
    if not meta_path.exists():
        # promoted metadata
        latest_meta = settings.METADATA_DIR / "latest_metadata.json"
        if latest_meta.exists():
            meta_path = latest_meta

    model = joblib.load(model_path)
    metadata: Dict[str, Any] = {}
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

    prep_path = _find_latest_artifact(
        settings.PREPROCESSORS_DIR, f"preprocessor_{model_name}_*.joblib"
    )
    if prep_path is None:
        latest_prep = settings.PREPROCESSORS_DIR / "latest_preprocessor.joblib"
        if latest_prep.exists():
            prep_path = latest_prep
    preprocessor = joblib.load(prep_path) if prep_path else None

    logger.info("Loaded model %s from %s", model_name, model_path)
    return model, metadata, preprocessor


def _build_feature_vector(
    url: str,
    html: Optional[str] = None,
    feature_names: Optional[List[str]] = None,
) -> Tuple[np.ndarray, Dict[str, float]]:
    """
    Build numeric vector in the **same column order as training**.
    Never sort feature names alphabetically.
    """
    url_feats = extract_url_features(url)
    html_feats = extract_html_features(html or "")
    combined = {**url_feats, **html_feats}

    names = feature_names if feature_names else DEFAULT_FEATURE_NAMES
    vector = np.array(
        [[float(combined.get(name, 0.0)) for name in names]],
        dtype=np.float32,
    )
    return vector, combined


def _risk_band(p_phish: Optional[float], pred_class: int) -> str:
    """Map probability to a clear risk label for the UI."""
    if p_phish is None:
        return "Phishing" if pred_class == 1 else "Benign"
    if p_phish < RISK_LOW:
        return "Benign"
    if p_phish > RISK_HIGH:
        return "Phishing"
    return "Uncertain"


def predict_url(
    url: str,
    html: Optional[str] = None,
    model_name: str = "random_forest",
    threshold: Optional[float] = None,
    return_evidence: bool = True,
) -> Dict[str, Any]:
    """
    High-level inference for the URL Threat Analyzer tab.

    Returns class, P(phish), confidence, risk_band, evidence, disclaimer.
    """
    model, metadata, preprocessor = load_model_artifacts(model_name)

    threshold = float(
        threshold
        if threshold is not None
        else metadata.get("default_threshold", DEFAULT_THRESHOLD)
    )

    # Prefer feature names saved at train time; else fixed URL+HTML order
    feature_names = metadata.get("feature_names")
    if not feature_names:
        feature_names = DEFAULT_FEATURE_NAMES

    X, evidence = _build_feature_vector(url, html, feature_names)

    if preprocessor is not None:
        X = preprocessor.transform(X)

    p_phish: Optional[float] = None
    confidence: Optional[float] = None

    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X)[0]
        # Assume class 1 = phish (LABEL_MAP)
        if len(proba) >= 2:
            p_phish = float(proba[1])
            pred_class = 1 if p_phish >= threshold else 0
            confidence = float(proba[pred_class])
        else:
            pred_class = int(np.argmax(proba))
            confidence = float(max(proba))
    else:
        pred_class = int(model.predict(X)[0])

    label = LABEL_INVERSE_MAP.get(pred_class, "unknown")
    display = LABEL_DISPLAY.get(label, label)
    risk = _risk_band(p_phish, pred_class)

    result: Dict[str, Any] = {
        "url": url,
        "predicted_label": label,
        "predicted_display": display,
        "predicted_class": pred_class,
        "p_phish": p_phish,
        "confidence": confidence,
        "risk_band": risk,
        "threshold": threshold,
        "model_name": model_name,
        "model_version": metadata.get("version", CURRENT_MODEL_VERSION),
        "disclaimer": DISCLAIMER_BENIGN if pred_class == 0 else DISCLAIMER_PHISHING,
        "feature_dim": int(X.shape[1]),
    }

    if return_evidence:
        interesting = {
            k: float(v)
            for k, v in evidence.items()
            if isinstance(v, (int, float)) and v != 0
        }
        result["evidence"] = dict(
            sorted(interesting.items(), key=lambda x: -abs(x[1]))[:30]
        )

    return result