"""
MongoDB connection management via PyMongo.

- Reads URI and database name exclusively from environment variables.
- Provides graceful handling of connection failures, timeouts and missing collections.
- Never hard-codes credentials.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Optional

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, PyMongoError

from config.settings import settings

logger = logging.getLogger(__name__)

# Module-level client (lazy)
_client: Optional[MongoClient] = None


def get_client(force_new: bool = False) -> MongoClient:
    """
    Return a singleton MongoClient.
    Raises a clear exception if the server cannot be reached.
    """
    global _client

    if _client is not None and not force_new:
        return _client

    try:
        client = MongoClient(
            settings.MONGO_URI,
            serverSelectionTimeoutMS=5000,   # fail fast
            connectTimeoutMS=5000,
            socketTimeoutMS=30000,
            maxPoolSize=50,
            retryWrites=True,
        )
        # Force a round-trip to verify connectivity
        client.admin.command("ping")
        _client = client
        logger.info("Connected to MongoDB at %s", settings.MONGO_URI)
        return _client
    except (ConnectionFailure, ServerSelectionTimeoutError) as exc:
        logger.error("Cannot connect to MongoDB: %s", exc)
        raise ConnectionError(
            f"Unable to connect to MongoDB at {settings.MONGO_URI}. "
            "Ensure the server is running and the URI is correct."
        ) from exc
    except PyMongoError as exc:
        logger.exception("Unexpected MongoDB error during connection")
        raise


def get_db(db_name: Optional[str] = None) -> Database:
    """Return the application database."""
    client = get_client()
    name = db_name or settings.MONGO_DB_NAME
    return client[name]


def get_collection(
    collection_name: str,
    db_name: Optional[str] = None,
) -> Collection:
    """
    Return a collection handle.
    Does not create the collection until the first write (MongoDB behaviour).
    """
    db = get_db(db_name)
    return db[collection_name]


def close_client() -> None:
    """Explicitly close the client (useful for scripts / tests)."""
    global _client
    if _client is not None:
        _client.close()
        _client = None
        logger.info("MongoDB client closed")


def ping() -> bool:
    """Health-check helper used by the Dashboard."""
    try:
        get_client().admin.command("ping")
        return True
    except Exception:
        return False