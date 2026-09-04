from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.supabase_client import supabase


def get_recovery_attempts(payment_id: str) -> list[dict[str, Any]]:
    """
    Fetch all recovery attempts for a payment.
    """

    response = (
        supabase
        .table("recovery_attempts")
        .select("*")
        .eq("payment_id", payment_id)
        .order("attempt_number")
        .execute()
    )

    return response.data or []


def create_recovery_attempt(
    payment_id: str,
    attempt_number: int,
    intervention: str,
    recovery_action_id: str | None = None,
) -> dict[str, Any]:
    """
    Create a new pending recovery attempt.
    """

    payload = {
        "payment_id": payment_id,
        "attempt_number": attempt_number,
        "intervention": intervention,
        "status": "pending",
    }

    if recovery_action_id:
        payload["recovery_action_id"] = recovery_action_id

    response = (
        supabase
        .table("recovery_attempts")
        .insert(payload)
        .execute()
    )

    if not response.data:
        raise RuntimeError("Failed to create recovery attempt")

    return response.data[0]


def update_recovery_attempt(
    attempt_id: str,
    status: str,
    failure_reason: str | None = None,
) -> dict[str, Any]:
    """
    Complete a recovery attempt and record its outcome.
    """

    allowed_statuses = {"success", "failed"}

    if status not in allowed_statuses:
        raise ValueError(
            f"Invalid status '{status}'. "
            f"Allowed values: {sorted(allowed_statuses)}"
        )

    payload: dict[str, Any] = {
        "status": status,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }

    if failure_reason:
        payload["failure_reason"] = failure_reason

    response = (
        supabase
        .table("recovery_attempts")
        .update(payload)
        .eq("id", attempt_id)
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            "Recovery attempt not found or could not be updated"
        )

    return response.data[0]
