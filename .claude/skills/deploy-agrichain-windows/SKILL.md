---
name: deploy-agrichain-windows
description: Use when deploying, installing, or running the AgriChain blockchain supply-chain app (FastAPI backend + Streamlit dashboard) on a Windows machine, or when someone hands you the AgriChain folder/zip and asks how to start it and get a localhost URL on Windows.
---

# Deploy AgriChain on Windows

## Overview

AgriChain is a **two-process Python app**: a FastAPI backend (the authoritative
blockchain ledger, port **8000**) and a Streamlit dashboard (the user-facing UI,
port **8501**). The dashboard talks to the backend over HTTP via `config.API_BASE`.
Deploying = create a venv, install deps, (optionally) train models, then run **both**
processes in **two terminals**, and open the dashboard URL.

**Everything — ports, paths, difficulty, seeds — lives in `config.py`** (single
source of truth). Default: API `127.0.0.1:8000`, UI `127.0.0.1:8501`.

## ⚠️ First: make sure you actually have the CODE

`AgriChain_submission.zip` contains **only documentation** (`README.md`, `docs/`,
`presentation/AgriChain.pptx`) — **no code**. You **cannot deploy from that zip**.
You need the full project folder containing these, or the deploy will fail:

```
backend\  frontend\  ai\  iot\  qr\  data\  scripts\  config.py  requirements.txt
```

Verify before starting (PowerShell, from the project root):

```powershell
Test-Path .\config.py, .\requirements.txt, .\backend\main.py, .\frontend\dashboard.py
```

All must print `True`. If they don't, get the complete repo (git clone or a
full-folder zip) — not the submission bundle.

## Prerequisites

- **Python 3.11+** (developed on 3.13.7). Install from **python.org** and tick
  **"Add python.exe to PATH"**. Do NOT rely on the Microsoft Store stub.
- Verify: `python --version` (or `py -3 --version`). If `python` opens the Store,
  use `py -3` everywhere below.
- ~500 MB free disk (scikit-learn + model artifacts).

## Quick Reference (PowerShell, run from the project root)

| Step | Command |
|------|---------|
| 1. Create venv | `python -m venv .venv` |
| 2. Activate (PowerShell) | `.\.venv\Scripts\Activate.ps1` |
| 2. Activate (cmd.exe) | `.\.venv\Scripts\activate.bat` |
| 3. Upgrade pip | `python -m pip install --upgrade pip` |
| 4. Install deps | `pip install -r requirements.txt` |
| 5. *(optional)* train models | `python -m data.generate_dataset` then `python -m scripts.train_models` |
| 6. Run backend (terminal 1) | `python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000` |
| 7. Run dashboard (terminal 2) | `python -m streamlit run frontend\dashboard.py --server.port 8501` |
| 8. *(optional)* seed demo | `python scripts\seed_demo.py` |
| 9. Run tests | `python -m pytest -v` |

**Both terminals must have the venv activated** (repeat step 2 in each), OR call the
venv Python directly: `.\.venv\Scripts\python.exe -m ...`.

## URLs to open and validate

- **Dashboard (primary — validate here):** http://127.0.0.1:8501
- **API Swagger docs:** http://127.0.0.1:8000/docs
- **API health:** http://127.0.0.1:8000/ → expect `{"status":"running", ... "chain_valid":true}`

The dashboard sidebar shows live block count + chain validity. The **Verify** page
has the tamper-detection demo (the "money shot"): tamper flips `chain_valid` to
`false`; **Reset ledger** restores it.

## Convenience scripts (bundled with this skill)

From the project root:

```powershell
# One-time setup: venv + deps (+ models unless -SkipModels)
powershell -ExecutionPolicy Bypass -File .\.claude\skills\deploy-agrichain-windows\setup.ps1

# Launch backend + dashboard in two new windows, then print the URLs
powershell -ExecutionPolicy Bypass -File .\.claude\skills\deploy-agrichain-windows\run.ps1
```

These are conveniences; the manual commands in Quick Reference are the source of
truth if a script misbehaves.

## Models are optional (graceful fallback)

The trained models (`ai\models\*.joblib`) are **git-ignored**, so a fresh clone
won't have them. The app still runs: `/risk` falls back to the transparent
rule-based score, and anomaly detection refits on the fly. Train them (step 5) only
if you want the RandomForest ML score and the Regulator page's
`feature_importance.png`.

## Common Mistakes (Windows-specific)

| Symptom | Fix |
|---------|-----|
| `Activate.ps1 cannot be loaded ... execution policy` | Run PowerShell as-is: `Set-ExecutionPolicy -Scope Process RemoteSigned` then activate. Or skip activation and call `.\.venv\Scripts\python.exe -m ...` directly. |
| `python` opens Microsoft Store / wrong version | Use `py -3` instead of `python`, or install from python.org with "Add to PATH". |
| `'uvicorn'/'streamlit' is not recognized` | Venv not activated. Activate it, or use `python -m uvicorn` / `python -m streamlit`. |
| `Cannot reach the AgriChain API` in the dashboard | Backend (step 6) isn't running on port 8000. Start it first, in its own terminal. |
| `ModuleNotFoundError` | Venv not active or `pip install -r requirements.txt` didn't run in this venv. |
| Port already in use | Change the port on the command line AND in `config.py` so the UI still finds the API. |
| Blank feature-importance image on Regulator page | Run step 5 (`python -m scripts.train_models`). |
| Backslash vs forward slash | Both work in PowerShell/cmd; examples use `\`. Module targets like `backend.main:app` always use dots. |

## Verification checklist

- [ ] Code present: the `Test-Path` line above prints all `True`
- [ ] Backend: http://127.0.0.1:8000/ returns `chain_valid: true`
- [ ] Dashboard: http://127.0.0.1:8501 loads with no "Cannot reach the AgriChain API" banner
- [ ] Swagger: http://127.0.0.1:8000/docs loads
- [ ] *(if you seeded)* dashboard shows batches and a growing block count
