"""
Index creation for query performance and uniqueness guarantees.

Indexes are created idempotently (safe to run multiple times).
"""

from __future__ import annotations

import logging
from typing import List, Tuple

from pymongo import ASCENDING, DESCENDING
from pymongo.collection import Collection
from pymongo.errors import OperationFailure

from config.settings import settings
from src.db.connection import get_collection

logger = logging.getLogger(__name__)


def _create_index_safe(
    collection: Collection,
    keys: List[Tuple[str, int]],
    **kwargs,
) -> None:
    """Create an index; ignore if it already exists with the same options."""
    try:
        name = collection.create_index(keys, **kwargs)
        logger.info("Index created/verified on %s: %s", collection.name, name)
    except OperationFailure as exc:
        # IndexOptionsConflict or IndexKeySpecsConflict – already exists
        if exc.code in (85, 86):
            logger.debug("Index already exists on %s – skipping", collection.name)
        else:
            logger.warning("Index creation warning on %s: %s", collection.name, exc)


def ensure_indexes() -> None:
    """
    Create all recommended indexes for the five collections.
    Safe to call at application startup or from a setup script.
    """
    src = get_collection(settings.COLLECTION_SOURCE)
    _create_index_safe(src, [("sha256", ASCENDING)], unique=True, name="idx_sha256_unique")
    _create_index_safe(src, [("url", ASCENDING)], name="idx_url")
    _create_index_safe(src, [("label", ASCENDING)], name="idx_label")
    _create_index_safe(src, [("date", DESCENDING)], name="idx_date")
    _create_index_safe(src, [("lang", ASCENDING)], name="idx_lang")
    _create_index_safe(
        src,
        [("label", ASCENDING), ("date", DESCENDING)],
        name="idx_label_date",
    )

    feat = get_collection(settings.COLLECTION_FEATURES)
    _create_index_safe(feat, [("sha256", ASCENDING)], unique=True, name="idx_feat_sha256")

    pred = get_collection(settings.COLLECTION_PREDICTIONS)
    _create_index_safe(pred, [("timestamp", DESCENDING)], name="idx_pred_ts")
    _create_index_safe(pred, [("predicted_label", ASCENDING)], name="idx_pred_label")
    _create_index_safe(pred, [("model_name", ASCENDING)], name="idx_pred_model")
    _create_index_safe(
        pred,
        [("model_name", ASCENDING), ("timestamp", DESCENDING)],
        name="idx_pred_model_ts",
    )

    meta = get_collection(settings.COLLECTION_MODELS)
    _create_index_safe(meta, [("model_name", ASCENDING)], name="idx_model_name")
    _create_index_safe(meta, [("saved_at", DESCENDING)], name="idx_model_saved")

    ev = get_collection(settings.COLLECTION_EVALUATION)
    _create_index_safe(ev, [("model_name", ASCENDING)], name="idx_eval_model")
    _create_index_safe(ev, [("saved_at", DESCENDING)], name="idx_eval_saved")

    logger.info("All indexes ensured successfully")