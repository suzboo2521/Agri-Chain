# AgriChain — Installation & Setup Guide

This guide takes you from a fresh clone to a running system with the dashboard,
API, seeded demo data, trained models and passing tests.

---

## 1. Prerequisites

- **Python 3.11+** (developed and tested on **Python 3.13.7**)
- **pip** and **venv** (bundled with Python)
- macOS / Linux / Windows (commands below use a POSIX shell; Windows notes inline)
- ~500 MB free disk (mostly for scikit-learn / model artifacts)

Check your Python:

```bash
python3 --version   # expect 3.11 or newer
```

## 2. Create and activate a virtual environment

```bash
cd AgriChain

python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows (PowerShell/cmd)
```

## 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This installs FastAPI, Uvicorn, Streamlit, Plotly, scikit-learn, NumPy, Pandas,
matplotlib, qrcode/Pillow, python-pptx, pytest and httpx.

## 4. (Optional) Regenerate dataset and ML models

The repo already ships trained models, but you can rebuild everything
reproducibly (`RANDOM_SEED = 42`):

```bash
python -m data.generate_dataset      # writes data/agricultural_data.csv (~1000 rows)
python -m scripts.train_models       # writes ai/models/{risk_model,anomaly_model}.joblib + feature_importance.png
python -m scripts.make_architecture  # writes docs/architecture.png
```

## 5. Run the backend (API)

```bash
uvicorn backend.main:app --port 8000
```

- Health check: <http://127.0.0.1:8000/>
- Interactive Swagger docs: <http://127.0.0.1:8000/docs>

Leave this running in its own terminal.

## 6. Run the dashboard (UI)

In a **second terminal** (venv active, API running):

```bash
streamlit run frontend/dashboard.py
```

Open <http://127.0.0.1:8501>. The sidebar shows live block count and chain
validity. If you see "Cannot reach the AgriChain API", make sure step 5 is
running on port 8000.

## 7. Seed demo data (optional but recommended)

With the API running, populate a realistic demo (5 batches × 7 events):

```bash
python scripts/seed_demo.py
```

## 8. Run the tests

```bash
python -m pytest -v
```

Expected: **21 passed**. Tests run against an isolated temporary ledger and do
**not** modify your seeded `chain.json` / `agrichain.db`.

## 9. Build the presentation & submission bundle (optional)

```bash
python -m presentation.make_deck    # → presentation/AgriChain.pptx
python -m scripts.make_submission    # → AgriChain_submission.zip
```

---

## Ports & configuration

All paths, ports, difficulty and seeds live in **`config.py`** (single source of
truth):

| Setting | Default |
|---------|---------|
| API | `127.0.0.1:8000` |
| UI | `127.0.0.1:8501` |
| PoW difficulty (live) | `3` |
| PoW difficulty (tests/bulk) | `2` |
| Random seed | `42` |

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `Cannot reach the AgriChain API` in the UI | Start the backend (step 5) on port 8000. |
| `ModuleNotFoundError` | Ensure the venv is activated and `pip install -r requirements.txt` ran. |
| Port already in use | Change the port: `uvicorn backend.main:app --port 8010` (and update `config.py` if needed). |
| Blank feature-importance image on Regulator page | Run `python -m scripts.train_models`. |
| Want a clean ledger | Call `POST /debug/reset` (or delete `chain.json` and `agrichain.db`). |
| Chain shows as invalid after the tamper demo | Click **Reset ledger** on the Verify page, or `POST /debug/reset`. |
