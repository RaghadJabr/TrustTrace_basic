from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.errors import TrustTraceAPIError
from ..integrations.open_finance.provider import JOFSAdapter
from ..ml.interfaces import FraudModelService
from ..models.orm import Account, AssessmentExplanation, Customer, Device, FraudAssessment, Merchant, Transaction
from ..schemas import RiskAssessment, RiskFactor, TraditionalRiskRequest, TransactionSignals
from . import audit_service
from .decision_engine import decide
from .explanation_service import _severity, build_explanations, to_risk_factor
from .feature_service import TransactionHistory, build_traditional_features
from .jofs_normalization import normalize_account, normalize_beneficiary, normalize_transactions
from .trust_score_service import compute_trust_score

_VERDICTS: dict[str, dict[str, str]] = {
    "high_trust": {
        "verdict_en": "Verified — low risk",
        "verdict_ar": "تم التحقق — مخاطر منخفضة",
        "summary_en": "No significant fraud indicators were detected in this assessment.",
        "summary_ar": "لم يتم اكتشاف مؤشرات احتيال مهمة في هذا التقييم.",
    },
    "moderate_trust": {
        "verdict_en": "Verified with minor notices",
        "verdict_ar": "تم التحقق مع ملاحظات بسيطة",
        "summary_en": "The transaction is broadly consistent with expected behaviour, with minor notices.",
        "summary_ar": "العملية متوافقة إلى حد كبير مع السلوك المتوقع، مع ملاحظات بسيطة.",
    },
    "elevated_risk": {
        "verdict_en": "Review recommended",
        "verdict_ar": "يُنصح بالمراجعة",
        "summary_en": "Pause and review the highlighted risk factors, or verify the recipient, before continuing.",
        "summary_ar": "توقف وراجع عوامل الخطر الموضحة، أو تحقق من المستفيد، قبل المتابعة.",
    },
    "high_risk": {
        "verdict_en": "Elevated fraud risk",
        "verdict_ar": "مخاطر احتيال مرتفعة",
        "summary_en": "This activity differs significantly from expected behaviour. Manual review is recommended.",
        "summary_ar": "يختلف هذا النشاط بشكل كبير عن السلوك المتوقع. يُنصح بمراجعة يدوية.",
    },
    "critical_risk": {
        "verdict_en": "Critical fraud risk — additional verification required",
        "verdict_ar": "مخاطر احتيال حرجة — يلزم تحقق إضافي",
        "summary_en": "Strong fraud indicators were detected. This is a risk assessment, not proof of fraud; block or escalate per policy.",
        "summary_ar": "تم رصد مؤشرات احتيال قوية. هذا تقييم مخاطر وليس إثباتاً للاحتيال؛ يُرجى الحظر أو التصعيد وفق السياسة.",
    },
}


def _get_or_create_customer(db: Session, external_customer_ref: str) -> Customer:
    customer = db.scalar(
        select(Customer).where(Customer.external_customer_ref == external_customer_ref)
    )
    if customer is None:
        customer = Customer(external_customer_ref=external_customer_ref)
        db.add(customer)
        db.flush()
    return customer


def _get_or_create_account(db: Session, external_account_id: str, customer: Customer) -> Account:
    account = db.scalar(select(Account).where(Account.external_account_id == external_account_id))
    if account is None:
        account = Account(customer_id=customer.id, external_account_id=external_account_id)
        db.add(account)
        db.flush()
    return account


def _get_or_create_merchant(db: Session, domain: str, name: str, category: str) -> Merchant:
    merchant = db.scalar(select(Merchant).where(Merchant.merchant_domain == domain))
    if merchant is None:
        merchant = Merchant(merchant_name=name, merchant_domain=domain, category=category)
        db.add(merchant)
        db.flush()
    return merchant


def _get_or_create_device(db: Session, fingerprint: str, customer: Customer) -> Device:
    device = db.scalar(select(Device).where(Device.device_fingerprint == fingerprint))
    if device is None:
        device = Device(customer_id=customer.id, device_fingerprint=fingerprint)
        db.add(device)
        db.flush()
    return device


