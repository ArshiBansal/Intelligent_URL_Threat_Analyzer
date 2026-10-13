"""
Shared preprocessing utilities used by both offline training scripts
and the Streamlit inference path.

Guarantees that the same transformations applied during model development
are applied at prediction time (prevents train/serve skew).
"""

from __future__ import annotations

import re
import logging
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

import numpy as np
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Maximum HTML length we will process (memory safety)
_MAX_HTML_CHARS = 500_000

# Characters that are often noise in phishing pages
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")


def normalize_url(url: str, keep_fragment: bool = False) -> str:
    """
    Canonicalize a URL for consistent feature extraction.

    - Lower-case scheme and host
    - Remove default ports
    - Strip trailing slash from path (except root)
    - Sort query parameters
    - Optionally drop fragment
    """
    if not url or not isinstance(url, str):
        return ""

    url = url.strip()
    if not url:
        return ""

    # Add scheme if missing so urlparse works
    if not re.match(r"^https?://", url, re.I):
        url = "http://" + url

    try:
        parsed = urlparse(url)
    except Exception:
        return url  # return original on parse failure

    scheme = (parsed.scheme or "http").lower()
    netloc = (parsed.netloc or "").lower()

    # Remove default ports
    if netloc.endswith(":80") and scheme == "http":
        netloc = netloc[:-3]
    if netloc.endswith(":443") and scheme == "https":
        netloc = netloc[:-4]

    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")

    # Sort query parameters for determinism
    query_pairs = parse_qsl(parsed.query, keep_blank_values=True)
    query = urlencode(sorted(query_pairs))

    fragment = parsed.fragment if keep_fragment else ""

    normalized = urlunparse((scheme, netloc, path, "", query, fragment))
    return normalized


def clean_html(html: str, max_chars: int = _MAX_HTML_CHARS) -> str:
    """
    Light cleaning of HTML before feature extraction or text processing.

    - Truncates extremely long documents
    - Removes control characters
    - Strips script and style content (optional, for text views)
    """
    if not html or not isinstance(html, str):
        return ""

    html = html[:max_chars]
    html = _CONTROL_CHARS_RE.sub(" ", html)

    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        try:
            soup = BeautifulSoup(html, "html.parser")
        except Exception:
            return html  # return cleaned string as-is

    # Remove script / style tags so visible text is cleaner
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    return str(soup)


def prepare_text_for_nlp(
    text: str,
    lowercase: bool = True,
    remove_urls: bool = True,
    remove_emails: bool = True,
    max_length: int = 50_000,
) -> str:
    """
    Prepare raw text (URL, title, or concatenated page text)
    for classical NLP vectorizers.
    """
    if not text or not isinstance(text, str):
        return ""

    text = text[:max_length]

    if remove_urls:
        text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    if remove_emails:
        text = re.sub(r"\S+@\S+", " ", text)

    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()

    if lowercase:
        text = text.lower()

    return text


def feature_dict_to_vector(
    feature_dict: Dict[str, float],
    feature_names: List[str],
    dtype=np.float32,
) -> np.ndarray:
    """
    Convert a feature dictionary into a fixed-order numeric vector.
    Missing keys become 0.0.
    """
    return np.array(
        [[feature_dict.get(name, 0.0) for name in feature_names]],
        dtype=dtype,
    )


def combine_feature_dicts(
    *dicts: Dict[str, float],
) -> Dict[str, float]:
    """Merge multiple feature dictionaries (later dicts overwrite earlier keys)."""
    combined: Dict[str, float] = {}
    for d in dicts:
        if d:
            combined.update(d)
    return combined