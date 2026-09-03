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
from sklearn.metrics import make_scorer, average_precision_score

from xgboost import XGBClassifier


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_PATH = (
    BASE_DIR
    / "data"
    / "recovery_training_data_v2.csv"
)

OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# CONFIGURATION
# ============================================================

RANDOM_STATE = 42
N_SPLITS = 5


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("AgentReady V2 - OVERFITTING-SAFE MODEL TUNING")
print("=" * 70)

df = pd.read_csv(DATA_PATH)

print(f"\nDataset shape: {df.shape}")

TARGET = "recovered"

# Prevent target leakage.
df = df.drop(
    columns=["recovered_amount"],
    errors="ignore",
)


# ============================================================
# FEATURE ENGINEERING
# ============================================================

def build_features(data: pd.DataFrame) -> pd.DataFrame:

    data = data.copy()

    # --------------------------------------------------------
    # Amount
    # --------------------------------------------------------

    data["log_amount"] = np.log1p(data["amount"])

    data["high_value_flag"] = (
        data["amount"] >= data["amount"].quantile(0.75)
    ).astype(int)

    data["amount_band"] = pd.cut(
        data["amount"],
        bins=[
            -np.inf,
            1000,
            5000,
            10000,
            np.inf,
        ],
        labels=[
            "low",
            "medium",
            "high",
            "very_high",
        ],
    ).astype(str)

    # --------------------------------------------------------
    # Customer reliability
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Recovery history
    # --------------------------------------------------------

    data["recovery_attempt_pressure"] = (
        data["previous_recovery_attempts"]
        + data["previous_attempts"]
    )

    data["customer_recovery_momentum"] = (
        data["previous_recovery_success"]
        * data["customer_success_rate"]
    )

    # --------------------------------------------------------
    # Recency
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Attempts
    # --------------------------------------------------------

    data["no_previous_attempt"] = (
        data["previous_attempts"] == 0
    ).astype(int)

    data["multiple_attempt_flag"] = (
        data["previous_attempts"] >= 2
    ).astype(int)

    # --------------------------------------------------------
    # Time
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
    # Interactions
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
        data["historical_recovery_rate"]
        * (1 + data["previous_recovery_attempts"])
    )

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
# PREPARE FEATURES
# ============================================================

X = df.drop(columns=[TARGET])
y = df[TARGET]

X = build_features(X)

print(
    f"Engineered feature count: {X.shape[1]}"
)


# ============================================================
# COLUMN TYPES
# ============================================================

categorical_features = X.select_dtypes(
    include=["object", "category"]
).columns.tolist()

numerical_features = X.select_dtypes(
    include=[
        "int64",
        "float64",
        "int32",
        "float32",
    ]
).columns.tolist()


# ============================================================
# PREPROCESSOR
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
            "num",
            numeric_pipeline,
            numerical_features,
        ),
        (
            "cat",
            categorical_pipeline,
            categorical_features,
        ),
    ]
)


# ============================================================
# MODELS
# ============================================================

models = {

    "Logistic Regression": LogisticRegression(
        C=1.0,
        max_iter=3000,
        random_state=RANDOM_STATE,
    ),

    "Random Forest": RandomForestClassifier(
        n_estimators=400,
        max_depth=10,
        min_samples_split=10,
        min_samples_leaf=4,
        max_features="sqrt",
        class_weight="balanced",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    ),

    "HistGradientBoosting": HistGradientBoostingClassifier(
        max_iter=200,
        learning_rate=0.05,
        max_leaf_nodes=20,
        max_depth=6,
        l2_regularization=1.0,
        random_state=RANDOM_STATE,
    ),

    "XGBoost": XGBClassifier(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        min_child_weight=5,
        subsample=0.85,
        colsample_bytree=0.85,
        reg_alpha=0.1,
        reg_lambda=2.0,
        objective="binary:logistic",
        eval_metric="logloss",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    ),
}