def _defaulted_signal_fields(signals: TransactionSignals) -> list[str]:
    """Which TransactionSignals fields are still at their neutral default --
    i.e. likely never supplied by a real gateway/device integration for this
    request. Best-effort: a genuinely-supplied value that happens to equal the
    default is indistinguishable from an unsupplied one, which is why this is
    reported as provenance metadata rather than treated as an error."""

    defaults = TransactionSignals()
    return [
        name
        for name in TransactionSignals.model_fields
        if getattr(signals, name) == getattr(defaults, name)
    ]


def get_assessment(db: Session, assessment_id: uuid.UUID) -> RiskAssessment | None:
    assessment = db.get(FraudAssessment, assessment_id)
    if assessment is None:
        return None

    transaction = db.get(Transaction, assessment.transaction_id)
    verdict = _VERDICTS[assessment.risk_category]
    stored_metadata = (transaction.metadata_json if transaction else None) or {}
    provenance = {
        key: value
        for key, value in stored_metadata.items()
        if key not in ("beneficiary_id", "rapid_attempts")
    }

    risk_factors = [
        _explanation_row_to_risk_factor(row)
        for row in assessment.explanations
        if row.impact_direction == "risk"
    ]
    protective_factors = [
        _explanation_row_to_risk_factor(row)
        for row in assessment.explanations
        if row.impact_direction == "protective"
    ]
    if not risk_factors and assessment.explanations:
        # Same fallback as assess_traditional: if every SHAP contribution was
        # protective, still surface the top-ranked one rather than an empty list.
        risk_factors = [_explanation_row_to_risk_factor(assessment.explanations[0])]

    return RiskAssessment(
        assessment_id=str(assessment.id),
        correlation_id=str(uuid.uuid4()),
        payment_type="traditional",
        risk_score=round(assessment.calibrated_probability * 100),
        risk_level=assessment.ui_risk_level,  # type: ignore[arg-type]
        recommendation=assessment.ui_recommendation,  # type: ignore[arg-type]
        verdict_en=verdict["verdict_en"],
        verdict_ar=verdict["verdict_ar"],
        summary_en=verdict["summary_en"],
        summary_ar=verdict["summary_ar"],
        factors=risk_factors,
        data_sources=[
            f"JOFS account/balance/beneficiary/transaction history ({provenance.get('jofs_mode', 'unknown')} mode)",
            "PostgreSQL account & transaction history",
            f"{assessment.model_name} fraud model (v{assessment.model_version})",
            "SHAP explainability",
        ],
        fraud_probability=assessment.calibrated_probability,
        trust_score=assessment.trust_score,
        risk_category=assessment.risk_category,  # type: ignore[arg-type]
        recommended_action=assessment.recommended_action,  # type: ignore[arg-type]
        model_name=assessment.model_name,
        model_version=assessment.model_version,
        decision_threshold=assessment.decision_threshold,
        protective_factors=protective_factors,
        processing_time_ms=assessment.processing_time_ms,
        created_at=transaction.created_at if transaction else assessment.created_at,
        provenance=provenance,
    )


def _explanation_row_to_risk_factor(row: AssessmentExplanation) -> RiskFactor:
    abs_shap = abs(row.shap_value)
    return RiskFactor(
        code=row.feature_name.upper(),
        severity=_severity(abs_shap),  # type: ignore[arg-type]
        points=round(min(abs_shap * 15, 100)),
        message_en=row.explanation_en,
        message_ar=row.explanation_ar,
    )


