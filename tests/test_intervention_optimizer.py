from ml.intervention_optimizer import optimize_intervention


def test_optimizer_evaluates_all_interventions(monkeypatch):
    probabilities = {
        "retry_now": 0.40,
        "retry_later": 0.90,
        "request_alternative_payment": 0.60,
        "request_card_update": 0.50,
    }

    def fake_predict_recovery(context):
        return {
            "recovery_probability": probabilities[
                context["intervention"]
            ]
        }

    monkeypatch.setattr(
        "ml.intervention_optimizer.predict_recovery",
        fake_predict_recovery,
    )

    result = optimize_intervention(
        {
            "amount": 10000,
        }
    )

    assert len(result["candidates"]) == 4

    interventions = {
        candidate["intervention"]
        for candidate in result["candidates"]
    }

    assert interventions == {
        "retry_now",
        "retry_later",
        "request_alternative_payment",
        "request_card_update",
    }


def test_optimizer_calculates_expected_recovery_value(monkeypatch):
    probabilities = {
        "retry_now": 0.40,
        "retry_later": 0.80,
        "request_alternative_payment": 0.60,
        "request_card_update": 0.50,
    }

    def fake_predict_recovery(context):
        return {
            "recovery_probability": probabilities[
                context["intervention"]
            ]
        }

    monkeypatch.setattr(
        "ml.intervention_optimizer.predict_recovery",
        fake_predict_recovery,
    )

    result = optimize_intervention(
        {
            "amount": 10000,
        }
    )

    retry_later = next(
        candidate
        for candidate in result["candidates"]
        if candidate["intervention"] == "retry_later"
    )

    assert retry_later["recovery_probability"] == 0.80
    assert retry_later["recovery_probability_percent"] == 80.0
    assert retry_later["expected_recovery_value"] == 8000.0


def test_optimizer_selects_highest_expected_recovery_value(monkeypatch):
    probabilities = {
        "retry_now": 0.40,
        "retry_later": 0.90,
        "request_alternative_payment": 0.60,
        "request_card_update": 0.50,
    }

    def fake_predict_recovery(context):
        return {
            "recovery_probability": probabilities[
                context["intervention"]
            ]
        }

    monkeypatch.setattr(
        "ml.intervention_optimizer.predict_recovery",
        fake_predict_recovery,
    )

    result = optimize_intervention(
        {
            "amount": 10000,
        }
    )

    assert result["recommended_intervention"] == "retry_later"
    assert result["recommended_probability"] == 0.90
    assert result["recommended_probability_percent"] == 90.0
    assert result["expected_recovery_value"] == 9000.0


def test_optimizer_ranks_candidates_highest_first(monkeypatch):
    probabilities = {
        "retry_now": 0.40,
        "retry_later": 0.90,
        "request_alternative_payment": 0.60,
        "request_card_update": 0.50,
    }

    def fake_predict_recovery(context):
        return {
            "recovery_probability": probabilities[
                context["intervention"]
            ]
        }

    monkeypatch.setattr(
        "ml.intervention_optimizer.predict_recovery",
        fake_predict_recovery,
    )

    result = optimize_intervention(
        {
            "amount": 10000,
        }
    )

    values = [
        candidate["expected_recovery_value"]
        for candidate in result["candidates"]
    ]

    assert values == sorted(values, reverse=True)


def test_optimizer_handles_zero_amount(monkeypatch):
    probabilities = {
        "retry_now": 0.40,
        "retry_later": 0.90,
        "request_alternative_payment": 0.60,
        "request_card_update": 0.50,
    }

    def fake_predict_recovery(context):
        return {
            "recovery_probability": probabilities[
                context["intervention"]
            ]
        }

    monkeypatch.setattr(
        "ml.intervention_optimizer.predict_recovery",
        fake_predict_recovery,
    )

    result = optimize_intervention(
        {
            "amount": 0,
        }
    )

    assert all(
        candidate["expected_recovery_value"] == 0.0
        for candidate in result["candidates"]
    )
