from __future__ import annotations

from typing import Any

from app.supabase_client import supabase


def get_payment_context(
    payment_id: str,
    intervention: str,
) -> dict[str, Any]:
    """
    Fetch a failed payment and its customer recovery profile
    from Supabase and construct the ML input context.
    """

    # ---------------------------------------------------------
    # 1. Fetch payment
    # ---------------------------------------------------------

    payment_response = (
        supabase
        .table("payments")
        .select("*")
        .eq("id", payment_id)
        .limit(1)
        .execute()
    )

    if not payment_response.data:
        raise ValueError("Payment not found")

    payment = payment_response.data[0]

    # ---------------------------------------------------------
    # 2. Fetch customer recovery profile
    # ---------------------------------------------------------

    customer_id = payment["customer_id"]

    profile_response = (
        supabase
        .table("customer_recovery_profiles")
        .select("*")
        .eq("customer_id", customer_id)
        .limit(1)
        .execute()
    )

    if not profile_response.data:
        raise ValueError(
            f"Customer recovery profile not found for {customer_id}"
        )

    profile = profile_response.data[0]

    # ---------------------------------------------------------
    # 3. Extract payment timestamp
    # ---------------------------------------------------------

    created_at = payment.get("created_at")

    if created_at:
        try:
            payment_hour = int(
                created_at[11:13]
            )
        except (ValueError, TypeError):
            payment_hour = 12
    else:
        payment_hour = 12

    # ---------------------------------------------------------
    # 4. Build ML context
    # ---------------------------------------------------------

    context = {
        "amount": float(payment["amount"]),
        "failure_reason": payment.get("failure_reason"),
        "payment_method": payment.get(
            "payment_method",
            "card",
        ),

        "customer_success_rate": float(
            profile["customer_success_rate"]
        ),

        "customer_tenure_days": int(
            profile["customer_tenure_days"]
        ),

        "historical_payments": int(
            profile["historical_payments"]
        ),

        "historical_failed_payments": int(
            profile["historical_failed_payments"]
        ),

        "historical_recovered_payments": int(
            profile["historical_recovered_payments"]
        ),

        "historical_recovery_rate": float(
            profile["historical_recovery_rate"]
        ),

        "days_since_last_success": int(
            profile["days_since_last_success"]
        ),

        "previous_attempts": int(
            profile["previous_attempts"]
        ),

        "hours_since_failure": 24,

        "payment_hour": payment_hour,

        "previous_recovery_attempts": int(
            profile["previous_recovery_attempts"]
        ),

        "previous_recovery_success": int(
            profile["previous_recovery_success"]
        ),

        "customer_recovery_history": float(
            profile["customer_recovery_history"]
        ),

        # The model predicts recovery conditional
        # on the selected intervention.
        "intervention": intervention,
    }

    return context
    