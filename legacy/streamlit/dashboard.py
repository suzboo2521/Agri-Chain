"""AgriChain operations console — Streamlit frontend.

QR deep-links still open ``?page=Verify&batch_id=...`` and land on Consumer.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from config import API_BASE
from frontend import api_client as api
from frontend import theme
from frontend.views import (
    page_batches,
    page_cold_chain,
    page_consumer,
    page_documents,
    page_farmer,
    page_home,
    page_integrity,
    page_ledger,
    page_record,
    page_regulator,
    page_risk,
)

st.set_page_config(
    page_title="AgriChain",
    page_icon="A",
    layout="wide",
    initial_sidebar_state="expanded",
)
theme.apply()

PAGES = [
    "Command Center",
    "Batches",
    "Record Event",
    "Cold Chain",
    "Risk AI",
    "Ledger",
    "Integrity Lab",
    "Documents",
    "Farmer",
    "Consumer",
    "Regulator",
]

PAGE_ALIASES = {
    "Home": "Command Center",
    "Add Supply Chain Event": "Record Event",
    "Track Batch": "Batches",
    "Blockchain Explorer": "Ledger",
    "Verify Blockchain": "Integrity Lab",
    "Verify": "Consumer",
}

qp = st.query_params
default_page = PAGE_ALIASES.get(qp.get("page", "Command Center"), qp.get("page", "Command Center"))
if default_page not in PAGES:
    default_page = "Command Center"

st.sidebar.markdown(
    """
    <div class="brand">
      <div class="mark">A</div>
      <div>
        <div class="name">AgriChain</div>
        <div class="tag">Farm to fork ledger</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)


def api_up() -> bool:
    try:
        api.health()
        return True
    except Exception:
        return False


if not api_up():
    st.error(
        f"Cannot reach the AgriChain API at {API_BASE}. "
        "Start it with: `uvicorn backend.main:app --port 8000`"
    )
    st.stop()

health = api.health()
valid = bool(health.get("chain_valid"))
st.sidebar.markdown(
    f"""
    <div class="health-pill">
      <span class="muted">{health.get("blocks", "?")} blocks</span>
      <span class="{"ok" if valid else "bad"}">{"Chain valid" if valid else "Integrity alert"}</span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown('<div class="nav-label">Navigate</div>', unsafe_allow_html=True)
menu = st.sidebar.radio("Navigate", PAGES, index=PAGES.index(default_page), label_visibility="collapsed")

st.sidebar.markdown("---")
st.sidebar.caption("Single authoritative ledger · PoW SHA-256 · SQLite off-chain store")

ROUTER = {
    "Command Center": page_home,
    "Batches": page_batches,
    "Record Event": page_record,
    "Cold Chain": page_cold_chain,
    "Risk AI": page_risk,
    "Ledger": page_ledger,
    "Integrity Lab": page_integrity,
    "Documents": page_documents,
    "Farmer": page_farmer,
    "Consumer": page_consumer,
    "Regulator": page_regulator,
}
ROUTER[menu]()
