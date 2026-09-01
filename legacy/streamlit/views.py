"""Page views for the AgriChain operations console."""
from __future__ import annotations

import json
from html import escape
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config import FEATURE_IMPORTANCE_PNG
from frontend import api_client as api
from frontend import components as ui

CROPS = ["Rice", "Maize", "Wheat", "Chilli", "Turmeric", "Groundnut", "Cotton", "Banana"]
GRADES = ["A", "B", "C"]
EVENT_TYPES = [code for code, _ in ui.PIPELINE]

DOC_TYPES = [
    "quality_certificate",
    "organic_certificate",
    "lab_report",
    "phytosanitary_certificate",
    "invoice",
]

_EVENT_DEFAULTS: dict[str, dict[str, Any]] = {
    "QUALITY_CHECK": {"moisture_percent": 12.4, "foreign_matter_percent": 0.8, "grade": "A", "quality_status": "PASSED"},
    "TRANSPORT": {"vehicle_id": "AP05AB1234", "temperature": 26.1, "humidity": 65, "distance_km": 82},
    "WAREHOUSE_ENTRY": {"storage_temperature": 24.5, "humidity": 58, "quantity_kg": 2450},
    "PROCESSING": {"process": "Milling", "input_kg": 2450, "output_kg": 1750, "quality_grade": "Premium"},
    "DISTRIBUTION": {"destination": "Retail Network", "quantity_kg": 1750},
    "RETAIL": {"selling_price": 85, "unit": "kg", "availability": "AVAILABLE"},
    "HARVEST": {"note": "Additional harvest metadata"},
}


def _batches() -> list[dict[str, Any]]:
    return api.list_batches().get("batches") or []


def _batch_ids() -> list[str]:
    return [b["batch_id"] for b in _batches()]


def _ok(resp, success: str) -> None:
    if resp.status_code == 200:
        st.success(success)
        st.json(resp.json())
    else:
        st.error(resp.text)


# ---------------------------------------------------------------------------
def page_home() -> None:
    a = api.analytics()
    valid = bool(a.get("chain_valid"))
    ui.hero(
        "Operations",
        "From farm to fork, every handoff is on the ledger.",
        "AgriChain records harvest, quality, transit, warehousing, processing "
        "and retail as hash-linked Proof-of-Work blocks. Consumers scan a QR; "
        "regulators see risk, IoT anomalies and document hashes in one place.",
    )
    ui.kpi_grid([
        ("Batches", a.get("total_batches", 0), "registered on ledger", "good" if a.get("total_batches") else ""),
        ("Volume", f"{a.get('total_kg', 0):,.0f} kg", "declared harvest mass", ""),
        ("Blocks", a.get("total_blocks", 0), "incl. genesis", ""),
        ("Integrity", "Valid" if valid else "Compromised",
         "SHA-256 + prev-hash links", "good" if valid else "warn"),
        ("Temp alerts", a.get("temperature_alerts", 0), "anomalous cold-chain batches",
         "warn" if a.get("temperature_alerts") else ""),
        ("Quality fails", a.get("quality_failures", 0), "FAILED quality checks",
         "warn" if a.get("quality_failures") else ""),
        ("Documents", len(a.get("documents") or []), "hashes anchored on-chain", ""),
        ("Farmers", len(a.get("farmer_mix") or {}), "distinct origin actors", ""),
    ])

    left, right = st.columns((1.15, 1), gap="large")
    with left:
        st.subheader("Live activity")
        events = a.get("recent_events") or []
        if not events:
            ui.empty("No events yet", "Register a harvest or run the demo seeder.")
        else:
            df = pd.DataFrame(events)
            show = df[["timestamp", "batch_id", "event_type", "actor_id", "location"]].copy()
            show["timestamp"] = show["timestamp"].astype(str).str.replace("T", " ").str[:19]
            st.dataframe(show, use_container_width=True, hide_index=True, height=360)

    with right:
        st.subheader("Crop mix")
        mix = a.get("crop_mix") or {}
        if mix:
            fig = px.pie(names=list(mix.keys()), values=list(mix.values()), hole=0.58)
            fig.update_traces(textinfo="label+percent", marker=dict(line=dict(color="#0a100c", width=2)))
            ui.plot(ui.style_fig(fig), height=230)
        else:
            ui.empty("No crop data", "Register batches to populate this chart.")

        st.subheader("Event types")
        emix = a.get("event_mix") or {}
        if emix:
            fig = px.bar(x=list(emix.keys()), y=list(emix.values()))
            fig.update_layout(xaxis_title="", yaxis_title="Count")
            ui.plot(ui.style_fig(fig), height=230)

    sensors = a.get("recent_sensors") or []
    if sensors:
        st.subheader("Cold-chain pulse")
        sdf = pd.DataFrame(sensors)
        fig = px.scatter(
            sdf, x="humidity", y="temperature", color="anomaly_flag",
            hover_data=["batch_id"], color_continuous_scale=["#8fbf88", "#e07058"],
        )
        fig.update_layout(coloraxis_showscale=False, xaxis_title="Humidity %", yaxis_title="°C")
        ui.plot(ui.style_fig(fig, "Temperature vs humidity (latest readings)"), height=300)


