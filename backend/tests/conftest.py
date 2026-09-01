import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///" + str(Path("/tmp/agrichain_test.db"))
os.environ["CHAIN_PATH"] = "/tmp/agrichain_test_chain.json"
os.environ["SECRET_KEY"] = "test-secret"

for p in ("/tmp/agrichain_test.db", "/tmp/agrichain_test_chain.json"):
    Path(p).unlink(missing_ok=True)

from app.core.config import settings  # noqa: E402

settings.database_url = os.environ["DATABASE_URL"]
settings.chain_path = os.environ["CHAIN_PATH"]
settings.secret_key = "test-secret"
settings.pow_difficulty = 1

from app.core.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def admin_headers(client: TestClient):
    r = client.post("/api/auth/login", json={"email": "admin@agrichain.local", "password": "Demo@12345"})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
