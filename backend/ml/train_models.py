from pathlib import Path

import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBClassifier


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_PATH = (
    PROJECT_ROOT
    / "backend"
    / "data"
    / "recovery_training_data.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "backend"
    / "ml"
    / "outputs"
)

MODEL_DIR = (
    PROJECT_ROOT
    / "backend"
    / "ml"
    / "models"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# Load dataset
# ---------------------------------------------------------

print("=" * 70)
print("AgentReady - ML Model Benchmark")
print("=" * 70)

df = pd.read_csv(DATA_PATH)

print(f"\nDataset: {DATA_PATH}")
print(f"Rows: {len(df):,}")
print(f"Columns: {len(df.columns)}")


# ---------------------------------------------------------
# Remove target leakage
# ---------------------------------------------------------

# recovered_amount is calculated from recovered.
# It must NOT be used as a model feature.

LEAKAGE_COLUMNS = ["recovered_amount"]

df = df.drop(columns=LEAKAGE_COLUMNS)


# ---------------------------------------------------------
# Features and target
# ---------------------------------------------------------

TARGET = "recovered"

X = df.drop(columns=[TARGET])
y = df[TARGET]


# ---------------------------------------------------------
# Train / test split
# ---------------------------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y,
)

print("\n" + "-" * 70)
print("DATA SPLIT")
print("-" * 70)

print(f"Training samples: {len(X_train):,}")
print(f"Testing samples:  {len(X_test):,}")

print(f"Training recovery rate: {y_train.mean():.2%}")
print(f"Testing recovery rate:  {y_test.mean():.2%}")


# ---------------------------------------------------------
# Feature types
# ---------------------------------------------------------

NUMERICAL_FEATURES = [
    "amount",
    "customer_success_rate",
    "previous_attempts",
    "hours_since_failure",
]

CATEGORICAL_FEATURES = [
    "failure_reason",
    "payment_method",
    "intervention",
]


# ---------------------------------------------------------
# Preprocessing
# ---------------------------------------------------------

preprocessor = ColumnTransformer(
    transformers=[
        (
            "numerical",
            StandardScaler(),
            NUMERICAL_FEATURES,
        ),
        (
            "categorical",
            OneHotEncoder(
                handle_unknown="ignore",
                sparse_output=False,
            ),
            CATEGORICAL_FEATURES,
        ),
    ]
)


# ---------------------------------------------------------
# Models
# ---------------------------------------------------------

models = {
    "Logistic Regression": LogisticRegression(
        max_iter=2000,
        random_state=42,
    ),

    "Random Forest": RandomForestClassifier(
        n_estimators=300,
        max_depth=None,
        min_samples_split=5,
        random_state=42,
        n_jobs=-1,
    ),

    "HistGradientBoosting": HistGradientBoostingClassifier(
        max_iter=200,
        learning_rate=0.08,
        max_leaf_nodes=31,
        random_state=42,
    ),

    "XGBoost": XGBClassifier(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="binary:logistic",
        eval_metric="logloss",
        random_state=42,
        n_jobs=-1,
    ),
}


# ---------------------------------------------------------
# Train and evaluate
# ---------------------------------------------------------

results = []
trained_pipelines = {}

for model_name, model in models.items():

    print("\n" + "=" * 70)
    print(f"Training: {model_name}")
    print("=" * 70)

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", model),
        ]
    )

    pipeline.fit(X_train, y_train)

    predictions = pipeline.predict(X_test)
    probabilities = pipeline.predict_proba(X_test)[:, 1]

    accuracy = accuracy_score(
        y_test,
        predictions,
    )

    precision = precision_score(
        y_test,
        predictions,
        zero_division=0,
    )

    recall = recall_score(
        y_test,
        predictions,
        zero_division=0,
    )

    f1 = f1_score(
        y_test,
        predictions,
        zero_division=0,
    )

    roc_auc = roc_auc_score(
        y_test,
        probabilities,
    )

    result = {
        "model": model_name,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "roc_auc": roc_auc,
    }

    results.append(result)
    trained_pipelines[model_name] = pipeline

    print(f"Accuracy : {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall   : {recall:.4f}")
    print(f"F1 Score : {f1:.4f}")
    print(f"ROC-AUC  : {roc_auc:.4f}")


# ---------------------------------------------------------
# Compare models
# ---------------------------------------------------------

results_df = pd.DataFrame(results)

results_df = results_df.sort_values(
    by="roc_auc",
    ascending=False,
).reset_index(drop=True)


print("\n" + "=" * 70)
print("MODEL COMPARISON")
print("=" * 70)

print(
    results_df.to_string(
        index=False,
        float_format=lambda value: f"{value:.4f}",
    )
)


# ---------------------------------------------------------
# Select best model
# ---------------------------------------------------------

best_model_name = results_df.iloc[0]["model"]

best_pipeline = trained_pipelines[
    best_model_name
]


print("\n" + "=" * 70)
print("BEST MODEL")
print("=" * 70)

print(f"Selected model: {best_model_name}")
print(
    f"ROC-AUC: "
    f"{results_df.iloc[0]['roc_auc']:.4f}"
)


# ---------------------------------------------------------
# Save benchmark results
# ---------------------------------------------------------

results_path = (
    OUTPUT_DIR
    / "model_benchmark.csv"
)

results_df.to_csv(
    results_path,
    index=False,
)


# ---------------------------------------------------------
# Save best model
# ---------------------------------------------------------

model_path = (
    MODEL_DIR
    / "best_recovery_model.joblib"
)

joblib.dump(
    best_pipeline,
    model_path,
)


# ---------------------------------------------------------
# Save model metadata
# ---------------------------------------------------------

metadata = {
    "selected_model": best_model_name,
    "target": TARGET,
    "test_size": 0.20,
    "random_state": 42,
    "features": list(X.columns),
    "metrics": results_df.iloc[0].to_dict(),
}

metadata_path = (
    OUTPUT_DIR
    / "best_model_metadata.json"
)

import json

with open(
    metadata_path,
    "w",
    encoding="utf-8",
) as file:
    json.dump(
        metadata,
        file,
        indent=4,
        default=float,
    )


# ---------------------------------------------------------
# Complete
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("MODEL TRAINING COMPLETE")
print("=" * 70)

print(f"\nBenchmark results:")
print(results_path)

print(f"\nBest model:")
print(model_path)

print(f"\nMetadata:")
print(metadata_path)

print("\nNext step: integrate the selected model into AgentReady.")	