from pathlib import Path

import pandas as pd
import numpy as np

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
    brier_score_loss,
)
from sklearn.inspection import permutation_importance


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "recovery_training_data_v2.csv"
OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("AgentReady V2 MODEL DIAGNOSTICS")
print("=" * 70)

df = pd.read_csv(DATA_PATH)

print(f"\nDataset shape: {df.shape}")

TARGET = "recovered"

if TARGET not in df.columns:
    raise ValueError("Target column 'recovered' not found.")

# Prevent target leakage
df = df.drop(columns=["recovered_amount"], errors="ignore")


# ============================================================
# FEATURE ENGINEERING
# ============================================================

def build_features(data: pd.DataFrame) -> pd.DataFrame:

    data = data.copy()

    # -----------------------------
    # Amount features
    # -----------------------------

    data["log_amount"] = np.log1p(data["amount"])

    data["high_value_flag"] = (
        data["amount"] >= data["amount"].quantile(0.75)
    ).astype(int)

    data["amount_band"] = pd.cut(
        data["amount"],
        bins=[-np.inf, 1000, 5000, 10000, np.inf],
        labels=["low", "medium", "high", "very_high"],
    ).astype(str)

    # -----------------------------
    # Customer reliability
    # -----------------------------

    data["customer_unreliability"] = (
        1 - data["customer_success_rate"]
    )

    data["historical_failure_rate"] = (
        data["historical_failed_payments"]
        / data["historical_payments"].replace(0, 1)
    )

    data["historical_recovery_rate_safe"] = (
        data["historical_recovered_payments"]
        / data["historical_failed_payments"].replace(0, 1)
    )

    data["customer_history_strength"] = np.log1p(
        data["historical_payments"]
    )

    data["customer_tenure_years"] = (
        data["customer_tenure_days"] / 365
    )

    # -----------------------------
    # Recovery history
    # -----------------------------

    data["recovery_attempt_pressure"] = (
        data["previous_recovery_attempts"]
        + data["previous_attempts"]
    )

    data["customer_recovery_momentum"] = (
        data["previous_recovery_success"]
        * data["customer_success_rate"]
    )

    # -----------------------------
    # Recency
    # -----------------------------

    data["recency_risk"] = (
        data["days_since_last_success"] / 30
    )

    data["recent_failure_flag"] = (
        data["hours_since_failure"] <= 6
    ).astype(int)

    data["stale_failure_flag"] = (
        data["hours_since_failure"] >= 48
    ).astype(int)

    data["days_since_success_risk"] = (
        data["days_since_last_success"] >= 30
    ).astype(int)

    # -----------------------------
    # Attempt history
    # -----------------------------

    data["no_previous_attempt"] = (
        data["previous_attempts"] == 0
    ).astype(int)

    data["multiple_attempt_flag"] = (
        data["previous_attempts"] >= 2
    ).astype(int)

    # -----------------------------
    # Time features
    # -----------------------------

    data["business_hours_flag"] = (
        (data["payment_hour"] >= 9)
        & (data["payment_hour"] <= 18)
    ).astype(int)

    data["late_night_flag"] = (
        (data["payment_hour"] < 6)
        | (data["payment_hour"] >= 23)
    ).astype(int)

    # -----------------------------
    # Interaction features
    # -----------------------------

    data["failure_payment_method"] = (
        data["failure_reason"].astype(str)
        + "_"
        + data["payment_method"].astype(str)
    )

    data["failure_intervention"] = (
        data["failure_reason"].astype(str)
        + "_"
        + data["intervention"].astype(str)
    )

    data["method_intervention"] = (
        data["payment_method"].astype(str)
        + "_"
        + data["intervention"].astype(str)
    )

    data["customer_attempt_interaction"] = (
        data["customer_success_rate"]
        * (1 + data["previous_attempts"])
    )

    data["history_attempt_interaction"] = (
        data["historical_recovery_rate"]
        * (1 + data["previous_recovery_attempts"])
    )

    # -----------------------------
    # Intervention strength
    # -----------------------------

    intervention_strength_map = {
        "retry_now": 1,
        "retry_later": 2,
        "request_alternative_payment": 3,
        "request_card_update": 4,
    }

    data["intervention_strength"] = (
        data["intervention"]
        .map(intervention_strength_map)
        .fillna(0)
    )

    return data


