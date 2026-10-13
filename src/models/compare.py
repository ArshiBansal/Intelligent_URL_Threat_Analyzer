"""
Comparison utilities for the required ≥4 ML approaches
and ≥4 text-representation approaches.
Produces side-by-side metrics ready for the Model Performance tab
and for offline experiment reports.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import numpy as np
from sklearn.model_selection import train_test_split

from config.constants import SUPPORTED_MODEL_NAMES
from src.models.train import train_model
from src.models.evaluate import evaluate_model, full_evaluation_report
from src.features.text_features import TextFeatureExtractor

logger = logging.getLogger(__name__)


def compare_models(
    X: np.ndarray,
    y: np.ndarray,
    model_names: Optional[List[str]] = None,
    test_size: float = 0.2,
    random_state: int = 42,
    threshold: float = 0.5,
) -> Dict[str, Dict[str, Any]]:
    """
    Train and evaluate every requested classical model on the same split.
    Returns a dictionary keyed by model name containing full metrics.
    """
    names = model_names or SUPPORTED_MODEL_NAMES
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    comparison = {}
    for name in names:
        logger.info("Comparing model: %s", name)
        model, meta = train_model(
            X_train, y_train, model_name=name, test_size=0.0, random_state=random_state
        )
        # train_model with test_size=0 uses whole X_train; we evaluate on held-out
        report = full_evaluation_report(
            model, X_train, y_train, X_test, y_test, model_name=name, threshold=threshold
        )
        comparison[name] = {
            "metadata": meta,
            "metrics": report,
        }
    return comparison


def compare_text_approaches(
    texts: List[str],
    y: np.ndarray,
    methods: Optional[List[str]] = None,
    test_size: float = 0.2,
    random_state: int = 42,
    classifier_name: str = "logistic_regression",
) -> Dict[str, Dict[str, Any]]:
    """
    Compare at least four classical text representations:
    tfidf_word, tfidf_char, bow, lexical (and optionally union).
    Each is paired with the same downstream classifier for fairness.
    """
    methods = methods or ["tfidf_word", "tfidf_char", "bow", "lexical"]
    results = {}

    X_train_txt, X_test_txt, y_train, y_test = train_test_split(
        texts, y, test_size=test_size, random_state=random_state, stratify=y
    )

    for method in methods:
        logger.info("Text approach: %s", method)
        extractor = TextFeatureExtractor(method=method)
        X_train = extractor.fit_transform(X_train_txt)
        X_test = extractor.transform(X_test_txt)

        model, meta = train_model(
            X_train,
            y_train,
            model_name=classifier_name,
            test_size=0.0,
            random_state=random_state,
        )
        metrics = evaluate_model(model, X_test, y_test)
        results[method] = {
            "feature_dim": X_train.shape[1],
            "metrics": metrics,
            "metadata": meta,
        }
    return results


def summary_table(comparison: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Flatten comparison results into a list of rows
    convenient for Streamlit dataframes / Plotly tables.
    """
    rows = []
    for name, payload in comparison.items():
        m = payload.get("metrics", {}).get("test", payload.get("metrics", {}))
        rows.append(
            {
                "model": name,
                "accuracy": m.get("accuracy"),
                "balanced_accuracy": m.get("balanced_accuracy"),
                "precision": m.get("precision"),
                "recall": m.get("recall"),
                "f1": m.get("f1"),
                "roc_auc": m.get("roc_auc"),
                "pr_auc": m.get("pr_auc"),
                "f1_phish": m.get("f1_phish"),
                "recall_phish": m.get("recall_phish"),
            }
        )
    return rows