"""
Input validation for user-supplied URLs and related form data.
Used by the Streamlit "URL Threat Analyzer" tab.
"""

from __future__ import annotations

import re
from typing import Optional, Tuple
from urllib.parse import urlparse

from config.settings import settings
from config.constants import MAX_URL_LENGTH  # re-exported for convenience

# Allowed schemes – we deliberately restrict to http/https
_ALLOWED_SCHEMES = {"http", "https"}

# Very permissive but practical URL regex
_URL_RE = re.compile(
    r"^(?:https?://)?"  # optional scheme
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain
    r"localhost|"  # localhost
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # or IPv4
    r"(?::\d+)?"  # optional port
    r"(?:/?|[/?]\S+)$",
    re.IGNORECASE,
)


def is_safe_url_scheme(url: str) -> bool:
    """Return True only for http and https schemes."""
    try:
        parsed = urlparse(url if "://" in url else "http://" + url)
        return parsed.scheme.lower() in _ALLOWED_SCHEMES
    except Exception:
        return False


def validate_url_input(
    raw: str,
    max_length: Optional[int] = None,
) -> Tuple[bool, str, Optional[str]]:
    """
    Validate a user-supplied URL string.

    Returns
    -------
    (is_valid, message, normalized_url_or_None)

    - is_valid : bool
    - message  : human-readable success or error message
    - normalized_url : cleaned URL ready for feature extraction (or None)
    """
    max_length = max_length or settings.MAX_URL_LENGTH

    if raw is None:
        return False, "URL is required.", None

    url = str(raw).strip()
    if not url:
        return False, "URL cannot be empty.", None

    if len(url) > max_length:
        return (
            False,
            f"URL is too long (max {max_length} characters).",
            None,
        )

    # Basic syntactic check
    if not _URL_RE.match(url):
        return False, "URL format appears invalid.", None

    # Scheme restriction
    if not is_safe_url_scheme(url):
        return (
            False,
            "Only http:// and https:// URLs are supported.",
            None,
        )

    # Final parse check
    try:
        test = url if "://" in url else "http://" + url
        parsed = urlparse(test)
        if not parsed.netloc:
            return False, "URL is missing a valid host.", None
    except Exception:
        return False, "URL could not be parsed.", None

    # Success – return a lightly normalized version
    from src.utils.preprocessing import normalize_url

    normalized = normalize_url(url)
    return True, "URL looks valid.", normalized


def sanitize_user_input(text: str, max_length: int = 10_000) -> str:
    """
    Generic sanitization for free-text fields (e.g. optional HTML paste).
    Removes null bytes and truncates.
    """
    if not text or not isinstance(text, str):
        return ""
    text = text.replace("\x00", "")
    return text[:max_length].strip()