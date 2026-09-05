import pytest

from ml.recovery_agent import answer_recovery_question


def make_payment(
    payment_id="payment-001",
    customer_id="cust_001",
    amount=5000,
    failure_reason="insufficient_funds",
):
    return {
        "id": payment_id,
        "customer_id": customer_id,
        "amount": amount,
        "currency": "INR",
        "payment_status": "failed",
        "failure_reason": failure_reason,
    }


def make_optimization(
    intervention="retry_later",
    probability=0.90,
    expected_value=4500,
):
    return {
        "recommended_intervention": intervention,
        "recommended_probability": probability,
        "recommended_probability_percent": probability * 100,
        "expected_recovery_value": expected_value,
        "candidates": [
            {
                "intervention": intervention,
                "recovery_probability": probability,
                "expected_recovery_value": expected_value,
            }
        ],
    }


def make_policy(decision="AUTO_EXECUTE"):
    return {
        "decision": decision,
        "auto_execute": decision == "AUTO_EXECUTE",
        "requires_human_review": decision != "AUTO_EXECUTE",
        "policy_reasons": [],
    }


def test_revenue_at_risk_question(monkeypatch):
    monkeypatch.setattr(
        "ml.recovery_agent._get_failed_payments",
        lambda: [make_payment()],
    )

    monkeypatch.setattr(
        "ml.recovery_agent.analyze_batch_recovery",
        lambda: {
            "payment_count": 1,
            "total_revenue_at_risk": 5000,
            "total_expected_recovery": 4500,
            "recovery_opportunity_percent": 90.0,
            "results": [],
        },
    )

    result = answer_recovery_question(
        "How much revenue is currently at risk?"
    )

    assert result["intent"] == "revenue_at_risk"
    assert result["metrics"]["payment_count"] == 1
    assert result["metrics"]["total_revenue_at_risk"] == 5000
    assert result["metrics"]["total_expected_recovery"] == 4500


def test_prioritize_question_returns_ranked_recommendations(monkeypatch):
    monkeypatch.setattr(
        "ml.recovery_agent._get_failed_payments",
        lambda: [
            make_payment(
                payment_id="payment-001",
                customer_id="cust_001",
                amount=5000,
            ),
            make_payment(
                payment_id="payment-002",
                customer_id="cust_002",
                amount=9000,
            ),
        ],
    )

    monkeypatch.setattr(
        "ml.recovery_agent.analyze_batch_recovery",
        lambda: {
            "payment_count": 2,
            "total_revenue_at_risk": 14000,
            "total_expected_recovery": 10000,
            "recovery_opportunity_percent": 71.43,
            "results": [
                {
                    "payment_id": "payment-001",
                    "customer_id": "cust_001",
                    "amount": 5000,
                    "currency": "INR",
                    "failure_reason": "insufficient_funds",
                    "recommended_intervention": "retry_later",
                    "recovery_probability": 0.80,
                    "expected_recovery_value": 4000,
                    "policy_decision": "AUTO_EXECUTE",
                },
                {
                    "payment_id": "payment-002",
                    "customer_id": "cust_002",
                    "amount": 9000,
                    "currency": "INR",
                    "failure_reason": "card_declined",
                    "recommended_intervention": "request_card_update",
                    "recovery_probability": 0.67,
                    "expected_recovery_value": 6030,
                    "policy_decision": "HUMAN_REVIEW",
                },
            ],
        },
    )

    result = answer_recovery_question(
        "Which failed payments should I prioritize?"
    )

    assert result["intent"] == "prioritize_recovery"
    assert len(result["recommendations"]) == 2
    assert result["recommendations"][0]["payment_id"] == "payment-002"
    assert result["recommendations"][0]["expected_recovery_value"] == 6030


