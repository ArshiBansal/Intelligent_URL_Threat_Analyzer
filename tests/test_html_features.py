"""
Unit tests for HTML feature extraction.
"""

from __future__ import annotations

import numpy as np
import pytest

from src.features.html_features import extract_html_features, HTMLFeatureExtractor
from config.constants import HTML_FEATURE_NAMES


SIMPLE_HTML = """
<html>
<head><title>Login Page</title>
<meta name="description" content="Secure login">
<link rel="icon" href="/favicon.ico">
</head>
<body>
<form action="/login">
  <input type="text" name="user">
  <input type="password" name="pass">
  <input type="hidden" name="token" value="abc">
  <button type="submit">Login</button>
</form>
<a href="https://external.com">External</a>
<a href="/internal">Internal</a>
<img src="logo.png">
<script>document.write('x');</script>
<iframe src="ads.html"></iframe>
</body>
</html>
"""

EMPTY_HTML = ""
MALFORMED_HTML = "<html><body><form><input type='password'><<<broken"


class TestExtractHtmlFeatures:
    def test_empty_html(self):
        feats = extract_html_features("")
        assert isinstance(feats, dict)
        assert set(feats.keys()) == set(HTML_FEATURE_NAMES)
        assert feats["html_length"] == 0.0
        assert feats["num_forms"] == 0.0

    def test_none_html(self):
        feats = extract_html_features(None)  # type: ignore
        assert feats["html_length"] == 0.0

    def test_simple_html(self):
        feats = extract_html_features(SIMPLE_HTML)
        assert feats["html_length"] > 0
        assert feats["num_forms"] == 1.0
        assert feats["num_inputs"] >= 3.0
        assert feats["num_password_inputs"] == 1.0
        assert feats["num_hidden_inputs"] == 1.0
        assert feats["num_links"] == 2.0
        assert feats["num_external_links"] == 1.0
        assert feats["num_internal_links"] == 1.0
        assert feats["num_images"] == 1.0
        assert feats["num_scripts"] == 1.0
        assert feats["num_iframes"] == 1.0
        assert feats["has_title"] == 1.0
        assert feats["title_length"] > 0
        assert feats["has_meta_description"] == 1.0
        assert feats["has_favicon"] == 1.0
        assert feats["num_buttons"] >= 1.0
        assert feats["has_login_form"] == 1.0
        assert feats["has_suspicious_js"] == 1.0  # document.write

    def test_malformed_html_does_not_crash(self):
        feats = extract_html_features(MALFORMED_HTML)
        assert isinstance(feats, dict)
        assert feats["html_length"] > 0
        # Should still detect the password input
        assert feats["num_password_inputs"] >= 1.0

    def test_all_features_numeric(self):
        feats = extract_html_features(SIMPLE_HTML)
        for name, value in feats.items():
            assert isinstance(value, float), f"{name} is not float"


class TestHTMLFeatureExtractor:
    def test_transform_shape(self):
        extractor = HTMLFeatureExtractor()
        htmls = [SIMPLE_HTML, "", MALFORMED_HTML]
        X = extractor.transform(htmls)
        assert X.shape == (3, len(HTML_FEATURE_NAMES))
        assert X.dtype == np.float32

    def test_get_feature_names_out(self):
        extractor = HTMLFeatureExtractor()
        names = extractor.get_feature_names_out()
        assert list(names) == HTML_FEATURE_NAMES