"""
Tab 5 – Threat Analytics

Interactive charts for class balance, temporal trends, URL/HTML feature
distributions, language patterns and other dataset insights.
"""

from __future__ import annotations

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from config.constants import (
    DATASET_DISPLAY_NAME,
    LABEL_BENIGN,
    LABEL_PHISHING,
    LABEL_DISPLAY,
)
from src.db.connection import ping
from src.db.repositories import SourceRepository
from src.data.explore import (
    class_distribution,
    language_distribution,
    date_range,
    generate_data_quality_report,
)


def render_threat_analytics() -> None:
    st.header("Threat Analytics")
    st.caption(
        f"Interactive insights derived from the **{DATASET_DISPLAY_NAME}** collection."
    )

    if not ping():
        st.error("MongoDB is unavailable. Analytics cannot be loaded.")
        return

    repo = SourceRepository()

    st.subheader("Class Balance")
    try:
        dist = repo.label_distribution()
        benign = dist.get(LABEL_BENIGN, 0)
        phish = dist.get(LABEL_PHISHING, 0)
        total = benign + phish

        fig = go.Figure(
            data=[
                go.Bar(
                    x=[LABEL_DISPLAY[LABEL_BENIGN], LABEL_DISPLAY[LABEL_PHISHING]],
                    y=[benign, phish],
                    marker_color=["#2ecc71", "#e74c3c"],
                    text=[f"{benign:,}", f"{phish:,}"],
                    textposition="auto",
                )
            ]
        )
        fig.update_layout(
            yaxis_title="Count",
            title=f"Total records: {total:,}",
            height=360,
            margin=dict(t=40, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as exc:
        st.warning(f"Could not load class distribution: {exc}")

    st.subheader("Top Languages")
    try:
        langs = language_distribution(top_n=15)
        if langs:
            df_lang = pd.DataFrame(langs)
            fig_lang = px.bar(
                df_lang,
                x="lang",
                y="count",
                title="Records by language (top 15)",
                labels={"lang": "Language", "count": "Count"},
            )
            fig_lang.update_layout(height=360)
            st.plotly_chart(fig_lang, use_container_width=True)
        else:
            st.info("No language data available.")
    except Exception as exc:
        st.warning(f"Language distribution unavailable: {exc}")

    st.subheader("Temporal Coverage")
    try:
        dates = date_range()
        st.markdown(
            f"- **Earliest date:** {dates.get('min_date')}\n"
            f"- **Latest date:** {dates.get('max_date')}\n"
            f"- **Records with date:** {dates.get('count_with_date', 0):,}"
        )
    except Exception as exc:
        st.warning(f"Date range unavailable: {exc}")

    st.subheader("Data-Quality Snapshot")
    try:
        report = generate_data_quality_report()
        missing = report.get("missingness", {})
        if missing:
            miss_df = pd.DataFrame(
                [
                    {"Field": k, "Missing / empty": v}
                    for k, v in missing.items()
                    if k != "total_documents"
                ]
            )
            st.dataframe(miss_df, use_container_width=True, hide_index=True)

        html_stats = report.get("html_length_sample", {})
        if html_stats:
            st.markdown(
                f"**HTML length (sample of {html_stats.get('sample_size', 0):,} records)**  \n"
                f"Avg: {html_stats.get('avg', 0):,.0f} · "
                f"Min: {html_stats.get('min', 0):,} · "
                f"Max: {html_stats.get('max', 0):,}"
            )
    except Exception as exc:
        st.warning(f"Quality report unavailable: {exc}")