# ---------------------------------------------------------------------------
def page_batches() -> None:
    ui.hero("Directory", "Every batch on the ledger.",
            "Search, filter and inspect origin, status, alerts and the seven-stage journey.")
    rows = _batches()
    if not rows:
        ui.empty("Ledger is empty", "Record a harvest under Record Event, or seed the demo.")
        return

    df = pd.DataFrame(rows)
    c1, c2, c3, c4 = st.columns((2, 1, 1, 1))
    q = c1.text_input("Search", placeholder="Batch ID, farmer, location…")
    crop = c2.selectbox("Crop", ["All"] + sorted(df["crop"].dropna().unique().tolist()))
    status = c3.selectbox("Status", ["All"] + sorted(df["status"].dropna().unique().tolist()))
    alert_only = c4.checkbox("Alerts only")

    view = df.copy()
    if q:
        mask = view.apply(lambda r: q.lower() in str(r.values).lower(), axis=1)
        view = view[mask]
    if crop != "All":
        view = view[view["crop"] == crop]
    if status != "All":
        view = view[view["status"] == status]
    if alert_only:
        view = view[view["has_alert"] == True]  # noqa: E712

    display = view.rename(columns={
        "batch_id": "Batch", "crop": "Crop", "farmer": "Farmer",
        "location": "Origin", "quantity_kg": "Kg", "quality_grade": "Grade",
        "status": "Status", "events": "Events", "has_alert": "Alert",
        "created_at": "Registered",
    })
    if "Registered" in display.columns:
        display["Registered"] = display["Registered"].astype(str).str.replace("T", " ").str[:19]
    st.dataframe(display, use_container_width=True, hide_index=True, height=320)
    st.download_button(
        "Export CSV",
        display.to_csv(index=False).encode(),
        file_name="agrichain_batches.csv",
        mime="text/csv",
    )

    ids = view["batch_id"].tolist() if "batch_id" in view.columns else view["Batch"].tolist()
    if not ids:
        return
    selected = st.selectbox("Inspect batch", ids)
    _render_batch_detail(selected)


