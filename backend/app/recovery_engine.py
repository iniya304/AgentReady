from typing import Any


def analyze_payment(payment: dict[str, Any]) -> dict[str, Any]:
    """
    Analyze a failed payment and recommend a recovery strategy.
    """

    failure_reason = payment.get("failure_reason")
    amount = float(payment.get("amount", 0))

    strategies = {
        "insufficient_funds": {
            "strategy": "retry_later",
            "reason": "The payment appears to have failed because the customer may not have sufficient funds.",
            "recommended_delay_hours": 24,
            "confidence": 0.87,
        },
        "card_declined": {
            "strategy": "request_alternative_payment",
            "reason": "The card was declined, so requesting another payment method is recommended.",
            "recommended_delay_hours": 0,
            "confidence": 0.91,
        },
        "network_error": {
            "strategy": "retry_now",
            "reason": "A temporary network issue may have interrupted the payment.",
            "recommended_delay_hours": 0,
            "confidence": 0.94,
        },
        "expired_card": {
            "strategy": "request_card_update",
            "reason": "The customer's card appears to be expired.",
            "recommended_delay_hours": 0,
            "confidence": 0.98,
        },
    }

    recommendation = strategies.get(
        failure_reason,
        {
            "strategy": "manual_review",
            "reason": "The failure reason is not recognized, so manual review is recommended.",
            "recommended_delay_hours": 0,
            "confidence": 0.50,
        },
    )

    return {
        "payment_id": payment.get("id"),
        "customer_id": payment.get("customer_id"),
        "amount": amount,
        "failure_reason": failure_reason,
        **recommendation,
    }

