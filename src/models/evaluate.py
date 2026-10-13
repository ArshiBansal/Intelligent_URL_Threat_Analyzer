"""
Comprehensive evaluation of classical models.
Reports precision, recall, F1, per-class metrics, confusion matrix,
balanced accuracy, PR-AUC, ROC-AUC and threshold analysis.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

from config.constants import LABEL_INVERSE_MAP, DEFAULT_THRESHOLD
from config.settings import settings

logger = logging.getLogger(__name__)


def evaluate_model(
    model: Any,
    X: np.ndarray,
    y_true: np.ndarray,
    threshold: float = DEFAULT_THRESHOLD,
    average: str = "binary",
) -> Dict[str, Any]:
    """
    Core evaluation for a binary classifier that exposes predict_proba.
    """
    if hasattr(model, "predict_proba"):
        y_proba = model.predict_proba(X)[:, 1]
        y_pred = (y_proba >= threshold).astype(int)
    else:
        y_pred = model.predict(X)
        y_proba = None

    report = classification_report(
        y_true,
        y_pred,
        target_names=[LABEL_INVERSE_MAP.get(0, "benign"), LABEL_INVERSE_MAP.get(1, "phish")],
        output_dict=True,
        zero_division=0,
    )

    metrics = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "precision_benign": report["benign"]["precision"],
        "recall_benign": report["benign"]["recall"],
        "f1_benign": report["benign"]["f1-score"],
        "precision_phish": report["phish"]["precision"],
        "recall_phish": report["phish"]["recall"],
        "f1_phish": report["phish"]["f1-score"],
        "support_benign": report["benign"]["support"],
        "support_phish": report["phish"]["support"],
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
        "threshold": threshold,
    }

    if y_proba is not None:
        try:
            metrics["roc_auc"] = float(roc_auc_score(y_true, y_proba))
        except ValueError:
            metrics["roc_auc"] = None
        try:
            metrics["pr_auc"] = float(average_precision_score(y_true, y_proba))
        except ValueError:
            metrics["pr_auc"] = None

        # Threshold analysis (F1 at different cut-offs)
        precisions, recalls, thresholds = precision_recall_curve(y_true, y_proba)
        f1_scores = 2 * (precisions * recalls) / (precisions + recalls + 1e-12)
        best_idx = int(np.nanargmax(f1_scores))
        metrics["best_f1_threshold"] = float(thresholds[best_idx]) if best_idx < len(thresholds) else threshold
        metrics["best_f1"] = float(f1_scores[best_idx])

    return metrics


def full_evaluation_report(
    model: Any,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    model_name: str = "unknown",
    threshold: float = DEFAULT_THRESHOLD,
) -> Dict[str, Any]:
    """
    Produce a complete evaluation dictionary suitable for saving
    and for the Model Performance tab.
    """
    train_metrics = evaluate_model(model, X_train, y_train, threshold=threshold)
    test_metrics = evaluate_model(model, X_test, y_test, threshold=threshold)

    report = {
        "model_name": model_name,
        "threshold": threshold,
        "train": train_metrics,
        "test": test_metrics,
        "gap_f1": train_metrics["f1"] - test_metrics["f1"],
        "gap_roc_auc": (
            (train_metrics.get("roc_auc") or 0) - (test_metrics.get("roc_auc") or 0)
        ),
    }
    return report


def save_evaluation_report(
    report: Dict[str, Any],
    output_dir: Optional[Path] = None,
    filename: Optional[str] = None,
) -> Path:
    """Persist evaluation JSON."""
    output_dir = output_dir or settings.METADATA_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    name = filename or f"eval_{report.get('model_name', 'model')}.json"
    path = output_dir / name
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    logger.info("Evaluation report saved → %s", path)
    return path


def load_evaluation_report(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)