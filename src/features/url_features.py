"""
URL structural feature extraction.

All features are deterministic, fast, and require only the URL string.
Compatible with scikit-learn transformers.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin

from config.constants import URL_FEATURE_NAMES

# Suspicious TLDs frequently observed in phishing (heuristic list)
_SUSPICIOUS_TLDS = {
    "tk", "ml", "ga", "cf", "gq", "xyz", "top", "work", "click",
    "link", "info", "online", "site", "website", "space", "icu",
}

# Common URL shorteners
_SHORTENER_DOMAINS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd",
    "buff.ly", "adf.ly", "bit.do", "shorturl.at", "rebrand.ly",
    "cutt.ly", "tiny.cc", "rb.gy",
}

# Keyword lists for phishing-related signals
_LOGIN_KEYWORDS = {"login", "signin", "sign-in", "log-in", "logon"}
_SECURE_KEYWORDS = {"secure", "security", "https", "ssl", "verify"}
_ACCOUNT_KEYWORDS = {"account", "acct", "myaccount", "user"}
_UPDATE_KEYWORDS = {"update", "upgrade", "confirm", "validation"}
_VERIFY_KEYWORDS = {"verify", "verification", "authenticate", "auth"}
_BANK_KEYWORDS = {"bank", "banking", "paypal", "wallet", "finance"}
_PAYPAL_KEYWORDS = {"paypal", "pay-pal", "payp"}


def _safe_parse(url: str):
    """Parse URL safely; return None on failure."""
    try:
        if not url or not isinstance(url, str):
            return None
        url = url.strip()
        if not url.startswith(("http://", "https://")):
            url = "http://" + url
        return urlparse(url)
    except Exception:
        return None


def extract_url_features(url: str) -> Dict[str, float]:
    """
    Extract a fixed set of numeric features from a single URL.

    Returns a dictionary with keys matching URL_FEATURE_NAMES.
    Missing / failed parsing yields 0.0 for most features.
    """
    features = {name: 0.0 for name in URL_FEATURE_NAMES}

    if not url or not isinstance(url, str):
        return features

    url = url.strip()
    parsed = _safe_parse(url)
    if parsed is None:
        features["url_length"] = float(len(url))
        return features

    # Basic lengths
    features["url_length"] = float(len(url))
    features["hostname_length"] = float(len(parsed.netloc or ""))
    features["path_length"] = float(len(parsed.path or ""))
    features["query_length"] = float(len(parsed.query or ""))

    # Character counts on the full URL
    features["num_dots"] = float(url.count("."))
    features["num_hyphens"] = float(url.count("-"))
    features["num_underscores"] = float(url.count("_"))
    features["num_slashes"] = float(url.count("/"))
    features["num_question_marks"] = float(url.count("?"))
    features["num_equals"] = float(url.count("="))
    features["num_at"] = float(url.count("@"))
    features["num_ampersand"] = float(url.count("&"))
    features["num_exclamation"] = float(url.count("!"))
    features["num_tilde"] = float(url.count("~"))
    features["num_comma"] = float(url.count(","))
    features["num_plus"] = float(url.count("+"))
    features["num_asterisk"] = float(url.count("*"))
    features["num_hash"] = float(url.count("#"))
    features["num_dollar"] = float(url.count("$"))
    features["num_percent"] = float(url.count("%"))

    # Host-related
    host = (parsed.netloc or "").lower()
    if ":" in host:
        host = host.split(":")[0]

    # IP address check (IPv4)
    ip_pattern = re.compile(
        r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
        r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    )
    features["has_ip_address"] = 1.0 if ip_pattern.match(host) else 0.0

    features["has_https"] = 1.0 if parsed.scheme == "https" else 0.0
    features["has_www"] = 1.0 if host.startswith("www.") else 0.0

    # Shortener detection
    features["is_shortened"] = (
        1.0 if any(s in host for s in _SHORTENER_DOMAINS) else 0.0
    )

    # Subdomains
    parts = host.split(".")
    features["num_subdomains"] = float(max(0, len(parts) - 2))

    # TLD
    tld = parts[-1] if parts else ""
    features["tld_length"] = float(len(tld))
    features["has_suspicious_tld"] = 1.0 if tld in _SUSPICIOUS_TLDS else 0.0

    # Keyword presence (case-insensitive on full URL)
    url_lower = url.lower()
    features["has_login_keyword"] = (
        1.0 if any(k in url_lower for k in _LOGIN_KEYWORDS) else 0.0
    )
    features["has_secure_keyword"] = (
        1.0 if any(k in url_lower for k in _SECURE_KEYWORDS) else 0.0
    )
    features["has_account_keyword"] = (
        1.0 if any(k in url_lower for k in _ACCOUNT_KEYWORDS) else 0.0
    )
    features["has_update_keyword"] = (
        1.0 if any(k in url_lower for k in _UPDATE_KEYWORDS) else 0.0
    )
    features["has_verify_keyword"] = (
        1.0 if any(k in url_lower for k in _VERIFY_KEYWORDS) else 0.0
    )
    features["has_bank_keyword"] = (
        1.0 if any(k in url_lower for k in _BANK_KEYWORDS) else 0.0
    )
    features["has_paypal_keyword"] = (
        1.0 if any(k in url_lower for k in _PAYPAL_KEYWORDS) else 0.0
    )

    return features


class URLFeatureExtractor(BaseEstimator, TransformerMixin):
    """
    scikit-learn compatible transformer that converts a list/Series of URLs
    into a numeric feature matrix.
    """

    def __init__(self, feature_names: Optional[List[str]] = None):
        self.feature_names = feature_names or URL_FEATURE_NAMES

    def fit(self, X, y=None):
        return self

    def transform(self, X) -> np.ndarray:
        rows = []
        for url in X:
            feats = extract_url_features(str(url) if url is not None else "")
            rows.append([feats.get(name, 0.0) for name in self.feature_names])
        return np.array(rows, dtype=np.float32)

    def get_feature_names_out(self, input_features=None):
        return np.array(self.feature_names)