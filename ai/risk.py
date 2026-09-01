"""Supply-chain risk scoring for AgriChain.

Two complementary views:

* ``calculate_risk`` — a transparent, rule-based 0-100 score (great for
  explaining *why* a batch is risky to judges / regulators).
* ``train_risk_model`` / ``predict_risk`` — a RandomForest trained on the
  synthetic dataset, plus ``feature_importance`` (explainable AI) so we can
  show which factors drive risk.
"""
from __future__ import annotations

from typing import Any, Optional

FEATURES = [
    "quantity_kg",
    "temperature",
    "humidity",
    "transport_distance_km",
    "delay_hours",
    "quality_score",
]

RANDOM_STATE = 42


# --- Rule-based score ------------------------------------------------------
def calculate_risk(
    temperature: float, humidity: float, delay_hours: float, quality_score: float
) -> dict[str, Any]:
    factors: dict[str, int] = {}
    factors["temperature"] = 30 if temperature > 35 else 0
    factors["humidity"] = 20 if humidity > 80 else 0
    factors["delay_hours"] = 25 if delay_hours > 24 else 0
    factors["quality_score"] = 25 if quality_score < 70 else 0
    score = min(sum(factors.values()), 100)
    if score > 60:
        level = "HIGH"
    elif score >= 30:
        level = "MEDIUM"
    else:
        level = "LOW"
    return {"score": score, "level": level, "factors": factors}


# --- ML model --------------------------------------------------------------
def _risk_label(row) -> int:
    r = calculate_risk(
        row["temperature"], row["humidity"], row["delay_hours"], row["quality_score"]
    )
    return 1 if r["level"] in ("HIGH", "MEDIUM") else 0


def train_risk_model(csv_path, model_path=None, png_path=None):
    import joblib
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier

    from config import FEATURE_IMPORTANCE_PNG, RISK_MODEL_PATH

    model_path = model_path or RISK_MODEL_PATH
    png_path = png_path or FEATURE_IMPORTANCE_PNG

    df = pd.read_csv(csv_path)
    df["risk"] = df.apply(_risk_label, axis=1)
    X = df[FEATURES]
    y = df["risk"]
    model = RandomForestClassifier(n_estimators=200, random_state=RANDOM_STATE)
    model.fit(X, y)
    joblib.dump(model, model_path)
    try:
        plot_feature_importance(model, png_path)
    except Exception as exc:  # plotting must never break training
        print(f"[risk] feature-importance plot skipped: {exc}")
    return model


def load_model(model_path=None):
    import joblib

    from config import RISK_MODEL_PATH

    model_path = model_path or RISK_MODEL_PATH
    try:
        return joblib.load(model_path)
    except Exception:
        return None


def predict_risk(model, features: dict[str, float]) -> Optional[str]:
    if model is None:
        return None
    import pandas as pd

    row = pd.DataFrame([[features.get(f, 0) for f in FEATURES]], columns=FEATURES)
    pred = int(model.predict(row)[0])
    return "AT_RISK" if pred == 1 else "OK"


def feature_importance(model) -> dict[str, float]:
    return {f: float(v) for f, v in zip(FEATURES, model.feature_importances_)}


def plot_feature_importance(model, png_path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import pandas as pd

    imp = pd.Series(model.feature_importances_, index=FEATURES).sort_values()
    fig, ax = plt.subplots(figsize=(7, 4))
    imp.plot(kind="barh", ax=ax, color="#2e7d32")
    ax.set_title("Supply-Chain Risk — Feature Importance")
    ax.set_xlabel("Importance")
    fig.tight_layout()
    fig.savefig(png_path, dpi=120)
    plt.close(fig)
