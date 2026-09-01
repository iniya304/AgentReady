from typing import Any


def calculate_priority(
    amount: float,
    failure_reason: str | None,
    confidence: float,
) -> dict[str, Any]:
    """
    Calculate recovery priority using payment value,
    failure type, and agent confidence.
    """

    score = 0

    # Higher-value payments deserve faster attention.
    if amount >= 10000:
        score += 40
    elif amount >= 5000:
        score += 30
    elif amount >= 1000:
        score += 20
    else:
        score += 10

    # Some failures are more recoverable than others.
    failure_weights = {
        "network_error": 30,
        "insufficient_funds": 25,
        "card_declined": 20,
        "expired_card": 15,
    }

    score += failure_weights.get(failure_reason, 10)

    # High-confidence recommendations get a small boost.
    score += round(confidence * 20)

    if score >= 75:
        priority = "high"
    elif score >= 50:
        priority = "medium"
    else:
        priority = "low"

    return {
        "priority": priority,
        "priority_score": min(score, 100),
    }


def analyze_payment(payment: dict[str, Any]) -> dict[str, Any]:
    """
    Analyze a failed payment and recommend a recovery strategy.
    """

    failure_reason = payment.get("failure_reason")
    amount = float(payment.get("amount", 0))

    strategies = {
        "insufficient_funds": {
            "strategy": "retry_later",
            "reason": (
                "The payment appears to have failed because the customer "
                "may not have sufficient funds."
            ),
            "recommended_delay_hours": 24,
            "confidence": 0.87,
        },
        "card_declined": {
            "strategy": "request_alternative_payment",
            "reason": (
                "The card was declined, so requesting another payment "
                "method is recommended."
            ),
            "recommended_delay_hours": 0,
            "confidence": 0.91,
        },
        "network_error": {
            "strategy": "retry_now",
            "reason": (
                "A temporary network issue may have interrupted the payment."
            ),
            "recommended_delay_hours": 0,
            "confidence": 0.94,
        },
        "expired_card": {
            "strategy": "request_card_update",
            "reason": (
                "The customer's card appears to be expired."
            ),
            "recommended_delay_hours": 0,
            "confidence": 0.98,
        },
    }

    recommendation = strategies.get(
        failure_reason,
        {
            "strategy": "manual_review",
            "reason": (
                "The failure reason is not recognized, so manual review "
                "is recommended."
            ),
            "recommended_delay_hours": 0,
            "confidence": 0.50,
        },
    )

    priority = calculate_priority(
        amount=amount,
        failure_reason=failure_reason,
        confidence=recommendation["confidence"],
    )

    return {
        "payment_id": payment.get("id"),
        "customer_id": payment.get("customer_id"),
        "amount": amount,
        "failure_reason": failure_reason,
        **recommendation,
        **priority,
    }