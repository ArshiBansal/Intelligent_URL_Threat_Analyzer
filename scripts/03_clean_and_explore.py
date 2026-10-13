"""
Phase 3 – Data-quality report & exploration.

- Reads the already-ingested MongoDB collection
- Computes class distribution, missingness, language stats, date range
- Writes a JSON report to data/reports/
- Never loads the full dataset into memory

Usage:
    python scripts/03_clean_and_explore.py
    python scripts/03_clean_and_explore.py --output data/reports/quality.json
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import settings
from config.constants import DATASET_DISPLAY_NAME
from src.utils.helpers import setup_logging, safe_json_serialize
from src.db.connection import ping, close_client
from src.data.explore import (
    generate_data_quality_report,
    class_distribution,
    language_distribution,
    date_range,
    missingness_summary,
)

logger = logging.getLogger("explore")


def main() -> None:
    parser = argparse.ArgumentParser(description="Data-quality exploration")
    parser.add_argument(
        "--output",
        type=Path,
        default=settings.REPORTS_DIR / "data_quality_report.json",
    )
    args = parser.parse_args()

    setup_logging()
    settings.ensure_directories()

    if not ping():
        logger.error("MongoDB unavailable at %s", settings.MONGO_URI)
        sys.exit(1)

    logger.info("Generating data-quality report for %s…", DATASET_DISPLAY_NAME)
    report = generate_data_quality_report()

    # Extra console summary
    dist = class_distribution()
    logger.info("Class distribution: %s", dist)
    logger.info("Date range: %s", date_range())
    logger.info("Top languages: %s", language_distribution(top_n=5))
    logger.info("Missingness: %s", missingness_summary())

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(safe_json_serialize(report, indent=2))

    logger.info("Report written → %s", args.output)
    close_client()


if __name__ == "__main__":
    main()