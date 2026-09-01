"""Thin HTTP client around the AgriChain FastAPI backend.

The Streamlit UI never touches the blockchain directly — it goes through these
functions so there is exactly one authoritative ledger (in the API process).
"""
from __future__ import annotations

from typing import Any

import requests

from config import API_BASE

TIMEOUT = 10


def _url(path: str) -> str:
    return f"{API_BASE}{path}"


def health() -> dict[str, Any]:
    return requests.get(_url("/"), timeout=TIMEOUT).json()


def register(payload: dict[str, Any]) -> requests.Response:
    return requests.post(_url("/register"), json=payload, timeout=TIMEOUT)


def add_event(payload: dict[str, Any]) -> requests.Response:
    return requests.post(_url("/event"), json=payload, timeout=TIMEOUT)


def get_chain() -> list[dict[str, Any]]:
    return requests.get(_url("/blockchain"), timeout=TIMEOUT).json()


def verify() -> dict[str, Any]:
    return requests.get(_url("/verify"), timeout=TIMEOUT).json()


def batch_history(batch_id: str) -> requests.Response:
    return requests.get(_url(f"/batch/{batch_id}"), timeout=TIMEOUT)


def stream_sensors(batch_id: str, n: int = 10, inject_anomaly: bool = False) -> dict[str, Any]:
    return requests.post(
        _url("/sensor/stream"),
        params={"batch_id": batch_id, "n": n, "inject_anomaly": inject_anomaly},
        timeout=30,
    ).json()


def anomalies(batch_id: str) -> dict[str, Any]:
    return requests.get(_url(f"/anomalies/{batch_id}"), timeout=TIMEOUT).json()


def risk(payload: dict[str, Any]) -> dict[str, Any]:
    return requests.post(_url("/risk"), json=payload, timeout=TIMEOUT).json()


def qr_url(batch_id: str) -> str:
    return _url(f"/qr/{batch_id}")


def stats() -> dict[str, Any]:
    return requests.get(_url("/stats"), timeout=TIMEOUT).json()


def list_batches() -> dict[str, Any]:
    return requests.get(_url("/batches"), timeout=TIMEOUT).json()


def activity(limit: int = 25) -> dict[str, Any]:
    return requests.get(_url("/activity"), params={"limit": limit}, timeout=TIMEOUT).json()


def analytics() -> dict[str, Any]:
    return requests.get(_url("/analytics"), timeout=TIMEOUT).json()


def qr_png(batch_id: str) -> bytes:
    return requests.get(_url(f"/qr/{batch_id}"), timeout=TIMEOUT).content


def upload_document(batch_id: str, doc_type: str, filename: str, content: bytes) -> dict[str, Any]:
    return requests.post(
        _url("/document"),
        data={"batch_id": batch_id, "doc_type": doc_type},
        files={"file": (filename, content)},
        timeout=30,
    ).json()


def list_documents(batch_id: str) -> dict[str, Any]:
    return requests.get(_url(f"/document/{batch_id}"), timeout=TIMEOUT).json()


def verify_document(batch_id: str, filename: str, content: bytes) -> requests.Response:
    return requests.post(
        _url("/document/verify"),
        data={"batch_id": batch_id},
        files={"file": (filename, content)},
        timeout=30,
    )


def tamper() -> dict[str, Any]:
    return requests.post(_url("/debug/tamper"), timeout=TIMEOUT).json()


def reset() -> dict[str, Any]:
    return requests.post(_url("/debug/reset"), timeout=TIMEOUT).json()
