from typing import Any

from app.supabase_client import supabase


def log_audit_event(
    event_type: str,
    payment_id: str | None = None,
    actor: str = "AgentReady",
    decision: str | None = None,
    intervention: str | None = None,
    status: str | None = None,
    reason: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """
    Persist an AgentReady decision/outcome event.

    Audit logging is intentionally fail-safe:
    if the audit write fails, the main recovery workflow
    should continue operating.
    """

    try:
        event = {
            "payment_id": payment_id,
            "event_type": event_type,
            "actor": actor,
            "decision": decision,
            "intervention": intervention,
            "status": status,
            "reason": reason,
            "metadata": metadata or {},
        }

        response = (
            supabase
            .table("audit_events")
            .insert(event)
            .execute()
        )

        if response.data:
            return response.data[0]

        return None

    except Exception as exc:
        print("========== AUDIT LOGGING ERROR ==========")
        print("EVENT TYPE:", event_type)
        print("PAYMENT ID:", payment_id)
        print("ERROR TYPE:", type(exc).__name__)
        print("ERROR:", repr(exc))
        print("AUDIT FAILURE IGNORED — MAIN WORKFLOW CONTINUES")
        print("==========================================")

        return None


def get_audit_events(
    payment_id: str | None = None,
) -> list[dict[str, Any]]:
    """
    Retrieve audit events.

    If payment_id is provided, only events for that payment
    are returned. Otherwise the complete audit trail is returned.
    """

    try:
        query = (
            supabase
            .table("audit_events")
            .select("*")
            .order("created_at", desc=True)
        )

        if payment_id:
            query = query.eq("payment_id", payment_id)

        response = query.execute()

        return response.data or []

    except Exception as exc:
        print("========== AUDIT READ ERROR ==========")
        print("ERROR TYPE:", type(exc).__name__)
        print("ERROR:", repr(exc))
        print("======================================")

        raise
