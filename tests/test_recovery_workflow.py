from ml.recovery_workflow import get_next_intervention


def test_first_attempt_continues_with_retry_later():
    result = get_next_intervention([])

    assert result["decision"] == "CONTINUE"
    assert result["next_intervention"] == "retry_later"
    assert result["attempt_number"] == 1


def test_pending_attempt_does_not_create_duplicate():
    previous_attempts = [
        {
            "attempt_number": 1,
            "intervention": "retry_later",
            "status": "pending",
        }
    ]

    result = get_next_intervention(previous_attempts)

    assert result["decision"] == "PENDING"
    assert result["next_intervention"] == "retry_later"
    assert result["attempt_number"] == 1


def test_failed_first_attempt_moves_to_next_intervention():
    previous_attempts = [
        {
            "attempt_number": 1,
            "intervention": "retry_later",
            "status": "failed",
        }
    ]

    result = get_next_intervention(previous_attempts)

    assert result["decision"] == "CONTINUE"
    assert result["next_intervention"] == "request_alternative_payment"
    assert result["attempt_number"] == 2


def test_successful_attempt_stops_workflow():
    previous_attempts = [
        {
            "attempt_number": 1,
            "intervention": "retry_later",
            "status": "success",
        }
    ]

    result = get_next_intervention(previous_attempts)

    assert result["decision"] == "STOP"
    assert result["next_intervention"] is None


def test_maximum_attempts_require_human_review():
    previous_attempts = [
        {
            "attempt_number": 1,
            "intervention": "retry_later",
            "status": "failed",
        },
        {
            "attempt_number": 2,
            "intervention": "request_alternative_payment",
            "status": "failed",
        },
    ]

    result = get_next_intervention(previous_attempts)

    assert result["decision"] == "HUMAN_REVIEW"
    assert result["next_intervention"] is None
    assert result["attempt_number"] == 2


def test_used_intervention_is_not_repeated():
    previous_attempts = [
        {
            "attempt_number": 1,
            "intervention": "retry_later",
            "status": "failed",
        },
    ]

    result = get_next_intervention(previous_attempts)

    assert result["next_intervention"] != "retry_later"


def test_success_takes_priority_over_max_attempt_rule():
    previous_attempts = [
        {
            "attempt_number": 1,
            "intervention": "retry_later",
            "status": "failed",
        },
        {
            "attempt_number": 2,
            "intervention": "request_alternative_payment",
            "status": "success",
        },
    ]

    result = get_next_intervention(previous_attempts)

    assert result["decision"] == "STOP"
    assert result["next_intervention"] is None
