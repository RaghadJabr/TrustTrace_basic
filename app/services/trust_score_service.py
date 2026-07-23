from __future__ import annotations

from dataclasses import dataclass

from ..core.config import get_decision_config


@dataclass
class TrustScoreResult:
    trust_score: int
    risk_category: str
    ui_risk_level: str


def compute_trust_score(fraud_probability: float) -> TrustScoreResult:
    """Trust Score = round((1 - fraud_probability) * 100), per spec section 4.
    Risk category bands are read from configuration (app/config/decision_thresholds.json)
    rather than hard-coded, so they can later be overridden per institution."""

    trust_score = round((1 - fraud_probability) * 100)
    trust_score = max(0, min(100, trust_score))

    for band in get_decision_config()["trust_score_bands"]:
        if band["min"] <= trust_score <= band["max"]:
            return TrustScoreResult(
                trust_score=trust_score,
                risk_category=band["risk_category"],
                ui_risk_level=band["ui_risk_level"],
            )

    # Bands in the config are expected to cover 0-100 contiguously.
    raise ValueError(f"No configured trust_score_band covers score {trust_score}")
