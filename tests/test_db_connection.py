"""
Tests for MongoDB connection helpers.
These tests are skipped when MongoDB is not reachable.
"""

from __future__ import annotations

import pytest

from src.db.connection import get_client, get_db, get_collection, ping, close_client
from config.settings import settings


def mongo_available() -> bool:
    try:
        return ping()
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not mongo_available(),
    reason="MongoDB is not available – skipping DB tests",
)


class TestConnection:
    def test_ping(self):
        assert ping() is True

    def test_get_client(self):
        client = get_client()
        assert client is not None
        # Second call returns the same singleton
        assert get_client() is client

    def test_get_db(self):
        db = get_db()
        assert db.name == settings.MONGO_DB_NAME

    def test_get_collection(self):
        coll = get_collection(settings.COLLECTION_SOURCE)
        assert coll.name == settings.COLLECTION_SOURCE

    def test_close_and_reconnect(self):
        close_client()
        # Should be able to open again
        assert ping() is True
        close_client()