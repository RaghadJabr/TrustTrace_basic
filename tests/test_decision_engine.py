import pytest

from app.services.decision_engine import decide


@pytest.mark.parametrize(
    "risk_category,expected_action,expected_ui",
    [
        ("high_trust", "continue", "continue"),
        ("moderate_trust", "continue_with_warning", "continue"),
        ("elevated_risk", "verify_recipient", "review"),
        ("high_risk", "manual_review", "review"),
        ("critical_risk", "block", "cancel"),
    ],
)
def test_decide_maps_risk_category_to_action(risk_category, expected_action, expected_ui):
    decision = decide(risk_category)
    assert decision.recommended_action == expected_action
    assert decision.ui_recommendation == expected_ui


def test_decide_rejects_unknown_category():
    with pytest.raises(KeyError):
        decide("not_a_real_category")
