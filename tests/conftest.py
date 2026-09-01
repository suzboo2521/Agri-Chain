"""Shared pytest fixtures.

CRITICAL ISOLATION: the real ``chain.json`` (36 seeded blocks) and
``agrichain.db`` must never be touched by the test suite. The ``api_client``
fixture repoints the ledger singletons at per-test temp files and uses the
faster ``TEST_DIFFICULTY`` for mining, then restores everything afterwards.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config  # noqa: E402
import backend.ledger as ledger  # noqa: E402


@pytest.fixture
def temp_ledger(tmp_path, monkeypatch):
    """Repoint the process-wide ledger at isolated temp paths + fast difficulty."""
    monkeypatch.setattr(ledger, "CHAIN_PATH", tmp_path / "chain.json")
    monkeypatch.setattr(ledger, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(ledger, "DIFFICULTY", config.TEST_DIFFICULTY)
    monkeypatch.setattr(ledger, "_chain", None, raising=False)
    monkeypatch.setattr(ledger, "_db", None, raising=False)
    yield tmp_path
    # Drop temp singletons so nothing leaks into later imports/tests.
    ledger._chain = None
    ledger._db = None


@pytest.fixture
def api_client(temp_ledger, monkeypatch):
    """FastAPI TestClient wired to the isolated ledger."""
    from fastapi.testclient import TestClient

    import backend.main as main

    # Keep uploaded test files out of the real data/uploads dir.
    monkeypatch.setattr(main, "UPLOADS_DIR", temp_ledger / "uploads")
    with TestClient(main.app) as client:
        yield client
