"""Generate a reproducible synthetic agricultural supply-chain dataset.

~1000 batches with realistic distributions plus a deliberate slice of
high-risk rows so the risk classifier has balanced labels to learn from.
Run:  python -m data.generate_dataset
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from config import DATA_CSV, RANDOM_SEED, ensure_dirs

CROPS = ["Rice", "Maize", "Wheat", "Chilli"]
LOCATIONS = ["Konaseema", "Amalapuram", "Kothapeta", "Razole", "Rajahmundry"]
GRADES = ["A", "B", "C"]


def generate(n: int = 1000) -> pd.DataFrame:
    rng = np.random.default_rng(RANDOM_SEED)
    df = pd.DataFrame(
        {
            "batch_id": [f"RICE-{i:05d}" for i in range(n)],
            "crop": rng.choice(CROPS, n),
            "farmer": [f"F{rng.integers(1, 300):03d}" for _ in range(n)],
            "location": rng.choice(LOCATIONS, n),
            "quantity_kg": rng.integers(500, 5000, n),
            "temperature": np.round(rng.normal(27, 5, n), 2),
            "humidity": np.round(rng.normal(65, 10, n), 2),
            "quality_grade": rng.choice(GRADES, n, p=[0.6, 0.3, 0.1]),
            "transport_distance_km": rng.integers(10, 300, n),
            "delay_hours": np.round(np.abs(rng.normal(12, 10, n)), 1),
            "quality_score": np.round(np.clip(rng.normal(80, 15, n), 0, 100), 1),
        }
    )
    # Inject a slice of clearly high-risk rows for label balance
    idx = rng.choice(n, size=n // 5, replace=False)
    df.loc[idx, "temperature"] = np.round(rng.uniform(36, 45, len(idx)), 2)
    df.loc[idx, "delay_hours"] = np.round(rng.uniform(25, 60, len(idx)), 1)
    df.loc[idx, "quality_score"] = np.round(rng.uniform(30, 68, len(idx)), 1)
    return df


def main() -> None:
    ensure_dirs()
    df = generate()
    df.to_csv(DATA_CSV, index=False)
    print(f"Wrote {len(df)} rows -> {DATA_CSV}")
    print(df.head())


if __name__ == "__main__":
    main()
