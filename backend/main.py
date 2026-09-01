"""AgriChain FastAPI backend — the single authoritative ledger + REST API."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from config import (
    ANOMALY_MODEL_PATH,
    RANDOM_SEED,
    TAMPER_BAD_VALUE,
    TAMPER_FIELD,
    UPLOADS_DIR,
)
from backend.database import calculate_data_hash, calculate_file_hash
from backend.ledger import get_chain, get_db, persist, reset_all
from backend.models import (
    EventResponse,
    ProductRegistration,
    RegistrationResponse,
    RiskInput,
    RiskResult,
    SensorReading,
    StatsResponse,
    SupplyChainEvent,
    VerifyResponse,
)

app = FastAPI(
    title="AgriChain API",
    description="Blockchain-based agricultural supply-chain transparency: "
    "tamper-resistant, end-to-end traceability from farm to consumer.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _detect_anomalies(readings: list[dict]) -> list[bool]:
    """Flag anomalous (temperature, humidity) readings.

    Uses the persisted IsolationForest model (``anomaly_model.joblib``, produced
    by ``python -m scripts.train_models``) when it exists, otherwise fits an
    ad-hoc detector on just these readings. Behaviour is unchanged when no model
    is present.
    """
    from ai.anomaly import detect_with_model, fit_detect

    if ANOMALY_MODEL_PATH.exists():
        try:
            import joblib

            model = joblib.load(ANOMALY_MODEL_PATH)
            return detect_with_model(model, readings)
        except Exception:
            pass  # fall back to ad-hoc detection
    return fit_detect(readings)


# --------------------------------------------------------------------------
@app.get("/")
def home():
    chain = get_chain()
    return {
        "message": "AgriChain Blockchain API",
        "status": "running",
        "blocks": len(chain.chain),
        "chain_valid": chain.is_chain_valid(),
    }


@app.post("/register", response_model=RegistrationResponse)
def register_product(reg: ProductRegistration):
    chain, db = get_chain(), get_db()
    year = datetime.now(timezone.utc).year
    seq = db.next_sequence(reg.crop, reg.location, year)
    batch_id = f"{reg.crop[:4].upper()}-{reg.location[:6].upper()}-{year}-{seq:04d}"

    db.create_batch(
        batch_id, reg.crop, reg.farmer, reg.location, reg.quantity_kg, reg.quality_grade
    )
    data = {
        "crop": reg.crop,
        "variety": reg.variety,
        "quantity_kg": reg.quantity_kg,
        "harvest_date": reg.harvest_date,
        "quality_grade": reg.quality_grade,
    }
    tx = {
        "batch_id": batch_id,
        "event_type": "HARVEST",
        "actor_id": reg.farmer,
        "location": reg.location,
        "timestamp": _now(),
        "data": data,
        "data_hash": calculate_data_hash(data),
    }
    chain.add_transaction(tx)
    block = chain.mine_pending_transactions()
    db.insert_event(
        batch_id, "HARVEST", reg.farmer, reg.location, tx["timestamp"],
        data, tx["data_hash"], block.index,
    )
    persist()
    return RegistrationResponse(
        message="Product registered and HARVEST event recorded on-chain.",
        batch_id=batch_id,
        block_index=block.index,
        block_hash=block.hash,
    )


@app.post("/event", response_model=EventResponse)
def add_event(event: SupplyChainEvent):
    chain, db = get_chain(), get_db()
    timestamp = event.timestamp or _now()
    data_hash = calculate_data_hash(event.data)
    tx = {
        "batch_id": event.batch_id,
        "event_type": event.event_type.value,
        "actor_id": event.actor_id,
        "location": event.location,
        "timestamp": timestamp,
        "data": event.data,
        "data_hash": data_hash,
    }
    chain.add_transaction(tx)
    block = chain.mine_pending_transactions()
    db.insert_event(
        event.batch_id, event.event_type.value, event.actor_id, event.location,
        timestamp, event.data, data_hash, block.index,
    )
    # advance batch status to the latest event type
    if db.get_batch(event.batch_id):
        db.set_status(event.batch_id, event.event_type.value)
    persist()
    return EventResponse(
        message="Event added successfully.",
        block_index=block.index,
        block_hash=block.hash,
    )


@app.get("/blockchain")
def get_blockchain():
    return [b.to_dict() for b in get_chain().chain]


@app.get("/verify", response_model=VerifyResponse)
def verify_blockchain():
    chain = get_chain()
    valid = chain.is_chain_valid()
    return VerifyResponse(
        valid=valid,
        message=(
            "Blockchain is valid and has not been tampered with."
            if valid
            else "INTEGRITY COMPROMISED — the ledger has been tampered with!"
        ),
        blocks=len(chain.chain),
    )


@app.get("/batch/{batch_id}")
def get_batch(batch_id: str):
    chain, db = get_chain(), get_db()
    history = chain.get_batch_history(batch_id)
    batch = db.get_batch(batch_id)
    if not history and not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    readings = db.get_sensor_readings(batch_id)
    return {
        "batch_id": batch_id,
        "batch": batch,
        "history": history,
        "sensor_readings": readings,
        "chain_valid": chain.is_chain_valid(),
        "verified": chain.is_chain_valid() and bool(history),
    }


@app.post("/sensor")
def add_sensor(reading: SensorReading):
    db = get_db()
    ts = reading.timestamp or _now()
    existing = db.get_sensor_readings(reading.batch_id)
    all_readings = [
        {"temperature": r["temperature"], "humidity": r["humidity"]} for r in existing
    ] + [{"temperature": reading.temperature, "humidity": reading.humidity}]
    flags = _detect_anomalies(all_readings)
    anomaly_flag = int(flags[-1]) if flags else 0
    db.insert_sensor_reading(
        reading.batch_id, reading.temperature, reading.humidity,
        reading.gps_lat, reading.gps_lon, ts, anomaly_flag,
    )
    return {"message": "sensor reading stored", "anomaly": bool(anomaly_flag)}


@app.post("/sensor/stream")
def stream_sensors(batch_id: str, n: int = 10, inject_anomaly: bool = False):
    import numpy as np

    from iot.sensor_sim import generate_sensor_data

    db = get_db()
    rng = np.random.default_rng(RANDOM_SEED)
    readings = generate_sensor_data(batch_id, n, inject_anomaly=inject_anomaly, rng=rng)
    flags = _detect_anomalies(
        [{"temperature": r["temperature"], "humidity": r["humidity"]} for r in readings]
    )
    for r, flag in zip(readings, flags):
        db.insert_sensor_reading(
            batch_id, r["temperature"], r["humidity"],
            r["gps_lat"], r["gps_lon"], r["timestamp"], int(flag),
        )
    return {
        "message": f"{n} sensor readings recorded",
        "anomalies": int(sum(flags)),
    }


@app.get("/anomalies/{batch_id}")
def get_anomalies(batch_id: str):
    db = get_db()
    readings = db.get_sensor_readings(batch_id)
    anomalies = [r for r in readings if r["anomaly_flag"]]
    return {"batch_id": batch_id, "total": len(readings), "anomalies": anomalies}


@app.post("/risk", response_model=RiskResult)
def risk(inp: RiskInput):
    from ai.risk import calculate_risk, load_model, predict_risk

    result = calculate_risk(
        inp.temperature, inp.humidity, inp.delay_hours, inp.quality_score
    )
    model = load_model()
    ml = predict_risk(model, inp.model_dump()) if model else None
    return RiskResult(
        score=result["score"], level=result["level"],
        factors=result["factors"], ml_prediction=ml,
    )


@app.get("/qr/{batch_id}")
def get_qr(batch_id: str):
    from qr.qr_generator import generate_qr

    path = generate_qr(batch_id)
    return FileResponse(path, media_type="image/png", filename=f"{batch_id}.png")


# --- Documents (off-chain files, on-chain hashes) --------------------------
@app.post("/document")
def upload_document(
    batch_id: str = Form(...),
    doc_type: str = Form("certificate"),
    file: UploadFile = File(...),
):
    """Store an uploaded certificate/document off-chain and record its SHA-256
    hash on the blockchain, so any later modification is detectable."""
    chain, db = get_chain(), get_db()
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    dest = UPLOADS_DIR / f"{batch_id}__{file.filename}"
    with open(dest, "wb") as fh:
        fh.write(file.file.read())
    sha256 = calculate_file_hash(str(dest))

    data = {"filename": file.filename, "doc_type": doc_type, "sha256": sha256}
    tx = {
        "batch_id": batch_id,
        "event_type": "DOCUMENT",
        "actor_id": "DOCUMENT_UPLOADER",
        "location": "",
        "timestamp": _now(),
        "data": data,
        "data_hash": calculate_data_hash(data),
    }
    chain.add_transaction(tx)
    block = chain.mine_pending_transactions()
    db.insert_document(batch_id, file.filename, str(dest), sha256)
    persist()
    return {
        "message": "Document stored off-chain; SHA-256 recorded on-chain.",
        "batch_id": batch_id,
        "filename": file.filename,
        "doc_type": doc_type,
        "sha256": sha256,
        "block_index": block.index,
        "block_hash": block.hash,
    }


@app.get("/document/{batch_id}")
def list_documents(batch_id: str):
    return {"batch_id": batch_id, "documents": get_db().list_documents(batch_id)}


@app.post("/document/verify")
def verify_document(batch_id: str = Form(...), file: UploadFile = File(...)):
    """Recompute the SHA-256 of an uploaded file and compare it against the hash
    recorded on-chain for this batch. Detects a modified certificate."""
    chain = get_chain()
    actual = hashlib.sha256(file.file.read()).hexdigest()

    recorded = [
        {
            "filename": h["transaction"]["data"].get("filename"),
            "sha256": h["transaction"]["data"].get("sha256"),
            "block_index": h["block_index"],
        }
        for h in chain.get_batch_history(batch_id)
        if h["transaction"].get("event_type") == "DOCUMENT"
    ]
    if not recorded:
        raise HTTPException(
            status_code=404,
            detail="No document recorded on-chain for this batch.",
        )
    # Prefer a record with the same filename; otherwise use the latest document.
    rec = next((r for r in recorded if r["filename"] == file.filename), recorded[-1])
    expected = rec["sha256"]
    status = "MATCH" if actual == expected else "MODIFIED"
    return {
        "batch_id": batch_id,
        "filename": file.filename,
        "status": status,
        "message": (
            "Document is authentic — hash matches the blockchain record."
            if status == "MATCH"
            else "Document has been MODIFIED — hash does not match the blockchain!"
        ),
        "expected": expected,
        "actual": actual,
        "block_index": rec["block_index"],
    }


@app.get("/batches")
def list_batches():
    """Directory of every registered batch (off-chain records + event counts)."""
    return {"batches": get_db().list_batches()}


@app.get("/activity")
def activity(limit: int = 25):
    """Most recent supply-chain events, newest first."""
    return {"events": get_db().recent_events(limit)}


@app.get("/analytics")
def analytics():
    """Aggregate view for the operations command centre."""
    chain, db = get_chain(), get_db()
    batches = db.list_batches()
    crop_mix: dict[str, int] = {}
    status_mix: dict[str, int] = {}
    farmer_mix: dict[str, int] = {}
    total_kg = 0.0
    for b in batches:
        crop_mix[b["crop"]] = crop_mix.get(b["crop"], 0) + 1
        status_mix[b.get("status") or "UNKNOWN"] = status_mix.get(b.get("status") or "UNKNOWN", 0) + 1
        farmer_mix[b["farmer"]] = farmer_mix.get(b["farmer"], 0) + 1
        total_kg += float(b.get("quantity_kg") or 0)
    sensors = db.recent_sensor_readings(400)
    return {
        "total_batches": len(batches),
        "total_kg": round(total_kg, 1),
        "total_blocks": len(chain.chain),
        "chain_valid": chain.is_chain_valid(),
        "crop_mix": crop_mix,
        "status_mix": status_mix,
        "farmer_mix": farmer_mix,
        "event_mix": db.event_counts_by_type(),
        "recent_events": db.recent_events(18),
        "recent_sensors": sensors[:80],
        "temperature_alerts": db.stats()["temperature_alerts"],
        "quality_failures": db.stats()["quality_failures"],
        "documents": db.list_all_documents(),
    }


@app.get("/stats", response_model=StatsResponse)
def stats():
    chain, db = get_chain(), get_db()
    base = db.stats()
    chain_valid = chain.is_chain_valid()
    batches = db.list_batches()
    total = base["total_batches"]
    high_risk = base["temperature_alerts"] + base["quality_failures"]
    flagged = high_risk
    return StatsResponse(
        total_batches=total,
        verified=total if chain_valid else 0,
        flagged=flagged,
        high_risk=high_risk,
        quality_failures=base["quality_failures"],
        temperature_alerts=base["temperature_alerts"],
        total_blocks=len(chain.chain),
        chain_valid=chain_valid,
    )


# --- Demo controls ---------------------------------------------------------
@app.post("/debug/tamper")
def tamper():
    """Mutate a fixed on-chain transaction value WITHOUT re-mining, so the
    next /verify call detects the tampering. The 'money shot' for judges."""
    chain = get_chain()
    for block in chain.chain:
        for tx in block.transactions:
            data = tx.get("data", {})
            if TAMPER_FIELD in data:
                old = data[TAMPER_FIELD]
                data[TAMPER_FIELD] = TAMPER_BAD_VALUE
                return {
                    "message": "Transaction silently modified (not re-mined).",
                    "batch_id": tx.get("batch_id"),
                    "block_index": block.index,
                    "field": TAMPER_FIELD,
                    "old_value": old,
                    "new_value": TAMPER_BAD_VALUE,
                    "chain_valid": chain.is_chain_valid(),
                }
    raise HTTPException(status_code=400, detail="No tamperable transaction found. Seed data first.")


@app.post("/debug/reset")
def reset():
    reset_all()
    return {"message": "Ledger + database reset to genesis.", "blocks": 1}
