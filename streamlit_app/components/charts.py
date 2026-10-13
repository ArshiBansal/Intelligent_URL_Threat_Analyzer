"""
Reusable Plotly chart helpers.
All functions return a Plotly Figure so callers can pass them to st.plotly_chart.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

import plotly.express as px
import plotly.graph_objects as go

from config.constants import LABEL_BENIGN, LABEL_PHISHING, LABEL_DISPLAY


def plot_class_distribution(
    benign_count: int,
    phishing_count: int,
    title: str = "Class Distribution",
    hole: float = 0.45,
) -> go.Figure:
    """Donut / pie chart for benign vs phishing counts."""
    fig = go.Figure(
        data=[
            go.Pie(
                labels=[
                    LABEL_DISPLAY.get(LABEL_BENIGN, "Benign"),
                    LABEL_DISPLAY.get(LABEL_PHISHING, "Phishing"),
                ],
                values=[benign_count, phishing_count],
                hole=hole,
                marker_colors=["#2ecc71", "#e74c3c"],
                textinfo="label+percent+value",
                insidetextorientation="horizontal",
            )
        ]
    )
    fig.update_layout(
        title=title,
        margin=dict(t=40, b=20, l=20, r=20),
        height=340,
        showlegend=True,
    )
    return fig


def plot_confusion_matrix(
    cm: Sequence[Sequence[int]],
    title: str = "Confusion Matrix",
) -> go.Figure:
    """
    2x2 confusion-matrix heatmap.
    Expects cm = [[TN, FP], [FN, TP]] or equivalent row-major layout.
    """
    if not cm or len(cm) != 2 or len(cm[0]) != 2:
        # Return an empty figure rather than crashing
        fig = go.Figure()
        fig.update_layout(title="Invalid confusion matrix data", height=300)
        return fig

    fig = go.Figure(
        data=go.Heatmap(
            z=cm,
            x=["Predicted Benign", "Predicted Phish"],
            y=["Actual Benign", "Actual Phish"],
            colorscale="Blues",
            text=cm,
            texttemplate="%{text}",
            showscale=False,
            hovertemplate="Actual: %{y}<br>Predicted: %{x}<br>Count: %{z}<extra></extra>",
        )
    )
    fig.update_layout(
        title=title,
        height=340,
        margin=dict(t=40, b=20, l=20, r=20),
    )
    return fig


def plot_metric_bars(
    metrics: Dict[str, float],
    title: str = "Model Metrics",
    color: str = "#3498db",
) -> go.Figure:
    """Horizontal or vertical bar chart for a flat metrics dictionary."""
    names = list(metrics.keys())
    values = [metrics[k] if metrics[k] is not None else 0.0 for k in names]

    fig = go.Figure(
        data=[
            go.Bar(
                x=names,
                y=values,
                marker_color=color,
                text=[f"{v:.3f}" for v in values],
                textposition="auto",
            )
        ]
    )
    fig.update_layout(
        title=title,
        yaxis_title="Score",
        yaxis=dict(range=[0, 1.05]),
        height=360,
        margin=dict(t=40, b=80, l=20, r=20),
    )
    return fig


def plot_language_distribution(
    lang_counts: List[Dict[str, Any]],
    title: str = "Records by Language",
    top_n: int = 15,
) -> go.Figure:
    """
    Bar chart for language distribution.
    Expects a list of {"lang": str, "count": int}.
    """
    if not lang_counts:
        fig = go.Figure()
        fig.update_layout(title="No language data", height=300)
        return fig

    # Keep top_n
    data = sorted(lang_counts, key=lambda x: x.get("count", 0), reverse=True)[:top_n]
    df_langs = [d.get("lang", "unknown") for d in data]
    df_counts = [d.get("count", 0) for d in data]

    fig = px.bar(
        x=df_langs,
        y=df_counts,
        labels={"x": "Language", "y": "Count"},
        title=title,
        color=df_counts,
        color_continuous_scale="Teal",
    )
    fig.update_layout(
        height=360,
        margin=dict(t=40, b=40, l=20, r=20),
        coloraxis_showscale=False,
    )
    return fig


def plot_feature_importance(
    feature_names: List[str],
    importances: List[float],
    title: str = "Top Feature Importances",
    top_n: int = 20,
) -> go.Figure:
    """Horizontal bar chart for feature importances (if available)."""
    pairs = sorted(
        zip(feature_names, importances),
        key=lambda x: abs(x[1]),
        reverse=True,
    )[:top_n]
    names = [p[0] for p in pairs][::-1]
    vals = [p[1] for p in pairs][::-1]

    fig = go.Figure(
        data=[
            go.Bar(
                y=names,
                x=vals,
                orientation="h",
                marker_color="#9b59b6",
            )
        ]
    )
    fig.update_layout(
        title=title,
        xaxis_title="Importance",
        height=max(300, top_n * 22),
        margin=dict(t=40, b=20, l=120, r=20),
    )
    return fig