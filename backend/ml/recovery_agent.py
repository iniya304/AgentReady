from __future__ import annotations

from typing import Any

from app.supabase_client import supabase
from ml.batch_recovery_service import analyze_batch_recovery
from ml.recovery_context import get_payment_context
from ml.intervention_optimizer import optimize_intervention
from ml.policy_engine import evaluate_policy


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def _get_failed_payments() -> list[dict[str, Any]]:
    response = (
        supabase
        .table("payments")
        .select("*")
        .eq("payment_status", "failed")
        .execute()
    )

    return response.data or []


def _find_payment(payment_reference: str) -> dict[str, Any] | None:
    payments = _get_failed_payments()

    reference = payment_reference.strip().lower()

    for payment in payments:
        payment_id = str(payment.get("id", "")).lower()
        customer_id = str(payment.get("customer_id", "")).lower()

        if reference == payment_id or reference == customer_id:
            return payment

    return None


def _format_currency(amount: float, currency: str = "INR") -> str:
    if currency == "INR":
        return f"₹{amount:,.0f}"

    return f"{currency} {amount:,.2f}"


# ---------------------------------------------------------
# Portfolio questions
# ---------------------------------------------------------

def answer_portfolio_question(question: str) -> dict[str, Any]:
    """
    Answer merchant-level revenue recovery questions using
    the existing AgentReady batch intelligence pipeline.
    """

    result = analyze_batch_recovery()

    normalized = question.lower()

    payments = result.get("results", [])

    # -----------------------------------------------------
    # Highest recovery opportunity
    # -----------------------------------------------------

    if (
        "prioritize" in normalized
        or "priority" in normalized
        or "highest" in normalized
        or "best payment" in normalized
        or "most worth" in normalized
    ):
        ranked = sorted(
            payments,
            key=lambda item: float(
                item.get("expected_recovery_value", 0)
            ),
            reverse=True,
        )

        top = ranked[:3]

        recommendations = []

        for item in top:
            recommendations.append(
                {
                    "payment_id": item.get("payment_id"),
                    "customer_id": item.get("customer_id"),
                    "amount": item.get("amount"),
                    "currency": item.get("currency"),
                    "failure_reason": item.get("failure_reason"),
                    "recommended_intervention": item.get(
                        "recommended_intervention"
                    ),
                    "recovery_probability": item.get(
                        "recovery_probability"
                    ),
                    "expected_recovery_value": item.get(
                        "expected_recovery_value"
                    ),
                    "policy_decision": item.get(
                        "policy_decision"
                    ),
                }
            )

        return {
            "intent": "prioritize_recovery",
            "answer": (
                f"I found {len(payments)} failed payments. "
                f"The highest-value recovery opportunities are "
                f"ranked using model-estimated recovery probability "
                f"and expected recovery value."
            ),
            "recommendations": recommendations,
            "source": "AgentReady recovery intelligence",
        }

    # -----------------------------------------------------
    # Revenue at risk
    # -----------------------------------------------------

    if (
        "revenue at risk" in normalized
        or "money at risk" in normalized
        or "at risk" in normalized
    ):
        return {
            "intent": "revenue_at_risk",
            "answer": (
                f"AgentReady currently identifies "
                f"{_format_currency(float(result.get('total_revenue_at_risk', 0)))} "
                f"of failed-payment value at risk."
            ),
            "metrics": {
                "payment_count": result.get("payment_count"),
                "total_revenue_at_risk": result.get(
                    "total_revenue_at_risk"
                ),
                "total_expected_recovery": result.get(
                    "total_expected_recovery"
                ),
                "recovery_opportunity_percent": result.get(
                    "recovery_opportunity_percent"
                ),
            },
            "source": "AgentReady batch recovery intelligence",
        }

    # -----------------------------------------------------
    # Human review
    # -----------------------------------------------------

    if (
        "human review" in normalized
        or "manual review" in normalized
        or "need review" in normalized
    ):
        human_review = [
            item
            for item in payments
            if str(item.get("policy_decision", "")).upper()
            in {"HUMAN_REVIEW", "REVIEW"}
        ]

        return {
            "intent": "human_review",
            "answer": (
                f"{len(human_review)} failed payments currently "
                f"require human review under AgentReady's policy guardrails."
            ),
            "payments": human_review,
            "source": "AgentReady policy engine",
        }

    # -----------------------------------------------------
    # Automatic recovery
    # -----------------------------------------------------

    if (
        "automatic" in normalized
        or "auto recover" in normalized
        or "auto-recover" in normalized
    ):
        auto_recovery = [
            item
            for item in payments
            if str(item.get("policy_decision", "")).upper()
            in {"AUTO_EXECUTE", "AUTO"}
        ]

        return {
            "intent": "automatic_recovery",
            "answer": (
                f"{len(auto_recovery)} failed payments are currently "
                f"eligible for automated recovery under the configured "
                f"policy guardrails."
            ),
            "payments": auto_recovery,
            "source": "AgentReady policy engine",
        }

    # -----------------------------------------------------
    # General portfolio summary
    # -----------------------------------------------------

    return {
        "intent": "portfolio_summary",
        "answer": (
            f"AgentReady analyzed {result.get('payment_count', 0)} "
            f"failed payments with "
            f"{_format_currency(float(result.get('total_revenue_at_risk', 0)))} "
            f"of revenue at risk and "
            f"{_format_currency(float(result.get('total_expected_recovery', 0)))} "
            f"of model-estimated expected recovery."
        ),
        "metrics": result,
        "source": "AgentReady recovery intelligence",
    }


