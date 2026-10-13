"""
Simple metric / status / info card helpers built with Streamlit columns.
"""

from __future__ import annotations

from typing import Optional

import streamlit as st


def metric_card(
    label: str,
    value: str | int | float,
    delta: Optional[str] = None,
    delta_color: str = "normal",
    help_text: Optional[str] = None,
) -> None:
    """
    Thin wrapper around st.metric for consistent styling.
    delta_color: "normal" | "inverse" | "off"
    """
    st.metric(
        label=label,
        value=value,
        delta=delta,
        delta_color=delta_color,
        help=help_text,
    )


def status_card(
    title: str,
    status: str,
    ok: bool = True,
    details: Optional[str] = None,
) -> None:
    """
    Display a coloured status indicator.
    """
    colour = "green" if ok else "red"
    icon = "✅" if ok else "❌"
    st.markdown(
        f"""
        <div style="
            border-left: 4px solid {colour};
            padding: 0.6rem 1rem;
            margin-bottom: 0.5rem;
            background-color: rgba(128,128,128,0.05);
            border-radius: 0 6px 6px 0;
        ">
            <strong>{icon} {title}</strong>: {status}
            {f'<br><small>{details}</small>' if details else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def info_card(
    title: str,
    body: str,
    icon: str = "ℹ️",
) -> None:
    """
    Neutral information card.
    """
    st.markdown(
        f"""
        <div style="
            border-left: 4px solid #3498db;
            padding: 0.6rem 1rem;
            margin-bottom: 0.5rem;
            background-color: rgba(52,152,219,0.07);
            border-radius: 0 6px 6px 0;
        ">
            <strong>{icon} {title}</strong><br>
            {body}
        </div>
        """,
        unsafe_allow_html=True,
    )


def warning_card(title: str, body: str) -> None:
    """Warning-styled card."""
    st.markdown(
        f"""
        <div style="
            border-left: 4px solid #f39c12;
            padding: 0.6rem 1rem;
            margin-bottom: 0.5rem;
            background-color: rgba(243,156,18,0.08);
            border-radius: 0 6px 6px 0;
        ">
            <strong>⚠️ {title}</strong><br>
            {body}
        </div>
        """,
        unsafe_allow_html=True,
    )