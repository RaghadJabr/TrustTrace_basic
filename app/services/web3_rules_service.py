from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from ..schemas import RiskAssessment, RiskFactor, Web3RiskRequest


class Web3RuleEngine:
    """Hand-authored rule engine for the Web3 approval flow.

    Out of scope for this iteration: the trained Web3 Random Forest model +
    SHAP bundle (see app/ml/traditional/service.py for the traditional
    equivalent, which *is* wired to a real trained model). This class keeps
    the Web3 tab of the demo functional with transparent, clearly-labelled
    demonstration rules until that integration lands.
    """

    def __init__(self) -> None:
        data_path = Path(__file__).resolve().parent.parent / "data" / "demo_data.json"
        self.demo_data: dict[str, Any] = json.loads(data_path.read_text(encoding="utf-8"))

    @staticmethod
    def _factor(code: str, severity: str, points: int, en: str, ar: str) -> RiskFactor:
        return RiskFactor(code=code, severity=severity, points=points, message_en=en, message_ar=ar)  # type: ignore[arg-type]

    @staticmethod
    def _finalize(score: int, factors: list[RiskFactor], data_sources: list[str]) -> RiskAssessment:
        score = max(0, min(100, score))
        if score >= 70:
            level, recommendation = "high", "cancel"
            verdict_en, verdict_ar = "Warning — suspicious payment", "تحذير — عملية دفع مشبوهة"
            summary_en = "Cancel the payment and verify the recipient through a trusted channel."
            summary_ar = "ألغِ عملية الدفع وتحقق من المستفيد عبر قناة موثوقة."
        elif score >= 40:
            level, recommendation = "review", "review"
            verdict_en, verdict_ar = "Review required", "تحتاج العملية إلى مراجعة"
            summary_en = "Pause and review the highlighted risks before continuing."
            summary_ar = "توقف وراجع عوامل الخطر الموضحة قبل المتابعة."
        else:
            level, recommendation = "low", "continue"
            verdict_en, verdict_ar = "Verified — low risk", "تم التحقق — مخاطر منخفضة"
            summary_en = "No major fraud indicators were detected in this assessment."
            summary_ar = "لم يتم اكتشاف مؤشرات احتيال رئيسية في هذا التقييم."

        return RiskAssessment(
            assessment_id=f"TT-{uuid.uuid4().hex[:8].upper()}",
            correlation_id=str(uuid.uuid4()),
            payment_type="web3",
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

    async def assess(self, request: Web3RiskRequest) -> RiskAssessment:
        contract = self.demo_data["web3_contracts"].get(
            request.contract_address,
            {"verified": False, "age_days": 0, "scam_reports": 0, "connected_risky_wallets": 0},
        )
        score = 0
        factors: list[RiskFactor] = []

        if not contract.get("verified", False):
            score += 20
            factors.append(self._factor(
                "UNVERIFIED_CONTRACT", "high", 20,
                "The smart contract is not verified.", "العقد الذكي غير موثق.",
            ))

        if contract.get("age_days", 0) < 7:
            score += 15
            factors.append(self._factor(
                "NEW_CONTRACT", "medium", 15,
                "The smart contract was deployed very recently.", "تم نشر العقد الذكي مؤخراً.",
            ))

        if request.approval_limit == "unlimited":
            score += 30
            factors.append(self._factor(
                "UNLIMITED_APPROVAL", "high", 30,
                f"The contract requests unlimited access to the user's {request.token_symbol}.",
                f"يطلب العقد وصولاً غير محدود إلى {request.token_symbol} الخاص بالمستخدم.",
            ))

        total_reports = int(contract.get("scam_reports", 0)) + request.wallet_scam_reports
        if total_reports > 0:
            score += 25
            factors.append(self._factor(
                "SCAM_REPORTS", "high", 25,
                "The wallet or contract is linked to previous scam reports.",
                "المحفظة أو العقد مرتبطان ببلاغات احتيال سابقة.",
            ))

        if contract.get("connected_risky_wallets", 0) > 0 or request.suspicious_network:
            score += 20
            factors.append(self._factor(
                "SUSPICIOUS_NETWORK", "high", 20,
                "The contract is connected to a suspicious wallet network.",
                "العقد مرتبط بشبكة محافظ مشبوهة.",
            ))

        if not factors:
            factors.append(self._factor(
                "VERIFIED_CONTRACT", "low", 0,
                "The contract is verified and no major scam indicators were detected.",
                "العقد موثق ولم يتم اكتشاف مؤشرات احتيال رئيسية.",
            ))

        return self._finalize(
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
