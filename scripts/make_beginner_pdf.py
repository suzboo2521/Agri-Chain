from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, ListFlowable, ListItem
from reportlab.lib.colors import HexColor
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "docs" / "AgriChain_Beginner_Setup_Guide.pdf"


def p(text, style):
    return Paragraph(text.replace("\n", "<br/>"), style)


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(OUT), pagesize=A4, title="AgriChain v2 — Beginner Setup Guide")
    styles = getSampleStyleSheet()
    h = ParagraphStyle("h", parent=styles["Heading1"], textColor=HexColor("#0b3d2e"), fontSize=18, spaceAfter=10)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], textColor=HexColor("#145c43"), fontSize=13, spaceBefore=10, spaceAfter=6)
    b = ParagraphStyle("b", parent=styles["BodyText"], fontSize=10, leading=14, spaceAfter=6)
    code = ParagraphStyle("c", parent=styles["Code"], fontSize=8, leading=11, backColor=HexColor("#eef6f1"), spaceAfter=8)
    story = []
    story += [
        p("AgriChain v2 — Complete beginner guide", h),
        p("From Farm to Fork — Verified, Transparent and Traceable.", b),
        p("This PDF tells you exactly what to install, which folder to open, which commands to type, which URL to click, and how the frontend talks to the backend. Follow the steps in order. Do not skip.", b),
        p("1. What you are building", h2),
        p("AgriChain has two programs that must run at the same time: (1) Backend API on port 8000 — Python FastAPI, database, blockchain, AI, IoT. (2) Frontend website on port 5173 — React dark dashboard. The website calls the API. If only one is running, login will fail.", b),
        p("2. Install software (one time)", h2),
        p("<b>macOS / Linux</b>", b),
        p("Install Python 3.11+ from python.org. Install Node.js 20+ from nodejs.org (LTS). In Terminal: python3 --version and node --version must print numbers.", b),
        p("<b>Windows</b>", b),
        p("Install Python from python.org and tick Add python.exe to PATH. Install Node.js LTS. Open PowerShell. If python opens the Microsoft Store, use py -3 instead of python in every command below.", b),
        p("3. Open the project in VS Code", h2),
        p("File → Open Folder → select the AgriChain folder (the folder that contains frontend, backend, README.md). Open Terminal → New Terminal. You should be inside AgriChain.", b),
        p("4. Backend setup", h2),
        p("macOS / Linux:", b),
        p("cd backend<br/>python3 -m venv .venv<br/>source .venv/bin/activate<br/>pip install -r requirements.txt", code),
        p("Windows PowerShell:", b),
        p("cd backend<br/>py -3 -m venv .venv<br/>.\\.venv\\Scripts\\Activate.ps1<br/>pip install -r requirements.txt", code),
        p("If Activate.ps1 is blocked: Set-ExecutionPolicy -Scope Process RemoteSigned", b),
        p("Copy environment file from project root:", b),
        p("cd ..<br/>copy .env.example .env     (Windows)<br/>cp .env.example .env       (macOS/Linux)", code),
        p("You can leave the default SECRET_KEY for local demo. Never use it on the public internet.", b),
        p("5. Start the backend (Terminal 1)", h2),
        p("cd backend<br/>source .venv/bin/activate   (Windows: .venv\\Scripts\\activate)<br/>python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000", code),
        p("Wait until you see Application startup complete. First start creates the database and mines demo blocks (30–90 seconds). Then open http://127.0.0.1:8000/docs — this is Swagger. If it opens, backend works. http://127.0.0.1:8000/api/health should show status ok and chain_valid true.", b),
        p("6. Frontend setup (Terminal 2 — NEW terminal)", h2),
        p("cd frontend<br/>npm install<br/>npm run dev", code),
        p("Open http://127.0.0.1:5173 — dark landing page. Vite proxies /api to port 8000, so you do not type the API URL yourself.", b),
        p("7. Login (how frontend connects to backend)", h2),
        p("Click Login. Email admin@agrichain.local password Demo@12345. The site POSTs JSON to /api/auth/login. Backend checks the password hash, returns a JWT. The site stores the token and sends Authorization: Bearer … on every later request. If login fails: backend not running, wrong password, or CORS. Farmer account cannot open Users page (403) — that is correct RBAC.", b),
        p("8. Click-by-click demo for judges", h2),
    ]
    steps = [
        "Landing page: read hero, animated farm-to-fork steps, hash ticker.",
        "Login as admin@agrichain.local / Demo@12345.",
        "Dashboard: totals, temperature chart, live blockchain card.",
        "Batches → open RICE-KONASEEMA-2026-0001 → QR + timeline + AgriTrust score.",
        "Quality page: moisture 12.4, submit, see Grade A.",
        "Tracking: load route map (OpenStreetMap, no paid key).",
        "IoT: Simulate reading, then Inject 89°C. Graph spikes. AI should flag anomaly.",
        "AI Risk Center: click MAIZE-ELURU-2026-0004 or the spiked rice batch. Read reasons and bar importance — this is Isolation Forest + rules, not random text.",
        "Blockchain explorer: Verify entire chain → valid. Simulate tampering → INTEGRITY COMPROMISED and failed block number. Restore demo state.",
        "Open /verify/RICE-KONASEEMA-2026-0001 (or scan QR). Consumer page: Authentic Product, four checks, trust score. No blockchain jargon.",
        "Documents: upload a txt, then verify same file (VERIFIED) vs edited file (COMPROMISED).",
        "Recall: start recall on CHILLI-GUNTUR-2026-0003, see downstream locations.",
        "Hackathon Demo page: Next walks 10 presentation steps.",
        "Logout. Login as farmer@agrichain.local. Sidebar hides admin Users/Audit.",
        "Optional: Telugu toggle in the header.",
    ]
    story.append(ListFlowable([ListItem(p(s, b)) for s in steps], bulletType="1"))
    story += [
        p("9. Demo accounts (all password Demo@12345)", h2),
        p("admin, farmer, collection, inspector, transporter, warehouse, processor, distributor, retailer, regulator, consumer — each is email like farmer@agrichain.local", b),
        p("10. How layers connect", h2),
        p("Browser (React) → HTTP JSON → FastAPI → SQLite off-chain data + Python SHA-256 PoW chain (on-chain hashes) → IsolationForest risk → IoT simulator writes sensor_readings → QR encodes http://127.0.0.1:5173/verify/BATCH_ID. Solidity contract in /contracts is optional; BLOCKCHAIN_MODE=python is default and does not need MetaMask.", b),
        p("11. Tests", h2),
        p("cd backend<br/>source .venv/bin/activate<br/>python -m pytest -v", code),
        p("12. Docker (optional)", h2),
        p("From project root: docker compose up --build. UI http://127.0.0.1:8080 API http://127.0.0.1:8000/docs", code),
        p("13. If something breaks", h2),
        p("Port in use: close the other app or change port. ModuleNotFoundError: activate venv and pip install again. Blank UI data: backend must be on 8000. Tamper stays red: click Restore demo state. Camera QR scanner needs HTTPS or localhost permission.", b),
        p("14. What NOT to claim", h2),
        p("This is a hackathon prototype. Python PoW is not Ethereum mainnet. Sustainability numbers are estimates. Price charts are recorded values, not a fairness guarantee.", b),
        PageBreak(),
        p("API map (frontend path → backend)", h2),
        p("POST /api/auth/login · GET /api/auth/me · GET /api/dashboard · GET/POST /api/batches · GET /api/batches/{id} · GET /api/batches/{id}/qr · POST /api/events · POST /api/quality · POST /api/sensor-data · POST /api/sensor-data/anchor · GET /api/risk/{id} · GET /api/blockchain · GET /api/blockchain/verify · POST /api/debug/tamper · POST /api/debug/restore · POST /api/documents/hash · POST /api/documents/verify · GET /api/verify/{id} · POST /api/recalls · GET /api/analytics · GET /api/health · GET /docs", b),
        p("You now have the full loop: Agricultural data → IoT → AI risk → blockchain integrity → QR → consumer trust.", b),
    ]
    doc.build(story)
    print("Wrote", OUT)


if __name__ == "__main__":
    main()
