from __future__ import annotations

import math
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models.orm import Account, Merchant, Transaction
from ..schemas import TransactionSignals
from .jofs_normalization import NormalizedTransaction

# Bin edges below are a documented, reasonable heuristic: the training
# notebook that produced these bins was not provided to this integration, so
# exact training-time cut points are unknown. They only affect two low-
# importance categorical features (transaction_amount_bin, geo_velocity_bin
# rank 24th/16th of 31 by mean |SHAP|), so this assumption has limited effect
# on the assessment outcome.


def _amount_bin(amount: float) -> str:
    if amount < 50:
        return "low"
    if amount < 500:
        return "medium"
    if amount < 2000:
        return "high"
    return "very_high"


def _geo_velocity_bin(kmh: float) -> str:
    if kmh <= 120:
        return "normal"
    if kmh <= 900:
        return "fast"
    return "impossible"


def _geo_distance_bin(km: float) -> str:
    if km <= 5:
        return "same_location"
    if km <= 300:
        return "short"
    return "long"


def _session_duration_bin(seconds: float) -> str:
    if seconds < 5:
        return "bot_speed"
    if seconds < 30:
        return "very_fast"
    if seconds <= 180:
        return "normal"
    return "slow"


def _time_of_transaction(moment: datetime) -> str:
    hour = moment.astimezone(timezone.utc).hour
    if 6 <= hour < 12:
        return "morning_6_12"
    if 12 <= hour < 18:
        return "afternoon_12_18"
    if 18 <= hour < 24:
        return "evening_18_24"
    return "late_night_0_5"


def _merchant_risk_bucket(reputation_score: int) -> str:
    if reputation_score >= 80:
        return "low_risk"
    if reputation_score >= 50:
        return "medium_risk"
    if reputation_score >= 20:
        return "high_risk"
    return "very_high_risk"


def _segment_from_age(account_age_days: int) -> str:
    if account_age_days >= 365:
        return "A_established"
    if account_age_days >= 90:
        return "B_regular"
    if account_age_days >= 1:
        return "C_new"
    return "D_guest"


def _category_history_bucket(total_transactions: int, category_matches: int) -> str:
    if total_transactions == 0:
        return "no_history"
    if category_matches == 0:
        return "never_before_category"
    if category_matches >= 5:
        return "frequent_category"
    if category_matches >= 2:
        return "occasional_category"
    return "rare_category"


class TransactionHistory:
    """Real historical stats used to compute avg_amount_deviation_sigma and
    merchant_category_vs_history -- no hand-waving, these are actual prior
    transactions, merged from whichever sources are actually available:

    - Postgres: every transaction TrustTrace has itself assessed. Carries a
      merchant link, so it's the only source that can contribute to
      merchant_category_vs_history.
    - JOFS (optional): the account's real transaction history, when supplied.
      JOFS has no merchant-category taxonomy, so it can only widen the
      account-level amount baseline (avg_amount_deviation_sigma), not the
      category-match count. Deduplicated against Postgres via
      external_transaction_id (stored in Transaction.metadata_json) so a
      transaction already persisted locally isn't double-counted.
    """

    def __init__(
        self,
        db: Session,
        account: Account,
        merchant: Merchant,
        jofs_transactions: list[NormalizedTransaction] | None = None,
    ) -> None:
        local_rows = db.scalars(select(Transaction).where(Transaction.account_id == account.id)).all()
        local_amounts = [float(row.amount) for row in local_rows]
        local_external_ids = {
            row.metadata_json.get("external_transaction_id")
            for row in local_rows
            if row.metadata_json and row.metadata_json.get("external_transaction_id")
        }

        jofs_amounts = [
            t.amount
            for t in (jofs_transactions or [])
            if t.external_transaction_id not in local_external_ids
        ]

        self.amounts: list[float] = local_amounts + jofs_amounts
        self.total_transactions = len(self.amounts)
        self.jofs_transaction_count = len(jofs_amounts)

        self.category_matches = db.scalar(
            select(func.count())
            .select_from(Transaction)
            .join(Merchant, Transaction.merchant_id == Merchant.id)
            .where(Transaction.account_id == account.id, Merchant.category == merchant.category)
        ) or 0

    @property
    def mean_amount(self) -> float:
        return sum(self.amounts) / len(self.amounts) if self.amounts else 0.0

    @property
    def stdev_amount(self) -> float:
        if len(self.amounts) < 2:
            return 0.0
        mean = self.mean_amount
        variance = sum((a - mean) ** 2 for a in self.amounts) / (len(self.amounts) - 1)
        return math.sqrt(variance)


def build_traditional_features(
    *,
    amount: float,
    account: Account,
    merchant: Merchant,
    signals: TransactionSignals,
    history: TransactionHistory,
    now: datetime | None = None,
) -> dict:
    now = now or datetime.now(timezone.utc)

    account_age_days = max(0, (now - account.created_at).days)

    if history.stdev_amount > 0:
        avg_amount_deviation_sigma = (amount - history.mean_amount) / history.stdev_amount
    else:
        avg_amount_deviation_sigma = 0.0

    merchant_category = merchant.category or signals.merchant_category
    merchant_risk_score = signals.merchant_risk_score or _merchant_risk_bucket(merchant.reputation_score)
    segment = signals.segment or _segment_from_age(account_age_days)

    return {
        "transaction_amount": amount,
        "transaction_amount_bin": _amount_bin(amount),
        "avg_amount_deviation_sigma": avg_amount_deviation_sigma,
        "merchant_category": merchant_category,
        "merchant_risk_score": merchant_risk_score,
        "merchant_category_vs_history": _category_history_bucket(
            history.total_transactions, history.category_matches
        ),
        "geo_velocity_kmh": signals.geo_velocity_kmh,
        "geo_velocity_bin": _geo_velocity_bin(signals.geo_velocity_kmh),
        "geo_distance_km": signals.geo_distance_km,
        "geo_distance_bin": _geo_distance_bin(signals.geo_distance_km),
        "merchant_location": signals.merchant_location,
        "country_consistency": signals.country_consistency,
        "ip_address_type": signals.ip_address_type,
        "device_fingerprint_match": signals.device_fingerprint_match,
        "session_duration_sec": signals.session_duration_sec,
        "session_duration_bin": _session_duration_bin(signals.session_duration_sec),
        "network_carrier_type": signals.network_carrier_type,
        "cards_on_device_30d": signals.cards_on_device_30d,
        "cvv_match_status": signals.cvv_match_status,
        "three_ds_auth_result": signals.three_ds_auth_result,
        "tokenization_used": signals.tokenization_used,
        "failed_attempts_before_success": signals.failed_attempts_before_success,
        "transaction_velocity_1h": signals.transaction_velocity_1h,
        "time_of_transaction": _time_of_transaction(now),
        "account_credential_change_recency": signals.account_credential_change_recency,
        "card_present_cnp": signals.card_present_cnp,
        "order_shipping_speed": signals.order_shipping_speed,
        "account_age_days": account_age_days,
        "segment": segment,
        "customer_type": signals.customer_type,
        # log1p is the standard, monotonic, zero-safe choice; the exact training
        # formula wasn't available (no traditional training notebook was supplied,
        # only the trained artifacts), and this feature ranks 25th/31 by mean |SHAP|.
        "log_transaction_amount": math.log1p(amount),
    }
