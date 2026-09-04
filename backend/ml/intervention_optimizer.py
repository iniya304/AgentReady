from __future__ import annotations

from typing import Any

from ml.prediction_service import predict_recovery


INTERVENTIONS = [
    "retry_now",
    "retry_later",
    "request_alternative_payment",
    "request_card_update",
]


def optimize_intervention(
    payment_context: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate all supported recovery interventions and select
    the intervention with the highest model-estimated
    Expected Recovery Value (ERV).

    ERV = payment amount × recovery probability
    """

    amount = float(payment_context["amount"])

    candidates = []

    for intervention in INTERVENTIONS:
        context = {
            **payment_context,
            "intervention": intervention,
        }

        prediction = predict_recovery(context)

        probability = float(
            prediction["recovery_probability"]
        )

        expected_recovery_value = (
            amount * probability
        )

        candidates.append(
            {
                "intervention": intervention,
                "recovery_probability": round(
                    probability,
                    4,
                ),
                "recovery_probability_percent": round(
                    probability * 100,
                    2,
                ),
                "expected_recovery_value": round(
                    expected_recovery_value,
                    2,
                ),
            }
        )

    candidates.sort(
        key=lambda item: item["expected_recovery_value"],
        reverse=True,
    )

    best = candidates[0]

    return {
        "recommended_intervention": best["intervention"],
        "recommended_probability": best[
            "recovery_probability"
        ],
        "recommended_probability_percent": best[
            "recovery_probability_percent"
        ],
        "expected_recovery_value": best[
            "expected_recovery_value"
        ],
        "candidates": candidates,
    }

    