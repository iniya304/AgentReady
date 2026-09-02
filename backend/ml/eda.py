from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


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

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# Load dataset
# ---------------------------------------------------------

df = pd.read_csv(DATA_PATH)

print("=" * 70)
print("AgentReady - Exploratory Data Analysis")
print("=" * 70)

print(f"\nDataset path: {DATA_PATH}")
print(f"Shape: {df.shape}")


# ---------------------------------------------------------
# Column information
# ---------------------------------------------------------

print("\n" + "-" * 70)
print("COLUMN INFORMATION")
print("-" * 70)

print(df.dtypes)


# ---------------------------------------------------------
# Missing values
# ---------------------------------------------------------

print("\n" + "-" * 70)
print("MISSING VALUES")
print("-" * 70)

print(df.isnull().sum())


# ---------------------------------------------------------
# Duplicate rows
# ---------------------------------------------------------

print("\n" + "-" * 70)
print("DUPLICATES")
print("-" * 70)

print("Duplicate rows:", df.duplicated().sum())


# ---------------------------------------------------------
# Target distribution
# ---------------------------------------------------------

print("\n" + "-" * 70)
print("TARGET DISTRIBUTION")
print("-" * 70)

print(df["recovered"].value_counts())

print("\nPercentage:")
print(df["recovered"].value_counts(normalize=True))


# ---------------------------------------------------------
# Numerical statistics
# ---------------------------------------------------------

print("\n" + "-" * 70)
print("NUMERICAL SUMMARY")
print("-" * 70)

print(df.describe())


# ---------------------------------------------------------
# Recovery rate by failure reason
# ---------------------------------------------------------

print("\n" + "-" * 70)
print("RECOVERY RATE BY FAILURE REASON")
print("-" * 70)

failure_analysis = (
    df.groupby("failure_reason")["recovered"]
    .agg(["count", "mean"])
    .sort_values("mean", ascending=False)
)

print(failure_analysis)


# ---------------------------------------------------------
# Recovery rate by payment method
# ---------------------------------------------------------

print("\n" + "-" * 70)
print("RECOVERY RATE BY PAYMENT METHOD")
print("-" * 70)

method_analysis = (
    df.groupby("payment_method")["recovered"]
    .agg(["count", "mean"])
    .sort_values("mean", ascending=False)
)

print(method_analysis)


# ---------------------------------------------------------
# Recovery rate by intervention
# ---------------------------------------------------------

print("\n" + "-" * 70)
print("RECOVERY RATE BY INTERVENTION")
print("-" * 70)

intervention_analysis = (
    df.groupby("intervention")["recovered"]
    .agg(["count", "mean"])
    .sort_values("mean", ascending=False)
)

print(intervention_analysis)


# ---------------------------------------------------------
# Average payment amount by outcome
# ---------------------------------------------------------

print("\n" + "-" * 70)
print("AVERAGE PAYMENT AMOUNT BY OUTCOME")
print("-" * 70)

amount_analysis = (
    df.groupby("recovered")["amount"]
    .agg(["count", "mean", "median"])
)

print(amount_analysis)


# ---------------------------------------------------------
# Save analysis tables
# ---------------------------------------------------------

failure_analysis.to_csv(
    OUTPUT_DIR / "recovery_by_failure_reason.csv"
)

method_analysis.to_csv(
    OUTPUT_DIR / "recovery_by_payment_method.csv"
)

intervention_analysis.to_csv(
    OUTPUT_DIR / "recovery_by_intervention.csv"
)


# ---------------------------------------------------------
# Visualization 1
# ---------------------------------------------------------

plt.figure(figsize=(9, 5))

failure_analysis["mean"].plot(kind="bar")

plt.title("Recovery Rate by Failure Reason")
plt.xlabel("Failure Reason")
plt.ylabel("Recovery Rate")
plt.xticks(rotation=30)
plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "recovery_by_failure_reason.png",
    dpi=150
)

plt.close()


# ---------------------------------------------------------
# Visualization 2
# ---------------------------------------------------------

plt.figure(figsize=(9, 5))

intervention_analysis["mean"].plot(kind="bar")

plt.title("Recovery Rate by Intervention")
plt.xlabel("Intervention")
plt.ylabel("Recovery Rate")
plt.xticks(rotation=30)
plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "recovery_by_intervention.png",
    dpi=150
)

plt.close()


# ---------------------------------------------------------
# Visualization 3
# ---------------------------------------------------------

plt.figure(figsize=(7, 5))

df["recovered"].value_counts().sort_index().plot(
    kind="bar"
)

plt.title("Payment Recovery Distribution")
plt.xlabel("Recovered")
plt.ylabel("Number of Payments")

plt.xticks(
    [0, 1],
    ["Not Recovered", "Recovered"],
    rotation=0
)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "recovery_distribution.png",
    dpi=150
)

plt.close()


# ---------------------------------------------------------
# Complete
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("EDA COMPLETE")
print("=" * 70)

print(f"Outputs saved to: {OUTPUT_DIR}")