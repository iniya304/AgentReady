from pathlib import Path

import pandas as pd
import numpy as np

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"

PREDICTIONS_PATH = OUTPUT_DIR / "v2_test_predictions.csv"


# ============================================================
# LOAD PREDICTIONS
# ============================================================

print("=" * 70)
print("AgentReady - Threshold Optimization")
print("=" * 70)

df = pd.read_csv(PREDICTIONS_PATH)

print(f"\nLoaded test predictions: {len(df):,}")


# ============================================================
# TEST THRESHOLDS
# ============================================================

results = []

thresholds = np.arange(0.30, 0.81, 0.01)

for threshold in thresholds:

    predictions = (
        df["probability"] >= threshold
    ).astype(int)

    accuracy = accuracy_score(
        df["actual"],
        predictions,
    )

    precision = precision_score(
        df["actual"],
        predictions,
        zero_division=0,
    )

    recall = recall_score(
        df["actual"],
        predictions,
        zero_division=0,
    )

    f1 = f1_score(
        df["actual"],
        predictions,
        zero_division=0,
    )

    tn, fp, fn, tp = confusion_matrix(
        df["actual"],
        predictions,
    ).ravel()

    results.append(
        {
            "threshold": round(threshold, 2),
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "true_negative": tn,
            "false_positive": fp,
            "false_negative": fn,
            "true_positive": tp,
        }
    )


# ============================================================
# RESULTS
# ============================================================

results_df = pd.DataFrame(results)

best_accuracy = results_df.loc[
    results_df["accuracy"].idxmax()
]

best_f1 = results_df.loc[
    results_df["f1"].idxmax()
]

best_precision = results_df.loc[
    results_df["precision"].idxmax()
]


# ============================================================
# PRINT RESULTS
# ============================================================

print("\n" + "=" * 70)
print("DEFAULT THRESHOLD (0.50)")
print("=" * 70)

default = results_df[
    results_df["threshold"] == 0.50
].iloc[0]

print(default.to_string())


print("\n" + "=" * 70)
print("BEST ACCURACY THRESHOLD")
print("=" * 70)

print(best_accuracy.to_string())


print("\n" + "=" * 70)
print("BEST F1 THRESHOLD")
print("=" * 70)

print(best_f1.to_string())


print("\n" + "=" * 70)
print("HIGHEST PRECISION THRESHOLD")
print("=" * 70)

print(best_precision.to_string())


# ============================================================
# TOP THRESHOLDS BY ACCURACY
# ============================================================

print("\n" + "=" * 70)
print("TOP 10 THRESHOLDS BY ACCURACY")
print("=" * 70)

top_accuracy = results_df.sort_values(
    "accuracy",
    ascending=False,
).head(10)

print(
    top_accuracy[
        [
            "threshold",
            "accuracy",
            "precision",
            "recall",
            "f1",
            "false_positive",
            "false_negative",
        ]
    ].to_string(index=False)
)


# ============================================================
# SAVE
# ============================================================

OUTPUT_PATH = OUTPUT_DIR / "threshold_optimization.csv"

results_df.to_csv(
    OUTPUT_PATH,
    index=False,
)

print("\n" + "=" * 70)
print("THRESHOLD OPTIMIZATION COMPLETE")
print("=" * 70)

print(f"\nResults saved to:")
print(OUTPUT_PATH)

print("\nNext step:")
print("Use the selected threshold in the AgentReady prediction service.")

