"""Visual system for the AgriChain operations console."""

from __future__ import annotations

import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,560;9..144,700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

:root {
  --ink: #0a100c;
  --pine: #111914;
  --panel: #172019;
  --panel-2: #1e2a21;
  --line: rgba(196, 214, 188, 0.12);
  --text: #eef3ea;
  --muted: #8b9a86;
  --sage: #8fbf88;
  --wheat: #d4b56a;
  --alert: #e07058;
  --ok: #6ecf8a;
  --info: #79c3c9;
  --radius: 8px;
}

html, body, [data-testid="stAppViewContainer"], .stApp {
  background: var(--ink) !important;
  color: var(--text);
  font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
}

.stApp {
  background:
    radial-gradient(1200px 500px at 12% -10%, rgba(143, 191, 136, 0.10), transparent 55%),
    radial-gradient(900px 420px at 100% 0%, rgba(212, 181, 106, 0.07), transparent 50%),
    var(--ink) !important;
}

[data-testid="stHeader"] {
  background: transparent !important;
}
[data-testid="stToolbar"], [data-testid="stDecoration"],
#MainMenu, footer, .stAppDeployButton, [data-testid="stStatusWidget"] {
  visibility: hidden;
  height: 0;
  display: none !important;
}

.block-container {
  padding-top: 1.35rem !important;
  padding-bottom: 3.5rem !important;
  max-width: 1240px !important;
}

section[data-testid="stSidebar"] {
  background: var(--pine) !important;
  border-right: 1px solid var(--line);
}
section[data-testid="stSidebar"] * {
  font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
}
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
  color: var(--muted);
}

.brand {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 4px 2px 18px;
  border-bottom: 1px solid var(--line);
  margin-bottom: 14px;
}
.brand .mark {
  width: 36px;
  height: 36px;
  border-radius: 9px;
  background: linear-gradient(160deg, #2d4a32 0%, #8fbf88 100%);
  color: #0a100c;
  font-family: Fraunces, Georgia, serif;
  font-weight: 700;
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  letter-spacing: -0.04em;
}
.brand .name {
  font-family: Fraunces, Georgia, serif;
  font-size: 1.15rem;
  color: var(--text);
  line-height: 1.1;
}
.brand .tag {
  font-size: 0.72rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--muted);
  margin-top: 3px;
}

.health-pill {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 10px 12px;
  border: 1px solid var(--line);
  background: var(--panel);
  border-radius: var(--radius);
  margin: 8px 0 16px;
  font-size: 0.82rem;
}
.health-pill .ok { color: var(--ok); font-weight: 600; }
.health-pill .bad { color: var(--alert); font-weight: 600; }
.health-pill .muted { color: var(--muted); }

.nav-label {
  font-size: 0.68rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--muted);
  margin: 12px 0 6px;
}

h1, h2, h3, .hero-title {
  font-family: Fraunces, Georgia, serif !important;
  letter-spacing: -0.02em;
  color: var(--text) !important;
}
h1 { font-size: 2rem !important; font-weight: 560 !important; }
h2 { font-size: 1.35rem !important; }
h3 { font-size: 1.12rem !important; }

.hero {
  padding: 8px 0 6px;
}
.hero-kicker {
  font-size: 0.72rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--wheat);
  margin-bottom: 8px;
}
.hero-title {
  font-size: 2.15rem;
  margin: 0 0 8px;
}
.hero-copy {
  color: var(--muted);
  max-width: 62ch;
  line-height: 1.55;
  font-size: 0.98rem;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 12px;
  margin: 18px 0 8px;
}
.kpi {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 14px 16px 12px;
  min-height: 92px;
}
.kpi .label {
  font-size: 0.7rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--muted);
}
.kpi .value {
  font-family: Fraunces, Georgia, serif;
  font-size: 1.7rem;
  margin-top: 6px;
  color: var(--text);
  line-height: 1.1;
}
.kpi .hint {
  font-size: 0.78rem;
  color: var(--muted);
  margin-top: 6px;
}
.kpi.warn { border-color: rgba(224, 112, 88, 0.45); }
.kpi.good { border-color: rgba(110, 207, 138, 0.35); }

.panel {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 16px 18px;
  margin: 8px 0 16px;
}
.panel h3 { margin: 0 0 10px; }

.pipeline {
  display: flex;
  gap: 0;
  overflow-x: auto;
  padding: 6px 0 14px;
}
.step {
  flex: 1;
  min-width: 108px;
  text-align: center;
  position: relative;
  padding: 0 6px;
}
.step .dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin: 0 auto 8px;
  background: #2a382c;
  border: 2px solid #3d5140;
  position: relative;
  z-index: 1;
}
.step.done .dot { background: var(--sage); border-color: var(--sage); }
.step.current .dot { background: var(--wheat); border-color: var(--wheat); box-shadow: 0 0 0 4px rgba(212,181,106,0.18); }
.step .cap {
  font-size: 0.72rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--muted);
}
.step.done .cap { color: var(--sage); }
.step.current .cap { color: var(--wheat); }
.step:not(:last-child)::after {
  content: "";
  position: absolute;
  top: 6px;
  left: 50%;
  width: 100%;
  height: 2px;
  background: #2a382c;
  z-index: 0;
}
.step.done:not(:last-child)::after { background: var(--sage); }

.cert {
  background: linear-gradient(180deg, #1c261e 0%, #141c16 100%);
  border: 1px solid var(--line);
  border-top: 3px solid var(--wheat);
  border-radius: 10px;
  padding: 22px 24px;
}
.cert .seal {
  font-size: 0.72rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--wheat);
}
.cert h2 { margin: 6px 0 4px; }
.checks { margin-top: 14px; }
.check {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid var(--line);
  font-size: 0.92rem;
}
.check .pass { color: var(--ok); }
.check .fail { color: var(--alert); }

.empty {
  border: 1px dashed var(--line);
  border-radius: var(--radius);
  padding: 28px 18px;
  text-align: center;
  color: var(--muted);
}
.hash {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.78rem;
  color: var(--info);
  word-break: break-all;
}

div[data-testid="stMetric"] {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 8px 12px;
}
div[data-testid="stMetric"] label { color: var(--muted) !important; }

.stButton > button {
  background: var(--sage) !important;
  color: #0a100c !important;
  border: 0 !important;
  border-radius: 7px !important;
  font-weight: 600 !important;
}
.stButton > button:hover { filter: brightness(1.05); }
.stButton > button[kind="secondary"] {
  background: transparent !important;
  color: var(--text) !important;
  border: 1px solid var(--line) !important;
}

[data-testid="stForm"] {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 8px 12px 4px;
}

[data-baseweb="tab-list"] {
  gap: 6px;
  background: transparent;
  border-bottom: 1px solid var(--line);
}
button[data-baseweb="tab"] {
  color: var(--muted) !important;
  font-weight: 500 !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
  color: var(--text) !important;
}

[data-testid="stExpander"] {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: var(--radius);
}

.stAlert { border-radius: var(--radius); }

hr { border-color: var(--line) !important; }

@media (max-width: 980px) {
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
"""


def apply() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