async def assess_traditional(
    db: Session,
    request: TraditionalRiskRequest,
    model_service: FraudModelService,
    jofs: JOFSAdapter,
) -> RiskAssessment:
    started_at = time.perf_counter()
    now = datetime.now(timezone.utc)
    missing_data: list[str] = []

    # 1. Resolve the account through JOFS -- required. A failure here must not
    # fall back to demo/local-only data or produce a score; it's a clear error.
    try:
        raw_account = await jofs.get_account(request.account_id)
    except Exception as exc:
        raise TrustTraceAPIError(
            code="JOFS_ACCOUNT_LOOKUP_FAILED",
            message="Could not reach JOFS to resolve the account.",
            status_code=502,
            details=f"{type(exc).__name__}: {exc}",
        ) from exc

    if raw_account is None:
        raise TrustTraceAPIError(
            code="JOFS_ACCOUNT_NOT_FOUND",
            message=f"JOFS has no account matching '{request.account_id}'.",
            status_code=404,
        )

    normalized_account = normalize_account(raw_account)

    # 2. Balance -- optional business context (not a model feature).
    try:
        balance = await jofs.get_balance(request.account_id)
        balance_status = "ok"
    except Exception:
        balance = None
        balance_status = "unavailable"
        missing_data.append("balance")

    # 3. Beneficiary -- optional.
    try:
        raw_beneficiary = await jofs.get_beneficiary(request.account_id, request.beneficiary_id)
        normalized_beneficiary = normalize_beneficiary(raw_beneficiary)
        beneficiary_status = "ok" if normalized_beneficiary else "not_found"
        if normalized_beneficiary is None:
            missing_data.append("beneficiary")
    except Exception:
        normalized_beneficiary = None
        beneficiary_status = "unavailable"
        missing_data.append("beneficiary")

    # 4. Transaction history -- optional, feeds avg_amount_deviation_sigma via
    # feature_service.TransactionHistory (existing formula, unchanged).
    try:
        raw_transactions = await jofs.get_transactions(request.account_id)
        jofs_transactions = normalize_transactions(raw_transactions)
        history_status = "ok"
    except Exception:
        jofs_transactions = []
        history_status = "unavailable"
        missing_data.append("transaction_history")

    # 5. Available-funds confirmation -- optional, business info only, not a
    # model feature.
    try:
        funds_result = await jofs.confirm_available_funds(
            account_id=request.account_id, amount=request.amount, currency=request.currency
        )
        funds_available = bool(funds_result.get("fundsAvailable"))
        funds_status = "ok"
    except Exception:
        funds_available = None
        funds_status = "unavailable"
        missing_data.append("funds_confirmation")

    customer = _get_or_create_customer(db, request.account_id)
    account = _get_or_create_account(db, request.account_id, customer)
    if balance is not None:
        account.available_balance = balance["available_balance"]
        if balance.get("currency"):
            account.currency = balance["currency"]
    if normalized_account.masked_iban:
        account.masked_iban = normalized_account.masked_iban

    merchant = _get_or_create_merchant(
        db, request.domain, request.merchant, request.signals.merchant_category
    )
    _get_or_create_device(db, request.device_id, customer)

    history = TransactionHistory(db, account, merchant, jofs_transactions=jofs_transactions)
    features = build_traditional_features(
        amount=request.amount,
        account=account,
        merchant=merchant,
        signals=request.signals,
        history=history,
        now=now,
    )

    # Explicit contract check: exactly the 31 training-time features, nothing
    # missing or silently dropped, before this feature vector is used for
    # both the prediction and the SHAP explanation below.
    model_service.validate_feature_contract(features)

    prediction = model_service.predict(features)
    explanation = model_service.explain(features)
    trust = compute_trust_score(prediction.calibrated_probability)
    decision = decide(trust.risk_category)

    provenance: dict[str, object] = {
        "jofs_mode": jofs.mode,
        "account_source": "JOFS",
        "beneficiary_source": beneficiary_status,
        "balance_status": balance_status,
        "transaction_history_source": "JOFS+PostgreSQL" if history.jofs_transaction_count else "PostgreSQL",
        "transaction_history_status": history_status,
        "jofs_transaction_count": history.jofs_transaction_count,
        "funds_confirmation_status": funds_status,
        "model_name": prediction.model_name,
        "model_version": prediction.model_version,
        "model_threshold": prediction.threshold,
        "calibration_applied": True,
        "explanation_method": "SHAP",
        "missing_data": missing_data,
        "defaulted_signals": _defaulted_signal_fields(request.signals),
    }

    transaction = Transaction(
        account_id=account.id,
        merchant_id=merchant.id,
        amount=request.amount,
        currency=request.currency,
        city=request.location,
        channel="card_checkout",
        status="assessed",
        metadata_json={
            "beneficiary_id": request.beneficiary_id,
            "rapid_attempts": request.rapid_attempts,
            **provenance,
        },
    )
    db.add(transaction)
    db.flush()

    processing_time_ms = (time.perf_counter() - started_at) * 1000

    assessment = FraudAssessment(
        transaction_id=transaction.id,
        model_name=prediction.model_name,
        model_version=prediction.model_version,
        raw_probability=prediction.raw_probability,
        calibrated_probability=prediction.calibrated_probability,
        decision_threshold=prediction.threshold,
        trust_score=trust.trust_score,
        risk_category=trust.risk_category,
        ui_risk_level=trust.ui_risk_level,
        recommended_action=decision.recommended_action,
        ui_recommendation=decision.ui_recommendation,
        processing_time_ms=processing_time_ms,
    )
    db.add(assessment)
    db.flush()

    entries = build_explanations(explanation.contributions)
    for entry in entries:
        db.add(
            AssessmentExplanation(
                assessment_id=assessment.id,
                feature_name=entry.feature_name,
                feature_display_name=entry.feature_display_name,
                feature_value=entry.feature_value,
                shap_value=entry.shap_value,
                impact_direction=entry.impact_direction,
                importance_rank=entry.importance_rank,
                explanation_en=entry.explanation_en,
                explanation_ar=entry.explanation_ar,
            )
        )

    correlation_id = uuid.uuid4()
    audit_service.record(
        db,
        event_type="assessment_completed",
        entity_type="transaction",
        entity_id=transaction.id,
        correlation_id=correlation_id,
        details={
            "trust_score": trust.trust_score,
            "risk_category": trust.risk_category,
            "recommended_action": decision.recommended_action,
            **provenance,
        },
    )

    db.commit()

    risk_factors = [to_risk_factor(e) for e in entries if e.impact_direction == "risk"]
    protective_factors = [to_risk_factor(e) for e in entries if e.impact_direction == "protective"]
    verdict = _VERDICTS[trust.risk_category]

    return RiskAssessment(
        assessment_id=str(assessment.id),
        correlation_id=str(correlation_id),
        payment_type="traditional",
        risk_score=round(prediction.calibrated_probability * 100),
        risk_level=trust.ui_risk_level,  # type: ignore[arg-type]
        recommendation=decision.ui_recommendation,  # type: ignore[arg-type]
        verdict_en=verdict["verdict_en"],
        verdict_ar=verdict["verdict_ar"],
        summary_en=verdict["summary_en"],
        summary_ar=verdict["summary_ar"],
        factors=risk_factors or [to_risk_factor(e) for e in entries[:1]],
        data_sources=[
            f"JOFS account/balance/beneficiary/transaction history ({jofs.mode} mode)",
            "PostgreSQL account & transaction history",
            f"{prediction.model_name} fraud model (v{prediction.model_version})",
            "SHAP explainability",
        ],
        fraud_probability=prediction.calibrated_probability,
        trust_score=trust.trust_score,
        risk_category=trust.risk_category,  # type: ignore[arg-type]
        recommended_action=decision.recommended_action,  # type: ignore[arg-type]
        model_name=prediction.model_name,
        model_version=prediction.model_version,
        decision_threshold=prediction.threshold,
        protective_factors=protective_factors,
        processing_time_ms=processing_time_ms,
        created_at=now,
        account_balance=balance["available_balance"] if balance else None,
        funds_available=funds_available,
        beneficiary_verified=normalized_beneficiary.verified if normalized_beneficiary else None,
        provenance=provenance,
    )
