"""
Tests for the prediction helpers.
Uses a lightweight mock when real model artifacts are absent.
"""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import numpy as np
import pytest

from src.models.predict import _build_feature_vector, predict_url
from config.constants import LABEL_INVERSE_MAP, CURRENT_MODEL_VERSION


class TestBuildFeatureVector:
    def test_url_only(self):
        X, evidence = _build_feature_vector("https://example.com/login")
        assert X.ndim == 2
        assert X.shape[0] == 1
        assert isinstance(evidence, dict)
        assert evidence["url_length"] > 0
        assert evidence["has_https"] == 1.0

    def test_url_plus_html(self):
        html = "<html><body><form><input type='password'></form></body></html>"
        X, evidence = _build_feature_vector("https://example.com", html=html)
        assert X.shape[0] == 1
        assert evidence["num_password_inputs"] == 1.0

    def test_empty_inputs(self):
        X, evidence = _build_feature_vector("")
        assert X.shape[0] == 1
        assert evidence["url_length"] == 0.0


class TestPredictUrl:
    """
    These tests mock the artifact loader so they run without trained models.
    """

    def _make_mock_model(self, proba_phish: float = 0.8):
        model = MagicMock()
        model.predict_proba.return_value = np.array([[1 - proba_phish, proba_phish]])
        return model

    def test_predict_phishing(self):
        mock_model = self._make_mock_model(0.85)
        mock_meta = {
            "version": CURRENT_MODEL_VERSION,
            "default_threshold": 0.5,
            "feature_names": None,
        }
        with patch(
            "src.models.predict.load_model_artifacts",
            return_value=(mock_model, mock_meta, None),
        ):
            result = predict_url("https://secure-login-paypal.tk/update")
            assert result["predicted_label"] == "phish"
            assert result["predicted_class"] == 1
            assert result["confidence"] == pytest.approx(0.85)
            assert "disclaimer" in result
            assert "evidence" in result

    def test_predict_benign(self):
        mock_model = self._make_mock_model(0.15)
        mock_meta = {
            "version": CURRENT_MODEL_VERSION,
            "default_threshold": 0.5,
        }
        with patch(
            "src.models.predict.load_model_artifacts",
            return_value=(mock_model, mock_meta, None),
        ):
            result = predict_url("https://www.wikipedia.org")
            assert result["predicted_label"] == "benign"
            assert result["predicted_class"] == 0
            assert result["confidence"] == pytest.approx(0.85)  # max proba

    def test_missing_artifact_raises(self):
        with patch(
            "src.models.predict.load_model_artifacts",
            side_effect=FileNotFoundError("No model"),
        ):
            with pytest.raises(FileNotFoundError):
                predict_url("https://example.com")