from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from .jofs_adapter import JOFSAdapter
from .models import (
    RiskAssessment,
    RiskFactor,
    TraditionalRiskRequest,
    Web3RiskRequest,
)


class RiskEngine:
    def __init__(self, jofs: JOFSAdapter) -> None:
        self.jofs = jofs
        data_path = Path(__file__).parent / "data" / "demo_data.json"
        self.demo_data: dict[str, Any] = json.loads(data_path.read_text(encoding="utf-8"))

    @staticmethod
    def _factor(
        code: str,
        severity: str,
        points: int,
        en: str,
        ar: str,
    ) -> RiskFactor:
        return RiskFactor(
            code=code,
            severity=severity,  # type: ignore[arg-type]
            points=points,
            message_en=en,
            message_ar=ar,
        )

    @staticmethod
    def _finalize(
        payment_type: str,
        score: int,
        factors: list[RiskFactor],
        data_sources: list[str],
    ) -> RiskAssessment:
        score = max(0, min(100, score))
        if score >= 70:
            level = "high"
            recommendation = "cancel"
            verdict_en = "Warning — suspicious payment"
            verdict_ar = "تحذير — عملية دفع مشبوهة"
            summary_en = "Cancel the payment and verify the recipient through a trusted channel."
            summary_ar = "ألغِ عملية الدفع وتحقق من المستفيد عبر قناة موثوقة."
        elif score >= 40:
            level = "review"
            recommendation = "review"
            verdict_en = "Review required"
            verdict_ar = "تحتاج العملية إلى مراجعة"
            summary_en = "Pause and review the highlighted risks before continuing."
            summary_ar = "توقف وراجع عوامل الخطر الموضحة قبل المتابعة."
        else:
            level = "low"
            recommendation = "continue"
            verdict_en = "Verified — low risk"
            verdict_ar = "تم التحقق — مخاطر منخفضة"
            summary_en = "No major fraud indicators were detected in this assessment."
            summary_ar = "لم يتم اكتشاف مؤشرات احتيال رئيسية في هذا التقييم."

        return RiskAssessment(
            assessment_id=f"TT-{uuid.uuid4().hex[:8].upper()}",
            payment_type=payment_type,  # type: ignore[arg-type]
            risk_score=score,
            risk_level=level,  # type: ignore[arg-type]
            recommendation=recommendation,  # type: ignore[arg-type]
            verdict_en=verdict_en,
            verdict_ar=verdict_ar,
            summary_en=summary_en,
            summary_ar=summary_ar,
            factors=sorted(factors, key=lambda f: f.points, reverse=True),
            data_sources=data_sources,
        )

    async def assess_traditional(self, request: TraditionalRiskRequest) -> RiskAssessment:
        transactions = await self.jofs.get_transactions(request.account_id)
        account = await self.jofs.get_account(request.account_id)
        beneficiary = await self.jofs.get_beneficiary(
            request.account_id, request.beneficiary_id
        )
        if account is None:
            raise ValueError("Account not found")
        if beneficiary is None:
            raise ValueError("Beneficiary not found")

        score = 0
        factors: list[RiskFactor] = []

        if beneficiary.get("previous_payments", 0) == 0:
            score += 15
            factors.append(
                self._factor(
                    "NEW_BENEFICIARY",
                    "medium",
                    15,
                    "This beneficiary has not received payments from this account before.",
                    "لم يسبق لهذا الحساب إرسال دفعات إلى هذا المستفيد.",
                )
            )

        debit_amounts = [
            float(transaction["transactionAmount"]["amount"])
            for transaction in transactions
            if transaction.get("transactionType") == "debit"
            and transaction.get("transactionAmount", {}).get("amount") is not None
        ]

        average = (
            sum(debit_amounts) / len(debit_amounts)
            if debit_amounts
            else 100.0
        )

        if request.amount >= average * 3:
            score += 20
            factors.append(
                self._factor(
                    "UNUSUAL_AMOUNT",
                    "high",
                    20,
                    "The amount is much higher than the customer's usual transfers.",
                    "المبلغ أعلى بكثير من التحويلات المعتادة للعميل.",
                )
            )
        elif request.amount >= average * 1.8:
            score += 10
            factors.append(
                self._factor(
                    "ELEVATED_AMOUNT",
                    "medium",
                    10,
                    "The amount is higher than the customer's typical transfer.",
                    "المبلغ أعلى من التحويل المعتاد للعميل.",
                )
            )

        if request.device_id not in account.get("trusted_devices", []):
            score += 10
            factors.append(
                self._factor(
                    "NEW_DEVICE",
                    "medium",
                    10,
                    "The payment request came from a device not previously trusted.",
                    "تم إرسال طلب الدفع من جهاز غير موثوق سابقاً.",
                )
            )

        if request.location not in account.get("usual_locations", []):
            score += 10
            factors.append(
                self._factor(
                    "UNUSUAL_LOCATION",
                    "medium",
                    10,
                    "The payment location differs from the customer's usual activity.",
                    "موقع الدفع مختلف عن النشاط المعتاد للعميل.",
                )
            )

        merchant = self.demo_data["merchant_profiles"].get(
            request.merchant,
            {"verified": False, "risk_level": "review", "known_scam_reports": 0},
        )
        if not merchant.get("verified", False):
            score += 20
            factors.append(
                self._factor(
                    "UNVERIFIED_MERCHANT",
                    "high",
                    20,
                    "The merchant could not be verified in the trusted merchant registry.",
                    "تعذر التحقق من التاجر ضمن سجل التجار الموثوقين.",
                )
            )
        if merchant.get("known_scam_reports", 0) > 0:
            score += 20
            factors.append(
                self._factor(
                    "MERCHANT_SCAM_REPORTS",
                    "high",
                    20,
                    "The merchant is linked to previous scam reports.",
                    "التاجر مرتبط ببلاغات احتيال سابقة.",
                )
            )

        domain = self.demo_data["domain_profiles"].get(
            request.domain,
            {"trusted": False, "age_days": 0, "phishing_reports": 0},
        )
        if not domain.get("trusted", False):
            score += 15
            factors.append(
                self._factor(
                    "UNTRUSTED_DOMAIN",
                    "high",
                    15,
                    "The payment domain is not in the trusted-domain registry.",
                    "نطاق الدفع غير موجود ضمن سجل النطاقات الموثوقة.",
                )
            )
        if domain.get("age_days", 0) < 14:
            score += 10
            factors.append(
                self._factor(
                    "NEW_DOMAIN",
                    "medium",
                    10,
                    "The website domain was registered very recently.",
                    "تم تسجيل نطاق الموقع مؤخراً.",
                )
            )
        if domain.get("phishing_reports", 0) > 0:
            score += 20
            factors.append(
                self._factor(
                    "PHISHING_REPORTS",
                    "high",
                    20,
                    "The website appears in phishing or scam intelligence records.",
                    "ظهر الموقع ضمن سجلات التصيد أو معلومات الاحتيال.",
                )
            )

        if request.rapid_attempts >= 3:
            score += 15
            factors.append(
                self._factor(
                    "RAPID_ATTEMPTS",
                    "high",
                    15,
                    "Several payment attempts were made within a short period.",
                    "تم إجراء عدة محاولات دفع خلال فترة قصيرة.",
                )
            )

        if not factors:
            factors.append(
                self._factor(
                    "NORMAL_BEHAVIOUR",
                    "low",
                    0,
                    "The payment is consistent with the customer's known behaviour.",
                    "عملية الدفع متوافقة مع السلوك المعروف للعميل.",
                )
            )

        return self._finalize(
            "traditional",
            score,
            factors,
            [
                "JOFS account context",
                "JOFS beneficiary context",
                "Merchant intelligence",
                "Website/domain intelligence",
                "Device and location signals",
                "Behavioural transaction rules",
            ],
        )

    async def assess_web3(self, request: Web3RiskRequest) -> RiskAssessment:
        contract = self.demo_data["web3_contracts"].get(
            request.contract_address,
            {
                "verified": False,
                "age_days": 0,
                "scam_reports": 0,
                "connected_risky_wallets": 0,
            },
        )
        score = 0
        factors: list[RiskFactor] = []

        if not contract.get("verified", False):
            score += 20
            factors.append(
                self._factor(
                    "UNVERIFIED_CONTRACT",
                    "high",
                    20,
                    "The smart contract is not verified.",
                    "العقد الذكي غير موثق.",
                )
            )

        if contract.get("age_days", 0) < 7:
            score += 15
            factors.append(
                self._factor(
                    "NEW_CONTRACT",
                    "medium",
                    15,
                    "The smart contract was deployed very recently.",
                    "تم نشر العقد الذكي مؤخراً.",
                )
            )

        if request.approval_limit == "unlimited":
            score += 30
            factors.append(
                self._factor(
                    "UNLIMITED_APPROVAL",
                    "high",
                    30,
                    f"The contract requests unlimited access to the user's {request.token_symbol}.",
                    f"يطلب العقد وصولاً غير محدود إلى {request.token_symbol} الخاص بالمستخدم.",
                )
            )

        total_reports = int(contract.get("scam_reports", 0)) + request.wallet_scam_reports
        if total_reports > 0:
            score += 25
            factors.append(
                self._factor(
                    "SCAM_REPORTS",
                    "high",
                    25,
                    "The wallet or contract is linked to previous scam reports.",
                    "المحفظة أو العقد مرتبطان ببلاغات احتيال سابقة.",
                )
            )

        if contract.get("connected_risky_wallets", 0) > 0 or request.suspicious_network:
            score += 20
            factors.append(
                self._factor(
                    "SUSPICIOUS_NETWORK",
                    "high",
                    20,
                    "The contract is connected to a suspicious wallet network.",
                    "العقد مرتبط بشبكة محافظ مشبوهة.",
                )
            )

        if not factors:
            factors.append(
                self._factor(
                    "VERIFIED_CONTRACT",
                    "low",
                    0,
                    "The contract is verified and no major scam indicators were detected.",
                    "العقد موثق ولم يتم اكتشاف مؤشرات احتيال رئيسية.",
                )
            )

        return self._finalize(
            "web3",
            score,
            factors,
            [
                "Blockchain transaction context",
                "Smart-contract verification",
                "Token approval permissions",
                "Wallet reputation",
                "Suspicious wallet-network intelligence",
            ],
        )
