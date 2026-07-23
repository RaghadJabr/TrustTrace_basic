from app.services.trust_score_service import compute_trust_score


def test_high_trust_band():
    result = compute_trust_score(0.02)
    assert result.trust_score == 98
    assert result.risk_category == "high_trust"
    assert result.ui_risk_level == "low"


def test_critical_risk_band():
    result = compute_trust_score(0.995)
    assert result.trust_score == 1
    assert result.risk_category == "critical_risk"
    assert result.ui_risk_level == "high"


def test_elevated_risk_band_boundary():
    # trust_score = round((1 - 0.55) * 100) = 45 -> elevated_risk (40-59)
    result = compute_trust_score(0.55)
    assert result.trust_score == 45
    assert result.risk_category == "elevated_risk"
    assert result.ui_risk_level == "review"


def test_trust_score_is_clamped_to_0_100():
    assert compute_trust_score(1.5).trust_score == 0
    assert compute_trust_score(-0.5).trust_score == 100
