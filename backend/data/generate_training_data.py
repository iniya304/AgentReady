import numpy as np
import pandas as pd

# ---------------------------------------------------------
# AgentReady - Synthetic Payment Recovery Dataset
# ---------------------------------------------------------
# This dataset is synthetic and is used ONLY for
# ML model development and benchmarking.
#
# Target:
#   recovered = 1  -> payment was eventually recovered
#   recovered = 0  -> payment remained unrecovered
# ---------------------------------------------------------

RANDOM_SEED = 42
N_SAMPLES = 10_000

rng = np.random.default_rng(RANDOM_SEED)

# ---------------------------------------------------------
# 1. Basic payment information
# ---------------------------------------------------------

amount = rng.lognormal(
    mean=np.log(5000),
    sigma=0.8,
    size=N_SAMPLES
)

amount = np.clip(amount, 300, 50_000)
amount = np.round(amount, 2)

failure_reasons = [
    "insufficient_funds",
    "card_declined",
    "network_error",
    "expired_card",
]

failure_reason = rng.choice(
    failure_reasons,
    size=N_SAMPLES,
    p=[0.35, 0.30, 0.20, 0.15],
)

payment_methods = [
    "card",
    "upi",
    "netbanking",
    "wallet",
]

payment_method = rng.choice(
    payment_methods,
    size=N_SAMPLES,
    p=[0.45, 0.30, 0.15, 0.10],
)

# ---------------------------------------------------------
# 2. Customer behaviour
# ---------------------------------------------------------

customer_success_rate = np.round(
    rng.beta(6, 2, size=N_SAMPLES),
    3,
)

previous_attempts = rng.choice(
    [0, 1, 2, 3, 4],
    size=N_SAMPLES,
    p=[0.35, 0.30, 0.20, 0.10, 0.05],
)

hours_since_failure = np.round(
    rng.exponential(
        scale=18,
        size=N_SAMPLES
    ),
    2,
)

hours_since_failure = np.clip(
    hours_since_failure,
    0.25,
    96
)

# ---------------------------------------------------------
# 3. Recovery intervention
# ---------------------------------------------------------

interventions = [
    "retry_now",
    "retry_later",
    "request_alternative_payment",
    "request_card_update",
]

intervention = rng.choice(
    interventions,
    size=N_SAMPLES,
)

# ---------------------------------------------------------
# 4. Generate a realistic recovery tendency
# ---------------------------------------------------------

recovery_score = np.full(
    N_SAMPLES,
    -0.30
)

# Customer history
recovery_score += (
    2.00 * (customer_success_rate - 0.70)
)

# Previous failed attempts
recovery_score -= (
    0.28 * previous_attempts
)

# Time decay
recovery_score -= (
    0.012 * hours_since_failure
)

# Amount effect
# Higher-value payments are slightly harder to recover
recovery_score -= (
    0.000012 * amount
)

# ---------------------------------------------------------
# Failure reason effects
# ---------------------------------------------------------

recovery_score += np.where(
    failure_reason == "network_error",
    0.80,
    0
)

recovery_score += np.where(
    failure_reason == "insufficient_funds",
    0.25,
    0
)

recovery_score += np.where(
    failure_reason == "card_declined",
    -0.25,
    0
)

recovery_score += np.where(
    failure_reason == "expired_card",
    -0.45,
    0
)

# ---------------------------------------------------------
# Payment method effects
# ---------------------------------------------------------

recovery_score += np.where(
    payment_method == "upi",
    0.18,
    0
)

recovery_score += np.where(
    payment_method == "netbanking",
    0.05,
    0
)

recovery_score += np.where(
    payment_method == "wallet",
    0.10,
    0
)

# ---------------------------------------------------------
# Intervention effects
# ---------------------------------------------------------

recovery_score += np.where(
    intervention == "retry_now",
    0.18,
    0
)

recovery_score += np.where(
    intervention == "retry_later",
    0.30,
    0
)

recovery_score += np.where(
    intervention == "request_alternative_payment",
    0.42,
    0
)

recovery_score += np.where(
    intervention == "request_card_update",
    0.35,
    0
)

# ---------------------------------------------------------
# Add random real-world-like noise
# ---------------------------------------------------------

noise = rng.normal(
    loc=0,
    scale=0.75,
    size=N_SAMPLES
)

recovery_score += noise

# Convert score to probability
recovery_probability = (
    1 / (1 + np.exp(-recovery_score))
)

# Keep probabilities away from absolute 0/1
recovery_probability = np.clip(
    recovery_probability,
    0.03,
    0.97
)

# ---------------------------------------------------------
# 5. Actual recovery outcome
# ---------------------------------------------------------

recovered = rng.binomial(
    n=1,
    p=recovery_probability
)

# ---------------------------------------------------------
# 6. Recovered amount
# ---------------------------------------------------------

recovered_amount = np.where(
    recovered == 1,
    amount,
    0
)

# ---------------------------------------------------------
# 7. Build dataframe
# ---------------------------------------------------------

df = pd.DataFrame(
    {
        "amount": amount,
        "failure_reason": failure_reason,
        "payment_method": payment_method,
        "customer_success_rate": customer_success_rate,
        "previous_attempts": previous_attempts,
        "hours_since_failure": hours_since_failure,
        "intervention": intervention,
        "recovered": recovered,
        "recovered_amount": recovered_amount,
    }
)

# ---------------------------------------------------------
# 8. Save dataset
# ---------------------------------------------------------

output_path = "recovery_training_data.csv"

df.to_csv(
    output_path,
    index=False
)

# ---------------------------------------------------------
# 9. Dataset summary
# ---------------------------------------------------------

print("=" * 60)
print("AgentReady - Synthetic Recovery Dataset")
print("=" * 60)

print(f"Rows: {len(df):,}")
print(f"Columns: {len(df.columns)}")

print(
    f"Recovery rate: "
    f"{df['recovered'].mean():.2%}"
)

print(
    f"Total payment value: "
    f"₹{df['amount'].sum():,.2f}"
)

print(
    f"Recovered value: "
    f"₹{df['recovered_amount'].sum():,.2f}"
)

print()
print("Failure reason distribution:")
print(
    df["failure_reason"]
    .value_counts()
)

print()
print("Intervention distribution:")
print(
    df["intervention"]
    .value_counts()
)

print()
print("Dataset saved to:")
print(output_path)

print("=" * 60)