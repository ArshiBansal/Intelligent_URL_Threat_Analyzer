"""
Selected HTML / page feature extraction.

Uses BeautifulSoup with a tolerant parser (lxml or html.parser)
so malformed markup does not crash the pipeline.
HTML length is capped to stay memory-safe (aligned with ingest).
"""

from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional

import numpy as np
from bs4 import BeautifulSoup
from sklearn.base import BaseEstimator, TransformerMixin

from config.constants import HTML_FEATURE_NAMES

logger = logging.getLogger(__name__)

# Align with ingest / feature-matrix loader
_MAX_HTML_CHARS = 200_000


def _safe_soup(html: str) -> Optional[BeautifulSoup]:
    """Parse HTML robustly; return None on total failure."""
    if not html or not isinstance(html, str):
        return None
    html = html[:_MAX_HTML_CHARS]
    try:
        return BeautifulSoup(html, "lxml")
    except Exception:
        try:
            return BeautifulSoup(html, "html.parser")
        except Exception as exc:
            logger.debug("HTML parse failed: %s", exc)
            return None


def extract_html_features(html: str) -> Dict[str, float]:
    """
    Extract a fixed set of numeric features from HTML content.

    Returns a dictionary with keys matching HTML_FEATURE_NAMES.
    Empty / unparsable HTML yields zeros.
    """
    features = {name: 0.0 for name in HTML_FEATURE_NAMES}

    if not html or not isinstance(html, str):
        return features

    features["html_length"] = float(min(len(html), _MAX_HTML_CHARS))

    soup = _safe_soup(html)
    if soup is None:
        return features

    forms = soup.find_all("form")
    features["num_forms"] = float(len(forms))

    inputs = soup.find_all("input")
    features["num_inputs"] = float(len(inputs))

    password_inputs = [
        i for i in inputs if (i.get("type") or "").lower() == "password"
    ]
    features["num_password_inputs"] = float(len(password_inputs))

    hidden_inputs = [
        i for i in inputs if (i.get("type") or "").lower() == "hidden"
    ]
    features["num_hidden_inputs"] = float(len(hidden_inputs))

    anchors = soup.find_all("a", href=True)
    features["num_links"] = float(len(anchors))

    external = 0
    internal = 0
    for a in anchors:
        href = (a.get("href") or "").strip().lower()
        if href.startswith(("http://", "https://", "//")):
            external += 1
        elif href.startswith(("#", "javascript:", "mailto:")):
            continue
        else:
            internal += 1
    features["num_external_links"] = float(external)
    features["num_internal_links"] = float(internal)

    features["num_images"] = float(len(soup.find_all("img")))
    features["num_scripts"] = float(len(soup.find_all("script")))
    features["num_iframes"] = float(len(soup.find_all("iframe")))

    title_tag = soup.find("title")
    if title_tag and title_tag.string:
        title_text = title_tag.string.strip()
        features["has_title"] = 1.0
        features["title_length"] = float(len(title_text))
    else:
        features["has_title"] = 0.0
        features["title_length"] = 0.0

    meta_tags = soup.find_all("meta")
    features["num_meta_tags"] = float(len(meta_tags))
    features["has_meta_description"] = (
        1.0
        if any((m.get("name") or "").lower() == "description" for m in meta_tags)
        else 0.0
    )

    has_favicon = bool(
        soup.find("link", rel=lambda x: x and "icon" in str(x).lower())
    )
    features["has_favicon"] = 1.0 if has_favicon else 0.0

    buttons = soup.find_all(["button", "input"])
    button_count = sum(
        1
        for b in buttons
        if b.name == "button"
        or (b.get("type") or "").lower() in {"submit", "button"}
    )
    features["num_buttons"] = float(button_count)

    has_login_form = False
    for form in forms:
        form_html = str(form).lower()
        if any(k in form_html for k in ("password", "login", "signin", "username")):
            has_login_form = True
            break
    features["has_login_form"] = 1.0 if has_login_form else 0.0

    scripts = soup.find_all("script")
    suspicious_js = False
    js_patterns = [
        r"eval\s*\(",
        r"document\.write\s*\(",
        r"window\.location\s*=",
        r"unescape\s*\(",
    ]
    for script in scripts:
        content = script.string or ""
        if any(re.search(p, content, re.I) for p in js_patterns):
            suspicious_js = True
            break
    features["has_suspicious_js"] = 1.0 if suspicious_js else 0.0

    return features


class HTMLFeatureExtractor(BaseEstimator, TransformerMixin):
    """scikit-learn compatible transformer for HTML feature extraction."""

    def __init__(self, feature_names: Optional[List[str]] = None):
        self.feature_names = feature_names or HTML_FEATURE_NAMES

    def fit(self, X, y=None):
        return self

    def transform(self, X) -> np.ndarray:
        rows = []
        for html in X:
            feats = extract_html_features(str(html) if html is not None else "")
            rows.append([feats.get(name, 0.0) for name in self.feature_names])
        return np.array(rows, dtype=np.float32)

    def get_feature_names_out(self, input_features=None):
        return np.array(self.feature_names)