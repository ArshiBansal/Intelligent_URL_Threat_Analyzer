# src/data/ingest.py
"""
Ingestion of PhreshPhish dataset into MongoDB.

Memory-safe design:
- Streams via Hugging Face `datasets` (streaming=True)
- Truncates HTML before any write
- Modest batch size for bulk writes
- Upserts by sha256 → safe to re-run

Usage:
    python scripts/02_ingest_to_mongodb.py --split train --max-samples 50000 --batch-size 100
"""

from __future__ import annotations

import gc
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

# 200k chars is enough for HTML features and much safer on laptops than 500k+
_MAX_HTML_CHARS = 200_000
_GC_EVERY = 5_000  # force GC every N records on long runs


def _normalize_record(raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        sha256 = raw.get("sha256")
        url = raw.get("url")
        label = raw.get("label")

        if not sha256 or not url or label not in (LABEL_BENIGN, LABEL_PHISHING):
            return None

        html = raw.get("html")
        if isinstance(html, str):
            if len(html) > _MAX_HTML_CHARS:
                html = html[:_MAX_HTML_CHARS]
        elif html is not None:
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
    logger.info(
        "Loading %s (split=%s, max_samples=%s) streaming…",
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
    batch_size: int = 100,
    max_samples: Optional[int] = None,
    collection_name: Optional[str] = None,
    dry_run: bool = False,
) -> Dict[str, int]:
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
            del raw

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

            batch.append(
                UpdateOne(
                    {"sha256": doc["sha256"]},
                    {"$set": doc},
                    upsert=True,
                )
            )

            if len(batch) >= batch_size:
                result = _flush_batch(collection, batch)
                stats["inserted"] += result.get("upserted", 0)
                stats["updated"] += result.get("modified", 0)
                batch.clear()

            if stats["total_seen"] % _GC_EVERY == 0:
                gc.collect()

        if batch and not dry_run:
            result = _flush_batch(collection, batch)
            stats["inserted"] += result.get("upserted", 0)
            stats["updated"] += result.get("modified", 0)
            batch.clear()

    except Exception as exc:
        logger.exception(
            "Ingestion failed after %d records: %s", stats["total_seen"], exc
        )
        stats["errors"] += 1
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
        gc.collect()

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
    coll = get_collection(collection_name or settings.COLLECTION_SOURCE)
    return coll.estimated_document_count()