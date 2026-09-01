# AGRI-CHAIN

From farm to consumer, every journey is traceable, verifiable and protected by blockchain.

This repo has **one authoritative ledger** (Python Proof-of-Work + SQLite) exposed by the original FastAPI app. The React app in `frontend/` is a multi-page AgriTech console that talks **only** to that API. It does not invent hashes, batch IDs, or stats.

## What talks to what

| Piece | Command | URL |
|---|---|---|
| **API this UI expects** | from the **repo root**: `python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000` | http://127.0.0.1:8000 · Swagger http://127.0.0.1:8000/docs |
| **This frontend** | `cd frontend && npm install && npm run dev` | http://127.0.0.1:5173 |

`backend/app` (v2, JWT, `/api/...`) is a **separate** FastAPI app. This UI does **not** use it. Leave it untouched unless you are working on v2 on purpose.

All browser HTTP goes through `frontend/src/lib/api.ts`. Base URL:

`import.meta.env.VITE_AGRICHAIN_API_URL` (default `http://127.0.0.1:8000`)

Copy `frontend/.env.example` to `frontend/.env` if you need to change it.

## Beginner setup (macOS / Linux)

You need **Python 3.11+** and **Node 18+**. Open two terminals in the project folder.

**Terminal 1 — API (original ledger)**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Check http://127.0.0.1:8000 — you should see `"status": "running"`.

**Terminal 2 — UI**

```bash
cd frontend
npm install
npm run dev
```

Open **http://127.0.0.1:5173**

Optional demo data (with the API already running):

```bash
python scripts/seed_demo.py
```

## Windows (PowerShell)

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Second terminal: `cd frontend; npm install; npm run dev`

If PowerShell blocks the venv: `Set-ExecutionPolicy -Scope Process RemoteSigned`

## Production build (frontend)

```bash
cd frontend
npm install
npm run build
npm run preview
```

## API this UI uses

These paths live on `backend/main.py`:

`GET /` · `POST /register` · `POST /event` · `GET /batch/{batch_id}` · `GET /blockchain` · `GET /verify` · `POST /sensor` · `POST /sensor/stream` · `GET /anomalies/{batch_id}` · `POST /risk` · `GET /qr/{batch_id}` · `POST /document` · `GET /document/{batch_id}` · `POST /document/verify` · `GET /batches` · `GET /activity` · `GET /analytics` · `GET /stats` · `POST /debug/tamper` · `POST /debug/reset`

QR codes encode `?page=Verify&batch_id=...`. This UI accepts that query string and opens the product passport.

## Product pages

Home / Dashboard · Register batch · Traceability · Verify product · QR verification · IoT monitoring · AI risk · Documents · Blockchain explorer · Analytics · Batch directory

Tamper demo (explorer): mutates a mined transaction without re-mining, then `GET /verify` should report a compromised chain. **Reset ledger** restores genesis.

## Tests (Python ledger)

```bash
source .venv/bin/activate
python -m pytest -v
```

## Docker note

`docker compose up --build` still starts the **v2** API (`backend/app`). For this frontend, run `uvicorn backend.main:app` locally as above.

The old Streamlit UI is archived under `legacy/streamlit/` if it is present.

## Team

Hackathon team — AgriChain.
