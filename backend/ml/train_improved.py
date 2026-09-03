from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import (
    RandomForestClassifier,
    HistGradientBoostingClassifier,
)
from sklearn.model_selection import StratifiedKFold, cross_validate

from xgboost import XGBClassifier


# ============================================================
# AgentReady - V2 Improved ML Benchmark
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

# IMPORTANT:
# Use the V2 dataset, not the original V1 dataset.
DATA_PATH = BASE_DIR / "data" / "recovery_training_data_v2.csv"

OUTPUT_DIR = BASE_DIR / "ml" / "outputs"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 1. LOAD DATA
# ============================================================

print("=" * 70)
print("AgentReady - V2 Improved ML Benchmark")
print("=" * 70)

print("\nLoading dataset...")

df = pd.read_csv(DATA_PATH)

print(f"Dataset path: {DATA_PATH}")
print(f"Dataset shape: {df.shape}")


# ============================================================
# 2. BASIC VALIDATION
# ============================================================

required_columns = [
    "amount",
    "failure_reason",
    "payment_method",
    "customer_success_rate",
    "customer_tenure_days",
    "historical_payments",
    "historical_failed_payments",
    "historical_recovered_payments",
    "historical_recovery_rate",
    "days_since_last_success",
    "previous_attempts",
    "hours_since_failure",
    "payment_hour",
    "previous_recovery_attempts",
    "previous_recovery_success",
    "customer_recovery_history",
    "intervention",
    "recovered",
    "recovered_amount",
]

missing_columns = [
    column for column in required_columns
    if column not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing required columns: {missing_columns}"
    )

print("\nDataset validation passed.")

print(f"Missing values: {df.isna().sum().sum()}")
print(f"Duplicate rows: {df.duplicated().sum()}")


# ============================================================
# 3. REMOVE DATA LEAKAGE
# ============================================================

# recovered_amount is calculated directly from recovered.
# Therefore it MUST NOT be used as a model feature.

df = df.drop(columns=["recovered_amount"])


# ============================================================
# 4. FEATURE ENGINEERING
# ============================================================

