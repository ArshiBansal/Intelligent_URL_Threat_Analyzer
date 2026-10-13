"""
Lightweight exploration helpers for PhreshPhish data already stored in MongoDB.
Produces summary statistics and a data-quality report without loading the
entire collection into memory.
"""

from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Optional

from pymongo.collection import Collection

from config.settings import settings
from config.constants import LABEL_BENIGN, LABEL_PHISHING, DATASET_DISPLAY_NAME
from src.db.connection import get_collection

logger = logging.getLogger(__name__)


def class_distribution(
    collection_name: Optional[str] = None,
) -> Dict[str, int]:
    """
    Return count of benign vs phish records.
    Uses aggregation so it never loads all documents.
    """
    coll: Collection = get_collection(collection_name or settings.COLLECTION_SOURCE)

    pipeline = [
        {"$group": {"_id": "$label", "count": {"$sum": 1}}},
    ]
    result = list(coll.aggregate(pipeline))

    dist = {LABEL_BENIGN: 0, LABEL_PHISHING: 0}
    for row in result:
        label = row["_id"]
        if label in dist:
            dist[label] = row["count"]
    return dist


def language_distribution(
    collection_name: Optional[str] = None,
    top_n: int = 20,
) -> List[Dict[str, Any]]:
    """Top languages present in the dataset."""
    coll = get_collection(collection_name or settings.COLLECTION_SOURCE)
    pipeline = [
        {"$match": {"lang": {"$ne": None}}},
        {"$group": {"_id": "$lang", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": top_n},
    ]
    return [
        {"lang": r["_id"], "count": r["count"]}
        for r in coll.aggregate(pipeline)
    ]


def date_range(
    collection_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Earliest and latest date in the collection."""
    coll = get_collection(collection_name or settings.COLLECTION_SOURCE)
    pipeline = [
        {"$match": {"date": {"$ne": None}}},
        {
            "$group": {
                "_id": None,
                "min_date": {"$min": "$date"},
                "max_date": {"$max": "$date"},
                "count_with_date": {"$sum": 1},
            }
        },
    ]
    result = list(coll.aggregate(pipeline))
    if not result:
        return {"min_date": None, "max_date": None, "count_with_date": 0}
    return result[0]


def missingness_summary(
    collection_name: Optional[str] = None,
) -> Dict[str, int]:
    """
    Count missing / null values for key fields using aggregation.
    """
    coll = get_collection(collection_name or settings.COLLECTION_SOURCE)
    total = coll.estimated_document_count()

    fields = ["url", "label", "html", "date", "lang", "lang_score", "target", "sha256"]
    missing = {}

    for field in fields:
        count = coll.count_documents({field: {"$in": [None, ""]}})
        missing[field] = count

    missing["total_documents"] = total
    return missing


def generate_data_quality_report(
    collection_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    High-level data-quality report suitable for the Dashboard
    and for the offline exploration script.
    """
    coll_name = collection_name or settings.COLLECTION_SOURCE
    coll = get_collection(coll_name)

    total = coll.estimated_document_count()
    dist = class_distribution(coll_name)
    langs = language_distribution(coll_name, top_n=10)
    dates = date_range(coll_name)
    missing = missingness_summary(coll_name)

    # Simple HTML length stats (sample-based to avoid full scan)
    sample_size = min(5000, total)
    pipeline = [
        {"$sample": {"size": sample_size}},
        {
            "$project": {
                "html_len": {
                    "$cond": [
                        {"$eq": [{"$type": "$html"}, "string"]},
                        {"$strLenCP": "$html"},
                        0,
                    ]
                }
            }
        },
        {
            "$group": {
                "_id": None,
                "avg_html_len": {"$avg": "$html_len"},
                "max_html_len": {"$max": "$html_len"},
                "min_html_len": {"$min": "$html_len"},
            }
        },
    ]
    html_stats = list(coll.aggregate(pipeline))
    html_summary = html_stats[0] if html_stats else {}

    report = {
        "dataset_name": DATASET_DISPLAY_NAME,
        "collection": coll_name,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_documents": total,
        "class_distribution": dist,
        "benign_ratio": dist.get(LABEL_BENIGN, 0) / total if total else 0.0,
        "phishing_ratio": dist.get(LABEL_PHISHING, 0) / total if total else 0.0,
        "top_languages": langs,
        "date_range": {
            "min": str(dates.get("min_date")),
            "max": str(dates.get("max_date")),
            "records_with_date": dates.get("count_with_date", 0),
        },
        "missingness": missing,
        "html_length_sample": {
            "sample_size": sample_size,
            "avg": html_summary.get("avg_html_len"),
            "min": html_summary.get("min_html_len"),
            "max": html_summary.get("max_html_len"),
        },
    }
    return report


def sample_records(
    n: int = 10,
    label: Optional[str] = None,
    collection_name: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Return a small random sample of records (useful for UI previews).
    HTML is truncated to avoid huge payloads.
    """
    coll = get_collection(collection_name or settings.COLLECTION_SOURCE)
    query: Dict[str, Any] = {}
    if label in (LABEL_BENIGN, LABEL_PHISHING):
        query["label"] = label

    cursor = coll.aggregate(
        [
            {"$match": query},
            {"$sample": {"size": n}},
            {
                "$project": {
                    "sha256": 1,
                    "url": 1,
                    "label": 1,
                    "target": 1,
                    "date": 1,
                    "lang": 1,
                    "lang_score": 1,
                    "html_preview": {
                        "$substrCP": ["$html", 0, 2000]
                    },
                }
            },
        ]
    )
    return list(cursor)