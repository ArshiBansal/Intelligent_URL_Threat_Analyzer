"""
Unit tests for URL feature extraction.
"""

from __future__ import annotations

import numpy as np
import pytest

from src.features.url_features import extract_url_features, URLFeatureExtractor
from config.constants import URL_FEATURE_NAMES


class TestExtractUrlFeatures:
    def test_empty_url(self):
        feats = extract_url_features("")
        assert isinstance(feats, dict)
        assert set(feats.keys()) == set(URL_FEATURE_NAMES)
        assert feats["url_length"] == 0.0

    def test_none_url(self):
        feats = extract_url_features(None)  # type: ignore
        assert feats["url_length"] == 0.0

    def test_basic_https_url(self):
        url = "https://www.example.com/path/to/page?q=1&b=2"
        feats = extract_url_features(url)
        assert feats["url_length"] == len(url)
        assert feats["has_https"] == 1.0
        assert feats["has_www"] == 1.0
        assert feats["num_dots"] >= 2
        assert feats["num_slashes"] >= 3
        assert feats["num_question_marks"] == 1.0
        assert feats["num_equals"] == 2.0
        assert feats["num_ampersand"] == 1.0

    def test_ip_address_url(self):
        url = "http://192.168.1.1/login"
        feats = extract_url_features(url)
        assert feats["has_ip_address"] == 1.0
        assert feats["has_https"] == 0.0

    def test_suspicious_keywords(self):
        url = "https://secure-login-paypal-verify.example.tk/update-account"
        feats = extract_url_features(url)
        assert feats["has_login_keyword"] == 1.0
        assert feats["has_secure_keyword"] == 1.0
        assert feats["has_paypal_keyword"] == 1.0
        assert feats["has_verify_keyword"] == 1.0
        assert feats["has_update_keyword"] == 1.0
        assert feats["has_account_keyword"] == 1.0
        assert feats["has_suspicious_tld"] == 1.0

    def test_shortener_detection(self):
        url = "https://bit.ly/abc123"
        feats = extract_url_features(url)
        assert feats["is_shortened"] == 1.0

    def test_all_features_are_numeric(self):
        url = "https://sub.domain.example.com/path"
        feats = extract_url_features(url)
        for name, value in feats.items():
            assert isinstance(value, float), f"{name} is not float"
            assert value >= 0.0


class TestURLFeatureExtractor:
    def test_transform_shape(self):
        extractor = URLFeatureExtractor()
        urls = [
            "https://example.com",
            "http://192.168.0.1/login",
            "",
        ]
        X = extractor.transform(urls)
        assert X.shape == (3, len(URL_FEATURE_NAMES))
        assert X.dtype == np.float32

    def test_get_feature_names_out(self):
        extractor = URLFeatureExtractor()
        names = extractor.get_feature_names_out()
        assert list(names) == URL_FEATURE_NAMES

    def test_fit_transform_idempotent(self):
        extractor = URLFeatureExtractor()
        urls = ["https://test.com"]
        X1 = extractor.fit(urls).transform(urls)
        X2 = extractor.transform(urls)
        np.testing.assert_array_equal(X1, X2)