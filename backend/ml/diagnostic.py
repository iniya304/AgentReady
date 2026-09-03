from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score


# ============================================================
# AgentReady - Dataset Signal Diagnostic
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "recovery_training_data.csv"

print("=" * 70)
print("AgentReady - Dataset Signal Diagnostic")
print("=" * 70)

df = pd.read_csv(DATA_PATH)

print(f"\nDataset shape: {df.shape}")

# ------------------------------------------------------------
# Remove leakage
# ------------------------------------------------------------

df = df.drop(columns=["recovered_amount"])

X = df.drop(columns=["recovered"])
y = df["recovered"]


# ------------------------------------------------------------
# Preprocessing
# ------------------------------------------------------------

categorical_features = [
    "failure_reason",
    "payment_method",
    "intervention",
]

numerical_features = [
    "amount",
    "customer_success_rate",
    "previous_attempts",
    "hours_since_failure",
]


preprocessor = ColumnTransformer(
    transformers=[
        (
            "numeric",
            StandardScaler(),
            numerical_features,
        ),
        (
            "categorical",
            OneHotEncoder(
                handle_unknown="ignore",
                sparse_output=False,
            ),
            categorical_features,
        ),
    ]
)


# ------------------------------------------------------------
# Model
# ------------------------------------------------------------

model = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        (
            "classifier",
            LogisticRegression(
                max_iter=3000,
                random_state=42,
            ),
        ),
    ]
)


# ------------------------------------------------------------
# 5-fold cross validation
# ------------------------------------------------------------

cv = StratifiedKFold(
    n_splits=5,
    shuffle=True,
    random_state=42,
)


scores = cross_val_score(
    model,
    X,
    y,
    cv=cv,
    scoring="roc_auc",
)


print("\nROC-AUC by fold:")

for i, score in enumerate(scores, start=1):
    print(f"Fold {i}: {score:.4f}")


print("\n" + "=" * 70)
print("DIAGNOSTIC RESULT")
print("=" * 70)

print(f"Mean ROC-AUC: {scores.mean():.4f}")
print(f"Std ROC-AUC : {scores.std():.4f}")

print("\nMajority-class baseline:")
print(f"Recovery rate: {y.mean():.2%}")

print("\nInterpretation:")

if scores.mean() < 0.60:
    print(
        "⚠️ The dataset contains weak learnable signal."
    )
elif scores.mean() < 0.70:
    print(
        "🟡 The dataset contains moderate learnable signal."
    )
else:
    print(
        "🟢 The dataset contains strong learnable signal."
    )

print("=" * 70)