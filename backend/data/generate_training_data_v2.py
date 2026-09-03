from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# AgentReady - Synthetic Recovery Dataset V2
# ============================================================

RANDOM_SEED = 42
N_SAMPLES = 15_000

rng = np.random.default_rng(RANDOM_SEED)

OUTPUT_PATH = (
    Path(__file__).resolve().parent
    / "recovery_training_data_v2.csv"
)


# ============================================================
# 1. PAYMENT FEATURES
# ============================================================

amount = rng.lognormal(
    mean=np.log(5000),
    sigma=0.8,
    size=N_SAMPLES,
)

amount = np.clip(
    amount,
    300,
    50_000,
)

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


# ============================================================
# 2. CUSTOMER HISTORY
# ============================================================

customer_success_rate = np.round(
    rng.beta(
        7,
        2,
        size=N_SAMPLES,
    ),
    3,
)


customer_tenure_days = rng.gamma(
    shape=4,
    scale=120,
    size=N_SAMPLES,
)

customer_tenure_days = np.clip(
    customer_tenure_days,
    7,
    1500,
).astype(int)


historical_payments = rng.poisson(
    lam=18,
    size=N_SAMPLES,
)

historical_payments = np.clip(
    historical_payments,
    1,
    100,
)


historical_failed_payments = rng.binomial(
    historical_payments,
    1 - customer_success_rate,
)


historical_recovered_payments = rng.binomial(
    historical_failed_payments,
    np.clip(
        customer_success_rate + 0.05,
        0.05,
        0.98,
    ),
)


days_since_last_success = rng.exponential(
    scale=25,
    size=N_SAMPLES,
)

days_since_last_success = np.clip(
    days_since_last_success,
    0.5,
    180,
)

days_since_last_success = np.round(
    days_since_last_success,
    2,
)


# ============================================================
# 3. CURRENT PAYMENT HISTORY
# ============================================================

previous_attempts = rng.choice(
    [0, 1, 2, 3, 4],
    size=N_SAMPLES,
    p=[0.40, 0.30, 0.18, 0.08, 0.04],
)


hours_since_failure = rng.exponential(
    scale=18,
    size=N_SAMPLES,
)

hours_since_failure = np.clip(
    hours_since_failure,
    0.25,
    96,
)

hours_since_failure = np.round(
    hours_since_failure,
    2,
)


# ============================================================
# 4. PAYMENT TIMING
# ============================================================

payment_hour = rng.integers(
    0,
    24,
    size=N_SAMPLES,
)


# ============================================================
# 5. CANDIDATE INTERVENTION
# ============================================================

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


# ============================================================
# 6. PREVIOUS RECOVERY EXPERIENCE
# ============================================================

previous_recovery_attempts = rng.poisson(
    lam=1.2,
    size=N_SAMPLES,
)

previous_recovery_attempts = np.clip(
    previous_recovery_attempts,
    0,
    6,
)


previous_recovery_success = np.where(
    previous_recovery_attempts > 0,
    rng.binomial(
        previous_recovery_attempts,
        np.clip(
            customer_success_rate,
            0.05,
            0.95,
        ),
    ),
    0,
)


# ============================================================
# 7. DERIVED CUSTOMER SIGNALS
# ============================================================

customer_recovery_history = np.divide(
    previous_recovery_success,
    previous_recovery_attempts,
    out=np.zeros(N_SAMPLES),
    where=previous_recovery_attempts > 0,
)


historical_recovery_rate = np.divide(
    historical_recovered_payments,
    historical_failed_payments,
    out=np.zeros(N_SAMPLES),
    where=historical_failed_payments > 0,
)


# ============================================================
# 8. GENERATE RECOVERY SIGNAL
# ============================================================

recovery_score = np.full(
    N_SAMPLES,
    -0.75,
)


# Customer reliability

recovery_score += (
    2.5
    * (customer_success_rate - 0.70)
)


# Historical recovery behaviour

recovery_score += (
    1.4
    * historical_recovery_rate
)


recovery_score += (
    1.2
    * customer_recovery_history
)


# Customer tenure

recovery_score += np.where(
    customer_tenure_days >= 365,
    0.30,
    0,
)


# Payment amount

recovery_score -= (
    0.000015
    * amount
)


# Previous attempts

recovery_score -= (
    0.30
    * previous_attempts
)


# Time since failure

recovery_score -= (
    0.015
    * hours_since_failure
)


# Time since customer's last successful payment

recovery_score -= (
    0.004
    * days_since_last_success
)


# ============================================================
# 9. FAILURE REASON EFFECT
# ============================================================

recovery_score += np.where(
    failure_reason == "network_error",
    0.95,
    0,
)

recovery_score += np.where(
    failure_reason == "insufficient_funds",
    0.30,
    0,
)

recovery_score += np.where(
    failure_reason == "card_declined",
    -0.30,
    0,
)

recovery_score += np.where(
    failure_reason == "expired_card",
    -0.55,
    0,
)


