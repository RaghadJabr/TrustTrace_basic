from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


RiskLevel = Literal["low", "review", "high"]
Recommendation = Literal["continue", "review", "cancel"]
Severity = Literal["low", "medium", "high"]


class RiskFactor(BaseModel):
    code: str
    severity: Severity
    points: int
    message_en: str
    message_ar: str


class RiskAssessment(BaseModel):
    assessment_id: str
    payment_type: Literal["traditional", "web3"]
    risk_score: int = Field(ge=0, le=100)
    risk_level: RiskLevel
    recommendation: Recommendation
    verdict_en: str
    verdict_ar: str
    summary_en: str
    summary_ar: str
    factors: list[RiskFactor]
    data_sources: list[str]
    prototype_notice: str = (
        "Hackathon prototype: JOFS context may be sandbox or mock data; "
        "device, location, behavioural and fraud-intelligence signals are simulated."
    )


class TraditionalRiskRequest(BaseModel):
    account_id: str
    beneficiary_id: str
    amount: float = Field(gt=0)
    currency: str = "JOD"
    merchant: str
    domain: str
    device_id: str
    location: str
    rapid_attempts: int = Field(default=0, ge=0)


class Web3RiskRequest(BaseModel):
    wallet_address: str
    contract_address: str
    network: str = "ethereum"
    action: str = "token_approval"
    token_symbol: str = "USDT"
    approval_limit: Literal["limited", "unlimited"] = "limited"
    wallet_scam_reports: int = Field(default=0, ge=0)
    suspicious_network: bool = False
