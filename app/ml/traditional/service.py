from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
import shap

from ..interfaces import ExplanationResult, FeatureContribution, FraudModelService, PredictionResult

ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"
MISSING_SENTINEL = "__MISSING__"
UNKNOWN_SENTINEL = "__UNKNOWN__"


class TraditionalFraudModelService(FraudModelService):
    """Serves the trained LightGBM traditional-payment fraud model.

    Loads the exact artifacts produced during training
    (trusttrace_lightgbm_model.txt + trusttrace_lightgbm_support.joblib) once
    at process start, and encodes inference-time features using the *same*
    feature order, numeric/categorical split and category vocabularies that
    were captured in the support bundle at training time -- this is what
    prevents training-serving skew.
    """

    def __init__(self) -> None:
        support = joblib.load(ARTIFACTS_DIR / "trusttrace_lightgbm_support.joblib")
        metadata = json.loads((ARTIFACTS_DIR / "best_model_metadata.json").read_text())

        self.model_name: str = support["model_name"]
        self.model_version: str = "1.0.0"
        self.schema: dict[str, Any] = support["schema"]
        self.calibrator = support["calibrator"]
        self.threshold: float = support["threshold"]
        self.training_metrics: dict[str, Any] = metadata

        self.booster = lgb.Booster(model_file=str(ARTIFACTS_DIR / "trusttrace_lightgbm_model.txt"))
        self._explainer = shap.TreeExplainer(self.booster)

    def validate_feature_contract(self, features: dict) -> None:
        """Explicit guard: the model input must contain exactly the 31 features
        captured at training time, nothing missing and nothing unexpected silently
        dropped. Raises ValueError naming the discrepancy."""

        expected = set(self.schema["model_features"])
        provided = set(features.keys())
        missing = sorted(expected - provided)
        unexpected = sorted(provided - expected)

        if missing or unexpected:
            parts = []
            if missing:
                parts.append(f"missing: {missing}")
            if unexpected:
                parts.append(f"unexpected: {unexpected}")
            raise ValueError(
                f"Feature contract violation ({len(provided)} provided, "
                f"{len(expected)} expected) -- " + "; ".join(parts)
            )

    def _to_frame(self, features: dict) -> pd.DataFrame:
        self.validate_feature_contract(features)
        row = {name: features[name] for name in self.schema["model_features"]}
        frame = pd.DataFrame([row])[self.schema["model_features"]]

        for column in self.schema["categorical_features"]:
            levels: list[str] = self.schema["category_levels"][column]
            value = frame[column].iloc[0]
            if value is None or (isinstance(value, float) and np.isnan(value)):
                value = MISSING_SENTINEL
            elif value not in levels:
                value = UNKNOWN_SENTINEL
            frame[column] = pd.Categorical([value], categories=levels)

        for column in self.schema["numerical_features"]:
            frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(0.0)

        return frame

    def predict(self, features: dict) -> PredictionResult:
        frame = self._to_frame(features)
        raw_probability = float(self.booster.predict(frame)[0])
        calibrated_probability = float(
            self.calibrator.predict_proba(np.array([[raw_probability]]))[0, 1]
        )
        predicted_class = "fraud" if calibrated_probability >= self.threshold else "legitimate"

        return PredictionResult(
            model_name=self.model_name,
            model_version=self.model_version,
            raw_probability=raw_probability,
            calibrated_probability=calibrated_probability,
            threshold=self.threshold,
            predicted_class=predicted_class,
        )

    def explain(self, features: dict) -> ExplanationResult:
        frame = self._to_frame(features)
        shap_values = self._explainer.shap_values(frame)
        if isinstance(shap_values, list):
            shap_values = shap_values[1]

        expected_value = self._explainer.expected_value
        if isinstance(expected_value, (list, np.ndarray)):
            expected_value = expected_value[1]

        contributions = [
            FeatureContribution(
                feature_name=name,
                feature_value=frame[name].iloc[0],
                shap_value=float(value),
            )
            for name, value in zip(self.schema["model_features"], shap_values[0])
        ]
        contributions.sort(key=lambda c: abs(c.shap_value), reverse=True)

        return ExplanationResult(contributions=contributions, base_value=float(expected_value))

    def health_check(self) -> dict:
        return {
            "status": "ok",
            "model_name": self.model_name,
            "model_version": self.model_version,
            "threshold": self.threshold,
            "feature_count": len(self.schema["model_features"]),
            "training_roc_auc": self.training_metrics.get("roc_auc"),
        }
