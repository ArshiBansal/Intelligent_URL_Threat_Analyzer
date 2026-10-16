"""
Intelligent URL Threat Analyzer
Main Streamlit entry point.

Run with:
    streamlit run app.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import settings
from config.constants import (
    APP_TITLE,
    APP_ICON,
    PAGE_LAYOUT,
    TAB_NAMES,
    DATASET_DISPLAY_NAME,
    RESPONSIBLE_USE_NOTE,
)
from src.utils.helpers import setup_logging
from src.db.connection import ping
from src.db.indexes import ensure_indexes

# Tab renderers
from streamlit_app.tabs import (
    render_dashboard,
    render_url_threat_analyzer,
    render_threat_evidence,
    render_dataset_explorer,
    render_threat_analytics,
    render_prediction_history,
    render_model_performance,
    render_about,
)

setup_logging()
logger = logging.getLogger("app")

st.set_page_config(
    page_title=APP_TITLE,
    layout=PAGE_LAYOUT,
    initial_sidebar_state="expanded",
)

with st.sidebar:
    st.title(f"{APP_TITLE}")
    st.caption(f"Dataset: **{DATASET_DISPLAY_NAME}**")
    st.markdown("---")

    # Navigation – radio keeps a single active tab
    selected_tab = st.radio(
        "Navigation",
        options=TAB_NAMES,
        index=0,
        label_visibility="collapsed",
    )

    st.markdown("---")

    # Lightweight system status
    mongo_ok = False
    try:
        mongo_ok = ping()
    except Exception:
        mongo_ok = False

    if mongo_ok:
        st.success("MongoDB: Connected")
    else:
        st.error("MongoDB: Unavailable")
        st.caption(
            "Check MONGO_URI in your .env file and ensure the "
            "MongoDB server is running."
        )

    st.markdown("---")
    st.caption(RESPONSIBLE_USE_NOTE)


if "indexes_checked" not in st.session_state:
    if mongo_ok:
        try:
            ensure_indexes()
            logger.info("Indexes verified")
        except Exception as exc:
            logger.warning("Index check failed: %s", exc)
    st.session_state["indexes_checked"] = True


TAB_RENDERERS = {
    TAB_NAMES[0]: render_dashboard,               # Dashboard
    TAB_NAMES[1]: render_url_threat_analyzer,     # URL Threat Analyzer
    TAB_NAMES[2]: render_threat_evidence,         # Threat Evidence & Explanation
    TAB_NAMES[3]: render_dataset_explorer,        # Dataset Explorer
    TAB_NAMES[4]: render_threat_analytics,        # Threat Analytics
    TAB_NAMES[5]: render_prediction_history,      # Prediction History
    TAB_NAMES[6]: render_model_performance,       # Model Performance
    TAB_NAMES[7]: render_about,                   # About, Dataset & Methodology
}

renderer = TAB_RENDERERS.get(selected_tab)
if renderer:
    try:
        renderer()
    except Exception as exc:
        logger.exception("Tab '%s' raised an error", selected_tab)
        st.error(
            f"An unexpected error occurred while rendering **{selected_tab}**.\n\n"
            f"`{type(exc).__name__}: {exc}`"
        )
        st.info(
            "If this is a database or model-loading issue, verify that:\n"
            "1. MongoDB is running and reachable.\n"
            "2. Offline training scripts have been executed.\n"
            "3. Model artifacts exist under `artifacts/models/`."
        )
else:
    st.error(f"Unknown tab: {selected_tab}")