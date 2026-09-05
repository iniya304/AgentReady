from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_PATH = BASE_DIR / "data" / "recovery_training_data_v2.csv"
MODEL_DIR = BASE_DIR / "ml" / "models"

MODEL_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = MODEL_DIR / "agentready_recovery_model.joblib"


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("SAVING FINAL AGENTREADY RECOVERY MODEL")
print("=" * 70)

df = pd.read_csv(DATA_PATH)

df = df.drop(columns=["recovered_amount"])

TARGET = "recovered"

X_raw = df.drop(columns=[TARGET])
y = df[TARGET]


# ============================================================
# FEATURE ENGINEERING
# ============================================================

def build_features(df_input: pd.DataFrame) -> pd.DataFrame:

    df = df_input.copy()

    # Amount
    df["log_amount"] = np.log1p(df["amount"])

    df["high_value_flag"] = (
        df["amount"] >= 10000
    ).astype(int)

    df["amount_band"] = pd.cut(
        df["amount"],
        bins=[-np.inf, 1000, 5000, 10000, np.inf],
        labels=[
            "low",
            "medium",
            "high",
            "very_high",
        ],
    ).astype(str)

    # Customer history
    df["historical_failure_rate"] = (
        df["historical_failed_payments"]
        / df["historical_payments"].replace(0, 1)
    )

    df["customer_history_strength"] = np.log1p(
        df["historical_payments"]
    )

    df["customer_recovery_momentum"] = (
        df["historical_recovered_payments"]
        + df["previous_recovery_success"]
    )

    # Attempts
    df["attempt_pressure"] = (
        df["previous_attempts"]
        + df["previous_recovery_attempts"]
    )

    df["recovery_attempt_pressure"] = (
        df["previous_recovery_attempts"] + 1
    )

    df["no_previous_attempt"] = (
        df["previous_attempts"] == 0
    ).astype(int)

    df["multiple_attempt_flag"] = (
        df["previous_attempts"] >= 2
    ).astype(int)

    # Recency
    df["recent_failure_flag"] = (
        df["hours_since_failure"] <= 6
    ).astype(int)

    df["stale_failure_flag"] = (
        df["hours_since_failure"] >= 48
    ).astype(int)

    df["recency_risk"] = np.log1p(
        df["days_since_last_success"]
    )

    # Time
    df["business_hours_flag"] = (
        df["payment_hour"].between(9, 18)
    ).astype(int)

    df["late_night_flag"] = (
        (df["payment_hour"] < 6)
        | (df["payment_hour"] >= 23)
    ).astype(int)

    # Interactions
    df["failure_payment_method"] = (
        df["failure_reason"].astype(str)
        + "_"
        + df["payment_method"].astype(str)
    )

    df["failure_intervention"] = (
        df["failure_reason"].astype(str)
        + "_"
        + df["intervention"].astype(str)
    )

    df["method_intervention"] = (
        df["payment_method"].astype(str)
        + "_"
        + df["intervention"].astype(str)
    )

    df["customer_attempt_interaction"] = (
        df["customer_recovery_history"].astype(str)
        + "_"
        + df["previous_attempts"].astype(str)
    )

    df["history_attempt_interaction"] = (
        pd.cut(
            df["historical_recovery_rate"],
            bins=[-np.inf, 0.3, 0.6, np.inf],
            labels=["low", "medium", "high"],
        ).astype(str)
        + "_"
        + df["previous_attempts"].astype(str)
    )

    df["intervention_strength"] = (
        df["intervention"]
        .map(
            {
                "retry_now": 1,
                "retry_later": 2,
                "request_alternative_payment": 3,
                "request_card_update": 3,
            }
        )
        .fillna(0)
    )

    return df


X = build_features(X_raw)

print(f"Training rows: {len(X)}")
print(f"Training features: {X.shape[1]}")


# ============================================================
# PREPROCESSING
# ============================================================

categorical_features = [
    col
    for col in X.columns
    if str(X[col].dtype)
    in {"object", "string", "str", "category"}
]

numerical_features = [
    col
    for col in X.columns
    if col not in categorical_features
]


preprocessor = ColumnTransformer(
    transformers=[
        (
            "num",
            StandardScaler(),
            numerical_features,
        ),
        (
            "cat",
            OneHotEncoder(
                handle_unknown="ignore",
                sparse_output=False,
            ),
            categorical_features,
        ),
    ]
)


# ============================================================
# FINAL MODEL
# ============================================================

model = LogisticRegression(
    C=0.03,
    max_iter=3000,
    random_state=42,
)


pipeline = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        ("model", model),
    ]
)


# ============================================================
# TRAIN
# ============================================================

print("\nTraining final model...")

pipeline.fit(X, y)


# ============================================================
# SAVE
# ============================================================

joblib.dump(
    pipeline,
    MODEL_PATH,
)


print("\n" + "=" * 70)
print("MODEL SAVED SUCCESSFULLY")
print("=" * 70)

print(f"\nModel path:")
print(MODEL_PATH)

print("\nModel configuration:")
print("Algorithm : Logistic Regression")            
print("C         : 0.03")
print(f"Features  : {X.shape[1]}")

print("\nThe trained model is ready for backend integration.")



