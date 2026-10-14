"""
Offline model training for Intelligent URL Threat Analyzer.

Trains six classical algorithms on reproducible splits.
Saves model + preprocessing artifacts with version metadata.
Never trains inside the Streamlit app.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import (
    ExtraTreesClassifier,
    HistGradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC
from xgboost import XGBClassifier

from config.settings import settings
from config.constants import (
    CURRENT_MODEL_VERSION,
    SUPPORTED_MODEL_NAMES,
    LABEL_MAP,
    DEFAULT_THRESHOLD,
)

logger = logging.getLogger(__name__)


def _get_estimator(name: str, random_state: int = 42):
    """Return a fresh classical estimator tuned for URL+HTML tabular features."""
    name = name.lower().strip()

    if name == "logistic_regression":
        return LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            solver="lbfgs",
            C=1.0,
            random_state=random_state,
            n_jobs=-1,
        )

    if name == "hist_gradient_boosting":
        return HistGradientBoostingClassifier(
            max_depth=6,
            learning_rate=0.08,
            max_iter=250,
            min_samples_leaf=25,
            l2_regularization=0.15,
            early_stopping=True,
            validation_fraction=0.1,
            n_iter_no_change=15,
            random_state=random_state,
        )

    if name == "extra_trees":
        return ExtraTreesClassifier(
            n_estimators=400,
            max_depth=14,
            min_samples_split=8,
            min_samples_leaf=6,
            max_features="sqrt",
            class_weight="balanced_subsample",
            random_state=random_state,
            n_jobs=-1,
        )

    if name == "random_forest":
        return RandomForestClassifier(
            n_estimators=300,
            max_depth=12,
            min_samples_split=8,
            min_samples_leaf=5,
            max_features="sqrt",
            class_weight="balanced_subsample",
            random_state=random_state,
            n_jobs=-1,
        )

    if name == "linear_svc":
        base = LinearSVC(
            class_weight="balanced",
            C=1.0,
            max_iter=8000,
            dual=False,
            random_state=random_state,
        )
        return CalibratedClassifierCV(base, method="sigmoid", cv=3)

    if name == "xgboost":
        return XGBClassifier(
            n_estimators=250,
            max_depth=5,
            learning_rate=0.06,
            min_child_weight=8,
            subsample=0.75,
            colsample_bytree=0.75,
            reg_lambda=2.0,
            reg_alpha=0.4,
            eval_metric="logloss",
            random_state=random_state,
            n_jobs=-1,
        )

    raise ValueError(
        f"Unsupported model '{name}'. Choose from {SUPPORTED_MODEL_NAMES}"
    )


def build_pipeline(
    model_name: str,
    use_url: bool = True,
    use_html: bool = True,
    text_method: Optional[str] = None,
    random_state: int = 42,
) -> Pipeline:
    """
    Build a scikit-learn Pipeline.
    Feature extraction stays outside the pipeline for flexibility.
    """
    estimator = _get_estimator(model_name, random_state=random_state)
    steps = [
        ("scaler", StandardScaler()),
        ("clf", estimator),
    ]
    return Pipeline(steps)


def train_model(
    X: np.ndarray,
    y: np.ndarray,
    model_name: str = "logistic_regression",
    test_size: float = 0.2,
    random_state: int = 42,
    sample_weight: Optional[np.ndarray] = None,
) -> Tuple[Any, Dict[str, Any]]:
    """
    Train a single model on a numeric feature matrix.

    Returns
    -------
    (fitted_pipeline, metadata_dict)
    """
    if model_name not in SUPPORTED_MODEL_NAMES:
        raise ValueError(f"model_name must be one of {SUPPORTED_MODEL_NAMES}")

    if test_size <= 0:
        X_train, y_train = X, y
        n_val = 0
    else:
        X_train, X_val, y_train, y_val = train_test_split(
            X,
            y,
            test_size=test_size,
            random_state=random_state,
            stratify=y,
        )
        n_val = int(len(X_val))

    pipeline = build_pipeline(model_name, random_state=random_state)

    fit_params: Dict[str, Any] = {}
    if sample_weight is not None:
        # Pipeline step name is "clf"
        fit_params["clf__sample_weight"] = sample_weight

    try:
        pipeline.fit(X_train, y_train, **fit_params)
    except TypeError:
        # Some estimators (e.g. CalibratedClassifierCV) reject sample_weight
        pipeline.fit(X_train, y_train)

    metadata = {
        "model_name": model_name,
        "version": CURRENT_MODEL_VERSION,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "n_train": int(len(X_train)),
        "n_val": n_val,
        "feature_dim": int(X.shape[1]),
        "label_map": LABEL_MAP,
        "default_threshold": DEFAULT_THRESHOLD,
        "random_state": random_state,
    }
    return pipeline, metadata


def train_all_models(
    X: np.ndarray,
    y: np.ndarray,
    model_names: Optional[List[str]] = None,
    test_size: float = 0.2,
    random_state: int = 42,
) -> Dict[str, Dict[str, Any]]:
    """Train all configured classical models and return a dict of results."""
    names = model_names or list(SUPPORTED_MODEL_NAMES)
    results: Dict[str, Dict[str, Any]] = {}

    for name in names:
        logger.info("Training %s ...", name)
        model, meta = train_model(
            X, y, model_name=name, test_size=test_size, random_state=random_state
        )
        results[name] = {"model": model, "metadata": meta}
        logger.info("Finished %s", name)

    return results


def save_artifacts(
    model: Any,
    metadata: Dict[str, Any],
    preprocessor: Optional[Any] = None,
    model_dir: Optional[Path] = None,
    preprocessor_dir: Optional[Path] = None,
    metadata_dir: Optional[Path] = None,
) -> Dict[str, str]:
    """
    Persist model, optional preprocessor and metadata with versioned names.
    Returns paths of written files.
    """
    model_dir = model_dir or settings.MODELS_DIR
    preprocessor_dir = preprocessor_dir or settings.PREPROCESSORS_DIR
    metadata_dir = metadata_dir or settings.METADATA_DIR

    settings.ensure_directories()

    name = metadata["model_name"]
    version = metadata.get("version", CURRENT_MODEL_VERSION)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    model_path = model_dir / f"{name}_{version}_{stamp}.joblib"
    meta_path = metadata_dir / f"{name}_{version}_{stamp}.json"

    joblib.dump(model, model_path)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, default=str)

    paths = {"model": str(model_path), "metadata": str(meta_path)}

    if preprocessor is not None:
        prep_path = (
            preprocessor_dir / f"preprocessor_{name}_{version}_{stamp}.joblib"
        )
        joblib.dump(preprocessor, prep_path)
        paths["preprocessor"] = str(prep_path)

    logger.info("Artifacts saved: %s", paths)
    return paths