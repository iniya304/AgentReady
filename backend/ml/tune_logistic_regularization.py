from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    brier_score_loss,
)
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_PATH = BASE_DIR / "data" / "recovery_training_data_v2.csv"
OUTPUT_DIR = BASE_DIR / "ml" / "outputs"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("LOGISTIC REGRESSION REGULARIZATION + FEATURE SELECTION")
print("=" * 70)

df = pd.read_csv(DATA_PATH)

print(f"\nDataset shape: {df.shape}")

TARGET = "recovered"

if TARGET not in df.columns:
    raise ValueError(f"Target column '{TARGET}' not found.")

# Prevent target leakage
df = df.drop(columns=["recovered_amount"])

X_raw = df.drop(columns=[TARGET])
y = df[TARGET]


# ============================================================
# FEATURE ENGINEERING
# ============================================================

def build_features(df_input: pd.DataFrame) -> pd.DataFrame:

    df = df_input.copy()

    # --------------------------------------------------------
    # Amount features
    # --------------------------------------------------------

    df["log_amount"] = np.log1p(df["amount"])

    df["high_value_flag"] = (
        df["amount"] >= 10000
    ).astype(int)

    # IMPORTANT:
    # Fixed business thresholds instead of dataset quantiles.
    # This avoids information leakage.
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

    # --------------------------------------------------------
    # Customer reliability
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Attempt pressure
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Recency
    # --------------------------------------------------------

    df["recent_failure_flag"] = (
        df["hours_since_failure"] <= 6
    ).astype(int)

    df["stale_failure_flag"] = (
        df["hours_since_failure"] >= 48
    ).astype(int)

    df["recency_risk"] = np.log1p(
        df["days_since_last_success"]
    )

    # --------------------------------------------------------
    # Time features
    # --------------------------------------------------------

    df["business_hours_flag"] = (
        df["payment_hour"].between(9, 18)
    ).astype(int)

    df["late_night_flag"] = (
        (df["payment_hour"] < 6)
        | (df["payment_hour"] >= 23)
    ).astype(int)

    # --------------------------------------------------------
    # Interaction features
    # --------------------------------------------------------

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

    df["intervention_strength"] = df[
        "intervention"
    ].map(
        {
            "retry_now": 1,
            "retry_later": 2,
            "request_alternative_payment": 3,
            "request_card_update": 3,
        }
    ).fillna(0)

    return df


X = build_features(X_raw)

print(f"Engineered feature count: {X.shape[1]}")


# ============================================================
# FEATURE SETS
# ============================================================

# All available engineered features
ALL_FEATURES = X.columns.tolist()


# Reduced set:
# Remove deliberately redundant features.
REDUCED_FEATURES = [
    # Raw/core
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

    # Amount
    "log_amount",
    "high_value_flag",
    "amount_band",

    # Customer history
    "historical_failure_rate",
    "customer_history_strength",
    "customer_recovery_momentum",

    # Attempts
    "attempt_pressure",
    "recovery_attempt_pressure",
    "no_previous_attempt",
    "multiple_attempt_flag",

    # Recency
    "recent_failure_flag",
    "stale_failure_flag",

    # Time
    "business_hours_flag",
    "late_night_flag",

    # Interactions
    "failure_payment_method",
    "failure_intervention",
    "method_intervention",
    "customer_attempt_interaction",
    "history_attempt_interaction",
    "intervention_strength",
]


# Keep only columns that actually exist
REDUCED_FEATURES = [
    col for col in REDUCED_FEATURES
    if col in X.columns
]


FEATURE_SETS = {
    "all_features": ALL_FEATURES,
    "reduced_features": REDUCED_FEATURES,
}


# ============================================================
# TRAIN / FINAL TEST SPLIT
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y,
)

print(f"\nTraining samples: {len(X_train)}")
print(f"Final test samples: {len(X_test)}")


# ============================================================
# CROSS VALIDATION
# ============================================================

cv = StratifiedKFold(
    n_splits=5,
    shuffle=True,
    random_state=42,
)


C_VALUES = [
    0.01,
    0.03,
    0.1,
    0.3,
    1.0,
    3.0,
]


results = []


# ============================================================
# HELPER
# ============================================================

