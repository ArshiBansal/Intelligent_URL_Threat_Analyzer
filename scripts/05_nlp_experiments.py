"""
Phase 5 – NLP / text-representation experiments.

Compares at least four classical text approaches on a sample of
PhreshPhish records (TF-IDF word, TF-IDF char, Bag-of-Words, lexical).
Results are written to data/reports/ for later inspection.

Usage:
    python scripts/05_nlp_experiments.py
    python scripts/05_nlp_experiments.py --max-records 8000 --output data/reports/nlp_comparison.json
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import settings
from config.constants import LABEL_MAP, LABEL_BENIGN, LABEL_PHISHING
from src.utils.helpers import setup_logging, safe_json_serialize
from src.db.connection import ping, close_client, get_collection
from src.models.compare import compare_text_approaches, summary_table

logger = logging.getLogger("nlp_experiments")


def load_text_sample(
    max_records: int = 8000,
) -> tuple[List[str], np.ndarray]:
    """
    Load a balanced-ish sample of (text, label) pairs from MongoDB.
    Text = URL + truncated visible HTML (or URL alone if HTML missing).
    """
    coll = get_collection(settings.COLLECTION_SOURCE)
    cursor = coll.find(
        {"label": {"$in": [LABEL_BENIGN, LABEL_PHISHING]}},
        projection={"url": 1, "html": 1, "label": 1},
        no_cursor_timeout=True,
    )

    texts: List[str] = []
    labels: List[int] = []

    try:
        for i, doc in enumerate(tqdm(cursor, desc="Loading text sample", total=max_records)):
            if i >= max_records:
                break
            url = doc.get("url") or ""
            html = (doc.get("html") or "")[:3000]  # keep memory modest
            # Simple concatenation – good enough for classical vectorizers
            text = f"{url} {html}".strip()
            label = LABEL_MAP.get(doc.get("label"))
            if label is None or not text:
                continue
            texts.append(text)
            labels.append(label)
    finally:
        cursor.close()

    return texts, np.array(labels, dtype=np.int32)


def main() -> None:
    parser = argparse.ArgumentParser(description="NLP text-representation experiments")
    parser.add_argument("--max-records", type=int, default=8000)
    parser.add_argument(
        "--methods",
        nargs="+",
        default=["tfidf_word", "tfidf_char", "bow", "lexical"],
        help="Text approaches to compare",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=settings.REPORTS_DIR / "nlp_comparison.json",
    )
    args = parser.parse_args()

    setup_logging()
    settings.ensure_directories()

    if not ping():
        logger.error("MongoDB unavailable")
        sys.exit(1)

    logger.info("Loading text sample (max=%d)…", args.max_records)
    texts, y = load_text_sample(max_records=args.max_records)
    logger.info("Loaded %d samples (class balance: %s)", len(y), np.bincount(y))

    if len(y) < 100:
        logger.error("Not enough samples for meaningful experiments")
        sys.exit(1)

    logger.info("Comparing text approaches: %s", args.methods)
    results = compare_text_approaches(
        texts=texts,
        y=y,
        methods=args.methods,
        classifier_name="logistic_regression",
    )

    # Flatten for easy reading
    summary = summary_table(
        {k: {"metrics": v["metrics"]} for k, v in results.items()}
    )

    payload = {
        "n_samples": len(y),
        "methods": args.methods,
        "summary": summary,
        "full_results": {
            k: {
                "feature_dim": v["feature_dim"],
                "metrics": v["metrics"],
            }
            for k, v in results.items()
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(safe_json_serialize(payload, indent=2))

    logger.info("NLP comparison written → %s", args.output)
    for row in summary:
        logger.info(
            "  %s | F1=%.4f  ROC-AUC=%s  dim=%s",
            row["model"],
            row.get("f1") or 0,
            row.get("roc_auc"),
            results[row["model"]]["feature_dim"],
        )

    close_client()


if __name__ == "__main__":
    main()