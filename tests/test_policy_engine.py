from ml.policy_engine import evaluate_policy


def make_context(
    amount=5000,
    previous_attempts=0,
    previous_recovery_attempts=0,
):
    return {
        "amount": amount,
        "previous_attempts": previous_attempts,
        "previous_recovery_attempts": previous_recovery_attempts,
    }


def make_optimization(
    probability=0.90,
    intervention="retry_later",
):
    return {
        "recommended_probability": probability,
        "recommended_intervention": intervention,
    }


def test_high_value_payment_requires_human_review():
    decision = evaluate_policy(
        make_context(amount=20000),
        make_optimization(probability=0.95),
    )

    assert decision["decision"] == "HUMAN_REVIEW"
    assert decision["auto_execute"] is False


def test_high_probability_payment_can_auto_execute():
    decision = evaluate_policy(
        make_context(amount=5000),
        make_optimization(probability=0.90),
    )

    assert decision["decision"] == "AUTO_EXECUTE"
    assert decision["auto_execute"] is True


def test_low_probability_payment_requires_human_review():
    decision = evaluate_policy(
        make_context(amount=5000),
        make_optimization(probability=0.50),
    )

    assert decision["decision"] == "HUMAN_REVIEW"
    assert decision["auto_execute"] is False


def test_too_many_previous_attempts_require_human_review():
    decision = evaluate_policy(
        make_context(
            amount=5000,
            previous_attempts=2,
        ),
        make_optimization(probability=0.90),
    )

    assert decision["decision"] == "HUMAN_REVIEW"
    assert decision["auto_execute"] is False


def test_too_many_recovery_attempts_require_human_review():
    decision = evaluate_policy(
        make_context(
            amount=5000,
            previous_recovery_attempts=2,
        ),
        make_optimization(probability=0.90),
    )

    assert decision["decision"] == "HUMAN_REVIEW"
    assert decision["auto_execute"] is False