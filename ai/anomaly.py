"""AI anomaly detection over IoT sensor readings (IsolationForest).

The blockchain answers "*was the data changed?*"; this module answers "*does the
data look suspicious?*". An IsolationForest over (temperature, humidity) flags
readings that deviate from the learned normal cold-chain envelope.
"""
from __future__ import annotations

from typing import Any, Sequence

import numpy as np
from sklearn.ensemble import IsolationForest

RANDOM_STATE = 42


def _to_matrix(readings: Sequence[dict[str, Any]]) -> np.ndarray:
    return np.array(
        [[float(r["temperature"]), float(r["humidity"])] for r in readings],
        dtype=float,
    )


def fit_detect(
    readings: Sequence[dict[str, Any]], contamination: float | str = "auto"
) -> list[bool]:
    """Fit on the given readings and return a per-reading anomaly flag.

    Deterministic for a fixed input (``random_state`` pinned). Returns ``True``
    where a reading is judged anomalous. Falls back to a simple rule when there
    are too few points for the model to be meaningful.
    """
    if len(readings) == 0:
        return []
    X = _to_matrix(readings)
    if len(readings) < 6:
        # Not enough data to learn a distribution — use a physical threshold.
        return [bool(t > 35 or t < 15) for t in X[:, 0]]
    model = IsolationForest(
        n_estimators=100, contamination=contamination, random_state=RANDOM_STATE
    )
    preds = model.fit_predict(X)  # -1 = anomaly, 1 = normal
    return [bool(p == -1) for p in preds]


def train_anomaly_model(readings: Sequence[dict[str, Any]], path) -> IsolationForest:
    import joblib

    X = _to_matrix(readings)
    model = IsolationForest(
        n_estimators=100, contamination="auto", random_state=RANDOM_STATE
    )
    model.fit(X)
    joblib.dump(model, path)
    return model


def detect_with_model(model: IsolationForest, readings: Sequence[dict[str, Any]]) -> list[bool]:
    if not readings:
        return []
    preds = model.predict(_to_matrix(readings))
    return [bool(p == -1) for p in preds]
