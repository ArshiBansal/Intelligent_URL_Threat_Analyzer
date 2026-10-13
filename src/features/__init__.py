"""
Feature engineering package for Intelligent URL Threat Analyzer.

Provides URL structural features, selected HTML/page features,
and classical NLP / text representations.
All extractors are pure Python / scikit-learn compatible
(no deep learning).
"""

from .url_features import extract_url_features, URLFeatureExtractor
from .html_features import extract_html_features, HTMLFeatureExtractor
from .text_features import (
    TextFeatureExtractor,
    build_tfidf_vectorizer,
    build_count_vectorizer,
    lexical_stats,
)

__all__ = [
    "extract_url_features",
    "URLFeatureExtractor",
    "extract_html_features",
    "HTMLFeatureExtractor",
    "TextFeatureExtractor",
    "build_tfidf_vectorizer",
    "build_count_vectorizer",
    "lexical_stats",
]