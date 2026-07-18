from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .jofs_adapter import JOFSAdapter
from .models import RiskAssessment, TraditionalRiskRequest, Web3RiskRequest
from .risk_engine import RiskEngine


load_dotenv()

app = FastAPI(
    title="TrustTrace Prototype API",
    version="0.1.0",
    description="Explainable pre-authorization fraud assessment for traditional and Web3 payments.",
)

jofs = JOFSAdapter()
risk_engine = RiskEngine(jofs)
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "jofs_mode": jofs.mode}


@app.get("/api/jofs/accounts")
async def accounts():
    try:
        return await jofs.get_accounts()
    except Exception as exc:  # pragma: no cover - live integration safeguard
        raise HTTPException(status_code=502, detail=f"JOFS error: {exc}") from exc


@app.get("/api/jofs/accounts/{account_id}/balance")
async def balance(account_id: str):
    try:
        return await jofs.get_balance(account_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=502, detail=f"JOFS error: {exc}") from exc


@app.get("/api/jofs/accounts/{account_id}/beneficiaries")
async def beneficiaries(account_id: str):
    try:
        return await jofs.get_beneficiaries(account_id)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=502, detail=f"JOFS error: {exc}") from exc


@app.post("/api/risk/traditional", response_model=RiskAssessment)
async def assess_traditional(request: TraditionalRiskRequest) -> RiskAssessment:
    try:
        return await risk_engine.assess_traditional(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/risk/web3", response_model=RiskAssessment)
async def assess_web3(request: Web3RiskRequest) -> RiskAssessment:
    return await risk_engine.assess_web3(request)


@app.get("/api/demo/scenarios")
async def scenarios() -> dict:
    return {
        "traditional": {
            "safe": {
                "account_id": "ACC-1001",
                "beneficiary_id": "BEN-001",
                "amount": 89,
                "currency": "JOD",
                "merchant": "Noon Jordan",
                "domain": "www.noon.com",
                "device_id": "LEEN-IP15",
                "location": "Amman",
                "rapid_attempts": 0,
            },
            "suspicious": {
                "account_id": "ACC-1001",
                "beneficiary_id": "BEN-777",
                "amount": 650,
                "currency": "JOD",
                "merchant": "Fast Visa Approval",
                "domain": "visa-fast-approval.example",
                "device_id": "UNKNOWN-DEVICE",
                "location": "Unknown",
                "rapid_attempts": 4,
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
                "suspicious_network": False
            },
            "suspicious": {
                "wallet_address": "0xLEEN000000000000000000000000000000000001",
                "contract_address": "0xBAD0000000000000000000000000000000000777",
                "network": "ethereum",
                "action": "token_approval",
                "token_symbol": "USDT",
                "approval_limit": "unlimited",
                "wallet_scam_reports": 5,
                "suspicious_network": True
            }
        }
    }
