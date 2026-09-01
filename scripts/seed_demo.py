"""Headless demo seeder — populates the running API with realistic data.

Registers a set of batches, runs the full event lifecycle for each, streams
IoT sensor readings (one batch gets an injected anomaly), generates QR codes,
and verifies the chain. Prints a summary + a "tamper-ready" batch id.

Usage:  python -m scripts.seed_demo [--n-batches N] [--base-url URL]
Requires the API to be running (uvicorn backend.main:app --port 8000).
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests  # noqa: E402

from config import API_BASE  # noqa: E402

BATCHES = [
    {"crop": "Rice", "farmer": "FARMER-001", "location": "Konaseema", "quantity_kg": 2500, "quality_grade": "A", "variety": "BPT-5204"},
    {"crop": "Rice", "farmer": "FARMER-002", "location": "Amalapuram", "quantity_kg": 1800, "quality_grade": "B", "variety": "Sona"},
    {"crop": "Maize", "farmer": "FARMER-003", "location": "Kothapeta", "quantity_kg": 3000, "quality_grade": "A", "variety": "DHM-117"},
    {"crop": "Wheat", "farmer": "FARMER-004", "location": "Razole", "quantity_kg": 2200, "quality_grade": "C", "variety": "HD-2967"},
    {"crop": "Chilli", "farmer": "FARMER-005", "location": "Rajahmundry", "quantity_kg": 1200, "quality_grade": "A", "variety": "Teja"},
]

LIFECYCLE = [
    ("QUALITY_CHECK", "INSPECTOR-001", "Amalapuram Collection Center",
     {"moisture_percent": 12.4, "foreign_matter_percent": 0.8, "grade": "A", "quality_status": "PASSED"}),
    ("TRANSPORT", "TRANSPORT-001", "Konaseema",
     {"vehicle_id": "AP05AB1234", "temperature": 26.1, "humidity": 65, "distance_km": 82}),
    ("WAREHOUSE_ENTRY", "WAREHOUSE-001", "Rajahmundry Warehouse",
     {"storage_temperature": 24.5, "humidity": 58, "quantity_kg": 2450}),
    ("PROCESSING", "MILL-001", "Rice Processing Unit",
     {"process": "Milling", "input_kg": 2450, "output_kg": 1750, "quality_grade": "Premium"}),
    ("DISTRIBUTION", "DIST-001", "Vijayawada Hub",
     {"destination": "Retail Network", "quantity_kg": 1750}),
    ("RETAIL", "RETAILER-001", "Retail Store",
     {"selling_price": 85, "unit": "kg", "availability": "AVAILABLE"}),
]


def wait_for_api(base: str, tries: int = 30) -> bool:
    for _ in range(tries):
        try:
            if requests.get(f"{base}/", timeout=2).status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-batches", type=int, default=len(BATCHES))
    ap.add_argument("--base-url", default=API_BASE)
    args = ap.parse_args()
    base = args.base_url

    if not wait_for_api(base):
        print(f"ERROR: API not reachable at {base}. Start uvicorn first.")
        return 1

    print("Resetting ledger…")
    requests.post(f"{base}/debug/reset", timeout=10)

    batch_ids: list[str] = []
    for spec in BATCHES[: args.n_batches]:
        r = requests.post(f"{base}/register", json=spec, timeout=10)
        bid = r.json()["batch_id"]
        batch_ids.append(bid)
        print(f"  registered {bid} ({spec['crop']}, {spec['quantity_kg']}kg)")
        for et, actor, loc, data in LIFECYCLE:
            requests.post(f"{base}/event", json={
                "batch_id": bid, "event_type": et, "actor_id": actor,
                "location": loc, "data": data,
            }, timeout=10)
        # QR
        requests.get(f"{base}/qr/{bid}", timeout=10)

    # Stream sensors; give the 3rd batch a temperature anomaly
    for i, bid in enumerate(batch_ids):
        inject = (i == 2)
        res = requests.post(f"{base}/sensor/stream",
                            params={"batch_id": bid, "n": 15, "inject_anomaly": inject},
                            timeout=30).json()
        print(f"  sensors for {bid}: {res.get('anomalies',0)} anomalies"
              + ("  <-- injected" if inject else ""))

    v = requests.get(f"{base}/verify", timeout=10).json()
    s = requests.get(f"{base}/stats", timeout=10).json()
    print("\n" + "=" * 56)
    print(f"Seeded {len(batch_ids)} batches · {s['total_blocks']} blocks · "
          f"chain valid: {v['valid']}")
    print(f"QR codes written to: qr/output/")
    print(f"Tamper-ready batch (has quantity_kg): {batch_ids[0]}")
    print("Try:  curl -X POST %s/debug/tamper   then   curl %s/verify" % (base, base))
    print("=" * 56)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