# ---------------------------------------------------------
# Payment-specific questions
# ---------------------------------------------------------

def answer_payment_question(
    question: str,
    payment_reference: str,
) -> dict[str, Any]:
    """
    Answer questions about one specific failed payment.

    The reference can be either:
    - payment UUID
    - customer ID
    """

    payment = _find_payment(payment_reference)

    if not payment:
        raise ValueError(
            f"No failed payment found for '{payment_reference}'."
        )

    normalized = question.lower()

    # -----------------------------------------------------
    # Build candidate intervention intelligence
    # -----------------------------------------------------

    context = get_payment_context(
        payment_id=payment["id"],
        intervention="retry_later",
    )

    optimization = optimize_intervention(context)

    policy = evaluate_policy(
        payment_context=context,
        optimization=optimization,
    )

    # -----------------------------------------------------
    # Extract selected intervention
    # -----------------------------------------------------

    selected_intervention = (
        optimization.get("selected_intervention")
        or optimization.get("best_intervention")
        or optimization.get("recommended_intervention")
    )

    policy_decision = (
        policy.get("decision")
        or policy.get("action")
        or policy.get("policy_decision")
    )

    # -----------------------------------------------------
    # Recovery probability
    # -----------------------------------------------------

    probability = None

    ranked_interventions = (
        optimization.get("ranked_interventions")
        or optimization.get("interventions")
        or optimization.get("candidates")
        or []
    )

    for candidate in ranked_interventions:
        intervention_name = (
            candidate.get("intervention")
            or candidate.get("strategy")
            or candidate.get("action")
        )

        if intervention_name == selected_intervention:
            probability = (
                candidate.get("recovery_probability")
                or candidate.get("probability")
            )
            break

    # -----------------------------------------------------
    # "What should we do?"
    # -----------------------------------------------------

    if (
        "what should" in normalized
        or "recommend" in normalized
        or "intervention" in normalized
        or "recover" in normalized
    ):
        return {
            "intent": "payment_recommendation",
            "answer": (
                f"For {payment.get('customer_id')}, AgentReady recommends "
                f"{selected_intervention}. "
                f"The policy decision is {policy_decision}."
            ),
            "payment": payment,
            "optimization": optimization,
            "policy": policy,
            "recovery_probability": probability,
            "source": "AgentReady ML + intervention optimizer + policy engine",
        }

    # -----------------------------------------------------
    # "Why?"
    # -----------------------------------------------------

    if (
        "why" in normalized
        or "reason" in normalized
        or "explain" in normalized
    ):
        return {
            "intent": "payment_explanation",
            "answer": (
                f"The payment for {payment.get('customer_id')} failed "
                f"because of {payment.get('failure_reason')}. "
                f"AgentReady evaluated candidate recovery interventions "
                f"using the trained recovery model and then applied "
                f"policy guardrails. The resulting policy decision is "
                f"{policy_decision}."
            ),
            "payment": payment,
            "optimization": optimization,
            "policy": policy,
            "source": "AgentReady decision pipeline",
        }

    # -----------------------------------------------------
    # Default payment answer
    # -----------------------------------------------------

    return {
        "intent": "payment_summary",
        "answer": (
            f"{payment.get('customer_id')} has a failed payment of "
            f"{_format_currency(float(payment.get('amount', 0)), payment.get('currency', 'INR'))}. "
            f"The failure reason is {payment.get('failure_reason')}. "
            f"The recommended intervention is {selected_intervention}, "
            f"with policy decision {policy_decision}."
        ),
        "payment": payment,
        "optimization": optimization,
        "policy": policy,
        "recovery_probability": probability,
        "source": "AgentReady recovery intelligence",
    }


# ---------------------------------------------------------
# Main agent
# ---------------------------------------------------------

def answer_recovery_question(
    question: str,
) -> dict[str, Any]:
    """
    Main entry point for the AgentReady Revenue Recovery Agent.

    This is intentionally deterministic and grounded in the
    existing recovery pipeline. It does not invent financial data.
    """

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    normalized = question.lower().strip()

    # -----------------------------------------------------
    # Detect customer/payment reference
    # -----------------------------------------------------

    payments = _get_failed_payments()

    matched_payment = None

    for payment in payments:
        payment_id = str(payment.get("id", "")).lower()
        customer_id = str(payment.get("customer_id", "")).lower()

        if payment_id in normalized or customer_id in normalized:
            matched_payment = payment
            break

    if matched_payment:
        return answer_payment_question(
            question=question,
            payment_reference=matched_payment["id"],
        )

    # -----------------------------------------------------
    # Portfolio-level question
    # -----------------------------------------------------

    return answer_portfolio_question(question)