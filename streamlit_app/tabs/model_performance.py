"""
Tab 7 – Model Performance

Show saved evaluation metrics, per-class precision/recall/F1,
confusion matrix, PR-AUC/ROC-AUC, threshold comparisons and model version.
Never invents metrics at runtime – only displays previously saved results.
"""

from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import json

from config.constants import SUPPORTED_MODEL_NAMES, CURRENT_MODEL_VERSION
from config.settings import settings
from src.db.connection import ping
from src.db.repositories import EvaluationRepository, ModelMetadataRepository


def _load_local_eval_files() -> list[dict]:
    """Fallback: read evaluation JSON files from the metadata directory."""
    results = []
    meta_dir = settings.METADATA_DIR
    if not meta_dir.exists():
        return results
    for path in sorted(meta_dir.glob("eval_*.json"), reverse=True):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
                data["_source_file"] = path.name
                results.append(data)
        except Exception:
            continue
    return results


def render_model_performance() -> None:
    st.header("Model Performance")
    st.caption(
        "Evaluation results produced by the offline training pipeline. "
        "Metrics are never recomputed inside the app."
    )

    reports = []
    if ping():
        try:
            ev_repo = EvaluationRepository()
            reports = ev_repo.list_evaluations(limit=30)
        except Exception:
            pass

    if not reports:
        reports = _load_local_eval_files()

    if not reports:
        st.warning(
            "No evaluation reports found. "
            "Run the offline scripts (06_ml_experiments.py / 07_evaluate_and_select.py) "
            "and save the results first."
        )
        # Still show model metadata if present
        if ping():
            try:
                meta_repo = ModelMetadataRepository()
                models = meta_repo.list_models()
                if models:
                    st.subheader("Registered Model Metadata")
                    st.dataframe(pd.DataFrame(models), use_container_width=True)
            except Exception:
                pass
        return

    model_names = sorted({r.get("model_name", "unknown") for r in reports})
    selected = st.selectbox("Select model", options=model_names)

    # Pick the most recent report for the chosen model
    candidates = [r for r in reports if r.get("model_name") == selected]
    report = candidates[0] if candidates else reports[0]

    st.markdown(
        f"**Version:** {report.get('model_version', report.get('version', CURRENT_MODEL_VERSION))}  \n"
        f"**Saved at:** {report.get('saved_at', report.get('trained_at', 'N/A'))}"
    )

    test_metrics = report.get("test") or report.get("metrics") or report
    train_metrics = report.get("train") or {}

    def _metrics_df(m: dict, split: str) -> pd.DataFrame:
        rows = [
            {"Metric": "Accuracy", "Value": m.get("accuracy")},
            {"Metric": "Balanced Accuracy", "Value": m.get("balanced_accuracy")},
            {"Metric": "Precision (overall)", "Value": m.get("precision")},
            {"Metric": "Recall (overall)", "Value": m.get("recall")},
            {"Metric": "F1 (overall)", "Value": m.get("f1")},
            {"Metric": "ROC-AUC", "Value": m.get("roc_auc")},
            {"Metric": "PR-AUC", "Value": m.get("pr_auc")},
            {"Metric": "Precision (benign)", "Value": m.get("precision_benign")},
            {"Metric": "Recall (benign)", "Value": m.get("recall_benign")},
            {"Metric": "F1 (benign)", "Value": m.get("f1_benign")},
            {"Metric": "Precision (phish)", "Value": m.get("precision_phish")},
            {"Metric": "Recall (phish)", "Value": m.get("recall_phish")},
            {"Metric": "F1 (phish)", "Value": m.get("f1_phish")},
            {"Metric": "Threshold", "Value": m.get("threshold")},
            {"Metric": "Best F1 threshold", "Value": m.get("best_f1_threshold")},
        ]
        df = pd.DataFrame(rows)
        df["Value"] = df["Value"].apply(
            lambda x: f"{x:.4f}" if isinstance(x, (int, float)) else str(x)
        )
        df.insert(0, "Split", split)
        return df

    st.subheader("Test-set Metrics")
    st.dataframe(_metrics_df(test_metrics, "test"), use_container_width=True, hide_index=True)

    if train_metrics:
        with st.expander("Train-set Metrics"):
            st.dataframe(
                _metrics_df(train_metrics, "train"),
                use_container_width=True,
                hide_index=True,
            )

    cm = test_metrics.get("confusion_matrix")
    if cm and len(cm) == 2 and len(cm[0]) == 2:
        st.subheader("Confusion Matrix (test)")
        fig = go.Figure(
            data=go.Heatmap(
                z=cm,
                x=["Pred Benign", "Pred Phish"],
                y=["True Benign", "True Phish"],
                colorscale="Blues",
                text=cm,
                texttemplate="%{text}",
                showscale=False,
            )
        )
        fig.update_layout(height=320, margin=dict(t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)

    if len(model_names) > 1:
        st.subheader("Quick Comparison (test F1 / ROC-AUC)")
        rows = []
        for name in model_names:
            r = next((x for x in reports if x.get("model_name") == name), None)
            if not r:
                continue
            m = r.get("test") or r.get("metrics") or r
            rows.append(
                {
                    "Model": name,
                    "F1": m.get("f1"),
                    "ROC-AUC": m.get("roc_auc"),
                    "PR-AUC": m.get("pr_auc"),
                    "Recall (phish)": m.get("recall_phish"),
                }
            )
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)