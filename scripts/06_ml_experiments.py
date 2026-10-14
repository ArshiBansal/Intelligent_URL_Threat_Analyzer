#!/usr/bin/env python3
"""
Phase 6 – Classical ML experiments.

Trains ≥4 algorithms on URL+HTML features and saves joblib artifacts
with feature_names in metadata (required for correct Streamlit inference).

Usage:
    python scripts/06_ml_experiments.py --max-records 15000
    python scripts/06_ml_experiments.py --max-records 20000 --models random_forest xgboost
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from sklearn.model_selection import train_test_split

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import settings
from config.constants import SUPPORTED_MODEL_NAMES
from src.utils.helpers import setup_logging, safe_json_serialize
from src.db.connection import ping, close_client
from src.models.train import train_model, save_artifacts
from src.models.evaluate import full_evaluation_report, save_evaluation_report
from src.models.compare import compare_models, summary_table
from scripts.ml_feature_utils import load_feature_matrix, FEATURE_NAMES

logger = logging.getLogger("ml_experiments")


def main() -> None:
    parser = argparse.ArgumentParser(description="Classical ML experiments")
    parser.add_argument("--max-records", type=int, default=15000)
    parser.add_argument(
        "--models",
        nargs="+",
        default=list(SUPPORTED_MODEL_NAMES),
        help="Models to train",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=settings.REPORTS_DIR / "ml_comparison.json",
    )
    parser.add_argument(
        "--no-save-artifacts",
        action="store_true",
        help="Skip writing joblib models",
    )
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--random-state", type=int, default=42)
    args = parser.parse_args()

    setup_logging()
    settings.ensure_directories()

    if not ping():
        logger.error("MongoDB unavailable")
        sys.exit(1)

    X, y, _ = load_feature_matrix(max_records=args.max_records)
    if len(y) < 200:
        logger.error("Not enough samples (%d). Ingest more data first.", len(y))
        sys.exit(1)

    n_classes = len(set(y.tolist()))
    if n_classes < 2:
        logger.error("Need both benign and phish labels; found %d class(es).", n_classes)
        sys.exit(1)

    logger.info(
        "Training models=%s | n=%d | dim=%d | features=%d",
        args.models,
        len(y),
        X.shape[1],
        len(FEATURE_NAMES),
    )

    comparison = compare_models(
        X,
        y,
        model_names=args.models,
        test_size=args.test_size,
        random_state=args.random_state,
    )

    summary = summary_table(comparison)
    full_results = {}
    for name, payload in comparison.items():
        full_results[name] = {
            "metadata": payload.get("metadata"),
            "metrics": payload.get("metrics"),
        }

    report_payload = {
        "n_samples": int(len(y)),
        "feature_dim": int(X.shape[1]),
        "feature_names": list(FEATURE_NAMES),
        "models": list(args.models),
        "summary": summary,
        "full_results": full_results,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(safe_json_serialize(report_payload, indent=2))
    logger.info("ML comparison written → %s", args.output)

    for row in summary:
        logger.info(
            "  %s | F1=%.4f  ROC-AUC=%s  PR-AUC=%s",
            row.get("model"),
            row.get("f1") or 0,
            row.get("roc_auc"),
            row.get("pr_auc"),
        )

    if not args.no_save_artifacts:
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=args.test_size,
            random_state=args.random_state,
            stratify=y,
        )
        for name in args.models:
            logger.info("Saving artifacts for %s …", name)
            # Fit on full train split (test_size=0 inside train_model)
            model, meta = train_model(
                X_train,
                y_train,
                model_name=name,
                test_size=0.0,
                random_state=args.random_state,
            )
            meta["feature_names"] = list(FEATURE_NAMES)
            meta["feature_dim"] = int(X.shape[1])
            meta["n_samples_total"] = int(len(y))
            paths = save_artifacts(model, meta)

            eval_report = full_evaluation_report(
                model,
                X_train,
                y_train,
                X_test,
                y_test,
                model_name=name,
            )
            save_evaluation_report(
                eval_report,
                filename=f"eval_{name}_{meta['version']}.json",
            )
            logger.info("  saved → %s", paths)

    close_client()
    logger.info("Phase 6 complete.")


if __name__ == "__main__":
    main()