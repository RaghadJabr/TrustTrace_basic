from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

RiskLevel = Literal["low", "review", "high"]
Recommendation = Literal["continue", "review", "cancel"]
Severity = Literal["low", "medium", "high"]

RiskCategory = Literal[
    "high_trust", "moderate_trust", "elevated_risk", "high_risk", "critical_risk"
]
RecommendedAction = Literal[
    "continue",
    "continue_with_warning",
    "verify_recipient",
    "additional_authentication",
    "otp_verification",
    "delay_transaction",
    "manual_review",
    "cancel",
    "block",
]


class RiskFactor(BaseModel):
    code: str
    severity: Severity
    points: int
    message_en: str
    message_ar: str


class TransactionSignals(BaseModel):
    """Gateway/device/session telemetry a real card-network or device-intelligence
    integration would supply. All fields are optional with neutral defaults so the
    demo works with a thin payload; a production integration would populate these
    from the real payment gateway, 3DS provider and device-fingerprinting vendor."""

    cvv_match_status: str = "cvv2_match"
    three_ds_auth_result: str = "frictionless_pass"
    tokenization_used: str = "network_token_wallet"
    card_present_cnp: str = "cnp_online"
    ip_address_type: str = "residential"
    device_fingerprint_match: str = "known_device"
    network_carrier_type: str = "wifi"
    session_duration_sec: float = Field(default=45.0, ge=0)
    geo_velocity_kmh: float = Field(default=5.0, ge=0)
    geo_distance_km: float = Field(default=2.0, ge=0)
    merchant_location: str = "home_city"
    country_consistency: str = "same_country"
    cards_on_device_30d: int = Field(default=1, ge=0)
    failed_attempts_before_success: int = Field(default=0, ge=0)
    transaction_velocity_1h: str = "within_normal"
    account_credential_change_recency: str = "no_recent_change"
    order_shipping_speed: str = "standard"
    merchant_category: str = "retail"
    merchant_risk_score: str | None = None
    customer_type: str = "customer_based"
    segment: str | None = None


class TraditionalRiskRequest(BaseModel):
    account_id: str
    beneficiary_id: str
    amount: float = Field(gt=0)
    currency: str = "JOD"
    merchant: str
    domain: str
    device_id: str
    location: str = "Amman"
    rapid_attempts: int = Field(default=0, ge=0)
    signals: TransactionSignals = Field(default_factory=TransactionSignals)


class Web3RiskRequest(BaseModel):
    wallet_address: str
    contract_address: str
    network: str = "ethereum"
    action: str = "token_approval"
    token_symbol: str = "USDT"
    approval_limit: Literal["limited", "unlimited"] = "limited"
    wallet_scam_reports: int = Field(default=0, ge=0)
    suspicious_network: bool = False


class RiskAssessment(BaseModel):
    assessment_id: str
    correlation_id: str
    payment_type: Literal["traditional", "web3"]

    # UI-facing (kept compatible with the existing frontend)
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
        "This is an AI-assisted risk assessment, not proof of fraud or legal "
        "determination. The institution or user makes the final decision."
    )

    # Model / analyst-facing (spec section 5 & 13)
    fraud_probability: float | None = None
    trust_score: int | None = Field(default=None, ge=0, le=100)
    risk_category: RiskCategory | None = None
    recommended_action: RecommendedAction | None = None
    model_name: str | None = None
    model_version: str | None = None
    decision_threshold: float | None = None
    protective_factors: list[RiskFactor] = Field(default_factory=list)
    processing_time_ms: float | None = None
    created_at: datetime | None = None


class FundsConfirmationRequest(BaseModel):
    amount: float = Field(gt=0)
    currency: str = "JOD"


class IBANConfirmationRequest(BaseModel):
    account_type: str = Field(min_length=1, description="Account identification scheme, normally IBAN.")
    account_id: str = Field(min_length=1, description="Account identifier, such as the IBAN.")
    uid_type: str = Field(min_length=1, description="Identity type, such as National ID or Passport.")
    uid_value: str = Field(min_length=1, description="Identity value to compare with the account holder.")
    auth_date: str | None = Field(default=None, description="Optional date/time of the latest authentication.")
