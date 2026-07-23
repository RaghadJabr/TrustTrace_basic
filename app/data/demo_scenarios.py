"""Demo request payloads for the frontend's scenario dropdowns.

The traditional scenarios intentionally send a *full* TransactionSignals
payload (not just amount/merchant/domain) so the real LightGBM model and its
SHAP explanations actually differentiate "safe" from "suspicious" -- a thin
payload would just fall back to the neutral defaults in schemas.py and the
two scenarios would score almost identically.
"""

SCENARIOS: dict[str, dict] = {
    "traditional": {
        "safe": {
            "account_id": "ACC-1001",
            "beneficiary_id": "BEN-001",
            "amount": 55,
            "currency": "JOD",
            "merchant": "Noon Jordan",
            "domain": "www.noon.com",
            "device_id": "LEEN-IP15",
            "location": "Amman",
            "rapid_attempts": 0,
            "signals": {
                "cvv_match_status": "cvv2_match",
                "three_ds_auth_result": "frictionless_pass",
                "tokenization_used": "network_token_wallet",
                "card_present_cnp": "cnp_online",
                "ip_address_type": "residential",
                "device_fingerprint_match": "known_device",
                "network_carrier_type": "wifi",
                "session_duration_sec": 50,
                "geo_velocity_kmh": 4,
                "geo_distance_km": 1.5,
                "merchant_location": "home_city",
                "country_consistency": "same_country",
                "cards_on_device_30d": 1,
                "failed_attempts_before_success": 0,
                "transaction_velocity_1h": "within_normal",
                "account_credential_change_recency": "no_recent_change",
                "order_shipping_speed": "standard",
                "merchant_category": "retail",
                "customer_type": "customer_based",
            },
        },
        "suspicious": {
            "account_id": "ACC-1001",
            "beneficiary_id": "BEN-777",
            "amount": 2450,
            "currency": "JOD",
            "merchant": "Fast Visa Approval",
            "domain": "visa-fast-approval.example",
            "device_id": "UNKNOWN-DEVICE-771",
            "location": "Unknown",
            "rapid_attempts": 4,
            "signals": {
                "cvv_match_status": "cvv2_mismatch",
                "three_ds_auth_result": "challenge_fail",
                "tokenization_used": "raw_pan_online",
                "card_present_cnp": "cnp_online",
                "ip_address_type": "vpn",
                "device_fingerprint_match": "new_device",
                "network_carrier_type": "datacenter_hosting",
                "session_duration_sec": 8,
                "geo_velocity_kmh": 1400,
                "geo_distance_km": 3200,
                "merchant_location": "foreign_far",
                "country_consistency": "new_country",
                "cards_on_device_30d": 7,
                "failed_attempts_before_success": 3,
                "transaction_velocity_1h": "burst_pattern",
                "account_credential_change_recency": "changed_within_24h",
                "order_shipping_speed": "overnight",
                "merchant_category": "crypto_giftcard",
                "customer_type": "customer_based",
            },
        },
    },
    "web3": {
        "safe": {
            "wallet_address": "0xLEEN000000000000000000000000000000000001",
            "contract_address": "0xSAFE000000000000000000000000000000000001",
            "network": "ethereum",
            "action": "token_approval",
            "token_symbol": "USDT",
            "approval_limit": "limited",
            "wallet_scam_reports": 0,
            "suspicious_network": False,
        },
        "suspicious": {
            "wallet_address": "0xLEEN000000000000000000000000000000000001",
            "contract_address": "0xBAD0000000000000000000000000000000000777",
            "network": "ethereum",
            "action": "token_approval",
            "token_symbol": "USDT",
            "approval_limit": "unlimited",
            "wallet_scam_reports": 5,
            "suspicious_network": True,
        },
    },
}
