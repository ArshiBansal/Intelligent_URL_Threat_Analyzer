"""
Tab 4 – Dataset Explorer

Search, filter and paginate validated PhreshPhish records by label, date,
language or other verified fields. Show record details without loading
the entire collection into memory.
"""

from __future__ import annotations

import streamlit as st
import pandas as pd
from datetime import datetime

from config.constants import (
    DATASET_DISPLAY_NAME,
    LABEL_BENIGN,
    LABEL_PHISHING,
    LABEL_DISPLAY,
    MAX_HTML_PREVIEW_CHARS,
)
from config.settings import settings
from src.db.connection import ping
from src.db.repositories import SourceRepository


def render_dataset_explorer() -> None:
    st.header("Dataset Explorer")
    st.caption(
        f"Browse validated records from the **{DATASET_DISPLAY_NAME}** dataset. "
        "All queries are paginated – the full collection is never loaded."
    )

    if not ping():
        st.error("MongoDB is unavailable. Cannot explore the dataset.")
        return

    repo = SourceRepository()

    with st.expander("Filters", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            label_filter = st.selectbox(
                "Label",
                options=["All", LABEL_DISPLAY[LABEL_BENIGN], LABEL_DISPLAY[LABEL_PHISHING]],
                index=0,
            )
        with c2:
            lang_filter = st.text_input("Language code (e.g. en, es)", value="")
        with c3:
            url_contains = st.text_input("URL contains", value="")

        c4, c5 = st.columns(2)
        with c4:
            date_from = st.text_input("Date from (YYYY-MM-DD)", value="")
        with c5:
            date_to = st.text_input("Date to (YYYY-MM-DD)", value="")

        page_size = st.slider("Page size", 10, settings.MAX_PAGE_SIZE, settings.DEFAULT_PAGE_SIZE)

    # Map display label back to storage value
    label_val = None
    if label_filter == LABEL_DISPLAY[LABEL_BENIGN]:
        label_val = LABEL_BENIGN
    elif label_filter == LABEL_DISPLAY[LABEL_PHISHING]:
        label_val = LABEL_PHISHING

    if "explorer_page" not in st.session_state:
        st.session_state.explorer_page = 1

    col_prev, col_page, col_next = st.columns([1, 2, 1])
    with col_prev:
        if st.button("← Previous", disabled=st.session_state.explorer_page <= 1):
            st.session_state.explorer_page = max(1, st.session_state.explorer_page - 1)
            st.rerun()
    with col_next:
        # We enable Next optimistically; actual bounds checked after query
        if st.button("Next →"):
            st.session_state.explorer_page += 1
            st.rerun()

    try:
        result = repo.search(
            label=label_val,
            lang=lang_filter.strip() or None,
            date_from=date_from.strip() or None,
            date_to=date_to.strip() or None,
            url_contains=url_contains.strip() or None,
            page=st.session_state.explorer_page,
            page_size=page_size,
        )
    except Exception as exc:
        st.error(f"Query failed: {exc}")
        return

    total = result["total"]
    pages = result["pages"]
    items = result["items"]

    # Clamp page if filters reduced the result set
    if st.session_state.explorer_page > pages and pages > 0:
        st.session_state.explorer_page = pages
        st.rerun()

    with col_page:
        st.markdown(
            f"**Page {result['page']} / {max(pages, 1)}**  ·  {total:,} matching records"
        )

    if not items:
        st.info("No records match the current filters.")
        return

    rows = []
    for doc in items:
        rows.append(
            {
                "sha256": doc.get("sha256", "")[:16] + "…",
                "url": (doc.get("url") or "")[:80],
                "label": LABEL_DISPLAY.get(doc.get("label"), doc.get("label")),
                "lang": doc.get("lang"),
                "date": str(doc.get("date") or ""),
            }
        )
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.subheader("Record Detail")
    selected_sha_prefix = st.selectbox(
        "Select a record (by sha256 prefix)",
        options=[r["sha256"] for r in rows],
    )
    # Resolve full sha256
    full_sha = None
    for doc in items:
        if doc.get("sha256", "").startswith(selected_sha_prefix.rstrip("…")):
            full_sha = doc["sha256"]
            break

    if full_sha:
        detail = repo.get_record(full_sha, include_html=True)
        if detail:
            st.markdown(f"**Full URL:** `{detail.get('url')}`")
            st.markdown(f"**Label:** {LABEL_DISPLAY.get(detail.get('label'), detail.get('label'))}")
            st.markdown(f"**Language:** {detail.get('lang')} (score: {detail.get('lang_score')})")
            st.markdown(f"**Date:** {detail.get('date')}")
            st.markdown(f"**Target:** {detail.get('target')}")
            html = detail.get("html") or ""
            if html:
                preview = html[:MAX_HTML_PREVIEW_CHARS]
                with st.expander("HTML preview (truncated)"):
                    st.code(preview, language="html")
            else:
                st.caption("No HTML stored for this record.")