def make_pipeline(X_subset: pd.DataFrame, C: float):

    categorical_features = [
        col
        for col in X_subset.columns
        if str(X_subset[col].dtype)
        in {"object", "string", "str", "category"}
    ]

    numerical_features = [
        col
        for col in X_subset.columns
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

    model = LogisticRegression(
        C=C,
        max_iter=3000,
        random_state=42,
    )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", model),
        ]
    )


# ============================================================
# CV EXPERIMENTS
# ============================================================

print("\n")
print("=" * 70)
print("CROSS-VALIDATION RESULTS")
print("=" * 70)

for feature_set_name, feature_columns in FEATURE_SETS.items():

    print(f"\nFeature set: {feature_set_name}")
    print(f"Features: {len(feature_columns)}")

    X_train_subset = X_train[feature_columns]

    for C in C_VALUES:

        fold_metrics = []

        for fold, (train_idx, val_idx) in enumerate(
            cv.split(X_train_subset, y_train),
            start=1,
        ):

            X_fold_train = X_train_subset.iloc[train_idx]
            X_fold_val = X_train_subset.iloc[val_idx]

            y_fold_train = y_train.iloc[train_idx]
            y_fold_val = y_train.iloc[val_idx]

            pipeline = make_pipeline(
                X_fold_train,
                C,
            )

            pipeline.fit(
                X_fold_train,
                y_fold_train,
            )

            val_prob = pipeline.predict_proba(
                X_fold_val
            )[:, 1]

            val_pred = (
                val_prob >= 0.50
            ).astype(int)

            train_prob = pipeline.predict_proba(
                X_fold_train
            )[:, 1]

            train_auc = roc_auc_score(
                y_fold_train,
                train_prob,
            )

            val_auc = roc_auc_score(
                y_fold_val,
                val_prob,
            )

            fold_metrics.append(
                {
                    "accuracy": accuracy_score(
                        y_fold_val,
                        val_pred,
                    ),
                    "precision": precision_score(
                        y_fold_val,
                        val_pred,
                        zero_division=0,
                    ),
                    "recall": recall_score(
                        y_fold_val,
                        val_pred,
                        zero_division=0,
                    ),
                    "f1": f1_score(
                        y_fold_val,
                        val_pred,
                        zero_division=0,
                    ),
                    "roc_auc": val_auc,
                    "pr_auc": average_precision_score(
                        y_fold_val,
                        val_prob,
                    ),
                    "brier": brier_score_loss(
                        y_fold_val,
                        val_prob,
                    ),
                    "train_auc": train_auc,
                }
            )

        fold_df = pd.DataFrame(fold_metrics)

        mean_metrics = fold_df.mean()

        train_val_gap = (
            mean_metrics["train_auc"]
            - mean_metrics["roc_auc"]
        )

        result = {
            "feature_set": feature_set_name,
            "feature_count": len(feature_columns),
            "C": C,
            "cv_accuracy": mean_metrics["accuracy"],
            "cv_precision": mean_metrics["precision"],
            "cv_recall": mean_metrics["recall"],
            "cv_f1": mean_metrics["f1"],
            "cv_roc_auc": mean_metrics["roc_auc"],
            "cv_pr_auc": mean_metrics["pr_auc"],
            "cv_brier": mean_metrics["brier"],
            "train_roc_auc": mean_metrics["train_auc"],
            "train_cv_gap": train_val_gap,
            "roc_auc_std": fold_df["roc_auc"].std(),
        }

        results.append(result)

        print(
            f"C={C:<4} | "
            f"Accuracy={result['cv_accuracy']:.4f} | "
            f"ROC-AUC={result['cv_roc_auc']:.4f} | "
            f"PR-AUC={result['cv_pr_auc']:.4f} | "
            f"Brier={result['cv_brier']:.4f} | "
            f"Gap={result['train_cv_gap']:.4f}"
        )


# ============================================================
# RESULTS TABLE
# ============================================================

results_df = pd.DataFrame(results)

results_path = (
    OUTPUT_DIR
    / "logistic_regularization_results.csv"
)

results_df.to_csv(
    results_path,
    index=False,
)


# ============================================================
# MODEL SELECTION
# ============================================================

# We want:
# 1. Strong ROC-AUC
# 2. Small train/CV gap
# 3. Good calibration (low Brier score)
#
# Reject clearly overfit candidates.

SAFE_RESULTS = results_df[
    results_df["train_cv_gap"] <= 0.03
].copy()


