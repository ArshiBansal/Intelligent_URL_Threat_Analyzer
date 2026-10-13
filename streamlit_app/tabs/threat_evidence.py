"""
Tab 3 – Threat Evidence & Explanation

Show extracted URL and HTML-derived signals, suspicious indicators,
and an explanation of what the model used.
Distinguish observed features from model interpretation.
"""

from __future__ import annotations

import streamlit as st
import pandas as pd

from config.constants import LABEL_DISPLAY, RESPONSIBLE_USE_NOTE
from src.features.url_features import extract_url_features
from src.features.html_features import extract_html_features
from src.utils.validation import validate_url_input, sanitize_user_input


def render_threat_evidence() -> None:
    st.header("Threat Evidence & Explanation")
    st.caption(
        "Observed features are extracted deterministically from the URL and HTML. "
        "They are **not** proof of malicious intent by themselves."
    )

    last = st.session_state.get("last_prediction")

    if last:
        st.success("Showing evidence from the most recent analysis.")
        url = last.get("url", "")
        evidence = last.get("evidence") or {}
        label = last.get("predicted_display", "Unknown")
        conf = last.get("confidence")
        st.markdown(f"**URL:** `{url}`")
        st.markdown(
            f"**Model prediction:** {label}"
            + (f" (confidence {conf:.1%})" if conf is not None else "")
        )
    else:
        st.info(
            "No recent analysis found. You can still inspect features for any URL below, "
            "or run an analysis in the **URL Threat Analyzer** tab first."
        )
        url_input = st.text_input("URL to inspect", placeholder="https://example.com")
        html_input = st.text_area("Optional HTML", height=100)
        if not url_input:
            st.stop()
        is_valid, msg, url = validate_url_input(url_input)
        if not is_valid:
            st.error(msg)
            st.stop()
        html = sanitize_user_input(html_input) if html_input else ""
        evidence = {
            **extract_url_features(url),
            **extract_html_features(html),
        }
        # keep only non-zero for display
        evidence = {k: v for k, v in evidence.items() if v != 0}

    st.subheader("Extracted Signals")

    if not evidence:
        st.warning("No non-zero features extracted.")
        return

    # Split into URL vs HTML for clarity
    url_keys = [k for k in evidence if not k.startswith(("html_", "num_forms", "num_inputs",
                                                         "num_password", "num_hidden", "num_links",
                                                         "num_external", "num_internal", "num_images",
                                                         "num_scripts", "num_iframes", "has_title",
                                                         "title_", "has_meta", "num_meta", "has_favicon",
                                                         "num_buttons", "has_login", "has_suspicious"))]
    html_keys = [k for k in evidence if k not in url_keys]

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### URL-derived features")
        if url_keys:
            df_url = pd.DataFrame(
                [{"Feature": k, "Value": evidence[k]} for k in sorted(url_keys)]
            )
            st.dataframe(df_url, use_container_width=True, hide_index=True)
        else:
            st.caption("None")

    with c2:
        st.markdown("##### HTML-derived features")
        if html_keys:
            df_html = pd.DataFrame(
                [{"Feature": k, "Value": evidence[k]} for k in sorted(html_keys)]
            )
            st.dataframe(df_html, use_container_width=True, hide_index=True)
        else:
            st.caption("None (HTML not provided or empty)")

    st.subheader("How to read these signals")
    st.markdown(
        """
- **Observed features** are factual measurements (length, counts, presence of keywords, etc.).
- The **model** combines many weak signals; no single feature proves that a page is malicious.
- High counts of password fields, external links, or login-related keywords raise suspicion
  but can also appear on legitimate sites.
- Always treat the final prediction as probabilistic decision support, not a definitive verdict.
        """
    )
    st.info(RESPONSIBLE_USE_NOTE)