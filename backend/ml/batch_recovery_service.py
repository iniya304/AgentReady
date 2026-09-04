from __future__ import annotations

from typing import Any

from app.supabase_client import supabase
from ml.recovery_context import get_payment_context
from ml.intervention_optimizer import optimize_intervention
from ml.policy_engine import evaluate_policy


def get_failed_payments() -> list[dict[str, Any]]:
    """
    Fetch all failed payments from Supabase.
    """

    response = (
        supabase
        .table("payments")
        .select("*")
        .eq("payment_status", "failed")
        .order("created_at", desc=True)
        .execute()
    )

    return response.data or []


def analyze_batch_recovery() -> dict[str, Any]:
    """
    Analyze every failed payment and calculate:

    - best recovery intervention
    - model-estimated recovery probability
    - expected recovery value
    - policy decision
    - portfolio-level recovery opportunity
    """

    payments = get_failed_payments()

    results: list[dict[str, Any]] = []

    total_revenue_at_risk = 0.0
    total_expected_recovery = 0.0
    auto_recovery_count = 0
    human_review_count = 0

    for payment in payments:

        payment_id = str(payment["id"])
        amount = float(payment["amount"])

        try:
            # Build customer + payment context.
            context = get_payment_context(
                payment_id=payment_id,
                intervention="retry_later",
            )

            # Evaluate every supported intervention.
            optimization = optimize_intervention(context)

            # Apply recovery policy.
            policy = evaluate_policy(
                payment_context=context,
                optimization=optimization,
            )

            expected_recovery_value = float(
                optimization["expected_recovery_value"]
            )

            total_revenue_at_risk += amount
            total_expected_recovery += expected_recovery_value

            if policy["decision"] == "AUTO_EXECUTE":
                auto_recovery_count += 1
            else:
                human_review_count += 1

            results.append(
                {
                    "payment_id": payment_id,
                    "customer_id": payment.get("customer_id"),
                    "amount": amount,
                    "currency": payment.get("currency", "INR"),
                    "failure_reason": payment.get("failure_reason"),
                    "payment_method": payment.get("payment_method"),
                    "recommended_intervention": optimization[
                        "recommended_intervention"
                    ],
                    "recovery_probability": optimization[
                        "recommended_probability"
                    ],
                    "recovery_probability_percent": optimization[
                        "recommended_probability_percent"
                    ],
                    "expected_recovery_value": expected_recovery_value,
                    "policy_decision": policy["decision"],
                    "requires_human_review": policy[
                        "requires_human_review"
                    ],
                    "policy_reasons": policy["policy_reasons"],
                }
            )

        except Exception as exc:
            results.append(
                {
                    "payment_id": payment_id,
                    "customer_id": payment.get("customer_id"),
                    "amount": amount,
                    "currency": payment.get("currency", "INR"),
                    "failure_reason": payment.get("failure_reason"),
                    "payment_method": payment.get("payment_method"),
                    "error": str(exc),
                    "policy_decision": "ERROR",
                }
            )

            total_revenue_at_risk += amount

    payment_count = len(payments)

    average_probability = (
        sum(
            item.get("recovery_probability", 0)
            for item in results
            if "recovery_probability" in item
        )
        / max(
            1,
            sum(
                1
                for item in results
                if "recovery_probability" in item
            ),
        )
    )

    recovery_opportunity_rate = (
        total_expected_recovery / total_revenue_at_risk
        if total_revenue_at_risk > 0
        else 0.0
    )

    return {
        "payment_count": payment_count,
        "total_revenue_at_risk": round(
            total_revenue_at_risk,
            2,
        ),
        "total_expected_recovery": round(
            total_expected_recovery,
            2,
        ),
        "recovery_opportunity_rate": round(
            recovery_opportunity_rate,
            4,
        ),
        "recovery_opportunity_percent": round(
            recovery_opportunity_rate * 100,
            2,
        ),
        "average_recovery_probability": round(
            average_probability,
            4,
        ),
        "average_recovery_probability_percent": round(
            average_probability * 100,
            2,
        ),
        "auto_recovery_count": auto_recovery_count,
        "human_review_count": human_review_count,
        "results": results,
    }
