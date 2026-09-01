"""AgriChain shared configuration.

Single source of truth for paths, ports, blockchain difficulty and seeds so
the API, UI, QR generator and demo scripts never drift out of sync.
"""
from __future__ import annotations

from pathlib import Path

# --- Filesystem layout -----------------------------------------------------
ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
QR_DIR = ROOT / "qr" / "output"
MODELS_DIR = ROOT / "ai" / "models"
DOCS_DIR = ROOT / "docs"
PRESENTATION_DIR = ROOT / "presentation"
UPLOADS_DIR = ROOT / "data" / "uploads"

DB_PATH = ROOT / "agrichain.db"
CHAIN_PATH = ROOT / "chain.json"
DATA_CSV = DATA_DIR / "agricultural_data.csv"
RISK_MODEL_PATH = MODELS_DIR / "risk_model.joblib"
ANOMALY_MODEL_PATH = MODELS_DIR / "anomaly_model.joblib"
FEATURE_IMPORTANCE_PNG = MODELS_DIR / "feature_importance.png"
ARCHITECTURE_PNG = DOCS_DIR / "architecture.png"

# --- Blockchain ------------------------------------------------------------
DIFFICULTY = 3          # proof-of-work leading zeros for the live demo
TEST_DIFFICULTY = 2     # faster mining for the test suite / bulk seeding

# --- Networking ------------------------------------------------------------
API_HOST = "127.0.0.1"
API_PORT = 8000
UI_HOST = "127.0.0.1"
UI_PORT = 8501
API_BASE = f"http://{API_HOST}:{API_PORT}"
UI_BASE = f"http://{UI_HOST}:{UI_PORT}"

# --- Reproducibility -------------------------------------------------------
RANDOM_SEED = 42

# The fixed batch/field the tamper demo mutates so the "money shot" is
# identical on every run.
TAMPER_FIELD = "quantity_kg"
TAMPER_BAD_VALUE = 9999999


def consumer_verify_url(batch_id: str) -> str:
    """Deep link that a scanned QR code opens — lands on the Consumer verify
    page of the Streamlit UI (port 8501), NOT the raw JSON API."""
    return f"{UI_BASE}/?page=Verify&batch_id={batch_id}"


def ensure_dirs() -> None:
    for d in (DATA_DIR, QR_DIR, MODELS_DIR, DOCS_DIR, PRESENTATION_DIR, UPLOADS_DIR):
        d.mkdir(parents=True, exist_ok=True)
