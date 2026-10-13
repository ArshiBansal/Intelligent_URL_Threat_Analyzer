"""
Tab 1 – Dashboard
Dataset totals, phishing/benign distribution, recent activity,
model status and key performance indicators.
"""

from __future__ import annotations

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from config.constants import (
    APP_TITLE,
    DATASET_DISPLAY_NAME,
    LABEL_BENIGN,
    LABEL_PHISHING,
    LABEL_DISPLAY,
    CURRENT_MODEL_VERSION,
)
from config.settings import settings
from src.db.connection import ping
from src.db.repositories import (
    SourceRepository,
    PredictionRepository,
    ModelMetadataRepository,
    EvaluationRepository,
)
from src.data.explore import class_distribution, generate_data_quality_report


def render_dashboard() -> None:
    st.header("Dashboard")
    st.caption(
        f"Defensive phishing detection powered by the **{DATASET_DISPLAY_NAME}** dataset"
    )

    col_h1, col_h2, col_h3 = st.columns(3)
    with col_h1:
        mongo_ok = ping()
        st.metric(
            "MongoDB",
            "Connected" if mongo_ok else "Unavailable",
            delta="OK" if mongo_ok else "Check connection",
            delta_color="normal" if mongo_ok else "inverse",
        )
    with col_h2:
        st.metric("Model Version", CURRENT_MODEL_VERSION)
    with col_h3:
        st.metric("Environment", settings.APP_ENV.title())

    if not mongo_ok:
        st.warning(
            "MongoDB is not reachable. Dataset statistics and history will be unavailable. "
            "Verify MONGO_URI and that the server is running."
        )
        return

    st.subheader("Dataset Overview")
    try:
        src_repo = SourceRepository()
        total = src_repo.estimated_count()
        dist = src_repo.label_distribution()
        benign = dist.get(LABEL_BENIGN, 0)
        phish = dist.get(LABEL_PHISHING, 0)

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Records", f"{total:,}")
        k2.metric("Benign", f"{benign:,}", delta=f"{(benign/total*100):.1f}%" if total else "0%")
        k3.metric("Phishing", f"{phish:,}", delta=f"{(phish/total*100):.1f}%" if total else "0%")
        k4.metric(
            "Class Balance",
            f"{benign/phish:.2f}:1" if phish else "N/A",
            help="Benign : Phishing ratio",
        )
    except Exception as exc:
        st.error(f"Could not load dataset statistics: {exc}")
        total = benign = phish = 0

    if total > 0:
        fig = go.Figure(
            data=[
                go.Pie(
                    labels=[LABEL_DISPLAY[LABEL_BENIGN], LABEL_DISPLAY[LABEL_PHISHING]],
                    values=[benign, phish],
                    hole=0.45,
                    marker_colors=["#2ecc71", "#e74c3c"],
                )
            ]
        )
        fig.update_layout(
            title="Class Distribution",
            margin=dict(t=40, b=20, l=20, r=20),
            height=320,
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Recent Activity & Model Status")
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("##### Prediction History")
        try:
            pred_repo = PredictionRepository()
            hist_count = pred_repo.count()
            st.metric("Stored Predictions", f"{hist_count:,}")
            recent = pred_repo.list_history(page=1, page_size=5)
            if recent["items"]:
                for item in recent["items"]:
                    label = item.get("predicted_label", "unknown")
                    conf = item.get("confidence")
                    conf_str = f"{conf:.1%}" if conf is not None else "n/a"
                    ts = item.get("timestamp", "")
                    if isinstance(ts, datetime):
                        ts = ts.strftime("%Y-%m-%d %H:%M")
                    st.caption(f"{ts} · **{label}** ({conf_str}) · {item.get('url', '')[:60]}")
            else:
                st.info("No predictions recorded yet.")
        except Exception as exc:
            st.warning(f"Could not load prediction history: {exc}")

    with c2:
        st.markdown("##### Latest Model Metadata")
        try:
            meta_repo = ModelMetadataRepository()
            latest = meta_repo.get_latest()
            if latest:
                st.json(
                    {
                        "model_name": latest.get("model_name"),
                        "version": latest.get("version"),
                        "trained_at": str(latest.get("trained_at") or latest.get("saved_at")),
                        "feature_dim": latest.get("feature_dim"),
                    }
                )
            else:
                st.info("No model metadata found. Run offline training first.")
        except Exception as exc:
            st.warning(f"Could not load model metadata: {exc}")

    st.divider()
    st.info(
        "➡️ **Primary workflow:** open the **URL Threat Analyzer** tab to submit a URL for analysis."
    )