"""Render the AgriChain layered architecture diagram to ``docs/architecture.png``.

Run:  python -m scripts.make_architecture
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

from config import ARCHITECTURE_PNG, ensure_dirs  # noqa: E402

GREEN = "#2e7d32"
LIGHT = "#e8f5e9"
AMBER = "#f9a825"
BLUE = "#1565c0"
GREY = "#455a64"


def _box(ax, x, y, w, h, text, face, edge=GREEN, fc="#1b1b1b", fontsize=10, bold=True):
    ax.add_patch(
        FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.02,rounding_size=0.06",
            linewidth=1.6, edgecolor=edge, facecolor=face,
        )
    )
    ax.text(
        x + w / 2, y + h / 2, text,
        ha="center", va="center", fontsize=fontsize,
        color=fc, weight="bold" if bold else "normal", wrap=True,
    )


def _arrow(ax, p1, p2, color=GREY, style="-|>"):
    ax.add_patch(
        FancyArrowPatch(
            p1, p2, arrowstyle=style, mutation_scale=14,
            linewidth=1.4, color=color, shrinkA=2, shrinkB=2,
        )
    )


def main() -> int:
    ensure_dirs()
    fig, ax = plt.subplots(figsize=(11, 8))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 11)
    ax.axis("off")

    ax.text(6, 10.6, "AgriChain — System Architecture", ha="center",
            fontsize=16, weight="bold", color=GREEN)
    ax.text(6, 10.15, "Farm → Fork traceability on a tamper-evident blockchain",
            ha="center", fontsize=10, color=GREY)

    # Layer 1 — actors
    _box(ax, 0.7, 8.7, 3.0, 1.0, "Farmer / Inspector\nTransporter · Regulator", LIGHT)
    _box(ax, 8.3, 8.7, 3.0, 1.0, "Consumer\n(scans QR on phone)", LIGHT)

    # Layer 2 — UI
    _box(ax, 2.0, 6.9, 8.0, 1.1,
         "Streamlit Dashboard  (frontend/dashboard.py)\n"
         "Home · Add Event · Track · Explorer · Verify · Documents · Farmer · Consumer · Regulator",
         "#c8e6c9", fontsize=9)

    # Layer 3 — API client
    _box(ax, 3.7, 5.5, 4.6, 0.8, "HTTP  (frontend/api_client.py)", "#fff8e1",
         edge=AMBER, fontsize=9)

    # Layer 4 — backend
    _box(ax, 2.0, 3.9, 8.0, 1.1,
         "FastAPI Backend  (backend/main.py)\n"
         "Single authoritative ledger · REST API · CORS",
         "#bbdefb", edge=BLUE, fontsize=10)

    # Layer 5 — core services
    _box(ax, 0.4, 1.7, 2.05, 1.4,
         "Blockchain\nPoW · SHA-256\nprev-hash links", "#c8e6c9", fontsize=8.5)
    _box(ax, 2.75, 1.7, 2.05, 1.4,
         "SQLite\noff-chain data\n+ documents", "#c8e6c9", fontsize=8.5)
    _box(ax, 5.1, 1.7, 1.9, 1.4,
         "QR\ngenerator", "#c8e6c9", fontsize=8.5)
    _box(ax, 7.25, 1.7, 2.05, 1.4,
         "AI\nrisk (RF) +\nanomaly (IF)", "#c8e6c9", fontsize=8.5)
    _box(ax, 9.6, 1.7, 2.0, 1.4,
         "IoT\nsensor sim\n(temp/hum/GPS)", "#c8e6c9", fontsize=8.5)

    # Layer 6 — persistence
    _box(ax, 0.4, 0.3, 4.4, 0.9, "chain.json  (persisted ledger)", "#eceff1",
         edge=GREY, fc=GREY, fontsize=9)
    _box(ax, 5.1, 0.3, 6.5, 0.9, "agrichain.db  (batches · events · documents · sensors)",
         "#eceff1", edge=GREY, fc=GREY, fontsize=9)

    # Arrows
    _arrow(ax, (2.2, 8.7), (4.0, 8.0))       # farmer -> UI
    _arrow(ax, (9.8, 8.7), (8.0, 8.0))       # consumer -> UI
    _arrow(ax, (6.0, 6.9), (6.0, 6.3))       # UI -> api client
    _arrow(ax, (6.0, 5.5), (6.0, 5.0))       # api client -> backend
    for cx in (1.4, 3.75, 6.05, 8.25, 10.6):
        _arrow(ax, (6.0, 3.9), (cx, 3.1), color=BLUE)  # backend -> services
    _arrow(ax, (1.4, 1.7), (2.6, 1.2), color=GREY)      # blockchain -> chain.json
    _arrow(ax, (3.75, 1.7), (7.0, 1.2), color=GREY)     # sqlite -> db

    fig.savefig(ARCHITECTURE_PNG, dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {ARCHITECTURE_PNG}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