# ============================================================
# CROSS VALIDATION
# ============================================================

cv = StratifiedKFold(
    n_splits=N_SPLITS,
    shuffle=True,
    random_state=RANDOM_STATE,
)


scoring = {
    "accuracy": "accuracy",
    "precision": "precision",
    "recall": "recall",
    "f1": "f1",
    "roc_auc": "roc_auc",
    "pr_auc": "average_precision",
    "neg_brier": "neg_brier_score",
}


# ============================================================
# RUN BENCHMARK
# ============================================================

results = []

for name, model in models.items():

    print("\n" + "-" * 70)
    print(f"Testing: {name}")
    print("-" * 70)

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
        return_train_score=True,
    )

    row = {
        "model": name,

        "accuracy_mean":
            scores["test_accuracy"].mean(),

        "accuracy_std":
            scores["test_accuracy"].std(),

        "precision_mean":
            scores["test_precision"].mean(),

        "recall_mean":
            scores["test_recall"].mean(),

        "f1_mean":
            scores["test_f1"].mean(),

        "roc_auc_mean":
            scores["test_roc_auc"].mean(),

        "roc_auc_std":
            scores["test_roc_auc"].std(),

        "pr_auc_mean":
            scores["test_pr_auc"].mean(),

        "brier_score_mean":
            -scores["test_neg_brier"].mean(),

        # Training ROC-AUC is included ONLY to detect
        # suspicious train/test gaps.
        "train_roc_auc_mean":
            scores["train_roc_auc"].mean(),
    }

    row["roc_auc_gap"] = (
        row["train_roc_auc_mean"]
        - row["roc_auc_mean"]
    )

    results.append(row)

    print(
        f"CV Accuracy : "
        f"{row['accuracy_mean']:.4f} "
        f"+/- {row['accuracy_std']:.4f}"
    )

    print(
        f"CV ROC-AUC  : "
        f"{row['roc_auc_mean']:.4f} "
        f"+/- {row['roc_auc_std']:.4f}"
    )

    print(
        f"CV PR-AUC   : "
        f"{row['pr_auc_mean']:.4f}"
    )

    print(
        f"Train/Test ROC-AUC gap: "
        f"{row['roc_auc_gap']:.4f}"
    )


# ============================================================
# RESULTS
# ============================================================

results_df = pd.DataFrame(results)

results_df = results_df.sort_values(
    "roc_auc_mean",
    ascending=False,
)


# ============================================================
# PRINT FINAL COMPARISON
# ============================================================

print("\n" + "=" * 70)
print("OVERFITTING-SAFE MODEL COMPARISON")
print("=" * 70)

display_columns = [
    "model",
    "accuracy_mean",
    "accuracy_std",
    "precision_mean",
    "recall_mean",
    "f1_mean",
    "roc_auc_mean",
    "roc_auc_std",
    "pr_auc_mean",
    "brier_score_mean",
    "train_roc_auc_mean",
    "roc_auc_gap",
]

print(
    results_df[
        display_columns
    ].to_string(index=False)
)


# ============================================================
# SAVE
# ============================================================

output_path = (
    OUTPUT_DIR
    / "v2_model_tuning_results.csv"
)

results_df.to_csv(
    output_path,
    index=False,
)

print("\nResults saved to:")
print(output_path)


# ============================================================
# OVERFITTING CHECK
# ============================================================

print("\n" + "=" * 70)
print("OVERFITTING CHECK")
print("=" * 70)

for _, row in results_df.iterrows():

    gap = row["roc_auc_gap"]

    if gap <= 0.03:
        status = "GOOD"
    elif gap <= 0.07:
        status = "WATCH"
    else:
        status = "POSSIBLE OVERFITTING"

    print(
        f"{row['model']}: "
        f"gap={gap:.4f} -> {status}"
    )


print("\n" + "=" * 70)
print("TUNING COMPLETE")
print("=" * 70)

