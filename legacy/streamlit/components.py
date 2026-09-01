"""Reusable UI pieces for the AgriChain console."""
from __future__ import annotations

from html import escape
from typing import Any, Iterable

import plotly.graph_objects as go
import streamlit as st

PIPELINE = [
    ("HARVEST", "Harvest"),
    ("QUALITY_CHECK", "Quality"),
    ("TRANSPORT", "Transit"),
    ("WAREHOUSE_ENTRY", "Warehouse"),
    ("PROCESSING", "Mill"),
    ("DISTRIBUTION", "Hub"),
    ("RETAIL", "Retail"),
]

EVENT_HELP = {
    "HARVEST": "Origin event — crop, quantity and grade locked to the batch.",
    "QUALITY_CHECK": "Inspector moisture, foreign-matter and pass/fail.",
    "TRANSPORT": "Vehicle, cold-chain reading and distance.",
    "WAREHOUSE_ENTRY": "Storage conditions on inbound.",
    "PROCESSING": "Milling / packing conversion.",
    "DISTRIBUTION": "Dispatch to the retail network.",
    "RETAIL": "Shelf price and availability.",
    "DOCUMENT": "Certificate hash anchored on-chain.",
}


def kpi_grid(items: list[tuple[str, str, str, str]]) -> None:
    """items: (label, value, hint, tone) where tone is '', 'good', or 'warn'."""
    cards = []
    for label, value, hint, tone in items:
        cls = f"kpi {tone}".strip()
        cards.append(
            f'<div class="{cls}"><div class="label">{escape(label)}</div>'
            f'<div class="value">{escape(str(value))}</div>'
            f'<div class="hint">{escape(hint)}</div></div>'
        )
    st.markdown(f'<div class="kpi-grid">{"".join(cards)}</div>', unsafe_allow_html=True)


def hero(kicker: str, title: str, copy: str) -> None:
    st.markdown(
        f'<div class="hero"><div class="hero-kicker">{escape(kicker)}</div>'
        f'<div class="hero-title">{escape(title)}</div>'
        f'<div class="hero-copy">{escape(copy)}</div></div>',
        unsafe_allow_html=True,
    )


def pipeline(event_types: Iterable[str]) -> None:
    seen = set(event_types)
    ordered = [code for code, _ in PIPELINE]
    current = None
    for code in reversed(ordered):
        if code in seen:
            current = code
            break
    parts = []
    for code, cap in PIPELINE:
        cls = "step"
        if code in seen and code != current:
            cls += " done"
        elif code == current:
            cls += " current"
        parts.append(
            f'<div class="{cls}"><div class="dot"></div>'
            f'<div class="cap">{escape(cap)}</div></div>'
        )
    st.markdown(f'<div class="pipeline">{"".join(parts)}</div>', unsafe_allow_html=True)


def empty(title: str, body: str) -> None:
    st.markdown(
        f'<div class="empty"><strong>{escape(title)}</strong><br>{escape(body)}</div>',
        unsafe_allow_html=True,
    )


def short_hash(value: str | None, n: int = 16) -> str:
    if not value:
        return "—"
    return value if len(value) <= n * 2 else f"{value[:n]}…{value[-6:]}"


def style_fig(fig: go.Figure, title: str | None = None) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color="#eef3ea")) if title else None,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#d7e0d4", family="IBM Plex Sans, sans-serif", size=12),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
        margin=dict(l=10, r=10, t=42 if title else 10, b=10),
        colorway=["#8fbf88", "#d4b56a", "#79c3c9", "#e07058", "#b8a1d4", "#c4d4b8"],
        hoverlabel=dict(bgcolor="#172019", font_size=12),
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.06)", zeroline=False, color="#8b9a86")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.06)", zeroline=False, color="#8b9a86")
    return fig


def plot(fig: go.Figure, height: int = 320) -> None:
    fig.update_layout(height=height)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def latest_quality(history: list[dict[str, Any]]) -> float:
    score = 82.0
    for item in history:
        tx = item.get("transaction") or item
        if tx.get("event_type") != "QUALITY_CHECK":
            continue
        data = tx.get("data") or {}
        if data.get("quality_status") == "FAILED":
            score = 48.0
        grade = str(data.get("grade") or data.get("quality_grade") or "")
        if grade == "A":
            score = 90.0
        elif grade == "B":
            score = 75.0
        elif grade == "C":
            score = 58.0
    return score


def delay_hours(history: list[dict[str, Any]]) -> float:
    stamps = []
    for item in history:
        tx = item.get("transaction") or item
        ts = tx.get("timestamp")
        if ts:
            stamps.append(ts)
    if len(stamps) < 2:
        return 0.0
    try:
        import pandas as pd

        t0 = pd.to_datetime(stamps[0], utc=True)
        t1 = pd.to_datetime(stamps[-1], utc=True)
        return max(0.0, (t1 - t0).total_seconds() / 3600.0)
    except Exception:
        return 0.0
