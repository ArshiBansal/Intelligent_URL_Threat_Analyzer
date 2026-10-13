"""
Reusable form fragments for URL input, filtering and confirmation dialogs.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import streamlit as st

from config.constants import LABEL_DISPLAY, LABEL_BENIGN, LABEL_PHISHING, SUPPORTED_MODEL_NAMES
from config.settings import settings
from src.utils.validation import validate_url_input, sanitize_user_input


def url_input_form(
    key_prefix: str = "url_form",
    show_html: bool = True,
    show_model_selector: bool = True,
    default_model: str = "random_forest",
) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
    """
    Render a complete URL-analysis form.

    Returns
    -------
    (submitted, normalized_url_or_None, cleaned_html_or_None, selected_model_or_None)
    """
    with st.form(f"{key_prefix}_form", clear_on_submit=False):
        url_raw = st.text_input(
            "URL to analyse",
            placeholder="https://example.com/login",
            key=f"{key_prefix}_url",
            help="Only http:// and https:// schemes are accepted.",
        )

        html_raw = None
        if show_html:
            html_raw = st.text_area(
                "Optional HTML content",
                height=110,
                key=f"{key_prefix}_html",
                help="Paste page HTML if available. Improves feature coverage.",
            )

        model = None
        if show_model_selector:
            idx = (
                SUPPORTED_MODEL_NAMES.index(default_model)
                if default_model in SUPPORTED_MODEL_NAMES
                else 0
            )
            model = st.selectbox(
                "Model",
                options=SUPPORTED_MODEL_NAMES,
                index=idx,
                key=f"{key_prefix}_model",
            )

        submitted = st.form_submit_button("Analyse URL", type="primary")

    if not submitted:
        return False, None, None, None

    is_valid, message, normalized = validate_url_input(url_raw)
    if not is_valid:
        st.error(message)
        return True, None, None, None

    html_clean = sanitize_user_input(html_raw) if html_raw else None
    return True, normalized, html_clean, model


def filter_form(
    key_prefix: str = "filter",
    include_label: bool = True,
    include_lang: bool = True,
    include_date: bool = True,
    include_url: bool = True,
    include_page_size: bool = True,
) -> Dict[str, Any]:
    """
    Generic filter controls used by Dataset Explorer and Prediction History.
    Returns a dictionary of filter values (ready to pass to repositories).
    """
    filters: Dict[str, Any] = {}

    cols = st.columns(3)
    col_idx = 0

    if include_label:
        with cols[col_idx % 3]:
            label_disp = st.selectbox(
                "Label",
                options=["All"] + list(LABEL_DISPLAY.values()),
                key=f"{key_prefix}_label",
            )
            label_val = None
            for k, v in LABEL_DISPLAY.items():
                if v == label_disp:
                    label_val = k
                    break
            filters["label"] = label_val
        col_idx += 1

    if include_lang:
        with cols[col_idx % 3]:
            lang = st.text_input(
                "Language code",
                value="",
                key=f"{key_prefix}_lang",
                placeholder="e.g. en",
            )
            filters["lang"] = lang.strip() or None
        col_idx += 1

    if include_url:
        with cols[col_idx % 3]:
            url_contains = st.text_input(
                "URL contains",
                value="",
                key=f"{key_prefix}_url",
            )
            filters["url_contains"] = url_contains.strip() or None
        col_idx += 1

    if include_date:
        c1, c2 = st.columns(2)
        with c1:
            date_from = st.text_input(
                "Date from (YYYY-MM-DD)",
                value="",
                key=f"{key_prefix}_from",
            )
            filters["date_from"] = date_from.strip() or None
        with c2:
            date_to = st.text_input(
                "Date to (YYYY-MM-DD)",
                value="",
                key=f"{key_prefix}_to",
            )
            filters["date_to"] = date_to.strip() or None

    if include_page_size:
        filters["page_size"] = st.slider(
            "Page size",
            min_value=10,
            max_value=settings.MAX_PAGE_SIZE,
            value=settings.DEFAULT_PAGE_SIZE,
            key=f"{key_prefix}_ps",
        )

    return filters


def confirmation_input(
    prompt: str = "Type DELETE to confirm",
    expected: str = "DELETE",
    button_label: str = "Confirm",
    key: str = "confirm",
) -> bool:
    """
    Safe confirmation pattern (used for clearing prediction history).
    Returns True only when the user types the expected string and clicks the button.
    """
    typed = st.text_input(prompt, key=f"{key}_text")
    clicked = st.button(button_label, key=f"{key}_btn", type="secondary")
    if clicked:
        if typed.strip() == expected:
            return True
        st.error(f"Confirmation text did not match “{expected}”. Action cancelled.")
    return False