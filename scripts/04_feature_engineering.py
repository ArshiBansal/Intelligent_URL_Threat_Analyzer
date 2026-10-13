"""
Phase 4 – Feature engineering.

- Reads a sample (or full set) of records from MongoDB
- Extracts URL + HTML features
- Stores derived feature vectors back into the features collection
- Optionally writes a local Parquet/CSV sample for offline ML experiments

Usage:
    python scripts/04_feature_engineering.py
    python scripts/04_feature_engineering.py --max-records 10000
    python scripts/04_feature_engineering.py --export-csv data/samples/features_sample.csv
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import settings
from config.constants import LABEL_MAP, URL_FEATURE_NAMES, HTML_FEATURE_NAMES
from src.utils.helpers import setup_logging, chunked
from src.db.connection import ping, close_client, get_collection
from src.db.repositories import SourceRepository, FeatureRepository
from src.features.url_features import extract_url_features
from src.features.html_features import extract_html_features

logger = logging.getLogger("features")


def extract_and_store(
    max_records: int | None = None,
    batch_size: int = 200,
    export_csv: Path | None = None,
) -> Dict[str, int]:
    """Extract features for records and upsert into the features collection."""
    src_repo = SourceRepository()
    feat_repo = FeatureRepository()

    # Projection: we need url, html, label, sha256
    coll = get_collection(settings.COLLECTION_SOURCE)
    cursor = coll.find(
        {},
        projection={"sha256": 1, "url": 1, "html": 1, "label": 1},
        no_cursor_timeout=True,
    )

    stats = {"processed": 0, "stored": 0, "skipped": 0, "errors": 0}
    rows_for_export: List[Dict[str, Any]] = []

    try:
        pbar = tqdm(desc="Feature extraction", unit="rec")
        for doc in cursor:
            if max_records is not None and stats["processed"] >= max_records:
                break

            stats["processed"] += 1
            pbar.update(1)

            sha = doc.get("sha256")
            url = doc.get("url")
            html = doc.get("html") or ""
            label = doc.get("label")

            if not sha or not url:
                stats["skipped"] += 1
                continue

            try:
                url_feats = extract_url_features(url)
                html_feats = extract_html_features(html)
                combined = {**url_feats, **html_feats}

                feat_repo.upsert_features(sha, combined)
                stats["stored"] += 1

                if export_csv is not None:
                    row = {
                        "sha256": sha,
                        "url": url,
                        "label": label,
                        "label_id": LABEL_MAP.get(label, -1),
                        **combined,
                    }
                    rows_for_export.append(row)

            except Exception as exc:
                logger.debug("Feature extraction failed for %s: %s", sha, exc)
                stats["errors"] += 1

        pbar.close()
    finally:
        cursor.close()

    if export_csv is not None and rows_for_export:
        export_csv.parent.mkdir(parents=True, exist_ok=True)
        df = pd.DataFrame(rows_for_export)
        df.to_csv(export_csv, index=False)
        logger.info("Exported %d rows → %s", len(df), export_csv)

    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Feature engineering")
    parser.add_argument(
        "--max-records",
        type=int,
        default=None,
        help="Limit number of records (default: all)",
    )
    parser.add_argument("--batch-size", type=int, default=200)
    parser.add_argument(
        "--export-csv",
        type=Path,
        default=None,
        help="Optional path to write a CSV sample for offline training",
    )
    args = parser.parse_args()

    setup_logging()
    settings.ensure_directories()

    if not ping():
        logger.error("MongoDB unavailable at %s", settings.MONGO_URI)
        sys.exit(1)

    logger.info(
        "Starting feature extraction (max_records=%s)…",
        args.max_records or "all",
    )
    stats = extract_and_store(
        max_records=args.max_records,
        batch_size=args.batch_size,
        export_csv=args.export_csv,
    )
    logger.info("Finished: %s", stats)
    close_client()


if __name__ == "__main__":
    main()