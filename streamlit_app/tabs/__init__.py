"""
Required Streamlit tabs (exactly eight as per specification).
"""

from .dashboard import render_dashboard
from .url_threat_analyzer import render_url_threat_analyzer
from .threat_evidence import render_threat_evidence
from .dataset_explorer import render_dataset_explorer
from .threat_analytics import render_threat_analytics
from .prediction_history import render_prediction_history
from .model_performance import render_model_performance
from .about import render_about

__all__ = [
    "render_dashboard",
    "render_url_threat_analyzer",
    "render_threat_evidence",
    "render_dataset_explorer",
    "render_threat_analytics",
    "render_prediction_history",
    "render_model_performance",
    "render_about",
]