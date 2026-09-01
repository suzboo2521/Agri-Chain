"""Simulated IoT cold-chain sensors.

Produces temperature / humidity / GPS readings that look like real transport
telemetry. Readings can be turned into blockchain events, and the AI anomaly
detector flags injected spikes (e.g. a broken reefer unit reading ~89 C).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterator, Optional

import numpy as np

# Konaseema / Godavari delta region (Andhra Pradesh)
_BASE_LAT = 16.58
_BASE_LON = 82.00


def generate_sensor_data(
    batch_id: str,
    n: int = 1,
    inject_anomaly: bool = False,
    rng: Optional[np.random.Generator] = None,
) -> list[dict[str, Any]]:
    """Generate ``n`` sensor readings for a batch.

    Normal readings: temperature ~N(25, 1.5) clamped 20-30, humidity
    ~N(65, 5) clamped 50-80. When ``inject_anomaly`` is set, the final reading
    is forced to a ~89 C spike so the anomaly detector has something to catch.
    """
    if rng is None:
        rng = np.random.default_rng()
    readings: list[dict[str, Any]] = []
    for i in range(n):
        temp = float(np.clip(rng.normal(25, 1.5), 20, 30))
        humidity = float(np.clip(rng.normal(65, 5), 50, 80))
        if inject_anomaly and i == n - 1:
            temp = float(round(rng.uniform(85, 92), 2))
        readings.append(
            {
                "batch_id": batch_id,
                "temperature": round(temp, 2),
                "humidity": round(humidity, 2),
                "gps_lat": round(_BASE_LAT + float(rng.normal(0, 0.05)), 4),
                "gps_lon": round(_BASE_LON + float(rng.normal(0, 0.05)), 4),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    return readings


def stream_sensor_data(
    batch_id: str, count: int, rng: Optional[np.random.Generator] = None
) -> Iterator[dict[str, Any]]:
    if rng is None:
        rng = np.random.default_rng()
    for _ in range(count):
        yield generate_sensor_data(batch_id, 1, rng=rng)[0]


if __name__ == "__main__":  # pragma: no cover
    rng = np.random.default_rng(42)
    for r in generate_sensor_data("RICE-DEMO", 5, inject_anomaly=True, rng=rng):
        print(r)
