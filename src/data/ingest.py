"""
Ingestion of PhreshPhish dataset into MongoDB.

- Loads exclusively via Hugging Face `datasets` library (streaming / chunked).
- Never downloads or stores a full CSV.
- Performs basic validation, deduplication by sha256, and batch writes.
- Safe for re-runs (upsert by sha256).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Generator, Iterable, List, Optional

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
    SOURCE_FIELDS,
)
from src.db.connection import get_collection
from src.data.validate import validate_record

logger = logging.getLogger(__name__)


def _normalize_record(raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Convert a raw Hugging Face example into a clean MongoDB document.
    Returns None if the record is invalid.
    """
    try:
        # Ensure required fields exist
        sha256 = raw.get("sha256")
        url = raw.get("url")
        label = raw.get("label")

        if not sha256 or not url or label not in (LABEL_BENIGN, LABEL_PHISHING):
            return None

        doc = {
            "sha256": str(sha256).strip().lower(),
            "url": str(url).strip(),
            "label": label,
            "target": raw.get("target"),
            "date": raw.get("date"),
            "lang": raw.get("lang"),
            "lang_score": raw.get("lang_score"),
            "html": raw.get("html"),  # may be very large – stored as-is
            "ingested_at": datetime.now(timezone.utc),
            "dataset_name": DATASET_DISPLAY_NAME,
            "dataset_hf_id": DATASET_HF_ID,
            "source_revision": raw.get("_revision") or "unknown",
        }

        # Keep only known source fields + metadata
        # (extra fields from HF are ignored for safety)
        return doc
    except Exception as exc:
        logger.debug("Failed to normalize record: %s", exc)
        return None


def _stream_dataset(
    split: str = "train",
    max_samples: Optional[int] = None,
) -> Generator[Dict[str, Any], None, None]:
    """
    Stream PhreshPhish examples using Hugging Face datasets library.
    Uses streaming=True to avoid loading the entire dataset into memory.
    """
    logger.info(
        "Loading %s (split=%s) via Hugging Face datasets library (streaming)...",
        DATASET_HF_ID,
        split,
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


def ingest_phreshphish(
    split: str = "train",
    batch_size: int = 500,
    max_samples: Optional[int] = None,
    collection_name: Optional[str] = None,
    dry_run: bool = False,
) -> Dict[str, int]:
    """
    Main ingestion entry point.

    Parameters
    ----------
    split : str
        Hugging Face split ("train" or "test").
    batch_size : int
        Number of documents per MongoDB bulk write.
    max_samples : int | None
        Limit for testing / development. None = full split.
    collection_name : str | None
        Override default source collection.
    dry_run : bool
        If True, only validate and count – no writes.

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

            doc = _normalize_record(raw)
            if doc is None:
                stats["skipped"] += 1
                continue

            # Light validation before write
            is_valid, _ = validate_record(doc, require_html=False)
            if not is_valid:
                stats["skipped"] += 1
                continue

            stats["valid"] += 1

            if dry_run:
                continue

            # Upsert by sha256 (safe re-runs)
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

    except Exception as exc:
        logger.exception("Ingestion failed: %s", exc)
        stats["errors"] += 1
        raise
    finally:
        pbar.close()

    logger.info(
        "Ingestion finished | seen=%d valid=%d inserted=%d updated=%d skipped=%d",
        stats["total_seen"],
        stats["valid"],
        stats["inserted"],
        stats["updated"],
        stats["skipped"],
    )
    return stats


def _flush_batch(collection: Collection, batch: List[UpdateOne]) -> Dict[str, int]:
    """Execute a bulk write and return simple counters."""
    try:
        result = collection.bulk_write(batch, ordered=False)
        return {
            "upserted": result.upserted_count,
            "modified": result.modified_count,
        }
    except BulkWriteError as bwe:
        logger.warning("Bulk write partial failure: %s", bwe.details)
        # Still return what succeeded
        return {
            "upserted": bwe.details.get("nUpserted", 0),
            "modified": bwe.details.get("nModified", 0),
        }
    except PyMongoError as exc:
        logger.error("MongoDB write error: %s", exc)
        raise


def count_source_records(collection_name: Optional[str] = None) -> int:
    """Quick count of documents in the source collection."""
    coll = get_collection(collection_name or settings.COLLECTION_SOURCE)
    return coll.estimated_document_count()