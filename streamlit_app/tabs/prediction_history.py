"""
Tab 6 – Prediction History

Display prior analyses, timestamps, predicted classes, model versions
and selected evidence. Supports search/filter and safe clear-history.
"""

from __future__ import annotations

import streamlit as st
import pandas as pd
from datetime import datetime

from config.constants import LABEL_DISPLAY, SUPPORTED_MODEL_NAMES
from src.db.connection import ping
from src.db.repositories import PredictionRepository


def render_prediction_history() -> None:
    st.header("Prediction History")
    st.caption("Previously analysed URLs stored in MongoDB.")

    if not ping():
        st.error("MongoDB is unavailable. History cannot be loaded.")
        return

    repo = PredictionRepository()

    c1, c2, c3 = st.columns(3)
    with c1:
        label_filter = st.selectbox(
            "Predicted label",
            options=["All"] + list(LABEL_DISPLAY.values()),
            index=0,
        )
    with c2:
        model_filter = st.selectbox(
            "Model",
            options=["All"] + SUPPORTED_MODEL_NAMES,
            index=0,
        )
    with c3:
        page_size = st.selectbox("Page size", options=[10, 25, 50, 100], index=1)

    label_val = None
    for k, v in LABEL_DISPLAY.items():
        if v == label_filter:
            label_val = k
            break
    model_val = model_filter if model_filter != "All" else None

    if "history_page" not in st.session_state:
        st.session_state.history_page = 1

    col_prev, col_info, col_next = st.columns([1, 3, 1])
    with col_prev:
        if st.button("← Prev", key="hist_prev", disabled=st.session_state.history_page <= 1):
            st.session_state.history_page = max(1, st.session_state.history_page - 1)
            st.rerun()
    with col_next:
        if st.button("Next →", key="hist_next"):
            st.session_state.history_page += 1
            st.rerun()

    try:
        result = repo.list_history(
            page=st.session_state.history_page,
            page_size=page_size,
            label=label_val,
            model_name=model_val,
        )
    except Exception as exc:
        st.error(f"Failed to load history: {exc}")
        return

    total = result["total"]
    pages = max(result["pages"], 1)
    if st.session_state.history_page > pages:
        st.session_state.history_page = pages
        st.rerun()

    with col_info:
        st.markdown(f"**Page {result['page']} / {pages}**  ·  {total:,} records")

    items = result["items"]
    if not items:
        st.info("No prediction history found.")
    else:
        rows = []
        for doc in items:
            ts = doc.get("timestamp")
            if isinstance(ts, datetime):
                ts = ts.strftime("%Y-%m-%d %H:%M:%S")
            rows.append(
                {
                    "Timestamp": ts,
                    "URL": (doc.get("url") or "")[:70],
                    "Prediction": LABEL_DISPLAY.get(
                        doc.get("predicted_label"), doc.get("predicted_label")
                    ),
                    "Confidence": f"{doc['confidence']:.1%}"
                    if doc.get("confidence") is not None
                    else "N/A",
                    "Model": f"{doc.get('model_name')} ({doc.get('model_version')})",
                }
            )
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        # Detail expander
        with st.expander("View evidence of a selected prediction"):
            idx = st.number_input(
                "Row index (0-based)",
                min_value=0,
                max_value=len(items) - 1,
                value=0,
            )
            selected = items[idx]
            st.json(
                {
                    "url": selected.get("url"),
                    "predicted_label": selected.get("predicted_label"),
                    "confidence": selected.get("confidence"),
                    "model": selected.get("model_name"),
                    "version": selected.get("model_version"),
                    "evidence": selected.get("evidence"),
                }
            )

    st.divider()
    st.subheader("Clear History")
    st.warning("This permanently deletes all stored predictions.")
    confirm = st.text_input("Type DELETE to confirm")
    if st.button("Clear all prediction history", type="secondary"):
        if confirm.strip() == "DELETE":
            try:
                deleted = repo.clear_history()
                st.success(f"Deleted {deleted:,} records.")
                st.session_state.history_page = 1
                st.rerun()
            except Exception as exc:
                st.error(f"Clear failed: {exc}")
        else:
            st.error("Confirmation text did not match. History not cleared.")