# ============================================================
# 10. PAYMENT METHOD EFFECT
# ============================================================

recovery_score += np.where(
    payment_method == "upi",
    0.18,
    0,
)

recovery_score += np.where(
    payment_method == "netbanking",
    0.10,
    0,
)

recovery_score += np.where(
    payment_method == "wallet",
    0.05,
    0,
)


# ============================================================
# 11. PAYMENT HOUR EFFECT
# ============================================================

# Daytime payments receive a small positive signal.

daytime_payment = (
    (payment_hour >= 8)
    & (payment_hour <= 21)
)

recovery_score += np.where(
    daytime_payment,
    0.12,
    -0.08,
)


# ============================================================
# 12. INTERVENTION EFFECT
# ============================================================

recovery_score += np.where(
    intervention == "retry_now",
    0.15,
    0,
)

recovery_score += np.where(
    intervention == "retry_later",
    0.30,
    0,
)

recovery_score += np.where(
    intervention == "request_alternative_payment",
    0.45,
    0,
)

recovery_score += np.where(
    intervention == "request_card_update",
    0.38,
    0,
)


# ============================================================
# 13. INTERACTION EFFECTS
# ============================================================

# Network errors respond particularly well to immediate retry.

recovery_score += np.where(
    (
        (failure_reason == "network_error")
        & (intervention == "retry_now")
    ),
    0.45,
    0,
)


# Insufficient funds respond better to delayed retry.

recovery_score += np.where(
    (
        (failure_reason == "insufficient_funds")
        & (intervention == "retry_later")
    ),
    0.40,
    0,
)


# Card declines respond better to alternative payment.

recovery_score += np.where(
    (
        (failure_reason == "card_declined")
        & (
            intervention
            == "request_alternative_payment"
        )
    ),
    0.50,
    0,
)


# Expired cards respond better to card updates.

recovery_score += np.where(
    (
        (failure_reason == "expired_card")
        & (
            intervention
            == "request_card_update"
        )
    ),
    0.55,
    0,
)


# Strong customers with fewer previous attempts
# are more recoverable.

recovery_score += np.where(
    (
        (customer_success_rate >= 0.80)
        & (previous_attempts <= 1)
    ),
    0.35,
    0,
)


# ============================================================
# 14. REALISTIC RANDOMNESS
# ============================================================

noise = rng.normal(
    loc=0,
    scale=0.45,
    size=N_SAMPLES,
)

recovery_score += noise


# ============================================================
# 15. CONVERT SCORE → PROBABILITY
# ============================================================

recovery_probability = (
    1
    / (
        1
        + np.exp(
            -recovery_score
        )
    )
)


recovery_probability = np.clip(
    recovery_probability,
    0.03,
    0.97,
)


# ============================================================
# 16. GENERATE OUTCOME
# ============================================================

recovered = rng.binomial(
    n=1,
    p=recovery_probability,
)


# ============================================================
# 17. RECOVERED AMOUNT
# ============================================================

recovered_amount = np.where(
    recovered == 1,
    amount,
    0,
)


# ============================================================
# 18. BUILD DATAFRAME
# ============================================================

df = pd.DataFrame(
    {
        "amount": amount,
        "failure_reason": failure_reason,
        "payment_method": payment_method,

        "customer_success_rate":
            customer_success_rate,

        "customer_tenure_days":
            customer_tenure_days,

        "historical_payments":
            historical_payments,

        "historical_failed_payments":
            historical_failed_payments,

        "historical_recovered_payments":
            historical_recovered_payments,

        "historical_recovery_rate":
            historical_recovery_rate,

        "days_since_last_success":
            days_since_last_success,

        "previous_attempts":
            previous_attempts,

        "hours_since_failure":
            hours_since_failure,

        "payment_hour":
            payment_hour,

        "previous_recovery_attempts":
            previous_recovery_attempts,

        "previous_recovery_success":
            previous_recovery_success,

        "customer_recovery_history":
            customer_recovery_history,

        "intervention":
            intervention,

        "recovered":
            recovered,

        "recovered_amount":
            recovered_amount,
    }
)


# ============================================================
# 19. DATASET VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("DATASET SUMMARY")
print("=" * 70)

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

print(
    f"Missing values: "
    f"{df.isna().sum().sum()}"
)

print(
    f"Duplicate rows: "
    f"{df.duplicated().sum()}"
)


print("\nRecovery by failure reason:")

print(
    df.groupby("failure_reason")[
        "recovered"
    ].mean().sort_values(
        ascending=False
    )
)


print("\nRecovery by intervention:")

print(
    df.groupby("intervention")[
        "recovered"
    ].mean().sort_values(
        ascending=False
    )
)


# ============================================================
# 20. SAVE DATASET
# ============================================================

df.to_csv(
    OUTPUT_PATH,
    index=False,
)


print("\n" + "=" * 70)
print("V2 DATASET CREATED")
print("=" * 70)

print(f"Saved to:\n{OUTPUT_PATH}")

print("=" * 70)