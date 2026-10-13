"""
Repository pattern for the five logical MongoDB collections.

Each repository encapsulates common CRUD, pagination and safe query patterns
so that Streamlit tabs never issue raw queries.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from pymongo import ASCENDING, DESCENDING, ReturnDocument
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError, PyMongoError

from config.settings import settings
from config.constants import LABEL_BENIGN, LABEL_PHISHING
from src.db.connection import get_collection

logger = logging.getLogger(__name__)


def _paginate(
    collection: Collection,
    query: Dict[str, Any],
    page: int = 1,
    page_size: int = 50,
    sort: Optional[List[Tuple[str, int]]] = None,
    projection: Optional[Dict[str, int]] = None,
) -> Dict[str, Any]:
    """
    Generic pagination that never loads the full result set.
    """
    page = max(1, page)
    page_size = min(max(1, page_size), settings.MAX_PAGE_SIZE)

    total = collection.count_documents(query)
    cursor = collection.find(query, projection=projection)
    if sort:
        cursor = cursor.sort(sort)
    cursor = cursor.skip((page - 1) * page_size).limit(page_size)

    items = list(cursor)
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size if page_size else 0,
    }


class SourceRepository:
    def __init__(self, collection_name: Optional[str] = None):
        self.coll = get_collection(collection_name or settings.COLLECTION_SOURCE)

    def count(self, query: Optional[Dict] = None) -> int:
        return self.coll.count_documents(query or {})

    def estimated_count(self) -> int:
        return self.coll.estimated_document_count()

    def find_by_sha256(self, sha256: str) -> Optional[Dict]:
        return self.coll.find_one({"sha256": sha256})

    def find_by_url(self, url: str) -> Optional[Dict]:
        return self.coll.find_one({"url": url})

    def search(
        self,
        label: Optional[str] = None,
        lang: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        url_contains: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        query: Dict[str, Any] = {}
        if label in (LABEL_BENIGN, LABEL_PHISHING):
            query["label"] = label
        if lang:
            query["lang"] = lang
        if date_from or date_to:
            query["date"] = {}
            if date_from:
                query["date"]["$gte"] = date_from
            if date_to:
                query["date"]["$lte"] = date_to
        if url_contains:
            query["url"] = {"$regex": url_contains, "$options": "i"}

        # Exclude heavy html field by default for list views
        projection = {"html": 0}
        return _paginate(
            self.coll,
            query,
            page=page,
            page_size=page_size,
            sort=[("date", DESCENDING)],
            projection=projection,
        )

    def get_record(self, sha256: str, include_html: bool = False) -> Optional[Dict]:
        projection = None if include_html else {"html": 0}
        return self.coll.find_one({"sha256": sha256}, projection=projection)

    def label_distribution(self) -> Dict[str, int]:
        pipeline = [{"$group": {"_id": "$label", "count": {"$sum": 1}}}]
        result = {r["_id"]: r["count"] for r in self.coll.aggregate(pipeline)}
        return {
            LABEL_BENIGN: result.get(LABEL_BENIGN, 0),
            LABEL_PHISHING: result.get(LABEL_PHISHING, 0),
        }


class FeatureRepository:
    def __init__(self, collection_name: Optional[str] = None):
        self.coll = get_collection(collection_name or settings.COLLECTION_FEATURES)

    def upsert_features(self, sha256: str, features: Dict[str, Any]) -> None:
        doc = {
            "sha256": sha256,
            "features": features,
            "updated_at": datetime.now(timezone.utc),
        }
        self.coll.update_one(
            {"sha256": sha256},
            {"$set": doc},
            upsert=True,
        )

    def get_features(self, sha256: str) -> Optional[Dict]:
        return self.coll.find_one({"sha256": sha256})


class PredictionRepository:
    def __init__(self, collection_name: Optional[str] = None):
        self.coll = get_collection(collection_name or settings.COLLECTION_PREDICTIONS)

    def insert_prediction(self, record: Dict[str, Any]) -> str:
        """
        Insert a prediction document.
        Expected keys: url, predicted_label, confidence, model_name,
                       model_version, evidence, timestamp, ...
        """
        record = dict(record)
        record.setdefault("timestamp", datetime.now(timezone.utc))
        result = self.coll.insert_one(record)
        return str(result.inserted_id)

    def list_history(
        self,
        page: int = 1,
        page_size: int = 50,
        label: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        query: Dict[str, Any] = {}
        if label:
            query["predicted_label"] = label
        if model_name:
            query["model_name"] = model_name
        return _paginate(
            self.coll,
            query,
            page=page,
            page_size=page_size,
            sort=[("timestamp", DESCENDING)],
        )

    def clear_history(self) -> int:
        """Delete all prediction history. Returns deleted count."""
        result = self.coll.delete_many({})
        return result.deleted_count

    def count(self) -> int:
        return self.coll.estimated_document_count()


class ModelMetadataRepository:
    def __init__(self, collection_name: Optional[str] = None):
        self.coll = get_collection(collection_name or settings.COLLECTION_MODELS)

    def save_metadata(self, metadata: Dict[str, Any]) -> str:
        metadata = dict(metadata)
        metadata["saved_at"] = datetime.now(timezone.utc)
        result = self.coll.insert_one(metadata)
        return str(result.inserted_id)

    def get_latest(self, model_name: Optional[str] = None) -> Optional[Dict]:
        query = {"model_name": model_name} if model_name else {}
        return self.coll.find_one(query, sort=[("saved_at", DESCENDING)])

    def list_models(self) -> List[Dict]:
        return list(self.coll.find().sort("saved_at", DESCENDING))


class EvaluationRepository:
    def __init__(self, collection_name: Optional[str] = None):
        self.coll = get_collection(collection_name or settings.COLLECTION_EVALUATION)

    def save_evaluation(self, report: Dict[str, Any]) -> str:
        report = dict(report)
        report["saved_at"] = datetime.now(timezone.utc)
        result = self.coll.insert_one(report)
        return str(result.inserted_id)

    def get_latest(self, model_name: Optional[str] = None) -> Optional[Dict]:
        query = {"model_name": model_name} if model_name else {}
        return self.coll.find_one(query, sort=[("saved_at", DESCENDING)])

    def list_evaluations(self, limit: int = 20) -> List[Dict]:
        return list(
            self.coll.find().sort("saved_at", DESCENDING).limit(limit)
        )