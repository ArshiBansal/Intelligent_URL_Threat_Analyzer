#!/usr/bin/env python3
"""
Phase 7 – Final evaluation and model selection.

Loads artifacts for every name in SUPPORTED_MODEL_NAMES (six classical models),
scores them on a held-out split, writes model_selection.json, and optionally
registers the winner in MongoDB.

Usage:
    python scripts/07_evaluate_and_select.py
    python scripts/07_evaluate_and_select.py --prefer logistic_regression --metric f1
    python scripts/07_evaluate_and_select.py --metric pr_auc --register-mongo
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from sklearn.model_selection import train_test_split

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import settings
from config.constants import (
    SUPPORTED_MODEL_NAMES,
    CURRENT_MODEL_VERSION,
    DEFAULT_THRESHOLD,
)
from src.utils.helpers import setup_logging, safe_json_serialize
from src.db.connection import ping, close_client
from src.db.repositories import EvaluationRepository, ModelMetadataRepository
from src.models.predict import load_model_artifacts
from src.models.evaluate import full_evaluation_report, save_evaluation_report
from scripts.ml_feature_utils import load_feature_matrix, FEATURE_NAMES

logger = logging.getLogger("evaluate_select")


def select_best(
    results: Dict[str, Dict[str, Any]],
    prefer: Optional[str] = None,
    metric: str = "f1",
) -> str:
    """Return the best model name by metric, or `prefer` if present."""
    if prefer and prefer in results:
        logger.info("Forced preference: %s", prefer)
        return prefer

    best_name: Optional[str] = None
    best_score = -1.0

    for name, payload in results.items():
        m = payload.get("test") or payload.get("metrics") or {}
        score = m.get(metric)
        if score is None:
            continue
        score = float(score)
        if score > best_score:
            best_score = score
            best_name = name

    if best_name is None:
        return next(iter(results.keys()))
    logger.info("Best by %s = %.4f → %s", metric, best_score, best_name)
    return best_name


def _leaderboard(
    results: Dict[str, Dict[str, Any]],
    metric: str = "f1",
) -> list:
    """Sorted list of {model, metric, f1, roc_auc, pr_auc} for the report."""
    rows = []
    for name, payload in results.items():
        m = payload.get("test") or {}
        rows.append(
            {
                "model": name,
                metric: m.get(metric),
                "f1": m.get("f1"),
                "roc_auc": m.get("roc_auc"),
                "pr_auc": m.get("pr_auc"),
                "balanced_accuracy": m.get("balanced_accuracy"),
                "recall_phish": m.get("recall_phish"),
            }
        )
    rows.sort(key=lambda r: (r.get(metric) is not None, r.get(metric) or 0), reverse=True)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate & select final model")
    parser.add_argument("--max-records", type=int, default=20000)
    parser.add_argument(
        "--prefer",
        default=None,
        help="Force this model if its artifact exists",
    )
    parser.add_argument(
        "--metric",
        default="f1",
        choices=["f1", "roc_auc", "pr_auc", "recall_phish", "balanced_accuracy"],
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=settings.REPORTS_DIR / "model_selection.json",
    )
    parser.add_argument(
        "--register-mongo",
        action="store_true",
        help="Write selected model metadata & evaluation into MongoDB",
    )
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--test-size", type=float, default=0.2)
    args = parser.parse_args()

    if args.prefer and args.prefer not in SUPPORTED_MODEL_NAMES:
        logger.error(
            "--prefer=%s is not in SUPPORTED_MODEL_NAMES: %s",
            args.prefer,
            SUPPORTED_MODEL_NAMES,
        )
        sys.exit(1)

    setup_logging()
    settings.ensure_directories()

    if not ping():
        logger.error("MongoDB unavailable")
        sys.exit(1)

    X, y, _ = load_feature_matrix(max_records=args.max_records)
    if len(y) < 200:
        logger.error("Not enough samples for evaluation (%d)", len(y))
        sys.exit(1)

    if len(set(y.tolist())) < 2:
        logger.error("Need both classes in the evaluation matrix")
        sys.exit(1)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=args.test_size,
        random_state=args.random_state,
        stratify=y,
    )

    results: Dict[str, Dict[str, Any]] = {}
    for name in SUPPORTED_MODEL_NAMES:
        try:
            model, meta, _ = load_model_artifacts(name)
            report = full_evaluation_report(
                model, X_train, y_train, X_test, y_test, model_name=name
            )
            results[name] = report
            save_evaluation_report(report, filename=f"eval_{name}_final.json")
            logger.info(
                "%s | test F1=%.4f  ROC-AUC=%s  PR-AUC=%s",
                name,
                report.get("test", {}).get("f1") or 0,
                report.get("test", {}).get("roc_auc"),
                report.get("test", {}).get("pr_auc"),
            )
        except FileNotFoundError:
            logger.warning("No artifact found for %s – skipping", name)
        except Exception as exc:
            logger.warning("Evaluation failed for %s: %s", name, exc)

    if not results:
        logger.error("No models evaluated. Run 06_ml_experiments.py first.")
        sys.exit(1)

    best = select_best(results, prefer=args.prefer, metric=args.metric)
    board = _leaderboard(results, metric=args.metric)

    logger.info("Selected model: %s (by %s)", best, args.metric)
    for row in board:
        logger.info(
            "  rank %-28s F1=%s  ROC-AUC=%s  PR-AUC=%s",
            row["model"],
            row.get("f1"),
            row.get("roc_auc"),
            row.get("pr_auc"),
        )

    selection = {
        "selected_model": best,
        "selection_metric": args.metric,
        "version": CURRENT_MODEL_VERSION,
        "threshold": DEFAULT_THRESHOLD,
        "feature_names": list(FEATURE_NAMES),
        "feature_dim": len(FEATURE_NAMES),
        "n_samples": int(len(y)),
        "n_test": int(len(y_test)),
        "supported_models": list(SUPPORTED_MODEL_NAMES),
        "leaderboard": board,
        "results": results,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(safe_json_serialize(selection, indent=2))
    logger.info("Selection report → %s", args.output)

    if args.register_mongo:
        try:
            ModelMetadataRepository().save_metadata(
                {
                    "model_name": best,
                    "version": CURRENT_MODEL_VERSION,
                    "selection_metric": args.metric,
                    "is_selected": True,
                    "feature_names": list(FEATURE_NAMES),
                    "feature_dim": len(FEATURE_NAMES),
                }
            )
            EvaluationRepository().save_evaluation(results[best])
            logger.info("Registered selected model in MongoDB")
        except Exception as exc:
            logger.warning("MongoDB registration failed: %s", exc)

    close_client()
    logger.info("Phase 7 complete.")


if __name__ == "__main__":
    main()