def test_human_review_question_filters_policy_decisions(monkeypatch):
    monkeypatch.setattr(
        "ml.recovery_agent._get_failed_payments",
        lambda: [make_payment()],
    )

    monkeypatch.setattr(
        "ml.recovery_agent.analyze_batch_recovery",
        lambda: {
            "payment_count": 2,
            "total_revenue_at_risk": 14000,
            "total_expected_recovery": 9000,
            "recovery_opportunity_percent": 64.29,
            "results": [
                {
                    "payment_id": "payment-001",
                    "customer_id": "cust_001",
                    "amount": 5000,
                    "policy_decision": "AUTO_EXECUTE",
                },
                {
                    "payment_id": "payment-002",
                    "customer_id": "cust_002",
                    "amount": 9000,
                    "policy_decision": "HUMAN_REVIEW",
                },
            ],
        },
    )

    result = answer_recovery_question(
        "Which payments need human review?"
    )

    assert result["intent"] == "human_review"
    assert len(result["payments"]) == 1
    assert result["payments"][0]["payment_id"] == "payment-002"


def test_payment_recommendation_question(monkeypatch):
    payment = make_payment()

    monkeypatch.setattr(
        "ml.recovery_agent._get_failed_payments",
        lambda: [payment],
    )

    monkeypatch.setattr(
        "ml.recovery_agent.get_payment_context",
        lambda payment_id, intervention: {
            "payment_id": payment_id,
            "amount": 5000,
            "previous_attempts": 0,
            "previous_recovery_attempts": 0,
        },
    )

    monkeypatch.setattr(
        "ml.recovery_agent.optimize_intervention",
        lambda context: make_optimization(),
    )

    monkeypatch.setattr(
        "ml.recovery_agent.evaluate_policy",
        lambda payment_context, optimization: make_policy(
            "AUTO_EXECUTE"
        ),
    )

    result = answer_recovery_question(
        "What should we do with cust_001?"
    )

    assert result["intent"] == "payment_recommendation"
    assert result["payment"]["customer_id"] == "cust_001"
    assert result["optimization"]["recommended_intervention"] == "retry_later"
    assert result["policy"]["decision"] == "AUTO_EXECUTE"
    assert result["recovery_probability"] == 0.90


def test_payment_explanation_question(monkeypatch):
    payment = make_payment(
        failure_reason="card_declined"
    )

    monkeypatch.setattr(
        "ml.recovery_agent._get_failed_payments",
        lambda: [payment],
    )

    monkeypatch.setattr(
        "ml.recovery_agent.get_payment_context",
        lambda payment_id, intervention: {
            "payment_id": payment_id,
            "amount": 5000,
            "previous_attempts": 0,
            "previous_recovery_attempts": 0,
        },
    )

    monkeypatch.setattr(
        "ml.recovery_agent.optimize_intervention",
        lambda context: make_optimization(
            intervention="request_card_update",
            probability=0.75,
            expected_value=3750,
        ),
    )

    monkeypatch.setattr(
        "ml.recovery_agent.evaluate_policy",
        lambda payment_context, optimization: make_policy(
            "HUMAN_REVIEW"
        ),
    )

    result = answer_recovery_question(
        "Why was cust_001 selected?"
    )

    assert result["intent"] == "payment_explanation"
    assert "card_declined" in result["answer"]
    assert "policy guardrails" in result["answer"]
    assert result["policy"]["decision"] == "HUMAN_REVIEW"


def test_unknown_payment_reference_falls_back_to_portfolio(monkeypatch):
    monkeypatch.setattr(
        "ml.recovery_agent._get_failed_payments",
        lambda: [make_payment()],
    )

    monkeypatch.setattr(
        "ml.recovery_agent.analyze_batch_recovery",
        lambda: {
            "payment_count": 1,
            "total_revenue_at_risk": 5000,
            "total_expected_recovery": 4500,
            "recovery_opportunity_percent": 90.0,
            "results": [],
        },
    )

    result = answer_recovery_question(
        "What is happening with cust_unknown?"
    )

    assert result["intent"] == "portfolio_summary"
    assert "AgentReady analyzed" in result["answer"]
