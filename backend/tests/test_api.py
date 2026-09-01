def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_login_and_rbac(client, admin_headers):
    r = client.get("/api/auth/me", headers=admin_headers)
    assert r.json()["role"] == "ADMIN"
    farmer = client.post("/api/auth/login", json={"email": "farmer@agrichain.local", "password": "Demo@12345"})
    headers = {"Authorization": f"Bearer {farmer.json()['access_token']}"}
    denied = client.get("/api/users", headers=headers)
    assert denied.status_code == 403


def test_batch_and_verify(client, admin_headers):
    r = client.get("/api/batches/RICE-KONASEEMA-2026-0001", headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["crop"] == "Rice"
    v = client.get("/api/verify/RICE-KONASEEMA-2026-0001")
    assert v.status_code == 200
    assert v.json()["batch_id"] == "RICE-KONASEEMA-2026-0001"
    unknown = client.get("/api/verify/NO-SUCH-BATCH")
    assert unknown.status_code in (200, 404)


def test_event_anchor(client, admin_headers):
    r = client.post(
        "/api/events",
        headers=admin_headers,
        json={
            "batch_id": "RICE-KONASEEMA-2026-0001",
            "event_type": "WAREHOUSE_ENTRY",
            "location": "Demo Warehouse",
            "metadata": {"note": "test"},
        },
    )
    assert r.status_code == 200
    assert r.json()["verification_status"] == "ANCHORED"
    assert "transaction_id" in r.json()


def test_document_hash(client, admin_headers):
    files = {"file": ("cert.txt", b"organic certificate body", "text/plain")}
    r = client.post(
        "/api/documents/hash",
        headers=admin_headers,
        data={"batch_id": "RICE-KONASEEMA-2026-0001", "doc_type": "QUALITY_CERTIFICATE"},
        files=files,
    )
    assert r.status_code == 200
    digest = r.json()["sha256"]
    ok = client.post(
        "/api/documents/verify",
        headers=admin_headers,
        data={"batch_id": "RICE-KONASEEMA-2026-0001"},
        files={"file": ("cert.txt", b"organic certificate body", "text/plain")},
    )
    assert ok.json()["status"] == "DOCUMENT_VERIFIED"
    bad = client.post(
        "/api/documents/verify",
        headers=admin_headers,
        data={"batch_id": "RICE-KONASEEMA-2026-0001"},
        files={"file": ("cert.txt", b"tampered", "text/plain")},
    )
    assert bad.json()["status"] == "DOCUMENT_MODIFIED"
    assert len(digest) == 64


def test_risk_and_qr(client, admin_headers):
    r = client.get("/api/risk/MAIZE-ELURU-2026-0004", headers=admin_headers)
    assert r.status_code == 200
    qr = client.get("/api/batches/RICE-KONASEEMA-2026-0001/qr")
    assert qr.status_code == 200
    assert qr.headers["content-type"].startswith("image/")


def test_tamper_demo(client, admin_headers):
    before = client.get("/api/blockchain/verify", headers=admin_headers)
    assert before.json()["valid"] is True
    tamper = client.post("/api/debug/tamper", headers=admin_headers)
    assert tamper.status_code == 200
    assert tamper.json()["valid"] is False
    restore = client.post("/api/debug/restore", headers=admin_headers)
    assert restore.json()["valid"] is True
