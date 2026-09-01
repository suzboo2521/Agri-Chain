"""Reproducibly (re)train both AgriChain models.

Produces, under ``ai/models/``:
  * ``risk_model.joblib``        — RandomForest supply-chain risk classifier
  * ``feature_importance.png``   — explainable-AI feature-importance chart
  * ``anomaly_model.joblib``     — IsolationForest cold-chain anomaly detector

Run:  python -m scripts.train_models
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np  # noqa: E402

from config import (  # noqa: E402
    ANOMALY_MODEL_PATH,
    DATA_CSV,
    FEATURE_IMPORTANCE_PNG,
    RANDOM_SEED,
    RISK_MODEL_PATH,
    ensure_dirs,
)


def _ensure_dataset() -> None:
    if not DATA_CSV.exists():
        print(f"[data] {DATA_CSV.name} missing — generating synthetic dataset…")
        from data.generate_dataset import main as gen

        gen()


def train_risk() -> None:
    from ai.risk import train_risk_model

    print("[risk] training RandomForest risk classifier…")
    model = train_risk_model(DATA_CSV)
    from ai.risk import feature_importance

    imp = feature_importance(model)
    top = sorted(imp.items(), key=lambda kv: kv[1], reverse=True)[:3]
    print(f"[risk] saved -> {RISK_MODEL_PATH}")
    print(f"[risk] chart -> {FEATURE_IMPORTANCE_PNG}")
    print("[risk] top factors:", ", ".join(f"{k}={v:.2f}" for k, v in top))


def train_anomaly() -> None:
    from ai.anomaly import train_anomaly_model
    from iot.sensor_sim import generate_sensor_data

    print("[anomaly] generating normal cold-chain readings…")
    rng = np.random.default_rng(RANDOM_SEED)
    readings = generate_sensor_data("TRAIN", 500, inject_anomaly=False, rng=rng)
    train_anomaly_model(readings, ANOMALY_MODEL_PATH)
    print(f"[anomaly] trained on {len(readings)} readings -> {ANOMALY_MODEL_PATH}")


def main() -> int:
    ensure_dirs()
    _ensure_dataset()
    train_risk()
    train_anomaly()
    print("\n✅ All models trained.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