def _render_batch_detail(batch_id: str) -> None:
    r = api.batch_history(batch_id)
    if r.status_code != 200:
        st.warning("Batch not found on chain.")
        return
    data = r.json()
    b = data.get("batch") or {}
    history = data.get("history") or []
    types = [h["transaction"]["event_type"] for h in history]

    top = st.columns(5)
    top[0].metric("Crop", b.get("crop", "—"))
    top[1].metric("Quantity", f"{b.get('quantity_kg', '—')} kg")
    top[2].metric("Grade", b.get("quality_grade", "—"))
    top[3].metric("Status", b.get("status", "—"))
    top[4].metric("Integrity", "Valid" if data.get("chain_valid") else "Broken")

    st.caption("Supply-chain pipeline")
    ui.pipeline(types)

    tabs = st.tabs(["Journey", "Sensors", "QR / share"])
    with tabs[0]:
        if not history:
            ui.empty("No on-chain events", "This batch has no history yet.")
        for h in history:
            tx = h["transaction"]
            with st.expander(
                f"Block {h['block_index']}  ·  {tx['event_type']}  ·  {tx.get('location') or '—'}",
                expanded=False,
            ):
                c1, c2 = st.columns(2)
                c1.write(f"Actor `{tx.get('actor_id')}`")
                c1.write(f"Time `{tx.get('timestamp')}`")
                c2.write(f"Data hash `{ui.short_hash(tx.get('data_hash'), 20)}`")
                st.json(tx.get("data") or {})

    with tabs[1]:
        readings = data.get("sensor_readings") or []
        if not readings:
            ui.empty("No telemetry", "Stream readings from the Cold Chain page.")
        else:
            sdf = pd.DataFrame(readings)
            fig = go.Figure()
            fig.add_trace(go.Scatter(y=sdf["temperature"], name="Temp °C", mode="lines+markers"))
            fig.add_trace(go.Scatter(y=sdf["humidity"], name="Humidity %", yaxis="y2", mode="lines+markers"))
            anom = sdf[sdf["anomaly_flag"] == 1]
            if not anom.empty:
                fig.add_trace(go.Scatter(
                    x=anom.index, y=anom["temperature"], mode="markers",
                    marker=dict(size=12, color="#e07058"), name="Anomaly",
                ))
            fig.update_layout(yaxis=dict(title="°C"), yaxis2=dict(title="%", overlaying="y", side="right"))
            ui.plot(ui.style_fig(fig, "Cold-chain telemetry"), height=320)

    with tabs[2]:
        c1, c2 = st.columns((1, 2))
        with c1:
            st.image(api.qr_url(batch_id), width=220)
            st.download_button(
                "Download QR",
                api.qr_png(batch_id),
                file_name=f"{batch_id}.png",
                mime="image/png",
            )
        with c2:
            st.write("Scanning this code opens the consumer certificate for this batch.")
            st.code(batch_id)


# ---------------------------------------------------------------------------
def page_record() -> None:
    ui.hero("Capture", "Register origin, then append every handoff.",
            "Each submit mines a new block. Structured fields replace raw JSON so records stay consistent.")
    tab_reg, tab_event = st.tabs(["Register harvest", "Append event"])

    with tab_reg:
        with st.form("register"):
            c1, c2, c3 = st.columns(3)
            crop = c1.selectbox("Crop", CROPS)
            grade = c2.selectbox("Quality grade", GRADES)
            quantity = c3.number_input("Quantity (kg)", min_value=1.0, value=2500.0, step=50.0)
            c4, c5, c6 = st.columns(3)
            farmer = c4.text_input("Farmer ID", "FARMER-001")
            location = c5.text_input("Origin / mandal", "Konaseema")
            variety = c6.text_input("Variety", "BPT-5204")
            harvest_date = st.date_input("Harvest date")
            submitted = st.form_submit_button("Mine harvest block")
        if submitted:
            _ok(api.register({
                "crop": crop, "farmer": farmer, "location": location,
                "quantity_kg": quantity, "quality_grade": grade, "variety": variety,
                "harvest_date": harvest_date.isoformat(),
            }), "Harvest recorded. Batch ID is in the response below.")

    with tab_event:
        ids = _batch_ids()
        event_type = st.selectbox(
            "Event type",
            EVENT_TYPES,
            help=ui.EVENT_HELP.get("QUALITY_CHECK"),
        )
        st.caption(ui.EVENT_HELP.get(event_type, ""))
        with st.form("event"):
            batch_id = st.selectbox("Batch", ids) if ids else st.text_input("Batch ID")
            c1, c2 = st.columns(2)
            actor = c1.text_input("Actor ID", "INSPECTOR-001")
            loc = c2.text_input("Location", "Amalapuram")
            payload = _structured_event_fields(event_type)
            submitted = st.form_submit_button("Mine event block")
        if submitted and batch_id:
            _ok(api.add_event({
                "batch_id": batch_id, "event_type": event_type,
                "actor_id": actor, "location": loc, "data": payload,
            }), f"{event_type} anchored on-chain.")
        elif submitted:
            st.error("Choose a batch first.")


