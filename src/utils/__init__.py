# src/utils/__init__.py
"""
Utility helpers for Intelligent URL Threat Analyzer.
Preprocessing, input validation, logging, timing and common helpers.
"""

from .preprocessing import (
    normalize_url,
    clean_html,
    prepare_text_for_nlp,
    feature_dict_to_vector,
)
from .validation import (
    validate_url_input,
    is_safe_url_scheme,
    sanitize_user_input,
)
from .helpers import (
    setup_logging,
    timed,
    sha256_hex,
    truncate,
    safe_json_serialize,
    chunked,
)

__all__ = [
    "normalize_url",
    "clean_html",
    "prepare_text_for_nlp",
    "feature_dict_to_vector",
    "validate_url_input",
    "is_safe_url_scheme",
    "sanitize_user_input",
    "setup_logging",
    "timed",
    "sha256_hex",
    "truncate",
    "safe_json_serialize",
    "chunked",
]