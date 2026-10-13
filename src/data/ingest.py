# src/data/ingest.py
"""
Ingestion of PhreshPhish dataset into MongoDB.

Memory-safe design:
- Streams via Hugging Face `datasets` (streaming=True) – never loads full split.
- Truncates HTML to _MAX_HTML_CHARS before any processing or write.
- Small default batch size for MongoDB bulk writes.
- Upserts by sha256 → safe to re-run; already-ingested rows are updated, not duplicated.

Usage (via scripts/02_ingest_to_mongodb.py):
    python scripts/02_ingest_to_mongodb.py --split train --max-samples 50000 --batch-size 100
    python scripts/02_ingest_to_mongodb.py --split test  --max-samples 20000
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Generator, List, Optional

from datasets import load_dataset, IterableDataset
from pymongo import UpdateOne
from pymongo.collection import Collection
from pymongo.errors import BulkWriteError, PyMongoError
from tqdm import tqdm

from config.settings import settings
from config.constants import (
    DATASET_HF_ID,
    DATASET_DISPLAY_NAME,
    LABEL_BENIGN,
    LABEL_PHISHING,
)
from src.db.connection import get_collection
from src.data.validate import validate_record

logger = logging.getLogger(__name__)

_MAX_HTML_CHARS = 350_000


def _normalize_record(raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Convert a raw Hugging Face example into a clean MongoDB document.
    Returns None if the record is invalid (missing sha256/url/label).
    HTML is truncated to _MAX_HTML_CHARS to keep RAM and disk under control.
    """
    try:
        sha256 = raw.get("sha256")
        url = raw.get("url")
        label = raw.get("label")

        if not sha256 or not url or label not in (LABEL_BENIGN, LABEL_PHISHING):
            return None

        html = raw.get("html")
        if isinstance(html, str) and len(html) > _MAX_HTML_CHARS:
            html = html[:_MAX_HTML_CHARS]
        elif html is not None and not isinstance(html, str):
            html = str(html)[:_MAX_HTML_CHARS]

        return {
            "sha256": str(sha256).strip().lower(),
            "url": str(url).strip(),
            "label": label,
            "target": raw.get("target"),
            "date": raw.get("date"),
            "lang": raw.get("lang"),
            "lang_score": raw.get("lang_score"),
            "html": html,
            "ingested_at": datetime.now(timezone.utc),
            "dataset_name": DATASET_DISPLAY_NAME,
            "dataset_hf_id": DATASET_HF_ID,
            "source_revision": str(raw.get("_revision") or "unknown"),
        }
    except Exception as exc:
        logger.debug("Failed to normalize record: %s", exc)
        return None


def _stream_dataset(
    split: str = "train",
    max_samples: Optional[int] = None,
) -> Generator[Dict[str, Any], None, None]:
    """
    Stream PhreshPhish examples using Hugging Face datasets library.
    streaming=True avoids loading the entire split into memory.
    """
    logger.info(
        "Loading %s (split=%s, max_samples=%s) via Hugging Face datasets "
        "(streaming=True)…",
        DATASET_HF_ID,
        split,
        max_samples if max_samples is not None else "all",
    )

    ds: IterableDataset = load_dataset(
        DATASET_HF_ID,
        split=split,
        streaming=True,
        token=settings.HF_TOKEN,
    )

    count = 0
    for example in ds:
        if max_samples is not None and count >= max_samples:
            break
        yield example
        count += 1


def _flush_batch(collection: Collection, batch: List[UpdateOne]) -> Dict[str, int]:
    """Execute a bulk write and return simple counters. Safe on partial failure."""
    try:
        result = collection.bulk_write(batch, ordered=False)
        return {
            "upserted": result.upserted_count,
            "modified": result.modified_count,
        }
    except BulkWriteError as bwe:
        logger.warning("Bulk write partial failure: %s", bwe.details)
        return {
            "upserted": bwe.details.get("nUpserted", 0),
            "modified": bwe.details.get("nModified", 0),
        }
    except PyMongoError as exc:
        logger.error("MongoDB write error: %s", exc)
        raise


def ingest_phreshphish(
    split: str = "train",
    batch_size: int = 200,
    max_samples: Optional[int] = None,
    collection_name: Optional[str] = None,
    dry_run: bool = False,
) -> Dict[str, int]:
    """
    Main ingestion entry point. Safe to re-run (upsert by sha256).

    Parameters
    ----------
    split : str
        Hugging Face split ("train" or "test").
    batch_size : int
        Number of documents per MongoDB bulk write.
        Keep modest (100–500) to limit peak memory.
    max_samples : int | None
        Hard limit on rows processed. Use this on laptops
        (e.g. 30000–100000). None = entire split (can still OOM
        on very large HTML even with truncation).
    collection_name : str | None
        Override default source collection name.
    dry_run : bool
        If True, only validate and count – no MongoDB writes.

    Returns
    -------
    dict with counters: total_seen, valid, inserted, updated, skipped, errors
    """
    coll_name = collection_name or settings.COLLECTION_SOURCE
    collection: Collection = get_collection(coll_name)

    stats = {
        "total_seen": 0,
        "valid": 0,
        "inserted": 0,
        "updated": 0,
        "skipped": 0,
        "errors": 0,
    }

    batch: List[UpdateOne] = []
    pbar = tqdm(desc=f"Ingesting {split}", unit="rec")

    try:
        for raw in _stream_dataset(split=split, max_samples=max_samples):
            stats["total_seen"] += 1
            pbar.update(1)

            # Drop heavy raw reference ASAP after normalize
            doc = _normalize_record(raw)
            del raw  # help GC on large HTML rows

            if doc is None:
                stats["skipped"] += 1
                continue

            is_valid, _ = validate_record(doc, require_html=False)
            if not is_valid:
                stats["skipped"] += 1
                continue

            stats["valid"] += 1

            if dry_run:
                continue

            # Upsert by sha256 → idempotent / safe re-runs
            op = UpdateOne(
                {"sha256": doc["sha256"]},
                {"$set": doc},
                upsert=True,
            )
            batch.append(op)

            if len(batch) >= batch_size:
                result = _flush_batch(collection, batch)
                stats["inserted"] += result.get("upserted", 0)
                stats["updated"] += result.get("modified", 0)
                batch.clear()

        # Final partial batch
        if batch and not dry_run:
            result = _flush_batch(collection, batch)
            stats["inserted"] += result.get("upserted", 0)
            stats["updated"] += result.get("modified", 0)
            batch.clear()

    except Exception as exc:
        logger.exception("Ingestion failed after %d records: %s", stats["total_seen"], exc)
        stats["errors"] += 1
        # Flush whatever we still hold so progress is not lost
        if batch and not dry_run:
            try:
                result = _flush_batch(collection, batch)
                stats["inserted"] += result.get("upserted", 0)
                stats["updated"] += result.get("modified", 0)
            except Exception:
                pass
        raise
    finally:
        pbar.close()

    logger.info(
        "Ingestion finished | seen=%d valid=%d inserted=%d updated=%d skipped=%d errors=%d",
        stats["total_seen"],
        stats["valid"],
        stats["inserted"],
        stats["updated"],
        stats["skipped"],
        stats["errors"],
    )
    return stats


def count_source_records(collection_name: Optional[str] = None) -> int:
    """Quick count of documents in the source collection."""
    coll = get_collection(collection_name or settings.COLLECTION_SOURCE)
    return coll.estimated_document_count()