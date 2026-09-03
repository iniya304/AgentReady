from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from ml.model_features import build_features


# ============================================================
# MODEL PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "models" / "agentready_recovery_model.joblib"


# ============================================================
# LOAD MODEL
# ============================================================

if not MODEL_PATH.exists():
    raise RuntimeError(
        f"AgentReady recovery model not found at: {MODEL_PATH}"
    )

model = joblib.load(MODEL_PATH)


# ============================================================
# MODEL METADATA
# ============================================================

EXPECTED_FEATURE_COUNT = model.n_features_in_

EXPECTED_FEATURES = list(
    model.feature_names_in_
)


# ============================================================
# PREDICTION
# ============================================================

def predict_recovery(
    payment_context: dict[str, Any],
) -> dict[str, Any]:
    """
    Predict the probability that a failed payment will be recovered
    under the supplied intervention.

    The supplied payment context must contain the same raw inputs
    used during model training.
    """

    features = build_features(payment_context)

    # --------------------------------------------------------
    # Safety check: feature count
    # --------------------------------------------------------

    if features.shape[1] != EXPECTED_FEATURE_COUNT:
        raise ValueError(
            f"Feature count mismatch. "
            f"Model expects {EXPECTED_FEATURE_COUNT}, "
            f"but feature builder produced {features.shape[1]}."
        )

    # --------------------------------------------------------
    # Safety check: feature names and order
    # --------------------------------------------------------

    actual_features = list(features.columns)

    if actual_features != EXPECTED_FEATURES:
        raise ValueError(
            "Feature names/order do not match the trained model."
        )

    # --------------------------------------------------------
    # Prediction
    # --------------------------------------------------------

    probability = float(
        model.predict_proba(features)[0][1]
    )

    prediction = int(
        probability >= 0.5
    )

    return {
        "recovery_probability": round(probability, 4),
        "recovery_probability_percent": round(
            probability * 100,
            2,
        ),
        "predicted_recovery": prediction,
        "model": "Logistic Regression",
        "model_c": 0.03,
        "feature_count": EXPECTED_FEATURE_COUNT,
        "intervention": payment_context.get(
            "intervention"
        ),
    }

