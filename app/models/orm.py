from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(Uuid, primary_key=True, default=uuid.uuid4)


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = _uuid_pk()
    external_customer_ref: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    accounts: Mapped[list["Account"]] = relationship(back_populates="customer")
    devices: Mapped[list["Device"]] = relationship(back_populates="customer")


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = _uuid_pk()
    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.id"), index=True)
    external_account_id: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    available_balance: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    currency: Mapped[str] = mapped_column(String(3), default="JOD")
    masked_iban: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    customer: Mapped[Customer] = relationship(back_populates="accounts")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="account")


class Merchant(Base):
    __tablename__ = "merchants"

    id: Mapped[uuid.UUID] = _uuid_pk()
    merchant_name: Mapped[str] = mapped_column(String(200))
    merchant_domain: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    category: Mapped[str | None] = mapped_column(String(60), nullable=True)
    reputation_score: Mapped[int] = mapped_column(Integer, default=50)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    blacklisted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="merchant")


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[uuid.UUID] = _uuid_pk()
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("customers.id"), nullable=True, index=True
    )
    device_fingerprint: Mapped[str] = mapped_column(String(200), index=True)
    device_type: Mapped[str] = mapped_column(String(40), default="unknown")
    network_carrier_type: Mapped[str] = mapped_column(String(40), default="unknown")
    ip_address_type: Mapped[str] = mapped_column(String(40), default="unknown")
    trusted: Mapped[bool] = mapped_column(Boolean, default=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    customer: Mapped[Customer | None] = relationship(back_populates="devices")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="device")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = _uuid_pk()
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.id"), index=True)
    merchant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("merchants.id"), index=True)
    device_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("devices.id"), nullable=True, index=True
    )
    amount: Mapped[float] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(3), default="JOD")
    country_code: Mapped[str] = mapped_column(String(2), default="JO")
    city: Mapped[str | None] = mapped_column(String(80), nullable=True)
    channel: Mapped[str] = mapped_column(String(40), default="card_checkout")
    status: Mapped[str] = mapped_column(String(20), default="under_review")
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)

    account: Mapped[Account] = relationship(back_populates="transactions")
    merchant: Mapped[Merchant] = relationship(back_populates="transactions")
    device: Mapped[Device | None] = relationship(back_populates="transactions")
    assessment: Mapped["FraudAssessment"] = relationship(
        back_populates="transaction", uselist=False
    )


class FraudAssessment(Base):
    __tablename__ = "fraud_assessments"

    id: Mapped[uuid.UUID] = _uuid_pk()
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("transactions.id"), unique=True, index=True
    )
    model_name: Mapped[str] = mapped_column(String(80))
    model_version: Mapped[str] = mapped_column(String(40))
    raw_probability: Mapped[float] = mapped_column(Float)
    calibrated_probability: Mapped[float] = mapped_column(Float)
    decision_threshold: Mapped[float] = mapped_column(Float)
    trust_score: Mapped[int] = mapped_column(Integer)
    risk_category: Mapped[str] = mapped_column(String(30), index=True)
    ui_risk_level: Mapped[str] = mapped_column(String(10))
    recommended_action: Mapped[str] = mapped_column(String(40))
    ui_recommendation: Mapped[str] = mapped_column(String(10))
    processing_time_ms: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)

    transaction: Mapped[Transaction] = relationship(back_populates="assessment")
    explanations: Mapped[list["AssessmentExplanation"]] = relationship(
        back_populates="assessment", order_by="AssessmentExplanation.importance_rank"
    )


class AssessmentExplanation(Base):
    __tablename__ = "assessment_explanations"

    id: Mapped[uuid.UUID] = _uuid_pk()
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fraud_assessments.id"), index=True
    )
    feature_name: Mapped[str] = mapped_column(String(80))
    feature_display_name: Mapped[str] = mapped_column(String(160))
    feature_value: Mapped[str] = mapped_column(String(200))
    shap_value: Mapped[float] = mapped_column(Float)
    impact_direction: Mapped[str] = mapped_column(String(12))
    importance_rank: Mapped[int] = mapped_column(Integer)
    explanation_en: Mapped[str] = mapped_column(String(300))
    explanation_ar: Mapped[str] = mapped_column(String(300))

    assessment: Mapped[FraudAssessment] = relationship(back_populates="explanations")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = _uuid_pk()
    event_type: Mapped[str] = mapped_column(String(60))
    entity_type: Mapped[str] = mapped_column(String(40))
    entity_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    correlation_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    details: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)


class ModelRegistry(Base):
    __tablename__ = "model_registry"

    id: Mapped[uuid.UUID] = _uuid_pk()
    model_name: Mapped[str] = mapped_column(String(80))
    model_type: Mapped[str] = mapped_column(String(40))
    version: Mapped[str] = mapped_column(String(40))
    artifact_path: Mapped[str] = mapped_column(String(300))
    feature_schema_version: Mapped[str] = mapped_column(String(40))
    deployment_status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
