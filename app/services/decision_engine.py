from __future__ import annotations

from dataclasses import dataclass

from ..core.config import get_decision_config


@dataclass
class Decision:
    recommended_action: str
    ui_recommendation: str


def decide(risk_category: str) -> Decision:
    """Separates the business decision from the model's raw probability: the
    model produces fraud_probability, trust_score_service turns that into a
    risk_category, and this function -- driven entirely by configuration, not
    inference code -- turns the risk_category into a recommended action."""

    config = get_decision_config()
    recommended_action = config["recommended_action_by_category"][risk_category]
    ui_recommendation = config["ui_recommendation_by_action"][recommended_action]
    return Decision(recommended_action=recommended_action, ui_recommendation=ui_recommendation)
