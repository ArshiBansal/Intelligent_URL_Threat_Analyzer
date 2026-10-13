"""
Model training, evaluation, prediction and comparison package.
Classical machine-learning only (scikit-learn + XGBoost).
No deep learning.
"""

from .train import train_model, train_all_models, save_artifacts
from .evaluate import evaluate_model, full_evaluation_report
from .predict import load_model_artifacts, predict_url
from .compare import compare_models, compare_text_approaches

__all__ = [
    "train_model",
    "train_all_models",
    "save_artifacts",
    "evaluate_model",
    "full_evaluation_report",
    "load_model_artifacts",
    "predict_url",
    "compare_models",
    "compare_text_approaches",
]