def build_features(data: pd.DataFrame) -> pd.DataFrame:

    data = data.copy()

    # --------------------------------------------------------
    # Payment amount features
    # --------------------------------------------------------

    data["log_amount"] = np.log1p(data["amount"])

    data["high_value_flag"] = (
        data["amount"] >= 10000
    ).astype(int)

    data["amount_band"] = pd.cut(
        data["amount"],
        bins=[0, 1000, 5000, 10000, 25000, np.inf],
        labels=[
            "very_low",
            "low",
            "medium",
            "high",
            "very_high",
        ],
    ).astype(str)

    # --------------------------------------------------------
    # Customer behaviour
    # --------------------------------------------------------

    data["customer_unreliability"] = (
        1 - data["customer_success_rate"]
    )

    data["attempt_pressure"] = (
        data["previous_attempts"]
        * data["customer_unreliability"]
    )

    data["reliability_band"] = pd.cut(
        data["customer_success_rate"],
        bins=[0, 0.5, 0.75, 0.9, 1.01],
        labels=[
            "low",
            "medium",
            "high",
            "very_high",
        ],
    ).astype(str)

    # --------------------------------------------------------
    # NEW V2: Customer history
    # --------------------------------------------------------

    data["historical_failure_rate"] = np.where(
        data["historical_payments"] > 0,
        data["historical_failed_payments"]
        / data["historical_payments"],
        0,
    )

    data["historical_recovery_rate_safe"] = (
        data["historical_recovery_rate"].clip(0, 1)
    )

    data["customer_history_strength"] = (
        data["historical_recovery_rate_safe"]
        * np.log1p(data["historical_payments"])
    )

    data["customer_tenure_years"] = (
        data["customer_tenure_days"] / 365
    )

    data["recovery_attempt_pressure"] = (
        data["previous_recovery_attempts"]
        * (1 - data["previous_recovery_success"])
    )

    data["customer_recovery_momentum"] = (
        data["customer_recovery_history"]
        + data["previous_recovery_success"]
    )

    # --------------------------------------------------------
    # Failure recency
    # --------------------------------------------------------

    data["recency_risk"] = (
        data["hours_since_failure"] / 24
    )

    data["recent_failure_flag"] = (
        data["hours_since_failure"] <= 6
    ).astype(int)

    data["stale_failure_flag"] = (
        data["hours_since_failure"] >= 48
    ).astype(int)

    data["days_since_success_risk"] = (
        data["days_since_last_success"] / 30
    )

    # --------------------------------------------------------
    # Previous attempt behaviour
    # --------------------------------------------------------

    data["no_previous_attempt"] = (
        data["previous_attempts"] == 0
    ).astype(int)

    data["multiple_attempt_flag"] = (
        data["previous_attempts"] >= 2
    ).astype(int)

    # --------------------------------------------------------
    # Time behaviour
    # --------------------------------------------------------

    data["business_hours_flag"] = (
        (data["payment_hour"] >= 9)
        & (data["payment_hour"] <= 18)
    ).astype(int)

    data["late_night_flag"] = (
        (data["payment_hour"] < 6)
        | (data["payment_hour"] >= 23)
    ).astype(int)

    # --------------------------------------------------------
    # Interaction features
    # --------------------------------------------------------

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
        data["historical_recovery_rate_safe"]
        * (1 + data["previous_recovery_attempts"])
    )

    # --------------------------------------------------------
    # Intervention pressure
    # --------------------------------------------------------

    intervention_weights = {
        "retry_now": 1.0,
        "retry_later": 1.2,
        "request_alternative_payment": 1.4,
        "request_card_update": 1.3,
    }

    data["intervention_strength"] = (
        data["intervention"]
        .map(intervention_weights)
        .fillna(1.0)
    )

    return data


# ============================================================
# 5. PREPARE FEATURES AND TARGET
# ============================================================

X = df.drop(columns=["recovered"])

y = df["recovered"]

X = build_features(X)

print("\nFeature engineering complete.")

print(f"Original features: {len(df.columns) - 1}")
print(f"Engineered features: {X.shape[1]}")

print(
    f"Recovery rate: {y.mean():.2%}"
)


# ============================================================
# 6. FEATURE GROUPS
# ============================================================

categorical_features = [
    "failure_reason",
    "payment_method",
    "intervention",
    "amount_band",
    "reliability_band",
    "failure_payment_method",
    "failure_intervention",
    "method_intervention",
]


numerical_features = [
    column
    for column in X.columns
    if column not in categorical_features
]


print(
    f"Categorical features: {len(categorical_features)}"
)

print(
    f"Numerical features: {len(numerical_features)}"
)


# ============================================================
# 7. PREPROCESSING
# ============================================================

numeric_pipeline = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(strategy="median"),
        ),
        (
            "scaler",
            StandardScaler(),
        ),
    ]
)


categorical_pipeline = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(strategy="most_frequent"),
        ),
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
        (
            "numeric",
            numeric_pipeline,
            numerical_features,
        ),
        (
            "categorical",
            categorical_pipeline,
            categorical_features,
        ),
    ]
)


# ============================================================
# 8. MODELS
# ============================================================

models = {

    "Logistic Regression": LogisticRegression(
        max_iter=3000,
        C=1.0,
        random_state=42,
    ),

    "Random Forest": RandomForestClassifier(
        n_estimators=400,
        max_depth=12,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    ),

    "HistGradientBoosting": HistGradientBoostingClassifier(
        max_iter=250,
        learning_rate=0.06,
        max_leaf_nodes=31,
        l2_regularization=1.0,
        random_state=42,
    ),

    "XGBoost": XGBClassifier(
        n_estimators=400,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        min_child_weight=3,
        reg_lambda=1.0,
        objective="binary:logistic",
        eval_metric="logloss",
        random_state=42,
        n_jobs=-1,
    ),
}


