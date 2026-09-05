from __future__ import annotations

import hashlib
import time
from typing import Any

from razorpay_client import razorpay_client


def _build_reference_id(payment_id: str) -> str:
    """
    Build a deterministic Razorpay reference ID.

    Razorpay reference IDs have a length limit, so we use
    a short hash derived from the AgentReady payment ID.
    """
    digest = hashlib.sha256(payment_id.encode("utf-8")).hexdigest()[:28]
    return f"agentready-{digest}"


def create_recovery_payment_link(
    amount: float,
    customer_id: str,
    payment_id: str,
    description: str,
) -> dict[str, Any]:
    """
    Create a Razorpay Test Mode payment link for a recovery action.
    """

    if amount <= 0:
        raise ValueError("Recovery amount must be greater than zero")

    if not payment_id:
        raise ValueError("Payment ID is required")

    reference_id = _build_reference_id(payment_id)

    payload = {
        "amount": int(round(amount * 100)),
        "currency": "INR",
        "description": description,
        "reference_id": reference_id,
        "expire_by": int(time.time()) + (24 * 60 * 60),
        "reminder_enable": False,
        "notes": {
            "agentready_payment_id": payment_id,
            "agentready_customer_id": customer_id,
        },
    }

    response = razorpay_client.payment_link.create(payload)

    return {
        "payment_link_id": response.get("id"),
        "short_url": response.get("short_url"),
        "status": response.get("status"),
        "amount": response.get("amount"),
        "currency": response.get("currency"),
        "reference_id": response.get("reference_id"),
    }


def fetch_recovery_payment_link(
    payment_link_id: str,
) -> dict[str, Any]:
    """
    Fetch the current status of a Razorpay Payment Link.
    """

    if not payment_link_id:
        raise ValueError("Payment link ID is required")

    response = razorpay_client.payment_link.fetch(payment_link_id)

    return {
        "payment_link_id": response.get("id"),
        "short_url": response.get("short_url"),
        "status": response.get("status"),
        "amount": response.get("amount"),
        "currency": response.get("currency"),
        "reference_id": response.get("reference_id"),
    }