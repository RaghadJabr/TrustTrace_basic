from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.schemas import TransactionSignals
from app.services.feature_service import (
    _amount_bin,
    _category_history_bucket,
    _geo_distance_bin,
    _geo_velocity_bin,
    _segment_from_age,
    _session_duration_bin,
    build_traditional_features,
)


def test_amount_bin_boundaries():
    assert _amount_bin(10) == "low"
    assert _amount_bin(200) == "medium"
    assert _amount_bin(1000) == "high"
    assert _amount_bin(5000) == "very_high"


def test_geo_velocity_bin_flags_impossible_travel():
    assert _geo_velocity_bin(50) == "normal"
    assert _geo_velocity_bin(500) == "fast"
    assert _geo_velocity_bin(2000) == "impossible"


def test_geo_distance_bin():
    assert _geo_distance_bin(1) == "same_location"
    assert _geo_distance_bin(50) == "short"
    assert _geo_distance_bin(1000) == "long"


def test_session_duration_bin_flags_bot_speed():
    assert _session_duration_bin(1) == "bot_speed"
    assert _session_duration_bin(10) == "very_fast"
    assert _session_duration_bin(60) == "normal"
    assert _session_duration_bin(600) == "slow"


def test_segment_from_age():
    assert _segment_from_age(0) == "D_guest"
    assert _segment_from_age(30) == "C_new"
    assert _segment_from_age(200) == "B_regular"
    assert _segment_from_age(400) == "A_established"


def test_category_history_bucket():
    assert _category_history_bucket(0, 0) == "no_history"
    assert _category_history_bucket(5, 0) == "never_before_category"
    assert _category_history_bucket(5, 1) == "rare_category"
    assert _category_history_bucket(5, 3) == "occasional_category"
    assert _category_history_bucket(10, 8) == "frequent_category"


def test_build_traditional_features_produces_all_31_model_inputs():
    now = datetime.now(timezone.utc)
    account = SimpleNamespace(created_at=now - timedelta(days=100))
    merchant = SimpleNamespace(category="retail", reputation_score=80)
    signals = TransactionSignals()
    history = SimpleNamespace(
        total_transactions=4,
        category_matches=2,
        mean_amount=60.0,
        stdev_amount=10.0,
    )

    features = build_traditional_features(
        amount=200.0, account=account, merchant=merchant, signals=signals, history=history, now=now
    )

    expected_keys = {
        "transaction_amount", "transaction_amount_bin", "avg_amount_deviation_sigma",
        "merchant_category", "merchant_risk_score", "merchant_category_vs_history",
        "geo_velocity_kmh", "geo_velocity_bin", "geo_distance_km", "geo_distance_bin",
        "merchant_location", "country_consistency", "ip_address_type", "device_fingerprint_match",
        "session_duration_sec", "session_duration_bin", "network_carrier_type",
        "cards_on_device_30d", "cvv_match_status", "three_ds_auth_result", "tokenization_used",
        "failed_attempts_before_success", "transaction_velocity_1h", "time_of_transaction",
        "account_credential_change_recency", "card_present_cnp", "order_shipping_speed",
        "account_age_days", "segment", "customer_type", "log_transaction_amount",
    }
    assert set(features.keys()) == expected_keys
    assert features["account_age_days"] == 100
    assert features["avg_amount_deviation_sigma"] == (200.0 - 60.0) / 10.0
    assert features["merchant_category_vs_history"] == "occasional_category"


def test_avg_amount_deviation_sigma_is_neutral_with_no_history():
    now = datetime.now(timezone.utc)
    account = SimpleNamespace(created_at=now)
    merchant = SimpleNamespace(category="retail", reputation_score=50)
    history = SimpleNamespace(total_transactions=0, category_matches=0, mean_amount=0.0, stdev_amount=0.0)

    features = build_traditional_features(
        amount=100.0,
        account=account,
        merchant=merchant,
        signals=TransactionSignals(),
        history=history,
        now=now,
    )
    assert features["avg_amount_deviation_sigma"] == 0.0
