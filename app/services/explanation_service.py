from __future__ import annotations

from dataclasses import dataclass

from ..ml.interfaces import FeatureContribution
from ..schemas import RiskFactor

FEATURE_DISPLAY_NAMES: dict[str, tuple[str, str]] = {
    "transaction_amount": ("Transaction amount", "مبلغ العملية"),
    "transaction_amount_bin": ("Transaction amount range", "نطاق مبلغ العملية"),
    "avg_amount_deviation_sigma": ("Deviation from usual spending", "الانحراف عن الإنفاق المعتاد"),
    "merchant_category": ("Merchant category", "فئة التاجر"),
    "merchant_risk_score": ("Merchant risk rating", "تصنيف مخاطر التاجر"),
    "merchant_category_vs_history": ("History with this merchant type", "السجل مع هذا النوع من التجار"),
    "geo_velocity_kmh": ("Implied travel speed", "سرعة الانتقال الضمنية"),
    "geo_velocity_bin": ("Travel-speed plausibility", "معقولية سرعة الانتقال"),
    "geo_distance_km": ("Distance from usual location", "المسافة عن الموقع المعتاد"),
    "geo_distance_bin": ("Location distance range", "نطاق مسافة الموقع"),
    "merchant_location": ("Merchant location", "موقع التاجر"),
    "country_consistency": ("Country consistency", "اتساق الدولة"),
    "ip_address_type": ("Connection type", "نوع الاتصال"),
    "device_fingerprint_match": ("Device recognition", "التعرف على الجهاز"),
    "session_duration_sec": ("Session duration", "مدة الجلسة"),
    "session_duration_bin": ("Session pace", "وتيرة الجلسة"),
    "network_carrier_type": ("Network type", "نوع الشبكة"),
    "cards_on_device_30d": ("Cards used on this device (30d)", "بطاقات استُخدمت على الجهاز (٣٠ يوماً)"),
    "cvv_match_status": ("Card verification code match", "تطابق رمز التحقق من البطاقة"),
    "three_ds_auth_result": ("3-D Secure authentication result", "نتيجة مصادقة 3-D Secure"),
    "tokenization_used": ("Card data protection method", "طريقة حماية بيانات البطاقة"),
    "failed_attempts_before_success": ("Failed attempts before this payment", "محاولات فاشلة قبل هذه العملية"),
    "transaction_velocity_1h": ("Payment frequency (last hour)", "وتيرة الدفع (الساعة الأخيرة)"),
    "time_of_transaction": ("Time of transaction", "وقت العملية"),
    "account_credential_change_recency": ("Recent credential changes", "تغييرات حديثة على بيانات الحساب"),
    "card_present_cnp": ("Card presence", "حضور البطاقة"),
    "order_shipping_speed": ("Requested shipping speed", "سرعة الشحن المطلوبة"),
    "account_age_days": ("Account age", "عمر الحساب"),
    "segment": ("Customer segment", "شريحة العميل"),
    "customer_type": ("Customer type", "نوع العميل"),
    "log_transaction_amount": ("Transaction amount (log scale)", "مبلغ العملية (مقياس لوغاريتمي)"),
}

_RISK_OVERRIDES: dict[str, tuple[str, str]] = {
    "avg_amount_deviation_sigma": (
        "This amount is much higher than the customer's typical payments.",
        "هذا المبلغ أعلى بكثير من مدفوعات العميل المعتادة.",
    ),
    "merchant_category_vs_history": (
        "The customer has no prior history paying this type of merchant.",
        "لا يمتلك العميل سجلاً سابقاً للدفع لهذا النوع من التجار.",
    ),
    "device_fingerprint_match": (
        "The payment was initiated from a new or unrecognized device.",
        "تم بدء الدفع من جهاز جديد أو غير معروف.",
    ),
    "cvv_match_status": (
        "The card verification code (CVV) did not match.",
        "لم يتطابق رمز التحقق من البطاقة (CVV).",
    ),
    "three_ds_auth_result": (
        "3-D Secure authentication failed or was bypassed.",
        "فشلت مصادقة 3-D Secure أو تم تجاوزها.",
    ),
    "ip_address_type": (
        "The connection used a VPN, proxy, or datacenter network rather than a typical residential connection.",
        "استخدم الاتصال شبكة VPN أو وكيلاً أو مركز بيانات بدلاً من اتصال منزلي معتاد.",
    ),
    "transaction_velocity_1h": (
        "Several payment attempts happened in a short period of time.",
        "حدثت عدة محاولات دفع خلال فترة زمنية قصيرة.",
    ),
    "geo_velocity_bin": (
        "The transaction location changed faster than physically plausible travel allows.",
        "تغيّر موقع العملية بسرعة تفوق ما يسمح به السفر الطبيعي.",
    ),
    "geo_distance_km": (
        "This transaction is far from the customer's usual location.",
        "هذه العملية بعيدة عن الموقع المعتاد للعميل.",
    ),
    "account_credential_change_recency": (
        "The account's login credentials were changed recently.",
        "تم تغيير بيانات دخول الحساب مؤخراً.",
    ),
    "cards_on_device_30d": (
        "Many different cards have recently been used from this device.",
        "تم استخدام عدة بطاقات مختلفة من هذا الجهاز مؤخراً.",
    ),
    "failed_attempts_before_success": (
        "There were failed payment attempts immediately before this one.",
        "حدثت محاولات دفع فاشلة قبل هذه العملية مباشرة.",
    ),
    "tokenization_used": (
        "The raw card number was used instead of a secure token.",
        "تم استخدام رقم البطاقة مباشرة بدلاً من رمز آمن.",
    ),
    "order_shipping_speed": (
        "The order requested unusually fast shipping, a pattern often seen in card-testing fraud.",
        "طلب الشحن كان سريعاً بشكل غير معتاد، وهو نمط شائع في احتيال اختبار البطاقات.",
    ),
    "merchant_risk_score": (
        "The merchant carries an elevated risk rating.",
        "يحمل التاجر تصنيف مخاطر مرتفعاً.",
    ),
}

