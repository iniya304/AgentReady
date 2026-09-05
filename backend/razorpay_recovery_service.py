from __future__ import annotations

from typing import Any

from razorpay_client import razorpay_client


def create_recovery_payment_link(
    amount: float,
    customer_id: str,
    description: str,
) -> dict[str, Any]:
    """Create a Razorpay Test Mode payment link for a recovery action."""

    if amount <= 0:
        raise ValueError("Recovery amount must be greater than zero")

    payload = {
        "amount": int(round(amount * 100)),
        "currency": "INR",
        "description": description,
        "reference_id": f"agentready-{customer_id}",
        "expire_by": 0,
    }

    response = razorpay_client.payment_link.create(payload)

    return {
        "payment_link_id": response.get("id"),
        "short_url": response.get("short_url"),
        "status": response.get("status"),
        "amount": response.get("amount"),
        "currency": response.get("currency"),
    }