# ============================================================
# BUILD FEATURES
# ============================================================

X = df.drop(columns=[TARGET])
y = df[TARGET]

X = build_features(X)

print(f"Engineered feature count: {X.shape[1]}")


# ============================================================
# TRAIN / TEST SPLIT
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y,
)


# ============================================================
# IDENTIFY COLUMN TYPES
# ============================================================

categorical_features = X.select_dtypes(
    include=["object", "category"]
).columns.tolist()

numerical_features = X.select_dtypes(
    include=["int64", "float64", "int32", "float32"]
).columns.tolist()


# ============================================================
# PREPROCESSING
# ============================================================

numeric_pipeline = Pipeline(
    steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ]
)

categorical_pipeline = Pipeline(
    steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        (
            "encoder",
            OneHotEncoder(
                handle_unknown="ignore",
                sparse_output=False,
            ),
        ),
    ]
)

preprocessor = ColumnTransformer(
    transformers=[
        ("num", numeric_pipeline, numerical_features),
        ("cat", categorical_pipeline, categorical_features),
    ]
)


# ============================================================
# MODEL
# ============================================================

model = LogisticRegression(
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

print("\nTraining diagnostic model...")

pipeline.fit(X_train, y_train)


# ============================================================
# PREDICTIONS
# ============================================================

predictions = pipeline.predict(X_test)
probabilities = pipeline.predict_proba(X_test)[:, 1]


# ============================================================
# PERFORMANCE
# ============================================================

accuracy = accuracy_score(y_test, predictions)
precision = precision_score(y_test, predictions)
recall = recall_score(y_test, predictions)
f1 = f1_score(y_test, predictions)
roc_auc = roc_auc_score(y_test, probabilities)
pr_auc = average_precision_score(y_test, probabilities)
brier = brier_score_loss(y_test, probabilities)

print("\n" + "=" * 70)
print("MODEL PERFORMANCE")
print("=" * 70)

print(f"Accuracy       : {accuracy:.4f}")
print(f"Precision      : {precision:.4f}")
print(f"Recall         : {recall:.4f}")
print(f"F1 Score       : {f1:.4f}")
print(f"ROC-AUC        : {roc_auc:.4f}")
print(f"PR-AUC         : {pr_auc:.4f}")
print(f"Brier Score    : {brier:.4f}")


# ============================================================
# CONFUSION MATRIX
# ============================================================

cm = confusion_matrix(y_test, predictions)

print("\n" + "=" * 70)
print("CONFUSION MATRIX")
print("=" * 70)

print(cm)

cm_df = pd.DataFrame(
    cm,
    index=["Actual 0", "Actual 1"],
    columns=["Predicted 0", "Predicted 1"],
)

cm_df.to_csv(
    OUTPUT_DIR / "v2_confusion_matrix.csv"
)


# ============================================================
# PERMUTATION IMPORTANCE
# ============================================================

print("\n" + "=" * 70)
print("CALCULATING FEATURE IMPORTANCE")
print("=" * 70)

importance = permutation_importance(
    pipeline,
    X_test,
    y_test,
    scoring="roc_auc",
    n_repeats=5,
    random_state=42,
    n_jobs=-1,
)

importance_df = pd.DataFrame(
    {
        "feature": X_test.columns,
        "importance_mean": importance.importances_mean,
        "importance_std": importance.importances_std,
    }
).sort_values(
    "importance_mean",
    ascending=False,
)

importance_path = OUTPUT_DIR / "v2_feature_importance.csv"

importance_df.to_csv(
    importance_path,
    index=False,
)

print("\nTOP 20 FEATURES")

print(
    importance_df.head(20).to_string(index=False)
)


# ============================================================
# ERROR ANALYSIS DATASET
# ============================================================

analysis_df = X_test.copy()

analysis_df["actual"] = y_test.values
analysis_df["predicted"] = predictions
analysis_df["probability"] = probabilities

analysis_df["error_type"] = np.where(
    (analysis_df["actual"] == 1)
    & (analysis_df["predicted"] == 0),
    "false_negative",
    np.where(
        (analysis_df["actual"] == 0)
        & (analysis_df["predicted"] == 1),
        "false_positive",
        "correct",
    ),
)


# ============================================================
# ERROR RATE BY FAILURE REASON
# ============================================================

failure_analysis = (
    analysis_df.groupby("failure_reason")
    .agg(
        samples=("actual", "size"),
        actual_recovery_rate=("actual", "mean"),
        predicted_recovery_rate=("predicted", "mean"),
        average_probability=("probability", "mean"),
        false_negatives=(
            "error_type",
            lambda x: (x == "false_negative").sum(),
        ),
        false_positives=(
            "error_type",
            lambda x: (x == "false_positive").sum(),
        ),
    )
    .reset_index()
)

failure_analysis.to_csv(
    OUTPUT_DIR / "v2_error_by_failure_reason.csv",
    index=False,
)

print("\n" + "=" * 70)
print("ERROR ANALYSIS BY FAILURE REASON")
print("=" * 70)

print(
    failure_analysis.to_string(index=False)
)


# ============================================================
# ERROR RATE BY INTERVENTION
# ============================================================

intervention_analysis = (
    analysis_df.groupby("intervention")
    .agg(
        samples=("actual", "size"),
        actual_recovery_rate=("actual", "mean"),
        predicted_recovery_rate=("predicted", "mean"),
        average_probability=("probability", "mean"),
        false_negatives=(
            "error_type",
            lambda x: (x == "false_negative").sum(),
        ),
        false_positives=(
            "error_type",
            lambda x: (x == "false_positive").sum(),
        ),
    )
    .reset_index()
)

intervention_analysis.to_csv(
    OUTPUT_DIR / "v2_error_by_intervention.csv",
    index=False,
)

print("\n" + "=" * 70)
print("ERROR ANALYSIS BY INTERVENTION")
print("=" * 70)

print(
    intervention_analysis.to_string(index=False)
)


# ============================================================
# PROBABILITY CALIBRATION BINS
# ============================================================

analysis_df["probability_bin"] = pd.cut(
    analysis_df["probability"],
    bins=[
        0.0,
        0.1,
        0.2,
        0.3,
        0.4,
        0.5,
        0.6,
        0.7,
        0.8,
        0.9,
        1.0,
    ],
    include_lowest=True,
)

calibration = (
    analysis_df.groupby(
        "probability_bin",
        observed=False,
    )
    .agg(
        samples=("actual", "size"),
        predicted_probability=("probability", "mean"),
        actual_recovery_rate=("actual", "mean"),
    )
    .reset_index()
)

calibration.to_csv(
    OUTPUT_DIR / "v2_calibration.csv",
    index=False,
)


# ============================================================
# SAVE COMPLETE TEST RESULTS
# ============================================================

results_path = OUTPUT_DIR / "v2_test_predictions.csv"

analysis_df.to_csv(
    results_path,
    index=False,
)


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("DIAGNOSTIC COMPLETE")
print("=" * 70)

print(f"\nFeature importance saved to:")
print(importance_path)

print("\nError analysis saved to:")
print(OUTPUT_DIR / "v2_error_by_failure_reason.csv")

print("\nIntervention analysis saved to:")
print(OUTPUT_DIR / "v2_error_by_intervention.csv")

print("\nCalibration saved to:")
print(OUTPUT_DIR / "v2_calibration.csv")

print("\nTest predictions saved to:")
print(results_path)

print("\nNext step:")
print("Use these diagnostics to decide what to improve.")
