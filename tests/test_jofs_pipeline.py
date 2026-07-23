"""Proves the traditional assessment pipeline is live and JOFS-backed, not a
static/demo score path. Runs entirely against JOFS_MODE=mock (the default) --
no live JOFS sandbox is contacted."""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import patch

import pytest
from sqlalchemy import func, select

from app.core.errors import TrustTraceAPIError
from app.db.session import SessionLocal
from app.models.orm import AssessmentExplanation, FraudAssessment, Transaction
from app.schemas import TraditionalRiskRequest, TransactionSignals
from app.services import assessment_service


def _request(**overrides) -> TraditionalRiskRequest:
    payload = {
        "account_id": "ACC-1001",
        "beneficiary_id": "BEN-001",
        "amount": 55,
        "currency": "JOD",
        "merchant": "Noon Jordan",
        "domain": "www.noon.com",
        "device_id": "LEEN-IP15",
        "location": "Amman",
        "rapid_attempts": 0,
        "signals": TransactionSignals(),
    }
    payload.update(overrides)
    return TraditionalRiskRequest(**payload)


def test_jofs_mode_is_mock_in_tests(client):
    assert client.app.state.jofs.mode == "mock"


def test_missing_feature_raises_clear_contract_error(client):
    model_service = client.app.state.traditional_model_service
    complete = {name: 0 for name in model_service.schema["model_features"]}
    incomplete = dict(complete)
    del incomplete["transaction_amount"]

    with pytest.raises(ValueError, match="missing"):
        model_service.validate_feature_contract(incomplete)

    unexpected = dict(complete)
    unexpected["not_a_real_feature"] = 1
    with pytest.raises(ValueError, match="unexpected"):
        model_service.validate_feature_contract(unexpected)

    model_service.validate_feature_contract(complete)  # does not raise


def test_prediction_and_explanation_use_the_identical_feature_vector(client):
    model_service = client.app.state.traditional_model_service
    jofs = client.app.state.jofs
    db = SessionLocal()

    predict_features = []
    explain_features = []
    original_predict = model_service.predict
    original_explain = model_service.explain

    def spy_predict(features):
        predict_features.append(dict(features))
        return original_predict(features)

    def spy_explain(features):
        explain_features.append(dict(features))
        return original_explain(features)

    try:
        with patch.object(model_service, "predict", side_effect=spy_predict), patch.object(
            model_service, "explain", side_effect=spy_explain
        ):
            asyncio.run(
                assessment_service.assess_traditional(db, _request(), model_service, jofs)
            )
    finally:
        db.close()

    assert len(predict_features) == 1
    assert len(explain_features) == 1
    assert predict_features[0] == explain_features[0]


def test_two_different_inputs_produce_different_feature_vectors(client):
    model_service = client.app.state.traditional_model_service
    jofs = client.app.state.jofs

    captured = []
    original_predict = model_service.predict

    def spy_predict(features):
        captured.append(dict(features))
        return original_predict(features)

    db = SessionLocal()
    try:
        with patch.object(model_service, "predict", side_effect=spy_predict):
            asyncio.run(
                assessment_service.assess_traditional(
                    db, _request(amount=55), model_service, jofs
                )
            )
            asyncio.run(
                assessment_service.assess_traditional(
                    db,
                    _request(
                        amount=2450,
                        beneficiary_id="BEN-777",
                        merchant="Fast Visa Approval",
                        domain="visa-fast-approval.example",
                        signals=TransactionSignals(
                            cvv_match_status="cvv2_mismatch",
                            three_ds_auth_result="challenge_fail",
                            ip_address_type="vpn",
                        ),
                    ),
                    model_service,
                    jofs,
                )
            )
    finally:
        db.close()

    assert len(captured) == 2
    assert captured[0] != captured[1]
    assert captured[0]["transaction_amount"] != captured[1]["transaction_amount"]
    assert captured[0]["cvv_match_status"] != captured[1]["cvv_match_status"]


def test_provenance_reflects_real_jofs_sourcing(client):
    model_service = client.app.state.traditional_model_service
    jofs = client.app.state.jofs
    db = SessionLocal()
    try:
        result = asyncio.run(
            assessment_service.assess_traditional(db, _request(), model_service, jofs)
        )
    finally:
        db.close()

    assert result.provenance["jofs_mode"] == "mock"
    assert result.provenance["account_source"] == "JOFS"
    assert result.provenance["explanation_method"] == "SHAP"
    assert result.provenance["calibration_applied"] is True
    assert result.provenance["transaction_history_status"] == "ok"
    assert result.account_balance is not None
    assert result.funds_available is not None


def test_unknown_jofs_account_fails_clearly_without_fabricating_a_score(client):
    model_service = client.app.state.traditional_model_service
    jofs = client.app.state.jofs
    db = SessionLocal()

    try:
        assessment_count_before = db.scalar(select(func.count()).select_from(FraudAssessment))
        transaction_count_before = db.scalar(select(func.count()).select_from(Transaction))

        with pytest.raises(TrustTraceAPIError) as excinfo:
            asyncio.run(
                assessment_service.assess_traditional(
                    db, _request(account_id="NOT-A-REAL-ACCOUNT"), model_service, jofs
                )
            )
        assert excinfo.value.code == "JOFS_ACCOUNT_NOT_FOUND"
        assert excinfo.value.status_code == 404
        db.rollback()

        assessment_count_after = db.scalar(select(func.count()).select_from(FraudAssessment))
        transaction_count_after = db.scalar(select(func.count()).select_from(Transaction))
        assert assessment_count_after == assessment_count_before
        assert transaction_count_after == transaction_count_before
    finally:
        db.close()


def test_explanations_belong_to_the_correct_assessment(client):
    model_service = client.app.state.traditional_model_service
    jofs = client.app.state.jofs
    db = SessionLocal()
    try:
        first = asyncio.run(
            assessment_service.assess_traditional(db, _request(amount=51), model_service, jofs)
        )
        second = asyncio.run(
            assessment_service.assess_traditional(db, _request(amount=52), model_service, jofs)
        )

        first_id = uuid.UUID(first.assessment_id)
        second_id = uuid.UUID(second.assessment_id)
        assert first_id != second_id

        first_rows = db.scalars(
            select(AssessmentExplanation).where(AssessmentExplanation.assessment_id == first_id)
        ).all()
        second_rows = db.scalars(
            select(AssessmentExplanation).where(AssessmentExplanation.assessment_id == second_id)
        ).all()

        assert len(first_rows) > 0
        assert len(second_rows) > 0
        assert {row.id for row in first_rows}.isdisjoint({row.id for row in second_rows})
    finally:
        db.close()


def test_no_score_calculation_in_frontend_javascript():
    import re
    from pathlib import Path

    app_js = (Path(__file__).resolve().parent.parent / "app" / "static" / "app.js").read_text()

    # The frontend must render assessment.* fields returned by the backend,
    # never derive its own score/level/recommendation. Assignment (=), not
    # comparison (==, ===, !=), is what would indicate local calculation.
    forbidden = ["riskScore", "trustScore", "riskLevel", "recommendation"]
    for name in forbidden:
        assignment = re.search(rf"(?<![=!<>]){name}\s*=(?!=)", app_js)
        assert assignment is None, f"frontend appears to assign '{name}' itself: {assignment}"

    assert "assessment.risk_score" in app_js
    assert "assessment.risk_level" in app_js