# ============================================================
# 9. 5-FOLD CROSS VALIDATION
# ============================================================

cv = StratifiedKFold(
    n_splits=5,
    shuffle=True,
    random_state=42,
)


scoring = {
    "accuracy": "accuracy",
    "precision": "precision",
    "recall": "recall",
    "f1": "f1",
    "roc_auc": "roc_auc",
}


results = []


print("\n")
print("=" * 70)
print("5-FOLD CROSS-VALIDATION")
print("=" * 70)


for name, model in models.items():

    print(f"\nTraining {name}...")

    pipeline = Pipeline(
        steps=[
            (
                "preprocessor",
                preprocessor,
            ),
            (
                "model",
                model,
            ),
        ]
    )

    scores = cross_validate(
        pipeline,
        X,
        y,
        cv=cv,
        scoring=scoring,
        n_jobs=-1,
        return_train_score=False,
    )

    result = {
        "model": name,

        "accuracy_mean": scores[
            "test_accuracy"
        ].mean(),

        "accuracy_std": scores[
            "test_accuracy"
        ].std(),

        "precision_mean": scores[
            "test_precision"
        ].mean(),

        "recall_mean": scores[
            "test_recall"
        ].mean(),

        "f1_mean": scores[
            "test_f1"
        ].mean(),

        "roc_auc_mean": scores[
            "test_roc_auc"
        ].mean(),

        "roc_auc_std": scores[
            "test_roc_auc"
        ].std(),
    }

    results.append(result)

    print(
        f"Accuracy : {result['accuracy_mean']:.4f}"
    )

    print(
        f"Precision: {result['precision_mean']:.4f}"
    )

    print(
        f"Recall   : {result['recall_mean']:.4f}"
    )

    print(
        f"F1       : {result['f1_mean']:.4f}"
    )

    print(
        f"ROC-AUC  : "
        f"{result['roc_auc_mean']:.4f}"
        f" ± {result['roc_auc_std']:.4f}"
    )


# ============================================================
# 10. SAVE RESULTS
# ============================================================

results_df = pd.DataFrame(results)

results_df = results_df.sort_values(
    "roc_auc_mean",
    ascending=False,
)


output_path = (
    OUTPUT_DIR
    / "improved_model_benchmark_v2.csv"
)


results_df.to_csv(
    output_path,
    index=False,
)


# ============================================================
# 11. DISPLAY FINAL RANKING
# ============================================================

print("\n")
print("=" * 70)
print("FINAL MODEL RANKING - V2")
print("=" * 70)

print(
    results_df[
        [
            "model",
            "accuracy_mean",
            "precision_mean",
            "recall_mean",
            "f1_mean",
            "roc_auc_mean",
            "roc_auc_std",
        ]
    ].to_string(index=False)
)


# ============================================================
# 12. BEST MODEL
# ============================================================

best_model = results_df.iloc[0]


print("\n")
print("=" * 70)
print("🏆 BEST V2 MODEL")
print("=" * 70)

print(
    f"Model: {best_model['model']}"
)

print(
    f"ROC-AUC: "
    f"{best_model['roc_auc_mean']:.4f}"
)

print(
    f"Accuracy: "
    f"{best_model['accuracy_mean']:.4f}"
)

print(
    f"Precision: "
    f"{best_model['precision_mean']:.4f}"
)

print(
    f"Recall: "
    f"{best_model['recall_mean']:.4f}"
)

print(
    f"F1: "
    f"{best_model['f1_mean']:.4f}"
)

print(
    f"ROC-AUC std: "
    f"{best_model['roc_auc_std']:.4f}"
)

print(
    f"\nResults saved to:\n{output_path}"
)

print("=" * 70)