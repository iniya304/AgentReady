from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


MODEL_INPUT_COLUMNS = [
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
]


def build_features(
    data: dict[str, Any] | pd.DataFrame,
) -> pd.DataFrame:
    """
    Build the exact 38 raw/engineered features used by the
    final AgentReady recovery model.

    IMPORTANT:
    This logic intentionally mirrors save_final_model.py.
    Do not modify feature calculations independently in the
    backend inference layer.
    """

    if isinstance(data, dict):
        df = pd.DataFrame([data])
    else:
        df = data.copy()

    # ========================================================
    # AMOUNT
    # ========================================================

    df["log_amount"] = np.log1p(df["amount"])

    df["high_value_flag"] = (
        df["amount"] >= 10000
    ).astype(int)

    df["amount_band"] = pd.cut(
        df["amount"],
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

    # ========================================================
    # CUSTOMER HISTORY
    # ========================================================

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

    # ========================================================
    # ATTEMPTS
    # ========================================================

    df["attempt_pressure"] = (
        df["previous_attempts"]
        + df["previous_recovery_attempts"]
    )

    df["recovery_attempt_pressure"] = (
        df["previous_recovery_attempts"]
        + 1
    )

    df["no_previous_attempt"] = (
        df["previous_attempts"] == 0
    ).astype(int)

    df["multiple_attempt_flag"] = (
        df["previous_attempts"] >= 2
    ).astype(int)

    # ========================================================
    # RECENCY
    # ========================================================

    df["recent_failure_flag"] = (
        df["hours_since_failure"] <= 6
    ).astype(int)

    df["stale_failure_flag"] = (
        df["hours_since_failure"] >= 48
    ).astype(int)

    df["recency_risk"] = np.log1p(
        df["days_since_last_success"]
    )

    # ========================================================
    # TIME
    # ========================================================

    df["business_hours_flag"] = (
        df["payment_hour"].between(9, 18)
    ).astype(int)

    df["late_night_flag"] = (
        (df["payment_hour"] < 6)
        | (df["payment_hour"] >= 23)
    ).astype(int)

    # ========================================================
    # INTERACTIONS
    # ========================================================

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
            bins=[
                -np.inf,
                0.3,
                0.6,
                np.inf,
            ],
            labels=[
                "low",
                "medium",
                "high",
            ],
        ).astype(str)
        + "_"
        + df["previous_attempts"].astype(str)
    )

    df["intervention_strength"] = (
        df["intervention"]
        .map(
            {
                "retry_now": 1,
                "retry_later": 2,
                "request_alternative_payment": 3,
                "request_card_update": 3,
            }
        )
        .fillna(0)
    )

    return df

