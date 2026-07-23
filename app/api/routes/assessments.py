from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...core.errors import TrustTraceAPIError
from ...db.session import get_db
from ...ml.interfaces import FraudModelService
from ...schemas import RiskAssessment, TraditionalRiskRequest, Web3RiskRequest
from ...services import assessment_service
from ...services.web3_rules_service import Web3RuleEngine
from ..deps import get_model_service, get_web3_engine

router = APIRouter(tags=["assessments"])


@router.post("/api/risk/traditional", response_model=RiskAssessment)
async def assess_traditional(
    request: TraditionalRiskRequest,
    db: Session = Depends(get_db),
    model_service: FraudModelService = Depends(get_model_service),
) -> RiskAssessment:
    try:
        return assessment_service.assess_traditional(db, request, model_service)
    except Exception as exc:
        db.rollback()
        raise TrustTraceAPIError(
            code="MODEL_INFERENCE_FAILED",
            message="The risk assessment could not be completed.",
            status_code=502,
            details=f"{type(exc).__name__}: {exc}",
        ) from exc


@router.get("/api/risk/traditional/{assessment_id}", response_model=RiskAssessment)
async def get_traditional_assessment(
    assessment_id: uuid.UUID, db: Session = Depends(get_db)
) -> RiskAssessment:
    result = assessment_service.get_assessment(db, assessment_id)
    if result is None:
        raise TrustTraceAPIError(
            code="ASSESSMENT_NOT_FOUND",
            message=f"No assessment found with id {assessment_id}.",
            status_code=404,
        )
    return result


@router.get("/api/risk/traditional/{assessment_id}/explanation")
async def get_traditional_explanation(
    assessment_id: uuid.UUID, db: Session = Depends(get_db)
) -> dict[str, Any]:
    result = assessment_service.get_assessment(db, assessment_id)
    if result is None:
        raise TrustTraceAPIError(
            code="ASSESSMENT_NOT_FOUND",
            message=f"No assessment found with id {assessment_id}.",
            status_code=404,
        )
    return {
        "assessment_id": result.assessment_id,
        "trust_score": result.trust_score,
        "fraud_probability": result.fraud_probability,
        "risk_factors": result.factors,
        "protective_factors": result.protective_factors,
    }


@router.post("/api/risk/web3", response_model=RiskAssessment)
async def assess_web3(
    request: Web3RiskRequest, engine: Web3RuleEngine = Depends(get_web3_engine)
) -> RiskAssessment:
    try:
        return await engine.assess(request)
    except Exception as exc:
        raise TrustTraceAPIError(
            code="WEB3_ASSESSMENT_FAILED",
            message="The Web3 risk assessment could not be completed.",
            status_code=502,
            details=f"{type(exc).__name__}: {exc}",
        ) from exc


@router.get("/api/demo/scenarios")
async def scenarios() -> dict[str, Any]:
    from ...data import demo_scenarios

    return demo_scenarios.SCENARIOS