_PROTECTIVE_OVERRIDES: dict[str, tuple[str, str]] = {
    "cvv_match_status": (
        "The card verification code matched correctly.",
        "تطابق رمز التحقق من البطاقة بشكل صحيح.",
    ),
    "three_ds_auth_result": (
        "3-D Secure authentication passed successfully.",
        "نجحت مصادقة 3-D Secure.",
    ),
    "device_fingerprint_match": (
        "The payment came from a known, previously trusted device.",
        "جاءت العملية من جهاز معروف وموثوق سابقاً.",
    ),
    "merchant_category_vs_history": (
        "The customer regularly pays merchants of this type.",
        "يدفع العميل بانتظام لتجار من هذا النوع.",
    ),
    "avg_amount_deviation_sigma": (
        "This amount is consistent with the customer's usual spending.",
        "هذا المبلغ متوافق مع الإنفاق المعتاد للعميل.",
    ),
    "ip_address_type": (
        "The connection came from a typical residential network.",
        "جاء الاتصال من شبكة منزلية معتادة.",
    ),
}


@dataclass
class ExplanationEntry:
    feature_name: str
    feature_display_name: str
    feature_value: str
    shap_value: float
    impact_direction: str  # "risk" | "protective"
    importance_rank: int
    explanation_en: str
    explanation_ar: str


def _severity(abs_shap: float) -> str:
    if abs_shap >= 1.5:
        return "high"
    if abs_shap >= 0.5:
        return "medium"
    return "low"


def _fallback_sentence(display_en: str, display_ar: str, is_risk: bool) -> tuple[str, str]:
    if is_risk:
        return (
            f"{display_en} contributed to this transaction's elevated risk assessment.",
            f"ساهم عامل «{display_ar}» في رفع تقييم المخاطر لهذه العملية.",
        )
    return (
        f"{display_en} is consistent with expected, lower-risk behaviour.",
        f"عامل «{display_ar}» متوافق مع سلوك متوقع وأقل خطورة.",
    )


def build_explanations(
    contributions: list[FeatureContribution], top_n: int = 10
) -> list[ExplanationEntry]:
    entries: list[ExplanationEntry] = []

    for rank, contribution in enumerate(contributions[:top_n], start=1):
        display_en, display_ar = FEATURE_DISPLAY_NAMES.get(
            contribution.feature_name, (contribution.feature_name, contribution.feature_name)
        )
        is_risk = contribution.shap_value > 0
        overrides = _RISK_OVERRIDES if is_risk else _PROTECTIVE_OVERRIDES
        explanation_en, explanation_ar = overrides.get(
            contribution.feature_name, _fallback_sentence(display_en, display_ar, is_risk)
        )

        entries.append(
            ExplanationEntry(
                feature_name=contribution.feature_name,
                feature_display_name=display_en,
                feature_value=str(contribution.feature_value),
                shap_value=contribution.shap_value,
                impact_direction="risk" if is_risk else "protective",
                importance_rank=rank,
                explanation_en=explanation_en,
                explanation_ar=explanation_ar,
            )
        )

    return entries


def to_risk_factor(entry: ExplanationEntry) -> RiskFactor:
    abs_shap = abs(entry.shap_value)
    return RiskFactor(
        code=entry.feature_name.upper(),
        severity=_severity(abs_shap),  # type: ignore[arg-type]
        points=round(min(abs_shap * 15, 100)),
        message_en=entry.explanation_en,
        message_ar=entry.explanation_ar,
    )
