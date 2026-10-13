"""
Classical NLP / text representation utilities.

Implements at least four suitable text approaches as required:
1. TF-IDF (word)
2. TF-IDF (char n-grams)
3. Bag-of-Words / CountVectorizer
4. Lexical / statistical features (length, entropy, digit ratio, etc.)

All are scikit-learn compatible and do not use deep learning.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any, Dict, List, Optional, Union

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import StandardScaler


# ----------------------------------------------------------------------
# 1 & 2. Vectorizers
# ----------------------------------------------------------------------
def build_tfidf_vectorizer(
    analyzer: str = "word",
    ngram_range: tuple = (1, 2),
    max_features: int = 10_000,
    min_df: int = 2,
    max_df: float = 0.95,
    sublinear_tf: bool = True,
) -> TfidfVectorizer:
    """
    Create a TF-IDF vectorizer.
    analyzer="word" or "char" / "char_wb" covers two distinct approaches.
    """
    return TfidfVectorizer(
        analyzer=analyzer,
        ngram_range=ngram_range,
        max_features=max_features,
        min_df=min_df,
        max_df=max_df,
        sublinear_tf=sublinear_tf,
        lowercase=True,
        strip_accents="unicode",
        stop_words="english" if analyzer == "word" else None,
    )


def build_count_vectorizer(
    analyzer: str = "word",
    ngram_range: tuple = (1, 1),
    max_features: int = 10_000,
    min_df: int = 2,
    max_df: float = 0.95,
) -> CountVectorizer:
    """Bag-of-Words / Count vectorizer."""
    return CountVectorizer(
        analyzer=analyzer,
        ngram_range=ngram_range,
        max_features=max_features,
        min_df=min_df,
        max_df=max_df,
        lowercase=True,
        strip_accents="unicode",
        stop_words="english" if analyzer == "word" else None,
    )


# ----------------------------------------------------------------------
# 3. Lexical / statistical features
# ----------------------------------------------------------------------
def _char_entropy(text: str) -> float:
    if not text:
        return 0.0
    counts = Counter(text)
    total = len(text)
    return -sum((c / total) * math.log2(c / total) for c in counts.values())


def lexical_stats(text: str) -> Dict[str, float]:
    """
    Lightweight lexical / statistical features from raw text
    (URL, title, or concatenated visible text).
    """
    if not text or not isinstance(text, str):
        text = ""

    text = text.strip()
    length = len(text)
    if length == 0:
        return {
            "lex_length": 0.0,
            "lex_num_digits": 0.0,
            "lex_num_letters": 0.0,
            "lex_num_spaces": 0.0,
            "lex_num_special": 0.0,
            "lex_digit_ratio": 0.0,
            "lex_letter_ratio": 0.0,
            "lex_space_ratio": 0.0,
            "lex_special_ratio": 0.0,
            "lex_entropy": 0.0,
            "lex_avg_word_len": 0.0,
            "lex_num_words": 0.0,
            "lex_num_unique_words": 0.0,
            "lex_uppercase_ratio": 0.0,
        }

    digits = sum(c.isdigit() for c in text)
    letters = sum(c.isalpha() for c in text)
    spaces = sum(c.isspace() for c in text)
    special = length - digits - letters - spaces
    upper = sum(c.isupper() for c in text)

    words = re.findall(r"\b\w+\b", text.lower())
    num_words = len(words)
    unique_words = len(set(words))
    avg_word_len = (sum(len(w) for w in words) / num_words) if num_words else 0.0

    return {
        "lex_length": float(length),
        "lex_num_digits": float(digits),
        "lex_num_letters": float(letters),
        "lex_num_spaces": float(spaces),
        "lex_num_special": float(special),
        "lex_digit_ratio": digits / length,
        "lex_letter_ratio": letters / length,
        "lex_space_ratio": spaces / length,
        "lex_special_ratio": special / length,
        "lex_entropy": _char_entropy(text),
        "lex_avg_word_len": avg_word_len,
        "lex_num_words": float(num_words),
        "lex_num_unique_words": float(unique_words),
        "lex_uppercase_ratio": upper / length,
    }


LEXICAL_FEATURE_NAMES = list(lexical_stats("").keys())


class LexicalStatsExtractor(BaseEstimator, TransformerMixin):
    """scikit-learn transformer for lexical statistics."""

    def fit(self, X, y=None):
        return self

    def transform(self, X) -> np.ndarray:
        rows = []
        for text in X:
            stats = lexical_stats(str(text) if text is not None else "")
            rows.append([stats[name] for name in LEXICAL_FEATURE_NAMES])
        return np.array(rows, dtype=np.float32)

    def get_feature_names_out(self, input_features=None):
        return np.array(LEXICAL_FEATURE_NAMES)


# ----------------------------------------------------------------------
# 4. Combined TextFeatureExtractor
# ----------------------------------------------------------------------
class TextFeatureExtractor(BaseEstimator, TransformerMixin):
    """
    Unified text feature extractor that can produce any of the four
    required classical representations (or a combination).

    Parameters
    ----------
    method : str
        One of:
        - "tfidf_word"
        - "tfidf_char"
        - "bow"
        - "lexical"
        - "union"  (tfidf_word + lexical)
    """

    def __init__(
        self,
        method: str = "tfidf_word",
        max_features: int = 10_000,
        ngram_range: tuple = (1, 2),
    ):
        self.method = method
        self.max_features = max_features
        self.ngram_range = ngram_range
        self._vectorizer = None
        self._lexical = LexicalStatsExtractor()

    def fit(self, X, y=None):
        texts = [str(t) if t is not None else "" for t in X]

        if self.method == "tfidf_word":
            self._vectorizer = build_tfidf_vectorizer(
                analyzer="word",
                ngram_range=self.ngram_range,
                max_features=self.max_features,
            )
            self._vectorizer.fit(texts)
        elif self.method == "tfidf_char":
            self._vectorizer = build_tfidf_vectorizer(
                analyzer="char_wb",
                ngram_range=(3, 5),
                max_features=self.max_features,
            )
            self._vectorizer.fit(texts)
        elif self.method == "bow":
            self._vectorizer = build_count_vectorizer(
                analyzer="word",
                ngram_range=(1, 1),
                max_features=self.max_features,
            )
            self._vectorizer.fit(texts)
        elif self.method == "lexical":
            self._lexical.fit(texts)
        elif self.method == "union":
            self._vectorizer = build_tfidf_vectorizer(
                analyzer="word",
                ngram_range=self.ngram_range,
                max_features=self.max_features,
            )
            self._vectorizer.fit(texts)
            self._lexical.fit(texts)
        else:
            raise ValueError(f"Unknown text method: {self.method}")

        return self

    def transform(self, X) -> np.ndarray:
        texts = [str(t) if t is not None else "" for t in X]

        if self.method == "lexical":
            return self._lexical.transform(texts)

        if self.method in {"tfidf_word", "tfidf_char", "bow"}:
            return self._vectorizer.transform(texts).toarray().astype(np.float32)

        if self.method == "union":
            tfidf_part = self._vectorizer.transform(texts).toarray()
            lex_part = self._lexical.transform(texts)
            return np.hstack([tfidf_part, lex_part]).astype(np.float32)

        raise ValueError(f"Unknown text method: {self.method}")

    def get_feature_names_out(self, input_features=None):
        if self.method == "lexical":
            return self._lexical.get_feature_names_out()
        if self.method in {"tfidf_word", "tfidf_char", "bow"}:
            return self._vectorizer.get_feature_names_out()
        if self.method == "union":
            return np.concatenate(
                [
                    self._vectorizer.get_feature_names_out(),
                    self._lexical.get_feature_names_out(),
                ]
            )
        return np.array([])