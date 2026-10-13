"""
Phase 2 – Ingest PhreshPhish into MongoDB.

- Streams the dataset via Hugging Face datasets library
- Validates and normalises records
- Batch-upserts by sha256 (safe re-runs)
- Creates recommended indexes

Usage:
    python scripts/02_ingest_to_mongodb.py
    python scripts/02_ingest_to_mongodb.py --split train --max-samples 5000
    python scripts/02_ingest_to_mongodb.py --split test --batch-size 200
    python scripts/02_ingest_to_mongodb.py --dry-run
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import settings
from src.utils.helpers import setup_logging
from src.data.ingest import ingest_phreshphish, count_source_records
from src.db.indexes import ensure_indexes
from src.db.connection import ping, close_client

logger = logging.getLogger("ingest")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest PhreshPhish → MongoDB")
    parser.add_argument("--split", default="train", choices=["train", "test"])
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument(
        "--max-samples",
        type=int,
        default=None,
        help="Limit for testing; omit for full split",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate only – no writes",
    )
    parser.add_argument(
        "--skip-indexes",
        action="store_true",
        help="Do not create/ensure indexes",
    )
    args = parser.parse_args()

    setup_logging()
    settings.ensure_directories()

    if not ping():
        logger.error(
            "Cannot connect to MongoDB at %s. Aborting.", settings.MONGO_URI
        )
        sys.exit(1)

    if not args.skip_indexes and not args.dry_run:
        logger.info("Ensuring indexes…")
        ensure_indexes()

    logger.info(
        "Starting ingestion (split=%s, batch_size=%d, max_samples=%s, dry_run=%s)",
        args.split,
        args.batch_size,
        args.max_samples,
        args.dry_run,
    )

    stats = ingest_phreshphish(
        split=args.split,
        batch_size=args.batch_size,
        max_samples=args.max_samples,
        dry_run=args.dry_run,
    )

    logger.info("Ingestion finished: %s", stats)

    if not args.dry_run:
        total = count_source_records()
        logger.info("Source collection now contains ~%d documents", total)

    close_client()


if __name__ == "__main__":
    main()