def _structured_event_fields(event_type: str) -> dict[str, Any]:
    defaults = _EVENT_DEFAULTS.get(event_type, {})
    if event_type == "QUALITY_CHECK":
        c1, c2, c3, c4 = st.columns(4)
        return {
            "moisture_percent": c1.number_input("Moisture %", 0.0, 40.0, float(defaults["moisture_percent"])),
            "foreign_matter_percent": c2.number_input("Foreign matter %", 0.0, 20.0, float(defaults["foreign_matter_percent"])),
            "grade": c3.selectbox("Grade", GRADES, index=0),
            "quality_status": c4.selectbox("Result", ["PASSED", "FAILED"]),
        }
    if event_type == "TRANSPORT":
        c1, c2, c3, c4 = st.columns(4)
        return {
            "vehicle_id": c1.text_input("Vehicle", defaults["vehicle_id"]),
            "temperature": c2.number_input("Temp °C", -5.0, 50.0, float(defaults["temperature"])),
            "humidity": c3.number_input("Humidity %", 0.0, 100.0, float(defaults["humidity"])),
            "distance_km": c4.number_input("Distance km", 0.0, 2000.0, float(defaults["distance_km"])),
        }
    if event_type == "WAREHOUSE_ENTRY":
        c1, c2, c3 = st.columns(3)
        return {
            "storage_temperature": c1.number_input("Storage °C", -5.0, 45.0, float(defaults["storage_temperature"])),
            "humidity": c2.number_input("Humidity %", 0.0, 100.0, float(defaults["humidity"])),
            "quantity_kg": c3.number_input("Inbound kg", 1.0, 100000.0, float(defaults["quantity_kg"])),
        }
    if event_type == "PROCESSING":
        c1, c2, c3, c4 = st.columns(4)
        return {
            "process": c1.text_input("Process", defaults["process"]),
            "input_kg": c2.number_input("Input kg", 1.0, 100000.0, float(defaults["input_kg"])),
            "output_kg": c3.number_input("Output kg", 1.0, 100000.0, float(defaults["output_kg"])),
            "quality_grade": c4.text_input("Out grade", defaults["quality_grade"]),
        }
    if event_type == "DISTRIBUTION":
        c1, c2 = st.columns(2)
        return {
            "destination": c1.text_input("Destination", defaults["destination"]),
            "quantity_kg": c2.number_input("Dispatch kg", 1.0, 100000.0, float(defaults["quantity_kg"])),
        }
    if event_type == "RETAIL":
        c1, c2, c3 = st.columns(3)
        return {
            "selling_price": c1.number_input("Price", 1.0, 10000.0, float(defaults["selling_price"])),
            "unit": c2.text_input("Unit", defaults["unit"]),
            "availability": c3.selectbox("Availability", ["AVAILABLE", "SOLD_OUT"]),
        }
    extra = st.text_area("Additional JSON", json.dumps(defaults, indent=2))
    try:
        return json.loads(extra or "{}")
    except json.JSONDecodeError as exc:
        st.error(f"Invalid JSON: {exc}")
        return {}