if SAFE_RESULTS.empty:
    print("\nNo candidate satisfied the strict 0.03 overfitting gap.")
    SAFE_RESULTS = results_df.copy()


BEST = SAFE_RESULTS.sort_values(
    by=[
        "cv_roc_auc",
        "cv_brier",
        "train_cv_gap",
    ],
    ascending=[
        False,
        True,
        True,
    ],
).iloc[0]


# ============================================================
# FINAL TEST EVALUATION
# ============================================================

best_features = FEATURE_SETS[
    BEST["feature_set"]
]

best_C = float(BEST["C"])

print("\n")
print("=" * 70)
print("SELECTED MODEL")
print("=" * 70)

print(f"Feature set : {BEST['feature_set']}")
print(f"Features    : {len(best_features)}")
print(f"C           : {best_C}")
print(f"CV ROC-AUC  : {BEST['cv_roc_auc']:.4f}")
print(f"CV PR-AUC   : {BEST['cv_pr_auc']:.4f}")
print(f"CV Brier    : {BEST['cv_brier']:.4f}")
print(f"Train/CV gap: {BEST['train_cv_gap']:.4f}")


final_pipeline = make_pipeline(
    X_train[best_features],
    best_C,
)

final_pipeline.fit(
    X_train[best_features],
    y_train,
)

test_prob = final_pipeline.predict_proba(
    X_test[best_features]
)[:, 1]

test_pred = (
    test_prob >= 0.50
).astype(int)


# ============================================================
# FINAL TEST METRICS
# ============================================================

final_metrics = {
    "accuracy": accuracy_score(
        y_test,
        test_pred,
    ),
    "precision": precision_score(
        y_test,
        test_pred,
        zero_division=0,
    ),
    "recall": recall_score(
        y_test,
        test_pred,
        zero_division=0,
    ),
    "f1": f1_score(
        y_test,
        test_pred,
        zero_division=0,
    ),
    "roc_auc": roc_auc_score(
        y_test,
        test_prob,
    ),
    "pr_auc": average_precision_score(
        y_test,
        test_prob,
    ),
    "brier": brier_score_loss(
        y_test,
        test_prob,
    ),
}


print("\n")
print("=" * 70)
print("FINAL UNTOUCHED TEST RESULTS")
print("=" * 70)

for metric, value in final_metrics.items():
    print(f"{metric.upper():<12}: {value:.4f}")


# ============================================================
# SAVE FINAL TEST PREDICTIONS
# ============================================================

test_output = X_test.copy()

test_output["actual_recovered"] = y_test.values

test_output["predicted_probability"] = test_prob

test_output["predicted_recovered"] = test_pred

test_predictions_path = (
    OUTPUT_DIR
    / "regularized_final_test_predictions.csv"
)

test_output.to_csv(
    test_predictions_path,
    index=False,
)


# ============================================================
# SAVE FINAL MODEL METRICS
# ============================================================

final_summary = pd.DataFrame(
    [
        {
            "feature_set": BEST["feature_set"],
            "feature_count": len(best_features),
            "C": best_C,
            "cv_accuracy": BEST["cv_accuracy"],
            "cv_precision": BEST["cv_precision"],
            "cv_recall": BEST["cv_recall"],
            "cv_f1": BEST["cv_f1"],
            "cv_roc_auc": BEST["cv_roc_auc"],
            "cv_pr_auc": BEST["cv_pr_auc"],
            "cv_brier": BEST["cv_brier"],
            "train_cv_gap": BEST["train_cv_gap"],
            "final_test_accuracy": final_metrics["accuracy"],
            "final_test_precision": final_metrics["precision"],
            "final_test_recall": final_metrics["recall"],
            "final_test_f1": final_metrics["f1"],
            "final_test_roc_auc": final_metrics["roc_auc"],
            "final_test_pr_auc": final_metrics["pr_auc"],
            "final_test_brier": final_metrics["brier"],
        }
    ]
)

summary_path = (
    OUTPUT_DIR
    / "regularized_final_model_summary.csv"
)

final_summary.to_csv(
    summary_path,
    index=False,
)


print("\n")
print("=" * 70)
print("FILES SAVED")
print("=" * 70)

print(results_path)
print(test_predictions_path)
print(summary_path)

print("\nExperiment complete.")


