from __future__ import annotations

from typing import Any


MAX_AUTO_RECOVERY_AMOUNT = 15000
MIN_AUTO_RECOVERY_PROBABILITY = 0.80
MAX_PREVIOUS_ATTEMPTS = 1
MAX_PREVIOUS_RECOVERY_ATTEMPTS = 1


def evaluate_policy(
    payment_context: dict[str, Any],
    optimization: dict[str, Any],
) -> dict[str, Any]:
    """
    Apply safety and business guardrails to the optimizer's
    recommended recovery intervention.

    The policy decides whether the recommendation can proceed
    automatically or requires human review.
    """

    amount = float(payment_context["amount"])

    previous_attempts = int(
        payment_context.get("previous_attempts", 0)
    )

    previous_recovery_attempts = int(
        payment_context.get(
            "previous_recovery_attempts",
            0,
        )
    )

    probability = float(
        optimization["recommended_probability"]
    )

    intervention = optimization[
        "recommended_intervention"
    ]

    reasons = []

    # Guardrail 1: payment amount
    if amount > MAX_AUTO_RECOVERY_AMOUNT:
        reasons.append(
            "Payment amount exceeds automatic recovery limit"
        )

    # Guardrail 2: model confidence
    if probability < MIN_AUTO_RECOVERY_PROBABILITY:
        reasons.append(
            "Recovery probability is below automatic execution threshold"
        )

    # Guardrail 3: repeated payment attempts
    if previous_attempts > MAX_PREVIOUS_ATTEMPTS:
        reasons.append(
            "Payment has already received too many retry attempts"
        )

    # Guardrail 4: repeated recovery attempts
    if (
        previous_recovery_attempts
        > MAX_PREVIOUS_RECOVERY_ATTEMPTS
    ):
        reasons.append(
            "Recovery workflow has already been attempted too many times"
        )

    # Final decision
    if reasons:
        decision = "HUMAN_REVIEW"
        auto_execute = False
    else:
        decision = "AUTO_EXECUTE"
        auto_execute = True

    return {
        "decision": decision,
        "auto_execute": auto_execute,
        "requires_human_review": not auto_execute,
        "recommended_intervention": intervention,
        "recovery_probability": round(
            probability,
            4,
        ),
        "policy_reasons": reasons,
        "policy_limits": {
            "max_auto_recovery_amount": MAX_AUTO_RECOVERY_AMOUNT,
            "min_auto_recovery_probability": MIN_AUTO_RECOVERY_PROBABILITY,
            "max_previous_attempts": MAX_PREVIOUS_ATTEMPTS,
            "max_previous_recovery_attempts": MAX_PREVIOUS_RECOVERY_ATTEMPTS,
        },
    }

    