import asyncio

from app.jofs_adapter import JOFSAdapter
from app.models import TraditionalRiskRequest, Web3RiskRequest
from app.risk_engine import RiskEngine


engine = RiskEngine(JOFSAdapter())


def test_safe_traditional_payment_is_low_risk():
    result = asyncio.run(
        engine.assess_traditional(
            TraditionalRiskRequest(
                account_id="ACC-1001",
                beneficiary_id="BEN-001",
                amount=89,
                currency="JOD",
                merchant="Noon Jordan",
                domain="www.noon.com",
                device_id="LEEN-IP15",
                location="Amman",
            )
        )
    )
    assert result.risk_level == "low"
    assert result.recommendation == "continue"


def test_suspicious_traditional_payment_is_high_risk():
    result = asyncio.run(
        engine.assess_traditional(
            TraditionalRiskRequest(
                account_id="ACC-1001",
                beneficiary_id="BEN-777",
                amount=650,
                currency="JOD",
                merchant="Fast Visa Approval",
                domain="visa-fast-approval.example",
                device_id="UNKNOWN-DEVICE",
                location="Unknown",
                rapid_attempts=4,
            )
        )
    )
    assert result.risk_level == "high"
    assert result.recommendation == "cancel"
    assert result.risk_score >= 70


def test_unlimited_web3_approval_is_high_risk():
    result = asyncio.run(
        engine.assess_web3(
            Web3RiskRequest(
                wallet_address="0xLEEN",
                contract_address="0xBAD0000000000000000000000000000000000777",
                approval_limit="unlimited",
                wallet_scam_reports=5,
                suspicious_network=True,
            )
        )
    )
    assert result.risk_level == "high"
    assert any(f.code == "UNLIMITED_APPROVAL" for f in result.factors)
