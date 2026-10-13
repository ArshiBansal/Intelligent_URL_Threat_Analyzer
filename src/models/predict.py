"""
Inference helpers used by the Streamlit application.

Loads saved artifacts (never trains) and returns
predicted class + confidence + feature evidence.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

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
)
from src.features.url_features import extract_url_features, URLFeatureExtractor
from src.features.html_features import extract_html_features, HTMLFeatureExtractor

logger = logging.getLogger(__name__)


def _find_latest_artifact(directory: Path, pattern: str) -> Optional[Path]:
    """Return the most recently modified file matching pattern."""
    files = sorted(directory.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def load_model_artifacts(
    model_name: str = "random_forest",
    version: Optional[str] = None,
) -> Tuple[Any, Dict[str, Any], Optional[Any]]:
    """
    Load the newest (or version-specific) model, metadata and optional preprocessor.

    Returns
    -------
    (model, metadata, preprocessor_or_None)
    """
    settings.ensure_directories()
    version = version or CURRENT_MODEL_VERSION

    model_path = _find_latest_artifact(
        settings.MODELS_DIR, f"{model_name}_{version}_*.joblib"
    )
    if model_path is None:
        # fallback: any version of this model
        model_path = _find_latest_artifact(settings.MODELS_DIR, f"{model_name}_*.joblib")

    if model_path is None:
        raise FileNotFoundError(
            f"No saved model found for '{model_name}'. "
            "Run the offline training scripts first."
        )

    meta_path = model_path.with_suffix(".json")
    # metadata may live in METADATA_DIR with same stem
    if not meta_path.exists():
        meta_path = settings.METADATA_DIR / model_path.name.replace(".joblib", ".json")

    model = joblib.load(model_path)
    metadata = {}
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

    # optional preprocessor
    prep_path = _find_latest_artifact(
        settings.PREPROCESSORS_DIR, f"preprocessor_{model_name}_*.joblib"
    )
    preprocessor = joblib.load(prep_path) if prep_path else None

    logger.info("Loaded model %s from %s", model_name, model_path)
    return model, metadata, preprocessor


def _build_feature_vector(
    url: str,
    html: Optional[str] = None,
    feature_names: Optional[List[str]] = None,
) -> Tuple[np.ndarray, Dict[str, float]]:
    """
    Construct a numeric feature vector from URL (+ optional HTML).
    Returns (vector, feature_dict) for evidence display.
    """
    url_feats = extract_url_features(url)
    html_feats = extract_html_features(html or "")

    combined = {**url_feats, **html_feats}

    if feature_names is None:
        feature_names = sorted(combined.keys())

    vector = np.array([[combined.get(name, 0.0) for name in feature_names]], dtype=np.float32)
    return vector, combined


def predict_url(
    url: str,
    html: Optional[str] = None,
    model_name: str = "random_forest",
    threshold: Optional[float] = None,
    return_evidence: bool = True,
) -> Dict[str, Any]:
    """
    High-level inference used by the Streamlit "URL Threat Analyzer" tab.

    Returns a dictionary containing:
    - predicted_label (str)
    - predicted_class (int)
    - confidence (float | None)
    - threshold used
    - model_name / version
    - evidence (feature dict) if requested
    - disclaimer
    """
    model, metadata, preprocessor = load_model_artifacts(model_name)

    threshold = threshold or metadata.get("default_threshold", DEFAULT_THRESHOLD)
    feature_names = metadata.get("feature_names")  # may be None

    X, evidence = _build_feature_vector(url, html, feature_names)

    if preprocessor is not None:
        X = preprocessor.transform(X)

    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X)[0]
        confidence = float(max(proba))
        pred_class = int(np.argmax(proba))
        # apply threshold on positive class if binary
        if len(proba) == 2:
            pred_class = 1 if proba[1] >= threshold else 0
            confidence = float(proba[pred_class])
    else:
        pred_class = int(model.predict(X)[0])
        confidence = None

    label = LABEL_INVERSE_MAP.get(pred_class, "unknown")
    display = LABEL_DISPLAY.get(label, label)

    result = {
        "url": url,
        "predicted_label": label,
        "predicted_display": display,
        "predicted_class": pred_class,
        "confidence": confidence,
        "threshold": threshold,
        "model_name": model_name,
        "model_version": metadata.get("version", CURRENT_MODEL_VERSION),
        "disclaimer": DISCLAIMER_BENIGN if pred_class == 0 else DISCLAIMER_PHISHING,
    }

    if return_evidence:
        # keep only the most interesting non-zero signals for UI
        interesting = {
            k: v for k, v in evidence.items() if isinstance(v, (int, float)) and v != 0
        }
        result["evidence"] = dict(sorted(interesting.items(), key=lambda x: -abs(x[1]))[:30])

    return result