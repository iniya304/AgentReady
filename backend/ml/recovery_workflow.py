from __future__ import annotations

from typing import Any

MAX_RECOVERY_ATTEMPTS = 2

RECOVERY_SEQUENCE = [
    "retry_later",
    "request_alternative_payment",
    "request_card_update",
]


def get_next_intervention(
    previous_attempts: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Determine the next recovery intervention using stopping rules.

    Rules:
    1. If any previous attempt succeeded -> STOP.
    2. If an attempt is already pending -> return the existing attempt.
    3. If maximum attempts have been reached -> HUMAN_REVIEW.
    4. Otherwise select the next unused intervention.
    """

    # ---------------------------------------------------------
    # RULE 1: Stop if recovery has already succeeded
    # ---------------------------------------------------------
    for attempt in previous_attempts:
        if attempt.get("status") == "success":
            return {
                "decision": "STOP",
                "reason": "Recovery already succeeded",
                "next_intervention": None,
                "attempt_number": attempt.get("attempt_number"),
            }

    # ---------------------------------------------------------
    # RULE 2: Do not create duplicate pending attempts
    # ---------------------------------------------------------
    pending_attempts = [
        attempt
        for attempt in previous_attempts
        if attempt.get("status") == "pending"
    ]

    if pending_attempts:
        existing_attempt = pending_attempts[-1]

        return {
            "decision": "PENDING",
            "reason": "A recovery attempt is already pending",
            "next_intervention": existing_attempt.get("intervention"),
            "attempt_number": existing_attempt.get("attempt_number"),
        }

    # ---------------------------------------------------------
    # RULE 3: Stop after maximum recovery attempts
    # ---------------------------------------------------------
    if len(previous_attempts) >= MAX_RECOVERY_ATTEMPTS:
        return {
            "decision": "HUMAN_REVIEW",
            "reason": "Maximum recovery attempts reached",
            "next_intervention": None,
            "attempt_number": len(previous_attempts),
        }

    # ---------------------------------------------------------
    # RULE 4: Select next unused intervention
    # ---------------------------------------------------------
    used_interventions = {
        attempt.get("intervention")
        for attempt in previous_attempts
    }

    for intervention in RECOVERY_SEQUENCE:
        if intervention not in used_interventions:
            return {
                "decision": "CONTINUE",
                "reason": "Recovery attempt available",
                "next_intervention": intervention,
                "attempt_number": len(previous_attempts) + 1,
            }

    # ---------------------------------------------------------
    # FALLBACK
    # ---------------------------------------------------------
    return {
        "decision": "HUMAN_REVIEW",
        "reason": "No unused recovery intervention remains",
        "next_intervention": None,
        "attempt_number": len(previous_attempts),
    }
