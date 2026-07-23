const express = require("express");
const pool = require("../db");
const {
    analyzeTraditionalPayment,
} = require("../services/riskEngine");

const router = express.Router();

/*
GET /api/assessments/traditional

Reads traditional payment assessments from PostgreSQL.
*/
router.get("/traditional", async (req, res) => {
    try {
        const requestedLimit = Number.parseInt(req.query.limit, 10) || 20;
        const limit = Math.min(Math.max(requestedLimit, 1), 100);

        const result = await pool.query(
            `
      SELECT *
      FROM traditional_transaction_risk_view
      ORDER BY assessed_at DESC NULLS LAST
      LIMIT $1
      `,
            [limit]
        );

        res.status(200).json({
            count: result.rows.length,
            data: result.rows,
        });
    } catch (error) {
        console.error("Traditional assessments error:", error);

        res.status(500).json({
            message: "Could not retrieve traditional-payment assessments.",
            error: error.message,
        });
    }
});

/*
GET /api/assessments/web3

Reads blockchain/Web3 assessments from PostgreSQL.
*/
router.get("/web3", async (req, res) => {
    try {
        const requestedLimit = Number.parseInt(req.query.limit, 10) || 20;
        const limit = Math.min(Math.max(requestedLimit, 1), 100);

        const result = await pool.query(
            `
      SELECT *
      FROM web3_transaction_risk_view
      ORDER BY assessed_at DESC NULLS LAST
      LIMIT $1
      `,
            [limit]
        );

        res.status(200).json({
            count: result.rows.length,
            data: result.rows,
        });
    } catch (error) {
        console.error("Web3 assessments error:", error);

        res.status(500).json({
            message: "Could not retrieve Web3 assessments.",
            error: error.message,
        });
    }
});
/*
POST /api/assessments/traditional

Creates and analyzes a traditional card payment.
*/
router.post("/traditional", async (req, res) => {
    const {
        externalAccountId,
        merchantName,
        merchantDomain,
        deviceFingerprint,
        amount,
        currency = "JOD",
        countryCode = "JO",
        city = "Amman",
    } = req.body;

    if (
        !externalAccountId ||
        !merchantDomain ||
        !deviceFingerprint ||
        amount === undefined
    ) {
        return res.status(400).json({
            message:
                "externalAccountId, merchantDomain, deviceFingerprint, and amount are required.",
        });
    }

    const numericAmount = Number(amount);

    if (!Number.isFinite(numericAmount) || numericAmount <= 0) {
        return res.status(400).json({
            message: "amount must be a positive number.",
        });
    }

    const client = await pool.connect();

    try {
        await client.query("BEGIN");

        /*
        1. Find the source account.
        Later, this account information will come from JOFS.
        */
        const accountResult = await client.query(
            `
      SELECT
        a.account_id,
        a.user_id,
        a.available_balance,
        a.currency
      FROM accounts a
      WHERE a.external_account_id = $1
      LIMIT 1
      `,
            [externalAccountId]
        );

        if (accountResult.rows.length === 0) {
            await client.query("ROLLBACK");

            return res.status(404).json({
                message: "Account not found.",
            });
        }

        const account = accountResult.rows[0];

        /*
        2. Find or create the merchant.
        */
        let merchantResult = await client.query(
            `
      SELECT *
      FROM merchants
      WHERE merchant_domain = $1
      LIMIT 1
      `,
            [merchantDomain]
        );

        if (merchantResult.rows.length === 0) {
            merchantResult = await client.query(
                `
        INSERT INTO merchants (
          merchant_name,
          merchant_domain,
          country_code,
          reputation_score,
          verified,
          blacklisted
        )
        VALUES ($1, $2, $3, 50, FALSE, FALSE)
        RETURNING *
        `,
                [
                    merchantName || "Unknown Merchant",
                    merchantDomain,
                    countryCode,
                ]
            );
        }

        const merchant = merchantResult.rows[0];

        /*
        3. Find or create the device.
        */
        let deviceResult = await client.query(
            `
      SELECT *
      FROM devices
      WHERE device_fingerprint = $1
      LIMIT 1
      `,
            [deviceFingerprint]
        );

        if (deviceResult.rows.length === 0) {
            deviceResult = await client.query(
                `
        INSERT INTO devices (
          user_id,
          device_fingerprint,
          device_type,
          operating_system,
          browser,
          country_code,
          city,
          trusted,
          reputation_score
        )
        VALUES (
          $1,
          $2,
          'unknown',
          'unknown',
          'unknown',
          $3,
          $4,
          FALSE,
          30
        )
        RETURNING *
        `,
                [
                    account.user_id,
                    deviceFingerprint,
                    countryCode,
                    city,
                ]
            );
        }

        const device = deviceResult.rows[0];

        /*
        4. Calculate the customer's historical average amount.
        */
        const historyResult = await client.query(
            `
      SELECT
        COALESCE(AVG(amount), 0) AS average_amount
      FROM transactions
      WHERE sender_account_id = $1
      `,
            [account.account_id]
        );

        const averageTransactionAmount =
            historyResult.rows[0].average_amount;

        /*
        5. Run TrustTrace risk analysis.
        */
        const riskResult = analyzeTraditionalPayment({
            amount: numericAmount,
            availableBalance: account.available_balance,
            averageTransactionAmount,
            merchant,
            device,
            countryCode,
        });

        /*
        6. Save the payment transaction.
        */
        const transactionResult = await client.query(
            `
      INSERT INTO transactions (
        sender_account_id,
        merchant_id,
        device_id,
        transaction_type,
        payment_channel,
        amount,
        currency,
        country_code,
        city,
        status,
        metadata
      )
      VALUES (
        $1,
        $2,
        $3,
        'card_payment',
        'card_checkout',
        $4,
        $5,
        $6,
        $7,
        'under_review',
        $8::jsonb
      )
      RETURNING *
      `,
            [
                account.account_id,
                merchant.merchant_id,
                device.device_id,
                numericAmount,
                currency,
                countryCode,
                city,
                JSON.stringify({
                    source: "trusttrace-node-demo",
                    merchantDomain,
                }),
            ]
        );

        const transaction = transactionResult.rows[0];

        /*
        7. Find the active model version.
        */
        const modelResult = await client.query(
            `
      SELECT model_version_id
      FROM model_versions
      WHERE active = TRUE
      ORDER BY created_at DESC
      LIMIT 1
      `
        );

        const modelVersionId =
            modelResult.rows.length > 0
                ? modelResult.rows[0].model_version_id
                : null;

        const summaryEn =
            riskResult.reasons.length > 0
                ? riskResult.reasons
                    .slice(0, 3)
                    .map((reason) => reason.descriptionEn)
                    .join(" ")
                : "No significant fraud indicators were detected.";

        const summaryAr =
            riskResult.reasons.length > 0
                ? riskResult.reasons
                    .slice(0, 3)
                    .map((reason) => reason.descriptionAr)
                    .join(" ")
                : "لم يتم اكتشاف مؤشرات احتيال مهمة.";

        /*
        8. Save the Trust Assessment.
        */
        const assessmentResult = await client.query(
            `
      INSERT INTO trust_assessments (
        transaction_id,
        model_version_id,
        trust_score,
        fraud_probability,
        risk_level,
        recommended_action,
        decision_source,
        explanation_summary_en,
        explanation_summary_ar
      )
      VALUES (
        $1,
        $2,
        $3,
        $4,
        $5,
        $6,
        'hybrid',
        $7,
        $8
      )
      RETURNING *
      `,
            [
                transaction.transaction_id,
                modelVersionId,
                riskResult.trustScore,
                riskResult.fraudProbability,
                riskResult.riskLevel,
                riskResult.recommendedAction,
                summaryEn,
                summaryAr,
            ]
        );

        const assessment = assessmentResult.rows[0];

        /*
        9. Save every explainable risk reason.
        */
        for (const reason of riskResult.reasons) {
            await client.query(
                `
        INSERT INTO risk_reasons (
          assessment_id,
          reason_code,
          feature_name,
          feature_value,
          importance,
          severity,
          description_en,
          description_ar
        )
        VALUES (
          $1,
          $2,
          $3,
          $4::jsonb,
          $5,
          $6,
          $7,
          $8
        )
        `,
                [
                    assessment.assessment_id,
                    reason.code,
                    reason.featureName,
                    JSON.stringify(reason.featureValue),
                    reason.importance,
                    reason.severity,
                    reason.descriptionEn,
                    reason.descriptionAr,
                ]
            );
        }

        /*
        10. Save the audit event.
        */
        await client.query(
            `
      INSERT INTO audit_logs (
        user_id,
        transaction_id,
        assessment_id,
        event_type,
        actor_type,
        actor_id,
        details
      )
      VALUES (
        $1,
        $2,
        $3,
        'assessment_completed',
        'system',
        'trusttrace-node-risk-engine',
        $4::jsonb
      )
      `,
            [
                account.user_id,
                transaction.transaction_id,
                assessment.assessment_id,
                JSON.stringify({
                    trustScore: riskResult.trustScore,
                    riskLevel: riskResult.riskLevel,
                    recommendedAction: riskResult.recommendedAction,
                }),
            ]
        );

        await client.query("COMMIT");

        return res.status(201).json({
            message: "Payment assessment completed.",
            transactionId: transaction.transaction_id,
            assessmentId: assessment.assessment_id,
            trustScore: riskResult.trustScore,
            fraudProbability: riskResult.fraudProbability,
            riskLevel: riskResult.riskLevel,
            recommendedAction: riskResult.recommendedAction,
            explanations: riskResult.reasons.map((reason) => ({
                code: reason.code,
                severity: reason.severity,
                descriptionEn: reason.descriptionEn,
                descriptionAr: reason.descriptionAr,
            })),
        });
    } catch (error) {
        await client.query("ROLLBACK");

        console.error("Traditional assessment failed:", error);

        return res.status(500).json({
            message: "The payment assessment could not be completed.",
            error: error.message,
        });
    } finally {
        client.release();
    }
});
module.exports = router;