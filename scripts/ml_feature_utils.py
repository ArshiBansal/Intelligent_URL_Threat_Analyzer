"""
Shared feature-matrix loader used by offline ML scripts (06, 07, 08).

Builds a numeric feature matrix from URL + HTML features stored in MongoDB.
Never loads the full dataset into memory; supports a max_records limit.
"""

from __future__ import annotations

import logging
from typing import List, Optional, Tuple

import numpy as np
from tqdm import tqdm

from config.settings import settings
from config.constants import (
    LABEL_MAP,
    LABEL_BENIGN,
    LABEL_PHISHING,
    URL_FEATURE_NAMES,
    HTML_FEATURE_NAMES,
)
from src.db.connection import get_collection
from src.features.url_features import extract_url_features
from src.features.html_features import extract_html_features

logger = logging.getLogger(__name__)

FEATURE_NAMES = URL_FEATURE_NAMES + HTML_FEATURE_NAMES


def load_feature_matrix(
    max_records: Optional[int] = 15000,
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Build a numeric feature matrix from the source collection.

    Parameters
    ----------
    max_records : int | None
        Maximum number of documents to process. None = no limit.

    Returns
    -------
    X : np.ndarray of shape (n_samples, n_features)
    y : np.ndarray of shape (n_samples,) with 0/1 labels
    sha256_list : list of sha256 strings (same order as rows)
    """
    coll = get_collection(settings.COLLECTION_SOURCE)
    cursor = coll.find(
        {"label": {"$in": [LABEL_BENIGN, LABEL_PHISHING]}},
        projection={"sha256": 1, "url": 1, "html": 1, "label": 1},
        no_cursor_timeout=True,
    )

    rows: List[List[float]] = []
    labels: List[int] = []
    shas: List[str] = []

    try:
        pbar = tqdm(desc="Building feature matrix", unit="rec")
        for i, doc in enumerate(cursor):
            if max_records is not None and i >= max_records:
                break

            url = doc.get("url")
            label = LABEL_MAP.get(doc.get("label"))
            if not url or label is None:
                continue

            html = doc.get("html") or ""
            feats = {
                **extract_url_features(url),
                **extract_html_features(html),
            }
            rows.append([feats.get(name, 0.0) for name in FEATURE_NAMES])
            labels.append(label)
            shas.append(doc.get("sha256", ""))
            pbar.update(1)
        pbar.close()
    finally:
        cursor.close()

    X = np.array(rows, dtype=np.float32)
    y = np.array(labels, dtype=np.int32)

    logger.info(
        "Feature matrix ready | shape=%s | class counts=%s",
        X.shape,
        np.bincount(y) if len(y) else "empty",
    )
    return X, y, shas