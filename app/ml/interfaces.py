from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class PredictionResult:
    model_name: str
    model_version: str
    raw_probability: float
    calibrated_probability: float
    threshold: float
    predicted_class: str


@dataclass
class FeatureContribution:
    feature_name: str
    feature_value: object
    shap_value: float


@dataclass
class ExplanationResult:
    contributions: list[FeatureContribution] = field(default_factory=list)
    base_value: float = 0.0
    explanation_version: str = "1.0.0"


class FraudModelService(ABC):
    """Model-serving interface. Keeps API/service code independent of any
    specific ML library (LightGBM today, potentially others later)."""

    @abstractmethod
    def predict(self, features: dict) -> PredictionResult: ...

    @abstractmethod
    def explain(self, features: dict) -> ExplanationResult: ...

    @abstractmethod
    def health_check(self) -> dict: ...
