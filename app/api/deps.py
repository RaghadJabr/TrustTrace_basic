from __future__ import annotations

from fastapi import Request

from ..integrations.open_finance.provider import JOFSAdapter
from ..ml.interfaces import FraudModelService
from ..services.web3_rules_service import Web3RuleEngine


def get_model_service(request: Request) -> FraudModelService:
    return request.app.state.traditional_model_service


def get_jofs(request: Request) -> JOFSAdapter:
    return request.app.state.jofs


def get_web3_engine(request: Request) -> Web3RuleEngine:
    return request.app.state.web3_engine
