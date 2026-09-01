"""End-to-end API tests via FastAPI's TestClient.

Every test runs against an isolated temp ledger (see conftest.py) so the real
seeded chain.json / agrichain.db are never modified.
"""
from __future__ import annotations


def _register(client, crop="Rice", location="Konaseema", quantity_kg=2500):
    resp = client.post(
        "/register",
        json={
            "crop": crop,
            "farmer": "FARMER-001",
            "location": location,
            "quantity_kg": quantity_kg,
            "quality_grade": "A",
            "variety": "BPT-5204",
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_health_reports_running_and_valid(api_client):
    r = api_client.get("/")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "running"
    assert body["chain_valid"] is True
    assert body["blocks"] == 1  # fresh genesis on the isolated ledger


def test_register_creates_batch_and_advances_chain(api_client):
    before = api_client.get("/").json()["blocks"]
    body = _register(api_client)
    assert body["batch_id"].startswith("RICE-KONASE-")
    assert body["block_index"] == before  # new block appended at index == old length
    after = api_client.get("/").json()["blocks"]
    assert after == before + 1


def test_event_records_and_advances_status(api_client):
    batch_id = _register(api_client)["batch_id"]
    r = api_client.post(
        "/event",
        json={
            "batch_id": batch_id,
            "event_type": "QUALITY_CHECK",
            "actor_id": "INSPECTOR-001",
            "location": "Amalapuram",
            "data": {"grade": "A", "quality_status": "PASSED"},
        },
    )
    assert r.status_code == 200, r.text
    batch = api_client.get(f"/batch/{batch_id}").json()
    assert batch["batch"]["status"] == "QUALITY_CHECK"
    types = {h["transaction"]["event_type"] for h in batch["history"]}
    assert types == {"HARVEST", "QUALITY_CHECK"}


def test_batch_history_and_404(api_client):
    batch_id = _register(api_client)["batch_id"]
    ok = api_client.get(f"/batch/{batch_id}")
    assert ok.status_code == 200
    assert ok.json()["chain_valid"] is True
    missing = api_client.get("/batch/DOES-NOT-EXIST")
    assert missing.status_code == 404


def test_tamper_then_reset_round_trip(api_client):
    _register(api_client)  # gives a tamperable quantity_kg on-chain
    assert api_client.get("/verify").json()["valid"] is True

    tampered = api_client.post("/debug/tamper").json()
    assert tampered["field"] == "quantity_kg"
    assert tampered["new_value"] == 9999999
    assert api_client.get("/verify").json()["valid"] is False  # detected!

    api_client.post("/debug/reset")
    verify = api_client.get("/verify").json()
    assert verify["valid"] is True
    assert verify["blocks"] == 1


def test_tamper_without_data_returns_400(api_client):
    # No batches registered -> nothing tamperable.
    r = api_client.post("/debug/tamper")
    assert r.status_code == 400


def test_stats_shape(api_client):
    _register(api_client)
    s = api_client.get("/stats").json()
    assert s["total_batches"] == 1
    assert s["chain_valid"] is True
    assert s["total_blocks"] >= 2


def test_risk_scoring(api_client):
    r = api_client.post(
        "/risk",
        json={"temperature": 40, "humidity": 85, "delay_hours": 30, "quality_score": 50},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["level"] == "HIGH"          # all four rules trip
    assert body["score"] == 100
    assert set(body["factors"]) == {"temperature", "humidity", "delay_hours", "quality_score"}


def test_sensor_stream_records_readings(api_client):
    batch_id = _register(api_client)["batch_id"]
    r = api_client.post(
        "/sensor/stream",
        params={"batch_id": batch_id, "n": 12, "inject_anomaly": True},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["anomalies"] >= 1           # the injected ~89C spike is flagged
    readings = api_client.get(f"/batch/{batch_id}").json()["sensor_readings"]
    assert len(readings) == 12


def test_document_upload_and_verify(api_client):
    batch_id = _register(api_client)["batch_id"]
    original = b"ORGANIC CERTIFICATE\nbatch authentic\n"

    up = api_client.post(
        "/document",
        data={"batch_id": batch_id, "doc_type": "organic_certificate"},
        files={"file": ("cert.txt", original)},
    )
    assert up.status_code == 200, up.text
    sha = up.json()["sha256"]
    assert len(sha) == 64

    listing = api_client.get(f"/document/{batch_id}").json()["documents"]
    assert len(listing) == 1
    assert listing[0]["sha256"] == sha

    # Unchanged file -> MATCH
    match = api_client.post(
        "/document/verify",
        data={"batch_id": batch_id},
        files={"file": ("cert.txt", original)},
    ).json()
    assert match["status"] == "MATCH"

    # Edited file -> MODIFIED
    modified = api_client.post(
        "/document/verify",
        data={"batch_id": batch_id},
        files={"file": ("cert.txt", original + b"tampered!")},
    ).json()
    assert modified["status"] == "MODIFIED"
    assert modified["expected"] != modified["actual"]


def test_document_verify_without_record_404(api_client):
    batch_id = _register(api_client)["batch_id"]
    r = api_client.post(
        "/document/verify",
        data={"batch_id": batch_id},
        files={"file": ("x.txt", b"nothing recorded")},
    )
    assert r.status_code == 404


def test_batches_directory_and_analytics(api_client):
    _register(api_client, crop="Rice", location="Konaseema", quantity_kg=2500)
    _register(api_client, crop="Maize", location="Kothapeta", quantity_kg=3000)

    listing = api_client.get("/batches").json()
    assert len(listing["batches"]) == 2
    ids = {b["batch_id"] for b in listing["batches"]}
    assert any(i.startswith("RICE-") for i in ids)
    assert all("events" in b and "has_alert" in b for b in listing["batches"])

    activity = api_client.get("/activity", params={"limit": 5}).json()
    assert len(activity["events"]) >= 2
    assert activity["events"][0]["event_type"] == "HARVEST"

    analytics = api_client.get("/analytics").json()
    assert analytics["total_batches"] == 2
    assert analytics["total_kg"] == 5500
    assert analytics["crop_mix"]["Rice"] == 1
    assert analytics["crop_mix"]["Maize"] == 1
    assert analytics["chain_valid"] is True
    assert "HARVEST" in analytics["event_mix"]


def test_qr_endpoint_returns_png(api_client):
    batch_id = _register(api_client)["batch_id"]
    r = api_client.get(f"/qr/{batch_id}")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"
    assert r.content[:8] == b"\x89PNG\r\n\x1a\n"  # PNG magic bytes
