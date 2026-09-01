# Frontend (this UI)

Talks to the original AgriChain API only.

```bash
# from repo root — API
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

# from frontend/
npm install
npm run dev
```

UI: http://127.0.0.1:5173  
API: http://127.0.0.1:8000  

Optional: copy `.env.example` to `.env` and set `VITE_AGRICHAIN_API_URL`.

See the root [README.md](../README.md) for the full beginner setup.
