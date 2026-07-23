function analyzeTraditionalPayment({
    amount,
    availableBalance,
    averageTransactionAmount,
    merchant,
    device,
    countryCode,
}) {
    let riskScore = 0;
    const reasons = [];

    function addReason({
        code,
        featureName,
        featureValue,
        score,
        severity,
        descriptionEn,
        descriptionAr,
    }) {
        riskScore += score;

        reasons.push({
            code,
            featureName,
            featureValue,
            scoreContribution: score,
            importance: Number((score / 100).toFixed(5)),
            severity,
            descriptionEn,
            descriptionAr,
        });
    }

    // Merchant checks
    if (merchant.blacklisted) {
        addReason({
            code: "MERCHANT_BLACKLISTED",
            featureName: "merchant.blacklisted",
            featureValue: true,
            score: 40,
            severity: "critical",
            descriptionEn:
                "The merchant appears in a known fraud-intelligence list.",
            descriptionAr:
                "يظهر التاجر في قائمة معروفة لمعلومات الاحتيال.",
        });
    }

    if (!merchant.verified) {
        addReason({
            code: "MERCHANT_NOT_VERIFIED",
            featureName: "merchant.verified",
            featureValue: false,
            score: 15,
            severity: "high",
            descriptionEn: "The merchant has not been verified.",
            descriptionAr: "لم يتم التحقق من التاجر.",
        });
    }

    if (Number(merchant.reputation_score) < 30) {
        addReason({
            code: "LOW_MERCHANT_REPUTATION",
            featureName: "merchant.reputation_score",
            featureValue: Number(merchant.reputation_score),
            score: 20,
            severity: "high",
            descriptionEn: "The merchant has a low reputation score.",
            descriptionAr: "يمتلك التاجر درجة سمعة منخفضة.",
        });
    }

    // Device checks
    if (!device.trusted) {
        addReason({
            code: "UNTRUSTED_DEVICE",
            featureName: "device.trusted",
            featureValue: false,
            score: 15,
            severity: "high",
            descriptionEn:
                "The payment was initiated from a new or untrusted device.",
            descriptionAr:
                "تمت محاولة الدفع من جهاز جديد أو غير موثوق.",
        });
    }

    // Location check
    if (
        device.country_code &&
        countryCode &&
        device.country_code !== countryCode
    ) {
        addReason({
            code: "LOCATION_MISMATCH",
            featureName: "transaction.country_code",
            featureValue: countryCode,
            score: 10,
            severity: "medium",
            descriptionEn:
                "The payment location differs from the device's normal location.",
            descriptionAr:
                "يختلف موقع الدفع عن الموقع المعتاد للجهاز.",
        });
    }

    // Balance check
    if (
        Number(availableBalance) > 0 &&
        Number(amount) > Number(availableBalance) * 0.5
    ) {
        addReason({
            code: "HIGH_BALANCE_PERCENTAGE",
            featureName: "transaction.amount",
            featureValue: Number(amount),
            score: 15,
            severity: "medium",
            descriptionEn:
                "The payment uses more than half of the available balance.",
            descriptionAr:
                "تستخدم الدفعة أكثر من نصف الرصيد المتاح.",
        });
    }

    // Behavioural amount check
    if (
        Number(averageTransactionAmount) > 0 &&
        Number(amount) > Number(averageTransactionAmount) * 3
    ) {
        addReason({
            code: "UNUSUAL_AMOUNT",
            featureName: "transaction.amount",
            featureValue: Number(amount),
            score: 20,
            severity: "high",
            descriptionEn:
                "The payment amount is much higher than the customer's usual payments.",
            descriptionAr:
                "مبلغ الدفعة أعلى بكثير من دفعات العميل المعتادة.",
        });
    }

    riskScore = Math.min(riskScore, 100);
    const trustScore = 100 - riskScore;
    const fraudProbability = Number((riskScore / 100).toFixed(5));

    let riskLevel;
    let recommendedAction;

    if (riskScore < 30) {
        riskLevel = "low";
        recommendedAction = "allow";
    } else if (riskScore < 60) {
        riskLevel = "medium";
        recommendedAction = "review";
    } else if (riskScore < 80) {
        riskLevel = "high";
        recommendedAction = "review";
    } else {
        riskLevel = "critical";
        recommendedAction = "cancel";
    }

    return {
        riskScore,
        trustScore,
        fraudProbability,
        riskLevel,
        recommendedAction,
        reasons,
    };
}

module.exports = {
    analyzeTraditionalPayment,
};