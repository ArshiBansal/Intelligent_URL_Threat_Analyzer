"""
MongoDB data-access layer for Intelligent URL Threat Analyzer.
Uses PyMongo only (local / self-hosted MongoDB – no Atlas).
"""

from .connection import get_client, get_db, get_collection, close_client
from .repositories import (
    SourceRepository,
    FeatureRepository,
    PredictionRepository,
    ModelMetadataRepository,
    EvaluationRepository,
)
from .indexes import ensure_indexes

__all__ = [
    "get_client",
    "get_db",
    "get_collection",
    "close_client",
    "SourceRepository",
    "FeatureRepository",
    "PredictionRepository",
    "ModelMetadataRepository",
    "EvaluationRepository",
    "ensure_indexes",
]