"""
Tests for URL input validation and sanitization helpers.
"""

from __future__ import annotations

import pytest

from src.utils.validation import (
    validate_url_input,
    is_safe_url_scheme,
    sanitize_user_input,
)
from config.settings import settings


class TestIsSafeUrlScheme:
    def test_https(self):
        assert is_safe_url_scheme("https://example.com") is True

    def test_http(self):
        assert is_safe_url_scheme("http://example.com") is True

    def test_ftp_rejected(self):
        assert is_safe_url_scheme("ftp://files.example.com") is False

    def test_javascript_rejected(self):
        assert is_safe_url_scheme("javascript:alert(1)") is False

    def test_no_scheme_defaults_to_http(self):
        # The helper adds http:// internally for parsing
        assert is_safe_url_scheme("example.com") is True


class TestValidateUrlInput:
    def test_empty_string(self):
        ok, msg, normalized = validate_url_input("")
        assert ok is False
        assert "empty" in msg.lower()
        assert normalized is None

    def test_none(self):
        ok, msg, normalized = validate_url_input(None)  # type: ignore
        assert ok is False
        assert normalized is None

    def test_valid_https(self):
        ok, msg, normalized = validate_url_input("https://www.example.com/path")
        assert ok is True
        assert normalized is not None
        assert normalized.startswith("https://")

    def test_valid_without_scheme(self):
        ok, msg, normalized = validate_url_input("example.com")
        assert ok is True
        assert normalized is not None

    def test_too_long(self):
        long_url = "https://example.com/" + "a" * (settings.MAX_URL_LENGTH + 10)
        ok, msg, normalized = validate_url_input(long_url)
        assert ok is False
        assert "too long" in msg.lower()
        assert normalized is None

    def test_unsupported_scheme(self):
        ok, msg, normalized = validate_url_input("ftp://files.example.com")
        assert ok is False
        assert "http" in msg.lower()
        assert normalized is None

    def test_malformed(self):
        ok, msg, normalized = validate_url_input("not a url at all")
        assert ok is False
        assert normalized is None


class TestSanitizeUserInput:
    def test_normal_text(self):
        assert sanitize_user_input("  hello world  ") == "hello world"

    def test_null_bytes_removed(self):
        assert "\x00" not in sanitize_user_input("hello\x00world")

    def test_truncation(self):
        text = "a" * 20_000
        result = sanitize_user_input(text, max_length=100)
        assert len(result) == 100

    def test_none_and_empty(self):
        assert sanitize_user_input(None) == ""  # type: ignore
        assert sanitize_user_input("") == ""