# ---------------------------------------------------------------------------
def page_cold_chain() -> None:
    ui.hero("IoT", "Cold-chain telemetry and anomaly detection.",
            "Simulated reefer sensors stream temperature, humidity and GPS. IsolationForest flags spikes such as a broken cooling unit.")
    ids = _batch_ids()
    if not ids:
        ui.empty("No batches", "Register produce before streaming sensors.")
        return

    c1, c2, c3, c4 = st.columns(4)
    batch_id = c1.selectbox("Batch", ids)
    n = c2.slider("Readings", 5, 40, 12)
    inject = c3.checkbox("Inject heat spike", value=True)
    if c4.button("Stream sensors"):
        res = api.stream_sensors(batch_id, n=n, inject_anomaly=inject)
        st.success(f"{res.get('message')} — anomalies: {res.get('anomalies')}")

    hist = api.batch_history(batch_id)
    if hist.status_code != 200:
        return
    readings = hist.json().get("sensor_readings") or []
    anom = api.anomalies(batch_id)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Readings", len(readings))
    k2.metric("Anomalies", len(anom.get("anomalies") or []))
    if readings:
        last = readings[-1]
        k3.metric("Last temp", f"{last['temperature']} °C")
        k4.metric("Last humidity", f"{last['humidity']} %")

    if not readings:
        ui.empty("No sensor trail", "Stream a window of readings to plot the cold chain.")
        return

    sdf = pd.DataFrame(readings)
    fig = go.Figure()
    fig.add_trace(go.Scatter(y=sdf["temperature"], name="Temperature", mode="lines+markers"))
    flagged = sdf[sdf["anomaly_flag"] == 1]
    if not flagged.empty:
        fig.add_trace(go.Scatter(
            x=flagged.index, y=flagged["temperature"], mode="markers",
            marker=dict(size=14, color="#e07058", symbol="x"), name="Flagged",
        ))
    ui.plot(ui.style_fig(fig, "Temperature (°C)"), height=300)

    fig_h = px.line(sdf, y="humidity", markers=True)
    ui.plot(ui.style_fig(fig_h, "Humidity (%)"), height=240)

    map_df = sdf.dropna(subset=["gps_lat", "gps_lon"])
    if not map_df.empty:
        fig_m = px.scatter_mapbox(
            map_df, lat="gps_lat", lon="gps_lon", color="anomaly_flag",
            hover_data=["temperature", "humidity", "timestamp"],
            zoom=8, height=380,
        )
        fig_m.update_layout(mapbox_style="carto-darkmatter", margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig_m, use_container_width=True, config={"displayModeBar": False})

    flags = anom.get("anomalies") or []
    if flags:
        st.subheader("Flagged readings")
        st.dataframe(pd.DataFrame(flags), use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
def page_risk() -> None:
    ui.hero("Intelligence", "Explainable supply-chain risk.",
            "Rule-based scoring (temperature, humidity, delay, quality) plus a RandomForest trained on the synthetic Konaseema dataset.")
    ids = _batch_ids()
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Score a live batch")
        if not ids:
            ui.empty("No batches", "Register produce to auto-score from sensors.")
        else:
            batch_id = st.selectbox("Batch", ids, key="risk_batch")
            if st.button("Score from telemetry"):
                payload = _risk_payload_from_batch(batch_id)
                if payload is None:
                    st.warning("Need at least one sensor reading on this batch.")
                else:
                    _render_risk(api.risk(payload), payload)

    with col_b:
        st.subheader("What-if laboratory")
        with st.form("risk_lab"):
            t = st.slider("Temperature °C", 0, 60, 28)
            h = st.slider("Humidity %", 0, 100, 65)
            d = st.slider("Delay hours", 0, 96, 8)
            q = st.slider("Quality score", 0, 100, 85)
            go_score = st.form_submit_button("Run model")
        if go_score:
            payload = {
                "temperature": t, "humidity": h, "delay_hours": d,
                "quality_score": q, "quantity_kg": 2000, "transport_distance_km": 100,
            }
            _render_risk(api.risk(payload), payload)

    st.subheader("Why the model cares")
    if FEATURE_IMPORTANCE_PNG.exists():
        st.image(str(FEATURE_IMPORTANCE_PNG), caption="RandomForest feature importance — temperature, delay and quality dominate.")
    else:
        st.info("Train models to see feature importance: `python -m scripts.train_models`")


def _risk_payload_from_batch(batch_id: str) -> dict[str, Any] | None:
    r = api.batch_history(batch_id)
    if r.status_code != 200:
        return None
    data = r.json()
    readings = data.get("sensor_readings") or []
    if not readings:
        return None
    last = readings[-1]
    hist = data.get("history") or []
    batch = data.get("batch") or {}
    dist = 80.0
    for h in hist:
        tx = h.get("transaction") or {}
        if tx.get("event_type") == "TRANSPORT":
            dist = float((tx.get("data") or {}).get("distance_km") or dist)
    return {
        "temperature": float(last["temperature"]),
        "humidity": float(last["humidity"]),
        "delay_hours": ui.delay_hours(hist),
        "quality_score": ui.latest_quality(hist),
        "quantity_kg": float(batch.get("quantity_kg") or 2000),
        "transport_distance_km": dist,
    }


def _render_risk(res: dict[str, Any], payload: dict[str, Any]) -> None:
    level = res.get("level", "—")
    tone = {"HIGH": "warn", "MEDIUM": "", "LOW": "good"}.get(level, "")
    ui.kpi_grid([
        ("Risk score", f"{res.get('score', '—')}/100", level, tone),
        ("ML view", res.get("ml_prediction") or "rule-only", "RandomForest when models exist", ""),
        ("Temp in", f"{payload['temperature']} °C", "latest or slider", ""),
        ("Delay in", f"{payload['delay_hours']:.1f} h", "first→last event", ""),
    ])
    factors = res.get("factors") or {}
    if factors:
        fig = go.Figure(go.Bar(x=list(factors.keys()), y=list(factors.values())))
        ui.plot(ui.style_fig(fig, "Rule contributions"), height=260)


# ---------------------------------------------------------------------------
def page_ledger() -> None:
    ui.hero("Explorer", "The authoritative chain.",
            "Each block stores index, timestamp, transactions, previous hash, nonce and SHA-256. Difficulty is three leading zeros.")
    chain = api.get_chain()
    st.caption(f"{len(chain)} blocks  ·  newest first")
    rows = []
    for b in chain:
        rows.append({
            "Index": b["index"],
            "Tx": len(b.get("transactions") or []),
            "Nonce": b.get("nonce"),
            "Hash": ui.short_hash(b.get("hash"), 14),
            "Previous": ui.short_hash(b.get("previous_hash"), 14),
            "Time": str(b.get("timestamp", ""))[:19],
        })
    st.dataframe(pd.DataFrame(list(reversed(rows))), use_container_width=True, hide_index=True, height=360)

    idx = st.number_input("Open block index", min_value=0, max_value=max(0, len(chain) - 1), value=min(1, max(0, len(chain) - 1)))
    block = next((b for b in chain if b["index"] == idx), None)
    if not block:
        return
    st.code(block.get("hash") or "", language=None)
    st.write(f"Previous `{block.get('previous_hash')}`  ·  nonce `{block.get('nonce')}`")
    if block.get("transactions"):
        st.json(block["transactions"])
    else:
        st.info("Genesis carries no supply-chain transactions.")


# ---------------------------------------------------------------------------
def page_integrity() -> None:
    ui.hero("Integrity", "Tamper evidence is the product.",
            "is_chain_valid() recomputes every hash from current transactions. Edit a stored field without re-mining and the chain fails immediately.")
    v = api.verify()
    if v.get("valid"):
        st.success(f"Ledger intact — {v.get('message')} ({v.get('blocks')} blocks)")
    else:
        st.error(v.get("message"))

    chain = api.get_chain()
    if chain:
        last = chain[-1]
        c1, c2 = st.columns(2)
        c1.write("Tip hash")
        c1.code(last.get("hash") or "")
        c2.write("Tip previous")
        c2.code(last.get("previous_hash") or "")

    st.subheader("Detection demo")
    st.write(
        "Simulate an attacker who changes `quantity_kg` on a mined harvest block "
        "and never re-mines. Verification must flip to invalid. Reset restores genesis."
    )
    c1, c2, c3 = st.columns(3)
    if c1.button("Simulate tampering"):
        t = api.tamper()
        if "field" in t:
            st.warning(
                f"Mutated `{t['field']}` on **{t['batch_id']}** "
                f"(block {t['block_index']}): {t['old_value']} → {t['new_value']}"
            )
        else:
            st.info(t.get("detail", str(t)))
        st.rerun()
    if c2.button("Re-verify"):
        st.rerun()
    if c3.button("Reset ledger"):
        api.reset()
        st.success("Ledger returned to genesis. Re-seed to restore the demo.")
        st.rerun()


# ---------------------------------------------------------------------------
def page_documents() -> None:
    ui.hero("Documents", "Files live off-chain. Proof lives on-chain.",
            "Upload a certificate; only its SHA-256 is mined into a DOCUMENT block. Re-upload later to prove the bytes never moved.")
    analytics = api.analytics()
    docs = analytics.get("documents") or []
    if docs:
        st.dataframe(pd.DataFrame(docs).drop(columns=["filepath"], errors="ignore"),
                     use_container_width=True, hide_index=True)
    else:
        st.caption("No documents recorded yet.")

    tab_upload, tab_verify = st.tabs(["Anchor a file", "Verify a file"])
    ids = _batch_ids()
    with tab_upload:
        with st.form("doc_upload"):
            batch_id = st.selectbox("Batch", ids) if ids else st.text_input("Batch ID")
            doc_type = st.selectbox("Type", DOC_TYPES)
            up = st.file_uploader("Certificate or lab report")
            go = st.form_submit_button("Record hash on blockchain")
        if go and up and batch_id:
            res = api.upload_document(batch_id, doc_type, up.name, up.getvalue())
            if "sha256" in res:
                st.success(f"Anchored on block {res['block_index']}")
                st.code(res["sha256"])
            else:
                st.error(res.get("detail", str(res)))
        elif go:
            st.error("Batch and file are required.")

    with tab_verify:
        st.write("Original file → MATCH. One edited byte → MODIFIED.")
        batch_id = st.selectbox("Batch", ids, key="doc_v_batch") if ids else st.text_input("Batch ID", key="doc_v_batch")
        up = st.file_uploader("File to check", key="doc_verify_file")
        if st.button("Compare to on-chain hash") and up and batch_id:
            r = api.verify_document(batch_id, up.name, up.getvalue())
            if r.status_code != 200:
                st.error(r.json().get("detail", r.text))
            else:
                res = r.json()
                if res["status"] == "MATCH":
                    st.success(res["message"])
                else:
                    st.error(res["message"])
                st.write("Expected", res["expected"])
                st.write("Actual", res["actual"])


# ---------------------------------------------------------------------------
def page_farmer() -> None:
    ui.hero("Farmer desk", "Your lots, volume and consumer QR.",
            "Filter by farmer ID to see harvests, current status and shareable verification codes.")
    rows = _batches()
    farmer = st.text_input("Farmer ID", "FARMER-001")
    mine = [b for b in rows if str(b.get("farmer", "")).lower() == farmer.lower()]
    if not mine:
        ui.empty("No lots for this farmer", "Register a harvest with this Farmer ID.")
        return
    df = pd.DataFrame(mine)
    ui.kpi_grid([
        ("Lots", len(mine), farmer, "good"),
        ("Volume", f"{df['quantity_kg'].sum():,.0f} kg", "declared", ""),
        ("Crops", df["crop"].nunique(), ", ".join(sorted(df["crop"].unique())), ""),
        ("Alerts", int(df["has_alert"].sum()), "cold-chain flags", "warn" if df["has_alert"].any() else ""),
    ])
    st.dataframe(
        df[["batch_id", "crop", "location", "quantity_kg", "quality_grade", "status", "events"]],
        use_container_width=True, hide_index=True,
    )
    pick = st.selectbox("QR for lot", df["batch_id"].tolist())
    c1, c2 = st.columns((1, 2))
    c1.image(api.qr_url(pick), width=220)
    c2.write("Share this with buyers. Scanning opens the public certificate — they never see farmer-only tools.")
    c2.code(pick)


# ---------------------------------------------------------------------------
def page_consumer() -> None:
    ui.hero("Certificate", "Prove origin before you buy.",
            "Enter a batch ID from the pack, or arrive here from a scanned QR.")
    qp = st.query_params
    default = qp.get("batch_id", "")
    ids = _batch_ids()
    batch_id = st.selectbox("Known batches", [""] + ids, index=(ids.index(default) + 1) if default in ids else 0)
    typed = st.text_input("Or paste a Batch ID", default)
    batch_id = typed or batch_id
    go = st.button("Verify product", type="primary") or bool(qp.get("batch_id") and batch_id)
    if not (go and batch_id):
        return
    r = api.batch_history(batch_id)
    if r.status_code != 200:
        st.error("Product not found on the ledger. Treat this as unverified.")
        return
    data = r.json()
    history = data.get("history") or []
    types = {h["transaction"]["event_type"] for h in history}
    valid = bool(data.get("chain_valid"))
    b = data.get("batch") or {}
    checks = {
        "Origin recorded": "HARVEST" in types,
        "Quality recorded": "QUALITY_CHECK" in types,
        "Chain depth": len(types) >= 3,
        "Blockchain intact": valid,
    }
    seal = "Verified authentic" if all(checks.values()) else ("Do not trust this record" if not valid else "Partial trail")
    checks_html = "".join(
        f'<div class="check"><span>{escape(label)}</span>'
        f'<span class="{"pass" if ok else "fail"}">{"Pass" if ok else "Missing"}</span></div>'
        for label, ok in checks.items()
    )
    st.markdown(
        f'<div class="cert"><div class="seal">AgriChain certificate</div>'
        f'<h2>{escape(str(batch_id))}</h2>'
        f'<p>{escape(str(b.get("crop") or "Produce"))} · {escape(str(b.get("location") or "origin n/a"))} · '
        f'{escape(str(b.get("quantity_kg") or "—"))} kg · grade {escape(str(b.get("quality_grade") or "—"))}</p>'
        f'<p><strong>{escape(seal)}</strong></p><div class="checks">{checks_html}</div></div>',
        unsafe_allow_html=True,
    )
    ui.pipeline(types)
    st.subheader("Journey")
    for h in history:
        tx = h["transaction"]
        st.write(f"**{tx['event_type']}** — {tx.get('location') or '—'} · {tx.get('actor_id')} · {str(tx.get('timestamp', ''))[:19]}")


# ---------------------------------------------------------------------------
def page_regulator() -> None:
    ui.hero("Oversight", "Network health, flags and explainable AI.",
            "Regulators see volume, integrity, quality failures and temperature alerts without opening farmer tools.")
    s = api.stats()
    a = api.analytics()
    ui.kpi_grid([
        ("Batches", s["total_batches"], "network", ""),
        ("Verified", s["verified"], "when chain is valid", "good" if s["chain_valid"] else "warn"),
        ("Flagged", s["flagged"], "quality + temp", "warn" if s["flagged"] else ""),
        ("High risk", s["high_risk"], "combined pressure", "warn" if s["high_risk"] else ""),
        ("Quality fails", s["quality_failures"], "FAILED checks", ""),
        ("Temp alerts", s["temperature_alerts"], "IsolationForest", ""),
        ("Blocks", s["total_blocks"], "PoW height", ""),
        ("Integrity", "Valid" if s["chain_valid"] else "Broken", "full recompute", "good" if s["chain_valid"] else "warn"),
    ])

    rows = _batches()
    if rows:
        df = pd.DataFrame(rows)
        flagged = df[df["has_alert"] == True]  # noqa: E712
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Status mix")
            mix = a.get("status_mix") or {}
            if mix:
                fig = px.bar(x=list(mix.keys()), y=list(mix.values()))
                ui.plot(ui.style_fig(fig), height=280)
        with c2:
            st.subheader("Flagged lots")
            if flagged.empty:
                st.info("No cold-chain alerts on current lots.")
            else:
                st.dataframe(
                    flagged[["batch_id", "crop", "location", "status", "events"]],
                    use_container_width=True, hide_index=True,
                )
        st.subheader("Network lots")
        st.dataframe(
            df[["batch_id", "crop", "farmer", "location", "quantity_kg", "status", "has_alert"]],
            use_container_width=True, hide_index=True, height=280,
        )
    if FEATURE_IMPORTANCE_PNG.exists():
        st.subheader("Model transparency")
        st.image(str(FEATURE_IMPORTANCE_PNG), caption="Risk drivers (RandomForest).")
